#!/usr/bin/env python3
"""R01-R08: revisione di prodotto del 30/9/2026.

R01 rm ricorsivo e find che cancella chiedono conferma fuori dalle cartelle
rigenerabili. R02-R04 il canale di aggiornamento: /aggiorna annulla da solo
un'applicazione che rompe la config, torna indietro anche dopo un /fine, e con
un repository personale fa un merge invece di riscrivere commit pubblicati.
R05 il controllo di integrita' della config. R06 i tool di task tracking
riaccesi per i modelli attuali. R07 lo stesso slug di handoff in /inizio e
/fine. R08 l'audit senza PyYAML. I blocchi bash di /aggiorna si eseguono cosi'
come sono scritti nel comando. Sulla base 86ba137 ogni controllo deve fallire.
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

BASH = shutil.which("bash") or "bash"
GIT_ENV = {
    "GIT_AUTHOR_NAME": "prova", "GIT_AUTHOR_EMAIL": "prova@example.invalid",
    "GIT_COMMITTER_NAME": "prova", "GIT_COMMITTER_EMAIL": "prova@example.invalid",
    "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1",
}


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def blocco(testo: str, titolo: str, indice: int = 0) -> str:
    """Il blocco ```bash numero `indice` dopo l'intestazione `titolo`."""
    inizio = testo.index(titolo)
    blocchi = re.findall(r"```bash\n(.*?)```", testo[inizio:], re.S)
    return "\n".join(riga[3:] if riga.startswith("   ") else riga for riga in blocchi[indice].splitlines())


def esegui(script: str, home: Path, cwd: Path | None = None) -> subprocess.CompletedProcess:
    env = dict(os.environ, HOME=str(home), **GIT_ENV)
    return subprocess.run([BASH, "-c", script], cwd=str(cwd or home), env=env,
                          capture_output=True, text=True, timeout=60)


def git(cartella: Path, *argomenti: str, home: Path) -> str:
    r = subprocess.run(["git", "-C", str(cartella), *argomenti], env=dict(os.environ, HOME=str(home), **GIT_ENV),
                       capture_output=True, text=True, timeout=30)
    assert r.returncode == 0, f"git {' '.join(argomenti)}: {r.stderr.strip()}"
    return r.stdout.strip()


def decisione(repo: Path, home: Path, comando: str) -> str:
    dati = json.dumps({"tool_name": "Bash", "tool_input": {"command": comando}, "cwd": str(home / "progetto")})
    r = subprocess.run([BASH, str(home / ".claude" / "hooks" / "bash-dispatcher.sh")], input=dati,
                       env=dict(os.environ, HOME=str(home)), capture_output=True, text=True, timeout=30)
    if r.returncode == 2:
        return "deny"
    return "ask" if '"ask"' in r.stdout else "nessuna"


def test_r01(repo: Path) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        home = Path(tmp) / "home"
        (home / ".claude").mkdir(parents=True)
        shutil.copytree(repo / "hooks", home / ".claude" / "hooks")
        casi = {
            f'rm -rf "{home}/Documents"': "ask",
            "rm -rf ~/Desktop/Tesi": "ask",
            "rm -rf mio-libro/capitoli": "ask",
            "/bin/rm -rf ~/Documents": "ask",
            "\\rm -r capitoli": "ask",
            'find . -name "*.md" -delete': "ask",
            "find ~/Documents -type f -exec rm {} +": "ask",
            "rm -rf node_modules": "nessuna",
            "rm -rf dist build": "nessuna",
            "rm -rf /tmp/prova": "nessuna",
            "rm file.txt": "nessuna",
            "find . -name '*.md'": "nessuna",
        }
        for comando, atteso in casi.items():
            ottenuto = decisione(repo, home, comando)
            assert ottenuto == atteso, f"R01 {comando!r}: atteso {atteso}, ottenuto {ottenuto}"


def laboratorio(repo: Path, base: Path):
    """Upstream bare con settings.json, NOVITA.md e il controllo di integrita', e un utente che lo clona."""
    home = base / "home"
    seme = base / "seme"
    (seme / "hooks").mkdir(parents=True)
    home.mkdir()
    impostazioni = {"env": {"A": "1", "B": "2", "C": "3"}, "permissions": {"defaultMode": "auto"}}
    (seme / "settings.json").write_text(json.dumps(impostazioni, indent=2) + "\n")
    (seme / "NOVITA.md").write_text("# Novita\n\n## 2026-09-01 — Prima\n")
    controllo = repo / "hooks" / "controlla-config.py"
    if controllo.exists():
        shutil.copy(controllo, seme / "hooks" / "controlla-config.py")
    git(seme, "init", "-q", "-b", "main", home=home)
    git(seme, "add", "-A", home=home)
    git(seme, "commit", "-q", "-m", "v0", home=home)
    upstream = base / "upstream.git"
    git(base, "clone", "-q", "--bare", str(seme), str(upstream), home=home)
    git(base, "clone", "-q", str(upstream), str(home / ".claude"), home=home)
    autore = base / "autore"
    git(base, "clone", "-q", str(upstream), str(autore), home=home)
    return home, upstream, autore


def pubblica(autore: Path, home: Path, file: str, testo: str, messaggio: str) -> None:
    (autore / file).write_text(testo)
    git(autore, "commit", "-q", "-am", messaggio, home=home)
    git(autore, "push", "-q", "origin", "main", home=home)


def aggiorna(repo: Path, home: Path) -> subprocess.CompletedProcess:
    testo = read(repo / "commands" / "aggiorna.md")
    return esegui(blocco(testo, "## Passo 1") + "\n" + blocco(testo, "## Passo 3"), home)


def test_r02(repo: Path) -> None:
    """Conflitto su settings.json: l'applicazione si annulla e la config resta integra."""
    with tempfile.TemporaryDirectory() as tmp:
        home, _, autore = laboratorio(repo, Path(tmp))
        utente = home / ".claude"
        (utente / "settings.json").write_text(read(utente / "settings.json").replace('"B": "2"', '"B": "utente"'))
        git(utente, "commit", "-q", "-am", "chore: session sync", home=home)
        prima = git(utente, "rev-parse", "HEAD", home=home)
        pubblica(autore, home, "settings.json", read(autore / "settings.json").replace('"B": "2"', '"B": "autore"'), "v1")
        esito = aggiorna(repo, home)
        assert "APPLICAZIONE ANNULLATA" in esito.stdout, f"R02 conflitto non annullato: {esito.stdout[-400:]} {esito.stderr[-400:]}"
        assert git(utente, "rev-parse", "HEAD", home=home) == prima, "R02 la copia non e' tornata a prima"
        json.loads(read(utente / "settings.json"))
        assert not git(utente, "status", "--porcelain", home=home), "R02 file lasciati a meta'"


def test_r03(repo: Path) -> None:
    """/aggiorna indietro dopo un session sync di /fine: torna alla versione vecchia e tiene il commit dell'utente."""
    with tempfile.TemporaryDirectory() as tmp:
        home, _, autore = laboratorio(repo, Path(tmp))
        utente = home / ".claude"
        pubblica(autore, home, "NOVITA.md", "# Novita\n\n## 2026-09-02 — Seconda\n\n## 2026-09-01 — Prima\n", "v1")
        esito = aggiorna(repo, home)
        assert "Seconda" in read(utente / "NOVITA.md"), f"R03 aggiornamento non applicato: {esito.stdout[-300:]} {esito.stderr[-300:]}"
        (utente / "mio.txt").write_text("mio\n")
        git(utente, "add", "mio.txt", home=home)
        git(utente, "commit", "-q", "-m", "chore: session sync", home=home)
        testo = read(repo / "commands" / "aggiorna.md")
        indietro = esegui(blocco(testo, "## Tornare indietro", 1), home)
        assert "Seconda" not in read(utente / "NOVITA.md"), f"R03 indietro non eseguito: {indietro.stdout[-300:]} {indietro.stderr[-300:]}"
        assert (utente / "mio.txt").exists(), "R03 il commit dell'utente e' sparito"


def test_r04(repo: Path) -> None:
    """Con un repository personale come origin l'aggiornamento non riscrive i commit gia' pubblicati."""
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        home, upstream, autore = laboratorio(repo, base)
        utente = home / ".claude"
        personale = base / "personale.git"
        git(base, "init", "-q", "--bare", "-b", "main", str(personale), home=home)
        git(utente, "remote", "rename", "origin", "upstream", home=home)
        git(utente, "remote", "add", "origin", str(personale), home=home)
        (utente / "mio.txt").write_text("mio\n")
        git(utente, "add", "mio.txt", home=home)
        git(utente, "commit", "-q", "-m", "chore: session sync", home=home)
        git(utente, "push", "-q", "origin", "main", home=home)
        pubblicato = git(utente, "rev-parse", "HEAD", home=home)
        pubblica(autore, home, "NOVITA.md", "# Novita\n\n## 2026-09-02 — Seconda\n\n## 2026-09-01 — Prima\n", "v1")
        esito = aggiorna(repo, home)
        assert "Seconda" in read(utente / "NOVITA.md"), f"R04 aggiornamento non applicato: {esito.stdout[-300:]} {esito.stderr[-300:]}"
        r = subprocess.run(["git", "-C", str(utente), "merge-base", "--is-ancestor", pubblicato, "HEAD"], capture_output=True)
        assert r.returncode == 0, "R04 i commit pubblicati sono stati riscritti"


def test_r05(repo: Path) -> None:
    controllo = repo / "hooks" / "controlla-config.py"
    assert controllo.exists(), "R05 controllo di integrita' assente"
    with tempfile.TemporaryDirectory() as tmp:
        cartella = Path(tmp)
        (cartella / "settings.json").write_text('{"env": {')
        r = subprocess.run([sys.executable, str(controllo), str(cartella)], capture_output=True, text=True)
        assert r.returncode == 1 and "CONFIG ROTTA" in r.stdout, "R05 JSON rotto non segnalato"
        (cartella / "settings.json").write_text("{}")
        r = subprocess.run([sys.executable, str(controllo), "--quiet", str(cartella)], capture_output=True, text=True)
        assert r.returncode == 0 and not r.stdout, "R05 config sana segnalata"
    for comando in ("inizio.md", "fine.md", "aggiorna.md"):
        assert "controlla-config.py" in read(repo / "commands" / comando), f"R05 {comando} non controlla la config"
    assert "controlla-config.py" in read(repo / "hooks" / "session-start.sh"), "R05 l'avvio non controlla la config"
    inizio = read(repo / "commands" / "inizio.md")
    fase0 = inizio[inizio.index("## FASE 0"):inizio.index("## FASE 1")]
    assert "ORIGIN_ARTURO" in fase0, "R05 /inizio applica gli aggiornamenti di Arturo senza chiedere"


def test_r06(repo: Path) -> None:
    impostazioni = json.loads(read(repo / "settings.json"))
    usati = any("TaskCreate" in read(p) for p in (repo / "commands").glob("*.md"))
    if usati:
        assert impostazioni.get("env", {}).get("CLAUDE_CODE_ENABLE_TODO_TOOLS") == "1", \
            "R06 i comandi usano TaskCreate, che sui modelli attuali e' spento senza CLAUDE_CODE_ENABLE_TODO_TOOLS=1"


def test_r07(repo: Path) -> None:
    inizio = read(repo / "commands" / "inizio.md")
    fine = read(repo / "commands" / "fine.md")
    regola = "tr '[:upper:]' '[:lower:]' | sed -E 's/[^a-z0-9]+/-/g; s/^-+|-+$//g'"
    assert regola in inizio and regola in fine, "R07 /inizio e /fine calcolano lo slug dell'handoff in modi diversi"
    assert "ls -t" not in fine and "ls -t" not in inizio, "R07 handoff ordinati per data del file"


def test_r08(repo: Path) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        home = base / "home"
        shutil.copytree(repo, home / ".claude", ignore=shutil.ignore_patterns(".git", "*.ipc"))
        finto = base / "senzayaml"
        finto.mkdir()
        (finto / "yaml.py").write_text('raise ImportError("PyYAML assente")\n')
        r = subprocess.run([BASH, str(home / ".claude" / "skills" / "system-audit" / "audit.sh")],
                           env=dict(os.environ, HOME=str(home), PYTHONPATH=str(finto)),
                           capture_output=True, text=True, timeout=120)
        testo = r.stdout + r.stderr
        assert "FAIL" not in testo.replace("FAIL=0", ""), f"R08 audit rosso senza PyYAML: {[l for l in testo.splitlines() if 'FAIL' in l]}"


TESTS = {
    "R01": test_r01, "R02": test_r02, "R03": test_r03, "R04": test_r04,
    "R05": test_r05, "R06": test_r06, "R07": test_r07, "R08": test_r08,
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
            except (AssertionError, FileNotFoundError, ValueError, IndexError, json.JSONDecodeError,
                    subprocess.SubprocessError):
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
