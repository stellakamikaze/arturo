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
    p = subprocess.run([sys.executable, str(guardia)], input=evento(c), capture_output=True, text=True,
                       encoding="utf-8", timeout=60)
    return round(time.perf_counter() - i, 2), p.returncode, len(p.stdout)


corto = "ls -la"
quarto = "python3 -c \"" + "print('a b c d');" * 1_312 + "\""
lungo = "python3 -c \"" + "print('a b c d');" * 5_247 + "\""
for g in range(giri):
    s, q, l = t(corto), t(quarto), t(lungo)
    r = l[0] / max(q[0], .05)
    netto = (l[0] - s[0]) / max(q[0] - s[0], .05)
    esito = "PASSA_SP02" if l[0] < 8 and r < 6 else "ROSSO_SP02"
    print(f"{etichetta} giro={g} corto={s[0]} quarto={q[0]} lungo={l[0]} rapporto={r:.1f} netto={netto:.1f} "
          f"rc={q[1]},{l[1]} {esito}", flush=True)
