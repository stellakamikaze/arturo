// La tabella dei tasti del pannello /dafare: per ogni verbo, gli argomenti di `arturo todo` e il
// passo inverso. L'inverso si calcola dai campi della riga PRIMA di scrivere, così «u» rimette le
// cose come erano. Gli inversi usano `ripristina` (stato e motivo esatti) e `--annullo`: chi legge
// la storia sa che non sono scelte della persona.
//
// Il file è JavaScript puro, senza `$`: lo carica il pannello e lo carica anche il banco
// tests/test_pannello.py (U04), che lancia ogni argomento sulla CLI vera.
//
// «scarta» resta fuori: nel pannello ci sono solo gesti annullabili, per scartare si chiede a Claude.

/** @typedef {{ id: number, stato: string, motivo: string | null, chi: string, quando: string }} Riga */
/** @typedef {{ tasto: string, etichetta: string, argv: (t: Riga) => string[], inverso: (t: Riga) => string[] }} Voce */

/** Il giro di «chi lo fa»: tu, poi decidi, poi io, poi di nuovo tu. */
export const GIRO_CHI = ['tu', 'decidi', 'io']

/** @param {string} chi @returns {string} */
export function prossimoChi(chi) {
  const i = GIRO_CHI.indexOf(chi)
  return GIRO_CHI[(i + 1) % GIRO_CHI.length] ?? 'tu'
}

/** Rimette stato e motivo della riga com'erano. @param {Riga} t @returns {string[]} */
function ripristina(t) {
  return t.motivo ? ['ripristina', String(t.id), t.stato, t.motivo] : ['ripristina', String(t.id), t.stato]
}

/** @type {Record<string, Voce>} */
export const VERBI = {
  fatto: { tasto: 'f', etichetta: 'fatto', argv: t => ['fatto', String(t.id)], inverso: ripristina },
  ferma: { tasto: 's', etichetta: 'ferma', argv: t => ['ferma', String(t.id)], inverso: ripristina },
  riprendi: { tasto: 'r', etichetta: 'riprendi', argv: t => ['riprendi', String(t.id)], inverso: ripristina },
  chi: {
    tasto: 'c',
    etichetta: 'chi lo fa',
    argv: t => ['modifica', String(t.id), '--chi', prossimoChi(t.chi)],
    inverso: t => ['modifica', String(t.id), '--chi', t.chi, '--annullo'],
  },
  avvicina: {
    tasto: 'a',
    etichetta: 'avvicina',
    argv: t => ['su', String(t.id)],
    inverso: t => ['modifica', String(t.id), '--quando', t.quando, '--annullo'],
  },
  allontana: {
    tasto: 'l',
    etichetta: 'allontana',
    argv: t => ['giu', String(t.id)],
    inverso: t => ['modifica', String(t.id), '--quando', t.quando, '--annullo'],
  },
}
