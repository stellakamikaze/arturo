// Prova del pannello /dafare: una linguetta per progetto (A3) e la catena a un clic (B2).
// Dati di esempio in memoria, come sulla pagina di prova: niente CLI, niente archivio.

import { atom, read, update } from 'claude-code'
import type { EngineInterface, Register } from 'claude-code'

import type { Chi, Voce } from '../types'

const PANE = 'dafare-prova'
const TITOLO = 'Le tue cose da fare'

const C = {
  tela: '#fefffc',
  inchiostro: '#171717',
  cenere: '#646464',
  sera: '#2b6f9e',
  passa: '#2f7a4f',
  blocca: '#b2392b',
}

function v(id: number, progetto: string, titolo: string, chi: Chi, campi: Partial<Voce> = {}): Voce {
  return { id, titolo, progetto, chi, stato: 'da fare', giorni: null, motivo: null, dopo: [], ...campi }
}

const ESEMPIO: Voce[] = [
  v(4, 'Sito nuovo', "Scegliere l'hosting", 'decidi'),
  v(7, 'Sito nuovo', 'Configurare il dominio', 'io', { dopo: [4] }),
  v(9, 'Sito nuovo', 'Pubblicare la beta', 'io', { dopo: [7] }),
  v(8, 'Sito nuovo', 'Attivare le email', 'io', { dopo: [4] }),
  v(5, 'Sito nuovo', 'Mandare il logo in vettoriale', 'tu', { giorni: -1 }),
  v(11, 'Sito nuovo', 'Stampare i biglietti', 'io', { dopo: [5] }),
  v(6, 'Sito nuovo', 'Approvare i testi della home', 'decidi'),
  v(12, 'Sito nuovo', 'Impaginare la home', 'io', { dopo: [6] }),
  v(2, 'Sito nuovo', 'Rileggere la pagina privacy', 'tu', { giorni: 3 }),
  v(13, 'Sito nuovo', 'Preparare le immagini per i social', 'io'),
  v(15, 'Sito nuovo', 'Scrivere la pagina contatti', 'io'),
  v(14, 'Sito nuovo', 'Rinnovare il certificato', 'io', { stato: 'fermo', motivo: 'aspetta la risposta di Aruba' }),
  v(1, 'Sito nuovo', 'Comprare il dominio', 'tu', { stato: 'fatto' }),
  v(3, 'Sito nuovo', 'Scegliere i colori', 'decidi', { stato: 'fatto' }),
  v(10, 'Sito nuovo', 'Scrivere la home', 'io', { stato: 'fatto' }),
  v(16, 'Sito nuovo', 'Raccogliere le foto', 'tu', { stato: 'fatto' }),
  v(17, 'Sito nuovo', 'Fare la mappa del sito', 'io', { stato: 'fatto' }),
  v(20, 'Podcast', 'Registrare la puntata 3', 'tu', { giorni: 2 }),
  v(21, 'Podcast', 'Montare la puntata 3', 'io', { dopo: [20] }),
  v(22, 'Podcast', 'Scrivere le note della puntata 3', 'io', { dopo: [21] }),
  v(24, 'Podcast', 'Caricare la puntata 3 su Spotify', 'io', { dopo: [21] }),
  v(23, 'Podcast', 'Scegliere la copertina della stagione', 'decidi'),
  v(25, 'Podcast', "Invitare l'ospite della puntata 4", 'tu'),
  v(26, 'Podcast', "Preparare le domande per l'ospite", 'io', { dopo: [25] }),
  v(18, 'Podcast', 'Registrare la puntata 2', 'tu', { stato: 'fatto' }),
  v(19, 'Podcast', 'Montare la puntata 2', 'io', { stato: 'fatto' }),
  v(31, 'Fatture', 'Mandare la fattura a Rossi', 'tu', { giorni: -3 }),
  v(32, 'Fatture', 'Controllare i pagamenti di settembre', 'io'),
  v(34, 'Fatture', 'Archiviare le ricevute', 'io', { dopo: [32] }),
  v(33, 'Fatture', 'Chiedere il rimborso spese', 'tu', { stato: 'fermo', motivo: 'aspetta il commercialista' }),
  v(30, 'Fatture', 'Mandare la fattura di agosto', 'tu', { stato: 'fatto' }),
  v(40, 'Trasloco', 'Chiamare la ditta', 'tu'),
  v(41, 'Trasloco', 'Scegliere il giorno del trasloco', 'decidi', { dopo: [40] }),
]

const voci = atom({ plugin: 'dafare-prova', key: 'voci' } as const, ESEMPIO, { shape: 'voci-1' })
const filtro = atom({ plugin: 'dafare-prova', key: 'filtro' } as const, 'tutti')
const catena = atom({ plugin: 'dafare-prova', key: 'catena' } as const, false)
const scelto = atom({ plugin: 'dafare-prova', key: 'scelto' } as const, null)
const esito = atom({ plugin: 'dafare-prova', key: 'esito' } as const, '')

type Riga = { t: Voce; prefisso: string }

// --- funzioni che ricevono $ ---------------------------------------------------------------

async function apri($: EngineInterface): Promise<void> {
  try {
    await $.ui.open({ id: PANE, title: TITOLO, columns: 66, rows: 30 })
  } catch {
    // Senza superficie il pannello non si apre.
  }
}

async function vaiA($: EngineInterface, progetto: string): Promise<void> {
  await update($, filtro, () => progetto)
  await update($, scelto, () => null)
  await update($, esito, () => '')
}

async function sceltaOra($: EngineInterface): Promise<Voce | undefined> {
  const tutte = righe(await read($, voci), await read($, filtro), await read($, catena))
  const id = await read($, scelto)
  return (tutte.find(r => r.t.id === id) ?? tutte[0])?.t
}

async function cambia($: EngineInterface, come: (t: Voce) => Voce, testo: (t: Voce) => string): Promise<void> {
  const t = await sceltaOra($)
  if (!t) return
  const nuova = come(t)
  await update($, voci, lista => lista.map(x => (x.id === t.id ? nuova : x)))
  await update($, esito, () => testo(nuova))
}

async function sposta($: EngineInterface, passo: number): Promise<void> {
  const tutte = righe(await read($, voci), await read($, filtro), await read($, catena))
  if (tutte.length === 0) return
  const id = await read($, scelto)
  const i = Math.max(0, tutte.findIndex(r => r.t.id === id))
  const dopo = tutte[Math.min(tutte.length - 1, Math.max(0, i + passo))]
  if (dopo) await update($, scelto, () => dopo.t.id)
}

async function ripristina($: EngineInterface): Promise<void> {
  await update($, voci, () => ESEMPIO)
  await update($, scelto, () => null)
  await update($, esito, () => 'Dati di esempio ripristinati.')
}

// --- funzioni pure ---------------------------------------------------------------------------

function aperta(t: Voce): boolean {
  return t.stato !== 'fatto'
}

function progetti(lista: Voce[]): string[] {
  const visti: string[] = []
  for (const t of lista) if (aperta(t) && !visti.includes(t.progetto)) visti.push(t.progetto)
  return visti
}

// I todo aperti che t aspetta.
function attende(t: Voce, lista: Voce[]): number[] {
  return t.dopo.filter(id => lista.some(x => x.id === id && aperta(x)))
}

function sblocca(t: Voce, lista: Voce[]): number[] {
  return lista.filter(x => aperta(x) && x.dopo.includes(t.id)).map(x => x.id)
}

function gruppo(t: Voce): string {
  return t.stato === 'fermo' ? 'fermo' : t.chi
}

function chiTesto(t: Voce): string {
  if (t.stato === 'fermo') return 'fermo'
  return t.chi === 'tu' ? 'tocca a te' : t.chi === 'decidi' ? 'decidi tu' : 'faccio io'
}

function scadenza(g: number | null): string {
  if (g === null) return ''
  if (g < 0) return g === -1 ? 'scaduto ieri' : `scaduto da ${-g} g`
  return g === 0 ? 'scade oggi' : g === 1 ? 'scade domani' : `scade tra ${g} g`
}

function scaduta(t: Voce): boolean {
  return t.giorni !== null && t.giorni < 0
}

// La stessa regola di todo_store.da_dove: prima chi chiede una persona, poi chi sblocca, poi le scadute.
function chiave(t: Voce, lista: Voce[]): number[] {
  return [
    t.stato === 'fermo' ? 1 : 0,
    t.chi === 'io' ? 1 : 0,
    sblocca(t, lista).length > 0 ? 0 : 1,
    scaduta(t) ? 0 : 1,
    t.giorni ?? 1e6,
    t.id,
  ]
}

function prima(a: number[], b: number[]): number {
  for (let i = 0; i < a.length; i++) if (a[i] !== b[i]) return (a[i] ?? 0) - (b[i] ?? 0)
  return 0
}

function daQui(lista: Voce[], progetto: string): { t: Voce; motivo: string } | null {
  const candidati = lista
    .filter(t => t.progetto === progetto && t.stato === 'da fare' && attende(t, lista).length === 0)
    .sort((a, b) => prima(chiave(a, lista), chiave(b, lista)))
  const t = candidati[0]
  if (!t) return null
  const s = sblocca(t, lista)
  const motivo = s.length > 0 ? `sblocca ${s.map(n => `#${n}`).join(', ')}` : scaduta(t) ? scadenza(t.giorni) : chiTesto(t)
  return { t, motivo }
}

function lista(tutte: Voce[], progetto: string): Riga[] {
  const ordine = ['tu', 'decidi', 'io', 'fermo']
  return tutte
    .filter(t => t.progetto === progetto && aperta(t))
    .sort((a, b) => ordine.indexOf(gruppo(a)) - ordine.indexOf(gruppo(b)) || prima(chiave(a, tutte), chiave(b, tutte)))
    .map(t => ({ t, prefisso: '' }))
}

// La catena: ogni todo sotto il primo todo aperto che aspetta. Le radici con la regola di daQui.
function albero(tutte: Voce[], progetto: string): Riga[] {
  const qui = tutte.filter(t => t.progetto === progetto && aperta(t))
  const padre = (t: Voce): number | undefined => attende(t, qui)[0]
  const figli = (id: number): Voce[] => qui.filter(t => padre(t) === id).sort((a, b) => a.id - b.id)
  const radici = qui.filter(t => padre(t) === undefined).sort((a, b) => prima(chiave(a, tutte), chiave(b, tutte)))
  const fuori: Riga[] = []
  const giu = (t: Voce, rientro: string, ultimo: boolean, radice: boolean): void => {
    fuori.push({ t, prefisso: radice ? '' : rientro + (ultimo ? '└─ ' : '├─ ') })
    const sotto = figli(t.id)
    const dentro = radice ? '' : rientro + (ultimo ? '   ' : '│  ')
    sotto.forEach((f, i) => giu(f, dentro, i === sotto.length - 1, false))
  }
  radici.forEach(r => giu(r, '', true, true))
  return fuori
}

function righe(tutte: Voce[], f: string, c: boolean): Riga[] {
  if (f === 'tutti') return []
  return c ? albero(tutte, f) : lista(tutte, f)
}

function conta(n: number, uno: string, tanti: string): string {
  return n === 1 ? `1 ${uno}` : `${n} ${tanti}`
}

function stato(tutte: Voce[], progetto: string | null): string {
  const qui = tutte.filter(t => progetto === null || t.progetto === progetto)
  const aperte = qui.filter(aperta)
  const fatte = qui.length - aperte.length
  const scad = aperte.filter(scaduta).length
  const ferme = aperte.filter(t => t.stato === 'fermo').length
  return [
    conta(aperte.length, 'aperta', 'aperte'),
    fatte > 0 ? conta(fatte, 'fatta', 'fatte') : '',
    scad > 0 ? conta(scad, 'scaduta', 'scadute') : '',
    ferme > 0 ? conta(ferme, 'ferma', 'ferme') : '',
  ].filter(x => x !== '').join(' · ')
}

// La versione in testo, per chi non vuole il pannello: una riga per cosa, allineata.
const LARGO = 44

function testoTutti(tutte: Voce[]): string {
  const elenco = progetti(tutte)
  const larghezza = Math.max(...elenco.map(p => p.length)) + 3
  const righe = [`Le tue cose da fare · ${conta(elenco.length, 'progetto', 'progetti')} · ${stato(tutte, null)}`, '']
  for (const p of elenco) {
    righe.push(p.padEnd(larghezza) + stato(tutte.filter(aperta), p))
    const dq = daQui(tutte, p)
    if (dq) righe.push(' '.repeat(larghezza) + `da qui: #${dq.t.id} ${dq.t.titolo}`)
  }
  righe.push('', 'Un progetto: /dafare-prova testo sito · la catena: /dafare-prova catena sito')
  return righe.join('\n')
}

function testoProgetto(tutte: Voce[], progetto: string, c: boolean): string {
  const titoli: Record<string, string> = { tu: 'TOCCA A TE', decidi: 'DECIDI TU', io: 'FACCIO IO', fermo: 'FERMO' }
  const righe = [`${progetto} · ${stato(tutte, progetto)}`]
  const dq = daQui(tutte, progetto)
  if (dq) righe.push(`Da qui: #${dq.t.id} ${dq.t.titolo}, ${dq.motivo}`)
  righe.push('')
  let prima = ''
  for (const r of c ? albero(tutte, progetto) : lista(tutte, progetto)) {
    const g = gruppo(r.t)
    if (!c && g !== prima) righe.push(titoli[g] ?? g)
    prima = g
    const att = attende(r.t, tutte)
    const destra = c
      ? chiTesto(r.t) + (scaduta(r.t) ? `, ${scadenza(r.t.giorni)}` : '')
      : r.t.stato === 'fermo' ? (r.t.motivo ?? '') : att.length > 0 ? `aspetta ${att.map(n => `#${n}`).join(', ')}` : scadenza(r.t.giorni)
    righe.push(`  ${`#${r.t.id}`.padEnd(5)}${(r.prefisso + r.t.titolo).padEnd(LARGO)}${destra}`)
  }
  righe.push('', c
    ? `La lista: /dafare-prova testo ${progetto.toLowerCase()} · chiudere: /dafare-prova fatto 5`
    : `La catena: /dafare-prova catena ${progetto.toLowerCase()} · chiudere: /dafare-prova fatto 5`)
  return righe.join('\n')
}

export const register: Register = on => {
  on('session.start', async ($, e, next) => {
    await $.command.register({
      name: 'dafare-prova',
      description: 'Apre la prova del pannello /dafare, o la scrive come testo',
      argumentHint: '[testo | catena | fatto N] [progetto]',
    })
    return next(e)
  })

  on('command.run', { command: 'dafare-prova' }, async ($, e) => {
    const parole = e.args.trim().split(/\s+/).filter(x => x !== '')
    if (parole.length === 0) {
      await apri($)
      return { text: 'Pannello di prova aperto.' }
    }
    let tutte = await read($, voci)
    const c = parole[0] === 'catena'
    let nome = parole.slice(1).join(' ')
    let avviso = ''
    if (parole[0] === 'fatto') {
      const id = Number(parole[1])
      const t = tutte.find(x => x.id === id && aperta(x))
      if (!t) return { text: `Non trovo una cosa aperta col numero ${parole[1] ?? ''}.` }
      tutte = tutte.map(x => (x.id === id ? { ...x, stato: 'fatto' as const } : x))
      await update($, voci, () => tutte)
      avviso = `Fatto: #${t.id} ${t.titolo}.\n\n`
      nome = t.progetto
    }
    const progetto = progetti(tutte).find(p => nome !== '' && p.toLowerCase().startsWith(nome.toLowerCase()))
    if (nome !== '' && !progetto) return { text: `Non trovo il progetto "${nome}". Progetti: ${progetti(tutte).join(', ')}.` }
    return { text: avviso + (progetto ? testoProgetto(tutte, progetto, c) : testoTutti(tutte)) }
  })

  on('ui.render', { component: 'Pane', requestId: PANE }, async ($, e) => {
    const { Box, Text, Button } = $.ui.resolve(e)
    const tutte = await read($, voci)
    const f = await read($, filtro)
    const c = await read($, catena)
    const ultimo = await read($, esito)
    const elenco = progetti(tutte)
    const sel = elenco.includes(f) ? f : 'tutti'
    const rr = righe(tutte, sel, c)
    const id = await read($, scelto)
    const attiva = (rr.find(r => r.t.id === id) ?? rr[0])?.t.id
    const aperteTutte = tutte.filter(aperta).length

    const linguette = (
      <Box gap={1} flexWrap="wrap">
        <Button key="tab-tutti" label={`Tutti ${aperteTutte}`} hotkey="0"
          variant={sel === 'tutti' ? 'primary' : undefined} dimColor={sel !== 'tutti'}
          onPress={() => vaiA($, 'tutti')} />
        {elenco.map((p, i) => (
          <Button key={`tab-${p}`} label={`${p} ${tutte.filter(t => t.progetto === p && aperta(t)).length}`}
            hotkey={i < 9 ? String(i + 1) : undefined}
            variant={sel === p ? 'primary' : undefined} dimColor={sel !== p}
            onPress={() => vaiA($, p)} />
        ))}
      </Box>
    )

    const testa = (
      <Box justifyContent="space-between">
        <Text bold color={C.inchiostro}>{TITOLO}</Text>
        {sel !== 'tutti'
          ? <Button key="catena" label={c ? 'lista' : 'catena'} hotkey="g" onPress={() => update($, catena, x => !x)} />
          : null}
      </Box>
    )

    const corpoTutti = (
      <Box flexDirection="column" gap={1}>
        <Text color={C.cenere}>{conta(elenco.length, 'progetto', 'progetti')} · {stato(tutte, null)}</Text>
        {elenco.map(p => {
          const dq = daQui(tutte, p)
          return (
            <Box key={`p-${p}`} flexDirection="column">
              <Box gap={2}>
                <Button key={`apri-${p}`} plain label={p} onPress={() => vaiA($, p)} />
                <Text color={C.cenere}>{stato(tutte.filter(aperta), p)}</Text>
              </Box>
              {dq
                ? <Box paddingLeft={2}><Text color={C.inchiostro} wrap="wrap">da qui: #{dq.t.id} {dq.t.titolo}</Text></Box>
                : null}
            </Box>
          )
        })}
        <Text color={C.cenere}>Clicca un progetto o una linguetta per aprirlo.</Text>
      </Box>
    )

    const dq = sel !== 'tutti' ? daQui(tutte, sel) : null
    const titoliGruppo: Record<string, string> = { tu: 'TOCCA A TE', decidi: 'DECIDI TU', io: 'FACCIO IO', fermo: 'FERMO' }
    let gruppoPrima = ''

    const corpoProgetto = (
      <Box flexDirection="column">
        <Text color={C.cenere}>{sel} · {stato(tutte, sel)}</Text>
        {dq ? <Text color={C.sera} bold wrap="wrap">Da qui: #{dq.t.id} {dq.t.titolo}, {dq.motivo}</Text> : null}
        <Text> </Text>
        {rr.length === 0 ? <Text color={C.cenere}>Niente di aperto in {sel}.</Text> : null}
        {rr.map(r => {
          const g = gruppo(r.t)
          const intesta = !c && g !== gruppoPrima
          gruppoPrima = g
          const sua = r.t.id === attiva
          const att = attende(r.t, tutte)
          const destra = c
            ? chiTesto(r.t)
            : r.t.stato === 'fermo' ? (r.t.motivo ?? '') : att.length > 0 ? `aspetta ${att.map(n => `#${n}`).join(', ')}` : scadenza(r.t.giorni)
          const rosso = scaduta(r.t) && !c
          return (
            <Box key={`r-${r.t.id}`} flexDirection="column">
              {intesta ? <Text bold color={g === 'fermo' ? C.blocca : g === 'io' ? C.passa : C.sera}>{titoliGruppo[g]}</Text> : null}
              <Box justifyContent="space-between" gap={1}>
                <Box gap={1} flexShrink={1}>
                  <Text bold color={C.sera}>{sua ? '›' : ' '}</Text>
                  <Text color={C.cenere}>{`#${r.t.id}`.padEnd(4)}</Text>
                  <Text color={C.cenere}>{r.prefisso}</Text>
                  <Button key={`sel-${r.t.id}`} plain label={r.t.titolo} onPress={() => update($, scelto, () => r.t.id)} />
                </Box>
                <Text color={rosso ? C.blocca : C.cenere} bold={rosso}>{destra}</Text>
              </Box>
              {c && scaduta(r.t)
                ? <Box paddingLeft={7}><Text color={C.blocca} bold>{scadenza(r.t.giorni)}</Text></Box>
                : null}
            </Box>
          )
        })}
      </Box>
    )

    const piede = (
      <Box flexDirection="column" borderStyle="single" borderColor={C.cenere} paddingX={1}>
        {sel !== 'tutti' ? (
          <Box gap={2} flexWrap="wrap">
            <Button key="fatto" plain hotkey="f" label="fatto"
              onPress={() => cambia($, t => ({ ...t, stato: 'fatto' }), t => `Fatto: #${t.id} ${t.titolo}.`)} />
            <Button key="ferma" plain hotkey="s" label="ferma o riprendi"
              onPress={() => cambia($, t => ({ ...t, stato: t.stato === 'fermo' ? 'da fare' : 'fermo', motivo: t.stato === 'fermo' ? null : 'fermato da te' }), t => `#${t.id}: ${t.stato}.`)} />
            <Button key="chi" plain hotkey="c" label="chi lo fa"
              onPress={() => cambia($, t => ({ ...t, chi: t.chi === 'tu' ? 'decidi' : t.chi === 'decidi' ? 'io' : 'tu' }), t => `#${t.id}: ${chiTesto(t)}.`)} />
            <Button key="giu" plain hotkey="j" label="giù" onPress={() => sposta($, 1)} />
            <Button key="su" plain hotkey="k" label="su" onPress={() => sposta($, -1)} />
          </Box>
        ) : null}
        <Box gap={2} flexWrap="wrap">
          <Button key="ripristina" plain hotkey="r" label="ripristina i dati" onPress={() => ripristina($)} />
          <Text color={C.cenere}>Prova con dati di esempio. Esc torna al prompt.</Text>
        </Box>
      </Box>
    )

    return (
      <Box flexDirection="column" gap={1} backgroundColor={C.tela} paddingX={1} paddingY={1} flexGrow={1}>
        {testa}
        {linguette}
        {ultimo ? <Text color={C.passa} wrap="wrap">{ultimo}</Text> : null}
        {sel === 'tutti' ? corpoTutti : corpoProgetto}
        {piede}
      </Box>
    )
  })
}
