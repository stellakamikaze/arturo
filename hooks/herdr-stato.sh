#!/bin/sh
# Stato di Claude Code verso Herdr, col protocollo OSC 7501.
# Uso: herdr-stato.sh <idle|working|blocked|done|error>. Fuori da Herdr esce subito.
cat >/dev/null 2>&1
[ -n "${HC_TERMINAL_ID:-}" ] || exit 0
case "${1:-}" in idle|working|blocked|done|error) ;; *) exit 0 ;; esac
seq=$(printf '\033]7501;state=%s:app=claude-code\033\\' "$1")
if { printf '%s' "$seq" > /dev/tty; } 2>/dev/null; then exit 0; fi
# Senza terminale di controllo: il primo tty fra gli antenati (al massimo 8).
p=$PPID
for _ in 1 2 3 4 5 6 7 8; do
  [ -n "$p" ] && [ "$p" -gt 1 ] 2>/dev/null || exit 0
  t=$(ps -o tty= -p "$p" 2>/dev/null | tr -d ' ')
  case "$t" in '' | '?' | '??') p=$(ps -o ppid= -p "$p" 2>/dev/null | tr -d ' ') ;;
    *) { printf '%s' "$seq" > "/dev/$t"; } 2>/dev/null; exit 0 ;;
  esac
done
exit 0
