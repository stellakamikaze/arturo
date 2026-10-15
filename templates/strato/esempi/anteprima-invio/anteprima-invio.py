#!/usr/bin/env python3
"""ESEMPIO DA ADATTARE. Anteprima prima di un invio email da uno strumento MCP.

Prima che Claude mandi un'email con un connettore (send, reply, forward), l'hook mostra alla
persona destinatari, oggetto e i controlli dell'organizzazione, e chiede conferma. Non blocca mai
da solo: la decisione resta alla persona.

Le regole dell'organizzazione stanno in `regole-invio.txt`, nella cartella dello strato. Il codice
non contiene indirizzi, nomi o parole dell'organizzazione: per cambiare una regola si cambia il
file e si pubblica lo strato.

Gli invii da riga di comando (gws, sendmail, smtplib) li ferma gia' la guardia comms-guard di
Arturo. Se qualcosa va storto, l'hook lascia passare: l'invio arriva comunque alla conferma
normale di Claude Code.
"""
import json
import os
import re
import sys
from pathlib import Path

RADICE = Path(os.environ.get("CLAUDE_PLUGIN_ROOT") or Path(__file__).resolve().parent.parent)
INVIO = re.compile(r"send|reply|forward", re.IGNORECASE)
# Accenti scritti con l'apostrofo: «perche'», «puo'». Vale per ogni testo in italiano.
APOSTROFO = re.compile(r"\b(perche|poiche|e|puo|piu|gia|cosi|cioe|citta|sara|fara)['’](?=[\s.,;:!?]|$)", re.IGNORECASE)
CIFRA = re.compile(r"€\s?\d|\d[\d.,]*\s?(€|euro\b)", re.IGNORECASE)


def regole(percorso):
    """Le regole del file: lista di (tipo, valore). Una riga «tipo: valore», # per i commenti."""
    voci = []
    for riga in percorso.read_text(encoding="utf-8").splitlines():
        riga = riga.split("#", 1)[0].strip()
        if ":" not in riga:
            continue
        tipo, valore = riga.split(":", 1)
        voci.append((tipo.strip().lower(), valore.strip()))
    return voci


def lista(valore):
    if isinstance(valore, list):
        return [str(x) for x in valore]
    if isinstance(valore, str):
        return [x.strip() for x in valore.split(",") if x.strip()]
    return []


def email(ingresso):
    corpo = ingresso.get("body") or ingresso.get("text") or ingresso.get("content") or ""
    if not corpo and isinstance(ingresso.get("htmlBody"), str):
        corpo = re.sub(r"<[^>]+>", " ", ingresso["htmlBody"])
    thread = ingresso.get("replyThreadId") or ingresso.get("threadId") or ingresso.get("messageId")
    return {
        "a": lista(ingresso.get("to")),
        "cc": lista(ingresso.get("cc")),
        "oggetto": str(ingresso.get("subject") or ""),
        "corpo": str(corpo),
        "thread": thread is not None,
    }


def controlli(m, voci):
    avvisi = []
    tutti = [x.lower() for x in m["a"] + m["cc"]]
    if not m["a"] and not m["thread"]:
        avvisi.append("nessun destinatario leggibile")
    for tipo, valore in voci:
        if tipo == "copia" and not any(valore.lower() in x for x in tutti):
            avvisi.append(f"manca in copia: {valore}")
        elif tipo == "oggetto-nuovo" and not m["thread"] and not m["oggetto"].startswith(valore):
            avvisi.append(f"oggetto senza «{valore}»")
        elif tipo == "parola":
            parola, _, consiglio = valore.partition("=>")
            parola = parola.strip()
            if parola and re.search(r"\b" + re.escape(parola) + r"\b", m["corpo"]):
                avvisi.append(f"«{parola}» nel testo" + (f": {consiglio.strip()}" if consiglio.strip() else ""))
        elif tipo == "cifre-nel-corpo" and valore.lower() == "no" and CIFRA.search(m["corpo"]):
            avvisi.append("una cifra nel corpo dell'email")
    accenti = sorted({x.group(0) for x in APOSTROFO.finditer(m["corpo"])})
    if accenti:
        avvisi.append("accenti con l'apostrofo: " + " ".join(accenti[:4]))
    return avvisi


def riepilogo(m, avvisi):
    righe = [
        "Anteprima dell'invio",
        "A: " + (", ".join(m["a"]) or "-") + (" · Cc: " + ", ".join(m["cc"]) if m["cc"] else ""),
        "Oggetto: " + (m["oggetto"] or "-") + (" (nel thread)" if m["thread"] else ""),
        "Controlli: tutto in regola." if not avvisi else "Controlli: " + " · ".join(avvisi),
    ]
    return "\n".join(righe)


def main():
    try:
        dati = json.load(sys.stdin)
        strumento = dati.get("tool_name") or ""
        if not strumento.startswith("mcp__") or not INVIO.search(strumento.rsplit("__", 1)[-1]):
            return 0
        ingresso = dati.get("tool_input") or {}
        # Solo le email: un messaggio in chat non ha destinatari né oggetto.
        if not any(k in ingresso for k in ("to", "subject", "replyThreadId", "messageId")):
            return 0
        m = email(ingresso)
        try:
            voci = regole(RADICE / "regole-invio.txt")
        except OSError:
            voci = []
        avvisi = controlli(m, voci)
        print(json.dumps({"hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "ask",
            "permissionDecisionReason": riepilogo(m, avvisi),
        }}, ensure_ascii=False))
    except Exception:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
