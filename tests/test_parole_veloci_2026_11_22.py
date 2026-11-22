#!/usr/bin/env python3
"""SP: le guardie di Bash più veloci, con gli stessi giudizi (22/11/2026, #6327 e #5347).

Il 21/11/2026 il dispatcher costava 377 ms in mediana a ogni comando Bash, e block-dangerous impiegava 13 secondi
su un `python3 -c` di 94.000 caratteri. Tre cause, ognuna con un controllo:

  SP01  forma_comando.parole dà le stesse parole di shlex (o lo stesso ValueError) su stringhe casuali, nelle tre
        forme che usano le guardie: segmenti_parole, lexer e shlex.split. shlex allungava la parola un carattere
        alla volta, e il costo cresceva col quadrato.
  SP02  block-dangerous giudica un `python3 -c` di 94.000 caratteri in meno di 8 secondi (prima 13), e un rm in
        coda allo stesso comando chiede ancora conferma.
  SP03  segmenti_parole e le altre letture del comando si ricordano per tutto il processo, e ogni chiamante
        riceve una lista sua: modificarla non sporca la chiamata dopo.
  SP04  evento_bash.py leggi dà comando, comando delle guardie, copia dell'evento e tool_use_id, con le lunghezze
        in byte: a capo in coda, lettere accentate, byte nullo, CRLF su Windows, `.exe`, heredoc inerte, JSON
        rotto.
  SP05  evento_bash.py esegui lancia uno script come python3: argomenti, codice d'uscita, __name__, cartella dei
        moduli. Il bytecode è a hash controllato: una modifica con la stessa lunghezza e la stessa data si vede.
  SP06  il dispatcher fa partire un solo python3 su un comando semplice (prima due, più jq), e le guardie passano
        da evento_bash.py esegui. Senza evento_bash.py ogni comando chiede conferma.

Con --baseline-ref ogni controllo deve fallire col suo codice: su 663bcba parole ed evento_bash.py non ci sono,
segmenti_parole non si ricorda e block-dangerous va oltre gli 8 secondi.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import random
import shlex
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from salti_windows import dichiara  # noqa: E402

WINDOWS = os.name == "nt"
BASH = shutil.which("bash")


def carica(repo: Path, nome: str):
    percorso = repo / "hooks" / nome
    assert percorso.is_file(), f"manca {percorso}"
    spec = importlib.util.spec_from_file_location("sp_" + nome.replace(".", "_").replace("-", "_"), percorso)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


def _shlex(testo: str, punteggiatura: str, spazi: str):
    lx = shlex.shlex(testo, posix=True, punctuation_chars=punteggiatura) if punteggiatura else \
        shlex.shlex(testo, posix=True)
    lx.commenters = ""
    lx.whitespace = spazi
    lx.whitespace_split = True
    try:
        return list(lx)
    except ValueError as e:
        return ("ValueError", str(e))


def test_sp01(repo: Path) -> None:
    fc = carica(repo, "forma_comando.py")
    assert hasattr(fc, "parole"), "SP01 forma_comando non ha parole()"
    alfabeto = list("ab '\"\\()\t\n\r;&|#$~-./*?=àß") + ["  ", "\\\n", "''", '""', "\\\"", "\\\\"]
    forme = (("()", " \t\r\n"), (";&|()\n", " \t\r"), ("", " \t\r\n"))
    caso = random.Random(5347)
    diversi = []
    for _ in range(30_000):
        testo = "".join(caso.choice(alfabeto) for _ in range(caso.randint(0, 24)))
        for punteggiatura, spazi in forme:
            try:
                nuovo = fc.parole(testo, punteggiatura, spazi)
            except ValueError as e:
                nuovo = ("ValueError", str(e))
            if nuovo != _shlex(testo, punteggiatura, spazi):
                diversi.append(repr((testo, punteggiatura)))
    assert not diversi, f"SP01 parole diverse da shlex su {len(diversi)} casi, per esempio {diversi[:3]}"
    lungo = "python3 -c \"" + "print('a b');" * 20_000 + "\""
    assert fc.parole(lungo, "()") == _shlex(lungo, "()", " \t\r\n"), "SP01 parole diverse su un comando lungo"


def _evento(comando: str, cwd: str = "/tmp", **altro) -> str:
    return json.dumps(dict({"tool_name": "Bash", "tool_input": {"command": comando}, "cwd": cwd,
                            "session_id": "sp"}, **altro))


def test_sp02(repo: Path) -> None:
    guardia = repo / "hooks" / "block-dangerous.py"
    lungo = "python3 -c \"" + "print('a b c d');" * 5_247 + "\""
    esiti = []
    for comando in (lungo, lungo + "\nrm -rf ~/Documents/progetto"):
        inizio = time.perf_counter()
        try:
            p = subprocess.run([sys.executable, str(guardia)], input=_evento(comando), capture_output=True,
                               text=True, encoding="utf-8", timeout=8)
        except subprocess.TimeoutExpired:
            raise AssertionError(f"SP02 block-dangerous oltre 8 secondi su {len(comando)} caratteri")
        decisione = json.loads(p.stdout)["hookSpecificOutput"]["permissionDecision"] if p.stdout.strip() else \
            ("block" if p.returncode == 2 else "silent")
        esiti.append((decisione, round(time.perf_counter() - inizio, 1)))
    assert [e[0] for e in esiti] == ["silent", "ask"], f"SP02 giudizi cambiati sul comando lungo: {esiti}"


def test_sp03(repo: Path) -> None:
    fc = carica(repo, "forma_comando.py")
    assert hasattr(fc.segmenti_parole, "__wrapped__"), "SP03 segmenti_parole non si ricorda"
    comando = "cd ~/x && rm -rf build; (echo a | tee f)"
    prima = fc.segmenti_parole(comando)
    atteso = [list(s) for s in prima]
    prima[0].append("sporco")
    prima.append(["sporco"])
    assert fc.segmenti_parole(comando) == atteso, "SP03 la lista ricordata si sporca col chiamante"
    sep = fc._separatori(comando)
    sep.append((0, 0, "sporco"))
    assert fc._separatori(comando) != sep, "SP03 _separatori ricordati si sporcano"


def _leggi(repo: Path, evento: bytes, *argomenti: str):
    p = subprocess.run([sys.executable, str(repo / "hooks" / "evento_bash.py"), "leggi", *argomenti],
                       input=evento, capture_output=True, timeout=30)
    assert p.returncode == 0, f"SP04 leggi esce {p.returncode}: {p.stderr[-300:]!r}"
    testa, _, resto = p.stdout.partition(b"\n")
    lunghezze = [int(x) for x in testa.split()]
    assert len(lunghezze) == 4 and sum(lunghezze) == len(resto), f"SP04 lunghezze che non tornano: {testa!r}"
    campi, k = [], 0
    for n in lunghezze:
        campi.append(resto[k:k + n].decode("utf-8"))
        k += n
    return campi


def test_sp04(repo: Path) -> None:
    assert (repo / "hooks" / "evento_bash.py").is_file(), "SP04 manca hooks/evento_bash.py"
    comando = "echo 'caffè €'\n\n"
    c, g, copia, uso = _leggi(repo, _evento(comando, tool_use_id="toolu_1").encode("utf-8"))
    assert c == g == "echo 'caffè €'", f"SP04 a capo in coda o accenti: {c!r} {g!r}"
    assert json.loads(copia)["tool_input"]["command"] == g and json.loads(copia)["cwd"] == "/tmp", \
        f"SP04 copia dell'evento: {copia!r}"
    assert uso == "toolu_1", f"SP04 tool_use_id: {uso!r}"
    c, g, _, _ = _leggi(repo, _evento("rm.exe -rf x\ngit.EXE push").encode("utf-8"))
    assert c == "rm.exe -rf x\ngit.EXE push" and g == "rm -rf x\ngit push", f"SP04 suffisso .exe: {g!r}"
    c, g, _, _ = _leggi(repo, _evento("a\0b\r\nc").encode("utf-8"), "crlf")
    assert c == g == "ab\nc", f"SP04 byte nullo o CRLF: {c!r}"
    c, _, _, _ = _leggi(repo, _evento("a\r\nc").encode("utf-8"))
    assert c == "a\r\nc", f"SP04 il CR fuori da Windows deve restare: {c!r}"
    c, g, copia, _ = _leggi(repo, _evento("cat <<'EOF' > nota.txt\nrm -rf ~\nEOF").encode("utf-8"))
    assert "rm -rf" in c and "rm -rf" not in g and "rm -rf" not in copia, f"SP04 heredoc inerte: {g!r}"
    c, g, _, _ = _leggi(repo, _evento("cat <<EOF | bash\nrm -rf ~\nEOF").encode("utf-8"))
    assert "rm -rf" in g, f"SP04 un heredoc eseguito deve restare: {g!r}"
    assert _leggi(repo, b'{"tool_input": {"command": "ls"') == ["", "", "", ""], "SP04 JSON rotto"
    c, _, _, _ = _leggi(repo, b'{"tool_input": {"command": "rm \xff -rf x"}}')
    assert c == "rm \ufffd -rf x", f"SP04 byte non UTF-8: {c!r}"


def test_sp05(repo: Path) -> None:
    lanciatore = repo / "hooks" / "evento_bash.py"
    assert lanciatore.is_file(), "SP05 manca hooks/evento_bash.py"
    with tempfile.TemporaryDirectory(prefix="sp05-") as d:
        cartella = Path(d)
        (cartella / "vicino.py").write_text("VALORE = 'vicino'\n", encoding="utf-8")
        script = cartella / "guardia.py"
        corpo = ("import sys, vicino\nprint(__name__, vicino.VALORE, sys.argv[1:], sys.stdin.read().strip(), "
                 "'{}')\nsys.exit({})\n")
        script.write_text(corpo.format("A", 2), encoding="utf-8")
        ambiente = {k: v for k, v in os.environ.items() if k != "PYTHONDONTWRITEBYTECODE"}

        def lancia():
            return subprocess.run([sys.executable, str(lanciatore), "esegui", str(script), "uno", "due"],
                                  input="dati", capture_output=True, text=True, timeout=30, env=ambiente)
        p = lancia()
        assert p.returncode == 2 and p.stdout.split() == ["__main__", "vicino", "['uno',", "'due']", "dati", "A"], \
            f"SP05 esegui diverso da python3: rc={p.returncode} {p.stdout!r} {p.stderr[-300:]!r}"
        pyc = importlib.util.cache_from_source(str(script))
        assert os.path.isfile(pyc), "SP05 nessun bytecode in __pycache__"
        with open(pyc, "rb") as f:
            testa = f.read(8)
        assert int.from_bytes(testa[4:8], "little") == 3, "SP05 il bytecode non è a hash controllato"
        stato = os.stat(script)
        script.write_text(corpo.format("B", 3), encoding="utf-8")
        os.utime(script, ns=(stato.st_atime_ns, stato.st_mtime_ns))
        assert os.stat(script).st_size == stato.st_size
        p = lancia()
        assert p.returncode == 3 and p.stdout.split()[-1] == "B", \
            f"SP05 bytecode vecchio dopo una modifica della stessa lunghezza: rc={p.returncode} {p.stdout!r}"


def _casa(repo: Path, radice: Path) -> Path:
    casa = radice / "home"
    shutil.copytree(repo, casa / ".claude", ignore=shutil.ignore_patterns(".git", "__pycache__", "worktrees"))
    (casa / "Documents" / "progetto").mkdir(parents=True)
    return casa


def _dispatcher(casa: Path, comando: str, ambiente: dict) -> str:
    p = subprocess.run([BASH, str(casa / ".claude" / "hooks" / "bash-dispatcher.sh")],
                       input=_evento(comando, cwd=str(casa)), capture_output=True, text=True, encoding="utf-8",
                       env=ambiente, timeout=60)
    if p.returncode == 2:
        return "block"
    return json.loads(p.stdout)["hookSpecificOutput"]["permissionDecision"] if p.stdout.strip() else "silent"


def test_sp06(repo: Path) -> None:
    if WINDOWS:
        dichiara("SP06", "il finto python3 sul PATH è uno script sh, che Windows non lancia come programma")
        return
    with tempfile.TemporaryDirectory(prefix="sp06-") as d:
        radice = Path(d)
        casa = _casa(repo, radice)
        finti = radice / "bin"
        finti.mkdir()
        registro = radice / "python3.log"
        (finti / "python3").write_text(f'#!/bin/sh\nprintf "%s\\n" "$*" >> "{registro}"\nexec "{sys.executable}" "$@"\n',
                                       encoding="utf-8")
        (finti / "python3").chmod(0o755)
        ambiente = {"HOME": str(casa), "USERPROFILE": str(casa), "PATH": f"{finti}{os.pathsep}{os.environ.get('PATH', '')}",
                    "PYTHONDONTWRITEBYTECODE": "1"}
        assert _dispatcher(casa, "ls -la", ambiente) == "silent", "SP06 ls -la non è muto"
        avvii = registro.read_text(encoding="utf-8").splitlines() if registro.exists() else []
        assert len(avvii) == 1, f"SP06 su ls -la partono {len(avvii)} python3: {avvii}"
        registro.unlink()
        assert _dispatcher(casa, f"rm -rf {casa}/Documents/progetto", ambiente) == "ask", "SP06 rm -rf non chiede"
        avvii = registro.read_text(encoding="utf-8").splitlines()
        assert any("evento_bash.py esegui" in a and "block-dangerous.py" in a for a in avvii), \
            f"SP06 block-dangerous non passa da evento_bash.py esegui: {avvii}"
        (casa / ".claude" / "hooks" / "evento_bash.py").unlink()
        assert _dispatcher(casa, "ls -la", ambiente) == "ask", "SP06 senza evento_bash.py un comando passa muto"


TESTS = {"SP01": test_sp01, "SP02": test_sp02, "SP03": test_sp03, "SP04": test_sp04, "SP05": test_sp05,
         "SP06": test_sp06}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[1])
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
