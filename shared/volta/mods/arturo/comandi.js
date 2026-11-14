// I comandi del mod: "arturo.<nome>", da un tasto, da herdr-app do o da una finestra del mod. Herdr li
// consegna a nextCommand() delle sole parti mostrate. Li esegue la barra (barra.js), che resta viva: una
// finestra che fa nascere una sessione manda il comando e si chiude, perché un overlay chiuso ferma il suo
// codice al primo await e la nascita resterebbe a metà. Qui c'è solo cosa chiede ogni comando: niente
// Herdr, così il banco lo prova con node.

// Il comando con cui la barra di stato chiede alla barra se riceve i comandi (testata.js, barra nascosta).
export const PING = "ci-sei";

// Il comando che apre un progetto (la finestra "Apri un progetto", "Fai il punto" della settimana).
export const comandoApri = (slug) => `arturo.apri-${slug}`;

// Il comando che fa nascere una conversazione nuova in un progetto (la tessera di ⌘T, 12/11/2026).
export const comandoConversazione = (slug) => `arturo.conversazione-${slug}`;

// Il comando che esegue una richiesta di "Cosa posso chiedere".
export const comandoSuggerimento = (id) => `arturo.suggerimento-${id}`;

// Cosa chiede il comando `c` (senza "arturo."): { verbo, arg, lungo }. `lungo`: il comando aspetta una
// nascita o uno scatto della finestra, e chi lo esegue non lo aspetta, altrimenti i comandi dopo restano
// in coda per minuti. L'ordine conta: "volta-nuova" e "volta-menu-<id>" vengono prima di "volta-<id>".
// Un comando che nessuno conosce ha verbo null.
export function instrada(c) {
  c = String(c ?? "");
  const dopo = (prefisso) => c.slice(prefisso.length);
  if (c === PING) return { verbo: "ci-sei", arg: null, lungo: false };
  if (c === "apri") return { verbo: "apri", arg: null, lungo: false };
  // "apri-<slug>": il progetto, nel suo spazio o in una sessione nuova.
  if (c.startsWith("apri-")) return { verbo: "progetto", arg: dopo("apri-"), lungo: true };
  // "conversazione-<slug>": una conversazione nuova nel progetto, anche se il suo spazio c'è già.
  if (c.startsWith("conversazione-")) return { verbo: "conversazione", arg: dopo("conversazione-"), lungo: true };
  if (c === "chiedi") return { verbo: "chiedi", arg: null, lungo: false };
  // "suggerimento-<id>": una richiesta di "Cosa posso chiedere".
  if (c.startsWith("suggerimento-")) return { verbo: "suggerimento", arg: dopo("suggerimento-"), lungo: true };
  if (c === "settimana") return { verbo: "settimana", arg: null, lungo: false };
  // "guida" e "guida<N>": la guida, alla pagina N (da 1).
  if (/^guida\d?$/.test(c)) return { verbo: "guida", arg: Math.max(0, Number(dopo("guida") || 1) - 1), lungo: false };
  if (c === "nuova") return { verbo: "nuova", arg: null, lungo: true };
  // "nuova-<esadecimale>": Nuova richiesta col testo scritto nella ricerca (⌘K, #5369), quattro cifre
  // per carattere (comandoNuova di sessioni.js); la barra lo decodifica.
  if (/^nuova-(?:[0-9a-f]{4})+$/.test(c)) return { verbo: "nuova", arg: dopo("nuova-"), lungo: true };
  // "dove-scelta": apre il selettore di "Nasce su" (prove senza clic). Viene prima di "dove-<macchina>".
  if (c === "dove-scelta") return { verbo: "dove-scelta", arg: null, lungo: false };
  // "dove-<macchina>": la scelta di "Nasce su" (dove-qui per questa macchina).
  if (c.startsWith("dove-")) return { verbo: "dove", arg: dopo("dove-"), lungo: false };
  if (c === "nota") return { verbo: "nota", arg: null, lungo: true };
  // "nota-<id>": il velo aperto sulla nota <id>, dall'elenco delle note.
  if (c.startsWith("nota-")) return { verbo: "nota", arg: dopo("nota-"), lungo: true };
  if (c === "note") return { verbo: "note", arg: null, lungo: false };
  // "versione": la versione del mod e l'ultimo controllo, in un avviso (prove senza clic).
  if (c === "versione") return { verbo: "versione", arg: null, lungo: false };
  // "movimento", "movimento-acceso", "movimento-spento": l'interruttore delle animazioni (#5410); il primo
  // lo gira, gli altri due lo mettono (prove senza clic, herdr-app do).
  // "impostazioni": il menu di Impostazioni del piede (prove senza clic).
  if (c === "impostazioni") return { verbo: "impostazioni", arg: null, lungo: false };
  if (c === "movimento" || c === "movimento-acceso" || c === "movimento-spento") return { verbo: "movimento", arg: c === "movimento" ? null : c.endsWith("acceso"), lungo: false };
  // "volta-gruppi-<macchina|progetto>": l'interruttore dell'elenco.
  if (c === "volta-gruppi-macchina" || c === "volta-gruppi-progetto") return { verbo: "gruppi", arg: dopo("volta-gruppi-"), lungo: false };
  // "casa": le tessere dei progetti al posto del terminale (⌘T dal 12/11/2026, #5371); "casa-chiudi" torna
  // al terminale (prove senza clic, herdr-app do).
  if (c === "casa" || c === "casa-chiudi") return { verbo: c, arg: null, lungo: false };
  // "volta-nuova": la scheda nuova (la prima tessera di ⌘T) è una sessione di Claude, non una shell (#5290).
  if (c === "volta-nuova") return { verbo: "volta-nuova", arg: null, lungo: true };
  // "volta-giro-avanti" e "volta-giro-indietro": ⌘↓ e ⌘↑, la sessione dopo o prima nell'elenco.
  if (c === "volta-giro-avanti" || c === "volta-giro-indietro") return { verbo: "volta-giro", arg: c.endsWith("avanti") ? 1 : -1, lungo: false };
  // "volta-chiudi": ⌘W (Ctrl+W su Windows) sulla scheda davanti: una sessione in background va in congedo
  // e fuori dall'elenco subito, il resto si chiude come in Herdr (12/11/2026).
  if (c === "volta-chiudi") return { verbo: "volta-chiudi", arg: null, lungo: false };
  // "volta-chiudi-<scheda>": la X di una scheda nella fila delle schede, lo stesso gesto su quella scheda.
  if (c.startsWith("volta-chiudi-")) return { verbo: "volta-chiudi", arg: dopo("volta-chiudi-"), lungo: false };
  // "contesto" e "contesto-<slug>": la finestra del contesto di un progetto (contestoui.js); senza slug
  // quello dello spazio aperto.
  if (c === "contesto") return { verbo: "contesto", arg: null, lungo: false };
  if (c.startsWith("contesto-")) return { verbo: "contesto", arg: dopo("contesto-"), lungo: false };
  // "volta-menu-<id>": il menu del tasto destro su una sessione (#5291).
  if (c.startsWith("volta-menu-")) return { verbo: "volta-menu", arg: dopo("volta-menu-"), lungo: false };
  // "volta-altro-<id>": il riquadro "Altro" di una sessione.
  if (c.startsWith("volta-altro-")) return { verbo: "volta-altro", arg: dopo("volta-altro-"), lungo: false };
  // "volta-cambia-<nome|progetto>-<esadecimale>-<id>": il nome o il progetto nuovo di una sessione, dal
  // dialogo di cambio.js (#5292). L'argomento è il comando intero: lo legge cambiaComando di volta.js.
  if (c.startsWith("volta-cambia-")) return { verbo: "volta-cambia", arg: c, lungo: false };
  // "volta-spostatutto-<macchina>": tutte le sessioni spostabili su <macchina> (Sposta tutto su…, sposta.js).
  if (c.startsWith("volta-spostatutto-")) return { verbo: "volta-spostatutto", arg: dopo("volta-spostatutto-"), lungo: false };
  // "volta-sposta-<chiave>-<macchina>": la sessione <chiave> (macchina:id, chiave di sessioni.js, #5643)
  // su un'altra macchina (sposta.js). La chiave viene prima: il nome di una macchina può avere trattini, e
  // l'id non ne ha, quindi il primo trattino dopo i due punti chiude la chiave. La forma di prima del
  // 14/11, "volta-sposta-<macchina>-<id>" senza due punti, vale ancora per herdr-app do: lì l'id è l'ultimo pezzo.
  const sk = /^volta-sposta-([^:]+:[0-9A-Za-z]+)-(.+)$/.exec(c);
  if (sk) return { verbo: "volta-sposta", arg: { macchina: sk[2], id: sk[1] }, lungo: false };
  const sp = /^volta-sposta-([^:]+)-([0-9A-Za-z]+)$/.exec(c);
  if (sp) return { verbo: "volta-sposta", arg: { macchina: sp[1], id: sp[2] }, lungo: false };
  // "volta-gesto-<verbo>-<chiave>": un gesto di "Altro" o del menu, per macchina:id (o il solo id, da herdr-app do).
  const g = /^volta-gesto-([a-z]+)-(.+)$/.exec(c);
  if (g) return { verbo: "volta-gesto", arg: { verbo: g[1], id: g[2] }, lungo: false };
  // "volta-<id>": lo stesso clic di una sessione di Volta, da tastiera o da herdr-app do.
  if (c.startsWith("volta-")) return { verbo: "volta", arg: dopo("volta-"), lungo: false };
  return { verbo: null, arg: null, lungo: false };
}

// Con la barra nascosta (⌘B) nessuno esegue i comandi: la barra di stato la mostra e rimanda il comando.
// Con la barra mostrata non fa niente, e il comando di controllo non si rimanda mai.
export const daRimandare = (c, nascosta) => Boolean(nascosta) && c !== PING && instrada(c).verbo !== null;
