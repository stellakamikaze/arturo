#!/usr/bin/env python3
"""SB01-SB06: la sandbox di Claude Code come opzione della persona, spenta di default (19/11/2026, #6098).

SB01 il frammento di Arturo non accende la sandbox: settings.json del repo e il frammento del plugin non hanno
     sandbox.enabled, e `arturo sandbox stato` su una casa vuota dice spenta.
SB02 `arturo sandbox accendi` scrive enabled, le credenziali in deny e i comandi esclusi, e lascia com'erano le
     altre chiavi della persona e la voce allowWrite di Arturo.
SB03 `arturo sandbox spegni` toglie solo le voci aggiunte: settings.json torna uguale a prima, anche con una
     voce sandbox che la persona aveva già, e un enabled: false scritto da lei torna false.
SB04 accendi due volte non duplica niente.
SB05 dopo accendi l'unione a tre vie di `arturo impostazioni` (base = frammento, nostro = settings della persona,
     loro = frammento) non va in conflitto e tiene la sandbox accesa.
SB06 accendi lascia la copia settings.json.prima-della-sandbox, uguale al file di prima.

Sulla base f500fc1 ogni controllo deve fallire con un AssertionError che comincia con il suo codice.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

PERSONA = {
    "model": "opus",
    "permissions": {"deny": ["Read(./.env)"]},
    "sandbox": {"filesystem": {"allowWrite": ["~/.claude/data", "/tmp/mio"]}},
}


def casa(settings=None) -> Path:
    radice = Path(tempfile.mkdtemp(prefix="arturo-sandbox.")) / ".claude"
    (radice / "data").mkdir(parents=True)
    if settings is not None:
        (radice / "settings.json").write_text(json.dumps(settings, indent=2), encoding="utf-8")
    return radice


def ambiente(radice: Path) -> dict:
    env = dict(os.environ)
    env.update(HOME=str(radice.parent), USERPROFILE=str(radice.parent), CLAUDE_CONFIG_DIR=str(radice),
               ARTURO_RADICE=str(radice), PYTHONDONTWRITEBYTECODE="1", PYTHONIOENCODING="utf-8",
               ARTURO_TELEMETRIA="spenta")
    return env


def arturo(repo: Path, radice: Path, codice: str, *argomenti: str) -> subprocess.CompletedProcess:
    assert (repo / "bin" / "sandbox.py").is_file(), f"{codice} manca bin/sandbox.py"
    r = subprocess.run([sys.executable, str(repo / "bin" / "arturo"), "sandbox", *argomenti], env=ambiente(radice),
                       capture_output=True, text=True, encoding="utf-8", timeout=60)
    assert r.returncode == 0, f"{codice} arturo sandbox {' '.join(argomenti)} esce {r.returncode}: {r.stdout!r} {r.stderr!r}"
    return r


def leggi(radice: Path) -> dict:
    return json.loads((radice / "settings.json").read_text(encoding="utf-8"))


def carica(repo: Path, nome: str, file: str):
    sys.path.insert(0, str(repo / "bin"))
    try:
        spec = importlib.util.spec_from_file_location(nome, repo / "bin" / file)
        m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
    finally:
        sys.path.pop(0)
    return m


def pulisci(radice: Path) -> None:
    shutil.rmtree(radice.parent, ignore_errors=True)


def test_sb01(repo: Path) -> None:
    settings = json.loads((repo / "settings.json").read_text(encoding="utf-8"))
    assert "enabled" not in (settings.get("sandbox") or {}), "SB01 settings.json di Arturo accende la sandbox"
    frammento = carica(repo, "impacchetta_sb01", "impacchetta.py").impostazioni(settings)
    assert "enabled" not in (frammento.get("sandbox") or {}), "SB01 il frammento del plugin accende la sandbox"
    radice = casa()
    try:
        r = arturo(repo, radice, "SB01", "stato")
        assert "spenta" in r.stdout, f"SB01 su una casa vuota lo stato non è spenta: {r.stdout!r}"
    finally:
        pulisci(radice)


def test_sb02(repo: Path) -> None:
    radice = casa(PERSONA)
    try:
        arturo(repo, radice, "SB02", "accendi")
        s = leggi(radice)
        sb = s["sandbox"]
        assert sb.get("enabled") is True, f"SB02 accendi non scrive enabled: {sb!r}"
        negati = {f["path"] for f in sb.get("credentials", {}).get("files", []) if f.get("mode") == "deny"}
        assert {"~/.ssh", "~/.aws"} <= negati, f"SB02 accendi non nega le chiavi SSH e AWS: {negati!r}"
        assert "git push *" in sb.get("excludedCommands", []), "SB02 git push non è escluso: su macOS fallisce in sandbox"
        assert s["model"] == "opus" and s["permissions"] == PERSONA["permissions"], "SB02 accendi cambia altre chiavi"
        scrive = sb["filesystem"]["allowWrite"]
        assert "~/.claude/data" in scrive and "/tmp/mio" in scrive, f"SB02 accendi perde voci di allowWrite: {scrive!r}"
    finally:
        pulisci(radice)


def test_sb03(repo: Path) -> None:
    for prima in (PERSONA, dict(PERSONA, sandbox={"enabled": False, "filesystem": {"allowWrite": ["~/.claude/data"]}})):
        radice = casa(prima)
        try:
            arturo(repo, radice, "SB03", "accendi")
            arturo(repo, radice, "SB03", "spegni")
            assert leggi(radice) == prima, f"SB03 spegni non riporta settings.json com'era: {leggi(radice)!r}"
            assert not (radice / "data" / "arturo-sandbox.json").exists(), "SB03 spegni lascia il registro delle voci"
        finally:
            pulisci(radice)


def test_sb04(repo: Path) -> None:
    radice = casa(PERSONA)
    try:
        arturo(repo, radice, "SB04", "accendi")
        una = leggi(radice)
        r = arturo(repo, radice, "SB04", "accendi")
        assert leggi(radice) == una, "SB04 il secondo accendi cambia settings.json"
        assert "già accesa" in r.stdout, f"SB04 il secondo accendi non dice che è già accesa: {r.stdout!r}"
    finally:
        pulisci(radice)


def test_sb05(repo: Path) -> None:
    settings = json.loads((repo / "settings.json").read_text(encoding="utf-8"))
    frammento = carica(repo, "impacchetta_sb05", "impacchetta.py").impostazioni(settings)
    radice = casa(frammento)
    try:
        arturo(repo, radice, "SB05", "accendi")
        persona = leggi(radice)
        spec = importlib.util.spec_from_file_location("unisci_sb05", repo / "bin" / "unisci-settings.py")
        unisci = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(unisci)
        try:
            unito = unisci.unisci(frammento, persona, frammento)
        except unisci.Conflitto as errore:
            raise AssertionError(f"SB05 l'unione delle impostazioni va in conflitto dopo accendi: {errore}")
        assert unito["sandbox"].get("enabled") is True, "SB05 l'unione delle impostazioni spegne la sandbox"
    finally:
        pulisci(radice)


def test_sb06(repo: Path) -> None:
    radice = casa(PERSONA)
    try:
        prima = (radice / "settings.json").read_text(encoding="utf-8")
        arturo(repo, radice, "SB06", "accendi")
        copia = radice / "settings.json.prima-della-sandbox"
        assert copia.is_file() and copia.read_text(encoding="utf-8") == prima, "SB06 manca la copia di prima"
    finally:
        pulisci(radice)


TESTS = {"SB01": test_sb01, "SB02": test_sb02, "SB03": test_sb03, "SB04": test_sb04, "SB05": test_sb05,
         "SB06": test_sb06}


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
