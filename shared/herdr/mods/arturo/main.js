// Arturo per Herdr: un mod, più parti. Il layout dice quale con props.parte:
// marchio, barra (i progetti), piede, testata, todo (il pannello Da fare), stato, benvenuto.
// La finestra "Apri un progetto" è la parte apri, aperta come dialogo.

import { View } from "gpui-kit";
import { props } from "herdr";
import { Marchio, Barra, Piede } from "./barra.js";
import { Testata, Stato, Benvenuto } from "./testata.js";
import { Todo } from "./todo.js";
import { Apri } from "./apri.js";

const PARTI = { marchio: Marchio, barra: Barra, piede: Piede, testata: Testata, stato: Stato, benvenuto: Benvenuto, todo: Todo, apri: Apri };

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
