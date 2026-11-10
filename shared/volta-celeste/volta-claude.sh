#!/bin/sh
# volta-claude: il comando claude di Volta Celeste (#5172 passo 2).
# In un terminale vero la sessione nasce in background (claude --bg) e si apre qui con claude attach:
# così Volta la apre da qualunque macchina anche mentre lavora, e chiudere il terminale non la ferma.
# Il resto passa a claude com'è: i sottocomandi (agents, attach, mcp, ...), -p, --version, e chi lancia
# claude da uno script o da un'altra sessione.
#
# Via di fuga: CLAUDE_QUI=1 claude apre la sessione qui, interattiva, come prima.
# Nei terminali di Herdr (HC_TERMINAL_ID) la sessione resta interattiva finché Volta non legge lo stato
# delle sessioni in background (passo 4): l'hook herdr-stato.sh scrive lo stato nel terminale della sessione,
# e una sessione in background non ce l'ha.
# Una sessione in background prende l'ambiente dal servizio di Claude, non da questa shell: una variabile
# esportata solo qui non arriva. Chi ne ha bisogno usa CLAUDE_QUI=1.
#
# Lo installa installa-herdr.sh in ~/.config/herdr-app/volta-claude; il blocco nel file di avvio della
# shell (nascita.sh) chiama questo file. Per i banchi: VOLTA_CLAUDE_BIN (il claude da lanciare) e
# VOLTA_CLAUDE_TTY=1 (fa finta che il terminale sia vero).

bin=${VOLTA_CLAUDE_BIN:-claude}

qui_interattiva() { exec "$bin" "$@"; }

[ "${CLAUDE_QUI:-0}" = 1 ] && qui_interattiva "$@"
[ -n "${CLAUDECODE:-}" ] && qui_interattiva "$@"
[ -n "${HC_TERMINAL_ID:-}" ] && qui_interattiva "$@"
if [ "${VOLTA_CLAUDE_TTY:-0}" != 1 ]; then
  { [ -t 0 ] && [ -t 1 ]; } || qui_interattiva "$@"
fi

# I sottocomandi di claude 2.1 (claude --help, Commands) restano com'erano.
case "${1:-}" in
  agents | attach | auth | auto-mode | config | doctor | gateway | import | install | logs | mcp | migrate-installer | \
  plugin | plugins | purge | respawn | rm | setup-token | stop | kill | ultrareview | update | upgrade)
    qui_interattiva "$@" ;;
esac

# Le opzioni che non hanno senso in background, o che lo sono già.
# --resume senza id apre la scelta della sessione, che è interattiva; con l'id va in background.
senza_id=""
for a in "$@"; do
  if [ -n "$senza_id" ]; then
    case "$a" in -*) qui_interattiva "$@" ;; esac
    senza_id=""
  fi
  case "$a" in
    -p | --print | -v | --version | -h | --help | --bg | --background | -c | --continue | \
    --cloud | --cloud=* | --desktop | --teleport | --teleport=* | --remote-control | --remote-control=* | \
    --tmux | --tmux=* | --output-format | --output-format=* | --input-format | --input-format=* | --ide)
      qui_interattiva "$@" ;;
    -r | --resume) senza_id=1 ;;
  esac
done
[ -n "$senza_id" ] && qui_interattiva "$@"

uscita=$("$bin" --bg "$@" 2>&1)
rc=$?
id=$(printf '%s\n' "$uscita" | sed -n 's/^.*claude attach \([0-9A-Za-z-]*\).*$/\1/p' | head -n 1)
if [ $rc -ne 0 ] || [ -z "$id" ]; then
  if [ $rc -eq 0 ]; then
    # È partita ma non ha stampato l'id che conosco: niente seconda sessione, mostro cosa ha detto.
    printf '%s\n' "$uscita"
    printf 'Volta: la sessione è partita in background, ma non ho letto il suo id. claude agents la elenca.\n' >&2
    exit 0
  fi
  # La prima riga che dice perché: "Starting background service" la stampa claude a ogni avvio del servizio.
  motivo=$(printf '%s\n' "$uscita" | grep -v '^Starting background service' | sed -n '/./{p;q;}')
  printf 'Volta: la sessione non parte in background (%s). La apro qui, come prima.\n' "$motivo" >&2
  qui_interattiva "$@"
fi

"$bin" attach "$id"
rc=$?
printf 'La sessione %s continua in background: claude attach %s la riapre qui.\n' "$id" "$id" >&2
exit $rc
