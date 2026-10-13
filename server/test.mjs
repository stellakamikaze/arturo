// Banco del server di Arturo (W-casi con la sigla V): logica.js con un archivio e una posta finti.
// Uso: node server/test.mjs   (esce con 0 se tutto passa)
import assert from "node:assert/strict";
import { gestisci, settimanale, mime, LIMITI, EVENTI } from "./logica.js";

function finti() {
  const stato = { eventi: [], segnalazioni: [], email: [], contatori: {}, pulito: null };
  const archivio = {
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
    async segnaEmail() {},
    async riepilogo() {
      return { installazioni: 2, sessioni: 5, versioni: [{ valore: "v2026-10-13", n: 2 }], sistemi: [], comandi: [{ valore: "fine", n: 3 }],
        guardie: [], aggiorna: [], segnalazioni: 1 };
    },
    async pulisci(prima) { stato.pulito = prima; },
  };
  const posta = async (m) => { stato.email.push(m); };
  return { stato, archivio, posta };
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
    assert.deepEqual(Object.keys(EVENTI), ["sessione", "comando", "guardia", "aggiorna", "segnalazione"]);
  },
  async V09() {
    const f = finti();
    assert.equal((await gestisci(new Request("https://arturo.example/v1/eventi"), { ...f, adesso })).status, 405);
    assert.equal((await gestisci(post("/altro", {}), { ...f, adesso })).status, 404);
    assert.equal((await gestisci(post("/v1/eventi", "{non json"), { ...f, adesso })).status, 400);
  },
};

for (const [nome, caso] of Object.entries(casi)) await caso();
console.log(`PASS ${Object.keys(casi).join(",")} controlli=${Object.keys(casi).length}`);
