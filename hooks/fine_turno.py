"""Il testo con cui Claude chiude il turno, e se chiede qualcosa alla persona (24/11/2026).

Lo usano due hook di Stop: carta-sessione.py (la carta per la Coda di Volta) e continua.py (la sessione
va avanti da sola quando il passo dopo è di Claude). Prima stava solo in carta-sessione.py.

  testo_del_turno(dati)  l'ultimo testo di Claude: last_assistant_message dell'evento Stop, oppure, se manca,
                         l'ultimo messaggio assistant con testo nella trascrizione (transcript_path).
  ultimo_testo(percorso) l'ultimo testo di Claude nella trascrizione, letto dal fondo (CODA byte).
  chiede(testo)          vero se la fine del testo chiede qualcosa alla persona: le stesse regole di
                         chiede() in sessioni.js di Volta.

Solo libreria standard, Python 3.8+.
"""
from __future__ import annotations

import json
import os
import re

CODA = 3000000       # byte della trascrizione letti dal fondo, come la sonda di Volta

# Le stesse regole di chiede() in arturo/mods/arturo/sessioni.js di Volta: se cambiano là, cambiano qui
# (CS01 di tests/test_carta_sessione.py le confronta con node quando c'è).
CHIEDE = [
    re.compile(r"\?[\s*_`)]*$"),
    re.compile(r"\?\s*\n"),
    re.compile(r"^\s*!\s*\S", re.M),
    re.compile(r"\b(scrivimi|scrivi|dimmi|dimmelo|rispondi|rispondimi|fammi sapere|conferma|confermi|scegli|decidi|lancia|tocca a te|serve il tuo|il tuo s[iì]|aspetto la tua|attendo la tua)\b", re.I),
    re.compile(r"prossimo passo:[^\n]*(\btu\b|\btuo\b|\btua\b|\(tu\))", re.I),
]


def chiede(testo: str) -> bool:
    c = str(testo or "")[-220:]
    return any(r.search(c) for r in CHIEDE)


def testo_di(contenuto) -> str:
    if isinstance(contenuto, str):
        return contenuto
    if isinstance(contenuto, list):
        return "\n".join(b.get("text", "") for b in contenuto if isinstance(b, dict) and b.get("type") == "text")
    return ""


def ultimo_testo(trascrizione: str) -> str:
    """L'ultimo testo di Claude nella trascrizione (solo i blocchi di testo, non gli strumenti)."""
    try:
        with open(trascrizione, "rb") as fh:
            fh.seek(0, os.SEEK_END)
            lungo = fh.tell()
            fh.seek(max(0, lungo - CODA))
            dati = fh.read().decode("utf-8", "replace")
    except OSError:
        return ""
    ultimo = ""
    for r in dati.splitlines():
        try:
            d = json.loads(r)
        except ValueError:
            continue
        if not isinstance(d, dict) or d.get("type") != "assistant":
            continue
        t = testo_di((d.get("message") or {}).get("content"))
        if t.strip():
            ultimo = t
    return ultimo


def testo_del_turno(dati: dict) -> str:
    """L'ultimo testo di Claude per un evento Stop: il campo dell'evento, o la trascrizione se manca."""
    return str(dati.get("last_assistant_message") or "") or ultimo_testo(str(dati.get("transcript_path") or ""))
