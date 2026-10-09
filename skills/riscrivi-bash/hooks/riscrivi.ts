// Logica pura, provata da tests/riscrivi.test.ts. Le regole ricalcano i due blocchi
// di hooks/bash-dispatcher.sh («Recidiva timeout» e «Recidiva glob in un'opzione»):
// il dispatcher resta come rete, questo mod corregge il comando prima che ci arrivi.

const Q = '\u0000'

// Stessa lunghezza dell'originale: le posizioni nel mascherato valgono nel comando vero.
export function maschera(c: string): string {
  const out: string[] = []
  let q: string | null = null
  for (let i = 0; i < c.length; i++) {
    const ch = c[i] as string
    if (ch === '\\' && q !== "'") {
      out.push(Q)
      if (i + 1 < c.length) out.push(Q)
      i += 1
      continue
    }
    if (q === null && (ch === "'" || ch === '"')) {
      q = ch
      out.push(Q)
    } else if (q !== null) {
      out.push(Q)
      if (ch === q) q = null
    } else {
      out.push(ch)
    }
  }
  return out.join('')
}

const OPTGLOB = /(^|[\s;&|(])(--[A-Za-z][\w-]*)=([^\s;&|()<>]*\*[^\s;&|()<>]*)/g

export function quotaGlob(c: string): { command: string; fatti: string[] } {
  if (c.includes('<<')) return { command: c, fatti: [] }
  const m = maschera(c)
  const fatti: string[] = []
  const pezzi: string[] = []
  let ultimo = 0
  for (const x of m.matchAll(OPTGLOB)) {
    const opt = x[2] as string
    const val = x[3] as string
    // Un valore che tocca una parte quotata o un escape resta al dispatcher.
    if (val.includes(Q)) continue
    // Un valore con una variabile o una tilde non si quota: fra apici `$HOME` e `~`
    // restano letterali e il comando cambierebbe senso (review del 9/10/2026).
    if (val.includes('$') || val.startsWith('~')) continue
    const start = (x.index ?? 0) + (x[1] as string).length
    const end = start + opt.length + 1 + val.length
    pezzi.push(c.slice(ultimo, start), `${opt}='${c.slice(start + opt.length + 1, end)}'`)
    ultimo = end
    fatti.push(`${opt}=${val} quotato`)
  }
  pezzi.push(c.slice(ultimo))
  return { command: pezzi.join(''), fatti }
}

const REMOTO = /(^|[\s;&|(])(ssh|docker\s+exec|kubectl\s+exec)\s|<</
const TIMEOUT = /(^|[;&|(`\n])(\s*)((?:sudo|env|command|exec)\s+)?timeout\s+((?:-[^\s]+\s+(?:[A-Z]+\s+)?)*)(\d+(?:\.\d+)?)([smhd]?)\s+/g
const UNITA: Record<string, number> = { '': 1, s: 1, m: 60, h: 3600, d: 86400 }

export function togliTimeout(c: string): { command: string; secondi: number; fatti: string[] } {
  if (REMOTO.test(c)) return { command: c, secondi: 0, fatti: [] }
  const m = maschera(c)
  const pezzi: string[] = []
  const fatti: string[] = []
  let ultimo = 0
  let secondi = 0
  const trovati = [...m.matchAll(TIMEOUT)]
  // Si riscrive solo un timeout unico nell'ultimo segmento: lì il tetto del tool vale come il
  // timeout tolto. Con un `|| echo giù` o un altro comando dopo, togliere il timeout cambia cosa fa
  // il comando, e il blocco spiegato del dispatcher resta la via giusta (3/10/2026).
  const dopo = trovati.length === 1 ? m.slice((trovati[0]?.index ?? 0) + (trovati[0]?.[0].length ?? 0)) : ''
  if (trovati.length !== 1 || /[;&|\n`]/.test(dopo)) return { command: c, secondi: 0, fatti: [] }
  for (const x of trovati) {
    const start = x.index ?? 0
    const testa = (x[1] as string) + (x[2] as string) + (x[3] ?? '')
    const n = Number(x[5]) * (UNITA[x[6] as string] ?? 1)
    secondi += n
    pezzi.push(c.slice(ultimo, start), testa)
    ultimo = start + x[0].length
    fatti.push(`timeout ${x[5]}${x[6]} tolto`)
  }
  pezzi.push(c.slice(ultimo))
  return { command: pezzi.join(''), secondi, fatti }
}

export type Contesto = { zsh: boolean; haTimeout: boolean; timeoutMs?: number; background?: boolean }

export function riscrivi(c: string, ctx: Contesto): { command: string; timeoutMs?: number; fatti: string[] } {
  let command = c
  const fatti: string[] = []
  let timeoutMs = ctx.timeoutMs
  if (ctx.zsh && command.includes('*')) {
    const r = quotaGlob(command)
    command = r.command
    fatti.push(...r.fatti)
  }
  if (!ctx.haTimeout && command.includes('timeout')) {
    const r = togliTimeout(command)
    if (r.fatti.length > 0) {
      command = r.command
      fatti.push(...r.fatti)
      const tetto = ctx.background === true ? 7_200_000 : 600_000
      timeoutMs = Math.min(tetto, Math.max(ctx.timeoutMs ?? 0, Math.ceil(r.secondi * 1000) + 5_000))
    }
  }
  return { command, timeoutMs, fatti }
}
