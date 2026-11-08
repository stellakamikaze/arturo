// "Cosa posso chiedere": le richieste da imparare, come pulsanti. Le usa il benvenuto
// e la finestra che si apre da "Cosa posso chiedere" (in basso a sinistra e in alto).

import { div } from "gpui-kit";
import { v_flex, h_flex } from "gpui-base";
import { theme, props, closeOverlay, openOverlay } from "herdr";
import { SUGGERIMENTI, chiedi } from "./dati.js";
import { apriFinestra } from "./comuni.js";

export function apriSuggerimenti() {
  openOverlay({ mod: "arturo", props: { parte: "chiedi" }, kind: "dialog", width: 620 });
}

export function esegui(sug) {
  if (sug.dove === "apri") return apriFinestra();
  return chiedi(sug);
}

// Una richiesta come scheda cliccabile: titolo e una riga che dice cosa succede.
export function voce(t, sug, prima, dopo) {
  return v_flex().id(`s-${sug.id}`).p(14).gap(4).rounded(10).cursor_pointer()
    .border_1().border_color(prima ? t.accent : t.border).bg(prima ? t.selected : t.raised)
    .hover((s) => s.border_color(t.accent))
    .on_mouse_down("left", (_e, cx) => cx.stop_propagation())
    .on_click(() => { dopo?.(); esegui(sug); })
    .child(div().text_size(14).font_semibold().text_color(t.foreground).child(sug.titolo))
    .child(div().whitespace_normal().text_size(12.5).text_color(t.muted).child(sug.testo));
}

export class Chiedi {
  init(_p, cx) {
    this.handle = cx.focus_handle();
    cx.timer.after(150, () => this.handle.focus());
  }

  render() {
    const t = theme();
    const chiudi = () => closeOverlay(props().overlay);
    const coppie = [];
    for (let i = 0; i < SUGGERIMENTI.length; i += 2) coppie.push(SUGGERIMENTI.slice(i, i + 2));
    return v_flex().id("chiedi").track_focus(this.handle).w_full().p(24).gap(16).bg(t.popover)
      .on_key_down((e, cx) => { if (e.key === "escape") { chiudi(); cx.stop_propagation(); } })
      .child(v_flex().gap(4)
        .child(div().font_family("Arturo Archivo").text_size(19).text_color(t.foreground).child("Cosa posso chiedere"))
        .child(div().text_size(13).text_color(t.muted).child("Un clic e Claude parte. Puoi anche scrivergli queste cose con parole tue.")))
      .child(v_flex().gap(10).children(coppie.map((c) => h_flex().gap(10).children(c.map((s) =>
        div().flex_1().min_w(0).child(voce(t, s, false, chiudi)))))))
      .child(div().text_size(12).text_color(t.dim).child("Esc chiude"));
  }
}
