// Volta Celeste nella barra: tutte le sessioni di Claude di tutte le macchine, per macchina o per
// progetto. L'elenco lo scrive teletrasporto.py volta in ~/.cache/volta/sessioni.json ogni 30 s; un
// clic aggancia la sessione in una scheda (claude attach, via ssh se è su un'altra macchina), o la
// sposta prima in background se è aperta in un Terminale ed è ferma.
// Senza teletrasporto.py (chi usa Arturo senza le macchine di Federico) la sezione non compare.

import { div, svg } from "gpui-kit";
import { h_flex, v_flex } from "gpui-base";
import { theme, exec, readTextFile, appHome, home, run, spaces, terminals, panes, shared, setShared, watchFolder } from "herdr";
import { gruppi, titolo, dettaglio, clic, agganciata, MODI } from "./sessioni.js";
import { ICONA, punto, colore } from "./comuni.js";
import { slug, config } from "./dati.js";

const OGNI = 30000;

// Il percorso di teletrasporto.py: "volta" in arturo.json, altrimenti quello della config.
async function teletrasporto() {
  let c = {};
  try { c = JSON.parse((await readTextFile(`${appHome()}/arturo.json`)) ?? "{}"); } catch { c = {}; }
  const p = typeof c.volta === "string" && c.volta ? c.volta : `${home()}/.claude/scripts/teletrasporto.py`;
  try { return (await readTextFile(p)) ? p : null; } catch { return null; }
}

export class Volta {
  init(cx) {
    this.cartella = `${home()}/.cache/volta`;
    this.file = `${this.cartella}/sessioni.json`;
    this.dati = null;
    this.avvisi = {};
    this.sposto = {};
    this.aperti = {};
    this.script = undefined;
    this.py = "python3";
    cx.spawn(async (cx) => {
      // Il Python che installa-herdr.sh ha trovato e scritto in arturo.json: su Windows può essere "python".
      this.py = (await config()).arturo[0];
      this.script = await teletrasporto();
      if (!this.script) return cx.notify();
      await this.leggi();
      cx.notify();
      this.aggiorna(cx);
      // Un altro Volta Celeste (o /teletrasporto) che riscrive il file: lo si rilegge subito.
      try {
        for (;;) { await watchFolder(this.cartella); await this.leggi(); cx.notify(); }
      } catch { /* senza cartella resta il timer */ }
    });
    cx.timer.every(OGNI, (cx) => this.aggiorna(cx));
  }

  async leggi() {
    try {
      const testo = await readTextFile(this.file);
      if (testo) this.dati = JSON.parse(testo);
    } catch { /* un file a metà: resta l'ultima lettura buona */ }
  }

  // Un giro di teletrasporto.py volta, mai due insieme: con una macchina lenta un giro dura 10 s.
  aggiorna(cx) {
    if (!this.script || this.inCorso) return;
    this.inCorso = true;
    cx.spawn(async (cx) => {
      try {
        const r = await exec(this.py, [this.script, "volta", "--scrivi", this.file], { timeout: 60000 });
        this.errore = r.code === 0 ? null : (r.stderr || r.stdout || "").trim().split("\n").pop();
      } catch (e) {
        this.errore = String(e?.message ?? e);
      }
      setShared("arturo.volta.errore", this.errore ?? null);
      await this.leggi();
      this.inCorso = false;
      cx.notify();
    });
  }

  modo() {
    return shared("arturo.volta.gruppi") === "progetto" ? "progetto" : "macchina";
  }

  avvisa(s, testo, cx) {
    const k = s.sessionId;
    this.avvisi[k] = testo;
    cx.notify();
    cx.timer.after(7000, (cx) => { if (this.avvisi[k] === testo) { delete this.avvisi[k]; cx.notify(); } });
  }

  // Il clic su una sessione: aggancia, sposta e poi aggancia, oppure dice perché no.
  premi(s, cx) {
    if (this.sposto[s.sessionId]) return;
    const d = clic(s);
    if (d.azione === "no") return this.avvisa(s, d.motivo, cx);
    if (d.azione === "aggancia") return this.apri(s, d.argv);
    this.sposto[s.sessionId] = true;
    cx.notify();
    cx.spawn(async (cx) => {
      let esito = null;
      try {
        const r = await exec(this.py, [this.script, "porta-volta", s.host, s.sessionId], { timeout: 60000 });
        esito = JSON.parse((r.stdout || "").trim().split("\n").pop() || "{}");
      } catch (e) {
        esito = { errore: `${s.macchina} non risponde.` };
      }
      delete this.sposto[s.sessionId];
      if (esito?.attach?.length) {
        this.apri({ ...s, id: esito.id ?? s.id }, esito.attach);
        this.aggiorna(cx);
      } else this.avvisa(s, `Non la sposto: ${esito?.errore ?? "risposta vuota"}.`, cx);
      cx.notify();
    });
  }

  premiId(id, cx) {
    const s = (this.dati?.sessioni ?? []).find((x) => x.id === id || String(x.sessionId).startsWith(id));
    if (s) this.premi(s, cx);
  }

  // La scheda dell'aggancio: se c'è già la si porta davanti, altrimenti nasce nello spazio del
  // progetto (lo stesso della barra) o nello spazio "Volta" per le sessioni senza progetto.
  apri(s, argv) {
    const nome = titolo(s).slice(0, 40);
    const gia = terminals().find((x) => agganciata(x.argv, s));
    if (gia) {
      const p = panes().find((x) => x.terminal === gia.address);
      const sp = p && spaces().find((x) => x.tabs.some((tb) => tb.id === p.tab));
      if (sp) { run("space.select", { id: sp.id }); run("tab.select", { id: p.tab }); }
      run("pane.focus", { terminal: gia.address });
      return;
    }
    const nomeSpazio = s.progetto ? slug(s.progetto) : "Volta";
    const sp = spaces().find((x) => !x.machine && slug(x.name) === slug(nomeSpazio));
    const cartella = s.questa && s.cartella ? s.cartella : home();
    if (sp) {
      const tab = sp.tabs.find((tb) => tb.name === nome);
      run("space.select", { id: sp.id });
      if (tab) return run("tab.select", { id: tab.id });
      run("tab.new", { name: nome, space: sp.id, folder: cartella, argv });
    } else run("space.new", { name: nomeSpazio, folder: cartella, machine: "", tab: nome, argv });
  }

  riga(t, s, modo, cx) {
    const sposto = this.sposto[s.sessionId];
    const d = sposto ? { testo: "La sposto nella finestra…", colore: "working" } : dettaglio(s, modo);
    const avviso = this.avvisi[s.sessionId];
    const vivo = s.stato === "aspetta" || s.stato === "lavora" || s.stato === "errore";
    return v_flex().id(`v-${s.host}-${s.id}`).mx(8).px(10).py(7).gap(2).rounded(8).cursor_pointer()
      .hover((st) => st.bg(t.hover))
      .on_click((_e, cx) => this.premi(s, cx))
      .child(h_flex().gap(11).items_start()
        .child(div().pt(6).child(vivo || sposto ? punto(colore(t, d.colore)) : div().size(8).flex_none()))
        .child(v_flex().flex_1().min_w(0).gap(2)
          .child(div().truncate().text_size(14).text_color(s.vecchia ? t.muted : t.foreground).child(titolo(s)))
          .child(div().truncate().text_size(12.5).text_color(colore(t, d.colore)).child(d.testo))))
      .when(Boolean(avviso), (el) => el.child(div().pl(19).whitespace_normal().text_size(12.5).text_color(t.foreground).child(avviso)));
  }

  interruttore(t) {
    const m = this.modo();
    const voce = (k) => div().id(`volta-${k}`).flex_1().py(4).rounded(6).cursor_pointer().text_size(12.5).text_center()
      .when(m === k, (el) => el.bg(t.selected).text_color(t.foreground))
      .when(m !== k, (el) => el.text_color(t.muted).hover((s) => s.bg(t.hover)))
      .on_mouse_down("left", (_e, cx) => cx.stop_propagation())
      .on_click(() => setShared("arturo.volta.gruppi", k))
      .child(MODI[k]);
    return h_flex().mx(14).mb(4).p(2).gap(2).rounded(8).border_1().border_color(t.border).child(voce("macchina")).child(voce("progetto"));
  }

  // Un gruppo: le sessioni vive sempre; le ferme dietro "Altre N ferme", salvo un gruppo di due o meno.
  gruppo(t, g, modo, cx) {
    const vive = g.sessioni.filter((s) => s.stato !== "ferma");
    const ferme = g.sessioni.filter((s) => s.stato === "ferma");
    const tutte = (!vive.length && ferme.length <= 2) || this.aperti[g.chiave];
    const mostra = tutte ? g.sessioni : vive;
    return v_flex().gap(1)
      .child(h_flex().px(18).pb(2).gap(6).items_center()
        .child(div().flex_1().truncate().text_size(12).text_color(t.foreground).child(g.titolo))
        .when(g.sessioni.length > 0, (el) => el.child(div().text_size(12).text_color(t.dim).child(String(g.sessioni.length)))))
      .when(Boolean(g.nota), (el) => el.child(div().px(18).pb(2).text_size(12).text_color(t.dim).child(g.nota)))
      .children(mostra.map((s) => this.riga(t, s, modo, cx)))
      .when(ferme.length > 0 && (vive.length > 0 || ferme.length > 2), (el) => el.child(h_flex().id(`vf-${g.chiave || "senza"}`).mx(8).px(10).py(5).gap(8).items_center().rounded(8).cursor_pointer()
        .hover((st) => st.bg(t.hover))
        .on_click((_e, cx) => { this.aperti[g.chiave] = !this.aperti[g.chiave]; cx.notify(); })
        .child(svg(ICONA(this.aperti[g.chiave] ? "chevron-down" : "chevron-right")).size(12).text_color(t.dim))
        .child(div().text_size(12.5).text_color(t.muted).child(this.aperti[g.chiave] ? "Nascondi le ferme" : `${ferme.length} ${ferme.length > 1 ? "ferme" : "ferma"}`))));
  }

  // null quando la sezione non serve (niente teletrasporto.py su questo computer).
  render(cx) {
    if (!this.script) return null;
    const t = theme();
    const chiusa = shared("arturo.volta.chiusa") === true;
    const modo = this.modo();
    const lista = gruppi(this.dati, modo);
    const tot = (this.dati?.sessioni ?? []).length;
    const testa = h_flex().px(18).pb(4).gap(8).items_center()
      .child(h_flex().id("volta-testa").flex_1().gap(6).items_center().cursor_pointer()
        .on_click(() => setShared("arturo.volta.chiusa", !chiusa))
        .child(div().text_size(12.5).font_semibold().text_color(t.muted).child("Tutte le sessioni"))
        .when(tot > 0, (el) => el.child(div().text_size(12).text_color(t.dim).child(String(tot))))
        .child(svg(ICONA(chiusa ? "chevron-right" : "chevron-down")).size(12).text_color(t.dim)));
    let corpo;
    if (chiusa) corpo = null;
    else if (!this.dati) corpo = div().px(18).py(4).text_size(13).text_color(t.muted).child(this.errore ? "Non riesco a leggere le sessioni delle macchine." : "Leggo le sessioni delle macchine…");
    else if (!lista.length) corpo = div().px(18).py(4).text_size(13).text_color(t.muted).child("Nessuna sessione aperta.");
    // Un elenco suo, alto al massimo 360 px: i progetti sotto restano a vista.
    else corpo = v_flex().id("volta-elenco").max_h(360).overflow_y_scrollbar().gap(10).children(lista.map((g) => this.gruppo(t, g, modo, cx)));
    const vecchio = this.dati && this.errore && this.dati.letto ? `Non riesco ad aggiornare: lettura delle ${String(this.dati.letto).slice(11, 16)}.` : null;
    return v_flex().id("volta").pb(12).mb(12).gap(4).border_b(1).border_color(t.border)
      .child(testa)
      .when(!chiusa, (el) => el.child(this.interruttore(t)))
      .when(Boolean(vecchio) && !chiusa, (el) => el.child(div().px(18).text_size(12).text_color(t.blocked).child(vecchio)))
      .when(Boolean(corpo), (el) => el.child(corpo));
  }
}
