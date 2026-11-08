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

// La frase di un progetto: prima la sessione viva, poi i todo.
export function frase(stato, conti) {
  if (stato === "blocked") return { testo: "Claude ti aspetta", colore: "blocked" };
  if (stato === "working") return { testo: "Claude sta lavorando", colore: "working" };
  if (stato === "done") return { testo: "Claude ha finito", colore: "done" };
  if (conti) {
    if (conti.tu) return { testo: `${conti.tu} ${conti.tu > 1 ? "cose" : "cosa"} per te`, colore: "muted" };
    if (conti.decidi) return { testo: `${conti.decidi} da decidere`, colore: "muted" };
    if (conti.scaduti) return { testo: `${conti.scaduti} ${conti.scaduti > 1 ? "scaduti" : "scaduto"}`, colore: "muted" };
    if (conti.io) return { testo: "Va avanti con Claude", colore: "muted" };
    if (conti.fermo) return { testo: "Fermo", colore: "muted" };
  }
  if (stato === "idle") return { testo: "Aperto", colore: "muted" };
  return { testo: "Niente da fare", colore: "dim" };
}

// La vista di tutti i progetti: conti per chi agisce, uniti agli spazi aperti.
export function progetti(vista) {
  const per = new Map();
  const voce = (nome) => {
    const k = slug(nome);
    if (!k) return null;
    if (!per.has(k)) per.set(k, { nome: k, tu: 0, decidi: 0, io: 0, fermo: 0, scaduti: 0, aperti: 0 });
    return per.get(k);
  };
  for (const g of vista?.gruppi ?? []) for (const t of g.todo ?? []) {
    const v = voce(t.progetto);
    if (!v) continue;
    v[g.tipo] = (v[g.tipo] ?? 0) + 1;
    v.aperti++;
    if (typeof t.giorni === "number" && t.giorni < 0) v.scaduti++;
  }
  for (const p of vista?.progetti ?? []) {
    const v = voce(p.nome);
    if (v && p.scaduti) v.scaduti = Math.max(v.scaduti, p.scaduti);
  }
  for (const s of spaces()) if (!s.machine && s.named) voce(s.name);
  const RANGO = { blocked: 5, done: 4, working: 3, idle: 2 };
  const lista = [...per.values()].map((v) => ({ ...v, stato: spazio(v.nome)?.status ?? null, aperto: Boolean(spazio(v.nome)) }));
  lista.sort((a, b) =>
    (RANGO[b.stato] ?? 0) - (RANGO[a.stato] ?? 0) ||
    Number(b.aperto) - Number(a.aperto) ||
    b.tu + b.decidi - (a.tu + a.decidi) ||
    a.nome.localeCompare(b.nome));
  return lista;
}

// Apre il progetto: lo spazio se c'è, altrimenti una sessione nuova che parte da /inizio.
// `todoScelto` ({id, titolo}) porta Claude direttamente su quel todo.
export async function apri(nome, todoScelto) {
  const c = await config();
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
