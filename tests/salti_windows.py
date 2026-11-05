"""Salti dichiarati su Windows (31/10/2026, #4383).

Windows crea link simbolici solo con la Modalità sviluppatore o da amministratore: altrimenti
os.symlink esce con WinError 1314. Un controllo che ha bisogno di un link vero non si può provare,
e non è né verde né rosso. Prima alcuni banchi tornavano in silenzio (Y08, G211) e altri cadevano
rossi (NA01, SI01): ora il controllo esce come SALTO col suo codice e il gate li conta nell'esito.

Il salto scatta solo per WinError 1314 su Windows: su macOS e Linux, e per ogni altro errore,
il link resta obbligatorio e un guasto resta rosso.
"""
from __future__ import annotations

import contextlib
import os
import shutil
import stat
import sys
import tempfile
import time
from pathlib import Path
from typing import Iterator

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


def _togli_sola_lettura(funzione, percorso, _errore) -> None:
    """I file di git sono di sola lettura: su Windows si cancellano solo dopo il permesso di scrittura."""
    os.chmod(percorso, stat.S_IWRITE)
    funzione(percorso)


def _cancella(cartella: str) -> None:
    if sys.version_info >= (3, 12):
        shutil.rmtree(cartella, onexc=_togli_sola_lettura)
    else:
        shutil.rmtree(cartella, onerror=lambda f, p, e: _togli_sola_lettura(f, p, e[1]))


@contextlib.contextmanager
def cartella_prova(attesa: float = 60.0) -> Iterator[str]:
    """Una cartella temporanea che su Windows aspetta i processi staccati prima di sparire (#4440).

    Le versioni vecchie di statusline.js e session-start.sh lanciano processi staccati (git status,
    il controllo degli aggiornamenti, git fetch) che tengono aperto un file nella cartella di prova
    dopo la fine del controllo. Col computer carico vivono più a lungo, e su Windows la pulizia di
    TemporaryDirectory esce con WinError 32 al posto dell'esito del controllo. Qui la pulizia
    toglie la sola lettura ai file di git, come TemporaryDirectory, e riprova solo sul WinError 32
    finché quei processi escono; dopo `attesa` secondi lascia la cartella nella TMPDIR, perché un
    file ancora aperto non dice niente sul controllo. Ogni altro errore resta un errore.
    """
    d = tempfile.mkdtemp()
    try:
        yield d
    finally:
        fine = time.monotonic() + attesa
        while True:
            try:
                _cancella(d)
                break
            except FileNotFoundError:
                break
            except PermissionError as e:
                if os.name != "nt" or getattr(e, "winerror", None) != 32:
                    raise
                if time.monotonic() > fine:
                    print(f"cartella di prova lasciata, un processo staccato la tiene ancora aperta: {d}")
                    break
                time.sleep(0.5)
