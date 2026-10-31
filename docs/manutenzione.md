# Manutenzione di Arturo

Per chi mantiene Arturo e per chi ne fa un fork. Le regole sono poche e deliberate.

## Due branch

- **`dev`**: lo sviluppo quotidiano. Ogni modifica entra qui.
- **`main`**: il canale di rilascio. È il branch che ricevono gli utenti con
  `git clone` e `/aggiorna`: deve contenere solo versioni che funzionano.

## Portare `dev` su `main`

**Il ritmo è un rilascio al giorno** (dal 31/10/2026): se `dev` ha cambi col gate verde dopo
l'ultimo tag, quel giorno esce un rilascio. Senza cambi, niente rilascio.

Una modifica è pronta per il rilascio quando passano tutte e quattro le cose:

1. **Gate verde**: `bash tests/verifica-allineamento.sh` esce con `0`. Dentro c'è l'igiene (I03,
   `tests/igiene.py`): nessun nome della config privata nei file, nei percorsi e nei messaggi dei
   commit che non sono ancora su un remoto. Su GitHub lo stesso controllo gira a ogni push, su ogni
   branch, solo nel repository pubblico di Arturo (`.github/workflows/igiene.yml`): nelle copie
   private di `~/.claude` di chi usa Arturo il job non parte. I nomi stanno nel controllo solo come impronte sha256:
   uno nuovo si aggiunge con `python3 tests/igiene.py --impronta < file`, mai in chiaro.
2. **Entry nuova in `NOVITA.md`**: in cima, con data ISO nell'intestazione, nel formato delle
   altre (Cosa cambia, Il principio dietro, Da sapere). Gli utenti imparano la novità da lì.
3. **Prova su un clone pulito**: clona il repo in una cartella temporanea e verifica che i
   comandi e gli hook toccati funzionino da zero, senza lo stato locale della tua macchina.
   Poi la prova di aggiornamento come un utente, dall'ultimo tag pubblicato:

   ```bash
   bash tests/prova-aggiornamento.sh "$(git describe --tags --abbrev=0 main)"
   ```

   Un utente a quella versione, con una sua riga in `/inizio`, riceve `dev` con lo stesso
   `bin/aggiorna-applica.sh` di `/aggiorna`, in una HOME finta. Ogni riga deve dire `PASS`.
4. **Pubblicazione**, solo a questo punto:

   ```bash
   git checkout main && git merge --ff-only dev
   V="v$(grep -m1 '^## ' NOVITA.md | grep -oE '[0-9]{4}-[0-9]{2}-[0-9]{2}')"
   git rev-parse -q --verify "refs/tags/$V" >/dev/null && V="$V.2"   # seconda uscita nello stesso giorno
   git tag -a "$V" -m "Arturo $V" && git push origin main "$V"
   ```

   Dal 16/10/2026 il tag è **firmato**: l'aggiornamento automatico installa solo i tag firmati dalla
   chiave dei rilasci (`firme/rilasci.allowed_signers`). La privata sta nel gestore di password di
   chi mantiene Arturo, mai nel repository. Esce dal gestore in un file 600 temporaneo solo per
   firmare, e si cancella subito dopo. Al posto di `git tag -a`:

   ```bash
   git -c gpg.format=ssh -c user.signingkey="$CHIAVE" tag -s "$V" -m "Arturo $V"
   git -c gpg.format=ssh -c gpg.ssh.allowedSignersFile=firme/rilasci.allowed_signers verify-tag "$V"
   ```

   Il push parte solo se `verify-tag` dice `Good "git" signature`. Un tag non firmato non si
   installa mai, né da solo né con `/aggiorna`: gli utenti vedono "possibile compromissione: non
   aggiornare, segnala a chi mantiene Arturo". `/aggiorna` applica solo l'ultimo tag firmato, con la
   procedura letta da quel tag, e mai `main` (17/10/2026, #3504). Un rilascio pubblicato senza firma
   ferma quindi tutti: si corregge con un tag nuovo, firmato. Per cambiare chiave, la nuova entra in
   `allowed_signers` con un rilascio firmato dalla vecchia.

   `--ff-only` è un freno: se `main` non può avanzare in modo lineare, il merge si ferma e
   ti costringe a guardare perché `dev` e `main` hanno diverto. Mai forzare.

## La versione è la data

Non c'è semver. La versione di Arturo è la data dell'entry in cima a `NOVITA.md`:
`## 2026-09-16 — …` vuol dire "versione del 16 settembre 2026". Il tag `v2026-09-16` che
accompagna ogni pubblicazione è la stessa data scritta in un punto che Git sa leggere: non è un
secondo sistema di versioni. Serve perché la data del commit locale cambia con ogni `/fine`,
e perché due uscite nello stesso giorno si distinguono solo con `.2`. La telemetria e il modulo
delle segnalazioni leggono il tag con `git describe --tags --abbrev=0 --match 'v*'`: l'ultimo
rilascio installato, senza i commit della persona.

**Mai riscrivere `main` dopo un tag.** `/aggiorna` confronta la versione pubblicata con quella
che la copia dell'utente conosceva, e se la nuova non discende dalla vecchia si ferma con
`STORIA RISCRITTA`: è lo stesso segnale che darebbe un repository compromesso.

## Misurare l'uso

Arturo manda una telemetria accesa di default (README, Impegni), che serve a migliorarlo. Il server è in
`server/`: un Worker Cloudflare su `arturo-dati.stellakamikaze.org` con un database D1 `arturo`.

- **Dove migliorare Arturo.** Il riepilogo del lunedì si apre con questa sezione, sugli ultimi 30
  giorni: fase di `/setup` dove si fermano le installazioni che non arrivano in fondo, guardie che
  chiedono conferma con la quota di sì (vicina al 100% vuol dire domanda inutile), sommate per guardia
  (`confermeGuardie`) e per regola dove la guardia la dice (`conferme`: block-dangerous e
  commit-secret-gate), guardie che si rompono, installazioni rimaste indietro (`indietro`: attive
  negli ultimi 3 giorni senza un rilascio uscito da almeno 3, anche su Telegram ogni mattina),
  aggiornamenti rifiutati o annullati per versione, ritenzione a 7, 30 e 60 giorni,
  versioni di Claude Code. Dal 24/10/2026 la finestra di 30 giorni vale per tutto il blocco, setup e
  ritenzione compresi, e contano solo le installazioni viste dal server in almeno due giorni (salvo la
  ritenzione), come per le guardie. Sono numeri, non verdetti: cosa correggere lo decide chi mantiene Arturo. Ogni correzione nata
  da un segnale lo dice nella sua voce di `NOVITA.md` ("Da sapere: lo mostrava la telemetria").
- **Il riepilogo in JSON.** `GET /v1/riepilogo?dal=AAAA-MM-GG&al=AAAA-MM-GG` con l'intestazione
  `authorization: Bearer <token>` dà lo stesso riepilogo, per la routine che propone le correzioni.
  Il token è il secret `RIEPILOGO_TOKEN` del Worker (almeno 32 caratteri): senza, la rotta risponde 401.
  Le statistiche delle guardie contano solo le installazioni viste dal server in almeno due giorni
  diversi, e ogni numero porta quante installazioni lo producono (`installazioni`). Regola per la
  routine e per chi legge: **una guardia non si allenta sulla sola base della telemetria**.
  Gli eventi arrivano da id casuali che chiunque può creare: una quota di sì vicina al 100% è un
  indizio da verificare (una segnalazione, una prova su un'installazione pulita), mai la prova
  (17/10/2026, #3507).
- **Il recap di ogni mattina.** Ogni mattina alle 8 il Worker manda a chi mantiene il recap del
  giorno prima: installazioni attive, versioni, sistemi, comandi usati, guardie che hanno bloccato,
  esiti di `/aggiorna`, config rotte, deriva (per ogni installazione il cui elenco è cambiato:
  OSTACOLO se un hook di Arturo è spento, una guardia è modificata o un comando modificato va in
  conflitto con un aggiornamento), segnalazioni, eventi scartati perché fuori elenco, avvisi Telegram ed
  email non partiti (contatori `scartati`, `telegram-ko`, `email-ko`, senza id, dal 24/10/2026). Nei giorni
  in cui tutti questi numeri sono zero non parte.
- **La config rotta arriva subito.** Un'email `[Arturo] Config rotta su un'installazione`, una sola
  al giorno per installazione, dentro un tetto di 20 tutto suo.
- **Il riepilogo del lunedì.** Il lunedì arriva sempre lo stesso riepilogo della settimana prima, da lunedì a
  domenica in ora di Roma, anche vuoto: se manca, il server è fermo. In più ha la deriva di tutte le
  installazioni che ne hanno una, anche ferma, e le guardie frequenti: almeno 5 blocchi della stessa guardia nella settimana sulla
  stessa installazione, il segno che Arturo intralcia. Poi il Worker cancella gli eventi più vecchi
  di 12 mesi.
- **Le segnalazioni.** Ogni segnalazione di `/segnala` col canale `arturo` resta in D1, e arriva per
  email e su Telegram come campanello (24/10/2026): mai il testo, il titolo o l'id completo. Dal
  27/10/2026 porta numero, tipo in parole, le prime 8 cifre dell'installazione, versione e sistema, e
  il link `LEGGI_SEGNALAZIONI/<n>` alla pagina privata dell'admin, che legge il testo da D1 col token
  del riepilogo; l'email aggiunge l'ora di arrivo. Il feedback del sito arriva su
  Telegram allo stesso modo, senza testo né email, e il vocale non si accetta più. Le segnalazioni si
  cancellano dopo 12 mesi, come gli eventi. Quelle aperte da GitHub sono issue con il titolo
  `[problema]`, `[proposta]` o `[integrazione]`.
- **Le installazioni nuove.** Il primo lotto di eventi da un id mai visto manda un messaggio
  Telegram: id abbreviato, versione e sistema. Telegram parte solo se il Worker ha i secret
  `TELEGRAM_TOKEN` e `TELEGRAM_CHAT` (come si danno: `server/README.md`, passo 4).
- **Le query** di lettura (eventi, installazioni attive, segnalazioni e il loro testo) stanno in
  `server/README.md`, sezione "Le query": è l'unica copia.

- **Una richiesta di cancellazione** arriva con un id: `DELETE FROM eventi WHERE installazione = '…'`,
  `DELETE FROM segnalazioni WHERE installazione = '…'` e
  `DELETE FROM contatori WHERE substr(chiave, instr(chiave, ':') + 1) = '…'`. La terza toglie le
  chiavi che portano l'id (`setup-fine:`, `rotta:`, `indietro:`), che altrimenti restano fino a 12 mesi.
  Il feedback del sito non ha un id: si cancella con l'email lasciata nel modulo,
  `DELETE FROM feedback WHERE email = '…'`. Una segnalazione senza id o un feedback senza email si
  cancella col suo numero (`WHERE id = N`), se la persona lo dice.
  Le copie già uscite verso Gmail e Telegram non si raggiungono dal server, e la pulizia dei 12 mesi non
  le tocca: il recap e il riepilogo del lunedì (prime 8 cifre dell'id con deriva, guardie frequenti e
  installazioni indietro), gli avvisi di installazione nuova, setup finito, installazione indietro e
  config rotta. Prima del 24/10/2026 portavano anche il testo delle segnalazioni e del feedback. Chi
  mantiene Arturo le cancella a mano nella casella e nella chat; l'elenco intero sta in `docs/privacy.md`
  ("Chi li riceve"). La stessa procedura sta in `server/README.md` (banco CP01).

Dal lato GitHub restano le misure di prima:

```bash
gh api repos/stellakamikaze/arturo/traffic/clones --jq '{count,uniques}'
gh repo view stellakamikaze/arturo --json stargazerCount,forkCount
gh issue list --repo stellakamikaze/arturo --state all
```

Un cambio dell'elenco degli eventi tocca tre posti che il banco M09 confronta: `bin/telemetria.py`,
`server/logica.js` e l'Impegno 3 del README. Gli eventi però sono raccontati anche in
`server/README.md`, nell'avviso di `bin/telemetria.py`, nella FASE 0 di
`commands/setup.md` e nella landing: prima del rilascio, `git grep -n` sul nome di un evento. Il server va pubblicato **prima** del client: un
evento o un valore che il server non conosce si scarta e si conta in `scartati` (dal 24/10/2026; prima
faceva rifiutare il lotto intero), quindi un client più nuovo del server perde quei dati. Anche una
guardia, una regola o un comando nuovi vanno nelle liste chiuse di `server/logica.js` (`GUARDIE`,
`REGOLE`, `COMANDI`), che il banco TF03 (`tests/test_telemetria_f1_2026_10_24.py`) confronta con il
repository e con `bin/telemetria.py`. Lo stesso vale per una skill, un agent, un file della radice o un
hook di `settings.json` nuovi: vanno in `DERIVA_NOMI` e `DERIVA_HOOK`, che il banco TF05 confronta con
il repository. Fino al deploy il server salva quel nome come `file:altro` o `hook:altro`. Per lo stesso motivo un evento tolto dal client resta accettato dal server ancora qualche
settimana, per i client non aggiornati: sta in coda all'elenco di `server/logica.js` e in
`EVENTI_VECCHI` di `tests/test_telemetria.py`, e da lì si toglie insieme (oggi: `tappa`, tolta il
16/10/2026). Se cambia cosa esce, alza anche `PROMESSA` in `bin/telemetria.py`: l'avviso torna una volta.

## Se lo sviluppo si ferma

L'impegno verso chi usa Arturo (README, sezione "Impegni") è dirlo esplicitamente. Tre passi:

1. Entry in `NOVITA.md` che dichiara lo stop, in cima, con la data.
2. Riga in cima al `README.md` che dice che il progetto non è più mantenuto.
3. Archiviazione del repository su GitHub (Settings → Archive). Un repo archiviato resta
   leggibile: clone e fork continuano a funzionare, e la copia di chi lo usa continua a girare.
