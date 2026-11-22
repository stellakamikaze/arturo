#!/usr/bin/env python3
"""PB: il pre-filtro del dispatcher di Bash in Python, con gli stessi giudizi e in tempo lineare (#6327).

Fino al 22/11/2026 il pre-filtro erano regex di bash: 13 µs per carattere, e oltre 100.000 caratteri il
dispatcher chiedeva conferma senza leggere il comando. Ora i pattern stanno in hooks/prefiltro_bash.py, che li
traduce da POSIX ERE a regex Python, e il limite è 1.000.000.

  PB01  la traduzione: classi POSIX, `$` a fine testo, parentesi quadre con `]` e `\\` dentro, nessun avviso
        di Python sulle classi;
  PB02  la forma lineare (corse temperate e forme a mano) trova esattamente ciò che trova la traduzione esatta:
        testi casuali dai letterali di ogni alternativa, più i controesempi trovati il 22/11/2026;
  PB03  i testi costruiti per far lavorare le regex (parole ripetute, `git commit` a ogni riga) stanno sotto i
        3 secondi su 100.000 caratteri: in bash, e nella traduzione esatta, alcuni passavano i 50;
  PB04  il dispatcher legge un comando di 300.000 caratteri e lo giudica (rm -rf in fondo chiede conferma per
        block-dangerous); oltre 1.000.000 chiede conferma senza leggerlo;
  PB05  le parole necessarie di ogni pattern (Pattern.serve): se la regex trova qualcosa, una parola c'è;
  PB06  hooks/prefiltro_regex.py è quello che genera il sorgente di adesso;
  PB07  un link verso un file che non esiste fa partire block-dangerous, come `readlink -f` su macOS;
  PB08  un pre-filtro rotto fa chiedere conferma, mai passare muto.

Il confronto completo con il dispatcher di prima, sui 52.148 comandi Bash veri dei 30 giorni prima, ha dato una
sola differenza (PB07, corretta): sta in una sonda privata, perché i comandi sono della persona. Qui ci sono le
regole, non i comandi.
Con --baseline-ref ogni controllo deve fallire col suo codice: su 5fdb286 il modulo non c'è e il limite è 100.000.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import random
import re
import shutil
import subprocess
import sys
import tempfile
import time
import warnings
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from salti_windows import dichiara  # noqa: E402

WINDOWS = os.name == "nt"
BASH = shutil.which("bash")
SEP = [" ", " ", "|", ";", "&", "\n", "-", ".", "/", "=", "'", '"', "x", "(", ")", "\t", "#", "$", "{", "`", "a", "D", "r"]
# Controesempi del 22/11/2026: ognuno faceva sbagliare una prima versione della forma lineare.
CONTROESEMPI = ["wget x wget\n", "wget wget\twget", "curl -o x curl a\n--output", "git -c x git y push -c",
                "find -name a find -exec x -name b", "git x clean yclean -f", "email-xemail.amazonaws",
                "git x commit ycommit --am", "docker compose x down y down -v", "X=a;Y=b git commit",
                "env\nenv\ngit commit", "gws x gmail y gmail +send"]


def carica(repo: Path, codice: str):
    percorso = repo / "hooks" / "prefiltro_bash.py"
    assert percorso.is_file(), f"{codice} manca hooks/prefiltro_bash.py"
    spec = importlib.util.spec_from_file_location("pb_prefiltro_bash", percorso)
    modulo = importlib.util.module_from_spec(spec)
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        spec.loader.exec_module(modulo)
    return modulo


def pattern(pb):
    return [(n, getattr(pb, n)) for n in sorted(dir(pb)) if isinstance(getattr(pb, n), pb.Pattern)]


def letterali(alt: str):
    fuori = re.sub(r"\[:[a-z]+:\]", " ", re.sub(r"\[(\^)?\]?[^]]*\]", " ", alt))
    return [x.replace("\\", "") for x in re.findall(r"(?:\\.|[A-Za-z0-9_/@:+-])+", fuori) if x.replace("\\", "")] or ["x"]


def casuali(alt: str, quanti: int, seme: int):
    rnd = random.Random(seme)
    lett = letterali(alt)
    for _ in range(quanti):
        yield "".join(rnd.choice(lett) if rnd.random() < 0.55 else rnd.choice(SEP) for _ in range(rnd.randint(1, 22)))


def test_pb01(repo: Path) -> None:
    pb = carica(repo, "PB01")
    casi = [("a[[:space:]]b", "a\tb", True), ("a[[:space:]]b", "a b", False), ("x$", "x\n", False),
            ("x$", "x", True), ("[]*?[]", "]", True), ("[]*?[]", "[", True), ("[/\\\\]", "\\", True),
            ("[^[:alnum:]_.-]git", "ègit", True), ("[^[:alnum:]_.-]git", "agit", False),
            ("a.b", "a\nb", True), ("[;&[:cntrl:]]", "\x7f", True), ("\\.claude", "xclaude", False)]
    for ere, testo, atteso in casi:
        trovato = bool(re.search(pb._ere(ere), testo, re.S | re.A))
        assert trovato == atteso, f"PB01 {ere!r} su {testo!r}: {trovato}, atteso {atteso}"
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        for _, p in pattern(pb):
            p._compila(0)
            p._compila(re.I, esatta=True)


def test_pb02(repo: Path) -> None:
    pb = carica(repo, "PB02")
    lineari = [(n, p) for n, p in pattern(pb) if p.lineare]
    assert len(lineari) >= 12, f"PB02 pattern lineari: {len(lineari)}"
    diversi = []
    for nome, p in lineari:
        for flag in (0, re.I):
            for alt, e, t in zip(pb._alternative(p.ere), p._compila(flag, esatta=True), p._compila(flag)):
                for s in list(casuali(alt, 1500, len(alt))) + CONTROESEMPI:
                    if bool(e.search(s)) != bool(t.search(s)):
                        diversi.append((nome, alt[:50], s))
    assert not diversi, f"PB02 la forma lineare cambia risultato su {len(diversi)} testi: {diversi[:5]}"


def _costruiti():
    n = 100_000
    riga = "x = 'form rm term' * 3  # find -name curl gi" + "t commit -m smtplib curl -d @k gh repo delete\n"
    return {"rm": "perform " * (n // 8), "find": "find . " + "-name x " * (n // 8),
            "gws": "gws " + "gmail x " * (n // 8), "curl": "curl x " * (n // 7), "env": "env\n" * (n // 4),
            "commit": "python3 - <<'EOF'\n" + riga * (n // len(riga)) + "EOF",
            "clean": ("gi" + "t clean x ") * (n // 12), "branch": ("gi" + "t branch x ") * (n // 13),
            "docker": "docker compose " + "down x " * (n // 7)}


def test_pb03(repo: Path) -> None:
    pb = carica(repo, "PB03")
    lenti = []
    for nome, testo in _costruiti().items():
        dati = {"tool_name": "Bash", "session_id": "pb", "cwd": "/tmp", "tool_input": {"command": testo}}
        inizio = time.perf_counter()
        pb.analizza(testo, testo, json.dumps(dati), dati, senza_maiuscole=True, zsh=True)
        durata = time.perf_counter() - inizio
        if durata > 3:
            lenti.append(f"{nome} {durata:.1f} s")
    assert not lenti, f"PB03 pre-filtro lento su 100.000 caratteri: {lenti}"


def _casa(repo: Path, radice: Path) -> Path:
    casa = radice / "home"
    shutil.copytree(repo, casa / ".claude", ignore=shutil.ignore_patterns(".git", "__pycache__", "worktrees"))
    (casa / "Documents" / "progetto").mkdir(parents=True)
    return casa


def _dispatcher(casa: Path, comando: str, ambiente: dict):
    evento = json.dumps({"tool_name": "Bash", "tool_input": {"command": comando}, "cwd": str(casa), "session_id": "pb"})
    p = subprocess.run([BASH, str(casa / ".claude" / "hooks" / "bash-dispatcher.sh")], input=evento,
                       capture_output=True, text=True, encoding="utf-8", env=ambiente, timeout=60)
    if p.returncode == 2:
        return "block", p.stderr
    if not p.stdout.strip():
        return "silent", ""
    uscita = json.loads(p.stdout)["hookSpecificOutput"]
    return uscita["permissionDecision"], uscita.get("permissionDecisionReason", "")


def _ambiente(casa: Path) -> dict:
    return {"HOME": str(casa), "USERPROFILE": str(casa), "PATH": os.environ.get("PATH", ""), "SHELL": "/bin/bash"}


def test_pb04(repo: Path) -> None:
    if WINDOWS:
        dichiara("PB04", "il banco copia la casa intera e lancia il dispatcher con bash: lo copre il gate su macOS")
        return
    with tempfile.TemporaryDirectory(prefix="pb04-") as d:
        casa = _casa(repo, Path(d))
        corpo = "".join(f"valore_{i} = 'form term {i}'\n" for i in range(15_000))
        lungo = f"python3 - <<'EOF'\n{corpo}EOF\nrm -rf {casa}/Documents/progetto"
        assert len(lungo) > 300_000, f"PB04 comando corto: {len(lungo)}"
        decisione, motivo = _dispatcher(casa, lungo, _ambiente(casa))
        assert decisione == "ask" and "troppo lungo" not in motivo, \
            f"PB04 un comando di {len(lungo)} caratteri non arriva a block-dangerous: {decisione} {motivo[:120]}"
        enorme = "echo " + "a" * 1_000_001
        decisione, motivo = _dispatcher(casa, enorme, _ambiente(casa))
        assert decisione == "ask" and "1.000.000" in motivo, f"PB04 oltre 1.000.000: {decisione} {motivo[:120]}"


def test_pb05(repo: Path) -> None:
    pb = carica(repo, "PB05")
    con = [(n, p) for n, p in pattern(pb) if p.serve]
    assert len(con) >= 15, f"PB05 pattern con parole necessarie: {len(con)}"
    mancano = []
    for nome, p in con:
        for alt, r in zip(pb._alternative(p.ere), p._compila(re.I, esatta=True)):
            for s in list(casuali(alt, 1500, 7 + len(alt))) + CONTROESEMPI:
                if r.search(s) and not any(w in s.lower() for w in p.serve):
                    mancano.append((nome, s))
    assert not mancano, f"PB05 la regex trova testi senza le parole necessarie: {mancano[:5]}"


def test_pb06(repo: Path) -> None:
    pb = carica(repo, "PB06")
    generato = repo / "hooks" / "prefiltro_regex.py"
    assert generato.is_file() and generato.read_text(encoding="utf-8") == pb.genera(), \
        "PB06 hooks/prefiltro_regex.py non è aggiornato: python3 hooks/prefiltro_bash.py genera"


def test_pb07(repo: Path) -> None:
    pb = carica(repo, "PB07")
    if WINDOWS:
        dichiara("PB07", "i link simbolici su Windows chiedono la modalità sviluppatore")
        return
    with tempfile.TemporaryDirectory(prefix="pb07-") as d:
        link = Path(d) / "cartella" / "lnk"
        link.parent.mkdir()
        os.symlink(Path(d) / "non-esiste", link)
        comando = f"cat {link}"
        dati = {"tool_name": "Bash", "session_id": "pb", "cwd": d, "tool_input": {"command": comando}}
        viste, _ = pb.analizza(comando, comando, json.dumps(dati), dati)
        assert "danger" in viste, f"PB07 un link verso un file che manca non fa partire block-dangerous: {viste}"


def test_pb08(repo: Path) -> None:
    if WINDOWS:
        dichiara("PB08", "il banco copia la casa intera e lancia il dispatcher con bash: lo copre il gate su macOS")
        return
    with tempfile.TemporaryDirectory(prefix="pb08-") as d:
        casa = _casa(repo, Path(d))
        (casa / ".claude" / "hooks" / "prefiltro_bash.py").write_text("def analizza(*a, **k):\n    raise RuntimeError\n",
                                                                      encoding="utf-8")
        decisione, motivo = _dispatcher(casa, "ls -la", _ambiente(casa))
        assert decisione == "ask", f"PB08 con il pre-filtro rotto ls -la non chiede conferma: {decisione}"


TESTS = {"PB01": test_pb01, "PB02": test_pb02, "PB03": test_pb03, "PB04": test_pb04, "PB05": test_pb05,
         "PB06": test_pb06, "PB07": test_pb07, "PB08": test_pb08}


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
