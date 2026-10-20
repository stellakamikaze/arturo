#!/usr/bin/env python3
"""C01-C06 e I03: contratti pubblici dell'allineamento."""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path


REMOVED = (
    "commands/arewedone.md", "commands/commit.md", "commands/creative.md", "commands/deep-review.md",
    "commands/doc-update.md", "commands/feature.md", "commands/plan-review.md", "commands/rebase.md",
    "commands/retro.md", "commands/scope.md", "commands/ship.md", "commands/ui.md", "commands/worktree.md",
    "agents/drafter.md", "agents/synthesizer.md", "hooks/github_issue_guard.py", "hooks/quality-check.sh",
    "hooks/session-reminder.sh", "skills/autofix", "skills/keyword-research", "skills/review-checklist",
    "skills/ui-reference", "skills/validate",
)
# I03 dal 17/10/2026 (#3505): i nomi della config privata stanno solo come impronte sha256 in
# tests/igiene.py. Sul ramo della landing il resto del file resta quello del ramo: i controlli di dev
# (defaultMode, validation-gate-lang, file tolti) qui non valgono (20/10/2026, #3551).
sys.path.insert(0, str(Path(__file__).resolve().parent))
import igiene  # noqa: E402


def assert_igiene(repo: Path) -> None:
    problemi = igiene.controlla(repo)
    assert not problemi, "I03 igiene: " + "; ".join(problemi)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--baseline-ref")
    args = parser.parse_args()
    repo = args.repo.resolve()
    if args.baseline_ref:
        probe = subprocess.run([sys.executable, "-B", __file__, "--repo", str(args.repo)], capture_output=True, text=True, timeout=30, check=False)
        assert probe.returncode != 0, "baseline non discriminante su wiring e potature"
        print("BASELINE_DISCRIMINANTE=C01-C06,I03")
        return 0
    settings = (repo / "settings.json").read_text(encoding="utf-8")
    assert '"defaultMode": "acceptEdits"' in settings, "I01 defaultMode cambiato"
    assert "github_issue_guard.py" not in settings and "quality-check.sh" not in settings and "session-reminder.sh" not in settings, "C05 wiring rimosso residuo"
    gate = (repo / "shared" / "validation-gate.md").read_text(encoding="utf-8")
    assert "PIPESTATUS[0]" in gate and "Quality gate: SKIP" not in gate, "C06 gate maschera errori"
    start = (repo / "hooks" / "session-start.sh").read_text(encoding="utf-8")
    end = (repo / "hooks" / "session-end.sh").read_text(encoding="utf-8")
    assert "rev-parse --git-path rebase-merge" in start, "C01 rebase non rilevato"
    assert end.index("rm -f ~/.claude/claude-md-unlock-") < end.index("git -C"), "C02 cleanup dopo uscita anticipata"
    for item in REMOVED:
        assert not (repo / item).exists(), f"I03 file rimosso ancora presente: {item}"
    # README dichiara python3 >= 3.8: annotazioni `X | None` e `list[str]` senza import
    # differito vanno in TypeError al caricamento su 3.8 e spengono la guardia.
    for hook in sorted((repo / "hooks").glob("*.py")):
        source = hook.read_text(encoding="utf-8")
        if re.search(r"(->|:)\s*[\w\[\], .]*(\|\s*None|\b(list|dict|tuple|set|type)\[)", source):
            assert "from __future__ import annotations" in source, f"C07 {hook.name}: annotazione moderna senza import differito"
    assert_igiene(repo)
    print(f"PASS C01-C06,I03 rimossi={len(REMOVED)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
