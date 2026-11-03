// I tipi delle parti del mod arturo che tengono valori in $.state: cache-fredda, dafare, testata.
// Un mod solo ha un solo contratto: le chiavi delle tre parti stanno sotto 'arturo' e non si ripetono.

// --- cache-fredda ---
// Cache del prompt della sessione principale: ultimo contatto col modello, token da riscrivere, durata.
export type Cache = {
  ultimo: number | null
  tokens: number | null
  ttlMs: number
  fredda: boolean
}

// L'altro avviso sotto il prompt: gli account gws con il token in errore.
export type Segnali = { gwsKo: string[] }

// --- dafare ---
// Il contratto del pannello /dafare con la CLI `arturo todo --json`.
// TodoVoce ha le chiavi di CHIAVI_TODO in bin/todo_store.py: il banco tests/test_pannello.py (U04)
// le confronta con il JSON vero della CLI.

export type Chi = 'tu' | 'decidi' | 'io'
export type TipoGruppo = 'tu' | 'decidi' | 'io' | 'fermo'

export type TodoVoce = {
  id: number
  titolo: string
  progetto: string
  scadenza: string | null
  scadenza_testo: string | null
  giorni: number | null
  priorita: string
  stato: string
  quando: string
  chi: Chi
  perche: string | null
  motivo: string | null
  gruppo: TipoGruppo | null
  dopo: number[]
  attende: number[]
  note: string[]
}

export type Gruppo = {
  tipo: TipoGruppo
  titolo: string
  descrizione: string
  todo: TodoVoce[]
}

export type Vista = {
  versione: number
  oggi: string
  progetto: string | null
  gruppi: Gruppo[]
  chiusi: number
  avvisi: string[]
}

// Un passo da annullare: gli argomenti della CLI dopo "todo", calcolati prima di scrivere.
export type Annullabile = { argv: string[]; descrizione: string; id: number }

// L'ultima risposta a un tasto: una riga sotto il titolo del pannello.
export type Esito = { testo: string; ok: boolean }

// --- testata ---
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
    arturo: {
      // cache-fredda
      cache: Cache
      segnali: Segnali
      // dafare
      vista: Vista | null
      errore: string
      esito: Esito | null
      scelto: number | null
      filtro: string
      chiusiQui: TodoVoce[]
      annullabili: Annullabile[]
      python: string[] | null
      barraNascosta: boolean
      // testata
      ultima: Testata | null
      blocco: Blocco | null
    }
  }
}
