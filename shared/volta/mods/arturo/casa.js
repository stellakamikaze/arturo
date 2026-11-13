// Le tessere su ⌘T (#5371): al posto del terminale, una tessera per progetto con la sua immagine, il
// titolo e lo stato. La prima tessera è "Nuova richiesta", così ⌘T e Invio fanno quello che faceva ⌘T.
// Scrivi per filtrare, frecce per muoverti, Invio apre, Esc torna al terminale. L'elenco lo scrive la
// barra (shared arturo.casa.progetti, barra.js); le immagini le copia volta_mod.py in immagini/ con
// l'elenco in immagini/elenco.json. Ordine, filtro e tastiera stanno in tessere.js, senza Herdr.

import { div, image, svg } from "gpui-kit";
import { v_flex, h_flex, InputState, Input } from "gpui-base";
import { theme, shared, setShared, run, readTextFile, appHome, layout } from "herdr";
import { comandoConversazione } from "./comandi.js";
import { ICONA, punto, colore, tasti } from "./comuni.js";
import { tessere, passo, colonne, iniziali, tinta, immagine, senzaTessere, STACK, TERMINALE, GAP, MIN_W } from "./tessere.js";

// Torna al terminale: lo stack del layout mostra di nuovo la scheda. Un layout senza tessere non ha lo
// stack: niente comando, che aprirebbe un avviso d'errore a ogni avvio della barra (#5456).
export const terminale = () => { if (!senzaTessere(layout())) run("layout.select", { stack: STACK, child: TERMINALE }); };

export class Casa {
  init(_p, cx) {
    this.filtro = "";
    this.at = 0;
    this.arrivate = new Set();
    this.aperta = shared("arturo.casa.apri") ?? 0;
    this.input = InputState.new({ placeholder: "Cerca un progetto" });
    this.input.on("change", (_e, cx) => { this.filtro = this.input.value(); this.at = 0; cx.notify(); });
    this.input.on("submit", () => this.vai(this.elenco()[this.at]));
    this.handle = cx.focus_handle();
    // Niente terminale() qui: la parte nasce la prima volta che si mostra, cioè a ⌘T, e la rimanderebbe
    // subito al terminale. Il ritorno al terminale all'avvio lo fa la barra (barra.js, init).
    this.leggiImmagini(cx);
    cx.timer.every(60000, (cx) => this.leggiImmagini(cx));
    // ⌘T scrive arturo.casa.apri (barra.js): campo vuoto, prima tessera, tastiera nel campo. La parte
    // resta viva anche nascosta (figlio di uno stack): basta guardare il segno, piano.
    cx.timer.every(200, (cx) => {
      const a = shared("arturo.casa.apri") ?? 0;
      if (a === this.aperta) return;
      this.aperta = a;
      this.filtro = "";
      this.at = 0;
      this.input.set_value("");
      this.input.focus();
      cx.notify();
    });
  }

  leggiImmagini(cx) {
    cx.spawn(async (cx) => {
      try {
        const l = JSON.parse((await readTextFile(`${appHome()}/immagini/elenco.json`)) ?? "[]");
        const nuove = new Set(Array.isArray(l) ? l.filter((x) => typeof x === "string") : []);
        if ([...nuove].join() !== [...this.arrivate].join()) { this.arrivate = nuove; cx.notify(); }
      } catch {
        // niente elenco: le tessere mostrano le iniziali
      }
    });
  }

  elenco() {
    return tessere(shared("arturo.casa.progetti"), this.filtro);
  }

  // Apre la tessera: la esegue la barra, come la finestra Apri. La tessera di un progetto fa nascere sempre
  // una conversazione nuova nel progetto, anche col suo spazio già aperto (Federico, 12/11/2026: "ho scelto
  // Volta ma non mi apre una nuova convo").
  vai(t) {
    if (!t) return;
    terminale();
    run(t.tipo === "nuova" ? "arturo.volta-nuova" : comandoConversazione(t.chiave));
  }

  render() {
    const t = theme();
    const l = this.elenco();
    this.at = Math.max(0, Math.min(this.at, l.length - 1));
    const lw = shared("arturo.casa.larghezza") ?? 0;
    const col = colonne(lw);
    const w = lw ? Math.floor((lw - GAP * (col - 1)) / col) : MIN_W;
    const h = Math.round((w * 10) / 16);

    const figura = (tt) => {
      if (tt.tipo === "nuova") {
        return v_flex().w(w).h(h).items_center().justify_center().gap(10).bg(t.raised)
          .child(svg(ICONA("square-pen")).size(28).text_color(t.accent))
          .child(div().text_size(12.5).text_color(t.muted).child(`${tasti().tessere} poi Invio`));
      }
      const img = immagine(tt.chiave, this.arrivate);
      if (img) return image(img).w(w).h(h);
      return v_flex().w(w).h(h).items_center().justify_center().bg(tinta(tt.chiave))
        .child(div().font_family("Arturo Archivo").text_size(30).text_color(t.foreground).opacity(0.85).child(iniziali(tt.titolo)));
    };

    const tessera = (tt, i) => {
      const scelta = i === this.at;
      const f = tt.frase ?? null;
      return v_flex().id(`casa-${tt.chiave || "nuova"}`).w(w).flex_none().rounded(10).overflow_hidden().cursor_pointer()
        .bg(t.background).border_1().border_color(scelta ? t.ring : t.border)
        .hover((st) => st.border_color(scelta ? t.ring : t.muted))
        .on_click(() => this.vai(tt))
        .child(figura(tt))
        .child(v_flex().px(12).pt(9).pb(11).gap(3)
          .child(div().truncate().text_size(14).text_color(t.foreground).child(tt.titolo))
          .child(h_flex().gap(7).items_center()
            .when(tt.tipo !== "nuova", (el) => el.child(punto(f ? colore(t, f.colore) : t.border, 7)))
            .child(div().flex_1().truncate().text_size(12.5).text_color(f ? colore(t, f.colore) : t.muted)
              .child(tt.tipo === "nuova" ? "Una sessione di Claude da zero" : f?.testo ?? ""))));
    };

    const vuoto = div().px(4).py(8).text_size(13.5).text_color(t.muted).whitespace_normal()
      .child(shared("arturo.casa.progetti") ? "Nessun progetto con questo nome." : "Leggo i tuoi progetti…");

    return v_flex().id("casa").track_focus(this.handle).size_full().bg(t.background).rounded(10)
      .border_1().border_color(t.border).overflow_hidden()
      .on_key_down((e, cx) => {
        if (e.key === "escape") { terminale(); cx.stop_propagation(); return; }
        const dopo = passo(this.at, e.key, l.length, col);
        if (dopo === this.at && !["left", "right", "up", "down"].includes(e.key)) return;
        // a destra e a sinistra il cursore del campo vince finché c'è testo: le frecce muovono le tessere
        // solo col campo vuoto
        if ((e.key === "left" || e.key === "right") && this.filtro) return;
        this.at = dopo;
        cx.stop_propagation();
        cx.notify();
      })
      .child(v_flex().flex_none().px(24).pt(22).pb(14).gap(12)
        .child(h_flex().items_center().gap(10)
          .child(div().flex_1().font_family("Arturo Archivo").text_size(20).text_color(t.foreground).child("Progetti"))
          .child(div().text_size(12.5).text_color(t.dim).child("Invio apre · Esc torna alla sessione")))
        .child(h_flex().h(40).px(12).gap(9).items_center().rounded(9).border_1().border_color(t.accent).bg(t.raised)
          .child(svg(ICONA("search")).size(15).text_color(t.muted))
          .child(Input.new(this.input).flex_1().h_full().text_size(14).text_color(t.foreground))))
      .child(div().id("casa-tessere").flex_1().overflow_y_scroll().px(24).pb(24)
        .on_size_change((m) => {
          // 48: il margine a destra e a sinistra; 8 in più per la barra di scorrimento e gli arrotondamenti,
          // che altrimenti mandano a capo l'ultima tessera della riga (12/11/2026, scatto di hzp)
          // La misura passa da shared: un campo della parte cambiato qui non ridisegna, shared sì.
          const lw = Math.max(0, Math.floor(m.width) - 56);
          if (shared("arturo.casa.larghezza") !== lw) setShared("arturo.casa.larghezza", lw);
        })
        .child(l.length
          ? h_flex().flex_wrap().gap(GAP).items_start().children(l.map(tessera))
          : vuoto));
  }
}
