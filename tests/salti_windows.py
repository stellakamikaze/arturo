"""Salti dichiarati su Windows (31/10/2026, #4383).

Windows crea link simbolici solo con la Modalità sviluppatore o da amministratore: altrimenti
os.symlink esce con WinError 1314. Un controllo che ha bisogno di un link vero non si può provare,
e non è né verde né rosso. Prima alcuni banchi tornavano in silenzio (Y08, G211) e altri cadevano
rossi (NA01, SI01): ora il controllo esce come SALTO col suo codice e il gate li conta nell'esito.

Il salto scatta solo per WinError 1314 su Windows: su macOS e Linux, e per ogni altro errore,
il link resta obbligatorio e un guasto resta rosso.
"""
from __future__ import annotations

import os
from pathlib import Path

MOTIVO = ("Windows non concede i link simbolici (WinError 1314): "
          "con la Modalità sviluppatore il controllo si prova")


class SaltoWindows(Exception):
    """Un controllo che Windows non permette di provare."""


def link(nuovo: Path, bersaglio: Path, cartella: bool = False) -> None:
    """Crea il link `nuovo` -> `bersaglio`; su Windows senza permesso solleva SaltoWindows."""
    try:
        nuovo.symlink_to(bersaglio, target_is_directory=cartella)
    except OSError as e:
        if os.name == "nt" and getattr(e, "winerror", None) == 1314:
            raise SaltoWindows(MOTIVO) from e
        raise


def dichiara(codice: str, motivo: object = MOTIVO) -> None:
    """Stampa la riga SALTO e la aggiunge al file $ARTURO_SALTI, che il gate riporta nell'esito."""
    riga = f"SALTO {codice}: {motivo}"
    print(riga)
    percorso = os.environ.get("ARTURO_SALTI")
    if percorso:
        with open(percorso, "a", encoding="utf-8") as f:
            f.write(riga + "\n")
