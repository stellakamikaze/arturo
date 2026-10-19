#!/usr/bin/env python3
"""TV01-TV02: la telemetria manda il rilascio di Arturo installato, non i commit della persona (19/10/2026, #3613).

Il riepilogo del 19/10 mostrava versioni come «v2026-10-17-94-g03ee13d»: il git describe del repository
privato di sync, con un hash che in Arturo non esiste. Non si capiva chi era sull'ultimo rilascio.

TV01 con tre commit della persona sopra il tag v2026-10-17, la versione è «v2026-10-17».
TV02 un tag della persona («backup/prima») sopra il tag di Arturo non cambia la versione.

Sulla base 0c12a5b ogni controllo deve fallire con un AssertionError che comincia con il suo codice.
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
import tempfile
from pathlib import Path

LEGGI = ("import importlib.util, sys\n"
         "spec = importlib.util.spec_from_file_location('telemetria', sys.argv[1])\n"
         "t = importlib.util.module_from_spec(spec)\n"
         "spec.loader.exec_module(t)\n"
         "print(t.versione())\n")


def git(cartella: Path, *argomenti: str) -> None:
    subprocess.run(["git", "-C", str(cartella), *argomenti], check=True, capture_output=True)


def copia_con_commit(home: Path, commit_dopo: int, tag_persona: str = "") -> None:
    c = home / ".claude"
    c.mkdir(parents=True)
    git(c, "init", "-q")
    git(c, "config", "user.email", "banco@example.invalid")
    git(c, "config", "user.name", "banco")
    git(c, "commit", "-q", "--allow-empty", "-m", "rilascio")
    git(c, "tag", "v2026-10-17")
    for i in range(commit_dopo):
        git(c, "commit", "-q", "--allow-empty", "-m", f"commit della persona {i}")
    if tag_persona:
        git(c, "tag", tag_persona)


def versione(repo: Path, home: Path) -> str:
    env = dict(os.environ, HOME=str(home), USERPROFILE=str(home), ARTURO_TELEMETRIA="0")
    p = subprocess.run([sys.executable, "-B", "-c", LEGGI, str(repo / "bin" / "telemetria.py")],
                       capture_output=True, text=True, env=env, encoding="utf-8")
    return p.stdout.strip().splitlines()[-1] if p.stdout.strip() else f"errore: {p.stderr.strip()[-200:]}"


def test_tv01(repo: Path) -> None:
    with tempfile.TemporaryDirectory() as td:
        home = Path(os.path.realpath(td))
        copia_con_commit(home, 3)
        v = versione(repo, home)
        assert v == "v2026-10-17", f"TV01 con commit della persona la versione è {v!r}, non il rilascio v2026-10-17"


def test_tv02(repo: Path) -> None:
    with tempfile.TemporaryDirectory() as td:
        home = Path(os.path.realpath(td))
        copia_con_commit(home, 1, "backup/prima")
        v = versione(repo, home)
        assert v == "v2026-10-17", f"TV02 con un tag della persona la versione è {v!r}, non il rilascio v2026-10-17"


TESTS = {"TV01": test_tv01, "TV02": test_tv02}


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
        assert not altro and len(rossi) == len(TESTS), \
            "baseline non discriminante: ogni controllo deve fallire col suo codice.\n" + "\n".join(altro + rossi)
        print(f"BASELINE_DISCRIMINANTE={','.join(r.split(':')[0] for r in rossi)}")
        return 0
    for test in TESTS.values():
        test(repo)
    print(f"PASS {','.join(TESTS)} controlli={len(TESTS)}")
    return 0


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    raise SystemExit(main())
