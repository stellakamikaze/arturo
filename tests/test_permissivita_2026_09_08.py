#!/usr/bin/env python3
"""I01/I02: unlock separati, fail-closed e letture SSH protette."""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path


def invoke(path: Path, payload: dict, env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run([sys.executable, "-B", str(path)], input=json.dumps(payload), text=True, capture_output=True, env=env, timeout=10, check=False)


def decision(stdout: str) -> str:
    return json.loads(stdout)["hookSpecificOutput"]["permissionDecision"]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--baseline-ref")
    args = parser.parse_args()
    if args.baseline_ref:
        probe = subprocess.run([sys.executable, "-B", __file__, "--repo", str(args.repo)], capture_output=True, text=True, timeout=30, check=False)
        assert probe.returncode == 0, "invarianti non preservati sulla baseline"
        print("BASELINE_INVARIANTE=I01,I02")
        return 0
    with tempfile.TemporaryDirectory(prefix="arturo-invarianti-") as raw:
        home = Path(raw) / "home"; config = home / ".claude"; hooks = config / "hooks"
        hooks.mkdir(parents=True)
        env = {"HOME": str(home), "USERPROFILE": str(home), "PATH": os.environ.get("PATH", "")}
        protected = invoke(args.repo / "hooks" / "protect_claude_md.py", {"tool_name": "Write", "tool_input": {"file_path": str(config / "settings.json")}, "session_id": "one"}, env)
        assert protected.returncode == 0 and decision(protected.stdout) == "deny", "I01 settings senza unlock"
        wrong = config / "config-unlock-other"; wrong.touch()
        still = invoke(args.repo / "hooks" / "protect_claude_md.py", {"tool_name": "Write", "tool_input": {"file_path": str(hooks / "x.py")}, "session_id": "one"}, env)
        assert still.returncode == 0 and decision(still.stdout) == "deny", "I01 unlock altra sessione"
        malformed = subprocess.run([sys.executable, "-B", str(args.repo / "hooks" / "protect_claude_md.py")], input="{", text=True, capture_output=True, env=env, timeout=10, check=False)
        assert malformed.returncode == 2, "I02 parsing deve fail-closed"
        secret = invoke(args.repo / "hooks" / "block-dangerous.py", {"tool_name": "Bash", "tool_input": {"command": "cat ~/.ssh/id_ed25519"}, "cwd": str(home)}, env)
        assert secret.returncode == 0 and decision(secret.stdout) == "ask", "I02 lettura SSH"
    print("PASS I01,I02")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
