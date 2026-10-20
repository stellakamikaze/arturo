#!/usr/bin/env python3
"""LT01-LT05: lotto del 20/10/2026 sui task aperti di Arturo.

LT01 l'audit vede lo script della barra anche dentro `... statusline.js; echo ...` (#3632): se
     manca, lo dice invece di saltare il controllo.
LT02 il README dice cosa succede senza node e cita la riga NODE dell'avvio (#3632).
LT03 README, /aggiorna, SECURITY e la docstring di aggiornamenti.py conoscono il caso «firma non
     verificabile», che non è una compromissione; /segnala manda il solo tag del rilascio (#3552).
LT04 un hook di terzi in testa a Notification o senza `command` non fa cadere K09 e i banchi M (#3596).
LT05 l'avvio non usa più osascript, e il README racconta le schede nel Terminale di macOS (#3587).

Sulla base 910ac0b ogni controllo deve fallire con un AssertionError che comincia con il suo codice.
"""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

BASH = shutil.which("bash") or "bash"


def casa(repo: Path, radice: Path) -> Path:
    home = radice / "home"
    shutil.copytree(repo, home / ".claude", ignore=shutil.ignore_patterns(".git", "__pycache__"))
    return home


def env_di(home: Path, **extra: str) -> dict:
    env = {"HOME": str(home), "USERPROFILE": str(home), "PATH": os.environ.get("PATH", ""),
           "PYTHONDONTWRITEBYTECODE": "1", "GIT_CONFIG_GLOBAL": "/dev/null", "ARTURO_TELEMETRIA": "0"}
    env.update(extra)
    return env


def test_lt01(repo: Path) -> None:
    with tempfile.TemporaryDirectory() as d:
        home = casa(repo, Path(d))
        (home / ".claude" / "hooks" / "statusline.js").unlink()
        r = subprocess.run([BASH, str(home / ".claude" / "skills" / "system-audit" / "audit.sh")],
                           capture_output=True, text=True, timeout=180, env=env_di(home), check=False)
        uscita = r.stdout + r.stderr
        assert "hook diretto mancante" in uscita and "statusline.js" in uscita, \
            "LT01 l'audit non vede che manca statusline.js quando la barra è `... statusline.js; echo ...`"


def test_lt02(repo: Path) -> None:
    readme = (repo / "README.md").read_text(encoding="utf-8")
    assert "riga `NODE`" in readme and "manca node" in readme, \
        "LT02 il README non dice cosa succede senza node né la riga NODE dell'avvio"


def test_lt03(repo: Path) -> None:
    for nome in ("README.md", "commands/aggiorna.md", "bin/aggiornamenti.py", "SECURITY.md"):
        testo = (repo / nome).read_text(encoding="utf-8").lower()
        assert "non verificabile" in testo, f"LT03 {nome} non conosce il caso «firma non verificabile»"
    segnala = (repo / "bin" / "segnala.py").read_text(encoding="utf-8")
    assert '"--abbrev=0", "--match", "v*"' in segnala, "LT03 /segnala manda ancora describe --always"


def test_lt04(repo: Path) -> None:
    import importlib.util
    import json
    with tempfile.TemporaryDirectory() as d:
        copia = Path(d) / "repo"
        shutil.copytree(repo, copia, ignore=shutil.ignore_patterns(".git", "__pycache__"))
        f = copia / "settings.json"
        s = json.loads(f.read_text(encoding="utf-8"))
        terzi = {"hooks": [{"type": "command", "command": "~/.iterm2/cc-status notify"}]}
        s["hooks"]["Notification"].insert(0, terzi)
        s["hooks"]["PostToolUse"].insert(0, {"hooks": [{"type": "http", "url": "http://127.0.0.1:9/x"}]})
        f.write_text(json.dumps(s), encoding="utf-8")
        spec = importlib.util.spec_from_file_location("k_banco", copia / "tests" / "test_config_2026_10_15.py")
        m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
        try:
            m.test_k09(copia)
        except (AssertionError, KeyError, IndexError) as e:
            raise AssertionError(f"LT04 un hook di terzi in testa a Notification fa cadere K09: {e}") from None
    telemetria = (repo / "tests" / "test_telemetria.py").read_text(encoding="utf-8")
    assert 'h["command"]' not in telemetria, "LT04 test_telemetria legge h[\"command\"]: un hook senza command lo fa cadere"


def test_lt05(repo: Path) -> None:
    avvio = (repo / "hooks" / "session-start.sh").read_text(encoding="utf-8")
    righe = [r for r in avvio.splitlines() if not r.lstrip().startswith("#")]
    assert not any("osascript" in r for r in righe), "LT05 l'avvio usa ancora osascript per il titolo della finestra"
    readme = (repo / "README.md").read_text(encoding="utf-8")
    assert "TOCCA A TE" in readme and "Terminale di macOS" in readme, \
        "LT05 il README non racconta le schede nel Terminale di macOS"


TESTS = {"LT01": test_lt01, "LT02": test_lt02, "LT03": test_lt03, "LT04": test_lt04, "LT05": test_lt05}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--baseline-ref")
    args = parser.parse_args()
    repo = args.repo.resolve()
    if args.baseline_ref:
        rossi, altro = [], []
        for nome, test in TESTS.items():
            try:
                test(repo)
            except AssertionError as e:
                (rossi if str(e).startswith(nome) else altro).append(f"{nome}: {e}")
        assert not altro and len(rossi) == len(TESTS), \
            "baseline non discriminante: ogni controllo deve fallire col suo codice.\n" + "\n".join(altro + rossi)
        print(f"BASELINE_DISCRIMINANTE={','.join(r.split(':')[0] for r in rossi)}")
        return 0
    for test in TESTS.values():
        test(repo)
    print(f"PASS {','.join(TESTS)} controlli={len(TESTS)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
