#!/usr/bin/env python3
"""SO01-SO05: col plugin le skill omonime della persona si dichiarano in personale/sostituzioni.txt (strati F5).

Col plugin una skill, un comando o uno stile della persona con lo stesso nome di uno di Arturo prende il
nome nudo, e quello di Arturo resta come arturo:<nome> (docs/strati.md, prova del 2/11/2026). Federico
tiene così la sua /inizio, /fine, monitor, system-audit, prompt-master e lo stile Conciso. Una skill
nuova di Arturo con un nome che la persona usa già sparirebbe in silenzio: per questo ogni sostituzione
si dichiara, e `arturo personale omonimi` nomina quelle non dichiarate.

SO01 un omonimo non dichiarato esce con 1 e si nomina, con la sua cartella e il nome arturo:<nome>;
SO02 dichiarati tutti (anche uno stile, dal name: del frontmatter, e un /nome scritto con la barra) esce
     con 0 ed elenca i sostituiti;
SO03 una riga dichiarata senza omonimo si nomina ed esce con 1;
SO04 nel clone (Orsa e codice nella stessa cartella) tace, e un link dell'Orsa che porta dentro il
     codice di Arturo (il mod collegato) non è un omonimo;
SO05 il system-audit di Arturo riporta l'omonimo non dichiarato come WARN.

Sulla base e87ce62 (il dev prima di questo passo) sono tutti rossi: il comando omonimi non c'è.
Con --avvelena una copia del repository rotta nel punto sorvegliato fa rosso il caso suo.
"""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

CASI = ["SO01", "SO02", "SO03", "SO04", "SO05"]
DISCRIMINANTI = list(CASI)
BASH = shutil.which("bash") or "bash"


def esegui(argv, **kw):
    return subprocess.run(argv, capture_output=True, text=True, encoding="utf-8", errors="replace",
                          timeout=120, **kw)


def orsa_con(tmp: Path, nome: str, dichiarate: str | None) -> Path:
    """Un'Orsa con /inizio (comando), monitor (skill), lo stile Conciso e una skill solo sua."""
    orsa = tmp / nome
    (orsa / "commands").mkdir(parents=True)
    (orsa / "commands" / "inizio.md").write_text("# la mia /inizio\n", encoding="utf-8")
    (orsa / "skills" / "monitor").mkdir(parents=True)
    (orsa / "skills" / "monitor" / "SKILL.md").write_text("---\nname: monitor\n---\nmio\n", encoding="utf-8")
    (orsa / "skills" / "solo-mia").mkdir(parents=True)
    (orsa / "skills" / "solo-mia" / "SKILL.md").write_text("---\nname: solo-mia\n---\n", encoding="utf-8")
    (orsa / "output-styles").mkdir()
    (orsa / "output-styles" / "mio-stile.md").write_text("---\nname: Conciso\n---\nmio\n", encoding="utf-8")
    if dichiarate is not None:
        (orsa / "personale").mkdir()
        (orsa / "personale" / "sostituzioni.txt").write_text(dichiarate, encoding="utf-8")
    return orsa


def omonimi(repo: Path, orsa: Path):
    env = {**os.environ, "ARTURO_RADICE": str(orsa), "ARTURO_TELEMETRIA": "0"}
    return esegui([sys.executable, str(repo / "bin" / "personale.py"), "omonimi"], env=env)


def prova(repo: Path) -> list[str]:
    rossi = []
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)

        orsa1 = orsa_con(tmp, "orsa1", "inizio  # la tengo mia\n")
        e1 = omonimi(repo, orsa1)
        if e1.returncode != 1 or "OMONIMO NON DICHIARATO: monitor" not in e1.stdout \
                or "skills/monitor" not in e1.stdout or "arturo:monitor" not in e1.stdout \
                or "NON DICHIARATO: inizio" in e1.stdout or "solo-mia" in e1.stdout:
            rossi.append(f"SO01 non dichiarato: rc {e1.returncode}, {(e1.stdout + e1.stderr)[-220:]!r}")

        orsa2 = orsa_con(tmp, "orsa2", "# le mie\n/inizio\nmonitor   # la mia\nConciso\n\n")
        e2 = omonimi(repo, orsa2)
        if e2.returncode != 0 or "SOSTITUITI:" not in e2.stdout \
                or not all(f"{n} (Arturo: arturo:{n})" in e2.stdout for n in ("inizio", "monitor", "Conciso")) \
                or "NON DICHIARATO" in e2.stdout:
            rossi.append(f"SO02 tutti dichiarati: rc {e2.returncode}, {(e2.stdout + e2.stderr)[-220:]!r}")

        orsa3 = orsa_con(tmp, "orsa3", "inizio\nmonitor\nConciso\nsparita\n")
        e3 = omonimi(repo, orsa3)
        if e3.returncode != 1 or "DICHIARATO SENZA OMONIMO: sparita" not in e3.stdout:
            rossi.append(f"SO03 dichiarato senza omonimo: rc {e3.returncode}, {(e3.stdout + e3.stderr)[-220:]!r}")

        e4 = omonimi(repo, repo)
        orsa4 = tmp / "orsa4"
        (orsa4 / "skills").mkdir(parents=True)
        collegato = True
        try:
            os.symlink(repo / "skills" / "monitor", orsa4 / "skills" / "monitor", target_is_directory=True)
        except OSError:
            collegato = False  # Windows senza permesso di link: resta la sola parte del clone
        e4b = omonimi(repo, orsa4)
        if e4.returncode != 0 or "clone" not in e4.stdout or (collegato and (
                e4b.returncode != 0 or "monitor" in e4b.stdout)):
            rossi.append(f"SO04 clone e link nel codice: rc {e4.returncode}/{e4b.returncode}, "
                         f"{(e4.stdout + e4b.stdout + e4b.stderr)[-220:]!r}")

        casa = tmp / "casa"
        shutil.copytree(orsa1, casa / ".claude", symlinks=True)
        (casa / ".claude" / "settings.json").write_text("{}\n", encoding="utf-8")
        audit = esegui([BASH, str(repo / "skills" / "system-audit" / "audit.sh")],
                       env={**os.environ, "HOME": str(casa), "USERPROFILE": str(casa), "ARTURO_TELEMETRIA": "0"})
        warn = [r for r in audit.stdout.splitlines() if r.startswith("WARN") and "OMONIMO NON DICHIARATO: monitor" in r]
        if len(warn) != 1:
            rossi.append(f"SO05 system-audit: {len(warn)} righe WARN sull'omonimo, {audit.stdout[-200:]!r}")
    return rossi


# (caso, file, testo giusto, testo rotto): ogni veleno toglie la riga che il caso sorveglia.
VELENI = [
    ("SO01", "bin/personale.py", "        if n not in voluti:\n            esito = 1", "        if False:\n            esito = 1"),
    ("SO02", "bin/personale.py", '.lstrip("/")', ""),
    ("SO03", "bin/personale.py", "    for n in voluti:\n        if n not in comuni:", "    for n in []:\n        if n not in comuni:"),
    ("SO04", "bin/personale.py", "            if vero == codice or codice in vero.parents:\n                continue",
     "            if False:\n                continue"),
    ("SO05", "skills/system-audit/audit.sh", '"OMONIMO NON DICHIARATO:"*|', ""),
]


def avvelena(repo: Path) -> int:
    esiti = []
    for caso, rel, giusto, rotto in VELENI:
        with tempfile.TemporaryDirectory() as tmp:
            copia = Path(tmp) / "repo"
            shutil.copytree(repo, copia, ignore=shutil.ignore_patterns(".git", "__pycache__", "node_modules", "tests"))
            testo = (copia / rel).read_text(encoding="utf-8")
            assert testo.count(giusto) == 1, f"veleno {caso}: il testo da rompere non c'è più in {rel}"
            (copia / rel).write_text(testo.replace(giusto, rotto), encoding="utf-8")
            rossi = prova(copia)
            codici = [r.split()[0] for r in rossi]
            if caso not in codici:
                print(f"VELENO {caso} NON ATTACCA: rossi {codici}")
                return 1
            print(f"VELENO {caso} ROSSO: {next(r for r in rossi if r.startswith(caso))[:120]}")
            esiti.append(caso)
    print(f"VELENI_ROSSI={','.join(esiti)} veleni={len(VELENI)}")
    return 0 if len(esiti) == len(VELENI) else 1


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument("--baseline-ref")
    parser.add_argument("--avvelena", action="store_true")
    argomenti = parser.parse_args()
    if argomenti.avvelena:
        return avvelena(Path(argomenti.repo))
    rossi = prova(Path(argomenti.repo))
    if argomenti.baseline_ref:
        codici = [r.split()[0] for r in rossi]
        assert codici == DISCRIMINANTI, f"baseline non discriminante: rossi {codici}, attesi {DISCRIMINANTI}"
        print(f"BASELINE_DISCRIMINANTE={','.join(codici)}")
        return 0
    for r in rossi:
        print("ROSSO", r)
    print(f"sostituzioni: {len(CASI) - len(rossi)}/{len(CASI)} casi verdi")
    return 1 if rossi else 0


if __name__ == "__main__":
    sys.exit(main())
