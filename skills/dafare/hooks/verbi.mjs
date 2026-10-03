// La tabella dei tasti del pannello /dafare: per ogni verbo, gli argomenti di `arturo todo` e il
// passo inverso. L'inverso si calcola dai campi della riga PRIMA di scrivere, così «u» rimette le
// cose come erano. Gli inversi usano `ripristina` (stato e motivo esatti) e `--annullo`: chi legge
// la storia sa che non sono scelte della persona.
//
// Il file è JavaScript puro, senza `$`: lo carica il pannello e lo carica anche il banco
// tests/test_pannello.py (U04), che lancia ogni argomento sulla CLI vera.
//
// «scarta» resta fuori: nel pannello ci sono solo gesti annullabili, per scartare si chiede a Claude.

/** @typedef {{ id: number, titolo: string, stato: string, motivo: string | null, chi: string, quando: string }} Riga */
/** @typedef {{ tasto: string, etichetta: string, argv: (t: Riga) => string[], inverso: (t: Riga) => string[] }} Voce */

/** Il giro di «chi lo fa»: tu, poi decidi, poi io, poi di nuovo tu. */
export const GIRO_CHI = ['tu', 'decidi', 'io']

/** @param {string} chi @returns {string} */
export function prossimoChi(chi) {
  const i = GIRO_CHI.indexOf(chi)
  return GIRO_CHI[(i + 1) % GIRO_CHI.length] ?? 'tu'
}

/** La scala di «quando», come `su` e `giu` della CLI. */
const SCALA = ['più avanti', 'settimana', 'oggi']

/** @param {string} quando @param {number} passo @returns {string} */
function spostato(quando, passo) {
  const i = Math.max(0, SCALA.indexOf(quando))
  return SCALA[Math.max(0, Math.min(SCALA.length - 1, i + passo))] ?? quando
}

/**
 * Il titolo che il pannello ha mostrato. La CLI lo confronta prima di scrivere: dopo un merge che ha
 * rinumerato i todo, il numero può indicare un altro todo, e allora la CLI si ferma. Un token solo
 * con «=», così un titolo che comincia con un trattino resta un valore.
 * @param {Riga} t @returns {string}
 */
function titolo(t) {
  return `--titolo-atteso=${t.titolo}`
}

/**
 * Rimette stato e motivo della riga com'erano, solo se il todo è ancora nello stato `dopo` che il
 * tasto ha lasciato: se Claude o un'altra vista lo hanno cambiato nel frattempo, «u» non lo tocca.
 * Il motivo va in un token solo, `--motivo=TESTO`: la CLI lo legge prima di argparse, così torna
 * identico anche se è «-firma» o «--», su ogni Python.
 * @param {string} dopo @returns {(t: Riga) => string[]}
 */
function ripristina(dopo) {
  return t => {
    const motivo = t.motivo ? [`--motivo=${t.motivo}`] : []
    return ['ripristina', String(t.id), titolo(t), `--atteso=stato=${dopo}`, '--atteso=motivo=', ...motivo, '--', t.stato]
  }
}

/** @type {Record<string, Voce>} */
export const VERBI = {
  fatto: { tasto: 'f', etichetta: 'fatto', argv: t => ['fatto', String(t.id), titolo(t)], inverso: ripristina('fatto') },
  ferma: { tasto: 's', etichetta: 'ferma', argv: t => ['ferma', String(t.id), titolo(t)], inverso: ripristina('fermo') },
  riprendi: { tasto: 'r', etichetta: 'riprendi', argv: t => ['riprendi', String(t.id), titolo(t)], inverso: ripristina('da fare') },
  chi: {
    tasto: 'c',
    etichetta: 'chi lo fa',
    argv: t => ['modifica', String(t.id), titolo(t), '--chi', prossimoChi(t.chi)],
    inverso: t => ['modifica', String(t.id), titolo(t), `--atteso=chi=${prossimoChi(t.chi)}`, '--chi', t.chi, '--annullo'],
  },
  avvicina: {
    tasto: 'a',
    etichetta: 'avvicina',
    argv: t => ['su', String(t.id), titolo(t)],
    inverso: t => ['modifica', String(t.id), titolo(t), `--atteso=quando=${spostato(t.quando, 1)}`, '--quando', t.quando, '--annullo'],
  },
  allontana: {
    tasto: 'l',
    etichetta: 'allontana',
    argv: t => ['giu', String(t.id), titolo(t)],
    inverso: t => ['modifica', String(t.id), titolo(t), `--atteso=quando=${spostato(t.quando, -1)}`, '--quando', t.quando, '--annullo'],
  },
}
