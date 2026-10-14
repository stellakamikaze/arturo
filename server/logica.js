// La logica del server di Arturo, senza Cloudflare dentro: validazione, tetti, email, riepilogo.
// worker.js la collega a D1 e all'invio email; test.mjs la prova con node e un archivio finto.
//
// Cosa riceve il server, e solo questo:
//   POST /v1/eventi        un lotto di eventi d'uso, con un id di installazione casuale
//   POST /v1/segnalazioni  una segnalazione che la persona ha letto e approvato con /segnala
// L'IP non viene mai salvato. Gli eventi hanno il solo giorno, mai l'ora.

// L'elenco chiuso degli eventi. Lo stesso elenco sta in bin/telemetria.py e nel README:
// il banco M09 controlla che coincidano.
export const EVENTI = {
  sessione: /^$/,
  comando: /^[a-z0-9-]{1,40}$/,
  guardia: /^[a-z0-9_.-]{1,60}$/,
  aggiorna: /^(applicato|conflitto|fallito)$/,
  segnalazione: /^(problema|proposta|integrazione)$/,
  // La distanza fra la config della persona e quella di Arturo: un `insieme:<n>` apre l'elenco
  // corrente, seguito da n righe. Dei file esce solo il percorso dentro Arturo, che è pubblico.
  // Il percorso è relativo, senza "..", e comincia da una radice di Arturo o è un file della radice.
  deriva: /^(insieme:\d{1,3}|hook:[a-z0-9_.-]{1,60}|file:(?!.*\.\.)((agents|bin|commands|docs|hooks|server|shared|skills|templates|tests|\.github)\/[A-Za-z0-9_.\/-]{1,70}|[A-Za-z0-9_.-]{1,40}))$/,
  config: /^rotta-(settings|conflitto|rebase)$/,
};
export const TIPI = ["problema", "proposta", "integrazione"];
export const SISTEMI = ["Darwin", "Linux", "Windows", "altro"];
export const LIMITI = {
  corpoEventi: 64 * 1024,
  corpoSegnalazione: 20 * 1024,
  eventiPerLotto: 500,
  eventiPerGiorno: 500,
  eventiTotaliPerGiorno: 100000,
  segnalazioniPerGiorno: 200,
  emailPerGiorno: 40,
  guardieFrequenti: 5,
  conservazioneGiorni: 365,
};

const ID = /^[A-Za-z0-9-]{8,64}$/;
const GIORNO = /^\d{4}-\d{2}-\d{2}$/;

export function oggi(adesso = new Date()) {
  return adesso.toISOString().slice(0, 10);
}

function risposta(status, dati) {
  return new Response(JSON.stringify(dati), {
    status,
    headers: { "content-type": "application/json; charset=utf-8" },
  });
}

async function leggiJson(request, limite) {
  const testo = await request.text();
  if (new TextEncoder().encode(testo).length > limite) return { errore: risposta(413, { errore: "troppo grande" }) };
  try {
    return { dati: JSON.parse(testo) };
  } catch {
    return { errore: risposta(400, { errore: "JSON non valido" }) };
  }
}

function testoCorto(valore, massimo) {
  return typeof valore === "string" && valore.length <= massimo ? valore : null;
}

// Un lotto valido, oppure il motivo per cui non lo e'.
export function validaLotto(dati, giornoServer) {
  if (!dati || typeof dati !== "object") return { motivo: "corpo mancante" };
  const { installazione, versione, sistema, eventi } = dati;
  if (typeof installazione !== "string" || !ID.test(installazione)) return { motivo: "installazione non valida" };
  if (testoCorto(versione, 60) === null) return { motivo: "versione non valida" };
  if (!SISTEMI.includes(sistema)) return { motivo: "sistema non valido" };
  if (!Array.isArray(eventi) || eventi.length === 0 || eventi.length > LIMITI.eventiPerLotto) return { motivo: "eventi mancanti o troppi" };
  const righe = [];
  for (const e of eventi) {
    if (!e || typeof e !== "object") return { motivo: "evento non valido" };
    const regola = EVENTI[e.evento];
    const valore = e.valore ?? "";
    if (!regola || typeof valore !== "string" || !regola.test(valore)) return { motivo: `evento fuori elenco: ${String(e.evento).slice(0, 30)}` };
    // Un giorno nel futuro o malformato diventa il giorno del server.
    const giorno = typeof e.giorno === "string" && GIORNO.test(e.giorno) && e.giorno <= giornoServer ? e.giorno : giornoServer;
    righe.push({ giorno, installazione, versione, sistema, evento: e.evento, valore });
  }
  return { righe };
}

export function validaSegnalazione(dati) {
  if (!dati || typeof dati !== "object") return { motivo: "corpo mancante" };
  const tipo = TIPI.includes(dati.tipo) ? dati.tipo : null;
  const titolo = testoCorto(dati.titolo, 200);
  const testo = testoCorto(dati.testo, 16000);
  if (!tipo || !titolo || !titolo.trim() || !testo || !testo.trim()) return { motivo: "tipo, titolo o testo non validi" };
  const installazione = typeof dati.installazione === "string" && ID.test(dati.installazione) ? dati.installazione : "";
  return {
    segnalazione: {
      tipo,
      titolo: titolo.trim(),
      testo,
      versione: testoCorto(dati.versione, 60) || "",
      sistema: SISTEMI.includes(dati.sistema) ? dati.sistema : "altro",
      installazione,
    },
  };
}

// --- email -------------------------------------------------------------------

function base64(testo) {
  const byte = new TextEncoder().encode(testo);
  let binario = "";
  for (const b of byte) binario += String.fromCharCode(b);
  return btoa(binario).replace(/.{76}/g, "$&\r\n");
}

function intestazione(testo) {
  // RFC 2047: un oggetto con accenti passa intatto.
  return /^[\x20-\x7e]*$/.test(testo) ? testo : `=?UTF-8?B?${btoa(String.fromCharCode(...new TextEncoder().encode(testo)))}?=`;
}

export function mime({ da, a, oggetto, testo, adesso = new Date(), id = crypto.randomUUID() }) {
  const dominio = da.split("@")[1];
  return [
    `From: Arturo <${da}>`,
    `To: ${a}`,
    `Subject: ${intestazione(oggetto.replace(/[\r\n]+/g, " "))}`,
    `Date: ${adesso.toUTCString()}`,
    `Message-ID: <${id}@${dominio}>`,
    "MIME-Version: 1.0",
    "Content-Type: text/plain; charset=utf-8",
    "Content-Transfer-Encoding: base64",
    "",
    base64(testo),
  ].join("\r\n");
}

export function emailSegnalazione(s, numero) {
  const oggetto = `[Arturo] [${s.tipo}] ${s.titolo.replace(/^\[(problema|proposta|integrazione)\]\s*/i, "")}`;
  const testo = `${s.testo}\n\n---\nSegnalazione n. ${numero} · Arturo ${s.versione || "?"} · ${s.sistema}` +
    (s.installazione ? ` · installazione ${s.installazione}` : "") + "\n";
  return { oggetto, testo };
}

export function emailConfigRotta(installazione, valore, versione) {
  return {
    oggetto: "[Arturo] Config rotta su un'installazione",
    testo: `Un'installazione di Arturo ha la config rotta (${valore.replace("rotta-", "")}): le guardie possono non girare.\n\n` +
      `Installazione ${installazione.slice(0, 8)} · Arturo ${versione}\n`,
  };
}

const corto = (id) => id.slice(0, 8);

// Per ogni installazione l'elenco corrente della deriva. È un ostacolo se un hook di Arturo è
// spento, se una guardia (hooks/) è modificata, o se un file di Arturo modificato sta insieme a un
// aggiornamento finito in conflitto.
export function testoDeriva(deriva) {
  if (!deriva || !deriva.length) return ["  nessuna"];
  const righe = [];
  for (const d of deriva) {
    const hook = d.valori.filter((v) => v.startsWith("hook:")).map((v) => v.slice(5));
    const file = d.valori.filter((v) => v.startsWith("file:")).map((v) => v.slice(5));
    if (!hook.length && !file.length) { righe.push(`  ${corto(d.installazione)}  rientrata: nessuna differenza che conti`); continue; }
    if (hook.length) righe.push(`  ${corto(d.installazione)}  OSTACOLO, hook di Arturo spenti: ${hook.join(", ")}`);
    const guardie = file.filter((f) => f.startsWith("hooks/"));
    const altri = file.filter((f) => !f.startsWith("hooks/"));
    if (guardie.length) righe.push(`  ${corto(d.installazione)}  OSTACOLO, guardie di Arturo modificate: ${guardie.join(", ")}`);
    if (altri.length) {
      righe.push(`  ${corto(d.installazione)}  ${d.conflitto ? "OSTACOLO, aggiornamento in conflitto, " : ""}file di Arturo modificati: ${altri.join(", ")}`);
    }
  }
  return righe.sort((a, b) => Number(b.includes("OSTACOLO")) - Number(a.includes("OSTACOLO")));
}

export function testoRiepilogo(r, titolo) {
  const elenco = (righe, vuoto = "nessuno") => righe.length ? righe.map((x) => `  ${x.n}  ${x.valore || "(vuoto)"}`).join("\n") : `  ${vuoto}`;
  const frequenti = r.guardieFrequenti
    ? ["", `Guardie frequenti (almeno ${LIMITI.guardieFrequenti} blocchi nella settimana sulla stessa installazione):`,
      r.guardieFrequenti.length ? r.guardieFrequenti.map((x) => `  ${x.n}  ${x.valore} su ${corto(x.installazione)}`).join("\n") : "  nessuna"]
    : [];
  return [
    titolo,
    "",
    `Installazioni attive: ${r.installazioni}`,
    `Sessioni: ${r.sessioni}`,
    "",
    "Config rotte:", elenco(r.config || [], "nessuna"),
    "", "Deriva dalla config di Arturo:", ...testoDeriva(r.deriva),
    "",
    "Versioni in uso:", elenco(r.versioni, "nessuna"),
    "", "Sistemi:", elenco(r.sistemi),
    "", "Comandi usati:", elenco(r.comandi),
    "", "Guardie che hanno bloccato:", elenco(r.guardie, "nessuna"),
    "", "Esiti di /aggiorna:", elenco(r.aggiorna),
    ...frequenti,
    "", `Segnalazioni ricevute: ${r.segnalazioni}`,
    "",
  ].join("\n");
}

// --- i gestori -----------------------------------------------------------------
// `archivio` e `posta` arrivano da worker.js (D1 e send_email) o da test.mjs (finti).

export async function gestisci(request, { archivio, posta, adesso = new Date() }) {
  const url = new URL(request.url);
  if (request.method === "GET" && url.pathname === "/") {
    return new Response("Arturo: qui arrivano eventi d'uso anonimi e segnalazioni. Codice: https://github.com/stellakamikaze/arturo/tree/main/server\n",
      { headers: { "content-type": "text/plain; charset=utf-8" } });
  }
  if (request.method !== "POST") return risposta(405, { errore: "solo POST" });
  const giorno = oggi(adesso);

  if (url.pathname === "/v1/eventi") {
    const { dati, errore } = await leggiJson(request, LIMITI.corpoEventi);
    if (errore) return errore;
    const { righe, motivo } = validaLotto(dati, giorno);
    if (motivo) return risposta(400, { errore: motivo });
    const gia = await archivio.contaEventi(righe[0].installazione, giorno);
    if (gia + righe.length > LIMITI.eventiPerGiorno) return risposta(429, { errore: "troppi eventi oggi" });
    if (await archivio.contaEventi(null, giorno) + righe.length > LIMITI.eventiTotaliPerGiorno) {
      return risposta(429, { errore: "server pieno per oggi" });
    }
    await archivio.scriviEventi(righe, adesso.toISOString());
    // Una config rotta arriva subito per email: una sola al giorno per installazione.
    const rotta = righe.find((x) => x.evento === "config");
    if (rotta && await archivio.primaVolta(giorno, `rotta:${rotta.installazione}`) && await archivio.prendiEmail(giorno, LIMITI.emailPerGiorno)) {
      try {
        await posta(emailConfigRotta(rotta.installazione, rotta.valore, rotta.versione));
      } catch (e) {
        console.log("email non partita", e && e.message);
      }
    }
    return risposta(202, { ricevuti: righe.length });
  }

  if (url.pathname === "/v1/segnalazioni") {
    const { dati, errore } = await leggiJson(request, LIMITI.corpoSegnalazione);
    if (errore) return errore;
    const { segnalazione, motivo } = validaSegnalazione(dati);
    if (motivo) return risposta(400, { errore: motivo });
    if (await archivio.contaSegnalazioni(giorno) >= LIMITI.segnalazioniPerGiorno) {
      return risposta(429, { errore: "troppe segnalazioni oggi" });
    }
    const numero = await archivio.salvaSegnalazione(segnalazione, adesso.toISOString());
    let email = false;
    if (await archivio.prendiEmail(giorno, LIMITI.emailPerGiorno)) {
      try {
        await posta(emailSegnalazione(segnalazione, numero));
        email = true;
        await archivio.segnaEmail(numero);
      } catch (e) {
        console.log("email non partita", e && e.message);
      }
    }
    return risposta(201, { numero, email });
  }

  return risposta(404, { errore: "percorso sconosciuto" });
}

const giorniFa = (adesso, n) => oggi(new Date(adesso.getTime() - n * 86400000));

// Il recap del giorno prima. Nei giorni senza eventi né segnalazioni non parte (14/10/2026,
// Federico): un'email di zeri ogni mattina insegna a non leggerla. Il segno di vita del server
// è il riepilogo del lunedì, che parte sempre: se manca quello, il Worker è fermo.
export async function giornaliero({ archivio, posta, adesso = new Date() }) {
  const ieri = giorniFa(adesso, 1);
  const r = await archivio.riepilogo(giorniFa(adesso, 2), ieri);
  if (!r.installazioni && !r.segnalazioni) return;
  await posta({ oggetto: `[Arturo] Recap del ${ieri}`, testo: testoRiepilogo(r, `Arturo, il giorno ${ieri}`) });
}

export async function settimanale({ archivio, posta, adesso = new Date() }) {
  const al = oggi(adesso);
  const dal = giorniFa(adesso, 7);
  const r = await archivio.riepilogo(dal, al, { settimana: true });
  await posta({ oggetto: `[Arturo] Riepilogo della settimana ${dal} - ${al}`, testo: testoRiepilogo(r, `Arturo, settimana dal ${dal} al ${al}`) });
  await archivio.pulisci(giorniFa(adesso, LIMITI.conservazioneGiorni));
}

// Il cron gira ogni mattina alle 6 UTC: il recap del giorno prima se c'è qualcosa, il lunedì sempre la settimana.
export async function programmato({ archivio, posta, adesso = new Date() }) {
  await giornaliero({ archivio, posta, adesso });
  if (adesso.getUTCDay() === 1) await settimanale({ archivio, posta, adesso });
}
