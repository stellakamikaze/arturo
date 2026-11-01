#!/usr/bin/env python3
"""GT01-GT05: il controllo dei token gws all'avvio (hooks/gws-token-health.py, 1/11/2026).

L'hook non lancia gws dentro l'avvio: mostra la cache e, se serve, lancia `--refresh` staccato. Fino al
1/11 nessun banco provava questo percorso, e su Windows un gws appeso lasciava il refresh fermo.

GT01 gws lento: il refresh finisce entro il limite e scrive "? gws-x: non verificato", senza la riga fix.
GT02 gws con un token invalido: il refresh scrive "! gws-x" e la riga fix.
GT03 un lock fresco: l'hook non lancia un secondo refresh.
GT04 un login più recente della cache la scarta: l'avviso vecchio non esce.
GT05 l'hook senza cache torna subito, e il refresh che lancia scrive la cache.

Ogni caso gira con una HOME finta e un gws finto in testa al PATH. Con --avvelena il banco rompe la
copia dell'hook in due punti (un timeout che vale "ok", un refresh lanciato senza --refresh) e vuole
GT01 e GT05 rossi col loro codice.
"""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

FINTO = r'''
import json, os, sys, time
modo = os.environ.get("FINTO_GWS", "valido")
if modo == "lento":
    time.sleep(120)
if modo == "rotto":
    sys.exit(1)
valido = modo == "valido"
print("banner")
print(json.dumps({"has_refresh_token": True, "token_valid": valido, "user": "x@example.invalid"}))
'''


def prepara(radice: Path, hook: Path):
    home = radice / "home"
    conf = home / ".config" / "gws-x"
    conf.mkdir(parents=True)
    (conf / "credentials.enc").write_text("x", encoding="utf-8")
    bin_finto = radice / "bin"
    bin_finto.mkdir()
    (bin_finto / "gws_finto.py").write_text(FINTO, encoding="utf-8")
    if os.name == "nt":
        (bin_finto / "gws.cmd").write_text(f'@"{sys.executable}" "%~dp0gws_finto.py" %*\r\n', encoding="utf-8")
    else:
        g = bin_finto / "gws"
        g.write_text(f'#!/bin/sh\nexec "{sys.executable}" "$(dirname "$0")/gws_finto.py" "$@"\n', encoding="utf-8")
        g.chmod(0o755)
    copia = radice / "hooks"
    copia.mkdir()
    shutil.copy2(hook, copia / "gws-token-health.py")
    cache = home / ".claude" / "session-env" / "gws-health.cache"
    return home, bin_finto, copia / "gws-token-health.py", cache


def lancia(hook: Path, home: Path, bin_finto: Path, modo: str, *argomenti: str, timeout: int = 60):
    env = {**os.environ, "HOME": str(home), "USERPROFILE": str(home), "FINTO_GWS": modo,
           "PATH": str(bin_finto) + os.pathsep + os.environ.get("PATH", ""), "ARTURO_GWS_TIMEOUT_SEC": "3"}
    t0 = time.monotonic()
    r = subprocess.run([sys.executable, "-B", str(hook), *argomenti], capture_output=True, text=True,
                       encoding="utf-8", timeout=timeout, env=env, check=False)
    return r, time.monotonic() - t0


def test_gt01(hook: Path) -> None:
    with tempfile.TemporaryDirectory() as d:
        home, b, h, cache = prepara(Path(d), hook)
        r, durata = lancia(h, home, b, "lento", "--refresh")
        assert durata < 30, f"GT01 il refresh con gws lento resta appeso ({durata:.0f}s)"
        testo = cache.read_text(encoding="utf-8") if cache.exists() else ""
        assert "? gws-x: non verificato" in testo, f"GT01 gws lento non dà 'non verificato': {testo!r}"
        assert "fix:" not in testo, f"GT01 un timeout chiede di rifare il login: {testo!r}"


def test_gt02(hook: Path) -> None:
    with tempfile.TemporaryDirectory() as d:
        home, b, h, cache = prepara(Path(d), hook)
        lancia(h, home, b, "invalido", "--refresh")
        testo = cache.read_text(encoding="utf-8") if cache.exists() else ""
        assert "! gws-x: token invalido" in testo and "fix:" in testo, f"GT02 token invalido non segnalato: {testo!r}"


def test_gt03(hook: Path) -> None:
    with tempfile.TemporaryDirectory() as d:
        home, b, h, cache = prepara(Path(d), hook)
        lock = cache.with_suffix(".lock")
        lock.parent.mkdir(parents=True, exist_ok=True)
        lock.write_text("altro", encoding="utf-8")
        lancia(h, home, b, "valido")
        time.sleep(2)
        assert lock.read_text(encoding="utf-8") == "altro", "GT03 con un lock fresco parte un secondo refresh"
        assert not cache.exists(), "GT03 con un lock fresco la cache è stata scritta"


def test_gt04(hook: Path) -> None:
    with tempfile.TemporaryDirectory() as d:
        home, b, h, cache = prepara(Path(d), hook)
        cache.parent.mkdir(parents=True, exist_ok=True)
        cache.write_text("GWS TOKEN HEALTH:\n  ! gws-x: avviso vecchio\n", encoding="utf-8")
        vecchio = time.time() - 3600
        os.utime(cache, (vecchio, vecchio))
        cache.with_suffix(".lock").write_text("altro", encoding="utf-8")  # niente refresh vero
        r, _ = lancia(h, home, b, "valido")
        assert "avviso vecchio" not in r.stdout, "GT04 un login più recente della cache non la scarta"


def test_gt05(hook: Path) -> None:
    with tempfile.TemporaryDirectory() as d:
        home, b, h, cache = prepara(Path(d), hook)
        r, durata = lancia(h, home, b, "valido")
        assert durata < 12, f"GT05 l'hook senza cache non torna subito ({durata:.0f}s)"
        fine = time.monotonic() + 40
        while time.monotonic() < fine and not cache.exists():
            time.sleep(0.5)
        assert cache.exists(), "GT05 il refresh lanciato dall'hook non scrive la cache"
        lock = cache.with_suffix(".lock")
        while time.monotonic() < fine and lock.exists():
            time.sleep(0.5)


TESTS = {"GT01": test_gt01, "GT02": test_gt02, "GT03": test_gt03, "GT04": test_gt04, "GT05": test_gt05}
VELENI = {
    "GT01": ('return alias, "unverified", f"non verificato (auth status oltre', 'return alias, "ok", f"non verificato (auth status oltre'),
    "GT05": ('str(Path(__file__).resolve()), "--refresh"]', 'str(Path(__file__).resolve())]'),
}


def avvelena(hook: Path) -> int:
    testo = hook.read_text(encoding="utf-8")
    inerti = []
    for codice, (giusto, rotto) in VELENI.items():
        assert giusto in testo, f"veleno {codice}: il punto da rompere non c'è più nell'hook"
        with tempfile.TemporaryDirectory() as d:
            rotta = Path(d) / "gws-token-health.py"
            rotta.write_text(testo.replace(giusto, rotto), encoding="utf-8")
            try:
                TESTS[codice](rotta)
                inerti.append(f"{codice}: verde con l'hook rotto")
            except AssertionError as e:
                if not str(e).startswith(codice):
                    inerti.append(f"{codice}: rosso col motivo sbagliato: {e}")
                else:
                    print(f"VELENO {codice} ROSSO: {str(e)[:120]}")
    assert not inerti, "veleni che non attaccano:\n" + "\n".join(inerti)
    print(f"VELENI_ROSSI={','.join(VELENI)} veleni={len(VELENI)}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--avvelena", action="store_true")
    args = parser.parse_args()
    hook = args.repo.resolve() / "hooks" / "gws-token-health.py"
    if args.avvelena:
        return avvelena(hook)
    errori = []
    for prova in TESTS.values():
        try:
            prova(hook)
        except AssertionError as e:
            errori.append(str(e))
    for e in errori:
        print("KO", e)
    if errori:
        return 1
    print(f"PASS {','.join(TESTS)} controlli={len(TESTS)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
