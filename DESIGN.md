---
name: Arturo
description: Il custode di Claude Code, e dal 30/9/2026 della tua organizzazione, raccontato come un archivio d'ufficio.
colors:
  armadio: "#56615b"
  armadio-scuro: "#3b433f"
  armadio-chiaro: "#8b958f"
  rosso: "#c63a28"
  rosso-scuro: "#8f2616"
  blu: "#1d4c9c"
  blu-scuro: "#133670"
  verde: "#1d7449"
  verde-scuro: "#12512f"
  giallo: "#f3b50b"
  manila: "#e6c486"
  manila-scuro: "#bf9a58"
  foglio: "#fbfaf6"
  foglio-2: "#efece3"
  inchiostro: "#171816"
  inchiostro-2: "#484a45"
  viola-timbro: "#56389a"
  rosso-timbro: "#c0232b"
  verde-timbro: "#1b6a40"
  nastro-dymo: "#161616"
typography:
  display:
    fontFamily: "Big Shoulders, Arial Narrow, sans-serif"
    fontWeight: 900
    textTransform: uppercase
    lineHeight: 1.02
  dymo:
    fontFamily: "Big Shoulders"
    fontWeight: 800
    letterSpacing: "0.2em"
  body:
    fontFamily: "Atkinson Hyperlegible Next, system-ui, sans-serif"
    fontSize: "clamp(17px, 1.02rem + 0.2vw, 19.5px)"
    lineHeight: 1.56
  mono:
    fontFamily: "Courier Prime, Courier New, ui-monospace, monospace"
    use: "solo comandi, percorsi e messaggi reali delle guardie"
spacing:
  gutter: "clamp(16px, 4vw, 56px)"
  colonna: "1280px"
  ritmo: "clamp(80px, 11vw, 168px)"
---

# Design System: Arturo

## Overview

**North Star: «L'archivio d'ufficio».** Arturo si presenta come l'armadio di un ufficio italiano: cartelline di cartoncino pressato, faldoni con il foro sul dorso, etichette Dymo, fogli di trasmissione, registri di protocollo e timbri a inchiostro. Il pubblico fa lavoro della conoscenza e vive tra cartelle e pratiche: il mondo è il suo, non quello del terminale.

Il meccanismo del prodotto diventa oggetto. Quattro cartelle una dentro l'altra sono gli strati (Claude Code, Arturo, lo strato dell'organizzazione, tu). Le guardie timbrano le richieste. `/inizio` e `/fine` aprono e chiudono la pratica. Gli aggiornamenti arrivano in un vassoio e restano lì finché non dici sì.

Rifiuta l'hero scuro con il terminale al neon, la griglia di card uguali e la carta color crema.

## Colors

Strategia: **full palette su fondo di lamiera**. Il fondo è il grigio-verde ministeriale di un armadio metallico, con una trama verticale leggerissima. Le sezioni sono campiture intere di cartoncino: giallo per gli aggiornamenti, manila per referente e installazione, rosso per gli impegni. Il colore occupa superfici, non accenti.

- **Rosso, blu, verde, giallo, manila**: i cartoncini. Ogni strato ha il suo: blu Claude Code, rosso Arturo, verde lo strato, manila tu.
- **Foglio**: il bianco dei documenti dentro le cartelle. Non è mai il fondo della pagina.
- **Inchiostri dei timbri**: viola per «Chiede a te» e «Visto», rosso per «Blocca», verde per «Passa». Il viola è quello dei tamponi d'ufficio.
- Sul cartoncino rosso, blu e verde il testo è bianco. Su giallo e manila è inchiostro.

## Typography

- **Big Shoulders** (display, maiuscolo, 900): titoli, dorsi dei faldoni, linguette, timbri, nastro Dymo. Condensato come le scritte a normografo sui dorsi.
- **Atkinson Hyperlegible Next** (testo): scelto per la leggibilità di chi non è tecnico.
- **Courier Prime** (mono, 400 e 700): solo per comandi, percorsi e messaggi veri delle guardie. È la macchina da scrivere d'ufficio: il registro sembra battuto a macchina. Sostituisce Atkinson Hyperlegible Mono dal 1/10/2026, che si leggeva come un terminale. I comandi restano sempre in minuscolo, anche dentro un titolo o un pulsante.
- **Due strumenti, due ruoli.** Il normografo (Big Shoulders) per ciò che è stampato sul cartone. La macchina da scrivere (Courier Prime) per ciò che è battuto sul foglio. Il sottotitolo della copertina è Big Shoulders 500 con tracking largo, per distinguersi dai titoli a 900.
- **Big Shoulders con l'asse ottico** (`opsz` 10–72, `font-optical-sizing:auto`): le etichette piccole prendono il disegno aperto, i titoli quello stretto.
- I font stanno in `sito/font/` con licenza OFL. Nessun font da server esterni.
- Nel CSS le famiglie si chiamano «Big Shoulders», «Atkinson Next» e «Courier Prime».
- **Interlinea dei titoli display mai sotto 1,02.** In Big Shoulders 900 gli accenti maiuscoli (É, Ì, À) arrivano a 0,979 em: sotto 1,0 entrano nella riga sopra, e in italiano capita in quasi ogni titolo («FINCHÉ», «SÌ»).
- **Cifre tabulari solo nelle tabelle** (registro, foglio di trasmissione, datario). Nel testo corrente le cifre proporzionali spaziano meglio. Lo zero barrato di Atkinson Next è voluto dal font (distingue 0 da O) e resta.

## Components

- **Cartellina**: cartoncino con fibra (rumore SVG in moltiplica), ombra con offset e sfocatura, linguetta sagomata. Le linguette sono un `tablist` accessibile con frecce, Home e End.
- **Faldone**: dorso con finestrella bianca, scritta verticale e foro ad anello. È la navigazione dell'apertura.
- **Dymo**: nastro nero con lettere in rilievo (due ombre di testo opposte). Porta il nome ARTURO.
- **Timbro**: doppio bordo, inchiostro irregolare (filtro SVG `#inchiostro`: spostamento più erosione). È l'unico gesto animato della pagina: entra dall'alto e batte quando arriva in vista. Con movimento ridotto è già battuto.
- **Foglio**: documenti, registro, foglio di trasmissione, modulo. Leggermente ruotati, mai più di un grado.
- **Prova**: accanto a ogni affermazione c'è la prova vera. I messaggi del registro sono l'output reale delle guardie, eseguite il 30/9/2026.

## Motion

Un solo momento d'autore: il timbro che batte. In più l'apertura della copertina (rotazione sul cardine sinistro) e il foglio che entra nella cartella nella simulazione di `/aggiorna`. Tutto con uscita esponenziale e con `prefers-reduced-motion` rispettato.

## Named Rules

**La Regola della Prova.** Nessuna affermazione sulle guardie senza il messaggio che la guardia stampa davvero.
**La Regola dell'Assenza Disegnata.** Ciò che Arturo non fa (server, account, telemetria) si disegna come faldoni vuoti, non si tace.
**La Regola del Foglio.** Il bianco è sempre un documento dentro il mondo, mai il fondo della pagina.
