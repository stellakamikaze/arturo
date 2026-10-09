// Cache del prompt della sessione principale: ultimo contatto col modello, token da riscrivere, durata.
export type Cache = {
  ultimo: number | null
  tokens: number | null
  ttlMs: number
  fredda: boolean
}

declare module 'claude-code' {
  interface PluginState {
    'cache-fredda': { cache: Cache }
  }
}
