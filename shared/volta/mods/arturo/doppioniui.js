// Il dialogo "Cerca doppioni" (#6188, Fase 5 del piano del 20/11/2026): la revisione delle coppie di progetti che
// sembrano lo stesso. Si apre dal pulsante della schermata Progetti (⌘T, casa.js) o con "arturo.doppioni".
// Ogni riga dice quale progetto entra in quale, perché sembrano doppioni e perché resta quello. Quattro gesti:
// - "Unisci" (21/11/2026: unire dalla lista, senza altre schermate): il clic è il sì. Arturo
//   prima conta (--prova, non scrive niente); se il conto è buono parte l'unione vera, che fa la barra come per il
//   pulsante Unisci di unisci.js. La riga dice a che punto è e com'è finita, e il dialogo resta aperto.
// - "Guarda l'unione": apre "Unisci a…" già sull'anteprima di quei due (unisci.js), per chi vuole i conti prima.
// - "Al contrario": resta l'altro progetto.
// - "Non sono doppioni": la coppia sparisce e non torna (doppioni-scartati.json, lo scrive la barra).
// Le coppie scartate valgono su tutte le macchine (volta_note.py porta il file, #6268). Per ripensarci: "Rivedi le
// scartate" mostra l'elenco, e "Rimetti fra i doppioni" riporta la coppia fra le probabili, anche lì dappertutto.
// Quali coppie, con che motivo e chi resta lo decide doppioni.js, senza Herdr. L'unione la scrive sempre la barra.

import { div, svg } from "gpui-kit";
import { v_flex, h_flex } from "gpui-base";
import { theme, props, closeOverlay, openOverlay, run, shared, setShared } from "herdr";
import { progettiMemoria, doppioniScartati, unione } from "./dati.js";
import { ICONA } from "./comuni.js";
import { SPAZIO, TESTO, RAGGIO, ICONA_MISURA } from "./misure.js";
import { doppioni, alContrario, dopoProva, dopoUnione, unioneInCorso } from "./doppioni.js";
import { comandoUnisciProva, comandoUnisciVai, comandoScartaDoppione, comandoRiprendiDoppione, impostaProgetti, nomeProgetto, slug } from "./sessioni.js";

// Ogni quanto il dialogo guarda l'esito dell'unione che la barra sta facendo.
const UNIONE_GUARDA_MS = 300;

// L'altezza dell'elenco: quattro coppie intere, le altre scorrono.
const ALTO = 420;

// Dopo uno scarto, quanto il pulsante "Non sono doppioni" resta sordo.
export const SCARTO_PAUSA_MS = 500;

// Uno solo aperto.
let aperto = null;
export function apriDoppioni(rivedi = false) {
  if (aperto) closeOverlay(aperto);
  // "arturo.doppioniscartate" apre il dialogo già sull'elenco delle scartate (prove senza tastiera, herdr-app do)
  setShared("arturo.doppioni.rivedi", Boolean(rivedi));
  aperto = openOverlay({ mod: "arturo", props: { parte: "doppioni" }, kind: "dialog", width: 640 });
  return true;
}

export class Doppioni {
  init(_p, cx) {
    this.coppie = null;      // null mentre cerca
    this.errore = null;
    this.quanti = 0;         // i progetti guardati
    this.memoria = [];       // i progetti di Arturo: servono a rifare le coppie dopo un ripensamento
    this.via = {};           // le coppie scartate, { chiave: quando }: valgono su tutte le macchine
    this.rivedi = shared("arturo.doppioni.rivedi") === true; // l'elenco delle coppie scartate al posto delle probabili
    this.titoli = {};        // slug → titolo, dalla memoria di Arturo
    this.ultimoScarto = 0;
    this.unioni = {};        // le unioni partite da qui, { chiave: { stato, testo, backup, da, perdente, vincitore } }
    this.at = 0;
    this.handle = cx.focus_handle();
    this.handle.focus();
    cx.timer.after(300, () => this.handle.focus());
    cx.timer.every(UNIONE_GUARDA_MS, (cx) => this.guardaUnione(cx));
    cx.spawn(async (cx) => {
      const [memoria, via] = await Promise.all([progettiMemoria(), doppioniScartati()]);
      if (!memoria) this.errore = "Arturo non ha dato l'elenco dei progetti. Riprova fra poco; se resta così, l'Arturo di questa Volta va aggiornato.";
      else {
        this.quanti = memoria.length;
        this.memoria = memoria;
        this.via = { ...via };
        // i titoli si leggono dalla stessa lista delle coppie: un progetto che la barra non mostra ha il suo qui
        this.titoli = Object.fromEntries(memoria.filter((m) => m?.slug && m.titolo).map((m) => [m.slug, String(m.titolo)]));
        this.coppie = doppioni(memoria, via);
      }
      cx.notify();
    });
  }

  chiudi() { closeOverlay(props().overlay); }

  // L'anteprima dell'unione la apre la barra: questo dialogo si chiude, e un dialogo chiuso ferma il suo codice.
  guarda(c) {
    // una coppia che si sta unendo o è già unita non ha più un'anteprima: Arturo direbbe "già unito"
    if (!c || (this.unioni[c.chiave] && this.unioni[c.chiave].stato !== "errore")) return;
    run(comandoUnisciProva(c.perdente, c.vincitore));
    this.chiudi();
  }

  // Unisci dalla riga: il clic è il sì della persona. Prima il conto di Arturo, che non scrive niente; se è
  // buono, l'unione vera la fa la barra (un dialogo chiuso ferma il suo codice, la barra no) e la riga ne
  // mostra l'esito. Una alla volta: mentre una gira, gli altri pulsanti Unisci non rispondono.
  unisci(c, cx) {
    if (!c || unioneInCorso(this.unioni) || this.unioni[c.chiave]?.stato === "fatto") return;
    const k = c.chiave, perdente = c.perdente, vincitore = c.vincitore;
    this.unioni[k] = { stato: "controllo", testo: "", backup: null, da: Date.now(), perdente, vincitore };
    cx.notify();
    cx.spawn(async (cx) => {
      const esito = dopoProva(await unione(perdente, vincitore, true));
      if (this.unioni[k]?.stato !== "controllo") return;
      if (esito.vai) {
        this.unioni[k] = { ...this.unioni[k], stato: "corso", da: Date.now() };
        run(comandoUnisciVai(perdente, vincitore));
      } else this.unioni[k] = { ...this.unioni[k], stato: "errore", testo: esito.testo };
      cx.notify();
    });
  }

  // L'esito dell'unione in corso, che la barra scrive in shared arturo.unione.
  guardaUnione(cx) {
    const k = Object.keys(this.unioni).find((x) => this.unioni[x].stato === "corso");
    if (!k) return;
    const e = dopoUnione(shared("arturo.unione"), this.unioni[k].da);
    if (!e || e.stato === "corso") return;
    this.unioni[k] = { ...this.unioni[k], ...e };
    cx.notify();
  }

  gira(c, cx) {
    if (this.unioni[c.chiave] && this.unioni[c.chiave].stato !== "errore") return;
    delete this.unioni[c.chiave];
    this.coppie = this.coppie.map((x) => (x.chiave === c.chiave ? alContrario(x) : x));
    cx.notify();
  }

  // Lo scarto toglie la riga, e la riga sotto sale sotto il puntatore: il secondo clic di un doppio clic
  // scarterebbe una coppia mai letta. Per SCARTO_PAUSA_MS dopo uno scarto il pulsante non risponde.
  scarta(c, cx) {
    if (Date.now() - this.ultimoScarto < SCARTO_PAUSA_MS) return;
    delete this.unioni[c.chiave];
    this.ultimoScarto = Date.now();
    run(comandoScartaDoppione(c.perdente, c.vincitore));
    this.coppie = this.coppie.filter((x) => x.chiave !== c.chiave);
    this.via[c.chiave] = Date.now();
    cx.notify();
  }

  // Ripensarci (#6268): la coppia `chiave` torna fra le probabili, qui subito e sulle altre macchine al giro delle
  // note. Le coppie si rifanno da capo: una coppia girata con "Al contrario" torna col verso di Volta. La stessa
  // pausa dello scarto: la riga sotto sale sotto il puntatore.
  riprendi(chiave, cx) {
    const adesso = Date.now();
    if (adesso - this.ultimoScarto < SCARTO_PAUSA_MS) return;
    this.ultimoScarto = adesso;
    const [a, b] = chiave.split("|");
    run(comandoRiprendiDoppione(a, b));
    delete this.via[chiave];
    this.coppie = doppioni(this.memoria, this.via);
    if (!Object.keys(this.via).length) this.rivedi = false;
    cx.notify();
  }

  // Fra le coppie probabili e l'elenco delle scartate.
  volta(cx) {
    this.rivedi = !this.rivedi;
    this.at = 0;
    cx.notify();
  }

  render() {
    const t = theme();
    impostaProgetti(shared("arturo.progetti"));
    // le scartate, dalla più recente; con l'elenco delle scartate aperto le probabili non si scelgono
    const scartate = Object.keys(this.via).sort((x, y) => this.via[y] - this.via[x] || (x < y ? -1 : 1));
    const rivedi = this.rivedi && scartate.length > 0;
    const l = rivedi ? [] : this.coppie ?? [];
    this.at = Math.max(0, Math.min(this.at, l.length - 1));

    const bottone = (id, testo, azione, forte, acceso = true) => div().id(id).px(SPAZIO.l).py(SPAZIO.s + 1).rounded(RAGGIO.controllo).text_size(TESTO.etichetta)
      .when(forte, (el) => el.font_semibold().bg(acceso ? t.accent : t.raised).text_color(acceso ? t.accent_foreground : t.dim))
      .when(!forte, (el) => el.border_1().border_color(t.border).text_color(t.foreground))
      .when(acceso, (el) => el.cursor_pointer().hover((s) => s.opacity(0.9)))
      .on_mouse_down("left", (_e, cx) => cx.stop_propagation())
      .on_click((_e, cx) => { if (acceso) azione(cx); })
      .child(testo);

    const frase = (etichetta, testo) => h_flex().gap(SPAZIO.m).items_start()
      .child(div().flex_none().w(64).text_size(TESTO.etichetta).text_color(t.muted).child(etichetta))
      .child(div().flex_1().min_w(0).whitespace_normal().text_size(TESTO.etichetta).text_color(t.foreground).child(testo));

    // Il nome di un progetto: il suo titolo, altrimenti quello ricavato dallo slug. Due doppioni hanno spesso lo
    // stesso titolo ("Eredi Zucca entra in Eredi Zucca"): allora valgono i due slug.
    const nome = (k) => this.titoli[k] || nomeProgetto(k);
    const nomi = (c) => (slug(nome(c.perdente)) === slug(nome(c.vincitore)) ? [c.perdente, c.vincitore] : [nome(c.perdente), nome(c.vincitore)]);

    // Il piede di una riga: i pulsanti, oppure a che punto è l'unione partita da qui. Un'unione non riuscita
    // dice perché e lascia i pulsanti, per riprovare o guardare i conti.
    const occupato = unioneInCorso(this.unioni);
    const detto = (testo, colore) => div().whitespace_normal().text_size(TESTO.etichetta).text_color(colore).child(testo);
    const piede = (c) => {
      const u = this.unioni[c.chiave];
      if (u?.stato === "controllo") return detto("Arturo controlla cosa passa…", t.muted).pt(SPAZIO.xs);
      if (u?.stato === "corso") return detto("Arturo copia tutto, poi unisce… Puoi chiudere: un avviso ti dice com'è andata.", t.muted).pt(SPAZIO.xs);
      if (u?.stato === "fatto") return v_flex().gap(SPAZIO.xs).pt(SPAZIO.xs)
        .child(detto(`Uniti: ${u.perdente} ora apre ${u.vincitore}.`, t.foreground))
        .when(Boolean(u.backup), (el) => el.child(detto(`Copia di prima: ${u.backup}`, t.muted)));
      return v_flex().gap(SPAZIO.m).pt(SPAZIO.xs)
        .when(u?.stato === "errore", (el) => el.child(detto(`Non uniti: ${u.testo}`, t.blocked)))
        .child(h_flex().gap(SPAZIO.m).items_center()
          .child(bottone(`dp-unisci-${c.chiave}`, "Unisci", (cx) => this.unisci(c, cx), true, !occupato))
          .child(bottone(`dp-guarda-${c.chiave}`, "Guarda l'unione", () => this.guarda(c), false))
          .child(bottone(`dp-gira-${c.chiave}`, "Al contrario", (cx) => this.gira(c, cx), false))
          .child(div().flex_1())
          .child(bottone(`dp-scarta-${c.chiave}`, "Non sono doppioni", (cx) => this.scarta(c, cx), false)));
    };

    const riga = (c, i) => v_flex().id(`dp-${c.chiave}`).p(SPAZIO.l).gap(SPAZIO.m).rounded(RAGGIO.riga).border_1()
      .border_color(i === this.at ? t.ring : t.border)
      .on_mouse_down("left", (_e, cx) => { if (this.at !== i) { this.at = i; cx.notify(); } })
      .child(h_flex().gap(SPAZIO.m).items_center()
        .child(svg(ICONA("folder")).size(ICONA_MISURA.piccola).flex_none().text_color(t.muted))
        .child(div().flex_none().max_w(230).truncate().text_size(TESTO.riga).text_color(t.foreground).child(nomi(c)[0]))
        .child(div().flex_none().text_size(TESTO.etichetta).text_color(t.muted).child("entra in"))
        .child(div().flex_1().min_w(0).truncate().font_semibold().text_size(TESTO.riga).text_color(t.foreground).child(nomi(c)[1])))
      // sotto i titoli, i due slug: sono i nomi che il motivo usa. Se la riga sopra li mostra già, basta quella.
      .when(nomi(c)[0] !== c.perdente || nomi(c)[1] !== c.vincitore, (el) => el
        .child(div().truncate().text_size(TESTO.nota).text_color(t.dim).child(`${c.perdente} entra in ${c.vincitore}`)))
      .child(frase("Perché", `${c.motivo}.`))
      .child(frase("Resta", c.perche ? `${c.vincitore}: ${c.perche}.` : `${c.vincitore}: l'hai scelto tu.`))
      .child(piede(c));

    // Una coppia scartata: i due progetti e il pulsante per ripensarci.
    const rigaScartata = (k) => {
      const [a, b] = k.split("|");
      const uguali = slug(nome(a)) === slug(nome(b));
      return h_flex().id(`dp-via-${k}`).p(SPAZIO.l).gap(SPAZIO.m).items_center().rounded(RAGGIO.riga).border_1().border_color(t.border)
        .child(svg(ICONA("folder")).size(ICONA_MISURA.piccola).flex_none().text_color(t.muted))
        .child(v_flex().flex_1().min_w(0).gap(SPAZIO.xs)
          .child(div().truncate().text_size(TESTO.riga).text_color(t.foreground).child(uguali ? `${a} e ${b}` : `${nome(a)} e ${nome(b)}`))
          .when(!uguali && (nome(a) !== a || nome(b) !== b), (el) => el
            .child(div().truncate().text_size(TESTO.nota).text_color(t.dim).child(`${a} e ${b}`))))
        .child(bottone(`dp-riprendi-${k}`, "Rimetti fra i doppioni", (cx) => this.riprendi(k, cx), false));
    };

    const conto = (n, uno, tanti) => `${n} ${n === 1 ? uno : tanti}`;
    const sotto = this.errore ? ""
      : this.coppie === null ? "Guardo nomi, titoli, righe di stato e repository dei tuoi progetti."
      : rivedi ? `${conto(scartate.length, "coppia scartata", "coppie scartate")}: non ${scartate.length === 1 ? "torna" : "tornano"} su nessuna delle tue macchine, finché non la rimetti fra i doppioni.`
      : `${conto(l.length, "coppia probabile", "coppie probabili")} su ${conto(this.quanti, "progetto", "progetti")}`
        + (scartate.length ? ` · ${conto(scartate.length, "coppia scartata", "coppie scartate")}, che non ${scartate.length === 1 ? "torna" : "tornano"}` : "");

    const corpo = this.errore ? div().whitespace_normal().text_size(TESTO.corpo).text_color(t.blocked).child(this.errore)
      : this.coppie === null ? div().text_size(TESTO.riga).text_color(t.muted).child("Cerco i doppioni…")
      : rivedi ? v_flex().id("dp-scartate").max_h(ALTO).overflow_y_scroll().gap(SPAZIO.m).children(scartate.map(rigaScartata))
      : !l.length ? v_flex().gap(SPAZIO.s)
        .child(div().text_size(TESTO.riga).text_color(t.foreground).child("Nessun doppione probabile"))
        .child(div().whitespace_normal().text_size(TESTO.etichetta).text_color(t.muted)
          .child("Se due progetti sono lo stesso e qui non compaiono, uniscili dal tasto destro su uno dei due: Unisci a…"))
      : v_flex().id("dp-elenco").max_h(ALTO).overflow_y_scroll().gap(SPAZIO.m).children(l.map(riga));

    return v_flex().id("doppioni").track_focus(this.handle).w_full().p(SPAZIO.xxl).gap(SPAZIO.xl).bg(t.popover)
      .on_key_down((e, cx) => {
        if (e.key === "escape") return this.chiudi();
        if (!l.length) return;
        if (e.key === "down") this.at = (this.at + 1) % l.length;
        else if (e.key === "up") this.at = (this.at + l.length - 1) % l.length;
        else if (e.key === "enter") return this.guarda(l[this.at]);
        else return;
        cx.stop_propagation();
        cx.notify();
      })
      .child(v_flex().gap(SPAZIO.s)
        .child(div().font_family("Arturo Archivo").text_size(TESTO.titolo).text_color(t.foreground).child("Cerca doppioni"))
        .child(div().whitespace_normal().text_size(TESTO.etichetta).text_color(t.muted).child(sotto)))
      .child(corpo)
      .child(h_flex().items_center()
        .child(div().flex_1().text_size(TESTO.etichetta).text_color(t.dim)
          .child(l.length ? "Unisci copia tutto, poi unisce · Invio mostra prima i conti · ↑↓ scegli · Esc chiude" : "Esc chiude"))
        .when(this.coppie !== null && scartate.length > 0, (el) => el
          .child(bottone("dp-rivedi", rivedi ? "Torna ai doppioni" : "Rivedi le scartate", (cx) => this.volta(cx), false))));
  }
}
