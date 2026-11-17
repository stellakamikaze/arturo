// Le azioni sui todo del pannello Da fare: per ogni gesto, gli argomenti di `arturo todo`.
// Modulo puro, senza herdr: lo usa il pannello, lo prova il banco con node (HZ12) e il banco delle
// viste allineate (VA01-VA03) ne legge i verbi: il primo elemento di ogni `argv`.
// Ogni gesto che tocca un todo porta il titolo mostrato: se il numero ora indica un altro todo
// (dopo una rinumerazione), la CLI si ferma invece di scrivere sul todo sbagliato.

export const CHI = [["io", "Claude"], ["tu", "Tu"], ["decidi", "Decidi tu, poi Claude"]];
export const QUANDO = [["oggi", "Oggi"], ["settimana", "Questa settimana"], ["più avanti", "Più avanti"]];

const atteso = (t) => `--titolo-atteso=${t.titolo}`;

export const fatto = (t) => ({ argv: ["fatto", String(t.id), atteso(t)], esito: "Fatto" });

// Le spunte messe dalla persona che restano dopo una rilettura: quelle dei todo ancora in elenco. Una
// rilettura partita mentre "fatto" è in viaggio riporta il todo aperto, e la spunta non si toglie da
// sola; quando il todo esce dall'elenco la sua spunta non serve più.
export function ancoraFatti(fatti, vista) {
  const vivi = new Set();
  for (const g of vista?.gruppi ?? []) for (const t of g.todo ?? []) vivi.add(t.id);
  return new Set([...(fatti ?? [])].filter((id) => vivi.has(id)));
}

// "Lavoraci": il todo passa in corso prima che Claude parta. /fine lo chiude, o lo rimette da fare
// se il lavoro non è finito (#4994). Un todo già in corso non si riscrive: null.
export const inizia = (t) => (t.stato === "in corso" ? null : { argv: ["inizia", String(t.id), atteso(t)], esito: "Claude ci lavora" });

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
  if (t.stato === "fermo" || t.stato === "in corso") {
    const fermo = t.stato === "fermo";
    out.push({ id: "riprendi", gruppo: "Stato", etichetta: fermo ? "Riprendi" : "Claude non ci lavora più", esito: fermo ? "Ripreso" : "Di nuovo da fare",
      argv: () => ["riprendi", String(t.id), atteso(t)] });
  }
  if (t.stato !== "fermo") {
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

// Una risposta della Coda su una carta UF (#5722, volta_capo.py): cosa fa il gesto. Le carte di task hanno
// Fatto, Rimanda, A Claude, Scarta e Apri (gli stessi argomenti del menu Altro qui sopra); le carte di
// bozza Apri, Rimanda e Riscrivi. Una risposta libera (R) è una nota sul task, o l'indicazione per
// riscrivere la bozza. Torna { azione: "todo", argv, esito } | { azione: "apri", progetto, todo }
// | { azione: "link", url } | { azione: "rimanda" } | { azione: "nuova", prompt, esito } | null.
export const SCARTATA_DALLA_CODA = "Scartato dalla Coda di Volta";
// `extra.nota` (il commento della Coda, 16/11/2026): su un task diventa una nota scritta prima del gesto
// (`prima`), e su Scarta il motivo; su una bozza sono le indicazioni per Riscrivi.
export function gestoUf(c, testo, extra = {}) {
  const r = String(testo ?? "").replace(/\s+/g, " ").trim();
  const nota = String(extra?.nota ?? "").replace(/\s+/g, " ").trim();
  if (!c || c.origine !== "uf" || !r) return null;
  if (c.fonte === "bozza") {
    const b = c.bozza ?? {};
    if (r === "Apri") return b.link ? { azione: "link", url: b.link, esito: "Aperta in Gmail" } : null;
    if (r === "Rimanda") return { azione: "rimanda", esito: "Rimandata a domani" };
    if (r === "Già fatto") return { azione: "giafatto", esito: "Tolta dalla Coda" };
    const indicazioni = r === "Riscrivi" ? nota : r;
    const come = indicazioni ? ` Indicazioni di Federico: ${indicazioni}` : "";
    return { azione: "nuova", esito: "Claude la riscrive",
      prompt: `/posta riscrivi la bozza "${b.oggetto ?? c.domanda ?? ""}" (thread ${b.thread}${b.account ? `, account ${b.account}` : ""}): è in Gmail dal ${b.creato ?? "?"} e non è partita.${come}` };
  }
  const t = c.todo;
  if (!t || !Number.isInteger(t.id) || typeof t.titolo !== "string") return null;
  const g = gestoTask(t, r, nota, c);
  return g && nota && r !== "Scarta" && (g.azione === "todo" || g.azione === "apri") && g.argv?.[0] !== "nota"
    ? { ...g, prima: [["nota", String(t.id), atteso(t), "--", nota]] } : g;
}
function gestoTask(t, r, nota, c) {
  if (r === "Fatto") return { azione: "todo", ...fatto(t) };
  if (r === "Rimanda") return { azione: "todo", argv: ["modifica", String(t.id), atteso(t), "--quando", "più avanti"], esito: "Spostato a più avanti" };
  if (r === "A Claude") return { azione: "todo", argv: ["modifica", String(t.id), atteso(t), "--chi", "io"], esito: "Ora lo fa: Claude" };
  if (r === "Scarta") return { azione: "todo", argv: ["scarta", String(t.id), atteso(t), "--", nota || SCARTATA_DALLA_CODA], esito: "Scartato" };
  if (r === "Apri") return { azione: "apri", progetto: c.progetto ?? null, todo: { id: t.id, titolo: t.titolo } };
  return { azione: "todo", argv: ["nota", String(t.id), atteso(t), "--", r], esito: "Nota aggiunta" };
}

// Un todo nuovo: titolo, progetto, chi lo fa e quando. Torna null se il titolo è vuoto.
export function aggiungi({ titolo, progetto, chi = "tu", quando = "settimana" }) {
  const testo = String(titolo ?? "").replace(/\s+/g, " ").trim();
  if (!testo || !progetto) return null;
  return { argv: ["aggiungi", "--progetto", progetto, "--chi", chi, "--quando", quando, "--", testo], esito: "Aggiunto" };
}

// I gesti della checklist di Volta (checklist.js, 17/11/2026) sulle righe legate a un todo: gli argv di
// `arturo todo`, gli stessi del pannello e del menu Altro. `scelte`: { [n]: { gesto, nota } }. Scarta porta la
// nota della riga come motivo, altrimenti SCARTATA_DALLA_CHECKLIST. Una riga senza todo legato non ha gesti qui:
// la sua scelta arriva solo alla sessione, nel testo.
export const SCARTATA_DALLA_CHECKLIST = "Scartato dalla checklist di Volta";
export function gestiChecklist(lista, scelte = {}) {
  const out = [];
  for (const v of (lista?.filoni ?? []).flatMap((f) => f?.voci ?? [])) {
    const t = v.todo;
    const g = scelte?.[v.n]?.gesto;
    if (!g || !t || !Number.isInteger(t.id) || typeof t.titolo !== "string") continue;
    const nota = String(scelte?.[v.n]?.nota ?? "").replace(/\s+/g, " ").trim();
    if (g === "fatto") out.push({ n: v.n, ...fatto(t) });
    else if (g === "scarta") out.push({ n: v.n, argv: ["scarta", String(t.id), atteso(t), "--", nota || SCARTATA_DALLA_CHECKLIST], esito: "Scartato" });
    else if (g === "rimanda") out.push({ n: v.n, esito: "Spostato a più avanti", argv: ["modifica", String(t.id), atteso(t), "--quando", "più avanti"] });
    else if (g === "chi") {
      const chi = t.chi === "io" ? "tu" : "io";
      out.push({ n: v.n, argv: ["modifica", String(t.id), atteso(t), "--chi", chi], esito: chi === "io" ? "Ora lo fa: Claude" : "Ora lo fai tu" });
    }
  }
  return out;
}
