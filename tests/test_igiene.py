#!/usr/bin/env python3
"""IG01-IG04: l'igiene del repository pubblico regge e non contiene i nomi che cerca (17/10/2026, #3505).

Fino al 16/10/2026 i test tenevano i nomi della config privata spezzati in due ("xx", "yy"): leggibili
da chiunque apra il file, e il controllo li cercava solo interi o staccati da uno spazio o un trattino.

IG01 il controllo nuovo (tests/igiene.py, accanto a questo banco) non trova niente nel repository: né
     i nomi né le loro metà. Sulla base 93f323e trova le tuple spezzate dei test.
IG02 il controllo del repository riconosce un termine anche con un punto in mezzo, un a capo dopo un
     trattino, un carattere invisibile, una lettera cirillica, uno spazio, le maiuscole, la forma larga.
     Il termine di prova è inventato: le impronte vere non si mettono alla prova senza scriverle.
IG03 il controllo legge anche i percorsi dei file e i messaggi dei commit dell'intervallo, e il rapporto
     non ripete mai il termine.
IG04 un workflow di GitHub Actions lancia il solo controllo di igiene su ogni push, su ogni branch, in
     sola lettura, e solo nel repository pubblico di Arturo (19/10/2026, segnalazione n. 4).

Sulla base 93f323e ogni controllo deve fallire con un AssertionError che comincia con il suo codice.
"""
from __future__ import annotations

import argparse
import importlib.util
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml

QUI = Path(__file__).resolve().parent
PROVA = "zorbaquix"  # inventato: nessun significato, nessuna persona
VARIANTI = ("zorba.quix", "zorba-\nquix", "zor​baquix", "zоrbaquix", "Zorba Quix", "ZorbaQuix", "ZORBA_QUIX",
            "ｚｏｒｂａｑｕｉｘ", "zorba­quix")
GIT_ENV = {"GIT_AUTHOR_NAME": "a", "GIT_AUTHOR_EMAIL": "a@example.invalid", "GIT_COMMITTER_NAME": "a",
           "GIT_COMMITTER_EMAIL": "a@example.invalid", "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1"}


def modulo(percorso: Path, codice: str):
    assert percorso.is_file(), f"{codice} manca {percorso.name}: il controllo di igiene non ha un modulo suo"
    spec = importlib.util.spec_from_file_location(f"igiene_{codice}", str(percorso))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def test_ig01(repo: Path) -> None:
    nuovo = modulo(QUI / "igiene.py", "IG01")
    problemi = nuovo.controlla(repo)
    assert not problemi, "IG01 nomi della config privata, interi o spezzati, nel repository: " + "; ".join(problemi[:8])


def test_ig02(repo: Path) -> None:
    ig = modulo(repo / "tests" / "igiene.py", "IG02")
    h = ig.impronta(PROVA)
    mancate = [repr(v) for v in VARIANTI if not ig.trova(f"prima {v} dopo", {h})]
    assert not mancate, f"IG02 varianti che il controllo non vede: {mancate}"
    assert not ig.trova("una zorba e una quixote", {h}) and not ig.trova("zorbaquixote", {h}), \
        "IG02 il controllo unisce parole che non formano il termine"


def test_ig03(repo: Path) -> None:
    ig = modulo(repo / "tests" / "igiene.py", "IG03")
    h = ig.impronta(PROVA)
    with tempfile.TemporaryDirectory() as d:
        r = Path(d)

        def git(*a: str) -> str:
            return subprocess.run(["git", "-C", str(r), *a], env=dict(os.environ, **GIT_ENV), capture_output=True,
                                  text=True, check=True, timeout=30).stdout.strip()
        git("init", "-q", "-b", "main")
        (r / "pulito.md").write_text("niente\n", encoding="utf-8")
        git("add", "-A")
        git("commit", "-q", "-m", "vecchio commit con Zorba.Quix, gia' pubblicato")
        vecchio = git("rev-parse", "HEAD")
        (r / "note").mkdir()
        (r / "note" / "zorba-quix.md").write_text("niente\n", encoding="utf-8")
        git("add", "-A")
        git("commit", "-q", "-m", "aggiunge le note\n\nscritte da Zor​ba Quix")
        problemi = ig.controlla(r, f"{vecchio}..HEAD", {h})
        assert any("percorso" in p and "note/" in p for p in problemi), f"IG03 il percorso non si controlla: {problemi}"
        assert any(p.startswith("commit") for p in problemi), f"IG03 i messaggi dei commit non si controllano: {problemi}"
        assert not any(vecchio[:7] in p for p in problemi), f"IG03 un commit fuori dall'intervallo si controlla: {problemi}"
        assert not any("zorba" in p.lower() or "quix" in p.lower() for p in problemi if not p.startswith("percorso")), \
            f"IG03 il rapporto ripete il termine: {problemi}"


def test_ig04(repo: Path) -> None:
    f = repo / ".github" / "workflows" / "igiene.yml"
    assert f.is_file(), "IG04 manca .github/workflows/igiene.yml"
    dati = yaml.safe_load(f.read_text(encoding="utf-8"))
    quando = dati.get("on", dati.get(True)) or {}
    assert set(quando) == {"push"} and quando["push"].get("branches") == ["**"], f"IG04 non parte su ogni push di ogni branch: {quando}"
    assert dati.get("permissions") == {"contents": "read"}, f"IG04 permessi non in sola lettura: {dati.get('permissions')}"
    lavori = dati.get("jobs") or {}
    assert len(lavori) == 1, f"IG04 il workflow fa più di un lavoro: {list(lavori)}"
    passi = next(iter(lavori.values())).get("steps") or []
    comandi = [p["run"] for p in passi if "run" in p]
    azioni = [p["uses"] for p in passi if "uses" in p]
    assert len(comandi) == 1 and "python3 tests/igiene.py" in comandi[0] and "--intervallo" in comandi[0], \
        f"IG04 il workflow non lancia il solo controllo di igiene: {comandi}"
    assert all(a.startswith("actions/checkout@") and len(a.split("@")[1]) == 40 for a in azioni), \
        f"IG04 azioni non fissate a un commit: {azioni}"


TESTS = {"IG01": test_ig01, "IG02": test_ig02, "IG03": test_ig03, "IG04": test_ig04}


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
