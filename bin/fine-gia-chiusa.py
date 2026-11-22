#!/usr/bin/env python3
"""Ferma un /fine che arriva su una sessione già chiusa, prima che parta un turno del modello (22/11/2026, #6274).

Segnalazioni n. 79, 87 e 93: un mod della persona (chiusura-automatica) rilancia /fine ogni 45 minuti su una
sessione ferma. Ogni giro carica /fine nel contesto, trova git pulito e niente da salvare, e consuma quota.
Il mod non è di Arturo: qui Arturo ferma il giro da solo, qualunque cosa lo mandi.

Lo lancia hooks/inject-now.sh (UserPromptSubmit) col JSON dell'hook su stdin, solo per un prompt /fine o
/arturo:fine. Esce 2 con una riga su stderr, e Claude Code scarta il prompt senza chiamare il modello, solo se:
  1. il prompt è /fine senza --forza o --full, e non comincia con salva (/fine salva risponde alla domanda di
     un /fine) né con il congedo di Volta, che ha già il suo controllo;
  2. la trascrizione della sessione ha già un /fine, e dopo l'ultimo /fine non c'è nessun altro messaggio:
     né della persona, né di un'altra sessione, né di un lavoro in background. Le righe meta (corpo della
     skill, uscita dei comandi locali) e i risultati dei tool non contano;
  3. un handoff con la riga "- Sessione: <id>" e senza "- Salvato: in automatico" è stato scritto dopo
     quell'ultimo /fine.
In ogni altro caso, e a ogni errore (trascrizione illeggibile, JSON rotto), esce 0 e il /fine parte.

Uso: python3 bin/fine-gia-chiusa.py < evento-hook.json
"""
from __future__ import annotations

import json
import re
import sys
import time
from datetime import datetime
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent / "hooks"))
from radici import radice_orsa  # noqa: E402

PROMPT_FINE = re.compile(r"\s*/(?:arturo:)?fine(?:\s+(.*))?\s*\Z", re.S)
COMANDO_FINE = re.compile(r"<command-name>/(?:arturo:)?fine</command-name>")
SBLOCCO = ("--forza", "--full")
# Il congedo di Volta ha già il suo controllo (fineFatta in sessioni.js): dopo il congedo Volta aspetta che il
# turno di /fine finisca per fermare la sessione, e un prompt scartato lo lascerebbe ad aspettare.
VOLTA = "congedo da Volta"
MARCA_AUTO = "- Salvato: in automatico"
# I messaggi di un'altra sessione arrivano come meta, ma Claude ci lavora sopra: contano come attività.
ATTIVITA = ("peer", "task-notification")


def secondi(ts) -> float | None:
    """Il timestamp ISO della trascrizione (2026-11-20T17:26:03.120Z) in secondi epoch."""
    if not isinstance(ts, str) or not ts:
        return None
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00")).timestamp()
    except ValueError:
        return None


def testo(contenuto) -> str | None:
    """Il testo di un messaggio utente; None per un risultato di tool."""
    if isinstance(contenuto, str):
        return contenuto
    if isinstance(contenuto, list):
        if any(isinstance(b, dict) and b.get("type") == "tool_result" for b in contenuto):
            return None
        return "\n".join(b.get("text", "") for b in contenuto if isinstance(b, dict) and b.get("type") == "text")
    return None


def ultimo_fine_da_solo(trascrizione: Path) -> float | None:
    """L'ora dell'ultimo /fine, se dopo non è arrivato nessun messaggio; altrimenti None."""
    ultimo = None
    with trascrizione.open(encoding="utf-8", errors="replace") as righe:
        for riga in righe:
            if '"user"' not in riga:
                continue
            try:
                e = json.loads(riga)
            except ValueError:
                continue
            if not isinstance(e, dict) or e.get("type") != "user":
                continue
            origine = e.get("origin")
            if isinstance(origine, dict) and origine.get("kind") in ATTIVITA:
                ultimo = None   # un'altra sessione o un lavoro finito: Claude può aver fatto qualcosa
                continue
            if e.get("isMeta") or e.get("isSidechain") or e.get("isCompactSummary"):
                continue
            t = testo((e.get("message") or {}).get("content"))
            if t is None:
                continue
            if COMANDO_FINE.search(t) or PROMPT_FINE.match(t):
                ultimo = secondi(e.get("timestamp"))
            else:
                ultimo = None   # un messaggio dopo il /fine: la sessione ha di nuovo qualcosa da salvare
    return ultimo


def handoff_dopo(sid: str, dopo: float) -> Path | None:
    """Un handoff di questa sessione scritto dopo `dopo`, che non sia un salvataggio automatico."""
    riga = re.compile(rf"(?m)^- Sessione: {re.escape(sid)}\s*$")
    for f in (radice_orsa() / "data" / "handoffs").glob("*/HANDOFF_*.md"):
        try:
            if f.stat().st_mtime < dopo:
                continue
            corpo = f.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if riga.search(corpo) and MARCA_AUTO not in corpo.splitlines():
            return f
    return None


def da_fermare(dati: dict) -> Path | None:
    """L'handoff che chiude già la sessione, se il /fine va fermato; altrimenti None."""
    prompt = dati.get("prompt")
    if not isinstance(prompt, str):
        return None
    m = PROMPT_FINE.match(prompt)
    if not m:
        return None
    parole = (m.group(1) or "").split()
    if any(p in SBLOCCO for p in parole) or parole[:1] == ["salva"]:
        return None
    if (m.group(1) or "").lstrip().startswith(VOLTA):
        return None
    sid, percorso = dati.get("session_id"), dati.get("transcript_path")
    if not isinstance(sid, str) or not sid.strip() or not isinstance(percorso, str) or not percorso:
        return None
    trascrizione = Path(percorso)
    if not trascrizione.is_file():
        return None
    quando = ultimo_fine_da_solo(trascrizione)
    if quando is None:
        return None
    return handoff_dopo(sid.strip(), quando)


def main() -> int:
    for flusso in (sys.stdout, sys.stderr):  # su Windows la pipe è in cp1252, Claude Code legge UTF-8
        if hasattr(flusso, "reconfigure"):
            flusso.reconfigure(encoding="utf-8", errors="replace")
    try:
        dati = json.loads(sys.stdin.buffer.read().decode("utf-8", errors="replace"))
        handoff = da_fermare(dati) if isinstance(dati, dict) else None
    except Exception:
        return 0   # nel dubbio il /fine parte: fermarlo per un errore nostro costa più di un giro in più
    if handoff is None:
        return 0
    ora = time.strftime("%H:%M", time.localtime(handoff.stat().st_mtime))
    sys.stderr.write(
        f"/fine saltato: la sessione è già chiusa con l'handoff delle {ora} ({handoff.parent.name}/{handoff.name}),"
        " e dopo non è arrivato nessun messaggio. Per rifarlo comunque scrivi /fine --forza.\n")
    return 2


if __name__ == "__main__":
    sys.exit(main())
