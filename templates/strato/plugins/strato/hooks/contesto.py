#!/usr/bin/env python3
"""Strato dell'organizzazione: all'avvio della sessione dice a Claude per chi lavora.

Un plugin non puo' portare un CLAUDE.md: le regole sempre attive passano da qui,
come contesto aggiunto all'avvio (massimo 10.000 caratteri, per Claude Code).
Mette insieme:
  - ORGANIZZAZIONE.md: chi siamo, per chi lavoriamo, glossario;
  - l'inizio delle regole di scrittura (le regole intere le carica la skill `voce`);
  - le voci di dati-riservati.txt;
  - un avviso se lo strato non viene aggiornato da piu' di 14 giorni, o se il file
    delle regole sui dati non si legge.

Qualunque errore: esce con 0 e non scrive niente. La sessione si apre lo stesso.
"""
import datetime
import json
import os
import sys
from pathlib import Path

RADICE = Path(os.environ.get("CLAUDE_PLUGIN_ROOT") or Path(__file__).resolve().parent.parent)
TETTO = 9000  # sotto i 10.000 caratteri di Claude Code, con margine
GIORNI_VECCHIO = 14


def leggi(nome, massimo):
    try:
        testo = (RADICE / nome).read_text(encoding="utf-8").strip()
    except Exception:
        return None
    return testo if len(testo) <= massimo else testo[:massimo].rstrip() + "\n[…continua nel file]"


def voci_riservate():
    try:
        testo = (RADICE / "dati-riservati.txt").read_text(encoding="utf-8")
    except Exception:
        return None
    return [r.split("#", 1)[0].strip() for r in testo.splitlines() if r.split("#", 1)[0].strip()]


def giorni_da_pubblicazione():
    try:
        data = (RADICE / ".ultima-pubblicazione").read_text(encoding="utf-8").strip()[:10]
        return (datetime.date.today() - datetime.date.fromisoformat(data)).days
    except Exception:
        return None


def contesto():
    nome = RADICE.name
    try:
        nome = json.loads((RADICE / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8")).get("name") or nome
    except Exception:
        pass
    parti = [f"STRATO DELL'ORGANIZZAZIONE ATTIVO: {nome}."]
    organizzazione = leggi("ORGANIZZAZIONE.md", 4000)
    if organizzazione:
        parti.append(organizzazione)
    regole = leggi("skills/voce/regole.md", 2500)
    if regole:
        parti.append("Regole di scrittura (estratto; per un testo dell'organizzazione usa la skill "
                     f"`{nome}:voce`, che le carica intere):\n" + regole)
    voci = voci_riservate()
    if voci is None:
        parti.append("ATTENZIONE: il file delle regole sui dati dello strato non si legge. "
                     "Dillo all'utente: il referente deve sistemarlo nel repository.")
    elif voci:
        parti.append("Dati che non escono dal computer senza una conferma: " + ", ".join(voci[:60]) + ".")
    giorni = giorni_da_pubblicazione()
    if giorni is not None and giorni > GIORNI_VECCHIO:
        parti.append(f"Lo strato installato e' stato pubblicato {giorni} giorni fa. Se il referente "
                     "ha pubblicato qualcosa di nuovo, `/aggiorna` lo scarica: suggeriscilo all'utente "
                     "una volta, senza insistere.")
    testo = "\n\n".join(parti)
    return testo if len(testo) <= TETTO else testo[:TETTO].rstrip() + "\n[…troncato]"


def main():
    try:
        testo = contesto()
        print(json.dumps({"hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": testo,
        }}, ensure_ascii=False))
    except Exception:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
