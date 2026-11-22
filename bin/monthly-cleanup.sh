#!/usr/bin/env bash
# monthly-cleanup.sh: pulizia mensile dei residui di Claude Code e delle cache, più alcuni segnali.
#
# Uso:
#   bash ~/.claude/bin/monthly-cleanup.sh            # pulisce
#   bash ~/.claude/bin/monthly-cleanup.sh --prova    # elenca cosa farebbe, senza toccare niente
#
# Cosa fa:
#   1. cancella le cartelle di ~/.claude/tasks ferme da oltre 180 giorni
#   2. cancella i file di ~/.claude/shell-snapshots più vecchi di 180 giorni
#   3. cancella i file di ~/.claude/paste-cache più vecchi di 30 giorni
#   4. svuota le cache dei package manager con i loro comandi (uv, npm, brew, pip), mai con rm
#   5. facoltativo: sposta in un archivio i file sciolti e fermi da 60 giorni nella cartella dei progetti
#   6. segnala, senza agire: disco quasi pieno, node_modules di progetti fermi, LaunchAgent non caricati
#
# Impostazioni (variabili d'ambiente, tutte facoltative):
#   PULIZIA_CACHE=0                    salta il punto 4
#   PULIZIA_CARTELLA_PROGETTI=<dir>    attiva il punto 5 e la nota sui node_modules per quella cartella.
#                                      I file si spostano in <dir>/_archivio/<AAAA-MM>/, mai cancellati.
#   PULIZIA_PREFISSI_LAUNCHAGENT="com.esempio. com.altro."
#                                      solo macOS: segnala i LaunchAgent con quei prefissi che hanno il
#                                      file .plist ma non sono caricati. Vuota: controllo saltato.
#   PULIZIA_TETTO_SEGNALI=15           secondi massimi per ogni comando di sistema del punto 6 (df, tmutil,
#                                      launchctl). Scaduti, il segnale si salta e la pulizia finisce.
#
# Cron mensile suggerito (il primo del mese alle 4):
#   0 4 1 * * bash "$HOME/.claude/bin/monthly-cleanup.sh" >> "$HOME/.claude/data/logs/monthly-cleanup.log" 2>&1

set -u
PROVA=0
case "${1:-}" in
  --prova) PROVA=1 ;;
  "") ;;
  *) echo "Uso: $0 [--prova]" >&2; exit 2 ;;
esac
TS=$(date +%Y-%m-%d_%H-%M)
echo "=== Pulizia mensile — $TS$( [ "$PROVA" = 1 ] && echo ' (prova: niente viene toccato)') ==="

# Conta e (fuori da --prova) cancella ciò che find trova. Argomenti: etichetta, poi gli argomenti di find.
pulisci() {
  local etichetta="$1"; shift
  local n
  n=$(find "$@" 2>/dev/null | wc -l | tr -d ' ')
  if [ "$n" -eq 0 ]; then echo "[$TS] $etichetta: niente da togliere"; return 0; fi
  if [ "$PROVA" = 1 ]; then echo "[$TS] $etichetta: da togliere $n"; return 0; fi
  find "$@" -exec rm -rf {} + 2>/dev/null
  echo "[$TS] $etichetta: tolti $n"
}

# Lancia un comando di sistema con un tetto di secondi e ne stampa l'uscita. Se il tetto scade, esce 124.
# I segnali del punto 6 interrogano servizi del sistema: durante un backup di Time Machine verso un disco
# di rete, tmutil listlocalsnapshots può restare fermo per minuti. Il 22/11/2026 ha tenuto ferma la prova
# a vuoto oltre i 120 secondi del banco Z06 (#6390). Un segnale non deve bloccare la pulizia.
# PULIZIA_TETTO_SEGNALI: secondi massimi per ogni comando di sistema (predefinito 15).
con_tetto() {
  local tetto=$(( ${PULIZIA_TETTO_SEGNALI:-15} * 10 )) out pid n=0 rc
  out=$(mktemp "${TMPDIR:-/tmp}/pulizia-mensile.XXXXXX") || return 1
  "$@" >"$out" 2>/dev/null </dev/null &
  pid=$!
  while kill -0 "$pid" 2>/dev/null; do
    if [ "$n" -ge "$tetto" ]; then
      # Un comando fermo in attesa di un servizio può ignorare TERM: dopo un attimo arriva KILL.
      kill "$pid" 2>/dev/null; sleep 0.2; kill -9 "$pid" 2>/dev/null
      wait "$pid" 2>/dev/null; rm -f "$out"; return 124
    fi
    sleep 0.1; n=$((n+1))
  done
  wait "$pid"; rc=$?
  cat "$out"; rm -f "$out"
  return "$rc"
}

C="$HOME/.claude"
[ -d "$C/tasks" ] && pulisci "tasks oltre 180 giorni" "$C/tasks" -mindepth 1 -maxdepth 1 -type d -mtime +180
[ -d "$C/shell-snapshots" ] && pulisci "shell-snapshots oltre 180 giorni" "$C/shell-snapshots" -type f -mtime +180
[ -d "$C/paste-cache" ] && pulisci "paste-cache oltre 30 giorni" "$C/paste-cache" -type f -mtime +30

# 4. Cache dei package manager, con i loro comandi
if [ "${PULIZIA_CACHE:-1}" != 0 ]; then
  echo "[$TS] --- cache dei package manager ---"
  for t in uv npm brew pip; do
    case "$t" in
      uv)   command -v uv >/dev/null 2>&1   || continue; cmd="uv cache clean" ;;
      npm)  command -v npm >/dev/null 2>&1  || continue; cmd="npm cache clean --force" ;;
      brew) command -v brew >/dev/null 2>&1 || continue; cmd="brew cleanup --prune=all" ;;
      pip)  python3 -m pip --version >/dev/null 2>&1 || continue; cmd="python3 -m pip cache purge" ;;
    esac
    if [ "$PROVA" = 1 ]; then echo "[$TS] lancerei: $cmd"; else $cmd 2>&1 | tail -1; fi
  done
fi

# 5. Facoltativo: file sciolti nella cartella dei progetti, archiviati (mv) e mai cancellati
P="${PULIZIA_CARTELLA_PROGETTI:-}"
P="${P/#\~/$HOME}"
if [ -n "$P" ]; then
  if [ -d "$P" ]; then
    DEST="$P/_archivio/$(date +%Y-%m)"
    MOSSI=0
    while IFS= read -r f; do
      [ -n "$f" ] || continue
      if [ "$PROVA" = 1 ]; then echo "[$TS] sposterei: $f"; MOSSI=$((MOSSI+1)); continue; fi
      mkdir -p "$DEST"
      mv -n "$f" "$DEST/" 2>/dev/null && MOSSI=$((MOSSI+1))
    done <<EOF
$(find "$P" -maxdepth 1 -type f ! -name '.*' ! -name 'CLAUDE.md' ! -name 'CLAUDE.local.md' ! -name 'AGENTS.md' \
  ! -name 'README*' ! -name 'LICENSE*' -mtime +60 2>/dev/null)
EOF
    # Non modificato da 60 giorni non vuol dire non usato: CLAUDE.md e AGENTS.md sono le istruzioni della cartella
    # contenitore, README e LICENSE la descrivono. Fino al 22/11/2026 finivano in _archivio (revisione del 20/11, bug 12).
    echo "[$TS] cartella progetti: file sciolti: $MOSSI $( [ "$PROVA" = 1 ] && echo 'da archiviare' || echo "archiviati in $DEST")"
  else
    echo "[$TS] PULIZIA_CARTELLA_PROGETTI punta a una cartella che non esiste: $P"
  fi
fi

# 6. Segnali, non azioni: qui decide una persona
USO=$(con_tetto df -P "$HOME" | awk 'NR==2 {gsub(/%/,"",$5); print $5}')
if [ "${USO:-0}" -ge 85 ] 2>/dev/null; then echo "[$TS] DISCO QUASI PIENO: ${USO}% usato. Serve una decisione: cosa togliere?"; fi

if command -v tmutil >/dev/null 2>&1; then
  if ELENCO=$(con_tetto tmutil listlocalsnapshots /); then
    SNAP=$(printf '%s\n' "$ELENCO" | grep -c 'com.apple.TimeMachine')
    if [ "${SNAP:-0}" -gt 0 ]; then echo "[$TS] NOTA: $SNAP istantanee locali di Time Machine trattengono lo spazio appena liberato"; fi
  elif [ $? -eq 124 ]; then
    echo "[$TS] NOTA: Time Machine non ha risposto entro ${PULIZIA_TETTO_SEGNALI:-15} secondi (forse un backup in corso): istantanee non contate"
  fi
fi

if [ -n "$P" ] && [ -d "$P" ]; then
  NM=$(find "$P" -maxdepth 3 -name node_modules -type d -mtime +90 2>/dev/null | wc -l | tr -d ' ')
  if [ "${NM:-0}" -gt 0 ]; then echo "[$TS] NOTA: $NM cartelle node_modules in progetti fermi da oltre 90 giorni (non le tocco)"; fi
fi

# LaunchAgent con il file .plist ma non caricati: un servizio fermo che nessuno segnala
if [ -n "${PULIZIA_PREFISSI_LAUNCHAGENT:-}" ] && command -v launchctl >/dev/null 2>&1; then
  CARICATI=$(con_tetto launchctl list | awk '{print $3}')
  ORFANI=""
  for pref in $PULIZIA_PREFISSI_LAUNCHAGENT; do
    for p in "$HOME/Library/LaunchAgents/$pref"*.plist; do
      [ -e "$p" ] || continue
      LBL=$(basename "$p" .plist)
      printf '%s\n' "$CARICATI" | grep -qxF "$LBL" || ORFANI="$ORFANI $LBL"
    done
  done
  if [ -n "$ORFANI" ]; then
    echo "[$TS] LAUNCHAGENT NON CARICATI (il .plist c'è, il servizio no):$ORFANI"
    echo "[$TS]   per caricarne uno: launchctl bootstrap gui/\$(id -u) ~/Library/LaunchAgents/<nome>.plist"
  fi
fi

echo "[$TS] Pulizia mensile finita"
