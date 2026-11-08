#!/bin/sh
# Installa Herdr (herdr.dev) con il layout di Arturo e lo apre.
# Lo lancia /setup dopo il sì della persona (shared/setup-herdr.md). Si può rilanciare:
# non riscarica Herdr se c'è già, non tocca i tasti né le scelte della persona.
#
# Variabili per i banchi: HERDR_APP_HOME (cartella di Herdr), ARTURO_HERDR_INSTALLER (installer finto),
# ARTURO_HERDR_SISTEMA (mac-arm, mac-intel, windows, linux), ARTURO_HERDR_NON_APRIRE=1.
set -eu

qui=$(cd "$(dirname "$0")" && pwd)
# La cartella di Arturo (clone in ~/.claude o plugin): shared/herdr sta due livelli sotto.
radice=$(cd "$qui/../.." && pwd)
say() { printf '%s\n' "$*"; }

sistema=${ARTURO_HERDR_SISTEMA:-}
if [ -z "$sistema" ]; then
  case "$(uname -s)" in
    Darwin)
      if [ "$(sysctl -n hw.optional.arm64 2>/dev/null || echo 0)" = 1 ]; then sistema=mac-arm; else sistema=mac-intel; fi ;;
    MINGW* | MSYS* | CYGWIN*) sistema=windows ;;
    *) sistema=linux ;;
  esac
fi
case "$sistema" in
  mac-intel) say "HERDR NO: Herdr non gira sui Mac con processore Intel. Arturo funziona lo stesso nel Terminale."; exit 0 ;;
  linux) say "HERDR NO: su Linux questo passo per ora non c'è. Arturo funziona lo stesso nel terminale."; exit 0 ;;
esac

# Percorsi in forma Windows quando servono (C:/Users/...), uguali altrove.
percorso() { if command -v cygpath >/dev/null 2>&1; then cygpath -m "$1"; else printf '%s' "$1"; fi; }

if [ "$sistema" = windows ]; then
  app_home=${HERDR_APP_HOME:-${APPDATA:-$HOME/AppData/Roaming}/herdr-app}
else
  app_home=${HERDR_APP_HOME:-$HOME/.config/herdr-app}
fi

# 1. Herdr, dall'installer ufficiale (verifica sha256 e firma), solo se manca.
ha_herdr() {
  [ -n "${ARTURO_HERDR_INSTALLER:-}" ] && return 1
  command -v herdr-app >/dev/null 2>&1 || [ -x "$HOME/.local/bin/herdr-app" ] || [ -d "$HOME/Applications/Herdr.app" ] || [ -d /Applications/Herdr.app ]
}
if ha_herdr; then
  say "Herdr c'è già: aggiorno solo il layout di Arturo."
else
  say "Scarico Herdr da herdr.dev..."
  tmp=$(mktemp -d)
  trap 'rm -rf "$tmp"' EXIT
  if [ -n "${ARTURO_HERDR_INSTALLER:-}" ]; then
    sh "$ARTURO_HERDR_INSTALLER"
  elif [ "$sistema" = windows ]; then
    powershell -NoProfile -ExecutionPolicy Bypass -Command "irm https://releases.herdr.dev/app/install.ps1 | iex"
  else
    curl -fsSL https://releases.herdr.dev/app/install.sh -o "$tmp/install.sh"
    sh "$tmp/install.sh"
  fi
fi

# 2. Il layout, il tema, il mod e i font di Arturo.
mkdir -p "$app_home/layouts" "$app_home/themes" "$app_home/mods"
cp "$qui/layouts/arturo.json" "$qui/layouts/arturo.svg" "$app_home/layouts/"
cp "$qui"/themes/*.json "$app_home/themes/"
rm -rf "$app_home/mods/arturo.nuovo"
cp -R "$qui/mods/arturo" "$app_home/mods/arturo.nuovo"
rm -rf "$app_home/mods/arturo"
mv "$app_home/mods/arturo.nuovo" "$app_home/mods/arturo"

# 3. Come il mod chiama Arturo, e dove stanno i progetti.
py=python3
command -v python3 >/dev/null 2>&1 || py=python
base=${PROJECTS_BASE:-$HOME/Documents/ClaudeCode}
mkdir -p "$base"
versione=$(herdr-app --version 2>/dev/null | sed -n 's/^herdr-app //p' || true)
[ -n "$versione" ] || versione=$("$HOME/.local/bin/herdr-app" --version 2>/dev/null | sed -n 's/^herdr-app //p' || true)
ARTURO_HERDR_VERSIONE="${ARTURO_HERDR_VERSIONE:-$versione}" ARTURO_PY="$py" ARTURO_BIN="$(percorso "$radice/bin/arturo")" ARTURO_BASE="$(percorso "$base")" \
"$py" - "$qui" "$app_home" <<'PY'
import json, os, sys
qui, app = sys.argv[1], sys.argv[2]

def scrivi(nome, dati):
    dst = os.path.join(app, nome)
    tmp = dst + ".arturo-tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(dati, f, indent=2, ensure_ascii=False)
    os.replace(tmp, dst)

def leggi(nome):
    p = os.path.join(app, nome)
    if not os.path.exists(p):
        return None
    with open(p, encoding="utf-8") as f:
        return json.load(f)

scrivi("arturo.json", {"arturo": [os.environ["ARTURO_PY"], os.environ["ARTURO_BIN"]], "base": os.environ["ARTURO_BASE"]})

# Tasti: si aggiungono; un tasto che la persona usa già per altro resta suo.
tasti = leggi("keys.json") or {}
with open(os.path.join(qui, "keys.json"), encoding="utf-8") as f:
    nuovi = json.load(f)
for sez, voci in nuovi.items():
    mia = tasti.setdefault(sez, {})
    for k, v in voci.items():
        if k in mia and mia[k] != v:
            print(f"tasto {k} lasciato com'era ({mia[k]})")
            continue
        mia[k] = v
scrivi("keys.json", tasti)

# Impostazioni: la telemetria di Herdr resta spenta finché la persona non la accende.
imp = leggi("settings.json") or {}
imp.setdefault("telemetry", False)
imp.setdefault("sounds", {"enabled": True})
scrivi("settings.json", imp)

# Primo avvio: niente benvenuto né note di versione di Herdr in inglese, si parte dal layout di Arturo.
if leggi("shared.json") is None:
    scrivi("shared.json", {"layout": "arturo", "frame.welcomed": "skipped", "workspace.panels": []})
versione = os.environ.get("ARTURO_HERDR_VERSIONE", "")
if versione and leggi("update-notes.json") is None:
    scrivi("update-notes.json", {"last_run": versione, "presented": [versione]})
PY

# 4. Su Windows i terminali di Herdr partono in Git Bash, come vuole Arturo.
if [ "$sistema" = windows ]; then
  core_conf="${APPDATA:-$HOME/AppData/Roaming}/herdr-core/config.toml"
  mkdir -p "$(dirname "$core_conf")"
  if ! grep -q '^shell' "$core_conf" 2>/dev/null; then
    printf 'shell = ["%s", "-l"]\n' "$(percorso "$(command -v bash)")" >> "$core_conf"
  fi
fi

# 5. Controllo del mod e apertura.
if command -v herdr-app >/dev/null 2>&1 && [ -z "${ARTURO_HERDR_INSTALLER:-}" ]; then
  herdr-app check "$app_home/mods/arturo" >/dev/null || { say "HERDR ERRORE: il mod di Arturo non si carica (herdr-app check)."; exit 1; }
fi
if [ "${ARTURO_HERDR_NON_APRIRE:-0}" != 1 ]; then
  if [ "$sistema" = mac-arm ]; then
    open -a Herdr 2>/dev/null || open "$HOME/Applications/Herdr.app" 2>/dev/null || true
  fi
fi
say "HERDR OK: Herdr è pronto col layout di Arturo."
