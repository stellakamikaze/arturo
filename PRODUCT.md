# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Stack

HTML e CSS statici, nessun framework, nessuna dipendenza di build. Sorgente in `sito/`. Pubblicazione per ora su un server privato, raggiungibile solo dalla rete privata (decisione di Federico, 16/9/2026).

## Users

Visitatore principale: **chi non programma** e vuole cominciare a usare Claude Code senza sapere da dove partire. Professionista curioso dell'AI, anche senza un mestiere tecnico (primo utente reale: una persona non tecnica, dal 16/9/2026).

Altri casi d'uso confermati: chi scrive o fa un lavoro creativo; un piccolo studio o team; chi insegna o impara.

## Product Purpose

Arturo è un harness per Claude Code: guardie di sicurezza, sessioni che si aprono e si chiudono in ordine, agenti, skill e un curriculum dei principi. Gratuito, open source (MIT), in italiano. Successo: chi parte da zero lo installa con `/setup` e lavora senza fare danni irreversibili.

## Positioning

Estratto da una configurazione usata ogni giorno in produzione, igienizzato. Bene comune prima, contatti come effetto (decisione del 16/9/2026). Dice apertamente cosa non è neutro: Claude Code è un servizio a pagamento di un'azienda privata, e ogni aggiornamento è codice di altri che gira sul tuo computer.

## Operating Context

Terminale e Claude Code. Installazione: `git clone https://github.com/stellakamikaze/arturo.git ~/.claude`, poi `/setup`. Ciclo: `/inizio`, lavoro, `/fine`. Aggiornamenti: avviso all'avvio, `/aggiorna`, `/aggiorna indietro`. Curriculum in `docs/principi/`, novità in `NOVITA.md` raccontate da `/novita`, `/sparring`, `/guidami`.

## Capabilities and Constraints

- 18 hook, 11 comandi, 9 agenti, 3 skill (conteggi del README al 16/9/2026: vanno riletti dal README prima di citarli).
- Impegni del README: repository pubblico e MIT, niente telemetria, Arturo in italiano, stop dichiarato. L'avvio non applica aggiornamenti; `/inizio` sì.
- Nessun link a Ufficio Furore, nessuna cifra, nessun prezzo (decisione di Federico, 16/9/2026).
- La pagina non usa analytics, tracker, cookie né risorse che profilano il visitatore.

## Brand Commitments

- Nome: **Arturo**. Da Arktouros, «il guardiano dell'orsa», la stella dei naviganti.
- Figura: il **maggiordomo custode**, ispirato a Winston di Croft Manor. Nessun nome, marchio o riferimento esplicito a quel franchise sulla pagina.
- Firma: «progetto di Federico Nejrotti». Voce: italiano semplice, diretto, onesto sui limiti.
- Identità visiva propria di Arturo, separata dal canone SK di Federico.

## Evidence on Hand

README.md, NOVITA.md, docs/principi/00 e 01, commands/*.md. Nessuna testimonianza, nessun numero d'uso pubblicabile, nessun cliente: non inventarne.

## Product Principles

1. Chi non programma deve capire e installare senza aiuto.
2. Onestà prima della persuasione: i limiti si dicono nella stessa pagina dei benefici.
3. Nessuna promessa che il codice non mantiene.
