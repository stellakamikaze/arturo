#!/usr/bin/env python3
"""cursori.py: fin dove /monitor ha letto ogni fonte, in ~/.claude/data/monitor/cursori.json.

Ogni fonte ha il suo cursore. Il cursore avanza solo quando la fonte è stata letta per intero e le
sue cose da fare sono salvate: una fonte che non ha risposto resta indietro, e il giro dopo la
rilegge da dove era rimasta. Le altre fonti non ne risentono.

  cursori.py finestra <fonte> <giorni_base>   i giorni da rileggere per quella fonte:
                                              il più grande fra la base e i giorni dal cursore + 1;
                                              una fonte mai letta vale almeno 7 giorni
  cursori.py avanza --alle AAAA-MM-GGTHH:MM <fonte> [<fonte>...]
                                              porta il cursore all'ora in cui il giro ha cominciato
                                              a leggere. L'ora d'inizio, non quella del salvataggio:
                                              i messaggi arrivati nel frattempo restano nella
                                              finestra del giro dopo
  cursori.py mostra                           stampa i cursori

Il file è solo di Arturo: un /monitor personale con un suo file di stato non lo tocca.
Variabile per il banco: ARTURO_HOME (al posto di ~/.claude). Solo libreria standard, Python 3.8 o
successivo.
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime
from pathlib import Path

CASA = Path(os.environ.get("ARTURO_HOME") or Path.home() / ".claude")
FILE = CASA / "data" / "monitor" / "cursori.json"
MINIMO = 7


def carica():
    try:
        dati = json.loads(FILE.read_text(encoding="utf-8"))
        return dati if isinstance(dati.get("cursori"), dict) else {"cursori": {}}
    except (OSError, ValueError, AttributeError):
        return {"cursori": {}}


def salva(stato):
    FILE.parent.mkdir(parents=True, exist_ok=True)
    tmp = FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(stato, ensure_ascii=False, indent=1), encoding="utf-8")
    os.replace(tmp, FILE)


def finestra(stato, fonte, base, adesso):
    cur = stato["cursori"].get(fonte)
    if not cur:
        return max(base, MINIMO)
    giorni = (adesso.date() - datetime.fromisoformat(cur).date()).days
    return max(base, giorni + 1)


def main(argv):
    for flusso in (sys.stdout, sys.stderr):
        if hasattr(flusso, "reconfigure"):
            flusso.reconfigure(encoding="utf-8", errors="replace")
    stato = carica()
    adesso = datetime.now()
    if argv[:1] == ["mostra"]:
        print(json.dumps(stato, ensure_ascii=False, indent=1))
        return 0
    if len(argv) == 3 and argv[0] == "finestra":
        try:
            base = int(argv[2])
        except ValueError:
            print("ERRORE: i giorni di base sono un numero", file=sys.stderr)
            return 2
        print(finestra(stato, argv[1], base, adesso))
        return 0
    if argv[:1] == ["avanza"]:
        if len(argv) < 4 or argv[1] != "--alle":
            print("ERRORE: avanza vuole --alle AAAA-MM-GGTHH:MM e almeno una fonte, nessun cursore toccato",
                  file=sys.stderr)
            return 2
        try:
            alle = datetime.fromisoformat(argv[2])
        except ValueError:
            print("ERRORE: --alle vuole AAAA-MM-GGTHH:MM, nessun cursore toccato", file=sys.stderr)
            return 2
        if alle > adesso:
            print("ERRORE: --alle nel futuro, nessun cursore toccato", file=sys.stderr)
            return 2
        fonti = argv[3:]
        if any(f.startswith("-") for f in fonti):
            print("ERRORE: un'opzione al posto di una fonte, nessun cursore toccato", file=sys.stderr)
            return 2
        for fonte in fonti:
            stato["cursori"][fonte] = alle.isoformat(timespec="minutes")
        salva(stato)
        print(f"OK: cursore a {alle:%Y-%m-%d %H:%M} per {', '.join(fonti)}")
        return 0
    print(__doc__, file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
