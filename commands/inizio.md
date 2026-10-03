---
description: Avvia sessione lavoro su progetto
argument-hint: <nome-progetto>
---

# Inizio Sessione

Avvia sessione di lavoro su **$ARGUMENTS**.

---

## FASE -1: Onboarding speciali

Se `$ARGUMENTS` è `gws`: NON è un progetto. Leggi `~/.claude/docs/onboarding/gws.md`
e guida l'utente passo-passo nel setup multi-account della Google Workspace CLI
(installazione → progetti GCP → config dir → login → alias → verifica). Esegui i
comandi verificabili, chiedi all'utente quelli interattivi (login browser). Alla
fine esegui la checklist del documento. Poi FERMATI: le fasi sotto non si applicano.

---

## FASE 0: Sync Config

`/inizio` non applica mai gli aggiornamenti di Arturo: li controlla e li segnala. Li applica
solo `/aggiorna`, dopo il sì dell'utente (Impegno 2 del README). Se `origin` è un repository
suo (vedi `/setup` FASE 7), `/inizio` sincronizza quello: sono le sue macchine, non codice di
altri.

```bash
ORIGIN_URL=$(git -C ~/.claude remote get-url origin 2>/dev/null || echo "")
case "$ORIGIN_URL" in
  *github.com[:/]stellakamikaze/arturo|*github.com[:/]stellakamikaze/arturo.git) ORIGIN_ARTURO=1 ;;
  *) ORIGIN_ARTURO=0 ;;
esac
export GIT_TERMINAL_PROMPT=0 GIT_SSH_COMMAND="ssh -o BatchMode=yes"
if [ "$ORIGIN_ARTURO" = 1 ] || [ -z "$ORIGIN_URL" ]; then
  git -C ~/.claude fetch --quiet origin main 2>&1 || echo "Config sync: controllo aggiornamenti non riuscito (rete?)"
else
  PRIMA=$(git -C ~/.claude rev-parse HEAD)
  if ! SYNC_OUTPUT=$(git -C ~/.claude pull --rebase --autostash origin main 2>&1); then
    printf '%s\n' "$SYNC_OUTPUT"
    git -C ~/.claude rebase --abort 2>/dev/null
    echo "Config sync: il pull dal tuo repository non è riuscito. Ho annullato il tentativo: la config è com'era prima."
  fi
  if ! python3 ~/.claude/hooks/controlla-config.py --quiet; then
    git -C ~/.claude rebase --abort 2>/dev/null || git -C ~/.claude reset --keep "$PRIMA"
    echo "Config sync: dopo il pull la config non era integra. Ho riportato la copia a prima del pull."
  fi
fi
git -C ~/.claude remote get-url upstream >/dev/null 2>&1 && git -C ~/.claude fetch --quiet upstream main 2>&1
SRC=$(git -C ~/.claude remote get-url upstream >/dev/null 2>&1 && echo upstream || echo origin)
BEHIND=$(git -C ~/.claude rev-list --count "HEAD..$SRC/main" 2>/dev/null || echo 0)
[ "${BEHIND:-0}" -gt 0 ] && echo "ARTURO: $BEHIND aggiornamenti disponibili — li applica /aggiorna, dopo il tuo sì"
python3 ~/.claude/hooks/controlla-config.py --quiet || exit 1
```

Se l'ultima riga stampa `CONFIG ROTTA`, fermati: spiega all'utente il problema in parole
semplici e proponi il comando che la riga suggerisce. Non lavorare su una config rotta: le
guardie potrebbero essere spente.

---

## FASE 1: Localizza Progetto

```bash
# PB = PROJECTS_BASE espansa (la tilde da settings.json non si espande da sola),
# cercata per prima cosi' /inizio trova i progetti creati da /progetto.
PB="${PROJECTS_BASE:-$HOME/Documents/ClaudeCode}"; PB="${PB/#\~/$HOME}"
PROJECT_PATH=""
for dir in "./$ARGUMENTS" "$PB/$ARGUMENTS" "$HOME/Documents/ClaudeCode/$ARGUMENTS" "$HOME/Documents/$ARGUMENTS" "$HOME/Projects/$ARGUMENTS" "$HOME/$ARGUMENTS"; do
  [ -d "$dir" ] && PROJECT_PATH="$dir" && break
done

if [ -z "$PROJECT_PATH" ]; then
  echo "Progetto non trovato: $ARGUMENTS"
  echo "Cercato in: ./  $PB/  ~/Documents/  ~/Projects/  ~/"
else
  echo "Progetto: $PROJECT_PATH"
  cd "$PROJECT_PATH"
  git status --short 2>/dev/null
  git branch --show-current 2>/dev/null

  # Check merge conflicts
  CONFLICTS=$(git diff --name-only --diff-filter=U 2>/dev/null)
  if [ -n "$CONFLICTS" ]; then
    echo "MERGE CONFLICTS:"
    echo "$CONFLICTS"
  fi
fi
```

Se ci sono merge conflict, risolvili PRIMA di procedere.

---

## FASE 2: Localizza Handoff

Due fonti, si usa la **più recente**: lo store in `~/.claude/data/handoffs/` (scritto da
`/fine`, arrivato qui col sync di FASE 0 se il remote della config è privato) e un'eventuale
copia locale nel progetto lasciata da versioni precedenti di `/fine`.

```bash
SLUG=$(printf '%s' "$ARGUMENTS" | tr '[:upper:]' '[:lower:]' | sed -E 's/[^a-z0-9]+/-/g; s/^-+|-+$//g')   # stesso slug di /fine
HANDOFF_LOCAL=$(find . -maxdepth 1 -name "HANDOFF_*.md" 2>/dev/null | sort -r | head -1)
HANDOFF_SYNC=$(find ~/.claude/data/handoffs/"$SLUG" -maxdepth 1 -name "HANDOFF_*.md" 2>/dev/null | sort -r | head -1)
# Confronta i timestamp nel nome file (YYYY-MM-DD_HH-MM): vince il più recente
echo "Handoff locale: ${HANDOFF_LOCAL:-nessuno}"
echo "Handoff sync:   ${HANDOFF_SYNC:-nessuno}"
```

Se il progetto non viene trovato in FASE 1, o per una vista cross-progetto di cosa
c'è da fare ovunque, leggi `~/.claude/data/handoffs/INDEX.md` (una riga per progetto
con stato e prossimo passo) e proponi da lì.

---

## FASE 3: Carica Contesto

Leggi in ordine (se esistono):
1. `CLAUDE.md` — Istruzioni progetto
2. `HANDOFF_*.md` — Il più recente (per timestamp nel nome file)

---

## FASE 4: Carica i Todo con Cross-Reference

I todo stanno nell'archivio `~/.claude/data/todo/eventi.jsonl`, scritto da `/fine` e dalle
richieste della persona («ricordami di…»). È la fonte di verità: la tabella `## Task Pendenti`
dell'handoff è solo la fotografia dell'ultima sessione.

```bash
# Todo aperti del progetto, divisi per chi agisce, e commit recenti per il cross-reference
python3 "$HOME/.claude/bin/arturo" todo --progetto "$SLUG" 2>/dev/null
git log --oneline -20 2>/dev/null
# Il pannello /dafare c'è? I comandi di un mod non compaiono fra quelli che vedi.
claude plugin list --json 2>/dev/null | python3 -c 'import json,sys; v=[p for p in json.load(sys.stdin) if p.get("id") == "dafare@skills-dir"]; print("mod caricato" if v and v[0].get("enabled") else "mod assente")' 2>/dev/null || echo "mod assente"
```

1. Per ogni todo aperto, verifica se un commit recente lo ha già completato. Se sì, chiudilo
   con `python3 ~/.claude/bin/arturo todo fatto ID` e dillo alla persona.
2. Un item della tabella `## Task Pendenti` senza ID e senza todo (handoff di una versione
   precedente) diventa un todo con `arturo todo aggiungi`. Un todo già chiuso non si ricrea.
3. Non creare task di sessione (`TaskCreate`) all'apertura: si crea solo quello che la persona
   sceglie di riprendere.

---

## FASE 5: Presenta Dashboard

```
----------------------------------------------------
 SESSIONE: $ARGUMENTS
----------------------------------------------------

## Contesto
- Branch: [nome]
- Ultimo stato: [HANDOFF / nessuno]
- Config sync: [ok / failed]
- Merge conflicts: [nessuno / LISTA]

## Todo
[i gruppi di `arturo todo`: TOCCA A TE, DECIDI TU POI FACCIO IO, FACCIO IO, FERMO.
 Ogni todo con l'ID a destra e una riga su a cosa serve. Le scadenze passate in cima.]
[solo se il controllo del pannello della FASE 4 stampa «mod caricato»:]
Per chiuderli o spostarli con un tasto: /dafare

## Skill Progetto
[suggerisci le poche skill davvero utili a QUESTO progetto ora, in base a stack,
 stato dell'handoff e task pendenti — non una lista meccanica. Ometti la sezione
 se non c'è nulla di rilevante da proporre.]

----------------------------------------------------
```

Per farti un'idea dello stack (segnale per il tuo giudizio, non una regola):
```bash
[ -f "package.json" ] && echo "HAS_PKG=true"
[ -f "prisma/schema.prisma" ] && echo "HAS_PRISMA=true"
[ -d "docs" ] && echo "HAS_DOCS=true"
ls next.config.* 2>/dev/null && echo "HAS_NEXT=true"
```

---

## FASE 6: Selezione Lavoro

Usa AskUserQuestion:

**Header**: "Cosa vuoi fare?"

**Opzioni**:
1. **Continua task** — "Riprendi [primo task pending]"
2. **Nuovo task** — "Inizia nuovo lavoro"
3. **Review** — "Analizza stato codebase"
4. **Debug** — "C'è un bug da fixare"

---

## Orchestrazione

Questo workflow chiama automaticamente:
- Sync GitHub config (`git -C`)
- Check merge conflicts
- Cross-reference task vs `git log` (skip task già completati)
- `arturo todo` — I todo aperti del progetto (chiude quelli già fatti da un commit)

**L'utente chiama solo /inizio, il resto è automatico.**

---

## Avvia

Esegui FASE 0: sync config, poi FASE 1: localizza progetto $ARGUMENTS.
