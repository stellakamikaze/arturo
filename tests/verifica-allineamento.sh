#!/usr/bin/env bash
set -euo pipefail

ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
for tool in bash python3 git node; do
  command -v "$tool" >/dev/null 2>&1 || { echo "FAIL: $tool mancante" >&2; exit 1; }
done
python3 -c 'import yaml' >/dev/null 2>&1 || { echo "FAIL: PyYAML mancante" >&2; exit 1; }
# Un Python fino alla 3.11: lì argparse toglie «--» da `--motivo=--`, e U04 lo prova sulla CLI vera.
PYTHON_VECCHIO=""
for py in python3.8 python3.9 python3.10 python3.11 /usr/bin/python3; do
  if command -v "$py" >/dev/null 2>&1 && "$py" -c 'import sys; sys.exit(0 if (3, 8) <= sys.version_info[:2] <= (3, 11) else 1)' 2>/dev/null; then
    PYTHON_VECCHIO=$(command -v "$py"); break
  fi
done
[[ -n "$PYTHON_VECCHIO" ]] || { echo "FAIL: serve un Python dalla 3.8 alla 3.11 per U04 (il motivo «--» sui Python vecchi)" >&2; exit 1; }
echo "PYTHON_VECCHIO=$PYTHON_VECCHIO"
# Il pannello /dafare si prova con Claude Code vero (validate, test, claude -p): senza, il gate fallisce.
command -v claude >/dev/null 2>&1 || {
  echo "FAIL: claude mancante: il gate prova il pannello /dafare con claude plugin validate, claude plugin test e claude -p" >&2
  exit 1
}

FIXTURE=$(mktemp -d "${TMPDIR:-/tmp}/arturo-allineamento.XXXXXX")
trap 'rm -rf "$FIXTURE"' EXIT
HOME="$FIXTURE/home"
export HOME USERPROFILE="$HOME" XDG_CACHE_HOME="$FIXTURE/cache" TMPDIR="$FIXTURE/tmp" PYTHONDONTWRITEBYTECODE=1
# W13: nel gate la prova nel browser non salta. Senza Chrome o node 22 il gate è rosso.
export ARTURO_PROVA_BROWSER=obbligatoria
mkdir -p "$HOME" "$TMPDIR"
cp -R "$ROOT/." "$HOME/.claude"
REPO="$HOME/.claude"

BANCHI=(
  test-block-dangerous-falsi-positivi.py
  test-web-egress-guard.py
  test_bash_dispatcher_review.py
  test_bash_dispatcher_secrets.py
  test_permissivita_2026_09_08.py
  test_allineamento.py
  test_revisione_high.py
  test_revisione_medium.py
  test_revisione_low.py
  test_completezza.py
  test_prodotto.py
  test_revisione_2026_09_30.py
  test_strato.py
  test_todo.py
  test_pannello.py
  test_web.py
  test_percorso.py
  test_revisione_ciclo5.py
  test_mod_portati.py
)
for test in "${BANCHI[@]}"; do
  python3 -B "$REPO/tests/$test" --repo "$REPO"
done

# Il minimo dichiarato è Python 3.8: la CLI, la pagina e il percorso girano anche con quello. I banchi
# lanciano la CLI con l'interprete che li esegue (sys.executable).
PY38_BANCHI=(test_todo.py test_web.py test_percorso.py)
PY38=$(command -v python3.8 || true)
if [[ -n "$PY38" ]]; then
  for test in "${PY38_BANCHI[@]}"; do
    "$PY38" -B "$REPO/tests/$test" --repo "$REPO"
  done
else
  echo "NOTA: python3.8 assente, todo, pagina e percorso provati solo con $(python3 --version 2>&1)"
fi

# Controprove: ogni riga e' «banco ref [radice]». Il banco gira sulla base `ref` estratta con
# git archive e deve dichiararla discriminante. Con «radice» il banco riceve il repository vero
# e la base se la estrae da solo. Ogni ciclo aggiunge le sue righe in coda.
BASELINE=(
  # Revisioni fino al 29/9/2026: la base e' ee10fc6.
  "test-web-egress-guard.py ee10fc6 radice"
  "test-block-dangerous-falsi-positivi.py ee10fc6"
  "test_bash_dispatcher_review.py ee10fc6"
  "test_bash_dispatcher_secrets.py ee10fc6"
  "test_permissivita_2026_09_08.py ee10fc6"
  "test_allineamento.py ee10fc6"
  "test_revisione_high.py ee10fc6"
  "test_revisione_medium.py ee10fc6"
  "test_revisione_low.py ee10fc6"
  "test_completezza.py ee10fc6"
  "test_prodotto.py ee10fc6"
  # Revisione del 30/9/2026: 86ba137, l'ultimo dev prima delle correzioni.
  "test_revisione_2026_09_30.py 86ba137"
  # Strato dell'organizzazione (30/9/2026): e70da3d, l'ultimo dev prima dello strato.
  "test_strato.py e70da3d"
  # Archivio dei todo (3/10/2026): b8eff39, l'ultimo dev prima della CLI.
  "test_todo.py b8eff39"
  # Pannello dei todo (3/10/2026): fc6459f, l'ultimo dev prima del ciclo 1.5 e del pannello.
  "test_pannello.py fc6459f"
  # La pagina web dei todo (3/10/2026): 6ef1c0c, l'ultimo commit prima del ciclo 3.
  "test_web.py 6ef1c0c"
  # Il percorso a tappe (3/10/2026): 3001fcc, l'ultimo dev prima del ciclo 5.
  "test_percorso.py 3001fcc"
  # La revisione del ciclo 5 (3/10/2026): 81431a2, il commit subito prima delle correzioni. Il banco
  # conta un rosso solo se l'AssertionError comincia con il codice del controllo: un file o un
  # comando assente sulla base non prova niente. Le controprove dei cicli di correzione usano
  # questa regola e il commit subito prima della correzione.
  "test_revisione_ciclo5.py 81431a2"
  # I mod portati dalla config dell'autore (9/10/2026): cddcb10, l'ultimo dev prima del porting.
  "test_mod_portati.py cddcb10"
)
for riga in "${BASELINE[@]}"; do
  read -r test ref modo <<<"$riga"
  base="$FIXTURE/baseline-$ref"
  if [[ ! -d "$base" ]]; then
    mkdir -p "$base"
    git -C "$ROOT" archive "$ref" | tar -x -C "$base"
  fi
  if [[ "${modo:-}" == radice ]]; then
    python3 -B "$REPO/tests/$test" --repo "$ROOT" --baseline-ref "$ref"
  else
    python3 -B "$REPO/tests/$test" --repo "$base" --baseline-ref "$ref"
  fi
done

shells=0
while IFS= read -r -d '' file; do
  bash -n "$file"
  shells=$((shells + 1))
done < <(git -C "$REPO" ls-files -z -- '*.sh')
[[ $shells -gt 0 ]] || { echo "FAIL: nessun file shell" >&2; exit 1; }

python3 - "$REPO" "$FIXTURE/pycache" <<'PY'
import pathlib
import py_compile
import sys
root = pathlib.Path(sys.argv[1])
cache = pathlib.Path(sys.argv[2])
files = list(root.glob("**/*.py"))
if not files:
    raise SystemExit("FAIL: nessun file Python")
for index, path in enumerate(files):
    py_compile.compile(str(path), cfile=str(cache / f"{index}.pyc"), doraise=True)
print(f"PY_COMPILE={len(files)}")
PY

js=0
while IFS= read -r -d '' file; do
  node --check "$file"
  js=$((js + 1))
done < <(git -C "$REPO" ls-files -z -- '*.js' '*.mjs')
[[ $js -gt 0 ]] || { echo "FAIL: nessun file JavaScript" >&2; exit 1; }

bash "$REPO/skills/system-audit/audit.sh" --strict
printf 'PASS: banchi=%s shell=%s js=%s\n' "${#BANCHI[@]}" "$shells" "$js"
