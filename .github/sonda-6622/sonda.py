#!/usr/bin/env python3
"""Sonda #6622: lo scenario di T08 di tests/test_todo.py ripetuto, con lo stderr di ogni scrittura che cade.

Uso: python sonda.py <repo> <giri> <etichetta>. Stampa una riga CADUTA per ogni processo con rc != 0
e una riga RIEPILOGO alla fine. Esce sempre 0: e' una sonda, legge e basta.
"""
import json
import os
import subprocess
import sys
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

REPO = Path(sys.argv[1]).resolve()
GIRI = int(sys.argv[2])
NOME = sys.argv[3]


def cli(home, *argomenti):
    env = dict(os.environ, HOME=str(home), USERPROFILE=str(home), ARTURO_OGGI="2026-10-03",
               PYTHONIOENCODING="utf-8")
    env.pop("ARTURO_TODO", None)
    t0 = time.time()
    r = subprocess.run([sys.executable, str(REPO / "bin" / "arturo"), "todo", *argomenti],
                       cwd=str(home), env=env, capture_output=True, timeout=120)
    return r.returncode, time.time() - t0, r.stderr.decode("utf-8", "replace"), r.stdout.decode("utf-8", "replace")


cadute = 0
perse = 0
for giro in range(GIRI):
    with tempfile.TemporaryDirectory() as tmp:
        home = Path(tmp) / "home"
        home.mkdir()
        cli(home, "aggiungi", "Todo comune", "--progetto", "p")
        lavori = [("crea", n, ("aggiungi", f"processo {n}", "--progetto", "p")) for n in range(24)]
        note = [("nota", n, ("nota", "1", f"nota {n}")) for n in range(64)]
        esiti = []
        with ThreadPoolExecutor(max_workers=12) as pool:
            esiti += list(pool.map(lambda l: (l, cli(home, *l[2])), lavori))
        with ThreadPoolExecutor(max_workers=16) as pool:
            esiti += list(pool.map(lambda l: (l, cli(home, *l[2])), note))
        for (tipo, n, _), (rc, durata, err, out) in esiti:
            if rc != 0:
                cadute += 1
                print(f"CADUTA {NOME} giro={giro} {tipo} {n} rc={rc} durata={durata:.2f}s\n"
                      f"  stderr: {err.strip()}\n  stdout: {out.strip()[:300]}", flush=True)
        registro = home / ".claude" / "data" / "todo" / "eventi.jsonl"
        righe = [r for r in registro.read_text(encoding="utf-8").splitlines() if r.strip()]
        rotte = 0
        for r in righe:
            try:
                json.loads(r)
            except ValueError:
                rotte += 1
        if len(righe) != 89 or rotte:
            perse += 1
            print(f"REGISTRO {NOME} giro={giro} righe={len(righe)} rotte={rotte}", flush=True)
        lente = sorted((d for _, (_, d, _, _) in esiti), reverse=True)[:3]
        print(f"giro {NOME} {giro}: cadute={sum(1 for _, e in esiti if e[0])} "
              f"piu' lente={[round(x, 2) for x in lente]}", flush=True)
print(f"RIEPILOGO {NOME} python={sys.version.split()[0]} giri={GIRI} cadute={cadute} registri_sbagliati={perse}")
