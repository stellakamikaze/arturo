---
description: >-
  Chiude la sessione in dieci fasi: inventario dei file della sessione e destino di ognuno (repo,
  archivia, resta, scarto), validate e commit per pathspec, handoff con i todo e chi agisce, gate
  dell'handoff, retention e indice, CLAUDE.md del progetto, memoria, sync della config, una domanda per
  migliorare Arturo. Si invoca con /fine [--full] [salva] [note] e si può rilanciare senza danni. Non
  apre sessioni (/inizio).
argument-hint: "[--full] [salva] [note opzionali]"
---

# Fine sessione

Argomenti e note della persona: **$ARGUMENTS**. Con `--full`, o quando la loro condizione è vera,
applica anche gli opzionali in fondo: CLAUDE.md personale e doc staleness. `salva` dà in anticipo il sì
alle note di memoria della FASE 8, tranne il `CLAUDE.md` personale.

Tre regole per tutte le fasi:
- **Dentro /fine non si sviluppa.** Un gap, un fix o un test rosso diventa un todo con un numero.
- **/fine si può rilanciare senza danni.** L'handoff di questa sessione si riscrive (FASE 4), un todo
  che esiste non si ricrea, un commit vuoto non parte.
- **Un destino incerto non ferma la chiusura.** Il file resta dov'è e l'handoff dice dove sta.

## FASE 1 · Inventario

Git, validate e commit girano nella cartella del progetto: quella della riga `cartella:` che `/inizio`
ha letto da `arturo contesto`. Se la sessione è partita senza `/inizio`, lancia
`python3 ~/.claude/bin/arturo contesto` e leggi la riga. Con `cartella: nessuna` non c'è commit
di progetto, e lo dice la riga tecnica. Poi lancia `git status --short`, `TaskList` e l'inventario:

```bash
python3 ~/.claude/bin/inventario-sessione.py; echo "rc=$?"
```

Lo script legge la trascrizione della sessione (file scritti, uscite dei comandi, file nuovi in
Download e Scrivania, oggetti creati online con i connettori), salta `~/.claude` e propone per
ogni voce un `destino` con il motivo. Con `rc=2` manca l'id della sessione o la trascrizione:
ricostruisci l'elenco dalla conversazione e dillo nella riga tecnica. Con `rc=124` lo script ha
superato il suo tetto di 120 secondi: ricostruisci allo stesso modo, segnala il guasto e non rilanciarlo.
Aggiungi i file che ricordi e
che lo script non ha visto (per esempio quelli scritti da un programma Python). Raccogli anche i punti
pendenti emersi nella sessione: servono alla FASE 4.

## FASE 2 · Destino di ogni file

Il destino proposto è un punto di partenza, il giudizio è tuo. Ogni file finisce dove sopravvive
a un riavvio del computer:
- **repo**: codice, testi e note del progetto. Un file scritto fuori (scratchpad, Download) si
  copia nel progetto ed entra nel commit della FASE 3.
- **archivia**: un documento fuori da un repository. Chiedi alla persona dove lo tiene (la cartella
  del progetto, i suoi Documenti) e spostalo lì solo dopo il suo sì.
- **resta**: un file pesante (video, immagini grandi) o creato online. L'handoff scrive dove sta.
- **scarto**: un file temporaneo. La chiusura lo nomina, non lo cancella.

Nessun handoff indica lo scratchpad o `/tmp` come posizione di un file: si perdono al riavvio.
Una bozza di email creata nella sessione riceve un esito nell'handoff (mandata, da mandare, scartata).

## FASE 3 · Completezza, validate, commit del progetto

- **Completezza.** Confronta l'obiettivo della sessione con i deliverable. Se la sessione ha toccato
  codice, lancia l'agente `structural-completeness-reviewer`. Ogni gap diventa un todo.
- **Validate.** Applica `~/.claude/shared/validation-gate.md` con **mode=quick** (tsc, test, console.log).
  Verde: commit. Rosso: il codice toccato resta fuori dal commit e l'errore esatto diventa un todo.
  **NON committare** il codice rosso e non correggerlo qui. Un esito inconclusivo non è verde.
- **Commit per pathspec.** Ogni progetto ha un git. Se manca, crealo nella cartella del progetto
  (`git -C <cartella> init -b main`, un `CLAUDE.md` breve, un `.gitignore` per i binari), mai nella HOME.
  Staging file per file (`git add -- <file>`), mai `git add .` o `-A`. Fuori dal commit restano `.env`,
  credenziali e file temporanei. **NON usare Co-Authored-By.**

```bash
git diff --cached | grep -qE '^\+(<<<<<<< |=======$|>>>>>>> )' && echo "MARCATORE DI CONFLITTO: fermati e risolvi prima del commit"
git diff --cached --stat
```

  Controlla che l'elenco coincida con quello che volevi, poi `git commit -m "<messaggio>" -- <file-1> <file-2>`.
- **Sessione in un worktree** (aperto da `/inizio` perché un'altra sessione lavorava sullo stesso
  progetto). Il commit va sul branch del worktree. Prima di uscire guarda i file ignorati con
  `git status --short --ignored` (righe `!!`): i file di lavoro fuori da git, come una cartella
  `lavoro/`, esistono solo lì. Poi esci con `ExitWorktree` e `keep`: dentro il worktree la guardia di
  Claude Code vieta git sul tree principale. Fuori, riporta il lavoro con
  `git -C <tree principale> merge --ff-only <branch>`. Riuscito: copia nel tree principale, allo stesso
  percorso, i file ignorati che sono lavoro della sessione. Cache, dipendenze e build si rigenerano
  (`node_modules`, `__pycache__`, `.venv`, `dist`): restano fuori. Un file che esiste già nel tree
  principale non si sovrascrive: il worktree resta e l'handoff lo dice. Solo dopo la copia,
  `git -C <tree principale> worktree remove <percorso del worktree>` e `git -C <tree principale> branch
  -d <branch>`: `worktree remove` cancella anche i file ignorati, senza avviso (segnalazione n. 13,
  26/10/2026). Se il fast-forward non riesce perché l'altra sessione ha committato nel frattempo, e il
  tree principale non ha modifiche, prova `git -C <tree principale> merge --no-edit <branch>`; al primo
  conflitto `git -C <tree principale> merge --abort`. Rebase e merge con conflitti non si fanno a fine
  sessione. Il resto di /fine gira dal tree principale (segnalazione n. 11, 22/10/2026).
- **Il ramo è riportato? Controllalo prima dell'handoff.** `git -C <tree principale> cherry HEAD
  <branch>` non deve stampare righe con `+`: ognuna è un commit del ramo che la cartella principale
  non ha. Una riga con `-` è un commit già arrivato in altra forma (cherry-pick, rebase) e non conta.
  `branch --no-merged` qui non basta: guarda solo la storia, e segnerebbe bloccato un ramo già
  riportato. È lo stesso controllo di `arturo contesto`, così `/inizio` e `/fine` dicono la stessa
  cosa. Con almeno una riga `+` il lavoro non è nella
  cartella principale: il worktree resta, l'handoff ha Status `bloccato`, la Ripartenza comincia con
  "N commit restano sul ramo <branch>, non nella cartella principale", e riportarli diventa un todo.
  Lo dici alla persona nella chiusura, non solo nell'handoff (segnalazione n. 20, 27/10/2026: venti
  commit fermi sul ramo e nessuno lo sapeva).

## FASE 4 · Handoff e todo

L'handoff vive **solo** nello store `~/.claude/data/handoffs/<slug>/`, mai nel repository del progetto:
in un progetto pubblico decisioni, note e task entrerebbero nella storia Git. Prima chiediti cosa resta
da fare (anche detto di sfuggita), cosa è in sospeso o fallito, quali todo vecchi chiudere, quali bozze
aspettano un esito, cosa hai provato che non ha funzionato.

```markdown
# Session Handoff - AAAA-MM-GG HH:MM
## Progetto
- Nome: <slug> / Branch: <branch> / Status: in progress|completato|bloccato
- Filone: <solo se il progetto ha più filoni di lavoro: un nome breve, sempre lo stesso>
- Sessione: <valore di $CLAUDE_CODE_SESSION_ID>
- Ultimo commit: <hash - messaggio>
## Ripartenza
<Per la persona fra una settimana, tre o quattro frasi senza gergo, hash e nomi di file: cosa esiste
adesso, cosa è cambiato per lei, dove vi siete fermati e perché.>
Prossimo passo: <una azione col gesto che serve: «mi dici quale account uso»>
## Decisioni
1. <decisione e motivo>
## Vicoli ciechi
- NON fare X: causa Y, con l'errore esatto se c'è
## File e materiali
- <file o oggetto> → <posizione finale: percorso nel progetto, link, percorso dove resta, scarto>
## Task Pendenti
Da `arturo todo --progetto .`: tutti i todo aperti del progetto.

| ID | Progetto | Priorità | Task | Status | Descrizione | Chi |
|----|----------|----------|------|--------|-------------|-----|
| #4 | libro | alta | Rileggere il capitolo tre | da fare | Mancano le note dell'editor: senza, la revisione resta a metà | Claude |
| #5 | libro | media | Mandare la bozza all'editor | da fare | La bozza è pronta nella cartella del progetto | Tu: invio a terzi |

## In sospeso
- <decisione rimandata o dubbio>
## Idee
- <idea> → #ID | → memoria [[nome-della-nota]] | → scartata: <motivo>
```

Regole della tabella `## Task Pendenti` (le controlla il gate della FASE 5):
- **La sezione c'è sempre**, con questo titolo esatto. Senza task contiene la frase "Nessun task pendente".
- **Ogni riga ha nella colonna ID il numero del todo** nell'archivio (`#4`): prima crei il todo, poi
  scrivi la riga. Un todo chiuso non sta nella tabella. Entrano anche i todo aperti delle sessioni
  prima: la tabella è la fotografia, la fonte di verità è l'archivio.
- **Chi** è l'ultima colonna. Vale `Claude` per ogni passo che Claude esegue da solo, `Decidi tu` se
  serve una scelta della persona prima che Claude lavori, `Tu: <cosa serve>` se il gesto è della
  persona (`Tu: invio a terzi`, `Tu: password`, `Tu: pagamento`, `Tu: gesto fisico`). Nell'archivio
  Chi vale `tu`, `decidi` o `io`: `Claude` è `io`, `Decidi tu` è `decidi`, `Tu: …` è `tu`.
- Status `da fare|in corso|fermo`, priorità `alta|media|bassa`, come in `arturo todo`.
- **Task e Descrizione si leggono senza contesto**: il verbo all'infinito e cosa serve per riprendere.
  Gergo, percorsi e hash vanno in Decisioni.
- **Ogni idea ha un destino**: un'idea già vista prima non resta idea una terza volta. "→ memoria" nomina con `[[nome]]` la nota dove l'idea è finita: il controllo dell'handoff cerca quella nota nella memoria o in `_in-attesa.md`, e senza nota esce rosso.

**Todo.** Prima di scrivere l'handoff porta nell'archivio ogni item della tabella. L'archivio è
il file `~/.claude/data/todo/eventi.jsonl`: sopravvive alla sessione e lo leggono `/inizio`,
la CLI e le altre viste. `TaskList` vale solo per i passi di questa sessione: sparisce alla chiusura.
Un todo bloccato va in FERMO con `ferma`, non con `--chi`.

```bash
# Il progetto dei todo è quello della cartella, calcolato dalla CLI: lo stesso di "ricordami di…".
# Fuori da git e nella HOME è "generale". Ogni riga scrive il comando intero, con la tilde fuori
# dalle virgolette: una HOME con uno spazio ("Mario Rossi") resta un percorso solo, e in un worktree
# la guardia di Claude Code accetta la tilde ma rifiuta "$HOME" e $(...). Nessuna variabile deve
# sopravvivere da una chiamata all'altra.
python3 ~/.claude/bin/arturo todo progetto
python3 ~/.claude/bin/arturo todo --progetto .     # cosa c'è già: non creare doppioni
```

Poi, per ogni item, una riga intera come queste. `arturo todo aggiungi` mette il todo nel
progetto della cartella, come "ricordami di…":

```bash
python3 ~/.claude/bin/arturo todo aggiungi "verbo e oggetto" --chi io --priorita media --note "cosa serve per riprendere"
python3 ~/.claude/bin/arturo todo fatto ID
python3 ~/.claude/bin/arturo todo ferma ID "motivo"
python3 ~/.claude/bin/arturo todo nota ID "testo"
python3 ~/.claude/bin/arturo todo modifica ID --chi tu
```

Se la lettura stampa righe "Attenzione:", riportale alla persona: un todo può aver cambiato
numero dopo un merge. Per un numero letto da un handoff aggiungi `--titolo-atteso="titolo"`:
se il todo con quel numero ha un altro titolo, la CLI non scrive niente.

Il titolo dice l'azione a una persona ("Mandare a Gigi la parola d'ordine"), non uno slug.
Se la persona ha chiesto un todo durante la sessione ("ricordami di…"), c'è già: aggiornalo.
Un todo `tu` porta un perché (`--perche`) solo se la persona lo ha detto con parole sue nella
sessione ("la firma la metto io"). Non dedurlo tu dalla frase: un perché inventato diventa un limite
che la persona non ha mai messo. Se lei non l'ha detto, lascialo vuoto. Il `Tu: <cosa serve>` della
tabella nomina il gesto del passo (un invio, una password), non un perché. Non spostare mai un todo
da tu a io o decidi senza un sì.

**Dove va l'handoff.** Lo slug è il nome della cartella del progetto in kebab-case, lo stesso di `/inizio`:

```bash
# Slug: nome del progetto in minuscolo, spazi e simboli diventano trattini.
# /inizio calcola lo stesso slug, cosi' "Il mio libro" ritrova il suo handoff.
PROGETTO=$(basename "$(git rev-parse --show-toplevel 2>/dev/null || pwd)")   # la cartella del progetto
SLUG=$(printf '%s' "$PROGETTO" | tr '[:upper:]' '[:lower:]' | sed -E 's/[^a-z0-9]+/-/g; s/^-+|-+$//g')
HDIR=~/.claude/data/handoffs/"$SLUG"
mkdir -p "$HDIR"
HANDOFF_FILE="$HDIR/HANDOFF_$(date +%Y-%m-%d_%H-%M).md"
# /fine rilanciato nella stessa sessione riscrive il suo handoff invece di crearne un secondo.
if [ -n "${CLAUDE_CODE_SESSION_ID:-}" ]; then
  GIA=$(grep -l -- "^- Sessione: $CLAUDE_CODE_SESSION_ID\$" "$HDIR"/HANDOFF_*.md 2>/dev/null | sort -r | head -1)
  [ -n "$GIA" ] && HANDOFF_FILE="$GIA"
fi
echo "Handoff: $HANDOFF_FILE"
```

Scrivi il contenuto del modello nel file stampato dopo "Handoff:". La variabile non arriva
ai blocchi dopo: ognuno gira in una shell nuova, quindi lì scrivi il percorso per intero.
Se la persona chiede una copia dell'handoff nel progetto, prima mostrale la visibilità del remote
(`gh repo view --json visibility`) e aspetta una conferma esplicita.

## FASE 5 · Gate dell'handoff

Lancialo sul file appena scritto, al posto di `<handoff>`:

```bash
bash ~/.claude/bin/handoff-gate.sh "<handoff>"; echo "rc=$?"
```

Il gate è bloccante. Il rosso (`rc=1`) stampa una riga per difetto: la sezione `## Task Pendenti`
assente o vuota senza "Nessun task pendente", un ID che non è un todo aperto dell'archivio, un Chi
fuori lista o non in ultima colonna, un segnaposto del modello mai compilato. Correggi l'handoff (e
l'archivio, se manca un todo) e rilancia finché è verde.

## FASE 6 · Retention e indice

Lo store tiene gli ultimi 5 handoff per progetto, o per filone se l'handoff ha la riga "- Filone:".
Prima guarda cosa uscirebbe, senza cancellare niente:

```bash
SLUG=$(basename "$(git rev-parse --show-toplevel 2>/dev/null || pwd)" | tr '[:upper:]' '[:lower:]' | sed -E 's/[^a-z0-9]+/-/g; s/^-+|-+$//g')
python3 ~/.claude/bin/handoff-retention.py "$SLUG"; echo "rc=$?"
```

Per ogni handoff in uscita lo script stampa i Vicoli ciechi e le righe dei task senza ID: nessun
handoff esce senza essere letto. Per ogni voce scegli:
- **Promuovi.** Il vicolo cieco che può tornare va in due righe nel `CLAUDE.md` del progetto ("NON
  fare X: causa Y"). Un task ancora valido diventa un todo adesso.
- **Già coperto.** Dici dove, dopo una ricerca vera (`grep` sul `CLAUDE.md` del progetto, `arturo todo`,
  `arturo memoria cerca "parole"`).
- **Muore.** Era una tantum o è superato, e lo dici.

Lo spostamento nel cestino dello store (`~/.claude/data/handoffs/.cestino/`, dove i file restano 30
giorni e si recuperano) e l'indice li fa la coda della FASE 9. La coda dice quanti file sono andati nel
cestino e lo svuota oltre i 30 giorni per ogni progetto. Per riportare un handoff, sposta il file da
`.cestino/<slug>/` alla cartella `<slug>/`. Esce solo ciò che questo dry-run ha
mostrato: un handoff scritto nel frattempo da un'altra sessione resta. Senza dry-run non esce niente, e
la riga della coda dice "retention NON applicata". L'indice `~/.claude/data/handoffs/INDEX.md` nasce
dagli handoff e non si corregge a mano.

## FASE 7 · CLAUDE.md del progetto

Il `CLAUDE.md` del progetto è la sua memoria durevole: cosa è, decisioni chiuse, trappole già viste
(«NON fare X: causa Y»), percorsi dei materiali fuori dal repo. Non è un diario: la riga che invecchia
si riscrive, e stato e prossimo passo restano nei todo e nell'handoff. Le righe nuove di questa
sessione le scrivi tu ed entrano nel commit del progetto (FASE 3, o un commit a parte ora). Se il
progetto non ha un `CLAUDE.md` e ha sostanza, proponilo con due righe su cosa è.

## FASE 8 · Memoria

La domanda: **cosa di questa sessione serve fra tre mesi?** Il test: **può ripresentarsi?**
- Vale per questo progetto: due righe nel `CLAUDE.md` del progetto (FASE 7).
- Vale per ogni progetto: una nota nella memoria di Claude Code. Prima cerca se esiste già
  (`python3 ~/.claude/bin/arturo memoria cerca "parole"`): se c'è, aggiorna quella. Un fatto, un file.
- Una regola che deve valere in ogni sessione va nel `CLAUDE.md` personale (opzionale A).
- No: muore con l'handoff.

Mai in memoria: todo, uno stato che si legge dal vivo, una correzione una tantum, la copia di un
documento stabile, password e chiavi.

Chi decide: Claude **applica** una riga nel `CLAUDE.md` del progetto e un fatto aggiornato in una nota
che esiste. **Chiede il sì** per una nota nuova, per dati su persone e per il `CLAUDE.md` personale.
Con `/fine salva` il sì è già dato, tranne per il `CLAUDE.md` personale.

## FASE 9 · Config Sync, in una chiamata

Solo dopo le fasi 4-8. Se `ListAgents` mostra un'altra sessione viva su questa macchina, avvisala con
`SendMessage` prima: il commit di sync prende anche i suoi file della config.

```bash
python3 ~/.claude/bin/fine-coda.py; echo "rc=$?"
```

La coda trova da sola l'handoff di questa sessione, dalla riga "- Sessione:" della FASE 4, e lo slug
dalla sua cartella. Per un altro handoff aggiungi `--handoff <percorso>`, per la riga di attribuzione dei
commit `--trailer "<riga>"`. Senza handoff della sessione fa solo il sync della config. In ordine:
- si ferma se `~/.claude` è a metà di un rebase o se `hooks/controlla-config.py` la trova rotta: una
  config rotta committata arriverebbe su tutte le macchine;
- ripete il gate della FASE 5;
- sposta nel cestino i file del dry-run della FASE 6 e rigenera l'indice;
- aggiunge al commit i file di Arturo e gli handoff. CLAUDE.md, `personale/`, todo e memoria entrano
  solo se il remote della config risulta privato a `gh`, e mai lucchetti, log delle letture della memoria, copie
  `.bak-*` e indice della memoria;
- ferma il commit se un file in stage ha i marcatori di conflitto;
- fa due commit: la memoria a parte ("memoria: applicata da /fine"), così si annulla da sola, poi il
  sync;
- fa il push. Se il push è rifiutato, fa un pull `--rebase --autostash` e riprova una volta. Non
  pusha se origin è il repository pubblico di Arturo.

Per ogni commit stampa lo stat (`-- commit <hash> --`), poi le righe di `git status` rimaste fuori.
Confronta lo stat con i file della sessione. L'ultima riga (`coda: ...`) va nella riga tecnica della
chiusura.

- **rc=1**: gate rosso, niente commit. Correggi l'handoff (FASE 5) e rilancia.
- **rc=4**: rebase a metà, config rotta, marcatori di conflitto o blocco delle tue aggiunte. Niente
  commit. Leggi la riga, sistema e rilancia.
- **rc=6**: `git add` o `git commit` falliti, la riga dice perché.
- **rc=3**: le tue aggiunte dicono che un servizio è giù. Il resto è fatto.

La coda si può rilanciare: il gate si ripete, la retention non trova più niente, un commit vuoto non
parte, e un push fallito la volta prima si ritenta.

**Le tue aggiunte.** Se esiste `~/.claude/personale/fine-coda.py`, la coda lo lancia dopo l'indice
(`"fase": "dopo-index"`) e prima del commit (`"fase": "prima-commit"`). Riceve su stdin un JSON con
fase, handoff, slug, radice, i file in stage e gli argomenti scritti dopo `--` nel comando della coda.
Risponde con una riga JSON `{"esiti": [...], "path": [...], "blocca": null}`: gli esiti finiscono nella
riga `coda:`, i path entrano nel commit di sync (solo verso un remote privato). Exit 0 fatto, 3 servizio
giù, 4 blocca. Gli aggiornamenti di Arturo non lo toccano.

Se esce `SKILL TUE NON SALVATE`, dillo alla persona con i nomi delle skill: il repository della
sua config non risulta privato, e pubblicarle lì le rende visibili a tutti. Chiedi se vuole
pubblicarle. Col suo sì, per ognuna: `git -C ~/.claude add -- skills/<nome>`, poi
`git -C ~/.claude commit -m "skill <nome>"` e `git -C ~/.claude push origin main`. Senza sì
restano su questa macchina, e il prossimo `/fine` lo ricorda.

## FASE 10 · Migliorare Arturo

Una sola proposta per sessione, mai un elenco.
- **Se nella sessione Arturo o Claude Code si sono inceppati** (un comando fallito, una guardia che
  ha fermato un lavoro legittimo, una correzione della persona, una cosa che Arturo non sa fare),
  proponi la segnalazione col fatto già scritto: «Ho visto che X non ha funzionato. Lo segnalo a chi
  mantiene Arturo? Il testo lo preparo io.» Col sì segui `/segnala` dal Passo 1, che tiene fuori dalla
  issue pubblica un segreto esposto o una guardia aggirabile. Se l'hai già proposta, non riproporla.
- **Altrimenti** lancia `python3 ~/.claude/bin/arturo segnala chiedi`. Con exit 0 fai una
  domanda in una riga: «In questi giorni Arturo ti ha fatto perdere tempo, o c'è una cosa che vorresti
  facesse?» Se la persona racconta qualcosa, segui `/segnala`. Con exit 3 taci.
- Se la persona non vuole più queste domande, lancia `python3 ~/.claude/bin/arturo segnala basta`.

## Opzionali (`--full`, o quando la condizione è vera)

**A. CLAUDE.md personale**: con `--full`, o se la sessione ha prodotto una regola che vale in ogni
sessione. Sale in `~/.claude/CLAUDE.md` solo una preferenza della persona, un freno prima di un'azione
con effetti, o una correzione che si è ripetuta. Una riga per regola. La scrivi dopo il sì della
persona, ed entra nel commit della FASE 9.

**B. Doc staleness**: con `--full`, o se la sessione ha toccato documenti `.md`. Confronta le modifiche
con i `.md` del repo. Un documento che descrive codice cambiato e non aggiornato diventa un todo e una
riga della tabella dell'handoff.

## Chiusura

La chiusura non ristampa la ripartenza di `/inizio`. Il messaggio ha, in quest'ordine:
1. una riga per file o materiale della FASE 1 con la posizione finale, anche gli scarti;
2. la Ripartenza dell'handoff in tre righe, col prossimo passo;
3. la riga tecnica: «chiuso · commit a1b2c3d · handoff HANDOFF_2026-10-03_18-40.md · gate verde ·
   validate ok · retention: 1 tolto · config: push riuscito · segnalazione: nessuna · riprendi:
   /inizio libro». Per la config vale uno fra «push riuscito», «niente da pushare»,
   «push non riuscito: N commit da ritentare», «solo locale». Per la segnalazione uno fra «inviata»,
   «proposta, non inviata», «domanda fatta», «nessuna». Un passo saltato o fallito lo dice al suo posto.

Se la FASE 8 ha scritto memoria, segue il blocco **Memoria applicata**: un percorso per riga e cosa è
cambiato.

Nessun menu. Senza `salva`, elenca le note che aspettano il sì, una per riga (percorso e perché), e
chiudi con «scrivimi **salva** per tutte, **togli N** per escluderne una». Al sì le scrivi e, se
toccano `~/.claude`, ripeti la FASE 9.
