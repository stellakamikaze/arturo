#!/usr/bin/env bash
# Pubblica sito/ di un commit sul server della landing, nel container arturo-sito (23/10/2026).
# Il server lo dice ARTURO_SITO_HOST, un nome di ssh: il ramo è pubblico e non lo scrive.
#
#   strumenti/pubblica.sh prepara <commit>   carica sito/ in _arrivo-<commit> e mostra cosa cambia
#   strumenti/pubblica.sh applica <commit>   backup, copia, prova del servito, poi toglie _arrivo
#
# Fra i due passi si legge il diff: deve elencare solo i file attesi. Il pacchetto viene da
# `git archive`, quindi un file non committato non va mai online. Il container monta html/ per
# percorso: la cartella non si rinomina, si copia dentro. I *.json di html/ li scrive il server e
# restano. Il passo applica toglie la sua _arrivo solo dopo che html/ è identico al pacchetto e gli
# hash nel container tornano: Federico, 23/10/2026, "procedi su tutto" sulla pulizia del deploy.
set -euo pipefail

HOST=${ARTURO_SITO_HOST:?Scrivi in ARTURO_SITO_HOST il nome ssh del server della landing}
BASE=/mnt/user/appdata/arturo-sito
RADICE=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)

uso() { echo "Uso: $0 prepara|applica <commit>" >&2; exit 2; }
[[ $# -eq 2 ]] || uso
passo=$1
commit=$(git -C "$RADICE" rev-parse --short=7 --verify "$2^{commit}" 2>/dev/null) || { echo "Non trovo il commit $2" >&2; exit 2; }
git -C "$RADICE" cat-file -e "$commit:sito" 2>/dev/null || { echo "Il commit $commit non ha sito/" >&2; exit 2; }
arrivo="$BASE/_arrivo-$commit"

case "$passo" in
  prepara)
    # Senza core.autocrlf=false, da Windows git archive scrive i fine riga CRLF: il 31/10/2026 il
    # pacchetto di 58d4cad aveva 28 file diversi dal servito invece di 4.
    git -C "$RADICE" -c core.autocrlf=false archive "$commit" sito | ssh "$HOST" "rm -rf '$arrivo' && mkdir -p '$arrivo' && tar -x -C '$arrivo'"
    echo "Caricato in $arrivo. Cosa cambia rispetto al servito (i *.json del server restano):"
    ssh "$HOST" "cd '$BASE' && diff -rq -x '*.json' html '_arrivo-$commit/sito'" || true
    echo "Se l'elenco è quello atteso: $0 applica $commit"
    ;;
  applica)
    ssh "$HOST" "test -d '$arrivo/sito'" || { echo "Manca $arrivo: lancia prima $0 prepara $commit" >&2; exit 1; }
    backup="backup-$(date +%Y-%m-%d-%H%M%S)-html-prima-di-$commit"
    # Un nome che c'è già farebbe copiare html/ dentro il backup vecchio: si ferma prima.
    ssh "$HOST" "cd '$BASE' && test ! -e '$backup' && cp -a html '$backup' && diff -rq html '$backup' >/dev/null" \
      || { echo "Il backup $backup non è uguale a html/: mi fermo prima di copiare" >&2; exit 1; }
    ssh "$HOST" "cd '$BASE' && rsync -a --delete --exclude '*.json' '_arrivo-$commit/sito/' html/ && diff -rq -x '*.json' html '_arrivo-$commit/sito'" \
      || { echo "html/ non è uguale al pacchetto dopo la copia: $arrivo resta per guardarci" >&2; exit 1; }
    # La prova del servito: gli hash di ogni file del commit, letti dentro il container.
    tmp=$(mktemp -d)
    git -C "$RADICE" -c core.autocrlf=false archive "$commit" sito | tar -x -C "$tmp"
    hash=$(cd "$tmp/sito" && find . -type f ! -name '*.json' -print0 | xargs -0 shasum -a 256 | sed 's#  \./#  /usr/share/nginx/html/#')
    rm -rf "$tmp"
    # sha256sum del container è quello di BusyBox: niente --quiet, le righe giuste finiscono con ": OK".
    fuori=$(printf '%s\n' "$hash" | ssh "$HOST" "docker exec -i arturo-sito sha256sum -c" 2>&1) \
      || { echo "Il servito non ha gli hash del commit: $arrivo resta" >&2; printf '%s\n' "$fuori" | grep -v ': OK$' >&2; exit 1; }
    n=$(printf '%s\n' "$hash" | grep -c .)
    [[ "$arrivo" =~ ^$BASE/_arrivo-[0-9a-f]{7,40}$ ]] || { echo "Percorso inatteso: $arrivo" >&2; exit 1; }
    ssh "$HOST" "rm -rf '$arrivo'"
    echo "Pubblicato $commit: $n file con gli hash giusti nel container. Backup in $BASE/$backup, $arrivo tolta."
    ;;
  *) uso ;;
esac
