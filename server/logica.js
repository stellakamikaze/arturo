// La logica del server di Arturo, senza Cloudflare dentro: validazione, tetti, email, riepilogo.
// worker.js la collega a D1 e all'invio email; test.mjs la prova con node e un archivio finto.
//
// Cosa riceve il server, e solo questo:
//   POST /v1/eventi        un lotto di eventi d'uso, con un id di installazione casuale
//   POST /v1/segnalazioni  una segnalazione che la persona ha letto e approvato con /segnala
//   POST /v1/feedback      il modulo di feedback del sito (/api/feedback), anche con un vocale:
//                          il testo resta in D1, il vocale va solo a Telegram
//   POST /v1/sito          un download dal sito (/api/sito): il comando copiato o il repository aperto
// Cosa dà, solo a chi ha il token (secret RIEPILOGO_TOKEN):
//   GET  /v1/riepilogo     il riepilogo della settimana in JSON, con "Dove migliorare Arturo"
// L'IP non viene mai salvato. Gli eventi hanno il solo giorno, mai l'ora.

// L'elenco chiuso degli eventi. Lo stesso elenco sta in bin/telemetria.py e nel README:
// il banco M09 controlla che coincidano, salvo gli eventi vecchi che il client non manda più.
export const EVENTI = {
  sessione: /^$/,
  comando: /^[a-z0-9-]{1,40}$/,
  guardia: /^[a-z0-9_.-]{1,60}$/,
  aggiorna: /^(applicato|conflitto|fallito|rifiutato|indietro|scartato|automatico|rinviato|bloccato-firma|bloccato-verifica|bloccato-storia|bloccato-versione|manuale)$/,
  segnalazione: /^(problema|proposta|integrazione)$/,
  // La distanza fra la config della persona e quella di Arturo: un `insieme:<n>` apre l'elenco
  // corrente, seguito da n righe. Dei file esce solo il percorso dentro Arturo, che è pubblico.
  // Il percorso è relativo, senza "..", e comincia da una radice di Arturo o è un file della radice.
  deriva: /^(insieme:\d{1,3}|hook:[a-z0-9_.-]{1,60}|file:(?!.*\.\.)((agents|bin|commands|docs|firme|hooks|output-styles|server|shared|skills|templates|tests|tools|\.github)\/[A-Za-z0-9_.\/-]{1,70}|[A-Za-z0-9_.-]{1,40}))$/,
  config: /^rotta-(settings|conflitto|rebase|hook)$/,
  // Dal 15/10/2026, per il miglioramento di Arturo. In coda, nello stesso ordine di bin/telemetria.py.
  setup: /^(fase:(10|[0-9][a-z]?)|fine)$/,
  chiede: /^[a-z0-9_.-]{1,60}$/,
  confermata: /^[a-z0-9_.-]{1,60}$/,
  errore: /^[a-z0-9_.-]{1,60}$/,
  claude: /^\d{1,3}\.\d{1,3}\.\d{1,4}$/,
  // Eventi vecchi: il client non li manda più, ma un client non aggiornato sì. Restano accettati
  // perché validaLotto rifiuta il lotto intero per un evento fuori elenco. Da togliere dopo qualche
  // settimana, insieme al loro posto in M09 (tests/test_telemetria.py).
  // tappa: tolta dal client il 16/10/2026 con il percorso a tappe. Per la stessa ragione `deriva`
  // accetta ancora la radice templates/, tolta dal client il 16/10/2026: esce con tappa (#3435).
  tappa: /^(tappa:[0-4]|(decisioni|limiti|tenuti|proposte|rifiutate):\d{1,4})$/,
};
// Le soglie della ritenzione: installazioni ancora vive dopo 7, 30 e 60 giorni dalla prima volta.
// Sessanta giorni è il criterio di successo di Arturo (uso vivo dopo due mesi).
export const RITENZIONE = [7, 30, 60];
export const TIPI = ["problema", "proposta", "integrazione"];
export const SISTEMI = ["Darwin", "Linux", "Windows", "altro"];
export const LIMITI = {
  corpoEventi: 64 * 1024,
  corpoSegnalazione: 20 * 1024,
  eventiPerLotto: 500,
  eventiPerGiorno: 500,
  eventiTotaliPerGiorno: 100000,
  segnalazioniPerGiorno: 200,
  // Due tetti separati (16/10/2026): le segnalazioni, che chiunque può mandare, non consumano le
  // email delle config rotte.
  emailRottePerGiorno: 20,
  emailSegnalazioniPerGiorno: 20,
  // Gli avvisi su Telegram che un POST anonimo può far partire: oltre il tetto il dato si salva, il
  // messaggio no (review di sicurezza del 16/10/2026).
  avvisiInstallazioniPerGiorno: 20,
  avvisiSetupPerGiorno: 20,
  avvisiSegnalazioniPerGiorno: 30,
  // Una data dichiarata dal client più vecchia di così diventa il giorno del server.
  giorniIndietro: 7,
  guardieFrequenti: 5,
  // Le statistiche delle guardie contano solo installazioni viste in almeno tanti giorni diversi (#3507).
  giorniGuardie: 2,
  conservazioneGiorni: 365,
  // Il sito (16/10/2026): il modulo di feedback, anche con un vocale, e i download.
  feedbackPerGiorno: 100,
  feedbackTesto: 4000,
  feedbackCorpo: 5 * 1024 * 1024,
  audioMax: 4 * 1024 * 1024,
  sitoPerGiorno: 60,
};

const FEEDBACK_TIPI = ["problema", "idea", "installazione", "altro"];
const SITO_TIPI = ["download", "github"];
const SITO_SISTEMI = ["mac", "win", ""];

const ID = /^[A-Za-z0-9-]{8,64}$/;
const GIORNO = /^\d{4}-\d{2}-\d{2}$/;
// La versione è l'ultimo tag v* raggiungibile (`git describe --tags --abbrev=0`, bin/telemetria.py), oppure "sconosciuta".
// Niente testo libero: finisce nel riepilogo che legge la routine del lunedì.
const VERSIONE = /^[A-Za-z0-9._+-]{1,60}$/;

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
  if (typeof versione !== "string" || !VERSIONE.test(versione)) return { motivo: "versione non valida" };
  if (!SISTEMI.includes(sistema)) return { motivo: "sistema non valido" };
  if (!Array.isArray(eventi) || eventi.length === 0 || eventi.length > LIMITI.eventiPerLotto) return { motivo: "eventi mancanti o troppi" };
  const righe = [];
  const minimo = giorniFa(new Date(`${giornoServer}T12:00:00Z`), LIMITI.giorniIndietro);
  for (const e of eventi) {
    if (!e || typeof e !== "object") return { motivo: "evento non valido" };
    const regola = EVENTI[e.evento];
    const valore = e.valore ?? "";
    if (!regola || typeof valore !== "string" || !regola.test(valore)) return { motivo: `evento fuori elenco: ${String(e.evento).slice(0, 30)}` };
    // Un giorno nel futuro, troppo vecchio o malformato diventa il giorno del server.
    const giorno = typeof e.giorno === "string" && GIORNO.test(e.giorno) && e.giorno <= giornoServer && e.giorno >= minimo
      ? e.giorno : giornoServer;
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
      versione: typeof dati.versione === "string" && VERSIONE.test(dati.versione) ? dati.versione : "",
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
  const oggetto = `[Arturo] [${s.tipo}] (da verificare) ${s.titolo.replace(/^\[(problema|proposta|integrazione)\]\s*/i, "")}`;
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
const giorni = (a, b) => Math.round((Date.parse(b) - Date.parse(a)) / 86400000);

// Da {installazione, prima, ultima} ai numeri della ritenzione. Per ogni soglia contano solo le
// installazioni nate da almeno quei giorni: una nata ieri non può essere viva a 30 giorni.
export function ritenzione(righe, al) {
  const fuori = { nuove: righe.filter((x) => giorni(x.prima, al) < 7).length, soglie: [] };
  for (const n of RITENZIONE) {
    const idonee = righe.filter((x) => giorni(x.prima, al) >= n);
    fuori.soglie.push({ giorni: n, idonee: idonee.length, vive: idonee.filter((x) => giorni(x.prima, x.ultima) >= n).length });
  }
  return fuori;
}

// Viaggia col riepilogo in JSON: la routine che propone correzioni la legge insieme ai numeri (#3507).
export const REGOLA_GUARDIE = "Una guardia non si allenta sulla sola base della telemetria anonima: gli id sono casuali e " +
  "chiunque può crearne. Le statistiche delle guardie contano solo installazioni viste in almeno " +
  `${LIMITI.giorniGuardie} giorni diversi, e ogni numero dice quante installazioni lo producono.`;

const installazioni = (n) => `${n || 0} ${n === 1 ? "installazione" : "installazioni"}`;

// "Dove migliorare Arturo": la prima cosa del riepilogo del lunedì. Numeri, non verdetti.
export function testoMigliorare(m) {
  if (!m) return [];
  const righe = (elenco, riga, vuoto = "  niente") => elenco && elenco.length ? elenco.map(riga) : [vuoto];
  const per = (a, b) => (b ? `${Math.round((100 * a) / b)}%` : "-");
  const conferma = (x) => `  ${x.valore}  ${x.chiede} / ${x.confermata} / ${per(x.confermata, x.chiede)}, ${installazioni(x.installazioni)}`;
  const r = m.ritenzione || { nuove: 0, soglie: [] };
  return [
    "DOVE MIGLIORARE ARTURO (ultimi 30 giorni, numeri e non verdetti)",
    "",
    `Setup: ${m.setupIniziati || 0} iniziati, ${m.setupFiniti || 0} arrivati in fondo, ${m.setupMai || 0} installazioni nuove che non l'hanno mai lanciato. Fermi da più di 3 giorni, per ultima fase vista:`,
    ...righe(m.setupFermi, (x) => `  ${x.n}  ${x.valore}`, "  nessuno"),
    "",
    `Guardie: contano solo le installazioni viste in almeno ${LIMITI.giorniGuardie} giorni diversi. Una guardia non si allenta sulla sola base di questi numeri.`,
    "Guardie che chiedono conferma (chiede / confermata / quota di sì, installazioni):",
    ...righe(m.confermeGuardie || m.conferme, conferma, "  nessuna"),
    "Per regola, dove la guardia la dice:",
    ...righe((m.conferme || []).filter((x) => x.valore.includes(".py.")), conferma, "  nessuna"),
    "",
    "Guardie che si rompono (volte, installazioni):",
    ...righe(m.errori, (x) => `  ${x.valore}  ${x.n}, ${installazioni(x.installazioni)}`, "  nessuna"),
    "",
    "Aggiornamenti non applicati (versione, esito, volte):",
    ...righe(m.aggiornaStorti, (x) => `  ${x.versione}  ${x.valore}  ${x.n}`, "  nessuno"),
    "",
    `Ritenzione: ${r.nuove} installazioni nuove negli ultimi 7 giorni.`,
    ...r.soglie.map((s) => `  vive dopo ${s.giorni} giorni: ${s.vive} su ${s.idonee} (${per(s.vive, s.idonee)})`),
    "",
    "Versioni di Claude Code (installazioni):",
    ...righe(m.claude, (x) => `  ${x.n}  ${x.valore}`, "  nessun dato"),
    "",
    "---",
    "",
  ];
}

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
    ...testoMigliorare(r.migliorare),
    `Installazioni attive: ${r.installazioni}`,
    `Sessioni: ${r.sessioni}`,
    "",
    "Config rotte:", elenco(r.config || [], "nessuna"),
    "", "Deriva dalla config di Arturo:", ...testoDeriva(r.deriva),
    "",
    "Versioni in uso:", elenco(r.versioni, "nessuna"),
    "", "Sistemi:", elenco(r.sistemi),
    "", "Comandi usati:", elenco(r.comandi),
    "", `Guardie che hanno bloccato (volte, installazioni viste in almeno ${LIMITI.giorniGuardie} giorni):`,
    r.guardie.length ? r.guardie.map((x) => `  ${x.n}  ${x.valore || "(vuoto)"}, ${installazioni(x.installazioni)}`).join("\n") : "  nessuna",
    "", "Esiti di /aggiorna:", elenco(r.aggiorna),
    ...frequenti,
    "", `Segnalazioni ricevute: ${r.segnalazioni}`,
    "",
  ].join("\n");
}

// --- i gestori -----------------------------------------------------------------
// `archivio` e `posta` arrivano da worker.js (D1 e send_email) o da test.mjs (finti).

const giorniFa = (adesso, n) => oggi(new Date(adesso.getTime() - n * 86400000));

// Confronto a tempo costante: il token non si indovina un carattere alla volta.
function stessoToken(dato, atteso) {
  if (typeof dato !== "string" || typeof atteso !== "string" || atteso.length < 32) return false;
  const a = new TextEncoder().encode(dato);
  const b = new TextEncoder().encode(atteso);
  let diverso = a.length ^ b.length;
  for (let i = 0; i < b.length; i++) diverso |= (a[i] ?? 0) ^ b[i];
  return diverso === 0;
}

// Gli avvisi su Telegram a chi mantiene Arturo: un'installazione nuova, una segnalazione. Il testo non porta
// niente più di quello che il server già salva (installazione abbreviata, versione, sistema, titolo).
export function avvisoInstallazione(riga) {
  return `Arturo: installazione nuova (${riga.installazione.slice(0, 8)}) · ${riga.versione} · ${riga.sistema}`;
}

export function avvisoSegnalazione(s, numero) {
  const titolo = s.titolo.replace(/^\[(problema|proposta|integrazione)\]\s*/i, "");
  const testo = s.testo.length > 600 ? s.testo.slice(0, 600) + "…" : s.testo;
  return `Arturo: segnalazione n. ${numero} (${s.tipo}) · ${s.versione || "?"} · ${s.sistema}\n${titolo}\n\n${testo}`;
}

export function avvisoSetupFinito(riga) {
  return `Arturo: setup finito (${riga.installazione.slice(0, 8)}) · ${riga.versione} · ${riga.sistema}`;
}

export function avvisoFeedback(f, numero) {
  const testo = f.testo.length > 1500 ? f.testo.slice(0, 1500) + "…" : f.testo;
  return `Arturo: feedback n. ${numero} dal sito (${f.tipo})${f.email ? ` · ${f.email}` : ""}${f.voce ? " · con un vocale" : ""}`
    + (testo ? `\n\n${testo}` : "");
}

export function avvisoSito(e, n) {
  const cosa = e.tipo === "download" ? "qualcuno ha copiato il comando di installazione" : "qualcuno ha aperto il repository su GitHub";
  const dove = [e.pagina, e.sistema === "mac" ? "Mac" : e.sistema === "win" ? "Windows" : ""].filter(Boolean).join(", ");
  return `Arturo: ${cosa}${dove ? ` (${dove})` : ""} · ${n}° di oggi`;
}

// Il modulo del sito: testo, tipo, email facoltativa, un vocale facoltativo. Il campo "sito" è una
// trappola invisibile: una persona lo lascia vuoto, un bot lo riempie.
export function validaFeedback(modulo) {
  const campo = (nome) => {
    const v = modulo.get(nome);
    return typeof v === "string" ? v.trim() : "";
  };
  if (campo("sito")) return { trappola: true };
  const testo = campo("testo");
  if (testo.length > LIMITI.feedbackTesto) return { motivo: "testo troppo lungo" };
  const tipo = FEEDBACK_TIPI.includes(campo("tipo")) ? campo("tipo") : "altro";
  const email = campo("email");
  if (email && (email.length > 200 || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email))) return { motivo: "email non valida" };
  const v = modulo.get("voce");
  const audio = v && typeof v === "object" && typeof v.arrayBuffer === "function" && v.size > 0 ? v : null;
  if (audio && audio.size > LIMITI.audioMax) return { motivo: "vocale troppo lungo" };
  if (audio && !/^(audio|video)\/(webm|ogg|mp4|mpeg|x-m4a|aac|wav)/.test(audio.type || "")) return { motivo: "formato del vocale non riconosciuto" };
  if (!testo && !audio) return { motivo: "scrivi qualcosa o registra un vocale" };
  return { feedback: { tipo, testo, email, voce: audio ? 1 : 0 }, audio };
}

// Il tipo del vocale lo dichiara il browser: si guarda anche l'inizio del file. WebM (EBML), Ogg,
// MP4 e M4A (ftyp a 4 byte dall'inizio), MP3 (ID3 o sincronia MPEG), WAV (RIFF).
export async function audioVero(audio) {
  const b = new Uint8Array(await audio.slice(0, 12).arrayBuffer());
  const ascii = (da, a) => String.fromCharCode(...b.slice(da, a));
  return (b[0] === 0x1a && b[1] === 0x45 && b[2] === 0xdf && b[3] === 0xa3)
    || ascii(0, 4) === "OggS"
    || ascii(4, 8) === "ftyp"
    || ascii(0, 3) === "ID3" || (b[0] === 0xff && (b[1] & 0xe0) === 0xe0)
    || ascii(0, 4) === "RIFF";
}

// Legge il corpo con un tetto, anche quando manca content-length (invio a pezzi): null se lo supera.
async function corpoLimitato(request, limite) {
  if (!request.body) return new Uint8Array(0);
  const lettore = request.body.getReader();
  const pezzi = [];
  let totale = 0;
  for (;;) {
    const { done, value } = await lettore.read();
    if (done) break;
    totale += value.length;
    if (totale > limite) {
      await lettore.cancel();
      return null;
    }
    pezzi.push(value);
  }
  const tutto = new Uint8Array(totale);
  let i = 0;
  for (const p of pezzi) { tutto.set(p, i); i += p.length; }
  return tutto;
}

export function validaSito(dati) {
  if (!dati || typeof dati !== "object") return { motivo: "corpo mancante" };
  const tipo = SITO_TIPI.includes(dati.tipo) ? dati.tipo : null;
  const pagina = typeof dati.pagina === "string" && /^\/[a-z0-9/-]{0,40}$/.test(dati.pagina) ? dati.pagina : null;
  const sistema = SITO_SISTEMI.includes(dati.sistema || "") ? (dati.sistema || "") : null;
  if (!tipo || pagina === null || sistema === null) return { motivo: "evento del sito non valido" };
  return { evento: { tipo, pagina, sistema } };
}

async function avvisa(avviso, testo) {
  try {
    await avviso(testo);
  } catch (e) {
    console.log("avviso non partito", e && e.message);
  }
}

// `limite(tipo, request)` è il limite per IP del Worker (binding Rate Limiting): falso quando la
// richiesta va oltre. Senza binding, come nei test e in un fork che non lo configura, lascia passare.
export async function gestisci(request, { archivio, posta, avviso = async () => {}, voce = null, adesso = new Date(), token,
  limite = async () => true }) {
  const url = new URL(request.url);
  if (request.method === "GET" && url.pathname === "/") {
    return new Response("Arturo: qui arrivano eventi d'uso, con un id casuale e senza contenuti, e segnalazioni. Codice: https://github.com/stellakamikaze/arturo/tree/main/server\n",
      { headers: { "content-type": "text/plain; charset=utf-8" } });
  }
  // Il riepilogo in JSON, per chi mantiene Arturo: lo legge la routine del lunedì che propone le correzioni.
  if (request.method === "GET" && url.pathname === "/v1/riepilogo") {
    const dato = (request.headers.get("authorization") || "").replace(/^Bearer /, "");
    if (!stessoToken(dato, token)) return risposta(401, { errore: "token mancante o sbagliato" });
    const al = GIORNO.test(url.searchParams.get("al") || "") ? url.searchParams.get("al") : oggi(adesso);
    const dal = GIORNO.test(url.searchParams.get("dal") || "") ? url.searchParams.get("dal") : giorniFa(new Date(`${al}T12:00:00Z`), 7);
    return risposta(200, { dal, al, regola: REGOLA_GUARDIE, ...(await archivio.riepilogo(dal, al, { settimana: true })) });
  }
  if (request.method !== "POST") return risposta(405, { errore: "solo POST" });
  const giorno = oggi(adesso);
  // Il modulo e i download arrivano solo dalla landing: un altro sito non li fa inviare ai suoi visitatori.
  const daFuori = (request.headers.get("sec-fetch-site") || "") === "cross-site";

  if (url.pathname === "/v1/eventi") {
    if (!await limite("eventi", request)) return risposta(429, { errore: "troppe richieste" });
    const { dati, errore } = await leggiJson(request, LIMITI.corpoEventi);
    if (errore) return errore;
    const { righe, motivo } = validaLotto(dati, giorno);
    if (motivo) return risposta(400, { errore: motivo });
    const gia = await archivio.contaEventi(righe[0].installazione, giorno);
    if (gia + righe.length > LIMITI.eventiPerGiorno) return risposta(429, { errore: "troppi eventi oggi" });
    // Il totale del giorno sta in un contatore: un COUNT(*) su tutti gli eventi a ogni richiesta costa letture di D1.
    if (await archivio.incrementa(giorno, "eventi", righe.length) > LIMITI.eventiTotaliPerGiorno) {
      return risposta(429, { errore: "server pieno per oggi" });
    }
    const nuova = await archivio.installazioneNuova(righe[0].installazione);
    await archivio.scriviEventi(righe, adesso.toISOString());
    if (nuova && await archivio.incrementa(giorno, "avviso-installazione") <= LIMITI.avvisiInstallazioniPerGiorno) {
      await avvisa(avviso, avvisoInstallazione(righe[0]));
    }
    // Chi arriva in fondo a /setup, una volta sola per installazione (16/10/2026).
    const finito = righe.find((x) => x.evento === "setup" && x.valore === "fine");
    if (finito && await archivio.primaVolta("sempre", `setup-fine:${finito.installazione}`)
      && await archivio.incrementa(giorno, "avviso-setup") <= LIMITI.avvisiSetupPerGiorno) {
      await avvisa(avviso, avvisoSetupFinito(finito));
    }
    // Una config rotta arriva subito per email: una sola al giorno per installazione.
    const rotta = righe.find((x) => x.evento === "config");
    if (rotta && await archivio.primaVolta(giorno, `rotta:${rotta.installazione}`)
      && await archivio.incrementa(giorno, "email-rotta") <= LIMITI.emailRottePerGiorno) {
      try {
        await posta(emailConfigRotta(rotta.installazione, rotta.valore, rotta.versione));
      } catch (e) {
        console.log("email non partita", e && e.message);
      }
    }
    return risposta(202, { ricevuti: righe.length });
  }

  if (url.pathname === "/v1/segnalazioni") {
    if (!await limite("moduli", request)) return risposta(429, { errore: "troppe richieste" });
    const { dati, errore } = await leggiJson(request, LIMITI.corpoSegnalazione);
    if (errore) return errore;
    const { segnalazione, motivo } = validaSegnalazione(dati);
    if (motivo) return risposta(400, { errore: motivo });
    if (await archivio.contaSegnalazioni(giorno) >= LIMITI.segnalazioniPerGiorno) {
      return risposta(429, { errore: "troppe segnalazioni oggi" });
    }
    const numero = await archivio.salvaSegnalazione(segnalazione, adesso.toISOString());
    if (await archivio.incrementa(giorno, "avviso-segnalazione") <= LIMITI.avvisiSegnalazioniPerGiorno) {
      await avvisa(avviso, avvisoSegnalazione(segnalazione, numero));
    }
    let email = false;
    if (await archivio.incrementa(giorno, "email-segnalazione") <= LIMITI.emailSegnalazioniPerGiorno) {
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

  // Il modulo di feedback del sito, servito dalla landing come /api/feedback. Il testo resta qui,
  // il vocale no: passa a Telegram e basta. Senza JavaScript il modulo arriva come form: la
  // risposta allora è un rimando alla pagina, relativo, perché la richiesta passa dal sito.
  // L'ancora (#inviato, #errore...) fa vedere l'esito con :target, senza script.
  if (url.pathname === "/v1/feedback") {
    const pagina = (request.headers.get("accept") || "").includes("text/html");
    const fine = (status, dati, esito) => (pagina
      ? new Response(null, { status: 303, headers: { location: `/feedback/?${esito}#${esito}` } })
      : risposta(status, dati));
    if (daFuori) return fine(403, { errore: "invio da un altro sito" }, "errore");
    if (!await limite("moduli", request)) return fine(429, { errore: "troppe richieste" }, "troppi");
    if (Number(request.headers.get("content-length") || 0) > LIMITI.feedbackCorpo) {
      return fine(413, { errore: "troppo grande" }, "troppo-grande");
    }
    // Il corpo si legge con il tetto anche senza content-length: un invio a pezzi non riempie la memoria.
    const corpo = await corpoLimitato(request, LIMITI.feedbackCorpo);
    if (corpo === null) return fine(413, { errore: "troppo grande" }, "troppo-grande");
    let modulo;
    try {
      modulo = await new Response(corpo, { headers: { "content-type": request.headers.get("content-type") || "" } }).formData();
    } catch {
      return fine(400, { errore: "modulo non valido" }, "errore");
    }
    const { feedback, audio, motivo, trappola } = validaFeedback(modulo);
    if (trappola) return fine(202, { ricevuto: true }, "inviato");
    if (motivo) return fine(400, { errore: motivo }, "errore");
    if (audio && !await audioVero(audio)) return fine(400, { errore: "formato del vocale non riconosciuto" }, "errore");
    if (await archivio.incrementa(giorno, "feedback") > LIMITI.feedbackPerGiorno) {
      return fine(429, { errore: "troppi messaggi oggi" }, "troppi");
    }
    const numero = await archivio.salvaFeedback(feedback, adesso.toISOString());
    const testo = avvisoFeedback(feedback, numero);
    await avvisa(audio && voce ? (t) => voce(audio, t, numero) : avviso, testo);
    return fine(201, { numero }, "inviato");
  }

  // I download dal sito: il comando di installazione copiato, o il repository aperto.
  if (url.pathname === "/v1/sito") {
    if (daFuori) return risposta(403, { errore: "invio da un altro sito" });
    if (!await limite("moduli", request)) return risposta(429, { errore: "troppe richieste" });
    const { dati, errore } = await leggiJson(request, 2048);
    if (errore) return errore;
    const { evento, motivo } = validaSito(dati);
    if (motivo) return risposta(400, { errore: motivo });
    const n = await archivio.incrementa(giorno, `sito:${evento.tipo}`);
    if (n <= LIMITI.sitoPerGiorno) await avvisa(avviso, avvisoSito(evento, n));
    return risposta(202, { ricevuto: true });
  }

  return risposta(404, { errore: "percorso sconosciuto" });
}

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
