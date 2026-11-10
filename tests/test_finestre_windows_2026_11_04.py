#!/usr/bin/env python3
"""FW01-FW02: su Windows i lanci staccati non aprono finestre di terminale (4/11/2026).

Su un PC Windows si aprivano di continuo finestre di Windows Terminal intitolate git.exe. Causa:
aggiornamenti.py e telemetria.py si staccavano con DETACHED_PROCESS, cioè senza console, e ogni
programma a console lanciato da lì (git, bash, gws) ne apriva una nuova e visibile. gws-esito.py e
gws-token-health.py univano DETACHED_PROCESS e CREATE_NO_WINDOW: Windows ignora CREATE_NO_WINDOW
quando c'è DETACHED_PROCESS. Provato il 4/11/2026: col vecchio flag un git figlio apre la finestra
"C:\\Program Files\\Git\\mingw64\\bin\\git.exe", con CREATE_NO_WINDOW | CREATE_NEW_PROCESS_GROUP no.

FW01 nessun file Python di bin/ e hooks/ passa DETACHED_PROCESS (0x00000008) a creationflags.
FW02 invariante: i quattro lanci staccati su Windows restano in un gruppo nuovo e senza finestra
     (CREATE_NEW_PROCESS_GROUP 0x00000200 e CREATE_NO_WINDOW 0x08000000).

FW03 hooks/statusline.js non lancia con detached: true (review del 7/11/2026, finding 54): su Windows
     Node lo traduce in DETACHED_PROCESS, e i git figli di aggiornamenti.py aprono finestre. Su
     Windows i lanci staccati della barra usano detached: false, cioè CREATE_NO_WINDOW.
FW04 la barra non moltiplica i git status appesi (finding 59): con un git finto che dorme e la cache
     invecchiata a mano, quattro giri della barra lasciano vivo un solo git. Su Windows si salta.

Sulla base efaa296 (dev prima della correzione) sono rossi FW01, FW02, FW03 e FW04.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

CASI = ["FW01", "FW02", "FW03", "FW04"]
DISCRIMINANTI = ["FW01", "FW02", "FW03", "FW04"]
LANCI = ["bin/aggiornamenti.py", "bin/telemetria.py", "hooks/gws-esito.py", "hooks/gws-token-health.py"]
FLAG = re.compile(r"creationflags[\"']?\]?\s*[=:]\s*([^#\n]+)")


def _flag(riga: str) -> str:
    m = FLAG.search(riga)
    return m.group(1) if m else ""


def prova(repo: Path) -> list:
    rossi = []
    staccati = []
    for cartella in ("bin", "hooks"):
        for f in sorted((repo / cartella).glob("*.py")):
            for n, riga in enumerate(f.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
                valore = _flag(riga)
                if re.search(r"0x0*8\b|DETACHED_PROCESS", valore):
                    staccati.append(f"{cartella}/{f.name}:{n}")
    if staccati:
        rossi.append(f"FW01 DETACHED_PROCESS apre una finestra per ogni git figlio: {staccati}")

    mancano = []
    for rel in LANCI:
        f = repo / rel
        testo = f.read_text(encoding="utf-8", errors="replace") if f.exists() else ""
        valori = [_flag(r) for r in testo.splitlines() if _flag(r)]
        if not any(re.search(r"0x0*8000000\b", v) and re.search(r"0x0*200\b", v) for v in valori):
            mancano.append(rel)
    if mancano:
        rossi.append(f"FW02 lancio staccato senza CREATE_NO_WINDOW | CREATE_NEW_PROCESS_GROUP: {mancano}")

    barra = repo / "hooks" / "statusline.js"
    testo = barra.read_text(encoding="utf-8", errors="replace") if barra.exists() else ""
    staccati_js = [n for n, r in enumerate(testo.splitlines(), 1) if re.search(r"detached:\s*true", r)]
    if staccati_js or not re.search(r"process\.platform\s*!==\s*'win32'", testo):
        rossi.append(f"FW03 hooks/statusline.js lancia con detached: true anche su Windows (righe {staccati_js})")
    esito = fw04(barra)
    if esito:
        rossi.append(f"FW04 {esito}")
    return rossi


def fw04(barra: Path) -> str:
    node = shutil.which("node")
    if os.name == "nt" or node is None or not barra.exists():
        return ""  # su Windows niente sh per il git finto; senza node la barra non gira
    with tempfile.TemporaryDirectory(prefix="arturo-fw04-") as d:
        d = Path(d)
        casa, finti, repo = d / "casa", d / "finti", d / "progetto"
        (casa / ".claude").mkdir(parents=True)
        finti.mkdir()
        (repo / ".git").mkdir(parents=True)
        (repo / ".git" / "HEAD").write_text("ref: refs/heads/main\n", encoding="utf-8")
        segno = str(finti / "git")  # pgrep -f lo trova nella riga di comando dell'interprete
        (finti / "git").write_text(f"#!{sys.executable}\nimport time\ntime.sleep(40)\n", encoding="utf-8")
        (finti / "git").chmod(0o755)
        env = dict(os.environ, HOME=str(casa), CLAUDE_CONFIG_DIR=str(casa / ".claude"),
                   PATH=f"{finti}{os.pathsep}{os.environ.get('PATH', '')}")
        entrata = json.dumps({"model": {"display_name": "Opus"}, "workspace": {"current_dir": str(repo)}})
        cache = casa / ".claude" / "cache" / "statusline"
        try:
            for _ in range(4):
                subprocess.run([node, str(barra)], input=entrata, text=True, capture_output=True, env=env, timeout=30)
                time.sleep(0.3)
                vecchio = time.time() - 30  # la cache pare scaduta: senza freno ogni giro rilancia git
                for f in cache.glob("git-*") if cache.is_dir() else []:
                    if not f.name.endswith(".pid"):
                        os.utime(f, (vecchio, vecchio))
            vivi = subprocess.run(["pgrep", "-f", segno], capture_output=True, text=True).stdout.split()
            if len(vivi) > 1:
                return f"quattro giri della barra lasciano {len(vivi)} git status appesi"
            return ""
        finally:
            subprocess.run(["pkill", "-f", segno], capture_output=True)


def main() -> int:
    for flusso in (sys.stdout, sys.stderr):
        if hasattr(flusso, "reconfigure"):
            flusso.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument("--baseline-ref")
    a = parser.parse_args()
    rossi = prova(Path(a.repo))
    if a.baseline_ref:
        codici = [r.split()[0] for r in rossi]
        assert codici == DISCRIMINANTI, f"baseline non discriminante: rossi {codici}, attesi {DISCRIMINANTI}"
        print(f"BASELINE_DISCRIMINANTE={','.join(codici)}")
        return 0
    for r in rossi:
        print("ROSSO", r)
    print(f"finestre di Windows: {len(CASI) - len(rossi)}/{len(CASI)} casi verdi")
    return 1 if rossi else 0


if __name__ == "__main__":
    sys.exit(main())
