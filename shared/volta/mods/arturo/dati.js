// I dati di Arturo per Herdr: configurazione, todo, progetti e le azioni che aprono Claude.
// Tutte le parti del mod leggono da qui, così dicono le stesse cose con le stesse parole.

import { exec, readTextFile, writeTextFile, appHome, home, hc, spaces, agents, run, notify, shared, setShared, terminals, panes } from "herdr";
import { TOLTI_MS, macchinaDelProgetto, riparteAlClic, voloArturo, esitoSposta, SPOSTA_OGNI_MS, titolo, chiave as chiaveSessione, etichettaDice, suaScheda, doppio, unaPerConversazione, titoloFork, casellaVuota, percheNonEntra, daPortare, daIniziare, argvScheda, motivoUscita, rigaRilancio, tastiPulizia, percorsoWindows, shellPowerShell, promptPowerShell, occupanti, idAggancio, slug, progettoDi, nomeMacchina as nomeMacchinaDi, etichettaVista, agganciataDa, macchinaIndirizzo, mia, daDi, argvRemoto, attachLocale, schedaDelProgetto } from "./sessioni.js";
import { tettoDi, entroDi, servizioAcceso, claudeDavanti, testoTodo } from "./sessioni.js";
import { promptCompito, avvisoCompito, avvisoAttesa, nomeProgetto as nomeProgettoDi, nomeChi, sa } from "./sessioni.js";
import { leggiUnione, vistaUnione, percheNonUnire, UNIONE_PROVA_MS, UNIONE_MS } from "./sessioni.js";

// arturo.json nella cartella di Herdr: lo scrive installa-herdr.sh.
// { "arturo": ["python3", "/Users/x/.claude/bin/arturo"], "radice": "/Users/x/.claude", "base": "/Users/x/Documents/ClaudeCode", "note_progetto": "arturo" }
export async function config() {
  let c = {};
  try {
    c = JSON.parse((await readTextFile(`${appHome()}/arturo.json`)) ?? "{}");
  } catch {
    c = {};
  }
  const arturo = Array.isArray(c.arturo) && c.arturo.length ? c.arturo : ["python3", `${home()}/.claude/bin/arturo`];
  // La cartella di Arturo, dove stanno shared/ e bin/: ~/.claude per chi usa il clone, un'altra cartella
  // per il plugin o per una copia di prova. Un arturo.json di prima ce l'ha solo nel bin: …/bin/arturo.
  // Chi ha Arturo come plugin non ha né l'una né l'altro (#6217): la dice il file che il plugin riscrive a
  // ogni sessione, poi la voce del plugin. Lo stesso ordine di radice_di() in volta_mod.py.
  const radice = (typeof c.radice === "string" && c.radice ? c.radice : null)
    ?? RADICE_BIN.exec(String(arturo[arturo.length - 1] ?? ""))?.[1]
    ?? (await radicePlugin())
    ?? `${home()}/.claude`;
  return {
    arturo,
    radice,
    // Chi usa la finestra (#6217): l'autore delle note e il nome che Claude scrive in "Prossimo passo:".
    // Di serie "tu": il nome vero lo dà la chiave.
    chi: nomeChi(c.chi),
    // Cosa sa fare l'Arturo installato: { note, unisci, tasks }. Un gesto senza la sua capacità non si mostra.
    capacita: await capacitaDi(radice),
    base: typeof c.base === "string" && c.base ? c.base : `${home()}/Documents/ClaudeCode`,
    // Il progetto delle note sulla finestra (⌘⇧N); senza, va al progetto aperto.
    note_progetto: typeof c.note_progetto === "string" && c.note_progetto ? c.note_progetto : null,
    // volta_sonda.py: "volta" in arturo.json (una copia di prova), altrimenti quello del mod. L'unico
    // punto che lo dice: lo usano l'elenco di Volta (volta.js) e la nascita su un'altra macchina.
    volta: typeof c.volta === "string" && c.volta ? c.volta : `${appHome()}/mods/arturo/volta_sonda.py`,
    // La macchina del capo (#5722): quella dove il giro orario di volta_capo.py scrive le carte UF della
    // Coda (task e bozze). Il suo nome in herdr-core ("amaltea"); senza voce, o "qui", questa macchina.
    capo: typeof c.capo === "string" && c.capo ? c.capo : "qui",
    // La chiusura automatica delle sessioni che aspettano un comando (#5366): "prova" (scrive solo cosa
    // chiuderebbe, in congedo-auto.json di cacheVolta()), "acceso" o "spento". Senza voce vale "prova".
    congedo: {
      modo: ["prova", "acceso", "spento"].includes(c.congedo) ? c.congedo : "prova",
      dopoMin: numero(c.congedo_dopo_min, 60, 5),
      ora: numero(c.congedo_ora, 3, 0),
      giorno: numero(c.congedo_giorno, 12, 0),
    },
    // La ripresa da sola delle sessioni ferme per limite o connessione (#5882): "accesa" di serie, "spenta"
    // la toglie (approvata il 17/11/2026).
    ripresa: c.ripresa === "spenta" ? "spenta" : "accesa",
    // Il modello piccolo che propone il progetto di un compito nuovo (⌘N, volta_compito.py, #6186): "acceso"
    // di serie, "spento" lascia la sola proposta dalle parole del testo.
    compito_modello: c.compito_modello === "spento" ? "spento" : "acceso",
  };
}

// La cartella dei file di Volta: elenco delle sessioni, registro dei congedi ("volta") e stato delle note
// ("volta-note"). La finestra vera, con la cartella di Herdr di serie (~/.config/herdr-app), usa ~/.cache/<nome>.
// Una finestra di prova (HERDR_APP_HOME altrove) usa <cartella di Herdr>/cache/<nome>: prima riscriveva
// l'elenco della finestra vera col suo core senza macchine, e le sessioni remote sparivano (#5449).
// La stessa regola sta in volta_sonda.py (la variabile vc), in cache() di volta_microfono.py e di volta_mod.py.
export function cacheVolta(nome = "volta") {
  const pulito = (p) => String(p).replace(/\\/g, "/").replace(/\/+$/, "").toLowerCase();
  const vera = pulito(appHome()) === pulito(`${home()}/.config/herdr-app`);
  return vera ? `${home()}/.cache/${nome}` : `${appHome()}/cache/${nome}`;
}

// Un numero intero di arturo.json, non sotto `minimo`; altrimenti quello di serie.
const numero = (v, serie, minimo) => (Number.isInteger(v) && v >= minimo ? v : serie);

const RADICE_BIN = /^(.+)[\\/]bin[\\/]arturo$/;
export function radiceDa(bin) {
  const m = RADICE_BIN.exec(String(bin ?? ""));
  return m ? m[1] : `${home()}/.claude`;
}

// Un file c'è e si legge. Un errore di lettura vale no.
async function esiste(p) {
  try { return (await readTextFile(p)) != null; } catch { return false; }
}

// La cartella dell'Arturo installato come plugin, o null: ~/.claude/arturo/radice, che il plugin riscrive a
// ogni sessione, poi installPath della sua voce in installed_plugins.json di Claude Code.
async function radicePlugin() {
  const casa = (p) => (p.startsWith("~/") ? `${home()}${p.slice(1)}` : p);
  try {
    const r = String((await readTextFile(`${home()}/.claude/arturo/radice`)) ?? "").trim();
    if (r) return casa(r);
  } catch { /* si prova la voce del plugin */ }
  try {
    const d = JSON.parse((await readTextFile(`${home()}/.claude/plugins/installed_plugins.json`)) ?? "{}");
    const p = d?.plugins?.["arturo@arturo"]?.[0]?.installPath;
    if (typeof p === "string" && p) return casa(p);
  } catch { /* nessuno la dice */ }
  return null;
}

// Le capacità dell'Arturo in `radice` (#6217): le note sulla finestra e l'unione di due progetti stanno in
// bin/, la procedura dei task è la skill tasks della persona o di Arturo. Si rileggono al più una volta al
// minuto: config() gira a ogni comando.
export const CAPACITA_MS = 60000;
let capacitaLetta = null;
async function capacitaDi(radice) {
  if (capacitaLetta && capacitaLetta.radice === radice && Date.now() - capacitaLetta.quando < CAPACITA_MS) return capacitaLetta.valore;
  const [note, unisci, sue, diArturo] = await Promise.all([
    esiste(`${radice}/bin/note_finestra.py`), esiste(`${radice}/bin/unisci.py`),
    esiste(`${home()}/.claude/skills/tasks/SKILL.md`), esiste(`${radice}/skills/tasks/SKILL.md`)]);
  const valore = { note, unisci, tasks: sue || diArturo };
  capacitaLetta = { radice, quando: Date.now(), valore };
  return valore;
}

// La guida di "Trova i miei progetti": la prima che esiste. Nell'Arturo di oggi, in uno di prima del
// 12/11/2026, e accanto al mod, dove la mette volta_mod.py per chi ha un Arturo che non la porta (#6217).
export const TROVA_PROGETTI = ["{radice}/shared/volta/trova-progetti.md", "{radice}/shared/volta-celeste/trova-progetti.md", "{app}/trova-progetti.md"];
export async function trovaProgetti(radice) {
  const candidati = TROVA_PROGETTI.map((p) => p.split("{radice}").join(radice).split("{app}").join(appHome()));
  for (const p of candidati) if (await esiste(p)) return p;
  return candidati[0];
}

// Il testo di un suggerimento con la cartella di Arturo al posto di {radice}.
export const richiesta = (prompt, radice) => (prompt ?? "").split("{radice}").join(radice);

// arturo <comando> <args>: { ok, json, errore }. Mai un'eccezione verso l'interfaccia.
// Tempo massimo esplicito (13/11/2026): su un Mac `arturo todo --json` è rimasto appeso cinque ore su
// una richiesta di permesso di macOS mai vista. exec rifiuta allo scadere ma non ferma il processo:
// la risposta dice almeno perché, invece del solo "non riesco a leggere".
export const ARTURO_MAX_MS = 45000;
export const ARTURO_APPESO = "Arturo non risponde su questa macchina: forse macOS aspetta un permesso sullo schermo.";
// Un solo comando per argomenti in volo, e niente processi nuovi dopo uno appeso (13/11/2026): la barra
// ne lanciava fino a quattro ogni 30 s e i todo uno a ogni cambio di spazio, e su un Mac se ne erano
// accumulati decine. La regola sta in voloArturo() di sessioni.js.
const voli = {};
async function arturo(comando, args, errore) {
  const chiave = JSON.stringify([comando, ...args]);
  const passo = voloArturo(voli[chiave], Date.now(), ARTURO_MAX_MS);
  if (passo.fai === "appeso") return { ok: false, errore: ARTURO_APPESO };
  if (passo.fai === "aspetta") return voli[chiave].p;
  const p = arturoUnaVolta(comando, args, errore);
  voli[chiave] = { da: Date.now(), p };
  const r = await p;
  // appeso: la voce resta, con l'ora, così per ARTURO_PAUSA_MS nessuno ne lancia un altro
  if (r.errore === ARTURO_APPESO) voli[chiave] = { da: voli[chiave].da, appeso: Date.now() };
  else delete voli[chiave];
  return r;
}
async function arturoUnaVolta(comando, args, errore) {
  const t0 = Date.now();
  try {
    const c = await config();
    const [cmd, ...pre] = c.arturo;
    const r = await exec(cmd, [...pre, comando, ...args], { cwd: c.base, timeout: ARTURO_MAX_MS });
    if (r.code !== 0 && Date.now() - t0 >= ARTURO_MAX_MS - 1000) return { ok: false, errore: ARTURO_APPESO, codice: r.code };
    if (r.code !== 0) return { ok: false, errore: prima(r.stderr) || prima(r.stdout) || `uscita ${r.code}`, codice: r.code };
    if (!args.includes("--json")) return { ok: true, testo: prima(r.stdout) };
    return { ok: true, json: JSON.parse(r.stdout) };
  } catch (e) {
    return { ok: false, errore: Date.now() - t0 >= ARTURO_MAX_MS - 1000 ? ARTURO_APPESO : errore };
  }
}

export const todo = (args) => arturo("todo", args, "Non riesco a leggere i todo di Arturo.");

// Rispondi, Risolta e Scarta del velo: arturo note <verbo> <id> --chi <chi di arturo.json>. La CLI riscrive
// nota.json rileggendolo se è cambiato, e porta il gesto sul todo: velo e Claude chiudono con lo stesso codice.
export const gestoNota = async (verbo, id, testo) => {
  const t = String(testo ?? "").trim();
  return arturo("note", [verbo, id, "--chi", (await config()).chi, "--json", ...(t ? ["--", t] : [])],
    "Non riesco a scrivere la nota con arturo note.");
};

const prima = (s) => (s ?? "").split("\n").map((x) => x.trim()).find(Boolean) ?? "";

// L'esito di uno script che risponde con una riga JSON (volta_sonda.py, teletrasporto.py): l'ultima riga
// che inizia con "{". Un'uscita vuota, una riga che non è JSON o un codice diverso da 0 senza `errore`
// sono un errore, col motivo che lo script ha scritto: prima un `{}` passava per un sì, e un gesto
// fallito non diceva niente (revisione dell'11/11/2026). Di un Python caduto conta l'ultima riga.
export function esito(r) {
  const righe = String(r?.stdout ?? "").split("\n").map((x) => x.trim()).filter((x) => x.startsWith("{"));
  let d = null;
  try { d = righe.length ? JSON.parse(righe[righe.length - 1]) : null; } catch { d = null; }
  if (d && typeof d === "object" && !Array.isArray(d) && (r?.code === 0 || d.errore)) return d;
  const caduto = String(r?.stderr ?? "").trim().split("\n").map((x) => x.trim()).filter(Boolean);
  const detto = d ? "" : prima(r?.stdout); // un JSON letto con un'uscita storta non è il motivo
  const motivo = /^Traceback/.test(caduto[0] ?? "") ? caduto[caduto.length - 1] : prima(r?.stderr) || detto;
  return { errore: (motivo || (r?.code ? `uscita ${r.code}` : "nessuna risposta")).slice(0, 200) };
}

// Lo slug come lo fa Arturo: la copia sola sta in sessioni.js (slug, progettoDi).
export { slug };

// Lo spazio che raccoglie le sessioni senza progetto (aggancia). Fino al 12/11/2026 si chiamava "Volta";
// dal 17/11/2026 "volta" è lo slug del progetto Volta (prima herdr-arturo), e uno spazio "Volta" è il suo.
export const SPAZIO_LIBERO = "Senza progetto";
export const libero = (nome) => slug(nome) === "senza-progetto";

// Uno spazio è un progetto se sta su questo computer, ha un nome scritto e non è lo spazio libero: quello
// non ha todo e non va fra i progetti della barra.
export const eProgetto = (s) => Boolean(s) && !s.machine && Boolean(s.named) && !libero(s.name);

// La chiave di un progetto: un nome alternativo ("volta-celeste") porta alla chiave della scheda ("volta"),
// così il progetto trova il suo spazio e non uno che ha per nome l'alternativo (progettoDi di sessioni.js).
export const canonico = (nome) => progettoDi(nome, shared("arturo.progetti")).chiave;

// Lo spazio di Herdr di un progetto: quello su questo computer col nome del progetto, anche se lo spazio
// porta un nome alternativo ("herdr-arturo" o "volta-celeste" per volta). Lo spazio libero non è mai di un
// progetto. La mappa dei progetti si legge una volta.
// `macchina`: lo spazio del progetto su quella macchina di Herdr (aggancia, #5802), invece che qui.
export function spazio(nome, macchina = null) {
  const m = shared("arturo.progetti");
  const k = progettoDi(nome, m).chiave;
  const dove = (s) => (macchina ? s.machine === macchina : !s.machine);
  return k ? spaces().find((s) => dove(s) && !libero(s.name) && progettoDi(s.name, m).chiave === k) : undefined;
}

export const PAROLE = {
  tu: "Tocca a te",
  decidi: "Decidi tu, poi fa Claude",
  io: "Ci pensa Claude",
  fermo: "Fermi",
};

// Il nome di un progetto per le persone: il titolo della fonte, altrimenti lo slug ripulito
// ("due-mondi" → "Due mondi", "uf" → "UF").
export function bello(p) {
  if (p?.titolo) return p.titolo;
  const s = String(p?.nome ?? p ?? "").replace(/\s*\((commessa|area):[^)]*\)\s*$/, "");
  if (/[A-Z]/.test(s)) return s;
  const parole = s.split(/[-_\s]+/).filter(Boolean).map((w) => (w.length <= 2 ? w.toUpperCase() : w));
  const t = parole.join(" ");
  return t ? t[0].toUpperCase() + t.slice(1) : "Senza nome";
}

// Il titolo di un todo come si legge: via le code tecniche (percorsi, opzioni, rimandi a piani).
export function titoloTodo(t) {
  let s = String(t ?? "");
  s = s.replace(/\s*\(([^()]*)\)/g, (m, dentro) => (/[\/~#]|--|https?:|\.(md|py|sh|js|json)\b/.test(dentro) || dentro.length > 48 ? "" : m));
  s = s.replace(/\s*(Piano|Vedi|Fonte|Rif\.?)\s+[~\/][^\s]*.*$/i, "");
  // Solo i percorsi veri (~/x, /a/b): un comando come /fine o una pagina come /en/ resta, è parte della frase.
  s = s.replace(/\s+(~\/|\/[\w.-]+\/[\w.-])[\w.\/-]*/g, "");
  s = s.replace(/\s+/g, " ").replace(/\s+([,.;:])/g, "$1").replace(/[\s,;:]+$/, "").trim();
  if (s.length > 140) s = s.slice(0, 140).replace(/\s+\S*$/, "") + "…";
  return s ? s[0].toUpperCase() + s.slice(1) : String(t ?? "");
}

// La frase di un progetto: prima la sessione viva, poi la riga scritta da Arturo, poi i conti.
export function frase(stato, p) {
  if (stato === "blocked") return { testo: "Claude ti aspetta", colore: "blocked" };
  if (stato === "working") return { testo: "Claude sta lavorando", colore: "working" };
  if (stato === "done") return { testo: "Claude ha finito", colore: "done" };
  if (p) {
    if (p.riga && !p.calcolato) return { testo: p.riga.replace(/\s+$/, ""), colore: "muted" };
    if (p.tu) return { testo: `${p.tu} ${p.tu > 1 ? "cose toccano" : "cosa tocca"} a te`, colore: "muted" };
    if (p.decidi) return { testo: `${p.decidi} ${p.decidi > 1 ? "scelte aspettano" : "scelta aspetta"} te`, colore: "muted" };
    if (p.io) return { testo: "Va avanti con Claude", colore: "muted" };
    if (p.fermo) return { testo: "Fermo", colore: "muted" };
  }
  if (stato === "idle") return { testo: "Aspetta un tuo comando", colore: "muted" };
  return { testo: "Niente da fare", colore: "dim" };
}

// La chiave di un progetto: lo slug per /inizio e per lo spazio di Herdr, altrimenti il nome.
export const chiave = (p) => slug(p.slug || p.nome);

const URGENZA = { "a rischio": 0, "chiede te": 1, "fermo": 3, "va": 2 };

// Tutti i progetti: la vista di Arturo (titolo, categoria, riga), i conti per chi agisce, la memoria
// di Arturo (extra.memoria) e gli spazi aperti. Ogni voce: { chiave, titolo, categoria, riga, tu, decidi, io, fermo, stato, aperto }.
export function progetti(vista, extra = {}) {
  const per = new Map();
  const conti = new Map();
  for (const g of vista?.gruppi ?? []) for (const t of g.todo ?? []) {
    const c = conti.get(t.progetto) ?? { tu: 0, decidi: 0, io: 0, fermo: 0 };
    c[g.tipo] = (c[g.tipo] ?? 0) + 1;
    conti.set(t.progetto, c);
  }
  // La memoria di Arturo (extra.memoria, da arturo progetti): un nome alternativo porta alla voce del suo
  // progetto, così "ariaperta" nella fonte dei task e "tuttovero" negli handoff sono una riga sola.
  const memoria = Array.isArray(extra.memoria) ? extra.memoria : null;
  const capo = new Map();
  for (const m of memoria ?? []) for (const a of m.alias ?? []) capo.set(a, m.slug);
  for (const p of vista?.progetti ?? []) {
    const k = capo.get(chiave(p)) ?? chiave(p);
    if (!k || per.has(k)) continue;
    per.set(k, { ...p, ...(conti.get(p.nome) ?? { tu: 0, decidi: 0, io: 0, fermo: 0 }), chiave: k, titolo: bello(p), categoria: p.categoria || "" });
  }
  const conCategorie = [...per.values()].some((v) => v.categoria);
  // I progetti della memoria senza todo aperti: stato e prossimo passo vengono dall'ultimo handoff. Quelli
  // con l'ultimo handoff più vecchio di un mese vanno in fondo (ferma); una cartella che Arturo non
  // conosce ancora (niente handoff, niente riga, niente titolo) resta fra le "Altre cartelle".
  const limite = giorniPrima(vista?.oggi, FERMA_GG);
  for (const m of memoria ?? []) {
    if (!m?.slug) continue;
    const v = per.get(m.slug);
    // il titolo della memoria (scheda del progetto, poi fonte) vince sul nome ricavato dallo slug
    if (v) { v.alias = m.alias ?? []; v.data = m.data || ""; v.macchine = m.macchine ?? []; if (m.titolo) v.titolo = m.titolo; continue; }
    const noto = Boolean(m.handoff || m.riga || m.titolo);
    per.set(m.slug, { chiave: m.slug, nome: m.cartella ? m.nome : m.slug, titolo: m.titolo || bello(m.nome || m.slug),
      categoria: m.categoria || (noto || !conCategorie ? "" : "Altre cartelle"), riga: m.riga ?? "", calcolato: !m.riga,
      tu: 0, decidi: 0, io: 0, fermo: 0, cartella: Boolean(m.cartella), alias: m.alias ?? [], data: m.data || "", macchine: m.macchine ?? [],
      ferma: noto && Boolean(limite) && (m.data || "") < limite });
  }
  // Con un Arturo senza il comando: le cartelle della base dei progetti senza todo, come prima.
  for (const nome of memoria ? [] : extra.cartelle ?? []) {
    const k = slug(nome);
    if (!k || per.has(k)) continue;
    const st = extra.stati?.[nome] ?? extra.stati?.[k];
    per.set(k, { chiave: k, nome, titolo: bello(nome), categoria: conCategorie ? "Altre cartelle" : "", riga: st?.riga ?? "", calcolato: !st?.riga, tu: 0, decidi: 0, io: 0, fermo: 0, cartella: true });
  }
  const noti = shared("arturo.progetti");
  for (const s of spaces()) {
    if (!eProgetto(s)) continue;
    const k = progettoDi(s.name, noti).chiave;
    if (!per.has(k)) per.set(k, { chiave: k, nome: s.name, titolo: bello(s.name), categoria: "", tu: 0, decidi: 0, io: 0, fermo: 0 });
  }
  const RANGO = { blocked: 5, done: 4, working: 3, idle: 2 };
  // Gli spazi si leggono una volta sola: spaces() attraversa il confine con Herdr, e chiamarlo due volte
  // per ognuna delle cento e più voci (cartelle della base comprese) sfora i 50 ms del render.
  const locali = new Map();
  for (const s of spaces()) if (!s.machine && !libero(s.name)) { const k = progettoDi(s.name, noti).chiave; if (!locali.has(k)) locali.set(k, s); }
  return [...per.values()]
    .map((v) => { const s = locali.get(v.chiave); return { ...v, stato: statoSpazio(s), aperto: Boolean(s) }; })
    .sort((a, b) => (RANGO[b.stato] ?? 0) - (RANGO[a.stato] ?? 0) || Number(b.aperto) - Number(a.aperto)
      || (URGENZA[a.parola] ?? 2) - (URGENZA[b.parola] ?? 2) || b.tu + b.decidi - (a.tu + a.decidi)
      || (b.data ?? "").localeCompare(a.data ?? "") || a.titolo.localeCompare(b.titolo));
}

// Dopo quanti giorni dall'ultimo handoff un progetto senza todo aperti scende fra le ferme.
const FERMA_GG = 30;
export const FERME = "Ferme da più di un mese";

// La data di N giorni prima di `oggi` (AAAA-MM-GG), o "" se oggi non si legge.
export function giorniPrima(oggi, n) {
  const d = new Date(`${String(oggi ?? "").slice(0, 10)}T12:00:00Z`);
  if (Number.isNaN(d.getTime())) return "";
  d.setUTCDate(d.getUTCDate() - n);
  return d.toISOString().slice(0, 10);
}

// I progetti in sezioni: "Adesso" (conversazioni aperte), poi le categorie della fonte.
export function sezioni(lista) {
  const adesso = lista.filter((p) => p.aperto);
  const ferme = lista.filter((p) => !p.aperto && p.ferma);
  const resto = lista.filter((p) => !p.aperto && !p.ferma);
  const per = new Map();
  for (const p of resto) {
    const c = p.categoria || "Progetti";
    if (!per.has(c)) per.set(c, []);
    per.get(c).push(p);
  }
  const out = [];
  if (adesso.length) out.push({ titolo: "Adesso", progetti: adesso });
  const cat = [...per.entries()].sort((a, b) => (a[0] === "Altre cartelle") - (b[0] === "Altre cartelle") || (a[1].length === b[1].length ? a[0].localeCompare(b[0]) : b[1].length - a[1].length));
  if (cat.length === 1 && !adesso.length) out.push({ titolo: "I tuoi progetti", progetti: cat[0][1] });
  else for (const [c, l] of cat) out.push({ titolo: c, progetti: l });
  // In fondo e chiusa: la barra la apre con un clic.
  if (ferme.length) out.push({ titolo: FERME, progetti: ferme, chiusa: true });
  return out;
}

// La scheda di uno spazio che aggancia una sessione con claude attach (qui o via ssh): Herdr non la vede
// come un agente, perché nella scheda gira ssh o attach e non claude. { terminal, tab } oppure null.
// Prima la scheda attiva: lo spazio libero ne tiene più d'una, e la testata parla di quella che vedi.
// Una scheda dove gira un'interattiva di questa macchina (occupate) è la scheda di quella sessione, non
// dell'aggancio con cui è nata: su Windows Herdr non la vede come agente, e senza questo la testata
// mostrava lo stato di un'altra scheda dello spazio (12/11/2026).
export function schedaAgganciata(s) {
  const tabs = new Set((s?.tabs ?? []).map((tb) => tb.id));
  const attiva = s?.tabs?.find((tb) => tb.active)?.id;
  const occupate = shared("arturo.volta.dove")?.occupate ?? {};
  for (const p of [...panes()].sort((a, b) => (b.tab === attiva) - (a.tab === attiva))) {
    if (!tabs.has(p.tab)) continue;
    const t = terminals().find((x) => x.address === p.terminal);
    const id = occupate[p.terminal] ?? idAggancio(t?.argv);
    if (id) return { terminal: p.terminal, tab: p.tab, id };
  }
  return null;
}

// Le schede di uno spazio dove c'è Claude, l'attiva per prima (Lavoraci, #5485): { terminale, a } per un
// agente di Herdr, { terminale, g } per una scheda che aggancia una sessione (g come schedaAgganciata).
// Un agente che panes() non mostra (un core di un'altra macchina) va in fondo, col suo indirizzo.
function schedeDiClaude(s) {
  const tabs = new Set((s?.tabs ?? []).map((tb) => tb.id));
  const attiva = s?.tabs?.find((tb) => tb.active)?.id;
  const occupate = shared("arturo.volta.dove")?.occupate ?? {};
  const qui = agents().filter((x) => x.space === s?.id);
  const terminale = (ind) => terminals().find((x) => x.address === ind) ?? { address: ind };
  const out = [];
  for (const p of [...panes()].sort((x, y) => Number(y.tab === attiva) - Number(x.tab === attiva))) {
    if (!tabs.has(p.tab)) continue;
    const t = terminale(p.terminal);
    const a = qui.find((x) => x.address === p.terminal);
    const id = a ? null : occupate[p.terminal] ?? idAggancio(t.argv);
    if (a) out.push({ terminale: t, a });
    else if (id) out.push({ terminale: t, g: { terminal: p.terminal, tab: p.tab, id } });
  }
  for (const a of qui) if (!out.some((x) => x.a === a)) out.push({ terminale: terminale(a.address), a });
  return out;
}

// Gli stati di Volta (aspetta, lavora, ferma, errore) nelle parole di Herdr, per la barra e la testata.
// Un errore non ha una parola di Herdr: resta senza stato, e Volta lo mostra nel suo elenco.
const DA_VOLTA = { aspetta: "blocked", lavora: "working", ferma: "idle" };

// Lo stato della sessione agganciata nella scheda `g` (schedaAgganciata), dall'ultima lettura di Volta
// (shared arturo.volta.stati, { <id corto>: { stato, host } }, volta.js). null se Volta non la elenca.
export function statoAgganciata(g) {
  const st = g?.id ? shared("arturo.volta.stati")?.[g.id.slice(0, 8)] : null;
  return DA_VOLTA[st?.stato] ?? null;
}

// Le sessioni di questa macchina nell'ultima lettura di Volta: { <id corto>: aspetta|lavora|ferma|errore }.
// La barra le guarda come guarda gli agenti di Herdr, che non vedono le sessioni in background.
export function statiQui() {
  const out = {};
  for (const [id, v] of Object.entries(shared("arturo.volta.stati") ?? {})) if (v?.host === "qui") out[id] = v.stato;
  return out;
}

// Lo stato della scheda aperta di uno spazio, per la testata (12/11/2026 notte): quello di Volta se la
// scheda aggancia una sessione (Herdr lì vede solo attach o ssh, e il suo stato resta vecchio), poi
// quello di Herdr per la scheda, e solo per ultimo quello dello spazio, che somma tutte le schede: uno
// spazio "ti aspetta" se una sola scheda aspetta, e la testata lo diceva sopra una sessione che lavorava.
export function statoScheda(s, tab) {
  if (!s) return null;
  const g = schedaAgganciata(s);
  const volta = g && g.tab === tab?.id ? statoAgganciata(g) : null;
  return volta ?? tab?.status ?? s.status ?? null;
}

// Lo stato di uno spazio: quello di Herdr, oppure, per una scheda che aggancia una sessione in background
// (dove Herdr non vede un agente), quello che legge Volta. Lo usano barra e todo.
export function statoSpazio(s) {
  if (!s) return null;
  return s.status ?? statoAgganciata(schedaAgganciata(s));
}

// Le sessioni di tutte le macchine come le elenca Volta (sessioni.json in cacheVolta(), scritto da
// volta_sonda.py ogni 10 s), chiuse comprese: la ricerca di ⌘K (apri.js) le legge da qui, perché la
// finestra è un'altra copia del mod e non vede l'elenco della barra. Senza file: [].
export async function sessioniVolta() {
  return (await elencoVolta()).sessioni;
}

// L'elenco intero di Volta ({ macchine, sessioni }): le macchine portano `nascita` quando non fanno
// partire sessioni (riparteAlClic di sessioni.js). Vuoto se il file non si legge.
export async function elencoVolta() {
  try {
    const d = JSON.parse((await readTextFile(`${cacheVolta()}/sessioni.json`)) ?? "{}");
    return { macchine: Array.isArray(d.macchine) ? d.macchine : [], sessioni: Array.isArray(d.sessioni) ? d.sessioni : [] };
  } catch {
    return { macchine: [], sessioni: [] };
  }
}

// La sessione agganciata nella scheda `g` come la elenca Volta (sessioni.json in cacheVolta()), o null.
// Lo stesso id su due macchine (#5634): decide la scheda (etichetta e argv), poi la copia che non è ferma.
async function sessioneDi(g) {
  try {
    const d = JSON.parse((await readTextFile(`${cacheVolta()}/sessioni.json`)) ?? "{}");
    const l = (d.sessioni ?? []).filter((x) => x?.id === g.id && Array.isArray(x.attach));
    if (l.length < 2) return l[0] ?? null;
    const t = terminals().find((x) => x.address === g.terminal);
    const sua = t ? l.find((x) => suaScheda(t, x, true)) : null;
    if (sua) return sua;
    const vive = unaPerConversazione(l);
    return vive.length === 1 ? vive[0] : null;
  } catch {
    return null;
  }
}

// Prima di scrivere a Claude in una scheda agganciata: se claude attach è uscito, nella scheda c'è la
// shell, e il testo di un todo ci finirebbe come comando. true: la scheda ha la shell, il testo non
// parte. La sessione si riapre nella sua scheda (apriSessione) e la persona riprova: il testo non si
// manda dopo il rilancio, perché nessuno dice quando Claude è pronto a riceverlo.
export async function tornataShell(g) {
  if (!(await nuda(g.terminal))) return false;
  const s = await sessioneDi(g);
  if (!s) {
    notify({ title: "La sessione di questa scheda è chiusa", body: "Chiudi la scheda e riapri la sessione dall'elenco di Volta.", level: "warning" });
    return true;
  }
  // Una sessione che si sposta o aspetta di spostarsi (shared arturo.volta.sposto di volta.js): riaprirla
  // qui riaccenderebbe la copia di partenza, viva su due macchine (#5635).
  const verso = shared("arturo.volta.sposto")?.[chiaveSessione(s)];
  if (verso) {
    notify({ title: `La sposto su ${nomeMacchina(verso)}`, body: "Riprova a spostamento finito, nella scheda d'arrivo.", level: "warning" });
    return true;
  }
  const r = await apriSessione(s, s.attach);
  if (r.errore) notify({ title: "La sessione era chiusa e non si riapre", body: r.errore, level: "error" });
  else {
    notify({ title: "Ho riaperto la sessione", body: "Riprova fra qualche secondo.", level: "warning" });
    r.veglia?.then((v) => { if (v?.errore) notify({ title: "La sessione non resta aperta", body: v.errore, level: "error" }); }).catch(() => {});
  }
  return true;
}

// Apre il progetto: lo spazio se c'è, altrimenti una sessione nuova che parte da /inizio, sulla macchina
// di "Nasce su" (il clic nella barra, Lavoraci, Fai il punto e la finestra Apri: la riga sta sotto Apri
// un progetto). `todoScelto` ({id, titolo}) porta Claude direttamente su quel todo.
export async function apri(nome, todoScelto) {
  nome = canonico(nome);
  // senza uno spazio qui, quello del progetto nel core di un'altra macchina (aggancia, #5802)
  const s = spazio(nome) ?? spaces().map((x) => x.machine).filter(Boolean).map((m) => spazio(nome, m)).find(Boolean);
  if (s) {
    run("space.select", { id: s.id });
    if (!todoScelto) return;
    const testo = testoTodo(todoScelto);
    // Il todo va solo a una scheda la cui sessione lavora su questo progetto (#5485): Claude in una
    // scheda (agente di Herdr) o la scheda che aggancia una sessione in background. Senza, nasce sotto.
    const schede = schedeDiClaude(s);
    const x = schedaDelProgetto(schede, nome, (await elencoVolta()).sessioni, shared("arturo.progetti"));
    const a = x?.a ?? null;
    // Uno spazio nato su un'altra macchina: si scrive nella scheda che la aggancia. hc send non scrive
    // se il programma aspetta una risposta, e così non risponde al posto della persona.
    const g = x?.g ?? null;
    if (g) {
      run("tab.select", { id: g.tab });
      if (statoAgganciata(g) === "blocked") return notify({ title: "Claude aspetta una tua risposta", body: "Rispondi nella sessione, poi riprova.", level: "warning" });
      if (await tornataShell(g)) return;
      const r = await hc(["send", g.terminal, testo]);
      if (r.code !== 0) notify({ title: "Non sono riuscito a scrivere a Claude", body: prima(r.stderr) || "Se Claude aspetta una tua risposta, rispondi nella sessione e riprova.", level: "warning" });
      return;
    }
    if (a) {
      if (a.status === "blocked") return notify({ title: "Claude aspetta una tua risposta", body: "Rispondi nella sessione, poi riprova.", level: "warning" });
      const r = await hc(["send", a.address, testo]);
      if (r.code !== 0) notify({ title: "Non sono riuscito a scrivere a Claude", body: prima(r.stderr), level: "error" });
      return;
    }
    // Nessuna sessione dello spazio lavora su questo progetto: il todo non va a quella di un altro, e
    // nasce una sessione nuova che parte da /inizio col todo, come per un progetto senza spazio.
    if (schede.length) notify({ title: "Apro una sessione nuova per questo todo", body: "Le sessioni di questo spazio lavorano su un altro progetto.", level: "info", timeout: 5000 });
  }
  const prompt = todoScelto ? `/inizio ${nome} -- #${todoScelto.id} ${pulito(todoScelto.titolo)}` : `/inizio ${nome}`;
  // Con "Nasce su" su questa macchina, un progetto la cui cartella sta solo altrove nasce lì (campo
  // macchina: della scheda del progetto). Una scelta esplicita in "Nasce su" vince sempre.
  const d = dove();
  const sua = d === "qui" ? macchinaDelProgetto(shared("arturo.progetti")?.[nome]?.macchine, shared("arturo.volta.macchine")) : null;
  return nasciSu(sua ?? d, prompt, nome);
}

// Una richiesta nuova, senza progetto: Claude nella cartella dei progetti, sulla macchina scelta in
// "Nasce su". `soloQui`: le richieste di "Cosa posso chiedere" restano su questa macchina, perché
// parlano dei suoi progetti, dei suoi todo e della sua configurazione (chiedi()).
export async function nuova(prompt, soloQui = false) {
  return nasciSu(soloQui ? "qui" : dove(), prompt, null);
}

// Porta Claude su un todo (Apri e A Claude dell'Orchestratore, volta.js rispondiUf): nella sessione del
// progetto se il todo ne ha uno (apri), altrimenti in una richiesta nuova senza progetto.
export async function portaSulTodo(progetto, t) {
  return progetto ? apri(progetto, t) : nuova(testoTodo(t));
}

// Una conversazione nuova in un progetto (la tessera di ⌘T, 12/11/2026): sempre una sessione nuova
// che parte da /inizio, sulla macchina di "Nasce su", in una scheda nuova dello spazio del progetto se c'è
// (aggancia), altrimenti in uno spazio nuovo. apri() invece porta allo spazio che c'è già.
export async function conversazione(nome) {
  nome = canonico(nome);
  return nasciSu(dove(), `/inizio ${nome}`, nome);
}

// La scheda nuova (Nuova richiesta, la prima tessera di ⌘T, o ⌘T in un layout senza tessere; comando
// arturo.volta-nuova): una sessione di Claude vuota, non una shell. Nasce
// in background sulla macchina di "Nasce su" e si aggancia nello spazio che la persona sta guardando,
// col suo progetto; dallo spazio libero, o senza spazio, nasce senza progetto.
export async function nuovaScheda() {
  return nasciSu(dove(), "", progettoDavanti(), "Nuova sessione");
}

// Il progetto dello spazio che la persona sta guardando, o null dallo spazio libero o senza spazio.
// Anche uno spazio di un'altra macchina dà il progetto: lì Volta apre le sessioni di quella macchina (#5802).
export function progettoDavanti() {
  const s = spaces().find((x) => x.active);
  return s?.named && !libero(s.name) ? canonico(s.name) : null;
}

// Il compito di ⌘N (#6186, leggiCompito di sessioni.js): un progetto noto parte da "/inizio <slug> -- <compito>"
// sulla macchina del progetto, come apri() con un todo; un progetto nuovo e un compito senza progetto nascono
// sulla macchina di "Nasce su". Con `apri` (⌘Invio) la scheda si apre, altrimenti la sessione lavora dietro.
//
// Più compiti di fila (#6198, 21/11/2026): le sessioni nascono una alla volta, e un compito mandato durante
// una nascita aspetta il suo turno invece di ricevere "Sta già nascendo un'altra sessione". I compiti in
// attesa stanno in `compitiInFila`, nell'ordine in cui sono arrivati, al più COMPITI_IN_FILA_MAX: il primo è
// quello che nasce. Un avviso dice che il compito aspetta; quando nasce arriva "Compito partito", come
// sempre. La fila sta nella memoria della barra: se Volta si chiude, i compiti non ancora nati si perdono.
// Il clic su una scheda nuova durante una nascita riceve ancora l'avviso: la fila vale per i compiti.
export const COMPITI_IN_FILA_MAX = 8;
const FILA_OGNI_MS = 1000;
const compitiInFila = [];
let filaGira = false;

// Gli argomenti di nasciSu per un compito. Si calcolano prima dell'attesa: fra la fine dell'attesa e
// nasciSu non c'è nessun await, così un'altra nascita non si infila in mezzo.
async function nascitaCompito(x) {
  const d = dove();
  if (x.tipo === "progetto") {
    const nome = canonico(x.slug);
    const sua = d === "qui" ? macchinaDelProgetto(shared("arturo.progetti")?.[nome]?.macchine, shared("arturo.volta.macchine")) : null;
    return [sua ?? d, promptCompito({ ...x, slug: nome }), nome, null, null, !x.apri];
  }
  // un progetto nuovo: senza la skill dei task la sessione crea la cartella e basta (#6217)
  return [d, promptCompito(x, sa((await config()).capacita, "tasks")), x.tipo === "nuovo" ? x.slug : null, null, null, !x.apri];
}

export async function compito(x) {
  if (!x?.testo) return { errore: "compito vuoto" };
  if (compitiInFila.length >= COMPITI_IN_FILA_MAX) {
    notify({ title: "Troppi compiti in attesa", body: `Ce ne sono già ${COMPITI_IN_FILA_MAX}: questo non parte. Riprova quando ne è nato uno.`, level: "warning" });
    return { errore: "troppi compiti in attesa" };
  }
  const prima = compitiInFila.length;
  compitiInFila.push(x);
  // davanti a lui: i compiti in attesa, senza quello che sta nascendo
  if (filaGira || inNascita()) notify({ title: "Compito in attesa", body: avvisoAttesa(Math.max(0, prima - 1)), level: "info" });
  // la fila la svuota chi l'ha fatta partire: gli altri lasciano il compito e tornano
  if (filaGira) return { ok: true, attesa: prima };
  filaGira = true;
  let esito = null;
  try {
    while (compitiInFila.length) {
      try {
        const args = await nascitaCompito(compitiInFila[0]);
        // un'altra nascita (un clic, un'altra finestra): inNascita la conta al più NASCITA_MAX, poi si parte
        // Una pausa che torna subito (né orologio né Python) non aspetta niente: si esce, e nasciSu dice lui
        // se la nascita di prima è ancora in corso.
        while (inNascita()) {
          const t0 = Date.now();
          await pausa(FILA_OGNI_MS);
          if (Date.now() - t0 < FILA_OGNI_MS / 2) break;
        }
        esito = await nasciSu(...args);
      } catch (e) {
        esito = { errore: String(e?.message ?? e).slice(0, 160) };
        notify({ title: "Il compito non parte", body: esito.errore, level: "error" });
      }
      compitiInFila.shift();
    }
  } finally { filaGira = false; }
  return esito;
}

// Le richieste da imparare: i pulsanti del benvenuto e della finestra "Cosa posso chiedere".
// dove: "nuova" apre sempre una conversazione nuova; "qui" scrive nella conversazione aperta,
// e senza conversazione ne apre una; "apri" apre la finestra dei progetti.
export const SUGGERIMENTI = [
  { id: "trova", titolo: "Trova i miei progetti", testo: "Claude cerca sul computer le cartelle di lavoro e te le propone come progetti.",
    prompt: "Trova i miei progetti sul computer e proponimeli. Segui {trova}: la cartella di Arturo è {radice}.", dove: "nuova" },
  { id: "guidami", titolo: "Cosa faccio adesso?", testo: "Claude guarda il lavoro recente e ti propone da dove partire.", prompt: "/guidami", dove: "qui" },
  { id: "ricorda", titolo: "Ricordami una cosa", testo: "Un todo nuovo, per te o per Claude, nel progetto giusto.",
    prompt: "Voglio aggiungere un todo. Chiedimi cosa, per quale progetto e chi lo fa.", dove: "qui" },
  { id: "riprendi", titolo: "Riprendi un progetto", testo: "Scegli fra le tue cartelle: Claude riparte da dove eri rimasto.", dove: "apri" },
  { id: "fine", titolo: "Chiudi la giornata", testo: "Claude salva il punto, aggiorna i todo e ti dice cosa resta.", prompt: "/fine", dove: "qui" },
  { id: "diagnosi", titolo: "Controlla che Arturo funzioni", testo: "Claude prova la configurazione e ti dice se c'è qualcosa da sistemare.", prompt: "/diagnosi", dove: "nuova" },
];

// Esegue un suggerimento: nella conversazione aperta se c'è e non aspetta una risposta, altrimenti in una
// nuova su questa macchina, qualunque sia "Nasce su": tutti parlano di questa macchina (nuova()).
export async function chiedi(sug) {
  const c = await config();
  // {trova}: la guida di "Trova i miei progetti" che c'è davvero su questa macchina (TROVA_PROGETTI)
  const testo = String(sug.prompt ?? "");
  const prompt = richiesta(testo.includes("{trova}") ? testo.split("{trova}").join(await trovaProgetti(c.radice)) : testo, c.radice);
  if (sug.dove === "nuova") return nuova(prompt, true);
  const s = spaces().find((x) => x.active && !x.machine);
  const a = s ? agents().find((x) => x.space === s.id && x.tab === s.tabs.find((t) => t.active)?.id) ?? agents().find((x) => x.space === s.id) : null;
  // Senza agente di Herdr: la scheda che aggancia una sessione in background, se lo spazio ne ha una.
  const g = a || !s ? null : schedaAgganciata(s);
  if (!a && !g) return nuova(prompt, true);
  if ((a ? a.status : statoAgganciata(g)) === "blocked") return notify({ title: "Claude aspetta una tua risposta", body: "Rispondi nella conversazione, poi riprova.", level: "warning" });
  if (!a && (await tornataShell(g))) return;
  const r = await hc(["send", a ? a.address : g.terminal, prompt]);
  if (r.code !== 0) notify({ title: "Non sono riuscito a scrivere a Claude", body: prima(r.stderr), level: "error" });
}

// Le altre macchine dove può nascere una sessione: quelle con Claude nell'elenco di Volta, che volta.js
// pubblica in shared arturo.volta.macchine a ogni lettura: [{ host, macchina, giu }].
export const altreMacchine = () => {
  const l = shared("arturo.volta.macchine");
  return Array.isArray(l) ? l.filter((m) => m && !m.questa && m.host) : [];
};

// Dove nasce una sessione nuova (#5172 passo 4): "qui" oppure il nome di una macchina di Herdr, scelto
// nella riga "Nasce su" (shared arturo.dove). Una macchina che Volta non elenca più torna "qui".
export const dove = () => {
  const d = shared("arturo.dove");
  return typeof d === "string" && altreMacchine().some((m) => m.host === d) ? d : "qui";
};

// Porta davanti la scheda che mostra un terminale. false se nessun pannello lo mostra: chi chiama ripiega.
export function mostra(indirizzo) {
  const p = panes().find((x) => x.terminal === indirizzo);
  if (!p) return false;
  const sp = spaces().find((x) => x.tabs.some((tb) => tb.id === p.tab));
  if (sp) { run("space.select", { id: sp.id }); run("tab.select", { id: p.tab }); }
  run("pane.focus", { terminal: indirizzo });
  return true;
}

// L'etichetta di Herdr sul terminale che aggancia una sessione (hc label): la sua chiave macchina:id
// (chiave() di sessioni.js, qui chiaveSessione, dal 14/11/2026: #5634), prima il solo id di claude attach. Con l'argv dice di chi
// è una scheda; il nome della scheda no, perché due schede possono chiamarsi uguale e una rinominata cambia
// nome (#5290).
export const ETICHETTA = "arturo.sessione";

// L'id sta su due macchine nell'ultima lettura di Volta (statiCorti, shared arturo.volta.stati): allora
// un'etichetta vecchia col solo id non dice quale copia aggancia la scheda (etichettaDice di sessioni.js).
const ambiguo = (id) => Boolean(shared("arturo.volta.stati")?.[id]?.doppio);

// Un argv come riga di comando per la shell di una scheda: fra apici ciò che non è una parola semplice.
// Su Windows la shell della scheda è PowerShell (il programma ha un percorso come C:\...): lì una riga
// che comincia con una stringa fra apici è un'espressione, e gli argomenti dopo danno ParserError
// ("Token imprevisto '-t'"). Serve l'operatore & e gli apici di PowerShell, dove ' si scrive ''.
export const comando = (argv) => {
  const a = (argv ?? []).map(String);
  if (percorsoWindows(a[0])) return "& " + a.map((x) => `'${x.replace(/'/g, "''")}'`).join(" ");
  return a.map((x) => (/^[\w@%+=:,./-]+$/.test(x) ? x : `'${x.replace(/'/g, `'\\''`)}'`)).join(" ");
};

// I terminali che agganciano la sessione e che un pannello mostra: per etichetta, poi per argv.
// Quelli di questa macchina e, dal 16/11/2026 (#5802), quelli del core della macchina della sessione
// ("amaltea/t21"), dove la scheda aggancia in locale: le schede di un'altra macchina valgono solo per le
// sessioni di quella macchina (etichettaVista, agganciataDa). Chiudere, staccare e mandare in congedo resta
// di chi l'ha aperta (mie). Un terminale che Volta ha appena chiuso (segnaTolto) non conta: Herdr lo elenca
// ancora per un attimo, e dopo Sposta la sessione arrivata ha lo stesso id della partita, quindi la
// scheda vecchia passava per la nuova e la nuova non si apriva (13/11/2026, #5537).
export function schedeDi(s) {
  if (!s?.id) return [];
  const visti = new Set(panes().map((p) => p.terminal));
  const tolti = shared("arturo.volta.tolti") ?? {};
  const casa = s.host ?? "qui";
  const l = terminals().filter((x) => visti.has(x.address) && [null, casa].includes(macchinaIndirizzo(x.address)) && !occupataDaAltra(x, s) &&
    !(tolti[x.address] && Date.now() - tolti[x.address] < TOLTI_MS));
  const dice = (x) => etichettaDice(etichettaVista(x), s, ambiguo(s.id));
  const etichetta = l.filter((x) => dice(x) === true);
  return etichetta.concat(l.filter((x) => !etichetta.includes(x) && dice(x) === null && agganciataDa(x.argv, s, x.address)));
}

// Le schede della sessione aperte da questa finestra (mia di sessioni.js): quelle che chiude, stacca e
// manda in congedo. Una scheda aperta dalla finestra di un'altra macchina la guarda quella: se la chiudesse
// questa, l'altra la vedrebbe sparire e manderebbe la sessione in congedo una seconda volta.
export function mie(s) {
  const io = ioQui();
  return schedeDi(s).filter((t) => mia(t, io));
}

// Il nome di questa macchina per il segno delle schede (SEGNO_DA di sessioni.js), dall'elenco che volta.js
// pubblica in shared arturo.volta.macchine. null prima della prima lettura: le schede restano qui, con ssh.
export function ioQui() {
  const l = shared("arturo.volta.macchine");
  const q = Array.isArray(l) ? l.find((m) => m?.questa && m.macchina) : null;
  return q ? nomeFile(q.macchina) : null;
}

// I terminali di questa macchina che agganciano la sessione fuori dalla finestra: il core li tiene e
// nessun pannello li mostra. È una finestra del Terminale aperta col lanciatore volta-claude
// (hc run sh -c "claude attach <id>"). Vuoto se la sessione ha già una scheda qui (schedeDi): il clic
// porta davanti quella, e ogni altro terminale che la aggancia è per forza fuori dai pannelli. Senza
// questo controllo il clic apre un secondo aggancio, e i due si contendono la larghezza del terminale.
// Una scheda aperta dalla finestra di un'altra macchina (non mie) non conta come scheda di qui, e i terminali
// che un pannello mostra non sono mai fuori: così il Terminale fuori si trova e si stacca anche quando
// la sessione ha la scheda di un'altra finestra in questo core (#5811, 17/11/2026).
export function altrove(s) {
  if (!s?.id || mie(s).length) return [];
  const visti = new Set(panes().map((p) => p.terminal));
  return terminals().filter((x) => !String(x.address).includes("/") && !visti.has(x.address) && (x.state ?? "live") === "live" &&
    !occupataDaAltra(x, s) && suaScheda(x, s, ambiguo(s.id)));
}

// Nel terminale gira adesso un'altra sessione interattiva (occupanti di sessioni.js, che volta.js mette
// in shared arturo.volta.dove.occupate): etichetta e argv di nascita non valgono più. Il clic non la
// porta davanti, non ci scrive l'aggancio e non la chiude come se fosse sua.
function occupataDaAltra(x, s) {
  const id = shared("arturo.volta.dove")?.occupate?.[x.address];
  return Boolean(id) && id !== s.id;
}

// Stacca quei terminali: chiude l'aggancio, la sessione continua in background. Torna quanti erano.
export function stacca(s) {
  const l = altrove(s);
  for (const t of l) { segnaTolto(t.address); run("terminal.kill", { terminal: t.address }); }
  return l.length;
}

// Gli handoff delle macchine che non rispondono (salvaHandoff di volta.js): ~/.cache/volta-handoff per la
// finestra vera, <appHome>/cache/volta-handoff per una copia di prova. Fuori da cacheVolta(): un file
// nuovo lì fa rileggere l'elenco. giu.json tiene l'ora della caduta di ogni macchina fra una ricarica
// del mod e l'altra. writeTextFile vuole la cartella: la crea il Python di arturo.json.
export const cartellaHandoff = () => cacheVolta("volta-handoff");
export const nomeFile = (x) => String(x ?? "").replace(/[^\w.-]+/g, "-").replace(/^-+|-+$/g, "") || "senza-nome";
export async function creaCartella(cartella, py) {
  try { await exec(py ?? (await config()).arturo[0], ["-c", "import os,sys; os.makedirs(sys.argv[1], exist_ok=True)", cartella], { timeout: 15000 }); }
  catch (e) { registra("cartella", { esito: "errore", errore: String(e?.message ?? e).slice(0, 120) }); }
}
export async function leggiGiu() {
  try { const d = JSON.parse((await readTextFile(`${cartellaHandoff()}/giu.json`)) ?? "{}"); return d && typeof d === "object" ? d : {}; }
  catch { return {}; }
}
export async function scriviGiu(giu, py) {
  const file = `${cartellaHandoff()}/giu.json`;
  try {
    await creaCartella(cartellaHandoff(), py);
    const prima = await readTextFile(file).catch(() => null);
    await writeTextFile(file, JSON.stringify(giu), prima ?? null);
  } catch { /* un'altra finestra l'ha scritto nel frattempo: vale il giro dopo */ }
}

// Stacca l'aggancio di una scheda ferma e lascia la scheda (F3.2 di #5587, daStaccare di sessioni.js):
// Ctrl+Z, che claude attach legge come "torna alla shell". La sessione continua, la bozza resta, e
// all'uscita claude attach spegne mouse, schermo alternativo e tastiera kitty. Un segnale invece (TERM,
// HUP, INT) lo chiude senza spegnerli, e la shell riceverebbe il mouse come testo (prova del 14/11/2026).
// Il tasto parte solo se in primo piano gira davvero l'aggancio di `s` (anche dentro ssh): mai dentro
// un altro programma, a cui Ctrl+Z sospenderebbe il lavoro. Su Windows il primo piano resta pwsh:
// lì decide lo schermo, come in nuda(). Torna { ok }, { gia } se la scheda ha già la shell, o { errore }.
const STACCO_ATTESA = 500, STACCO_MAX_MS = 8000;
export async function staccaAggancio(indirizzo, s) {
  let d;
  try {
    const r = await hc(["get", indirizzo, "--json"]);
    if (r.code !== 0) return { errore: "la scheda non risponde" };
    d = JSON.parse(r.stdout);
  } catch (e) {
    return { errore: String(e?.message ?? e).slice(0, 120) };
  }
  if (d.state !== "live") return { errore: "la scheda non è viva" };
  if (shellPowerShell(d.argv?.[0])) {
    if (await nuda(indirizzo)) return { gia: true };
    if (!agganciataDa(d.argv, s, indirizzo)) return { errore: "la scheda non è nata per agganciare questa sessione" };
  } else {
    const f = d.foreground;
    if (!f || f.pid === d.pid) return { gia: true };
    if (!agganciataDa(f.argv, s, indirizzo)) return { errore: "in primo piano non c'è l'aggancio di questa sessione" };
  }
  const k = await hc(["keys", indirizzo, "ctrl+z"]);
  if (k.code !== 0) return { errore: "il tasto non arriva alla scheda" };
  // la shell torna in circa un secondo con un aggancio fresco, ma alla prova vera del 14/11 (sessione
  // ferma da 45 minuti) non era tornata dopo 1,5 s: si guarda più volte, fino a STACCO_MAX_MS
  for (let t = 0; t < STACCO_MAX_MS; t += STACCO_ATTESA) {
    await pausa(STACCO_ATTESA);
    if (await nuda(indirizzo)) return { ok: true };
  }
  return { errore: "claude attach non si è staccato" };
}

// I terminali che chiude Volta stessa (Stacca, Sposta, Cambia progetto, Chiudi del menu): la guardia del
// congedo (volta.js, sparite() di sessioni.js) non li prende per una scheda chiusa da chi usa la finestra.
// In shared: le schede le chiude la barra, ma un comando può arrivare da un'altra copia del mod.
export function segnaTolto(indirizzo) {
  const ora = Date.now();
  const prima = shared("arturo.volta.tolti") ?? {};
  const tieni = Object.fromEntries(Object.entries(prima).filter(([, t]) => ora - t < 120000));
  setShared("arturo.volta.tolti", { ...tieni, [indirizzo]: ora });
}

// Le schede di questa macchina che agganciano una sessione in background dell'elenco, con la sessione:
// { indirizzo: { sessionId, id, host, macchina, cartella, titolo } }. Conta solo il terminale vivo che un
// pannello mostra, come schedeDi: panes() di Herdr elenca i pannelli di ogni spazio e di ogni scheda, quindi
// cambiare spazio non chiude niente. Un terminale del core senza pannello (un claude attach aperto con
// hc run, o col lanciatore volta-claude) non è una scheda: chiuderlo non manda la sessione in congedo
// (#5630). Per etichetta, poi per argv (come schedeDi), con la macchina: lo stesso id su due macchine è di
// due sessioni (#5634). Dal 16/11/2026 (#5802) solo le schede aperte da questa finestra (mia), anche nel
// core di un'altra macchina: quella che ha aperto un'altra finestra la guarda l'altra.
export function schedeAgganciate(sessioni) {
  const out = {};
  // anche le righe vecchie (macchina che non risponde): la scheda resta aperta, e senza la sua riga
  // la guardia del congedo la prenderebbe per chiusa
  const fondo = (sessioni ?? []).filter((s) => s.tipo === "background" && s.id);
  const dentro = occupanti(sessioni);
  const visti = new Set(panes().map((p) => p.terminal));
  const io = ioQui();
  for (const x of terminals()) {
    if (!visti.has(x.address) || !mia(x, io) || (x.state ?? "live") !== "live" || dentro[x.address]) continue;
    const dice = (y) => etichettaDice(etichettaVista(x), y, doppio(sessioni, y.id));
    const s = fondo.find((y) => dice(y) === true) ?? fondo.find((y) => dice(y) === null && agganciataDa(x.argv, y, x.address));
    if (s) out[x.address] = { sessionId: s.sessionId, id: s.id, host: s.host, macchina: s.macchina, questa: Boolean(s.questa), cartella: s.cartella ?? null, titolo: titolo(s) };
  }
  return out;
}

// Il primo tempo del congedo: volta_sonda.py congeda (stop, poi la ripresa con /fine) sulla macchina della
// sessione. { ok } oppure { errore }. Attese: ATTESA_AZIONE più ATTESA_SERVIZIO più ATTESA_NASCITA.
export async function congedaSessione(c) {
  const cfg = await config();
  try {
    const r = await exec(cfg.arturo[0], [cfg.volta, ...entroDi("congeda"), "congeda", c.host ?? "qui", c.id, c.sessionId, ...(c.cartella ? ["--cartella", c.cartella] : []), ...(c.auto ? ["--auto"] : [])], { timeout: tettoDi("congeda") });
    return esito(r);
  } catch (e) {
    return { errore: `${c.macchina ?? nomeMacchina(c.host ?? "qui")} non risponde (${String(e?.message ?? e).slice(0, 120)})` };
  }
}

// La scheda è rimasta con la shell nuda: claude attach è uscito (sessione fermata altrove, connessione
// caduta, servizio spento) e Herdr ha lasciato la shell che lo aveva lanciato. Si riconosce dal programma
// in primo piano: è la shell del terminale (stesso pid) e non ha più l'argv con cui è nata, cioè ha già
// passato il comando. Mentre la shell si sta ancora avviando l'argv è quello di nascita: non è nuda.
// Su Windows (scheda con PowerShell) il primo piano resta sempre pwsh, con un percorso diverso
// dall'argv di nascita: il confronto la darebbe nuda anche con claude attach acceso, e il rilancio
// scriverebbe il comando dentro Claude come un messaggio. Lì decide lo schermo: è nuda solo se l'ultima
// riga è il prompt di PowerShell (promptPowerShell di sessioni.js).
export async function nuda(indirizzo) {
  try {
    const r = await hc(["get", indirizzo, "--json"]);
    if (r.code !== 0) return false;
    const d = JSON.parse(r.stdout);
    if (shellPowerShell(d.argv?.[0])) {
      if (d.state !== "live") return false;
      const s = await hc(["read", indirizzo]);
      return s.code === 0 && promptPowerShell(s.stdout);
    }
    const f = d.foreground;
    return d.state === "live" && Boolean(f) && f.pid === d.pid && JSON.stringify(f.argv) !== JSON.stringify(d.argv);
  } catch (e) {
    registra("nuda", { esito: "eccezione", errore: String(e?.message ?? e) });
    return false;
  }
}

// Sul core di un'altra macchina l'etichetta usa la chiave di là, "qui:<id>" (etichettaVista di sessioni.js):
// così anche la finestra di quella macchina riconosce la scheda della sua sessione.
async function etichetta(t, s) {
  const v = macchinaIndirizzo(t?.address) ? `qui:${s.id}` : chiaveSessione(s);
  if (!t || t.labels?.[ETICHETTA] === v) return;
  try { await hc(["label", t.address, `${ETICHETTA}=${v}`]); } catch { /* resta l'argv */ }
}

// Il registro eventi (#5549): gli eventi della finestra si accodano qui e svuotaRegistro li scrive a lotti
// con volta_registro.py, nel registro di questa macchina accanto a quelli della sonda. Un lotto resta sotto
// REGISTRO_LOTTO caratteri: exec di Herdr non ha stdin e su Windows la riga di comando ha un tetto. La coda
// tiene al più REGISTRO_CODA eventi: se il Python non parte, i più vecchi si perdono e Volta va avanti.
const REGISTRO_LOTTO = 6000, REGISTRO_CODA = 300;
const codaRegistro = [];
let registroInCorso = false;
export function registra(evento, campi = {}) {
  codaRegistro.push({ t: Date.now(), fonte: "finestra", evento, ...campi });
  if (codaRegistro.length > REGISTRO_CODA) codaRegistro.splice(0, codaRegistro.length - REGISTRO_CODA);
}
export const codaDelRegistro = () => codaRegistro.slice();
export function lottiRegistro(coda, tetto = REGISTRO_LOTTO) {
  const lotti = [];
  let lotto = [], n = 2;
  for (const e of coda) {
    const l = JSON.stringify(e).length + 1;
    if (l + 2 > tetto) continue; // un evento troppo lungo da solo non entra mai: si scarta
    if (n + l > tetto) { lotti.push(lotto); lotto = []; n = 2; }
    lotto.push(e);
    n += l;
  }
  if (lotto.length) lotti.push(lotto);
  return lotti;
}
export async function svuotaRegistro(py) {
  // una scrittura che non torna non ferma il registro per sempre: dopo due tetti si riparte (19/11/2026)
  if (registroInCorso && Date.now() - registroInCorso < 2 * tettoDi("registro")) return;
  if (!codaRegistro.length) return;
  const mio = (registroInCorso = Date.now());
  const coda = codaRegistro.splice(0, codaRegistro.length);
  try {
    for (const lotto of lottiRegistro(coda))
      await exec(py, [`${appHome()}/mods/arturo/volta_registro.py`, ...entroDi("registro"), "scrivi", "--righe", JSON.stringify(lotto)], { timeout: tettoDi("registro") });
  } catch { /* il registro non ferma Volta */ } finally {
    if (registroInCorso === mio) registroInCorso = false;
  }
}

// L'orologio del mod: cx.sleep del contesto che main.js riceve in init e che vale anche dopo un await
// (#5579, 14/11/2026). Prima ogni attesa lanciava un processo Python, fino a dieci per apertura, e senza
// Python la ricerca della scheda finiva subito. Senza orologio, o con il contesto di una copia ricaricata
// che non vale più, resta l'attesa con Python.
/** @type {((ms: number) => Promise<void>) | null} */
let orologio = null;
/** @param {((ms: number) => Promise<void>) | null} f */
export function impostaDormi(f) { orologio = typeof f === "function" ? f : null; }

export async function pausa(ms) {
  if (orologio) {
    try { return await orologio(ms); } catch (e) { orologio = null; registra("pausa", { esito: "orologio", errore: String(e instanceof Error ? e.message : e) }); }
  }
  try {
    const c = await config();
    await exec(c.arturo[0], ["-c", "import sys,time;time.sleep(float(sys.argv[1]))", String(ms / 1000)], { timeout: ms + 10000 });
  } catch (e) { registra("pausa", { esito: "eccezione", errore: String(e?.message ?? e) }); /* senza Python si va avanti senza attesa */ }
}

// volta_sonda.py apri: il servizio di Claude acceso sulla macchina della sessione, e con `riavvia` la
// sessione fatta ripartire (claude respawn). { ok, riavviata } oppure { errore }.
// Attese: ATTESA_SERVIZIO di volta_sonda.py più 30 s; con riavvia anche ATTESA_AZIONE (come Riavvia).
export async function prepara(s, riavvia = false) {
  const c = await config();
  try {
    const r = await exec(c.arturo[0], [c.volta, ...entroDi(riavvia ? "apri_riavvia" : "apri"), "apri", s.host ?? "qui", s.id, ...(riavvia ? ["--riavvia"] : [])], { timeout: tettoDi(riavvia ? "apri_riavvia" : "apri") });
    const e = esito(r);
    if (!e.errore) servizioVisto(s.host);
    return e;
  } catch (e) {
    return { errore: `${s.macchina ?? nomeMacchina(s.host ?? "qui")} non risponde (${String(e?.message ?? e).slice(0, 120)})` };
  }
}

// Il servizio di Claude trovato acceso su `host` adesso (prepara, una nascita): per SERVIZIO_VISTO_MS il clic
// su una sessione di quella macchina salta prepara (servizioAcceso di sessioni.js). In shared, così vale per
// tutte le copie del mod della finestra e resta dopo una ricarica.
export function servizioVisto(host, ora = Date.now()) {
  const v = shared("arturo.volta.servizio") ?? {};
  setShared("arturo.volta.servizio", { ...v, [host ?? "qui"]: ora });
}

// La scheda nuova che aggancia una sessione: nello spazio del progetto (lo stesso della barra) o nello
// spazio libero ("Senza progetto") per le sessioni senza progetto. Mai una scheda ritrovata per nome: quella la cerca
// apriSessione, per etichetta e per argv.
// Una sessione di un'altra macchina (#5802, 16/11/2026) apre la scheda in uno spazio di quella macchina, con
// claude attach in locale (argvRemoto): resta aperta anche a questa macchina spenta, e il telefono la vede.
// Resta qui con ssh se quella macchina non è fra le macchine di Volta o non risponde, se è Windows, o se
// non si sa ancora il nome di questa. Torna l'argv che la scheda lancia: lo rilanciano apriSessione e veglia.
export function aggancia(s, argv) {
  const nome = titolo(s).slice(0, 40);
  // lo spazio prende la chiave del progetto, mai il nome alternativo: uno spazio "volta" sarebbe preso per
  // quello libero e rinominato "Senza progetto" (#5487)
  const nomeSpazio = s.progetto ? canonico(s.progetto) : SPAZIO_LIBERO;
  const remoto = !s.questa && altreMacchine().some((m) => m.host === s.host && !m.giu) ? argvRemoto(argv, ioQui()) : null;
  if (remoto) {
    const sp = s.progetto ? spazio(nomeSpazio, s.host) : spaces().find((x) => x.machine === s.host && libero(x.name));
    // la cartella di un'altra macchina non si guarda da qui: la scheda parte dalla casa di là
    if (sp) {
      run("space.select", { id: sp.id });
      run("tab.new", { name: nome, space: sp.id, argv: remoto });
    } else run("space.new", { name: nomeSpazio, machine: s.host, tab: nome, argv: remoto });
    return remoto;
  }
  const sp = s.progetto ? spazio(nomeSpazio) : spaces().find((x) => !x.machine && libero(x.name));
  // una cartella che non c'è più (un worktree tolto) non apre la scheda: la sonda dà la più vicina che c'è (#5669)
  const cartella = s.questa && s.cartella ? (s.cartellaViva || s.cartella) : home();
  if (sp) {
    run("space.select", { id: sp.id });
    run("tab.new", { name: nome, space: sp.id, folder: cartella, argv: argvScheda(argv) });
  } else run("space.new", { name: nomeSpazio, folder: cartella, machine: "", tab: nome, argv: argvScheda(argv) });
  return argv;
}

// L'aggancio da rilanciare nella scheda `indirizzo`: una scheda nel core della macchina della sessione
// aggancia in locale (attachLocale), una di qui con l'argv della sonda.
const argvPer = (indirizzo, argv) => (macchinaIndirizzo(indirizzo) ? attachLocale(argv) ?? argv : argv);

// Quanto si aspetta prima di guardare se claude attach è rimasto in piedi nella scheda (veglia).
const VEGLIA = 6000;
// La ricerca della scheda appena chiesta a Herdr (step 5, 17/11/2026): ogni CERCA_OGNI ms, fino a CERCA_ENTRO.
// Con 400 ms il clic aspettava in media 200 ms di troppo; il tetto resta quello di prima (20 giri da 400).
const CERCA_OGNI = 120, CERCA_ENTRO = 8000;
// Quanto la veglia guarda la scheda per dire quando Claude è davanti (l'evento apri): ogni VISIBILE_OGNI ms.
const VISIBILE_OGNI = 250;

// Apre una sessione in una scheda con Claude dentro (#5290). La usano il clic di Volta, la sessione
// spostata da un Terminale e quella appena nata (`pronta`: il servizio è già acceso, niente prepara).
// - La scheda c'è e Claude gira: la porta davanti e basta.
// - La scheda c'è ma è rimasta la shell nuda: accende il servizio e rilancia claude attach lì dentro.
// - La scheda non c'è: accende il servizio e la crea.
// Una sessione in errore riparte prima con claude respawn. Torna { errore } se non si può aprire,
// altrimenti { come: "davanti" | "rilanciata" | "nuova", veglia }: `veglia` è la promessa che guarda,
// dopo qualche secondo, se Claude è rimasto nella scheda. Se è uscito subito riavvia la sessione, una
// volta sola, e rilancia l'aggancio; se esce ancora torna { errore }.
export async function apriSessione(s, argv, pronta = false) {
  const schede = schedeDi(s);
  let scheda = null, rilancia = false;
  for (const x of schede) if (!(await nuda(x.address))) { scheda = x; break; }
  if (scheda) {
    await etichetta(scheda, s);
    mostra(scheda.address);
    return { come: "davanti", indirizzo: scheda.address };
  }
  if (schede.length) { scheda = schede[0]; rilancia = true; }
  let riavviata = false;
  const elenco = await elencoVolta();
  // in errore su una macchina che non fa partire sessioni: niente respawn, cadrebbe ancora (13/11/2026)
  const rc = s.stato === "errore" ? riparteAlClic(s, elenco) : { riparte: false };
  if (rc.errore) return { errore: rc.errore };
  // il servizio già acceso su quella macchina (servizioAcceso di sessioni.js): niente prepara, che su un'altra
  // macchina costava un giro di hc exec prima della scheda (step 5). Una sessione in errore riparte sempre da lì.
  const servizio = pronta ? "pronta" : s.stato !== "errore" && servizioAcceso(elenco, s.host, shared("arturo.volta.servizio") ?? {}) ? "acceso" : "chiesto";
  if (servizio === "chiesto") {
    const a = await prepara(s, s.stato === "errore");
    if (a.errore) return { errore: `Non la apro: ${a.errore}.` };
    // conta il riavvio chiesto, non la risposta: la veglia non deve mai riavviare due volte
    riavviata = s.stato === "errore";
  }
  if (rilancia) {
    mostra(scheda.address);
    const r = await rilanciaAggancio(scheda.address, argvPer(scheda.address, argv));
    if (r.code !== 0) return { errore: "Non riesco a rilanciare Claude nella sua scheda: chiudi la scheda e riprova." };
    await etichetta(scheda, s);
  } else {
    aggancia(s, argv);
    // run() non dice quale terminale ha creato: lo si cerca per argv appena Herdr lo elenca. Una scheda
    // nel core di un'altra macchina compare quando quella macchina risponde: l'attesa è più lunga.
    // a giri contati, non a orologio: una pausa che torna subito (l'orologio caduto, il banco) non gira a vuoto
    for (let i = 0; i <= CERCA_ENTRO / CERCA_OGNI && !scheda; i++) {
      scheda = schedeDi(s)[0] ?? null;
      if (!scheda) await pausa(CERCA_OGNI);
    }
    // run() non dice gli errori di Herdr: senza scheda dopo l'attesa il clic lo dice, non finisce in silenzio (#5669)
    if (!scheda) return { errore: "Herdr non ha aperto la scheda: riprova fra poco." };
    await etichetta(scheda, s);
  }
  const a = argvPer(scheda.address, argv);
  return { come: rilancia ? "rilanciata" : "nuova", servizio, riavviata, indirizzo: scheda.address, veglia: veglia(s, a, scheda.address, riavviata) };
}

// Aspetta `ms` guardando la scheda ogni VISIBILE_OGNI ms finché Claude non compare davanti (claudeDavanti di
// sessioni.js): torna l'istante in cui l'ha visto, o null. Legge terminals() di Herdr, in memoria: niente
// processi. Il giudizio su una scheda nuda resta a veglia, dopo tutta l'attesa: all'avvio la shell cambia
// argv (sh -c, poi zsh -lic) e una lettura presto la darebbe nuda con claude attach in arrivo.
async function aspettaClaude(indirizzo, ms) {
  // a giri contati, come la ricerca della scheda: con una pausa che torna subito il ciclo finisce lo stesso
  const giri = Math.ceil(ms / VISIBILE_OGNI);
  for (let i = 0; i < giri; i++) {
    let t = null;
    try { t = terminals().find((x) => x.address === indirizzo) ?? null; } catch { t = null; }
    if (claudeDavanti(t)) {
      const visto = Date.now();
      // il resto dell'attesa in una pausa sola: la veglia guarda dopo `ms`, come prima
      if (giri - i > 0) await pausa((giri - i) * VISIBILE_OGNI);
      return visto;
    }
    await pausa(VISIBILE_OGNI);
  }
  return null;
}

// Il rilancio dell'aggancio nella shell rimasta in una scheda (#5637): prima pulisce la riga (un mouse
// rimasto acceso ci scrive "35;16;1M"), poi scrive l'aggancio col segno e il reset dei modi
// (rigaRilancio di sessioni.js). Il codice d'uscita è quello di hc send.
async function rilanciaAggancio(indirizzo, argv) {
  const a = argvScheda(argv);
  const powershell = percorsoWindows(a[0]);
  await hc(["keys", indirizzo, ...tastiPulizia(powershell)]);
  return hc(["send", indirizzo, rigaRilancio(comando(a), powershell)]);
}

// Perché Claude è uscito dalla scheda: lo dice lo schermo della scheda (motivoUscita di sessioni.js),
// letto con l'argv dell'aggancio che la scheda ha lanciato.
async function perche(s, indirizzo, argv) {
  try {
    const r = await hc(["read", indirizzo]);
    return r.code === 0 ? motivoUscita(r.stdout, s, argv) : null;
  } catch {
    return null;
  }
}

// Se Claude è uscito, la riga dice il motivo letto nella scheda. Una causa che sta nella macchina o
// nella connessione (`fermo`) non si riprova: il riavvio non la toglie, e terrebbe la riga occupata.
// La veglia non riavvia la sessione (#5636): da un elenco vecchio riavviava anche una sessione che
// lavorava. Rilancia solo l'aggancio, una volta, col servizio acceso; Riavvia resta un gesto del menu.
async function veglia(s, argv, indirizzo, riavviata) {
  // `visto`: quando Claude è comparso nella scheda, per l'evento apri (step 5)
  const visto = await aspettaClaude(indirizzo, VEGLIA);
  if (!(await nuda(indirizzo))) return visto ? { visto } : {};
  const fallita = (m) => ({ errore: m?.testo ?? "Claude non resta aperto in questa sessione: riprova, oppure eliminala da Altro." });
  const m = await perche(s, indirizzo, argv);
  if (riavviata || m?.fermo) return fallita(m);
  const a = await prepara(s);
  if (a.errore) return { errore: `Claude non si riapre: ${a.errore}.` };
  const r = await rilanciaAggancio(indirizzo, argv);
  if (r.code !== 0) return fallita(m);
  await pausa(VEGLIA);
  return (await nuda(indirizzo)) ? fallita((await perche(s, indirizzo, argv)) ?? m) : { rilanciata: true };
}

// Il nome di una macchina di "Nasce su" per le persone: "qui" è il nome vero di questa macchina, letto
// dall'elenco che volta.js pubblica (nomeMacchina di sessioni.js).
export const nomeMacchina = (m) => nomeMacchinaDi(m, shared("arturo.volta.macchine"));

// Una sessione nuova in background (volta_sonda.py nasci), su questa macchina o su un'altra, agganciata
// qui in una scheda: continua a girare anche chiusa la scheda, e Volta la apre da ogni macchina. Anche
// qui nasce in background (#5072): lo stato in barra lo dà Volta (statoSpazio).
// Durante la nascita shared arturo.nascita dice dove e da quando, per la riga "Nasce su" (inNascita).
// `copia` ({ verbo: "duplica" | "fork", sessionId, cartella, titolo }) è il Duplica o il Fork di una
// sessione (#5291): stessa strada e stesse attese, coi verbi duplica e fork della sonda. Torna { ok } o
// { errore }; l'errore di una copia lo mostra la riga di Volta, ogni errore di una nascita un avviso
// (chi chiama non guarda l'esito: il clic nella barra, Lavoraci, i comandi).
// Riprendi su… (14/11/2026): una sessione nuova su `macchina` col prompt dell'handoff (promptRipresa di
// sessioni.js), nella cartella del progetto se c'è. Torna { ok, id } o { errore }, come nasciSu.
export const riprendiSu = (macchina, prompt, progetto, nome) => nasciSu(macchina, prompt, progetto, nome);
// Arturo c'è se arturo.json nomina la sua CLI: allora la ripresa parte da /inizio del progetto (F5: senza
// Arturo Volta funziona, e il prompt è il solo testo).
export const conArturo = (c) => (c?.arturo ?? []).some((a) => /(^|[\\/])arturo(\.cmd|\.exe)?$/.test(String(a)));

// `dietro` (⌘N con Invio, #6186): la sessione nasce e lavora in background senza una scheda, e la finestra
// resta dov'è; un avviso dice dove è nata, e la riga compare nell'elenco e nell'Orchestratore.
async function nasciSu(macchina, prompt, progetto, nomeScheda = null, copia = null, dietro = false) {
  const dico = (titolo, errore, level = "error") => {
    if (!copia) notify({ title: titolo, body: errore, level });
    return { errore };
  };
  if (inNascita()) return dico("Sta già nascendo un'altra sessione", "sta già nascendo un'altra sessione: riprova fra poco", "warning");
  // Una sessione che nasce vuota in un progetto (la scheda nuova, Duplica) parte da /inizio di quel
  // progetto, come Apri un progetto (#5465). La Fork no: porta già la sua conversazione.
  if (progetto && !prompt && copia?.verbo !== "fork") prompt = `/inizio ${progetto}`;
  const da = Date.now();
  setShared("arturo.nascita", { macchina, da });
  try {
    const c = await config();
    const args = [c.volta, ...entroDi("nasci"), copia ? copia.verbo : "nasci", macchina, ...(copia?.verbo === "fork" ? [copia.sessionId] : []),
      ...(progetto ? ["--progetto", progetto] : []), ...(copia?.cartella ? ["--cartella", copia.cartella] : []),
      ...(copia?.titolo ? ["--titolo", copia.titolo] : []), ...(prompt ? ["--", prompt] : [])];
    let nata = {};
    const t0 = Date.now();
    try {
      // TETTI.comandi.nasci (sessioni.js): le attese di volta_sonda.py (macchine, servizio, nascita) più un
      // margine, così Volta non dice "non risponde" mentre la sessione sta ancora nascendo (#5214)
      nata = esito(await exec(c.arturo[0], args, { timeout: tettoDi("nasci") }));
    } catch (e) {
      registra("nascita", { macchina, ms: Date.now() - t0, esito: "eccezione", errore: String(e?.message ?? e) });
      nata = { errore: `${nomeMacchina(macchina)} non ha risposto in ${Math.round(tettoDi("nasci") / 60000)} minuti: se la sessione è nata, la trovi fra le sessioni` };
    }
    registra("nascita", { macchina, sid: nata.id, ms: Date.now() - t0, esito: nata.errore ? "errore" : "ok", errore: nata.errore });
    if (nata.attach?.length) {
      // la nascita accende il servizio di Claude su quella macchina: il clic dopo salta prepara (step 5)
      servizioVisto(macchina);
      if (dietro) {
        notify({ title: "Compito partito", body: avvisoCompito(progetto ? nomeProgettoDi(progetto) : null, nomeMacchina(macchina)), level: "info" });
        return { ok: true, id: nata.id };
      }
      const nome = nomeScheda ?? progetto ?? (prompt ? pulito(prompt) : `Richiesta su ${nomeMacchina(macchina)}`);
      // La scheda parte dalla home anche qui: claude attach non ha bisogno della cartella della sessione.
      const v = await apriSessione({ id: nata.id, sessionId: nata.sessionId, nome, progetto, questa: macchina === "qui", host: macchina }, nata.attach, true);
      // la veglia non tiene occupata la nascita: se Claude non resta nella scheda arriva un avviso
      v.veglia?.then((x) => { if (x?.errore) notify({ title: "La sessione nuova non resta aperta", body: x.errore, level: "warning" }); });
      return v.errore ? dico("La sessione è nata, ma non si apre", v.errore) : { ok: true, id: nata.id };
    }
    return dico(`La sessione non nasce su ${nomeMacchina(macchina)}`, nata.errore ?? "nessuna risposta");
  } catch (e) {
    return dico(`La sessione non nasce su ${nomeMacchina(macchina)}`, String(e?.message ?? e).slice(0, 160));
  } finally {
    // solo la propria: se questa è scaduta e ne è partita un'altra, quella resta segnata
    if (shared("arturo.nascita")?.da === da) setShared("arturo.nascita", null);
  }
}

// Quanto dura al massimo una nascita: l'attesa della sonda (TETTI.comandi.nasci) più un minuto per
// l'aggancio della scheda.
const NASCITA_MAX = tettoDi("nasci") + 60000;

// La macchina dove sta nascendo una sessione, o null. shared arturo.nascita è { macchina, da }: oltre
// NASCITA_MAX non vale più, perché chi l'ha scritto può essere morto prima di toglierlo (una finestra
// chiusa a metà, Volta chiusa durante la nascita) e nessuna sessione nascerebbe più. La stringa che
// scriveva la versione di prima non ha un'ora: è scaduta.
export function inNascita(ora = Date.now()) {
  const n = shared("arturo.nascita");
  if (!n || typeof n !== "object" || typeof n.macchina !== "string" || !Number.isFinite(n.da)) return null;
  return ora - n.da < NASCITA_MAX ? n.macchina : null;
}

// Duplica e Fork del menu di una sessione (#5291), sulla macchina della sessione e non su "Nasce su":
// la copia sta accanto all'originale, nella sua cartella e nel suo progetto. Duplica nasce vuota; Fork
// porta la conversazione (serve il sessionId di adesso, non l'id del lavoro) e si chiama "<titolo> (fork)".
export function copiaSessione(s, verbo) {
  const fork = verbo === "fork";
  return nasciSu(s.host ?? "qui", "", s.progetto ? String(s.progetto) : null, fork ? titoloFork(s).slice(0, 40) : "Nuova sessione",
    { verbo: fork ? "fork" : "duplica", sessionId: s.sessionId, cartella: s.cartella || null, titolo: fork ? titoloFork(s) : null });
}

// Sposta una sessione in background su un'altra macchina (volta_sonda.py sposta, 12/11/2026): la stessa
// conversazione riparte là, la scheda che la agganciava qui si chiude e una scheda nuova aggancia quella
// di là. 20 minuti: una trascrizione grande e un git clone ci mettono. { ok } oppure { errore }.
// Lo spostamento parte staccato e scrive l'esito in cacheVolta()/sposta/<sessionId>.json (13/11/2026): exec
// di Herdr si ferma a 10 minuti, uno spostamento ne può chiedere di più, e lo script restava a girare da
// solo. `dormi(ms)`: l'attesa fra due letture (cx.sleep di chi chiama); senza, pausa().
export async function spostaSessione(s, macchina, dormi = null) {
  const c = await config();
  const file = `${cacheVolta()}/sposta/${nomeSposta(s)}.json`;
  const traccia = (passo, dati) => tracciaSposta(s, passo, dati);
  const argv = [c.volta, ...entroDi("sposta"), "sposta", s.host ?? "qui", macchina, s.id, s.sessionId, "--cartella", s.cartella || ""];
  // Prima di chiudere le schede, la macchina della sessione dice se ha appena cominciato un turno (#5635):
  // lo spostamento aspetta il turno finito, e la scheda resta aperta. Un controllo che non torna (exec
  // caduto, uscita storta, macchina che non risponde) vale come un turno in corso, `nonLetto` (#6110): prima
  // valeva come via libera, e le schede si chiudevano su una sessione forse a metà turno.
  // Un errore certo (`certo`: l'id non valido, #6126) non si riprova: ogni tentativo darebbe lo stesso.
  let prima;
  try { prima = esito(await exec(c.arturo[0], [...argv, "--controlla"], { timeout: tettoDi("sposta") })); } catch (e) {
    prima = { errore: String(e?.message ?? e).slice(0, 120) };
  }
  if (prima?.certo === true && prima.errore && !prima.lavora) {
    await traccia("rifiuto", { da: s.host ?? "qui", a: macchina, id: s.id, errore: prima.errore });
    return { errore: String(prima.errore) };
  }
  if (prima?.lavora || prima?.errore) {
    const nonLetto = !prima.lavora || prima.nonLetto === true;
    await traccia("lavora", { da: s.host ?? "qui", a: macchina, id: s.id, ...(nonLetto ? { nonLetto: true } : {}) });
    return { errore: prima.lavora ? prima.errore || "sta lavorando: la sposto a turno finito" : `non so se lavora (${prima.errore}): riprovo`,
      lavora: true, ...(nonLetto ? { nonLetto: true } : {}) };
  }
  // Le schede che la agganciano si chiudono prima: un claude attach rimasto aperto riaccende la sessione
  // dopo claude stop, e la conversazione resta viva su tutte e due le macchine (#5537, 13/11/2026). Se lo
  // spostamento non va, la scheda si riapre sulla sessione rimasta qui. Si staccano anche gli agganci di
  // questa macchina fuori dalle schede (hc run, una finestra del Terminale): stacca() dopo chiudiSchede,
  // perché altrove() vede quei terminali solo quando la sessione non ha più schede.
  const schede = schedeDi(s).map((t) => t.address);
  const chiuse = chiudiSchede(s);
  const staccati = stacca(s);
  await traccia("inizio", { da: s.host ?? "qui", a: macchina, id: s.id, attach: s.attach ?? null, schede, chiuse, staccati });
  let r;
  try {
    r = esito(await exec(c.arturo[0], [...argv, ...(s.progetto ? ["--progetto", String(s.progetto)] : []),
      "--titolo", titolo(s).slice(0, 60), "--esito", file], { timeout: tettoDi("sposta") }));
  } catch (e) {
    // exec è caduto dopo aver forse lanciato lo spostamento: non si sa dove sia la sessione (nonSiSa)
    return fineSposta(s, macchina, { errore: `non riesco a far partire lo spostamento su ${nomeMacchina(macchina)} (${String(e?.message ?? e).slice(0, 80)})`, nonSiSa: true }, chiuse);
  }
  await traccia("avvio", { risposta: r });
  if (!r.avviato) return fineSposta(s, macchina, r, chiuse);
  const v = { s, macchina, file, dal: Date.now(), chiuse };
  await cambiaVolo((d) => { d[nomeSposta(s)] = { ...v, preso: Date.now() }; });
  return attendiSposta(v, dormi);
}

// Uno spostamento rimasto in volo da una ricarica del mod (#5559, voloSposta di sessioni.js): riprende
// l'attesa dell'esito dove l'aveva lasciata la copia di prima, poi apre la scheda d'arrivo o riapre quella
// chiusa. `v`: la voce di volo.json. Torna come spostaSessione.
export async function riprendiSposta(v, dormi = null) {
  await tracciaSposta(v.s, "ripresa", { a: v.macchina, dal: v.dal, chiuse: v.chiuse ?? 0 });
  return attendiSposta(v, dormi);
}

// Gli spostamenti in volo di questa macchina: le voci di volo.json, rotte comprese (le scarta chi chiama).
export async function spostamentiInVolo() {
  try {
    const d = JSON.parse((await readTextFile(fileVolo())) ?? "{}");
    return d && typeof d === "object" && !Array.isArray(d) ? Object.entries(d).map(([k, v]) => ({ k, v })) : [];
  } catch { return []; }
}

// Toglie da volo.json la voce `k`: uno spostamento finito, o rotto.
export const togliVolo = (k) => cambiaVolo((d) => { delete d[k]; });

const fileVolo = () => `${cacheVolta()}/sposta/volo.json`;

// Cambia volo.json con `f(d)`, solo se il file è ancora quello letto: un'altra copia del mod può scrivere
// in mezzo. Tre tentativi; false se non ci è riuscita (lo spostamento va avanti lo stesso).
async function cambiaVolo(f) {
  for (let i = 0; i < 3; i++) {
    try {
      const prima = await readTextFile(fileVolo()).catch(() => null);
      let d = {};
      try { d = JSON.parse(prima ?? "{}"); } catch { d = {}; }
      if (!d || typeof d !== "object" || Array.isArray(d)) d = {};
      f(d);
      await writeTextFile(fileVolo(), JSON.stringify(d, null, 1), prima);
      return true;
    } catch { /* scritto in mezzo, o la cartella manca: si riprova */ }
  }
  return false;
}

// L'attesa dell'esito di uno spostamento staccato e la sua fine, per spostaSessione e per riprendiSposta.
// A ogni giro segna `preso` in volo.json (questa copia del mod è viva); la voce si toglie dopo la fine, così
// una ricarica durante l'apertura della scheda la rifà: apriSessione porta davanti una scheda già aperta.
async function attendiSposta(v, dormi) {
  const { s, macchina, file, dal } = v;
  const k = nomeSposta(s);
  for (let giri = 1; ; giri++) {
    await (dormi ? dormi(SPOSTA_OGNI_MS) : pausa(SPOSTA_OGNI_MS));
    const p = esitoSposta(await readTextFile(file).catch(() => null), dal, Date.now(), nomeMacchina(macchina));
    await cambiaVolo((d) => { if (d[k]) d[k].preso = Date.now(); });
    // l'attesa una volta al minuto: 25 minuti di giri ogni 5 secondi riempirebbero la traccia
    if (p.attendi) { if (giri === 1 || giri % 12 === 0) await tracciaSposta(s, "attesa", { giri }); continue; }
    await tracciaSposta(s, "esito", { giri, esito: p.fatto ?? p });
    const x = await fineSposta(s, macchina, p.errore ? { errore: p.errore, nonSiSa: p.nonSiSa === true } : p.fatto, v.chiuse);
    await togliVolo(k);
    return x;
  }
}

// La fine di uno spostamento con la risposta `r` di volta_sposta.py: con l'aggancio apre la scheda
// d'arrivo; senza, riapre la scheda chiusa all'inizio (`chiuse`) sulla sessione rimasta qui. Con `nonSiSa`
// (exec caduto, nessun esito in 25 minuti) la sessione può già vivere di là: riaprire la scheda di partenza
// la riaccenderebbe anche qui (#5635), e la scheda resta chiusa. `avviso`: spostata, con un segno non scritto.
async function fineSposta(s, macchina, r, chiuse) {
  // `lavora`: la sessione ha cominciato un turno, e volta_sposta.py non l'ha toccata (si riprova dopo).
  // `nonLetto`: il secondo controllo, dopo la preparazione della cartella, non ha letto il turno (#6110):
  // passa alla coda, che lo riprova al più SPOSTA_NON_LETTO_MAX volte (#6126). Senza, la coda riprovava
  // senza limite e riapriva ogni volta la scheda.
  if (!r?.attach?.length) {
    const nonSiSa = r?.nonSiSa === true;
    const lavora = r?.lavora === true;
    const x = { errore: (r?.errore ?? "nessuna risposta") + (nonSiSa && chiuse ? "; non riapro la scheda di partenza" : ""), lavora,
      ...(lavora && r?.nonLetto === true ? { nonLetto: true } : {}) };
    let riaperta = null;
    if (chiuse && !nonSiSa && Array.isArray(s.attach) && s.attach.length) riaperta = await apriSessione(s, s.attach).catch((e) => ({ errore: String(e?.message ?? e) }));
    await tracciaSposta(s, "male", { esito: x, riaperta: riaperta && { come: riaperta.come, errore: riaperta.errore } });
    return x;
  }
  const traccia = (passo, dati) => tracciaSposta(s, passo, dati);
  const dopo = chiudiSchede(s);
  const nuova = { id: r.id, sessionId: r.sessionId, nome: titolo(s), progetto: s.progetto ?? null, questa: macchina === "qui", host: macchina };
  await traccia("apro", { nuova, attach: r.attach, chiuseDopo: dopo, schedeNuova: schedeDi(nuova).map((t) => t.address) });
  const v = await apriSessione(nuova, r.attach, true);
  await traccia("aperta", { come: v.come ?? null, errore: v.errore ?? null, schedeNuova: schedeDi(nuova).map((t) => t.address) });
  if (v.errore) return { errore: `è su ${nomeMacchina(macchina)}, ma non si apre: ${v.errore}` };
  return r.avviso ? { ok: true, avviso: String(r.avviso) } : { ok: true };
}

// Il nome dei file di uno spostamento in cacheVolta()/sposta: il sessionId senza caratteri strani.
const nomeSposta = (s) => String(s?.sessionId ?? s?.id ?? "").replace(/[^0-9A-Za-z-]/g, "");

// La traccia di Sposta (#5556): i passi di uno spostamento, in cacheVolta()/sposta/<sessionId>.traccia.json,
// perché le notifiche di Volta non si leggono da fuori. `nuova`: il primo passo (il comando), che toglie la
// traccia di prima. Ogni passo rilegge il file prima di scriverlo: la barra che sposta e chi la chiama
// possono essere copie diverse del mod. Una traccia che non si scrive non ferma lo spostamento: torna false.
export async function tracciaSposta(s, passo, dati = {}, nuova = false) {
  const file = `${cacheVolta()}/sposta/${nomeSposta(s)}.traccia.json`;
  for (let i = 0; i < 3; i++) {
    try {
      const prima = await readTextFile(file).catch(() => null);
      let l = [];
      if (!nuova) { try { l = JSON.parse(prima ?? "[]"); } catch { l = []; } }
      if (!Array.isArray(l)) l = [];
      l.push({ ora: new Date().toISOString(), passo, ...dati });
      await writeTextFile(file, JSON.stringify(l.slice(-100), null, 1), prima);
      return true;
    } catch { /* un'altra copia ha scritto in mezzo, o la cartella manca: si riprova */ }
  }
  return false;
}

// Chiude le schede che agganciano la sessione: la prima metà di "Chiudi", prima di claude stop. La
// scheda intera se dentro c'è solo quel terminale, altrimenti il solo terminale: i pannelli accanto
// restano. Solo quelle aperte da questa finestra (mie), anche nel core di un'altra macchina. Torna quante ne ha chiuse.
export function chiudiSchede(s) {
  let n = 0;
  for (const t of mie(s)) {
    if (!panes().some((x) => x.terminal === t.address)) continue;
    segnaTolto(t.address);
    chiudiTerminale(t.address);
    n++;
  }
  return n;
}

// confirmed: sull'ultima scheda di uno spazio Herdr chiederebbe "Close space?", e annullare lasciava
// la scheda aperta col congedo già partito (12/11/2026)
function chiudiTerminale(indirizzo) {
  const p = panes().find((x) => x.terminal === indirizzo);
  if (!p) return;
  if (panes().filter((x) => x.tab === p.tab).length === 1) run("tab.close", { id: p.tab, confirmed: true });
  else run("terminal.kill", { terminal: indirizzo });
}

// Chiudi del menu su una sessione con la scheda aperta dalla finestra di un'altra macchina (#5811, 17/11/2026):
// prima questa finestra mandava la sessione in congedo e la scheda dell'altra restava aperta. Ora chiude anche
// quella scheda, senza segnarla tolta: la finestra che l'ha aperta la vede sparire e manda lei la sessione in
// congedo (guardaSchede di volta.js), come col ⌘W. Due congedi farebbero due /fine. Se la macchina di una di
// quelle finestre non risponde, nessuno vedrebbe sparire la scheda: allora non chiude niente e torna 0, e il
// congedo lo fa questa finestra. Una scheda senza segno nel core di un'altra macchina non la guarda nessuno: si
// chiude come una di qui. Torna quante schede di altre finestre ha chiuso.
export function chiudiAltrui(s) {
  const io = ioQui();
  const l = schedeDi(s).filter((t) => !mia(t, io));
  const giu = new Set((shared("arturo.volta.macchine") ?? []).filter((m) => m?.giu && m.macchina).map((m) => nomeFile(m.macchina)));
  const note = new Set((shared("arturo.volta.macchine") ?? []).filter((m) => m?.macchina).map((m) => nomeFile(m.macchina)));
  const padroni = l.filter((t) => daDi(t.argv));
  if (padroni.some((t) => giu.has(daDi(t.argv)) || !note.has(daDi(t.argv)))) return 0;
  for (const t of l) {
    if (!daDi(t.argv)) segnaTolto(t.address);
    chiudiTerminale(t.address);
  }
  return padroni.length;
}

// Rinomina e Cambia progetto (#5292): volta_sonda.py rinomina o progetto scrive il nome o il progetto
// sulla macchina della sessione, con fonte "persona". Vuole il sessionId intero: i file della cache
// portano quello. `opzioni`: ["--portato"] quando Claude Code ha già il nome. { ok } oppure { errore }.
export async function cambiaSessione(s, cosa, valore, opzioni = []) {
  const c = await config();
  try {
    const r = await exec(c.arturo[0], [c.volta, ...entroDi("cambia"), cosa === "nome" ? "rinomina" : "progetto", s.host ?? "qui", s.sessionId, ...opzioni,
      ...(valore ? ["--", valore] : [])], { timeout: tettoDi("cambia") });
    return esito(r);
  } catch (e) {
    return { errore: `${s.macchina ?? nomeMacchina(s.host ?? "qui")} non risponde (${String(e?.message ?? e).slice(0, 120)})` };
  }
}

// I terminali di questa finestra che mostrano la sessione: le schede che la agganciano e, per
// un'interattiva partita in una scheda di Herdr su questa macchina, quella scheda.
// `solo_mie`: solo le schede aperte da questa finestra (mie). Una scheda nel core di un'altra macchina la
// vedono due finestre, e /rename e /inizio li scrive solo chi l'ha aperta (#5810, 17/11/2026).
function terminaliDi(s, soloMie = false) {
  const l = (soloMie ? mie(s) : schedeDi(s)).map((t) => t.address);
  if (s?.questa && s.terminale && !l.includes(s.terminale) && panes().some((p) => p.terminal === s.terminale)) l.push(s.terminale);
  return l;
}

// Il nome nuovo sulle schede della sessione, come le chiama aggancia(). Torna quante ne ha rinominate.
export function rinominaSchede(s, nome) {
  let n = 0;
  for (const a of terminaliDi(s)) {
    const p = panes().find((x) => x.terminal === a);
    if (!p || panes().filter((x) => x.tab === p.tab).length !== 1) continue;
    run("tab.rename", { id: p.tab, name: String(nome).slice(0, 40) });
    n++;
  }
  return n;
}

// Porta in Claude Code il nome scritto dalla persona: /rename nella scheda della sessione, così il
// nome compare anche in claude agents e in /resume. Solo se la sessione è ferma (daPortare), ha una
// scheda in questa finestra con Claude dentro e la casella vuota: mai sopra una bozza. Poi lo segna
// alla sonda (--portato), così non lo riscrive. Torna true se l'ha portato; altrimenti si riprova
// alla lettura dopo.
// Lo stesso nome non si riscrive per PORTA_MS: se la sonda non riesce a segnarlo (macchina lenta, rete
// giù) daPortare resta, e senza questa memoria /rename finiva nella conversazione a ogni lettura.
// In quel tempo si riprova solo a segnarlo.
export const PORTA_MS = 5 * 60 * 1000;
const portati = new Map(); // sessionId → { nome, quando }

// Scrive un comando di Claude Code (/rename, /inizio) nella prima scheda buona della sessione, solo
// a casella vuota. Torna true se l'ha scritto.
async function scriviComando(s, testo) {
  let scritto = false;
  // la prima scheda buona: una sessione può averne più d'una, e una può essere rimasta con la shell
  for (const a of terminaliDi(s, true)) {
    if (await nuda(a)) continue;
    try {
      const schermo = await hc(["read", a]);
      if (schermo.code !== 0 || !casellaVuota(schermo.stdout)) continue;
      const r = await hc(["send", a, testo]);
      scritto = r.code === 0;
    } catch { /* si prova la scheda dopo */ }
    break;
  }
  return scritto;
}
const scriviNome = (s, nome) => scriviComando(s, `/rename ${nome}`);

// La risposta della Coda e della checklist nella scheda, come scriviComando, ma dice perché non entra:
// l'errore va nel registro e nell'avviso (17/11/2026). La casella vuota sullo schermo vuol dire che non
// c'è un dialogo aperto: se hc send rifiuta la scheda perché la conversazione aspetta la persona
// (stato blocked dopo una domanda), si riprova una volta con --force.
async function scriviRisposta(s, testo) {
  const schede = terminaliDi(s, true);
  if (!schede.length) return { errore: "la scheda della sessione l'ha aperta un'altra finestra" };
  let errore = "la scheda ha solo la shell, senza Claude";
  for (const a of schede) {
    if (await nuda(a)) continue;
    try {
      const schermo = await hc(["read", a]);
      if (schermo.code !== 0) { errore = "hc read non legge la scheda"; continue; }
      const perche = percheNonEntra(schermo.stdout);
      if (perche) { errore = perche; continue; }
      let r = await hc(["send", a, testo]);
      if (r.code !== 0) r = await hc(["send", "--force", a, testo]);
      return r.code === 0 ? { ok: true } : { errore: `hc send non scrive: ${String(r.stderr || r.stdout || "").trim().slice(0, 120)}` };
    } catch (e) {
      errore = `la scheda non risponde (${String(e?.message ?? e).slice(0, 80)})`;
    }
  }
  return { errore };
}

// Quante schede di questa finestra mostrano la sessione: per canaleRisposta() di sessioni.js.
export const schedeRisposta = (s) => terminaliDi(s).length;

// La risposta della Coda alla sessione (#5721), sul canale scelto da canaleRisposta(): "scheda" la scrive
// nella scheda a casella vuota, "background" passa da volta_sonda.py rispondi (stop e ripresa con la
// risposta). Gli altri canali li apre chi chiama. Torna { ok } oppure { errore, rifiutata? }.
// Attesa: ATTESA_AZIONE più ATTESA_NASCITA della sonda, come iniziaSessione.
export async function rispondiSessione(s, testo, canale) {
  if (canale === "scheda") return scriviRisposta(s, testo);
  if (canale !== "background") return { errore: `canale ${canale}: la risposta non parte da qui` };
  const cfg = await config();
  try {
    const r = await exec(cfg.arturo[0], [cfg.volta, ...entroDi("rispondi"), "rispondi", s.host ?? "qui", s.id, s.sessionId,
      ...(s.cartella ? ["--cartella", s.cartella] : []), "--", testo], { timeout: tettoDi("rispondi") });
    return esito(r);
  } catch (e) {
    return { errore: `${s.macchina ?? nomeMacchina(s.host ?? "qui")} non risponde (${String(e?.message ?? e).slice(0, 120)})` };
  }
}

// Il giudice dei permessi acceso o spento su una macchina (tasto G dell'Orchestratore, Fase 2 del piano del
// 20/11/2026): volta_sonda.py giudice scrive o toglie cache/giudice-spento. Torna { ok, giudice } | { errore }.
export async function giudiceSu(host, stato) {
  const cfg = await config();
  try {
    return esito(await exec(cfg.arturo[0], [cfg.volta, ...entroDi("giudice"), "giudice", host ?? "qui", stato], { timeout: tettoDi("giudice") }));
  } catch (e) {
    return { errore: `${nomeMacchina(host ?? "qui")} non risponde (${String(e?.message ?? e).slice(0, 120)})` };
  }
}

// La ripresa da sola (#5882): il canale come la risposta della Coda, ma solo dove arriva senza la persona.
// Una scheda di questa finestra: il testo si scrive lì. Una scheda di un'altra finestra: lo fa quella. In
// background senza schede: stop e ripresa col testo (rispondi). Prima volta_sonda.py ripresa conta il
// tentativo sulla macchina della sessione, e rifiuta con la rete giù o un tentativo già fatto.
// Torna { ok, tentativo } | { errore, rifiutata?, rete?, salta? }.
export async function riprendiDaSola(s, testo) {
  const canale = terminaliDi(s, true).length ? "scheda" : terminaliDi(s).length ? null : s.tipo === "background" ? "background" : null;
  if (!canale) return { errore: "la sessione la raggiunge un'altra finestra", salta: true };
  const cfg = await config();
  let r;
  try {
    r = esito(await exec(cfg.arturo[0], [cfg.volta, ...entroDi("ripresa"), "ripresa", s.host ?? "qui", s.sessionId, "--errore", s.errore.quando,
      "--tipo", s.errore.tipo, ...(s.riuscita ? ["--riuscita", s.riuscita] : [])], { timeout: tettoDi("ripresa") }));
  } catch (e) {
    return { errore: `${s.macchina ?? nomeMacchina(s.host ?? "qui")} non risponde (${String(e?.message ?? e).slice(0, 120)})` };
  }
  if (r.errore) return r;
  const m = await rispondiSessione(s, testo, canale);
  return { ...m, tentativo: r.tentativo, canale };
}

// Una riga nel registro delle risposte (volta_carte.py risposta, rigaRisposta() di sessioni.js): per la
// misura delle raccomandazioni accettate. Una scrittura che non riesce non ferma la Coda.
// Le carte scartate dalla Coda (16/11/2026): volta_carte.py le tiene in scartate.json accanto al registro.
export async function scartaCarta(chiaveCarta, quando) {
  try {
    const cfg = await config();
    await exec(cfg.arturo[0], [`${appHome()}/mods/arturo/volta_carte.py`, ...entroDi("carte"), "scarta", JSON.stringify({ chiave: chiaveCarta, quando })], { timeout: tettoDi("carte") });
  } catch { /* resta scartata fino al riavvio */ }
}
// Le risposte UF delle ultime 48 ore dal registro (#5742): dopo un riavvio una carta già risposta resta
// fuori fino al giro dopo del capo. { chiave: istante in ms }, {} se non si legge.
export async function leggiRecenti() {
  try {
    const cfg = await config();
    const d = esito(await exec(cfg.arturo[0], [`${appHome()}/mods/arturo/volta_carte.py`, ...entroDi("carte"), "recenti"], { timeout: tettoDi("carte") }));
    return d.errore ? {} : d;
  } catch { return {}; }
}
export async function leggiScartate() {
  try {
    const cfg = await config();
    const d = esito(await exec(cfg.arturo[0], [`${appHome()}/mods/arturo/volta_carte.py`, ...entroDi("carte"), "scartate"], { timeout: tettoDi("carte") }));
    return d.errore ? {} : d;
  } catch { return {}; }
}

export async function registraRisposta(riga) {
  try {
    const cfg = await config();
    await exec(cfg.arturo[0], [`${appHome()}/mods/arturo/volta_carte.py`, ...entroDi("carte"), "risposta", JSON.stringify(riga)], { timeout: tettoDi("carte") });
  } catch { /* il registro non ferma la Coda */ }
}

export async function portaNome(s) {
  const nome = daPortare(s);
  if (!nome) return false;
  const p = portati.get(s.sessionId);
  let scritto = Boolean(p) && p.nome === nome && Date.now() - p.quando < PORTA_MS;
  if (!scritto) {
    scritto = await scriviNome(s, nome);
    if (scritto) portati.set(s.sessionId, { nome, quando: Date.now() });
  }
  if (!scritto) return false;
  const esito = await cambiaSessione(s, "nome", nome, ["--portato"]);
  return Boolean(esito.ok);
}

// Una sessione spostata dalla persona in un altro progetto riparte da /inizio di quel progetto, così
// carica handoff, task e scheda (#5465, 12/11/2026: "Volta lancia /inizio a ogni spostamento").
// Solo a sessione ferma (daIniziare). Con una scheda in questa finestra /inizio si scrive lì, a casella
// vuota; in background senza scheda la sonda la ferma e la riprende col solo /inizio (inizia, come il
// congedo); un'interattiva in un Terminale non si raggiunge, e lo dice chi chiama (come "terminale").
// Poi il segno alla sonda (--iniziato). Lo stesso progetto non si riscrive per PORTA_MS, come il nome.
// `ripresa`: false nelle finestre che non hanno fatto lo spostamento. Lì vale solo la scheda: ogni
// finestra di Volta vede la stessa sessione, e la ripresa partirebbe una volta per finestra.
// Torna { fatto, come } con come = scheda | ripresa | terminale.
const iniziati = new Map(); // sessionId → { slug, quando, come }

export async function iniziaSessione(s, slug) {
  const cfg = await config();
  try {
    const r = await exec(cfg.arturo[0], [cfg.volta, ...entroDi("inizia"), "inizia", s.host ?? "qui", s.id, s.sessionId, slug, ...(s.cartella ? ["--cartella", s.cartella] : [])], { timeout: tettoDi("inizia") });
    return esito(r);
  } catch (e) {
    return { errore: `${s.macchina ?? nomeMacchina(s.host ?? "qui")} non risponde (${String(e?.message ?? e).slice(0, 120)})` };
  }
}

export async function portaInizio(s, ripresa = true) {
  const slug = daIniziare(s);
  if (!slug) return { fatto: false };
  const p = iniziati.get(s.sessionId);
  let come = p && p.slug === slug && Date.now() - p.quando < PORTA_MS ? p.come : null;
  if (!come) {
    if (terminaliDi(s, true).length) come = (await scriviComando(s, `/inizio ${slug}`)) ? "scheda" : null;
    // una scheda c'è ma l'ha aperta un'altra finestra: /inizio lo scrive quella (#5810)
    else if (terminaliDi(s).length) return { fatto: false };
    else if (!ripresa) return { fatto: false };
    else if (s.tipo === "background") come = (await iniziaSessione(s, slug)).ok ? "ripresa" : null;
    else come = "terminale";
    if (come) iniziati.set(s.sessionId, { slug, quando: Date.now(), come });
  }
  if (!come) return { fatto: false };
  const esito = await cambiaSessione(s, "progetto", slug, ["--iniziato"]);
  return { fatto: Boolean(esito.ok), come };
}

// La sessione nello spazio del progetto nuovo. Una scheda che la aggancia si chiude e si riapre là:
// chiudere un aggancio non ferma la sessione. Un'interattiva che gira dentro una scheda di Herdr non si
// sposta, perché chiudere quella scheda la fermerebbe: resta dov'è, e lo dice chi chiama.
// Torna { spostata } | { resta } | {} (nessuna scheda aperta) | { errore }.
export async function spostaScheda(s, progetto) {
  if (s.tipo !== "background" || !Array.isArray(s.attach)) return s.terminale ? { resta: true } : {};
  if (!chiudiSchede(s)) return {};
  await pausa(600);
  const r = await apriSessione({ ...s, progetto }, s.attach);
  return r.errore ? { errore: r.errore } : { spostata: true };
}

// Come bin/sessione.py: niente caratteri che rompono il prompt.
const pulito = (t) => (t ?? "").replace(/[`$"\\\n\r]/g, " ").replace(/\s+/g, " ").trim().slice(0, 160);

// I progetti dalla memoria che la persona ha già (arturo progetti --json): cartelle, handoff, righe di
// stato e catalogo della fonte dei task, uniti da Arturo. null se l'Arturo installato non ha il comando:
// chi chiama ricade sulle cartelle.
export async function progettiMemoria() {
  const r = await arturo("progetti", ["--json"], "");
  return r.ok && Array.isArray(r.json?.progetti) ? r.json.progetti : null;
}

// I nomi fra cui scegliere in "Apri un progetto" e "Cambia progetto", dal più recente: la memoria, o le
// cartelle con un Arturo che non ha ancora il comando.
export async function nomiProgetti() {
  const m = await progettiMemoria();
  return m ? m.map((p) => (p.cartella ? p.nome : p.slug)).filter(Boolean) : cartelle();
}

// Unisci due progetti doppioni (#6187): arturo progetti unisci PERDENTE VINCITORE [--prova] --json, letto da
// vistaUnione di sessioni.js. Con `prova` Arturo conta e non scrive niente. Arturo esce 2 col motivo in JSON
// quando rifiuta: per questo non passa da arturo(), che di un'uscita diversa da 0 tiene solo la prima riga.
export async function unione(perdente, vincitore, prova) {
  const tetto = prova ? UNIONE_PROVA_MS : UNIONE_MS;
  const t0 = Date.now();
  try {
    const c = await config();
    const [cmd, ...pre] = c.arturo;
    const r = await exec(cmd, [...pre, "progetti", "unisci", perdente, vincitore, ...(prova ? ["--prova"] : []), "--json"], { cwd: c.base, timeout: tetto });
    const d = leggiUnione(r.stdout);
    if (d) return vistaUnione(d, perdente, vincitore);
    return { ...vistaUnione(null), testo: prima(r.stderr) || `Arturo si è fermato senza dire perché (uscita ${r.code}).` };
  } catch (e) {
    const scaduto = Date.now() - t0 >= tetto - 1000;
    return { ...vistaUnione(null), testo: scaduto ? `Arturo non ha risposto in ${Math.round(tetto / 1000)} secondi.` : String(e?.message ?? e).slice(0, 160) };
  }
}

// L'unione vera, dalla barra: la manda solo il pulsante Unisci del dialogo (unisci.js), che è il sì della
// persona. Lo stato sta in shared arturo.unione, che il dialogo mostra: { perdente, vincitore, stato:
// "corso" | "fatto" | "errore", vista, quando }. Una alla volta. Un'unione che non risponde entro il tetto può
// essere ancora in corso: l'avviso lo dice, e non si rilancia da sola.
export async function unisci(perdente, vincitore) {
  const noti = shared("arturo.progetti");
  const no = percheNonUnire(perdente, vincitore, noti);
  if (no) { notify({ title: "Non unisco", body: no, level: "warning" }); return { stato: "errore", testo: no }; }
  const p = canonico(perdente), v = canonico(vincitore);
  const ora = shared("arturo.unione");
  if (ora?.stato === "corso" && Date.now() - ora.quando < UNIONE_MS) {
    notify({ title: "Un'unione è già in corso", body: `${ora.perdente} entra in ${ora.vincitore}: aspetta che finisca.`, level: "warning" });
    return { stato: "errore", testo: "Un'unione è già in corso." };
  }
  setShared("arturo.unione", { perdente: p, vincitore: v, stato: "corso", vista: null, quando: Date.now() });
  const vista = await unione(p, v, false);
  const ok = vista.stato === "fatto";
  setShared("arturo.unione", { perdente: p, vincitore: v, stato: ok ? "fatto" : "errore", vista, quando: Date.now() });
  if (ok) notify({ title: `${nomeProgettoDi(p)} ora è ${nomeProgettoDi(v)}`, body: `Il nome ${p} resta valido. Copia di prima: ${vista.backup}`, level: "info" });
  else notify({ title: "L'unione non è riuscita", body: `${vista.testo || "Arturo non ha confermato."} Guarda data/progetti/unioni/ prima di riprovare.`, level: "error" });
  return vista;
}

// Cerca doppioni (#6188): le coppie che la persona ha scartato ("Non sono doppioni") stanno in
// doppioni-scartati.json nella cartella di Volta, { "<slug>|<slug>": { n, quando } }. `n` conta i gesti della
// persona sulla coppia: dispari è scartata, pari è rimessa fra i doppioni ("Rimetti fra i doppioni", #6268).
// volta_note.py porta il file sulle altre macchine a ogni giro delle note, e fra due copie vale il conto più
// alto: uno scarto e un ripensamento arrivano dappertutto senza guardare gli orologi delle macchine. Un numero
// solo (il file del 21/11/2026, per macchina) vale { n: 1, quando: quel numero }.
export const fileDoppioni = () => `${appHome()}/doppioni-scartati.json`;
// Una voce del file come { n, quando }, o null se non è una voce.
export function voceScarto(v) {
  if (typeof v === "number" && Number.isFinite(v)) return { n: 1, quando: v };
  if (!v || typeof v !== "object" || !Number.isInteger(v.n) || v.n < 1) return null;
  return { n: v.n, quando: Number.isFinite(v.quando) ? v.quando : 0 };
}
export const scartata = (v) => (voceScarto(v)?.n ?? 0) % 2 === 1;
// null se il file c'è e non si legge come un oggetto: chi scrive non lo sostituisce.
const leggiScartati = (testo) => {
  try { const d = JSON.parse(testo ?? "{}"); return d && typeof d === "object" && !Array.isArray(d) ? d : null; }
  catch { return null; }
};
// Le coppie scartate adesso, { chiave: quando }: quelle rimesse fra i doppioni restano nel file e non stanno qui.
export async function doppioniScartati() {
  const d = leggiScartati(await readTextFile(fileDoppioni()).catch(() => null)) ?? {};
  return Object.fromEntries(Object.entries(d).filter(([, v]) => scartata(v)).map(([k, v]) => [k, voceScarto(v).quando]));
}
// Scarta la coppia `chiave` (chiaveCoppia di doppioni.js), o la rimette fra i doppioni. La esegue la barra: due
// gesti di fila si scrivono uno sull'altro, e writeTextFile rifiuta chi ha letto il file prima dell'altro. Allora
// rilegge e riprova. Un file che non si legge (una virgola sbagliata dopo una correzione a mano) non si riscrive:
// porterebbe via tutti gli scarti di prima. L'avviso dice di sistemarlo. La voce non si toglie mai: il conto sale
// di uno, e così il gesto vince sulle copie delle altre macchine.
export const SCARTA_TENTATIVI = 4;
const DETTO = {
  scarta: { titolo: "Non ho salvato lo scarto", poi: "scarta di nuovo la coppia", esito: "tornerà fra i doppioni probabili" },
  riprendi: { titolo: "Non ho rimesso la coppia fra i doppioni", poi: "rimettila di nuovo", esito: "resta fra le scartate" },
};
async function segnaDoppione(chiave, verso) {
  const detto = DETTO[verso];
  if (!/^[a-z0-9][a-z0-9-]*\|[a-z0-9][a-z0-9-]*$/.test(String(chiave ?? ""))) return false;
  for (let i = 0; i < SCARTA_TENTATIVI; i += 1) {
    const prima = await readTextFile(fileDoppioni()).catch(() => null);
    const d = leggiScartati(prima);
    if (!d) {
      notify({ title: detto.titolo, body: `${fileDoppioni()} non si legge: sistemalo o toglilo, poi ${detto.poi}.`, level: "warning" });
      return false;
    }
    if (scartata(d[chiave]) === (verso === "scarta")) return true;
    const voce = { n: (voceScarto(d[chiave])?.n ?? 0) + 1, quando: Date.now() };
    try { await writeTextFile(fileDoppioni(), JSON.stringify({ ...d, [chiave]: voce }, null, 1), prima ?? null); return true; }
    catch { /* un altro gesto ha scritto nel frattempo: si rilegge */ }
  }
  notify({ title: detto.titolo, body: `La coppia ${chiave.replace("|", " e ")} ${detto.esito}.`, level: "warning" });
  return false;
}
export const scartaDoppione = (chiave) => segnaDoppione(chiave, "scarta");
// "Rimetti fra i doppioni" (#6268): la coppia scartata torna fra le probabili, su tutte le macchine.
export const riprendiDoppione = (chiave) => segnaDoppione(chiave, "riprendi");

// Le cartelle della base dei progetti, dalla più recente.
export async function cartelle() {
  try {
    const c = await config();
    const r = await exec("sh", ["-c", 'cd "$1" 2>/dev/null && ls -td -- */ 2>/dev/null', "sh", c.base], { timeout: 15000 });
    if (r.code !== 0) return [];
    return r.stdout.split("\n").map((d) => d.trim().replace(/\/$/, "")).filter((d) => d && !d.startsWith("_") && !d.startsWith("."));
  } catch {
    return [];
  }
}

// Un gesto su una sessione di Volta (sessioni.js azioni): volta_sonda.py azione, qui o via herdr-core.
// Torna { righe } per l'anteprima, { ok, testo } per gli altri, { errore } se non va.
// Riavvia accende prima il servizio di Claude (#5215): aspetta ATTESA_SERVIZIO più ATTESA_AZIONE di
// volta_sonda.py, più 30 s; gli altri gesti ATTESA_AZIONE più 30 s (il banco HZ42 tiene i conti).
// `congedo`: lo stop o l'rm li chiede il congedo, non la persona. Lo stop passa allora dal controllo fresco
// di volta_sonda.py (#5636): con un'altra scheda che la aggancia torna { errore, rifiutata }.
export async function azioneSessione(s, verbo, { congedo = false } = {}) {
  const c = await config();
  try {
    const r = await exec(c.arturo[0], [c.volta, ...entroDi(verbo === "respawn" ? "respawn" : "azione"), "azione", s.host, verbo, s.id, ...(congedo ? ["--congedo"] : [])], { timeout: tettoDi(verbo === "respawn" ? "respawn" : "azione") });
    return esito(r);
  } catch (e) {
    return { errore: `${s.macchina} non risponde (${String(e?.message ?? e).slice(0, 120)})` };
  }
}

// Il contesto di un progetto per la finestra di contestoui.js: `arturo contesto <slug> --json` (le fonti
// che /inizio legge, nell'ordine). { ok, json } oppure { ok: false, errore }; un Arturo senza il comando
// risponde con un errore che la finestra mostra.
export async function contestoProgetto(progetto) {
  return arturo("contesto", [String(progetto ?? ""), "--json"], "Arturo non risponde");
}

// Le carte UF della Coda (#5722): `volta_capo.py prendi <capo>` le legge dal capo con herdr-core, ne
// tiene una copia e, col capo giù, rende l'ultima con vecchia: true. { letto, carte, vecchia?, errore? }
// oppure null se lo script non risponde.
export async function prendiCarteUf() {
  try {
    const c = await config();
    const r = await exec(c.arturo[0], [`${appHome()}/mods/arturo/volta_capo.py`, ...entroDi("capo"), "prendi", c.capo], { timeout: tettoDi("capo") });
    const d = JSON.parse(String(r.stdout ?? "").trim().split("\n").pop() || "null");
    return d && Array.isArray(d.carte) ? d : null;
  } catch {
    return null;
  }
}

// "Apri" di una bozza della Coda: Gmail in Firefox, che è il browser delle schede da leggere; senza
// Firefox il browser di sistema.
export async function apriLink(url) {
  if (!/^https:\/\//.test(String(url ?? ""))) return false;
  const win = home().includes("\\") || /^[A-Za-z]:/.test(home());
  const prove = win ? [["cmd", ["/c", "start", "", "firefox", url]], ["cmd", ["/c", "start", "", url]]]
    : [["open", ["-a", "Firefox", url]], ["open", [url]]];
  for (const [cmd, args] of prove) {
    try { if ((await exec(cmd, args, { timeout: 10000 })).code === 0) return true; } catch { /* la prossima */ }
  }
  notify({ title: "Non riesco ad aprire il link", body: url, level: "warning" });
  return false;
}

// "Apri" di una fonte del contesto: il file nel programma di sistema (open sul Mac, start su Windows).
export async function apriFile(percorso) {
  if (!percorso) return;
  const win = /^[A-Za-z]:[\\/]/.test(percorso) || percorso.includes("\\");
  try {
    const r = win ? await exec("cmd", ["/c", "start", "", percorso], { timeout: 10000 }) : await exec("open", [percorso], { timeout: 10000 });
    if (r.code !== 0) notify({ title: "Non riesco ad aprire il file", body: percorso, level: "warning" });
  } catch {
    notify({ title: "Non riesco ad aprire il file", body: percorso, level: "warning" });
  }
}
