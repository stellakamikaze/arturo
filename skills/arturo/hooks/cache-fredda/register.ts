import { atom, read, update } from 'claude-code'
import type { EngineInterface, Register } from 'claude-code'

import { type Avanti, type Evento, parteSpenta, stato } from '../parti'
import { avvisi, cacheFredda, cartelleGws, SEGNALI_VUOTI, tokenBuono, ttlDa, VUOTA } from './cache'

// Gli avvisi stanno nella riga sotto il prompt (stato() di parti.ts, una riga per tutto il mod), accanto a quelli di Claude Code: non
// coprono la fascia di /dafare. Solo eccezioni: cache fredda e token gws in errore.
const cache = atom({ plugin: 'arturo', key: 'cache' } as const, VUOTA)
const segnali = atom({ plugin: 'arturo', key: 'segnali' } as const, SEGNALI_VUOTI)
const UN_MINUTO = 60_000
const SEI_ORE = 6 * 3_600_000

async function mostra($: EngineInterface): Promise<void> {
  stato($, 'cache-fredda', avvisi(await read($, cache), await read($, segnali)))
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

export async function avvio($: EngineInterface, e: Evento<'session.start'>, next: Avanti<'session.start'>) {
  if (await parteSpenta($, 'cache-fredda')) return next(e)
  $.clock.every(UN_MINUTO, () => void controlla($))
  // I controlli partono dopo l'avvio, per non rallentarlo, e poi tornano da soli.
  $.clock.after(20_000, () => void gws($).catch(() => undefined))
  $.clock.every(SEI_ORE, () => void gws($).catch(() => undefined))
  return next(e)
}

export async function fineTurno($: EngineInterface, e: Evento<'turn.complete'>, next: Avanti<'turn.complete'>) {
  if (await parteSpenta($, 'cache-fredda')) return next(e)
  const r = await next(e)
  if (e.agentId === undefined) await rinnovata($)
  return r
}

export const register: Register = on => {

  // Ogni richiesta al modello della sessione principale rinnova la cache: un turno lungo la tiene calda.
  on('turn.step', async function* ($, e, next) {
    if (await parteSpenta($, 'cache-fredda')) return yield* next(e)
    const risposta = yield* next(e)
    if (e.agentId === undefined) {
      const ora = await $.clock.now()
      await update($, cache, c => ({ ...c, ultimo: ora, fredda: false })).catch(() => undefined)
      await mostra($).catch(() => undefined)
    }
    return risposta
  })

}
