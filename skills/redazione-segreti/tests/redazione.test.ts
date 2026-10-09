import { describe, expect, test } from 'claude-code/testing'

import { redigi } from '../hooks/register'

// Token finti, costruiti a pezzi: nessun valore vero nel sorgente.
const FINTI: ReadonlyArray<readonly [string, string]> = [
  ['anthropic-key', 'sk-ant-' + 'api03-' + 'A'.repeat(30)],
  ['github-token', 'ghp_' + 'b'.repeat(36)],
  ['aws-key', 'AKIA' + 'C'.repeat(16)],
  ['slack-token', 'xoxb-' + '1'.repeat(12)],
  ['jwt', 'eyJ' + 'd'.repeat(22) + '.eyJ' + 'e'.repeat(22) + '.' + 'f'.repeat(22)],
  ['google-api-key', 'AIza' + 'g'.repeat(35)],
  ['supabase-key', 'supabase_anon=' + 'eyJ' + 'h'.repeat(30)],
]

describe('redigi', () => {
  for (const [tipo, token] of FINTI) {
    test(`toglie il valore e lascia la forma: ${tipo}`, async () => {
      const { text, count } = await redigi(`prima ${token} dopo`)
      expect(text.includes(token)).toBe(false)
      expect(text).toContain(`[REDATTO:${tipo} len=${token.length} sha256=`)
      expect(text.startsWith('prima ')).toBe(true)
      expect(count).toBeGreaterThan(0)
    })
  }

  test('stringa di connessione: password via, utente e host restano', async () => {
    const pw = 'Zq' + 'x'.repeat(14)
    const { text } = await redigi(`postgres://utente:${pw}@db.example:5432/db`)
    expect(text.includes(pw)).toBe(false)
    expect(text).toContain('postgres://utente:[REDATTO:db-password len=16')
    expect(text).toContain('@db.example:5432/db')
  })

  test('stringa di connessione con password interpolata: è codice, passa intatta', async () => {
    for (const pw of ['${pw}', '$DB_PASSWORD', '%s', '{password}']) {
      const src = `postgres://utente:${pw}@db.example:5432/db`
      const { text, count } = await redigi(src)
      expect(text).toBe(src)
      expect(count).toBe(0)
    }
  })

  test('testo normale passa intatto', async () => {
    const plain = 'git status: 3 file modificati, nessun segreto qui'
    const { text, count } = await redigi(plain)
    expect(text).toBe(plain)
    expect(count).toBe(0)
  })

  test('stesso valore, stesso hash: si confrontano due segreti senza vederli', async () => {
    const t = 'ghp_' + 'z'.repeat(36)
    const a = (await redigi(t)).text
    const b = (await redigi(`x ${t}`)).text
    expect(b.endsWith(a)).toBe(true)
  })
})
