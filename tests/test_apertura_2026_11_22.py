#!/usr/bin/env python3
"""Le letture della FASE 4 di /inizio partono insieme (#6368, 22/11/2026).

AP01 arturo apertura lancia insieme le letture che aspettano la rete: le chiamate alla fonte esterna dei
     todo e `claude plugin list` si sovrappongono tutte. Prima /inizio le lanciava in fila, e ognuna
     poteva aspettare la rete fino a 90 s.
AP02 l'uscita ha l'ordine dei comandi in fila: PROGETTO, TODO DEL PROGETTO, TODO DI GENERALE, GIT LOG,
     PANNELLO, con il testo della fonte, il commit e "mod caricato".

Sulla base 2120b4d (il dev prima) il comando non c'è: AP01 e AP02 sono rossi.
Su Windows il banco salta: il claude finto è uno script senza estensione, e lì il PATH non lo trova.
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

CASI = ["AP01", "AP02"]
DISCRIMINANTI = ["AP01", "AP02"]
ATTESA = 2.5
# Ogni chiamata scrive il suo file con inizio e fine: niente scritture concorrenti sullo stesso file.
FONTE = ('import os, sys, time\n'
         'from pathlib import Path\n'
         'log = Path({log!r}) / f"fonte-{{os.getpid()}}"\n'
         'log.write_text(f"inizio {{time.time()}}\\n", encoding="utf-8")\n'
         'time.sleep({attesa})\n'
         'with log.open("a", encoding="utf-8") as f:\n'
         '    f.write(f"fine {{time.time()}}\\n")\n'
         'argomenti = " ".join(sys.argv[1:])\n'
         'print("libro" if argomenti == "progetto" else f"FONTE-{{argomenti}}")\n')
CLAUDE_FINTO = ('#!{py}\n'
                'import os, time\n'
                'from pathlib import Path\n'
                'log = Path({log!r}) / f"claude-{{os.getpid()}}"\n'
                'log.write_text(f"inizio {{time.time()}}\\n", encoding="utf-8")\n'
                'time.sleep({attesa})\n'
                'with log.open("a", encoding="utf-8") as f:\n'
                '    f.write(f"fine {{time.time()}}\\n")\n'
                'print(\'[{{"id": "arturo@arturo", "enabled": true}}]\')\n')


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
        self.progetto = self.home / "Documents" / "ClaudeCode" / "libro"
        self.progetto.mkdir(parents=True)
        git = ["git", "-C", str(self.progetto), "-c", "user.name=Prova", "-c", "user.email=prova@example.invalid"]
        subprocess.run(["git", "init", "-q", "-b", "main", str(self.progetto)], check=True)
        subprocess.run([*git, "commit", "-q", "--allow-empty", "-m", "COMMIT-DEL-LIBRO"], check=True)
        self.log = tmp / "tempi"
        self.log.mkdir()
        fonte = tmp / "fonte.py"
        fonte.write_text(FONTE.format(log=str(self.log), attesa=ATTESA), encoding="utf-8")
        (self.cl / "bin" / "fonte-task.local").write_text(
            f"comando = {Path(sys.executable).as_posix()} {fonte.as_posix()}\n", encoding="utf-8")
        self.finti = tmp / "finti"
        self.finti.mkdir()
        claude = self.finti / "claude"
        claude.write_text(CLAUDE_FINTO.format(py=sys.executable, log=str(self.log), attesa=ATTESA), encoding="utf-8")
        claude.chmod(0o755)

    def env(self) -> dict:
        e = dict(os.environ, HOME=str(self.home), USERPROFILE=str(self.home), ARTURO_TODO=str(self.tmp / "eventi.jsonl"),
                 ARTURO_TELEMETRIA="0", PYTHONDONTWRITEBYTECODE="1", ARTURO_OGGI="2026-11-22",
                 PATH=f"{self.finti}{os.pathsep}{os.environ.get('PATH', '')}")
        e.pop("PROJECTS_BASE", None)
        return e

    def apertura(self) -> subprocess.CompletedProcess:
        return subprocess.run([sys.executable, "-B", str(self.cl / "bin" / "arturo"), "apertura"],
                              capture_output=True, text=True, encoding="utf-8", errors="replace", env=self.env(),
                              timeout=120, cwd=str(self.progetto))


def prova(lab: Lab) -> list:
    rossi = []
    r = lab.apertura()
    tempi = {}
    for f in sorted(lab.log.iterdir()):
        try:
            tempi[f.name] = {k: float(v) for k, v in (x.split() for x in f.read_text(encoding="utf-8").splitlines())}
        except (OSError, ValueError):
            pass
    inizi = [t["inizio"] for t in tempi.values() if "inizio" in t]
    fini = [t["fine"] for t in tempi.values() if "fine" in t]
    fonti = [n for n in tempi if n.startswith("fonte-")]
    claude = [n for n in tempi if n.startswith("claude-")]
    # AP01: tre letture della fonte (progetto, todo del progetto, generale) e claude, tutte sovrapposte.
    insieme = bool(inizi) and len(fini) == len(inizi) and max(inizi) < min(fini)
    if r.returncode != 0 or len(fonti) < 3 or len(claude) != 1 or not insieme:
        rossi.append(f"AP01 letture insieme: rc={r.returncode} fonte={len(fonti)} claude={len(claude)} "
                     f"sovrapposte={insieme} {r.stderr[-200:]!r}")
    # AP02
    out = r.stdout
    attese = ["PROGETTO libro", "TODO DEL PROGETTO", "FONTE---progetto .", "TODO DI GENERALE",
              "FONTE---progetto generale", "GIT LOG", "COMMIT-DEL-LIBRO", "PANNELLO", "mod caricato"]
    posti = [out.find(a) for a in attese]
    if r.returncode != 0 or -1 in posti or posti != sorted(posti):
        mancanti = [a for a, p in zip(attese, posti) if p == -1]
        rossi.append(f"AP02 uscita in ordine: rc={r.returncode} mancanti={mancanti} {out[-400:]!r} {r.stderr[-200:]!r}")
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
        print("letture dell'apertura insieme: saltato su Windows")
        return 0
    with tempfile.TemporaryDirectory(prefix="arturo-ap-") as tmp:
        rossi = prova(Lab(Path(argomenti.repo), argomenti.baseline_ref, Path(tmp)))
    if argomenti.baseline_ref:
        codici = [r.split()[0] for r in rossi]
        assert codici == DISCRIMINANTI, f"baseline non discriminante: rossi {codici}, attesi {DISCRIMINANTI}"
        print(f"BASELINE_DISCRIMINANTE={','.join(codici)}")
        return 0
    for r in rossi:
        print("ROSSO", r)
    print(f"letture dell'apertura insieme: {len(CASI) - len(rossi)}/{len(CASI)} casi verdi")
    return 1 if rossi else 0


if __name__ == "__main__":
    sys.exit(main())
