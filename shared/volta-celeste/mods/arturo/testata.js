// La testata sopra la sessione, la barra di stato in basso e il benvenuto a finestra vuota.

import { div, svg } from "gpui-kit";
import { h_flex, v_flex } from "gpui-base";
import { theme, run, agents, spaces, layout, shared } from "herdr";
import { frase, nuova, slug, SUGGERIMENTI } from "./dati.js";
import { ICONA, punto, pulsante, colore, apriFinestra } from "./comuni.js";
import { apriSuggerimenti, voce } from "./suggerimenti.js";

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
      .child(svg(icona.includes("/") ? icona : ICONA(icona)).size(14)).child(div().text_size(12.5).child(testo));
    return h_flex().size_full().bg(t.chrome).border_b(1).border_color(t.border).pl(20).pr(12).gap(16).items_center()
      .child(v_flex().min_w(0).gap(1)
        .child(div().truncate().font_family("Arturo Archivo").text_size(16).text_color(t.foreground)
          .child(s ? (shared("arturo.progetti")?.[slug(s.name)]?.titolo ?? s.name) : "Volta Celeste"))
        .when(Boolean(f), (el) => el.child(h_flex().gap(7).items_center().child(punto(colore(t, f.colore), 7)).child(div().text_size(12).text_color(colore(t, f.colore)).child(f.testo)))))
      .child(div().flex_1())
      .when(Boolean(schede), (el) => el.child(schede))
      .child(bottone("chiedi", "mods/arturo/chiedi.svg", "Cosa posso chiedere", () => apriSuggerimenti()))
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
    if (spaces().length > 0 || shared("arturo.guida.aperta")) return div();
    const haProgetti = Object.keys(shared("arturo.progetti") ?? {}).length > 0;
    // Chi non ha progetti parte dalla ricerca; chi li ha, da cosa fare adesso.
    const scelti = (haProgetti ? ["guidami", "riprendi", "ricorda", "trova"] : ["trova", "riprendi", "ricorda", "guidami"])
      .map((id) => SUGGERIMENTI.find((x) => x.id === id));
    return v_flex().w(520).px(28).pt(28).pb(28).gap(20)
      .child(v_flex().gap(8)
        .child(div().font_family("Arturo Archivo").text_size(22).text_color(t.foreground).child("Cosa facciamo oggi?"))
        .child(div().w(464).whitespace_normal().text_size(14).text_color(t.muted)
          .child(haProgetti
            ? "Scegli un progetto a sinistra, oppure parti da una di queste richieste."
            : "Comincia facendo trovare a Claude i tuoi progetti. Oppure scrivigli cosa ti serve, come in una chat.")))
      .child(v_flex().gap(10)
        .child(h_flex().gap(10).child(div().w(227).child(voce(t, scelti[0], true))).child(div().w(227).child(voce(t, scelti[1], false))))
        .child(h_flex().gap(10).child(div().w(227).child(voce(t, scelti[2], false))).child(div().w(227).child(voce(t, scelti[3], false)))))
      .child(h_flex().gap(10).items_center()
        .child(pulsante("b-nuova", "square-pen", "Nuova richiesta", () => nuova(), !haProgetti ? false : true))
        .child(div().text_size(12.5).text_color(t.dim).child("Altre richieste in Cosa posso chiedere, in alto")));
  }
}
