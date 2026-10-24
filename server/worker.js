// Il Worker di Arturo: collega logica.js e archivio.js a D1 (env.DB), all'invio email (env.POSTA) e a Telegram.
// Deploy e query utili: server/README.md.
import { EmailMessage } from "cloudflare:email";
import { gestisci, programmato, mime, avvisoTelegram } from "./logica.js";
import { archivio } from "./archivio.js";

function posta(env) {
  return async ({ oggetto, testo }) => {
    const grezzo = mime({ da: env.MITTENTE, a: env.DESTINATARIO, oggetto, testo });
    await env.POSTA.send(new EmailMessage(env.MITTENTE, env.DESTINATARIO, grezzo));
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
    return gestisci(request, { archivio: archivio(env.DB), posta: posta(env), avviso: avvisoTelegram(env), token: env.RIEPILOGO_TOKEN,
      limite: limite(env) });
  },
  async scheduled(evento, env, ctx) {
    ctx.waitUntil(programmato({ archivio: archivio(env.DB), posta: posta(env), avviso: avvisoTelegram(env) }));
  },
};
