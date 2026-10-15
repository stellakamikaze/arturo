import { describe, expect, test } from 'claude-code/testing'

import { avvisi, avviso, cacheFredda, cartelleGws, leggiBanchi, SEGNALI_VUOTI, SOGLIA_TOKEN, tokenBuono, TTL_ABBONAMENTO, TTL_CREDITI, ttlDa } from '../hooks/cache'
import type { Cache } from '../types'

describe('cache fredda', () => {
  const t0 = 1_000_000
  const pesante: Cache = { ultimo: t0, tokens: 120_000, ttlMs: TTL_ABBONAMENTO, fredda: false }
  test('entro il TTL è calda', () => {
    expect(cacheFredda(pesante, t0 + TTL_ABBONAMENTO)).toBe(false)
  })
  test('oltre il TTL, con un contesto che pesa, è fredda', () => {
    expect(cacheFredda(pesante, t0 + TTL_ABBONAMENTO + 1)).toBe(true)
  })
  test('contesto leggero: nessun avviso anche se scaduta', () => {
    expect(cacheFredda({ ...pesante, tokens: SOGLIA_TOKEN - 1 }, t0 + 2 * TTL_ABBONAMENTO)).toBe(false)
  })
  test('nessun turno ancora: nessun avviso', () => {
    expect(cacheFredda({ ...pesante, ultimo: null, tokens: null }, t0)).toBe(false)
  })
  test('quota piena: TTL di 5 minuti, fredda dopo 6', () => {
    const ttl = ttlDa([{ kind: 'five_hour', percentUsed: 100 }, { kind: 'seven_day', percentUsed: 40 }])
    expect(ttl).toBe(TTL_CREDITI)
    expect(cacheFredda({ ...pesante, ttlMs: ttl }, t0 + 6 * 60_000)).toBe(true)
  })
  test('quota sotto il 100% o nessuna finestra: 1 ora', () => {
    expect(ttlDa([{ kind: 'five_hour', percentUsed: 99 }])).toBe(TTL_ABBONAMENTO)
    expect(ttlDa([])).toBe(TTL_ABBONAMENTO)
  })
  test("l'avviso dice quanti token riscrive, e tace se la cache è calda", () => {
    expect(avviso({ ...pesante, fredda: true })).toContain('riscrive 120k token')
    expect(avviso(pesante)).toBeUndefined()
  })
})

describe('banchi rossi', () => {
  // Il formato di tests/banchi-avvio.sh, l'unico che scrive il file.
  test('esito rosso col numero di banchi rossi', () => {
    const esito = 'ROSSO\n2 banchi delle guardie rossi su 5 (2026-10-15 09:12)\ntest_guardie_unite.py: AssertionError\n'
    expect(leggiBanchi(esito)).toEqual({ rosso: true, riassunto: '2 banchi rossi su 5' })
  })
  test('esito rosso senza conteggio, esito verde, file illeggibile', () => {
    expect(leggiBanchi('ROSSO\n')).toEqual({ rosso: true, riassunto: 'banchi rossi' })
    expect(leggiBanchi('VERDE\n5 banchi delle guardie verdi (2026-10-15 09:12)\n')).toEqual({ rosso: false, riassunto: 'verdi' })
    expect(leggiBanchi('')).toBeNull()
  })
})

describe('token gws in errore', () => {
  test('le cartelle di gws: quella di default e una per account', () => {
    expect(cartelleGws(['gws-personale', 'git', 'gws', 'gws-lavoro', 'gwsx', 'gh'])).toEqual(['gws', 'gws-lavoro', 'gws-personale'])
  })
  test('token buono solo con refresh token e token valido', () => {
    expect(tokenBuono(0, 'banner\n{"has_refresh_token": true, "token_valid": true}')).toBe(true)
    expect(tokenBuono(0, '{"has_refresh_token": true, "token_valid": false}')).toBe(false)
    expect(tokenBuono(0, '{"has_refresh_token": false, "token_valid": true}')).toBe(false)
    expect(tokenBuono(1, '{"has_refresh_token": true, "token_valid": true}')).toBe(false)
    expect(tokenBuono(0, 'niente JSON')).toBe(false)
  })
})

describe('avvisi sotto il prompt: solo eccezioni', () => {
  const calda: Cache = { ultimo: 1, tokens: 120_000, ttlMs: TTL_ABBONAMENTO, fredda: false }
  test('tutto in regola: nessuna riga', () => {
    expect(avvisi(calda, SEGNALI_VUOTI)).toBeUndefined()
    expect(avvisi(calda, { banchi: { rosso: false, riassunto: 'verdi' }, gwsKo: [] })).toBeUndefined()
  })
  test('banchi rossi e gws in errore nella stessa riga', () => {
    const r = avvisi(calda, { banchi: { rosso: true, riassunto: '2 banchi rossi su 5' }, gwsKo: ['gws-lavoro'] })
    expect(r).toContain('guardie: 2 banchi rossi su 5')
    expect(r).toContain('bash ~/.claude/tests/banchi-avvio.sh')
    expect(r).toContain('gws: login da rifare per gws-lavoro')
  })
  test('la cache fredda resta il primo avviso', () => {
    const r = avvisi({ ...calda, fredda: true }, { banchi: null, gwsKo: ['gws'] }) ?? ''
    expect(r.startsWith('cache fredda')).toBe(true)
    expect(r).toContain('gws: login da rifare per gws')
  })
})
