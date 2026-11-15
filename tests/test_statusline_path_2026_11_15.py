#!/usr/bin/env python3
"""SP01: la barra trova node anche col PATH minimo di una sessione aperta via ssh (15/11/2026).

Volta apre le sessioni di un'altra macchina con `ssh -t <macchina> claude attach <id>`. Il client
`claude attach` nasce dalla shell di ssh, che non legge il file di avvio della persona: il PATH è
/usr/bin:/bin:/usr/sbin:/sbin, senza Homebrew e senza ~/.local/bin. Il comando della barra in
settings.json cercava node solo nel PATH, quindi in quelle sessioni la riga spariva e restava l'avviso
"manca node" anche con node installato.

SP01 con node solo in ~/.local/bin e PATH minimo, il comando di settings.json stampa la riga della
     barra e non l'avviso "manca node".

Sulla base 8f62532 (il dev prima di questo passo) SP01 è rosso: il comando non allarga il PATH.
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


def comando(repo: Path) -> str:
    return json.loads((repo / "settings.json").read_text(encoding="utf-8"))["statusLine"]["command"]


def test_sp01(repo: Path) -> None:
    node = shutil.which("node")
    assert node, "SP01 serve node su questa macchina per la prova"
    with tempfile.TemporaryDirectory() as tmp:
        home = Path(tmp)
        (home / ".claude" / "hooks").mkdir(parents=True)
        shutil.copy(repo / "hooks" / "statusline.js", home / ".claude" / "hooks" / "statusline.js")
        (home / ".local" / "bin").mkdir(parents=True)
        os.symlink(os.path.realpath(node), home / ".local" / "bin" / "node")
        dati = json.dumps({"model": {"display_name": "Opus 5.5"}, "workspace": {"current_dir": tmp},
                           "context_window": {"remaining_percentage": 78}})
        r = subprocess.run(["/bin/sh", "-c", comando(repo)], input=dati, capture_output=True, text=True,
                           timeout=30, cwd=tmp,
                           env={"HOME": str(home), "USERPROFILE": str(home), "PATH": "/usr/bin:/bin:/usr/sbin:/sbin"})
        assert "manca node" not in r.stdout and "│" in r.stdout, \
            f"SP01 col PATH di ssh la barra non trova node in ~/.local/bin: {r.stdout.strip()[:160]!r}"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--repo", default=str(Path(__file__).resolve().parents[1]))
    ap.add_argument("--baseline-ref")
    args = ap.parse_args()
    if os.name == "nt":
        print("SALTO SP01 la shell di ssh col PATH minimo è di Mac e Linux")
        return 0
    try:
        test_sp01(Path(args.repo))
    except AssertionError as e:
        if args.baseline_ref:
            print("BASELINE_DISCRIMINANTE=SP01")
            return 0
        print(f"ROSSO {e}")
        return 1
    if args.baseline_ref:
        print("baseline non discriminante: SP01 verde sulla base")
        return 1
    print("PASS SP01 controlli=1")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
