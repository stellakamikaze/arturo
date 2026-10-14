// Il Worker di Arturo: collega logica.js a D1 (env.DB) e all'invio email (env.POSTA).
// Deploy e query utili: server/README.md.
import { EmailMessage } from "cloudflare:email";
import { gestisci, programmato, mime, LIMITI } from "./logica.js";

function archivio(db) {
  return {
    async contaEventi(installazione, giorno) {
      const r = installazione
        ? await db.prepare("SELECT COUNT(*) AS n FROM eventi WHERE installazione = ? AND ricevuto_giorno = ?").bind(installazione, giorno).first()
        : await db.prepare("SELECT COUNT(*) AS n FROM eventi WHERE ricevuto_giorno = ?").bind(giorno).first();
      return r ? r.n : 0;
    },
    async scriviEventi(righe, ricevuto) {
      const giorno = ricevuto.slice(0, 10);
      const insert = db.prepare(
        "INSERT INTO eventi (giorno, ricevuto_giorno, installazione, versione, sistema, evento, valore) VALUES (?, ?, ?, ?, ?, ?, ?)");
      await db.batch(righe.map((x) => insert.bind(x.giorno, giorno, x.installazione, x.versione, x.sistema, x.evento, x.valore)));
    },
    async contaSegnalazioni(giorno) {
      const r = await db.prepare("SELECT COUNT(*) AS n FROM segnalazioni WHERE substr(ricevuta, 1, 10) = ?").bind(giorno).first();
      return r ? r.n : 0;
    },
    async salvaSegnalazione(s, ricevuta) {
      const r = await db.prepare(
        "INSERT INTO segnalazioni (ricevuta, tipo, titolo, testo, versione, sistema, installazione) VALUES (?, ?, ?, ?, ?, ?, ?) RETURNING id")
        .bind(ricevuta, s.tipo, s.titolo, s.testo, s.versione, s.sistema, s.installazione).first();
      return r.id;
    },
    // Prende un posto fra le email del giorno: vero se c'era ancora posto.
    async prendiEmail(giorno, massimo) {
      const r = await db.prepare(
        "INSERT INTO contatori (giorno, chiave, n) VALUES (?, 'email', 1) ON CONFLICT (giorno, chiave) DO UPDATE SET n = n + 1 RETURNING n")
        .bind(giorno).first();
      return r.n <= massimo;
    },
    // Vero solo la prima volta che la chiave compare nel giorno: un avviso al giorno, non uno per lotto.
    async primaVolta(giorno, chiave) {
      const r = await db.prepare(
        "INSERT INTO contatori (giorno, chiave, n) VALUES (?, ?, 1) ON CONFLICT (giorno, chiave) DO UPDATE SET n = n + 1 RETURNING n")
        .bind(giorno, chiave).first();
      return r.n === 1;
    },
    async segnaEmail(id) {
      await db.prepare("UPDATE segnalazioni SET email_inviata = 1 WHERE id = ?").bind(id).run();
    },
    // L'elenco corrente della deriva per installazione: le righe dopo l'ultimo `insieme:<n>`.
    // Il giorno: solo gli elenchi cambiati nella finestra. La settimana: anche quelli fermi ma non vuoti.
    async deriva(dal, al, settimana) {
      const marcatori = (await db.prepare(
        `SELECT e.installazione, e.rowid AS r, e.valore, e.giorno FROM eventi e
         JOIN (SELECT installazione, MAX(rowid) AS r FROM eventi WHERE evento = 'deriva' AND valore LIKE 'insieme:%' GROUP BY installazione) m
           ON e.rowid = m.r`).all()).results
        .filter((m) => (m.giorno > dal && m.giorno <= al) || (settimana && m.valore !== "insieme:0"));
      const conflitti = new Set((await db.prepare(
        "SELECT DISTINCT installazione FROM eventi WHERE evento = 'aggiorna' AND valore = 'conflitto' AND giorno > date(?, '-30 day') AND giorno <= ?")
        .bind(al, al).all()).results.map((x) => x.installazione));
      const fuori = [];
      for (const m of marcatori) {
        const valori = (await db.prepare(
          "SELECT valore FROM eventi WHERE installazione = ? AND evento = 'deriva' AND rowid > ? AND valore NOT LIKE 'insieme:%' ORDER BY rowid")
          .bind(m.installazione, m.r).all()).results.map((x) => x.valore);
        fuori.push({ installazione: m.installazione, valori, conflitto: conflitti.has(m.installazione) });
      }
      return fuori;
    },
    async riepilogo(dal, al, { settimana = false } = {}) {
      const gruppo = async (evento) => (await db.prepare(
        "SELECT valore, COUNT(*) AS n FROM eventi WHERE evento = ? AND giorno > ? AND giorno <= ? GROUP BY valore ORDER BY n DESC LIMIT 20")
        .bind(evento, dal, al).all()).results;
      const colonna = async (nome) => (await db.prepare(
        `SELECT ${nome} AS valore, COUNT(DISTINCT installazione) AS n FROM eventi WHERE giorno > ? AND giorno <= ? GROUP BY ${nome} ORDER BY n DESC LIMIT 20`)
        .bind(dal, al).all()).results;
      const uno = async (sql) => ((await db.prepare(sql).bind(dal, al).first()) || { n: 0 }).n;
      return {
        installazioni: await uno("SELECT COUNT(DISTINCT installazione) AS n FROM eventi WHERE giorno > ? AND giorno <= ?"),
        sessioni: await uno("SELECT COUNT(*) AS n FROM eventi WHERE evento = 'sessione' AND giorno > ? AND giorno <= ?"),
        versioni: await colonna("versione"),
        sistemi: await colonna("sistema"),
        comandi: await gruppo("comando"),
        guardie: await gruppo("guardia"),
        aggiorna: await gruppo("aggiorna"),
        config: await gruppo("config"),
        deriva: await this.deriva(dal, al, settimana),
        guardieFrequenti: settimana ? (await db.prepare(
          "SELECT installazione, valore, COUNT(*) AS n FROM eventi WHERE evento = 'guardia' AND giorno > ? AND giorno <= ? GROUP BY installazione, valore HAVING n >= ? ORDER BY n DESC LIMIT 20")
          .bind(dal, al, LIMITI.guardieFrequenti).all()).results : null,
        segnalazioni: await uno("SELECT COUNT(*) AS n FROM segnalazioni WHERE substr(ricevuta, 1, 10) > ? AND substr(ricevuta, 1, 10) <= ?"),
      };
    },
    async pulisci(prima) {
      await db.batch([
        db.prepare("DELETE FROM eventi WHERE giorno < ?").bind(prima),
        db.prepare("DELETE FROM contatori WHERE giorno < ?").bind(prima),
      ]);
    },
  };
}

function posta(env) {
  return async ({ oggetto, testo }) => {
    const grezzo = mime({ da: env.MITTENTE, a: env.DESTINATARIO, oggetto, testo });
    await env.POSTA.send(new EmailMessage(env.MITTENTE, env.DESTINATARIO, grezzo));
  };
}

export default {
  async fetch(request, env) {
    return gestisci(request, { archivio: archivio(env.DB), posta: posta(env) });
  },
  async scheduled(evento, env, ctx) {
    ctx.waitUntil(programmato({ archivio: archivio(env.DB), posta: posta(env) }));
  },
};
