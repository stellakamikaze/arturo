#!/bin/bash
# Hook Fine Sessione - Promemoria
# Mostra reminder prima della chiusura

PROJECT_ROOT="${PWD}"
PROJECT_NAME="$(basename "$PROJECT_ROOT")"

# Esegui solo se siamo in una directory di progetto
if [ ! -d "$PROJECT_ROOT/.git" ] && [ ! -f "$PROJECT_ROOT/CLAUDE.md" ]; then
    exit 0
fi

# Cleanup file temporanei sessione: deve avvenire anche su tree pulito.
rm -f ~/.claude/claude-md-unlock-* ~/.claude/config-unlock-* ~/.claude/system-unlock-* 2>/dev/null
rm -f /tmp/claude_session_reminder_* 2>/dev/null

# Il promemoria esce anche a tree pulito: una sessione di ricerca, bozze o decisioni non
# cambia file, ma produce cose da ricordare. Cambia solo il testo.
SOLO_LETTURA=0
if [ -d "$PROJECT_ROOT/.git" ]; then
    CHANGES=$(git -C "$PROJECT_ROOT" status --porcelain 2>/dev/null)
    [ -z "$CHANGES" ] && SOLO_LETTURA=1
fi

# macOS: ripristina titolo terminale
if [[ "$OSTYPE" == "darwin"* ]]; then
  WID_FILE="$HOME/.claude/session-env/terminal-wid-$PROJECT_NAME"
  if [ -f "$WID_FILE" ]; then
    WID=$(cat "$WID_FILE")
    osascript -e "tell application \"Terminal\" to set custom title of window id $WID to \"Terminal\"" 2>/dev/null
    rm -f "$WID_FILE"
  fi
fi

if [ "$SOLO_LETTURA" = "1" ]; then
cat << 'EOF'
---
PROMEMORIA FINE SESSIONE (nessun file cambiato)

Avete preso decisioni, scritto bozze o scartato strade? Chiudi con /fine:
salva quello che serve alla prossima sessione. Se non e' emerso niente,
chiudi pure senza.
---
EOF
else
cat << 'EOF'
---
PROMEMORIA FINE SESSIONE

Prima di chiudere, considera:

1. **Task pendenti** - Saranno inclusi nell'handoff
2. **Usa /fine** per chiudere sessione correttamente
3. **Commit** - Committa le modifiche se necessario
---
EOF
fi
