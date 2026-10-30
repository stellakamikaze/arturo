#!/usr/bin/env python3
"""Retention degli handoff di un progetto: tiene i più recenti PER FILONE.

Uso: handoff-retention.py <slug> [--keep 5] [--dry-run | --applica] [--radice DIR] [--elenco PATH]
La chiave del filone è quella di index-rigenera.py (la stessa funzione, importata).
L'ordine viene dalla data nel nome del file, mai dalla data del file: dopo un pull o un
ripristino le date dei file sono tutte fresche. Per ogni file in uscita stampa i Vicoli
ciechi e le righe di Task Pendenti senza #ID, per decidere cosa salvare prima che esca.
Di default non tocca niente. Con --applica sposta i file in uscita nel cestino dello store,
<radice>/.cestino/<slug>/, e toglie dal cestino quelli che ci stanno da più di 30 giorni,
di ogni progetto (#4264): un handoff tolto si recupera per un mese (segnalazione n. 26,
28/10/2026: con os.remove era sparito per sempre). Per riaverlo si sposta il file da
.cestino/<slug>/ alla cartella <slug>/. L'indice e /inizio saltano le cartelle col punto.

Esce solo ciò che il dry-run ha mostrato (30/10/2026, #4291). Il dry-run scrive l'elenco dei file in
uscita in <cartella temporanea>/retention-<slug>-<sessione>.txt, con la sessione da
CLAUDE_CODE_SESSION_ID; --elenco PATH lo sceglie. --applica sposta solo i file di quell'elenco ancora
oltre il keep: un handoff scritto da un'altra sessione fra dry-run e applica non fa uscire un file che
nessuno ha letto. Senza elenco --applica non sposta niente e stampa AVVISO e una riga RESTA per file.

Output (stdout):
  RETENTION <slug> · keep N per filone · <dry-run|applica>
  FILONE <chiave>: <n> file, tengo <k>[, escono <m>]
  === IN USCITA <slug>/<file> (filone <chiave>) ===
  Vicoli ciechi: / Task senza ID: (righe, o "nessuno")
  NEL CESTINO <slug>/<file> → .cestino/<slug>/<file>     (solo con --applica)
  RESTA <slug>/<file> (...)                              (con --applica: fuori dall'elenco del dry-run)
  Per riportarne uno: sposta il file da … a …            (solo con --applica e file in uscita)
  TOLTO DAL CESTINO <progetto>/<file> (oltre 30 giorni)  (solo con --applica, ogni progetto)
  TOTALE in uscita: <m>
Exit: 0 fatto (anche niente da fare) · 2 uso sbagliato o slug assente · 3 spostamento fallito.
"""
from __future__ import annotations

import argparse
import importlib.util
import os
import re
import sys
import tempfile
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


def percorso_elenco(slug, esplicito=None):
    """File dell'elenco del dry-run: --elenco, altrimenti per sessione nella cartella temporanea.
    Senza CLAUDE_CODE_SESSION_ID e senza --elenco non c'è un elenco: due sessioni ne scriverebbero uno solo."""
    if esplicito:
        return Path(esplicito)
    sessione = re.sub(r"[^A-Za-z0-9_-]", "_", os.environ.get("CLAUDE_CODE_SESSION_ID", ""))
    if not sessione:
        return None
    return Path(tempfile.gettempdir()) / f"retention-{slug}-{sessione}.txt"


def task_senza_id(corpo, celle, colonna="id"):
    """Righe della tabella Task Pendenti senza #numero nella colonna ID (il nome viene dal profilo,
    hooks/handoff-gate.local)."""
    out, col = [], None
    for r in corpo.splitlines():
        if not r.lstrip().startswith("|"):
            continue
        c = celle(r)
        if col is None and any(x.lower() == "task" for x in c):
            col = next((i for i, x in enumerate(c) if x.lower() == colonna.lower()), -1)
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
    ap.add_argument("--elenco", help="file dell'elenco del dry-run (default per sessione, nella cartella temporanea)")
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

    sys.path.insert(0, str(QUI))
    import handoff_profilo
    colonna = handoff_profilo.carica()["colonna-id"]
    for k, h in uscita:
        print(f"\n=== IN USCITA {h['rel']} (filone {k}) ===")
        vicoli = [r for r in ir.sezione(h["testo"], "Vicoli ciechi").splitlines() if r.strip()]
        print("Vicoli ciechi:" if vicoli else "Vicoli ciechi: nessuno")
        for r in vicoli:
            print(f"  {r}")
        senza = task_senza_id(ir.sezione(h["testo"], "Task Pendenti"), ir.celle, colonna)
        print("Task senza ID:" if senza else "Task senza ID: nessuno")
        for r in senza:
            print(f"  {r}")

    elenco = percorso_elenco(a.slug, a.elenco)
    if a.applica:
        try:
            letti = set(elenco.read_text(encoding="utf-8").split()) if elenco else set()
        except OSError:
            letti = set()
        if not letti and uscita:
            dove = elenco or "manca CLAUDE_CODE_SESSION_ID"
            print(f"AVVISO: nessun elenco del dry-run ({dove}): niente spostato. Lancia prima il dry-run e "
                  "decidi cosa salvare.")
        for k, h in uscita:
            if h["rel"] not in letti:
                print(f"RESTA {h['rel']} (filone {k}): oltre il keep, ma il dry-run non l'ha mostrato")
        uscita = [(k, h) for k, h in uscita if h["rel"] in letti]
    elif elenco is None:
        print("AVVISO: manca CLAUDE_CODE_SESSION_ID: elenco del dry-run non scritto, --applica non sposterà "
              "niente. Passa --elenco PATH.", file=sys.stderr)
    else:
        # Anche vuoto: un elenco vuoto dice a --applica che non deve uscire niente.
        try:
            elenco.write_text("".join(f"{h['rel']}\n" for _, h in uscita), encoding="utf-8")
        except OSError as e:
            print(f"AVVISO: elenco del dry-run non scritto ({elenco}): {e}", file=sys.stderr)

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
        if uscita:
            print(f"Per riportarne uno: sposta il file da {cestino / a.slug} a {radice / a.slug}.")
        # Il cestino si svuota per ogni progetto, non solo per questo: un progetto che non passa
        # più da /fine terrebbe i suoi file per sempre (#4264).
        limite = time.time() - GIORNI_NEL_CESTINO * 86400
        for f in sorted(cestino.glob("*/HANDOFF_*.md")) if cestino.is_dir() else []:
            rel = f"{f.parent.name}/{f.name}"
            try:
                if f.stat().st_mtime < limite:
                    f.unlink()
                    print(f"TOLTO DAL CESTINO {rel} (oltre {GIORNI_NEL_CESTINO} giorni)")
            except OSError as e:
                print(f"ERRORE {CESTINO}/{rel}: {e}", file=sys.stderr)
    print(f"\nTOTALE in uscita: {len(uscita)}")
    if uscita and not a.applica:
        print("Niente spostato. Dopo aver deciso cosa salvare, rilancia con --applica.")
    if a.applica and not errori and elenco:
        try:
            elenco.unlink()  # consumato: il prossimo giro rifà il dry-run
        except OSError:
            pass
    return 3 if errori else 0


if __name__ == "__main__":
    for flusso in (sys.stdout, sys.stderr):  # su Windows la pipe è in cp1252, Claude legge UTF-8
        try:
            flusso.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass
    sys.exit(main())
