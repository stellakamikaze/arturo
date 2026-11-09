// La finestra "La settimana": i progetti con todo scaduti, quelli che aspettano te e quelli fermi
// da più di sette giorni. "Fai il punto" apre Claude sul progetto con /inizio.
// Si apre dal piede a sinistra, e da sola alla prima apertura di ogni settimana (barra.js).

import { div, svg } from "gpui-kit";
import { h_flex, v_flex } from "gpui-base";
import { theme, props, closeOverlay, openOverlay } from "herdr";
import { todo, apri, bello, chiave } from "./dati.js";
import { ICONA } from "./comuni.js";
import { revisione, FERMO_GG } from "./settimana.js";

const MOSTRA = 5;

const LISTE = [
  { tipo: "scaduti", titolo: "Con todo scaduti", vuoto: "Nessun todo scaduto." },
  { tipo: "te", titolo: "Aspettano te", vuoto: "Nessun progetto aspetta una tua risposta." },
  { tipo: "fermi", titolo: `Fermi da più di ${FERMO_GG} giorni`, vuoto: "Nessun progetto fermo." },
];

export function apriRevisione() {
  openOverlay({ mod: "arturo", props: { parte: "settimana" }, kind: "dialog", width: 640, height: 0.82 });
}

export class Settimana {
  init(_p, cx) {
    this.liste = null;
    this.errore = null;
    this.tutti = {};
    this.handle = cx.focus_handle();
    cx.timer.after(150, () => this.handle.focus());
    cx.spawn(async (cx) => {
      const r = await todo(["--json"]);
      if (r.ok) this.liste = revisione(r.json);
      else this.errore = r.errore;
      cx.notify();
    });
  }

  chiudi() { closeOverlay(props().overlay); }

  riga(t, v) {
    const k = chiave(v.progetto);
    return h_flex().id(`r-${k}`).px(12).py(9).gap(12).items_center().rounded(8).hover((s) => s.bg(t.hover))
      .child(v_flex().flex_1().min_w(0).gap(2)
        .child(div().truncate().text_size(14).text_color(t.foreground).child(bello(v.progetto)))
        .child(div().whitespace_normal().text_size(12.5).text_color(t.muted).child(v.motivo)))
      .child(div().id(`r-punto-${k}`).flex_none().px(10).py(5).rounded(6).cursor_pointer()
        .text_size(12.5).text_color(t.accent).border_1().border_color(t.border)
        .hover((s) => s.bg(t.selected))
        .on_mouse_down("left", (_e, cx) => cx.stop_propagation())
        // prima apre, poi chiude: un overlay chiuso ferma il suo codice al primo await
        .on_click(async () => { try { await apri(k); } finally { this.chiudi(); } })
        .child("Fai il punto"));
  }

  lista(t, { tipo, titolo, vuoto }) {
    const l = this.liste[tipo];
    const aperta = this.tutti[tipo];
    const mostrati = aperta ? l : l.slice(0, MOSTRA);
    return v_flex().gap(2)
      .child(h_flex().px(12).pb(2).gap(8).items_center()
        .child(div().flex_1().text_size(13).font_semibold().text_color(tipo === "scaduti" && l.length ? t.blocked : t.foreground).child(titolo))
        .child(div().text_size(12).text_color(t.muted).child(String(l.length))))
      .when(!l.length, (el) => el.child(div().px(12).py(4).text_size(12.5).text_color(t.dim).child(vuoto)))
      .children(mostrati.map((v) => this.riga(t, v)))
      .when(l.length > MOSTRA, (el) => el.child(h_flex().id(`r-altri-${tipo}`).px(12).py(6).gap(6).items_center().rounded(6).cursor_pointer()
        .text_size(12.5).text_color(t.muted).hover((s) => s.bg(t.hover).text_color(t.foreground))
        .on_mouse_down("left", (_e, cx) => cx.stop_propagation())
        .on_click((_e, cx) => { this.tutti[tipo] = !aperta; cx.notify(); })
        .child(svg(ICONA(aperta ? "chevron-down" : "chevron-right")).size(13))
        .child(aperta ? "Mostra meno" : `Mostra gli altri ${l.length - MOSTRA}`)));
  }

  render() {
    const t = theme();
    let corpo;
    if (this.errore) corpo = div().px(12).text_size(13).text_color(t.muted).whitespace_normal().child(`Non riesco a leggere i todo: ${this.errore}`);
    else if (!this.liste) corpo = div().px(12).text_size(13).text_color(t.muted).child("Leggo i progetti…");
    else if (!LISTE.some((x) => this.liste[x.tipo].length)) corpo = div().px(12).text_size(13).text_color(t.muted).child("Tutto in ordine: niente da guardare questa settimana.");
    else corpo = v_flex().gap(18).children(LISTE.map((x) => this.lista(t, x)));
    return v_flex().id("settimana").track_focus(this.handle).size_full().p(24).gap(14).bg(t.popover)
      .on_key_down((e, cx) => { if (e.key === "escape") { this.chiudi(); cx.stop_propagation(); } })
      .child(v_flex().gap(4)
        .child(div().font_family("Arturo Archivo").text_size(19).text_color(t.foreground).child("La settimana"))
        .child(div().whitespace_normal().text_size(13).text_color(t.muted)
          .child("I progetti da guardare. Fai il punto apre Claude sul progetto e ti dice da dove ripartire.")))
      .child(v_flex().id("settimana-elenco").flex_1().min_h(0).overflow_y_scrollbar().child(corpo))
      .child(div().text_size(12).text_color(t.dim).child("Esc chiude"));
  }
}
