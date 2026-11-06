#!/usr/bin/env python3
"""RD01-RD09: col plugin le regole consigliate da /setup che il CLAUDE.md della persona ripete (#4874, strati F5).

Prima del plugin /setup scriveva nel CLAUDE.md le regole di shared/setup-claude-md.md. Col plugin le stesse
regole arrivano col metodo all'avvio (hooks/metodo.sh), e nel contesto stanno due volte. Il CLAUDE.md è della
persona: `arturo personale regole-doppie` le elenca, e solo con --togli le toglie, con la copia di prima.

RD01 l'elenco trova le regole consigliate anche dentro un punto d'elenco con spazi diversi, esce 1, e il
     CLAUDE.md non cambia;
RD02 --togli toglie solo quelle righe, tiene le altre, lascia CLAUDE.md.prima-del-plugin uguale all'originale;
     rilanciato non trova più niente;
RD03 una regola scritta dalla persona con parole simili non è doppia e non somiglia;
RD04 nel clone (Orsa e codice nella stessa cartella) il metodo non arriva all'avvio: tace e non scrive;
RD05 una riga con l'inizio della regola e un testo suo, anche contrario, si elenca come simile e resta;
RD06 una regola con un seguito rientrato resta, così l'eccezione non perde la sua riga;
RD07 un secondo --togli ha la sua copia: niente di quello che il primo non aveva visto si perde;
RD08 un CLAUDE.md con gli a capo CRLF li tiene;
RD09 il CLAUDE.md si cerca in CLAUDE_CONFIG_DIR, come fa Claude Code.

Sulla base 3b5e6c3 (il dev prima) sono tutti rossi: il comando non c'è. Con --avvelena una copia del
repository rotta nel punto sorvegliato fa rosso il caso suo.
"""
from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

CASI = ["RD01", "RD02", "RD03", "RD04", "RD05", "RD06", "RD07", "RD08", "RD09"]
DISCRIMINANTI = list(CASI)

PERSONALE = "- Un comando che dura più di tre minuti lo lancio io, da un Terminale mio.\n"


def regola(repo: Path, numero: int) -> str:
    """La regola n. numero come /setup la scrive nel CLAUDE.md."""
    for riga in (repo / "shared" / "setup-claude-md.md").read_text(encoding="utf-8").splitlines():
        m = re.match(rf'^{numero}\. "(.*?)"(?: \(|$)', riga)
        if m:
            return m.group(1)
    raise AssertionError(f"manca la regola {numero} in shared/setup-claude-md.md")


def regole(repo: Path, orsa: Path, *argomenti: str, env_extra: dict | None = None):
    env = {**os.environ, "ARTURO_RADICE": str(orsa), "ARTURO_TELEMETRIA": "0", **(env_extra or {})}
    env = {k: v for k, v in env.items() if v is not None}
    return subprocess.run([sys.executable, str(repo / "bin" / "personale.py"), "regole-doppie", *argomenti],
                          capture_output=True, text=True, encoding="utf-8", errors="replace", env=env, timeout=60)


def prova(repo: Path) -> list[str]:
    rossi = []
    uno, due = regola(repo, 1), regola(repo, 2)
    CLAUDE_MD = ("# Chi sono\nFederica, illustratrice.\n\n## Regole\n- "
                 + uno.replace("le esegui", "le  esegui") + "\n" + PERSONALE + due + "\n- Niente emoji.\n")
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
        if e3.returncode != 0 or "non ripete" not in e3.stdout or "REGOLE SIMILI" in e3.stdout:
            rossi.append(f"RD03 regola riscritta: rc {e3.returncode}, {(e3.stdout + e3.stderr)[-200:]!r}")

        clone = tmp / "clone"
        shutil.copytree(repo, clone, ignore=shutil.ignore_patterns(".git", "__pycache__", "node_modules", "tests"))
        (clone / "CLAUDE.md").write_text(CLAUDE_MD, encoding="utf-8")
        e4 = regole(clone, clone, "--togli")
        if e4.returncode != 0 or "clone" not in e4.stdout or (clone / "CLAUDE.md").read_text(encoding="utf-8") != CLAUDE_MD:
            rossi.append(f"RD04 clone: rc {e4.returncode}, {(e4.stdout + e4.stderr)[-200:]!r}")

        orsa5 = tmp / "orsa5"
        orsa5.mkdir()
        contraria = f"# Mio\n- {due[:60]} NO: parti subito, niente brief.\n"
        (orsa5 / "CLAUDE.md").write_text(contraria, encoding="utf-8")
        e5 = regole(repo, orsa5, "--togli")
        if e5.returncode != 0 or "REGOLE SIMILI: 1" not in e5.stdout \
                or (orsa5 / "CLAUDE.md").read_text(encoding="utf-8") != contraria:
            rossi.append(f"RD05 riga simile: rc {e5.returncode}, {(e5.stdout + e5.stderr)[-200:]!r}")

        orsa6 = tmp / "orsa6"
        orsa6.mkdir()
        con_seguito = f"# Mio\n- {uno}\n  Eccezione: sul server chiedimi prima.\n"
        (orsa6 / "CLAUDE.md").write_text(con_seguito, encoding="utf-8")
        e6 = regole(repo, orsa6, "--togli")
        if e6.returncode != 0 or (orsa6 / "CLAUDE.md").read_text(encoding="utf-8") != con_seguito:
            rossi.append(f"RD06 seguito rientrato: rc {e6.returncode}, {(e6.stdout + e6.stderr)[-200:]!r}")

        orsa7 = tmp / "orsa7"
        orsa7.mkdir()
        (orsa7 / "CLAUDE.md").write_text(f"# Mio\n- {uno}\n", encoding="utf-8")
        regole(repo, orsa7, "--togli")
        secondo = f"# Mio\nRiga scritta dopo.\n- {due}\n"
        (orsa7 / "CLAUDE.md").write_text(secondo, encoding="utf-8")
        e7 = regole(repo, orsa7, "--togli")
        copia7 = orsa7 / "CLAUDE.md.prima-del-plugin.2"
        if e7.returncode != 0 or copia7.name not in e7.stdout or not copia7.exists() \
                or copia7.read_text(encoding="utf-8") != secondo:
            rossi.append(f"RD07 secondo giro: rc {e7.returncode}, copia {copia7.exists()}, {e7.stdout[-160:]!r}")

        orsa8 = tmp / "orsa8"
        orsa8.mkdir()
        (orsa8 / "CLAUDE.md").write_bytes(f"# Mio\r\n- {uno}\r\nAltra\r\n".encode("utf-8"))
        e8 = regole(repo, orsa8, "--togli")
        if e8.returncode != 0 or (orsa8 / "CLAUDE.md").read_bytes() != b"# Mio\r\nAltra\r\n":
            rossi.append(f"RD08 CRLF: rc {e8.returncode}, {(orsa8 / 'CLAUDE.md').read_bytes()[:40]!r}")

        orsa9 = tmp / "orsa9"
        orsa9.mkdir()
        (orsa9 / "CLAUDE.md").write_text(f"- {uno}\n", encoding="utf-8")
        e9 = regole(repo, orsa9, env_extra={"ARTURO_RADICE": None, "CLAUDE_CONFIG_DIR": str(orsa9)})
        if e9.returncode != 1 or "REGOLE DOPPIE: 1" not in e9.stdout:
            rossi.append(f"RD09 CLAUDE_CONFIG_DIR: rc {e9.returncode}, {(e9.stdout + e9.stderr)[-200:]!r}")
    return rossi


# (caso, file, testo giusto, testo rotto): ogni veleno toglie la riga che il caso sorveglia.
VELENI = [
    ("RD01", "bin/personale.py",
     '        nuda = piano(re.sub(r"^\\s*(?:[-*+]|\\d+[.)])\\s+", "", riga))',
     "        nuda = riga"),
    ("RD02", "bin/personale.py",
     'f.write("".join(x for i, x in enumerate(righe) if i not in set(doppie)))',
     'f.write(testo)'),
    ("RD03", "bin/personale.py", "INIZIO_REGOLA = 45", "INIZIO_REGOLA = 5"),
    ("RD04", "bin/personale.py",
     "    if Path(os.path.realpath(r)) == codice:\n        print(\"REGOLE: Arturo è un clone",
     "    if False:\n        print(\"REGOLE: Arturo è un clone"),
    ("RD05", "bin/personale.py", "        if nuda in intere and not seguito:",
     "        if any(inizio in nuda for inizio in inizi) and not seguito:"),
    ("RD06", "bin/personale.py", "        if nuda in intere and not seguito:", "        if nuda in intere:"),
    ("RD07", "bin/personale.py", "    while copia.exists():\n", "    while False:\n"),
    ("RD08", "bin/personale.py", '        with open(file, encoding="utf-8", newline="") as f:',
     '        with open(file, encoding="utf-8") as f:'),
    ("RD09", "bin/personale.py", 'os.environ.get("ARTURO_RADICE") or os.environ.get("CLAUDE_CONFIG_DIR") or',
     'os.environ.get("ARTURO_RADICE") or'),
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
