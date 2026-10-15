#!/usr/bin/env python3
"""S01-S03: i finding di struttura della review del 15/10/2026 (task #3377).

S01 il pre-filtro dei commit del dispatcher chiama commit-secret-gate.py anche su un commit dentro
virgolette (`bash -c 'git commit'`, `eval "git commit"`) e dopo nohup, xargs, sudo: il gate li sapeva
già leggere, ma il pre-filtro non lo chiamava.
S02 block-dangerous.py e forma_comando.py non si caricano a vicenda: una sola copia di ogni modulo,
e il tokenizer sta in forma_comando.py. Le shell di commit-secret-gate.py sono quelle di forma_comando.
S03 prompt-injection-scanner.py guarda solo WebFetch, WebSearch e MCP: il suo matcher non nomina
Bash, che faceva partire un processo a ogni comando per uscire subito.

Sulla base 4515e63 ogni controllo è rosso.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path
import shutil

# Su Windows "bash" per nome è quello di WSL: si prende il bash del PATH (Git Bash).
BASH = shutil.which("bash") or "bash"

CASI = ["S01", "S02", "S03"]

PROVA_COMMIT = r'''
eval "$(grep -E '^_NL=' "$1")"
eval "$(grep -E '^PATTERN_COMMIT=' "$1")"
shift
for c in "$@"; do [[ "$c" =~ $PATTERN_COMMIT ]] && echo "PARTE $c" || echo "SALTA $c"; done
'''


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument("--baseline-ref")
    argomenti = parser.parse_args()
    repo = Path(argomenti.repo)
    rossi = []

    devono = ["bash -c 'git commit -m x'", 'eval "git commit -am y"', "xargs git commit",
              "nohup git commit -m z", "sudo git commit -m w", "git commit -m a"]
    non_devono = ["echo commit", "git log --oneline", "ls commit/"]
    r = subprocess.run([BASH, "-c", PROVA_COMMIT, "_", str(repo / "hooks" / "bash-dispatcher.sh"),
                        *devono, *non_devono], capture_output=True, text=True, timeout=30)
    righe = r.stdout.splitlines()
    persi = [c for c in devono if f"PARTE {c}" not in righe]
    troppi = [c for c in non_devono if f"SALTA {c}" not in righe]
    if persi or troppi or len(righe) != len(devono) + len(non_devono):
        rossi.append(f"S01 pre-filtro dei commit: non parte su {persi}, parte su {troppi}, uscita {r.stdout[-200:]!r}")

    forma = (repo / "hooks" / "forma_comando.py").read_text(encoding="utf-8")
    gate = (repo / "hooks" / "commit-secret-gate.py").read_text(encoding="utf-8")
    caricati: dict = {}
    vero = importlib.util.spec_from_file_location

    def spia(nome, percorso, *a, **k):
        chiave = os.path.basename(str(percorso))
        caricati[chiave] = caricati.get(chiave, 0) + 1
        return vero(nome, percorso, *a, **k)

    importlib.util.spec_from_file_location = spia
    try:
        spec = vero("bd_s02", repo / "hooks" / "block-dangerous.py")
        bd = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(bd)
        bd._find_delete("find . -name x -delete")
    finally:
        importlib.util.spec_from_file_location = vero
    if caricati.get("block-dangerous.py") or caricati.get("heredoc.py", 0) > 1:
        rossi.append(f"S02 block-dangerous e forma_comando si caricano a vicenda: caricamenti {caricati}")
    elif "def testo_shell" not in forma or '"bash", "sh", "zsh"' in gate:
        rossi.append("S02 il tokenizer non sta in forma_comando.py, o commit-secret-gate.py ha ancora la sua lista di shell")

    impostazioni = json.loads((repo / "settings.json").read_text(encoding="utf-8"))
    matcher = [g.get("matcher", "") for g in impostazioni["hooks"]["PostToolUse"]
               if any("prompt-injection-scanner.py" in h.get("command", "") for h in g.get("hooks", []))]
    if not matcher or any("Bash" in m.split("|") for m in matcher):
        rossi.append(f"S03 prompt-injection-scanner parte anche su Bash: matcher {matcher}")

    if argomenti.baseline_ref:
        codici = [r.split()[0] for r in rossi]
        assert codici == CASI, f"baseline non discriminante: rossi {codici}, attesi {CASI}"
        print(f"BASELINE_DISCRIMINANTE={','.join(codici)}")
        return 0
    for riga in rossi:
        print("ROSSO", riga)
    print(f"review struttura: {len(CASI) - len(rossi)}/{len(CASI)} casi verdi")
    return 1 if rossi else 0


if __name__ == "__main__":
    sys.exit(main())
