// Il testo che Claude ha scritto nel turno in corso, dal prompt della persona in poi.
export type Msg = { role: 'user' | 'assistant'; text: string; toolResults?: readonly unknown[] }

export function testoDelTurno(msgs: readonly Msg[]): string {
  const pezzi: string[] = []
  for (let i = msgs.length - 1; i >= 0; i--) {
    const m = msgs[i] as Msg
    if (m.role === 'user') {
      const eRisultato = (m.toolResults?.length ?? 0) > 0
      if (!eRisultato && m.text.trim() !== '' && !m.text.startsWith('<')) break
      continue
    }
    if (m.text.trim() !== '') pezzi.unshift(m.text.trim())
  }
  return pezzi.join('\n\n')
}

// Un testo di una o due righe si legge già sopra il menu: il pannello serve oltre.
export function servePannello(testo: string): boolean {
  return testo.split('\n').filter(r => r.trim() !== '').length > 2
}

// Markdown ridotto a righe di testo: il pannello usa Text coi suoi colori, non il Markdown del tema.
export function righeLeggibili(testo: string): string[] {
  return testo
    .split('\n')
    .map(r => r.replace(/\*\*(.+?)\*\*/g, '$1').replace(/`([^`]+)`/g, '$1').replace(/^#+\s*/, ''))
}
