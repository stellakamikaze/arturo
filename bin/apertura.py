#!/usr/bin/env python3
"""arturo apertura: le letture della FASE 4 di /inizio, tutte insieme (#6368, 22/11/2026).

Il progetto della cartella, i todo del progetto, quelli di "generale", il git log e il controllo del
pannello non leggono l'uno il risultato dell'altro. Con una fonte esterna dei task ogni lettura dei
todo può aspettare la rete fino a 90 s, e così `claude plugin list`: in fila i tempi si sommavano.
Qui partono insieme e /inizio aspetta la più lenta. L'uscita ha l'ordine dei comandi in fila.

Solo libreria standard, Python 3.8 o successivo.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

QUI = Path(os.path.realpath(__file__)).parent
ARTURO = QUI / "arturo"
# La CLI dei todo dà 120 s alla fonte esterna: il tetto di ogni lettura sta sopra, così vince il suo errore.
LIMITE = 150
# Col plugin il mod arriva dentro Arturo, con l'id arturo@arturo (review del 7/11/2026, finding 75).
ID_MOD = ("arturo@skills-dir", "arturo@arturo")


def mod_dal_json(testo: str) -> str:
    """"mod caricato" se la lista di `claude plugin list --json` ha il mod di Arturo acceso."""
    try:
        lista = json.loads(testo)
        voci = [p for p in lista if isinstance(p, dict) and p.get("id") in ID_MOD]
    except (ValueError, TypeError):
        return "mod assente"
    return "mod caricato" if any(p.get("enabled") for p in voci) else "mod assente"


def lancia(comando: list, unisci: bool = True) -> tuple:
    """(codice, testo) di un comando. Con unisci gli avvisi su stderr ("Attenzione: …") restano nel testo."""
    try:
        r = subprocess.run(comando, stdout=subprocess.PIPE, stderr=subprocess.STDOUT if unisci else subprocess.DEVNULL,
                           timeout=LIMITE, env={**os.environ, "PYTHONIOENCODING": "utf-8"})
    except subprocess.TimeoutExpired:
        return 124, f"Errore: {Path(comando[0]).name} non ha risposto in {LIMITE} s.\n"
    except OSError as e:
        return 127, f"Errore: {Path(comando[0]).name} non parte ({e}).\n"
    return r.returncode, r.stdout.decode("utf-8", "replace")


def todo(*argomenti: str) -> tuple:
    return lancia([sys.executable, str(ARTURO), "todo", *argomenti])


def pannello() -> str:
    # I comandi di un mod non compaiono fra quelli che il modello vede: lo dice la lista dei plugin.
    claude = shutil.which("claude")
    if not claude:
        return "mod assente"
    codice, testo = lancia([claude, "plugin", "list", "--json"], unisci=False)
    return mod_dal_json(testo) if codice == 0 else "mod assente"


def blocco(titolo: str, testo: str) -> list:
    return [titolo, *(testo.rstrip("\n").splitlines() or ["  niente"]), ""]


def main(argv: list) -> int:
    if argv and argv[0] in ("-h", "--help", "aiuto", "help"):
        print(__doc__)
        return 0
    with ThreadPoolExecutor(max_workers=5) as pool:
        nome = pool.submit(todo, "progetto")
        progetto = pool.submit(todo, "--progetto", ".")
        generale = pool.submit(todo, "--progetto", "generale")
        storia = pool.submit(lancia, ["git", "log", "--oneline", "-20"], False)
        mod = pool.submit(pannello)
        codice_nome, testo_nome = nome.result()
        slug = testo_nome.strip().splitlines()[-1].strip() if codice_nome == 0 and testo_nome.strip() else ""
        righe = [f"PROGETTO {slug}" if slug else "PROGETTO", *([] if slug else testo_nome.rstrip("\n").splitlines()), ""]
        righe += blocco("TODO DEL PROGETTO", progetto.result()[1])
        if slug == "generale":
            righe += ["TODO DI GENERALE", "  è il progetto della cartella: la lista è quella sopra", ""]
        else:
            righe += blocco("TODO DI GENERALE", generale.result()[1])
        codice_git, testo_git = storia.result()
        righe += blocco("GIT LOG", testo_git if codice_git == 0 else "  nessun repository git")
        righe += ["PANNELLO", mod.result()]
    print("\n".join(righe))
    return 0


if __name__ == "__main__":
    for flusso in (sys.stdout, sys.stderr):  # su Windows la pipe è in cp1252
        if hasattr(flusso, "reconfigure"):
            flusso.reconfigure(encoding="utf-8", errors="replace")
    raise SystemExit(main(sys.argv[1:]))
