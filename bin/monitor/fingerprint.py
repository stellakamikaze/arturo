#!/usr/bin/env python3
"""fingerprint.py: la stringa che riconosce una cosa da fare fra un giro e l'altro di /monitor.

Lo stesso messaggio letto due volte deve dare la stessa stringa, e quindi lo stesso hash: così il
secondo giro sa che la cosa c'è già e non crea un doppione. Per questo la stringa nasce solo da ID
stabili della fonte (l'ID del thread, del file, del todo, una data), mai dal testo del riassunto,
che il modello riscrive ogni volta in modo diverso.

Forma: `<fonte>:<id>[:<id>...]`.
  - `<fonte>` è il nome del ponte: lettere minuscole, cifre e trattini, per esempio `email`, `task`,
    `sessioni` o il nome di un ponte personale.
  - ogni `<id>` è un pezzo senza spazi. Una stringa con spazi è testo libero e si rifiuta.
  - in tutto al massimo 300 caratteri.
Se una riga non porta `fp`, vale `<fonte>:<id_sorgente>` (righe.py).

Hash: i primi 8 caratteri dell'md5 della stringa, come `printf %s S | md5sum | cut -c1-8`.

  fingerprint.py "email:1a0f7a23d0379a35"   stampa `hash<TAB>stringa`, exit 0
  fingerprint.py "testo libero"             motivo su stderr, exit 2

Solo libreria standard, Python 3.8 o successivo.
"""
from __future__ import annotations

import hashlib
import re
import sys

FORMA = re.compile(r"^[a-z][a-z0-9-]{0,39}(?::[^\s:]+)+$")
MASSIMO = 300


def valida(s):
    """(True, fonte) se la stringa è un fingerprint valido, altrimenti (False, motivo)."""
    s = (s or "").strip()
    if not s:
        return False, "stringa vuota"
    if len(s) > MASSIMO:
        return False, f"più di {MASSIMO} caratteri: servono ID, non testo"
    if re.search(r"\s", s):
        return False, "contiene spazi: è testo libero, servono ID stabili della fonte"
    if not FORMA.match(s):
        return False, "forma non valida: serve <fonte>:<id>, con la fonte in minuscolo e nessun pezzo vuoto"
    return True, s.split(":", 1)[0]


def hash_di(s):
    return hashlib.md5(s.strip().encode("utf-8")).hexdigest()[:8]


def main(argv):
    for flusso in (sys.stdout, sys.stderr):
        if hasattr(flusso, "reconfigure"):
            flusso.reconfigure(encoding="utf-8", errors="replace")
    if len(argv) != 1:
        print(__doc__, file=sys.stderr)
        return 2
    valido, motivo = valida(argv[0])
    if not valido:
        print(f"ERRORE: {motivo}", file=sys.stderr)
        return 2
    print(f"{hash_di(argv[0])}\t{argv[0].strip()}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
