// La finestra "Apri un progetto": le cartelle della base dei progetti, dalla più recente.
// Scrivi per filtrare, frecce e Invio per aprire, Esc per chiudere.

import { div, svg } from "gpui-kit";
import { v_flex, h_flex, InputState, Input } from "gpui-base";
import { theme, props, closeOverlay } from "herdr";
import { cartelle, apri, spazio, frase, bello } from "./dati.js";
import { ICONA, punto, colore } from "./comuni.js";

const MAX = 10;

export class Apri {
  init(_p, cx) {
    this.filtro = "";
    this.at = 0;
    this.lista = null;
    this.input = InputState.new({ placeholder: "Cerca un progetto" });
    this.input.on("change", (_e, cx) => { this.filtro = this.input.value(); this.at = 0; cx.notify(); });
    this.input.on("submit", () => this.vai(this.righe()[this.at]));
    this.input.focus();
    cx.timer.after(300, () => this.input.focus());
    this.handle = cx.focus_handle();
    cx.spawn(async (cx) => { this.lista = await cartelle(); cx.notify(); });
  }

  chiudi() { closeOverlay(props().overlay); }

  righe() {
    const f = this.filtro.trim().toLowerCase();
    const l = this.lista ?? [];
    const presi = f ? [...l.filter((d) => d.toLowerCase().startsWith(f)), ...l.filter((d) => !d.toLowerCase().startsWith(f) && d.toLowerCase().includes(f))] : l;
    return presi.slice(0, MAX);
  }

  vai(nome) {
    if (!nome) return;
    this.chiudi();
    apri(nome);
  }

  render() {
    const t = theme();
    const righe = this.righe();
    this.at = Math.max(0, Math.min(this.at, righe.length - 1));
    const riga = (nome, i) => {
      const s = spazio(nome);
      const f = s?.status ? frase(s.status) : null;
      return h_flex().id(`a-${nome}`).h(38).px(12).gap(11).items_center().rounded(8).cursor_pointer()
        .when(i === this.at, (el) => el.bg(t.selected)).hover((st) => st.bg(t.hover))
        .on_click(() => this.vai(nome))
        .child(punto(f ? colore(t, f.colore) : s ? t.idle : t.border))
        .child(div().flex_1().truncate().text_size(14).text_color(t.foreground).child(bello(nome)))
        .child(div().text_size(12).text_color(f ? colore(t, f.colore) : t.muted).child(f ? f.testo : s ? "Conversazione aperta" : ""));
    };
    return v_flex().id("apri").track_focus(this.handle).w_full().p(20).gap(12).bg(t.popover)
      .on_key_down((e, cx) => {
        if (e.key === "escape") return this.chiudi();
        if (e.key === "down") this.at = (this.at + 1) % Math.max(1, righe.length);
        else if (e.key === "up") this.at = (this.at + righe.length - 1) % Math.max(1, righe.length);
        else return;
        cx.stop_propagation();
        cx.notify();
      })
      .child(div().font_family("Arturo Archivo").text_size(18).text_color(t.foreground).child("Apri un progetto"))
      .child(h_flex().h(40).px(12).gap(9).items_center().rounded(9).border_1().border_color(t.accent).bg(t.raised)
        .child(svg(ICONA("search")).size(15).text_color(t.muted))
        .child(Input.new(this.input).flex_1().h_full().text_size(14).text_color(t.foreground)))
      .child(this.lista === null
        ? div().px(12).py(8).text_size(13).text_color(t.muted).child("Cerco i progetti…")
        : righe.length
          ? v_flex().gap(2).children(righe.map(riga))
          : div().px(12).py(8).text_size(13).text_color(t.muted).whitespace_normal().child(this.filtro ? "Nessun progetto con questo nome." : "Non ci sono ancora progetti. Chiedi a Claude di crearne uno con Nuova richiesta."))
      .child(div().px(2).text_size(12).text_color(t.dim).child("Invio apre · Esc chiude"));
  }
}
