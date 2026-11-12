// Volta Celeste: le sessioni di Claude di tutte le macchine, come le legge teletrasporto.py volta.
// Modulo puro, senza herdr: raggruppa, ordina, scrive le frasi e decide cosa fa un clic.
// Lo prova il banco HZ17-HZ19 con node (tests/test_herdr_2026_11_08.py).
//
// Una riga del file (~/.cache/volta/sessioni.json, campo "sessioni"):
// { macchina, host, questa, sessionId, id, nome, progetto, titolo, stato: aspetta|lavora|ferma|errore,
//   tipo: background|interattiva, attach: argv | null, cartella, ultimo, risposta, azione, vecchia?,
//   daPortare?: il nome scritto dalla persona che Claude Code non ha ancora (rinomina, #5292) }

export const MODI = { macchina: "Per macchina", progetto: "Per progetto" };
export const SENZA = "Senza progetto";

// Il riquadro dei gesti di "Altro" sta sotto l'elenco con al più 160 px: un'anteprima lunga scorre lì
// dentro. L'elenco prende il resto della colonna (12/11/2026: niente più tetto, la sezione dei progetti
// aperti non c'è più).
export const GESTI_MAX = 160;

const tempo = (s) => Date.parse(s.ultimo || "") || 0;

// I progetti noti, da shared arturo.progetti della barra: { slug o nome alternativo: { chiave, titolo } }.
// Il titolo vero ("Volta", "Post Office") sta nella scheda del progetto (arturo progetti, campo titolo:) o
// nella fonte dei task; un nome alternativo porta alla chiave del suo progetto. Ogni parte del mod gira
// in una sua copia: chi mostra nomi di progetto li imposta prima del disegno (progettiNoti di volta.js e
// cambio.js). Senza, vale il nome ricavato dallo slug.
let NOTI = {};
export function impostaProgetti(mappa) { NOTI = mappa && typeof mappa === "object" ? mappa : {}; }
const slugDi = (p) => String(p ?? "").toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "").replace(/[^a-z0-9-]+/g, "-").replace(/^-+|-+$/g, "");
// La chiave del progetto: quella del suo gruppo anche quando la sessione porta un nome alternativo.
export const chiaveProgetto = (p) => (p ? NOTI[slugDi(p)]?.chiave ?? String(p) : "");

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

// La frase di stato e il colore del tema (blocked, working, done, idle, muted, dim).
export function fraseStato(s, adesso = Date.now()) {
  if (s.vecchia) return { testo: "Ultima lettura: la macchina non risponde", colore: "dim" };
  if (s.stato === "aspetta") return { testo: "Ti aspetta", colore: "blocked" };
  if (s.stato === "lavora") return { testo: "Sta lavorando", colore: "working" };
  if (s.stato === "errore") return { testo: "Si è fermata con un errore", colore: "blocked" };
  const q = daQuanto(s.ultimo, adesso);
  return { testo: q ? `Ferma ${q}` : "Ferma", colore: "muted" };
}

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
    if (giu.length && out.length) out[out.length - 1].nota = `${giu.join(", ")} non ${giu.length > 1 ? "rispondono" : "risponde"}`;
    return out;
  }
  for (const m of dati?.macchine ?? []) metti(m.host, m.macchina, null);
  for (const s of righe) metti(s.host, s.macchina, s);
  const out = [];
  for (const m of dati?.macchine ?? []) {
    const g = per.get(m.host);
    if (m.irraggiungibile) g.nota = g.sessioni.length ? "Non risponde: mostro l'ultima lettura" : "Non risponde";
    if (g.sessioni.length || g.nota) out.push(g);
    per.delete(m.host);
  }
  return out.concat([...per.values()].filter((g) => g.sessioni.length)).sort((a, b) => recente(b) - recente(a));
}

// Chiudere una sessione (12/11/2026, decisione di Federico): ⌘W, la X della scheda o Chiudi del menu
// fanno il congedo, cioè /fine e poi claude stop. Una sessione chiusa o in congedo non compare più
// nell'elenco: si ritrova con Apri un progetto. Chiusa = in background, senza processo e senza status
// (claude agents dopo claude stop: sonda S1 dell'11/11); una in errore resta, perché Riavvia serve.
export const chiusa = (s) => Boolean(s) && s.tipo === "background" && s.chiusa === true;
export function visibili(dati, congedi = {}) {
  if (!dati) return dati;
  const via = new Set(Object.values(congedi ?? {}).flatMap((c) => [c.sessionId, c.id].filter(Boolean)));
  return { ...dati, sessioni: (dati.sessioni ?? []).filter((s) => !chiusa(s) && !via.has(s.sessionId) && !via.has(s.id)) };
}

// Le schede chiuse da chi usa la finestra: i terminali che agganciavano una sessione al giro di prima e
// ora non ci sono più, tolti quelli che ha chiuso Volta stessa (`tolti`: indirizzo → ms, per Sposta,
// Cambia progetto, Stacca) negli ultimi TOLTI_MS. `prima` e `adesso`: { indirizzo: sessione }.
export const TOLTI_MS = 60000;
export function sparite(prima, adesso, tolti = {}, ora = Date.now()) {
  if (prima == null) return [];  // il primo giro dopo l'apertura solo guarda
  const viste = new Set();
  const out = [];
  for (const [ind, s] of Object.entries(prima)) {
    if (ind in (adesso ?? {}) || (tolti?.[ind] && ora - tolti[ind] < TOLTI_MS) || !s?.sessionId || viste.has(s.sessionId)) continue;
    // un'altra scheda aggancia ancora la stessa sessione: chiusa una copia, la sessione resta aperta
    if (Object.values(adesso ?? {}).some((x) => x?.sessionId === s.sessionId)) continue;
    viste.add(s.sessionId);
    out.push(s);
  }
  return out;
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
    if (s.stato === "lavora" && ora - da < CONGEDO_MAX_MS) return { fai: "attendi" };
    return { fai: "fine", fase: "fine" };
  }
  if (c.fase === "fine") {
    if (ora - dal < CONGEDO_AVVIO_MS) return { fai: "attendi" };
    if (s.stato === "errore") return { fai: "togli", avviso: `${nome}: /fine si è fermato con un errore. La sessione resta ferma.` };
    if (chiusa(s)) return ora - dal > CONGEDO_SENZA_FINE_MS ? { fai: "togli", avviso: `${nome} non è ripartita per /fine: l'ho lasciata chiusa senza salvataggio.` } : { fai: "attendi" };
    if (s.stato === "aspetta") return { fai: "stop", fase: "ferma", avviso: `${nome} ha chiesto qualcosa durante /fine: l'ho fermata lo stesso.` };
    if (s.stato === "lavora") return ora - dal > CONGEDO_MAX_MS ? { fai: "stop", fase: "ferma", avviso: `${nome}: /fine non ha finito in 20 minuti, l'ho fermata.` } : { fai: "attendi" };
    // ferma e viva: /fine ha finito il turno se la trascrizione è andata avanti dopo la ripresa
    if (tempo(s) > dal - 5000) return { fai: "stop", fase: "ferma", salvata: true };
    return ora - dal > CONGEDO_SENZA_FINE_MS ? { fai: "stop", fase: "ferma", avviso: `${nome} non ha fatto /fine: l'ho fermata senza salvataggio.` } : { fai: "attendi" };
  }
  // fase "ferma": aspetta che claude agents la dica chiusa, e riprova lo stop dopo due minuti
  if (chiusa(s)) return c.salvata ? { fai: "rm" } : { fai: "togli" };
  return ora - dal > 120000 ? { fai: "stop", fase: "ferma" } : { fai: "attendi" };
}

// Le sessioni di un gruppo che l'elenco mostra: le vive sempre; le ferme solo se il gruppo è aperto, o se
// non ha vive e le ferme sono due o meno.
export function mostrate(g, aperto) {
  const vive = g.sessioni.filter((s) => s.stato !== "ferma");
  const ferme = g.sessioni.length - vive.length;
  return (!vive.length && ferme <= 2) || aperto ? g.sessioni : vive;
}

// Il giro fra le sessioni (⌘↓ e ⌘↑): le sessioni aperte, nell'ordine dell'elenco. Aperta vuol dire che
// lavora o ti aspetta, oppure che è ferma ma ha una scheda in questa finestra (`conScheda`, gli id). Una
// ferma senza scheda resta fuori: è chiusa con /fine o lasciata, e il tasto la riaggancerebbe (Federico,
// 12/11: "ha aperto piano gare bergamo che avevo chiuso"). Le ferme con scheda nascoste dietro "N ferme"
// vengono dopo le righe a vista del loro gruppo. Restano fuori anche le sessioni che stanno in un
// Terminale: il clic lì le sposta con /bg, e un giro di tasti non deve spostare niente.
export function ordineGiro(lista, aperti = {}, conScheda = new Set()) {
  return (lista ?? []).flatMap((g) => {
    const vista = mostrate(g, aperti[g.chiave]);
    return vista.concat(g.sessioni.filter((s) => !vista.includes(s)));
  })
    .filter((s) => s.stato !== "ferma" || conScheda.has(s.sessionId))
    .filter((s) => ["aggancia", "mostra"].includes(clic(s).azione)).map((s) => s.sessionId);
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

// La sessione dopo (verso 1) o prima (verso -1) di `corrente`, in tondo. Senza corrente, o con una
// corrente fuori dal giro: la prima andando avanti, l'ultima andando indietro. null a giro vuoto.
export function passoGiro(ids, corrente, verso) {
  if (!ids?.length) return null;
  const i = ids.indexOf(corrente);
  if (i < 0) return verso < 0 ? ids[ids.length - 1] : ids[0];
  return ids[(i + (verso < 0 ? -1 : 1) + ids.length) % ids.length];
}

// La sessione che una scheda mostra: per l'etichetta di Herdr (hc label arturo.sessione), per l'argv
// dell'aggancio, o perché è nata nella shell di quella scheda. null se la scheda non è di una sessione.
export function sessioneDi(terminale, sessioni) {
  if (!terminale) return null;
  const l = sessioni ?? [];
  return l.find((s) => s.id && terminale.labels?.["arturo.sessione"] === s.id)
    ?? l.find((s) => agganciata(terminale.argv, s))
    ?? l.find((s) => s.questa && s.terminale && s.terminale === terminale.address) ?? null;
}

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
const dentro = (a, id) => typeof a === "string" &&
  new RegExp(`\\battach['"]?\\s+['"]?${id.replace(/[^\w-]/g, "")}\\b`).test(a);
export const agganciata = (argv, s) => Array.isArray(argv) && !!s?.id &&
  ((argv.includes("attach") && argv.includes(s.id)) || argv.some((a) => dentro(a, s.id)));

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
  righe.forEach((r, i) => { if (/[%$#>]\s.*\battach\s+['"]?[\w-]{4,}/.test(r)) da = i; });
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
// (rm, con conferma) se è ferma. Un'interattiva e una riga vecchia non ne hanno: si aprono e basta.
export function azioni(s) {
  if (!s || s.vecchia || s.tipo !== "background") return [];
  const out = [{ verbo: "logs", testo: "Anteprima" }];
  if (s.stato === "lavora" || s.stato === "aspetta") out.push({ verbo: "stop", testo: "Ferma" });
  if (s.stato === "errore") out.push({ verbo: "respawn", testo: "Riavvia" });
  if (s.stato === "ferma" || s.stato === "errore") out.push({ verbo: "rm", testo: "Elimina", conferma: "Sì, elimina" });
  return out;
}

// Il menu del tasto destro su una sessione (#5291): Apri è il clic; Chiudi chiude la scheda e ferma la
// sessione (la conversazione resta, Apri la fa ripartire); Duplica ne apre una nuova e vuota nella stessa
// cartella, sulla stessa macchina, nello stesso progetto; Fork ne apre una con una copia della
// conversazione. Rinomina e Cambia progetto aprono il dialogo di cambio.js (#5292). Poi i gesti di
// "Altro", senza Ferma: qui la ferma Chiudi. Un'interattiva non ha un lavoro in background da fermare:
// resta senza Chiudi. Una riga vecchia non ha menu.
export function menu(s) {
  if (!s || s.vecchia) return [];
  const out = [{ verbo: "apri", testo: "Apri" }];
  if (s.tipo === "background") out.push({ verbo: "chiudi", testo: "Chiudi" });
  out.push({ verbo: "duplica", testo: "Duplica" }, { verbo: "fork", testo: "Fork" });
  out.push({ verbo: "rinomina", testo: "Rinomina" }, { verbo: "progetto", testo: "Cambia progetto" });
  return out.concat(azioni(s).filter((a) => a.verbo !== "stop"));
}

// I gesti che stanno solo nel menu: lavorano sulla riga, senza aprire il riquadro di "Altro".
export const SOLO_MENU = new Set(["apri", "chiudi", "duplica", "fork", "rinomina", "progetto"]);

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
// chiama (spazi aperti, cartelle della base), senza doppi, in ordine alfabetico.
export function progettiNoti(dati, altri = []) {
  const visti = new Set();
  for (const p of [...(dati?.sessioni ?? []).map((s) => s.progetto), ...altri]) {
    const k = progettoNuovo(p);
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

// Il dialogo è un'altra copia del mod: manda il cambio alla barra come comando, lo stesso di herdr-app
// do. Il testo viaggia in esadecimale (quattro cifre per carattere), perché il nome di un comando non
// porta spazi né accenti: "arturo.volta-cambia-<nome|progetto>-<esadecimale>-<id>".
export const codifica = (testo) => [...String(testo ?? "")].flatMap((c) => c.length === 2 ? [c.charCodeAt(0), c.charCodeAt(1)] : [c.charCodeAt(0)])
  .map((n) => n.toString(16).padStart(4, "0")).join("");
export const decodifica = (hex) => (String(hex ?? "").match(/[0-9a-f]{4}/g) ?? []).map((h) => String.fromCharCode(parseInt(h, 16))).join("");
export const comandoCambio = (s, cosa, valore) => `arturo.volta-cambia-${cosa}-${codifica(valore)}-${s.id}`;

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

const chiave = (s) => `${s.host}/${s.sessionId}`;

// Le sessioni che da una lettura all'altra sono passate a "ti aspetta", di qualunque macchina.
// Alla prima lettura nessuna: l'avviso è per un cambio, non per chi aspettava già all'apertura.
export function nuoveInAttesa(prima, dopo) {
  if (!prima) return [];
  const era = new Map((prima.sessioni ?? []).map((s) => [chiave(s), s.stato]));
  return (dopo?.sessioni ?? []).filter((s) => !s.vecchia && s.stato === "aspetta" && era.get(chiave(s)) !== "aspetta");
}

// Lo stato di ogni sessione per id corto, per le parti che agganciano una sessione in background in
// una scheda: lì Herdr non ha lo stato del terminale, e lo prendono da qui (shared arturo.volta.stati).
export function statiCorti(dati) {
  const out = {};
  for (const s of dati?.sessioni ?? []) if (s.id && !s.vecchia) out[s.id] = { stato: s.stato, host: s.host };
  return out;
}

// La versione del mod accanto a "Impostazioni" (shared arturo.mod, lo scrive controllaMod di volta.js; la disegna il piede di barra.js):
// "mod abc1234 · 09:52", l'ora dell'ultima installazione (col giorno se non è oggi). Dopo un giorno
// senza riuscire a controllare lo dice, col motivo. Il piede è alto 190 px: niente riga in più.
export function rigaMod(m, adesso = Date.now()) {
  if (!m?.corta) return null;
  const due = (n) => String(n).padStart(2, "0");
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
