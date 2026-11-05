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
ST08 nessun percorso al codice o all'Orsa scritto a mano negli script di hooks/ e bin/: le radici
     passano da hooks/radici.py (radice_arturo, radice_orsa), i messaggi col comando di Arturo da
     comando_arturo(). Restano solo le eccezioni di AMMESSI_ST08, ognuna col suo motivo (#4531);
ST09 radici.py nei due layout: col clone codice e Orsa sono ~/.claude e il comando è
     "python3 ~/.claude/bin/arturo"; col plugin il codice è la cartella del plugin, l'Orsa resta
     ~/.claude (o CLAUDE_CONFIG_DIR) e il comando ha il percorso vero;
ST10 l'interruttore della memoria non guarda bin/arturo accanto agli hook: senza impostazioni è
     spenta in tutti e due i layout, con "accesa": true è accesa in tutti e due (#4531).

Invariante (verde anche sulla base): ST01. Sulla base 94db031 sono rossi ST02-ST10.
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

CASI = ["ST01", "ST02", "ST03", "ST04", "ST05", "ST06", "ST07", "ST08", "ST09", "ST10"]
DISCRIMINANTI = ["ST02", "ST03", "ST04", "ST05", "ST06", "ST07", "ST08", "ST09", "ST10"]
BASH = shutil.which("bash") or "bash"
CODICE = ["hooks/bash-dispatcher.sh", "hooks/inject-now.sh", "hooks/session-start.sh", "bin/telemetria-esito.sh"]
# Ammessi: il file delle preferenze della persona e la cartella delle sue guardie.
AMMESSE = re.compile(r'ORSA_HOOKS=|bash-dispatcher\.local')
# ST08: le radici scritte a mano vietate e le eccezioni, ognuna col perché. None esclude il file,
# una regex ammette solo le righe che la contengono.
FISSO_PY = re.compile(r'Path\.home\(\)\s*/\s*["\']\.claude["\']|expanduser\(\s*["\']~/\.claude|python3 ~/\.claude/bin/arturo')
FISSO_SH = re.compile(r'(\$HOME|\$\{HOME\}|~)/\.claude/(hooks|bin)/')
AMMESSI_ST08 = {
    # Le guardie giudicano i percorsi di ~/.claude come li scrive il comando: restano sulla home vera.
    "hooks/forma_comando.py": None,
    "hooks/memory-write-scanner.py": None,
    "hooks/protect_claude_md.py": None,
    "hooks/radici.py": None,  # è la fonte
    # Le guardie della persona e il suo file .local stanno nell'Orsa per definizione.
    "hooks/bash-dispatcher.sh": r"ORSA_HOOKS=|bash-dispatcher\.local",
    # L'aggiornamento del clone gira solo se il clone sta in ~/.claude: col plugin aggiorna Claude Code (F3).
    "hooks/session-end.sh": r"bin/aggiornamenti\.py",
    # L'aggiornamento del clone è autonomo: deve girare anche con il resto dell'albero a metà o
    # modificato, quindi non importa radici.py. Vale solo col clone in ~/.claude (col plugin, F3).
    "bin/aggiornamenti.py": None,
    "bin/personale.py": None,  # lo lancia l'aggiornamento a metà: autonomo come lui
}


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

        fissi = []
        for file in sorted(list(plugin.glob("hooks/*.py")) + list(plugin.glob("bin/**/*.py"))
                           + list(plugin.glob("hooks/*.sh")) + list(plugin.glob("bin/**/*.sh")) + [plugin / "bin" / "arturo"]):
            rel = file.relative_to(plugin).as_posix()
            if rel in AMMESSI_ST08 and AMMESSI_ST08[rel] is None:
                continue
            ammessa = AMMESSI_ST08.get(rel)
            regola = FISSO_SH if file.suffix == ".sh" else FISSO_PY
            for n, riga in enumerate(file.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
                if riga.lstrip().startswith("#") or not regola.search(riga):
                    continue
                if ammessa and re.search(ammessa, riga):
                    continue
                fissi.append(f"{rel}:{n}")
        if fissi:
            rossi.append(f"ST08 radici scritte a mano ({len(fissi)}): {', '.join(fissi[:8])}")

        def radici(codice: Path, casa: Path, extra: dict | None = None) -> list[str]:
            prog = ("import sys; sys.path.insert(0, sys.argv[1]); import radici as r; "
                    "print(r.radice_arturo()); print(r.radice_orsa()); print(r.comando_arturo())")
            esito = subprocess.run([sys.executable, "-B", "-c", prog, str(codice / "hooks")], capture_output=True,
                                   text=True, encoding="utf-8", errors="replace", env=ambiente(casa, extra), timeout=60)
            return esito.stdout.splitlines() if esito.returncode == 0 else [esito.stderr.strip()[-160:]]

        reale = lambda q: str(Path(os.path.realpath(q)))  # noqa: E731
        clone = radici(clone_home / ".claude", clone_home)
        atteso_clone = [reale(clone_home / ".claude"), str(clone_home / ".claude"), "python3 ~/.claude/bin/arturo"]
        con_plugin = radici(plugin, orsa_home)
        atteso_plugin = [reale(plugin), str(orsa_home / ".claude"), f"python3 {Path(reale(plugin)) / 'bin' / 'arturo'}"]
        altra = tmp / "altra-config"
        con_config = radici(plugin, orsa_home, {"CLAUDE_CONFIG_DIR": str(altra)})
        if clone != atteso_clone:
            rossi.append(f"ST09 radici col clone: {clone} invece di {atteso_clone}")
        elif con_plugin != atteso_plugin:
            rossi.append(f"ST09 radici col plugin: {con_plugin} invece di {atteso_plugin}")
        elif con_config[1:2] != [str(altra)]:
            rossi.append(f"ST09 radice_orsa non segue CLAUDE_CONFIG_DIR: {con_config}")

        def memoria(codice: Path, casa: Path) -> str:
            prog = "import sys; sys.path.insert(0, sys.argv[1]); import melchior_match as m; print(m.memoria_accesa())"
            esito = subprocess.run([sys.executable, "-B", "-c", prog, str(codice / "hooks")], capture_output=True,
                                   text=True, encoding="utf-8", errors="replace",
                                   env={k: v for k, v in ambiente(casa).items() if k != "ARTURO_MEMORIA"}, timeout=60)
            return esito.stdout.strip() or esito.stderr.strip()[-120:]

        sciolti = tmp / "sciolti"  # gli hook senza bin/arturo accanto
        shutil.copytree(plugin / "hooks", sciolti / "hooks", ignore=shutil.ignore_patterns("__pycache__"))
        casa_vuota = tmp / "casa-memoria"
        (casa_vuota / ".claude").mkdir(parents=True)
        spenti = [memoria(plugin, casa_vuota), memoria(sciolti, casa_vuota)]
        impostazioni = casa_vuota / ".claude" / "data" / "memoria" / "impostazioni.json"
        impostazioni.parent.mkdir(parents=True)
        impostazioni.write_text('{"accesa": true}', encoding="utf-8")
        accesi = [memoria(plugin, casa_vuota), memoria(sciolti, casa_vuota)]
        if spenti != ["False", "False"] or accesi != ["True", "True"]:
            rossi.append(f"ST10 la memoria dipende da bin/arturo: senza impostazioni {spenti}, accesa {accesi}")
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
