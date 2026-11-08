// La colonna di sinistra: il marchio, i progetti, il piede.

import { div, image, svg } from "gpui-kit";
import { h_flex, v_flex } from "gpui-base";
import { theme, run, agents, spaces, window, shared, setShared, nextCommand, openOverlay, updates } from "herdr";
import { todo, progetti, sezioni, frase, apri, nuova, slug, cartelle, SUGGERIMENTI } from "./dati.js";
import { ICONA, punto, pulsante, colore, apriFinestra } from "./comuni.js";
import { apriGuida } from "./guida.js";
import { apriSuggerimenti, esegui } from "./suggerimenti.js";
import { apriRevisione } from "./revisione.js";
import { revisione, settimanaDi } from "./settimana.js";

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
    // La guida si apre da sola la prima volta, per chi arriva da /setup e per chi usa già Arturo.
    this.primoAvvio = !shared("arturo.guida");
    if (this.primoAvvio) cx.timer.after(900, () => { setShared("arturo.guida", "vista"); apriGuida(); });
    cx.timer.every(30000, (cx) => this.carica(cx));
    // Quando una sessione cambia stato, i todo possono essere cambiati: si rileggono.
    cx.timer.every(3000, (cx) => {
      // Anche un todo scritto dal pannello (shared arturo.scritto) cambia i conti della barra.
      const f = agents().map((a) => `${a.address}:${a.status}`).join(",") + `|${shared("arturo.scritto") ?? ""}`;
      if (f !== this.firma) { this.firma = f; this.carica(cx); }
    });
    cx.spawn(async (cx) => {
      for (;;) {
        const c = await nextCommand();
        if (c === "apri") apriFinestra();
        else if (c === "chiedi") apriSuggerimenti();
        else if (c === "settimana") apriRevisione();
        else if (/^guida\d?$/.test(c)) apriGuida(Math.max(0, Number(c.slice(5) || 1) - 1));
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
      // Le cartelle dei progetti e le righe di stato dell'archivio di Arturo (una fonte esterna può non averle).
      this.cartelle = await cartelle();
      const st = await todo(["progetti", "--json"]);
      this.stati = st.ok ? st.json?.stati ?? {} : {};
      this.inCorso = false;
      if (r.ok) {
        this.vista = r.json;
        this.errore = null;
        // Per la testata e il pannello Da fare: il nome per la fonte, il titolo e la riga di ogni progetto.
        const mappa = {};
        for (const p of progetti(this.vista, this.extra())) mappa[p.chiave] = { nome: p.nome ?? p.chiave, titolo: p.titolo, riga: p.calcolato ? "" : (p.riga ?? "") };
        setShared("arturo.progetti", mappa);
        setShared("arturo.letto", Date.now());
        this.settimana();
      }
      else this.errore = r.errore;
      cx.notify();
    });
  }

  // La revisione della settimana si apre da sola alla prima lettura di ogni settimana, se c'è qualcosa
  // da guardare. Al primo avvio no: c'è già la guida.
  settimana() {
    const ora = settimanaDi(this.vista?.oggi ?? "");
    if (!ora || shared("arturo.settimana") === ora) return;
    setShared("arturo.settimana", ora);
    const l = revisione(this.vista);
    if (!this.primoAvvio && (l.scaduti.length || l.te.length || l.fermi.length)) apriRevisione();
  }

  extra() {
    return { cartelle: this.cartelle ?? [], stati: this.stati ?? {} };
  }

  riga(t, p, attivo) {
    const f = frase(p.stato, p);
    const vivo = p.stato && p.stato !== "idle";
    return h_flex().id(`p-${p.chiave}`).mx(8).px(10).py(7).gap(11).items_start().rounded(8).cursor_pointer()
      .when(attivo, (el) => el.bg(t.selected))
      .when(!attivo, (el) => el.hover((s) => s.bg(t.hover)))
      .on_click(() => apri(p.chiave))
      .child(div().pt(6).child(vivo ? punto(colore(t, f.colore)) : p.aperto ? punto(t.idle) : div().size(8).flex_none()))
      .child(v_flex().flex_1().min_w(0).gap(2)
        .child(div().truncate().text_size(14).text_color(t.foreground).when(attivo, (d) => d.font_semibold()).child(p.titolo))
        .child(div().truncate().text_size(12.5).text_color(colore(t, f.colore)).child(f.testo)));
  }

  render() {
    const t = theme();
    const lista = progetti(this.vista, this.extra());
    const attivo = slug(spaces().find((s) => s.active)?.name);
    const corpo = v_flex().id("progetti-elenco").flex_1().min_h(0).overflow_y_scrollbar().pb(10);
    let contenuto;
    if (this.vista === null && !this.errore) contenuto = div().px(18).py(6).text_size(13).text_color(t.muted).child("Leggo i tuoi progetti…");
    else if (!lista.length) contenuto = v_flex().px(14).gap(10)
      .child(div().px(4).text_size(13).text_color(t.muted).whitespace_normal()
        .child(this.errore ? "Non riesco a leggere i todo di Arturo. Le conversazioni funzionano lo stesso." : "Non hai ancora progetti. Claude può cercarli sul tuo computer e proporteli."))
      .when(!this.errore, (el) => el.child(pulsante("trova", "search", "Trova i miei progetti", () => esegui(SUGGERIMENTI[0]), true)));
    else contenuto = v_flex().gap(14).children(sezioni(lista).map((sez) => v_flex().gap(1)
      .child(div().px(18).pb(4).text_size(12.5).font_semibold().text_color(t.muted).child(sez.titolo))
      .children(sez.progetti.map((p) => this.riga(t, p, p.chiave === attivo)))));
    return v_flex().size_full().bg(t.chrome)
      .child(v_flex().px(14).pt(6).pb(14).gap(8)
        .child(pulsante("nuova", "square-pen", "Nuova richiesta", () => nuova(), lista.length > 0 || Boolean(this.errore)))
        .child(pulsante("apri", "folder", "Apri un progetto", () => apriFinestra())))
      .when(Boolean(this.errore) && lista.length > 0, (el) => el.child(div().px(18).pb(6).text_size(12).text_color(t.blocked).child("Non riesco ad aggiornare i todo: mostro gli ultimi letti.")))
      .child(corpo.child(contenuto));
  }
}

export class Piede {
  render() {
    const t = theme();
    const voce = (id, icona, testo, azione) => h_flex().id(id).h(32).px(10).gap(10).items_center().rounded(8).cursor_pointer()
      .text_color(t.muted).hover((s) => s.bg(t.hover).text_color(t.foreground)).on_click(azione)
      .child(svg(icona.includes("/") ? icona : ICONA(icona)).size(15)).child(div().flex_1().text_size(13).child(testo));
    return v_flex().size_full().bg(t.chrome).border_t(1).border_color(t.border).px(8).py(8).gap(2)
      .child(voce("chiedi", "mods/arturo/chiedi.svg", "Cosa posso chiedere", () => apriSuggerimenti()))
      .child(voce("settimana", "mods/arturo/settimana.svg", "La settimana", () => apriRevisione()))
      .child(voce("guida", "mods/arturo/guida.svg", "Guida", () => apriGuida()))
      .child(voce("impostazioni", "settings", "Impostazioni", () => run("app.settings"))
        .when(Boolean(updates().app.ready), (el) => el.child(punto(t.accent, 7))));
  }
}
