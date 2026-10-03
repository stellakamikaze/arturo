// I test del pannello /dafare con il kit di Claude Code (`claude plugin test`).
// Ogni test comincia con il suo id (U20-U33): il banco tests/test_pannello.py (U03) confronta
// l'insieme degli id passati con il suo elenco, sulle due superfici.
//
// Sotto il pannello c'è una CLI finta: tiene un piccolo archivio in memoria, risponde a
// `todo --json` e ai verbi del pannello, e registra ogni argv.

import { expect, mock, test } from 'claude-code/testing'
import type { On } from 'claude-code'
import type { Engine } from 'claude-code/testing'

import type { TodoVoce, Vista } from '../types'

type Uscita = { exitCode: number; stdout: string; stderr: string }
type Opzioni = {
  python?: Record<string, 'ok' | 'rifiuta' | 'alias'>
  json?: () => string
  rompi?: (argomenti: string[]) => Uscita | null
}

const PANE = { title: 'Le tue cose da fare', isFocused: true, bodyColumns: 80, placement: 'inline' } as never
const BAND = { hasSurvey: false, isWorking: false, maxRows: 4, bodyColumns: 120 } as never
const BAND_SONDAGGIO = { hasSurvey: true, isWorking: false, maxRows: 4, bodyColumns: 120 } as never
const COMANDO = { presentation: { isFullscreen: false, columns: 120 }, origin: { kind: 'composer' } }

function voce(id: number, campi: Partial<TodoVoce> = {}): TodoVoce {
  return {
    id, titolo: `Cosa numero ${id}`, progetto: 'libro', scadenza: null, scadenza_testo: null, giorni: null,
    priorita: 'media', stato: 'da fare', quando: 'settimana', chi: 'tu', perche: null, motivo: null,
    gruppo: 'tu', dopo: [], attende: [], note: [], ...campi,
  }
}

const GRUPPI = [
  { tipo: 'tu', titolo: 'TOCCA A TE', descrizione: 'Lo fai tu.' },
  { tipo: 'decidi', titolo: 'DECIDI TU, POI FACCIO IO', descrizione: 'Serve una tua scelta, poi lavora Claude.' },
  { tipo: 'io', titolo: 'FACCIO IO', descrizione: 'Lo fa Claude.' },
  { tipo: 'fermo', titolo: 'FERMO', descrizione: 'Aspetta qualcosa o qualcuno.' },
] as const

function gruppoDi(t: TodoVoce): TodoVoce['gruppo'] {
  if (t.stato === 'fatto' || t.stato === 'scartato') return null
  return t.stato === 'fermo' ? 'fermo' : t.chi
}

// La CLI finta: un archivio in memoria che cambia con i verbi, come quella vera.
function motore(on: On, iniziali: TodoVoce[], opzioni: Opzioni = {}) {
  const archivio = iniziali.map(t => ({ ...t }))
  const python = opzioni.python ?? { python3: 'ok' }
  const chiamate: string[][] = []
  const toast: string[] = []
  const aperture: unknown[] = []
  let versione = 1
  let avvisi: string[] = []

  const vista = (): Vista => ({
    versione, oggi: '2026-10-03', progetto: null, chiusi: 0, avvisi,
    gruppi: GRUPPI.map(g => ({ ...g, todo: archivio.filter(t => gruppoDi(t) === g.tipo).map(t => ({ ...t, gruppo: gruppoDi(t) })) })),
  })

  const esegui = (a: string[]): Uscita => {
    const rotto = opzioni.rompi?.(a)
    if (rotto) return rotto
    if (a[0] === '--json') return { exitCode: 0, stdout: opzioni.json ? opzioni.json() : JSON.stringify(vista()), stderr: '' }
    const t = archivio.find(x => String(x.id) === a[1])
    if (!t) return { exitCode: 2, stdout: '', stderr: `Errore: il todo #${a[1]} non esiste. Vedi la lista con: arturo todo\n` }
    const scala = ['più avanti', 'settimana', 'oggi']
    if (a[0] === 'fatto') Object.assign(t, { stato: 'fatto', motivo: null })
    else if (a[0] === 'ferma') Object.assign(t, { stato: 'fermo', motivo: a[2] ?? null })
    else if (a[0] === 'riprendi') Object.assign(t, { stato: 'da fare', motivo: null })
    else if (a[0] === 'ripristina') Object.assign(t, { stato: a[2], motivo: a[3] ?? null })
    else if (a[0] === 'su') t.quando = scala[Math.min(2, scala.indexOf(t.quando) + 1)]!
    else if (a[0] === 'giu') t.quando = scala[Math.max(0, scala.indexOf(t.quando) - 1)]!
    else if (a[0] === 'modifica' && a[2] === '--chi') t.chi = a[3] as TodoVoce['chi']
    else if (a[0] === 'modifica' && a[2] === '--quando') t.quando = a[3]!
    else return { exitCode: 2, stdout: '', stderr: `Errore: comando sconosciuto: «${a[0]}»\n` }
    return { exitCode: 0, stdout: 'ok\n', stderr: '' }
  }

  on('process.run', async (_$, e) => {
    const argv = [...e.argv]
    chiamate.push(argv)
    if (argv[1] === '-c' || argv[2] === '-c') {
      const stato = python[argv[0]!] ?? 'rifiuta'
      if (stato === 'rifiuta') throw new Error(`${argv[0]}: comando non trovato`)
      const uscita = stato === 'ok' ? { exitCode: 0, stdout: '1\n', stderr: '' } : { exitCode: 9009, stdout: '', stderr: '' }
      return { value: { ...uscita, isStdoutTruncated: false, isStderrTruncated: false } }
    }
    const i = argv.findIndex(x => x.endsWith('/bin/arturo'))
    return { value: { ...esegui(argv.slice(i + 2)), isStdoutTruncated: false, isStderrTruncated: false } }
  })
  on('ui.open', async (_$, e) => {
    aperture.push(e)
    return { value: { isPlaced: true } } as never
  })
  on('ui.close', async () => ({ value: undefined }) as never)
  on('ui.toast', async (_$, e) => {
    toast.push(e.text)
    return { value: undefined }
  })
  on('ui.render', async ($, e) => {
    const { Box } = $.ui.resolve(e)
    return <Box />
  })
  on('turn.complete', async (_$, e) => ({ text: e.answer }))

  // Gli argomenti della CLI dopo il percorso di bin/arturo: ['todo', ...].
  const cli = () => chiamate.filter(a => a.some(x => x.endsWith('/bin/arturo'))).map(a => a.slice(a.findIndex(x => x.endsWith('/bin/arturo')) + 1))
  return {
    archivio, chiamate, toast, aperture, cli,
    scritture: () => cli().filter(a => a[1] !== '--json'),
    versione: (n: number) => { versione = n },
    avvisi: (a: string[]) => { avvisi = a },
  }
}

for (const surface of ['terminal', 'desktop'] as const) {
  const apri = async ($: Engine, args = '') => {
    const r = await $.command.run({ command: 'dafare', args, ...COMANDO } as never)
    const pane = await $.ui.mount({ plugin: 'dafare', surface, component: 'Pane', requestId: 'dafare', props: PANE })
    return { r, pane }
  }

  test(`${surface}: U20 archivio vuoto, il pannello si apre e lo dice`, async ($, on) => {
    const m = motore(on, [])
    const { r, pane } = await apri($)
    const aperto = m.aperture[0] as Record<string, unknown>
    expect(aperto).toMatchObject({ id: 'dafare', focus: true, closeOnEscape: true, holdToasts: true })
    expect(m.cli()[0]).toEqual(['todo', '--json'])
    expect((r as { text: string }).text).toContain('non hai cose da fare')
    expect(await pane.find({ type: 'Text', text: 'Non hai cose da fare segnate' })).toBeTruthy()
    expect(await pane.find({ type: 'Text', text: 'ricordami di' })).toBeTruthy()
    expect(await pane.find({ key: 'fatto' })).toBeFalsy()
  })

  test(`${surface}: U21 i gruppi nell'ordine della CLI, scadenze e motivo`, async ($, on) => {
    const m = motore(on, [
      voce(1, { chi: 'io', titolo: 'Riordinare le note' }),
      voce(2, { stato: 'fermo', motivo: 'aspetto la firma', titolo: 'Spedire il contratto' }),
      voce(3, { chi: 'decidi', titolo: 'Scegliere la copertina', giorni: 0, scadenza: '2026-10-03', scadenza_testo: 'scade oggi' }),
      voce(4, { titolo: 'Mandare il preventivo', giorni: -2, scadenza: '2026-10-01', scadenza_testo: 'scaduto da 2 g' }),
    ])
    m.avvisi(['riga 7 del registro illeggibile, saltata'])
    const { r, pane } = await apri($)
    expect((r as { text: string }).text).toContain('4 cose da fare')
    const titoli = (await pane.findAll({ type: 'Text', text: /^(TOCCA A TE|DECIDI TU|FACCIO IO|FERMO)/ })).map(x => x.text)
    expect(titoli).toEqual(['TOCCA A TE (1)', 'DECIDI TU, POI FACCIO IO (1)', 'FACCIO IO (1)', 'FERMO (1)'])
    expect(await pane.find({ type: 'Text', text: 'scaduto da 2 g' })).toBeTruthy()
    expect(await pane.find({ type: 'Text', text: 'scade oggi' })).toBeTruthy()
    expect(await pane.find({ type: 'Text', text: 'fermo: aspetto la firma' })).toBeTruthy()
    expect(await pane.find({ type: 'Text', text: 'riga 7 del registro illeggibile' })).toBeTruthy()
  })

  test(`${surface}: U22 scelgo la riga 3 e premo f: fatto, rilettura, CHIUSI ORA`, async ($, on) => {
    const m = motore(on, [voce(1), voce(2), voce(3, { titolo: 'Chiamare la tipografia' })])
    const { pane } = await apri($)
    await pane.press({ key: 'riga-3' })
    await pane.press({ key: 'fatto' })
    const dopo = m.cli().slice(-2)
    expect(dopo).toEqual([['todo', 'fatto', '3'], ['todo', '--json']])
    expect(await pane.find({ type: 'Text', text: 'CHIUSI ORA (1)' })).toBeTruthy()
    expect(await pane.find({ type: 'Text', text: '#3 Chiamare la tipografia' })).toBeTruthy()
    expect(m.toast.some(x => x.includes('u per annullare'))).toBe(true)
  })

  test(`${surface}: U23 u annulla il fatto, il secondo u non lancia niente`, async ($, on) => {
    const m = motore(on, [voce(1), voce(2), voce(3)])
    const { pane } = await apri($)
    await pane.press({ key: 'riga-3' })
    await pane.press({ key: 'fatto' })
    await pane.press({ key: 'annulla' })
    expect(m.scritture().slice(-1)).toEqual([['todo', 'ripristina', '3', 'da fare']])
    expect(await pane.find({ type: 'Text', text: 'CHIUSI ORA' })).toBeFalsy()
    const prima = m.chiamate.length
    await pane.press({ key: 'annulla' })
    expect(m.chiamate.length).toBe(prima)
    expect(m.toast[m.toast.length - 1]).toContain('Niente da annullare')
  })

  test(`${surface}: U24 ferma e riprendi con i loro inversi`, async ($, on) => {
    const m = motore(on, [voce(3), voce(4, { stato: 'fermo', motivo: 'aspetto la firma' })])
    const { pane } = await apri($)
    await pane.press({ key: 'riga-3' })
    await pane.press({ key: 'ferma' })
    await pane.press({ key: 'annulla' })
    await pane.press({ key: 'riga-4' })
    await pane.press({ key: 'riprendi' })
    await pane.press({ key: 'annulla' })
    expect(m.scritture()).toEqual([
      ['todo', 'ferma', '3'],
      ['todo', 'ripristina', '3', 'da fare'],
      ['todo', 'riprendi', '4'],
      ['todo', 'ripristina', '4', 'fermo', 'aspetto la firma'],
    ])
  })

  test(`${surface}: U25 c fa il giro tu, decidi, io, tu, e u lo riporta indietro`, async ($, on) => {
    const m = motore(on, [voce(3)])
    const { pane } = await apri($)
    await pane.press({ key: 'chi' })
    await pane.press({ key: 'annulla' })
    await pane.press({ key: 'chi' })
    await pane.press({ key: 'chi' })
    await pane.press({ key: 'chi' })
    expect(m.scritture()).toEqual([
      ['todo', 'modifica', '3', '--chi', 'decidi'],
      ['todo', 'modifica', '3', '--chi', 'tu', '--annullo'],
      ['todo', 'modifica', '3', '--chi', 'decidi'],
      ['todo', 'modifica', '3', '--chi', 'io'],
      ['todo', 'modifica', '3', '--chi', 'tu'],
    ])
  })

  test(`${surface}: U26 a avvicina, u rimette il quando di prima, l allontana`, async ($, on) => {
    const m = motore(on, [voce(3, { quando: 'settimana' })])
    const { pane } = await apri($)
    await pane.press({ key: 'avvicina' })
    await pane.press({ key: 'annulla' })
    await pane.press({ key: 'allontana' })
    expect(m.scritture()).toEqual([
      ['todo', 'su', '3'],
      ['todo', 'modifica', '3', '--quando', 'settimana', '--annullo'],
      ['todo', 'giu', '3'],
    ])
  })

  test(`${surface}: U27 un errore della CLI si vede e non cambia niente`, async ($, on) => {
    const m = motore(on, [voce(3)], {
      rompi: a => (a[0] === 'fatto' ? { exitCode: 2, stdout: '', stderr: 'Errore: il todo #3 non esiste\n' } : null),
    })
    const { pane } = await apri($)
    await pane.press({ key: 'fatto' })
    expect(m.toast[m.toast.length - 1]).toBe('Errore: il todo #3 non esiste')
    expect((await pane.findAll({ type: 'Text', text: 'Errore: il todo #3 non esiste' })).length).toBe(1)
    expect(await pane.find({ type: 'Text', text: 'CHIUSI ORA' })).toBeFalsy()
    expect(await pane.find({ key: 'riga-3' })).toBeTruthy()
    await pane.press({ key: 'annulla' })
    expect(m.toast[m.toast.length - 1]).toContain('Niente da annullare')
    expect(m.scritture()).toEqual([['todo', 'fatto', '3']])
  })

  test(`${surface}: U28 la ricerca di Python e il percorso della CLI`, async ($, on) => {
    const m = motore(on, [voce(3)], { python: { python3: 'rifiuta', python: 'ok' } })
    const { pane } = await apri($)
    await pane.press({ key: 'fatto' })
    const prove = m.chiamate.filter(a => a.includes('-c')).map(a => a[0])
    expect(prove).toEqual(['python3', 'python'])
    const allaCli = m.chiamate.filter(a => !a.includes('-c'))
    expect(allaCli.length).toBeGreaterThan(1)
    for (const a of allaCli) {
      expect(a[0]).toBe('python')
      // La radice del mod è un percorso assoluto che finisce con la sua cartella.
      expect(a[1]!).toMatch(/^(\/|[A-Za-z]:).*dafare\/\.\.\/\.\.\/bin\/arturo$/)
    }
  })

  test(`${surface}: U28 l'alias di Windows che esce con 9009 non vale, e senza Python lo dice`, async ($, on) => {
    const m = motore(on, [voce(3)], { python: { python3: 'alias', python: 'alias', py: 'ok' } })
    await apri($)
    expect(m.chiamate.filter(a => a.includes('-c')).map(a => a[0])).toEqual(['python3', 'python', 'py'])
    expect(m.cli()[0]).toEqual(['todo', '--json'])
    expect(m.chiamate.find(a => !a.includes('-c'))?.slice(0, 2)).toEqual(['py', '-3'])
  })

  test(`${surface}: U28 nessun Python: l'esito dice «Non trovo Python»`, async ($, on) => {
    motore(on, [voce(3)], { python: {} })
    const { r, pane } = await apri($)
    expect((r as { text: string }).text).toContain('Non trovo Python')
    expect(await pane.find({ type: 'Text', text: 'Non trovo Python' })).toBeTruthy()
  })

  test(`${surface}: U29 p cambia progetto e /dafare libro apre già filtrato`, async ($, on) => {
    motore(on, [voce(1, { progetto: 'libro' }), voce(2, { progetto: 'casa' }), voce(3, { progetto: 'libro' })])
    const { pane } = await apri($)
    expect(await pane.find({ type: 'Text', text: '3 cose da fare' })).toBeTruthy()
    await pane.press({ key: 'progetto' })
    expect(await pane.find({ type: 'Text', text: 'progetto libro' })).toBeTruthy()
    expect(await pane.find({ key: 'riga-2' })).toBeFalsy()
    expect(await pane.find({ type: 'Text', text: 'TOCCA A TE (2)' })).toBeTruthy()
    await pane.press({ key: 'progetto' })
    expect(await pane.find({ type: 'Text', text: 'progetto casa' })).toBeTruthy()
    expect(await pane.find({ key: 'riga-1' })).toBeFalsy()
    await pane.press({ key: 'progetto' })
    expect(await pane.find({ type: 'Text', text: 'tutti i progetti' })).toBeTruthy()
    await pane.unmount()
    const filtrato = await apri($, 'libro')
    expect((filtrato.r as { text: string }).text).toContain('2 cose da fare in libro')
    expect(await filtrato.pane.find({ key: 'riga-2' })).toBeFalsy()
  })

  test(`${surface}: U30 una CLI con un'altra versione: niente tasti, il pannello chiede /aggiorna`, async ($, on) => {
    const m = motore(on, [voce(3)])
    m.versione(2)
    const { pane } = await apri($)
    expect(await pane.find({ type: 'Text', text: '/aggiorna' })).toBeTruthy()
    expect(await pane.find({ key: 'fatto' })).toBeFalsy()
  })

  test(`${surface}: U31 la barra sopra il prompt, il sondaggio e /dafare nascondi`, async ($, on) => {
    mock.store(on)
    const m = motore(on, [voce(1), voce(2, { giorni: -1, scadenza_testo: 'scaduto ieri' }), voce(3, { chi: 'io' })])
    await $.command.run({ command: 'dafare', args: '', ...COMANDO } as never)
    const barra = await $.ui.mount({ plugin: 'dafare', surface, component: 'AbovePrompt', props: BAND })
    const testo = (await barra.find({ type: 'Text', text: 'cose da fare' }))?.text ?? ''
    expect(testo).toContain('3 cose da fare')
    expect(testo).toContain('1 scaduta')
    expect(testo).toContain('/dafare')
    await barra.unmount()
    const sondaggio = await $.ui.mount({ plugin: 'dafare', surface, component: 'AbovePrompt', props: BAND_SONDAGGIO })
    expect(await sondaggio.find({ type: 'Text', text: 'cose da fare' })).toBeFalsy()
    await sondaggio.unmount()
    await $.command.run({ command: 'dafare', args: 'nascondi', ...COMANDO } as never)
    const spenta = await $.ui.mount({ plugin: 'dafare', surface, component: 'AbovePrompt', props: BAND })
    expect(await spenta.find({ type: 'Text', text: 'cose da fare' })).toBeFalsy()
    await spenta.unmount()
    await $.command.run({ command: 'dafare', args: 'mostra', ...COMANDO } as never)
    const accesa = await $.ui.mount({ plugin: 'dafare', surface, component: 'AbovePrompt', props: BAND })
    expect(await accesa.find({ type: 'Text', text: 'cose da fare' })).toBeTruthy()
    await accesa.unmount()
    m.archivio.splice(0, m.archivio.length)
    await $.command.run({ command: 'dafare', args: '', ...COMANDO } as never)
    const vuota = await $.ui.mount({ plugin: 'dafare', surface, component: 'AbovePrompt', props: BAND })
    expect(await vuota.find({ type: 'Text', text: 'cose da fare' })).toBeFalsy()
  })

  test(`${surface}: U32 a fine turno il pannello rilegge e la barra si aggiorna`, async ($, on) => {
    const m = motore(on, [voce(1)])
    await $.command.run({ command: 'dafare', args: '', ...COMANDO } as never)
    m.archivio.push(voce(2), voce(3))
    const prima = m.cli().length
    await $.turn.complete({ answer: 'fatto', durationMs: 10, isAborted: false, turnId: 't1', reason: 'end_turn' } as never)
    expect(m.cli().slice(prima)).toEqual([['todo', '--json']])
    const barra = await $.ui.mount({ plugin: 'dafare', surface, component: 'AbovePrompt', props: BAND })
    expect(await barra.find({ type: 'Text', text: '3 cose da fare' })).toBeTruthy()
  })

  test(`${surface}: U33 uno stdout che non è JSON lascia intera la vista di prima`, async ($, on) => {
    let rotto = false
    motore(on, [voce(1), voce(2)], {
      rompi: a => (rotto && a[0] === '--json' ? { exitCode: 0, stdout: 'non è JSON', stderr: '' } : null),
    })
    const { pane } = await apri($)
    rotto = true
    await pane.press({ key: 'fatto' })
    expect(await pane.find({ type: 'Text', text: 'formato che il pannello non legge' })).toBeTruthy()
    expect(await pane.find({ key: 'riga-1' })).toBeTruthy()
    expect(await pane.find({ key: 'riga-2' })).toBeTruthy()
  })
}
