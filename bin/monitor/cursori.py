#!/usr/bin/env python3
"""Cursori per fonte di /monitor (lotto 3, 3/10/2026): ~/.claude/data/monitor/stato.json.

Prima i file di stato valevano tutto o niente: una run con una fonte bucata o non
aggiornava `last_run.txt` (e rileggeva tutte le fonti), o lo aggiornava (e il buco non si
recuperava più). Adesso ogni fonte ha il suo cursore, che avanza solo quando la fonte è
stata letta per intero e i suoi item sono salvati o in coda.

  cursori.py finestra <fonte> <giorni_base>   stampa i giorni della finestra di quella fonte:
                                              max(base, giorni dal suo cursore + 1)
  cursori.py avanza [--alle YYYY-MM-DDTHH:MM] <fonte> [<fonte>...]
                                              porta il cursore all'ora di lettura (solo fonti
                                              "letta"). /monitor passa sempre --alle con l'ora
                                              d'inizio della run: senza, vale adesso, e i
                                              messaggi arrivati fra lettura e salvataggio si
                                              perdono (23/10/2026: lettura 18:17, salvataggio
                                              00:44, #3866)
  cursori.py mostra                           stampa lo stato
  cursori.py slack-canali [c1,c2,...]         legge o scrive i canali di progetto letti
                                              l'ultima volta (rotazione dello scanner Slack)
"""
import json
import os
import sys
from datetime import datetime

STATO = os.path.expanduser(os.environ.get("MONITOR_STATO", "~/.claude/data/monitor/stato.json"))


def carica():
    try:
        with open(STATO, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {"cursori": {}, "slack_canali": []}


def salva(stato):
    os.makedirs(os.path.dirname(STATO), exist_ok=True)
    tmp = STATO + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(stato, f, ensure_ascii=False, indent=1)
    os.replace(tmp, STATO)


def finestra(stato, fonte, base, adesso):
    cur = stato.get("cursori", {}).get(fonte)
    if not cur:
        return max(base, 7)          # fonte mai letta col cursore: una settimana
    giorni = (adesso.date() - datetime.fromisoformat(cur).date()).days
    return max(base, giorni + 1)


def main(argv):
    stato = carica()
    adesso = datetime.now()
    if len(argv) >= 2 and argv[1] == "mostra":
        print(json.dumps(stato, ensure_ascii=False, indent=1))
        return 0
    if len(argv) == 4 and argv[1] == "finestra":
        print(finestra(stato, argv[2], int(argv[3]), adesso))
        return 0
    if len(argv) >= 3 and argv[1] == "avanza":
        fonti, alle = argv[2:], adesso
        if fonti[0] == "--alle":
            try:
                alle = datetime.fromisoformat(fonti[1])
            except (IndexError, ValueError):
                print("ERROR: --alle vuole YYYY-MM-DDTHH:MM, nessun cursore toccato", file=sys.stderr)
                return 2
            fonti = fonti[2:]
            if alle > adesso:
                print("ERROR: --alle nel futuro, nessun cursore toccato", file=sys.stderr)
                return 2
        if not fonti or any(f.startswith("-") for f in fonti):
            print("ERROR: nessuna fonte, o un'opzione al posto di una fonte", file=sys.stderr)
            return 2
        for fonte in fonti:
            stato.setdefault("cursori", {})[fonte] = alle.isoformat(timespec="minutes")
        salva(stato)
        print(f"OK: cursore a {alle:%Y-%m-%d %H:%M} per {', '.join(fonti)}")
        return 0
    if len(argv) in (2, 3) and argv[1] == "slack-canali":
        if len(argv) == 3:
            stato["slack_canali"] = [c.strip() for c in argv[2].split(",") if c.strip()]
            salva(stato)
        print(",".join(stato.get("slack_canali", [])))
        return 0
    print(__doc__, file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
