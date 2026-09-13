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
# Legge solo gli oggetti Git gia' presenti in locale.
if git -C "$HOME/.claude" rev-parse --git-dir >/dev/null 2>&1; then
  AHEAD=$(git -C "$HOME/.claude" rev-list --count origin/main..HEAD 2>/dev/null || echo 0)
  BEHIND=$(git -C "$HOME/.claude" rev-list --count HEAD..origin/main 2>/dev/null || echo 0)
  if [ "${AHEAD:-0}" -gt 0 ]; then
    echo "CONFIG: ~/.claude e' AVANTI di $AHEAD commit non pushati"
  fi
  if [ "${BEHIND:-0}" -gt 0 ]; then
    echo "CONFIG: ~/.claude e' INDIETRO di $BEHIND commit rispetto a origin/main"
  fi
  # Con un repository personale come origin, Arturo vive su upstream.
  if git -C "$HOME/.claude" rev-parse --verify --quiet upstream/main >/dev/null 2>&1; then
    UPSTREAM_BEHIND=$(git -C "$HOME/.claude" rev-list --count HEAD..upstream/main 2>/dev/null || echo 0)
    if [ "${UPSTREAM_BEHIND:-0}" -gt 0 ]; then
      echo "ARTURO: $UPSTREAM_BEHIND aggiornamenti dell'harness su upstream/main non ancora applicati — /novita te li racconta"
    fi
  fi
fi

# Canale novità: se NOVITA.md ha una entry più recente dell'ultima vista, segnala.
# Solo un avviso — il racconto lo fa /novita, mai in automatico.
if [ -f "$HOME/.claude/NOVITA.md" ]; then
  ULTIMA_NOVITA=$(grep -m1 '^## ' "$HOME/.claude/NOVITA.md" 2>/dev/null | grep -oE '[0-9]{4}-[0-9]{2}-[0-9]{2}')
  # Segnalibro per entry (novita-viste); un vecchio novita-vista vale come "viste fino a".
  NOVITA_VISTE="$HOME/.claude/session-env/novita-viste"
  NOVITA_VECCHIA=$(cat "$HOME/.claude/session-env/novita-vista" 2>/dev/null || echo "")
  NON_VISTE=0
  while IFS= read -r DATA; do
    [ -z "$DATA" ] && continue
    [ -n "$NOVITA_VECCHIA" ] && [[ ! "$DATA" > "$NOVITA_VECCHIA" ]] && continue
    grep -qxF "$DATA" "$NOVITA_VISTE" 2>/dev/null && continue
    NON_VISTE=$((NON_VISTE + 1))
  done < <(grep '^## ' "$HOME/.claude/NOVITA.md" 2>/dev/null | grep -oE '[0-9]{4}-[0-9]{2}-[0-9]{2}')
  if [ "$NON_VISTE" -gt 0 ]; then
    echo "NOVITA': $NON_VISTE aggiornamenti dell'harness non ancora letti (ultimo: $ULTIMA_NOVITA) — digita /novita per fartelo raccontare"
  fi
fi
