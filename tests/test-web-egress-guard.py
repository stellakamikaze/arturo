#!/usr/bin/env python3
"""S08-W: l'host decide il destinatario, non userinfo, porta o sottostringa."""
from __future__ import annotations

import argparse
import io
import json
import shutil
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path


PAYLOAD = "x" * 320
CASES = {
    "localhost.example.invalid": f"https://localhost.example.invalid/?d={PAYLOAD}",
    "userinfo-esterno": f"https://localhost@outside.example.invalid/?d={PAYLOAD}",
    "suffisso-falso": f"https://node.ts.net.example.invalid/?d={PAYLOAD}",
    "ipv4-falso": f"https://127.0.0.1.example.invalid/?d={PAYLOAD}",
    "case-punto": f"https://OUTSIDE.EXAMPLE.INVALID./?d={PAYLOAD}",
    "interno-vero": f"https://localhost/?d={PAYLOAD}",
    "esterno-corto": "https://outside.example.invalid/?d=breve",
}


def decision(repo: Path, url: str) -> str:
    payload = json.dumps({"tool_input": {"url": url}})
    result = subprocess.run(
        [sys.executable, "-B", str(repo / "hooks" / "web-egress-guard.py")],
        input=payload,
        text=True,
        capture_output=True,
        timeout=10,
        check=False,
    )
    if result.returncode:
        raise AssertionError(f"guardia rc={result.returncode}: {result.stderr}")
    if not result.stdout.strip():
        return "silent"
    try:
        return json.loads(result.stdout)["hookSpecificOutput"]["permissionDecision"]
    except (json.JSONDecodeError, KeyError, TypeError) as exc:
        raise AssertionError(f"stdout non decisionale: {result.stdout!r}") from exc


def materialize_baseline(repo: Path, ref: str) -> tuple[tempfile.TemporaryDirectory[str], Path]:
    temp = tempfile.TemporaryDirectory(prefix="arturo-baseline-")
    archive = subprocess.run(
        ["git", "-C", str(repo), "archive", ref],
        capture_output=True,
        timeout=20,
        check=True,
    ).stdout
    root = Path(temp.name)
    with tarfile.open(fileobj=io.BytesIO(archive)) as bundle:
        bundle.extractall(root, filter="data")
    return temp, root


def assert_candidate(repo: Path) -> None:
    for name in ("localhost.example.invalid", "userinfo-esterno", "suffisso-falso", "ipv4-falso", "case-punto"):
        got = decision(repo, CASES[name])
        assert got == "ask", f"{name}: atteso ask, ricevuto {got}"
    for name in ("interno-vero", "esterno-corto"):
        got = decision(repo, CASES[name])
        assert got == "silent", f"{name}: atteso silent, ricevuto {got}"
    settings = json.loads((repo / "settings.json").read_text(encoding="utf-8"))
    matchers = [item["matcher"] for item in settings["hooks"]["PreToolUse"]]
    assert any("mcp__playwright-ff__browser_navigate" in matcher for matcher in matchers), "matcher Firefox assente"


def assert_baseline(repo: Path, ref: str) -> None:
    temp, baseline = materialize_baseline(repo, ref)
    try:
        observed = {name: decision(baseline, CASES[name]) for name in (
            "localhost.example.invalid", "userinfo-esterno", "suffisso-falso"
        )}
    finally:
        temp.cleanup()
    wrong = [name for name, got in observed.items() if got != "ask"]
    assert wrong, f"baseline non discriminante: {observed}"
    print("BASELINE_DISCRIMINANTI=" + ",".join(wrong))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--baseline-ref")
    args = parser.parse_args()
    if args.baseline_ref:
        assert_baseline(args.repo.resolve(), args.baseline_ref)
    else:
        assert_candidate(args.repo.resolve())
        print(f"PASS S08-W casi={len(CASES)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
