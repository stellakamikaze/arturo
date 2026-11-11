// Il microfono di questa macchina per le sessioni che girano su un'altra (11/11/2026).
// Claude Code registra la dettatura dall'ingresso audio della macchina dove gira la sessione. Quando
// la scheda in primo piano aggancia una sessione di un'altra macchina, volta.js accende il ponte di
// volta_microfono.py (accanto a questo file): cattura qui, ssh, microfono virtuale là. La barra
// spaziatrice tenuta premuta resta quella di Claude Code. Qui stanno solo le decisioni, senza Herdr:
// a chi va il ponte, quando accenderlo e spegnerlo, cosa dice la riga.

// L'etichetta di Herdr sul terminale che aggancia una sessione (ETICHETTA di dati.js).
const ETICHETTA = "arturo.sessione";
// Ogni quanto il ponte acceso va rinnovato (volta_microfono.py lo chiude dopo 100 s senza rinnovo),
// ogni quanto si richiede lo stato mentre si collega, e quanto resta acceso dopo che il fuoco è
// passato altrove: cambiare scheda per un attimo non deve toccare l'ingresso dell'altra macchina.
export const RINNOVO = 30000;
export const IN_AVVIO = 2000;
export const TENUTA = 60000;

// La macchina a cui portare il microfono: { target, macchina } se il terminale in primo piano aggancia
// con ssh una sessione di un'altra macchina, altrimenti null. `target` è il nome che ssh usa già per
// l'aggancio (argv_attach di volta_sonda.py: ssh, -t, target, claude, attach, id). La sessione si
// riconosce dall'etichetta della scheda, poi dall'argv: una scheda rilanciata ha l'argv della shell.
export function bersaglio(terminale, sessioni) {
  if (!terminale || typeof terminale.address !== "string" || terminale.address.includes("/")) return null;
  const argv = Array.isArray(terminale.argv) ? terminale.argv : [];
  const i = argv.indexOf("attach");
  const id = terminale.labels?.[ETICHETTA] ?? (i >= 0 ? argv[i + 1] : null);
  if (!id) return null;
  const s = (sessioni ?? []).find((x) => x && x.id === id && !x.questa && Array.isArray(x.attach));
  if (!s) return null;
  const a = s.attach;
  if (a.length !== 6 || !/(^|[\\/])ssh(\.exe)?$/.test(String(a[0])) || a[1] !== "-t" || a[4] !== "attach") return null;
  const target = String(a[2] ?? "");
  if (!target || target.startsWith("-")) return null;
  return { target, macchina: s.macchina ?? target };
}

// Un giro del controllo. `st` è { target, macchina, visto, rinnovato, stato } (null all'inizio), `b` il
// bersaglio di adesso (o null), `spento` l'interruttore della persona. Torna { st, azione }: azione è
// null, { verbo: "accendi", target } o { verbo: "spegni" }.
export function passo(st, b, adesso, spento = false) {
  const acceso = Boolean(st?.target);
  if (spento) return { st: null, azione: acceso ? { verbo: "spegni" } : null };
  if (b) {
    if (!acceso || st.target !== b.target)
      return { st: { target: b.target, macchina: b.macchina, visto: adesso, rinnovato: adesso, stato: "avvio" }, azione: { verbo: "accendi", target: b.target } };
    const ogni = st.stato === "avvio" ? IN_AVVIO : RINNOVO;
    if (adesso - st.rinnovato >= ogni) return { st: { ...st, visto: adesso, rinnovato: adesso }, azione: { verbo: "accendi", target: st.target } };
    return { st: { ...st, visto: adesso }, azione: null };
  }
  if (!acceso) return { st: null, azione: null };
  if (adesso - st.visto > TENUTA) return { st: null, azione: { verbo: "spegni" } };
  // fuoco altrove da poco: il ponte resta, e va rinnovato perché non scada da solo
  if (adesso - st.rinnovato >= RINNOVO) return { st: { ...st, rinnovato: adesso }, azione: { verbo: "accendi", target: st.target } };
  return { st, azione: null };
}

// La riga sotto "Tutte le sessioni": { testo, avviso } oppure null se non c'è niente da dire.
// `m` è shared arturo.microfono: { stato, macchina, motivo, qui, spento }.
export function rigaMicrofono(m) {
  if (!m) return null;
  if (m.spento) return { testo: "Microfono: spento, le sessioni delle altre macchine sentono il loro" };
  if (m.stato === "attivo") return { testo: `Microfono: ${m.qui ?? "questa macchina"} → ${m.macchina}` };
  if (m.stato === "avvio") return { testo: `Microfono: collego ${m.macchina}…` };
  if (m.stato === "errore") return { testo: `Microfono: ${m.motivo ?? "il ponte si è chiuso"}${m.macchina ? ` (${m.macchina})` : ""}`, avviso: true };
  return null;
}
