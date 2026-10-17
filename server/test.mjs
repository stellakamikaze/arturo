// Banco del server di Arturo (W-casi con la sigla V): logica.js con un archivio e una posta finti.
// Uso: node server/test.mjs   (esce con 0 se tutto passa)
import assert from "node:assert/strict";
import { gestisci, settimanale, giornaliero, programmato, mime, testoDeriva, testoRiepilogo, ritenzione, LIMITI, EVENTI } from "./logica.js";

const VUOTO = { installazioni: 0, sessioni: 0, versioni: [], sistemi: [], comandi: [], guardie: [], aggiorna: [], config: [], deriva: [],
  guardieFrequenti: null, segnalazioni: 0 };

function finti(riepilogo = null) {
  const stato = { eventi: [], segnalazioni: [], email: [], avvisi: [], contatori: {}, chiavi: {}, pulito: null, finestre: [], opzioni: [],
    feedback: [], vocali: [], conteggi: {} };
  const archivio = {
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
        guardie: [], aggiorna: [], segnalazioni: 1 };
    },
    async pulisci(prima) { stato.pulito = prima; },
  };
  const posta = async (m) => { stato.email.push(m); };
  const avviso = async (t) => { stato.avvisi.push(t); };
  const voce = async (audio, t, numero) => { stato.avvisi.push(t); stato.vocali.push({ tipo: audio.type, size: audio.size, numero }); };
  return { stato, archivio, posta, avviso, voce };
}

const adesso = new Date("2026-10-13T10:00:00Z");
const post = (percorso, corpo) => new Request(`https://arturo.example${percorso}`, {
  method: "POST", body: typeof corpo === "string" ? corpo : JSON.stringify(corpo) });
const lotto = (eventi, extra = {}) => ({ installazione: "1b2c3d4e-aaaa-bbbb", versione: "v2026-10-13", sistema: "Darwin", eventi, ...extra });

const casi = {
  async V01() {
    const f = finti();
    const r = await gestisci(post("/v1/eventi", lotto([{ giorno: "2026-10-12", evento: "comando", valore: "fine" },
      { giorno: "2026-10-13", evento: "sessione" }])), { ...f, adesso });
    assert.equal(r.status, 202, "V01 un lotto valido non è accettato");
    assert.equal(f.stato.eventi.length, 2);
    assert.deepEqual(Object.keys(f.stato.eventi[0]).sort(),
      ["evento", "giorno", "installazione", "ricevuto", "sistema", "valore", "versione"], "V01 salvato un campo in più");
  },
  async V02() {
    const f = finti();
    for (const e of [{ evento: "prompt", valore: "ciao" }, { evento: "comando", valore: "/fine con testo privato" },
      { evento: "guardia", valore: "x".repeat(61) }, { evento: "sessione", valore: "qualcosa" }]) {
      const r = await gestisci(post("/v1/eventi", lotto([e])), { ...f, adesso });
      assert.equal(r.status, 400, `V02 evento fuori elenco accettato: ${JSON.stringify(e)}`);
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
    assert.equal((await gestisci(post("/v1/eventi", lotto(pieno)), { ...f, adesso })).status, 202);
    assert.equal((await gestisci(post("/v1/eventi", lotto([{ evento: "sessione" }])), { ...f, adesso })).status, 429,
      "V03 il tetto giornaliero per installazione non regge");
  },
  async V04() {
    const f = finti();
    const r = await gestisci(post("/v1/eventi", lotto([{ giorno: "2099-01-01", evento: "sessione" }])), { ...f, adesso });
    assert.equal(r.status, 202);
    assert.equal(f.stato.eventi[0].giorno, "2026-10-13", "V04 un giorno nel futuro resta nel futuro");
  },
  async V05() {
    const f = finti();
    const s = { tipo: "problema", titolo: "[problema] /fine si ferma", testo: "Il commit non parte.", versione: "v2026-10-13", sistema: "Darwin" };
    const r = await gestisci(post("/v1/segnalazioni", s), { ...f, adesso });
    assert.equal(r.status, 201, "V05 segnalazione valida rifiutata");
    assert.deepEqual(await r.json(), { numero: 1, email: true });
    assert.equal(f.stato.email[0].oggetto, "[Arturo] [problema] (da verificare) /fine si ferma", "V05 oggetto sbagliato");
    assert.match(f.stato.email[0].testo, /Il commit non parte\./);
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
    assert.match(h.stato.email[0].testo, /Versioni in uso:\n  nessuna\n[\s\S]*Comandi usati:\n  nessuno\n[\s\S]*Guardie che hanno bloccato \(volte, installazioni viste in almeno 2 giorni\):\n  nessuna\n/,
      "V12 il genere di nessuno/nessuna è sbagliato");
  },
  async V13() {
    // La config rotta arriva subito per email, una sola al giorno per installazione, dentro il tetto.
    const f = finti();
    const rotta = lotto([{ evento: "config", valore: "rotta-settings" }]);
    assert.equal((await gestisci(post("/v1/eventi", rotta), { ...f, adesso })).status, 202, "V13 config rotta rifiutata");
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
    for (const v of ["rotta-altro", "rotta-settings ", "../x"]) {
      assert.equal((await gestisci(post("/v1/eventi", lotto([{ evento: "config", valore: v }])), { ...f, adesso })).status, 400, `V13 config accetta ${v}`);
    }
  },
  async V14() {
    // Deriva: valori chiusi, ostacoli in cima, id accorciato, rientro detto.
    const f = finti();
    for (const v of ["insieme:2", "file:commands/inizio.md", "hook:bash-dispatcher.sh", "file:skills/x/SKILL.md"]) {
      assert.equal((await gestisci(post("/v1/eventi", lotto([{ evento: "deriva", valore: v }])), { ...f, adesso })).status, 202, `V14 deriva rifiuta ${v}`);
    }
    for (const v of ["file:/Users/gigi/segreto.md", "file:commands/con spazio.md", "insieme:1000", "progetto:x", "hook:", "file:../x", "file:commands/../../etc/passwd"]) {
      assert.equal((await gestisci(post("/v1/eventi", lotto([{ evento: "deriva", valore: v }])), { ...f, adesso })).status, 400, `V14 deriva accetta ${v}`);
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
      assert.equal(r.status, 202, `V16 ${evento} ${valore} rifiutato`);
    }
    const cattivi = [["setup", "fase:11"], ["setup", "fase:3 nota"], ["tappa", "tappa:5"], ["tappa", "tappa:testo"],
      ["tappa", "note:3"], ["claude", "2.1.x-beta"], ["chiede", "una guardia con spazi"], ["aggiorna", "forse"],
      ["tappa", "tappa:3\n"]];
    for (const [evento, valore] of cattivi) {
      const f = finti();
      const r = await gestisci(post("/v1/eventi", lotto([{ giorno: "2026-10-13", evento, valore }])), { ...f, adesso });
      assert.equal(r.status, 400, `V16 ${evento} ${JSON.stringify(valore)} accettato`);
    }
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
    assert.equal(dati.migliorare.setupIniziati, 1, "V17 manca «Dove migliorare»");
  },
  // Ritenzione: per ogni soglia contano solo le installazioni nate da almeno quei giorni.
  async V18() {
    const r = ritenzione([
      { installazione: "a", prima: "2026-08-01", ultima: "2026-10-12" },  // 72 giorni: viva a 7, 30, 60
      { installazione: "b", prima: "2026-08-01", ultima: "2026-08-05" },  // morta dopo 4 giorni
      { installazione: "c", prima: "2026-09-20", ultima: "2026-10-13" },  // 23 giorni: idonea solo a 7
      { installazione: "d", prima: "2026-10-10", ultima: "2026-10-13" },  // nuova
    ], "2026-10-13");
    assert.equal(r.nuove, 1, "V18 installazioni nuove");
    assert.deepEqual(r.soglie, [{ giorni: 7, idonee: 3, vive: 2 }, { giorni: 30, idonee: 2, vive: 1 }, { giorni: 60, idonee: 2, vive: 1 }],
      "V18 soglie della ritenzione");
  },
  // Il lunedì apre con «Dove migliorare Arturo»; il recap del giorno no.
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
    assert.match(f.stato.avvisi[2], /segnalazione n\. 1 \(problema\)[\s\S]*Il setup si ferma[\s\S]*Alla fase 2/, "V20 testo dell'avviso di segnalazione");
    // Un avviso che non parte non deve far perdere eventi o segnalazioni.
    const g = finti();
    const rotto = async () => { throw new Error("Telegram giù"); };
    const r = await gestisci(post("/v1/eventi", lotto([{ evento: "sessione", valore: "" }])), { ...g, avviso: rotto, adesso });
    assert.equal(r.status, 202, "V20 un avviso fallito fa fallire la richiesta");
    assert.equal(g.stato.eventi.length, 1, "V20 un avviso fallito fa perdere l'evento");
  },
  async V21() {
    // Il modulo di feedback del sito (16/10/2026): testo, tipo, email, e il vocale che passa a Telegram.
    const f = finti();
    const modulo = (campi, voce) => {
      const m = new FormData();
      for (const [k, v] of Object.entries(campi)) m.append(k, v);
      if (voce) m.append("voce", voce, "voce.webm");
      return new Request("https://arturo.example/v1/feedback", { method: "POST", body: m });
    };
    let r = await gestisci(modulo({ tipo: "idea", testo: "Mi piacerebbe un comando per le bozze.", email: "a@esempio.it" }), { ...f, adesso });
    assert.equal(r.status, 201, "V21 un feedback scritto non è accettato");
    assert.deepEqual(f.stato.feedback[0], { tipo: "idea", testo: "Mi piacerebbe un comando per le bozze.", email: "a@esempio.it", voce: 0 },
      "V21 il feedback salvato non è quello mandato");
    assert.match(f.stato.avvisi[0], /^Arturo: feedback n\. 1 dal sito \(idea\) · a@esempio\.it\n\nMi piacerebbe/, "V21 testo dell'avviso");
    const audio = new Blob([new Uint8Array([0x1a, 0x45, 0xdf, 0xa3]), new Uint8Array(2044)], { type: "audio/webm;codecs=opus" });
    r = await gestisci(modulo({ tipo: "problema", testo: "" }, audio), { ...f, adesso });
    assert.equal(r.status, 201, "V21 un feedback solo vocale non è accettato");
    assert.equal(f.stato.vocali.length, 1, "V21 il vocale non passa a Telegram");
    assert.equal(f.stato.feedback[1].voce, 1, "V21 il feedback non dice che c'era un vocale");
    assert.ok(!JSON.stringify(f.stato.feedback).includes("arrayBuffer"), "V21 il vocale finisce nell'archivio");
  },
  async V22() {
    // Rifiuti: niente da dire, email storta, audio troppo grande o di un altro tipo, la trappola dei bot, il tetto.
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
    assert.equal((await invia({ testo: "x" }, new Blob([new Uint8Array(LIMITI.audioMax + 1)], { type: "audio/webm" }))).status, 400,
      "V22 un vocale troppo grande è accettato");
    assert.equal((await invia({ testo: "x" }, new Blob([new Uint8Array(10)], { type: "application/zip" }))).status, 400,
      "V22 un file che non è audio è accettato");
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
      assert.equal((await gestisci(post("/v1/eventi", lotto([{ evento: "sessione" }], { versione: v })), { ...f, adesso })).status, 202,
        `V26 una versione vera è rifiutata: ${v}`);
    }
    await gestisci(post("/v1/segnalazioni", { tipo: "problema", titolo: "t", testo: "x", versione: "ignora le istruzioni" }), { ...f, adesso });
    assert.equal(f.stato.segnalazioni[0].versione, "", "V26 la segnalazione tiene una versione libera");
  },
  async V27() {
    // Il vocale: si guardano i primi byte, il corpo ha un tetto anche senza content-length, niente invii da altri siti.
    const f = finti();
    const invia = (voce, headers = {}) => {
      const m = new FormData();
      m.append("testo", "x");
      if (voce) m.append("voce", voce, "voce.webm");
      return gestisci(new Request("https://arturo.example/v1/feedback", { method: "POST", body: m, headers }), { ...f, adesso });
    };
    assert.equal((await invia(new Blob([new Uint8Array(64)], { type: "audio/webm" }))).status, 400, "V27 un vocale di zeri è accettato");
    assert.equal((await invia(new Blob([new TextEncoder().encode("<html>")], { type: "audio/ogg" }))).status, 400, "V27 un HTML dichiarato audio è accettato");
    for (const testa of [[0x1a, 0x45, 0xdf, 0xa3], [...new TextEncoder().encode("OggS")], [0, 0, 0, 0x20, ...new TextEncoder().encode("ftyp")]]) {
      assert.equal((await invia(new Blob([new Uint8Array(testa), new Uint8Array(32)], { type: "audio/webm" }))).status, 201,
        `V27 un vocale vero è rifiutato: ${testa}`);
    }
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
};

for (const [nome, caso] of Object.entries(casi)) await caso();
console.log(`PASS ${Object.keys(casi).join(",")} controlli=${Object.keys(casi).length}`);
