#!/usr/bin/env python3
"""Il fetch della config all'avvio, staccato dalla sessione (#6370, 22/11/2026).

    avvio-fetch.py stacca <radice> <adesso> <riuscito>

`stacca` lancia questo file con `lavora` e gli stessi argomenti, poi esce subito. Il processo che lavora
non è figlio di un processo vivo: su Windows Claude Code, quando annulla un hook al timeout, chiude
l'albero dei processi dell'hook partendo dai padri, e un `( ... ) &` di bash moriva con lui. Su
un computer Windows di chi mantiene Arturo il fetch dura 35 secondi e non arrivava mai in fondo (10 avvii su 11 dal 20/11).

`lavora` fa il fetch di main e dei tag dalla sorgente degli aggiornamenti (upstream se c'è, altrimenti
origin) e scrive <adesso> in <riuscito> solo se il fetch riesce. Con upstream fa anche il fetch di
origin, il repository privato di chi usa (30/10/2026). Nessun comando chiede niente: niente prompt delle
credenziali, ssh in BatchMode, tetti di tempo su connessione e trasferimento (lotto L10, 9/11/2026).

Flag di Windows: CREATE_NO_WINDOW | CREATE_NEW_PROCESS_GROUP, mai DETACHED_PROCESS, che apre una
finestra per ogni git figlio (tests/test_finestre_windows_2026_11_04.py).
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys

LENTO = ["-c", "http.lowSpeedLimit=1000", "-c", "http.lowSpeedTime=30"]
TETTO_S = 300  # un fetch appeso non resta vivo per sempre, uno in più a ogni tentativo


def staccato() -> dict:
    opzioni = {"stdin": subprocess.DEVNULL, "stdout": subprocess.DEVNULL, "stderr": subprocess.DEVNULL}
    if os.name == "nt":
        opzioni["creationflags"] = 0x08000000 | 0x00000200  # CREATE_NO_WINDOW | CREATE_NEW_PROCESS_GROUP
    else:
        opzioni["start_new_session"] = True
    return opzioni


def git(radice: str, *argomenti: str, tetto: float = 20) -> int:
    # shutil.which legge PATHEXT: su Windows trova anche un git.cmd (i banchi usano un git finto).
    eseguibile = shutil.which("git") or "git"
    env = {**os.environ, "GIT_TERMINAL_PROMPT": "0",
           "GIT_SSH_COMMAND": "ssh -o BatchMode=yes -o ConnectTimeout=10 -o ServerAliveInterval=15 -o ServerAliveCountMax=2"}
    try:
        return subprocess.run([eseguibile, "-C", radice, *argomenti], stdin=subprocess.DEVNULL,
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, env=env, timeout=tetto).returncode
    except (OSError, subprocess.SubprocessError):
        return 1


def lavora(radice: str, adesso: str, riuscito: str) -> int:
    remoto = "upstream" if git(radice, "remote", "get-url", "upstream") == 0 else "origin"
    rc = git(radice, *LENTO, "fetch", "--quiet", "--tags", remoto, "main", tetto=TETTO_S)
    if rc == 0:
        try:
            with open(riuscito, "w", encoding="utf-8") as f:
                f.write(adesso)
        except OSError:
            pass
    if remoto == "upstream":
        git(radice, *LENTO, "fetch", "--quiet", "origin", "main", tetto=TETTO_S)
    return rc


def main(argv: list) -> int:
    if len(argv) != 5 or argv[1] not in ("stacca", "lavora") or not argv[3].isdigit():
        print("uso: avvio-fetch.py stacca|lavora <radice> <adesso> <riuscito>", file=sys.stderr)
        return 2
    if argv[1] == "lavora":
        return lavora(*argv[2:])
    try:
        subprocess.Popen([sys.executable, os.path.realpath(__file__), "lavora", *argv[2:]], **staccato())
    except OSError:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
