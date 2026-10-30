#!/usr/bin/env python3
"""PL01-PL10: le decisioni personali di hooks/protect_claude_md.local.

Il .local cambia la decisione di alcune categorie (CLAUDE.md, settings in radice, config, il resto di
~/.claude) senza toccare la guardia (30/10/2026, #4291). Non può allentare i percorsi di avvio, i file
di sblocco, firme/, gli script dell'aggiornamento, i file hooks/*.local né la validità JSON dei settings.

Invarianti (verdi anche sulla base): PL01, PL04, PL05, PL07, PL08, PL09, PL10.
Sulla base 749e18d sono rossi i casi del meccanismo: PL02, PL03, PL06.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

CASI = [f"PL{n:02d}" for n in range(1, 11)]
DISCRIMINANTI = ["PL02", "PL03", "PL06"]


def decidi(guardia: str, local: str | None, strumento: str, relativo: str, contenuto: str | None = None,
           esiste: bool = True, in_progetto: bool = False) -> str:
    with tempfile.TemporaryDirectory() as tmp:
        home = Path(tmp)
        hooks = home / ".claude" / "hooks"
        hooks.mkdir(parents=True)
        (hooks / "protect_claude_md.py").write_text(guardia, encoding="utf-8")
        if local is not None:
            (hooks / "protect_claude_md.local").write_text(local, encoding="utf-8")
        bersaglio = (home / "progetto" / relativo) if in_progetto else (home / ".claude" / relativo)
        bersaglio.parent.mkdir(parents=True, exist_ok=True)
        if esiste:
            bersaglio.write_text("{}\n" if bersaglio.suffix == ".json" else "riga\n", encoding="utf-8")
        ti = {"file_path": str(bersaglio)}
        ti.update({"content": contenuto} if contenuto is not None else {"old_string": "riga", "new_string": "altra"})
        env = {**os.environ, "HOME": str(home), "USERPROFILE": str(home), "ARTURO_TELEMETRIA": "0"}
        p = subprocess.run([sys.executable, "-B", str(hooks / "protect_claude_md.py")],
                           input=json.dumps({"tool_name": strumento, "tool_input": ti, "session_id": "s1"}),
                           capture_output=True, text=True, encoding="utf-8", env=env, timeout=30)
        if p.returncode == 2:
            return "block"
        if not p.stdout.strip():
            return "silent"
        return json.loads(p.stdout)["hookSpecificOutput"]["permissionDecision"]


def prova(guardia: str) -> list[str]:
    rossi = []
    tutto = "allow claude-md-globale\nallow claude-md-progetto\nallow settings-radice\nallow config\nallow dot-claude\n"
    casi = [
        ("PL01", None, "Edit", "CLAUDE.md", None, True, False, "deny"),
        ("PL02", "ask claude-md-globale  # Federico\n", "Edit", "CLAUDE.md", None, True, False, "ask"),
        ("PL03", "allow config\n", "Edit", "hooks/mia-guardia.py", None, True, False, "allow"),
        ("PL04", tutto, "Edit", "hooks/bash-dispatcher.local", None, True, False, "deny"),
        ("PL05", tutto, "Write", "firme/rilasci.allowed_signers", "chiave", True, False, "deny"),
        ("PL06", "allow dot-claude\n", "Edit", "data/appunti.md", None, True, False, "allow"),
        ("PL07", tutto, "Write", "settings.json", "{ non json", True, False, "deny"),
        ("PL08", tutto, "Write", "config-unlock-s1", "", False, False, "ask"),
        ("PL09", tutto, "Write", "CLAUDE.md", "nuovo", False, True, "ask"),
        ("PL10", "allow tutto\nallow\n", "Edit", "CLAUDE.md", None, True, False, "deny"),
    ]
    for codice, local, strumento, relativo, contenuto, esiste, in_progetto, atteso in casi:
        avuto = decidi(guardia, local, strumento, relativo, contenuto, esiste, in_progetto)
        if avuto != atteso:
            rossi.append(f"{codice} {strumento} {relativo}: atteso {atteso}, avuto {avuto}")
    return rossi


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument("--baseline-ref")
    argomenti = parser.parse_args()
    repo = Path(argomenti.repo)
    if argomenti.baseline_ref:
        vecchia = subprocess.run(["git", "-C", str(repo), "show", f"{argomenti.baseline_ref}:hooks/protect_claude_md.py"],
                                 capture_output=True, text=True, encoding="utf-8", check=True).stdout
        codici = [r.split()[0] for r in prova(vecchia)]
        assert codici == DISCRIMINANTI, f"baseline non discriminante: rossi {codici}, attesi {DISCRIMINANTI}"
        print(f"BASELINE_DISCRIMINANTE={','.join(codici)}")
        return 0
    rossi = prova((repo / "hooks" / "protect_claude_md.py").read_text(encoding="utf-8"))
    for r in rossi:
        print("ROSSO", r)
    print(f"protect .local: {len(CASI) - len(rossi)}/{len(CASI)} casi verdi")
    return 1 if rossi else 0


if __name__ == "__main__":
    sys.exit(main())
