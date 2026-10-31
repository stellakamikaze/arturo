#!/usr/bin/env python3
"""GL01-GL06: un solo gate completo per macchina (bin/gate-lucchetto.sh, 31/10/2026, #4360).

Il 30-31/10 sul MacBook Air due tests/verifica-allineamento.sh in parallelo hanno dato rossi che da
soli passano. Il gate prende un lucchetto all'avvio: il secondo aspetta in fila e dice chi lo tiene.

GL01 lucchetto libero: si prende, "chi" porta il pid, si lascia all'uscita.
GL02 lucchetto preso: il secondo aspetta, nomina il pid di chi lo tiene, parte dopo.
GL03 lucchetto rimasto da un gate che non gira più: si toglie e si prende.
GL04 attesa scaduta: rosso, col pid di chi lo tiene.
GL05 lasciare non toglie il lucchetto di un altro gate.
GL06 il gate prende il lucchetto prima della cartella di prova e lo lascia all'uscita.

Veleno interno: GL02 e GL04 girano anche contro un lucchetto finto che non blocca, e devono dare
rosso col loro codice. Sulla base 5122a03 è rosso GL06: il gate non aveva il lucchetto.
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

CASI = [f"GL{n:02d}" for n in range(1, 7)]
DISCRIMINANTI = ["GL06"]
BASH = shutil.which("bash") or "bash"
FINTO = """
GATE_LUCCHETTO_DIR=""
gate_lucchetto_prendi() { mkdir -p "$1"; printf '%s, dalle 00:00:00, finto\\n' "$$" > "$1/chi"; GATE_LUCCHETTO_DIR=$1; }
gate_lucchetto_lascia() { rm -rf "$GATE_LUCCHETTO_DIR"; }
"""


def bash(script: Path, corpo: str, env_extra: dict[str, str] | None = None, timeout: int = 60):
    import os
    env = {**os.environ, "ARTURO_GATE_PASSO": "0.2", **(env_extra or {})}
    return subprocess.run([BASH, "-c", f'source "{script.as_posix()}"\n{corpo}'], capture_output=True,
                          text=True, encoding="utf-8", errors="replace", env=env, timeout=timeout)


def tenitore(script: Path, lucchetto: Path, secondi: float):
    """Un gate finto che prende il lucchetto e lo tiene per `secondi`. Ritorna (processo, pid bash)."""
    p = subprocess.Popen([BASH, "-c", f'source "{script.as_posix()}"\n'
                          f'gate_lucchetto_prendi "{lucchetto.as_posix()}" tenitore || exit 1\n'
                          f'trap gate_lucchetto_lascia EXIT\necho "PRESO $$"\nsleep {secondi}\n'],
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8")
    riga = p.stdout.readline().strip()
    assert riga.startswith("PRESO "), f"il tenitore non ha preso il lucchetto: {riga!r} {p.stderr.read()!r}"
    return p, riga.split()[1]


def caso_gl02(script: Path, tmp: Path) -> str | None:
    lucchetto = tmp / "gl02.lucchetto"
    p, pid = tenitore(script, lucchetto, 3)
    try:
        t0 = time.monotonic()
        r = bash(script, f'gate_lucchetto_prendi "{lucchetto.as_posix()}" secondo && cat "{lucchetto.as_posix()}/chi"')
        durata = time.monotonic() - t0
    finally:
        p.wait(timeout=30)
    if r.returncode != 0:
        return f"GL02 il secondo gate non ha preso il lucchetto: rc={r.returncode} {r.stderr!r}"
    if f"pid {pid}" not in r.stderr:
        return f"GL02 il secondo gate non dice chi tiene il lucchetto (pid {pid}): {r.stderr!r}"
    if durata < 1.5:
        return f"GL02 il secondo gate non ha aspettato: partito dopo {durata:.1f}s col primo ancora acceso"
    if "secondo" not in r.stdout:
        return f"GL02 dopo l'attesa il lucchetto non è del secondo gate: {r.stdout!r}"
    return None


def caso_gl04(script: Path, tmp: Path) -> str | None:
    lucchetto = tmp / "gl04.lucchetto"
    p, pid = tenitore(script, lucchetto, 4)
    try:
        r = bash(script, f'gate_lucchetto_prendi "{lucchetto.as_posix()}" secondo', {"ARTURO_GATE_ATTESA": "1"})
    finally:
        p.wait(timeout=30)
    if r.returncode == 0:
        return "GL04 con l'attesa scaduta il secondo gate parte lo stesso"
    if "FAIL" not in r.stderr or f"pid {pid}" not in r.stderr:
        return f"GL04 l'attesa scaduta non dice chi tiene il lucchetto (pid {pid}): {r.stderr!r}"
    return None


def prova_script(script: Path) -> list[str]:
    rossi: list[str] = []
    with tempfile.TemporaryDirectory() as t:
        tmp = Path(t)
        # GL01
        l1 = tmp / "gl01.lucchetto"
        r = bash(script, f'gate_lucchetto_prendi "{l1.as_posix()}" primo || exit 9\n'
                         f'cat "{l1.as_posix()}/chi"; echo "PID $$"\ngate_lucchetto_lascia\n'
                         f'[ -e "{l1.as_posix()}" ] && echo RESTA || echo TOLTO')
        righe = r.stdout.split("\n")
        pid = next((x.split()[1] for x in righe if x.startswith("PID ")), "?")
        if r.returncode != 0 or not r.stdout.startswith(f"{pid},") or "TOLTO" not in r.stdout:
            rossi.append(f"GL01 lucchetto libero: rc={r.returncode} {r.stdout!r} {r.stderr!r}")
        # GL02
        e = caso_gl02(script, tmp)
        if e:
            rossi.append(e)
        # GL03: un pid che non gira (un bash già uscito)
        morto = subprocess.run([BASH, "-c", "echo $$"], capture_output=True, text=True).stdout.strip()
        l3 = tmp / "gl03.lucchetto"
        l3.mkdir()
        (l3 / "chi").write_text(f"{morto}, dalle 03:00:00, gate spento\n", encoding="utf-8")
        r = bash(script, f'gate_lucchetto_prendi "{l3.as_posix()}" nuovo && cat "{l3.as_posix()}/chi"',
                 {"ARTURO_GATE_ATTESA": "5"})
        if r.returncode != 0 or "nuovo" not in r.stdout or "non gira più" not in r.stderr:
            rossi.append(f"GL03 lucchetto rimasto: rc={r.returncode} {r.stdout!r} {r.stderr!r}")
        # GL04
        e = caso_gl04(script, tmp)
        if e:
            rossi.append(e)
        # GL05: il lucchetto di un altro gate resta
        l5 = tmp / "gl05.lucchetto"
        l5.mkdir()
        (l5 / "chi").write_text("1, dalle 05:00:00, altro gate\n", encoding="utf-8")
        r = bash(script, f'GATE_LUCCHETTO_DIR="{l5.as_posix()}"\ngate_lucchetto_lascia')
        if not (l5 / "chi").exists():
            rossi.append("GL05 lasciare ha tolto il lucchetto di un altro gate")
    return rossi


def prova_gate(testo: str) -> str | None:
    righe = testo.splitlines()
    try:
        sorgente = next(i for i, x in enumerate(righe) if "gate-lucchetto.sh" in x and x.lstrip().startswith("source"))
        prende = next(i for i, x in enumerate(righe) if x.lstrip().startswith("gate_lucchetto_prendi"))
        fixture = next(i for i, x in enumerate(righe) if x.startswith("FIXTURE=$(mktemp"))
        home = next(i for i, x in enumerate(righe) if x.startswith('HOME="$FIXTURE'))
    except StopIteration:
        return "GL06 il gate non prende il lucchetto (manca source di bin/gate-lucchetto.sh o gate_lucchetto_prendi)"
    if not sorgente < prende < fixture < home:
        return "GL06 il gate prende il lucchetto dopo aver cambiato cartella di prova o HOME"
    trappole = [x for x in righe[fixture:fixture + 3] if x.startswith("trap ") and "EXIT" in x]
    if not trappole or "gate_lucchetto_lascia" not in trappole[0]:
        return "GL06 la trap EXIT dopo la cartella di prova non lascia il lucchetto"
    return None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument("--baseline-ref")
    argomenti = parser.parse_args()
    repo = Path(argomenti.repo)
    if argomenti.baseline_ref:
        vecchio = subprocess.run(["git", "-C", str(repo), "show", f"{argomenti.baseline_ref}:tests/verifica-allineamento.sh"],
                                 capture_output=True, text=True, encoding="utf-8", check=True).stdout
        e = prova_gate(vecchio)
        codici = [e.split()[0]] if e else []
        assert codici == DISCRIMINANTI, f"baseline non discriminante: rossi {codici}, attesi {DISCRIMINANTI}"
        print(f"BASELINE_DISCRIMINANTE={','.join(codici)}")
        return 0
    rossi = prova_script(repo / "bin" / "gate-lucchetto.sh")
    e = prova_gate((repo / "tests" / "verifica-allineamento.sh").read_text(encoding="utf-8"))
    if e:
        rossi.append(e)
    # Veleno: un lucchetto che non blocca deve far rosso GL02 e GL04.
    with tempfile.TemporaryDirectory() as t:
        finto = Path(t) / "gate-lucchetto.sh"
        finto.write_text(FINTO, encoding="utf-8")
        tmp = Path(t)
        for codice, caso in (("GL02", caso_gl02), ("GL04", caso_gl04)):
            esito = caso(finto, tmp)
            if not esito or not esito.startswith(codice):
                rossi.append(f"{codice} veleno: col lucchetto finto il caso resta verde ({esito!r})")
    for r in rossi:
        print("ROSSO", r)
    print(f"lucchetto del gate: {len(CASI) - len({r.split()[0] for r in rossi})}/{len(CASI)} casi verdi, veleno provato")
    return 1 if rossi else 0


if __name__ == "__main__":
    sys.exit(main())
