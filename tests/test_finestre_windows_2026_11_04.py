#!/usr/bin/env python3
"""FW01-FW02: su Windows i lanci staccati non aprono finestre di terminale (4/11/2026).

Su Balthasar si aprivano di continuo finestre di Windows Terminal intitolate git.exe. Causa:
aggiornamenti.py e telemetria.py si staccavano con DETACHED_PROCESS, cioè senza console, e ogni
programma a console lanciato da lì (git, bash, gws) ne apriva una nuova e visibile. gws-esito.py e
gws-token-health.py univano DETACHED_PROCESS e CREATE_NO_WINDOW: Windows ignora CREATE_NO_WINDOW
quando c'è DETACHED_PROCESS. Provato il 4/11/2026: col vecchio flag un git figlio apre la finestra
"C:\\Program Files\\Git\\mingw64\\bin\\git.exe", con CREATE_NO_WINDOW | CREATE_NEW_PROCESS_GROUP no.

FW01 nessun file Python di bin/ e hooks/ passa DETACHED_PROCESS (0x00000008) a creationflags.
FW02 invariante: i quattro lanci staccati su Windows restano in un gruppo nuovo e senza finestra
     (CREATE_NEW_PROCESS_GROUP 0x00000200 e CREATE_NO_WINDOW 0x08000000).

Sulla base efaa296 (dev prima della correzione) sono rossi FW01 e FW02.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

CASI = ["FW01", "FW02"]
DISCRIMINANTI = ["FW01", "FW02"]
LANCI = ["bin/aggiornamenti.py", "bin/telemetria.py", "hooks/gws-esito.py", "hooks/gws-token-health.py"]
FLAG = re.compile(r"creationflags[\"']?\]?\s*[=:]\s*([^#\n]+)")


def _flag(riga: str) -> str:
    m = FLAG.search(riga)
    return m.group(1) if m else ""


def prova(repo: Path) -> list:
    rossi = []
    staccati = []
    for cartella in ("bin", "hooks"):
        for f in sorted((repo / cartella).glob("*.py")):
            for n, riga in enumerate(f.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
                valore = _flag(riga)
                if re.search(r"0x0*8\b|DETACHED_PROCESS", valore):
                    staccati.append(f"{cartella}/{f.name}:{n}")
    if staccati:
        rossi.append(f"FW01 DETACHED_PROCESS apre una finestra per ogni git figlio: {staccati}")

    mancano = []
    for rel in LANCI:
        f = repo / rel
        testo = f.read_text(encoding="utf-8", errors="replace") if f.exists() else ""
        valori = [_flag(r) for r in testo.splitlines() if _flag(r)]
        if not any(re.search(r"0x0*8000000\b", v) and re.search(r"0x0*200\b", v) for v in valori):
            mancano.append(rel)
    if mancano:
        rossi.append(f"FW02 lancio staccato senza CREATE_NO_WINDOW | CREATE_NEW_PROCESS_GROUP: {mancano}")
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
    print(f"finestre di Windows: {len(CASI) - len(rossi)}/{len(CASI)} casi verdi")
    return 1 if rossi else 0


if __name__ == "__main__":
    sys.exit(main())
