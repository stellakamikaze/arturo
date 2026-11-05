#!/usr/bin/env python3
"""SP01-SP08: lo sportello delle segnalazioni (4/11/2026, #3925; piano della telemetria del 24/10/2026, F2 e F3).

Chi segnala riceve col numero un codice (la ricevuta), vede nell'anteprima cosa esce e cosa è stato tolto, sceglie
le caselle del pacchetto tecnico, legge la risposta di chi mantiene Arturo, aggiunge un seguito o ritira la
segnalazione. Il server finto risponde come server/logica.js; il server vero lo provano V36, V46-V49, QC1 e QM1.

SP01 redigi toglie email, indirizzi web esterni, indirizzi IP, nomi di computer della rete e nomi di documenti;
     lascia gli indirizzi pubblici di Arturo e i numeri di versione; l'anteprima dice cosa ha tolto; --tieni rimette.
SP02 il pacchetto tecnico a caselle: ambiente, banchi e config accese, deriva, errore e collega spente; --pacchetto
     cambia le caselle, --errore accende l'errore, un segreto nell'errore ferma tutto.
SP03 l'invio porta pacchetto e origine, l'id dell'installazione solo con collega; il codice della ricevuta resta in
     data/segnalazioni/ricevute.json, leggibile solo dalla persona; la copia dice quali voci sono partite.
SP04 stato legge dal server, col codice nell'header e mai nell'indirizzo, lo stato e la risposta.
SP05 l'avvio dice SPORTELLO una volta per una risposta nuova, letta dall'invio in background; dopo stato tace.
SP06 seguito e ritira: senza --conferma non parte niente; con --conferma partono col codice; senza ricevuta, exit 3.
SP07 una segnalazione partita in differita salva anche lei il codice; una rifiutata compare in stato come tale.
SP08 /segnala, docs/privacy.md e server/README.md raccontano lo sportello.
SP09 le liste scritte due volte coincidono: voci del pacchetto, origini e stati in bin/segnala.py,
     bin/telemetria.py e server/logica.js.

Sulla base fa14218 ogni controllo deve fallire con un AssertionError che comincia con il suo codice.
"""
from __future__ import annotations

import argparse
import atexit
import http.server
import importlib.util
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import threading
from pathlib import Path

CODICE = "0123456789abcdef0123456789abcdef"
NUMERO = 7


class Server:
    """Risponde come server/logica.js: numero e codice alla segnalazione, stato e risposta col codice giusto."""

    def __init__(self):
        self.richieste = []
        self.giu = False
        fuori = self

        class Gestore(http.server.BaseHTTPRequestHandler):
            def _rispondi(self, status, dati):
                corpo = json.dumps(dati).encode("utf-8")
                self.send_response(status)
                self.send_header("content-type", "application/json")
                self.send_header("content-length", str(len(corpo)))
                self.end_headers()
                self.wfile.write(corpo)

            def _registra(self):
                n = int(self.headers.get("content-length") or 0)
                corpo = json.loads(self.rfile.read(n) or b"{}") if n else {}
                fuori.richieste.append({"metodo": self.command, "percorso": self.path, "corpo": corpo,
                                        "codice": self.headers.get("x-arturo-codice", "")})
                return corpo

            def do_GET(self):  # noqa: N802
                self._registra()
                if self.path == f"/v1/contributi/{NUMERO}" and self.headers.get("x-arturo-codice") == CODICE:
                    return self._rispondi(200, {"numero": NUMERO, "stato": "serve-info", "risposta": "Su quale cartella succede?",
                                                "versione_fix": "", "aggiornata": "2026-11-05T09:00:00Z", "seguiti": 0})
                return self._rispondi(404, {"errore": "segnalazione inesistente o codice sbagliato"})

            def do_POST(self):  # noqa: N802
                self._registra()
                if self.path == "/v1/segnalazioni":
                    return self._rispondi(201, {"numero": NUMERO, "email": True, "codice": CODICE})
                if self.path.startswith(f"/v1/contributi/{NUMERO}/") and self.headers.get("x-arturo-codice") == CODICE:
                    return self._rispondi(201 if self.path.endswith("seguito") else 200, {"numero": NUMERO})
                return self._rispondi(404, {"errore": "segnalazione inesistente o codice sbagliato"})

            def log_message(self, *_):
                pass

        self.http = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Gestore)
        threading.Thread(target=self.http.serve_forever, daemon=True).start()
        self.url = f"http://127.0.0.1:{self.http.server_address[1]}"
        atexit.register(self.http.shutdown)


class Lab:
    def __init__(self, repo: Path, server: Server | None = None, **env):
        self.repo = repo
        self.dir = Path(tempfile.mkdtemp(prefix="arturo-sp."))
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

    def arturo(self, *argomenti: str, **env) -> subprocess.CompletedProcess:
        return subprocess.run([sys.executable, "-B", str(self.repo / "bin" / "arturo"), *argomenti],
                              capture_output=True, text=True, encoding="utf-8", errors="replace",
                              env={**self.env, **env}, timeout=60)

    def telemetria(self, *argomenti: str, **env) -> subprocess.CompletedProcess:
        return subprocess.run([sys.executable, "-B", str(self.repo / "bin" / "telemetria.py"), *argomenti],
                              capture_output=True, text=True, encoding="utf-8", errors="replace",
                              env={**self.env, **env}, timeout=60)

    def bozza(self, testo: str, nome: str = "bozza.md") -> Path:
        f = self.dir / nome
        f.write_text(testo, encoding="utf-8")
        return f

    def prepara(self, testo: str, *extra: str) -> tuple:
        r = self.arturo("segnala", "prepara", "--tipo", "problema", "--titolo", "La sessione si ferma",
                        "--file", str(self.bozza(testo)), *extra)
        righe = [x for x in r.stdout.splitlines() if x.startswith("PRONTA: ")]
        pronta = json.loads(Path(righe[0][8:]).read_text(encoding="utf-8")) if righe else {}
        return r, pronta, (righe[0][8:] if righe else "")

    def codici(self) -> dict:
        f = self.claude / "data" / "segnalazioni" / "ricevute.json"
        return json.loads(f.read_text(encoding="utf-8")) if f.exists() else {}


def lab_con_cache(repo: Path, server: Server | None = None) -> Lab:
    lab = Lab(repo, server)
    (lab.claude / "cache").mkdir()
    (lab.claude / "cache" / "banchi-ultimo-esito.txt").write_text(
        "ROSSO\n1 banchi delle guardie rossi su 10 (2026-11-04 10:00)\ntest_heredoc.py: AssertionError H03\n", encoding="utf-8")
    (lab.claude / "cache" / "deriva.json").write_text(json.dumps(
        {"misurata": True, "file": ["hooks/comms-guard.py"], "guardie": ["hooks/comms-guard.py"], "hook": [], "config": []}),
        encoding="utf-8")
    return lab


SENSIBILI = ("mario.rossi@cliente.it", "https://intranet.cliente.it/ticket/42", "192.168.1.20", "nas.local",
             "macbook.tail1234.ts.net", "Preventivo_Rossi.pdf")


def test_sp01(repo: Path) -> None:
    lab = Lab(repo)
    testo = ("Mandando l'email a mario.rossi@cliente.it dal link https://intranet.cliente.it/ticket/42 la sessione si ferma.\n"
             "Succede col disco su 192.168.1.20 (nas.local) e su macbook.tail1234.ts.net, aprendo Preventivo_Rossi.pdf.\n"
             "Claude Code 2.1.318, guida https://github.com/stellakamikaze/arturo/blob/main/README.md e server 127.0.0.1:8080.")
    r, pronta, _ = lab.prepara(testo)
    assert r.returncode == 0 and pronta, f"SP01 prepara non parte: {r.stderr!r}"
    for x in SENSIBILI:
        assert x not in pronta.get("testo", "") and x not in r.stdout, f"SP01 resta nel testo: {x}"
    tenuti = ("https://github.com/stellakamikaze/arturo/blob/main/README.md", "2.1.318", "127.0.0.1:8080", "[documento].pdf")
    for x in tenuti:
        assert x in pronta.get("testo", ""), f"SP01 tolto quello che serve: {x}"
    assert "Tolto dal testo:" in r.stdout and "1 email" in r.stdout and "1 indirizzi IP" in r.stdout \
        and "2 nomi di computer della rete" in r.stdout, f"SP01 l'anteprima non dice cosa ha tolto: {r.stdout!r}"
    r, pronta, _ = lab.prepara(testo, "--tieni", "ip,computer")
    assert "192.168.1.20" in pronta.get("testo", "") and "nas.local" in pronta.get("testo", ""), \
        "SP01 --tieni non rimette indirizzi IP e computer"
    assert "mario.rossi@cliente.it" not in pronta.get("testo", ""), "SP01 --tieni rimette anche le email"


def test_sp02(repo: Path) -> None:
    lab = lab_con_cache(repo)
    r, pronta, _ = lab.prepara("Non parte.")
    assert r.returncode == 0, f"SP02 prepara non parte: {r.stderr!r}"
    caselle = {riga.split("]")[1].split(":")[0].strip(): riga.strip().startswith("[x]")
               for riga in r.stdout.splitlines() if riga.strip().startswith(("[x]", "[ ]"))}
    assert caselle == {"ambiente": True, "banchi": True, "config": True, "deriva": False, "errore": False, "collega": False}, \
        f"SP02 le caselle di default sono sbagliate: {caselle}"
    assert set(pronta.get("pacchetto") or {}) == {"ambiente", "banchi", "config"} and pronta.get("collega") is False, \
        f"SP02 il pacchetto preparato non segue le caselle: {pronta.get('pacchetto')}"
    assert "test_heredoc.py" in r.stdout and "Python:" in r.stdout, "SP02 l'anteprima non mostra il contenuto delle voci accese"
    _, pronta, _ = lab.prepara("Non parte.", "--pacchetto", "nessuna")
    assert pronta.get("pacchetto") == {} and pronta.get("collega") is False, "SP02 --pacchetto nessuna lascia voci accese"
    _, pronta, _ = lab.prepara("Non parte.", "--pacchetto", "deriva,collega")
    assert set(pronta.get("pacchetto") or {}) == {"deriva"} and pronta.get("collega") is True, \
        f"SP02 --pacchetto non accende deriva e collega: {pronta}"
    errore = lab.bozza("Traceback: KeyError 'x' in /Users/mario/progetto/a.py", "errore.txt")
    _, pronta, _ = lab.prepara("Non parte.", "--errore", str(errore))
    assert "KeyError" in (pronta.get("pacchetto") or {}).get("errore", ""), "SP02 --errore non accende l'errore"
    assert "/Users/mario" not in json.dumps(pronta), "SP02 l'errore esce con la cartella personale"
    segreto = lab.bozza("token ghp_" + "a1B2c3D4e5F6g7H8i9J0" * 2, "segreto.txt")
    r, _, _ = lab.prepara("Non parte.", "--errore", str(segreto))
    assert r.returncode == 3, f"SP02 un segreto nell'errore non ferma prepara: {r.returncode} {r.stdout!r}"


def test_sp03(repo: Path) -> None:
    server = Server()
    lab = lab_con_cache(repo, server)
    _, _, pronta = lab.prepara("Non parte.", "--origine", "fine")
    r = lab.arturo("segnala", "invia", "--canale", "arturo", "--file", pronta)
    assert r.returncode == 0, f"SP03 invia non parte: {r.stderr!r}"
    assert f"è la segnalazione n. {NUMERO}" in r.stdout and "appunti" not in r.stdout, \
        f"SP03 il canale arturo finisce in un altro canale: {r.stdout!r}"
    corpo = next((x["corpo"] for x in server.richieste if x["percorso"] == "/v1/segnalazioni"), {})
    assert set(corpo.get("pacchetto") or {}) == {"ambiente", "banchi", "config"} and corpo.get("origine") == "fine", \
        f"SP03 il pacchetto o l'origine non partono: {corpo}"
    assert "installazione" not in corpo, "SP03 l'id dell'installazione parte senza la casella collega"
    assert lab.codici() == {str(NUMERO): CODICE}, f"SP03 il codice della ricevuta non è salvato: {lab.codici()}"
    if os.name != "nt":
        modo = stat.S_IMODE((lab.claude / "data" / "segnalazioni" / "ricevute.json").stat().st_mode)
        assert modo == 0o600, f"SP03 il file dei codici è leggibile da altri: {oct(modo)}"
    assert "Ricevuta" in r.stdout, f"SP03 la persona non sa della ricevuta: {r.stdout!r}"
    copia = next((lab.claude / "data" / "segnalazioni").glob("*_problema.md"))
    assert "Pacchetto: ambiente, banchi, config" in copia.read_text(encoding="utf-8"), "SP03 la copia non dice cosa è partito"
    _, _, pronta = lab.prepara("Non parte.", "--pacchetto", "collega")
    lab.arturo("segnala", "invia", "--canale", "arturo", "--file", pronta)
    ultimo = [x["corpo"] for x in server.richieste if x["percorso"] == "/v1/segnalazioni"][-1]
    assert "installazione" in ultimo and "pacchetto" not in ultimo, f"SP03 la casella collega non porta l'id: {ultimo}"


def test_sp04(repo: Path) -> None:
    server = Server()
    lab = Lab(repo, server)
    _, _, pronta = lab.prepara("Non parte.")
    lab.arturo("segnala", "invia", "--canale", "arturo", "--file", pronta)
    r = lab.arturo("segnala", "stato")
    assert r.returncode == 0 and "Su quale cartella succede?" in r.stdout, f"SP04 stato non mostra la risposta: {r.stdout!r}"
    assert "altre informazioni" in r.stdout, f"SP04 stato non dice che serve un'informazione: {r.stdout!r}"
    letture = [x for x in server.richieste if x["metodo"] == "GET"]
    assert letture and all(x["codice"] == CODICE and CODICE not in x["percorso"] for x in letture), \
        f"SP04 il codice non viaggia nell'header: {letture}"


def test_sp05(repo: Path) -> None:
    server = Server()
    lab = Lab(repo, server)
    _, _, pronta = lab.prepara("Non parte.")
    lab.arturo("segnala", "invia", "--canale", "arturo", "--file", pronta)
    lab.telemetria("segnalazioni")  # l'invio in background delle segnalazioni legge anche le risposte
    r = lab.telemetria("avvio", ARTURO_TELEMETRIA="0")
    assert f"SPORTELLO" in r.stdout and f"n. {NUMERO}" in r.stdout, f"SP05 l'avvio non dice della risposta: {r.stdout!r}"
    lab.arturo("segnala", "stato")
    r = lab.telemetria("avvio", ARTURO_TELEMETRIA="0")
    assert "SPORTELLO" not in r.stdout, f"SP05 l'avvio ripete una risposta già vista: {r.stdout!r}"


def test_sp06(repo: Path) -> None:
    server = Server()
    lab = Lab(repo, server)
    _, _, pronta = lab.prepara("Non parte.")
    lab.arturo("segnala", "invia", "--canale", "arturo", "--file", pronta)
    aggiunta = lab.bozza("La cartella è su nas.local, Documenti.", "aggiunta.md")
    prima = len(server.richieste)
    r = lab.arturo("segnala", "seguito", str(NUMERO), "--file", str(aggiunta))
    assert r.returncode == 0 and len(server.richieste) == prima, f"SP06 seguito parte senza --conferma: {r.stdout!r}"
    assert "nas.local" not in r.stdout and "[computer]" in r.stdout, "SP06 il seguito non passa dalla pulizia"
    r = lab.arturo("segnala", "seguito", str(NUMERO), "--file", str(aggiunta), "--conferma")
    inviato = server.richieste[-1]
    assert r.returncode == 0 and inviato["percorso"] == f"/v1/contributi/{NUMERO}/seguito" and inviato["codice"] == CODICE \
        and "nas.local" not in json.dumps(inviato["corpo"]), f"SP06 il seguito non parte col codice: {inviato} {r.stderr!r}"
    prima = len(server.richieste)
    r = lab.arturo("segnala", "ritira", str(NUMERO))
    assert r.returncode == 0 and len(server.richieste) == prima, "SP06 ritira parte senza --conferma"
    r = lab.arturo("segnala", "ritira", str(NUMERO), "--conferma")
    assert r.returncode == 0 and server.richieste[-1]["percorso"] == f"/v1/contributi/{NUMERO}/ritira", \
        f"SP06 il ritiro non parte: {r.stderr!r}"
    r = lab.arturo("segnala", "ritira", "99", "--conferma")
    assert r.returncode == 3, f"SP06 una segnalazione senza ricevuta non esce con 3: {r.returncode}"


def test_sp07(repo: Path) -> None:
    server = Server()
    lab = Lab(repo)  # rete giù: 127.0.0.1:9
    _, _, pronta = lab.prepara("Non parte.")
    r = lab.arturo("segnala", "invia", "--canale", "arturo", "--file", pronta)
    assert "in attesa" in r.stdout, f"SP07 la segnalazione non resta in attesa: {r.stdout!r}"
    lab.telemetria("segnalazioni", ARTURO_TELEMETRIA_URL=server.url)
    assert lab.codici() == {str(NUMERO): CODICE}, f"SP07 la segnalazione partita in differita non salva il codice: {lab.codici()}"
    cartella = lab.claude / "data" / "segnalazioni"
    copia = next(cartella.glob("*_problema.md"))
    (cartella / f"{copia.stem}.rifiutata.json").write_text("{}", encoding="utf-8")
    r = lab.arturo("segnala", "stato", ARTURO_TELEMETRIA_URL="http://127.0.0.1:9")
    assert "rifiutata dal server" in r.stdout, f"SP07 stato non dice della segnalazione rifiutata: {r.stdout!r}"


def test_sp08(repo: Path) -> None:
    comando = (repo / "commands" / "segnala.md").read_text(encoding="utf-8")
    for x in ("--pacchetto", "segnala seguito", "segnala ritira", "Tolto dal testo", "ricevuta"):
        assert x in comando, f"SP08 /segnala non racconta {x}"
    privacy = (repo / "docs" / "privacy.md").read_text(encoding="utf-8")
    for x in ("pacchetto tecnico", "90 giorni", "codice", "ritira"):
        assert x in privacy, f"SP08 docs/privacy.md non racconta {x}"
    server = (repo / "server" / "README.md").read_text(encoding="utf-8")
    for x in ("/v1/contributi", "2026-11-04-sportello.sql"):
        assert x in server, f"SP08 server/README.md non racconta {x}"


def _lista_js(testo: str, nome: str) -> list:
    m = re.search(r"export const " + nome + r" = \[(.*?)\];", testo, re.S)
    assert m, f"SP09 server/logica.js non ha {nome}"
    return re.findall(r'"([^"]+)"', m.group(1))


def _modulo(repo: Path, nome: str):
    sys.path.insert(0, str(repo / "bin"))
    try:
        spec = importlib.util.spec_from_file_location(f"{nome}_sp09", str(repo / "bin" / f"{nome}.py"))
        modulo = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(modulo)
        return modulo
    finally:
        sys.path.pop(0)


def test_sp09(repo: Path) -> None:
    js = (repo / "server" / "logica.js").read_text(encoding="utf-8")
    segnala, telemetria = _modulo(repo, "segnala"), _modulo(repo, "telemetria")
    voci = [v for v, _, _ in getattr(segnala, "VOCI_PACCHETTO", ()) if v != "collega"]
    assert voci == _lista_js(js, "VOCI_PACCHETTO"), f"SP09 le voci del pacchetto non coincidono: {voci}"
    assert list(getattr(segnala, "ORIGINI", ())) == _lista_js(js, "ORIGINI"), "SP09 le origini non coincidono"
    stati = _lista_js(js, "STATI") + ["ritirata"]
    assert sorted(getattr(telemetria, "STATI_SPORTELLO", ())) == sorted(stati), "SP09 gli stati del client non sono quelli del server"
    assert sorted(getattr(segnala, "STATO_IN_PAROLE", {})) == sorted(stati), "SP09 uno stato non ha le sue parole in /segnala stato"


TESTS = {"SP01": test_sp01, "SP02": test_sp02, "SP03": test_sp03, "SP04": test_sp04, "SP05": test_sp05,
         "SP06": test_sp06, "SP07": test_sp07, "SP08": test_sp08, "SP09": test_sp09}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--baseline-ref")
    args = parser.parse_args()
    repo = args.repo.resolve()
    if args.baseline_ref:
        rossi, altro = [], []
        for nome, test in TESTS.items():
            try:
                test(repo)
            except AssertionError as e:
                (rossi if str(e).startswith(nome) else altro).append(f"{nome}: {e}")
            except Exception as e:  # noqa: BLE001
                altro.append(f"{nome}: {type(e).__name__} {e}")
        assert not altro and len(rossi) == len(TESTS), \
            "baseline non discriminante: ogni controllo deve fallire col suo codice.\n" + "\n".join(altro + rossi)
        print(f"BASELINE_DISCRIMINANTE={','.join(r.split(':')[0] for r in rossi)}")
        return 0
    for test in TESTS.values():
        test(repo)
    print(f"PASS {','.join(TESTS)} controlli={len(TESTS)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
