#!/usr/bin/env python3
"""GS01-GS19: una chiave letta con un glob o con le graffe nella cartella e nel nome (21/11/2026, #6279).

`cat ~/.s??/i?_ed25519` non nomina né `.ssh` né `id_ed25519`: il pre-filtro del dispatcher deve passare il
comando alle guardie (quelle personali del punto prima-danger e block-dangerous), e block-dangerous deve
risolvere il percorso. Il banco passa al dispatcher il JSON del PreToolUse in una casa finta e legge la
decisione: nessun comando viene eseguito. Una guardia personale finta ("spia") lascia un segno quando il
dispatcher la chiama.

Invarianti (verdi anche sulla base): GS01 e GS02, rossi fino a 0f3e48b^ (il plugin 0.2.19), e i casi che
devono tacere, GS11-GS18.
Sulla base e794f3e sono rossi GS03-GS10 e GS19: il `cd` in una cartella scritta con un glob, le graffe, la cartella
intera con un glob, e i file segreti della home fuori dalle cartelle (`.npmrc`, `.docker/config.json`), e `*` con dotglob acceso.
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

CASI = [f"GS{n:02d}" for n in range(1, 20)]
DISCRIMINANTI = [f"GS{n:02d}" for n in range(3, 11)] + ["GS19"]
BASH = shutil.which("bash") or "bash"
# I file che il comando di git prende dalla base: il pre-filtro e la guardia che risolve il percorso.
SORVEGLIATI = ("hooks/bash-dispatcher.sh", "hooks/block-dangerous.py")

SPIA = ('import os\nopen(os.path.join(os.path.expanduser("~"), "spia-chiamata"), "w").close()\n')

# (codice, comando, decisione attesa, la spia deve essere chiamata)
COMANDI = [
    # Il caso del task: glob nella cartella e nel nome.
    ("GS01", "cat ~/.s??/i?_ed25519", "ask", True),
    ("GS02", "cat ~/.s*/i*", "ask", True),
    # La cartella col glob in un cd, il nome col glob dopo.
    ("GS03", "cd ~/.s?? && cat i?_ed25519", "ask", True),
    # Le graffe si espandono prima del glob.
    ("GS04", "cat ~/.s{sh,x}/i?_ed25519", "ask", True),
    ("GS05", "cat ~/{.ssh,x}/i?_ed25519", "ask", True),
    ("GS06", "cat ~/.{netrc,x}", "ask", True),
    # La cartella intera, per un programma che legge le cartelle.
    ("GS07", "grep -r KEY ~/.s??", "ask", True),
    # I file segreti della home che non stanno in una cartella dei segreti.
    ("GS08", "cat ~/.np?rc", "ask", True),
    ("GS09", "cat ~/.d*/c*.json", "ask", True),
    ("GS10", "head -1 ~/.config/g?/h*", "ask", True),
    # Quello che deve restare muto.
    ("GS11", "cat ~/doc.?/nota.txt", "silent", None),
    ("GS12", "jq '.items[]' a.json", "silent", None),
    ("GS13", "ls ~/.s??", "silent", None),
    ("GS14", "cat ~/.s??/*.pub", "silent", None),
    # `*` non entra in una cartella che comincia col punto, e `*.json` non trova `.claude.json`.
    ("GS15", "cat ~/*/i?_ed25519", "silent", None),
    ("GS16", "grep -r --include=*.json chiave .", "silent", None),
    ("GS17", "cat ~/doc.{d,x}/n?ta.txt", "silent", None),
    ("GS18", "cd ~/doc.? && cat n*", "silent", None),
    # Con dotglob `*` entra anche in `.ssh`.
    ("GS19", "shopt -s dotglob; cat ~/*/i?_ed25519", "ask", True),
]


def casa(repo: Path, base: Path, vecchi: dict[str, str]) -> Path:
    home = base / "home"
    hooks = home / ".claude" / "hooks"
    shutil.copytree(repo / "hooks", hooks, ignore=shutil.ignore_patterns("*.local", "__pycache__"))
    shutil.copytree(repo / "bin", home / ".claude" / "bin", ignore=shutil.ignore_patterns("__pycache__", "web"))
    for relativo, testo in vecchi.items():
        with open(str(home / ".claude" / relativo), "w", encoding="utf-8", newline="\n") as uscita:
            uscita.write(testo)
    (hooks / "spia.py").write_text(SPIA, encoding="utf-8")
    (home / ".claude" / "arturo").mkdir()
    (home / ".claude" / "arturo" / "bash-dispatcher.local").write_text("prima-danger spia.py\n", encoding="utf-8")
    for relativo in (".ssh/id_ed25519", ".ssh/id_ed25519.pub", ".ssh/config", ".netrc", ".npmrc",
                     ".docker/config.json", ".config/gh/hosts.yml", "doc.d/nota.txt", "a.json"):
        f = home / relativo
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text("finto\n", encoding="utf-8")
    return home


def decidi(home: Path, comando: str) -> tuple[str, bool]:
    """(decisione del dispatcher, la spia è stata chiamata)."""
    segno = home / "spia-chiamata"
    if segno.exists():
        segno.unlink()
    env = {**os.environ, "HOME": str(home), "USERPROFILE": str(home), "ARTURO_TELEMETRIA": "0", "SHELL": "/bin/bash"}
    env.pop("CLAUDE_CONFIG_DIR", None)
    dati = {"tool_name": "Bash", "tool_input": {"command": comando}, "cwd": str(home), "session_id": "s1"}
    p = subprocess.run([BASH, str(home / ".claude" / "hooks" / "bash-dispatcher.sh")], input=json.dumps(dati),
                       capture_output=True, text=True, encoding="utf-8", errors="replace", env=env, timeout=120)
    if p.returncode == 2:
        decisione = "block"
    elif not p.stdout.strip():
        decisione = "silent" if p.returncode == 0 else f"rc{p.returncode}"
    else:
        decisione = json.loads(p.stdout)["hookSpecificOutput"]["permissionDecision"]
    return decisione, segno.exists()


def prova(repo: Path, vecchi: dict[str, str]) -> list[str]:
    rossi = []
    with tempfile.TemporaryDirectory() as tmp:
        # realpath: sul Mac /var è un link, e la casa del comando deve essere quella che la guardia risolve
        home = casa(repo, Path(os.path.realpath(tmp)), vecchi)
        for codice, comando, atteso, spia in COMANDI:
            avuto, chiamata = decidi(home, comando)
            if avuto != atteso:
                rossi.append(f"{codice} {comando}: atteso {atteso}, avuto {avuto}")
            elif spia and not chiamata:
                rossi.append(f"{codice} {comando}: la guardia personale non è stata chiamata")
    return rossi


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument("--baseline-ref")
    argomenti = parser.parse_args()
    repo = Path(argomenti.repo)
    for relativo in SORVEGLIATI:
        assert (repo / relativo).is_file(), f"manca {relativo} in {repo}"
    if argomenti.baseline_ref:
        vecchi = {r: subprocess.run(["git", "-C", str(repo), "show", f"{argomenti.baseline_ref}:{r}"],
                                    capture_output=True, text=True, encoding="utf-8", check=True).stdout
                  for r in SORVEGLIATI}
        codici = [r.split()[0] for r in prova(repo, vecchi)]
        assert codici == DISCRIMINANTI, f"baseline non discriminante: rossi {codici}, attesi {DISCRIMINANTI}"
        print(f"BASELINE_DISCRIMINANTE={','.join(codici)}")
        return 0
    rossi = prova(repo, {})
    for r in rossi:
        print("ROSSO", r)
    print(f"glob segreti: {len(CASI) - len(rossi)}/{len(CASI)} casi verdi")
    return 1 if rossi else 0


if __name__ == "__main__":
    sys.exit(main())
