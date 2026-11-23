"""Sonda di #6455, solo sul ramo sonda-6455-win: i banchi rossi su Windows, uno per uno, con le ultime righe."""
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

repo = Path(__file__).resolve().parents[1]
elenco = [r.strip() for r in (repo / "tests" / "sonda_6455.txt").read_text(encoding="utf-8").splitlines()
          if r.strip() and not r.startswith("#")]
py38 = os.environ.get("PY38", "")
print("bash:", shutil.which("bash"), "sh:", shutil.which("sh"), "python3:", shutil.which("python3"), flush=True)
rossi = 0
for voce in elenco:
    tipo, _, banco = voce.partition(":")
    test = str(repo / "tests" / banco)
    if tipo == "py38":
        comando = [py38, "-B", test, "--repo", str(repo)]
    elif tipo == "veleno":
        comando = [sys.executable, "-B", test, "--repo", str(repo), "--avvelena"]
    else:
        comando = [sys.executable, "-B", test, "--repo", str(repo)]
    inizio = time.monotonic()
    try:
        p = subprocess.run(comando, capture_output=True, timeout=900, cwd=str(repo))
        rc, uscita = p.returncode, (p.stdout + p.stderr).decode("utf-8", "replace")
    except subprocess.TimeoutExpired as e:
        rc, uscita = "tetto", ((e.stdout or b"") + (e.stderr or b"")).decode("utf-8", "replace")
    durata = time.monotonic() - inizio
    esito = "VERDE" if rc == 0 else "ROSSO"
    rossi += esito == "ROSSO"
    print(f"{esito} {durata:6.1f}s {voce}", flush=True)
    if esito == "ROSSO":
        for riga in uscita.splitlines()[-30:]:
            print("    " + riga[:400], flush=True)
print(f"SONDA: {len(elenco) - rossi}/{len(elenco)} verdi", flush=True)
