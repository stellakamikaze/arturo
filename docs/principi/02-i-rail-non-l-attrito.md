Bozza: la rilegge e la corregge Federico prima del rilascio su main.

# 02 — I rail, non l'attrito

> Questo principio sta in una riga: **pochi punti fermi sui gesti senza ritorno, e sul resto
> lascia correre.** Una conferma che dai senza leggere non protegge niente.

## Il problema delle mille conferme

Il modo più semplice di rendere sicuro un assistente è fargli chiedere il permesso a ogni passo.
Vuoi leggere un file? Chiedi. Vuoi creare una cartella? Chiedi. Sembra prudente.

Dopo un'ora succede una cosa che conosci già dai cookie dei siti: clicchi «sì» senza leggere.
La finestra arriva, la mano risponde. A quel punto la conferma importante, quella prima di
cancellare una cartella di lavoro, passa con lo stesso gesto delle cento inutili.

La sicurezza fatta di attrito ha due costi. Ti fa perdere il tempo che volevi guadagnare. E ti
abitua a non guardare proprio dove dovresti.

## Cosa sono i rail

Un rail è un binario: non ti chiede niente finché resti sopra, e non cede quando provi a uscire.
In Arturo i rail sono pochi, e stanno sui gesti da cui non si torna indietro:

- cancellare per sempre una cartella che contiene lavoro tuo;
- mandare un'email o un messaggio a un'altra persona;
- mettere una password o una chiave in un posto da cui esce (un salvataggio di git, un invio);
- leggere una chiave privata e farla finire nella conversazione;
- spedire dati verso un server che non conosci;
- svuotare un database.

Tutto il resto, cioè leggere, scrivere bozze, riordinare file, provare, scorre senza domande.

## Come funziona in Arturo

Ci sono due reti, una sopra l'altra.

La prima è il controllo di sicurezza di Claude Code. In modalità `auto` giudica ogni comando
prima che parta, senza fermarti per ogni passo.

La seconda sono le **guardie** di Arturo: programmi piccoli che guardano il comando prima che
parta e cercano solo quei gesti senza ritorno. Una guardia non si stanca e non si fa convincere.
Quando trova uno di quei gesti, quasi sempre ti chiede conferma e ti mostra il comando vero.
Blocca soltanto pochi casi che non hanno mai un uso buono.

Le guardie si controllano anche da sole. Ogni dodici ore Arturo le prova su una serie di casi
noti, e se una risponde male te lo dice all'avvio.

## Perché chiedere invece di bloccare

Un blocco sembra più sicuro di una domanda. In pratica insegna la cosa sbagliata.

All'inizio una guardia di Arturo bloccava ogni comando che nominava l'invio di email. In un mese
ha bloccato 14 comandi, e 13 non inviavano niente. Erano testi che parlavano di email: un file in
scrittura, una ricerca, un messaggio di salvataggio. Una volta Claude ha riscritto un comando
apposta per evitare le parole vietate. Una regola che sbaglia tredici volte su quattordici non
ferma il pericolo: insegna ad aggirarla.

Una conferma fa il contrario. Ti mette davanti il comando com'è, e decidi tu.

## Perché un falso allarme conta

Ogni conferma inutile consuma la tua attenzione e ti riporta all'abitudine del «sì» automatico.
Per questo le guardie di Arturo leggono il comando come lo legge il computer. Un testo che
Claude scrive in un file e che nessuno esegue non conta come un comando. Un messaggio che
descrive un'operazione non è l'operazione. Così la domanda arriva poco, e quando arriva vale
la pena leggerla.

## Cosa tocca a te

- **Quando arriva una conferma, leggila.** È rara apposta: se te la chiede, c'è un motivo.
- **Se una guardia ti ferma spesso su cose innocue, dillo** con `/segnala`. Spegnerla da solo
  ti toglie il rail insieme all'attrito.
- **Non cercare la modalità che non chiede mai niente.** Sui gesti senza ritorno la domanda
  serve: è lì per te.

## La cosa da portarsi via

Davanti a una conferma che lo strumento ti chiede, chiediti: **se dico sì senza leggere, cosa
può succedere?** Se la risposta è «niente», quella conferma è attrito, e conviene toglierla. Se
la risposta è «qualcosa che non si rimedia», quella è un rail, e va tenuta.

---

*Vuoi provarlo sul tuo lavoro? Chiedi a Claude uno sparring su «i rail».*
