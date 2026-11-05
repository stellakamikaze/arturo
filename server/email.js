// L'impaginazione delle email del server (5/11/2026): segnalazione, config rotta, recap del mattino e riepilogo del
// lunedì. Prima erano solo testo, un muro di righe allineate a spazi che il telefono spezzava a caso. Ogni email ha la
// stessa forma: riga piccola "Arturo · giorno", titolo con l'esito in una frase, corpo a card e tabelle, un bottone
// con l'azione, piede attenuato con il perché arriva. CSS in linea, larghezza massima 600 px, colori della landing.
// Il testo semplice resta accanto, nella parte text/plain (mime in logica.js).
//
// Qui non entra mai il testo di chi scrive: le funzioni ricevono solo numeri, valori di elenchi chiusi e id corti.
// esc() protegge comunque ogni valore, perché un nome di installazione arriva da una variabile del Worker.

const INCHIOSTRO = "#0b0d10";
const GRAFITE = "#2a2e35";
const CENERE = "#59606a";
const FILETTO = "#d6d8d4";
const CARTA = "#f5f5f3";
const CARTA_2 = "#ebebe8";
const AZIONE = "#0b5fff";
const VELO = "#e3efff";
const SANS = "-apple-system, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif";
const MONO = "ui-monospace, 'SF Mono', Menlo, Consolas, monospace";

export const esc = (v) => String(v ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);

// Un pezzo di HTML già pronto, che le funzioni sotto non riescapano.
export const crudo = (html) => ({ html });
const cella = (v) => (v && typeof v === "object" && "html" in v ? v.html : esc(v));

export function bottone(href, etichetta) {
  return `<a href="${esc(href)}" style="display:inline-block;padding:11px 18px;background:${AZIONE};border-radius:6px;` +
    `font-family:${SANS};font-size:15px;font-weight:600;color:#ffffff;text-decoration:none">${esc(etichetta)}</a>`;
}

export function codice(v) {
  return crudo(`<span style="font-family:${MONO};font-size:13px">${esc(v)}</span>`);
}

// Le cifre in testa: una casella per numero, con l'etichetta sotto. Si va a capo da sole sul telefono.
export function cifre(voci) {
  const caselle = voci.map((v) => `<td valign="top" style="padding:0 8px 8px 0;width:${Math.floor(100 / voci.length)}%">` +
    `<div style="padding:12px 14px;background:${CARTA};border:1px solid ${FILETTO};border-radius:6px">` +
    `<div style="font-family:${SANS};font-size:26px;font-weight:700;line-height:1.1;color:${INCHIOSTRO}">${esc(v.valore)}</div>` +
    `<div style="padding-top:4px;font-family:${SANS};font-size:13px;line-height:1.35;color:${CENERE}">${cella(v.etichetta)}</div>` +
    "</div></td>").join("");
  return `<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0"><tr>${caselle}</tr></table>`;
}

// Una tabella: intestazione, righe di celle (testo o crudo()), le colonne numeriche allineate a destra.
export function tabella(colonne, righe, { numeriche = [] } = {}) {
  const allinea = (i) => (numeriche.includes(i) ? "right" : "left");
  const testa = colonne.map((c, i) => `<th align="${allinea(i)}" style="padding:6px 8px;border-bottom:1px solid ${GRAFITE};` +
    `font-family:${SANS};font-size:12px;font-weight:600;color:${CENERE};text-transform:uppercase;letter-spacing:0.03em">${esc(c)}</th>`).join("");
  const corpo = righe.map((r) => `<tr>${r.map((v, i) => `<td align="${allinea(i)}" valign="top" style="padding:7px 8px;` +
    `border-bottom:1px solid ${FILETTO};font-family:${SANS};font-size:14px;line-height:1.4;color:${INCHIOSTRO}">${cella(v)}</td>`).join("")}</tr>`).join("");
  return `<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="border-collapse:collapse">` +
    `<tr>${testa}</tr>${corpo}</table>`;
}

// Una card: titolo piccolo e coppie etichetta-valore, per la segnalazione e la config rotta.
export function scheda(coppie) {
  const righe = coppie.map(([k, v]) => `<tr><td valign="top" style="padding:6px 12px 6px 0;width:110px;font-family:${SANS};font-size:13px;` +
    `color:${CENERE}">${esc(k)}</td><td style="padding:6px 0;font-family:${SANS};font-size:15px;line-height:1.4;color:${INCHIOSTRO}">${cella(v)}</td></tr>`).join("");
  return `<div style="padding:12px 16px;background:${CARTA};border:1px solid ${FILETTO};border-radius:6px">` +
    `<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0">${righe}</table></div>`;
}

export function elenco(voci) {
  return `<ul style="margin:0;padding:0 0 0 18px">${voci.map((v) => `<li style="padding:3px 0;font-family:${SANS};font-size:14px;` +
    `line-height:1.45;color:${INCHIOSTRO}">${cella(v)}</li>`).join("")}</ul>`;
}

export function paragrafo(v, { attenuato = false } = {}) {
  return `<p style="margin:0;font-family:${SANS};font-size:${attenuato ? 13 : 15}px;line-height:1.5;color:${attenuato ? CENERE : INCHIOSTRO}">${cella(v)}</p>`;
}

// Una sezione: titolo, nota facoltativa, contenuto. Il riquadro "da fare" ha il fondo azzurro della landing.
export function sezione(titolo, contenuto, { nota = "", evidenza = false } = {}) {
  const fondo = evidenza ? `background:${VELO};padding:14px 16px;border-radius:6px;` : "";
  return `<tr><td style="padding:22px 0 0"><div style="${fondo}">` +
    `<div style="padding-bottom:${nota ? 2 : 8}px;font-family:${SANS};font-size:17px;font-weight:700;line-height:1.3;color:${INCHIOSTRO}">${esc(titolo)}</div>` +
    (nota ? `<div style="padding-bottom:8px;font-family:${SANS};font-size:13px;line-height:1.4;color:${CENERE}">${cella(nota)}</div>` : "") +
    `${contenuto}</div></td></tr>`;
}

// La pagina intera. `testa` è la riga piccola ("Arturo · 4/11"), `titolo` l'esito in una frase, `blocchi` le
// sezioni (già <tr>), `azione` il bottone principale, `piede` le righe attenuate in fondo.
export function pagina({ testa, titolo, apertura = "", blocchi = [], azione = null, piede = [], anteprima = "" }) {
  return `<!doctype html>
<html lang="it"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="color-scheme" content="light only"><title>${esc(titolo)}</title></head>
<body style="margin:0;padding:0;background:${CARTA_2}">
<div style="display:none;max-height:0;overflow:hidden">${esc(anteprima || apertura || titolo)}</div>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="background:${CARTA_2}"><tr><td align="center" style="padding:20px 12px">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="max-width:600px;background:#ffffff;border:1px solid ${FILETTO};border-radius:8px">
<tr><td style="padding:22px 22px 0">
<div style="font-family:${SANS};font-size:12px;font-weight:600;letter-spacing:0.04em;text-transform:uppercase;color:${CENERE}">${esc(testa)}</div>
<div style="padding-top:8px;font-family:${SANS};font-size:24px;font-weight:700;line-height:1.2;color:${INCHIOSTRO}">${esc(titolo)}</div>
${apertura ? `<div style="padding-top:10px;font-family:${SANS};font-size:15px;line-height:1.5;color:${GRAFITE}">${cella(apertura)}</div>` : ""}
</td></tr>
<tr><td style="padding:0 22px"><table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0">${blocchi.join("")}</table></td></tr>
${azione ? `<tr><td style="padding:24px 22px 0">${bottone(azione.href, azione.etichetta)}</td></tr>` : ""}
<tr><td style="padding:24px 22px 22px"><div style="border-top:1px solid ${FILETTO};padding-top:12px;font-family:${SANS};font-size:12px;line-height:1.5;color:${CENERE}">${piede.map(esc).join("<br>")}</div></td></tr>
</table></td></tr></table>
</body></html>`;
}
