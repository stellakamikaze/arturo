import { atom, read, update } from 'claude-code'
import type { EngineInterface, Register } from 'claude-code'

import { type Avanti, type Evento, parteSpenta } from '../parti'
import { radiciArturo } from './radici'
import {
  COLONNE_MARCHIO, LARGHEZZA_MARCHIO, URL_INVIA, URL_ROADMAP, blocco, dataRoadmap,
  decidiInvito, dettaglio, leggiAggiornamento, leggiDeriva, leggiTimbro, nuovoTimbro, versioneArturo,
} from './testata'
import type { Blocco, Invito, Testata } from '../../types'

// L'intestazione di Claude Code (mascotte, versione, modello) non si sostituisce: nessuna opzione la cambia e
// nessun mod la ridisegna (verificato su 2.1.317, 3/11/2026). Il blocco di Arturo è la prima riga piazzata
// nella conversazione, quindi sta subito sotto: il marchio con la stella a sinistra, tre righe a destra.
const ultima = atom({ plugin: 'arturo', key: 'ultima' } as const, null as Testata | null)
const disegno = atom({ plugin: 'arturo', key: 'blocco' } as const, null as Blocco | null)

async function leggi($: EngineInterface, path: string): Promise<string | null> {
  return $.fs.read(path).then(
    t => (typeof t === 'string' ? t : null),
    () => null,
  )
}

async function versione($: EngineInterface, home: string): Promise<string | null> {
  for (const radice of await radici($, home)) {
    const r = await $.process
      .run(['git', '-C', radice, 'describe', '--tags', '--match', 'v*'], { timeoutMs: 5_000 })
      .catch(() => undefined)
    const v = r !== undefined && r.exitCode === 0 ? versioneArturo(r.stdout) : null
    if (v !== null) return v
  }
  return null
}

async function casa($: EngineInterface): Promise<string> {
  return (await $.env.get('HOME')) ?? (await $.env.get('USERPROFILE')) ?? ''
}

// Il mod può arrivare da un link in ~/.claude/skills verso un clone di Arturo altrove: la radice vera
// la dice git dalla cartella del mod, che segue il link. Senza git (il plugin) restano le radici di radici.ts.
async function radici($: EngineInterface, home: string): Promise<string[]> {
  const r = await $.process
    .run(['git', '-C', $.plugin.root, 'rev-parse', '--show-toplevel'], { timeoutMs: 5_000 })
    .catch(() => undefined)
  const vera = r !== undefined && r.exitCode === 0 ? r.stdout.trim() : ''
  return [...(vera === '' ? [] : [vera]), ...radiciArturo($.plugin.root, home)]
}

export async function componi($: EngineInterface): Promise<Testata> {
  const home = await casa($)
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

// L'invito alla roadmap: la data viene dal ROADMAP.md installato, il timbro dice quando l'ho mostrato.
async function invito($: EngineInterface): Promise<Invito> {
  const home = await casa($)
  let data: string | null = null
  for (const radice of await radici($, home)) {
    const md = await leggi($, `${radice}/ROADMAP.md`)
    data = md === null ? null : dataRoadmap(md)
    if (data !== null) break
  }
  const percorso = `${home}/.claude/session-env/roadmap-vista.json`
  const grezzo = await leggi($, percorso)
  const timbro = grezzo === null ? null : leggiTimbro(grezzo)
  const adessoS = (await $.clock.now()) / 1000
  const tipo = decidiInvito(data, timbro, adessoS)
  if (tipo === null || data === null) return null
  await $.fs.write(percorso, nuovoTimbro(timbro, data, adessoS)).catch(() => undefined)
  return { tipo, data }
}

export async function avvio($: EngineInterface, e: Evento<'session.start'>, next: Avanti<'session.start'>) {
  if (await parteSpenta($, 'testata')) return next(e)
  await $.command.register({ name: 'versione', description: 'Versione di Arturo e di Claude Code, deriva della config e aggiornamenti' })
  const [t, inv] = await Promise.all([componi($), invito($)])
  await update($, ultima, () => t)
  await update($, disegno, () => blocco(t, inv))
  const r = await next(e)
  await $.ui.place({ id: 'testata' })
  return r
}

export const register: Register = on => {

  on('ui.render', { component: 'Placed' }, async ($, e, next) => {
    if (await parteSpenta($, 'testata')) return next(e)
    if (e.props.plugin !== $.plugin.name || e.props.id !== 'testata') return next(e)
    const b = await read($, disegno)
    if (b === null) return next(e)
    const elementi = $.ui.resolve(e)
    const { Box, Text, Link } = elementi
    const BLU = '#2b8cff'
    // Come l'intestazione di Claude Code: nome in grassetto e versione, una riga di stato, poi i due link.
    const righe = (
      <Box flexDirection="column">
        <Text><Text bold>Arturo</Text>{b.versione === null ? '' : <Text dimColor>{` ${b.versione}`}</Text>}</Text>
        {b.stato === null ? null : <Text dimColor>{b.stato}</Text>}
        <Text>
          <Link href={URL_ROADMAP}><Text color={BLU} bold={b.roadmapNuova}>{b.roadmap}</Text></Link>
          <Text dimColor>{' \u00b7 '}</Text>
          <Link href={URL_INVIA}><Text color={BLU}>Invia Arturo a chi ne ha bisogno</Text></Link>
        </Text>
      </Box>
    )
    // Una superficie che non dice la sua larghezza riceve il blocco intero.
    const colonne = (e.viewport as { columns?: number } | undefined)?.columns
    if (colonne !== undefined && colonne < COLONNE_MARCHIO) return righe
    // Una superficie senza Client (il modulo che anima la stella) riceve solo le righe.
    if (!('Client' in elementi)) return righe
    const { Client } = elementi
    // Arturo in pixel accanto al testo, come la mascotte di Claude Code accanto al suo.
    return (
      <Box flexDirection="row">
        <Box flexDirection="column" width={LARGHEZZA_MARCHIO} flexShrink={0}>
          <Client key="stella" module="./stella.tsx" />
        </Box>
        {righe}
      </Box>
    )
  })

  on('command.run', { command: 'versione' }, async ($, e, next) => {
    if (await parteSpenta($, 'testata')) return next(e)
    const t = await componi($)
    await update($, ultima, () => t)
    return { text: dettaglio(t) }
  })
}
