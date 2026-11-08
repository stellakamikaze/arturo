// I dati di Arturo per Herdr: configurazione, todo, progetti e le azioni che aprono Claude.
// Tutte le parti del mod leggono da qui, così dicono le stesse cose con le stesse parole.

import { exec, readTextFile, appHome, home, hc, spaces, agents, run, notify } from "herdr";

// arturo.json nella cartella di Herdr: lo scrive installa-herdr.sh.
// { "arturo": ["python3", "/Users/x/.claude/bin/arturo"], "base": "/Users/x/Documents/ClaudeCode" }
export async function config() {
  let c = {};
  try {
    c = JSON.parse((await readTextFile(`${appHome()}/arturo.json`)) ?? "{}");
  } catch {
    c = {};
  }
  return {
    arturo: Array.isArray(c.arturo) && c.arturo.length ? c.arturo : ["python3", `${home()}/.claude/bin/arturo`],
    base: typeof c.base === "string" && c.base ? c.base : `${home()}/Documents/ClaudeCode`,
  };
}

// arturo todo <args>: { ok, json, errore }. Mai un'eccezione verso l'interfaccia.
export async function todo(args) {
  try {
    const c = await config();
    const [cmd, ...pre] = c.arturo;
    const r = await exec(cmd, [...pre, "todo", ...args], { cwd: c.base });
    if (r.code !== 0) return { ok: false, errore: prima(r.stderr) || prima(r.stdout) || `uscita ${r.code}`, codice: r.code };
    if (!args.includes("--json")) return { ok: true, testo: prima(r.stdout) };
    return { ok: true, json: JSON.parse(r.stdout) };
  } catch (e) {
    return { ok: false, errore: "Non riesco a leggere i todo di Arturo." };
  }
}

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
  s = s.replace(/\s+[~\/][\w.\/-]+/g, "");
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
export function progetti(vista) {
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
  for (const s of spaces()) {
    if (s.machine || !s.named) continue;
    const k = slug(s.name);
    if (!per.has(k)) per.set(k, { chiave: k, nome: s.name, titolo: bello(s.name), categoria: "", tu: 0, decidi: 0, io: 0, fermo: 0 });
  }
  const RANGO = { blocked: 5, done: 4, working: 3, idle: 2 };
  return [...per.values()]
    .map((v) => ({ ...v, stato: spazio(v.chiave)?.status ?? null, aperto: Boolean(spazio(v.chiave)) }))
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
  const cat = [...per.entries()].sort((a, b) => a[1].length === b[1].length ? a[0].localeCompare(b[0]) : b[1].length - a[1].length);
  if (cat.length === 1 && !adesso.length) out.push({ titolo: "I tuoi progetti", progetti: cat[0][1] });
  else for (const [c, l] of cat) out.push({ titolo: c, progetti: l });
  return out;
}

// Apre il progetto: lo spazio se c'è, altrimenti una sessione nuova che parte da /inizio.
// `todoScelto` ({id, titolo}) porta Claude direttamente su quel todo.
export async function apri(nome, todoScelto) {
  const c = await config();
  nome = slug(nome);
  const s = spazio(nome);
  if (s) {
    run("space.select", { id: s.id });
    if (!todoScelto) return;
    const a = agents().find((x) => x.space === s.id);
    if (!a) return notify({ title: "La sessione di questo progetto è chiusa", body: "Chiudi lo spazio e riaprilo dalla barra.", level: "warning" });
    if (a.status === "blocked") return notify({ title: "Claude aspetta una tua risposta", body: "Rispondi nella sessione, poi riprova.", level: "warning" });
    const r = await hc(["send", a.address, `Lavoriamo sul todo #${todoScelto.id}: ${todoScelto.titolo}`]);
    if (r.code !== 0) notify({ title: "Non sono riuscito a scrivere a Claude", body: prima(r.stderr), level: "error" });
    return;
  }
  const prompt = todoScelto ? `/inizio ${nome} -- #${todoScelto.id} ${pulito(todoScelto.titolo)}` : `/inizio ${nome}`;
  run("space.new", { name: nome, folder: c.base, machine: "", tab: "Claude", argv: ["claude", prompt] });
}

// Una richiesta nuova, senza progetto: Claude nella cartella dei progetti.
export async function nuova() {
  const c = await config();
  const ora = new Date();
  const hh = String(ora.getHours()).padStart(2, "0");
  const mm = String(ora.getMinutes()).padStart(2, "0");
  run("space.new", { name: `Richiesta delle ${hh}:${mm}`, folder: c.base, machine: "", tab: "Claude", argv: ["claude"] });
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
