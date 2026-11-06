#!/usr/bin/env python3
"""RD01-RD04: col plugin le regole consigliate da /setup che il CLAUDE.md della persona ripete (#4874, strati F5).

Prima del plugin /setup scriveva nel CLAUDE.md le regole di shared/setup-claude-md.md. Col plugin le stesse
regole arrivano col metodo all'avvio (hooks/metodo.sh), e nel contesto stanno due volte. Il CLAUDE.md è della
persona: `arturo personale regole-doppie` le elenca, e solo con --togli le toglie, con la copia di prima.

RD01 l'elenco trova le regole consigliate anche dentro un punto d'elenco con spazi diversi, esce 1, e il
     CLAUDE.md non cambia;
RD02 --togli toglie solo quelle righe, tiene le altre, lascia CLAUDE.md.prima-del-plugin uguale all'originale;
     rilanciato non trova più niente;
RD03 una regola riscritta dalla persona (stesso inizio di parole, testo suo) non è doppia;
RD04 nel clone (Orsa e codice nella stessa cartella) il metodo non arriva all'avvio: tace e non scrive.

Sulla base 3b5e6c3 (il dev prima) sono tutti rossi: il comando non c'è. Con --avvelena una copia del
repository rotta nel punto sorvegliato fa rosso il caso suo.
"""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

CASI = ["RD01", "RD02", "RD03", "RD04"]
DISCRIMINANTI = list(CASI)

PERSONALE = "- Un comando che dura più di tre minuti lo lancio io, da un Terminale mio.\n"
CLAUDE_MD = (
    "# Chi sono\nFederica, illustratrice.\n\n## Regole\n"
    "- Le azioni tecniche le  esegui tu — comandi, script, riavvii, verifiche. Chiedimi solo ciò che solo una persona può fare.\n"
    + PERSONALE +
    "Prima di ogni richiesta di lavoro, anche breve, riscrivi la mia richiesta come la eseguirai (il prompt).\n"
    "- Niente emoji.\n"
)


def regole(repo: Path, orsa: Path, *argomenti: str):
    env = {**os.environ, "ARTURO_RADICE": str(orsa), "ARTURO_TELEMETRIA": "0"}
    return subprocess.run([sys.executable, str(repo / "bin" / "personale.py"), "regole-doppie", *argomenti],
                          capture_output=True, text=True, encoding="utf-8", errors="replace", env=env, timeout=60)


def prova(repo: Path) -> list[str]:
    rossi = []
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        orsa = tmp / "orsa"
        orsa.mkdir()
        (orsa / "CLAUDE.md").write_text(CLAUDE_MD, encoding="utf-8")

        e1 = regole(repo, orsa)
        if e1.returncode != 1 or "REGOLE DOPPIE: 2 righe" not in e1.stdout or "riga 5" not in e1.stdout \
                or "riga 7" not in e1.stdout or (orsa / "CLAUDE.md").read_text(encoding="utf-8") != CLAUDE_MD:
            rossi.append(f"RD01 elenco: rc {e1.returncode}, {(e1.stdout + e1.stderr)[-200:]!r}")

        e2 = regole(repo, orsa, "--togli")
        dopo = (orsa / "CLAUDE.md").read_text(encoding="utf-8")
        copia = orsa / "CLAUDE.md.prima-del-plugin"
        e2b = regole(repo, orsa)
        if e2.returncode != 0 or "Le azioni tecniche" in dopo or "Prima di ogni richiesta" in dopo \
                or "Niente emoji" not in dopo or "Federica" not in dopo or not copia.exists() \
                or copia.read_text(encoding="utf-8") != CLAUDE_MD or e2b.returncode != 0:
            rossi.append(f"RD02 togli: rc {e2.returncode}/{e2b.returncode}, dopo {dopo[-160:]!r}")

        orsa3 = tmp / "orsa3"
        orsa3.mkdir()
        (orsa3 / "CLAUDE.md").write_text("## Regole\n" + PERSONALE, encoding="utf-8")
        e3 = regole(repo, orsa3)
        if e3.returncode != 0 or "non ripete" not in e3.stdout:
            rossi.append(f"RD03 regola riscritta: rc {e3.returncode}, {(e3.stdout + e3.stderr)[-200:]!r}")

        clone = tmp / "clone"
        shutil.copytree(repo, clone, ignore=shutil.ignore_patterns(".git", "__pycache__", "node_modules", "tests"))
        (clone / "CLAUDE.md").write_text(CLAUDE_MD, encoding="utf-8")
        e4 = regole(clone, clone, "--togli")
        if e4.returncode != 0 or "clone" not in e4.stdout or (clone / "CLAUDE.md").read_text(encoding="utf-8") != CLAUDE_MD:
            rossi.append(f"RD04 clone: rc {e4.returncode}, {(e4.stdout + e4.stderr)[-200:]!r}")
    return rossi


# (caso, file, testo giusto, testo rotto): ogni veleno toglie la riga che il caso sorveglia.
VELENI = [
    ("RD01", "bin/personale.py",
     "    return [i for i, riga in enumerate(testo.splitlines()) if any(piano(r) in piano(riga) for r in regole)]",
     "    return [i for i, riga in enumerate(testo.splitlines()) if any(r in riga for r in regole)]"),
    ("RD02", "bin/personale.py",
     'file.write_text("".join(x for i, x in enumerate(righe) if i not in set(doppie)), encoding="utf-8")',
     'file.write_text(testo, encoding="utf-8")'),
    ("RD03", "bin/personale.py", "INIZIO_REGOLA = 45", "INIZIO_REGOLA = 5"),
    ("RD04", "bin/personale.py",
     "    if Path(os.path.realpath(r)) == codice:\n        print(\"REGOLE: Arturo è un clone",
     "    if False:\n        print(\"REGOLE: Arturo è un clone"),
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
    print(f"regole doppie: {len(CASI) - len(rossi)}/{len(CASI)} casi verdi")
    return 1 if rossi else 0


if __name__ == "__main__":
    sys.exit(main())
