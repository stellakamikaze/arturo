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

// Un passo da annullare: gli argomenti della CLI dopo «todo», calcolati prima di scrivere.
export type Annullabile = { argv: string[]; descrizione: string; id: number }

// L'ultima risposta a un tasto: una riga sotto il titolo del pannello.
export type Esito = { testo: string; ok: boolean }

declare module 'claude-code' {
  interface PluginState {
    dafare: {
      vista: Vista | null
      errore: string
      esito: Esito | null
      scelto: number | null
      filtro: string
      chiusiQui: TodoVoce[]
      annullabili: Annullabile[]
      python: string[] | null
      barraNascosta: boolean
    }
  }
}
