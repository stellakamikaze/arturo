#!/bin/sh
# Stato di Claude Code verso Herdr, col protocollo OSC 7501.
# Uso: herdr-stato.sh <idle|working|blocked|done|error>. Fuori da Herdr esce subito.
cat >/dev/null 2>&1
[ -n "${HC_TERMINAL_ID:-}" ] || exit 0
case "${1:-}" in idle|working|blocked|done|error) ;; *) exit 0 ;; esac
# Windows (25/11/2026, #5639): l'hook gira senza terminale di controllo, il ps di Git non ha -o e il padre che
# vede sh è 1. Scrive l'aiutante accanto, agganciato alla console di claude.exe. Prima python: su Windows
# python3 è spesso il rimando del Microsoft Store, che esce 9009 senza eseguire. Un Python di MSYS2 o Cygwin
# fa uscire l'aiutante con 2: anche allora si prova l'interprete dopo. Il percorso può avere le \.
if [ "${OS:-}" = Windows_NT ]; then
  export PYTHONIOENCODING=utf-8
  case "$0" in */* | *\\*) cartella=${0%[/\\]*} ;; *) cartella=. ;; esac
  for py in python python3; do
    "$py" "$cartella/herdr-stato-windows.py" "$1" </dev/null >/dev/null 2>&1 && exit 0
  done
  exit 0
fi
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
