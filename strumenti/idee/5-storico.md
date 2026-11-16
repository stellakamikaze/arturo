slug: storico
passo: 5
titolo: Si parte da quello che hai già fatto
sottotitolo: Le tue chat con l'IA diventano un indice dei lavori, sul tuo computer.
descrizione: Come Arturo legge l'esportazione delle chat di ChatGPT, Claude.ai o Gemini e ne ricava un indice dei lavori, e cosa resta sul computer.
prossima: sì
---
{prossima} Chi arriva dalla chat non parte da zero. Ha mesi di lavoro alle spalle, chiusi dentro le conversazioni: una newsletter seguita ogni settimana, una mostra preparata in primavera, i preventivi di un festival. Arturo parte da lì, invece di chiederti di rispiegare tutto da capo.

## L'esportazione

Ogni servizio ti permette di scaricare la copia di tutte le tue conversazioni. ChatGPT e Claude.ai la preparano dalle impostazioni, Gemini da Google Takeout. Di solito arriva per email come file .zip, da pochi minuti a qualche ora dopo. La scarichi tu e la metti in una cartella: Arturo non entra nel tuo account e non scarica niente da solo.

## Cosa fa lo script

`/setup` ti propone di leggere l'esportazione, con un sì. La legge uno script sul tuo computer, che lavora da solo, senza mandare niente a Claude o ad altre IA. Apre il file .zip senza estrarlo e raggruppa le conversazioni per lavoro, dai titoli, dalle parole che tornano e dalle date. Toglie password scritte in chiaro, chiavi, IBAN, numeri di carta, codici fiscali, telefoni e le email che non sono la tua, e salta le conversazioni che dal titolo o dal testo sembrano d'identità, di salute o di banca. È un controllo su parole e formati, quindi qualcosa può passare: per questo vedi ogni lavoro prima che resti.

## Cosa resta

A Claude arriva la proposta di indice: per ogni lavoro i titoli delle conversazioni, le date, le parole che tornano e i nomi dei file allegati. Claude te li mostra uno per uno, e resta solo quello a cui dici sì. Sul computer resta l'indice dei lavori approvati, mai il testo delle chat, in una cartella che la copia Git della tua configurazione lascia fuori. `arturo storico mostra` ti fa vedere cosa contiene, `arturo storico togli` toglie un lavoro, `arturo storico cancella` lo cancella tutto. L'esportazione resta dove l'hai scaricata, con tutte le conversazioni per intero: quando l'indice è pronto puoi cancellarla.

## A cosa serve l'indice

Un lavoro con almeno cinque conversazioni, la prima e l'ultima in due mesi diversi, è un lavoro che torna. Diventa subito una proposta della Scoperta, senza aspettare che i file cambino tre volte: per esempio una sintesi della mostra, o un calendario editoriale della newsletter. Lo racconta il paper sulle proposte.

Fonti:
- [La privacy di Arturo, sezione "Lo storico delle chat"](https://github.com/stellakamikaze/arturo/blob/dev/docs/privacy.md)
- [La roadmap, voce "Arturo parte da quello che hai già fatto con l'IA"](../../roadmap/)
