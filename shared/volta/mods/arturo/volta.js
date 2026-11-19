// Volta nella barra: tutte le sessioni di Claude di tutte le macchine, per macchina o per
// progetto. L'elenco lo scrive volta_sonda.py (accanto a questo file) in ~/.cache/volta/sessioni.json ogni 10 s
// (una finestra di prova nella sua cartella di Herdr: cacheVolta() di dati.js, #5449),
// con le macchine aggiunte a Herdr (#5172); un
// clic aggancia la sessione in una scheda (claude attach, via ssh se è su un'altra macchina), o la
// sposta prima in background se è aperta in un Terminale ed è ferma.
// Spostare in background una sessione aperta in un Terminale (porta-volta) resta a teletrasporto.py, se c'è.
// "Altro" su una sessione in background: anteprima (ultima risposta e ultima azione), ferma, riavvia, elimina (#5172 passo 4).
// Una sessione che passa a "ti aspetta", di qualunque macchina, dà un avviso; lo stato di ogni sessione
// va in shared arturo.volta.stati per le schede che agganciano una sessione in background.
// Il tasto destro su una riga apre il menu della sessione (menusessione.js): Apri, Chiudi, Duplica, Fork
// e i gesti di "Altro" (#5291). Il menu è un'altra copia del mod: manda il gesto qui come comando.
// Rinomina e Cambia progetto, dal menu o col doppio clic sul titolo, aprono il dialogo di cambio.js
// (#5292): il nome e il progetto nuovi vanno nei file della sessione con fonte "persona", sulla scheda
// e, appena la sessione è ferma, in Claude Code con /rename.
// Dopo ogni giro dell'elenco volta_note.py (accanto a questo file) porta le note della finestra (⌘⇧N)
// fra le macchine di Herdr, con l'esito in ~/.cache/volta-note/stato.json (sincronizzaNote, cacheVolta("volta-note")).
// Al più ogni minuto volta_davanti.py scrive su ogni macchina quale ha davanti la persona (l'ultima toccata, #5881),
// in ~/.cache/volta-davanti/davanti.json: le sessioni lo leggono prima di aprire una pagina (giraDavanti).

import { div, svg } from "gpui-kit";
import { h_flex, v_flex } from "gpui-base";
import { theme, exec, readTextFile, writeTextFile, appHome, home, shared, setShared, watchFolder, notify, focused, terminals, spaces, window, settings } from "herdr";
import { impostaProgetti, gruppi, mostrate, inAttesa, daCongedare, restanti, registroProva, daQuanto, ordineGiro, statoGiro, passoGiro, corrente, GIRO_MS, sessioneDi, sessioneDavanti, titolo, dettaglio, clic, MODI, azioni, anteprima, nuoveInAttesa, statiCorti, menu, SOLO_MENU, CAMBIA, leggiCambio, progettiNoti, daPortare, daIniziare, mosso, arrivoTrascino, nomeProgetto, progettoApribile, progettoDi, macchinaQui, GESTI_MAX, visibili, sparite, passoCongedo, diProva, chiusa, chiave, trova, mia, vociRipartenza, checklistMandata, dopoRisposta } from "./sessioni.js";
import { entrate, motoRiga, ritardo, fase, ENTRA, ESCE, SCALA_MAX, occupanti } from "./sessioni.js";
import { ICONA, colore, segno, motoDi, movimento, tasti } from "./comuni.js";
import { SPAZIO, MARGINE, RAGGIO, TESTO, PULSANTE } from "./misure.js";
import { config, apri as apriProgetto, slug, apriSessione, mostra, azioneSessione, copiaSessione, chiudiSchede, chiudiAltrui, cambiaSessione, rinominaSchede, portaNome, portaInizio, spostaScheda, nomiProgetti, esito, altrove, stacca, schedeAgganciate, congedaSessione } from "./dati.js";
import { libero, schedeDi, cacheVolta, spostaSessione, tracciaSposta, nomeMacchina, riprendiSposta, spostamentiInVolo, togliVolo, registra, svuotaRegistro, staccaAggancio, nuda, ioQui } from "./dati.js";
import { voloSposta, VOLO_FRESCO_MS, giuDa, dimenticata, testoHandoff, promptRipresa } from "./sessioni.js";
import { cartellaHandoff, nomeFile, creaCartella, leggiGiu, scriviGiu, riprendiSu, conArturo } from "./dati.js";
import { nonSiSposta, aFineTurno, spostabili, apriSposta, perSposta } from "./sposta.js";
import { apriMenuSessione } from "./menusessione.js";
import { apriCambio } from "./cambio.js";
import { apriChecklist } from "./checklist.js";
import { bersaglio, passo, rigaMicrofono } from "./microfono.js";
import { run, panes } from "herdr";
import { congedoSullaCopia } from "./sessioni.js";
import { xRiga, uscenti, nascitePerAvviso, congediOrfani, tocca, daStaccare, schedeSpente, SCHEDA, daAllineare } from "./sessioni.js";
import { ricordaChiuse } from "./sessioni.js";
import { ANNULLA_MS, inAnnullo, senzaAnnullo, conAnnullo, daAnnullare } from "./sessioni.js";
import { apriContesto } from "./contestoui.js";
import { apriMenuProgetto } from "./menusessione.js";
import { carte, ordineCoda, canaleRisposta, rigaRisposta, senzaRisposte, carteUf, LETTURA_UF_MS, RIMANDA_MS, conCapo, fondiDoppie, testoPerSessione, rigaMisura } from "./sessioni.js";
import { gestoCoda, senzaScartate } from "./sessioni.js";
import { schedeRisposta, rispondiSessione, registraRisposta, prendiCarteUf, apriLink, todo, nuova, scartaCarta, leggiScartate } from "./dati.js";
import { leggiRecenti, riprendiDaSola } from "./dati.js";
import { daRiprendere, testoRipresa } from "./sessioni.js";
import { gestoUf } from "./azioni.js";
import { terminale } from "./casa.js";
import { tettoDi, entroDi, appesa, liberaAppese, lascia, SPOSTA_MAX_MS } from "./sessioni.js";

// Il giro dell'elenco (step 5 del piano di revisione, 17/11/2026): ogni 10 s, e subito dopo un gesto (aggiorna
// chiesto durante un giro ne fa partire un altro alla fine). Con 30 s un cambio arrivava fino a 30 s dopo.
const OGNI = 10000;
// La scrittura del registro resta ogni 30 s: col giro a 10 s sarebbero tre volte tanti processi. Le note
// ogni 2 minuti (step 6, #5583): volta_note.py va su tutte le macchine insieme, e una nota nuova non ha fretta.
const NOTE_MS = 120000, REGISTRO_MS = 30000;
// L'ora di adesso come la scrive la sonda in `letto` (ora locale, "AAAA-MM-GGTHH:MM:SS").
const oraQui = (d = new Date()) => {
  const p = (n) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}T${p(d.getHours())}:${p(d.getMinutes())}:${p(d.getSeconds())}`;
};
// Ogni quanto il mod chiede a volta_mod.py se nel repository c'è un mod nuovo (anche all'apertura).
const OGNI_MOD = 3600000;
// Ogni quanto si guarda se la scheda in primo piano aggancia una sessione di un'altra macchina (microfono.js).
const OGNI_MICROFONO = 2000;
// Ogni quanto si guarda se una scheda che agganciava una sessione è stata chiusa (⌘W, la X): il congedo.
const OGNI_SCHEDE = 3000;
const SPARITE_MAX = 3;
// Il font del terminale come lo dicono le impostazioni (font del layout), per lo schermo di claude logs
// nel riquadro dei gesti: prima era scritto qui fisso (fase 4, #5371).
const fontTerminale = () => {
  try { const f = settings()?.font; return typeof f === "string" && f ? f : "Atkinson Hyperlegible Mono"; } catch { return "Atkinson Hyperlegible Mono"; }
};
// Ogni quanto si guarda se la scheda in primo piano è cambiata, per la riga accesa dell'elenco.
const OGNI_FUOCO = 1000;
// Ogni quanto si guarda se c'è una sessione da chiudere da sola (#5366): una ferma da un'ora non ha fretta.
const OGNI_AUTO = 60000;
// la ripresa da sola (#5882): la stessa sessione non si riprova prima di due minuti
const RIPROVA_MS = 2 * 60000;
// Ogni quanto si ridisegna la riga "Si chiude fra N s · Annulla" di una sessione appena chiusa (#5883).
const OGNI_ANNULLO = 1000;
// il giro della macchina davanti (#5881): al più uno al minuto
const DAVANTI_MS = 60000;
// La sessione è già agganciata in un Terminale fuori dalla finestra: la frase del primo clic, e per
// quanto resta sulla riga. Finché c'è, il clic dopo stacca quel Terminale e apre la scheda qui.
const ALTROVE = "È aperta in un Terminale. Un altro clic la porta qui.";
const ALTROVE_MS = 20000;
// Il tetto di ogni attesa del mod (#6109, liberaAppese di sessioni.js): il tetto del comando che l'attesa
// aspetta, o il più lungo se ne aspetta più d'uno. Dopo due tetti l'attesa si spegne e il registro lo dice.
// Uno Sposta aspetta l'esito fino a SPOSTA_MAX_MS. Il giro dell'elenco (inCorso) e il congedo hanno la
// loro guardia, con giroN e this.congedo.
const TETTI_ATTESE = () => ({ noteInCorso: tettoDi("note"), davantiInCorso: tettoDi("davanti"), micLavora: tettoDi("microfono"),
  leggoUf: tettoDi("capo"), autoLavora: tettoDi("azione"), riprendoDaSola: tettoDi("ripresa"), handoffLavora: tettoDi("azione"),
  staccoLavora: tettoDi("congeda"), allineaLavora: tettoDi("congeda"), orfaniLavora: tettoDi("respawn"), spostando: SPOSTA_MAX_MS,
  apro: tettoDi("nasci"), sposto: tettoDi("porta"), porto: tettoDi("cambia"), inizio: tettoDi("inizia") });
// il controllo del mod: volta_mod.py controlla (300 s) più stato (20 s)
const TETTO_MOD = 320000;

// Il mod si aggiorna da solo: volta_mod.py (fuori dalla cartella del mod, così un mod rotto non lo
// ferma) scarica, controlla con herdr-app check e scambia; Herdr ricarica il mod a file cambiati.
// Poi la versione installata e l'ultimo esito vanno in shared arturo.mod, per il piede della barra:
// { corta, installato, esito, giu_da, motivo }. Senza volta_mod.py o senza sorgente non fa niente.
let controlloMod = false;
export async function controllaMod(py) {
  const script = `${appHome()}/volta_mod.py`;
  // un controllo che non torna non ferma l'aggiornamento del mod per sempre (#6109)
  if ((controlloMod && !appesa(controlloMod, TETTO_MOD)) || !(await esiste(script))) return;
  if (controlloMod) registra("attesa appesa", { attesa: "controlloMod", ms: Date.now() - controlloMod });
  const mio = (controlloMod = Date.now());
  try {
    await exec(py, [script, "controlla"], { timeout: 300000 });
  } catch { /* l'esito sta in mod-stato.json */ }
  try {
    const r = await exec(py, [script, "stato"], { timeout: 20000 });
    // l'ultima riga JSON, come dati.js (#5578): un avviso stampato dopo il JSON non perde lo stato
    const d = esito(r);
    if (d.sorgente) setShared("arturo.mod", { corta: d.installato?.corta ?? null, installato: d.installato?.installato ?? null,
      esito: d.esito ?? null, giu_da: d.giu_da ?? null, motivo: d.motivo ?? null, modo: d.modo ?? null,
      programmi: d.programmi ?? null });
  } catch { /* resta l'ultimo stato letto */ }
  if (controlloMod === mio) controlloMod = false;
}

// La frase della riga mentre un gesto del menu lavora, e quella che resta qualche secondo a gesto fatto.
const LAVORO = { chiudi: "La chiudo…", duplica: "La duplico…", fork: "Copio la conversazione…", nome: "Cambio il nome…", progetto: "Cambio il progetto…" };
const FATTO = { stop: "Fermata: un clic la riapre.", respawn: "Riavviata.", rm: "Eliminata.",
  chiudi: "Chiusa: Claude salva con /fine, poi si ferma.", duplica: "Duplicata: la sessione nuova è nella sua scheda.",
  fork: "Copiata: la copia è nella sua scheda." };

// "Riduci movimento" del sistema (Mac: Accessibilità > Schermo), in shared arturo.movimento.ridotto per
// movimento() di comuni.js. Le transizioni lo seguono già da sole; loop e rotazioni no. Si legge all'avvio:
// chi lo cambia riapre la finestra o aspetta il mod ricaricato. Altrove resta com'è.
// Su Windows è "Mostra animazioni in Windows" (Impostazioni > Accessibilità > Effetti visivi), letto con
// SystemParametersInfoW(SPI_GETCLIENTAREAANIMATION) dal Python di arturo.json (12/11/2026: prima su
// Windows la stella girava e il pallino pulsava anche con le animazioni spente).
export const RIDOTTO_WINDOWS = "import ctypes\nb = ctypes.c_int(1)\nctypes.windll.user32.SystemParametersInfoW(0x1042, 0, ctypes.byref(b), 0)\nprint(0 if b.value else 1)";
async function ridotto(py = "python") {
  try {
    const p = window()?.platform;
    const r = p === "macos" ? await exec("defaults", ["read", "com.apple.universalaccess", "reduceMotion"], { timeout: 5000 })
      : p === "windows" ? await exec(py, ["-c", RIDOTTO_WINDOWS], { timeout: 10000 }) : null;
    if (!r) return;
    const v = r.code === 0 && r.stdout.trim() === "1";
    if (shared("arturo.movimento.ridotto") !== v) setShared("arturo.movimento.ridotto", v);
  } catch { /* senza defaults o senza Python resta acceso */ }
}

async function esiste(p) {
  try { return (await readTextFile(p)) ? p : null; } catch { return null; }
}

// Lo script dell'elenco: volta_sonda.py come lo dice config() di dati.js, se c'è.
// Quello che sposta le sessioni del Terminale: teletrasporto.py della config, se c'è.
async function script(c) {
  return { elenco: await esiste(c.volta), sposta: await esiste(`${home()}/.claude/scripts/teletrasporto.py`) };
}

export class Volta {
  init(cx) {
    this.cartella = cacheVolta();
    this.file = `${this.cartella}/sessioni.json`;
    this.dati = null;
    this.avvisi = {};
    this.sposto = {};
    this.apro = {};        // chiave -> ora di partenza mentre il clic prepara la scheda (servizio, respawn)
    this.veglio = {};      // chiave -> true mentre si guarda se Claude resta nella scheda appena aperta
    this.aperti = {};
    this.menu = null;      // la chiave della sessione con i gesti aperti
    // Le mappe delle sessioni vanno per chiave (macchina:id, chiave() di sessioni.js, #5634): dopo Sposta su
    // lo stesso sessionId c'è su due macchine, e un /clear lo cambia.
    this.anteprime = {};   // chiave -> true (risposta e azione lette dalla riga) o righe di claude logs
    this.chiedo = {};      // chiave -> verbo che aspetta la conferma
    this.faccio = {};      // chiave -> verbo in corso
    this.codaSposta = {};  // chiave -> { macchina, id, da, dopo }: Sposta su e Sposta tutto, una alla volta
    this.sopra = null;     // la sessione sotto il puntatore: lì compare la X
    this.porto = {};       // chiave -> ora di partenza mentre il nome scritto dalla persona va in Claude Code
    this.inizio = {};      // chiave -> ora di partenza mentre la sessione spostata riparte da /inizio (#5465)
    this.trascino = null;  // { s, da, mosso, sopra }: la sessione che la persona sta trascinando su un progetto
    this.trascinata = 0;   // quando è finito l'ultimo trascinamento: il rilascio sulla riga non è un clic
    this.spostate = {};    // chiave -> slug: spostate da questa finestra, che sola può riprenderle
    this.script = undefined;
    this.py = "python3";
    this.mic = null;       // il ponte del microfono acceso da questa finestra (passo di microfono.js)
    this.micScript = null; // volta_microfono.py, se c'è
    this.micLavora = false;
    this.schede = null;    // { indirizzo: sessione } al giro di prima: una che sparisce è una scheda chiusa
    this.congedo = {};     // chiave -> true mentre un passo del congedo lavora
    this.entrano = new Map(); // chiave -> { fase, ritardo } delle righe che entrano in dissolvenza (#5410)
    this.escono = {};      // chiave -> true mentre la riga di una sessione in congedo si dissolve
    this.noteScript = null; // volta_note.py, se c'è: le note della finestra uguali su tutte le macchine
    this.noteInCorso = false;
    this.davantiScript = null; // volta_davanti.py, se c'è: la macchina davanti alla persona (#5881)
    this.davantiInCorso = false;
    this.davantiUltimo = 0;
    this.autoLavora = false;   // l'ora di partenza mentre congedaFerme lavora: un giro alla volta
    this.staccoLavora = false; // l'ora di partenza mentre staccaFerme lavora
    this.noStacco = new Set(); // indirizzi delle schede che non si sono staccate: non si riprovano fino al ricarico
    this.allineaLavora = false; // l'ora di partenza mentre allineaSpazi lavora
    this.allineati = new Set(); // "chiave|progetto" degli spostamenti già fatti: non si ripetono fino al ricarico
    // "Riduci movimento" del sistema: sul Mac subito, su Windows col Python di arturo.json (sotto)
    cx.spawn(async (cx) => {
      // Il Python che installa-herdr.sh ha trovato e scritto in arturo.json: su Windows può essere "python".
      const c = await config();
      this.py = c.arturo[0];
      ridotto(this.py);
      controllaMod(this.py);
      const sc = await script(c);
      // Un ponte rimasto da prima (mod ricaricato, Volta riaperta) si chiude: lo riaccende il primo giro.
      this.micScript = await esiste(`${appHome()}/mods/arturo/volta_microfono.py`);
      if (this.micScript) { try { await exec(this.py, [this.micScript, ...entroDi("microfono"), "spegni"], { timeout: tettoDi("microfono") }); } catch { /* niente ponte */ } }
      this.noteScript = await esiste(`${appHome()}/mods/arturo/volta_note.py`);
      this.davantiScript = await esiste(`${appHome()}/mods/arturo/volta_davanti.py`);
      this.script = sc.elenco;
      this.sposta = sc.sposta;
      if (!this.script) return cx.notify();
      await this.leggiSenzaFermarsi(cx);
      cx.notify();
      this.aggiorna(cx);
      // uno spostamento lasciato a metà dalla ricarica che ha appena caricato questo mod (#5559)
      this.riprendiVolo(cx);
      // Un'altra Volta che riscrive il file: lo si rilegge subito. Solo per sessioni.json (o la cartella
      // intera, che per l'API vuol dire "rileggi tutto"): la cartella tiene anche il clone del mod e i file
      // del microfono, riscritti ogni 2 s, e ogni lotto rileggeva e ridisegnava l'elenco (13/11/2026).
      try {
        for (;;) { if (tocca(await watchFolder(this.cartella), this.cartella, this.file)) { await this.leggiSenzaFermarsi(cx); cx.notify(); } }
      } catch { /* senza cartella resta il timer */ }
    });
    // il timer non mette in coda: con un giro più lungo di OGNI i giri andrebbero di fila
    cx.timer.every(OGNI, (cx) => this.aggiorna(cx, false));
    // il registro su disco anche quando il giro dell'elenco resta appeso (19/11/2026): prima si scriveva solo
    // a giro finito, e nelle 9 ore del giro appeso del 18/11 non ha scritto niente
    cx.timer.every(REGISTRO_MS, () => svuotaRegistro(this.py));
    cx.timer.every(OGNI_MOD, () => controllaMod(this.py));
    cx.timer.every(OGNI_MICROFONO, (cx) => this.microfono(cx));
    cx.timer.every(OGNI_SCHEDE, (cx) => this.guardaSchede(cx));
    // la scheda in primo piano cambiata (un clic in testata, ⌘⇧↓): la riga accesa la segue
    cx.timer.every(OGNI_FUOCO, (cx) => {
      const k = focused()?.terminal ?? null;
      if (k !== this.fuoco) { this.fuoco = k; cx.notify(); this.riaggancia(k, cx); }
      this.davanti(k);
    });
    cx.timer.every(OGNI_ANNULLO, (cx) => this.giraAnnullo(cx));
    cx.timer.every(OGNI_AUTO, (cx) => this.congedaFerme(cx));
    cx.timer.every(OGNI_AUTO, (cx) => this.staccaFerme(cx));
    cx.timer.every(OGNI_AUTO, (cx) => this.allineaSpazi(cx));
    cx.timer.every(OGNI_AUTO, (cx) => { this.avvisaNascite(); this.chiudiOrfani(cx); });
    // le carte UF della Coda dal capo (#5722): subito e ogni cinque minuti; il capo le rifà ogni ora
    this.leggiUf(cx);
    cx.timer.every(LETTURA_UF_MS, (cx) => this.leggiUf(cx));
    // le carte scartate dalla Coda restano fuori anche dopo un riavvio (scartate.json, 16/11/2026)
    cx.spawn(async (cx) => { this.scartate = { ...(await leggiScartate()), ...(this.scartate ?? {}) }; this.aggiornaCoda(); cx.notify(); });
    // e le carte UF già risposte restano fuori fino al giro dopo del capo, anche dopo un riavvio (#5742)
    cx.spawn(async (cx) => { this.risposte = { ...(await leggiRecenti()), ...(this.risposte ?? {}) }; this.aggiornaCoda(); cx.notify(); });
  }

  // Una macchina che smette di far partire sessioni (13/11/2026): un avviso solo per episodio, in shared
  // arturo.volta.nascite ({ host: true }), così un mod ricaricato non lo ripete.
  avvisaNascite() {
    if (!this.dati) return;
    const prima = shared("arturo.volta.nascite") ?? {};
    const { avvisi, viste } = nascitePerAvviso(this.dati, prima);
    for (const testo of avvisi) if (testo) notify({ title: "Sessioni che non partono", body: testo, level: "warning" });
    if (JSON.stringify(viste) !== JSON.stringify(prima)) setShared("arturo.volta.nascite", viste);
  }

  // I congedi rimasti a metà di questa macchina (congediOrfani di sessioni.js): uno alla volta, stop se è
  // ancora viva, rm se è ferma. Un rm rifiutato (un worktree con modifiche) si dice una volta e la riga resta.
  async chiudiOrfani(cx) {
    if (this.orfaniLavora || !this.dati) return;
    const conScheda = new Set(Object.values(this.schede ?? {}).filter((x) => x?.id).map(chiave));
    this.orfaniNo = this.orfaniNo ?? new Set();
    const p = congediOrfani(this.dati, this.congedi(), Date.now(), conScheda).find((x) => !this.orfaniNo.has(chiave(x.s)));
    if (!p) return;
    const mio = (this.orfaniLavora = Date.now());
    try {
      // lo stesso controllo fresco del congedo (#5636): rm e stop si rifiutano se la sessione gira o è agganciata
      const r = await azioneSessione(p.s, p.fai, { congedo: true }).catch((e) => ({ errore: String(e?.message ?? e).slice(0, 160) }));
      if (r?.errore) {
        this.orfaniNo.add(chiave(p.s));
        notify({ title: `${titolo(p.s)}: non riesco a chiuderla`, body: r.errore, level: "warning" });
      } else if (p.fai === "rm" && p.avviso) notify({ title: `${titolo(p.s)}: chiusa`, body: p.avviso, level: "info" });
      this.aggiorna(cx);
      cx.notify();
    } finally { lascia(this, "orfaniLavora", mio); }
  }

  // Le sessioni in congedo (shared, così restano anche se il mod si ricarica): { chiave: c }. Una voce
  // scritta prima del 14/11 sta sotto il sessionId: si legge sotto la sua chiave (#5634).
  congedi() {
    const m = shared("arturo.volta.congedi") ?? {};
    return Object.fromEntries(Object.entries(m).map(([k, c]) => [c?.id ? chiave(c) : k, c]));
  }

  // L'elenco come lo vede chi usa la finestra: senza chiuse e senza sessioni in congedo.
  vis() {
    return visibili(this.dati, this.congedi(), this.chiuse());
  }

  // Le sessioni chiuse da chi usa la finestra e rimaste in claude agents (chiusaDaTe di sessioni.js, 16/11/2026):
  // shared arturo.volta.chiuse, così restano fuori anche se il mod si ricarica.
  chiuse() {
    return shared("arturo.volta.chiuse") ?? {};
  }

  // Segna chiuse le sessioni di un congedo finito: la sessione e, se il congedo era passato alla copia,
  // l'originale. Senza claude rm restano in claude agents, e l'elenco le rimostrava (Federico, 16/11/2026).
  ricorda(c) {
    if (!c?.id) return;
    const voci = [{ host: c.host, id: c.id }, ...(c.copiaDi ? [{ host: c.host, id: c.copiaDi }] : [])];
    setShared("arturo.volta.chiuse", ricordaChiuse(this.chiuse(), voci, Date.now()));
  }

  // Riaperta da chi usa la finestra (clic, ⌘K): via dalle chiuse, torna nell'elenco.
  riapri(s) {
    const ch = this.chiuse();
    if (!s || !ch[chiave(s)]) return;
    const { [chiave(s)]: _, ...resto } = ch;
    setShared("arturo.volta.chiuse", resto);
  }

  // L'elenco disegnato a sinistra: come vis(), e in più le sessioni chiuse da meno di ANNULLA_MS, con la riga
  // "Si chiude fra N s · Annulla" in `annullo` (#5883). Solo per il disegno: Sposta, il giro e la ricerca
  // usano vis(), e una sessione che si sta chiudendo non entra nei loro elenchi.
  visLista(ora = Date.now()) {
    const tutti = this.congedi();
    return conAnnullo(visibili(this.dati, senzaAnnullo(tutti, ora), this.chiuse()), tutti, ora);
  }

  // Il conto alla rovescia delle sessioni appena chiuse (#5883): un disegno al secondo finché ce n'è una, e
  // il passo del congedo appena un'attesa finisce, senza aspettare il giro delle schede.
  giraAnnullo(cx) {
    const ora = Date.now();
    const l = Object.entries(this.congedi()).filter(([, c]) => inAnnullo(c, ora));
    const n = l.length;
    // nell'ultimo secondo la riga si dissolve (#5410), come quella della chiusura automatica
    for (const [k, c] of l) {
      if (!movimento() || this.escono[k] || Number(c.annulla) - ora > OGNI_ANNULLO) continue;
      this.escono[k] = true;
      cx.timer.after(Number(c.annulla) - ora + ESCE.duration + 50, (cx) => { delete this.escono[k]; cx.notify(); });
    }
    if (!n && !this.annulli) return;
    const finita = n < (this.annulli ?? 0);
    this.annulli = n;
    cx.notify();
    if (finita) this.passiCongedo(cx);
  }

  // ⌘Z (Ctrl+Alt+Z su Windows) o il clic sulla riga "Si chiude fra N s · Annulla" (#5883): il congedo non è
  // ancora partito (passoCongedo aspetta), la sua voce si toglie e la sessione si riapre in una scheda, con
  // lo stesso gesto del clic. `k`: la chiave della riga; senza, l'ultima sessione chiusa. Scaduta l'attesa
  // non annulla più niente: /fine potrebbe essere partito. true se ha annullato.
  annulla(k, cx) {
    const tutti = this.congedi(), ora = Date.now();
    const voce = k ? (inAnnullo(tutti[k], ora) ? [k, tutti[k]] : null) : daAnnullare(tutti, ora);
    if (!voce) return false;
    const [kc, c] = voce;
    const { [kc]: _, ...resto } = tutti;
    setShared("arturo.volta.congedi", resto);
    delete this.escono[kc];
    registra("congedo", { macchina: c.host, sid: c.id, esito: "annullato" });
    const s = trova(this.dati?.sessioni, c);
    if (s) this.premi(s, cx);
    cx.notify();
    return true;
  }

  // L'elenco del giro ⌘↓/⌘↑: come vis(), e in più fuori le sessioni che stanno uscendo (la dissolvenza
  // prima del congedo) e quelle con la scheda appena sparita (`forse` di guardaSchede), così un ⌘↓ subito
  // dopo ⌘W non riaggancia la sessione che si sta chiudendo.
  visGiro() {
    return visibili(this.dati, uscenti(this.congedi(), this.escono, this.forse), this.chiuse());
  }

  // Una scheda che agganciava una sessione e non c'è più, chiusa da chi usa la finestra (⌘W, la X,
  // un'uscita della shell): la sessione va in congedo. Il primo giro dopo l'apertura solo guarda.
  // Sicure contro un congedo per sbaglio: un core che non risponde (nessun terminale, anche per un
  // attimo durante un aggiornamento) non chiude niente; una scheda conta come chiusa solo se manca per
  // due giri di fila; più di SPARITE_MAX schede sparite insieme non sono il gesto di chiudere una
  // sessione: dopo tre giri le si lascia andare senza congedo, e lo si dice.
  guardaSchede(cx) {
    if (!this.dati || !terminals().length) return;
    const adesso = schedeAgganciate(this.dati.sessioni);
    // chi gira davvero nel terminale vince sull'aggancio con cui la scheda è nata (occupanti): una scheda
    // occupata da un'altra sessione non è chiusa, e quella di prima non va in congedo (#5630)
    const dentro = occupanti(this.dati.sessioni);
    const ora = sparite(this.schede, adesso, shared("arturo.volta.tolti") ?? {}, Date.now(), dentro);
    if (ora.length > SPARITE_MAX) {
      this.troppe = (this.troppe ?? 0) + 1;
      if (this.troppe < 3) return;
      notify({ title: `${ora.length} schede chiuse insieme`, body: "Le sessioni restano aperte in background: per chiuderle usa Chiudi dal menu di ognuna.", level: "info" });
      ora.length = 0;
    }
    this.troppe = 0;
    const forse = this.forse ?? {};
    const via = ora.filter((c) => forse[chiave(c)]);
    this.forse = Object.fromEntries(ora.filter((c) => !forse[chiave(c)]).map((c) => [chiave(c), c]));
    // una scheda vista sparire una volta sola resta nel giro di prima: al prossimo, se manca ancora, chiude
    for (const [ind, s] of Object.entries(this.schede ?? {})) if (this.forse[chiave(s)] && !(ind in adesso)) adesso[ind] = s;
    this.schede = adesso;
    // Per la testata: la macchina di ogni scheda di questa finestra che mostra una sessione, anche
    // un'interattiva partita nella shell di una scheda; le altre schede sono di questa macchina.
    const qui = macchinaQui(this.dati);
    const dove = Object.fromEntries(Object.entries(adesso).map(([a, s]) => [a, s.questa ? qui : s.macchina]));
    for (const a of Object.keys(dentro)) dove[a] = qui;
    const occupate = Object.fromEntries(Object.entries(dentro).map(([a, s]) => [a, s.id]));
    const m = { qui, schede: dove, occupate };
    if (JSON.stringify(m) !== JSON.stringify(shared("arturo.volta.dove") ?? null)) setShared("arturo.volta.dove", m);
    for (const c of via) this.congeda(c, cx);
    if (Object.keys(this.congedi()).length) this.passiCongedo(cx);
  }

  // Mette una sessione in congedo: /fine, poi claude stop (decisione di Federico, 12/11/2026). Se lavora
  // aspetta che finisca il turno. Una sessione già chiusa non ha niente da salvare. `c.auto`: la chiusura
  // automatica (#5366); con `c.fineFatta` la sessione ha già fatto /fine e si ferma soltanto. `c` porta id e
  // macchina della sessione: dopo Sposta su il solo sessionId c'è anche sulla copia ferma (#5634).
  congeda(c, cx) {
    const s = trova(this.dati?.sessioni, c);
    if (!s || s.tipo !== "background" || chiusa(s) || this.congedi()[chiave(s)]) return;
    // un gesto della persona aspetta ANNULLA_MS prima di /fine (#5883): la riga resta, senza dissolvenza
    const annulla = !c.auto;
    if (!annulla && !c.uscita && this.esce(s, c, cx)) return;
    const ora = Date.now();
    setShared("arturo.volta.congedi", { ...this.congedi(), [chiave(s)]: { sessionId: s.sessionId, id: s.id, host: s.host, macchina: s.macchina,
      cartella: s.cartella ?? null, titolo: titolo(s), fase: "attende", da: ora, dal: ora,
      ...(c.auto ? { auto: true } : {}), ...(c.auto && s.fineFatta ? { fineFatta: true } : {}), ...(annulla ? { annulla: ora + ANNULLA_MS } : {}) } });
    if (this.menu === chiave(s)) this.menu = null;
    cx.notify();
    this.passiCongedo(cx);
  }

  // Le righe che entrano (#5410): un disegno a opacità 0, poi 1 con la transizione. `ids` in ordine: la
  // scala dei ritardi segue l'elenco. Le voci si tolgono a transizione finita, mai a metà (il ritardo fa
  // parte della transizione: toglierlo prima la farebbe saltare).
  entra(ids, cx) {
    if (!ids?.length || !cx || !movimento()) return;
    ids.forEach((k, i) => this.entrano.set(k, { fase: "prima", ritardo: ritardo(i) }));
    cx.timer.after(50, (cx) => {
      for (const k of ids) { const e = this.entrano.get(k); if (e) this.entrano.set(k, { ...e, fase: "via" }); }
      cx.notify();
    });
    cx.timer.after(50 + SCALA_MAX + ENTRA.duration + 60, (cx) => { for (const k of ids) this.entrano.delete(k); cx.notify(); });
  }

  // La riga di una sessione che va in congedo si dissolve prima di sparire: il congedo vero parte dopo
  // ESCE. true se la dissolvenza è partita (o è già in corso), e allora il congedo lo rilancia il timer.
  esce(s, c, cx) {
    if (!movimento()) return false;
    const k = chiave(s);
    if (this.escono[k]) return true;
    this.escono[k] = true;
    cx.notify();
    cx.timer.after(ESCE.duration + 20, (cx) => { delete this.escono[k]; this.congeda({ ...c, uscita: true }, cx); });
    return true;
  }

  // Un passo per ogni sessione in congedo, dallo stato dell'ultima lettura (passoCongedo di sessioni.js).
  passiCongedo(cx) {
    const tutti = this.congedi();
    for (const [kc, c] of Object.entries(tutti)) {
      // un congedo che non torna (19/11/2026) si lascia andare dopo due tetti: prima la sessione restava
      // fuori dall'elenco e accesa sulla sua macchina, senza /fine, fino al ricarico del mod
      if (this.congedo[kc] && Date.now() - this.congedo[kc] < 2 * tettoDi("congeda")) continue;
      if (this.congedo[kc]) registra("congedo appeso", { sid: c.id, ms: Date.now() - this.congedo[kc] });
      // la riga della stessa macchina e dello stesso id: prima bastava il sessionId o l'id, e dopo Sposta su
      // il congedo prendeva la copia ferma (#5634)
      const s = trova(this.dati?.sessioni, c) ?? undefined;
      const p = passoCongedo(c, s, Date.now());
      if (p.avviso) notify({ title: `${c.titolo ?? "Sessione"}: chiusa`, body: p.avviso, level: "warning" });
      if (p.fai === "attendi") continue;
      const scrivi = (cambio) => {
        const ora = this.congedi();
        if (!ora[kc]) return;
        if (cambio === null) { const { [kc]: _, ...resto } = ora; setShared("arturo.volta.congedi", resto); }
        else setShared("arturo.volta.congedi", { ...ora, [kc]: { ...ora[kc], ...cambio } });
      };
      // il congedo finisce e la sessione resta in claude agents: fuori dall'elenco lo stesso (chiuse)
      if (p.fai === "togli" && p.riaperta) {
        // riaperta durante il congedo (#5633): resta aperta, niente stop, e torna nell'elenco
        scrivi(null);
        this.riapri(s);
        registra("congedo", { macchina: s?.host, sid: s?.id ?? c.id, esito: "riaperta" });
        notify({ title: `${c.titolo ?? "Sessione"}: resta aperta`, body: "L'hai riaperta durante la chiusura: non la fermo.", level: "info" });
        continue;
      }
      if (p.fai === "togli") { scrivi(null); this.ricorda(c); continue; }
      // la ripresa con /fine si segna prima di lanciarla (16/11/2026): una ricarica del mod durante la
      // ripresa perdeva this.congedo, e la copia nuova del mod trovava ancora "attende". Toglieva il congedo
      // della sessione ferma (la ripresa poi la riaccendeva fuori dal registro, visibile) o rifaceva /fine.
      if (p.fai === "fine") scrivi({ fase: "fine", dal: Date.now() });
      const mio = (this.congedo[kc] = Date.now());
      cx.spawn(async (cx) => {
        let r;
        try {
          r = p.fai === "fine" ? await congedaSessione({ ...c, id: s?.id ?? c.id }) : await azioneSessione({ ...s, ...c, id: s?.id ?? c.id }, p.fai === "rm" ? "rm" : "stop", { congedo: true });
        } catch (e) { r = { errore: String(e?.message ?? e).slice(0, 120) }; }
        if (this.congedo[kc] !== mio) return;  // lasciato andare per appeso: un altro passo l'ha già ripreso
        delete this.congedo[kc];
        if (r?.rifiutata && p.fai !== "rm") {
          // il controllo fresco sulla macchina (#5636): un'altra scheda la aggancia ancora, o l'hai riaperta
          // tu. La sessione resta aperta e il congedo finisce qui: niente stop dopo il rifiuto.
          notify({ title: `${c.titolo ?? "Sessione"}: resta aperta`, body: r.errore, level: "info" });
          registra("congedo", { macchina: s?.host, sid: s?.id ?? c.id, esito: "rifiutato", errore: r.errore });
          scrivi(null);
        } else if (p.fai === "rm") {
          // /fine ha salvato e la sessione è ferma: claude rm la toglie anche da claude agents (#5401).
          // Se rm non va, la sessione resta lì, già fuori dall'elenco di Volta, e lo si dice.
          if (r?.errore) notify({ title: `${c.titolo ?? "Sessione"}: chiusa`, body: `Salvata con /fine, ma non riesco a eliminarla: ${r.errore}`, level: "warning" });
          scrivi(null);
          this.ricorda(c);
        } else if (r?.errore && p.fai === "fine") {
          // la ripresa con /fine non parte: la sessione si ferma comunque, e lo si dice
          notify({ title: `${c.titolo ?? "Sessione"}: chiusa senza /fine`, body: r.errore, level: "warning" });
          registra("congedo", { macchina: s?.host, sid: s?.id ?? c.id, esito: "senza fine", errore: r.errore });
          const ferma = await azioneSessione({ ...s, ...c, id: s?.id ?? c.id }, "stop").catch((e) => ({ errore: String(e?.message ?? e) }));
          if (ferma?.errore) registra("congedo stop", { macchina: s?.host, sid: s?.id ?? c.id, esito: "errore", errore: ferma.errore });
          // una copia nata dalla ripresa e rimasta senza processo si ferma anche lei
          if (congedoSullaCopia(c, r?.copia)) await azioneSessione({ ...c, id: r.copia.id, sessionId: r.copia.sessionId }, "stop").catch(() => null);
          scrivi({ fase: "ferma", dal: Date.now() });
        } else if (p.fai === "fine" && congedoSullaCopia(c, r?.copia)) {
          // la ripresa è nata come copia con un id nuovo: il congedo segue lei, che fa /fine e poi si ferma
          const nuovo = congedoSullaCopia(c, r.copia, Date.now());
          const { [kc]: _, ...resto } = this.congedi();
          setShared("arturo.volta.congedi", { ...resto, [nuovo.chiave]: nuovo.voce });
          registra("congedo copia", { macchina: c.host, sid: c.id, copia: nuovo.voce.id, esito: "ok" });
        } else scrivi({ fase: p.fase ?? c.fase, dal: Date.now(), ...(p.salvata ? { salvata: true } : {}) });
        this.aggiorna(cx);
        cx.notify();
      });
    }
  }

  // La ripresa da sola (#5882, Federico 17/11/2026): dopo ogni giro, una sessione col turno chiuso dal limite
  // d'uso o dalla connessione persa riparte quando è ora (daRiprendere di sessioni.js). Una alla volta; la
  // stessa sessione non si riprova per RIPROVA_MS (la rete ancora giù, un'altra finestra), e il conto dei
  // tentativi lo tiene la macchina della sessione. Ogni esito va nel registro, la ripresa riuscita anche
  // in un avviso.
  riprendiFerme(cx) {
    if (this.riprendoDaSola || !this.dati) return;
    const adesso = Date.now();
    this.provate = Object.fromEntries(Object.entries(this.provate ?? {}).filter(([, t]) => adesso - t < RIPROVA_MS));
    const s = daRiprendere(this.dati, adesso, { congedi: this.congedi() }).find((x) => !(chiave(x) in this.provate));
    if (!s) return;
    const mio = (this.riprendoDaSola = adesso);
    this.provate[chiave(s)] = adesso;
    cx.spawn(async (cx) => {
      try {
        if ((await config()).ripresa === "spenta") return;
        let r;
        try { r = await riprendiDaSola(s, testoRipresa(s)); } catch (e) { r = { errore: String(e?.message ?? e).slice(0, 160) }; }
        if (r.salta) return;
        registra("ripresa", { macchina: s.host ?? "qui", sid: s.id, tipo: s.errore?.tipo, tentativo: r.tentativo, canale: r.canale,
          esito: r.ok ? "ok" : r.rete === false ? "rete" : r.rifiutata ? "rifiutata" : "errore", errore: r.errore });
        if (!r.ok) return;
        notify({ title: `${titolo(s)} è ripartita da sola`, body: s.errore?.tipo === "limite" ? "Il limite d'uso si è sbloccato." : "La connessione è tornata.", level: "info", timeout: 6000 });
        this.aggiorna(cx);
      } finally { lascia(this, "riprendoDaSola", mio); }
    });
  }

  // La chiusura automatica (#5366, nota di Federico dell'11/11): una sessione di questa macchina che
  // aspetta un comando da più di un'ora va in congedo da sola, una alla volta, al più 3 all'ora e 12 al
  // giorno (arturo.json: congedo, congedo_dopo_min, congedo_ora, congedo_giorno). In modo "prova" scrive
  // soltanto chi chiuderebbe. Il registro sta in congedo-auto.json di cacheVolta(): lo scrive solo chi lo
  // ha letto per ultimo (writeTextFile con il testo di prima), così due finestre aperte sulla stessa
  // macchina non chiudono la stessa sessione e non sforano i tetti.
  async congedaFerme(cx) {
    if (this.autoLavora || !this.dati) return;
    const mio = (this.autoLavora = Date.now());
    try {
      const cfg = (await config()).congedo;
      if (cfg.modo === "spento") return;
      const file = `${this.cartella}/congedo-auto.json`;
      const testo = await readTextFile(file).catch(() => null);
      let reg = {};
      try { reg = JSON.parse(testo ?? "{}") ?? {}; } catch { reg = {}; }
      const adesso = Date.now();
      const conScheda = new Set(Object.values(this.schede ?? {}).filter((x) => x?.id).map(chiave));
      const scelte = daCongedare(this.dati, adesso, { dopoMin: cfg.dopoMin, congedi: this.congedi(), conScheda });
      const fatti = (reg.fatti ?? []).filter((x) => adesso - Number(x) < 86400000);
      if (cfg.modo === "prova") {
        // si scrive solo quando entra una sessione nuova: ogni scrittura fa rileggere la cartella
        const viste = new Set((reg.prova ?? []).map((v) => v.sessionId));
        if (!scelte.some((s) => !viste.has(s.sessionId))) return;
        const prova = registroProva(reg.prova, scelte, adesso);
        await writeTextFile(file, JSON.stringify({ ...reg, modo: "prova", prova }, null, 1), testo);
        return;
      }
      if (!scelte.length || restanti(fatti, adesso, cfg) < 1) return;
      const s = scelte[0];
      await writeTextFile(file, JSON.stringify({ ...reg, modo: "acceso", fatti: [...fatti, adesso],
        chiuse: [...(reg.chiuse ?? []).slice(-39), { sessionId: s.sessionId, titolo: titolo(s), quando: adesso, interazione: s.interazione || s.ultimo || "" }] }, null, 1), testo);
      notify({ title: `${titolo(s)}: la chiudo`, body: `Aspettava un comando ${daQuanto(s.interazione || s.ultimo, adesso)}: ${diProva(s) ? "è una prova, la elimino." : "faccio /fine e la fermo."}`, level: "info" });
      this.congeda({ sessionId: s.sessionId, id: s.id, host: s.host ?? "qui", auto: true }, cx);
    } catch { /* un registro scritto da un'altra finestra nel frattempo: si riprova al giro dopo */ }
    finally { lascia(this, "autoLavora", mio); }
  }

  // Lo stacco delle schede ferme (F3.2 di #5587, daStaccare di sessioni.js): ogni minuto, le schede che
  // agganciano una sessione ferma da 45 minuti lasciano andare claude attach, così il servizio di Claude
  // la ritira dopo un'ora. La scheda resta con la shell. Le schede staccate da Volta stanno in shared
  // arturo.volta.staccate ({ indirizzo: { id, host, da } }, così restano anche se il mod si ricarica):
  // quando una torna in primo piano, riaggancia() rilancia l'aggancio. Una scheda che non si stacca non
  // si riprova finché il mod non si ricarica, e lo dice il registro.
  async staccaFerme(cx) {
    if (this.staccoLavora || !this.dati || !this.schede) return;
    const mio = (this.staccoLavora = Date.now());
    try {
      const prima = shared("arturo.volta.staccate") ?? {};
      // via le schede chiuse e quelle riagganciate da un'altra strada (il clic sulla riga)
      const tieni = {};
      for (const [a, v] of Object.entries(prima)) if (a in this.schede && (await nuda(a))) tieni[a] = v;
      const visti = new Set(panes().map((p) => p.terminal));
      const no = new Set([...this.noStacco, ...Object.keys(tieni)]);
      const l = daStaccare(this.schede, this.dati.sessioni, Date.now(), { davanti: focused()?.terminal ?? null, visti, no });
      for (const { indirizzo, s } of l) {
        const r = await staccaAggancio(indirizzo, s).catch((e) => ({ errore: String(e?.message ?? e).slice(0, 120) }));
        // una scheda che ha già la shell (aggancio caduto da solo) non si segna: il clic sulla riga la riapre
        if (r.gia) continue;
        registra("stacco", { macchina: s.host, sid: s.id, terminale: indirizzo, esito: r.errore ? "errore" : "ok", errore: r.errore });
        if (r.errore) this.noStacco.add(indirizzo);
        else if (r.ok) tieni[indirizzo] = { id: s.id, host: s.host, da: Date.now() };
      }
      if (JSON.stringify(tieni) !== JSON.stringify(prima)) setShared("arturo.volta.staccate", tieni);
    } finally { lascia(this, "staccoLavora", mio); }
  }

  // Lo spazio della scheda segue il progetto della sessione (daAllineare di sessioni.js, 14/11/2026): ogni
  // minuto, una scheda in "Senza progetto" o nello spazio di un altro progetto passa a quello del progetto
  // che l'elenco le dà da due letture. Lo spostamento è quello di "Cambia progetto" (spostaScheda): chiude
  // l'aggancio senza congedo e lo riapre nello spazio giusto. Uno spostamento fatto non si ripete finché il
  // mod non si ricarica, anche se non riesce: lo dice il registro.
  async allineaSpazi(cx) {
    if (this.allineaLavora || !this.dati || !this.schede) return;
    const mio = (this.allineaLavora = Date.now());
    try {
      const sp = spaces();
      const voci = [];
      for (const [indirizzo, c] of Object.entries(this.schede)) {
        const s = c && this.dati.sessioni.find((x) => x.id === c.id && x.host === c.host);
        const p = panes().find((x) => x.terminal === indirizzo);
        // anche lo spazio di un'altra macchina: lì stanno le schede delle sue sessioni (#5802)
        const dove = p ? sp.find((x) => (!x.machine || x.machine === s?.host) && x.tabs.some((tb) => tb.id === p.tab)) : null;
        if (s) voci.push({ indirizzo, s, spazio: dove ? { nome: dove.name, libero: libero(dove.name) } : null });
      }
      const r = daAllineare(voci, { prima: this.visteProgetti, letto: this.giroBuono ?? this.dati.letto, davanti: focused()?.terminal ?? null, fatti: this.allineati });
      this.visteProgetti = r.visti;
      for (const { indirizzo, s, progetto } of r.sposta) {
        this.allineati.add(`${chiave(s)}|${progettoDi(progetto).chiave}`);
        const esito = await spostaScheda(s, progetto).catch((e) => ({ errore: String(e?.message ?? e).slice(0, 120) }));
        registra("allinea", { macchina: s.host, sid: s.id, terminale: indirizzo, progetto, esito: esito.errore ? "errore" : esito.spostata ? "ok" : "niente", errore: esito.errore });
      }
      if (r.sposta.length) cx.notify();
    } finally { lascia(this, "allineaLavora", mio); }
  }

  // Una scheda staccata da staccaFerme torna in primo piano (un clic sulla scheda, ⌘⇧↓, ⌘↓ e ⌘↑): l'aggancio
  // riparte da solo, con la strada del clic sulla riga (apri), che accende il servizio e risveglia una
  // sessione già ritirata.
  riaggancia(indirizzo, cx) {
    const st = shared("arturo.volta.staccate") ?? {};
    const v = indirizzo ? st[indirizzo] : null;
    if (!v) return;
    const resto = { ...st };
    delete resto[indirizzo];
    setShared("arturo.volta.staccate", resto);
    const s = (this.dati?.sessioni ?? []).find((x) => x.id === v.id && x.host === v.host);
    if (!s || chiusa(s) || !Array.isArray(s.attach) || !s.attach.length) return;
    if (this.sposto[chiave(s)] || this.apro[chiave(s)] || this.veglio[chiave(s)] || this.faccio[chiave(s)] === "sposta") return;
    registra("riaggancio", { macchina: s.host, sid: s.id, terminale: indirizzo });
    this.apri(s, s.attach, false, cx);
  }

  // Il ponte del microfono: acceso finché la scheda in primo piano aggancia una sessione di un'altra
  // macchina, spento un minuto dopo. Lo stato va in shared arturo.microfono, per la riga dell'elenco.
  async microfono(cx) {
    if (!this.micScript || this.micLavora) return;
    const spento = shared("arturo.microfono.spento") === true;
    const f = focused();
    const t = f?.terminal ? terminals().find((x) => x.address === f.terminal) : null;
    const { st, azione } = passo(this.mic, spento ? null : bersaglio(t, this.dati?.sessioni), Date.now(), spento);
    this.mic = st;
    if (!azione) return this.dicoMicrofono(spento, cx);
    const mio = (this.micLavora = Date.now());
    let risposta = null;
    try {
      const r = await exec(this.py, [this.micScript, ...entroDi("microfono"), azione.verbo, ...(azione.target ? [azione.target] : [])], { timeout: tettoDi("microfono") });
      // l'ultima riga JSON, come dati.js (#5578): prima un avviso dopo il JSON dava "non riesco a lanciare il ponte"
      const d = esito(r);
      risposta = d.errore && !d.stato ? { stato: "errore", motivo: d.errore } : d;
    } catch { risposta = { stato: "errore", motivo: "non riesco a lanciare il ponte" }; }
    lascia(this, "micLavora", mio);
    if (this.mic && azione.verbo === "accendi") this.mic = { ...this.mic, stato: risposta.stato ?? "avvio", motivo: risposta.motivo ?? null };
    this.dicoMicrofono(spento, cx);
  }

  dicoMicrofono(spento, cx) {
    const qui = (this.dati?.macchine ?? []).find((x) => x.questa)?.macchina ?? null;
    const m = spento ? { spento: true } : this.mic ? { stato: this.mic.stato, macchina: this.mic.macchina, motivo: this.mic.motivo ?? null, qui } : null;
    if (JSON.stringify(m) !== JSON.stringify(shared("arturo.microfono") ?? null)) { setShared("arturo.microfono", m); cx.notify(); }
  }

  // "arturo.volta-riprendi-<chiave>-<macchina>": Riprendi su… di una sessione di una macchina che non
  // risponde (sposta.js in modo "riprendi"). Nasce su `macchina` una sessione nuova col prompt
  // dell'ultima lettura; quella di partenza non si tocca, e la riga dice dove è ripresa.
  riprendiId(macchina, id, cx) {
    const s = this.trovaId(id);
    if (!s) return;
    const k = chiave(s);
    if (this.apro[k]) return;
    const mio = (this.apro[k] = Date.now());
    cx.notify();
    cx.spawn(async (cx) => {
      let r;
      try {
        const c = await config();
        const prompt = promptRipresa(s, testoHandoff(s, this.dati?.giuDa?.[s.host]), conArturo(c));
        r = await riprendiSu(macchina, prompt, s.progetto ?? null, `Ripresa: ${titolo(s)}`);
      } catch (e) { r = { errore: String(e?.message ?? e).slice(0, 160) }; }
      lascia(this, "apro", mio, k);
      registra("riprendi", { macchina, sid: s.id, esito: r?.errore ? "errore" : "ok", errore: r?.errore });
      if (r?.errore) this.avvisa(s, `Non riprende: ${r.errore}`, cx);
      else this.avvisa(s, `Ripresa su ${nomeMacchina(macchina)}: la conversazione di qui resta com'è.`, cx, 600000);
      this.aggiorna(cx);
      cx.notify();
    });
  }

  // Gli handoff delle sessioni di una macchina giù da DIMENTICA_MS (testoHandoff di sessioni.js), uno per
  // sessione e per caduta, in ~/.cache/volta-handoff/<macchina>/<id>.md: fuori da cacheVolta(), che a ogni
  // file nuovo fa rileggere l'elenco. Un handoff della stessa caduta (riga "Giù da") non si riscrive.
  async salvaHandoff() {
    if (this.handoffLavora || !this.dati?.giuDa) return;
    const mio = (this.handoffLavora = Date.now());
    try {
      const ora = Date.now();
      for (const [host, da] of Object.entries(this.dati.giuDa)) {
        if (!dimenticata(this.dati.giuDa, host, ora)) continue;
        const l = (this.dati.sessioni ?? []).filter((s) => s.host === host && s.tipo === "background" && !chiusa(s) && s.id);
        if (!l.length) continue;
        const cartella = `${cartellaHandoff()}/${nomeFile(l[0].macchina ?? host)}`;
        await creaCartella(cartella, this.py);
        for (const s of l) {
          const file = `${cartella}/${nomeFile(s.id)}.md`;
          const prima = await readTextFile(file).catch(() => null);
          const testo = testoHandoff(s, da);
          if (prima && prima.includes(testo.split("\n").find((r) => r.startsWith("- Giù da:")))) continue;
          try { await writeTextFile(file, testo, prima ?? null); registra("handoff", { macchina: host, sid: s.id, esito: "ok" }); }
          catch (e) { registra("handoff", { macchina: host, sid: s.id, esito: "errore", errore: String(e?.message ?? e).slice(0, 120) }); }
        }
      }
    } finally { lascia(this, "handoffLavora", mio); }
  }

  async leggi(cx) {
    const prima = this.dati;
    try {
      const testo = await readTextFile(this.file);
      if (testo) this.dati = JSON.parse(testo);
    } catch { /* un file a metà: resta l'ultima lettura buona */ }
    // le macchine che non rispondono, con l'ora della caduta (giuDa di sessioni.js): gruppi() piega le
    // loro sessioni dopo DIMENTICA_MS, e salvaHandoff ne scrive l'handoff
    if (this.dati && this.dati !== prima) {
      if (this.giu === undefined) this.giu = await leggiGiu();
      const giu = giuDa(this.giu, this.dati.macchine, Date.now());
      if (JSON.stringify(giu) !== JSON.stringify(this.giu)) { this.giu = giu; scriviGiu(giu, this.py); }
      this.dati.giuDa = giu;
      this.salvaHandoff();
    }
    if (this.dati !== prima) {
      this.entra(entrate(prima, this.dati), cx);
      for (const s of nuoveInAttesa(prima, this.dati))
        notify({ title: `${titolo(s)} ti aspetta`, body: `Su ${s.macchina}: aprila da Tutte le sessioni.`, level: "info" });
      const st = statiCorti(this.dati);
      if (JSON.stringify(st) !== JSON.stringify(shared("arturo.volta.stati") ?? {})) setShared("arturo.volta.stati", st);
      this.aggiornaCoda();
    }
    this.portaNomi();
    this.portaInizi();
    // Le macchine per la riga "Nasce su" (dati.js altreMacchine), scritte solo quando cambiano.
    const m = (this.dati?.macchine ?? []).map((x) => ({ host: x.host, macchina: x.macchina, questa: Boolean(x.questa), giu: Boolean(x.irraggiungibile) }));
    if (JSON.stringify(m) !== JSON.stringify(shared("arturo.volta.macchine") ?? [])) setShared("arturo.volta.macchine", m);
  }

  // leggi con l'errore tenuto da parte: un'eccezione dopo il parse (entra, portaNomi, ...) usciva dal giro
  // della sonda, dal primo caricamento e dall'attesa sulla cartella, e li fermava per sempre (#5550).
  // L'errore resta in erroreLettura finché una lettura riesce.
  async leggiSenzaFermarsi(cx) {
    try {
      await this.leggi(cx);
      this.erroreLettura = null;
    } catch (e) {
      this.erroreLettura = String(e?.message ?? e).slice(0, 200);
      registra("lettura elenco", { esito: "eccezione", errore: this.erroreLettura });
    }
  }

  // I nomi scritti dalla persona che Claude Code non ha ancora (campo daPortare): a ogni lettura si
  // prova a portarli con /rename, una sessione alla volta. Riesce quando la sessione è ferma e ha una
  // scheda in questa finestra; altrimenti si riprova alla lettura dopo.
  portaNomi() {
    for (const s of this.dati?.sessioni ?? []) {
      const k = chiave(s);
      if (!daPortare(s) || this.porto[k]) continue;
      const mio = (this.porto[k] = Date.now());
      portaNome(s).catch(() => false).then(() => lascia(this, "porto", mio, k));
    }
  }

  // Le sessioni spostate in un altro progetto (campo daIniziare) ripartono da /inizio appena sono
  // ferme (#5465). Ogni finestra lo scrive in una sua scheda; la ripresa senza scheda la fa solo la
  // finestra che ha fatto lo spostamento (spostate). Una alla volta per sessione; chiuse e in congedo no.
  portaInizi() {
    for (const s of this.vis()?.sessioni ?? []) {
      const k = chiave(s);
      if (!daIniziare(s) || this.inizio[k]) continue;
      const mio = (this.inizio[k] = Date.now());
      portaInizio(s, this.spostate[k] === s.daIniziare).catch(() => ({ fatto: false })).then((r) => {
        lascia(this, "inizio", mio, k);
        if (!r.fatto) return;
        delete this.spostate[k];
        if (r.come === "terminale")
          notify({ title: `${titolo(s)} è in ${nomeProgetto(s.daIniziare)}`, body: `Gira in un Terminale: scrivi lì /inizio ${s.daIniziare}.`, level: "info" });
      });
    }
  }

  // Le attese appese del mod (#6109, liberaAppese di sessioni.js): a ogni giro si spengono quelle accese da
  // due tetti, e il registro scrive "attesa appesa". Uno Sposta appeso libera anche la sua sessione
  // (faccio), che altrimenti non si apriva più, e la toglie dalla coda: dopo due volte SPOSTA_MAX_MS lo
  // spostamento staccato è finito da sé, e la coda non deve farne partire un secondo.
  sciogliAppese() {
    const via = liberaAppese(this, TETTI_ATTESE());
    for (const a of via) registra("attesa appesa", a);
    if (!via.some((a) => a.attesa === "spostando")) return;
    for (const [k, v] of Object.entries(this.faccio ?? {})) if (v === "sposta") { delete this.faccio[k]; delete this.codaSposta?.[k]; }
    this.pubblicaSposto();
  }

  // Un giro di volta_sonda.py volta, mai due insieme: con una macchina lenta un giro dura qualche secondo.
  aggiorna(cx, gesto = true) {
    this.sciogliAppese();
    if (!this.script) return;
    // Un giro appeso si lascia andare dopo due tetti (19/11/2026): il 18/11 alle 23:00 un giro non è più
    // tornato, nonostante il timeout di exec, e la barra è rimasta ferma sull'elenco della sera fino al
    // mattino dopo. Il giro vecchio, se torna, non tocca più inCorso (giroN).
    if (this.inCorso && Date.now() - (this.inCorsoDa ?? 0) > 2 * tettoDi("volta")) {
      registra("giro appeso", { ms: Date.now() - (this.inCorsoDa ?? 0) });
      this.inCorso = false;
    }
    // un gesto durante un giro (apri, Riavvia, Sposta): il giro dopo parte appena questo finisce, non fra 10 s
    if (this.inCorso) { if (gesto) this.ancora = true; return; }
    this.inCorso = true;
    this.inCorsoDa = Date.now();
    const giro = (this.giroN = (this.giroN ?? 0) + 1);
    this.ancora = false;
    cx.spawn(async (cx) => {
      // inCorso torna falso in ogni caso: un errore nella lettura dell'elenco fermava il giro per sempre (#5550)
      const t0 = Date.now();
      try {
        try {
          // un giro chiesto da un gesto vuole le altre macchine lette adesso; quello del timer accetta la loro
          // lettura di pochi secondi fa (step 6, #5583): con tre Volta aperte ogni macchina si legge una volta
          const r = await exec(this.py, [this.script, ...entroDi("volta"), "volta", ...(gesto ? ["--fresca"] : []), "--scrivi", this.file], { timeout: tettoDi("volta") });
          this.errore = r.code === 0 ? null : (r.stderr || r.stdout || "").trim().split("\n").pop();
          // l'ora dell'ultimo giro riuscito: la sonda riscrive sessioni.json solo se cambia qualcosa (step 5),
          // quindi `letto` del file può essere più vecchio del giro
          if (r.code === 0) this.giroBuono = oraQui();
        } catch (e) {
          this.errore = String(e?.message ?? e);
        }
        await this.leggiSenzaFermarsi(cx);
      } finally {
        if (this.giroN === giro) this.inCorso = false;
      }
      // il giro visto dalla finestra (#5549): la sonda registra il suo, qui anche l'attesa di exec
      registra("giro", { ms: Date.now() - t0, esito: this.errore ? "errore" : "ok", errore: this.errore });
      if (Date.now() - (this.registroUltimo ?? 0) >= REGISTRO_MS) { this.registroUltimo = Date.now(); svuotaRegistro(this.py); }
      this.passiCongedo(cx);
      this.giraCoda(cx);
      this.riprendiFerme(cx);
      cx.notify();
      this.sincronizzaNote(cx);
      this.giraDavanti(cx);
      if (this.ancora) this.aggiorna(cx);
    });
  }

  // Le note della finestra (⌘⇧N) dopo ogni giro dell'elenco: volta_note.py porta qui quelle delle altre
  // macchine e di là quelle di qui (12/11/2026). Mai due giri insieme. Lo stato va fuori da cacheVolta(),
  // che questa finestra guarda: scriverci farebbe rileggere l'elenco a ogni giro. testata.js vede le note
  // nuove da solo, perché guarda la cartella delle note.
  sincronizzaNote(cx) {
    if (!this.noteScript || this.noteInCorso || Date.now() - (this.noteUltimo ?? 0) < NOTE_MS) return;
    const mio = (this.noteInCorso = Date.now());
    this.noteUltimo = mio;
    cx.spawn(async () => {
      try {
        await exec(this.py, [this.noteScript, ...entroDi("note"), "sincronizza", "--scrivi", `${cacheVolta("volta-note")}/stato.json`], { timeout: tettoDi("note") });
      } catch { /* il giro dopo riprova; l'esito sta in stato.json */ }
      lascia(this, "noteInCorso", mio);
    });
  }

  // La macchina davanti (17/11/2026, #5881): volta_davanti.py chiede a ogni macchina da quanto nessuno tocca
  // tastiera o mouse e scrive su tutte il file con l'ultimo tocco. Il giro dell'elenco dura 8 s: questo al più
  // ogni DAVANTI_MS, mai due insieme. Il tocco vale 15 minuti, quindi un minuto di ritardo non sposta niente.
  giraDavanti(cx) {
    if (!this.davantiScript || this.davantiInCorso || Date.now() - this.davantiUltimo < DAVANTI_MS) return;
    const mio = (this.davantiInCorso = Date.now());
    this.davantiUltimo = mio;
    cx.spawn(async () => {
      try {
        await exec(this.py, [this.davantiScript, ...entroDi("davanti"), "giro", "--scrivi", `${cacheVolta("volta-davanti")}/stato.json`], { timeout: tettoDi("davanti") });
      } catch { /* il giro dopo riprova; l'esito sta in stato.json */ }
      lascia(this, "davantiInCorso", mio);
    });
  }

  modo() {
    // Senza una scelta della persona vale "per progetto": chi apre Volta cerca il lavoro, non la macchina.
    return shared("arturo.volta.gruppi") === "macchina" ? "macchina" : "progetto";
  }

  avvisa(s, testo, cx, ms = 7000) {
    const k = chiave(s);
    this.avvisi[k] = testo;
    cx.notify();
    cx.timer.after(ms, (cx) => { if (this.avvisi[k] === testo) { delete this.avvisi[k]; cx.notify(); } });
  }

  // Una sessione che non si apre: il motivo resta sulla riga due minuti (o fino al clic dopo) e arriva
  // anche come avviso, perché chi ha cliccato sta guardando la scheda e non l'elenco.
  nonApre(s, testo, cx) {
    this.avvisa(s, testo, cx, 120000);
    notify({ title: `${titolo(s)} non si apre`, body: testo, level: "warning" });
  }

  // Il clic su una sessione: aggancia, sposta e poi aggancia, oppure dice perché no.
  premi(s, cx) {
    // un secondo clic mentre il primo lavora non lancia un secondo aggancio nella stessa scheda
    if (this.sposto[chiave(s)] || this.apro[chiave(s)]) return;
    // Durante la veglia la scheda c'è già: il clic la porta davanti (prima si perdeva in silenzio per 6 s)
    if (this.veglio[chiave(s)]) { if (typeof this.veglio[chiave(s)] === "string") mostra(this.veglio[chiave(s)]); return; }
    // Durante uno Sposta l'aggancio riaccenderebbe la copia di partenza dopo claude stop: la stessa
    // conversazione resterebbe viva su due macchine (#5635). La scheda d'arrivo la apre la fine di Sposta.
    if (this.faccio[chiave(s)] === "sposta") return this.avvisa(s, `La sposto su ${nomeMacchina(this.spostoSu?.[chiave(s)] ?? "qui")}…`, cx);
    const secondo = this.avvisi[chiave(s)] === ALTROVE;
    delete this.avvisi[chiave(s)];
    let d = clic(s);
    // la scheda che la ospita non è in questa finestra: vale la regola di un'interattiva in un Terminale
    if (d.azione === "mostra") { if (mostra(d.terminale)) return; d = clic({ ...s, terminale: null }); }
    if (d.azione === "no") return this.avvisa(s, d.motivo, cx);
    if (d.azione === "aggancia" && this.fuori(s, secondo, cx)) return;
    if (d.azione === "aggancia") return this.apri(s, d.argv, false, cx);
    // senza teletrasporto.py nessuno sa scrivere /bg nel Terminale di quella sessione
    if (!this.sposta) return this.avvisa(s, "È aperta in un Terminale: aprila da lì.", cx);
    const mioSposto = (this.sposto[chiave(s)] = Date.now());
    cx.notify();
    cx.spawn(async (cx) => {
      let portata = null;
      try {
        portata = esito(await exec(this.py, [this.sposta, ...entroDi("porta"), "porta-volta", s.host, s.sessionId], { timeout: tettoDi("porta") }));
      } catch (e) {
        portata = { errore: `${s.macchina} non risponde` };
      }
      lascia(this, "sposto", mioSposto, chiave(s));
      if (portata?.attach?.length) {
        this.apri({ ...s, id: portata.id ?? s.id }, portata.attach, true, cx);
        this.aggiorna(cx);
      } else this.avvisa(s, `Non la sposto: ${String(portata?.errore ?? "risposta vuota").replace(/\.+$/, "")}.`, cx);
      cx.notify();
    });
  }

  // La sessione è già agganciata in un Terminale fuori dalla finestra (dati.js altrove): il primo clic lo
  // dice sulla riga, il secondo (finché l'avviso è lì) stacca quel terminale e lascia aprire la scheda.
  // La sessione continua: si chiude solo l'aggancio. Torna true se il clic si ferma all'avviso.
  fuori(s, secondo, cx) {
    if (!altrove(s).length) return false;
    if (secondo) { stacca(s); return false; }
    this.avvisa(s, ALTROVE, cx, ALTROVE_MS);
    return true;
  }

  // Apre la sessione in una scheda con Claude dentro (dati.js apriSessione): prima il servizio di Claude,
  // il riavvio se era in errore, poi la scheda. Se Claude esce subito dalla scheda, lo dice la riga.
  apri(s, argv, pronta, cx) {
    const k = chiave(s);
    this.riapri(s);
    const mio = (this.apro[k] = Date.now());
    cx.notify();
    cx.spawn(async (cx) => {
      let r;
      const t0 = Date.now();
      try { r = await apriSessione(s, argv, pronta); } catch (e) { r = { errore: `Non la apro: ${String(e?.message ?? e).slice(0, 120)}.` }; }
      // l'evento apri (step 5): `ms` dal clic alla scheda davanti, `visibile` dal clic a Claude nella scheda
      // (letto dalla veglia; subito se la scheda c'era già), `servizio` se prepara è servito
      const apri = { macchina: s.host, sid: s.id, ms: Date.now() - t0, come: r.come, servizio: r.servizio, esito: r.errore ? "errore" : "ok", errore: r.errore };
      if (!r.veglia) registra("apri", { ...apri, visibile: r.come === "davanti" ? apri.ms : null });
      lascia(this, "apro", mio, k);
      if (r.errore) this.nonApre(s, r.errore, cx);
      // un'apertura cambia lo stato della sessione (dorme, ferma): l'elenco si rilegge subito
      if (!r.errore) this.aggiorna(cx);
      if (r.veglia) this.veglio[k] = r.indirizzo || true;
      cx.notify();
      let v = null;
      try { v = r.veglia ? await r.veglia : null; } catch { /* senza veglia la scheda resta com'è */ }
      if (r.veglia) registra("apri", { ...apri, visibile: v?.visto ? v.visto - t0 : null });
      if (v?.errore) registra("scheda vuota", { macchina: s.host, sid: s.id, ms: Date.now() - t0, esito: "errore", errore: v.errore });
      delete this.veglio[k];
      if (v?.errore) this.nonApre(s, v.errore, cx);
      cx.notify();
    });
  }

  // Dal comando `do` può arrivare l'id di una sessione appena nata, che il giro in corso non ha
  // ancora scritto nell'elenco: si dice, invece di non fare niente (#5078). Prima le righe visibili: dopo
  // Sposta la copia chiusa di partenza ha lo stesso id, e il clic (o ⌘K) la riaprirebbe lì (#5537). Vale
  // anche la chiave macchina:id (#5634), che dice da sola quale copia.
  trovaId(id) {
    // Un id nudo vale prima come id del lavoro, poi come inizio del sessionId: la prima conversazione di un
    // lavoro che rinasce come lavoro suo ha il sessionId che comincia con l'id del lavoro (#5907).
    const nudo = !String(id).includes(":");
    const esatti = (l) => (l ?? []).filter((x) => (nudo ? x.id === id : chiave(x) === id));
    const prefisso = (l) => (nudo ? (l ?? []).filter((x) => String(x.sessionId).startsWith(id)) : []);
    // Prima la riga visibile: la copia chiusa di partenza ha lo stesso id (#5537).
    const liste = [this.vis()?.sessioni, this.dati?.sessioni];
    const l = liste.map(esatti).find((x) => x.length) ?? liste.map(prefisso).find((x) => x.length) ?? [];
    const copie = [...new Set(l.map(chiave))];
    if (!l.length) notify({ title: `Non trovo la sessione ${id}`, body: "L'elenco si aggiorna fra pochi secondi: riprova.", level: "warning" });
    // Il solo id che sta su due macchine non dice quale copia (#5643): i comandi di Volta portano la chiave
    // macchina:id, e un id nudo da herdr-app do non sceglie a caso la prima.
    else if (copie.length > 1) notify({ title: `La sessione ${id} sta su due macchine`, body: `Scrivi anche la macchina: ${copie.join(" o ")}.`, level: "warning" });
    return copie.length === 1 ? l[0] : undefined;
  }

  // ⌘↓ e ⌘↑ ("arturo.volta-giro-avanti" e "-indietro"): la sessione dopo o prima nel giro (ordineGiro), di
  // ogni macchina: quelle con una scheda e quelle in background senza scheda che lavorano o ti aspettano,
  // aperte col gesto del clic. In coda le schede spente (schedeSpente), portate davanti con mostra. Parte
  // dalla scheda in primo piano; dentro una raffica di tasti parte dall'ultima chiesta, perché un aggancio
  // ci mette qualche secondo ad aprirsi.
  giro(verso, cx) {
    impostaProgetti(shared("arturo.progetti"));
    const sessioni = this.dati?.sessioni ?? [];
    // Nel giro solo le sessioni con una scheda in un pannello di questa finestra (ordineGiro): l'aggancio
    // (schedeDi) o il terminale dove gira l'interattiva, qui o su un'altra macchina ("amaltea/t2s"). Un
    // terminale senza pannello (hc run) non è una scheda: il tasto lì non mostrava niente (14/11/2026).
    const pannelli = [...new Set(panes().map((p) => p.terminal))];
    const visti = new Set(pannelli);
    const conScheda = new Set(sessioni.filter((s) => (s.terminale && s.tipo !== "background" && visti.has(s.questa ? s.terminale : `${s.host}/${s.terminale}`))
      || schedeDi(s).length).map(chiave));
    const spente = schedeSpente(pannelli.map((a) => terminals().find((x) => x.address === a) ?? { address: a }), sessioni,
      uscenti(this.congedi(), this.escono, this.forse));
    const st = statoGiro(this.giroSt, ordineGiro(gruppi(this.visGiro(), this.modo()), this.aperti, conScheda).concat(spente), Date.now());
    const f = focused();
    const scheda = f?.terminal ? terminals().find((x) => x.address === f.terminal) : null;
    const qui = sessioneDi(scheda, sessioni);
    const daQui = f?.terminal && st.ids.includes(SCHEDA + f.terminal) ? SCHEDA + f.terminal : qui ? chiave(qui) : null;
    const id = passoGiro(st.ids, st.ultimo ?? daQui, verso);
    this.giroSt = { ...st, ultimo: id };
    // la riga accesa (corrente) segue il tasto subito, e a raffica finita torna alla scheda in primo piano
    cx.notify();
    cx.timer.after(GIRO_MS + 50, (cx) => cx.notify());
    // la scheda di una sessione chiusa o di una macchina giù: davanti e basta, niente da riagganciare
    if (id?.startsWith(SCHEDA)) { mostra(id.slice(SCHEDA.length)); return; }
    const s = id ? sessioni.find((x) => chiave(x) === id) : null;
    if (s) { this.scopri(s); this.premi(s, cx); }
    else notify({ title: "Nessuna sessione da aprire", body: "L'elenco non ha sessioni che un tasto può mostrare.", level: "info", timeout: 3000 });
  }

  // La sessione della scheda in primo piano, per "Sposta su" della testata (testata.js e sposta.js, che
  // sono altre copie del mod): shared arturo.volta.davanti, null se la scheda non mostra una sessione.
  davanti(indirizzo) {
    const t = indirizzo ? terminals().find((x) => x.address === indirizzo) ?? { address: indirizzo } : null;
    const s = sessioneDavanti(t, this.dati?.sessioni ?? []);
    const v = s ? { id: s.id, sessionId: s.sessionId, host: s.host ?? "qui", macchina: s.macchina, tipo: s.tipo,
      stato: s.stato, titolo: titolo(s), progetto: s.progetto ?? null, sintesi: s.sintesi ?? null, fase: fase(s),
      sposto: this.faccio?.[chiave(s)] === "sposta" || Boolean(this.codaSposta?.[chiave(s)]),
      // la checklist della ripartenza ancora da mandare (17/11/2026): quante voci, per la testata, e
      // l'elenco intero per il blocco sovrapposto (checklist.js, parte ripartenza)
      checklist: s.ripartenza && !checklistMandata(s, shared("arturo.checklist.mandate")) ? vociRipartenza(s.ripartenza).length : 0,
      chiave: chiave(s), ripartenza: s.ripartenza && !checklistMandata(s, shared("arturo.checklist.mandate")) ? s.ripartenza : null } : null;
    if (JSON.stringify(v) !== JSON.stringify(shared("arturo.volta.davanti") ?? null)) setShared("arturo.volta.davanti", v);
  }

  // La sessione `id` come la vede l'elenco: dopo uno spostamento lo stesso id c'è su due macchine, e vale
  // la copia che l'elenco mostra. Una chiave macchina:id (i comandi di Volta dal 14/11, #5643) passa da trovaId, che
  // la cerca per chiave.
  vistaId(id) {
    return (this.vis()?.sessioni ?? []).find((x) => x.id === id) ?? this.trovaId(id);
  }

  // Quante sessioni aspettano di spostarsi o si stanno spostando (la pastiglia "Sposta tutto su…").
  inCoda() {
    return Object.keys(this.codaSposta ?? {}).length;
  }

  // "arturo.volta-sposta-<chiave>-<macchina>": "Sposta su" della testata o del menu (sposta.js) o herdr-app
  // do. La sessione entra nella coda: riparte sull'altra macchina con la stessa conversazione
  // (volta_sposta.py), a turno finito se sta lavorando. Intanto la riga dice dove va, e a fine lavoro un
  // avviso dice com'è andata. `zitto`: niente avvisi per la singola sessione (Sposta tutto ne dà uno).
  // true se la sessione è entrata in coda.
  spostaId(macchina, id, cx, zitto = false) {
    const s = this.vistaId(id);
    if (!s) return false;
    const no = nonSiSposta(s) ?? ((s.host ?? "qui") === macchina ? `È già su ${nomeMacchina(macchina)}.` : null);
    if (no) {
      if (!zitto) notify({ title: "Non la sposto", body: no, level: "warning" });
      tracciaSposta(s, "comando", { a: macchina, id, no }, true);
      return false;
    }
    const k = chiave(s);
    if (this.faccio[k] || this.codaSposta[k]) {
      tracciaSposta(s, "comando", { a: macchina, id, no: "già in corso o in coda", faccio: this.faccio[k] ?? null, coda: this.codaSposta[k] ?? null });
      return false;
    }
    tracciaSposta(s, "comando", { a: macchina, id, da: s.host ?? "qui", aFineTurno: aFineTurno(s) }, true);
    this.codaSposta[k] = { macchina, id: s.id, da: s.host ?? "qui", dopo: 0 };
    this.spostoSu = { ...(this.spostoSu ?? {}), [k]: macchina };
    if (!zitto && aFineTurno(s)) notify({ title: `La sposto su ${nomeMacchina(macchina)} a turno finito`, body: titolo(s), level: "info", timeout: 5000 });
    cx.notify();
    this.giraCoda(cx);
    return true;
  }

  // "arturo.volta-spostatutto-<macchina>": "Sposta tutto su…" della barra. Ogni sessione spostabile
  // delle altre macchine entra nella coda (spostabili di sposta.js); un avviso solo dice quante.
  spostaTutto(macchina, cx) {
    const l = spostabili(this.vis()?.sessioni ?? [], macchina);
    const prese = l.filter((s) => this.spostaId(macchina, chiave(s), cx, true));
    if (!prese.length) return notify({ title: "Niente da spostare", body: `Nessuna sessione in background da portare su ${nomeMacchina(macchina)}.`, level: "info", timeout: 4000 });
    const dopo = prese.filter(aFineTurno).length;
    notify({ title: `Sposto ${prese.length === 1 ? "1 sessione" : `${prese.length} sessioni`} su ${nomeMacchina(macchina)}`,
      body: `Una alla volta${dopo ? `; ${dopo} a turno finito` : ""}.`, level: "info", timeout: 6000 });
  }

  // La coda di Sposta: una sessione alla volta, perché due spostamenti nello stesso repository farebbero
  // git pull e worktree add insieme. Una che lavora aspetta il giro dell'elenco in cui il turno è finito:
  // lo spostamento ferma la sessione, e a metà turno il lavoro si interromperebbe. Se volta_sposta.py
  // trova che un turno è appena partito (`lavora`), la sessione resta in coda e si riprova dopo un giro.
  // Una sessione sparita dall'elenco, chiusa o già altrove esce dalla coda. La coda vive in questa
  // finestra: chiudere Volta la svuota, e le sessioni restano dove sono.
  giraCoda(cx) {
    this.pubblicaSposto();
    if (this.spostando) return;
    const vive = this.vis()?.sessioni ?? [];
    const ora = Date.now();
    for (const [k, v] of Object.entries(this.codaSposta)) {
      const s = vive.find((x) => chiave(x) === k);
      if (!s || nonSiSposta(s)) { delete this.codaSposta[k]; continue; }
      // un aggancio che si sta aprendo (clic in coda, veglia) non ha ancora la scheda che Sposta chiude:
      // partirebbe dopo claude stop e riaccenderebbe la copia di partenza (#5635). Si aspetta il giro dopo.
      if (aFineTurno(s) || v.dopo > ora || this.apro[k] || this.veglio[k] || this.sposto[k]) continue;
      const mio = (this.spostando = Date.now());
      this.faccio[k] = "sposta";
      this.pubblicaSposto();
      cx.notify();
      cx.spawn(async (cx) => {
        let r;
        try { r = await spostaSessione(s, v.macchina, (ms) => cx.sleep(ms)); } catch (e) {
          r = { errore: String(e?.message ?? e).slice(0, 160) };
          await tracciaSposta(s, "caduto", { errore: r.errore });
        }
        await tracciaSposta(s, "fine", { esito: r });
        this.finitoSposta(s, v, r, cx, mio);
      });
      return;
    }
    this.pubblicaSposto();
  }

  // Le sessioni che si spostano o aspettano in coda, in shared arturo.volta.sposto ({ chiave: macchina }):
  // tornataShell di dati.js gira anche nelle altre copie del mod, e non riapre la copia di partenza (#5635).
  pubblicaSposto() {
    const m = Object.fromEntries(Object.entries(this.codaSposta ?? {}).map(([k, v]) => [k, v.macchina]));
    for (const [k, v] of Object.entries(this.faccio ?? {})) if (v === "sposta") m[k] = this.spostoSu?.[k] ?? m[k] ?? "?";
    if (JSON.stringify(m) !== JSON.stringify(shared("arturo.volta.sposto") ?? {})) setShared("arturo.volta.sposto", m);
  }

  // Dopo uno spostamento (dalla coda o ripreso): libera la coda, dice com'è andata e passa al prossimo.
  // `v` = { macchina, id, da }. Una sessione che ha cominciato un turno (`lavora`) torna in coda.
  finitoSposta(s, v, r, cx, mio) {
    const k = chiave(s);
    // uno Sposta appeso e già lasciato andare (sciogliAppese) non tocca quello partito dopo
    if (this.spostando !== mio) return;
    delete this.faccio[k];
    this.spostando = false;
    if (r.lavora) this.codaSposta[k] = { ...v, dopo: Date.now() + OGNI };
    else {
      delete this.codaSposta[k];
      if (r.errore) {
        notify({ title: `Non la sposto su ${nomeMacchina(v.macchina)}`, body: r.errore, level: "error" });
        this.avvisa(s, `Non la sposto: ${r.errore}`, cx);
      } else if (r.avviso) notify({ title: `Spostata su ${nomeMacchina(v.macchina)}, con un problema`, body: r.avviso, level: "warning" });
      else notify({ title: `Spostata su ${nomeMacchina(v.macchina)}`, body: titolo(s), level: "info", timeout: 5000 });
    }
    this.aggiorna(cx);
    cx.notify();
    this.giraCoda(cx);
  }

  // Gli spostamenti rimasti in volo da una ricarica del mod (#5559, voloSposta di sessioni.js): al
  // caricamento Volta li riprende uno alla volta, come la coda. Uno che un'altra copia viva segue
  // ("altrui") si riguarda dopo VOLO_FRESCO_MS, finché non finisce o resta senza nessuno; per al più un'ora.
  riprendiVolo(cx) {
    if (this.riprendo) return;
    this.riprendo = true;
    cx.spawn(async (cx) => {
      try {
        for (let giri = 0; giri < 180; giri++) {
          let altrui = false;
          for (const { k, v } of await spostamentiInVolo()) {
            const che = voloSposta(v, Date.now());
            if (che === "scarta") { await togliVolo(k); continue; }
            if (che === "altrui" || this.faccio[chiave(v.s)]) { altrui = true; continue; }
            while (this.spostando) await cx.sleep(1000);
            const s = v.s, k2 = chiave(s);
            const mio = (this.spostando = Date.now());
            this.faccio[k2] = "sposta";
            this.spostoSu = { ...(this.spostoSu ?? {}), [k2]: v.macchina };
            this.pubblicaSposto();
            cx.notify();
            let r;
            try { r = await riprendiSposta(v, (ms) => cx.sleep(ms)); } catch (e) {
              r = { errore: String(e?.message ?? e).slice(0, 160) };
              await tracciaSposta(s, "caduto", { errore: r.errore });
            }
            await tracciaSposta(s, "fine", { esito: r, ripreso: true });
            this.finitoSposta(s, { macchina: v.macchina, id: s.id, da: s.host ?? "qui" }, r, cx, mio);
          }
          if (!altrui) break;
          await cx.sleep(VOLO_FRESCO_MS);
        }
      } finally { this.riprendo = false; }
    });
  }

  premiId(id, cx) {
    const s = this.trovaId(id);
    if (s) this.premi(s, cx);
  }

  // Le carte della Coda (#5720), già in ordine, senza quelle appena risposte (senzaRisposte): la parte
  // coda.js e la barra di stato le leggono da shared arturo.coda. Il capo (#5723) mette i suoi giudizi
  // sulle carte delle sessioni (conCapo) e fonde le doppie; la misura della settimana va in
  // arturo.coda.misura, per la testata della Coda.
  aggiornaCoda() {
    const cc = fondiDoppie(senzaScartate(senzaRisposte(ordineCoda([...conCapo(carte(this.dati?.sessioni), this.uf), ...carteUf(this.uf)]), this.risposte), this.scartate));
    if (JSON.stringify(cc) !== JSON.stringify(shared("arturo.coda") ?? [])) setShared("arturo.coda", cc);
    const m = rigaMisura(this.uf?.misura);
    if (m !== (shared("arturo.coda.misura") ?? null)) setShared("arturo.coda.misura", m);
  }

  // "arturo.checklist" (⌘⇧S) e "arturo.checklist-<chiave>" (17/11/2026): la ripartenza di /inizio come
  // checklist con le note, nel dialogo di checklist.js. Senza chiave vale la sessione della scheda davanti.
  // La scelta torna con arturo.coda-rispondi, cioè rispondiCoda qui sotto: stessi canali della Coda.
  checklist(k = null) {
    const davanti = shared("arturo.volta.davanti");
    const s = k ? this.trovaId(k) : davanti ? this.trovaId(`${davanti.host ?? "qui"}:${davanti.id}`) : null;
    if (!s) return notify({ title: "Nessuna sessione davanti", body: "La checklist è quella della sessione nella scheda in primo piano.", level: "info", timeout: 4000 });
    // senza ripartenza la lista sono i task del progetto della sessione (checklist.js); senza progetto non c'è
    if (!vociRipartenza(s.ripartenza).length && !s.progetto) return notify({ title: `${titolo(s)} non ha una checklist`, body: "La checklist viene dalla ripartenza di /inizio o dai task del progetto: questa sessione non ha un progetto.", level: "info", timeout: 5000 });
    const mandata = checklistMandata(s, shared("arturo.checklist.mandate"));
    apriChecklist({ chiave: chiave(s), sessionId: s.sessionId, titolo: titolo(s), progetto: s.progetto ?? null, ripartenza: mandata ? null : s.ripartenza });
  }

  // "arturo.coda-rispondi-<chiave>-<esadecimale>": la risposta scelta su una carta della Coda (#5720),
  // che torna alla sessione su qualunque macchina (#5721). Il canale lo sceglie canaleRisposta() di
  // sessioni.js: un dialogo aperto o un'interattiva fuori da Herdr si aprono nella scheda con un avviso
  // che dice il testo; con una scheda qui la risposta si scrive lì; in background la sonda ferma la
  // sessione e la riprende con la risposta. Se non arriva, la sessione si apre come per il dialogo.
  // Ogni risposta va nel registro (volta_carte.py risposta). La carta esce subito dalla Coda.
  rispondiCoda(k, testo, cx, p = null) {
    if (/^(uf|bozza):/.test(String(k))) return this.rispondiUf(k, testo, cx, p);
    const s = this.trovaId(k);
    if (!s || !testo) return;
    const c = (shared("arturo.coda") ?? []).find((x) => x?.chiave === k) ?? { chiave: k, macchina: s.macchina, progetto: s.progetto ?? null };
    const canale = canaleRisposta(s, c, schedeRisposta(s));
    const apri = (perche) => {
      terminale();
      this.premi(s, cx);
      notify({ title: perche ? `Scrivi tu in ${titolo(s)}: ${perche}` : `Scrivi in ${titolo(s)}`, body: testoPerSessione(testo), level: perche ? "warning" : "info", timeout: 12000 });
    };
    this.risposte = { ...(this.risposte ?? {}), [k]: Date.now() };
    this.aggiornaCoda();
    // la checklist resta in bozza finché la risposta non arriva (dopoRisposta di sessioni.js)
    const esitoChecklist = (ok, errore) => {
      const st = dopoRisposta({ bozze: shared("arturo.checklist.bozze"), mandate: shared("arturo.checklist.mandate"), aperte: shared("arturo.checklist.aperte") },
        s.sessionId, { ok, errore, testo });
      if (!st) return;
      setShared("arturo.checklist.bozze", st.bozze);
      setShared("arturo.checklist.mandate", st.mandate);
      setShared("arturo.checklist.aperte", st.aperte);
    };
    if (canale === "dialogo" || canale === "apri") {
      apri(null);
      esitoChecklist(false, canale === "dialogo" ? "la sessione era ferma su un dialogo: rispondi lì, poi rimanda" : "la sessione è fuori da Herdr: scrivila tu");
      registraRisposta(rigaRisposta(c, p?.scelta ?? testo, canale, "aperta", null, p?.nota));
      return;
    }
    cx.spawn(async (cx) => {
      let r;
      try { r = await rispondiSessione(s, testoPerSessione(testo), canale); } catch (e) { r = { errore: String(e?.message ?? e).slice(0, 160) }; }
      esitoChecklist(Boolean(r?.ok), r?.errore);
      registraRisposta(rigaRisposta(c, p?.scelta ?? testo, canale, r?.ok ? "ok" : "errore", r?.errore, p?.nota));
      registra("risposta", { macchina: s.host ?? "qui", sid: s.id, esito: r?.ok ? "ok" : "errore", errore: r?.errore });
      if (r?.ok) return notify({ title: `Risposta a ${titolo(s)}`, body: testo, level: "info", timeout: 6000 });
      // non è arrivata: la carta torna in Coda e la sessione si apre, col testo da scrivere
      this.risposte = { ...(this.risposte ?? {}) };
      delete this.risposte[k];
      this.aggiornaCoda();
      apri(r?.errore ?? "non ha risposto");
      cx.notify();
    });
  }

  // "arturo.coda-gesto-<chiave>-<esadecimale>" (16/11/2026): Già fatto, Scarta, Note o un'opzione col
  // commento di C. gestoCoda() di sessioni.js dice cosa fa il gesto; Scarta di una sessione o di una bozza
  // toglie la carta da questa macchina (scartate.json), il resto passa da rispondiCoda e rispondiUf.
  gestoDaCoda(k, gesto, commento, cx) {
    const c = (shared("arturo.coda") ?? []).find((x) => x?.chiave === k);
    const p = gestoCoda(c, gesto, commento);
    if (!p) return notify({ title: c ? "Scrivi la nota prima di Invio" : "Questa carta non c'è più", body: c ? c.domanda : "La Coda si rilegge fra poco.", level: "warning" });
    if (p.azione !== "scarta") return this.rispondiCoda(k, p.testo, cx, p);
    const quando = Number(c.quando) || Date.now();
    this.scartate = { ...(this.scartate ?? {}), [k]: quando };
    this.aggiornaCoda();
    cx.spawn(async () => { await scartaCarta(k, quando); });
    registraRisposta(rigaRisposta(c, p.scelta, "scarta", "ok", null, p.nota));
    notify({ title: "Tolta dalla Coda", body: c.domanda, level: "info", timeout: 4000 });
  }

  // Le carte UF dal capo (volta_capo.py prendi, #5722). Un capo che non risponde lascia le carte di prima,
  // segnate vecchie dallo script; uno script che non risponde lascia le carte com'erano.
  leggiUf(cx) {
    if (this.leggoUf) return;
    const mio = (this.leggoUf = Date.now());
    cx.spawn(async (cx) => {
      try {
        const d = await prendiCarteUf();
        if (d) { this.uf = d; this.aggiornaCoda(); cx.notify(); }
      } finally { lascia(this, "leggoUf", mio); }
    });
  }

  // La risposta su una carta UF (#5722): il gesto di gestoUf() di azioni.js. Un task si scrive con
  // `arturo todo` su questa macchina (il titolo atteso ferma il gesto se il task è cambiato); Apri porta
  // Claude sul task, o Gmail in Firefox per una bozza; Riscrivi fa nascere Claude con /posta. La carta
  // resta fuori dalla Coda fino al giro dopo del capo (senzaRisposte); se il gesto non riesce, torna.
  rispondiUf(k, testo, cx, p = null) {
    const c = (shared("arturo.coda") ?? []).find((x) => x?.chiave === k);
    const g = gestoUf(c, testo, { nota: p?.nota });
    if (!g) return notify({ title: "Questa carta non c'è più", body: "La Coda si rilegge fra poco.", level: "warning" });
    const torna = (titoloAvviso, body) => {
      this.risposte = { ...(this.risposte ?? {}) };
      delete this.risposte[k];
      this.aggiornaCoda();
      notify({ title: titoloAvviso, body, level: "warning", timeout: 8000 });
      cx.notify();
    };
    this.risposte = { ...(this.risposte ?? {}), [k]: Date.now() + (g.azione === "rimanda" ? RIMANDA_MS : 0) };
    this.aggiornaCoda();
    registraRisposta(rigaRisposta(c, p?.scelta ?? testo, "uf", "ok", null, p?.nota));
    if (g.azione === "rimanda" || g.azione === "giafatto") return notify({ title: g.esito, body: c.domanda, level: "info", timeout: 4000 });
    cx.spawn(async () => {
      if (g.azione === "link") { if (!(await apriLink(g.url))) torna("Gmail non si apre", c.domanda); return; }
      if (g.azione === "nuova") { terminale(); await nuova(g.prompt); return; }
      // il commento della Coda va sul task prima del gesto: un gesto che chiude il task non lo perde
      for (const argv of g.prima ?? []) {
        const n = await todo(argv);
        if (!n.ok) return torna("Il commento non è arrivato sul task", n.errore ?? c.domanda);
      }
      if (g.azione === "apri") {
        terminale();
        if (g.progetto) await apriProgetto(g.progetto, g.todo);
        else await nuova(`Lavoriamo sul todo #${g.todo.id}: ${g.todo.titolo}`);
        return;
      }
      const r = await todo(g.argv);
      setShared("arturo.scritto", Date.now());
      // "A Claude": il task passa a Claude e Claude ci lavora subito, nella sessione del progetto se c'è,
      // altrimenti in una nuova con /inizio. Federico resta nella Coda.
      if (r.ok && g.poi) {
        notify({ title: g.esito, body: c.domanda, level: "success", timeout: 5000 });
        if (g.poi.progetto) await apriProgetto(g.poi.progetto, g.poi.todo);
        else await nuova(`Lavoriamo sul todo #${g.poi.todo.id}: ${g.poi.todo.titolo}`);
        return;
      }
      if (r.ok) return notify({ title: g.esito, body: c.domanda, level: "success", timeout: 4000 });
      torna(r.codice === 2 ? "Questo task è cambiato nel frattempo" : "Non sono riuscito a scrivere il task",
        r.codice === 2 ? "La carta torna in Coda: riprova dopo il giro del capo." : r.errore);
    });
  }

  // "arturo.volta-altro-<chiave>" e "arturo.volta-gesto-<verbo>-<chiave>": il clic su "Altro" e su un suo
  // bottone, da herdr-app do. Herdr non ha clic simulati: le prove dei gesti passano da qui (#5203).
  altroId(id, cx) {
    const s = this.trovaId(id);
    if (!s) return;
    if (!azioni(s).length) return notify({ title: "Niente gesti su questa sessione", body: "Altro c'è solo sulle sessioni in background.", level: "warning" });
    this.menu = this.menu === chiave(s) ? null : chiave(s);
    this.scopri(s);
    cx.notify();
  }

  // Una sessione ferma sta dietro "N ferme": il comando che ne apre i gesti apre anche il suo gruppo.
  scopri(s) {
    const g = gruppi(this.vis(), this.modo()).find((x) => x.sessioni.some((y) => chiave(y) === chiave(s)));
    if (g && s.stato === "ferma") this.aperti[g.chiave] = true;
  }

  // "arturo.volta-menu-<id>": il menu del tasto destro, da herdr-app do (si apre al puntatore).
  menuId(id) {
    const s = this.trovaId(id);
    if (s && !apriMenuSessione(s)) notify({ title: "Niente menu su questa sessione", body: "La sua macchina non risponde.", level: "warning" });
  }

  // Un gesto per nome: dal menu del tasto destro (che è un'altra copia del mod) e da herdr-app do.
  gestoId(verbo, id, cx) {
    const s = this.trovaId(id);
    if (!s) return;
    const voci = menu(s).concat(azioni(s).filter((x) => x.verbo === "stop"));
    const a = voci.find((x) => x.verbo === verbo);
    if (!a) return notify({ title: `${verbo}: gesto che qui non c'è`, body: `Su questa sessione: ${voci.map((x) => x.verbo).join(", ") || "nessuno"}.`, level: "warning" });
    if (verbo in CAMBIA) return this.chiedi(s, CAMBIA[verbo]);
    // Sposta su… del menu: il popup delle macchine (sposta.js), per la copia che l'elenco mostra.
    if (verbo === "sposta") return apriSposta(perSposta(this.vistaId(id) ?? s));
    if (verbo === "riprendi") return apriSposta(perSposta(s), "riprendi");
    if (SOLO_MENU.has(verbo)) return this.fare(s, a, cx);
    this.menu = chiave(s);
    this.scopri(s);
    this.fare(s, a, cx);
  }

  // Rinomina e Cambia progetto: il dialogo di cambio.js, coi progetti fra cui scegliere (quelli
  // dell'elenco e le cartelle della base). Il dialogo risponde col comando "arturo.volta-cambia-…".
  chiedi(s, cosa) {
    if (s.vecchia) return notify({ title: "Non la posso cambiare adesso", body: `${s.macchina} non risponde.`, level: "warning" });
    if (cosa !== "progetto") return apriCambio(s, cosa, []);
    nomiProgetti().catch(() => []).then((l) => apriCambio(s, cosa, progettiNoti(this.dati, l)));
  }

  // "arturo.volta-cambia-<nome|progetto>-<esadecimale>-<id>": il cambio deciso nel dialogo, o da herdr-app do.
  cambiaComando(c, cx) {
    const d = leggiCambio(c);
    if (!d) return notify({ title: "Cambio non valido", body: "Serve un nome, oppure un progetto con lettere, numeri e trattini.", level: "warning" });
    const s = this.trovaId(d.id);
    if (s) this.cambia(s, d.cosa, d.valore, cx);
  }

  // Scrive il nome o il progetto nuovo sulla macchina della sessione, poi lo porta dove si vede: il
  // nome sulla scheda e in Claude Code (subito se è ferma, altrimenti alla prima lettura in cui lo è),
  // il progetto spostando la scheda nel suo spazio. L'elenco si rilegge subito.
  cambia(s, cosa, valore, cx) {
    const k = chiave(s);
    if (this.faccio[k]) return;
    if (s.vecchia) return this.avvisa(s, `${s.macchina} non risponde: riprova quando torna.`, cx);
    this.faccio[k] = cosa;
    cx.notify();
    cx.spawn(async (cx) => {
      let r, dopo = {};
      try {
        r = await cambiaSessione(s, cosa, valore);
        if (r.ok && cosa === "nome" && valore) rinominaSchede(s, valore);
        if (r.ok && cosa === "progetto" && String(s.progetto ?? "") !== valore) dopo = await spostaScheda(s, valore);
        // la ripresa da /inizio la fa questa finestra, alla prima lettura in cui la sessione è ferma (#5465)
        if (r.ok && cosa === "progetto" && r.iniziato === false) this.spostate[k] = valore;
      } catch (e) { r = { errore: String(e?.message ?? e).slice(0, 120) }; }
      delete this.faccio[k];
      if (r.errore) this.avvisa(s, `Non riesco: ${r.errore}`, cx);
      else {
        const inizio = cosa === "progetto" && r.iniziato === false ? ` Riparte da /inizio ${valore} appena è ferma.` : "";
        const frase = cosa === "nome" ? (valore ? `Ora si chiama "${valore}".` : "Nome tolto: torna il titolo automatico.")
          : (dopo.errore ? `Ora è in ${nomeProgetto(valore)}, ma la scheda non si riapre: ${dopo.errore}`
          : dopo.resta ? `Ora è in ${nomeProgetto(valore)}. La sua scheda resta dov'è: chiuderla fermerebbe la sessione.`
          : `Ora è in ${nomeProgetto(valore)}.`) + inizio;
        this.avvisa(s, frase, cx);
        this.aggiorna(cx);
      }
      cx.notify();
    });
  }

  // ⌘W (Ctrl+W su Windows): il comando "arturo.volta-chiudi" (Federico, 12/11/2026: "quella sessione va
  // in chiusura e non deve più apparirmi nelle freccette e nell'elenco"). Se la scheda davanti aggancia
  // una sessione in background non chiusa, anche di una macchina che non risponde, è Chiudi del menu: via
  // la scheda, congedo, fuori da elenco e giro subito. Una scheda senza sessione (una shell,
  // un'interattiva) si chiude come il ⌘W di Herdr.
  // `scheda`: la X di una scheda nella fila delle schede (testata.js); senza, la scheda in primo piano.
  chiudiDavanti(cx, scheda = null) {
    const f = focused();
    const tab = scheda ?? f?.tab ?? null;
    const indirizzo = scheda ? panes().find((p) => p.tab === scheda)?.terminal : f?.terminal;
    const t = indirizzo ? terminals().find((x) => x.address === indirizzo) ?? null : null;
    const s = t ? sessioneDi(t, this.dati?.sessioni ?? []) : null;
    // anche la sessione di una macchina che non risponde: il congedo aspetta che torni (passoCongedo, fino a
    // CONGEDO_VECCHIO_MS). Prima ⌘W chiudeva solo la scheda, e la sessione restava accesa su quella macchina
    // e tornava nell'elenco (Federico, 14/11/2026: "con CMD + W non chiude davvero alcune schede").
    // Una scheda aperta dalla finestra di un'altra macchina (#5802) si chiude soltanto: il congedo lo fa la
    // finestra che l'ha aperta, quando la vede sparire. Due congedi della stessa sessione farebbero due /fine.
    if (s && s.tipo === "background" && !chiusa(s) && mia(t, ioQui())) return this.fare(s, { verbo: "chiudi", testo: "Chiudi" }, cx);
    run("tab.close", tab ? { id: tab } : {});
  }

  // Chiudi del menu: via la scheda, poi il congedo (/fine e claude stop), come ⌘W sulla scheda.
  // Con la scheda aperta dalla finestra di un'altra macchina (#5811) chiude anche quella, e il congedo lo fa
  // l'altra finestra quando la vede sparire (chiudiAltrui di dati.js): qui niente congedo, o sarebbero due /fine.
  async chiudi(s, cx) {
    if (chiudiAltrui(s)) {
      chiudiSchede(s);
      return { ok: true };
    }
    chiudiSchede(s);
    this.congeda(s, cx);
    return { ok: true };
  }

  // Un gesto di "Altro" o del menu: l'anteprima resta sotto la riga, gli altri rileggono l'elenco.
  // Elimina chiede prima la conferma, con un secondo clic sullo stesso bottone.
  fare(s, a, cx) {
    const k = chiave(s);
    if (this.faccio[k]) return;
    if (a.verbo === "apri") return this.premi(s, cx);
    if (a.verbo === "contesto") return apriContesto(s.progetto);
    if (a.conferma && this.chiedo[k] !== a.verbo) { this.chiedo[k] = a.verbo; return cx.notify(); }
    delete this.chiedo[k];
    if (a.verbo === "logs" && this.anteprime[k]) { delete this.anteprime[k]; return cx.notify(); }
    // L'anteprima viene dalla riga già letta (#5240): niente comando, e segue le letture dopo.
    if (a.verbo === "logs" && anteprima(s)) { this.anteprime[k] = true; return cx.notify(); }
    this.faccio[k] = a.verbo;
    cx.notify();
    cx.spawn(async (cx) => {
      let r;
      try {
        r = a.verbo === "chiudi" ? await this.chiudi(s, cx)
          : a.verbo === "duplica" || a.verbo === "fork" ? await copiaSessione(s, a.verbo)
          : await azioneSessione(s, a.verbo);
      } catch (e) { r = { errore: String(e?.message ?? e).slice(0, 120) }; }
      delete this.faccio[k];
      // Duplica e Fork dicono sempre com'è andata anche fuori dalla riga: la copia nasce in un'altra
      // scheda, e un errore sulla sola riga passava inosservato (12/11/2026).
      if (a.verbo === "duplica" || a.verbo === "fork") notify(r.errore
        ? { title: a.verbo === "fork" ? "Fork non riuscito" : "Duplica non riuscita", body: r.errore, level: "warning" }
        : { title: FATTO[a.verbo], body: titolo(s), level: "info", timeout: 4000 });
      if (r.errore) this.avvisa(s, `Non riesco: ${r.errore}`, cx);
      else if (a.verbo === "logs") this.anteprime[k] = r.righe?.length ? r.righe : ["(niente da mostrare)"];
      else {
        // la riga di una sessione chiusa dice già "Si chiude fra N s · Annulla" (#5883): niente avviso sotto
        if (a.verbo !== "chiudi") this.avvisa(s, FATTO[a.verbo], cx);
        // l'esito va in un avviso, col modo di annullare finché l'attesa dura
        if (a.verbo === "chiudi") notify({ title: titolo(s), level: "info", timeout: 5000,
          body: (s.vecchia ? `Chiusa: ${s.macchina ?? "la sua macchina"} non risponde, Claude salva con /fine e si ferma quando torna.` : FATTO.chiudi)
            + (inAnnullo(this.congedi()[chiave(s)]) ? ` Fra ${Math.round(ANNULLA_MS / 1000)} s: per annullare clicca la riga o premi ${tasti().annulla}.` : "") });
        if (a.verbo === "rm") this.menu = null;
        this.aggiorna(cx);
      }
      cx.notify();
    });
  }

  gesti(t, s, az) {
    const k = chiave(s);
    const bottone = (a) => {
      const testo = this.faccio[k] === a.verbo ? "…" : this.chiedo[k] === a.verbo ? a.conferma
        : a.verbo === "logs" && this.anteprime[k] ? "Chiudi l'anteprima" : a.testo;
      return div().id(`vg-${s.host}-${s.id}-${a.verbo}`).px(8).py(3).rounded(6).cursor_pointer()
        .text_size(12).border_1().border_color(this.chiedo[k] === a.verbo ? t.blocked : t.border)
        .text_color(this.chiedo[k] === a.verbo ? t.blocked : t.muted)
        .hover((st) => st.bg(t.selected))
        .on_click((_e, cx) => this.fare(s, a, cx))
        .child(testo);
    };
    // Risposta e azione vanno a capo; lo schermo di claude logs (senza trascrizione) resta a righe fisse.
    const vista = this.anteprime[k];
    const blocchi = vista === true ? anteprima(s) : vista ? [{ schermo: true, righe: vista }] : null;
    const rigo = (b, r, id) => b.schermo
      ? div().id(id).truncate().font_family(fontTerminale()).text_size(11.5).text_color(t.muted).child(r || " ")
      : div().id(id).whitespace_normal().text_size(12.5).text_color(t.foreground).child(r);
    return v_flex().gap(6)
      .child(h_flex().gap(6).flex_wrap().children(az.map(bottone)))
      .when(Boolean(blocchi), (el) => el.child(v_flex().p(8).gap(8).rounded(6).bg(t.hover).overflow_hidden()
        .children(blocchi.map((b, i) => v_flex().gap(2)
          .when(Boolean(b.etichetta), (e) => e.child(div().text_size(11).text_color(t.dim).child(b.etichetta)))
          .children(b.righe.map((r, j) => rigo(b, r, `vl-${s.id}-${i}-${j}`)))))));
  }

  // I gesti di "Altro" stanno sotto l'elenco, fuori dalla parte che scorre (#5241): sotto una riga in
  // fondo finivano oltre il bordo dei 360 px, e Herdr non ha uno scorrimento comandato per un elenco
  // semplice. Qui si vedono sempre, col titolo della sessione a cui valgono.
  pannello(t) {
    const s = this.menu ? (this.dati?.sessioni ?? []).find((x) => chiave(x) === this.menu) : null;
    const az = s ? azioni(s) : [];
    if (!az.length) return null;
    const avviso = this.avvisi[chiave(s)];
    // Al più 160 px (GESTI_MAX): un'anteprima lunga scorre nel riquadro e non spinge via i progetti.
    return v_flex().id("volta-gesti").max_h(GESTI_MAX).flex_none().overflow_y_scroll().mx(MARGINE).mt(SPAZIO.xs).px(SPAZIO.m + 2).py(SPAZIO.m).gap(SPAZIO.s + 2).rounded(RAGGIO.riga).border_1().border_color(t.border)
      .child(h_flex().gap(6).items_start()
        .child(div().id("volta-gesti-titolo").flex_1().min_w(0).truncate().text_size(12.5).font_semibold().text_color(t.foreground).child(titolo(s)))
        .child(div().id("volta-gesti-chiudi").px(6).rounded(6).cursor_pointer().text_size(12).text_color(t.dim)
          .hover((st) => st.bg(t.selected))
          .on_click((_e, cx) => { this.menu = null; cx.notify(); })
          .child("Chiudi")))
      .child(this.gesti(t, s, az))
      .when(Boolean(avviso), (el) => el.child(div().id("volta-gesti-avviso").whitespace_normal().text_size(12.5).text_color(t.foreground).child(avviso)));
  }

  riga(t, s, modo, cx) {
    const k = chiave(s);
    const sposto = this.sposto[k];
    const apro = this.apro[k];
    const su = nomeMacchina(this.spostoSu?.[k] ?? "qui");
    const lavoro = this.faccio[k] === "sposta" ? `La sposto su ${su}…`
      : this.codaSposta[k] ? (aFineTurno(s) ? `La sposto su ${su} a turno finito` : `In coda per ${su}…`)
      : LAVORO[this.faccio[k]];
    const d = sposto ? { testo: "La sposto nella finestra…", colore: "working" }
      : apro ? { testo: "La apro…", colore: "working" }
      : this.veglio[k] ? { testo: "Aperta: guardo se Claude resta nella scheda…", colore: "working" }
      : lavoro ? { testo: lavoro, colore: "working" }
      : s.annullo ? { testo: s.annullo, colore: "accent" } : dettaglio(s, modo);
    const avviso = this.avvisi[chiave(s)];
    // il pallino per chi lavora, ti aspetta o è in errore; niente per chi aspetta solo un comando (#5366)
    const vivo = !s.vecchia && !inAttesa(s) && !s.annullo;
    // la riga di una sessione appena chiusa (#5883): niente "Altro" e niente X, il clic annulla la chiusura
    const az = s.annullo ? [] : azioni(s);
    const aperto = this.menu === k && az.length > 0;
    // La X compare col puntatore sopra la riga, e il primo clic chiede la conferma (xRiga di sessioni.js).
    // Su una sessione viva chiude con /fine e la toglie dall'elenco, come ⌘W (Federico, 12/11/2026); su una
    // chiusa o in errore la elimina (claude rm, lo stesso Elimina di "Altro"). Nascosta tiene il suo posto:
    // il titolo non va a capo in modo diverso quando appare.
    const xa = s.annullo ? null : xRiga(s);
    const chiedoX = Boolean(xa) && this.chiedo[k] === xa.verbo, faccioX = Boolean(xa) && this.faccio[k] === xa.verbo;
    const vediX = Boolean(xa) && (this.sopra === k || chiedoX || faccioX);
    const x = xa ? div().id(`vx-${s.host}-${s.id}`).mt(2).px(5).py(2).rounded(6).flex_none()
      .when(!vediX, (el) => el.invisible())
      .when(vediX, (el) => el.cursor_pointer().hover((st) => st.bg(t.selected)).tooltip(xa.aiuto).on_click((_e, cx) => this.fare(s, xa, cx)))
      .child(faccioX ? div().text_size(12).text_color(t.dim).child("…")
        : chiedoX ? div().text_size(12).text_color(t.blocked).child(xa.conferma)
        : svg(ICONA("x")).size(12).text_color(t.dim)) : null;
    // Il clic sulla riga apre la sessione; "Altro" sta a fianco, fuori dall'area che apre.
    // Entrata e uscita in dissolvenza (#5410): solo opacità, l'altezza della riga non cambia.
    const mr = movimento() ? motoRiga(this.entrano.get(k), this.escono[k]) : null;
    // La sessione che hai davanti (corrente di sessioni.js): una barra accesa sul bordo sinistro e il fondo
    // della selezione. La barra sta sopra il padding, così il testo non si sposta.
    const acceso = this.acceso === k;
    const trascinata = Boolean(this.trascino?.mosso) && chiave(this.trascino.s) === k;
    return v_flex().id(`vr-${s.host}-${s.id}`).relative().mx(MARGINE).px(SPAZIO.m).py(SPAZIO.m).gap(SPAZIO.xs).rounded(RAGGIO.riga).when(aperto, (el) => el.bg(t.hover))
      .when(acceso, (el) => el.bg(t.selected).child(div().id(`vacc-${s.host}-${s.id}`).absolute().left(2).top(SPAZIO.m).bottom(SPAZIO.m).w(3).rounded_full().bg(t.accent)))
      .when(Boolean(mr), (el) => el.opacity(mr.opacita))
      .when(Boolean(mr?.politica), (el) => el.transition("opacity", mr.politica))
      .when(trascinata, (el) => el.opacity(0.5))
      // La pressione può cominciare un trascinamento verso un altro progetto (vista per progetto): diventa
      // tale solo dopo MOSSA_PX di movimento sull'elenco; altrimenti resta un clic.
      .on_mouse_down("left", (e) => { if (modo === "progetto") this.trascino = { s, da: e.position, mosso: false, sopra: null }; })
      .on_hover((h, cx) => {
        if (h) this.sopra = k;
        else if (this.sopra === k) {
          this.sopra = null;
          // Una conferma chiesta dalla X e lasciata lì non resta armata; quella del pannello sì.
          if ((this.chiedo[k] === "rm" || this.chiedo[k] === "chiudi") && this.menu !== k) delete this.chiedo[k];
        }
        cx.notify();
      })
      // Il tasto destro, ovunque sulla riga: il menu della sessione al puntatore.
      .on_mouse_down("right", (_e, cx) => { if (apriMenuSessione(s)) cx.stop_propagation(); })
      .child(h_flex().gap(6).items_start()
        .child(h_flex().id(`v-${s.host}-${s.id}`).flex_1().min_w(0).gap(11).items_start().cursor_pointer()
          // Un clic apre la sessione; il doppio clic sul titolo apre anche il dialogo del nome.
          .on_click((e, cx) => {
            if (this.trascino?.mosso || Date.now() - this.trascinata < 500) return;  // un trascinamento non apre
            if (s.annullo) return this.annulla(k, cx);
            return e?.click_count >= 2 ? this.chiedi(s, "nome") : this.premi(s, cx);
          })
          .child(div().pt(6).child(vivo || sposto || apro || lavoro || this.veglio[k] ? segno(colore(t, d.colore), motoDi(d.colore, !sposto && !apro && !lavoro && !this.veglio[k] && fase(s) === "stasi")) : div().size(8).flex_none()))
          .child(v_flex().flex_1().min_w(0).gap(2)
            // Un titolo scritto (al più 60 caratteri) va a capo su due righe; gli altri si tagliano.
            .child((s.titolo ? div().whitespace_normal() : div().truncate()).id(`vt-${s.host}-${s.id}`).text_size(TESTO.riga).text_color(s.vecchia || s.annullo ? t.muted : t.foreground).child(titolo(s)))
            .child(div().id(`vd-${s.host}-${s.id}`).truncate().text_size(TESTO.etichetta).text_color(colore(t, d.colore)).child(d.testo))))
        .when(az.length > 0, (el) => el.child(div().id(`va-${s.host}-${s.id}`).mt(SPAZIO.xs).px(SPAZIO.s + 2).py(1).rounded(RAGGIO.controllo).cursor_pointer()
          .text_size(TESTO.nota).text_color(aperto ? t.foreground : t.dim).hover((st) => st.bg(t.selected))
          .on_click((_e, cx) => { this.menu = aperto ? null : k; cx.notify(); })
          .child("Altro")))
        .when(Boolean(x), (el) => el.child(x)))
      .when(Boolean(avviso) && !aperto, (el) => el.child(div().id(`vw-${s.host}-${s.id}`).pl(19).whitespace_normal().text_size(TESTO.etichetta).text_color(t.foreground).child(avviso)));
  }

  // Fine di un trascinamento. Lasciata su un gruppo che la può ricevere (arrivoTrascino), la sessione
  // cambia progetto come da Cambia progetto: scheda spostata, avviso e ripartenza da /inizio (#5465).
  finisciTrascino(g, modo, cx) {
    const tr = this.trascino;
    this.trascino = null;
    if (!tr) return;
    if (tr.mosso) this.trascinata = Date.now();
    const arrivo = g ? arrivoTrascino(tr, g, modo) : null;
    if (arrivo) this.cambia(tr.s, "progetto", arrivo, cx);
    cx.notify();
  }

  interruttore(t) {
    const m = this.modo();
    const voce = (k) => h_flex().id(`volta-${k}`).flex_1().h_full().justify_center().items_center().rounded(RAGGIO.controllo).cursor_pointer().text_size(TESTO.etichetta)
      .when(m === k, (el) => el.bg(t.selected).text_color(t.foreground))
      .when(m !== k, (el) => el.text_color(t.muted).hover((s) => s.bg(t.hover)))
      .on_mouse_down("left", (_e, cx) => cx.stop_propagation())
      .on_click(() => setShared("arturo.volta.gruppi", k))
      .child(MODI[k]);
    return h_flex().mx(MARGINE).mb(SPAZIO.s).h(PULSANTE.piccolo).p(SPAZIO.xs).gap(SPAZIO.xs).rounded(RAGGIO.riga).border_1().border_color(t.border).child(voce("macchina")).child(voce("progetto"));
  }

  // Un gruppo: le sessioni che lavorano o ti aspettano sempre; quelle che aspettano un comando dietro
  // "N in attesa di comando" (#5366), salvo un gruppo di due o meno.
  gruppo(t, g, modo, cx, aperto = null) {
    const vive = g.sessioni.filter((s) => !inAttesa(s) || s.annullo);
    const ferme = g.sessioni.filter((s) => inAttesa(s) && !s.annullo);
    const mostra = mostrate(g, this.aperti[g.chiave]);
    // Per progetto l'intestazione è il progetto: un clic lo apre (il suo spazio, con /inizio), come la
    // riga di "Adesso" che c'era sotto. Quello dello spazio aperto ha il fondo della selezione.
    const progetto = modo === "progetto" && !g.raccolta && progettoApribile(g.chiave);
    const attivo = progetto && aperto === slug(g.chiave);
    // Il gruppo dove una sessione trascinata può finire, col puntatore sopra: bordo acceso e la frase.
    const arrivo = this.trascino?.sopra === g.chiave ? arrivoTrascino(this.trascino, g, modo) : null;
    return v_flex().id(`vg-${g.chiave || "senza"}`).gap(1).mx(arrivo ? 4 : 0).rounded(10)
      .when(Boolean(arrivo), (el) => el.border_1().border_color(t.accent))
      .on_hover((h, cx) => {
        if (!this.trascino?.mosso) return;
        if (h) this.trascino.sopra = g.chiave;
        else if (this.trascino.sopra === g.chiave) this.trascino.sopra = null;
        cx.notify();
      })
      .on_mouse_up("left", (_e, cx) => {
        if (!this.trascino?.mosso) return;
        this.finisciTrascino(g, modo, cx);
        cx.stop_propagation();
      })
      .child(h_flex().id(`vgh-${g.chiave || "senza"}`).mx(MARGINE).px(SPAZIO.m).py(SPAZIO.s + 1).gap(SPAZIO.s + 2).items_center().rounded(RAGGIO.riga)
        .when(attivo, (el) => el.bg(t.selected))
        .when(progetto && !attivo, (el) => el.cursor_pointer().hover((st) => st.bg(t.hover)))
        .when(progetto, (el) => el.on_click(() => apriProgetto(g.chiave))
          // il tasto destro: Apri il progetto e Contesto del progetto (menusessione.js)
          .on_mouse_down("right", (_e, cx) => { if (apriMenuProgetto(slug(g.chiave), g.titolo)) cx.stop_propagation(); }))
        .child(div().id(`vgt-${g.chiave || "senza"}`).flex_1().truncate().font_family("Arturo Archivo").text_size(TESTO.corpo).text_color(t.foreground).child(g.titolo))
        .when(g.sessioni.length > 0, (el) => el.child(div().id(`vgn-${g.chiave || "senza"}`).text_size(TESTO.nota).text_color(t.dim).child(String(g.sessioni.length)))))
      .when(Boolean(arrivo), (el) => el.child(div().id(`vgl-${g.chiave || "senza"}`).px(MARGINE + SPAZIO.m).pb(SPAZIO.xs).text_size(TESTO.nota).text_color(t.accent)
        .child(`Lascia qui per spostarla in ${g.titolo}`)))
      .when(Boolean(g.nota), (el) => el.child(div().id(`vgo-${g.chiave || "senza"}`).px(MARGINE + SPAZIO.m).pb(SPAZIO.xs).text_size(TESTO.nota).text_color(t.dim).child(g.nota)))
      .children(mostra.map((s) => this.riga(t, s, modo, cx)))
      .when((g.raccolta && g.sessioni.length > 0) || (!g.raccolta && ferme.length > 0 && (vive.length > 0 || ferme.length > 2)), (el) => el.child(h_flex().id(`vf-${g.chiave || "senza"}`).mx(MARGINE).px(SPAZIO.m).py(SPAZIO.s + 1).gap(SPAZIO.m).items_center().rounded(RAGGIO.riga).cursor_pointer()
        .hover((st) => st.bg(t.hover))
        .on_click((_e, cx) => {
          const prima = new Set(mostrate(g, this.aperti[g.chiave]).map(chiave));
          this.aperti[g.chiave] = !this.aperti[g.chiave];
          // le righe che il gruppo aperto mostra in più entrano una dopo l'altra (#5410)
          if (this.aperti[g.chiave]) this.entra(mostrate(g, true).map(chiave).filter((k) => !prima.has(k)), cx);
          cx.notify();
        })
        .child(svg(ICONA(this.aperti[g.chiave] ? "chevron-down" : "chevron-right")).size(12).text_color(t.dim))
        .child(div().text_size(TESTO.etichetta).text_color(t.muted).child(g.raccolta
          ? (this.aperti[g.chiave] ? "Nascondi le sessioni salvate" : "Mostra le sessioni salvate")
          : (this.aperti[g.chiave] ? "Nascondi quelle in attesa" : `${ferme.length} in attesa di comando`)))));
  }

  // null quando la sezione non serve (manca lo script dell'elenco). La sezione prende tutta l'altezza
  // della colonna sotto i pulsanti (12/11/2026): l'interruttore in cima, poi i gruppi che scorrono, poi
  // il riquadro dei gesti di "Altro" quando è aperto.
  render(cx) {
    if (!this.script) return null;
    const t = theme();
    impostaProgetti(shared("arturo.progetti"));
    const modo = this.modo();
    const lista = gruppi(this.visLista(), modo);
    // lo spazio aperto, letto una volta sola: spaces() passa il confine con Herdr, e una chiamata per
    // gruppo faceva sforare il tempo del disegno ("This view could not be re-rendered", 12/11/2026)
    const aperto = progettoDi(spaces().find((x) => x.active)?.name).chiave;
    // la riga accesa a sinistra: l'ultima del giro, altrimenti quella della scheda in primo piano
    const f = focused();
    const scheda = f?.terminal ? terminals().find((x) => x.address === f.terminal) ?? { address: f.terminal } : null;
    const davanti = sessioneDavanti(scheda, this.dati?.sessioni ?? []);
    this.acceso = corrente(this.giroSt, davanti ? chiave(davanti) : null, Date.now(), terminals(), this.dati?.sessioni ?? []);
    // il guasto del giro della sonda, o quello della lettura dell'elenco dopo il giro (#5575): prima il
    // secondo restava nel registro, e la colonna mostrava un elenco vecchio come se fosse fresco
    const guasto = this.errore || this.erroreLettura;
    let corpo;
    if (!this.dati) corpo = div().id("volta-vuoto").px(MARGINE + SPAZIO.m).py(SPAZIO.s).text_size(TESTO.corpo).text_color(t.muted).child(guasto ? "Non riesco a leggere le sessioni delle macchine." : "Leggo le sessioni delle macchine…");
    else if (!lista.length) corpo = div().id("volta-vuoto").px(MARGINE + SPAZIO.m).py(SPAZIO.s).text_size(TESTO.corpo).text_color(t.muted).whitespace_normal().child(`Nessuna sessione aperta. Nuova richiesta ne apre una; un progetto si apre da Cerca (${tasti().apri}) o dalle tessere (${tasti().tessere}).`);
    // overflow_y_scroll e non overflow_y_scrollbar, che avvolge l'elenco in un contenitore a cui l'altezza
    // non arriva: lì non scorreva.
    else corpo = v_flex().id("volta-elenco").flex_1().min_h(0).overflow_y_scroll().pb(12).gap(12)
      // Il trascinamento vive sull'elenco: il movimento lo fa partire oltre MOSSA_PX; un rilascio fuori
      // da un gruppo, o il puntatore che esce dall'elenco, lo chiude senza spostare niente.
      .on_mouse_move((e, cx) => {
        if (this.trascino && !this.trascino.mosso && mosso(this.trascino.da, e.position)) { this.trascino.mosso = true; cx.notify(); }
      })
      .on_mouse_up("left", (_e, cx) => { if (this.trascino) this.finisciTrascino(null, modo, cx); })
      .on_hover((h, cx) => { if (!h && this.trascino) this.finisciTrascino(null, modo, cx); })
      .children(lista.map((g) => this.gruppo(t, g, modo, cx, aperto)));
    const ultima = this.giroBuono ?? this.dati?.letto;
    const vecchio = this.dati && guasto && ultima ? `Non riesco ad aggiornare: lettura delle ${String(ultima).slice(11, 16)}.` : null;
    const gesti = this.pannello(t);
    return v_flex().id("volta").flex_1().min_h(0).gap(6)
      .child(this.interruttore(t))
      // Il ponte del microfono (microfono.js): dove va la voce adesso. Un clic lo spegne o lo riaccende.
      .when(Boolean(rigaMicrofono(shared("arturo.microfono"))), (el) => { const r = rigaMicrofono(shared("arturo.microfono")); return el.child(h_flex().id("volta-microfono").px(MARGINE + SPAZIO.m).gap(SPAZIO.s + 2).items_center().cursor_pointer()
        .on_click(() => setShared("arturo.microfono.spento", shared("arturo.microfono.spento") !== true))
        .child(svg("mods/arturo/microfono.svg").size(12).text_color(r.avviso ? t.blocked : t.accent))
        .child(div().text_size(TESTO.nota).text_color(r.avviso ? t.blocked : t.muted).child(r.testo))); })
      .when(Boolean(vecchio), (el) => el.child(div().id("volta-vecchio").px(MARGINE + SPAZIO.m).text_size(TESTO.nota).text_color(t.blocked).child(vecchio)))
      .child(corpo)
      .when(Boolean(gesti), (el) => el.child(gesti.mb(10)));
  }
}
