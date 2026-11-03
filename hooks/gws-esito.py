#!/usr/bin/env python3
"""gws: la sintassi di Gmail prima del comando, le credenziali mancanti dopo.

Fino al 3/11/2026 lo faceva il mod skills/gws, che cambiava il comando prima di eseguirlo. In
modalità auto un comando cambiato dopo la revisione del classificatore viene respinto e va
rilanciato identico (segnalazioni n. 46-48): un hook che nega e spiega non cambia niente.

PreToolUse(Bash)            `gws gmail messages …` non esiste: nega e scrive la forma con `users`.
PostToolUse(Bash)           un gws che esce 0 ma dice "invalid_grant" o "No credentials provided".
PostToolUseFailure(Bash)    lo stesso guasto con un codice d'uscita diverso da 0 (il caso comune).
  Dopo il guasto: un avviso alla persona (systemMessage), una nota a Claude che dice di fermarsi e
  chiedere il login, e il controllo dei token di gws-token-health.py rifatto subito, così l'avviso
  di avvio e la riga sotto il prompt non aspettano le 6 ore della cache.

Mai bloccante dopo il comando: qualunque errore esce 0 in silenzio.
"""
from __future__ import annotations

import json
import os
import platform
import re
import subprocess
import sys
from pathlib import Path
from typing import Optional

# gws in posizione di comando: "echo gws …" o un grep su gws non contano.
GWS = re.compile(r"(?:^|[;&|\n(])\s*(?:[A-Za-z_]+=\S+\s+)*gws\s")
# `gws gmail messages …` non esiste: le risorse di Gmail stanno sotto `users`.
GMAIL = re.compile(r"((?:^|[;&|\n(])\s*(?:[A-Za-z_]+=\S+\s+)*gws\s+gmail\s+)(messages|threads|drafts|labels|history)\b")
# Credenziali mancanti o revocate. Un 403 di scope non è qui: lì il token c'è e manca un permesso.
GUASTI = ("No credentials provided", "invalid_grant", "undecryptable")
CONFIG_DIR = re.compile(r"GOOGLE_WORKSPACE_CLI_CONFIG_DIR=([\"']?)([^\s\"';]+)\1")


def corretto(cmd: str) -> str:
    return GMAIL.sub(r"\1users \2", cmd)


def guasto(testo: str) -> Optional[str]:
    return next((g for g in GUASTI if g in testo), None)


def account(cmd: str) -> tuple[str, str]:
    """Nome e cartella dell'account: quella del comando, poi quella della sessione, poi il default di gws."""
    m = CONFIG_DIR.search(cmd)
    cartella = (m.group(2) if m else os.environ.get("GOOGLE_WORKSPACE_CLI_CONFIG_DIR", "")).strip() or "~/.config/gws"
    nome = re.split(r"[\\/]", cartella.rstrip("/\\"))[-1] or "gws"
    return nome, cartella


def nota(nome: str, cartella: str) -> str:
    macchina = platform.node().split(".")[0] or "questo computer"
    return (f"[gws] L'account {nome} non ha credenziali valide su {macchina}. "
            "Non riprovare con un altro account e non cambiare comando. "
            f"Serve che la persona rifaccia il login: GOOGLE_WORKSPACE_CLI_CONFIG_DIR={cartella} gws auth login "
            "(la guida è in ~/.claude/docs/onboarding/gws.md). Diglielo e fermati su gws.")


def rifai_controllo() -> None:
    """Il controllo dei token gira staccato: l'hook risponde subito, la cache si riscrive dopo."""
    script = Path(__file__).resolve().with_name("gws-token-health.py")
    if not script.is_file():
        return
    kw: dict = {"stdin": subprocess.DEVNULL, "stdout": subprocess.DEVNULL, "stderr": subprocess.DEVNULL}
    if sys.platform == "win32":
        kw["creationflags"] = 0x00000008 | 0x00000200 | 0x08000000  # DETACHED | NEW_GROUP | NO_WINDOW
    else:
        kw["start_new_session"] = True
    subprocess.Popen([sys.executable, str(script), "--refresh"], **kw)


def testo_esito(payload: dict) -> str:
    if payload.get("hook_event_name") == "PostToolUseFailure":
        return str(payload.get("error") or "")
    r = payload.get("tool_response")
    if isinstance(r, dict):
        return f"{r.get('stdout') or ''}\n{r.get('stderr') or ''}"
    return str(r or "")


def main() -> int:
    payload = json.loads(sys.stdin.buffer.read().decode("utf-8") or "{}")
    if payload.get("tool_name") != "Bash":
        return 0
    cmd = str((payload.get("tool_input") or {}).get("command") or "")
    if "gws" not in cmd or not GWS.search(cmd):
        return 0
    evento = payload.get("hook_event_name")
    if evento == "PreToolUse":
        giusto = corretto(cmd)
        if giusto != cmd:
            print(json.dumps({"hookSpecificOutput": {
                "hookEventName": "PreToolUse", "permissionDecision": "deny",
                "permissionDecisionReason": "gws: le risorse di Gmail stanno sotto \"users\" (gws gmail users messages …). "
                                            f"Rilancia così: {giusto}"}}, ensure_ascii=False))
        return 0
    if evento not in ("PostToolUse", "PostToolUseFailure"):
        return 0
    g = guasto(testo_esito(payload))
    if g is None:
        return 0
    nome, cartella = account(cmd)
    try:
        rifai_controllo()
    except Exception:
        pass
    print(json.dumps({"systemMessage": f"gws: {nome} senza credenziali ({g}), serve il login",
                      "hookSpecificOutput": {"hookEventName": evento, "additionalContext": nota(nome, cartella)}},
                     ensure_ascii=False))
    return 0


if __name__ == "__main__":
    # Claude Code scrive e legge in UTF-8. Su Windows la pipe è in cp1252 (16/10/2026).
    for _flusso in (sys.stdout, sys.stderr):
        try:
            _flusso.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass
    try:
        sys.exit(main())
    except Exception:
        sys.exit(0)
