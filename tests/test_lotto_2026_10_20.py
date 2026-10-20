#!/usr/bin/env python3
"""LT01-LT02: lotto del 20/10/2026 sui task aperti di Arturo.

LT01 l'audit vede lo script della barra anche dentro `... statusline.js; echo ...` (#3632): se
     manca, lo dice invece di saltare il controllo.
LT02 il README dice cosa succede senza node e cita la riga NODE dell'avvio (#3632).

Sulla base 910ac0b ogni controllo deve fallire con un AssertionError che comincia con il suo codice.
"""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

BASH = shutil.which("bash") or "bash"


def casa(repo: Path, radice: Path) -> Path:
    home = radice / "home"
    shutil.copytree(repo, home / ".claude", ignore=shutil.ignore_patterns(".git", "__pycache__"))
    return home


def env_di(home: Path, **extra: str) -> dict:
    env = {"HOME": str(home), "USERPROFILE": str(home), "PATH": os.environ.get("PATH", ""),
           "PYTHONDONTWRITEBYTECODE": "1", "GIT_CONFIG_GLOBAL": "/dev/null", "ARTURO_TELEMETRIA": "0"}
    env.update(extra)
    return env


def test_lt01(repo: Path) -> None:
    with tempfile.TemporaryDirectory() as d:
        home = casa(repo, Path(d))
        (home / ".claude" / "hooks" / "statusline.js").unlink()
        r = subprocess.run([BASH, str(home / ".claude" / "skills" / "system-audit" / "audit.sh")],
                           capture_output=True, text=True, timeout=180, env=env_di(home), check=False)
        uscita = r.stdout + r.stderr
        assert "hook diretto mancante" in uscita and "statusline.js" in uscita, \
            "LT01 l'audit non vede che manca statusline.js quando la barra è `... statusline.js; echo ...`"


def test_lt02(repo: Path) -> None:
    readme = (repo / "README.md").read_text(encoding="utf-8")
    assert "riga `NODE`" in readme and "manca node" in readme, \
        "LT02 il README non dice cosa succede senza node né la riga NODE dell'avvio"


TESTS = {"LT01": test_lt01, "LT02": test_lt02}


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
    raise SystemExit(main())
