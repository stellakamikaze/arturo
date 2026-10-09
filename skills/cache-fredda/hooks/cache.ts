// Logica pura, provata da tests/cache.test.ts.
import type { Cache } from '../types'

// TTL della cache secondo le regole di Claude Code: 1 ora con un abbonamento Claude, 5 minuti quando
// una finestra di quota (5 ore o 7 giorni) è piena e le richieste passano ai crediti. Metodo preso da
// prompt-cache-control (davila7/claude-code-templates, MIT).
export const TTL_ABBONAMENTO = 3_600_000
export const TTL_CREDITI = 300_000
// Sotto questa soglia rileggere il contesto costa poco: nessun avviso.
export const SOGLIA_TOKEN = 50_000

export const VUOTA: Cache = { ultimo: null, tokens: null, ttlMs: TTL_ABBONAMENTO, fredda: false }

export function ttlDa(finestre: readonly { kind: string; percentUsed: number }[]): number {
  const piena = finestre.some(w => (w.kind === 'five_hour' || w.kind === 'seven_day') && w.percentUsed >= 100)
  return piena ? TTL_CREDITI : TTL_ABBONAMENTO
}

export function cacheFredda(c: Cache, ora: number): boolean {
  return c.ultimo !== null && c.tokens !== null && c.tokens >= SOGLIA_TOKEN && ora - c.ultimo > c.ttlMs
}

export function avviso(c: Cache): string | undefined {
  if (!c.fredda || c.tokens === null) return undefined
  return `cache fredda: il prossimo messaggio riscrive ${Math.round(c.tokens / 1000)}k token. Se il lavoro è cambiato, conviene una sessione nuova`
}
