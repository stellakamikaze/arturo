---
name: recap
description: ESEMPIO DA ADATTARE. Prepara a una riunione di {{ORGANIZZAZIONE}} con lo stato del progetto e le domande aperte, e dopo la riunione ricava dalla trascrizione intera decisioni, cose da fare con responsabile e scadenza, cifre e date.
when_to_use: Quando l'utente dice «prepara la riunione con X», «cosa abbiamo deciso nell'ultima call», «recupera la trascrizione della riunione di ieri». NON per scrivere l'email di follow-up (quella è la skill di posta).
disable-model-invocation: true
---

# Recap: prima e dopo una riunione

<!-- ESEMPIO DA ADATTARE. Sostituisci le parti tra parentesi quadre con i vostri strumenti.
     Togli `disable-model-invocation` solo dopo averla provata su una riunione vera. -->

Il metodo ha una regola sola: **si legge la trascrizione intera**. Il riassunto automatico dello
strumento di videochiamata serve solo da indice. Sbaglia le cifre (1.400 diventa 14.000) e
attribuisce a una persona sola le frasi di chi parla dallo stesso microfono.

## Prima

1. **L'evento.** Cerca nel calendario la riunione di oggi o di domani: titolo, partecipanti,
   progetto.
2. **Lo stato.** Leggi i todo aperti (`arturo todo`) e tieni quelli del progetto. Poi leggi
   l'ultimo handoff e il recap dell'ultima riunione dello stesso progetto.
3. **In chat, una pagina:** che cosa è cambiato dall'ultima volta, le decisioni ancora aperte, le
   domande da fare, le cifre con la loro fonte.

## Dopo

1. **Trova la trascrizione** in [la cartella delle trascrizioni, o lo strumento di
   videochiamata]. Abbinala all'evento del calendario per titolo e data. Se c'è solo il
   riassunto, dillo in testa al recap: cifre e attribuzioni valgono meno.
2. **Leggi la trascrizione intera**, dall'inizio alla fine.
3. **Estrai**, ognuno con il segno del tempo (`hh:mm:ss`) per ritrovarlo:
   - le decisioni, con chi le ha prese;
   - le cose da fare, con un responsabile vero e una scadenza. Una data detta a voce («entro
     giovedì») si calcola dalla data della riunione;
   - le cifre e le date citate, marcate «dette in riunione»: un dato a voce non batte un
     documento finché non ha una fonte scritta;
   - le domande rimaste aperte.
4. **I todo.** Per ogni cosa da fare che spetta a voi, proponi un todo:
   `arturo todo aggiungi "<cosa>" --scadenza <data> --chi tu`. Crealo solo dopo il sì della
   persona.

## Un buon risultato

> **Riunione con il cliente, 2/10 ore 15** · trascrizione intera, 52 minuti
>
> **Deciso**: il workshop si sposta a novembre. Lo propone la coordinatrice, il cliente è
> d'accordo (00:14:20).
>
> **Da fare**: mandare al cliente due date di novembre · coordinatrice · entro mercoledì 8/10.
>
> **Cifre dette in riunione** (da verificare): budget 12.000 € (00:31:05).
>
> **Aperto**: chi paga la sala?

Perché funziona: ogni punto ha il segno del tempo per ritrovarlo, ogni cosa da fare ha un
responsabile e una scadenza, e la cifra è marcata come detta a voce.
