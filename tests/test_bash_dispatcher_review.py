#!/usr/bin/env python3
"""S01, S02, S05, S06: dispatcher in HOME completamente isolata."""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


BASH = shutil.which("bash")


def copy_home(repo: Path) -> tuple[tempfile.TemporaryDirectory[str], Path]:
    temp = tempfile.TemporaryDirectory(prefix="arturo-dispatcher-")
    home = Path(temp.name) / "home"
    shutil.copytree(repo, home / ".claude", ignore=shutil.ignore_patterns(".git", "__pycache__"))
    return temp, home


def run(home: Path, command: str) -> subprocess.CompletedProcess[str]:
    env = {
        "HOME": str(home), "USERPROFILE": str(home), "PATH": os.environ.get("PATH", ""),
        "PYTHONDONTWRITEBYTECODE": "1", "COMMS_REDUCED": "avvelenata",
    }
    return subprocess.run(
        [BASH, str(home / ".claude" / "hooks" / "bash-dispatcher.sh")],
        input=json.dumps({"tool_name": "Bash", "tool_input": {"command": command}, "cwd": str(home)}),
        text=True, capture_output=True, env=env, timeout=10, check=False,
    )


def permission(result: subprocess.CompletedProcess[str]) -> str:
    if result.returncode == 2:
        return "block"
    if result.returncode:
        raise AssertionError(f"dispatcher rc={result.returncode}: stdout={result.stdout!r} stderr={result.stderr!r}")
    if not result.stdout.strip():
        return "silent"
    try:
        return json.loads(result.stdout)["hookSpecificOutput"]["permissionDecision"]
    except (json.JSONDecodeError, KeyError, TypeError) as exc:
        raise AssertionError(f"stdout non decisionale: {result.stdout!r}") from exc


def stub(home: Path, body: str) -> None:
    path = home / ".claude" / "hooks" / "commit-secret-gate.py"
    path.write_text("#!/usr/bin/env python3\n" + body, encoding="utf-8")


def test_s01(repo: Path) -> None:
    for label, body, expected in (
        ("crash", "import sys; sys.exit(1)\n", "ask"),
        ("block", "import sys; sys.exit(2)\n", "block"),
        ("spurio", "print('non-json')\n", "ask"),
        ("silent", "pass\n", "silent"),
    ):
        temp, home = copy_home(repo)
        try:
            stub(home, body)
            got = permission(run(home, "git commit -m test"))
            assert got == expected, f"S01 {label}: atteso {expected}, ricevuto {got}"
        finally:
            temp.cleanup()


def test_routes(repo: Path) -> None:
    temp, home = copy_home(repo)
    try:
        (home / ".claude" / "hooks" / "block-dangerous.py").write_text(
            "import json; print(json.dumps({'hookSpecificOutput': {'permissionDecision': 'ask'}}))\n", encoding="utf-8"
        )
        assert permission(run(home, "git log --output=destino")) == "ask", "S02 --output deve raggiungere una guardia"
    finally:
        temp.cleanup()
    temp, home = copy_home(repo)
    try:
        cases = {
            "gws-send": ("gws gmail users messages send --json '{}'", "block"),
            "msmtp": ("printf x | msmtp outside@example.invalid", "block"),
            "draft": ("gws gmail users drafts create --json '{}'", "silent"),
        }
        for label, (command, expected) in cases.items():
            got = permission(run(home, command))
            assert got == expected, f"{label}: atteso {expected}, ricevuto {got}"
    finally:
        temp.cleanup()


def test_reduction(repo: Path) -> None:
    temp, home = copy_home(repo)
    try:
        inert = "cat <<'EOF'\nmailx -s testo\nEOF"
        executable = "sh <<'EOF'\nmailx -s testo\nEOF"
        followed = "cat <<'EOF'\ntesto\nEOF\n; mailx -s testo"
        assert permission(run(home, inert)) == "silent", "S06 heredoc cat deve restare inerte"
        assert permission(run(home, executable)) == "block", "S06 heredoc shell deve restare analizzato"
        assert permission(run(home, followed)) == "block", "S06 comando successivo deve restare analizzato"
        # Casi avvelenati: quello che segue il delimitatore SULLA STESSA RIGA viene eseguito.
        same_line = {
            "pipe verso shell": "cat <<'EOF' | sh\nmailx -s testo\nEOF",
            "redirect su settings": "cat <<'EOF' > ~/.claude/settings.json\n{}\nEOF",
            "comando concatenato": "cat <<'EOF' && mailx -s testo\ntesto\nEOF",
        }
        for label, command in same_line.items():
            got = permission(run(home, command))
            assert got != "silent", f"S06 {label}: la riga del delimitatore deve restare analizzata, ricevuto {got}"
    finally:
        temp.cleanup()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--baseline-ref")
    args = parser.parse_args()
    if args.baseline_ref:
        probe = subprocess.run([sys.executable, "-B", __file__, "--repo", str(args.repo)], capture_output=True, text=True, timeout=60, check=False)
        assert probe.returncode != 0, "baseline non discriminante su dispatcher"
        print("BASELINE_DISCRIMINANTE=S01,S02,S05,S06")
        return 0
    repo = args.repo.resolve()
    test_s01(repo)
    test_routes(repo)
    test_reduction(repo)
    print("PASS S01,S02,S05,S06")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
