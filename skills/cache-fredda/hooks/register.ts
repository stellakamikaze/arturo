import { atom, read, update } from 'claude-code'
import type { EngineInterface, Register } from 'claude-code'

import { avviso, cacheFredda, ttlDa, VUOTA } from './cache'

// L'avviso sta nella riga sotto il prompt ($.ui.status), accanto agli avvisi di Claude Code: non
// copre la fascia di /dafare e sparisce alla prima risposta del modello.
const cache = atom({ plugin: 'cache-fredda', key: 'cache' } as const, VUOTA)
const UN_MINUTO = 60_000

async function controlla($: EngineInterface): Promise<void> {
  const c = await read($, cache)
  const fredda = cacheFredda(c, await $.clock.now())
  if (fredda === c.fredda) return
  const nuova = { ...c, fredda }
  await update($, cache, () => nuova)
  $.ui.status(avviso(nuova))
}

async function rinnovata($: EngineInterface): Promise<void> {
  const { context, rateLimits } = await $.session.usage()
  const ora = await $.clock.now()
  await update($, cache, () => ({ ultimo: ora, tokens: context.tokens ?? null, ttlMs: ttlDa(rateLimits), fredda: false }))
  $.ui.status(undefined)
}

export const register: Register = on => {
  on('session.start', async ($, e, next) => {
    $.clock.every(UN_MINUTO, () => void controlla($))
    return next(e)
  })

  // Ogni richiesta al modello della sessione principale rinnova la cache: un turno lungo la tiene calda.
  on('turn.step', async function* ($, e, next) {
    const risposta = yield* next(e)
    if (e.agentId === undefined) {
      const ora = await $.clock.now()
      await update($, cache, c => ({ ...c, ultimo: ora, fredda: false })).catch(() => undefined)
      $.ui.status(undefined)
    }
    return risposta
  })

  on('turn.complete', async ($, e, next) => {
    const r = await next(e)
    if (e.agentId === undefined) await rinnovata($)
    return r
  })
}
