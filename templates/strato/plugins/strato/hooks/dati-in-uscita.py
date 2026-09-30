#!/usr/bin/env python3
"""Strato dell'organizzazione: chiede conferma quando un dato riservato sta per uscire.

Guarda solo cio' che esce dal computer: un comando che manda dati in rete, una
pagina web richiesta con un indirizzo che contiene il dato, uno strumento MCP che
invia, pubblica o condivide. Non guarda Write ed Edit: il lavoro quotidiano tocca
clienti e progetti, e una domanda a ogni file insegnerebbe a dire si' senza leggere.

Le voci stanno in `dati-riservati.txt`, accanto a questa cartella: una per riga,
`#` per i commenti. Le cura il referente nel repository dell'organizzazione.

Se il file non si legge, o qualcosa va storto, l'hook lascia passare: un collega
non deve restare bloccato da un file rotto. L'avviso arriva all'avvio della
sessione da contesto.py.
"""
import json
import os
import re
import sys
from pathlib import Path

RADICE = Path(os.environ.get("CLAUDE_PLUGIN_ROOT") or Path(__file__).resolve().parent.parent)

# Comandi che mandano dati fuori: invio HTTP con un corpo, upload, copie verso un
# altro computer, canali grezzi, push.
USCITA_BASH = re.compile(
    r"\b(curl|wget)\b[^|;&]*(\s-d\b|\s--data|\s-F\b|\s--form|\s-T\b|\s--upload-file|\s-X\s*(POST|PUT|PATCH)|\s--request\s*(POST|PUT|PATCH))"
    r"|requests\.(post|put|patch)|urllib\.request|httpx\.(post|put|patch)|smtplib"
    r"|\bscp\b|\brsync\b[^|;&]*\S+:|\b(nc|ncat|socat)\b|\bgit\b[^|;&]*\bpush\b"
    r"|\bgws\b[^|;&]*(\bsend\b|\+send|\bcreate\b|\bupload\b|\bshare\b)",
    re.IGNORECASE,
)
# Strumenti MCP che mandano qualcosa a qualcuno o fuori.
USCITA_MCP = re.compile(r"send|reply|forward|post|publish|share|upload|create|update|write|message|comment|invite", re.IGNORECASE)


def voci_riservate():
    """Le voci del file, in minuscolo. None se il file non si legge."""
    try:
        testo = (RADICE / "dati-riservati.txt").read_text(encoding="utf-8")
    except Exception:
        return None
    voci = []
    for riga in testo.splitlines():
        riga = riga.split("#", 1)[0].strip()
        if riga:
            voci.append(riga.lower())
    return voci


def trova(testo, voci):
    basso = testo.lower()
    for voce in voci:
        if re.fullmatch(r"[\w.-]+", voce):
            # Una parola o un dominio: deve comparire intera, non dentro un'altra parola.
            if re.search(r"(?<![\w.-])" + re.escape(voce) + r"(?![\w-])", basso):
                return voce
        elif voce in basso:
            return voce
    return None


def testo_in_uscita(dati):
    strumento = dati.get("tool_name") or ""
    ingresso = dati.get("tool_input") or {}
    if strumento == "Bash":
        comando = ingresso.get("command") or ""
        return comando if USCITA_BASH.search(comando) else None
    if strumento == "WebFetch":
        return ingresso.get("url") or ""
    if strumento.startswith("mcp__") and USCITA_MCP.search(strumento.rsplit("__", 1)[-1]):
        return json.dumps(ingresso, ensure_ascii=False)
    return None


def main():
    try:
        dati = json.load(sys.stdin)
        testo = testo_in_uscita(dati)
        if not testo:
            return 0
        voci = voci_riservate()
        if not voci:
            return 0
        voce = trova(testo, voci)
        if not voce:
            return 0
        print(json.dumps({"hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "ask",
            "permissionDecisionReason": (
                f"Sta per uscire dal computer qualcosa che l'organizzazione tiene riservato "
                f"(«{voce}», dalle regole sui dati dello strato). Conferma solo se questo "
                "invio e' previsto."
            ),
        }}))
        return 0
    except Exception:
        return 0


if __name__ == "__main__":
    sys.exit(main())
