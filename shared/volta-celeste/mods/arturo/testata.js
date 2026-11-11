// La testata sopra la sessione, la barra di stato in basso e il benvenuto a finestra vuota. La barra di
// stato tiene d'occhio anche le note sulla finestra: ne mostra il conteggio, che apre l'elenco, e avvisa
// quando Claude risponde a una nota.

import { div, svg } from "gpui-kit";
import { h_flex, v_flex } from "gpui-base";
import { theme, run, agents, spaces, layout, shared, setShared, watchFolder, notify, home } from "herdr";
import { frase, nuova, slug, config, statoSpazio, SUGGERIMENTI } from "./dati.js";
import { ICONA, punto, pulsante, colore, apriFinestra, apriElenco, tasti, nasceSu } from "./comuni.js";
import { leggiTutte } from "./notaui.js";
import { cartellaNote, progettoNota, contaNote, noteAperte, risposteClaude, risposteNuove } from "./nota.js";

const ARANCIO = "#f2a24a";

// Il progetto delle note adesso: quello di arturo.json, altrimenti lo spazio aperto (come il velo).
export function progettoAdesso(scelto) {
  const s = spaces().find((x) => x.active);
  return progettoNota(scelto, s && !s.machine && s.named ? s.name : null);
}
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
    const st = statoSpazio(s);
    const f = st ? frase(st) : null;
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
        .child(div().id("testata-titolo").truncate().font_family("Arturo Archivo").text_size(16).text_color(t.foreground)
          .child(s ? (shared("arturo.progetti")?.[slug(s.name)]?.titolo ?? s.name) : "Volta Celeste"))
        .when(Boolean(f), (el) => el.child(h_flex().id("testata-stato").gap(7).items_center().child(punto(colore(t, f.colore), 7)).child(div().text_size(12).text_color(colore(t, f.colore)).child(f.testo)))))
      .child(div().flex_1())
      .when(Boolean(schede), (el) => el.child(schede))
      .child(bottone("chiedi", "mods/arturo/chiedi.svg", "Cosa posso chiedere", () => apriSuggerimenti()))
      .when(Boolean(s), (el) => el.child(bottone("altra", "plus", "Altra conversazione", () => run("tab.new", { argv: ["claude"] }))))
      .child(bottone("dafare", "panel-right", pannello?.hidden ? "Mostra Da fare" : "Nascondi Da fare", () => run("layout.toggle", { id: "pannello" })));
  }
}

export class Stato {
  init(_p, cx) {
    this.note = [];
    this.scelto = null;
    this.py = "python3";
    this.viste = null;      // le risposte di Claude già viste, per nota
    cx.spawn(async (cx) => {
      const c = await config();
      this.py = c.arturo[0];
      this.scelto = c.note_progetto;
      await this.leggi();
      cx.notify();
      this.guarda(cx);
    });
    // Senza la cartella delle note (nessuna nota ancora) il watch non parte: il timer rilegge e riprova.
    cx.timer.every(30000, (cx) => cx.spawn(async (cx) => { await this.leggi(); cx.notify(); this.guarda(cx); }));
  }

  // Un nota.json che cambia (il velo, o Claude con arturo note) si rilegge subito.
  guarda(cx) {
    if (this.guardo) return;
    this.guardo = true;
    cx.spawn(async (cx) => {
      try {
        for (;;) { await watchFolder(cartellaNote(home())); await this.leggi(); cx.notify(); }
      } catch { this.guardo = false; }
    });
  }

  // Una lettura alla volta; un cambio arrivato durante la lettura ne chiede un'altra subito dopo.
  async leggi() {
    if (this.leggo) { this.ancora = true; return; }
    this.leggo = true;
    try {
      do {
        this.ancora = false;
        const tutte = await leggiTutte(this.py);
        if (!tutte) continue;
        const note = tutte.map((x) => ({ ...x.nota, dove: { ...x.nota.dove, testo_terminale: null } }));
        const nuove = risposteNuove(this.viste, note);
        this.viste = risposteClaude(note);
        this.note = note;
        setShared("arturo.note", note);
        for (const n of nuove) {
          const numero = noteAperte(note, n.progetto).find((x) => x.id === n.id)?.numero;
          const ultima = n.filo.filter((v) => v.chi === "claude").pop();
          notify({ title: numero ? `Claude ha risposto alla nota ${numero}` : "Claude ha risposto a una nota",
            body: ultima?.testo ?? n.testo, level: "info", timeout: 8000, action: { name: "arturo.note" } });
        }
      } while (this.ancora);
    } finally {
      this.leggo = false;
    }
  }

  render() {
    const t = theme();
    const a = agents();
    const n = (st) => a.filter((x) => x.status === st).length;
    const pezzo = (id, c, testo) => h_flex().id(id).gap(7).items_center().child(punto(c, 7)).child(testo);
    const k = tasti();
    const quante = contaNote(this.note, progettoAdesso(this.scelto)).aperte;
    const scorciatoie = `${k.apri} apri un progetto   ${k.prossima} prossima sessione   ${k.impostazioni} impostazioni`;
    return h_flex().size_full().px(18).gap(18).items_center().bg(t.chrome).border_t(1).border_color(t.border).text_size(12).text_color(t.muted)
      .when(a.length === 0, (el) => el.child(pezzo("stato-sessioni", t.idle, "Nessuna sessione aperta")))
      .when(n("blocked") > 0, (el) => el.child(pezzo("stato-aspettano", t.blocked, div().text_color(t.foreground).child(`${n("blocked")} ti aspett${n("blocked") > 1 ? "ano" : "a"}`))))
      .when(n("working") > 0, (el) => el.child(pezzo("stato-lavoro", t.working, `${n("working")} al lavoro`)))
      .when(n("done") > 0, (el) => el.child(pezzo("stato-finito", t.done, `${n("done")} hanno finito`.replace(/^1 hanno/, "1 ha"))))
      .when(a.length > 0 && !n("blocked") && !n("working") && !n("done"), (el) => el.child(pezzo("stato-sessioni", t.idle, a.length > 1 ? `${a.length} sessioni aperte, nessuna ti aspetta` : "1 sessione aperta, non ti aspetta")))
      .when(quante > 0, (el) => el.child(h_flex().id("stato-note").gap(7).items_center().cursor_pointer()
        .text_color(t.foreground).hover((s) => s.text_color(t.accent))
        .on_mouse_down("left", (_e, cx) => cx.stop_propagation())
        .on_click(() => apriElenco())
        .child(punto(ARANCIO, 7)).child(`${quante === 1 ? "1 nota" : `${quante} note`} · ${k.elenco}`)))
      .child(div().flex_1())
      .child(div().id("stato-tasti").text_color(t.dim).child(scorciatoie));
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
    // Largo 520 quando c'è spazio; in una finestra stretta si restringe e le carte vanno a capo (#5077).
    return v_flex().w_full().max_w(520).px(20).pt(24).pb(24).gap(20)
      .child(v_flex().gap(8)
        .child(div().id("benvenuto-titolo").font_family("Arturo Archivo").text_size(22).text_color(t.foreground).child("Cosa facciamo oggi?"))
        .child(div().id("benvenuto-testo").w_full().whitespace_normal().text_size(14).text_color(t.muted)
          .child(haProgetti
            ? "Scegli un progetto a sinistra, oppure parti da una di queste richieste."
            : "Comincia facendo trovare a Claude i tuoi progetti. Oppure scrivigli cosa ti serve, come in una chat.")))
      .child(h_flex().flex_wrap().gap(10)
        // due per riga quando entrano (almeno 200 l'una), altrimenti una sotto l'altra
        .children(scelti.map((s, i) => div().flex_1().min_w(200).child(voce(t, s, i === 0)))))
      .child(h_flex().flex_wrap().gap(10).items_center()
        .child(pulsante("b-nuova", "square-pen", "Nuova richiesta", () => nuova(), !haProgetti ? false : true))
        .child(div().text_size(12.5).text_color(t.dim).child("Altre richieste in Cosa posso chiedere, in alto")))
      // la stessa scelta della barra: qui Nuova richiesta la segue, quindi si vede anche qui
      .when(Boolean(nasceSu(t)), (el) => el.child(nasceSu(t)));
  }
}
