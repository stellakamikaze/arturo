#!/usr/bin/env python3
"""BA01-BA02: la base di Arturo si sceglie in un posto solo (21/11/2026, #6216).

Dal 20/11 (#5383) tests/banchi-avvio.sh sceglieva la base come hooks/deriva.py, ma con una copia sua della
scelta: upstream/main se c'è un remote upstream, altrimenti origin/main. Nessun banco controllava che le due
copie restassero uguali. Adesso il .sh chiede la base a `deriva.py --base`.

BA01 deriva.py --base stampa la merge-base con origin/main nella forma clone, con upstream/main nel fork, e
     niente con un upstream dichiarato e mai scaricato (lì origin è il repository della persona).
BA02 banchi-avvio.sh prende la base da deriva.py --base e non riscrive la scelta: nessun merge-base e nessun
     remote.upstream nelle righe di codice.

Sulla base cecf8fc ogni controllo deve fallire con un AssertionError che comincia con il suo codice.
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def _git(cartella: Path, *argomenti: str) -> str:
    r = subprocess.run(["git", "-C", str(cartella), "-c", "user.name=t", "-c", "user.email=t@t",
                        "-c", "commit.gpgsign=false", *argomenti],
                       capture_output=True, text=True, check=True)
    return r.stdout.strip()


def _base(repo: Path, config: Path) -> str:
    r = subprocess.run([sys.executable, "-B", str(repo / "hooks" / "deriva.py"), "--base", str(config)],
                       capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60)
    return r.stdout.strip()


def test_ba01(repo: Path) -> None:
    with tempfile.TemporaryDirectory() as d:
        radice = Path(d)
        arturo = radice / "arturo"
        arturo.mkdir()
        _git(arturo, "init", "-q", "-b", "main")
        (arturo / "README.md").write_text("arturo\n", encoding="utf-8")
        _git(arturo, "add", "-A")
        _git(arturo, "commit", "-q", "-m", "arturo")
        base_arturo = _git(arturo, "rev-parse", "HEAD")
        # Forma clone: origin è Arturo, la persona aggiunge un commit suo.
        clone = radice / "clone"
        subprocess.run(["git", "clone", "-q", str(arturo), str(clone)], check=True, capture_output=True)
        (clone / "mio.md").write_text("mio\n", encoding="utf-8")
        _git(clone, "add", "-A")
        _git(clone, "commit", "-q", "-m", "mio")
        trovata = _base(repo, clone)
        assert trovata == base_arturo, f"BA01 forma clone: attesa {base_arturo[:12]}, uscita {trovata!r}"
        # Fork: origin è il repository della persona, già avanti; Arturo è upstream.
        fork = radice / "fork.git"
        subprocess.run(["git", "clone", "-q", "--bare", str(clone), str(fork)], check=True, capture_output=True)
        config = radice / "config"
        subprocess.run(["git", "clone", "-q", str(fork), str(config)], check=True, capture_output=True)
        _git(config, "remote", "add", "upstream", str(arturo))
        # Upstream dichiarato e mai scaricato: niente base, non la merge-base con origin/main.
        trovata = _base(repo, config)
        assert trovata == "", f"BA01 upstream mai scaricato: attesa nessuna base, uscita {trovata!r}"
        _git(config, "fetch", "-q", "upstream")
        trovata = _base(repo, config)
        assert trovata == base_arturo, f"BA01 fork con upstream: attesa {base_arturo[:12]}, uscita {trovata!r}"


def test_ba02(repo: Path) -> None:
    testo = (repo / "tests" / "banchi-avvio.sh").read_text(encoding="utf-8")
    codice = [r for r in testo.splitlines() if r.strip() and not r.lstrip().startswith("#")]
    chiede = [r for r in codice if "hooks/deriva.py" in r and "--base" in r and "BASE_ARTURO=" in r]
    assert chiede, "BA02 banchi-avvio.sh non prende BASE_ARTURO da hooks/deriva.py --base"
    copie = [r.strip() for r in codice if "merge-base" in r or "remote.upstream" in r]
    assert not copie, f"BA02 banchi-avvio.sh riscrive la scelta della base: {copie}"


TESTS = {"BA01": test_ba01, "BA02": test_ba02}


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
