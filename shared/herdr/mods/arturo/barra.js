// La colonna di sinistra: il marchio, i progetti, il piede.

import { div, image, svg } from "gpui-kit";
import { h_flex, v_flex } from "gpui-base";
import { theme, run, agents, spaces, window, setShared, nextCommand, openOverlay, updates } from "herdr";
import { todo, progetti, frase, apri, nuova, slug } from "./dati.js";
import { ICONA, punto, pulsante, colore } from "./comuni.js";

export class Marchio {
  render() {
    const t = theme();
    const aspetta = agents().some((a) => a.status === "blocked");
    const stella = image("mods/arturo/stella.svg").size(20).flex_none();
    const mac = window()?.platform === "macos" && !window()?.fullscreen;
    return h_flex().size_full().bg(t.chrome).pl(mac ? 84 : 18).pr(14).gap(10).items_center()
      .child(aspetta ? stella.loop("opacity", { from: 0.3, to: 1, period: 1100 }) : stella)
      .child(div().font_family("Arturo Archivo").text_size(17).text_color(t.foreground).child("Arturo"));
  }
}

export class Barra {
  init(_p, cx) {
    this.vista = null;
    this.errore = null;
    this.firma = "";
    this.carica(cx);
    cx.timer.every(30000, (cx) => this.carica(cx));
    // Quando una sessione cambia stato, i todo possono essere cambiati: si rileggono.
    cx.timer.every(3000, (cx) => {
      const f = agents().map((a) => `${a.address}:${a.status}`).join(",");
      if (f !== this.firma) { this.firma = f; this.carica(cx); }
    });
    cx.spawn(async (cx) => {
      for (;;) {
        const c = await nextCommand();
        if (c === "apri") apriFinestra();
        else if (c === "nuova") await nuova();
        cx.notify();
      }
    });
  }

  carica(cx) {
    if (this.inCorso) return;
    this.inCorso = true;
    cx.spawn(async (cx) => {
      const r = await todo(["--json"]);
      this.inCorso = false;
      if (r.ok) { this.vista = r.json; this.errore = null; setShared("arturo.letto", Date.now()); }
      else this.errore = r.errore;
      cx.notify();
    });
  }

  riga(t, p, attivo) {
    const f = frase(p.stato, p);
    return h_flex().id(`p-${p.nome}`).mx(8).px(10).py(8).gap(11).items_center().rounded(8).cursor_pointer()
      .when(attivo, (el) => el.bg(t.selected))
      .when(!attivo, (el) => el.hover((s) => s.bg(t.hover)))
      .on_click(() => apri(p.nome))
      .child(p.stato && p.stato !== "idle" ? punto(colore(t, f.colore)) : p.aperto ? punto(t.idle) : div().size(8).flex_none())
      .child(v_flex().flex_1().min_w(0).gap(2)
        .child(div().truncate().text_size(14).text_color(t.foreground).when(attivo, (d) => d.font_semibold()).child(p.nome))
        .child(div().truncate().text_size(12.5).text_color(colore(t, f.colore)).child(f.testo)));
  }

  render() {
    const t = theme();
    const lista = progetti(this.vista);
    const attivo = slug(spaces().find((s) => s.active)?.name);
    const corpo = v_flex().id("progetti-elenco").flex_1().min_h(0).overflow_y_scrollbar().pb(8);
    let contenuto;
    if (this.vista === null && !this.errore) contenuto = div().px(18).py(6).text_size(13).text_color(t.muted).child("Leggo i tuoi progetti…");
    else if (!lista.length) contenuto = div().px(18).py(6).text_size(13).text_color(t.muted).whitespace_normal()
      .child(this.errore ? "Non riesco a leggere i todo di Arturo. Le sessioni funzionano lo stesso." : "Qui compariranno i tuoi progetti. Comincia con una richiesta a Claude.");
    else contenuto = v_flex().gap(2).children(lista.map((p) => this.riga(t, p, p.nome === attivo)));
    return v_flex().size_full().bg(t.chrome)
      .child(v_flex().px(14).pt(6).pb(14).gap(8)
        .child(pulsante("nuova", "square-pen", "Nuova richiesta", () => nuova(), true))
        .child(pulsante("apri", "folder", "Apri un progetto", () => apriFinestra())))
      .child(h_flex().px(18).pt(6).pb(8).items_center()
        .child(div().flex_1().text_size(12.5).font_semibold().text_color(t.muted).child("I tuoi progetti"))
        .when(Boolean(this.errore) && lista.length > 0, (el) => el.child(div().text_size(11.5).text_color(t.blocked).child("todo non aggiornati"))))
      .child(corpo.child(contenuto));
  }
}

export function apriFinestra() {
  openOverlay({ mod: "arturo", props: { parte: "apri" }, kind: "dialog", width: 560 });
}

export class Piede {
  render() {
    const t = theme();
    const voce = (id, icona, testo, azione) => h_flex().id(id).h(32).px(10).gap(10).items_center().rounded(8).cursor_pointer()
      .text_color(t.muted).hover((s) => s.bg(t.hover).text_color(t.foreground)).on_click(azione)
      .child(svg(ICONA(icona)).size(15)).child(div().flex_1().text_size(13).child(testo));
    return v_flex().size_full().bg(t.chrome).border_t(1).border_color(t.border).px(8).py(8)
      .child(voce("impostazioni", "settings", "Impostazioni", () => run("app.settings"))
        .when(Boolean(updates().app.ready), (el) => el.child(punto(t.accent, 7))));
  }
}
