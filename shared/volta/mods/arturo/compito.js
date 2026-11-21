// Il dialogo "Compito nuovo" (⌘N, Ctrl+Shift+N su Windows, #6186, 20/11/2026): scrivi il compito, Volta
// propone il progetto mentre scrivi, Invio fa nascere la sessione che ci lavora. Decisione del
// 20/11: "Volta propone il progetto e Invio conferma".
// - La proposta viene dalle parole del testo (scelteCompito di sessioni.js): slug, titolo, nomi alternativi e
//   riga di stato dei progetti. "nome: compito" dice il progetto a mano. Quando il testo non nomina un
//   progetto, dopo un secondo di pausa un modello piccolo (volta_compito.py) può cambiare la proposta,
//   finché la persona non ha scelto con le frecce.
// - ↑↓ scorrono: i progetti proposti, "Progetto nuovo: <slug>", "Senza progetto".
// - Invio: la sessione nasce in background e la finestra resta dov'è. ⌘Invio (Ctrl+Invio): nasce e si apre.
// La nascita la fa la barra: il dialogo manda il comando e si chiude, perché un overlay chiuso ferma il suo
// codice al primo await (comandi.js).

import { div, svg } from "gpui-kit";
import { v_flex, h_flex, InputState, Input } from "gpui-base";
import { theme, props, closeOverlay, run, shared, exec, appHome, writeTextFile, readTextFile } from "herdr";
import { config, cacheVolta, creaCartella, progettoDavanti } from "./dati.js";
import { ICONA, nasceSu, tasti } from "./comuni.js";
import { SPAZIO, TESTO, RAGGIO, PULSANTE, ICONA_MISURA } from "./misure.js";
import { scelteCompito, progettiPerCompito, comandoCompito, testoCompito, nomeDetto, serveModello, codifica, impostaProgetti, nomeProgetto,
  TESTO_COMPITO_MAX, COMPITO_PAUSA_MS } from "./sessioni.js";

// Il tetto dell'attesa del modello piccolo: il suo (TETTO di volta_compito.py) più l'avvio di Python.
const MODELLO_MS = 30000;

export class Compito {
  init(_p, cx) {
    this.testo = typeof props()?.testo === "string" ? props().testo : "";
    this.at = null;        // la riga scelta con le frecce; null = la proposta
    this.modello = null;   // { testo, slug }: la risposta del modello piccolo per quel testo
    this.chiesto = null;   // il testo dell'ultima domanda al modello
    this.inVolo = false;
    this.battuta = Date.now();
    this.partito = false;
    this.acceso = false;   // il modello piccolo: lo dice arturo.json (compito_modello)
    this.davanti = progettoDavanti();
    this.input = InputState.new({ value: this.testo, placeholder: "Cosa deve fare Claude?" });
    this.input.on("change", (_e, cx) => { this.testo = this.input.value(); this.at = null; this.battuta = Date.now(); cx.notify(); });
    this.input.on("submit", () => this.vai(false));
    this.input.focus();
    cx.timer.after(300, () => this.input.focus());
    this.handle = cx.focus_handle();
    cx.spawn(async () => {
      try {
        const c = await config();
        this.py = c.arturo[0];
        this.acceso = c.compito_modello === "acceso";
      } catch { /* senza configurazione resta la proposta dalle parole */ }
    });
    cx.timer.every(250, (cx) => this.chiedi(cx));
  }

  chiudi() { closeOverlay(props().overlay); }

  progetti() { return progettiPerCompito(shared("arturo.progetti"), shared("arturo.casa.progetti")); }

  // Le righe e quella scelta: la proposta, finché la persona non usa le frecce.
  scelte() {
    const m = this.modello?.testo === this.testo ? this.modello.slug : null;
    const s = scelteCompito(this.testo, this.progetti(), this.davanti, m);
    const at = this.at === null ? s.at : Math.max(0, Math.min(this.at, s.righe.length - 1));
    return { righe: s.righe, at };
  }

  // Il modello piccolo, una volta per testo, dopo la pausa: scrive i progetti in un file e lancia lo script.
  chiedi(cx) {
    const testo = this.testo;
    if (!this.acceso || !this.py || this.inVolo || this.partito || testo === this.chiesto) return;
    if (Date.now() - this.battuta < COMPITO_PAUSA_MS) return;
    const progetti = this.progetti();
    if (!serveModello(testo, progetti)) return;
    this.chiesto = testo;
    this.inVolo = true;
    cx.notify();
    cx.spawn(async (cx) => {
      try {
        const cartella = cacheVolta("volta-compito");
        const file = `${cartella}/progetti.json`;
        await creaCartella(cartella, this.py);
        const prima = await readTextFile(file).catch(() => null);
        const dati = JSON.stringify(progetti.map((p) => ({ chiave: p.chiave, titolo: p.titolo, riga: p.riga })));
        if (prima !== dati) await writeTextFile(file, dati, prima ?? null);
        const r = await exec(this.py, [`${appHome()}/mods/arturo/volta_compito.py`, "proponi", file, codifica(testoCompito(testo))], { timeout: MODELLO_MS });
        const d = JSON.parse(String(r.stdout ?? "").trim().split("\n").pop() || "{}");
        // una scelta già fatta con le frecce resta: la risposta arrivata dopo non sposta le righe sotto il cursore
        if (typeof d.slug === "string" && d.slug && this.at === null) this.modello = { testo, slug: d.slug };
      } catch { /* senza risposta resta la proposta dalle parole */ }
      this.inVolo = false;
      cx.notify();
    });
  }

  // Prima il comando, poi la chiusura. `apri`: ⌘Invio, la scheda si apre.
  vai(apri, riga = null) {
    if (this.partito || !testoCompito(this.testo)) return;
    const s = this.scelte();
    const r = riga ?? s.righe[s.at];
    if (!r) return;
    this.partito = true;
    run(comandoCompito(r, this.testo, apri));
    this.chiudi();
  }

  render() {
    const t = theme();
    impostaProgetti(shared("arturo.progetti"));
    const scritto = Boolean(testoCompito(this.testo));
    const { righe, at } = this.scelte();
    const lungo = this.testo.length > TESTO_COMPITO_MAX;
    const perche = { testo: "Proposto · dal testo", modello: "Proposto da Arturo", davanti: "Proposto · il progetto aperto" };
    const riga = (r, i) => {
      const su = i === at;
      const icona = r.tipo === "progetto" ? "folder" : r.tipo === "nuovo" ? "folder-plus" : "square";
      const nome = r.tipo === "progetto" ? nomeProgetto(r.slug) : r.tipo === "nuovo" ? `Progetto nuovo: ${r.slug}` : "Senza progetto";
      const proposta = su && this.at === null && r.tipo === "progetto";
      const dopo = r.tipo === "progetto" ? (proposta ? perche[r.perche] ?? "Proposto" : r.slug)
        : r.tipo === "nuovo" ? (nomeDetto(this.testo) ? "Claude crea scheda e task" : "nome dalle prime parole")
        : "Claude parte dalla cartella dei progetti";
      return h_flex().id(`compito-r-${r.tipo}-${r.slug || "senza"}`).h(PULSANTE.grande).px(SPAZIO.l).gap(SPAZIO.l).items_center().rounded(RAGGIO.riga).cursor_pointer()
        .when(su, (el) => el.bg(t.selected)).hover((st) => st.bg(t.hover))
        .on_mouse_down("left", (_e, cx) => cx.stop_propagation())
        .on_click(() => this.vai(false, r))
        .child(svg(ICONA(icona)).size(ICONA_MISURA.piccola).flex_none().text_color(su ? t.accent : t.muted))
        .child(div().flex_1().min_w(0).truncate().text_size(TESTO.riga).text_color(t.foreground).child(nome))
        .child(div().flex_none().max_w(260).truncate().text_size(TESTO.etichetta).text_color(proposta ? t.accent : t.dim).child(dopo));
    };
    const sotto = lungo ? `Il compito è lungo: partono i primi ${TESTO_COMPITO_MAX} caratteri.`
      : this.inVolo ? "Arturo cerca il progetto…"
      : `Invio parte e resti qui · ${tasti().apriCompito} parte e apre la sessione · ↑↓ cambia progetto · Esc chiude`;
    return v_flex().id("compito").track_focus(this.handle).w_full().p(SPAZIO.xxl).gap(SPAZIO.l).bg(t.popover)
      .on_key_down((e, cx) => {
        if (e.key === "escape") return this.chiudi();
        if (e.key === "enter" && (e.modifiers?.platform || e.modifiers?.control)) { cx.stop_propagation(); return this.vai(true); }
        if (e.key === "down") this.at = (at + 1) % Math.max(1, righe.length);
        else if (e.key === "up") this.at = (at + righe.length - 1) % Math.max(1, righe.length);
        else return;
        cx.stop_propagation();
        cx.notify();
      })
      .child(div().font_family("Arturo Archivo").text_size(TESTO.titolo).text_color(t.foreground).child("Compito nuovo"))
      .when(Boolean(nasceSu(t)), (el) => el.child(nasceSu(t)))
      .child(h_flex().h(PULSANTE.grande).px(SPAZIO.l).gap(SPAZIO.m).items_center().rounded(RAGGIO.riga).border_1().border_color(t.accent).bg(t.raised)
        .child(svg(ICONA("square-pen")).size(ICONA_MISURA.grande).text_color(t.muted))
        .child(Input.new(this.input).flex_1().h_full().text_size(TESTO.riga).text_color(t.foreground)))
      .when(scritto, (el) => el.child(v_flex().gap(SPAZIO.xs)
        .child(div().px(SPAZIO.xs).text_size(TESTO.etichetta).text_color(t.muted).child("In quale progetto"))
        .children(righe.map(riga))))
      .when(!scritto, (el) => el.child(div().px(SPAZIO.xs).text_size(TESTO.corpo).text_color(t.muted).whitespace_normal()
        .child("Scrivi il compito: Arturo propone il progetto mentre scrivi. Per dirlo tu: \"progetto: compito\".")))
      .child(div().px(SPAZIO.xs).text_size(TESTO.etichetta).text_color(lungo ? t.blocked : t.dim).child(sotto));
  }
}
