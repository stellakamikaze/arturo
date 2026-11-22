#!/usr/bin/env python3
"""TG: le guardie hanno un tetto di tempo, e oltre si chiede conferma (22/11/2026, #6363).

Claude Code ferma un hook dopo 30 secondi, e allora il comando parte senza giudizio. Su 90.000 caratteri di
`curl` ripetuti block-dangerous impiegava 83 secondi e il dispatcher oltre 120 (sonda del 22/11/2026).

  TG01  evento_bash.py esegui con ARTURO_RESTANTE=N ferma lo script dopo N secondi con codice 1; senza la
        variabile lo script arriva in fondo. Un valore oltre 25 vale 25, uno sotto 0,5 vale 0,5.
  TG02  il dispatcher scrive ARTURO_RESTANTE a ogni guardia: con block-dangerous che dorme 60 secondi, su 90.000
        caratteri di `curl` ripetuti finisce entro 29 secondi e chiede conferma. Fino al #6363 dormiva da sé.

Con --baseline-ref ogni controllo deve fallire col suo codice: su e1a03e6 lo script dorme fino in fondo e il
dispatcher va oltre i 40 secondi.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from salti_windows import dichiara  # noqa: E402

WINDOWS = os.name == "nt"
BASH = shutil.which("bash") or "bash"


def _esegui(repo: Path, script: Path, restante: str | None):
    ambiente = {k: v for k, v in os.environ.items() if k != "ARTURO_RESTANTE"}
    if restante is not None:
        ambiente["ARTURO_RESTANTE"] = restante
    t = time.time()
    p = subprocess.run([sys.executable, str(repo / "hooks" / "evento_bash.py"), "esegui", str(script)],
                       capture_output=True, text=True, timeout=60, env=ambiente)
    return p, time.time() - t


def test_tg01(repo: Path) -> None:
    with tempfile.TemporaryDirectory(prefix="tg01-") as d:
        lento = Path(d) / "lento.py"
        lento.write_text("import time\ntime.sleep(4)\nprint('fine')\n", encoding="utf-8")
        p, durata = _esegui(repo, lento, "1")
        assert p.returncode == 1 and durata < 3 and "fine" not in p.stdout, \
            f"TG01 con ARTURO_RESTANTE=1 lo script non si ferma: rc={p.returncode} in {durata:.1f} s"
        p, durata = _esegui(repo, lento, "0")
        assert p.returncode == 1 and durata < 3, f"TG01 ARTURO_RESTANTE=0 non vale 0,5 secondi: {durata:.1f} s"
        p, _ = _esegui(repo, lento, None)
        assert p.returncode == 0 and "fine" in p.stdout, f"TG01 senza la variabile lo script non arriva in fondo: {p.returncode}"
        breve = Path(d) / "breve.py"
        breve.write_text("import sys\nprint('ok')\nsys.exit(2)\n", encoding="utf-8")
        p, _ = _esegui(repo, breve, "1000")
        assert p.returncode == 2 and "ok" in p.stdout, f"TG01 con un tetto alto lo script cambia esito: {p.returncode}"
        testo = (repo / "hooks" / "evento_bash.py").read_text(encoding="utf-8")
        assert "25.0)" in testo, "TG01 il tetto di ARTURO_RESTANTE non è 25 secondi"


def test_tg02(repo: Path) -> None:
    if WINDOWS:
        dichiara("TG02", "il dispatcher si prova su macOS e Linux; su Windows il tetto è lo stesso esegui di TG01")
        return
    with tempfile.TemporaryDirectory(prefix="tg02-") as d:
        casa = Path(d) / "home"
        shutil.copytree(repo, casa / ".claude", ignore=shutil.ignore_patterns(".git", "__pycache__", "worktrees"))
        # Dal #6363 le guardie leggono i curl ripetuti in un secondo: qui block-dangerous è una guardia che dorme,
        # così il banco prova il tetto e non la lentezza di una regex.
        (casa / ".claude" / "hooks" / "block-dangerous.py").write_text("import time\ntime.sleep(60)\n", encoding="utf-8")
        comando = ("curl " * 18_001)[:90_000]
        evento = json.dumps({"tool_name": "Bash", "tool_input": {"command": comando}, "cwd": str(casa),
                             "session_id": "tg", "tool_use_id": "toolu_tg"})
        ambiente = dict(os.environ, HOME=str(casa), USERPROFILE=str(casa))
        ambiente.pop("ARTURO_RESTANTE", None)
        t = time.time()
        try:
            p = subprocess.run([BASH, str(casa / ".claude" / "hooks" / "bash-dispatcher.sh")], input=evento,
                               capture_output=True, text=True, timeout=40, env=ambiente)
        except subprocess.TimeoutExpired:
            raise AssertionError("TG02 il dispatcher su 90.000 caratteri di curl va oltre i 40 secondi")
        durata = time.time() - t
        assert durata < 29 and '"ask"' in p.stdout, \
            f"TG02 il dispatcher dura {durata:.1f} s o non chiede conferma: {p.stdout[:200]!r}"


TESTS = {"TG01": test_tg01, "TG02": test_tg02}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[1])
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
        print(f"baseline {args.baseline_ref}: {len(rossi)}/{len(TESTS)} rossi col loro codice")
        return 0
    for nome, test in TESTS.items():
        test(repo)
        print(f"{nome} ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())
