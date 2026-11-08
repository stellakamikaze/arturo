// La revisione della settimana: i progetti da guardare, in tre liste.
// Ogni progetto sta in una lista sola, la più urgente: prima i todo scaduti, poi i todo che aspettano
// la persona, poi i progetti senza un punto da più di FERMO_GG giorni. Il motivo dice tutti i fatti.
// Modulo senza import di Herdr, così il banco lo prova con node (HZ11).

export const FERMO_GG = 7;

const giorni = (n) => (n === 1 ? "1 giorno" : `${n} giorni`);

// vista: la vista di `arturo todo --json`. Restituisce { scaduti, te, fermi }: liste di
// { progetto, motivo }, ognuna dal caso più urgente.
export function revisione(vista) {
  const scaduti = new Map();
  for (const g of vista?.gruppi ?? []) for (const t of g.todo ?? []) {
    if (typeof t.giorni !== "number" || t.giorni >= 0) continue;
    const s = scaduti.get(t.progetto) ?? { n: 0, peggio: 0 };
    s.n += 1;
    s.peggio = Math.max(s.peggio, -t.giorni);
    scaduti.set(t.progetto, s);
  }
  const liste = { scaduti: [], te: [], fermi: [] };
  for (const p of vista?.progetti ?? []) {
    const s = scaduti.get(p.nome);
    const te = Number(p.chiedono_te) || 0;
    const eta = typeof p.eta_gg === "number" ? p.eta_gg : null;
    const fermo = eta !== null && eta > FERMO_GG;
    const pezzi = [];
    if (s) pezzi.push(s.n === 1 ? `1 todo scaduto da ${giorni(s.peggio)}` : `${s.n} todo scaduti, il più vecchio da ${giorni(s.peggio)}`);
    if (te) pezzi.push(te === 1 ? "1 todo aspetta te" : `${te} todo aspettano te`);
    if (fermo) pezzi.push(`ultimo punto ${giorni(eta)} fa`);
    if (!pezzi.length) continue;
    const motivo = pezzi.join(" · ");
    const voce = { progetto: p, motivo: motivo[0].toUpperCase() + motivo.slice(1) };
    if (s) liste.scaduti.push({ ...voce, peso: s.peggio });
    else if (te) liste.te.push({ ...voce, peso: te });
    else liste.fermi.push({ ...voce, peso: eta });
  }
  for (const l of Object.values(liste)) l.sort((a, b) => b.peso - a.peso);
  return liste;
}

// La settimana ISO di una data "AAAA-MM-GG": "2026-W45". Serve ad aprire la finestra una volta a settimana.
export function settimanaDi(giorno) {
  const d = new Date(`${giorno}T12:00:00Z`);
  if (Number.isNaN(d.getTime())) return "";
  const dow = (d.getUTCDay() + 6) % 7; // lunedì = 0
  d.setUTCDate(d.getUTCDate() - dow + 3); // il giovedì della stessa settimana decide l'anno
  const anno = d.getUTCFullYear();
  const n = 1 + Math.floor((d - new Date(Date.UTC(anno, 0, 1, 12))) / 86400000 / 7);
  return `${anno}-W${String(n).padStart(2, "0")}`;
}
