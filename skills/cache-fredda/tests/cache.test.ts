import { describe, expect, test } from 'claude-code/testing'

import { avviso, cacheFredda, SOGLIA_TOKEN, TTL_ABBONAMENTO, TTL_CREDITI, ttlDa } from '../hooks/cache'
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
