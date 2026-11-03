#!/usr/bin/env python3
"""SZ01-SZ03: le segnalazioni n. 45 e n. 46 di Filippo del 3/11/2026.

SZ01 l'avvio scrive in $CLAUDE_ENV_FILE, una volta sola anche dopo due avvii, la riga che dà a zsh
     nonomatch, noequals e shwordsplit; in bash la stessa riga esce 0 e non ferma il comando dopo.
     Claude Code esegue quel file prima di ogni comando Bash (provato su 2.1.304 con claude -p).
SZ02 nessun mod cambia il comando: in modalità auto un comando cambiato dopo la revisione del
     classificatore va rilanciato identico (n. 46). Dal 3/11/2026 il mod riscrivi-bash è uscito, e
     bash-dispatcher.sh legge lo stesso marcatore dell'avvio per non bloccare un glob in un'opzione.
SZ03 /inizio dice perché la copia separata parte dall'HEAD locale (worktree.baseRef: "head" nei
     settings) e come accorgersene e rimediare se non succede (n. 45).

Sulla base 9c6a0e6 ogni controllo deve fallire con un AssertionError che comincia con il suo codice.
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

MARCATORE = "arturo-zsh-come-bash"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.is_file() else ""


def avvia(repo: Path, d: Path, ambiente: Path) -> None:
    home = d / "home"
    if not (home / ".claude").exists():
        shutil.copytree(repo, home / ".claude", ignore=shutil.ignore_patterns(".git", "__pycache__", "cache"))
    env = {"HOME": str(home), "USERPROFILE": str(home), "PATH": "/usr/bin:/bin:/usr/sbin:/sbin",
           "CLAUDE_ENV_FILE": str(ambiente), "ARTURO_BANCHI_AVVIO": "0", "ARTURO_TELEMETRIA": "0",
           "GIT_CONFIG_GLOBAL": "/dev/null", "TMPDIR": tempfile.gettempdir()}
    subprocess.run([shutil.which("bash") or "bash", str(home / ".claude" / "hooks" / "session-start.sh")],
                   input="{}", text=True, capture_output=True, cwd=str(d), env=env, timeout=60)


def test_sz01(repo: Path) -> None:
    with tempfile.TemporaryDirectory() as t:
        d = Path(t)
        ambiente = d / "ambiente.sh"
        ambiente.write_text("", encoding="utf-8")
        avvia(repo, d, ambiente)
        avvia(repo, d, ambiente)
        righe = [r for r in read(ambiente).splitlines() if MARCATORE in r]
        assert len(righe) == 1, f"SZ01 l'avvio non scrive una volta sola la riga di zsh: {righe}"
        bash = shutil.which("bash") or "bash"
        r = subprocess.run([bash, "-c", f'source "{ambiente}" && echo dopo'], text=True, capture_output=True, timeout=30)
        assert r.returncode == 0 and r.stdout.strip().endswith("dopo"), \
            f"SZ01 in bash la riga ferma il comando dopo: {r.returncode} {r.stdout!r} {r.stderr!r}"
        zsh = shutil.which("zsh")
        if zsh is None:  # Windows e Linux senza zsh: la riga serve solo dove c'è zsh
            return
        r = subprocess.run([zsh, "-f", "-c", f'source "{ambiente}" && setopt'], text=True, capture_output=True, timeout=30)
        opzioni = set(r.stdout.split())
        assert {"nonomatch", "noequals", "shwordsplit"} <= opzioni, f"SZ01 in zsh mancano opzioni: {sorted(opzioni)}"


def test_sz02(repo: Path) -> None:
    assert not (repo / "skills" / "riscrivi-bash").exists(), "SZ02 il mod riscrivi-bash c'è ancora e cambia il comando"
    assert MARCATORE in read(repo / "hooks" / "bash-dispatcher.sh"), \
        "SZ02 bash-dispatcher.sh non legge il marcatore dell'avvio"
    assert MARCATORE in read(repo / "hooks" / "session-start.sh"), "SZ02 l'avvio non scrive il marcatore"


def test_sz03(repo: Path) -> None:
    inizio = " ".join(read(repo / "commands" / "inizio.md").split())
    voce = inizio[inizio.find("**Worktree"):][:1600]
    for pezzo in ('worktree.baseRef: "head"', "git rev-parse HEAD", "git worktree add -b", "ExitWorktree", "`path`"):
        assert pezzo in voce, f"SZ03 la voce del worktree di /inizio non dice {pezzo!r}"
    settings = json.loads(read(repo / "settings.json") or "{}")
    assert settings.get("worktree", {}).get("baseRef") == "head", "SZ03 settings.json non ha worktree.baseRef head"


TESTS = {"SZ01": test_sz01, "SZ02": test_sz02, "SZ03": test_sz03}


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
            except Exception as e:  # noqa: BLE001
                altro.append(f"{nome}: {type(e).__name__} {e}")
        assert not altro and len(rossi) == len(TESTS), \
            "baseline non discriminante: ogni controllo deve fallire col suo codice.\n" + "\n".join(altro + rossi)
        print(f"BASELINE_DISCRIMINANTE={','.join(r.split(':')[0] for r in rossi)}")
        return 0
    for test in TESTS.values():
        test(repo)
    print(f"PASS {','.join(TESTS)} controlli={len(TESTS)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
