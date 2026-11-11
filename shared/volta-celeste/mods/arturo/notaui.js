// La parte "nota": il velo su tutta la finestra per lasciare a Claude una nota su un punto preciso (⌘⇧N).
// All'apertura il velo mostra le note aperte del progetto come segni numerati: un clic su un segno apre la
// nota col suo filo, e da lì Federico risponde, la dà per risolta o la scarta. Un clic altrove sceglie il
// punto di una nota nuova: il segno nel punto, le pastiglie del tipo e il campo accanto; Invio manda, Esc
// annulla. Lo screenshot lo fa barra.js prima di aprire il velo, nella cartella che arriva nei props.

import { div } from "gpui-kit";
import { v_flex, h_flex, InputState, Input } from "gpui-base";
import { theme, props, closeOverlay, notify, setShared, shared, spaces, writeTextFile, layout, focused, panes, hc,
  exec, home } from "herdr";
import { todo, gestoNota, config } from "./dati.js";
import { nota, progettoNota, evidenza, misureDaLayout, ultimeRighe, TIPI, TIPO_PREDEFINITO, etichettaTipo,
  leggiNota, noteAperte, prossimoNumero, segno, cartellaNote, LEGGI_NOTE } from "./nota.js";

// I bottoni della scheda e i verbi di arturo note.
const VERBI = { rispondi: "rispondi", risolta: "risolvi", scarta: "scarta" };

const CAMPO = 360;
const SCHEDA = 380;
const SEGNO = 22;
const ARANCIO = "#f2a24a";
const VELO = "#05080c66";
const PARTI = ["marchio", "barra", "piede", "testata", "todo", "stato", "benvenuto"];

const misure = (finestra) => misureDaLayout(layout(),
  Object.fromEntries(PARTI.map((x) => [x, shared(`arturo.misura.${x}`) ?? null])), finestra);

// Gli elementi sotto un punto, da Volta Celeste: window.elements() dice dove sta ogni elemento con un id,
// di qualunque parte. Herdr e una Volta più vecchia non ce l'hanno: lì il velo segue le parti, come prima.
const W = globalThis.window;
const ELEMENTI = typeof W?.elements === "function" && typeof W?.track_elements === "function";
function segui(acceso) {
  if (!ELEMENTI) return;
  try { W.track_elements(acceso); } catch { /* il velo segue le parti */ }
}
function elementi(punto) {
  if (!ELEMENTI || !punto) return [];
  try { return W.elements({ x: punto.x, y: punto.y }) ?? []; } catch { return []; }
}
// Ciò che sta sotto un punto: l'elemento se la finestra lo riporta, altrimenti la parte.
const sotto = (punto, finestra) => (punto && finestra ? evidenza(punto, misure(finestra), elementi(punto)) : null);
const chiave = (ev) => (ev ? `${ev.elemento?.id ?? ""}|${ev.blocco}|${ev.rettangolo.x},${ev.rettangolo.y},${ev.rettangolo.larghezza},${ev.rettangolo.altezza}` : "");

// Su cosa è la nota: l'elemento e la parte della finestra sotto il punto e, se è la sessione, il terminale
// attivo con le sue ultime 40 righe. Senza regione (misure assenti o vecchie) restano terminale e cwd.
async function doveNota(punto, misura) {
  const ev = sotto(punto, misura);
  const dove = { blocco: ev?.blocco ?? null, parte: ev?.parte ?? null, elemento: ev?.elemento ?? null,
    terminale: null, titolo: null, cwd: null, testo_terminale: null };
  if (dove.blocco && dove.blocco !== "main") return dove;
  const f = focused();
  if (!f?.terminal) return dove;
  dove.terminale = f.terminal;
  dove.cwd = f.cwd ?? null;
  dove.titolo = panes().find((x) => x.terminal === f.terminal)?.title ?? null;
  try {
    const out = await hc(["read", f.terminal]);
    if (out?.code === 0) dove.testo_terminale = ultimeRighe(out.stdout) || null;
  } catch { /* la nota parte senza il testo */ }
  return dove;
}

// Tutte le note della cartella: [{ nota, testo }] con il testo del file com'era, che serve per riscriverlo
// solo se nessun altro (la CLI di Claude) l'ha cambiato nel frattempo. null se la lettura non riesce: chi
// conta le risposte di Claude (la barra di stato) tiene allora l'ultima lettura buona.
export async function leggiTutte(py) {
  try {
    const r = await exec(py, ["-c", LEGGI_NOTE, cartellaNote(home())], { timeout: 10000 });
    if (r.code !== 0) return null;
    return JSON.parse(r.stdout).map(([id, testo]) => ({ nota: leggiNota(testo, id), testo })).filter((x) => x.nota);
  } catch {
    return null;
  }
}

const json = (d) => JSON.stringify(d, null, 2);

export class Nota {
  init(_p, cx) {
    this.punto = null;
    this.sopra = null;      // il punto sotto il puntatore: ciò che ha sotto prende il riquadro, come in Agentation
    this.vista = "";        // la chiave di ciò che il riquadro mostra: il velo si ridisegna solo quando cambia
    this.misura = null;
    this.dim = null;        // la misura del velo, da on_size_change: serve ai segni prima di ogni clic
    this.invio = false;
    this.tipo = TIPO_PREDEFINITO;
    this.tutte = [];        // [{ nota, testo }]
    this.aperte = [];       // le note aperte o prese del progetto, coi numeri
    this.aperta = null;     // la nota della scheda aperta
    this.progetto = null;
    this.py = "python3";
    this.input = InputState.new({ placeholder: "Cosa non va, o cosa vorresti?" });
    this.input.on("submit", (_e, cx) => this.manda(cx));
    this.risposta = InputState.new({ placeholder: "Rispondi, o scrivi perché la chiudi" });
    this.risposta.on("submit", (_e, cx) => this.azione(cx, "rispondi"));
    segui(true);
    cx.spawn(async (cx) => {
      const c = await config();
      this.py = c.arturo[0];
      const s = spaces().find((x) => x.active);
      this.progetto = progettoNota(c.note_progetto, s && !s.machine && s.named ? s.name : null);
      await this.ricarica();
      // props.apri: il velo si apre già sulla scheda di quella nota (dall'elenco delle note, noteui.js).
      const apri = props().apri;
      if (apri) this.aperta = this.aperte.find((n) => n.id === apri) ?? null;
      cx.notify();
    });
  }

  async ricarica() {
    this.tutte = (await leggiTutte(this.py)) ?? [];
    this.aperte = noteAperte(this.tutte.map((x) => x.nota), this.progetto);
    if (this.aperta) this.aperta = this.aperte.find((n) => n.id === this.aperta.id) ?? null;
  }

  chiudi() { closeOverlay(props().overlay); }
  // Esc e ogni altra chiusura passano di qui (main.js): la finestra smette di annotare gli elementi.
  close() { segui(false); }

  manda(cx) {
    if (this.invio || !this.punto) return;
    const s = spaces().find((x) => x.active);
    const schermo = s ? s.name : null;
    this.invio = true;
    cx.spawn(async (cx) => {
      const c = await config();
      const progetto = progettoNota(c.note_progetto, s && !s.machine && s.named ? s.name : null);
      const cartella = props().cartella;
      const dove = await doveNota(this.punto, this.misura);
      const aperte = progetto === this.progetto ? this.aperte : noteAperte(this.tutte.map((x) => x.nota), progetto);
      const n = nota({ testo: this.input.value(), ...this.punto, ...this.misura, progetto, cartella, schermo,
        quando: new Date().toISOString(), dove, tipo: this.tipo, numero: prossimoNumero(aperte) });
      if (!n) { this.invio = false; cx.notify(); return; }
      const file = `${cartella}/nota.json`;
      let scritto = null;
      try { await writeTextFile(file, json(n.dati), null); scritto = json(n.dati); } catch { /* la nota parte lo stesso */ }
      let r = { ok: true };
      if (n.argv) r = await todo(n.argv);
      // L'id del todo nella nota: Claude e la finestra chiudono l'uno con l'altra.
      if (r.ok && r.json?.id != null && scritto) {
        try { await writeTextFile(file, json({ ...n.dati, todo: r.json.id }), scritto); } catch { /* resta senza todo */ }
      }
      setShared("arturo.scritto", Date.now());
      this.chiudi();
      if (!n.argv) notify({ title: "Nota salvata", body: `Nessun progetto aperto: la trovi in ${cartella}`, level: "info", timeout: 6000 });
      else if (r.ok) notify({ title: `Nota ${n.dati.numero} mandata a Claude`, body: `La trovi fra le cose da fare di ${progetto}.`, level: "success", timeout: 4000 });
      else notify({ title: "Nota salvata, ma non fra le cose da fare", body: `${r.errore} · La nota è in ${cartella}`, level: "warning" });
    });
  }

  // Rispondi, Risolta o Scarta sulla nota aperta: tutto passa da `arturo note <verbo> --chi federico`, lo
  // stesso codice con cui Claude chiude le note. La CLI riscrive nota.json e porta il gesto sul todo
  // collegato (una nota, fatto o scartato); se Claude l'ha già chiusa, lo dice e il velo rilegge.
  azione(cx, che) {
    const n = this.aperta;
    if (!n || this.invio) return;
    const testo = this.risposta.value();
    if (che === "rispondi" && !String(testo ?? "").trim()) return;
    this.invio = true;
    cx.notify();
    cx.spawn(async (cx) => {
      const r = await gestoNota(VERBI[che], n.id, testo);
      this.invio = false;
      if (!r.ok) {
        await this.ricarica();
        notify({ title: `La nota ${n.numero} non è cambiata`, body: r.errore, level: "warning", timeout: 6000 });
        cx.notify();
        return;
      }
      if (n.todo != null) setShared("arturo.scritto", Date.now());
      this.risposta.set_value("");
      if (che !== "rispondi") this.aperta = null;
      await this.ricarica();
      const esito = r.json?.todo_esito ?? "";
      if (esito.startsWith("Attenzione")) notify({ title: `Nota ${n.numero}: il todo non è cambiato`, body: esito, level: "warning", timeout: 6000 });
      else if (che !== "rispondi") notify({ title: `Nota ${n.numero} ${che === "risolta" ? "risolta" : "scartata"}`, body: n.testo, level: "success", timeout: 3000 });
      cx.notify();
    });
  }

  // Un riquadro largo w e alto h accanto al punto p: a destra, o a sinistra se non ci entra; sotto, o sopra
  // vicino al fondo.
  accanto(p, w, h) {
    const m = this.misura ?? this.dim;
    if (!p || !m) return { x: 0, y: 0 };
    const x = p.x + 24 + w > m.larghezza ? Math.max(12, p.x - 24 - w) : p.x + 24;
    const y = p.y + h > m.altezza ? Math.max(12, m.altezza - h - 12) : Math.max(12, p.y - 8);
    return { x, y };
  }

  // Cosa mettere in luce: ciò che sta sotto la nota aperta, poi sotto il punto scelto, poi sotto il
  // puntatore. null se mancano sia gli elementi sia le misure delle parti: il velo resta intero.
  inLuce() {
    const f = this.misura?.larghezza ? this.misura : this.dim;
    if (!f) return null;
    const p = this.aperta ? segno(this.aperta, this.dim) : (this.punto ?? this.sopra);
    return sotto(p, f);
  }

  // Il riquadro e l'etichetta di ciò che è in luce. Niente id né gestori: i clic passano al velo.
  riquadro(t, ev) {
    const q = ev.rettangolo, e = ev.etichetta;
    return [
      div().absolute().left(q.x).top(q.y).w(q.larghezza).h(q.altezza).rounded(4).border_2().border_color(ARANCIO).bg("#f2a24a14"),
      div().absolute().left(e.x + (e.dentro ? 4 : 0)).top(e.y).px(8).py(2).rounded(4).bg(ARANCIO)
        .text_size(11.5).font_semibold().text_color("#1a1206").child(ev.nome),
    ];
  }

  pastiglie(t) {
    return h_flex().gap(6).flex_wrap().children(TIPI.map((k) => {
      const scelto = k.id === this.tipo;
      return div().id(`nota-tipo-${k.id}`).px(9).py(3).rounded_full().cursor_pointer().text_size(12)
        .border_1().border_color(scelto ? t.accent : t.border).bg(scelto ? t.accent : t.raised)
        .text_color(scelto ? t.accent_foreground : t.muted)
        .hover((s) => s.opacity(0.9))
        .on_click((_e, cx) => { this.tipo = k.id; cx.notify(); })
        .child(k.etichetta);
    }));
  }

  segni(t) {
    return this.aperte.map((n) => {
      const q = segno(n, this.dim);
      const presa = n.stato === "presa";
      const scelto = this.aperta?.id === n.id;
      return h_flex().id(`nota-segno-${n.id}`).absolute().left(q.x - SEGNO / 2).top(q.y - SEGNO / 2).size(SEGNO)
        .items_center().justify_center().rounded_full().cursor_pointer().border_2()
        .border_color(scelto ? t.foreground : t.accent).bg(presa ? t.popover : ARANCIO)
        .text_size(11.5).font_semibold().text_color(presa ? t.foreground : "#1a1206")
        .on_mouse_down("left", (_e, cx) => {
          cx.stop_propagation();
          if (this.punto) return;
          this.aperta = scelto ? null : n;
          cx.notify();
        })
        .child(String(n.numero));
    });
  }

  scheda(t) {
    const n = this.aperta;
    const q = segno(n, this.dim);
    const pos = this.accanto(q, SCHEDA, 300);
    const voce = (v) => v_flex().gap(2)
      .child(div().text_size(11.5).text_color(v.chi === "claude" ? t.accent : t.muted).child(v.chi === "claude" ? "Claude" : "Tu"))
      .child(div().text_size(13).text_color(t.foreground).child(v.testo));
    const bottone = (id, testo, primario, fa) => div().id(id).px(primario ? 12 : 10).py(5).rounded(6).cursor_pointer()
      .text_size(12.5).when(primario, (s) => s.bg(t.accent).text_color(t.accent_foreground).font_semibold())
      .when(!primario, (s) => s.text_color(t.muted).hover((x) => x.bg(t.hover)))
      .on_click((_e, cx) => fa(cx)).child(testo);
    return v_flex().id("nota-scheda").absolute().left(pos.x).top(pos.y).w(SCHEDA).p(12).gap(10).rounded(10)
      .bg(t.popover).border_1().border_color(t.border).cursor_default()
      .on_mouse_down("left", (_e, cx) => cx.stop_propagation())
      .child(h_flex().gap(8).items_center()
        .child(div().text_size(12.5).font_semibold().text_color(t.foreground).child(`Nota ${n.numero}`))
        .child(div().px(8).py(1).rounded_full().bg(t.raised).text_size(11.5).text_color(t.muted).child(etichettaTipo(n.tipo)))
        .when(n.stato === "presa", (el) => el.child(div().text_size(11.5).text_color(t.accent).child("Claude ci lavora"))))
      .child(v_flex().gap(8).children(n.filo.slice(-6).map(voce)))
      .child(h_flex().h(36).px(10).items_center().rounded(8).border_1().border_color(t.border).bg(t.raised)
        .child(Input.new(this.risposta).flex_1().h_full().text_size(13).text_color(t.foreground)))
      .child(h_flex().gap(6).justify_end()
        .child(bottone("nota-scarta", "Scarta", false, (cx) => this.azione(cx, "scarta")))
        .child(bottone("nota-risolta", "Risolta", false, (cx) => this.azione(cx, "risolta")))
        .child(bottone("nota-rispondi", this.invio ? "Scrivo…" : "Rispondi", true, (cx) => this.azione(cx, "rispondi"))));
  }

  render() {
    const t = theme();
    const p = this.punto;
    const campo = this.accanto(p, CAMPO, 150);
    const quante = this.aperte.length;
    const ev = this.inLuce();
    this.vista = chiave(ev);
    const invito = (ev ? (ELEMENTI ? "Passa su un elemento e clicca quello di cui vuoi parlare" : "Passa su una parte e clicca il punto di cui vuoi parlare") : "Clicca il punto di cui vuoi parlare") +
      (quante ? ` · ${quante === 1 ? "1 nota aperta" : `${quante} note aperte`}: clicca un numero per leggerla` : "") +
      " · Esc annulla";
    return v_flex().id("nota-velo").size_full().relative().cursor_crosshair().when(!ev, (el) => el.bg(VELO))
      .on_mouse_move((e, cx) => {
        if (this.punto || this.aperta) return;
        this.sopra = { x: e.position.x, y: e.position.y };
        if (chiave(sotto(this.sopra, this.dim)) !== this.vista) cx.notify();
      })
      .on_size_change((m, cx) => {
        const d = { larghezza: Math.round(m.width), altezza: Math.round(m.height) };
        if (d.larghezza === this.dim?.larghezza && d.altezza === this.dim?.altezza) return;
        this.dim = d;
        cx?.notify?.();
      })
      .on_mouse_down("left", (e, cx) => {
        if (this.punto) return;
        if (this.aperta) { this.aperta = null; cx.notify(); return; }
        const b = e.bounds;
        this.punto = { x: e.position.x, y: e.position.y };
        this.misura = { larghezza: b ? b.width : 0, altezza: b ? b.height : 0 };
        this.input.focus();
        cx.notify();
      })
      .when(Boolean(ev), (el) => el
        .children(ev.fasce.map((f) => div().absolute().left(f.x).top(f.y).w(f.larghezza).h(f.altezza).bg(VELO)))
        .children(this.riquadro(t, ev)))
      .when(!p, (el) => el.children(this.segni(t)))
      .when(!p && !this.aperta, (el) => el.child(h_flex().absolute().top(18).left(0).w_full().justify_center()
        .child(div().px(16).py(8).rounded(8).bg(t.popover).border_1().border_color(t.border)
          .text_size(13.5).text_color(t.foreground).child(invito))))
      .when(!p && Boolean(this.aperta), (el) => el.child(this.scheda(t)))
      .when(Boolean(p), (el) => el
        .child(div().absolute().left(p.x - 9).top(p.y - 9).size(18).rounded_full().border_2().border_color(t.accent).bg(ARANCIO))
        .child(v_flex().absolute().left(campo.x).top(campo.y).w(CAMPO).p(12).gap(8).rounded(10).bg(t.popover)
          .border_1().border_color(t.border).cursor_default()
          .on_mouse_down("left", (_e, cx) => cx.stop_propagation())
          .child(div().text_size(12.5).text_color(t.muted).child(`Nota ${prossimoNumero(this.aperte)} per Claude${ev ? ` su ${ev.nome}` : " su questo punto"}`))
          .child(this.pastiglie(t))
          .child(h_flex().h(38).px(10).items_center().rounded(8).border_1().border_color(t.accent).bg(t.raised)
            .child(Input.new(this.input).flex_1().h_full().text_size(13.5).text_color(t.foreground)))
          .child(h_flex().gap(8).justify_end()
            .child(div().id("nota-annulla").px(10).py(5).rounded(6).cursor_pointer().text_size(12.5).text_color(t.muted)
              .hover((s) => s.bg(t.hover)).on_click(() => this.chiudi()).child("Annulla"))
            .child(div().id("nota-manda").px(12).py(5).rounded(6).cursor_pointer().bg(t.accent)
              .text_color(t.accent_foreground).text_size(12.5).font_semibold()
              .hover((s) => s.opacity(0.9)).on_click((_e, cx) => this.manda(cx))
              .child(this.invio ? "Mando…" : "Manda a Claude")))));
  }
}
