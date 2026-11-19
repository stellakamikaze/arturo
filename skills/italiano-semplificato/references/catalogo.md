# Il catalogo delle regole ITS

Le 63 regole di italiano-semplificato, coi numeri che `SKILL.md` cita.

63 regole in 10 sezioni. Le sezioni da 1 a 9 seguono la struttura di ASD-STE100 Issue 9 con contenuto italiano ed esempi software. La sezione 10 è solo italiana.

### Sezione 1 — Parole (Regole 1.1-1.12)

| Regola | Istruzione |
|---|---|
| 1.1 | Usa solo parole del glossario di progetto, nomi tecnici o verbi tecnici. |
| 1.2 | Usa una parola solo nella parte del discorso in cui l'hai registrata. |
| 1.3 | Usa una parola solo con il significato che le hai assegnato. |
| 1.4 | Tra due parole che dicono la stessa cosa, scegli sempre la più breve e la più comune. |
| 1.5 | Le parole di dominio sono nomi tecnici legittimi ("webhook", "commit", "endpoint", "stazione appaltante"). |
| 1.6 | Usa una parola fuori glossario solo se è un nome tecnico o ne fa parte. |
| 1.7 | Non trasformare i nomi tecnici in verbi ("deployare", "schedulare", "triggerare", "committare"). |
| 1.8 | Usa i nomi tecnici del tuo settore e scrivili nel glossario. |
| 1.9 | Quando scegli un nome tecnico, scegline uno breve e trasparente. |
| 1.10 | Niente regionalismi, gergo di reparto, sigle non sciolte alla prima occorrenza. |
| 1.11 | Una cosa, un nome. Non chiamarla "configurazione" qui e "impostazioni" là. |
| 1.12 | I verbi di dominio sono verbi tecnici legittimi ("compila", "distribuisci", "unisci"). |

La Regola 1.4 è la leva più forte in italiano: la lingua tecnica preferisce per abitudine `utilizzare` a `usare`, `effettuare` al verbo pieno, `provvedere a` all'azione.

**Prima:** Dopo aver committato, puoi deployare la release e triggerare il job.
**Dopo:** Registra le modifiche con un commit. Poi distribuisci la release e avvia il job.

### Sezione 2 — Nomi composti (Regole 2.1-2.3)

| Regola | Istruzione |
|---|---|
| 2.1 | Scrivi catene di nomi di tre parole al massimo. |
| 2.2 | Se un nome tecnico chiede più di tre parole, scrivilo per esteso una volta, poi dai la forma breve. |
| 2.3 | Spezza le catene lunghe con le preposizioni (di, per, su, in, tra). |

**Prima:** il valore di configurazione del timeout del pool di connessioni al database
**Dopo:** il timeout del pool di connessioni. Il file di configurazione contiene questo valore.

### Sezione 3 — Verbi (Regole 3.1-3.9)

| Regola | Istruzione |
|---|---|
| 3.1 | Usa solo questi modi e tempi: infinito, imperativo, indicativo presente, passato prossimo, futuro semplice, participio passato con funzione di aggettivo. |
| 3.2 | Non usare congiuntivo, condizionale, trapassato prossimo, futuro anteriore, passato remoto. |
| 3.3 | Non usare il gerundio come verbo. Spezza la frase in due. |
| 3.4 | Non usare il participio presente come verbo ("i dati risultanti dalla query" diventa "i dati che la query restituisce"). |
| 3.5 | Voce attiva. Nel testo descrittivo il passivo è ammesso solo quando l'agente è ignoto. |
| 3.6 | Niente "si" passivante o impersonale nelle procedure. |
| 3.7 | Un'azione si dice con un verbo, non con un nome. |
| 3.8 | Non usare l'infinito sostantivato al posto del verbo ("l'invio dei dati avviene" diventa "il servizio invia i dati"). |
| 3.9 | Modali ammessi: `puoi`, `devi`, il futuro semplice. Vietati: `dovresti`, `potresti`, `sarebbe`, `si consiglia di`, `è opportuno`, `eventualmente`. |

Il condizionale è la principale fonte di ambiguità dell'italiano tecnico: un agente e un lettore stanco leggono `dovresti` come facoltativo.

| Hai scritto | ITS scrive |
|---|---|
| dovresti, si consiglia di, è opportuno (requisito) | devi |
| dovresti (consiglio) | Cancella, oppure afferma il fatto: "X è più veloce perché Y." |
| potrebbe, può darsi, eventualmente, in taluni casi | può |
| sarebbe, qualora si verificasse, laddove | Se X, allora Y (indicativo) |
| è possibile che si verifichi un errore | può verificarsi un errore |

Il gerundio (Regola 3.3) è il gemello italiano della subordinata inglese in `-ing`: nasconde il soggetto e il rapporto logico tra le due azioni.

**Prima:** Verificando i log, noterai l'errore, permettendo di isolare la causa.
**Dopo:** Leggi i log. Il log mostra l'errore. L'errore indica la causa del guasto.

La nominalizzazione (Regole 3.7 e 3.8) è il burocratese in forma pura: il verbo pieno sparisce e resta un verbo vuoto più un nome in `-zione`.

**Prima:** Si procede all'effettuazione della configurazione del client tramite l'apposito file.
**Dopo:** Configura il client nel file `client.yaml`.

**Prima:** La temperatura deve essere regolata dall'operatore.
**Dopo:** Regola la temperatura.

### Sezione 4 — Frasi (Regole 4.1-4.6)

| Regola | Istruzione |
|---|---|
| 4.1 | Scrivi frasi brevi e chiare. |
| 4.2 | Non tagliare parole per accorciare. Tieni gli articoli, le preposizioni e il "che" completivo. |
| 4.3 | Usa un elenco verticale quando il testo diventa complesso. |
| 4.4 | Collega le frasi con connettivi espliciti ("Poi", "Di conseguenza", "Invece", "Per questo"). |
| 4.5 | Metti l'articolo o il dimostrativo davanti ai nomi. |
| 4.6 | Ripeti il soggetto quando il soggetto cambia. L'italiano lo sottintende e il lettore lo perde. |

La Regola 4.2 vieta lo stile telegrafico: frasi corte con grammatica completa, non appunti.

**Accorciamento sbagliato:** Verificare esistenza backup prima migrazione.
**ITS:** Verifica che il backup esista. Poi esegui la migrazione.

La Regola 4.6 non esiste in inglese, dove il soggetto è obbligatorio. In italiano tre frasi senza soggetto esplicito costringono il lettore a tornare indietro.

**Prima:** Il servizio legge la coda e la elabora. Poi la scrive su disco. Quando è pieno, si blocca.
**Dopo:** Il servizio legge la coda e la elabora. Poi il servizio scrive i messaggi su disco. Se il disco è pieno, il servizio si blocca.

### Sezione 5 — Testo procedurale (Regole 5.1-5.5)

| Regola | Istruzione |
|---|---|
| 5.1 | Massimo 22 parole per frase. Le avvertenze rientrano nel limite. |
| 5.2 | Un'istruzione per frase, salvo due azioni simultanee. |
| 5.3 | Scrivi le istruzioni all'imperativo, seconda persona singolare: "Esegui la migrazione." L'infinito ("Eseguire la migrazione") è ammesso nei contesti industriali e regolati, ma una forma sola per tutto il documento. |
| 5.4 | Metti la condizione prima del comando, separata da una virgola: "Se la build fallisce, leggi il log." |
| 5.5 | Le note danno informazioni, mai istruzioni. Le note hanno il limite di 28 parole. |

La Regola 5.3 chiude l'oscillazione dei manuali italiani, che alternano "Premere il tasto", "Premi il tasto" e "Prema il tasto" nella stessa pagina.

**Prima:** Sarà necessario recuperare la chiave API dalla dashboard prima di procedere alla configurazione del client, operazione che si effettua nella sezione Impostazioni.
**Dopo:** Apri la dashboard, sezione Impostazioni. Copia la chiave API. Poi configura il client con questa chiave.

### Sezione 6 — Testo descrittivo (Regole 6.1-6.6)

| Regola | Istruzione |
|---|---|
| 6.1 | Dai le informazioni per gradi: un fatto nuovo per frase. |
| 6.2 | Usa parole chiave ricorrenti per dare al testo una struttura logica. |
| 6.3 | Massimo 28 parole per frase. |
| 6.4 | Raggruppa in un paragrafo le informazioni collegate. |
| 6.5 | Un tema per paragrafo. |
| 6.6 | Massimo sei frasi per paragrafo. |

Niente imperativo nel testo descrittivo. Le descrizioni spiegano, le procedure comandano.

### Sezione 7 — Avvertenze di sicurezza (Regole 7.1-7.3)

| Regola | Istruzione |
|---|---|
| 7.1 | Usa una parola che dichiari il livello di rischio. |
| 7.2 | Comincia con il comando o con la condizione. |
| 7.3 | Poi dai il rischio o la conseguenza. |

Livelli, allineati alla pratica italiana della norma ISO 3864:

| Parola | Rischio |
|---|---|
| **PERICOLO** | Morte o lesioni gravi, certe se il lettore ignora l'avvertenza. |
| **ATTENZIONE** | Lesioni alle persone, oppure perdita di dati non recuperabile. |
| **AVVISO** | Danno a cose o dati recuperabili. Nessun rischio per le persone. |

Lo schema vale identico per le opzioni distruttive della riga di comando, le migrazioni non reversibili e le chiamate API pericolose.

**Prima:** Si segnala che, nell'eventualità in cui il flag distruttivo risultasse abilitato in ambiente di produzione, potrebbe verificarsi una perdita di dati.
**Dopo:** ATTENZIONE: non usare il flag `--force` in produzione. Il flag cancella le righe che non esistono nella sorgente.

### Sezione 8 — Punteggiatura e conteggio delle parole (Regole 8.1-8.8)

| Regola | Istruzione |
|---|---|
| 8.1 | Tutta la punteggiatura standard è ammessa tranne il punto e virgola. Scrivi due frasi. |
| 8.2 | Usa il trattino per unire parole che funzionano come una sola unità. |
| 8.3 | Le parentesi tonde sono ammesse per riferimenti, numeri di elemento, sigle, alternative. |
| 8.4 | In un elenco verticale, i due punti della frase introduttiva chiudono la frase per il conteggio. |
| 8.5 | Il testo tra parentesi conta come una parola. |
| 8.6 | Contano come una parola: numeri, numeri con unità, sigle, identificatori alfanumerici, testo tra virgolette o tra backtick, titoli, etichette, nomi propri. |
| 8.7 | Una parola con il trattino conta come una parola. |
| 8.8 | Niente lineetta lunga come pausa retorica. Usa il punto, la virgola o le parentesi. |

Per la Regola 8.6, `sqlpipe run --config sqlpipe.yaml` tra backtick vale una parola: gli identificatori lunghi non consumano il budget della frase. La Regola 8.8 non viene da ASD-STE100: la lineetta come sospensione è il segno più riconoscibile del testo generato.

### Sezione 9 — Pratiche di scrittura (Regole 9.1-9.5)

| Regola | Istruzione |
|---|---|
| 9.1 | Quando la sostituzione parola per parola non funziona, ristruttura la frase. |
| 9.2 | Usa ogni parola con il significato e la parte del discorso che le hai assegnato nel glossario. |
| 9.3 | Non costruire perifrasi verbali: "andare a configurare" diventa "configura", "provvedere all'invio" diventa "invia". |
| 9.4 | Tieni uno stile e una terminologia coerenti in tutto il documento. |
| 9.5 | Niente abbreviazioni oscure: "ad es." diventa "per esempio", "cfr." diventa "vedi", "N.B." diventa "Nota". Cancella "ecc." ed elenca le voci. |

La Regola 9.3 colpisce due tic: "andare a" più infinito (il tutorial parlato) e "provvedere a", "procedere a", "effettuare" più nome (il documento amministrativo).

### Sezione 10 — Ortografia e forma italiana (Regole 10.1-10.6)

| Regola | Istruzione |
|---|---|
| 10.1 | Accenti sempre corretti. Mai l'apostrofo al posto dell'accento: `e'`, `puo'`, `citta'`, `piu'` sono errori, non varianti. |
| 10.2 | Accento acuto su `perché`, `poiché`, `affinché`, `benché`, `né`, `sé`. Accento grave su `è`, `cioè`, `caffè`, `ciò`. |
| 10.3 | Usa `ad` ed `ed` solo davanti alla stessa vocale: "ad andare", "ed erano". Scrivi "per esempio", non "ad esempio". |
| 10.4 | Usa solo le virgolette dritte ("). Mai le basse (« ») né quelle curve (“ ”). |
| 10.5 | Numeri all'italiana: virgola decimale, spazio fine per le migliaia, spazio prima dell'unità (`12 GB`, `30 s`). Date in formato ISO oppure per esteso, mai `03/04/2026`. |
| 10.6 | Maiuscole all'italiana: solo la prima parola del titolo, i nomi propri e le sigle. Niente Title Case all'inglese. |
