#!/usr/bin/env python3
"""Finding LOW della revisione del 13/9/2026: L01, L03, L04.

L02 non si applica piu' (/ui potato). Sulla base ee10fc6 ogni finding deve
fallire per conto suo.
"""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

BASH = shutil.which("bash")


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def riga(testo: str, frammento: str) -> str:
    return next((row for row in testo.splitlines() if frammento in row), "")


def test_l01(repo: Path) -> None:
    readme = read(repo / "README.md")
    gh = riga(readme, "gh → gh-destructive-guard.py")
    assert "blocco" in gh, f"L01 il diagramma dice solo ask per una guardia che blocca: {gh.strip()!r}"
    commit = riga(readme, "commit-secret-gate.py     │")
    assert commit.rstrip().endswith("ask"), f"L01 il diagramma non dice l'esito del gate segreti: {commit.strip()!r}"
    statusline = riga(readme, "- `statusline.js`")
    if "branch" not in read(repo / "hooks" / "statusline.js"):
        assert "branch" not in statusline, "L01 il README promette il branch nella statusline, che non lo legge"


NOVITA_FIXTURE = """# Novita

## 2026-09-13 — Terza

testo

## 2026-09-02 — Seconda

testo

## 2026-08-17 — Prima

testo
"""


def avviso_novita(repo: Path, viste: str | None, vecchia: str | None) -> str:
    with tempfile.TemporaryDirectory(prefix="arturo-l03-") as tmp:
        home = Path(tmp) / "home"
        config = home / ".claude"
        (config / "hooks").mkdir(parents=True)
        (config / "session-env").mkdir()
        shutil.copy(repo / "hooks" / "session-start.sh", config / "hooks" / "session-start.sh")
        (config / "NOVITA.md").write_text(NOVITA_FIXTURE, encoding="utf-8")
        if viste is not None:
            (config / "session-env" / "novita-viste").write_text(viste, encoding="utf-8")
        if vecchia is not None:
            (config / "session-env" / "novita-vista").write_text(vecchia, encoding="utf-8")
        env = {"HOME": str(home), "USERPROFILE": str(home), "PATH": os.environ.get("PATH", "")}
        result = subprocess.run([BASH, str(config / "hooks" / "session-start.sh")], cwd=tmp, text=True,
                                capture_output=True, env=env, timeout=30, check=False)
        return next((row for row in result.stdout.splitlines() if row.startswith("NOVITA")), "")


def test_l03(repo: Path) -> None:
    got = avviso_novita(repo, "2026-09-13\n", None)
    assert "2 aggiornamenti" in got, f"L03 vista solo l'ultima: le due precedenti restano da leggere, avviso={got!r}"
    got = avviso_novita(repo, "2026-09-13\n2026-09-02\n2026-08-17\n", None)
    assert got == "", f"L03 controllo: tutte viste, nessun avviso atteso, avviso={got!r}"
    got = avviso_novita(repo, None, "2026-09-02")
    assert "1 aggiornamenti" in got, f"L03 il vecchio segnalibro deve valere come viste fino a quella data, avviso={got!r}"
    novita = read(repo / "commands" / "novita.md")
    assert '>> "$HOME/.claude/session-env/novita-viste"' in novita, "L03 /novita non segna le entry una per una"
    assert "novità AAAA-MM-GG" in novita, "L03 /novita non passa allo sparring la data dell'entry"
    assert "novità AAAA-MM-GG" in read(repo / "commands" / "sparring.md"), "L03 /sparring non sa partire da un'entry precisa"


def test_l04(repo: Path) -> None:
    license_file = repo / "LICENSE"
    assert license_file.is_file(), "L04 manca il file LICENSE di Arturo"
    text = read(license_file)
    assert text.startswith("MIT License") and "Federico Nejrotti" in text, "L04 LICENSE non e' la MIT intestata all'autore"
    readme = read(repo / "README.md")
    sezione = readme[readme.find("## Licenza"):]
    assert "MIT" in sezione and "LICENSE" in sezione, "L04 il README non rimanda alla licenza"


TESTS = {"L01": test_l01, "L03": test_l03, "L04": test_l04}


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
            except AssertionError:
                failed.append(name)
        assert failed == list(TESTS), f"baseline non discriminante: falliscono solo {failed} su {list(TESTS)}"
        print(f"BASELINE_DISCRIMINANTE={','.join(failed)}")
        return 0
    for test in TESTS.values():
        test(repo)
    print(f"PASS {','.join(TESTS)} finding={len(TESTS)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
