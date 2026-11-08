import type { On } from 'claude-code'
import { describe, expect, mock, test } from 'claude-code/testing'

import { argomentiInizio, decidi, MIN_INTERVALLO_MS, nomeTool, spenta, vediBozza } from '../hooks/rotazione/rotazione'

// Il nome che il motore finto dà al tool: il mod usa quello, qualunque sia il nome del plugin.
const TOOL = 'mcp__prova__ruota'

const base = { armata: { progetto: 'arturo', compito: 'step 2' }, reason: 'answer', agentId: undefined, bozza: '', ora: 10_000_000, ultima: undefined }

describe('decidi', () => {
  test('armata, turno finito, casella vuota: clear', () => {
    expect(decidi(base)).toEqual({ azione: 'clear' })
  })
  test('niente armato: niente', () => {
    expect(decidi({ ...base, armata: undefined })).toEqual({ azione: 'niente' })
  })
  test('turno interrotto con Esc: disarma', () => {
    expect(decidi({ ...base, reason: 'aborted' }).azione).toBe('disarma')
  })
  test('errore API: disarma', () => {
    expect(decidi({ ...base, reason: 'error' }).azione).toBe('disarma')
  })
  test('testo nella casella: aspetta, non disarma', () => {
    expect(decidi({ ...base, bozza: 'aspetta' })).toEqual({ azione: 'attendi' })
  })
  test('turno di un subagent: aspetta, non disarma', () => {
    expect(decidi({ ...base, agentId: 'a1' })).toEqual({ azione: 'niente' })
  })
  test('seconda rotazione entro 3 minuti: disarma', () => {
    expect(decidi({ ...base, ultima: base.ora - MIN_INTERVALLO_MS + 1 }).azione).toBe('disarma')
  })
  test('rotazione dopo 3 minuti: clear', () => {
    expect(decidi({ ...base, ultima: base.ora - MIN_INTERVALLO_MS })).toEqual({ azione: 'clear' })
  })
})

describe('vediBozza', () => {
  const a = { bozza: '2', fermaDa: 0, iniziata: 0 }
  test('bozza ferma da meno di un minuto: aspetta', () => {
    expect(vediBozza(a, '2', 30_000).azione).toBe('aspetta')
  })
  test('bozza ferma da un minuto: clear e la bozza da rimettere', () => {
    expect(vediBozza(a, '2', 60_000)).toEqual({ azione: 'clear', bozza: '2' })
  })
  test('casella svuotata: clear senza bozza', () => {
    expect(vediBozza(a, '', 15_000)).toEqual({ azione: 'clear', bozza: '' })
  })
  test('bozza che cambia: aspetta e riparte il minuto', () => {
    expect(vediBozza(a, '2 e', 45_000)).toEqual({ azione: 'aspetta', attesa: { bozza: '2 e', fermaDa: 45_000, iniziata: 0 } })
  })
  test('bozza che cambia da 10 minuti: disarma', () => {
    expect(vediBozza(a, 'altro', 600_000).azione).toBe('disarma')
  })
})

test('argomenti di /inizio: slug, separatore, marca, compito su una riga', () => {
  expect(argomentiInizio({ progetto: 'arturo', compito: 'scrivere\n  i test' })).toBe('arturo -- --rotazione scrivere i test')
})

test('nome del tool dal plugin: rotazione in Arturo, una copia rinominata ha il suo', () => {
  expect(nomeTool('rotazione')).toBe('mcp__rotazione__ruota')
  expect(nomeTool('mia-rotazione')).toBe('mcp__mia-rotazione__ruota')
})

test('interruttore: 0, no, off spengono; vuoto o assente no', () => {
  expect(['0', 'no', 'OFF', 'spenta', 'false'].map(spenta)).toEqual([true, true, true, true, true])
  expect([undefined, '', '1', 'si'].map(spenta)).toEqual([false, false, false, false])
})

type Dati = {
  comandi: { command: string; args: string }[]
  store: Record<string, unknown>
  stato: (string | undefined)[]
  toast: string[]
  riempita?: string
}

function motore(on: On, opz: { bozza?: string | (() => string); env?: Record<string, string> } = {}): Dati {
  // Il mod arturo ha sei parti: qui si prova solo questa (ARTURO_PARTI, hooks/parti.ts).
  on('env.get', { name: 'ARTURO_PARTI' }, () => ({ value: 'rotazione' }))
  const d: Dati = { comandi: [], store: {}, stato: [], toast: [] }
  on('session.start', (_, e) => ({ cwd: e.cwd }))
  on('tool.register', (_, e) => ({ value: { tool: `mcp__prova__${e.name}` } }))
  on('tool.call', () => ({ result: 'motore' }))
  on('turn.complete', () => ({ text: '' }))
  on('session.end', (_, e) => ({ sessionId: e.sessionId }))
  on('prompt.read', () => ({ value: { text: typeof opz.bozza === 'function' ? opz.bozza() : opz.bozza ?? '', cursor: 0 } }))
  on('prompt.fill', (_, e) => {
    d.riempita = (e as { text: string }).text
    return { isFilled: true }
  })
  on('env.get', (_, e) => ({ value: (opz.env ?? {})[(e as { name: string }).name] }))
  on('store.get', (_, e) => ({ value: d.store[e.key] }))
  on('store.set', (_, e) => {
    d.store[e.key] = e.value
    return { value: undefined }
  })
  on('ui.status', (_, e) => {
    d.stato.push((e as { text?: string }).text)
    return { value: undefined }
  })
  on('ui.toast', (_, e) => {
    d.toast.push(String((e as { text?: unknown }).text))
    return { value: undefined }
  })
  on('command.run', (_, e) => {
    d.comandi.push({ command: e.command, args: e.args })
    return { text: '' }
  })
  return d
}

const fineTurno = (reason: 'answer' | 'aborted') =>
  ({ reason, answer: '', durationMs: 1, isAborted: reason === 'aborted', turnId: 't1' }) as never
const fine = { reason: 'clear', sessionId: 's1', resume: { id: 's1' } } as never

test('giro intero: ruota → fine turno → /clear → /inizio con la marca, riga per la persona', async ($, on) => {
  const d = motore(on)
  const clock = mock.clock(on)
  await $.session.start({ cwd: '/', surface: 'terminal', isInteractive: true })
  const r = await $.tool.call({ tool: TOOL, progetto: 'arturo', compito: 'scrivere i test' } as never)
  expect(JSON.stringify(r)).toContain('Rotazione armata')
  await $.turn.complete(fineTurno('answer'))
  await clock.advance(1_000)
  expect(d.comandi).toEqual([{ command: 'clear', args: '' }])
  await $.session.end(fine)
  await clock.advance(2_000)
  expect(d.comandi[1]).toEqual({ command: 'inizio', args: 'arturo -- --rotazione scrivere i test' })
  expect(d.stato.at(-1)).toBeUndefined()
  expect(d.toast.some(t => t.includes('Sessione rinnovata'))).toBe(true)
})

test('un altro tool passa al motore', async ($, on) => {
  motore(on)
  await $.session.start({ cwd: '/', surface: 'terminal', isInteractive: true })
  const r = await $.tool.call({ tool: 'Bash', command: 'ls' } as never)
  expect(JSON.stringify(r)).toContain('motore')
})

test('ARTURO_ROTAZIONE=0: il tool non arma, nessun /clear', async ($, on) => {
  const d = motore(on, { env: { ARTURO_ROTAZIONE: '0' } })
  const clock = mock.clock(on)
  await $.session.start({ cwd: '/', surface: 'terminal', isInteractive: true })
  const r = await $.tool.call({ tool: TOOL, progetto: 'arturo', compito: 'x' } as never)
  expect(JSON.stringify(r)).toContain('Rotazione spenta')
  await $.turn.complete(fineTurno('answer'))
  await clock.advance(20_000)
  expect(d.comandi).toEqual([])
})

test('/clear che non chiude la sessione: un solo secondo tentativo', async ($, on) => {
  const d = motore(on)
  const clock = mock.clock(on)
  await $.session.start({ cwd: '/', surface: 'terminal', isInteractive: true })
  await $.tool.call({ tool: TOOL, progetto: 'arturo', compito: 'x' } as never)
  await $.turn.complete(fineTurno('answer'))
  await clock.advance(20_000)
  expect(d.comandi).toEqual([{ command: 'clear', args: '' }, { command: 'clear', args: '' }])
})

test('Esc durante il turno: nessun /clear', async ($, on) => {
  const d = motore(on)
  const clock = mock.clock(on)
  await $.session.start({ cwd: '/', surface: 'terminal', isInteractive: true })
  await $.tool.call({ tool: TOOL, progetto: 'arturo', compito: 'x' } as never)
  await $.turn.complete(fineTurno('aborted'))
  await clock.advance(20_000)
  expect(d.comandi).toEqual([])
})

test('testo nella casella: nessun /clear nei primi 20 secondi', async ($, on) => {
  const d = motore(on, { bozza: 'aspetta un attimo' })
  const clock = mock.clock(on)
  await $.session.start({ cwd: '/', surface: 'terminal', isInteractive: true })
  await $.tool.call({ tool: TOOL, progetto: 'arturo', compito: 'x' } as never)
  await $.turn.complete(fineTurno('answer'))
  await clock.advance(20_000)
  expect(d.comandi).toEqual([])
})

test('VELENO 7/11: un "2" rimasto nella casella non annulla la rotazione, e torna nella casella', async ($, on) => {
  let casella = '2'
  const d = motore(on, { bozza: () => casella })
  const clock = mock.clock(on)
  await $.session.start({ cwd: '/', surface: 'terminal', isInteractive: true })
  await $.tool.call({ tool: TOOL, progetto: 'arturo', compito: 'step 5' } as never)
  await $.turn.complete(fineTurno('answer'))
  await clock.advance(45_000)
  expect(d.comandi).toEqual([])
  await clock.advance(16_000)
  expect(d.comandi).toEqual([{ command: 'clear', args: '' }])
  casella = ''
  await $.session.end(fine)
  await clock.advance(2_000)
  expect(d.comandi[1]).toEqual({ command: 'inizio', args: 'arturo -- --rotazione step 5' })
  expect(d.riempita).toBe('2')
})

test('casella svuotata durante l\'attesa: clear al controllo dopo', async ($, on) => {
  let casella = 'una frase'
  const d = motore(on, { bozza: () => casella })
  const clock = mock.clock(on)
  await $.session.start({ cwd: '/', surface: 'terminal', isInteractive: true })
  await $.tool.call({ tool: TOOL, progetto: 'arturo', compito: 'x' } as never)
  await $.turn.complete(fineTurno('answer'))
  casella = ''
  await clock.advance(17_000)
  expect(d.comandi[0]).toEqual({ command: 'clear', args: '' })
})

test('messaggio mandato durante l\'attesa: nessun /clear', async ($, on) => {
  const d = motore(on, { bozza: 'sto scrivendo' })
  on('prompt.submit', (_, e) => e as never)
  const clock = mock.clock(on)
  await $.session.start({ cwd: '/', surface: 'terminal', isInteractive: true })
  await $.tool.call({ tool: TOOL, progetto: 'arturo', compito: 'x' } as never)
  await $.turn.complete(fineTurno('answer'))
  await $.prompt.submit({ text: 'sto scrivendo' } as never)
  await clock.advance(120_000)
  expect(d.comandi).toEqual([])
})

test('sessione headless: il tool non arma', async ($, on) => {
  const d = motore(on)
  const clock = mock.clock(on)
  await $.session.start({ cwd: '/', surface: null, isInteractive: false })
  const r = await $.tool.call({ tool: TOOL, progetto: 'arturo', compito: 'x' } as never)
  expect(JSON.stringify(r)).toContain('non disponibile')
  await $.turn.complete(fineTurno('answer'))
  await clock.advance(20_000)
  expect(d.comandi).toEqual([])
})

test('slug non valido: rifiuto', async ($, on) => {
  motore(on)
  await $.session.start({ cwd: '/', surface: 'terminal', isInteractive: true })
  const r = await $.tool.call({ tool: TOOL, progetto: 'a b; rm', compito: 'x' } as never)
  expect(JSON.stringify(r)).toContain('deny')
})

test('un /clear scritto a mano non lancia /inizio', async ($, on) => {
  const d = motore(on)
  const clock = mock.clock(on)
  await $.session.start({ cwd: '/', surface: 'terminal', isInteractive: true })
  await $.session.end(fine)
  await clock.advance(5_000)
  expect(d.comandi).toEqual([])
})
