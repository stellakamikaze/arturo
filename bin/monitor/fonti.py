#!/usr/bin/env python3
"""fonti.py: le fonti che la persona ha scelto per /monitor, in ~/.claude/data/monitor/fonti.json.

Al primo avvio il file non c'è: /monitor mostra i ponti (`ponti.py`), la persona sceglie, e questo
script scrive la scelta. Accetta solo ponti che esistono e che si possono leggere: un ponte "da
collegare" o "rotto" va prima collegato, e lo script lo dice invece di scriverlo.

  fonti.py mostra                     stampa le fonti scelte; exit 3 se il file manca (primo avvio)
  fonti.py scrivi <ponte>[=giorni]... scrive la scelta: ogni ponte con la sua finestra in giorni
                                      (di serie 7). Se un nome non va, esce con 2 e non scrive niente

fonti.json:
  {"fonti": [{"nome": "task", "finestra": 7}, {"nome": "google-gws", "finestra": 3}],
   "scelte_il": "2026-11-03T21:58"}

Variabili per il banco: le stesse di ponti.py (ARTURO_HOME, GWS_CONFIG_BASE, ARTURO_BIN). Solo
libreria standard, Python 3.8 o successivo.
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ponti  # noqa: E402

FILE = ponti.CASA / "data" / "monitor" / "fonti.json"
LEGGIBILI = {"pronto", "da controllare in sessione"}
FINESTRA = 7


def mostra():
    if not FILE.is_file():
        print("primo avvio: nessuna fonte scelta (manca data/monitor/fonti.json)")
        return 3
    try:
        dati = json.loads(FILE.read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        print(f"ERRORE: fonti.json illeggibile: {e}", file=sys.stderr)
        return 2
    print(json.dumps(dati, ensure_ascii=False, indent=1))
    return 0


def famiglia(nome):
    """La sorgente che un ponte legge: i ponti google-* leggono tutti la stessa Gmail e lo stesso Calendar."""
    return "google" if nome.startswith("google-") else ""


def scrivi(scelte):
    if not scelte:
        print("ERRORE: nessun ponte scelto, niente scritto", file=sys.stderr)
        return 2
    stati = {v["nome"]: v for v in ponti.inventario()}
    fonti, errori = [], []
    for s in scelte:
        nome, _, giorni = s.partition("=")
        v = stati.get(nome)
        if v is None:
            errori.append(f"{nome}: non è un ponte (ponti.py li elenca)")
        elif v["stato"] not in LEGGIBILI:
            errori.append(f"{nome}: è {v['stato']}" + (f", prima {v['passo']}" if v["passo"] else ""))
        elif giorni and (not giorni.isdigit() or not 1 <= int(giorni) <= 90):
            errori.append(f"{nome}: la finestra è un numero di giorni da 1 a 90")
        elif any(f["nome"] == nome for f in fonti):
            errori.append(f"{nome}: scelto due volte")
        elif any(famiglia(f["nome"]) == famiglia(nome) and famiglia(nome) for f in fonti):
            # Due ponti della stessa famiglia leggono la stessa casella: ogni email diventerebbe due todo, con due
            # fingerprint diversi (review del 9/11/2026, lotto L10).
            errori.append(f"{nome}: legge le stesse cose di un ponte già scelto della famiglia {famiglia(nome)}")
        else:
            fonti.append({"nome": nome, "finestra": int(giorni) if giorni else FINESTRA})
    if errori:
        for e in errori:
            print(f"ERRORE: {e}", file=sys.stderr)
        print("niente scritto", file=sys.stderr)
        return 2
    FILE.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(FILE.parent), prefix=".fonti.", suffix=".tmp")
    with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps({"fonti": fonti, "scelte_il": datetime.now().isoformat(timespec="minutes")},
                           ensure_ascii=False, indent=1))
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, str(FILE))
    print("OK: " + ", ".join(f"{f['nome']} ({f['finestra']} giorni)" for f in fonti))
    return 0


def main(argv):
    for flusso in (sys.stdout, sys.stderr):
        if hasattr(flusso, "reconfigure"):
            flusso.reconfigure(encoding="utf-8", errors="replace")
    if argv[:1] == ["mostra"] and len(argv) == 1:
        return mostra()
    if argv[:1] == ["scrivi"]:
        return scrivi(argv[1:])
    print(__doc__, file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
