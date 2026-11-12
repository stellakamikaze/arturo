---
description: >-
  Chiude la sessione in dieci fasi: inventario e destino dei file, validate e commit per pathspec, handoff
  con i todo e chi agisce, gate, retention, CLAUDE.md, memoria, sync della config, una domanda per Arturo.
  A sessione vuota fa solo il sync. /fine [--full] [salva] [--rotazione] [note], rilanciabile. Con
  --rotazione è il fine leggero che Claude lancia a ogni passo chiuso, seguito dal tool ruota del mod
  rotazione (/clear e /inizio da soli). Non apre sessioni (/inizio).
argument-hint: "[--full] [salva] [--rotazione] [note opzionali]"
---

# Fine sessione

Argomenti e note della persona: **$ARGUMENTS**. Con `--full`, o quando la loro condizione è vera, applica
anche gli opzionali in fondo. `salva` dà in anticipo il sì alle note della FASE 8, tranne il `CLAUDE.md` personale.

Tre regole per tutte le fasi:
- **Dentro /fine non si sviluppa.** Un gap, un fix o un test rosso diventa un todo con un numero.
- **/fine si può rilanciare senza danni.** L'handoff si riscrive, un todo che c'è non si ricrea, un commit vuoto non parte.
- **Un destino incerto non ferma la chiusura.** Il file resta dov'è e l'handoff dice dove sta.

## Modo rotazione (`--rotazione`)

Lo lancia Claude, mai la persona, a ogni compito chiuso: uno step del piano compiuto o un incarico finito,
con i test verdi e la sonda fatta. Parte sempre, anche col contesto leggero e anche quando non c'è un passo
dopo: è la raccolta dei risultati (handoff del giorno, todo, memoria, commit). Un compito conta quando ha
lasciato una traccia da salvare: un commit, un file, un documento, una decisione, un todo cambiato.
Un'azione senza traccia (accendere la musica, leggere uno stato) non lo fa partire.
La rotazione è il secondo tempo, e solo se il passo dopo è di Claude: dopo la coda il tool `ruota` del mod
`rotazione` fa `/clear` e `/inizio` da solo, e il lavoro riparte sul passo dopo.

- **Una volta al giorno è completo.** Se `~/.claude/data/handoffs/<slug>/.ultimo-fine-completo` non porta la
  data di oggi e sono passate le 18, questo giro segue tutte le fasi, poi ruota. Il `/fine` scritto dalla
  persona è sempre completo e non ruota.
- **Fasi del fine leggero:** FASE 1 senza `structural-completeness-reviewer`, poi 2, 3, 4, 5, 7 solo se è
  cambiato un fatto durevole del progetto, 8, e la 9 con `python3 ~/.claude/bin/fine-coda.py --leggero`.
  Saltano la FASE 6 (la retention aspetta il fine completo) e la FASE 10.
- **Un handoff per giornata.** Prima del blocco della FASE 4 cerca nel mirror l'ultimo handoff con
  `- Rotazione: <oggi>`: se c'è, riscrivi quello e aggiorna la sua riga `- Sessione:`. Se non c'è, il
  nuovo handoff porta `- Rotazione: <AAAA-MM-GG>` sotto `- Sessione:`.
- **Il piano sopravvive al /clear.** Se la sessione lavora su un piano, l'handoff porta
  `- Piano: <percorso in ~/.claude/plans/> · step <N> di <M> fatto`, e la Ripartenza nomina lo step dopo.
- **Le note che chiedono il sì non si perdono.** Nel fine leggero non si chiede niente: le note nuove, i
  dati su persone e le righe del `CLAUDE.md` personale vanno nella sezione `## Note in attesa del sì`
  dell'handoff, una per riga col percorso e il testo. Il prossimo `/fine` scritto dalla persona le propone.
- **Poi la rotazione.** Con la coda a `rc=0` scegli il passo dopo. Se è un passo di Claude (Chi `io`), la
  chiusura è una riga ("ruoto: step N fatto · commit abc1234 · riparto da <passo>") e subito la chiamata
  `mcp__arturo__ruota` con `progetto` (lo slug) e `compito` (il passo dopo in una frase). È l'ultima
  azione del turno.
- **Niente rotazione, chiusura normale**, se: la coda esce con un codice diverso da 0; il passo dopo chiede
  la persona (una decisione, un invio, un pagamento, un accesso, un gesto fisico); non ci sono passi; la
  persona ha scritto durante il turno; il tool risponde "Rotazione spenta". Il fine leggero resta fatto:
  la chiusura alla persona è la raccolta dei risultati, cioè l'esito, una riga per materiale con la sua
  posizione e il prossimo passo con chi lo fa. Se il tool non c'è (mod spento),
  chiudi con "scrivi **/clear** e poi **/inizio <slug>**".

## FASE 1 · Inventario

Git, validate e commit girano nella cartella del progetto: la riga `cartella:` di `arturo contesto`, che
`/inizio` ha letto. Senza `/inizio`, lancia `python3 ~/.claude/bin/arturo contesto` e leggi la riga. Con
`cartella: nessuna` non c'è commit di progetto. Poi lancia `git status --short`, `TaskList` e l'inventario:

```bash
python3 ~/.claude/bin/inventario-sessione.py; echo "rc=$?"
```

Lo script legge la trascrizione (file scritti, uscite dei comandi, file nuovi in Download e Scrivania,
oggetti creati online), salta `~/.claude` e propone per ogni voce un `destino` col motivo. Con `rc=2`
(manca l'id o la trascrizione) o `rc=124` (oltre 120 secondi: non rilanciarlo) ricostruisci l'elenco dalla
conversazione e dillo nella riga tecnica. Aggiungi i file che lo script non ha visto e i punti pendenti.

**Uscita breve a sessione vuota.** Se valgono tutte e quattro le condizioni, salta le fasi 2-8 e 10:
- l'inventario non ha file né oggetti;
- `git status --short` del progetto è pulito;
- la sessione non ha todo nuovi né punti pendenti, e non ha aperto un lavoro che riprende nei giorni dopo;
- `arturo contesto` dice `cartella: nessuna`, o NON TROVATO.

Lancia solo la coda della FASE 9 (`python3 ~/.claude/bin/fine-coda.py`): senza handoff fa solo il sync
della config. Chiudi con una riga tecnica breve: "chiuso · sessione vuota · config: push riuscito".
Se una condizione manca, segui tutte le fasi.

## FASE 2 · Destino di ogni file

Il destino proposto è un punto di partenza, il giudizio è tuo. Ogni file finisce dove sopravvive a un riavvio:
- **repo**: codice, testi e note del progetto. Un file scritto fuori (scratchpad, Download) si copia dentro.
- **archivia**: un documento fuori da un repository. Chiedi alla persona dove lo tiene e spostalo lì dopo il sì.
- **resta**: un file pesante (video, immagini grandi) o creato online. L'handoff scrive dove sta.
- **scarto**: un file temporaneo. La chiusura lo nomina, non lo cancella.

Nessun handoff indica scratchpad o `/tmp` come posizione: si perdono al riavvio. Una bozza di email della
sessione riceve un esito nell'handoff (mandata, da mandare, scartata).

## FASE 3 · Completezza, validate, commit del progetto

- **Completezza.** Confronta l'obiettivo della sessione con i deliverable. Se la sessione ha toccato
  codice, lancia l'agente `structural-completeness-reviewer`. Ogni gap diventa un todo.
- **Validate.** Applica `~/.claude/shared/validation-gate.md` con **mode=quick** (tsc, test, console.log).
  Verde: commit. Rosso: il codice toccato resta fuori e l'errore esatto diventa un todo. **NON committare**
  il codice rosso e non correggerlo qui. Un esito inconclusivo non è verde.
- **Commit per pathspec.** Se il progetto non ha un git, crealo nella sua cartella, mai nella HOME
  (`git -C <cartella> init -b main`, un `CLAUDE.md` breve, un `.gitignore` per i binari). Staging file per
  file (`git add -- <file>`), mai `git add .` o `-A`; fuori restano `.env`, credenziali e file temporanei.
  **NON usare Co-Authored-By.**

```bash
git diff --cached | grep -qE '^\+(<<<<<<< |=======$|>>>>>>> )' && echo "MARCATORE DI CONFLITTO: fermati e risolvi prima del commit"
git diff --cached --stat
# Un progetto senza identità prende quella scelta da /setup: col plugin ~/.claude non è un repository.
bash ~/.claude/bin/identita-git.sh .
```

  Se lo script stampa `AVVISO`, il commit parte con l'identità automatica di Git: procedi e riporta la riga
  nella chiusura, con l'invito a sceglierne una con `/setup`. Solo `MANCA` ferma il commit.

  Controlla che l'elenco coincida con quello che volevi, poi `git commit -m "<messaggio>" -- <file-1> <file-2>`.
- **Sessione in un worktree** (aperto da `/inizio` perché un'altra sessione lavorava sullo stesso
  progetto): leggi `~/.claude/shared/fine-worktree.md` e seguilo prima dell'handoff. Riporta il lavoro
  nel tree principale senza perdere i file ignorati e controlla che il ramo sia arrivato.

## FASE 4 · Handoff e todo

L'handoff vive **solo** in `~/.claude/data/handoffs/<slug>/`, mai nel repository del progetto: in un
progetto pubblico decisioni e task entrerebbero nella storia Git. Prima chiediti cosa resta da fare (anche
detto di sfuggita), cosa è in sospeso o fallito, quali todo vecchi chiudere, quali bozze aspettano un
esito, cosa non ha funzionato. Poi leggi `~/.claude/shared/fine-handoff.md`: modello e regole della tabella.

**Todo.** Prima dell'handoff porta ogni item nell'archivio `~/.claude/data/todo/eventi.jsonl`, che
sopravvive alla sessione e che `/inizio` rilegge. `TaskList` vale solo per questa sessione.

```bash
# Il progetto lo calcola la CLI dalla cartella, come per "ricordami di…" ("generale" fuori da git). Comando intero
# su ogni riga, tilde fuori dalle virgolette: regge una HOME con spazi, e la guardia del worktree rifiuta "$HOME".
python3 ~/.claude/bin/arturo todo progetto
python3 ~/.claude/bin/arturo todo --progetto .     # cosa c'è già: non creare doppioni
```

Poi, per ogni item, una riga intera:

```bash
python3 ~/.claude/bin/arturo todo aggiungi "verbo e oggetto" --chi io --priorita media --note "cosa serve per riprendere"
python3 ~/.claude/bin/arturo todo fatto ID
python3 ~/.claude/bin/arturo todo ferma ID "motivo"
python3 ~/.claude/bin/arturo todo nota ID "testo"
python3 ~/.claude/bin/arturo todo modifica ID --chi tu
python3 ~/.claude/bin/arturo todo aggiungi "passo che viene dopo" --dopo ID   # la catena: aspetta il todo ID
python3 ~/.claude/bin/arturo todo stato "a che punto è il progetto, in una frase"
```

- **Il todo della sessione** (#4994). Se la sessione è partita da "Lavoraci" in Herdr (il compito di
  `/inizio` o il messaggio "Lavoriamo sul todo #ID"), quel todo è in corso e il pannello dice che Claude
  ci lavora. Lavoro finito: `fatto ID --titolo-atteso="titolo"`. Lavoro non finito: `riprendi ID
  --titolo-atteso="titolo"` più una `nota` col punto a cui è arrivato. Dopo `/fine` un todo non resta in
  corso, salvo con `--rotazione` quando il passo dopo continua lo stesso todo.
- Un item che può partire solo dopo un altro nasce legato con `--dopo ID`: `/inizio` e le viste lo
  saltano finché ID è aperto, e mettono avanti chi lo sblocca.
- La riga di stato si scrive a ogni `/fine`: una frase sul punto in cui è il progetto, letta da chi non c'era
  ("La bozza è finita, manca la rilettura del capitolo 3"). `/inizio` la mostra prima dei todo, la pagina
  web sotto il nome del progetto. Se la fonte dei task è esterna e risponde 2, salta la riga e prosegui.

- Nell'archivio Chi vale `tu`, `decidi` o `io`: `Claude` è `io`, `Decidi tu` è `decidi`, `Tu: …` è `tu`.
  Un todo bloccato va in FERMO con `ferma`, non con `--chi`. Mai da tu a io o decidi senza un sì.
- Le righe "Attenzione:" vanno alla persona: un todo può aver cambiato numero dopo un merge. Per un numero
  letto da un handoff aggiungi `--titolo-atteso="titolo"`: se il titolo non coincide, la CLI non scrive.
- Il titolo dice l'azione a una persona ("Mandare a Giulia la parola d'ordine"). Un todo chiesto nella
  sessione ("ricordami di…") c'è già: aggiornalo. Un todo `tu` porta un perché (`--perche`) solo se la
  persona lo ha detto con parole sue ("la firma la metto io"): un perché dedotto diventa un limite finto.

**Dove va l'handoff.** Lo slug è il nome della cartella del progetto in kebab-case, come in `/inizio`.
Se la shell torna alla cartella di partenza ("Shell cwd was reset"), apri il blocco con
`cd "<cartella del progetto>" &&`, altrimenti lo slug esce dalla cartella sbagliata:

```bash
PROGETTO=$(basename "$(git rev-parse --show-toplevel 2>/dev/null || pwd)")   # la cartella del progetto
SLUG=$(printf '%s' "$PROGETTO" | tr '[:upper:]' '[:lower:]' | sed -E 's/[^a-z0-9]+/-/g; s/^-+|-+$//g')
HDIR=~/.claude/data/handoffs/"$SLUG"
mkdir -p "$HDIR"
HANDOFF_FILE="$HDIR/HANDOFF_$(date +%Y-%m-%d_%H-%M).md"
if [ -n "${CLAUDE_CODE_SESSION_ID:-}" ]; then   # /fine rilanciato riscrive l'handoff della sessione
  GIA=$(grep -l -- "^- Sessione: $CLAUDE_CODE_SESSION_ID\$" "$HDIR"/HANDOFF_*.md 2>/dev/null | sort -r | head -1)
  [ -n "$GIA" ] && HANDOFF_FILE="$GIA"
fi
echo "Handoff: $HANDOFF_FILE"
```

**Sessione senza progetto** (`cartella: nessuna` o NON TROVATO; proposta n. 23, #4071). Se il lavoro
riprende nei giorni dopo, lascia un handoff breve: senza, la persona non ritrova più dove stava. Lo slug
viene dal lavoro, non dalla cartella corrente, che qui è la home o la cartella dei progetti. Scegli un
nome di due o tre parole che la persona riconosce ("preventivo-cucina"). Prima lancia
`python3 ~/.claude/bin/arturo contesto <nome>`: se trova un progetto che è lo stesso lavoro, usa quello,
altrimenti scegli un altro nome. Nel blocco sotto la prima riga diventa `PROGETTO="<nome>"`. L'handoff
breve ha `## Progetto` con `- Nome: <slug> / Cartella: nessuna`, `## Ripartenza`, `## File e materiali`
con la posizione di ogni file e documento, e `## Task Pendenti` coi todo creati con
`--progetto <slug>`. Le altre sezioni entrano solo se hanno qualcosa. La chiusura dice "riprendi:
/inizio <slug>" e offre in una riga la cartella di progetto: la crei solo dopo un sì.

Scrivi il modello nel file stampato dopo "Handoff:". Ogni blocco gira in una shell nuova: dopo, scrivi il
percorso intero. Una copia nel progetto solo su richiesta: mostra la visibilità del remote
(`gh repo view --json visibility`) e aspetta un sì esplicito.

## FASE 5 · Gate dell'handoff

Lancialo sul file appena scritto, al posto di `<handoff>`:

```bash
bash ~/.claude/bin/handoff-gate.sh "<handoff>"; echo "rc=$?"
```

Il gate è bloccante. Il rosso (`rc=1`) stampa una riga per difetto (tabella, ID, Chi, segnaposto mai
compilato). Correggi l'handoff (e l'archivio) e rilancia finché è verde.

## FASE 6 · Retention e indice

Lo store tiene gli ultimi 5 handoff per progetto o per filone. Prima guarda cosa uscirebbe, senza cancellare
(in una sessione senza progetto la prima riga diventa `SLUG="<slug della FASE 4>"`):

```bash
SLUG=$(basename "$(git rev-parse --show-toplevel 2>/dev/null || pwd)" | tr '[:upper:]' '[:lower:]' | sed -E 's/[^a-z0-9]+/-/g; s/^-+|-+$//g')
python3 ~/.claude/bin/handoff-retention.py "$SLUG"; echo "rc=$?"
```

Se stampa un blocco `=== IN USCITA`, leggi `~/.claude/shared/fine-retention.md` e scegli per ogni voce.
Cestino e indice li fa la coda della FASE 9, solo per ciò che questo dry-run ha mostrato.

## FASE 7 · CLAUDE.md del progetto

Il `CLAUDE.md` del progetto è la sua memoria durevole: cosa è, decisioni chiuse, trappole già viste ("NON
fare X: causa Y"), percorsi dei materiali fuori dal repo. Non è un diario: la riga che invecchia si
riscrive, e stato e prossimo passo stanno nei todo e nell'handoff. Le righe nuove entrano nel commit del
progetto. Senza `CLAUDE.md`, se il progetto ha sostanza, proponilo.

## FASE 8 · Memoria

La domanda: **cosa di questa sessione serve fra tre mesi?** Il test: **può ripresentarsi?**
- Vale per questo progetto: due righe nel `CLAUDE.md` del progetto (FASE 7).
- Vale per ogni progetto: una nota nella memoria di Claude Code. Prima cerca se esiste già
  (`python3 ~/.claude/bin/arturo memoria cerca "parole"`) e aggiorna quella. Un fatto, un file.
- Vale in ogni sessione: una regola nel `CLAUDE.md` personale (opzionale A). Altrimenti muore con l'handoff.
  Le correzioni della sessione (`arturo correzione elenco`) passano da questo test: finiscono con la sessione.

Mai in memoria: todo, uno stato che si legge dal vivo, una correzione una tantum, la copia di un documento
stabile, password e chiavi. Claude **applica** una riga nel `CLAUDE.md` del progetto e un fatto aggiornato
in una nota che esiste. **Chiede il sì** per una nota nuova, per dati su persone e per il `CLAUDE.md`
personale; con `/fine salva` il sì è già dato, tranne per il `CLAUDE.md` personale. Nel Modo rotazione
non si chiede: le note aspettano nella sezione `## Note in attesa del sì` dell'handoff. Un `/fine` scritto
dalla persona propone anche quelle ancora nella sezione degli handoff precedenti, di qualunque giorno, e al sì
le toglie dalla sezione.

## FASE 9 · Config Sync, in una chiamata

Dopo le fasi 4-8, o subito con l'uscita breve. Se `ListAgents` mostra un'altra sessione viva su questa
macchina, avvisala prima con `SendMessage`: il commit di sync prende anche i suoi file della config.

```bash
python3 ~/.claude/bin/fine-coda.py; echo "rc=$?"
```

La coda trova l'handoff dalla riga "- Sessione:" (un altro con `--handoff <percorso>`; attribuzione dei
commit con `--trailer "<riga>"`). Si ferma su un rebase a metà o una config rotta
(`hooks/controlla-config.py`), ripete il gate, applica la retention, committa (la memoria a parte) e
pusha; memoria, todo, `personale/` e `CLAUDE.md` solo verso un remote privato. Confronta lo stat di ogni commit
(`-- commit <hash> --`) e le righe rimaste fuori coi file della sessione. L'ultima riga (`coda: ...`) va
nella riga tecnica.
- **rc=1**: gate rosso, niente commit. **rc=4**: rebase a metà, config rotta, marcatori di conflitto o
  blocco delle tue aggiunte, niente commit. In entrambi i casi leggi la riga, sistema e rilancia.
- **rc=6**: `git add` o `git commit` falliti, la riga dice perché. **rc=3**: le tue aggiunte dicono che
  un servizio è giù, il resto è fatto.

La coda si può rilanciare senza danni, e un push fallito si ritenta. Se l'uscita non è chiara, se esce
`SKILL TUE NON SALVATE` o se esiste `~/.claude/personale/fine-coda.py`, leggi `~/.claude/shared/fine-coda-casi.md`.

## FASE 10 · Migliorare Arturo

Una sola proposta per sessione, mai un elenco.
- **Se Arturo o Claude Code si sono inceppati** (comando fallito, guardia su un lavoro legittimo,
  correzione della persona, cosa che Arturo non sa fare) e il fatto non è già partito in questa sessione,
  segnalalo senza chiedere: segui `/segnala` dal Passo 1, con `manda` e `--origine fine`. Poi dillo in una
  riga: "Ho segnalato a chi mantiene Arturo che X non ha funzionato: è la n. N. Se non la vuoi, dimmi
  ritirala." Se `manda` esce con 4, serve il sì: fai la domanda del Passo 5 di `/segnala`. Nel Modo
  rotazione, con un'uscita 4, non chiedere: scrivi il fatto nell'handoff, sotto "In sospeso".
- **Altrimenti** lancia `python3 ~/.claude/bin/arturo segnala chiedi`. Con exit 0 chiedi in una riga: "In
  questi giorni Arturo ti ha fatto perdere tempo, o c'è una cosa che vorresti facesse?" e, se la persona
  racconta qualcosa, segui `/segnala`. Con exit 3 taci. Se lei non vuole più queste domande, lancia
  `python3 ~/.claude/bin/arturo segnala basta`.

## Opzionali (`--full`, o quando la condizione è vera)

**A. CLAUDE.md personale**, se la sessione ha prodotto una regola che vale in ogni sessione. **B. Doc
staleness**, se la sessione ha toccato documenti `.md`. Per entrambi leggi `~/.claude/shared/fine-opzionali.md`.

## Chiusura

La chiusura non ristampa la ripartenza di `/inizio`. Il messaggio ha, in quest'ordine:
1. una riga per file o materiale della FASE 1 con la posizione finale, anche gli scarti;
2. la Ripartenza dell'handoff in tre righe, col prossimo passo;
3. la riga tecnica: "chiuso · commit a1b2c3d · handoff HANDOFF_2026-10-03_18-40.md · gate verde · validate
   ok · retention: 1 tolto · config: push riuscito · segnalazione: nessuna · riprendi: /inizio libro".
   Config: "push riuscito", "niente da pushare", "push non riuscito: N commit da ritentare" o "solo
   locale". Segnalazione: "inviata n. N", "in coda", "proposta, non inviata", "domanda fatta" o "nessuna". Un passo
   saltato o fallito lo dice al suo posto.

Se la FASE 8 ha scritto memoria, segue il blocco **Memoria applicata** (un percorso per riga e cosa è
cambiato). Nessun menu. Senza `salva`, elenca le note che aspettano il sì (percorso e perché) e chiudi con
"scrivimi **salva** per tutte, **togli N** per escluderne una". Al sì le scrivi e, se toccano
`~/.claude`, ripeti la FASE 9.
