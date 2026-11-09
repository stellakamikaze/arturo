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

// Il progetto a cui va la nota: quello scelto in arturo.json (note_progetto), altrimenti quello aperto.
export const progettoNota = (scelto, aperto) => (scelto || aperto || null);

// { dati, argv } oppure null se il testo è vuoto. argv è null senza progetto: la nota resta nella cartella.
export function nota({ testo, x, y, larghezza, altezza, progetto, cartella, schermo, quando }) {
  const t = String(testo ?? "").replace(/\s+/g, " ").trim();
  if (!t) return null;
  const punto = { x: Math.round(x), y: Math.round(y) };
  const finestra = { larghezza: Math.round(larghezza), altezza: Math.round(altezza) };
  const dati = { versione: 1, quando, testo: t, punto, finestra, progetto: progetto || null,
    schermo: schermo || null, screenshot: "finestra.png" };
  const breve = t.length > 110 ? t.slice(0, 110).replace(/\s+\S*$/, "") + "…" : t;
  const dove = `Punto ${punto.x},${punto.y} su una finestra di ${finestra.larghezza}x${finestra.altezza}` +
    (schermo ? `, schermata ${schermo}` : "") + `. Nota e screenshot in ${cartella}`;
  const argv = progetto
    ? ["aggiungi", "--progetto", progetto, "--chi", "io", "--quando", "oggi", "--note", dove, "--", `Nota sulla finestra: ${breve}`]
    : null;
  return { dati, argv };
}
