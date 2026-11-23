#!/usr/bin/env python3
"""arturo progetti elimina: un progetto esce dall'elenco e la sua memoria entra in Miscellanea.

Uso: arturo progetti elimina PROGETTO [--prova] [--json]

Nasce da Volta il 22/11/2026 ("Elimina progetto…" nel menu di una tessera di ⌘T). È arturo progetti unisci
PROGETTO miscellanea (bin/unisci.py, che ha le regole di Miscellanea): todo, handoff e scheda passano a
Miscellanea, la scheda del progetto va in _archive/progetti/, la copia di prima in data/progetti/unioni/.
La cartella del codice resta dov'è. Il nome del progetto eliminato resta valido e apre Miscellanea.
--prova stampa l'anteprima e non scrive niente; --json dà l'anteprima o l'esito in JSON, per Volta.
Volta guarda se questo file c'è per mostrare la voce: un Arturo senza le regole di Miscellanea non la mostra.
Exit: quelli di arturo progetti unisci.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

QUI = Path(os.path.realpath(__file__)).parent
sys.path.insert(0, str(QUI))
import unisci  # noqa: E402


def main(argv: list) -> int:
    opzioni = [a for a in argv if a in ("--prova", "--json")]
    nomi = [a for a in argv if a not in ("--prova", "--json")]
    if len(nomi) != 1 or nomi[0].startswith("-"):
        print("uso: arturo progetti elimina PROGETTO [--prova] [--json]", file=sys.stderr)
        return 3
    return unisci.main([nomi[0], unisci.MISCELLANEA, *opzioni])


if __name__ == "__main__":
    for flusso in (sys.stdout, sys.stderr):
        if hasattr(flusso, "reconfigure"):
            flusso.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(main(sys.argv[1:]))
