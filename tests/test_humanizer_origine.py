#!/usr/bin/env python3
"""HO01-HO05: bin/humanizer-origine.py tiene humanizer agganciato al suo repository d'origine (4/11/2026).

Lavora su un repository finto che fa da origine (blader/humanizer) e su una radice finta di Arturo con
skills/humanizer/ORIGINE e references/originale-en.md.

HO01 origine e ORIGINE pari: controlla tace.
HO02 un commit nuovo sull'origine: controlla stampa la riga HUMANIZER con versione e commit nuovi.
HO03 porta: riscrive originale-en.md e ORIGINE (con lo sha intero), e scrive la differenza da riportare in italiano.
HO04 origine che non risponde: controlla esce 0 e non stampa la riga.
HO05 un uso sbagliato esce 2, anche --commit con uno sha corto.

--avvelena fa girare una copia dello script dove controlla non confronta i commit: HO01 deve diventare
rosso, perché la riga compare anche con origine e Arturo pari. Esce 0 se il veleno attacca.
"""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

GIT_ENV = {"GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1", "GIT_AUTHOR_NAME": "t",
           "GIT_AUTHOR_EMAIL": "t@esempio.org", "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@esempio.org"}
SKILL_V1 = '---\nname: humanizer\nmetadata:\n  version: "3.1.0"\n---\n\n# Humanizer\n\n## 1. Not X but Y\n'
SKILL_V2 = SKILL_V1.replace("3.1.0", "3.2.0") + "\n## 27. A new pattern\n"


def git(cwd: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(cwd), *args], check=True, capture_output=True, text=True,
                          env=dict(os.environ, **GIT_ENV)).stdout.strip()


class Scena:
    def __init__(self, radice: Path) -> None:
        self.origine, self.arturo = radice / "origine", radice / "arturo"
        self.origine.mkdir()
        git(self.origine, "init", "-q", "-b", "main")
        self.commit = self.pubblica(SKILL_V1)
        skill = self.arturo / "skills" / "humanizer"
        (skill / "references").mkdir(parents=True)
        (skill / "references" / "originale-en.md").write_text(SKILL_V1, encoding="utf-8")
        (skill / "ORIGINE").write_text(f"repository {self.origine}\ncommit {self.commit[:7]}\nversione 3.1.0\n",
                                       encoding="utf-8")

    def pubblica(self, testo: str) -> str:
        (self.origine / "SKILL.md").write_text(testo, encoding="utf-8")
        git(self.origine, "add", "SKILL.md")
        git(self.origine, "commit", "-q", "-m", "skill")
        return git(self.origine, "rev-parse", "HEAD")

    def lancia(self, script: Path, *args: str, url: str | None = None) -> subprocess.CompletedProcess:
        env = dict(os.environ, **GIT_ENV, HUMANIZER_ORIGINE_URL=url or str(self.origine),
                   ARTURO_REPO_HUMANIZER=str(self.arturo))
        return subprocess.run([sys.executable, "-B", str(script), *args], capture_output=True, text=True,
                              encoding="utf-8", env=env, timeout=120)


def ho01(s: Scena, script: Path) -> None:
    p = s.lancia(script, "controlla")
    assert p.returncode == 0 and "HUMANIZER" not in p.stdout, f"HO01 con origine e Arturo pari la riga compare: {p.stdout!r}"


def ho02(s: Scena, script: Path) -> None:
    nuovo = s.pubblica(SKILL_V2)
    p = s.lancia(script, "controlla")
    assert p.returncode == 0 and "HUMANIZER:" in p.stdout and "3.2.0" in p.stdout and nuovo[:7] in p.stdout, \
        f"HO02 un commit nuovo non si vede: {p.stdout!r} {p.stderr!r}"


def ho03(s: Scena, script: Path) -> None:
    nuovo = s.pubblica(SKILL_V2)
    p = s.lancia(script, "porta")
    skill = s.arturo / "skills" / "humanizer"
    inglese = (skill / "references" / "originale-en.md").read_text(encoding="utf-8")
    origine = (skill / "ORIGINE").read_text(encoding="utf-8")
    differenza = s.arturo / "cache" / "humanizer-differenza.md"
    assert p.returncode == 0 and inglese == SKILL_V2, f"HO03 porta non riscrive l'originale inglese: {p.stderr!r}"
    assert f"commit {nuovo}\n" in origine and "versione 3.2.0" in origine, f"HO03 ORIGINE non segue: {origine!r}"
    assert differenza.is_file() and "+## 27. A new pattern" in differenza.read_text(encoding="utf-8"), \
        "HO03 manca la differenza da riportare in italiano"
    assert s.lancia(script, "controlla").stdout == "", "HO03 dopo porta il controllo non tace"


def ho04(s: Scena, script: Path) -> None:
    p = s.lancia(script, "controlla", url=str(s.origine.parent / "non-esiste"))
    assert p.returncode == 0 and "HUMANIZER" not in p.stdout, f"HO04 offline: rc={p.returncode} {p.stdout!r}"


def ho05(s: Scena, script: Path) -> None:
    # Uno sha corto non si scarica: porta vuole lo sha intero (review del 7/11/2026, finding 116).
    for args in (("bogus",), ("porta", "--commit", "non-un-sha"), ("porta", "--commit", s.commit[:7]),
                 ("controlla", "altro")):
        assert s.lancia(script, *args).returncode == 2, f"HO05 uso sbagliato non esce 2: {args}"


TESTS = {"HO01": ho01, "HO02": ho02, "HO03": ho03, "HO04": ho04, "HO05": ho05}


def prova(script: Path) -> list[str]:
    rossi = []
    for codice, test in TESTS.items():
        radice = Path(tempfile.mkdtemp(prefix="banco-humanizer."))
        try:
            test(Scena(radice), script)
        except AssertionError as e:
            rossi.append(str(e))
        finally:
            shutil.rmtree(radice, ignore_errors=True)
    return rossi


def main() -> int:
    for flusso in (sys.stdout, sys.stderr):
        if hasattr(flusso, "reconfigure"):
            flusso.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--avvelena", action="store_true")
    a = parser.parse_args()
    script = a.repo.resolve() / "bin" / "humanizer-origine.py"
    if a.avvelena:
        copia = Path(tempfile.mkdtemp(prefix="veleno-humanizer.")) / "humanizer-origine.py"
        testo = script.read_text(encoding="utf-8")
        avvelenato = testo.replace("    if pari(fissato, commit):\n        return 0\n", "")
        assert avvelenato != testo, "veleno non applicato: il confronto in controlla è cambiato"
        copia.write_text(avvelenato, encoding="utf-8")
        rossi = prova(copia)
        assert any(r.startswith("HO01") for r in rossi), f"il veleno non attacca HO01: {rossi}"
        print("VELENO HO01 ROSSO: con il confronto tolto la riga compare anche a origine pari")
        return 0
    rossi = prova(script)
    for r in rossi:
        print("ROSSO", r)
    print(f"humanizer origine: {len(TESTS) - len(rossi)}/{len(TESTS)} casi verdi")
    return 1 if rossi else 0


if __name__ == "__main__":
    sys.exit(main())
