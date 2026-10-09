import type { Register } from 'claude-code'

import { DB_URL, PATTERNS } from './patterns'

// I fixture dei test contengono token finti per mestiere: redatti, un Edit su quei file fallirebbe.
// Vale anche per i test dei mod in skills/: il test di questo mod tornerebbe a Claude con la sigla al posto del codice.
const ESENTI = /\/(?:hooks\/test[^/]*|tests\/fixtures\/|skills\/[^/]+\/tests\/)/

// Una sigla completa, come la scrive forma(): se compare in un testo da scrivere, Claude sta
// riscrivendo su disco un file che ha letto redatto, e il valore vero andrebbe perso.
export const SIGLA = /\[REDATTO:[a-z0-9-]+ len=\d+ sha256=[0-9a-f]{8}\]/

export function testiDaScrivere(e: Record<string, unknown>): string[] {
  const out: string[] = []
  for (const k of ['content', 'new_string', 'new_source']) if (typeof e[k] === 'string') out.push(e[k] as string)
  if (Array.isArray(e.edits)) {
    for (const ed of e.edits as unknown[]) {
      const ns = (ed as { new_string?: unknown } | null)?.new_string
      if (typeof ns === 'string') out.push(ns)
    }
  }
  return out
}

async function hash8(value: string): Promise<string> {
  const bytes = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(value))
  return Array.from(new Uint8Array(bytes).slice(0, 4), b => b.toString(16).padStart(2, '0')).join('')
}

async function forma(tipo: string, value: string): Promise<string> {
  return `[REDATTO:${tipo} len=${value.length} sha256=${await hash8(value)}]`
}

async function replaceAsync(text: string, re: RegExp, fn: (m: RegExpExecArray) => Promise<string>): Promise<string> {
  const parti: string[] = []
  let ultimo = 0
  re.lastIndex = 0
  for (let m = re.exec(text); m !== null; m = re.exec(text)) {
    parti.push(text.slice(ultimo, m.index), await fn(m))
    ultimo = m.index + m[0].length
    if (m[0].length === 0) re.lastIndex += 1
  }
  parti.push(text.slice(ultimo))
  return parti.join('')
}

const INTERPOLAZIONE = /^(?:\$\{[^}]*\}|\$[A-Za-z_][A-Za-z0-9_]*|%s|\{[^}]*\})$/

export async function redigi(text: string): Promise<{ text: string; count: number }> {
  let count = 0
  let out = await replaceAsync(text, DB_URL, async m => {
    // Una password fatta solo di interpolazione (${pw}, $PW, %s, {pw}) è codice, non un segreto:
    // redigerla faceva leggere a Claude sorgenti falsati, compreso il test di questo mod (3/10/2026).
    if (INTERPOLAZIONE.test(m[3] ?? '')) return m[0]
    count += 1
    return `${m[1]}://${m[2]}:${await forma('db-password', m[3] ?? '')}@`
  })
  for (const [re, tipo] of PATTERNS) {
    out = await replaceAsync(out, re, async m => {
      count += 1
      return forma(tipo, m[0])
    })
  }
  return { text: out, count }
}

type Blocco = { type: string; [field: string]: unknown }

async function redigiBlocchi(blocchi: readonly Blocco[]): Promise<{ blocchi: Blocco[]; count: number }> {
  let count = 0
  const out: Blocco[] = []
  for (const b of blocchi) {
    if (b.type === 'text' && typeof b.text === 'string') {
      const r = await redigi(b.text)
      count += r.count
      out.push({ ...b, text: r.text })
    } else if (b.type === 'tool_result' && typeof b.content === 'string') {
      const r = await redigi(b.content)
      count += r.count
      out.push({ ...b, content: r.text })
    } else if (b.type === 'tool_result' && Array.isArray(b.content)) {
      const r = await redigiBlocchi(b.content as Blocco[])
      count += r.count
      out.push({ ...b, content: r.blocchi })
    } else {
      out.push(b)
    }
  }
  return { blocchi: out, count }
}

export const register: Register = on => {
  // tool_use_id dei Read su fixture esenti. Una variabile del modulo basta: un reload perde
  // al massimo la chiamata in corso, che allora viene redatta (fallisce verso il lato sicuro).
  const esenti = new Set<string>()

  on('tool.call', { tool: 'Read' }, ($, e, next) => {
    if (e.tool_use_id !== undefined && ESENTI.test(e.file_path)) esenti.add(e.tool_use_id)
    return next(e)
  })

  on('tool.call', { tool: ['Write', 'Edit', 'NotebookEdit'] }, ($, e, next) => {
    if (testiDaScrivere(e as unknown as Record<string, unknown>).some(t => SIGLA.test(t))) {
      return {
        deny:
          'redazione-segreti: il testo da scrivere contiene una sigla [REDATTO:…]. Il file è stato letto redatto: ' +
          'scrivere la sigla cancellerebbe il valore vero. Modifica solo le righe senza segreti, oppure chiedi a chi usa Claude Code di farla a mano.',
      }
    }
    return next(e)
  })

  on('session.append', { door: 'tool-result' }, async ($, e, next) => {
    const ids = e.message.content.flatMap(b => (b.type === 'tool_result' && typeof b.tool_use_id === 'string' ? [b.tool_use_id] : []))
    if (ids.length > 0 && ids.every(id => esenti.delete(id))) return next(e)

    const { blocchi, count } = await redigiBlocchi(e.message.content)
    if (count === 0) return next(e)

    $.ui.toast(`${count} segreti redatti nell'output`)
    return next({ ...e, message: { ...e.message, content: blocchi } })
  }).catch(($, e, next) =>
    next({
      ...e,
      message: {
        ...e.message,
        content: e.message.content.map(b =>
          b.type === 'tool_result' ? { ...b, content: '[REDATTO: errore del mod redazione-segreti, output nascosto]' } : b,
        ),
      },
    }),
  )
}
