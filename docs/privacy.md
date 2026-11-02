# Privacy: cosa raccoglie Arturo e cosa puoi fare

Arturo manda a chi lo mantiene pochi dati d'uso, per capire dove le persone si bloccano e correggerlo.
Questa pagina dice chi tiene quei dati, quali sono, per quanto restano e come li cancelli.
L'elenco esatto degli eventi sta nell'Impegno 3 del [README](../README.md#impegni) e nel codice di `bin/telemetria.py`.

## Chi tiene i dati

Il titolare è chi mantiene Arturo. Contatto: federico@stellakamikaze.org.
Scrivi a questo indirizzo per ogni domanda o richiesta su questa pagina.

## Base giuridica

La base giuridica è il legittimo interesse (art. 6.1.f del GDPR) di chi mantiene Arturo a migliorare uno strumento che usi.
Per questo la telemetria è accesa di default, raccoglie solo eventi da un elenco chiuso e mai contenuti, e la spegni in un comando (vedi "I tuoi diritti").
Quando cambia cosa esce, Arturo te lo dice alla prima sessione dopo l'aggiornamento, prima di mandare i dati nuovi.

## Non sono dati anonimi

Ogni installazione ha un id casuale, creato da Arturo sul tuo computer. L'id non contiene il tuo nome, la tua email o il tuo computer.
L'id però resta sempre lo stesso. Chi mantiene Arturo può sapere quale persona c'è dietro un id se la conosce: per esempio se gli hai detto tu di avere installato Arturo ieri.
Per questo i dati non sono anonimi, e questa pagina li tratta come dati personali.

## Cosa si raccoglie e per quanto

| Dato | Cosa contiene | Da dove arriva | Quanto resta |
|---|---|---|---|
| Eventi d'uso | L'id casuale, il rilascio di Arturo installato (un tuo tag non esce), il sistema (Darwin, Linux, Windows), il giorno (mai l'ora) e un evento da un elenco chiuso: comandi di Arturo, guardie che bloccano o chiedono, esiti degli aggiornamenti, fase di `/setup`, file di Arturo cambiati, versione di Claude Code, skill di Arturo usate. Dal 3/11/2026, alla chiusura di ogni sessione, anche la sua durata e quanti messaggi hai scritto, solo in fasce larghe (meno di 5 minuti, fino a 30, fino a 2 ore, oltre; 1, da 2 a 5, da 6 a 20, oltre 20 messaggi): per contarli Arturo legge sul tuo computer la cronologia della sessione, e non ne esce niente altro | Da solo, al massimo ogni sei ore | 12 mesi |
| Segnalazioni di `/segnala` | Tipo, titolo e testo che hai letto e approvato, versione, sistema, l'id solo con la telemetria accesa | Solo dopo il tuo sì | 12 mesi |
| Feedback dal sito | Tipo, testo, email solo se la scrivi tu | Dal modulo del sito | 12 mesi |
| Contatori senza id | Numeri del giorno: download dal sito, eventi scartati, avvisi non partiti | Dal server | 12 mesi |
| Eventi di Lancillotto (dal 25/10/2026) | Solo se usi Lancillotto, l'app che annota sul tuo Mac come lavori: un suo id casuale, la versione, la versione di macOS, il giorno e un evento da un elenco chiuso (passi della guida, permessi sì o no, fasce di eventi, MB e ore del giorno, sensori guasti, browser senza indirizzo, comandi della CLI, routine contate). Il registro di Lancillotto resta sul Mac: non escono app, siti, titoli, file né testo. Elenco in `lancillotto/telemetria.py` e in `server/lancillotto.js` | Ogni ora, se nella guida hai detto sì; si spegne dalla finestra di Lancillotto | 12 mesi |

Cosa non esce mai: prompt, risposte, file tuoi, percorsi del tuo computer, nomi, testi.
Di un file tuo, per esempio una skill che hai scritto tu, esce solo `file:altro`. Il testo di una tua skill esce solo se la proponi tu con `/proponi`: come una segnalazione, dopo che hai letto la copia ripulita e detto sì. Di un comando tuo esce solo `altro`.
Di un segreto fermato in un commit esce solo la famiglia, come `segreto-cloud`, mai il servizio.
Il server non salva il tuo indirizzo IP. Il modulo del sito accetta solo testo scritto, fino a 64 KB per messaggio.

Sul tuo computer restano la coda degli eventi non ancora partiti (`~/.claude/data/telemetria/coda.jsonl`) e lo stato della telemetria (`~/.claude/session-env/telemetria.json`).
Li vedi con `python3 ~/.claude/bin/arturo telemetria mostra`.

## Il ritratto di /setup

Nelle fasi 2b e 2c `/setup` ti chiede due volte un sì, per conoscerti prima di scrivere il tuo `CLAUDE.md`. Un no non blocca niente.

- **Cosa legge, col primo sì.** Le tue ultime conversazioni con Claude Code: solo le frasi che hai scritto tu, tagliate, e le note che Claude Code ha preso da solo. Legge anche le ultime richieste nella cronologia di Claude Code (`~/.claude/history.jsonl`), comprese quelle di conversazioni che hai cancellato, e le conversazioni nella copia fatta all'installazione. Poi ti chiede di incollare le istruzioni dei tuoi Progetti di claude.ai, se li usi.
- **Cosa legge, col secondo sì.** Ti mostra prima l'elenco delle cartelle. Poi legge i nomi di file e cartelle fino a tre livelli, e l'inizio di al massimo 12 documenti di testo in Documenti, Scrivania e nelle cartelle dei progetti. Da Download legge solo i nomi, anche quando una cartella di lavoro sta dentro Download. Se al primo sì hai risposto no, non apre le conversazioni nemmeno per trovare le cartelle di lavoro.
- **Cosa non legge mai.** Cartelle di sistema e dei programmi, cartelle nascoste, `.ssh`, chiavi, password manager, file `.env`, credenziali, e i documenti che dal nome o dal testo sembrano d'identità, di salute o di banca. Dai testi che legge toglie password scritte in chiaro, chiavi, IBAN, numeri di carta, codici fiscali, telefoni e le email che non sono la tua. Le esclusioni stanno nel codice di `bin/ritratto.py`, non in un'istruzione a Claude.
- **Dove va.** Quello che legge passa dalla conversazione con Anthropic, come ogni richiesta che scrivi a Claude. Non va a chi mantiene Arturo.
- **Cosa esce in telemetria.** Solo il passaggio per le due fasi, `setup fase:2b` e `setup fase:2c`. Mai conteggi, esiti, nomi di file o testi.
- **Cosa resta sul computer.** Arturo non salva il ritratto in nessun file. Quello che legge resta nella cronologia della conversazione di `/setup`, che Claude Code tiene sul tuo computer e cancella da sola dopo 90 giorni. Arturo non ne fa altre copie. La cronologia sta in `~/.claude/projects`, e i 90 giorni li fissa `cleanupPeriodDays` nel `settings.json` di Arturo. Oltre a quella resta il `CLAUDE.md` che approvi prima che venga scritto.

## Chi li riceve

- **Cloudflare** ospita il server e il database (Workers e D1). È il solo posto dove stanno gli eventi e i testi.
- **Telegram** riceve questi messaggi per chi mantiene Arturo:
  - il campanello di una segnalazione: numero, tipo, le prime 8 cifre dell'id, la versione di Arturo, il sistema e il link alla pagina privata che la mostra a chi mantiene Arturo;
  - il campanello di un feedback dal sito: numero, tipo e origine;
  - l'avviso di un'installazione nuova e di un `/setup` finito: le prime 8 cifre dell'id, la versione di Arturo e il sistema;
  - l'avviso di un'installazione rimasta indietro: le prime 8 cifre dell'id, il rilascio installato, il giorno dell'ultima attività e il rilascio che manca;
  - l'avviso di un download dal sito: la pagina, Mac o Windows e quanti download ci sono stati quel giorno, senza id.
- **Gmail** riceve queste email per chi mantiene Arturo:
  - lo stesso campanello delle segnalazioni, con l'ora di arrivo e il link alla pagina privata;
  - l'avviso di una config rotta: le prime 8 cifre dell'id, la versione di Arturo e il tipo di guasto;
  - il recap di ogni mattina e il riepilogo del lunedì: i numeri degli eventi sommati fra le installazioni e, per installazione con le prime 8 cifre dell'id, i file e gli hook di Arturo cambiati o spenti, le guardie che bloccano spesso e le installazioni rimaste indietro;
  - dal 2/11/2026, nel riepilogo del lunedì, la sezione "Chi lo usa": per installazione, con le prime 8 cifre dell'id, i giorni attivi della settimana, le sessioni, il comando più usato e l'ultimo giorno visto.

Chi mantiene Arturo vede gli stessi numeri per installazione anche in una sua pagina privata, protetta da accesso, dove dà un nome agli id delle persone che conosce. Quei nomi stanno solo sul suo server, non nel server della telemetria e non in questo repository.

Telegram e Gmail non ricevono mai il testo di una segnalazione o di un feedback, la tua email o l'id completo.
Queste copie stanno fuori dal server: la pulizia dei 12 mesi e la cancellazione sul server non le raggiungono.
Chi mantiene Arturo le cancella a mano nella chat e nella casella, se lo chiedi.
I messaggi e le email partiti prima del 24/10/2026 possono contenere anche il titolo e il testo di una segnalazione, l'email e il testo di un feedback.
Nessun altro riceve i dati. Non si vendono e non servono per pubblicità.

## I tuoi diritti

- **Vedere cosa parte.** `python3 ~/.claude/bin/arturo telemetria mostra` stampa l'id e gli eventi in coda, così come partono.
- **Accesso.** Scrivi a federico@stellakamikaze.org con l'id che ti mostra `mostra`: ricevi i dati legati a quell'id.
- **Cancellazione.** Scrivi allo stesso indirizzo con l'id: chi mantiene Arturo cancella i tuoi eventi e le tue segnalazioni dal server, e a mano le copie su Telegram e Gmail (vedi "Chi li riceve").
- **Opposizione.** `python3 ~/.claude/bin/arturo telemetria spegni` spegne la telemetria e svuota la coda. Valgono anche `ARTURO_TELEMETRIA=0` e `DO_NOT_TRACK=1`. `/segnala` continua a funzionare: ogni segnalazione parte solo col tuo sì.
- **Reclamo.** Puoi rivolgerti al Garante per la protezione dei dati personali (garanteprivacy.it).

Quando cambia cosa esce, Arturo te lo dice di nuovo alla prima sessione.

## Dove sta il codice

Il codice è pubblico, con licenza MIT:

- `bin/telemetria.py`: cosa si registra sul tuo computer, gli elenchi chiusi e l'invio;
- `hooks/deriva.py` e `bin/aggiorna-applica.sh`: i file di Arturo cambiati o in conflitto;
- `server/`: cosa accetta il server, cosa salva e quando cancella.
