import { describe, expect, mock, test } from 'claude-code/testing'

import { dettaglio, leggiAggiornamento, leggiDeriva, nomeVersione, parolaDeriva, riga, versioneArturo } from '../hooks/testata'
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

describe('la riga', () => {
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

test("all'avvio la riga va sotto l'intestazione, con versione, Claude Code e deriva", async ($, on) => {
  mock.env(on, { HOME: '/casa' })
  const file: Record<string, string> = {
    '/casa/.claude/cache/deriva.json': '{"misurata": true, "file": ["a", "b", "c"], "guardie": [], "hook": [], "config": []}',
  }
  on('fs.read', ($, e) => {
    const t = file[e.path.replace(/\\/g, '/').replace(/^[A-Za-z]:/, '')]
    if (t === undefined) throw new Error(`ENOENT ${e.path}`)
    return { value: t }
  })
  on('process.run', ($, e) => ({ value: { exitCode: e.argv.includes('describe') ? 0 : 1, stdout: 'v0.2.0-8-gc247fed\n', stderr: '', isStdoutTruncated: false, isStderrTruncated: false } }))
  on('session.version', () => ({ value: { version: '2.1.317', base: '2.1.317' } }))
  const righe: string[] = []
  on('ui.log', ($, e) => {
    righe.push(e.text)
    return { value: undefined }
  })
  on('command.register', async (_$, e) => ({ value: { command: e.name } }) as never)
  on('session.start', async (_$, e) => ({ cwd: e.cwd }))
  await $.session.start({ cwd: '/progetto', surface: 'terminal', isInteractive: true })
  expect(righe).toEqual(['Arturo 0.2.0, con 8 modifiche non ancora rilasciate · Claude Code 2.1.317 · deriva: 3 file di Arturo cambiati'])
})
