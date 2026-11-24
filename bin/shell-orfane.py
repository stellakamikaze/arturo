#!/usr/bin/env python3
"""Chiude le shell dei comandi di Claude rimaste accese dopo la chiusura della loro sessione (24/11/2026).

Quando una sessione si chiude, Claude Code non spegne le shell lanciate in background: le lascia orfane, per
riprenderle se la sessione riparte (jobs/<id>/adopt.json). Dopo un /fine la sessione non riparte, e l'esito non lo
legge nessuno. Su un Mac, dal 13 al 24/11, 23 shell così: cicli di attesa via ssh fino a sera, server di prova,
ricerche su disco. Una leggeva un log su un altro computer ogni 15 minuti per 16 ore.

Una shell dei comandi di Claude ha nel comando `-c source .../shell-snapshots/snapshot-...`. È orfana quando il
padre non è più un processo di Claude: su macOS passa a launchd (pid 1). La si chiude col suo gruppo di processi
(il ciclo e il suo `sleep`), solo se è dell'utente che lancia e ha almeno ARTURO_ORFANE_ETA_S secondi (120).
Una shell che deve restare accesa porta nel comando il segno `arturo:tieni`. ARTURO_ORFANE_FILTRO limita ai comandi
che contengono quel testo (i banchi).

    shell-orfane.py elenca    # stampa le orfane, senza chiudere niente
    shell-orfane.py chiudi    # le chiude e scrive una riga per shell in data/logs/shell-orfane.log

La lancia hooks/session-start.sh, staccata, a ogni avvio di sessione. Su Windows non fa niente.
"""
from __future__ import annotations

import os
import re
import signal
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(os.path.realpath(__file__)).parent.parent / "hooks"))
import radici  # noqa: E402

SEGNO_SHELL = re.compile(r"-c source \S*shell-snapshots/snapshot-")
TIENI = "arturo:tieni"


def secondi(etime: str) -> int:
    """etime di ps: [[gg-]hh:]mm:ss."""
    giorni, _, resto = etime.rpartition("-")
    parti = [int(p) for p in resto.split(":")]
    while len(parti) < 3:
        parti.insert(0, 0)
    ore, minuti, sec = parti
    return (int(giorni) if giorni else 0) * 86400 + ore * 3600 + minuti * 60 + sec


def processi() -> dict[int, dict]:
    out = subprocess.run(["ps", "-Ao", "pid=,ppid=,pgid=,uid=,etime=,command="],
                         capture_output=True, text=True, check=True).stdout
    tab = {}
    for riga in out.splitlines():
        campi = riga.split(None, 5)
        if len(campi) < 6:
            continue
        pid, ppid, pgid, uid, etime, comando = campi
        try:
            tab[int(pid)] = dict(pid=int(pid), ppid=int(ppid), pgid=int(pgid), uid=int(uid),
                                 eta=secondi(etime), comando=comando)
        except ValueError:
            continue
    return tab


def orfane(tab: dict[int, dict], eta_min: int, filtro: str = "") -> list[dict]:
    mio = os.getuid()
    trovate = []
    for p in tab.values():
        if p["uid"] != mio or not SEGNO_SHELL.search(p["comando"]) or TIENI in p["comando"]:
            continue
        if filtro and filtro not in p["comando"]:
            continue
        if p["eta"] < eta_min:
            continue
        padre = tab.get(p["ppid"])
        if padre and "claude" in padre["comando"].lower():
            continue
        trovate.append(p)
    return trovate


def discendenti(tab: dict[int, dict], radice: int) -> list[int]:
    figli, coda = [], [radice]
    while coda:
        attuale = coda.pop()
        for p in tab.values():
            if p["ppid"] == attuale and p["pid"] not in figli:
                figli.append(p["pid"])
                coda.append(p["pid"])
    return figli


def segnala(pids: list[int], pgid: int | None, sig: int) -> None:
    if pgid is not None:
        try:
            os.killpg(pgid, sig)
        except OSError:
            pass
    for pid in pids:
        try:
            os.kill(pid, sig)
        except OSError:
            pass


def vivo(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


def chiudi(tab: dict[int, dict], p: dict) -> bool:
    # Le shell di Claude sono capigruppo (setsid): col gruppo se ne va anche lo sleep del ciclo. Se non lo è,
    # si chiudono lei e i suoi discendenti uno per uno, senza toccare il gruppo di altri.
    pgid = p["pid"] if p["pgid"] == p["pid"] else None
    pids = [p["pid"]] + discendenti(tab, p["pid"])
    segnala(pids, pgid, signal.SIGTERM)
    for _ in range(20):
        if not vivo(p["pid"]):
            return True
        time.sleep(0.1)
    segnala(pids, pgid, signal.SIGKILL)
    time.sleep(0.2)
    return not vivo(p["pid"])


def registro() -> Path:
    if os.environ.get("ARTURO_ORFANE_LOG"):
        return Path(os.environ["ARTURO_ORFANE_LOG"])
    return radici.radice_orsa() / "data" / "logs" / "shell-orfane.log"


def comando_breve(p: dict) -> str:
    c = p["comando"]
    # Il comando vero sta dopo il preambolo `source <snapshot> ... && eval '...'`.
    m = re.search(r"eval '(.*)", c)
    return (m.group(1) if m else c)[:200].replace("\n", " ")


def main(argv: list[str]) -> int:
    if os.name == "nt":
        return 0
    if len(argv) != 2 or argv[1] not in ("elenca", "chiudi"):
        print("uso: shell-orfane.py elenca|chiudi", file=sys.stderr)
        return 2
    eta_min = int(os.environ.get("ARTURO_ORFANE_ETA_S", "120"))
    tab = processi()
    # ARTURO_ORFANE_FILTRO limita la ricerca ai comandi che contengono quel testo: i banchi lo usano, così un
    # veleno sul controllo del padre non chiude le shell delle sessioni vive (24/11/2026, successo alla prima prova).
    trovate = orfane(tab, eta_min, os.environ.get("ARTURO_ORFANE_FILTRO", ""))
    if argv[1] == "elenca":
        for p in trovate:
            print(f"{p['pid']} da {p['eta']} s | {comando_breve(p)}")
        return 0
    if not trovate:
        return 0
    log = registro()
    log.parent.mkdir(parents=True, exist_ok=True)
    with log.open("a", encoding="utf-8") as f:
        for p in trovate:
            esito = "chiusa" if chiudi(tab, p) else "RESISTE"
            f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} {esito} pid {p['pid']} da {p['eta']} s | "
                    f"{comando_breve(p)}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
