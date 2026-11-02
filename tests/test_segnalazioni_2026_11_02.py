#!/usr/bin/env python3
"""SG01-SG02: le segnalazioni n. 36, 38 e 41 di fine ottobre 2026, lette il 2/11/2026.

SG01 il classificatore della modalità auto ferma un passo già approvato senza offrire una conferma:
     la scrittura di brew shellenv in ~/.zprofile (n. 36), il touch dello sblocco di una guardia (n. 38),
     un aggiornamento via ssh (n. 41). Lo stile Conciso dice di preparare un solo comando con `!`, dà la
     riga di Homebrew e avvisa che un LaunchAgent non scrive in iCloud Drive, Documenti e Scrivania.
SG02 la guardia dei percorsi di avvio automatico e quella dei file di config dicevano a Claude
     "esegui: touch ~/.claude/system-unlock-..." e "config-unlock-...": in modalità auto il classificatore
     lo ferma come [Self-Modification]. Lo sblocco resta alla persona: il messaggio le fa lanciare il
     touch col prefisso `!`.

Sulla base 8b141c0 ogni controllo deve fallire con un AssertionError che comincia con il suo codice.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_sg01(repo: Path) -> None:
    stile = read(repo / "output-styles" / "conciso.md")
    titolo = "## I comandi che lancia la persona"
    assert titolo in stile, "SG01 lo stile Conciso non ha la sezione dei comandi della persona"
    sezione = stile[stile.index(titolo):]
    sezione = sezione[:sezione.find("\n## ", 1)] if "\n## " in sezione[1:] else sezione
    for pezzo in ("auto mode classifier", "`!`", "brew shellenv", "~/.zprofile", "LaunchAgent", "iCloud Drive"):
        assert pezzo in sezione, f"SG01 la sezione dei comandi della persona non dice: {pezzo}"


def messaggio(repo: Path, relativo: str) -> str:
    """La ragione del deny di protect_claude_md.py per un Write su ~/<relativo>, in una home finta."""
    with tempfile.TemporaryDirectory() as tmp:
        home = Path(tmp)
        hooks = home / ".claude" / "hooks"
        hooks.mkdir(parents=True)
        (hooks / "protect_claude_md.py").write_text(read(repo / "hooks" / "protect_claude_md.py"), encoding="utf-8")
        bersaglio = home / relativo
        bersaglio.parent.mkdir(parents=True, exist_ok=True)
        bersaglio.write_text("riga\n", encoding="utf-8")
        env = {**os.environ, "HOME": str(home), "USERPROFILE": str(home), "ARTURO_TELEMETRIA": "0"}
        ingresso = {"tool_name": "Edit", "session_id": "sg02",
                    "tool_input": {"file_path": str(bersaglio), "old_string": "riga", "new_string": "altra"}}
        p = subprocess.run([sys.executable, "-B", str(hooks / "protect_claude_md.py")], input=json.dumps(ingresso),
                           capture_output=True, text=True, encoding="utf-8", env=env, timeout=30)
        uscita = json.loads(p.stdout)["hookSpecificOutput"] if p.stdout.strip() else {}
        return uscita.get("permissionDecision", "") + " " + uscita.get("permissionDecisionReason", "")


def test_sg02(repo: Path) -> None:
    for relativo, sblocco in (("Library/LaunchAgents/com.prova.backup.plist", "system-unlock"),
                              (".claude/hooks/mia-guardia.py", "config-unlock")):
        m = messaggio(repo, relativo)
        assert m.startswith("deny"), f"SG02 {relativo} non è più protetto: {m[:200]}"
        assert f"! touch ~/.claude/{sblocco}-sg02" in m, \
            f"SG02 lo sblocco di {relativo} non passa alla persona col prefisso !: {m[:300]}"


TESTS = {"SG01": test_sg01, "SG02": test_sg02}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--baseline-ref")
    args = parser.parse_args()
    repo = args.repo.resolve()
    if args.baseline_ref:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            for f in ("output-styles/conciso.md", "hooks/protect_claude_md.py"):
                (base / f).parent.mkdir(parents=True, exist_ok=True)
                (base / f).write_text(subprocess.run(["git", "-C", str(repo), "show", f"{args.baseline_ref}:{f}"],
                                                     capture_output=True, text=True, encoding="utf-8",
                                                     check=True).stdout, encoding="utf-8")
            rossi, altro = [], []
            for nome, test in TESTS.items():
                try:
                    test(base)
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
