import type { EngineInterface, Register } from 'claude-code'

import { riscrivi } from './riscrivi'

const BIN_TIMEOUT = ['/opt/homebrew/bin/timeout', '/usr/local/bin/timeout', '/usr/bin/timeout', '/bin/timeout']
const MARCATORE = 'arturo-zsh-come-bash'

// La riga di session-start.sh in $CLAUDE_ENV_FILE (~/.claude/session-env/<sessione>/sessionstart-hook-N.sh).
// Si cerca a ogni comando finché non c'è: l'avvio può finire dopo il session.start del mod. Senza la
// riga (Claude Code vecchio, avvio fallito) il mod riscrive come prima.
async function rigaNellaShell($: EngineInterface): Promise<boolean> {
  const sessione = await $.session.id().catch(() => '')
  const home = (await $.env.get('HOME')) ?? (await $.env.get('USERPROFILE')) ?? ''
  const conf = (await $.env.get('CLAUDE_CONFIG_DIR')) || `${home}/.claude`
  if (sessione === '' || conf === '/.claude') return false
  const cartella = `${conf}/session-env/${sessione}`
  const voci = await $.fs.list(cartella).catch(() => [])
  for (const v of voci) {
    if (v.kind !== 'file' || !v.name.startsWith('sessionstart-hook-')) continue
    const testo = await $.fs.read(`${cartella}/${v.name}`).catch(() => '')
    if (typeof testo === 'string' && testo.includes(MARCATORE)) return true
  }
  return false
}

export const register: Register = on => {
  let zsh = false
  let haTimeout = true
  let opzioniNellaShell = false

  on('session.start', async ($, e, next) => {
    zsh = ((await $.env.get('SHELL')) ?? '').endsWith('/zsh')
    // Su Windows Git Bash ha /usr/bin/timeout, ma $.fs.stat risolve quei path su C:\ e non lo
    // trova: lì il mod non tocca i timeout (3/10/2026).
    const windows = (await $.env.get('OS')) === 'Windows_NT'
    const trovati = await Promise.all(BIN_TIMEOUT.map(p => $.fs.stat(p).then(() => true, () => false)))
    haTimeout = windows || trovati.some(Boolean)
    return next(e)
  })

  on('tool.call', { tool: 'Bash' }, async ($, e, next) => {
    if (zsh && !opzioniNellaShell) opzioniNellaShell = await rigaNellaShell($).catch(() => false)
    const r = riscrivi(e.command, { zsh, haTimeout, timeoutMs: e.timeout, background: e.run_in_background, opzioniNellaShell })
    if (r.fatti.length === 0) return next(e)
    // setopt non cambia cosa fa il comando: niente toast, compare solo nel comando eseguito.
    const visibili = r.fatti.filter(f => !f.startsWith('setopt'))
    if (visibili.length > 0) $.ui.toast(`riscritto: ${visibili.join(', ')}`)
    return next({ ...e, command: r.command, ...(r.timeoutMs === undefined ? {} : { timeout: r.timeoutMs }) })
  })
}
