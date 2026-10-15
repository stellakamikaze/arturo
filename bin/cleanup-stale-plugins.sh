#!/usr/bin/env bash
# cleanup-stale-plugins.sh: disinstalla i plugin installati ma NON attivi in enabledPlugins di settings.json.
# Si può rilanciare senza danni. Serve dopo una sincronizzazione fra macchine: l'elenco dei plugin
# installati (plugins/installed_plugins.json) resta locale, settings.json viaggia.
#
# Uso: --dry-run elenca e stampa il comando, senza toccare niente (lo usa /system-audit);
#      --yes disinstalla senza chiedere; senza opzioni chiede conferma.
# Exit: 0 fatto o niente da fare, 1 settings.json assente o illeggibile.

set -euo pipefail

# Plugin installati che non compaiono fra gli attivi
STALE=$(python3 - <<'PYEOF'
import json, os, sys
home = os.path.expanduser("~")
settings = os.path.join(home, ".claude", "settings.json")
installed = os.path.join(home, ".claude", "plugins", "installed_plugins.json")
try:
    with open(settings, encoding="utf-8") as f:
        enabled = {k for k, v in json.load(f).get("enabledPlugins", {}).items() if v}
except (OSError, ValueError, AttributeError) as e:
    print("ERRORE: settings.json assente o illeggibile: %s" % e, file=sys.stderr)
    sys.exit(1)
if not os.path.exists(installed):
    sys.exit(0)  # nessun plugin installato: niente da pulire
try:
    with open(installed, encoding="utf-8") as f:
        installed_set = set(json.load(f).get("plugins", {}).keys())
except (OSError, ValueError, AttributeError) as e:
    print("ERRORE: installed_plugins.json illeggibile: %s" % e, file=sys.stderr)
    sys.exit(1)
for p in sorted(installed_set - enabled):
    print(p)
PYEOF
)

if [ -z "$STALE" ]; then
  echo "Nessun plugin da togliere: tutti gli installati sono attivi."
  exit 0
fi

echo "Plugin installati ma non attivi:"
echo "$STALE" | sed 's/^/  - /'
echo ""

if [ "${1:-}" = "--dry-run" ]; then
  echo "Prova a vuoto: niente rimosso. Per rimuoverli: bash ~/.claude/bin/cleanup-stale-plugins.sh --yes"
  exit 0
fi

if [ "${1:-}" != "--yes" ]; then
  read -p "Li disinstallo? [s/N] " -n 1 -r
  echo
  [[ ! $REPLY =~ ^[SsYy]$ ]] && { echo "Annullato."; exit 0; }
fi

while IFS= read -r plugin; do
  [ -z "$plugin" ] && continue
  echo "-> disinstallo $plugin"
  claude plugin uninstall "$plugin" 2>&1 | tail -1
done <<< "$STALE"

echo ""
echo "Fatto."
