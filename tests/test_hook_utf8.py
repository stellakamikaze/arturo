#!/usr/bin/env python3
"""U01-U06: gli hook leggono in UTF-8 il JSON di Claude Code anche su Windows (16/10/2026).

Su Windows la pipe di un processo Python è in cp1252. Claude Code scrive il JSON in UTF-8: le
lettere accentate arrivavano storpiate e un byte che cp1252 non conosce (0x9D, dentro «”») faceva
fallire la lettura. Il banco simula quella pipe su ogni sistema con PYTHONIOENCODING=cp1252.

U01 nessun hook Python legge stdin come testo: tutti decodificano sys.stdin.buffer in UTF-8.
U02 block-dangerous chiede conferma per un rm ricorsivo anche se il comando contiene «”».
U03 emoji_remover vede l'emoji nuova in un file di codice.
U04 memoria-scrittura vede i caratteri invisibili in una nota di memoria.
U05 memoria-richiamo trova una nota con le parole accentate del messaggio.
U06 il dispatcher passa alle guardie il comando intero: un rm con «”» e un invio con «→»
chiedono conferma.

Sulla base b0ec3ac ogni controllo deve fallire con un AssertionError che comincia con il suo codice.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

# Su Windows "bash" per nome è quello di WSL: si prende il bash del PATH (Git Bash).
BASH = shutil.which("bash") or "bash"
VIRGOLETTA = "”"  # in UTF-8 è E2 80 9D: 0x9D non esiste in cp1252


def ambiente(casa: Path, **extra: str) -> dict:
    env = dict(os.environ)
    for k in ("PYTHONUTF8", "PYTHONIOENCODING", "ARTURO_MEMORIA"):
        env.pop(k, None)
    env.update(HOME=str(casa), USERPROFILE=str(casa), PYTHONDONTWRITEBYTECODE="1",
               PYTHONIOENCODING="cp1252", PYTHONUTF8="0", **extra)
    return env


def hook(repo: Path, nome: str, dati: dict, casa: Path, **extra: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, "-B", str(repo / "hooks" / nome)],
                          input=json.dumps(dati, ensure_ascii=False).encode("utf-8"),
                          capture_output=True, cwd=str(casa), env=ambiente(casa, **extra), timeout=30)


def testo(b: bytes) -> str:
    return b.decode("utf-8", errors="replace")


def test_u01(repo: Path) -> None:
    lettura = re.compile(r"json\.load\(\s*sys\.stdin\s*\)|sys\.stdin\.read\(")
    rotti = []
    for f in sorted((repo / "hooks").glob("*.py")):
        for n, riga in enumerate(f.read_text(encoding="utf-8").splitlines(), 1):
            if lettura.search(riga.split("#", 1)[0]):
                rotti.append(f"{f.name}:{n}")
    assert not rotti, f"U01 hook che leggono stdin come testo (cp1252 su Windows): {', '.join(rotti)}"


def test_u02(repo: Path) -> None:
    with tempfile.TemporaryDirectory() as d:
        casa = Path(d)
        comando = f"rm -rf ~/Documents  # pulizia {VIRGOLETTA}vecchia{VIRGOLETTA}"
        r = hook(repo, "block-dangerous.py", {"tool_name": "Bash", "tool_input": {"command": comando}, "cwd": d}, casa)
        assert r.returncode == 2 or '"ask"' in testo(r.stdout), \
            f"U02 rm ricorsivo con «”» passa senza conferma: rc={r.returncode} stdout={testo(r.stdout)[-300:]!r}"


def test_u03(repo: Path) -> None:
    with tempfile.TemporaryDirectory() as d:
        casa = Path(d)
        f = casa / "a.py"
        f.write_text("x = 1\n", encoding="utf-8")
        dati = {"tool_name": "Write", "tool_input": {"file_path": str(f), "content": f"x = 1  # {VIRGOLETTA}fatto \U0001F680\n"}}
        r = hook(repo, "emoji_remover.py", dati, casa)
        assert r.returncode == 2, f"U03 emoji nuova non vista: rc={r.returncode} stderr={testo(r.stderr)[-300:]!r}"


def test_u04(repo: Path) -> None:
    with tempfile.TemporaryDirectory() as d:
        casa = Path(d)
        nota = casa / ".claude" / "projects" / "prova" / "memory" / "nota.md"
        nota.parent.mkdir(parents=True)
        nota.write_text("", encoding="utf-8")
        contenuto = f"---\nname: nota\n---\nRicorda la città​ e la società {VIRGOLETTA}\n"
        r = hook(repo, "memoria-scrittura.py", {"tool_name": "Write", "tool_input": {"file_path": str(nota), "content": contenuto}}, casa)
        assert "invisibili" in testo(r.stdout), f"U04 caratteri invisibili non visti: rc={r.returncode} stdout={testo(r.stdout)[-300:]!r}"


def test_u05(repo: Path) -> None:
    with tempfile.TemporaryDirectory() as d:
        casa = Path(d)
        cartella = casa / ".claude" / "projects" / "prova" / "memory"
        cartella.mkdir(parents=True)
        (cartella / "fattura-societa.md").write_text(
            "---\nname: fattura-societa\ndescription: perché la società paga la città\n"
            "triggers: società, città, perché\ntype: reference\n---\nLa società paga la città.\n", encoding="utf-8")
        dati = {"prompt": "la società paga la città perché?", "session_id": "u05"}
        r = hook(repo, "memoria-richiamo.py", dati, casa, ARTURO_MEMORIA="1")
        assert "fattura-societa" in testo(r.stdout), \
            f"U05 nota con parole accentate non richiamata: rc={r.returncode} stdout={testo(r.stdout)[-300:]!r} stderr={testo(r.stderr)[-300:]!r}"


def dispatcher(casa: Path, comando: str) -> str:
    env = ambiente(casa, COMMS_REDUCED="avvelenata")
    r = subprocess.run([BASH, str(casa / ".claude" / "hooks" / "bash-dispatcher.sh")],
                       input=json.dumps({"tool_name": "Bash", "tool_input": {"command": comando}, "cwd": str(casa)},
                                        ensure_ascii=False).encode("utf-8"),
                       capture_output=True, env=env, timeout=30)
    if r.returncode == 2:
        return "block"
    uscita = testo(r.stdout)
    return "ask" if '"ask"' in uscita else "silent" if not uscita.strip() else uscita


def test_u06(repo: Path) -> None:
    with tempfile.TemporaryDirectory() as d:
        casa = Path(d) / "casa"
        shutil.copytree(repo, casa / ".claude", ignore=shutil.ignore_patterns(".git", "__pycache__", "worktrees"))
        esito = dispatcher(casa, f"rm -rf ~/Documents  # {VIRGOLETTA}vecchia{VIRGOLETTA}")
        assert esito in ("block", "ask"), f"U06 rm con «”» dal dispatcher passa senza conferma: {esito!r}"
        esito = dispatcher(casa, f"echo \"nota {VIRGOLETTA} → fine\" | sendmail a@esempio.org")
        assert esito == "ask", f"U06 invio con «→» e «”» dal dispatcher: {esito!r}"


TESTS = {"U01": test_u01, "U02": test_u02, "U03": test_u03, "U04": test_u04, "U05": test_u05, "U06": test_u06}


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
