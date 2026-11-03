// Cache del prompt della sessione principale: ultimo contatto col modello, token da riscrivere, durata.
export type Cache = {
  ultimo: number | null
  tokens: number | null
  ttlMs: number
  fredda: boolean
}

// L'altro avviso sotto il prompt: gli account gws con il token in errore.
export type Segnali = { gwsKo: string[] }

declare module 'claude-code' {
  interface PluginState {
    'cache-fredda': { cache: Cache; segnali: Segnali }
  }
}
