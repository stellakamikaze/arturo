---
name: italiano-semplificato
description: >-
  Riscrive o controlla un testo dato con l'Italiano Tecnico Semplificato (ITS, adattamento italiano di
  ASD-STE100, 63 regole): classifica il testo, lo riscrive frase per frase e ne verifica la
  conformità, lasciando intatti codice, comandi e fatti.
when_to_use: >-
  Usa quando l'utente passa un testo e dice «riscrivi in ITS», «togli il burocratese», «rendi
  leggibile», «accorcia le frasi», «de-slop», «controlla che sia conforme», o chiede documentazione,
  runbook, messaggi di errore, note di rilascio, capitolati, istruzioni per agenti. NON per le
  risposte in chat (le regole base stanno nel CLAUDE.md), non per marketing o voce di brand, non per impaginare un documento che ha un suo standard grafico. Segui tutti i passi nell'ordine: non prendere scorciatoie
  basandoti su questa description.
version: 1.1.0
license: MIT
compatibility: claude-code cursor codex gemini-cli opencode
metadata:
  derivato-da: ASD-STE100 Issue 9 (2025-01-15) via github.com/AminBlg/SimpleEnglish (MIT)
  standard: ITS 1.1
---

# Italiano Semplificato: scrivi come un manuale di manutenzione

## Che cosa deve uscire

Il lettore è stanco, di fretta o non madrelingua: ogni frase regge una lettura sola. Un testo ITS ha queste proprietà. Il percorso per arrivarci lo scegli tu.

- Ogni passaggio è procedurale oppure descrittivo, mai le due cose insieme. La classificazione fissa il limite di parole e la forma verbale (tabella sotto).
- Una parola per concetto in tutto il testo. Prima di scrivere scegli il verbo tra `verifica / controlla / accertati`, il nome tra `configurazione / impostazioni / parametri`, il verbo tra `esegui / avvia / lancia`.
- Una sola forma per le istruzioni: imperativo alla seconda singolare, oppure infinito (Regola 5.3).
- Codice, identificatori, comandi, errori citati e fatti restano esatti (vedi Intoccabili).
- Prima di consegnare, il controllo della sezione «Prima di consegnare».

Se ti chiedono di CONTROLLARE un testo invece di riscriverlo, riporta ogni violazione con: numero di regola (la numerazione è quella della sezione «Limiti»), testo che la viola, riscrittura conforme.

## Due modalità

| Modalità | Quando | Che cosa applichi |
|---|---|---|
| **Pragmatica** (predefinita) | Documentazione, README, messaggi di errore. L'utente vuole un testo chiaro. | Tutte le regole di struttura. Le parole di dominio restano («idempotente», «webhook», «capitolato»). |
| **Rigorosa** | L'utente nomina ITS, ASD-STE100 o la conformità. Il testo va tradotto o certificato. | Regole di struttura più glossario di progetto scritto, una sola forma verbale per le istruzioni, nessuna parola fuori glossario. |

In modalità rigorosa dichiara sempre il limite della sezione «Limiti»: ITS trasporta la meccanica di ASD-STE100, non la certificazione.

## Classifica il testo

| Tratto | Procedurale (istruzioni) | Descrittivo (spiegazioni) |
|---|---|---|
| Scopo | Dire al lettore che cosa fare | Spiegare che cosa è o che cosa fa una cosa |
| Forma verbale | Imperativo: «Installa la pompa.» | Indicativo presente, passato prossimo, futuro semplice |
| Limite di frase | **22 parole** (Regola 5.1) | **28 parole** (Regola 6.3) |
| Unità | Un'istruzione per frase (5.2) | Un tema per paragrafo (6.5), massimo sei frasi (6.6) |

Una sezione «Per iniziare» è procedurale. Una sezione «Architettura» è descrittiva. Una nota dentro una procedura è descrittiva: limite di 28 parole, niente imperativo.

ASD-STE100 fissa 20 e 25 parole. L'italiano dice la stessa cosa con più parole grammaticali («the configuration file» sono tre parole, «il file di configurazione» quattro): il rapporto misurato in localizzazione sta tra 1,10 e 1,20. ITS applica 1,10 e arrotonda a 22 e 28. Se il dominio ha nomi tecnici lunghi, alza le soglie una volta sola e scrivilo nella guida di stile del progetto.

## Il catalogo delle regole

63 regole in 10 sezioni. Le sezioni da 1 a 9 seguono la struttura di ASD-STE100 Issue 9 con contenuto italiano ed esempi software. La sezione 10 è solo italiana.

### Sezione 1 — Parole (Regole 1.1-1.12)

| Regola | Istruzione |
|---|---|
| 1.1 | Usa solo parole del glossario di progetto, nomi tecnici o verbi tecnici. |
| 1.2 | Usa una parola solo nella parte del discorso in cui l'hai registrata. |
| 1.3 | Usa una parola solo con il significato che le hai assegnato. |
| 1.4 | Tra due parole che dicono la stessa cosa, scegli sempre la più breve e la più comune. |
| 1.5 | Le parole di dominio sono nomi tecnici legittimi («webhook», «commit», «endpoint», «stazione appaltante»). |
| 1.6 | Usa una parola fuori glossario solo se è un nome tecnico o ne fa parte. |
| 1.7 | Non trasformare i nomi tecnici in verbi («deployare», «schedulare», «triggerare», «committare»). |
| 1.8 | Usa i nomi tecnici del tuo settore e scrivili nel glossario. |
| 1.9 | Quando scegli un nome tecnico, scegline uno breve e trasparente. |
| 1.10 | Niente regionalismi, gergo di reparto, sigle non sciolte alla prima occorrenza. |
| 1.11 | Una cosa, un nome. Non chiamarla «configurazione» qui e «impostazioni» là. |
| 1.12 | I verbi di dominio sono verbi tecnici legittimi («compila», «distribuisci», «unisci»). |

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
| 3.4 | Non usare il participio presente come verbo («i dati risultanti dalla query» diventa «i dati che la query restituisce»). |
| 3.5 | Voce attiva. Nel testo descrittivo il passivo è ammesso solo quando l'agente è ignoto. |
| 3.6 | Niente «si» passivante o impersonale nelle procedure. |
| 3.7 | Un'azione si dice con un verbo, non con un nome. |
| 3.8 | Non usare l'infinito sostantivato al posto del verbo («l'invio dei dati avviene» diventa «il servizio invia i dati»). |
| 3.9 | Modali ammessi: `puoi`, `devi`, il futuro semplice. Vietati: `dovresti`, `potresti`, `sarebbe`, `si consiglia di`, `è opportuno`, `eventualmente`. |

Il condizionale è la principale fonte di ambiguità dell'italiano tecnico: un agente e un lettore stanco leggono `dovresti` come facoltativo.

| Hai scritto | ITS scrive |
|---|---|
| dovresti, si consiglia di, è opportuno (requisito) | devi |
| dovresti (consiglio) | Cancella, oppure afferma il fatto: «X è più veloce perché Y.» |
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
| 4.2 | Non tagliare parole per accorciare. Tieni gli articoli, le preposizioni e il «che» completivo. |
| 4.3 | Usa un elenco verticale quando il testo diventa complesso. |
| 4.4 | Collega le frasi con connettivi espliciti («Poi», «Di conseguenza», «Invece», «Per questo»). |
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
| 5.3 | Scrivi le istruzioni all'imperativo, seconda persona singolare: «Esegui la migrazione.» L'infinito («Eseguire la migrazione») è ammesso nei contesti industriali e regolati, ma una forma sola per tutto il documento. |
| 5.4 | Metti la condizione prima del comando, separata da una virgola: «Se la build fallisce, leggi il log.» |
| 5.5 | Le note danno informazioni, mai istruzioni. Le note hanno il limite di 28 parole. |

La Regola 5.3 chiude l'oscillazione dei manuali italiani, che alternano «Premere il tasto», «Premi il tasto» e «Prema il tasto» nella stessa pagina.

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
| 9.3 | Non costruire perifrasi verbali: «andare a configurare» diventa «configura», «provvedere all'invio» diventa «invia». |
| 9.4 | Tieni uno stile e una terminologia coerenti in tutto il documento. |
| 9.5 | Niente abbreviazioni oscure: «ad es.» diventa «per esempio», «cfr.» diventa «vedi», «N.B.» diventa «Nota». Cancella «ecc.» ed elenca le voci. |

La Regola 9.3 colpisce due tic: «andare a» più infinito (il tutorial parlato) e «provvedere a», «procedere a», «effettuare» più nome (il documento amministrativo).

### Sezione 10 — Ortografia e forma italiana (Regole 10.1-10.6)

| Regola | Istruzione |
|---|---|
| 10.1 | Accenti sempre corretti. Mai l'apostrofo al posto dell'accento: `e'`, `puo'`, `citta'`, `piu'` sono errori, non varianti. |
| 10.2 | Accento acuto su `perché`, `poiché`, `affinché`, `benché`, `né`, `sé`. Accento grave su `è`, `cioè`, `caffè`, `ciò`. |
| 10.3 | Usa `ad` ed `ed` solo davanti alla stessa vocale: «ad andare», «ed erano». Scrivi «per esempio», non «ad esempio». |
| 10.4 | Scegli un tipo di virgolette e tienilo. Se il documento ha uno standard di casa, vale quello. |
| 10.5 | Numeri all'italiana: virgola decimale, spazio fine per le migliaia, spazio prima dell'unità (`12 GB`, `30 s`). Date in formato ISO oppure per esteso, mai `03/04/2026`. |
| 10.6 | Maiuscole all'italiana: solo la prima parola del titolo, i nomi propri e le sigle. Niente Title Case all'inglese. |

## Una parola, un concetto

ASD-STE100 ha un dizionario ufficiale di circa 900 parole. Per l'italiano non esiste, ma la meccanica funziona lo stesso: una parola, un significato, una parte del discorso. Il dizionario lo costruisci tu in un glossario di progetto di dieci righe, prima di scrivere. L'italiano tecnico ruota i sinonimi per eleganza, e ITS lo vieta (Regole 1.11 e 9.4). Per ogni riga scegli una colonna e tieni quella.

| Concetto | Le parole che ruotano | Scelta consigliata |
|---|---|---|
| accertare uno stato | verificare, controllare, accertarsi, assicurarsi, validare | `verifica che` |
| avviare un programma | eseguire, avviare, lanciare, far partire, runnare | `esegui` |
| togliere un dato | cancellare, eliminare, rimuovere, distruggere | `cancella` per i dati, `rimuovi` per gli oggetti fisici |
| mostrare a schermo | visualizzare, mostrare, riportare, restituire, renderizzare | `mostra` |
| impostazioni | configurazione, impostazioni, parametri, opzioni, settaggi | `configurazione` |
| cosa che non funziona | errore, problema, anomalia, criticità, problematica, issue | `errore` per la condizione tecnica, `problema` per il resto |
| mandare dati | inviare, mandare, spedire, trasmettere | `invia` |
| creare una risorsa | creare, generare, istanziare, produrre | `crea` |

Se il dominio usa un'altra parola, cambiala una volta e scrivila nel glossario. Le tabelle di sostituzione per slop AI e burocratese (da «al fine di» a «per», da «consente di» a «puoi») stanno in `references/sostituzioni.md`. Aprile quando riscrivi un testo scritto da persone o preesistente.

## Intoccabili

Questi elementi sono nomi tecnici (Regole 1.5 e 8.6). Lasciali esatti, anche quando violano le regole di lessico:

- Blocchi di codice, codice in linea, identificatori, comandi, flag, percorsi di file
- Messaggi di errore e righe di log citati
- Nomi di prodotto, nomi di endpoint API, chiavi di configurazione
- Citazioni testuali di norme, bandi e contratti
- Numeri con unità: ognuno conta come una parola nel limite di frase

Anche i fatti sono intoccabili. Riscrivi lo stile, non il contenuto. Quando la fonte non dà un numero, una causa o un termine esatto, tieni l'affermazione generica. Non inventare dettagli per sembrare concreto.

## Altri bersagli

Stesse regole, adattamenti diversi, in `references/casi-uso.md`: messaggi di errore (che cosa è successo, causa, soluzione all'imperativo), runbook, report di incidente (solo passato prossimo, niente attenuazioni), commit e pull request, note di rilascio, istruzioni per agenti AI, documenti di gara e capitolati (riferimenti normativi intoccabili), macro di assistenza, testo di interfaccia, preparazione alla traduzione.

## Prima di consegnare

Il benchmark del 20/8/2026 (54 generazioni, 3 modelli Claude) dice dove sta il lavoro. Condizionale, nominalizzazioni, «qualora», «si consiglia» e accenti sbagliati non compaiono quasi mai nel testo generato. Le violazioni vere sono quattro: frasi oltre il limite, gerundio, rotazione di sinonimi, lineetta lunga. Controlla prima quelle quattro. Poi ogni «se» e ogni «quando» di un comando: deve stare all'inizio della sua frase.

Per un testo scritto da persone, e per la modalità controllo, usa `references/checklist.md`. Su questo Mac c'è anche il linter: `python3 ~/Documents/ClaudeCode/italiano-semplificato/evals/its_lint.py --tipo procedurale FILE` (oppure `--tipo descrittivo`, `-` per stdin). Conta per difetto e non dà un verdetto di conformità.

## Esempio completo

**Prima (testo reale non modificato, generato da un LLM):**

> **Timeout di connessione.** Qualora sqlpipe risultasse bloccato o fallisse con `dial tcp: i/o timeout`, è importante verificare che l'host su cui gira sqlpipe possa raggiungere la porta Postgres (solitamente la 5432) — si tratta spesso di una regola di firewall o di un security group che sta bloccando la connessione. Nel caso in cui ci si stia connettendo a un database gestito (RDS, Cloud SQL, ecc.), occorre altresì accertarsi che l'istanza consenta le connessioni provenienti dall'IP di sqlpipe. Si potrebbe inoltre provare ad andare ad aumentare `source.connect_timeout_seconds` nella config, dal momento che una rete lenta potrebbe far scattare il timeout di default anche quando la connessione andrebbe comunque a buon fine.

**Dopo (classificato procedurale, verbo scelto «verifica», condizioni prima, un'istruzione per frase):**

> **Timeout di connessione.** sqlpipe si ferma con `dial tcp: i/o timeout` quando non raggiunge la porta Postgres (5432 nella configurazione predefinita).
>
> 1. Verifica che l'host su cui gira sqlpipe raggiunga la porta Postgres. Di solito la blocca un firewall o un security group.
> 2. Se il database è gestito (RDS, Cloud SQL), verifica che l'istanza accetti le connessioni dall'IP di sqlpipe.
> 3. Se la rete è lenta, aumenta `source.connect_timeout_seconds` nella configurazione.

Che cosa è cambiato: frasi da 50 parole spezzate sotto le 22, tolti tre condizionali e due congiuntivi, `verificare / accertarsi` uniti in `verifica`. Via il gerundio, «andare ad aumentare», «altresì», «ecc.» e la lineetta lunga. Ogni condizione sta prima del comando. Codice e stringhe di errore sono intatti.

## Limiti

ITS serve per fatti tecnici e istruzioni. Non applicarlo a testi di marketing, a un pezzo con una voce d'autore o alla scrittura di brand: toglie la persuasione per costruzione, e toglie anche il ritmo. Quando l'utente chiede ITS su un testo promozionale, dillo e offri ITS per la documentazione collegata.

Se il documento ha uno standard di casa (titoli, virgolette, voce), quello standard detta la voce e ITS governa la frase.

### ITS non è ASD-STE100 e non lo sostituisce

ASD-STE100 è la lingua controllata dei manuali di manutenzione aeronautici, una norma per la sola lingua inglese, con un dizionario ufficiale protetto da copyright, scaricabile gratis su asd-ste100.org (ASD-STE100 è un marchio registrato di ASD). ITS ne trasporta la meccanica in italiano. La numerazione delle regole è nostra e non coincide con ASD-STE100: nel controllo cita solo i numeri di questo file. Nessuna conformità ASD-STE100 discende dall'uso di questa skill e nessuno strumento può garantire la conformità a una lingua controllata. L'ultima parola resta a chi scrive.

## Riferimenti

- `references/checklist.md` — controllo completo con schemi cercabili, per la modalità controllo e per il testo scritto da persone
- `references/sostituzioni.md` — tabelle slop AI e burocratese, con la parola corta da scrivere al posto
- `references/casi-uso.md` — adattamenti per messaggi di errore, runbook, report di incidente, commit, note di rilascio, agenti, gare, interfaccia, traduzione
