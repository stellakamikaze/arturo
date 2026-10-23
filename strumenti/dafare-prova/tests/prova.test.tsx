import { expect, test } from 'claude-code/testing'

const PROPS = { title: 'Le tue cose da fare', isFocused: true, bodyColumns: 64, placement: 'dock' } as never

test('linguette, catena e lista', async $ => {
  const pane = await $.ui.mount({ plugin: 'dafare-prova', surface: 'terminal', component: 'Pane', requestId: 'dafare-prova', props: PROPS })
  expect(await pane.find({ type: 'Text', text: '4 progetti · 25 aperte · 8 fatte · 2 scadute · 2 ferme' })).toBeTruthy()
  expect(await pane.find({ key: 'catena' })).toBeFalsy()
  await pane.press({ key: 'apri-Sito nuovo' })
  expect(await pane.find({ type: 'Text', text: 'Da qui: #5 Mandare il logo in vettoriale, sblocca #11' })).toBeTruthy()
  expect(await pane.find({ type: 'Text', text: 'TOCCA A TE' })).toBeTruthy()
  expect(await pane.find({ type: 'Text', text: 'aspetta #4' })).toBeTruthy()
  await pane.press({ key: 'catena' })
  expect(await pane.find({ type: 'Text', text: 'TOCCA A TE' })).toBeFalsy()
  expect(await pane.find({ type: 'Text', text: '│  └─ ' })).toBeTruthy()
  expect(await pane.find({ key: 'lista' })).toBeFalsy()
  await pane.press({ key: 'tab-Podcast' })
  expect(await pane.find({ type: 'Text', text: 'Da qui: #20 Registrare la puntata 3, sblocca #21' })).toBeTruthy()
  await pane.press({ key: 'sel-20' })
  await pane.press({ key: 'fatto' })
  expect(await pane.find({ type: 'Text', text: 'Fatto: #20 Registrare la puntata 3.' })).toBeTruthy()
  expect(await pane.find({ type: 'Text', text: 'Da qui: #25 Invitare' })).toBeTruthy()
})
