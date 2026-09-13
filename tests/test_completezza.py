#!/usr/bin/env python3
"""K1-K6: lacune trovate dalla review di completezza del 13/9/2026.

Documentazione rimasta indietro rispetto al codice e un canale novita' che
perdeva una voce. Sulla base ee10fc6 ogni controllo deve fallire per conto suo.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_k1(repo: Path) -> None:
    intestazioni = [row[3:] for row in read(repo / "NOVITA.md").splitlines() if row.startswith("## ")]
    doppie = sorted({h for h in intestazioni if intestazioni.count(h) > 1})
    assert not doppie, f"K1 intestazioni di NOVITA ripetute: il segnalibro non le distingue {doppie}"
    assert any("Seconda passata" in h for h in intestazioni), "K1 la seconda passata non ha un'entry sua: chi ha gia' letto il 13/9 non la vede"


def test_k2(repo: Path) -> None:
    readme = read(repo / "README.md")
    assert "regex `INTERNAL`" not in readme, "K2 il README cita la regex INTERNAL, che non esiste piu'"
    assert "INTERNAL_HOSTS" in readme, "K2 il README non dice dove aggiungere un host interno"


def test_k3(repo: Path) -> None:
    readme = read(repo / "README.md")
    for promessa in ('"non eseguibile"', "WARN su `MEMORY.md`", "serve `gtimeout`"):
        assert promessa not in readme, f"K3 il README descrive un controllo che audit.sh non fa: {promessa}"


def test_k4(repo: Path) -> None:
    skill = read(repo / "skills" / "system-audit" / "SKILL.md")
    description = skill.split("when_to_use:", 1)[0]
    assert "comandi inesistenti" not in description, "K4 la description di system-audit promette controlli che lo script non fa"


def test_k5(repo: Path) -> None:
    riga = next((row for row in read(repo / "commands" / "fine.md").splitlines() if row.startswith("| Config sync")), "")
    assert "non riuscito" in riga, f"K5 la tabella di chiusura non prevede il push rimasto indietro: {riga.strip()!r}"


def test_k6(repo: Path) -> None:
    assert "fetch --quiet upstream" in read(repo / "commands" / "inizio.md"), "K6 nessuno aggiorna upstream/main: l'avviso di session-start resta muto"


TESTS = {"K1": test_k1, "K2": test_k2, "K3": test_k3, "K4": test_k4, "K5": test_k5, "K6": test_k6}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--baseline-ref")
    args = parser.parse_args()
    repo = args.repo.resolve()
    if args.baseline_ref:
        failed = []
        for name, test in TESTS.items():
            try:
                test(repo)
            except AssertionError:
                failed.append(name)
        assert failed == list(TESTS), f"baseline non discriminante: falliscono solo {failed} su {list(TESTS)}"
        print(f"BASELINE_DISCRIMINANTE={','.join(failed)}")
        return 0
    for test in TESTS.values():
        test(repo)
    print(f"PASS {','.join(TESTS)} controlli={len(TESTS)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
