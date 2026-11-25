#!/usr/bin/env python3
"""HW01-HW05, HW08-HW09: lo stato verso Herdr su Windows (hooks/herdr-stato-windows.py, 25/11/2026, #5639).

Su Windows Claude Code lancia gli hook senza terminale di controllo: herdr-stato.sh non trovava dove scrivere
e lo stato in Herdr restava vuoto. Ora su Windows (OS=Windows_NT) lo sh passa all'aiutante Python, che sale
fino a claude.exe e scrive sulla sua console. Prova dal vero su un PC Windows, sessione prova-5639, 25/11/2026:
due turni, `working` poi `blocked` in Herdr, schermo pulito.

HW01 con OS=Windows_NT lo sh chiama python con l'aiutante accanto e lo stato, anche con le \\ nel percorso.
HW02 se python non parte (rimando del Microsoft Store, 9009) o è di MSYS2 (l'aiutante esce 2), lo sh prova python3.
HW03 fuori da Herdr (senza HC_TERMINAL_ID) e con uno stato sconosciuto lo sh non chiama nessun python.
HW04 scegli() trova claude.exe fra gli antenati, e si ferma su un PID riusato (padre nato dopo il figlio).
HW05 fuori da Windows l'aiutante esce 2 senza scrivere niente, così lo sh prova l'interprete dopo.
HW08 in_ordine() scarta uno stato più vecchio dell'ultimo scritto, e non segna l'ora se la scrittura fallisce.
HW09 sali() dà anche il figlio di claude.exe, e con un'ora illeggibile confronta l'ultima ora letta più in basso.

HW06 e HW07 sono della PR #50 (ramo dopo questo). HW08-HW09 vengono dalla revisione della PR #49 (25/11/2026).

Sulla base 75082b4 (dev prima della modifica) sono rossi tutti: l'aiutante non c'è.
Solo libreria standard. Nessun modello.
"""
from __future__ import annotations

import argparse
import importlib.util
import os
import shutil
import stat
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from salti_windows import dichiara  # noqa: E402  (i salti contano nell'esito del gate)

CASI = ["HW01", "HW02", "HW03", "HW04", "HW05", "HW08", "HW09"]
DISCRIMINANTI = CASI

FINTO = "#!/bin/sh\nprintf '%s|%s|%s\\n' \"$(basename \"$0\")\" \"$1\" \"$2\" >> \"$REGISTRO\"\nexit {rc}\n"


def _python_finti(cartella: Path, rc_py: int) -> None:
    for nome, rc in (("python", rc_py), ("python3", 0)):
        p = cartella / nome
        p.write_text(FINTO.format(rc=rc), encoding="utf-8")
        p.chmod(p.stat().st_mode | stat.S_IEXEC)


def _lancia(script: str, stato: str, d: Path, rc_py: int = 0, hc: str = "t1") -> list:
    finti = d / "finti"
    finti.mkdir(exist_ok=True)
    _python_finti(finti, rc_py)
    registro = d / "registro.txt"
    registro.write_text("", encoding="utf-8")
    env = {"PATH": f"{finti}:/usr/bin:/bin", "OS": "Windows_NT", "REGISTRO": str(registro), "HC_TERMINAL_ID": hc}
    subprocess.run(["sh", script, stato], input=b"{}", env=env, capture_output=True, timeout=20)
    return [r for r in registro.read_text(encoding="utf-8").splitlines() if r]


def prova(repo: Path) -> list:
    rossi = []
    sh = repo / "hooks" / "herdr-stato.sh"
    aiuto = repo / "hooks" / "herdr-stato-windows.py"
    if not aiuto.is_file():
        return [f"{c} manca hooks/herdr-stato-windows.py" for c in CASI]
    with tempfile.TemporaryDirectory() as t:
        d = Path(t)
        hooks = d / "hooks"
        shutil.copytree(repo / "hooks", hooks, ignore=shutil.ignore_patterns("__pycache__"))
        righe = _lancia(str(hooks / "herdr-stato.sh"), "working", d)
        if righe != [f"python|{hooks}/herdr-stato-windows.py|working"]:
            rossi.append(f"HW01 lo sh non chiama l'aiutante con python: {righe}")
        else:
            # Le \ del percorso di Windows: su POSIX un file che ha le \ nel nome.
            shutil.copy(hooks / "herdr-stato.sh", d / "a\\b\\herdr-stato.sh")
            righe = _lancia(str(d / "a") + "\\b\\herdr-stato.sh", "idle", d)
            if righe != [f"python|{d}/a\\b/herdr-stato-windows.py|idle"]:
                rossi.append(f"HW01 con le \\ nel percorso la cartella dell'aiutante è sbagliata: {righe}")
        for rc in (9009 % 256, 2):
            righe = _lancia(str(hooks / "herdr-stato.sh"), "blocked", d, rc_py=rc)
            if [r.split("|")[0] for r in righe] != ["python", "python3"]:
                rossi.append(f"HW02 con python che esce {rc} lo sh non prova python3: {righe}")
        senza = _lancia(str(hooks / "herdr-stato.sh"), "working", d, hc="")
        ignoto = _lancia(str(hooks / "herdr-stato.sh"), "boh", d)
        if senza or ignoto:
            rossi.append(f"HW03 lo sh chiama python fuori da Herdr o con uno stato ignoto: {senza} {ignoto}")
    spec = importlib.util.spec_from_file_location("herdr_stato_windows", aiuto)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    padri = {10: (9, "python.exe"), 9: (8, "sh.exe"), 8: (7, "bash.exe"), 7: (6, "claude.exe"), 6: (5, "pwsh.exe"),
             5: (0, "herdr-core.exe")}
    nati = {10: 100, 9: 90, 8: 80, 7: 70, 6: 60, 5: 50}
    if m.scegli(padri, 10, nati.get) != 7:
        rossi.append(f"HW04 scegli() non trova claude.exe: {m.scegli(padri, 10, nati.get)}")
    riuso = {**nati, 8: 500}
    if m.scegli(padri, 10, riuso.get) is not None:
        rossi.append("HW04 scegli() sale oltre un PID riusato (padre nato dopo il figlio)")
    # Un figlio illeggibile (None) non spegne il controllo: il padre nato dopo l'ultima ora letta è un PID riusato.
    buco = {**nati, 9: None, 8: 150}
    sali = getattr(m, "sali", None)
    if sali is None or sali(padri, 10, nati.get) != (7, 8):
        rossi.append(f"HW09 sali() non dà claude.exe e il suo figlio: {sali and sali(padri, 10, nati.get)}")
    elif m.scegli(padri, 10, buco.get) is not None:
        rossi.append("HW09 con un'ora illeggibile scegli() sale oltre un PID riusato")
    if not hasattr(m, "in_ordine"):
        rossi.append("HW08 manca in_ordine()")
    else:
        with tempfile.TemporaryDirectory() as t:
            f = Path(t) / "ordine.txt"
            scritti = []
            esiti = [m.in_ordine(f, ora, lambda o=ora: scritti.append(o) or True) for ora in (200, 100, 300)]
            fallita = m.in_ordine(f, 400, lambda: False)
            dopo = m.in_ordine(f, 350, lambda: scritti.append(350) or True)
            if esiti != [True, False, True] or fallita or not dopo or scritti != [200, 300, 350]:
                rossi.append(f"HW08 in_ordine() non scarta gli stati vecchi: {esiti} {fallita} {dopo} {scritti}")
    if sys.platform != "win32":
        p = subprocess.run([sys.executable, str(aiuto), "working"], capture_output=True, timeout=20)
        if p.returncode != 2 or p.stdout or p.stderr:
            rossi.append(f"HW05 fuori da Windows l'aiutante non tace: rc={p.returncode} {p.stdout[:80]!r} {p.stderr[-120:]!r}")
    return sorted(rossi)


def main() -> int:
    for flusso in (sys.stdout, sys.stderr):
        if hasattr(flusso, "reconfigure"):
            flusso.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument("--baseline-ref")
    a = parser.parse_args()
    if os.name == "nt":
        dichiara("HW01-HW09", "sh e python finti sono script di POSIX senza estensione")
        return 0
    rossi = prova(Path(a.repo).resolve())
    if a.baseline_ref:
        codici = sorted({r.split()[0] for r in rossi})
        assert codici == DISCRIMINANTI, f"baseline non discriminante: rossi {codici}, attesi {DISCRIMINANTI}"
        print(f"BASELINE_DISCRIMINANTE={','.join(codici)}")
        return 0
    for r in rossi:
        print("ROSSO", r)
    print(f"stato Herdr su Windows: {len(CASI) - len(rossi)}/{len(CASI)} casi verdi")
    return 1 if rossi else 0


if __name__ == "__main__":
    sys.exit(main())
