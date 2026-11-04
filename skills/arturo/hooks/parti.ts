// Le parti del mod arturo: ognuna registra i suoi hook col suo matcher, e apre ogni hook con parteSpenta.
//
// Un mod solo ha un modulo solo, una riga di stato sola e uno store suo (Claude Code 2.1.317). Qui stanno
// le tre cose che le parti condividono: l'interruttore per parte, la riga di stato e la radice del codice.
import type { EngineInterface, EventName, Hook } from 'claude-code'

export const PARTI = ['apri', 'cache-fredda', 'dafare', 'redazione-segreti', 'rotazione', 'testata'] as const
export type Parte = (typeof PARTI)[number]

// ~/.claude/arturo/parti.json, {"spente": ["dafare"]}: una parte spenta non scatta. Senza file sono tutte
// accese. Un file illeggibile o con un nome sconosciuto non spegne niente: l'errore resta lato acceso.
export function leggiSpente(testo: string | null): Set<string> {
  if (testo === null) return new Set()
  try {
    const dati = JSON.parse(testo) as { spente?: unknown }
    if (!Array.isArray(dati.spente)) return new Set()
    return new Set(dati.spente.filter((x): x is string => typeof x === 'string' && (PARTI as readonly string[]).includes(x)))
  } catch {
    return new Set()
  }
}

let spente: Promise<Set<string>> | undefined

async function casa($: EngineInterface): Promise<string> {
  return (await $.env.get('HOME').catch(() => undefined)) ?? (await $.env.get('USERPROFILE').catch(() => undefined)) ?? ''
}

// Letto una volta per caricamento del modulo: cambiare il file vale dalla sessione dopo. ARTURO_PARTI, se c'è,
// vince sul file e accende solo le parti che nomina (ARTURO_PARTI=testata,rotazione): serve a provarne una.
export function soloQueste(valore: string | undefined): Set<string> | null {
  if (valore === undefined || valore.trim() === '') return null
  const accese = new Set(valore.split(',').map(x => x.trim()))
  return new Set(PARTI.filter(p => !accese.has(p)))
}

export function parteSpenta($: EngineInterface, parte: Parte): Promise<boolean> {
  spente ??= $.env.get('ARTURO_PARTI').then(
    v => v,
    () => undefined,
  ).then(async solo => {
    const daEnv = soloQueste(solo)
    if (daEnv !== null) return daEnv
    const home = await casa($).catch(() => '')
    if (home === '') return new Set<string>()
    const t = await $.fs.read(`${home}/.claude/arturo/parti.json`).then(
      x => (typeof x === 'string' ? x : null),
      () => null,
    )
    return leggiSpente(t)
  })
  return spente.then(s => s.has(parte))
}

// La riga sotto il prompt è una per mod: ogni parte scrive la sua voce, la riga le mette in fila.
const voci = new Map<Parte, string>()

export function unisciVoci(v: ReadonlyMap<Parte, string>): string | undefined {
  const testi = PARTI.flatMap(p => (v.get(p) ? [v.get(p) as string] : []))
  return testi.length === 0 ? undefined : testi.join(' · ')
}

export function stato($: EngineInterface, parte: Parte, testo: string | undefined): void {
  if (testo === undefined || testo === '') voci.delete(parte)
  else voci.set(parte, testo)
  $.ui.status(unisciVoci(voci))
}

// La radice del codice di Arturo. Nel clone il mod sta in <radice>/skills/arturo; nel pacchetto plugin di
// bin/impacchetta.py il modulo lo porta il plugin Arturo, e $.plugin.root è già la radice.
export function radiceCodice(radicePlugin: string): string {
  const pulita = radicePlugin.replace(/[\\/]+$/, '')
  return /[\\/]skills[\\/]arturo$/.test(pulita) ? `${pulita}/../..` : pulita
}

// Gli hook in catena (session.start, turn.complete, session.end) sono funzioni dichiarate: il motore segue $ in un altro
// file solo dentro una dichiarazione. Il loro next è la parte dopo, quindi una funzione semplice.
export type Evento<N extends EventName> = Parameters<Hook<N>>[1]
export type Avanti<N extends EventName> = (e: Evento<N>) => ReturnType<Parameters<Hook<N>>[2]>
