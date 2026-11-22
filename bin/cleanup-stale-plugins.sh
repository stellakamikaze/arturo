#!/usr/bin/env bash
# cleanup-stale-plugins.sh: disinstalla i plugin installati che enabledPlugins non nomina più.
# Si può rilanciare senza danni. Serve dopo una sincronizzazione fra macchine: l'elenco dei plugin
# installati (plugins/installed_plugins.json) resta locale, settings.json viaggia.
#
# Non tocca (A9, revisione del 20/11/2026: fino al 22/11 li disinstallava):
# - un plugin spento ("nome": false in enabledPlugins): la persona l'ha spento, non l'ha tolto;
# - un plugin nominato solo in settings.local.json;
# - Arturo (arturo@...), anche spento: senza, la persona perde guardie e comandi;
# - un plugin installato solo per un progetto (scope project o local): lo attiva la config del progetto.
#
# Uso: --dry-run elenca e stampa il comando, senza toccare niente (lo usa /system-audit);
#      --yes disinstalla senza chiedere; senza opzioni chiede conferma.
# Exit: 0 fatto o niente da fare, 1 settings.json assente o illeggibile.

set -euo pipefail

# Plugin installati che enabledPlugins non nomina, né accesi né spenti
STALE=$(python3 - <<'PYEOF'
import json, os, sys
home = os.path.expanduser("~")
settings = os.path.join(home, ".claude", "settings.json")
locale = os.path.join(home, ".claude", "settings.local.json")
installed = os.path.join(home, ".claude", "plugins", "installed_plugins.json")
try:
    with open(settings, encoding="utf-8") as f:
        nominati = set(json.load(f).get("enabledPlugins", {}))
except (OSError, ValueError, AttributeError) as e:
    print("ERRORE: settings.json assente o illeggibile: %s" % e, file=sys.stderr)
    sys.exit(1)
try:
    with open(locale, encoding="utf-8") as f:
        nominati |= set(json.load(f).get("enabledPlugins", {}))
except (OSError, ValueError, AttributeError):
    pass  # settings.local.json è facoltativo
if not os.path.exists(installed):
    sys.exit(0)  # nessun plugin installato: niente da pulire
try:
    with open(installed, encoding="utf-8") as f:
        plugins = json.load(f).get("plugins", {})
except (OSError, ValueError, AttributeError) as e:
    print("ERRORE: installed_plugins.json illeggibile: %s" % e, file=sys.stderr)
    sys.exit(1)

def di_progetto(voci):
    """Vero se ogni installazione è legata a un progetto: la attiva la config di quel progetto."""
    if not isinstance(voci, list) or not voci:
        return False
    return all(isinstance(v, dict) and v.get("scope") in ("project", "local") for v in voci)

for p in sorted(plugins):
    if p in nominati or p.startswith("arturo@") or di_progetto(plugins[p]):
        continue
    print(p)
PYEOF
)

if [ -z "$STALE" ]; then
  echo "Nessun plugin da togliere: settings.json nomina tutti gli installati."
  exit 0
fi

echo "Plugin installati che settings.json non nomina più:"
echo "$STALE" | sed 's/^/  - /'
echo ""

if [ "${1:-}" = "--dry-run" ]; then
  echo "Prova a vuoto: niente rimosso. Per rimuoverli: bash $(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/cleanup-stale-plugins.sh --yes"
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
