// La logica della rotazione, pura: si prova senza motore (3/11/2026).

export const MIN_INTERVALLO_MS = 3 * 60 * 1000
export const ATTESA_CLEAR_MS = 800
export const ATTESA_INIZIO_MS = 1500
export const RIPROVA_CLEAR_MS = 5000

export type Rotazione = { progetto: string; compito: string }

export type Esito =
  | { azione: 'clear' }
  | { azione: 'niente' }
  | { azione: 'disarma'; motivo: string }

// Il nome del tool viene dal plugin: `rotazione` in Arturo, la copia nella config ha il suo.
export function nomeTool(plugin: string): string {
  return `mcp__${plugin}__ruota`
}

// La decisione a fine turno.
export function decidi(p: {
  armata: Rotazione | undefined
  reason: string
  agentId: string | undefined
  bozza: string
  ora: number
  ultima: number | undefined
  intervalloMs?: number // ROTAZIONE_MIN_S lo abbassa solo nelle prove dal vivo
}): Esito {
  if (!p.armata) return { azione: 'niente' }
  if (p.agentId) return { azione: 'niente' } // turno di un subagent: la rotazione aspetta il turno principale
  if (p.reason !== 'answer') return { azione: 'disarma', motivo: 'turno interrotto: rotazione annullata' }
  if (p.bozza.trim() !== '') return { azione: 'disarma', motivo: 'stai scrivendo: rotazione annullata' }
  if (p.ultima !== undefined && p.ora - p.ultima < (p.intervalloMs ?? MIN_INTERVALLO_MS))
    return { azione: 'disarma', motivo: 'due rotazioni in meno di 3 minuti: giro fermato' }
  return { azione: 'clear' }
}

export function argomentiInizio(r: Rotazione): string {
  const compito = r.compito.replace(/\s+/g, ' ').trim()
  return `${r.progetto.trim()} -- --rotazione ${compito}`
}

export function leggiArgomenti(e: unknown): Rotazione | string {
  const a = e as { progetto?: unknown; compito?: unknown }
  const progetto = typeof a.progetto === 'string' ? a.progetto.trim() : ''
  const compito = typeof a.compito === 'string' ? a.compito.trim() : ''
  if (!/^[\w.-]+$/.test(progetto)) return 'progetto mancante o non valido (serve lo slug, es. "arturo")'
  if (compito === '') return 'compito mancante: scrivi il prossimo step in una frase'
  return { progetto, compito }
}

// "0", "no", "off", "spenta" spengono la rotazione; vuoto o assente la lasciano accesa.
export function spenta(valore: string | undefined): boolean {
  return valore !== undefined && /^(0|no|off|spent[ao]|false)$/i.test(valore.trim())
}
