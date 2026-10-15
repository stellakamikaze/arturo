#!/usr/bin/env python3
"""G201-G2xx: le guardie di Arturo unite alle migliorie della config dell'autore (15/10/2026).

G201 protect_claude_md: git hook, LaunchAgents, systemd utente e autostart si scrivono via
     Edit/Write solo con l'unlock di sistema; un file qualunque resta libero.
G202 protect_claude_md: avvisa quando il CLAUDE.md globale, dopo la modifica, supera il budget
     di righe; sotto il budget tace.
G203 dispatcher: una scrittura via shell su un git hook o un servizio di avvio chiede conferma;
     leggerli o copiarli altrove no.

Sulla base cbd8305 ogni controllo deve fallire con un AssertionError che comincia con il suo codice.
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

BASH = shutil.which("bash") or "bash"


def casa(repo: Path, radice: Path) -> Path:
    home = radice / "home"
    shutil.copytree(repo, home / ".claude", ignore=shutil.ignore_patterns(".git", "__pycache__"))
    return home


def decisione(proc: subprocess.CompletedProcess) -> str:
    if proc.returncode == 2:
        return "block"
    out = proc.stdout.strip()
    if not out:
        return "silent"
    try:
        return json.loads(out.splitlines()[-1])["hookSpecificOutput"]["permissionDecision"]
    except (json.JSONDecodeError, KeyError, TypeError, IndexError):
        return "silent"


def motivo(proc: subprocess.CompletedProcess) -> str:
    try:
        return json.loads(proc.stdout.strip().splitlines()[-1])["hookSpecificOutput"]["permissionDecisionReason"]
    except (json.JSONDecodeError, KeyError, TypeError, IndexError):
        return ""


def env_di(home: Path, **extra: str) -> dict:
    env = {"HOME": str(home), "USERPROFILE": str(home), "PATH": os.environ.get("PATH", ""),
           "PYTHONDONTWRITEBYTECODE": "1", "GIT_CONFIG_GLOBAL": "/dev/null", "ARTURO_TELEMETRIA": "0",
           "TMPDIR": os.environ.get("TMPDIR", "/tmp")}
    env.update(extra)
    return env


def hook(home: Path, nome: str, dati: dict, cwd: Path, **extra: str) -> subprocess.CompletedProcess:
    percorso = home / ".claude" / "hooks" / nome
    assert percorso.exists(), f"{nome} assente"
    return subprocess.run([sys.executable, "-B", str(percorso)], input=json.dumps(dati), text=True,
                          capture_output=True, cwd=str(cwd), timeout=30, check=False, env=env_di(home, **extra))


def dispatcher(home: Path, comando: str, cwd: Path) -> str:
    proc = subprocess.run([BASH, str(home / ".claude" / "hooks" / "bash-dispatcher.sh")],
                          input=json.dumps({"tool_name": "Bash", "tool_input": {"command": comando},
                                            "cwd": str(cwd), "session_id": "g2"}),
                          text=True, capture_output=True, cwd=str(cwd), env=env_di(home), timeout=60, check=False)
    return decisione(proc)


def test_g201(repo: Path) -> None:
    with tempfile.TemporaryDirectory() as d:
        radice = Path(d)
        home = casa(repo, radice)
        progetto = home / "progetto"
        (progetto / ".git" / "hooks").mkdir(parents=True)
        bersagli = [progetto / ".git" / "hooks" / "pre-commit",
                    home / "Library" / "LaunchAgents" / "org.esempio.plist",
                    home / ".config" / "systemd" / "user" / "esempio.service",
                    home / ".config" / "autostart" / "esempio.desktop"]

        def esito(path: Path, sessione: str = "g201") -> str:
            dati = {"tool_name": "Write", "tool_input": {"file_path": str(path), "content": "x"}, "session_id": sessione}
            return decisione(hook(home, "protect_claude_md.py", dati, radice))

        for path in bersagli:
            assert esito(path) == "deny", f"G201 scrittura su un percorso di avvio senza unlock: {path.relative_to(home)}"
        (home / ".claude" / "system-unlock-g201").touch()
        for path in bersagli:
            assert esito(path) == "allow", f"G201 l'unlock di sistema non sblocca {path.relative_to(home)}"
        assert esito(bersagli[0], "altra") == "deny", "G201 l'unlock di una sessione vale per un'altra"
        assert esito(progetto / "capitolo.md") == "silent", "G201 un file qualunque viene fermato"
        assert esito(progetto / ".git" / "config") == "silent", "G201 .git/config viene trattato come un hook"


def test_g202(repo: Path) -> None:
    with tempfile.TemporaryDirectory() as d:
        radice = Path(d)
        home = casa(repo, radice)
        globale = home / ".claude" / "CLAUDE.md"
        globale.write_text("riga\n" * 195, encoding="utf-8")
        (home / ".claude" / "claude-md-unlock-g202").touch()

        def prova(dati: dict, **extra: str) -> subprocess.CompletedProcess:
            return hook(home, "protect_claude_md.py", dict(dati, session_id="g202"), radice, **extra)

        lunga = {"tool_name": "Edit", "tool_input": {"file_path": str(globale), "old_string": "riga\n",
                                                      "new_string": "riga\n" * 11}}
        p = prova(lunga)
        assert decisione(p) == "allow" and "205" in motivo(p) and "200" in motivo(p), \
            f"G202 nessun avviso sul budget di righe del CLAUDE.md globale: {motivo(p)!r}"
        corta = {"tool_name": "Edit", "tool_input": {"file_path": str(globale), "old_string": "riga\n",
                                                      "new_string": "riga\n" * 3}}
        assert "ATTENZIONE" not in motivo(prova(corta)), "G202 avviso sotto il budget"
        assert "ATTENZIONE" in motivo(prova(corta, ARTURO_CLAUDE_MD_RIGHE="150")), \
            "G202 il budget non si cambia con ARTURO_CLAUDE_MD_RIGHE"
        altro = home / "progetto" / "CLAUDE.md"
        altro.parent.mkdir()
        altro.write_text("riga\n" * 400, encoding="utf-8")
        p = prova({"tool_name": "Edit", "tool_input": {"file_path": str(altro), "old_string": "riga\n", "new_string": "x\n"}})
        assert "ATTENZIONE" not in motivo(p), "G202 l'avviso scatta su un CLAUDE.md di progetto"


def test_g203(repo: Path) -> None:
    with tempfile.TemporaryDirectory() as d:
        radice = Path(d)
        home = casa(repo, radice)
        progetto = home / "progetto"
        (progetto / ".git" / "hooks").mkdir(parents=True)
        for comando in ("echo 'curl x' > .git/hooks/pre-commit", "cp script.sh .git/hooks/",
                        "cd .git/hooks && printf x > post-checkout",
                        "cp agente.plist ~/Library/LaunchAgents/org.esempio.plist",
                        "tee ~/.config/systemd/user/esempio.service < unita.txt",
                        "ln -s /tmp/x .git/hooks/pre-push",
                        "python3 -c \"open('.git/hooks/pre-commit','w').write('x')\""):
            assert dispatcher(home, comando, progetto) == "ask", f"G203 scrittura shell su un percorso di avvio: {comando}"
        for comando in ("cat .git/hooks/pre-commit.sample", "cp .git/hooks/pre-commit.sample /tmp/copia",
                        "ls ~/Library/LaunchAgents"):
            assert dispatcher(home, comando, progetto) == "silent", f"G203 lettura di un percorso di avvio fermata: {comando}"


TESTS = {"G201": test_g201, "G202": test_g202, "G203": test_g203}


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
