import { describe, expect, test } from 'claude-code/testing'

import { SIGLA, testiDaScrivere } from '../hooks/register'

// Dal 4/10/2026: il mod nega una scrittura che contiene una sigla completa. Un file letto redatto
// e riscritto da Claude perderebbe il valore vero, sostituito dalla sigla.
const sigla = '[REDATTO:' + 'db-password len=16 sha256=' + 'ab12cd34]'

describe('blocco delle scritture con sigla', () => {
  test('Write con la sigla nel contenuto: trovata', () => {
    expect(testiDaScrivere({ content: `url = postgres://u:${sigla}@h/db` }).some(t => SIGLA.test(t))).toBe(true)
  })

  test('Edit e MultiEdit: la sigla nel testo nuovo è trovata', () => {
    expect(testiDaScrivere({ old_string: 'x', new_string: sigla }).some(t => SIGLA.test(t))).toBe(true)
    expect(testiDaScrivere({ edits: [{ new_string: 'ok' }, { new_string: sigla }] }).some(t => SIGLA.test(t))).toBe(true)
  })

  test('la sigla solo nel testo vecchio di un Edit non blocca: quel testo non arriva su disco', () => {
    expect(testiDaScrivere({ old_string: sigla, new_string: 'nuovo' }).some(t => SIGLA.test(t))).toBe(false)
  })

  test('il codice che costruisce la sigla non è una sigla', () => {
    const codice = 'return `[REDATTO:${tipo} len=${value.length} sha256=${await hash8(value)}]`'
    expect(SIGLA.test(codice)).toBe(false)
    expect(SIGLA.test('[REDATTO: errore del mod redazione-segreti, output nascosto]')).toBe(false)
  })
})
