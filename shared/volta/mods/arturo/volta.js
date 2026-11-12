// Volta nella barra: tutte le sessioni di Claude di tutte le macchine, per macchina o per
// progetto. L'elenco lo scrive volta_sonda.py (accanto a questo file) in ~/.cache/volta/sessioni.json ogni 30 s
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

import { div, svg } from "gpui-kit";
import { h_flex, v_flex } from "gpui-base";
import { theme, exec, readTextFile, writeTextFile, appHome, home, shared, setShared, watchFolder, notify, focused, terminals, spaces, window } from "herdr";
import { impostaProgetti, gruppi, mostrate, inAttesa, daCongedare, restanti, registroProva, daQuanto, ordineGiro, statoGiro, passoGiro, corrente, GIRO_MS, sessioneDi, sessioneDavanti, titolo, dettaglio, clic, MODI, azioni, anteprima, nuoveInAttesa, statiCorti, menu, SOLO_MENU, CAMBIA, leggiCambio, progettiNoti, daPortare, daIniziare, mosso, arrivoTrascino, nomeProgetto, progettoApribile, GESTI_MAX, visibili, sparite, passoCongedo, chiusa } from "./sessioni.js";
import { entrate, motoRiga, ritardo, fase, ENTRA, ESCE, SCALA_MAX, occupanti } from "./sessioni.js";
import { ICONA, punto, colore, segno, motoDi, movimento } from "./comuni.js";
import { config, apri as apriProgetto, slug, apriSessione, mostra, azioneSessione, copiaSessione, chiudiSchede, cambiaSessione, rinominaSchede, portaNome, portaInizio, spostaScheda, nomiProgetti, esito, altrove, stacca, schedeAgganciate, congedaSessione } from "./dati.js";
import { schedeDi, cacheVolta, spostaSessione, nomeMacchina } from "./dati.js";
import { nonSiSposta, aFineTurno, spostabili, apriSposta, perSposta } from "./sposta.js";
import { apriMenuSessione } from "./menusessione.js";
import { apriCambio } from "./cambio.js";
import { bersaglio, passo, rigaMicrofono } from "./microfono.js";

const OGNI = 30000;
// Ogni quanto il mod chiede a volta_mod.py se nel repository c'è un mod nuovo (anche all'apertura).
const OGNI_MOD = 3600000;
// Ogni quanto si guarda se la scheda in primo piano aggancia una sessione di un'altra macchina (microfono.js).
const OGNI_MICROFONO = 2000;
// Ogni quanto si guarda se una scheda che agganciava una sessione è stata chiusa (⌘W, la X): il congedo.
const OGNI_SCHEDE = 3000;
const SPARITE_MAX = 3;
// Ogni quanto si guarda se la scheda in primo piano è cambiata, per la riga accesa dell'elenco.
const OGNI_FUOCO = 1000;
// Ogni quanto si guarda se c'è una sessione da chiudere da sola (#5366): una ferma da un'ora non ha fretta.
const OGNI_AUTO = 60000;
// La sessione è già agganciata in un Terminale fuori dalla finestra: la frase del primo clic, e per
// quanto resta sulla riga. Finché c'è, il clic dopo stacca quel Terminale e apre la scheda qui.
const ALTROVE = "È aperta in un Terminale. Un altro clic la porta qui.";
const ALTROVE_MS = 20000;

// Il mod si aggiorna da solo: volta_mod.py (fuori dalla cartella del mod, così un mod rotto non lo
// ferma) scarica, controlla con herdr-app check e scambia; Herdr ricarica il mod a file cambiati.
// Poi la versione installata e l'ultimo esito vanno in shared arturo.mod, per il piede della barra:
// { corta, installato, esito, giu_da, motivo }. Senza volta_mod.py o senza sorgente non fa niente.
let controlloMod = false;
export async function controllaMod(py) {
  const script = `${appHome()}/volta_mod.py`;
  if (controlloMod || !(await esiste(script))) return;
  controlloMod = true;
  try {
    await exec(py, [script, "controlla"], { timeout: 300000 });
  } catch { /* l'esito sta in mod-stato.json */ }
  try {
    const r = await exec(py, [script, "stato"], { timeout: 20000 });
    const d = JSON.parse((r.stdout || "").trim().split("\n").pop() || "{}");
    if (d.sorgente) setShared("arturo.mod", { corta: d.installato?.corta ?? null, installato: d.installato?.installato ?? null,
      esito: d.esito ?? null, giu_da: d.giu_da ?? null, motivo: d.motivo ?? null, modo: d.modo ?? null,
      programmi: d.programmi ?? null });
  } catch { /* resta l'ultimo stato letto */ }
  controlloMod = false;
}

// La frase della riga mentre un gesto del menu lavora, e quella che resta qualche secondo a gesto fatto.
const LAVORO = { chiudi: "La chiudo…", duplica: "La duplico…", fork: "Copio la conversazione…", nome: "Cambio il nome…", progetto: "Cambio il progetto…" };
const FATTO = { stop: "Fermata: un clic la riapre.", respawn: "Riavviata.", rm: "Eliminata.",
  chiudi: "Chiusa: Claude salva con /fine, poi si ferma.", duplica: "Duplicata: la sessione nuova è nella sua scheda.",
  fork: "Copiata: la copia è nella sua scheda." };

// "Riduci movimento" del sistema (Mac: Accessibilità > Schermo), in shared arturo.movimento.ridotto per
// movimento() di comuni.js. Le transizioni lo seguono già da sole; loop e rotazioni no. Si legge all'avvio:
// chi lo cambia riapre la finestra o aspetta il mod ricaricato. Altrove resta com'è.
async function ridotto() {
  try {
    if (window()?.platform !== "macos") return;
    const r = await exec("defaults", ["read", "com.apple.universalaccess", "reduceMotion"], { timeout: 5000 });
    const v = r.code === 0 && r.stdout.trim() === "1";
    if (shared("arturo.movimento.ridotto") !== v) setShared("arturo.movimento.ridotto", v);
  } catch { /* senza defaults resta acceso */ }
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
    this.apro = {};        // sessionId -> true mentre il clic prepara la scheda (servizio, respawn)
    this.veglio = {};      // sessionId -> true mentre si guarda se Claude resta nella scheda appena aperta
    this.aperti = {};
    this.menu = null;      // la sessione con i gesti aperti
    this.anteprime = {};   // sessionId -> true (risposta e azione lette dalla riga) o righe di claude logs
    this.chiedo = {};      // sessionId -> verbo che aspetta la conferma
    this.faccio = {};      // sessionId -> verbo in corso
    this.codaSposta = {};  // sessionId -> { macchina, id, da, dopo }: Sposta su e Sposta tutto, una alla volta
    this.sopra = null;     // la sessione sotto il puntatore: lì compare la X
    this.porto = {};       // sessionId -> true mentre il nome scritto dalla persona va in Claude Code
    this.inizio = {};      // sessionId -> true mentre la sessione spostata riparte da /inizio (#5465)
    this.trascino = null;  // { s, da, mosso, sopra }: la sessione che la persona sta trascinando su un progetto
    this.trascinata = 0;   // quando è finito l'ultimo trascinamento: il rilascio sulla riga non è un clic
    this.spostate = {};    // sessionId -> slug: spostate da questa finestra, che sola può riprenderle
    this.script = undefined;
    this.py = "python3";
    this.mic = null;       // il ponte del microfono acceso da questa finestra (passo di microfono.js)
    this.micScript = null; // volta_microfono.py, se c'è
    this.micLavora = false;
    this.schede = null;    // { indirizzo: sessione } al giro di prima: una che sparisce è una scheda chiusa
    this.congedo = {};     // sessionId -> true mentre un passo del congedo lavora
    this.entrano = new Map(); // sessionId -> { fase, ritardo } delle righe che entrano in dissolvenza (#5410)
    this.escono = {};      // sessionId -> true mentre la riga di una sessione in congedo si dissolve
    this.noteScript = null; // volta_note.py, se c'è: le note della finestra uguali su tutte le macchine
    this.noteInCorso = false;
    ridotto();
    cx.spawn(async (cx) => {
      // Il Python che installa-herdr.sh ha trovato e scritto in arturo.json: su Windows può essere "python".
      const c = await config();
      this.py = c.arturo[0];
      controllaMod(this.py);
      const sc = await script(c);
      // Un ponte rimasto da prima (mod ricaricato, Volta riaperta) si chiude: lo riaccende il primo giro.
      this.micScript = await esiste(`${appHome()}/mods/arturo/volta_microfono.py`);
      if (this.micScript) { try { await exec(this.py, [this.micScript, "spegni"], { timeout: 20000 }); } catch { /* niente ponte */ } }
      this.noteScript = await esiste(`${appHome()}/mods/arturo/volta_note.py`);
      this.script = sc.elenco;
      this.sposta = sc.sposta;
      if (!this.script) return cx.notify();
      await this.leggi(cx);
      cx.notify();
      this.aggiorna(cx);
      // Un'altra Volta (o /teletrasporto) che riscrive il file: lo si rilegge subito.
      try {
        for (;;) { await watchFolder(this.cartella); await this.leggi(cx); cx.notify(); }
      } catch { /* senza cartella resta il timer */ }
    });
    cx.timer.every(OGNI, (cx) => this.aggiorna(cx));
    cx.timer.every(OGNI_MOD, () => controllaMod(this.py));
    cx.timer.every(OGNI_MICROFONO, (cx) => this.microfono(cx));
    cx.timer.every(OGNI_SCHEDE, (cx) => this.guardaSchede(cx));
    // la scheda in primo piano cambiata (un clic in testata, ⌘⇧↓): la riga accesa la segue
    cx.timer.every(OGNI_FUOCO, (cx) => {
      const k = focused()?.terminal ?? null;
      if (k !== this.fuoco) { this.fuoco = k; cx.notify(); }
      this.davanti(k);
    });
    cx.timer.every(OGNI_AUTO, (cx) => this.congedaFerme(cx));
  }

  // Le sessioni in congedo (shared, così restano anche se il mod si ricarica): { sessionId: c }.
  congedi() {
    return shared("arturo.volta.congedi") ?? {};
  }

  // L'elenco come lo vede chi usa la finestra: senza chiuse e senza sessioni in congedo.
  vis() {
    return visibili(this.dati, this.congedi());
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
    const ora = sparite(this.schede, adesso, shared("arturo.volta.tolti") ?? {});
    if (ora.length > SPARITE_MAX) {
      this.troppe = (this.troppe ?? 0) + 1;
      if (this.troppe < 3) return;
      notify({ title: `${ora.length} schede chiuse insieme`, body: "Le sessioni restano aperte in background: per chiuderle usa Chiudi dal menu di ognuna.", level: "info" });
      ora.length = 0;
    }
    this.troppe = 0;
    const forse = this.forse ?? {};
    const via = ora.filter((c) => forse[c.sessionId]);
    this.forse = Object.fromEntries(ora.filter((c) => !forse[c.sessionId]).map((c) => [c.sessionId, c]));
    // una scheda vista sparire una volta sola resta nel giro di prima: al prossimo, se manca ancora, chiude
    for (const [ind, s] of Object.entries(this.schede ?? {})) if (this.forse[s.sessionId] && !(ind in adesso)) adesso[ind] = s;
    this.schede = adesso;
    // Per la testata: la macchina di ogni scheda di questa finestra che mostra una sessione, anche
    // un'interattiva partita nella shell di una scheda; le altre schede sono di questa macchina.
    const qui = (this.dati.macchine ?? []).find((x) => x.questa)?.macchina ?? null;
    const dove = Object.fromEntries(Object.entries(adesso).map(([a, s]) => [a, s.questa ? qui : s.macchina]));
    // chi gira davvero nel terminale vince sull'aggancio con cui la scheda è nata (occupanti)
    const dentro = occupanti(this.dati.sessioni);
    for (const a of Object.keys(dentro)) dove[a] = qui;
    const occupate = Object.fromEntries(Object.entries(dentro).map(([a, s]) => [a, s.id]));
    const m = { qui, schede: dove, occupate };
    if (JSON.stringify(m) !== JSON.stringify(shared("arturo.volta.dove") ?? null)) setShared("arturo.volta.dove", m);
    for (const c of via) this.congeda(c, cx);
    if (Object.keys(this.congedi()).length) this.passiCongedo(cx);
  }

  // Mette una sessione in congedo: /fine, poi claude stop (decisione di Federico, 12/11/2026). Se lavora
  // aspetta che finisca il turno. Una sessione già chiusa non ha niente da salvare. `c.auto`: la chiusura
  // automatica (#5366); con `c.fineFatta` la sessione ha già fatto /fine e si ferma soltanto.
  congeda(c, cx) {
    const s = (this.dati?.sessioni ?? []).find((x) => x.sessionId === c.sessionId);
    if (!s || s.tipo !== "background" || chiusa(s) || this.congedi()[c.sessionId]) return;
    if (!c.uscita && this.esce(s, c, cx)) return;
    const ora = Date.now();
    setShared("arturo.volta.congedi", { ...this.congedi(), [c.sessionId]: { sessionId: s.sessionId, id: s.id, host: s.host, macchina: s.macchina,
      cartella: s.cartella ?? null, titolo: titolo(s), fase: "attende", da: ora, dal: ora,
      ...(c.auto ? { auto: true } : {}), ...(c.auto && s.fineFatta ? { fineFatta: true } : {}) } });
    if (this.menu === s.sessionId) this.menu = null;
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
    const k = s.sessionId;
    if (this.escono[k]) return true;
    this.escono[k] = true;
    cx.notify();
    cx.timer.after(ESCE.duration + 20, (cx) => { delete this.escono[k]; this.congeda({ ...c, uscita: true }, cx); });
    return true;
  }

  // Un passo per ogni sessione in congedo, dallo stato dell'ultima lettura (passoCongedo di sessioni.js).
  passiCongedo(cx) {
    const tutti = this.congedi();
    for (const c of Object.values(tutti)) {
      if (this.congedo[c.sessionId]) continue;
      const s = (this.dati?.sessioni ?? []).find((x) => x.sessionId === c.sessionId || (c.id && x.id === c.id));
      const p = passoCongedo(c, s, Date.now());
      if (p.avviso) notify({ title: `${c.titolo ?? "Sessione"}: chiusa`, body: p.avviso, level: "warning" });
      if (p.fai === "attendi") continue;
      const scrivi = (cambio) => {
        const ora = this.congedi();
        if (!ora[c.sessionId]) return;
        if (cambio === null) { const { [c.sessionId]: _, ...resto } = ora; setShared("arturo.volta.congedi", resto); }
        else setShared("arturo.volta.congedi", { ...ora, [c.sessionId]: { ...ora[c.sessionId], ...cambio } });
      };
      if (p.fai === "togli") { scrivi(null); continue; }
      this.congedo[c.sessionId] = true;
      cx.spawn(async (cx) => {
        let r;
        try {
          r = p.fai === "fine" ? await congedaSessione({ ...c, id: s?.id ?? c.id }) : await azioneSessione({ ...s, ...c, id: s?.id ?? c.id }, p.fai === "rm" ? "rm" : "stop");
        } catch (e) { r = { errore: String(e?.message ?? e).slice(0, 120) }; }
        delete this.congedo[c.sessionId];
        if (p.fai === "rm") {
          // /fine ha salvato e la sessione è ferma: claude rm la toglie anche da claude agents (#5401).
          // Se rm non va, la sessione resta lì, già fuori dall'elenco di Volta, e lo si dice.
          if (r?.errore) notify({ title: `${c.titolo ?? "Sessione"}: chiusa`, body: `Salvata con /fine, ma non riesco a eliminarla: ${r.errore}`, level: "warning" });
          scrivi(null);
        } else if (r?.errore && p.fai === "fine") {
          // la ripresa con /fine non parte: la sessione si ferma comunque, e lo si dice
          notify({ title: `${c.titolo ?? "Sessione"}: chiusa senza /fine`, body: r.errore, level: "warning" });
          await azioneSessione({ ...s, ...c, id: s?.id ?? c.id }, "stop").catch(() => null);
          scrivi({ fase: "ferma", dal: Date.now() });
        } else scrivi({ fase: p.fase ?? c.fase, dal: Date.now(), ...(p.salvata ? { salvata: true } : {}) });
        this.aggiorna(cx);
        cx.notify();
      });
    }
  }

  // La chiusura automatica (#5366, nota di Federico dell'11/11): una sessione di questa macchina che
  // aspetta un comando da più di un'ora va in congedo da sola, una alla volta, al più 3 all'ora e 12 al
  // giorno (arturo.json: congedo, congedo_dopo_min, congedo_ora, congedo_giorno). In modo "prova" scrive
  // soltanto chi chiuderebbe. Il registro sta in congedo-auto.json di cacheVolta(): lo scrive solo chi lo
  // ha letto per ultimo (writeTextFile con il testo di prima), così due finestre aperte sulla stessa
  // macchina non chiudono la stessa sessione e non sforano i tetti.
  async congedaFerme(cx) {
    if (this.autoLavora || !this.dati) return;
    this.autoLavora = true;
    try {
      const cfg = (await config()).congedo;
      if (cfg.modo === "spento") return;
      const file = `${this.cartella}/congedo-auto.json`;
      const testo = await readTextFile(file).catch(() => null);
      let reg = {};
      try { reg = JSON.parse(testo ?? "{}") ?? {}; } catch { reg = {}; }
      const adesso = Date.now();
      const conScheda = new Set(Object.values(this.schede ?? {}).map((x) => x?.sessionId).filter(Boolean));
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
      notify({ title: `${titolo(s)}: la chiudo`, body: `Aspettava un comando ${daQuanto(s.interazione || s.ultimo, adesso)}: faccio /fine e la fermo.`, level: "info" });
      this.congeda({ sessionId: s.sessionId, auto: true }, cx);
    } catch { /* un registro scritto da un'altra finestra nel frattempo: si riprova al giro dopo */ }
    finally { this.autoLavora = false; }
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
    this.micLavora = true;
    let esito = null;
    try {
      const r = await exec(this.py, [this.micScript, azione.verbo, ...(azione.target ? [azione.target] : [])], { timeout: 20000 });
      esito = JSON.parse((r.stdout || "").trim().split("\n").pop() || "{}");
    } catch { esito = { stato: "errore", motivo: "non riesco a lanciare il ponte" }; }
    this.micLavora = false;
    if (this.mic && azione.verbo === "accendi") this.mic = { ...this.mic, stato: esito.stato ?? "avvio", motivo: esito.motivo ?? null };
    this.dicoMicrofono(spento, cx);
  }

  dicoMicrofono(spento, cx) {
    const qui = (this.dati?.macchine ?? []).find((x) => x.questa)?.macchina ?? null;
    const m = spento ? { spento: true } : this.mic ? { stato: this.mic.stato, macchina: this.mic.macchina, motivo: this.mic.motivo ?? null, qui } : null;
    if (JSON.stringify(m) !== JSON.stringify(shared("arturo.microfono") ?? null)) { setShared("arturo.microfono", m); cx.notify(); }
  }

  async leggi(cx) {
    const prima = this.dati;
    try {
      const testo = await readTextFile(this.file);
      if (testo) this.dati = JSON.parse(testo);
    } catch { /* un file a metà: resta l'ultima lettura buona */ }
    if (this.dati !== prima) {
      this.entra(entrate(prima, this.dati), cx);
      for (const s of nuoveInAttesa(prima, this.dati))
        notify({ title: `${titolo(s)} ti aspetta`, body: `Su ${s.macchina}: aprila da Tutte le sessioni.`, level: "info" });
      const st = statiCorti(this.dati);
      if (JSON.stringify(st) !== JSON.stringify(shared("arturo.volta.stati") ?? {})) setShared("arturo.volta.stati", st);
    }
    this.portaNomi();
    this.portaInizi();
    // Le macchine per la riga "Nasce su" (dati.js altreMacchine), scritte solo quando cambiano.
    const m = (this.dati?.macchine ?? []).map((x) => ({ host: x.host, macchina: x.macchina, questa: Boolean(x.questa), giu: Boolean(x.irraggiungibile) }));
    if (JSON.stringify(m) !== JSON.stringify(shared("arturo.volta.macchine") ?? [])) setShared("arturo.volta.macchine", m);
  }

  // I nomi scritti dalla persona che Claude Code non ha ancora (campo daPortare): a ogni lettura si
  // prova a portarli con /rename, una sessione alla volta. Riesce quando la sessione è ferma e ha una
  // scheda in questa finestra; altrimenti si riprova alla lettura dopo.
  portaNomi() {
    for (const s of this.dati?.sessioni ?? []) {
      const k = s.sessionId;
      if (!daPortare(s) || this.porto[k]) continue;
      this.porto[k] = true;
      portaNome(s).catch(() => false).then(() => { delete this.porto[k]; });
    }
  }

  // Le sessioni spostate in un altro progetto (campo daIniziare) ripartono da /inizio appena sono
  // ferme (#5465). Ogni finestra lo scrive in una sua scheda; la ripresa senza scheda la fa solo la
  // finestra che ha fatto lo spostamento (spostate). Una alla volta per sessione; chiuse e in congedo no.
  portaInizi() {
    for (const s of this.vis()?.sessioni ?? []) {
      const k = s.sessionId;
      if (!daIniziare(s) || this.inizio[k]) continue;
      this.inizio[k] = true;
      portaInizio(s, this.spostate[k] === s.daIniziare).catch(() => ({ fatto: false })).then((r) => {
        delete this.inizio[k];
        if (!r.fatto) return;
        delete this.spostate[k];
        if (r.come === "terminale")
          notify({ title: `${titolo(s)} è in ${nomeProgetto(s.daIniziare)}`, body: `Gira in un Terminale: scrivi lì /inizio ${s.daIniziare}.`, level: "info" });
      });
    }
  }

  // Un giro di volta_sonda.py volta, mai due insieme: con una macchina lenta un giro dura qualche secondo.
  aggiorna(cx) {
    if (!this.script || this.inCorso) return;
    this.inCorso = true;
    cx.spawn(async (cx) => {
      try {
        const r = await exec(this.py, [this.script, "volta", "--scrivi", this.file], { timeout: 60000 });
        this.errore = r.code === 0 ? null : (r.stderr || r.stdout || "").trim().split("\n").pop();
      } catch (e) {
        this.errore = String(e?.message ?? e);
      }
      setShared("arturo.volta.errore", this.errore ?? null);
      await this.leggi(cx);
      this.inCorso = false;
      this.passiCongedo(cx);
      this.giraCoda(cx);
      cx.notify();
      this.sincronizzaNote(cx);
    });
  }

  // Le note della finestra (⌘⇧N) dopo ogni giro dell'elenco: volta_note.py porta qui quelle delle altre
  // macchine e di là quelle di qui (12/11/2026). Mai due giri insieme. Lo stato va fuori da cacheVolta(),
  // che questa finestra guarda: scriverci farebbe rileggere l'elenco a ogni giro. testata.js vede le note
  // nuove da solo, perché guarda la cartella delle note.
  sincronizzaNote(cx) {
    if (!this.noteScript || this.noteInCorso) return;
    this.noteInCorso = true;
    cx.spawn(async () => {
      try {
        await exec(this.py, [this.noteScript, "sincronizza", "--scrivi", `${cacheVolta("volta-note")}/stato.json`], { timeout: 60000 });
      } catch { /* il giro dopo riprova; l'esito sta in stato.json */ }
      this.noteInCorso = false;
    });
  }

  modo() {
    // Senza una scelta della persona vale "per progetto": chi apre Volta cerca il lavoro, non la macchina.
    return shared("arturo.volta.gruppi") === "macchina" ? "macchina" : "progetto";
  }

  avvisa(s, testo, cx, ms = 7000) {
    const k = s.sessionId;
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
    if (this.sposto[s.sessionId] || this.apro[s.sessionId] || this.veglio[s.sessionId]) return;
    const secondo = this.avvisi[s.sessionId] === ALTROVE;
    delete this.avvisi[s.sessionId];
    let d = clic(s);
    // la scheda che la ospita non è in questa finestra: vale la regola di un'interattiva in un Terminale
    if (d.azione === "mostra") { if (mostra(d.terminale)) return; d = clic({ ...s, terminale: null }); }
    if (d.azione === "no") return this.avvisa(s, d.motivo, cx);
    if (d.azione === "aggancia" && this.fuori(s, secondo, cx)) return;
    if (d.azione === "aggancia") return this.apri(s, d.argv, false, cx);
    // senza teletrasporto.py nessuno sa scrivere /bg nel Terminale di quella sessione
    if (!this.sposta) return this.avvisa(s, "È aperta in un Terminale: aprila da lì.", cx);
    this.sposto[s.sessionId] = true;
    cx.notify();
    cx.spawn(async (cx) => {
      let portata = null;
      try {
        portata = esito(await exec(this.py, [this.sposta, "porta-volta", s.host, s.sessionId], { timeout: 60000 }));
      } catch (e) {
        portata = { errore: `${s.macchina} non risponde` };
      }
      delete this.sposto[s.sessionId];
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
    const k = s.sessionId;
    this.apro[k] = true;
    cx.notify();
    cx.spawn(async (cx) => {
      let r;
      try { r = await apriSessione(s, argv, pronta); } catch (e) { r = { errore: `Non la apro: ${String(e?.message ?? e).slice(0, 120)}.` }; }
      delete this.apro[k];
      if (r.errore) this.nonApre(s, r.errore, cx);
      if (r.riavviata) this.aggiorna(cx);
      if (r.veglia) this.veglio[k] = true;
      cx.notify();
      let v = null;
      try { v = r.veglia ? await r.veglia : null; } catch { /* senza veglia la scheda resta com'è */ }
      delete this.veglio[k];
      if (v?.errore) this.nonApre(s, v.errore, cx);
      if (v?.riavviata) this.aggiorna(cx);
      cx.notify();
    });
  }

  // Dal comando `do` può arrivare l'id di una sessione appena nata, che il giro in corso non ha
  // ancora scritto nell'elenco: si dice, invece di non fare niente (#5078).
  trovaId(id) {
    const s = (this.dati?.sessioni ?? []).find((x) => x.id === id || String(x.sessionId).startsWith(id));
    if (!s) notify({ title: `Non trovo la sessione ${id}`, body: "L'elenco si aggiorna fra pochi secondi: riprova.", level: "warning" });
    return s;
  }

  // ⌘↓ e ⌘↑ ("arturo.volta-giro-avanti" e "-indietro"): la sessione dopo o prima nell'elenco, di ogni
  // macchina, con lo stesso gesto del clic. Parte dalla scheda in primo piano; dentro una raffica di
  // tasti parte dall'ultima sessione chiesta, perché un aggancio ci mette qualche secondo ad aprirsi.
  giro(verso, cx) {
    impostaProgetti(shared("arturo.progetti"));
    const sessioni = this.dati?.sessioni ?? [];
    // Una ferma entra nel giro solo se ha una scheda qui: aggancio (schedeDi) o shell della scheda stessa.
    const conScheda = new Set(sessioni.filter((s) => (s.questa && s.terminale) || schedeDi(s).length).map((s) => s.sessionId));
    const st = statoGiro(this.giroSt, ordineGiro(gruppi(this.vis(), this.modo()), this.aperti, conScheda), Date.now());
    const f = focused();
    const scheda = f?.terminal ? terminals().find((x) => x.address === f.terminal) : null;
    const id = passoGiro(st.ids, st.ultimo ?? sessioneDi(scheda, sessioni)?.sessionId ?? null, verso);
    this.giroSt = { ...st, ultimo: id };
    const s = id ? sessioni.find((x) => x.sessionId === id) : null;
    // la riga accesa (corrente) segue il tasto subito, e a raffica finita torna alla scheda in primo piano
    cx.notify();
    cx.timer.after(GIRO_MS + 50, (cx) => cx.notify());
    if (s) { this.scopri(s); this.premi(s, cx); }
    else notify({ title: "Nessuna sessione da aprire", body: "L'elenco non ha sessioni che un tasto può mostrare.", level: "info", timeout: 3000 });
  }

  // La sessione della scheda in primo piano, per "Sposta su" della testata (testata.js e sposta.js, che
  // sono altre copie del mod): shared arturo.volta.davanti, null se la scheda non mostra una sessione.
  davanti(indirizzo) {
    const t = indirizzo ? terminals().find((x) => x.address === indirizzo) ?? { address: indirizzo } : null;
    const s = sessioneDavanti(t, this.dati?.sessioni ?? []);
    const v = s ? { id: s.id, sessionId: s.sessionId, host: s.host ?? "qui", macchina: s.macchina, tipo: s.tipo,
      stato: s.stato, titolo: titolo(s), progetto: s.progetto ?? null,
      sposto: this.faccio?.[s.sessionId] === "sposta" || Boolean(this.codaSposta?.[s.sessionId]) } : null;
    if (JSON.stringify(v) !== JSON.stringify(shared("arturo.volta.davanti") ?? null)) setShared("arturo.volta.davanti", v);
  }

  // La sessione `id` come la vede l'elenco: dopo uno spostamento lo stesso id c'è su due macchine, e vale
  // la copia che l'elenco mostra.
  vistaId(id) {
    return (this.vis()?.sessioni ?? []).find((x) => x.id === id) ?? this.trovaId(id);
  }

  // Quante sessioni aspettano di spostarsi o si stanno spostando (la pastiglia "Sposta tutto su…").
  inCoda() {
    return Object.keys(this.codaSposta ?? {}).length;
  }

  // "arturo.volta-sposta-<macchina>-<id>": "Sposta su" della testata o del menu (sposta.js) o herdr-app
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
      return false;
    }
    const k = s.sessionId;
    if (this.faccio[k] || this.codaSposta[k]) return false;
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
    const prese = l.filter((s) => this.spostaId(macchina, s.id, cx, true));
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
    if (this.spostando) return;
    const vive = this.vis()?.sessioni ?? [];
    const ora = Date.now();
    for (const [k, v] of Object.entries(this.codaSposta)) {
      const s = vive.find((x) => x.sessionId === k && (x.host ?? "qui") === v.da);
      if (!s || nonSiSposta(s)) { delete this.codaSposta[k]; continue; }
      if (aFineTurno(s) || v.dopo > ora) continue;
      this.spostando = true;
      this.faccio[k] = "sposta";
      cx.notify();
      cx.spawn(async (cx) => {
        let r;
        try { r = await spostaSessione(s, v.macchina); } catch (e) { r = { errore: String(e?.message ?? e).slice(0, 160) }; }
        delete this.faccio[k];
        this.spostando = false;
        if (r.lavora) this.codaSposta[k] = { ...v, dopo: Date.now() + OGNI };
        else {
          delete this.codaSposta[k];
          if (r.errore) {
            notify({ title: `Non la sposto su ${nomeMacchina(v.macchina)}`, body: r.errore, level: "error" });
            this.avvisa(s, `Non la sposto: ${r.errore}`, cx);
          } else notify({ title: `Spostata su ${nomeMacchina(v.macchina)}`, body: titolo(s), level: "info", timeout: 5000 });
        }
        this.aggiorna(cx);
        cx.notify();
        this.giraCoda(cx);
      });
      return;
    }
  }

  premiId(id, cx) {
    const s = this.trovaId(id);
    if (s) this.premi(s, cx);
  }

  // "arturo.volta-altro-<id>" e "arturo.volta-gesto-<verbo>-<id>": il clic su "Altro" e su un suo
  // bottone, da herdr-app do. Herdr non ha clic simulati: le prove dei gesti passano da qui (#5203).
  altroId(id, cx) {
    const s = this.trovaId(id);
    if (!s) return;
    if (!azioni(s).length) return notify({ title: "Niente gesti su questa sessione", body: "Altro c'è solo sulle sessioni in background.", level: "warning" });
    this.menu = this.menu === s.sessionId ? null : s.sessionId;
    this.scopri(s);
    cx.notify();
  }

  // Una sessione ferma sta dietro "N ferme": il comando che ne apre i gesti apre anche il suo gruppo.
  scopri(s) {
    const g = gruppi(this.vis(), this.modo()).find((x) => x.sessioni.some((y) => y.sessionId === s.sessionId));
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
    if (SOLO_MENU.has(verbo)) return this.fare(s, a, cx);
    this.menu = s.sessionId;
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
    const k = s.sessionId;
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

  // Chiudi del menu: via la scheda, poi il congedo (/fine e claude stop), come ⌘W sulla scheda.
  async chiudi(s, cx) {
    chiudiSchede(s);
    this.congeda(s, cx);
    return { ok: true };
  }

  // Un gesto di "Altro" o del menu: l'anteprima resta sotto la riga, gli altri rileggono l'elenco.
  // Elimina chiede prima la conferma, con un secondo clic sullo stesso bottone.
  fare(s, a, cx) {
    const k = s.sessionId;
    if (this.faccio[k]) return;
    if (a.verbo === "apri") return this.premi(s, cx);
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
      if (r.errore) this.avvisa(s, `Non riesco: ${r.errore}`, cx);
      else if (a.verbo === "logs") this.anteprime[k] = r.righe?.length ? r.righe : ["(niente da mostrare)"];
      else {
        this.avvisa(s, FATTO[a.verbo], cx);
        if (a.verbo === "rm") this.menu = null;
        this.aggiorna(cx);
      }
      cx.notify();
    });
  }

  gesti(t, s, az) {
    const k = s.sessionId;
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
      ? div().id(id).truncate().font_family("Atkinson Hyperlegible Mono").text_size(11.5).text_color(t.muted).child(r || " ")
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
    const s = this.menu ? (this.dati?.sessioni ?? []).find((x) => x.sessionId === this.menu) : null;
    const az = s ? azioni(s) : [];
    if (!az.length) return null;
    const avviso = this.avvisi[s.sessionId];
    // Al più 160 px (GESTI_MAX): un'anteprima lunga scorre nel riquadro e non spinge via i progetti.
    return v_flex().id("volta-gesti").max_h(GESTI_MAX).flex_none().overflow_y_scroll().mx(8).mt(2).px(10).py(8).gap(6).rounded(8).border_1().border_color(t.border)
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
    const sposto = this.sposto[s.sessionId];
    const apro = this.apro[s.sessionId];
    const su = nomeMacchina(this.spostoSu?.[s.sessionId] ?? "qui");
    const lavoro = this.faccio[s.sessionId] === "sposta" ? `La sposto su ${su}…`
      : this.codaSposta[s.sessionId] ? (aFineTurno(s) ? `La sposto su ${su} a turno finito` : `In coda per ${su}…`)
      : LAVORO[this.faccio[s.sessionId]];
    const d = sposto ? { testo: "La sposto nella finestra…", colore: "working" }
      : apro ? { testo: "La apro…", colore: "working" }
      : this.veglio[s.sessionId] ? { testo: "Aperta: guardo se Claude resta nella scheda…", colore: "working" }
      : lavoro ? { testo: lavoro, colore: "working" } : dettaglio(s, modo);
    const avviso = this.avvisi[s.sessionId];
    // il pallino per chi lavora, ti aspetta o è in errore; niente per chi aspetta solo un comando (#5366)
    const vivo = !s.vecchia && !inAttesa(s);
    const az = azioni(s);
    const aperto = this.menu === s.sessionId && az.length > 0;
    // La X chiude per sempre una sessione ferma (claude rm, lo stesso Elimina di "Altro"): compare col
    // puntatore sopra la riga, e il primo clic chiede la conferma. Nascosta tiene il suo posto: il
    // titolo non va a capo in modo diverso quando appare.
    const rm = az.find((a) => a.verbo === "rm");
    const k = s.sessionId;
    const chiedoRm = this.chiedo[k] === "rm", facciorm = this.faccio[k] === "rm";
    const vediX = Boolean(rm) && (this.sopra === k || chiedoRm || facciorm);
    const x = rm ? div().id(`vx-${s.host}-${s.id}`).mt(2).px(5).py(2).rounded(6).flex_none()
      .when(!vediX, (el) => el.invisible())
      .when(vediX, (el) => el.cursor_pointer().hover((st) => st.bg(t.selected)).on_click((_e, cx) => this.fare(s, rm, cx)))
      .child(facciorm ? div().text_size(12).text_color(t.dim).child("…")
        : chiedoRm ? div().text_size(12).text_color(t.blocked).child(rm.conferma)
        : svg(ICONA("x")).size(12).text_color(t.dim)) : null;
    // Il clic sulla riga apre la sessione; "Altro" sta a fianco, fuori dall'area che apre.
    // Entrata e uscita in dissolvenza (#5410): solo opacità, l'altezza della riga non cambia.
    const mr = movimento() ? motoRiga(this.entrano.get(k), this.escono[k]) : null;
    // La sessione che hai davanti (corrente di sessioni.js): una barra accesa sul bordo sinistro e il fondo
    // della selezione. La barra sta sopra il padding, così il testo non si sposta.
    const acceso = this.acceso === k;
    const trascinata = Boolean(this.trascino?.mosso) && this.trascino.s.sessionId === k;
    return v_flex().id(`vr-${s.host}-${s.id}`).relative().mx(8).px(10).py(7).gap(2).rounded(8).when(aperto, (el) => el.bg(t.hover))
      .when(acceso, (el) => el.bg(t.selected).child(div().id(`vacc-${s.host}-${s.id}`).absolute().left(2).top(7).bottom(7).w(3).rounded_full().bg(t.accent)))
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
          if (this.chiedo[k] === "rm" && this.menu !== k) delete this.chiedo[k];
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
            return e?.click_count >= 2 ? this.chiedi(s, "nome") : this.premi(s, cx);
          })
          .child(div().pt(6).child(vivo || sposto || apro || lavoro || this.veglio[s.sessionId] ? segno(colore(t, d.colore), motoDi(d.colore, !sposto && !apro && !lavoro && !this.veglio[s.sessionId] && fase(s) === "stasi")) : div().size(8).flex_none()))
          .child(v_flex().flex_1().min_w(0).gap(2)
            // Un titolo scritto (al più 60 caratteri) va a capo su due righe; gli altri si tagliano.
            .child((s.titolo ? div().whitespace_normal() : div().truncate()).id(`vt-${s.host}-${s.id}`).text_size(14).text_color(s.vecchia ? t.muted : t.foreground).child(titolo(s)))
            .child(div().id(`vd-${s.host}-${s.id}`).truncate().text_size(12.5).text_color(colore(t, d.colore)).child(d.testo))))
        .when(az.length > 0, (el) => el.child(div().id(`va-${s.host}-${s.id}`).mt(2).px(6).py(1).rounded(6).cursor_pointer()
          .text_size(12).text_color(aperto ? t.foreground : t.dim).hover((st) => st.bg(t.selected))
          .on_click((_e, cx) => { this.menu = aperto ? null : s.sessionId; cx.notify(); })
          .child("Altro")))
        .when(Boolean(x), (el) => el.child(x)))
      .when(Boolean(avviso) && !aperto, (el) => el.child(div().id(`vw-${s.host}-${s.id}`).pl(19).whitespace_normal().text_size(12.5).text_color(t.foreground).child(avviso)));
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
    const voce = (k) => div().id(`volta-${k}`).flex_1().py(4).rounded(6).cursor_pointer().text_size(12.5).text_center()
      .when(m === k, (el) => el.bg(t.selected).text_color(t.foreground))
      .when(m !== k, (el) => el.text_color(t.muted).hover((s) => s.bg(t.hover)))
      .on_mouse_down("left", (_e, cx) => cx.stop_propagation())
      .on_click(() => setShared("arturo.volta.gruppi", k))
      .child(MODI[k]);
    return h_flex().mx(14).mb(4).p(2).gap(2).rounded(8).border_1().border_color(t.border).child(voce("macchina")).child(voce("progetto"));
  }

  // Un gruppo: le sessioni che lavorano o ti aspettano sempre; quelle che aspettano un comando dietro
  // "N in attesa di comando" (#5366), salvo un gruppo di due o meno.
  gruppo(t, g, modo, cx, aperto = null) {
    const vive = g.sessioni.filter((s) => !inAttesa(s));
    const ferme = g.sessioni.filter(inAttesa);
    const mostra = mostrate(g, this.aperti[g.chiave]);
    // Per progetto l'intestazione è il progetto: un clic lo apre (il suo spazio, con /inizio), come la
    // riga di "Adesso" che c'era sotto. Quello dello spazio aperto ha il fondo della selezione.
    const progetto = modo === "progetto" && progettoApribile(g.chiave);
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
      .child(h_flex().id(`vgh-${g.chiave || "senza"}`).mx(8).px(10).py(5).gap(6).items_center().rounded(8)
        .when(attivo, (el) => el.bg(t.selected))
        .when(progetto && !attivo, (el) => el.cursor_pointer().hover((st) => st.bg(t.hover)))
        .when(progetto, (el) => el.on_click(() => apriProgetto(g.chiave)))
        .child(div().id(`vgt-${g.chiave || "senza"}`).flex_1().truncate().font_family("Arturo Archivo").text_size(13.5).text_color(t.foreground).child(g.titolo))
        .when(g.sessioni.length > 0, (el) => el.child(div().id(`vgn-${g.chiave || "senza"}`).text_size(12).text_color(t.dim).child(String(g.sessioni.length)))))
      .when(Boolean(arrivo), (el) => el.child(div().id(`vgl-${g.chiave || "senza"}`).px(18).pb(2).text_size(12).text_color(t.accent)
        .child(`Lascia qui per spostarla in ${g.titolo}`)))
      .when(Boolean(g.nota), (el) => el.child(div().id(`vgo-${g.chiave || "senza"}`).px(18).pb(2).text_size(12).text_color(t.dim).child(g.nota)))
      .children(mostra.map((s) => this.riga(t, s, modo, cx)))
      .when(ferme.length > 0 && (vive.length > 0 || ferme.length > 2), (el) => el.child(h_flex().id(`vf-${g.chiave || "senza"}`).mx(8).px(10).py(5).gap(8).items_center().rounded(8).cursor_pointer()
        .hover((st) => st.bg(t.hover))
        .on_click((_e, cx) => {
          const prima = new Set(mostrate(g, this.aperti[g.chiave]).map((s) => s.sessionId));
          this.aperti[g.chiave] = !this.aperti[g.chiave];
          // le righe che il gruppo aperto mostra in più entrano una dopo l'altra (#5410)
          if (this.aperti[g.chiave]) this.entra(mostrate(g, true).map((s) => s.sessionId).filter((k) => !prima.has(k)), cx);
          cx.notify();
        })
        .child(svg(ICONA(this.aperti[g.chiave] ? "chevron-down" : "chevron-right")).size(12).text_color(t.dim))
        .child(div().text_size(12.5).text_color(t.muted).child(this.aperti[g.chiave] ? "Nascondi quelle in attesa" : `${ferme.length} in attesa di comando`))));
  }

  // null quando la sezione non serve (manca lo script dell'elenco). La sezione prende tutta l'altezza
  // della colonna sotto i pulsanti (12/11/2026): l'interruttore in cima, poi i gruppi che scorrono, poi
  // il riquadro dei gesti di "Altro" quando è aperto.
  render(cx) {
    if (!this.script) return null;
    const t = theme();
    impostaProgetti(shared("arturo.progetti"));
    const modo = this.modo();
    const lista = gruppi(this.vis(), modo);
    // lo spazio aperto, letto una volta sola: spaces() passa il confine con Herdr, e una chiamata per
    // gruppo faceva sforare il tempo del disegno ("This view could not be re-rendered", 12/11/2026)
    const aperto = slug(spaces().find((x) => x.active)?.name);
    // la riga accesa a sinistra: l'ultima del giro, altrimenti quella della scheda in primo piano
    const f = focused();
    const scheda = f?.terminal ? terminals().find((x) => x.address === f.terminal) ?? { address: f.terminal } : null;
    this.acceso = corrente(this.giroSt, sessioneDavanti(scheda, this.dati?.sessioni ?? [])?.sessionId ?? null, Date.now());
    let corpo;
    if (!this.dati) corpo = div().id("volta-vuoto").px(18).py(4).text_size(13).text_color(t.muted).child(this.errore ? "Non riesco a leggere le sessioni delle macchine." : "Leggo le sessioni delle macchine…");
    else if (!lista.length) corpo = div().id("volta-vuoto").px(18).py(4).text_size(13).text_color(t.muted).whitespace_normal().child("Nessuna sessione aperta. Nuova richiesta ne apre una; un progetto si apre da Apri un progetto.");
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
    const vecchio = this.dati && this.errore && this.dati.letto ? `Non riesco ad aggiornare: lettura delle ${String(this.dati.letto).slice(11, 16)}.` : null;
    const gesti = this.pannello(t);
    return v_flex().id("volta").flex_1().min_h(0).gap(6)
      .child(this.interruttore(t))
      // Il ponte del microfono (microfono.js): dove va la voce adesso. Un clic lo spegne o lo riaccende.
      .when(Boolean(rigaMicrofono(shared("arturo.microfono"))), (el) => { const r = rigaMicrofono(shared("arturo.microfono")); return el.child(h_flex().id("volta-microfono").px(18).gap(6).items_center().cursor_pointer()
        .on_click(() => setShared("arturo.microfono.spento", shared("arturo.microfono.spento") !== true))
        .child(svg("mods/arturo/microfono.svg").size(12).text_color(r.avviso ? t.blocked : t.accent))
        .child(div().text_size(12).text_color(r.avviso ? t.blocked : t.muted).child(r.testo))); })
      .when(Boolean(vecchio), (el) => el.child(div().id("volta-vecchio").px(18).text_size(12).text_color(t.blocked).child(vecchio)))
      .child(corpo)
      .when(Boolean(gesti), (el) => el.child(gesti.mb(10)));
  }
}
