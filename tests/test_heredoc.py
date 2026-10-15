#!/usr/bin/env python3
"""H01-H06: un solo modulo riconosce gli heredoc per le quattro guardie (15/10/2026).

Fino al 15/10 commit-secret-gate, block-dangerous, data-guard e comms-prefilter avevano ognuna il
suo parser di heredoc, e le copie divergevano. Il testo che una guardia toglie è testo che non
controlla: un parser che toglie troppo è un buco, non un falso allarme in meno.

H01 hooks/heredoc.py esiste, le quattro guardie lo usano e nessuna ha più una regex sua per `<<`.
H02 la here-string `<<<"x"` non è un heredoc: il comando dopo resta visibile a tutte e quattro.
H03 `cat <<'EOF' | bash`: il corpo va a bash, e resta visibile a tutte e quattro.
H04 un heredoc senza riga di chiusura resta visibile a tutte e quattro.
H05 delimitatore senza virgolette e `$( )` nel corpo: la shell lo esegue, resta visibile a tutte.
H06 due heredoc sulla stessa riga si leggono uno per uno: `bash <<'A'` non fa restare il corpo di
    un `cat > f <<'B'` che viene dopo, e il corpo di A resta.

Le regole già decise restano quelle di G205 (test_guardie_unite.py): questo banco aggiunge i casi
in cui le copie sbagliavano. Sulla base 62dfb51 ogni controllo deve fallire col suo codice.
"""
from __future__ import annotations

import argparse
import importlib.util
import re
import sys
from pathlib import Path
from typing import Callable, Dict

GUARDIE = {"commit-secret-gate": ("commit-secret-gate.py", "_senza_heredoc"),
           "block-dangerous": ("block-dangerous.py", "_testo_shell"),
           "data-guard": ("data-guard.py", "_senza_testo"),
           "comms-prefilter": ("comms-prefilter.py", "reduce")}


def _carica(path: Path):
    spec = importlib.util.spec_from_file_location(path.stem.replace("-", "_") + "_h", path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    argv, sys.argv = sys.argv, [str(path)]
    try:
        spec.loader.exec_module(mod)
    except SystemExit:
        pass
    finally:
        sys.argv = argv
    return mod


def _parser(repo: Path) -> Dict[str, Callable[[str], str]]:
    trovati = {}
    for guardia, (file, funzione) in GUARDIE.items():
        mod = _carica(repo / "hooks" / file)
        trovati[guardia] = getattr(mod, funzione)
    return trovati


def _visibile_a_tutte(codice: str, repo: Path, comando: str, segno: str = "SEGNO") -> None:
    for guardia, f in _parser(repo).items():
        assert segno in f(comando), f"{codice} {guardia} toglie il testo di {comando!r}"


def test_h01(repo: Path) -> None:
    modulo = repo / "hooks" / "heredoc.py"
    assert modulo.exists(), "H01 hooks/heredoc.py assente"
    assert hasattr(_carica(modulo), "togli"), "H01 heredoc.py senza togli()"
    for guardia, (file, _) in GUARDIE.items():
        testo = (repo / "hooks" / file).read_text(encoding="utf-8")
        # block-dangerous lo usa attraverso forma_comando.py, dove sta il tokenizer dal 15/10/2026.
        via_forma = "forma_comando.py" in testo and "heredoc.py" in (repo / "hooks" / "forma_comando.py").read_text(encoding="utf-8")
        assert "heredoc.py" in testo or via_forma, f"H01 {guardia} non usa hooks/heredoc.py"
        assert not re.search(r"<<-\?\\s\*", testo), f"H01 {guardia} ha ancora una regex sua per gli heredoc"


def test_h02(repo: Path) -> None:
    _visibile_a_tutte("H02", repo, "cat <<<\"x\"\nSEGNO rm -rf ~/lavoro\nx")
    _visibile_a_tutte("H02", repo, "grep -c a <<<'EOF'\nSEGNO\nEOF")


def test_h03(repo: Path) -> None:
    _visibile_a_tutte("H03", repo, "cat <<'EOF' | bash\nSEGNO\nEOF")
    _visibile_a_tutte("H03", repo, "cat <<'EOF' | sudo sh\nSEGNO\nEOF")


def test_h04(repo: Path) -> None:
    _visibile_a_tutte("H04", repo, "cat > f.txt <<'EOF'\nriga\nSEGNO")


def test_h05(repo: Path) -> None:
    _visibile_a_tutte("H05", repo, "cat > f.txt <<EOF\n$(SEGNO)\nEOF")
    _visibile_a_tutte("H05", repo, "cat > f.txt <<EOF\n`SEGNO`\nEOF")


def test_h06(repo: Path) -> None:
    comando = "bash <<'A'; cat > f.txt <<'B'\nVIVO\nA\nSEGNO\nB"
    for guardia, f in _parser(repo).items():
        testo = f(comando)
        assert "VIVO" in testo, f"H06 {guardia} toglie il corpo che va a bash"
        assert "SEGNO" not in testo, f"H06 {guardia} tiene il corpo di cat dopo un heredoc verso bash"


TESTS: Dict[str, Callable[[Path], None]] = {
    "H01": test_h01, "H02": test_h02, "H03": test_h03, "H04": test_h04, "H05": test_h05, "H06": test_h06,
}


def baseline(scelti: Dict[str, Callable[[Path], None]], repo: Path):
    rossi, altro = [], []
    for codice, test in scelti.items():
        try:
            test(repo)
        except AssertionError as e:
            (rossi if str(e).startswith(codice) else altro).append(codice if str(e).startswith(codice) else f"{codice}: {e}")
        except Exception as e:  # noqa: BLE001 - sulla base un errore qualunque non prova niente
            altro.append(f"{codice}: {type(e).__name__}: {e}")
        else:
            altro.append(f"{codice}: verde sulla base")
    return rossi, altro


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--baseline-ref")
    parser.add_argument("--solo")
    args = parser.parse_args()
    repo = args.repo.resolve()
    scelti = {k: v for k, v in TESTS.items() if not args.solo or k in args.solo.split(",")}
    if args.baseline_ref:
        rossi, altro = baseline(scelti, repo)
        assert not altro and rossi == list(scelti), \
            "baseline non discriminante: ogni controllo deve fallire col suo codice.\n" + "\n".join(altro)
        print(f"BASELINE_DISCRIMINANTE={','.join(rossi)}")
        return 0
    for test in scelti.values():
        test(repo)
    print(f"PASS {','.join(scelti)} controlli={len(scelti)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
