// Le note sulla finestra (⌘⇧N): da testo, punto e misura della finestra, il contenuto di nota.json e gli
// argomenti di `arturo todo aggiungi`. Modulo puro, senza herdr: lo usa la parte `nota`, lo prova il banco
// HZ14 con node. La nota diventa una cosa da fare di Claude nel progetto delle note, con l'oggi come quando:
// Claude la trova nel pannello Da fare e a /inizio, e dalle note risale alla cartella con lo screenshot.

const due = (n) => String(n).padStart(2, "0");

// La cartella di una nota: ~/.claude/data/note-finestra/AAAA-MM-GG_HH-MM-SS.
export function cartellaNota(home, d = new Date()) {
  const quando = `${d.getFullYear()}-${due(d.getMonth() + 1)}-${due(d.getDate())}_${due(d.getHours())}-${due(d.getMinutes())}-${due(d.getSeconds())}`;
  return `${home}/.claude/data/note-finestra/${quando}`;
}

// Le misure che servono a regione(), dal layout vivo (layout() di herdr) e dalle misure che le parti riportano
// in shared arturo.misura.<parte>: divisore fra barra e lavoro, padding e gap attorno alla sessione, pannello
// Da fare nascosto. Senza un nodo, valgono i numeri di layouts/arturo.json.
export function misureDaLayout(lay, parti, finestra) {
  const trova = (n, id) => {
    if (n?.id === id) return n;
    for (const c of n?.children ?? []) { const x = trova(c, id); if (x) return x; }
    return null;
  };
  const corpo = trova(lay, "work-body");
  return { ...parti, finestra,
    divisore: lay?.divider?.width ?? 1, padding: corpo?.padding ?? 12, gap: corpo?.gap ?? 12,
    pannello_nascosto: Boolean(trova(lay, "pannello")?.hidden) };
}

// Il benvenuto galleggia in cima alla sessione, 12 px sotto il bordo (herdr-app status: y 78 su main.y 66).
const MARGINE_FLOAT = 12;
const dentro = (p, r) => r && p.x >= r.x && p.x < r.x + r.larghezza && p.y >= r.y && p.y < r.y + r.altezza;
const rett = (x, y, larghezza, altezza) => ({ x, y, larghezza, altezza });

// Su quale parte della finestra cade il punto: { blocco, parte, rettangolo } coi nomi di layouts/arturo.json,
// oppure null se le misure mancano o non tornano con la finestra (la nota tiene allora solo terminale e cwd).
// A sinistra marchio, progetti e piede; a destra testata, sessione (main) col benvenuto sopra, Da fare
// (pannello) e stato. Padding e gap attorno alla sessione vanno alla parte più vicina. Misure provate
// nell'istanza di prova il 10/11/2026: 292+1+1147 = 1440 e 54+690+156 = 900, rettangoli uguali allo scatto.
export function regione(punto, m) {
  const f = m?.finestra;
  const { marchio, barra, piede, testata, stato, todo } = m ?? {};
  if (!f || !marchio || !barra || !piede || !testata || !stato || (!todo && !m.pannello_nascosto)) return null;
  const W = f.larghezza, H = f.altezza;
  const S = barra.larghezza;
  // Misure vecchie (finestra cambiata dopo l'ultimo giro delle parti): meglio nessuna regione che una sbagliata.
  if (Math.abs(marchio.altezza + barra.altezza + piede.altezza - H) > 2) return null;
  if (Math.abs(S + (m.divisore ?? 1) + testata.larghezza - W) > 2) return null;
  const p = { x: punto.x, y: punto.y };
  if (p.x < 0 || p.y < 0 || p.x >= W || p.y >= H) return null;
  const x0 = W - testata.larghezza;
  const pad = m.padding ?? 12, gap = m.gap ?? 12;
  const corpoY = testata.altezza, corpoH = H - testata.altezza - stato.altezza;
  const pannelloW = m.pannello_nascosto ? 0 : todo.larghezza;
  const mainW = testata.larghezza - 2 * pad - (pannelloW ? pannelloW + gap : 0);
  const main = rett(x0 + pad, corpoY + pad, mainW, corpoH - 2 * pad);
  const b = m.benvenuto;
  const benvenuto = b && b.larghezza > 0 && b.altezza > 0
    ? rett(main.x + Math.round((main.larghezza - b.larghezza) / 2), main.y + MARGINE_FLOAT, b.larghezza, b.altezza) : null;
  const blocchi = [
    ["marchio", "marchio", rett(0, 0, S, marchio.altezza)],
    ["progetti", "barra", rett(0, marchio.altezza, S, barra.altezza)],
    ["piede", "piede", rett(0, H - piede.altezza, S, piede.altezza)],
    ["testata", "testata", rett(x0, 0, testata.larghezza, testata.altezza)],
    ["stato", "stato", rett(x0, H - stato.altezza, testata.larghezza, stato.altezza)],
    ["benvenuto", "benvenuto", benvenuto],
    ["main", null, main],
    ["pannello", "todo", pannelloW ? rett(W - pad - pannelloW, main.y, pannelloW, main.altezza) : null],
  ];
  for (const [blocco, parte, r] of blocchi) if (dentro(p, r)) return { blocco, parte, rettangolo: r };
  // Il divisore va alla barra; padding e gap del corpo alla sessione o al pannello, il più vicino.
  if (p.x < x0) return { blocco: "progetti", parte: "barra", rettangolo: blocchi[1][2] };
  const pannello = blocchi[7][2];
  if (pannello && p.x >= main.x + main.larghezza + gap / 2) return { blocco: "pannello", parte: "todo", rettangolo: pannello };
  return { blocco: "main", parte: null, rettangolo: main };
}

// Il terminale sotto la nota, quando il punto cade sulla sessione: le ultime `n` righe non vuote del testo.
export function ultimeRighe(testo, n = 40) {
  const righe = String(testo ?? "").replace(/\r/g, "").split("\n");
  while (righe.length && !righe[righe.length - 1].trim()) righe.pop();
  return righe.slice(-n).join("\n");
}

// Il progetto a cui va la nota: quello scelto in arturo.json (note_progetto), altrimenti quello aperto.
export const progettoNota = (scelto, aperto) => (scelto || aperto || null);

// { dati, argv } oppure null se il testo è vuoto. argv è null senza progetto: la nota resta nella cartella.
export function nota({ testo, x, y, larghezza, altezza, progetto, cartella, schermo, quando, dove }) {
  const t = String(testo ?? "").replace(/\s+/g, " ").trim();
  if (!t) return null;
  const punto = { x: Math.round(x), y: Math.round(y) };
  const finestra = { larghezza: Math.round(larghezza), altezza: Math.round(altezza) };
  const dati = { versione: 1, quando, testo: t, punto, finestra, progetto: progetto || null,
    schermo: schermo || null, dove: dove || null, screenshot: "finestra.png" };
  const breve = t.length > 110 ? t.slice(0, 110).replace(/\s+\S*$/, "") + "…" : t;
  const riga = `Punto ${punto.x},${punto.y} su una finestra di ${finestra.larghezza}x${finestra.altezza}` +
    (schermo ? `, schermata ${schermo}` : "") +
    (dove?.blocco ? `, parte ${dove.blocco}` : "") + (dove?.cwd ? ` (terminale in ${dove.cwd})` : "") +
    `. Nota e screenshot in ${cartella}`;
  const argv = progetto
    ? ["aggiungi", "--progetto", progetto, "--chi", "io", "--quando", "oggi", "--note", riga, "--", `Nota sulla finestra: ${breve}`]
    : null;
  return { dati, argv };
}
