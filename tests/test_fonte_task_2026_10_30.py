#!/usr/bin/env python3
"""La fonte dei task fuori da Arturo: bin/fonte-task.local (#4291, F0 L4).

FT01 con bin/fonte-task.local `arturo todo <argomenti>` lancia il programma della fonte con gli stessi
     argomenti e ne restituisce il codice d'uscita (3 = fonte giù).
FT02 senza il file `arturo todo` usa l'archivio di Arturo come prima.
FT03 arturo contesto mostra i todo e i chiusi dalla fonte esterna.
FT04 se la fonte non risponde, arturo contesto mostra i task dell'ultimo handoff con NON VERIFICATO, mai
     "nessuno".
FT05 arturo contesto --stdin legge gli argomenti da stdin e stampa il compito, senza eseguire niente.

Sulla base ba61272 (il dev prima di L4) sono rossi tutti i casi tranne FT02, che è l'invariante.
"""
from __future__ import annotations

import argparse
import io
import json
import os
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path

CASI = ["FT01", "FT02", "FT03", "FT04", "FT05"]
DISCRIMINANTI = ["FT01", "FT03", "FT04", "FT05"]
SU = ('import json, sys\n'
      'open(sys.argv[0] + ".argomenti", "w", encoding="utf-8").write(json.dumps(sys.argv[1:]))\n'
      'if "aggiungi" in sys.argv:\n'
      '    sys.exit(3)\n'
      'print(json.dumps({"gruppi": [{"tipo": "io", "todo": [{"id": 77, "titolo": "TODO-DALLA-FONTE"}]}],\n'
      '                  "chiusi_todo": [{"id": 76, "titolo": "CHIUSO-DALLA-FONTE", "stato": "fatto",\n'
      '                                   "chiuso": "2026-10-30T20:00"}]}))\n')
GIU = 'import sys\nprint("servizio giù", file=sys.stderr)\nsys.exit(3)\n'
HANDOFF = ("# Session Handoff - 2026-10-29 10:00\n## Progetto\n- Nome: libro / Branch: main\n\n"
           "## Task Pendenti\n| # | ID | Progetto | Priorità | Task | Status | Descrizione | Chi |\n"
           "|---|---|---|---|---|---|---|---|\n"
           "| 1 | #55 | libro | alta | TASK-DALL-HANDOFF | pending | d | Claude |\n")


class Lab:
    def __init__(self, repo: Path, ref: str | None, tmp: Path):
        self.tmp, self.home = tmp, tmp / "home"
        self.cl = self.home / ".claude"
        self.cl.mkdir(parents=True)
        if ref:
            dati = subprocess.run(["git", "-C", str(repo), "archive", ref, "bin"], capture_output=True, check=True).stdout
            with tarfile.open(fileobj=io.BytesIO(dati)) as archivio:
                archivio.extractall(self.cl, **({"filter": "data"} if hasattr(tarfile, "data_filter") else {}))
        else:
            import shutil
            shutil.copytree(str(repo / "bin"), str(self.cl / "bin"), ignore=shutil.ignore_patterns("__pycache__", "*.local"))
        h = self.cl / "data" / "handoffs" / "libro" / "HANDOFF_2026-10-29_10-00.md"
        h.parent.mkdir(parents=True)
        h.write_text(HANDOFF, encoding="utf-8")
        (self.home / "Documents" / "ClaudeCode" / "libro").mkdir(parents=True)
        self.fonte = tmp / "fonte.py"

    def env(self) -> dict:
        e = dict(os.environ, HOME=str(self.home), USERPROFILE=str(self.home), ARTURO_TODO=str(self.tmp / "eventi.jsonl"),
                 ARTURO_TELEMETRIA="0", PYTHONDONTWRITEBYTECODE="1", ARTURO_OGGI="2026-10-30")
        e.pop("PROJECTS_BASE", None)
        return e

    def locale(self, codice: str | None) -> None:
        f = self.cl / "bin" / "fonte-task.local"
        if codice is None:
            f.unlink(missing_ok=True)
            return
        self.fonte.write_text(codice, encoding="utf-8")
        f.write_text(f"# la mia fonte\ncomando = {Path(sys.executable).as_posix()} {self.fonte.as_posix()}\n", encoding="utf-8")

    def arturo(self, *a: str, entrata: str | None = None) -> subprocess.CompletedProcess:
        return subprocess.run([sys.executable, "-B", str(self.cl / "bin" / "arturo"), *a], capture_output=True, text=True,
                              encoding="utf-8", errors="replace", env=self.env(), timeout=120, input=entrata,
                              cwd=str(self.home))


def prova(lab: Lab) -> list:
    rossi = []
    # FT01
    lab.locale(SU)
    r = lab.arturo("todo", "--progetto", "libro", "--json")
    try:
        visti = json.loads(Path(str(lab.fonte) + ".argomenti").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        visti = None
    a = lab.arturo("todo", "aggiungi", "Nuovo task")
    if r.returncode != 0 or "TODO-DALLA-FONTE" not in r.stdout or visti != ["--progetto", "libro", "--json"] \
            or a.returncode != 3:
        rossi.append(f"FT01 instradamento: rc={r.returncode} argomenti={visti} aggiungi rc={a.returncode}")
    # FT02
    lab.locale(None)
    r1 = lab.arturo("todo", "aggiungi", "Rileggere il capitolo", "--progetto", "libro", "--chi", "io")
    r2 = lab.arturo("todo", "--progetto", "libro")
    if r1.returncode != 0 or "Rileggere il capitolo" not in r2.stdout:
        rossi.append(f"FT02 archivio di Arturo: rc={r1.returncode} {r1.stderr.strip()[-120:]!r} {r2.stdout[-120:]!r}")
    # FT03
    lab.locale(SU)
    r = lab.arturo("contesto", "libro")
    if r.returncode != 0 or "TODO-DALLA-FONTE" not in r.stdout or "CHIUSO-DALLA-FONTE" not in r.stdout \
            or "Rileggere il capitolo" in r.stdout:
        rossi.append(f"FT03 contesto dalla fonte: rc={r.returncode} {r.stdout[-300:]!r}")
    # FT04
    lab.locale(GIU)
    r = lab.arturo("contesto", "libro")
    if r.returncode != 0 or "NON VERIFICATO" not in r.stdout or "TASK-DALL-HANDOFF" not in r.stdout \
            or "servizio giù" not in r.stdout:
        rossi.append(f"FT04 fonte giù: rc={r.returncode} {r.stdout[-300:]!r}")
    # FT05
    lab.locale(None)
    trappola = lab.tmp / "ESEGUITO"
    r = lab.arturo("contesto", "--stdin", entrata=f'libro -- rileggere "tutto" $(touch {trappola.as_posix()}) # fine\n')
    if r.returncode != 0 or "PROGETTO libro" not in r.stdout or 'compito: rileggere "tutto"' not in r.stdout \
            or trappola.exists():
        rossi.append(f"FT05 stdin: rc={r.returncode} {r.stdout[:200]!r} {r.stderr[-160:]!r}")
    return rossi


def main() -> int:
    for flusso in (sys.stdout, sys.stderr):  # su Windows la pipe è in cp1252
        if hasattr(flusso, "reconfigure"):
            flusso.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument("--baseline-ref")
    argomenti = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix="arturo-ft-") as tmp:
        rossi = prova(Lab(Path(argomenti.repo), argomenti.baseline_ref, Path(tmp)))
    if argomenti.baseline_ref:
        codici = [r.split()[0] for r in rossi]
        assert codici == DISCRIMINANTI, f"baseline non discriminante: rossi {codici}, attesi {DISCRIMINANTI}"
        print(f"BASELINE_DISCRIMINANTE={','.join(codici)}")
        return 0
    for r in rossi:
        print("ROSSO", r)
    print(f"fonte dei task: {len(CASI) - len(rossi)}/{len(CASI)} casi verdi")
    return 1 if rossi else 0


if __name__ == "__main__":
    sys.exit(main())
