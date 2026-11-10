// La logica della rotazione, pura: si prova senza motore (3/11/2026).

// Fra due rotazioni non c'è più un tempo minimo (10/11/2026): il limite di 3 minuti fermava il giro
// quando una rotazione decisa non partiva e si riarmava subito. Resta solo se ROTAZIONE_MIN_S lo chiede.
export const MIN_INTERVALLO_MS = 0
export const ATTESA_CLEAR_MS = 800
export const ATTESA_INIZIO_MS = 1500
export const RIPROVA_CLEAR_MS = 5000
// Dopo il secondo /clear: se la sessione non si chiude entro questo tempo, la rotazione si annulla.
export const SCADENZA_CLEAR_MS = 10_000
// Testo nella casella a fine turno: si aspetta invece di annullare. Il 7 e l'8/11 un "2" rimasto
// nella casella per ore ha annullato due rotazioni ("stai scrivendo"). Una bozza ferma per un minuto
// è vecchia: si ruota e la si rimette nella casella. Una bozza che cambia aspetta fino a 10 minuti.
export const CONTROLLO_BOZZA_MS = 15_000
export const BOZZA_FERMA_MS = 60_000
export const ATTESA_BOZZA_MAX_MS = 10 * 60_000

// `domanda`: la domanda alla persona arrivata dopo ruota nello stesso turno (segnalazione n. 65, 10/11/2026).
export type Rotazione = { progetto: string; compito: string; domanda?: string }

// Quanto della domanda viaggia nella riga di /inizio.
export const DOMANDA_MAX = 300

// La domanda aperta alla fine del turno: quella fatta con AskUserQuestion dopo ruota, se c'è, oppure l'ultima
// riga del testo finale quando finisce con "?". Senza domanda, undefined: la rotazione riparte come sempre.
export function domandaAperta(answer: string, chiesta?: string): string | undefined {
  if (chiesta && chiesta.trim()) return chiesta.replace(/\s+/g, ' ').trim()
  const righe = answer.split('\n').map(r => r.replace(/[*_`>#]/g, '').trim()).filter(Boolean)
  const ultima = righe[righe.length - 1]
  return ultima && /\?\s*$/.test(ultima) ? ultima : undefined
}

// Il testo delle domande di una chiamata ad AskUserQuestion.
export function testoDomande(e: unknown): string {
  const q = (e as { questions?: unknown }).questions
  if (!Array.isArray(q)) return ''
  return q.map(x => (x && typeof (x as { question?: unknown }).question === 'string' ? (x as { question: string }).question : ''))
    .filter(Boolean).join(' · ')
}

export type Esito =
  | { azione: 'clear' }
  | { azione: 'attendi' }
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
  intervalloMs?: number // ROTAZIONE_MIN_S: tempo minimo fra due rotazioni, spento se manca
}): Esito {
  if (!p.armata) return { azione: 'niente' }
  if (p.agentId) return { azione: 'niente' } // turno di un subagent: la rotazione aspetta il turno principale
  if (p.reason !== 'answer') return { azione: 'disarma', motivo: 'turno interrotto: rotazione annullata' }
  if (p.bozza.trim() !== '') return { azione: 'attendi' }
  const intervallo = p.intervalloMs ?? MIN_INTERVALLO_MS
  if (intervallo > 0 && p.ultima !== undefined && p.ora - p.ultima < intervallo)
    return {
      azione: 'disarma',
      motivo: `due rotazioni in meno di ${Math.round(intervallo / 1000)} secondi: giro fermato`,
    }
  return { azione: 'clear' }
}

// Un controllo della casella durante l'attesa. `fermaDa` è quando la bozza ha preso il testo attuale.
export type Attesa = { bozza: string; fermaDa: number; iniziata: number }
export function vediBozza(a: Attesa, testo: string, ora: number):
  | { azione: 'clear'; bozza: string }
  | { azione: 'aspetta'; attesa: Attesa }
  | { azione: 'disarma'; motivo: string } {
  if (testo.trim() === '') return { azione: 'clear', bozza: '' }
  if (testo !== a.bozza) {
    if (ora - a.iniziata >= ATTESA_BOZZA_MAX_MS)
      return { azione: 'disarma', motivo: 'stai scrivendo da 10 minuti: rotazione annullata' }
    return { azione: 'aspetta', attesa: { ...a, bozza: testo, fermaDa: ora } }
  }
  if (ora - a.fermaDa >= BOZZA_FERMA_MS) return { azione: 'clear', bozza: testo }
  return { azione: 'aspetta', attesa: a }
}

// Con una domanda aperta la riga porta --in-attesa: /inizio in rotazione si ferma lì e rifà la domanda.
export function argomentiInizio(r: Rotazione): string {
  const compito = r.compito.replace(/\s+/g, ' ').trim()
  const domanda = (r.domanda ?? '').replace(/\s+/g, ' ').trim().slice(0, DOMANDA_MAX)
  return `${r.progetto.trim()} -- --rotazione ${compito}${domanda ? ` --in-attesa ${domanda}` : ''}`
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
