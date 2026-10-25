// Banco del server di Arturo (W-casi con la sigla V): logica.js con un archivio e una posta finti.
// Uso: node server/test.mjs   (esce con 0 se tutto passa)
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
// Import per nome dal modulo intero: una funzione che manca (il veleno sulla versione vecchia) fa fallire il suo
// caso con il suo messaggio, non il caricamento del banco.
import * as logica from "./logica.js";
const { gestisci, settimanale, giornaliero, programmato, pulizia, giornoRoma, settimanaPrima, mime, testoDeriva, testoRiepilogo, ritenzione,
  LIMITI, EVENTI, calcolaIndietro, rilascio } = logica;

const VUOTO = { installazioni: 0, sessioni: 0, versioni: [], sistemi: [], comandi: [], guardie: [], aggiorna: [], config: [], deriva: [],
  guardieFrequenti: null, segnalazioni: 0, scartati: 0, telegramKo: 0, emailKo: 0 };

function finti(riepilogo = null) {
  const stato = { eventi: [], segnalazioni: [], email: [], avvisi: [], contatori: {}, chiavi: {}, pulito: null, finestre: [], opzioni: [],
    feedback: [], conteggi: {} };
  stato.lancillotto = [];
  const archivio = {
    async installazioneNuovaLancillotto(inst) { return !stato.lancillotto.some((e) => e.installazione === inst); },
    async contaEventiLancillotto(inst, giorno) {
      return stato.lancillotto.filter((e) => e.ricevuto === giorno && e.installazione === inst).length;
    },
    async scriviEventiLancillotto(righe, ricevuto) {
      for (const r of righe) stato.lancillotto.push({ ...r, ricevuto: ricevuto.slice(0, 10) });
    },
    async installazioneNuova(inst) { return !stato.eventi.some((e) => e.installazione === inst); },
    async contaEventi(inst, giorno) {
      return stato.eventi.filter((e) => e.ricevuto === giorno && e.installazione === inst).length;
    },
    async scriviEventi(righe, ricevuto) {
      for (const r of righe) stato.eventi.push({ ...r, ricevuto: ricevuto.slice(0, 10) });
    },
    async contaSegnalazioni() { return stato.segnalazioni.length; },
    async salvaSegnalazione(s) { stato.segnalazioni.push(s); return stato.segnalazioni.length; },
    async primaVolta(giorno, chiave) {
      const k = `${giorno} ${chiave}`;
      stato.chiavi[k] = (stato.chiavi[k] || 0) + 1;
      return stato.chiavi[k] === 1;
    },
    async segnaEmail() {},
    async incrementa(giorno, chiave, quanti = 1) {
      const k = `${giorno} ${chiave}`;
      stato.conteggi[k] = (stato.conteggi[k] || 0) + quanti;
      return stato.conteggi[k];
    },
    async salvaFeedback(f) { stato.feedback.push(f); return stato.feedback.length; },
    async riepilogo(dal, al, opzioni = {}) {
      stato.finestre.push([dal, al]);
      stato.opzioni.push(opzioni);
      if (riepilogo) return riepilogo;
      return { installazioni: 2, sessioni: 5, versioni: [{ valore: "v2026-10-13", n: 2 }], sistemi: [], comandi: [{ valore: "fine", n: 3 }],
        guardie: [], aggiorna: [], segnalazioni: 1, scartati: 0, telegramKo: 0, emailKo: 0 };
    },
    async pulisci(prima) { stato.pulito = prima; },
    async indietro() { return stato.indietro || []; },
    async ultimoAvviso(chiave) {
      const giorni = Object.keys(stato.conteggi).filter((k) => k.endsWith(` ${chiave}`)).map((k) => k.split(" ")[0]).sort();
      return giorni.length ? giorni[giorni.length - 1] : null;
    },
  };
  const posta = async (m) => { stato.email.push(m); };
  const avviso = async (t) => { stato.avvisi.push(t); };
  return { stato, archivio, posta, avviso };
}

const adesso = new Date("2026-10-13T10:00:00Z");
const post = (percorso, corpo) => new Request(`https://arturo.example${percorso}`, {
  method: "POST", body: typeof corpo === "string" ? corpo : JSON.stringify(corpo) });
const lotto = (eventi, extra = {}) => ({ installazione: "1b2c3d4e-aaaa-bbbb", versione: "v2026-10-13", sistema: "Darwin", eventi, ...extra });
// Dal 24/10/2026 un evento fuori elenco non fa rifiutare il lotto: si scarta, si conta, e non si salva niente.
async function scartato(evento, valore, marcatore) {
  const f = finti();
  const r = await gestisci(post("/v1/eventi", lotto([{ giorno: "2026-10-13", evento, valore }])), { ...f, adesso });
  assert.equal(r.status, 200, `${marcatore} ${evento} ${JSON.stringify(valore)}: il lotto non è accettato in parte`);
  assert.deepEqual(await r.json(), { accettati: 0, scartati: 1 }, `${marcatore} ${evento} ${JSON.stringify(valore)} accettato`);
  assert.equal(f.stato.eventi.length, 0, `${marcatore} ${evento} ${JSON.stringify(valore)} salvato`);
}

const casi = {
  async V01() {
    const f = finti();
    const r = await gestisci(post("/v1/eventi", lotto([{ giorno: "2026-10-12", evento: "comando", valore: "fine" },
      { giorno: "2026-10-13", evento: "sessione" }])), { ...f, adesso });
    assert.equal(r.status, 200, "V01 un lotto valido non è accettato");
    assert.deepEqual(await r.json(), { accettati: 2, scartati: 0 }, "V01 la risposta non conta gli accettati");
    assert.equal(f.stato.eventi.length, 2);
    assert.deepEqual(Object.keys(f.stato.eventi[0]).sort(),
      ["evento", "giorno", "installazione", "ricevuto", "sistema", "valore", "versione"], "V01 salvato un campo in più");
  },
  async V02() {
    const f = finti();
    for (const e of [{ evento: "prompt", valore: "ciao" }, { evento: "comando", valore: "/fine con testo privato" },
      { evento: "guardia", valore: "x".repeat(61) }, { evento: "sessione", valore: "qualcosa" }]) {
      await scartato(e.evento, e.valore, "V02");
    }
    for (const extra of [{ installazione: "corto" }, { sistema: "Amiga" }, { versione: "v".repeat(61) }]) {
      const r = await gestisci(post("/v1/eventi", lotto([{ evento: "sessione" }], extra)), { ...f, adesso });
      assert.equal(r.status, 400, `V02 lotto non valido accettato: ${JSON.stringify(extra)}`);
    }
    assert.equal(f.stato.eventi.length, 0, "V02 un lotto rifiutato ha scritto qualcosa");
  },
  async V03() {
    const f = finti();
    const grande = post("/v1/eventi", JSON.stringify(lotto([{ evento: "sessione" }])) + " ".repeat(LIMITI.corpoEventi));
    assert.equal((await gestisci(grande, { ...f, adesso })).status, 413, "V03 corpo troppo grande accettato");
    const pieno = Array.from({ length: LIMITI.eventiPerGiorno }, () => ({ evento: "sessione" }));
    assert.equal((await gestisci(post("/v1/eventi", lotto(pieno)), { ...f, adesso })).status, 200);
    assert.equal((await gestisci(post("/v1/eventi", lotto([{ evento: "sessione" }])), { ...f, adesso })).status, 429,
      "V03 il tetto giornaliero per installazione non regge");
  },
  async V04() {
    const f = finti();
    const r = await gestisci(post("/v1/eventi", lotto([{ giorno: "2099-01-01", evento: "sessione" }])), { ...f, adesso });
    assert.equal(r.status, 200);
    assert.equal(f.stato.eventi[0].giorno, "2026-10-13", "V04 un giorno nel futuro resta nel futuro");
  },
  async V05() {
    const f = finti();
    const s = { tipo: "problema", titolo: "[problema] /fine si ferma", testo: "Il commit non parte.", versione: "v2026-10-13", sistema: "Darwin" };
    const r = await gestisci(post("/v1/segnalazioni", s), { ...f, adesso });
    assert.equal(r.status, 201, "V05 segnalazione valida rifiutata");
    assert.deepEqual(await r.json(), { numero: 1, email: true });
    // Dal 24/10/2026 l'email è un campanello: numero e tipo, il testo resta in D1 (R18).
    assert.equal(f.stato.email[0].oggetto, "[Arturo] [problema] Segnalazione n. 1", "V05 oggetto sbagliato");
    assert.doesNotMatch(f.stato.email[0].testo, /Il commit non parte/, "V05 il testo della segnalazione esce per email");
    assert.match(f.stato.email[0].testo, /WHERE id = 1"/, "V05 l'email non dice come leggere la segnalazione");
    assert.equal(f.stato.segnalazioni[0].testo, "Il commit non parte.", "V05 il testo non resta sul server");
    for (const cattiva of [{ ...s, tipo: "spam" }, { ...s, titolo: "" }, { ...s, testo: "x".repeat(16001) }]) {
      assert.equal((await gestisci(post("/v1/segnalazioni", cattiva), { ...f, adesso })).status, 400, "V05 segnalazione non valida accettata");
    }
  },
  async V06() {
    const f = finti();
    const s = { tipo: "proposta", titolo: "t", testo: "x" };
    for (let i = 0; i < LIMITI.avvisiSegnalazioniPerGiorno + 3; i++) await gestisci(post("/v1/segnalazioni", s), { ...f, adesso });
    assert.equal(f.stato.segnalazioni.length, LIMITI.avvisiSegnalazioniPerGiorno + 3, "V06 oltre il tetto email la segnalazione non è salvata");
    assert.equal(f.stato.email.length, LIMITI.emailSegnalazioniPerGiorno, "V06 il tetto delle email non regge");
    assert.equal(f.stato.avvisi.length, LIMITI.avvisiSegnalazioniPerGiorno, "V06 il tetto degli avvisi delle segnalazioni non regge");
    // Le segnalazioni hanno finito le loro email: una config rotta ha ancora le sue.
    await gestisci(post("/v1/eventi", lotto([{ evento: "config", valore: "rotta-settings" }])), { ...f, adesso });
    assert.equal(f.stato.email.length, LIMITI.emailSegnalazioniPerGiorno + 1, "V06 le segnalazioni consumano le email delle config rotte");
  },
  async V07() {
    const f = finti();
    await settimanale({ ...f, adesso });
    assert.equal(f.stato.email.length, 1, "V07 il riepilogo non parte");
    assert.match(f.stato.email[0].testo, /Installazioni attive: 2/);
    await pulizia({ ...f, adesso });
    assert.equal(f.stato.pulito, "2025-10-13", "V07 la pulizia non usa 12 mesi");
  },
  async V08() {
    const m = mime({ da: "arturo@example.org", a: "x@example.org", oggetto: "[Arturo] perché", testo: "àèì", adesso, id: "abc" });
    assert.match(m, /^Message-ID: <abc@example\.org>$/m, "V08 manca il Message-ID");
    assert.match(m, /^Subject: =\?UTF-8\?B\?/m, "V08 l'oggetto con accenti non è codificato");
    const corpo = m.split("\r\n\r\n")[1].replace(/\r\n/g, "");
    assert.equal(Buffer.from(corpo, "base64").toString("utf8"), "àèì", "V08 il corpo non torna uguale");
    assert.deepEqual(Object.keys(EVENTI), ["sessione", "comando", "guardia", "aggiorna", "segnalazione", "deriva", "config",
      "setup", "chiede", "confermata", "errore", "claude", "tappa"], "V08 l'elenco degli eventi, con i vecchi in coda");
  },
  async V10() {
    const f = finti();
    await giornaliero({ ...f, adesso });
    assert.deepEqual(f.stato.finestre, [["2026-10-11", "2026-10-12"]], "V10 il recap non copre il solo giorno prima");
    assert.equal(f.stato.email[0].oggetto, "[Arturo] Recap del 2026-10-12", "V10 oggetto del recap sbagliato");
    assert.match(f.stato.email[0].testo, /^Arturo, il giorno 2026-10-12\n[\s\S]*Installazioni attive: 2/, "V10 testo del recap");
    assert.equal(f.stato.pulito, null, "V10 il recap giornaliero non deve pulire");
  },
  async V11() {
    const lunedi = new Date("2026-10-12T06:00:00Z"), martedi = new Date("2026-10-13T06:00:00Z");
    const f = finti();
    await programmato({ ...f, adesso: martedi });
    assert.deepEqual(f.stato.email.map((m) => m.oggetto.split(" ")[1]), ["Recap"], "V11 il martedì parte solo il recap");
    const g = finti();
    await programmato({ ...g, adesso: lunedi });
    assert.deepEqual(g.stato.email.map((m) => m.oggetto.split(" ")[1]), ["Recap", "Riepilogo"], "V11 il lunedì mancano recap o riepilogo");
    assert.equal(g.stato.pulito, "2025-10-12", "V11 il lunedì la pulizia non parte");
  },
  async V12() {
    const f = finti(VUOTO);
    await giornaliero({ ...f, adesso });
    assert.equal(f.stato.email.length, 0, "V12 il recap di un giorno vuoto parte lo stesso");
    const g = finti({ ...VUOTO, segnalazioni: 1 });
    await giornaliero({ ...g, adesso });
    assert.equal(g.stato.email.length, 1, "V12 una segnalazione sola non basta a far partire il recap");
    const h = finti(VUOTO);
    await programmato({ ...h, adesso: new Date("2026-10-12T06:00:00Z") });
    assert.deepEqual(h.stato.email.map((m) => m.oggetto.split(" ")[1]), ["Riepilogo"], "V12 il lunedì vuoto deve mandare il solo riepilogo");
    assert.match(h.stato.email[0].testo, /Versioni in uso:\n  nessuna\n[\s\S]*Comandi usati \(installazioni viste in almeno 2 giorni\):\n  nessuno\n[\s\S]*Guardie che hanno bloccato \(volte, installazioni viste in almeno 2 giorni\):\n  nessuna\n/,
      "V12 il genere di nessuno/nessuna è sbagliato");
  },
  async V13() {
    // La config rotta arriva subito per email, una sola al giorno per installazione, dentro il tetto.
    const f = finti();
    const rotta = lotto([{ evento: "config", valore: "rotta-settings" }]);
    assert.equal((await gestisci(post("/v1/eventi", rotta), { ...f, adesso })).status, 200, "V13 config rotta rifiutata");
    assert.equal(f.stato.email.length, 1, "V13 la config rotta non manda l'email subito");
    assert.match(f.stato.email[0].oggetto, /Config rotta/);
    assert.match(f.stato.email[0].testo, /Installazione 1b2c3d4e /, "V13 l'id non è accorciato");
    await gestisci(post("/v1/eventi", rotta), { ...f, adesso });
    assert.equal(f.stato.email.length, 1, "V13 seconda email per la stessa installazione nello stesso giorno");
    await gestisci(post("/v1/eventi", lotto([{ evento: "config", valore: "rotta-rebase" }], { installazione: "99999999-zzzz" })), { ...f, adesso });
    assert.equal(f.stato.email.length, 2, "V13 un'altra installazione non riceve il suo avviso");
    const g = finti();
    g.stato.conteggi["2026-10-13 email-rotta"] = LIMITI.emailRottePerGiorno;
    await gestisci(post("/v1/eventi", rotta), { ...g, adesso });
    assert.equal(g.stato.email.length, 0, "V13 il tetto delle email non vale per la config rotta");
    for (const v of ["rotta-altro", "rotta-settings ", "../x"]) await scartato("config", v, "V13");
  },
  async V14() {
    // Deriva: valori chiusi, ostacoli in cima, id accorciato, rientro detto.
    const f = finti();
    for (const v of ["insieme:2", "file:commands/inizio.md", "hook:bash-dispatcher.sh", "file:skills/x/SKILL.md"]) {
      assert.equal((await gestisci(post("/v1/eventi", lotto([{ evento: "deriva", valore: v }])), { ...f, adesso })).status, 200, `V14 deriva rifiuta ${v}`);
    }
    for (const v of ["file:/Users/gigi/segreto.md", "file:commands/con spazio.md", "insieme:1000", "progetto:x", "hook:", "file:../x", "file:commands/../../etc/passwd"]) {
      await scartato("deriva", v, "V14");
    }
    const righe = testoDeriva([
      { installazione: "aaaaaaaa-1111", valori: ["file:commands/inizio.md"], conflitto: false },
      { installazione: "bbbbbbbb-2222", valori: ["hook:bash-dispatcher.sh"], conflitto: false },
      { installazione: "cccccccc-3333", valori: ["file:commands/fine.md"], conflitto: true },
      { installazione: "dddddddd-4444", valori: [], conflitto: false },
      { installazione: "eeeeeeee-5555", valori: ["file:hooks/comms-guard.py"], conflitto: false },
    ]);
    assert.ok(righe[0].includes("OSTACOLO") && righe[1].includes("OSTACOLO"), "V14 gli ostacoli non stanno in cima");
    assert.ok(righe.some((r) => r === "  bbbbbbbb  OSTACOLO, hook di Arturo spenti: bash-dispatcher.sh"), "V14 riga dell'hook");
    assert.ok(righe.some((r) => /cccccccc  OSTACOLO, aggiornamento in conflitto, file di Arturo modificati: commands\/fine\.md/.test(r)), "V14 conflitto non segnato");
    assert.ok(righe.some((r) => r === "  aaaaaaaa  file di Arturo modificati: commands/inizio.md"), "V14 file senza conflitto");
    assert.ok(righe.some((r) => r.startsWith("  dddddddd  rientrata")), "V14 il rientro non è detto");
    assert.ok(righe.some((r) => r === "  eeeeeeee  OSTACOLO, guardie di Arturo modificate: hooks/comms-guard.py"), "V14 guardia modificata non è un ostacolo");
    assert.deepEqual(testoDeriva([]), ["  nessuna"]);
    const g = finti({ ...VUOTO, installazioni: 1, deriva: [{ installazione: "bbbbbbbb-2222", valori: ["hook:tutti"], conflitto: false }] });
    await giornaliero({ ...g, adesso });
    assert.match(g.stato.email[0].testo, /Deriva dalla config di Arturo:\n  bbbbbbbb  OSTACOLO, hook di Arturo spenti: tutti\n/, "V14 il recap non mostra la deriva");
  },
  async V15() {
    // Guardie frequenti: solo il lunedì, con la soglia scritta nel testo.
    const f = finti();
    await giornaliero({ ...f, adesso });
    assert.deepEqual(f.stato.opzioni, [{}], "V15 il recap del giorno chiede la settimana");
    assert.doesNotMatch(f.stato.email[0].testo, /Guardie frequenti/, "V15 guardie frequenti nel recap del giorno");
    const g = finti({ ...VUOTO, guardieFrequenti: [{ installazione: "aaaaaaaa-1111", valore: "comms-guard.py", n: 7 }] });
    await settimanale({ ...g, adesso });
    assert.deepEqual(g.stato.opzioni, [{ settimana: true }], "V15 il riepilogo non chiede la settimana");
    assert.match(g.stato.email[0].testo, /Guardie frequenti \(almeno 5 blocchi[^\n]*\n  7  comms-guard\.py su aaaaaaaa\n/, "V15 guardie frequenti mancanti");
    const h = finti({ ...VUOTO, guardieFrequenti: [] });
    await settimanale({ ...h, adesso });
    assert.match(h.stato.email[0].testo, /Guardie frequenti[^\n]*\n  nessuna\n/, "V15 settimana senza guardie frequenti");
  },
  async V09() {
    const f = finti();
    assert.equal((await gestisci(new Request("https://arturo.example/v1/eventi"), { ...f, adesso })).status, 405);
    assert.equal((await gestisci(post("/altro", {}), { ...f, adesso })).status, 404);
    assert.equal((await gestisci(post("/v1/eventi", "{non json"), { ...f, adesso })).status, 400);
  },
  // Gli eventi del 15/10/2026: i valori giusti passano, quelli con un testo dentro no. `tappa` è un
  // evento vecchio (il client non lo manda più dal 16/10/2026): resta accettato, con la stessa regola.
  async V16() {
    const buoni = [["setup", "fase:7b"], ["setup", "fase:4b"], ["setup", "fine"], ["chiede", "exfil-guard.py"], ["confermata", "exfil-guard.py"],
      ["errore", "data-guard.py"], ["tappa", "tappa:3"], ["tappa", "decisioni:12"], ["claude", "2.1.290"],
      ["aggiorna", "rifiutato"], ["aggiorna", "indietro"], ["aggiorna", "scartato"]];
    for (const [evento, valore] of buoni) {
      const f = finti();
      const r = await gestisci(post("/v1/eventi", lotto([{ giorno: "2026-10-13", evento, valore }])), { ...f, adesso });
      assert.deepEqual(await r.json(), { accettati: 1, scartati: 0 }, `V16 ${evento} ${valore} rifiutato`);
    }
    const cattivi = [["setup", "fase:11"], ["setup", "fase:3 nota"], ["tappa", "tappa:5"], ["tappa", "tappa:testo"],
      ["tappa", "note:3"], ["claude", "2.1.x-beta"], ["chiede", "una guardia con spazi"], ["aggiorna", "forse"],
      ["tappa", "tappa:3\n"]];
    for (const [evento, valore] of cattivi) await scartato(evento, valore, "V16");
  },
  // Il riepilogo in JSON esce solo con il token giusto, e un token corto non apre niente.
  async V17() {
    const token = "t".repeat(40);
    const get = (intestazione) => new Request("https://arturo.example/v1/riepilogo?dal=2026-10-06&al=2026-10-13",
      { headers: intestazione ? { authorization: intestazione } : {} });
    const f = finti({ ...VUOTO, migliorare: { setupIniziati: 1 } });
    assert.equal((await gestisci(get(null), { ...f, adesso, token })).status, 401, "V17 senza token risponde");
    assert.equal((await gestisci(get("Bearer " + "x".repeat(40)), { ...f, adesso, token })).status, 401, "V17 token sbagliato accettato");
    assert.equal((await gestisci(get("Bearer " + token.slice(0, 39)), { ...f, adesso, token })).status, 401, "V17 token corto accettato");
    assert.equal((await gestisci(get("Bearer "), { ...f, adesso, token: "" })).status, 401, "V17 senza token configurato risponde");
    const r = await gestisci(get("Bearer " + token), { ...f, adesso, token });
    assert.equal(r.status, 200, "V17 il token giusto non apre");
    const dati = await r.json();
    assert.equal(dati.dal, "2026-10-06");
    assert.deepEqual(f.stato.opzioni, [{ settimana: true }], "V17 il JSON non chiede la settimana");
    assert.equal(dati.migliorare.setupIniziati, 1, "V17 manca \"Dove migliorare\"");
  },
  // Ritenzione: per ogni soglia n contano solo le installazioni nate da almeno n giorni, e dal 24/10/2026 da meno
  // di n+30: la finestra di 30 giorni del blocco "Dove migliorare".
  async V18() {
    const r = ritenzione([
      { installazione: "a", prima: "2026-08-01", ultima: "2026-10-12" },  // nata 73 giorni fa: idonea solo a 60, viva
      { installazione: "b", prima: "2026-08-01", ultima: "2026-08-05" },  // nata 73 giorni fa, morta dopo 4 giorni
      { installazione: "c", prima: "2026-09-20", ultima: "2026-10-13" },  // 23 giorni: idonea solo a 7
      { installazione: "d", prima: "2026-10-10", ultima: "2026-10-13" },  // nuova
    ], "2026-10-13");
    assert.equal(r.nuove, 1, "V18 installazioni nuove");
    assert.deepEqual(r.soglie, [{ giorni: 7, idonee: 1, vive: 1 }, { giorni: 30, idonee: 0, vive: 0 }, { giorni: 60, idonee: 2, vive: 1 }],
      "V18 soglie della ritenzione");
  },
  // Il lunedì apre con "Dove migliorare Arturo"; il recap del giorno no.
  async V19() {
    const migliorare = { setupIniziati: 3, setupFiniti: 1, setupMai: 2, setupFermi: [{ valore: "fase:2", n: 2 }],
      conferme: [{ valore: "exfil-guard.py", chiede: 10, confermata: 9 }], errori: [], aggiornaStorti: [],
      ritenzione: { nuove: 1, soglie: [{ giorni: 60, idonee: 4, vive: 1 }] }, claude: [] };
    const f = finti({ ...VUOTO, migliorare });
    await settimanale({ ...f, adesso });
    const testo = f.stato.email[0].testo;
    assert.ok(testo.indexOf("DOVE MIGLIORARE ARTURO") < testo.indexOf("Installazioni attive"), "V19 la sezione non viene prima");
    assert.match(testo, /Setup: 3 iniziati, 1 arrivati in fondo, 2 installazioni nuove che non l'hanno mai lanciato[^\n]*\n  2  fase:2\n/, "V19 setup fermi");
    assert.match(testo, /exfil-guard\.py  10 \/ 9 \/ 90%/, "V19 quota di sì delle guardie");
    assert.doesNotMatch(testo, /Tappe/, "V19 la sezione delle tappe resta nel riepilogo");
    assert.match(testo, /vive dopo 60 giorni: 1 su 4 \(25%\)/, "V19 ritenzione");
    const g = finti();
    await giornaliero({ ...g, adesso });
    assert.doesNotMatch(g.stato.email[0].testo, /DOVE MIGLIORARE/, "V19 la sezione nel recap del giorno");
  },
  async V20() {
    // Un avviso Telegram per ogni installazione nuova e per ogni segnalazione, mai per i lotti successivi.
    const f = finti();
    await gestisci(post("/v1/eventi", lotto([{ evento: "sessione", valore: "" }])), { ...f, adesso });
    await gestisci(post("/v1/eventi", lotto([{ evento: "comando", valore: "fine" }])), { ...f, adesso });
    assert.equal(f.stato.avvisi.length, 1, "V20 l'installazione nuova va avvisata una volta sola");
    assert.match(f.stato.avvisi[0], /^Arturo: installazione nuova \(1b2c3d4e\) · v2026-10-13 · Darwin$/, "V20 testo dell'avviso di installazione");
    await gestisci(post("/v1/eventi", lotto([{ evento: "sessione", valore: "" }], { installazione: "99999999-zzzz" })), { ...f, adesso });
    assert.equal(f.stato.avvisi.length, 2, "V20 una seconda installazione non viene avvisata");
    await gestisci(post("/v1/segnalazioni", { tipo: "problema", titolo: "Il setup si ferma", testo: "Alla fase 2 esce un errore.", versione: "v2026-10-13", sistema: "Darwin" }), { ...f, adesso });
    assert.equal(f.stato.avvisi.length, 3, "V20 la segnalazione non viene avvisata");
    assert.equal(f.stato.avvisi[2], "Arturo: segnalazione n. 1 · problema · segnala", "V20 testo dell'avviso di segnalazione");
    // Un avviso che non parte non deve far perdere eventi o segnalazioni.
    const g = finti();
    const rotto = async () => { throw new Error("Telegram giù"); };
    const r = await gestisci(post("/v1/eventi", lotto([{ evento: "sessione", valore: "" }])), { ...g, avviso: rotto, adesso });
    assert.equal(r.status, 200, "V20 un avviso fallito fa fallire la richiesta");
    assert.equal(g.stato.eventi.length, 1, "V20 un avviso fallito fa perdere l'evento");
  },
  async V21() {
    // Il modulo di feedback del sito (16/10/2026): testo, tipo, email. Su Telegram il solo campanello (24/10/2026).
    const f = finti();
    const m = new FormData();
    for (const [k, v] of Object.entries({ tipo: "idea", testo: "Mi piacerebbe un comando per le bozze.", email: "a@esempio.it" })) m.append(k, v);
    const r = await gestisci(new Request("https://arturo.example/v1/feedback", { method: "POST", body: m }), { ...f, adesso });
    assert.equal(r.status, 201, "V21 un feedback scritto non è accettato");
    assert.deepEqual(f.stato.feedback[0], { tipo: "idea", testo: "Mi piacerebbe un comando per le bozze.", email: "a@esempio.it" },
      "V21 il feedback salvato non è quello mandato");
    assert.equal(f.stato.avvisi[0], "Arturo: feedback n. 1 · idea · sito", "V21 testo dell'avviso");
  },
  async V22() {
    // Rifiuti: niente da dire, email storta, la trappola dei bot, il tetto. Il vocale rifiutato sta in V39.
    const f = finti();
    const invia = (campi, voce, accept) => {
      const m = new FormData();
      for (const [k, v] of Object.entries(campi)) m.append(k, v);
      if (voce) m.append("voce", voce, "voce.webm");
      return gestisci(new Request("https://arturo.example/v1/feedback", { method: "POST", body: m,
        headers: accept ? { accept } : {} }), { ...f, adesso });
    };
    assert.equal((await invia({ testo: "  " })).status, 400, "V22 un feedback vuoto è accettato");
    assert.equal((await invia({ testo: "x", email: "non-una-email" })).status, 400, "V22 un'email storta è accettata");
    const bot = await invia({ testo: "compra ora", sito: "https://spam.example" });
    assert.equal(bot.status, 202, "V22 la trappola risponde diversamente da un invio vero");
    assert.equal(f.stato.feedback.length + f.stato.avvisi.length, 0, "V22 il messaggio di un bot è salvato o avvisato");
    const senzaJs = await invia({ testo: "dal modulo senza JavaScript" }, null, "text/html,application/xhtml+xml");
    assert.equal(senzaJs.status, 303, "V22 il modulo senza JavaScript non torna alla pagina");
    assert.equal(senzaJs.headers.get("location"), "/feedback/?inviato#inviato", "V22 il rimando non è relativo alla pagina del sito, o non ha l'ancora dell'esito");
    for (let i = 1; i < LIMITI.feedbackPerGiorno; i++) await invia({ testo: `n ${i}` });
    assert.equal((await invia({ testo: "uno di troppo" })).status, 429, "V22 il tetto giornaliero dei feedback non regge");
  },
  async V23() {
    // I download dal sito: un avviso per evento, con pagina e sistema, fino al tetto del giorno.
    const f = finti();
    let r = await gestisci(post("/v1/sito", { tipo: "download", pagina: "/installa/", sistema: "mac" }), { ...f, adesso });
    assert.equal(r.status, 202, "V23 un download non è accettato");
    assert.equal(f.stato.avvisi[0], "Arturo: qualcuno ha copiato il comando di installazione (/installa/, Mac) · 1° di oggi",
      "V23 testo dell'avviso di download");
    for (const sbagliato of [{ tipo: "virus", pagina: "/" }, { tipo: "download", pagina: "https://altro.example" },
      { tipo: "github", pagina: "/", sistema: "amiga" }]) {
      r = await gestisci(post("/v1/sito", sbagliato), { ...f, adesso });
      assert.equal(r.status, 400, `V23 un evento del sito fuori elenco è accettato: ${JSON.stringify(sbagliato)}`);
    }
    for (let i = 1; i < LIMITI.sitoPerGiorno + 5; i++) await gestisci(post("/v1/sito", { tipo: "github", pagina: "/" }), { ...f, adesso });
    assert.equal(f.stato.avvisi.length, 1 + LIMITI.sitoPerGiorno, "V23 i download oltre il tetto mandano ancora avvisi");
  },
  async V24() {
    // Chi arriva in fondo a /setup: un avviso solo, la prima volta per installazione.
    const f = finti();
    await gestisci(post("/v1/eventi", lotto([{ evento: "setup", valore: "fase:9" }, { evento: "setup", valore: "fine" }])), { ...f, adesso });
    await gestisci(post("/v1/eventi", lotto([{ evento: "setup", valore: "fine" }])), { ...f, adesso });
    const finiti = f.stato.avvisi.filter((a) => a.startsWith("Arturo: setup finito"));
    assert.equal(finiti.length, 1, `V24 il setup finito va avvisato una volta sola: ${JSON.stringify(f.stato.avvisi)}`);
    assert.equal(finiti[0], "Arturo: setup finito (1b2c3d4e) · v2026-10-13 · Darwin", "V24 testo dell'avviso di setup finito");
    // Tetto degli avvisi: oltre, il setup finito si registra ma non manda niente.
    const g = finti();
    g.stato.conteggi["2026-10-13 avviso-setup"] = LIMITI.avvisiSetupPerGiorno;
    await gestisci(post("/v1/eventi", lotto([{ evento: "setup", valore: "fine" }], { installazione: "77777777-setup" })), { ...g, adesso });
    assert.ok(!g.stato.avvisi.some((t) => t.includes("setup finito")), "V24 oltre il tetto il setup finito manda ancora avvisi");
  },
  async V25() {
    // Review di sicurezza del 16/10/2026: limite per IP e tetto degli avvisi delle installazioni nuove.
    const f = finti();
    const chiesti = [];
    const fermo = async (tipo) => { chiesti.push(tipo); return false; };
    assert.equal((await gestisci(post("/v1/eventi", lotto([{ evento: "sessione" }])), { ...f, adesso, limite: fermo })).status, 429,
      "V25 il limite per IP non ferma gli eventi");
    assert.equal(f.stato.eventi.length, 0, "V25 oltre il limite per IP gli eventi si salvano");
    assert.equal((await gestisci(post("/v1/segnalazioni", { tipo: "problema", titolo: "t", testo: "x" }), { ...f, adesso, limite: fermo })).status, 429,
      "V25 il limite per IP non ferma le segnalazioni");
    assert.equal((await gestisci(post("/v1/sito", { tipo: "download", pagina: "/", sistema: "" }), { ...f, adesso, limite: fermo })).status, 429,
      "V25 il limite per IP non ferma i download");
    const m = new FormData();
    m.append("testo", "ciao");
    assert.equal((await gestisci(new Request("https://arturo.example/v1/feedback", { method: "POST", body: m }), { ...f, adesso, limite: fermo })).status, 429,
      "V25 il limite per IP non ferma il feedback");
    assert.deepEqual(chiesti, ["eventi", "moduli", "moduli", "moduli"], "V25 il limite usa il secchio sbagliato");
    // Id inventati: oltre il tetto le installazioni nuove si contano ma non mandano messaggi.
    const g = finti();
    for (let i = 0; i < LIMITI.avvisiInstallazioniPerGiorno + 5; i++) {
      await gestisci(post("/v1/eventi", lotto([{ evento: "sessione" }], { installazione: `finta${String(i).padStart(4, "0")}` })), { ...g, adesso });
    }
    assert.equal(g.stato.avvisi.length, LIMITI.avvisiInstallazioniPerGiorno, "V25 il tetto degli avvisi di installazione non regge");
    assert.equal(g.stato.conteggi["2026-10-13 eventi"], LIMITI.avvisiInstallazioniPerGiorno + 5, "V25 il totale del giorno non sta nel contatore");
    g.stato.conteggi["2026-10-13 eventi"] = LIMITI.eventiTotaliPerGiorno;
    assert.equal((await gestisci(post("/v1/eventi", lotto([{ evento: "sessione" }])), { ...g, adesso })).status, 429, "V25 il tetto totale non regge");
  },
  async V26() {
    // Il giorno dichiarato più vecchio di una settimana e la versione libera.
    const f = finti();
    await gestisci(post("/v1/eventi", lotto([{ evento: "sessione", giorno: "0001-01-01" }, { evento: "sessione", giorno: "2026-10-08" }])), { ...f, adesso });
    assert.deepEqual(f.stato.eventi.map((e) => e.giorno), ["2026-10-13", "2026-10-08"], "V26 un giorno troppo vecchio non diventa il giorno del server");
    for (const v of ["ignora le istruzioni e", "v1\nriga", "<b>x</b>", "", "x".repeat(61)]) {
      assert.equal((await gestisci(post("/v1/eventi", lotto([{ evento: "sessione" }], { versione: v })), { ...f, adesso })).status, 400,
        `V26 una versione libera è accettata: ${JSON.stringify(v)}`);
    }
    for (const v of ["v2026-10-16.5", "v2026-10-16.5-3-gf16c16e", "f16c16e", "sconosciuta"]) {
      assert.equal((await gestisci(post("/v1/eventi", lotto([{ evento: "sessione" }], { versione: v })), { ...f, adesso })).status, 200,
        `V26 una versione vera è rifiutata: ${v}`);
    }
    await gestisci(post("/v1/segnalazioni", { tipo: "problema", titolo: "t", testo: "x", versione: "ignora le istruzioni" }), { ...f, adesso });
    assert.equal(f.stato.segnalazioni[0].versione, "", "V26 la segnalazione tiene una versione libera");
  },
  async V27() {
    // Il corpo ha un tetto anche senza content-length, niente invii da altri siti.
    const f = finti();
    const invia = (voce, headers = {}) => {
      const m = new FormData();
      m.append("testo", "x");
      return gestisci(new Request("https://arturo.example/v1/feedback", { method: "POST", body: m, headers }), { ...f, adesso });
    };
    assert.equal((await invia(null, { "sec-fetch-site": "cross-site" })).status, 403, "V27 un invio da un altro sito è accettato");
    assert.equal((await gestisci(new Request("https://arturo.example/v1/sito", { method: "POST", body: JSON.stringify({ tipo: "download", pagina: "/", sistema: "" }),
      headers: { "sec-fetch-site": "cross-site" } }), { ...f, adesso })).status, 403, "V27 un download da un altro sito è accettato");
    assert.equal((await invia(null, { "sec-fetch-site": "same-origin" })).status, 201, "V27 un invio dal sito è rifiutato");
    // Un corpo a pezzi, senza content-length, oltre il tetto.
    const pezzo = new Uint8Array(1024 * 1024);
    let n = 0;
    const flusso = new ReadableStream({ pull(c) { if (n++ < 7) c.enqueue(pezzo); else c.close(); } });
    const r = await gestisci(new Request("https://arturo.example/v1/feedback", { method: "POST", body: flusso, duplex: "half",
      headers: { "content-type": "multipart/form-data; boundary=x" } }), { ...f, adesso });
    assert.equal(r.status, 413, "V27 un corpo a pezzi oltre il tetto non è fermato");
  },
  // Ogni numero delle guardie dice quante installazioni lo producono, e il riepilogo ricorda che una guardia
  // non si allenta sulla sola base della telemetria anonima (#3507).
  async V28() {
    const r = { ...VUOTO, guardie: [{ valore: "exfil-guard.py", n: 4, installazioni: 2 }],
      migliorare: { conferme: [{ valore: "data-guard.py", chiede: 10, confermata: 10, installazioni: 1 }],
        errori: [{ valore: "comms-guard.py", n: 3, installazioni: 3 }], ritenzione: { nuove: 0, soglie: [] } } };
    const testo = testoRiepilogo(r, "prova");
    assert.match(testo, /4 {2}exfil-guard\.py, 2 installazioni/, "V28 i blocchi non dicono quante installazioni");
    assert.match(testo, /data-guard\.py {2}10 \/ 10 \/ 100%, 1 installazione\b/, "V28 le conferme non dicono quante installazioni");
    assert.match(testo, /comms-guard\.py {2}3, 3 installazioni/, "V28 gli errori non dicono quante installazioni");
    assert.match(testo, /almeno 2 giorni diversi\. Una guardia non si allenta sulla sola base di questi numeri/,
      "V28 il riepilogo non dice la regola sulle guardie");
    const token = "t".repeat(40);
    const f = finti({ ...VUOTO });
    const json = await (await gestisci(new Request("https://arturo.example/v1/riepilogo", { headers: { authorization: "Bearer " + token } }),
      { ...f, adesso, token })).json();
    assert.match(json.regola || "", /non si allenta sulla sola base della telemetria anonima/, "V28 il JSON per la routine non porta la regola");
  },
  // Le conferme per guardia vengono prima, poi quelle per regola, dove la guardia la dice (#3799).
  async V29() {
    const r = { ...VUOTO, migliorare: {
      confermeGuardie: [{ valore: "block-dangerous.py", chiede: 42, confermata: 2, installazioni: 2 },
        { valore: "exfil-guard.py", chiede: 1, confermata: 0, installazioni: 1 }],
      conferme: [{ valore: "block-dangerous.py.rm-cartella", chiede: 21, confermata: 1, installazioni: 2 }],
      errori: [], ritenzione: { nuove: 0, soglie: [] } } };
    const testo = testoRiepilogo(r, "prova");
    assert.match(testo, /quota di sì, installazioni\):\n {2}block-dangerous\.py {2}42 \/ 2 \/ 5%, 2 installazioni\n {2}exfil-guard\.py {2}1 \/ 0 \/ 0%, 1 installazione\n/,
      "V29 le conferme non sono sommate per guardia");
    assert.match(testo, /Per regola, dove la guardia la dice:\n {2}block-dangerous\.py\.rm-cartella {2}21 \/ 1 \/ 5%, 2 installazioni\n/,
      "V29 manca il dettaglio per regola");
  },
  // Le installazioni rimaste indietro (23/10/2026): il caso di Alessio, ferma alla v2026-10-19.2 con la
  // v2026-10-19.3 uscita da quattro giorni. Filippo alla v2026-10-21 non lo è: la v2026-10-22.2 ha un giorno.
  async V30() {
    assert.equal(rilascio("v2026-10-19.2-1-gdf1c2d0"), "v2026-10-19.2", "V30 il rilascio tiene i commit della persona");
    assert.equal(rilascio("sconosciuta"), null, "V30 una versione senza rilascio ha un rilascio");
    const versioni = [{ versione: "v2026-10-19.2", prima: "2026-10-19" }, { versione: "v2026-10-19.3-4-gabc1234", prima: "2026-10-19" },
      { versione: "v2026-10-21", prima: "2026-10-21" }, { versione: "v2026-10-22.2", prima: "2026-10-22" },
      { versione: "v2099-01-01", prima: "2026-10-01" }];  // inventata da un lotto: data nel futuro, non conta
    const attive = [{ installazione: "2c64c0dc-aaaa", versione: "v2026-10-19.2-1-gdf1c2d0", ultima: "2026-10-23" },
      { installazione: "826cca31-bbbb", versione: "v2026-10-21", ultima: "2026-10-22" },
      { installazione: "91288389-cccc", versione: "v2026-10-22.2", ultima: "2026-10-23" }];
    const fuori = calcolaIndietro(attive, versioni, "2026-10-23");
    assert.deepEqual(fuori, [{ installazione: "2c64c0dc-aaaa", rilascio: "v2026-10-19.2", ultima: "2026-10-23", nuovo: "v2026-10-19.3",
      dal: "2026-10-19" }], "V30 le installazioni indietro sono sbagliate");
    const f = finti();
    f.stato.indietro = fuori;
    await programmato({ ...f, adesso: new Date("2026-10-23T06:00:00Z") });
    assert.equal(f.stato.avvisi.length, 1, "V30 l'installazione indietro non arriva su Telegram");
    assert.match(f.stato.avvisi[0], /^Arturo: installazione 2c64c0dc ferma alla v2026-10-19\.2, attiva il 2026-10-23\..*\/aggiorna a mano/,
      "V30 il testo dell'avviso");
    await programmato({ ...f, adesso: new Date("2026-10-24T06:00:00Z") });
    assert.equal(f.stato.avvisi.length, 1, "V30 l'avviso torna il giorno dopo");
    await programmato({ ...f, adesso: new Date("2026-10-30T06:00:00Z") });
    assert.equal(f.stato.avvisi.length, 2, "V30 dopo una settimana l'avviso non torna");
    const g = finti();
    g.stato.indietro = Array.from({ length: 9 }, (_, i) => ({ ...fuori[0], installazione: `id${i}-xxxxxxxx` }));
    await programmato({ ...g, adesso: new Date("2026-10-23T06:00:00Z") });
    assert.equal(g.stato.avvisi.length, LIMITI.avvisiIndietroPerGiorno, "V30 gli avvisi superano il tetto del giorno");
    const testo = testoRiepilogo({ ...VUOTO, migliorare: { indietro: fuori, ritenzione: { nuove: 0, soglie: [] } } }, "prova");
    assert.match(testo, /Rimaste indietro[^\n]*\n {2}2c64c0dc {2}ferma alla v2026-10-19\.2, manca dal 2026-10-19, c'è la v2026-10-19\.3\n/,
      "V30 il riepilogo non elenca chi è rimasto indietro");
  },
  async V31() {
    // Il riepilogo del lunedì copre da lunedì a domenica della settimana prima, in ora di Roma (24/10/2026).
    // archivio.riepilogo esclude il primo giorno: la finestra (18/10, 25/10] sono i sette giorni dal 19 al 25.
    const f = finti();
    await programmato({ ...f, adesso: new Date("2026-10-26T06:00:00Z") });  // dopo il cambio d'ora del 25/10
    const settimana = f.stato.opzioni.findIndex((o) => o.settimana);
    assert.deepEqual(f.stato.finestre[settimana], ["2026-10-18", "2026-10-25"], "V31 la settimana non va dal lunedì 19 alla domenica 25");
    const oggetto = f.stato.email.find((m) => /Riepilogo/.test(m.oggetto)).oggetto;
    assert.equal(oggetto, "[Arturo] Riepilogo della settimana 2026-10-19 - 2026-10-25", "V31 il titolo non ha sette date");
    // Le 22:30 UTC di domenica 18/10 (ora legale) sono le 00:30 di lunedì 19 a Roma: parte la settimana dal 12 al 18.
    const g = finti();
    assert.equal(giornoRoma(new Date("2026-10-18T22:30:00Z")), "2026-10-19", "V31 il giorno di Roma è sbagliato");
    await programmato({ ...g, adesso: new Date("2026-10-18T22:30:00Z") });
    assert.ok(g.stato.email.some((m) => m.oggetto === "[Arturo] Riepilogo della settimana 2026-10-12 - 2026-10-18"),
      "V31 il lunedì di Roma non manda la settimana dal 12 al 18");
    // In un giorno qualsiasi la settimana è l'ultima finita, mai una che comprende oggi.
    assert.deepEqual(settimanaPrima(new Date("2026-10-24T10:00:00Z")), { lunedi: "2026-10-12", domenica: "2026-10-18" },
      "V31 di sabato la settimana non è l'ultima finita");
    assert.deepEqual(settimanaPrima(new Date("2026-10-25T10:00:00Z")), { lunedi: "2026-10-12", domenica: "2026-10-18" },
      "V31 di domenica la settimana comprende oggi");
  },
  async V32() {
    // Un passo del cron che fallisce non ferma gli altri, e il suo errore va nel log (24/10/2026).
    const errori = [];
    const originale = console.error;
    console.error = (...a) => errori.push(a.join(" "));
    try {
      const f = finti();
      f.stato.indietro = [{ installazione: "2c64c0dc-aaaa", rilascio: "v2026-10-19.2", ultima: "2026-10-25", nuovo: "v2026-10-22.1",
        dal: "2026-10-20" }];
      const posta = async (m) => { if (/Recap/.test(m.oggetto)) throw new Error("posta giù"); f.stato.email.push(m); };
      // Il cron finisce tutti i passi e poi risulta fallito, con i nomi dei passi falliti.
      const esito = await programmato({ ...f, posta, adesso: new Date("2026-10-26T06:00:00Z") }).then(() => null, (e) => e);
      assert.equal(f.stato.avvisi.length, 1, "V32 dopo il recap fallito l'avviso delle installazioni indietro non parte");
      assert.ok(f.stato.email.some((m) => /Riepilogo/.test(m.oggetto)), "V32 dopo il recap fallito il riepilogo del lunedì non parte");
      assert.equal(f.stato.pulito, "2025-10-26", "V32 dopo il recap fallito la pulizia non parte");
      assert.ok(esito, "V32 con un passo fallito il cron risulta riuscito");
      assert.deepEqual(esito.falliti, ["recap"], "V32 il cron non dice quale passo è fallito");
      assert.ok(errori.some((x) => /recap/.test(x) && /posta giù/.test(x)), "V32 l'errore del recap non è nel log");
      // Il riepilogo del lunedì fallito non salta la pulizia, e gli avvisi falliti non fermano la settimana.
      const g = finti();
      g.archivio.indietro = async () => { throw new Error("D1 giù"); };
      const postaG = async (m) => { if (/Riepilogo/.test(m.oggetto)) throw new Error("posta giù"); g.stato.email.push(m); };
      const esitoG = await programmato({ ...g, posta: postaG, adesso: new Date("2026-10-26T06:00:00Z") }).then(() => null, (e) => e);
      assert.deepEqual(esitoG && esitoG.falliti, ["indietro", "settimana"], "V32 i passi falliti sono sbagliati");
      assert.equal(g.stato.pulito, "2025-10-26", "V32 dopo il riepilogo fallito la pulizia non parte");
    } finally {
      console.error = originale;
    }
  },
  // F1 della telemetria (24/10/2026): liste chiuse, lotti accettati in parte, campanelli, contatori senza id.
  async V33() {
    // Una guardia che non è di Arturo ("hook-di-rossi") si scarta e si conta, senza id; il resto del lotto passa.
    const f = finti();
    const r = await gestisci(post("/v1/eventi", lotto([{ evento: "guardia", valore: "hook-di-rossi" }, { evento: "sessione" }])), { ...f, adesso });
    assert.equal(r.status, 200, "V33 il lotto con una guardia ignota non è accettato in parte");
    assert.deepEqual(await r.json(), { accettati: 1, scartati: 1 }, "V33 la risposta non conta la guardia scartata");
    assert.ok(!JSON.stringify(f.stato.eventi).includes("rossi"), "V33 la guardia hook-di-rossi è salvata");
    assert.equal(f.stato.conteggi["2026-10-13 scartati"], 1, "V33 la guardia scartata non è contata");
    assert.ok(Object.keys(f.stato.conteggi).every((k) => !k.includes("1b2c3d4e")), "V33 un contatore porta l'id dell'installazione");
    // Nomi parlanti, regole che non esistono, il fornitore del segreto, un comando della persona: tutti fuori.
    for (const [evento, valore] of [["guardia", "hook-di-rossi"], ["chiede", "hook-di-rossi"], ["confermata", "rossi-guard.py"],
      ["errore", "cliente-rossi.py"], ["chiede", "commit-secret-gate.py.google-api-key"], ["confermata", "block-dangerous.py.regola-inventata"],
      ["chiede", "block-dangerous.py."], ["comando", "cliente-rossi"], ["guardia", "block-dangerous"]]) {
      await scartato(evento, valore, "V33");
    }
    // I nomi veri del repository passano, con la regola dove la guardia la dice e "altro" per un comando della persona.
    for (const [evento, valore] of [["guardia", "block-dangerous.py"], ["chiede", "commit-secret-gate.py.segreto-cloud"],
      ["confermata", "block-dangerous.py.rm-cartella"], ["errore", "web-egress-guard.py"], ["chiede", "protect_claude_md.py"],
      ["chiede", "commit-secret-gate.py.scaduta"], ["comando", "altro"], ["comando", "fine"]]) {
      const g = finti();
      const r2 = await gestisci(post("/v1/eventi", lotto([{ evento, valore }])), { ...g, adesso });
      assert.deepEqual(await r2.json(), { accettati: 1, scartati: 0 }, `V33 ${evento} ${valore} è scartato`);
    }
  },
  async V34() {
    // Un lotto con 2 eventi validi e 1 ignoto salva i 2 e risponde {accettati: 2, scartati: 1}: prima il 400 faceva
    // perdere al client il lotto intero.
    const f = finti();
    const r = await gestisci(post("/v1/eventi", lotto([{ evento: "sessione" }, { evento: "prompt", valore: "testo privato" },
      { evento: "comando", valore: "fine" }])), { ...f, adesso });
    assert.equal(r.status, 200, "V34 il lotto con un evento ignoto non è accettato in parte");
    assert.deepEqual(await r.json(), { accettati: 2, scartati: 1 }, "V34 la risposta non è {accettati: 2, scartati: 1}");
    assert.deepEqual(f.stato.eventi.map((e) => e.evento), ["sessione", "comando"], "V34 non si salvano i 2 eventi validi");
    assert.equal(f.stato.conteggi["2026-10-13 eventi"], 2, "V34 il totale del giorno conta anche lo scartato");
    // Un lotto tutto fuori elenco: niente salvato, nessun avviso, e "constructor" non fa cadere il server.
    const g = finti();
    const tutti = await gestisci(post("/v1/eventi", lotto([{ evento: "constructor" }, { evento: "__proto__" }, { evento: "prompt" }, null])),
      { ...g, adesso });
    assert.deepEqual([tutti.status, await tutti.json()], [200, { accettati: 0, scartati: 4 }], "V34 il lotto tutto scartato");
    assert.equal(g.stato.eventi.length + g.stato.avvisi.length, 0, "V34 un lotto tutto scartato salva o avvisa");
    // Il 400 resta per il lotto malformato, che non conta scartati.
    const h = finti();
    for (const extra of [{ installazione: "corto" }, { eventi: "non un elenco" }, { sistema: "Amiga" }]) {
      assert.equal((await gestisci(post("/v1/eventi", lotto([{ evento: "sessione" }], extra)), { ...h, adesso })).status, 400,
        `V34 un lotto malformato è accettato: ${JSON.stringify(extra)}`);
    }
    assert.equal(h.stato.conteggi["2026-10-13 scartati"], undefined, "V34 un lotto malformato conta scartati");
  },
  async V39() {
    // Il vocale non si accetta più (24/10/2026): 400 con il motivo, niente salvato e niente su Telegram.
    const f = finti();
    const m = new FormData();
    m.append("testo", "Ecco il mio vocale.");
    m.append("voce", new Blob([new Uint8Array([0x1a, 0x45, 0xdf, 0xa3]), new Uint8Array(64)], { type: "audio/webm" }), "voce.webm");
    const r = await gestisci(new Request("https://arturo.example/v1/feedback", { method: "POST", body: m }), { ...f, adesso });
    assert.equal(r.status, 400, "V39 un feedback con il vocale è accettato");
    assert.match((await r.json()).errore || "", /vocale/, "V39 il rifiuto non dice il motivo");
    assert.equal(f.stato.feedback.length + f.stato.avvisi.length, 0, "V39 il feedback con il vocale è salvato o avvisato");
    // Dal 25/10/2026 il tetto è quello di un messaggio scritto: un vocale di un minuto (circa 500 KB) torna 413.
    const lungo = new FormData();
    lungo.append("testo", "Ecco il mio vocale lungo.");
    lungo.append("voce", new Blob([new Uint8Array(500 * 1024)], { type: "audio/webm" }), "voce.webm");
    const l = await gestisci(new Request("https://arturo.example/v1/feedback", { method: "POST", body: lungo }), { ...f, adesso });
    assert.equal(l.status, 413, "V39 un vocale di un minuto passa il tetto del modulo");
    assert.equal(f.stato.feedback.length + f.stato.avvisi.length, 0, "V39 il vocale lungo è salvato o avvisato");
    // Testo ed email facoltativa restano, anche al massimo dei caratteri.
    const n = new FormData();
    n.append("testo", "è".repeat(4000));
    n.append("email", "x@esempio.it");
    assert.equal((await gestisci(new Request("https://arturo.example/v1/feedback", { method: "POST", body: n }), { ...f, adesso })).status, 201,
      "V39 un feedback scritto con l'email è rifiutato");
  },
  async R18() {
    // Telegram ed email sono campanelli (24/10/2026): nessuna parola del testo, nessuna email, nessun id completo.
    const f = finti();
    const titolo = "Fattura sparita a Vigevano";
    const testo = "Il cliente Rossi ha perso la fattura numero 4471 dentro Dropbox";
    const installazione = "1b2c3d4e-aaaa-bbbb-cccc-ddddeeeeffff";
    await gestisci(post("/v1/segnalazioni", { tipo: "problema", titolo, testo, versione: "v2026-10-13", sistema: "Darwin", installazione }),
      { ...f, adesso });
    const m = new FormData();
    for (const [k, v] of Object.entries({ tipo: "idea", testo: "Vorrei salvare le bozze di Zanzibar", email: "maria.bianchi@esempio.it" })) m.append(k, v);
    await gestisci(new Request("https://arturo.example/v1/feedback", { method: "POST", body: m }), { ...f, adesso });
    assert.equal(f.stato.avvisi.length, 2, "R18 segnalazione e feedback non arrivano su Telegram");
    assert.equal(f.stato.email.length, 1, "R18 la segnalazione non arriva per email");
    const uscito = [...f.stato.avvisi, ...f.stato.email.map((e) => `${e.oggetto}\n${e.testo}`)].join("\n").toLowerCase();
    for (const parola of `${titolo} ${testo} Vorrei salvare le bozze di Zanzibar`.split(/\s+/).filter((p) => p.length >= 4)) {
      assert.ok(!uscito.includes(parola.toLowerCase()), `R18 la parola "${parola}" del testo esce verso Telegram o email`);
    }
    assert.ok(!uscito.includes("maria.bianchi") && !uscito.includes("esempio.it"), "R18 l'email del feedback esce verso Telegram");
    assert.ok(!uscito.includes(installazione.slice(0, 9)), "R18 l'id completo dell'installazione esce");
    assert.match(f.stato.avvisi[0], /segnalazione n\. 1 · problema · segnala$/, "R18 il campanello non dice numero, tipo e origine");
    assert.equal(f.stato.segnalazioni[0].testo, testo, "R18 il testo non resta sul server");
  },
  async V37() {
    // Un canale che tace si conta (24/10/2026): "telegram-ko" ed "email-ko" per giorno, senza id, e il recap li mostra.
    const f = finti();
    const giu = async () => { throw new Error("Telegram giù"); };
    const postaGiu = async () => { throw new Error("posta giù"); };
    const s = await gestisci(post("/v1/segnalazioni", { tipo: "problema", titolo: "t", testo: "x" }), { ...f, avviso: giu, posta: postaGiu, adesso });
    assert.deepEqual(await s.json(), { numero: 1, email: false }, "V37 con la posta giù la segnalazione non è salvata");
    await gestisci(post("/v1/eventi", lotto([{ evento: "config", valore: "rotta-settings" }])), { ...f, avviso: giu, posta: postaGiu, adesso });
    assert.equal(f.stato.conteggi["2026-10-13 telegram-ko"], 2, "V37 gli avvisi Telegram non partiti non sono contati");
    assert.equal(f.stato.conteggi["2026-10-13 email-ko"], 2, "V37 le email non partite non sono contate");
    const g = finti();
    const esito = await giornaliero({ ...g, posta: postaGiu, adesso }).then(() => null, (e) => e);
    assert.ok(esito, "V37 il recap non partito risulta riuscito");
    assert.equal(g.stato.conteggi["2026-10-13 email-ko"], 1, "V37 il recap non partito non è contato");
    // Un giorno con soli canali muti non è un giorno di zeri: il recap parte e li mostra, anche il lunedì.
    const h = finti({ ...VUOTO, scartati: 3, telegramKo: 2, emailKo: 1 });
    await giornaliero({ ...h, adesso });
    await settimanale({ ...h, adesso });
    assert.equal(h.stato.email.length, 2, "V37 un giorno con canali muti non manda il recap");
    for (const e of h.stato.email) {
      assert.match(e.testo, /Eventi scartati perché fuori elenco: 3\nAvvisi non partiti: Telegram 2, email 1\n/, `V37 ${e.oggetto} non mostra i contatori`);
    }
  },
  async V40() {
    // La cancellazione manuale copre anche feedback e segnalazioni, e dice che Gmail e Telegram non si raggiungono dal
    // server (24/10/2026). Il banco CP01 (tests/test_copie_2026_10_23.py) controlla che le due copie coincidano.
    for (const nome of ["server/README.md", "docs/manutenzione.md"]) {
      const testo = readFileSync(new URL(`../${nome}`, import.meta.url), "utf8");
      assert.match(testo, /DELETE FROM feedback WHERE email = '/, `V40 ${nome}: la cancellazione non tocca il feedback`);
      assert.match(testo, /DELETE FROM segnalazioni WHERE installazione = '/, `V40 ${nome}: la cancellazione non tocca le segnalazioni`);
      assert.match(testo, /Gmail\s+e\s+Telegram[^.]*non\s+si\s+raggiungono\s+dal\s+server/, `V40 ${nome}: non dice che Gmail e Telegram restano fuori`);
    }
  },
  async V41() {
    // Si salva solo il rilascio di Arturo (24/10/2026). Un tag della persona come "v-clienti-rossi" passava la forma di
    // VERSIONE e arrivava al D1, a Telegram (installazione nuova, setup finito), all'email della config rotta e al recap.
    const f = finti();
    const r = await gestisci(post("/v1/eventi", lotto([{ evento: "sessione" }, { evento: "setup", valore: "fine" },
      { evento: "config", valore: "rotta-settings" }], { versione: "v-clienti-rossi" })), { ...f, adesso });
    assert.ok(r.status >= 200 && r.status < 300, "V41 un lotto con un tag della persona come versione è rifiutato");
    const uscito = JSON.stringify([f.stato.eventi, f.stato.avvisi, f.stato.email]);
    assert.ok(!uscito.includes("rossi"), `V41 un tag della persona esce come versione: ${uscito.slice(0, 300)}`);
    assert.deepEqual([...new Set(f.stato.eventi.map((e) => e.versione))], ["sconosciuta"], "V41 un tag della persona non diventa sconosciuta");
    // Il conteggio e l'hash dei commit della persona cadono: resta il rilascio.
    const g = finti();
    await gestisci(post("/v1/eventi", lotto([{ evento: "sessione" }], { versione: "v2026-10-16.5-3-gf16c16e" })), { ...g, adesso });
    assert.deepEqual(g.stato.eventi.map((e) => e.versione), ["v2026-10-16.5"], "V41 l'hash dei commit della persona si salva");
    await gestisci(post("/v1/segnalazioni", { tipo: "problema", titolo: "t", testo: "x", versione: "vacanze-rossi" }), { ...g, adesso });
    assert.equal(g.stato.segnalazioni[0].versione, "sconosciuta", "V41 la segnalazione tiene il tag della persona come versione");
  },
  async V42() {
    // La deriva sul server ha i suoi elenchi chiusi (24/10/2026): un client di prima di F1 mandava i file della persona in
    // conflitto, e il recap li stampava. Un nome fuori elenco si salva come file:altro o hook:altro, il resto com'è.
    const f = finti();
    const valori = ["insieme:7", "file:skills/clienti-rossi/SKILL.md", "file:preventivo-rossi.md", "hook:hook-di-rossi.py",
      "file:agents/rossi.md", "file:skills/apri/SKILL.md", "file:settings.json", "hook:session-start.sh"];
    const r = await gestisci(post("/v1/eventi", lotto(valori.map((valore) => ({ evento: "deriva", valore })))), { ...f, adesso });
    assert.ok(r.status >= 200 && r.status < 300, "V42 la deriva di un client vecchio non è accettata");
    const salvati = f.stato.eventi.map((e) => e.valore);
    assert.ok(!salvati.join(" ").includes("rossi"), `V42 un file o un hook della persona si salva col suo nome: ${salvati}`);
    assert.deepEqual(salvati, ["insieme:7", "file:altro", "file:altro", "hook:altro", "file:altro", "file:skills/apri/SKILL.md",
      "file:settings.json", "hook:session-start.sh"], "V42 i nomi di Arturo non restano, o quelli fuori elenco non diventano altro");
    assert.deepEqual(await r.json(), { accettati: 8, scartati: 0 }, "V42 la deriva di un client vecchio non conta come accettata");
    const recap = testoDeriva([{ installazione: "1b2c3d4e-aaaa-bbbb", conflitto: true, valori: salvati.slice(1) }]).join("\n");
    assert.ok(!recap.includes("rossi"), "V42 il recap stampa un nome della persona");
    assert.deepEqual(["hook:tutti", "file:altro", "insieme:0"].map(logica.derivaPubblica), ["hook:tutti", "file:altro", "insieme:0"],
      "V42 hook:tutti, file:altro o insieme cambiano");
  },
  async V43() {
    // Una risposta di Telegram che non è ok diventa un errore, e consegna() la conta in "telegram-ko" (24/10/2026).
    // Prima finiva nel log del Worker: telegram-ko restava a zero con Telegram muto.
    const { avvisoTelegram } = logica;
    assert.equal(typeof avvisoTelegram, "function", "V43 avvisoTelegram manca in logica.js: la risposta di Telegram non si prova");
    const env = { TELEGRAM_TOKEN: "finto", TELEGRAM_CHAT: "42" };
    const chiamate = [];
    const risponde = (corpo, status = 200) => async (url, init) => {
      chiamate.push([url, JSON.parse(init.body)]);
      return new Response(JSON.stringify(corpo), { status });
    };
    for (const [corpo, status] of [[{ ok: false, description: "Bad Request: chat not found" }, 400], [{ ok: false }, 200], [{}, 502]]) {
      const errore = await avvisoTelegram(env, risponde(corpo, status))("x").then(() => null, (e) => e);
      assert.ok(errore, `V43 una risposta di Telegram non ok non diventa un errore: ${status} ${JSON.stringify(corpo)}`);
    }
    await avvisoTelegram(env, risponde({ ok: true, result: { message_id: 7 } }))("prova");
    assert.deepEqual(chiamate[chiamate.length - 1][1], { chat_id: "42", text: "prova", disable_web_page_preview: true }, "V43 il messaggio cambia");
    const f = finti();
    await gestisci(post("/v1/segnalazioni", { tipo: "problema", titolo: "t", testo: "x" }),
      { ...f, avviso: avvisoTelegram(env, risponde({ ok: false }, 200)), adesso });
    assert.equal(f.stato.conteggi["2026-10-13 telegram-ko"], 1, "V43 un avviso che Telegram rifiuta non è contato in telegram-ko");
    // Senza token non parte niente e non c'è errore.
    const prima = chiamate.length;
    await avvisoTelegram({}, risponde({ ok: false }))("x");
    assert.equal(chiamate.length, prima, "V43 senza token parte una chiamata a Telegram");
  },
  // Lancillotto (25/10/2026): un lotto valido va nella sua tabella, non tra gli eventi di Arturo.
  async L01() {
    const f = finti();
    const corpo = { installazione: "9f8e7d6c-1111-2222", versione: "0.2.0", sistema: "macos-26", eventi: [
      { giorno: "2026-10-13", evento: "installa", valore: "nuova" }, { giorno: "2026-10-13", evento: "giorno", valore: "eventi:3" },
      { giorno: "2026-10-13", evento: "url_assente", valore: "org.mozilla.firefox" }] };
    const r = await gestisci(post("/v1/lancillotto/eventi", corpo), { ...f, adesso });
    assert.equal(r.status, 200, "L01 un lotto valido di Lancillotto non è accettato");
    assert.deepEqual(await r.json(), { accettati: 3, scartati: 0 }, "L01 conteggio sbagliato");
    assert.equal(f.stato.lancillotto.length, 3, "L01 eventi non salvati nella tabella di Lancillotto");
    assert.equal(f.stato.eventi.length, 0, "L01 eventi di Lancillotto finiti tra quelli di Arturo");
    assert.equal(f.stato.avvisi.length, 1, "L01 nessun avviso per la nuova installazione");
    assert.match(f.stato.avvisi[0], /^Lancillotto: nuova installazione 9f8e7d6c/, "L01 avviso sbagliato");
    await gestisci(post("/v1/lancillotto/eventi", corpo), { ...f, adesso });
    assert.equal(f.stato.avvisi.length, 1, "L01 avviso ripetuto per la stessa installazione");
  },
  // Niente nomi di app, siti, titoli o testo: tutto fuori elenco si scarta.
  async L02() {
    const f = finti();
    const base = { installazione: "9f8e7d6c-1111-2222", versione: "0.2.0", sistema: "macos-26" };
    for (const [evento, valore] of [["url_assente", "com.esempio.GestionaleRossi"], ["comando", "cerca Mario Rossi"],
      ["giorno", "eventi:1234"], ["sensore", "ax:ok"], ["finestra", "https://web.bbva.it"], ["titolo", "Fattura 2026"],
      ["errore", "Traceback /Users/liliana"], ["__proto__", "x"]]) {
      const r = await gestisci(post("/v1/lancillotto/eventi", { ...base, eventi: [{ evento, valore }] }), { ...f, adesso });
      assert.deepEqual(await r.json(), { accettati: 0, scartati: 1 }, `L02 ${evento}=${valore} accettato`);
    }
    assert.equal(f.stato.lancillotto.length, 0, "L02 un valore fuori elenco è stato salvato");
    for (const extra of [{ versione: "v2026-10-13" }, { sistema: "Darwin" }, { installazione: "corto" }]) {
      const r = await gestisci(post("/v1/lancillotto/eventi", { ...base, ...extra, eventi: [{ evento: "installa", valore: "nuova" }] }),
        { ...f, adesso });
      assert.equal(r.status, 400, `L02 base non valida accettata: ${JSON.stringify(extra)}`);
    }
  },
  // L'elenco del server e quello del client (lancillotto/telemetria.py) coincidono, se il client è accanto.
  async L03() {
    const { EVENTI_LANCILLOTTO } = await import("./lancillotto.js");
    let client;
    try {
      client = readFileSync(new URL("../../lancillotto/lancillotto/telemetria.py", import.meta.url), "utf8");
    } catch {
      return;  // il repo di Lancillotto non è accanto: il confronto lo fa il suo banco
    }
    const blocco = /EVENTI = \{([\s\S]*?)\n\}/.exec(client);
    assert.ok(blocco, "L03 EVENTI non trovato nel client");
    const nomi = [...blocco[1].matchAll(/^\s+"([a-z_]+)":/gm)].map((m) => m[1]).sort();
    assert.deepEqual(nomi, Object.keys(EVENTI_LANCILLOTTO).sort(), "L03 eventi diversi fra client e server");
  },
};

// `node test.mjs V31 V32` fa girare i soli casi nominati (serve al veleno di un caso alla volta).
const scelti = process.argv.slice(2);
// Un nome sbagliato ferma il banco: altrimenti un caso scritto male non girerebbe e il banco direbbe PASS.
const ignoti = scelti.filter((nome) => !(nome in casi));
if (ignoti.length) throw new Error(`nessun caso con questi nomi: ${ignoti.join(" ")}`);
const daFare = Object.entries(casi).filter(([nome]) => !scelti.length || scelti.includes(nome));
for (const [, caso] of daFare) await caso();
console.log(`PASS ${daFare.map(([nome]) => nome).join(",")} controlli=${daFare.length}`);
