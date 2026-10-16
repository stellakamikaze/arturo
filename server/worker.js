// Il Worker di Arturo: collega logica.js e archivio.js a D1 (env.DB), all'invio email (env.POSTA) e a Telegram.
// Deploy e query utili: server/README.md.
import { EmailMessage } from "cloudflare:email";
import { gestisci, programmato, mime } from "./logica.js";
import { archivio } from "./archivio.js";

function posta(env) {
  return async ({ oggetto, testo }) => {
    const grezzo = mime({ da: env.MITTENTE, a: env.DESTINATARIO, oggetto, testo });
    await env.POSTA.send(new EmailMessage(env.MITTENTE, env.DESTINATARIO, grezzo));
  };
}

// Gli avvisi su Telegram: secret TELEGRAM_TOKEN e TELEGRAM_CHAT. Senza, non parte niente.
function avviso(env) {
  return async (testo) => {
    if (!env.TELEGRAM_TOKEN || !env.TELEGRAM_CHAT) return;
    const r = await fetch(`https://api.telegram.org/bot${env.TELEGRAM_TOKEN}/sendMessage`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ chat_id: env.TELEGRAM_CHAT, text: testo, disable_web_page_preview: true }),
    });
    const esito = await r.json().catch(() => ({}));
    console.log(esito.ok ? `Telegram: messaggio ${esito.result && esito.result.message_id} inviato` : `Telegram ha risposto ${r.status}`);
  };
}

// Il vocale del modulo di feedback: prima il testo, poi l'audio. Un .ogg (Firefox) va come messaggio
// vocale; webm e mp4 (Chrome, Safari) come file, che Telegram fa ascoltare lo stesso.
function voce(env) {
  const testo = avviso(env);
  return async (audio, messaggio, numero) => {
    await testo(messaggio);
    if (!env.TELEGRAM_TOKEN || !env.TELEGRAM_CHAT) return;
    const tipo = audio.type || "audio/webm";
    const vocale = /ogg/.test(tipo);
    const estensione = /ogg/.test(tipo) ? "ogg" : /mp4|m4a|aac/.test(tipo) ? "m4a" : /mpeg/.test(tipo) ? "mp3" : /wav/.test(tipo) ? "wav" : "webm";
    const corpo = new FormData();
    corpo.append("chat_id", env.TELEGRAM_CHAT);
    corpo.append(vocale ? "voice" : "document", new File([await audio.arrayBuffer()], `feedback-${numero}.${estensione}`, { type: tipo }));
    const r = await fetch(`https://api.telegram.org/bot${env.TELEGRAM_TOKEN}/${vocale ? "sendVoice" : "sendDocument"}`, { method: "POST", body: corpo });
    console.log(r.ok ? `Telegram: vocale del feedback ${numero} inviato` : `Telegram ha risposto ${r.status} al vocale`);
  };
}

// Il limite per IP: binding Rate Limiting LIMITE_EVENTI e LIMITE_MODULI (wrangler.toml). La chiave è
// l'IP di chi chiama, che il Worker non salva. Senza binding lascia passare.
function limite(env) {
  return async (tipo, request) => {
    const binding = tipo === "eventi" ? env.LIMITE_EVENTI : env.LIMITE_MODULI;
    if (!binding) return true;
    const { success } = await binding.limit({ key: request.headers.get("cf-connecting-ip") || "senza-ip" });
    return success;
  };
}

export default {
  async fetch(request, env) {
    return gestisci(request, { archivio: archivio(env.DB), posta: posta(env), avviso: avviso(env), voce: voce(env), token: env.RIEPILOGO_TOKEN,
      limite: limite(env) });
  },
  async scheduled(evento, env, ctx) {
    ctx.waitUntil(programmato({ archivio: archivio(env.DB), posta: posta(env) }));
  },
};
