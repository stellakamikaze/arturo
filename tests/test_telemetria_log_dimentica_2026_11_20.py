#!/usr/bin/env python3
"""SD01-SD05: il resto dello sportello lato client (20/11/2026, #4793; piano della telemetria del 24/10/2026, F3).

La persona vede cosa partirebbe senza mandarlo (ARTURO_TELEMETRIA=log), vede gli ultimi lotti partiti davvero e
cancella da sola i suoi dati dal server (`arturo telemetria dimentica`, POST /v1/dimentica). Il server finto risponde
come server/logica.js; il server vero lo provano V66 (server/test.mjs) e Q25 (server/test-sql.mjs).

SD01 in modo log `invia` non tocca la rete, nemmeno prima della risposta di /setup: stampa il lotto, lo scrive in
     data/telemetria/lotti/ con inviato false e svuota la coda. `stato` dice il modo log.
SD02 in modo normale ogni lotto partito lascia una copia con inviato true, e la cartella tiene solo gli ultimi 10;
     `mostra` dice dove stanno.
SD03 `dimentica` manda l'id della installazione a /v1/dimentica, anche con la telemetria spenta; col 200 dice quanto ha
     cancellato, toglie l'id e svuota la coda.
SD04 `dimentica` col server giù esce 1 e tiene l'id, così si riprova; senza un id non chiama il server.
SD05 bin/arturo, docs/privacy.md e server/README.md raccontano dimentica e il modo log.

Sulla base 0cc681e ogni controllo fallisce con un AssertionError che comincia con il suo codice.
Con --avvelena tre copie rotte del repository fanno rosso il caso che le sorvegliano.
"""
from __future__ import annotations

import argparse
import atexit
import http.server
import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
from pathlib import Path

CASI = ["SD01", "SD02", "SD03", "SD04", "SD05"]


class Server:
    """Risponde come server/logica.js a /v1/eventi e /v1/dimentica, e tiene ogni richiesta."""

    def __init__(self, status_dimentica: int = 200):
        self.richieste = []
        fuori = self

        class Gestore(http.server.BaseHTTPRequestHandler):
            def _rispondi(self, status, dati):
                corpo = json.dumps(dati).encode("utf-8")
                self.send_response(status)
                self.send_header("content-type", "application/json")
                self.send_header("content-length", str(len(corpo)))
                self.end_headers()
                self.wfile.write(corpo)

            def do_GET(self):  # noqa: N802
                fuori.richieste.append({"metodo": "GET", "percorso": self.path, "corpo": {}})
                return self._rispondi(404, {})

            def do_POST(self):  # noqa: N802
                n = int(self.headers.get("content-length") or 0)
                corpo = json.loads(self.rfile.read(n) or b"{}") if n else {}
                fuori.richieste.append({"metodo": "POST", "percorso": self.path, "corpo": corpo})
                if self.path == "/v1/eventi":
                    return self._rispondi(202, {"accettati": len(corpo.get("eventi") or [])})
                if self.path == "/v1/dimentica":
                    return self._rispondi(status_dimentica, {"eventi": 5, "segnalazioni": 1})
                return self._rispondi(404, {})

            def log_message(self, *_):
                pass

        self.http = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Gestore)
        threading.Thread(target=self.http.serve_forever, daemon=True).start()
        self.url = f"http://127.0.0.1:{self.http.server_address[1]}"
        atexit.register(self.http.shutdown)

    def a(self, percorso: str) -> list:
        return [r for r in self.richieste if r["percorso"] == percorso]


class Lab:
    def __init__(self, repo: Path, server: Server | None = None, **env):
        self.repo = repo
        self.dir = Path(tempfile.mkdtemp(prefix="arturo-sd."))
        atexit.register(shutil.rmtree, self.dir, True)
        self.home = self.dir / "home"
        self.claude = self.home / ".claude"
        self.claude.mkdir(parents=True)
        for nome in ("bin", "hooks", "commands"):
            try:
                os.symlink(repo / nome, self.claude / nome)
            except OSError:
                shutil.copytree(repo / nome, self.claude / nome)
        self.env = dict(os.environ, HOME=str(self.home), USERPROFILE=str(self.home),
                        ARTURO_TELEMETRIA_URL=server.url if server else "http://127.0.0.1:9")
        for chiave in ("ARTURO_TELEMETRIA", "DO_NOT_TRACK", "ARTURO_OGGI"):
            self.env.pop(chiave, None)
        self.env.update(env)

    def tel(self, *argomenti: str, **env) -> subprocess.CompletedProcess:
        return subprocess.run([sys.executable, "-B", str(self.repo / "bin" / "telemetria.py"), *argomenti],
                              capture_output=True, text=True, encoding="utf-8", errors="replace",
                              env={**self.env, **env}, timeout=60)

    def stato(self) -> dict:
        f = self.claude / "session-env" / "telemetria.json"
        return json.loads(f.read_text(encoding="utf-8")) if f.exists() else {}

    def coda(self) -> list:
        f = self.claude / "data" / "telemetria" / "coda.jsonl"
        return [r for r in f.read_text(encoding="utf-8").splitlines() if r.strip()] if f.exists() else []

    def lotti(self) -> list:
        d = self.claude / "data" / "telemetria" / "lotti"
        return [json.loads(f.read_text(encoding="utf-8")) for f in sorted(d.glob("*.json"))] if d.is_dir() else []


def sd01(repo: Path) -> None:
    server = Server()
    lab = Lab(repo, server, ARTURO_TELEMETRIA="log")
    for _ in range(3):
        lab.tel("registra", "sessione")
    assert len(lab.coda()) == 3, f"SD01 la coda non si riempie in modo log: {lab.coda()}"
    r = lab.tel("invia")
    assert not server.a("/v1/eventi"), f"SD01 in modo log il lotto parte: {server.a('/v1/eventi')}"
    assert '"evento": "sessione"' in r.stdout, f"SD01 in modo log invia non stampa il lotto: {r.stdout!r}"
    lotti = lab.lotti()
    assert len(lotti) == 1 and lotti[0].get("inviato") is False and len(lotti[0]["lotto"]["eventi"]) == 3, \
        f"SD01 in modo log il lotto non resta nella cartella: {lotti}"
    assert lab.coda() == [], f"SD01 in modo log la coda non si svuota: {lab.coda()}"
    s = lab.tel("stato")
    assert "modo log" in s.stdout, f"SD01 stato non dice il modo log: {s.stdout!r}"


def sd02(repo: Path) -> None:
    server = Server()
    lab = Lab(repo, server)
    lab.tel("accendi")
    for _ in range(12):
        lab.tel("registra", "sessione")
        lab.tel("invia")
    assert len(server.a("/v1/eventi")) == 12, f"SD02 i lotti non partono: {len(server.a('/v1/eventi'))}"
    lotti = lab.lotti()
    assert len(lotti) == 10, f"SD02 la cartella non tiene gli ultimi 10 lotti: {len(lotti)}"
    assert all(x.get("inviato") is True for x in lotti), "SD02 un lotto partito non è segnato inviato"
    m = lab.tel("mostra")
    assert "Ultimi lotti (10" in m.stdout, f"SD02 mostra non dice dove stanno i lotti: {m.stdout!r}"


def sd03(repo: Path) -> None:
    server = Server()
    lab = Lab(repo, server)
    lab.tel("accendi")
    lab.tel("registra", "sessione")
    lab.tel("invia")
    io = lab.stato().get("id")
    assert io, "SD03 l'invio non crea l'id"
    lab.tel("registra", "sessione")
    r = lab.tel("dimentica", ARTURO_TELEMETRIA="0")
    chiamate = server.a("/v1/dimentica")
    assert r.returncode == 0 and chiamate and chiamate[-1]["corpo"] == {"installazione": io}, \
        f"SD03 dimentica non manda l'id, anche con la telemetria spenta: {r.returncode} {chiamate} {r.stderr!r}"
    assert "5 eventi e 1 segnalazioni" in r.stdout, f"SD03 dimentica non dice cosa ha cancellato: {r.stdout!r}"
    assert "id" not in lab.stato(), f"SD03 dopo dimentica l'id resta: {lab.stato()}"
    assert lab.coda() == [], f"SD03 dopo dimentica la coda resta: {lab.coda()}"


def sd04(repo: Path) -> None:
    lab = Lab(repo)
    r = lab.tel("dimentica")
    assert r.returncode == 0 and "non ha ancora un id" in r.stdout, f"SD04 senza id dimentica non lo dice: {r.stdout!r}"
    server = Server(status_dimentica=500)
    lab = Lab(repo, server)
    lab.tel("accendi")
    lab.tel("registra", "sessione")
    lab.tel("invia")
    io = lab.stato().get("id")
    r = lab.tel("dimentica")
    assert r.returncode == 1 and "non riuscita" in r.stderr, f"SD04 un errore del server sembra riuscito: {r.returncode} {r.stderr!r}"
    assert lab.stato().get("id") == io, "SD04 un errore del server toglie l'id"


def sd05(repo: Path) -> None:
    arturo = (repo / "bin" / "arturo").read_text(encoding="utf-8")
    privacy = (repo / "docs" / "privacy.md").read_text(encoding="utf-8")
    server = (repo / "server" / "README.md").read_text(encoding="utf-8")
    assert "dimentica" in arturo, "SD05 l'aiuto di arturo non nomina dimentica"
    assert "arturo telemetria dimentica" in privacy and "ARTURO_TELEMETRIA=log" in privacy, \
        "SD05 la privacy non racconta dimentica e il modo log"
    assert "/v1/dimentica" in server, "SD05 il README del server non racconta /v1/dimentica"


TESTS = {"SD01": sd01, "SD02": sd02, "SD03": sd03, "SD04": sd04, "SD05": sd05}


def prova(repo: Path) -> list:
    rossi = []
    for nome, test in TESTS.items():
        try:
            test(repo)
        except AssertionError as e:
            rossi.append(f"{nome} {e}" if not str(e).startswith(nome) else str(e))
        except Exception as e:  # noqa: BLE001
            rossi.append(f"{nome} errore {type(e).__name__}: {e}")
    return rossi


# caso -> (file, testo, testo rotto, motivo atteso nel rosso)
VELENI = (
    ("SD01", "bin/telemetria.py", "        if log:\n", "        if False:\n", "in modo log il lotto parte"),
    ("SD02", "bin/telemetria.py", "        for vecchio in sorted(cartella.glob(\"*.json\"))[:-LOTTI_TENUTI]:\n",
     "        for vecchio in []:\n", "ultimi 10"),
    ("SD03", "bin/telemetria.py", "        cambia_stato(lambda s: s.pop(\"id\", None) if s.get(\"id\") == io else None)\n", "",
     "l'id resta"),
)


def avvelena(repo: Path) -> int:
    esiti = []
    for caso, rel, giusto, rotto, motivo in VELENI:
        with tempfile.TemporaryDirectory(prefix="arturo-sd-v-") as tmp:
            copia = Path(tmp) / "repo"
            shutil.copytree(repo, copia, ignore=shutil.ignore_patterns(".git", "__pycache__", "node_modules", "tests",
                                                                        "cache", ".claude"))
            testo = (copia / rel).read_text(encoding="utf-8")
            assert testo.count(giusto) == 1, f"veleno {caso}: il testo da rompere non c'è più in {rel}"
            (copia / rel).write_text(testo.replace(giusto, rotto), encoding="utf-8")
            colpiti = [r for r in prova(copia) if r.startswith(caso) and motivo in r]
            if not colpiti:
                print(f"VELENO {caso} NON ATTACCA: atteso {motivo!r}")
                return 1
            print(f"VELENO {caso} ROSSO: {colpiti[0][:120]}")
            esiti.append(caso)
    print(f"VELENI_ROSSI={','.join(esiti)} veleni={len(VELENI)}")
    return 0 if len(esiti) == len(VELENI) else 1


def main() -> int:
    for flusso in (sys.stdout, sys.stderr):
        if hasattr(flusso, "reconfigure"):
            flusso.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument("--baseline-ref")
    parser.add_argument("--avvelena", action="store_true")
    a = parser.parse_args()
    repo = Path(a.repo).resolve()
    if a.avvelena:
        return avvelena(repo)
    rossi = prova(repo)
    if a.baseline_ref:
        codici = sorted({r.split()[0] for r in rossi})
        assert codici == CASI, f"baseline non discriminante: rossi {codici}, attesi {CASI}\n" + "\n".join(rossi)
        print(f"BASELINE_DISCRIMINANTE={','.join(codici)}")
        return 0
    for r in rossi:
        print("ROSSO", r)
    print(("PASS " if not rossi else "") + f"{','.join(TESTS)} verdi {len(CASI) - len(rossi)}/{len(CASI)}")
    return 1 if rossi else 0


if __name__ == "__main__":
    sys.exit(main())
