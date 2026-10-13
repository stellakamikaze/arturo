#!/usr/bin/env python3
"""M01-M10: la telemetria minima di Arturo (bin/telemetria.py) e il canale diretto di /segnala.

Ogni caso gira con una HOME finta e un server HTTP finto su 127.0.0.1 (ARTURO_TELEMETRIA_URL):
niente parte mai verso il server vero. Sulla base db96709, prima della telemetria, ogni controllo
deve fallire per conto suo.
"""
from __future__ import annotations

import argparse
import atexit
import http.server
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path


class Server:
    """Registra ogni POST. `status` decide la risposta; None simula un server spento."""

    def __init__(self):
        self.richieste = []
        self.status = 202
        fuori = self

        class Gestore(http.server.BaseHTTPRequestHandler):
            def do_POST(self):  # noqa: N802
                corpo = self.rfile.read(int(self.headers.get("content-length", 0)))
                fuori.richieste.append((self.path, json.loads(corpo)))
                self.send_response(fuori.status)
                self.end_headers()
                self.wfile.write(b"{}")

            def log_message(self, *_):
                pass

        self.http = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Gestore)
        threading.Thread(target=self.http.serve_forever, daemon=True).start()
        self.url = f"http://127.0.0.1:{self.http.server_address[1]}"
        atexit.register(self.http.shutdown)


class Lab:
    def __init__(self, repo: Path, server: Server | None = None, **env):
        self.repo = repo
        self.dir = Path(tempfile.mkdtemp(prefix="arturo-m."))
        atexit.register(shutil.rmtree, self.dir, True)
        self.home = self.dir / "home"
        (self.home / ".claude").mkdir(parents=True)
        # Gli hook leggono ~/.claude: bin, hooks e commands del repo, come in un'installazione vera.
        for nome in ("bin", "hooks", "commands"):
            os.symlink(repo / nome, self.home / ".claude" / nome)
        self.env = dict(os.environ, HOME=str(self.home), ARTURO_TELEMETRIA_URL=server.url if server else "http://127.0.0.1:9")
        for chiave in ("ARTURO_TELEMETRIA", "DO_NOT_TRACK", "ARTURO_OGGI"):
            self.env.pop(chiave, None)
        self.env.update(env)

    def arturo(self, *argomenti: str) -> subprocess.CompletedProcess:
        return subprocess.run([sys.executable, "-B", str(self.repo / "bin" / "arturo"), *argomenti],
                              capture_output=True, text=True, env=self.env, timeout=60)

    def hook(self, nome: str, stdin: str = "") -> subprocess.CompletedProcess:
        return subprocess.run(["bash", str(self.repo / "hooks" / nome)], input=stdin, capture_output=True, text=True,
                              env=self.env, cwd=str(self.dir), timeout=60)

    def coda(self) -> list:
        f = self.home / ".claude" / "data" / "telemetria" / "coda.jsonl"
        return [json.loads(r) for r in f.read_text(encoding="utf-8").splitlines()] if f.exists() else []

    def stato(self) -> dict:
        f = self.home / ".claude" / "session-env" / "telemetria.json"
        return json.loads(f.read_text(encoding="utf-8")) if f.exists() else {}


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_m01(repo: Path) -> None:
    srv = Server()
    lab = Lab(repo, srv)
    assert lab.arturo("telemetria", "registra", "comando", "fine").returncode == 0
    assert lab.arturo("telemetria", "registra", "sessione").returncode == 0
    assert srv.richieste == [], "M01 registra usa la rete"
    assert [e["evento"] for e in lab.coda()] == ["comando", "sessione"], f"M01 coda: {lab.coda()}"
    r = lab.arturo("telemetria", "invia")
    assert r.returncode == 0 and "Eventi partiti: 2" in r.stdout, f"M01 invia: {r.stdout!r} {r.stderr!r}"
    percorso, lotto = srv.richieste[0]
    assert percorso == "/v1/eventi", f"M01 percorso: {percorso}"
    assert set(lotto) == {"installazione", "versione", "sistema", "eventi"}, f"M01 campi del lotto: {set(lotto)}"
    assert re.fullmatch(r"[0-9a-f-]{36}", lotto["installazione"]), "M01 l'id non è un uuid casuale"
    assert all(set(e) == {"giorno", "evento", "valore"} and re.fullmatch(r"\d{4}-\d{2}-\d{2}", e["giorno"])
               for e in lotto["eventi"]), f"M01 eventi: {lotto['eventi']}"
    assert lab.coda() == [], "M01 la coda non si svuota dopo un 2xx"


def test_m02(repo: Path) -> None:
    srv = Server()
    srv.status = 500
    lab = Lab(repo, srv)
    lab.arturo("telemetria", "registra", "sessione")
    lab.arturo("telemetria", "invia")
    assert len(lab.coda()) == 1, "M02 con un 500 la coda si perde"
    giu = Lab(repo)  # nessun server in ascolto sulla porta 9
    giu.arturo("telemetria", "registra", "sessione")
    inizio = time.time()
    giu.arturo("telemetria", "invia")
    assert len(giu.coda()) == 1 and time.time() - inizio < 20, "M02 con il server giù la coda si perde o invia appende"


def test_m03(repo: Path) -> None:
    srv = Server()
    for env in ({"ARTURO_TELEMETRIA": "0"}, {"DO_NOT_TRACK": "1"}):
        lab = Lab(repo, srv, **env)
        lab.arturo("telemetria", "registra", "sessione")
        lab.arturo("telemetria", "invia")
        assert lab.coda() == [], f"M03 {env} non ferma registra"
        assert "spenta" in lab.arturo("telemetria", "stato").stdout, f"M03 {env}: stato dice accesa"
    lab = Lab(repo, srv)
    lab.arturo("telemetria", "registra", "sessione")
    assert lab.arturo("telemetria", "spegni").returncode == 0
    assert lab.coda() == [], "M03 spegni non svuota la coda"
    lab.arturo("telemetria", "registra", "sessione")
    lab.arturo("telemetria", "invia")
    assert lab.coda() == [] and srv.richieste == [], "M03 dopo spegni qualcosa parte"
    lab.arturo("telemetria", "accendi")
    lab.arturo("telemetria", "registra", "sessione")
    assert len(lab.coda()) == 1, "M03 accendi non riaccende"


def test_m04(repo: Path) -> None:
    lab = Lab(repo)
    for evento, valore in (("prompt", "ciao"), ("comando", "/fine testo privato"), ("comando", "x" * 41),
                           ("guardia", "Block Dangerous"), ("sessione", "qualcosa"), ("aggiorna", "forse")):
        lab.arturo("telemetria", "registra", evento, valore)
    lab.arturo("telemetria", "registra", "aggiorna", "applicato")
    assert [(e["evento"], e["valore"]) for e in lab.coda()] == [("aggiorna", "applicato")], \
        f"M04 entra un evento fuori elenco, o non entra quello valido: {lab.coda()}"


def test_m05(repo: Path) -> None:
    lab = Lab(repo)
    lab.hook("inject-now.sh", json.dumps({"prompt": "/fine nota privata sul cliente Rossi"}))
    lab.hook("inject-now.sh", json.dumps({"prompt": "scrivimi una email a Rossi"}))
    lab.hook("inject-now.sh", json.dumps({"prompt": "/comandoinesistente"}))
    assert lab.coda() and [(e["evento"], e["valore"]) for e in lab.coda()] == [("comando", "fine")], \
        f"M05 inject-now registra altro: {lab.coda()}"
    assert "Rossi" not in json.dumps(lab.coda()), "M05 il testo del prompt finisce in coda"


def test_m06(repo: Path) -> None:
    lab = Lab(repo)
    # Un invio che comms-guard nega sempre (banco del 30/9): la guardia blocca, il comando non parte.
    entrata = {"tool_name": "Bash", "tool_input": {"command": "open 'mailto:rossi@example.com?subject=Documents'"}}
    r = lab.hook("bash-dispatcher.sh", json.dumps(entrata))
    bloccato = r.returncode == 2 or '"deny"' in r.stdout
    assert bloccato, f"M06 il comando di prova non è bloccato: {r.returncode} {r.stdout[:200]}"
    guardie = [e["valore"] for e in lab.coda() if e["evento"] == "guardia"]
    assert guardie == ["comms-guard.py"], f"M06 la guardia non è registrata: {lab.coda()}"
    assert "rossi" not in json.dumps(lab.coda()), "M06 il comando finisce in coda"
    lab.hook("bash-dispatcher.sh", json.dumps({"tool_name": "Bash", "tool_input": {"command": "ls"}}))
    assert len(lab.coda()) == 1, "M06 un comando permesso registra una guardia"


def test_m07(repo: Path) -> None:
    srv = Server()
    lab = Lab(repo, srv)
    primo = lab.hook("session-start.sh").stdout
    assert "TELEMETRIA:" in primo and "telemetria spegni" in primo, "M07 nessun avviso alla prima sessione"
    assert "TELEMETRIA:" not in lab.hook("session-start.sh").stdout, "M07 l'avviso torna alla seconda sessione"
    for _ in range(50):  # l'invio parte in background
        if srv.richieste:
            break
        time.sleep(0.1)
    assert srv.richieste and srv.richieste[0][0] == "/v1/eventi", "M07 l'avvio non manda la coda"
    assert sum(1 for p, _ in srv.richieste if p == "/v1/eventi") == 1, "M07 due avvii di fila mandano due volte"
    assert [e["evento"] for e in lab.coda()] == ["sessione"], f"M07 la seconda sessione non è in coda: {lab.coda()}"
    spenta = Lab(repo, srv, ARTURO_TELEMETRIA="0")
    assert "TELEMETRIA:" not in spenta.hook("session-start.sh").stdout, "M07 avviso a telemetria spenta"


def test_m08(repo: Path) -> None:
    srv = Server()
    srv.status = 201
    lab = Lab(repo, srv)
    bozza = lab.dir / "bozza.md"
    bozza.write_text("Il commit non parte.", encoding="utf-8")
    r = lab.arturo("segnala", "prepara", "--tipo", "problema", "--titolo", "fine si ferma", "--file", str(bozza))
    pronta = next(x for x in r.stdout.splitlines() if x.startswith("PRONTA: "))[8:]
    r = lab.arturo("segnala", "invia", "--canale", "arturo", "--file", pronta)
    assert r.returncode == 0, f"M08 invia arturo: {r.stderr!r}"
    percorso, dati = srv.richieste[-1]
    assert percorso == "/v1/segnalazioni" and dati["tipo"] == "problema" and dati["titolo"] == "[problema] fine si ferma", \
        f"M08 segnalazione: {percorso} {dati}"
    assert ("segnalazione", "problema") in [(e["evento"], e["valore"]) for e in lab.coda()], "M08 l'evento segnalazione manca"
    # Server giù: la segnalazione resta in attesa e parte con il prossimo invio.
    giu = Lab(repo)
    bozza = giu.dir / "bozza.md"
    bozza.write_text("Il commit non parte.", encoding="utf-8")
    r = giu.arturo("segnala", "prepara", "--tipo", "proposta", "--titolo", "idea", "--file", str(bozza))
    pronta = next(x for x in r.stdout.splitlines() if x.startswith("PRONTA: "))[8:]
    r = giu.arturo("segnala", "invia", "--canale", "arturo", "--file", pronta)
    attesa = list((giu.home / ".claude" / "data" / "segnalazioni").glob("*.attesa.json"))
    assert r.returncode == 0 and len(attesa) == 1, f"M08 la segnalazione non resta in attesa: {r.stdout!r}"
    giu.env["ARTURO_TELEMETRIA_URL"] = srv.url
    giu.env["ARTURO_TELEMETRIA"] = "0"  # una segnalazione approvata parte anche a telemetria spenta
    prima = len(srv.richieste)
    giu.arturo("telemetria", "invia")
    assert not attesa[0].exists() and srv.richieste[prima][0] == "/v1/segnalazioni", "M08 la segnalazione in attesa non parte"


def test_m09(repo: Path) -> None:
    py = re.search(r"EVENTI = \{(.*?)\n\}", read(repo / "bin" / "telemetria.py"), re.S)
    js = re.search(r"export const EVENTI = \{(.*?)\n\};", read(repo / "server" / "logica.js"), re.S)
    nomi_py = re.findall(r'"([a-z]+)": re\.compile', py.group(1))
    nomi_js = re.findall(r"^\s+([a-z]+):", js.group(1), re.M)
    assert nomi_py == nomi_js, f"M09 client e server hanno elenchi diversi: {nomi_py} {nomi_js}"
    impegno = next(r for r in read(repo / "README.md").splitlines() if r.startswith("3. **Telemetria minima"))
    for nome in nomi_py:
        assert f"`{nome}`" in impegno, f"M09 l'Impegno 3 del README non nomina {nome}"
    assert "Niente telemetria" not in read(repo / "README.md").split("## Indice")[0], "M09 il README promette ancora niente telemetria"


def test_m10(repo: Path) -> None:
    # Un comando della persona (qui nel suo ~/.claude/commands, non un link al repo) ha un nome suo.
    lab = Lab(repo)
    mie = lab.home / ".claude" / "commands"
    mie.unlink()
    mie.mkdir()
    (mie / "cliente-rossi.md").write_text("Un comando mio.\n", encoding="utf-8")
    (mie / "fine.md").write_text("La /fine di Arturo.\n", encoding="utf-8")
    lab.hook("inject-now.sh", json.dumps({"prompt": "/cliente-rossi"}))
    lab.arturo("telemetria", "registra", "comando", "cliente-rossi")
    lab.hook("inject-now.sh", json.dumps({"prompt": "/fine"}))
    assert [(e["evento"], e["valore"]) for e in lab.coda()] == [("comando", "fine")], \
        f"M10 parte il nome di un comando che non è di Arturo: {lab.coda()}"
    elenco = re.search(r"COMANDI = frozenset\(\{(.*?)\}\)", read(repo / "bin" / "telemetria.py"), re.S)
    assert elenco, "M10 manca l'elenco dei comandi di Arturo"
    assert sorted(re.findall(r'"([a-z0-9-]+)"', elenco.group(1))) == sorted(f.stem for f in (repo / "commands").glob("*.md")), \
        "M10 l'elenco dei comandi non coincide con commands/"


TESTS = {"M01": test_m01, "M02": test_m02, "M03": test_m03, "M04": test_m04, "M05": test_m05,
         "M06": test_m06, "M07": test_m07, "M08": test_m08, "M09": test_m09, "M10": test_m10}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--baseline-ref")
    args = parser.parse_args()
    repo = args.repo.resolve()
    if args.baseline_ref:
        failed = []
        for name, test in TESTS.items():
            try:
                test(repo)
            except (AssertionError, OSError, ValueError, KeyError, StopIteration, AttributeError,
                    json.JSONDecodeError, subprocess.SubprocessError):
                failed.append(name)
        assert failed == list(TESTS), f"baseline non discriminante: falliscono solo {failed} su {list(TESTS)}"
        print(f"BASELINE_DISCRIMINANTE={','.join(failed)}")
        return 0
    for test in TESTS.values():
        test(repo)
    print(f"PASS {','.join(TESTS)} controlli={len(TESTS)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
