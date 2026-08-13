#!/bin/bash
# Hook: Session reminder
# Controlla se è passato troppo tempo dall'ultimo commit e suggerisce checkpoint
# Eseguito come hook PostToolUse periodico

# Nome stabile per il state file (basato sulla directory di lavoro, non sul PID)
PROJECT_HASH=$(echo "$PWD" | md5 -q 2>/dev/null || echo "$PWD" | md5sum 2>/dev/null | cut -d' ' -f1 || python3 -c "import hashlib,sys; print(hashlib.md5(sys.argv[1].encode()).hexdigest()[:16])" "$PWD" 2>/dev/null || echo "$PWD" | tr -dc 'a-zA-Z0-9' | cut -c1-16)
STATE_FILE="/tmp/claude_session_reminder_${PROJECT_HASH}"
REMINDER_INTERVAL=7200  # 2 ore in secondi

# Inizializza se non esiste
if [ ! -f "$STATE_FILE" ]; then
  echo "$(date +%s)" > "$STATE_FILE"
  exit 0
fi

# Leggi ultimo check
LAST_CHECK=$(cat "$STATE_FILE")
NOW=$(date +%s)
ELAPSED=$((NOW - LAST_CHECK))

# Se sono passate più di 2 ore
if [ $ELAPSED -gt $REMINDER_INTERVAL ]; then
  # Verifica se siamo in un repo git
  if git rev-parse --git-dir > /dev/null 2>&1; then
    # Controlla ultimo commit
    LAST_COMMIT=$(git log -1 --format=%ct 2>/dev/null)

    if [ -n "$LAST_COMMIT" ]; then
      SINCE_COMMIT=$((NOW - LAST_COMMIT))

      # Se l'ultimo commit è più vecchio di 2 ore
      if [ $SINCE_COMMIT -gt $REMINDER_INTERVAL ]; then
        HOURS=$((SINCE_COMMIT / 3600))
        echo ""
        echo "--- SESSION REMINDER ---"
        echo "Ultimo commit: ${HOURS}h fa"
        echo "Considera: /commit o checkpoint con git stash"
        echo "Per chiudere pulito: /fine"
        echo "------------------------"
      fi
    fi
  fi

  # Aggiorna timestamp
  echo "$NOW" > "$STATE_FILE"
fi

exit 0
