// Il contesto di un progetto, come lo legge /inizio (Federico, 12/11/2026: "una sorta di back-end del
// catalogo dei progetti che mi permette di vedere come è formato il contesto"). I dati li dà
// `arturo contesto <slug> --json`: le fonti nell'ordine in cui Claude le legge, ognuna col suo file, la
// data, il peso. Qui solo il conto e le parole: niente Herdr, così il banco lo prova con node.

// Circa quattro caratteri per token, in italiano un po' meno: basta a dire "pesa poco" o "pesa tanto".
export const CARATTERI_PER_TOKEN = 3.5;

// "3.200 caratteri, circa 900 token" (numeri all'italiana, col punto delle migliaia).
export function peso(caratteri) {
  const n = Math.max(0, Math.round(Number(caratteri) || 0));
  const fmt = (x) => String(x).replace(/\B(?=(\d{3})+(?!\d))/g, ".");
  if (!n) return "vuoto";
  const tok = Math.max(1, Math.round(n / CARATTERI_PER_TOKEN / 10) * 10);
  return `${fmt(n)} caratteri, circa ${fmt(tok)} token`;
}

// Da quanto è stata cambiata una fonte: "oggi", "ieri", "3 giorni fa", "il 4/11".
export function quando(iso, ora = Date.now()) {
  const t = Date.parse(iso ?? "");
  if (!Number.isFinite(t)) return "";
  const g = Math.floor((new Date(ora).setHours(0, 0, 0, 0) - new Date(t).setHours(0, 0, 0, 0)) / 86400000);
  if (g <= 0) return "oggi";
  if (g === 1) return "ieri";
  if (g < 7) return `${g} giorni fa`;
  const d = new Date(t);
  return `il ${d.getDate()}/${d.getMonth() + 1}`;
}

// Le righe della finestra dal JSON di arturo contesto: { titolo, totale, fonti: [{ id, titolo, perche,
// percorso, dettaglio, anteprima, presente }], avvisi }. Le fonti assenti restano, in fondo, per dire
// cosa manca (un progetto senza CLAUDE.md, senza handoff); null se il JSON non è quello atteso.
export function vistaContesto(j, ora = Date.now()) {
  if (!j || typeof j !== "object" || !Array.isArray(j.fonti)) return null;
  const fonti = j.fonti.filter((f) => f && typeof f === "object").map((f, i) => {
    const presente = f.presente !== false;
    const pezzi = presente ? [quando(f.data, ora), peso(f.caratteri)].filter(Boolean) : ["manca"];
    if (presente && Number(f.voci) > 0) pezzi.unshift(`${f.voci} ${f.voci === 1 ? "voce" : "voci"}`);
    return { id: String(f.id ?? i), titolo: String(f.titolo ?? f.id ?? "Fonte"), perche: String(f.perche ?? ""),
      percorso: presente && f.percorso ? String(f.percorso) : null, dettaglio: pezzi.join(" · "),
      anteprima: presente && Array.isArray(f.anteprima) ? f.anteprima.map(String).slice(0, 6) : [],
      presente, caratteri: presente ? Number(f.caratteri) || 0 : 0 };
  });
  const ordinate = fonti.filter((f) => f.presente).concat(fonti.filter((f) => !f.presente));
  const totale = ordinate.reduce((a, f) => a + f.caratteri, 0);
  const p = j.progetto ?? {};
  return { titolo: String(p.titolo ?? p.slug ?? "Progetto"), slug: String(p.slug ?? ""),
    totale: peso(totale), fonti: ordinate, avvisi: Array.isArray(j.avvisi) ? j.avvisi.map(String) : [] };
}
