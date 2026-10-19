#!/usr/bin/env python3
"""SG01-SG02: le segnalazioni n. 4 e n. 5 arrivate con /segnala il 19/10/2026.

SG01 il workflow di igiene gira solo sul repository pubblico. /aggiorna lo porta anche nella copia
     privata di ~/.claude di chi usa Arturo: lì cercava i nomi dell'autore negli appunti della persona
     e falliva a ogni push del session sync (segnalazione n. 4).
SG02 i banchi d'avvio restano verdi quando un programma di terzi aggiunge a settings.json hook senza
     matcher, che per Claude Code è facoltativo. iTerm2 (cc-status) ne aggiunge uno per evento, e
     test-web-egress-guard.py cadeva con KeyError: 'matcher' prima del controllo vero: l'avvio diceva
     «una guardia potrebbe non proteggere» con la guardia al suo posto (segnalazione n. 5).

Sulla base 439a92b ogni controllo deve fallire con un AssertionError che comincia con il suo codice.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml

BASH = shutil.which("bash") or "bash"
GIT_ENV = {"GIT_AUTHOR_NAME": "a", "GIT_AUTHOR_EMAIL": "a@example.invalid", "GIT_COMMITTER_NAME": "a",
           "GIT_COMMITTER_EMAIL": "a@example.invalid", "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1"}
EVENTI = ("PreToolUse", "PostToolUse", "Stop", "Notification", "UserPromptSubmit", "SessionStart", "SessionEnd",
          "SubagentStop", "PreCompact", "PermissionRequest")


def test_sg01(repo: Path) -> None:
    f = repo / ".github" / "workflows" / "igiene.yml"
    assert f.is_file(), "SG01 manca .github/workflows/igiene.yml"
    lavori = yaml.safe_load(f.read_text(encoding="utf-8")).get("jobs") or {}
    senza = [nome for nome, lavoro in lavori.items()
             if (lavoro or {}).get("if", "").replace('"', "'").replace(" ", "") != "github.repository=='stellakamikaze/arturo'"]
    assert lavori and not senza, f"SG01 il workflow di igiene gira anche fuori dal repository pubblico: {senza}"


def test_sg02(repo: Path) -> None:
    with tempfile.TemporaryDirectory() as d:
        copia = Path(d) / "claude"
        shutil.copytree(repo, copia, ignore=shutil.ignore_patterns(".git", "cache", "node_modules"))
        impostazioni = copia / "settings.json"
        dati = json.loads(impostazioni.read_text(encoding="utf-8"))
        for evento in EVENTI:
            dati.setdefault("hooks", {}).setdefault(evento, []).append(
                {"hooks": [{"type": "command", "command": f"/Applications/iTerm.app/cc-status {evento}"}]})
        impostazioni.write_text(json.dumps(dati, indent=2, ensure_ascii=False), encoding="utf-8")
        # Come ~/.claude di chi usa Arturo: un repository git. Senza, banchi-avvio.sh copia solo alcune
        # cartelle, e i banchi che leggono il resto cadono per un motivo che nell'installazione vera non c'è.
        for comando in (["init", "-q"], ["add", "-A"], ["commit", "-q", "-m", "copia"]):
            subprocess.run(["git", "-C", str(copia), *comando], env=dict(os.environ, **GIT_ENV), check=True,
                           capture_output=True, timeout=120)
        env = dict(os.environ, ARTURO_DIR=str(copia), HOME=d, USERPROFILE=d)
        p = subprocess.run([BASH, str(copia / "tests" / "banchi-avvio.sh")], env=env, capture_output=True,
                           text=True, encoding="utf-8", timeout=900)
        esito = copia / "cache" / "banchi-ultimo-esito.txt"
        testo = esito.read_text(encoding="utf-8") if esito.is_file() else f"nessun esito (rc {p.returncode})"
        assert p.returncode == 0 and testo.startswith("VERDE"), \
            f"SG02 con hook senza matcher i banchi d'avvio sono rossi: {testo.strip()[:400]}"


TESTS = {"SG01": test_sg01, "SG02": test_sg02}


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
            except Exception as e:  # noqa: BLE001
                altro.append(f"{nome}: {type(e).__name__} {e}")
        assert not altro and len(rossi) == len(TESTS), \
            "baseline non discriminante: ogni controllo deve fallire col suo codice.\n" + "\n".join(altro + rossi)
        print(f"BASELINE_DISCRIMINANTE={','.join(r.split(':')[0] for r in rossi)}")
        return 0
    for test in TESTS.values():
        test(repo)
    print(f"PASS {','.join(TESTS)} controlli={len(TESTS)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
