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

// Le tre righe del blocco sotto l'intestazione: Arturo e versione, data e stato in parole, i link.
export type Blocco = {
  versione: string | null
  stato: string | null
  roadmap: string
  roadmapNuova: boolean
}

// L'invito alla roadmap: la data di ROADMAP.md e se è nuova o un promemoria; null = nessuna evidenza.
export type Invito = { tipo: 'nuova' | 'promemoria'; data: string } | null

// ~/.claude/session-env/roadmap-vista.json: la data della roadmap dell'ultimo invito e quando è stato mostrato
// (secondi). {"pausa": "sempre"} spegne l'invito.
export type Timbro = {
  data?: string
  mostrata?: number
  pausa?: 'sempre'
}

declare module 'claude-code' {
  interface PluginState {
    'testata': { ultima: Testata | null; blocco: Blocco | null }
  }
}
