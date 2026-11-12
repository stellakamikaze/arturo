// La parte "note": l'elenco delle note sulla finestra del progetto (⌘⇧E, o il conteggio nella barra di
// stato). Una riga per nota: numero, tipo, testo, stato, ultima risposta di Claude, età. "Aperte" mostra
// quelle che Claude deve ancora chiudere, "Tutte" anche le risolte e le scartate. Un clic su una nota aperta
// apre il velo su quella nota, dove si risponde o si chiude; un clic su una chiusa ne mostra il filo.
// Le note le legge e le rilegge la barra di stato (testata.js) e le passa in shared arturo.note.

import { div } from "gpui-kit";
import { h_flex, v_flex } from "gpui-base";
import { theme, props, closeOverlay, shared, run } from "herdr";
import { config } from "./dati.js";
import { tasti } from "./comuni.js";
import { leggiTutte } from "./notaui.js";
import { progettoAdesso } from "./testata.js";
import { righeElenco, contaNote } from "./nota.js";

const ARANCIO = "#f2a24a";
const FILTRI = [{ id: "aperte", etichetta: "Aperte" }, { id: "tutte", etichetta: "Tutte" }];

export class Note {
  init(_p, cx) {
    this.filtro = "aperte";
    this.espansa = null;    // l'id della nota chiusa di cui si vede il filo
    this.scelto = null;
    this.pronto = false;
    this.proprie = null;    // una lettura sua, se la barra di stato non ha ancora letto
    this.handle = cx.focus_handle();
    cx.timer.after(150, () => this.handle.focus());
    cx.spawn(async (cx) => {
      const c = await config();
      this.scelto = c.note_progetto;
      if (!shared("arturo.note")) this.proprie = ((await leggiTutte(c.arturo[0])) ?? []).map((x) => x.nota);
      this.pronto = true;
      cx.notify();
    });
  }

  note() { return shared("arturo.note") ?? this.proprie ?? []; }

  chiudi() { closeOverlay(props().overlay); }

  // Prima il comando, poi la chiusura: un overlay chiuso ferma il suo codice.
  apri(r) {
    run(`arturo.nota-${r.id}`);
    this.chiudi();
  }

  pastiglia(t, f, n) {
    const scelto = f.id === this.filtro;
    return div().id(`note-filtro-${f.id}`).px(11).py(4).rounded_full().cursor_pointer().text_size(12.5)
      .border_1().border_color(scelto ? t.accent : t.border).bg(scelto ? t.accent : t.raised)
      .text_color(scelto ? t.accent_foreground : t.muted)
      .on_mouse_down("left", (_e, cx) => cx.stop_propagation())
      .on_click((_e, cx) => { this.filtro = f.id; this.espansa = null; cx.notify(); })
      .child(`${f.etichetta} · ${n}`);
  }

  riga(t, r) {
    const aperta = this.espansa === r.id;
    const voce = (v) => v_flex().gap(1)
      .child(div().text_size(11.5).text_color(v.chi === "claude" ? t.accent : t.muted).child(v.chi === "claude" ? "Claude" : "Tu"))
      .child(div().whitespace_normal().text_size(12.5).text_color(t.foreground).child(v.testo));
    const numero = r.numero != null
      ? h_flex().size(22).flex_none().items_center().justify_center().rounded_full().border_2()
        .border_color(t.accent).bg(r.stato === "presa" ? t.popover : ARANCIO)
        .text_size(11.5).font_semibold().text_color(r.stato === "presa" ? t.foreground : "#1a1206").child(String(r.numero))
      : h_flex().size(22).flex_none().items_center().justify_center().child(div().size(8).rounded_full().bg(t.dim));
    return v_flex().id(`note-riga-${r.id}`).px(12).py(10).gap(8).rounded(8).cursor_pointer().hover((s) => s.bg(t.hover))
      .on_mouse_down("left", (_e, cx) => cx.stop_propagation())
      .on_click((_e, cx) => {
        if (r.aperta) return this.apri(r);
        this.espansa = aperta ? null : r.id;
        cx.notify();
      })
      .child(h_flex().gap(12).items_start()
        .child(numero)
        .child(v_flex().flex_1().min_w(0).gap(4)
          .child(h_flex().gap(8).items_center()
            .child(div().px(8).py(1).rounded_full().bg(t.raised).text_size(11.5).text_color(t.muted).child(r.tipo))
            .child(div().text_size(11.5).text_color(r.stato === "presa" ? t.accent : r.aperta ? t.foreground : t.dim).child(r.etichettaStato))
            .child(div().flex_1())
            .child(div().text_size(11.5).text_color(t.dim).child(r.eta)))
          .child(div().whitespace_normal().text_size(13.5).text_color(r.aperta ? t.foreground : t.muted).child(r.testo))
          .when(Boolean(r.risposta) && !aperta, (el) => el.child(div().truncate().text_size(12.5).text_color(t.accent)
            .child(`Claude: ${r.risposta}`)))
          .when(!r.aperta && Boolean(r.chiusura) && !aperta, (el) => el.child(div().truncate().text_size(12.5).text_color(t.muted)
            .child(`${r.stato === "risolta" ? "Risolta" : "Scartata"}: ${r.chiusura}`)))))
      .when(aperta, (el) => el.child(v_flex().pl(34).gap(8).children(r.filo.slice(1).map(voce))));
  }

  render() {
    const t = theme();
    const k = tasti();
    const progetto = progettoAdesso(this.scelto);
    const note = this.note();
    const conta = contaNote(note, progetto);
    const righe = righeElenco(note, progetto, this.filtro, new Date());
    let corpo;
    if (!this.pronto && !shared("arturo.note")) corpo = div().px(12).text_size(13).text_color(t.muted).child("Leggo le note…");
    else if (!righe.length) corpo = div().px(12).whitespace_normal().text_size(13).text_color(t.muted)
      .child(this.filtro === "aperte"
        ? `Nessuna nota aperta. Premi ${k.nota} e clicca il punto della finestra di cui vuoi parlare.`
        : `Nessuna nota in questo progetto. Premi ${k.nota} e clicca il punto della finestra di cui vuoi parlare.`);
    else corpo = v_flex().gap(2).children(righe.map((r) => this.riga(t, r)));
    return v_flex().id("note").track_focus(this.handle).size_full().p(24).gap(14).bg(t.popover)
      .on_key_down((e, cx) => { if (e.key === "escape") { this.chiudi(); cx.stop_propagation(); } })
      .child(v_flex().gap(4)
        .child(div().font_family("Arturo Archivo").text_size(19).text_color(t.foreground).child("Note sulla finestra"))
        .child(div().whitespace_normal().text_size(13).text_color(t.muted)
          .child(`${progetto ? `Le note di ${progetto}` : "Le note senza progetto"}. Una nota aperta si apre nel suo punto: lì rispondi a Claude, la dai per risolta o la scarti.`)))
      .child(h_flex().gap(8).children(FILTRI.map((f) => this.pastiglia(t, f, f.id === "aperte" ? conta.aperte : conta.tutte))))
      .child(v_flex().id("note-elenco").flex_1().min_h(0).overflow_y_scrollbar().child(corpo))
      .child(div().text_size(12).text_color(t.dim).child(`${k.nota} nuova nota · Esc chiude`));
  }
}
