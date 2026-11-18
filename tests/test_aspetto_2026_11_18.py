#!/usr/bin/env python3
"""AS01-AS06: l'aspetto della persona in ~/.claude/personale/aspetto.json (proposta n. 73, 18/11/2026, #5432).

AS01 hooks/aspetto_valori.py tiene i valori validi e mette fuori, come errori, un colore senza #, un numero
     oltre 255, uno stato o una sezione sconosciuti e un JSON rotto. Senza file: niente valori, niente errori.
AS02 la scheda del terminale usa l'RGB della persona in iTerm2 e il suo indice in Windows Terminal; uno stato che
     il file non nomina resta col colore di serie.
AS03 la barra salta i pezzi spenti e accoda il testo di personale/barra.js; una barra.js che lancia un errore non
     rompe la barra, e dal suo testo escono i caratteri di controllo ma restano i colori.
AS04 `arturo aspetto mostra dafare` rende i colori validi; il pannello /dafare li chiede alla CLI e legge la
     palette a ogni disegno, non una volta sola al caricamento.
AS05 la riga DERIVA su una barra cambiata dice di usare personale/aspetto.json.
AS06 `arturo aspetto controlla` esce 1 su un file sbagliato e 0 su uno buono, e `arturo personale elenco` lo nomina.

Sulla base 58e0435 ogni controllo deve fallire con un AssertionError che comincia con il suo codice.
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


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.is_file() else ""


def casa(aspetto, barra_js: str = "") -> Path:
    radice = Path(tempfile.mkdtemp(prefix="arturo-aspetto.")) / ".claude"
    (radice / "personale").mkdir(parents=True)
    if aspetto is not None:
        testo = aspetto if isinstance(aspetto, str) else json.dumps(aspetto)
        (radice / "personale" / "aspetto.json").write_text(testo, encoding="utf-8")
    if barra_js:
        (radice / "personale" / "barra.js").write_text(barra_js, encoding="utf-8")
    return radice


def ambiente(radice: Path, **altro) -> dict:
    env = {k: v for k, v in os.environ.items() if k not in ("WT_SESSION", "TERM_PROGRAM", "ARTURO_SCHEDA_USCITA")}
    env.update(HOME=str(radice.parent), USERPROFILE=str(radice.parent), CLAUDE_CONFIG_DIR=str(radice),
               ARTURO_RADICE=str(radice), PYTHONDONTWRITEBYTECODE="1", PYTHONIOENCODING="utf-8", **altro)
    return env


def modulo(repo: Path, codice: str):
    f = repo / "hooks" / "aspetto_valori.py"
    assert f.is_file(), f"{codice} manca hooks/aspetto_valori.py"
    sys.path.insert(0, str(repo / "hooks"))
    try:
        spec = importlib.util.spec_from_file_location(f"aspetto_{codice}", f)
        m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
    finally:
        sys.path.pop(0)
    return m


def test_as01(repo: Path) -> None:
    m = modulo(repo, "AS01")
    radice = casa({"dafare": {"colori": {"tela": "#1E1E1E", "inchiostro": "f0f0f0", "ombra": "#000000"}},
                   "scheda": {"colori": {"fermo": [1, 2, 3], "lavoro": [300, 0, 0], "sogno": [1, 1, 1]},
                              "decac": {"chiusa": 5, "fermo": 22}},
                   "barra": {"spenti": ["quota", "meteo"], "aggiunta": "../fuori.js"}, "altro": 1})
    try:
        validi, errori = m.leggi(radice / "personale" / "aspetto.json")
        assert validi == {"dafare": {"colori": {"tela": "#1e1e1e"}}, "scheda": {"colori": {"fermo": [1, 2, 3]},
                          "decac": {"chiusa": 5}}, "barra": {"spenti": ["quota"]}}, f"AS01 valori validi sbagliati: {validi}"
        for pezzo in ("altro", "inchiostro", "ombra", "lavoro", "sogno", "decac.fermo", "meteo", "../fuori.js"):
            assert any(pezzo in e for e in errori), f"AS01 manca l'errore su {pezzo}: {errori}"
        (radice / "personale" / "aspetto.json").write_text("{rotto", encoding="utf-8")
        validi, errori = m.leggi(radice / "personale" / "aspetto.json")
        assert validi == {} and len(errori) == 1, f"AS01 un JSON rotto: {validi} {errori}"
        assert m.leggi(radice / "personale" / "manca.json") == ({}, []), "AS01 senza file nasce un valore o un errore"
    finally:
        shutil.rmtree(radice.parent, ignore_errors=True)


def scheda(repo: Path, radice: Path, terminale: dict, evento: str) -> str:
    uscita = radice.parent / "uscita.txt"
    if uscita.exists():
        uscita.unlink()
    dati = {"hook_event_name": evento, "session_id": "aspetto-1", "cwd": str(radice.parent)}
    subprocess.run([sys.executable, "-B", str(repo / "hooks" / "scheda-terminale.py")], input=json.dumps(dati).encode(),
                   env=ambiente(radice, ARTURO_SCHEDA_USCITA=str(uscita), **terminale), capture_output=True, timeout=30)
    return read(uscita)


def test_as02(repo: Path) -> None:
    radice = casa({"scheda": {"colori": {"lavoro": [11, 22, 33]}, "decac": {"lavoro": 6}}})
    try:
        it = scheda(repo, radice, {"TERM_PROGRAM": "iTerm.app"}, "UserPromptSubmit")
        assert "bg;red;brightness;11\x07" in it and "bg;blue;brightness;33\x07" in it, \
            f"AS02 iTerm2 non usa l'RGB di aspetto.json: {it!r}"
        shutil.rmtree(radice / "cache", ignore_errors=True)  # stesso stato e progetto: la scheda non riscriverebbe
        wt = scheda(repo, radice, {"WT_SESSION": "1"}, "UserPromptSubmit")
        assert "\x1b[2;15;6,|" in wt, f"AS02 Windows Terminal non usa l'indice di aspetto.json: {wt!r}"
        shutil.rmtree(radice / "cache", ignore_errors=True)
        serie = scheda(repo, radice, {"TERM_PROGRAM": "iTerm.app"}, "SessionStart")
        assert "bg;red;brightness;40\x07" in serie, f"AS02 uno stato non nominato perde il colore di serie: {serie!r}"
    finally:
        shutil.rmtree(radice.parent, ignore_errors=True)


def barra(repo: Path, radice: Path) -> subprocess.CompletedProcess:
    dati = {"session_id": "aspetto-barra-1", "workspace": {"current_dir": str(radice.parent)},
            "model": {"display_name": "Opus"}, "rate_limits": {"five_hour": {"used_percentage": 40}},
            "context_window": {"remaining_percentage": 70}}
    return subprocess.run(["node", str(repo / "hooks" / "statusline.js")], input=json.dumps(dati).encode(),
                          env=ambiente(radice), capture_output=True, timeout=30)


def test_as03(repo: Path) -> None:
    js = "module.exports = d => `\\x1b[35mmio ${d.model.display_name}\\x07\\x1b]0;titolo`;\n"
    radice = casa({"barra": {"spenti": ["quota"], "aggiunta": "barra.js"}}, js)
    try:
        piena = barra(repo, casa(None)).stdout.decode("utf-8", "replace")
        assert "5 ore" in piena, f"AS03 la prova non vale: la barra di serie non mostra la quota ({piena!r})"
        uscita = barra(repo, radice).stdout.decode("utf-8", "replace")
        assert "5 ore" not in uscita, f"AS03 il pezzo quota spento resta nella barra: {uscita!r}"
        assert "\x1b[35mmio Opus" in uscita, f"AS03 la barra non accoda il testo di personale/barra.js: {uscita!r}"
        assert "\x07" not in uscita and "\x1b]" not in uscita, f"AS03 il testo della persona porta caratteri di controllo: {uscita!r}"
        (radice / "personale" / "barra.js").write_text("module.exports = () => { throw new Error('rotto') }\n", encoding="utf-8")
        rotta = barra(repo, radice)
        assert rotta.returncode == 0 and "Opus" in rotta.stdout.decode("utf-8", "replace"), \
            f"AS03 una barra.js che lancia un errore rompe la barra: {rotta.stdout!r} {rotta.stderr[-200:]!r}"
    finally:
        shutil.rmtree(radice.parent, ignore_errors=True)


def arturo(repo: Path, radice: Path, *argomenti: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(repo / "bin" / "arturo"), *argomenti], env=ambiente(radice),
                          capture_output=True, text=True, timeout=60)


def test_as04(repo: Path) -> None:
    radice = casa({"dafare": {"colori": {"tela": "#101010", "sera": "nero"}}})
    try:
        r = arturo(repo, radice, "aspetto", "mostra", "dafare")
        assert r.returncode == 0, f"AS04 arturo aspetto mostra dafare esce {r.returncode}: {r.stderr[-200:]}"
        assert json.loads(r.stdout or "{}") == {"colori": {"tela": "#101010"}}, f"AS04 la palette resa è sbagliata: {r.stdout!r}"
        sorgente = read(repo / "skills" / "arturo" / "hooks" / "dafare" / "register.tsx")
        assert "['mostra', 'dafare'], 'aspetto'" in sorgente, "AS04 il pannello non chiede la palette alla CLI"
        assert "COLORE_GRUPPO" not in sorgente and "COLORE_PAROLA" not in sorgente, \
            "AS04 il pannello calcola i colori di gruppi e parole una volta sola, prima della palette della persona"
    finally:
        shutil.rmtree(radice.parent, ignore_errors=True)


def test_as05(repo: Path) -> None:
    f = repo / "hooks" / "deriva.py"
    sys.path.insert(0, str(repo / "hooks"))
    try:
        spec = importlib.util.spec_from_file_location("deriva_as05", f)
        m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
    finally:
        sys.path.pop(0)
    assert hasattr(m, "riga_plugin"), "AS05 in deriva.py manca riga_plugin, la riga DERIVA del plugin"
    testo = m.riga_plugin({"hook": [], "file": ["hooks/statusline.js"], "plugin": {"firma": "buona", "motivo": ""}})
    assert "personale/aspetto.json" in testo, f"AS05 DERIVA su una barra cambiata non nomina aspetto.json: {testo!r}"
    guardia = m.riga_plugin({"hook": [], "file": ["hooks/data-guard.py"], "plugin": {"firma": "buona", "motivo": ""}})
    assert "aspetto.json" not in guardia, f"AS05 DERIVA nomina aspetto.json anche per una guardia: {guardia!r}"


def test_as06(repo: Path) -> None:
    assert (repo / "bin" / "aspetto.py").is_file(), "AS06 manca bin/aspetto.py"
    sbagliato, buono = casa({"barra": {"spenti": ["meteo"]}}), casa({"barra": {"spenti": ["quota"]}})
    try:
        r = arturo(repo, sbagliato, "aspetto", "controlla")
        assert r.returncode == 1 and "meteo" in r.stdout, f"AS06 controlla su un file sbagliato: {r.returncode} {r.stdout!r}"
        r = arturo(repo, buono, "aspetto", "controlla")
        assert r.returncode == 0, f"AS06 controlla su un file buono esce {r.returncode}: {r.stdout!r}"
        r = arturo(repo, sbagliato, "personale", "elenco")
        assert "aspetto.json" in r.stdout and "1 valori sbagliati" in r.stdout, f"AS06 personale elenco non nomina l'aspetto: {r.stdout!r}"
    finally:
        shutil.rmtree(sbagliato.parent, ignore_errors=True)
        shutil.rmtree(buono.parent, ignore_errors=True)


TESTS = {"AS01": test_as01, "AS02": test_as02, "AS03": test_as03, "AS04": test_as04, "AS05": test_as05, "AS06": test_as06}


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
