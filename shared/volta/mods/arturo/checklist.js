// La checklist di Volta (17/11/2026). Federico: "voglio poter vedere una checklist con spazio per eventuali
// note per poter indicare ad Arturo e Volta su cosa lavorare"; "vorrei si vedesse in sovrimpressione con un
// pulsante cliccabile, in maniera semplice"; "deve funzionare associandola a tutte le convo e i progetti,
// inoltre la lista dei todo deve prevedere uno scarta e un già fatto e simili".
//
// La lista (listaChecklist di sessioni.js) viene dalla ripartenza di /inizio, se la sessione l'ha scritta
// (ripartenza-scrivi.py della config, portata dalla sonda), altrimenti dai task aperti del progetto della
// sessione (`arturo todo --progetto X --json`, come il pannello Da fare). Due parti:
//
//   ripartenza  blocco sovrapposto alla sessione davanti (floating del blocco "main" in layouts/arturo.json,
//               in basso a destra). Chiuso è una barra "Su cosa lavoro adesso? · N · Apri"; dopo /inizio si
//               apre da solo. Lo stato aperto o chiuso resta per sessione (shared arturo.checklist.aperte).
//               Dal 17/11 sera il layout non lo mostra più (Federico: "teniamolo solo in alto a dx"): resta
//               la parte, per chi ha un layout suo che la nomina.
//   checklist   lo stesso elenco come dialogo: ⌘⇧S, il pulsante della testata, la carta della Coda.
//
// Una riga: casella "lavoraci adesso" (casella, numero e testo sono un bersaglio solo), poi i gesti Già fatto,
// Scarta, Rimanda, A Claude (A te se è già di Claude) e "+ Nota". Niente parte finché non si preme "Manda":
// prima i gesti sui todo con `arturo todo` (gestiChecklist di azioni.js), poi il messaggio alla sessione col
// comando della Coda (comandoRisposta). Invio manda; nel dialogo Esc con qualcosa di scelto avvisa e solo la
// seconda chiude. I campi (InputState) nascono in init o nei timer: dentro render() non nascono.

import { div, svg } from "gpui-kit";
import { v_flex, h_flex, InputState, Input } from "gpui-base";
import { theme, props, closeOverlay, openOverlay, run, shared, setShared, notify } from "herdr";
import { ICONA } from "./comuni.js";
import { todo } from "./dati.js";
import { gestiChecklist } from "./azioni.js";
import { listaChecklist, riportaScelte, testoChecklist, comandoRisposta, nomeProgetto, etichettaGesto, bozzaPersa, GESTI_CHECKLIST, TESTO_CHECKLIST_MAX } from "./sessioni.js";
import { SPAZIO, TESTO, RAGGIO, PULSANTE } from "./misure.js";

// La casella è un bersaglio da cliccare, come quella dei todo (todo.js, DESIGN.md: 18 px, raggio 5).
const CASELLA = 18;
// Il blocco sovrapposto: largo quanto una colonna di lettura, l'elenco scorre oltre ALTO px.
const LARGO = 460;
const ALTO = 420;

// `s`: { chiave, sessionId, titolo, progetto, ripartenza }, da checklist() di volta.js.
export function apriChecklist(s) {
  openOverlay({ mod: "arturo", props: { parte: "checklist", sessione: s }, kind: "dialog", width: 760, height: 0.82 });
}

// Un segno per sessione in shared arturo.checklist.<chi>: { [sessionId]: valore }.
const segna = (chi, sid, valore) => setShared(`arturo.checklist.${chi}`, { ...(shared(`arturo.checklist.${chi}`) ?? {}), [sid]: valore });
// La lista col segno di sessione e ripartenza, per riportaScelte e per la bozza di "Manda".
const idLista = (s, l) => (l ? { ...l, sessione: s?.sessionId, quando: s?.ripartenza?.quando ?? null } : null);
const chiaveLista = (s, l) => (l ? `${s.sessionId}|${l.fonte}|${s.ripartenza?.quando ?? ""}|${l.filoni.flatMap((f) => f.voci.map((v) => `${v.n}:${v.id ?? ""}`)).join(",")}` : null);

export class Checklist {
  init(_p, cx) {
    this.galleggia = props()?.parte === "ripartenza";
    this.s = null;
    this.lista = null;
    this.chi = null;          // la lista mostrata (chiaveLista): se cambia, le scelte ripartono
    this.vista = null;        // i task del progetto, da arturo todo
    this.vistaDi = null;      // "progetto|letto": quando cambia, la vista si rilegge
    this.mando = false;
    this.handle = cx.focus_handle();
    this.generale = InputState.new({ placeholder: "Una nota per tutto l'elenco (facoltativa)" });
    this.generale.on("change", (_e, cx) => { this.esci = false; cx.notify(); });
    this.generale.on("submit", (_e, cx) => this.manda(cx));
    this.campi = {};          // i campi nota, per numero di riga; nascono nel timer
    const giro = (cx) => {
      const s = this.galleggia ? this.davanti() : props()?.sessione ?? null;
      this.carica(s, cx);
      const l = s ? listaChecklist(s.ripartenza, this.vista) : null;
      const k = s ? chiaveLista(s, l) : null;
      if (this.fuoco != null) { this.campi[this.fuoco]?.focus(); this.fuoco = null; }
      if (k === this.chi) { if (s) this.s = s; if (this.riprendi()) cx.notify(); this.provaChecklist(cx); return; }
      if (s && l) this.prepara(s, l);
      else { this.s = s; this.lista = null; this.chi = null; }
      this.riprendi();
      cx.notify();
    };
    giro(cx);
    cx.timer.every(500, giro);
    if (!this.galleggia) cx.timer.after(150, () => this.handle.focus());
  }

  // La sessione davanti, da volta.js davanti(): chiave, progetto e ripartenza ancora da mandare.
  davanti() {
    const d = shared("arturo.volta.davanti");
    if (!d?.sessionId || !d.chiave) return null;
    return { chiave: d.chiave, sessionId: d.sessionId, titolo: d.titolo, progetto: d.progetto ?? null, ripartenza: d.ripartenza ?? null };
  }

  // La vista del progetto della sessione: si rilegge quando cambia il progetto o dopo un gesto (arturo.scritto).
  carica(s, cx) {
    const p = s?.progetto ?? null;
    const di = `${p}|${shared("arturo.letto")}:${shared("arturo.scritto")}`;
    if (di === this.vistaDi) return;
    this.vistaDi = di;
    if (!p) { this.vista = null; return; }
    cx.spawn(async (cx) => {
      const r = await todo(["--progetto", shared("arturo.progetti")?.[p]?.nome ?? p, "--json"]);
      if (!this.vistaDi?.startsWith(`${p}|`)) return;
      this.vista = r.ok ? r.json : null;
      cx.notify();
    });
  }

  // Le scelte di una lista: casella, gesto e nota per riga, e la nota in fondo.
  // Se la lista si rifà sulla stessa sessione e fonte (un task nuovo, una rilettura), scelte, note aperte, gruppi
  // chiusi e nota in fondo restano (riportaScelte). Dopo "Manda" (this.azzera) ripartono da zero.
  prepara(s, l) {
    const id = (x, y) => idLista(x, y);
    const vecchie = {};
    for (const v of (this.lista?.filoni ?? []).flatMap((f) => f.voci)) {
      const x = this.scelte?.[v.n];
      const nota = this.campi[v.n]?.value() ?? "";
      if (x?.spunta || x?.gesto || nota || this.aperte?.has(v.n)) vecchie[v.n] = { ...x, nota, aperta: this.aperte?.has(v.n) };
    }
    const resta = this.azzera ? {} : riportaScelte(this.lista && id(this.s, this.lista), id(s, l), vecchie);
    const stessa = !this.azzera && this.lista && this.s?.sessionId === s.sessionId && this.lista.fonte === l.fonte;
    this.azzera = false;
    this.s = s;
    this.lista = l;
    this.chi = chiaveLista(s, l);
    this.scelte = {};
    this.aperte = new Set();
    // coi task del progetto i gruppi di Claude e dei fermi partono chiusi, come nel pannello Da fare
    if (!stessa) this.chiusi = new Set(l.fonte === "progetto" ? ["Ci pensa Claude", "Fermi"] : []);
    this.esci = false;
    if (!stessa) this.generale.set_value("");
    for (const v of l.filoni.flatMap((f) => f.voci)) {
      const p = resta[v.n];
      this.scelte[v.n] = { spunta: Boolean(p?.spunta), gesto: p?.gesto ?? null };
      if (p?.aperta) this.aperte.add(v.n);
      if (!this.campi[v.n]) {
        const x = InputState.new({ placeholder: "Nota per questa riga" });
        x.on("change", (_e, cx) => { this.esci = false; cx.notify(); });
        x.on("submit", (_e, cx) => this.manda(cx));
        this.campi[v.n] = x;
      }
      this.campi[v.n].set_value(p?.nota ?? "");
    }
  }

  // Aperto o chiuso: dopo /inizio si apre da solo (una ripartenza non ancora mandata); poi decide la persona.
  aperto() {
    if (!this.galleggia) return true;
    const scelto = shared("arturo.checklist.aperte")?.[this.s?.sessionId];
    if (typeof scelto === "boolean") return scelto;
    return this.lista?.fonte === "ripartenza";
  }

  apri(si, cx) {
    if (this.s?.sessionId) segna("aperte", this.s.sessionId, si);
    cx.notify();
  }

  chiudi() { if (!this.galleggia) closeOverlay(props().overlay); }

  scelteConNote() {
    const out = {};
    for (const [n, x] of Object.entries(this.scelte ?? {})) out[n] = { ...x, nota: this.campi[n]?.value() ?? "" };
    return out;
  }

  testo() { return this.lista ? testoChecklist(this.lista, this.scelteConNote(), this.generale?.value() ?? "") : ""; }

  // "Manda": prima i gesti sui todo, uno per volta, poi il messaggio alla sessione. Un gesto che non riesce lo
  // dice un avviso. Il dialogo si chiude solo alla fine: un overlay chiuso ferma il suo codice. `cx` è quello del
  // gesto che manda (clic, Invio): Herdr vieta di tenere un cx e usarlo dopo, e con quello di render() l'invio
  // restava fermo su "Mando…" (17/11/2026).
  manda(cx) {
    const testo = this.testo();
    if (!cx?.spawn || this.mando || !testo || testo.length > TESTO_CHECKLIST_MAX || !this.s?.chiave) return;
    const s = this.s;
    const gesti = gestiChecklist(this.lista, this.scelteConNote());
    const ripartenza = this.lista.fonte === "ripartenza" ? s.ripartenza?.quando : null;
    // la bozza: se la risposta non arriva, volta.js la segna persa e la checklist rimette tutto (dopoRisposta)
    const bozza = { quando: Date.now(), ripartenza, lista: idLista(s, this.lista), scelte: this.scelteConNote(),
      generale: this.generale?.value() ?? "", testo: String(testo).trim().slice(0, TESTO_CHECKLIST_MAX) };
    this.persa = null;
    this.mando = true;
    cx.notify();
    cx.spawn(async (cx) => {
      const errori = [];
      try {
        for (const g of gesti) {
          let r;
          try { r = await todo(g.argv); } catch (e) { r = { ok: false, errore: String(e?.message ?? e) }; }
          if (!r.ok) errori.push(`${g.n}: ${r.codice === 2 ? "il todo è cambiato nel frattempo" : r.errore}`);
        }
        if (gesti.length) setShared("arturo.scritto", Date.now());
        segna("bozze", s.sessionId, bozza);
        run(comandoRisposta(s.chiave, testo, TESTO_CHECKLIST_MAX));
        segna("aperte", s.sessionId, false);
        if (errori.length) notify({ title: "Alcuni gesti non sono riusciti", body: errori.join(" · ").slice(0, 300), level: "warning" });
      } catch (e) {
        notify({ title: "La checklist non è partita", body: String(e?.message ?? e).slice(0, 200), level: "warning" });
      } finally {
        this.mando = false;
        this.chi = null;   // la lista si rifà al giro dopo, coi task riletti, e le scelte ripartono da zero
        this.azzera = true;
        cx.notify();
      }
      this.chiudi();
    });
  }

  gira(n, cx) {
    const x = this.scelte[n];
    x.spunta = !x.spunta;
    if (x.spunta && (x.gesto === "fatto" || x.gesto === "scarta")) x.gesto = null;
    this.esci = false;
    cx.notify();
  }

  gesto(n, g, cx) {
    const x = this.scelte[n];
    x.gesto = x.gesto === g ? null : g;
    if (x.gesto === "fatto" || x.gesto === "scarta") x.spunta = false;
    this.esci = false;
    cx.notify();
  }

  // Il campo nasce col render dopo: il fuoco dato subito non resta, e i tasti andavano al terminale sotto
  // (17/11/2026, Federico: "la sezione Note non funziona"). Si ridà al giro dopo, come in cambio.js.
  apriNota(n, cx) {
    this.aperte.add(n);
    this.campi[n]?.focus();
    this.fuoco = n;
    cx.notify();
  }

  // Una bozza persa (dopoRisposta di sessioni.js): rimette scelte, note e nota generale sulla lista di
  // adesso e dice perché non è arrivata. Una volta per bozza. Torna true se ha rimesso qualcosa.
  riprendi() {
    const r = bozzaPersa(shared("arturo.checklist.bozze")?.[this.s?.sessionId], idLista(this.s, this.lista), this.ripresa);
    if (!r) return false;
    this.ripresa = r.quando;
    for (const [n, p] of Object.entries(r.scelte)) {
      if (!this.scelte?.[n]) continue;
      this.scelte[n] = { spunta: Boolean(p.spunta), gesto: p.gesto ?? null };
      if (p.nota) { this.aperte.add(Number(n)); this.campi[n]?.set_value(p.nota); }
    }
    if (r.generale) this.generale.set_value(r.generale);
    this.persa = r.errore;
    return true;
  }

  // "arturo.checklist-prova-…" (barra.js, shared arturo.checklist.prova): i passi di una persona eseguiti con gli
  // stessi metodi dei clic (gira, gesto, apriNota, manda) e col cx del timer, una volta per segno. Solo il blocco
  // sovrapposto, sulla lista già pronta.
  provaChecklist(cx) {
    const p = shared("arturo.checklist.prova");
    if (!this.galleggia || !p?.quando || p.quando === this.provata || !this.lista) return;
    this.provata = p.quando;
    const voci = this.lista.filoni.flatMap((f) => f.voci);
    if (this.s?.sessionId) segna("aperte", this.s.sessionId, true);
    for (const x of p.passi ?? []) {
      const v = voci.find((y) => (Number.isInteger(x.id) ? y.id === x.id : y.n === x.n));
      if (!v) continue;
      if (x.fai === "spunta") this.gira(v.n, cx);
      else if (x.fai === "gesto") this.gesto(v.n, x.gesto, cx);
      else if (x.fai === "nota") { this.apriNota(v.n, cx); this.campi[v.n]?.set_value(String(x.testo ?? "")); }
    }
    cx.notify();
    if (p.manda) this.manda(cx);
  }

  // Esc nel dialogo: chiude subito se non c'è niente da perdere, altrimenti la prima volta avvisa.
  esc(cx) {
    if (!this.testo() || this.esci) return this.chiudi();
    this.esci = true;
    cx.notify();
  }

  render() {
    const t = theme();
    if (!this.s || !this.lista) {
      if (this.galleggia) return div();   // niente sessione con un progetto o niente da fare: niente blocco
      return v_flex().id("checklist").size_full().bg(t.popover).p(SPAZIO.xxl).gap(SPAZIO.m)
        .child(div().font_family("Arturo Archivo").text_size(TESTO.titolo).text_color(t.foreground).child("Su cosa lavoro adesso?"))
        .child(div().text_size(TESTO.corpo).text_color(t.muted).child(this.s?.progetto ? "Leggo i task del progetto…" : "Questa sessione non ha un progetto né una ripartenza di /inizio."));
    }
    const quante = this.lista.filoni.reduce((a, f) => a + f.voci.length, 0);
    const testa = [this.s.progetto ? nomeProgetto(this.s.progetto) : "", this.s.titolo].filter(Boolean).join(" · ");
    if (!this.aperto()) return this.barra(t, quante, testa);
    const testo = this.testo();
    const troppo = testo.length > TESTO_CHECKLIST_MAX;
    const pronto = Boolean(testo) && !troppo && !this.mando;
    const elenco = v_flex().gap(SPAZIO.m).children(this.lista.filoni.map((f, i) => this.filone(t, f, i)));
    const corpo = this.galleggia
      ? div().id("ripartenza-corpo").max_h(ALTO).overflow_y_scroll().child(elenco)
      : div().id("checklist-corpo").flex_1().overflow_y_scroll().px(SPAZIO.xxl - SPAZIO.m).pb(SPAZIO.l).child(elenco);
    const radice = this.galleggia
      ? v_flex().id("ripartenza").w(LARGO).px(SPAZIO.l).pt(SPAZIO.m).pb(SPAZIO.s).gap(SPAZIO.m)
      : v_flex().id("checklist").size_full().bg(t.popover);
    const fonte = this.lista.fonte === "ripartenza" ? "La ripartenza di /inizio" : `I task del progetto · ${quante}`;
    return radice.track_focus(this.handle)
      .on_key_down((e, cx) => {
        if (e.key === "escape" && !this.galleggia) this.esc(cx);
        else if (e.key === "enter" && (e.modifiers?.platform || e.modifiers?.control)) this.manda(cx);
        else return;
        cx.stop_propagation();
      })
      .child(this.galleggia
        ? h_flex().gap(SPAZIO.m).items_center()
          .child(v_flex().flex_1().min_w(0)
            .child(div().font_family("Arturo Archivo").text_size(TESTO.testata).text_color(t.foreground).child("Su cosa lavoro adesso?"))
            .child(div().truncate().text_size(TESTO.nota).text_color(t.muted).child(`${testa} · ${fonte}`)))
          .child(this.piccolo(t, "ripartenza-riduci", "Riduci", (_e, cx) => this.apri(false, cx)))
        : v_flex().flex_none().px(SPAZIO.xxl).pt(SPAZIO.xxl).pb(SPAZIO.l).gap(SPAZIO.xs + 1)
          .child(div().font_family("Arturo Archivo").text_size(TESTO.titolo).text_color(t.foreground).child("Su cosa lavoro adesso?"))
          .child(div().truncate().text_size(TESTO.etichetta).text_color(t.muted).child(`${testa} · ${fonte}`)))
      .child(corpo)
      .child(this.piede(t, testo, troppo, pronto));
  }

  // Il blocco chiuso: una barra sola, cliccabile tutta, col pulsante Apri.
  barra(t, quante, testa) {
    return h_flex().id("ripartenza-barra").w(LARGO).px(SPAZIO.l).py(SPAZIO.s).gap(SPAZIO.m).items_center().cursor_pointer()
      .on_mouse_down("left", (_e, cx) => cx.stop_propagation())
      .on_click((_e, cx) => this.apri(true, cx))
      .child(svg(ICONA("circle-check")).size(16).flex_none().text_color(t.accent))
      .child(v_flex().flex_1().min_w(0)
        .child(div().text_size(TESTO.corpo).font_semibold().text_color(t.foreground).child(`Su cosa lavoro adesso? · ${quante}`))
        .child(div().truncate().text_size(TESTO.nota).text_color(t.muted).child(testa)))
      .child(div().id("ripartenza-apri").flex_none().px(SPAZIO.l).h(PULSANTE.piccolo).flex().items_center().rounded(RAGGIO.controllo)
        .bg(t.accent).text_color(t.accent_foreground).text_size(TESTO.etichetta).font_semibold().child("Apri"));
  }

  piccolo(t, id, testo, azione, acceso = false) {
    return div().id(id).flex_none().px(SPAZIO.m).h(24).flex().items_center().rounded(RAGGIO.controllo).cursor_pointer()
      .text_size(TESTO.nota).border_1().border_color(acceso ? t.accent : t.border)
      .bg(acceso ? t.accent : t.background).text_color(acceso ? t.accent_foreground : t.muted)
      .hover((st) => st.border_color(t.accent))
      .on_mouse_down("left", (_e, cx) => cx.stop_propagation())
      .on_click(azione)
      .child(testo);
  }

  // Un gruppo: l'intestazione apre e chiude, col numero delle righe.
  filone(t, f, i) {
    const chiuso = this.chiusi.has(f.nome);
    return v_flex().id(`ck-f-${i}`).gap(SPAZIO.xs)
      .when(Boolean(f.nome), (el) => el.child(h_flex().id(`ck-fn-${i}`).px(SPAZIO.m).pt(SPAZIO.s).gap(SPAZIO.s + 2).items_center().cursor_pointer()
        .on_mouse_down("left", (_e, cx) => cx.stop_propagation())
        .on_click((_e, cx) => { if (chiuso) this.chiusi.delete(f.nome); else this.chiusi.add(f.nome); cx.notify(); })
        .child(svg(ICONA(chiuso ? "chevron-right" : "chevron-down")).size(12).text_color(t.dim))
        .child(div().text_size(TESTO.nota).font_semibold().text_color(t.muted).child(`${f.nome} · ${f.voci.length}`))))
      .when(!chiuso, (el) => el.children(f.voci.map((v) => this.riga(t, v))));
  }

  riga(t, v) {
    const x = this.scelte[v.n] ?? {};
    const preso = Boolean(x.spunta);
    const via = x.gesto === "fatto" || x.gesto === "scarta";
    const nota = this.aperte.has(v.n) ? this.campi[v.n] : null;
    const parto = this.lista.partenza?.n === v.n;
    // il rientro di marca, gesti e nota: casella + spazio + numero, così stanno sotto il testo
    const rientro = CASELLA + SPAZIO.m + 2 + 22 + SPAZIO.m;
    return v_flex().id(`ck-${v.n}`).w_full().px(SPAZIO.m).py(SPAZIO.s + 2).gap(SPAZIO.xs + 2).rounded(RAGGIO.riga)
      .when(preso || Boolean(x.gesto), (el) => el.bg(t.raised))
      // casella, numero e testo: un bersaglio solo, senza zone morte fra la casella e il testo
      .child(h_flex().id(`ck-t-${v.n}`).w_full().gap(SPAZIO.m + 2).items_start().cursor_pointer()
        .on_mouse_down("left", (_e, cx) => cx.stop_propagation())
        .on_click((_e, cx) => this.gira(v.n, cx))
        .child(div().id(`ck-c-${v.n}`).mt(1).size(CASELLA).flex_none().rounded(RAGGIO.controllo - 1).border_1()
          .border_color(preso ? t.accent : t.input).when(preso, (el) => el.bg(t.accent))
          .flex().items_center().justify_center()
          .when(preso, (el) => el.child(svg(ICONA("check")).size(CASELLA - 5).text_color(t.accent_foreground))))
        .child(div().w(22).flex_none().text_size(TESTO.corpo).text_color(t.muted).child(`${v.n}.`))
        .child(div().flex_1().min_w(0).whitespace_normal().text_size(TESTO.corpo).text_color(via ? t.dim : t.foreground).child(v.testo)))
      .when(Boolean(v.marca) || parto || Boolean(x.gesto), (el) => el.child(h_flex().pl(rientro).gap(SPAZIO.m).items_center().flex_wrap()
        .when(Boolean(v.marca), (e) => e.child(div().text_size(TESTO.nota).text_color(t.muted).child(v.marca)))
        .when(parto, (e) => e.child(div().text_size(TESTO.nota).text_color(t.accent).child("Da dove partirei")))
        .when(Boolean(x.gesto), (e) => e.child(div().text_size(TESTO.nota).font_semibold().text_color(t.accent).child(`Scelto: ${etichettaGesto(x.gesto, v)}`)))))
      .child(h_flex().pl(rientro).gap(SPAZIO.s + 2).items_center().flex_wrap()
        .children(GESTI_CHECKLIST.map(([g]) => this.piccolo(t, `ck-g-${v.n}-${g}`, etichettaGesto(g, v), (_e, cx) => this.gesto(v.n, g, cx), x.gesto === g)))
        .when(!nota, (e) => e.child(this.piccolo(t, `ck-n-${v.n}`, "+ Nota", (_e, cx) => this.apriNota(v.n, cx)))))
      .when(Boolean(nota), (el) => el.child(div().pl(rientro).child(h_flex().h(30).px(SPAZIO.m).items_center().rounded(RAGGIO.controllo)
        .border_1().border_color(t.accent).bg(t.background)
        .child(Input.new(nota).flex_1().h_full().text_size(TESTO.etichetta).text_color(t.foreground)))));
  }

  piede(t, testo, troppo, pronto) {
    const scelte = Object.values(this.scelte ?? {}).filter((x) => x.spunta || x.gesto).length;
    const avviso = this.mando ? "Mando…"
      : this.esci ? "Le scelte non sono partite. Esc di nuovo chiude senza mandarle."
        : troppo ? `Troppo lungo: ${testo.length} caratteri su ${TESTO_CHECKLIST_MAX}. Accorcia le note.`
          : this.persa ? `Non è arrivata: ${this.persa}. Le scelte sono rimaste: premi Manda per riprovare.`
          : testo ? `Arriva alla sessione: ${testo}` : "Spunta su cosa lavorare, o scegli Già fatto, Scarta, Rimanda.";
    return v_flex().flex_none().gap(SPAZIO.m)
      .when(!this.galleggia, (el) => el.px(SPAZIO.xxl).pt(SPAZIO.l).pb(SPAZIO.xl).border_t(1).border_color(t.border))
      .when(this.galleggia, (el) => el.pt(SPAZIO.s))
      .when(!this.galleggia, (el) => el.child(h_flex().h(PULSANTE.grande).px(SPAZIO.l).items_center().rounded(RAGGIO.riga).border_1().border_color(t.border).bg(t.raised)
        .child(Input.new(this.generale).flex_1().h_full().text_size(TESTO.corpo).text_color(t.foreground))))
      .child(div().whitespace_normal().text_size(TESTO.nota).text_color(troppo || this.esci || this.persa ? t.blocked : t.dim).child(avviso))
      // il pulsante: grande e pieno, largo quanto il blocco, perché è il gesto che conta
      .child(div().id("checklist-manda").w_full().h(PULSANTE.grande).flex().items_center().justify_center().rounded(RAGGIO.riga)
        .cursor_pointer().text_size(TESTO.riga).font_semibold()
        .bg(pronto ? t.accent : t.raised).text_color(pronto ? t.accent_foreground : t.dim)
        .when(pronto, (el) => el.hover((st) => st.opacity(0.9)))
        .on_mouse_down("left", (_e, cx) => cx.stop_propagation())
        .on_click((_e, cx) => this.manda(cx))
        .child(scelte ? `Manda · ${scelte}` : "Manda alla sessione"))
      .when(!this.galleggia, (el) => el.child(div().text_size(TESTO.etichetta).text_color(t.dim).child("Invio manda · Esc chiude")));
  }
}
