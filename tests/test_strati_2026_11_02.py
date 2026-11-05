#!/usr/bin/env python3
"""ST01-ST05: il codice di Arturo funziona anche fuori da ~/.claude (strati F1, docs/strati.md).

Il plugin mette hook e bin/ in una cartella sua; ~/.claude resta l'Orsa della persona. Le guardie,
l'avvio e la telemetria devono trovare il codice dalla propria cartella, non da $HOME/.claude.

ST01 nel clone (codice dentro ~/.claude) il dispatcher blocca `rm -rf ~/`;
ST02 col codice fuori da ~/.claude e un'Orsa vuota, il dispatcher blocca `rm -rf ~/`
     (prima la guardia mancava in ~/.claude/hooks e il crash diventava una sola conferma);
ST03 col codice fuori, la lettura delle credenziali chiede conferma come nel clone;
ST04 l'avvio scrive in $CLAUDE_ENV_FILE ARTURO_CODICE e il PATH della cartella del codice;
ST05 dispatcher, inject-now, session-start e telemetria-esito non chiamano codice in
     $HOME/.claude/hooks|bin: restano solo il file .local e le guardie della persona;
ST06 Write su un file della cache di un plugin installato (~/.claude/plugins/cache/...) è negato
     da protect_claude_md: col plugin lì stanno le guardie e l'aggiornamento di Arturo;
ST07 una scrittura via shell nella cache dei plugin chiede conferma, come su ~/.claude/hooks: col
     percorso assoluto, relativa dopo un `cd ~/.claude` e con la sessione già nella cache. Il file ha
     un nome neutro (#4566, 4/11/2026): con aggiornamenti.py il caso passava per il nome, e il
     pre-filtro del dispatcher non conosceva la cartella.

Invariante (verde anche sulla base): ST01. Sulla base 94db031 sono rossi ST02-ST07.
"""
from __future__ import annotations

import argparse
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path

CASI = ["ST01", "ST02", "ST03", "ST04", "ST05", "ST06", "ST07"]
DISCRIMINANTI = ["ST02", "ST03", "ST04", "ST05", "ST06", "ST07"]
BASH = shutil.which("bash") or "bash"
CODICE = ["hooks/bash-dispatcher.sh", "hooks/inject-now.sh", "hooks/session-start.sh", "bin/telemetria-esito.sh"]
# Ammessi: il file delle preferenze della persona e la cartella delle sue guardie.
AMMESSE = re.compile(r'ORSA_HOOKS=|bash-dispatcher\.local')


def estrai(repo: Path, ref: str | None, dest: Path) -> None:
    """hooks/ e bin/ del repository (o della base `ref`) dentro dest."""
    dest.mkdir(parents=True, exist_ok=True)
    if ref:
        dati = subprocess.run(["git", "-C", str(repo), "archive", ref, "hooks", "bin"],
                              capture_output=True, check=True).stdout
        with tarfile.open(fileobj=io.BytesIO(dati)) as tar:
            tar.extractall(dest)
        return
    for cartella in ("hooks", "bin"):
        shutil.copytree(repo / cartella, dest / cartella, ignore=shutil.ignore_patterns("__pycache__"))


def ambiente(home: Path, extra: dict | None = None) -> dict:
    return {**os.environ, "HOME": str(home), "USERPROFILE": str(home), "ARTURO_TELEMETRIA": "0",
            "ARTURO_AGGIORNAMENTI": "manuali", "GIT_TERMINAL_PROMPT": "0", **(extra or {})}


def dispatcher(codice: Path, home: Path, comando: str, cwd: Path | None = None) -> subprocess.CompletedProcess:
    dati = {"tool_name": "Bash", "tool_input": {"command": comando}, "session_id": "st", "cwd": str(cwd or home)}
    return subprocess.run([BASH, str(codice / "hooks" / "bash-dispatcher.sh")], input=json.dumps(dati),
                          capture_output=True, text=True, encoding="utf-8", errors="replace",
                          env=ambiente(home), timeout=120)


def bloccato(esito: subprocess.CompletedProcess) -> bool:
    return esito.returncode == 2 and "Bloccato" in esito.stderr


def chiede(esito: subprocess.CompletedProcess) -> bool:
    return esito.returncode == 0 and '"permissionDecision": "ask"' in esito.stdout


def prova(repo: Path, ref: str | None) -> list[str]:
    rossi = []
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        clone_home, orsa_home, plugin = tmp / "clone", tmp / "orsa", tmp / "plugin" / "arturo"
        estrai(repo, ref, clone_home / ".claude")
        (orsa_home / ".claude").mkdir(parents=True)
        estrai(repo, ref, plugin)

        if not bloccato(dispatcher(clone_home / ".claude", clone_home, "rm -rf ~/")):
            rossi.append("ST01 nel clone il dispatcher non blocca rm -rf ~/")
        esito = dispatcher(plugin, orsa_home, "rm -rf ~/")
        if not bloccato(esito):
            rossi.append(f"ST02 col codice fuori da ~/.claude rm -rf ~/ non è bloccato: rc={esito.returncode}")
        if not chiede(dispatcher(plugin, orsa_home, "cat ~/.claude/.credentials.json")):
            rossi.append("ST03 col codice fuori la lettura delle credenziali non chiede conferma")

        env_file = tmp / "env"
        progetto = tmp / "progetto"
        progetto.mkdir()
        subprocess.run([BASH, str(plugin / "hooks" / "session-start.sh")], input='{"source":"startup"}',
                       cwd=progetto, capture_output=True, text=True, encoding="utf-8", errors="replace",
                       env=ambiente(orsa_home, {"CLAUDE_ENV_FILE": str(env_file)}), timeout=120)
        scritto = env_file.read_text(encoding="utf-8") if env_file.exists() else ""
        # La cartella come la scrive bash: su Windows `/tmp/...` o `/c/...`, non `C:\...` (#4790).
        visto = subprocess.run([BASH, "-c", 'cd "$1" && pwd', "_", str(plugin)], capture_output=True,
                               text=True, encoding="utf-8", errors="replace").stdout.strip() or str(plugin)
        if f'ARTURO_CODICE="{visto}"' not in scritto or f'{visto}/bin:' not in scritto:
            rossi.append(f"ST04 l'avvio non esporta la cartella del codice: {scritto[-200:]!r}")

        fissi = []
        for rel in CODICE:
            for n, riga in enumerate((plugin / rel).read_text(encoding="utf-8").splitlines(), 1):
                if riga.lstrip().startswith("#") or AMMESSE.search(riga):
                    continue
                if re.search(r'\$HOME/\.claude/(hooks|bin)/', riga):
                    fissi.append(f"{rel}:{n}")
        if fissi:
            rossi.append(f"ST05 codice cercato in $HOME/.claude: {', '.join(fissi[:6])}")

        cache = orsa_home / ".claude" / "plugins" / "cache" / "arturo" / "arturo" / "1.0" / "bin"
        cache.mkdir(parents=True)
        # Un nome che nessuna regola conosce: conta solo la cartella (#4566).
        bersaglio = cache / "strumento.py"
        bersaglio.write_text("# firmato\n", encoding="utf-8")
        dati = {"tool_name": "Write", "session_id": "st", "cwd": str(orsa_home),
                "tool_input": {"file_path": str(bersaglio), "content": "print('altro')\n"}}
        esito = subprocess.run([sys.executable, str(plugin / "hooks" / "protect_claude_md.py")],
                               input=json.dumps(dati), capture_output=True, text=True, encoding="utf-8",
                               errors="replace", env=ambiente(orsa_home), timeout=60)
        if '"permissionDecision": "deny"' not in esito.stdout:
            rossi.append(f"ST06 Write nella cache del plugin non è negato: {esito.stdout[-160:]!r}")
        relativo = bersaglio.relative_to(orsa_home / ".claude").as_posix()
        # In bash `C:\Users\...` senza virgolette perde le barre: su Windows le forme vere sono
        # `C:/Users/...` e quella di Git Bash, `/c/Users/...`, che la guardia non riconosceva (#4790).
        assolute = [("assoluta", f"echo x > {bersaglio.as_posix()}", None)]
        if os.name == "nt":
            git_bash = "/" + bersaglio.as_posix()[0].lower() + bersaglio.as_posix()[2:]
            assolute.append(("assoluta di Git Bash", f"echo x > {git_bash}", None))
        for nome, comando, cwd in (*assolute,
                                   ("dopo cd ~/.claude", f"cd ~/.claude && echo x > {relativo}", None),
                                   ("dalla cartella della cache", "echo x > strumento.py", cache)):
            if not chiede(dispatcher(plugin, orsa_home, comando, cwd)):
                rossi.append(f"ST07 la scrittura via shell nella cache del plugin non chiede conferma ({nome})")
                break
    return rossi


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument("--baseline-ref")
    argomenti = parser.parse_args()
    rossi = prova(Path(argomenti.repo), argomenti.baseline_ref)
    if argomenti.baseline_ref:
        codici = [r.split()[0] for r in rossi]
        assert codici == DISCRIMINANTI, f"baseline non discriminante: rossi {codici}, attesi {DISCRIMINANTI}"
        print(f"BASELINE_DISCRIMINANTE={','.join(codici)}")
        return 0
    for r in rossi:
        print("ROSSO", r)
    print(f"strati: {len(CASI) - len(rossi)}/{len(CASI)} casi verdi")
    return 1 if rossi else 0


if __name__ == "__main__":
    sys.exit(main())
