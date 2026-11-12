// "Sposta su un'altra macchina" (Federico, 12/11/2026: la RAM di una macchina finisce, la sessione
// continua su un'altra). Tre ingressi: il pulsante della testata, per la sessione della scheda in primo
// piano (shared arturo.volta.davanti di volta.js); "Sposta su…" nel menu del tasto destro di una sessione;
// "Sposta tutto su…" sotto "Nasce su" nella barra, per tutte le sessioni in background delle altre
// macchine. I popup sono altre copie del mod: elencano le macchine, chiedono conferma col secondo clic e
// mandano alla barra "arturo.volta-sposta-<macchina>-<id>" o "arturo.volta-spostatutto-<macchina>"
// (spostaId e spostaTutto di volta.js). Lo spostamento non interrompe un turno: una sessione che lavora
// aspetta in coda la fine del turno (Federico: "dando continuità al task in corso e senza interromperlo").
// Lo spostamento vero sta in volta_sposta.py.

import { div, svg } from "gpui-kit";
import { h_flex, v_flex } from "gpui-base";
import { theme, props, closeOverlay, openOverlay, run } from "herdr";
import { vociMacchina } from "./comuni.js";
import { titolo, nonSiSposta, aFineTurno, spostabili, perSposta, contoTutto } from "./sessioni.js";

// Le regole di Sposta stanno in sessioni.js (pure, provate con node): qui per chi le prende da sposta.js.
export { nonSiSposta, aFineTurno, spostabili, perSposta, contoTutto };

export const ICONA_SPOSTA = "mods/arturo/sposta.svg";

// Il comando che sposta la sessione `id` su `macchina` ("qui" per questa).
export const comandoSposta = (macchina, id) => `arturo.volta-sposta-${macchina}-${id}`;

// "Sposta tutto su <macchina>": ogni sessione spostabile delle altre macchine (spostabili di sessioni.js).
// "spostatutto" senza trattino: "volta-sposta-tutto-x" si leggerebbe come la sessione "x" su "tutto".
export const comandoSpostaTutto = (macchina) => `arturo.volta-spostatutto-${macchina}`;

// Le macchine dove la sessione `s` può andare: tutte quelle di Volta, tranne la sua.
export const destinazioni = (s, voci) => (voci ?? []).filter((m) => m.host !== (s?.host ?? "qui"));

export function apriSposta(s) {
  openOverlay({ mod: "arturo", props: { parte: "sposta", sessione: s }, kind: "popup", width: 260 });
}

// "Sposta tutto su…": `sessioni` è l'elenco visibile della barra, già ridotto con perSposta.
export function apriSpostaTutto(sessioni) {
  openOverlay({ mod: "arturo", props: { parte: "spostatutto", sessioni }, kind: "popup", width: 280 });
}

// La pastiglia "Sposta tutto su…" sotto "Nasce su" nella barra, con lo stesso disegno. Niente se Volta non
// conosce altre macchine o se nessuna sessione si può spostare. `coda`: quante aspettano di partire o
// stanno partendo (codaSposta di volta.js); allora dice quante e non riapre il popup.
export function pastigliaTutto(t, sessioni, coda = 0) {
  const voci = vociMacchina();
  if (voci.length < 2) return null;
  if (!coda && !voci.some((m) => spostabili(sessioni, m.host).length > 0)) return null;
  return h_flex().child(h_flex().id("sposta-tutto").h(26).px(8).gap(6).items_center().rounded(6).text_size(12.5)
    .border_1().border_color(t.border)
    .when(!coda, (el) => el.cursor_pointer().hover((s) => s.bg(t.hover))
      .on_click(() => apriSpostaTutto((sessioni ?? []).map(perSposta))))
    .on_mouse_down("left", (_e, cx) => cx.stop_propagation())
    .child(svg(ICONA_SPOSTA).size(12).text_color(coda ? t.working : t.muted))
    .child(div().id("sposta-tutto-etichetta").text_color(coda ? t.working : t.dim)
      .child(coda ? `Sposto ${coda === 1 ? "1 sessione" : `${coda} sessioni`}…` : "Sposta tutto su…")));
}

export class SceltaSposta {
  init(_p, cx) {
    this.s = props()?.sessione ?? null;
    this.scelta = null;
    this.handle = cx.focus_handle();
    cx.timer.after(120, () => this.handle.focus());
  }

  chiudi() { closeOverlay(props().overlay); }

  // Il primo clic sceglie, il secondo sposta. Prima il comando, poi la chiusura: un overlay chiuso
  // ferma il suo codice.
  scegli(m, cx) {
    if (this.scelta !== m.host) { this.scelta = m.host; return cx.notify(); }
    run(comandoSposta(m.host, this.s.id));
    this.chiudi();
  }

  render() {
    const t = theme();
    const no = nonSiSposta(this.s);
    const voci = destinazioni(this.s, vociMacchina());
    const voce = (m) => {
      const scelta = this.scelta === m.host;
      return h_flex().id(`sposta-${m.host}`).h(30).px(10).gap(8).items_center().rounded(6)
        .when(!no, (el) => el.cursor_pointer().hover((st) => st.bg(t.hover)).on_click((_e, cx) => this.scegli(m, cx)))
        .when(scelta, (el) => el.bg(t.selected))
        .on_mouse_down("left", (_e, cx) => cx.stop_propagation())
        .child(div().flex_1().truncate().text_size(13).text_color(no || m.giu ? t.dim : t.foreground).child(m.macchina))
        .when(scelta, (el) => el.child(div().flex_none().text_size(12).text_color(t.accent).child("Clic per spostare")))
        .when(!scelta && Boolean(m.giu), (el) => el.child(div().flex_none().text_size(11.5).text_color(t.dim).child("non risponde")));
    };
    return v_flex().id("scelta-sposta").track_focus(this.handle).w_full().p(8).gap(4).bg(t.popover)
      .on_key_down((e, cx) => { if (e.key === "escape") { this.chiudi(); cx.stop_propagation(); } })
      .child(h_flex().px(10).pt(4).gap(6).items_center()
        .child(svg(ICONA_SPOSTA).size(13).text_color(t.muted))
        .child(div().text_size(12.5).text_color(t.muted).child("Sposta su")))
      .child(div().px(10).pb(2).truncate().text_size(12.5).text_color(t.foreground).child(this.s ? titolo(this.s) : ""))
      .when(Boolean(no), (el) => el.child(div().px(10).pb(2).whitespace_normal().text_size(12).text_color(t.blocked).child(no)))
      .when(!no && aFineTurno(this.s), (el) => el.child(div().px(10).pb(2).whitespace_normal().text_size(12).text_color(t.dim).child("Sta lavorando: la sposto a turno finito.")))
      .when(!voci.length, (el) => el.child(div().px(10).pb(2).text_size(12).text_color(t.dim).child("Volta non conosce altre macchine.")))
      .child(v_flex().gap(1).children(voci.map(voce)));
  }
}

// "Sposta tutto su…": una voce per macchina col conto di quello che ci andrebbe. Il primo clic sceglie e
// dice il conto, il secondo sposta. Una macchina senza niente da portare resta in grigio.
export class SceltaSpostaTutto {
  init(_p, cx) {
    this.sessioni = props()?.sessioni ?? [];
    this.scelta = null;
    this.handle = cx.focus_handle();
    cx.timer.after(120, () => this.handle.focus());
  }

  chiudi() { closeOverlay(props().overlay); }

  scegli(m, cx) {
    if (this.scelta !== m.host) { this.scelta = m.host; return cx.notify(); }
    run(comandoSpostaTutto(m.host));
    this.chiudi();
  }

  render() {
    const t = theme();
    const voce = (m) => {
      const c = contoTutto(this.sessioni, m.host);
      const scelta = this.scelta === m.host;
      const vuota = c.n === 0 || Boolean(m.giu);
      return h_flex().id(`sposta-tutto-${m.host}`).h(30).px(10).gap(8).items_center().rounded(6)
        .when(!vuota, (el) => el.cursor_pointer().hover((st) => st.bg(t.hover)).on_click((_e, cx) => this.scegli(m, cx)))
        .when(scelta, (el) => el.bg(t.selected))
        .on_mouse_down("left", (_e, cx) => cx.stop_propagation())
        .child(div().flex_1().truncate().text_size(13).text_color(vuota ? t.dim : t.foreground).child(m.macchina))
        .child(div().flex_none().text_size(12).text_color(scelta ? t.accent : t.dim)
          .child(scelta ? "Clic per spostare" : m.giu ? "non risponde" : c.testo));
    };
    const scelta = this.scelta ? contoTutto(this.sessioni, this.scelta) : null;
    return v_flex().id("scelta-sposta-tutto").track_focus(this.handle).w_full().p(8).gap(4).bg(t.popover)
      .on_key_down((e, cx) => { if (e.key === "escape") { this.chiudi(); cx.stop_propagation(); } })
      .child(h_flex().px(10).pt(4).gap(6).items_center()
        .child(svg(ICONA_SPOSTA).size(13).text_color(t.muted))
        .child(div().text_size(12.5).text_color(t.muted).child("Sposta tutto su")))
      .child(div().px(10).pb(2).whitespace_normal().text_size(12).text_color(t.dim)
        .child(scelta ? `Sposto ${scelta.testo}. Chi lavora finisce il turno, poi parte.` : "Le sessioni in background delle altre macchine, una alla volta."))
      .child(v_flex().gap(1).children(vociMacchina().map(voce)));
  }
}
