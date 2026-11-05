// Le parti del mod arturo: interruttore, riga di stato condivisa, radice del codice (mod passo 3, 3/11/2026).
import { describe, expect, test } from 'claude-code/testing'

import { leggiSpente, PARTI, radiceCodice, soloQueste, unisciVoci } from '../hooks/parti'

describe('interruttore delle parti', () => {
  test('senza file sono tutte accese, il file spegne solo nomi veri', () => {
    expect([...leggiSpente(null)]).toEqual([])
    expect([...leggiSpente('{"spente": ["dafare", "cache-fredda", "inventata", 3]}')].sort()).toEqual(['cache-fredda', 'dafare'])
    expect([...leggiSpente('non è json')]).toEqual([])
    expect([...leggiSpente('{"spente": "dafare"}')]).toEqual([])
  })

  test('ARTURO_PARTI accende solo le parti che nomina', () => {
    expect(soloQueste(undefined)).toBeNull()
    expect(soloQueste('  ')).toBeNull()
    expect([...(soloQueste('testata, rotazione') ?? [])].sort()).toEqual(['apri', 'cache-fredda', 'dafare', 'redazione-segreti'])
    expect(PARTI.length).toBe(6)
  })
})

test('la riga di stato mette in fila le voci nell\'ordine delle parti', () => {
  expect(unisciVoci(new Map())).toBeUndefined()
  const voci = new Map([
    ['rotazione', 'rotazione pronta'],
    ['cache-fredda', 'cache fredda'],
  ] as const)
  expect(unisciVoci(voci)).toBe('cache fredda \u00b7 rotazione pronta')
})

test('la radice del codice: nel clone due cartelle sopra, nel pacchetto la radice stessa', () => {
  expect(radiceCodice('/casa/.claude/skills/arturo')).toBe('/casa/.claude/skills/arturo/../..')
  expect(radiceCodice('/casa/.claude/skills/arturo/')).toBe('/casa/.claude/skills/arturo/../..')
  expect(radiceCodice('C:\\Users\\x\\.claude\\skills\\arturo')).toBe('C:\\Users\\x\\.claude\\skills\\arturo/../..')
  expect(radiceCodice('/cache/plugins/arturo/1.0.0')).toBe('/cache/plugins/arturo/1.0.0')
})

test('una parte spenta non scatta: con ARTURO_PARTI=apri all\'avvio si registra solo /apri', async ($, on) => {
  const comandi: string[] = []
  on('env.get', { name: 'ARTURO_PARTI' }, () => ({ value: 'apri' }))
  on('command.register', async (_$, e) => {
    comandi.push(e.name)
    return { value: { command: e.name } } as never
  })
  on('session.start', async (_$, e) => ({ cwd: e.cwd }))
  await $.session.start({ cwd: '/progetto', surface: 'terminal', isInteractive: true })
  expect(comandi).toEqual(['apri'])
})
