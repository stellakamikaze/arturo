#!/usr/bin/env python3
"""CF01-CF03: revisione della config del 19/10/2026.

CF01 nessuna regola allow approva per intero un comando che esegue codice o riscrive file con un
     flag: `rg --pre script`, `sed -n -i`, `find -fprint`, `awk 'system()'`, `xargs`. Le forme di
     sola lettura le approva già Claude Code da solo, nella cartella di lavoro.
CF02 `fallbackModel`: se il modello principale è sovraccarico, la sessione prosegue con Sonnet
     invece di fermarsi con un errore.
CF03 context-monitor.js non legge più `.planning/config.json`, resto di un altro framework.

Sulla base 439a92b ogni controllo deve fallire con un AssertionError che comincia con il suo codice.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

# Comandi con un flag che esegue un programma o scrive un file: una regola `Bash(<cmd>…:*)` li
# approva in tutte le forme e salta sia la domanda sia il classificatore della modalità auto.
CON_FLAG_PERICOLOSI = ("rg", "sed", "find", "awk", "xargs")


def impostazioni(repo: Path) -> dict:
    return json.loads((repo / "settings.json").read_text(encoding="utf-8"))


def test_cf01(repo: Path) -> None:
    for voce in impostazioni(repo)["permissions"]["allow"]:
        m = re.fullmatch(r"Bash\(([^\s:)]+)[^)]*\)", voce)
        assert not (m and m.group(1) in CON_FLAG_PERICOLOSI), \
            f"CF01 {voce} approva anche le forme che eseguono codice o riscrivono file"


def test_cf02(repo: Path) -> None:
    riserva = impostazioni(repo).get("fallbackModel")
    assert isinstance(riserva, list) and riserva and all(isinstance(x, str) and x for x in riserva), \
        f"CF02 fallbackModel assente o vuoto: {riserva!r}"


def test_cf03(repo: Path) -> None:
    testo = (repo / "hooks" / "context-monitor.js").read_text(encoding="utf-8")
    assert ".planning" not in testo, "CF03 context-monitor.js legge ancora .planning/config.json"


TESTS = {"CF01": test_cf01, "CF02": test_cf02, "CF03": test_cf03}


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
