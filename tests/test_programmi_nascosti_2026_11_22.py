#!/usr/bin/env python3
"""PN: un programma nascosto alle guardie, con una parola pericolosa nel comando, chiede conferma (#6323).

Le guardie leggono il nome del programma. Quattro forme lo tolgono dal testo: un nome che si calcola quando il
comando gira (sostituzione, variabile, alias, funzione), xargs, un testo che una shell o un interprete esegue
dallo stdin, il codice inline di un interprete. La regola codice-nascosto di block-dangerous chiede conferma se
c'è una di queste forme e il comando contiene una parola pericolosa: rm, unlink, shred, push, reset, clean,
curl, wget, bw, gh, o un percorso dei segreti. Una parola che è già un programma visibile, o il sottocomando di
un git visibile, non conta. Il codice di un interprete conta solo se ha una primitiva che lancia un programma.

Qui c'è un caso per forma, più i comandi vicini che devono restare muti: vengono dalla misura del 22/11/2026 su
24.493 comandi Bash veri, dove la regola chiede su 52 (0,21%). Le forme provate per intero stanno in una sonda
privata (SECURITY.md): questo banco prova la regola, non le elenca.

Ogni caso passa al dispatcher il JSON del PreToolUse nella casa finta di test_aggiramenti_2026_11_21.py e legge
la decisione: nessun comando viene eseguito. Sulla base 0e37768 sono rossi i casi di DISCRIMINANTI.
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_aggiramenti_2026_11_21 import GIT, _fuori_da_claude, casa, decidi  # noqa: E402

SORVEGLIATI = ("hooks/bash-dispatcher.sh", "hooks/block-dangerous.py", "hooks/forma_comando.py")

COMANDI = [
    # --- un nome calcolato quando il comando gira ---
    ("PN01", "$(echo rm) -rf ~/Documents/progetto", "ferma"),
    ("PN02", "P=git; $P push --force origin main", "ferma"),
    ("PN03", "alias q='rm'; q -rf ~/Documents/progetto", "ferma"),
    ("PN04", 'g(){ git "$@"; }; g push --force origin main', "ferma"),
    ("PN05", "$(echo cat) ~/.ssh/id_ed25519", "ferma"),
    # --- xargs ---
    ("PN06", "echo push --force origin main | xargs git", "ferma"),
    # --- un testo eseguito dallo stdin ---
    ("PN07", "printf '%s' 'rm -rf ~/Documents/progetto' | sh", "ferma"),
    ("PN08", "bash <<< 'git push --force origin main'", "ferma"),
    # --- il codice di un interprete ---
    ("PN09", "python3 -c \"import os; os.system('git push --force origin main')\"", "ferma"),
    ("PN10", "node -e \"require('child_process').execSync('rm -rf ~/Documents/progetto')\"", "ferma"),
    ("PN11", "osascript -e 'tell application \"Terminal\" to do script \"rm -rf ~/Documents/progetto\"'", "ferma"),
    # --- vicini che restano muti ---
    ("PN-S1", "curl -s https://x.example/d.json | python3 -c 'import json,sys; print(json.load(sys.stdin))'",
     "silent"),
    ("PN-S2", "python3 - <<'EOF'\ns = open('nota.txt').read().replace('rm -rf', '')\nprint(len(s))\nEOF", "silent"),
    ("PN-S3", "node -e \"const a = []; a.push(1); console.log(a)\"", "silent"),
    ("PN-S4", "C=~/.local/bin/claude; $C rm abc123", "silent"),
    ("PN-S5", "find . -name '*.txt' | xargs wc -l", "silent"),
    ("PN-S6", "perl -e 'select(undef,undef,undef,0.2)'; rm -f nota.txt", "silent"),
    ("PN-S7", "git status && python3 -c 'print(\"rm e push\")'", "silent"),
    ("PN-S8", "P=python3; $P conta.py nota.txt", "silent"),
    ("PN-S9", "printf '%s\\n' a b | sh -c 'cat'", "silent"),
    ("PN-S10", "find . -name '*.md' | xargs grep -n rm", "silent"),
]
CASI = [c[0] for c in COMANDI]
# Già fermi sulla base 0e37768: nessuno. Tutti i casi "ferma" sulla base sono rossi.
INVARIANTI = frozenset()
DISCRIMINANTI = [c[0] for c in COMANDI if c[2] == "ferma" and c[0] not in INVARIANTI]


def prova(repo: Path, vecchi: dict, mostra: bool = False) -> list:
    rossi = []
    with tempfile.TemporaryDirectory(dir=_fuori_da_claude()) as tmp:
        posti = casa(repo, Path(os.path.realpath(tmp)), vecchi)
        for codice, comando, atteso in COMANDI:
            avuto, motivo = decidi(posti["home"], comando)
            classe = "ferma" if avuto in ("ask", "deny", "block") else avuto
            if mostra:
                print(f"{'ok ' if classe == atteso else 'NO '} {codice} {avuto:7} {comando[:80]!r}  [{motivo[:70]}]")
            if classe != atteso:
                rossi.append(f"{codice} {comando[:120]!r}: atteso {atteso}, avuto {avuto} ({motivo[:120]})")
    return rossi


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument("--baseline-ref")
    parser.add_argument("--mostra", action="store_true")
    argomenti = parser.parse_args()
    repo = Path(argomenti.repo)
    for relativo in SORVEGLIATI:
        assert (repo / relativo).is_file(), f"manca {relativo} in {repo}"
    assert len(CASI) == len(set(CASI)) == 21, f"casi doppi o mancanti: {len(CASI)}"
    vecchi = {}
    if argomenti.baseline_ref:
        vecchi = {r: subprocess.run([GIT, "-C", str(repo), "show", f"{argomenti.baseline_ref}:{r}"],
                                    capture_output=True, text=True, encoding="utf-8", check=True).stdout
                  for r in SORVEGLIATI}
    rossi = prova(repo, vecchi, argomenti.mostra)
    if argomenti.baseline_ref:
        codici = [r.split()[0] for r in rossi]
        if argomenti.mostra:
            print("DISCRIMINANTI =", codici)
            return 0
        assert codici == DISCRIMINANTI, f"baseline non discriminante: rossi {codici}, attesi {DISCRIMINANTI}"
        print(f"BASELINE_DISCRIMINANTE={','.join(codici)}")
        return 0
    for r in rossi:
        print("ROSSO", r)
    print(f"programmi nascosti: {len(CASI) - len(rossi)}/{len(CASI)} casi verdi")
    return 1 if rossi else 0


if __name__ == "__main__":
    sys.exit(main())
