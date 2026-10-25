// Banco delle query vere del server (sigla Q): archivio.js su SQLite in memoria, con un piccolo
// adattatore che imita D1 (prepare, bind, all, first, run, batch). test.mjs prova la logica con un
// archivio finto: qui si prova che le query dicono quello che il riepilogo promette.
// Uso: node server/test-sql.mjs   (Node 22 o successivo; esce con 0 se tutto passa)
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { DatabaseSync } from "node:sqlite";
import { archivio } from "./archivio.js";
import { settimanale, pulizia, gestisci } from "./logica.js";

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
  // Setup: conta l'ultima fase di chi non è arrivato in fondo e tace da 3 giorni. Dal 24/10/2026 contano solo
  // installazioni viste in almeno due giorni: la sessione del 30/09 dà a ognuna il secondo giorno.
  async Q01() {
    const a = await con([
      ...["aaaaaaaa", "bbbbbbbb", "cccccccc", "dddddddd"].map((io) => ["2026-09-30", io, "sessione"]),
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
    assert.deepEqual(m.conferme, [{ valore: "exfil-guard.py", chiede: 2, confermata: 1, installazioni: 2 }], "Q02 conferme");
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
  // Il riepilogo della settimana porta "Dove migliorare"; quello del giorno no. Le query vecchie girano ancora.
  async Q05() {
    const a = await con([["2026-10-12", "aaaaaaaa", "sessione"], ["2026-10-12", "aaaaaaaa", "comando", "fine"]]);
    const settimana = await a.riepilogo("2026-10-06", AL, { settimana: true });
    assert.ok(settimana.migliorare && Array.isArray(settimana.migliorare.conferme), "Q05 manca \"Dove migliorare\"");
    assert.equal(settimana.migliorare.tappe, undefined, "Q05 la query delle tappe c'è ancora");
    assert.equal(settimana.sessioni, 1, "Q05 sessioni");
    const giorno = await a.riepilogo("2026-10-11", "2026-10-12");
    assert.equal(giorno.migliorare, null, "Q05 \"Dove migliorare\" nel recap del giorno");
  },
  // Il feedback del sito e i contatori del giorno (16/10/2026): testo salvato, conteggio che sale.
  async Q08() {
    const a = await con([]);
    const n = await a.salvaFeedback({ tipo: "idea", testo: "Un comando per le bozze.", email: "" }, "2026-10-13T10:00:00Z");
    assert.equal(n, 1, "Q08 il feedback non ha un numero");
    assert.equal(await a.incrementa("2026-10-13", "feedback"), 1, "Q08 il contatore non parte da 1");
    assert.equal(await a.incrementa("2026-10-13", "feedback"), 2, "Q08 il contatore non sale");
    assert.equal(await a.incrementa("2026-10-14", "feedback"), 1, "Q08 il contatore non riparte il giorno dopo");
    assert.equal(await a.incrementa("2026-10-14", "eventi", 40), 40, "Q08 il contatore non aggiunge un lotto intero");
    assert.equal(await a.incrementa("2026-10-14", "eventi", 2), 42, "Q08 il contatore del lotto non somma");
  },
  // Il feedback può avere un'email: pulisci() lo cancella dopo 12 mesi, come gli eventi (#3482).
  async Q09() {
    const db = d1();
    const a = archivio(db);
    await a.salvaFeedback({ tipo: "idea", testo: "vecchio", email: "a@b.it" }, "2025-10-01T10:00:00Z");
    await a.salvaFeedback({ tipo: "idea", testo: "nuovo", email: "" }, "2026-10-13T10:00:00Z");
    await a.pulisci("2025-10-16");
    const resto = await db.prepare("SELECT testo FROM feedback ORDER BY id").all();
    assert.deepEqual(resto.results.map((r) => r.testo), ["nuovo"], "Q09 pulisci() non tiene solo il feedback degli ultimi 12 mesi");
  },
  // Le statistiche delle guardie contano solo installazioni che il server ha visto in almeno due giorni
  // diversi, e dicono quante installazioni producono ogni numero (#3507). Il giorno che il client dichiara
  // non conta: conta quello in cui il server ha ricevuto il lotto.
  async Q10() {
    const a = await con([
      ["2026-10-10", "aaaaaaaa", "chiede", "data-guard.py"], ["2026-10-11", "aaaaaaaa", "confermata", "data-guard.py"],
      ["2026-10-10", "aaaaaaaa", "guardia", "block-dangerous.py"], ["2026-10-11", "aaaaaaaa", "errore", "exfil-guard.py"],
    ]);
    // Un id nuovo, tutto in un lotto ricevuto lo stesso giorno, anche se dichiara giorni diversi.
    const finte = [];
    for (let i = 0; i < 30; i++) {
      finte.push({ giorno: `2026-10-${String(5 + (i % 7)).padStart(2, "0")}`, installazione: "ffffffff", versione: "v1", sistema: "Darwin",
        evento: i % 3 === 0 ? "chiede" : i % 3 === 1 ? "confermata" : "guardia", valore: i % 3 === 2 ? "block-dangerous.py" : "data-guard.py" });
    }
    finte.push({ giorno: "2026-10-12", installazione: "ffffffff", versione: "v1", sistema: "Darwin", evento: "errore", valore: "exfil-guard.py" });
    await a.scriviEventi(finte, "2026-10-12T10:00:00Z");
    const m = await a.miglioramento(AL);
    assert.deepEqual(m.conferme, [{ valore: "data-guard.py", chiede: 1, confermata: 1, installazioni: 1 }],
      "Q10 le conferme contano un'installazione vista in un giorno solo");
    assert.deepEqual(m.errori, [{ valore: "exfil-guard.py", n: 1, installazioni: 1 }], "Q10 gli errori contano un'installazione vista in un giorno solo");
    const r = await a.riepilogo("2026-10-01", AL, { settimana: true });
    assert.deepEqual(r.guardie, [{ valore: "block-dangerous.py", n: 1, installazioni: 1 }], "Q10 i blocchi contano un'installazione vista in un giorno solo");
    assert.deepEqual(r.guardieFrequenti, [], "Q10 le guardie frequenti contano un'installazione vista in un giorno solo");
  },
  // Le chiavi "una volta per installazione" (giorno 'sempre') se ne vanno con gli eventi della loro
  // installazione, dopo 12 mesi: prima restavano per sempre (#3507).
  async Q11() {
    const db = d1();
    const a = archivio(db);
    await a.scriviEventi([{ giorno: "2025-09-01", installazione: "vecchiaa", versione: "v1", sistema: "Darwin", evento: "setup", valore: "fine" }],
      "2025-09-01T10:00:00Z");
    await a.scriviEventi([{ giorno: "2026-10-12", installazione: "viva0000", versione: "v1", sistema: "Darwin", evento: "setup", valore: "fine" }],
      "2026-10-12T10:00:00Z");
    assert.equal(await a.primaVolta("sempre", "setup-fine:vecchiaa"), true, "Q11 la prima volta non è vera");
    assert.equal(await a.primaVolta("sempre", "setup-fine:viva0000"), true, "Q11 la prima volta non è vera");
    await a.pulisci("2025-10-16");
    const resto = (await db.prepare("SELECT chiave FROM contatori WHERE giorno = 'sempre' ORDER BY chiave").all()).results.map((r) => r.chiave);
    assert.deepEqual(resto, ["setup-fine:viva0000"], "Q11 pulisci() non toglie le chiavi \"sempre\" delle installazioni senza più eventi");
    assert.equal(await a.primaVolta("sempre", "setup-fine:viva0000"), false, "Q11 la chiave di un'installazione viva è sparita");
  },
  // Dal 22/10/2026 block-dangerous dice la regola: le conferme si sommano anche per guardia, e
  // ventuno regole non fanno sparire dal riepilogo un'altra guardia (#3799).
  async Q12() {
    const righe = [];
    for (const io of ["aaaaaaaa", "bbbbbbbb"]) {
      righe.push(["2026-10-01", io, "sessione"]);
      for (let i = 0; i < 21; i++) righe.push(["2026-10-10", io, "chiede", `block-dangerous.py.regola-${i}`]);
      righe.push(["2026-10-10", io, "confermata", "block-dangerous.py.regola-0"]);
    }
    righe.push(["2026-10-11", "aaaaaaaa", "chiede", "exfil-guard.py"]);
    const m = await (await con(righe)).miglioramento(AL);
    assert.ok(!m.conferme.some((x) => x.valore === "exfil-guard.py"), "Q12 prova: exfil-guard.py resta nelle prime 20 regole");
    assert.deepEqual(m.confermeGuardie, [
      { valore: "block-dangerous.py", chiede: 42, confermata: 2, installazioni: 2 },
      { valore: "exfil-guard.py", chiede: 1, confermata: 0, installazioni: 1 },
    ], "Q12 le conferme per guardia");
  },
  // Le installazioni rimaste indietro, con le query vere (23/10/2026): conta la versione dell'ultimo evento,
  // e solo chi il server ha visto in almeno due giorni.
  async Q13() {
    const a = await con([
      ["2026-10-18", "gigi0000", "sessione", "", "v2026-10-19.3"], ["2026-10-19", "gigi0000", "sessione", "", "v2026-10-19.3"],
      ["2026-10-22", "gigi0000", "sessione", "", "v2026-10-22.2"],
      ["2026-10-19", "ales0000", "sessione", "", "v2026-10-19.2"], ["2026-10-23", "ales0000", "sessione", "", "v2026-10-19.2-1-gdf1c2d0"],
      ["2026-10-23", "nuov0000", "sessione", "", "v2026-10-14"],  // vista un giorno solo: non conta
      ["2026-10-10", "vecc0000", "sessione", "", "v2026-10-14"], ["2026-10-11", "vecc0000", "sessione", "", "v2026-10-14"],  // non attiva
    ]);
    const fuori = await a.indietro("2026-10-23");
    assert.deepEqual(fuori.map((x) => [x.installazione, x.rilascio, x.nuovo, x.dal, x.ultima]),
      [["ales0000", "v2026-10-19.2", "v2026-10-19.3", "2026-10-18", "2026-10-23"]], "Q13 installazioni indietro");
    assert.equal(await a.ultimoAvviso("indietro:ales0000"), null, "Q13 un avviso mai mandato ha un giorno");
    await a.incrementa("2026-10-23", "indietro:ales0000");
    assert.equal(await a.ultimoAvviso("indietro:ales0000"), "2026-10-23", "Q13 l'ultimo avviso non si ritrova");
    assert.deepEqual((await a.miglioramento("2026-10-23")).indietro, fuori, "Q13 il riepilogo non porta chi è indietro");
  },
  // Installazione nuova: vera solo finché dall'id non è arrivato niente (l'avviso Telegram parte una volta).
  async Q06() {
    const a = await con([["2026-10-12", "aaaaaaaa", "sessione"]]);
    assert.equal(await a.installazioneNuova("aaaaaaaa"), false, "Q06 un'installazione già vista risulta nuova");
    assert.equal(await a.installazioneNuova("bbbbbbbb"), true, "Q06 un'installazione mai vista non risulta nuova");
  },
  // Il riepilogo del lunedì sulle query vere: conta il lunedì della settimana prima, non il lunedì di oggi (24/10/2026).
  async Q14() {
    const a = await con([
      ["2026-10-18", "dddddddd", "sessione"],  // domenica della settimana prima ancora: fuori
      ["2026-10-19", "aaaaaaaa", "sessione"], ["2026-10-19", "a2a2a2a2", "sessione"],  // lunedì 19: dentro
      ["2026-10-25", "bbbbbbbb", "sessione"],  // domenica 25: dentro
      ["2026-10-26", "cccccccc", "sessione"],  // lunedì 26, il giorno del riepilogo: fuori
    ]);
    const email = [];
    await settimanale({ archivio: a, posta: async (m) => { email.push(m); }, adesso: new Date("2026-10-26T06:00:00Z") });
    assert.match(email[0].testo, /Installazioni attive: 3\nSessioni: 3\n/, "Q14 la settimana non conta dal lunedì 19 alla domenica 25");
  },
  // F1 della telemetria (24/10/2026). Le segnalazioni se ne vanno dopo 12 mesi, con la data degli eventi:
  // una di 366 giorni si cancella, una di 364 resta.
  async Q15() {
    const db = d1();
    const a = archivio(db);
    const s = (titolo) => ({ tipo: "problema", titolo, testo: "x", versione: "", sistema: "Darwin", installazione: "" });
    await a.salvaSegnalazione(s("di 366 giorni"), "2025-10-12T10:00:00Z");
    await a.salvaSegnalazione(s("di 364 giorni"), "2025-10-14T10:00:00Z");
    await pulizia({ archivio: a, adesso: new Date("2026-10-13T06:00:00Z") });
    const resto = (await db.prepare("SELECT titolo FROM segnalazioni ORDER BY id").all()).results.map((r) => r.titolo);
    assert.deepEqual(resto, ["di 364 giorni"], "Q15 pulisci() non cancella le segnalazioni più vecchie di 12 mesi");
  },
  // "Dove migliorare" conta gli ultimi 30 giorni in tutto il blocco: setup e ritenzione non contano più lo storico.
  async Q19() {
    const a = await con([
      ["2026-09-02", "vecchia0", "sessione"], ["2026-09-03", "vecchia0", "setup", "fase:0"], ["2026-09-03", "vecchia0", "setup", "fine"],  // 40 giorni fa
      ["2026-09-07", "ferma000", "sessione"], ["2026-09-08", "ferma000", "setup", "fase:4"],  // ferma da 35 giorni: fuori
      ["2026-10-02", "nuova000", "sessione"], ["2026-10-03", "nuova000", "setup", "fase:2"],  // ferma da 10 giorni: dentro
      ["2026-03-27", "antica00", "sessione"], ["2026-07-05", "antica00", "sessione"],  // nata 200 giorni fa: fuori da ogni soglia
      ["2026-08-04", "giovane0", "sessione"], ["2026-10-08", "giovane0", "sessione"],  // nata 70 giorni fa, viva 65: dentro a 60
    ]);
    const m = await a.miglioramento(AL);
    assert.equal(m.setupIniziati, 1, "Q19 i setup iniziati contano oltre i 30 giorni");
    assert.equal(m.setupFiniti, 0, "Q19 i setup finiti contano oltre i 30 giorni");
    assert.deepEqual(m.setupFermi, [{ valore: "fase:2", n: 1 }], "Q19 i setup fermi contano oltre i 30 giorni");
    assert.deepEqual(m.ritenzione.soglie.find((x) => x.giorni === 60), { giorni: 60, idonee: 1, vive: 1 }, "Q19 la ritenzione conta tutto lo storico");
    // Anche chi non ha mai lanciato /setup: una nata 40 giorni fa resta fuori, una nata 11 giorni fa conta. La data è dopo
    // SETUP_DAL, così la finestra è l'unico filtro che le separa.
    const b = await con([
      ["2026-10-22", "mai00040", "sessione"], ["2026-10-23", "mai00040", "sessione"],
      ["2026-11-20", "mai00011", "sessione"], ["2026-11-21", "mai00011", "sessione"],
    ]);
    assert.equal((await b.miglioramento("2026-12-01")).setupMai, 1, "Q19 le installazioni senza /setup contano oltre i 30 giorni");
  },
  // Comandi, setup, versioni di Claude Code e aggiornamenti non applicati contano solo installazioni viste in almeno
  // due giorni: un id nuovo, tutto in un lotto di un giorno, non li sposta (24/10/2026).
  async Q20() {
    const a = await con([
      ["2026-10-10", "vera0000", "sessione"], ["2026-10-11", "vera0000", "comando", "fine"], ["2026-10-11", "vera0000", "setup", "fase:1"],
      ["2026-10-11", "vera0000", "claude", "2.1.290"], ["2026-10-11", "vera0000", "aggiorna", "rifiutato", "v2026-10-05"],
    ]);
    const finta = (evento, valore, versione = "v1") => ({ giorno: "2026-10-09", installazione: "finta000", versione, sistema: "Darwin", evento, valore });
    await a.scriviEventi([...Array.from({ length: 5 }, () => finta("comando", "inizio")), finta("setup", "fase:1"), finta("claude", "9.9.9"),
      finta("aggiorna", "rifiutato", "v2026-10-05"), { ...finta("sessione", ""), giorno: "2026-10-12" }], "2026-10-12T10:00:00Z");
    const r = await a.riepilogo("2026-10-06", AL, { settimana: true });
    assert.deepEqual(r.comandi, [{ valore: "fine", n: 1 }], "Q20 i comandi contano un'installazione vista in un giorno solo");
    assert.equal(r.migliorare.setupIniziati, 1, "Q20 i setup contano un'installazione vista in un giorno solo");
    assert.deepEqual(r.migliorare.claude, [{ valore: "2.1.290", n: 1 }], "Q20 le versioni di Claude Code contano un'installazione vista in un giorno solo");
    assert.deepEqual(r.migliorare.aggiornaStorti, [{ versione: "v2026-10-05", valore: "rifiutato", n: 1 }],
      "Q20 gli aggiornamenti contano un'installazione vista in un giorno solo");
    // Lo stesso per chi non ha mai lanciato /setup e per i setup fermi: un id visto in un giorno solo non li sposta.
    const c = await con([
      ["2026-11-20", "vista000", "sessione"], ["2026-11-21", "vista000", "sessione"],                   // due giorni, mai /setup: conta
      ["2026-11-20", "unavolta", "sessione"],                                                         // un giorno solo, mai /setup: fuori
      ["2026-11-10", "ferma001", "sessione"], ["2026-11-11", "ferma001", "setup", "fase:3"],           // ferma, due giorni: conta
      ["2026-11-12", "ferma002", "setup", "fase:5"],                                                  // ferma, un giorno solo: fuori
    ]);
    const mc = await c.miglioramento("2026-12-01");
    assert.equal(mc.setupMai, 1, "Q20 le installazioni senza /setup contano un'installazione vista in un giorno solo");
    assert.deepEqual(mc.setupFermi, [{ valore: "fase:3", n: 1 }], "Q20 i setup fermi contano un'installazione vista in un giorno solo");
  },
  // I contatori senza id (scartati, telegram-ko, email-ko) arrivano nel riepilogo, sommati nella finestra, e un
  // lotto con un evento ignoto passa in parte anche sulle query vere.
  async Q21() {
    const db = d1();
    const a = archivio(db);
    const res = await gestisci(new Request("https://arturo.example/v1/eventi", { method: "POST", body: JSON.stringify({
      installazione: "bbbbbbbb-1111", versione: "v1", sistema: "Darwin",
      eventi: [{ evento: "sessione" }, { evento: "guardia", valore: "hook-di-rossi" }] }) }),
      { archivio: a, posta: async () => {}, adesso: new Date("2026-10-12T10:00:00Z") });
    assert.deepEqual(await res.json(), { accettati: 1, scartati: 1 }, "Q21 il lotto non passa in parte sulle query vere");
    await a.incrementa("2026-10-12", "scartati", 4);
    await a.incrementa("2026-10-12", "telegram-ko");
    await a.incrementa("2026-10-12", "email-ko");
    await a.incrementa("2026-10-11", "email-ko");  // fuori dalla finestra (11, 12]
    await a.incrementa("2026-10-12", "avviso-segnalazione", 7);  // un'altra chiave: non conta
    const r = await a.riepilogo("2026-10-11", "2026-10-12");
    assert.deepEqual([r.scartati, r.telegramKo, r.emailKo], [5, 1, 1], "Q21 il riepilogo non porta i contatori senza id");
    const conId = (await db.prepare("SELECT chiave FROM contatori WHERE chiave LIKE '%bbbbbbbb%'").all()).results;
    assert.deepEqual(conId, [], "Q21 un contatore porta l'id dell'installazione");
    const salvati = (await db.prepare("SELECT valore FROM eventi WHERE evento = 'guardia'").all()).results;
    assert.deepEqual(salvati, [], "Q21 la guardia scartata è salvata");
  },
  // Lancillotto (25/10/2026): la tabella nasce dal Worker, il riepilogo conta installazioni, la pulizia regge
  // anche su un database dove la tabella non c'era ancora.
  async QL1() {
    const db = d1();
    const a = archivio(db);
    await a.pulisci("2025-10-13");
    const corpo = (id, eventi) => JSON.stringify({ installazione: id, versione: "0.2.0", sistema: "macos-26", eventi });
    for (const [id, eventi] of [
      ["aaaa1111-l", [{ evento: "guida", valore: "accessibilita:ok" }, { evento: "permesso", valore: "schermo:no" },
        { evento: "url_assente", valore: "org.mozilla.firefox" }, { evento: "riavvio", valore: "2" }]],
      ["bbbb2222-l", [{ evento: "guida", valore: "accessibilita:ok" }, { evento: "permesso", valore: "ax:si" },
        { evento: "riavvio", valore: "1" }]]]) {
      const r = await gestisci(new Request("https://x/v1/lancillotto/eventi", { method: "POST", body: corpo(id, eventi) }),
        { archivio: a, posta: async () => {}, adesso: new Date("2026-10-12T10:00:00Z") });
      assert.equal(r.status, 200, "QL1 lotto rifiutato");
    }
    const r = await a.riepilogoLancillotto("2026-10-11", "2026-10-12");
    assert.equal(r.installazioni, 2, "QL1 installazioni");
    assert.deepEqual(r.guida, [{ valore: "accessibilita:ok", n: 2 }], "QL1 guida");
    assert.deepEqual(r.permessiMancanti, [{ valore: "schermo:no", n: 1 }], "QL1 permessi mancanti");
    assert.equal(r.riavvii, 3, "QL1 riavvii");
    const arturo = (await db.prepare("SELECT COUNT(*) AS n FROM eventi").first()).n;
    assert.equal(arturo, 0, "QL1 eventi di Lancillotto tra quelli di Arturo");
    const tutto = await a.riepilogo("2026-10-11", "2026-10-12");
    assert.equal(tutto.lancillotto.installazioni, 2, "QL1 il riepilogo di Arturo non porta Lancillotto");
    await a.pulisci("2026-10-13");
    assert.equal((await db.prepare("SELECT COUNT(*) AS n FROM eventi_lancillotto").first()).n, 0, "QL1 la pulizia non tocca Lancillotto");
  },
};

// `node test-sql.mjs Q15 Q19` fa girare i soli casi nominati (24/10/2026: serve al veleno di un caso alla volta).
const scelti = process.argv.slice(2);
const ignoti = scelti.filter((nome) => !(nome in casi));
if (ignoti.length) throw new Error(`nessun caso con questi nomi: ${ignoti.join(" ")}`);
const daFare = Object.entries(casi).filter(([nome]) => !scelti.length || scelti.includes(nome));
for (const [, caso] of daFare) await caso();
console.log(`PASS ${daFare.map(([nome]) => nome).join(",")} controlli=${daFare.length}`);
