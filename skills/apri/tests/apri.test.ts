import { describe, expect, test } from 'claude-code/testing'

import { comando, estrai, scegli, sistemaDa } from '../hooks/apri'

describe('link e file nelle risposte', () => {
  test('prende URL e percorsi locali, in ordine, senza doppioni', () => {
    const t = 'Fatto: [il doc](https://example.org/doc/abc) e `~/Documenti/deck/v3.key`.\nPDF in /home/anna/export/v3.pdf, di nuovo https://example.org/doc/abc.'
    expect(estrai(t)).toEqual(['https://example.org/doc/abc', '~/Documenti/deck/v3.key', '/home/anna/export/v3.pdf'])
  })
  test('prende un percorso di Windows', () => {
    expect(estrai('Salvato in C:\\Lavoro\\report.pdf.')).toEqual(['C:\\Lavoro\\report.pdf'])
  })
  test('toglie la punteggiatura finale e ignora i percorsi di sistema', () => {
    expect(estrai('Vedi https://x.it/a?b=1). Poi /usr/bin/python3 e /tmp/x.')).toEqual(['https://x.it/a?b=1'])
  })
})

describe('quale aprire', () => {
  const risposte = [
    { role: 'assistant', text: 'vecchio https://a.it' },
    { role: 'user', text: 'https://scritto-dalla-persona.it' },
    { role: 'assistant', text: 'nuovo https://b.it e https://c.it' },
    { role: 'assistant', text: 'niente link qui' },
  ]
  test("senza argomento: l'ultimo dell'ultima risposta che ne ha", () => {
    expect(scegli(risposte, '')).toEqual({ voce: 'https://c.it', lista: ['https://c.it', 'https://b.it', 'https://a.it'] })
  })
  test('un numero sceglie dalla lista, una parola filtra', () => {
    expect(scegli(risposte, '3').voce).toBe('https://a.it')
    expect(scegli(risposte, 'b.it').voce).toBe('https://b.it')
    expect(scegli(risposte, '9').voce).toBeNull()
  })
  test('i link scritti dalla persona non contano', () => {
    expect(scegli(risposte, '').lista).not.toContain('https://scritto-dalla-persona.it')
  })
})

describe('come si apre: il programma predefinito del sistema', () => {
  test('Mac: open, senza scegliere il browser', () => {
    expect(comando('https://b.it', '/home/anna', 'mac')).toEqual(['open', 'https://b.it'])
    expect(comando('~/deck/v3.key', '/home/anna', 'mac')).toEqual(['open', '/home/anna/deck/v3.key'])
  })
  test('Linux: xdg-open', () => {
    expect(comando('https://b.it', '/home/anna', 'linux')).toEqual(['xdg-open', 'https://b.it'])
  })
  test('Windows: start, con & protetto per cmd', () => {
    expect(comando('https://b.it/?x=1&y=2', 'C:\\Anna', 'windows')).toEqual(['cmd', '/c', 'start', '', 'https://b.it/?x=1^&y=2'])
    expect(comando('~\\report.pdf', 'C:\\Anna', 'windows')).toEqual(['cmd', '/c', 'start', '', 'C:\\Anna\\report.pdf'])
  })
  test('il sistema dalla variabile OS e da uname', () => {
    expect(sistemaDa('Windows_NT', undefined)).toBe('windows')
    expect(sistemaDa(undefined, 'Darwin\n')).toBe('mac')
    expect(sistemaDa(undefined, 'Linux\n')).toBe('linux')
    expect(sistemaDa(undefined, undefined)).toBe('linux')
  })
})
