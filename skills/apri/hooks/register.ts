import type { EngineInterface, Register } from 'claude-code'

import { comando, scegli, sistemaDa } from './apri'

async function sistema($: EngineInterface) {
  const os = await $.env.get('OS')
  if (os === 'Windows_NT') return sistemaDa(os, undefined)
  const u = await $.process.run(['uname', '-s'], { timeoutMs: 5_000 }).catch(() => undefined)
  return sistemaDa(os, u?.exitCode === 0 ? u.stdout : undefined)
}

export const register: Register = on => {
  on('session.start', async ($, e, next) => {
    await $.command.register({
      name: 'apri',
      description: "Apre l'ultimo link o file citato nelle risposte, con il programma predefinito",
      argumentHint: '[numero | parola | lista]',
      immediate: true,
    })
    return next(e)
  })

  on('command.run', { command: 'apri' }, async ($, e) => {
    const args = String((e as unknown as { args?: unknown }).args ?? '').trim()
    const messaggi = (await $.session.messages()) as unknown as { role: string; text?: string }[]
    const { voce, lista } = scegli(messaggi, args === 'lista' ? '' : args)
    if (args === 'lista' || voce === null) {
      if (lista.length === 0) return { text: 'Nelle risposte non ci sono link né file da aprire.' }
      const righe = lista.slice(0, 10).map((v, i) => `${i + 1}. ${v}`).join('\n')
      const premessa = voce === null && args !== 'lista' ? `Niente che corrisponda a "${args}". ` : ''
      return { text: `${premessa}Da aprire con /apri <numero>:\n${righe}` }
    }
    const home = (await $.env.get('HOME')) ?? (await $.env.get('USERPROFILE')) ?? ''
    const argv = comando(voce, home, await sistema($))
    const r = await $.process.run(argv, { timeoutMs: 15_000 }).catch((err: unknown) => ({ exitCode: 1, stdout: '', stderr: String(err) }))
    if (r.exitCode !== 0) return { text: `Non si apre: ${voce} (${r.stderr.trim().split('\n')[0] || 'errore'})` }
    $.ui.toast(`Aperto: ${voce.length > 60 ? `${voce.slice(0, 57)}…` : voce}`)
    return {}
  })
}
