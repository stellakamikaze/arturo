import { expect, test } from 'claude-code/testing'

test('il pannello si disegna su terminale e desktop', async $ => {
  for (const surface of ['terminal', 'desktop'] as const) {
    const ui = await $.ui.mount({ plugin: 'menu-contesto', surface, component: 'Pane', requestId: 'menu-contesto', props: { bodyColumns: 80, placement: 'dock' } as never } as never)
    const t = (await ui.findAll({ type: 'Text' })).map(x => x.text).join('|')
    expect(t).toContain('PRIMA DELLA DOMANDA')
  }
})
