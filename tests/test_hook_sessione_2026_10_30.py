#!/usr/bin/env python3
"""HS01-HS04: gli hook di inizio e fine sessione con più sessioni aperte.

HS01 la chiusura toglie i file di sblocco della propria sessione;
HS02 lascia quelli di un'altra sessione aperta (fino al 30/10/2026 li toglieva tutti);
HS03 toglie quelli rimasti da più di un giorno e i file seen vecchi di memory-retrieve;
HS04 l'avvio dice che ~/.claude è a metà rebase anche se la sessione parte da un progetto.

Invariante (verde anche sulla base): HS01.
Sulla base 749e18d sono rossi HS02, HS03, HS04.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

CASI = ["HS01", "HS02", "HS03", "HS04"]
DISCRIMINANTI = ["HS02", "HS03", "HS04"]
BASH = shutil.which("bash") or "bash"


def lancia(hook: str, testo: str, home: Path, progetto: Path, dati: dict) -> subprocess.CompletedProcess:
    script = home / ".claude" / "hooks" / hook
    script.parent.mkdir(parents=True, exist_ok=True)
    script.write_text(testo, encoding="utf-8", newline="\n")
    env = {**os.environ, "HOME": str(home), "USERPROFILE": str(home), "ARTURO_TELEMETRIA": "0",
           "ARTURO_AGGIORNAMENTI": "manuali", "GIT_TERMINAL_PROMPT": "0"}
    return subprocess.run([BASH, str(script)], input=json.dumps(dati), cwd=progetto, capture_output=True,
                          text=True, encoding="utf-8", errors="replace", env=env, timeout=120)


def prova(fine: str, avvio: str) -> list[str]:
    rossi = []
    with tempfile.TemporaryDirectory() as tmp:
        home, progetto = Path(tmp, "home"), Path(tmp, "progetto")
        cartella = home / ".claude"
        (cartella / "session-env").mkdir(parents=True)
        progetto.mkdir()
        (progetto / "CLAUDE.md").write_text("progetto\n", encoding="utf-8")
        mia, altra, vecchia = (cartella / "config-unlock-mia", cartella / "config-unlock-altra",
                               cartella / "claude-md-unlock-vecchia")
        seen_vecchio = cartella / "session-env" / "retrieve-vecchia.seen"
        for f in (mia, altra, vecchia, seen_vecchio):
            f.write_text("", encoding="utf-8")
        due_giorni_fa = time.time() - 2 * 86400
        for f in (vecchia, seen_vecchio):
            os.utime(f, (due_giorni_fa, due_giorni_fa))
        lancia("session-end.sh", fine, home, progetto, {"session_id": "mia", "hook_event_name": "SessionEnd"})
        if mia.exists():
            rossi.append("HS01 lo sblocco della propria sessione resta")
        if not altra.exists():
            rossi.append("HS02 lo sblocco di un'altra sessione aperta è stato tolto")
        if vecchia.exists() or seen_vecchio.exists():
            rossi.append("HS03 restano lo sblocco o il file seen di più di un giorno fa")

        subprocess.run(["git", "init", "-q", str(cartella)], check=True)
        (cartella / ".git" / "rebase-merge").mkdir()
        esito = lancia("session-start.sh", avvio, home, progetto, {"source": "startup"})
        if "metà rebase" not in esito.stdout:
            rossi.append(f"HS04 l'avvio non segnala il rebase in ~/.claude: {esito.stdout[-200:]!r}")
    return rossi


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument("--baseline-ref")
    argomenti = parser.parse_args()
    repo = Path(argomenti.repo)

    def testo(nome: str) -> str:
        if argomenti.baseline_ref:
            return subprocess.run(["git", "-C", str(repo), "show", f"{argomenti.baseline_ref}:hooks/{nome}"],
                                  capture_output=True, text=True, encoding="utf-8", check=True).stdout
        return (repo / "hooks" / nome).read_text(encoding="utf-8")

    rossi = prova(testo("session-end.sh"), testo("session-start.sh"))
    if argomenti.baseline_ref:
        codici = [r.split()[0] for r in rossi]
        assert codici == DISCRIMINANTI, f"baseline non discriminante: rossi {codici}, attesi {DISCRIMINANTI}"
        print(f"BASELINE_DISCRIMINANTE={','.join(codici)}")
        return 0
    for r in rossi:
        print("ROSSO", r)
    print(f"hook di sessione: {len(CASI) - len(rossi)}/{len(CASI)} casi verdi")
    return 1 if rossi else 0


if __name__ == "__main__":
    sys.exit(main())
