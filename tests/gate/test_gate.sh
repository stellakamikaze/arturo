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
#   7. Swift e .NET (#3906): un Package.swift col test rotto dà ROSSO, col test verde dà VERDE con
#      la prova nell'output; una .sln in una sottocartella va nel ramo dotnet; senza dotnet il gate
#      esce INCONCLUSIVO e lo dice.
#   8. Un progetto Python senza test (review del 7/11/2026, finding 31): pytest esce 5, il gate esce 2
#      INCONCLUSIVO e lo dice, mai ROSSO. Rosso sulla 0b083f5.
#   9. Lotto L10 (9/11/2026): un progetto node con requirements.txt fa girare anche pytest; lo script
#      test di `npm init` e un tsconfig senza typescript sono SKIP; --dir relativo vale come assoluto;
#      --dir senza valore esce 2.
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

# --- 8. Un progetto Python senza test: INCONCLUSIVO, non ROSSO ------------------------------
SENZA="$(mktemp -d "${TMPDIR:-/tmp}/gate-senza-test.XXXXXX")"
echo '# req' > "$SENZA/requirements.txt"
printf 'X = 1\n' > "$SENZA/a.py"
if command -v pytest >/dev/null 2>&1; then
  s_out="$( bash "$GATE" --dir "$SENZA" --mode quick 2>&1 )"; s_rc=$?
  note "senza test -> rc=$s_rc"
  if [ "$s_rc" -eq 2 ] && printf '%s' "$s_out" | grep -q "nessun test" \
     && ! printf '%s' "$s_out" | grep -q "pytest FALLITO"; then
    ok "senza test: Python senza test -> INCONCLUSIVO (rc=2), non ROSSO"
  else
    ko "senza test" "atteso rc=2 con 'nessun test', avuto rc=$s_rc: $(printf '%s' "$s_out" | grep -E '\[(X|WARN)\]' | head -3 | tr '\n' ' ')"
  fi
else
  ko "senza test" "pytest assente su questa macchina: il caso non puo' girare, installa pytest"
fi
rm -rf "$SENZA"

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

# --- 7. SWIFT E .NET (#3906, 26/10/2026): non più prosa, e un test rotto è ROSSO ---------
# Il caso vero: Cornetta (Swift, C#) usciva "prosa" e il gate non lanciava nessun test.
SW="$(mktemp -d "${TMPDIR:-/tmp}/gate-swift.XXXXXX")"
mkdir -p "$SW/scripts"
echo '// swift-tools-version:5.9' > "$SW/Package.swift"
printf 'echo "test rotto"\nexit 1\n' > "$SW/scripts/test.sh"
sw_out="$( bash "$GATE" --dir "$SW" --mode quick 2>&1 )"; sw_rc=$?
[ "$sw_rc" -eq 1 ] && printf '%s' "$sw_out" | grep -q "scripts/test.sh FALLITO" \
  && ok "swift: scripts/test.sh rotto -> ROSSO (rc=1)" \
  || ko "swift veleno" "atteso rc=1 con 'scripts/test.sh FALLITO', avuto rc=$sw_rc"
printf 'exit 0\n' > "$SW/scripts/test.sh"
sw_out="$( bash "$GATE" --dir "$SW" --mode quick 2>&1 )"; sw_rc=$?
[ "$sw_rc" -eq 0 ] && printf '%s' "$sw_out" | grep -q "scripts/test.sh passato" \
  && ok "swift: scripts/test.sh verde -> VERDE con la prova nell'output" \
  || ko "swift verde" "atteso rc=0 con 'scripts/test.sh passato', avuto rc=$sw_rc"
rm -rf "$SW"
NET="$(mktemp -d "${TMPDIR:-/tmp}/gate-dotnet.XXXXXX")"
mkdir -p "$NET/windows" && echo 'Microsoft Visual Studio Solution File' > "$NET/windows/App.sln"
net_lang="$( bash "$GATE" --detect-only --dir "$NET" 2>/dev/null | tail -1 )"
[ "$net_lang" = "dotnet" ] && ok "routing: una .sln in una sottocartella -> 'dotnet'" \
  || ko "routing dotnet" "atteso 'dotnet', avuto '$net_lang'"
if ! command -v dotnet >/dev/null 2>&1; then
  net_out="$( bash "$GATE" --dir "$NET" --mode quick 2>&1 )"; net_rc=$?
  [ "$net_rc" -eq 2 ] && printf '%s' "$net_out" | grep -q "non installato" \
    && ok "dotnet assente: INCONCLUSIVO (rc=2) con lo SKIP detto" \
    || ko "dotnet assente" "atteso rc=2 con 'non installato', avuto rc=$net_rc"
fi
rm -rf "$NET"

# --- 9. Lotto L10 (9/11/2026): node con Python, --dir relativo, tsc e npm test assenti, uso sbagliato -----
L10="$(mktemp -d "${TMPDIR:-/tmp}/gate-l10.XXXXXX")"
mkdir -p "$L10/misto" "$L10/init" "$L10/ts" "$L10/rel/w"
printf '{"scripts":{"test":"node -e 0"}}' > "$L10/misto/package.json"
echo '# req' > "$L10/misto/requirements.txt"
printf 'def test_rotto():\n    assert 1 == 2\n' > "$L10/misto/test_rotto.py"
printf '{"name":"test","scripts":{"test":"echo \\"Error: no test specified\\" && exit 1"}}' > "$L10/init/package.json"
printf '{"name":"x"}' > "$L10/ts/package.json"; echo '{}' > "$L10/ts/tsconfig.json"
echo '# req' > "$L10/rel/w/requirements.txt"; printf 'X = 1\n' > "$L10/rel/w/a.py"
l_misto="$( bash "$GATE" --dir "$L10/misto" 2>&1 )"; r_misto=$?
l_init="$( bash "$GATE" --dir "$L10/init" 2>&1 )"; r_init=$?
l_ts="$( PATH="/usr/bin:/bin" bash "$GATE" --dir "$L10/ts" 2>&1 )"; r_ts=$?
( cd "$L10/rel" && bash "$GATE" --dir w >/dev/null 2>&1 ); r_rel=$?
bash "$GATE" --dir >/dev/null 2>&1; r_uso=$?
if command -v pytest >/dev/null 2>&1 && [ "$r_misto" -eq 1 ] && printf '%s' "$l_misto" | grep -q "pytest FALLITO"; then
  ok "L10: node con requirements.txt fa girare anche pytest, e il test rotto è ROSSO"
else ko "L10 misto" "atteso rc=1 con pytest FALLITO, avuto rc=$r_misto"; fi
if [ "$r_init" -ne 1 ] && ! printf '%s' "$l_init" | grep -q "npm test FALLITO"; then
  ok "L10: lo script test di npm init non è un test rosso (rc=$r_init)"
else ko "L10 npm init" "avuto rc=$r_init"; fi
if [ "$r_ts" -ne 1 ] && ! printf '%s' "$l_ts" | grep -q "tsc --noEmit FALLITO"; then
  ok "L10: tsconfig senza typescript installato è SKIP, non ROSSO (rc=$r_ts)"
else ko "L10 tsc assente" "avuto rc=$r_ts"; fi
if [ "$r_rel" -ne 1 ] && [ "$r_uso" -eq 2 ]; then
  ok "L10: --dir relativo non dà rosso falso, --dir senza valore è un errore d'uso (2)"
else ko "L10 --dir" "relativo rc=$r_rel, senza valore rc=$r_uso"; fi
rm -rf "$L10"

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
