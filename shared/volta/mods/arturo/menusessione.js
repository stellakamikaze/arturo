// Il menu del tasto destro su una sessione di Volta (#5291): Apri, Duplica, Fork, Sposta in un progetto
// (#5292, apre il dialogo di cambio.js) e Sposta su… (il popup di sposta.js), poi Rinomina e Contesto del
// progetto, poi Chiudi con /fine e i gesti di "Altro" (Anteprima, Riavvia, Elimina). Le voci le decide menu() di sessioni.js. Il menu è un popup,
// cioè un'altra copia del mod: non ha l'elenco né i suoi stati, quindi manda il gesto alla barra come
// comando ("arturo.volta-gesto-<verbo>-<chiave>", lo stesso di herdr-app do) e si chiude. La chiave è
// macchina:id (#5643): dopo uno spostamento il solo id sta su due macchine.

import { div } from "gpui-kit";
import { v_flex, h_flex } from "gpui-base";
import { theme, props, closeOverlay, openOverlay, run } from "herdr";
import { menu, titolo, GRUPPI_MENU, chiave as chiaveSessione } from "./sessioni.js";
import { vociMacchina } from "./comuni.js";
import { destinazioni } from "./sposta.js";

// "Sposta su…" c'è solo se Volta conosce un'altra macchina dove la sessione `s` può andare.
const conMacchina = (s) => (v) => v.verbo !== "sposta" || destinazioni(s, vociMacchina()).length > 0;

// Apre il menu al puntatore. false se la sessione non ha voci (una riga vecchia).
export function apriMenuSessione(s) {
  if (!menu(s).filter(conMacchina(s)).length) return false;
  openOverlay({ mod: "arturo", props: { parte: "sessione", sessione: s }, kind: "popup", width: 230 });
  return true;
}

// Il comando che esegue una voce: lo legge barra.js e lo passa a gestoId di volta.js.
export const comandoGesto = (s, v) => `arturo.volta-gesto-${v.verbo}-${chiaveSessione(s)}`;

export class MenuSessione {
  init(_p, cx) {
    this.s = props()?.sessione ?? {};
    this.voci = menu(this.s);
    this.voci = this.voci.filter(conMacchina(this.s));
    this.handle = cx.focus_handle();
    cx.timer.after(120, () => this.handle.focus());
  }

  chiudi() { closeOverlay(props().overlay); }

  // Prima il comando, poi la chiusura: un overlay chiuso ferma il suo codice.
  scegli(v) {
    run(comandoGesto(this.s, v));
    this.chiudi();
  }

  render() {
    const t = theme();
    const voce = (v) => h_flex().id(`ms-${v.verbo}`).h(30).px(10).items_center().rounded(6).cursor_pointer()
      .hover((st) => st.bg(t.hover))
      .on_mouse_down("left", (_e, cx) => cx.stop_propagation())
      .on_click(() => this.scegli(v))
      .child(div().flex_1().truncate().text_size(13).text_color(v.verbo === "rm" || v.verbo === "chiudi" ? t.blocked : t.foreground).child(v.testo));
    // Tre gruppi (GRUPPI_MENU di sessioni.js): copiare e spostare, nome e contesto, poi chiudere e i
    // gesti di "Altro".
    const primi = this.voci.filter((v) => GRUPPI_MENU[0].includes(v.verbo));
    const cambi = this.voci.filter((v) => GRUPPI_MENU[1].includes(v.verbo));
    const altri = this.voci.filter((v) => !primi.includes(v) && !cambi.includes(v));
    const gruppo = (l) => v_flex().gap(1).pt(4).border_t(1).border_color(t.border).children(l.map(voce));
    return v_flex().id("menu-sessione").track_focus(this.handle).w_full().p(8).gap(4).bg(t.popover)
      .on_key_down((e, cx) => { if (e.key === "escape") { this.chiudi(); cx.stop_propagation(); } })
      .child(div().px(10).pt(4).pb(2).truncate().text_size(12.5).text_color(t.muted).child(titolo(this.s)))
      .child(v_flex().gap(1).children(primi.map(voce)))
      .when(cambi.length > 0, (el) => el.child(gruppo(cambi)))
      .when(altri.length > 0, (el) => el.child(gruppo(altri)));
  }
}

// Il menu del tasto destro sull'intestazione di un progetto nella colonna (vista per progetto, 12/11/2026):
// Apri il progetto (lo stesso clic) e il suo contesto. Manda il comando alla barra e si chiude.
export function apriMenuProgetto(chiave, titoloProgetto) {
  if (!chiave) return false;
  openOverlay({ mod: "arturo", props: { parte: "menuprogetto", chiave, titolo: titoloProgetto ?? chiave }, kind: "popup", width: 230 });
  return true;
}

export const VOCI_PROGETTO = [{ verbo: "apri", testo: "Apri il progetto" }, { verbo: "contesto", testo: "Contesto del progetto" }];

// Il comando di una voce: "arturo.apri-<slug>" o "arturo.contesto-<slug>" (instrada di comandi.js).
export const comandoProgetto = (chiave, v) => `arturo.${v.verbo === "apri" ? "apri" : "contesto"}-${chiave}`;

export class MenuProgetto {
  init(_p, cx) {
    this.chiave = props()?.chiave ?? "";
    this.titolo = props()?.titolo ?? this.chiave;
    this.handle = cx.focus_handle();
    cx.timer.after(120, () => this.handle.focus());
  }

  chiudi() { closeOverlay(props().overlay); }

  render() {
    const t = theme();
    return v_flex().id("menu-progetto").track_focus(this.handle).w_full().p(8).gap(1).bg(t.popover)
      .on_key_down((e, cx) => { if (e.key === "escape") { this.chiudi(); cx.stop_propagation(); } })
      .child(div().px(10).pt(4).pb(2).truncate().text_size(12.5).text_color(t.muted).child(this.titolo))
      .children(VOCI_PROGETTO.map((v) => h_flex().id(`mp-${v.verbo}`).h(30).px(10).items_center().rounded(6).cursor_pointer()
        .hover((st) => st.bg(t.hover))
        .on_mouse_down("left", (_e, cx) => cx.stop_propagation())
        .on_click(() => { run(comandoProgetto(this.chiave, v)); this.chiudi(); })
        .child(div().flex_1().truncate().text_size(13).text_color(t.foreground).child(v.testo))));
  }
}
