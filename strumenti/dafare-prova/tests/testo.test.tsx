import { expect, test } from 'claude-code/testing'
const RUN = { presentation: { isFullscreen: false, columns: 120 }, origin: { kind: 'composer' } }
test('testo: tutti, catena, fatto', async $ => {
  const tutti = await $.command.run({ command: 'dafare-prova', args: 'testo', ...RUN } as never) as { text: string }
  expect(tutti.text).toContain('da qui: #20 Registrare la puntata 3')
  const cat = await $.command.run({ command: 'dafare-prova', args: 'catena sito', ...RUN } as never) as { text: string }
  expect(cat.text).toContain('│  └─ Pubblicare la beta')
  const f = await $.command.run({ command: 'dafare-prova', args: 'fatto 20', ...RUN } as never) as { text: string }
  expect(f.text).toContain('Fatto: #20')
  expect(f.text).toContain('Da qui: #25')
})
