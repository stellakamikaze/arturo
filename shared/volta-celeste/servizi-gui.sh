#!/bin/sh
# Servizi di Claude e di herdr-core nati nella sessione grafica del Mac, non da ssh (solo macOS, 9/11/2026).
#
#   servizi-gui.sh               herdr-core da LaunchAgent; il gestore delle sessioni di Claude in una
#                                finestra del Terminale (vedi "Documenti" qui sotto)
#   servizi-gui.sh --launchd     anche il gestore da LaunchAgent: solo dopo aver dato a `claude` l'accesso
#                                a Documenti (Impostazioni di Sistema, Privacy e sicurezza, File e cartelle)
#   servizi-gui.sh --rimuovi     ferma e toglie i LaunchAgent
#
# Perché. Il gestore delle sessioni in background (`claude daemon`) e herdr-core partono su richiesta
# dal primo programma che li cerca. Se il primo arriva da ssh (Herdr su un altro Mac, /teletrasporto,
# `claude --bg` o `claude attach` da remoto) partono nella sessione di ssh, che non apre il portachiavi:
# ogni sessione che ne nasce risponde "Not logged in" finché non vengono riavviati. Provato il 9/11/2026
# su un secondo Mac: gestore e herdr-core nati da ssh, Claude senza login sia in background sia da Herdr.
#
# Documenti. Nato da launchd il gestore ha il login, ma macOS non gli dà Documenti: una sessione con la
# cartella in ~/Documents muore all'avvio ("exit 1 before init", EINTR sulla cartella). Il Terminale
# quell'accesso ce l'ha, e lo passa a quello che lancia: per questo il gestore va in una sua finestra
# del Terminale, finché `claude` non ha il permesso suo. La finestra va lasciata aperta (si può ridurre).
#
# Prima di lanciarlo: `claude daemon stop --any --keep-workers` (le sessioni staccate restano vive) e
# `hc server stop`. Un `claude attach` vivo da un altro Mac fa ripartire il gestore da ssh appena si
# ferma: va messo in pausa (kill -STOP) per i pochi secondi del cambio, poi ripreso (kill -CONT).
#
# Variabili per i banchi: SERVIZI_AGENTI (cartella dei LaunchAgent), SERVIZI_NO_LAUNCHCTL=1 (niente
# launchctl e niente Terminale).
set -eu

PREFISSO=org.stellakamikaze.arturo
agenti=${SERVIZI_AGENTI:-$HOME/Library/LaunchAgents}
log=$HOME/Library/Logs/arturo
dominio=gui/$(id -u)
claude=$HOME/.local/bin/claude
core=$HOME/.local/bin/herdr-core
say() { printf '%s\n' "$*"; }

[ "$(uname -s)" = Darwin ] || { say "SERVIZI GUI NO: servono solo su macOS."; exit 0; }

prova() { [ "${SERVIZI_NO_LAUNCHCTL:-}" = 1 ]; }
lc() { prova || launchctl "$@"; }

# plist <nome> <keepalive true|false> <programma> <argomento...>
plist() {
  nome=$1 vivo=$2; shift 2
  f=$agenti/$PREFISSO.$nome.plist
  {
    printf '%s\n' '<?xml version="1.0" encoding="UTF-8"?>' \
      '<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">' \
      '<!-- Scritto da servizi-gui.sh di Arturo: lo avvia la sessione grafica, non ssh. -->' \
      '<plist version="1.0">' '<dict>' \
      "  <key>Label</key><string>$PREFISSO.$nome</string>" \
      '  <key>ProgramArguments</key>' '  <array>'
    for a in "$@"; do printf '    <string>%s</string>\n' "$a"; done
    printf '%s\n' '  </array>' \
      '  <key>RunAtLoad</key><true/>' \
      "  <key>KeepAlive</key><$vivo/>" \
      '  <key>ProcessType</key><string>Interactive</string>' \
      "  <key>WorkingDirectory</key><string>$HOME</string>" \
      '  <key>EnvironmentVariables</key>' '  <dict>' \
      "    <key>PATH</key><string>$HOME/.local/bin:$HOME/.local/node/bin:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin</string>" \
      '  </dict>' \
      "  <key>StandardOutPath</key><string>$log/$nome.log</string>" \
      "  <key>StandardErrorPath</key><string>$log/$nome.log</string>" \
      '</dict>' '</plist>'
  } > "$f.tmp"
  mv "$f.tmp" "$f"
  lc bootout "$dominio/$PREFISSO.$nome" 2>/dev/null || true
  lc bootstrap "$dominio" "$f"
  say "SERVIZI GUI: $PREFISSO.$nome avviato da $dominio"
}

if [ "${1:-}" = --rimuovi ]; then
  for nome in claude-daemon herdr-core; do
    lc bootout "$dominio/$PREFISSO.$nome" 2>/dev/null || true
    rm -f "$agenti/$PREFISSO.$nome.plist"
    say "SERVIZI GUI: $PREFISSO.$nome tolto"
  done
  exit 0
fi

mkdir -p "$agenti" "$log"
# herdr-core serve si passa da solo a launchd (--hc-launchd) ed esce 0: niente KeepAlive, o launchd
# lo rilancerebbe ogni dieci secondi.
if [ -x "$core" ]; then plist herdr-core false "$core" serve; else say "SERVIZI GUI: herdr-core non trovato in $core, saltato"; fi

[ -x "$claude" ] || { say "SERVIZI GUI: claude non trovato in $claude, saltato"; exit 0; }
if [ "${1:-}" = --launchd ]; then
  plist claude-daemon true "$claude" daemon run
else
  rm -f "$agenti/$PREFISSO.claude-daemon.plist"
  prova || osascript -e "tell application \"Terminal\" to do script \"exec '$claude' daemon run\"" >/dev/null
  say "SERVIZI GUI: gestore delle sessioni avviato in una finestra del Terminale (lasciala aperta)"
fi
