#!/usr/bin/env python3
"""P01-P08: i mod portati dalla config dell'autore (9/10/2026, rivisti il 14/10 e il 15/10/2026).

P01, P02, P04 redazione-segreti, riscrivi-bash e cache-fredda passano claude plugin validate e
claude plugin test. P03 menu-contesto e agent-flow (tolti il 14/10/2026) e blast-radius (tolto il
15/10/2026, era su main dal 14/10) non ci sono più, e NOVITA.md annuncia ogni uscita. P06 nei mod non ci sono nomi, host o percorsi personali. P08 il README nomina ogni mod.
P05 e P07 (blast-radius) sono usciti col mod.

Il gate richiede il binario `claude`: se manca, il banco fallisce con un messaggio esplicito.
Sulla base cddcb10 ogni controllo deve fallire.
"""
from __future__ import annotations

import argparse
import re
import shutil
import subprocess
from pathlib import Path
from typing import Callable, Dict, List

MOD = ("redazione-segreti", "riscrivi-bash", "cache-fredda")
TOLTI = ("menu-contesto", "agent-flow", "blast-radius")
# Le parole sono spezzate: il controllo di igiene I03 legge anche i test.
PERSONALI = re.compile("|".join(re.escape(a + b) for a, b in (("fede", "rico"), ("gani", "mede"), ("fur", "ore"), ("/Us", "ers/")))
                       + r"|\buf-[a-z]", re.IGNORECASE)


def claude() -> str:
    exe = shutil.which("claude")
    assert exe is not None, "claude mancante: il banco prova i mod con claude plugin validate e claude plugin test"
    return exe


def prova_mod(repo: Path, nome: str, codice: str, con_test: bool = True) -> None:
    cartella = repo / "skills" / nome
    assert (cartella / ".claude-plugin" / "plugin.json").is_file(), f"{codice} manca skills/{nome}"
    # Claude Code scrive in UTF-8: letto con la codifica di Windows lo stdout diventa None.
    v = subprocess.run([claude(), "plugin", "validate", str(cartella)], capture_output=True, text=True,
                       encoding="utf-8", errors="replace", timeout=120)
    assert v.returncode == 0, f"{codice} validate di {nome}: rc={v.returncode} {v.stdout[-300:]}{v.stderr[-200:]}"
    if not con_test:
        return
    t = subprocess.run([claude(), "plugin", "test", str(cartella)], capture_output=True, text=True,
                       encoding="utf-8", errors="replace", timeout=180)
    esito = t.stdout + t.stderr
    assert t.returncode == 0 and re.search(r"\b0 fail\b", esito), f"{codice} plugin test di {nome}: rc={t.returncode} {esito[-300:]}"


def test_p06(repo: Path) -> None:
    trovati: List[str] = []
    for nome in MOD:
        cartella = repo / "skills" / nome
        assert cartella.is_dir(), f"P06 manca skills/{nome}"
        for f in sorted(cartella.rglob("*")):
            if not f.is_file() or ".claude-plugin/types" in f.as_posix() or f.name in ("tsconfig.json", "LICENSE"):
                continue
            for riga, linea in enumerate(f.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
                if f.name == "plugin.json" and "Nejrotti" in linea:
                    continue
                if PERSONALI.search(linea):
                    trovati.append(f"{f.relative_to(repo)}:{riga}: {linea.strip()[:100]}")
    assert not trovati, "P06 dati personali nei mod: " + "; ".join(trovati[:5])


def test_p03(repo: Path) -> None:
    rimasti = [m for m in TOLTI if (repo / "skills" / m).exists()]
    assert not rimasti, f"P03 mod tolti ancora presenti: {rimasti}"
    # Chi li aveva li perde con /aggiorna: NOVITA.md deve dirglielo.
    novita = (repo / "NOVITA.md").read_text(encoding="utf-8")
    annunciati = [m for m in TOLTI if re.search(rf"[Ee]sc(?:e|ono)\b[^\n]*\n?[^\n]*`{m}`", novita)]
    assert annunciati == list(TOLTI), f"P03 NOVITA.md non annuncia l'uscita di {[m for m in TOLTI if m not in annunciati]}"


def test_p08(repo: Path) -> None:
    readme = (repo / "README.md").read_text(encoding="utf-8")
    mancanti = [m for m in MOD if f"skills/{m}/" not in readme]
    assert not mancanti, f"P08 il README non nomina {mancanti}"


TESTS: Dict[str, Callable[[Path], None]] = {
    "P01": lambda r: prova_mod(r, "redazione-segreti", "P01"),
    "P02": lambda r: prova_mod(r, "riscrivi-bash", "P02"),
    "P03": test_p03,
    "P04": lambda r: prova_mod(r, "cache-fredda", "P04"),
    "P06": test_p06,
    "P08": test_p08,
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--baseline-ref")
    parser.add_argument("--solo", nargs="+", choices=list(TESTS), help="solo questi controlli (per i veleni)")
    args = parser.parse_args()
    repo = args.repo.resolve()
    if args.solo:
        for nome in args.solo:
            TESTS[nome](repo)
        print(f"PASS {','.join(args.solo)} controlli={len(args.solo)} (solo)")
        return 0
    if args.baseline_ref:
        failed = []
        for name, test in TESTS.items():
            try:
                test(repo)
            except (AssertionError, OSError, ValueError, subprocess.SubprocessError):
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
