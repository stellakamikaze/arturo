// Arturo per Herdr: un mod, più parti. Il layout dice quale con props.parte:
// marchio, barra (i progetti), piede, testata, todo (il pannello Da fare), stato, benvenuto, casa (le
// tessere di ⌘T, nello stack "lavoro" accanto al terminale), coda (la Coda delle decisioni di ⌘⇧J, terzo
// figlio dello stesso stack).
// "Apri un progetto" (apri), la guida (guida), "Cosa posso chiedere" (chiedi), "La settimana"
// (settimana), "Aggiungi un todo" (nuovo), il velo delle note (nota, ⌘⇧N), l'elenco delle note (note, ⌘⇧E) e la
// checklist della ripartenza (checklist, ⌘⇧S) e il compito nuovo (compito, ⌘N) si aprono come dialoghi, e così il nome o il progetto di una
// sessione di Volta (cambio). La stessa checklist sta anche sopra la sessione, da sola (ripartenza, blocco
// sovrapposto del layout). Il menu di un todo
// (azioni), quello di una sessione di Volta (sessione), il selettore di "Nasce su" (macchina) e il menu di
// "Impostazioni" col movimento (impostazioni) come popup, e così "Sposta su" (sposta) e "Sposta tutto su" (spostatutto).
// "Unisci a…" (unisci, #6187) è un dialogo: sceglie il progetto in cui entra un doppione, mostra l'anteprima di Arturo
// e ha il pulsante Unisci. "Cerca doppioni" (doppioni, #6188) è un dialogo: le coppie di progetti che sembrano lo
// stesso, col motivo e col progetto che resta; da lì si apre l'anteprima di "Unisci a…".

import { View } from "gpui-kit";
import { props, shared, setShared } from "herdr";
import { Marchio, Barra, Piede } from "./barra.js";
import { Testata, Schede, Stato, Benvenuto } from "./testata.js";
import { Todo } from "./todo.js";
import { Apri } from "./apri.js";
import { Guida } from "./guida.js";
import { Chiedi } from "./suggerimenti.js";
import { Settimana } from "./revisione.js";
import { Azioni, Nuovo } from "./menu.js";
import { MenuSessione, MenuProgetto } from "./menusessione.js";
import { SceltaMacchina, Impostazioni } from "./comuni.js";
import { Cambio } from "./cambio.js";
import { Nota } from "./notaui.js";
import { Note } from "./noteui.js";
import { Casa } from "./casa.js";
import { Coda } from "./coda.js";
import { Checklist } from "./checklist.js";
import { SceltaSposta, SceltaSpostaTutto } from "./sposta.js";
import { Contesto } from "./contestoui.js";
import { Compito } from "./compito.js";
import { Unisci } from "./unisci.js";
import { Doppioni } from "./doppioniui.js";
import { impostaDormi, config } from "./dati.js";
import { impostaChi } from "./sessioni.js";

// Le parti del layout riportano la propria misura in px logici (shared arturo.misura.<parte>): al clic di
// una nota, nota.js ne ricava su quale parte della finestra cade il punto.
const MISURATE = new Set(["marchio", "barra", "piede", "testata", "schede", "todo", "stato", "benvenuto", "casa"]);

const PARTI = { impostazioni: Impostazioni, marchio: Marchio, barra: Barra, piede: Piede, testata: Testata, stato: Stato, benvenuto: Benvenuto, todo: Todo, apri: Apri, guida: Guida, chiedi: Chiedi, settimana: Settimana, azioni: Azioni, sessione: MenuSessione, macchina: SceltaMacchina, cambio: Cambio, nuovo: Nuovo, nota: Nota, note: Note, casa: Casa, coda: Coda, checklist: Checklist, ripartenza: Checklist, sposta: SceltaSposta, spostatutto: SceltaSpostaTutto, contesto: Contesto, menuprogetto: MenuProgetto, schede: Schede, compito: Compito, doppioni: Doppioni, unisci: Unisci };

export default class Arturo extends View {
  init(p, cx) {
    // le attese di dati.js (pausa) con cx.sleep invece di un processo Python (#5579)
    impostaDormi((/** @type {number} */ ms) => cx.sleep(ms));
    // Chi usa la finestra e cosa sa fare l'Arturo installato (#6217): ogni copia del mod li legge da
    // config(). Le capacità vanno in shared arturo.capacita, per le parti che disegnano senza aspettare.
    config().then((c) => {
      impostaChi(c.chi);
      if (JSON.stringify(shared("arturo.capacita") ?? null) !== JSON.stringify(c.capacita)) setShared("arturo.capacita", c.capacita);
    }).catch(() => { /* restano il nome di serie e tutti i gesti */ });
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
