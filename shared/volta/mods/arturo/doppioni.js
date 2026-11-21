// Cerca doppioni (#6188, Fase 5 del piano del 20/11/2026): le coppie di progetti che sono probabilmente lo
// stesso progetto, col motivo e col progetto che resta. Niente Herdr e niente import: il banco le prova con
// node. Il dialogo sta in doppioniui.js, l'unione in unisci.js: qui si propone soltanto, e non si scrive niente.
//
// I progetti sono le voci di `arturo progetti --json` (progettiMemoria di dati.js):
// { slug, titolo, riga, data, filoni, handoff, cartella, alias, fonte, repo }.

// Sotto questa forza una coppia non si mostra. Ogni segno forte vale 3 e basta da solo; i segni deboli valgono 2
// e hanno già dentro la loro condizione (un nome dentro l'altro conta solo se uno dei due ha handoff senza scheda).
export const DOPPIONI_SOGLIA = 2;
// Quante coppie al più: la revisione si fa a mano, una riga alla volta.
export const DOPPIONI_MAX = 40;
// Una riga di stato più corta non dice niente: "Fermo." è uguale in dieci progetti.
export const RIGA_MIN = 20;

// La chiave di una coppia, uguale nei due versi: gli slug non hanno la barra dritta.
export const chiaveCoppia = (a, b) => [String(a ?? ""), String(b ?? "")].sort().join("|");

const piano = (x) => String(x ?? "").toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, "").replace(/[^a-z0-9]+/g, " ").trim();
const conScheda = (m) => Array.isArray(m?.fonte) && m.fonte.includes("scheda");
const filoni = (m) => Number(m?.filoni) || 0;
const conHandoff = (m) => Boolean(m?.handoff) || filoni(m) > 0;
const alias = (m) => (Array.isArray(m?.alias) ? m.alias.filter((x) => typeof x === "string" && x) : []);

// Un guscio: un progetto senza scheda e senza handoff. C'è solo come cartella o come voce della fonte dei task.
// Non entra mai in una coppia: non ha niente da unire, e Arturo rifiuta l'unione ("non trovo niente di…", prova
// del 21/11/2026 su uf-dashboard-area-uf-dashboard). Sui progetti veri erano 18 coppie su 22, tutte senza uscita.
export const guscio = (m) => !conScheda(m) && !conHandoff(m);
// Handoff scritti sotto un nome che non ha mai avuto la sua scheda: il segno di un secondo nome dello stesso progetto.
export const senzaScheda = (m) => conHandoff(m) && !conScheda(m);

// Quante lettere cambiano fra due nomi (inserite, tolte o scambiate), al più `tetto`: oltre, tetto + 1.
export function distanza(a, b, tetto = 2) {
  a = String(a ?? ""); b = String(b ?? "");
  if (Math.abs(a.length - b.length) > tetto) return tetto + 1;
  let riga = Array.from({ length: b.length + 1 }, (_x, i) => i);
  for (let i = 1; i <= a.length; i += 1) {
    const dopo = [i];
    for (let j = 1; j <= b.length; j += 1) dopo.push(Math.min(riga[j] + 1, dopo[j - 1] + 1, riga[j - 1] + (a[i - 1] === b[j - 1] ? 0 : 1)));
    riga = dopo;
  }
  return Math.min(riga[b.length], tetto + 1);
}

// I segni che `a` e `b` sono lo stesso progetto: [{ forza, testo }], dal più forte. Il testo continua la frase
// "Sembrano doppioni perché…" e nomina i progetti con lo slug, che la riga del dialogo mostra accanto al nome.
// `repoComuni`: i repository che più di due progetti condividono (un monorepo): lì lo stesso repository non dice niente.
export function segniDoppione(a, b, repoComuni = new Set()) {
  const sa = String(a?.slug ?? ""), sb = String(b?.slug ?? "");
  if (!sa || !sb || sa === sb) return [];
  const segni = [];
  const aa = alias(a), ab = alias(b);
  if (aa.includes(sb)) segni.push({ forza: 3, testo: `${sb} è già un nome alternativo di ${sa}` });
  else if (ab.includes(sa)) segni.push({ forza: 3, testo: `${sa} è già un nome alternativo di ${sb}` });
  else {
    const comune = aa.find((x) => ab.includes(x));
    if (comune) segni.push({ forza: 3, testo: `hanno lo stesso nome alternativo, ${comune}` });
  }
  // il nome: uguale a meno dei trattini, quasi uguale, o uno dentro l'altro
  const na = sa.replace(/-/g, ""), nb = sb.replace(/-/g, "");
  const pa = sa.split("-").filter(Boolean), pb = sb.split("-").filter(Boolean);
  const dentro = (corte, lunghe) => corte.length < lunghe.length && corte.every((p) => lunghe.includes(p));
  if (na === nb) segni.push({ forza: 3, testo: "hanno lo stesso nome, scritto in due modi" });
  else if (dentro(pa, pb) || dentro(pb, pa)) {
    const [corto, lungo] = dentro(pa, pb) ? [a, b] : [b, a];
    // "uf" sta dentro "sito-uf", ma sono due progetti con la loro scheda: conta solo se uno dei due non ce l'ha
    const orfano = senzaScheda(lungo) ? lungo : senzaScheda(corto) ? corto : null;
    const altro = orfano === lungo ? corto : lungo;
    if (orfano && conScheda(altro)) segni.push({ forza: 2, dentro: orfano.slug, testo: `il nome ${lungo.slug} contiene ${corto.slug}, e ${orfano.slug} ha handoff ma non ha la scheda` });
  } else {
    // una lettera su un nome di almeno cinque, due su uno di almeno nove: "teleclub" e "telecub", non "eos" e "uf"
    const corto = Math.min(na.length, nb.length);
    const d = distanza(na, nb);
    // "gara-2026" e "gara-2027" sono due edizioni, non un refuso: se cambiano solo le cifre il segno non vale
    const edizioni = na.replace(/\d/g, "") === nb.replace(/\d/g, "");
    if (!edizioni && ((d === 1 && corto >= 5) || (d === 2 && corto >= 9))) segni.push({ forza: 2, testo: d === 1 ? "i nomi cambiano di una lettera" : "i nomi cambiano di due lettere" });
  }
  const ta = piano(a?.titolo), tb = piano(b?.titolo);
  if (ta && ta === tb && na !== nb) segni.push({ forza: 3, testo: `hanno lo stesso titolo, ${String(a.titolo).trim()}` });
  // la stessa riga di stato nello stesso giorno: i due nomi leggono gli stessi handoff
  const ra = String(a?.riga ?? "").trim();
  if (ra.length >= RIGA_MIN && ra === String(b?.riga ?? "").trim() && a?.data && a.data === b?.data)
    segni.push({ forza: 3, testo: "hanno la stessa riga di stato, dello stesso giorno" });
  const repo = String(a?.repo ?? "").trim();
  if (repo && !repoComuni.has(repo) && repo === String(b?.repo ?? "").trim()) segni.push({ forza: 3, testo: `hanno lo stesso repository, ${repo}` });
  return segni.sort((x, y) => y.forza - x.forza);
}

// Quale dei due resta: { vincitore, perdente, perche }. Vale il primo criterio che li distingue, nell'ordine:
// chi ha già l'altro come nome alternativo, chi ha la scheda, chi ha più filoni, chi ha handoff, il più recente,
// chi ha la cartella, il nome più corto, l'ordine alfabetico. `perche` continua la frase "Resta X perché…" e
// porta anche il secondo criterio a favore del vincitore, se c'è.
export function vincitoreProposto(a, b) {
  const sa = String(a?.slug ?? ""), sb = String(b?.slug ?? "");
  const data = (m) => String(m?.data ?? "");
  // ogni criterio: [quanto vale a, quanto vale b, il testo se vince a, il testo se vince b]
  const criteri = [
    [Number(alias(a).includes(sb)), Number(alias(b).includes(sa)), `${sb} è già un suo nome alternativo`, `${sa} è già un suo nome alternativo`],
    [Number(conScheda(a)), Number(conScheda(b)), "ha la scheda", "ha la scheda"],
    [filoni(a), filoni(b), `ha più filoni (${filoni(a)} contro ${filoni(b)})`, `ha più filoni (${filoni(b)} contro ${filoni(a)})`],
    [Number(conHandoff(a)), Number(conHandoff(b)), "ha gli handoff", "ha gli handoff"],
    [data(a), data(b), "ha l'handoff più recente", "ha l'handoff più recente"],
    [Number(Boolean(a?.cartella)), Number(Boolean(b?.cartella)), "ha la cartella", "ha la cartella"],
    [-sa.length, -sb.length, "ha il nome più corto", "ha il nome più corto"],
    [sb, sa, "viene prima in ordine alfabetico", "viene prima in ordine alfabetico"],
  ];
  // Gli ultimi due criteri spareggiano soltanto: non fanno da secondo motivo ("ha la scheda e viene prima in
  // ordine alfabetico" non dice niente).
  const SPAREGGI = 2;
  let vinceA = null;
  const motivi = [];
  for (const [i, [va, vb, testoA, testoB]] of criteri.entries()) {
    if (va === vb) continue;
    const perA = va > vb;
    if (vinceA === null) { vinceA = perA; motivi.push(perA ? testoA : testoB); continue; }
    if (perA === vinceA && i < criteri.length - SPAREGGI) { motivi.push(perA ? testoA : testoB); break; }
  }
  if (vinceA === null) vinceA = true;
  // "ha la scheda e più filoni", non "ha la scheda e ha più filoni"
  if (motivi.length === 2 && motivi[0].startsWith("ha ") && motivi[1].startsWith("ha ")) motivi[1] = motivi[1].slice(3);
  return { vincitore: vinceA ? sa : sb, perdente: vinceA ? sb : sa, perche: motivi.join(" e ") || "sono pari" };
}

// Le coppie probabili fra i progetti `lista`, tolte quelle già scartate (`scartate`: { chiaveCoppia: quando }):
// [{ chiave, perdente, vincitore, forza, motivo, perche }], dalla più forte, a pari forza quella toccata più di
// recente. `motivo` porta i due segni più forti. Al più DOPPIONI_MAX.
export function doppioni(lista, scartate = {}, quante = DOPPIONI_MAX) {
  const l = (Array.isArray(lista) ? lista : []).filter((m) => m && typeof m.slug === "string" && m.slug);
  const via = scartate && typeof scartate === "object" ? scartate : {};
  const conta = new Map();
  for (const m of l) { const r = String(m.repo ?? "").trim(); if (r) conta.set(r, (conta.get(r) ?? 0) + 1); }
  const repoComuni = new Set([...conta].filter(([, n]) => n > 2).map(([r]) => r));
  let coppie = [];
  for (let i = 0; i < l.length; i += 1) for (let j = i + 1; j < l.length; j += 1) {
    const a = l[i], b = l[j];
    const chiave = chiaveCoppia(a.slug, b.slug);
    if (a.slug === b.slug || chiave in via) continue;
    if (guscio(a) || guscio(b)) continue;
    const segni = segniDoppione(a, b, repoComuni);
    const forza = segni.reduce((n, s) => n + s.forza, 0);
    if (forza < DOPPIONI_SOGLIA) continue;
    const recente = [String(a.data ?? ""), String(b.data ?? "")].sort()[1];
    // `dentro`: la coppia sta in piedi solo sul nome contenuto, e dice quale dei due è senza scheda
    const dentro = segni.length === 1 && segni[0].dentro ? segni[0].dentro : null;
    coppie.push({ chiave, ...vincitoreProposto(a, b), forza, motivo: segni.slice(0, 2).map((s) => s.testo).join("; "), recente, dentro });
  }
  // Un nome contenuto è ambiguo quando lega lo stesso progetto a più candidati ("personale" sta in "fiscale-personale"
  // e in "niente-di-personale"), o quando quel progetto ha già una coppia forte con un altro ("herdr-arturo" è volta,
  // non arturo): allora la coppia non si mostra. Sui progetti veri del 21/11/2026 erano 3 coppie false su 8.
  const volte = new Map(), forti = new Set();
  for (const c of coppie) {
    if (c.dentro) volte.set(c.dentro, (volte.get(c.dentro) ?? 0) + 1);
    else { forti.add(c.perdente); forti.add(c.vincitore); }
  }
  coppie = coppie.filter((c) => !c.dentro || (volte.get(c.dentro) === 1 && !forti.has(c.dentro)));
  return coppie.sort((x, y) => y.forza - x.forza || (x.recente < y.recente ? 1 : x.recente > y.recente ? -1 : 0) || (x.chiave < y.chiave ? -1 : 1))
    .slice(0, Math.max(0, quante)).map(({ recente: _r, dentro: _d, ...c }) => c);
}

// La stessa coppia al contrario: lo sceglie la persona col pulsante, e allora il perché non è più quello di Volta.
export const alContrario = (c) => ({ ...c, perdente: c.vincitore, vincitore: c.perdente, perche: null });
