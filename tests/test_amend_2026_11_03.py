#!/usr/bin/env python3
"""AM01-AM05: git commit --amend chiede quando l'ultimo commit non è di questa sessione (3/11/2026, #4187).

Segnalazione n. 25: fra il commit della sessione A e il suo `--amend` per un refuso, la sessione B aveva
fatto un commit, e l'amend ha riscritto quello di B. block-dangerous.py nel modo `dopo` (PostToolUse di
Bash) registra per sessione l'HEAD lasciato da ogni `git commit`; prima di un amend, un HEAD che la
sessione non ha registrato chiede conferma (regola git-amend).

AM01 amend con il registro vuoto: chiede.
AM02 commit registrato col modo `dopo`, poi amend dalla stessa sessione: tace. Da un'altra sessione: chiede.
AM03 dopo il commit registrato, un commit fatto da un'altra sessione (git diretto, senza registro):
     l'amend chiede. Il caso di Filippo.
AM04 il dispatcher vero manda alla guardia `git -C repo commit --amend --no-edit` e `git commit --am -m x`.
AM05 il modo `dopo` senza session_id, con un id non valido o fuori da un repository non scrive niente
     e non fallisce; `git commit -m x && git commit --amend --no-edit` nello stesso comando tace.

Sulla base c4ae5a4 ogni gruppo fallisce con un AssertionError che comincia con il suo codice. Con
--avvelena il banco lo prova da solo: rimette nella copia le guardie di c4ae5a4 (git show) e vuole
ogni gruppo rosso col suo codice. --baseline-ref fa lo stesso con un altro commit.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

BASE = "c4ae5a4"
SESSIONE = "sessione-a"
ALTRA = "sessione-b"


def decisione(proc: subprocess.CompletedProcess) -> str:
    if proc.returncode == 2:
        return "block"
    out = proc.stdout.strip()
    if not out:
        return "silent" if proc.returncode == 0 else f"rc{proc.returncode}"
    try:
        return json.loads(out.splitlines()[0])["hookSpecificOutput"]["permissionDecision"]
    except (json.JSONDecodeError, KeyError, TypeError, IndexError):
        return "silent"


def _env(home: Path) -> dict:
    temp = home / "tmp"
    temp.mkdir(parents=True, exist_ok=True)
    env = {"HOME": str(home), "USERPROFILE": str(home), "PATH": os.environ.get("PATH", ""),
           "PYTHONDONTWRITEBYTECODE": "1", "PYTHONIOENCODING": "utf-8", "ARTURO_TELEMETRIA": "0",
           "TEMP": str(temp), "TMP": str(temp), "TMPDIR": str(temp),
           "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1",
           "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@example.invalid",
           "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@example.invalid"}
    for k in ("SYSTEMROOT", "SystemRoot", "WINDIR"):
        if k in os.environ:
            env[k] = os.environ[k]
    return env


def guardia(hooks: Path, home: Path, comando: str, cwd: Path, sessione, dopo: bool = False) -> subprocess.CompletedProcess:
    dati = {"tool_name": "Bash", "tool_input": {"command": comando}, "cwd": str(cwd),
            "hook_event_name": "PostToolUse" if dopo else "PreToolUse"}
    if sessione is not None:
        dati["session_id"] = sessione
    argomenti = [sys.executable, "-B", str(hooks / "block-dangerous.py")] + (["dopo"] if dopo else [])
    return subprocess.run(argomenti, input=json.dumps(dati), text=True, encoding="utf-8", capture_output=True,
                          timeout=30, check=False, env=_env(home))


def prima(hooks, home, comando, cwd, sessione=SESSIONE) -> str:
    return decisione(guardia(hooks, home, comando, cwd, sessione))


def git(home: Path, cartella: Path, *argomenti: str) -> None:
    subprocess.run(["git", *argomenti], cwd=str(cartella), env=_env(home), capture_output=True, check=True, timeout=30)


def commit_della_sessione(hooks, home, repo, nome, sessione=SESSIONE) -> None:
    """Un commit fatto dalla sessione: git, poi il modo `dopo` col comando che l'ha fatto."""
    (repo / nome).write_text(nome + "\n", encoding="utf-8")
    git(home, repo, "add", nome)
    comando = f"git commit -qm {nome}"
    git(home, repo, "commit", "-qm", nome)
    p = guardia(hooks, home, comando, repo, sessione, dopo=True)
    assert p.returncode == 0 and not p.stdout.strip(), f"il modo dopo ha scritto o fallito: rc={p.returncode} {p.stdout!r}"


def commit_esterno(home, repo, nome) -> None:
    (repo / nome).write_text(nome + "\n", encoding="utf-8")
    git(home, repo, "add", nome)
    git(home, repo, "commit", "-qm", nome)


def banco(radice: Path):
    home = radice / "home"
    repo = radice / "progetto"
    (home / ".claude").mkdir(parents=True)
    repo.mkdir()
    git(home, repo, "init", "-q", "-b", "main")
    commit_esterno(home, repo, "base.txt")
    return home, repo


def verifica(codice: str, casi) -> int:
    sbagliati = [f"{nome}: atteso {atteso}, ottenuto {got}" for nome, got, atteso in casi if got != atteso]
    assert not sbagliati, f"{codice} " + " | ".join(sbagliati)
    return len(casi)


def test_am01(hooks: Path) -> int:
    with tempfile.TemporaryDirectory() as d:
        home, repo = banco(Path(d))
        casi = [
            ("amend senza registro", prima(hooks, home, "git commit --amend -m refuso", repo), "ask"),
            ("amend --no-edit senza registro", prima(hooks, home, f"git -C {repo.as_posix()} commit --amend --no-edit",
                                                    Path(d)), "ask"),
            ("amend senza session_id", prima(hooks, home, "git commit --amend -m x", repo, sessione=None), "ask"),
            ("commit normale tace", prima(hooks, home, "git commit -m x", repo), "silent"),
        ]
        return verifica("AM01", casi)


def test_am02(hooks: Path) -> int:
    with tempfile.TemporaryDirectory() as d:
        home, repo = banco(Path(d))
        commit_della_sessione(hooks, home, repo, "a.txt")
        casi = [
            ("amend della stessa sessione", prima(hooks, home, "git commit --amend -m 'senza refuso'", repo), "silent"),
            ("amend da una sottocartella", prima(hooks, home, "cd .. && git -C progetto commit --amend --no-edit", repo),
             "silent"),
            ("amend di un'altra sessione", prima(hooks, home, "git commit --amend -m x", repo, sessione=ALTRA), "ask"),
        ]
        # Dopo l'amend confermato, il modo `dopo` registra il commit nuovo: l'amend successivo tace.
        git(home, repo, "commit", "-q", "--amend", "-m", "senza refuso")
        guardia(hooks, home, "git commit -q --amend -m 'senza refuso'", repo, SESSIONE, dopo=True)
        casi.append(("secondo amend dopo il primo", prima(hooks, home, "git commit --amend --no-edit", repo), "silent"))
        return verifica("AM02", casi)


def test_am03(hooks: Path) -> int:
    with tempfile.TemporaryDirectory() as d:
        home, repo = banco(Path(d))
        commit_della_sessione(hooks, home, repo, "a.txt")
        commit_esterno(home, repo, "b.txt")  # la sessione B, fra il commit di A e il suo amend
        casi = [
            ("amend sul commit di B", prima(hooks, home, "git commit --amend -m refuso", repo), "ask"),
            ("amend con prefisso --am", prima(hooks, home, "git commit --am -m refuso", repo), "ask"),
        ]
        motivo = guardia(hooks, home, "git commit --amend -m refuso", repo, SESSIONE).stdout
        casi.append(("il motivo nomina il commit", "b.txt" in motivo and "un'altra sessione" in motivo, True))
        return verifica("AM03", casi)


def test_am04(hooks: Path) -> int:
    with tempfile.TemporaryDirectory() as d:
        home, repo = banco(Path(d))
        shutil.copytree(hooks, home / ".claude" / "hooks", ignore=shutil.ignore_patterns("__pycache__", "*.local"))
        commit_esterno(home, repo, "b.txt")

        def dispatcher(comando: str) -> str:
            dati = {"tool_name": "Bash", "tool_input": {"command": comando}, "cwd": str(repo),
                    "hook_event_name": "PreToolUse", "session_id": SESSIONE}
            p = subprocess.run([shutil.which("bash") or "bash", str(home / ".claude" / "hooks" / "bash-dispatcher.sh")],
                               input=json.dumps(dati), text=True, encoding="utf-8", capture_output=True, timeout=120,
                               check=False, env=_env(home))
            return decisione(p)

        casi = [
            ("-C e --no-edit", dispatcher(f"git -C {repo.as_posix()} commit --amend --no-edit"), "ask"),
            ("--am -m", dispatcher("git commit --am -m x"), "ask"),
            ("git log e amend", dispatcher("git log -1 && git commit --amend -m x"), "ask"),
        ]
        return verifica("AM04", casi)


def test_am05(hooks: Path) -> int:
    with tempfile.TemporaryDirectory() as d:
        home, repo = banco(Path(d))
        registro = home / ".claude" / "session-env"
        fuori = Path(d) / "fuori"
        fuori.mkdir()
        esiti = [guardia(hooks, home, "git commit -m x", repo, None, dopo=True),
                 guardia(hooks, home, "git commit -m x", repo, "../fuga", dopo=True),
                 guardia(hooks, home, "git commit -m x", fuori, SESSIONE, dopo=True)]
        casi = [("il modo dopo non fallisce", all(p.returncode == 0 and not p.stdout.strip() for p in esiti), True),
                ("niente registro senza id valido o fuori repo",
                 sorted(p.name for p in registro.glob("*")) if registro.is_dir() else [], [])]
        guardia(hooks, home, "echo commit", repo, SESSIONE, dopo=True)
        casi.append(("un comando che non è un commit non registra",
                     sorted(p.name for p in registro.glob("*")) if registro.is_dir() else [], []))
        casi.append(("commit e amend nello stesso comando",
                     prima(hooks, home, "git commit -qm x && git commit --amend --no-edit", repo), "silent"))
        commit_della_sessione(hooks, home, repo, "a.txt")
        casi.append(("il registro esiste dopo un commit vero", (registro / f"commit-{SESSIONE}.json").is_file(), True))
        return verifica("AM05", casi)


TESTS = {"AM01": test_am01, "AM02": test_am02, "AM03": test_am03, "AM04": test_am04, "AM05": test_am05}


def avvelena(repo: Path, ref: str) -> int:
    """Ogni gruppo, con le guardie com'erano su `ref`, deve fallire col suo codice."""
    elenco = subprocess.run(["git", "-C", str(repo), "ls-tree", "--name-only", f"{ref}:hooks"], capture_output=True,
                            text=True, encoding="utf-8", check=False)
    assert elenco.returncode == 0, f"veleno: la base {ref} non si legge da {repo}: {elenco.stderr.strip()}"
    inerti = []
    for codice, test in TESTS.items():
        copia = Path(tempfile.mkdtemp(prefix="arturo-veleno."))
        try:
            shutil.copytree(repo / "hooks", copia / "hooks", ignore=shutil.ignore_patterns("__pycache__", "*.local"))
            for nome in ("block-dangerous.py", "bash-dispatcher.sh"):
                vecchio = subprocess.run(["git", "-C", str(repo), "show", f"{ref}:hooks/{nome}"], capture_output=True,
                                         check=False)
                if vecchio.returncode == 0:
                    (copia / "hooks" / nome).write_bytes(vecchio.stdout)
            try:
                test(copia / "hooks")
                inerti.append(f"{codice}: verde con le guardie di {ref}")
            except AssertionError as e:
                if not str(e).startswith(codice):
                    inerti.append(f"{codice}: rosso col motivo sbagliato: {e}")
                else:
                    print(f"VELENO {codice} ROSSO: {str(e)[:120]}")
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
    args = parser.parse_args()
    repo = args.repo.resolve()
    if args.avvelena or args.baseline_ref:
        return avvelena(repo, args.baseline_ref or BASE)
    totale, errori = 0, []
    for prova in TESTS.values():
        try:
            totale += prova(repo / "hooks")
        except AssertionError as e:
            errori.append(str(e))
    for e in errori:
        print("KO", e)
    if errori:
        return 1
    print(f"PASS amend gruppi={len(TESTS)} casi={totale}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
