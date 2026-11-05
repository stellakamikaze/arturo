import { describe, expect, mock, test } from 'claude-code/testing'

import {
  FOTOGRAMMI_STELLA, FOTOGRAMMI_TOTALI, INTERVALLO_INVITO_S, blocco, dataRoadmap, decidiInvito, dettaglio, leggiAggiornamento, leggiDeriva, leggiTimbro,
  nomeVersione, nuovoTimbro, parolaDeriva, parolaInvito, parolaVersione, riga, statoChiaro, versioneArturo,
} from '../hooks/testata/testata'
import type { Deriva, Testata } from '../types'

const pulita: Deriva = { misurata: true, file: [], guardie: [], hook: [], config: [] }

describe('versione di Arturo', () => {
  test('rilascio, commit dopo il rilascio, nessun tag', () => {
    expect(versioneArturo('v0.2.0\n')).toBe('v0.2.0')
    expect(versioneArturo('v0.2.0-8-gabc1234')).toBe('v0.2.0 +8')
    expect(versioneArturo('v0.10.12')).toBe('v0.10.12')
    expect(versioneArturo('v2026-11-03-2-gabc1234')).toBe('v2026-11-03 +2')
    expect(versioneArturo('v2026-10-12.2')).toBe('v2026-10-12.2')
    expect(versioneArturo('fatal: No names found')).toBeNull()
  })
  test('il nome che si legge', () => {
    expect(nomeVersione('v0.2.0')).toBe('0.2.0')
    expect(nomeVersione('v0.2.0 +8')).toBe('0.2.0, con 8 modifiche non ancora rilasciate')
    expect(nomeVersione('v0.2.0 +1')).toBe('0.2.0, con 1 modifica non ancora rilasciata')
    expect(nomeVersione('v2026-11-03')).toBe('v2026-11-03')
  })
  test('la versione nella riga di stato', () => {
    expect(parolaVersione('v0.2.0')).toBeNull()
    expect(parolaVersione('v0.2.0 +8')).toBe('8 modifiche non ancora rilasciate')
    expect(parolaVersione('v2026-11-03')).toBe('aggiornato il 3 novembre 2026')
    expect(parolaVersione(null)).toBeNull()
  })
})

describe('deriva', () => {
  test('quella che conta per prima', () => {
    expect(parolaDeriva(pulita)).toBe('deriva: nessuna')
    expect(parolaDeriva({ ...pulita, file: ['a', 'b', 'c'] })).toBe('deriva: 3 file di Arturo cambiati')
    expect(parolaDeriva({ ...pulita, file: ['hooks/x-guard.py'], guardie: ['hooks/x-guard.py'] })).toBe('deriva: 1 guardia cambiata')
    expect(parolaDeriva({ ...pulita, hook: ['tutti'], file: ['a'] })).toBe('deriva: hook spenti')
    expect(parolaDeriva({ ...pulita, misurata: false })).toBeNull()
    expect(parolaDeriva(null)).toBeNull()
  })
  test('il file della deriva: forma giusta, rotta, caratteri di controllo', () => {
    expect(leggiDeriva('{"misurata": true, "file": ["a\\u001b[31m"], "guardie": [], "hook": [], "config": []}')?.file).toEqual(['a[31m'])
    expect(leggiDeriva('non json')).toBeNull()
    expect(leggiDeriva('{"file": []}')).toBeNull()
  })
})

describe('la riga di /versione', () => {
  const t: Testata = { arturo: 'v0.2.0', claude: '2.1.317', deriva: pulita, aggiornamento: null }
  test('versioni e deriva in una riga', () => {
    expect(riga(t)).toBe('Arturo 0.2.0 · Claude Code 2.1.317 · deriva: nessuna')
  })
  test('aggiornamento pronto o fermo', () => {
    expect(riga({ ...t, aggiornamento: leggiAggiornamento('{"stato": "pronto", "versione": "v0.3.0"}') })).toContain('↑ 0.3.0 si installa alla chiusura')
    expect(riga({ ...t, aggiornamento: leggiAggiornamento('{"stato": "manuale", "versione": "v0.3.0"}') })).toContain('↑ 0.3.0: serve /aggiorna')
    expect(riga({ ...t, aggiornamento: leggiAggiornamento('{"stato": "aggiornato", "versione": "v0.2.0"}') })).toBe(riga(t))
  })
  test('senza dati resta il nome, mai una riga vuota', () => {
    expect(riga({ arturo: null, claude: null, deriva: null, aggiornamento: null })).toBe('Arturo')
  })
  test('/versione dice i file dietro la deriva', () => {
    expect(dettaglio({ ...t, deriva: { ...pulita, file: ['bin/x.py'] } })).toContain('file di Arturo cambiati: bin/x.py')
  })
})

describe('il blocco gemello', () => {
  const t: Testata = { arturo: 'v0.2.0', claude: '2.1.317', deriva: pulita, aggiornamento: null }
  test('versione e stato in parole', () => {
    expect(blocco(t, null)).toEqual({ versione: '0.2.0', stato: 'configurazione in ordine', roadmap: 'Roadmap', roadmapNuova: false })
    expect(blocco({ ...t, arturo: 'v0.2.0 +8', deriva: null }, null)).toMatchObject({ versione: '0.2.0', stato: '8 modifiche non ancora rilasciate' })
    expect(blocco({ ...t, arturo: 'v2026-11-03' }, null)).toMatchObject({ versione: 'v2026-11-03', stato: 'aggiornato il 3 novembre 2026 \u00b7 configurazione in ordine' })
    expect(blocco({ arturo: null, claude: null, deriva: null, aggiornamento: null }, null).stato).toBeNull()
  })
  test('lo stato dice cosa fare, senza gergo', () => {
    expect(statoChiaro({ ...t, deriva: { ...pulita, file: ['a', 'b', 'c'] } })).toBe('hai cambiato 3 file di Arturo: /versione li elenca')
    expect(statoChiaro({ ...t, deriva: { ...pulita, file: ['g'], guardie: ['g'] } })).toBe('hai cambiato una guardia di Arturo: /versione le elenca')
    expect(statoChiaro({ ...t, deriva: { ...pulita, hook: ['tutti'] } })).toBe('i controlli di Arturo sono spenti: scrivi /diagnosi')
    expect(statoChiaro({ ...t, aggiornamento: leggiAggiornamento('{"stato": "pronto", "versione": "v0.3.0"}') })).toBe('la versione 0.3.0 si installa quando chiudi la sessione')
    expect(statoChiaro({ ...t, aggiornamento: leggiAggiornamento('{"stato": "manuale", "versione": "v0.3.0"}') })).toBe("c'è la versione 0.3.0: scrivi /aggiorna")
    expect(statoChiaro({ ...t, aggiornamento: leggiAggiornamento('{"stato": "pronto", "versione": "v2026-11-04"}') })).toBe('la versione del 4 novembre 2026 si installa quando chiudi la sessione')
    expect(statoChiaro({ ...t, deriva: null })).toBeNull()
    expect(statoChiaro(t)).not.toContain('misurat')
  })
  test('la stella in pixel: tre righe larghe uguali, si ferma grande', () => {
    for (const f of FOTOGRAMMI_STELLA) {
      expect(f.map(r => [...r].length)).toEqual([8, 9, 8])
    }
    expect(FOTOGRAMMI_STELLA[0]).toEqual(FOTOGRAMMI_STELLA[FOTOGRAMMI_TOTALI % FOTOGRAMMI_STELLA.length])
  })
})

describe("l'invito alla roadmap", () => {
  const giorno = 24 * 60 * 60
  test('la data in testa a ROADMAP.md', () => {
    expect(dataRoadmap('# La strada di Arturo\n\nAggiornata il 2026-11-03\n')).toBe('2026-11-03')
    expect(dataRoadmap('# niente data')).toBeNull()
  })
  test('roadmap nuova, promemoria dopo due settimane, silenzio prima', () => {
    expect(decidiInvito('2026-11-03', null, 1_000)).toBe('nuova')
    expect(decidiInvito('2026-11-03', { data: '2026-10-20', mostrata: 900 }, 1_000)).toBe('nuova')
    expect(decidiInvito('2026-11-03', { data: '2026-11-03', mostrata: 1_000 }, 1_000 + 13 * giorno)).toBeNull()
    expect(decidiInvito('2026-11-03', { data: '2026-11-03', mostrata: 1_000 }, 1_000 + INTERVALLO_INVITO_S)).toBe('promemoria')
  })
  test('spento, o senza roadmap: niente invito', () => {
    expect(decidiInvito('2026-11-03', { pausa: 'sempre' }, 1_000)).toBeNull()
    expect(decidiInvito(null, null, 1_000)).toBeNull()
  })
  test('il timbro: forma rotta, pausa che resta', () => {
    expect(leggiTimbro('non json')).toBeNull()
    expect(leggiTimbro('{"data": 3, "mostrata": "x"}')).toEqual({ data: undefined, mostrata: undefined, pausa: undefined })
    expect(JSON.parse(nuovoTimbro({ pausa: 'sempre' }, '2026-11-03', 12.7))).toEqual({ pausa: 'sempre', data: '2026-11-03', mostrata: 12 })
  })
  test('le parole', () => {
    expect(parolaInvito({ tipo: 'nuova', data: '2026-11-03' })).toBe('Roadmap aggiornata il 3/11')
    expect(parolaInvito({ tipo: 'promemoria', data: '2026-11-03' })).toBe('Roadmap: dimmi cosa ne pensi')
    expect(parolaInvito(null)).toBe('Roadmap')
  })
})

type Registra = Parameters<Extract<Parameters<typeof test>[1], (...a: never[]) => unknown>>[1]

function finto(on: Registra, file: Record<string, string>, scritti: Record<string, string>, posti: string[]) {
  // Il mod arturo ha sei parti: qui si prova solo questa (ARTURO_PARTI, hooks/parti.ts).
  on('env.get', { name: 'ARTURO_PARTI' }, () => ({ value: 'testata' }))
  mock.env(on, { HOME: '/casa' })
  // Su Windows i percorsi arrivano con la barra rovesciata e il disco: lettura e scrittura si
  // normalizzano allo stesso modo (5/11/2026, #4790).
  const normale = (p: string) => p.replace(/\\/g, '/').replace(/^[A-Za-z]:/, '')
  on('fs.read', ($, e) => {
    const percorso = normale(e.path)
    if (percorso.endsWith('/ROADMAP.md')) return { value: 'Aggiornata il 2026-11-03\n' }
    const t = file[percorso]
    if (t === undefined) throw new Error(`ENOENT ${e.path}`)
    return { value: t }
  })
  on('fs.write', ($, e) => {
    scritti[normale(e.path)] = e.text
    return { value: undefined }
  })
  on('process.run', ($, e) => ({ value: { exitCode: e.argv.includes('describe') ? 0 : 1, stdout: 'v0.2.0-8-gc247fed\n', stderr: '', isStdoutTruncated: false, isStderrTruncated: false } }))
  on('session.version', () => ({ value: { version: '2.1.317', base: '2.1.317' } }))
  on('clock.now', () => ({ value: 1_000_000_000 }))
  on('ui.place', ($, e) => {
    posti.push(e.id)
    return { value: { id: e.id } } as never
  })
  on('command.register', async (_$, e) => ({ value: { command: e.name } }) as never)
  on('session.start', async (_$, e) => ({ cwd: e.cwd }))
}

const PIAZZATA = { plugin: 'arturo', component: 'Placed', requestId: 'testata', surface: 'terminal', props: { id: 'testata', plugin: 'arturo' } } as never

test("all'avvio il blocco va sotto l'intestazione, con versione, deriva e invito", async ($, on) => {
  const scritti: Record<string, string> = {}
  const posti: string[] = []
  finto(on, {
    '/casa/.claude/cache/deriva.json': '{"misurata": true, "file": ["a", "b", "c"], "guardie": [], "hook": [], "config": []}',
  }, scritti, posti)
  await $.session.start({ cwd: '/progetto', surface: 'terminal', isInteractive: true })
  expect(posti).toEqual(['testata'])
  expect(JSON.parse(scritti['/casa/.claude/session-env/roadmap-vista.json']!)).toEqual({ data: '2026-11-03', mostrata: 1_000_000 })
  const ui = await $.ui.mount(PIAZZATA)
  expect((await ui.find({ type: 'Text', text: /^ 0\./ }))?.text).toBe(' 0.2.0')
  expect((await ui.find({ type: 'Text', text: /file di Arturo/ }))?.text).toBe('8 modifiche non ancora rilasciate \u00b7 hai cambiato 3 file di Arturo: /versione li elenca')
  expect((await ui.find({ type: 'Text', text: /^Roadmap/ }))?.text).toBe('Roadmap aggiornata il 3/11')
  expect((await ui.find({ type: 'Text', text: /^Invia Arturo/ }))?.text).toBe('Invia Arturo a chi ne ha bisogno')
  await ui.unmount()
})

test("con l'invito già visto e la stessa roadmap, il link resta senza evidenza", async ($, on) => {
  const scritti: Record<string, string> = {}
  const posti: string[] = []
  finto(on, { '/casa/.claude/session-env/roadmap-vista.json': '{"data": "2026-11-03", "mostrata": 999000}' }, scritti, posti)
  await $.session.start({ cwd: '/progetto', surface: 'terminal', isInteractive: true })
  expect(Object.keys(scritti)).toEqual([])
  const ui = await $.ui.mount(PIAZZATA)
  expect((await ui.find({ type: 'Text', text: /^Roadmap/ }))?.text).toBe('Roadmap')
  await ui.unmount()
})
