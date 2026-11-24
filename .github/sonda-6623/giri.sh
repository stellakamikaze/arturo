#!/bin/bash
# Sonda temporanea #6623: lancia il test vero N volte e stampa l'esito di ogni giro.
# Uso: giri.sh <repo> <giri> <etichetta> [--baseline-ref 663bcba]
repo=$1 giri=$2 etichetta=$3
shift 3
for ((g = 0; g < giri; g++)); do
  inizio=$SECONDS
  uscita=$(python tests/test_parole_veloci_2026_11_22.py --repo "$repo" "$@" 2>&1)
  rc=$?
  riga=$(printf '%s\n' "$uscita" | grep -E "^(PASS|BASELINE_DISCRIMINANTE)|SP02|AssertionError" | tr '\n' ' ')
  echo "$etichetta giro=$g rc=$rc secondi=$((SECONDS - inizio)) $riga"
done
