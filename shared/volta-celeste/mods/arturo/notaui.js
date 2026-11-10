// La parte "nota": il velo su tutta la finestra per lasciare a Claude una nota su un punto preciso (⌘⇧N).
// Prima fase: "Clicca il punto". Seconda: il segno nel punto e il campo accanto; Invio manda, Esc annulla.
// Lo screenshot lo fa barra.js prima di aprire il velo, nella cartella che arriva nei props.

import { div } from "gpui-kit";
import { v_flex, h_flex, InputState, Input } from "gpui-base";
import { theme, props, closeOverlay, notify, setShared, shared, spaces, writeTextFile, layout, focused, panes, hc } from "herdr";
import { todo, config } from "./dati.js";
import { nota, progettoNota, regione, misureDaLayout, ultimeRighe } from "./nota.js";

const CAMPO = 360;
const PARTI = ["marchio", "barra", "piede", "testata", "todo", "stato", "benvenuto"];

// Su cosa è la nota: la parte della finestra sotto il punto e, se è la sessione, il terminale attivo con le
// sue ultime 40 righe. Senza regione (misure assenti o vecchie) restano terminale e cwd.
async function doveNota(punto, misura) {
  const parti = Object.fromEntries(PARTI.map((x) => [x, shared(`arturo.misura.${x}`) ?? null]));
  const r = regione(punto, misureDaLayout(layout(), parti, misura));
  const dove = { blocco: r?.blocco ?? null, parte: r?.parte ?? null, terminale: null, titolo: null, cwd: null, testo_terminale: null };
  if (r && r.blocco !== "main") return dove;
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

export class Nota {
  init(_p, cx) {
    this.punto = null;
    this.misura = null;
    this.invio = false;
    this.input = InputState.new({ placeholder: "Cosa non va, o cosa vorresti?" });
    this.input.on("submit", (_e, cx) => this.manda(cx));
  }

  chiudi() { closeOverlay(props().overlay); }

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
      const n = nota({ testo: this.input.value(), ...this.punto, ...this.misura, progetto, cartella, schermo,
        quando: new Date().toISOString(), dove });
      if (!n) { this.invio = false; cx.notify(); return; }
      try { await writeTextFile(`${cartella}/nota.json`, JSON.stringify(n.dati, null, 2), null); } catch { /* la nota parte lo stesso */ }
      let r = { ok: true };
      if (n.argv) r = await todo(n.argv);
      setShared("arturo.scritto", Date.now());
      this.chiudi();
      if (!n.argv) notify({ title: "Nota salvata", body: `Nessun progetto aperto: la trovi in ${cartella}`, level: "info", timeout: 6000 });
      else if (r.ok) notify({ title: "Nota mandata a Claude", body: `La trovi fra le cose da fare di ${progetto}.`, level: "success", timeout: 4000 });
      else notify({ title: "Nota salvata, ma non fra le cose da fare", body: `${r.errore} · La nota è in ${cartella}`, level: "warning" });
    });
  }

  render() {
    const t = theme();
    const p = this.punto;
    const m = this.misura;
    // Il campo sta a destra del punto, o a sinistra se non ci entra; sotto, o sopra vicino al fondo.
    const campoX = p && m ? (p.x + 24 + CAMPO > m.larghezza ? Math.max(12, p.x - 24 - CAMPO) : p.x + 24) : 0;
    const campoY = p && m ? (p.y + 120 > m.altezza ? Math.max(12, p.y - 120) : p.y - 8) : 0;
    return v_flex().id("nota-velo").size_full().relative().cursor_crosshair().bg("#05080c66")
      .on_mouse_down("left", (e, cx) => {
        if (this.punto) return;
        const b = e.bounds;
        this.punto = { x: e.position.x, y: e.position.y };
        this.misura = { larghezza: b ? b.width : 0, altezza: b ? b.height : 0 };
        this.input.focus();
        cx.notify();
      })
      .when(!p, (el) => el.child(h_flex().absolute().top(18).left(0).w_full().justify_center()
        .child(div().px(16).py(8).rounded(8).bg(t.popover).border_1().border_color(t.border)
          .text_size(13.5).text_color(t.foreground).child("Clicca il punto di cui vuoi parlare · Esc annulla"))))
      .when(Boolean(p), (el) => el
        .child(div().absolute().left(p.x - 9).top(p.y - 9).size(18).rounded_full().border_2().border_color(t.accent).bg("#f2a24a"))
        .child(v_flex().absolute().left(campoX).top(campoY).w(CAMPO).p(12).gap(8).rounded(10).bg(t.popover)
          .border_1().border_color(t.border).cursor_default()
          .on_mouse_down("left", (_e, cx) => cx.stop_propagation())
          .child(div().text_size(12.5).text_color(t.muted).child("Nota per Claude su questo punto"))
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
