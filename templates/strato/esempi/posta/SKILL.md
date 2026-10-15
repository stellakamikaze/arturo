---
name: posta
description: ESEMPIO DA ADATTARE. Scrive le email di lavoro di {{ORGANIZZAZIONE}} come bozza nel thread giusto, con la voce dell'organizzazione, e dopo l'invio confronta la bozza con l'email inviata per proporre regole di voce nuove.
when_to_use: Quando l'utente chiede di scrivere o rispondere a un'email di lavoro («scrivi a X», «rispondi nel thread di Y»), oppure dice «inviata» o «l'ho mandata, guarda cosa ho cambiato». NON per inviare l'email e NON per i messaggi in chat.
disable-model-invocation: true
---

# Posta: bozza, inviata, regola di voce

<!-- ESEMPIO DA ADATTARE. Sostituisci le parti tra parentesi quadre con i vostri strumenti.
     Togli `disable-model-invocation` solo dopo averla provata su un'email vera. -->

Il ciclo ha tre momenti. Claude scrive la bozza. La persona la corregge e la invia. Claude
confronta le due versioni e propone una regola di voce. Senza il terzo momento le correzioni della
persona si perdono, e la bozza successiva ripete gli stessi errori.

## Freni

- Claude non invia mai. Crea solo la bozza. L'invio lo fa la persona.
- Una cifra, una data o un nome nel corpo hanno una fonte: un documento, un'email, un contratto.
  Se la fonte manca, scrivi `[FONTE?]` al posto del dato.
- Prima di scrivere, cerca una bozza che esiste già per lo stesso thread: aggiornala, non crearne
  una seconda.

## 1. Bozza

1. **Il thread.** Una risposta va nel thread aperto. Cerca la conversazione per nome e dominio
   del destinatario con [lo strumento di posta: connettore, CLI o client]. Scrivi in una riga
   l'ultimo contatto: data, chi ha scritto a chi.
2. **La voce.** Leggi `skills/voce/regole.md` dello strato. Poi leggi le ultime tre email inviate
   allo stesso destinatario: saluto, lunghezza e registro vengono da lì.
3. **La forma.** [Oggetto, firma, chi va in copia: le regole della vostra organizzazione.]
4. **Crea la bozza** nello strumento di posta. Salva una copia del testo in
   `~/.claude/data/posta/bozze/<data>-<oggetto>.md`. La cartella resta sul computer della persona:
   non va nello strato né in un repository.
5. **Mostra in chat** tre blocchi: la richiesta in una riga, la bozza, le domande aperte (massimo
   tre).

## 2. Inviata

1. Quando la persona dice «inviata», leggi l'ultima email inviata nel thread. Se non c'è
   un'inviata successiva alla bozza, dillo e fermati.
2. Confronta l'inviata con la copia della bozza, frase per frase.
3. **Giudica che cosa è un'abitudine.** Un saluto più asciutto, una frase tolta perché spiegava il
   metodo, una domanda resa più diretta: sono abitudini. Un dato corretto (una data, un nome, una
   cifra) è contenuto: non diventa una regola.
4. Se l'inviata è uguale alla bozza, scrivilo in una riga. Anche questo è un'informazione.

## 3. Regola di voce

Per ogni abitudine scrivi una proposta in questa forma:

> Claude aveva scritto: «…» → la persona ha mandato: «…» → regola: «…»

La proposta va al referente dello strato. Il referente decide se aggiungerla a
`skills/voce/regole.md` nel repository dello strato e la pubblica con `/strato pubblica`. Claude
non modifica i file installati dello strato: il prossimo aggiornamento li sostituirebbe.

## Un buon risultato

> **Richiesta**: risposta sulla data dell'incontro, nel thread aperto. Ultimo contatto: 29/9, dal
> cliente a noi.
>
> **Bozza** (nel thread, copia salvata): quattro righe. Conferma della data, chi viene, una
> domanda sul luogo.
>
> **Domande aperte**: 1. In copia anche il responsabile del progetto?

Perché funziona: la riga dell'ultimo contatto prova che Claude ha guardato la posta vera, la bozza
sta nel thread e lo dice, e c'è una sola domanda vera.
