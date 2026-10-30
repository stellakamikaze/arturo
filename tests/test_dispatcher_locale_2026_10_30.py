#!/usr/bin/env python3
"""DL01-DL09: le guardie personali di hooks/bash-dispatcher.local.

Chi installa Arturo aggiunge le sue guardie senza toccare il dispatcher: il .local nomina punto,
guardia e argomenti, e il dispatcher le lancia dentro run_guard (30/10/2026, migrazione della config
di Federico, #4291). Il banco costruisce una HOME finta con hooks e bin del repo, scrive il .local e
qualche guardia finta, e guarda la decisione del dispatcher.

Invarianti (verdi anche sulla base): DL01 senza .local un rm ricorsivo chiede come prima; DL03 una
riga `exit 0` nel .local non spegne le guardie; DL07 attenua non scioglie un blocco.
Sulla base 749e18d sono rossi i casi del meccanismo: DL02, DL04, DL05, DL06, DL08, DL09.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

CASI = ["DL01", "DL02", "DL03", "DL04", "DL05", "DL06", "DL07", "DL08", "DL09"]
DISCRIMINANTI = ["DL02", "DL04", "DL05", "DL06", "DL08", "DL09"]
BASH = shutil.which("bash") or "bash"

GUARDIE = {
    "dice-allow.py": 'import json\nprint(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", '
                     '"permissionDecision": "allow", "permissionDecisionReason": "allow personale"}}))\n',
    "tace.py": "",
    "si-rompe.py": "import sys\nsys.exit(1)\n",
    # print scrive CRLF su Windows: il dispatcher deve riconoscere "tace" lo stesso.
    "attenua-finta.py": 'print("tace")\n',
}


def casa(repo: Path, base: Path, dispatcher: str | None, local: str | None) -> Path:
    home = base / "home"
    shutil.copytree(repo / "hooks", home / ".claude" / "hooks", ignore=shutil.ignore_patterns("*.local", "__pycache__"))
    shutil.copytree(repo / "bin", home / ".claude" / "bin", ignore=shutil.ignore_patterns("__pycache__", "web"))
    if dispatcher is not None:
        (home / ".claude" / "hooks" / "bash-dispatcher.sh").write_text(dispatcher, encoding="utf-8", newline="\n")
    for nome, testo in GUARDIE.items():
        (home / ".claude" / "hooks" / nome).write_text(testo, encoding="utf-8")
    if local is not None:
        (home / ".claude" / "hooks" / "bash-dispatcher.local").write_text(local, encoding="utf-8")
    return home


def decidi(home: Path, comando: str) -> tuple[str, str, str]:
    """(decisione, motivo, stderr) del dispatcher su `comando`."""
    env = {**os.environ, "HOME": str(home), "USERPROFILE": str(home), "ARTURO_TELEMETRIA": "0"}
    dati = {"tool_name": "Bash", "tool_input": {"command": comando}, "cwd": str(home)}
    p = subprocess.run([BASH, str(home / ".claude" / "hooks" / "bash-dispatcher.sh")], input=json.dumps(dati),
                       capture_output=True, text=True, encoding="utf-8", errors="replace", env=env, timeout=120)
    if p.returncode == 2:
        return "block", "", p.stderr
    if not p.stdout.strip():
        return "silent", "", p.stderr
    try:
        h = json.loads(p.stdout)["hookSpecificOutput"]
        return h["permissionDecision"], h.get("permissionDecisionReason", ""), p.stderr
    except (json.JSONDecodeError, KeyError, TypeError):
        return "?", p.stdout[:80], p.stderr


def prova(repo: Path, dispatcher: str | None) -> list[str]:
    rossi: list[str] = []

    def caso(codice: str, local: str | None, comando: str, verifica) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            esito = decidi(casa(repo, Path(tmp), dispatcher, local), comando)
            if not verifica(*esito):
                rossi.append(f"{codice} {comando!r}: {esito[0]} {esito[1][:70]!r} {esito[2][:90]!r}")

    caso("DL01", None, "rm -rf ~/Documents/lavoro", lambda d, m, e: d == "ask")
    caso("DL02", "prima-danger dice-allow.py\n", "rm -rf ~/Documents/lavoro", lambda d, m, e: d == "allow")
    caso("DL03", "exit 0\nprima-danger tace.py ; exit 0\n", "rm -rf ~/Documents/lavoro",
         lambda d, m, e: d == "ask")
    caso("DL04", "danger-claude tace.py guardia\n", "rm -rf ~/.claude/data/vecchio", lambda d, m, e: d == "silent")
    caso("DL05", "danger-claude dice-allow.py\n", "rm -rf ~/.claude/data/vecchio",
         lambda d, m, e: d == "ask" and "non ha prodotto una decisione valida" in m)
    caso("DL06", "attenua attenua-finta.py\n", "rm -rf ~/Documents/lavoro", lambda d, m, e: d == "silent")
    caso("DL07", "attenua attenua-finta.py\n", "bw export", lambda d, m, e: d == "block")
    caso("DL08", "finale dice-allow.py\n", "ls ~/.claude/data", lambda d, m, e: d == "allow")
    caso("DL09", "prima-danger ../fuori.py\ndove-vuoi dice-allow.py\n", "rm -rf ~/Documents/lavoro",
         lambda d, m, e: d == "ask" and e.count("riga ignorata") == 2)
    return rossi


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument("--baseline-ref")
    argomenti = parser.parse_args()
    repo = Path(argomenti.repo)
    if argomenti.baseline_ref:
        vecchio = subprocess.run(["git", "-C", str(repo), "show", f"{argomenti.baseline_ref}:hooks/bash-dispatcher.sh"],
                                 capture_output=True, text=True, encoding="utf-8", check=True).stdout
        codici = [r.split()[0] for r in prova(repo, vecchio)]
        assert codici == DISCRIMINANTI, f"baseline non discriminante: rossi {codici}, attesi {DISCRIMINANTI}"
        print(f"BASELINE_DISCRIMINANTE={','.join(codici)}")
        return 0
    rossi = prova(repo, None)
    for r in rossi:
        print("ROSSO", r)
    print(f"dispatcher .local: {len(CASI) - len(rossi)}/{len(CASI)} casi verdi")
    return 1 if rossi else 0


if __name__ == "__main__":
    sys.exit(main())
