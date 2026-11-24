#!/usr/bin/env python3
"""SO01-SO05: bin/shell-orfane.py chiude le shell dei comandi di Claude rimaste senza sessione (24/11/2026).

Il 24/11 una shell di una sessione chiusa alle 11:24 leggeva un log su un altro computer ogni 15 minuti fino alle 23.
Dal 13/11 su un Mac erano 23: Claude Code non spegne le shell in background quando la sessione si chiude.

SO01 un'orfana (padre launchd) si chiude col suo sleep, e il registro ne scrive una riga;
SO02 una shell col padre di Claude resta accesa;
SO03 un'orfana col segno arturo:tieni resta accesa;
SO04 un'orfana più giovane della soglia resta accesa;
SO05 hooks/session-start.sh lancia la pulizia staccata, con stdout e stderr chiusi.

Invariante (verde anche sulla base): nessuno. Sulla base 9d460bb sono rossi tutti: lo script non c'è.
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

CASI = ["SO01", "SO02", "SO03", "SO04", "SO05"]
DISCRIMINANTI = CASI


def vivo(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


def comando(tmp: Path, nome: str, extra: str = "") -> str:
    return f"source {tmp}/shell-snapshots/snapshot-{nome}.sh 2>/dev/null || true && sleep 300; true {extra}"


def orfana(tmp: Path, nome: str, extra: str = "") -> int:
    """Shell capogruppo il cui padre esce subito: passa a launchd come una shell di una sessione chiusa."""
    pidfile = tmp / f"{nome}.pid"
    lancia = ("import subprocess,sys;"
              f"p=subprocess.Popen(['/bin/zsh','-c',{comando(tmp, nome, extra)!r}],start_new_session=True,"
              "stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);"
              f"open({str(pidfile)!r},'w').write(str(p.pid))")
    subprocess.run([sys.executable, "-c", lancia], check=True)
    return int(pidfile.read_text())


def con_padre_claude(tmp: Path, nome: str) -> tuple[subprocess.Popen, int]:
    pidfile = tmp / f"{nome}.pid"
    corpo = f"/bin/zsh -c {comando(tmp, nome)!r} & echo $! > {pidfile}; wait"
    padre = subprocess.Popen(["claude-finto", "-c", corpo], executable="/bin/sh", start_new_session=True,
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(50):
        if pidfile.exists() and pidfile.read_text().strip():
            break
        time.sleep(0.1)
    return padre, int(pidfile.read_text())


def figli(pid: int) -> list[int]:
    out = subprocess.run(["pgrep", "-P", str(pid)], capture_output=True, text=True).stdout
    return [int(x) for x in out.split()]


def lancia_script(script: Path, tmp: Path, eta: str = "0") -> None:
    env = dict(os.environ, ARTURO_ORFANE_ETA_S=eta, ARTURO_ORFANE_LOG=str(tmp / "orfane.log"),
               ARTURO_ORFANE_FILTRO=str(tmp))   # mai le shell vere della macchina, neanche col veleno
    subprocess.run([sys.executable, str(script), "chiudi"], env=env, check=True, timeout=30)


def caso_avvio(repo: Path) -> list[str]:
    avvio = (repo / "hooks" / "session-start.sh").read_text(encoding="utf-8")
    riga = next((r for r in avvio.splitlines() if "shell-orfane.py" in r and not r.lstrip().startswith("#")), "")
    if not riga or "chiudi" not in riga or "&" not in riga or ">/dev/null 2>&1" not in riga:
        return [f"SO05 session-start.sh non lancia la pulizia staccata: {riga!r}"]
    return []


def prova(repo: Path) -> list[str]:
    script = repo / "bin" / "shell-orfane.py"
    if not script.exists():
        return [f"{c} manca bin/shell-orfane.py" for c in CASI]
    if os.name == "nt":
        # Su Windows lo script esce subito: le shell di Claude lì non restano orfane allo stesso modo.
        return caso_avvio(repo)
    rossi: list[str] = []
    tmp = Path(tempfile.mkdtemp(prefix="arturo-orfane-"))
    da_spegnere: list[int] = []
    padre = None
    try:
        o1 = orfana(tmp, "so01")
        time.sleep(0.5)
        sonno = figli(o1)
        da_spegnere += [o1, *sonno]
        o3 = orfana(tmp, "so03", "# arturo:tieni")
        padre, o2 = con_padre_claude(tmp, "so02")
        da_spegnere += [o2, o3]
        time.sleep(0.5)
        lancia_script(script, tmp)
        log = (tmp / "orfane.log").read_text() if (tmp / "orfane.log").exists() else ""
        if vivo(o1) or any(vivo(s) for s in sonno) or not sonno:
            rossi.append(f"SO01 orfana o il suo sleep ancora vivi (pid {o1}, sleep {sonno})")
        elif f"chiusa pid {o1}" not in log:
            rossi.append(f"SO01 manca la riga nel registro: {log!r}")
        if not vivo(o2):
            rossi.append("SO02 chiusa una shell col padre di Claude")
        if not vivo(o3):
            rossi.append("SO03 chiusa un'orfana col segno arturo:tieni")
        o4 = orfana(tmp, "so04")
        da_spegnere.append(o4)
        time.sleep(0.3)
        lancia_script(script, tmp, eta="3600")
        if not vivo(o4):
            rossi.append("SO04 chiusa un'orfana più giovane della soglia")
        rossi += caso_avvio(repo)
    finally:
        for pid in da_spegnere:
            try:
                os.kill(pid, 9)
            except OSError:
                pass
        if padre:
            padre.kill()
    return rossi


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument("--baseline-ref")
    argomenti = parser.parse_args()
    rossi = prova(Path(argomenti.repo))
    if argomenti.baseline_ref:
        codici = [r.split()[0] for r in rossi]
        assert codici == DISCRIMINANTI, f"baseline non discriminante: rossi {codici}, attesi {DISCRIMINANTI}"
        print(f"BASELINE_DISCRIMINANTE={','.join(codici)}")
        return 0
    for r in rossi:
        print("ROSSO", r)
    print(f"shell orfane: {len(CASI) - len(rossi)}/{len(CASI)} casi verdi")
    return 1 if rossi else 0


if __name__ == "__main__":
    sys.exit(main())
