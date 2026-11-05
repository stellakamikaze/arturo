#!/usr/bin/env bash
# banco.sh: banco di prova di `scrape`, senza rete. Un server locale serve quattro pagine:
# una vera, una con la verifica anti-bot, un 403 e un 404. Rilancialo prima di cambiare
# i criteri (frasi di CHALLENGE, tabella BLOCCO).
#
#   bash ~/.claude/tools/scrapling/banco.sh
#
# Usa il Python del venv di setup.sh. SCRAPE_PYTHON=<python> ne prova un altro con Scrapling.
# Exit 0 tutti i casi verdi, 1 almeno un caso rosso, 3 Scrapling non installato.
set -u
QUI="$(cd "$(dirname "$0")" && pwd)"
PY="${SCRAPE_PYTHON:-}"
if [ -z "$PY" ]; then
  for c in "$QUI/.venv/bin/python" "$QUI/.venv/Scripts/python.exe"; do [ -x "$c" ] && PY="$c" && break; done
fi
[ -n "$PY" ] && "$PY" -c 'import scrapling' >/dev/null 2>&1 || { echo "Scrapling non installato: lancia prima setup.sh"; exit 3; }

LAVORO="$(mktemp -d "${TMPDIR:-/tmp}/banco-scrape.XXXXXX")" || exit 3
trap 'kill "$SRV" 2>/dev/null; rm -rf "$LAVORO"' EXIT INT TERM

python3 - "$LAVORO/porta" <<'PY' &
import http.server, sys
PAGINE = {
    "/vera": (200, "<html><head><title>Bandi aperti</title></head><body><main><h1>Bandi aperti</h1><p>Contributi per la cultura, scadenza a marzo.</p></main></body></html>"),
    "/verifica": (200, "<html><head><title>Just a moment...</title></head><body>Checking your browser before accessing.</body></html>"),
    "/vietata": (403, "<html><body>Forbidden</body></html>"),
}
class H(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/chi":  # rimanda indietro le intestazioni: niente impronta di browser
            corpo = "<html><body><main><p>UA=%s REFERER=%s</p></main></body></html>" % (
                self.headers.get("User-Agent"), self.headers.get("Referer"))
            status = 200
        else:
            status, corpo = PAGINE.get(self.path, (404, "<html><body>Not found</body></html>"))
        dati = corpo.encode()
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(dati)))
        self.end_headers()
        self.wfile.write(dati)
    def log_message(self, *a):
        pass
srv = http.server.HTTPServer(("127.0.0.1", 0), H)
open(sys.argv[1], "w").write(str(srv.server_address[1]))
srv.serve_forever()
PY
SRV=$!
i=0; while [ ! -s "$LAVORO/porta" ] && [ $i -lt 50 ]; do sleep 0.1; i=$((i+1)); done
[ -s "$LAVORO/porta" ] || { echo "banco guasto: il server locale non parte"; exit 3; }
BASE="http://127.0.0.1:$(cat "$LAVORO/porta")"

n=0; ko=0
caso() {  # nome, exit atteso, testo atteso nell'output, argomenti di scrape
  local nome="$1" atteso="$2" testo="$3"; shift 3; n=$((n+1))
  "$PY" -B "$QUI/scrape.py" "$@" >"$LAVORO/out" 2>&1 </dev/null; echo $? >"$LAVORO/rc"
  local rc; rc=$(cat "$LAVORO/rc")
  if [ "$rc" = "$atteso" ] && grep -qF -- "$testo" "$LAVORO/out"; then echo "  VERDE  $nome"
  else ko=$((ko+1)); echo "  ROSSO  $nome (exit $rc, atteso $atteso)"; sed 's/^/         /' "$LAVORO/out" | tail -3; fi
}
caso "una pagina vera si legge in markdown" 0 "Contributi per la cultura" "$BASE/vera" --md -q
caso "--sel estrae solo il nodo" 0 "Bandi aperti" "$BASE/vera" --sel h1 -q
caso "VELENO: una pagina di verifica anti-bot è un blocco" 3 "browser" "$BASE/verifica" --md -q
caso "VELENO: un 403 è un blocco e consiglia il browser" 3 "browser" "$BASE/vietata" --md -q
caso "un 404 non è un blocco" 2 "status 404" "$BASE/manca" --md -q
caso "si presenta come scrape, senza referer finto" 0 "UA=Mozilla/5.0 (compatible; scrape/1.0" "$BASE/chi" --text -q
grep -q "REFERER=None" "$LAVORO/out" || { ko=$((ko+1)); echo "  ROSSO  la richiesta porta un referer: $(cat "$LAVORO/out")"; }

echo; echo "  totale casi: $n · rossi: $ko"
[ "$ko" -eq 0 ]
