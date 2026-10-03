#!/usr/bin/env bash
set -euo pipefail

ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
for tool in bash python3 git node; do
  command -v "$tool" >/dev/null 2>&1 || { echo "FAIL: $tool mancante" >&2; exit 1; }
done
python3 -c 'import yaml' >/dev/null 2>&1 || { echo "FAIL: PyYAML mancante" >&2; exit 1; }
# Il pannello /dafare si prova con Claude Code vero (validate, test, claude -p): senza, il gate fallisce.
command -v claude >/dev/null 2>&1 || {
  echo "FAIL: claude mancante: il gate prova il pannello /dafare con claude plugin validate, claude plugin test e claude -p" >&2
  exit 1
}

FIXTURE=$(mktemp -d "${TMPDIR:-/tmp}/arturo-allineamento.XXXXXX")
trap 'rm -rf "$FIXTURE"' EXIT
HOME="$FIXTURE/home"
export HOME USERPROFILE="$HOME" XDG_CACHE_HOME="$FIXTURE/cache" TMPDIR="$FIXTURE/tmp" PYTHONDONTWRITEBYTECODE=1
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
)
for test in "${BANCHI[@]}"; do
  python3 -B "$REPO/tests/$test" --repo "$REPO"
done

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
