#!/usr/bin/env bash
# UserPromptSubmit: guscio di hooks/inject-now.py (#6492, B4, 23/11/2026). In settings.json l'hook gira dentro
# `hooks/hub.py prompt`, senza processi in più; questo file resta per le config vecchie e per i banchi.
# Il prompt arriva in UTF-8 e Claude Code legge l'uscita in UTF-8: su Windows python3 userebbe cp1252
# su stdin e stdout (5/11/2026, #4790).
export PYTHONIOENCODING=utf-8
D="$(cd "$(dirname "${BASH_SOURCE[0]}")" 2>/dev/null && pwd)"
if command -v python3 >/dev/null 2>&1 && [ -f "$D/inject-now.py" ]; then
  exec python3 "$D/inject-now.py"
fi
# Senza python3 resta l'ora.
date '+Ora corrente: %Y-%m-%d %H:%M %Z (%A)'
