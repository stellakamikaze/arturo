#!/usr/bin/env python3
"""Retention degli handoff di un progetto: tiene i più recenti PER FILONE.

Uso: handoff-retention.py <slug> [--keep 5] [--dry-run | --applica] [--radice DIR]
La chiave del filone è quella di index-rigenera.py (la stessa funzione, importata).
L'ordine viene dalla data nel nome del file, mai dalla data del file: dopo un pull o un
ripristino le date dei file sono tutte fresche. Per ogni file in uscita stampa i Vicoli
ciechi e le righe di Task Pendenti senza #ID, per decidere cosa salvare prima che esca.
Di default non tocca niente. Con --applica sposta i file in uscita nel cestino dello store,
<radice>/.cestino/<slug>/, e toglie dal cestino quelli che ci stanno da più di 30 giorni:
un handoff tolto si recupera per un mese (segnalazione n. 26, 28/10/2026: con os.remove
era sparito per sempre). L'indice e /inizio saltano le cartelle col punto.

Output (stdout):
  RETENTION <slug> · keep N per filone · <dry-run|applica>
  FILONE <chiave>: <n> file, tengo <k>[, escono <m>]
  === IN USCITA <slug>/<file> (filone <chiave>) ===
  Vicoli ciechi: / Task senza ID: (righe, o "nessuno")
  NEL CESTINO <slug>/<file> → .cestino/<slug>/<file>     (solo con --applica)
  TOLTO DAL CESTINO <slug>/<file> (oltre 30 giorni)      (solo con --applica)
  TOTALE in uscita: <m>
Exit: 0 fatto (anche niente da fare) · 2 uso sbagliato o slug assente · 3 spostamento fallito.
"""
from __future__ import annotations

import argparse
import importlib.util
import os
import re
import sys
import time
from pathlib import Path

QUI = Path(__file__).resolve().parent
CESTINO = ".cestino"
GIORNI_NEL_CESTINO = 30


def carica_index():
    spec = importlib.util.spec_from_file_location("index_rigenera", str(QUI / "index-rigenera.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def task_senza_id(corpo, celle):
    """Righe della tabella Task Pendenti senza #numero nella colonna ID."""
    out, col = [], None
    for r in corpo.splitlines():
        if not r.lstrip().startswith("|"):
            continue
        c = celle(r)
        if col is None and any(x.lower() == "task" for x in c):
            col = next((i for i, x in enumerate(c) if x.lower() == "id"), -1)
            continue
        if set("".join(c)) <= set("-: "):
            continue
        cella = c[col] if col is not None and 0 <= col < len(c) else " ".join(c)
        if not re.search(r"#\d+", cella):
            out.append(r.strip())
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description="Retention degli handoff per filone.")
    ap.add_argument("slug")
    ap.add_argument("--keep", type=int, default=5)
    modo = ap.add_mutually_exclusive_group()
    modo.add_argument("--dry-run", action="store_true", help="default: mostra, non cancella")
    modo.add_argument("--applica", action="store_true", help="sposta i file in uscita nel cestino dello store")
    ap.add_argument("--radice", help="cartella degli handoff (default ~/.claude/data/handoffs)")
    a = ap.parse_args(argv)
    if a.keep < 1:
        print("handoff-retention: --keep deve essere almeno 1", file=sys.stderr)
        return 2
    ir = carica_index()
    radice = Path(a.radice) if a.radice else ir.RADICE
    if "/" in a.slug or a.slug.startswith(".") or not (radice / a.slug).is_dir():
        print(f"handoff-retention: cartella assente: {radice / a.slug}", file=sys.stderr)
        return 2

    tutti = [h for h in ir.elenca(radice) if h["slug"] == a.slug]
    gruppi = ir.per_chiave(tutti)
    print(f"RETENTION {a.slug} · keep {a.keep} per filone · {'applica' if a.applica else 'dry-run'}")
    uscita = []
    for k in sorted(gruppi):
        g = gruppi[k]
        escono = g[a.keep:]
        coda = f", escono {len(escono)}" if escono else ""
        print(f"FILONE {k}: {len(g)} file, tengo {min(len(g), a.keep)}{coda}")
        uscita += [(k, h) for h in escono]

    for k, h in uscita:
        print(f"\n=== IN USCITA {h['rel']} (filone {k}) ===")
        vicoli = [r for r in ir.sezione(h["testo"], "Vicoli ciechi").splitlines() if r.strip()]
        print("Vicoli ciechi:" if vicoli else "Vicoli ciechi: nessuno")
        for r in vicoli:
            print(f"  {r}")
        senza = task_senza_id(ir.sezione(h["testo"], "Task Pendenti"), ir.celle)
        print("Task senza ID:" if senza else "Task senza ID: nessuno")
        for r in senza:
            print(f"  {r}")

    errori = 0
    if a.applica:
        cestino = radice / CESTINO
        for _, h in uscita:
            dove = cestino / h["rel"]
            try:
                dove.parent.mkdir(parents=True, exist_ok=True)
                os.replace(str(radice / h["rel"]), str(dove))
                os.utime(str(dove))  # i 30 giorni contano da oggi, non dalla data dell'handoff
                print(f"NEL CESTINO {h['rel']} → {CESTINO}/{h['rel']}")
            except OSError as e:
                errori += 1
                print(f"ERRORE {h['rel']}: {e}", file=sys.stderr)
        limite = time.time() - GIORNI_NEL_CESTINO * 86400
        for f in sorted((cestino / a.slug).glob("HANDOFF_*.md")) if (cestino / a.slug).is_dir() else []:
            try:
                if f.stat().st_mtime < limite:
                    f.unlink()
                    print(f"TOLTO DAL CESTINO {a.slug}/{f.name} (oltre {GIORNI_NEL_CESTINO} giorni)")
            except OSError as e:
                print(f"ERRORE {CESTINO}/{a.slug}/{f.name}: {e}", file=sys.stderr)
    print(f"\nTOTALE in uscita: {len(uscita)}")
    if uscita and not a.applica:
        print("Niente spostato. Dopo aver deciso cosa salvare, rilancia con --applica.")
    return 3 if errori else 0


if __name__ == "__main__":
    for flusso in (sys.stdout, sys.stderr):  # su Windows la pipe è in cp1252, Claude legge UTF-8
        try:
            flusso.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass
    sys.exit(main())
