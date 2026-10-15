// Cache del prompt della sessione principale: ultimo contatto col modello, token da riscrivere, durata.
export type Cache = {
  ultimo: number | null
  tokens: number | null
  ttlMs: number
  fredda: boolean
}

// L'ultimo esito dei banchi delle guardie (tests/banchi-avvio.sh), letto da cache/banchi-ultimo-esito.txt.
export type Banchi = { rosso: boolean; riassunto: string }

// Gli altri avvisi sotto il prompt: banchi rossi e account gws con il token in errore.
export type Segnali = { banchi: Banchi | null; gwsKo: string[] }

declare module 'claude-code' {
  interface PluginState {
    'cache-fredda': { cache: Cache; segnali: Segnali }
  }
}
