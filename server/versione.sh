#!/usr/bin/env bash
# versione.sh: la versione del codice del server (revisione del 22/11/2026, A4). È lo sha dell'ultimo commit che
# tocca i file che finiscono nel Worker o nel D1: i moduli .js, schema.sql e migrazioni/. Test, README e
# wrangler.toml coi segnaposto non contano.
# Il deploy la passa al Worker come VERSIONE_SERVER, e GET / la dice. firma-rilascio-arturo.sh la confronta col
# commit del rilascio, e si ferma se il rilascio porta un server/ più nuovo del Worker.
#
#   bash server/versione.sh [rev]      lo sha corto (12 caratteri) per rev, di serie HEAD
#   bash server/versione.sh --percorsi i percorsi che contano, uno per riga (per git diff e git log)
set -euo pipefail
PERCORSI=('server/*.js' server/schema.sql server/migrazioni)
if [ "${1:-}" = --percorsi ]; then printf '%s\n' "${PERCORSI[@]}"; exit 0; fi
cd "$(dirname "$0")/.."
SHA=$(git log -1 --format=%H "${1:-HEAD}" -- "${PERCORSI[@]}")
[ -n "$SHA" ] || { echo "versione.sh: nessun commit tocca il server in ${1:-HEAD}" >&2; exit 1; }
echo "${SHA:0:12}"
