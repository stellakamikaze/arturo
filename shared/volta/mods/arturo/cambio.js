// Il dialogo che cambia il nome o il progetto di una sessione di Volta (#5292). Si apre da Rinomina e
// Cambia progetto del menu del tasto destro e col doppio clic sul titolo. È un'altra copia del mod: non
// ha l'elenco, quindi manda il cambio alla barra come comando (comandoCambio di sessioni.js, lo stesso
// di herdr-app do) e si chiude. Il progetto si sceglie fra quelli noti o si scrive.

import { div } from "gpui-kit";
import { v_flex, h_flex, InputState, Input } from "gpui-base";
import { theme, props, closeOverlay, openOverlay, run, shared } from "herdr";
import { titolo, nomeNuovo, progettoNuovo, nomeProgetto, filtraProgetti, comandoCambio, impostaProgetti } from "./sessioni.js";

// `noti`: i progetti fra cui scegliere (progettiNoti di sessioni.js), solo per cosa = "progetto".
export function apriCambio(s, cosa, noti = []) {
  openOverlay({ mod: "arturo", props: { parte: "cambio", sessione: s, cosa, noti }, kind: "dialog", width: 480 });
}

const TESTI = {
  nome: { titolo: "Rinomina la sessione", campo: "Il nome nuovo", fai: "Rinomina",
    nota: "Il nome resta: il titolo automatico non lo riscrive. Lascia vuoto per tornare al titolo automatico." },
  progetto: { titolo: "Cambia progetto", campo: "Scrivi o scegli un progetto", fai: "Sposta",
    nota: "La sessione passa nello spazio di quel progetto. L'handoff già scritto resta dov'è: il prossimo /fine scrive nel progetto nuovo." },
};

export class Cambio {
  init(_p, cx) {
    const p = props() ?? {};
    this.s = p.sessione ?? {};
    this.cosa = p.cosa === "progetto" ? "progetto" : "nome";
    this.noti = Array.isArray(p.noti) ? p.noti : [];
    this.at = -1;   // la voce scelta con le frecce fra i progetti noti; -1 = ciò che è scritto
    this.scritto = false;   // finché la persona non scrive, l'elenco mostra tutti i progetti e non solo quello di adesso
    const valore = this.cosa === "nome" ? titolo(this.s) : String(this.s.progetto ?? "");
    this.input = InputState.new({ value: valore, placeholder: TESTI[this.cosa].campo });
    if (valore) this.input.set_selected_range({ start: 0, end: valore.length });
    this.input.on("change", (_e, cx) => { this.at = -1; this.scritto = true; cx.notify(); });
    this.input.on("submit", () => this.conferma());
    this.input.focus();
    cx.timer.after(300, () => this.input.focus());
    this.handle = cx.focus_handle();
  }

  chiudi() { closeOverlay(props().overlay); }

  // Ciò che il dialogo manderebbe: il nome ripulito, o lo slug del progetto (scritto o scelto).
  valore() {
    if (this.cosa === "nome") return nomeNuovo(this.input.value());
    const scelte = this.scelte();
    return this.at >= 0 && scelte[this.at] ? scelte[this.at] : progettoNuovo(this.input.value());
  }

  scelte() { return this.cosa === "progetto" ? filtraProgetti(this.noti, this.scritto ? this.input.value() : "") : []; }

  pronto() { return this.cosa === "nome" || Boolean(this.valore()); }

  // Prima il comando, poi la chiusura: un overlay chiuso ferma il suo codice.
  conferma(valore = this.valore()) {
    if (this.cosa === "progetto" && !valore) return;
    run(comandoCambio(this.s, this.cosa, valore));
    this.chiudi();
  }

  render() {
    const t = theme();
    impostaProgetti(shared("arturo.progetti"));
    const x = TESTI[this.cosa];
    const scelte = this.scelte();
    const pronto = this.pronto();
    this.at = Math.min(this.at, scelte.length - 1);
    const voce = (p, i) => h_flex().id(`cp-${p}`).h(30).px(10).gap(8).items_center().rounded(6).cursor_pointer()
      .when(i === this.at, (el) => el.bg(t.selected)).hover((st) => st.bg(t.hover))
      .on_mouse_down("left", (_e, cx) => cx.stop_propagation())
      .on_click(() => this.conferma(p))
      .child(div().flex_1().truncate().text_size(13).text_color(t.foreground).child(nomeProgetto(p)))
      .child(div().text_size(12).text_color(t.dim).child(p));
    return v_flex().id("cambio").track_focus(this.handle).w_full().p(22).gap(14).bg(t.popover)
      .on_key_down((e, cx) => {
        if (e.key === "escape") this.chiudi();
        else if (e.key === "down" && scelte.length) this.at = (this.at + 1) % scelte.length;
        else if (e.key === "up" && scelte.length) this.at = (this.at + scelte.length - 1) % scelte.length;
        else return;
        cx.stop_propagation();
        cx.notify();
      })
      .child(v_flex().gap(3)
        .child(div().font_family("Arturo Archivo").text_size(18).text_color(t.foreground).child(x.titolo))
        .child(div().truncate().text_size(12.5).text_color(t.muted).child(titolo(this.s))))
      .child(h_flex().h(40).px(12).items_center().rounded(9).border_1().border_color(t.accent).bg(t.raised)
        .child(Input.new(this.input).flex_1().h_full().text_size(14).text_color(t.foreground)))
      .when(scelte.length > 0, (el) => el.child(v_flex().gap(1).children(scelte.map(voce))))
      .when(this.cosa === "progetto" && this.at < 0 && ![ "", this.input.value().trim() ].includes(progettoNuovo(this.input.value())), (el) =>
        el.child(div().text_size(12).text_color(t.dim).child(`Diventa: ${progettoNuovo(this.input.value())}`)))
      .child(div().whitespace_normal().text_size(12).text_color(t.dim).child(x.nota))
      .child(h_flex().gap(10).items_center()
        .child(div().id("cambio-fai").px(14).py(7).rounded(7).cursor_pointer().text_size(13).font_semibold()
          .bg(pronto ? t.accent : t.raised).text_color(pronto ? t.accent_foreground : t.dim)
          .when(pronto, (el) => el.hover((s) => s.opacity(0.9)))
          .on_mouse_down("left", (_e, cx) => cx.stop_propagation())
          .on_click(() => this.conferma())
          .child(x.fai))
        .child(div().text_size(12).text_color(t.dim).child(`Invio conferma · Esc chiude${scelte.length ? " · frecce per scegliere" : ""}`)));
  }
}
