// La testata sopra la sessione, la barra di stato in basso e il benvenuto a finestra vuota. La barra di
// stato tiene d'occhio anche le note sulla finestra: ne mostra il conteggio, che apre l'elenco, e avvisa
// quando Claude risponde a una nota.

import { div, svg } from "gpui-kit";
import { h_flex, v_flex } from "gpui-base";
import { theme, run, agents, spaces, panes, focused, layout, shared, setShared, watchFolder, notify, home, nextCommand } from "herdr";
import { frase, slug, config, statoSpazio, statoScheda, SUGGERIMENTI } from "./dati.js";
import { PING, daRimandare } from "./comandi.js";
import { ICONA, punto, pulsante, colore, apriFinestra, apriElenco, tasti, nasceSu, segno, motoDi, vociMacchina } from "./comuni.js";
import { apriSposta, ICONA_SPOSTA } from "./sposta.js";
import { leggiTutte } from "./notaui.js";
import { macchinaBreve, sintesiTestata } from "./sessioni.js";
import { apriContesto } from "./contestoui.js";
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

// La testata (12/11/2026 sera, Federico: "si affastellano tante cose, non si capisce"): a sinistra il
// titolo del progetto, che non si taglia, e sotto cosa succede adesso nella sessione aperta, in al più
// cinque parole (la sintesi di titolo-sessione.py, sintesiTestata di sessioni.js), con macchina e stato.
// A destra solo icone: Sposta su, Contesto del progetto, Da fare. Le schede stanno nella fila sotto
// (Schede), non più qui.
export class Testata {
  render() {
    const t = theme();
    const s = spaces().find((x) => x.active);
    const tab = s?.tabs.find((x) => x.active);
    // lo stato della scheda aperta, non quello dello spazio: uno spazio "ti aspetta" se una sola delle
    // sue schede aspetta, e la testata lo diceva sopra una sessione che lavorava
    const st = statoScheda(s, tab);
    const f = st ? frase(st) : null;
    const pannello = trova(layout(), "pannello");
    // La macchina dove gira la sessione della scheda aperta (shared arturo.volta.dove di volta.js): una
    // scheda che aggancia una sessione di un'altra macchina dice quella; le altre sono di questa macchina.
    const f2 = focused();
    const term = (f2?.terminal && panes().some((p) => p.terminal === f2.terminal && p.tab === tab?.id)) ? f2.terminal
      : panes().find((p) => p.tab === tab?.id)?.terminal;
    const dv = shared("arturo.volta.dove");
    const macchina = tab ? (dv?.schede?.[term] ?? dv?.qui ?? null) : null;
    const davanti = shared("arturo.volta.davanti");
    const sintesi = tab ? sintesiTestata(davanti, tab.named ? tab.name : null) : null;
    const progetto = s ? (shared("arturo.progetti")?.[slug(s.name)]?.titolo ?? s.name) : "Volta";
    const bottone = (id, icona, testo, azione) => h_flex().id(id).flex_none().h(30).w(30).justify_center().items_center().rounded(7).cursor_pointer()
      .text_color(t.muted).hover((st) => st.bg(t.hover).text_color(t.foreground))
      .on_mouse_down("left", (_e, cx) => cx.stop_propagation()).on_click(azione)
      .tooltip(testo)
      .child(svg(icona.includes("/") ? icona : ICONA(icona)).size(15));
    return h_flex().size_full().bg(t.chrome).pl(20).pr(12).gap(12).items_center()
      .child(v_flex().flex_1().min_w(0).gap(2)
        .child(div().id("testata-titolo").flex_none().font_family("Arturo Archivo").text_size(16).text_color(t.foreground).child(progetto))
        .when(Boolean(sintesi) || Boolean(f) || Boolean(macchina), (el) => el.child(h_flex().id("testata-stato").min_w(0).gap(7).items_center()
          .when(Boolean(f), (e) => e.child(segno(colore(t, f.colore), motoDi(f.colore, st === "blocked"), 7)))
          .when(Boolean(sintesi), (e) => e.child(div().id("testata-sintesi").flex_none().text_size(12.5).text_color(t.foreground).child(sintesi)))
          .child(div().id("testata-dove").min_w(0).truncate().text_size(12).text_color(t.dim)
            .child(rigaDove(Boolean(sintesi), macchina ? macchinaBreve(macchina) : null, f ? f.testo : null))))))
      // "Sposta su un'altra macchina" (sposta.js): per la sessione in background della scheda in primo
      // piano, quando Volta conosce un'altra macchina. Durante lo spostamento resta acceso e non riapre.
      .when(Boolean(davanti) && davanti.tipo === "background" && vociMacchina().length > 1, (el) => el.child(davanti.sposto
        ? h_flex().id("sposta-in-corso").flex_none().h(30).px(8).gap(6).items_center().text_size(12).text_color(t.working)
          .child(svg(ICONA_SPOSTA).size(15)).child(div().child("La sposto…"))
        : bottone("sposta", ICONA_SPOSTA, "Sposta la sessione su un'altra macchina", () => apriSposta(davanti))))
      // il contesto del progetto aperto: cosa legge Claude quando lo apri (contestoui.js)
      .when(Boolean(s) && !s.machine && Boolean(s.named), (el) => el.child(bottone("contesto", "layers", "Contesto del progetto", () => apriContesto(s.name))))
      .child(bottone("dafare", "panel-right", pannello?.hidden ? "Mostra Da fare" : "Nascondi Da fare", () => run("layout.toggle", { id: "pannello" })));
  }
}

// La fila delle schede sotto la testata (parte "schede" del layout), disegnata come schede vere: la
// scheda aperta ha il fondo del terminale e si attacca alla linea sotto, le altre restano sul fondo della
// finestra. Ogni scheda ha il segno del suo stato e, col puntatore sopra o da aperta, la X che la chiude
// come ⌘W (arturo.volta-chiudi: una sessione di Volta va in congedo). In fondo il + delle tessere (⌘T).
export class Schede {
  init() { this.sopra = null; }

  render() {
    const t = theme();
    const s = spaces().find((x) => x.active);
    const tabs = s?.tabs ?? [];
    const fondo = t.background ?? t.surface;
    const scheda = (x, i) => {
      const fx = x.status ? frase(x.status) : null;
      const vediX = x.active || this.sopra === x.id;
      return h_flex().id(`scheda-${x.id}`).flex_none().max_w(LARGA).min_w(0).h(32).pl(12).pr(6).gap(7).items_center().rounded_t(8).cursor_pointer()
        .border_t(1).border_l(1).border_r(1)
        .when(x.active, (el) => el.relative().bg(fondo).border_color(t.border).text_color(t.foreground)
          // la linea accesa in alto: la scheda aperta si vede anche con la coda dell'occhio
          .child(div().id(`scheda-acc-${x.id}`).absolute().top(0).left(8).right(8).h(2).rounded_full().bg(t.accent)))
        .when(!x.active, (el) => el.border_color(t.chrome).text_color(t.muted).hover((st) => st.bg(t.hover)))
        .on_hover((h, cx) => { if (h) this.sopra = x.id; else if (this.sopra === x.id) this.sopra = null; cx.notify(); })
        .on_mouse_down("left", (_e, cx) => cx.stop_propagation())
        .on_click(() => run("tab.select", { id: x.id }))
        .when(Boolean(fx), (el) => el.child(segno(colore(t, fx.colore), motoDi(fx.colore, x.status === "blocked"), 7)))
        .child(div().min_w(0).truncate().text_size(12.5).child(nomeScheda(x, i)))
        .child(div().id(`scheda-x-${x.id}`).flex_none().p(3).rounded(5)
          .when(!vediX, (el) => el.invisible())
          .when(vediX, (el) => el.cursor_pointer().hover((st) => st.bg(t.selected))
            .on_mouse_down("left", (_e, cx) => cx.stop_propagation())
            .on_click((_e, cx) => { cx.stop_propagation(); chiudiScheda(x); }))
          .tooltip("Chiudi la scheda")
          .child(svg(ICONA("x")).size(11).text_color(t.dim)));
    };
    return h_flex().size_full().bg(t.chrome).pl(14).pr(12).gap(2).items_end().border_b(1).border_color(t.border)
      .children(tabs.map(scheda))
      .child(h_flex().id("scheda-nuova").flex_none().mb(4).h(26).w(26).justify_center().items_center().rounded(6).cursor_pointer()
        .text_color(t.dim).hover((st) => st.bg(t.hover).text_color(t.foreground))
        .on_mouse_down("left", (_e, cx) => cx.stop_propagation())
        .on_click(() => run("arturo.casa"))
        .tooltip("Nuova scheda")
        .child(svg(ICONA("plus")).size(13)));
  }
}

// La larghezza massima di una scheda: oltre, il nome si taglia.
const LARGA = 240;

// Il nome di una scheda: quello che le ha dato Herdr o Volta (il titolo della sessione), altrimenti un numero.
export const nomeScheda = (x, i) => (x.named && x.name ? x.name : `Scheda ${i + 1}`);

// La X di una scheda: la porta davanti e manda il comando di ⌘W, così fa lo stesso (congedo di una
// sessione di Volta, chiusura di Herdr per il resto).
function chiudiScheda(x) {
  run(`arturo.volta-chiudi-${x.id}`);
}

// Dopo la sintesi, macchina e stato in grigio: "· MacBook Air · Claude sta lavorando".
export function rigaDove(conSintesi, macchina, stato) {
  const r = [macchina, stato].filter(Boolean).join(" · ");
  return r && conSintesi ? `· ${r}` : r;
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
    // Con la barra nascosta (⌘B) i comandi non li legge nessuno: Herdr li consegna solo alle parti
    // mostrate, e i tasti (⌘O, ⌘T, ⌘⇧N) non facevano niente. La barra di stato resta mostrata: legge
    // i comandi anche lei e agisce solo a barra nascosta (daRimandare).
    cx.spawn(async (cx) => {
      for (;;) {
        const c = await nextCommand();
        try { await this.rimanda(c, cx); } catch { /* il comando dopo si legge lo stesso */ }
      }
    });
  }

  // Mostra la barra, aspetta che riceva i comandi e le rimanda `c`. Che li riceve lo dice lei: risponde
  // al comando di controllo scrivendo l'ora in shared arturo.barra.viva. Al massimo 3 secondi.
  async rimanda(c, cx) {
    if (!daRimandare(c, Boolean(trova(layout(), "sidebar")?.hidden))) return;
    const da = Date.now();
    run("layout.toggle", { id: "sidebar" });
    for (let i = 0; i < 20; i++) {
      run(`arturo.${PING}`);
      await cx.sleep(150);
      if (Number(shared("arturo.barra.viva")) >= da) return run(`arturo.${c}`);
    }
    notify({ title: "La barra di sinistra non risponde", body: "Mostrala con il suo tasto e riprova.", level: "warning" });
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
    const scorciatoie = `${k.apri} cerca   ${k.giro} giro delle sessioni   ${k.prossima} chi ti aspetta   ${k.impostazioni} impostazioni`;
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
        // la nascita la fa la barra: il benvenuto sparisce appena nasce uno spazio (suggerimenti.js)
        .child(pulsante("b-nuova", "square-pen", "Nuova richiesta", () => run("arturo.nuova"), !haProgetti ? false : true))
        .child(div().text_size(12.5).text_color(t.dim).child("Altre richieste in Cosa posso chiedere, in alto")))
      // la stessa scelta della barra: qui Nuova richiesta la segue, quindi si vede anche qui
      .when(Boolean(nasceSu(t)), (el) => el.child(nasceSu(t)));
  }
}
