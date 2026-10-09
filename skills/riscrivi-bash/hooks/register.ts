import type { Register } from 'claude-code'

import { riscrivi } from './riscrivi'

const BIN_TIMEOUT = ['/opt/homebrew/bin/timeout', '/usr/local/bin/timeout', '/usr/bin/timeout', '/bin/timeout']

export const register: Register = on => {
  let zsh = false
  let haTimeout = true

  on('session.start', async ($, e, next) => {
    zsh = ((await $.env.get('SHELL')) ?? '').endsWith('/zsh')
    // Su Windows Git Bash ha /usr/bin/timeout, ma $.fs.stat risolve quei path su C:\ e non lo
    // trova: lì il mod non tocca i timeout (3/10/2026).
    const windows = (await $.env.get('OS')) === 'Windows_NT'
    const trovati = await Promise.all(BIN_TIMEOUT.map(p => $.fs.stat(p).then(() => true, () => false)))
    haTimeout = windows || trovati.some(Boolean)
    return next(e)
  })

  on('tool.call', { tool: 'Bash' }, ($, e, next) => {
    const r = riscrivi(e.command, { zsh, haTimeout, timeoutMs: e.timeout, background: e.run_in_background })
    if (r.fatti.length === 0) return next(e)
    $.ui.toast(`riscritto: ${r.fatti.join(', ')}`)
    return next({ ...e, command: r.command, ...(r.timeoutMs === undefined ? {} : { timeout: r.timeoutMs }) })
  })
}
