#!/usr/bin/env python3
"""/monitor in Arturo, primo avvio (3/11/2026, #4538): skill monitor, fonti scelte, schema delle righe,
fingerprint e cursori generici.

MG01 primo avvio: con la casa vuota `fonti.py mostra` esce 3; `scrivi` con ponti leggibili scrive
     fonti.json con la finestra di serie e quella chiesta; un ponte da collegare, uno inesistente o una
     finestra fuori misura escono con 2 e non toccano il file.
MG02 schema delle righe: una consegna buona passa intera, con fp e hash; una riga senza un campo, con
     un'urgenza inventata, con un campo personale (cifra), con testo libero nel fingerprint o non JSON è
     scartata col motivo; una fonte con item e senza copertura fa uscire 1. Gli accenti passano intatti
     dallo standard input anche su Windows, dove il default è cp1252.
MG03 fingerprint stabile: la stessa stringa dà lo stesso hash (8 caratteri dell'md5) e due stringhe
     diverse due hash; testo con spazi, fonte maiuscola o pezzo vuoto escono con 2.
MG04 cursori: una fonte mai letta vale 7 giorni; dopo `avanza --alle` la finestra conta dal cursore; un
     --alle nel futuro o assente non tocca niente; il file è cursori.json, non stato.json.
MG05 skill: skills/monitor/SKILL.md ha name: monitor, chiama fonti.py e ponti.py da ${CLAUDE_SKILL_DIR},
     e ogni file di bin/monitor che nomina esiste.

Con --avvelena quattro copie rotte del repository devono far rosso il caso che le sorveglia: righe.py che
accetta un'urgenza inventata (MG02), righe.py che legge lo standard input con la codifica di sistema
(MG02), fingerprint.py che accetta gli spazi (MG03), cursori.py che scrive stato.json (MG04). Sulla base 9248ea9 (il dev prima dello smistamento) sono rossi tutti i casi.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

CASI = ("MG01", "MG02", "MG03", "MG04", "MG05")


class Lab:
    """Una casa finta per ogni caso, come la Lab del banco dei ponti (MP)."""

    def __init__(self, repo: Path, tmp: Path):
        self.repo, self.tmp = repo, tmp
        self.cartella = repo / "bin" / "monitor"

    def casa(self, nome):
        c = self.tmp / nome
        for d in ("home", "config", "bin", "path"):
            (c / d).mkdir(parents=True)
        finto = c / "path" / "gws"
        finto.write_text("#!/bin/sh\nexit 127\n")
        finto.chmod(0o755)
        return c

    def lancia(self, c, script, *arg, stdin=None):
        file = self.cartella / script
        if not file.is_file():
            return 127, "", f"{script} assente"
        # PYTHONIOENCODING=cp1252: il default di Windows anche su Mac e Linux, così gli accenti si provano ovunque.
        env = dict(os.environ, ARTURO_HOME=str(c / "home"), GWS_CONFIG_BASE=str(c / "config"),
                   ARTURO_BIN=str(c / "bin"), PATH=f"{c / 'path'}{os.pathsep}{os.environ.get('PATH', '')}",
                   PYTHONIOENCODING="cp1252")
        r = subprocess.run([sys.executable, str(file), *arg], capture_output=True, text=True, encoding="utf-8",
                           input=stdin, env=env, timeout=60)
        return r.returncode, r.stdout, r.stderr


def item(**campi):
    base = {"tipo": "item", "fonte": "email", "id_sorgente": "1a0f7a23d0379a35", "data": "2026-11-03",
            "scadenza": None, "progetto": "sito", "riassunto": "Una persona aspetta le foto", "urgenza": "giallo",
            "promessa": None, "extra": {}}
    base.update(campi)
    return {k: v for k, v in base.items() if v != "-"}


def copertura(fonte="email"):
    return {"tipo": "copertura", "fonte": fonte, "listati": 3, "letti": 3, "troncato": False}


def jsonl(*righe):
    # ensure_ascii=False: gli accenti arrivano come byte UTF-8, come da un ponte vero, non come è.
    return "".join((r if isinstance(r, str) else json.dumps(r, ensure_ascii=False)) + "\n" for r in righe)


def prova(lab: Lab) -> list:
    rossi = []

    # MG01
    c = lab.casa("mg01")
    file = c / "home" / "data" / "monitor" / "fonti.json"
    (c / "home" / "data" / "handoffs").mkdir(parents=True)
    (c / "home" / "data" / "handoffs" / "INDEX.md").write_text("- prova HANDOFF_2026-11-03.md\n")
    m1, _, _ = lab.lancia(c, "fonti.py", "mostra")
    s1, out1, err1 = lab.lancia(c, "fonti.py", "scrivi", "task", "sessioni=3")
    try:
        dati = json.loads(file.read_text(encoding="utf-8"))
        scelte = {f["nome"]: f["finestra"] for f in dati["fonti"]}
    except (OSError, ValueError, KeyError, TypeError):
        scelte = None
    m2, _, _ = lab.lancia(c, "fonti.py", "mostra")
    prima = file.read_bytes() if file.is_file() else b""
    ko = [lab.lancia(c, "fonti.py", "scrivi", *a)[0] for a in
          (["memoria"], ["inventato"], ["task=0"], ["task", "task"], [])]
    intatto = file.is_file() and file.read_bytes() == prima
    if not (m1 == 3 and s1 == 0 and scelte == {"task": 7, "sessioni": 3} and m2 == 0
            and ko == [2] * 5 and intatto):
        rossi.append(f"MG01 primo avvio: mostra {m1}/{m2}, scrivi {s1} {scelte}, rifiuti {ko}, intatto {intatto}, "
                     f"{(err1 or out1).strip()[:100]}")

    # MG02
    c = lab.casa("mg02")
    accentato = "Perché la bozza è già lì: più tardi"
    buona = jsonl(item(), item(id_sorgente="1b2c3d4e5f607182", fp="email:1b2c3d4e5f607182:2026-11-03",
                               riassunto=accentato), copertura(), copertura("task"))
    cod, out, err = lab.lancia(c, "righe.py", stdin=buona)
    try:
        valide = [json.loads(r) for r in out.splitlines() if r.strip()]
    except ValueError:
        valide = []
    hash_ok = (len(valide) == 4 and valide[0].get("fp") == "email:1a0f7a23d0379a35"
               and valide[0].get("hash") == hashlib.md5(b"email:1a0f7a23d0379a35").hexdigest()[:8]
               and valide[1].get("fp") == "email:1b2c3d4e5f607182:2026-11-03"
               and valide[1].get("riassunto") == accentato)
    if not (cod == 0 and hash_ok):
        rossi.append(f"MG02 consegna buona: exit {cod}, valide {len(valide)}, {err.strip()[:120]}")
    cattive = {
        "senza urgenza": (item(urgenza="-"), "mancano urgenza"),
        "urgenza inventata": (item(urgenza="arancio"), "urgenza"),
        "campo personale": (item(cifra={"valore": "10 €"}), "campo cifra"),
        "testo libero": (item(fp="email:la mail di ieri"), "spazi"),
        "data sbagliata": (item(data="3/11/2026"), "data"),
        "non json": ("{rotto", "non è JSON"),
    }
    for nome, (riga, motivo) in cattive.items():
        cod, out, err = lab.lancia(c, "righe.py", stdin=jsonl(riga, copertura()))
        passate = [r for r in out.splitlines() if '"item"' in r]
        if cod != 1 or passate or motivo not in err:
            rossi.append(f"MG02 riga {nome}: exit {cod}, passate {len(passate)}, motivo atteso {motivo!r}, "
                         f"stderr {err.strip()[:120]!r}")
    cod, _, err = lab.lancia(c, "righe.py", stdin=jsonl(item()))
    if cod != 1 or "manca la riga di copertura" not in err:
        rossi.append(f"MG02 copertura mancante: exit {cod}, {err.strip()[:120]!r}")

    # MG03
    c = lab.casa("mg03")
    a1 = lab.lancia(c, "fingerprint.py", "task:12:2026-11-03")
    a2 = lab.lancia(c, "fingerprint.py", "task:12:2026-11-03")
    b = lab.lancia(c, "fingerprint.py", "task:13:2026-11-03")
    atteso = hashlib.md5(b"task:12:2026-11-03").hexdigest()[:8]
    rifiuti = [lab.lancia(c, "fingerprint.py", s)[0] for s in ("task:la cosa di ieri", "Task:12", "task::12", "task")]
    if not (a1[0] == 0 and a1[1] == a2[1] and a1[1].split("\t")[0] == atteso and b[1].split("\t")[0] != atteso
            and rifiuti == [2] * 4):
        rossi.append(f"MG03 fingerprint: {a1[1].strip()!r} contro {atteso}, rifiuti {rifiuti}")

    # MG04
    c = lab.casa("mg04")
    f0 = lab.lancia(c, "cursori.py", "finestra", "email", "2")[1].strip()
    tre_giorni = (datetime.now() - timedelta(days=3)).strftime("%Y-%m-%dT%H:%M")
    av = lab.lancia(c, "cursori.py", "avanza", "--alle", tre_giorni, "email")[0]
    f1 = lab.lancia(c, "cursori.py", "finestra", "email", "2")[1].strip()
    file = c / "home" / "data" / "monitor" / "cursori.json"
    prima = file.read_bytes() if file.is_file() else b""
    futuro = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%dT%H:%M")
    ko = [lab.lancia(c, "cursori.py", *a)[0] for a in
          (["avanza", "--alle", futuro, "email"], ["avanza", "email"], ["finestra", "email", "x"])]
    intatto = file.is_file() and file.read_bytes() == prima
    stato = (c / "home" / "data" / "monitor" / "stato.json").exists()
    if not (f0 == "7" and av == 0 and f1 == "4" and ko == [2] * 3 and intatto and not stato):
        rossi.append(f"MG04 cursori: finestra {f0!r}/{f1!r}, avanza {av}, rifiuti {ko}, intatto {intatto}, "
                     f"stato.json {stato}")

    # MG05
    skill = lab.repo / "skills" / "monitor" / "SKILL.md"
    testo = skill.read_text(encoding="utf-8") if skill.is_file() else ""
    citati = sorted(set(re.findall(r"bin/monitor/([a-z_]+\.(?:py|md))", testo)))
    nominati = sorted(set(re.findall(r"`([a-z_]+\.py)`", testo)))
    mancano = [n for n in set(citati) | set(nominati) if not (lab.cartella / n).is_file()]
    if not (testo.startswith("---\nname: monitor\n") and '"${CLAUDE_SKILL_DIR}/../../bin/monitor/fonti.py"' in testo
            and '"${CLAUDE_SKILL_DIR}/../../bin/monitor/ponti.py"' in testo and not mancano):
        rossi.append(f"MG05 skill: presente {skill.is_file()}, citati {citati}, mancano {sorted(mancano)}")
    return rossi


# (caso, file, [(testo giusto, testo rotto)], motivo atteso nel rosso)
VELENI = [
    ("MG02", "bin/monitor/righe.py", [('    if r["urgenza"] not in URGENZE:', "    if False:")],
     "MG02 riga urgenza inventata"),
    ("MG02", "bin/monitor/righe.py", [('sys.stdin.buffer.read().decode("utf-8")', "sys.stdin.read()")],
     "MG02 consegna buona"),
    ("MG03", "bin/monitor/fingerprint.py",
     [('    if re.search(r"\\s", s):', "    if False:"),
      (r'FORMA = re.compile(r"^[a-z][a-z0-9-]{0,39}(?::[^\s:]+)+$")', 'FORMA = re.compile(r"^[a-z].*$")')],
     "MG03 fingerprint"),
    ("MG04", "bin/monitor/cursori.py",
     [('FILE = CASA / "data" / "monitor" / "cursori.json"', 'FILE = CASA / "data" / "monitor" / "stato.json"')],
     "stato.json True"),
]


def avvelena(repo: Path) -> int:
    esiti = []
    for caso, rel, cambi, motivo in VELENI:
        with tempfile.TemporaryDirectory(prefix="arturo-mg-v-") as tmp:
            copia = Path(tmp) / "repo"
            shutil.copytree(repo, copia, ignore=shutil.ignore_patterns(".git", "__pycache__", "node_modules", "tests", "cache"))
            testo = (copia / rel).read_text(encoding="utf-8")
            for giusto, rotto in cambi:
                assert testo.count(giusto) == 1, f"veleno {caso}: il testo da rompere non c'è più in {rel}"
                testo = testo.replace(giusto, rotto)
            (copia / rel).write_text(testo, encoding="utf-8")
            (Path(tmp) / "lab").mkdir()
            rossi = prova(Lab(copia, Path(tmp) / "lab"))
            colpiti = [r for r in rossi if r.startswith(caso) and motivo in r]
            if not colpiti:
                print(f"VELENO {caso} NON ATTACCA: rossi {[r[:60] for r in rossi]}, atteso {motivo!r}")
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
    with tempfile.TemporaryDirectory(prefix="arturo-mg-") as tmp:
        rossi = prova(Lab(repo, Path(tmp)))
    if a.baseline_ref:
        codici = sorted({r.split()[0] for r in rossi})
        assert codici == list(CASI), f"baseline non discriminante: rossi {codici}, attesi {list(CASI)}"
        print(f"BASELINE_DISCRIMINANTE={','.join(codici)}")
        return 0
    for r in rossi:
        print("ROSSO", r)
    print(f"primo avvio di /monitor: {len(CASI) - len({r.split()[0] for r in rossi})}/{len(CASI)} casi verdi")
    return 1 if rossi else 0


if __name__ == "__main__":
    raise SystemExit(main())
