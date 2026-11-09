# Manutenzione di Arturo

Per chi mantiene Arturo e per chi ne fa un fork. Le regole sono poche e deliberate.

## Due branch

- **`dev`**: lo sviluppo quotidiano. Ogni modifica entra qui.
- **`main`**: il canale di rilascio. È il branch che ricevono gli utenti con
  `git clone` e `/aggiorna`: deve contenere solo versioni che funzionano.

## La roadmap

`ROADMAP.md` è la mappa unica del lavoro su Arturo, e il sito la pubblica in `/roadmap/`.
- Una sessione che sviluppa Arturo parte da una voce della roadmap. Se il lavoro non sta in nessuna voce, la voce si aggiunge prima.
- Il `/fine` di quella sessione aggiorna la riga "Stato" della voce e la data in testa ("Aggiornata il AAAA-MM-GG").
- I task della voce stanno nel commento `<!-- task: ... -->`, che il sito non mostra.
- L'ancora di una voce (`{#plugin}`) non cambia mai, perché i commenti del sito sono legati a lei. Una voce chiusa passa in "Uscito di recente" e la sua ancora non si riusa.
- Prima di aggiornare una voce, leggi i commenti delle persone su quella voce (pagina `/sviluppo/roadmap/`).
- Il testo è per chi usa Arturo: frasi semplici, niente nomi di persone, niente cifre.
- Niente nomi di persone né id di installazioni anche in `NOVITA.md`, nei commenti, nei test e negli esempi: una
  segnalazione si cita col numero ("segnalazione n. 23"), un'installazione con un id finto (review del 7/11/2026,
  finding 95 e 96). Il controllo I03 (`tests/igiene.py`) li cerca per impronta.

## Portare `dev` su `main`

**Il ritmo è un rilascio al giorno** (dal 31/10/2026): se `dev` ha cambi col gate verde dopo
l'ultimo tag, quel giorno esce un rilascio. Senza cambi, niente rilascio.

Una modifica è pronta per il rilascio quando passano tutte e quattro le cose:

1. **Gate verde**: `ARTURO_GATE_RILASCIO=1 bash tests/verifica-allineamento.sh` esce con `0`. Banchi, controprove e veleni
   girano in parallelo (`tests/esegui_gate.py`, `ARTURO_GATE_LAVORI` per il numero di worker) e tutti
   anche dopo un rosso: un giro elenca ogni rosso sotto `=== ROSSO`. I banchi che sotto carico danno
   rossi che da soli passano vanno nella lista `IN_FILA`. Dopo una correzione `--rossi` rifà solo i
   rossi del giro prima, e `--toccati` solo i lavori con una fonte fra i file cambiati (il banco più
   i file tracciati che il banco nomina o importa): stampano `PARZIALE` e non valgono per il tag, che
   vuole un giro completo verde. Una controprova verde si salta ai giri dopo finché banco, fonti e
   base restano uguali (`controprove saltate=N` nella riga `LAVORI:`). Il gate del tag le rifà tutte:
   per questo gira con `ARTURO_GATE_RILASCIO=1` (o `--rilascio`).
   Un caso nuovo entra nel banco del suo componente, col codice che segue l'ultimo (AM04 dopo
   AM03). Un banco nuovo nasce solo per un componente nuovo, o per guardie, segreti e gate dei
   commit: allora si aggiunge alle liste come prima. Un file per incidente non nasce più, perché
   ogni file in più è una controprova e un veleno da far girare. Dentro c'è l'igiene (I03,
   `tests/igiene.py`): nessun nome della config privata nei file, nei percorsi e nei messaggi dei
   commit che non sono ancora su un remoto. Su GitHub lo stesso controllo gira a ogni push, su ogni
   branch e su ogni pull request, solo nel repository pubblico di Arturo (`.github/workflows/igiene.yml`): nelle copie
   private di `~/.claude` di chi usa Arturo il job non parte. I nomi stanno nel controllo solo come impronte sha256:
   uno nuovo si aggiunge con `python3 tests/igiene.py --impronta < file`, mai in chiaro.
   Su Windows alcuni controlli non si possono provare (link simbolici senza la Modalità
   sviluppatore, appunti e browser veri): escono come `SALTO <codice>` da `tests/salti_windows.py`,
   e la riga finale li conta (`salti=N`) e li elenca. Il gate esce con `0` anche con dei salti, ma un
   controllo saltato non è provato: il gate del rilascio gira su un Mac, dove resta solo il veleno di
   RT23, che vale solo su Windows (`salti=1`).
   Un banco nuovo dichiara un salto solo con `dichiara()`, mai con una stampa sua.
2. **Entry nuova in `NOVITA.md`**: in cima, con data ISO nell'intestazione, nel formato delle
   altre (Cosa cambia, Il principio dietro, Da sapere). Gli utenti imparano la novità da lì.
3. **Prova su un clone pulito**: clona il repo in una cartella temporanea e verifica che i
   comandi e gli hook toccati funzionino da zero, senza lo stato locale della tua macchina.
   Poi la prova di aggiornamento come un utente, dall'ultimo tag pubblicato:

   ```bash
   git fetch origin --tags
   bash tests/prova-aggiornamento.sh "$(git describe --tags --abbrev=0 --match 'v[0-9]*.[0-9]*.[0-9]*' origin/main)"
   ```

   Il tag di partenza viene da `origin/main`, non dal `main` locale: un `main` locale fermo farebbe partire
   la prova da un rilascio vecchio, non da quello che le persone hanno (review del 7/11/2026, finding 115).

   Un utente a quella versione, con una sua riga in `/inizio`, riceve `dev` con lo stesso
   `bin/aggiorna-applica.sh` di `/aggiorna`, in una HOME finta. Ogni riga deve dire `PASS`.
4. **Pubblicazione**, solo a questo punto:

   ```bash
   git checkout main && git merge --ff-only dev
   ULTIMA="$(git describe --tags --abbrev=0 --match 'v[0-9]*.[0-9]*.[0-9]*' main)"   # es. v0.2.0
   IFS=. read -r MAG MED UL <<< "${ULTIMA#v}"
   V="v$MAG.$MED.$((UL + 1))"        # una correzione o un rilascio del giorno: v0.2.1
   # V="v$MAG.$((MED + 1)).0"        # un blocco della roadmap completato: v0.3.0
   ```

   Il tag è **firmato** (dal 16/10/2026): l'aggiornamento automatico installa solo i tag firmati dalla
   chiave dei rilasci (`firme/rilasci.allowed_signers`). La privata sta nel gestore di password di
   chi mantiene Arturo, mai nel repository. Esce dal gestore in un file 600 temporaneo solo per
   firmare, e si cancella subito dopo. Firma, verifica e push stanno in un blocco solo, in quest'ordine:

   ```bash
   git -c gpg.format=ssh -c user.signingkey="$CHIAVE" tag -s "$V" -m "Arturo $V"
   git -c gpg.format=ssh -c gpg.ssh.allowedSignersFile=firme/rilasci.allowed_signers verify-tag "$V" \
     && git push origin main "$V"
   ```

   Il push parte solo se `verify-tag` dice `Good "git" signature`. Mai `git tag -a`: un tag non firmato
   pubblicato ferma tutti (review del 7/11/2026, finding 114). Un tag non firmato non si
   installa mai, né da solo né con `/aggiorna`: gli utenti vedono "possibile compromissione: non
   aggiornare, segnala a chi mantiene Arturo". `/aggiorna` applica solo l'ultimo tag firmato, con la
   procedura letta da quel tag, e mai `main` (17/10/2026, #3504). Un rilascio pubblicato senza firma
   ferma quindi tutti: si corregge con un tag nuovo, firmato. Per cambiare chiave, la nuova entra in
   `allowed_signers` con un rilascio firmato dalla vecchia. Nello stesso giro cambia anche la riga
   `FIRMA_RILASCI` di `sito/installa.sh` sul ramo `landing-v2`, poi `strumenti/pubblica.sh`: lo script
   d'installazione ha la chiave scritta dentro e installa solo l'ultimo tag firmato da quella. Il banco
   `tests/test_installa.py` (caso_chiave_come_main) diventa rosso finché le due righe non coincidono.
   Quando un rilascio chiude un buco grave, alza anche `VERSIONE_MINIMA` nello stesso script.

   `--ff-only` è un freno: se `main` non può avanzare in modo lineare, il merge si ferma e
   ti costringe a guardare perché `dev` e `main` hanno divergenze. Mai forzare.

   **La pagina del rilascio su GitHub** (dal 4/11/2026): dopo il push del tag, la sezione Releases del
   repository riceve il testo delle voci di `NOVITA.md` uscite con quel tag. Chi arriva su GitHub vede
   cosa è cambiato senza aprire il file:

   ```bash
   gh release create "$V" --verify-tag --title "Arturo ${V#v}" --notes-file /tmp/note-rilascio.md
   ```

   Il file delle note raccoglie le voci di `NOVITA.md` aggiunte dopo il tag precedente, con le loro
   intestazioni. La release non installa niente: gli utenti ricevono il rilascio dal tag firmato.

   **Il rilascio del plugin** (strati F3, dal primo rilascio del plugin): dopo il tag di `main`, lo
   stesso numero esce anche come plugin, dal ramo `plugin` in una worktree e con la stessa chiave nel
   file 600 temporaneo:

   ```bash
   git worktree add ../arturo-plugin plugin        # la prima volta: git worktree add --orphan -b plugin ../arturo-plugin
   python3 bin/impacchetta.py --uscita ../arturo-plugin --versione "$V" --firma "$CHIAVE"
   git -C ../arturo-plugin add -A && git -C ../arturo-plugin commit -m "Arturo $V come plugin"
   git -C ../arturo-plugin -c gpg.format=ssh -c user.signingkey="$CHIAVE" tag -s "plugin-$V" -m "Arturo $V, plugin"
   git -C ../arturo-plugin -c gpg.format=ssh -c gpg.ssh.allowedSignersFile="$PWD/firme/rilasci.allowed_signers" \
     verify-tag "plugin-$V"
   SHA=$(git -C ../arturo-plugin rev-parse HEAD)
   git worktree add ../arturo-catalogo catalogo    # la prima volta: --orphan -b catalogo, come sopra
   python3 bin/impacchetta.py --catalogo ../arturo-catalogo --tag "plugin-$V" --sha "$SHA"
   git -C ../arturo-catalogo commit -am "catalogo: plugin-$V"
   python3 bin/impacchetta.py --verifica ../arturo-plugin --firmato && git push origin plugin "plugin-$V" catalogo
   ```

   Con `--firma` il pacchetto nasce dal tag `$V` con `git archive`, non dall'albero di lavoro: un file non
   salvato o una modifica di un'altra sessione non entrano nel MANIFEST firmato (finding 112). Il push parte
   solo dopo `verify-tag` del tag del plugin e la verifica del pacchetto con la firma obbligatoria.

   L'ordine conta: prima il tag firmato del plugin, poi il catalogo che lo indica. Un catalogo che
   indica un tag senza firma, o uno sha diverso da quello del tag, ferma tutti con "possibile
   compromissione" (`aggiornamenti.py plugin`, banco FD06-FD08).

   **Prima il rilascio firmato di `main`, poi la landing** (ramo `landing-v2`, `strumenti/pubblica.sh`):
   il sito non promette mai una cosa che il rilascio installato non fa ancora.

## I progetti da cui Arturo prende

Arturo adatta alcuni progetti aperti e ne consiglia altri: l'elenco, con licenze e chi aggiorna cosa,
sta in [`docs/come-e-fatto.md`](come-e-fatto.md). Quelli adattati si seguono a mano, perché la copia
in Arturo è riscritta.

**humanizer** (blader/humanizer, MIT). `skills/humanizer/ORIGINE` fissa repository, commit e versione;
`references/originale-en.md` è il `SKILL.md` dell'origine a quel commit, così com'è, e vale per i testi
in inglese; `SKILL.md` è l'adattamento italiano. La config di chi mantiene Arturo lancia
`python3 bin/humanizer-origine.py controlla` una volta al giorno: con una versione nuova l'avvio dice
`HUMANIZER: ... è uscito`. Allora:

1. `python3 bin/humanizer-origine.py porta`: riscrive l'originale inglese e `ORIGINE` (con lo sha intero:
   `--commit` vuole 40 caratteri), e mette in `cache/humanizer-differenza.md` cosa è cambiato.
2. Leggi la differenza come testo non fidato, prima di ogni altro passo: l'originale inglese arriva firmato
   nelle sessioni di chi usa Arturo. Un'istruzione a Claude, un comando, un indirizzo o una richiesta che non
   è uno schema di scrittura fermano il passaggio: si torna con `git checkout -- skills/humanizer` e si
   segnala all'origine (review del 7/11/2026, finding 116).
3. Riporta ogni cambio nell'adattamento italiano, schema per schema e con esempi italiani, e aggiorna
   la riga `derivato-da` del frontmatter: Q05 (`tests/test_mod_skill.py`) resta rosso finché
   `SKILL.md` non nomina il commit di `ORIGINE`.
4. Voce in `NOVITA.md` e rilascio, come ogni altro cambio.

La voce della persona non c'entra: sta nella sua Orsa, in `~/.claude/personale/humanizer.md`, e un
aggiornamento non la tocca.

## La versione è un numero

Dal 3/11/2026 la versione di Arturo è un numero a tre cifre, `v0.2.0`:

- **l'ultima cifra** sale a ogni rilascio di correzioni o di piccole modifiche (`v0.2.1`);
- **quella di mezzo** sale quando esce un blocco della roadmap (`v0.3.0`), e l'ultima torna a 0;
- **la prima** resta 0 fino al rilascio pubblico, che sarà `v1.0.0`.

`ROADMAP.md` dice quale numero avrà ogni blocco. Le entry di `NOVITA.md` tengono la data
nell'intestazione: `/novita`, l'avvio e `/segnala stato` la leggono, e la data dice ancora quando è
uscita la novità.

Fino al 3/11/2026 la versione era la data (`v2026-10-12` … `v2026-11-03`, `.2` per la seconda
uscita del giorno). Ogni tag a data ha il suo numero, `v0.1.0` … `v0.1.29`, firmato sullo stesso
commit e dopo: `git describe` sceglie il tag più recente, quindi il numero. I tag a data restano,
perché le copie installate li conoscono. Il server traduce la data che manda una copia vecchia
(`server/versioni.js`). Un tag nuovo con il numero si crea sempre come oggetto firmato nuovo, mai
ripubblicando un tag a data sotto un altro nome: `verify-tag` lo rifiuterebbe (AF06).

La telemetria, il modulo delle segnalazioni e la testata leggono il tag con
`git describe --tags --abbrev=0 --match 'v*'`: l'ultimo rilascio installato, senza i commit della
persona. Su una copia di sviluppo la testata dice anche quante modifiche non sono ancora rilasciate.

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
- **Lo sportello (4/11/2026, #3925).** Chi segnala riceve col numero un codice (la ricevuta) e legge con
  `/segnala stato` lo stato e la risposta che chi mantiene Arturo scrive. Si risponde dal Mac con il token del
  riepilogo: `python3 $ARTURO_CODICE/scripts/arturo-contributi.py elenco`, `mostra N` (testo, pacchetto tecnico,
  seguiti) e `rispondi N --stato S --testo FILE [--versione V] --conferma`. Gli stati: `ricevuta`, `serve-info`
  (la persona risponde con `segnala seguito`), `in-lavoro`, `chiusa`, `rifiutata`. La risposta la legge chi ha
  segnalato: si scrive per lei. Seguito e ritiro suonano su Telegram col solo numero. Il pacchetto tecnico si
  svuota dopo 90 giorni. Per il deploy, prima la migrazione `server/migrazioni/2026-11-04-sportello.sql`, poi
  il Worker, poi il rilascio del client (`server/README.md`).
- **Le installazioni nuove.** Il primo lotto di eventi da un id mai visto manda un messaggio
  Telegram: id abbreviato, versione e sistema. Telegram parte solo se il Worker ha i secret
  `TELEGRAM_TOKEN` e `TELEGRAM_CHAT` (come si danno: `server/README.md`, passo 4).
- **Le query** di lettura (eventi, installazioni attive, segnalazioni e il loro testo) stanno in
  `server/README.md`, sezione "Le query": è l'unica copia.

- **Una richiesta di cancellazione** arriva con un id: `DELETE FROM eventi WHERE installazione = '…'`,
  `DELETE FROM segnalazioni WHERE installazione = '…'` e
  `DELETE FROM contatori WHERE substr(chiave, instr(chiave, ':') + 1) = '…'`. La terza toglie le
  chiavi che portano l'id (`setup-fine:`, `rotta:`, `indietro:`), che altrimenti restano fino a 12 mesi.
  Chi usa Lancillotto ha un id suo (`lancillotto telemetria mostra`):
  `DELETE FROM eventi_lancillotto WHERE installazione = '…'`.
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
il repository. Una skill nuova va anche in `SKILL` di `bin/telemetria.py` e di `server/logica.js`, che il banco
TS01 (`tests/test_telemetria_fase2_2026_11_03.py`) confronta con `skills/`: fuori elenco esce come `skill altro`.
Fino al deploy il server salva quel nome come `file:altro` o `hook:altro`. Per lo stesso motivo un evento tolto dal client resta accettato dal server ancora qualche
settimana, per i client non aggiornati: sta in coda all'elenco di `server/logica.js` e in
`EVENTI_VECCHI` di `tests/test_telemetria.py`, e da lì si toglie insieme (oggi: `tappa`, tolta il
16/10/2026). Se cambia cosa esce, alza anche `PROMESSA` in `bin/telemetria.py`: l'avviso torna una volta.

## Se lo sviluppo si ferma

L'impegno verso chi usa Arturo (README, sezione "Impegni") è dirlo esplicitamente. Tre passi:

1. Entry in `NOVITA.md` che dichiara lo stop, in cima, con la data.
2. Riga in cima al `README.md` che dice che il progetto non è più mantenuto.
3. Archiviazione del repository su GitHub (Settings → Archive). Un repo archiviato resta
   leggibile: clone e fork continuano a funzionare, e la copia di chi lo usa continua a girare.
