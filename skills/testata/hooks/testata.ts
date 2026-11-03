// Logica pura della testata, provata da tests/testata.test.ts.
import type { Aggiornamento, Deriva, Testata } from '../types'

// `git describe --tags --match v*`: "v0.2.0" su un rilascio, "v0.2.0-2-gabc1234" due commit dopo -> "v0.2.0 +2".
// Dal 3/11/2026 i rilasci sono numeri; una copia senza i tag nuovi ha ancora la data ("v2026-11-03"), e passa com'è.
export function versioneArturo(describe: string): string | null {
  const m = /^(v\d{1,4}\.\d{1,4}\.\d{1,6}|v\d{4}-\d{2}-\d{2}(?:\.\d+)?)(?:-(\d+)-g[0-9a-f]+)?$/.exec(describe.trim())
  if (m === null) return null
  return m[2] === undefined ? m[1]! : `${m[1]} +${m[2]}`
}

// Il nome che si legge: "v0.2.0" -> "0.2.0"; "v0.2.0 +8" -> "0.2.0, con 8 modifiche non ancora rilasciate".
export function nomeVersione(v: string): string {
  const m = /^v?([^ ]+)(?: \+(\d+))?$/.exec(v)
  if (m === null) return v
  const nome = /^\d+\.\d+\.\d+$/.test(m[1]!) ? m[1]! : `v${m[1]}`
  if (m[2] === undefined) return nome
  return `${nome}, con ${m[2] === '1' ? '1 modifica non ancora rilasciata' : `${m[2]} modifiche non ancora rilasciate`}`
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
  return righe.join('\n')
}
