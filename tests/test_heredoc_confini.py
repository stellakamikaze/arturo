#!/usr/bin/env python3
"""HC01-HC07: le guardie tolgono il corpo di un heredoc solo quando i confini sono certi (15/10/2026).

La review del 15/10 ha trovato comandi che la shell esegue e che le guardie non vedevano, perché un
confine letto male faceva sparire il testo. Ogni controllo prova che il testo dopo il confine
(SEGNO) resta visibile a tutte e quattro le guardie: commit-secret-gate, block-dangerous,
data-guard, comms-prefilter.

HC01 delimitatore intero e chiusura esatta: `<<'E'OF` chiude su EOF, `<<'EOF'x` su EOFx, una
     chiusura indentata non chiude (con `<<-` valgono solo i tab).
HC02 `<<` dentro virgolette o in un commento non apre un heredoc.
HC03 il corpo che qualcuno esegue resta: pipe a fine riga, `\\` e pipe, `| /bin/bash`, `. /dev/stdin`,
     `$( )`, `while read; do $l`, file scritto e poi eseguito.
HC04 due heredoc sulla stessa riga hanno lo stesso consumatore: `bash <<'A' <<'B'`.
HC05 una `\\` a fine riga dentro un corpo quotato è testo: non incolla la chiusura alla riga dopo.
HC06 `-m "` dentro altre virgolette non è un messaggio di commit.
HC08 dal vivo, col dispatcher completo: un rm scritto in un file e poi eseguito, o dopo un `<<`
     dentro virgolette, chiede conferma.
HC07 nessun falso allarme nuovo: cat su file, tee e poi `git add`, python senza programmi lanciati,
     il messaggio vero di git commit restano tolti.

Sulla base 7c8e0a0 ogni controllo deve fallire col suo codice.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Callable, Dict

GUARDIE = {"commit-secret-gate": ("commit-secret-gate.py", "_senza_heredoc"),
           "block-dangerous": ("block-dangerous.py", "_testo_shell"),
           "data-guard": ("data-guard.py", "_senza_testo"),
           "comms-prefilter": ("comms-prefilter.py", "reduce")}
SEGRETO = "~/.s" + "sh/id_ed25519"


def _carica(path: Path):
    spec = importlib.util.spec_from_file_location(path.stem.replace("-", "_") + "_hc", path)
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
    return {g: getattr(_carica(repo / "hooks" / f), fn) for g, (f, fn) in GUARDIE.items()}


def _visibile(codice: str, repo: Path, casi: Dict[str, str]) -> None:
    parser = _parser(repo)
    for nome, comando in casi.items():
        for guardia, f in parser.items():
            assert "SEGNO" in f(comando), f"{codice} {guardia} · {nome}: toglie il testo dopo il confine"


def test_hc01(repo: Path) -> None:
    _visibile("HC01", repo, {
        "'E'OF": "cat <<'E'OF\nx\nEOF\nSEGNO\nE",
        "'EOF'x": "cat > f.txt <<'EOF'x\nx\nEOFx\nSEGNO\nEOF",
        "chiusura indentata": "tee /dev/null <<'EOF'\n  EOF\nx <<'Z'\nEOF\nSEGNO\nZ",
        "<<- chiude sul tab": "cat <<-'EOF'\nx\n\tEOF\nSEGNO\nEOF",
    })


def test_hc02(repo: Path) -> None:
    _visibile("HC02", repo, {
        "virgolette": "echo \"<<'A'\"\nSEGNO\nA",
        "commento": "# vedi cat <<'A'\nSEGNO\nA",
        "stringa su più righe": "echo \"inizio\ncat <<'A'\nfine\"\nSEGNO\nA",
    })


def test_hc03(repo: Path) -> None:
    _visibile("HC03", repo, {
        "pipe a fine riga": "cat <<'EOF' |\nSEGNO\nEOF\nbash",
        "barra e pipe": "cat <<'EOF' \\\n| bash\nSEGNO\nEOF",
        "/bin/bash": "cat <<'EOF' | /bin/bash\nSEGNO\nEOF",
        "punto": ". /dev/stdin <<'EOF'\nSEGNO\nEOF",
        "dentro $( )": "X=$(cat <<'EOF'\nSEGNO\nEOF\n)",
        "while read": "while read -r l; do $l; done <<'EOF'\nSEGNO\nEOF",
        "file eseguito sulla riga": "cat <<'EOF' > /tmp/x.sh && bash /tmp/x.sh\nSEGNO\nEOF",
        "file eseguito dopo": "cat > x.txt <<'EOF'\nSEGNO\nEOF\nsh x.txt",
    })


def test_hc04(repo: Path) -> None:
    _visibile("HC04", repo, {"bash con due heredoc": "bash <<'A' <<'B'\nuno\nA\nSEGNO\nB"})


def test_hc05(repo: Path) -> None:
    comando = "cat >/dev/null <<'EOF'\nx \\\nEOF\ncat " + SEGRETO + "\ncat >/dev/null <<'EOF'\ny\nEOF"
    p = subprocess.run([sys.executable, str(repo / "hooks" / "block-dangerous.py")],
                       input=json.dumps({"tool_name": "Bash", "tool_input": {"command": comando}}),
                       capture_output=True, text=True, timeout=60)
    assert p.returncode == 2 or '"ask"' in p.stdout, \
        f"HC05 block-dangerous non vede la lettura dopo una \\ in un corpo quotato: rc={p.returncode} {p.stdout[:120]!r}"
    dg = _carica(repo / "hooks" / "data-guard.py")
    assert "SEGNO" in dg._senza_testo("cat >/dev/null <<'EOF'\nx \\\nEOF\nSEGNO\ncat >/dev/null <<'EOF'\ny\nEOF"), \
        "HC05 data-guard incolla la chiusura alla riga dopo"


def test_hc06(repo: Path) -> None:
    bd = _carica(repo / "hooks" / "block-dangerous.py")
    assert "SEGNO" in bd._testo_shell("echo ' -m \"' ; SEGNO ; echo '\"'"), "HC06 un -m dentro apici svuota il comando"


def test_hc07(repo: Path) -> None:
    hd = _carica(repo / "hooks" / "heredoc.py")
    assert hasattr(hd, "Heredoc") and hasattr(hd.Heredoc, "inerte"), "HC07 heredoc.py senza la regola del lettore inerte"
    parser = _parser(repo)
    for nome, comando in {"cat su file": "cat > f.txt <<'EOF'\nSEGNO\nEOF",
                          "tee e git add": "tee a.md <<'EOF'\nSEGNO\nEOF\ngit add a.md"}.items():
        for guardia, f in parser.items():
            assert "SEGNO" not in f(comando), f"HC07 {guardia} · {nome}: falso allarme nuovo"
    bd = _carica(repo / "hooks" / "block-dangerous.py")
    assert "SEGNO" not in bd._testo_shell("python3 - <<'PY'\nprint('SEGNO')\nPY"), "HC07 block-dangerous: python senza programmi"
    assert "SEGNO" not in bd._testo_shell("git commit -m \"tolto SEGNO dal README\""), "HC07 block-dangerous: messaggio di commit"


def test_hc08(repo: Path) -> None:
    spec = importlib.util.spec_from_file_location("guardie_unite_hc", Path(__file__).with_name("test_guardie_unite.py"))
    assert spec and spec.loader
    gu = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gu)
    cancella = "r" + "m -rf ~/lavoro"
    with tempfile.TemporaryDirectory() as d:
        radice = Path(d)
        home = gu.casa(repo, radice)
        for nome, comando in {"file eseguito": "cat <<'EOF' > /tmp/x.sh && bash /tmp/x.sh\n" + cancella + "\nEOF",
                              "virgolette": "echo \"<<'A'\"\n" + cancella + "\nA"}.items():
            esito = gu.dispatcher(home, comando, radice)
            assert esito in ("ask", "block"), f"HC08 il dispatcher lascia passare · {nome}: {esito}"


TESTS: Dict[str, Callable[[Path], None]] = {
    "HC01": test_hc01, "HC02": test_hc02, "HC03": test_hc03, "HC04": test_hc04, "HC05": test_hc05,
    "HC06": test_hc06, "HC07": test_hc07, "HC08": test_hc08,
}


def baseline(scelti: Dict[str, Callable[[Path], None]], repo: Path):
    rossi, altro = [], []
    for codice, test in scelti.items():
        try:
            test(repo)
        except AssertionError as e:
            if str(e).startswith(codice):
                rossi.append(codice)
            else:
                altro.append(f"{codice}: {e}")
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
