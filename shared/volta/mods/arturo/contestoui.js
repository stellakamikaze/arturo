// La finestra "Contesto del progetto": come si forma il contesto che Claude legge quando apri un
// progetto con /inizio. Una sezione per fonte, nell'ordine di lettura: cos'è, perché c'è, il file, la
// data, il peso e le prime righe; "Apri" mostra il file. Il conto sta in contesto.js.
// Si apre dall'icona della testata (il progetto dello spazio aperto), dal tasto destro su un progetto
// della colonna e dal menu di una sessione. È un dialogo, cioè un'altra copia del mod.

import { div, svg } from "gpui-kit";
import { h_flex, v_flex } from "gpui-base";
import { theme, props, closeOverlay, openOverlay, spaces, notify } from "herdr";
import { contestoProgetto, apriFile, slug } from "./dati.js";
import { vistaContesto } from "./contesto.js";
import { ICONA } from "./comuni.js";
import { TESTO } from "./misure.js";

// `progetto`: lo slug o il nome; senza, quello dello spazio aperto. false se non c'è un progetto.
export function apriContesto(progetto) {
  const s = spaces().find((x) => x.active);
  const p = progetto || (s && !s.machine && s.named ? s.name : null);
  if (!p) {
    notify({ title: "Nessun progetto aperto", body: "Apri un progetto, o usa il tasto destro su un progetto a sinistra.", level: "info", timeout: 4000 });
    return false;
  }
  openOverlay({ mod: "arturo", props: { parte: "contesto", progetto: slug(p) }, kind: "dialog", width: 680, height: 0.84 });
  return true;
}

export class Contesto {
  init(_p, cx) {
    this.progetto = props()?.progetto ?? "";
    this.vista = null;
    this.errore = null;
    this.aperte = {};
    this.handle = cx.focus_handle();
    cx.timer.after(150, () => this.handle.focus());
    cx.spawn(async (cx) => {
      const r = await contestoProgetto(this.progetto);
      if (r.ok) this.vista = vistaContesto(r.json);
      if (!this.vista) this.errore = r.errore || "Arturo non ha risposto come mi aspettavo.";
      cx.notify();
    });
  }

  chiudi() { closeOverlay(props().overlay); }

  fonte(t, f, i) {
    const aperta = Boolean(this.aperte[f.id]);
    return v_flex().id(`cx-${f.id}`).px(12).py(10).gap(6).rounded(8).border_1().border_color(t.border)
      .when(!f.presente, (el) => el.opacity(0.6))
      .child(h_flex().gap(10).items_start()
        .child(div().flex_none().w(22).pt(1).text_size(12).text_color(t.dim).child(`${i + 1}.`))
        .child(v_flex().flex_1().min_w(0).gap(2)
          .child(div().id(`cx-t-${f.id}`).truncate().text_size(14).text_color(t.foreground).child(f.titolo))
          .when(Boolean(f.perche), (el) => el.child(div().whitespace_normal().text_size(12.5).text_color(t.muted).child(f.perche)))
          .child(div().id(`cx-d-${f.id}`).truncate().text_size(12).text_color(f.presente ? t.dim : t.blocked).child(f.dettaglio)))
        .when(f.anteprima.length > 0, (el) => el.child(div().id(`cx-v-${f.id}`).flex_none().px(8).py(3).rounded(6).cursor_pointer()
          .text_size(12).text_color(t.muted).hover((s) => s.bg(t.hover))
          .on_click((_e, cx) => { this.aperte[f.id] = !aperta; cx.notify(); })
          .child(aperta ? "Nascondi" : "Anteprima")))
        .when(Boolean(f.percorso), (el) => el.child(div().id(`cx-a-${f.id}`).flex_none().px(8).py(3).rounded(6).cursor_pointer()
          .text_size(12).text_color(t.accent).border_1().border_color(t.border).hover((s) => s.bg(t.selected))
          .on_click(() => apriFile(f.percorso))
          .child("Apri"))))
      .when(Boolean(f.percorso), (el) => el.child(div().pl(32).truncate().font_family("Atkinson Hyperlegible Mono").text_size(11.5).text_color(t.dim).child(f.percorso)))
      .when(aperta, (el) => el.child(v_flex().ml(32).p(8).gap(2).rounded(6).bg(t.hover)
        .children(f.anteprima.map((r, j) => div().id(`cx-r-${f.id}-${j}`).truncate().font_family("Atkinson Hyperlegible Mono").text_size(11.5).text_color(t.muted).child(r || " ")))));
  }

  render() {
    const t = theme();
    const v = this.vista;
    const corpo = v
      ? v_flex().id("cx-elenco").flex_1().min_h(0).overflow_y_scrollbar().gap(8).pr(4)
        .children(v.fonti.map((f, i) => this.fonte(t, f, i)))
        .when(v.avvisi.length > 0, (el) => el.child(v_flex().gap(2).pt(4).children(v.avvisi.map((a, i) => div().id(`cx-w-${i}`).whitespace_normal().text_size(12.5).text_color(t.blocked).child(a)))))
      : div().id("cx-stato").text_size(13).text_color(this.errore ? t.blocked : t.muted).whitespace_normal()
        .child(this.errore ? `Non riesco a leggere il contesto: ${this.errore}` : "Leggo il contesto del progetto…");
    return v_flex().id("contesto").track_focus(this.handle).size_full().p(20).gap(14).bg(t.popover)
      .on_key_down((e, cx) => { if (e.key === "escape") { this.chiudi(); cx.stop_propagation(); } })
      .child(h_flex().gap(12).items_start()
        .child(v_flex().flex_1().min_w(0).gap(4)
          .child(div().id("cx-titolo").truncate().font_family("Arturo Archivo").text_size(TESTO.titolo).text_color(t.foreground).child(v ? `Contesto di ${v.titolo}` : "Contesto del progetto"))
          .child(div().whitespace_normal().text_size(12.5).text_color(t.muted)
            .child(v ? `Cosa legge Claude quando apri il progetto, nell'ordine. In tutto: ${v.totale}.` : "Cosa legge Claude quando apri il progetto.")))
        .child(div().id("cx-chiudi").flex_none().p(4).rounded(6).cursor_pointer().hover((s) => s.bg(t.hover))
          .on_click(() => this.chiudi())
          .child(svg(ICONA("x")).size(14).text_color(t.muted))))
      .child(corpo);
  }
}
