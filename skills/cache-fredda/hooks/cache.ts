// Logica pura, provata da tests/cache.test.ts.
import type { Banchi, Cache, Segnali } from '../types'

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

// --- Gli altri avvisi sotto il prompt: banchi rossi e token gws in errore -----------------------
// Solo eccezioni: un segnale in regola, o che non si può leggere, non scrive niente.

// cache/banchi-ultimo-esito.txt, scritto dal gate (tests/verifica-allineamento.sh) a ogni corsa:
// riga 1 ROSSO o VERDE, riga 2 il riassunto («=== … 1 FAIL … ===»).
export function leggiBanchi(testo: string): Banchi | null {
  const righe = testo.split('\n')
  const stato = (righe[0] ?? '').trim()
  if (stato !== 'ROSSO' && stato !== 'VERDE') return null
  const fail = /(\d+) FAIL/.exec(righe[1] ?? '')
  return { rosso: stato === 'ROSSO', riassunto: stato === 'ROSSO' ? (fail ? `${fail[1]} FAIL` : 'rossi') : 'verdi' }
}

// Le cartelle di config di gws in ~/.config: gws (quella di default) e gws-<nome>, una per account.
export function cartelleGws(nomi: readonly string[]): string[] {
  return nomi.filter(n => /^gws(?:[-_][\w.-]+)?$/.test(n)).sort()
}

// Esito di `gws auth status` per un account che ha fatto il login: vero se il token è buono.
export function tokenBuono(exitCode: number, stdout: string): boolean {
  if (exitCode !== 0) return false
  const i = stdout.indexOf('{')
  if (i < 0) return false
  try {
    const d = JSON.parse(stdout.slice(i)) as { has_refresh_token?: unknown; token_valid?: unknown }
    return d.has_refresh_token === true && d.token_valid === true
  } catch {
    return false
  }
}

export const SEGNALI_VUOTI: Segnali = { banchi: null, gwsKo: [] }

export function avvisi(c: Cache, s: Segnali): string | undefined {
  const pezzi: string[] = []
  const fredda = avviso(c)
  if (fredda !== undefined) pezzi.push(fredda)
  if (s.banchi?.rosso) pezzi.push(`banchi ${s.banchi.riassunto}: rilancia bash tests/verifica-allineamento.sh`)
  if (s.gwsKo.length > 0) pezzi.push(`gws: login da rifare per ${s.gwsKo.join(', ')} (docs/onboarding/gws.md)`)
  return pezzi.length === 0 ? undefined : pezzi.join(' · ')
}
