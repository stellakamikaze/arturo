"""Sonda temporanea #6623: i tempi di SP02 (test_parole_veloci) su Windows, base 663bcba contro dev."""
import json
import subprocess
import sys
import time
from pathlib import Path

repo, giri, etichetta = Path(sys.argv[1]), int(sys.argv[2]), sys.argv[3]
guardia = repo / "hooks" / "block-dangerous.py"


def evento(c):
    return json.dumps({"tool_name": "Bash", "tool_input": {"command": c}, "cwd": "/tmp", "session_id": "sp"})


def t(c):
    i = time.perf_counter()
    try:
        subprocess.run([sys.executable, str(guardia)], input=evento(c), capture_output=True, text=True,
                       encoding="utf-8", timeout=90)
    except subprocess.TimeoutExpired:
        return 90.0
    return round(time.perf_counter() - i, 2)


def comando(n):
    return "python3 -c \"" + "print('a b c d');" * n + "\""


for g in range(giri):
    s, q, l, tr = t("ls -la"), t(comando(1_312)), t(comando(5_247)), t(comando(15_741))
    print(f"{etichetta} giro={g} corto={s} quarto={q} lungo={l} triplo={tr} rapporto={l / max(q, .05):.1f} "
          f"{'TRIPLO_SOTTO_8' if tr < 8 else 'TRIPLO_OLTRE_8'}", flush=True)
