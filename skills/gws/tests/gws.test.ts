import { describe, expect, test } from 'claude-code/testing'

import { account, correggiSintassi, guasto, nota } from '../hooks/gws'

describe('guasto di credenziali', () => {
  test('riconosce le tre forme', () => {
    expect(guasto('{"error":{"code":401,"message":"Access denied. No credentials provided"}}')).toBe('No credentials provided')
    expect(guasto('error: invalid_grant: Token has been expired or revoked.')).toBe('invalid_grant')
    expect(guasto('credentials.enc undecryptable')).toBe('undecryptable')
  })
  test('un 403 di scope o un esito buono non sono un guasto di credenziali', () => {
    expect(guasto('"code": 403, "message": "Request had insufficient authentication scopes."')).toBeNull()
    expect(guasto('{"emailAddress": "persona@example.org"}')).toBeNull()
  })
})

describe('account', () => {
  test('dalla cartella scritta nel comando', () => {
    expect(account('GOOGLE_WORKSPACE_CLI_CONFIG_DIR=~/.config/gws-lavoro gws drive files list', undefined)).toEqual({ nome: 'gws-lavoro', dir: '~/.config/gws-lavoro' })
    expect(account('GOOGLE_WORKSPACE_CLI_CONFIG_DIR="$HOME/.config/gws-personale" gws gmail users getProfile', undefined).nome).toBe('gws-personale')
  })
  test('poi dalla sessione, poi la cartella di default di gws', () => {
    expect(account('gws drive files list', '/home/anna/.config/gws-lavoro/').nome).toBe('gws-lavoro')
    expect(account('gws drive files list', undefined)).toEqual({ nome: 'gws', dir: '~/.config/gws' })
  })
  test('nota: niente altri account, serve il login della persona', () => {
    const n = nota({ nome: 'gws-lavoro', dir: '~/.config/gws-lavoro' })
    expect(n).toContain('gws-lavoro')
    expect(n).toContain('GOOGLE_WORKSPACE_CLI_CONFIG_DIR=~/.config/gws-lavoro gws auth login')
    expect(n).toContain('docs/onboarding/gws.md')
  })
})

describe('sintassi', () => {
  test('gws gmail messages diventa gws gmail users messages', () => {
    expect(correggiSintassi("gws gmail messages list --params '{\"userId\":\"me\"}'")).toBe("gws gmail users messages list --params '{\"userId\":\"me\"}'")
    expect(correggiSintassi('X=1 gws gmail threads get')).toBe('X=1 gws gmail users threads get')
  })
  test('la forma giusta, gli helper e il testo citato restano', () => {
    for (const c of ['gws gmail users messages list', 'gws gmail +read --id X', 'echo "gws gmail messages"', 'gws drive files list']) {
      expect(correggiSintassi(c)).toBe(c)
    }
  })
})
