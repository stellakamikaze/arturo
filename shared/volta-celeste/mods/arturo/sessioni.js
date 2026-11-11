// Volta Celeste: le sessioni di Claude di tutte le macchine, come le legge teletrasporto.py volta.
// Modulo puro, senza herdr: raggruppa, ordina, scrive le frasi e decide cosa fa un clic.
// Lo prova il banco HZ17-HZ19 con node (tests/test_herdr_2026_11_08.py).
//
// Una riga del file (~/.cache/volta/sessioni.json, campo "sessioni"):
// { macchina, host, questa, sessionId, id, nome, progetto, titolo, stato: aspetta|lavora|ferma|errore,
//   tipo: background|interattiva, attach: argv | null, cartella, ultimo, risposta, azione, vecchia? }

export const MODI = { macchina: "Per macchina", progetto: "Per progetto" };
export const SENZA = "Senza progetto";

const RANGO = { aspetta: 0, errore: 1, lavora: 2, ferma: 3 };
const rango = (s) => RANGO[s.stato] ?? 3;
const tempo = (s) => Date.parse(s.ultimo || "") || 0;

// Il nome di un progetto per le persone: "due-mondi" → "Due mondi", "uf" → "UF".
export function nomeProgetto(p) {
  const s = String(p ?? "").trim();
  if (!s) return SENZA;
  if (/[A-Z]/.test(s)) return s;
  const t = s.split(/[-_\s]+/).filter(Boolean).map((w) => (w.length <= 2 ? w.toUpperCase() : w)).join(" ");
  return t[0].toUpperCase() + t.slice(1);
}

// Il titolo di una sessione. Prima quello che hooks/titolo-sessione.py scrive a fine turno (poche
// parole in italiano sul lavoro in corso, campo "titolo"). Senza, il nome di Claude; i nomi automatici
// ("claudecode-ca": cartella più due lettere) non dicono niente: al loro posto la prima riga
// dell'ultima risposta.
export function titolo(s) {
  const scritto = String(s.titolo ?? "").replace(/\s+/g, " ").trim();
  if (scritto) return scritto;
  const nome = String(s.nome ?? "").trim();
  const automatico = !nome || nome === s.id || /^[\w.-]+-[0-9a-f]{2}$/.test(nome);
  if (!automatico) return nome;
  const riga = String(s.risposta ?? "").split("\n").map((r) => r.replace(/[*_`#>]/g, "").replace(/\s+/g, " ").trim()).find(Boolean);
  if (riga) return riga.length > 70 ? riga.slice(0, 70).replace(/\s+\S*$/, "") + "…" : riga;
  return `Sessione ${s.id}`;
}

// "da 4 min", "da 3 ore", "da 2 giorni"; vuoto senza data.
export function daQuanto(iso, adesso = Date.now()) {
  const t = Date.parse(iso || "");
  if (!t) return "";
  const min = Math.max(0, Math.round((adesso - t) / 60000));
  if (min < 1) return "da poco";
  if (min < 60) return `da ${min} min`;
  const ore = Math.round(min / 60);
  if (ore < 24) return `da ${ore} ${ore === 1 ? "ora" : "ore"}`;
  const gg = Math.round(ore / 24);
  return `da ${gg} ${gg === 1 ? "giorno" : "giorni"}`;
}

// La frase di stato e il colore del tema (blocked, working, done, idle, muted, dim).
export function fraseStato(s, adesso = Date.now()) {
  if (s.vecchia) return { testo: "Ultima lettura: la macchina non risponde", colore: "dim" };
  if (s.stato === "aspetta") return { testo: "Ti aspetta", colore: "blocked" };
  if (s.stato === "lavora") return { testo: "Sta lavorando", colore: "working" };
  if (s.stato === "errore") return { testo: "Si è fermata con un errore", colore: "blocked" };
  const q = daQuanto(s.ultimo, adesso);
  return { testo: q ? `Ferma ${q}` : "Ferma", colore: "muted" };
}

// La seconda riga: ciò che il gruppo non dice già (il progetto per macchina, la macchina per progetto).
export function dettaglio(s, modo, adesso = Date.now()) {
  const dove = modo === "progetto" ? s.macchina : (s.progetto ? nomeProgetto(s.progetto) : "");
  const f = fraseStato(s, adesso);
  return { testo: dove ? `${dove} · ${f.testo}` : f.testo, colore: f.colore };
}

// I gruppi: [{ chiave, titolo, nota?, sessioni }]. Per macchina nell'ordine del file (questa per
// prima), con una nota per la macchina che non risponde; per progetto prima chi ti aspetta,
// "Senza progetto" in fondo. Dentro ogni gruppo: ti aspetta, errore, lavora, ferma; poi la più recente.
export function gruppi(dati, modo = "macchina") {
  const righe = [...(dati?.sessioni ?? [])].sort((a, b) => rango(a) - rango(b) || tempo(b) - tempo(a) || titolo(a).localeCompare(titolo(b)));
  const per = new Map();
  const metti = (chiave, tit, s) => {
    if (!per.has(chiave)) per.set(chiave, { chiave, titolo: tit, sessioni: [] });
    if (s) per.get(chiave).sessioni.push(s);
  };
  if (modo === "progetto") {
    for (const s of righe) metti(s.progetto ? String(s.progetto) : "", nomeProgetto(s.progetto), s);
    const out = [...per.values()];
    const primo = (g) => Math.min(...g.sessioni.map(rango));
    out.sort((a, b) => (a.chiave === "") - (b.chiave === "") || primo(a) - primo(b) || a.titolo.localeCompare(b.titolo));
    const giu = (dati?.macchine ?? []).filter((m) => m.irraggiungibile).map((m) => m.macchina);
    if (giu.length && out.length) out[out.length - 1].nota = `${giu.join(", ")} non ${giu.length > 1 ? "rispondono" : "risponde"}`;
    return out;
  }
  for (const m of dati?.macchine ?? []) metti(m.host, m.macchina, null);
  for (const s of righe) metti(s.host, s.macchina, s);
  const out = [];
  for (const m of dati?.macchine ?? []) {
    const g = per.get(m.host);
    if (m.irraggiungibile) g.nota = g.sessioni.length ? "Non risponde: mostro l'ultima lettura" : "Non risponde";
    if (g.sessioni.length || g.nota) out.push(g);
    per.delete(m.host);
  }
  return out.concat([...per.values()].filter((g) => g.sessioni.length));
}

// Cosa fa il clic: { azione: "aggancia", argv } per una sessione in background, { azione: "porta" }
// per un'interattiva ferma (prima /bg con porta-volta), { azione: "mostra", terminale } per
// un'interattiva che gira in una scheda di Herdr, { azione: "no", motivo } altrimenti.
export function clic(s) {
  if (s.vecchia) return { azione: "no", motivo: `${s.macchina} non risponde: riprova quando torna.` };
  if (s.tipo === "background") {
    if (!Array.isArray(s.attach) || !s.attach.length) return { azione: "no", motivo: "Non so come agganciare questa sessione." };
    return { azione: "aggancia", argv: s.attach };
  }
  // partita nella shell di una scheda di Herdr: sta già in Volta, il clic la porta davanti
  if (s.terminale) return { azione: "mostra", terminale: s.questa ? s.terminale : `${s.host}/${s.terminale}` };
  if (s.stato === "lavora") return { azione: "no", motivo: "Sta lavorando nel suo Terminale: la sposto quando si ferma." };
  if (s.stato === "aspetta") return { azione: "no", motivo: "Ti aspetta nel suo Terminale: rispondi lì, poi la sposto." };
  if (s.stato === "errore") return { azione: "no", motivo: "Si è fermata con un errore: aprila dal suo Terminale." };
  return { azione: "porta" };
}

// La chiave che riconosce una sessione già agganciata in una scheda: l'id corto nell'argv, come
// parola a sé oppure dentro un comando di shell: "sh -c 'while :; do ssh … claude attach <id>; …'"
// delle schede aperte da altre strade, "pwsh -Command & '…claude.exe' 'attach' '<id>'" su Windows.
// Senza, il clic apre un secondo aggancio della stessa sessione e le due schede si contendono la
// larghezza del terminale.
const dentro = (a, id) => typeof a === "string" &&
  new RegExp(`\\battach['"]?\\s+['"]?${id.replace(/[^\w-]/g, "")}\\b`).test(a);
export const agganciata = (argv, s) => Array.isArray(argv) && !!s?.id &&
  ((argv.includes("attach") && argv.includes(s.id)) || argv.some((a) => dentro(a, s.id)));

// I gesti sulla riga di una sessione in background, oltre al clic che la apre (claude attach, anche se
// lavora): l'anteprima (anteprima() qui sotto, o claude logs senza trascrizione), ferma (stop) se è viva, riavvia (respawn) dopo un errore, elimina
// (rm, con conferma) se è ferma. Un'interattiva e una riga vecchia non ne hanno: si aprono e basta.
export function azioni(s) {
  if (!s || s.vecchia || s.tipo !== "background") return [];
  const out = [{ verbo: "logs", testo: "Anteprima" }];
  if (s.stato === "lavora" || s.stato === "aspetta") out.push({ verbo: "stop", testo: "Ferma" });
  if (s.stato === "errore") out.push({ verbo: "respawn", testo: "Riavvia" });
  if (s.stato === "ferma" || s.stato === "errore") out.push({ verbo: "rm", testo: "Elimina", conferma: "Sì, elimina" });
  return out;
}

// L'Anteprima di una sessione senza aprirla (#5240): l'ultima risposta e l'ultima azione che la sonda
// legge dalla trascrizione (campi risposta e azione), come blocchi { etichetta, righe } da mandare a
// capo. Del markdown toglie solo i segni (grassetto, codice, titoli, citazioni): i nomi col trattino
// basso restano interi. null se la trascrizione manca: allora Volta mostra lo schermo di claude logs.
const senzaSegni = (r) => r.replace(/\*\*|`/g, "").replace(/^\s*(#+|>)\s*/, "").replace(/\s+/g, " ").trim();
export function anteprima(s) {
  const righe = String(s?.risposta ?? "").split("\n").map(senzaSegni).filter(Boolean);
  const azione = senzaSegni(String(s?.azione ?? "").replace(/\s+/g, " ")).replace(/:$/, "");
  const out = [];
  if (righe.length) out.push({ etichetta: "Ultima risposta", righe });
  if (azione) out.push({ etichetta: "Ultima azione", righe: [azione] });
  return out.length ? out : null;
}

const chiave = (s) => `${s.host}/${s.sessionId}`;

// Le sessioni che da una lettura all'altra sono passate a "ti aspetta", di qualunque macchina.
// Alla prima lettura nessuna: l'avviso è per un cambio, non per chi aspettava già all'apertura.
export function nuoveInAttesa(prima, dopo) {
  if (!prima) return [];
  const era = new Map((prima.sessioni ?? []).map((s) => [chiave(s), s.stato]));
  return (dopo?.sessioni ?? []).filter((s) => !s.vecchia && s.stato === "aspetta" && era.get(chiave(s)) !== "aspetta");
}

// Lo stato di ogni sessione per id corto, per le parti che agganciano una sessione in background in
// una scheda: lì Herdr non ha lo stato del terminale, e lo prendono da qui (shared arturo.volta.stati).
export function statiCorti(dati) {
  const out = {};
  for (const s of dati?.sessioni ?? []) if (s.id && !s.vecchia) out[s.id] = { stato: s.stato, host: s.host };
  return out;
}
