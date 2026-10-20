#!/usr/bin/env python3
"""HB01-HB02: il backtick negli heredoc conta come esecuzione solo dove lancia un comando (#3584).

HB01 un `nome` fra backtick in un corpo python o node (commento, template literal) non tiene
     visibile il corpo: era il falso positivo di una decina di blocchi a settimana (18/10/2026).
HB02 restano visibili i corpi che eseguono: backtick in ruby, perl e php, subprocess in python,
     child_process in node.

Sulla base 3211b74 (prima di 439a92b) ogni controllo deve fallire con un AssertionError che comincia
con il suo codice.
"""
from __future__ import annotations

import argparse
import importlib.util
from pathlib import Path

SEGNO = "SEGNO_HB"


def modulo(repo: Path):
    spec = importlib.util.spec_from_file_location("heredoc_banco", repo / "hooks" / "heredoc.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def resta(repo: Path, comando: str) -> bool:
    """Il corpo resta davanti alle guardie dopo la pulizia che fanno data-guard e commit-secret-gate."""
    hd = modulo(repo)
    return SEGNO in hd.togli(comando, lambda h: h.inerte() or h.codice_inerte())


def test_hb01(repo: Path) -> None:
    casi = [
        f"python3 - <<'EOF'\n# legge `config.json` e stampa {SEGNO}\nprint('{SEGNO}')\nEOF",
        f"node <<'EOF'\nconst x = `ciao ${{1}} {SEGNO}`;\nconsole.log(x);\nEOF",
    ]
    for c in casi:
        assert not resta(repo, c), f"HB01 il backtick tiene visibile un corpo che non esegue niente: {c.splitlines()[0]}"


def test_hb02(repo: Path) -> None:
    casi = [
        f"ruby <<'EOF'\nputs `echo {SEGNO}`\nEOF",
        f"perl <<'EOF'\nprint `echo {SEGNO}`;\nEOF",
        f"php <<'EOF'\n<?php echo `echo {SEGNO}`;\nEOF",
        f"python3 - <<'EOF'\nimport subprocess\nsubprocess.run(['echo', '{SEGNO}'])\nEOF",
        f"node <<'EOF'\nrequire('child_process').execSync('echo {SEGNO}');\nEOF",
    ]
    for c in casi:
        assert resta(repo, c), f"HB02 un corpo che esegue sparisce dalle guardie: {c.splitlines()[0]}"
    # Sulla base anche HB02 deve dare rosso: lì il backtick era esecuzione in ogni interprete, quindi
    # il controllo che lo distingue è la coppia. Un corpo python col backtick visibile è il segno della base.
    assert not resta(repo, f"python3 - <<'EOF'\n# `x`\nprint('{SEGNO}')\nEOF"), \
        "HB02 il backtick in python conta ancora come esecuzione: la distinzione fra interpreti manca"


TESTS = {"HB01": test_hb01, "HB02": test_hb02}


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
        assert not altro and len(rossi) == len(TESTS), \
            "baseline non discriminante: ogni controllo deve fallire col suo codice.\n" + "\n".join(altro + rossi)
        print(f"BASELINE_DISCRIMINANTE={','.join(r.split(':')[0] for r in rossi)}")
        return 0
    for test in TESTS.values():
        test(repo)
    print(f"PASS {','.join(TESTS)} controlli={len(TESTS)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
