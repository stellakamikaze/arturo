// Le note sulla finestra (⌘⇧N): da testo, punto e misura della finestra, il contenuto di nota.json e gli
// argomenti di `arturo todo aggiungi`. Modulo puro, senza herdr: lo usa la parte `nota`, lo prova il banco
// HZ14 con node. La nota diventa una cosa da fare di Claude nel progetto delle note, con l'oggi come quando:
// Claude la trova nel pannello Da fare e a /inizio, e dalle note risale alla cartella con lo screenshot.

const due = (n) => String(n).padStart(2, "0");

// La cartella di una nota: ~/.claude/data/note-finestra/AAAA-MM-GG_HH-MM-SS.
export const cartellaNote = (home) => `${home}/.claude/data/note-finestra`;
export function cartellaNota(home, d = new Date()) {
  const quando = `${d.getFullYear()}-${due(d.getMonth() + 1)}-${due(d.getDate())}_${due(d.getHours())}-${due(d.getMinutes())}-${due(d.getSeconds())}`;
  return `${cartellaNote(home)}/${quando}`;
}

// Le misure che servono a regione(), dal layout vivo (layout() di herdr) e dalle misure che le parti riportano
// in shared arturo.misura.<parte>: divisore fra barra e lavoro, padding e gap attorno alla sessione, pannello
// Da fare nascosto, tessere di ⌘T al posto del terminale. Senza un nodo, valgono i numeri di layouts/arturo.json.
export function misureDaLayout(lay, parti, finestra) {
  const trova = (n, id) => {
    if (n?.id === id) return n;
    for (const c of n?.children ?? []) { const x = trova(c, id); if (x) return x; }
    return null;
  };
  const corpo = trova(lay, "work-body");
  return { ...parti, finestra,
    divisore: lay?.divider?.width ?? 1, padding: corpo?.padding ?? 12, gap: corpo?.gap ?? 12,
    pannello_nascosto: Boolean(trova(lay, "pannello")?.hidden),
    // Lo stack "lavoro" mostra "casa", le tessere (STACK e CASA di tessere.js: qui niente import, il banco
    // prova nota.js da sola con node).
    tessere: trova(lay, "lavoro")?.active === "casa" };
}

// Il benvenuto galleggia in cima alla sessione, 12 px sotto il bordo (herdr-app status: y 78 su main.y 66).
const MARGINE_FLOAT = 12;
const dentro = (p, r) => r && p.x >= r.x && p.x < r.x + r.larghezza && p.y >= r.y && p.y < r.y + r.altezza;
const rett = (x, y, larghezza, altezza) => ({ x, y, larghezza, altezza });

// Su quale parte della finestra cade il punto: { blocco, parte, rettangolo } coi nomi di layouts/arturo.json,
// oppure null se le misure mancano o non tornano con la finestra (la nota tiene allora solo terminale e cwd).
// A sinistra marchio, progetti e piede; a destra testata, sessione (main) col benvenuto sopra, Da fare
// (pannello) e stato. Padding e gap attorno alla sessione vanno alla parte più vicina. Misure provate
// nell'istanza di prova il 10/11/2026: 292+1+1147 = 1440 e 54+690+156 = 900, rettangoli uguali allo scatto.
export function regione(punto, m) {
  const f = m?.finestra;
  const { marchio, barra, piede, testata, stato, todo } = m ?? {};
  if (!f || !marchio || !barra || !piede || !testata || !stato || (!todo && !m.pannello_nascosto)) return null;
  const W = f.larghezza, H = f.altezza;
  const S = barra.larghezza;
  // Misure vecchie (finestra cambiata dopo l'ultimo giro delle parti): meglio nessuna regione che una sbagliata.
  if (Math.abs(marchio.altezza + barra.altezza + piede.altezza - H) > 2) return null;
  if (Math.abs(S + (m.divisore ?? 1) + testata.larghezza - W) > 2) return null;
  const p = { x: punto.x, y: punto.y };
  if (p.x < 0 || p.y < 0 || p.x >= W || p.y >= H) return null;
  const x0 = W - testata.larghezza;
  const pad = m.padding ?? 12, gap = m.gap ?? 12;
  const corpoY = testata.altezza, corpoH = H - testata.altezza - stato.altezza;
  const pannelloW = m.pannello_nascosto ? 0 : todo.larghezza;
  const mainW = testata.larghezza - 2 * pad - (pannelloW ? pannelloW + gap : 0);
  const main = rett(x0 + pad, corpoY + pad, mainW, corpoH - 2 * pad);
  const b = m.benvenuto;
  const benvenuto = b && b.larghezza > 0 && b.altezza > 0
    ? rett(main.x + Math.round((main.larghezza - b.larghezza) / 2), main.y + MARGINE_FLOAT, b.larghezza, b.altezza) : null;
  const blocchi = [
    ["marchio", "marchio", rett(0, 0, S, marchio.altezza)],
    ["progetti", "barra", rett(0, marchio.altezza, S, barra.altezza)],
    ["piede", "piede", rett(0, H - piede.altezza, S, piede.altezza)],
    ["testata", "testata", rett(x0, 0, testata.larghezza, testata.altezza)],
    ["stato", "stato", rett(x0, H - stato.altezza, testata.larghezza, stato.altezza)],
    ["benvenuto", "benvenuto", benvenuto],
    // Con le tessere di ⌘T mostrate, il posto della sessione è loro: una nota lì non va sul terminale (#5456).
    m.tessere ? ["tessere", "casa", main] : ["main", null, main],
    ["pannello", "todo", pannelloW ? rett(W - pad - pannelloW, main.y, pannelloW, main.altezza) : null],
  ];
  for (const [blocco, parte, r] of blocchi) if (dentro(p, r)) return { blocco, parte, rettangolo: r };
  // Il divisore va alla barra; padding e gap del corpo alla sessione o al pannello, il più vicino.
  if (p.x < x0) return { blocco: "progetti", parte: "barra", rettangolo: blocchi[1][2] };
  const pannello = blocchi[7][2];
  if (pannello && p.x >= main.x + main.larghezza + gap / 2) return { blocco: "pannello", parte: "todo", rettangolo: pannello };
  return m.tessere ? { blocco: "tessere", parte: "casa", rettangolo: main } : { blocco: "main", parte: null, rettangolo: main };
}

// I nomi delle parti come li legge la persona: l'etichetta del riquadro che segue il puntatore.
export const NOMI_BLOCCO = { marchio: "Marchio", progetti: "Barra dei progetti", piede: "Piede della barra",
  testata: "Testata", stato: "Barra di stato", benvenuto: "Benvenuto", main: "Sessione", pannello: "Da fare",
  tessere: "Tessere dei progetti" };

// I nomi degli elementi come li legge la persona. Un elemento è un pezzo di una parte con un id suo: la
// finestra dice dove sta (window.elements() di Volta), qui prende il nome. Prima gli id fissi, poi
// i prefissi degli id che portano una chiave (una sessione, un progetto, un todo).
// Nessun prefisso è l'inizio di un altro: l'ordine non conta.
export const NOMI_ELEMENTO = {
  nuova: "Nuova richiesta", cerca: "Cerca o chiedi", apri: "Apri un progetto", trova: "Trova i miei progetti", "progetti-elenco": "Elenco dei progetti",
  "volta-testa": "Tutte le sessioni", "volta-macchina": "Vista per macchina", "volta-progetto": "Vista per progetto",
  "volta-elenco": "Elenco delle sessioni", "volta-gesti": "Gesti della sessione", "volta-gesti-chiudi": "Chiudi i gesti",
  chiedi: "Cosa posso chiedere", settimana: "La settimana", note: "Note", guida: "Guida", impostazioni: "Impostazioni",
  "testata-titolo": "Titolo del progetto", "testata-stato": "Stato della sessione",
  dafare: "Mostra o nascondi Da fare",
  "stato-sessioni": "Sessioni aperte", "stato-aspettano": "Sessioni che ti aspettano", "stato-lavoro": "Sessioni al lavoro",
  "stato-finito": "Sessioni che hanno finito", "stato-note": "Note aperte", "stato-tasti": "Tasti",
  "todo-titolo": "Titolo di Da fare", "todo-progetto": "Progetto di Da fare", "todo-riga": "Stato del progetto",
  "todo-aggiungi": "Aggiungi un todo", partenza: "Da dove partire", "partenza-lavoraci": "Lavoraci",
  "marchio-nome": "Nome dell'app", "progetti-vuoto": "Elenco dei progetti vuoto", "dove-etichetta": "Etichetta Nasce su",
  "volta-titolo": "Titolo Tutte le sessioni", "volta-conto": "Conto delle sessioni", "volta-vuoto": "Elenco delle sessioni vuoto",
  "volta-vecchio": "Avviso di lettura vecchia", "volta-microfono": "Microfono", "volta-gesti-titolo": "Sessione dei gesti",
  "volta-gesti-avviso": "Avviso dei gesti", "todo-vuoto": "Da fare vuoto", "partenza-titolo": "Titolo Da dove partire",
  "partenza-todo": "Todo da cui partire", "partenza-motivo": "Motivo della partenza",
  "benvenuto-titolo": "Titolo del benvenuto", "benvenuto-testo": "Testo del benvenuto", "b-nuova": "Nuova richiesta",
  "casa-tessere": "Elenco delle tessere", "casa-nuova": "Tessera Nuova richiesta",
};
const PREFISSI = [
  ["todo-elenco-", "Elenco delle cose da fare"], ["scheda-", "Scheda"], ["dove-", "Dove nasce la sessione"], ["macchina-", "Macchina dove nasce la sessione"],
  ["sez-", "Titolo di sezione"], ["poi-", "Todo che viene dopo"],
  ["vgt-", "Nome del gruppo (macchina o progetto)"], ["vgn-", "Conto del gruppo"], ["vgo-", "Nota del gruppo"],
  ["vt-", "Titolo della sessione"], ["vd-", "Macchina e stato della sessione"], ["vw-", "Avviso della sessione"],
  ["pt-", "Nome del progetto"], ["ps-", "Stato del progetto"],
  ["tt-", "Testo del todo"], ["tl-", "Chi lavora al todo"], ["tq-", "Scadenza del todo"],
  ["gt-", "Nome del gruppo di todo"], ["gn-", "Conto del gruppo di todo"],
  ["st-", "Titolo del suggerimento"], ["sx-", "Testo del suggerimento"],
  ["vr-", "Riga di sessione"], ["va-", "Azioni della sessione"], ["vx-", "Togli la sessione"], ["vf-", "Sessioni ferme"],
  ["vg-", "Gesto della sessione"], ["vl-", "Anteprima della sessione"], ["v-", "Sessione"],
  ["casa-", "Tessera del progetto"], ["p-", "Progetto"], ["g-", "Gruppo di todo"], ["t-", "Cosa da fare"], ["c-", "Spunta del todo"],
  ["l-", "Lavoraci"], ["m-", "Altro sul todo"], ["s-", "Suggerimento"],
];

// Il nome di un elemento dal suo id, o null se l'id non è fra quelli di Arturo.
export function nomeElemento(id) {
  const k = String(id ?? "");
  if (Object.hasOwn(NOMI_ELEMENTO, k)) return NOMI_ELEMENTO[k];
  return PREFISSI.find(([p]) => k.startsWith(p))?.[1] ?? null;
}

// Le parti del layout e il loro blocco: la radice di ogni parte ha l'id misura-<parte> (main.js).
const RADICE = "misura-";
const PARTE_BLOCCO = { marchio: "marchio", barra: "progetti", piede: "piede", testata: "testata", todo: "pannello",
  stato: "stato", benvenuto: "benvenuto", casa: "tessere" };

// L'elemento più piccolo sotto il punto, fra quelli che la finestra riporta: { id, nome, blocco, parte,
// rettangolo } oppure null. Restano fuori gli elementi del velo stesso (own, nota-*) e quelli vuoti. A pari
// area vince chi è disegnato dopo, cioè chi sta dentro. La parte viene dalla radice della stessa vista: due
// parti possono usare lo stesso id (chiedi sta nel piede e nella testata), e il nome le distingue.
export function elementoSotto(punto, elementi) {
  if (!punto) return null;
  const validi = (elementi ?? []).filter((e) => e && typeof e.id === "string" && !e.own && !e.id.startsWith("nota-") &&
    e.width > 0 && e.height > 0);
  const sotto = validi.filter((e) => punto.x >= e.x && punto.x < e.x + e.width && punto.y >= e.y && punto.y < e.y + e.height)
    .sort((a, b) => a.width * a.height - b.width * b.height || (b.order ?? 0) - (a.order ?? 0));
  const e = sotto[0];
  if (!e) return null;
  const radice = e.id.startsWith(RADICE) ? e : validi.find((x) => x.view === e.view && x.id.startsWith(RADICE));
  const parte = radice ? radice.id.slice(RADICE.length) : null;
  const blocco = PARTE_BLOCCO[parte] ?? null;
  const nomeBlocco = blocco ? NOMI_BLOCCO[blocco] : null;
  const proprio = e === radice ? null : nomeElemento(e.id);
  const nome = proprio ? (nomeBlocco ? `${proprio} · ${nomeBlocco}` : proprio) : (nomeBlocco ?? e.id);
  return { id: e.id, nome, blocco, parte: blocco ? parte : null,
    rettangolo: rett(Math.round(e.x), Math.round(e.y), Math.round(e.width), Math.round(e.height)) };
}

// Il riquadro da disegnare attorno a ciò che sta sotto il puntatore, alla maniera di Agentation: { blocco,
// parte, elemento, nome, rettangolo, fasce, etichetta }. Prima l'elemento (riga, bottone, scheda), se la
// finestra li riporta; altrimenti la parte, da regione(). Le fasce sono i quattro rettangoli del velo
// attorno al riquadro, che resta così in piena luce. null senza elemento né regione: il velo resta intero e il clic sceglie il punto.
const ALTEZZA_ETICHETTA = 22;
export function evidenza(punto, m, elementi = []) {
  const f = m?.finestra;
  if (!punto || !f) return null;
  const r = regione(punto, m);
  const el = elementoSotto(punto, elementi);
  if (!el && !r?.rettangolo) return null;
  const q = el ? el.rettangolo : r.rettangolo, W = f.larghezza, H = f.altezza;
  const blocco = el?.blocco ?? r?.blocco ?? null;
  const fasce = [rett(0, 0, W, q.y), rett(0, q.y + q.altezza, W, H - q.y - q.altezza),
    rett(0, q.y, q.x, q.altezza), rett(q.x + q.larghezza, q.y, W - q.x - q.larghezza, q.altezza)]
    .filter((x) => x.larghezza > 0 && x.altezza > 0);
  const nome = el ? el.nome : (NOMI_BLOCCO[blocco] ?? blocco);
  // L'etichetta sta sopra il riquadro; in cima alla finestra va sotto, se il riquadro è basso (un bottone
  // resta leggibile), altrimenti dentro. A destra non esce dalla finestra: la larghezza è una stima dal nome.
  const sopra = q.y >= ALTEZZA_ETICHETTA + 2;
  const sotto = !sopra && q.altezza < 60 && q.y + q.altezza + ALTEZZA_ETICHETTA + 2 <= H;
  const larga = Math.round(String(nome).length * 6.6 + 16);
  const dentro = !sopra && !sotto;
  return { blocco, parte: el ? el.parte : r.parte, elemento: el ? { id: el.id, nome: el.nome, rettangolo: q } : null,
    nome, rettangolo: q, fasce,
    etichetta: { x: Math.max(0, Math.min(q.x, W - larga - 4 - (dentro ? 4 : 0))),
      y: sopra ? q.y - ALTEZZA_ETICHETTA - 2 : (sotto ? q.y + q.altezza + 2 : q.y + 4), dentro } };
}

// Il terminale sotto la nota, quando il punto cade sulla sessione: le ultime `n` righe non vuote del testo.
export function ultimeRighe(testo, n = 40) {
  const righe = String(testo ?? "").replace(/\r/g, "").split("\n");
  while (righe.length && !righe[righe.length - 1].trim()) righe.pop();
  return righe.slice(-n).join("\n");
}

// Il progetto a cui va la nota: quello scelto in arturo.json (note_progetto), altrimenti quello aperto.
export const progettoNota = (scelto, aperto) => (scelto || aperto || null);

// I tipi di nota, gli intenti di Agentation in italiano: le pastiglie sopra il campo, nell'ordine.
export const TIPI = [
  { id: "correggere", etichetta: "Correggere" },
  { id: "cambiare", etichetta: "Cambiare" },
  { id: "domanda", etichetta: "Domanda" },
  { id: "va-bene", etichetta: "Va bene così" },
];
export const TIPO_PREDEFINITO = "correggere";
const tipoValido = (t) => (TIPI.some((x) => x.id === t) ? t : TIPO_PREDEFINITO);
export const etichettaTipo = (t) => TIPI.find((x) => x.id === tipoValido(t)).etichetta;
// Gli stati aperti e il dove vuoto: bin/note_finestra.py ne tiene una copia, e HZ32 le confronta.
export const APERTE = new Set(["aperta", "presa"]);
export const VUOTO = { blocco: null, parte: null, elemento: null, terminale: null, titolo: null, cwd: null, testo_terminale: null };

// L'ultimo pezzo di un percorso: l'id della nota è il nome della sua cartella.
const ultimo = (c) => String(c ?? "").split(/[\\/]/).filter(Boolean).pop() ?? null;

// { dati, argv } oppure null se il testo è vuoto. argv è null senza progetto: la nota resta nella cartella.
// nota.json versione 2: id, numero fra le note aperte, tipo, dove, stato, filo delle risposte, todo.
export function nota({ testo, x, y, larghezza, altezza, progetto, cartella, schermo, quando, dove, tipo, numero }) {
  const t = String(testo ?? "").replace(/\s+/g, " ").trim();
  if (!t) return null;
  const punto = { x: Math.round(x), y: Math.round(y) };
  const finestra = { larghezza: Math.round(larghezza), altezza: Math.round(altezza) };
  const k = tipoValido(tipo);
  const dati = { versione: 2, id: ultimo(cartella), numero: Number.isInteger(numero) ? numero : 1, quando, tipo: k,
    testo: t, punto, finestra, progetto: progetto || null, schermo: schermo || null, dove: { ...VUOTO, ...(dove ?? {}) },
    stato: "aperta", chiusa_quando: null, riassunto: null, motivo: null,
    filo: [{ chi: "federico", quando, testo: t }], todo: null, screenshot: "finestra.png" };
  const breve = t.length > 110 ? t.slice(0, 110).replace(/\s+\S*$/, "") + "…" : t;
  const riga = `Tipo: ${etichettaTipo(k).toLowerCase()}. Punto ${punto.x},${punto.y} su una finestra di ${finestra.larghezza}x${finestra.altezza}` +
    (schermo ? `, schermata ${schermo}` : "") +
    (dove?.blocco ? `, parte ${dove.blocco}` : "") +
    (dove?.elemento?.id ? `, su ${dove.elemento.nome ?? dove.elemento.id} (${dove.elemento.id})` : "") + (dove?.cwd ? ` (terminale in ${dove.cwd})` : "") +
    `. Nota e screenshot in ${cartella}. Per partire: arturo note mostra ${dati.id}`;
  const argv = progetto
    ? ["aggiungi", "--progetto", progetto, "--chi", "io", "--quando", "oggi", "--note", riga, "--json", "--", `Nota sulla finestra: ${breve}`]
    : null;
  return { dati, argv };
}

// Il testo di un nota.json, versione 1 o 2, come nota versione 2; null se non si legge. Una nota versione 1
// è aperta, di tipo predefinito, senza dove, col suo testo come prima voce del filo.
export function leggiNota(testo, id) {
  let d;
  try { d = JSON.parse(testo); } catch { return null; }
  if (!d || typeof d !== "object" || !d.punto || !d.finestra || typeof d.testo !== "string") return null;
  const filo = Array.isArray(d.filo) && d.filo.length ? d.filo : [{ chi: "federico", quando: d.quando ?? null, testo: d.testo }];
  return { ...d, versione: 2, id: d.id || id, numero: Number.isInteger(d.numero) ? d.numero : null,
    tipo: tipoValido(d.tipo), dove: { ...VUOTO, ...(d.dove ?? {}) },
    stato: Object.hasOwn(STATI, d.stato) ? d.stato : "aperta",
    chiusa_quando: d.chiusa_quando ?? null, riassunto: d.riassunto ?? null, motivo: d.motivo ?? null,
    filo, todo: d.todo ?? null };
}

// Le note aperte o prese di un progetto, nell'ordine dei numeri. Una nota senza numero (versione 1) prende
// il primo libero, nell'ordine in cui è nata, così ogni segno ha un numero e due segni non lo dividono.
// Due note nate su due macchine possono avere lo stesso numero (volta_note.py le porta l'una dall'altra):
// lo tiene la più vecchia, la più nuova prende il primo libero.
export function noteAperte(lista, progetto) {
  const qui = (lista ?? []).filter((n) => n && APERTE.has(n.stato) && (n.progetto || null) === (progetto || null))
    .sort((a, b) => String(a.quando ?? a.id).localeCompare(String(b.quando ?? b.id)));
  const presi = new Set(qui.map((n) => n.numero).filter(Number.isInteger));
  const tenuti = new Set();
  let libero = 1;
  const out = qui.map((n) => {
    if (Number.isInteger(n.numero) && !tenuti.has(n.numero)) { tenuti.add(n.numero); return n; }
    while (presi.has(libero)) libero++;
    presi.add(libero);
    return { ...n, numero: libero };
  });
  return out.sort((a, b) => a.numero - b.numero);
}

// Il numero di una nota nuova: uno più del più alto fra le aperte, 1 se non ce ne sono.
export const prossimoNumero = (aperte) => (aperte ?? []).reduce((m, n) => Math.max(m, n.numero ?? 0), 0) + 1;

// Dove sta il segno di una nota sulla finestra di adesso: il punto riportato in scala se la finestra è
// cambiata, e tenuto dentro i bordi.
export function segno(n, finestra) {
  const f = n.finestra, W = finestra?.larghezza, H = finestra?.altezza;
  if (!W || !H || !f?.larghezza || !f?.altezza) return { x: n.punto.x, y: n.punto.y };
  const dentroDi = (v, max) => Math.min(Math.max(Math.round(v), 0), max - 1);
  return { x: dentroDi(n.punto.x * W / f.larghezza, W), y: dentroDi(n.punto.y * H / f.altezza, H) };
}

// Lo script che legge in un colpo tutte le note: [[id, testo di nota.json], ...], in ordine di nome. Lo
// lancia il Python di arturo.json, perché i mod di Herdr non leggono le cartelle senza un permesso.
export const LEGGI_NOTE = [
  "import json, os, sys",
  "d = sys.argv[1]",
  "o = []",
  "for n in (sorted(os.listdir(d)) if os.path.isdir(d) else []):",
  "    try:",
  "        with open(os.path.join(d, n, 'nota.json'), encoding='utf-8') as f: o.append([n, f.read()])",
  "    except OSError: pass",
  "print(json.dumps(o))",
].join("\n");

// L'elenco delle note (⌘⇧E, noteui.js). L'età di una nota: "adesso", "12 min fa", "3 ore fa", "ieri",
// "4 giorni fa"; vuota se una delle due date non si legge.
export function eta(quando, ora) {
  const t = Date.parse(quando ?? ""), n = ora instanceof Date ? ora.getTime() : Date.parse(ora ?? "");
  if (!Number.isFinite(t) || !Number.isFinite(n)) return "";
  const min = Math.max(0, Math.floor((n - t) / 60000));
  if (min < 1) return "adesso";
  if (min < 60) return `${min} min fa`;
  const ore = Math.floor(min / 60);
  if (ore < 24) return ore === 1 ? "1 ora fa" : `${ore} ore fa`;
  const g = Math.floor(ore / 24);
  return g === 1 ? "ieri" : `${g} giorni fa`;
}

export const STATI = { aperta: "Aperta", presa: "Claude ci lavora", risolta: "Risolta", scartata: "Scartata" };
const vociClaude = (n) => (n.filo ?? []).filter((v) => v.chi === "claude");

// Le righe dell'elenco per un progetto: prima le aperte coi numeri dei segni, poi, con filtro "tutte", le
// chiuse dalla più recente. Una chiusa non ha numero: il suo l'ha già ripreso una nota nuova.
export function righeElenco(lista, progetto, filtro, ora) {
  const qui = (lista ?? []).filter((n) => n && (n.progetto || null) === (progetto || null));
  const recente = (n) => String(n.chiusa_quando ?? n.quando ?? n.id);
  const chiuse = filtro === "tutte"
    ? qui.filter((n) => !APERTE.has(n.stato)).sort((a, b) => recente(b).localeCompare(recente(a))) : [];
  return [...noteAperte(qui, progetto), ...chiuse].map((n) => {
    const aperta = APERTE.has(n.stato);
    const claude = vociClaude(n);
    return { id: n.id, numero: aperta ? n.numero : null, aperta, stato: n.stato, etichettaStato: STATI[n.stato],
      tipo: etichettaTipo(n.tipo), testo: n.testo, risposta: claude.length ? claude[claude.length - 1].testo : null,
      chiusura: n.riassunto ?? n.motivo ?? null, filo: n.filo ?? [],
      eta: eta(aperta ? n.quando : (n.chiusa_quando ?? n.quando), ora) };
  });
}

// Quante note ha un progetto: { aperte, tutte }.
export function contaNote(lista, progetto) {
  const qui = (lista ?? []).filter((n) => n && (n.progetto || null) === (progetto || null));
  return { aperte: qui.filter((n) => APERTE.has(n.stato)).length, tutte: qui.length };
}

// Le risposte di Claude già viste, per nota: { id: quante }. Le note con più risposte di prima sono quelle
// da annunciare; alla prima lettura (prima null) nessuna, se no ogni avvio annuncerebbe tutto.
export const risposteClaude = (lista) => Object.fromEntries((lista ?? []).map((n) => [n.id, vociClaude(n).length]));
export function risposteNuove(prima, lista) {
  if (!prima) return [];
  return (lista ?? []).filter((n) => vociClaude(n).length > (prima[n.id] ?? 0));
}
