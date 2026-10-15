#!/usr/bin/env bash
# bgjob.sh: lavoro lungo staccato dalla sessione, con la fine scritta su file.
#
#   bgjob.sh start <nome> -- <comando> [argomenti...]
#   bgjob.sh status <nome|cartella>     # in corso / finito exit=N / morto senza esito
#   bgjob.sh stop <nome|cartella>       # SIGTERM al gruppo di processi del job
#
# Ogni job ha una cartella in ~/.claude/data/logs/bgjobs/<nome>-<AAAAMMGG-HHMMSS>/ con:
#   cmd    il comando lanciato        log   stdout+stderr
#   pid    PID del runner             start ora di avvio del PID, contro il riuso del PID
#   exit   marker di fine con l'exit code. Lo scrive il runner, quindi manca se il runner muore.
#
# Il comando gira come argv, senza eval: per pipe o redirezioni usa  -- bash -c '...'.
# Lo stato si legge dal marker e da kill -0 sul PID salvato. Mai pgrep -f: trova anche chi osserva.
# Exit di status: 0 finito con exit 0, 1 finito con exit diverso, 2 in corso,
# 3 morto senza esito, 4 uso sbagliato.
#
# Ora di avvio del PID: `ps -o lstart=` su macOS e Linux. Il ps di Git Bash (Windows) non ha -o:
# lì si legge il campo starttime di /proc/<pid>/stat. Se nessuna delle due vie risponde, il
# controllo si riduce a kill -0 (un PID riusato da un altro processo sembrerebbe ancora vivo).
# Su macOS il runner tiene sveglio il computer con caffeinate finché il job gira.
set -u

BASE="${BGJOB_DIR:-$HOME/.claude/data/logs/bgjobs}"
SELF="$(cd "$(dirname "$0")" && pwd)/$(basename "$0")"
PROC="${BGJOB_PROC:-/proc}"   # variabile solo per il banco, che simula il /proc di Git Bash

die() { printf 'bgjob: %s\n' "$1" >&2; exit 4; }

avvio_pid() {  # stampa un'impronta dell'ora di avvio del PID, vuota se non si legge
  local pid="$1" v s
  v=$(ps -o lstart= -p "$pid" 2>/dev/null)
  if [[ -n "${v//[[:space:]]/}" ]]; then printf 'ps:%s\n' "$v"; return 0; fi
  if [[ -r "$PROC/$pid/stat" ]]; then
    s=$(cat "$PROC/$pid/stat" 2>/dev/null)
    s=${s##*) }   # il nome del processo sta fra parentesi e può contenere spazi
    # dopo «) » il primo campo è il 3 di stat: starttime (campo 22) è il ventesimo
    set -- $s
    [[ $# -ge 20 ]] && { printf 'proc:%s\n' "${20}"; return 0; }
  fi
  return 0
}

resolve() {  # nome o cartella -> cartella del job (la più recente per quel nome)
  local ref="$1" d
  if [[ -d "$ref" && -f "$ref/pid" ]]; then printf '%s\n' "$ref"; return 0; fi
  [[ "$ref" =~ ^[A-Za-z0-9._-]+$ ]] || die "nome non valido: $ref"
  d=$(ls -1d "$BASE/$ref"-2[0-9]*-[0-9]* 2>/dev/null | sort | tail -n 1)
  [[ -n "$d" ]] || die "nessun job con nome $ref in $BASE"
  printf '%s\n' "$d"
}

alive() {  # vero se il PID salvato vive ed è lo stesso processo avviato dal job
  local dir="$1" pid start now
  pid=$(cat "$dir/pid" 2>/dev/null) || return 1
  [[ "$pid" =~ ^[0-9]+$ ]] || return 1
  kill -0 "$pid" 2>/dev/null || return 1
  start=$(cat "$dir/start" 2>/dev/null)
  now=$(avvio_pid "$pid")
  [[ -z "$start" || "$start" == "$now" ]]
}

cmd_start() {
  local name="${1:-}"; shift || true
  [[ "$name" =~ ^[A-Za-z0-9._-]+$ ]] || die "serve un nome [A-Za-z0-9._-]: bgjob.sh start <nome> -- <comando>"
  [[ "${1:-}" == "--" ]] || die "manca -- prima del comando"
  shift
  [[ $# -gt 0 ]] || die "manca il comando dopo --"

  local dir="$BASE/$name-$(date +%Y%m%d-%H%M%S)"
  [[ -e "$dir" ]] && die "cartella già esistente: $dir (rilancia fra un secondo)"
  mkdir -p "$dir" || die "non riesco a creare $dir"
  printf '%q ' "$@" > "$dir/cmd"; printf '\n' >> "$dir/cmd"

  # Runner: esegue il comando, poi scrive il marker in modo atomico.
  # set -m dà al runner un gruppo di processi suo, così stop ferma anche i figli.
  set -m
  nohup bash -c '
    dir=$1; shift
    command -v caffeinate >/dev/null 2>&1 && caffeinate -i -w $$ &
    "$@"
    rc=$?
    printf "\n[bgjob] fine %s exit=%s\n" "$(date "+%F %T")" "$rc"
    printf "%s\n" "$rc" > "$dir/exit.tmp" && mv "$dir/exit.tmp" "$dir/exit"
  ' bgjob-runner "$dir" "$@" > "$dir/log" 2>&1 < /dev/null &
  local pid=$!
  set +m
  printf '%s\n' "$pid" > "$dir/pid"
  avvio_pid "$pid" > "$dir/start"

  printf 'job:     %s\n' "$dir"
  printf 'pid:     %s\n' "$pid"
  printf 'log:     %s/log\n' "$dir"
  printf 'marker:  %s/exit\n' "$dir"
  printf 'stato:   bash %s status %s\n' "$SELF" "$dir"
  printf 'attesa:  until test -f %s/exit || ! kill -0 %s 2>/dev/null; do sleep 30; done; bash %s status %s\n' \
    "$dir" "$pid" "$SELF" "$dir"
}

cmd_status() {
  local dir rc pid
  dir=$(resolve "${1:-}") || exit 4
  pid=$(cat "$dir/pid" 2>/dev/null)
  if [[ -f "$dir/exit" ]]; then
    rc=$(cat "$dir/exit")
    printf 'finito exit=%s · pid %s · %s\n' "$rc" "$pid" "$dir"
    [[ "$rc" == "0" ]] && return 0 || return 1
  fi
  if alive "$dir"; then
    printf 'in corso · pid %s · %s\n' "$pid" "$dir"
    return 2
  fi
  # ricontrolla il marker: il runner può averlo scritto fra le due letture
  if [[ -f "$dir/exit" ]]; then cmd_status "$dir"; return $?; fi
  printf 'morto senza esito · pid %s non è più il processo del job e manca il marker · %s\n' "$pid" "$dir"
  return 3
}

cmd_stop() {
  local dir pid
  dir=$(resolve "${1:-}") || exit 4
  pid=$(cat "$dir/pid")
  if alive "$dir"; then
    kill -TERM -- "-$pid" 2>/dev/null || kill -TERM "$pid"
    printf 'SIGTERM inviato al gruppo %s\n' "$pid"
  else
    printf 'niente da fermare\n'
  fi
  cmd_status "$dir"
}

case "${1:-}" in
  start)  shift; cmd_start "$@" ;;
  status) shift; cmd_status "$@" ;;
  stop)   shift; cmd_stop "$@" ;;
  _avvio) shift; avvio_pid "${1:-}" ;;   # per il banco: l'impronta di avvio di un PID
  *) sed -n '2,6p' "$0" >&2; exit 4 ;;
esac
