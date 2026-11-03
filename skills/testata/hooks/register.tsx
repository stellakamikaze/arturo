import { atom, update } from 'claude-code'
import type { EngineInterface, Register } from 'claude-code'

import { radiciArturo } from './radici'
import { dettaglio, leggiAggiornamento, leggiDeriva, riga, versioneArturo } from './testata'
import type { Testata } from '../types'

// Il logo di Claude Code non si sostituisce: nessuna opzione lo cambia e nessun mod lo ridisegna
// (verificato su 2.1.317, 3/11/2026). La testata di Arturo è la prima riga sotto l'intestazione.
const ultima = atom({ plugin: 'testata', key: 'ultima' } as const, null as Testata | null)

async function leggi($: EngineInterface, path: string): Promise<string | null> {
  return $.fs.read(path).then(
    t => (typeof t === 'string' ? t : null),
    () => null,
  )
}

async function versione($: EngineInterface, home: string): Promise<string | null> {
  for (const radice of radiciArturo($.plugin.root, home)) {
    const r = await $.process
      .run(['git', '-C', radice, 'describe', '--tags', '--match', 'v*'], { timeoutMs: 5_000 })
      .catch(() => undefined)
    const v = r !== undefined && r.exitCode === 0 ? versioneArturo(r.stdout) : null
    if (v !== null) return v
  }
  return null
}

export async function componi($: EngineInterface): Promise<Testata> {
  const home = (await $.env.get('HOME')) ?? (await $.env.get('USERPROFILE')) ?? ''
  const [arturo, claude, deriva, agg] = await Promise.all([
    versione($, home),
    $.session.version().then(v => v.version, () => null),
    leggi($, `${home}/.claude/cache/deriva.json`),
    leggi($, `${home}/.claude/session-env/aggiornamento.json`),
  ])
  return {
    arturo,
    claude,
    deriva: deriva === null ? null : leggiDeriva(deriva),
    aggiornamento: agg === null ? null : leggiAggiornamento(agg),
  }
}

export const register: Register = on => {
  on('session.start', async ($, e, next) => {
    await $.command.register({ name: 'versione', description: 'Versione di Arturo e di Claude Code, deriva della config e aggiornamenti' })
    const t = await componi($)
    await update($, ultima, () => t)
    $.ui.log(riga(t))
    return next(e)
  })

  on('command.run', { command: 'versione' }, async $ => {
    const t = await componi($)
    await update($, ultima, () => t)
    return { text: dettaglio(t) }
  })
}
