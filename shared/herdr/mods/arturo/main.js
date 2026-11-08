// Arturo per Herdr: un mod, più parti. Il layout dice quale con props.parte:
// marchio, barra (i progetti), piede, testata, todo (il pannello Da fare), stato, benvenuto.
// "Apri un progetto" (apri), la guida (guida), "Cosa posso chiedere" (chiedi), "La settimana"
// (settimana) e "Aggiungi un todo" (nuovo) si aprono come dialoghi; il menu di un todo (azioni) come popup.

import { View } from "gpui-kit";
import { props } from "herdr";
import { Marchio, Barra, Piede } from "./barra.js";
import { Testata, Stato, Benvenuto } from "./testata.js";
import { Todo } from "./todo.js";
import { Apri } from "./apri.js";
import { Guida } from "./guida.js";
import { Chiedi } from "./suggerimenti.js";
import { Settimana } from "./revisione.js";
import { Azioni, Nuovo } from "./menu.js";

const PARTI = { marchio: Marchio, barra: Barra, piede: Piede, testata: Testata, stato: Stato, benvenuto: Benvenuto, todo: Todo, apri: Apri, guida: Guida, chiedi: Chiedi, settimana: Settimana, azioni: Azioni, nuovo: Nuovo };

export default class Arturo extends View {
  init(p, cx) {
    const Parte = PARTI[props()?.parte] ?? (props()?.overlay ? Apri : Barra);
    this.parte = new Parte();
    this.parte.init?.(p, cx);
  }
  render(cx) {
    return this.parte.render(cx);
  }
  async close(cx) {
    await this.parte.close?.(cx);
  }
}
