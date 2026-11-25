#!/bin/sh
# Stato di Claude Code verso Herdr, col protocollo OSC 7501.
# Uso: herdr-stato.sh <idle|working|blocked|done|error>. Fuori da Herdr esce subito.
cat >/dev/null 2>&1
# Una sessione in background (claude --bg, CLAUDE_JOB_DIR) passa anche senza HC_TERMINAL_ID: la vedono le
# schede che la agganciano con claude attach, non il terminale di chi ha avviato il servizio (25/11/2026, #5587).
[ -n "${HC_TERMINAL_ID:-}" ] || [ -n "${CLAUDE_JOB_DIR:-}" ] || exit 0
case "${1:-}" in idle|working|blocked|done|error) ;; *) exit 0 ;; esac
# Windows (25/11/2026, #5639): l'hook gira senza terminale di controllo, il ps di Git non ha -o e il padre che
# vede sh è 1. Scrive l'aiutante accanto, agganciato alla console di claude.exe. Prima python: su Windows
# python3 è spesso il rimando del Microsoft Store, che esce 9009 senza eseguire. Un Python di MSYS2 o Cygwin
# fa uscire l'aiutante con 2: anche allora si prova l'interprete dopo. Il percorso può avere le \.
if [ "${OS:-}" = Windows_NT ]; then
  # Una sessione in background su Windows non ha lo stato nel file (niente /bin/sh per l'aggancio, #5587).
  [ -n "${HC_TERMINAL_ID:-}" ] || exit 0
  export PYTHONIOENCODING=utf-8
  case "$0" in */* | *\\*) cartella=${0%[/\\]*} ;; *) cartella=. ;; esac
  for py in python python3; do
    "$py" "$cartella/herdr-stato-windows.py" "$1" </dev/null >/dev/null 2>&1 && exit 0
  done
  exit 0
fi
seq=$(printf '\033]7501;state=%s:app=claude-code\033\\' "$1")
if [ -n "${HC_TERMINAL_ID:-}" ] && ! { printf '%s' "$seq" > /dev/tty; } 2>/dev/null; then
  # Senza terminale di controllo: il primo tty fra gli antenati (al massimo 8).
  p=$PPID
  for _ in 1 2 3 4 5 6 7 8; do
    [ -n "$p" ] && [ "$p" -gt 1 ] 2>/dev/null || break
    t=$(ps -o tty= -p "$p" 2>/dev/null | tr -d ' ')
    case "$t" in '' | '?' | '??') p=$(ps -o ppid= -p "$p" 2>/dev/null | tr -d ' ') ;;
      *) { printf '%s' "$seq" > "/dev/$t"; } 2>/dev/null; break ;;
    esac
  done
fi
# Sessione in background (#5587): il suo tty è il terminale nascosto del servizio, e claude attach non
# inoltra l'OSC. Lo stato va in ~/.cache/herdr-stato/<job id>, che l'aggancio di Volta legge all'apertura,
# e sul tty di ogni claude attach <job id> di questa macchina. Un attach via ssh mostra la sessione di
# un'altra macchina: lì scrive l'hook di là. Sul tty solo quando lo stato cambia: così l'OSC non entra a
# ogni strumento nello schermo che claude attach sta disegnando.
job=${CLAUDE_JOB_DIR:-}
job=${job%/}
job=${job##*/}
case "$job" in '' | *[!0-9A-Za-z_-]*) exit 0 ;; esac
[ -n "${HOME:-}" ] || exit 0
cache="$HOME/.cache/herdr-stato"
prima=$(cat "$cache/$job" 2>/dev/null)
[ "$prima" = "$1" ] && exit 0
mkdir -p "$cache" 2>/dev/null
printf '%s\n' "$1" > "$cache/$job.$$" 2>/dev/null && mv -f "$cache/$job.$$" "$cache/$job" 2>/dev/null
ps -Ao tty=,args= 2>/dev/null | {
  visti=" "
  while read -r t a; do
    case "$t" in '' | '?' | '??') continue ;; esac
    case "$visti" in *" $t "*) continue ;; esac
    case " $a " in *" attach $job "*) ;; *) continue ;; esac
    case "$a" in *claude*) ;; *) continue ;; esac
    case " $a " in *" ssh "* | */ssh\ *) continue ;; esac
    visti="$visti$t "
    { printf '%s' "$seq" > "/dev/$t"; } 2>/dev/null
  done
}
exit 0
