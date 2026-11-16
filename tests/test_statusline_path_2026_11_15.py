#!/usr/bin/env python3
"""SP01: la barra trova node anche col PATH minimo di una sessione aperta via ssh (15/11/2026).

Volta apre le sessioni di un'altra macchina con `ssh -t <macchina> claude attach <id>`. Il client
`claude attach` nasce dalla shell di ssh, che non legge il file di avvio della persona: il PATH è
/usr/bin:/bin:/usr/sbin:/sbin, senza Homebrew e senza ~/.local/bin. Il comando della barra in
settings.json cercava node solo nel PATH, quindi in quelle sessioni la riga spariva e restava l'avviso
"manca node" anche con node installato.

SP01 con node solo in ~/.local/bin e PATH minimo, il comando di settings.json stampa la riga della
     barra e non l'avviso "manca node".
SP02 lo stesso per l'avviso sul contesto (hook PostToolUse di context-monitor.js): col PATH minimo di una
     sessione di `claude --bg` o di ssh il comando partiva con `node` nudo e usciva 127 (16/11/2026).

Sulla base 8f62532 (il dev prima di questo passo) SP01 è rosso: il comando non allarga il PATH.
Sulla base fe199ff SP02 è rosso: l'hook dell'avviso sul contesto non allarga il PATH.
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


def comando_contesto(repo: Path) -> str:
    impostazioni = json.loads((repo / "settings.json").read_text(encoding="utf-8"))
    comandi = [h["command"] for m in impostazioni["hooks"]["PostToolUse"] for h in m["hooks"]
               if "context-monitor.js" in h["command"]]
    assert len(comandi) == 1, f"SP02 atteso un solo hook di context-monitor.js, trovati {len(comandi)}"
    return comandi[0]


def test_sp02(repo: Path) -> None:
    node = shutil.which("node")
    assert node, "SP02 serve node su questa macchina per la prova"
    with tempfile.TemporaryDirectory() as tmp:
        home = Path(tmp)
        (home / ".claude" / "hooks").mkdir(parents=True)
        shutil.copy(repo / "hooks" / "context-monitor.js", home / ".claude" / "hooks" / "context-monitor.js")
        (home / ".local" / "bin").mkdir(parents=True)
        os.symlink(os.path.realpath(node), home / ".local" / "bin" / "node")
        dati = json.dumps({"session_id": "sp02", "tool_name": "Bash", "cwd": tmp})
        r = subprocess.run(["/bin/sh", "-c", comando_contesto(repo)], input=dati, capture_output=True, text=True,
                           timeout=30, cwd=tmp,
                           env={"HOME": str(home), "USERPROFILE": str(home), "PATH": "/usr/bin:/bin:/usr/sbin:/sbin",
                                "TMPDIR": tmp})
        assert r.returncode != 127 and "not found" not in r.stderr, \
            f"SP02 col PATH minimo l'avviso sul contesto non trova node: rc={r.returncode} err={r.stderr.strip()[:160]!r}"


TESTS = {"SP01": test_sp01, "SP02": test_sp02}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--repo", default=str(Path(__file__).resolve().parents[1]))
    ap.add_argument("--baseline-ref")
    args = ap.parse_args()
    if os.name == "nt":
        print("SALTO SP01 SP02 la shell di ssh col PATH minimo è di Mac e Linux")
        return 0
    rossi = []
    for nome, test in TESTS.items():
        try:
            test(Path(args.repo))
        except AssertionError as e:
            rossi.append((nome, str(e)))
    if args.baseline_ref:
        if rossi and all(m.startswith(n) for n, m in rossi):
            print("BASELINE_DISCRIMINANTE=" + ",".join(n for n, _ in rossi))
            return 0
        print("baseline non discriminante: " + ("tutti verdi sulla base" if not rossi else str(rossi)))
        return 1
    if rossi:
        for _, m in rossi:
            print(f"ROSSO {m}")
        return 1
    print(f"PASS {','.join(TESTS)} controlli={len(TESTS)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
