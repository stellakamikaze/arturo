// Pezzi d'interfaccia comuni alle parti.

import { div, svg } from "gpui-kit";
import { h_flex } from "gpui-base";
import { theme, openOverlay } from "herdr";

export const ICONA = (nome) => `mods/workspace-chrome/${nome}.svg`;

// Un pallino di stato disegnato, non un carattere.
export const punto = (colore, d = 8) => div().size(d).flex_none().rounded_full().bg(colore);

// Un pulsante con icona e testo. `forte`: il pulsante principale della barra.
export function pulsante(id, icona, testo, azione, forte = false) {
  const t = theme();
  return h_flex().id(id).h(36).px(12).gap(9).items_center().rounded(8).cursor_pointer()
    .on_mouse_down("left", (_e, cx) => cx.stop_propagation())
    .when(forte, (el) => el.bg(t.accent).text_color(t.accent_foreground).font_semibold().hover((s) => s.opacity(0.9)))
    .when(!forte, (el) => el.border_1().border_color(t.border).text_color(t.foreground).hover((s) => s.bg(t.hover)))
    .on_click(azione)
    .child(svg(ICONA(icona)).size(15))
    .child(div().text_size(13.5).child(testo));
}

export const colore = (t, nome) => t[nome] ?? nome;

// La finestra "Apri un progetto".
export function apriFinestra() {
  openOverlay({ mod: "arturo", props: { parte: "apri" }, kind: "dialog", width: 560 });
}
