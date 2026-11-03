// La deriva come la scrive hooks/deriva.py in ~/.claude/cache/deriva.json a ogni avvio.
export type Deriva = {
  // false quando la config non ha un riferimento ad Arturo con cui confrontarsi (niente da dire).
  misurata: boolean
  file: string[]
  guardie: string[]
  hook: string[]
  config: string[]
}

// Lo stato degli aggiornamenti come lo scrive bin/aggiornamenti.py in ~/.claude/session-env/aggiornamento.json.
export type Aggiornamento = {
  stato: string
  versione: string
  compromesso?: boolean
  non_verificabile?: boolean
}

export type Testata = {
  arturo: string | null
  claude: string | null
  deriva: Deriva | null
  aggiornamento: Aggiornamento | null
}

declare module 'claude-code' {
  interface PluginState {
    testata: { ultima: Testata | null }
  }
}
