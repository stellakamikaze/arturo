#!/bin/bash
# Hook Fine Sessione - Promemoria
# Mostra reminder prima della chiusura

PROJECT_ROOT="${PWD}"
PROJECT_NAME="$(basename "$PROJECT_ROOT")"

# L'aggiornamento automatico (bin/aggiornamenti.py), prima dell'uscita qui sotto: ogni chiusura,
# anche fuori da un progetto. Gira staccato dalla sessione, così la sessione dopo parte con
# impostazioni e hook della stessa versione. Aspetta che Claude Code sia uscito davvero, e rimanda
# se resta aperta un'altra sessione: la installa l'ultima che chiude.
if [ -f "$HOME/.claude/bin/aggiornamenti.py" ] && [ "${ARTURO_AGGIORNAMENTI:-}" != "manuali" ]; then
  mkdir -p "$HOME/.claude/session-env" 2>/dev/null
  ARTURO_BASH="$BASH" nohup python3 "$HOME/.claude/bin/aggiornamenti.py" applica \
    >> "$HOME/.claude/session-env/aggiornamento.log" 2>&1 < /dev/null &
fi

# Il resto solo in una directory di progetto
if [ ! -d "$PROJECT_ROOT/.git" ] && [ ! -f "$PROJECT_ROOT/CLAUDE.md" ]; then
    exit 0
fi

# Cleanup file temporanei sessione: deve avvenire anche su tree pulito.
# I file di sblocco di questa sessione, e quelli rimasti da più di un giorno: un'altra sessione ancora
# aperta perdeva il suo sblocco a metà lavoro (30/10/2026). L'id arriva nel JSON dell'hook.
HOOK_INPUT=""
[ -t 0 ] || IFS= read -r -t 2 -d '' HOOK_INPUT || true
SESSIONE=$(printf '%s' "$HOOK_INPUT" | sed -n 's/.*"session_id"[[:space:]]*:[[:space:]]*"\([A-Za-z0-9_-]*\)".*/\1/p' | head -1)
if [ -n "$SESSIONE" ]; then
  rm -f ~/.claude/claude-md-unlock-"$SESSIONE" ~/.claude/config-unlock-"$SESSIONE" \
        ~/.claude/system-unlock-"$SESSIONE" ~/.claude/session-env/retrieve-"$SESSIONE".seen 2>/dev/null
fi
find ~/.claude -maxdepth 1 \( -name 'claude-md-unlock-*' -o -name 'config-unlock-*' -o -name 'system-unlock-*' \) \
  -mtime +0 -exec rm -f {} + 2>/dev/null
# I file seen di memory-retrieve.py, uno per sessione: nessuno li toglieva.
find ~/.claude/session-env -maxdepth 1 -name 'retrieve-*.seen' -mtime +0 -exec rm -f {} + 2>/dev/null
# Le conferme chieste dalle guardie e rimaste senza esito (un no): gli id valgono per una sessione.
rm -f ~/.claude/session-env/telemetria-attese.json 2>/dev/null

# Il promemoria esce anche a tree pulito: una sessione di ricerca, bozze o decisioni non
# cambia file, ma produce cose da ricordare. Cambia solo il testo.
SOLO_LETTURA=0
if [ -d "$PROJECT_ROOT/.git" ]; then
    CHANGES=$(git -C "$PROJECT_ROOT" status --porcelain 2>/dev/null)
    [ -z "$CHANGES" ] && SOLO_LETTURA=1
fi

# macOS: ripristina il titolo della finestra lasciato dalle versioni prima del 20/10/2026, che lo
# impostavano via osascript all'avvio. Il file si cancella, quindi succede una volta sola (#3587).
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

# Le aggiunte della persona (personale/session-end.sh, 16/10/2026): gli aggiornamenti di Arturo non le
# toccano, e /aggiorna ci sposta da solo le righe aggiunte a questo file. Girano in una subshell
# alla fine, con le variabili di qui: un loro errore non ferma la sessione.
if [ -f "$HOME/.claude/personale/session-end.sh" ]; then
  ( . "$HOME/.claude/personale/session-end.sh" ) || true
fi
