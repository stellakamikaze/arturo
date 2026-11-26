#!/usr/bin/env python3
"""RR01-RR05: rsync verso una macchina remota non scrive sulla config (26/11/2026, #6732).

Prima `rsync -az ~/.claude/data/memory/ backup@nas:/srv/x/` lanciato da ~/.claude/hooks chiedeva conferma
con "scrive sulla config di ~/.claude: ~/.claude/hooks/backup@nas:/srv/x": scritture_config leggeva
la destinazione remota come un percorso relativo alla cartella corrente. E `rsync -t` (per rsync è --times)
contava l'argomento dopo come cartella di destinazione, come per cp.

  RR01  rsync verso host:percorso da una cartella della config: nessuna scrittura sulla config.
  RR02  rsync -t con una sorgente nella config e la destinazione fuori: nessuna scrittura sulla config.
  RR03  rsync da una macchina remota verso la config: scrittura sulla config (invariante).
  RR04  rsync verso una cartella relativa della config: scrittura sulla config (invariante).
  RR05  cp -t verso la config: scrittura sulla config (invariante).

Invarianti (verdi anche sulla base): RR03, RR04, RR05.
Sulla base 062e126 sono rossi RR01, RR02.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

DISCRIMINANTI = ["RR01", "RR02"]
# (codice, comando, cartella relativa alla home, scrive sulla config)
CASI = [
    ("RR01", "rsync -az ~/.claude/data/memory/ backup@nas:/srv/memoria/", ".claude/hooks", False),
    ("RR02", "rsync -t ~/.claude/settings.json /tmp/copia.json", ".", False),
    ("RR03", "rsync -a nas:/srv/hooks/ ~/.claude/hooks/", ".", True),
    ("RR04", "rsync -a nuovi/ ./hooks/", ".claude", True),
    ("RR05", "cp -t ~/.claude/hooks nuovo.py", ".", True),
]

SONDA = (
    "import json, os, sys\n"
    "sys.path.insert(0, sys.argv[1])\n"
    "import forma_comando as fc\n"
    "casi = json.loads(sys.argv[2])\n"
    "h = os.path.expanduser('~')\n"
    "print(json.dumps({c: fc.scritture_config(cmd, os.path.normpath(os.path.join(h, d))) for c, cmd, d, _ in casi}))\n"
)


def prova(repo: Path) -> list[str]:
    with tempfile.TemporaryDirectory() as tmp:
        home = Path(tmp)
        (home / ".claude" / "hooks").mkdir(parents=True)
        (home / ".claude" / "data" / "memory").mkdir(parents=True)
        (home / ".claude" / "settings.json").write_text("{}\n", encoding="utf-8")
        env = {**os.environ, "HOME": str(home), "USERPROFILE": str(home), "ARTURO_TELEMETRIA": "0"}
        env.pop("CLAUDE_CONFIG_DIR", None)
        p = subprocess.run([sys.executable, "-B", "-c", SONDA, str(repo / "hooks"), json.dumps(CASI)],
                           capture_output=True, text=True, encoding="utf-8", env=env, timeout=30, check=False)
        if p.returncode != 0:
            return [f"{c}: la sonda di forma_comando non gira: {p.stderr[-300:]}" for c, *_ in CASI]
        esiti = json.loads(p.stdout)
    rossi = []
    for codice, comando, _, scrive in CASI:
        trovati = esiti[codice]
        if bool(trovati) != scrive:
            atteso = "una scrittura sulla config" if scrive else "nessuna scrittura sulla config"
            rossi.append(f"{codice}: {comando!r} atteso {atteso}, ottenuto {trovati}")
    return rossi


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parent.parent)
    parser.add_argument("--baseline-ref")
    args = parser.parse_args()
    rossi = prova(args.repo.resolve())
    if args.baseline_ref:
        codici = sorted(r.split(":")[0] for r in rossi)
        assert codici == DISCRIMINANTI, \
            f"baseline non discriminante: attesi rossi {DISCRIMINANTI}, ottenuti {codici}\n" + "\n".join(rossi)
        print(f"BASELINE_DISCRIMINANTE={','.join(codici)}")
        return 0
    if rossi:
        print("\n".join(rossi))
        return 1
    print(f"PASS {','.join(c for c, *_ in CASI)} controlli={len(CASI)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
