// Le azioni sui todo del pannello Da fare: per ogni gesto, gli argomenti di `arturo todo`.
// Modulo puro, senza herdr: lo usa il pannello, lo prova il banco con node (HZ12) e il banco delle
// viste allineate (VA01-VA03) ne legge i verbi: il primo elemento di ogni `argv`.
// Ogni gesto che tocca un todo porta il titolo mostrato: se il numero ora indica un altro todo
// (dopo una rinumerazione), la CLI si ferma invece di scrivere sul todo sbagliato.

export const CHI = [["io", "Claude"], ["tu", "Tu"], ["decidi", "Decidi tu, poi Claude"]];
export const QUANDO = [["oggi", "Oggi"], ["settimana", "Questa settimana"], ["più avanti", "Più avanti"]];

const atteso = (t) => `--titolo-atteso=${t.titolo}`;

export const fatto = (t) => ({ argv: ["fatto", String(t.id), atteso(t)], esito: "Fatto" });

// I gesti del menu di una riga, nell'ordine in cui compaiono. Ognuno:
// { id, gruppo, etichetta, argv(testo), esito, chiede? }. Con `chiede` il menu mostra un campo
// prima di scrivere: { domanda, obbligo } (obbligo: senza testo il gesto non parte).
export function azioni(t) {
  const out = [];
  for (const [chi, etichetta] of CHI) {
    if (chi === t.chi) continue;
    out.push({ id: `chi-${chi}`, gruppo: "Chi lo fa", etichetta, esito: `Ora lo fa: ${etichetta}`,
      argv: () => ["modifica", String(t.id), atteso(t), "--chi", chi] });
  }
  for (const [quando, etichetta] of QUANDO) {
    if (quando === t.quando) continue;
    out.push({ id: `quando-${quando}`, gruppo: "Quando", etichetta, esito: `Spostato a: ${etichetta.toLowerCase()}`,
      argv: () => ["modifica", String(t.id), atteso(t), "--quando", quando] });
  }
  if (t.stato === "fermo") {
    out.push({ id: "riprendi", gruppo: "Stato", etichetta: "Riprendi", esito: "Ripreso",
      argv: () => ["riprendi", String(t.id), atteso(t)] });
  } else {
    out.push({ id: "ferma", gruppo: "Stato", etichetta: "Fermo: aspetta qualcosa", esito: "Fermato",
      chiede: { domanda: "Cosa aspetta? (si può lasciare vuoto)", obbligo: false },
      argv: (testo) => ["ferma", String(t.id), atteso(t), ...(testo ? ["--", testo] : [])] });
  }
  out.push({ id: "nota", gruppo: "Stato", etichetta: "Aggiungi una nota", esito: "Nota aggiunta",
    chiede: { domanda: "La nota", obbligo: true },
    argv: (testo) => ["nota", String(t.id), atteso(t), "--", testo] });
  out.push({ id: "scarta", gruppo: "Stato", etichetta: "Scarta", esito: "Scartato",
    chiede: { domanda: "Perché lo scarti?", obbligo: true },
    argv: (testo) => ["scarta", String(t.id), atteso(t), "--", testo] });
  return out;
}

// Un todo nuovo: titolo, progetto, chi lo fa e quando. Torna null se il titolo è vuoto.
export function aggiungi({ titolo, progetto, chi = "tu", quando = "settimana" }) {
  const testo = String(titolo ?? "").replace(/\s+/g, " ").trim();
  if (!testo || !progetto) return null;
  return { argv: ["aggiungi", "--progetto", progetto, "--chi", chi, "--quando", quando, "--", testo], esito: "Aggiunto" };
}
