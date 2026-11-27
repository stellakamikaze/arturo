#!/usr/bin/env python3
"""IG04, IG07, IG08 sul ramo della landing: il workflow di igiene controlla solo i commit nuovi (27/11/2026, #6811).

Il 27/11/2026 la PR 90 (arturo-6791-minima, nata da landing-v2) ha avuto igiene rossa. Al primo push di un ramo
il "prima" è 000…0, e il workflow della landing controllava tutta la storia: I03 trovava i messaggi vecchi di
landing-v2, già pubblici. Il passo ora è lo stesso di dev, e questo banco è il sottoinsieme di tests/test_igiene.py
di dev che vale qui (la landing non ha .githooks/pre-push né i banchi datati).

IG04 il workflow parte su ogni push di ogni branch e su ogni pull request, in sola lettura, e lancia il solo
     controllo di igiene con azioni fissate a un commit.
IG07 fuori da dev il workflow toglie dall'intervallo i commit che dev ha già.
IG08 il passo del workflow gira davvero, in bash: il primo push di un ramo nato da landing-v2 non ricontrolla i
     commit che landing-v2 ha già, e un nome in un commit nuovo dà ancora rosso.

Sulla base 319ae38 (landing-v2 prima della correzione) ogni controllo fallisce con un AssertionError che comincia
con il suo codice.
"""
from __future__ import annotations

import argparse
import importlib.util
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml

# Il bash del PATH: un "bash" senza percorso, su Windows, apre il bash.exe di WSL in System32 (#6455).
BASH_VERO = shutil.which("bash") or "bash"

PROVA = "zorbaquix"  # inventato: nessun significato, nessuna persona
GIT_ENV = {"GIT_AUTHOR_NAME": "a", "GIT_AUTHOR_EMAIL": "a@example.invalid", "GIT_COMMITTER_NAME": "a",
           "GIT_COMMITTER_EMAIL": "a@example.invalid", "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1"}


def modulo(percorso: Path, codice: str):
    assert percorso.is_file(), f"{codice} manca {percorso.name}: il controllo di igiene non ha un modulo suo"
    spec = importlib.util.spec_from_file_location(f"igiene_{codice}", str(percorso))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def test_ig04(repo: Path) -> None:
    f = repo / ".github" / "workflows" / "igiene.yml"
    assert f.is_file(), "IG04 manca .github/workflows/igiene.yml"
    dati = yaml.safe_load(f.read_text(encoding="utf-8"))
    quando = dati.get("on", dati.get(True)) or {}
    assert set(quando) == {"push", "pull_request"} and quando["push"].get("branches") == ["**"], \
        f"IG04 non parte su ogni push di ogni branch e su ogni pull request: {quando}"
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


def test_ig07(repo: Path) -> None:
    f = repo / ".github" / "workflows" / "igiene.yml"
    testo = f.read_text(encoding="utf-8") if f.is_file() else ""
    assert "^origin/dev" in testo and '"$RAMO" != "dev"' in testo, \
        "IG07 fuori da dev il workflow ricontrolla i commit già su dev: la stessa email da main e da ogni ramo"


def test_ig08(repo: Path) -> None:
    f = repo / ".github" / "workflows" / "igiene.yml"
    assert f.is_file(), "IG08 manca .github/workflows/igiene.yml"
    passi = next(iter((yaml.safe_load(f.read_text(encoding="utf-8")).get("jobs") or {}).values())).get("steps") or []
    blocco = next((p["run"] for p in passi if "run" in p), "")
    assert blocco, "IG08 il workflow non ha il passo che lancia il controllo"
    sorgente = repo / "tests" / "igiene.py"
    h = modulo(sorgente, "IG08").impronta(PROVA)
    with tempfile.TemporaryDirectory() as d:
        r = Path(d)
        ambiente = dict(os.environ, **GIT_ENV, ARTURO_IGIENE_IMPRONTE_EXTRA=h)

        def git(*a: str) -> str:
            return subprocess.run(["git", "-C", str(r), *a], env=ambiente, capture_output=True, text=True,
                                  check=True, timeout=30).stdout.strip()

        def commit(messaggio: str) -> str:
            git("commit", "-q", "--allow-empty", "-m", messaggio)
            return git("rev-parse", "HEAD")

        def pubblica(**rami: str) -> None:
            for nome, sha in rami.items():
                git("update-ref", f"refs/remotes/origin/{nome}", sha)

        def esito(prima: str, dopo: str, ramo: str, evento: str = "push") -> int:
            env = dict(ambiente, PRIMA=prima, DOPO=dopo, RAMO=ramo, EVENTO=evento)
            return subprocess.run([BASH_VERO, "-e", "-c", blocco], cwd=str(r), env=env, capture_output=True, text=True,
                                  timeout=60).returncode

        zero = "0" * 40
        git("init", "-q", "-b", "dev")
        (r / "tests").mkdir()
        (r / "tests" / "igiene.py").write_bytes(sorgente.read_bytes())
        git("add", "-A")
        radice = commit("radice")
        pubblica(dev=radice)
        # landing-v2 porta un nome in un messaggio vecchio, già pubblico (come e7c5a7d e gli altri della PR 90).
        git("checkout", "-q", "-b", "landing-v2")
        landing = commit(f"landing, con {PROVA}, già pubblico")
        pubblica(**{"landing-v2": landing})
        # Il primo push di un ramo nato da landing-v2, con un solo commit nuovo e pulito.
        git("checkout", "-q", "-b", "minima")
        minima = commit("installa.sh, pulito")
        pubblica(minima=minima)
        assert esito(zero, minima, "minima") == 0, \
            "IG08 il primo push di un ramo nato da landing-v2 ricontrolla i commit che landing-v2 ha già (PR 90, #6811)"
        # Lo stesso ramo, con un nome in un commit nuovo: resta rosso.
        sporco = commit(f"nuovo, con {PROVA}")
        pubblica(minima=sporco)
        assert esito(zero, sporco, "minima") == 1, "IG08 il primo push di un ramo non controlla i suoi commit nuovi"
        # Un ramo che contiene già il commit spinto non conta: due rami spinti insieme non si tolgono il nome.
        pubblica(gemello=sporco)
        assert esito(minima, sporco, "minima") == 1, \
            "IG08 due rami spinti insieme con lo stesso commit nuovo si tolgono a vicenda: il nome passa"
        # Una pull request da un fork verso landing-v2 resta controllata.
        git("checkout", "-q", "-b", "fork", landing)
        fork = commit(f"da un fork, con {PROVA}")
        assert esito(landing, fork, "91/merge", "pull_request") == 1, \
            "IG08 una pull request da un fork non controlla i suoi commit"


TESTS = {"IG04": test_ig04, "IG07": test_ig07, "IG08": test_ig08}


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
