// La colonna di sinistra: il marchio, i progetti, il piede.

import { div, image, svg } from "gpui-kit";
import { h_flex, v_flex } from "gpui-base";
import { theme, run, agents, spaces, window, shared, setShared, nextCommand, updates, notify, layout } from "herdr";
import { todo, progetti, apri, nuova, nuovaScheda, conversazione, libera, slug, cartelle, progettiMemoria, statiQui, frase, SUGGERIMENTI } from "./dati.js";
import { STACK, CASA, senzaTessere } from "./tessere.js";
import { terminale } from "./casa.js";
import { ICONA, pulsante, pulsanteIcona, segnaleImpostazioni, apriFinestra, apriNota, apriElenco, nasceSu, apriSceltaMacchina, tasti, movimento, giraMovimento, apriImpostazioni } from "./comuni.js";
import { SPAZIO, MARGINE, RAGGIO, TESTO, PULSANTE } from "./misure.js";
import { APERTE } from "./nota.js";
import { apriGuida } from "./guida.js";
import { apriSuggerimenti, esegui } from "./suggerimenti.js";
import { apriRevisione } from "./revisione.js";
import { revisione, settimanaDi } from "./settimana.js";
import { Volta } from "./volta.js";
import { rigaMod, decodifica } from "./sessioni.js";
import { instrada } from "./comandi.js";
import { pastigliaTutto } from "./sposta.js";
import { apriContesto } from "./contestoui.js";

export class Marchio {
  render() {
    const t = theme();
    const aspetta = agents().some((a) => a.status === "blocked") || Object.values(statiQui()).includes("aspetta");
    const stella = image("mods/arturo/stella.svg").size(20).flex_none();
    const mac = window()?.platform === "macos" && !window()?.fullscreen;
    return h_flex().size_full().bg(t.chrome).pl(mac ? 84 : MARGINE + SPAZIO.m).pr(14).gap(10).items_center()
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
    // lo spazio delle sessioni senza progetto si chiama "Senza progetto" (12/11/2026): rinomina quelli "Volta"
    libera();
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
    else if (c === "conversazione") { if (arg) this.lungo(c, cx, () => conversazione(arg)); }
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
    // Un layout senza tessere (fatto a mano, di Herdr) apre la sessione nuova, la prima tessera (#5456).
    else if (c === "casa" && senzaTessere(layout())) this.lungo("volta-nuova", cx, () => nuovaScheda());
    else if (c === "casa") { run("layout.select", { stack: STACK, child: CASA }); setShared("arturo.casa.apri", Date.now()); }
    else if (c === "casa-chiudi") terminale();
    else if (c === "volta-nuova") this.lungo(c, cx, () => nuovaScheda());
    else if (c === "volta-giro") this.volta.giro(arg, cx);
    else if (c === "volta-chiudi") this.volta.chiudiDavanti(cx, arg);
    else if (c === "contesto") apriContesto(arg);
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
    if (this.vista === null && !this.errore && !v) vuoto = div().id("progetti-vuoto").px(MARGINE + SPAZIO.m).py(SPAZIO.s + 2).text_size(TESTO.corpo).text_color(t.muted).child("Leggo i tuoi progetti…");
    else if (!quanti && this.vista !== null) vuoto = v_flex().px(MARGINE).gap(SPAZIO.l)
      .child(div().px(4).text_size(13).text_color(t.muted).whitespace_normal()
        .child(this.errore ? "Non riesco a leggere i todo di Arturo. Le conversazioni funzionano lo stesso." : "Non hai ancora progetti. Claude può cercarli sul tuo computer e proporteli."))
      .when(!this.errore, (el) => el.child(pulsante("trova", "search", "Trova i miei progetti", () => esegui(SUGGERIMENTI[0]), true)));
    // In cima (fase 4 del piano di design, #5371): il campo "Cerca o chiedi" apre la ricerca (⌘K), che trova
    // sessioni e progetti e manda anche una richiesta scritta; accanto, Nuova richiesta come icona. "Apri un
    // progetto" stava qui come secondo pulsante: oggi lo fanno la ricerca e le tessere di ⌘T.
    const forte = quanti > 0 || Boolean(this.errore);
    const campo = h_flex().id("cerca").flex_1().min_w(0).h(PULSANTE.grande).px(SPAZIO.l).gap(SPAZIO.m).items_center()
      .rounded(RAGGIO.riga).border_1().border_color(t.border).bg(t.raised).cursor_pointer()
      .hover((s) => s.bg(t.hover))
      .on_mouse_down("left", (_e, cx) => cx.stop_propagation())
      .on_click(() => apriFinestra())
      .accessibility_label("Cerca o chiedi")
      .child(svg(ICONA("search")).size(15).flex_none().text_color(t.muted))
      .child(div().flex_1().min_w(0).truncate().text_size(TESTO.corpo).text_color(t.muted).child("Cerca o chiedi"))
      .child(div().flex_none().text_size(TESTO.nota).text_color(t.dim).child(tasti().apri));
    const fila = [dove, tutto].filter(Boolean);
    // overflow_hidden sulla radice: quello che non entra si taglia qui e la barra non chiede più altezza
    // del suo posto nel layout.
    return v_flex().size_full().overflow_hidden().bg(t.chrome)
      .child(v_flex().id("barra-cima").flex_none().px(MARGINE).pt(SPAZIO.s).pb(SPAZIO.l).gap(SPAZIO.m)
        .on_size_change((m) => {
          const v = { altezza: Math.round(m.height) };
          if (shared("arturo.misura.cima")?.altezza !== v.altezza) setShared("arturo.misura.cima", v);
        })
        .child(h_flex().gap(SPAZIO.m).items_center()
          .child(campo)
          .child(pulsanteIcona("nuova", "square-pen", `Nuova richiesta · ${tasti().tessere}`, () => nuova(), { forte })))
        .when(fila.length > 0, (el) => el.child(h_flex().flex_wrap().gap(SPAZIO.s + 2).children(fila))))
      .when(Boolean(vuoto), (el) => el.child(vuoto))
      .when(Boolean(v), (el) => el.child(v));
  }
}

// Le note ancora da guardare (aperte o prese da Claude), da shared arturo.note della barra di stato.
const aperteNote = () => (shared("arturo.note") ?? []).filter((n) => APERTE.has(n?.stato)).length;

export class Piede {
  // Una fila di icone alta PIEDE px (fase 4, #5371): prima erano cinque righe in 192 px, che toglievano
  // spazio all'elenco delle sessioni. Il nome di ogni voce sta nel suggerimento; Note porta il conto delle
  // note da guardare; Impostazioni un pallino (rosso per un avviso del mod, accento per un'app nuova
  // pronta) e, nel suo menu, la versione del mod.
  render() {
    const t = theme();
    const note = aperteNote();
    return h_flex().size_full().bg(t.chrome).border_t(1).border_color(t.border).px(MARGINE - SPAZIO.s).gap(SPAZIO.xs).items_center()
      .child(pulsanteIcona("chiedi", "mods/arturo/chiedi.svg", "Cosa posso chiedere", () => apriSuggerimenti(), { misura: "piccolo" }))
      .child(pulsanteIcona("settimana", "mods/arturo/settimana.svg", "La settimana", () => apriRevisione(), { misura: "piccolo" }))
      // Le note alla maniera di Agentation: il clic apre l'elenco; la nota nuova parte dallo scatto della
      // finestra, col tasto scritto nel suggerimento (#5156).
      .child(pulsanteIcona("note", "pin", `Note · ${tasti().nota} nuova · ${tasti().elenco} elenco`, () => apriElenco(), { misura: "piccolo", numero: note }))
      .child(pulsanteIcona("guida", "mods/arturo/guida.svg", "Guida", () => apriGuida(), { misura: "piccolo" }))
      .child(div().flex_1())
      // Un clic apre il menu col movimento, le impostazioni dell'app (⌘, le apre dirette) e la versione del mod.
      .child(pulsanteIcona("impostazioni", "settings", `Impostazioni · ${rigaMod(shared("arturo.mod"))?.testo ?? tasti().impostazioni}`, () => apriImpostazioni(),
        { misura: "piccolo", segnale: segnaleImpostazioni(Boolean(updates().app.ready)) }));
  }
}
