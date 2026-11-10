// Pezzi d'interfaccia comuni alle parti.

import { div, svg } from "gpui-kit";
import { h_flex } from "gpui-base";
import { theme, openOverlay, window, exec, home } from "herdr";
import { cartellaNota } from "./nota.js";

export const ICONA = (nome) => `mods/workspace-chrome/${nome}.svg`;

// I tasti come li scrivono i testi: sui Mac quelli di keys.json, altrove quelli di keys-ctrl.json e di
// Herdr (Alt+↓ per la sessione che aspetta), perché su Windows ⌘ sarebbe il tasto Windows.
export function tasti() {
  return window()?.platform === "macos"
    ? { apri: "⌘O", prossima: "⌘⇧↓", impostazioni: "⌘,", nota: "⌘⇧N", elenco: "⌘⇧E" }
    : { apri: "Ctrl+Shift+A", prossima: "Alt+↓", impostazioni: "Ctrl+,", nota: "Ctrl+Shift+M", elenco: "Ctrl+Shift+I" };
}

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

// ⌘⇧N: prima lo screenshot della finestra com'è, poi il velo per scegliere il punto (notaui.js). Con `apri`
// (l'id di una nota, dall'elenco) il velo si apre già sulla scheda di quella nota.
export async function apriNota(apri = null) {
  const cartella = cartellaNota(home());
  try {
    await exec("sh", ["-c", 'mkdir -p "$1" && h=$(command -v herdr-app || echo "$HOME/.local/bin/herdr-app") && "$h" shot "$1/finestra.png"', "sh", cartella], {});
  } catch { /* senza screenshot la nota parte lo stesso */ }
  openOverlay({ mod: "arturo", props: { parte: "nota", cartella, apri }, kind: "dialog", width: 1, height: 1, frame: "none", modal: true });
}

// ⌘⇧E, o il conteggio nella barra di stato: l'elenco delle note del progetto (noteui.js).
export function apriElenco() {
  openOverlay({ mod: "arturo", props: { parte: "note" }, kind: "dialog", width: 660, height: 0.78 });
}
