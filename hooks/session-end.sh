#!/bin/bash
# Hook Fine Sessione - Promemoria
# Mostra reminder prima della chiusura

# Su Windows python3 userebbe cp1252 su stdin e stdout: ogni hook .sh che lancia Python forza UTF-8 (U08).
export PYTHONIOENCODING=utf-8

PROJECT_ROOT="${PWD}"
PROJECT_NAME="$(basename "$PROJECT_ROOT")"

# Il JSON dell'hook: id della sessione, transcript e motivo. Si legge prima dell'uscita qui sotto, perché
# l'aggiornamento e la telemetria della chiusura valgono anche fuori da un progetto.
HOOK_INPUT=""
[ -t 0 ] || IFS= read -r -t 2 -d '' HOOK_INPUT || true
MOTIVO=$(printf '%s' "$HOOK_INPUT" | sed -n 's/.*"reason"[[:space:]]*:[[:space:]]*"\([a-z_]*\)".*/\1/p' | head -1)

# L'aggiornamento automatico (bin/aggiornamenti.py), prima dell'uscita qui sotto: ogni chiusura,
# anche fuori da un progetto. Gira staccato dalla sessione, così la sessione dopo parte con
# impostazioni e hook della stessa versione. Aspetta che Claude Code sia uscito davvero, e rimanda
# se resta aperta un'altra sessione: la installa la chiusura dopo, senza più aspettare le altre (#4074).
# Un /clear chiude la sessione ma il processo resta vivo, coi mod caricati: niente aggiornamento, né subito
# né come rinvio. Il secondo /clear installava il rinvio sotto la sessione aperta (finding 19, 7/11/2026).
# Il codice si trova dalla cartella di questo hook, come in session-start.sh (strati F1, docs/strati.md).
ARTURO_CODICE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." 2>/dev/null && pwd)"
[ -n "$ARTURO_CODICE" ] || ARTURO_CODICE="$HOME/.claude"
# Col clone lo script sta in ~/.claude. Col plugin sta accanto a questo hook (10/11/2026): la chiusura installa
# il rilascio firmato con la strada di /aggiorna, e non rinvia. Fino alla 0.2.10 col plugin qui non partiva
# niente. Un checkout di sviluppo (con .git, fuori da ~/.claude) non installa niente.
AGGIORNA=""
ORSA_AGG="$HOME/.claude"
if [ -f "$HOME/.claude/bin/aggiornamenti.py" ]; then
  AGGIORNA="$HOME/.claude/bin/aggiornamenti.py"
elif [ -f "$ARTURO_CODICE/.claude-plugin/plugin.json" ] && [ ! -e "$ARTURO_CODICE/.git" ]; then
  AGGIORNA="$ARTURO_CODICE/bin/aggiornamenti.py"
  ORSA_AGG="${ARTURO_RADICE:-${CLAUDE_CONFIG_DIR:-$HOME/.claude}}"
fi
if [ -n "$AGGIORNA" ] && [ -f "$AGGIORNA" ] && [ "${ARTURO_AGGIORNAMENTI:-}" != "manuali" ] && [ "$MOTIVO" != clear ]; then
  mkdir -p "$ORSA_AGG/session-env" 2>/dev/null
  # Il processo staccato può restare senza `claude` nel PATH: glielo passa la sessione che si chiude.
  ARTURO_BASH="$BASH" ARTURO_CLAUDE="${ARTURO_CLAUDE:-$(command -v claude 2>/dev/null)}" \
    nohup python3 "$AGGIORNA" applica >> "$ORSA_AGG/session-env/aggiornamento.log" 2>&1 < /dev/null &
fi

# Telemetria (3/11/2026, #4540): durata e messaggi della sessione in fasce, e le skill usate. Legge il
# transcript in background, così la chiusura non aspetta; spenta, telemetria.py non registra niente.
if [ -n "$HOOK_INPUT" ] && [ -f "$ARTURO_CODICE/bin/telemetria.py" ]; then
  printf '%s' "$HOOK_INPUT" | nohup python3 "$ARTURO_CODICE/bin/telemetria.py" fine >/dev/null 2>&1 &
fi

# Il resto solo in una directory di progetto
if [ ! -d "$PROJECT_ROOT/.git" ] && [ ! -f "$PROJECT_ROOT/CLAUDE.md" ]; then
    exit 0
fi

# Cleanup file temporanei sessione: deve avvenire anche su tree pulito.
# I file di sblocco di questa sessione, e quelli rimasti da più di un giorno: un'altra sessione ancora
# aperta perdeva il suo sblocco a metà lavoro (30/10/2026). L'id arriva nel JSON dell'hook.
SESSIONE=$(printf '%s' "$HOOK_INPUT" | sed -n 's/.*"session_id"[[:space:]]*:[[:space:]]*"\([A-Za-z0-9_-]*\)".*/\1/p' | head -1)
if [ -n "$SESSIONE" ]; then
  rm -f ~/.claude/claude-md-unlock-"$SESSIONE" ~/.claude/config-unlock-"$SESSIONE" \
        ~/.claude/system-unlock-"$SESSIONE" ~/.claude/session-env/retrieve-"$SESSIONE".seen 2>/dev/null
fi
find ~/.claude -maxdepth 1 \( -name 'claude-md-unlock-*' -o -name 'config-unlock-*' -o -name 'system-unlock-*' \) \
  -mtime +0 -exec rm -f {} + 2>/dev/null
# I file seen di memory-retrieve.py, uno per sessione: nessuno li toglieva.
find ~/.claude/session-env -maxdepth 1 -name 'retrieve-*.seen' -mtime +0 -exec rm -f {} + 2>/dev/null
# I registri dei commit per sessione della regola git-amend (block-dangerous.py dopo, 3/11/2026).
find ~/.claude/session-env -maxdepth 1 -name 'commit-*.json' -mtime +0 -exec rm -f {} + 2>/dev/null
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
    # Prima il file, poi osascript staccato: se macOS chiede il permesso di Automazione, osascript aspetta, l'hook
    # scade a 10 secondi e il file restava, con la stessa attesa a ogni chiusura (lotto L10).
    rm -f "$WID_FILE"
    osascript -e "tell application \"Terminal\" to set custom title of window id $WID to \"Terminal\"" >/dev/null 2>&1 &
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
