#!/bin/sh
# Arturo.app: Herdr col nome e l'icona di Arturo, accanto a Herdr.app (solo macOS, #5002, 9/11/2026).
#
#   arturo-app.sh            crea Arturo.app, o la riallinea se un aggiornamento le ha ridato il nome di Herdr
#   arturo-app.sh --agente   in più installa il LaunchAgent che la riallinea da solo
#
# Perché una copia. Herdr.app è firmato da chi lo fa: cambiarne il nome rompe la firma, e l'aggiornamento
# lo rimetterebbe com'era. Arturo.app è una copia firmata in locale, con nome, identificativo e icona suoi.
# Herdr la aggiorna da sé come aggiorna Herdr.app: sostituisce il pacchetto intero, quindi dopo un
# aggiornamento Arturo.app si chiama di nuovo Herdr (provato l'8/11/2026 con la 0.1.13 portata alla
# 0.1.14 dal server vero). Il LaunchAgent guarda i due Info.plist e rilancia questo script, che parte
# dalla copia più nuova delle due. Il prezzo: macOS lega i permessi (microfono, automazione) alla firma,
# e una firma locale cambia a ogni aggiornamento, quindi li richiede.
#
# La firma: con l'identità "Arturo firma locale" nel portachiavi (la crea firma-locale.sh, #5012) Arturo.app
# tiene la stessa identità da un aggiornamento all'altro e macOS ricorda i permessi; senza, firma ad hoc.
#   arturo-app.sh --firma    rifirma Arturo.app anche se è già a posto (dopo firma-locale.sh)
#
# Variabili per i banchi: ARTURO_HERDR_APP (Herdr.app), ARTURO_APP (Arturo.app), ARTURO_APP_AGENTI
# (cartella dei LaunchAgent), ARTURO_APP_NO_LAUNCHCTL=1, ARTURO_APP_FIRMA=adhoc (niente portachiavi).
set -eu

qui=$(cd "$(dirname "$0")" && pwd)
herdr=${ARTURO_HERDR_APP:-$HOME/Applications/Herdr.app}
arturo=${ARTURO_APP:-$HOME/Applications/Arturo.app}
ID=org.stellakamikaze.arturo
IDENTITA="Arturo firma locale"
say() { printf '%s\n' "$*"; }

[ "$(uname -s)" = Darwin ] || { say "ARTURO APP NO: serve solo su macOS."; exit 0; }

campo() { /usr/libexec/PlistBuddy -c "Print :$2" "$1/Contents/Info.plist" 2>/dev/null || true; }
# 0 se la versione $1 è più nuova di $2.
piu_nuova() {
  python3 -c 'import sys
v = lambda s: tuple(int(x) if x.isdigit() else 0 for x in s.split("."))
sys.exit(0 if v(sys.argv[1]) > v(sys.argv[2]) else 1)' "$1" "$2"
}

# L'icona nasce dallo SVG con gli strumenti di macOS (Quick Look, sips, iconutil): un .icns nel repository
# fa rosso l'igiene, perché i suoi byte compressi possono contenere per caso un nome privato.
# Il disegno riempie il quadrato: dal 2025 macOS dà da sé la forma arrotondata alle icone.
icona() {
  t=$(mktemp -d)
  qlmanage -t -s 1024 -o "$t" "$qui/arturo-icona.svg" >/dev/null 2>&1 || { rm -rf "$t"; return 1; }
  png="$t/arturo-icona.svg.png"
  [ -f "$png" ] || { rm -rf "$t"; return 1; }
  mkdir -p "$t/Arturo.iconset"
  for s in 16 32 128 256 512; do
    sips -z $s $s "$png" --out "$t/Arturo.iconset/icon_${s}x${s}.png" >/dev/null 2>&1
    sips -z $((s * 2)) $((s * 2)) "$png" --out "$t/Arturo.iconset/icon_${s}x${s}@2x.png" >/dev/null 2>&1
  done
  iconutil -c icns "$t/Arturo.iconset" -o "$1" 2>/dev/null
  r=$?
  rm -rf "$t"
  return $r
}

# L'identità con cui firmare: quella locale se è valida nel portachiavi, altrimenti ad hoc ("-").
identita() {
  if [ "${ARTURO_APP_FIRMA:-}" != adhoc ] && security find-identity -v -p codesigning 2>/dev/null | grep -q "\"$IDENTITA\""; then
    printf '%s' "$IDENTITA"
  else
    printf '%s' -
  fi
}
# 0 se Arturo.app è firmata come vuole identita(): ad hoc, o con l'identità locale.
firmata_bene() {
  autorita=$(codesign -dv --verbose=2 "$arturo" 2>&1 | sed -n 's/^Authority=//p' | head -1)
  if [ "$(identita)" = - ]; then [ -z "$autorita" ]; else [ "$autorita" = "$IDENTITA" ]; fi
}

riallinea() {
  if [ ! -d "$herdr" ] && [ ! -d "$arturo" ]; then
    say "ARTURO APP NO: non trovo Herdr.app ($herdr)."
    return 0
  fi
  v_herdr=$(campo "$herdr" CFBundleShortVersionString)
  v_arturo=$(campo "$arturo" CFBundleShortVersionString)
  # Si parte dalla copia più nuova: Herdr.app aggiornato dall'installer, o Arturo.app aggiornata da sé.
  base=$herdr
  if [ -d "$arturo" ] && { [ ! -d "$herdr" ] || ! piu_nuova "$v_herdr" "$v_arturo"; }; then base=$arturo; fi
  if [ "$base" = "$arturo" ] && [ "$(campo "$arturo" CFBundleIdentifier)" = "$ID" ] && [ "${FIRMA:-0}" != 1 ] && firmata_bene; then
    say "ARTURO APP OK: Arturo.app $v_arturo è già a posto."
    return 0
  fi
  nuova="$arturo.arturo-nuova"
  rm -rf "$nuova"
  ditto "$base" "$nuova"
  /usr/libexec/PlistBuddy \
    -c "Set :CFBundleName Arturo" \
    -c "Set :CFBundleDisplayName Arturo" \
    -c "Set :CFBundleIdentifier $ID" \
    -c "Set :CFBundleIconFile Arturo" \
    "$nuova/Contents/Info.plist"
  icona "$nuova/Contents/Resources/Arturo.icns" || say "Arturo.app resta con l'icona di Herdr: non sono riuscito a disegnare la sua."
  chi=$(identita)
  codesign --force --deep --sign "$chi" "$nuova" >/dev/null 2>&1 \
    || { [ "$chi" != - ] && say "Firma con \"$IDENTITA\" non riuscita: firmo ad hoc." && codesign --force --deep --sign - "$nuova" >/dev/null 2>&1; } \
    || { rm -rf "$nuova"; say "ARTURO APP ERRORE: firma locale non riuscita."; exit 1; }
  # Lo scambio: la copia vecchia esce solo quando la nuova è pronta.
  if [ -d "$arturo" ]; then mv "$arturo" "$arturo.arturo-prima"; fi
  mv "$nuova" "$arturo"
  rm -rf "$arturo.arturo-prima"
  touch "$arturo"
  lsregister=/System/Library/Frameworks/CoreServices.framework/Frameworks/LaunchServices.framework/Support/lsregister
  [ -x "$lsregister" ] && "$lsregister" -f "$arturo" >/dev/null 2>&1 || true
  say "ARTURO APP OK: Arturo.app $(campo "$arturo" CFBundleShortVersionString) pronta in $arturo."
}

agente() {
  cartella=${ARTURO_APP_AGENTI:-$HOME/Library/LaunchAgents}
  plist="$cartella/$ID-app.plist"
  mkdir -p "$cartella"
  python3 - "$plist" "$qui/arturo-app.sh" "$herdr" "$arturo" <<'PY'
import plistlib, sys
plist, script, herdr, arturo = sys.argv[1:]
dati = {
    "Label": "org.stellakamikaze.arturo-app",
    "ProgramArguments": ["/bin/sh", script],
    # Un aggiornamento riscrive uno dei due Info.plist; l'ora è la rete se il pacchetto sostituito sfugge.
    "WatchPaths": [herdr + "/Contents/Info.plist", arturo + "/Contents/Info.plist"],
    "StartInterval": 3600,
    "RunAtLoad": True,
    "StandardOutPath": "/tmp/arturo-app.log",
    "StandardErrorPath": "/tmp/arturo-app.log",
}
with open(plist, "wb") as f:
    plistlib.dump(dati, f)
PY
  if [ "${ARTURO_APP_NO_LAUNCHCTL:-0}" != 1 ]; then
    launchctl bootout "gui/$(id -u)/org.stellakamikaze.arturo-app" 2>/dev/null || true
    launchctl bootstrap "gui/$(id -u)" "$plist"
  fi
  say "ARTURO APP OK: il LaunchAgent rimette il nome dopo ogni aggiornamento ($plist)."
}

FIRMA=0
[ "${1:-}" = --firma ] && FIRMA=1
riallinea
[ "${1:-}" = --agente ] && agente
exit 0
