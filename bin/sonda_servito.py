#!/usr/bin/env python3
"""sonda_servito.py: dopo un deploy, il file servito coincide con quello locale?

Un deploy riuscito (exit 0, servizio attivo, risposta 200) non prova che giri il codice nuovo:
la stessa risposta arriva anche dalla versione vecchia. Questa sonda confronta lo sha256 di ogni
file locale con quello che il server restituisce, e riprova finché la versione nuova non risponde.

Uso:
    sonda_servito.py --base URL [--attesa 60] FILE_LOCALE[=PERCORSO_URL] ...
        FILE_LOCALE=PERCORSO_URL confronta il file con BASE/PERCORSO_URL. Senza «=», usa il nome
        del file. Esempio: sonda_servito.py --base https://esempio.org web/index.html= web/app.js
    sonda_servito.py --selftest

Exit: 0 tutti uguali · 1 almeno un file diverso o assente (404) allo scadere dell'attesa
      · 3 sonda non valida: l'URL risponde 3xx, 401 o 403, cioè misura un login e non il sito.
"""
import argparse
import hashlib
import os
import ssl
import sys
import time
import urllib.error
import urllib.request


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *a, **k):
        return None


def scarica(url, timeout=15):
    """(status, corpo). I redirect non si seguono: un 302 verso il login è un esito, non un passo."""
    op = urllib.request.build_opener(_NoRedirect, urllib.request.HTTPSHandler(context=ssl.create_default_context()))
    req = urllib.request.Request(url, headers={"Cache-Control": "no-cache", "User-Agent": "sonda-servito"})
    try:
        with op.open(req, timeout=timeout) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, b""
    except (urllib.error.URLError, OSError) as e:
        return 0, str(e).encode()


def sha(b):
    return hashlib.sha256(b).hexdigest()


def sonda(base, coppie, attesa=60, passo=5):
    """coppie: [(file_locale, percorso_url)]. Ritorna (exit, righe)."""
    locali = {f: sha(open(f, "rb").read()) for f, _ in coppie}
    fine = time.monotonic() + attesa
    while True:
        righe, diversi = [], 0
        for f, p in coppie:
            url = base.rstrip("/") + "/" + p.lstrip("/")
            st, corpo = scarica(url)
            if st in (301, 302, 303, 307, 308, 401, 403):
                return 3, [f"SONDA NON VALIDA {url}: HTTP {st}, risponde il login e non il sito"]
            if st == 200 and sha(corpo) == locali[f]:
                righe.append(f"UGUALE  {f} = {url}")
            else:
                diversi += 1
                stato = f"HTTP {st}" if st != 200 else f"sha servito {sha(corpo)[:12]} ≠ locale {locali[f][:12]}"
                righe.append(f"DIVERSO {f} ≠ {url} ({stato})")
        if not diversi or time.monotonic() >= fine:
            return (0 if not diversi else 1), righe
        time.sleep(passo)


def _selftest():
    import http.server
    import tempfile
    import threading
    d = tempfile.mkdtemp(prefix="sonda-servito-")
    open(os.path.join(d, "a.js"), "w").write("console.log('nuovo')\n")
    loc_uguale = os.path.join(d, "uguale.js")
    open(loc_uguale, "w").write("console.log('nuovo')\n")
    loc_vecchio = os.path.join(d, "vecchio.js")
    open(loc_vecchio, "w").write("console.log('vecchio')\n")

    class H(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *a, **k):
            super().__init__(*a, directory=d, **k)

        def do_GET(self):
            if self.path == "/login":
                self.send_response(302)
                self.send_header("Location", "/accedi")
                self.end_headers()
                return
            super().do_GET()

        def log_message(self, *a):
            pass

    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), H)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{srv.server_address[1]}"
    casi = [
        ("file uguale al servito: 0", sonda(base, [(loc_uguale, "a.js")], attesa=0)[0] == 0),
        ("VELENO: file locale diverso dal servito: 1", sonda(base, [(loc_vecchio, "a.js")], attesa=0)[0] == 1),
        ("VELENO: file assente sul server (404): 1", sonda(base, [(loc_uguale, "manca.js")], attesa=0)[0] == 1),
        ("VELENO: redirect al login: 3", sonda(base, [(loc_uguale, "login")], attesa=0)[0] == 3),
    ]
    srv.shutdown()
    import shutil
    shutil.rmtree(d, ignore_errors=True)
    ko = 0
    for nome, ok in casi:
        ko += not ok
        print(("VERDE " if ok else "ROSSO ") + nome)
    print(f"totale casi: {len(casi)} · rossi: {ko}")
    return 1 if ko else 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--base")
    ap.add_argument("--attesa", type=int, default=60)
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("file", nargs="*")
    a = ap.parse_args(argv)
    if a.selftest:
        return _selftest()
    if not a.base or not a.file:
        ap.error("servono --base e almeno un file")
    coppie = []
    for x in a.file:
        f, _, p = x.partition("=")
        coppie.append((f, p if "=" in x else os.path.basename(f)))
    rc, righe = sonda(a.base, coppie, a.attesa)
    print("\n".join(righe))
    print({0: "SERVITO = LOCALE", 1: "SERVITO DIVERSO: il deploy non è arrivato", 3: "SONDA NON VALIDA"}[rc])
    return rc


if __name__ == "__main__":
    sys.exit(main())
