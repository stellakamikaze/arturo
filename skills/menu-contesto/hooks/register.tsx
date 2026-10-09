import { atom, read, update } from 'claude-code'
import type { Register } from 'claude-code'

import { righeLeggibili, servePannello, testoDelTurno } from './turno'

// Prove del 2/10: riscrivere la domanda del dialogo la svuota, e un pannello coi colori di default
// col tema chiaro resta scuro su scuro. Il pannello porta il suo fondo e colori espliciti.
const PANE = 'menu-contesto'
const C = { fondo: '#faf8f2', testo: '#1c1c1c', titolo: '#1f4fbf' }
const testo = atom({ plugin: 'menu-contesto', key: 'testo' } as const, '')

export const register: Register = on => {
  on('tool.call', { tool: 'AskUserQuestion' }, async ($, e, next) => {
    // Una domanda posta da un plugin ($.ui.ask) porta un id toolu_plugin_: niente contesto.
    if (e.tool_use_id === undefined || e.tool_use_id.startsWith('toolu_plugin_') || e.agentId !== undefined) return next(e)
    const t = testoDelTurno(await $.session.messages())
    if (!servePannello(t)) return next(e)
    await update($, testo, () => t)
    const aperto = await $.ui.open({ id: PANE, title: 'Contesto della domanda', rows: Math.min(30, t.split('\n').length + 4), columns: 90 })
    if (!aperto.isPlaced) $.ui.toast('Allarga il terminale per vedere il contesto della domanda')
    try {
      return await next(e)
    } finally {
      await $.ui.close({ id: PANE }).catch(() => undefined)
    }
  })

  on('ui.render', { component: 'Pane', requestId: PANE }, async ($, e) => {
    const { Box, Text } = $.ui.resolve(e)
    const t = await read($, testo)
    return (
      <Box flexDirection="column" backgroundColor={C.fondo} paddingX={2} paddingY={1} flexGrow={1}>
        <Text bold color={C.titolo}>PRIMA DELLA DOMANDA</Text>
        {righeLeggibili(t).map(r => (
          <Text color={C.testo} wrap="wrap">{r === '' ? ' ' : r}</Text>
        ))}
      </Box>
    )
  })
}
