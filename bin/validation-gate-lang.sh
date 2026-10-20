#!/usr/bin/env bash
# validation-gate-lang.sh: gate di validazione che riconosce il linguaggio del progetto.
#
# PERCHÉ ESISTE
#   Un gate che esce 0 senza aver validato niente dà un verde falso. Succede a un gate che
#   guarda solo package.json (tutto il resto passa), e a un gate che legge ${PIPESTATUS[0]}
#   nella shell zsh del tool Bash, dove PIPESTATUS non esiste e l'exit resta vuoto.
#   Questo script riconosce il linguaggio e, quando non può certificare, lo dice.
#
# CONTRATTO EXIT CODE
#   0  VERDE        validatori core eseguiti e passati
#   1  ROSSO        un validatore ha fallito: il chiamante si ferma
#   2  INCONCLUSIVO nessun validatore core disponibile o applicabile (prosa, o toolchain
#                   assente). NON è verde: serve un controllo di sostanza.
#
# ROUTING (meglio "inconclusivo" che un verde falso)
#   package.json                             -> node
#   pyproject.toml|requirements.txt|setup.py -> python
#   *.py nella radice                        -> python (marcatore secondario)
#   altrimenti                               -> prosa (mai verde da solo)
#
# STRUMENTI ASSENTI
#   Se ruff, pytest, mypy (o npx, npm) non ci sono, stampa [WARN] <tool> non installato: SKIP.
#   Se manca il validatore core, esce 2. Uno skip è sempre esplicito, mai un verde finto.
#   Un eseguibile che c'è ma non parte (per esempio bloccato dall'antivirus su Windows)
#   ripiega su `python -m <tool>` (vedi py_tool).
#
# GIUDIZIO SULLA PROSA (facoltativo)
#   Con --semantic e prosa, chiede un giudizio a `claude -p`. Se claude non risponde entro
#   60 s (perl alarm: su macOS `timeout` non esiste), resta il conteggio delle parole.
#
# USO
#   validation-gate-lang.sh [--dir DIR] [--mode quick|full|shipping]
#   quick = tsc + test + console.log · full = + lint + build · shipping = full senza console.log
#   validation-gate-lang.sh --detect-only [--dir DIR]   # stampa solo il linguaggio
#   validation-gate-lang.sh --semantic --dir DIR        # giudizio di claude sulla prosa
#   validation-gate-lang.sh --selftest                  # test interni su fixture sintetiche
#   Lo chiama shared/validation-gate.md. Il banco è tests/gate/test_gate.sh.
#
# NOTA: niente `set -e`: gli exit code si gestiscono a mano, di proposito.
set -uo pipefail

VERDE=0; ROSSO=1; INCONCLUSIVO=2

have() { command -v "$1" >/dev/null 2>&1; }

# --- funzione pura testabile: routing linguaggio -----------------------------
detect_lang() {
  local d="$1"
  [ -f "$d/package.json" ] && { echo "node"; return; }
  if [ -f "$d/pyproject.toml" ] || [ -f "$d/requirements.txt" ] || [ -f "$d/setup.py" ]; then
    echo "python"; return
  fi
  # marcatore secondario: sorgenti python in radice (shallow -> alta precisione)
  if ls "$d"/*.py >/dev/null 2>&1; then echo "python"; return; fi
  echo "prosa"
}

# --- esegue un tool e riporta rc, con skip esplicito se assente --------------
# uso: run_tool <bin> <etichetta> <dir> <comando...>; ritorna: 0 pass, 1 fail, 3 skip
run_tool() {
  local bin="$1" label="$2" dir="$3"; shift 3
  if ! have "$bin"; then
    echo "[WARN] ${label}: '${bin}' non installato — SKIP (non conta come verde)"
    return 3
  fi
  echo "--- ${label} ---"
  local out rc
  out="$( cd "$dir" && "$@" 2>&1 )"; rc=$?
  printf '%s\n' "$out" | tail -20
  if [ "$rc" -eq 0 ]; then echo "[OK] ${label} passato"; return 0
  else echo "[X] ${label} FALLITO (rc=${rc})"; return 1; fi
}

# --- comando di un tool Python: l'eseguibile se parte, se no `python -m` -------
# Su Windows un antivirus può bloccare pytest.exe o mypy.exe: `have` li trova, ma non partono e il gate
# uscirebbe rosso col codice verde. Stampa il comando, ritorna 1 se non c'è nessuna delle due vie.
py_tool() {
  local t="$1" py
  if have "$t" && "$t" --version >/dev/null 2>&1; then echo "$t"; return 0; fi
  for py in python3 python; do
    if have "$py" && "$py" -m "$t" --version >/dev/null 2>&1; then echo "$py -m $t"; return 0; fi
  done
  return 1
}

# --- validazione Python: core = pytest; ruff/mypy = layer qualita' -----------
run_python() {
  local dir="$1"
  local core_ran=0 any_fail=0 c

  if c="$(py_tool pytest)"; then
    # shellcheck disable=SC2086  # $c e' "pytest" o "python3 -m pytest": lo split e' voluto
    run_tool ${c%% *} "pytest" "$dir" $c -q -p no:cacheprovider .
    case $? in 0) core_ran=1;; 1) core_ran=1; any_fail=1;; esac
  else
    echo "[WARN] pytest non installato — nessun validatore CORE per Python"
  fi

  c="$(py_tool ruff)" || c=ruff
  # shellcheck disable=SC2086
  run_tool ${c%% *} "ruff" "$dir" $c check . ; [ $? -eq 1 ] && any_fail=1
  c="$(py_tool mypy)" || c=mypy
  # shellcheck disable=SC2086
  run_tool ${c%% *} "mypy" "$dir" $c . ;       [ $? -eq 1 ] && any_fail=1

  if [ "$any_fail" -eq 1 ]; then
    echo "[X] gate ROSSO (python) — almeno un validatore ha fallito"
    return "$ROSSO"
  fi
  if [ "$core_ran" -eq 1 ]; then
    echo "[OK] gate VERDE (python) — pytest passato"
    return "$VERDE"
  fi
  echo "[WARN] gate INCONCLUSIVO (python) — nessun validatore core eseguibile. NON e' verde."
  return "$INCONCLUSIVO"
}

# --- validazione Node: core = tsc + test (fedele al gate originale) ----------
run_node() {
  local dir="$1" mode="$2"
  local core_ran=0 any_fail=0

  if [ -f "$dir/tsconfig.json" ] && have npx; then
    run_tool npx "tsc --noEmit" "$dir" npx --no-install tsc --noEmit
    case $? in 0) core_ran=1;; 1) core_ran=1; any_fail=1;; esac
  else
    echo "[WARN] tsc: nessun tsconfig.json o npx assente — SKIP typecheck"
  fi

  if have npm && grep -q '"test"' "$dir/package.json" 2>/dev/null; then
    run_tool npm "npm test" "$dir" npm test --silent
    case $? in 0) core_ran=1;; 1) core_ran=1; any_fail=1;; esac
  else
    echo "[WARN] npm test: npm assente o nessuno script 'test' — SKIP"
  fi

  # lint e build: solo full e shipping, se lo script esiste nel package.json
  if [ "$mode" = "full" ] || [ "$mode" = "shipping" ]; then
    if grep -q '"lint"' "$dir/package.json" 2>/dev/null; then
      run_tool npm "npm run lint" "$dir" npm run lint --silent; [ $? -eq 1 ] && any_fail=1
    else echo "[WARN] lint: nessuno script 'lint' — SKIP"; fi
    if grep -q '"build"' "$dir/package.json" 2>/dev/null; then
      run_tool npm "npm run build" "$dir" npm run build --silent; [ $? -eq 1 ] && any_fail=1
    else echo "[WARN] build: nessuno script 'build' — SKIP"; fi
  fi

  # console.log nei file in stage: avviso, non blocca (quick e full)
  if [ "$mode" != "shipping" ]; then
    local cl
    cl="$(git -C "$dir" diff --cached --diff-filter=ACM 2>/dev/null | grep -n '^+.*console\.log')"
    if [ -n "$cl" ]; then echo "[WARN] console.log nei file in stage:"; printf '%s\n' "$cl" | head -10
    else echo "[OK] nessun console.log in stage"; fi
  fi

  if [ "$any_fail" -eq 1 ]; then
    echo "[X] gate ROSSO (node)"; return "$ROSSO"
  fi
  if [ "$core_ran" -eq 1 ]; then
    echo "[OK] gate VERDE (node)"; return "$VERDE"
  fi
  echo "[WARN] gate INCONCLUSIVO (node) — nessun validatore core eseguibile. NON e' verde."
  return "$INCONCLUSIVO"
}

# --- prosa/non-code: substance gate, MAI auto-verde --------------------------
run_prose() {
  local dir="$1" semantic="$2"
  echo "[gate] prosa/non-code: nessun validatore automatico applicabile."
  # substance note deterministica (prefilter che funziona da solo)
  local words files
  files=$(find "$dir" -maxdepth 2 -type f \( -name '*.md' -o -name '*.txt' \) 2>/dev/null | wc -l | tr -d ' ')
  words=$(cat "$dir"/*.md "$dir"/*.txt 2>/dev/null | wc -w | tr -d ' ')
  echo "[gate] substance: ${files} file testuali, ~${words} parole totali."
  [ "${words:-0}" -lt 20 ] && echo "[WARN] contenuto molto scarno (<20 parole) — verificare che non sia un placeholder."

  # layer semantico OPZIONALE via claude -p, con fallback graceful
  if [ "$semantic" = "1" ]; then
    if have claude; then
      local content verdict
      content="$(cat "$dir"/*.md "$dir"/*.txt 2>/dev/null | head -c 6000)"
      verdict="$(printf '%s' "$content" | perl -e 'alarm 60; exec @ARGV' claude -p \
        'Questo testo e in stato consegnabile o e un placeholder/bozza incompleta? Rispondi con una riga: CONSEGNABILE o INCOMPLETO + motivo breve.' \
        2>/dev/null)"
      if [ -n "$verdict" ]; then
        echo "[gate] giudizio semantico (claude): ${verdict}"
      else
        echo "[WARN] claude non ha risposto — fallback su substance deterministico."
      fi
    else
      echo "[WARN] --semantic richiesto ma 'claude' non disponibile — solo substance deterministico."
    fi
  fi

  echo "[WARN] gate INCONCLUSIVO (prosa) — substance gate manuale/semantico richiesto. NON e' verde."
  return "$INCONCLUSIVO"
}

# --- selftest interno: fixture sintetiche in tempdir -------------------------
_selftest() {
  local tmp ok=1
  tmp="$(mktemp -d "${TMPDIR:-/tmp}/gatelang.XXXXXX")"

  mkdir -p "$tmp/node" "$tmp/py" "$tmp/prose"
  echo '{"name":"x"}' > "$tmp/node/package.json"
  echo '# req' > "$tmp/py/requirements.txt"
  echo 'Testo di prova con abbastanza parole per non essere scarno affatto.' > "$tmp/prose/nota.md"

  assert_lang() {
    local got; got="$(detect_lang "$1")"
    if [ "$got" = "$2" ]; then echo "[OK] detect_lang($(basename "$1")) = $got"
    else echo "[X] detect_lang($(basename "$1")) = $got (atteso $2)"; ok=0; fi
  }
  assert_lang "$tmp/node" node
  assert_lang "$tmp/py" python
  assert_lang "$tmp/prose" prosa

  # prosa NON deve mai uscire verde
  run_prose "$tmp/prose" 0 >/dev/null; local rc=$?
  if [ "$rc" -eq "$INCONCLUSIVO" ]; then echo "[OK] run_prose ritorna INCONCLUSIVO (2), non verde"
  else echo "[X] run_prose ha ritornato $rc invece di 2"; ok=0; fi

  rm -rf "$tmp"
  if [ "$ok" -eq 1 ]; then echo "selftest OK"; return 0
  else echo "selftest FAILED"; return 1; fi
}

main() {
  local dir="$PWD" mode="${MODE:-quick}" detect_only=0 semantic=0
  while [ $# -gt 0 ]; do
    case "$1" in
      --dir) dir="$2"; shift 2;;
      --mode) mode="$2"; shift 2;;
      --detect-only) detect_only=1; shift;;
      --semantic) semantic=1; shift;;
      --selftest) _selftest; return $?;;
      -h|--help) grep '^#' "$0" | sed 's/^# \{0,1\}//'; return 0;;
      *) echo "[WARN] argomento ignoto: $1"; shift;;
    esac
  done

  local lang; lang="$(detect_lang "$dir")"
  echo "[gate] dir: ${dir} · mode: ${mode} · linguaggio rilevato: ${lang}"
  [ "$detect_only" -eq 1 ] && { echo "$lang"; return 0; }

  case "$lang" in
    node)   run_node "$dir" "$mode"; return $?;;
    python) run_python "$dir"; return $?;;
    prosa)  run_prose "$dir" "$semantic"; return $?;;
  esac
}

main "$@"
