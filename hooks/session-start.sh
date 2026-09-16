#!/bin/bash
# Hook Avvio Sessione - Caricamento Memoria
# Carica il contesto del progetto all'avvio della sessione

PROJECT_ROOT="${PWD}"
PROJECT_NAME="$(basename "$PROJECT_ROOT")"

# macOS: cattura window ID e setta titolo terminale
if [[ "$OSTYPE" == "darwin"* ]]; then
  mkdir -p "$HOME/.claude/session-env"   # dir gitignored: non esiste su un clone fresco
  WID_FILE="$HOME/.claude/session-env/terminal-wid-$PROJECT_NAME"
  WID=$(osascript -e 'tell application "Terminal" to id of front window' 2>/dev/null)
  if [ -n "$WID" ]; then
    echo "$WID" > "$WID_FILE"
    osascript -e "tell application \"Terminal\" to set custom title of window id $WID to \"Claude: $PROJECT_NAME\"" 2>/dev/null
  fi
fi

# Info directory di lavoro
echo "DIRECTORY: $PROJECT_ROOT"

# Reminder context management
echo "CONTEXT: al ~65% di utilizzo completa il task, chiudi con /fine e riparti con /inizio in una sessione nuova"

# Avvisi Git locali: nessuna rete, nessun comando in background.
if git -C "$PROJECT_ROOT" rev-parse --git-dir >/dev/null 2>&1; then
  CHANGES=$(git -C "$PROJECT_ROOT" status --porcelain 2>/dev/null || true)
  [[ -n "$CHANGES" ]] && echo "GIT: working tree con modifiche non committate"
  REBASE_MERGE=$(git -C "$PROJECT_ROOT" rev-parse --git-path rebase-merge 2>/dev/null)
  REBASE_APPLY=$(git -C "$PROJECT_ROOT" rev-parse --git-path rebase-apply 2>/dev/null)
  if [[ -d "$REBASE_MERGE" || -d "$REBASE_APPLY" ]]; then
    echo "GIT: rebase in corso — risolvilo prima di lavorare"
  fi
fi

# Guardia anti-divergenza config (~/.claude vs origin/main).
# Il confronto legge gli oggetti Git gia' presenti in locale: senza un fetch resta fermo a
# quello che sapeva l'ultima volta, e chi non lancia mai /inizio non vedrebbe mai un
# aggiornamento. Per questo il fetch parte qui, in background e al massimo ogni 6 ore, cosi'
# l'avvio non aspetta la rete. L'avviso di questa sessione usa il fetch della volta prima.
if git -C "$HOME/.claude" rev-parse --git-dir >/dev/null 2>&1; then
  MARCATORE="$HOME/.claude/session-env/ultimo-fetch"
  ADESSO=$(date +%s)
  SCORSO=$(cat "$MARCATORE" 2>/dev/null || echo 0)
  case "$SCORSO" in (*[!0-9]*|"") SCORSO=0 ;; esac
  if [ $((ADESSO - SCORSO)) -gt 21600 ]; then
    mkdir -p "$HOME/.claude/session-env" 2>/dev/null
    printf '%s' "$ADESSO" > "$MARCATORE" 2>/dev/null
    # GIT_TERMINAL_PROMPT=0: un repository che chiede le credenziali non deve mai appendere
    # l'avvio della sessione.
    ( GIT_TERMINAL_PROMPT=0 git -C "$HOME/.claude" fetch --quiet --all >/dev/null 2>&1 & ) >/dev/null 2>&1
  fi
  AHEAD=$(git -C "$HOME/.claude" rev-list --count origin/main..HEAD 2>/dev/null || echo 0)
  BEHIND=$(git -C "$HOME/.claude" rev-list --count HEAD..origin/main 2>/dev/null || echo 0)
  # Se origin e' il repo originale di Arturo, chi usa non puo' pusharci: commit locali
  # "avanti" sono normali e l'avviso sarebbe solo rumore. Tace solo in quel caso.
  ORIGIN_URL=$(git -C "$HOME/.claude" remote get-url origin 2>/dev/null || echo "")
  case "$ORIGIN_URL" in
    https://github.com/stellakamikaze/arturo | https://github.com/stellakamikaze/arturo.git | \
    git@github.com:stellakamikaze/arturo | git@github.com:stellakamikaze/arturo.git | \
    ssh://git@github.com/stellakamikaze/arturo | ssh://git@github.com/stellakamikaze/arturo.git)
      ORIGIN_ARTURO=1 ;;
    *)
      ORIGIN_ARTURO=0 ;;
  esac
  if [ "${AHEAD:-0}" -gt 0 ] && [ "$ORIGIN_ARTURO" -eq 0 ]; then
    echo "CONFIG: ~/.claude e' AVANTI di $AHEAD commit non pushati"
  fi
  if [ "${BEHIND:-0}" -gt 0 ]; then
    echo "ARTURO: c'e' un aggiornamento ($BEHIND commit) — scaricalo con /aggiorna"
  fi
  # Con un repository personale come origin, Arturo vive su upstream.
  if git -C "$HOME/.claude" rev-parse --verify --quiet upstream/main >/dev/null 2>&1; then
    UPSTREAM_BEHIND=$(git -C "$HOME/.claude" rev-list --count HEAD..upstream/main 2>/dev/null || echo 0)
    if [ "${UPSTREAM_BEHIND:-0}" -gt 0 ]; then
      echo "ARTURO: c'e' un aggiornamento dell'harness ($UPSTREAM_BEHIND commit su upstream) — scaricalo con /aggiorna"
    fi
  fi
fi

# Canale novità: se NOVITA.md ha una entry più recente dell'ultima vista, segnala.
# Solo un avviso — il racconto lo fa /novita, mai in automatico.
if [ -f "$HOME/.claude/NOVITA.md" ]; then
  ULTIMA_NOVITA=$(grep -m1 '^## ' "$HOME/.claude/NOVITA.md" 2>/dev/null | grep -oE '[0-9]{4}-[0-9]{2}-[0-9]{2}')
  # Segnalibro per intestazione (novita-viste: data e titolo); un vecchio novita-vista
  # con una sola data vale come "viste fino a".
  NOVITA_VISTE="$HOME/.claude/session-env/novita-viste"
  NOVITA_VECCHIA=$(cat "$HOME/.claude/session-env/novita-vista" 2>/dev/null || echo "")
  NON_VISTE=0
  while IFS= read -r ENTRY; do
    [ -z "$ENTRY" ] && continue
    DATA=$(printf '%s' "$ENTRY" | grep -oE '^[0-9]{4}-[0-9]{2}-[0-9]{2}')
    [ -n "$NOVITA_VECCHIA" ] && [ -n "$DATA" ] && [[ ! "$DATA" > "$NOVITA_VECCHIA" ]] && continue
    grep -qxF "$ENTRY" "$NOVITA_VISTE" 2>/dev/null && continue
    NON_VISTE=$((NON_VISTE + 1))
  done < <(grep '^## ' "$HOME/.claude/NOVITA.md" 2>/dev/null | sed 's/^## //')
  if [ "$NON_VISTE" -gt 0 ]; then
    echo "NOVITA': $NON_VISTE aggiornamenti dell'harness non ancora letti (ultimo: $ULTIMA_NOVITA) — digita /novita per fartelo raccontare"
  fi
fi
