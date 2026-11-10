// I dati di Arturo per Herdr: configurazione, todo, progetti e le azioni che aprono Claude.
// Tutte le parti del mod leggono da qui, così dicono le stesse cose con le stesse parole.

import { exec, readTextFile, appHome, home, hc, spaces, agents, run, notify, shared, setShared, terminals, panes } from "herdr";
import { titolo, agganciata } from "./sessioni.js";

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
  };
}

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

// Lo slug come lo fa Arturo: minuscole, lettere, numeri e trattini.
export const slug = (s) => (s ?? "").toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, "").replace(/[^a-z0-9-]+/g, "-").replace(/^-+|-+$/g, "");

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
  if (stato === "idle") return { testo: "Conversazione aperta", colore: "muted" };
  return { testo: "Niente da fare", colore: "dim" };
}

// La chiave di un progetto: lo slug per /inizio e per lo spazio di Herdr, altrimenti il nome.
export const chiave = (p) => slug(p.slug || p.nome);

const URGENZA = { "a rischio": 0, "chiede te": 1, "fermo": 3, "va": 2 };

// Tutti i progetti: la vista di Arturo (titolo, categoria, riga), i conti per chi agisce
// e gli spazi aperti. Ogni voce: { chiave, titolo, categoria, riga, tu, decidi, io, fermo, stato, aperto }.
export function progetti(vista, extra = {}) {
  const per = new Map();
  const conti = new Map();
  for (const g of vista?.gruppi ?? []) for (const t of g.todo ?? []) {
    const c = conti.get(t.progetto) ?? { tu: 0, decidi: 0, io: 0, fermo: 0 };
    c[g.tipo] = (c[g.tipo] ?? 0) + 1;
    conti.set(t.progetto, c);
  }
  for (const p of vista?.progetti ?? []) {
    const k = chiave(p);
    if (!k || per.has(k)) continue;
    per.set(k, { ...p, ...(conti.get(p.nome) ?? { tu: 0, decidi: 0, io: 0, fermo: 0 }), chiave: k, titolo: bello(p), categoria: p.categoria || "" });
  }
  // Le cartelle della base dei progetti senza todo: ci sono, anche se Arturo non ne sa ancora niente.
  const conCategorie = [...per.values()].some((v) => v.categoria);
  for (const nome of extra.cartelle ?? []) {
    const k = slug(nome);
    if (!k || per.has(k)) continue;
    const st = extra.stati?.[nome] ?? extra.stati?.[k];
    per.set(k, { chiave: k, nome, titolo: bello(nome), categoria: conCategorie ? "Altre cartelle" : "", riga: st?.riga ?? "", calcolato: !st?.riga, tu: 0, decidi: 0, io: 0, fermo: 0, cartella: true });
  }
  for (const s of spaces()) {
    if (s.machine || !s.named) continue;
    const k = slug(s.name);
    if (!per.has(k)) per.set(k, { chiave: k, nome: s.name, titolo: bello(s.name), categoria: "", tu: 0, decidi: 0, io: 0, fermo: 0 });
  }
  const RANGO = { blocked: 5, done: 4, working: 3, idle: 2 };
  return [...per.values()]
    .map((v) => ({ ...v, stato: statoSpazio(spazio(v.chiave)), aperto: Boolean(spazio(v.chiave)) }))
    .sort((a, b) => (RANGO[b.stato] ?? 0) - (RANGO[a.stato] ?? 0) || Number(b.aperto) - Number(a.aperto)
      || (URGENZA[a.parola] ?? 2) - (URGENZA[b.parola] ?? 2) || b.tu + b.decidi - (a.tu + a.decidi) || a.titolo.localeCompare(b.titolo));
}

// I progetti in sezioni: "Adesso" (conversazioni aperte), poi le categorie della fonte.
export function sezioni(lista) {
  const adesso = lista.filter((p) => p.aperto);
  const resto = lista.filter((p) => !p.aperto);
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

// Le richieste da imparare: i pulsanti del benvenuto e della finestra "Cosa posso chiedere".
// dove: "nuova" apre sempre una conversazione nuova; "qui" scrive nella conversazione aperta,
// e senza conversazione ne apre una; "apri" apre la finestra dei progetti.
export const SUGGERIMENTI = [
  { id: "trova", titolo: "Trova i miei progetti", testo: "Claude cerca sul computer le cartelle di lavoro e te le propone come progetti.",
    prompt: "Trova i miei progetti sul computer e proponimeli. Segui {radice}/shared/volta-celeste/trova-progetti.md: la cartella di Arturo è {radice}.", dove: "nuova" },
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

// La scheda che aggancia una sessione: se c'è già la si porta davanti, altrimenti nasce nello spazio del
// progetto (lo stesso della barra) o nello spazio "Volta" per le sessioni senza progetto. La usano il
// clic su una sessione di Volta e la nascita su un'altra macchina.
export function aggancia(s, argv) {
  const nome = titolo(s).slice(0, 40);
  const gia = terminals().find((x) => agganciata(x.argv, s));
  if (gia) {
    const p = panes().find((x) => x.terminal === gia.address);
    const sp = p && spaces().find((x) => x.tabs.some((tb) => tb.id === p.tab));
    if (sp) { run("space.select", { id: sp.id }); run("tab.select", { id: p.tab }); }
    run("pane.focus", { terminal: gia.address });
    return;
  }
  const nomeSpazio = s.progetto ? slug(s.progetto) : "Volta";
  const sp = spaces().find((x) => !x.machine && slug(x.name) === slug(nomeSpazio));
  const cartella = s.questa && s.cartella ? s.cartella : home();
  if (sp) {
    const tab = sp.tabs.find((tb) => tb.name === nome);
    run("space.select", { id: sp.id });
    if (tab) return run("tab.select", { id: tab.id });
    run("tab.new", { name: nome, space: sp.id, folder: cartella, argv });
  } else run("space.new", { name: nomeSpazio, folder: cartella, machine: "", tab: nome, argv });
}

// Il nome di una macchina di "Nasce su" per le persone: "qui" è questa macchina.
export const nomeMacchina = (m) => (m === "qui" ? "questa macchina" : m);

// Una sessione nuova in background (volta_sonda.py nasci), su questa macchina o su un'altra, agganciata
// qui in una scheda: continua a girare anche chiusa la scheda, e Volta la apre da ogni macchina. Anche
// qui nasce in background (#5072): lo stato in barra lo dà Volta (statoSpazio).
// Durante la nascita shared arturo.nascita dice dove, per la riga "Nasce su".
async function nasciSu(macchina, prompt, progetto) {
  if (shared("arturo.nascita")) return;
  setShared("arturo.nascita", macchina);
  try {
    const c = await config();
    const args = [c.volta, "nasci", macchina,
      ...(progetto ? ["--progetto", progetto] : []), ...(prompt ? ["--", prompt] : [])];
    let esito = {};
    try {
      // 6 minuti: le attese di volta_sonda.py (macchine 15 s, servizio 120 s, nascita 180 s) più un margine,
      // così Volta non dice "non risponde" mentre la sessione sta ancora nascendo (#5214)
      const r = await exec(c.arturo[0], args, { timeout: 360000 });
      esito = JSON.parse((r.stdout || "").trim().split("\n").pop() || "{}");
    } catch {
      esito = { errore: `${nomeMacchina(macchina)} non ha risposto in 6 minuti: se la sessione è nata, la trovi fra le sessioni` };
    }
    if (esito.attach?.length) {
      const nome = progetto ?? (prompt ? pulito(prompt) : `Richiesta su ${nomeMacchina(macchina)}`);
      // La scheda parte dalla home anche qui: claude attach non ha bisogno della cartella della sessione.
      aggancia({ id: esito.id, sessionId: esito.sessionId, nome, progetto, questa: macchina === "qui" }, esito.attach);
    } else notify({ title: `La sessione non nasce su ${nomeMacchina(macchina)}`, body: esito.errore ?? "Nessuna risposta.", level: "error" });
  } finally {
    setShared("arturo.nascita", null);
  }
}

// Come bin/sessione.py: niente caratteri che rompono il prompt.
const pulito = (t) => (t ?? "").replace(/[`$"\\\n\r]/g, " ").replace(/\s+/g, " ").trim().slice(0, 160);

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
    const riga = (r.stdout || "").trim().split("\n").pop() || "{}";
    return JSON.parse(riga);
  } catch (e) {
    return { errore: `${s.macchina} non risponde (${String(e?.message ?? e).slice(0, 120)})` };
  }
}
