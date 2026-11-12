// La colonna di sinistra: il marchio, i progetti, il piede.

import { div, image, svg } from "gpui-kit";
import { h_flex, v_flex } from "gpui-base";
import { theme, run, agents, spaces, window, shared, setShared, nextCommand, updates, notify } from "herdr";
import { todo, progetti, apri, nuova, nuovaScheda, slug, cartelle, progettiMemoria, statiQui, frase, SUGGERIMENTI } from "./dati.js";
import { STACK, CASA } from "./tessere.js";
import { terminale } from "./casa.js";
import { ICONA, punto, pulsante, colore, apriFinestra, apriNota, apriElenco, nasceSu, apriSceltaMacchina, tasti, movimento, giraMovimento, apriImpostazioni } from "./comuni.js";
import { APERTE } from "./nota.js";
import { apriGuida } from "./guida.js";
import { apriSuggerimenti, esegui } from "./suggerimenti.js";
import { apriRevisione } from "./revisione.js";
import { revisione, settimanaDi } from "./settimana.js";
import { Volta } from "./volta.js";
import { rigaMod, decodifica } from "./sessioni.js";
import { instrada } from "./comandi.js";
import { pastigliaTutto } from "./sposta.js";

export class Marchio {
  render() {
    const t = theme();
    const aspetta = agents().some((a) => a.status === "blocked") || Object.values(statiQui()).includes("aspetta");
    const stella = image("mods/arturo/stella.svg").size(20).flex_none();
    const mac = window()?.platform === "macos" && !window()?.fullscreen;
    return h_flex().size_full().bg(t.chrome).pl(mac ? 84 : 18).pr(14).gap(10).items_center()
      .child(aspetta && movimento() ? stella.loop("opacity", { from: 0.3, to: 1, period: 1100 }) : stella)
      .child(div().id("marchio-nome").font_family("Arturo Archivo").text_size(17).text_color(t.foreground).child("Volta"));
  }
}

export class Barra {
  init(_p, cx) {
    this.vista = null;
    this.errore = null;
    this.firma = "";
    // In cima alla barra: tutte le sessioni di tutte le macchine (Volta, volta.js).
    this.volta = new Volta();
    this.volta.init(cx);
    // All'avvio lo stack "lavoro" mostra il terminale anche se .state/ ha salvato le tessere (sonda D2 del
    // 12/11): la barra c'è sempre, la parte Casa nasce solo a ⌘T.
    terminale();
    this.carica(cx);
    // La guida si apre da sola la prima volta, per chi arriva da /setup e per chi usa già Arturo.
    this.primoAvvio = !shared("arturo.guida");
    if (this.primoAvvio) cx.timer.after(900, () => { setShared("arturo.guida", "vista"); apriGuida(); });
    cx.timer.every(30000, (cx) => this.carica(cx));
    // Quando una sessione cambia stato, i todo possono essere cambiati: si rileggono.
    cx.timer.every(3000, (cx) => {
      // Cambiano i conti della barra anche un todo scritto dal pannello (shared arturo.scritto) e una
      // sessione in background di questa macchina, che Herdr non vede (statiQui).
      const f = agents().map((a) => `${a.address}:${a.status}`).join(",") + `|${JSON.stringify(statiQui())}|${shared("arturo.scritto") ?? ""}`;
      if (f !== this.firma) { this.firma = f; this.carica(cx); }
    });
    // I comandi "arturo.<nome>" (comandi.js dice cosa chiede ognuno). Un comando che si rompe non ferma
    // il ciclo: senza il try la barra smetteva di rispondere ai tasti fino al riavvio.
    cx.spawn(async (cx) => {
      for (;;) {
        const c = await nextCommand();
        try { this.comando(instrada(c), cx); } catch (e) { this.rotto(c, e); }
        cx.notify();
      }
    });
  }

  rotto(c, e) {
    notify({ title: "Un comando di Volta non è riuscito", body: `arturo.${c}: ${String(e?.message ?? e).slice(0, 160)}`, level: "error" });
  }

  // Un comando lungo (una nascita, lo scatto della finestra per una nota) parte e il ciclo non lo
  // aspetta: con l'await una sessione che nasce in sei minuti teneva in coda tutti i comandi dopo.
  lungo(c, cx, lavoro) {
    cx.spawn(async (cx) => {
      try { await lavoro(); } catch (e) { this.rotto(c, e); }
      cx.notify();
    });
  }

  // Esegue un comando già letto da instrada(). Niente await: i lunghi passano da lungo().
  comando({ verbo, arg }, cx) {
    const c = verbo;
    if (c === "ci-sei") setShared("arturo.barra.viva", Date.now());
    else if (c === "apri") apriFinestra();
    else if (c === "progetto") { if (arg) this.lungo(c, cx, () => apri(arg)); }
    else if (c === "chiedi") apriSuggerimenti();
    else if (c === "suggerimento") { const s = SUGGERIMENTI.find((x) => x.id === arg); if (s) this.lungo(c, cx, () => esegui(s)); }
    else if (c === "settimana") apriRevisione();
    else if (c === "guida") apriGuida(arg);
    else if (c === "nuova") this.lungo(c, cx, () => (arg ? nuova(decodifica(arg)) : nuova()));
    else if (c === "dove-scelta") apriSceltaMacchina();
    else if (c === "dove") setShared("arturo.dove", arg);
    else if (c === "nota") this.lungo(c, cx, () => apriNota(arg));
    else if (c === "note") apriElenco();
    else if (c === "versione") { const m = shared("arturo.mod"); notify({ title: rigaMod(m)?.testo ?? "Il mod non ha una versione", body: m?.motivo ?? `Ultimo controllo: ${m?.esito ?? "mai"}.`, level: "info" }); }
    else if (c === "gruppi") setShared("arturo.volta.gruppi", arg);
    else if (c === "movimento") giraMovimento(arg);
    else if (c === "impostazioni") apriImpostazioni();
    // ⌘T: le tessere al posto del terminale; il segno dice alla parte Casa di ripartire dal campo vuoto.
    else if (c === "casa") { run("layout.select", { stack: STACK, child: CASA }); setShared("arturo.casa.apri", Date.now()); }
    else if (c === "casa-chiudi") terminale();
    else if (c === "volta-nuova") this.lungo(c, cx, () => nuovaScheda());
    else if (c === "volta-giro") this.volta.giro(arg, cx);
    else if (c === "volta-menu") this.volta.menuId(arg);
    else if (c === "volta-altro") this.volta.altroId(arg, cx);
    else if (c === "volta-cambia") this.volta.cambiaComando(arg, cx);
    else if (c === "volta-gesto") this.volta.gestoId(arg.verbo, arg.id, cx);
    else if (c === "volta-sposta") this.volta.spostaId(arg.macchina, arg.id, cx);
    else if (c === "volta-spostatutto") this.volta.spostaTutto(arg, cx);
    else if (c === "volta") this.volta.premiId(arg, cx);
  }

  carica(cx) {
    if (this.inCorso) return;
    this.inCorso = true;
    cx.spawn(async (cx) => {
      const r = await todo(["--json"]);
      // I progetti dalla memoria di Arturo. Con un Arturo che non ha ancora il comando: le cartelle dei
      // progetti e le righe di stato del suo archivio, come prima (una fonte esterna può non averle).
      this.memoria = await progettiMemoria();
      if (!this.memoria) {
        this.cartelle = await cartelle();
        const st = await todo(["progetti", "--json"]);
        this.stati = st.ok ? st.json?.stati ?? {} : {};
      }
      this.inCorso = false;
      if (r.ok) {
        this.vista = r.json;
        this.errore = null;
        // Per la testata e il pannello Da fare: il nome per la fonte, il titolo e la riga di ogni progetto.
        const mappa = {};
        const tutti = progetti(this.vista, this.extra());
        this.quanti = tutti.length;
        for (const p of tutti) {
          mappa[p.chiave] = { chiave: p.chiave, nome: p.nome ?? p.chiave, titolo: p.titolo, riga: p.calcolato ? "" : (p.riga ?? "") };
          // Uno spazio aperto col nome alternativo trova lo stesso progetto.
          for (const a of p.alias ?? []) if (!(a in mappa)) mappa[a] = mappa[p.chiave];
        }
        setShared("arturo.progetti", mappa);
        // Per le tessere di ⌘T (casa.js): i progetti nell'ordine della barra, con la frase dello stato.
        setShared("arturo.casa.progetti", tutti.map((p) => ({ chiave: p.chiave, titolo: p.titolo, frase: frase(p.stato, p) })));
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
    return { cartelle: this.cartelle ?? [], stati: this.stati ?? {}, memoria: this.memoria ?? null };
  }

  // Una colonna sola (12/11/2026, scelta di Federico): sotto i pulsanti, l'elenco di Volta per progetto a
  // tutta altezza. La sezione dei progetti aperti ("Adesso") doppiava i gruppi e lasciava all'elenco
  // metà colonna: un progetto senza sessioni si apre da Apri un progetto. I progetti si leggono ancora
  // qui (carica), per i titoli in shared arturo.progetti e per lo stato vuoto.
  render(cx) {
    const t = theme();
    // progetti() costa (cento e più voci, spazi di Herdr): il conto lo scrive carica()
    const quanti = this.quanti ?? 0;
    const v = this.volta ? this.volta.render(cx) : null;
    const dove = nasceSu(t);
    // "Sposta tutto su…" sotto "Nasce su" (Federico, 12/11/2026): le sessioni delle altre macchine su una sola.
    const tutto = dove && this.volta ? pastigliaTutto(t, this.volta.vis()?.sessioni ?? [], this.volta.inCoda()) : null;
    let vuoto = null;
    if (this.vista === null && !this.errore && !v) vuoto = div().id("progetti-vuoto").px(18).py(6).text_size(13).text_color(t.muted).child("Leggo i tuoi progetti…");
    else if (!quanti && this.vista !== null) vuoto = v_flex().px(14).gap(10)
      .child(div().px(4).text_size(13).text_color(t.muted).whitespace_normal()
        .child(this.errore ? "Non riesco a leggere i todo di Arturo. Le conversazioni funzionano lo stesso." : "Non hai ancora progetti. Claude può cercarli sul tuo computer e proporteli."))
      .when(!this.errore, (el) => el.child(pulsante("trova", "search", "Trova i miei progetti", () => esegui(SUGGERIMENTI[0]), true)));
    // overflow_hidden sulla radice: quello che non entra si taglia qui e la barra non chiede più altezza
    // del suo posto nel layout (senza, il piede sotto perdeva 89 px dei suoi 190).
    return v_flex().size_full().overflow_hidden().bg(t.chrome)
      .child(v_flex().id("barra-cima").flex_none().px(14).pt(6).pb(14).gap(8)
        .on_size_change((m) => {
          const v = { altezza: Math.round(m.height) };
          if (shared("arturo.misura.cima")?.altezza !== v.altezza) setShared("arturo.misura.cima", v);
        })
        .child(pulsante("nuova", "square-pen", "Nuova richiesta", () => nuova(), quanti > 0 || Boolean(this.errore)))
        .child(pulsante("apri", "folder", "Apri un progetto", () => apriFinestra()))
        .when(Boolean(dove), (el) => el.child(dove))
        .when(Boolean(tutto), (el) => el.child(tutto)))
      .when(Boolean(vuoto), (el) => el.child(vuoto))
      .when(Boolean(v), (el) => el.child(v));
  }
}

// Le note ancora da guardare (aperte o prese da Claude), da shared arturo.note della barra di stato.
const aperteNote = () => (shared("arturo.note") ?? []).filter((n) => APERTE.has(n?.stato)).length;

export class Piede {
  render() {
    const t = theme();
    const voce = (id, icona, testo, azione) => h_flex().id(id).h(32).px(10).gap(10).items_center().rounded(8).cursor_pointer()
      .text_color(t.muted).hover((s) => s.bg(t.hover).text_color(t.foreground)).on_click(azione)
      .child(svg(icona.includes("/") ? icona : ICONA(icona)).size(15)).child(div().flex_1().text_size(13).child(testo));
    return v_flex().size_full().bg(t.chrome).border_t(1).border_color(t.border).px(8).py(8).gap(2)
      .child(voce("chiedi", "mods/arturo/chiedi.svg", "Cosa posso chiedere", () => apriSuggerimenti()))
      .child(voce("settimana", "mods/arturo/settimana.svg", "La settimana", () => apriRevisione()))
      // Le note alla maniera di Agentation: il clic apre l'elenco, i due tasti stanno scritti accanto
      // perché la nota nuova parte dallo scatto della finestra, non da un pulsante (#5156).
      .child(voce("note", "pin", "Note", () => apriElenco())
        .when(aperteNote() > 0, (el) => el.child(div().text_size(12).text_color(t.accent).child(String(aperteNote()))))
        .child(div().text_size(11.5).text_color(t.dim).child(`${tasti().nota} nuova · ${tasti().elenco}`)))
      .child(voce("guida", "mods/arturo/guida.svg", "Guida", () => apriGuida()))
      // Un clic apre il menu con l'interruttore del movimento e le impostazioni dell'app (⌘, le apre dirette).
      .child(voce("impostazioni", "settings", "Impostazioni", () => apriImpostazioni())
        .when(Boolean(rigaMod(shared("arturo.mod"))), (el) => { const r = rigaMod(shared("arturo.mod")); return el.child(div().text_size(11.5).text_color(r.avviso ? t.blocked : t.dim).child(r.testo)); })
        .when(Boolean(updates().app.ready), (el) => el.child(punto(t.accent, 7))));
  }
}
