#!/bin/bash
# Notifica audio one-shot quando Claude attende input (cross-platform)
# macOS: afplay, Windows/Git Bash: PowerShell beep, Linux: noop

# Detect platform e comando notifica
if [[ "$OSTYPE" == "darwin"* ]]; then
  afplay /System/Library/Sounds/Sosumi.aiff 2>/dev/null &
elif [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" ]]; then
  pwsh -NoProfile -Command "[console]::beep(800,300)" 2>/dev/null || powershell -NoProfile -Command "[console]::beep(800,300)" 2>/dev/null &
fi

exit 0
