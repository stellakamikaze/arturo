// I dati di Arturo per Herdr: configurazione, todo, progetti e le azioni che aprono Claude.
// Tutte le parti del mod leggono da qui, così dicono le stesse cose con le stesse parole.

import { exec, readTextFile, appHome, home, hc, spaces, agents, run, notify, shared, setShared, terminals, panes } from "herdr";
import { titolo, agganciata, titoloFork, casellaVuota, daPortare, argvScheda, motivoUscita } from "./sessioni.js";

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
  return {
    arturo,
    // La cartella di Arturo, dove stanno shared/ e bin/: ~/.claude per chi usa il clone, un'altra cartella
    // per il plugin o per una copia di prova. Un arturo.json di prima ce l'ha solo nel bin: …/bin/arturo.
    radice: typeof c.radice === "string" && c.radice ? c.radice : radiceDa(arturo[arturo.length - 1]),
    base: typeof c.base === "string" && c.base ? c.base : `${home()}/Documents/ClaudeCode`,
    // Il progetto delle note sulla finestra (⌘⇧N); senza, va al progetto aperto.
    note_progetto: typeof c.note_progetto === "string" && c.note_progetto ? c.note_progetto : null,
    // volta_sonda.py: "volta" in arturo.json (una copia di prova), altrimenti quello del mod. L'unico
    // punto che lo dice: lo usano l'elenco di Volta (volta.js) e la nascita su un'altra macchina.
    volta: typeof c.volta === "string" && c.volta ? c.volta : `${appHome()}/mods/arturo/volta_sonda.py`,
    // La chiusura automatica delle sessioni che aspettano un comando (#5366): "prova" (scrive solo cosa
    // chiuderebbe, in ~/.cache/volta/congedo-auto.json), "acceso" o "spento". Senza voce vale "prova".
    congedo: {
      modo: ["prova", "acceso", "spento"].includes(c.congedo) ? c.congedo : "prova",
      dopoMin: numero(c.congedo_dopo_min, 60, 5),
      ora: numero(c.congedo_ora, 3, 0),
      giorno: numero(c.congedo_giorno, 12, 0),
    },
  };
}

// Un numero intero di arturo.json, non sotto `minimo`; altrimenti quello di serie.
const numero = (v, serie, minimo) => (Number.isInteger(v) && v >= minimo ? v : serie);

export function radiceDa(bin) {
  const m = /^(.+)[\\/]bin[\\/]arturo$/.exec(String(bin ?? ""));
  return m ? m[1] : `${home()}/.claude`;
}

// Il testo di un suggerimento con la cartella di Arturo al posto di {radice}.
export const richiesta = (prompt, radice) => (prompt ?? "").split("{radice}").join(radice);

// arturo <comando> <args>: { ok, json, errore }. Mai un'eccezione verso l'interfaccia.
async function arturo(comando, args, errore) {
  try {
    const c = await config();
    const [cmd, ...pre] = c.arturo;
    const r = await exec(cmd, [...pre, comando, ...args], { cwd: c.base });
    if (r.code !== 0) return { ok: false, errore: prima(r.stderr) || prima(r.stdout) || `uscita ${r.code}`, codice: r.code };
    if (!args.includes("--json")) return { ok: true, testo: prima(r.stdout) };
    return { ok: true, json: JSON.parse(r.stdout) };
  } catch (e) {
    return { ok: false, errore };
  }
}

export const todo = (args) => arturo("todo", args, "Non riesco a leggere i todo di Arturo.");

// Rispondi, Risolta e Scarta del velo: arturo note <verbo> <id> --chi federico. La CLI riscrive nota.json
// rileggendolo se è cambiato, e porta il gesto sul todo: velo e Claude chiudono con lo stesso codice.
export const gestoNota = (verbo, id, testo) => {
  const t = String(testo ?? "").trim();
  return arturo("note", [verbo, id, "--chi", "federico", "--json", ...(t ? ["--", t] : [])],
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

// Lo slug come lo fa Arturo: minuscole, lettere, numeri e trattini.
export const slug = (s) => (s ?? "").toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, "").replace(/[^a-z0-9-]+/g, "-").replace(/^-+|-+$/g, "");

// Uno spazio è un progetto se sta su questo computer, ha un nome scritto e non è "Volta": quello
// raccoglie le sessioni senza progetto (aggancia), non ha todo e non va fra i progetti della barra.
export const eProgetto = (s) => Boolean(s) && !s.machine && Boolean(s.named) && slug(s.name) !== "volta";

// Lo spazio di Herdr di un progetto: quello su questo computer col nome del progetto.
export const spazio = (nome) => spaces().find((s) => !s.machine && slug(s.name) === slug(nome));

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
    if (v) { v.alias = m.alias ?? []; v.data = m.data || ""; if (m.titolo) v.titolo = m.titolo; continue; }
    const noto = Boolean(m.handoff || m.riga || m.titolo);
    per.set(m.slug, { chiave: m.slug, nome: m.cartella ? m.nome : m.slug, titolo: m.titolo || bello(m.nome || m.slug),
      categoria: m.categoria || (noto || !conCategorie ? "" : "Altre cartelle"), riga: m.riga ?? "", calcolato: !m.riga,
      tu: 0, decidi: 0, io: 0, fermo: 0, cartella: Boolean(m.cartella), alias: m.alias ?? [], data: m.data || "",
      ferma: noto && Boolean(limite) && (m.data || "") < limite });
  }
  // Con un Arturo senza il comando: le cartelle della base dei progetti senza todo, come prima.
  for (const nome of memoria ? [] : extra.cartelle ?? []) {
    const k = slug(nome);
    if (!k || per.has(k)) continue;
    const st = extra.stati?.[nome] ?? extra.stati?.[k];
    per.set(k, { chiave: k, nome, titolo: bello(nome), categoria: conCategorie ? "Altre cartelle" : "", riga: st?.riga ?? "", calcolato: !st?.riga, tu: 0, decidi: 0, io: 0, fermo: 0, cartella: true });
  }
  for (const s of spaces()) {
    if (!eProgetto(s)) continue;
    const k = slug(s.name);
    if (!per.has(k)) per.set(k, { chiave: k, nome: s.name, titolo: bello(s.name), categoria: "", tu: 0, decidi: 0, io: 0, fermo: 0 });
  }
  const RANGO = { blocked: 5, done: 4, working: 3, idle: 2 };
  // Gli spazi si leggono una volta sola: spaces() attraversa il confine con Herdr, e chiamarlo due volte
  // per ognuna delle cento e più voci (cartelle della base comprese) sfora i 50 ms del render.
  const locali = new Map();
  for (const s of spaces()) if (!s.machine) { const k = slug(s.name); if (!locali.has(k)) locali.set(k, s); }
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
// Prima la scheda attiva: lo spazio "Volta" ne tiene più d'una, e la testata parla di quella che vedi.
export function schedaAgganciata(s) {
  const tabs = new Set((s?.tabs ?? []).map((tb) => tb.id));
  const attiva = s?.tabs?.find((tb) => tb.active)?.id;
  for (const p of [...panes()].sort((a, b) => (b.tab === attiva) - (a.tab === attiva))) {
    if (!tabs.has(p.tab)) continue;
    const t = terminals().find((x) => x.address === p.terminal);
    if (Array.isArray(t?.argv) && t.argv.includes("attach")) {
      return { terminal: t.address, tab: p.tab, id: String(t.argv[t.argv.indexOf("attach") + 1] ?? "") };
    }
  }
  return null;
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

// Lo stato di uno spazio: quello di Herdr, oppure, per una scheda che aggancia una sessione in background
// (dove Herdr non vede un agente), quello che legge Volta. Lo usano barra, testata e todo.
export function statoSpazio(s) {
  if (!s) return null;
  return s.status ?? statoAgganciata(schedaAgganciata(s));
}

// La sessione agganciata nella scheda `g` come la elenca Volta (~/.cache/volta/sessioni.json), o null.
async function sessioneDi(g) {
  try {
    const d = JSON.parse((await readTextFile(`${home()}/.cache/volta/sessioni.json`)) ?? "{}");
    return (d.sessioni ?? []).find((x) => x?.id === g.id && Array.isArray(x.attach)) ?? null;
  } catch {
    return null;
  }
}

// Prima di scrivere a Claude in una scheda agganciata: se claude attach è uscito, nella scheda c'è la
// shell, e il testo di un todo ci finirebbe come comando. true: la scheda ha la shell, il testo non
// parte. La sessione si riapre nella sua scheda (apriSessione) e la persona riprova: il testo non si
// manda dopo il rilancio, perché nessuno dice quando Claude è pronto a riceverlo.
async function tornataShell(g) {
  if (!(await nuda(g.terminal))) return false;
  const s = await sessioneDi(g);
  if (!s) {
    notify({ title: "La sessione di questa scheda è chiusa", body: "Chiudi la scheda e riapri la sessione dall'elenco di Volta.", level: "warning" });
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
  nome = slug(nome);
  const s = spazio(nome);
  if (s) {
    run("space.select", { id: s.id });
    if (!todoScelto) return;
    const testo = `Lavoriamo sul todo #${todoScelto.id}: ${todoScelto.titolo}`;
    const a = agents().find((x) => x.space === s.id);
    // Uno spazio nato su un'altra macchina: si scrive nella scheda che la aggancia. hc send non scrive
    // se il programma aspetta una risposta, e così non risponde al posto della persona.
    const g = a ? null : schedaAgganciata(s);
    if (g) {
      run("tab.select", { id: g.tab });
      if (statoAgganciata(g) === "blocked") return notify({ title: "Claude aspetta una tua risposta", body: "Rispondi nella sessione, poi riprova.", level: "warning" });
      if (await tornataShell(g)) return;
      const r = await hc(["send", g.terminal, testo]);
      if (r.code !== 0) notify({ title: "Non sono riuscito a scrivere a Claude", body: prima(r.stderr) || "Se Claude aspetta una tua risposta, rispondi nella sessione e riprova.", level: "warning" });
      return;
    }
    if (!a) return notify({ title: "La sessione di questo progetto è chiusa", body: "Chiudi lo spazio e riaprilo dalla barra.", level: "warning" });
    if (a.status === "blocked") return notify({ title: "Claude aspetta una tua risposta", body: "Rispondi nella sessione, poi riprova.", level: "warning" });
    const r = await hc(["send", a.address, testo]);
    if (r.code !== 0) notify({ title: "Non sono riuscito a scrivere a Claude", body: prima(r.stderr), level: "error" });
    return;
  }
  const prompt = todoScelto ? `/inizio ${nome} -- #${todoScelto.id} ${pulito(todoScelto.titolo)}` : `/inizio ${nome}`;
  return nasciSu(dove(), prompt, nome);
}

// Una richiesta nuova, senza progetto: Claude nella cartella dei progetti, sulla macchina scelta in
// "Nasce su". `soloQui`: le richieste di "Cosa posso chiedere" restano su questa macchina, perché
// parlano dei suoi progetti, dei suoi todo e della sua configurazione (chiedi()).
export async function nuova(prompt, soloQui = false) {
  return nasciSu(soloQui ? "qui" : dove(), prompt, null);
}

// La scheda nuova (⌘T, comando arturo.volta-nuova): una sessione di Claude vuota, non una shell. Nasce
// in background sulla macchina di "Nasce su" e si aggancia nello spazio che la persona sta guardando,
// col suo progetto; dallo spazio "Volta", o senza spazio, nasce senza progetto.
export async function nuovaScheda() {
  const s = spaces().find((x) => x.active && !x.machine);
  const progetto = s?.named && slug(s.name) !== "volta" ? slug(s.name) : null;
  return nasciSu(dove(), "", progetto, "Nuova sessione");
}

// Le richieste da imparare: i pulsanti del benvenuto e della finestra "Cosa posso chiedere".
// dove: "nuova" apre sempre una conversazione nuova; "qui" scrive nella conversazione aperta,
// e senza conversazione ne apre una; "apri" apre la finestra dei progetti.
export const SUGGERIMENTI = [
  { id: "trova", titolo: "Trova i miei progetti", testo: "Claude cerca sul computer le cartelle di lavoro e te le propone come progetti.",
    prompt: "Trova i miei progetti sul computer e proponimeli. Segui {radice}/shared/volta/trova-progetti.md (in un Arturo di prima del 12/11/2026 sta in shared/volta-celeste/): la cartella di Arturo è {radice}.", dove: "nuova" },
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
  const prompt = richiesta(sug.prompt, (await config()).radice);
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

// L'etichetta di Herdr sul terminale che aggancia una sessione (hc label): il suo id, quello di claude
// attach. Con l'argv dice di chi è una scheda; il nome della scheda no, perché due schede possono
// chiamarsi uguale e una rinominata cambia nome (#5290).
export const ETICHETTA = "arturo.sessione";

// Un argv come riga di comando per la shell di una scheda: fra apici ciò che non è una parola semplice.
export const comando = (argv) => (argv ?? []).map((a) => (/^[\w@%+=:,./-]+$/.test(String(a)) ? String(a) : `'${String(a).replace(/'/g, `'\\''`)}'`)).join(" ");

// I terminali che agganciano la sessione e che un pannello mostra: per etichetta, poi per argv.
// Solo quelli di questa macchina: la finestra mostra anche le schede delle altre macchine di Herdr
// ("amaltea/t21"), ma lì l'argv dell'aggancio non vale (è scritto per partire da qui: sarebbe un ssh
// dalla macchina verso sé stessa), e chiudere o rinominare da qui le schede di un'altra finestra non
// è il gesto chiesto.
export function schedeDi(s) {
  if (!s?.id) return [];
  const visti = new Set(panes().map((p) => p.terminal));
  const l = terminals().filter((x) => visti.has(x.address) && !String(x.address).includes("/"));
  const etichetta = l.filter((x) => x.labels?.[ETICHETTA] === s.id);
  return etichetta.concat(l.filter((x) => !etichetta.includes(x) && agganciata(x.argv, s)));
}

// I terminali di questa macchina che agganciano la sessione fuori dalla finestra: il core li tiene e
// nessun pannello li mostra. È una finestra del Terminale aperta col lanciatore volta-claude
// (hc run sh -c "claude attach <id>"). Vuoto se la sessione ha già una scheda qui (schedeDi): il clic
// porta davanti quella, e ogni altro terminale che la aggancia è per forza fuori dai pannelli. Senza
// questo controllo il clic apre un secondo aggancio, e i due si contendono la larghezza del terminale.
export function altrove(s) {
  if (!s?.id || schedeDi(s).length) return [];
  return terminals().filter((x) => !String(x.address).includes("/") && (x.state ?? "live") === "live" &&
    (x.labels?.[ETICHETTA] === s.id || agganciata(x.argv, s)));
}

// Stacca quei terminali: chiude l'aggancio, la sessione continua in background. Torna quanti erano.
export function stacca(s) {
  const l = altrove(s);
  for (const t of l) { segnaTolto(t.address); run("terminal.kill", { terminal: t.address }); }
  return l.length;
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
// { indirizzo: { sessionId, id, host, macchina, cartella, titolo } }. Conta il terminale vivo nel core,
// non il pannello: cambiare spazio non chiude niente. Per etichetta, poi per argv (come schedeDi).
export function schedeAgganciate(sessioni) {
  const out = {};
  // anche le righe vecchie (macchina che non risponde): la scheda resta aperta, e senza la sua riga
  // la guardia del congedo la prenderebbe per chiusa
  const fondo = (sessioni ?? []).filter((s) => s.tipo === "background" && s.id);
  for (const x of terminals()) {
    if (String(x.address).includes("/") || (x.state ?? "live") !== "live") continue;
    const s = fondo.find((y) => x.labels?.[ETICHETTA] === y.id) ?? fondo.find((y) => agganciata(x.argv, y));
    if (s) out[x.address] = { sessionId: s.sessionId, id: s.id, host: s.host, macchina: s.macchina, questa: Boolean(s.questa), cartella: s.cartella ?? null, titolo: titolo(s) };
  }
  return out;
}

// Il primo tempo del congedo: volta_sonda.py congeda (stop, poi la ripresa con /fine) sulla macchina della
// sessione. { ok } oppure { errore }. Attese: ATTESA_AZIONE più ATTESA_SERVIZIO più ATTESA_NASCITA.
export async function congedaSessione(c) {
  const cfg = await config();
  try {
    const r = await exec(cfg.arturo[0], [cfg.volta, "congeda", c.host ?? "qui", c.id, c.sessionId, ...(c.cartella ? ["--cartella", c.cartella] : []), ...(c.auto ? ["--auto"] : [])], { timeout: 400000 });
    return esito(r);
  } catch (e) {
    return { errore: `${c.macchina ?? nomeMacchina(c.host ?? "qui")} non risponde (${String(e?.message ?? e).slice(0, 120)})` };
  }
}

// La scheda è rimasta con la shell nuda: claude attach è uscito (sessione fermata altrove, connessione
// caduta, servizio spento) e Herdr ha lasciato la shell che lo aveva lanciato. Si riconosce dal programma
// in primo piano: è la shell del terminale (stesso pid) e non ha più l'argv con cui è nata, cioè ha già
// passato il comando. Mentre la shell si sta ancora avviando l'argv è quello di nascita: non è nuda.
// Su Windows la shell non cambia argv: lì una scheda non risulta mai nuda, e resta com'è.
export async function nuda(indirizzo) {
  try {
    const r = await hc(["get", indirizzo, "--json"]);
    if (r.code !== 0) return false;
    const d = JSON.parse(r.stdout);
    const f = d.foreground;
    return d.state === "live" && Boolean(f) && f.pid === d.pid && JSON.stringify(f.argv) !== JSON.stringify(d.argv);
  } catch {
    return false;
  }
}

async function etichetta(t, s) {
  if (!t || t.labels?.[ETICHETTA] === s.id) return;
  try { await hc(["label", t.address, `${ETICHETTA}=${s.id}`]); } catch { /* resta l'argv */ }
}

// Un'attesa: il mod non ha un orologio fuori da cx.timer, e qui cx non c'è.
async function pausa(ms) {
  try {
    const c = await config();
    await exec(c.arturo[0], ["-c", "import sys,time;time.sleep(float(sys.argv[1]))", String(ms / 1000)], { timeout: ms + 10000 });
  } catch { /* senza Python si va avanti senza attesa */ }
}

// volta_sonda.py apri: il servizio di Claude acceso sulla macchina della sessione, e con `riavvia` la
// sessione fatta ripartire (claude respawn). { ok, riavviata } oppure { errore }.
// Attese: ATTESA_SERVIZIO di volta_sonda.py più 30 s; con riavvia anche ATTESA_AZIONE (come Riavvia).
export async function prepara(s, riavvia = false) {
  const c = await config();
  try {
    const r = await exec(c.arturo[0], [c.volta, "apri", s.host ?? "qui", s.id, ...(riavvia ? ["--riavvia"] : [])], { timeout: riavvia ? 210000 : 150000 });
    return esito(r);
  } catch (e) {
    return { errore: `${s.macchina ?? nomeMacchina(s.host ?? "qui")} non risponde (${String(e?.message ?? e).slice(0, 120)})` };
  }
}

// La scheda nuova che aggancia una sessione: nello spazio del progetto (lo stesso della barra) o nello
// spazio "Volta" per le sessioni senza progetto. Mai una scheda ritrovata per nome: quella la cerca
// apriSessione, per etichetta e per argv.
export function aggancia(s, argv) {
  const nome = titolo(s).slice(0, 40);
  const nomeSpazio = s.progetto ? slug(s.progetto) : "Volta";
  const sp = spaces().find((x) => !x.machine && slug(x.name) === slug(nomeSpazio));
  const cartella = s.questa && s.cartella ? s.cartella : home();
  if (sp) {
    run("space.select", { id: sp.id });
    run("tab.new", { name: nome, space: sp.id, folder: cartella, argv: argvScheda(argv) });
  } else run("space.new", { name: nomeSpazio, folder: cartella, machine: "", tab: nome, argv: argvScheda(argv) });
}

// Quanto si aspetta prima di guardare se claude attach è rimasto in piedi nella scheda (veglia).
const VEGLIA = 6000;

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
    return { come: "davanti" };
  }
  if (schede.length) { scheda = schede[0]; rilancia = true; }
  let riavviata = false;
  if (!pronta) {
    const a = await prepara(s, s.stato === "errore");
    if (a.errore) return { errore: `Non la apro: ${a.errore}.` };
    // conta il riavvio chiesto, non la risposta: la veglia non deve mai riavviare due volte
    riavviata = s.stato === "errore";
  }
  if (rilancia) {
    mostra(scheda.address);
    const r = await hc(["send", scheda.address, comando(argvScheda(argv))]);
    if (r.code !== 0) return { errore: "Non riesco a rilanciare Claude nella sua scheda: chiudi la scheda e riprova." };
    await etichetta(scheda, s);
  } else {
    aggancia(s, argv);
    // run() non dice quale terminale ha creato: lo si cerca per argv appena Herdr lo elenca.
    for (let i = 0; i < 10 && !scheda; i++) { scheda = schedeDi(s)[0] ?? null; if (!scheda) await pausa(400); }
    if (scheda) await etichetta(scheda, s);
  }
  return { come: rilancia ? "rilanciata" : "nuova", riavviata, veglia: scheda ? veglia(s, argv, scheda.address, riavviata) : Promise.resolve({}) };
}

// Perché Claude è uscito dalla scheda: lo dice lo schermo della scheda (motivoUscita di sessioni.js).
async function perche(s, indirizzo) {
  try {
    const r = await hc(["read", indirizzo]);
    return r.code === 0 ? motivoUscita(r.stdout, s) : null;
  } catch {
    return null;
  }
}

// Se Claude è uscito, la riga dice il motivo letto nella scheda. Una causa che sta nella macchina o
// nella connessione (`fermo`) non si riprova: il riavvio non la toglie, e terrebbe la riga occupata.
async function veglia(s, argv, indirizzo, riavviata) {
  await pausa(VEGLIA);
  if (!(await nuda(indirizzo))) return {};
  const fallita = (m) => ({ errore: m?.testo ?? "Claude non resta aperto in questa sessione: riprova, oppure eliminala da Altro." });
  const m = await perche(s, indirizzo);
  if (riavviata || m?.fermo) return fallita(m);
  const a = await prepara(s, true);
  if (a.errore) return { errore: `Claude non si riapre: ${a.errore}.` };
  const r = await hc(["send", indirizzo, comando(argvScheda(argv))]);
  if (r.code !== 0) return fallita(m);
  await pausa(VEGLIA);
  return (await nuda(indirizzo)) ? fallita((await perche(s, indirizzo)) ?? m) : { riavviata: true };
}

// Il nome di una macchina di "Nasce su" per le persone: "qui" è questa macchina.
export const nomeMacchina = (m) => (m === "qui" ? "questa macchina" : m);

// Una sessione nuova in background (volta_sonda.py nasci), su questa macchina o su un'altra, agganciata
// qui in una scheda: continua a girare anche chiusa la scheda, e Volta la apre da ogni macchina. Anche
// qui nasce in background (#5072): lo stato in barra lo dà Volta (statoSpazio).
// Durante la nascita shared arturo.nascita dice dove e da quando, per la riga "Nasce su" (inNascita).
// `copia` ({ verbo: "duplica" | "fork", sessionId, cartella, titolo }) è il Duplica o il Fork di una
// sessione (#5291): stessa strada e stesse attese, coi verbi duplica e fork della sonda. Torna { ok } o
// { errore }; l'errore di una copia lo mostra la riga di Volta, ogni errore di una nascita un avviso
// (chi chiama non guarda l'esito: il clic nella barra, Lavoraci, i comandi).
async function nasciSu(macchina, prompt, progetto, nomeScheda = null, copia = null) {
  const dico = (titolo, errore, level = "error") => {
    if (!copia) notify({ title: titolo, body: errore, level });
    return { errore };
  };
  if (inNascita()) return dico("Sta già nascendo un'altra sessione", "sta già nascendo un'altra sessione: riprova fra poco", "warning");
  const da = Date.now();
  setShared("arturo.nascita", { macchina, da });
  try {
    const c = await config();
    const args = [c.volta, copia ? copia.verbo : "nasci", macchina, ...(copia?.verbo === "fork" ? [copia.sessionId] : []),
      ...(progetto ? ["--progetto", progetto] : []), ...(copia?.cartella ? ["--cartella", copia.cartella] : []),
      ...(copia?.titolo ? ["--titolo", copia.titolo] : []), ...(prompt ? ["--", prompt] : [])];
    let nata = {};
    try {
      // 6 minuti: le attese di volta_sonda.py (macchine 15 s, servizio 120 s, nascita 180 s) più un margine,
      // così Volta non dice "non risponde" mentre la sessione sta ancora nascendo (#5214)
      nata = esito(await exec(c.arturo[0], args, { timeout: 360000 }));
    } catch {
      nata = { errore: `${nomeMacchina(macchina)} non ha risposto in 6 minuti: se la sessione è nata, la trovi fra le sessioni` };
    }
    if (nata.attach?.length) {
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

// Quanto dura al massimo una nascita: i 6 minuti di attesa della sonda più l'aggancio della scheda.
const NASCITA_MAX = 420000;

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

// Chiude le schede che agganciano la sessione: la prima metà di "Chiudi", prima di claude stop. La
// scheda intera se dentro c'è solo quel terminale, altrimenti il solo terminale: i pannelli accanto
// restano. Torna quante ne ha chiuse.
export function chiudiSchede(s) {
  let n = 0;
  for (const t of schedeDi(s)) {
    const p = panes().find((x) => x.terminal === t.address);
    if (!p) continue;
    segnaTolto(t.address);
    if (panes().filter((x) => x.tab === p.tab).length === 1) run("tab.close", { id: p.tab });
    else run("terminal.kill", { terminal: t.address });
    n++;
  }
  return n;
}

// Rinomina e Cambia progetto (#5292): volta_sonda.py rinomina o progetto scrive il nome o il progetto
// sulla macchina della sessione, con fonte "persona". Vuole il sessionId intero: i file della cache
// portano quello. `opzioni`: ["--portato"] quando Claude Code ha già il nome. { ok } oppure { errore }.
export async function cambiaSessione(s, cosa, valore, opzioni = []) {
  const c = await config();
  try {
    const r = await exec(c.arturo[0], [c.volta, cosa === "nome" ? "rinomina" : "progetto", s.host ?? "qui", s.sessionId, ...opzioni,
      ...(valore ? ["--", valore] : [])], { timeout: 90000 });
    return esito(r);
  } catch (e) {
    return { errore: `${s.macchina ?? nomeMacchina(s.host ?? "qui")} non risponde (${String(e?.message ?? e).slice(0, 120)})` };
  }
}

// I terminali di questa finestra che mostrano la sessione: le schede che la agganciano e, per
// un'interattiva partita in una scheda di Herdr su questa macchina, quella scheda.
function terminaliDi(s) {
  const l = schedeDi(s).map((t) => t.address);
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

// Scrive /rename nella prima scheda buona della sessione. Torna true se l'ha scritto.
async function scriviNome(s, nome) {
  let scritto = false;
  // la prima scheda buona: una sessione può averne più d'una, e una può essere rimasta con la shell
  for (const a of terminaliDi(s)) {
    if (await nuda(a)) continue;
    try {
      const schermo = await hc(["read", a]);
      if (schermo.code !== 0 || !casellaVuota(schermo.stdout)) continue;
      const r = await hc(["send", a, `/rename ${nome}`]);
      scritto = r.code === 0;
    } catch { /* si prova la scheda dopo */ }
    break;
  }
  return scritto;
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

// Le cartelle della base dei progetti, dalla più recente.
export async function cartelle() {
  try {
    const c = await config();
    const r = await exec("sh", ["-c", 'cd "$1" 2>/dev/null && ls -td -- */ 2>/dev/null', "sh", c.base], {});
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
export async function azioneSessione(s, verbo) {
  const c = await config();
  try {
    const r = await exec(c.arturo[0], [c.volta, "azione", s.host, verbo, s.id], { timeout: verbo === "respawn" ? 210000 : 90000 });
    return esito(r);
  } catch (e) {
    return { errore: `${s.macchina} non risponde (${String(e?.message ?? e).slice(0, 120)})` };
  }
}
