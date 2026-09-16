#!/usr/bin/env python3
"""P01-P04: la porta d'ingresso di Arturo come prodotto (16/9/2026).

Il README deve dire cosa non e' neutro e cosa Arturo promette a chi lo usa, e le
promesse devono corrispondere al codice. Sulla base ee10fc6 ogni controllo deve
fallire per conto suo.
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def sezione(readme: str, titolo: str) -> str:
    match = re.search(rf"^## {re.escape(titolo)}\n(.*?)(?=^## |\Z)", readme, re.M | re.S)
    return match.group(1) if match else ""


def test_p01(repo: Path) -> None:
    testo = sezione(read(repo / "README.md"), "Cosa non è neutro")
    assert "Anthropic" in testo, "P01 il README non dice che Claude Code e' un servizio di Anthropic"
    assert "docs/principi/00-chi-possiede-lo-strumento.md" in testo, "P01 la sezione non rimanda al capitolo 00"


def test_p02(repo: Path) -> None:
    testo = sezione(read(repo / "README.md"), "Impegni")
    for parola in ("MIT", "telemetria", "fork", "NOVITA.md"):
        assert parola in testo, f"P02 gli impegni non nominano {parola}"


def test_p03(repo: Path) -> None:
    testo = sezione(read(repo / "README.md"), "Impegni")
    assert testo, "P03 nessuna sezione Impegni"
    assert "senza il tuo sì" not in testo.replace("dopo il tuo sì", ""), "P03 gli impegni promettono aggiornamenti solo col tuo sì"
    if re.search(r"git -C ~/\.claude pull", read(repo / "commands" / "inizio.md")):
        assert "/inizio" in testo, "P03 /inizio applica gli aggiornamenti ma gli impegni non lo dicono"


def test_p04(repo: Path) -> None:
    testo = sezione(read(repo / "README.md"), "Impegni")
    avvio = read(repo / "hooks" / "session-start.sh")
    assert "sei ore" in testo, "P04 gli impegni non dicono ogni quanto parte il controllo degli aggiornamenti"
    assert "-gt 21600" in avvio, "P04 session-start non controlla piu' ogni sei ore: l'impegno e' falso"


TESTS = {"P01": test_p01, "P02": test_p02, "P03": test_p03, "P04": test_p04}


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
            except (AssertionError, FileNotFoundError):
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
