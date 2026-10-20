import type { Register } from 'claude-code'

import { account, correggiSintassi, guasto, nota } from './gws'

// gws in posizione di comando: "echo gws …" o un grep non contano.
const GWS = /(?:^|[;&|\n(])\s*(?:[A-Za-z_]+=\S+\s+)*gws\s/

export const register: Register = on => {
  on('tool.call', { tool: 'Bash' }, async ($, e, next) => {
    if (!GWS.test(e.command)) return next(e)
    const command = correggiSintassi(e.command)
    if (command !== e.command) $.ui.toast('gws: aggiunto "users" dopo "gmail"')
    const esito = await next({ ...e, command })
    if (esito.deny !== undefined) return esito

    const out = esito.result as { stdout?: string; stderr?: string } | undefined
    const g = guasto(`${out?.stdout ?? ''}\n${out?.stderr ?? ''}`)
    if (g === null || out === undefined) return esito

    const acc = account(command, await $.env.get('GOOGLE_WORKSPACE_CLI_CONFIG_DIR'))
    $.ui.toast(`gws: ${acc.nome} senza credenziali (${g}), serve il login`)
    return { ...esito, result: { ...out, stdout: `${out.stdout ?? ''}${nota(acc)}` } }
  })
}
