#!/usr/bin/env python3
"""I controlli indipendenti di /inizio girano insieme (#6317, 22/11/2026).

PA01 arturo contesto legge git mentre la fonte esterna dei todo risponde: la maggioranza delle chiamate a git
     cade prima della fine della lettura della fonte. Prima git partiva solo dopo la fonte, che può
     aspettare fino a 90 s la rete.
PA02 l'uscita resta la stessa: GIT viene prima dei todo, i todo della fonte ci sono.

Sulla base 300567c (il dev prima) è rosso PA01; PA02 è l'invariante.
Su Windows il banco salta: il git finto è uno script senza estensione, e lì il PATH non lo trova.
"""
from __future__ import annotations

import argparse
import io
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path

CASI = ["PA01", "PA02"]
DISCRIMINANTI = ["PA01"]
FONTE = ('import json, sys, time\n'
         'from pathlib import Path\n'
         'log = Path(sys.argv[0] + ".tempi")\n'
         'log.write_text(f"inizio {time.time()}\\n", encoding="utf-8")\n'
         'time.sleep(1.5)\n'
         'with log.open("a", encoding="utf-8") as f:\n'
         '    f.write(f"fine {time.time()}\\n")\n'
         'print(json.dumps({"gruppi": [{"tipo": "io", "todo": [{"id": 77, "titolo": "TODO-DALLA-FONTE"}]}],\n'
         '                  "chiusi_todo": []}))\n')
# Il git finto annota l'ora e passa la mano al git vero.
GIT_FINTO = ('#!{py}\n'
             'import os, sys, time\n'
             'with open({log!r}, "a", encoding="utf-8") as f:\n'
             '    f.write(f"{{time.time()}}\\n")\n'
             'os.execv({vero!r}, [{vero!r}, *sys.argv[1:]])\n')


class Lab:
    def __init__(self, repo: Path, ref: str | None, tmp: Path):
        self.tmp, self.home = tmp, tmp / "home"
        self.cl = self.home / ".claude"
        self.cl.mkdir(parents=True)
        if ref:
            dati = subprocess.run(["git", "-C", str(repo), "archive", ref, "bin", "hooks/radici.py"],
                                  capture_output=True, check=True).stdout
            with tarfile.open(fileobj=io.BytesIO(dati)) as archivio:
                archivio.extractall(self.cl, **({"filter": "data"} if hasattr(tarfile, "data_filter") else {}))
        else:
            shutil.copytree(str(repo / "bin"), str(self.cl / "bin"), ignore=shutil.ignore_patterns("__pycache__", "*.local"))
            (self.cl / "hooks").mkdir()
            shutil.copy2(str(repo / "hooks" / "radici.py"), str(self.cl / "hooks" / "radici.py"))
        h = self.cl / "data" / "handoffs" / "libro" / "HANDOFF_2026-11-21_10-00.md"
        h.parent.mkdir(parents=True)
        h.write_text("# Session Handoff - 2026-11-21 10:00\n## Progetto\n- Nome: libro / Branch: main\n", encoding="utf-8")
        progetto = self.home / "Documents" / "ClaudeCode" / "libro"
        progetto.mkdir(parents=True)
        subprocess.run(["git", "init", "-q", "-b", "main", str(progetto)], check=True)
        self.fonte = tmp / "fonte.py"
        self.fonte.write_text(FONTE, encoding="utf-8")
        (self.cl / "bin" / "fonte-task.local").write_text(
            f"comando = {Path(sys.executable).as_posix()} {self.fonte.as_posix()}\n", encoding="utf-8")
        self.finti = tmp / "finti"
        self.finti.mkdir()
        self.log_git = tmp / "git.tempi"
        finto = self.finti / "git"
        finto.write_text(GIT_FINTO.format(py=sys.executable, log=str(self.log_git), vero=shutil.which("git")),
                         encoding="utf-8")
        finto.chmod(0o755)

    def env(self) -> dict:
        e = dict(os.environ, HOME=str(self.home), USERPROFILE=str(self.home), ARTURO_TODO=str(self.tmp / "eventi.jsonl"),
                 ARTURO_TELEMETRIA="0", PYTHONDONTWRITEBYTECODE="1", ARTURO_OGGI="2026-11-22",
                 PATH=f"{self.finti}{os.pathsep}{os.environ.get('PATH', '')}")
        e.pop("PROJECTS_BASE", None)
        return e

    def contesto(self) -> subprocess.CompletedProcess:
        return subprocess.run([sys.executable, "-B", str(self.cl / "bin" / "arturo"), "contesto", "libro"],
                              capture_output=True, text=True, encoding="utf-8", errors="replace", env=self.env(),
                              timeout=120, cwd=str(self.home))


def prova(lab: Lab) -> list:
    rossi = []
    r = lab.contesto()
    try:
        tempi = dict(x.split() for x in Path(str(lab.fonte) + ".tempi").read_text(encoding="utf-8").splitlines())
        inizio, fine = float(tempi["inizio"]), float(tempi["fine"])
    except (OSError, ValueError, KeyError):
        inizio = fine = None
    try:
        chiamate = [float(x) for x in lab.log_git.read_text(encoding="utf-8").split()]
    except (OSError, ValueError):
        chiamate = []
    # PA01: la maggioranza delle chiamate prima della fine della fonte. "Fra inizio e fine" non bastava: la fonte
    # scrive l'inizio dopo l'avvio di Python, e sul runner Linux della CI le 11 chiamate finivano prima (#6453).
    # Su 300567c 2 chiamate cadono prima della fonte e 9 dopo la fine; oggi tutte e 11 prima della fine.
    prima = [t for t in chiamate if fine is not None and t < fine]
    if r.returncode != 0 or not chiamate or len(prima) * 2 <= len(chiamate):
        rossi.append(f"PA01 git insieme alla fonte: rc={r.returncode} fonte={inizio}..{fine} "
                     f"git={len(chiamate)} chiamate, {len(prima)} prima della fine della fonte")
    # PA02
    out = r.stdout
    if r.returncode != 0 or "TODO-DALLA-FONTE" not in out or "GIT" not in out \
            or out.find("GIT") > out.find("TODO-DALLA-FONTE"):
        rossi.append(f"PA02 uscita invariata: rc={r.returncode} {out[-300:]!r} {r.stderr[-200:]!r}")
    return rossi


def main() -> int:
    for flusso in (sys.stdout, sys.stderr):  # su Windows la pipe è in cp1252
        if hasattr(flusso, "reconfigure"):
            flusso.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument("--baseline-ref")
    argomenti = parser.parse_args()
    if os.name == "nt":
        print("controlli in parallelo: saltato su Windows")
        return 0
    with tempfile.TemporaryDirectory(prefix="arturo-pa-") as tmp:
        rossi = prova(Lab(Path(argomenti.repo), argomenti.baseline_ref, Path(tmp)))
    if argomenti.baseline_ref:
        codici = [r.split()[0] for r in rossi]
        assert codici == DISCRIMINANTI, f"baseline non discriminante: rossi {codici}, attesi {DISCRIMINANTI}"
        print(f"BASELINE_DISCRIMINANTE={','.join(codici)}")
        return 0
    for r in rossi:
        print("ROSSO", r)
    print(f"controlli in parallelo: {len(CASI) - len(rossi)}/{len(CASI)} casi verdi")
    return 1 if rossi else 0


if __name__ == "__main__":
    sys.exit(main())
