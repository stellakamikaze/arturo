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
ricostruisci l'elenco dalla conversazione e dillo nella riga tecnica. Aggiungi i file che ricordi e
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
- <idea> → #ID | → memoria | → scartata: <motivo>
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
- **Ogni idea ha un destino**: un'idea già vista prima non resta idea una terza volta.

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

Poi sposta i vecchi nel cestino dello store (`~/.claude/data/handoffs/.cestino/`, dove restano 30
giorni e si recuperano) e rigenera l'indice:

```bash
SLUG=$(basename "$(git rev-parse --show-toplevel 2>/dev/null || pwd)" | tr '[:upper:]' '[:lower:]' | sed -E 's/[^a-z0-9]+/-/g; s/^-+|-+$//g')
python3 ~/.claude/bin/handoff-retention.py "$SLUG" --applica; echo "rc=$?"
python3 ~/.claude/bin/index-rigenera.py --scrivi; echo "rc=$?"
```

`rc=3` della retention: uno spostamento non è riuscito, il file resta e la riga tecnica lo dice.
L'indice `~/.claude/data/handoffs/INDEX.md` nasce dagli handoff e non si corregge a mano: una
riga per progetto o filone, con stato e prossimo passo (dalla riga "Prossimo passo:" della
Ripartenza). Con `rc=1` l'indice non è stato scritto: la riga stampata dice perché.

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

## FASE 9 · Config Sync

**Si attiva se `~/.claude` ha modifiche non committate o commit non ancora pushati.** Un push fallito
la volta prima si ritenta qui. Se `ListAgents` mostra un'altra sessione viva su questa macchina,
avvisala con `SendMessage` prima del commit: il commit di sync prende anche i suoi file della config.

```bash
PREV_DIR="$PWD" && cd ~/.claude
# Una config rotta (JSON non valido, conflitto, rebase a meta') non si committa: il commit
# la porterebbe su tutte le macchine dell'utente.
CONFIG_INTEGRA=1
python3 hooks/controlla-config.py --quiet || CONFIG_INTEGRA=0
[ "$CONFIG_INTEGRA" = 1 ] || echo "Config sync saltato: la config non è integra (vedi sopra). Sistemala prima con /aggiorna o con il comando indicato."
ORIGIN_URL=$(git remote get-url origin 2>/dev/null || echo "")
case "$ORIGIN_URL" in
  *github.com[:/]stellakamikaze/arturo|*github.com[:/]stellakamikaze/arturo.git) ORIGIN_ARTURO=1 ;;
  *) ORIGIN_ARTURO=0 ;;
esac
if [ "$CONFIG_INTEGRA" = 1 ] && [ -n "$(git status --porcelain 2>/dev/null)" ]; then
  VIS=$(gh repo view "$ORIGIN_URL" --json visibility -q .visibility 2>/dev/null)
  # Senza -f: git add salta i file ignorati, come il venv di scrape (tools/scrapling/.venv/).
  for p in settings.json .gitattributes .gitignore bin commands agents hooks shared docs tools tests output-styles NOVITA.md README.md package.json; do
    [ -e "$p" ] || continue
    git add -- "$p" || echo "git add fallito su $p: resta fuori dal commit"
  done
  # Le skill già nel repository (quelle di Arturo, le tue già salvate) seguono le modifiche. Una skill
  # nuova della persona (/creaskill) può avere dati suoi: verso un remote che non risulta privato
  # resta fuori, e Claude chiede.
  [ -d skills ] && git add -u -- skills
  SKILL_NUOVE=$(git ls-files --others --exclude-standard --directory -- skills 2>/dev/null | tr '\n' ' ')
  if [ -n "$SKILL_NUOVE" ]; then
    if [ "$VIS" = "PRIVATE" ] || [ "$ORIGIN_ARTURO" = 1 ] || [ -z "$ORIGIN_URL" ]; then
      git add -- skills || echo "git add fallito su skills: resta fuori dal commit"
    else
      echo "SKILL TUE NON SALVATE: ${SKILL_NUOVE}- il remote della config non risulta privato (visibilità: ${VIS:-sconosciuta}). Restano su questa macchina."
    fi
  fi
  # CLAUDE.md personale, aggiunte ai comandi (personale/), handoff e todo viaggiano solo verso un remote privato verificato.
  if [ "$VIS" = "PRIVATE" ]; then
    # -f scavalca .gitignore: l'esclusione tiene fuori il lucchetto (*.lock) di arturo todo.
    for p in CLAUDE.md data/todo personale data/memory; do
      [ -e "$p" ] || continue
      git add -f -- "$p" ':(exclude,glob)**/*.lock' || echo "git add fallito su $p: resta fuori dal commit"
    done
    # Gli handoff senza -f: Arturo non li esclude, e una riga della persona nel .gitignore (un progetto
    # riservato) va rispettata (segnalazione n. 12, 23/10/2026).
    [ -e data/handoffs ] && { git add -- data/handoffs || echo "git add fallito su data/handoffs: resta fuori dal commit"; }
  else
    echo "CLAUDE.md, personale/, handoff e todo non sincronizzati: il remote della config non risulta privato (visibilità: ${VIS:-sconosciuta}). Restano su questa macchina."
    # Senza un remote dove pushare, un archivio già tracciato esce dal tracciamento e resta su disco
    # (segnalazione n. 14, 26/10/2026): altrimenti la retention lascia per sempre file cancellati e non
    # salvati. Con un remote suo non si tocca: un'altra macchina, al pull, li cancellerebbe dal disco.
    if [ "$ORIGIN_ARTURO" = 1 ] || [ -z "$ORIGIN_URL" ]; then
      for p in data/handoffs data/todo data/memory; do
        [ -n "$(git ls-files -- "$p")" ] || continue
        git rm -r -q --cached -- "$p" && echo "$p: tolto dal tracciamento di git, i file restano su questa macchina"
      done
    fi
  fi
  git diff --cached --quiet || git commit -m "chore: session sync $(date +%Y-%m-%d)" || echo "Commit di sync non riuscito: vedi errore sopra"
fi
if [ "$ORIGIN_ARTURO" = 1 ]; then
  echo "Config: commit salvati su questa macchina. origin è il repository pubblico di Arturo, dove non puoi pushare: per sincronizzare tra più computer vedi /setup FASE 7."
elif [ "$CONFIG_INTEGRA" = 1 ] && git remote get-url origin >/dev/null 2>&1; then
  GIT_TERMINAL_PROMPT=0 git fetch --quiet origin main 2>/dev/null
  AHEAD=$(git rev-list --count origin/main..HEAD 2>/dev/null || echo "?")
  if [ "$AHEAD" = "0" ]; then
    echo "Config: niente da pushare"
  elif git push origin main 2>&1; then
    echo "Config: push riuscito"
  else
    echo "Config push non riuscito: $AHEAD commit restano locali e il prossimo /fine li ritenta (serve un remote tuo con accesso in scrittura)"
  fi
elif [ "$CONFIG_INTEGRA" = 1 ]; then
  echo "Config senza remote 'origin': i commit restano locali (ok). Per sincronizzare tra le tue macchine, configura un tuo repo privato come origin."
fi
cd "$PREV_DIR"
```

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
