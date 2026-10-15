import { atom, read, update } from 'claude-code'
import type { EngineInterface, Register } from 'claude-code'

import { avvisi, cacheFredda, cartelleGws, leggiBanchi, SEGNALI_VUOTI, tokenBuono, ttlDa, VUOTA } from './cache'

// Gli avvisi stanno nella riga sotto il prompt ($.ui.status), accanto a quelli di Claude Code: non
// coprono la fascia di /dafare. Solo eccezioni: cache fredda, banchi rossi, token gws in errore.
const cache = atom({ plugin: 'cache-fredda', key: 'cache' } as const, VUOTA)
const segnali = atom({ plugin: 'cache-fredda', key: 'segnali' } as const, SEGNALI_VUOTI)
const UN_MINUTO = 60_000
const DIECI_MINUTI = 600_000
const SEI_ORE = 6 * 3_600_000
// L'esito del gate sta nella copia di Arturo che porta questo mod: <radice>/skills/cache-fredda/../../cache.
const ESITO_REL = '/../../cache/banchi-ultimo-esito.txt'

async function mostra($: EngineInterface): Promise<void> {
  $.ui.status(avvisi(await read($, cache), await read($, segnali)))
}

async function controlla($: EngineInterface): Promise<void> {
  const c = await read($, cache)
  const fredda = cacheFredda(c, await $.clock.now())
  if (fredda === c.fredda) return
  await update($, cache, x => ({ ...x, fredda }))
  await mostra($)
}

async function rinnovata($: EngineInterface): Promise<void> {
  const { context, rateLimits } = await $.session.usage()
  const ora = await $.clock.now()
  await update($, cache, () => ({ ultimo: ora, tokens: context.tokens ?? null, ttlMs: ttlDa(rateLimits), fredda: false }))
  await mostra($)
}

async function banchi($: EngineInterface): Promise<void> {
  const testo = await $.fs.read($.plugin.root + ESITO_REL).then(
    t => (typeof t === 'string' ? t : null),
    () => null,
  )
  const b = testo === null ? null : leggiBanchi(testo)
  await update($, segnali, s => ({ ...s, banchi: b }))
  await mostra($)
}

// Un account conta solo se ha fatto il login (credentials.enc o credentials.json): una cartella
// preparata e mai usata non è un token in errore. Se gws non parte, l'account non si giudica.
async function gwsInErrore($: EngineInterface, home: string, nome: string, windows: boolean): Promise<boolean> {
  const dir = `${home}/.config/${nome}`
  const credenziali = await Promise.all(['credentials.enc', 'credentials.json'].map(f => $.fs.stat(`${dir}/${f}`).then(() => true, () => false)))
  if (!credenziali.some(Boolean)) return false
  const argv = windows ? ['cmd', '/c', 'gws', 'auth', 'status'] : ['gws', 'auth', 'status']
  const r = await $.process.run(argv, { env: { GOOGLE_WORKSPACE_CLI_CONFIG_DIR: dir }, timeoutMs: 10_000 }).catch(() => undefined)
  if (r === undefined) return false
  return !tokenBuono(r.exitCode, r.stdout)
}

async function gws($: EngineInterface): Promise<void> {
  const home = (await $.env.get('HOME')) ?? (await $.env.get('USERPROFILE')) ?? ''
  if (home === '') return
  const windows = (await $.env.get('OS')) === 'Windows_NT'
  const voci = await $.fs.list(`${home}/.config`).catch(() => [])
  const nomi = cartelleGws(voci.filter(v => v.kind !== 'file').map(v => v.name))
  const esiti = await Promise.all(nomi.map(n => gwsInErrore($, home, n, windows)))
  const ko = nomi.filter((_, i) => esiti[i])
  await update($, segnali, s => ({ ...s, gwsKo: ko }))
  await mostra($)
}

export const register: Register = on => {
  on('session.start', async ($, e, next) => {
    $.clock.every(UN_MINUTO, () => void controlla($))
    // I controlli partono dopo l'avvio, per non rallentarlo, e poi tornano da soli.
    $.clock.after(5_000, () => void banchi($).catch(() => undefined))
    $.clock.after(20_000, () => void gws($).catch(() => undefined))
    $.clock.every(DIECI_MINUTI, () => void banchi($).catch(() => undefined))
    $.clock.every(SEI_ORE, () => void gws($).catch(() => undefined))
    return next(e)
  })

  // Ogni richiesta al modello della sessione principale rinnova la cache: un turno lungo la tiene calda.
  on('turn.step', async function* ($, e, next) {
    const risposta = yield* next(e)
    if (e.agentId === undefined) {
      const ora = await $.clock.now()
      await update($, cache, c => ({ ...c, ultimo: ora, fredda: false })).catch(() => undefined)
      await mostra($).catch(() => undefined)
    }
    return risposta
  })

  on('turn.complete', async ($, e, next) => {
    const r = await next(e)
    if (e.agentId === undefined) await rinnovata($)
    return r
  })
}
