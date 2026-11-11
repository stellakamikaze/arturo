// Il pannello "Da fare": i todo del progetto aperto, divisi per chi agisce.
// Casella: segna fatto. "Lavoraci": segna il todo in corso e porta Claude su quel todo; finché è in
// corso la riga dice cosa fa Claude, e /fine lo chiude (#4994). "Altro": chi lo fa, quando, fermo,
// nota, scarta (menu.js). "Aggiungi" in alto: un todo nuovo senza passare da Claude.

import { div, svg } from "gpui-kit";
import { h_flex, v_flex } from "gpui-base";
import { theme, spaces, shared, setShared, notify } from "herdr";
import { todo, slug, apri, spazio, statoSpazio, PAROLE, titoloTodo } from "./dati.js";
import { ICONA, colore } from "./comuni.js";
import { partenza } from "./partenza.js";
import { fatto, inizia } from "./azioni.js";
import { apriMenu, apriNuovo } from "./menu.js";

const ORDINE = ["tu", "decidi", "io", "fermo"];

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
    return s && !s.machine && s.named ? slug(s.name) : null;
  }

  carica(cx) {
    const p = this.progetto;
    if (!p) { this.vista = null; this.errore = null; cx.notify(); return; }
    cx.spawn(async (cx) => {
      const nome = shared("arturo.progetti")?.[p]?.nome ?? p;
      const r = await todo(["--progetto", nome, "--json"]);
      if (p !== this.progetto) return;
      if (r.ok) { this.vista = r.json; this.errore = null; this.fatti.clear(); }
      else this.errore = r.errore;
      cx.notify();
    });
  }

  fatto(t, cx) {
    this.fatti.add(t.id);
    cx.notify();
    cx.spawn(async (cx) => {
      const r = await todo(fatto(t).argv);
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
    return h_flex().id(`t-${item.id}`).px(10).py(8).gap(10).items_start().rounded(8)
      .on_hover((h, cx) => { this.sopra = h ? item.id : this.sopra === item.id ? null : this.sopra; cx.notify(); })
      .when(sopra, (el) => el.bg(t.hover))
      .child(div().id(`c-${item.id}`).mt(1).size(18).flex_none().rounded(5).border_1().cursor_pointer()
        .border_color(fatto ? t.done : t.input).when(fatto, (el) => el.bg(t.done))
        .flex().items_center().justify_center()
        .hover((s) => s.border_color(t.done))
        .on_click((_e, cx) => { if (!fatto) this.fatto(item, cx); })
        .when(fatto, (el) => el.child(svg(ICONA("check")).size(13).text_color(t.background))))
      .child(v_flex().flex_1().min_w(0).gap(3)
        .child(div().whitespace_normal().text_size(13.5).text_color(fatto ? t.dim : t.foreground).child(titoloTodo(item.titolo)))
        .when(Boolean(lavoro), (el) => el.child(h_flex().gap(6).items_center()
          .child(div().size(7).flex_none().rounded_full().bg(colore(t, lavoro.colore)))
          .child(div().text_size(12).text_color(colore(t, lavoro.colore)).child(lavoro.testo))))
        .when(Boolean(quando), (el) => el.child(div().text_size(12).text_color(scaduto ? t.blocked : t.muted).child(quando))))
      .when(sopra && !fatto, (el) => el.child(div().id(`l-${item.id}`).flex_none().px(9).py(4).rounded(6).cursor_pointer()
        .text_size(12).text_color(t.accent).border_1().border_color(t.border)
        .hover((s) => s.bg(t.selected))
        .on_click((_e, cx) => this.lavoraci(item, cx))
        .child(this.parola(item))))
      .when(sopra && !fatto, (el) => el.child(div().id(`m-${item.id}`).flex_none().px(9).py(4).rounded(6).cursor_pointer()
        .text_size(12).text_color(t.muted).border_1().border_color(t.border)
        .hover((s) => s.bg(t.selected))
        .on_click(() => apriMenu(item))
        .child("Altro")));
  }

  gruppo(t, tipo, lista) {
    const aperto = this.aperti[tipo];
    return v_flex().gap(2)
      .child(h_flex().id(`g-${tipo}`).px(10).py(6).gap(8).items_center().rounded(6).cursor_pointer()
        .hover((s) => s.bg(t.hover))
        .on_click((_e, cx) => { this.aperti[tipo] = !aperto; cx.notify(); })
        .child(div().flex_1().text_size(13).font_semibold().text_color(tipo === "tu" ? t.blocked : t.foreground).child(PAROLE[tipo]))
        .child(div().text_size(12).text_color(t.muted).child(String(lista.length)))
        .child(svg(ICONA(aperto ? "chevron-down" : "chevron-right")).size(13).text_color(t.dim)))
      .when(aperto, (el) => el.children(lista.map((x) => this.riga(t, x))));
  }

  // In cima: il todo da cui ripartire, col motivo, Lavoraci sempre visibile e i passi che seguono.
  partenza(t) {
    const p = partenza(this.vista, this.fatti);
    if (!p) return null;
    const { todo: item, motivo, poi } = p;
    const lavoro = this.lavoro(item);
    return v_flex().id("partenza").px(12).py(12).gap(8).rounded(8).border_1().border_color(t.accent)
      .child(div().text_size(12).font_semibold().text_color(t.accent).child("Da dove partire"))
      .child(div().whitespace_normal().text_size(14).text_color(t.foreground).child(titoloTodo(item.titolo)))
      .when(Boolean(motivo) && !lavoro, (el) => el.child(div().whitespace_normal().text_size(12.5).text_color(t.muted).child(motivo)))
      .when(Boolean(lavoro), (el) => el.child(div().whitespace_normal().text_size(12.5).text_color(colore(t, lavoro.colore)).child(lavoro.testo)))
      .child(h_flex().child(div().id("partenza-lavoraci").px(12).py(6).rounded(6).cursor_pointer()
        .bg(t.accent).text_color(t.accent_foreground).text_size(13).font_semibold()
        .hover((s) => s.opacity(0.9))
        .on_click((_e, cx) => this.lavoraci(item, cx))
        .child(this.parola(item))))
      .when(poi.length > 0, (el) => el.child(v_flex().pt(4).gap(4)
        .child(div().text_size(12).text_color(t.muted).child("Poi"))
        .children(poi.map((x, i) => h_flex().id(`poi-${i}`).gap(8).items_start()
          .child(div().flex_none().w(14).text_size(12.5).text_color(t.dim).child(String(i + 1)))
          .child(div().flex_1().min_w(0).whitespace_normal().text_size(12.5).text_color(t.foreground).child(titoloTodo(x.titolo)))))));
  }

  vuoto(t, testo) {
    return div().px(16).py(10).whitespace_normal().text_size(13).text_color(t.muted).child(testo);
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
        ? v_flex().gap(8).px(6).children(gruppi.map(([tipo, l]) => this.gruppo(t, tipo, l)))
        : this.vuoto(t, "Niente da fare qui. Quando tu o Claude aggiungete un todo, compare in questo pannello.");
    }
    return v_flex().size_full().bg(t.chrome).rounded(8).border_1().border_color(t.border)
      .child(v_flex().px(16).pt(14).pb(10).gap(2)
        .child(h_flex().items_center()
          .child(div().id("todo-titolo").flex_1().font_family("Arturo Archivo").text_size(15).text_color(t.foreground).child("Da fare"))
          .when(Boolean(this.progetto) && !this.errore, (el) => el.child(h_flex().id("todo-aggiungi").px(8).py(3).gap(5).items_center()
            .rounded(6).cursor_pointer().text_size(12).text_color(t.muted).hover((s) => s.bg(t.hover).text_color(t.foreground))
            .on_click(() => apriNuovo(shared("arturo.progetti")?.[this.progetto]?.nome ?? this.progetto, shared("arturo.progetti")?.[this.progetto]?.titolo))
            .child(svg(ICONA("plus")).size(12))
            .child("Aggiungi"))))
        .when(Boolean(this.progetto), (el) => {
          const info = shared("arturo.progetti")?.[this.progetto];
          return el.child(div().id("todo-progetto").truncate().text_size(12.5).text_color(t.foreground).child(info?.titolo ?? this.progetto))
            .when(Boolean(info?.riga), (e) => e.child(div().id("todo-riga").pt(4).whitespace_normal().text_size(12.5).text_color(t.muted).child(info.riga)));
        }))
      .when(Boolean(cima), (el) => el.child(div().px(12).pb(8).child(cima)))
      // Uno scorrimento per progetto: cambiando progetto l'elenco riparte dall'alto.
      .child(v_flex().id(`todo-elenco-${this.progetto ?? ""}`).flex_1().min_h(0).overflow_y_scrollbar().pb(12).child(corpo));
  }
}
