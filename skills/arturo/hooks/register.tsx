// Il mod di Arturo: sei parti in un modulo solo (mod passo 3, 3/11/2026).
//
// apri: /apri apre l'ultimo link o file citato nelle risposte.
// cache-fredda: sotto il prompt, solo quando serve, la cache scaduta e i token gws in errore.
// dafare: il pannello /dafare con le cose da fare.
// redazione-segreti: i segreti nei risultati dei tool diventano la loro forma prima che Claude li legga.
// rotazione: il tool ruota, /clear e /inizio da soli a ogni passo chiuso.
// testata: il blocco di Arturo sotto l'intestazione di Claude Code, /versione.
//
// Una parte si spegne in ~/.claude/arturo/parti.json: {"spente": ["dafare"]}.
// Un evento senza matcher si registra una volta sola per mod: session.start e turn.complete li registra
// questo file, in catena; gli altri hook li registra ogni parte col suo matcher.
import type { Register } from 'claude-code'

import { avvio as avvioApri, register as registraApri } from './apri/register'
import { avvio as avvioCacheFredda, fineTurno as fineCacheFredda, register as registraCacheFredda } from './cache-fredda/register'
import { avvio as avvioDafare, fineTurno as fineDafare, register as registraDafare } from './dafare/register'
import { register as registraRedazioneSegreti } from './redazione-segreti/register'
import { avvio as avvioRotazione, fineTurno as fineRotazione, register as registraRotazione } from './rotazione/register'
import { avvio as avvioTestata, register as registraTestata } from './testata/register'

export const register: Register = (on, options) => {
  // Le registrazioni si annidano nell'ordine, la prima è la più esterna: la redazione dei segreti viene
  // prima, così ogni altra parte vede i risultati già redatti.
  registraRedazioneSegreti(on, options)
  registraTestata(on, options)
  registraRotazione(on, options)
  registraCacheFredda(on, options)
  registraApri(on, options)
  registraDafare(on, options)

  // La catena è scritta qui per esteso: il motore segue $ e next solo fra funzioni nominate.
  on('session.start', ($, e, next) =>
    avvioTestata($, e, e1 =>
      avvioRotazione($, e1, e2 => avvioCacheFredda($, e2, e3 => avvioApri($, e3, e4 => avvioDafare($, e4, next))))),
  )

  on('turn.complete', ($, e, next) =>
    fineRotazione($, e, e1 => fineCacheFredda($, e1, e2 => fineDafare($, e2, next))),
  )
}
