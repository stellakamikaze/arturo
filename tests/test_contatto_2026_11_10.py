#!/usr/bin/env python3
"""CT01-CT09: il contatto di chi segnala (10/11/2026).

La persona dà una volta un nome e un'email agli sviluppatori di Arturo, perché la ricontattino sulle sue
segnalazioni. Il contatto parte solo con le segnalazioni del canale arturo, mai con la telemetria. Il server finto
risponde come server/logica.js; il server vero lo provano V62, V63, R18, QC1 e QM1.

CT01 arturo contatto: imposta, mostra, togli e no; il file è leggibile solo dalla persona; chiesto dice se c'è
     una risposta; togli non fa tornare la domanda.
CT02 un'email rotta, un nome troppo lungo o con un a capo non si salvano.
CT03 prepara mette il contatto nella segnalazione pronta e nell'anteprima; invia lo porta al server anche a
     telemetria spenta; la copia locale non lo contiene.
CT04 --senza-contatto: quella segnalazione parte senza.
CT05 un contatto cambiato a mano dopo l'anteprima non parte: niente arriva al server.
CT06 gli eventi della telemetria non portano mai nome né email, mentre la segnalazione sì.
CT07 l'avvio fa la domanda una volta sola; prepara la ripete finché non c'è una risposta, poi tace.
CT08 /setup, /segnala, docs/privacy.md e README raccontano il contatto, e parlano di sviluppatori di Arturo.
CT09 i controlli del client sono quelli del server: regex dell'email e tetti di nome ed email.

Sulla base ogni controllo deve fallire con un AssertionError che comincia con il suo codice. --avvelena: ogni
copia rotta fa rosso il caso suo.
"""
from __future__ import annotations

import argparse
import atexit
import http.server
import json
import os
import re
import shutil
import stat
import sys
import tempfile
import threading
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_sportello_2026_11_04 import Lab  # noqa: E402

NOME, EMAIL = "Persona Prova", "prova@example.com"
NUMERO, CODICE = 9, "0123456789abcdef0123456789abcdef"


class Server:
    """Come server/logica.js: numero, codice e, se c'è, "contatto": "salvato"; agli eventi, accettati."""

    def __init__(self):
        self.richieste = []
        fuori = self

        class Gestore(http.server.BaseHTTPRequestHandler):
            def do_POST(self):  # noqa: N802
                n = int(self.headers.get("content-length") or 0)
                grezzo = self.rfile.read(n) if n else b""
                try:
                    corpo = json.loads(grezzo or b"{}")
                except ValueError:
                    corpo = {}
                fuori.richieste.append({"percorso": self.path, "corpo": corpo, "grezzo": grezzo.decode("utf-8", "replace")})
                if self.path == "/v1/segnalazioni":
                    dati = {"numero": NUMERO, "email": True, "codice": CODICE}
                    if isinstance(corpo, dict) and corpo.get("contatto"):
                        dati["contatto"] = "salvato"
                    status = 201
                else:
                    dati, status = {"accettati": len((corpo or {}).get("eventi") or []), "scartati": 0}, 200
                testo = json.dumps(dati).encode("utf-8")
                self.send_response(status)
                self.send_header("content-type", "application/json")
                self.send_header("content-length", str(len(testo)))
                self.end_headers()
                self.wfile.write(testo)

            def do_GET(self):  # noqa: N802
                self.send_response(404)
                self.send_header("content-length", "0")
                self.end_headers()

            def log_message(self, *_):
                pass

        self.http = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Gestore)
        threading.Thread(target=self.http.serve_forever, daemon=True).start()
        self.url = f"http://127.0.0.1:{self.http.server_address[1]}"
        atexit.register(self.http.shutdown)

    def segnalazioni(self) -> list:
        return [x["corpo"] for x in self.richieste if x["percorso"] == "/v1/segnalazioni"]


def salva_contatto(lab: Lab, **dati) -> None:
    """Scrive il file come lo scrive arturo contatto: così i casi arrivano al loro controllo anche sulla base."""
    f = lab.claude / "data" / "contatto.json"
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(json.dumps(dati or {"nome": NOME, "email": EMAIL, "data": "2026-11-10", "consenso": 1}), encoding="utf-8")


def test_ct01(repo: Path) -> None:
    lab = Lab(repo)
    r = lab.arturo("contatto", "chiesto")
    assert r.returncode == 3, f"CT01 senza risposta chiesto non esce 3: {r.returncode} {r.stderr!r}"
    r = lab.arturo("contatto", "imposta", "--nome", NOME, "--email", EMAIL)
    assert r.returncode == 0, f"CT01 imposta non salva: {r.returncode} {r.stderr!r}"
    f = lab.claude / "data" / "contatto.json"
    dati = json.loads(f.read_text(encoding="utf-8"))
    assert [dati.get("nome"), dati.get("email"), dati.get("consenso")] == [NOME, EMAIL, 1], f"CT01 il file non è quello atteso: {dati}"
    if os.name != "nt":
        modo = stat.S_IMODE(f.stat().st_mode)
        assert modo == 0o600, f"CT01 il file del contatto è leggibile da altri: {oct(modo)}"
    r = lab.arturo("contatto")
    assert EMAIL in r.stdout and "sviluppatori di Arturo" in r.stdout, f"CT01 mostra non dice il contatto: {r.stdout!r}"
    assert lab.arturo("contatto", "chiesto").returncode == 0, "CT01 con un contatto chiesto non esce 0"
    lab.arturo("contatto", "togli")
    assert EMAIL not in f.read_text(encoding="utf-8"), "CT01 togli lascia l'email nel file"
    assert lab.arturo("contatto", "chiesto").returncode == 0, "CT01 dopo togli la domanda torna"
    altro = Lab(repo)
    altro.arturo("contatto", "no")
    assert altro.arturo("contatto", "chiesto").returncode == 0, "CT01 dopo no la domanda torna"


def test_ct02(repo: Path) -> None:
    lab = Lab(repo)
    for nome, email in [(NOME, "non-una-email"), (NOME, ""), ("x" * 81, EMAIL), ("riga\nnuova", EMAIL),
                        (NOME, "a" * 200 + "@b.it")]:
        r = lab.arturo("contatto", "imposta", "--nome", nome, "--email", email)
        assert r.returncode == 2 and "Errore" in r.stderr, f"CT02 un contatto rotto non è rifiutato: {nome[:12]!r} {email[:20]!r}"
    assert not (lab.claude / "data" / "contatto.json").exists(), "CT02 un contatto rotto resta nel file"
    r = lab.arturo("contatto", "imposta", "--email", EMAIL)
    assert r.returncode == 0, f"CT02 l'email senza nome non si salva: {r.stderr!r}"


def test_ct03(repo: Path) -> None:
    server = Server()
    lab = Lab(repo, server, ARTURO_TELEMETRIA="0")
    salva_contatto(lab)
    r, pronta, percorso = lab.prepara("Non parte.")
    assert pronta.get("contatto") == {"nome": NOME, "email": EMAIL}, f"CT03 la segnalazione pronta non ha il contatto: {pronta}"
    assert "Contatto per gli sviluppatori di Arturo" in r.stdout and EMAIL in r.stdout, \
        f"CT03 l'anteprima non mostra il contatto: {r.stdout[-400:]!r}"
    r = lab.arturo("segnala", "invia", "--canale", "arturo", "--file", percorso)
    assert r.returncode == 0, f"CT03 invia non parte: {r.stderr!r}"
    corpo = (server.segnalazioni() or [{}])[-1]
    assert corpo.get("contatto") == {"nome": NOME, "email": EMAIL}, f"CT03 il contatto non arriva al server: {corpo}"
    assert "installazione" not in corpo, "CT03 il contatto si porta dietro l'id dell'installazione"
    for copia in (lab.claude / "data" / "segnalazioni").glob("*.md"):
        assert EMAIL not in copia.read_text(encoding="utf-8"), "CT03 la copia locale contiene l'email"


def test_ct04(repo: Path) -> None:
    server = Server()
    lab = Lab(repo, server)
    salva_contatto(lab)
    r, pronta, percorso = lab.prepara("Non parte.", "--senza-contatto")
    assert r.returncode == 0, f"CT04 prepara non conosce --senza-contatto: {r.stderr[-200:]!r}"
    assert "contatto" not in pronta and EMAIL not in r.stdout, f"CT04 --senza-contatto lascia il contatto: {pronta}"
    lab.arturo("segnala", "invia", "--canale", "arturo", "--file", percorso)
    assert server.segnalazioni() and "contatto" not in server.segnalazioni()[-1], "CT04 il contatto parte lo stesso"


def test_ct05(repo: Path) -> None:
    server = Server()
    lab = Lab(repo, server)
    salva_contatto(lab)
    _, pronta, percorso = lab.prepara("Non parte.")
    assert "contatto" in pronta, "CT05 la segnalazione pronta non ha il contatto da cambiare"
    pronta["contatto"]["email"] = "altro@example.com"
    Path(percorso).write_text(json.dumps(pronta), encoding="utf-8")
    r = lab.arturo("segnala", "invia", "--canale", "arturo", "--file", percorso)
    assert r.returncode == 2 and not server.segnalazioni(), f"CT05 un contatto cambiato a mano parte: {r.returncode}"


def test_ct06(repo: Path) -> None:
    server = Server()
    lab = Lab(repo, server)
    salva_contatto(lab)
    lab.telemetria("registra", "sessione")
    _, _, percorso = lab.prepara("Non parte.")
    lab.arturo("segnala", "invia", "--canale", "arturo", "--file", percorso)
    lab.telemetria("invia")
    eventi = [x["grezzo"] for x in server.richieste if x["percorso"] == "/v1/eventi"]
    assert any(EMAIL in json.dumps(c) for c in server.segnalazioni()), "CT06 la segnalazione non porta il contatto"
    assert eventi, "CT06 la telemetria non ha mandato eventi da controllare"
    assert not any(EMAIL in e or NOME in e for e in eventi), "CT06 gli eventi della telemetria portano il contatto"


def test_ct07(repo: Path) -> None:
    lab = Lab(repo, None, ARTURO_TELEMETRIA="0")
    prima = lab.telemetria("avvio").stdout
    assert "CONTATTO:" in prima and "sviluppatori di Arturo" in prima, f"CT07 l'avvio non fa la domanda: {prima!r}"
    assert "CONTATTO:" not in lab.telemetria("avvio").stdout, "CT07 l'avvio rifà la domanda"
    r, _, _ = lab.prepara("Non parte.")
    assert "CONTATTO:" in r.stdout, "CT07 prepara non ripete la domanda senza risposta"
    lab.arturo("contatto", "no")
    r, _, _ = lab.prepara("Non parte.")
    assert "CONTATTO:" not in r.stdout, "CT07 prepara rifà la domanda dopo il no"


def test_ct08(repo: Path) -> None:
    testi = {nome: (repo / nome).read_text(encoding="utf-8") for nome in
             ("commands/setup.md", "commands/segnala.md", "docs/privacy.md", "README.md")}
    for nome, testo in testi.items():
        assert "arturo contatto" in testo or "contatto" in testo.lower() and nome == "README.md", \
            f"CT08 {nome} non racconta il contatto"
    assert "sviluppatori di Arturo" in testi["docs/privacy.md"] and "contatto" in testi["docs/privacy.md"], \
        "CT08 docs/privacy.md non dice chi vede il contatto"
    assert re.search(r"contatto.{0,400}(12 mesi|ritir)", testi["docs/privacy.md"], re.S | re.I), \
        "CT08 docs/privacy.md non dice quanto resta il contatto"


def test_ct09(repo: Path) -> None:
    logica = (repo / "server" / "logica.js").read_text(encoding="utf-8")
    client = repo / "bin" / "contatto.py"
    assert client.exists() and "validaContatto" in logica, "CT09 manca il controllo del contatto nel client o nel server"
    testo = client.read_text(encoding="utf-8")
    regex = re.search(r'RE_EMAIL = re\.compile\(r"(.+?)"\)', testo)
    assert regex and f"RE_EMAIL = /{regex.group(1)}/" in logica, "CT09 la regex dell'email del client non è quella del server"
    for chiave, costante in (("contattoNome", "NOME_MASSIMO"), ("contattoEmail", "EMAIL_MASSIMO")):
        server = re.search(rf"{chiave}: (\d+)", logica)
        locale = re.search(rf"{costante} = (\d+)", testo)
        assert server and locale and server.group(1) == locale.group(1), f"CT09 il tetto {chiave} non coincide"


# Il veleno (caso, file, testo giusto, testo rotto): la copia rotta deve far rosso il suo caso.
VELENI = [
    ("CT03", "bin/segnala.py", '            dati_server["contatto"] = contatto', "            pass"),
    ("CT05", "bin/segnala.py", '        campi["contatto"] = dati["contatto"]', "        pass"),
    ("CT07", "bin/telemetria.py", "            domanda = _contatto.riga_avvio()", '            domanda = ""'),
]


def avvelena(repo: Path) -> int:
    esiti = []
    for caso, rel, giusto, rotto in VELENI:
        with tempfile.TemporaryDirectory() as tmp:
            copia = Path(tmp) / "repo"
            shutil.copytree(repo, copia, ignore=shutil.ignore_patterns(".git", "__pycache__", "node_modules"))
            testo = (copia / rel).read_text(encoding="utf-8")
            assert testo.count(giusto) == 1, f"veleno {caso}: il testo da rompere non c'è più in {rel}"
            (copia / rel).write_text(testo.replace(giusto, rotto), encoding="utf-8")
            try:
                TESTS[caso](copia)
            except AssertionError as e:
                if str(e).startswith(caso):
                    print(f"VELENO {caso} ROSSO: {str(e)[:120]}")
                    esiti.append(caso)
                    continue
                print(f"VELENO {caso} NON ATTACCA ({rel}): {e}")
                return 1
            print(f"VELENO {caso} NON ATTACCA ({rel}): il caso resta verde")
            return 1
    print(f"VELENI_ROSSI={','.join(esiti)} veleni={len(VELENI)}")
    return 0 if len(esiti) == len(VELENI) else 1


TESTS = {"CT01": test_ct01, "CT02": test_ct02, "CT03": test_ct03, "CT04": test_ct04, "CT05": test_ct05,
         "CT06": test_ct06, "CT07": test_ct07, "CT08": test_ct08, "CT09": test_ct09}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--baseline-ref")
    parser.add_argument("--avvelena", action="store_true")
    parser.add_argument("casi", nargs="*")
    args = parser.parse_args()
    repo = args.repo.resolve()
    if args.avvelena:
        return avvelena(repo)
    scelti = {k: v for k, v in TESTS.items() if not args.casi or k in args.casi}
    if args.baseline_ref:
        rossi, altro = [], []
        for nome, test in scelti.items():
            try:
                test(repo)
            except AssertionError as e:
                (rossi if str(e).startswith(nome) else altro).append(f"{nome}: {e}")
            except Exception as e:  # noqa: BLE001
                altro.append(f"{nome}: {type(e).__name__} {e}")
        assert not altro and len(rossi) == len(scelti), \
            "baseline non discriminante: ogni controllo deve fallire col suo codice.\n" + "\n".join(altro + rossi)
        print(f"BASELINE_DISCRIMINANTE={','.join(r.split(':')[0] for r in rossi)}")
        return 0
    for test in scelti.values():
        test(repo)
    print(f"PASS {','.join(scelti)} controlli={len(scelti)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
