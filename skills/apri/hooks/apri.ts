// Logica pura, provata da tests/apri.test.ts.
// «Aprimi quel link» costa un turno intero del modello. /apri apre su questo computer l'ultimo link
// o file citato nelle risposte, senza turno e senza modello, con il programma predefinito.

const URL_RE = /https?:\/\/[^\s<>()`"'\]]+(?:\([^\s()]*\))?[^\s<>()`"'\].,;:!?]*/g
// Percorsi della persona: ~/…, la cartella utente del Mac o di Linux, un disco di Windows.
const PERCORSO = /(?:^|[\s(`'"])((?:~|\/(?:Users|home)|[A-Za-z]:)[\\/][^\s`'"()<>]+)/g
const PUNTI = /[.,;:!?)\]]+$/

export type Sistema = 'mac' | 'windows' | 'linux'

export function estrai(testo: string): string[] {
  const trovati: { i: number; v: string }[] = []
  for (const m of testo.matchAll(URL_RE)) trovati.push({ i: m.index ?? 0, v: m[0].replace(PUNTI, '') })
  for (const m of testo.matchAll(PERCORSO)) {
    const v = m[1] as string
    trovati.push({ i: (m.index ?? 0) + m[0].indexOf(v), v: v.replace(PUNTI, '') })
  }
  const visti = new Set<string>()
  return trovati
    .sort((a, b) => a.i - b.i)
    .map(x => x.v)
    .filter(v => (visti.has(v) ? false : (visti.add(v), true)))
}

export type Messaggio = { role: string; text?: string }

// La lista va dalla risposta più recente alla più vecchia, e dentro una risposta dall'ultimo link
// al primo. Contano solo le risposte di Claude: un link scritto dalla persona non entra.
export function scegli(messaggi: readonly Messaggio[], args: string): { voce: string | null; lista: string[] } {
  const lista: string[] = []
  for (const m of [...messaggi].reverse()) {
    if (m.role !== 'assistant' || typeof m.text !== 'string') continue
    for (const v of estrai(m.text).reverse()) if (!lista.includes(v)) lista.push(v)
    if (lista.length >= 20) break
  }
  const a = args.trim()
  if (a === '') return { voce: lista[0] ?? null, lista }
  if (/^\d+$/.test(a)) return { voce: lista[Number(a) - 1] ?? null, lista }
  return { voce: lista.find(v => v.toLowerCase().includes(a.toLowerCase())) ?? null, lista }
}

// cmd.exe legge & | < > ^ come comandi: il caret li rende lettere normali.
function perCmd(s: string): string {
  return s.replace(/[&|<>^]/g, c => `^${c}`)
}

// Il programma predefinito del sistema: il browser per i link, l'app di solito per i file.
export function comando(voce: string, home: string, sistema: Sistema): string[] {
  const v = /^https?:\/\//.test(voce) ? voce : voce.replace(/^~(?=[\\/])/, home)
  if (sistema === 'windows') return ['cmd', '/c', 'start', '', perCmd(v)]
  if (sistema === 'mac') return ['open', v]
  return ['xdg-open', v]
}

export function sistemaDa(os: string | undefined, uname: string | undefined): Sistema {
  if (os === 'Windows_NT') return 'windows'
  return (uname ?? '').trim() === 'Darwin' ? 'mac' : 'linux'
}
