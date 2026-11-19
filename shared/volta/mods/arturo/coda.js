// La Coda delle decisioni (#5720, step 3 del piano della Coda di Volta, 15/11/2026): al posto del
// terminale, tutto ciò che le sessioni e i task aspettano dalla persona, di ogni macchina.
// Dal 18/11/2026 è un elenco e non più una carta per volta (Federico: "non mi permette di capire chiaramente
// quali sono le cose pending, come nella schermata Su cosa lavorare"): i gruppi per chi agisce come nella
// checklist (gruppiCoda di sessioni.js), una riga per carta con le opzioni in pulsanti piccoli, e la riga
// scelta aperta con la domanda intera, le prove e i gesti. Le carte le mette in ordine la barra (volta.js,
// shared arturo.coda, carte() e ordineCoda() di sessioni.js); ⌘⇧J scrive il segno arturo.coda.apri
// (barra.js) e la vista riparte dalla prima riga.
// Tasti sulla riga scelta: ↑↓ scelgono la riga, 1-6 un'opzione, Invio la raccomandata, T apre la sessione,
// F Già fatto, X Scarta, N (o R) Note, C il commento sul pulsante sotto il cursore (16/11/2026: Tab lo prende
// il motore per il fuoco), Esc torna al terminale. Le decisioni dei tasti stanno in sessioni.js (tastoCoda),
// senza Herdr. Le prove (screenshot, video) arrivano qui con volta_carte.py: Herdr mostra solo le immagini
// dentro la cartella dell'app.

import { div, image, svg } from "gpui-kit";
import { v_flex, h_flex, InputState, Input, ScrollHandle } from "gpui-base";
import { theme, shared, run, exec, appHome } from "herdr";
import { ICONA, punto, tasti } from "./comuni.js";
import { terminale } from "./casa.js";
import { config, apriFile, nomeMacchina } from "./dati.js";
import { tastoCoda, passoCoda, cartaDavanti, raccomandata, tipoProva, copiaProva, comandoRisposta, daQuanto, nomeProgetto, testoPiano, etichettaOpzione, CODA_OPZIONI } from "./sessioni.js";
import { comandoGesto, comandoChecklist, GIA_FATTO, SCARTA, NOTE, UMANI, gruppiCoda, ordineVisto } from "./sessioni.js";
import { SPAZIO, TESTO, RAGGIO, PULSANTE, ICONA_MISURA } from "./misure.js";
import { tettoDi, entroDi, daCopiare, PROVA_RIPROVA_MS } from "./sessioni.js";

// Altezza massima di uno screenshot nella riga aperta: il resto della riga deve restare in vista.
const PROVA_H = 300;
// Il pallino della riga, come quello delle sessioni (PALLINO di DESIGN.md).
const PALLINO = 7;
// Il rientro di tutto ciò che sta sotto il titolo: pallino più il suo spazio.
const RIENTRO = PALLINO + SPAZIO.m + 2;
// I pulsanti dentro una riga: più bassi del piccolo, come quelli della checklist (piccolo() di checklist.js).
const CHIP = 24;

export class Coda {
  init(_p, cx) {
    this.at = 0;
    this.chiave = null;   // la riga scelta, per chiave: l'elenco cambia sotto, la scelta resta
    this.scrivo = null;   // il campo aperto: { gesto } (N apre la nota, C il commento del pulsante sotto il cursore)
    this.sopra = null;    // il gesto del pulsante sotto il cursore (on_hover), per C
    this.copie = {};      // destinazione -> "copio" | "ok" | messaggio d'errore
    this.giri = {};       // destinazione -> { n, dopo }: le copie partite e da quando si riprova (daCopiare)
    this.chiusi = new Set();   // i gruppi chiusi, per chiave
    this.scroll = ScrollHandle.new();
    this.py = "python3";
    this.script = `${appHome()}/mods/arturo/volta_carte.py`;
    this.aperta = shared("arturo.coda.apri") ?? 0;
    this.input = InputState.new({ placeholder: "Scrivi e premi Invio" });
    this.input.on("submit", () => {
      const c = this.davanti();
      const testo = this.input.value().trim();
      const gesto = this.scrivo?.gesto ?? NOTE;
      if (c && (testo || gesto !== NOTE)) this.esegui(c, gesto, testo);
    });
    this.handle = cx.focus_handle();
    cx.spawn(async () => { try { this.py = (await config()).arturo[0]; } catch { /* resta python3 */ } });
    // La parte nasce la prima volta che si mostra, cioè al primo ⌘⇧J: la tastiera va subito all'elenco.
    cx.timer.after(150, () => this.handle.focus());
    // ⌘⇧J scrive arturo.coda.apri: prima riga, niente risposta libera, tastiera sull'elenco. La parte
    // resta viva anche nascosta (figlio di uno stack), come la casa: basta guardare il segno.
    cx.timer.every(200, (cx) => {
      const a = shared("arturo.coda.apri") ?? 0;
      if (a === this.aperta) return;
      this.aperta = a;
      this.at = 0;
      this.chiave = null;
      this.scrivo = null;
      this.input.set_value("");
      this.handle.focus();
      this.scroll.scroll_to_item(0);
      cx.notify();
    });
  }

  // Le carte nell'ordine dell'elenco: per gruppo, senza i gruppi chiusi.
  elenco() {
    const l = shared("arturo.coda");
    return ordineVisto(gruppiCoda(Array.isArray(l) ? l : []), this.chiusi);
  }

  davanti() {
    const l = this.elenco();
    this.at = cartaDavanti(l, this.chiave, this.at);
    const c = l[this.at] ?? null;
    this.chiave = c?.chiave ?? null;
    return c;
  }

  // Sceglie una riga col clic: la riga si apre, la tastiera resta sull'elenco.
  scegli(c, cx) {
    if (this.chiave === c.chiave) return;
    this.chiave = c.chiave;
    this.scrivo = null;
    this.input.set_value("");
    this.handle.focus();
    cx.notify();
  }

  // La risposta va alla barra, che la porta alla sessione (volta.js rispondiCoda). La riga dopo prende il
  // suo posto: la carta risposta sparisce quando la sessione riparte.
  rispondi(c, testo) {
    this.scrivo = null;
    this.input.set_value("");
    this.chiave = null;
    run(comandoRisposta(c.chiave, testo));
  }

  // Un gesto (Già fatto, Scarta, Note, o un'opzione) col commento: volta.js gestoDaCoda lo esegue.
  esegui(c, gesto, commento = "") {
    this.scrivo = null;
    this.input.set_value("");
    this.chiave = null;
    run(comandoGesto(c.chiave, gesto, commento));
  }

  // Il campo: N apre la nota, C il commento per il gesto sotto il cursore.
  apriCampo(gesto) {
    this.scrivo = { gesto };
    this.input.focus();
  }

  // Il pulsante sotto il cursore, per C.
  passa(gesto, dentro, cx) {
    if (dentro) this.sopra = String(gesto);
    else if (this.sopra === String(gesto)) this.sopra = null;
    cx.notify();
  }

  // T: la sessione nella sua scheda, con lo stesso gesto del clic sull'elenco. Su una carta UF (#5722) è
  // il gesto Apri: Claude sul task, Gmail per una bozza.
  apri(c) {
    if (c.origine === "uf") return this.rispondi(c, "Apri");
    terminale();
    run(`arturo.volta-${c.chiave}`);
  }

  // Apre o chiude un gruppo.
  giraGruppo(k, cx) {
    if (this.chiusi.has(k)) this.chiusi.delete(k);
    else this.chiusi.add(k);
    cx.notify();
  }

  // Le prove della riga scelta, copiate nella cartella dell'app. Una copia fallita riparte dopo
  // PROVA_RIPROVA_MS, al più PROVA_TENTATIVI volte (daCopiare di sessioni.js, #6112).
  copiaProve(c, cx) {
    for (const p of (c?.prove ?? []).slice(0, 4)) {
      const dest = copiaProva(c, p);
      if (!dest || !daCopiare(this.copie[dest], this.giri[dest])) continue;
      const giro = (this.giri[dest] = { n: (this.giri[dest]?.n ?? 0) + 1, dopo: 0 });
      this.copie[dest] = "copio";
      cx.spawn(async (cx) => {
        let esito;
        try {
          const r = await exec(this.py, [this.script, ...entroDi("prova"), "prova", c.host ?? "qui", String(p), `${appHome()}/${dest}`], { timeout: tettoDi("prova") });
          const d = JSON.parse(String(r.stdout ?? "").trim().split("\n").pop() || "{}");
          esito = d.ok ? "ok" : d.errore || "la copia non è riuscita";
        } catch (e) {
          esito = `la copia non è riuscita: ${String(e?.message ?? e).slice(0, 80)}`;
        }
        // l'errore resta scritto sulla riga; dopo l'attesa la vista si ridisegna e copiaProve riprova
        if (esito !== "ok") giro.dopo = Date.now() + PROVA_RIPROVA_MS;
        this.copie[dest] = esito;
        cx.notify();
        if (esito === "ok") return;
        await cx.sleep(PROVA_RIPROVA_MS);
        cx.notify();
      });
    }
  }

  tasto(e, c, n, cx) {
    if (this.scrivo) {
      if (e.key !== "escape") return;
      this.scrivo = null;
      cx.stop_propagation();
      return cx.notify();
    }
    const a = tastoCoda(e.key, c);
    if (!a) return;
    cx.stop_propagation();
    if (a.azione === "esci") return terminale();
    if (a.azione === "rispondi") return this.rispondi(c, a.testo);
    if (a.azione === "apri") return this.apri(c);
    if (a.azione === "scrivi") { this.apriCampo(NOTE); return cx.notify(); }
    if (a.azione === "gesto") return this.esegui(c, a.gesto);
    if (a.azione === "commenta") {
      if (!this.sopra) return;
      this.apriCampo(this.sopra);
      return cx.notify();
    }
    if (a.azione === "salta" || a.azione === "indietro") {
      this.at = passoCoda(this.at, a.azione === "salta" ? 1 : -1, n);
      this.chiave = this.elenco()[this.at]?.chiave ?? null;
      this.seguiScelta = true;
      cx.notify();
    }
  }

  render(cx) {
    const t = theme();
    const tutte = shared("arturo.coda");
    const gruppi = gruppiCoda(Array.isArray(tutte) ? tutte : []);
    const l = ordineVisto(gruppi, this.chiusi);
    const c = this.davanti();
    if (c) this.copiaProve(c, cx);
    // L'elenco ha figli piatti (intestazioni e righe), così scroll_to_item porta in vista la riga scelta.
    const figli = [];
    let scelta = -1;
    for (const g of gruppi) {
      figli.push(this.intestazione(t, g));
      if (this.chiusi.has(g.chiave)) continue;
      for (const x of g.carte) {
        if (c && x.chiave === c.chiave) scelta = figli.length;
        figli.push(this.riga(t, x, Boolean(c) && x.chiave === c.chiave));
      }
    }
    if (this.seguiScelta && scelta >= 0) { this.seguiScelta = false; this.scroll.scroll_to_item(scelta); }
    const quante = Array.isArray(tutte) ? tutte.length : 0;
    return v_flex().id("coda").track_focus(this.handle).size_full().bg(t.background).rounded(RAGGIO.riquadro)
      .border_1().border_color(t.border).overflow_hidden()
      .on_key_down((e, cx) => this.tasto(e, c, l.length, cx))
      .child(this.testa(t, gruppi, quante))
      .child(quante
        ? v_flex().id("coda-corpo").flex_1().overflow_y_scroll().track_scroll(this.scroll)
          .px(SPAZIO.xxl - SPAZIO.m).pb(SPAZIO.xxl).gap(SPAZIO.xs).children(figli)
        : div().id("coda-corpo").flex_1().child(this.vuota(t)));
  }

  // La testata: il titolo, il conto per gruppo e, se il capo l'ha contata (#5723), la quota di raccomandazioni
  // accettate. I tasti in una riga sola, i principali.
  testa(t, gruppi, quante) {
    const misura = shared("arturo.coda.misura");
    const conti = gruppi.map((g) => `${g.carte.length} ${g.nome.toLowerCase()}`).join(" · ");
    return v_flex().flex_none().px(SPAZIO.xxl).pt(SPAZIO.xxl).pb(SPAZIO.l).gap(SPAZIO.xs + 1)
      .child(h_flex().gap(SPAZIO.l).items_baseline()
        .child(div().font_family("Arturo Archivo").text_size(TESTO.titolo).text_color(t.foreground).child("Coda"))
        .when(quante > 0, (el) => el.child(div().text_size(TESTO.etichetta).text_color(t.muted).child(String(quante))))
        .child(div().flex_1())
        .child(div().text_size(TESTO.nota).text_color(t.dim)
          .child(quante ? "↑↓ scegli · 1-6 o Invio rispondono · T apre · Esc torna" : "Esc torna alla sessione")))
      .when(quante > 0, (el) => el.child(div().truncate().text_size(TESTO.etichetta).text_color(t.muted).child(conti)))
      .when(typeof misura === "string" && misura.length > 0, (el) => el.child(div().text_size(TESTO.nota).text_color(t.dim).child(misura)));
  }

  vuota(t) {
    return v_flex().id("coda-vuota").w_full().pt(SPAZIO.xxl * 2).items_center().gap(SPAZIO.l)
      .child(svg(ICONA("circle-check")).size(40).text_color(t.done ?? t.accent))
      .child(div().text_size(TESTO.testata).text_color(t.foreground).child("Niente ti aspetta"))
      .child(div().text_size(TESTO.etichetta).text_color(t.muted)
        .child(`Quando una sessione chiede qualcosa, la carta arriva qui. ${tasti().coda} la riapre.`));
  }

  // L'intestazione di un gruppo: apre e chiude, col conto. Come filone() della checklist.
  intestazione(t, g) {
    const chiuso = this.chiusi.has(g.chiave);
    return h_flex().id(`coda-g-${g.chiave}`).px(SPAZIO.m).pt(SPAZIO.l).pb(SPAZIO.xs).gap(SPAZIO.s + 2).items_center().cursor_pointer()
      .on_mouse_down("left", (_e, cx) => cx.stop_propagation())
      .on_click((_e, cx) => this.giraGruppo(g.chiave, cx))
      .child(svg(ICONA(chiuso ? "chevron-right" : "chevron-down")).size(12).text_color(t.dim))
      .child(div().text_size(TESTO.etichetta).font_semibold().text_color(g.chiave === "sessioni" ? t.blocked : t.muted).child(g.nome))
      .child(div().text_size(TESTO.nota).text_color(t.dim).child(String(g.carte.length)));
  }

  // Cosa dice una riga: il titolo, la riga sotto e dove viene. Su un task UF il titolo è il task (domanda):
  // il titolo della carta ("Task #5256 · Decidi tu") è solo il gruppo, che l'intestazione dice già.
  testi(c) {
    const uf = c.origine === "uf";
    const bozza = uf && c.fonte === "bozza";
    const quando = c.quando ? daQuanto(new Date(c.quando).toISOString()) : "";
    if (uf && !bozza) {
      return { titolo: testoPiano(c.domanda) || c.titolo || "",
        sotto: "",
        dove: [c.progetto ? nomeProgetto(c.progetto) : "", c.todo?.id ? `#${c.todo.id}` : "", c.esito, c.vecchia ? "il capo non risponde, lettura vecchia" : ""].filter(Boolean).join(" · ") };
    }
    if (bozza) {
      return { titolo: c.titolo ?? "", sotto: testoPiano(c.domanda),
        dove: ["Gmail", c.esito, c.vecchia ? "il capo non risponde, lettura vecchia" : ""].filter(Boolean).join(" · ") };
    }
    return { titolo: c.titolo ?? "", sotto: testoPiano(c.riassunto || c.domanda),
      dove: [c.progetto ? nomeProgetto(c.progetto) : "Senza progetto", nomeMacchina(c.host), quando].filter(Boolean).join(" · ") };
  }

  // Una riga: pallino, titolo, dove viene, la riga sotto e le opzioni in pulsanti piccoli. La riga scelta
  // ha il fondo selected e si apre col dettaglio (dettaglio()).
  riga(t, c, scelta) {
    const umano = UMANI.includes(c.tipo);
    const { titolo, sotto, dove } = this.testi(c);
    const oo = (c.opzioni ?? []).slice(0, CODA_OPZIONI);
    const ri = raccomandata(c);
    const r = String(c.raccomandazione ?? "").trim();
    return v_flex().id(`coda-r-${c.chiave}`).w_full().px(SPAZIO.m).py(SPAZIO.s + 2).gap(SPAZIO.xs + 2).rounded(RAGGIO.riga)
      .when(scelta, (el) => el.bg(t.selected))
      .when(!scelta, (el) => el.hover((s) => s.bg(t.hover)))
      // pallino, titolo e dove: un bersaglio solo, sceglie la riga
      .child(v_flex().id(`coda-rt-${c.chiave}`).w_full().gap(SPAZIO.xs).cursor_pointer()
        .on_mouse_down("left", (_e, cx) => cx.stop_propagation())
        .on_click((_e, cx) => this.scegli(c, cx))
        .child(h_flex().w_full().gap(SPAZIO.m + 2).items_center()
          .child(punto(c.blocco || umano ? t.blocked : t.accent, PALLINO))
          .child(div().flex_1().min_w(0).when(!scelta, (el) => el.truncate()).when(scelta, (el) => el.whitespace_normal())
            .text_size(TESTO.corpo).text_color(t.foreground).child(titolo))
          .when(umano, (el) => el.child(div().flex_none().px(SPAZIO.s + 2).rounded(RAGGIO.controllo).border_1().border_color(t.blocked)
            .text_size(TESTO.nota).text_color(t.blocked).child(`Solo tu: ${c.tipo}`))))
        .child(div().pl(RIENTRO).truncate().text_size(TESTO.nota).text_color(t.muted).child(dove))
        .when(Boolean(sotto) && !scelta, (el) => el.child(div().pl(RIENTRO).truncate().text_size(TESTO.etichetta).text_color(t.muted).child(sotto))))
      .when(scelta, (el) => el.child(this.dettaglio(t, c, sotto)))
      // le opzioni: il numero è il tasto sulla riga scelta; la raccomandata ha il bordo accent
      .when(oo.length > 0, (el) => el.child(h_flex().pl(RIENTRO).gap(SPAZIO.s + 2).items_center().flex_wrap()
        .children(oo.map((o, i) => this.opzione(t, c, o, i, i === ri, scelta)))))
      .when(Boolean(r) && ri < 0, (el) => el.child(h_flex().id(`coda-rac-${c.chiave}`).pl(RIENTRO).gap(SPAZIO.m).items_center().cursor_pointer()
        .on_hover((h, cx) => this.passa(r, h, cx))
        .on_mouse_down("left", (_e, cx) => cx.stop_propagation())
        .on_click(() => this.rispondi(c, r))
        .child(div().flex_none().text_size(TESTO.nota).text_color(t.accent).child(scelta ? "Invio" : "Raccomandata"))
        .child(div().flex_1().min_w(0).when(!scelta, (e) => e.truncate()).text_size(TESTO.etichetta).text_color(t.foreground)
          .child(`${c.capoRac ? "Raccomandata dal capo" : "Raccomandata"}: ${testoPiano(r)}`))))
      .when(scelta, (el) => el.child(this.gesti(t, c)));
  }

  // La riga scelta, aperta: la domanda intera, il riassunto, le doppie, le prove, il campo della nota.
  dettaglio(t, c, sotto) {
    const uf = c.origine === "uf";
    const domanda = testoPiano(c.domanda);
    return v_flex().pl(RIENTRO).gap(SPAZIO.m).pt(SPAZIO.xs)
      .when(!uf && Boolean(domanda) && domanda !== sotto, (el) => el.child(div().w_full().whitespace_normal().text_size(TESTO.riga).text_color(t.foreground).child(domanda)))
      .when(Boolean(c.riassunto || c.esito), (el) => el.child(div().w_full().whitespace_normal().text_size(TESTO.corpo).text_color(t.muted).child(testoPiano(c.riassunto || c.esito))))
      .when((c.doppie ?? []).length > 0, (el) => el.child(div().w_full().whitespace_normal().text_size(TESTO.etichetta).text_color(t.dim)
        .child(`Chiede la stessa cosa anche: ${c.doppie.join(" · ")}`)))
      .when(!(c.opzioni ?? []).length && !String(c.raccomandazione ?? "").trim(), (el) => el.child(div().text_size(TESTO.etichetta).text_color(t.muted)
        .child("Nessuna opzione: N per scrivere la risposta, T per aprire la sessione.")))
      .when((c.prove ?? []).length > 0, (el) => el.child(this.prove(t, c)))
      .when(Boolean(this.scrivo), (el) => el.child(v_flex().gap(SPAZIO.xs)
        .child(div().text_size(TESTO.etichetta).text_color(t.muted)
          .child(this.scrivo?.gesto === NOTE ? "Nota · Invio la manda · Esc annulla"
            : `Commento per: ${etichettaOpzione(this.scrivo?.gesto ?? "", -1)} · Invio esegue · Esc annulla`))
        .child(h_flex().h(PULSANTE.grande).px(SPAZIO.l).gap(SPAZIO.m).items_center()
          .rounded(RAGGIO.riga).border_1().border_color(t.accent).bg(t.raised)
          .child(svg(ICONA("square-pen")).size(ICONA_MISURA.grande).text_color(t.muted))
          .child(Input.new(this.input).flex_1().h_full().text_size(TESTO.riga).text_color(t.foreground)))));
  }

  // I gesti della riga scelta: Già fatto, Scarta, Note, la checklist della ripartenza, Apri.
  gesti(t, c) {
    const uf = c.origine === "uf";
    return h_flex().pl(RIENTRO).gap(SPAZIO.m).pt(SPAZIO.xs).flex_wrap()
      .child(this.gesto(t, "coda-fatto", "circle-check", "Già fatto · F", () => this.esegui(c, GIA_FATTO), GIA_FATTO))
      .child(this.gesto(t, "coda-scarta", "x", "Scarta · X", () => this.esegui(c, SCARTA), SCARTA))
      .child(this.gesto(t, "coda-note", "square-pen", "Note · N", () => this.apriCampo(NOTE), NOTE))
      // la ripartenza di /inizio ancora da mandare: la checklist con le note (checklist.js)
      .when(c.checklist > 0 && shared("arturo.checklist.mandate")?.[c.sessionId] !== c.ripQuando, (el) => el.child(this.gesto(t, "coda-checklist", "circle-check",
        `Su cosa lavorare · ${c.checklist}`, () => run(comandoChecklist(c.chiave)))))
      .child(this.gesto(t, "coda-apri", "terminal", uf ? "Apri · T" : "Apri la sessione · T", () => this.apri(c)));
  }

  // Un'opzione: pulsante piccolo col numero, che sulla riga scelta è il tasto. La raccomandata ha il bordo
  // accent; sulla riga scelta dice anche "Invio".
  opzione(t, c, o, i, consigliata, scelta) {
    return h_flex().id(`coda-o-${c.chiave}-${i + 1}`).flex_none().h(CHIP).px(SPAZIO.m).gap(SPAZIO.s + 2).items_center()
      .rounded(RAGGIO.controllo).cursor_pointer().border_1().border_color(consigliata ? t.accent : t.border)
      .bg(t.background).hover((s) => s.border_color(t.accent))
      .on_hover((h, cx) => this.passa(o, h, cx))
      .on_mouse_down("left", (_e, cx) => cx.stop_propagation())
      .on_click(() => this.rispondi(c, String(o)))
      .when(scelta, (el) => el.child(div().text_size(TESTO.nota).text_color(t.dim).child(String(i + 1))))
      .child(div().text_size(TESTO.etichetta).text_color(t.foreground).child(etichettaOpzione(o, i)))
      .when(consigliata, (el) => el.child(div().text_size(TESTO.nota).text_color(t.accent)
        .child(scelta ? (c.capoRac ? "Raccomandata dal capo · Invio" : "Raccomandata · Invio") : "raccomandata")))
      .when(scelta && this.sopra === String(o), (el) => el.child(div().text_size(TESTO.nota).text_color(t.dim).child("C commento")));
  }

  // Un gesto della riga scelta. Con `nome` (Già fatto, Scarta, Note) il cursore sopra più C apre il commento.
  gesto(t, id, icona, testo, azione, nome = null) {
    return h_flex().id(id).h(PULSANTE.piccolo).px(SPAZIO.m + 2).gap(7).items_center().rounded(RAGGIO.controllo)
      .cursor_pointer().border_1().border_color(t.border).text_color(t.foreground).hover((s) => s.bg(t.hover))
      .when(Boolean(nome), (el) => el.on_hover((h, cx) => this.passa(nome, h, cx)))
      .on_mouse_down("left", (_e, cx) => cx.stop_propagation())
      .on_click(azione)
      .child(svg(ICONA(icona)).size(ICONA_MISURA.piccola))
      .child(div().text_size(TESTO.etichetta).child(testo))
      .when(Boolean(nome) && this.sopra === nome && nome !== NOTE, (el) => el.child(div().text_size(TESTO.nota).text_color(t.dim).child("C commento")));
  }

  // Le prove: lo screenshot in linea appena la copia è arrivata, il video come riga che lo apre.
  prove(t, c) {
    const righe = (c.prove ?? []).slice(0, 4).map((p, i) => {
      const dest = copiaProva(c, p);
      const stato = dest ? this.copie[dest] : "non è un'immagine né un video";
      const nome = String(p).split(/[\\/]/).pop();
      if (stato === "ok" && tipoProva(p) === "immagine") {
        return v_flex().id(`coda-prova-${i}`).gap(SPAZIO.xs)
          .child(image(dest).max_h(PROVA_H).rounded(RAGGIO.riga))
          .child(div().text_size(TESTO.nota).text_color(t.dim).child(nome));
      }
      const testo = stato === "ok" ? `Apri il video ${nome}` : stato === "copio" ? `Prendo ${nome}…` : `${nome}: ${stato ?? "in arrivo"}`;
      return h_flex().id(`coda-prova-${i}`).gap(SPAZIO.m).items_center()
        .when(stato === "ok", (el) => el.cursor_pointer().on_click(() => apriFile(`${appHome()}/${dest}`)))
        .child(svg(ICONA("file-text")).size(ICONA_MISURA.piccola).text_color(t.muted))
        .child(div().text_size(TESTO.etichetta).text_color(stato === "ok" ? t.accent : t.muted).child(testo));
    });
    return v_flex().id("coda-prove").gap(SPAZIO.m).children(righe);
  }
}
