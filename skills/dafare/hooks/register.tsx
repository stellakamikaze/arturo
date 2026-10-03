// Il pannello /dafare: le cose da fare della persona dentro Claude Code.
//
// Legge e scrive solo con la CLI `arturo todo`, lanciata per argv e senza shell. Dopo ogni tasto
// rilegge `arturo todo --json`: il pannello non scrive mai l'archivio da solo. Un errore della CLI
// compare in italiano e non cambia niente. Ogni tasto si annulla con «u».

import { atom, read, update } from 'claude-code'
import type { EngineInterface, Register } from 'claude-code'

import type { Annullabile, Esito, TodoVoce, Vista } from '../types'
import { VERBI } from './verbi.mjs'

const PANE = 'dafare'
// La CLI sta accanto alla cartella skills/ di Arturo: <radice>/skills/dafare/../../bin/arturo.
const CLI_REL = '/../../bin/arturo'
const VERSIONE_VISTA = 1
const MAX_ANNULLI = 10
// La stella di Arturo, solo come segno nella barra.
const STELLA = '\u2605'
const CANDIDATI_PYTHON: string[][] = [['python3'], ['python'], ['py', '-3']]

// La palette di Arturo su fondo chiaro. Il pannello porta il suo fondo: i colori non dipendono dal
// tema del terminale. Gli esiti sono testo o bordo, mai un fondo pieno.
const C = {
  tela: '#fefffc',
  inchiostro: '#171717',
  cenere: '#646464',
  sera: '#2b6f9e',
  passa: '#2f7a4f',
  blocca: '#b2392b',
  arturo: '#f2a24a',
}

const COLORE_GRUPPO: Record<string, string> = { tu: C.sera, decidi: C.sera, io: C.passa, fermo: C.blocca }

const vista = atom({ plugin: 'dafare', key: 'vista' } as const, null)
const errore = atom({ plugin: 'dafare', key: 'errore' } as const, '')
const esito = atom({ plugin: 'dafare', key: 'esito' } as const, null)
const scelto = atom({ plugin: 'dafare', key: 'scelto' } as const, null)
const filtro = atom({ plugin: 'dafare', key: 'filtro' } as const, 'tutti')
const chiusiQui = atom({ plugin: 'dafare', key: 'chiusiQui' } as const, [])
const annullabili = atom({ plugin: 'dafare', key: 'annullabili' } as const, [])
const pythonScelto = atom({ plugin: 'dafare', key: 'python' } as const, null)
const barraNascosta = atom({ plugin: 'dafare', key: 'barraNascosta' } as const, false)

type Risposta = { ok: true; stdout: string } | { ok: false; testo: string }
type Riga = { t: TodoVoce; tasto: string }
type Verbo = keyof typeof VERBI

// --- funzioni che ricevono $ ---------------------------------------------------------------

// Il primo Python che risponde davvero: su Windows `python3` può essere un rimando al Microsoft
// Store che esce con 9009. Quello trovato resta per la sessione.
async function python($: EngineInterface): Promise<string[] | null> {
  const noto = await read($, pythonScelto)
  if (noto) return noto
  for (const candidato of CANDIDATI_PYTHON) {
    try {
      const r = await $.process.run([...candidato, '-c', 'print(1)'], { timeoutMs: 15000 })
      if (r.exitCode === 0 && r.stdout.trim() === '1') {
        await update($, pythonScelto, () => candidato)
        return candidato
      }
    } catch {
      // Il comando non parte: si prova il prossimo.
    }
  }
  return null
}

async function cli($: EngineInterface, argomenti: string[]): Promise<Risposta> {
  const py = await python($)
  if (!py) return { ok: false, testo: 'Non trovo Python: scrivi a Claude «lancia /setup».' }
  try {
    const r = await $.process.run([...py, $.plugin.root + CLI_REL, 'todo', ...argomenti], { timeoutMs: 15000 })
    if (r.exitCode === 0) return { ok: true, stdout: r.stdout }
    const prima = (r.stderr || r.stdout).split('\n').map(x => x.trim()).find(x => x !== '')
    return { ok: false, testo: prima ?? `La CLI dei todo si è fermata con il codice ${r.exitCode}.` }
  } catch {
    return { ok: false, testo: 'La CLI dei todo non parte: scrivi a Claude «lancia /diagnosi».' }
  }
}

// Rilegge le cose da fare. Un guasto lascia intatta la vista di prima: mai vuota per un errore.
async function carica($: EngineInterface): Promise<void> {
  const r = await cli($, ['--json'])
  if (!r.ok) {
    await update($, errore, () => r.testo)
    return
  }
  let dato: unknown
  try {
    dato = JSON.parse(r.stdout)
  } catch {
    await update($, errore, () => 'La CLI dei todo ha risposto in un formato che il pannello non legge.')
    return
  }
  const v = dato as Vista
  if (!v || typeof v !== 'object' || !Array.isArray(v.gruppi)) {
    await update($, errore, () => 'La CLI dei todo ha risposto in un formato che il pannello non legge.')
    return
  }
  if (v.versione !== VERSIONE_VISTA) {
    await update($, vista, () => null)
    await update($, errore, () => 'Il pannello e la CLI non vanno d\'accordo: scrivi /aggiorna.')
    return
  }
  await update($, vista, () => v)
  await update($, errore, () => '')
}

async function righeOra($: EngineInterface): Promise<Riga[]> {
  return righe(await read($, vista), await read($, filtro))
}

async function sceltaOra($: EngineInterface): Promise<TodoVoce | undefined> {
  const tutte = await righeOra($)
  const id = await read($, scelto)
  return (tutte.find(r => r.t.id === id) ?? tutte[0])?.t
}

async function dici($: EngineInterface, testo: string, ok: boolean): Promise<void> {
  const nuovo: Esito = { testo, ok }
  await update($, esito, () => nuovo)
  $.ui.toast(testo)
}

async function agisci($: EngineInterface, verbo: Verbo): Promise<void> {
  const t = await sceltaOra($)
  if (!t) {
    await dici($, 'Non ci sono righe da scegliere.', false)
    return
  }
  const voce = VERBI[verbo]
  if (!voce) return
  const inverso: Annullabile = { argv: voce.inverso(t), descrizione: `${voce.etichetta} su #${t.id}`, id: t.id }
  const r = await cli($, voce.argv(t))
  if (!r.ok) {
    await dici($, r.testo, false)
    return
  }
  await update($, annullabili, pila => [...pila, inverso].slice(-MAX_ANNULLI))
  if (verbo === 'fatto') await update($, chiusiQui, lista => [...lista.filter(x => x.id !== t.id), t])
  await update($, scelto, () => t.id)
  await carica($)
  await dici($, `Fatto: ${voce.etichetta} su #${t.id}. Premi u per annullare.`, true)
}

async function annulla($: EngineInterface): Promise<void> {
  const pila = await read($, annullabili)
  const ultimo = pila[pila.length - 1]
  if (!ultimo) {
    await dici($, 'Niente da annullare.', false)
    return
  }
  const r = await cli($, ultimo.argv)
  if (!r.ok) {
    await dici($, r.testo, false)
    return
  }
  await update($, annullabili, p => p.slice(0, -1))
  await update($, chiusiQui, lista => lista.filter(x => x.id !== ultimo.id))
  await update($, scelto, () => ultimo.id)
  await carica($)
  await dici($, `Annullato: ${ultimo.descrizione}.`, true)
}

async function sposta($: EngineInterface, passo: number): Promise<void> {
  const tutte = await righeOra($)
  if (tutte.length === 0) return
  const id = await read($, scelto)
  const i = Math.max(0, tutte.findIndex(r => r.t.id === id))
  const dopo = tutte[Math.min(tutte.length - 1, Math.max(0, i + passo))]
  if (dopo) await update($, scelto, () => dopo.t.id)
}

async function cambiaProgetto($: EngineInterface): Promise<void> {
  const elenco = ['tutti', ...progetti(await read($, vista))]
  const ora = await read($, filtro)
  const nuovo = elenco[(elenco.indexOf(ora) + 1) % elenco.length] ?? 'tutti'
  await update($, filtro, () => nuovo)
  await update($, scelto, () => null)
}

async function apri($: EngineInterface): Promise<void> {
  try {
    await $.ui.open({ id: PANE, title: 'Le tue cose da fare', focus: true, closeOnEscape: true, holdToasts: true, rows: 30 })
  } catch {
    // Senza una superficie (claude -p) il pannello non si apre: la risposta del comando basta.
  }
}

async function barra($: EngineInterface, nascosta: boolean): Promise<void> {
  await update($, barraNascosta, () => nascosta)
  await $.store.set('barraNascosta', nascosta)
}

// --- funzioni pure ---------------------------------------------------------------------------

function aperti(v: Vista | null): TodoVoce[] {
  return v ? v.gruppi.flatMap(g => g.todo) : []
}

function progetti(v: Vista | null): string[] {
  const visti: string[] = []
  for (const t of aperti(v)) if (!visti.includes(t.progetto)) visti.push(t.progetto)
  return visti
}

function righe(v: Vista | null, f: string): Riga[] {
  const scelte = aperti(v).filter(t => f === 'tutti' || t.progetto === f)
  return scelte.map((t, i) => ({ t, tasto: i < 9 ? String(i + 1) : '' }))
}

function quante(n: number): string {
  return n === 1 ? '1 cosa da fare' : `${n} cose da fare`
}

function scadute(lista: TodoVoce[]): number {
  return lista.filter(t => t.giorni !== null && t.giorni < 0).length
}

function dettagli(t: TodoVoce, conProgetto: boolean): string[] {
  return [
    conProgetto ? t.progetto : '',
    t.stato === 'in corso' ? 'in corso' : '',
    t.gruppo === 'fermo' && t.motivo ? `fermo: ${t.motivo}` : '',
    t.perche ? `perché: ${t.perche}` : '',
    t.attende.length > 0 ? `aspetta ${t.attende.map(n => `#${n}`).join(', ')}` : '',
  ].filter(x => x !== '')
}

const AIUTO = 'Tasti: numero o j/k per scegliere, f fatto, s ferma, r riprendi, c chi lo fa, a avvicina, l allontana, u annulla, p progetto, Esc chiude.'

export const register: Register = on => {
  on('session.start', async ($, e, next) => {
    await $.command.register({
      name: 'dafare',
      description: 'Apre il pannello delle tue cose da fare',
      argumentHint: '[progetto | nascondi | mostra]',
    })
    const nascosta = (await $.store.get('barraNascosta')) === true
    await update($, barraNascosta, () => nascosta)
    await carica($)
    return next(e)
  })

  on('command.run', { command: 'dafare' }, async ($, e) => {
    const arg = e.args.trim()
    if (arg === 'nascondi') {
      await barra($, true)
      return { text: 'La riga sopra il prompt è spenta. La riaccendi con /dafare mostra.' }
    }
    if (arg === 'mostra') {
      await barra($, false)
      return { text: 'La riga sopra il prompt è accesa.' }
    }
    await update($, filtro, () => arg || 'tutti')
    await update($, scelto, () => null)
    await carica($)
    const v = await read($, vista)
    const problema = await read($, errore)
    await apri($)
    if (!v) return { text: `Pannello aperto, ma non leggo le cose da fare. ${problema}` }
    const n = righe(v, arg || 'tutti').length
    const dove = arg ? ` in ${arg}` : ''
    return { text: n === 0 ? `Pannello aperto: non hai cose da fare segnate${dove}.` : `Pannello aperto: ${quante(n)}${dove}. ${AIUTO}` }
  })

  // Claude può aver usato la CLI nel turno: a fine turno il pannello e la barra rileggono.
  on('turn.complete', async ($, e, next) => {
    const r = await next(e)
    await carica($)
    return r
  })

  on('ui.render', { component: 'Pane', requestId: PANE }, async ($, e) => {
    const { Box, Text, Button } = $.ui.resolve(e)
    const v = await read($, vista)
    const problema = await read($, errore)
    const ultimo = await read($, esito)
    const f = await read($, filtro)
    const chiusi = await read($, chiusiQui)
    const tutte = righe(v, f)
    const id = await read($, scelto)
    const attiva = (tutte.find(r => r.t.id === id) ?? tutte[0])?.t.id
    const stretto = e.props.bodyColumns < 60

    const testa = v
      ? [quante(tutte.length), scadute(tutte.map(r => r.t)) > 0 ? `${scadute(tutte.map(r => r.t))} scadute` : '',
        f === 'tutti' ? 'tutti i progetti' : `progetto ${f}`].filter(x => x !== '').join(' · ')
      : ''

    const piede = (
      <Box flexDirection="column" borderStyle="single" borderColor={C.cenere} paddingX={1}>
        {v ? (
          <Box flexDirection="column">
            {tutte.length > 0 ? (
              <Box gap={2} flexWrap="wrap">
                {(Object.keys(VERBI) as Verbo[]).map(verbo => (
                  <Button key={verbo} plain hotkey={VERBI[verbo]!.tasto} label={VERBI[verbo]!.etichetta} onPress={() => agisci($, verbo)} />
                ))}
              </Box>
            ) : null}
            <Box gap={2} flexWrap="wrap">
              <Button key="annulla" plain hotkey="u" label="annulla" onPress={() => annulla($)} />
              <Button key="progetto" plain hotkey="p" label="progetto" onPress={() => cambiaProgetto($)} />
              {tutte.length > 1 ? <Button key="giu" plain hotkey="j" label="giù" onPress={() => sposta($, 1)} /> : null}
              {tutte.length > 1 ? <Button key="su" plain hotkey="k" label="su" onPress={() => sposta($, -1)} /> : null}
            </Box>
          </Box>
        ) : null}
        <Text color={C.cenere} wrap="wrap">Esc chiude. Se i tasti non rispondono: ctrl+x tab, oppure /dafare.</Text>
      </Box>
    )

    return (
      <Box flexDirection="column" gap={1} backgroundColor={C.tela} paddingX={stretto ? 1 : 2} paddingY={1} flexGrow={1}>
        <Box flexDirection="column">
          <Text bold color={C.inchiostro} wrap="wrap">Le tue cose da fare</Text>
          {testa ? <Text color={C.cenere} wrap="wrap">{testa}</Text> : null}
        </Box>
        {problema ? (
          <Box borderStyle="round" borderColor={C.blocca} paddingX={1}>
            <Text color={C.blocca} wrap="wrap">{problema}</Text>
          </Box>
        ) : null}
        {ultimo ? (
          <Box borderStyle="round" borderColor={ultimo.ok ? C.passa : C.blocca} paddingX={1}>
            <Text color={ultimo.ok ? C.passa : C.blocca} wrap="wrap">{ultimo.testo}</Text>
          </Box>
        ) : null}
        {v ? v.avvisi.map(a => <Text color={C.blocca} wrap="wrap">Attenzione: {a}</Text>) : null}
        {v && aperti(v).length === 0 ? (
          <Box flexDirection="column">
            <Text color={C.inchiostro} wrap="wrap">Non hai cose da fare segnate.</Text>
            <Text color={C.cenere} wrap="wrap">Di' a Claude: ricordami di…</Text>
          </Box>
        ) : null}
        {v && aperti(v).length > 0 && tutte.length === 0 ? (
          <Text color={C.cenere} wrap="wrap">Nessuna cosa da fare in {f}. Premi p per cambiare progetto.</Text>
        ) : null}
        {v
          ? v.gruppi.map(g => {
              const dentro = tutte.filter(r => r.t.gruppo === g.tipo)
              if (dentro.length === 0) return null
              const colore = COLORE_GRUPPO[g.tipo] ?? C.inchiostro
              return (
                <Box flexDirection="column">
                  <Text bold color={colore} wrap="wrap">{g.titolo} ({dentro.length})</Text>
                  {stretto ? null : <Text color={C.cenere} wrap="wrap">{g.descrizione}</Text>}
                  {dentro.map(r => {
                    const sua = r.t.id === attiva
                    const sotto = dettagli(r.t, f === 'tutti')
                    const scaduta = r.t.giorni !== null && r.t.giorni < 0
                    return (
                      <Box flexDirection="column" paddingLeft={1}>
                        <Box gap={1}>
                          <Text bold color={C.sera}>{sua ? '›' : ' '}</Text>
                          {r.tasto
                            ? <Button key={`riga-${r.t.id}`} plain hotkey={r.tasto} label={`#${r.t.id}`} onPress={() => update($, scelto, () => r.t.id)} />
                            : <Button key={`riga-${r.t.id}`} plain label={`#${r.t.id}`} onPress={() => update($, scelto, () => r.t.id)} />}
                          <Text bold={sua} color={sua ? C.sera : C.inchiostro} wrap="wrap">{r.t.titolo}</Text>
                        </Box>
                        {sotto.length > 0 || r.t.scadenza_testo ? (
                          <Box paddingLeft={6} gap={1} flexWrap="wrap">
                            {r.t.scadenza_testo ? <Text bold={scaduta} color={scaduta ? C.blocca : C.cenere}>{r.t.scadenza_testo}</Text> : null}
                            {sotto.length > 0 ? <Text color={C.cenere} wrap="wrap">{sotto.join(' · ')}</Text> : null}
                          </Box>
                        ) : null}
                      </Box>
                    )
                  })}
                </Box>
              )
            })
          : null}
        {chiusi.length > 0 ? (
          <Box flexDirection="column">
            <Text bold color={C.cenere}>CHIUSI ORA ({chiusi.length})</Text>
            {chiusi.map(t => (
              <Box paddingLeft={3}>
                <Text color={C.cenere} wrap="wrap">#{t.id} {t.titolo} · fatto</Text>
              </Box>
            ))}
          </Box>
        ) : null}
        {piede}
      </Box>
    )
  })

  on('ui.render', { component: 'AbovePrompt' }, async ($, e, next) => {
    const v = await read($, vista)
    const lista = aperti(v)
    if (e.props.hasSurvey || (await read($, barraNascosta)) || lista.length === 0) return next(e)
    const { Box, Text, Button } = $.ui.resolve(e)
    const k = scadute(lista)
    const corto = e.props.bodyColumns < 60
    const testo = corto
      ? `${quante(lista.length)} · /dafare`
      : [quante(lista.length), k === 1 ? '1 scaduta' : k > 1 ? `${k} scadute` : '', '/dafare per vederle']
          .filter(x => x !== '').join(' · ')
    return (
      <Box gap={1} backgroundColor={C.tela} paddingX={1}>
        <Text color={C.arturo}>{STELLA}</Text>
        <Text color={C.inchiostro}>{testo}</Text>
        {corto ? null : <Button key="apri" plain label="apri" onPress={() => apri($)} />}
      </Box>
    )
  })
}
