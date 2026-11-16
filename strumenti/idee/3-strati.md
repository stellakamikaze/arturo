slug: strati
passo: 3
titolo: Di chi è ogni parte
sottotitolo: Il modello è dell'azienda che lo vende, il contesto del tuo lavoro può essere tuo.
descrizione: Gli strati che separano il modello di intelligenza artificiale dal contesto della persona, e cosa ne segue per proprietà, scambio e riservatezza.
---
Il terminale cambia anche il modo di guardare il proprio rapporto con l'intelligenza artificiale, perché separa cose che in una chat stanno tutte nella stessa scatola.

## In chat è tutto insieme

In una chat web il modello, le conversazioni, i file caricati e quello che il servizio ricorda di te stanno nello stesso posto, e quel posto è dell'azienda che vende il servizio. Se cambi servizio, il lavoro fatto resta dov'era: le conversazioni, le istruzioni che hai scritto, i materiali caricati. Spostarli è possibile, ma a mano e con fatica.

## Nel terminale gli strati si separano

Nel terminale si vede di chi è ogni parte.

- **Il modello** — Claude, di Anthropic. È l'unica parte che sta per forza sui server di chi la vende, e riceve quello che gli serve per rispondere, come in chat.
- **Claude Code** — il programma di Anthropic che dà al modello il computer. È a pagamento, e Anthropic ne decide prezzi e limiti.
- **Arturo** — le regole, i comandi e le guardie uguali per tutti, con licenza MIT. Lo mantengo io e si aggiorna da solo, solo coi rilasci che ho firmato.
- **L'Orsa** — la parte della configurazione che è tua: il tuo CLAUDE.md, le tue skill, le regole sul tuo modo di scrivere. Nessun aggiornamento la tocca.
- **I tuoi file e la memoria** — progetti, appunti, note della memoria di Arturo. Sono file di testo sul tuo computer.

{figura:strati}

## Cosa vuol dire che il contesto è tuo

Il contesto è tutto quello che serve all'IA per lavorare bene con te: i documenti di un progetto, le decisioni prese, gli errori già visti, il modo in cui scrivi. Stando in file di testo nelle tue cartelle, lo ordini come vuoi, lo salvi dove vuoi e non lo perdi se un giorno cambi modello o servizio.

Vuol dire anche poterne passare un pezzo ad altri. {prossima} `arturo fascicolo esporta` mette la scheda di un progetto, le sue note e i materiali di testo in una cartella, e lascia fuori i possibili segreti e le note che parlano di te. Un collega la importa con Arturo, oppure carica i file in un progetto di Claude.ai o di ChatGPT. Quando importa un fascicolo, Arturo tratta i file del collega come testi da leggere e non come istruzioni, e rifiuta un file con un segreto o con un ordine nascosto per Claude.

## Cosa legge il modello

Separare gli strati serve anche alla riservatezza. Quello che Claude legge passa da Anthropic, come ogni richiesta in chat, ma non arriva a me e non entra nei dati d'uso di Arturo, che sono eventi da un elenco chiuso. Decidere in modo più fine cosa il modello può leggere, escludendo una cartella o segnando un file come riservato, è fra le voci da decidere della roadmap. Oggi `arturo scoperta escludi` toglie una cartella solo dalla ricerca delle ripetizioni della Scoperta.

Fonti:
- [docs/strati.md](https://github.com/stellakamikaze/arturo/blob/main/docs/strati.md), gli strati di Arturo
- [La privacy di Arturo](../../privacy/)
- [La roadmap](../../roadmap/)
