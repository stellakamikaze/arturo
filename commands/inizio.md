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

```bash
git -C ~/.claude pull origin main --rebase 2>/dev/null || echo "Config sync: nessun update"
```

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

Due fonti, si usa la **più recente**: la copia locale nel progetto e il mirror
cross-machine in `~/.claude/data/handoffs/` (scritto da `/fine` su qualsiasi macchina,
arrivato qui col sync di FASE 0).

```bash
HANDOFF_LOCAL=$(ls -t HANDOFF_*.md 2>/dev/null | head -1)
HANDOFF_SYNC=$(ls -t ~/.claude/data/handoffs/"$ARGUMENTS"/HANDOFF_*.md 2>/dev/null | head -1)
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

## FASE 4: Carica Task con Cross-Reference

Se l'handoff contiene "## Task Pendenti":

1. Esegui `git log --oneline -20` per vedere i commit recenti
2. Per ogni task nell'handoff, verifica se un commit recente lo ha già completato
3. Crea con `TaskCreate` solo i task NON ancora completati
4. Segnala all'utente eventuali task skippati perché già completati

```bash
# Commit recenti per cross-reference
git log --oneline -20 2>/dev/null
```

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

## Task Pendenti
[lista da TaskList — indica quali nuovi e quali ripresi da handoff]

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
- `TaskCreate` — Per task pendenti da handoff (solo quelli non completati)

**L'utente chiama solo /inizio, il resto è automatico.**

---

## Avvia

Esegui FASE 0: sync config, poi FASE 1: localizza progetto $ARGUMENTS.
