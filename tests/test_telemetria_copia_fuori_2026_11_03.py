#!/usr/bin/env python3
"""TC01-TC05: la telemetria tace quando il codice gira fuori dalla config di chi lo lancia (3/11/2026).

bin/telemetria.py legge stato, id e versione sempre in ~/.claude. Lanciato da un clone di sviluppo o da un
pacchetto del plugin provato con `claude -p --plugin-dir` (HOME vera), usava la config personale di chi
sviluppa Arturo: tre installazioni nuove con la versione "sconosciuta" e tre avvisi su Telegram (Balthasar
l'1/11, MacBook Air e Mac mini il 3/11).

TC01 codice fuori dalla config, HOME vera, nessun server indicato: spenta, e `registra` non scrive la coda;
TC02 codice dentro la config (~/.claude/bin, come in un clone installato): accesa;
TC03 codice fuori con ARTURO_TELEMETRIA_URL (i banchi col server finto): accesa;
TC04 codice fuori con una HOME di prova: accesa, gli eventi vanno solo al server indicato (url());
TC05 CLAUDE_CONFIG_DIR che contiene il codice: accesa.

Ogni caso carica bin/telemetria.py del repository in un processo suo, con la HOME in una cartella temporanea.
home_di_prova la riconoscerebbe come banco: TC01, TC02 e TC03 la sostituiscono con una che dice "persona vera".
Invarianti (verdi anche sulla base): TC02-TC05. Sulla base 9248ea9 è rosso TC01.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

CASI = ["TC01", "TC02", "TC03", "TC04", "TC05"]
DISCRIMINANTI = ["TC01"]


# Il caso gira in un processo suo: le variabili e la HOME si leggono quando il modulo chiama Path.home().
SONDA = r"""
import importlib.util, json, os, sys
from pathlib import Path
codice, vera, comando = sys.argv[1], sys.argv[2] == "1", sys.argv[3]
spec = importlib.util.spec_from_file_location("telemetria_sonda", codice)
t = importlib.util.module_from_spec(spec)
spec.loader.exec_module(t)
if vera:
    t.home_di_prova = lambda: False
if comando == "registra":
    t.main(["registra", "sessione"])
print(json.dumps({"spenta": t.perche_spenta(), "url": t.url()}))
"""


def sonda(codice: Path, home: Path, vera: bool, comando: str = "stato", **extra: str) -> dict:
    env = dict(os.environ, HOME=str(home), USERPROFILE=str(home))
    for chiave in ("ARTURO_TELEMETRIA", "DO_NOT_TRACK", "ARTURO_TELEMETRIA_URL", "CLAUDE_CONFIG_DIR"):
        env.pop(chiave, None)
    env.update(extra)
    r = subprocess.run([sys.executable, "-B", "-c", SONDA, str(codice), "1" if vera else "0", comando],
                       capture_output=True, text=True, encoding="utf-8", errors="replace", env=env, timeout=60)
    try:
        return json.loads(r.stdout.strip().splitlines()[-1])
    except (ValueError, IndexError):
        return {"errore": (r.stdout + r.stderr)[-300:]}


def prova(repo: Path) -> list[str]:
    rossi = []
    codice = repo / "bin" / "telemetria.py"
    with tempfile.TemporaryDirectory() as tmp:
        home = Path(tmp) / "home"
        (home / ".claude").mkdir(parents=True)
        coda = home / ".claude" / "data" / "telemetria" / "coda.jsonl"

        esito = sonda(codice, home, True, "registra")
        if esito.get("spenta") != "copia fuori dalla config" or coda.exists():
            rossi.append(f"TC01 codice fuori e HOME vera: {esito}, coda scritta: {coda.exists()}")

        shutil.copytree(repo / "bin", home / ".claude" / "bin")
        esito = sonda(home / ".claude" / "bin" / "telemetria.py", home, True)
        if "spenta" not in esito or esito["spenta"] is not None:
            rossi.append(f"TC02 codice dentro ~/.claude: {esito}")

        esito = sonda(codice, home, True, ARTURO_TELEMETRIA_URL="http://127.0.0.1:9")
        if "spenta" not in esito or esito["spenta"] is not None:
            rossi.append(f"TC03 codice fuori con un server indicato: {esito}")

        esito = sonda(codice, home, False)
        if "spenta" not in esito or esito["spenta"] is not None or "127.0.0.1:9" not in esito.get("url", ""):
            rossi.append(f"TC04 codice fuori con una HOME di prova: {esito}")

        esito = sonda(codice, home, True, CLAUDE_CONFIG_DIR=str(repo))
        if "spenta" not in esito or esito["spenta"] is not None:
            rossi.append(f"TC05 CLAUDE_CONFIG_DIR che contiene il codice: {esito}")
    return rossi


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument("--baseline-ref")
    argomenti = parser.parse_args()
    rossi = prova(Path(argomenti.repo).resolve())
    if argomenti.baseline_ref:
        codici = [r.split()[0] for r in rossi]
        assert codici == DISCRIMINANTI, f"baseline non discriminante: rossi {codici}, attesi {DISCRIMINANTI}"
        print(f"BASELINE_DISCRIMINANTE={','.join(codici)}")
        return 0
    for r in rossi:
        print("ROSSO", r)
    print(f"telemetria copia fuori: {len(CASI) - len(rossi)}/{len(CASI)} casi verdi")
    return 1 if rossi else 0


if __name__ == "__main__":
    sys.exit(main())
