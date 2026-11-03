// Arturo in pixel, accanto alla mascotte di Claude Code: una stella a quattro punte in blocchi arancio, con due
// stelle piccole blu dell'Orsa. La disegna il terminale stesso: pulsa col suo orologio per una ventina di
// secondi, poi resta grande e ferma. Nessun giro passa dal mod mentre brilla.
import type { ClientSurface } from 'claude-code'

import { FOTOGRAMMI_STELLA, FOTOGRAMMI_TOTALI, PASSO_MS, PUNTO } from './testata'

const ARANCIO = '#f2a24a'
const BLU = '#2b8cff'

export default function Stella(_props: unknown, surface: ClientSurface<number>) {
  if (surface.state === undefined) {
    let n = 0
    const ferma = surface.every(PASSO_MS, () => {
      n += 1
      if (n >= FOTOGRAMMI_TOTALI) {
        ferma()
        surface.setState(0)
        return
      }
      surface.setState(n)
    })
  }
  const { Box, Text } = surface.elements
  const [alta, mezzo, bassa] = FOTOGRAMMI_STELLA[(surface.state ?? 0) % FOTOGRAMMI_STELLA.length]!
  return (
    <Box flexDirection="column">
      <Text><Text color={ARANCIO}>{alta}</Text><Text color={BLU}>{PUNTO}</Text></Text>
      <Text color={ARANCIO}>{mezzo}</Text>
      <Text><Text color={BLU}>{PUNTO}</Text><Text color={ARANCIO}>{bassa}</Text></Text>
    </Box>
  )
}
