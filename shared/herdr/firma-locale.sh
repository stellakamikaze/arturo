#!/bin/sh
# Un'identità di firma locale per Arturo.app, "Arturo firma locale" (solo macOS, #5012, 9/11/2026).
#
# Perché. Arturo.app è una copia di Herdr.app firmata in locale (arturo-app.sh). Con la firma ad hoc
# l'identità cambia a ogni aggiornamento di Herdr, e macOS richiede i permessi (Documenti, microfono).
# Con un certificato locale l'identità resta la stessa: macOS li chiede una volta sola.
#
# Lo lancia la persona, nel suo Terminale: aggiunge un certificato al portachiavi login e lo segna come
# affidabile per la firma del codice, e macOS chiede la password del Mac. Claude non lo lancia: la
# fiducia in un certificato è un'impostazione di sicurezza.
# Il certificato vale solo su questo Mac e solo per firmare codice. Si toglie da Accesso Portachiavi
# (voce "Arturo firma locale"); arturo-app.sh torna allora alla firma ad hoc.
set -eu

NOME="Arturo firma locale"
qui=$(cd "$(dirname "$0")" && pwd)
say() { printf '%s\n' "$*"; }
[ "$(uname -s)" = Darwin ] || { say "Serve solo su macOS."; exit 0; }

if security find-identity -v -p codesigning | grep -q "\"$NOME\""; then
  say "L'identità \"$NOME\" c'è già."
else
  t=$(mktemp -d)
  chmod 700 "$t"
  trap 'rm -rf "$t"' EXIT
  cat > "$t/cert.cnf" <<EOF
[req]
distinguished_name = dn
x509_extensions = ext
prompt = no
[dn]
CN = $NOME
[ext]
basicConstraints = critical,CA:false
keyUsage = critical,digitalSignature
extendedKeyUsage = critical,codeSigning
EOF
  openssl req -x509 -newkey rsa:2048 -nodes -keyout "$t/k.pem" -out "$t/c.pem" -days 3650 -config "$t/cert.cnf" 2>/dev/null
  pw=$(openssl rand -hex 16)
  openssl pkcs12 -export -legacy -inkey "$t/k.pem" -in "$t/c.pem" -name "$NOME" -out "$t/id.p12" -passout "pass:$pw" 2>/dev/null \
    || openssl pkcs12 -export -inkey "$t/k.pem" -in "$t/c.pem" -name "$NOME" -out "$t/id.p12" -passout "pass:$pw"
  portachiavi="$HOME/Library/Keychains/login.keychain-db"
  security import "$t/id.p12" -k "$portachiavi" -P "$pw" -T /usr/bin/codesign >/dev/null
  say "Certificato aggiunto al portachiavi. Ora macOS chiede la password per segnarlo come affidabile."
  security add-trusted-cert -r trustRoot -p codeSign -k "$portachiavi" "$t/c.pem"
  say "Ora la password del Mac una seconda volta: serve perché la firma riparta da sola dopo ogni aggiornamento."
  printf 'Password del Mac (non si vede mentre scrivi): '
  stty -echo; read -r pwmac; stty echo; printf '\n'
  security set-key-partition-list -S apple-tool:,apple:,codesign: -s -k "$pwmac" -l "$NOME" "$portachiavi" >/dev/null 2>&1 \
    || say "Attenzione: il permesso per codesign non è passato. Al primo aggiornamento macOS ti chiederà di consentire l'accesso alla chiave: scegli Consenti sempre."
  pwmac=""
  security find-identity -v -p codesigning | grep -q "\"$NOME\"" || { say "L'identità non risulta valida: Arturo.app resta con la firma ad hoc."; exit 1; }
  say "Identità \"$NOME\" pronta."
fi
sh "$qui/arturo-app.sh" --firma
