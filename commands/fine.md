---
description: Chiudi la sessione - inventario dei file e destino di ognuno, commit, handoff con i todo e chi agisce, gate dell'handoff, retention e indice, sync della config
argument-hint: "[--full] [note opzionali]"
---

# Fine Sessione

Chiudi la sessione in modo pulito. **Chiusura tipica leggera**; le fasi costose sono
opzionali (flag `--full`) o condizionali (si attivano solo se rilevanti).

**Argomenti / Note utente**: $ARGUMENTS

- `--full` → esegue anche: plugin claude-md, doc-staleness, retro.
- Senza flag → esegue solo il core + le fasi condizionali che risultano rilevanti.

Tre regole per tutte le fasi:
- **Dentro /fine non si sviluppa.** Un gap, un fix o un test rosso diventa un todo con un numero.
- **/fine si può rilanciare senza danni.** L'handoff di questa sessione si riscrive (non ne nasce
  un secondo), un todo che esiste non si ricrea, un commit vuoto non parte.
- **Un destino incerto non ferma la chiusura.** Il file resta dov'è e l'handoff dice dove sta.

---

## CORE (sempre)

### 1. Stato e inventario

```bash
git status --short
git branch --show-current 2>/dev/null
```

Poi l'inventario dei file che questa sessione ha scritto, anche fuori dal progetto:

```bash
python3 "$HOME/.claude/bin/inventario-sessione.py"; echo "rc=$?"
```

Lo script legge la trascrizione della sessione (file scritti, uscite dei comandi, file nuovi in
Download e Scrivania, oggetti creati online con i connettori), salta `~/.claude` e propone per
ogni voce un `destino` con il motivo. Con `rc=2` manca l'id della sessione o la trascrizione:
ricostruisci l'elenco dalla conversazione e dillo nella chiusura. Aggiungi i file che ricordi e
che lo script non ha visto (per esempio quelli scritti da un programma Python).

Il destino proposto è un punto di partenza, il giudizio è tuo. Ogni file finisce dove sopravvive
a un riavvio del computer:
- **repo**: codice, testi e note del progetto. Un file scritto fuori (scratchpad, Download) si
  copia nel progetto ed entra nel commit della fase 4.
- **archivia**: un documento fuori da un repository. Chiedi alla persona dove lo tiene (la cartella
  del progetto, i suoi Documenti) e spostalo lì solo dopo il suo sì.
- **resta**: un file pesante (video, immagini grandi) o creato online. L'handoff scrive dove sta.
- **scarto**: un file temporaneo. La chiusura lo nomina, non lo cancella.

Nessun handoff indica lo scratchpad o `/tmp` come posizione di un file: si perdono al riavvio.
Una bozza di email creata nella sessione riceve un esito nell'handoff (mandata, da mandare, scartata).

Raccogli anche i punti pendenti emersi nella sessione prima di scrivere l'handoff.

### 2. Completezza

Se la sessione modifica codice, lancia internamente `structural-completeness-reviewer`. Ricostruisci poi l'obiettivo e confrontalo con i deliverable. Se la sessione non modifica codice, salta il reviewer e registra l'esito.

Se emergono gap: elencali e chiedi se fixare ora o documentarli nell'handoff come task pendente.
Se tutto coperto: procedi in silenzio.

### 3. Validate

Applica `~/.claude/shared/validation-gate.md` con **mode=quick** (tsc + test + console.log).

- Passa → commit.
- Errori chiari e ripetibili → correggi e rilancia il validate dopo l'ultima modifica.
- Errori ambigui o persistenti → documentali nell'handoff come punti pendenti e **NON committare** il codice rosso.

### 4. Commit Progetto

Solo con un validate verde eseguito dopo l'ultima modifica, oppure se la sessione non ha toccato codice. Se ci sono modifiche non committate:
1. Staging **selettivo**, file per file (`git add -- <file>` — MAI `git add .` / `-A`)
2. Escludi file sensibili (.env, credentials, temporanei)
3. Controlla lo staging: niente marcatori di conflitto, e l'elenco coincide con quello che volevi
4. Commit con messaggio appropriato. **NON usare Co-Authored-By.**

```bash
git diff --cached | grep -qE '^\+(<<<<<<< |=======$|>>>>>>> )' && echo "MARCATORE DI CONFLITTO: fermati e risolvi prima del commit"
git diff --cached --stat
```

### 5. Handoff + Push

Nome file: `HANDOFF_$(date +%Y-%m-%d_%H-%M).md`, scritto **solo** nello store
`~/.claude/data/handoffs/<slug>/` (vedi sotto). Mai nel repository del progetto: in un
progetto pubblico decisioni, note e task entrerebbero nella storia Git.

**Prima di scrivere, rispondi internamente alle 6 domande:**
1. Cosa c'è da fare? (anche cose dette di sfuggita)
2. Cosa è rimasto in sospeso? (decisioni rimandate, dubbi)
3. Cosa si potrebbe fare che non è stato discusso? (migliorie, edge case, tech debt)
4. Ogni item emerso è un todo nell'archivio (`arturo todo`)? Se manca, crealo ora (vedi
   «Todo» sotto). `TaskList` vale solo per i passi di questa sessione: sparisce alla chiusura.
5. I todo da sessioni precedenti vanno aggiornati o chiusi?
6. Cosa hai provato che non ha funzionato, e perché? (finisce in «Vicoli ciechi»: la
   sessione dopo non deve rifare gli stessi tentativi)

Template:

```markdown
# Session Handoff - [YYYY-MM-DD] [HH:MM]

## Progetto
- Nome: [slug] / Branch: [branch] / Status: in progress|completato|bloccato
- Filone: [solo se il progetto ha più filoni di lavoro separati: un nome breve e sempre lo stesso]
- Sessione: [valore di $CLAUDE_CODE_SESSION_ID]
- Ultimo commit: [hash - messaggio]

## Ripartenza
[Per la persona fra una settimana, tre o quattro frasi senza gergo, hash e nomi di file: cosa
esiste adesso, cosa è cambiato per lei, dove vi siete fermati e perché.]
Prossimo passo: [una azione, con il gesto che serve: «mi dici quale account uso»]

## Decisioni prese
1. [Decisione e motivazione]

## Vicoli ciechi (tentativi falliti)
- NON [cosa] — [perché non funziona, con l'errore esatto se c'è]

## File e materiali
- [file o oggetto] → [posizione finale: percorso nel progetto, link, percorso dove resta, scarto]

## Task Pendenti
Da `arturo todo --progetto .`, tutti i todo aperti del progetto:

| ID | Progetto | Priorità | Task | Status | Descrizione | Chi |
|----|----------|----------|------|--------|-------------|-----|
| #4 | libro | alta | Rileggere il capitolo tre | da fare | Mancano le note dell'editor: senza, la revisione resta a metà | io |

## In sospeso (non ancora task)
- [Decisioni rimandate, dubbi]

## Idee emerse (non discusse)
- [idea] → #ID se è diventata un todo | → scartata: [motivo]

## Riferimenti / Note
- [Link a issue/PR/doc] · [Note utente]
```

Regole della tabella `## Task Pendenti` (le controlla il gate più sotto):
- La sezione c'è sempre, con questo titolo esatto. Senza task contiene la frase «Nessun task pendente».
- Ogni riga ha nella colonna ID il numero del todo nell'archivio (`#4`): prima crei il todo, poi
  scrivi la riga. Un todo chiuso non sta nella tabella.
- **Chi** è l'ultima colonna e vale `tu`, `decidi` o `io`, come nell'archivio dei todo.
- Status `da fare|in corso|fermo`, priorità `alta|media|bassa`.
- Task e Descrizione si leggono senza contesto: il verbo all'infinito e cosa serve per riprendere.
  Il gergo, i percorsi e gli hash vanno in Decisioni.
- Includi anche i todo delle sessioni precedenti se ancora validi. La tabella è la fotografia
  della sessione: la fonte di verità è l'archivio dei todo.
- Ogni idea ha un destino: un'idea già vista prima non resta idea una terza volta.

**Todo.** Prima di scrivere l'handoff porta nell'archivio ogni item della tabella. L'archivio è
il file `~/.claude/data/todo/eventi.jsonl`: sopravvive alla sessione e lo leggono `/inizio`,
la CLI e le altre viste. Chi agisce: `tu` se tocca alla persona (un invio, una password, un
gesto), `decidi` se serve una sua scelta prima che lavori tu, `io` se lo fai tu. Un todo
bloccato va in FERMO con `ferma`, non con `--chi`.

```bash
# Il progetto dei todo è quello della cartella, calcolato dalla CLI: lo stesso di «ricordami di…».
# Fuori da git e nella HOME è «generale». Ogni riga scrive il comando intero, tra virgolette:
# una HOME con uno spazio («Mario Rossi») resta un percorso solo, e nessuna variabile deve
# sopravvivere da una chiamata all'altra.
python3 "$HOME/.claude/bin/arturo" todo progetto
python3 "$HOME/.claude/bin/arturo" todo --progetto .     # cosa c'è già: non creare doppioni
```

Poi, per ogni item, una riga intera come queste. `arturo todo aggiungi` mette il todo nel
progetto della cartella, come «ricordami di…»:

```bash
python3 "$HOME/.claude/bin/arturo" todo aggiungi "verbo e oggetto" --chi io --priorita media --note "cosa serve per riprendere"
python3 "$HOME/.claude/bin/arturo" todo fatto ID
python3 "$HOME/.claude/bin/arturo" todo ferma ID "motivo"
python3 "$HOME/.claude/bin/arturo" todo nota ID "testo"
python3 "$HOME/.claude/bin/arturo" todo modifica ID --chi tu
```

Se la lettura stampa righe «Attenzione:», riportale alla persona: un todo può aver cambiato
numero dopo un merge. Per un numero letto da un handoff aggiungi `--titolo-atteso="titolo"`:
se il todo con quel numero ha un altro titolo, la CLI non scrive niente.

Il titolo dice l'azione a una persona («Mandare a Gigi la parola d'ordine»), non uno slug.
Se la persona ha chiesto un todo durante la sessione («ricordami di…»), c'è già: aggiornalo.
Un todo `tu` porta un perché solo se la persona lo ha detto con parole sue nella sessione
(«la firma la metto io»). Non dedurlo tu dalla frase: il percorso conta il perché come un limite
che la persona ha dichiarato. Se lei non l'ha detto, lascialo vuoto: glielo chiede il percorso,
una domanda per volta, quando scrive `/percorso`. Non spostare mai un todo da tu a io
o decidi senza un sì.

**Una proposta, al massimo.** Se nella sessione la persona ha fatto a mano un passo che Claude
può fare, chiedi al percorso se puoi proporlo:

```bash
python3 "$HOME/.claude/bin/arturo" percorso suggerisci
```

Con exit 0 proponi una sola delega, in una riga, e di' cosa resta suo: «La prossima volta il
riassunto lo preparo io. Resta tuo: la scelta di cosa mandare.» Con exit 3 taci: la persona ha
detto no da poco, oppure ha chiesto basta. Se la persona dice no, lancia
`python3 "$HOME/.claude/bin/arturo" percorso no` e non insistere. Il numero di cose delegate non
conta: non proporre una delega su un todo che ha un perché.

Se nella sessione la persona ha fatto un esercizio del percorso (un todo del progetto
`_percorso`), chiedi «cosa hai tenuto per te?» prima di chiuderlo. Scrivi la risposta con
`python3 "$HOME/.claude/bin/arturo" todo nota ID "Tenuto: …"`, poi
`python3 "$HOME/.claude/bin/arturo" todo fatto ID`.

**Dove va l'handoff.** Scrivilo nello store `~/.claude/data/handoffs/<slug>/`. Slug = nome
progetto in kebab-case (lo stesso usato con `/inizio`). Non creare l'handoff nel repository
del progetto e non committarlo lì. Se l'utente chiede una copia nel progetto, prima mostragli
la visibilità del remote (`gh repo view --json visibility`) e aspetta una conferma esplicita.

```bash
# Slug: nome del progetto in minuscolo, spazi e simboli diventano trattini.
# /inizio calcola lo stesso slug, cosi' «Il mio libro» ritrova il suo handoff.
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

Scrivi il contenuto del template nel file stampato dopo «Handoff:». La variabile non arriva
ai blocchi dopo: ognuno gira in una shell nuova, quindi lì scrivi il percorso per intero.

**Gate dell'handoff.** Lancialo sul file appena scritto, al posto di `<handoff>`:

```bash
bash "$HOME/.claude/bin/handoff-gate.sh" "<handoff>"; echo "rc=$?"
```

Il gate è bloccante. Il rosso (`rc=1`) stampa una riga per difetto: la sezione `## Task Pendenti`
assente o vuota senza «Nessun task pendente», un ID che non è un todo aperto dell'archivio, un Chi
fuori da `tu|decidi|io` o non in ultima colonna, un segnaposto del modello mai compilato.
Correggi l'handoff (e l'archivio, se manca un todo) e rilancia finché è verde.

**Retention e indice.** Lo store tiene gli ultimi 5 handoff per progetto, o per filone se
l'handoff ha la riga «- Filone:». Prima guarda cosa uscirebbe, senza cancellare niente:

```bash
SLUG=$(basename "$(git rev-parse --show-toplevel 2>/dev/null || pwd)" | tr '[:upper:]' '[:lower:]' | sed -E 's/[^a-z0-9]+/-/g; s/^-+|-+$//g')
python3 "$HOME/.claude/bin/handoff-retention.py" "$SLUG"; echo "rc=$?"
```

Per ogni handoff in uscita lo script stampa i Vicoli ciechi e le righe dei task senza ID.
Nessun handoff esce senza essere letto. Per ogni voce scegli: un vicolo cieco che può tornare
entra nel `CLAUDE.md` del progetto in due righe («NON fare X: causa Y»), un task ancora valido
diventa un todo adesso, il resto muore e lo dici. Poi cancella i vecchi e rigenera l'indice:

```bash
SLUG=$(basename "$(git rev-parse --show-toplevel 2>/dev/null || pwd)" | tr '[:upper:]' '[:lower:]' | sed -E 's/[^a-z0-9]+/-/g; s/^-+|-+$//g')
python3 "$HOME/.claude/bin/handoff-retention.py" "$SLUG" --applica; echo "rc=$?"
python3 "$HOME/.claude/bin/index-rigenera.py" --scrivi; echo "rc=$?"
```

`rc=3` della retention: una cancellazione non è riuscita, il file resta e la chiusura lo dice.
L'indice `~/.claude/data/handoffs/INDEX.md` nasce dagli handoff e non si corregge a mano: una
riga per progetto o filone, con stato e prossimo passo (dalla riga «Prossimo passo:» della
Ripartenza). Con `rc=1` l'indice non è stato scritto: la riga stampata dice perché.

La copia degli handoff sulle altre macchine è facoltativa: avviene nel Config Sync della
FASE 6, e solo verso un remote privato.

### 6. Config Sync (condizionale)

**Si attiva se `~/.claude` ha modifiche non committate o commit non ancora pushati.** Un push fallito la volta prima si ritenta qui.

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
  # Senza -f: git add salta i file ignorati, come il venv di scrape (tools/scrapling/.venv/).
  for p in settings.json .gitattributes .gitignore bin commands agents hooks skills shared docs templates tools tests output-styles NOVITA.md README.md package.json; do
    [ -e "$p" ] || continue
    git add -- "$p" || echo "git add fallito su $p: resta fuori dal commit"
  done
  # CLAUDE.md personale, aggiunte ai comandi (personale/), handoff e todo viaggiano solo verso un remote privato verificato.
  VIS=$(gh repo view "$(git remote get-url origin 2>/dev/null)" --json visibility -q .visibility 2>/dev/null)
  if [ "$VIS" = "PRIVATE" ]; then
    # -f scavalca .gitignore: l'esclusione tiene fuori il lucchetto (*.lock) di arturo todo.
    for p in CLAUDE.md data/handoffs data/todo personale; do
      [ -e "$p" ] || continue
      git add -f -- "$p" ':(exclude,glob)**/*.lock' || echo "git add fallito su $p: resta fuori dal commit"
    done
  else
    echo "CLAUDE.md, personale/, handoff e todo non sincronizzati: il remote della config non risulta privato (visibilità: ${VIS:-sconosciuta}). Restano su questa macchina."
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

### 7. Migliorare Arturo

Arturo migliora con quello che le persone gli dicono: questo passo glielo chiede ogni volta
che ha senso. Una sola proposta per sessione, mai un elenco.

- **Se nella sessione Arturo o Claude Code si sono inceppati** (un comando fallito, una guardia
  che ha fermato un lavoro legittimo, la persona che ti ha corretto, una cosa chiesta che Arturo
  non sa fare), proponi la segnalazione con il fatto già scritto: «Ho visto che X non ha
  funzionato. Lo segnalo a chi mantiene Arturo? Il testo lo preparo io.» Con un sì segui
  `/segnala` dal Passo 1, con la bozza già pronta: il Passo 1 tiene fuori
  dalla issue pubblica un segreto esposto o una guardia aggirabile. Se l'hai già proposta durante la sessione,
  non riproporla.
- **Altrimenti** chiedi allo script se è il momento della domanda della settimana:

  ```bash
  python3 "$HOME/.claude/bin/arturo" segnala chiedi
  ```

  Con exit 0 fai una domanda, una riga: «In questi giorni Arturo ti ha fatto perdere tempo, o
  c'è una cosa che vorresti facesse?» Se la persona racconta qualcosa, segui `/segnala`. Con
  exit 3 taci.
- Se la persona dice di non volere più queste domande, lancia
  `python3 "$HOME/.claude/bin/arturo" segnala basta` e non insistere. `/segnala` resta lì.

### 8. Conferma

Prima della tabella, una riga per file o materiale della fase 1 con la sua posizione finale
(anche gli scarti), poi la Ripartenza dell'handoff in tre righe con il prossimo passo.

```
+====================================================================+
|                      SESSIONE CHIUSA                                |
+--------------------------------------------------------------------+
| Commit progetto | [hash o "nessuno"]                               |
| Materiali       | [N file: repo / archivia / resta / scarto]       |
| Handoff         | [HANDOFF_*.md]                                   |
| Gate handoff    | [verde / rosso: motivo]                          |
| Task pendenti   | [N] (nell'handoff)                               |
| Retention       | [N handoff vecchi tolti / niente da togliere]    |
| Validate        | [passed / N errori documentati]                  |
| Config sync     | [push riuscito / niente da pushare / push non riuscito: N commit da ritentare]                     |
| Segnalazione    | [inviata / proposta, non inviata / domanda fatta / nessuna]       |
| Extra (--full)  | [claude-md/doc o "skip"]                        |
+--------------------------------------------------------------------+
| Riprendi: /inizio [progetto]  ·  sessione esatta: claude -r        |
+====================================================================+
```

---

## OPZIONALI (`--full` o se rilevante)

Esegui queste fasi **solo** se è passato `--full`, oppure quando la condizione indicata è vera.

### A. CLAUDE.md — `--full`, o se la sessione ha prodotto una regola che vale in ogni sessione
Plugin `claude-md-management:revise-claude-md` (fallback: leggi, identifica pattern
ripetuti, proponi update). Sale nel `CLAUDE.md` solo ciò che deve valere in OGNI sessione:
una preferenza della persona, un freno prima di un'azione con effetti, o una correzione che si
è ripetuta. Una riga per regola. Le modifiche al `CLAUDE.md` personale le scrivi dopo il sì
della persona, ed entrano nel commit config della FASE 6.

### B. Doc staleness — `--full`, o se la sessione ha toccato doc/.md
Cross-reference le modifiche con i `.md` del repo. Se un doc descrive codice modificato ma non
aggiornato: diventa un todo e una riga della tabella dell'handoff.

### C. Riepilogo — `--full`, o se la sessione ha lavoro significativo

Registra nell'handoff i punti emersi e i prossimi passi.

---

## Avvia

Esegui il CORE. Attiva le fasi OPZIONALI solo con `--full` o quando la loro condizione è vera.
