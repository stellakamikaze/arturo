#!/usr/bin/env bash
# test_gate_run.sh: banco di bin/gate-run.sh. Un gate che decide se un altro gate vale
# deve avere un banco suo.
#
#   caso 1  veleno verde (exit 0)                  -> exit 2: il gate non discrimina
#   caso 2  veleno rosso senza il marcatore atteso -> exit 2: rosso per il motivo sbagliato
#   caso 3  veleno giusto, gate verde              -> exit 0
#   caso 4  veleno giusto, gate rosso              -> exit 1
#   casi 5-7 i guasti del banco, exit 3: sorgente assente, veleno che scrive fuori da
#            veleno-* in VELENO_DIR, veleno che scrive nella cartella corrente
#   caso 8  veleno che cancella un file della cartella corrente -> exit 3 (review del 7/11/2026, finding 93)
#   casi 9-10 --pass: gate verde col marcatore -> exit 0; senza il marcatore -> exit 1
#
# Gira in una cartella temporanea quieta: gate-run.sh guarda i file cambiati nella
# cartella corrente durante il veleno. GATE_RUN=<path> prova un'altra versione.
set -u
GR="${GATE_RUN:-$(cd "$(dirname "$0")/.." && pwd)/bin/gate-run.sh}"
DIR="$(mktemp -d "${TMPDIR:-/tmp}/test-gate-run.XXXXXX")"
cd "$DIR" || exit 3
pass=0; fail=0; CASI=0
OUTD="$(mktemp -d "${TMPDIR:-/tmp}/test-gate-run-out.XXXXXX")"  # esiti fuori dalla cartella sorvegliata
caso() { # nome | exit atteso | argomenti di gate-run.sh...
  local nome="$1" atteso="$2"; shift 2; CASI=$((CASI+1))
  bash "$GR" "$@" > "$OUTD/out.txt" 2>&1; echo $? > "$OUTD/rc.txt"
  local rc; rc="$(cat "$OUTD/rc.txt")"
  if [ "$rc" = "$atteso" ]; then pass=$((pass+1)); echo "[OK] $nome (exit $rc)"
  else fail=$((fail+1)); echo "[X]  $nome: exit $rc, atteso $atteso"; tail -5 "$OUTD/out.txt" | sed 's/^/     /'; fi
}
caso "veleno verde"                   2 --poison 'true' --expect 'ROTTO' -- true
caso "veleno rosso, marcatore sbagliato" 2 --poison 'echo altro; exit 1' --expect 'ROTTO' -- true
caso "veleno giusto, gate verde"      0 --poison 'echo ROTTO; exit 1' --expect 'ROTTO' -- true
caso "veleno giusto, gate rosso"      1 --poison 'echo ROTTO; exit 1' --expect 'ROTTO' -- false
caso "sorgente assente"               3 --source "$DIR/non-esiste" --poison 'echo ROTTO; exit 1' --expect 'ROTTO' -- true
caso "veleno scrive fuori da veleno-*" 3 --poison 'touch "$VELENO_DIR/altro"; echo ROTTO; exit 1' --expect 'ROTTO' -- true
caso "veleno scrive nella cartella"    3 --poison 'touch ./x; echo ROTTO; exit 1' --expect 'ROTTO' -- true
rm -f ./x
echo sorgente > ./sorgente.txt
caso "veleno cancella un file"         3 --poison 'rm -f sorgente.txt; echo ROTTO; exit 1' --expect 'ROTTO' -- true
rm -f ./sorgente.txt
caso "gate verde col marcatore"        0 --pass 'TUTTO-OK' --poison 'echo ROTTO; exit 1' --expect 'ROTTO' -- echo TUTTO-OK
caso "gate verde senza marcatore"      1 --pass 'TUTTO-OK' --poison 'echo ROTTO; exit 1' --expect 'ROTTO' -- true
cd / && rm -rf "$DIR" "$OUTD"
echo "totale casi: $CASI · verdi: $pass · rossi: $fail"
[ "$pass" -eq "$CASI" ]
