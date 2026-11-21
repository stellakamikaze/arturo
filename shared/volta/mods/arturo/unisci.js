// Il dialogo "Unisci a…" (#6187, Fase 4 del piano del 20/11/2026): un progetto doppione entra in un altro.
// Si apre dal tasto destro su una tessera di ⌘T e sull'intestazione di un progetto nella colonna.
// Tre passi:
// 1. scegli il progetto che resta (scrivi o frecce, Invio);
// 2. l'anteprima: Arturo conta cosa passa (arturo progetti unisci … --prova --json) e non scrive niente;
// 3. il pulsante Unisci, che è il sì della persona. Invio qui non unisce: serve il clic sul pulsante.
// L'unione vera la fa la barra (unisci() di dati.js): il dialogo manda il comando e resta aperto a mostrare
// l'esito, che legge da shared arturo.unione (guarda). Se la persona lo chiude prima, la barra avvisa a fine lavoro.
// Decisione del 20/11: unione completa, il perdente va in archivio e il suo nome resta valido.

import { div, svg } from "gpui-kit";
import { v_flex, h_flex, InputState, Input } from "gpui-base";
import { theme, props, closeOverlay, openOverlay, run, shared } from "herdr";
import { unione } from "./dati.js";
import { ICONA } from "./comuni.js";
import { SPAZIO, TESTO, RAGGIO, PULSANTE, ICONA_MISURA } from "./misure.js";
import { scelteUnione, progettiPerCompito, comandoUnisciVai, impostaProgetti, nomeProgetto, slug } from "./sessioni.js";

// Uno solo aperto. Con `vincitore` il dialogo parte dall'anteprima (comando arturo.unisciprova-…).
let aperto = null;
export function apriUnisci(perdente, vincitore = null) {
  const p = slug(perdente);
  if (!p) return false;
  if (aperto) closeOverlay(aperto);
  aperto = openOverlay({ mod: "arturo", props: { parte: "unisci", perdente: p, vincitore: vincitore ? slug(vincitore) : null }, kind: "dialog", width: 560 });
  return true;
}

export class Unisci {
  init(_p, cx) {
    const p = props() ?? {};
    this.perdente = String(p.perdente ?? "");
    this.vincitore = null;
    // i nomi si leggono adesso: a unione fatta il perdente è un nome alternativo del vincitore e si chiama come lui
    impostaProgetti(shared("arturo.progetti"));
    this.nomeP = nomeProgetto(this.perdente);
    this.nomeV = "";
    this.passo = "scegli";   // scegli · anteprima · corso · esito
    this.vista = null;       // la risposta di Arturo letta da vistaUnione; null mentre conta
    this.at = 0;
    this.aperto = Date.now();
    this.input = InputState.new({ placeholder: "Scrivi o scegli il progetto che resta" });
    this.input.on("change", (_e, cx) => { this.at = 0; cx.notify(); });
    this.input.on("submit", (_e, cx) => this.scegli(cx));
    this.input.focus();
    cx.timer.after(300, () => { if (this.passo === "scegli") this.input.focus(); else this.handle.focus(); });
    this.handle = cx.focus_handle();
    // l'esito dell'unione vera arriva dalla barra
    cx.timer.every(300, (cx) => this.guarda(cx));
    if (p.vincitore) this.prova(p.vincitore, cx);
  }

  chiudi() { closeOverlay(props().overlay); }

  scelte() {
    return scelteUnione(this.perdente, progettiPerCompito(shared("arturo.progetti"), shared("arturo.casa.progetti")), this.input.value());
  }

  scegli(cx, x = null) {
    const l = this.scelte();
    const v = x ?? l[Math.max(0, Math.min(this.at, l.length - 1))];
    if (v?.chiave) this.prova(v.chiave, cx);
  }

  // Passo 2: l'anteprima. Arturo conta e non scrive.
  prova(vincitore, cx) {
    this.vincitore = vincitore;
    impostaProgetti(shared("arturo.progetti"));
    this.nomeV = nomeProgetto(vincitore);
    this.passo = "anteprima";
    this.vista = null;
    this.handle?.focus();
    cx.notify();
    cx.spawn(async (cx) => {
      const vista = await unione(this.perdente, vincitore, true);
      // la persona è tornata indietro o ha scelto un altro progetto mentre Arturo contava
      if (this.passo !== "anteprima" || this.vincitore !== vincitore) return;
      this.vista = vista;
      cx.notify();
    });
  }

  indietro(cx) {
    this.passo = "scegli";
    this.vincitore = null;
    this.vista = null;
    this.input.focus();
    cx.notify();
  }

  // Passo 3: il sì. Parte solo da un'anteprima che Arturo ha dato per buona.
  unisci(cx) {
    if (this.passo !== "anteprima" || !this.vista?.pronta) return;
    this.passo = "corso";
    this.partita = Date.now();
    run(comandoUnisciVai(this.perdente, this.vincitore));
    cx.notify();
  }

  // L'unione di questi due progetti partita dopo l'apertura del dialogo: in corso, poi l'esito. Vale anche con
  // l'anteprima ancora a schermo, se il comando è arrivato da fuori (herdr-app do).
  guarda(cx) {
    if (this.passo !== "corso" && this.passo !== "anteprima") return;
    // la barra ha rifiutato l'unione prima di cominciarla: non scriverà altro (#6290)
    const r = shared("arturo.unione.rifiuto");
    if (this.passo === "corso" && r && r.perdente === this.perdente && r.vincitore === this.vincitore && r.quando >= (this.partita ?? Infinity)) {
      this.vista = { stato: "errore", testo: String(r.testo || "La barra ha rifiutato l'unione."), righe: [], avvisi: [], backup: null };
      this.passo = "esito";
      cx.notify();
      return;
    }
    const u = shared("arturo.unione");
    if (!u || u.perdente !== this.perdente || u.vincitore !== this.vincitore || !(u.quando >= this.aperto)) return;
    if (u.stato === "corso") {
      if (this.passo === "corso") return;
      this.passo = "corso";
    } else {
      this.vista = u.vista ?? { stato: "errore", testo: "La barra non ha detto com'è andata.", righe: [], avvisi: [], backup: null };
      this.passo = "esito";
    }
    cx.notify();
  }

  render() {
    const t = theme();
    impostaProgetti(shared("arturo.progetti"));
    const P = this.nomeP;
    const V = this.nomeV;
    const l = this.passo === "scegli" ? this.scelte() : [];
    this.at = Math.max(0, Math.min(this.at, l.length - 1));
    const v = this.vista;

    const voce = (x, i) => h_flex().id(`un-${x.chiave}`).h(PULSANTE.grande).px(SPAZIO.l).gap(SPAZIO.l).items_center().rounded(RAGGIO.riga).cursor_pointer()
      .when(i === this.at, (el) => el.bg(t.selected)).hover((st) => st.bg(t.hover))
      .on_mouse_down("left", (_e, cx) => cx.stop_propagation())
      .on_click((_e, cx) => this.scegli(cx, x))
      .child(svg(ICONA("folder")).size(ICONA_MISURA.piccola).flex_none().text_color(i === this.at ? t.accent : t.muted))
      .child(div().flex_1().min_w(0).truncate().text_size(TESTO.riga).text_color(t.foreground).child(nomeProgetto(x.chiave)))
      .child(div().flex_none().max_w(220).truncate().text_size(TESTO.etichetta).text_color(t.dim).child(x.chiave));

    const riga = (r, i) => h_flex().id(`un-r-${i}`).gap(SPAZIO.l).items_start()
      .child(div().flex_none().w(170).text_size(TESTO.corpo).text_color(t.muted).child(r.cosa))
      .child(div().flex_1().min_w(0).whitespace_normal().text_size(TESTO.corpo).text_color(t.foreground).child(r.quanto));

    const bottone = (id, testo, azione, forte, acceso = true) => div().id(id).px(SPAZIO.xl).py(SPAZIO.m).rounded(RAGGIO.riga).text_size(TESTO.corpo)
      .when(forte, (el) => el.font_semibold().bg(acceso ? t.accent : t.raised).text_color(acceso ? t.accent_foreground : t.dim))
      .when(!forte, (el) => el.border_1().border_color(t.border).text_color(t.foreground))
      .when(acceso, (el) => el.cursor_pointer().hover((s) => s.opacity(0.9)))
      .on_mouse_down("left", (_e, cx) => cx.stop_propagation())
      .on_click((_e, cx) => { if (acceso) azione(cx); })
      .child(testo);

    const titolo = this.passo === "scegli" ? `Unisci ${P} a…`
      : this.passo === "esito" && v?.stato === "fatto" ? `${P} ora è ${V}`
      : `Unisci ${P} a ${V}`;
    const sotto = this.passo === "scegli" ? `${P} entra nel progetto che scegli. Il nome ${this.perdente} resta valido e apre quel progetto.`
      : `${this.perdente} entra in ${this.vincitore}`;

    const corpo = () => {
      if (this.passo === "scegli") {
        return v_flex().gap(SPAZIO.l)
          .child(h_flex().h(PULSANTE.grande).px(SPAZIO.l).gap(SPAZIO.m).items_center().rounded(RAGGIO.riga).border_1().border_color(t.accent).bg(t.raised)
            .child(svg(ICONA("search")).size(ICONA_MISURA.grande).text_color(t.muted))
            .child(Input.new(this.input).flex_1().h_full().text_size(TESTO.riga).text_color(t.foreground)))
          .child(l.length
            ? v_flex().gap(SPAZIO.xs).children(l.map(voce))
            : div().px(SPAZIO.xs).text_size(TESTO.corpo).text_color(t.muted).child("Nessun altro progetto si chiama così."))
          .child(div().px(SPAZIO.xs).text_size(TESTO.etichetta).text_color(t.dim).child("Invio mostra cosa passa, senza scrivere niente · ↑↓ scegli · Esc chiude"));
      }
      if (this.passo === "corso") {
        return v_flex().gap(SPAZIO.m)
          .child(div().text_size(TESTO.riga).text_color(t.foreground).child("Arturo copia tutto, poi unisce…"))
          .child(div().whitespace_normal().text_size(TESTO.corpo).text_color(t.muted)
            .child("Può durare qualche minuto se i task sono tanti. Puoi chiudere questa finestra: un avviso ti dice com'è andata."));
      }
      if (!v) return div().text_size(TESTO.riga).text_color(t.muted).child("Arturo conta cosa passa…");
      const buono = v.stato === "anteprima" || v.stato === "fatto";
      return v_flex().gap(SPAZIO.l)
        .when(!buono, (el) => el.child(v_flex().gap(SPAZIO.s)
          .child(div().text_size(TESTO.riga).text_color(t.blocked)
            .child(v.stato === "rifiuto" ? "Questi due progetti non si uniscono" : this.passo === "esito" ? "L'unione non è riuscita" : "Non riesco a preparare l'unione"))
          .child(div().whitespace_normal().text_size(TESTO.corpo).text_color(t.foreground).child(v.testo || "Arturo non ha detto perché."))
          .when(this.passo === "esito", (e2) => e2.child(div().whitespace_normal().text_size(TESTO.etichetta).text_color(t.muted)
            .child("Prima di riprovare guarda la copia in data/progetti/unioni/ nella cartella di Arturo.")))))
        .when(buono, (el) => el.child(v_flex().p(SPAZIO.l).gap(SPAZIO.m).rounded(RAGGIO.riga).border_1().border_color(t.border).children(v.righe.map(riga))))
        .when(v.avvisi.length > 0, (el) => el.child(v_flex().gap(SPAZIO.s).children(v.avvisi.map((a, i) =>
          h_flex().id(`un-a-${i}`).gap(SPAZIO.m).items_start()
            .child(div().flex_none().text_size(TESTO.etichetta).text_color(t.blocked).child("Attenzione"))
            .child(div().flex_1().min_w(0).whitespace_normal().text_size(TESTO.etichetta).text_color(t.foreground).child(a))))))
        .when(v.stato === "anteprima", (el) => el.child(div().whitespace_normal().text_size(TESTO.etichetta).text_color(t.muted)
          .child(v.pronta
            ? `Niente è ancora scritto. Con Unisci, Arturo copia prima tutto in data/progetti/unioni/, poi sposta. La scheda di ${this.perdente} va in archivio, non si cancella.`
            : "La fonte dei task non risponde: l'unione aspetta che torni. Riprova fra poco.")))
        .when(v.stato === "fatto", (el) => el.child(div().whitespace_normal().text_size(TESTO.etichetta).text_color(t.muted)
          .child(`Copia di prima: ${v.backup}`)));
    };

    const piede = () => {
      if (this.passo === "scegli" || this.passo === "corso") return this.passo === "corso" ? h_flex().child(bottone("un-chiudi", "Chiudi", () => this.chiudi(), false)) : div();
      if (this.passo === "esito") return h_flex().child(bottone("un-chiudi", "Chiudi", () => this.chiudi(), true));
      return h_flex().gap(SPAZIO.l).items_center()
        .when(v?.stato === "anteprima", (el) => el.child(bottone("un-vai", "Unisci", (cx) => this.unisci(cx), true, Boolean(v?.pronta))))
        .child(bottone("un-indietro", "Scegli un altro progetto", (cx) => this.indietro(cx), false))
        .child(div().flex_1())
        .child(div().text_size(TESTO.etichetta).text_color(t.dim).child("Esc chiude"));
    };

    return v_flex().id("unisci").track_focus(this.handle).w_full().p(SPAZIO.xxl).gap(SPAZIO.xl).bg(t.popover)
      .on_key_down((e, cx) => {
        if (e.key === "escape") return this.chiudi();
        if (this.passo !== "scegli" || !l.length) return;
        if (e.key === "down") this.at = (this.at + 1) % l.length;
        else if (e.key === "up") this.at = (this.at + l.length - 1) % l.length;
        else return;
        cx.stop_propagation();
        cx.notify();
      })
      .child(v_flex().gap(SPAZIO.s)
        .child(div().font_family("Arturo Archivo").text_size(TESTO.titolo).text_color(t.foreground).child(titolo))
        .child(div().whitespace_normal().text_size(TESTO.etichetta).text_color(t.muted).child(sotto)))
      .child(corpo())
      .child(piede());
  }
}
