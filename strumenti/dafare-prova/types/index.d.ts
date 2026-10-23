export type Chi = 'tu' | 'decidi' | 'io'

export type Voce = {
  id: number
  titolo: string
  progetto: string
  chi: Chi
  stato: 'da fare' | 'fermo' | 'fatto'
  giorni: number | null
  motivo: string | null
  dopo: number[]
}

declare module 'claude-code' {
  interface PluginState {
    'dafare-prova': {
      voci: Shaped<Voce[]>
      filtro: string
      catena: boolean
      scelto: number | null
      esito: string
    }
  }
}
