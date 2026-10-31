# gate-lucchetto.sh: un solo gate completo per macchina (#4360).
#
# Due tests/verifica-allineamento.sh in parallelo sulla stessa macchina si pestano: il 30-31/10/2026
# sul MacBook Air hanno dato rossi (T22 di test_todo, SM04 di test_schede_mac) che da soli passano.
# Il gate prende il lucchetto all'avvio. Il secondo aspetta in fila e dice chi lo tiene.
#
# Il lucchetto è una cartella: mkdir è atomico su macOS, Linux e Windows (Git Bash). Dentro, il file
# "chi" dice pid, ora di partenza e repository del gate che lo tiene. Un lucchetto il cui pid non
# gira più (gate ucciso con kill -9, Mac spento) si toglie da solo al primo gate che lo trova.
#
# Uso (dentro uno script bash):
#   source bin/gate-lucchetto.sh
#   gate_lucchetto_prendi "$percorso" "descrizione di chi lo prende" || exit 1
#   trap gate_lucchetto_lascia EXIT
#
# ARTURO_GATE_ATTESA: secondi massimi di attesa (predefinito 5400, un'ora e mezza: un gate completo
# dura fra 20 e 50 minuti). Scaduti, il gate esce rosso e dice chi tiene il lucchetto.
# ARTURO_GATE_PASSO: secondi fra un controllo e l'altro (predefinito 15).

GATE_LUCCHETTO_DIR=""

gate_lucchetto_prendi() {
  local dir="$1" descrizione="${2:-}" attesa="${ARTURO_GATE_ATTESA:-5400}" passo="${ARTURO_GATE_PASSO:-15}"
  local inizio=$SECONDS detto="" chi pid
  mkdir -p "$(dirname "$dir")"
  while ! mkdir "$dir" 2>/dev/null; do
    chi=$(cat "$dir/chi" 2>/dev/null || true)
    pid=${chi%%,*}
    if [[ "$pid" =~ ^[0-9]+$ ]] && ! kill -0 "$pid" 2>/dev/null; then
      echo "LUCCHETTO: il gate che lo teneva non gira più ($chi): tolgo il lucchetto rimasto" >&2
      rm -rf "$dir"
      continue
    fi
    if [[ -z "$chi" ]] && [[ -n "$(find "$dir" -maxdepth 0 -mmin +1 2>/dev/null)" ]]; then
      # Una cartella senza "chi" da oltre un minuto: un gate morto fra mkdir e la scrittura.
      echo "LUCCHETTO: lucchetto senza proprietario da oltre un minuto: lo tolgo" >&2
      rm -rf "$dir"
      continue
    fi
    if [[ -n "$chi" && "$chi" != "$detto" ]]; then
      echo "LUCCHETTO: un altro gate completo gira su questa macchina (pid ${chi}). Aspetto che finisca." >&2
      detto=$chi
    fi
    if (( SECONDS - inizio >= attesa )); then
      echo "FAIL: dopo ${attesa}s il lucchetto del gate è ancora preso (pid ${chi:-sconosciuto}). Se quel gate è fermo, toglilo: rm -rf $dir" >&2
      return 1
    fi
    sleep "$passo"
  done
  printf '%s, dalle %s, %s\n' "$$" "$(date +%H:%M:%S)" "$descrizione" > "$dir/chi"
  GATE_LUCCHETTO_DIR=$dir
  [[ -z "$detto" ]] || echo "LUCCHETTO: preso dopo $(( SECONDS - inizio ))s di attesa" >&2
  return 0
}

gate_lucchetto_lascia() {
  # Toglie il lucchetto solo se è ancora suo: mai quello di un altro gate.
  local dir="$GATE_LUCCHETTO_DIR" chi
  [[ -n "$dir" ]] || return 0
  chi=$(cat "$dir/chi" 2>/dev/null || true)
  [[ "${chi%%,*}" == "$$" ]] && rm -rf "$dir"
  GATE_LUCCHETTO_DIR=""
  return 0
}
