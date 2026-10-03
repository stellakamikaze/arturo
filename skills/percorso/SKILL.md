---
name: percorso
description: >-
  Mostra alla persona il suo percorso a tappe (Osserva, Prova, Delega, Orchestra) con la CLI
  `arturo percorso`: la tappa con il todo che la prova, le cose che tiene per sé, una domanda sola
  e l'esercizio della settimana sul suo lavoro vero. Conta le decisioni che la persona tiene,
  non il lavoro che delega.
when_to_use: >-
  Usa quando la persona dice «a che punto sono?», «che esercizio ho?», «facciamo l'esercizio»,
  «cosa tengo per me?», «basta suggerimenti», «riprendi i suggerimenti», o scrive /percorso. NON
  per aggiungere o chiudere todo qualsiasi (quella è la skill todo). Segui tutti i passi
  nell'ordine: non prendere scorciatoie basandoti su questa description.
version: 1.0.0
license: MIT
---

# Percorso: le decisioni che la persona tiene

## Che cosa deve uscire

La persona capisce in poche righe a che punto è, e perché. Ogni tappa porta il numero del todo
che la prova, così la persona può controllare. Vede la lista delle cose che tiene per sé, come
regole sue. Riceve al massimo una domanda e una proposta di esercizio adatta al suo mestiere.
Niente si scrive senza il suo sì.

Il percorso è uno specchio, non un voto. Le tappe si sbloccano con segni di giudizio: una
decisione presa prima che Claude lavori, un limite dichiarato, un no motivato. Il numero di cose
delegate non conta mai. La tappa può anche scendere, se un todo si riapre: dillo come un fatto.

## Passi

1. **Leggi il percorso.**

   ```bash
   python3 ~/.claude/bin/arturo percorso --json
   ```

   I campi: `tappa` (0-4) e `nome`, `tappe` (ognuna con `segni`, `prova` = numero del todo o
   null, `capitolo`), `tieni_tu`, `domanda`, `esercizio`, `nuova_tappa`, `suggerimenti` e
   `avvisi`. Se ci sono avvisi, riferiscili in una riga.

2. **Racconta la tappa** in parole tue, in due o tre frasi. Cita il #id che prova ogni segno
   raggiunto. Poi di' quale segno apre la tappa dopo, come una possibilità: «La tappa Delega si
   apre quando decidi qualcosa prima che io lavori, per esempio con `deciso` su un todo
   DECIDI TU». Con `tappa` 0, di' che la prima tappa è Osserva e che basta un todo sul tuo
   lavoro: i todo degli esercizi non contano.

3. **Mostra «Cose che tieni per te»**: ogni voce di `tieni_tu` come una regola della persona
   («la firma resta tua»). Se la lista è vuota, dillo in una riga.

4. **Fai la domanda**, una sola, se `domanda` non è null: «#7 resta a te: perché?». Se la
   persona risponde, scrivi il perché:

   ```bash
   python3 ~/.claude/bin/arturo todo modifica 7 --perche "firma"
   ```

   «Lo faccio io e basta» è un perché valido. Se la persona dice che il lavoro può farlo Claude,
   chiedi conferma e poi usa `--chi io` oppure `--chi decidi`. Non spostare mai un todo da tu a
   io o decidi senza un sì.

5. **Proponi l'esercizio** di `esercizio`, adattato al mestiere che trovi nel CLAUDE.md della
   persona. Il testo intero sta in `~/.claude/docs/esercizi.md`, sotto l'intestazione del
   codice. Se la persona dice sì, crea il todo dell'esercizio:

   ```bash
   python3 ~/.claude/bin/arturo todo aggiungi "Esercizio E03: Una sintesi che puoi controllare" --progetto _percorso --chi tu
   ```

   Se `esercizio.todo` non è null, l'esercizio è già aperto: proponi di continuarlo.

6. **A esercizio finito**, chiedi: «cosa hai tenuto per te?». Scrivi la risposta come nota e
   poi chiudi il todo:

   ```bash
   python3 ~/.claude/bin/arturo todo nota 9 "Tenuto: le cifre le metto io"
   python3 ~/.claude/bin/arturo todo fatto 9
   ```

   «Niente» è una risposta valida: allora non scrivere la nota e chiudi solo il todo. La lista
   «Cose che tieni per te» raccoglie solo le cose tenute.

7. **Se `nuova_tappa` è vero**, proponi il capitolo della tappa (`capitolo`) oppure
   `/sparring` su quel capitolo. Per Orchestra, che non ha un capitolo suo, proponi
   `/sparring tieni la decisione`. Poi segna la tappa come vista:

   ```bash
   python3 ~/.claude/bin/arturo percorso visto
   ```

8. **Basta e riprendi.** Se la persona dice «basta suggerimenti», lancia
   `python3 ~/.claude/bin/arturo percorso basta`. Se dice «riprendi i suggerimenti», lancia
   `python3 ~/.claude/bin/arturo percorso riprendi`. Conferma in una riga.

## Freni

- **Non contare e non lodare il volume.** Non dire mai quante cose ha delegato, e non dire che
  delegare di più è meglio.
- **Non spingere a delegare un limite.** Un todo tu con un perché è una scelta della persona:
  non proporre di passarlo a Claude.
- **Scrivi solo dopo un sì.** Domanda, esercizio, nota: ogni scrittura nell'archivio aspetta la
  risposta della persona.
- **Niente colpa.** Non usare parole come «indietro», «saltato», «ritardo», «streak» o «punti».
  Un esercizio aperto da settimane è solo aperto.
- **Il percorso resta sul computer.** Il percorso si calcola dall'archivio locale dei todo, e il
  suo stato resta lì. I todo da cui nasce (perché e note «Tenuto:») viaggiano solo verso il
  repository privato della persona, come gli altri todo. Non mandare il percorso da nessuna parte
  e non riassumerlo per altre persone.
