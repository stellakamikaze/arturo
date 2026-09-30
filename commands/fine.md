---
description: Chiudi sessione lavoro correttamente
argument-hint: "[--full] [note opzionali]"
---

# Fine Sessione

Chiudi la sessione in modo pulito. **Chiusura tipica leggera**; le fasi costose sono
opzionali (flag `--full`) o condizionali (si attivano solo se rilevanti).

**Argomenti / Note utente**: $ARGUMENTS

- `--full` → esegue anche: plugin claude-md, doc-staleness, retro.
- Senza flag → esegue solo il core + le fasi condizionali che risultano rilevanti.

---

## CORE (sempre)

### 1. Stato

```bash
git status --short
git branch --show-current 2>/dev/null
```

Raccogli i punti pendenti emersi nella sessione prima di scrivere l'handoff.

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
1. `git diff --stat` per review
2. Staging **selettivo** (`git add` dei file pertinenti — MAI `git add .` / `-A`)
3. Escludi file sensibili (.env, credentials, temporanei)
4. Commit con messaggio appropriato. **NON usare Co-Authored-By.**

### 5. Handoff + Push

Nome file: `HANDOFF_$(date +%Y-%m-%d_%H-%M).md`, scritto **solo** nello store
`~/.claude/data/handoffs/<slug>/` (vedi sotto). Mai nel repository del progetto: in un
progetto pubblico decisioni, note e task entrerebbero nella storia Git.

**Prima di scrivere, rispondi internamente alle 5 domande:**
1. Cosa c'è da fare? (anche cose dette di sfuggita)
2. Cosa è rimasto in sospeso? (decisioni rimandate, dubbi)
3. Cosa si potrebbe fare che non è stato discusso? (migliorie, edge case, tech debt)
4. Ogni item emerso è in `TaskList`? Se manca, crealo con `TaskCreate` ora.
5. I task da sessioni precedenti vanno aggiornati/chiusi?
6. Cosa hai provato che non ha funzionato, e perché? (finisce in «Vicoli ciechi»: la
   sessione dopo non deve rifare gli stessi tentativi)

Template:

```markdown
# Session Handoff - [YYYY-MM-DD] [HH:MM]

## Progetto
- Nome / Branch / Status [in progress|completato|bloccato] / Ultimo commit [hash - msg]

## Cosa stavamo facendo
[Task/feature principale, conciso]

## Decisioni prese
1. [Decisione e motivazione]

## Vicoli ciechi (tentativi falliti)
- NON [cosa] — [perché non funziona, con l'errore esatto se c'è]

## File modificati
[git diff --stat o lista]

## Task Pendenti
Da `TaskList`, tutti i task con status != completed:

| # | Progetto | Priorità | Task | Status | Descrizione |
|---|----------|----------|------|--------|-------------|
| 1 | [nome] | alta | nome-task | in_progress | cosa resta |

Regole: ogni task DEVE avere il Progetto; status `pending|in_progress|blocked`;
priorità `alta|media|bassa`; Descrizione con contesto sufficiente a riprendere senza
rileggere il codice; includi anche task da sessioni precedenti se ancora validi.

## In sospeso (non ancora task)
- [Decisioni rimandate, dubbi]

## Idee emerse (non discusse)
- [Migliorie, edge case, tech debt]

## Prossimi passi
1. [ ] [Azione immediata più importante]

## Riferimenti / Note
- [Link a issue/PR/doc] · [Note utente]
```

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
# scrivi in "$HANDOFF_FILE" il contenuto del template
# retention: ultimi 5, per nome (la data sta nel nome). Dopo un pull o un ripristino
# le date dei file sono tutte fresche: ordinare per data cancellerebbe quello sbagliato.
find "$HDIR" -maxdepth 1 -name "HANDOFF_*.md" | sort -r | tail -n +6 | while IFS= read -r vecchio; do rm -f -- "$vecchio"; done
```

Poi aggiorna la riga del progetto in `~/.claude/data/handoffs/INDEX.md`
(colonne: Progetto | Ultimo handoff | Data | Stato | Prossimo passo — il "Prossimo passo"
deve essere leggibile senza aprire l'handoff). La copia sulle altre macchine avviene nel
Config Sync della FASE 6, e solo verso un remote privato.

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
  for p in settings.json commands agents hooks skills shared docs NOVITA.md README.md package.json; do
    [ -e "$p" ] || continue
    git add -- "$p" || echo "git add fallito su $p: resta fuori dal commit"
  done
  # CLAUDE.md personale e handoff viaggiano solo verso un remote privato verificato.
  VIS=$(gh repo view "$(git remote get-url origin 2>/dev/null)" --json visibility -q .visibility 2>/dev/null)
  if [ "$VIS" = "PRIVATE" ]; then
    for p in CLAUDE.md data/handoffs; do
      [ -e "$p" ] || continue
      git add -f -- "$p" || echo "git add fallito su $p: resta fuori dal commit"
    done
  else
    echo "CLAUDE.md e handoff non sincronizzati: il remote della config non risulta privato (visibilità: ${VIS:-sconosciuta}). Restano su questa macchina."
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

### 7. Conferma

```
+====================================================================+
|                      SESSIONE CHIUSA                                |
+--------------------------------------------------------------------+
| Commit progetto | [hash o "nessuno"]                               |
| Handoff         | [HANDOFF_*.md]                                   |
| Task pendenti   | [N] (nell'handoff)                               |
| Validate        | [passed / N errori documentati]                  |
| Config sync     | [push riuscito / niente da pushare / push non riuscito: N commit da ritentare]                     |
| Extra (--full)  | [claude-md/doc o "skip"]                        |
+--------------------------------------------------------------------+
| Riprendi: /inizio [progetto]  ·  sessione esatta: claude -r        |
+====================================================================+
```

---

## OPZIONALI (`--full` o se rilevante)

Esegui queste fasi **solo** se è passato `--full`, oppure quando la condizione indicata è vera.

### A. CLAUDE.md — `--full`, o se la sessione ha prodotto insight duraturi
Plugin `claude-md-management:revise-claude-md` (fallback: leggi, identifica pattern
ripetuti, proponi update). Le modifiche entrano nel commit config della FASE 6.

### B. Doc staleness — `--full`, o se la sessione ha toccato doc/.md
Cross-reference le modifiche con i `.md` del repo. Se un doc descrive codice modificato ma non
aggiornato: segnalalo nell'handoff.

### C. Riepilogo — `--full`, o se la sessione ha lavoro significativo

Registra nell'handoff i punti emersi e i prossimi passi.

---

## Avvia

Esegui il CORE. Attiva le fasi OPZIONALI solo con `--full` o quando la loro condizione è vera.
