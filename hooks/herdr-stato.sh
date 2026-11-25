#!/bin/sh
# Stato di Claude Code verso Herdr, col protocollo OSC 7501.
# Uso: herdr-stato.sh <idle|working|blocked|done|error>. Fuori da Herdr esce subito.
# L'ora per l'ordine (#5587) si prende prima di tutto: due hook vicini possono finire in ordine inverso.
ora=$(date +%s%N 2>/dev/null)
case "$ora" in '' | *[!0-9]*) ora=$(perl -MTime::HiRes=gettimeofday -e '($s,$u)=gettimeofday; printf "%d%06d000", $s, $u' 2>/dev/null) ;; esac
case "$ora" in '' | *[!0-9]*) ora="$(date +%s)000000000" ;; esac
ingresso=$(cat 2>/dev/null)
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
# Un claude -p lanciato da una sessione in background eredita CLAUDE_JOB_DIR (e HC_TERMINAL_ID) ma ha un suo
# session id (prova del 25/11/2026, #5587). Lo stato è della sessione di primo livello: il suo id sta in
# state.json del job (sessionId, e resumeSessionId dopo /clear). Senza la chiave sessionId il formato è
# cambiato, e si accetta come prima.
if [ -n "${CLAUDE_JOB_DIR:-}" ]; then
  sid=$(printf '%s' "$ingresso" | sed -n 's/.*"session_id"[[:space:]]*:[[:space:]]*"\([0-9A-Za-z_-]*\)".*/\1/p' | head -n 1)
  [ -n "$sid" ] || sid=${CLAUDE_CODE_SESSION_ID:-}
  st="${CLAUDE_JOB_DIR%/}/state.json"
  if [ -n "$sid" ] && grep -q '"sessionId"' "$st" 2>/dev/null && ! grep -qF "\"$sid\"" "$st" 2>/dev/null; then
    exit 0
  fi
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
# inoltra l'OSC. Lo stato va in ~/.cache/herdr-stato/<job id>, che l'aggancio di Volta legge all'apertura
# (una parola sola), e sul tty di ogni claude attach <job id> di questa macchina. Un attach via ssh mostra la
# sessione di un'altra macchina: lì scrive l'hook di là.
job=${CLAUDE_JOB_DIR:-}
job=${job%/}
job=${job##*/}
case "$job" in '' | *[!0-9A-Za-z_-]*) exit 0 ;; esac
[ -n "${HOME:-}" ] || exit 0
cache="$HOME/.cache/herdr-stato"
mkdir -p "$cache" 2>/dev/null || exit 0
# Ordine (#5587): PostToolUse working è async e può arrivare dopo PermissionRequest blocked. Sotto un
# lucchetto (mkdir, rotto dopo ~1 s) l'ora si confronta con l'ultima, che sta a parte in <job>.ora: uno stato
# più vecchio si scarta, uno uguale aggiorna solo l'ora.
lucchetto="$cache/$job.lock"
n=0
until mkdir "$lucchetto" 2>/dev/null; do
  n=$((n + 1))
  if [ "$n" -ge 20 ]; then
    rmdir "$lucchetto" 2>/dev/null
    mkdir "$lucchetto" 2>/dev/null
    break
  fi
  sleep 0.05 2>/dev/null || sleep 1
done
ultima=$(cat "$cache/$job.ora" 2>/dev/null)
case "$ultima" in '' | *[!0-9]*) ultima=0 ;; esac
if [ "$ora" -lt "$ultima" ] 2>/dev/null; then
  rmdir "$lucchetto" 2>/dev/null
  exit 0
fi
prima=$(cat "$cache/$job" 2>/dev/null)
printf '%s\n' "$ora" > "$cache/$job.ora.$$" 2>/dev/null && mv -f "$cache/$job.ora.$$" "$cache/$job.ora" 2>/dev/null
rm -f "$cache/$job.ora.$$" 2>/dev/null
if [ "$prima" = "$1" ]; then
  rmdir "$lucchetto" 2>/dev/null
  exit 0
fi
printf '%s\n' "$1" > "$cache/$job.$$" 2>/dev/null && mv -f "$cache/$job.$$" "$cache/$job" 2>/dev/null
rm -f "$cache/$job.$$" 2>/dev/null
rmdir "$lucchetto" 2>/dev/null
# Sul tty degli attach scrive un processo staccato, così l'hook esce subito. Il processo aspetta che claude
# attach sia fermo (tempo CPU invariato per ~100 ms, al massimo ~1 s): l'OSC non deve cadere dentro una
# sequenza che attach sta disegnando. Scrive solo se il file dice ancora questo stato: in una raffica vince
# l'ultimo. Il confronto è sul file dello stato e non su <job>.ora: uno stato uguale aggiorna l'ora senza
# lanciare un altro processo, e col confronto sull'ora quello stato non arriverebbe mai al tty.
dev=${HERDR_STATO_DEV:-/dev}
cpu() {
  if [ -r "/proc/$1/stat" ]; then
    sed 's/^.*) //' "/proc/$1/stat" 2>/dev/null | awk '{ print $12 + $13 }'
  else
    ps -o time= -p "$1" 2>/dev/null | tr -d ' '
  fi
}
(
  ps -Ao pid=,tty=,args= 2>/dev/null | {
    visti=" "
    while read -r pid t a; do
      case "$t" in '' | '?' | '??') continue ;; esac
      case "$visti" in *" $t "*) continue ;; esac
      case " $a " in *" attach $job "* | *" attach "*" $job "*) ;; *) continue ;; esac
      case "$a" in *claude*) ;; *) continue ;; esac
      case " $a " in *" ssh "* | */ssh\ *) continue ;; esac
      visti="$visti$t "
      c=$(cpu "$pid")
      fermo=0
      for _ in 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20; do
        sleep 0.05 2>/dev/null || break
        d=$(cpu "$pid")
        if [ "$d" = "$c" ]; then
          fermo=$((fermo + 1))
          [ "$fermo" -ge 2 ] && break
        else
          fermo=0
          c=$d
        fi
      done
      [ "$(cat "$cache/$job" 2>/dev/null)" = "$1" ] || exit 0
      # >> e non >: su un tty è uguale, e nel banco un file finto conta le scritture invece di troncarle.
      { printf '%s' "$seq" >> "$dev/$t"; } 2>/dev/null
    done
  }
) </dev/null >/dev/null 2>&1 &
exit 0
