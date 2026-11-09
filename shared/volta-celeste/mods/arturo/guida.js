// La guida di Arturo in Herdr: quattro passi, con lo schema della finestra e la zona di cui si parla.
// Si apre da sola al primo avvio (shared "arturo.guida") e si riapre da "Guida" in basso a sinistra.
// Frecce o Invio per andare avanti, Esc per chiudere.

import { div, image } from "gpui-kit";
import { v_flex, h_flex } from "gpui-base";
import { theme, props, closeOverlay, openOverlay, setShared } from "herdr";
import { punto } from "./comuni.js";

// `passo` (da 0) apre la guida a quel punto: "arturo.guida3" dai tasti o da herdr-app do.
export function apriGuida(passo = 0) {
  openOverlay({ mod: "arturo", props: { parte: "guida", passo }, kind: "dialog", width: 680 });
}

const PASSI = [
  {
    zona: null,
    titolo: "Arturo ha una finestra sua",
    righe: [
      "Scrivi a Claude come in una chat. Le regole, la memoria e i todo sono quelli di sempre.",
    ],
  },
  {
    zona: "progetti",
    titolo: "Più progetti alla volta",
    righe: [
      "Apri un progetto e passa al prossimo: Claude lavora su tutti insieme.",
      "Quando uno ha bisogno di te, senti un suono e il suo pallino diventa arancio. ⌘⇧↓ ti porta lì.",
    ],
    legenda: true,
  },
  {
    zona: "centro",
    titolo: "Chiudi pure la finestra",
    righe: [
      "Le conversazioni continuano anche a finestra chiusa, e le ritrovi dove le avevi lasciate.",
      "Altra conversazione, in alto, ne apre una seconda sullo stesso progetto.",
    ],
  },
  {
    zona: "dafare",
    titolo: "Da fare, accanto a Claude",
    righe: [
      "I todo del progetto, divisi fra te e Claude. Spunta quelli fatti; Lavoraci fa partire Claude da lì e segna il todo in corso, finché /fine lo chiude; Altro cambia chi lo fa e quando. Con ⌘⇧N lasci a Claude una nota su un punto della finestra.",
      "La settimana, in basso a sinistra, raccoglie i progetti da guardare. Si apre da sola alla prima apertura di ogni settimana.",
      "Cosa posso chiedere ti suggerisce le richieste. A fine giornata scrivi /fine.",
    ],
  },
];

// Lo schema della finestra: tre colonne, la zona del passo accesa.
function schema(t, zona) {
  const acceso = (nome) => zona === nome;
  const blocco = (nome, w) => div().h_full().rounded(5).border_1()
    .when(w, (el) => el.w(w)).when(!w, (el) => el.flex_1())
    .border_color(acceso(nome) ? t.accent : t.border)
    .bg(acceso(nome) ? t.selected : t.raised);
  const righe = (n, chiaro, largo) => v_flex().gap(5).p(7).children(Array.from({ length: n }, (_, i) =>
    div().h(5).rounded(3).w(i % 2 ? largo * 0.7 : largo).bg(chiaro ? t.muted : t.border)));
  if (!zona) {
    return v_flex().w(220).h(132).flex_none().items_center().justify_center().gap(10).rounded(9).bg(t.canvas).border_1().border_color(t.border)
      .child(image("mods/arturo/stella.svg").size(54))
      .child(div().font_family("Arturo Archivo").text_size(15).text_color(t.foreground).child("Arturo"));
  }
  return h_flex().w(220).h(132).flex_none().p(8).gap(6).rounded(9).bg(t.canvas).border_1().border_color(t.border)
    .child(blocco("progetti", 54).child(righe(5, acceso("progetti"), 36)))
    .child(blocco("centro").child(righe(3, acceso("centro"), 56)))
    .child(blocco("dafare", 50).child(righe(4, acceso("dafare"), 32)));
}

export class Guida {
  init(_p, cx) {
    this.passo = Math.max(0, Math.min(PASSI.length - 1, Number(props()?.passo) || 0));
    this.handle = cx.focus_handle();
    cx.timer.after(150, () => this.handle.focus());
    setShared("arturo.guida.aperta", true);
  }

  chiudi() { closeOverlay(props().overlay); }

  close() { setShared("arturo.guida.aperta", false); }

  render() {
    const t = theme();
    const p = PASSI[this.passo];
    const ultimo = this.passo === PASSI.length - 1;
    const avanti = (cx) => { if (ultimo) return this.chiudi(); this.passo++; cx.notify(); };
    const indietro = (cx) => { if (this.passo > 0) { this.passo--; cx.notify(); } };
    const tasto = (id, testo, forte, azione) => div().id(id).h(36).px(16).flex().items_center().rounded(8).cursor_pointer()
      .text_size(13.5)
      .when(forte, (el) => el.bg(t.accent).text_color(t.accent_foreground).font_semibold().hover((s) => s.opacity(0.9)))
      .when(!forte, (el) => el.border_1().border_color(t.border).text_color(t.foreground).hover((s) => s.bg(t.hover)))
      .on_click((_e, cx) => azione(cx)).child(testo);
    const legenda = h_flex().gap(16).pt(2)
      .child(h_flex().gap(7).items_center().child(punto(t.blocked)).child(div().text_size(12.5).text_color(t.foreground).child("ti aspetta")))
      .child(h_flex().gap(7).items_center().child(punto(t.working)).child(div().text_size(12.5).text_color(t.foreground).child("sta lavorando")))
      .child(h_flex().gap(7).items_center().child(punto(t.done)).child(div().text_size(12.5).text_color(t.foreground).child("ha finito")));
    return v_flex().id("guida").track_focus(this.handle).w_full().p(28).gap(22).bg(t.popover)
      .on_key_down((e, cx) => {
        if (e.key === "escape") return this.chiudi();
        if (e.key === "right" || e.key === "enter") avanti(cx);
        else if (e.key === "left") indietro(cx);
        else return;
        cx.stop_propagation();
      })
      .child(h_flex().gap(24).items_start()
        .child(schema(t, p.zona))
        .child(v_flex().w(360).gap(10)
          .child(div().text_size(12.5).text_color(t.muted).child(`${this.passo + 1} di ${PASSI.length}`))
          .child(div().font_family("Arturo Archivo").text_size(21).text_color(t.foreground).child(p.titolo))
          .children(p.righe.map((r) => div().w(360).whitespace_normal().text_size(14).text_color(t.muted).child(r)))
          .when(Boolean(p.legenda), (el) => el.child(legenda))))
      .child(h_flex().items_center().gap(10)
        .child(h_flex().gap(6).children(PASSI.map((_, i) => div().h(6).w(i === this.passo ? 18 : 6).rounded(3)
          .bg(i === this.passo ? t.accent : t.border))))
        .child(div().flex_1())
        .child(tasto("g-salta", ultimo ? "Rileggi" : "Salta", false, (cx) => { if (ultimo) { this.passo = 0; cx.notify(); } else this.chiudi(); }))
        .when(this.passo > 0 && !ultimo, (el) => el.child(tasto("g-indietro", "Indietro", false, indietro)))
        .child(tasto("g-avanti", ultimo ? "Comincia" : "Avanti", true, avanti)));
  }
}
