#!/usr/bin/env python3
"""Controlla che la config di Arturo sia integra dopo un aggiornamento.

Claude Code scarta un settings.json che non è JSON valido, e con lui i deny e
gli hook: una config rotta spegne tutte le guardie senza dire niente. Questo
controllo lo usano /inizio, /aggiorna, /fine e l'avvio della sessione.

Controlla:
  - settings.json è JSON valido;
  - ogni script citato da un hook di settings.json e settings.local.json esiste:
    `python3 file-mancante.py` esce con 2, e su PreToolUse il 2 blocca ogni azione;
  - nessun rebase o merge lasciato a metà;
  - nessun file in conflitto e nessun marcatore di conflitto nei file tracciati.

Uscita: 0 se la config è integra, 1 se c'è un problema (una riga per problema
su stdout). Con --quiet non stampa nulla quando è tutto a posto.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys


def git(radice, *argomenti):
    try:
        r = subprocess.run(["git", "-C", radice, *argomenti], capture_output=True, text=True, timeout=10)
    except Exception:
        return 1, ""
    return r.returncode, r.stdout


# Uno script dentro la config: ~/.claude/..., $HOME/.claude/... o ${HOME}/.claude/...
SCRIPT_IN_CONFIG = re.compile(r"(?:~|\$HOME|\$\{HOME\})/\.claude/([^\s\"';|&<>]+)")


def script_mancanti(radice, impostazioni):
    """Gli script citati dai comandi degli hook che non esistono nella radice."""
    mancanti = []
    for evento, gruppi in (impostazioni.get("hooks") or {}).items():
        for gruppo in gruppi if isinstance(gruppi, list) else []:
            for hook in (gruppo.get("hooks") or []) if isinstance(gruppo, dict) else []:
                comando = hook.get("command", "") if isinstance(hook, dict) else ""
                for relativo in SCRIPT_IN_CONFIG.findall(comando):
                    if not os.path.exists(os.path.join(radice, relativo)) and (evento, relativo) not in mancanti:
                        mancanti.append((evento, relativo))
    return mancanti


def problemi(radice):
    trovati = []
    for nome in ("settings.json", "settings.local.json"):
        impostazioni = os.path.join(radice, nome)
        if not os.path.exists(impostazioni):
            continue
        try:
            with open(impostazioni, encoding="utf-8") as f:
                dati = json.load(f)
        except Exception as errore:
            if nome == "settings.json":
                trovati.append(f"settings.json non è JSON valido ({errore}): Claude Code lo ignora e le guardie sono spente")
            else:
                trovati.append(f"settings.local.json non è JSON valido ({errore}): Claude Code lo ignora")
            continue
        if isinstance(dati, dict):
            for evento, relativo in script_mancanti(radice, dati):
                trovati.append(f"hook mancante: {nome} lancia ~/.claude/{relativo} su {evento}, ma il file non c'è")

    rc, _ = git(radice, "rev-parse", "--git-dir")
    if rc != 0:
        return trovati
    for nome, cosa in (("rebase-merge", "rebase"), ("rebase-apply", "rebase"), ("MERGE_HEAD", "merge")):
        rc, percorso = git(radice, "rev-parse", "--git-path", nome)
        percorso = percorso.strip()
        if rc == 0 and percorso and os.path.exists(os.path.join(radice, percorso) if not os.path.isabs(percorso) else percorso):
            trovati.append(f"{cosa} lasciato a metà: per tornare a prima esegui `git -C {radice} {cosa} --abort`")
            break
    _, conflitti = git(radice, "diff", "--name-only", "--diff-filter=U")
    for file in conflitti.split():
        trovati.append(f"file in conflitto: {file}")
    _, marcatori = git(radice, "grep", "-l", "-I", "-E", "^(<<<<<<<|>>>>>>>) ")
    for file in marcatori.split():
        if f"file in conflitto: {file}" not in trovati:
            trovati.append(f"marcatori di conflitto dentro {file}")
    return trovati


def main():
    quiet = "--quiet" in sys.argv[1:]
    argomenti = [a for a in sys.argv[1:] if a != "--quiet"]
    radice = argomenti[0] if argomenti else os.path.join(os.path.expanduser("~"), ".claude")
    trovati = problemi(radice)
    if trovati:
        for riga in trovati:
            print(f"CONFIG ROTTA: {riga}")
        return 1
    if not quiet:
        print("CONFIG OK: settings.json valido, nessun conflitto")
    return 0


if __name__ == "__main__":
    sys.exit(main())
