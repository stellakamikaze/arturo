// Banco del server di Arturo (W-casi con la sigla V): logica.js con un archivio e una posta finti.
// Uso: node server/test.mjs   (esce con 0 se tutto passa)
import assert from "node:assert/strict";
import { gestisci, settimanale, giornaliero, programmato, mime, testoDeriva, ritenzione, LIMITI, EVENTI } from "./logica.js";

const VUOTO = { installazioni: 0, sessioni: 0, versioni: [], sistemi: [], comandi: [], guardie: [], aggiorna: [], config: [], deriva: [],
  guardieFrequenti: null, segnalazioni: 0 };

function finti(riepilogo = null) {
  const stato = { eventi: [], segnalazioni: [], email: [], avvisi: [], contatori: {}, chiavi: {}, pulito: null, finestre: [], opzioni: [] };
  const archivio = {
    async installazioneNuova(inst) { return !stato.eventi.some((e) => e.installazione === inst); },
    async contaEventi(inst, giorno) {
      return stato.eventi.filter((e) => e.ricevuto === giorno && (!inst || e.installazione === inst)).length;
    },
    async scriviEventi(righe, ricevuto) {
      for (const r of righe) stato.eventi.push({ ...r, ricevuto: ricevuto.slice(0, 10) });
    },
    async contaSegnalazioni() { return stato.segnalazioni.length; },
    async salvaSegnalazione(s) { stato.segnalazioni.push(s); return stato.segnalazioni.length; },
    async prendiEmail(giorno, massimo) {
      stato.contatori[giorno] = (stato.contatori[giorno] || 0) + 1;
      return stato.contatori[giorno] <= massimo;
    },
    async primaVolta(giorno, chiave) {
      const k = `${giorno} ${chiave}`;
      stato.chiavi[k] = (stato.chiavi[k] || 0) + 1;
      return stato.chiavi[k] === 1;
    },
    async segnaEmail() {},
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
  return { stato, archivio, posta, avviso };
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
    assert.equal(f.stato.email[0].oggetto, "[Arturo] [problema] /fine si ferma", "V05 oggetto sbagliato");
    assert.match(f.stato.email[0].testo, /Il commit non parte\./);
    for (const cattiva of [{ ...s, tipo: "spam" }, { ...s, titolo: "" }, { ...s, testo: "x".repeat(16001) }]) {
      assert.equal((await gestisci(post("/v1/segnalazioni", cattiva), { ...f, adesso })).status, 400, "V05 segnalazione non valida accettata");
    }
  },
  async V06() {
    const f = finti();
    const s = { tipo: "proposta", titolo: "t", testo: "x" };
    for (let i = 0; i < LIMITI.emailPerGiorno + 3; i++) await gestisci(post("/v1/segnalazioni", s), { ...f, adesso });
    assert.equal(f.stato.segnalazioni.length, LIMITI.emailPerGiorno + 3, "V06 oltre il tetto email la segnalazione non è salvata");
    assert.equal(f.stato.email.length, LIMITI.emailPerGiorno, "V06 il tetto delle email non regge");
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
    assert.match(h.stato.email[0].testo, /Versioni in uso:\n  nessuna\n[\s\S]*Comandi usati:\n  nessuno\n[\s\S]*Guardie che hanno bloccato:\n  nessuna\n/,
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
    g.stato.contatori["2026-10-13"] = LIMITI.emailPerGiorno;
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
    const migliorare = { setupIniziati: 3, setupFiniti: 1, setupFermi: [{ valore: "fase:2", n: 2 }],
      conferme: [{ valore: "exfil-guard.py", chiede: 10, confermata: 9 }], errori: [], aggiornaStorti: [],
      ritenzione: { nuove: 1, soglie: [{ giorni: 60, idonee: 4, vive: 1 }] }, claude: [] };
    const f = finti({ ...VUOTO, migliorare });
    await settimanale({ ...f, adesso });
    const testo = f.stato.email[0].testo;
    assert.ok(testo.indexOf("DOVE MIGLIORARE ARTURO") < testo.indexOf("Installazioni attive"), "V19 la sezione non viene prima");
    assert.match(testo, /Setup: 3 iniziati, 1 arrivati in fondo[^\n]*\n  2  fase:2\n/, "V19 setup fermi");
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
};

for (const [nome, caso] of Object.entries(casi)) await caso();
console.log(`PASS ${Object.keys(casi).join(",")} controlli=${Object.keys(casi).length}`);
