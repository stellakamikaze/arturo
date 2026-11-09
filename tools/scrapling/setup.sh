#!/usr/bin/env bash
# setup.sh: installa Scrapling in un venv tutto suo (circa 300 MB).
# Il venv sta fra i dati della persona, in ~/.claude/data/scrapling/.venv: col plugin la cartella del codice
# cambia a ogni aggiornamento, e un venv lì dentro sparirebbe (review del 7/11/2026, finding 78). Un venv
# vecchio in tools/scrapling/.venv vale ancora. Solo il codice sta nel repository.
# Serve Python 3.10 o più recente. Con uv lo scarica uv; senza, usa il python3 del sistema.
#   bash setup.sh             installa
#   bash setup.sh --controlla dice se scrape è già installato
set -eu
cd "$(dirname "$0")"
VENV="${CLAUDE_CONFIG_DIR:-$HOME/.claude}/data/scrapling/.venv"
if [ "${1:-}" = "--controlla" ]; then
  for PY in "$VENV/bin/python" "$VENV/Scripts/python.exe" .venv/bin/python .venv/Scripts/python.exe; do
    [ -x "$PY" ] && { echo "scrape già installato"; exit 0; }
  done
  echo "scrape non installato"
  exit 0
fi
mkdir -p "$(dirname "$VENV")"
if command -v uv >/dev/null 2>&1; then
  uv venv --python 3.12 "$VENV"
  PY="$VENV/bin/python"; [ -x "$PY" ] || PY="$VENV/Scripts/python.exe"
  uv pip install --python "$PY" "scrapling[fetchers]" markdownify
else
  python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)' || {
    echo "Serve Python 3.10 o più recente (oppure uv, che lo scarica da solo)." >&2; exit 1; }
  python3 -m venv "$VENV"
  PY="$VENV/bin/python"; [ -x "$PY" ] || PY="$VENV/Scripts/python.exe"
  "$PY" -m pip install --quiet "scrapling[fetchers]" markdownify
fi
# Niente `scrapling install`: scarica i browser del livello stealth, che scrape non usa.
mkdir -p "$HOME/.local/bin"
if [ "$(pwd -P)" = "$(cd "${CLAUDE_CONFIG_DIR:-$HOME/.claude}/tools/scrapling" 2>/dev/null && pwd -P)" ]; then
  ln -sf "$PWD/scrape" "$HOME/.local/bin/scrape" 2>/dev/null || true
else
  # Col plugin un link andrebbe nella cartella di una versione: il lanciatore legge il puntatore
  # che l'avvio riscrive (~/.claude/arturo/radice).
  rm -f "$HOME/.local/bin/scrape"
  printf '#!/bin/sh\nR="$(cat "${CLAUDE_CONFIG_DIR:-$HOME/.claude}/arturo/radice" 2>/dev/null)"\nexec sh "${R:-%s}/tools/scrapling/scrape" "$@"\n' \
    "$(cd ../.. && pwd)" > "$HOME/.local/bin/scrape" && chmod +x "$HOME/.local/bin/scrape" || true
fi
echo "Fatto. Prova: bash $PWD/banco.sh"
echo "Comando: $PWD/scrape <url> --md  (oppure solo scrape, se ~/.local/bin è nel PATH)"
