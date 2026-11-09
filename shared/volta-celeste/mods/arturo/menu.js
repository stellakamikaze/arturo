// Le azioni sui todo senza passare da Claude: il menu di una riga del pannello Da fare (chi lo fa,
// quando, fermo, nota, scarta) e la finestra "Aggiungi un todo". Gli argomenti vengono da azioni.js.

import { div, svg } from "gpui-kit";
import { v_flex, h_flex, InputState, Input } from "gpui-base";
import { theme, props, closeOverlay, openOverlay, notify, setShared } from "herdr";
import { todo, titoloTodo } from "./dati.js";
import { ICONA } from "./comuni.js";
import { azioni, aggiungi, CHI, QUANDO } from "./azioni.js";

// Scrive con `arturo todo`, avvisa com'è andata e fa rileggere barra e pannello.
export async function scrivi(argv, esito, titolo) {
  const r = await todo(argv);
  if (r.ok) notify({ title: esito, body: titolo ? titoloTodo(titolo) : undefined, level: "success", timeout: 4000 });
  else notify({ title: r.codice === 2 ? "Non l'ho scritto" : "Non riesco a scrivere sui todo", body: r.codice === 2 && /cambiat|aspettavi/i.test(r.errore) ? "Questo todo è cambiato nel frattempo: ho riletto l'elenco, riprova." : r.errore, level: "warning" });
  setShared("arturo.scritto", Date.now());
  return r.ok;
}

export function apriMenu(item) {
  openOverlay({ mod: "arturo", props: { parte: "azioni", todo: item }, kind: "popup", width: 300 });
}

export function apriNuovo(progetto, titolo) {
  openOverlay({ mod: "arturo", props: { parte: "nuovo", progetto, titolo }, kind: "dialog", width: 520 });
}

const fermaClic = (el) => el.on_mouse_down("left", (_e, cx) => cx.stop_propagation());

// Il menu di una riga. Un gesto con una domanda (fermo, nota, scarta) apre il suo campo nel menu.
export class Azioni {
  init(_p, cx) {
    this.item = props()?.todo ?? {};
    this.voci = azioni(this.item);
    this.scelta = null;
    this.inCorso = false;
    this.input = InputState.new({ placeholder: "" });
    this.input.on("submit", (_e, cx) => this.conferma(cx));
    this.handle = cx.focus_handle();
    cx.timer.after(120, () => this.handle.focus());
  }

  chiudi() { closeOverlay(props().overlay); }

  scegli(v, cx) {
    if (!v.chiede) return this.esegui(v, "", cx);
    this.scelta = v;
    this.input.set_value("");
    cx.notify();
    cx.timer.after(60, () => this.input.focus());
  }

  conferma(cx) {
    const v = this.scelta;
    if (!v) return;
    const testo = this.input.value().replace(/\s+/g, " ").trim();
    if (v.chiede.obbligo && !testo) return;
    this.esegui(v, testo, cx);
  }

  esegui(v, testo, cx) {
    if (this.inCorso) return;
    this.inCorso = true;
    cx.notify();
    const titolo = this.item.titolo;
    this.chiudi();
    scrivi(v.argv(testo), v.esito, titolo);
  }

  render() {
    const t = theme();
    const gruppi = [];
    for (const v of this.voci) {
      const g = gruppi.find((x) => x.nome === v.gruppo) ?? (gruppi.push({ nome: v.gruppo, voci: [] }), gruppi.at(-1));
      g.voci.push(v);
    }
    const nome = (lista, v) => lista.find(([k]) => k === v)?.[1]?.toLowerCase();
    const ora = { "Chi lo fa": nome(CHI, this.item.chi), "Quando": nome(QUANDO, this.item.quando) };
    const voce = (v) => fermaClic(h_flex().id(`m-${v.id}`).h(30).px(10).items_center().rounded(6).cursor_pointer()
      .when(this.scelta?.id === v.id, (el) => el.bg(t.selected))
      .hover((s) => s.bg(t.hover))
      .on_click((_e, cx) => this.scegli(v, cx))
      .child(div().flex_1().truncate().text_size(13).text_color(v.id === "scarta" ? t.blocked : t.foreground).child(v.etichetta)));
    const campo = this.scelta && v_flex().px(6).pt(6).gap(6)
      .child(div().text_size(12).text_color(t.muted).child(this.scelta.chiede.domanda))
      .child(h_flex().h(34).px(10).items_center().rounded(7).border_1().border_color(t.accent).bg(t.raised)
        .child(Input.new(this.input).flex_1().h_full().text_size(13).text_color(t.foreground)))
      .child(div().text_size(11.5).text_color(t.dim).child("Invio conferma · Esc chiude"));
    return v_flex().id("azioni").track_focus(this.handle).w_full().p(8).gap(6).bg(t.popover)
      .on_key_down((e, cx) => { if (e.key === "escape") { this.chiudi(); cx.stop_propagation(); } })
      .child(div().px(10).pt(4).pb(2).whitespace_normal().text_size(12.5).text_color(t.muted).child(titoloTodo(this.item.titolo)))
      .children(gruppi.map((g) => v_flex().gap(1)
        .child(div().px(10).pt(4).text_size(11).font_semibold().text_color(t.dim).child(ora[g.nome] ? `${g.nome} · ora ${ora[g.nome]}` : g.nome))
        .children(g.voci.map(voce))))
      .when(Boolean(campo), (el) => el.child(campo));
  }
}

// La finestra "Aggiungi un todo": il titolo, chi lo fa e quando. Invio aggiunge.
export class Nuovo {
  init(_p, cx) {
    const p = props() ?? {};
    this.progetto = p.progetto;
    this.titolo = p.titolo ?? this.progetto;
    this.chi = "tu";
    this.quando = "settimana";
    this.inCorso = false;
    this.input = InputState.new({ placeholder: "Cosa c'è da fare?" });
    this.input.on("change", (_e, cx) => cx.notify());
    this.input.on("submit", (_e, cx) => this.aggiungi(cx));
    this.input.focus();
    cx.timer.after(300, () => this.input.focus());
    this.handle = cx.focus_handle();
  }

  chiudi() { closeOverlay(props().overlay); }

  aggiungi(cx) {
    const a = aggiungi({ titolo: this.input.value(), progetto: this.progetto, chi: this.chi, quando: this.quando });
    if (!a || this.inCorso) return;
    this.inCorso = true;
    cx.notify();
    const testo = this.input.value();
    cx.spawn(async (cx) => {
      const ok = await scrivi(a.argv, a.esito, testo);
      this.inCorso = false;
      if (ok) this.chiudi();
      else cx.notify();
    });
  }

  scelte(t, nome, opzioni, attuale, metti) {
    return v_flex().gap(6)
      .child(div().text_size(12).text_color(t.muted).child(nome))
      .child(h_flex().gap(6).children(opzioni.map(([valore, etichetta]) => fermaClic(div().id(`n-${nome}-${valore}`)
        .px(11).py(6).rounded(7).cursor_pointer().text_size(13)
        .border_1().border_color(valore === attuale ? t.accent : t.border)
        .when(valore === attuale, (el) => el.bg(t.selected))
        .text_color(t.foreground).hover((s) => s.bg(t.hover))
        .on_click((_e, cx) => { metti(valore); cx.notify(); })
        .child(etichetta)))));
  }

  render() {
    const t = theme();
    const pronto = Boolean(aggiungi({ titolo: this.input.value(), progetto: this.progetto }));
    return v_flex().id("nuovo").track_focus(this.handle).w_full().p(22).gap(16).bg(t.popover)
      .on_key_down((e, cx) => { if (e.key === "escape") { this.chiudi(); cx.stop_propagation(); } })
      .child(v_flex().gap(3)
        .child(div().font_family("Arturo Archivo").text_size(18).text_color(t.foreground).child("Aggiungi un todo"))
        .child(div().text_size(12.5).text_color(t.muted).child(this.titolo)))
      .child(h_flex().h(40).px(12).gap(9).items_center().rounded(9).border_1().border_color(t.accent).bg(t.raised)
        .child(svg(ICONA("plus")).size(15).text_color(t.muted))
        .child(Input.new(this.input).flex_1().h_full().text_size(14).text_color(t.foreground)))
      .child(this.scelte(t, "Chi lo fa", CHI, this.chi, (v) => { this.chi = v; }))
      .child(this.scelte(t, "Quando", QUANDO, this.quando, (v) => { this.quando = v; }))
      .child(h_flex().gap(10).items_center()
        .child(fermaClic(div().id("nuovo-aggiungi").px(14).py(7).rounded(7).cursor_pointer().text_size(13).font_semibold()
          .bg(pronto ? t.accent : t.raised).text_color(pronto ? t.accent_foreground : t.dim)
          .when(pronto, (el) => el.hover((s) => s.opacity(0.9)))
          .on_click((_e, cx) => this.aggiungi(cx))
          .child(this.inCorso ? "Aggiungo…" : "Aggiungi")))
        .child(div().text_size(12).text_color(t.dim).child("Invio aggiunge · Esc chiude")));
  }
}
