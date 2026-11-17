// La Coda delle decisioni (#5720, step 3 del piano della Coda di Volta, 15/11/2026): al posto del
// terminale, una carta per volta di tutto ciò che le sessioni aspettano dalla persona, di ogni macchina.
// Le carte le mette in ordine la barra (volta.js, shared arturo.coda, carte() e ordineCoda() di
// sessioni.js); ⌘⇧J scrive il segno arturo.coda.apri (barra.js) e la vista riparte dalla prima carta.
// Tasti: 1-6 scelgono un'opzione, Invio accetta la raccomandazione, → salta, ← torna indietro, T apre la
// sessione, F Già fatto, X Scarta, N (o R) Note, C il commento sul pulsante sotto il cursore (16/11/2026:
// Tab lo prende il motore per il fuoco), Esc torna al terminale. Le decisioni dei tasti stanno in
// sessioni.js (tastoCoda), senza Herdr. Le prove (screenshot, video) arrivano qui con volta_carte.py:
// Herdr mostra solo le immagini dentro la cartella dell'app.

import { div, image, svg } from "gpui-kit";
import { v_flex, h_flex, InputState, Input } from "gpui-base";
import { theme, shared, run, exec, appHome } from "herdr";
import { ICONA, punto, tasti } from "./comuni.js";
import { terminale } from "./casa.js";
import { config, apriFile, nomeMacchina } from "./dati.js";
import { tastoCoda, passoCoda, cartaDavanti, raccomandata, tipoProva, copiaProva, comandoRisposta, daQuanto, nomeProgetto, testoPiano, etichettaOpzione, CODA_OPZIONI } from "./sessioni.js";
import { comandoGesto, comandoChecklist, GIA_FATTO, SCARTA, NOTE } from "./sessioni.js";
import { SPAZIO, TESTO, RAGGIO, PULSANTE, ICONA_MISURA } from "./misure.js";

// Altezza massima di uno screenshot nella carta: il resto della carta deve restare in vista.
const PROVA_H = 300;

export class Coda {
  init(_p, cx) {
    this.at = 0;
    this.chiave = null;   // la carta davanti, per chiave: l'elenco cambia sotto, la carta resta
    this.scrivo = null;   // il campo aperto: { gesto } (N apre la nota, C il commento del pulsante sotto il cursore)
    this.sopra = null;    // il gesto del pulsante sotto il cursore (on_hover), per C
    this.copie = {};      // destinazione -> "copio" | "ok" | messaggio d'errore
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
    // La parte nasce la prima volta che si mostra, cioè al primo ⌘⇧J: la tastiera va subito alla carta.
    cx.timer.after(150, () => this.handle.focus());
    // ⌘⇧J scrive arturo.coda.apri: prima carta, niente risposta libera, tastiera sulla carta. La parte
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
      cx.notify();
    });
  }

  elenco() {
    const l = shared("arturo.coda");
    return Array.isArray(l) ? l : [];
  }

  davanti() {
    const l = this.elenco();
    this.at = cartaDavanti(l, this.chiave, this.at);
    const c = l[this.at] ?? null;
    this.chiave = c?.chiave ?? null;
    return c;
  }

  // La risposta va alla barra, che la porta alla sessione (volta.js rispondiCoda). La carta dopo la
  // prende il suo posto: la carta risposta sparisce quando la sessione riparte.
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

  // Le prove della carta davanti, copiate una volta nella cartella dell'app.
  copiaProve(c, cx) {
    for (const p of (c?.prove ?? []).slice(0, 4)) {
      const dest = copiaProva(c, p);
      if (!dest || this.copie[dest]) continue;
      this.copie[dest] = "copio";
      cx.spawn(async (cx) => {
        let esito;
        try {
          const r = await exec(this.py, [this.script, "prova", c.host ?? "qui", String(p), `${appHome()}/${dest}`], { timeout: 60000 });
          const d = JSON.parse(String(r.stdout ?? "").trim().split("\n").pop() || "{}");
          esito = d.ok ? "ok" : d.errore || "la copia non è riuscita";
        } catch (e) {
          esito = `la copia non è riuscita: ${String(e?.message ?? e).slice(0, 80)}`;
        }
        this.copie[dest] = esito;
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
      cx.notify();
    }
  }

  render(cx) {
    const t = theme();
    const l = this.elenco();
    const c = this.davanti();
    if (c) this.copiaProve(c, cx);
    return v_flex().id("coda").track_focus(this.handle).size_full().bg(t.background).rounded(RAGGIO.riquadro)
      .border_1().border_color(t.border).overflow_hidden()
      .on_key_down((e, cx) => this.tasto(e, c, l.length, cx))
      .child(this.testa(t, l))
      .child(div().id("coda-corpo").flex_1().overflow_y_scroll().px(SPAZIO.xxl).pb(SPAZIO.xxl)
        .child(c ? this.carta(t, c) : this.vuota(t)));
  }

  // La testata: il conteggio e, se il capo l'ha contata (#5723), la quota di raccomandazioni accettate.
  testa(t, l) {
    const quante = l.length;
    const misura = shared("arturo.coda.misura");
    return h_flex().flex_none().px(SPAZIO.xxl).pt(SPAZIO.xxl).pb(SPAZIO.xl).gap(SPAZIO.l).items_center()
      .child(div().font_family("Arturo Archivo").text_size(TESTO.titolo).text_color(t.foreground).child("Coda"))
      .when(quante > 0, (el) => el.child(div().text_size(TESTO.etichetta).text_color(t.muted)
        .child(`${this.at + 1} di ${quante}`)))
      .when(typeof misura === "string" && misura.length > 0, (el) => el.child(div().text_size(TESTO.etichetta).text_color(t.dim).child(misura)))
      .child(div().flex_1())
      .child(div().text_size(TESTO.etichetta).text_color(t.dim)
        .child(quante ? "1-6 scegli · Invio accetta · C commento sul pulsante · → salta · Esc torna" : "Esc torna alla sessione"));
  }

  vuota(t) {
    return v_flex().id("coda-vuota").w_full().pt(SPAZIO.xxl * 2).items_center().gap(SPAZIO.l)
      .child(svg(ICONA("circle-check")).size(40).text_color(t.done ?? t.accent))
      .child(div().text_size(TESTO.testata).text_color(t.foreground).child("Niente ti aspetta"))
      .child(div().text_size(TESTO.etichetta).text_color(t.muted)
        .child(`Quando una sessione chiede qualcosa, la carta arriva qui. ${tasti().coda} la riapre.`));
  }

  carta(t, c) {
    const oo = (c.opzioni ?? []).slice(0, CODA_OPZIONI);
    const ri = raccomandata(c);
    const quando = c.quando ? daQuanto(new Date(c.quando).toISOString()) : "";
    // una carta UF dice da dove viene (Da fare o Gmail) al posto della macchina, e se il capo non risponde
    const uf = c.origine === "uf";
    const dove = [c.progetto ? nomeProgetto(c.progetto) : uf ? "Posta" : "Senza progetto",
      uf ? (c.fonte === "bozza" ? "Gmail" : "Da fare") : nomeMacchina(c.host), quando,
      uf && c.vecchia ? "il capo non risponde, lettura vecchia" : ""].filter(Boolean).join(" · ");
    const umano = ["invio", "pagamento", "segreto", "otp", "oauth", "gesto"].includes(c.tipo);
    const r = String(c.raccomandazione ?? "").trim();
    return v_flex().id(`coda-carta-${c.chiave}`).w_full().max_w(760).gap(SPAZIO.xl)
      .child(v_flex().gap(SPAZIO.s)
        .child(h_flex().gap(SPAZIO.m).items_center()
          .child(punto(c.blocco || umano ? t.blocked : t.accent, 8))
          .child(div().text_size(TESTO.etichetta).text_color(t.muted).child(dove))
          .when(umano, (el) => el.child(div().px(SPAZIO.m).py(SPAZIO.xs).rounded(RAGGIO.controllo).border_1().border_color(t.blocked)
            .text_size(TESTO.nota).text_color(t.blocked).child(`Solo tu: ${c.tipo}`))))
        .child(div().text_size(TESTO.riga).text_color(t.foreground).child(c.titolo ?? "")))
      .when(Boolean(c.riassunto || c.esito), (el) => el.child(div().w_full().whitespace_normal().text_size(TESTO.corpo).text_color(t.muted).child(testoPiano(c.riassunto || c.esito))))
      .when((c.doppie ?? []).length > 0, (el) => el.child(div().w_full().whitespace_normal().text_size(TESTO.etichetta).text_color(t.dim)
        .child(`Chiede la stessa cosa anche: ${c.doppie.join(" · ")}`)))
      .child(div().w_full().whitespace_normal().text_size(TESTO.testata).text_color(t.foreground).child(testoPiano(c.domanda) || "Ti aspetta"))
      .when(oo.length > 0, (el) => el.child(v_flex().gap(SPAZIO.m).children(oo.map((o, i) => this.opzione(t, c, o, i, i === ri)))))
      .when(Boolean(r) && ri < 0, (el) => el.child(h_flex().id("coda-raccomandata").gap(SPAZIO.m).items_center().cursor_pointer()
        .on_hover((h, cx) => this.passa(r, h, cx))
        .on_click(() => this.rispondi(c, r))
        .child(div().text_size(TESTO.etichetta).text_color(t.accent).child("Invio"))
        .child(div().flex_1().whitespace_normal().text_size(TESTO.corpo).text_color(t.foreground).child(`${c.capoRac ? "Raccomandata dal capo" : "Raccomandata"}: ${testoPiano(r)}`))))
      .when(!oo.length && !r, (el) => el.child(div().text_size(TESTO.etichetta).text_color(t.muted)
        .child("Nessuna opzione: N per scrivere la risposta, T per aprire la sessione.")))
      .when((c.prove ?? []).length > 0, (el) => el.child(this.prove(t, c)))
      .when(Boolean(this.scrivo), (el) => el.child(v_flex().gap(SPAZIO.xs)
        .child(div().text_size(TESTO.etichetta).text_color(t.muted)
          .child(this.scrivo?.gesto === NOTE ? "Nota · Invio la manda · Esc annulla"
            : `Commento per: ${etichettaOpzione(this.scrivo?.gesto ?? "", -1)} · Invio esegue · Esc annulla`))
        .child(h_flex().h(PULSANTE.grande).px(SPAZIO.l).gap(SPAZIO.m).items_center()
          .rounded(RAGGIO.riga).border_1().border_color(t.accent).bg(t.raised)
          .child(svg(ICONA("square-pen")).size(ICONA_MISURA.grande).text_color(t.muted))
          .child(Input.new(this.input).flex_1().h_full().text_size(TESTO.riga).text_color(t.foreground)))))
      .child(h_flex().gap(SPAZIO.m).pt(SPAZIO.s).flex_wrap()
        .child(this.gesto(t, "coda-fatto", "circle-check", "Già fatto · F", () => this.esegui(c, GIA_FATTO), GIA_FATTO))
        .child(this.gesto(t, "coda-scarta", "x", "Scarta · X", () => this.esegui(c, SCARTA), SCARTA))
        .child(this.gesto(t, "coda-note", "square-pen", "Note · N", () => this.apriCampo(NOTE), NOTE))
        // la ripartenza di /inizio ancora da mandare: la checklist con le note (checklist.js)
        .when(c.checklist > 0 && shared("arturo.checklist.mandate")?.[c.sessionId] !== c.ripQuando, (el) => el.child(this.gesto(t, "coda-checklist", "circle-check",
          `Su cosa lavorare · ${c.checklist}`, () => run(comandoChecklist(c.chiave)))))
        .child(this.gesto(t, "coda-apri", "terminal", uf ? "Apri · T" : "Apri la sessione · T", () => this.apri(c)))
        .child(this.gesto(t, "coda-salta", "chevron-right", "Salta · →", () => {
          this.at = passoCoda(this.at, 1, this.elenco().length);
          this.chiave = this.elenco()[this.at]?.chiave ?? null;
        })));
  }

  // Un'opzione numerata: il numero è il tasto. La raccomandata ha il bordo e l'etichetta in accent.
  opzione(t, c, o, i, consigliata) {
    return h_flex().id(`coda-opzione-${i + 1}`).w_full().min_h(PULSANTE.grande).px(SPAZIO.l).py(SPAZIO.m).gap(SPAZIO.l).items_center()
      .rounded(RAGGIO.riga).cursor_pointer().border_1().border_color(consigliata ? t.accent : t.border)
      .bg(consigliata ? t.raised : t.background).hover((s) => s.border_color(consigliata ? t.accent : t.muted))
      .on_hover((h, cx) => this.passa(o, h, cx))
      .on_click(() => this.rispondi(c, String(o)))
      .child(div().w(22).h(22).flex_none().rounded(RAGGIO.controllo).bg(consigliata ? t.accent : t.raised)
        .items_center().justify_center().flex()
        .text_size(TESTO.etichetta).text_color(consigliata ? t.accent_foreground : t.muted).child(String(i + 1)))
      .child(div().flex_1().whitespace_normal().text_size(TESTO.riga).text_color(t.foreground).child(etichettaOpzione(o, i)))
      .when(consigliata, (el) => el.child(div().text_size(TESTO.nota).text_color(t.accent).child(c.capoRac ? "Raccomandata dal capo · Invio" : "Raccomandata · Invio")))
      .when(this.sopra === String(o), (el) => el.child(div().text_size(TESTO.nota).text_color(t.dim).child("C commento")));
  }

  // Un gesto della riga in basso. Con `nome` (Già fatto, Scarta, Note) il cursore sopra più C apre il commento.
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
