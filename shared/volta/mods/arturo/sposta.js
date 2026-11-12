// "Sposta su un'altra macchina" (Federico, 12/11/2026: la RAM di una macchina finisce, la sessione
// continua su un'altra). Il pulsante sta nella testata e vale per la sessione della scheda in primo
// piano, che volta.js scrive in shared arturo.volta.davanti. Il popup è un'altra copia del mod: elenca le
// altre macchine, chiede conferma col secondo clic e manda alla barra il comando
// "arturo.volta-sposta-<macchina>-<id>" (spostaId di volta.js). Lo spostamento vero sta in volta_sposta.py.

import { div, svg } from "gpui-kit";
import { h_flex, v_flex } from "gpui-base";
import { theme, props, closeOverlay, openOverlay, run } from "herdr";
import { vociMacchina } from "./comuni.js";
import { titolo } from "./sessioni.js";

export const ICONA_SPOSTA = "mods/arturo/sposta.svg";

// Il comando che sposta la sessione `id` su `macchina` ("qui" per questa).
export const comandoSposta = (macchina, id) => `arturo.volta-sposta-${macchina}-${id}`;

// Le macchine dove la sessione `s` può andare: tutte quelle di Volta, tranne la sua.
export const destinazioni = (s, voci) => (voci ?? []).filter((m) => m.host !== (s?.host ?? "qui"));

// Perché la sessione non si può spostare adesso, o null. Solo quelle in background: un'interattiva sta
// in un Terminale, e il suo processo non si ferma da qui. Una che lavora finirebbe a metà turno.
export function nonSiSposta(s) {
  if (!s) return "Nessuna sessione in questa scheda.";
  if (s.tipo !== "background") return "Si spostano solo le sessioni in background, non quelle aperte in un Terminale.";
  if (s.stato === "lavora") return "Sta lavorando: spostala a turno finito.";
  return null;
}

export function apriSposta(s) {
  openOverlay({ mod: "arturo", props: { parte: "sposta", sessione: s }, kind: "popup", width: 260 });
}

export class SceltaSposta {
  init(_p, cx) {
    this.s = props()?.sessione ?? null;
    this.scelta = null;
    this.handle = cx.focus_handle();
    cx.timer.after(120, () => this.handle.focus());
  }

  chiudi() { closeOverlay(props().overlay); }

  // Il primo clic sceglie, il secondo sposta. Prima il comando, poi la chiusura: un overlay chiuso
  // ferma il suo codice.
  scegli(m, cx) {
    if (this.scelta !== m.host) { this.scelta = m.host; return cx.notify(); }
    run(comandoSposta(m.host, this.s.id));
    this.chiudi();
  }

  render() {
    const t = theme();
    const no = nonSiSposta(this.s);
    const voci = destinazioni(this.s, vociMacchina());
    const voce = (m) => {
      const scelta = this.scelta === m.host;
      return h_flex().id(`sposta-${m.host}`).h(30).px(10).gap(8).items_center().rounded(6)
        .when(!no, (el) => el.cursor_pointer().hover((st) => st.bg(t.hover)).on_click((_e, cx) => this.scegli(m, cx)))
        .when(scelta, (el) => el.bg(t.selected))
        .on_mouse_down("left", (_e, cx) => cx.stop_propagation())
        .child(div().flex_1().truncate().text_size(13).text_color(no || m.giu ? t.dim : t.foreground).child(m.macchina))
        .when(scelta, (el) => el.child(div().flex_none().text_size(12).text_color(t.accent).child("Clic per spostare")))
        .when(!scelta && Boolean(m.giu), (el) => el.child(div().flex_none().text_size(11.5).text_color(t.dim).child("non risponde")));
    };
    return v_flex().id("scelta-sposta").track_focus(this.handle).w_full().p(8).gap(4).bg(t.popover)
      .on_key_down((e, cx) => { if (e.key === "escape") { this.chiudi(); cx.stop_propagation(); } })
      .child(h_flex().px(10).pt(4).gap(6).items_center()
        .child(svg(ICONA_SPOSTA).size(13).text_color(t.muted))
        .child(div().text_size(12.5).text_color(t.muted).child("Sposta su")))
      .child(div().px(10).pb(2).truncate().text_size(12.5).text_color(t.foreground).child(this.s ? titolo(this.s) : ""))
      .when(Boolean(no), (el) => el.child(div().px(10).pb(2).whitespace_normal().text_size(12).text_color(t.blocked).child(no)))
      .when(!voci.length, (el) => el.child(div().px(10).pb(2).text_size(12).text_color(t.dim).child("Volta non conosce altre macchine.")))
      .child(v_flex().gap(1).children(voci.map(voce)));
  }
}
