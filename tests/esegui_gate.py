#!/usr/bin/env python3
"""Esegue i banchi del gate completo in parallelo (3/11/2026).

Perché esiste: il gate faceva girare 90 banchi, 84 controprove e i veleni uno dopo l'altro, e si fermava
al primo rosso. Il 3/11/2026 su un Mac erano 22 minuti di lavoro, e il rilascio 0.2.0 ha avuto
bisogno di cinque giri, uno per rosso. Qui i lavori girano su N worker e il gate li fa girare tutti:
un giro solo dice ogni rosso.

  esegui_gate.py copia SORGENTE COPIA
      La copia del repository che usano i banchi: .git e i file che git vede (tracciati e nuovi non
      ignorati), come un clone pulito con le modifiche in corso. Con `cp -R` entravano anche cache/ e
      data/ della macchina: il 19/10/2026 una coda di telemetria vecchia ha fatto rosso GS06.

  esegui_gate.py esegui --root R --fixture F [--lavori N] [--rossi] [--py38 EXE]
                 [--banchi ...] [--in-fila ...] [--banchi-py38 ...] [--controprove "banco ref [radice]" ...]
                 [--veleni ...]
      Ogni worker ha HOME, TMPDIR, cache e file dei salti suoi, sotto F/w<i>, con la sua copia del
      repository in HOME/.claude. I lavori di un worker girano in fila nella sua copia. Prima i lavori
      più lunghi, coi tempi dell'ultimo giro. I banchi di --in-fila girano dopo, uno alla volta: sotto
      carico danno rossi che da soli passano (T22, SM04: per questo c'è il lucchetto, #4360).
      Con --rossi rifà solo i lavori rossi dell'ultimo giro e stampa PARZIALE: non vale per un rilascio.
      Esce 1 se un lavoro è rosso, dopo averli fatti girare tutti.

I tempi e i rossi dell'ultimo giro stanno nella cartella comune di git (arturo-gate-tempi.json,
arturo-gate-rossi.txt): restano sulla macchina e valgono per tutti i worktree. Solo libreria standard,
Python 3.8 o successivo.
"""
from __future__ import annotations

import argparse
import json
import os
import queue
import shutil
import stat
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import Dict, List, Optional

TETTO = 1800  # un lavoro appeso non deve tenere fermo il gate per sempre
RIGHE_ROSSO = 40


def _socket(cartella: str, nomi: List[str]) -> List[str]:  # fsmonitor--daemon.ipc: un socket non si copia
    return [n for n in nomi if stat.S_ISSOCK(os.lstat(os.path.join(cartella, n)).st_mode)]


def copia(radice: str, dest: str) -> None:
    git = os.path.join(radice, ".git")
    if os.path.isdir(git):
        shutil.copytree(git, os.path.join(dest, ".git"), symlinks=True, ignore=_socket)
    else:  # worktree: .git è un file che punta alla cartella vera
        os.makedirs(dest, exist_ok=True)
        shutil.copy2(git, os.path.join(dest, ".git"))
    elenco = subprocess.run(["git", "-C", radice, "ls-files", "-z", "-co", "--exclude-standard"],
                            capture_output=True, check=True).stdout.decode("utf-8")
    for rel in filter(None, elenco.split("\0")):
        origine = os.path.join(radice, rel)
        if not os.path.lexists(origine):  # tracciato ma cancellato nel tree
            continue
        d = os.path.join(dest, rel)
        os.makedirs(os.path.dirname(d), exist_ok=True)
        shutil.copy2(origine, d, follow_symlinks=False)


class Lavoro:
    def __init__(self, tipo: str, banco: str, ref: str = "", modo: str = "") -> None:
        self.tipo, self.banco, self.ref, self.modo = tipo, banco, ref, modo
        self.id = f"{tipo}:{banco}" + (f"@{ref}" if ref else "")
        self.secondi = 0.0
        self.rosso = False
        self.log = ""

    def comando(self, w: "Worker", root: Path, py38: str) -> List[str]:
        test = str(w.repo / "tests" / self.banco)
        if self.tipo == "py38":
            return [py38, "-B", test, "--repo", str(w.repo)]
        if self.tipo == "veleno":
            return [sys.executable, "-B", test, "--repo", str(w.repo), "--avvelena"]
        if self.tipo == "controprova":
            repo = root if self.modo == "radice" else w.base(root, self.ref)
            return [sys.executable, "-B", test, "--repo", str(repo), "--baseline-ref", self.ref]
        return [sys.executable, "-B", test, "--repo", str(w.repo)]


class Worker:
    def __init__(self, fixture: Path, n: int) -> None:
        self.dir = fixture / f"w{n}"
        self.home = self.dir / "home"
        self.repo = self.home / ".claude"
        self.tmp = self.dir / "tmp"
        self.salti = self.dir / "salti.txt"
        self.basi: Dict[str, Path] = {}

    def prepara(self, root: Path) -> None:
        self.tmp.mkdir(parents=True, exist_ok=True)
        self.salti.write_text("", encoding="utf-8")
        copia(str(root), str(self.repo))

    def base(self, root: Path, ref: str) -> Path:
        if ref not in self.basi:
            d = self.dir / f"baseline-{ref}"
            d.mkdir(parents=True, exist_ok=True)
            archivio = subprocess.Popen(["git", "-C", str(root), "archive", ref], stdout=subprocess.PIPE)
            subprocess.run(["tar", "-x", "-C", str(d)], stdin=archivio.stdout, check=True)
            archivio.stdout.close()  # type: ignore[union-attr]
            if archivio.wait() != 0:
                raise RuntimeError(f"git archive {ref} fallito")
            self.basi[ref] = d
        return self.basi[ref]

    def env(self) -> Dict[str, str]:
        return dict(os.environ, HOME=str(self.home), USERPROFILE=str(self.home), TMPDIR=str(self.tmp),
                    XDG_CACHE_HOME=str(self.dir / "cache"), ARTURO_SALTI=str(self.salti))


def esegui_uno(lavoro: Lavoro, w: Worker, root: Path, py38: str) -> None:
    inizio = time.monotonic()
    try:
        p = subprocess.run(lavoro.comando(w, root, py38), env=w.env(), cwd=str(w.dir), capture_output=True,
                           text=True, encoding="utf-8", errors="replace", timeout=TETTO)
        lavoro.log = (p.stdout or "") + (p.stderr or "")
        lavoro.rosso = p.returncode != 0
    except subprocess.TimeoutExpired:
        lavoro.log, lavoro.rosso = f"oltre {TETTO} s: fermato", True
    except Exception as e:  # noqa: BLE001 - un lavoro che non parte è un rosso, non un gate rotto
        lavoro.log, lavoro.rosso = f"non partito: {type(e).__name__} {e}", True
    lavoro.secondi = time.monotonic() - inizio
    esito = "ROSSO" if lavoro.rosso else "OK"
    print(f"{esito:5} {lavoro.secondi:6.1f}s  {lavoro.id}", flush=True)


def cartella_comune(root: Path) -> Path:
    r = subprocess.run(["git", "-C", str(root), "rev-parse", "--git-common-dir"], capture_output=True, text=True)
    comune = Path(r.stdout.strip() or ".git")
    return comune if comune.is_absolute() else (root / comune).resolve()


def leggi_tempi(f: Path) -> Dict[str, float]:
    try:
        dati = json.loads(f.read_text(encoding="utf-8"))
        return {str(k): float(v) for k, v in dati.items()}
    except (OSError, ValueError, AttributeError):
        return {}


def lavori_da(a: argparse.Namespace) -> List[Lavoro]:
    lavori = [Lavoro("banco", b) for b in a.banchi]
    if a.py38:
        lavori += [Lavoro("py38", b) for b in a.banchi_py38]
    for riga in a.controprove:
        parti = riga.split()
        lavori.append(Lavoro("controprova", parti[0], parti[1], parti[2] if len(parti) > 2 else ""))
    lavori += [Lavoro("veleno", b) for b in a.veleni]
    return lavori


def esegui(a: argparse.Namespace) -> int:
    root, fixture = Path(a.root).resolve(), Path(a.fixture)
    stato = cartella_comune(root)
    f_tempi, f_rossi = stato / "arturo-gate-tempi.json", stato / "arturo-gate-rossi.txt"
    paralleli, in_fila = lavori_da(a), [Lavoro("banco", b) for b in a.in_fila]
    if a.rossi:
        prima = set(f_rossi.read_text(encoding="utf-8").split()) if f_rossi.is_file() else set()
        if not prima:
            print("PARZIALE: nessun rosso registrato dall'ultimo giro, niente da rifare")
            return 0
        paralleli = [x for x in paralleli if x.id in prima]
        in_fila = [x for x in in_fila if x.id in prima]
    tempi = leggi_tempi(f_tempi)
    # Prima i più lunghi: l'ultimo lavoro lungo partito tardi allunga tutto il giro. Senza tempi, l'ordine
    # delle liste (sort stabile).
    paralleli.sort(key=lambda x: -tempi.get(x.id, 0.0))
    n = max(1, min(a.lavori, len(paralleli) or 1))
    workers = [Worker(fixture, i) for i in range(n)]
    inizio = time.monotonic()
    for w in workers:
        w.prepara(root)
    coda: "queue.Queue[Lavoro]" = queue.Queue()
    for x in paralleli:
        coda.put(x)

    def gira(w: Worker) -> None:
        while True:
            try:
                x = coda.get_nowait()
            except queue.Empty:
                return
            esegui_uno(x, w, root, a.py38)

    fili = [threading.Thread(target=gira, args=(w,)) for w in workers]
    for t in fili:
        t.start()
    for t in fili:
        t.join()
    for x in in_fila:
        esegui_uno(x, workers[0], root, a.py38)

    tutti = paralleli + in_fila
    rossi = [x for x in tutti if x.rosso]
    for x in rossi:
        coda_log = "\n".join(x.log.rstrip().splitlines()[-RIGHE_ROSSO:])
        print(f"\n=== ROSSO {x.id} ({x.secondi:.0f}s)\n{coda_log}")
    # Salti di Windows dei worker nel file che il gate conta.
    salti_gate = os.environ.get("ARTURO_SALTI")
    if salti_gate:
        with open(salti_gate, "a", encoding="utf-8") as out:
            for w in workers:
                out.write(w.salti.read_text(encoding="utf-8") if w.salti.is_file() else "")
    tempi.update({x.id: round(x.secondi, 1) for x in tutti})
    try:
        f_tempi.write_text(json.dumps(tempi, indent=1, sort_keys=True), encoding="utf-8")
        resto = (set(f_rossi.read_text(encoding="utf-8").split()) if a.rossi and f_rossi.is_file() else set())
        resto = (resto - {x.id for x in tutti}) | {x.id for x in rossi}
        f_rossi.write_text("".join(f"{i}\n" for i in sorted(resto)), encoding="utf-8")
    except OSError as e:
        print(f"NOTA: tempi e rossi non salvati ({e})")
    conta: Dict[str, int] = {}
    for x in tutti:
        conta[x.tipo] = conta.get(x.tipo, 0) + 1
    riepilogo = " ".join(f"{k}={v}" for k, v in sorted(conta.items()))
    print(f"\nLAVORI: {riepilogo} worker={n} rossi={len(rossi)} in {time.monotonic() - inizio:.0f}s"
          + (" PARZIALE (solo i rossi del giro prima: non vale per un rilascio)" if a.rossi else ""))
    return 1 if rossi else 0


def main(argv: Optional[List[str]] = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = p.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("copia")
    c.add_argument("sorgente")
    c.add_argument("dest")
    e = sub.add_parser("esegui")
    e.add_argument("--root", required=True)
    e.add_argument("--fixture", required=True)
    e.add_argument("--lavori", type=int, default=max(1, min(4, (os.cpu_count() or 2) // 2)))
    e.add_argument("--rossi", action="store_true")
    e.add_argument("--py38", default="")
    for lista in ("--banchi", "--in-fila", "--banchi-py38", "--controprove", "--veleni"):
        e.add_argument(lista, nargs="*", default=[])
    a = p.parse_args(argv)
    if a.cmd == "copia":
        copia(a.sorgente, a.dest)
        return 0
    return esegui(a)


if __name__ == "__main__":
    sys.exit(main())
