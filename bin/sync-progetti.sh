#!/bin/bash
# /inizio --tutti: aggiorna con un pull ogni repository della cartella dei progetti.
# Per ogni repository: stash dei soli file tracciati, pull --rebase, stash pop.
# I file non tracciati non bloccano il rebase, quindi non si mettono da parte.
#
# Sta su disco e non dentro /inizio: un blocco bash lungo in un comando .md è fragile, e
# ogni blocco gira in una shell nuova. /inizio lo lancia con una riga sola.
#
# Esito: rc 0 se ogni repository è passato, rc 1 se anche uno solo ha un pull fallito,
# uno stash pop in conflitto o file in conflitto. Lo script non ripara niente da solo:
# riporta e passa al repository dopo.
#
# Uso: bash ~/.claude/bin/sync-progetti.sh [cartella]
#   Senza cartella usa PROJECTS_BASE (come /inizio), di default ~/Documents/ClaudeCode.
set -u

ROOT="${1:-${PROJECTS_BASE:-$HOME/Documents/ClaudeCode}}"
case "$ROOT" in "~"*) ROOT="$HOME${ROOT#\~}" ;; esac
# Un pull che chiede una password aspetterebbe per sempre: meglio un errore che si legge.
export GIT_TERMINAL_PROMPT=0
UPDATED=0
ERRORS=0

if [ ! -d "$ROOT" ]; then
  echo "Cartella dei progetti assente: $ROOT"
  exit 1
fi

echo "=== Progetti in $ROOT ==="

for dir in "$ROOT"/*/; do
  [ -d "$dir/.git" ] || continue
  name=$(basename "$dir")
  echo ""
  echo "--- $name --- ($(git -C "$dir" branch --show-current 2>/dev/null))"

  LOCAL=$(git -C "$dir" status --porcelain 2>/dev/null | head -5)
  TRACKED_DIRTY=$(git -C "$dir" diff --quiet 2>/dev/null; echo $?)
  STAGED_DIRTY=$(git -C "$dir" diff --cached --quiet 2>/dev/null; echo $?)
  STASHED=0
  if [ -n "$LOCAL" ]; then
    echo "  Modifiche locali:"
    echo "$LOCAL" | sed 's/^/    /'
  fi

  # Un repository senza remoto non è rotto: è solo locale. Si esce prima dello stash,
  # perché senza pull non c'è niente da proteggere. Un rosso per un motivo innocuo
  # insegnerebbe a non leggere i rossi.
  if [ -z "$(git -C "$dir" remote 2>/dev/null)" ]; then
    echo "  Locale: nessun remoto configurato, niente da sincronizzare"
    continue
  fi

  if [ "$TRACKED_DIRTY" = "1" ] || [ "$STAGED_DIRTY" = "1" ]; then
    if git -C "$dir" stash push -m "auto-stash-sync-$(date +%s)" >/dev/null 2>&1; then
      STASHED=1
      echo "  Auto-stash applicato"
    fi
  fi

  BEFORE=$(git -C "$dir" rev-parse HEAD 2>/dev/null)
  PULL_OUT=$(git -C "$dir" pull --rebase 2>&1)
  PULL_RC=$?
  echo "$PULL_OUT" | tail -3

  if [ "$PULL_RC" -ne 0 ]; then
    # La causa si legge nell'output, non si indovina: un pull senza credenziali non è un conflitto.
    case "$PULL_OUT" in
      *"could not read Username"*|*"Authentication failed"*|*"Permission denied (publickey)"*|*"terminal prompts disabled"*)
        echo "ERRORE: pull $name fallito - credenziali git assenti per il remote, lancia: gh auth setup-git" ;;
      *)
        echo "ERRORE: pull $name fallito - conflitto con modifiche locali, risolvi con /inizio $name" ;;
    esac
    git -C "$dir" rebase --abort 2>/dev/null
    [ "$STASHED" = "1" ] && git -C "$dir" stash pop 2>/dev/null
    ERRORS=$((ERRORS + 1))
    continue
  fi

  AFTER=$(git -C "$dir" rev-parse HEAD 2>/dev/null)

  if [ "$STASHED" = "1" ]; then
    if git -C "$dir" stash pop 2>&1 | grep -qE "CONFLITTO|conflict"; then
      echo "  ATTENZIONE: stash pop con conflitti - risolvi a mano"
      ERRORS=$((ERRORS + 1))
    else
      echo "  Stash ripristinato"
    fi
  fi

  if [ "$BEFORE" != "$AFTER" ]; then
    UPDATED=$((UPDATED + 1))
    echo "  Aggiornato: $(git -C "$dir" log --oneline "$BEFORE..$AFTER" | wc -l | tr -d ' ') commit"
  else
    echo "  Già aggiornato"
  fi

  CONFLICTS=$(git -C "$dir" diff --name-only --diff-filter=U 2>/dev/null)
  if [ -n "$CONFLICTS" ]; then
    echo "  CONFLITTI:"
    echo "$CONFLICTS" | sed 's/^/    /'
    ERRORS=$((ERRORS + 1))
  fi
done

echo ""
echo "=== Riepilogo === aggiornati: $UPDATED - errori: $ERRORS"

[ "$ERRORS" -eq 0 ] || exit 1
exit 0
