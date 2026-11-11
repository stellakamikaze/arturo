// Arturo per Herdr: un mod, più parti. Il layout dice quale con props.parte:
// marchio, barra (i progetti), piede, testata, todo (il pannello Da fare), stato, benvenuto.
// "Apri un progetto" (apri), la guida (guida), "Cosa posso chiedere" (chiedi), "La settimana"
// (settimana), "Aggiungi un todo" (nuovo), il velo delle note (nota, ⌘⇧N) e l'elenco delle note (note, ⌘⇧E) si
// aprono come dialoghi, e così il nome o il progetto di una sessione di Volta (cambio); il menu di un todo
// (azioni) e quello di una sessione di Volta (sessione) come popup.

import { View } from "gpui-kit";
import { props, shared, setShared } from "herdr";
import { Marchio, Barra, Piede } from "./barra.js";
import { Testata, Stato, Benvenuto } from "./testata.js";
import { Todo } from "./todo.js";
import { Apri } from "./apri.js";
import { Guida } from "./guida.js";
import { Chiedi } from "./suggerimenti.js";
import { Settimana } from "./revisione.js";
import { Azioni, Nuovo } from "./menu.js";
import { MenuSessione } from "./menusessione.js";
import { Cambio } from "./cambio.js";
import { Nota } from "./notaui.js";
import { Note } from "./noteui.js";

// Le parti del layout riportano la propria misura in px logici (shared arturo.misura.<parte>): al clic di
// una nota, nota.js ne ricava su quale parte della finestra cade il punto.
const MISURATE = new Set(["marchio", "barra", "piede", "testata", "todo", "stato", "benvenuto"]);

const PARTI = { marchio: Marchio, barra: Barra, piede: Piede, testata: Testata, stato: Stato, benvenuto: Benvenuto, todo: Todo, apri: Apri, guida: Guida, chiedi: Chiedi, settimana: Settimana, azioni: Azioni, sessione: MenuSessione, cambio: Cambio, nuovo: Nuovo, nota: Nota, note: Note };

export default class Arturo extends View {
  init(p, cx) {
    const Parte = PARTI[props()?.parte] ?? (props()?.overlay ? Apri : Barra);
    this.nome = props()?.parte;
    this.parte = new Parte();
    this.parte.init?.(p, cx);
  }
  render(cx) {
    const el = this.parte.render(cx);
    if (!MISURATE.has(this.nome) || !el?.on_size_change) return el;
    return el.id(`misura-${this.nome}`).on_size_change((m) => {
      const k = `arturo.misura.${this.nome}`;
      const v = { larghezza: Math.round(m.width), altezza: Math.round(m.height) };
      const prima = shared(k);
      if (prima?.larghezza !== v.larghezza || prima?.altezza !== v.altezza) setShared(k, v);
    });
  }
  async close(cx) {
    await this.parte.close?.(cx);
  }
}
