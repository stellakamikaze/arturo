// Pezzi d'interfaccia comuni alle parti.

import { div, svg } from "gpui-kit";
import { h_flex, v_flex } from "gpui-base";
import { theme, props, openOverlay, closeOverlay, window, exec, home, shared, setShared, notify, run } from "herdr";
import { cartellaNota } from "./nota.js";
import { altreMacchine, dove, nomeMacchina, inNascita } from "./dati.js";

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

// Il movimento della finestra (#5410): acceso salvo l'interruttore di Impostazioni (shared arturo.movimento,
// false = spento) o "Riduci movimento" del sistema (shared arturo.movimento.ridotto, lo legge volta.js).
// Transizioni e molle seguono già da sole "Riduci movimento"; loop e rotazioni no, per questo serve qui.
export const movimento = () => shared("arturo.movimento") !== false && shared("arturo.movimento.ridotto") !== true;

// Quale movimento ha il segno di uno stato: chi lavora gira, chi ti aspetta pulsa, gli altri stanno fermi.
// `chiave` è il colore del tema della frase di stato (working, blocked, …), come lo dà dettaglio().
export const motoDi = (chiave, aspetta = chiave === "blocked") => (chiave === "working" ? "gira" : aspetta ? "pulsa" : null);

// Il segno dello stato al posto del pallino fermo. "gira": una stella a quattro punte che fa un giro ogni
// 2,4 s, nello stesso posto del pallino (non sposta il testo). "pulsa": il pallino va e viene ogni 2 s,
// più lento della stella del marchio, che chiama. Senza movimento torna il pallino fermo.
export const GIRO_MS = 2400;

// L'interruttore: `acceso` true o false lo mette, null lo gira. Lo dice con un avviso breve.
export function giraMovimento(acceso = null) {
  const v = acceso === null ? shared("arturo.movimento") === false : Boolean(acceso);
  setShared("arturo.movimento", v);
  notify({ title: v ? "Movimento acceso" : "Movimento spento", body: v ? undefined : "Le sessioni tengono il pallino fermo.", level: "info", timeout: 3000 });
}

// Il menu di "Impostazioni" nel piede: è un popup, cioè un'altra copia del mod (parte "impostazioni").
export function apriImpostazioni() {
  openOverlay({ mod: "arturo", props: { parte: "impostazioni" }, kind: "popup", width: 270 });
}

// Il menu: l'interruttore del movimento, disegnato (la levetta scorre in 140 ms), poi le impostazioni
// dell'app. Il popup scrive lo shared e si chiude solo per le impostazioni dell'app.
export class Impostazioni {
  init(_p, cx) {
    this.handle = cx.focus_handle();
    cx.timer.after(120, () => this.handle.focus());
  }
  chiudi() { closeOverlay(props().overlay); }
  render() {
    const t = theme();
    const acceso = shared("arturo.movimento") !== false;
    const ridotto = shared("arturo.movimento.ridotto") === true;
    const leva = div().relative().w(30).h(18).flex_none().rounded_full().bg(acceso ? t.accent : t.border)
      .child(div().absolute().top(2).left(acceso ? 14 : 2).size(14).rounded_full().bg(acceso ? t.accent_foreground : t.muted)
        .transition("left", { duration: 140, easing: "ease-out" }));
    const voce = (id) => h_flex().id(id).px(10).gap(10).rounded(6).cursor_pointer().hover((st) => st.bg(t.hover))
      .on_mouse_down("left", (_e, cx) => cx.stop_propagation());
    return v_flex().id("impostazioni-menu").track_focus(this.handle).w_full().p(8).gap(4).bg(t.popover)
      .on_key_down((e, cx) => { if (e.key === "escape") { this.chiudi(); cx.stop_propagation(); } })
      .child(voce("imp-movimento").py(8).items_center()
        .on_click(() => giraMovimento())
        .child(v_flex().flex_1().min_w(0).gap(2)
          .child(div().text_size(13).text_color(t.foreground).child("Movimento"))
          .child(div().whitespace_normal().text_size(12).text_color(t.muted)
            .child(ridotto ? "Spento da Riduci movimento del Mac." : acceso ? "La stella gira su chi lavora, il pallino pulsa su chi ti aspetta." : "Pallini fermi, righe senza dissolvenza.")))
        .child(leva))
      .child(div().h(1).mx(6).bg(t.border))
      .child(voce("imp-app").h(30).items_center()
        .on_click(() => { run("app.settings"); this.chiudi(); })
        .child(div().flex_1().text_size(13).text_color(t.foreground).child("Impostazioni dell'app"))
        .child(div().text_size(12).text_color(t.dim).child(tasti().impostazioni)));
  }
}
export const PULSA = { from: 0.45, to: 1, period: 2000 };
export function segno(colore, moto = null, d = 8) {
  if (!moto || !movimento()) return punto(colore, d);
  if (moto === "pulsa") return punto(colore, d).loop("opacity", PULSA);
  return div().size(d).flex_none().flex().items_center().justify_center()
    .child(svg("mods/arturo/stella-lavora.svg").size(d + 4).flex_none().text_color(colore).spin(GIRO_MS));
}

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

// "Nasce su": la macchina dove nascono Nuova richiesta e Apri un progetto (#5172 passo 4), nella barra,
// nella testata e nella finestra Apri. Una pastiglia sola, che dice la macchina scelta e apre il
// selettore (SceltaMacchina): la fila con una voce per macchina occupava due righe (#5368). Niente
// pastiglia se Volta non conosce altre macchine con Claude. Durante una nascita dice dove sta nascendo.
export const vociMacchina = () => [{ host: "qui", macchina: "questa macchina", giu: false }, ...altreMacchine()];

export function nasceSu(t) {
  const voci = vociMacchina();
  if (voci.length < 2) return null;
  const d = dove();
  const nascita = inNascita();
  const scelta = voci.find((m) => m.host === d) ?? voci[0];
  return h_flex().child(h_flex().id("dove-scelta").h(26).px(8).gap(6).items_center().rounded(6).cursor_pointer().text_size(12.5)
    .border_1().border_color(t.border).hover((s) => s.bg(t.hover))
    .on_mouse_down("left", (_e, cx) => cx.stop_propagation())
    .on_click(() => apriSceltaMacchina())
    .child(div().id("dove-etichetta").text_color(nascita ? t.working : t.dim).child(nascita ? `Nasce su ${nomeMacchina(nascita)}…` : "Nasce su"))
    .when(!nascita, (el) => el.child(div().truncate().text_color(scelta.giu ? t.dim : t.foreground).child(scelta.macchina)))
    .child(svg(ICONA("chevron-down")).size(12).text_color(t.muted)));
}

// Il selettore di "Nasce su": un popup al puntatore, come il menu di una sessione (menusessione.js).
export function apriSceltaMacchina() {
  openOverlay({ mod: "arturo", props: { parte: "macchina" }, kind: "popup", width: 230 });
}

// Il popup è un'altra copia del mod: legge le macchine e la scelta dagli stessi shared della barra, scrive
// arturo.dove e si chiude. Una macchina giù resta in elenco, in grigio: la nascita dirà perché non parte.
export class SceltaMacchina {
  init(_p, cx) {
    this.handle = cx.focus_handle();
    cx.timer.after(120, () => this.handle.focus());
  }

  chiudi() { closeOverlay(props().overlay); }

  // Prima la scrittura, poi la chiusura: un overlay chiuso ferma il suo codice.
  scegli(host) {
    setShared("arturo.dove", host);
    this.chiudi();
  }

  render() {
    const t = theme();
    const d = dove();
    const voce = (m) => h_flex().id(`macchina-${m.host}`).h(30).px(10).gap(8).items_center().rounded(6).cursor_pointer()
      .hover((st) => st.bg(t.hover))
      .on_mouse_down("left", (_e, cx) => cx.stop_propagation())
      .on_click(() => this.scegli(m.host))
      .child(div().w(14).flex_none().when(d === m.host, (el) => el.child(svg(ICONA("check")).size(13).text_color(t.accent))))
      .child(div().flex_1().truncate().text_size(13).text_color(m.giu ? t.dim : t.foreground).child(m.macchina))
      .when(Boolean(m.giu), (el) => el.child(div().flex_none().text_size(11.5).text_color(t.dim).child("non risponde")));
    return v_flex().id("scelta-macchina").track_focus(this.handle).w_full().p(8).gap(4).bg(t.popover)
      .on_key_down((e, cx) => { if (e.key === "escape") { this.chiudi(); cx.stop_propagation(); } })
      .child(div().px(10).pt(4).pb(2).text_size(12.5).text_color(t.muted).child("Nasce su"))
      .child(v_flex().gap(1).children(vociMacchina().map(voce)));
  }
}

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
