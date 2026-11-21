// Il dialogo "Cerca doppioni" (#6188, Fase 5 del piano del 20/11/2026): la revisione delle coppie di progetti che
// sembrano lo stesso. Si apre dal pulsante della schermata Progetti (⌘T, casa.js) o con "arturo.doppioni".
// Ogni riga dice quale progetto entra in quale, perché sembrano doppioni e perché resta quello. Tre gesti:
// - "Guarda l'unione": apre "Unisci a…" già sull'anteprima di quei due (unisci.js). Lì niente è ancora scritto:
//   l'unione vera parte solo dal suo pulsante Unisci.
// - "Al contrario": resta l'altro progetto.
// - "Non sono doppioni": la coppia sparisce e non torna (doppioni-scartati.json, lo scrive la barra).
// Quali coppie, con che motivo e chi resta lo decide doppioni.js, senza Herdr. Qui non si unisce niente.

import { div, svg } from "gpui-kit";
import { v_flex, h_flex } from "gpui-base";
import { theme, props, closeOverlay, openOverlay, run, shared } from "herdr";
import { progettiMemoria, doppioniScartati } from "./dati.js";
import { ICONA } from "./comuni.js";
import { SPAZIO, TESTO, RAGGIO, ICONA_MISURA } from "./misure.js";
import { doppioni, alContrario } from "./doppioni.js";
import { comandoUnisciProva, comandoScartaDoppione, impostaProgetti, nomeProgetto, slug } from "./sessioni.js";

// L'altezza dell'elenco: quattro coppie intere, le altre scorrono.
const ALTO = 420;

// Dopo uno scarto, quanto il pulsante "Non sono doppioni" resta sordo.
export const SCARTO_PAUSA_MS = 500;

// Uno solo aperto.
let aperto = null;
export function apriDoppioni() {
  if (aperto) closeOverlay(aperto);
  aperto = openOverlay({ mod: "arturo", props: { parte: "doppioni" }, kind: "dialog", width: 640 });
  return true;
}

export class Doppioni {
  init(_p, cx) {
    this.coppie = null;      // null mentre cerca
    this.errore = null;
    this.quanti = 0;         // i progetti guardati
    this.scartate = 0;       // le coppie già scartate, su questa macchina
    this.titoli = {};        // slug → titolo, dalla memoria di Arturo
    this.ultimoScarto = 0;
    this.at = 0;
    this.handle = cx.focus_handle();
    this.handle.focus();
    cx.timer.after(300, () => this.handle.focus());
    cx.spawn(async (cx) => {
      const [memoria, via] = await Promise.all([progettiMemoria(), doppioniScartati()]);
      if (!memoria) this.errore = "Arturo non ha dato l'elenco dei progetti. Riprova fra poco; se resta così, l'Arturo di questa Volta va aggiornato.";
      else {
        this.quanti = memoria.length;
        this.scartate = Object.keys(via).length;
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
    if (!c) return;
    run(comandoUnisciProva(c.perdente, c.vincitore));
    this.chiudi();
  }

  gira(c, cx) {
    this.coppie = this.coppie.map((x) => (x.chiave === c.chiave ? alContrario(x) : x));
    cx.notify();
  }

  // Lo scarto toglie la riga, e la riga sotto sale sotto il puntatore: il secondo clic di un doppio clic
  // scarterebbe una coppia mai letta. Per SCARTO_PAUSA_MS dopo uno scarto il pulsante non risponde.
  scarta(c, cx) {
    if (Date.now() - this.ultimoScarto < SCARTO_PAUSA_MS) return;
    this.ultimoScarto = Date.now();
    run(comandoScartaDoppione(c.perdente, c.vincitore));
    this.coppie = this.coppie.filter((x) => x.chiave !== c.chiave);
    this.scartate += 1;
    cx.notify();
  }

  render() {
    const t = theme();
    impostaProgetti(shared("arturo.progetti"));
    const l = this.coppie ?? [];
    this.at = Math.max(0, Math.min(this.at, l.length - 1));

    const bottone = (id, testo, azione, forte) => div().id(id).px(SPAZIO.l).py(SPAZIO.s + 1).rounded(RAGGIO.controllo).text_size(TESTO.etichetta).cursor_pointer()
      .when(forte, (el) => el.font_semibold().bg(t.accent).text_color(t.accent_foreground))
      .when(!forte, (el) => el.border_1().border_color(t.border).text_color(t.foreground))
      .hover((s) => s.opacity(0.9))
      .on_mouse_down("left", (_e, cx) => cx.stop_propagation())
      .on_click((_e, cx) => azione(cx))
      .child(testo);

    const frase = (etichetta, testo) => h_flex().gap(SPAZIO.m).items_start()
      .child(div().flex_none().w(64).text_size(TESTO.etichetta).text_color(t.muted).child(etichetta))
      .child(div().flex_1().min_w(0).whitespace_normal().text_size(TESTO.etichetta).text_color(t.foreground).child(testo));

    // Il nome di un progetto: il suo titolo, altrimenti quello ricavato dallo slug. Due doppioni hanno spesso lo
    // stesso titolo ("Eredi Zucca entra in Eredi Zucca"): allora valgono i due slug.
    const nome = (k) => this.titoli[k] || nomeProgetto(k);
    const nomi = (c) => (slug(nome(c.perdente)) === slug(nome(c.vincitore)) ? [c.perdente, c.vincitore] : [nome(c.perdente), nome(c.vincitore)]);

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
      .child(h_flex().gap(SPAZIO.m).items_center().pt(SPAZIO.xs)
        .child(bottone(`dp-guarda-${c.chiave}`, "Guarda l'unione", () => this.guarda(c), true))
        .child(bottone(`dp-gira-${c.chiave}`, "Al contrario", (cx) => this.gira(c, cx), false))
        .child(div().flex_1())
        .child(bottone(`dp-scarta-${c.chiave}`, "Non sono doppioni", (cx) => this.scarta(c, cx), false)));

    const conto = (n, uno, tanti) => `${n} ${n === 1 ? uno : tanti}`;
    const sotto = this.errore ? ""
      : this.coppie === null ? "Guardo nomi, titoli, righe di stato e repository dei tuoi progetti."
      : `${conto(l.length, "coppia probabile", "coppie probabili")} su ${conto(this.quanti, "progetto", "progetti")}`
        + (this.scartate ? ` · ${conto(this.scartate, "coppia scartata", "coppie scartate")}, che non ${this.scartate === 1 ? "torna" : "tornano"}` : "");

    const corpo = this.errore ? div().whitespace_normal().text_size(TESTO.corpo).text_color(t.blocked).child(this.errore)
      : this.coppie === null ? div().text_size(TESTO.riga).text_color(t.muted).child("Cerco i doppioni…")
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
          .child(l.length ? "Invio mostra l'unione, senza scrivere niente · ↑↓ scegli · Esc chiude" : "Esc chiude")));
  }
}
