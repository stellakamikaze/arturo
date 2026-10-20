#!/usr/bin/env bash
# test_gate.sh: banco del verde falso per bin/validation-gate-lang.sh.
#
# COSA PROVA
#   1. VELENO: un test Python che fallisce dà ROSSO (exit 1, "pytest FALLITO").
#   2. ROUTING: le fixture node, py e prose finiscono nel ramo giusto.
#   3. La fixture Python non esce 0 in silenzio: l'output mostra la validazione.
#   4. ruff e mypy assenti danno uno SKIP esplicito, non un fallimento.
#   5. La prosa esce 2 (INCONCLUSIVO), mai verde.
#   6. Il --selftest interno del gate è verde.
#   GATE_OVERRIDE=<path> prova un'altra versione del gate (controprova sul codice vecchio).
#
# Serve pytest nel PATH: senza, il veleno non gira e il banco è rosso, non verde.
# Le fixture stanno in fixtures/{node,py,prose}/ e si copiano in una cartella temporanea:
# ruff e mypy scrivono le loro cache accanto ai file.
#
#   bash test_gate.sh        # esegue
#   bash test_gate.sh -v     # verboso
# Niente pipefail: con `printf | grep -q` grep esce al primo match, printf può prendere
# SIGPIPE e con pipefail il match diventerebbe un fallimento.
set -u

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
GATE="${GATE_OVERRIDE:-$HERE/../../bin/validation-gate-lang.sh}"
FIX="$(mktemp -d "${TMPDIR:-/tmp}/gate-fixture.XXXXXX")"
cp -R "$HERE/fixtures/." "$FIX/"
trap 'rm -rf "$FIX"' EXIT
VERBOSE=0; [ "${1:-}" = "-v" ] && VERBOSE=1

PASS=0; FAIL=0
ok()   { PASS=$((PASS+1)); echo "  [OK]  $1"; }
ko()   { FAIL=$((FAIL+1)); echo "  [X]   $1 — $2"; }
note() { [ "$VERBOSE" -eq 1 ] && echo "        | $1"; return 0; }

# false-green := exit 0 SENZA alcuna evidenza di validazione nell'output.
is_false_green() {
  local rc="$1" out="$2"
  [ "$rc" -ne 0 ] && return 1
  printf '%s' "$out" | grep -Eiq 'pytest|ruff|mypy|npm test|tsc|\[OK\] gate VERDE' && return 1
  return 0   # rc==0 e nessuna evidenza -> false green
}

if [ ! -x "$GATE" ] && [ ! -f "$GATE" ]; then
  echo "[X] gate non trovato: $GATE"; exit 1
fi

echo "== Eval FALSE-GREEN — validation-gate =="

# --- 1. VELENO: un test Python che fallisce deve dare ROSSO (exit 1) -------
VELENO="$(mktemp -d "${TMPDIR:-/tmp}/gate-veleno.XXXXXX")"
echo '# req' > "$VELENO/requirements.txt"
printf 'def test_rotto():\n    assert 1 == 2\n' > "$VELENO/test_rotto.py"
if command -v pytest >/dev/null 2>&1; then
  v_out="$( bash "$GATE" --dir "$VELENO" --mode quick 2>&1 )"; v_rc=$?
  note "veleno -> rc=$v_rc"
  if [ "$v_rc" -eq 1 ] && printf '%s' "$v_out" | grep -q "pytest FALLITO"; then
    ok "veleno: test Python rotto -> ROSSO (rc=1, pytest FALLITO)"
  else
    ko "veleno" "atteso rc=1 con 'pytest FALLITO', avuto rc=$v_rc"
  fi
else
  # Senza pytest il veleno non gira: il banco non può certificare il gate, quindi è rosso.
  ko "veleno" "pytest assente su questa macchina: il caso non puo' girare, installa pytest"
fi
rm -rf "$VELENO"

# --- 2. ROUTING: detection deterministica -----------------------------------
node_lang="$( bash "$GATE" --detect-only --dir "$FIX/node" 2>/dev/null | tail -1 )"
[ "$node_lang" = "node" ] && ok "routing: fixture node -> 'node'" \
  || ko "routing node" "atteso 'node', avuto '$node_lang'"

py_lang="$( bash "$GATE" --detect-only --dir "$FIX/py" 2>/dev/null | tail -1 )"
[ "$py_lang" = "python" ] && ok "routing: fixture py -> 'python'" \
  || ko "routing py" "atteso 'python', avuto '$py_lang'"

prose_lang="$( bash "$GATE" --detect-only --dir "$FIX/prose" 2>/dev/null | tail -1 )"
[ "$prose_lang" = "prosa" ] && ok "routing: fixture prose -> 'prosa'" \
  || ko "routing prose" "atteso 'prosa', avuto '$prose_lang'"

# --- 3. LA CURA: la fixture Python NON esce 0-silenziosa (assert centrale) ---
py_out="$( bash "$GATE" --dir "$FIX/py" --mode quick 2>&1 )"
py_rc=$?
note "nuovo gate py -> rc=$py_rc"
note "$(printf '%s' "$py_out" | tail -6)"
if is_false_green "$py_rc" "$py_out"; then
  ko "gate LANGUAGE-AWARE su Python" "ANCORA false-green (rc=0 senza validazione)"
else
  ok "gate LANGUAGE-AWARE su Python NON esce 0-silenziosa (rc=$py_rc, validazione visibile)"
fi
# deve aver rilevato python e NON stampare un messaggio di skip muto
printf '%s' "$py_out" | grep -qi "python" \
  && ok "gate ha rilevato ed etichettato 'python'" \
  || ko "etichetta python" "output non menziona python"
printf '%s' "$py_out" | grep -qi "skip validation" \
  && ko "residuo vecchio gate" "output contiene ancora 'skip validation'" \
  || ok "nessun 'skip validation' muto nell'output Python"

# --- 4. DEGRADO CON GRAZIA: ruff/mypy assenti -> [WARN] skip, non crash ------
if printf '%s' "$py_out" | grep -q "ruff"; then
  if command -v ruff >/dev/null 2>&1; then
    ok "ruff presente: eseguito"
  else
    printf '%s' "$py_out" | grep -Eq "ruff.*(non installato|SKIP)" \
      && ok "ruff assente: [WARN] SKIP esplicito (degrado con grazia)" \
      || ko "degrado ruff" "ruff assente ma nessun SKIP esplicito"
  fi
fi

# --- 5. PROSA: substance gate, mai auto-verde -------------------------------
prose_out="$( bash "$GATE" --dir "$FIX/prose" --mode quick 2>&1 )"
prose_rc=$?
note "nuovo gate prose -> rc=$prose_rc"
if [ "$prose_rc" -eq 2 ] && ! printf '%s' "$prose_out" | grep -q "\[OK\] gate VERDE"; then
  ok "prosa -> INCONCLUSIVO (rc=2), nessun verde dichiarato"
else
  ko "gate su prosa" "atteso rc=2 senza verde, avuto rc=$prose_rc"
fi
if is_false_green "$prose_rc" "$prose_out"; then
  ko "gate su prosa" "false-green sulla prosa"
else
  ok "prosa NON esce 0-silenziosa"
fi

# --- 6. selftest interno del gate stesso ------------------------------------
if bash "$GATE" --selftest >/dev/null 2>&1; then
  ok "gate --selftest interno verde"
else
  ko "gate --selftest" "il selftest interno del gate fallisce"
fi

echo
echo "== ${PASS} PASS · ${FAIL} FAIL =="
[ "$FAIL" -eq 0 ] || { echo "[X] EVAL ROSSO — il gate non protegge dal false-green"; exit 1; }
echo "[OK] EVAL VERDE — il false-green e' catturato e il gate degrada con grazia"
exit 0
