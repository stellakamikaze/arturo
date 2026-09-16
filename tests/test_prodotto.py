#!/usr/bin/env python3
"""P01-P07: la porta d'ingresso di Arturo come prodotto (16/9/2026).

Il README deve dire cosa non e' neutro e cosa Arturo promette a chi lo usa, e le
promesse devono corrispondere al codice. P05-P07 coprono il canale di rilascio:
/aggiorna indietro, l'avviso AVANTI solo dove si puo' pushare, la manutenzione
scritta. Sulla base ee10fc6 ogni controllo deve fallire per conto suo.
"""
from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import tempfile
import time
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


def test_p05(repo: Path) -> None:
    testo = read(repo / "commands" / "aggiorna.md")
    for parola in ("--autostash", "ultimo-aggiornamento", "reset --keep"):
        assert parola in testo, f"P05 /aggiorna non contiene {parola}"
    for riga in testo.splitlines():
        if "reset --hard" in riga:
            assert re.search(r"\bmai\b|nessun|non ", riga, re.I), (
                "P05 reset --hard compare fuori da una frase che lo vieta"
            )


def _esegui(cmd: list[str], **kw) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True, timeout=120, **kw)


def test_p06(repo: Path) -> None:
    tmp = Path(tempfile.mkdtemp(prefix="arturo-p06-"))
    try:
        home = tmp / "home"
        claude = home / ".claude"
        claude.mkdir(parents=True)
        # stub osascript: niente finestra Terminal ne' prompt di automazione nel test
        bin_dir = tmp / "bin"
        bin_dir.mkdir()
        stub = bin_dir / "osascript"
        stub.write_text("#!/bin/sh\nexit 1\n")
        stub.chmod(0o755)
        env = dict(os.environ)
        env["HOME"] = str(home)
        env["PATH"] = f"{bin_dir}{os.pathsep}{env.get('PATH', '')}"
        git = ["git", "-C", str(claude)]
        _esegui(git + ["init", "--quiet", "-b", "main"])
        _esegui(git + ["config", "user.email", "test@example.com"])
        _esegui(git + ["config", "user.name", "Test"])
        (claude / "file.txt").write_text("uno\n")
        _esegui(git + ["add", "file.txt"])
        _esegui(git + ["commit", "--quiet", "-m", "primo"])
        _esegui(git + ["remote", "add", "origin", "https://github.com/stellakamikaze/arturo.git"])
        _esegui(git + ["update-ref", "refs/remotes/origin/main", "HEAD"])
        # commit locale non pushato: HEAD e' avanti di uno su origin/main
        (claude / "file.txt").write_text("due\n")
        _esegui(git + ["add", "file.txt"])
        _esegui(git + ["commit", "--quiet", "-m", "secondo"])
        # marcatore del fetch fresco: l'hook salta il fetch di rete
        session_env = claude / "session-env"
        session_env.mkdir(exist_ok=True)
        (session_env / "ultimo-fetch").write_text(str(int(time.time())))
        hook = str(repo / "hooks" / "session-start.sh")
        out = _esegui(["bash", hook], cwd=str(tmp), env=env)
        assert out.returncode == 0, (
            f"P06 session-start non e' partito: rc={out.returncode} {out.stderr.strip()!r}"
        )
        assert "AVANTI" not in out.stdout, (
            "P06 l'avviso AVANTI compare con origin = repo originale di Arturo"
        )
        _esegui(git + ["remote", "set-url", "origin", "https://github.com/altro/mio-claude.git"])
        out = _esegui(["bash", hook], cwd=str(tmp), env=env)
        assert "AVANTI" in out.stdout, (
            "P06 l'avviso AVANTI manca con origin = repo personale dell'utente"
        )
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_p07(repo: Path) -> None:
    testo = read(repo / "docs" / "manutenzione.md")
    for parola in ("verifica-allineamento.sh", "merge --ff-only", "NOVITA.md"):
        assert parola in testo, f"P07 docs/manutenzione.md non contiene {parola}"


TESTS = {
    "P01": test_p01,
    "P02": test_p02,
    "P03": test_p03,
    "P04": test_p04,
    "P05": test_p05,
    "P06": test_p06,
    "P07": test_p07,
}


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
            except (AssertionError, FileNotFoundError, subprocess.SubprocessError):
                # SubprocessError: solo P06 esegue comandi; un hook che non parte
                # sulla base e' comunque un P06 che fallisce.
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
