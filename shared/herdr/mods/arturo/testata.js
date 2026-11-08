// La testata sopra la sessione, la barra di stato in basso e il benvenuto a finestra vuota.

import { div, svg } from "gpui-kit";
import { h_flex, v_flex } from "gpui-base";
import { theme, run, agents, spaces, layout } from "herdr";
import { frase, nuova } from "./dati.js";
import { ICONA, punto, pulsante, colore } from "./comuni.js";
import { apriFinestra } from "./barra.js";

function trova(nodo, id) {
  if (nodo?.id === id) return nodo;
  for (const c of nodo?.children ?? []) { const x = trova(c, id); if (x) return x; }
  return null;
}

export class Testata {
  render() {
    const t = theme();
    const s = spaces().find((x) => x.active);
    const tab = s?.tabs.find((x) => x.active);
    const f = s?.status ? frase(s.status) : null;
    const pannello = trova(layout(), "pannello");
    const schede = (s?.tabs ?? []).length > 1
      ? h_flex().gap(4).children(s.tabs.map((x, i) => h_flex().id(`scheda-${x.id}`).h(28).px(10).gap(7).items_center().rounded(7).cursor_pointer()
          .on_mouse_down("left", (_e, cx) => cx.stop_propagation())
          .when(x.active, (el) => el.bg(t.selected).text_color(t.foreground))
          .when(!x.active, (el) => el.text_color(t.muted).hover((st) => st.bg(t.hover)))
          .on_click(() => run("tab.select", { id: x.id }))
          .when(Boolean(x.status), (el) => el.child(punto(colore(t, frase(x.status).colore), 7)))
          .child(div().text_size(12.5).child(x.named ? x.name : `Conversazione ${i + 1}`))))
      : null;
    const bottone = (id, icona, testo, azione) => h_flex().id(id).h(30).px(10).gap(7).items_center().rounded(7).cursor_pointer()
      .text_color(t.muted).hover((st) => st.bg(t.hover).text_color(t.foreground))
      .on_mouse_down("left", (_e, cx) => cx.stop_propagation()).on_click(azione)
      .child(svg(ICONA(icona)).size(14)).child(div().text_size(12.5).child(testo));
    return h_flex().size_full().bg(t.chrome).border_b(1).border_color(t.border).pl(20).pr(12).gap(16).items_center()
      .child(v_flex().min_w(0).gap(1)
        .child(div().truncate().font_family("Arturo Archivo").text_size(16).text_color(t.foreground).child(s ? s.name : "Arturo"))
        .when(Boolean(f), (el) => el.child(h_flex().gap(7).items_center().child(punto(colore(t, f.colore), 7)).child(div().text_size(12).text_color(colore(t, f.colore)).child(f.testo)))))
      .child(div().flex_1())
      .when(Boolean(schede), (el) => el.child(schede))
      .when(Boolean(s), (el) => el.child(bottone("altra", "plus", "Altra conversazione", () => run("tab.new", { argv: ["claude"] }))))
      .child(bottone("dafare", "panel-right", pannello?.hidden ? "Mostra Da fare" : "Nascondi Da fare", () => run("layout.toggle", { id: "pannello" })));
  }
}

export class Stato {
  render() {
    const t = theme();
    const a = agents();
    const n = (st) => a.filter((x) => x.status === st).length;
    const pezzo = (c, testo) => h_flex().gap(7).items_center().child(punto(c, 7)).child(testo);
    const tasti = "⌘O apri un progetto   ⌘⇧↓ prossima sessione   ⌘, impostazioni";
    return h_flex().size_full().px(18).gap(18).items_center().bg(t.chrome).border_t(1).border_color(t.border).text_size(12).text_color(t.muted)
      .when(a.length === 0, (el) => el.child(pezzo(t.idle, "Nessuna sessione aperta")))
      .when(n("blocked") > 0, (el) => el.child(pezzo(t.blocked, div().text_color(t.foreground).child(`${n("blocked")} ti aspett${n("blocked") > 1 ? "ano" : "a"}`))))
      .when(n("working") > 0, (el) => el.child(pezzo(t.working, `${n("working")} al lavoro`)))
      .when(n("done") > 0, (el) => el.child(pezzo(t.done, `${n("done")} hanno finito`.replace(/^1 hanno/, "1 ha"))))
      .when(a.length > 0 && !n("blocked") && !n("working") && !n("done"), (el) => el.child(pezzo(t.idle, a.length > 1 ? `${a.length} sessioni aperte, nessuna ti aspetta` : "1 sessione aperta, non ti aspetta")))
      .child(div().flex_1())
      .child(div().text_color(t.dim).child(tasti));
  }
}

export class Benvenuto {
  render() {
    const t = theme();
    if (spaces().length > 0) return div();
    const passo = (n, titolo, testo) => h_flex().gap(14).items_start()
      .child(div().size(26).flex_none().rounded_full().border_1().border_color(t.border).flex().items_center().justify_center()
        .text_size(12.5).text_color(t.muted).child(String(n)))
      .child(v_flex().w(378).gap(3)
        .child(div().text_size(14).font_semibold().text_color(t.foreground).child(titolo))
        .child(div().whitespace_normal().text_size(13.5).text_color(t.muted).child(testo)));
    return v_flex().w(480).px(28).pt(28).pb(32).gap(22)
      .child(v_flex().gap(8)
        .child(div().font_family("Arturo Archivo").text_size(22).text_color(t.foreground).child("Cosa facciamo oggi?"))
        .child(div().w(424).whitespace_normal().text_size(14).text_color(t.muted)
          .child("Qui lavori con Claude. Non serve conoscere il terminale: scrivi come in una chat.")))
      .child(v_flex().gap(16)
        .child(passo(1, "A sinistra, i tuoi progetti", "Per ognuno vedi se Claude sta lavorando, se aspetta te e quante cose ci sono da fare."))
        .child(passo(2, "Al centro, la conversazione", "Scrivi cosa ti serve e premi Invio. Claude ti chiede conferma prima di fare cose che non si annullano."))
        .child(passo(3, "A destra, cosa c'è da fare", "I todo del progetto, divisi fra quelli che toccano a te e quelli di Claude.")))
      .child(h_flex().gap(10).pt(4)
        .child(pulsante("b-nuova", "square-pen", "Nuova richiesta", () => nuova(), true))
        .child(pulsante("b-apri", "folder", "Apri un progetto", () => apriFinestra())));
  }
}
