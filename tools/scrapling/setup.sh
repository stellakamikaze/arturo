#!/usr/bin/env bash
# setup.sh: installa Scrapling in un venv tutto suo (tools/scrapling/.venv, circa 300 MB).
# Solo il codice sta nel repository: il venv si ricrea su ogni computer.
# Serve Python 3.10 o più recente. Con uv lo scarica uv; senza, usa il python3 del sistema.
set -eu
cd "$(dirname "$0")"
if command -v uv >/dev/null 2>&1; then
  uv venv --python 3.12 .venv
  PY=.venv/bin/python; [ -x "$PY" ] || PY=.venv/Scripts/python.exe
  uv pip install --python "$PY" "scrapling[fetchers]" markdownify
else
  python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)' || {
    echo "Serve Python 3.10 o più recente (oppure uv, che lo scarica da solo)." >&2; exit 1; }
  python3 -m venv .venv
  PY=.venv/bin/python; [ -x "$PY" ] || PY=.venv/Scripts/python.exe
  "$PY" -m pip install --quiet "scrapling[fetchers]" markdownify
fi
# Niente `scrapling install`: scarica i browser del livello stealth, che scrape non usa.
mkdir -p "$HOME/.local/bin" && ln -sf "$PWD/scrape" "$HOME/.local/bin/scrape" 2>/dev/null || true
echo "Fatto. Prova: bash $PWD/banco.sh"
echo "Comando: $PWD/scrape <url> --md  (oppure solo scrape, se ~/.local/bin è nel PATH)"
