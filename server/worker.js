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

export default {
  async fetch(request, env) {
    return gestisci(request, { archivio: archivio(env.DB), posta: posta(env), avviso: avviso(env), token: env.RIEPILOGO_TOKEN });
  },
  async scheduled(evento, env, ctx) {
    ctx.waitUntil(programmato({ archivio: archivio(env.DB), posta: posta(env) }));
  },
};
