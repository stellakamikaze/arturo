#!/usr/bin/env python3
"""PP01-PP15: le righe per percorso di arturo/protect_claude_md.local (21/11/2026).

Chi apre una categoria intera (`allow config`, `allow dot-claude-progetto`) può chiedere conferma sui pochi
file che decidono i permessi: `ask percorso <glob>` e `deny percorso <glob>`. La riga stringe soltanto: non
allenta la categoria, gli sblocchi, i percorsi intoccabili né la validità JSON dei settings.

Invarianti (verdi anche sulla base): PP02, PP05, PP06, PP07, PP12, PP14, PP15.
Sulla base 9641c7c sono rossi i casi del meccanismo: PP01, PP03, PP04, PP08, PP09, PP10, PP11, PP13.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

CASI = [f"PP{n:02d}" for n in range(1, 16)]
DISCRIMINANTI = ["PP01", "PP03", "PP04", "PP08", "PP09", "PP10", "PP11", "PP13"]

# Le sei righe della config di chi ha scritto Arturo: tutto aperto, salvo CLAUDE.md globale e settings in radice.
APERTO = ("ask claude-md-globale\nallow claude-md-progetto\nask settings-radice\nallow config\n"
          "allow dot-claude\nallow dot-claude-progetto\n")


def decidi(guardia: str, local: str, strumento: str, relativo: str, contenuto: str | None = None,
           radice: str = ".claude", sblocco: bool = False) -> str:
    """radice: `.claude` (la config), `progetto` (un progetto) o `.` (la home)."""
    with tempfile.TemporaryDirectory() as tmp:
        home = Path(tmp)
        claude = home / ".claude"
        (claude / "hooks").mkdir(parents=True)
        (claude / "arturo").mkdir()
        (claude / "hooks" / "protect_claude_md.py").write_text(guardia, encoding="utf-8")
        (claude / "arturo" / "protect_claude_md.local").write_text(local, encoding="utf-8")
        if sblocco:
            (claude / "config-unlock-s1").write_text("", encoding="utf-8")
        bersaglio = home / radice / relativo
        bersaglio.parent.mkdir(parents=True, exist_ok=True)
        bersaglio.write_text("{}\n" if bersaglio.suffix == ".json" else "riga\n", encoding="utf-8")
        ti = {"file_path": str(bersaglio)}
        ti.update({"content": contenuto} if contenuto is not None else {"old_string": "riga", "new_string": "altra"})
        env = {**os.environ, "HOME": str(home), "USERPROFILE": str(home), "ARTURO_TELEMETRIA": "0"}
        env.pop("CLAUDE_CONFIG_DIR", None)
        p = subprocess.run([sys.executable, "-B", str(claude / "hooks" / "protect_claude_md.py")],
                           input=json.dumps({"tool_name": strumento, "tool_input": ti, "session_id": "s1"}),
                           capture_output=True, text=True, encoding="utf-8", env=env, timeout=30)
        if p.returncode == 2:
            return "block"
        if not p.stdout.strip():
            return "silent"
        return json.loads(p.stdout)["hookSpecificOutput"]["permissionDecision"]


def prova(guardia: str) -> list[str]:
    rossi = []
    guardie = APERTO + "ask percorso hooks/giudice-permessi.py  # decide i permessi\nask percorso git/hooks/\n"
    progetti = APERTO + "ask percorso */.claude/settings*.json\n"
    casi = [
        # La guardia nominata chiede, il resto di hooks/ passa come prima.
        ("PP01", guardie, "Edit", "hooks/giudice-permessi.py", None, ".claude", False, "ask"),
        ("PP02", guardie, "Edit", "hooks/altro.py", None, ".claude", False, "allow"),
        # Un glob che finisce con la barra copre la cartella.
        ("PP03", guardie, "Write", "git/hooks/pre-push", "#!/bin/sh\n", ".claude", False, "ask"),
        # Un glob con * in testa vale ovunque: i settings di ogni progetto, non gli altri file di .claude.
        ("PP04", progetti, "Edit", ".claude/settings.local.json", None, "progetto", False, "ask"),
        ("PP05", progetti, "Edit", ".claude/agents/a.md", None, "progetto", False, "allow"),
        # La riga non allenta: `allow percorso` non esiste, e un ask non apre un intoccabile.
        ("PP06", "ask settings-radice\nallow percorso settings.json\n", "Edit", "settings.json", None, ".claude",
         False, "ask"),
        ("PP07", APERTO + "ask percorso firme/\n", "Write", "firme/rilasci.allowed_signers", "chiave", ".claude",
         False, "deny"),
        ("PP08", APERTO + "deny percorso hooks/giudice-permessi.py\n", "Edit", "hooks/giudice-permessi.py", None,
         ".claude", False, "deny"),
        ("PP09", APERTO + "ask percorso .git/config\n", "Edit", ".git/config", None, ".claude", False, "ask"),
        # Senza categoria, e fuori da ogni categoria, decide la riga.
        ("PP10", "ask percorso data/appunti.md\n", "Edit", "data/appunti.md", None, ".claude", False, "ask"),
        ("PP11", "ask percorso ~/fuori/\n", "Edit", "fuori/a.txt", None, ".", False, "ask"),
        # Lo sblocco della sessione vince, come su ogni file di config.
        ("PP12", guardie, "Edit", "hooks/giudice-permessi.py", None, ".claude", True, "allow"),
        # Il più severo vince: deny sulla riga, ask sulla categoria.
        ("PP13", "ask claude-md-globale\ndeny percorso CLAUDE.md\n", "Edit", "CLAUDE.md", None, ".claude", False,
         "deny"),
        # Un settings che diventerebbe JSON rotto si ferma comunque.
        ("PP14", progetti, "Write", ".claude/settings.local.json", "{ non json", "progetto", False, "deny"),
        # Una riga che non copre il file non cambia niente.
        ("PP15", "ask percorso hooks/giudice-permessi.py\n", "Edit", "fuori/a.txt", None, ".", False, "silent"),
    ]
    for codice, local, strumento, relativo, contenuto, radice, sblocco, atteso in casi:
        avuto = decidi(guardia, local, strumento, relativo, contenuto, radice, sblocco)
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
    print(f"protect percorso: {len(CASI) - len(rossi)}/{len(CASI)} casi verdi")
    return 1 if rossi else 0


if __name__ == "__main__":
    sys.exit(main())
