#!/usr/bin/env python3
"""RV01-RV09: i buchi trovati dalla review del 1/11/2026 sui 16 commit dopo v2026-10-30.

Ogni gruppo raccoglie i casi di una guardia. I casi "ask" o "block" sono quelli che la versione
e80e43d lasciava passare; i casi "silent" sono il lavoro proprio che deve restare libero.

RV01 block-dangerous, git: uno stash conta come salvato solo con `git stash show -p [ref] > file` o
     `git tag nome stash@{N}`, e solo per quel ref; `git stash branch` seguito da drop butta un altro
     stash; `git stash clear` chiede; `--forc` e `--dele` valgono come `--force` e `--delete`; due rami
     cancellati insieme non si coprono a vicenda; un tag omonimo non devia `--contains`.

Sulla base e80e43d ogni gruppo fallisce con un AssertionError che comincia con il suo codice. Con
--avvelena il banco lo prova da solo: rimette nella copia le guardie di e80e43d e vuole ogni gruppo
rosso col suo codice. --baseline-ref fa lo stesso con un altro commit.
"""
from __future__ import annotations

import argparse
import importlib.util
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

BASE = "e80e43d"
_QUI = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("lp", _QUI / "test_lavoro_proprio_2026_10_31.py")
lp = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(lp)
hook, dispatcher, banco, git, verifica, _env = lp.hook, lp.dispatcher, lp.banco, lp.git, lp.verifica, lp._env
sys.path.insert(0, str(_QUI))
import salti_windows  # noqa: E402


def _commit(env: dict, repo: Path, nome: str) -> None:
    (repo / f"{nome}.txt").write_text(nome + "\n", encoding="utf-8")
    git(env, repo, "add", f"{nome}.txt")
    git(env, repo, "commit", "-qm", nome)


def repo_rami_gemelli(radice: Path, env: dict) -> Path:
    """main pushato; i rami `a` e `b` sullo stesso commit unico; `c` con un commit unico e un tag `c`
    su main; `d` con un commit unico copiato anche nel ramo `copia`."""
    repo = lp.repo_con_rami(radice, env)
    git(env, repo, "checkout", "-q", "-b", "a")
    _commit(env, repo, "gemello")
    git(env, repo, "branch", "b")
    git(env, repo, "checkout", "-q", "main")
    git(env, repo, "tag", "c")
    git(env, repo, "checkout", "-q", "-b", "c")
    _commit(env, repo, "unico-c")
    git(env, repo, "checkout", "-q", "main")
    git(env, repo, "checkout", "-q", "-b", "d")
    _commit(env, repo, "unico-d")
    git(env, repo, "branch", "copia")
    git(env, repo, "checkout", "-q", "main")
    return repo


def test_rv01(repo: Path) -> int:
    with tempfile.TemporaryDirectory() as d:
        home, temp, _, _ = banco(Path(d))
        rami = repo_rami_gemelli(Path(d), _env(home, temp))
        casi = [
            # Lavoro proprio: resta libero.
            ("patch dello stesso stash", "git stash show -p > s.patch && git stash drop", "silent"),
            ("patch di stash@{1} e drop di stash@{1}", "git stash show -p stash@{1} > s.patch; git stash drop stash@{1}",
             "silent"),
            ("tag dello stash e drop", "git tag salva stash@{0} && git stash drop", "silent"),
            ("ramo con copia su un ramo che resta", "git branch -D d", "silent"),
            # Devono chiedere.
            ("show senza -p salva solo il diffstat", "git stash show > s.txt && git stash drop", "ask"),
            ("git tag -l non salva", "git tag -l; git stash drop", "ask"),
            ("salva stash@{1} e butta stash@{0}", "git stash show -p stash@{1} > s.patch; git stash drop", "ask"),
            ("stash branch toglie già lo stash: il drop ne butta un altro",
             "git stash branch salva && git stash drop", "ask"),
            ("stash clear", "git stash clear", "ask"),
            ("--forc vale --force", "git branch -d --forc locale", "ask"),
            ("--dele --forc", "git branch --dele --forc locale", "ask"),
            ("due rami gemelli insieme", "git branch -D a b", "ask"),
            ("due rami gemelli in catena", "git branch -D a && git branch -D b", "ask"),
            ("tag omonimo su main", "git branch -D c", "ask"),
        ]
        return verifica("RV01", casi, lambda c: hook(repo, "block-dangerous.py", c, rami, home, temp))


def test_rv02(repo: Path) -> int:
    with tempfile.TemporaryDirectory() as d:
        home, temp, progetto, scratch = banco(Path(d))
        S = scratch.as_posix()
        (progetto / "f.txt").write_text("x\n", encoding="utf-8")
        casi = [
            # Lavoro proprio: resta libero.
            ("sed con indirizzo /e/", "sed -n '/e/p' f.txt", "silent"),
            ("sed -e con s///", "sed -e 's/a/b/' f.txt", "silent"),
            ("xargs grep di rm", "find . -name '*.md' | xargs grep -n rm", "silent"),
            ("cd nello scratchpad e rm relativo", f'cd "{S}"; rm -rf x', "silent"),
            ("rm di una cartella temporanea assoluta", f'rm -rf "{temp.as_posix()}/arturo-prova-x"', "silent"),
            # Devono chiedere.
            ("sed comando e", "sed -n '1e rm -rf ~/Documents/ClaudeCode' f.txt", "ask"),
            ("sed flag e di s///", "sed 's/.*/rm -rf x/e' f.txt", "ask"),
            ("variabile riassegnata dopo il cd", 'S=~/Documents; cd "$S"; S=/tmp; rm -rf ClaudeCode', "ask"),
            ("find -exec env rm", "find . -exec env rm -rf {} +", "ask"),
            ("find -exec sudo rm", "find . -exec sudo rm -rf {} +", "ask"),
            ("find -exec command rm", "find . -exec command rm {} +", "ask"),
            ("find -exec nice -n 5 rm", "find . -exec nice -n 5 rm {} +", "ask"),
            ("find | xargs rm resta", "find . | xargs rm", "ask"),
            ("CR da solo dopo il cd", f'cd "{S}"\r; rm -rf .', "ask"),
            ("cd con due argomenti", f'cd "{S}" foo; rm -rf .', "ask"),
            ("cd ridefinito come funzione", f'cd() {{ :; }}; cd "{S}"; rm -rf .', "ask"),
            ("rm sotto un link creato nello stesso comando",
             f'ln -s ~/Documents/ClaudeCode "{S}/yy" && rm -rf "{S}/yy"/*', "ask"),
            # Bloccati.
            ("rm -rf /*", "rm -rf /*", "block"),
            ("rm -rf ~/*", "rm -rf ~/*", "block"),
            ("del /s /q C:\\*", "del /s /q C:\\*", "block"),
            ("rd /s /q C:\\ da cmd", "cmd //c rd /s /q C:\\", "block"),
            ("format C:", "format C:", "block"),
        ]
        link = scratch / "xx"
        try:
            salti_windows.link(link, home / "Documents" / "ClaudeCode", cartella=True)
            casi.append(("rm sotto un link che esiste verso i progetti", f'rm -rf "{link.as_posix()}"/*', "ask"))
        except salti_windows.SaltoWindows as e:
            salti_windows.dichiara("RV02-link", e)
        return verifica("RV02", casi, lambda c: hook(repo, "block-dangerous.py", c, progetto, home, temp))


TESTS = {"RV01": test_rv01, "RV02": test_rv02}
# Le guardie che ogni gruppo sorveglia: il veleno le rimette com'erano sulla base.
VELENI = {"RV01": ["block-dangerous.py"], "RV02": ["block-dangerous.py"]}


def avvelena(repo: Path, ref: str) -> int:
    """Ogni gruppo, con le sue guardie com'erano su `ref`, deve fallire col suo codice."""
    inerti = []
    for codice, test in TESTS.items():
        copia = Path(tempfile.mkdtemp(prefix="arturo-veleno."))
        try:
            shutil.copytree(repo, copia / "repo", ignore=shutil.ignore_patterns("__pycache__", "*.local", ".git"))
            for nome in VELENI[codice]:
                vecchio = subprocess.run(["git", "-C", str(repo), "show", f"{ref}:{nome if '/' in nome else 'hooks/' + nome}"],
                                         capture_output=True, check=False)
                assert vecchio.returncode == 0, f"veleno: {nome} non si legge su {ref}"
                (copia / "repo" / (nome if "/" in nome else "hooks/" + nome)).write_bytes(vecchio.stdout)
            try:
                test(copia / "repo")
                inerti.append(f"{codice}: verde con le guardie di {ref}")
            except AssertionError as e:
                if not str(e).startswith(codice):
                    inerti.append(f"{codice}: rosso col motivo sbagliato: {e}")
                else:
                    print(f"VELENO {codice} ROSSO: {str(e)[:160]}")
        finally:
            shutil.rmtree(copia, ignore_errors=True)
    assert not inerti, "veleni che non attaccano:\n" + "\n".join(inerti)
    print(f"VELENI_ROSSI={','.join(TESTS)} veleni={len(TESTS)}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--baseline-ref")
    parser.add_argument("--avvelena", action="store_true")
    parser.add_argument("--solo", help="codici dei gruppi da provare, separati da virgola")
    args = parser.parse_args()
    repo = args.repo.resolve()
    if args.avvelena or args.baseline_ref:
        return avvelena(repo, args.baseline_ref or BASE)
    totale, errori = 0, []
    for codice, prova in TESTS.items():
        if args.solo and codice not in args.solo.split(","):
            continue
        try:
            totale += prova(repo)
        except AssertionError as e:
            errori.append(str(e))
    for e in errori:
        print("KO", e)
    if errori:
        return 1
    print(f"PASS revisione-2026-11-01 gruppi={len(TESTS)} casi={totale}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
