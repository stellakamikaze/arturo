#!/usr/bin/env python3
"""Controlla che la config di Arturo sia integra dopo un aggiornamento.

Claude Code scarta un settings.json che non e' JSON valido, e con lui i deny e
gli hook: una config rotta spegne tutte le guardie senza dire niente. Questo
controllo lo usano /inizio, /aggiorna, /fine e l'avvio della sessione.

Controlla:
  - settings.json e' JSON valido;
  - nessun rebase o merge lasciato a meta';
  - nessun file in conflitto e nessun marcatore di conflitto nei file tracciati.

Uscita: 0 se la config e' integra, 1 se c'e' un problema (una riga per problema
su stdout). Con --quiet non stampa nulla quando e' tutto a posto.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys


def git(radice, *argomenti):
    try:
        r = subprocess.run(["git", "-C", radice, *argomenti], capture_output=True, text=True, timeout=10)
    except Exception:
        return 1, ""
    return r.returncode, r.stdout


def problemi(radice):
    trovati = []
    impostazioni = os.path.join(radice, "settings.json")
    if os.path.exists(impostazioni):
        try:
            with open(impostazioni, encoding="utf-8") as f:
                json.load(f)
        except Exception as errore:
            trovati.append(f"settings.json non e' JSON valido ({errore}): Claude Code lo ignora e le guardie sono spente")

    rc, _ = git(radice, "rev-parse", "--git-dir")
    if rc != 0:
        return trovati
    for nome, cosa in (("rebase-merge", "rebase"), ("rebase-apply", "rebase"), ("MERGE_HEAD", "merge")):
        rc, percorso = git(radice, "rev-parse", "--git-path", nome)
        percorso = percorso.strip()
        if rc == 0 and percorso and os.path.exists(os.path.join(radice, percorso) if not os.path.isabs(percorso) else percorso):
            trovati.append(f"{cosa} lasciato a meta': per tornare a prima esegui `git -C {radice} {cosa} --abort`")
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
