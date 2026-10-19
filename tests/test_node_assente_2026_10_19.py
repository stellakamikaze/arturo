#!/usr/bin/env python3
"""NA01-NA02: Arturo senza node (19/10/2026).

Claude Code si installa anche senza node. La barra in basso (hooks/statusline.js) e l'avviso sul
contesto (hooks/context-monitor.js) girano con node: su un Mac appena installato restavano spenti
in silenzio, e la persona non vedeva né contesto né quota.

NA01 senza node il comando della barra in settings.json esce con 0 e scrive una riga che nomina
     node. Con node la riga è quella di statusline.js.
NA02 senza node l'avvio (hooks/session-start.sh) scrive la riga NODE.

Sulla base dbaefa1 ogni controllo deve fallire con un AssertionError che comincia con il suo codice.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

ENTRATA = json.dumps({
    "model": {"display_name": "Opus 5.5"},
    "workspace": {"current_dir": "/tmp"},
    "session_id": "na",
    "context_window": {"remaining_percentage": 90},
    "rate_limits": {"five_hour": {"used_percentage": 15}, "seven_day": {"used_percentage": 16}},
})


def casa_finta(repo: Path, radice: Path) -> Path:
    """Una HOME con ~/.claude che punta al repository: il comando usa ~/.claude/hooks/…"""
    home = radice / "home"
    home.mkdir()
    (home / ".claude").symlink_to(repo, target_is_directory=True)
    return home


def senza_node(radice: Path) -> str:
    """Un PATH con i soli comandi di sistema che servono, e senza node."""
    bin_ = radice / "bin"
    bin_.mkdir()
    for nome in ("sh", "bash", "cat", "sed", "find", "git", "hostname", "scutil", "date", "mkdir",
                 "grep", "head", "tr", "basename", "dirname", "python3", "uname", "printf", "rm"):
        vero = shutil.which(nome)
        if vero:
            (bin_ / nome).symlink_to(vero)
    assert shutil.which("node", path=str(bin_)) is None
    return str(bin_)


def comando_barra(repo: Path) -> str:
    return json.loads((repo / "settings.json").read_text(encoding="utf-8"))["statusLine"]["command"]


def test_na01(repo: Path) -> None:
    with tempfile.TemporaryDirectory() as t:
        radice = Path(t)
        home = casa_finta(repo, radice)
        env = {"HOME": str(home), "USERPROFILE": str(home), "PATH": senza_node(radice)}
        p = subprocess.run(["/bin/sh", "-c", comando_barra(repo)], input=ENTRATA, env=env,
                           capture_output=True, text=True, timeout=20)
        assert p.returncode == 0 and "node" in p.stdout, \
            f"NA01 senza node la barra non dice cosa manca: rc={p.returncode} out={p.stdout!r} err={p.stderr[-200:]!r}"
        node = shutil.which("node")
        if node:
            env["PATH"] = f"{Path(node).parent}:{env['PATH']}"
            p = subprocess.run(["/bin/sh", "-c", comando_barra(repo)], input=ENTRATA, env=env,
                               capture_output=True, text=True, timeout=20)
            assert p.returncode == 0 and "quota 5h 15%" in p.stdout and "manca node" not in p.stdout, \
                f"NA01 con node la barra non è quella di statusline.js: {p.stdout!r}"


def test_na02(repo: Path) -> None:
    with tempfile.TemporaryDirectory() as t:
        radice = Path(t)
        home = casa_finta(repo, radice)
        env = {"HOME": str(home), "USERPROFILE": str(home), "PATH": senza_node(radice), "ARTURO_BANCHI_AVVIO": "0",
               "ARTURO_TELEMETRIA": "0", "CLAUDE_PROJECT_DIR": str(radice)}
        p = subprocess.run(["bash", str(repo / "hooks" / "session-start.sh")], input="{}", env=env,
                           cwd=radice, capture_output=True, text=True, timeout=60)
        assert any(r.startswith("NODE: manca node") for r in p.stdout.splitlines()), \
            f"NA02 senza node l'avvio non lo dice: rc={p.returncode} out={p.stdout[-400:]!r}"


TESTS = {"NA01": test_na01, "NA02": test_na02}


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
