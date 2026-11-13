// Le tessere di ⌘T senza Herdr: quali tessere, in che ordine, come si muove la tastiera, le iniziali e la
// tinta di un progetto senza immagine. Niente import di Herdr, così il banco le prova con node (casa.js le
// disegna).

// La prima tessera: "Nuova richiesta". ⌘T e Invio fanno quello che faceva ⌘T prima (12/11/2026).
export const NUOVA = { tipo: "nuova", chiave: "", titolo: "Nuova richiesta" };

// Lo stack del layout che tiene il terminale e le tessere, e i suoi due figli (layouts/arturo.json).
export const STACK = "lavoro";
export const TERMINALE = "main";
export const CASA = "casa";

// Il nodo `id` nell'albero del layout vivo (layout() di Herdr), o null.
function nodo(n, id) {
  if (n?.id === id) return n;
  for (const c of n?.children ?? []) { const x = nodo(c, id); if (x) return x; }
  return null;
}

// Il layout ha le tessere: lo stack "lavoro" con il figlio "casa". Un layout fatto a mano o di Herdr non le
// ha, e allora ⌘T apre una sessione nuova, come prima del 12/11/2026 (#5456).
export const haTessere = (lay) => (nodo(lay, STACK)?.children ?? []).some((c) => c?.id === CASA);

// Il layout è noto e non ha le tessere. Prima che Herdr pubblichi il layout, layout() è null: lì si prova lo
// stesso a mostrare le tessere, come prima. layout.select su uno stack che non c'è apre un avviso d'errore.
export const senzaTessere = (lay) => Boolean(lay) && !haTessere(lay);

// Le tessere sono mostrate al posto del terminale: lo stack "lavoro" ha "casa" come figlio attivo. Senza
// `active` lo stack mostra il primo figlio, il terminale.
export const tessereMostrate = (lay) => haTessere(lay) && nodo(lay, STACK).active === CASA;

// Larghezza minima di una tessera e spazio fra le tessere, in px logici: dalla larghezza dell'area
// si ricava quante tessere stanno in una riga, per le frecce su e giù.
export const MIN_W = 190;
export const GAP = 14;

// Le tessere per il filtro `f`: prima "Nuova richiesta", poi i progetti nell'ordine della barra (sessioni
// vive, poi conversazioni aperte, poi per ultima attività). Il filtro cerca nel titolo e nello slug:
// prima chi comincia così, poi chi lo contiene. Con un filtro "Nuova richiesta" resta solo se il filtro
// è vuoto, così Invio apre il primo progetto trovato.
export function tessere(lista, f) {
  const l = Array.isArray(lista) ? lista.filter((p) => p && p.chiave) : [];
  const q = String(f ?? "").trim().toLowerCase();
  if (!q) return [NUOVA, ...l];
  const testo = (p) => `${String(p.titolo ?? "").toLowerCase()} ${p.chiave}`;
  const inizia = (p) => String(p.titolo ?? "").toLowerCase().startsWith(q) || p.chiave.startsWith(q);
  return [...l.filter(inizia), ...l.filter((p) => !inizia(p) && testo(p).includes(q))];
}

// Quante tessere stanno in una riga larga `w` px.
export const colonne = (w) => Math.max(1, Math.floor(((Number(w) || 0) + GAP) / (MIN_W + GAP)));

// La tessera dopo un tasto: frecce a destra e sinistra di una, su e giù di una riga. Fuori dai bordi
// resta dov'è (niente giro: chi tiene premuta la freccia si ferma in fondo).
export function passo(at, tasto, n, col) {
  const c = Math.max(1, col | 0);
  const d = { right: 1, left: -1, down: c, up: -c }[tasto];
  if (d === undefined || n <= 0) return at;
  const dopo = at + d;
  if (dopo < 0) return tasto === "up" ? at : 0;
  if (dopo >= n) return tasto === "down" ? at : n - 1;
  return dopo;
}

// Le iniziali di un progetto senza immagine: due lettere, dalle prime due parole o dalla prima.
export function iniziali(titolo) {
  const parole = String(titolo ?? "").split(/[\s\-_]+/).filter((w) => /[\p{L}\p{N}]/u.test(w));
  if (!parole.length) return "?";
  const prima = (w) => [...w].find((ch) => /[\p{L}\p{N}]/u.test(ch)) ?? "";
  const s = parole.length > 1 ? prima(parole[0]) + prima(parole[1]) : [...parole[0]].filter((ch) => /[\p{L}\p{N}]/u.test(ch)).slice(0, 2).join("");
  return s.toUpperCase() || "?";
}

// La tinta di un progetto senza immagine: sempre la stessa per lo stesso slug, fra blu notte e viola
// spento, così le iniziali stanno fra le immagini senza gridare.
export function tinta(chiave) {
  let h = 0;
  for (const ch of String(chiave ?? "")) h = (h * 31 + ch.codePointAt(0)) >>> 0;
  return hex(200 + (h % 70), 0.38, 0.22);
}

// Un colore HSL (tono in gradi, saturazione e luce da 0 a 1) in #rrggbb, la forma dei colori del tema.
function hex(tono, s, l) {
  const k = (n) => (n + tono / 30) % 12;
  const a = s * Math.min(l, 1 - l);
  const f = (n) => l - a * Math.max(-1, Math.min(k(n) - 3, 9 - k(n), 1));
  return "#" + [f(0), f(8), f(4)].map((x) => Math.round(x * 255).toString(16).padStart(2, "0")).join("");
}

// Il percorso dell'immagine di un progetto, relativo alla cartella dell'app (volta_mod.py la copia lì),
// o null se l'elenco delle immagini arrivate non la nomina.
export function immagine(chiave, arrivate) {
  return chiave && arrivate instanceof Set && arrivate.has(chiave) ? `immagini/${chiave}.webp` : null;
}
