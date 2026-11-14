// La finestra "Cerca" (⌘K e ⌘O, #5369): le sessioni di Claude di tutte le macchine e i progetti della
// memoria di Arturo in un elenco solo (cerca() di sessioni.js). Scrivi per filtrare, frecce e Invio per
// aprire, Esc per chiudere. Invio su una sessione fa lo stesso clic dell'elenco di Volta, anche su una
// chiusa (si riaggancia); su un progetto lo apre; "Nuova richiesta" fa nascere una sessione col testo.

import { div, svg } from "gpui-kit";
import { v_flex, h_flex, InputState, Input } from "gpui-base";
import { theme, props, closeOverlay, run, shared } from "herdr";
import { nomiProgetti, slug, spazio, frase, bello, sessioniVolta } from "./dati.js";
import { comandoApri } from "./comandi.js";
import { ICONA, punto, colore, nasceSu } from "./comuni.js";
import { SPAZIO, TESTO, RAGGIO, PULSANTE, ICONA_MISURA } from "./misure.js";
import { cerca, comandoNuova, impostaProgetti, titolo, nomeProgetto, titoloNoto, fraseStato, chiusa, macchinaBreve, chiave as chiaveSessione } from "./sessioni.js";

export class Apri {
  init(_p, cx) {
    this.filtro = "";
    this.at = 0;
    this.lista = null;
    this.sessioni = [];
    this.input = InputState.new({ placeholder: "Cerca una sessione o un progetto, o scrivi una richiesta" });
    this.input.on("change", (_e, cx) => { this.filtro = this.input.value(); this.at = 0; cx.notify(); });
    this.input.on("submit", () => this.vai(this.righe()[this.at]));
    this.input.focus();
    cx.timer.after(300, () => this.input.focus());
    this.handle = cx.focus_handle();
    cx.spawn(async (cx) => {
      const [lista, sessioni] = await Promise.all([nomiProgetti(), sessioniVolta()]);
      this.lista = lista;
      this.sessioni = sessioni;
      cx.notify();
    });
  }

  chiudi() { closeOverlay(props().overlay); }

  righe() {
    impostaProgetti(shared("arturo.progetti"));
    return cerca(this.sessioni, this.lista ?? [], this.filtro);
  }

  // Sessione, progetto o richiesta li apre la barra: la finestra manda il comando e si chiude. Un overlay
  // chiuso ferma il suo codice al primo await, e una sessione fatta nascere da qui restava a metà se la
  // finestra si chiudeva prima della fine (11/11/2026).
  vai(r) {
    if (!r) return;
    if (r.tipo === "sessione") run(`arturo.volta-${chiaveSessione(r.s)}`);
    else if (r.tipo === "progetto") run(comandoApri(slug(r.nome)));
    else if (r.tipo === "nuova" && r.testo) run(comandoNuova(r.testo));
    else return;
    this.chiudi();
  }

  render() {
    const t = theme();
    const righe = this.righe();
    this.at = Math.max(0, Math.min(this.at, righe.length - 1));
    // 42: una riga porta due righe di testo (titolo e dove), più alta di un pulsante grande
    const base = (chiave, i, r) => h_flex().id(chiave).h(42).px(SPAZIO.l).gap(SPAZIO.l).items_center().rounded(RAGGIO.riga).cursor_pointer()
      .when(i === this.at, (el) => el.bg(t.selected)).hover((st) => st.bg(t.hover))
      .on_click(() => this.vai(r));
    const testo = (x) => div().truncate().text_size(TESTO.riga).text_color(t.foreground).child(x);
    const dopo = (x, c) => div().flex_none().max_w(200).truncate().text_size(TESTO.etichetta).text_color(c).child(x);
    const riga = (r, i) => {
      if (r.tipo === "sessione") {
        const s = r.s;
        const st = chiusa(s) ? { testo: "Chiusa: Invio la riapre", colore: "dim" } : fraseStato(s);
        const dove = [s.progetto ? nomeProgetto(s.progetto) : null, macchinaBreve(s.macchina)].filter(Boolean).join(" · ");
        return base(`c-s-${s.host}-${s.id}`, i, r)
          .child(punto(colore(t, st.colore)))
          .child(v_flex().flex_1().min_w(0)
            .child(testo(titolo(s)))
            .child(div().truncate().text_size(TESTO.nota).text_color(t.muted).child(dove)))
          .child(dopo(st.testo, colore(t, st.colore)));
      }
      if (r.tipo === "progetto") {
        const s = spazio(r.nome);
        const f = s?.status ? frase(s.status) : null;
        return base(`c-p-${r.nome}`, i, r)
          .child(svg(ICONA("folder")).size(ICONA_MISURA.piccola).flex_none().text_color(f ? colore(t, f.colore) : t.muted))
          .child(div().flex_1().min_w(0).child(testo(titoloNoto(r.nome) ?? bello(r.nome))))
          .child(dopo(f ? f.testo : s ? "Conversazione aperta" : "Progetto", f ? colore(t, f.colore) : t.dim));
      }
      return base("c-nuova", i, r)
        .child(svg(ICONA("square-pen")).size(ICONA_MISURA.piccola).flex_none().text_color(t.accent))
        .child(div().flex_1().min_w(0).child(testo(`Nuova richiesta: ${r.testo}`)))
        .child(dopo("Claude parte da qui", t.dim));
    };
    const vuoto = this.lista === null ? "Cerco sessioni e progetti…"
      : "Non ci sono ancora sessioni né progetti. Scrivi una richiesta: Invio la manda a Claude.";
    return v_flex().id("apri").track_focus(this.handle).w_full().p(SPAZIO.xxl).gap(SPAZIO.l).bg(t.popover)
      .on_key_down((e, cx) => {
        if (e.key === "escape") return this.chiudi();
        if (e.key === "down") this.at = (this.at + 1) % Math.max(1, righe.length);
        else if (e.key === "up") this.at = (this.at + righe.length - 1) % Math.max(1, righe.length);
        else return;
        cx.stop_propagation();
        cx.notify();
      })
      .child(div().font_family("Arturo Archivo").text_size(TESTO.titolo).text_color(t.foreground).child("Cerca"))
      .when(Boolean(nasceSu(t)), (el) => el.child(nasceSu(t)))
      .child(h_flex().h(PULSANTE.grande).px(SPAZIO.l).gap(SPAZIO.m).items_center().rounded(RAGGIO.riga).border_1().border_color(t.accent).bg(t.raised)
        .child(svg(ICONA("search")).size(ICONA_MISURA.grande).text_color(t.muted))
        .child(Input.new(this.input).flex_1().h_full().text_size(TESTO.riga).text_color(t.foreground)))
      .child(this.lista !== null && righe.length
        ? v_flex().gap(SPAZIO.xs).children(righe.map(riga))
        : div().px(SPAZIO.l).py(SPAZIO.m).text_size(TESTO.corpo).text_color(t.muted).whitespace_normal().child(vuoto))
      .child(div().px(SPAZIO.xs).text_size(TESTO.etichetta).text_color(t.dim).child("Invio apre · Esc chiude"));
  }
}
