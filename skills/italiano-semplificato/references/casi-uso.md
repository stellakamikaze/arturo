# Casi d'uso oltre la documentazione

ASD-STE100 è nato per i manuali di manutenzione degli aerei. Le stesse proprietà, un significato per parola, frasi brevi e condizione prima del comando, valgono per ogni testo in cui fraintendere costa. Alla chiusura di Issue 8 il 64% degli utenti registrati di STE lavorava fuori dall'aeronautica e dalla difesa.

Ogni caso dichiara la modalità e gli adattamenti.

## Messaggi di errore e output da riga di comando

Modalità: procedurale. È il bersaglio con il rendimento più alto: un messaggio di errore è un'istruzione data alle due di notte a un lettore sotto pressione.

Schema: di' che cosa è successo (passato prossimo), poi la causa se la conosci, poi il comando o la condizione per risolvere.

> **Prima:** Ops! Qualcosa è andato storto durante il tentativo di stabilire la connessione. Si prega di verificare che le credenziali siano state configurate correttamente e riprovare.
> **Dopo:** La connessione al database è fallita. La password dell'utente `app` non è corretta. Imposta `DB_PASSWORD`, poi riprova.

## Runbook e procedure operative

Modalità: procedurale, vicina alla rigorosa. È il terreno di casa di ITS: un runbook di reperibilità è un manuale di manutenzione.

- Ogni passo all'imperativo, un'istruzione per passo, condizioni prima.
- Avvertenze prima del passo, prima il comando e poi il rischio.
- Limite di 22 parole applicato senza sconti: chi è di turno legge ogni frase una volta sola.

## Report di incidente e post mortem

Modalità: descrittiva. Solo passato prossimo. Una cronologia scritta con "abbiamo riscontrato" e "risulterebbe" nasconde quando le cose sono successe.

> **Prima:** Abbiamo riscontrato una problematica che potrebbe aver impattato la capacità di alcuni utenti di accedere al servizio.
> **Dopo:** Tra le 14:02 e le 14:31 il 12% delle richieste è fallito. Un rilascio delle 14:00 ha tolto il riscaldamento della cache.

ITS vieta le attenuazioni ("potrebbe aver impattato"). Il report dice quello che si sa e scrive "non lo sappiamo" per il resto. Questo si legge come più onesto perché lo è.

## Messaggi di commit e descrizioni di pull request

Modalità: oggetto all'imperativo, corpo descrittivo. La convenzione coincide già con ITS: riga di oggetto all'imperativo, fatti al passato nel corpo. Applica al corpo la tabella delle sostituzioni e il limite di 28 parole. Cancella "questa PR si propone di".

## Note di rilascio e changelog di API

Modalità: descrittiva. Una voce, una modifica, una frase quando è possibile. Le voci "Rottura di compatibilità" seguono lo schema dell'avvertenza, prima il comando: "Aggiorna le chiamate a `v2/users`. Il campo `name` è diventato `first_name` e `last_name`."

## Istruzioni per agenti AI (prompt, AGENTS.md, skill)

Modalità: procedurale. Un prompt di sistema è una procedura eseguita da un lettore che non può fare domande, cioè esattamente il lettore per cui STE è nato.

- Un'istruzione per frase: le regole restano citabili una per una e diventano difficili da seguire a metà.
- Una parola un significato: il modello smette di trattare "verifica", "controlla" e "valida" come tre operazioni diverse.
- Condizione prima ("Se la build fallisce, fermati"): le condizioni in coda i modelli le perdono.
- Niente condizionale: un modello legge "dovresti" come facoltativo. Scrivi "devi", oppure cancella la regola.

## Documenti di gara, capitolati e relazioni tecniche

Modalità: descrittiva per le relazioni, procedurale per le prescrizioni. Qui il burocratese è la norma di reparto e non un errore di stile, quindi il lavoro va fatto con due cautele.

- Le citazioni normative, i riferimenti di legge, i codici CIG e CUP e le formule richieste dal bando sono intoccabili. Non riscriverli.
- Tutto il resto segue le regole: via le nominalizzazioni, via il condizionale di cortesia, via "il suddetto" e "altresì".
- La commissione legge decine di offerte. Una frase di 22 parole con il verbo all'inizio vince su un periodo di 60 parole con tre subordinate.

> **Prima:** Si evidenzia come la scrivente società, in virtù della pluriennale esperienza maturata nel settore di riferimento, sia in grado di garantire l'espletamento del servizio secondo i più elevati standard qualitativi.
> **Dopo:** Lavoriamo in questo settore dal 2014. Abbiamo consegnato 23 progetti dello stesso tipo. Il servizio rispetta i requisiti dell'articolo 4 del capitolato.

## Macro di assistenza e aggiornamenti di stato

Modalità: descrittiva, limite di 28 parole. Chi legge una pagina di stato ha già un problema. Niente "ci scusiamo per il disagio arrecato": scrivi "L'API è rimasta ferma per 18 minuti. Abbiamo salvato i caricamenti fatti in quei minuti e li elaboriamo oggi."

## Preparazione alla traduzione e alla localizzazione

Modalità: rigorosa. È lo scopo originale di STE, e funziona come pre-editing anche per la traduzione automatica. Una parola per significato più grammatica completa toglie quasi tutta l'ambiguità. Se i tuoi documenti vengono tradotti, ITS riduce gli errori e il costo.

Attenzione al verso: ITS prepara bene l'italiano alla traduzione verso altre lingue. Non produce inglese conforme ad ASD-STE100. Per quello serve la skill inglese e il dizionario ufficiale.

## Testo di interfaccia e stati vuoti

Modalità: procedurale, limiti di lunghezza duri. Bottoni ed etichette sono nomi tecnici e non rientrano nelle regole. Il testo di corpo segue le regole: "Non hai ancora progetti. Crea un progetto per iniziare." A questa lunghezza non sopravvive nient'altro.

## Dove ITS non va usato

Pagine di marketing, post di lancio, voce di brand, narrativa, testo con un ritmo d'autore. ITS toglie la persuasione per costruzione, e toglie il ritmo insieme a quella. Scrivi quei testi con la tua voce, poi usa ITS per la documentazione a cui la pagina rimanda.
