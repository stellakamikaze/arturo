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

# Rimette lo stash del repository $1 con la sua selezione in stage (--index). Fino al 22/11/2026 il pop era
# senza --index: i file preparati per un commit parziale tornavano tutti fuori dallo stage (revisione del
# 20/11, bug 11). Se lo stage non si può rimettere ("Conflicts in index"), git non tocca niente e lo stash
# resta: allora il pop semplice rimette almeno le modifiche. Stampa l'output di git, esce come il pop.
rimetti_stash() {
  local out
  out=$(LC_ALL=C git -C "$1" stash pop --index 2>&1) && { printf '%s\n' "$out"; return 0; }
  case "$out" in
    *"without --index"*|*"Conflicts in index"*) LC_ALL=C git -C "$1" stash pop 2>&1 ;;
    *) printf '%s\n' "$out"; return 1 ;;
  esac
}

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

  # Un rebase, un merge o un cherry-pick già a metà è lavoro di qualcuno (un'altra sessione, la
  # persona): lo script non lo tocca. Prima lanciava pull, credeva il rebase suo e lo annullava,
  # e lo stash pop rimetteva nel file i marcatori sopra la risoluzione (review del 7/11, finding 24).
  IN_CORSO=""
  for voce in rebase-merge rebase-apply MERGE_HEAD CHERRY_PICK_HEAD REVERT_HEAD; do
    gp=$(git -C "$dir" rev-parse --git-path "$voce" 2>/dev/null) || continue
    case "$gp" in /*|[A-Za-z]:*) ;; *) gp="$dir/$gp" ;; esac
    [ -e "$gp" ] && { IN_CORSO="$voce"; break; }
  done
  if [ -n "$IN_CORSO" ]; then
    echo "ERRORE: $name ha un'operazione git a metà ($IN_CORSO): non lo tocco, finiscila con /inizio $name"
    ERRORS=$((ERRORS + 1))
    continue
  fi
  # Un HEAD staccato (un bisect, una prova su un commit) è lavoro in corso anche lui: niente stash né pull.
  # Correzione portata dalla copia di Federico (30/10/2026), revisione del 22/11, passo 2.
  if ! git -C "$dir" symbolic-ref -q HEAD >/dev/null 2>&1; then
    echo "ERRORE: $name ha HEAD staccato: non lo tocco, rimetti un ramo con /inizio $name"
    ERRORS=$((ERRORS + 1))
    continue
  fi

  # Fetch prima dello stash: un repository sporco ma già allineato non si mette da parte. Lo stash tirava
  # indietro per qualche secondo i file di un'altra sessione al lavoro nel repository (7/11/2026, I11).
  # Con il fetch fallito, o senza upstream, si prosegue: il pull qui sotto fallisce e dice la causa.
  if git -C "$dir" fetch -q 2>/dev/null && [ "$(git -C "$dir" rev-list --count 'HEAD..@{u}' 2>/dev/null)" = "0" ]; then
    echo "  Già aggiornato"
    CONFLICTS=$(git -C "$dir" diff --name-only --diff-filter=U 2>/dev/null)
    if [ -n "$CONFLICTS" ]; then
      echo "  CONFLITTI:"
      echo "$CONFLICTS" | sed 's/^/    /'
      ERRORS=$((ERRORS + 1))
    fi
    continue
  fi

  if [ "$TRACKED_DIRTY" = "1" ] || [ "$STAGED_DIRTY" = "1" ]; then
    if git -C "$dir" stash push -m "auto-stash-sync-$(date +%s)" >/dev/null 2>&1; then
      STASHED=1
      echo "  Auto-stash applicato"
    fi
  fi

  BEFORE=$(git -C "$dir" rev-parse HEAD 2>/dev/null)
  # In inglese (LC_ALL=C): le cause qui sotto si leggono dai messaggi di git, che con git in italiano cambiano.
  PULL_OUT=$(LC_ALL=C git -C "$dir" pull --rebase 2>&1)
  PULL_RC=$?
  echo "$PULL_OUT" | tail -3

  if [ "$PULL_RC" -ne 0 ]; then
    # La causa si legge nell'output, non si indovina: un pull senza credenziali non è un conflitto.
    # Fino al 22/11/2026 ogni causa diversa dalle credenziali usciva come "conflitto": rete giù, ramo
    # senza upstream e ramo sparito dal remoto mandavano a risolvere un conflitto che non c'era (A10).
    case "$PULL_OUT" in
      *"could not read Username"*|*"Authentication failed"*|*"Permission denied (publickey)"*|*"terminal prompts disabled"*)
        echo "ERRORE: pull $name fallito - credenziali git assenti per il remote, lancia: gh auth setup-git" ;;
      *"Could not resolve host"*|*"Connection timed out"*|*"Connection refused"*|*"Operation timed out"*|*"Network is unreachable"*|*"unable to access"*|*"Could not read from remote repository"*)
        echo "ERRORE: pull $name fallito - remoto non raggiungibile (rete o indirizzo), riprova quando la rete torna" ;;
      *"There is no tracking information"*|*"no such ref was fetched"*|*"couldn't find remote ref"*)
        echo "ERRORE: pull $name fallito - il ramo non ha un ramo remoto da seguire, impostalo con /inizio $name" ;;
      *"CONFLICT"*|*"could not apply"*|*"Resolve all conflicts"*|*"would be overwritten"*|*"You have unstaged changes"*)
        echo "ERRORE: pull $name fallito - conflitto con modifiche locali, risolvi con /inizio $name" ;;
      *)
        echo "ERRORE: pull $name fallito - causa non riconosciuta: $(printf '%s\n' "$PULL_OUT" | grep -v '^[[:space:]]*$' | tail -1)" ;;
    esac
    # Prima del pull nessun rebase era a metà (controllo sopra): se ce n'è uno, è di questo pull.
    git -C "$dir" rebase --abort 2>/dev/null
    [ "$STASHED" = "1" ] && rimetti_stash "$dir" >/dev/null 2>&1
    ERRORS=$((ERRORS + 1))
    continue
  fi

  AFTER=$(git -C "$dir" rev-parse HEAD 2>/dev/null)

  if [ "$STASHED" = "1" ]; then
    if rimetti_stash "$dir" | grep -qiE "conflitto|conflict"; then
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
