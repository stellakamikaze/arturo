// Il pannello /dafare: le cose da fare della persona dentro Claude Code.
//
// Legge e scrive solo con la CLI `arturo todo`, lanciata per argv e senza shell. Dopo ogni tasto
// rilegge `arturo todo --json`: il pannello non scrive mai l'archivio da solo. Un errore della CLI
// compare in italiano e non cambia niente. Ogni tasto che cambia un todo si annulla con "u"; il tasto
// "o" apre una sessione con `arturo sessione` e non cambia niente.
//
// Tre schermate (5/11/2026, #3887): con 50 progetti una lista piatta non si legge.
//   Adesso    i progetti che chiedono la persona o sono a rischio, col todo da cui partire, poi le scadute;
//   Progetti  un progetto per riga, con la parola di stato, la frase e quante cose ha;
//   progetto  la catena dei todo legati da "dopo", poi gli altri todo per gruppo, coi tasti dei verbi.
// I progetti vengono dal blocco "progetti" della vista (bin/todo_store.py, docs/fonte-task.md). Una
// fonte esterna che non lo manda: il pannello li ricava dai gruppi e dice che la frase è calcolata.

import { atom, read, update } from 'claude-code'
import type { EngineInterface, Register } from 'claude-code'

import { type Avanti, type Evento, parteSpenta, radiceCodice } from '../parti'
import type { Annullabile, Esito, Parola, Progetto, Schermata, TodoVoce, Vista } from '../../types'
import { titolo, VERBI } from './verbi.mjs'

const PANE = 'dafare'
// La CLI sta nella radice di Arturo: <radice>/bin/arturo (radiceCodice di parti.ts).
const CLI_REL = '/bin/arturo'
const VERSIONE_VISTA = 1
const MAX_ANNULLI = 10
// Adesso mostra al massimo tante scadute: le altre stanno nei loro progetti.
const MAX_SCADUTE = 10
// Fino a tanti progetti il pannello apre la lista dei progetti, non Adesso.
const POCHI_PROGETTI = 3
// La stella di Arturo, solo come segno nella barra.
const STELLA = '★'
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
const COLORE_PAROLA: Record<Parola, string> = { 'a rischio': C.blocca, 'chiede te': C.sera, fermo: C.cenere, va: C.passa }
const PAROLE: Parola[] = ['a rischio', 'chiede te', 'fermo', 'va']

const vista = atom({ plugin: 'arturo', key: 'vista' } as const, null)
const errore = atom({ plugin: 'arturo', key: 'errore' } as const, '')
const esito = atom({ plugin: 'arturo', key: 'esito' } as const, null)
const scelto = atom({ plugin: 'arturo', key: 'scelto' } as const, null)
const filtro = atom({ plugin: 'arturo', key: 'filtro' } as const, '')
const schermata = atom({ plugin: 'arturo', key: 'schermata' } as const, 'adesso')
const sceltaLista = atom({ plugin: 'arturo', key: 'sceltaLista' } as const, null)
const chiusiQui = atom({ plugin: 'arturo', key: 'chiusiQui' } as const, [])
const annullabili = atom({ plugin: 'arturo', key: 'annullabili' } as const, [])
const pythonScelto = atom({ plugin: 'arturo', key: 'python' } as const, null)
const barraNascosta = atom({ plugin: 'arturo', key: 'barraNascosta' } as const, false)

type Risposta = { ok: true; stdout: string } | { ok: false; testo: string }
type Riga = { t: TodoVoce; tasto: string }
type Verbo = keyof typeof VERBI
// Una riga di Adesso o di Progetti: premerla apre il progetto, sul todo indicato.
type VoceLista = { chiave: string; progetto: string; todo: number | null }

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

async function cli($: EngineInterface, argomenti: string[], comando = 'todo'): Promise<Risposta> {
  const py = await python($)
  if (!py) return { ok: false, testo: 'Non trovo Python: scrivi a Claude "lancia /setup".' }
  try {
    const r = await $.process.run([...py, radiceCodice($.plugin.root) + CLI_REL, comando, ...argomenti], { timeoutMs: 15000 })
    if (r.exitCode === 0) return { ok: true, stdout: r.stdout }
    const prima = (r.stderr || r.stdout).split('\n').map(x => x.trim()).find(x => x !== '')
    return { ok: false, testo: prima ?? `Il comando arturo ${comando} si è fermato con il codice ${r.exitCode}.` }
  } catch {
    return { ok: false, testo: `Il comando arturo ${comando} non parte: scrivi /diagnosi.` }
  }
}

// Una fonte esterna (docs/fonte-task.md) manda di ogni todo solo id e titolo, e può non mandare versione,
// avvisi e titoli dei gruppi: i campi che il pannello legge prendono un valore vuoto, così il comando
// non salta (review del 7/11/2026, finding 63). Una versione presente e diversa resta un disaccordo.
const GRUPPI: Record<string, [string, string]> = {
  tu: ['TOCCA A TE', 'Lo fai tu.'],
  decidi: ['DECIDI TU, POI FACCIO IO', 'Serve una tua scelta, poi lavora Claude.'],
  io: ['FACCIO IO', 'Lo fa Claude.'],
  fermo: ['FERMO', 'Aspetta qualcosa o qualcuno.'],
}

function testo(x: unknown, altrimenti: string): string {
  return typeof x === 'string' ? x : altrimenti
}

function forseTesto(x: unknown): string | null {
  return typeof x === 'string' && x !== '' ? x : null
}

function numeri(x: unknown): number[] {
  return Array.isArray(x) ? x.filter((n): n is number => typeof n === 'number') : []
}

function testi(x: unknown): string[] {
  return Array.isArray(x) ? x.filter((t): t is string => typeof t === 'string') : []
}

function oggetti(x: unknown): Record<string, unknown>[] {
  return Array.isArray(x) ? x.filter((o): o is Record<string, unknown> => !!o && typeof o === 'object') : []
}

export function normalizzaVista(dato: unknown): Vista | 'versione' | 'forma' {
  if (!dato || typeof dato !== 'object') return 'forma'
  const d = dato as Record<string, unknown>
  if (d.versione !== undefined && d.versione !== VERSIONE_VISTA) return 'versione'
  if (!Array.isArray(d.gruppi)) return 'forma'
  const gruppi = oggetti(d.gruppi).flatMap(g => {
    const tipo = testo(g.tipo, '')
    if (!(tipo in GRUPPI)) return []
    const [titoloGruppo, descrizione] = GRUPPI[tipo]
    const todo = oggetti(g.todo).flatMap(t => {
      if (typeof t.id !== 'number' || typeof t.titolo !== 'string') return []
      const chi = t.chi === 'tu' || t.chi === 'decidi' || t.chi === 'io' ? t.chi : tipo === 'fermo' ? 'io' : tipo
      const voce: TodoVoce = {
        id: t.id,
        titolo: t.titolo,
        progetto: forseTesto(t.progetto) ?? 'generale',
        scadenza: forseTesto(t.scadenza),
        scadenza_testo: forseTesto(t.scadenza_testo),
        giorni: typeof t.giorni === 'number' ? t.giorni : null,
        priorita: testo(t.priorita, 'media'),
        stato: testo(t.stato, 'da fare'),
        quando: testo(t.quando, ''),
        chi: chi as TodoVoce['chi'],
        perche: forseTesto(t.perche),
        motivo: forseTesto(t.motivo),
        gruppo: tipo as TodoVoce['gruppo'],
        dopo: numeri(t.dopo),
        attende: numeri(t.attende),
        note: testi(t.note),
      }
      return [voce]
    })
    return [{ tipo: tipo as Vista['gruppi'][number]['tipo'], titolo: testo(g.titolo, titoloGruppo),
      descrizione: testo(g.descrizione, descrizione), todo }]
  })
  const progetti = Array.isArray(d.progetti)
    ? oggetti(d.progetti).filter(p => typeof p.nome === 'string').map(p => ({
        ...(p as unknown as Progetto),
        catena: numeri(p.catena),
        da_dove: p.da_dove && typeof p.da_dove === 'object' ? (p.da_dove as Progetto['da_dove']) : null,
      }))
    : undefined
  return {
    versione: VERSIONE_VISTA,
    oggi: testo(d.oggi, ''),
    progetto: forseTesto(d.progetto),
    gruppi,
    ...(progetti ? { progetti } : {}),
    chiusi: typeof d.chiusi === 'number' ? d.chiusi : 0,
    avvisi: testi(d.avvisi),
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
  const v = normalizzaVista(dato)
  // La versione prima della forma: una CLI nuova può cambiare la forma, e il pannello vecchio non
  // deve scrivere partendo dalla vista di prima.
  if (v === 'versione') {
    await update($, vista, () => null)
    await update($, errore, () => 'Il pannello e la CLI non vanno d\'accordo: scrivi /aggiorna.')
    return
  }
  if (v === 'forma') {
    await update($, errore, () => 'La CLI dei todo ha risposto in un formato che il pannello non legge.')
    return
  }
  await update($, vista, () => v)
  await update($, errore, () => '')
}

// Le righe su cui agiscono i verbi: solo dentro un progetto aperto.
async function righeOra($: EngineInterface): Promise<Riga[]> {
  if ((await read($, schermata)) !== 'progetto') return []
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

// Una finestra nuova del terminale con Claude già partito sul todo scelto (Computer Club N.3,
// 27/10/2026: "clicco e vado avanti"). Il todo non cambia: niente da annullare.
async function apriSessione($: EngineInterface): Promise<void> {
  const t = await sceltaOra($)
  if (!t) {
    await dici($, 'Non ci sono righe da scegliere.', false)
    return
  }
  // Col titolo atteso, come gli altri tasti: dopo un merge lo stesso numero può essere un altro todo.
  const r = await cli($, ['--todo', String(t.id), titolo(t)], 'sessione')
  await dici($, r.ok ? `Aperta una sessione nuova su #${t.id}: guarda la finestra del terminale.` : r.testo, r.ok)
}

async function annulla($: EngineInterface): Promise<void> {
  const pila = await read($, annullabili)
  const ultimo = pila[pila.length - 1]
  if (!ultimo) {
    await dici($, 'Niente da annullare.', false)
    return
  }
  const r = await cli($, ultimo.argv)
  // Il passo esce dalla pila anche se l'inverso fallisce: un passo che non si annulla non deve
  // bloccare "u" sugli annulli più vecchi.
  await update($, annullabili, p => p.slice(0, -1))
  if (!r.ok) {
    await dici($, `Non riesco ad annullare ${ultimo.descrizione} e lo salto: il prossimo u annulla il passo prima. La CLI dice: ${r.testo}`, false)
    return
  }
  await update($, chiusiQui, lista => lista.filter(x => x.id !== ultimo.id))
  await update($, scelto, () => ultimo.id)
  await carica($)
  await dici($, `Annullato: ${ultimo.descrizione}.`, true)
}

// j e k: dentro un progetto scorrono i todo, in Adesso e in Progetti le righe della lista.
async function sposta($: EngineInterface, passo: number): Promise<void> {
  const dove = await read($, schermata)
  if (dove === 'progetto') {
    const tutte = await righeOra($)
    if (tutte.length === 0) return
    const id = await read($, scelto)
    const i = Math.max(0, tutte.findIndex(r => r.t.id === id))
    const dopo = tutte[Math.min(tutte.length - 1, Math.max(0, i + passo))]
    if (dopo) await update($, scelto, () => dopo.t.id)
    return
  }
  const voci = vociLista(await read($, vista), dove)
  if (voci.length === 0) return
  const chiave = await read($, sceltaLista)
  const i = Math.max(0, voci.findIndex(x => x.chiave === chiave))
  const dopo = voci[Math.min(voci.length - 1, Math.max(0, i + passo))]
  if (dopo) await update($, sceltaLista, () => dopo.chiave)
}

// Apre un progetto, col todo indicato già scelto (quello da cui partire, o la scaduta premuta).
async function apriProgetto($: EngineInterface, nome: string, todo: number | null): Promise<void> {
  await update($, filtro, () => nome)
  await update($, scelto, () => todo)
  await update($, schermata, () => 'progetto')
}

// Il tasto e: apre il progetto della riga scelta in Adesso o in Progetti.
async function entra($: EngineInterface): Promise<void> {
  const dove = await read($, schermata)
  if (dove === 'progetto') return
  const voci = vociLista(await read($, vista), dove)
  const chiave = await read($, sceltaLista)
  const voce = voci.find(x => x.chiave === chiave) ?? voci[0]
  if (voce) await apriProgetto($, voce.progetto, voce.todo)
}

async function vaiA($: EngineInterface, dove: Schermata): Promise<void> {
  await update($, schermata, () => dove)
  await update($, sceltaLista, () => null)
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

function scaduta(t: TodoVoce): boolean {
  return t.giorni !== null && t.giorni < 0
}

// I progetti dal blocco della vista. Se la fonte non lo manda, si ricavano dai gruppi con le regole
// di bin/todo_store.py (parola, riga_calcolata), senza catena: i "dopo" di un'altra fonte non si sanno ordinare.
function progettiDi(v: Vista | null): Progetto[] {
  if (!v) return []
  const lista = aperti(v)
  if (Array.isArray(v.progetti)) {
    // Solo i progetti che hanno davvero todo nei gruppi: i tasti agiscono su quelli.
    const veri = new Set(lista.map(t => t.progetto))
    return v.progetti.filter(p => veri.has(p.nome))
  }
  const per: Map<string, TodoVoce[]> = new Map()
  for (const t of lista) per.set(t.progetto, [...(per.get(t.progetto) ?? []), t])
  const fuori: Progetto[] = []
  for (const [nome, sue] of per) {
    const scaduti = sue.filter(scaduta).length
    const chiedono = sue.filter(t => t.gruppo === 'tu' || t.gruppo === 'decidi').length
    const fermi = sue.filter(t => t.gruppo === 'fermo').length
    const parola: Parola = scaduti > 0 ? 'a rischio' : chiedono > 0 ? 'chiede te' : fermi === sue.length ? 'fermo' : 'va'
    const partenza = sue.find(t => t.gruppo !== 'fermo' && t.attende.length === 0)
    fuori.push({
      nome, parola, riga: rigaCalcolata(sue.length, scaduti, chiedono, fermi), calcolato: true, scritto: null,
      eta_gg: null, vecchio: false, aperti: sue.length, scaduti, chiedono_te: chiedono, fermi, catena: [],
      da_dove: partenza ? { id: partenza.id, motivo: '' } : null,
    })
  }
  return fuori.sort((a, b) => PAROLE.indexOf(a.parola) - PAROLE.indexOf(b.parola) || a.nome.localeCompare(b.nome))
}

function rigaCalcolata(n: number, scaduti: number, chiedono: number, fermi: number): string {
  const pezzi = [n === 1 ? '1 todo aperto' : `${n} todo aperti`]
  if (scaduti) pezzi.push(scaduti === 1 ? '1 scaduto' : `${scaduti} scaduti`)
  if (chiedono) pezzi.push(chiedono === 1 ? '1 chiede te' : `${chiedono} chiedono te`)
  if (fermi) pezzi.push(fermi === 1 ? '1 fermo' : `${fermi} fermi`)
  return pezzi.join(', ') + '.'
}

// Principio 4 di PRODUCT.md: una frase calcolata o vecchia lo dice.
function provenienza(p: Progetto): string {
  if (p.calcolato) return 'calcolata dai todo'
  if (p.vecchio && p.eta_gg !== null) return `scritta ${p.eta_gg} giorni fa`
  return ''
}

function urgenti(ps: Progetto[]): Progetto[] {
  return ps.filter(p => p.parola === 'a rischio' || p.parola === 'chiede te')
}

// Le scadute di tutti i progetti, la più vecchia prima.
function tutteScadute(v: Vista | null): TodoVoce[] {
  return aperti(v).filter(scaduta).sort((a, b) => (a.giorni ?? 0) - (b.giorni ?? 0) || a.id - b.id)
}

// Le righe premibili di Adesso e di Progetti, nell'ordine in cui si vedono.
function vociLista(v: Vista | null, dove: Schermata): VoceLista[] {
  const ps = progettiDi(v)
  if (dove === 'progetti') return ps.map(p => ({ chiave: `progetto-${p.nome}`, progetto: p.nome, todo: p.da_dove?.id ?? null }))
  if (dove !== 'adesso') return []
  return [
    ...urgenti(ps).map(p => ({ chiave: `adesso-${p.nome}`, progetto: p.nome, todo: p.da_dove?.id ?? null })),
    ...tutteScadute(v).slice(0, MAX_SCADUTE).map(t => ({ chiave: `scaduta-${t.id}`, progetto: t.progetto, todo: t.id })),
  ]
}

// I todo di un progetto: prima la catena, nell'ordine dei passi, poi gli altri nell'ordine dei gruppi.
function righe(v: Vista | null, nome: string): Riga[] {
  const sue = aperti(v).filter(t => t.progetto === nome)
  const passi = catenaDi(v, nome)
  const fuori = [...passi, ...sue.filter(t => !passi.includes(t))]
  return fuori.map((t, i) => ({ t, tasto: i < 9 ? String(i + 1) : '' }))
}

function catenaDi(v: Vista | null, nome: string): TodoVoce[] {
  const p = progettiDi(v).find(x => x.nome === nome)
  const sue = aperti(v).filter(t => t.progetto === nome)
  return (p?.catena ?? []).map(id => sue.find(t => t.id === id)).filter((t): t is TodoVoce => t !== undefined)
}

// La schermata con cui si apre /dafare senza argomenti: con un progetto solo, quel progetto; con
// pochi, la lista; con tanti, Adesso.
function partenza(v: Vista | null): { dove: Schermata; nome: string } {
  const ps = progettiDi(v)
  if (ps.length === 1) return { dove: 'progetto', nome: ps[0]!.nome }
  if (ps.length > 0 && ps.length <= POCHI_PROGETTI) return { dove: 'progetti', nome: '' }
  return { dove: 'adesso', nome: '' }
}

function quante(n: number): string {
  return n === 1 ? '1 cosa da fare' : `${n} cose da fare`
}

function quantiProgetti(n: number): string {
  return n === 1 ? '1 progetto' : `${n} progetti`
}

// Testata e barra dicono le scadute con la stessa forma: niente, "1 scaduta", "N scadute".
function quanteScadute(lista: TodoVoce[]): string {
  const k = lista.filter(scaduta).length
  return k === 0 ? '' : k === 1 ? '1 scaduta' : `${k} scadute`
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

const AIUTO = 'Tasti: v passa fra Adesso e Progetti, p apre la lista dei progetti, un numero apre un progetto. Dentro un progetto: numero o j/k per scegliere, o apre una sessione sul todo, f fatto, s ferma, r riprendi, c chi lo fa, a avvicina, l allontana, u annulla. Esc chiude.'

export async function avvio($: EngineInterface, e: Evento<'session.start'>, next: Avanti<'session.start'>) {
  if (await parteSpenta($, 'dafare')) return next(e)
  await $.command.register({
    name: 'dafare',
    description: 'Apre il pannello delle tue cose da fare',
    argumentHint: '[progetto | nascondi | mostra]',
  })
  await rileggi($)
  return next(e)
}

export async function fineTurno($: EngineInterface, e: Evento<'turn.complete'>, next: Avanti<'turn.complete'>) {
  if (await parteSpenta($, 'dafare')) return next(e)
  const r = await next(e)
  await carica($)
  return r
}

// /clear e /resume chiudono la sessione senza rilanciare session.start: la scelta della barra e la
// vista si rileggono qui, altrimenti "/dafare nascondi" si perde (19/10/2026). Il secondo dopo cade
// nella sessione nuova. Mai classic.SessionStart: il plugin di sistema cc-plugin-sec-default lo
// scavalca e all'avvio compare "classic.SessionStart hook was skipped" (4/11/2026).
// /branch resta fuori di proposito: session.end non ha un motivo suo per lui (i motivi sono clear,
// resume, logout, prompt_input_exit e other). Se Claude Code lo chiude come resume, la rilettura parte.
// session.end non ha matcher: lo registra hooks/register.tsx, in catena con le altre parti.
export async function fineSessione($: EngineInterface, e: Evento<'session.end'>, next: Avanti<'session.end'>) {
  if (await parteSpenta($, 'dafare')) return next(e)
  const r = await next(e)
  if (e.reason !== 'clear' && e.reason !== 'resume') return r
  $.clock.after(1_000, () => void rileggi($).catch(() => undefined))
  return r
}

// La scelta della barra dallo store, poi la vista: all'avvio e dopo /clear o /resume.
async function rileggi($: EngineInterface): Promise<void> {
  const nascosta = (await $.store.get('barraNascosta')) === true
  await update($, barraNascosta, () => nascosta)
  await carica($)
}

export const register: Register = on => {

  on('command.run', { command: 'dafare' }, async ($, e, next) => {
    if (await parteSpenta($, 'dafare')) return next(e)
    const arg = e.args.trim()
    if (arg === 'nascondi') {
      await barra($, true)
      return { text: 'La riga sopra il prompt è spenta. La riaccendi con /dafare mostra.' }
    }
    if (arg === 'mostra') {
      await barra($, false)
      return { text: 'La riga sopra il prompt è accesa.' }
    }
    await carica($)
    const v = await read($, vista)
    const problema = await read($, errore)
    const inizio = arg ? { dove: 'progetto' as const, nome: arg } : partenza(v)
    await update($, schermata, () => inizio.dove)
    await update($, filtro, () => inizio.nome)
    await update($, scelto, () => null)
    await update($, sceltaLista, () => null)
    await apri($)
    if (!v) return { text: `Pannello aperto, ma non leggo le cose da fare. ${problema}` }
    const n = arg ? righe(v, arg).length : aperti(v).length
    const dove = arg ? ` in ${arg}` : ''
    return { text: n === 0 ? `Pannello aperto: non hai cose da fare segnate${dove}.` : `Pannello aperto: ${quante(n)}${dove}. ${AIUTO}` }
  })

  // Claude può aver usato la CLI nel turno: a fine turno il pannello e la barra rileggono.

  on('ui.render', { component: 'Pane', requestId: PANE }, async ($, e, next) => {
    if (await parteSpenta($, 'dafare')) return next(e)
    const { Box, Text, Button } = $.ui.resolve(e)
    const v = await read($, vista)
    const problema = await read($, errore)
    const ultimo = await read($, esito)
    const dove = await read($, schermata)
    const nome = await read($, filtro)
    const chiusi = await read($, chiusiQui)
    const ps = progettiDi(v)
    const tutti = aperti(v)
    const tutte = dove === 'progetto' ? righe(v, nome) : []
    const id = await read($, scelto)
    const attiva = (tutte.find(r => r.t.id === id) ?? tutte[0])?.t.id
    const voci = vociLista(v, dove)
    const chiave = await read($, sceltaLista)
    const attivaLista = (voci.find(x => x.chiave === chiave) ?? voci[0])?.chiave
    const stretto = e.props.bodyColumns < 60
    const p = ps.find(x => x.nome === nome)

    const intestazione = dove === 'adesso' ? 'Adesso' : dove === 'progetti' ? 'I tuoi progetti' : nome
    const testa = !v
      ? ''
      : dove === 'progetto'
        ? [p ? p.parola : '', quante(tutte.length), quanteScadute(tutte.map(r => r.t))].filter(x => x !== '').join(' · ')
        : [quantiProgetti(ps.length), quante(tutti.length), quanteScadute(tutti)].filter(x => x !== '').join(' · ')

    // Una riga di Adesso o di Progetti: il pulsante col numero apre il progetto.
    const rigaLista = (voce: VoceLista, n: number, sopra: string, coloreSopra: string, sotto: string[]) => {
      const sua = voce.chiave === attivaLista
      return (
        <Box flexDirection="column" paddingLeft={1}>
          <Box gap={1}>
            <Text bold color={C.sera}>{sua ? '›' : ' '}</Text>
            {n < 9
              ? <Button key={voce.chiave} plain hotkey={String(n + 1)} label={voce.progetto} onPress={() => apriProgetto($, voce.progetto, voce.todo)} />
              : <Button key={voce.chiave} plain label={voce.progetto} onPress={() => apriProgetto($, voce.progetto, voce.todo)} />}
            <Text bold color={coloreSopra} wrap="wrap">{sopra}</Text>
          </Box>
          {sotto.filter(x => x !== '').map(riga => (
            <Box paddingLeft={6}>
              <Text color={C.cenere} wrap="wrap">{riga}</Text>
            </Box>
          ))}
        </Box>
      )
    }

    const fraseDi = (x: Progetto) => {
      const da = provenienza(x)
      return da ? `${x.riga} (${da})` : x.riga
    }

    const titoloDi = (todo: number | null | undefined) => tutti.find(t => t.id === todo)?.titolo ?? ''

    const adesso = () => {
      const chiedono = urgenti(ps)
      const scad = tutteScadute(v)
      return (
        <Box flexDirection="column" gap={1}>
          {chiedono.length === 0 ? (
            <Text color={C.inchiostro} wrap="wrap">Nessun progetto chiede te, e nessuno è a rischio. Premi v per vederli tutti.</Text>
          ) : (
            <Box flexDirection="column">
              <Text bold color={C.sera} wrap="wrap">CHIEDONO TE O SONO A RISCHIO ({chiedono.length})</Text>
              {stretto ? null : <Text color={C.cenere} wrap="wrap">Il numero apre il progetto sul todo da cui partire.</Text>}
              {chiedono.map((x, i) => rigaLista(
                { chiave: `adesso-${x.nome}`, progetto: x.nome, todo: x.da_dove?.id ?? null }, i, x.parola, COLORE_PAROLA[x.parola],
                [fraseDi(x), x.da_dove ? `parti da #${x.da_dove.id} ${titoloDi(x.da_dove.id)}${x.da_dove.motivo ? `: ${x.da_dove.motivo}` : ''}` : ''],
              ))}
            </Box>
          )}
          {scad.length > 0 ? (
            <Box flexDirection="column">
              <Text bold color={C.blocca} wrap="wrap">SCADUTE ({scad.length})</Text>
              {scad.slice(0, MAX_SCADUTE).map((t, i) => rigaLista(
                { chiave: `scaduta-${t.id}`, progetto: t.progetto, todo: t.id }, chiedono.length + i,
                t.scadenza_testo ?? 'scaduta', C.blocca, [`#${t.id} ${t.titolo}`],
              ))}
              {scad.length > MAX_SCADUTE ? <Text color={C.cenere} wrap="wrap">E altre {scad.length - MAX_SCADUTE}: le trovi nei loro progetti.</Text> : null}
            </Box>
          ) : null}
        </Box>
      )
    }

    const progetti = () => (
      <Box flexDirection="column">
        {ps.map((x, i) => rigaLista(
          { chiave: `progetto-${x.nome}`, progetto: x.nome, todo: x.da_dove?.id ?? null }, i,
          `${x.parola} · ${quante(x.aperti)}`, COLORE_PAROLA[x.parola], [fraseDi(x)],
        ))}
      </Box>
    )

    // Una riga di todo dentro un progetto, con il numero del passo se sta nella catena.
    const rigaTodo = (r: Riga, passo: string) => {
      const sua = r.t.id === attiva
      const sotto = dettagli(r.t, false)
      const scad = scaduta(r.t)
      return (
        <Box flexDirection="column" paddingLeft={1}>
          <Box gap={1}>
            <Text bold color={C.sera}>{sua ? '›' : ' '}</Text>
            {passo ? <Text color={C.cenere}>{passo}</Text> : null}
            {r.tasto
              ? <Button key={`riga-${r.t.id}`} plain hotkey={r.tasto} label={`#${r.t.id}`} onPress={() => update($, scelto, () => r.t.id)} />
              : <Button key={`riga-${r.t.id}`} plain label={`#${r.t.id}`} onPress={() => update($, scelto, () => r.t.id)} />}
            <Text bold={sua} color={sua ? C.sera : C.inchiostro} wrap="wrap">{r.t.titolo}</Text>
          </Box>
          {sotto.length > 0 || r.t.scadenza_testo ? (
            <Box paddingLeft={6} gap={1} flexWrap="wrap">
              {r.t.scadenza_testo ? <Text bold={scad} color={scad ? C.blocca : C.cenere}>{r.t.scadenza_testo}</Text> : null}
              {sotto.length > 0 ? <Text color={C.cenere} wrap="wrap">{sotto.join(' · ')}</Text> : null}
            </Box>
          ) : null}
        </Box>
      )
    }

    const progetto = () => {
      const passi = catenaDi(v, nome)
      const nellaCatena = tutte.filter(r => passi.includes(r.t))
      const altre = tutte.filter(r => !passi.includes(r.t))
      return (
        <Box flexDirection="column" gap={1}>
          {p ? (
            <Box flexDirection="column">
              <Text color={C.inchiostro} wrap="wrap">{fraseDi(p)}</Text>
              {p.da_dove ? (
                <Text color={C.cenere} wrap="wrap">Da dove partire: #{p.da_dove.id} {titoloDi(p.da_dove.id)}{p.da_dove.motivo ? `. ${p.da_dove.motivo}` : ''}</Text>
              ) : null}
            </Box>
          ) : null}
          {tutte.length === 0 ? (
            <Text color={C.cenere} wrap="wrap">Nessuna cosa da fare in {nome}. Premi p per la lista dei progetti.</Text>
          ) : null}
          {nellaCatena.length > 0 ? (
            <Box flexDirection="column">
              <Text bold color={C.sera} wrap="wrap">LA CATENA ({nellaCatena.length})</Text>
              {stretto ? null : <Text color={C.cenere} wrap="wrap">I passi legati da "dopo", nell'ordine in cui si fanno.</Text>}
              {nellaCatena.map((r, i) => rigaTodo(r, `${i + 1}.`))}
            </Box>
          ) : null}
          {v
            ? v.gruppi.map(g => {
                const dentro = altre.filter(r => r.t.gruppo === g.tipo)
                if (dentro.length === 0) return null
                const colore = COLORE_GRUPPO[g.tipo] ?? C.inchiostro
                return (
                  <Box flexDirection="column">
                    <Text bold color={colore} wrap="wrap">{g.titolo} ({dentro.length})</Text>
                    {stretto ? null : <Text color={C.cenere} wrap="wrap">{g.descrizione}</Text>}
                    {dentro.map(r => rigaTodo(r, ''))}
                  </Box>
                )
              })
            : null}
        </Box>
      )
    }

    const piede = (
      <Box flexDirection="column" borderStyle="single" borderColor={C.cenere} paddingX={1}>
        {v ? (
          <Box flexDirection="column">
            {tutte.length > 0 ? (
              <Box gap={2} flexWrap="wrap">
                {(Object.keys(VERBI) as Verbo[]).map(verbo => (
                  <Button key={verbo} plain hotkey={VERBI[verbo]!.tasto} label={VERBI[verbo]!.etichetta} onPress={() => agisci($, verbo)} />
                ))}
                <Button key="sessione" plain hotkey="o" label="apri sessione" onPress={() => apriSessione($)} />
              </Box>
            ) : null}
            <Box gap={2} flexWrap="wrap">
              <Button key="annulla" plain hotkey="u" label="annulla" onPress={() => annulla($)} />
              <Button key="vista" plain hotkey="v" label={dove === 'adesso' ? 'progetti' : 'adesso'} onPress={() => vaiA($, dove === 'adesso' ? 'progetti' : 'adesso')} />
              {dove !== 'progetti' ? <Button key="progetti" plain hotkey="p" label="lista dei progetti" onPress={() => vaiA($, 'progetti')} /> : null}
              {dove !== 'progetto' && voci.length > 0 ? <Button key="entra" plain hotkey="e" label="apri il progetto" onPress={() => entra($)} /> : null}
              {(dove === 'progetto' ? tutte.length : voci.length) > 1 ? <Button key="giu" plain hotkey="j" label="giù" onPress={() => sposta($, 1)} /> : null}
              {(dove === 'progetto' ? tutte.length : voci.length) > 1 ? <Button key="su" plain hotkey="k" label="su" onPress={() => sposta($, -1)} /> : null}
            </Box>
          </Box>
        ) : null}
        <Text color={C.cenere} wrap="wrap">Esc chiude. Se i tasti non rispondono: ctrl+x tab, oppure /dafare.</Text>
      </Box>
    )

    return (
      <Box flexDirection="column" gap={1} backgroundColor={C.tela} paddingX={stretto ? 1 : 2} paddingY={1} flexGrow={1}>
        <Box flexDirection="column">
          <Text bold color={C.inchiostro} wrap="wrap">{intestazione}</Text>
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
        {v && tutti.length === 0 ? (
          <Box flexDirection="column">
            <Text color={C.inchiostro} wrap="wrap">Non hai cose da fare segnate.</Text>
            <Text color={C.cenere} wrap="wrap">Di' a Claude: ricordami di…</Text>
          </Box>
        ) : null}
        {v && tutti.length > 0 ? (dove === 'adesso' ? adesso() : dove === 'progetti' ? progetti() : progetto()) : null}
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

  // La barra conta le cose da fare di tutti i progetti, e dice quando la fonte non risponde: la
  // vista resta quella dell'ultima lettura buona.
  on('ui.render', { component: 'AbovePrompt' }, async ($, e, next) => {
    if (await parteSpenta($, 'dafare')) return next(e)
    const v = await read($, vista)
    const lista = aperti(v)
    if (e.props.hasSurvey || (await read($, barraNascosta)) || lista.length === 0) return next(e)
    const { Box, Text, Button } = $.ui.resolve(e)
    const muta = (await read($, errore)) !== ''
    const corto = e.props.bodyColumns < 60
    const testo = corto
      ? `${quante(lista.length)} · /dafare`
      : [quante(lista.length), quanteScadute(lista), muta ? 'non riesco a rileggerle' : '', '/dafare per vederle']
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
