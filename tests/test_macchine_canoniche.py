#!/usr/bin/env python3
"""Il log degli accessi di Melchior col nome canonico della macchina (revisione del 22/11/2026, O10, #6416).

Una macchina che cambia nome (hostname, nome di rete) scriveva un log nuovo a ogni nome: la stessa macchina
finiva in tre file. data/macchine.json della persona dà a ogni macchina un nome canonico e i suoi alias.

MC01 con data/macchine.json, un nome di rete che è un alias (maiuscole diverse, suffisso .local) scrive nel
     log del nome canonico; anche un alias scritto con .local nel file vale.
MC02 senza data/macchine.json, o con un file rotto, il nome resta quello della macchina, come prima.
MC03 un nome che il file non conosce resta il nome della macchina, ripulito per un nome di file.

Ogni caso gira in un processo con una radice finta (CLAUDE_CONFIG_DIR) e platform.node() finto.
Veleno: --avvelena rompe nella copia di prova un punto per caso, ed esce 0 solo se ogni rottura fa rosso il suo caso.
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

REPO = Path(__file__).resolve().parent.parent
CASI = ["MC01", "MC02", "MC03"]
MM = "hooks/melchior_match.py"
# caso -> (testo, testo rotto)
VELENI = {
    "MC01": ("pieno = nodo.lower()", "pieno = nodo"),
    "MC02": ("            _CANONICI = {}\n    return _CANONICI", "            raise\n    return _CANONICI"),
    "MC03": ('or nodo.split(".")[0]', 'or "prova"'),
}

SONDA = r"""
import platform, sys
sys.path.insert(0, sys.argv[1])
platform.node = lambda: sys.argv[2]
import melchior_match as mm
print(mm.access_host())
print(mm.access_log_path().name)
"""

MACCHINE = {"versione": 1, "macchine": {
    "ufficio": {"claude_code": True, "alias": ["Mac-di-Prova", "computer di prova"]},
    "portatile": {"claude_code": True, "alias": ["Portatile-176.local"]},
}}


def host(hooks: Path, radice: Path, nodo: str) -> tuple[str, str]:
    env = {**os.environ, "CLAUDE_CONFIG_DIR": str(radice), "PYTHONIOENCODING": "utf-8"}
    p = subprocess.run([sys.executable, "-c", SONDA, str(hooks), nodo], capture_output=True, text=True,
                       env=env, timeout=30)
    if p.returncode != 0:
        return "errore", p.stderr.strip().splitlines()[-1] if p.stderr.strip() else ""
    righe = p.stdout.strip().splitlines()
    return righe[0], righe[1]


def casi(hooks: Path) -> dict[str, str]:
    """caso -> "" se verde, altrimenti il motivo."""
    esiti = {}
    with tempfile.TemporaryDirectory() as t:
        radice = Path(t)
        (radice / "data").mkdir()
        f = radice / "data" / "macchine.json"
        f.write_text(json.dumps(MACCHINE), encoding="utf-8")
        a = host(hooks, radice, "mac-di-prova.local")
        b = host(hooks, radice, "PORTATILE-176")
        esiti["MC01"] = "" if a == ("ufficio", "ufficio.log") and b[0] == "portatile" else f"alias: {a} {b}"

        f.write_text("{rotto", encoding="utf-8")
        a = host(hooks, radice, "Mac-di-Prova.local")
        f.unlink()
        b = host(hooks, radice, "Mac-di-Prova.local")
        esiti["MC02"] = "" if a[0] == "Mac-di-Prova" and b[0] == "Mac-di-Prova" else f"senza file: {a} {b}"

        f.write_text(json.dumps(MACCHINE), encoding="utf-8")
        a = host(hooks, radice, "Altra Macchina.local")
        esiti["MC03"] = "" if a == ("Altra-Macchina", "Altra-Macchina.log") else f"nome ignoto: {a}"
    return esiti


def avvelena() -> int:
    rossi = 0
    for caso, (testo, rotto) in VELENI.items():
        with tempfile.TemporaryDirectory() as t:
            hooks = Path(t) / "hooks"
            shutil.copytree(REPO / "hooks", hooks, ignore=shutil.ignore_patterns("__pycache__"))
            f = Path(t) / MM
            sorgente = f.read_text(encoding="utf-8")
            if sorgente.count(testo) != 1:
                print(f"ROSSO {caso} veleno da rivedere: il testo non c'è una volta sola")
                rossi += 1
                continue
            f.write_text(sorgente.replace(testo, rotto), encoding="utf-8")
            esito = casi(hooks)[caso]
            if esito:
                print(f"ok   {caso} rosso col veleno ({esito})")
            else:
                print(f"ROSSO {caso} resta verde col veleno")
                rossi += 1
    return 1 if rossi else 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--avvelena", action="store_true")
    ap.add_argument("--repo", type=Path, help="la copia del repository da provare (il gate la passa)")
    a = ap.parse_args()
    global REPO
    if a.repo:
        REPO = a.repo.resolve()
    if a.avvelena:
        return avvelena()
    esiti = casi(REPO / "hooks")
    for caso in CASI:
        print(f"{'ok  ' if not esiti[caso] else 'ROSSO'} {caso} {esiti[caso]}".rstrip())
    rossi = sum(1 for v in esiti.values() if v)
    print(f"macchine canoniche: {len(CASI) - rossi}/{len(CASI)} verdi")
    return 1 if rossi else 0


if __name__ == "__main__":
    sys.exit(main())
