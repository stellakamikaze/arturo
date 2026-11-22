#!/usr/bin/env python3
"""PC01-PC06: con `git -C` la guardia dei segreti legge solo i file del git add (22/11/2026, #6289).

Con `git -C <cartella> add f && git -C <cartella> commit` la guardia leggeva tutti i file nuovi non tracciati.
Su un computer, in 30 giorni, ha chiesto decine di volte "ha letto 374 file nuovi su 1337" su commit di un file
solo: è la causa troppi-file. Lavorandoci è uscito un buco: il -C di un git valeva anche per i comandi dopo, e
`git -C altro status && git commit` faceva leggere alla guardia l'altro repository.

PC01 stesso -C assoluto su add e commit: un segreto in un file fuori dal pathspec non fa chiedere.
PC02 stesso -C, 120 file da 200 KB oltre il tetto: `git add` di un file solo tace (prima: troppi-file).
PC03 stesso -C relativo su add e commit: la guardia trova il repository e tace (prima: cartella che non esiste).
PC04 il -C vale solo per il suo git: dopo `git -C altro status`, il commit nella cartella corrente si legge lì.
PC05 invariante: -C solo sull'add o solo sul commit, -C in una variabile, -C scritti diversi fanno leggere
     tutto; un segreto nel file dell'add si trova.
PC06 un alias di add accanto a `git add f` fa leggere tutti i file nuovi.

Sulla base de04b3b (dev prima della modifica) sono rossi tutti tranne PC05.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

CASI = ["PC01", "PC02", "PC03", "PC04", "PC05", "PC06"]
DISCRIMINANTI = [c for c in CASI if c != "PC05"]
# Token finto composto a runtime: nessun segreto nel sorgente.
GH_FINTO = "gh" + "p_" + "A1b2C3d4" * 5
GIT_ENV = {"GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1", "GIT_AUTHOR_NAME": "t",
           "GIT_AUTHOR_EMAIL": "t@esempio.org", "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@esempio.org"}


def _git(cartella: Path, *argomenti: str) -> None:
    subprocess.run(["git", "-C", str(cartella), *argomenti], env=dict(os.environ, **GIT_ENV),
                   capture_output=True, text=True, timeout=60, check=True)


def _repo(cartella: Path, segreto_fuori: bool = True) -> Path:
    cartella.mkdir(parents=True)
    _git(cartella, "init", "-q")
    (cartella / "pulito.txt").write_text("niente di segreto\n", encoding="utf-8")
    if segreto_fuori:
        (cartella / "conf.py").write_text(f'TOKEN = "{GH_FINTO}"\n', encoding="utf-8")
    return cartella


def _esito(repo: Path, comando: str, cwd: Path) -> str:
    """segreto, parziale, silent, oppure l'inizio del motivo della conferma."""
    p = subprocess.run([sys.executable, "-B", str(repo / "hooks" / "commit-secret-gate.py")], text=True,
                       input=json.dumps({"tool_name": "Bash", "tool_input": {"command": comando}, "cwd": str(cwd)}),
                       capture_output=True, timeout=60, env=dict(os.environ, PYTHONUTF8="1", **GIT_ENV))
    righe = [r for r in p.stdout.splitlines() if r.startswith("{")]
    if not righe:
        return "silent"
    motivo = json.loads(righe[-1])["hookSpecificOutput"].get("permissionDecisionReason", "")
    if "Possibile secret" in motivo:
        return "segreto"
    return "parziale" if "ha letto" in motivo else motivo[:70]


def prova(repo: Path) -> list:
    rossi = []
    with tempfile.TemporaryDirectory() as d:
        radice = Path(d)
        fuori = radice / "fuori"
        fuori.mkdir()

        r = _repo(radice / "pc01").as_posix()
        e = _esito(repo, f"git -C {r} add pulito.txt && git -C {r} commit -m uno", fuori)
        if e != "silent":
            rossi.append(f"PC01 stesso -C, segreto fuori dal pathspec: atteso silent, ottenuto {e}")

        molti = radice / "pc02"
        molti.mkdir()
        _git(molti, "init", "-q")
        for i in range(120):
            (molti / f"n{i:03}.txt").write_text(f"riga {i}\n" + "x" * 199_000, encoding="utf-8")
        m = molti.as_posix()
        e = _esito(repo, f"git -C {m} add n000.txt && git -C {m} commit -m uno", fuori)
        if e != "silent":
            rossi.append(f"PC02 stesso -C oltre il tetto, add di un file solo: atteso silent, ottenuto {e}")

        _repo(radice / "pc03" / "sotto")
        e = _esito(repo, "git -C sotto add pulito.txt && git -C sotto commit -m uno", radice / "pc03")
        if e != "silent":
            rossi.append(f"PC03 stesso -C relativo: atteso silent, ottenuto {e}")

        a = _repo(radice / "pc04a", segreto_fuori=False)
        (a / "conf.py").write_text(f'TOKEN = "{GH_FINTO}"\n', encoding="utf-8")
        _git(a, "add", "conf.py")
        b = _repo(radice / "pc04b", segreto_fuori=False).as_posix()
        e = _esito(repo, f"git -C {b} status && git commit -m uno", a)
        if e != "segreto":
            rossi.append(f"PC04 dopo git -C altro, il commit corrente col segreto in stage: atteso segreto, ottenuto {e}")

        sbagli = []
        for nome, comando, cwd, atteso in (
                ("-C solo sull'add", "git -C {r} add pulito.txt && git commit -m uno", "repo", "segreto"),
                ("-C solo sul commit", "git add pulito.txt && git -C {r} commit -m uno", "repo", "segreto"),
                ("-C in una variabile", "D={r}; git -C $D add pulito.txt && git -C $D commit -m uno", "fuori",
                 "segreto"),
                ("-C scritti diversi", "git -C {r} add pulito.txt && git -C {r}/. commit -m uno", "fuori", "segreto"),
                ("segreto nel file dell'add", "git -C {r} add conf.py && git -C {r} commit -m uno", "fuori",
                 "segreto")):
            cartella = _repo(radice / f"pc05-{len(sbagli)}-{abs(hash(nome))}")
            e = _esito(repo, comando.format(r=cartella.as_posix()), cartella if cwd == "repo" else fuori)
            if e != atteso:
                sbagli.append(f"{nome}: atteso {atteso}, ottenuto {e}")
        if sbagli:
            rossi.append("PC05 " + "; ".join(sbagli))

        r6 = _repo(radice / "pc06")
        e = _esito(repo, "git -c alias.tutto=add tutto . && git add pulito.txt && git commit -m uno", r6)
        if e != "segreto":
            rossi.append(f"PC06 alias di add accanto a git add f: atteso segreto, ottenuto {e}")
    return sorted(rossi)


def main() -> int:
    for flusso in (sys.stdout, sys.stderr):
        if hasattr(flusso, "reconfigure"):
            flusso.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument("--baseline-ref")
    a = parser.parse_args()
    rossi = prova(Path(a.repo).resolve())
    if a.baseline_ref:
        codici = [r.split()[0] for r in rossi]
        assert codici == DISCRIMINANTI, f"baseline non discriminante: rossi {codici}, attesi {DISCRIMINANTI}"
        print(f"BASELINE_DISCRIMINANTE={','.join(codici)}")
        return 0
    for r in rossi:
        print("ROSSO", r)
    print(f"pathspec con git -C: {len(CASI) - len(rossi)}/{len(CASI)} casi verdi")
    return 1 if rossi else 0


if __name__ == "__main__":
    sys.exit(main())
