import { describe, expect, test } from 'claude-code/testing'

import { redigi } from '../hooks/redazione-segreti/register'

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
      // supabase-key redige solo il valore: il nome della chiave resta (finding 70)
      const valore = tipo === 'supabase-key' ? token.slice(token.indexOf('=') + 1) : token
      expect(text).toContain(`[REDATTO:${tipo} len=${valore.length} sha256=`)
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

  // Review del 7/11/2026, lotto L6.
  const V = 'Ab' + 'c'.repeat(36) // 38 caratteri, finto

  test('finding 60: la chiave tra virgolette del JSON non salva il valore', async () => {
    for (const src of [`{"password":"${V}"}`, `{"token": "${V}"}`, `{"api_key": "${V}"}`, `{"apiKey":"${V}"}`,
      `{"client_secret":"${V}"}`, `headers["token"] = "${V}"`, `{"vercel_token": "${V}"}`]) {
      const { text, count } = await redigi(src)
      expect(text.includes(V)).toBe(false)
      expect(count).toBeGreaterThan(0)
    }
  })

  test('finding 70: resta il nome della chiave, e lo stesso valore dà la stessa sigla in ogni forma', async () => {
    const a = (await redigi(`token: ${V}`)).text
    const b = (await redigi(`API_TOKEN=${V}`)).text
    const c = (await redigi(`{"token": "${V}"}`)).text
    expect(a.startsWith('token: [REDATTO:generic-secret len=38 sha256=')).toBe(true)
    expect(b.startsWith('API_TOKEN=[REDATTO:generic-secret len=38 sha256=')).toBe(true)
    const sigla = (t: string) => t.match(/\[REDATTO:[^\]]+\]/)?.[0]
    expect(sigla(a)).toBe(sigla(b))
    expect(sigla(c)).toBe(sigla(a))
  })

  test('finding 70: un percorso dopo token: non è un segreto', async () => {
    for (const src of ['token: /opt/progetto/documenti/sorgenti/componenti/app.js',
      'token: ./sorgenti/componenti/pagine/progetto/app.js']) {
      const { text, count } = await redigi(src)
      expect(text).toBe(src)
      expect(count).toBe(0)
    }
  })

  test('finding 66: redis senza utente, rediss, amqp, https con utente e password', async () => {
    const pw = 'Sup3r' + 'Segreta9'
    for (const [src, resta] of [
      [`redis://:${pw}@cache.example:6379/0`, '@cache.example:6379/0'],
      [`rediss://default:${pw}@cache.example:6380`, 'rediss://default:'],
      [`amqp://u:${pw}@coda.example/vh`, 'amqp://u:'],
      [`https://u:${pw}@git.example/r.git`, '@git.example/r.git'],
    ] as const) {
      const { text, count } = await redigi(src)
      expect(text.includes(pw)).toBe(false)
      expect(text).toContain(resta)
      expect(count).toBe(1)
    }
  })

  test('finding 66: una @ dentro la password non lascia fuori il resto', async () => {
    const { text } = await redigi('mysql://root:' + 'ab' + '@123xyz@db.example/app')
    expect(text.includes('123xyz')).toBe(false)
    expect(text).toContain('mysql://root:[REDATTO:db-password len=9 ')
    expect(text).toContain('@db.example/app')
  })

  test('finding 66: la stringa di connessione dentro un JSON si ferma alla virgoletta', async () => {
    const pw = 'Sup3r' + 'Segreta9'
    const src = `{"url":"redis://:${pw}@cache.example","mail":"a@b.example"}`
    const { text } = await redigi(src)
    expect(text.includes(pw)).toBe(false)
    expect(text).toContain('@cache.example","mail":"a@b.example"}')
  })

  test('finding 67: chiave privata cifrata, chiave PGP e Authorization Bearer', async () => {
    const corpo = 'MII' + 'Q'.repeat(40)
    for (const tipo of ['ENCRYPTED PRIVATE KEY', 'PGP PRIVATE KEY BLOCK']) {
      const { text } = await redigi(`prima\n-----BEGIN ${tipo}-----\n${corpo}\n-----END ${tipo}-----\ndopo`)
      expect(text.includes(corpo)).toBe(false)
      expect(text).toContain('[REDATTO:private-key')
      expect(text.endsWith('\ndopo')).toBe(true)
    }
    const { text } = await redigi(`> Authorization: Bearer ${V}\n`)
    expect(text.includes(V)).toBe(false)
    expect(text).toContain('Authorization: Bearer [REDATTO:bearer-token len=38 ')
  })
})
