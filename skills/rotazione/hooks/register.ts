// rotazione: a ogni milestone il modello chiama il tool `ruota`; a fine turno il mod lancia /clear
// e nella sessione nuova `/inizio <progetto> -- --rotazione <compito>` (3/11/2026).
// Provato su Claude Code 2.1.317: $.command.run esegue /clear e i comandi slash;
// $.prompt.submit con un testo che comincia con "/" non esegue il comando.
// Il codice è lo stesso nella copia della config: nome del tool e registro vengono da $.plugin.name.
import type { EngineInterface, Register } from 'claude-code'

import {
  ATTESA_CLEAR_MS,
  ATTESA_INIZIO_MS,
  argomentiInizio,
  decidi,
  leggiArgomenti,
  nomeTool,
  RIPROVA_CLEAR_MS,
  type Rotazione,
  spenta,
} from './rotazione'

const CHIAVE_ULTIMA = 'ultima-rotazione'

let armata: Rotazione | undefined
let inCorso: Rotazione | undefined
let interattiva = true
let nomeRegistrato: string | undefined

export const register: Register = on => {
  on('session.start', async ($, e, next) => {
    const r = await next(e)
    interattiva = e.isInteractive
    // Il nome completo lo dà il motore (mcp__<plugin>__ruota): vale per Arturo e per una copia rinominata.
    const { tool } = await $.tool.register({
      name: 'ruota',
      description:
        'Rotazione della sessione a fine milestone (uno step del piano o un compito chiuso). Chiamalo DOPO ' +
        '/fine --rotazione andato a buon fine, come ultima azione del turno. A fine turno /clear, poi ' +
        '/inizio <progetto> -- --rotazione <compito>: il lavoro riparte da solo con il contesto pulito. ' +
        'Non chiamarlo se il prossimo step chiede la persona (una decisione, un invio, un pagamento, un ' +
        'accesso) o se non ci sono step.',
      inputSchema: {
        type: 'object',
        properties: {
          progetto: { type: 'string', description: 'slug del progetto per /inizio' },
          compito: { type: 'string', description: 'il prossimo step, in una frase' },
        },
        required: ['progetto', 'compito'],
      },
      isDeferred: false,
    })
    nomeRegistrato = tool
    return r
  })

  on('tool.call', async ($, e, next) => {
    if (e.tool !== (nomeRegistrato ?? nomeTool($.plugin.name))) return next(e)
    if (!interattiva) return { result: 'Rotazione non disponibile qui: sessione senza prompt (headless o SDK).' }
    const interruttore = await $.env.get('ARTURO_ROTAZIONE').catch(() => undefined)
    if (spenta(interruttore))
      return { result: 'Rotazione spenta (ARTURO_ROTAZIONE). Chiudi come sempre: proponi /fine, poi /clear e /inizio.' }
    const r = leggiArgomenti(e)
    if (typeof r === 'string') return { deny: `${$.plugin.name}: ${r}` }
    armata = r
    $.ui.status(`rotazione pronta: a fine turno riparto da "${r.compito}"`)
    return { result: `Rotazione armata: a fine turno /clear, poi /inizio ${argomentiInizio(r)}. Chiudi il turno ora.` }
  })

  on('turn.complete', async ($, e, next) => {
    const r = await next(e)
    if (!armata) return r
    try {
      const [box, ora, ultima, minS] = await Promise.all([
        $.prompt.read(),
        $.clock.now(),
        $.store.get(CHIAVE_ULTIMA),
        $.env.get('ROTAZIONE_MIN_S').catch(() => undefined),
      ])
      const esito = decidi({
        armata,
        reason: e.reason,
        agentId: e.agentId,
        bozza: box.text,
        ora,
        ultima: typeof ultima === 'number' ? ultima : undefined,
        intervalloMs: minS !== undefined && /^\d+$/.test(minS) ? Number(minS) * 1000 : undefined,
      })
      await registra(
        $,
        `${e.reason} agent=${e.agentId ?? '-'} bozza=${JSON.stringify(box.text.slice(0, 80))} ` +
          `ultima=${typeof ultima === 'number' ? Math.round((ora - ultima) / 1000) + 's fa' : '-'} → ${esito.azione}` +
          (esito.azione === 'disarma' ? ` (${esito.motivo})` : ''),
      )
      if (esito.azione === 'disarma') {
        armata = undefined
        $.ui.status(`rotazione: ${esito.motivo}`)
        $.ui.toast(`${$.plugin.name}: ${esito.motivo}`)
      } else if (esito.azione === 'clear') {
        inCorso = armata
        armata = undefined
        await $.store.set(CHIAVE_ULTIMA, ora)
        $.clock.after(ATTESA_CLEAR_MS, () => lanciaClear($))
        // Il 3/11 un /clear deciso non è partito (1 su 8): se dopo 5 s la sessione non si è chiusa,
        // un secondo tentativo, registrato.
        const attesa = inCorso
        $.clock.after(ATTESA_CLEAR_MS + RIPROVA_CLEAR_MS, async () => {
          if (inCorso !== attesa || !attesa) return
          await registra($, 'clear: nessuna chiusura dopo 5 s, secondo tentativo')
          await lanciaClear($)
        })
      }
    } catch (err) {
      armata = undefined
      $.ui.toast(`${$.plugin.name}: errore a fine turno, nessuna rotazione (${String(err)})`)
    }
    return r
  })

  on('session.end', async ($, e, next) => {
    const r = await next(e)
    if (e.reason !== 'clear' || !inCorso) return r
    const rot = inCorso
    inCorso = undefined
    // la riga "rotazione pronta" della sessione vecchia resterebbe sotto il prompt
    $.ui.status(undefined)
    $.clock.after(ATTESA_INIZIO_MS, () => lanciaInizio($, rot))
    return r
  })
}

// L'ultima decisione, in un file da leggere quando una rotazione non parte (ultime 40 righe).
async function registra($: EngineInterface, riga: string): Promise<void> {
  try {
    const home = await $.env.get('HOME')
    if (!home) return
    const f = `${home}/.claude/cache/${$.plugin.name}-ultimo.txt`
    let prima = ''
    try {
      prima = await $.fs.read(f)
    } catch {
      prima = ''
    }
    const righe = `${prima}${new Date().toISOString()} ${riga}\n`.split('\n').filter(Boolean).slice(-40)
    await $.fs.write(f, righe.join('\n') + '\n')
  } catch {
    // il registro non deve mai fermare la rotazione
  }
}

async function lanciaClear($: EngineInterface): Promise<void> {
  try {
    await registra($, 'clear: lanciato')
    const r = await $.command.run({ command: 'clear', args: '' })
    await registra($, `clear: risolto ${JSON.stringify(r).slice(0, 120)}`)
  } catch (err) {
    await registra($, `clear: rifiutato ${String(err)}`)
    inCorso = undefined
    $.ui.status(undefined)
    $.ui.toast(`${$.plugin.name}: /clear rifiutato, nessuna rotazione (${String(err)})`)
  }
}

async function lanciaInizio($: EngineInterface, rot: Rotazione): Promise<void> {
  try {
    $.ui.toast(`Sessione rinnovata: salvato tutto, riparto da "${rot.compito}"`)
    await registra($, `inizio: lanciato ${argomentiInizio(rot)}`)
    await $.command.run({ command: 'inizio', args: argomentiInizio(rot) })
  } catch (err) {
    await registra($, `inizio: rifiutato ${String(err)}`)
    $.ui.toast(`${$.plugin.name}: /inizio non partito (${String(err)}). Scrivi: /inizio ${rot.progetto}`)
  }
}
