#!/usr/bin/env python3
"""Finding MEDIUM della revisione del 13/9/2026: casi avvelenati e contratti.

M04 e M09 non si applicano piu' (quality-check.sh e /rebase potati).
Sulla base ee10fc6 ogni finding testato deve fallire per conto suo.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Callable

BASH = shutil.which("bash")


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def copy_home(repo: Path, tmp: str) -> Path:
    home = Path(tmp) / "home"
    shutil.copytree(repo, home / ".claude", ignore=shutil.ignore_patterns(".git", "__pycache__"))
    return home


def env_for(home: Path) -> dict[str, str]:
    return {"HOME": str(home), "USERPROFILE": str(home), "PATH": os.environ.get("PATH", ""),
            "SYSTEMROOT": os.environ.get("SYSTEMROOT", ""), "PYTHONDONTWRITEBYTECODE": "1"}


def dispatcher(home: Path, command: str) -> str:
    result = subprocess.run(
        [BASH, str(home / ".claude" / "hooks" / "bash-dispatcher.sh")],
        input=json.dumps({"tool_name": "Bash", "tool_input": {"command": command}, "cwd": str(home)}),
        text=True, capture_output=True, env=env_for(home), timeout=30, check=False,
    )
    if result.returncode == 2:
        return "block"
    if result.returncode:
        raise RuntimeError(f"dispatcher rc={result.returncode}: {result.stderr.strip()[:200]}")
    out = result.stdout.strip()
    return "silent" if not out else json.loads(out)["hookSpecificOutput"]["permissionDecision"]


def edit_settings(home: Path, change: Callable[[dict], None]) -> None:
    path = home / ".claude" / "settings.json"
    data = json.loads(read(path))
    change(data)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def run_audit(home: Path) -> tuple[int, str]:
    result = subprocess.run(
        [BASH, str(home / ".claude" / "skills" / "system-audit" / "audit.sh"), "--strict"],
        text=True, capture_output=True, env=env_for(home), timeout=180, check=False,
    )
    return result.returncode, result.stdout + result.stderr


M01_CASI = {
    "compose con -f prima di down": ("docker compose -f compose.yml down -v", "ask"),
    "docker-compose con --volumes": ("docker-compose -p app down --volumes", "ask"),
    "WHERE solo dentro una stringa": ("psql -c \"DELETE FROM users RETURNING 'WHERE'\"", "ask"),
    "controllo: WHERE vero": ("psql -c \"DELETE FROM users WHERE id = 1\"", "silent"),
    "controllo: WHERE con stringa": ("psql -c \"DELETE FROM users WHERE name = 'x'\"", "silent"),
    "controllo: down senza volumi": ("docker compose -f compose.yml down", "silent"),
}


def test_m01(repo: Path) -> None:
    with tempfile.TemporaryDirectory(prefix="arturo-m01-") as tmp:
        home = copy_home(repo, tmp)
        for label, (command, expected) in M01_CASI.items():
            got = dispatcher(home, command)
            assert got == expected, f"M01 {label}: atteso {expected}, ricevuto {got}"


def test_m02(repo: Path) -> None:
    with tempfile.TemporaryDirectory(prefix="arturo-m02a-") as tmp:
        home = copy_home(repo, tmp)
        edit_settings(home, lambda d: d.__setitem__("statusLine", {"type": "command", "command": "node ~/.claude/hooks/manca-statusline.js"}))
        rc, out = run_audit(home)
        assert rc != 0 and re.search(r"FAIL .*manca-statusline\.js", out), "M02 statusline mancante non segnalata dall'audit"
    with tempfile.TemporaryDirectory(prefix="arturo-m02b-") as tmp:
        home = copy_home(repo, tmp)
        edit_settings(home, lambda d: d["permissions"].pop("defaultMode", None))
        rc, out = run_audit(home)
        assert rc != 0 and re.search(r"FAIL .*defaultMode", out), "M02 defaultMode mancante non segnalato dall'audit"
    skill = read(repo / "skills" / "system-audit" / "SKILL.md")
    for promise in ("MEMORY.md", "eseguibile", "Verdetto in cima"):
        assert promise not in skill, f"M02 SKILL.md promette un controllo che audit.sh non fa: {promise}"


ANNOTAZIONE_MODERNA = re.compile(r"(->|:)\s*[\w\[\], .]*(\|\s*None|\b(list|dict|tuple|set|type)\[)")


def test_m03(repo: Path) -> None:
    missing = [hook.name for hook in sorted((repo / "hooks").glob("*.py"))
               if ANNOTAZIONE_MODERNA.search(read(hook)) and "from __future__ import annotations" not in read(hook)]
    assert not missing, f"M03 annotazioni moderne senza import differito (Python 3.8): {missing}"


def test_m05(repo: Path) -> None:
    assert "remote rename origin upstream" in read(repo / "commands" / "setup.md"), "M05 /setup crea origin senza tenere Arturo come upstream"
    assert "remote rename origin upstream" in read(repo / "README.md"), "M05 README sostituisce origin e perde gli aggiornamenti di Arturo"
    assert "upstream" in read(repo / "commands" / "novita.md"), "M05 /novita cerca aggiornamenti solo su origin"
    assert "upstream/main" in read(repo / "hooks" / "session-start.sh"), "M05 session-start non vede gli aggiornamenti su upstream"


def step6(repo: Path) -> str:
    fine = read(repo / "commands" / "fine.md")
    start = fine.find("### 6. Config Sync")
    return fine[start:fine.find("### 7.", start)] if start != -1 else ""


def test_m06(repo: Path) -> None:
    sync = step6(repo)
    assert "2>/dev/null; git commit" not in sync and "shared/ package.json README.md 2>/dev/null" not in sync, "M06 lo staging della sync nasconde gli errori"
    assert 'git add -- "$p" || echo' in sync, "M06 gli errori di git add non vengono riportati"
    for item in ("docs", "NOVITA.md", "CLAUDE.md"):
        assert item in sync, f"M06 la sync non porta {item}"
    private = sync.find('"$VIS" = "PRIVATE"')
    assert private != -1 and sync.find("for p in CLAUDE.md data/handoffs") > private, "M06 CLAUDE.md viaggia senza verificare che il remote sia privato"


def test_m07(repo: Path) -> None:
    assert "rev-list --count origin/main..HEAD" in step6(repo), "M07 la sync non ritenta i commit gia' fatti e non pushati"


def test_m08(repo: Path) -> None:
    fine = read(repo / "commands" / "fine.md")
    validate = fine[fine.find("### 3. Validate"):fine.find("### 4.")]
    assert "NON committare" in validate, "M08 /fine arriva al commit anche con il validate rosso"


def test_m10(repo: Path) -> None:
    line = next((row for row in read(repo / "README.md").splitlines() if "innestare Arturo" in row), "")
    for item in ("docs/", "NOVITA.md"):
        assert item in line, f"M10 l'installazione per copia omette {item}"


def test_m11(repo: Path) -> None:
    with tempfile.TemporaryDirectory(prefix="arturo-m11-") as tmp:
        home = copy_home(repo, tmp)
        (home / ".claude" / "hooks" / "sonda con spazio.py").write_text("pass\n", encoding="utf-8")
        edit_settings(home, lambda d: d["hooks"].setdefault("Stop", []).append(
            {"hooks": [{"type": "command", "command": 'python3 "~/.claude/hooks/sonda con spazio.py"'}]}))
        rc, out = run_audit(home)
        assert "PASS  hook diretto: sonda con spazio.py" in out, f"M11 path fra virgolette con spazio non riconosciuto dall'audit (rc={rc})"
        assert rc == 0, f"M11 audit rosso su una config valida: {out[-400:]}"


def test_m12(repo: Path) -> None:
    assert "${BASE/#\\~/$HOME}" in read(repo / "commands" / "setup.md"), "M12 mkdir riceve la tilde fra virgolette e crea una cartella chiamata ~"


def test_m13(repo: Path) -> None:
    offenders = [str(path.relative_to(repo)) for path in (repo / "skills").rglob("*.md")
                 if "Documents/ClaudeCode" in read(path) or "Su questo Mac" in read(path)]
    assert not offenders, f"M13 riferimenti alla macchina dell'autore nelle skill: {offenders}"


def test_m14(repo: Path) -> None:
    allow = json.loads(read(repo / "settings.json"))["permissions"]["allow"]
    assert "mcp__github__*" not in allow, "M14 allow globale su tutti i tool MCP GitHub, anche di scrittura"
    for prefix in ("get_", "list_", "search_"):
        assert f"mcp__github__{prefix}*" in allow, f"M14 manca l'allow di lettura mcp__github__{prefix}*"


TESTS = {
    "M01": test_m01, "M02": test_m02, "M03": test_m03, "M05": test_m05, "M06": test_m06, "M07": test_m07,
    "M08": test_m08, "M10": test_m10, "M11": test_m11, "M12": test_m12, "M13": test_m13, "M14": test_m14,
}


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
    print(f"PASS {','.join(TESTS)} finding={len(TESTS)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
