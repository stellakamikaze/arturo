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

# Guardia anti-divergenza config (~/.claude vs origin/main).
# Confronta con l'ultimo fetch (zero latenza) e lancia un fetch async per la
# prossima sessione. Evita che una macchina resti indietro
# rispetto alle altre senza accorgersene.
if git -C "$HOME/.claude" rev-parse --git-dir >/dev/null 2>&1; then
  BEHIND=$(git -C "$HOME/.claude" rev-list --count HEAD..origin/main 2>/dev/null || echo 0)
  if [ "${BEHIND:-0}" -gt 0 ]; then
    echo "CONFIG: ~/.claude e' INDIETRO di $BEHIND commit rispetto a origin/main — eseguire 'git -C ~/.claude pull --rebase' prima di lavorare (rischio divergenza tra macchine)"
  fi
  (git -C "$HOME/.claude" fetch --quiet origin main >/dev/null 2>&1 &)
fi

# Canale novità: se NOVITA.md ha una entry più recente dell'ultima vista, segnala.
# Solo un avviso — il racconto lo fa /novita, mai in automatico.
if [ -f "$HOME/.claude/NOVITA.md" ]; then
  ULTIMA_NOVITA=$(grep -m1 '^## ' "$HOME/.claude/NOVITA.md" 2>/dev/null | grep -oE '[0-9]{4}-[0-9]{2}-[0-9]{2}')
  NOVITA_VISTA=$(cat "$HOME/.claude/session-env/novita-vista" 2>/dev/null || echo "")
  if [ -n "$ULTIMA_NOVITA" ] && [ "$ULTIMA_NOVITA" != "$NOVITA_VISTA" ]; then
    echo "NOVITA': aggiornamenti dell'harness non ancora letti (ultimo: $ULTIMA_NOVITA) — digita /novita per fartelo raccontare"
  fi
fi
