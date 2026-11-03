#!/usr/bin/env python3
"""Testata di Arturo e banchi silenziosi (3/11/2026).

Federico, 3/11/2026: la notifica dei banchi rossi "è molto invasiva e non mi serve a niente saperlo";
al posto delle info di Claude Code vuole quelle di Arturo, "versione - drift e simili".

TB01 hooks/deriva.py scrive cache/deriva.json: misurata, i file di Arturo cambiati e, fra questi, le guardie.
TB02 tests/banchi-avvio.sh con un banco rosso manda il nome del banco con la telemetria, una volta sola
     finché l'elenco dei rossi non cambia; con la telemetria spenta non manda niente.
TB03 l'evento banchi accetta solo il nome di un banco, nel client e nel server.
TB04 il mod skills/testata passa validate e test, e piazza il suo blocco con $.ui.place all'avvio.

Ogni caso gira in una HOME finta: niente parte verso il server vero.
Sulla base c247fed ogni controllo deve fallire con un AssertionError che comincia con il suo codice.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def _carica(nome: str, file: str):
    spec = importlib.util.spec_from_file_location(nome, Path(__file__).with_name(file))
    assert spec and spec.loader
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


_deriva = _carica("banco_deriva", "test_deriva.py")
_mod = _carica("banco_mod_skill", "test_mod_skill.py")
_sicuro = _carica("aggiorna_copia", "test_aggiorna_copia.py")._sicuro
BASH = shutil.which("bash") or "bash"


def test_tb01(repo: Path) -> None:
    lab = _deriva.Lab(repo)
    lab.scrivi("commands/inizio.md", "# /inizio\n\nApri la sessione, a modo mio.\n", commit=False)
    lab.scrivi("hooks/bash-dispatcher.sh", "#!/bin/bash\nexit 1\n", commit=False)
    lab.deriva()
    f = lab.claude / "cache" / "deriva.json"
    assert f.is_file(), "TB01 hooks/deriva.py non scrive cache/deriva.json"
    dati = json.loads(f.read_text(encoding="utf-8"))
    assert dati.get("misurata") is True, f"TB01 deriva misurata su un clone di Arturo: {dati}"
    assert sorted(dati.get("file", [])) == ["commands/inizio.md", "hooks/bash-dispatcher.sh"], f"TB01 file: {dati}"
    assert dati.get("guardie") == ["hooks/bash-dispatcher.sh"], f"TB01 guardie: {dati}"


def _copia_con_rosso(repo: Path, radice: Path) -> Path:
    """Una copia minima di Arturo per banchi-avvio.sh: ogni banco passa, test_heredoc.py è rosso."""
    copia = radice / "claude"
    (copia / "tests").mkdir(parents=True)
    shutil.copy2(repo / "tests" / "banchi-avvio.sh", copia / "tests" / "banchi-avvio.sh")
    shutil.copytree(repo / "bin", copia / "bin")
    testo = (repo / "tests" / "banchi-avvio.sh").read_text(encoding="utf-8")
    banchi = re.search(r'^BANCHI="([^"]+)"', testo, re.M)
    assert banchi, "TB02 banchi-avvio.sh non ha più l'elenco BANCHI"
    for nome in banchi.group(1).split():
        corpo = "raise AssertionError('rotto')\n" if nome == "test_heredoc.py" else "pass\n"
        (copia / "tests" / nome).write_text(corpo, encoding="utf-8")
    return copia


def _banchi(copia: Path, home: Path, **extra: str) -> subprocess.CompletedProcess:
    env = dict(os.environ, ARTURO_DIR=str(copia), HOME=str(home), USERPROFILE=str(home),
               ARTURO_TELEMETRIA_URL="http://127.0.0.1:9")
    for chiave in ("ARTURO_TELEMETRIA", "DO_NOT_TRACK", "ARTURO_OGGI"):
        env.pop(chiave, None)
    env.update(extra)
    return subprocess.run([BASH, str(copia / "tests" / "banchi-avvio.sh")], env=env, capture_output=True,
                          text=True, encoding="utf-8", errors="replace", timeout=300)


def _coda(home: Path) -> list:
    f = home / ".claude" / "data" / "telemetria" / "coda.jsonl"
    righe = f.read_text(encoding="utf-8").splitlines() if f.exists() else []
    return [(e["evento"], e["valore"]) for e in map(json.loads, righe)]


def test_tb02(repo: Path) -> None:
    with tempfile.TemporaryDirectory() as d:
        radice = Path(d)
        home = radice / "home"
        (home / ".claude").mkdir(parents=True)
        copia = _copia_con_rosso(repo, radice)
        p = _banchi(copia, home)
        esito = (copia / "cache" / "banchi-ultimo-esito.txt").read_text(encoding="utf-8")
        assert p.returncode == 1 and esito.startswith("ROSSO"), f"TB02 il banco rotto non è rosso: {esito[:200]}"
        assert ("banchi", "test_heredoc.py") in _coda(home), f"TB02 il rosso non parte con la telemetria: {_coda(home)}"
        _banchi(copia, home)
        assert _coda(home).count(("banchi", "test_heredoc.py")) == 1, \
            f"TB02 lo stesso rosso riparte a ogni corsa: {_coda(home)}"
        spenta = radice / "spenta"
        (spenta / ".claude").mkdir(parents=True)
        (copia / "cache" / "banchi-ultimo-esito.txt").unlink()
        _banchi(copia, spenta, DO_NOT_TRACK="1")
        assert _coda(spenta) == [], f"TB02 con la telemetria spenta il rosso parte lo stesso: {_coda(spenta)}"


def test_tb03(repo: Path) -> None:
    spec = importlib.util.spec_from_file_location("telemetria_tb03", repo / "bin" / "telemetria.py")
    assert spec and spec.loader
    t = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(t)
    assert "banchi" in t.EVENTI, "TB03 il client non conosce l'evento banchi"
    assert t.valido("banchi", "test_heredoc.py") and t.valido("banchi", "test-web-egress-guard.py"), \
        "TB03 il nome di un banco non parte"
    for cattivo in ("/Users/x/test_a.py", "test_a.py: AssertionError", "rotto", "test_" + "a" * 80 + ".py"):
        assert not t.valido("banchi", cattivo), f"TB03 parte un valore che non è il nome di un banco: {cattivo!r}"
    logica = (repo / "server" / "logica.js").read_text(encoding="utf-8")
    assert re.search(r"^\s*banchi: /\^test\[a-z0-9_-\]\{1,56\}\\\.py\$/,", logica, re.M), \
        "TB03 il server non accetta l'evento banchi con la stessa forma del client"


def test_tb04(repo: Path) -> None:
    cartella = repo / "skills" / "testata"
    assert (cartella / "hooks" / "register.tsx").is_file(), "TB04 manca il mod skills/testata"
    codice = (cartella / "hooks" / "register.tsx").read_text(encoding="utf-8")
    assert "$.ui.place(" in codice and "session.version()" in codice, "TB04 la testata non piazza il blocco all'avvio"
    try:
        esito = _mod.prova_mod(repo, "testata", "TB04")
    except AssertionError as e:
        raise AssertionError(f"TB04 {e}") from None
    assert "all'avvio il blocco va sotto l'intestazione" in esito, "TB04 manca il test del blocco all'avvio"


TESTS = {"TB01": test_tb01, "TB02": test_tb02, "TB03": test_tb03, "TB04": test_tb04}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--baseline-ref")
    parser.add_argument("--solo", help="codici separati da virgola")
    args = parser.parse_args()
    repo = args.repo.resolve()
    scelti = {k: v for k, v in TESTS.items() if not args.solo or k in args.solo.split(",")}
    if args.baseline_ref:
        rossi, altro = _sicuro.baseline(scelti, repo)
        assert not altro and rossi == list(scelti), \
            "baseline non discriminante: ogni controllo deve fallire col suo codice.\n" + "\n".join(altro)
        print(f"BASELINE_DISCRIMINANTE={','.join(rossi)}")
        return 0
    for test in scelti.values():
        test(repo)
    print(f"PASS {','.join(scelti)} controlli={len(scelti)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
