#!/usr/bin/env python3
"""RI01: reinstallare Arturo non fa perdere niente della persona (#3825, 23/10/2026; plugin dal 22/11/2026).

Fino al 22/11/2026 il README aveva un blocco che metteva da parte ~/.claude, clonava Arturo e riportava
CLAUDE.md, personale/, memoria, todo, segnalazioni, scelte, handoff, file .local e skill della persona, e
RI01 lo eseguiva in una HOME usa e getta. Dal passo 5b della revisione del 22/11 (decisione D2) Arturo si
installa e si reinstalla come plugin: `claude plugin install` scrive solo in plugins/, e i file della persona
restano dove sono. La prova vera sta nel banco dell'installatore, tests/test_installa.py del ramo landing-v2
(caso_nuova: ~/.claude uguale byte per byte, salvo plugins/, arturo/ e le due voci di settings.json).

RI01 il README non ha più il blocco che sposta ~/.claude e riporta i file uno per uno: dà i comandi del plugin.
     Un blocco tornato riporterebbe la lista da tenere allineata a mano, che il 22/10 aveva già perso dei file.

Sulla base f4ae0aa il controllo deve fallire con un AssertionError che comincia con il suo codice.
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path


def test_ri01(repo: Path) -> None:
    readme = (repo / "README.md").read_text(encoding="utf-8")
    blocco = re.search(r"```bash\n(B=\"\$HOME/\.claude-backup.*?)```", readme, re.S)
    assert not blocco, "RI01 il README reinstalla ancora col clone e la lista dei file da riportare"
    assert "claude plugin install arturo@arturo" in readme, "RI01 il README non reinstalla col plugin"


TESTS = {"RI01": test_ri01}


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
