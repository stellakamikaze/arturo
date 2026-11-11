// Volta Celeste nella barra: tutte le sessioni di Claude di tutte le macchine, per macchina o per
// progetto. L'elenco lo scrive volta_sonda.py (accanto a questo file) in ~/.cache/volta/sessioni.json ogni 30 s,
// con le macchine aggiunte a Herdr (#5172); un
// clic aggancia la sessione in una scheda (claude attach, via ssh se è su un'altra macchina), o la
// sposta prima in background se è aperta in un Terminale ed è ferma.
// Spostare in background una sessione aperta in un Terminale (porta-volta) resta a teletrasporto.py, se c'è.
// "Altro" su una sessione in background: anteprima (ultima risposta e ultima azione), ferma, riavvia, elimina (#5172 passo 4).
// Una sessione che passa a "ti aspetta", di qualunque macchina, dà un avviso; lo stato di ogni sessione
// va in shared arturo.volta.stati per le schede che agganciano una sessione in background.

import { div, svg } from "gpui-kit";
import { h_flex, v_flex } from "gpui-base";
import { theme, exec, readTextFile, home, shared, setShared, watchFolder, notify } from "herdr";
import { gruppi, titolo, dettaglio, clic, MODI, azioni, anteprima, nuoveInAttesa, statiCorti } from "./sessioni.js";
import { ICONA, punto, colore } from "./comuni.js";
import { config, apriSessione, mostra, azioneSessione } from "./dati.js";

const OGNI = 30000;

async function esiste(p) {
  try { return (await readTextFile(p)) ? p : null; } catch { return null; }
}

// Lo script dell'elenco: volta_sonda.py come lo dice config() di dati.js, se c'è.
// Quello che sposta le sessioni del Terminale: teletrasporto.py della config, se c'è.
async function script(c) {
  return { elenco: await esiste(c.volta), sposta: await esiste(`${home()}/.claude/scripts/teletrasporto.py`) };
}

export class Volta {
  init(cx) {
    this.cartella = `${home()}/.cache/volta`;
    this.file = `${this.cartella}/sessioni.json`;
    this.dati = null;
    this.avvisi = {};
    this.sposto = {};
    this.apro = {};        // sessionId -> true mentre il clic prepara la scheda (servizio, respawn)
    this.aperti = {};
    this.menu = null;      // la sessione con i gesti aperti
    this.anteprime = {};   // sessionId -> true (risposta e azione lette dalla riga) o righe di claude logs
    this.chiedo = {};      // sessionId -> verbo che aspetta la conferma
    this.faccio = {};      // sessionId -> verbo in corso
    this.sopra = null;     // la sessione sotto il puntatore: lì compare la X
    this.script = undefined;
    this.py = "python3";
    cx.spawn(async (cx) => {
      // Il Python che installa-herdr.sh ha trovato e scritto in arturo.json: su Windows può essere "python".
      const c = await config();
      this.py = c.arturo[0];
      const sc = await script(c);
      this.script = sc.elenco;
      this.sposta = sc.sposta;
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
    const prima = this.dati;
    try {
      const testo = await readTextFile(this.file);
      if (testo) this.dati = JSON.parse(testo);
    } catch { /* un file a metà: resta l'ultima lettura buona */ }
    if (this.dati !== prima) {
      for (const s of nuoveInAttesa(prima, this.dati))
        notify({ title: `${titolo(s)} ti aspetta`, body: `Su ${s.macchina}: aprila da Tutte le sessioni.`, level: "info" });
      const st = statiCorti(this.dati);
      if (JSON.stringify(st) !== JSON.stringify(shared("arturo.volta.stati") ?? {})) setShared("arturo.volta.stati", st);
    }
    // Le macchine per la riga "Nasce su" (dati.js altreMacchine), scritte solo quando cambiano.
    const m = (this.dati?.macchine ?? []).map((x) => ({ host: x.host, macchina: x.macchina, questa: Boolean(x.questa), giu: Boolean(x.irraggiungibile) }));
    if (JSON.stringify(m) !== JSON.stringify(shared("arturo.volta.macchine") ?? [])) setShared("arturo.volta.macchine", m);
  }

  // Un giro di volta_sonda.py volta, mai due insieme: con una macchina lenta un giro dura qualche secondo.
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
    // Senza una scelta della persona vale "per progetto": chi apre Volta cerca il lavoro, non la macchina.
    return shared("arturo.volta.gruppi") === "macchina" ? "macchina" : "progetto";
  }

  avvisa(s, testo, cx) {
    const k = s.sessionId;
    this.avvisi[k] = testo;
    cx.notify();
    cx.timer.after(7000, (cx) => { if (this.avvisi[k] === testo) { delete this.avvisi[k]; cx.notify(); } });
  }

  // Il clic su una sessione: aggancia, sposta e poi aggancia, oppure dice perché no.
  premi(s, cx) {
    if (this.sposto[s.sessionId] || this.apro[s.sessionId]) return;
    let d = clic(s);
    // la scheda che la ospita non è in questa finestra: vale la regola di un'interattiva in un Terminale
    if (d.azione === "mostra") { if (mostra(d.terminale)) return; d = clic({ ...s, terminale: null }); }
    if (d.azione === "no") return this.avvisa(s, d.motivo, cx);
    if (d.azione === "aggancia") return this.apri(s, d.argv, false, cx);
    // senza teletrasporto.py nessuno sa scrivere /bg nel Terminale di quella sessione
    if (!this.sposta) return this.avvisa(s, "È aperta in un Terminale: aprila da lì.", cx);
    this.sposto[s.sessionId] = true;
    cx.notify();
    cx.spawn(async (cx) => {
      let esito = null;
      try {
        const r = await exec(this.py, [this.sposta, "porta-volta", s.host, s.sessionId], { timeout: 60000 });
        esito = JSON.parse((r.stdout || "").trim().split("\n").pop() || "{}");
      } catch (e) {
        esito = { errore: `${s.macchina} non risponde.` };
      }
      delete this.sposto[s.sessionId];
      if (esito?.attach?.length) {
        this.apri({ ...s, id: esito.id ?? s.id }, esito.attach, true, cx);
        this.aggiorna(cx);
      } else this.avvisa(s, `Non la sposto: ${esito?.errore ?? "risposta vuota"}.`, cx);
      cx.notify();
    });
  }

  // Apre la sessione in una scheda con Claude dentro (dati.js apriSessione): prima il servizio di Claude,
  // il riavvio se era in errore, poi la scheda. Se Claude esce subito dalla scheda, lo dice la riga.
  apri(s, argv, pronta, cx) {
    const k = s.sessionId;
    this.apro[k] = true;
    cx.notify();
    cx.spawn(async (cx) => {
      let r;
      try { r = await apriSessione(s, argv, pronta); } catch (e) { r = { errore: `Non la apro: ${String(e?.message ?? e).slice(0, 120)}.` }; }
      delete this.apro[k];
      if (r.errore) this.avvisa(s, r.errore, cx);
      if (r.riavviata) this.aggiorna(cx);
      cx.notify();
      const v = r.veglia ? await r.veglia : null;
      if (v?.errore) this.avvisa(s, v.errore, cx);
      if (v?.riavviata) this.aggiorna(cx);
      if (v?.errore || v?.riavviata) cx.notify();
    });
  }

  // Dal comando `do` può arrivare l'id di una sessione appena nata, che il giro in corso non ha
  // ancora scritto nell'elenco: si dice, invece di non fare niente (#5078).
  trovaId(id) {
    const s = (this.dati?.sessioni ?? []).find((x) => x.id === id || String(x.sessionId).startsWith(id));
    if (!s) notify({ title: `Non trovo la sessione ${id}`, body: "L'elenco si aggiorna fra pochi secondi: riprova.", level: "warning" });
    return s;
  }

  premiId(id, cx) {
    const s = this.trovaId(id);
    if (s) this.premi(s, cx);
  }

  // "arturo.volta-altro-<id>" e "arturo.volta-gesto-<verbo>-<id>": il clic su "Altro" e su un suo
  // bottone, da herdr-app do. Herdr non ha clic simulati: le prove dei gesti passano da qui (#5203).
  altroId(id, cx) {
    const s = this.trovaId(id);
    if (!s) return;
    if (!azioni(s).length) return notify({ title: "Niente gesti su questa sessione", body: "Altro c'è solo sulle sessioni in background.", level: "warning" });
    this.menu = this.menu === s.sessionId ? null : s.sessionId;
    this.scopri(s);
    cx.notify();
  }

  // Una sessione ferma sta dietro "N ferme": il comando che ne apre i gesti apre anche il suo gruppo.
  scopri(s) {
    const g = gruppi(this.dati, this.modo()).find((x) => x.sessioni.some((y) => y.sessionId === s.sessionId));
    if (g && s.stato === "ferma") this.aperti[g.chiave] = true;
  }

  gestoId(verbo, id, cx) {
    const s = this.trovaId(id);
    if (!s) return;
    const a = azioni(s).find((x) => x.verbo === verbo);
    if (!a) return notify({ title: `${verbo}: gesto che qui non c'è`, body: `Su questa sessione: ${azioni(s).map((x) => x.verbo).join(", ") || "nessuno"}.`, level: "warning" });
    this.menu = s.sessionId;
    this.scopri(s);
    this.fare(s, a, cx);
  }

  // Un gesto di "Altro": l'anteprima resta sotto la riga, gli altri rileggono l'elenco. Elimina chiede
  // prima la conferma, con un secondo clic sullo stesso bottone.
  fare(s, a, cx) {
    const k = s.sessionId;
    if (this.faccio[k]) return;
    if (a.conferma && this.chiedo[k] !== a.verbo) { this.chiedo[k] = a.verbo; return cx.notify(); }
    delete this.chiedo[k];
    if (a.verbo === "logs" && this.anteprime[k]) { delete this.anteprime[k]; return cx.notify(); }
    // L'anteprima viene dalla riga già letta (#5240): niente comando, e segue le letture dopo.
    if (a.verbo === "logs" && anteprima(s)) { this.anteprime[k] = true; return cx.notify(); }
    this.faccio[k] = a.verbo;
    cx.notify();
    cx.spawn(async (cx) => {
      const r = await azioneSessione(s, a.verbo);
      delete this.faccio[k];
      if (r.errore) this.avvisa(s, `Non riesco: ${r.errore}`, cx);
      else if (a.verbo === "logs") this.anteprime[k] = r.righe?.length ? r.righe : ["(niente da mostrare)"];
      else {
        this.avvisa(s, { stop: "Fermata: un clic la riapre.", respawn: "Riavviata.", rm: "Eliminata." }[a.verbo], cx);
        if (a.verbo === "rm") this.menu = null;
        this.aggiorna(cx);
      }
      cx.notify();
    });
  }

  gesti(t, s, az) {
    const k = s.sessionId;
    const bottone = (a) => {
      const testo = this.faccio[k] === a.verbo ? "…" : this.chiedo[k] === a.verbo ? a.conferma
        : a.verbo === "logs" && this.anteprime[k] ? "Chiudi l'anteprima" : a.testo;
      return div().id(`vg-${s.host}-${s.id}-${a.verbo}`).px(8).py(3).rounded(6).cursor_pointer()
        .text_size(12).border_1().border_color(this.chiedo[k] === a.verbo ? t.blocked : t.border)
        .text_color(this.chiedo[k] === a.verbo ? t.blocked : t.muted)
        .hover((st) => st.bg(t.selected))
        .on_click((_e, cx) => this.fare(s, a, cx))
        .child(testo);
    };
    // Risposta e azione vanno a capo; lo schermo di claude logs (senza trascrizione) resta a righe fisse.
    const vista = this.anteprime[k];
    const blocchi = vista === true ? anteprima(s) : vista ? [{ schermo: true, righe: vista }] : null;
    const rigo = (b, r, id) => b.schermo
      ? div().id(id).truncate().font_family("Atkinson Hyperlegible Mono").text_size(11.5).text_color(t.muted).child(r || " ")
      : div().id(id).whitespace_normal().text_size(12.5).text_color(t.foreground).child(r);
    return v_flex().gap(6)
      .child(h_flex().gap(6).flex_wrap().children(az.map(bottone)))
      .when(Boolean(blocchi), (el) => el.child(v_flex().p(8).gap(8).rounded(6).bg(t.hover).overflow_hidden()
        .children(blocchi.map((b, i) => v_flex().gap(2)
          .when(Boolean(b.etichetta), (e) => e.child(div().text_size(11).text_color(t.dim).child(b.etichetta)))
          .children(b.righe.map((r, j) => rigo(b, r, `vl-${s.id}-${i}-${j}`)))))));
  }

  // I gesti di "Altro" stanno sotto l'elenco, fuori dalla parte che scorre (#5241): sotto una riga in
  // fondo finivano oltre il bordo dei 360 px, e Herdr non ha uno scorrimento comandato per un elenco
  // semplice. Qui si vedono sempre, col titolo della sessione a cui valgono.
  pannello(t) {
    const s = this.menu ? (this.dati?.sessioni ?? []).find((x) => x.sessionId === this.menu) : null;
    const az = s ? azioni(s) : [];
    if (!az.length) return null;
    const avviso = this.avvisi[s.sessionId];
    return v_flex().id("volta-gesti").mx(8).mt(2).px(10).py(8).gap(6).rounded(8).border_1().border_color(t.border)
      .child(h_flex().gap(6).items_start()
        .child(div().flex_1().min_w(0).truncate().text_size(12.5).font_semibold().text_color(t.foreground).child(titolo(s)))
        .child(div().id("volta-gesti-chiudi").px(6).rounded(6).cursor_pointer().text_size(12).text_color(t.dim)
          .hover((st) => st.bg(t.selected))
          .on_click((_e, cx) => { this.menu = null; cx.notify(); })
          .child("Chiudi")))
      .child(this.gesti(t, s, az))
      .when(Boolean(avviso), (el) => el.child(div().whitespace_normal().text_size(12.5).text_color(t.foreground).child(avviso)));
  }

  riga(t, s, modo, cx) {
    const sposto = this.sposto[s.sessionId];
    const apro = this.apro[s.sessionId];
    const d = sposto ? { testo: "La sposto nella finestra…", colore: "working" }
      : apro ? { testo: "La apro…", colore: "working" } : dettaglio(s, modo);
    const avviso = this.avvisi[s.sessionId];
    const vivo = s.stato === "aspetta" || s.stato === "lavora" || s.stato === "errore";
    const az = azioni(s);
    const aperto = this.menu === s.sessionId && az.length > 0;
    // La X chiude per sempre una sessione ferma (claude rm, lo stesso Elimina di "Altro"): compare col
    // puntatore sopra la riga, e il primo clic chiede la conferma. Nascosta tiene il suo posto: il
    // titolo non va a capo in modo diverso quando appare.
    const rm = az.find((a) => a.verbo === "rm");
    const k = s.sessionId;
    const chiedoRm = this.chiedo[k] === "rm", facciorm = this.faccio[k] === "rm";
    const vediX = Boolean(rm) && (this.sopra === k || chiedoRm || facciorm);
    const x = rm ? div().id(`vx-${s.host}-${s.id}`).mt(2).px(5).py(2).rounded(6).flex_none()
      .when(!vediX, (el) => el.invisible())
      .when(vediX, (el) => el.cursor_pointer().hover((st) => st.bg(t.selected)).on_click((_e, cx) => this.fare(s, rm, cx)))
      .child(facciorm ? div().text_size(12).text_color(t.dim).child("…")
        : chiedoRm ? div().text_size(12).text_color(t.blocked).child(rm.conferma)
        : svg(ICONA("x")).size(12).text_color(t.dim)) : null;
    // Il clic sulla riga apre la sessione; "Altro" sta a fianco, fuori dall'area che apre.
    return v_flex().id(`vr-${s.host}-${s.id}`).mx(8).px(10).py(7).gap(2).rounded(8).when(aperto, (el) => el.bg(t.hover))
      .on_hover((h, cx) => {
        if (h) this.sopra = k;
        else if (this.sopra === k) {
          this.sopra = null;
          // Una conferma chiesta dalla X e lasciata lì non resta armata; quella del pannello sì.
          if (this.chiedo[k] === "rm" && this.menu !== k) delete this.chiedo[k];
        }
        cx.notify();
      })
      .child(h_flex().gap(6).items_start()
        .child(h_flex().id(`v-${s.host}-${s.id}`).flex_1().min_w(0).gap(11).items_start().cursor_pointer()
          .on_click((_e, cx) => this.premi(s, cx))
          .child(div().pt(6).child(vivo || sposto || apro ? punto(colore(t, d.colore)) : div().size(8).flex_none()))
          .child(v_flex().flex_1().min_w(0).gap(2)
            // Un titolo scritto (al più 60 caratteri) va a capo su due righe; gli altri si tagliano.
            .child((s.titolo ? div().whitespace_normal() : div().truncate()).text_size(14).text_color(s.vecchia ? t.muted : t.foreground).child(titolo(s)))
            .child(div().truncate().text_size(12.5).text_color(colore(t, d.colore)).child(d.testo))))
        .when(az.length > 0, (el) => el.child(div().id(`va-${s.host}-${s.id}`).mt(2).px(6).py(1).rounded(6).cursor_pointer()
          .text_size(12).text_color(aperto ? t.foreground : t.dim).hover((st) => st.bg(t.selected))
          .on_click((_e, cx) => { this.menu = aperto ? null : s.sessionId; cx.notify(); })
          .child("Altro")))
        .when(Boolean(x), (el) => el.child(x)))
      .when(Boolean(avviso) && !aperto, (el) => el.child(div().pl(19).whitespace_normal().text_size(12.5).text_color(t.foreground).child(avviso)));
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

  // null quando la sezione non serve (manca lo script dell'elenco).
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
    // Un elenco suo, alto al massimo 360 px: i progetti sotto restano a vista. overflow_y_scroll e non
    // overflow_y_scrollbar, che avvolge l'elenco in un contenitore a cui max_h non arriva: lì non scorreva.
    else corpo = v_flex().id("volta-elenco").max_h(360).min_h(0).flex_shrink(1).overflow_y_scroll().gap(10).children(lista.map((g) => this.gruppo(t, g, modo, cx)));
    const vecchio = this.dati && this.errore && this.dati.letto ? `Non riesco ad aggiornare: lettura delle ${String(this.dati.letto).slice(11, 16)}.` : null;
    const gesti = chiusa || !corpo ? null : this.pannello(t);
    return v_flex().id("volta").pb(12).mb(12).gap(4).border_b(1).border_color(t.border)
      .child(testa)
      .when(!chiusa, (el) => el.child(this.interruttore(t)))
      .when(Boolean(vecchio) && !chiusa, (el) => el.child(div().px(18).text_size(12).text_color(t.blocked).child(vecchio)))
      .when(Boolean(corpo), (el) => el.child(corpo))
      .when(Boolean(gesti), (el) => el.child(gesti));
  }
}
