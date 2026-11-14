// Volta: le sessioni di Claude di tutte le macchine, come le scrive volta_sonda.py volta.
// Modulo puro, senza herdr: raggruppa, ordina, scrive le frasi e decide cosa fa un clic.
// Lo prova il banco HZ17-HZ19 con node (tests/test_herdr_2026_11_08.py).
//
// Una riga del file (~/.cache/volta/sessioni.json, campo "sessioni"):
// { macchina, host, questa, sessionId, id, nome, progetto, titolo, stato: aspetta|lavora|ferma|errore,
//   tipo: background|interattiva, attach: argv | null, cartella, ultimo, risposta, azione, vecchia?,
//   daPortare?: il nome scritto dalla persona che Claude Code non ha ancora (rinomina, #5292),
//   daIniziare?: il progetto dato dalla persona da cui la sessione non è ancora ripartita (/inizio, #5465) }

export const MODI = { macchina: "Per macchina", progetto: "Per progetto" };
export const SENZA = "Senza progetto";

// Il riquadro dei gesti di "Altro" sta sotto l'elenco con al più 160 px: un'anteprima lunga scorre lì
// dentro. L'elenco prende il resto della colonna (12/11/2026: niente più tetto, la sezione dei progetti
// aperti non c'è più).
export const GESTI_MAX = 160;

const tempo = (s) => Date.parse(s.ultimo || "") || 0;

// La chiave di una sessione (#5634, 14/11/2026): macchina e id insieme. Dopo Sposta su lo stesso id c'è su
// due macchine, e un /clear cambia il sessionId: schede, congedi e mappe di volta.js passano da qui.
export const chiave = (s) => `${s?.host ?? "qui"}:${s?.id ?? ""}`;
// L'id `id` sta su più di una macchina dell'elenco `l`.
export const doppio = (l, id) => new Set((l ?? []).filter((x) => x?.id === id).map((x) => x.host ?? "qui")).size > 1;
// Le chiavi delle sessioni di una mappa ({ chiave: c }): le chiavi e quelle delle voci con id. Così vale
// anche una voce scritta prima del 14/11, quando le mappe andavano per sessionId.
export const chiaviDi = (m) => new Set([...Object.keys(m ?? {}), ...Object.values(m ?? {}).filter((c) => c?.id).map(chiave)]);
// La riga di `l` che è la sessione `c`: per chiave se `c` ha l'id, altrimenti per sessionId (e macchina,
// se `c` la dice).
export const trova = (l, c) => (l ?? []).find((x) => (c?.id ? chiave(x) === chiave(c)
  : Boolean(c?.sessionId) && x.sessionId === c.sessionId && (c.host == null || (x.host ?? "qui") === c.host))) ?? null;

// I progetti noti, da shared arturo.progetti della barra: { slug o nome alternativo: { chiave, titolo } }.
// Il titolo vero ("Volta", "Post Office") sta nella scheda del progetto (arturo progetti, campo titolo:) o
// nella fonte dei task; un nome alternativo porta alla chiave del suo progetto. Ogni parte del mod gira
// in una sua copia: chi mostra nomi di progetto li imposta prima del disegno (progettiNoti di volta.js e
// cambio.js). Senza, vale il nome ricavato dallo slug.
let NOTI = {};
export function impostaProgetti(mappa) { NOTI = mappa && typeof mappa === "object" ? mappa : {}; }
// Lo slug come lo fa Arturo: minuscole senza accenti, lettere, numeri e trattini. Una copia sola: dati.js
// la riesporta.
export const slug = (p) => String(p ?? "").toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, "").replace(/[^a-z0-9-]+/g, "-").replace(/^-+|-+$/g, "");
const slugDi = slug;

// Il progetto di un nome (il progetto di una sessione, il nome di uno spazio di Herdr, una tessera): la
// chiave del suo progetto e il titolo noto, o null (#5487). Un nome alternativo ("volta", "volta-celeste")
// porta alla chiave della scheda ("herdr-arturo"): colonna, spazi, testata, Da fare e tessere passano tutti
// da qui, così una sessione e il suo spazio non si separano. `noti` è la mappa di shared arturo.progetti:
// chi non chiama impostaProgetti (dati.js, testata.js) la passa letta da shared.
export function progettoDi(p, noti = NOTI) {
  const k = slug(p);
  const n = k ? noti?.[k] : null;
  return { chiave: n?.chiave ?? k, titolo: n?.titolo ?? null };
}
// La chiave del progetto: quella del suo gruppo anche quando la sessione porta un nome alternativo.
export const chiaveProgetto = (p) => progettoDi(p).chiave;
// Il titolo vero del progetto se è noto ("Volta" per herdr-arturo), altrimenti null: chi ha un suo modo
// di scrivere il nome ricavato dallo slug (bello() di dati.js) lo usa solo quando il titolo manca.
export const titoloNoto = (p) => progettoDi(p).titolo;
// Il nome di un gruppo "Per progetto" apre il progetto (/inizio) solo se il progetto è noto: un nome
// nato da una cartella che non è un progetto ("arturo-inizio-5465", un worktree) aprirebbe una sessione
// su un progetto che non esiste (12/11/2026). Senza elenco dei progetti non si sa: resta apribile.
export const progettoApribile = (p) => Boolean(p) && (Object.keys(NOTI).length === 0 || Boolean(NOTI[slugDi(p)]));

// Il nome di un progetto per le persone: il titolo noto, altrimenti "due-mondi" → "Due mondi", "uf" → "UF".
// Un progetto fatto di soli separatori ("-") non ha parole: vale come senza progetto, invece di far
// cadere la barra.
export function nomeProgetto(p) {
  const s = String(p ?? "").trim();
  if (!s) return SENZA;
  const noto = NOTI[slugDi(s)]?.titolo;
  if (noto) return noto;
  if (/[A-Z]/.test(s)) return s;
  const t = s.split(/[-_\s]+/).filter(Boolean).map((w) => (w.length <= 2 ? w.toUpperCase() : w)).join(" ");
  return t ? t[0].toUpperCase() + t.slice(1) : SENZA;
}

// Un nome di Claude è automatico se manca, se è l'id, oppure se è "<cartella>-xx": l'ultimo pezzo della
// cartella della sessione più due cifre esadecimali ("claudecode-8e" in C:\Users\x\Documents\ClaudeCode).
// Il confronto guarda solo lettere e numeri, in minuscolo. Un nome scritto dalla persona che finisce allo
// stesso modo ("bando-57") non è automatico. Senza la cartella vale la sola forma del nome.
const piatto = (x) => String(x ?? "").toLowerCase().replace(/[^a-z0-9]/g, "");
export function nomeAutomatico(s) {
  const nome = String(s?.nome ?? "").trim();
  if (!nome || nome === s.id) return true;
  const m = /^([\w.-]+)-[0-9a-f]{2}$/.exec(nome);
  if (!m) return false;
  const ultimo = String(s.cartella ?? "").split(/[\\/]+/).filter(Boolean).pop();
  return ultimo ? piatto(m[1]) === piatto(ultimo) : true;
}

// Il titolo di una sessione. Prima quello che hooks/titolo-sessione.py scrive a fine turno (poche
// parole in italiano sul lavoro in corso, campo "titolo"). Senza, il nome di Claude; i nomi automatici
// ("claudecode-ca": cartella più due lettere, nomeAutomatico) non dicono niente: al loro posto la prima
// riga dell'ultima risposta.
export function titolo(s) {
  const scritto = String(s.titolo ?? "").replace(/\s+/g, " ").trim();
  if (scritto) return scritto;
  const nome = String(s.nome ?? "").trim();
  if (!nomeAutomatico(s)) return nome;
  const riga = String(s.risposta ?? "").split("\n").map((r) => r.replace(/[*_`#>]/g, "").replace(/\s+/g, " ").trim()).find(Boolean);
  if (riga) return riga.length > 70 ? riga.slice(0, 70).replace(/\s+\S*$/, "") + "…" : riga;
  return `Sessione ${s.id}`;
}

// "da 4 min", "da 3 ore", "da 2 giorni"; vuoto senza data.
export function daQuanto(iso, adesso = Date.now()) {
  const t = Date.parse(iso || "");
  if (!t) return "";
  const min = Math.max(0, Math.round((adesso - t) / 60000));
  if (min < 1) return "da poco";
  if (min < 60) return `da ${min} min`;
  const ore = Math.round(min / 60);
  if (ore < 24) return `da ${ore} ${ore === 1 ? "ora" : "ore"}`;
  const gg = Math.round(ore / 24);
  return `da ${gg} ${gg === 1 ? "giorno" : "giorni"}`;
}

// Le fasi di una sessione (#5366, nota di Federico dell'11/11: "le ferme devono essere diverse").
// "ferma" della sonda tiene insieme due casi: Claude ha chiuso il turno chiedendo qualcosa alla persona
// (stasi: ti aspetta) oppure ha finito e aspetta un comando nuovo (attesa). Lo dice la fine dell'ultimo
// testo di Claude (campo coda). Nel dubbio vale stasi: una sessione in stasi non si chiude da sola.
// "Prossimo passo:" conta solo se la mossa è della persona ("tu", "Federico"); "Niente da fare per te" no.
const CHIEDE = [
  /\?[\s*_`)]*$/,
  /\?\s*\n/,
  /^\s*!\s*\S/m,
  /\b(scrivimi|scrivi|dimmi|dimmelo|rispondi|rispondimi|fammi sapere|conferma|confermi|scegli|decidi|lancia|tocca a te|serve il tuo|il tuo s[iì]|aspetto la tua|attendo la tua)\b/i,
  /prossimo passo:[^\n]*(\btu\b|\btuo\b|\btua\b|\bfederico\b|\(tu\))/i,
];
export function chiede(coda) {
  const c = String(coda ?? "").slice(-220);
  return CHIEDE.some((re) => re.test(c));
}

// Un lavoro lasciato in corso: Claude aspetta l'esito di qualcosa che gira da solo (un comando in
// background, un altro agente) e riprenderà da sé. Una sessione così non va chiusa, anche se tace.
const IN_CORSO = /\b(in background|appena finisce|quando finisce|appena arriva|ti aggiorno|ti avviso|riprendo da solo|aspetto (l'esito|il risultato|che finisca))\b/i;
export const lavoroInCorso = (coda) => IN_CORSO.test(String(coda ?? "").slice(-220));

// "attiva" (lavora), "stasi" (ti aspetta), "attesa" (aspetta un comando), "errore", "chiusa".
export function fase(s) {
  if (!s || chiusa(s)) return "chiusa";
  if (s.stato === "errore") return "errore";
  if (s.stato === "lavora") return "attiva";
  if (s.stato === "aspetta" || s.aspetta) return "stasi";
  // l'ultima parola non è un testo di Claude (un messaggio senza risposta, un comando interrotto,
  // nessuna trascrizione): nel dubbio, ti aspetta
  if (s.chi !== "claude" || chiede(s.coda)) return "stasi";
  return "attesa";
}

// L'ora dell'ultimo messaggio vero; una riga di una sonda di prima ha solo "ultimo".
const interazione = (s) => Date.parse(s?.interazione || s?.ultimo || "") || 0;

// La frase di stato e il colore del tema (blocked, working, done, idle, muted, dim).
export function fraseStato(s, adesso = Date.now()) {
  if (s.vecchia) return { testo: "Ultima lettura: la macchina non risponde", colore: "dim" };
  const f = fase(s);
  if (f === "attiva") return { testo: "Sta lavorando", colore: "working" };
  if (f === "errore") return { testo: "Si è fermata con un errore", colore: "blocked" };
  const q = daQuanto(s.interazione || s.ultimo, adesso);
  // addormentata (#5495): il servizio di Claude l'ha ritirata, il clic o il giro la riprendono
  const zz = dorme(s) ? ", addormentata" : "";
  if (f === "stasi") return { testo: (q ? `Ti aspetta ${q}` : "Ti aspetta") + zz, colore: "blocked" };
  if (zz) return { testo: q ? `Addormentata ${q}` : "Addormentata", colore: "dim" };
  return { testo: q ? `Aspetta un comando ${q}` : "Aspetta un comando", colore: "muted" };
}

// La chiusura automatica (#5366): le sessioni di questa macchina in background che aspettano un comando
// da più di `dopoMin` minuti, senza un lavoro lasciato in corso, senza una scheda aperta in questa
// finestra (chi la guarda la sta usando) e non già in congedo. Prima la più vecchia.
// `opz`: { dopoMin, congedi: { chiave: c }, conScheda: Set di chiavi }.
export function daCongedare(dati, adesso, opz = {}) {
  const soglia = adesso - (Number(opz.dopoMin) || 60) * 60000;
  const via = chiaviDi(opz.congedi);
  const scheda = opz.conScheda ?? new Set();
  return (dati?.sessioni ?? [])
    .filter((s) => s.questa && s.tipo === "background" && !s.vecchia && fase(s) === "attesa" && !lavoroInCorso(s.coda))
    .filter((s) => interazione(s) > 0 && interazione(s) < soglia && !via.has(chiave(s)) && !scheda.has(chiave(s)))
    .sort((a, b) => interazione(a) - interazione(b));
}

// Quante chiusure automatiche restano: al più `ora` nell'ultima ora e `giorno` nelle ultime 24 ore.
// `fatti`: le ore (ms) delle chiusure già fatte.
export function restanti(fatti, adesso, opz = {}) {
  const l = (fatti ?? []).map(Number).filter((x) => x > 0 && x <= adesso);
  const ora = l.filter((x) => adesso - x < 3600000).length, giorno = l.filter((x) => adesso - x < 86400000).length;
  return Math.max(0, Math.min((opz.ora ?? 3) - ora, (opz.giorno ?? 12) - giorno));
}

// Il registro del modo "prova": cosa la chiusura automatica avrebbe chiuso, una voce per sessione, con
// la prima e l'ultima volta che l'ha vista. Al più 40 voci, le più recenti. Lo legge Federico prima di
// accendere la chiusura vera (arturo.json, "congedo": "acceso").
export function registroProva(prima, scelte, adesso) {
  const per = new Map((prima ?? []).map((v) => [v.sessionId, v]));
  for (const s of scelte ?? []) {
    const v = per.get(s.sessionId);
    per.set(s.sessionId, { sessionId: s.sessionId, id: s.id, titolo: titolo(s), progetto: s.progetto ?? null,
      interazione: s.interazione || s.ultimo || "", coda: String(s.coda ?? "").slice(-160), fineFatta: Boolean(s.fineFatta),
      vista: v?.vista ?? adesso, ultima: adesso });
  }
  return [...per.values()].sort((a, b) => b.ultima - a.ultima).slice(0, 40);
}

// Il nome vero di questa macchina, dall'elenco delle macchine (`dati` di sessioni.json o shared
// arturo.volta.macchine): null se l'elenco non c'è ancora.
export const macchinaQui = (dati) => (Array.isArray(dati) ? dati : dati?.macchine ?? []).find((x) => x?.questa)?.macchina ?? null;
// Il nome di una macchina di "Nasce su" e dei messaggi: "qui" è il nome vero di questa macchina (#5534:
// gli errori dicevano "non parte su qui"), "questa macchina" solo finché l'elenco manca.
export const nomeMacchina = (m, macchine) => (m === "qui" ? macchinaQui(macchine) ?? "questa macchina" : m);

// Il nome di una macchina in una riga stretta: senza il proprietario e senza la coda fra parentesi che
// macOS aggiunge ("MacBook Air di Federico (156)" → "MacBook Air"). Il nome intero resta nei gruppi.
export function macchinaBreve(nome) {
  const s = String(nome ?? "").trim();
  const b = s.replace(/\s*\([^)]*\)\s*$/, "").replace(/\s+(di|de|of)\s+\S+$/i, "").replace(/^\S+['’]s\s+/, "").trim();
  return b || s;
}

// La seconda riga: ciò che il gruppo non dice già (il progetto per macchina, la macchina per progetto).
export function dettaglio(s, modo, adesso = Date.now()) {
  const dove = modo === "progetto" ? macchinaBreve(s.macchina) : (s.progetto ? nomeProgetto(s.progetto) : "");
  const f = fraseStato(s, adesso);
  return { testo: dove ? `${dove} · ${f.testo}` : f.testo, colore: f.colore };
}

// I gruppi: [{ chiave, titolo, nota?, sessioni }]. L'ordine è quello dell'ultima interazione (campo
// "ultimo"): dentro ogni gruppo la sessione toccata per ultima sta in cima, e viene per primo il gruppo
// che contiene la più recente. Lo stato non sposta le righe: lo dicono pallino e frase. A pari tempo
// l'ordine del file per le macchine (questa per prima) e l'alfabeto per i progetti; la macchina che
// non risponde porta una nota.
const recente = (g) => Math.max(0, ...g.sessioni.map(tempo));
export function gruppi(dati, modo = "macchina") {
  const righe = [...(dati?.sessioni ?? [])].sort((a, b) => tempo(b) - tempo(a) || titolo(a).localeCompare(titolo(b)));
  const per = new Map();
  const metti = (chiave, tit, s) => {
    if (!per.has(chiave)) per.set(chiave, { chiave, titolo: tit, sessioni: [] });
    if (s) per.get(chiave).sessioni.push(s);
  };
  if (modo === "progetto") {
    for (const s of righe) metti(chiaveProgetto(s.progetto), nomeProgetto(s.progetto), s);
    const out = [...per.values()];
    out.sort((a, b) => recente(b) - recente(a) || a.titolo.localeCompare(b.titolo));
    const giu = (dati?.macchine ?? []).filter((m) => m.irraggiungibile).map((m) => m.macchina);
    const rotte = (dati?.macchine ?? []).filter((m) => !m.irraggiungibile && m.nascita?.rotta === true).map((m) => m.macchina);
    const note = [giu.length ? `${giu.join(", ")} non ${giu.length > 1 ? "rispondono" : "risponde"}` : "",
      rotte.length ? `${rotte.join(", ")} non fa${rotte.length > 1 ? "nno" : ""} partire sessioni` : ""].filter(Boolean);
    if (note.length && out.length) out[out.length - 1].nota = note.join(" · ");
    return out;
  }
  for (const m of dati?.macchine ?? []) metti(m.host, m.macchina, null);
  for (const s of righe) metti(s.host, s.macchina, s);
  const out = [];
  for (const m of dati?.macchine ?? []) {
    const g = per.get(m.host);
    if (m.irraggiungibile) g.nota = g.sessioni.length ? "Non risponde: mostro l'ultima lettura" : "Non risponde";
    else if (m.nascita?.rotta === true) g.nota = "Non fa partire sessioni nuove";
    if (g.sessioni.length || g.nota) out.push(g);
    per.delete(m.host);
  }
  return out.concat([...per.values()].filter((g) => g.sessioni.length)).sort((a, b) => recente(b) - recente(a));
}

// Chiudere una sessione (12/11/2026, decisione di Federico): ⌘W, la X della scheda o Chiudi del menu
// fanno il congedo, cioè /fine e poi claude stop. Una sessione chiusa o in congedo non compare più
// nell'elenco: si ritrova con Apri un progetto. Chiusa = in background, senza processo e senza status,
// fermata con claude stop o dopo /fine (il campo `chiusa` di volta_sonda.py); una in errore resta,
// perché Riavvia serve. Addormentata = senza processo per altro, di solito ritirata dal servizio di
// Claude dopo un'ora ferma (#5495, 13/11/2026): resta nell'elenco e nel giro, e claude attach la riprende.
export const chiusa = (s) => Boolean(s) && s.tipo === "background" && s.chiusa === true;
export const dorme = (s) => Boolean(s) && s.tipo === "background" && s.dorme === true && !chiusa(s);
export function visibili(dati, congedi = {}) {
  if (!dati) return dati;
  const via = chiaviDi(congedi);
  const l = (dati.sessioni ?? []).filter((s) => !chiusa(s) && !via.has(chiave(s)));
  return { ...dati, sessioni: unaPerConversazione(l) };
}

// Al più `n` parole: la sintesi della testata ne vuole cinque (Federico, 12/11/2026). Oltre, "…".
export function cinqueParole(testo, n = 5) {
  const p = String(testo ?? "").trim().split(/\s+/).filter(Boolean);
  return p.length > n ? `${p.slice(0, n).join(" ")}…` : p.join(" ");
}

// Cosa scrive la testata sotto il progetto: la sintesi della sessione davanti (shared arturo.volta.davanti,
// la scrive titolo-sessione.py a ogni turno), altrimenti il suo titolo, altrimenti il nome della scheda;
// sempre al più cinque parole. null se non c'è niente da dire.
export function sintesiTestata(davanti, nomeScheda = null) {
  const t = davanti?.sintesi || davanti?.titolo || nomeScheda;
  return t ? cinqueParole(t) || null : null;
}

// Le sessioni che il giro ⌘↓/⌘↑ salta, nella forma dei congedi di visibili(): quelle in congedo, quelle
// la cui riga si sta dissolvendo (`escono`: { chiave: true }) e quelle con la scheda appena sparita
// (`forse`: { chiave: sessione }). Le chiavi bastano: visibili() le legge con chiaviDi.
export function uscenti(congedi = {}, escono = {}, forse = {}) {
  const out = { ...(congedi ?? {}) };
  for (const k of Object.keys(escono ?? {})) if (escono[k]) out[k] = { esce: true };
  for (const [k, s] of Object.entries(forse ?? {})) out[k] = s?.id ? { id: s.id, host: s.host ?? "qui" } : { esce: true };
  return out;
}

// Una conversazione spostata su un'altra macchina (Sposta su, 12/11/2026) c'è su due macchine: resta quella
// che non è ferma, cioè la copia viva. La stessa conversazione ha lo stesso sessionId, oppure lo stesso id
// su un'altra macchina: un /clear dopo lo spostamento cambia il sessionId e lascia l'id (#5634). Fra due
// ferme, o due vive, restano tutte e due.
export function unaPerConversazione(l) {
  const vive = l.filter((s) => s.stato !== "ferma");
  const stessa = (a, b) => (Boolean(a.sessionId) && a.sessionId === b.sessionId) || (Boolean(a.id) && a.id === b.id && (a.host ?? "qui") !== (b.host ?? "qui"));
  return l.filter((s) => s.stato !== "ferma" || !vive.some((x) => stessa(s, x)));
}

// Le schede chiuse da chi usa la finestra: i terminali che agganciavano una sessione al giro di prima e
// ora non ci sono più, tolti quelli che ha chiuso Volta stessa (`tolti`: indirizzo → ms, per Sposta,
// Cambia progetto, Stacca) negli ultimi TOLTI_MS. `prima` e `adesso`: { indirizzo: sessione }.
// `occupate`: { indirizzo: sessione } di occupanti(). Una scheda dove ora gira un'altra sessione (claude
// lanciato a mano nella shell rimasta dopo lo stacco) non è chiusa: la scheda c'è ancora, mostra solo
// un'altra sessione, e quella di prima non va in congedo (#5630).
export const TOLTI_MS = 60000;
export function sparite(prima, adesso, tolti = {}, ora = Date.now(), occupate = {}) {
  if (prima == null) return [];  // il primo giro dopo l'apertura solo guarda
  const viste = new Set();
  const out = [];
  for (const [ind, s] of Object.entries(prima)) {
    if (ind in (adesso ?? {}) || occupate?.[ind] || (tolti?.[ind] && ora - tolti[ind] < TOLTI_MS) || !s?.id || viste.has(chiave(s))) continue;
    // un'altra scheda aggancia ancora la stessa sessione: chiusa una copia, la sessione resta aperta
    if (Object.values(adesso ?? {}).some((x) => x?.id && chiave(x) === chiave(s))) continue;
    viste.add(chiave(s));
    out.push(s);
  }
  return out;
}

// Lo stacco delle schede ferme (F3.2 di #5587, deciso da Federico il 14/11/2026): un claude attach aperto
// impedisce al servizio di Claude di ritirare la sessione dopo un'ora ferma, e la sessione tiene 350-600 MB.
// Una scheda che aggancia una sessione ferma da STACCA_DOPO_MS si stacca con Ctrl+Z di claude attach: esce
// pulito, spegne i modi del terminale e la bozza resta nella sessione. La scheda resta con la shell, e il
// clic sulla riga o sulla scheda rilancia l'aggancio. `schede`: { indirizzo: sessione } di schedeAgganciate.
// `opz`: { davanti: l'indirizzo in primo piano, che chi guarda sta usando; visti: Set dei terminali in un
// pannello, perché un terminale fuori dalle schede (un Terminale col lanciatore) non è una scheda;
// no: Set di indirizzi da non riprovare }. Torna [{ indirizzo, s }], prima la più vecchia.
export const STACCA_DOPO_MS = 45 * 60000;
export function daStaccare(schede, sessioni, adesso, opz = {}) {
  const soglia = adesso - STACCA_DOPO_MS;
  const l = sessioni ?? [];
  const out = [];
  for (const [indirizzo, c] of Object.entries(schede ?? {})) {
    if (!c || indirizzo === opz.davanti || opz.no?.has(indirizzo) || (opz.visti && !opz.visti.has(indirizzo))) continue;
    // macchina e id insieme: dopo uno spostamento lo stesso id c'è su due macchine (#5634)
    const s = l.find((x) => x.id === c.id && x.host === c.host);
    if (!s || s.tipo !== "background" || s.vecchia || chiusa(s) || s.stato !== "ferma" || s.aspetta || lavoroInCorso(s.coda)) continue;
    const t = interazione(s);
    if (t > 0 && t <= soglia) out.push({ indirizzo, s, t });
  }
  return out.sort((a, b) => a.t - b.t).map(({ indirizzo, s }) => ({ indirizzo, s }));
}

// Un passo del congedo, deciso dallo stato di adesso. `c`: { sessionId, id, host, fase, da, dal } con fase
// "attende" (lavorava quando l'hai chiusa: finisce il turno), "fine" (ripresa con /fine), "ferma" (claude
// stop chiesto). `s`: la sua riga dell'elenco, o undefined. Torna { fai, fase?, salvata?, avviso? } con fai:
// "attendi" | "fine" (stop e ripresa con /fine) | "stop" | "togli" (via dal registro) | "rm" (claude rm,
// poi via dal registro). `salvata` va nel registro quando /fine ha finito il turno: solo allora la sessione
// chiusa si elimina anche da claude agents (#5401, Federico, 12/11: "aggiungi rm"). Dopo una domanda, un
// tetto o un /fine mai partito la sessione resta in claude agents, da riaprire o eliminare a mano.
// Tetti: CONGEDO_MAX_MS per il turno in corso e per /fine; dopo, la sessione si ferma lo stesso e Volta lo
// dice. Una macchina che non risponde tiene il congedo fino a CONGEDO_VECCHIO_MS.
export const CONGEDO_MAX_MS = 20 * 60000, CONGEDO_AVVIO_MS = 20000, CONGEDO_SENZA_FINE_MS = 3 * 60000, CONGEDO_VECCHIO_MS = 6 * 3600000;
export function passoCongedo(c, s, ora = Date.now()) {
  const da = Number(c?.da) || ora, dal = Number(c?.dal) || da;
  const nome = s ? titolo(s) : "La sessione";
  if (!s || s.vecchia) return ora - da > (s ? CONGEDO_VECCHIO_MS : 3600000) ? { fai: "togli" } : { fai: "attendi" };
  if (c.fase === "attende") {
    if (chiusa(s)) return { fai: "togli" };
    // la chiusura automatica di una sessione che ha già fatto /fine (#5366): niente secondo /fine
    if (c.fineFatta && s.stato !== "lavora") return { fai: "stop", fase: "ferma", salvata: true };
    if (s.stato === "lavora" && ora - da < CONGEDO_MAX_MS) return { fai: "attendi" };
    return { fai: "fine", fase: "fine" };
  }
  if (c.fase === "fine") {
    if (ora - dal < CONGEDO_AVVIO_MS) return { fai: "attendi" };
    if (s.stato === "errore") return { fai: "togli", avviso: `${nome}: /fine si è fermato con un errore. La sessione resta ferma.` };
    // senza processo dopo lo stop di Volta: claude agents la dice "stopped" o la lascia "done" (dorme)
    if (chiusa(s) || dorme(s)) return ora - dal > CONGEDO_SENZA_FINE_MS ? { fai: "togli", avviso: `${nome} non è ripartita per /fine: l'ho lasciata chiusa senza salvataggio.` } : { fai: "attendi" };
    if (s.stato === "aspetta") return { fai: "stop", fase: "ferma", avviso: `${nome} ha chiesto qualcosa durante /fine: l'ho fermata lo stesso.` };
    if (s.stato === "lavora") return ora - dal > CONGEDO_MAX_MS ? { fai: "stop", fase: "ferma", avviso: `${nome}: /fine non ha finito in 20 minuti, l'ho fermata.` } : { fai: "attendi" };
    // ferma e viva: /fine ha finito il turno se la trascrizione è andata avanti dopo la ripresa
    if (tempo(s) > dal - 5000) return { fai: "stop", fase: "ferma", salvata: true };
    return ora - dal > CONGEDO_SENZA_FINE_MS ? { fai: "stop", fase: "ferma", avviso: `${nome} non ha fatto /fine: l'ho fermata senza salvataggio.` } : { fai: "attendi" };
  }
  // fase "ferma": aspetta che claude agents la dica senza processo, e riprova lo stop dopo due minuti.
  // Lo stop l'ha chiesto Volta: anche "done" senza processo (dorme) vuol dire fermata.
  if (chiusa(s) || dorme(s)) return c.salvata ? { fai: "rm" } : { fai: "togli" };
  return ora - dal > 120000 ? { fai: "stop", fase: "ferma" } : { fai: "attendi" };
}

// Le nascite che cadono su una macchina (13/11/2026): la sonda scrive `nascita` nella voce della macchina
// quando le sessioni nuove escono prima di iniziare ("exit 1 before init"), come su un Mac con
// Documenti bloccato da macOS. Volta lo dice una volta per episodio e non fa ripartire al clic una
// sessione in errore di quella macchina: ogni ripartenza cadeva di nuovo, due volte per clic.
export function nascitaDi(dati, host) {
  const m = (dati?.macchine ?? []).find((x) => (x.host ?? "qui") === (host ?? "qui"));
  if (m?.nascita?.rotta !== true) return null;
  return { ...m.nascita, macchina: m.questa ? "questa macchina" : (m.macchina ?? m.host) };
}
const oraCorta = (iso) => {
  const d = new Date(iso ?? "");
  return Number.isNaN(d.getTime()) ? null : `${String(d.getHours()).padStart(2, "0")}:${String(d.getMinutes()).padStart(2, "0")}`;
};
export function avvisoNascita(n) {
  if (!n) return null;
  const m = n.macchina ?? "quella macchina", da = oraCorta(n.da);
  const volte = Number.isInteger(n.quante) && n.quante > 0 ? `${n.quante} volte` : "più volte";
  return `Su ${m} le sessioni non partono${da ? ` dalle ${da}` : ""}: Claude esce prima di iniziare (${volte}). Spesso macOS aspetta un permesso sullo schermo di ${m}: rispondi lì, o riavvia ${m}.`;
}
// Il clic su una sessione in errore la fa ripartire (claude respawn) solo se la sua macchina fa partire
// sessioni. Riavvia del menu resta: è un gesto esplicito.
export function riparteAlClic(s, dati) {
  if (s?.stato !== "errore") return { riparte: false };
  const n = nascitaDi(dati, s.host);
  return n ? { riparte: false, errore: avvisoNascita(n) } : { riparte: true };
}
// Gli avvisi da dare: una macchina che ha appena smesso di far partire sessioni. `viste`: le macchine già
// avvisate in questo episodio ({ host: true }); torna anche le viste nuove, senza quelle tornate a posto.
export function nascitePerAvviso(dati, viste = {}) {
  const avvisi = [], tieni = {};
  for (const m of dati?.macchine ?? []) {
    if (m?.irraggiungibile || m?.nascita?.rotta !== true) continue;
    const k = m.host ?? "qui";
    tieni[k] = true;
    if (!viste?.[k]) avvisi.push(avvisoNascita(nascitaDi(dati, k)));
  }
  return { avvisi, viste: tieni };
}

// I congedi rimasti a metà (13/11/2026): una sessione ripresa con /fine da un congedo (la sonda la segna
// `congedo`) che il registro non ha più, ferma da più di CONGEDO_ORFANO_MS; se è viva, senza scheda aperta qui.
// Solo questa macchina, come la chiusura automatica. Torna [{ s, fai, avviso? }]: "rm" se /fine ha finito
// e la sessione non ha più processo; "stop" se è ancora viva con /fine come ultimo messaggio (poi, ferma,
// diventa "rm"); "rm" con avviso se è in errore senza /fine (la ripresa è caduta): la persona l'aveva
// chiusa, la trascrizione resta su disco. Una viva, ferma o ritirata usata dopo il congedo non si tocca.
export const CONGEDO_ORFANO_MS = 10 * 60000;

// Lo spostamento staccato (13/11/2026): volta_sposta.py scrive l'esito in un file e Volta lo legge a giri.
// `testo`: il file (o null), `dal`: quando è partito, `ora`. Torna { fatto } con l'esito finito, { attendi }
// finché gira, { errore } oltre SPOSTA_MAX_MS: allora lo spostamento non si sa com'è andato.
export const SPOSTA_MAX_MS = 25 * 60000, SPOSTA_OGNI_MS = 5000;
export function esitoSposta(testo, dal, ora, macchina = "l'altra macchina") {
  let d = null;
  try { d = testo ? JSON.parse(testo) : null; } catch { d = null; }
  if (d && typeof d === "object" && d.finito === true) { const { finito: _, ...resto } = d; return { fatto: resto }; }
  if (ora - dal > SPOSTA_MAX_MS) return { errore: `${macchina} non ha finito in 25 minuti: guarda fra le sessioni dove è rimasta` };
  return { attendi: true };
}

// Gli spostamenti in volo (#5559, 13/11/2026): una ricarica del mod (dirama, controllo orario) cancella
// l'attesa di cx.sleep, e nessuno apriva la scheda d'arrivo né riapriva quella chiusa. Ogni spostamento
// staccato resta segnato in cacheVolta()/sposta/volo.json finché la sua fine non è fatta, e al caricamento
// Volta riprende quelli rimasti. `v` = { s, macchina, file, dal, chiuse, preso }: `preso` è l'ultima volta
// che una copia del mod ci ha lavorato (ogni giro dell'attesa). Torna "mia" se tocca a chi legge, "altrui"
// se un'altra copia viva lo segue, "scarta" se è rotto o più vecchio di VOLO_MAX_MS: dopo ore la sessione
// sta dove l'elenco la mostra, e una scheda che si apre da sola sorprenderebbe.
export const VOLO_FRESCO_MS = 20000, VOLO_MAX_MS = 2 * 3600000;
export function voloSposta(v, ora) {
  if (!v || typeof v !== "object" || !v.s || typeof v.s !== "object" || !v.s.sessionId || !v.s.id) return "scarta";
  if (typeof v.macchina !== "string" || !v.macchina || typeof v.file !== "string" || !v.file || !Number.isFinite(v.dal)) return "scarta";
  if (ora - v.dal > VOLO_MAX_MS) return "scarta";
  return Number.isFinite(v.preso) && ora - v.preso < VOLO_FRESCO_MS ? "altrui" : "mia";
}

// Il passo di arturo() di dati.js per un comando, dalla sua voce in volo: `v` = { da, p } se gira, { da,
// appeso } se l'ultimo è rimasto appeso (exec rifiuta ma il processo resta). "lancia" se non c'è niente;
// "aspetta" la stessa promessa se gira da meno del tetto; "appeso" se gira oltre il tetto o se l'ultimo è
// rimasto appeso da meno di ARTURO_PAUSA_MS: un processo in più non risponderebbe comunque.
export const ARTURO_PAUSA_MS = 5 * 60000;
export function voloArturo(v, ora, tetto) {
  if (!v) return { fai: "lancia" };
  if (v.appeso) return ora - v.appeso < ARTURO_PAUSA_MS ? { fai: "appeso" } : { fai: "lancia" };
  return ora - v.da < tetto ? { fai: "aspetta" } : { fai: "appeso" };
}

// Un lotto di watchFolder tocca l'elenco se contiene il file (o la cartella intera: rileggi tutto).
// I percorsi si confrontano senza barre finali e senza maiuscole: su Windows arrivano con \.
export function tocca(percorsi, cartella, file) {
  const n = (p) => String(p ?? "").replace(/\\/g, "/").replace(/\/+$/, "").toLowerCase();
  const c = n(cartella), f = n(file);
  return (percorsi ?? []).some((p) => { const x = n(p); return x === c || x === f; });
}
export function congediOrfani(dati, congedi = {}, ora = Date.now(), conScheda = new Set()) {
  const via = chiaviDi(congedi);
  const out = [];
  for (const s of dati?.sessioni ?? []) {
    if (!s?.questa || s.tipo !== "background" || s.vecchia || s.congedo !== true) continue;
    if (via.has(chiave(s))) continue;
    if (s.stato === "lavora") continue;
    if (!(tempo(s) > 0) || ora - tempo(s) < CONGEDO_ORFANO_MS) continue;
    const morta = chiusa(s) || dorme(s) || s.stato === "errore";
    // una scheda aperta protegge solo una sessione viva: su una ferma resta la shell, e la riga restava
    // in Volta per sempre (13/11/2026, un PC Windows: scheda t1z con PowerShell sul congedo 261279d3)
    if (!morta && conScheda.has(chiave(s))) continue;
    // viva: si ferma solo se /fine è ancora l'ultimo messaggio; riaperta e usata dopo il congedo, resta
    if (!morta) { if (s.fineFatta) out.push({ s, fai: "stop" }); }
    else if (s.fineFatta && s.stato !== "errore") out.push({ s, fai: "rm" });
    // ferma o ritirata senza /fine in fondo: riaperta e usata dopo il congedo, poi lasciata. Resta.
    else if (s.stato === "errore") out.push({ s, fai: "rm", avviso: `${titolo(s)}: chiusa senza salvataggio, /fine non era finito. La conversazione resta su disco.` });
  }
  return out;
}

// Le sessioni di un gruppo che l'elenco mostra: quelle che lavorano, ti aspettano o sono in errore
// sempre; quelle che aspettano un comando (fase "attesa", #5366) solo se il gruppo è aperto, o se non ce
// ne sono altre e sono due o meno.
export const inAttesa = (s) => fase(s) === "attesa";
export function mostrate(g, aperto) {
  const vive = g.sessioni.filter((s) => !inAttesa(s));
  const ferme = g.sessioni.length - vive.length;
  return (!vive.length && ferme <= 2) || aperto ? g.sessioni : vive;
}

// Il giro fra le sessioni (⌘↓ e ⌘↑, Ctrl+↓ e Ctrl+↑ su Windows): tutte le sessioni accese, nell'ordine
// dell'elenco, anche quelle che aspettano un comando (Federico, 12/11 sera: "voglio che cicli tra tutte
// le sessioni che sono accese in questo momento"). Resta fuori solo una ferma che ha già fatto /fine e
// non ha una scheda in questa finestra (`conScheda`, le chiavi): è chiusa, e il tasto la riaggancerebbe
// (Federico, 12/11: "ha aperto piano gare bergamo che avevo chiuso"). Le chiuse davvero (claude stop)
// le toglie già visibili(). Le ferme nascoste dietro "N in attesa" vengono dopo le righe a vista del
// loro gruppo. Restano fuori anche le sessioni che stanno in un Terminale: il clic lì le sposta con
// /bg, e un giro di tasti non deve spostare niente.
export function ordineGiro(lista, aperti = {}, conScheda = new Set()) {
  return (lista ?? []).flatMap((g) => {
    const vista = mostrate(g, aperti[g.chiave]);
    return vista.concat(g.sessioni.filter((s) => !vista.includes(s)));
  })
    .filter((s) => s.stato !== "ferma" || !s.fineFatta || conScheda.has(chiave(s)))
    .filter((s) => ["aggancia", "mostra"].includes(clic(s).azione)).map(chiave);
}

// L'ordine vale per tutta una raffica di tasti: l'elenco è per attività, e una sessione che lavora
// cambia posto mentre giri. Dopo GIRO_MS senza tasti il giro riparte dall'elenco di adesso. `adesso` sono
// gli id del giro di adesso: una sessione sparita esce, una nuova entra al prossimo giro.
export const GIRO_MS = 8000;
export function statoGiro(prima, adesso, ora) {
  const tiene = prima && ora - prima.quando <= GIRO_MS;
  const ids = tiene ? prima.ids.filter((id) => adesso.includes(id)) : adesso;
  return { ids: ids.length ? ids : adesso, ultimo: tiene ? prima.ultimo ?? null : null, quando: ora };
}

// La sessione che l'elenco accende a sinistra (Federico, 12/11/2026: "evidenziarmi su quale sto
// lavorando"). Dentro una raffica di ⌘↓ e ⌘↑ è l'ultima chiesta col giro, perché la scheda ci mette
// qualche secondo ad aprirsi; fuori dalla raffica è quella della scheda in primo piano. Chiavi (chiave()):
// null se nessuna.
export function corrente(giroSt, idScheda, ora) {
  if (giroSt?.ultimo && ora - giroSt.quando <= GIRO_MS) return giroSt.ultimo;
  return idScheda ?? null;
}

// La sessione che una scheda mostra, anche quando la scheda sta in uno spazio di un'altra macchina
// (indirizzo "torre/t13"): là Claude gira nel terminale t13 di torre, che la sonda di quella
// macchina scrive nel campo terminale. Chi gira nel terminale vince sull'etichetta, come in occupanti:
// una scheda nata per una sessione può ospitarne dopo un'altra. Poi vale sessioneDi.
export function sessioneDavanti(terminale, sessioni) {
  if (!terminale) return null;
  const [m, t] = String(terminale.address ?? "").split("/");
  const li = t ? (sessioni ?? []).find((s) => s.host === m && s.terminale === t && s.tipo !== "background") : null;
  return li ?? sessioneDi(terminale, sessioni);
}

// La sessione dopo (verso 1) o prima (verso -1) di `corrente`, in tondo. Senza corrente, o con una
// corrente fuori dal giro: la prima andando avanti, l'ultima andando indietro. null a giro vuoto.
export function passoGiro(ids, corrente, verso) {
  if (!ids?.length) return null;
  const i = ids.indexOf(corrente);
  if (i < 0) return verso < 0 ? ids[ids.length - 1] : ids[0];
  return ids[(i + (verso < 0 ? -1 : 1) + ids.length) % ids.length];
}

// I terminali di questa macchina dove gira adesso una sessione interattiva (la sonda lo legge dal
// processo, campo terminale): { indirizzo: sessione }. Vincono su etichetta e argv. Una scheda nata per
// agganciare una sessione può ospitare dopo un'altra sessione, avviata a mano nella sua shell: allora
// mostra quella, col suo progetto e la sua macchina (12/11/2026, Post Office al posto di Volta).
export function occupanti(sessioni) {
  const out = {};
  for (const s of sessioni ?? []) if (s?.questa && s.tipo !== "background" && s.terminale) out[s.terminale] = s;
  return out;
}

// La sessione che una scheda mostra: quella che ci gira (occupanti), poi l'etichetta di Herdr (hc label
// arturo.sessione), poi l'argv dell'aggancio. null se la scheda non è di una sessione.
export function sessioneDi(terminale, sessioni) {
  if (!terminale) return null;
  const l = sessioni ?? [];
  const e = terminale.labels?.[ETICHETTA];
  return occupanti(l)[terminale.address]
    ?? l.find((s) => etichettaDice(e, s, doppio(l, s.id)) === true)
    ?? l.find((s) => etichettaDice(e, s, doppio(l, s.id)) === null && agganciata(terminale.argv, s)) ?? null;
}

// L'etichetta di Herdr sul terminale che aggancia una sessione (hc label): dal 14/11/2026 la chiave
// macchina:id (#5634). Cosa dice su `s`: true è sua, false è di un'altra sessione, null non lo dice. Non lo
// dice una scheda senza etichetta, e un'etichetta di prima col solo id quando l'id sta su due macchine
// (`ambiguo`): lì decide l'argv. Un'etichetta vecchia con un id che una macchina sola ha vale ancora: le
// schede aperte prima restano riconosciute.
const ETICHETTA = "arturo.sessione";
export function etichettaDice(valore, s, ambiguo = false) {
  if (!valore || !s?.id) return null;
  const v = String(valore);
  if (v.includes(":")) return v === chiave(s);
  if (v !== s.id) return false;
  return ambiguo ? null : true;
}
// Il terminale `t` mostra la sessione `s`: per etichetta, poi per argv.
export const suaScheda = (t, s, ambiguo = false) => {
  const e = etichettaDice(t?.labels?.[ETICHETTA], s, ambiguo);
  return e ?? agganciata(t?.argv, s);
};

// Cosa fa il clic: { azione: "aggancia", argv } per una sessione in background, { azione: "porta" }
// per un'interattiva ferma (prima /bg con porta-volta), { azione: "mostra", terminale } per
// un'interattiva che gira in una scheda di Herdr, { azione: "no", motivo } altrimenti.
export function clic(s) {
  if (s.vecchia) return { azione: "no", motivo: `${s.macchina} non risponde: riprova quando torna.` };
  if (s.tipo === "background") {
    if (!Array.isArray(s.attach) || !s.attach.length) return { azione: "no", motivo: "Non so come agganciare questa sessione." };
    return { azione: "aggancia", argv: s.attach };
  }
  // partita nella shell di una scheda di Herdr: sta già in Volta, il clic la porta davanti
  if (s.terminale) return { azione: "mostra", terminale: s.questa ? s.terminale : `${s.host}/${s.terminale}` };
  if (s.stato === "lavora") return { azione: "no", motivo: "Sta lavorando nel suo Terminale: la sposto quando si ferma." };
  if (s.stato === "aspetta") return { azione: "no", motivo: "Ti aspetta nel suo Terminale: rispondi lì, poi la sposto." };
  if (s.stato === "errore") return { azione: "no", motivo: "Si è fermata con un errore: aprila dal suo Terminale." };
  return { azione: "porta" };
}

// La chiave che riconosce una sessione già agganciata in una scheda: l'id corto nell'argv, come
// parola a sé oppure dentro un comando di shell: "sh -c 'while :; do ssh … claude attach <id>; …'"
// delle schede aperte da altre strade, "pwsh -Command & '…claude.exe' 'attach' '<id>'" su Windows.
// Senza, il clic apre un secondo aggancio della stessa sessione e le due schede si contendono la
// larghezza del terminale.
// Dal 14/11/2026 (#5634) conta anche la macchina: l'argv aggancia `s` solo se raggiunge con ssh la stessa
// macchina del suo aggancio (campo attach), o se nessuno dei due passa da ssh. Dopo Sposta su lo stesso id
// c'è su due macchine: "claude attach a1" è la copia di qui, "ssh -t amaltea … attach a1" quella di amaltea.
const dentro = (a, id) => typeof a === "string" &&
  new RegExp(`\\battach['"]?\\s+['"]?${id.replace(/[^\w-]/g, "")}\\b`).test(a);
export const agganciata = (argv, s) => Array.isArray(argv) && !!s?.id &&
  ((argv.includes("attach") && argv.includes(s.id)) || argv.some((a) => dentro(a, s.id))) && stessoPosto(argv, s);

// La macchina che un argv raggiunge con ssh: il primo argomento di ssh che non è un'opzione, senza
// "utente@", in minuscolo. null se l'argv non passa da ssh. Vale anche dentro la riga di una shell
// (sh -c "while :; do ssh … attach <id>; …", pwsh -Command "& '…ssh.exe' '-t' 'amaltea' …").
const OPZIONI_CON_VALORE = new Set("bBcDEeFIiJLlmOoPpQRSWw");
export function sshDi(argv) {
  if (!Array.isArray(argv)) return null;
  const p = argv.flatMap((a) => (/\s/.test(String(a ?? "")) ? String(a).split(/[\s;&|()]+/) : [String(a ?? "")]))
    .map((x) => x.replace(/^['"]+|['"]+$/g, "")).filter(Boolean);
  const i = p.findIndex((x) => /(^|[\\/])ssh(\.exe)?$/i.test(x));
  if (i < 0) return null;
  for (let j = i + 1; j < p.length; j++) {
    const x = p[j];
    if (x.startsWith("-")) { if (x.length === 2 && OPZIONI_CON_VALORE.has(x[1])) j++; continue; }
    return x.replace(/^[^@]*@/, "").toLowerCase();
  }
  return null;
}
// L'argv raggiunge la macchina di `s`. Una riga senza argv d'aggancio (un'interattiva) non lo dice: vale.
export const stessoPosto = (argv, s) => !Array.isArray(s?.attach) || !s.attach.length || sshDi(argv) === sshDi(s.attach);

// L'id della sessione che l'argv di una scheda aggancia, nelle stesse due forme: "attach" come parola a
// sé (Mac, Linux) o dentro la riga di una shell, come pwsh -Command "& '…' 'attach' '<id>'" su Windows.
// Senza la seconda forma, su Windows la testata, il pannello Da fare e Lavoraci non vedevano mai la
// sessione agganciata (12/11/2026). "" se l'argv non aggancia niente.
export function idAggancio(argv) {
  if (!Array.isArray(argv)) return "";
  const i = argv.indexOf("attach");
  if (i >= 0) return String(argv[i + 1] ?? "");
  for (const a of argv) {
    const m = typeof a === "string" && a.match(/\battach['"]?\s+['"]?([\w-]{4,})/);
    if (m) return m[1];
  }
  return "";
}

// L'argv con cui la scheda lancia l'aggancio. Per ssh aggiunge un tetto alla connessione e il battito:
// senza, una macchina spenta tiene la scheda vuota per più di un minuto, e dopo il sonno del portatile
// la scheda resta ferma su una connessione morta, che il clic riporta davanti com'è. Col battito ssh
// esce entro 45 secondi, la scheda resta con la shell e il clic dopo rilancia l'aggancio.
// L'argv dell'elenco (campo attach) resta quello della sonda: lo leggono microfono.js e i confronti.
export const OPZIONI_SSH = ["-o", "ConnectTimeout=10", "-o", "ServerAliveInterval=15", "-o", "ServerAliveCountMax=3"];
export function argvScheda(argv) {
  const a = Array.isArray(argv) ? argv.map(String) : [];
  if (a.length < 3 || !/(^|[\\/])ssh(\.exe)?$/.test(a[0]) || a[1] !== "-t" || a.includes("ServerAliveInterval=15")) return a;
  return [a[0], "-t", ...OPZIONI_SSH, ...a.slice(2)];
}

// Windows. Un programma con un percorso di Windows (C:\... o C:/...): la scheda che lo lancia ha PowerShell.
export const percorsoWindows = (a) => /^[A-Za-z]:[\\/]/.test(String(a ?? ""));
// La shell di una scheda è PowerShell (pwsh.exe, powershell.exe, anche col percorso intero).
export const shellPowerShell = (a) => /(^|[\\/])(pwsh|powershell)(\.exe)?$/i.test(String(a ?? ""));
// Lo schermo di una scheda PowerShell finisce col prompt ("PS C:\Users\x>"): il comando è uscito e la
// shell aspetta. Con Claude acceso l'ultima riga è la sua barra; mentre ssh si collega è la riga lanciata.
export function promptPowerShell(schermo) {
  const righe = String(schermo ?? "").replace(/\u001b\[[0-9;?<>]*[A-Za-z]/g, "").split(/\r?\n/).filter((r) => r.trim());
  return righe.length > 0 && /^PS [^>]*>\s*$/.test(righe[righe.length - 1]);
}

// Perché Claude è uscito dalla scheda appena agganciata, dallo schermo della scheda (hc read): la
// frase per la riga della sessione, e `fermo` quando riprovare o riavviare non cambia niente (la causa
// sta nella macchina o nella connessione). null se lo schermo non dice niente di riconoscibile.
// Conta solo l'ultimo tentativo: il testo dopo l'ultimo comando di aggancio scritto nella shell.
const USCITE = [
  [/EINTR|Interrupted system call/, (m) => `Su ${m} Claude non riesce a leggere la cartella della sessione (Interrupted system call): finché ${m} non torna a posto le sessioni ferme non ripartono.`],
  [/Host key verification failed/, (m) => `ssh non riconosce ${m} (Host key verification failed): collegati una volta a mano da un terminale.`],
  [/Permission denied \(/, (m) => `${m} rifiuta l'accesso via ssh (Permission denied).`],
  [/Could not resolve hostname|No route to host|Network is unreachable|Operation timed out|Connection timed out|Connection refused|Connection closed by|Connection reset/, (m) => `${m} non si raggiunge via ssh: è spenta, dorme o è fuori rete.`],
  [/No job matching/, (m) => `Su ${m} questa sessione non c'è più: eliminala da Altro.`],
  [/Not logged in/, (m) => `Su ${m} Claude non è collegato all'account (Not logged in): apri Claude su ${m} e fai /login.`],
  [/Workspace not trusted/, (m) => `Su ${m} la cartella della sessione non è fra quelle fidate di Claude (Workspace not trusted).`],
  [/command not found|No such file or directory|is not recognized as/, (m) => `Su ${m} non trovo il programma claude dove lo cerca l'aggancio.`],
];
export function motivoUscita(schermo, s) {
  const m = s?.questa ? "questa macchina" : (s?.macchina ?? s?.host ?? "quella macchina");
  const righe = String(schermo ?? "").replace(/\u001b\[[0-9;?]*[A-Za-z]/g, "").split("\n");
  let da = 0;
  // anche la riga di PowerShell, dove ogni argomento sta fra apici: "& '…ssh.exe' … 'attach' 'a8ee6d5e'"
  righe.forEach((r, i) => { if (/[%$#>]\s.*\battach['"]?\s+['"]?[\w-]{4,}/.test(r)) da = i; });
  const coda = righe.slice(da).join("\n");
  for (const [re, frase] of USCITE) if (re.test(coda)) return { testo: frase(m), fermo: true };
  const u = [...coda.matchAll(/Session \S+ (?:has exited|can't start)\s*(?:\(|—|-)?\s*([^\n]*)/g)].pop();
  const perche = (u?.[1] ?? "").replace(/^[\s(—-]+|[\s).]+$/g, "").slice(0, 90);
  // "before init": il processo della sessione muore prima di caricare la conversazione; il resto del
  // messaggio è un pezzo di traccia interna, che alla persona non dice niente.
  if (/before init/.test(perche)) return { testo: `Su ${m} la sessione non riesce a partire: Claude esce prima di iniziare (${perche.match(/exit \d+ before init/)?.[0] ?? "before init"}). Prova da ${m}, o riavvia ${m}.`, fermo: false };
  if (perche) return { testo: `Su ${m} Claude esce appena parte (${perche}).`, fermo: false };
  return null;
}

// I gesti sulla riga di una sessione in background, oltre al clic che la apre (claude attach, anche se
// lavora): l'anteprima (anteprima() qui sotto, o claude logs senza trascrizione), ferma (stop) se è viva, riavvia (respawn) dopo un errore, elimina
// (rm, con conferma) se è chiusa o in errore. Un'interattiva e una riga vecchia non ne hanno: si aprono e basta.
export function azioni(s) {
  if (!s || s.vecchia || s.tipo !== "background") return [];
  const out = [{ verbo: "logs", testo: "Anteprima" }];
  if (s.stato === "lavora" || s.stato === "aspetta") out.push({ verbo: "stop", testo: "Ferma" });
  if (s.stato === "errore") out.push({ verbo: "respawn", testo: "Riavvia" });
  // Elimina solo su una sessione chiusa o in errore: una ferma ma viva si chiude con Chiudi (/fine e stop)
  if (s.stato === "errore" || chiusa(s)) out.push({ verbo: "rm", testo: "Elimina", conferma: "Sì, elimina" });
  return out;
}

// Il menu del tasto destro su una sessione (#5291), in tre gruppi (menusessione.js). Primo: Apri è il
// clic; Duplica ne apre una nuova e vuota nella stessa cartella, sulla stessa macchina, nello stesso
// progetto; Fork ne apre una con una copia della conversazione; "Sposta in un progetto…" è il taglia e
// incolla (Federico, 12/11/2026: "tagliare"), il dialogo di cambio.js (#5292). Secondo: Rinomina e il
// contesto del progetto (contestoui.js), se la sessione ne ha uno. Terzo: Chiudi (/fine, poi stop, come
// ⌘W) e i gesti di "Altro", senza Ferma: qui la ferma Chiudi. Un'interattiva non ha un lavoro in
// background da fermare: resta senza Chiudi. Una riga vecchia non ha menu.
export function menu(s) {
  if (!s || s.vecchia) return [];
  const out = [{ verbo: "apri", testo: "Apri" }, { verbo: "duplica", testo: "Duplica" }, { verbo: "fork", testo: "Fork" },
    { verbo: "progetto", testo: "Sposta in un progetto…" }];
  // Sposta su… (12/11/2026): la stessa conversazione su un'altra macchina, col popup di sposta.js. Solo in
  // background; il menu la toglie se Volta non conosce altre macchine (menusessione.js).
  if (s.tipo === "background") out.push({ verbo: "sposta", testo: "Sposta su…" });
  out.push({ verbo: "rinomina", testo: "Rinomina…" });
  if (s.progetto) out.push({ verbo: "contesto", testo: "Contesto del progetto" });
  // in errore non c'è un /fine da fare: lì c'è Elimina (azioni)
  if (s.tipo === "background" && !chiusa(s) && s.stato !== "errore") out.push({ verbo: "chiudi", testo: "Chiudi con /fine" });
  return out.concat(azioni(s).filter((a) => a.verbo !== "stop"));
}

// I primi due gruppi del menu (copiare e spostare, nome e contesto); il resto va nel terzo, chiudere.
export const GRUPPI_MENU = [["apri", "duplica", "fork", "progetto", "sposta"], ["rinomina", "contesto"]];

// La X della riga (Federico, 12/11/2026: "la X per chiudere e innescare il processo di fine"): su una
// sessione in background viva è Chiudi con /fine, con la conferma; su una chiusa o in errore è Elimina.
// Un'interattiva e una riga vecchia non hanno X: non hanno un congedo.
export function xRiga(s) {
  if (!s || s.vecchia || s.tipo !== "background") return null;
  const rm = azioni(s).find((a) => a.verbo === "rm");
  if (rm) return { ...rm, aiuto: "Elimina la sessione" };
  return { verbo: "chiudi", testo: "Chiudi", conferma: "Chiudi con /fine?", aiuto: "Chiudi: Claude salva con /fine, poi la sessione si ferma" };
}

// I gesti che stanno solo nel menu: lavorano sulla riga, senza aprire il riquadro di "Altro".
export const SOLO_MENU = new Set(["apri", "chiudi", "duplica", "fork", "rinomina", "progetto", "sposta", "contesto"]);

// Le voci del menu che aprono il dialogo, e che cosa cambiano.
export const CAMBIA = { rinomina: "nome", progetto: "progetto" };

// Nome e progetto di una sessione si cambiano dalla finestra (#5292). Il nome scritto dalla persona:
// una riga, senza caratteri di controllo, al più 60 caratteri come un titolo. Vuoto vuol dire "torna
// al titolo automatico".
export const nomeNuovo = (testo) => String(testo ?? "").replace(/[\u0000-\u001f\u007f-\u009f]/g, " ").replace(/\s+/g, " ").trim().slice(0, 60).trim();

// Il progetto scritto dalla persona come slug, con la stessa regola di slug() in dati.js: "Due Mondi"
// diventa "due-mondi". Al più 40 caratteri, come la scheda del terminale. Vuoto se non resta niente.
export const progettoNuovo = (testo) => String(testo ?? "").toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "")
  .replace(/[^a-z0-9-]+/g, "-").replace(/^-+|-+$/g, "").slice(0, 40).replace(/-+$/, "");

// I progetti fra cui scegliere nel dialogo: quelli delle sessioni dell'elenco e quelli che passa chi
// chiama (spazi aperti, cartelle della base), senza doppi, in ordine alfabetico. Un nome alternativo vale
// la chiave del suo progetto: una sessione nata nella cartella volta-celeste e il progetto herdr-arturo
// sono una riga sola, "Volta" (#5506).
export function progettiNoti(dati, altri = []) {
  const visti = new Set();
  for (const p of [...(dati?.sessioni ?? []).map((s) => s.progetto), ...altri]) {
    const k = progettoNuovo(chiaveProgetto(p));
    if (k) visti.add(k);
  }
  return [...visti].sort((a, b) => a.localeCompare(b));
}

// I progetti noti che corrispondono a ciò che la persona sta scrivendo: prima quelli che cominciano così.
export function filtraProgetti(noti, testo, quanti = 8) {
  const f = progettoNuovo(testo);
  const l = noti ?? [];
  // cerca nello slug e nel titolo ("volta" trova herdr-arturo, che si chiama Volta)
  const nomi = (p) => [p, slugDi(nomeProgetto(p))];
  const presi = f ? [...l.filter((p) => nomi(p).some((x) => x.startsWith(f))), ...l.filter((p) => !nomi(p).some((x) => x.startsWith(f)) && nomi(p).some((x) => x.includes(f)))] : l;
  return presi.slice(0, quanti);
}

// La ricerca di ⌘K e ⌘O (#5369, nota di Federico dell'11/11: "accedere a chat e progetti"): un elenco
// solo di sessioni e progetti. Il testo si confronta senza maiuscole, accenti e trattini, col titolo e il
// nome della sessione, col suo progetto e col titolo, lo slug e i nomi alternativi (NOTI) di un progetto.
// Prima chi comincia col testo, poi chi lo contiene; le sessioni chiuse in fondo, perché si riaprono ma
// sono il caso raro. Senza testo: le sessioni vive più recenti (al più VIVE_SENZA_TESTO), poi i progetti
// nell'ordine dato. Con un testo l'ultima voce è sempre "Nuova richiesta" con quel testo, anche quando
// qualcosa corrisponde: chi scrive una frase intera vuole quasi sempre chiederla.
// Righe: { tipo: "sessione", s } | { tipo: "progetto", nome } | { tipo: "nuova", testo }.
export const VIVE_SENZA_TESTO = 5;
const piano = (x) => String(x ?? "").toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, "").replace(/[^a-z0-9]+/g, " ").trim();
const alternativi = (p) => {
  const k = chiaveProgetto(p);
  return k ? Object.keys(NOTI).filter((a) => NOTI[a]?.chiave === k) : [];
};
export function cerca(sessioni, progetti, testo, quanti = 12) {
  const f = piano(testo);
  const ss = [...(sessioni ?? [])].filter((s) => s && s.sessionId).sort((a, b) => tempo(b) - tempo(a));
  const pp = [...new Set((progetti ?? []).filter(Boolean))];
  if (!f) {
    const vive = ss.filter((s) => !chiusa(s)).slice(0, VIVE_SENZA_TESTO).map((s) => ({ tipo: "sessione", s }));
    return [...vive, ...pp.map((nome) => ({ tipo: "progetto", nome }))].slice(0, quanti);
  }
  // 0: comincia col testo, 1: lo contiene, null: niente
  const voto = (campi) => {
    const c = campi.map(piano).filter(Boolean);
    return c.some((x) => x.startsWith(f)) ? 0 : c.some((x) => x.includes(f)) ? 1 : null;
  };
  const prese = [];
  ss.forEach((s, i) => {
    const v = voto([titolo(s), s.nome, s.progetto, s.progetto ? nomeProgetto(s.progetto) : "", ...alternativi(s.progetto), s.id]);
    if (v !== null) prese.push({ riga: { tipo: "sessione", s }, chiusa: chiusa(s) ? 1 : 0, v, i });
  });
  pp.forEach((nome, i) => {
    const v = voto([nome, nomeProgetto(nome), ...alternativi(nome)]);
    if (v !== null) prese.push({ riga: { tipo: "progetto", nome }, chiusa: 0, v, i: ss.length + i });
  });
  prese.sort((a, b) => a.chiusa - b.chiusa || a.v - b.v || a.i - b.i);
  return [...prese.slice(0, quanti - 1).map((x) => x.riga), { tipo: "nuova", testo: String(testo).trim() }];
}

// Il comando di "Nuova richiesta" dalla ricerca: il testo viaggia in esadecimale come in comandoCambio,
// al più TESTO_NUOVA_MAX caratteri (il resto la persona lo scrive nella sessione).
export const TESTO_NUOVA_MAX = 400;
export const comandoNuova = (testo) => `arturo.nuova-${codifica(String(testo ?? "").trim().slice(0, TESTO_NUOVA_MAX))}`;

// Il dialogo è un'altra copia del mod: manda il cambio alla barra come comando, lo stesso di herdr-app
// do. Il testo viaggia in esadecimale (quattro cifre per carattere), perché il nome di un comando non
// porta spazi né accenti: "arturo.volta-cambia-<nome|progetto>-<esadecimale>-<chiave>", con la chiave
// macchina:id (#5643): dopo uno spostamento il solo id sta su due macchine.
export const codifica = (testo) => [...String(testo ?? "")].flatMap((c) => c.length === 2 ? [c.charCodeAt(0), c.charCodeAt(1)] : [c.charCodeAt(0)])
  .map((n) => n.toString(16).padStart(4, "0")).join("");
export const decodifica = (hex) => (String(hex ?? "").match(/[0-9a-f]{4}/g) ?? []).map((h) => String.fromCharCode(parseInt(h, 16))).join("");
export const comandoCambio = (s, cosa, valore) => `arturo.volta-cambia-${cosa}-${codifica(valore)}-${chiave(s)}`;

// Il comando di un cambio come lo riceve la barra (senza "arturo."): { cosa, valore, id } con il valore
// già ripulito, oppure null. Un progetto vuoto non è un cambio; un nome vuoto toglie il nome scritto.
export function leggiCambio(c) {
  const m = /^volta-cambia-(nome|progetto)-((?:[0-9a-f]{4})*)-(.+)$/.exec(String(c ?? ""));
  if (!m) return null;
  const valore = m[1] === "nome" ? nomeNuovo(decodifica(m[2])) : progettoNuovo(decodifica(m[2]));
  if (m[1] === "progetto" && !valore) return null;
  return { cosa: m[1], valore, id: m[3] };
}

// La casella di Claude Code è vuota, cioè si può scrivere un comando senza toccare una bozza: fra le
// ultime due righe di bordo c'è il solo segno del prompt, o il suggerimento (Try "..."). Come
// casella_vuota di teletrasporto.py. `schermo` è il testo di hc read.
export function casellaVuota(schermo) {
  const testo = String(schermo ?? "").replace(/\u001b\[[0-9;]*m/g, "").replace(/\u00a0/g, " ")
    .replace(/(\u2500{20,})(\u276f|>|  )/g, "$1\n$2");
  const righe = testo.split("\n").map((r) => r.trim());
  const bordi = righe.map((r, i) => (r.startsWith("\u2500".repeat(20)) && r.endsWith("\u2500") ? i : -1)).filter((i) => i >= 0);
  if (bordi.length < 2) return false;
  const dentro = righe.slice(bordi[bordi.length - 2] + 1, bordi[bordi.length - 1]).filter(Boolean);
  if (dentro.length !== 1 || !["\u276f", ">"].includes(dentro[0][0])) return false;
  const t = dentro[0].slice(1).trim();
  return t === "" || /^Try ".*"$/.test(t);
}

// Il nome scritto dalla persona va portato in Claude Code con /rename (campo daPortare della sonda):
// solo quando la sessione è ferma, perché un comando scritto mentre lavora finirebbe in coda al turno.
export const daPortare = (s) => (s && !s.vecchia && s.stato === "ferma" && typeof s.daPortare === "string" && s.daPortare.trim() ? s.daPortare.trim() : null);

// Il progetto da cui una sessione spostata deve ripartire con /inizio (#5465): solo a sessione ferma,
// mai mentre lavora o aspetta un permesso, e solo uno slug valido (va dentro un comando).
export const daIniziare = (s) => (s && !s.vecchia && s.stato === "ferma" && typeof s.daIniziare === "string"
  && /^[a-z0-9][a-z0-9-]{0,39}$/.test(s.daIniziare) ? s.daIniziare : null);

// Trascinare una sessione su un altro progetto, nella vista per progetto (Federico, 12/11/2026: "voglio
// poter fare drag & drop"). Herdr non ha un trascinamento per i mod: volta.js lo costruisce con
// pressione, movimento e rilascio del mouse. Sotto MOSSA_PX di movimento è un clic, che apre la sessione.
export const MOSSA_PX = 6;
export const mosso = (da, a) => Boolean(da && a) && Math.hypot(a.x - da.x, a.y - da.y) >= MOSSA_PX;

// Lo slug del progetto dove finisce la sessione trascinata `t` ({ s, mosso }) lasciata sul gruppo `g`, o
// null: nella vista per macchina, su "Senza progetto", sul progetto dove sta già, senza movimento, con la
// macchina della sessione che non risponde.
export function arrivoTrascino(t, g, modo) {
  if (!t?.s || !t.mosso || t.s.vecchia || modo !== "progetto" || !g?.chiave) return null;
  if (chiaveProgetto(t.s.progetto) === g.chiave) return null;
  return progettoNuovo(g.chiave) || null;
}

// Il nome della copia di una conversazione: "<titolo> (fork)", entro i 60 caratteri di un titolo.
export const titoloFork = (s) => `${titolo(s).slice(0, 53).trim()} (fork)`;

// L'Anteprima di una sessione senza aprirla (#5240): l'ultima risposta e l'ultima azione che la sonda
// legge dalla trascrizione (campi risposta e azione), come blocchi { etichetta, righe } da mandare a
// capo. Del markdown toglie solo i segni (grassetto, codice, titoli, citazioni): i nomi col trattino
// basso restano interi. null se la trascrizione manca: allora Volta mostra lo schermo di claude logs.
const senzaSegni = (r) => r.replace(/\*\*|`/g, "").replace(/^\s*(#+|>)\s*/, "").replace(/\s+/g, " ").trim();
export function anteprima(s) {
  const righe = String(s?.risposta ?? "").split("\n").map(senzaSegni).filter(Boolean);
  const azione = senzaSegni(String(s?.azione ?? "").replace(/\s+/g, " ")).replace(/:$/, "");
  const out = [];
  if (righe.length) out.push({ etichetta: "Ultima risposta", righe });
  if (azione) out.push({ etichetta: "Ultima azione", righe: [azione] });
  return out.length ? out : null;
}

const conversazione = (s) => `${s.host}/${s.sessionId}`;

// Le sessioni che da una lettura all'altra sono passate a "ti aspetta", di qualunque macchina.
// Alla prima lettura nessuna: l'avviso è per un cambio, non per chi aspettava già all'apertura.
export function nuoveInAttesa(prima, dopo) {
  if (!prima) return [];
  const era = new Map((prima.sessioni ?? []).map((s) => [conversazione(s), s.stato]));
  return (dopo?.sessioni ?? []).filter((s) => !s.vecchia && s.stato === "aspetta" && era.get(conversazione(s)) !== "aspetta");
}

// Lo stato di ogni sessione per id corto, per le parti che agganciano una sessione in background in
// una scheda: lì Herdr non ha lo stato del terminale, e lo prendono da qui (shared arturo.volta.stati).
// Lo stesso id su due macchine (una sessione spostata, #5577): resta la copia che non è ferma, come in
// unaPerConversazione; prima vinceva l'ultima dell'elenco, e la scheda mostrava ferma la copia viva.
// Un id su più macchine porta `doppio`: le parti senza elenco (schedeDi di dati.js) sanno così che
// un'etichetta vecchia col solo id non dice quale copia è (#5634).
export function statiCorti(dati) {
  /** @type {Record<string, { stato: string, host: string, doppio?: true }>} */
  const out = {};
  const l = dati?.sessioni ?? [];
  for (const s of l) {
    if (!s.id || s.vecchia) continue;
    if (out[s.id] && out[s.id].stato !== "ferma" && s.stato === "ferma") continue;
    out[s.id] = { stato: s.stato, host: s.host, ...(doppio(l, s.id) ? { doppio: true } : {}) };
  }
  return out;
}

// La versione del mod nel menu di "Impostazioni" (shared arturo.mod, lo scrive controllaMod di volta.js; la disegna Impostazioni di comuni.js):
// "mod abc1234 · 09:52", l'ora dell'ultima installazione (col giorno se non è oggi). Dopo un giorno
// senza riuscire a controllare lo dice, col motivo; così un plugin di Arturo bloccato perché forse manomesso. Dal 13/11 la riga sta nel menu di Impostazioni, e il piede ne mostra solo il pallino (#5371).
export function rigaMod(m, adesso = Date.now()) {
  if (!m?.corta) return null;
  const due = (n) => String(n).padStart(2, "0");
  // Un aggiornamento di Arturo fermato per una possibile compromissione (volta_mod.py programmi): non si riprova da solo.
  const plugin = m.programmi?.plugin;
  if (plugin?.esito === "compromesso") return { testo: `mod ${m.corta} · Arturo non si aggiorna`, avviso: plugin.motivo || "possibile compromissione: non aggiornare e segnalalo" };
  if (m.esito === "errore" && m.giu_da && adesso / 1000 - m.giu_da > 86400) {
    const giorni = Math.floor((adesso / 1000 - m.giu_da) / 86400);
    return { testo: `mod ${m.corta} · non controllo da ${giorni} ${giorni === 1 ? "giorno" : "giorni"}`, avviso: m.motivo ?? "" };
  }
  if (!m.installato) return { testo: `mod ${m.corta}` };
  const d = new Date(m.installato * 1000);
  const oggi = new Date(adesso);
  const giorno = d.toDateString() === oggi.toDateString() ? "" : `${d.getDate()}/${d.getMonth() + 1} `;
  return { testo: `mod ${m.corta} · ${giorno}${due(d.getHours())}:${due(d.getMinutes())}` };
}

// Le animazioni delle righe (#5410). Le sessioni nuove fra due letture: entrano in dissolvenza. Alla prima
// lettura niente, altrimenti tutto l'elenco entrerebbe insieme all'apertura della finestra.
export function entrate(prima, dopo) {
  if (!prima?.sessioni) return [];
  const viste = new Set(prima.sessioni.filter((s) => s?.id).map(chiave));
  return (dopo?.sessioni ?? []).filter((s) => s?.id).map(chiave).filter((k) => !viste.has(k));
}

// I tempi: una riga entra in 180 ms e se ne va in 140 (uscire costa meno che entrare). Le righe di un
// gruppo che si apre entrano una dopo l'altra, 30 ms fra l'una e l'altra, al più 120 ms in tutto.
export const ENTRA = { duration: 180, easing: "ease-out" };
export const ESCE = { duration: 140, easing: "ease-in" };
export const SCALA_MS = 30;
export const SCALA_MAX = 120;

// Opacità e transizione di una riga. `entra`: { fase, ritardo } di una riga che entra, o undefined. In fase
// "prima" la riga disegna 0 senza transizione, così il motore parte da lì; in fase "via" chiede 1 con ENTRA
// e il ritardo della scala. `esce`: la riga se ne va, verso 0 con ESCE.
export function motoRiga(entra, esce) {
  if (esce) return { opacita: 0, politica: ESCE };
  if (entra?.fase === "prima") return { opacita: 0, politica: null };
  if (entra?.fase === "via") return { opacita: 1, politica: { ...ENTRA, delay: entra.ritardo ?? 0 } };
  return { opacita: 1, politica: ENTRA };
}
export const ritardo = (i) => Math.min(i * SCALA_MS, SCALA_MAX);

// Sposta su e Sposta tutto su (sposta.js, 12/11/2026): chi si sposta e come si conta.
// Perché la sessione non si può spostare, o null. Solo quelle in background: un'interattiva sta in un
// Terminale, e il suo processo non si ferma da qui. Una che lavora si sposta lo stesso, a turno finito
// (aFineTurno): la coda di volta.js aspetta che il turno finisca.
export function nonSiSposta(s) {
  if (!s) return "Nessuna sessione in questa scheda.";
  if (s.tipo !== "background") return "Si spostano solo le sessioni in background, non quelle aperte in un Terminale.";
  return null;
}

// Una sessione che sta facendo un turno parte dopo, quando il turno finisce.
export const aFineTurno = (s) => s?.stato === "lavora";

// Le sessioni di "Sposta tutto su <dest>": in background, vive (né chiuse, né in errore, né di una
// macchina che non risponde), non già su `dest`. `sessioni` è l'elenco visibile di Volta (visibili()).
export const spostabili = (sessioni, dest) => (sessioni ?? []).filter((s) => !s.vecchia && !chiusa(s)
  && s.stato !== "errore" && !nonSiSposta(s) && (s.host ?? "qui") !== dest);

// Quello che passa al popup, che è un'altra copia del mod: i soli campi che servono, non la riga intera.
export const perSposta = (s) => (s ? { id: s.id, sessionId: s.sessionId, host: s.host ?? "qui", macchina: s.macchina,
  tipo: s.tipo, stato: s.stato, titolo: titolo(s), progetto: s.progetto ?? null } : null);

// Il conto di "Sposta tutto" su `dest`, per il popup: "3 sessioni", "3 sessioni, 1 a turno finito".
export function contoTutto(sessioni, dest) {
  const l = spostabili(sessioni, dest);
  if (!l.length) return { n: 0, testo: "niente da spostare" };
  const dopo = l.filter(aFineTurno).length;
  return { n: l.length, testo: `${l.length === 1 ? "1 sessione" : `${l.length} sessioni`}${dopo ? `, ${dopo} a turno finito` : ""}` };
}

// La macchina dove nasce un progetto aperto da Volta. La scheda del progetto nella memoria dice in
// `macchina:` dove sta la sua cartella, con etichette corte scelte dalla persona ("ufficio", "portatile").
// Volta conosce le macchine coi nomi di Herdr (host e nome leggibile). Un'etichetta vale per una macchina
// quando, tolti spazi e segni, sta dentro il suo host o il suo nome. Torna l'host della prima macchina della
// scheda che risponde, oppure null: la cartella c'è anche qui, la scheda non lo dice, o nessuna risponde.
// Con null vale "Nasce su", come prima.
const compatto = (x) => String(x ?? "").toLowerCase().replace(/[^a-z0-9]/g, "");
export function macchinaDelProgetto(etichette, macchine) {
  const voglio = (etichette ?? []).map(compatto).filter(Boolean);
  const tutte = Array.isArray(macchine) ? macchine : [];
  const questa = tutte.find((m) => m?.questa);
  if (!voglio.length || !questa) return null;
  const tocca = (m, e) => compatto(m?.host).includes(e) || compatto(m?.macchina).includes(e);
  if (voglio.some((e) => tocca(questa, e))) return null;
  for (const e of voglio) {
    const m = tutte.find((x) => x && !x.questa && !x.giu && x.host && tocca(x, e));
    if (m) return m.host;
  }
  return null;
}
