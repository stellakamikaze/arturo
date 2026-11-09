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
import tempfile
from datetime import datetime
from pathlib import Path
sys.path.append(str(Path(os.path.realpath(__file__)).parents[2] / "hooks"))
from radici import radice_orsa  # noqa: E402

CASA = Path(os.environ.get("ARTURO_HOME") or radice_orsa())
FILE = CASA / "data" / "monitor" / "cursori.json"
MINIMO = 7


def carica():
    """Lo stato dei cursori; None se il file c'è ma non si legge: riscriverlo perderebbe i cursori delle altre
    fonti, che tornerebbero a 7 giorni (review del 9/11/2026, lotto L10)."""
    if not FILE.exists():
        return {"cursori": {}}
    try:
        dati = json.loads(FILE.read_text(encoding="utf-8"))
        return dati if isinstance(dati, dict) and isinstance(dati.get("cursori"), dict) else None
    except (OSError, ValueError):
        return None


def salva(stato):
    FILE.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(FILE.parent), prefix=".cursori.", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
            f.write(json.dumps(stato, ensure_ascii=False, indent=1))
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, str(FILE))
    except BaseException:
        Path(tmp).unlink(missing_ok=True)
        raise


def finestra(stato, fonte, base, adesso):
    cur = stato["cursori"].get(fonte)
    try:
        giorno = datetime.fromisoformat(cur).date() if isinstance(cur, str) and cur else None
    except ValueError:
        giorno = None  # un cursore che non è una data vale come mai letto: la finestra larga, non un errore
    if giorno is None:
        return max(base, MINIMO)
    return max(base, (adesso.date() - giorno).days + 1)


def main(argv):
    for flusso in (sys.stdout, sys.stderr):
        if hasattr(flusso, "reconfigure"):
            flusso.reconfigure(encoding="utf-8", errors="replace")
    stato = carica()
    if stato is None:
        print(f"ERRORE: {FILE} non si legge: correggilo o spostalo, nessun cursore letto o toccato", file=sys.stderr)
        return 2
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
            if alle.tzinfo is not None:
                raise ValueError("fuso orario")  # i cursori sono ore locali senza fuso
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
