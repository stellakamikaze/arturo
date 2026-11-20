// Volta: le sessioni di Claude di tutte le macchine, come le scrive volta_sonda.py volta.
// Modulo puro, senza herdr: raggruppa, ordina, scrive le frasi e decide cosa fa un clic.
// Lo prova il banco HZ17-HZ19 con node (tests/test_herdr_2026_11_08.py).
//
// Una riga del file (~/.cache/volta/sessioni.json, campo "sessioni"):
// { macchina, host, questa, sessionId, id, nome, progetto, titolo, stato: aspetta|lavora|ferma|errore,
//   tipo: background|interattiva, attach: argv | null, cartella, ultimo, risposta, azione, vecchia?,
//   daPortare?: il nome scritto dalla persona che Claude Code non ha ancora (rinomina, #5292),
//   daIniziare?: il progetto dato dalla persona da cui la sessione non è ancora ripartita (/inizio, #5465),
//   carta?: la carta della Coda (#5719) { tipo, fonte, quando, esito, domanda, opzioni, raccomandazione,
//   prove, link, menu }, scritta da hooks/carta-sessione.py quando la sessione chiede qualcosa }

export const MODI = { macchina: "Per macchina", progetto: "Per progetto" };
export const SENZA = "Senza progetto";

// Il riquadro dei gesti di "Altro" sta sotto l'elenco con al più 160 px: un'anteprima lunga scorre lì
// dentro. L'elenco prende il resto della colonna (12/11/2026: niente più tetto, la sezione dei progetti
// aperti non c'è più).
export const GESTI_MAX = 160;

const tempo = (s) => Date.parse(s.ultimo || "") || 0;

// La chiave di una sessione (#5634, 14/11/2026): macchina e id insieme. Dopo Sposta su lo stesso id c'è su
// due macchine, e un /clear cambia il sessionId: schede, congedi e mappe di volta.js passano da qui.
export const chiave = (s) => `${s?.host ?? "qui"}:${s?.id ?? ""}`;
// L'id `id` sta su più di una macchina dell'elenco `l`.
export const doppio = (l, id) => new Set((l ?? []).filter((x) => x?.id === id).map((x) => x.host ?? "qui")).size > 1;
// Le chiavi delle sessioni di una mappa ({ chiave: c }): le chiavi e quelle delle voci con id. Così vale
// anche una voce scritta prima del 14/11, quando le mappe andavano per sessionId.
export const chiaviDi = (m) => new Set([...Object.keys(m ?? {}), ...Object.values(m ?? {}).filter((c) => c?.id).map(chiave)]);
// La riga di `l` che è la sessione `c`: per chiave se `c` ha l'id, altrimenti per sessionId (e macchina,
// se `c` la dice).
export const trova = (l, c) => (l ?? []).find((x) => (c?.id ? chiave(x) === chiave(c)
  : Boolean(c?.sessionId) && x.sessionId === c.sessionId && (c.host == null || (x.host ?? "qui") === c.host))) ?? null;

// I progetti noti, da shared arturo.progetti della barra: { slug o nome alternativo: { chiave, titolo } }.
// Il titolo vero ("Volta", "Post Office") sta nella scheda del progetto (arturo progetti, campo titolo:) o
// nella fonte dei task; un nome alternativo porta alla chiave del suo progetto. Ogni parte del mod gira
// in una sua copia: chi mostra nomi di progetto li imposta prima del disegno (progettiNoti di volta.js e
// cambio.js). Senza, vale il nome ricavato dallo slug.
let NOTI = {};
export function impostaProgetti(mappa) { NOTI = mappa && typeof mappa === "object" ? mappa : {}; }
// Lo slug come lo fa Arturo: minuscole senza accenti, lettere, numeri e trattini. Una copia sola: dati.js
// la riesporta.
export const slug = (p) => String(p ?? "").toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, "").replace(/[^a-z0-9-]+/g, "-").replace(/^-+|-+$/g, "");
const slugDi = slug;

// Il progetto di un nome (il progetto di una sessione, il nome di uno spazio di Herdr, una tessera): la
// chiave del suo progetto e il titolo noto, o null (#5487). Un nome alternativo ("volta", "volta-celeste")
// porta alla chiave della scheda ("volta"): colonna, spazi, testata, Da fare e tessere passano tutti
// da qui, così una sessione e il suo spazio non si separano. `noti` è la mappa di shared arturo.progetti:
// chi non chiama impostaProgetti (dati.js, testata.js) la passa letta da shared.
export function progettoDi(p, noti = NOTI) {
  const k = slug(p);
  const n = k ? noti?.[k] : null;
  return { chiave: n?.chiave ?? k, titolo: n?.titolo ?? null };
}
// La chiave del progetto: quella del suo gruppo anche quando la sessione porta un nome alternativo.
export const chiaveProgetto = (p) => progettoDi(p).chiave;
// Il titolo vero del progetto se è noto ("Volta" per volta), altrimenti null: chi ha un suo modo
// di scrivere il nome ricavato dallo slug (bello() di dati.js) lo usa solo quando il titolo manca.
export const titoloNoto = (p) => progettoDi(p).titolo;
// Il nome di un gruppo "Per progetto" apre il progetto (/inizio) solo se il progetto è noto: un nome
// nato da una cartella che non è un progetto ("arturo-inizio-5465", un worktree) aprirebbe una sessione
// su un progetto che non esiste (12/11/2026). Senza elenco dei progetti non si sa: resta apribile.
export const progettoApribile = (p) => Boolean(p) && (Object.keys(NOTI).length === 0 || Boolean(NOTI[slugDi(p)]));

// Il nome di un progetto per le persone: il titolo noto, altrimenti "due-mondi" → "Due mondi", "uf" → "UF".
// Un progetto fatto di soli separatori ("-") non ha parole: vale come senza progetto, invece di far
// cadere la barra.
export function nomeProgetto(p) {
  const s = String(p ?? "").trim();
  if (!s) return SENZA;
  const noto = NOTI[slugDi(s)]?.titolo;
  if (noto) return noto;
  if (/[A-Z]/.test(s)) return s;
  const t = s.split(/[-_\s]+/).filter(Boolean).map((w) => (w.length <= 2 ? w.toUpperCase() : w)).join(" ");
  return t ? t[0].toUpperCase() + t.slice(1) : SENZA;
}

// Un nome di Claude è automatico se manca, se è l'id, oppure se è "<cartella>-xx": l'ultimo pezzo della
// cartella della sessione più due cifre esadecimali ("claudecode-8e" in C:\Users\x\Documents\ClaudeCode).
// Il confronto guarda solo lettere e numeri, in minuscolo. Un nome scritto dalla persona che finisce allo
// stesso modo ("bando-57") non è automatico. Senza la cartella vale la sola forma del nome.
const piatto = (x) => String(x ?? "").toLowerCase().replace(/[^a-z0-9]/g, "");
export function nomeAutomatico(s) {
  const nome = String(s?.nome ?? "").trim();
  if (!nome || nome === s.id) return true;
  const m = /^([\w.-]+)-[0-9a-f]{2}$/.exec(nome);
  if (!m) return false;
  const ultimo = String(s.cartella ?? "").split(/[\\/]+/).filter(Boolean).pop();
  return ultimo ? piatto(m[1]) === piatto(ultimo) : true;
}

// Il titolo di una sessione. Prima quello che hooks/titolo-sessione.py scrive a fine turno (poche
// parole in italiano sul lavoro in corso, campo "titolo"). Senza, il nome di Claude; i nomi automatici
// ("claudecode-ca": cartella più due lettere, nomeAutomatico) non dicono niente: al loro posto la prima
// riga dell'ultima risposta.
export function titolo(s) {
  const scritto = String(s.titolo ?? "").replace(/\s+/g, " ").trim();
  if (scritto) return scritto;
  const nome = String(s.nome ?? "").trim();
  if (!nomeAutomatico(s)) return nome;
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

// Le fasi di una sessione (#5366, nota di Federico dell'11/11: "le ferme devono essere diverse").
// "ferma" della sonda tiene insieme due casi: Claude ha chiuso il turno chiedendo qualcosa alla persona
// (stasi: ti aspetta) oppure ha finito e aspetta un comando nuovo (attesa). Lo dice la fine dell'ultimo
// testo di Claude (campo coda). Nel dubbio vale stasi: una sessione in stasi non si chiude da sola.
// "Prossimo passo:" conta solo se la mossa è della persona ("tu", "Federico"); "Niente da fare per te" no.
const CHIEDE = [
  /\?[\s*_`)]*$/,
  /\?\s*\n/,
  /^\s*!\s*\S/m,
  /\b(scrivimi|scrivi|dimmi|dimmelo|rispondi|rispondimi|fammi sapere|conferma|confermi|scegli|decidi|lancia|tocca a te|serve il tuo|il tuo s[iì]|aspetto la tua|attendo la tua)\b/i,
  /prossimo passo:[^\n]*(\btu\b|\btuo\b|\btua\b|\bfederico\b|\(tu\))/i,
];
export function chiede(coda) {
  const c = String(coda ?? "").slice(-220);
  return CHIEDE.some((re) => re.test(c));
}

// Un lavoro lasciato in corso: Claude aspetta l'esito di qualcosa che gira da solo (un comando in
// background, un altro agente) e riprenderà da sé. Una sessione così non va chiusa, anche se tace.
const IN_CORSO = /\b(in background|appena finisce|quando finisce|appena arriva|ti aggiorno|ti avviso|riprendo da solo|aspetto (l'esito|il risultato|che finisca))\b/i;
export const lavoroInCorso = (coda) => IN_CORSO.test(String(coda ?? "").slice(-220));

// "attiva" (lavora), "stasi" (ti aspetta), "attesa" (aspetta un comando), "errore", "chiusa".
export function fase(s) {
  if (!s || chiusa(s)) return "chiusa";
  if (s.stato === "errore") return "errore";
  if (s.stato === "lavora") return "attiva";
  if (s.stato === "aspetta" || s.aspetta) return "stasi";
  // la carta della Coda (#5719) è il segno forte: la sessione ha chiesto qualcosa e nessuno ha risposto
  if (s.carta) return "stasi";
  // l'ultima parola non è un testo di Claude (un messaggio senza risposta, un comando interrotto,
  // nessuna trascrizione): nel dubbio, ti aspetta
  if (s.chi !== "claude" || chiede(s.coda)) return "stasi";
  return "attesa";
}

// L'ora dell'ultimo messaggio vero; una riga di una sonda di prima ha solo "ultimo".
const interazione = (s) => Date.parse(s?.interazione || s?.ultimo || "") || 0;

// La frase di stato e il colore del tema (blocked, working, done, idle, muted, dim).
export function fraseStato(s, adesso = Date.now()) {
  if (s.vecchia) return { testo: "Ultima lettura: la macchina non risponde", colore: "dim" };
  // la ripresa da sola (#5882): l'errore e l'ora della ripresa al posto della fase; dopo, una coda alla fase
  const r = fraseRipresa(s, adesso);
  if (r?.colore) return r;
  const f0 = fraseFase(s, adesso);
  return r ? { testo: `${f0.testo} · ${r.testo}`, colore: f0.colore } : f0;
}
function fraseFase(s, adesso) {
  const f = fase(s);
  if (f === "attiva") return { testo: "Sta lavorando", colore: "working" };
  if (f === "errore") return { testo: "Si è fermata con un errore", colore: "blocked" };
  const q = daQuanto(s.interazione || s.ultimo, adesso);
  // addormentata (#5495): il servizio di Claude l'ha ritirata, il clic o il giro la riprendono
  const zz = dorme(s) ? ", addormentata" : "";
  if (f === "stasi" && chiestaInFine(s)) return { testo: q ? `Ha chiesto qualcosa durante /fine ${q}` : "Ha chiesto qualcosa durante /fine", colore: "blocked" };
  if (f === "stasi") return { testo: (q ? `Ti aspetta ${q}` : "Ti aspetta") + zz, colore: "blocked" };
  if (zz) return { testo: q ? `Addormentata ${q}` : "Addormentata", colore: "dim" };
  return { testo: q ? `Aspetta un comando ${q}` : "Aspetta un comando", colore: "muted" };
}

// La Coda (#5719, piano della Coda di Volta, 15/11/2026): una carta per ogni cosa che aspetta la persona.
// Le carte vengono dalle sessioni in stasi di una macchina che risponde: con la carta di
// hooks/carta-sessione.py, oppure con la carta minima letta da risposta e coda, così entrano anche le
// sessioni di una macchina senza l'hook. Una sessione che lavora o è in errore non ha carta.
// Le categorie umane di A20 (CHI_TU di pm/progetti/indice.py) come le scrive hooks/carta-sessione.py.
// "permesso" (20/11/2026): un permesso che il giudice dei permessi (hooks/giudice-permessi.py) lascia alla persona.
export const UMANI = ["invio", "pagamento", "segreto", "otp", "oauth", "gesto", "permesso"];
const pulita = (r, n) => {
  const t = String(r ?? "").replace(/[*_`#>]+/g, "").replace(/\s+/g, " ").replace(/^[\s\-·:]+|[\s\-·:]+$/g, "");
  return t.length <= n ? t : `${t.slice(0, n - 1).trimEnd()}…`;
};
const righeDi = (t) => String(t ?? "").split("\n").filter((r) => r.trim());
// La carta minima: esito dalla prima riga dell'ultimo testo, domanda dall'ultima riga con "?" fra le
// ultime otto (altrimenti l'ultima), opzioni dal grassetto dell'ultima riga, come carta-sessione.py.
// Una sessione ferma su un permesso ha per domanda il permesso: il testo di prima non c'entra.
export function cartaMinima(s) {
  const rr = righeDi(s?.coda);
  const ultima = rr[rr.length - 1] ?? "";
  const domanda = pulita([...rr.slice(-8)].reverse().find((r) => r.includes("?")) ?? ultima, 600);
  const opzioni = [...new Set([...ultima.matchAll(/\*\*(.+?)\*\*/g)].map((m) => pulita(m[1], 80)).filter(Boolean))].slice(0, 6);
  const permesso = s?.aspetta ? `Aspetta: ${pulita(s.aspetta, 80)}` : "";
  return { tipo: "scelta", fonte: "minima", quando: 0, esito: pulita(righeDi(s?.risposta)[0], 200),
    domanda: permesso || domanda || "Ti aspetta", opzioni, raccomandazione: "", prove: [], link: [], menu: false };
}
export function carte(lista) {
  return (lista ?? []).filter((s) => s && !s.vecchia && fase(s) === "stasi").map((s) => {
    const c = s.carta && typeof s.carta === "object" ? s.carta : cartaMinima(s);
    const quando = (Number(c.quando) > 0 ? Number(c.quando) * 1000 : 0) || interazione(s);
    return { ...c, opzioni: Array.isArray(c.opzioni) ? c.opzioni : [], origine: "sessione",
      chiave: chiave(s), id: s.id, sessionId: s.sessionId, host: s.host ?? "qui", macchina: s.macchina,
      progetto: s.progetto ?? null, titolo: titolo(s), quando,
      minima: !s.carta, blocco: s.stato === "aspetta" || Boolean(s.aspetta),
      // la ripartenza di /inizio (17/11/2026): la carta offre la checklist con le note
      checklist: vociRipartenza(s.ripartenza).length, ripQuando: s.ripartenza?.quando ?? null };
  });
}
// L'ordine della Coda: prima ciò che solo la persona fa (invio, pagamento, segreto...), poi le sessioni
// bloccate (un permesso, una domanda aperta), le scelte con la carta, quelle con la carta minima, le
// review, i task UF "tocca a te" e "decidi tu" (origine "uf", gruppo "tu"|"decidi", step 5 del piano).
// A parità vince la più vecchia: aspetta da più tempo.
export const RANGHI = ["umano", "blocco", "scelta", "minima", "review", "tu", "decidi"];
export function rangoCarta(c) {
  if (c?.origine === "uf") return RANGHI.indexOf(c.gruppo === "tu" ? "tu" : "decidi");
  if (UMANI.includes(c?.tipo)) return RANGHI.indexOf("umano");
  if (c?.blocco) return RANGHI.indexOf("blocco");
  if (c?.tipo === "review") return RANGHI.indexOf("review");
  return RANGHI.indexOf(c?.minima ? "minima" : "scelta");
}
export function ordineCoda(lista) {
  return (lista ?? []).filter(Boolean).map((c, i) => ({ c, i, r: rangoCarta(c), q: Number(c.quando) || Infinity }))
    .sort((a, b) => a.r - b.r || a.q - b.q || a.i - b.i).map((x) => x.c);
}

// La vista Coda (#5720, step 3 del piano): una carta per volta, risposta in un tasto. Qui stanno le
// decisioni senza Herdr (coda.js disegna): quale opzione è la raccomandata, cosa fa un tasto, dove va una
// prova. Al più CODA_OPZIONI opzioni, come i tetti della sonda.
export const CODA_OPZIONI = 6;
const piana = (t) => String(t ?? "").toLowerCase().replace(/[*_`"'.!?:;,()]+/g, " ").replace(/\s+/g, " ").trim();
// L'indice dell'opzione che la raccomandazione indica, o -1: prima l'opzione uguale, poi quella che la
// raccomandazione nomina per intero ("1 tutte" in "Raccomando 1 tutte perché..."), la più lunga.
export function raccomandata(c) {
  const r = piana(c?.raccomandazione);
  const oo = (Array.isArray(c?.opzioni) ? c.opzioni : []).slice(0, CODA_OPZIONI).map(piana);
  if (!r || !oo.length) return -1;
  const uguale = oo.indexOf(r);
  if (uguale >= 0) return uguale;
  const dentro = oo.map((o, i) => ({ o, i })).filter((x) => x.o && ` ${r} `.includes(` ${x.o} `))
    .sort((a, b) => b.o.length - a.o.length);
  return dentro.length ? dentro[0].i : -1;
}
// Cosa fa il tasto `k` (nome di Herdr: "1", "enter", "escape", "right", "t") sulla carta `c`:
// { azione: "rispondi", testo, scelta, accettata } | { azione: "salta"|"indietro"|"apri"|"esci"|"scrivi" } | null.
// Invio accetta la raccomandazione: l'opzione che indica, oppure il suo testo se non ne indica nessuna.
export function tastoCoda(k, c) {
  const oo = (Array.isArray(c?.opzioni) ? c.opzioni : []).slice(0, CODA_OPZIONI);
  const ri = raccomandata(c);
  if (/^[1-6]$/.test(k ?? "")) {
    const n = Number(k) - 1;
    if (!c || n >= oo.length) return null;
    return { azione: "rispondi", testo: String(oo[n]), scelta: n + 1, accettata: n === ri };
  }
  if (k === "enter") {
    if (!c) return null;
    if (ri >= 0) return { azione: "rispondi", testo: String(oo[ri]), scelta: ri + 1, accettata: true };
    const r = String(c.raccomandazione ?? "").trim();
    return r ? { azione: "rispondi", testo: r, scelta: 0, accettata: true } : null;
  }
  if (k === "right" || k === "down") return { azione: "salta" };
  if (k === "left" || k === "up") return { azione: "indietro" };
  if (k === "t") return c ? { azione: "apri" } : null;
  // i gesti di ogni carta (16/11/2026): F Già fatto, X Scarta, N Note (R resta la sua vecchia lettera),
  // C il commento sul pulsante sotto il cursore (Tab lo prende il motore per spostare il fuoco)
  if (k === "r" || k === "n") return c ? { azione: "scrivi" } : null;
  if (k === "f") return c ? { azione: "gesto", gesto: GIA_FATTO } : null;
  if (k === "x") return c ? { azione: "gesto", gesto: SCARTA } : null;
  if (k === "c") return c ? { azione: "commenta" } : null;
  if (k === "escape") return { azione: "esci" };
  return null;
}
// La Coda come elenco (18/11/2026, Federico: "non mi permette di capire chiaramente quali sono le cose
// pending, come nella schermata Su cosa lavorare"): i gruppi per chi agisce, come la checklist, e dentro
// l'ordine di ordineCoda. Un gruppo vuoto non c'è. Torna [{ chiave, nome, carte }].
export const GRUPPI_CODA = [
  ["sessioni", "Sessioni che ti aspettano"],
  ["bozze", "Bozze da mandare"],
  ["tu", "Tocca a te"],
  ["decidi", "Decidi tu"],
];
export function gruppoCarta(c) {
  if (c?.origine !== "uf") return "sessioni";
  if (c.fonte === "bozza") return "bozze";
  return c.gruppo === "tu" ? "tu" : "decidi";
}
export function gruppiCoda(lista) {
  const per = new Map(GRUPPI_CODA.map(([k]) => [k, []]));
  for (const c of lista ?? []) if (c) per.get(gruppoCarta(c)).push(c);
  return GRUPPI_CODA.map(([chiave, nome]) => ({ chiave, nome, carte: per.get(chiave) })).filter((g) => g.carte.length);
}
// Le carte nell'ordine in cui l'elenco le mostra, senza i gruppi chiusi: è l'ordine delle frecce.
export const ordineVisto = (gruppi, chiusi = new Set()) => (gruppi ?? []).flatMap((g) => (chiusi.has(g.chiave) ? [] : g.carte));
// L'Orchestratore (Fase 2 del piano del 20/11/2026, #6185): la Coda diventa il posto da cui si guidano tutte le
// sessioni. In cima le sessioni per stato, sotto i gruppi di prima (bozze, tocca a te, decidi tu), in fondo i
// permessi approvati da Arturo oggi, chiusi di serie. Le chiuse e le addormentate restano fuori. Le righe di
// sessione hanno `vista: "sessione"`, quelle dei permessi `vista: "giudizio"`; una carta non ha `vista`.
export const GRUPPI_ORCHESTRA = [
  ["aspettano", "Ti aspettano"],
  ["lavorano", "Lavorano"],
  ["comando", "Aspettano un comando"],
  ["errori", "Errori"],
  ["bozze", "Bozze da mandare"],
  ["tu", "Tocca a te"],
  ["decidi", "Decidi tu"],
  ["approvati", "Approvati da Arturo (oggi)"],
];
export const CHIUSI_DI_SERIE = ["approvati"];
// Al più tanti permessi approvati nel gruppo in fondo: i più recenti.
export const APPROVATI_MAX = 20;
// Le righe di sessione per l'Orchestratore, da vis(): senza chiuse e addormentate, con la fase, la frase di
// stato e i permessi approvati oggi. volta.js le pubblica in shared arturo.orchestra.
export function righeOrchestra(sessioni, adesso = Date.now()) {
  return (sessioni ?? []).filter((s) => s && !chiusa(s) && !dorme(s)).map((s) => ({
    vista: "sessione", chiave: `s:${chiave(s)}`, sessione: chiave(s), host: s.host ?? "qui", macchina: s.macchina ?? null,
    progetto: s.progetto ?? null, titolo: titolo(s), fase: fase(s), frase: fraseStato(s, adesso),
    azione: String(s.azione ?? "").replace(/\s+/g, " ").trim().slice(0, 160), quando: interazione(s),
    vecchia: Boolean(s.vecchia), giudizi: s.giudizi && typeof s.giudizi === "object" ? s.giudizi : null,
  }));
}
// I permessi approvati oggi da tutte le sessioni, dal più recente: una riga per permesso.
export function righeApprovati(righe) {
  const out = [];
  for (const r of righe ?? []) {
    for (const g of r?.giudizi?.ultimi ?? []) {
      if (g?.decisione !== "si") continue;
      const q = Number(g.quando) || 0;
      out.push({ vista: "giudizio", chiave: `g:${r.sessione}:${q}`, sessione: r.sessione, host: r.host, macchina: r.macchina,
        progetto: r.progetto, titolo: String(g.riga ?? ""), motivo: String(g.motivo ?? ""), quando: q * 1000, di: r.titolo });
    }
  }
  return out.sort((a, b) => b.quando - a.quando).slice(0, APPROVATI_MAX);
}
// Quanti permessi Arturo ha approvato oggi, su tutte le sessioni (anche le chiuse: il conto è della giornata).
export const siOggi = (sessioni) => (sessioni ?? []).reduce((n, s) => n + (Number(s?.giudizi?.si) || 0), 0);
// Il gruppo di una riga di sessione. Una sessione in stasi ha la sua carta in "Ti aspettano"; se la carta non
// c'è più (risposta o scartata) aspetta un comando. Una macchina che non risponde: l'ultima fase letta.
export function gruppoSessione(r, inCoda = new Set()) {
  if (r.fase === "attiva") return "lavorano";
  if (r.fase === "errore") return "errori";
  if (r.fase === "stasi" && inCoda.has(r.sessione)) return null;
  return "comando";
}
// I gruppi dell'Orchestratore: `carte` come shared arturo.coda (già in ordine), `righe` come righeOrchestra.
// Dentro i gruppi di sessione la più recente prima. Un gruppo vuoto non c'è. Torna [{ chiave, nome, carte }].
export function gruppiOrchestra(carte, righe) {
  const per = new Map(GRUPPI_ORCHESTRA.map(([k]) => [k, []]));
  const inCoda = new Set();
  for (const c of carte ?? []) {
    if (!c) continue;
    const g = gruppoCarta(c);
    per.get(g === "sessioni" ? "aspettano" : g).push(c);
    if (c.origine === "sessione") inCoda.add(c.chiave);
  }
  const ss = [...(righe ?? [])].filter(Boolean).sort((a, b) => (b.quando || 0) - (a.quando || 0));
  for (const r of ss) {
    const g = gruppoSessione(r, inCoda);
    if (g) per.get(g).push(r);
  }
  per.set("approvati", righeApprovati(righe));
  return GRUPPI_ORCHESTRA.map(([chiave, nome]) => ({ chiave, nome, carte: per.get(chiave) })).filter((g) => g.carte.length);
}
// Lo stato del giudice sulle macchine che lo dicono (campo `giudice` della voce di macchina della sonda):
// { accese, spente, testo } con testo "decide Arturo", "decidi tu" o "decide Arturo su 2 di 3 macchine".
// null se nessuna macchina lo dice (una sonda di prima).
export function statoGiudice(macchine) {
  const mm = (macchine ?? []).filter((m) => m && (m.giudice === "acceso" || m.giudice === "spento"));
  if (!mm.length) return null;
  const accese = mm.filter((m) => m.giudice === "acceso").length, spente = mm.length - accese;
  const testo = !spente ? "decide Arturo" : !accese ? "decidi tu" : `decide Arturo su ${accese} di ${mm.length} macchine`;
  return { accese, spente, testo };
}
// Il tasto G: spegne se il giudice è acceso su almeno una macchina, altrimenti accende.
export const giudiceDopo = (stato) => (stato && stato.accese > 0 ? "spento" : "acceso");
// Cosa fa un tasto sulla riga `c` dell'Orchestratore. Una riga di sessione o di permesso si apre con Invio o T;
// le frecce e Esc come sulla Coda; G accende o spegne il giudice su ogni riga. Il resto vale per le carte
// (tastoCoda).
export function tastoOrchestra(k, c) {
  if (k === "g") return { azione: "giudice" };
  if (!c?.vista) return tastoCoda(k, c);
  if (k === "enter" || k === "t") return { azione: "apri" };
  if (k === "right" || k === "down") return { azione: "salta" };
  if (k === "left" || k === "up") return { azione: "indietro" };
  if (k === "escape") return { azione: "esci" };
  return null;
}
// La riga sotto il titolo di una sessione dell'Orchestratore: progetto · macchina · da quanto · ultima azione.
// Su una sessione che non lavora l'ultima azione non serve: c'è la frase di stato.
export function dettaglioRiga(r, nomeMacchina = (h) => h, adesso = Date.now()) {
  const quanto = r.quando ? daQuanto(new Date(r.quando).toISOString(), adesso) : "";
  const az = r.fase === "attiva" ? r.azione : "";
  return [r.progetto ? nomeProgetto(r.progetto) : "Senza progetto", nomeMacchina(r.host), quanto, az].filter(Boolean).join(" · ");
}

// La carta davanti dopo un salto: in giro, così dall'ultima si torna alla prima.
export const passoCoda =(at, verso, n) => (n > 0 ? (((Number(at) || 0) + verso) % n + n) % n : 0);
// La carta da mostrare: la stessa di prima se c'è ancora (per chiave), altrimenti quella al suo posto.
export function cartaDavanti(lista, chiavePrima, at) {
  const l = lista ?? [];
  if (!l.length) return 0;
  const i = chiavePrima ? l.findIndex((c) => c?.chiave === chiavePrima) : -1;
  return i >= 0 ? i : Math.max(0, Math.min(Number(at) || 0, l.length - 1));
}
// Le prove di una carta: le immagini si mostrano nella vista, i video si aprono col programma del sistema.
export const tipoProva = (p) => (/\.(png|jpe?g|gif|webp)$/i.test(String(p ?? "")) ? "immagine" : /\.(mp4|mov)$/i.test(String(p ?? "")) ? "video" : null);
// Dove arriva la copia di una prova, relativa alla cartella dell'app: Herdr mostra solo le immagini che
// stanno lì dentro (gpui-kit assets.rs). Una cartella per macchina e sessione, il nome del file ripulito.
export function copiaProva(c, p) {
  const pulito = (x) => String(x ?? "").replace(/[^0-9A-Za-z._-]+/g, "_").replace(/^\.+/, "_").slice(0, 80) || "_";
  const nome = String(p ?? "").split(/[\\/]/).filter(Boolean).pop();
  if (!nome || !tipoProva(nome)) return null;
  return `carte/${pulito(c?.host ?? "qui")}/${pulito(String(c?.sessionId || c?.id || "").slice(0, 36))}/${pulito(nome)}`;
}
// Una copia delle prove fallita si riprova (#6112, 19/11/2026): prima l'errore restava per sempre, e la prova
// non arrivava più finché Volta non ripartiva, anche dopo che la macchina era tornata. Al più PROVA_TENTATIVI
// copie per prova, l'una PROVA_RIPROVA_MS dopo l'errore dell'altra. `esito` è "copio", "ok" o l'errore;
// `giro` è { n, dopo }: le copie partite e l'ora da cui si può riprovare.
export const PROVA_TENTATIVI = 3;
export const PROVA_RIPROVA_MS = 30000;
export function daCopiare(esito, giro, ora = Date.now()) {
  if (!esito) return true;
  if (esito === "copio" || esito === "ok") return false;
  return (giro?.n ?? 0) < PROVA_TENTATIVI && ora >= (giro?.dopo ?? 0);
}
// La risposta della Coda torna alla barra come comando (lo stesso di herdr-app do), col testo in
// esadecimale: "arturo.coda-rispondi-<chiave>-<esadecimale>". Al più TESTO_NUOVA_MAX caratteri.
export const comandoRisposta = (chiaveCarta, testo, tetto = TESTO_NUOVA_MAX) => `arturo.coda-rispondi-${chiaveCarta}-${codifica(String(testo ?? "").trim().slice(0, tetto))}`;
// Il testo di una carta come si legge: un link markdown "[testo](url)" resta il solo testo, o l'indirizzo se
// il testo è "link"; via il grassetto e il codice. Il testo scritto dall'hook è markdown di Claude.
export const testoPiano = (t) => String(t ?? "")
  .replace(/\[([^\]]*)\]\((\S+?)\)/g, (_m, x, u) => (!x.trim() || /^(link|qui)$/i.test(x.trim()) ? u : x))
  .replace(/\*\*(.+?)\*\*/g, "$1").replace(/`([^`]+)`/g, "$1");
// L'etichetta dell'opzione `i` (da 0): senza il numero davanti se è già il suo ("1 tutte" accanto al tasto 1).
// La risposta che torna alla sessione resta il testo intero.
export const etichettaOpzione = (o, i) => testoPiano(o).replace(new RegExp(`^\\s*${i + 1}[\\s.):-]+(?=\\S)`), "");
// Il conteggio della testata: "Coda · 3", o null con la coda vuota.
export const rigaCoda = (n) => (Number(n) > 0 ? `Coda · ${Number(n)}` : null);

// La risposta della Coda torna alla sessione (#5721, step 4 del piano). Il canale, dalla sessione `s`,
// dalla sua carta `c` e dal numero di schede che la mostrano in questa finestra:
//   dialogo    la sessione è ferma in un dialogo (AskUserQuestion, un permesso): si apre la sua scheda,
//              perché un testo scritto o uno stop perderebbero la domanda;
//   scheda     una scheda qui la mostra: la risposta si scrive lì, a casella vuota (scriviComando);
//   background nessuna scheda: volta_sonda.py rispondi, cioè claude stop e la stessa conversazione ripresa
//              con la risposta come prompt;
//   apri       un'interattiva in un Terminale fuori da Herdr: non si raggiunge, si apre e si dice il testo.
export function canaleRisposta(s, c, schede = 0) {
  if (!s) return "apri";
  if (c?.menu || c?.blocco || s.stato === "aspetta" || s.aspetta) return "dialogo";
  if (Number(schede) > 0) return "scheda";
  if (s.tipo === "background" && s.id && s.sessionId) return "background";
  return "apri";
}
// Quale opzione è la risposta `testo` sulla carta `c` e se segue la raccomandazione: { numero, accettata }.
// numero 0 = una risposta libera o la raccomandazione senza un'opzione. Per il registro delle risposte.
export function sceltaRisposta(c, testo) {
  const t = piana(testo);
  const oo = (Array.isArray(c?.opzioni) ? c.opzioni : []).slice(0, CODA_OPZIONI).map(piana);
  const i = t ? oo.indexOf(t) : -1;
  if (i >= 0) return { numero: i + 1, accettata: i === raccomandata(c) };
  const r = piana(c?.raccomandazione);
  return { numero: 0, accettata: Boolean(r) && r === t };
}
// La riga del registro delle risposte (volta_carte.py risposta), senza il testo della domanda.
export function rigaRisposta(c, testo, canale, esito, errore = null, nota = "") {
  const { numero, accettata } = sceltaRisposta(c, testo);
  return { chiave: c?.chiave ?? null, macchina: c?.macchina ?? null, progetto: c?.progetto ?? null,
    tipo: c?.tipo ?? null, canale, esito, raccomandazione: c?.raccomandazione || null,
    scelta: String(testo ?? "").trim().slice(0, TESTO_CHECKLIST_MAX), numero, accettata, capo: Boolean(c?.capoRac),
    ...(nota ? { nota: String(nota).slice(0, COMMENTO_MAX) } : {}),
    ...(errore ? { errore: String(errore).slice(0, 160) } : {}) };
}
// Una carta appena risposta esce dalla Coda subito, senza aspettare la sonda dopo: altrimenti la vista
// la rimostra e un secondo tasto risponde due volte. Torna se la sessione scrive una carta nuova (quando
// più recente) o dopo RISPOSTA_MS, se la risposta non l'ha raggiunta. `risposte`: chiave → istante.
export const RISPOSTA_MS = 3 * 60 * 1000;
export function senzaRisposte(lista, risposte, ora = Date.now()) {
  const rr = risposte && typeof risposte === "object" ? risposte : {};
  return (lista ?? []).filter((c) => {
    const q = Number(rr[c?.chiave]);
    // una carta UF (#5722) resta fuori finché il capo non la rilegge dopo la risposta: un giro all'ora,
    // con i task riletti dall'archivio. Rimanda di una bozza mette l'istante a domani (RIMANDA_MS).
    if (c?.origine === "uf" && q > 0) return Number(c?.letto) > q;
    return !(q > 0 && ora - q < RISPOSTA_MS && !(Number(c?.quando) > q));
  });
}

// Le carte UF della Coda (#5722, step 5 del piano): i task che aspettano la persona e le bozze email non
// partite, scritte dal giro orario del capo (volta_capo.py giro) e lette da ogni Volta con `volta_capo.py
// prendi` ogni LETTURA_UF_MS. `d`: { letto (ms), carte, vecchia?, errore? }. Una carta tiene solo le chiavi
// "uf:<numero>" e "bozza:<thread>", le sole che il comando della risposta sa portare (comandi.js).
export const LETTURA_UF_MS = 5 * 60 * 1000;
export const RIMANDA_MS = 24 * 3600 * 1000;
export function carteUf(d) {
  if (!d || !Array.isArray(d.carte)) return [];
  const letto = Number(d.letto) || 0;
  return d.carte.filter((c) => c && typeof c === "object" && /^(uf|bozza):[0-9A-Za-z]+$/.test(String(c.chiave ?? "")))
    .map((c) => ({ ...c, origine: "uf", gruppo: c.gruppo === "tu" ? "tu" : "decidi",
      opzioni: Array.isArray(c.opzioni) ? c.opzioni.map(String).slice(0, CODA_OPZIONI) : [],
      prove: [], menu: false, minima: false, blocco: false, host: null, macchina: null,
      quando: Number(c.quando) > 0 ? Number(c.quando) : 0, letto, vecchia: Boolean(d.vecchia) }));
}

// Il capo di gabinetto (#5723, step 6 del piano): il giro del capo giudica col modello le carte nuove e
// scrive i giudizi delle sessioni in carte-uf.json (`giudizi`, per "s:<sessionId>", con l'istante della carta
// giudicata); le carte UF arrivano già giudicate. conCapo mette il giudizio solo sulla stessa carta: una
// carta nuova della sessione aspetta il giro dopo. Una carta reversibile, che non sia di quelle che solo
// la persona fa, ha "Lascia a Claude" come prima opzione; il segno non agisce da solo.
export const LASCIA = "Lascia a Claude";
export const TESTO_LASCIA = "Scegli tu e vai avanti: il passo è reversibile. Fallo e riportalo come fatto.";
export const idCapo = (c) => (c?.origine === "uf" ? String(c?.chiave ?? "") : `s:${c?.sessionId ?? ""}`);
export function conCapo(lista, d) {
  const gg = d?.giudizi && typeof d.giudizi === "object" ? d.giudizi : {};
  return (lista ?? []).map((c) => {
    const g = c?.sessionId ? gg[idCapo(c)] : null;
    if (!g || typeof g !== "object" || Math.abs(Number(g.quando) - Number(c.quando)) >= 1000) return c;
    const rac = String(c.raccomandazione ?? "").trim() ? "" : String(g.raccomandazione ?? "").slice(0, 200);
    const reversibile = g.reversibile === true && !UMANI.includes(c.tipo);
    const oo = Array.isArray(c.opzioni) ? c.opzioni : [];
    return { ...c, riassunto: String(g.riassunto ?? "").slice(0, 140), reversibile,
      doppia: typeof g.doppia === "string" ? g.doppia : null,
      ...(rac ? { raccomandazione: rac, capoRac: true } : {}),
      ...(reversibile ? { opzioni: [LASCIA, ...oo.filter((o) => o !== LASCIA)].slice(0, CODA_OPZIONI) } : {}) };
  });
}
// Il testo che arriva alla sessione: "Lascia a Claude" diventa l'istruzione intera, il resto com'è.
export function testoPerSessione(t) {
  const x = String(t ?? "");
  if (x.trim() === LASCIA) return TESTO_LASCIA;
  return x.startsWith(`${LASCIA} · `) ? TESTO_LASCIA + x.slice(LASCIA.length) : x;
}

// I gesti di ogni carta (16/11/2026, Federico): Già fatto, Scarta e Note, più il commento che C apre sul
// pulsante sotto il cursore. Il comando porta gesto e commento insieme, in JSON esadecimale:
// "arturo.coda-gesto-<chiave>-<esadecimale>". gestoCoda() dice cosa fa il gesto su ogni tipo di carta:
//   sessione  un'opzione o la raccomandazione col commento "· Nota: …"; Già fatto scrive "L'ho già fatto io.";
//             Note scrive il commento; Scarta toglie la carta senza scrivere (torna con una carta nuova);
//   task UF   il gesto di gestoUf (Già fatto = Fatto), col commento come nota prima del gesto; Scarta col
//             commento lo usa come motivo; Note è la nota;
//   bozza     Già fatto la toglie fino al giro dopo del capo; Scarta la toglie per sempre da questa
//             macchina; Note e Riscrivi col commento fanno riscrivere a Claude con le indicazioni.
// Torna { azione: "rispondi"|"uf"|"scarta", testo?, scelta, nota } o null.
export const GIA_FATTO = "Già fatto";
export const SCARTA = "Scarta";
export const NOTE = "Note";
export const COMMENTO_MAX = 300;
export const comandoGesto = (chiaveCarta, gesto, commento = "") => `arturo.coda-gesto-${chiaveCarta}-${codifica(JSON.stringify({
  g: String(gesto ?? "").trim().slice(0, 120), n: String(commento ?? "").replace(/\s+/g, " ").trim().slice(0, COMMENTO_MAX) }))}`;
export function leggiGesto(hex) {
  try {
    const d = JSON.parse(decodifica(hex));
    return typeof d?.g === "string" && d.g.trim() ? { gesto: d.g.trim(), commento: typeof d.n === "string" ? d.n.trim() : "" } : null;
  } catch { return null; }
}
export function gestoCoda(c, gesto, commento = "") {
  const g = String(gesto ?? "").trim();
  const n = String(commento ?? "").replace(/\s+/g, " ").trim().slice(0, COMMENTO_MAX);
  if (!c || !g) return null;
  const uf = c.origine === "uf";
  if (g === NOTE && !n) return null;
  if (g === SCARTA && (!uf || c.fonte === "bozza")) return { azione: "scarta", scelta: g, nota: n };
  if (!uf) {
    if (g === NOTE) return { azione: "rispondi", testo: n, scelta: g, nota: n };
    const base = g === GIA_FATTO ? "L'ho già fatto io." : g;
    return { azione: "rispondi", testo: n ? `${base} · Nota: ${n}` : base, scelta: g, nota: n };
  }
  if (g === NOTE) return { azione: "uf", testo: n, scelta: g, nota: "" };
  return { azione: "uf", testo: g === GIA_FATTO && c.fonte !== "bozza" ? "Fatto" : g, scelta: g, nota: n };
}
// Le carte scartate restano fuori: una bozza per sempre, una sessione finché non scrive una carta nuova.
// `scartate`: chiave → istante della carta scartata (volta_carte.py scartate).
export function senzaScartate(lista, scartate) {
  const ss = scartate && typeof scartate === "object" ? scartate : {};
  return (lista ?? []).filter((c) => {
    if (!c || !Object.prototype.hasOwnProperty.call(ss, c.chiave)) return true;
    if (c.origine === "uf") return false;
    return Number(c.quando) > Number(ss[c.chiave]);
  });
}
// Le carte doppie (il capo dice quale altra carta chiede la stessa decisione): esce la doppia se la sua
// principale è in Coda e non è a sua volta una doppia; la principale porta i titoli delle doppie. Due
// carte che si indicano a vicenda restano tutte e due.
export function fondiDoppie(lista) {
  const l = (lista ?? []).filter(Boolean);
  const per = new Map(l.map((c) => [idCapo(c), c]));
  const radice = (c) => !(c?.doppia && per.has(c.doppia) && c.doppia !== idCapo(c));
  const via = new Set(l.filter((c) => !radice(c) && radice(per.get(c.doppia))).map(idCapo));
  const doppie = {};
  for (const c of l) if (via.has(idCapo(c))) (doppie[c.doppia] ??= []).push(String(c.titolo ?? c.domanda ?? "").slice(0, 80));
  return l.filter((c) => !via.has(idCapo(c))).map((c) => (doppie[idCapo(c)] ? { ...c, doppie: doppie[idCapo(c)] } : c));
}
// La misura in testata della Coda: "Raccomandazioni accettate: 3 su 5 questa settimana", o null senza
// raccomandazioni nel registro della settimana.
export const rigaMisura = (m) => (Number(m?.su) > 0 ? `Raccomandazioni accettate: ${Number(m.accettate) || 0} su ${Number(m.su)} questa settimana` : null);

// La chiusura automatica (#5366): le sessioni di questa macchina in background che aspettano un comando
// da più di `dopoMin` minuti, senza un lavoro lasciato in corso, senza una scheda aperta in questa
// finestra (chi la guarda la sta usando) e non già in congedo. Prima la più vecchia.
// Una sessione col turno chiuso da un errore (#5882) non ha finito: aspetta la ripresa, o la persona.
// `opz`: { dopoMin, congedi: { chiave: c }, conScheda: Set di chiavi }.
export function daCongedare(dati, adesso, opz = {}) {
  const soglia = adesso - (Number(opz.dopoMin) || 60) * 60000;
  const via = chiaviDi(opz.congedi);
  const scheda = opz.conScheda ?? new Set();
  return (dati?.sessioni ?? [])
    .filter((s) => s.questa && s.tipo === "background" && !s.vecchia && !s.errore && fase(s) === "attesa" && !lavoroInCorso(s.coda))
    .filter((s) => interazione(s) > 0 && interazione(s) < soglia && !via.has(chiave(s)) && !scheda.has(chiave(s)))
    .sort((a, b) => interazione(a) - interazione(b));
}

// La ripresa da sola (#5882, Federico 17/11/2026, dalla prima /revisione: "Riprendi" dopo Connection lost,
// "Ho resettato, procedi" dopo il limite). Volta fa ripartire una sessione solo se il turno è finito con un
// errore (campo errore della sonda): il limite d'uso all'ora di sblocco, la connessione persa (anche il Mac
// andato in stop) quando la rete torna, cioè quando RIPRESA sulla sua macchina raggiunge Anthropic. Mai se
// aspetta la persona (un dialogo, una carta della Coda), mai in congedo, mai un'interattiva fuori da Herdr.
// Al più RIPRESA_TENTATIVI tentativi per fermata: la fermata finisce con un turno riuscito dopo l'ultimo.
export const RIPRESA_TENTATIVI = 2;
// dopo un limite: un minuto oltre lo sblocco. Dopo una connessione persa: un minuto, cinque al secondo tentativo.
export const RIPRESA_DOPO_SBLOCCO_MS = 60000;
export const RIPRESA_CONNESSIONE_MS = [60000, 5 * 60000];
// per quanto la riga dice "ripresa da sola alle HH:MM" dopo l'ultimo tentativo
export const RIPRESA_RIGA_MS = 60 * 60000;

// I tentativi della fermata in corso: quelli dopo l'ultimo turno riuscito (le ore sono ISO UTC, si confrontano
// come stringhe, come fa RIPRESA).
export function tentativiRipresa(s) {
  const tt = (Array.isArray(s?.ripresa) ? s.ripresa : []).filter((x) => typeof x?.ora === "string");
  return tt.length && String(s?.riuscita ?? "") > tt[tt.length - 1].ora ? [] : tt;
}

// Quando la sessione riparte da sola (ms), o null se non riparte.
export function quandoRipresa(s) {
  const e = s?.errore;
  if (!s || s.vecchia || chiusa(s) || s.congedo || !e || !["limite", "connessione"].includes(e.tipo)) return null;
  if (s.stato === "lavora" || s.stato === "aspetta" || s.aspetta || s.carta) return null;
  if (s.tipo !== "background" && !s.terminale) return null;
  const tt = tentativiRipresa(s);
  if (tt.length >= RIPRESA_TENTATIVI || tt.some((x) => x.errore === e.quando)) return null;
  if (e.tipo === "limite") return Number(e.sblocco) > 0 ? Number(e.sblocco) * 1000 + RIPRESA_DOPO_SBLOCCO_MS : null;
  const t = Date.parse(e.quando || "");
  return t ? t + RIPRESA_CONNESSIONE_MS[Math.min(tt.length, RIPRESA_CONNESSIONE_MS.length - 1)] : null;
}

// Le sessioni da riprendere adesso, la più vecchia prima; non quelle in congedo. `opz`: { congedi }.
export function daRiprendere(dati, adesso, opz = {}) {
  const via = chiaviDi(opz.congedi);
  return (dati?.sessioni ?? [])
    .map((s) => ({ s, quando: quandoRipresa(s) }))
    .filter((x) => x.quando !== null && x.quando <= adesso && !via.has(chiave(x.s)))
    .sort((a, b) => a.quando - b.quando)
    .map((x) => x.s);
}

// Il testo che riceve la sessione: una riga, come la risposta della Coda.
export function testoRipresa(s) {
  const perche = s?.errore?.tipo === "limite" ? "il limite d'uso, che ora è sbloccato" : "la connessione persa";
  return `Riprendi da dove ti eri fermato: il turno di prima si è interrotto per ${perche}. È una ripresa automatica di Volta.`;
}

// La riga dell'elenco: prima della ripresa dice quando riparte, dopo che è ripartita da sola, e dopo due
// tentativi a vuoto che tocca alla persona. null se la ripresa non c'entra.
export function fraseRipresa(s, adesso = Date.now()) {
  const e = s?.errore, tt = tentativiRipresa(s);
  if (e && ["limite", "connessione"].includes(e.tipo)) {
    const perche = e.tipo === "limite" ? "Limite d'uso" : "Connessione persa";
    const q = quandoRipresa(s);
    if (q !== null) return { testo: q > adesso ? `${perche}: riparte da sola alle ${oraCorta(q)}` : `${perche}: riparte da sola fra poco`, colore: "muted" };
    if (tt.length >= RIPRESA_TENTATIVI && !tt.some((x) => x.errore === e.quando))
      return { testo: `${perche} di nuovo dopo ${tt.length} riprese: riprendila tu`, colore: "blocked" };
    if (e.tipo === "limite" && !(Number(e.sblocco) > 0)) return { testo: `${perche}: non so quando si sblocca, riprendila tu`, colore: "blocked" };
    return null;
  }
  const u = tt[tt.length - 1], t = Date.parse(u?.ora ?? "");
  return t && adesso - t < RIPRESA_RIGA_MS ? { testo: `ripresa da sola alle ${oraCorta(t)}`, colore: null } : null;
}

// Quante chiusure automatiche restano: al più `ora` nell'ultima ora e `giorno` nelle ultime 24 ore.
// `fatti`: le ore (ms) delle chiusure già fatte.
export function restanti(fatti, adesso, opz = {}) {
  const l = (fatti ?? []).map(Number).filter((x) => x > 0 && x <= adesso);
  const ora = l.filter((x) => adesso - x < 3600000).length, giorno = l.filter((x) => adesso - x < 86400000).length;
  return Math.max(0, Math.min((opz.ora ?? 3) - ora, (opz.giorno ?? 12) - giorno));
}

// Il registro del modo "prova": cosa la chiusura automatica avrebbe chiuso, una voce per sessione, con
// la prima e l'ultima volta che l'ha vista. Al più 40 voci, le più recenti. Lo legge Federico prima di
// accendere la chiusura vera (arturo.json, "congedo": "acceso").
export function registroProva(prima, scelte, adesso) {
  const per = new Map((prima ?? []).map((v) => [v.sessionId, v]));
  for (const s of scelte ?? []) {
    const v = per.get(s.sessionId);
    per.set(s.sessionId, { sessionId: s.sessionId, id: s.id, titolo: titolo(s), progetto: s.progetto ?? null,
      interazione: s.interazione || s.ultimo || "", coda: String(s.coda ?? "").slice(-160), fineFatta: Boolean(s.fineFatta),
      vista: v?.vista ?? adesso, ultima: adesso });
  }
  return [...per.values()].sort((a, b) => b.ultima - a.ultima).slice(0, 40);
}

// Il nome vero di questa macchina, dall'elenco delle macchine (`dati` di sessioni.json o shared
// arturo.volta.macchine): null se l'elenco non c'è ancora.
export const macchinaQui = (dati) => (Array.isArray(dati) ? dati : dati?.macchine ?? []).find((x) => x?.questa)?.macchina ?? null;
// Il nome di una macchina di "Nasce su" e dei messaggi: "qui" è il nome vero di questa macchina (#5534:
// gli errori dicevano "non parte su qui"), "questa macchina" solo finché l'elenco manca.
export const nomeMacchina = (m, macchine) => (m === "qui" ? macchinaQui(macchine) ?? "questa macchina" : m);

// Il nome di una macchina in una riga stretta: senza il proprietario e senza la coda fra parentesi che
// macOS aggiunge ("MacBook Air di Federico (156)" → "MacBook Air"). Il nome intero resta nei gruppi.
export function macchinaBreve(nome) {
  const s = String(nome ?? "").trim();
  const b = s.replace(/\s*\([^)]*\)\s*$/, "").replace(/\s+(di|de|of)\s+\S+$/i, "").replace(/^\S+['’]s\s+/, "").trim();
  return b || s;
}

// La seconda riga: ciò che il gruppo non dice già (il progetto per macchina, la macchina per progetto).
export function dettaglio(s, modo, adesso = Date.now()) {
  const dove = modo === "progetto" ? macchinaBreve(s.macchina) : (s.progetto ? nomeProgetto(s.progetto) : "");
  const f = fraseStato(s, adesso);
  return { testo: dove ? `${dove} · ${f.testo}` : f.testo, colore: f.colore };
}

// Le macchine che non rispondono (14/11/2026, Federico: le schede di una macchina spenta non si chiudono,
// "deve dimenticarle automaticamente, salvando però un handoff di quelle sessioni"). Dopo DIMENTICA_MS il
// core di Volta toglie le sue schede da questa finestra (mirror_sync.rs, stessa soglia), il mod salva un
// handoff per ogni sua sessione dall'ultima lettura e piega il suo gruppo in una riga. Al ritorno tutto
// riappare da solo. `giuDa`: { host: ms della prima lettura che l'ha vista giù }, tenuto fra un giro e
// l'altro (prima) e ripartito a ogni caduta.
export const DIMENTICA_MS = 10 * 60000;
export function giuDa(prima, macchine, ora = Date.now()) {
  const out = {};
  for (const m of macchine ?? []) if (m?.irraggiungibile && m.host) out[m.host] = Number(prima?.[m.host]) || ora;
  return out;
}
export const dimenticata = (giu, host, ora = Date.now()) => Boolean(giu?.[host]) && ora - giu[host] >= DIMENTICA_MS;

// L'handoff di una sessione rimasta su una macchina che non risponde: quello che Volta ha letto per ultimo
// (la conversazione vera resta sul disco di quella macchina). Markdown, in ~/.cache/volta-handoff/<macchina>/.
// La riga "Giù da" dice la caduta: un handoff della stessa caduta non si riscrive.
const ora8601 = (ms) => (ms ? new Date(ms).toISOString().replace(/\.\d+Z$/, "Z") : "");
export function testoHandoff(s, giuDaMs) {
  const righe = [`# ${titolo(s)}`, "",
    `- Macchina: ${s.macchina ?? s.host ?? "?"} (non risponde)`,
    `- Giù da: ${ora8601(giuDaMs)}`,
    `- Progetto: ${s.progetto || "nessuno"}`,
    `- Cartella: ${s.cartella || "?"}`,
    `- Sessione: ${s.sessionId ?? ""} (${s.id ?? ""})`,
    `- Ultimo messaggio: ${s.interazione || s.ultimo || "?"}`,
    `- Stato all'ultima lettura: ${s.stato ?? "?"}${s.aspetta ? ", ti aspettava" : ""}`];
  if (s.azione) righe.push(`- Ultima azione: ${s.azione}`);
  righe.push("", "## Ultima risposta di Claude", "", String(s.risposta || s.coda || "(nessun testo letto)").trim());
  righe.push("", "## Come riprenderla", "",
    "La conversazione intera è sul disco di quella macchina: quando torna, la sessione riprende da sola.",
    "Per andare avanti subito altrove: \"Riprendi su…\" nel menu della riga, che fa nascere su un'altra macchina una sessione nuova con questo handoff.");
  return righe.join("\n") + "\n";
}

// Il prompt della sessione nuova di "Riprendi su…": con Arturo parte da /inizio del progetto, e il resto
// della riga è il compito; senza, il solo testo. Sta sotto PROMPT_RIPRESA_MAX caratteri: il prompt viaggia
// come argomento (base64 dentro hc exec), e su Windows la riga di comando ha un tetto.
export const PROMPT_RIPRESA_MAX = 3500;
export function promptRipresa(s, testo, conArturo) {
  const dove = s.macchina ?? s.host ?? "un'altra macchina";
  const testa = `Riprendi il lavoro della sessione "${titolo(s)}", rimasta su ${dove} che non risponde. Quello che Volta ha letto per ultimo:`;
  const inizio = conArturo && s.progetto ? `/inizio ${s.progetto} -- ` : "";
  const corpo = String(testo ?? "").replace(/\s+/g, " ").trim();
  const resto = PROMPT_RIPRESA_MAX - inizio.length - testa.length - 2;
  return `${inizio}${testa} ${corpo.length > resto ? `${corpo.slice(0, Math.max(0, resto - 1))}…` : corpo}`;
}

// I gruppi: [{ chiave, titolo, nota?, sessioni }]. L'ordine è quello dell'ultima interazione (campo
// "ultimo"): dentro ogni gruppo la sessione toccata per ultima sta in cima, e viene per primo il gruppo
// che contiene la più recente. Lo stato non sposta le righe: lo dicono pallino e frase. A pari tempo
// l'ordine del file per le macchine (questa per prima) e l'alfabeto per i progetti; la macchina che
// non risponde porta una nota.
const recente = (g) => Math.max(0, ...g.sessioni.map(tempo));
export function gruppi(dati, modo = "macchina", ora = Date.now()) {
  const righe = [...(dati?.sessioni ?? [])].sort((a, b) => tempo(b) - tempo(a) || titolo(a).localeCompare(titolo(b)));
  const per = new Map();
  const metti = (chiave, tit, s) => {
    if (!per.has(chiave)) per.set(chiave, { chiave, titolo: tit, sessioni: [] });
    if (s) per.get(chiave).sessioni.push(s);
  };
  if (modo === "progetto") {
    // le sessioni di una macchina giù da DIMENTICA_MS escono dai progetti e vanno in fondo, in un gruppo
    // piegato per macchina: il menu si pulisce anche per progetto (Federico, 14/11/2026, vista Per progetto)
    const via = new Set((dati?.macchine ?? []).filter((m) => m.irraggiungibile && dimenticata(dati?.giuDa, m.host, ora)).map((m) => m.host));
    const ferme = new Map();
    for (const s of righe) {
      if (via.has(s.host)) {
        if (!ferme.has(s.host)) ferme.set(s.host, { chiave: `giu:${s.host}`, titolo: s.macchina ?? s.host, sessioni: [], raccolta: true });
        ferme.get(s.host).sessioni.push(s);
      } else metti(chiaveProgetto(s.progetto), nomeProgetto(s.progetto), s);
    }
    for (const g of ferme.values()) {
      const q = daQuanto(new Date(dati.giuDa[g.sessioni[0].host]).toISOString(), ora);
      g.nota = `Non risponde${q ? ` ${q}` : ""}: ${g.sessioni.length === 1 ? "una sessione salvata" : `${g.sessioni.length} sessioni salvate`}, da riprendere su un'altra macchina`;
    }
    const out = [...per.values()];
    out.sort((a, b) => recente(b) - recente(a) || a.titolo.localeCompare(b.titolo));
    // una macchina col suo gruppo piegato lo dice lì: la nota in fondo ai progetti nomina le altre
    const giu = (dati?.macchine ?? []).filter((m) => m.irraggiungibile && !via.has(m.host)).map((m) => m.macchina);
    const rotte = (dati?.macchine ?? []).filter((m) => !m.irraggiungibile && m.nascita?.rotta === true).map((m) => m.macchina);
    const note = [giu.length ? `${giu.join(", ")} non ${giu.length > 1 ? "rispondono" : "risponde"}` : "",
      rotte.length ? `${rotte.join(", ")} non fa${rotte.length > 1 ? "nno" : ""} partire sessioni` : ""].filter(Boolean);
    if (note.length && out.length) out[out.length - 1].nota = note.join(" · ");
    return out.concat([...ferme.values()]);
  }
  for (const m of dati?.macchine ?? []) metti(m.host, m.macchina, null);
  for (const s of righe) metti(s.host, s.macchina, s);
  const out = [];
  for (const m of dati?.macchine ?? []) {
    const g = per.get(m.host);
    // giù da DIMENTICA_MS: le schede le ha tolte Volta, gli handoff ci sono, il gruppo si piega in una riga
    if (m.irraggiungibile && dimenticata(dati?.giuDa, m.host, ora)) {
      g.raccolta = true;
      const q = daQuanto(new Date(dati.giuDa[m.host]).toISOString(), ora);
      g.nota = `Non risponde${q ? ` ${q}` : ""}: ${g.sessioni.length === 1 ? "una sessione salvata" : `${g.sessioni.length} sessioni salvate`}, da riprendere su un'altra macchina`;
    } else if (m.irraggiungibile) g.nota = g.sessioni.length ? "Non risponde: mostro l'ultima lettura" : "Non risponde";
    else if (m.nascita?.rotta === true)
      g.nota = m.nascita.permesso === true ? "Un permesso di macOS aspetta una risposta sullo schermo" : "Non fa partire sessioni nuove";
    if (g.sessioni.length || g.nota) out.push(g);
    per.delete(m.host);
  }
  return out.concat([...per.values()].filter((g) => g.sessioni.length)).sort((a, b) => recente(b) - recente(a));
}

// Chiudere una sessione (12/11/2026, decisione di Federico): ⌘W, la X della scheda o Chiudi del menu
// fanno il congedo, cioè /fine e poi claude stop. Una sessione chiusa o in congedo non compare più
// nell'elenco: si ritrova con Apri un progetto. Chiusa = in background, senza processo e senza status,
// fermata con claude stop o dopo /fine (il campo `chiusa` di volta_sonda.py); una in errore resta,
// perché Riavvia serve. Addormentata = senza processo per altro, di solito ritirata dal servizio di
// Claude dopo un'ora ferma (#5495, 13/11/2026): resta nell'elenco e nel giro, e claude attach la riprende.
export const chiusa = (s) => Boolean(s) && s.tipo === "background" && s.chiusa === true;
export const dorme = (s) => Boolean(s) && s.tipo === "background" && s.dorme === true && !chiusa(s);
// Ferma su una domanda di /fine (#5760, 16/11/2026, Federico: sì): senza processo, /fine in fondo e
// claude agents la dice in attesa. La sonda non la segna più chiusa: resta nell'elenco e nella Coda con
// la sua domanda, così la persona risponde (clic, claude attach) o la chiude (il congedo la ferma e la
// elimina, senza un secondo /fine).
export const chiestaInFine = (s) => dorme(s) && s.fineFatta === true && s.stato === "aspetta";
// Una sessione chiusa non riappare mentre fa il /fine di chiusura (16/11/2026, Federico: "mentre fanno il
// fine di chiusura non devono riapparire"). Restano fuori: la sessione nata da un congedo di Volta (la
// sonda la segna `congedo`) finché /fine è il suo ultimo messaggio, anche mentre lavora, salvo errore
// (Riavvia) o una domanda di /fine (#5760); riaperta e usata dopo, torna. E l'originale di un congedo
// passato alla copia (`copiaDi`), finché quel congedo c'è.
export const inChiusura = (s) => Boolean(s) && s.congedo === true && s.fineFatta === true && s.stato !== "errore" && !chiestaInFine(s);
// Le sessioni chiuse da chi usa la finestra e rimaste in claude agents (16/11/2026, Federico: "continua ad
// aprire schede che ho chiuso", a sinistra, dopo un po'). Un congedo che finisce senza claude rm (la ripresa
// che non parte, /fine senza salvataggio, un errore, un tetto, un rm che non va) lascia la sessione ferma
// ma non chiusa, e appena il congedo usciva dal registro l'elenco la rimostrava; così anche l'originale di
// un congedo passato alla copia, quando la copia aveva finito. `chiuse`: { chiave: { da } } in shared
// arturo.volta.chiuse. Resta fuori finché nessuno la riusa: torna se lavora o se la trascrizione va avanti
// dopo `da` (oltre CHIUSE_MARGINE_MS), e Volta toglie la voce quando la riapri tu (clic, ⌘K). Una domanda
// di /fine resta visibile (#5760): la persona risponde o la richiude. Le voci durano CHIUSE_TENUTA_MS.
export const CHIUSE_TENUTA_MS = 7 * 86400000, CHIUSE_MARGINE_MS = 60000;
export function chiusaDaTe(s, chiuse = {}) {
  const v = chiuse?.[chiave(s)];
  if (!v || s.stato === "lavora" || chiestaInFine(s)) return false;
  return tempo(s) <= (Number(v.da) || 0) + CHIUSE_MARGINE_MS;
}
// Il registro delle chiuse con le sessioni `voci` ({ host, id }) segnate ad `ora`, senza le voci scadute.
export function ricordaChiuse(chiuse = {}, voci = [], ora = Date.now()) {
  const out = Object.fromEntries(Object.entries(chiuse ?? {}).filter(([, v]) => ora - (Number(v?.da) || 0) < CHIUSE_TENUTA_MS));
  for (const v of voci) if (v?.id) out[chiave(v)] = { da: ora };
  return out;
}
export function visibili(dati, congedi = {}, chiuse = {}) {
  if (!dati) return dati;
  const via = chiaviDi(congedi);
  for (const c of Object.values(congedi ?? {})) if (c?.copiaDi) via.add(chiave({ host: c.host, id: c.copiaDi }));
  const l = (dati.sessioni ?? []).filter((s) => !chiusa(s) && !inChiusura(s) && !via.has(chiave(s)) && !chiusaDaTe(s, chiuse));
  return { ...dati, sessioni: unaPerConversazione(l) };
}

// Al più `n` parole: la sintesi della testata ne vuole cinque (Federico, 12/11/2026). Oltre, "…".
export function cinqueParole(testo, n = 5) {
  const p = String(testo ?? "").trim().split(/\s+/).filter(Boolean);
  return p.length > n ? `${p.slice(0, n).join(" ")}…` : p.join(" ");
}

// Cosa scrive la testata sotto il progetto: la sintesi della sessione davanti (shared arturo.volta.davanti,
// la scrive titolo-sessione.py a ogni turno), altrimenti il suo titolo, altrimenti il nome della scheda;
// sempre al più cinque parole. null se non c'è niente da dire.
export function sintesiTestata(davanti, nomeScheda = null) {
  const t = davanti?.sintesi || davanti?.titolo || nomeScheda;
  return t ? cinqueParole(t) || null : null;
}

// Il titolo della testata: il progetto della sessione in primo piano, se l'elenco gliene dà uno, altrimenti
// lo spazio (14/11/2026, Federico: "a sinistra è correttamente sistemato, mentre in alto no"). La scheda in
// primo piano non cambia spazio sotto le mani (daAllineare), quindi lo spazio può restare "Senza progetto"
// mentre la colonna dice già il progetto. `noti` è la mappa di shared arturo.progetti.
export function titoloTestata(nomeSpazio, davanti, noti) {
  const p = typeof davanti?.progetto === "string" ? davanti.progetto.trim() : "";
  const nome = p || nomeSpazio || "";
  if (!nome) return "Volta";
  return progettoDi(nome, noti).titolo ?? nome;
}

// Le sessioni che il giro ⌘↓/⌘↑ salta, nella forma dei congedi di visibili(): quelle in congedo, quelle
// la cui riga si sta dissolvendo (`escono`: { chiave: true }) e quelle con la scheda appena sparita
// (`forse`: { chiave: sessione }). Le chiavi bastano: visibili() le legge con chiaviDi.
export function uscenti(congedi = {}, escono = {}, forse = {}) {
  const out = { ...(congedi ?? {}) };
  for (const k of Object.keys(escono ?? {})) if (escono[k]) out[k] = { esce: true };
  for (const [k, s] of Object.entries(forse ?? {})) out[k] = s?.id ? { id: s.id, host: s.host ?? "qui" } : { esce: true };
  return out;
}

// Una conversazione spostata su un'altra macchina (Sposta su, 12/11/2026) c'è su due macchine: resta quella
// che non è ferma, cioè la copia viva. La stessa conversazione ha lo stesso sessionId, oppure lo stesso id
// su un'altra macchina: un /clear dopo lo spostamento cambia il sessionId e lascia l'id (#5634). Fra due
// ferme, o due vive, restano tutte e due.
export function unaPerConversazione(l) {
  const vive = l.filter((s) => s.stato !== "ferma");
  const stessa = (a, b) => (Boolean(a.sessionId) && a.sessionId === b.sessionId) || (Boolean(a.id) && a.id === b.id && (a.host ?? "qui") !== (b.host ?? "qui"));
  return l.filter((s) => s.stato !== "ferma" || !vive.some((x) => stessa(s, x)));
}

// Le schede chiuse da chi usa la finestra: i terminali che agganciavano una sessione al giro di prima e
// ora non ci sono più, tolti quelli che ha chiuso Volta stessa (`tolti`: indirizzo → ms, per Sposta,
// Cambia progetto, Stacca) negli ultimi TOLTI_MS. `prima` e `adesso`: { indirizzo: sessione }.
// `occupate`: { indirizzo: sessione } di occupanti(). Una scheda dove ora gira un'altra sessione (claude
// lanciato a mano nella shell rimasta dopo lo stacco) non è chiusa: la scheda c'è ancora, mostra solo
// un'altra sessione, e quella di prima non va in congedo (#5630).
export const TOLTI_MS = 60000;
export function sparite(prima, adesso, tolti = {}, ora = Date.now(), occupate = {}) {
  if (prima == null) return [];  // il primo giro dopo l'apertura solo guarda
  const viste = new Set();
  const out = [];
  for (const [ind, s] of Object.entries(prima)) {
    if (ind in (adesso ?? {}) || occupate?.[ind] || (tolti?.[ind] && ora - tolti[ind] < TOLTI_MS) || !s?.id || viste.has(chiave(s))) continue;
    // un'altra scheda aggancia ancora la stessa sessione: chiusa una copia, la sessione resta aperta
    if (Object.values(adesso ?? {}).some((x) => x?.id && chiave(x) === chiave(s))) continue;
    viste.add(chiave(s));
    out.push(s);
  }
  return out;
}

// Lo stacco delle schede ferme (F3.2 di #5587, deciso da Federico il 14/11/2026): un claude attach aperto
// impedisce al servizio di Claude di ritirare la sessione dopo un'ora ferma, e la sessione tiene 350-600 MB.
// Una scheda che aggancia una sessione ferma da STACCA_DOPO_MS si stacca con Ctrl+Z di claude attach: esce
// pulito, spegne i modi del terminale e la bozza resta nella sessione. La scheda resta con la shell, e il
// clic sulla riga o sulla scheda rilancia l'aggancio. `schede`: { indirizzo: sessione } di schedeAgganciate.
// `opz`: { davanti: l'indirizzo in primo piano, che chi guarda sta usando; visti: Set dei terminali in un
// pannello, perché un terminale fuori dalle schede (un Terminale col lanciatore) non è una scheda;
// no: Set di indirizzi da non riprovare }. Torna [{ indirizzo, s }], prima la più vecchia.
export const STACCA_DOPO_MS = 45 * 60000;
export function daStaccare(schede, sessioni, adesso, opz = {}) {
  const soglia = adesso - STACCA_DOPO_MS;
  const l = sessioni ?? [];
  const out = [];
  for (const [indirizzo, c] of Object.entries(schede ?? {})) {
    if (!c || indirizzo === opz.davanti || opz.no?.has(indirizzo) || (opz.visti && !opz.visti.has(indirizzo))) continue;
    // macchina e id insieme: dopo uno spostamento lo stesso id c'è su due macchine (#5634)
    const s = l.find((x) => x.id === c.id && x.host === c.host);
    if (!s || s.tipo !== "background" || s.vecchia || chiusa(s) || s.stato !== "ferma" || s.aspetta || lavoroInCorso(s.coda)) continue;
    const t = interazione(s);
    if (t > 0 && t <= soglia) out.push({ indirizzo, s, t });
  }
  return out.sort((a, b) => a.t - b.t).map(({ indirizzo, s }) => ({ indirizzo, s }));
}

// La scheda che va nello spazio del suo progetto (14/11/2026, Federico: "il progetto associato alle sessioni
// non viene aggiornato in tempo reale"). aggancia() di dati.js sceglie lo spazio solo quando apre la scheda:
// se il progetto arriva dopo (un file scritto, il progetto dedotto dal contenuto), la scheda restava in
// "Senza progetto" o nello spazio di prima. `voci`: [{ indirizzo, s, spazio: { nome, libero } }], una per
// scheda che aggancia una sessione. `prima`: { chiave: { progetto, letto } } del giro di prima, `letto`
// quello dell'elenco di adesso. Una scheda si sposta solo se il progetto è lo stesso in due letture
// diverse dell'elenco, è un progetto noto, la scheda non è quella in primo piano (dove la persona
// scrive) e quello spostamento non è già stato fatto (`fatti`: "chiave|progetto"). Un progetto vuoto
// non sposta mai: una lettura che lo perde per un attimo non deve svuotare lo spazio. Al più una
// scheda per giro. Torna { sposta: [{ indirizzo, s, progetto }], visti } con `visti` da ridare come `prima`.
export function daAllineare(voci, opz = {}) {
  const prima = opz.prima ?? {}, letto = opz.letto ?? "", fatti = opz.fatti ?? new Set();
  const sposta = [], visti = {};
  for (const { indirizzo, s, spazio } of voci ?? []) {
    if (!s?.id || s.vecchia || s.tipo !== "background" || !Array.isArray(s.attach)) continue;
    const p = String(s.progetto ?? "").trim();
    if (!p) continue;
    const k = chiave(s), v = prima[k];
    const uguale = Boolean(v) && v.progetto === p;
    visti[k] = uguale ? v : { progetto: p, letto };
    if (!uguale || v.letto === letto || indirizzo === opz.davanti || !spazio || !progettoApribile(p)) continue;
    const kp = chiaveProgetto(p);
    if (!spazio.libero && chiaveProgetto(spazio.nome) === kp) continue;
    if (fatti.has(`${k}|${kp}`)) continue;
    sposta.push({ indirizzo, s, progetto: p });
  }
  return { sposta: sposta.slice(0, 1), visti };
}

// Un passo del congedo, deciso dallo stato di adesso. `c`: { sessionId, id, host, fase, da, dal } con fase
// "attende" (lavorava quando l'hai chiusa: finisce il turno), "fine" (ripresa con /fine), "ferma" (claude
// stop chiesto). `s`: la sua riga dell'elenco, o undefined. Torna { fai, fase?, salvata?, avviso? } con fai:
// "attendi" | "fine" (stop e ripresa con /fine) | "stop" | "togli" (via dal registro) | "rm" (claude rm,
// poi via dal registro). `salvata` va nel registro quando /fine ha finito il turno: solo allora la sessione
// chiusa si elimina anche da claude agents (#5401, Federico, 12/11: "aggiungi rm"). Dopo una domanda, un
// tetto o un /fine mai partito la sessione resta in claude agents, da riaprire o eliminare a mano.
// Tetti: CONGEDO_MAX_MS per il turno in corso e per /fine; dopo, la sessione si ferma lo stesso e Volta lo
// dice. Una macchina che non risponde tiene il congedo fino a CONGEDO_VECCHIO_MS.
export const CONGEDO_MAX_MS = 20 * 60000, CONGEDO_AVVIO_MS = 20000, CONGEDO_SENZA_FINE_MS = 3 * 60000, CONGEDO_VECCHIO_MS = 6 * 3600000;
// La ripresa di un congedo nata come copia (16/11/2026): claude --bg --resume di una sessione fermata con
// claude stop apre una conversazione nuova con un id suo, e la sonda lo restituisce in `copia`. Il congedo
// passa alla copia, che fa /fine e poi si ferma; prima Volta aspettava l'id vecchio e la copia restava
// aperta. { chiave, voce } della voce nuova, o null se non c'è una copia diversa dalla sessione.
export function congedoSullaCopia(c, copia, ora = Date.now()) {
  if (!c || !copia?.id || copia.id === c.id) return null;
  const voce = { ...c, id: copia.id, sessionId: copia.sessionId || copia.id, fase: "fine", da: ora, dal: ora, copiaDi: c.id };
  return { chiave: chiave(voce), voce };
}

// Le sessioni di prova (#5877, 17/11/2026): nate da una sonda o da un banco col nome prova- (bin/prova.py di
// Arturo, stesso prefisso). Alla chiusura non hanno niente da salvare: niente /fine, stop subito anche se
// lavorano, poi claude rm come una salvata. Sul MacBook erano circa 30 sessioni su 143 in una settimana.
export const PROVA = /^\s*prova-/i;
export const diProva = (s) => PROVA.test(String(s?.nome ?? ""));

// Riaperta durante il congedo (#5633, 14/11/2026: quattro sessioni chiuse per sbaglio, riprese a mano con
// claude --bg --resume e richiuse da Volta due minuti dopo). La sonda dà in `persona` l'ora dell'ultimo
// messaggio della persona che non è /fine, senza i messaggi di un'altra sessione: se viene dopo il gesto
// di chiusura (oltre RIAPERTA_MARGINE_MS, per gli orologi di due macchine), qualcuno la sta usando. Il
// congedo finisce senza stop e senza rm, e la sessione torna nell'elenco.
export const RIAPERTA_MARGINE_MS = 30000;
export const riaperta = (c, s) => Boolean(s) && Number(c?.da) > 0 && (Date.parse(s.persona || "") || 0) > Number(c.da) + RIAPERTA_MARGINE_MS;

// ⌘W da annullare (#5883, Federico, 17/11/2026: "chiusa da Volta per sbaglio alle 17:06"). La scheda si chiude
// subito; /fine, stop e rm aspettano ANNULLA_MS. Il congedo di un gesto della persona porta in `annulla` l'ora
// in cui parte; fino ad allora la riga resta nell'elenco con "Si chiude fra N s · Annulla", e il clic sulla
// riga o ⌘Z (Ctrl+Alt+Z su Windows) toglie il congedo e riapre la sessione. Niente conferma prima. La
// chiusura automatica (#5366) non ha l'attesa: nessuno l'ha chiesta, e nessuno guarda.
export const ANNULLA_MS = 10000;
export const inAnnullo = (c, ora = Date.now()) => Boolean(c) && Number(c.annulla) > ora;
export const secondiAnnullo = (c, ora = Date.now()) => Math.max(1, Math.ceil((Number(c?.annulla) - ora) / 1000));
export const rigaAnnullo = (c, ora = Date.now()) => `Si chiude fra ${secondiAnnullo(c, ora)} s · Annulla`;
// Il registro dei congedi senza quelli ancora da annullare, nella forma di visibili(): l'elenco li mostra.
export function senzaAnnullo(congedi = {}, ora = Date.now()) {
  return Object.fromEntries(Object.entries(congedi ?? {}).filter(([, c]) => !inAnnullo(c, ora)));
}
// L'elenco di visibili() con le sessioni da annullare segnate: `annullo` è la riga da scrivere.
export function conAnnullo(dati, congedi = {}, ora = Date.now()) {
  if (!dati) return dati;
  const da = Object.fromEntries(Object.values(congedi ?? {}).filter((c) => c?.id && inAnnullo(c, ora)).map((c) => [chiave(c), c]));
  return { ...dati, sessioni: (dati.sessioni ?? []).map((s) => (da[chiave(s)] ? { ...s, annullo: rigaAnnullo(da[chiave(s)], ora) } : s)) };
}
// Quale congedo annulla ⌘Z: l'ultimo chiuso fra quelli ancora in attesa. [chiave, voce] o null.
export function daAnnullare(congedi = {}, ora = Date.now()) {
  const l = Object.entries(congedi ?? {}).filter(([, c]) => inAnnullo(c, ora));
  return l.length ? l.reduce((a, b) => ((Number(b[1].da) || 0) > (Number(a[1].da) || 0) ? b : a)) : null;
}

export function passoCongedo(c, s, ora = Date.now()) {
  if (inAnnullo(c, ora)) return { fai: "attendi" };
  const da = Number(c?.da) || ora, dal = Number(c?.dal) || da;
  const nome = s ? titolo(s) : "La sessione";
  if (!s || s.vecchia) return ora - da > (s ? CONGEDO_VECCHIO_MS : 3600000) ? { fai: "togli" } : { fai: "attendi" };
  if (riaperta(c, s)) return { fai: "togli", riaperta: true };
  if (c.fase === "attende") {
    if (chiusa(s)) return { fai: "togli" };
    if (diProva(s)) return { fai: "stop", fase: "ferma", salvata: true };
    // la chiusura automatica di una sessione che ha già fatto /fine (#5366): niente secondo /fine
    // /fine è già l'ultimo messaggio (un /fine di prima, una ripresa già partita, una domanda di /fine,
    // #5760): niente secondo /fine, la sessione si ferma. Prima lo stop, poi l'rm: il controllo di PRIMA
    // rifiuta l'rm di chi aspetta una risposta. Una ricarica del mod a metà congedo rifaceva /fine (16/11).
    if ((c.fineFatta || s.fineFatta === true) && s.stato !== "lavora") return { fai: "stop", fase: "ferma", salvata: true };
    if (s.stato === "lavora" && ora - da < CONGEDO_MAX_MS) return { fai: "attendi" };
    return { fai: "fine", fase: "fine" };
  }
  if (c.fase === "fine") {
    if (ora - dal < CONGEDO_AVVIO_MS) return { fai: "attendi" };
    if (s.stato === "errore") return { fai: "togli", avviso: `${nome}: /fine si è fermato con un errore. La sessione resta ferma.` };
    // senza processo dopo lo stop di Volta: claude agents la dice "stopped" o la lascia "done" (dorme)
    if (chiusa(s) || dorme(s)) return ora - dal > CONGEDO_SENZA_FINE_MS ? { fai: "togli", avviso: `${nome} non è ripartita per /fine: l'ho lasciata chiusa senza salvataggio.` } : { fai: "attendi" };
    if (s.stato === "aspetta") return { fai: "stop", fase: "ferma", avviso: `${nome} ha chiesto qualcosa durante /fine: l'ho fermata lo stesso.` };
    if (s.stato === "lavora") return ora - dal > CONGEDO_MAX_MS ? { fai: "stop", fase: "ferma", avviso: `${nome}: /fine non ha finito in 20 minuti, l'ho fermata.` } : { fai: "attendi" };
    // ferma e viva: /fine ha finito il turno se la trascrizione è andata avanti dopo la ripresa
    if (tempo(s) > dal - 5000) return { fai: "stop", fase: "ferma", salvata: true };
    return ora - dal > CONGEDO_SENZA_FINE_MS ? { fai: "stop", fase: "ferma", avviso: `${nome} non ha fatto /fine: l'ho fermata senza salvataggio.` } : { fai: "attendi" };
  }
  // fase "ferma": aspetta che claude agents la dica senza processo, e riprova lo stop dopo due minuti.
  // Lo stop l'ha chiesto Volta: anche "done" senza processo (dorme) vuol dire fermata.
  if (chiusa(s) || dorme(s)) return c.salvata ? { fai: "rm" } : { fai: "togli" };
  return ora - dal > 120000 ? { fai: "stop", fase: "ferma" } : { fai: "attendi" };
}

// Le nascite che cadono su una macchina (13/11/2026): la sonda scrive `nascita` nella voce della macchina
// quando le sessioni nuove escono prima di iniziare ("exit 1 before init"), come su un Mac con
// Documenti bloccato da macOS. Volta lo dice una volta per episodio e non fa ripartire al clic una
// sessione in errore di quella macchina: ogni ripartenza cadeva di nuovo, due volte per clic.
export function nascitaDi(dati, host) {
  const m = (dati?.macchine ?? []).find((x) => (x.host ?? "qui") === (host ?? "qui"));
  if (m?.nascita?.rotta !== true) return null;
  return { ...m.nascita, macchina: m.questa ? "questa macchina" : (m.macchina ?? m.host) };
}
const oraCorta = (iso) => {
  const d = new Date(iso ?? "");
  return Number.isNaN(d.getTime()) ? null : `${String(d.getHours()).padStart(2, "0")}:${String(d.getMinutes()).padStart(2, "0")}`;
};
export function avvisoNascita(n) {
  if (!n) return null;
  const m = n.macchina ?? "quella macchina", da = oraCorta(n.da);
  // Documenti appeso (18/11/2026): la sonda ha visto che la cartella non si legge
  if (n.permesso === true)
    return `Su ${m} un permesso di macOS aspetta una risposta sullo schermo${da ? ` dalle ${da}` : ""}: Documenti non si legge e le sessioni non partono. Rispondi lì, o riavvia ${m}.`;
  const volte = Number.isInteger(n.quante) && n.quante > 0 ? `${n.quante} volte` : "più volte";
  return `Su ${m} le sessioni non partono${da ? ` dalle ${da}` : ""}: Claude esce prima di iniziare (${volte}). Spesso macOS aspetta un permesso sullo schermo di ${m}: rispondi lì, o riavvia ${m}.`;
}
// Il clic su una sessione in errore la fa ripartire (claude respawn) solo se la sua macchina fa partire
// sessioni. Riavvia del menu resta: è un gesto esplicito.
export function riparteAlClic(s, dati) {
  if (s?.stato !== "errore") return { riparte: false };
  const n = nascitaDi(dati, s.host);
  return n ? { riparte: false, errore: avvisoNascita(n) } : { riparte: true };
}
// Il clic svelto (step 5 del piano di revisione, 17/11/2026): prima di ogni aggancio prepara chiedeva alla
// macchina se il servizio di Claude era acceso, e su un'altra macchina costava un giro di hc exec (1-2 s).
// Il servizio risulta acceso su `host` se prepara o una nascita l'hanno trovato acceso da meno di
// SERVIZIO_VISTO_MS (`visti`: { host: ms }), o se nell'elenco una sessione in background di quella macchina,
// letta da una macchina che risponde, lavora o aspetta: gira dentro il servizio. Allora il clic salta prepara;
// se il servizio fosse caduto nel frattempo, la veglia trova la scheda nuda e lo riaccende.
export const SERVIZIO_VISTO_MS = 5 * 60 * 1000;
export function servizioAcceso(dati, host, visti = {}, ora = Date.now()) {
  const h = host ?? "qui";
  if (ora - (Number(visti?.[h]) || 0) < SERVIZIO_VISTO_MS) return true;
  return (dati?.sessioni ?? []).some((s) => (s?.host ?? "qui") === h && s.tipo === "background" && !s.vecchia
    && !s.dorme && !s.chiusa && (s.stato === "lavora" || s.stato === "aspetta"));
}
// Claude è davanti nella scheda (l'evento apri, step 5): `t` è la voce di terminals() di Herdr, come la dà
// hc ls --json. Vale quando Herdr riconosce Claude Code nel programma della scheda (agent, app o program),
// anche su Windows, dove il primo piano resta pwsh.
export function claudeDavanti(t) {
  if (!t || t.state !== "live") return false;
  return t.agent === "claude-code" || t.app === "claude-code" || t.program?.key === "claude";
}

// Gli avvisi da dare: una macchina che ha appena smesso di far partire sessioni. `viste`: le macchine già
// avvisate in questo episodio ({ host: true }); torna anche le viste nuove, senza quelle tornate a posto.
export function nascitePerAvviso(dati, viste = {}) {
  const avvisi = [], tieni = {};
  for (const m of dati?.macchine ?? []) {
    if (m?.irraggiungibile || m?.nascita?.rotta !== true) continue;
    const k = m.host ?? "qui";
    tieni[k] = true;
    if (!viste?.[k]) avvisi.push(avvisoNascita(nascitaDi(dati, k)));
  }
  return { avvisi, viste: tieni };
}

// I congedi rimasti a metà (13/11/2026): una sessione ripresa con /fine da un congedo (la sonda la segna
// `congedo`) che il registro non ha più, ferma da più di CONGEDO_ORFANO_MS; se è viva, senza scheda aperta qui.
// Solo questa macchina, come la chiusura automatica. Torna [{ s, fai, avviso? }]: "rm" se /fine ha finito
// e la sessione non ha più processo; "stop" se è ancora viva con /fine come ultimo messaggio (poi, ferma,
// diventa "rm"); "rm" con avviso se è in errore senza /fine (la ripresa è caduta): la persona l'aveva
// chiusa, la trascrizione resta su disco. Una viva, ferma o ritirata usata dopo il congedo non si tocca.
// Una senza processo che aspetta una risposta (state "blocked" o "waiting") non si elimina (#5757, 16/11):
// /fine ha chiesto qualcosa e non ha finito, come in passoCongedo. Il controllo fresco di PRIMA rifiutava
// il suo rm, e Volta lo ritentava e lo ridiceva a ogni ricarica del mod (11 volte in un giorno sul MacBook).
export const CONGEDO_ORFANO_MS = 10 * 60000;

// Lo spostamento staccato (13/11/2026): volta_sposta.py scrive l'esito in un file e Volta lo legge a giri.
// `testo`: il file (o null), `dal`: quando è partito, `ora`. Torna { fatto } con l'esito finito, { attendi }
// finché gira, { errore } oltre SPOSTA_MAX_MS: allora lo spostamento non si sa com'è andato.
export const SPOSTA_MAX_MS = 25 * 60000, SPOSTA_OGNI_MS = 5000;

// La coda di Sposta dopo un rifiuto `lavora` (finitoSposta di volta.js): la voce con il prossimo tentativo,
// o null se esce dalla coda. Un turno in corso si riprova al giro dopo (`ogni`), senza limite. Un turno che
// la macchina di partenza non dice (`nonLetto`, #6110) vale come in corso, ma si riprova ogni
// SPOSTA_NON_LETTO_OGNI_MS e al più SPOSTA_NON_LETTO_MAX volte: poi esce con l'errore, che arriva alla persona.
export const SPOSTA_NON_LETTO_MAX = 10, SPOSTA_NON_LETTO_OGNI_MS = 60000;
export function riprovaSposta(v, r, ora, ogni) {
  if (!r?.lavora) return null;
  if (!r.nonLetto) return { ...v, dopo: ora + ogni, nonLetti: 0 };
  const n = (v?.nonLetti ?? 0) + 1;
  return n >= SPOSTA_NON_LETTO_MAX ? null : { ...v, dopo: ora + SPOSTA_NON_LETTO_OGNI_MS, nonLetti: n };
}
export function esitoSposta(testo, dal, ora, macchina = "l'altra macchina") {
  let d = null;
  try { d = testo ? JSON.parse(testo) : null; } catch { d = null; }
  if (d && typeof d === "object" && d.finito === true) { const { finito: _, ...resto } = d; return { fatto: resto }; }
  // senza esito non si sa dove sia la sessione: fineSposta non riapre la scheda di partenza (#5635)
  if (ora - dal > SPOSTA_MAX_MS) return { errore: `${macchina} non ha finito in 25 minuti: guarda fra le sessioni dove è rimasta`, nonSiSa: true };
  return { attendi: true };
}

// Gli spostamenti in volo (#5559, 13/11/2026): una ricarica del mod (dirama, controllo orario) cancella
// l'attesa di cx.sleep, e nessuno apriva la scheda d'arrivo né riapriva quella chiusa. Ogni spostamento
// staccato resta segnato in cacheVolta()/sposta/volo.json finché la sua fine non è fatta, e al caricamento
// Volta riprende quelli rimasti. `v` = { s, macchina, file, dal, chiuse, preso }: `preso` è l'ultima volta
// che una copia del mod ci ha lavorato (ogni giro dell'attesa). Torna "mia" se tocca a chi legge, "altrui"
// se un'altra copia viva lo segue, "scarta" se è rotto o più vecchio di VOLO_MAX_MS: dopo ore la sessione
// sta dove l'elenco la mostra, e una scheda che si apre da sola sorprenderebbe.
export const VOLO_FRESCO_MS = 20000, VOLO_MAX_MS = 2 * 3600000;
export function voloSposta(v, ora) {
  if (!v || typeof v !== "object" || !v.s || typeof v.s !== "object" || !v.s.sessionId || !v.s.id) return "scarta";
  if (typeof v.macchina !== "string" || !v.macchina || typeof v.file !== "string" || !v.file || !Number.isFinite(v.dal)) return "scarta";
  if (ora - v.dal > VOLO_MAX_MS) return "scarta";
  return Number.isFinite(v.preso) && ora - v.preso < VOLO_FRESCO_MS ? "altrui" : "mia";
}

// Il passo di arturo() di dati.js per un comando, dalla sua voce in volo: `v` = { da, p } se gira, { da,
// appeso } se l'ultimo è rimasto appeso (exec rifiuta ma il processo resta). "lancia" se non c'è niente;
// "aspetta" la stessa promessa se gira da meno del tetto; "appeso" se gira oltre il tetto o se l'ultimo è
// rimasto appeso da meno di ARTURO_PAUSA_MS: un processo in più non risponderebbe comunque.
export const ARTURO_PAUSA_MS = 5 * 60000;
export function voloArturo(v, ora, tetto) {
  if (!v) return { fai: "lancia" };
  if (v.appeso) return ora - v.appeso < ARTURO_PAUSA_MS ? { fai: "appeso" } : { fai: "lancia" };
  if (ora - v.da < tetto) return { fai: "aspetta" };
  // una promessa che non torna mai (19/11/2026): la voce resta {da, p} per sempre e rispondeva "appeso" a
  // vita, con i todo e la barra dei progetti fermi fino al ricarico. Oltre tetto + pausa si rilancia.
  return ora - v.da < tetto + ARTURO_PAUSA_MS ? { fai: "appeso" } : { fai: "lancia" };
}

// Un lotto di watchFolder tocca l'elenco se contiene il file (o la cartella intera: rileggi tutto).
// I percorsi si confrontano senza barre finali e senza maiuscole: su Windows arrivano con \.
export function tocca(percorsi, cartella, file) {
  const n = (p) => String(p ?? "").replace(/\\/g, "/").replace(/\/+$/, "").toLowerCase();
  const c = n(cartella), f = n(file);
  return (percorsi ?? []).some((p) => { const x = n(p); return x === c || x === f; });
}
export function congediOrfani(dati, congedi = {}, ora = Date.now(), conScheda = new Set()) {
  const via = chiaviDi(congedi);
  const out = [];
  for (const s of dati?.sessioni ?? []) {
    if (!s?.questa || s.tipo !== "background" || s.vecchia || s.congedo !== true) continue;
    if (via.has(chiave(s))) continue;
    if (s.stato === "lavora") continue;
    if (!(tempo(s) > 0) || ora - tempo(s) < CONGEDO_ORFANO_MS) continue;
    const morta = chiusa(s) || dorme(s) || s.stato === "errore";
    // una scheda aperta protegge solo una sessione viva: su una ferma resta la shell, e la riga restava
    // in Volta per sempre (13/11/2026, un PC Windows: scheda t1z con PowerShell sul congedo 261279d3)
    if (!morta && conScheda.has(chiave(s))) continue;
    // viva: si ferma solo se /fine è ancora l'ultimo messaggio; riaperta e usata dopo il congedo, resta
    if (!morta) { if (s.fineFatta) out.push({ s, fai: "stop" }); }
    else if (s.fineFatta && s.stato !== "errore" && s.stato !== "aspetta") out.push({ s, fai: "rm" });
    // ferma o ritirata senza /fine in fondo: riaperta e usata dopo il congedo, poi lasciata. Resta.
    else if (s.stato === "errore") out.push({ s, fai: "rm", avviso: `${titolo(s)}: chiusa senza salvataggio, /fine non era finito. La conversazione resta su disco.` });
  }
  return out;
}

// Le sessioni di un gruppo che l'elenco mostra: quelle che lavorano, ti aspettano o sono in errore
// sempre; quelle che aspettano un comando (fase "attesa", #5366) solo se il gruppo è aperto, o se non ce
// ne sono altre e sono due o meno.
export const inAttesa = (s) => fase(s) === "attesa";
export function mostrate(g, aperto) {
  // il gruppo di una macchina giù da DIMENTICA_MS si piega tutto (giuDa, più sotto)
  if (g.raccolta) return aperto ? g.sessioni : [];
  // una sessione appena chiusa (`annullo`, #5883) si vede sempre: la sua riga è il modo di annullare
  const vive = g.sessioni.filter((s) => !inAttesa(s) || s.annullo);
  const ferme = g.sessioni.length - vive.length;
  return (!vive.length && ferme <= 2) || aperto ? g.sessioni : vive;
}

// Il giro fra le sessioni (⌘↓ e ⌘↑, Ctrl+↓ e Ctrl+↑ su Windows), nell'ordine dell'elenco: le sessioni
// che hanno una scheda in questa finestra (`conScheda`, le chiavi), in ogni stato, e quelle in
// background senza scheda che lavorano o ti aspettano (fase attiva o stasi), che il tasto apre. Una
// ferma senza scheda resta fuori: l'hai chiusa, e il tasto la riaprirebbe (Federico, 14/11/2026: "mi apre
// schede chiuse"). Alle 20:27 dello stesso giorno, con le sole schede, il tasto non arrivava a una
// sessione che lavorava ("non mi apre Eseguire S4") e saltava quelle di un'altra macchina che ti
// aspettavano. Un'interattiva entra solo con la scheda: in un terminale senza pannello (un hc run) il
// tasto non la mostra. Le ferme nascoste dietro "N in attesa" vengono dopo le righe a vista del loro
// gruppo. Le schede delle sessioni chiuse o di una macchina che non risponde le aggiunge schedeSpente().
export function ordineGiro(lista, aperti = {}, conScheda = new Set()) {
  return (lista ?? []).flatMap((g) => {
    const vista = mostrate(g, aperti[g.chiave]);
    return vista.concat(g.sessioni.filter((s) => !vista.includes(s)));
  })
    .filter((s) => conScheda.has(chiave(s)) || (s.tipo === "background" && ["attiva", "stasi"].includes(fase(s))))
    .filter((s) => ["aggancia", "mostra"].includes(clic(s).azione)).map(chiave);
}

// Le schede di questa finestra che mostrano una sessione chiusa o di una macchina che non risponde: nel
// giro vengono dopo le sessioni, nell'ordine dei pannelli, come "scheda:<indirizzo>", e il tasto le porta
// davanti senza riagganciare niente (Federico, 14/11/2026: "non va su determinate schede"). Prima il giro
// le saltava: restavano aperte e non si raggiungevano coi tasti. `terminali`: quelli dei pannelli, in ordine.
// `uscita`: le sessioni che stanno uscendo (uscenti(), lo stesso filtro di visGiro): dopo ⌘W su una sessione
// di una macchina giù la sua scheda non rientra nel giro mentre il pannello sparisce.
export const SCHEDA = "scheda:";
export function schedeSpente(terminali, sessioni, uscita = {}) {
  const via = chiaviDi(uscita);
  const out = [];
  for (const t of terminali ?? []) {
    const s = sessioneDi(t, sessioni);
    if (s && (s.vecchia || chiusa(s)) && !via.has(chiave(s)) && !out.includes(SCHEDA + t.address)) out.push(SCHEDA + t.address);
  }
  return out;
}

// L'ordine vale per tutta una raffica di tasti: l'elenco è per attività, e una sessione che lavora
// cambia posto mentre giri. Dopo GIRO_MS senza tasti il giro riparte dall'elenco di adesso. `adesso` sono
// gli id del giro di adesso: una sessione sparita esce, una nuova entra al prossimo giro.
export const GIRO_MS = 8000;
export function statoGiro(prima, adesso, ora) {
  const tiene = prima && ora - prima.quando <= GIRO_MS;
  const ids = tiene ? prima.ids.filter((id) => adesso.includes(id)) : adesso;
  return { ids: ids.length ? ids : adesso, ultimo: tiene ? prima.ultimo ?? null : null, quando: ora };
}

// La sessione che l'elenco accende a sinistra (Federico, 12/11/2026: "evidenziarmi su quale sto
// lavorando"). Dentro una raffica di ⌘↓ e ⌘↑ è l'ultima chiesta col giro, perché la scheda ci mette
// qualche secondo ad aprirsi; fuori dalla raffica è quella della scheda in primo piano. Chiavi (chiave()),
// null se nessuna. Il giro può stare su una scheda spenta ("scheda:<indirizzo>", schedeSpente): lì si accende
// la riga della sessione che quella scheda mostra, cercata fra `terminali` e `sessioni`, o la scheda davanti.
export function corrente(giroSt, idScheda, ora, terminali = [], sessioni = []) {
  const u = giroSt?.ultimo && ora - giroSt.quando <= GIRO_MS ? giroSt.ultimo : null;
  if (!u) return idScheda ?? null;
  if (!u.startsWith(SCHEDA)) return u;
  const a = u.slice(SCHEDA.length);
  const s = sessioneDi((terminali ?? []).find((t) => t?.address === a) ?? { address: a }, sessioni);
  return s ? chiave(s) : idScheda ?? null;
}

// La sessione che una scheda mostra, anche quando la scheda sta in uno spazio di un'altra macchina
// (indirizzo "torre/t13"): là Claude gira nel terminale t13 di torre, che la sonda di quella
// macchina scrive nel campo terminale. Chi gira nel terminale vince sull'etichetta, come in occupanti:
// una scheda nata per una sessione può ospitarne dopo un'altra. Poi vale sessioneDi.
export function sessioneDavanti(terminale, sessioni) {
  if (!terminale) return null;
  const [m, t] = String(terminale.address ?? "").split("/");
  const li = t ? (sessioni ?? []).find((s) => s.host === m && s.terminale === t && s.tipo !== "background") : null;
  return li ?? sessioneDi(terminale, sessioni);
}

// La sessione dopo (verso 1) o prima (verso -1) di `corrente`, in tondo. Senza corrente, o con una
// corrente fuori dal giro: la prima andando avanti, l'ultima andando indietro. null a giro vuoto.
export function passoGiro(ids, corrente, verso) {
  if (!ids?.length) return null;
  const i = ids.indexOf(corrente);
  if (i < 0) return verso < 0 ? ids[ids.length - 1] : ids[0];
  return ids[(i + (verso < 0 ? -1 : 1) + ids.length) % ids.length];
}

// I terminali di questa macchina dove gira adesso una sessione interattiva (la sonda lo legge dal
// processo, campo terminale): { indirizzo: sessione }. Vincono su etichetta e argv. Una scheda nata per
// agganciare una sessione può ospitare dopo un'altra sessione, avviata a mano nella sua shell: allora
// mostra quella, col suo progetto e la sua macchina (12/11/2026, Post Office al posto di Volta).
export function occupanti(sessioni) {
  const out = {};
  for (const s of sessioni ?? []) if (s?.questa && s.tipo !== "background" && s.terminale) out[s.terminale] = s;
  return out;
}

// La sessione che una scheda mostra: quella che ci gira (occupanti), poi l'etichetta di Herdr (hc label
// arturo.sessione), poi l'argv dell'aggancio. null se la scheda non è di una sessione.
export function sessioneDi(terminale, sessioni) {
  if (!terminale) return null;
  const l = sessioni ?? [];
  const e = etichettaVista(terminale);
  return occupanti(l)[terminale.address]
    ?? l.find((s) => etichettaDice(e, s, doppio(l, s.id)) === true)
    ?? l.find((s) => etichettaDice(e, s, doppio(l, s.id)) === null && agganciataDa(terminale.argv, s, terminale.address)) ?? null;
}

// La scheda che riceve il todo di Lavoraci (#5485, 19/11/2026). Lo spazio prende il nome del progetto, ma
// una sua scheda può ospitare una sessione di un altro progetto: un todo di Post Office finiva nella
// sessione che lavorava su Volta. `schede`: le schede di Claude dello spazio, in ordine di preferenza,
// ognuna con `terminale` (di terminals()). Torna la prima la cui sessione (sessioneDi) ha la chiave di
// `nome`, o null: una sessione di un altro progetto, o senza progetto, non riceve il todo.
export function schedaDelProgetto(schede, nome, sessioni, noti = NOTI) {
  const k = progettoDi(nome, noti).chiave;
  if (!k) return null;
  return (schede ?? []).find((x) => {
    const s = sessioneDi(x?.terminale, sessioni);
    return Boolean(s?.progetto) && progettoDi(s.progetto, noti).chiave === k;
  }) ?? null;
}

// Le schede nel core della macchina della sessione (#5802, 16/11/2026). Una sessione di un'altra macchina
// si apriva in una scheda di qui con ssh -t <macchina> claude attach: a portatile chiuso la scheda spariva,
// e il telefono, che parla col core di quella macchina, non vedeva la sessione. Ora la scheda nasce in uno
// spazio di quella macchina e aggancia in locale. Da qui il suo indirizzo è "<macchina>/tNN".
// La macchina di un indirizzo di Herdr: "amaltea/t21" dà "amaltea", un indirizzo di qui dà null.
export function macchinaIndirizzo(a) {
  const s = String(a ?? "");
  const i = s.indexOf("/");
  return i > 0 ? s.slice(0, i) : null;
}
// L'etichetta come la legge questa macchina. Sul core di un'altra macchina l'etichetta è scritta con le
// chiavi di là: "qui:<id>" (la chiave che quella macchina dà alle sue sessioni), così la finestra di là
// riconosce la scheda come sua. Da qui vale "<macchina>:<id>". Il solo id di prima vale per la sua macchina.
export function etichettaVista(t) {
  const v = t?.labels?.[ETICHETTA];
  const m = macchinaIndirizzo(t?.address);
  if (!v || !m) return v;
  const x = String(v);
  if (x.startsWith("qui:")) return `${m}:${x.slice(4)}`;
  return x.includes(":") ? x : `${m}:${x}`;
}
// L'aggancio sul core della macchina della sessione: dall'argv della sonda (ssh, -t, opzioni, target,
// claude, attach, id) resta claude attach <id>. null se l'argv non passa da ssh o non finisce con attach.
export function attachLocale(argv) {
  const a = Array.isArray(argv) ? argv.map(String) : [];
  if (a.length < 4 || !/(^|[\\/])ssh(\.exe)?$/i.test(a[0]) || a[1] !== "-t") return null;
  let j = 2;
  while (j < a.length && a[j].startsWith("-")) j += a[j].length === 2 && OPZIONI_CON_VALORE.has(a[j][1]) ? 2 : 1;
  const resto = a.slice(j + 1);
  return resto.length === 3 && resto[1] === "attach" && resto[2] ? resto : null;
}
// L'argv aggancia `s` dal terminale `indirizzo`: un terminale di un'altra macchina aggancia in locale, e
// vale solo per una sessione di quella macchina; uno di qui come sempre (agganciata).
export function agganciataDa(argv, s, indirizzo) {
  const m = macchinaIndirizzo(indirizzo);
  if (!m) return agganciata(argv, s);
  const loc = (s?.host ?? "qui") === m ? attachLocale(s.attach) : null;
  return Boolean(loc) && agganciata(argv, { ...s, attach: loc });
}
// Chi ha aperto la scheda: la finestra di quella macchina la guarda, la stacca e la manda in congedo
// quando sparisce. Lo dice l'argv di nascita, che il core tiene: env VOLTA_DA=<macchina> davanti a
// claude attach. Un'etichetta arriverebbe dopo la nascita, e nel frattempo la finestra della macchina
// della sessione la prenderebbe per sua e la manderebbe in congedo quando cambia padrone.
export const SEGNO_DA = "VOLTA_DA=";
export function daDi(argv) {
  for (const a of Array.isArray(argv) ? argv : []) if (typeof a === "string" && a.startsWith(SEGNO_DA)) return a.slice(SEGNO_DA.length) || null;
  return null;
}
// La scheda è di questa finestra (`io`: il nome di questa macchina, ioQui di dati.js): una scheda di qui
// senza segno, come prima del 16/11/2026, o col segno di qui; una scheda di un'altra macchina solo col segno di qui.
export function mia(t, io) {
  const d = daDi(t?.argv);
  return macchinaIndirizzo(t?.address) ? Boolean(io) && d === io : !d || d === io;
}
// L'argv della scheda nel core della macchina della sessione: env col segno di chi la apre, poi claude
// attach in locale. null quando la scheda resta qui con ssh: senza il nome di questa macchina, senza un
// aggancio ssh, o con una macchina Windows (lì env non c'è, e la scheda ha PowerShell).
export function argvRemoto(argv, io) {
  const loc = attachLocale(argv);
  if (!io || !loc || percorsoWindows(loc[0])) return null;
  return ["/usr/bin/env", SEGNO_DA + io, ...loc];
}

// L'etichetta di Herdr sul terminale che aggancia una sessione (hc label): dal 14/11/2026 la chiave
// macchina:id (#5634). Cosa dice su `s`: true è sua, false è di un'altra sessione, null non lo dice. Non lo
// dice una scheda senza etichetta, e un'etichetta di prima col solo id quando l'id sta su due macchine
// (`ambiguo`): lì decide l'argv. Un'etichetta vecchia con un id che una macchina sola ha vale ancora: le
// schede aperte prima restano riconosciute.
const ETICHETTA = "arturo.sessione";
export function etichettaDice(valore, s, ambiguo = false) {
  if (!valore || !s?.id) return null;
  const v = String(valore);
  if (v.includes(":")) return v === chiave(s);
  if (v !== s.id) return false;
  return ambiguo ? null : true;
}
// Il terminale `t` mostra la sessione `s`: per etichetta, poi per argv.
export const suaScheda = (t, s, ambiguo = false) => {
  const e = etichettaDice(etichettaVista(t), s, ambiguo);
  return e ?? agganciataDa(t?.argv, s, t?.address);
};

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
// Dal 14/11/2026 (#5634) conta anche la macchina: l'argv aggancia `s` solo se raggiunge con ssh la stessa
// macchina del suo aggancio (campo attach), o se nessuno dei due passa da ssh. Dopo Sposta su lo stesso id
// c'è su due macchine: "claude attach a1" è la copia di qui, "ssh -t amaltea … attach a1" quella di amaltea.
const dentro = (a, id) => typeof a === "string" &&
  new RegExp(`\\battach['"]?\\s+['"]?${id.replace(/[^\w-]/g, "")}\\b`).test(a);
export const agganciata = (argv, s) => Array.isArray(argv) && !!s?.id &&
  ((argv.includes("attach") && argv.includes(s.id)) || argv.some((a) => dentro(a, s.id))) && stessoPosto(argv, s);

// La macchina che un argv raggiunge con ssh: il primo argomento di ssh che non è un'opzione, senza
// "utente@", in minuscolo. null se l'argv non passa da ssh. Vale anche dentro la riga di una shell
// (sh -c "while :; do ssh … attach <id>; …", pwsh -Command "& '…ssh.exe' '-t' 'amaltea' …").
const OPZIONI_CON_VALORE = new Set("bBcDEeFIiJLlmOoPpQRSWw");
export function sshDi(argv) {
  if (!Array.isArray(argv)) return null;
  const p = argv.flatMap((a) => (/\s/.test(String(a ?? "")) ? String(a).split(/[\s;&|()]+/) : [String(a ?? "")]))
    .map((x) => x.replace(/^['"]+|['"]+$/g, "")).filter(Boolean);
  const i = p.findIndex((x) => /(^|[\\/])ssh(\.exe)?$/i.test(x));
  if (i < 0) return null;
  for (let j = i + 1; j < p.length; j++) {
    const x = p[j];
    if (x.startsWith("-")) { if (x.length === 2 && OPZIONI_CON_VALORE.has(x[1])) j++; continue; }
    return x.replace(/^[^@]*@/, "").toLowerCase();
  }
  return null;
}
// L'argv raggiunge la macchina di `s`. Una riga senza argv d'aggancio (un'interattiva) non lo dice: vale.
export const stessoPosto = (argv, s) => !Array.isArray(s?.attach) || !s.attach.length || sshDi(argv) === sshDi(s.attach);

// L'id della sessione che l'argv di una scheda aggancia, nelle stesse due forme: "attach" come parola a
// sé (Mac, Linux) o dentro la riga di una shell, come pwsh -Command "& '…' 'attach' '<id>'" su Windows.
// Senza la seconda forma, su Windows la testata, il pannello Da fare e Lavoraci non vedevano mai la
// sessione agganciata (12/11/2026). "" se l'argv non aggancia niente.
export function idAggancio(argv) {
  if (!Array.isArray(argv)) return "";
  const i = argv.indexOf("attach");
  if (i >= 0) return String(argv[i + 1] ?? "");
  for (const a of argv) {
    const m = typeof a === "string" && a.match(/\battach['"]?\s+['"]?([\w-]{4,})/);
    if (m) return m[1];
  }
  return "";
}

// L'argv con cui la scheda lancia l'aggancio. Per ssh aggiunge un tetto alla connessione e il battito:
// senza, una macchina spenta tiene la scheda vuota per più di un minuto, e dopo il sonno del portatile
// la scheda resta ferma su una connessione morta, che il clic riporta davanti com'è. Col battito ssh
// esce entro 45 secondi, la scheda resta con la shell e il clic dopo rilancia l'aggancio.
// L'argv dell'elenco (campo attach) resta quello della sonda: lo leggono microfono.js e i confronti.
export const OPZIONI_SSH = ["-o", "ConnectTimeout=10", "-o", "ServerAliveInterval=15", "-o", "ServerAliveCountMax=3"];
export function argvScheda(argv) {
  const a = Array.isArray(argv) ? argv.map(String) : [];
  if (a.length < 3 || !/(^|[\\/])ssh(\.exe)?$/.test(a[0]) || a[1] !== "-t" || a.includes("ServerAliveInterval=15")) return a;
  return [a[0], "-t", ...OPZIONI_SSH, ...a.slice(2)];
}

// Windows. Un programma con un percorso di Windows (C:\... o C:/...): la scheda che lo lancia ha PowerShell.
export const percorsoWindows = (a) => /^[A-Za-z]:[\\/]/.test(String(a ?? ""));
// La shell di una scheda è PowerShell (pwsh.exe, powershell.exe, anche col percorso intero).
export const shellPowerShell = (a) => /(^|[\\/])(pwsh|powershell)(\.exe)?$/i.test(String(a ?? ""));
// Lo schermo di una scheda PowerShell finisce col prompt ("PS C:\Users\x>"): il comando è uscito e la
// shell aspetta. Con Claude acceso l'ultima riga è la sua barra; mentre ssh si collega è la riga lanciata.
export function promptPowerShell(schermo) {
  const righe = String(schermo ?? "").replace(/\u001b\[[0-9;?<>]*[A-Za-z]/g, "").split(/\r?\n/).filter((r) => r.trim());
  return righe.length > 0 && /^PS [^>]*>\s*$/.test(righe[righe.length - 1]);
}

// Il rilancio dell'aggancio nella shell rimasta in una scheda (#5637). Prima si pulisce la riga
// (tastiPulizia: fine riga e Ctrl-U, Esc in PowerShell): un mouse rimasto acceso o un testo a metà
// finirebbero davanti al comando. Poi la riga scrive il segno, spegne i modi d'ingresso e lancia
// l'aggancio; quando l'aggancio esce (ssh caduto) li rispegne, come il wrapper delle schede di Herdr.
// motivoUscita legge solo il testo dopo l'ultimo segno.
export const SEGNO_AGGANCIO = "[volta-aggancio]";
// Copia di RESET_INPUT_MODES di src/window.rs (il banco le confronta): mouse, fuoco, incolla e tastiera kitty.
export const RESET_MODI = "test -t 1 && printf '\\033[?1000l\\033[?1002l\\033[?1003l\\033[?1006l\\033[?1015l\\033[?1004l\\033[?2004l\\033[<u'";
export const tastiPulizia = (powershell) => (powershell ? ["esc"] : ["ctrl+e", "ctrl+u"]);
export function rigaRilancio(riga, powershell) {
  if (powershell) return `Write-Host '${SEGNO_AGGANCIO}'; ${riga}`;
  return `printf '%s\\n' '${SEGNO_AGGANCIO}'; ${RESET_MODI}; ${riga}; ${RESET_MODI}`;
}
// Il programma claude dell'argv di aggancio: la parola prima di "attach" ("claude" se l'argv non c'è).
export function programmaClaude(argv) {
  const a = Array.isArray(argv) ? argv.map(String) : [];
  const i = a.indexOf("attach");
  return i > 0 ? a[i - 1] : "claude";
}

// Perché Claude è uscito dalla scheda appena agganciata, dallo schermo della scheda (hc read): la
// frase per la riga della sessione, e `fermo` quando riprovare o riavviare non cambia niente (la causa
// sta nella macchina o nella connessione). null se lo schermo non dice niente di riconoscibile.
// Conta solo l'ultimo tentativo: il testo dopo l'ultimo segno del rilancio, o senza segno dopo l'ultimo
// comando di aggancio scritto nella shell. "Non trovo claude" vale solo se la riga dell'errore nomina il
// programma claude dell'argv (#5629): un "No such file or directory" nel testo di Claude non è quello.
const USCITE = [
  [/EINTR|Interrupted system call/, (m) => `Su ${m} Claude non riesce a leggere la cartella della sessione (Interrupted system call): finché ${m} non torna a posto le sessioni ferme non ripartono.`],
  [/Host key verification failed/, (m) => `ssh non riconosce ${m} (Host key verification failed): collegati una volta a mano da un terminale.`],
  [/Permission denied \(/, (m) => `${m} rifiuta l'accesso via ssh (Permission denied).`],
  [/Could not resolve hostname|No route to host|Network is unreachable|Operation timed out|Connection timed out|Connection refused|Connection closed by|Connection reset/, (m) => `${m} non si raggiunge via ssh: è spenta, dorme o è fuori rete.`],
  [/No job matching/, (m) => `Su ${m} questa sessione non c'è più: eliminala da Altro.`],
  [/Not logged in/, (m) => `Su ${m} Claude non è collegato all'account (Not logged in): apri Claude su ${m} e fai /login.`],
  [/Workspace not trusted/, (m) => `Su ${m} la cartella della sessione non è fra quelle fidate di Claude (Workspace not trusted).`],
  [/command not found|No such file or directory|is not recognized as/i, (m) => `Su ${m} non trovo il programma claude dove lo cerca l'aggancio.`, true],
];
export function motivoUscita(schermo, s, argv = s?.attach) {
  const m = s?.questa ? "questa macchina" : (s?.macchina ?? s?.host ?? "quella macchina");
  const righe = String(schermo ?? "").replace(/\u001b\[[0-9;?<>]*[A-Za-z]/g, "").split("\n");
  let da = -1;
  righe.forEach((r, i) => { if (r.trim() === SEGNO_AGGANCIO) da = i; });
  // anche la riga di PowerShell, dove ogni argomento sta fra apici: "& '…ssh.exe' … 'attach' 'a8ee6d5e'"
  if (da < 0) { da = 0; righe.forEach((r, i) => { if (/[%$#>]\s.*\battach['"]?\s+['"]?[\w-]{4,}/.test(r)) da = i; }); }
  const dopo = righe.slice(da);
  const coda = dopo.join("\n");
  const claude = programmaClaude(argv).toLowerCase();
  for (const [re, frase, nomina] of USCITE) {
    if (!re.test(coda)) continue;
    if (nomina && !dopo.some((r) => re.test(r) && r.toLowerCase().includes(claude))) continue;
    return { testo: frase(m), fermo: true };
  }
  const u = [...coda.matchAll(/Session \S+ (?:has exited|can't start)\s*(?:\(|—|-)?\s*([^\n]*)/g)].pop();
  const perche = (u?.[1] ?? "").replace(/^[\s(—-]+|[\s).]+$/g, "").slice(0, 90);
  // "before init": il processo della sessione muore prima di caricare la conversazione; il resto del
  // messaggio è un pezzo di traccia interna, che alla persona non dice niente.
  if (/before init/.test(perche)) return { testo: `Su ${m} la sessione non riesce a partire: Claude esce prima di iniziare (${perche.match(/exit \d+ before init/)?.[0] ?? "before init"}). Prova da ${m}, o riavvia ${m}.`, fermo: false };
  if (perche) return { testo: `Su ${m} Claude esce appena parte (${perche}).`, fermo: false };
  return null;
}

// I gesti sulla riga di una sessione in background, oltre al clic che la apre (claude attach, anche se
// lavora): l'anteprima (anteprima() qui sotto, o claude logs senza trascrizione), ferma (stop) se è viva, riavvia (respawn) dopo un errore, elimina
// (rm, con conferma) se è chiusa o in errore. Un'interattiva e una riga vecchia non ne hanno: si aprono e basta.
export function azioni(s) {
  if (!s || s.vecchia || s.tipo !== "background") return [];
  const out = [{ verbo: "logs", testo: "Anteprima" }];
  if (s.stato === "lavora" || s.stato === "aspetta") out.push({ verbo: "stop", testo: "Ferma" });
  if (s.stato === "errore") out.push({ verbo: "respawn", testo: "Riavvia" });
  // Elimina solo su una sessione chiusa o in errore: una ferma ma viva si chiude con Chiudi (/fine e stop)
  if (s.stato === "errore" || chiusa(s)) out.push({ verbo: "rm", testo: "Elimina", conferma: "Sì, elimina" });
  return out;
}

// Il menu del tasto destro su una sessione (#5291), in tre gruppi (menusessione.js). Primo: Apri è il
// clic; Duplica ne apre una nuova e vuota nella stessa cartella, sulla stessa macchina, nello stesso
// progetto; Fork ne apre una con una copia della conversazione; "Sposta in un progetto…" è il taglia e
// incolla (Federico, 12/11/2026: "tagliare"), il dialogo di cambio.js (#5292). Secondo: Rinomina e il
// contesto del progetto (contestoui.js), se la sessione ne ha uno. Terzo: Chiudi (/fine, poi stop, come
// ⌘W) e i gesti di "Altro", senza Ferma: qui la ferma Chiudi. Un'interattiva non ha un lavoro in
// background da fermare: resta senza Chiudi. Una riga vecchia ha solo Riprendi su… e Chiudi.
export function menu(s) {
  // una sessione di una macchina che non risponde: Riprendi su… (14/11/2026), una sessione nuova su
  // un'altra macchina dall'ultima lettura (promptRipresa), e Chiudi con /fine come ⌘W: il congedo aspetta
  // che la macchina torni (passoCongedo, fino a CONGEDO_VECCHIO_MS). La conversazione vera resta là.
  if (s?.vecchia) return s.tipo === "background" && !chiusa(s)
    ? [{ verbo: "riprendi", testo: "Riprendi su…" }, { verbo: "chiudi", testo: "Chiudi con /fine" }] : [];
  if (!s) return [];
  const out = [{ verbo: "apri", testo: "Apri" }, { verbo: "duplica", testo: "Duplica" }, { verbo: "fork", testo: "Fork" },
    { verbo: "progetto", testo: "Sposta in un progetto…" }];
  // Sposta su… (12/11/2026): la stessa conversazione su un'altra macchina, col popup di sposta.js. Solo in
  // background; il menu la toglie se Volta non conosce altre macchine (menusessione.js).
  if (s.tipo === "background") out.push({ verbo: "sposta", testo: "Sposta su…" });
  out.push({ verbo: "rinomina", testo: "Rinomina…" });
  if (s.progetto) out.push({ verbo: "contesto", testo: "Contesto del progetto" });
  // in errore non c'è un /fine da fare: lì c'è Elimina (azioni)
  if (s.tipo === "background" && !chiusa(s) && s.stato !== "errore") out.push({ verbo: "chiudi", testo: "Chiudi con /fine" });
  return out.concat(azioni(s).filter((a) => a.verbo !== "stop"));
}

// I primi due gruppi del menu (copiare e spostare, nome e contesto); il resto va nel terzo, chiudere.
export const GRUPPI_MENU = [["apri", "duplica", "fork", "progetto", "sposta", "riprendi"], ["rinomina", "contesto"]];

// La X della riga (Federico, 12/11/2026: "la X per chiudere e innescare il processo di fine"): su una
// sessione in background viva è Chiudi con /fine, con la conferma; su una chiusa o in errore è Elimina.
// Anche la riga di una macchina che non risponde ha Chiudi, come ⌘W: il congedo aspetta che torni.
// Un'interattiva non ha X: non ha un congedo. Una riga vecchia già chiusa neanche: Elimina vuole la macchina.
export function xRiga(s) {
  if (!s || s.tipo !== "background" || (s.vecchia && chiusa(s))) return null;
  const rm = azioni(s).find((a) => a.verbo === "rm");
  if (rm) return { ...rm, aiuto: "Elimina la sessione" };
  return { verbo: "chiudi", testo: "Chiudi", conferma: "Chiudi con /fine?", aiuto: "Chiudi: Claude salva con /fine, poi la sessione si ferma" };
}

// I gesti che stanno solo nel menu: lavorano sulla riga, senza aprire il riquadro di "Altro".
export const SOLO_MENU = new Set(["apri", "chiudi", "duplica", "fork", "rinomina", "progetto", "sposta", "contesto", "riprendi"]);

// Le voci del menu che aprono il dialogo, e che cosa cambiano.
export const CAMBIA = { rinomina: "nome", progetto: "progetto" };

// Nome e progetto di una sessione si cambiano dalla finestra (#5292). Il nome scritto dalla persona:
// una riga, senza caratteri di controllo, al più 60 caratteri come un titolo. Vuoto vuol dire "torna
// al titolo automatico".
export const nomeNuovo = (testo) => String(testo ?? "").replace(/[\u0000-\u001f\u007f-\u009f]/g, " ").replace(/\s+/g, " ").trim().slice(0, 60).trim();

// Il progetto scritto dalla persona come slug, con la stessa regola di slug() in dati.js: "Due Mondi"
// diventa "due-mondi". Al più 40 caratteri, come la scheda del terminale. Vuoto se non resta niente.
export const progettoNuovo = (testo) => String(testo ?? "").toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "")
  .replace(/[^a-z0-9-]+/g, "-").replace(/^-+|-+$/g, "").slice(0, 40).replace(/-+$/, "");

// I progetti fra cui scegliere nel dialogo: quelli delle sessioni dell'elenco e quelli che passa chi
// chiama (spazi aperti, cartelle della base), senza doppi, in ordine alfabetico. Un nome alternativo vale
// la chiave del suo progetto: una sessione nata nella cartella volta-celeste e il progetto volta
// sono una riga sola, "Volta" (#5506).
export function progettiNoti(dati, altri = []) {
  const visti = new Set();
  for (const p of [...(dati?.sessioni ?? []).map((s) => s.progetto), ...altri]) {
    const k = progettoNuovo(chiaveProgetto(p));
    if (k) visti.add(k);
  }
  return [...visti].sort((a, b) => a.localeCompare(b));
}

// I progetti noti che corrispondono a ciò che la persona sta scrivendo: prima quelli che cominciano così.
export function filtraProgetti(noti, testo, quanti = 8) {
  const f = progettoNuovo(testo);
  const l = noti ?? [];
  // cerca nello slug e nel titolo ("celeste" trova volta-celeste, che si chiama Volta)
  const nomi = (p) => [p, slugDi(nomeProgetto(p))];
  const presi = f ? [...l.filter((p) => nomi(p).some((x) => x.startsWith(f))), ...l.filter((p) => !nomi(p).some((x) => x.startsWith(f)) && nomi(p).some((x) => x.includes(f)))] : l;
  return presi.slice(0, quanti);
}

// La ricerca di ⌘K e ⌘O (#5369, nota di Federico dell'11/11: "accedere a chat e progetti"): un elenco
// solo di sessioni e progetti. Il testo si confronta senza maiuscole, accenti e trattini, col titolo e il
// nome della sessione, col suo progetto e col titolo, lo slug e i nomi alternativi (NOTI) di un progetto.
// Prima chi comincia col testo, poi chi lo contiene; le sessioni chiuse in fondo, perché si riaprono ma
// sono il caso raro. Senza testo: le sessioni vive più recenti (al più VIVE_SENZA_TESTO), poi i progetti
// nell'ordine dato. Con un testo l'ultima voce è sempre "Nuova richiesta" con quel testo, anche quando
// qualcosa corrisponde: chi scrive una frase intera vuole quasi sempre chiederla.
// Righe: { tipo: "sessione", s } | { tipo: "progetto", nome } | { tipo: "nuova", testo }.
export const VIVE_SENZA_TESTO = 5;
const piano = (x) => String(x ?? "").toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, "").replace(/[^a-z0-9]+/g, " ").trim();
const alternativi = (p) => {
  const k = chiaveProgetto(p);
  return k ? Object.keys(NOTI).filter((a) => NOTI[a]?.chiave === k) : [];
};
export function cerca(sessioni, progetti, testo, quanti = 12) {
  const f = piano(testo);
  const ss = [...(sessioni ?? [])].filter((s) => s && s.sessionId).sort((a, b) => tempo(b) - tempo(a));
  const pp = [...new Set((progetti ?? []).filter(Boolean))];
  if (!f) {
    const vive = ss.filter((s) => !chiusa(s)).slice(0, VIVE_SENZA_TESTO).map((s) => ({ tipo: "sessione", s }));
    return [...vive, ...pp.map((nome) => ({ tipo: "progetto", nome }))].slice(0, quanti);
  }
  // 0: comincia col testo, 1: lo contiene, null: niente
  const voto = (campi) => {
    const c = campi.map(piano).filter(Boolean);
    return c.some((x) => x.startsWith(f)) ? 0 : c.some((x) => x.includes(f)) ? 1 : null;
  };
  const prese = [];
  ss.forEach((s, i) => {
    const v = voto([titolo(s), s.nome, s.progetto, s.progetto ? nomeProgetto(s.progetto) : "", ...alternativi(s.progetto), s.id]);
    if (v !== null) prese.push({ riga: { tipo: "sessione", s }, chiusa: chiusa(s) ? 1 : 0, v, i });
  });
  pp.forEach((nome, i) => {
    const v = voto([nome, nomeProgetto(nome), ...alternativi(nome)]);
    if (v !== null) prese.push({ riga: { tipo: "progetto", nome }, chiusa: 0, v, i: ss.length + i });
  });
  prese.sort((a, b) => a.chiusa - b.chiusa || a.v - b.v || a.i - b.i);
  return [...prese.slice(0, quanti - 1).map((x) => x.riga), { tipo: "nuova", testo: String(testo).trim() }];
}

// Il comando di "Nuova richiesta" dalla ricerca: il testo viaggia in esadecimale come in comandoCambio,
// al più TESTO_NUOVA_MAX caratteri (il resto la persona lo scrive nella sessione).
export const TESTO_NUOVA_MAX = 400;
// La checklist manda più righe e più note: il suo tetto è più largo (17/11/2026, provato sul canale background).
export const TESTO_CHECKLIST_MAX = 1000;
export const comandoNuova = (testo) => `arturo.nuova-${codifica(String(testo ?? "").trim().slice(0, TESTO_NUOVA_MAX))}`;

// ⌘N, un compito nuovo (#6186, 20/11/2026): la persona scrive il compito e Volta propone il progetto mentre
// scrive (decisione di Federico: "Volta propone il progetto e Invio conferma"). progettoProbabile dà i progetti
// più probabili per un testo, dal più probabile. `progetti`: [{ chiave, titolo, alias, riga }] nell'ordine
// della barra, che decide i pari. Il testo si confronta senza maiuscole e accenti, a parole intere:
// - "nome: compito": il nome prima dei due punti vale più di tutto (PESO.detto);
// - lo slug, il titolo o un nome alternativo scritti per intero nel testo (PESO.nome, più uno per ogni
//   parola del nome: "sito uf" batte "uf");
// - una parola del testo uguale a una parola del nome (PESO.parola), o quasi uguale (PESO.inizio, vicine());
// - una parola del testo nella riga di stato della scheda (PESO.riga, al più tre).
// Le parole corte e le più comuni non contano: "controlla tutto" non deve proporre un progetto. Sotto
// PESO.inizio il progetto non si propone: una sola parola della riga di stato è rumore (prova dal vero del
// 20/11: "senti il commercialista per il modello 730" proponeva Sentinella e Mercurio).
export const TESTO_COMPITO_MAX = TESTO_CHECKLIST_MAX;
export const PESO = { detto: 40, nome: 10, parola: 4, inizio: 2, riga: 1 };
const COMUNI = new Set(("alla alle allo anche ancora aveva avere bene come cosa cose cosi dalla dalle dello degli della delle dopo dove "
  + "essere fare fatto fino hanno loro meno molto nella nelle nello niente ogni oltre perche pero poco prima quale quando quanto "
  + "quella quelle quello questa queste questi questo sono sopra sotto senza solo sola stata stato suoi sulla sulle tanto tutta tutte tutti tutto "
  + "progetto compito nuovo nuova sistema controlla prepara scrivi manda guarda verifica aggiorna").split(" "));
const parole = (x) => piano(x).split(" ").filter(Boolean);
const conta = (p) => p.length >= 4 && !COMUNI.has(p);
// Due parole quasi uguali: cominciano con le stesse cinque lettere o più e cambiano solo nelle ultime due
// ("preventivi" e "preventivo", "fiscale" e "fiscali"). "senti" non è "sentinella".
const vicine = (a, b) => {
  let n = 0;
  while (n < a.length && n < b.length && a[n] === b[n]) n += 1;
  return n >= 5 && a.length - n <= 2 && b.length - n <= 2;
};
// La parte prima dei due punti di "nome: compito", se è corta (al più tre parole) e il resto non è vuoto.
export function nomeDetto(testo) {
  const m = /^\s*([^:\n]{2,40}):\s+\S/.exec(String(testo ?? ""));
  if (!m || /^https?$/i.test(m[1].trim()) || parole(m[1]).length > 3) return "";
  return m[1].trim();
}
// Il compito su una riga sola, al più TESTO_COMPITO_MAX caratteri. `senzaNome` toglie il "nome:" davanti: vale
// solo per il progetto nuovo che da lì prende il nome, perché "sistema il banco: è rosso" è una frase intera.
export function testoCompito(testo, senzaNome = false) {
  let t = String(testo ?? "");
  if (senzaNome && nomeDetto(t)) t = t.slice(t.indexOf(":") + 1);
  return t.replace(/\s+/g, " ").trim().slice(0, TESTO_COMPITO_MAX);
}
export function votoProgetto(testo, p) {
  const nomi = [...new Set([p?.chiave, p?.titolo, ...(p?.alias ?? [])].map(piano).filter(Boolean))];
  if (!nomi.length) return 0;
  const detto = piano(nomeDetto(testo));
  const t = ` ${piano(testo)} `;
  const pt = parole(testo).filter(conta);
  let v = 0;
  if (detto && nomi.includes(detto)) v += PESO.detto;
  else if (detto.length >= 3 && nomi.some((n) => n.startsWith(detto) || (n.length >= 3 && detto.startsWith(n)))) v += PESO.detto / 2;
  const interi = nomi.filter((n) => n.length >= 3 && t.includes(` ${n} `));
  if (interi.length) v += PESO.nome + Math.max(...interi.map((n) => n.split(" ").length));
  else {
    const pn = [...new Set(nomi.flatMap((n) => n.split(" ")).filter(conta))];
    for (const x of pt) {
      if (pn.includes(x)) v += PESO.parola;
      else if (pn.some((n) => vicine(n, x))) v += PESO.inizio;
    }
  }
  const pr = new Set(parole(p?.riga).filter((x) => x.length >= 5 && !COMUNI.has(x)));
  v += Math.min(3, pt.filter((x) => x.length >= 5 && pr.has(x)).length) * PESO.riga;
  return v;
}
export function progettoProbabile(testo, progetti, quanti = 3) {
  return (progetti ?? []).map((p, i) => ({ k: p?.chiave, v: votoProgetto(testo, p), i }))
    .filter((x) => x.k && x.v >= PESO.inizio).sort((a, b) => b.v - a.v || a.i - b.i).slice(0, quanti).map((x) => x.k);
}

// Il modello piccolo (volta_compito.py) si chiede solo quando serve: un compito di almeno tre parole e
// COMPITO_MODELLO_MIN caratteri che non nomina un progetto per intero. Un nome scritto vale già la proposta.
// Dopo COMPITO_PAUSA_MS senza battute, una volta per testo.
export const COMPITO_PAUSA_MS = 1000;
export const COMPITO_MODELLO_MIN = 12;
export function serveModello(testo, progetti) {
  const t = testoCompito(testo);
  if (t.length < COMPITO_MODELLO_MIN || parole(t).length < 3 || !(progetti ?? []).length) return false;
  return !(progetti ?? []).some((p) => votoProgetto(testo, p) >= PESO.nome);
}

// I progetti per progettoProbabile dalla mappa di shared arturo.progetti (chiave e nomi alternativi portano
// alla stessa voce) e, se c'è, dall'ordine della barra (shared arturo.casa.progetti).
export function progettiPerCompito(mappa, ordine = []) {
  const per = {};
  for (const [k, p] of Object.entries(mappa && typeof mappa === "object" ? mappa : {})) {
    if (!p?.chiave) continue;
    const x = (per[p.chiave] ??= { chiave: p.chiave, titolo: p.titolo ?? null, riga: p.riga ?? "", alias: [] });
    if (k !== p.chiave) x.alias.push(k);
  }
  const prima = (Array.isArray(ordine) ? ordine : []).map((o) => o?.chiave).filter((k) => per[k]);
  return [...new Set([...prima, ...Object.keys(per)])].map((k) => per[k]);
}

// Le righe del dialogo di ⌘N, nell'ordine in cui ↑↓ le scorrono: i progetti proposti (al più tre), poi
// "Progetto nuovo: <slug>" e "Senza progetto". `davanti`: il progetto dello spazio aperto, proposto quando
// il testo ne indica meno di tre. `modello`: lo slug scelto dal modello piccolo (volta_compito.py), che va in
// cima se è un progetto noto. `at`: la riga proposta, cioè il primo progetto, o "Senza progetto" se non c'è
// nessun progetto da proporre. Il progetto nuovo prende il nome da "nome: compito", altrimenti dalle prime
// parole del compito: non è mai la proposta, lo sceglie la persona.
export function scelteCompito(testo, progetti, davanti = null, modello = null) {
  const noti = new Set((progetti ?? []).map((p) => p?.chiave).filter(Boolean));
  const presi = [];
  const metti = (k, perche) => {
    if (k && noti.has(k) && !presi.some((x) => x.slug === k) && presi.length < 3) presi.push({ tipo: "progetto", slug: k, perche });
  };
  metti(modello, "modello");
  for (const k of progettoProbabile(testo, progetti)) metti(k, "testo");
  metti(davanti, "davanti");
  const nome = progettoNuovo(nomeDetto(testo) || parole(testoCompito(testo)).filter(conta).slice(0, 3).join(" "));
  const righe = [...presi];
  if (nome && !noti.has(nome)) righe.push({ tipo: "nuovo", slug: nome });
  righe.push({ tipo: "senza", slug: "" });
  return { righe, at: presi.length ? 0 : righe.length - 1 };
}

// Il comando del dialogo, come lo riceve la barra: "arturo.compito-<slug>-<esadecimale>" per un progetto noto,
// "…-nuovo-<slug>-…" per uno nuovo, "…-senza-progetto-…" senza progetto. Con ⌘Invio il verbo è "compitoapri":
// la sessione nasce e la scheda si apre; con Invio nasce in background e la finestra resta dov'è.
export const SENZA_PROGETTO = "senza-progetto";
export function comandoCompito(riga, testo, apri = false) {
  const dove = riga?.tipo === "progetto" ? riga.slug : riga?.tipo === "nuovo" ? `nuovo-${riga.slug}` : SENZA_PROGETTO;
  return `arturo.compito${apri ? "apri" : ""}-${dove}-${codifica(testoCompito(testo, riga?.tipo === "nuovo" && riga.slug === progettoNuovo(nomeDetto(testo))))}`;
}
// { tipo, slug, testo, apri } o null. `noti`: la mappa dei progetti; un progetto noto che si chiama
// "nuovo-qualcosa" resta quel progetto.
export function leggiCompito(c, noti = NOTI) {
  const m = /^compito(apri)?-([a-z0-9-]+)-((?:[0-9a-f]{4})+)$/.exec(String(c ?? ""));
  if (!m) return null;
  const testo = decodifica(m[3]).replace(/\s+/g, " ").trim().slice(0, TESTO_COMPITO_MAX);
  if (!testo) return null;
  const apri = Boolean(m[1]);
  if (m[2] === SENZA_PROGETTO) return { tipo: "senza", slug: "", testo, apri };
  if (noti?.[m[2]]) return { tipo: "progetto", slug: noti[m[2]].chiave ?? m[2], testo, apri };
  if (m[2].startsWith("nuovo-") && progettoNuovo(m[2].slice(6))) return { tipo: "nuovo", slug: progettoNuovo(m[2].slice(6)), testo, apri };
  // un progetto che la mappa non ha (elenco non ancora letto): /inizio lo trova o lo dice
  return { tipo: "progetto", slug: m[2], testo, apri };
}
// L'avviso dopo Invio: dove è nata la sessione che lavora dietro.
export const avvisoCompito = (progetto, macchina) => `${progetto || "Senza progetto"} · ${macchina}. Claude ci lavora: la trovi nell'elenco e nell'Orchestratore.`;
// Il primo messaggio della sessione nata da ⌘N.
export function promptCompito(x) {
  if (x?.tipo === "progetto") return `/inizio ${x.slug} -- ${x.testo}`;
  if (x?.tipo === "nuovo") return `Progetto nuovo ${x.slug}: crea la scheda e la voce dei task (procedura Nuovo progetto di /tasks), poi esegui: ${x.testo}`;
  return String(x?.testo ?? "");
}

// Il dialogo è un'altra copia del mod: manda il cambio alla barra come comando, lo stesso di herdr-app
// do. Il testo viaggia in esadecimale (quattro cifre per carattere), perché il nome di un comando non
// porta spazi né accenti: "arturo.volta-cambia-<nome|progetto>-<esadecimale>-<chiave>", con la chiave
// macchina:id (#5643): dopo uno spostamento il solo id sta su due macchine.
export const codifica = (testo) => [...String(testo ?? "")].flatMap((c) => c.length === 2 ? [c.charCodeAt(0), c.charCodeAt(1)] : [c.charCodeAt(0)])
  .map((n) => n.toString(16).padStart(4, "0")).join("");
export const decodifica = (hex) => (String(hex ?? "").match(/[0-9a-f]{4}/g) ?? []).map((h) => String.fromCharCode(parseInt(h, 16))).join("");
export const comandoCambio = (s, cosa, valore) => `arturo.volta-cambia-${cosa}-${codifica(valore)}-${chiave(s)}`;

// Il comando di un cambio come lo riceve la barra (senza "arturo."): { cosa, valore, id } con il valore
// già ripulito, oppure null. Un progetto vuoto non è un cambio; un nome vuoto toglie il nome scritto.
export function leggiCambio(c) {
  const m = /^volta-cambia-(nome|progetto)-((?:[0-9a-f]{4})*)-(.+)$/.exec(String(c ?? ""));
  if (!m) return null;
  const valore = m[1] === "nome" ? nomeNuovo(decodifica(m[2])) : progettoNuovo(decodifica(m[2]));
  if (m[1] === "progetto" && !valore) return null;
  return { cosa: m[1], valore, id: m[3] };
}

// La casella di Claude Code è vuota, cioè si può scrivere un comando senza toccare una bozza: fra le
// ultime due righe di bordo c'è il solo segno del prompt, o il suggerimento (Try "..."). Come
// casella_vuota di teletrasporto.py. `schermo` è il testo di hc read.
export const casellaVuota = (schermo) => testoCasella(schermo) === "";

// Il testo nella casella di Claude Code: "" se \u00e8 vuota (o col suggerimento Try "..."), null se lo schermo
// non mostra la casella (un dialogo, la shell). Per casellaVuota e per dire perch\u00e9 una risposta non entra.
export function testoCasella(schermo) {
  const testo = String(schermo ?? "").replace(/\u001b\[[0-9;]*m/g, "").replace(/\u00a0/g, " ")
    .replace(/(\u2500{20,})(\u276f|>|  )/g, "$1\n$2");
  const righe = testo.split("\n").map((r) => r.trim());
  const bordi = righe.map((r, i) => (r.startsWith("\u2500".repeat(20)) && r.endsWith("\u2500") ? i : -1)).filter((i) => i >= 0);
  if (bordi.length < 2) return null;
  const dentro = righe.slice(bordi[bordi.length - 2] + 1, bordi[bordi.length - 1]).filter(Boolean);
  if (!dentro.length) return null;
  if (dentro.length !== 1 || !["\u276f", ">"].includes(dentro[0][0])) return dentro.join(" ").replace(/^[\u276f>]\s*/, "") || null;
  const t = dentro[0].slice(1).trim();
  return t === "" || /^Try ".*"$/.test(t) ? "" : t;
}

// Perch\u00e9 una risposta non entra nella scheda, in parole della persona; null se la casella \u00e8 vuota.
// "la scheda non ha la casella vuota" non diceva cosa c'era (17/11/2026, la checklist di belleville persa).
export function percheNonEntra(schermo) {
  const t = testoCasella(schermo);
  if (t === "") return null;
  if (t === null) return "la scheda non mostra la casella di Claude Code (un dialogo, o la sessione non \u00e8 pronta)";
  return `nella casella c'\u00e8 gi\u00e0 un testo: "${t.slice(0, 80)}"`;
}

// Il nome scritto dalla persona va portato in Claude Code con /rename (campo daPortare della sonda):
// solo quando la sessione è ferma, perché un comando scritto mentre lavora finirebbe in coda al turno.
export const daPortare = (s) => (s && !s.vecchia && s.stato === "ferma" && typeof s.daPortare === "string" && s.daPortare.trim() ? s.daPortare.trim() : null);

// Il progetto da cui una sessione spostata deve ripartire con /inizio (#5465): solo a sessione ferma,
// mai mentre lavora o aspetta un permesso, e solo uno slug valido (va dentro un comando).
export const daIniziare = (s) => (s && !s.vecchia && s.stato === "ferma" && typeof s.daIniziare === "string"
  && /^[a-z0-9][a-z0-9-]{0,39}$/.test(s.daIniziare) ? s.daIniziare : null);

// Trascinare una sessione su un altro progetto, nella vista per progetto (Federico, 12/11/2026: "voglio
// poter fare drag & drop"). Herdr non ha un trascinamento per i mod: volta.js lo costruisce con
// pressione, movimento e rilascio del mouse. Sotto MOSSA_PX di movimento è un clic, che apre la sessione.
export const MOSSA_PX = 6;
export const mosso = (da, a) => Boolean(da && a) && Math.hypot(a.x - da.x, a.y - da.y) >= MOSSA_PX;

// Lo slug del progetto dove finisce la sessione trascinata `t` ({ s, mosso }) lasciata sul gruppo `g`, o
// null: nella vista per macchina, su "Senza progetto", sul progetto dove sta già, senza movimento, con la
// macchina della sessione che non risponde.
export function arrivoTrascino(t, g, modo) {
  if (!t?.s || !t.mosso || t.s.vecchia || modo !== "progetto" || !g?.chiave) return null;
  if (chiaveProgetto(t.s.progetto) === g.chiave) return null;
  return progettoNuovo(g.chiave) || null;
}

// Il nome della copia di una conversazione: "<titolo> (fork)", entro i 60 caratteri di un titolo.
export const titoloFork = (s) => `${titolo(s).slice(0, 53).trim()} (fork)`;

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

const conversazione = (s) => `${s.host}/${s.sessionId}`;

// Le sessioni che da una lettura all'altra sono passate a "ti aspetta", di qualunque macchina.
// Alla prima lettura nessuna: l'avviso è per un cambio, non per chi aspettava già all'apertura.
export function nuoveInAttesa(prima, dopo) {
  if (!prima) return [];
  const era = new Map((prima.sessioni ?? []).map((s) => [conversazione(s), s.stato]));
  return (dopo?.sessioni ?? []).filter((s) => !s.vecchia && s.stato === "aspetta" && era.get(conversazione(s)) !== "aspetta");
}

// Lo stato di ogni sessione per id corto, per le parti che agganciano una sessione in background in
// una scheda: lì Herdr non ha lo stato del terminale, e lo prendono da qui (shared arturo.volta.stati).
// Lo stesso id su due macchine (una sessione spostata, #5577): resta la copia che non è ferma, come in
// unaPerConversazione; prima vinceva l'ultima dell'elenco, e la scheda mostrava ferma la copia viva.
// Un id su più macchine porta `doppio`: le parti senza elenco (schedeDi di dati.js) sanno così che
// un'etichetta vecchia col solo id non dice quale copia è (#5634).
export function statiCorti(dati) {
  /** @type {Record<string, { stato: string, host: string, doppio?: true }>} */
  const out = {};
  const l = dati?.sessioni ?? [];
  for (const s of l) {
    if (!s.id || s.vecchia) continue;
    if (out[s.id] && out[s.id].stato !== "ferma" && s.stato === "ferma") continue;
    out[s.id] = { stato: s.stato, host: s.host, ...(doppio(l, s.id) ? { doppio: true } : {}) };
  }
  return out;
}

// La versione del mod nel menu di "Impostazioni" (shared arturo.mod, lo scrive controllaMod di volta.js; la disegna Impostazioni di comuni.js):
// "mod abc1234 · 09:52", l'ora dell'ultima installazione (col giorno se non è oggi). Dopo un giorno
// senza riuscire a controllare lo dice, col motivo; così un plugin di Arturo bloccato perché forse manomesso. Dal 13/11 la riga sta nel menu di Impostazioni, e il piede ne mostra solo il pallino (#5371).
export function rigaMod(m, adesso = Date.now()) {
  if (!m?.corta) return null;
  const due = (n) => String(n).padStart(2, "0");
  // Un aggiornamento di Arturo fermato per una possibile compromissione (volta_mod.py programmi): non si riprova da solo.
  const plugin = m.programmi?.plugin;
  if (plugin?.esito === "compromesso") return { testo: `mod ${m.corta} · Arturo non si aggiorna`, avviso: plugin.motivo || "possibile compromissione: non aggiornare e segnalalo" };
  if (m.esito === "errore" && m.giu_da && adesso / 1000 - m.giu_da > 86400) {
    const giorni = Math.floor((adesso / 1000 - m.giu_da) / 86400);
    return { testo: `mod ${m.corta} · non controllo da ${giorni} ${giorni === 1 ? "giorno" : "giorni"}`, avviso: m.motivo ?? "" };
  }
  if (!m.installato) return { testo: `mod ${m.corta}` };
  const d = new Date(m.installato * 1000);
  const oggi = new Date(adesso);
  const giorno = d.toDateString() === oggi.toDateString() ? "" : `${d.getDate()}/${d.getMonth() + 1} `;
  return { testo: `mod ${m.corta} · ${giorno}${due(d.getHours())}:${due(d.getMinutes())}` };
}

// Le animazioni delle righe (#5410). Le sessioni nuove fra due letture: entrano in dissolvenza. Alla prima
// lettura niente, altrimenti tutto l'elenco entrerebbe insieme all'apertura della finestra.
export function entrate(prima, dopo) {
  if (!prima?.sessioni) return [];
  const viste = new Set(prima.sessioni.filter((s) => s?.id).map(chiave));
  return (dopo?.sessioni ?? []).filter((s) => s?.id).map(chiave).filter((k) => !viste.has(k));
}

// I tempi: una riga entra in 180 ms e se ne va in 140 (uscire costa meno che entrare). Le righe di un
// gruppo che si apre entrano una dopo l'altra, 30 ms fra l'una e l'altra, al più 120 ms in tutto.
export const ENTRA = { duration: 180, easing: "ease-out" };
export const ESCE = { duration: 140, easing: "ease-in" };
export const SCALA_MS = 30;
export const SCALA_MAX = 120;

// Opacità e transizione di una riga. `entra`: { fase, ritardo } di una riga che entra, o undefined. In fase
// "prima" la riga disegna 0 senza transizione, così il motore parte da lì; in fase "via" chiede 1 con ENTRA
// e il ritardo della scala. `esce`: la riga se ne va, verso 0 con ESCE.
export function motoRiga(entra, esce) {
  if (esce) return { opacita: 0, politica: ESCE };
  if (entra?.fase === "prima") return { opacita: 0, politica: null };
  if (entra?.fase === "via") return { opacita: 1, politica: { ...ENTRA, delay: entra.ritardo ?? 0 } };
  return { opacita: 1, politica: ENTRA };
}
export const ritardo = (i) => Math.min(i * SCALA_MS, SCALA_MAX);

// Sposta su e Sposta tutto su (sposta.js, 12/11/2026): chi si sposta e come si conta.
// Perché la sessione non si può spostare, o null. Solo quelle in background: un'interattiva sta in un
// Terminale, e il suo processo non si ferma da qui. Una che lavora si sposta lo stesso, a turno finito
// (aFineTurno): la coda di volta.js aspetta che il turno finisca.
export function nonSiSposta(s) {
  if (!s) return "Nessuna sessione in questa scheda.";
  if (s.tipo !== "background") return "Si spostano solo le sessioni in background, non quelle aperte in un Terminale.";
  return null;
}

// Una sessione che sta facendo un turno parte dopo, quando il turno finisce.
export const aFineTurno = (s) => s?.stato === "lavora";

// Le sessioni di "Sposta tutto su <dest>": in background, vive (né chiuse, né in errore, né di una
// macchina che non risponde), non già su `dest`. `sessioni` è l'elenco visibile di Volta (visibili()).
export const spostabili = (sessioni, dest) => (sessioni ?? []).filter((s) => !s.vecchia && !chiusa(s)
  && s.stato !== "errore" && !nonSiSposta(s) && (s.host ?? "qui") !== dest);

// Quello che passa al popup, che è un'altra copia del mod: i soli campi che servono, non la riga intera.
export const perSposta = (s) => (s ? { id: s.id, sessionId: s.sessionId, host: s.host ?? "qui", macchina: s.macchina,
  tipo: s.tipo, stato: s.stato, titolo: titolo(s), progetto: s.progetto ?? null } : null);

// Il conto di "Sposta tutto" su `dest`, per il popup: "3 sessioni", "3 sessioni, 1 a turno finito".
export function contoTutto(sessioni, dest) {
  const l = spostabili(sessioni, dest);
  if (!l.length) return { n: 0, testo: "niente da spostare" };
  const dopo = l.filter(aFineTurno).length;
  return { n: l.length, testo: `${l.length === 1 ? "1 sessione" : `${l.length} sessioni`}${dopo ? `, ${dopo} a turno finito` : ""}` };
}

// La macchina dove nasce un progetto aperto da Volta. La scheda del progetto nella memoria dice in
// `macchina:` dove sta la sua cartella, con etichette corte scelte dalla persona ("ufficio", "portatile").
// Volta conosce le macchine coi nomi di Herdr (host e nome leggibile). Un'etichetta vale per una macchina
// quando, tolti spazi e segni, sta dentro il suo host o il suo nome. Torna l'host della prima macchina della
// scheda che risponde, oppure null: la cartella c'è anche qui, la scheda non lo dice, o nessuna risponde.
// Con null vale "Nasce su", come prima.
const compatto = (x) => String(x ?? "").toLowerCase().replace(/[^a-z0-9]/g, "");
export function macchinaDelProgetto(etichette, macchine) {
  const voglio = (etichette ?? []).map(compatto).filter(Boolean);
  const tutte = Array.isArray(macchine) ? macchine : [];
  const questa = tutte.find((m) => m?.questa);
  if (!voglio.length || !questa) return null;
  const tocca = (m, e) => compatto(m?.host).includes(e) || compatto(m?.macchina).includes(e);
  if (voglio.some((e) => tocca(questa, e))) return null;
  for (const e of voglio) {
    const m = tutte.find((x) => x && !x.questa && !x.giu && x.host && tocca(x, e));
    if (m) return m.host;
  }
  return null;
}

// La checklist della ripartenza (17/11/2026). /inizio scrive l'elenco numerato (ripartenza-scrivi.py della
// config), la sonda lo porta in s.ripartenza, il dialogo di checklist.js lo mostra con una casella e una
// nota per riga. Federico: "voglio poter vedere una checklist con spazio per eventuali note per poter
// indicare ad Arturo e Volta su cosa lavorare".

// Le voci della ripartenza, in fila come nel terminale.
export const vociRipartenza = (r) => (Array.isArray(r?.filoni) ? r.filoni : []).flatMap((f) => (Array.isArray(f?.voci) ? f.voci : []));

// La lista della checklist, da due fonti (Federico, 17/11: "deve funzionare associandola a tutte le convo e i
// progetti"). Con la ripartenza di /inizio vale quella, coi suoi numeri. Senza, le voci sono i task aperti del
// progetto della sessione (`vista`: l'uscita di `arturo todo --progetto X --json`, la stessa del pannello Da
// fare), divisi per chi agisce e numerati da 1. Ogni voce con un ID si lega al todo della vista (`todo`): da lì
// vengono titolo esatto e chi lo fa, che servono ai gesti. Torna { fonte, filoni, partenza } o null.
export const GRUPPI_CHECKLIST = [["tu", "Tocca a te"], ["decidi", "Decidi tu"], ["io", "Ci pensa Claude"], ["fermo", "Fermi"]];
export function listaChecklist(ripartenza, vista) {
  const todi = new Map();
  for (const g of vista?.gruppi ?? []) for (const t of g?.todo ?? []) if (Number.isInteger(t?.id)) todi.set(t.id, t);
  const lega = (v) => ({ ...v, todo: Number.isInteger(v.id) ? todi.get(v.id) ?? null : null });
  if (vociRipartenza(ripartenza).length) {
    return { fonte: "ripartenza", partenza: ripartenza.partenza ?? null,
      filoni: ripartenza.filoni.map((f) => ({ nome: f.nome ?? "", voci: (f.voci ?? []).map(lega) })).filter((f) => f.voci.length) };
  }
  let n = 0;
  const filoni = GRUPPI_CHECKLIST.map(([tipo, nome]) => ({ nome,
    voci: ((vista?.gruppi ?? []).find((g) => g?.tipo === tipo)?.todo ?? []).filter((t) => Number.isInteger(t?.id))
      .map((t) => ({ n: ++n, id: t.id, testo: String(t.titolo ?? ""), marca: "", sotto: "", todo: t })) }))
    .filter((f) => f.voci.length);
  return filoni.length ? { fonte: "progetto", partenza: null, filoni } : null;
}

// Le scelte che restano quando la lista si rifà: un task nuovo nel progetto, uno chiuso altrove, una rilettura
// che cambia l'ordine. `vecchie`: { [n]: { spunta, gesto, nota, aperta } } sulla lista di prima. Una voce si
// riconosce dall'ID del task, o dal numero se non ne ha; con un'altra sessione, un'altra fonte o un'altra
// ripartenza non resta niente. Torna le scelte sui numeri della lista nuova.
export function riportaScelte(prima, dopo, vecchie = {}) {
  const out = {};
  if (!prima || !dopo || prima.fonte !== dopo.fonte || prima.sessione !== dopo.sessione || prima.quando !== dopo.quando) return out;
  const chi = (v) => (Number.isInteger(v.id) ? `#${v.id}` : `n${v.n}`);
  const per = new Map();
  for (const v of (prima.filoni ?? []).flatMap((f) => f?.voci ?? [])) if (vecchie?.[v.n]) per.set(chi(v), vecchie[v.n]);
  for (const v of (dopo.filoni ?? []).flatMap((f) => f?.voci ?? [])) if (per.has(chi(v))) out[v.n] = per.get(chi(v));
  return out;
}

// I gesti di una riga, oltre alla casella "lavoraci adesso": l'etichetta e la parola nel testo per la sessione.
// "chi" passa il task a Claude, o alla persona se è già di Claude.
export const GESTI_CHECKLIST = [["fatto", "Già fatto", "Già fatto"], ["scarta", "Scarta", "Scartati"], ["rimanda", "Rimanda", "Rimandati"], ["chi", "A Claude", "A Claude"]];
export const etichettaGesto = (g, v) => (g === "chi" && v?.todo?.chi === "io" ? "A te" : GESTI_CHECKLIST.find((x) => x[0] === g)?.[1] ?? "");

// Il testo che torna alla sessione. `lista`: quella di listaChecklist, oppure la sola ripartenza (le prove di
// prima). `scelte`: { [n]: { spunta, gesto, nota } }; `generale`: la nota in fondo. Solo le righe scelte, in
// ordine: "Lavora su 2 5. Già fatto: 3. Scartati: 4. Note: 7: testo. Nota generale". Con la ripartenza si
// usano i numeri, che la sessione conosce (FASE 3 di /inizio); coi task del progetto "#ID titolo corto",
// perché la sessione quei numeri non li ha visti. Niente di scelto né scritto: "".
export function testoChecklist(lista, scelte = {}, generale = "") {
  const pulito = (x) => String(x ?? "").replace(/\s+/g, " ").trim();
  const l = lista?.fonte ? lista : { fonte: "ripartenza", filoni: lista?.filoni ?? [] };
  const voci = (l.filoni ?? []).flatMap((f) => f?.voci ?? []);
  // il titolo corto si ferma a una parola intera, senza puntini: la frase chiude col suo punto
  const corto = (t) => (t.length > 40 ? t.slice(0, 41).replace(/\s+\S*$/, "").replace(/[\s,;:.(–-]+$/, "") : t);
  const rif = (v) => (l.fonte === "progetto" && Number.isInteger(v.id) ? `#${v.id} ${corto(pulito(v.testo))}` : String(v.n));
  const sep = l.fonte === "progetto" ? "; " : " ";
  const elenco = (filtro) => voci.filter(filtro).map(rif);
  const parti = [];
  const prese = elenco((v) => scelte?.[v.n]?.spunta);
  if (prese.length) parti.push(`Lavora su ${prese.join(sep)}.`);
  for (const [g, , parola] of GESTI_CHECKLIST) {
    const x = voci.filter((v) => scelte?.[v.n]?.gesto === g);
    if (g === "chi") {
      const a = x.filter((v) => v.todo?.chi !== "io").map(rif);
      const b = x.filter((v) => v.todo?.chi === "io").map(rif);
      if (a.length) parti.push(`A Claude: ${a.join(sep)}.`);
      if (b.length) parti.push(`A me: ${b.join(sep)}.`);
    } else if (x.length) parti.push(`${parola}: ${x.map(rif).join(sep)}.`);
  }
  const note = voci.map((v) => [v, pulito(scelte?.[v.n]?.nota)]).filter(([, t]) => t).map(([v, t]) => `${rif(v)}: ${t}`);
  if (note.length) parti.push(`Note: ${note.join("; ")}.`);
  const g = pulito(generale);
  if (g) parti.push(g);
  return parti.join(" ");
}

// La ripartenza è già stata mandata? `mandate`: { [sessionId]: quando } (shared arturo.checklist.mandate).
// Un /inizio nuovo scrive un quando nuovo: la checklist torna.
export const checklistMandata = (s, mandate) => Boolean(s?.ripartenza && mandate?.[s.sessionId] === s.ripartenza.quando);

// La checklist mandata resta in bozza finché la risposta non arriva (17/11/2026, Federico: "in tante
// sessioni la lista dei todo inviati non arriva"). Prima "Manda" segnava la ripartenza come mandata e
// azzerava scelte e note anche quando rispondiCoda falliva: la lista spariva. `stato`: { bozze, mandate,
// aperte } di shared arturo.checklist.*; `bozza` di una sessione: { quando, ripartenza, lista, scelte,
// generale, testo }. `esito`: { ok, errore, testo } di rispondiCoda: vale solo col testo della bozza, perché
// anche le carte della Coda passano di lì. Arrivata: la bozza esce e la ripartenza è mandata.
// Persa: la bozza resta con l'errore e il blocco si riapre, così la checklist rimette scelte e note.
export function dopoRisposta(stato, sid, esito, ora = Date.now()) {
  const bozze = { ...(stato?.bozze ?? {}) }, mandate = { ...(stato?.mandate ?? {}) }, aperte = { ...(stato?.aperte ?? {}) };
  const b = bozze[sid];
  if (!sid || !b || b.errore || String(b.testo ?? "").trim() !== String(esito?.testo ?? "").trim()) return null;
  if (esito?.ok) {
    delete bozze[sid];
    if (b.ripartenza) mandate[sid] = b.ripartenza;
  } else {
    bozze[sid] = { ...b, errore: String(esito?.errore || "la sessione non ha risposto").slice(0, 200), persa: ora };
    aperte[sid] = true;
  }
  return { bozze, mandate, aperte };
}

// Le scelte di una bozza persa sulla lista mostrata adesso, per numero di riga (riportaScelte: per ID del
// task), con la nota generale e il motivo. null se la bozza non è persa o è già stata ripresa.
export function bozzaPersa(bozza, lista, ripresa = null) {
  if (!bozza?.errore || !lista || bozza.quando === ripresa) return null;
  return { scelte: riportaScelte(bozza.lista, lista, bozza.scelte ?? {}), generale: String(bozza.generale ?? ""), errore: bozza.errore, quando: bozza.quando };
}

// La prova senza mouse della checklist sovrapposta (17/11/2026): `passi` sono i gesti di una persona, in ordine,
// ognuno { id | n, fai: "spunta" | "gesto" | "nota", gesto?, testo? }; con `manda` alla fine preme Manda. La parte
// li esegue nel suo timer, con lo stesso codice dei clic (checklist.js provaChecklist).
export const comandoProvaChecklist = (passi, manda = true) => `arturo.checklist-prova-${codifica(JSON.stringify({ passi, manda }))}`;
export function leggiProvaChecklist(hex) {
  try {
    const d = JSON.parse(decodifica(hex));
    const passi = (Array.isArray(d?.passi) ? d.passi : []).filter((p) => p && ["spunta", "gesto", "nota"].includes(p.fai)
      && (Number.isInteger(p.id) || Number.isInteger(p.n)) && (p.fai !== "gesto" || GESTI_CHECKLIST.some((g) => g[0] === p.gesto))).slice(0, 60);
    return { passi, manda: d?.manda === true };
  } catch { return null; }
}

// Il comando che apre la checklist: senza chiave quella della sessione davanti, con la chiave (dalla Coda)
// quella della sessione macchina:id.
export const comandoChecklist = (k = null) => (k ? `arturo.checklist-${k}` : "arturo.checklist");

// I tetti di tempo di Volta, in secondi: una tabella sola per il mod JS e per gli script Python (#5581,
// 17/11/2026). Sta qui perché sessioni.js lo caricano tutti, banchi compresi. volta_sonda.py legge
// l'oggetto TETTI di questo file come JSON: fra le due graffe di TETTI
// solo JSON, chiavi fra virgolette e niente commenti.
//
// `comandi`: quanto Volta aspetta un comando Python (exec di Herdr). Allo scadere Herdr uccide solo il
// figlio diretto (src/mods.rs): hc, ssh e claude lanciati da Python restavano orfani e si accumulavano.
// Per questo Volta passa a ogni comando `--entro`, il tetto meno `margine`: Python si ferma prima e
// chiude da sé i suoi figli.
// `fasi`: i tetti dentro Python. Le somme stanno sotto i comandi (il banco HZ42 tiene i conti):
// nasci aspetta macchine + servizio + nascita, Riavvia servizio + azione, gli altri gesti azione.
// Lo spostamento (volta_sposta.py) lavora staccato, senza la scadenza del comando: `pacco` per ogni pezzo
// che viaggia, `prepara` per la cartella sulla macchina d'arrivo (`clone` il git clone lì dentro), `agenti`
// per una lettura di claude agents, `riparte` per l'attesa della sessione ripresa. Il capo (volta_capo.py)
// gira da launchd: `todo`, `gmail`, `lettura_capo` (la sonda delle sessioni) e `modello` (claude -p).
// `dorme` e `riprova`: una macchina che non ha risposto all'ultima lettura si legge col tetto corto
// `dorme` (il giro non aspetta 40 s un Mac che dorme), e col tetto pieno solo ogni `riprova` secondi.
export const TETTI = {
  "margine": 5,
  "fasi": {
    "macchine": 15,
    "servizio": 120,
    "nascita": 180,
    "azione": 60,
    "lettura": 45,
    "margine_lettura": 3,
    "chiamata_note": 25,
    "giro_note": 50,
    "giro_davanti": 40,
    "remoto": 40,
    "pacco": 300,
    "prepara": 360,
    "clone": 300,
    "agenti": 15,
    "riparte": 90,
    "todo": 120,
    "gmail": 60,
    "lettura_capo": 120,
    "modello": 300,
    "dorme": 2,
    "riprova": 600
  },
  "comandi": {
    "volta": 60,
    "note": 60,
    "davanti": 60,
    "prova": 60,
    "capo": 60,
    "apri": 150,
    "apri_riavvia": 210,
    "azione": 90,
    "respawn": 210,
    "cambia": 90,
    "ripresa": 90,
    "giudice": 90,
    "nasci": 360,
    "sposta": 60,
    "congeda": 400,
    "rispondi": 400,
    "inizia": 400,
    "carte": 15,
    "registro": 15,
    "microfono": 30,
    "porta": 60
  }
};

// Il tetto di un comando in millisecondi, per exec.
export function tettoDi(nome) {
  return TETTI.comandi[nome] * 1000;
}

// Gli argomenti `--entro` per lo script: il tetto del comando meno il margine, in secondi. Vanno subito
// dopo il percorso dello script, prima del sottocomando.
export function entroDi(nome) {
  return ["--entro", String(TETTI.comandi[nome] - TETTI.margine)];
}

// Le attese del mod (#6109, 19/11/2026). Un lavoro "in corso" (un exec, una lettura, uno Sposta) tiene un
// campo acceso finché non torna. Se non torna mai (un exec appeso, un cx.sleep cancellato da un ricarico) il
// campo restava acceso, e quel lavoro non ripartiva più fino al ricarico del mod: è successo il 18/11 al giro
// della barra (VM48). Ogni attesa vale l'ora di partenza: un campo (`this.x = ora`) o una mappa
// (`this.x[k] = ora`). liberaAppese spegne quelle accese da due tetti o più e le elenca per il registro.
// lascia spegne un'attesa solo se è ancora la sua: un'attesa vecchia che torna tardi non spegne la nuova.
// Un valore che non è un numero (true, un indirizzo) non scade mai.
export const appesa = (da, tetto, ora = Date.now()) => typeof da === "number" && ora - da >= 2 * tetto;

// `tetti`: { campo: ms } con il tetto di ogni attesa. Torna [{ attesa, chiave?, ms }] delle attese spente.
export function liberaAppese(o, tetti, ora = Date.now()) {
  const via = [];
  for (const [campo, tetto] of Object.entries(tetti)) {
    const v = o?.[campo];
    if (v && typeof v === "object") {
      for (const [k, da] of Object.entries(v)) if (appesa(da, tetto, ora)) { delete v[k]; via.push({ attesa: campo, chiave: k, ms: ora - da }); }
    } else if (appesa(v, tetto, ora)) {
      o[campo] = false;
      via.push({ attesa: campo, ms: ora - v });
    }
  }
  return via;
}

// Spegne l'attesa `campo` (o la voce `k` della mappa `campo`) se vale ancora `mio`, l'ora con cui è partita.
export function lascia(o, campo, mio, k = undefined) {
  if (k === undefined) { if (o[campo] === mio) o[campo] = false; }
  else if (o[campo]?.[k] === mio) delete o[campo][k];
}
