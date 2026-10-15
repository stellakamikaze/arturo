// Il Worker di Arturo: collega logica.js e archivio.js a D1 (env.DB) e all'invio email (env.POSTA).
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

export default {
  async fetch(request, env) {
    return gestisci(request, { archivio: archivio(env.DB), posta: posta(env), token: env.RIEPILOGO_TOKEN });
  },
  async scheduled(evento, env, ctx) {
    ctx.waitUntil(programmato({ archivio: archivio(env.DB), posta: posta(env) }));
  },
};
