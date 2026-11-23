#!/usr/bin/env python3
"""Esegue uno script Python come `__main__` nello stesso processo, al posto di `python3 FILE ARG...` (#6492).

Modulo di hooks/hub.py e hooks/dispatcher.py, non un hook. Un processo costa 0,1-0,9 s su Windows, mentre la
logica di un hook ne usa 0,02: qui lo script gira dal bytecode in cache (come `evento_bash.py esegui`), con
argv, stdin, stdout, stderr e path suoi. Alla fine `ripristina` rimette tutto com'era, anche dopo
un'interruzione arrivata in ritardo.

Solo libreria standard, Python 3.8 o successivo.
"""
from __future__ import annotations

import io
import os
import sys

QUI = os.path.dirname(os.path.abspath(__file__))
if QUI not in sys.path:
    sys.path.insert(0, QUI)
import evento_bash  # noqa: E402


def stato():
    return (sys.argv, sys.stdin, sys.stdout, sys.stderr, list(sys.path), sys.modules.get("__main__"))


def ripristina(st):
    """Rimette argv, flussi, path e __main__. Un'interruzione arrivata in ritardo non lo lascia a metà."""
    for _ in range(5):
        try:
            sys.argv, sys.stdin, sys.stdout, sys.stderr = st[:4]
            sys.path[:] = st[4]
            if st[5] is not None:
                sys.modules["__main__"] = st[5]
            return
        except KeyboardInterrupt:
            continue


class _SenzaGuardia:
    def inizia(self, fine):
        return None

    def finisce(self):
        return None


def esegui(percorso, argomenti, payload, guardia=None, tetto=0.0):
    """Esegue `percorso` come __main__ con stdin `payload` (bytes). Torna (codice, stdout, stderr, scaduto).

    `guardia` (hub.Guardia) interrompe lo script oltre `tetto` secondi; senza, lo script non ha tetto qui.
    Il chiamante rimette lo stato con `ripristina` anche se un'interruzione esce di qui."""
    import importlib.util
    import time
    guardia = guardia or _SenzaGuardia()
    try:
        evento_bash._bytecode_controllato(percorso)
    except Exception:
        pass
    entrata = io.TextIOWrapper(io.BytesIO(payload), encoding="utf-8")
    b_out, b_err = io.BytesIO(), io.BytesIO()
    uscita = io.TextIOWrapper(b_out, encoding="utf-8", write_through=True)
    errori = io.TextIOWrapper(b_err, encoding="utf-8", write_through=True)
    codice, scaduto = 0, False
    sys.argv = [percorso] + list(argomenti)
    sys.stdin, sys.stdout, sys.stderr = entrata, uscita, errori
    sys.path.insert(0, os.path.dirname(percorso))
    guardia.inizia(time.monotonic() + tetto)
    try:
        try:
            spec = importlib.util.spec_from_file_location("__main__", percorso)
            modulo = importlib.util.module_from_spec(spec)
            sys.modules["__main__"] = modulo
            spec.loader.exec_module(modulo)
        except SystemExit as e:
            c = e.code
            codice = 0 if c is None else (c if isinstance(c, int) else 1)
            if not isinstance(c, (int, type(None))):
                errori.write(str(c))
        except KeyboardInterrupt:
            scaduto = True
        except BaseException as e:  # uno script rotto non ferma il chiamante
            codice = 1
            errori.write("%s: %s" % (type(e).__name__, e))
    except KeyboardInterrupt:  # l'interruzione arrivata fra un passo e l'altro
        scaduto = True
    finally:
        guardia.finisce()
    try:
        import signal
        if hasattr(signal, "SIGALRM"):
            signal.alarm(0)
            signal.signal(signal.SIGALRM, signal.SIG_DFL)
    except Exception:
        pass
    for f in (uscita, errori):
        try:
            f.flush()
        except Exception:
            pass
    return codice, b_out.getvalue(), b_err.getvalue(), scaduto
