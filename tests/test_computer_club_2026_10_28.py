#!/usr/bin/env python3
"""CC01-CC05: le domande della terza sera del Computer Club (27/10/2026), fatte a voce da chi usava
Arturo da una settimana.

CC01 la barra in basso dice la quota in parole ("5 ore", "settimana"): chi leggeva "5h 84%" lo prendeva
     per la settimana. L'orario di azzeramento delle 5 ore si vede sempre, quello della settimana solo
     da 75%. L'ultima quota letta resta in cache/statusline/quota.json, mai in data/.
CC02 /guidami legge la quota dal file che la barra scrive ("ho token e tempo, cosa facciamo?").
CC03 la skill concetti spiega contesto e memoria, git e GitHub, branch e fork, aggiornamenti, subagent,
     ultracode, le due finestre della quota e il sì a una conferma, ognuno con "In Arturo:". Il README
     conta le skill come le cartelle con SKILL.md.
CC04 /segnala dice il numero che il server assegna ("quando faccio il segnale cosa succede?").
CC05 il riepilogo di /setup presenta /dafare, la quota e il suono dell'attesa; NOVITA ha la voce del 28/10.

Sulla base 443b191 ogni controllo deve fallire con un AssertionError che comincia con il suo codice.
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
import subprocess
import sys
import tempfile
import threading
from pathlib import Path

NODE = shutil.which("node") or "node"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def banco_telemetria():
    spec = importlib.util.spec_from_file_location("telemetria_banco", Path(__file__).with_name("test_telemetria.py"))
    assert spec and spec.loader
    banco = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(banco)
    return banco


def barra(repo: Path, home: Path, rate: dict) -> str:
    dati = {"model": {"display_name": "Opus 5"}, "workspace": {"current_dir": str(home)}, "rate_limits": rate}
    env = {"HOME": str(home), "USERPROFILE": str(home), "PATH": os.environ.get("PATH", "")}
    if os.name == "nt":
        env["SYSTEMROOT"] = os.environ.get("SYSTEMROOT", r"C:\Windows")
    p = subprocess.run([NODE, str(repo / "hooks" / "statusline.js")], input=json.dumps(dati), text=True,
                       encoding="utf-8", capture_output=True, env=env, timeout=30, check=False)
    return re.sub(r"\x1b\[[0-9;]*m", "", p.stdout)


def test_cc01(repo: Path) -> None:
    with tempfile.TemporaryDirectory() as d:
        home = Path(d)
        (home / ".claude").mkdir()
        r = barra(repo, home, {"five_hour": {"used_percentage": 23.4, "resets_at": 1793170800},
                               "seven_day": {"used_percentage": 12, "resets_at": 1793430000}})
        assert "5 ore 23%" in r and "settimana 12%" in r, f"CC01 la quota non è in parole: {r!r}"
        assert re.search(r"5 ore 23%, si azzera alle \d\d:\d\d", r), f"CC01 sotto il 75% l'orario delle 5 ore sparisce: {r!r}"
        assert "settimana 12%," not in r, f"CC01 l'orario della settimana compare sotto il 75%: {r!r}"
        r = barra(repo, home, {"five_hour": {"used_percentage": 10}, "seven_day": {"used_percentage": 80,
                                                                                    "resets_at": 1793430000}})
        assert re.search(r"settimana 80%, si azzera \w{3} \d\d:\d\d", r), f"CC01 da 75% la settimana non dice quando: {r!r}"
        f = home / ".claude" / "cache" / "statusline" / "quota.json"
        assert f.exists(), "CC01 la barra non salva la quota per /guidami"
        q = json.loads(read(f))
        assert q["cinque_ore"]["pct"] == 10 and q["settimana"] == {"pct": 80, "resets": 1793430000}, f"CC01 quota salvata: {q}"
        assert not (home / ".claude" / "data").exists(), "CC01 la barra scrive in data/"


def test_cc02(repo: Path) -> None:
    guidami = read(repo / "commands" / "guidami.md")
    assert "cache\" / \"statusline\" / \"quota.json" in guidami, "CC02 /guidami non legge la quota salvata dalla barra"
    assert "si azzera" in guidami and "lavori lunghi" in guidami, "CC02 /guidami non usa la quota per scegliere il lavoro"


def test_cc03(repo: Path) -> None:
    f = repo / "skills" / "concetti" / "SKILL.md"
    assert f.exists(), "CC03 manca la skill concetti"
    testo = read(f)
    m = re.match(r"---\n(.*?)\n---\n", testo, re.S)
    assert m and re.search(r"^name: concetti$", m.group(1), re.M) and "when_to_use:" in m.group(1), \
        "CC03 il frontmatter della skill concetti non è valido"
    voci = re.findall(r"^\*\*(.+?)\*\*", testo[m.end():], re.M)
    attese = ["Contesto e memoria.", "Git e GitHub.", "Branch e fork.", "Le tue modifiche e gli aggiornamenti.",
              "Subagent e modelli più economici.", "Ultracode.", "Le due finestre della quota.", "Dire sì a una conferma."]
    assert voci == attese, f"CC03 le voci della skill concetti sono {voci}"
    assert len(re.findall(r"^In Arturo:", testo, re.M)) == len(attese), "CC03 una voce non dice dove trovi la cosa in Arturo"
    skill = len(list((repo / "skills").glob("*/SKILL.md")))
    readme = read(repo / "README.md")
    assert f"**{skill} skill**" in readme and f"{skill} skill (+ regole" in readme, \
        f"CC03 il README non conta {skill} skill"


class ServerNumero:
    """Come il Server di test_telemetria.py, ma risponde 201 col numero, come server/logica.js."""

    def __init__(self, numero: int):
        self.richieste = []
        fuori = self

        class Gestore(http.server.BaseHTTPRequestHandler):
            def do_POST(self):  # noqa: N802
                corpo = self.rfile.read(int(self.headers.get("content-length", 0)))
                fuori.richieste.append((self.path, json.loads(corpo)))
                risposta = json.dumps({"numero": numero, "email": True}).encode("utf-8")
                self.send_response(201)
                self.send_header("content-type", "application/json")
                self.end_headers()
                self.wfile.write(risposta)

            def log_message(self, *_):
                pass

        self.http = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Gestore)
        threading.Thread(target=self.http.serve_forever, daemon=True).start()
        self.url = f"http://127.0.0.1:{self.http.server_address[1]}"
        atexit.register(self.http.shutdown)


def test_cc04(repo: Path) -> None:
    banco = banco_telemetria()
    lab = banco.Lab(repo, ServerNumero(42))
    bozza = lab.dir / "bozza.md"
    bozza.write_text("La barra dice 5h e non capisco.", encoding="utf-8")
    r = lab.arturo("segnala", "prepara", "--tipo", "problema", "--titolo", "quota", "--file", str(bozza))
    pronta = next(x for x in r.stdout.splitlines() if x.startswith("PRONTA: "))[8:]
    r = lab.arturo("segnala", "invia", "--canale", "arturo", "--file", pronta)
    assert r.returncode == 0 and "è la segnalazione n. 42" in r.stdout, \
        f"CC04 /segnala non dice il numero: {r.stdout!r} {r.stderr!r}"
    copie = list((lab.home / ".claude" / "data" / "segnalazioni").glob("*_problema.md"))
    assert copie and "n. 42" in read(copie[0]), "CC04 la copia della segnalazione non tiene il numero"
    assert "è la segnalazione n." in read(repo / "commands" / "segnala.md"), "CC04 /segnala non dice di riferire il numero"


def test_cc05(repo: Path) -> None:
    setup = read(repo / "commands" / "setup.md")
    riepilogo = setup[setup.index("## Riepilogo finale"):]
    for parola in ("/dafare", "quota", "suona"):
        assert parola in riepilogo, f"CC05 il riepilogo di /setup non presenta {parola}"
    novita = read(repo / "NOVITA.md")
    prima = re.search(r"^## (\d{4}-\d\d-\d\d)", novita, re.M)
    assert prima and prima.group(1) == "2026-10-28" and "Computer Club" in novita[prima.start():prima.start() + 400], \
        "CC05 NOVITA non racconta le domande del Computer Club"


TESTS = {"CC01": test_cc01, "CC02": test_cc02, "CC03": test_cc03, "CC04": test_cc04, "CC05": test_cc05}


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
