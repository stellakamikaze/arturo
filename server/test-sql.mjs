// Banco delle query vere del server (sigla Q): archivio.js su SQLite in memoria, con un piccolo
// adattatore che imita D1 (prepare, bind, all, first, run, batch). test.mjs prova la logica con un
// archivio finto: qui si prova che le query dicono quello che il riepilogo promette.
// Uso: node server/test-sql.mjs   (Node 22 o successivo; esce con 0 se tutto passa)
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { DatabaseSync } from "node:sqlite";
import { archivio } from "./archivio.js";

function d1() {
  const db = new DatabaseSync(":memory:");
  db.exec(readFileSync(new URL("./schema.sql", import.meta.url), "utf8"));
  const preparata = (sql, valori = []) => ({
    bind: (...v) => preparata(sql, v),
    // D1 restituisce oggetti normali, node:sqlite oggetti senza prototipo: si copiano.
    all: async () => ({ results: db.prepare(sql).all(...valori).map((r) => ({ ...r })) }),
    first: async () => { const r = db.prepare(sql).get(...valori); return r ? { ...r } : null; },
    run: async () => db.prepare(sql).run(...valori),
  });
  return { prepare: (sql) => preparata(sql), batch: async (lista) => { for (const p of lista) await p.run(); } };
}

const AL = "2026-10-13";
// Una riga per evento: [giorno, installazione, evento, valore, versione?]
async function con(righe) {
  const a = archivio(d1());
  for (const [giorno, installazione, evento, valore = "", versione = "v1"] of righe) {
    await a.scriviEventi([{ giorno, installazione, versione, sistema: "Darwin", evento, valore }], `${giorno}T10:00:00Z`);
  }
  return a;
}

const casi = {
  // Setup: conta l'ultima fase di chi non è arrivato in fondo e tace da 3 giorni.
  async Q01() {
    const a = await con([
      ["2026-10-01", "aaaaaaaa", "setup", "fase:0"], ["2026-10-01", "aaaaaaaa", "setup", "fase:2"],
      ["2026-10-01", "bbbbbbbb", "setup", "fase:0"], ["2026-10-01", "bbbbbbbb", "setup", "fine"],
      ["2026-10-12", "cccccccc", "setup", "fase:1"],  // ferma da un giorno: non ancora
      ["2026-10-02", "dddddddd", "setup", "fase:2"],
      // Arrivata in fondo e poi rilancia /setup per cambiare una cosa sola: non è ferma.
      ["2026-09-20", "eeeeeeee", "setup", "fine"], ["2026-10-01", "eeeeeeee", "setup", "fase:3"],
    ]);
    const m = await a.miglioramento(AL);
    assert.deepEqual(m.setupFermi, [{ valore: "fase:2", n: 2 }], "Q01 setup fermi");
    assert.equal(m.setupIniziati, 5, "Q01 setup iniziati");
    assert.equal(m.setupFiniti, 2, "Q01 setup finiti");
  },
  // Chi non lancia mai /setup: nata dal 15/10, da almeno un giorno, senza nessun evento setup.
  async Q07() {
    const a = await con([
      ["2026-10-14", "aaaaaaaa", "sessione"],                                  // nata prima degli eventi di /setup
      ["2026-10-15", "bbbbbbbb", "sessione"], ["2026-10-16", "bbbbbbbb", "sessione"],  // mai /setup
      ["2026-10-15", "cccccccc", "sessione"], ["2026-10-15", "cccccccc", "setup", "fase:0"],
      ["2026-10-17", "dddddddd", "sessione"],                                  // nata oggi: ancora presto
    ]);
    const m = await a.miglioramento("2026-10-17");
    assert.equal(m.setupMai, 1, "Q07 installazioni senza /setup");
  },
  // Guardie: chiede e confermata contati per guardia, solo negli ultimi 30 giorni.
  async Q02() {
    const a = await con([
      ["2026-10-10", "aaaaaaaa", "chiede", "exfil-guard.py"], ["2026-10-10", "aaaaaaaa", "confermata", "exfil-guard.py"],
      ["2026-10-11", "bbbbbbbb", "chiede", "exfil-guard.py"],
      ["2026-08-01", "aaaaaaaa", "chiede", "exfil-guard.py"],  // fuori finestra
      ["2026-10-12", "aaaaaaaa", "errore", "data-guard.py"], ["2026-10-12", "bbbbbbbb", "errore", "data-guard.py"],
    ]);
    const m = await a.miglioramento(AL);
    assert.deepEqual(m.conferme, [{ valore: "exfil-guard.py", chiede: 2, confermata: 1 }], "Q02 conferme");
    assert.deepEqual(m.errori, [{ valore: "data-guard.py", n: 2, installazioni: 2 }], "Q02 errori");
  },
  // Aggiornamenti non applicati per versione, ritenzione dalla prima e dall'ultima volta, Claude Code.
  async Q04() {
    const a = await con([
      ["2026-10-05", "aaaaaaaa", "aggiorna", "rifiutato", "v2026-10-05"], ["2026-10-06", "cccccccc", "aggiorna", "rifiutato", "v2026-10-05"],
      ["2026-10-06", "cccccccc", "aggiorna", "applicato", "v2026-10-05"],
      ["2026-08-01", "aaaaaaaa", "sessione"], ["2026-10-12", "aaaaaaaa", "sessione"],
      ["2026-08-01", "bbbbbbbb", "sessione"],
      ["2026-10-12", "aaaaaaaa", "claude", "2.1.290"], ["2026-10-12", "cccccccc", "claude", "2.1.290"],
    ]);
    const m = await a.miglioramento(AL);
    assert.deepEqual(m.aggiornaStorti, [{ versione: "v2026-10-05", valore: "rifiutato", n: 2 }], "Q04 aggiornamenti");
    assert.deepEqual(m.ritenzione.soglie.find((s) => s.giorni === 60), { giorni: 60, idonee: 2, vive: 1 }, "Q04 ritenzione a 60");
    assert.deepEqual(m.claude, [{ valore: "2.1.290", n: 2 }], "Q04 versioni di Claude Code");
  },
  // Il riepilogo della settimana porta «Dove migliorare»; quello del giorno no. Le query vecchie girano ancora.
  async Q05() {
    const a = await con([["2026-10-12", "aaaaaaaa", "sessione"], ["2026-10-12", "aaaaaaaa", "comando", "fine"]]);
    const settimana = await a.riepilogo("2026-10-06", AL, { settimana: true });
    assert.ok(settimana.migliorare && Array.isArray(settimana.migliorare.conferme), "Q05 manca «Dove migliorare»");
    assert.equal(settimana.migliorare.tappe, undefined, "Q05 la query delle tappe c'è ancora");
    assert.equal(settimana.sessioni, 1, "Q05 sessioni");
    const giorno = await a.riepilogo("2026-10-11", "2026-10-12");
    assert.equal(giorno.migliorare, null, "Q05 «Dove migliorare» nel recap del giorno");
  },
  // Il feedback del sito e i contatori del giorno (16/10/2026): testo salvato, vocale no, conteggio che sale.
  async Q08() {
    const a = await con([]);
    const n = await a.salvaFeedback({ tipo: "idea", testo: "Un comando per le bozze.", email: "", voce: 1 }, "2026-10-13T10:00:00Z");
    assert.equal(n, 1, "Q08 il feedback non ha un numero");
    assert.equal(await a.incrementa("2026-10-13", "feedback"), 1, "Q08 il contatore non parte da 1");
    assert.equal(await a.incrementa("2026-10-13", "feedback"), 2, "Q08 il contatore non sale");
    assert.equal(await a.incrementa("2026-10-14", "feedback"), 1, "Q08 il contatore non riparte il giorno dopo");
  },
  // Installazione nuova: vera solo finché dall'id non è arrivato niente (l'avviso Telegram parte una volta).
  async Q06() {
    const a = await con([["2026-10-12", "aaaaaaaa", "sessione"]]);
    assert.equal(await a.installazioneNuova("aaaaaaaa"), false, "Q06 un'installazione già vista risulta nuova");
    assert.equal(await a.installazioneNuova("bbbbbbbb"), true, "Q06 un'installazione mai vista non risulta nuova");
  },
};

for (const caso of Object.values(casi)) await caso();
console.log(`PASS ${Object.keys(casi).join(",")} controlli=${Object.keys(casi).length}`);
