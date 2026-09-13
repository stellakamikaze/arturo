#!/usr/bin/env bash
set -euo pipefail

ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
for tool in bash python3 git node; do
  command -v "$tool" >/dev/null 2>&1 || { echo "FAIL: $tool mancante" >&2; exit 1; }
done
python3 -c 'import yaml' >/dev/null 2>&1 || { echo "FAIL: PyYAML mancante" >&2; exit 1; }

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
)
for test in "${BANCHI[@]}"; do
  python3 -B "$REPO/tests/$test" --repo "$REPO"
done

BASELINE="$FIXTURE/baseline"
mkdir -p "$BASELINE"
git -C "$ROOT" archive ee10fc6 | tar -x -C "$BASELINE"
python3 -B "$REPO/tests/test-web-egress-guard.py" --repo "$ROOT" --baseline-ref ee10fc6
for test in \
  test-block-dangerous-falsi-positivi.py \
  test_bash_dispatcher_review.py \
  test_bash_dispatcher_secrets.py \
  test_permissivita_2026_09_08.py \
  test_allineamento.py \
  test_revisione_high.py \
  test_revisione_medium.py \
  test_revisione_low.py \
  test_completezza.py; do
  python3 -B "$REPO/tests/$test" --repo "$BASELINE" --baseline-ref ee10fc6
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
done < <(git -C "$REPO" ls-files -z -- '*.js')
[[ $js -gt 0 ]] || { echo "FAIL: nessun file JavaScript" >&2; exit 1; }

bash "$REPO/skills/system-audit/audit.sh" --strict
printf 'PASS: banchi=%s shell=%s js=%s\n' "${#BANCHI[@]}" "$shells" "$js"
