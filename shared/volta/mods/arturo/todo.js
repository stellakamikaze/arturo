// Il pannello "Da fare": i todo del progetto aperto, divisi per chi agisce.
// Casella: segna fatto. "Lavoraci": segna il todo in corso e porta Claude su quel todo; finché è in
// corso la riga dice cosa fa Claude, e /fine lo chiude (#4994). "Altro": chi lo fa, quando, fermo,
// nota, scarta (menu.js). "Aggiungi" in alto: un todo nuovo senza passare da Claude.

import { div, svg } from "gpui-kit";
import { h_flex, v_flex } from "gpui-base";
import { theme, spaces, shared, setShared, notify } from "herdr";
import { todo, slug, apri, spazio, statoSpazio, eProgetto, PAROLE, titoloTodo } from "./dati.js";
import { ICONA, colore, pulsante } from "./comuni.js";
import { SPAZIO, MARGINE, RAGGIO, TESTO, PALLINO, ICONA_MISURA } from "./misure.js";
import { partenza } from "./partenza.js";
import { fatto, inizia, ancoraFatti } from "./azioni.js";
import { apriMenu, apriNuovo } from "./menu.js";

const ORDINE = ["tu", "decidi", "io", "fermo"];
// La casella per segnare fatto un todo: un bersaglio da cliccare, più grande delle icone della scala.
const CASELLA = 18;

export class Todo {
  init(_p, cx) {
    this.progetto = null;
    this.vista = null;
    this.errore = null;
    this.aperti = { tu: true, decidi: true, io: false, fermo: false };
    this.sopra = null;
    this.letto = null;
    this.fatti = new Set();
    this.sessione = null;
    cx.timer.every(1500, (cx) => {
      const p = this.attivo();
      const letto = `${shared("arturo.letto")}:${shared("arturo.scritto")}`;
      if (p !== this.progetto || letto !== this.letto) { this.progetto = p; this.letto = letto; this.carica(cx); }
      // La riga di un todo in corso segue la sessione: lavora, aspetta te, chiusa.
      const sessione = p ? statoSpazio(spazio(p)) ?? "chiusa" : null;
      if (sessione !== this.sessione) { this.sessione = sessione; cx.notify(); }
    });
    this.progetto = this.attivo();
    this.carica(cx);
  }

  attivo() {
    const s = spaces().find((x) => x.active);
    return eProgetto(s) ? slug(s.name) : null;
  }

  carica(cx) {
    const p = this.progetto;
    if (!p) { this.vista = null; this.errore = null; cx.notify(); return; }
    cx.spawn(async (cx) => {
      const nome = shared("arturo.progetti")?.[p]?.nome ?? p;
      const r = await todo(["--progetto", nome, "--json"]);
      if (p !== this.progetto) return;
      if (r.ok) { this.vista = r.json; this.errore = null; this.fatti = ancoraFatti(this.fatti, r.json); }
      else this.errore = r.errore;
      cx.notify();
    });
  }

  fatto(t, cx) {
    this.fatti.add(t.id);
    cx.notify();
    cx.spawn(async (cx) => {
      const r = await todo(fatto(t).argv);
      // la barra rilegge i conti subito, come dopo ogni altro gesto del pannello
      setShared("arturo.scritto", Date.now());
      if (r.ok) notify({ title: "Fatto", body: t.titolo, level: "success", timeout: 4000 });
      else {
        this.fatti.delete(t.id);
        notify({ title: r.codice === 2 ? "Questo todo è cambiato nel frattempo" : "Non sono riuscito a segnarlo", body: r.codice === 2 ? "Ho riletto l'elenco: riprova." : r.errore, level: "warning" });
      }
      this.carica(cx);
    });
  }

  // Lavoraci: prima il todo passa in corso, poi Claude parte su quel todo. Se il todo è cambiato nel
  // frattempo (codice 2) Claude non parte: lavorerebbe sul todo sbagliato. Con la fonte giù parte lo
  // stesso, e l'avviso lo dice. Un todo già in corso con la sessione aperta porta solo alla sessione.
  lavoraci(item, cx) {
    const progetto = this.progetto;
    const scelto = { id: item.id, titolo: item.titolo };
    const g = inizia(item);
    if (!g) return apri(progetto, spazio(progetto) ? undefined : scelto);
    cx.spawn(async (cx) => {
      const r = await todo(g.argv);
      setShared("arturo.scritto", Date.now());
      if (!r.ok && r.codice === 2) {
        notify({ title: "Claude non è partito", body: /cambiat|aspettavi/i.test(r.errore) ? "Questo todo è cambiato nel frattempo: ho riletto l'elenco, riprova." : r.errore, level: "warning" });
        return this.carica(cx);
      }
      if (!r.ok) notify({ title: "Claude parte, ma il todo non risulta in corso", body: r.errore, level: "warning" });
      await apri(progetto, scelto);
    });
  }

  // Cosa fa Claude su un todo in corso: lo dice la sessione del progetto, se è aperta.
  lavoro(item) {
    if (item.stato !== "in corso") return null;
    const s = spazio(this.progetto);
    if (!s) return { testo: "In corso, ma la sessione è chiusa: Lavoraci la riapre", colore: "muted" };
    const st = statoSpazio(s);
    if (st === "blocked") return { testo: "Claude ti aspetta", colore: "blocked" };
    if (st === "working") return { testo: "Claude ci sta lavorando", colore: "working" };
    return { testo: "Claude ci lavora", colore: "working" };
  }

  // Il pulsante della riga e della scheda in cima: "Vai da Claude" se ci lavora già, altrimenti "Lavoraci".
  parola(item) {
    return item.stato === "in corso" && spazio(this.progetto) ? "Vai da Claude" : "Lavoraci";
  }

  riga(t, item) {
    const sopra = this.sopra === item.id;
    const fatto = this.fatti.has(item.id);
    const scaduto = typeof item.giorni === "number" && item.giorni < 0;
    const quando = item.scadenza_testo || "";
    const lavoro = this.lavoro(item);
    return h_flex().id(`t-${item.id}`).mx(MARGINE).px(SPAZIO.m).py(SPAZIO.m).gap(SPAZIO.m + 2).items_start().rounded(RAGGIO.riga)
      .on_hover((h, cx) => { this.sopra = h ? item.id : this.sopra === item.id ? null : this.sopra; cx.notify(); })
      .when(sopra, (el) => el.bg(t.hover))
      // la casella è 18 px, fuori dalla scala delle icone: è un bersaglio da cliccare, non un segno
      .child(div().id(`c-${item.id}`).mt(1).size(CASELLA).flex_none().rounded(RAGGIO.controllo - 1).border_1().cursor_pointer()
        .border_color(fatto ? t.done : t.input).when(fatto, (el) => el.bg(t.done))
        .flex().items_center().justify_center()
        .hover((s) => s.border_color(t.done))
        .on_click((_e, cx) => { if (!fatto) this.fatto(item, cx); })
        .when(fatto, (el) => el.child(svg(ICONA("check")).size(CASELLA - 5).text_color(t.background))))
      .child(v_flex().flex_1().min_w(0).gap(SPAZIO.xs + 1)
        .child(div().id(`tt-${item.id}`).whitespace_normal().text_size(TESTO.corpo).text_color(fatto ? t.dim : t.foreground).child(titoloTodo(item.titolo)))
        .when(Boolean(lavoro), (el) => el.child(h_flex().id(`tl-${item.id}`).gap(SPAZIO.s + 2).items_center()
          .child(div().size(PALLINO).flex_none().rounded_full().bg(colore(t, lavoro.colore)))
          .child(div().text_size(TESTO.etichetta).text_color(colore(t, lavoro.colore)).child(lavoro.testo))))
        .when(Boolean(quando), (el) => el.child(div().id(`tq-${item.id}`).text_size(TESTO.etichetta).text_color(scaduto ? t.blocked : t.muted).child(quando))))
      // Lavoraci e Altro: pulsanti piccoli della scala (28 px), senza icona per lasciare spazio al titolo
      .when(sopra && !fatto, (el) => el.child(div().flex_none().child(pulsante(`l-${item.id}`, null, this.parola(item), (_e, cx) => this.lavoraci(item, cx), false, "piccolo"))))
      .when(sopra && !fatto, (el) => el.child(div().flex_none().child(pulsante(`m-${item.id}`, null, "Altro", () => apriMenu(item), false, "piccolo"))));
  }

  gruppo(t, tipo, lista) {
    const aperto = this.aperti[tipo];
    // l'intestazione di un gruppo come quella dei gruppi della colonna (volta.js): stesso bordo, stesso raggio
    return v_flex().gap(SPAZIO.xs)
      .child(h_flex().id(`g-${tipo}`).mx(MARGINE).px(SPAZIO.m).py(SPAZIO.s + 2).gap(SPAZIO.m).items_center().rounded(RAGGIO.riga).cursor_pointer()
        .hover((s) => s.bg(t.hover))
        .on_click((_e, cx) => { this.aperti[tipo] = !aperto; cx.notify(); })
        .child(div().id(`gt-${tipo}`).flex_1().text_size(TESTO.corpo).font_semibold().text_color(tipo === "tu" ? t.blocked : t.foreground).child(PAROLE[tipo]))
        .child(div().id(`gn-${tipo}`).text_size(TESTO.etichetta).text_color(t.muted).child(String(lista.length)))
        .child(svg(ICONA(aperto ? "chevron-down" : "chevron-right")).size(ICONA_MISURA.piccola).text_color(t.dim)))
      .when(aperto, (el) => el.children(lista.map((x) => this.riga(t, x))));
  }

  // In cima: il todo da cui ripartire, col motivo, Lavoraci sempre visibile e i passi che seguono.
  partenza(t) {
    const p = partenza(this.vista, this.fatti);
    if (!p) return null;
    const { todo: item, motivo, poi } = p;
    const lavoro = this.lavoro(item);
    // il testo della carta parte dallo stesso bordo delle righe (MARGINE + SPAZIO.m); Lavoraci è il
    // pulsante grande e forte, come Nuova richiesta nella colonna
    return v_flex().id("partenza").px(SPAZIO.m).py(SPAZIO.l).gap(SPAZIO.m).rounded(RAGGIO.riquadro).border_1().border_color(t.accent)
      .child(div().id("partenza-titolo").text_size(TESTO.etichetta).font_semibold().text_color(t.accent).child("Da dove partire"))
      .child(div().id("partenza-todo").whitespace_normal().text_size(TESTO.riga).text_color(t.foreground).child(titoloTodo(item.titolo)))
      .when(Boolean(motivo) && !lavoro, (el) => el.child(div().id("partenza-motivo").whitespace_normal().text_size(TESTO.etichetta).text_color(t.muted).child(motivo)))
      .when(Boolean(lavoro), (el) => el.child(div().whitespace_normal().text_size(TESTO.etichetta).text_color(colore(t, lavoro.colore)).child(lavoro.testo)))
      .child(h_flex().child(pulsante("partenza-lavoraci", null,this.parola(item), (_e, cx) => this.lavoraci(item, cx), true)))
      .when(poi.length > 0, (el) => el.child(v_flex().pt(SPAZIO.s).gap(SPAZIO.s)
        .child(div().text_size(TESTO.etichetta).text_color(t.muted).child("Poi"))
        .children(poi.map((x, i) => h_flex().id(`poi-${i}`).gap(SPAZIO.m).items_start()
          .child(div().flex_none().w(ICONA_MISURA.piccola).text_size(TESTO.etichetta).text_color(t.dim).child(String(i + 1)))
          .child(div().flex_1().min_w(0).whitespace_normal().text_size(TESTO.etichetta).text_color(t.foreground).child(titoloTodo(x.titolo)))))));
  }

  vuoto(t, testo) {
    return div().id("todo-vuoto").px(MARGINE + SPAZIO.m).py(SPAZIO.m + 2).whitespace_normal().text_size(TESTO.corpo).text_color(t.muted).child(testo);
  }

  render() {
    const t = theme();
    const cima = this.vista && !this.errore ? this.partenza(t) : null;
    let corpo;
    if (!this.progetto) corpo = this.vuoto(t, "Apri un progetto a sinistra: qui vedi cosa c'è da fare e chi lo fa.");
    else if (this.errore) corpo = this.vuoto(t, `Non riesco a leggere i todo: ${this.errore}`);
    else if (!this.vista) corpo = this.vuoto(t, "Leggo i todo…");
    else {
      const gruppi = ORDINE.map((tipo) => [tipo, (this.vista.gruppi ?? []).find((g) => g.tipo === tipo)?.todo ?? []]).filter(([, l]) => l.length);
      corpo = gruppi.length
        ? v_flex().gap(SPAZIO.m).children(gruppi.map(([tipo, l]) => this.gruppo(t, tipo, l)))
        : this.vuoto(t, "Niente da fare qui. Quando tu o Claude aggiungete un todo, compare in questo pannello.");
    }
    // Il pannello ha il raggio del riquadro della sessione (radius 10 in layouts/arturo.json); titolo,
    // carta in cima, gruppi e righe partono tutti da MARGINE + SPAZIO.m, come nella colonna di sinistra.
    return v_flex().size_full().bg(t.chrome).rounded(RAGGIO.riquadro).border_1().border_color(t.border)
      .child(v_flex().pl(MARGINE + SPAZIO.m).pr(MARGINE).pt(SPAZIO.l).pb(SPAZIO.m + 2).gap(SPAZIO.xs)
        .child(h_flex().items_center().gap(SPAZIO.m)
          .child(div().id("todo-titolo").flex_1().font_family("Arturo Archivo").text_size(TESTO.testata).text_color(t.foreground).child("Da fare"))
          .when(Boolean(this.progetto) && !this.errore, (el) => el.child(pulsante("todo-aggiungi", "plus", "Aggiungi",
            () => apriNuovo(shared("arturo.progetti")?.[this.progetto]?.nome ?? this.progetto, shared("arturo.progetti")?.[this.progetto]?.titolo), false, "piccolo"))))
        .when(Boolean(this.progetto), (el) => {
          const info = shared("arturo.progetti")?.[this.progetto];
          return el.child(div().id("todo-progetto").truncate().text_size(TESTO.etichetta).text_color(t.foreground).child(info?.titolo ?? this.progetto))
            .when(Boolean(info?.riga), (e) => e.child(div().id("todo-riga").pt(SPAZIO.s).whitespace_normal().text_size(TESTO.etichetta).text_color(t.muted).child(info.riga)));
        }))
      .when(Boolean(cima), (el) => el.child(div().px(MARGINE).pb(SPAZIO.m).child(cima)))
      // Uno scorrimento per progetto: cambiando progetto l'elenco riparte dall'alto.
      .child(v_flex().id(`todo-elenco-${this.progetto ?? ""}`).flex_1().min_h(0).overflow_y_scrollbar().pb(SPAZIO.l).child(corpo));
  }
}
