#!/usr/bin/env python3
"""CM01-CM05: una conferma sola per ogni modifica a un CLAUDE.md (3/11/2026, #4473).

Prima una modifica a un CLAUDE.md esistente riceveva un deny con le istruzioni dell'unlock: Claude
chiedeva in chat, poi il touch dell'unlock faceva chiedere block-dangerous. Due o tre sì per una
modifica (47 richieste e 43 sì in una settimana, su 4 installazioni). Ora protect_claude_md chiede
con un popup, e il popup è la conferma.

CM01 Edit su un CLAUDE.md di progetto esistente: ask, e il motivo non chiede di creare l'unlock.
CM02 Edit sul CLAUDE.md globale: ask, con l'avviso del budget di righe quando lo supera.
CM03 con l'unlock della sessione la modifica passa senza popup (allow).
CM04 `deny claude-md-progetto` nel .local decide ancora: deny.
CM05 un CLAUDE.md nuovo chiede come prima.

Sulla base f99d781 (il commit padre della modifica) sono rossi CM01 e CM02.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

CASI = ["CM01", "CM02", "CM03", "CM04", "CM05"]
DISCRIMINANTI = ["CM01", "CM02"]


def _decidi(guardia: Path, home: Path, bersaglio: Path, strumento: str = "Edit", contenuto: str = "") -> tuple[str, str]:
    env = {**os.environ, "HOME": str(home), "USERPROFILE": str(home), "ARTURO_TELEMETRIA": "0",
           "ARTURO_CLAUDE_MD_RIGHE": "3"}
    ti = {"file_path": str(bersaglio)}
    if strumento == "Write":
        ti["content"] = contenuto
    else:
        ti.update({"old_string": "riga", "new_string": "riga\nuno\ndue\ntre\nquattro"})
    p = subprocess.run([sys.executable, "-B", str(guardia)],
                       input=json.dumps({"tool_name": strumento, "tool_input": ti, "session_id": "s1"}),
                       capture_output=True, text=True, encoding="utf-8", env=env, timeout=30)
    if p.returncode == 2:
        return "block", p.stderr
    if not p.stdout.strip():
        return "silent", ""
    uscita = json.loads(p.stdout)["hookSpecificOutput"]
    return uscita["permissionDecision"], uscita.get("permissionDecisionReason", "")


def prova(repo: Path) -> list[str]:
    rossi = []
    with tempfile.TemporaryDirectory() as tmp:
        home = Path(tmp)
        hooks = home / ".claude" / "hooks"
        hooks.mkdir(parents=True)
        guardia = hooks / "protect_claude_md.py"
        guardia.write_text((repo / "hooks" / "protect_claude_md.py").read_text(encoding="utf-8"), encoding="utf-8")
        progetto = home / "progetto" / "CLAUDE.md"
        progetto.parent.mkdir()
        progetto.write_text("riga\n", encoding="utf-8")
        globale = home / ".claude" / "CLAUDE.md"
        globale.write_text("riga\n", encoding="utf-8")

        d, motivo = _decidi(guardia, home, progetto)
        if d != "ask" or "unlock" in motivo:
            rossi.append(f"CM01 CLAUDE.md di progetto: atteso ask senza istruzioni di unlock, avuto {d}: {motivo[:80]!r}")
        d, motivo = _decidi(guardia, home, globale)
        if d != "ask" or "ATTENZIONE" not in motivo:
            rossi.append(f"CM02 CLAUDE.md globale: atteso ask con l'avviso del budget, avuto {d}: {motivo[:80]!r}")

        sblocco = home / ".claude" / "claude-md-unlock-s1"
        sblocco.touch()
        d, _ = _decidi(guardia, home, progetto)
        if d != "allow":
            rossi.append(f"CM03 con l'unlock: atteso allow, avuto {d}")
        sblocco.unlink()

        (hooks / "protect_claude_md.local").write_text("deny claude-md-progetto\n", encoding="utf-8")
        d, _ = _decidi(guardia, home, progetto)
        if d != "deny":
            rossi.append(f"CM04 deny nel .local: atteso deny, avuto {d}")
        (hooks / "protect_claude_md.local").unlink()

        d, _ = _decidi(guardia, home, home / "nuova" / "CLAUDE.md", "Write", "# regole\n")
        if d != "ask":
            rossi.append(f"CM05 CLAUDE.md nuovo: atteso ask, avuto {d}")
    return rossi


def main() -> int:
    for flusso in (sys.stdout, sys.stderr):
        if hasattr(flusso, "reconfigure"):
            flusso.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument("--baseline-ref")
    a = parser.parse_args()
    rossi = prova(Path(a.repo))
    if a.baseline_ref:
        codici = [r.split()[0] for r in rossi]
        assert codici == DISCRIMINANTI, f"baseline non discriminante: rossi {codici}, attesi {DISCRIMINANTI}"
        print(f"BASELINE_DISCRIMINANTE={','.join(codici)}")
        return 0
    for r in rossi:
        print("ROSSO", r)
    print(f"una conferma per il CLAUDE.md: {len(CASI) - len(rossi)}/{len(CASI)} casi verdi")
    return 1 if rossi else 0


if __name__ == "__main__":
    sys.exit(main())
