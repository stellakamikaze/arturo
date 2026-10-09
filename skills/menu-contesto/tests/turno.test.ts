import { expect, test } from 'claude-code/testing'

import { righeLeggibili, servePannello, testoDelTurno } from '../hooks/turno'
import type { Msg } from '../hooks/turno'

const STORIA: Msg[] = [
  { role: 'user', text: 'prompt vecchio' },
  { role: 'assistant', text: 'risposta vecchia' },
  { role: 'user', text: 'fai il lavoro' },
  { role: 'assistant', text: 'Primo blocco.' },
  { role: 'user', text: '', toolResults: [{}] },
  { role: 'assistant', text: '**Risultati**\n1. uno\n2. due' },
  { role: 'user', text: '<system-reminder>x</system-reminder>' },
  { role: 'assistant', text: '' },
]

test('prende solo il testo del turno in corso', () => {
  expect(testoDelTurno(STORIA)).toBe('Primo blocco.\n\n**Risultati**\n1. uno\n2. due')
})

test('pannello solo oltre due righe', () => {
  expect(servePannello('una riga')).toBe(false)
  expect(servePannello('a\n\nb')).toBe(false)
  expect(servePannello('a\nb\nc')).toBe(true)
})

test('righe leggibili: tolti grassetto, codice e titoli, righe vuote tenute', () => {
  expect(righeLeggibili('**Titolo**\n\n1. usa `gws` qui\n## Sezione')).toEqual(['Titolo', '', '1. usa gws qui', 'Sezione'])
})
