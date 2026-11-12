#!/bin/sh
# Installa Herdr (herdr.dev) con il layout di Arturo e lo apre.
# Lo lancia /setup dopo il sì della persona (shared/setup-herdr.md). Si può rilanciare:
# non riscarica Herdr se c'è già, non tocca i tasti né le scelte della persona.
#
# Variabili per i banchi: HERDR_APP_HOME (cartella di Herdr), ARTURO_HERDR_INSTALLER (installer finto),
# ARTURO_HERDR_SISTEMA (mac-arm, mac-intel, windows, linux), ARTURO_HERDR_NON_APRIRE=1,
# ARTURO_HERDR_FIRMA (assente o presente: l'identità di firma locale senza chiedere al portachiavi),
# ARTURO_HERDR_VERSIONE (la versione di Herdr, senza chiederla a herdr-app --version).
set -eu

qui=$(cd "$(dirname "$0")" && pwd)
# La cartella di Arturo (clone in ~/.claude o plugin): shared/volta sta due livelli sotto.
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

# Anche su Windows Herdr legge ~/.config/herdr-app, non %APPDATA% (Herdr 0.1.14, provato il 9/11/2026).
app_home=${HERDR_APP_HOME:-$HOME/.config/herdr-app}

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
# Il primo Python che risponde davvero: su Windows python3 può essere lo stub dello Store, che
# esiste come comando ma esce 9009 e rimanda allo Store (#5079).
py=""
for c in python3 python; do
  if "$c" -c "import sys" >/dev/null 2>&1; then py=$c; break; fi
done
[ -n "$py" ] || { say "HERDR ERRORE: manca Python (python3 o python) per scrivere la configurazione."; exit 1; }
# Tasti: sui Mac quelli con ⌘; altrove ⌘ sarebbe il tasto Windows, che il sistema si tiene.
# I tasti di serie di Herdr dello stesso sistema (copie di defaults/): la base di un keys.json che non c'è.
tasti=keys.json
serie=keys-herdr-macos.json
[ "$sistema" = mac-arm ] || { tasti=keys-ctrl.json; serie=keys-herdr.json; }
base=${PROJECTS_BASE:-$HOME/Documents/ClaudeCode}
mkdir -p "$base"
versione=$(herdr-app --version 2>/dev/null | sed -n 's/^herdr-app //p' || true)
[ -n "$versione" ] || versione=$("$HOME/.local/bin/herdr-app" --version 2>/dev/null | sed -n 's/^herdr-app //p' || true)
ARTURO_HERDR_VERSIONE="${ARTURO_HERDR_VERSIONE:-$versione}" ARTURO_TASTI="$tasti" ARTURO_SERIE="$serie" ARTURO_PY="$py" ARTURO_BIN="$(percorso "$radice/bin/arturo")" ARTURO_RADICE="$(percorso "$radice")" ARTURO_BASE="$(percorso "$base")" \
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

# arturo.json: arturo, radice e base si riscrivono, le altre chiavi della persona (note_progetto) restano.
# radice è la cartella di Arturo: i suggerimenti la usano per i file di istruzioni, che non sempre stanno in ~/.claude.
arturo = leggi("arturo.json") or {}
arturo.update({"arturo": [os.environ["ARTURO_PY"], os.environ["ARTURO_BIN"]], "radice": os.environ["ARTURO_RADICE"], "base": os.environ["ARTURO_BASE"]})
scrivi("arturo.json", arturo)

# Tasti: si aggiungono; un tasto che la persona usa già per altro resta suo.
# Uno solo si prende a Herdr: la scheda nuova (tab.new, una shell) diventa la sessione nuova di Claude,
# e solo se quel tasto fa ancora la scheda nuova di Herdr (#5290).
PRENDE = {"arturo.volta-nuova": "tab.new"}
# Un tasto rimasto su un mod di Arturo tolto non apre più niente: vale come libero e si riallinea.
# Solo questi tre valori esatti, e solo sui tasti di Arturo: ogni altro tasto resta della persona.
VECCHI = ("mod.open:arturo-progetti", "mod.open:arturo-chrome", "mod.open:arturo-stato")
# Senza keys.json si parte dai tasti di serie di Herdr: Herdr li scrive solo se il file manca, e un
# file coi soli tasti di Arturo lasciava Volta senza ⌘W, ⌘C, ⌘V e gli altri (#5369, 12/11/2026).
tasti = leggi("keys.json")
if tasti is None:
    with open(os.path.join(qui, os.environ["ARTURO_SERIE"]), encoding="utf-8") as f:
        tasti = json.load(f)
with open(os.path.join(qui, os.environ["ARTURO_TASTI"]), encoding="utf-8") as f:
    nuovi = json.load(f)
for sez, voci in nuovi.items():
    mia = tasti.setdefault(sez, {})
    for k, v in voci.items():
        if mia.get(k) in VECCHI:
            del mia[k]
        if k in mia and mia[k] != v and mia[k] != PRENDE.get(v):
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
  # come per l'app: herdr-core legge ~/.config/herdr-core/config.toml anche su Windows (hc --help)
  core_conf="$HOME/.config/herdr-core/config.toml"
  mkdir -p "$(dirname "$core_conf")"
  if ! grep -q '^shell' "$core_conf" 2>/dev/null; then
    printf 'shell = ["%s", "-l"]\n' "$(percorso "$(command -v bash)")" >> "$core_conf"
  fi
fi

# 5. Sul Mac, Arturo.app: Herdr col nome e l'icona di Arturo, riallineata dopo ogni aggiornamento.
app_arturo=""
if [ "$sistema" = mac-arm ] && [ -z "${ARTURO_HERDR_INSTALLER:-}" ] && [ -d "$HOME/Applications/Herdr.app" ]; then
  sh "$qui/arturo-app.sh" --agente || say "Arturo.app non è pronta: Herdr funziona lo stesso col suo nome."
  [ -d "$HOME/Applications/Arturo.app" ] && app_arturo="$HOME/Applications/Arturo.app"
fi

# 5b. La firma locale di Arturo.app (#5020): senza, macOS richiede i permessi a ogni aggiornamento di Herdr.
# Lo script la propone e basta: firma-locale.sh chiede la password del Mac, quindi lo lancia la persona.
firma=${ARTURO_HERDR_FIRMA:-}
if [ -z "$firma" ] && [ -n "$app_arturo" ]; then
  if security find-identity -v -p codesigning 2>/dev/null | grep -q '"Arturo firma locale"'; then firma=presente; else firma=assente; fi
fi
if [ "$sistema" = mac-arm ] && [ "$firma" = assente ]; then
  say "HERDR FIRMA: perché macOS ricordi i permessi di Arturo.app dopo ogni aggiornamento, lancia nel tuo Terminale: sh \"$(percorso "$qui/firma-locale.sh")\""
fi

# 5c. La nascita in background (#5172): il comando claude dei terminali fa nascere la sessione in background
# e la apre lì, così Volta la apre da ogni macchina anche mentre lavora. I file si copiano sempre; il blocco
# nel file di avvio della shell lo scrive solo volta-nascita.sh, col sì della persona (/setup lancia il
# comando della riga HERDR NASCITA, o "no" per non sentirsela riproporre). Sul Mac zsh e bash, su Windows
# il profilo di PowerShell.
if [ "$sistema" = mac-arm ] || [ "$sistema" = windows ]; then
  cp "$qui/volta-claude.sh" "$app_home/volta-claude"
  cp "$qui/nascita.sh" "$app_home/volta-nascita.sh"
  chmod +x "$app_home/volta-claude" "$app_home/volta-nascita.sh"
  [ "$sistema" = windows ] && cp "$qui/volta-claude.ps1" "$app_home/volta-claude.ps1"
  nascita=$(percorso "$app_home/volta-nascita.sh")
  stato_nascita=$(sh "$app_home/volta-nascita.sh" stato)
  if printf '%s\n' "$stato_nascita" | grep -q '^assente' && ! printf '%s\n' "$stato_nascita" | grep -q '^rifiutata'; then
    say "HERDR NASCITA: perché Volta apra da ogni macchina le sessioni che apri nel terminale, il comando claude può farle nascere in background. Si accende con: sh \"$nascita\" metti (per non sentirtelo riproporre: sh \"$nascita\" no)"
  fi
  # Una funzione claude della persona vince sul blocco, e PowerShell con la policy Restricted non legge
  # il profilo: va detto, o la nascita resta spenta senza motivo.
  printf '%s\n' "$stato_nascita" | while IFS= read -r riga; do
    case "$riga" in
      "funzione "*.ps1) say "HERDR NASCITA FUNZIONE: in ${riga#funzione } c'è già una funzione claude, che vince sul blocco di Volta. Perché le sessioni nascano in background, falla finire con & '$(percorso "$app_home/volta-claude.ps1")' @args al posto della chiamata a claude.exe." ;;
      "funzione "*) say "HERDR NASCITA FUNZIONE: in ${riga#funzione } c'è già una funzione claude, che vince sul blocco di Volta. Perché le sessioni nascano in background, falla finire con \"$(percorso "$app_home/volta-claude")\" \"\$@\" al posto di command claude \"\$@\"." ;;
      "policy "*) f=${riga#policy }; say "HERDR NASCITA POLICY: PowerShell non legge il profilo ${f% *} (ExecutionPolicy ${f##* }), quindi il blocco di Volta non parte. Si sblocca, se lo scegli, con: Set-ExecutionPolicy -Scope CurrentUser RemoteSigned" ;;
      "utf16 "*) say "HERDR NASCITA UTF16: il profilo ${riga#utf16 } è salvato in UTF-16 e il blocco di Volta non lo tocca. Risalvalo in UTF-8 per accendere la nascita." ;;
    esac
  done
  # Il servizio di Claude fisso (#5208): senza, il primo claude --bg lo accende a tempo, e da ssh o da
  # hc exec nasce nel posto sbagliato. Su Windows un'attività all'accesso, sul Mac il LaunchAgent di
  # servizi-gui.sh, che vuole prima l'accesso di claude a Documenti: qui lo si propone soltanto, e /setup
  # sa cosa farne (shared/setup-herdr.md). I due nomi sono quelli di servizio-claude.ps1 e servizi-gui.sh
  # (banco HZ43).
  if [ "$sistema" = windows ]; then
    cp "$qui/servizio-claude.ps1" "$app_home/servizio-claude.ps1"
    if ! MSYS_NO_PATHCONV=1 schtasks /query /tn ArturoServizioClaude >/dev/null 2>&1; then
      say "HERDR SERVIZIO: perché le sessioni in background non muoiano con chi le fa nascere, il servizio di Claude può partire a ogni accesso. Si accende con: powershell -NoProfile -ExecutionPolicy Bypass -File \"$(percorso "$app_home/servizio-claude.ps1")\""
    fi
  elif [ ! -f "$HOME/Library/LaunchAgents/org.stellakamikaze.arturo.claude-daemon.plist" ]; then
    say "HERDR SERVIZIO: perché le sessioni in background non muoiano con chi le fa nascere, il servizio di Claude può partire a ogni login. Dai a claude l'accesso a Documenti (Impostazioni di Sistema, Privacy e sicurezza, File e cartelle), poi: sh \"$qui/servizi-gui.sh\" --launchd"
  fi
fi

# 6. Controllo del mod e apertura.
if command -v herdr-app >/dev/null 2>&1 && [ -z "${ARTURO_HERDR_INSTALLER:-}" ]; then
  herdr-app check "$app_home/mods/arturo" >/dev/null || { say "HERDR ERRORE: il mod di Arturo non si carica (herdr-app check)."; exit 1; }
fi
if [ "${ARTURO_HERDR_NON_APRIRE:-0}" != 1 ]; then
  if [ "$sistema" = mac-arm ]; then
    if [ -n "$app_arturo" ]; then open "$app_arturo" 2>/dev/null || true
    else open -a Herdr 2>/dev/null || open "$HOME/Applications/Herdr.app" 2>/dev/null || true; fi
  fi
fi
say "HERDR OK: Herdr è pronto col layout di Arturo."
