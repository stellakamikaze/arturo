// Logica pura della testata, provata da tests/testata.test.ts.
import type { Aggiornamento, Blocco, Deriva, Invito, Testata, Timbro } from '../../types'

// `git describe --tags --match v*`: "v0.2.0" su un rilascio, "v0.2.0-2-gabc1234" due commit dopo -> "v0.2.0 +2".
// Dal 3/11/2026 i rilasci sono numeri; una copia senza i tag nuovi ha ancora la data ("v2026-11-03"), e passa com'è.
export function versioneArturo(describe: string): string | null {
  const m = /^(v\d{1,4}\.\d{1,4}\.\d{1,6}|v\d{4}-\d{2}-\d{2}(?:\.\d+)?)(?:-(\d+)-g[0-9a-f]+)?$/.exec(describe.trim())
  if (m === null) return null
  return m[2] === undefined ? m[1]! : `${m[1]} +${m[2]}`
}

// Col plugin non c'è git: la versione è quella che bin/impacchetta.py scrive in .claude-plugin/plugin.json,
// senza la v ("0.2.8"). Review del 7/11/2026, finding 68: senza, /versione diceva solo "Arturo".
export function versioneDaManifest(json: string): string | null {
  try {
    const v = (JSON.parse(json) as { version?: unknown }).version
    return typeof v === 'string' ? versioneArturo(`v${v.replace(/^v/, '')}`) : null
  } catch {
    return null
  }
}

// Il nome che si legge: "v0.2.0" -> "0.2.0"; "v0.2.0 +8" -> "0.2.0, con 8 modifiche non ancora rilasciate".
export function nomeVersione(v: string): string {
  const m = /^v?([^ ]+)(?: \+(\d+))?$/.exec(v)
  if (m === null) return v
  const nome = /^\d+\.\d+\.\d+$/.test(m[1]!) ? m[1]! : `v${m[1]}`
  if (m[2] === undefined) return nome
  return `${nome}, con ${modifiche(m[2])}`
}

function modifiche(n: string): string {
  return n === '1' ? '1 modifica non ancora rilasciata' : `${n} modifiche non ancora rilasciate`
}

function testo(v: unknown, max: number): string {
  return typeof v === 'string' ? v.replace(/[\x00-\x1f\x7f]/g, '').slice(0, max) : ''
}

function elenco(v: unknown): string[] {
  return Array.isArray(v) ? v.filter((x): x is string => typeof x === 'string').map(x => testo(x, 120)) : []
}

export function leggiDeriva(json: string): Deriva | null {
  try {
    const d = JSON.parse(json) as Record<string, unknown>
    if (typeof d.misurata !== 'boolean') return null
    return { misurata: d.misurata, file: elenco(d.file), guardie: elenco(d.guardie), hook: elenco(d.hook), config: elenco(d.config) }
  } catch {
    return null
  }
}

export function leggiAggiornamento(json: string): Aggiornamento | null {
  try {
    const d = JSON.parse(json) as Record<string, unknown>
    const versione = testo(d.versione, 30)
    if (versione === '' || typeof d.stato !== 'string') return null
    return { stato: d.stato, versione, compromesso: d.compromesso === true, non_verificabile: d.non_verificabile === true }
  } catch {
    return null
  }
}

// La deriva in poche parole: quella che conta per prima. null = non si dice niente.
export function parolaDeriva(d: Deriva | null): string | null {
  if (d === null || !d.misurata) return null
  if (d.hook.includes('tutti')) return 'deriva: hook spenti'
  if (d.hook.length > 0) return `deriva: ${d.hook.length === 1 ? '1 hook di Arturo manca' : `${d.hook.length} hook di Arturo mancano`}`
  if (d.config.length > 0) return 'deriva: config da riparare'
  if (d.guardie.length > 0) return `deriva: ${d.guardie.length === 1 ? '1 guardia cambiata' : `${d.guardie.length} guardie cambiate`}`
  if (d.file.length > 0) return `deriva: ${d.file.length === 1 ? '1 file di Arturo cambiato' : `${d.file.length} file di Arturo cambiati`}`
  return 'deriva: nessuna'
}

export function parolaAggiornamento(a: Aggiornamento | null): string | null {
  if (a === null) return null
  const v = nomeVersione(a.versione)
  if (a.compromesso) return `${v} non verificato: segnala a chi mantiene Arturo`
  if (a.stato === 'pronto') return `↑ ${v} si installa alla chiusura`
  if (a.non_verificabile) return `↑ ${v}: aggiorna git e OpenSSH`
  if (a.stato === 'manuale' || a.stato === 'bloccato') return `↑ ${v}: serve /aggiorna`
  return null
}

export function riga(t: Testata): string {
  const pezzi = [t.arturo === null ? 'Arturo' : `Arturo ${nomeVersione(t.arturo)}`]
  if (t.claude !== null) pezzi.push(`Claude Code ${t.claude}`)
  const deriva = parolaDeriva(t.deriva)
  if (deriva !== null) pezzi.push(deriva)
  const agg = parolaAggiornamento(t.aggiornamento)
  if (agg !== null) pezzi.push(agg)
  return pezzi.join(' · ')
}

// /versione: la riga e, sotto, cosa c'è dietro la deriva.
export function dettaglio(t: Testata): string {
  const righe = [riga(t)]
  const d = t.deriva
  if (d !== null && d.misurata) {
    if (d.hook.length > 0) righe.push(`hook di Arturo che non girano: ${d.hook.join(', ')}`)
    if (d.config.length > 0) righe.push(`config: ${d.config.join(', ')}`)
    if (d.file.length > 0) righe.push(`file di Arturo cambiati: ${d.file.slice(0, 8).join(', ')}${d.file.length > 8 ? '…' : ''}`)
  }
  if (d === null || !d.misurata) righe.push('deriva: non misurata (la misura l\'avvio della sessione, se la config ha un riferimento ad Arturo)')
  righe.push(CREDITO)
  return righe.join('\n')
}

// ---------- il blocco gemello: tre righe sotto l'intestazione di Claude Code ----------
// Stessa forma dell'intestazione: nome e versione, poi una riga di stato, poi i link.

const MESI = ['gennaio', 'febbraio', 'marzo', 'aprile', 'maggio', 'giugno', 'luglio', 'agosto', 'settembre',
  'ottobre', 'novembre', 'dicembre']

function dataLunga(iso: string): string {
  const [anno, mese, giorno] = iso.split('-')
  return `${Number(giorno)} ${MESI[Number(mese) - 1]} ${anno}`
}

// Cosa dice la riga di stato sulla versione. "v0.2.0 +8" -> "8 modifiche non ancora rilasciate"; un rilascio
// numerato non ha niente da aggiungere, il numero sta già accanto al nome. Una copia vecchia, ancora a data:
// "v2026-11-03" -> "aggiornato il 3 novembre 2026".
export function parolaVersione(v: string | null): string | null {
  if (v === null) return null
  const n = /^v\d+\.\d+\.\d+(?: \+(\d+))?$/.exec(v)
  if (n !== null) return n[1] === undefined ? null : modifiche(n[1])
  const m = /^v(\d{4}-\d{2}-\d{2})(?:\.\d+)?(?: \+(\d+))?$/.exec(v)
  if (m === null) return null
  return m[2] === undefined ? `aggiornato il ${dataLunga(m[1]!)}` : modifiche(m[2])
}

// Lo stato in una frase che si capisce. null = niente da dire (la riga resta corta).
export function statoChiaro(t: Testata): string | null {
  const a = t.aggiornamento
  if (a !== null) {
    const quando = /^v(\d{4}-\d{2}-\d{2})/.exec(a.versione)
    const nuova = quando === null ? `la versione ${nomeVersione(a.versione)}` : `la versione del ${dataLunga(quando[1]!)}`
    if (a.compromesso) return `${nuova} non ha una firma valida: non aggiornare e scrivi /segnala`
    if (a.stato === 'pronto') return `${nuova} si installa quando chiudi la sessione`
    if (a.non_verificabile) return `c'è ${nuova}, ma prima vanno aggiornati git e OpenSSH`
    if (a.stato === 'manuale' || a.stato === 'bloccato') return `c'è ${nuova}: scrivi /aggiorna`
  }
  const d = t.deriva
  if (d === null || !d.misurata) return null
  const n = (k: number, uno: string, tanti: string) => (k === 1 ? uno : tanti.replace('#', String(k)))
  if (d.hook.includes('tutti')) return 'i controlli di Arturo sono spenti: scrivi /diagnosi'
  if (d.hook.length > 0) return `${n(d.hook.length, 'un controllo di Arturo non parte', '# controlli di Arturo non partono')}: scrivi /diagnosi`
  if (d.config.length > 0) return 'la configurazione va riparata: scrivi /diagnosi'
  if (d.guardie.length > 0) return `${n(d.guardie.length, 'hai cambiato una guardia', 'hai cambiato # guardie')} di Arturo: /versione le elenca`
  if (d.file.length > 0) return `${n(d.file.length, 'hai cambiato un file', 'hai cambiato # file')} di Arturo: /versione li elenca`
  return 'configurazione in ordine'
}

export function blocco(t: Testata, invito: Invito): Blocco {
  const stato = [parolaVersione(t.arturo), statoChiaro(t)].filter((x): x is string => x !== null)
  return {
    // Accanto al nome solo il numero: le modifiche non rilasciate le dice la riga di stato.
    versione: t.arturo === null ? null : nomeVersione(t.arturo.replace(/ \+\d+$/, '')),
    stato: stato.length > 0 ? stato.join(' · ') : null,
    roadmap: parolaInvito(invito),
    roadmapNuova: invito !== null,
  }
}

// Arturo in pixel: una stella a quattro punte in blocchi, tre righe come la mascotte di Claude Code.
// Ogni fotogramma è [riga alta, riga di mezzo, riga bassa]; le due stelle piccole blu le aggiunge stella.tsx
// in fondo alla riga alta e in testa alla riga bassa. Grande, grande, media, piccola, media: pulsa.
const GRANDE = ['   \u2597\u2588\u2596  ', '\u2597\u2584\u2584\u2588\u2588\u2588\u2584\u2584\u2596', '  \u259d\u2588\u2598   ']
const MEDIA = ['    \u2584   ', '  \u2584\u2588\u2588\u2588\u2584  ', '   \u2580    ']
const PICCOLA = ['        ', '   \u2597\u2588\u2596   ', '        ']
export const FOTOGRAMMI_STELLA: ReadonlyArray<readonly [string, string, string]> = [GRANDE, GRANDE, MEDIA, PICCOLA, MEDIA]
  .map(f => [f[0]!, f[1]!, f[2]!] as const)
export const PASSO_MS = 450
export const FOTOGRAMMI_TOTALI = 45 // circa 20 secondi, poi la stella resta grande e ferma
export const PUNTO = String.fromCodePoint(0x00b7)
export const LARGHEZZA_MARCHIO = 11

// Sotto questa larghezza il marchio non ci sta accanto al testo: restano le righe.
export const COLONNE_MARCHIO = 60

export const URL_ROADMAP = 'https://arturo.stellakamikaze.org/roadmap/'
export const URL_INVIA = 'https://arturo.stellakamikaze.org/'
// Il credito di Arturo, nella testata e in /versione (9/11/2026).
export const AUTORE = 'Federico Nejrotti'
export const URL_AUTORE = 'https://stellakamikaze.org/'
export const CREDITO = `Arturo è un progetto di ${AUTORE} · stellakamikaze.org`
export const INTERVALLO_INVITO_S = 14 * 24 * 60 * 60

// "Aggiornata il 2026-11-03" in testa a ROADMAP.md.
export function dataRoadmap(md: string): string | null {
  const m = /^Aggiornata il (\d{4}-\d{2}-\d{2})\s*$/m.exec(md)
  return m === null ? null : m[1]!
}

export function leggiTimbro(json: string): Timbro | null {
  try {
    const d = JSON.parse(json) as Record<string, unknown>
    if (d === null || typeof d !== 'object') return null
    return {
      data: typeof d.data === 'string' ? d.data : undefined,
      mostrata: typeof d.mostrata === 'number' && Number.isFinite(d.mostrata) ? d.mostrata : undefined,
      pausa: d.pausa === 'sempre' ? 'sempre' : undefined,
    }
  } catch {
    return null
  }
}

// Si mette in evidenza se la roadmap ha una data nuova, o se dall'ultimo invito sono passate due settimane.
// Senza roadmap leggibile niente evidenza; con un timbro illeggibile si evidenzia e il timbro si riscrive.
export function decidiInvito(data: string | null, timbro: Timbro | null, adessoS: number): 'nuova' | 'promemoria' | null {
  if (data === null) return null
  if (timbro?.pausa === 'sempre') return null
  if (timbro === null || timbro.data !== data) return 'nuova'
  if (timbro.mostrata === undefined || adessoS - timbro.mostrata >= INTERVALLO_INVITO_S) return 'promemoria'
  return null
}

// Il link alla roadmap c'è sempre; l'invito ne cambia solo le parole.
export function parolaInvito(invito: Invito): string {
  if (invito === null) return 'Roadmap'
  if (invito.tipo === 'promemoria') return 'Roadmap: dimmi cosa ne pensi'
  const [, mese, giorno] = invito.data.split('-')
  return `Roadmap aggiornata il ${Number(giorno)}/${Number(mese)}`
}

export function nuovoTimbro(vecchio: Timbro | null, data: string, adessoS: number): string {
  return JSON.stringify({ ...(vecchio?.pausa === 'sempre' ? { pausa: 'sempre' } : {}), data, mostrata: Math.floor(adessoS) })
}
