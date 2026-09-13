#!/usr/bin/env python3
"""H01, H07, H10: casi avvelenati dei finding HIGH della revisione del 13/9/2026.

Sulla base ee10fc6 ognuno dei tre finding deve fallire per conto suo.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path


def invoke(hook: Path, payload: dict, env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run([sys.executable, "-B", str(hook)], input=json.dumps(payload), text=True,
                          capture_output=True, env=env, timeout=10, check=False)


def outcome(result: subprocess.CompletedProcess[str]) -> str:
    if result.returncode == 2:
        return "block"
    if result.returncode:
        raise RuntimeError(f"hook rc={result.returncode}: {result.stderr.strip()[:200]}")
    if not result.stdout.strip():
        return "silent"
    return json.loads(result.stdout)["hookSpecificOutput"]["permissionDecision"]


def isolated_env(home: Path) -> dict[str, str]:
    return {"HOME": str(home), "USERPROFILE": str(home), "PATH": os.environ.get("PATH", ""),
            "SYSTEMROOT": os.environ.get("SYSTEMROOT", "")}


H01_CASI = [
    ("Write", "config-unlock-one", "ask"),
    ("Edit", "config-unlock-one", "ask"),
    ("Write", "claude-md-unlock-one", "ask"),
]

H07_CASI = {
    "graphql deleteRepository": ("gh api graphql -f query='mutation { deleteRepository(input: {repositoryId: \"R_x\"}) { clientMutationId } }'", "block"),
    "graphql altra mutazione": ("gh api graphql -f query='mutation { addStar(input: {starrableId: \"R_x\"}) { clientMutationId } }'", "ask"),
    "graphql da file": ("gh api graphql --input query.json", "ask"),
    "POST implicito con -f": ("gh api repos/o/r/issues -f title=prova", "ask"),
    "POST esplicito": ("gh api -X POST repos/o/r/forks", "ask"),
    "controllo: GET semplice": ("gh api repos/o/r", "silent"),
    "controllo: query GraphQL": ("gh api graphql -f query='query { viewer { login } }'", "silent"),
    "controllo: GET con campi": ("gh api -X GET search/issues -f q=prova", "silent"),
}


def test_h01(repo: Path) -> None:
    with tempfile.TemporaryDirectory(prefix="arturo-h01-") as raw:
        home = Path(raw) / "home"
        config = home / ".claude"
        config.mkdir(parents=True)
        env = isolated_env(home)
        hook = repo / "hooks" / "protect_claude_md.py"
        for tool, name, expected in H01_CASI:
            got = outcome(invoke(hook, {"tool_name": tool, "tool_input": {"file_path": str(config / name)}, "session_id": "one"}, env))
            assert got == expected, f"H01 {tool} {name}: atteso {expected}, ricevuto {got}"
        note = home / "progetto" / "note.md"
        got = outcome(invoke(hook, {"tool_name": "Write", "tool_input": {"file_path": str(note)}, "session_id": "one"}, env))
        assert got == "silent", f"H01 controllo file ordinario: atteso silent, ricevuto {got}"


def test_h07(repo: Path) -> None:
    with tempfile.TemporaryDirectory(prefix="arturo-h07-") as raw:
        env = isolated_env(Path(raw))
        hook = repo / "hooks" / "gh-destructive-guard.py"
        for label, (command, expected) in H07_CASI.items():
            got = outcome(invoke(hook, {"tool_name": "Bash", "tool_input": {"command": command}}, env))
            assert got == expected, f"H07 {label}: atteso {expected}, ricevuto {got}"


def test_h10(repo: Path) -> None:
    fine = (repo / "commands" / "fine.md").read_text(encoding="utf-8")
    assert 'git add "$HANDOFF_FILE"' not in fine, "H10 /fine committa l'handoff nel repository del progetto"
    assert 'HANDOFF_FILE="$HDIR/' in fine, "H10 l'handoff non nasce nello store privato"
    staging = fine.find("for p in CLAUDE.md data/handoffs")
    check = fine.find('"$VIS" = "PRIVATE"')
    assert check != -1 and staging > check, "H10 gli handoff si sincronizzano senza verificare che il remote sia privato"


TESTS = {"H01": test_h01, "H07": test_h07, "H10": test_h10}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--baseline-ref")
    args = parser.parse_args()
    repo = args.repo.resolve()
    if args.baseline_ref:
        failed = []
        for name, test in TESTS.items():
            try:
                test(repo)
            except AssertionError:
                failed.append(name)
        assert failed == list(TESTS), f"baseline non discriminante: falliscono solo {failed} su {list(TESTS)}"
        print(f"BASELINE_DISCRIMINANTE={','.join(failed)}")
        return 0
    for test in TESTS.values():
        test(repo)
    print(f"PASS H01,H07,H10 casi={len(H01_CASI) + len(H07_CASI) + 1}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
