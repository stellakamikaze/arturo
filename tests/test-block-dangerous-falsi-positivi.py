#!/usr/bin/env python3
"""Regressioni di falsi positivi della guardia Bash."""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


def result(repo: Path, command: str) -> int:
    return subprocess.run(
        [sys.executable, "-B", str(repo / "hooks" / "block-dangerous.py")],
        input=json.dumps({"tool_name": "Bash", "tool_input": {"command": command}, "cwd": "/tmp"}),
        text=True, capture_output=True, timeout=10, check=False,
    ).returncode


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--baseline-ref")
    args = parser.parse_args()
    if args.baseline_ref:
        probe = subprocess.run([sys.executable, "-B", __file__, "--repo", str(args.repo)], capture_output=True, text=True, timeout=20, check=False)
        assert probe.returncode != 0, "baseline non discriminante sui falsi positivi"
        print("BASELINE_DISCRIMINANTE=falsi-positivi")
        return 0
    cases = {
        "help": ("bw export --help", 0),
        "prosa": ("printf '%s\\n' 'bw export'", 0),
        "export": ("bw --raw export --format json", 2),
        "prosa-seguita": ("printf x; bw export", 2),
    }
    for name, (command, expected) in cases.items():
        got = result(args.repo.resolve(), command)
        assert got == expected, f"{name}: atteso rc={expected}, ricevuto rc={got}"
    print(f"PASS falsi-positivi casi={len(cases)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
