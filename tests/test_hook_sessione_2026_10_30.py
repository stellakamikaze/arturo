#!/usr/bin/env python3
"""HS01-HS04: gli hook di inizio e fine sessione con più sessioni aperte.

HS01 la chiusura toglie i file di sblocco della propria sessione;
HS02 lascia quelli di un'altra sessione aperta (fino al 30/10/2026 li toglieva tutti);
HS03 toglie quelli rimasti da più di un giorno e i file seen vecchi di memory-retrieve;
HS04 l'avvio dice che ~/.claude è a metà rebase anche se la sessione parte da un progetto.

HS05-HS09 (27/11/2026): l'avvio non riporta ~/.claude/arturo/radice a una versione più vecchia del plugin. Una
sessione aperta prima di un aggiornamento gira dalla cartella della versione vecchia, e ogni suo /clear riscriveva
radice verso quella cartella.
HS05 radice a 0.2.26, la sessione gira da 0.2.25: radice resta a 0.2.26;
HS06 radice a 0.2.24, la sessione gira da 0.2.25: radice passa a 0.2.25;
HS07 radice a una cartella sparita: radice passa alla cartella della sessione;
HS08 radice a un clone fuori dalla cartella dei plugin: radice passa alla cartella della sessione;
HS09 radice a 0.2.9, la sessione gira da 0.2.10: il confronto è numerico, radice passa a 0.2.10.

Invariante (verde su ogni base): HS01.
Sulla base 749e18d sono rossi HS02, HS03, HS04 e HS06-HS09 (radice non c'era ancora).
Sulla base c8b3a55 è rosso HS05.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

CASI = ["HS01", "HS02", "HS03", "HS04", "HS05", "HS06", "HS07", "HS08", "HS09"]
DISCRIMINANTI = {"749e18d": ["HS02", "HS03", "HS04", "HS06", "HS07", "HS08", "HS09"], "c8b3a55": ["HS05"]}
BASH = shutil.which("bash") or "bash"


def lancia(hook: str, testo: str, home: Path, progetto: Path, dati: dict) -> subprocess.CompletedProcess:
    script = home / ".claude" / "hooks" / hook
    script.parent.mkdir(parents=True, exist_ok=True)
    with open(str(script), "w", encoding="utf-8", newline="\n") as uscita:  # write_text(newline=) vuole Python 3.10
        uscita.write(testo)
    env = {**os.environ, "HOME": str(home), "USERPROFILE": str(home), "ARTURO_TELEMETRIA": "0",
           "ARTURO_AGGIORNAMENTI": "manuali", "GIT_TERMINAL_PROMPT": "0"}
    return subprocess.run([BASH, str(script)], input=json.dumps(dati), cwd=progetto, capture_output=True,
                          text=True, encoding="utf-8", errors="replace", env=env, timeout=120)


def prova(fine: str, avvio: str) -> list[str]:
    rossi = []
    with tempfile.TemporaryDirectory() as tmp:
        home, progetto = Path(tmp, "home"), Path(tmp, "progetto")
        cartella = home / ".claude"
        (cartella / "session-env").mkdir(parents=True)
        progetto.mkdir()
        (progetto / "CLAUDE.md").write_text("progetto\n", encoding="utf-8")
        mia, altra, vecchia = (cartella / "config-unlock-mia", cartella / "config-unlock-altra",
                               cartella / "claude-md-unlock-vecchia")
        seen_vecchio = cartella / "session-env" / "retrieve-vecchia.seen"
        for f in (mia, altra, vecchia, seen_vecchio):
            f.write_text("", encoding="utf-8")
        due_giorni_fa = time.time() - 2 * 86400
        for f in (vecchia, seen_vecchio):
            os.utime(f, (due_giorni_fa, due_giorni_fa))
        lancia("session-end.sh", fine, home, progetto, {"session_id": "mia", "hook_event_name": "SessionEnd"})
        if mia.exists():
            rossi.append("HS01 lo sblocco della propria sessione resta")
        if not altra.exists():
            rossi.append("HS02 lo sblocco di un'altra sessione aperta è stato tolto")
        if vecchia.exists() or seen_vecchio.exists():
            rossi.append("HS03 restano lo sblocco o il file seen di più di un giorno fa")

        subprocess.run(["git", "init", "-q", str(cartella)], check=True)
        (cartella / ".git" / "rebase-merge").mkdir()
        esito = lancia("session-start.sh", avvio, home, progetto, {"source": "startup"})
        if "metà rebase" not in esito.stdout:
            rossi.append(f"HS04 l'avvio non segnala il rebase in ~/.claude: {esito.stdout[-200:]!r}")
    return rossi

def avvio_radice(testo: str, home: Path, versione: str, radice_prima: str | None) -> str:
    cache = home / ".claude" / "plugins" / "cache" / "arturo" / "arturo"
    script = cache / versione / "hooks" / "session-start.sh"
    script.parent.mkdir(parents=True, exist_ok=True)
    with open(str(script), "w", encoding="utf-8", newline="\n") as uscita:
        uscita.write(testo)
    puntatore = home / ".claude" / "arturo" / "radice"
    puntatore.parent.mkdir(parents=True, exist_ok=True)
    if radice_prima is not None:
        puntatore.write_text(radice_prima, encoding="utf-8")
    progetto = home / "progetto"
    progetto.mkdir(exist_ok=True)
    env = {**os.environ, "HOME": str(home), "USERPROFILE": str(home), "ARTURO_TELEMETRIA": "0",
           "ARTURO_AGGIORNAMENTI": "manuali", "GIT_TERMINAL_PROMPT": "0", "ARTURO_PATH_CANDIDATE": ""}
    env.pop("CLAUDE_CONFIG_DIR", None)
    env.pop("CLAUDE_ENV_FILE", None)
    subprocess.run([BASH, str(script)], input=json.dumps({"source": "clear"}), cwd=progetto, capture_output=True,
                   text=True, encoding="utf-8", errors="replace", env=env, timeout=120)
    return puntatore.read_text(encoding="utf-8") if puntatore.exists() else ""


def prova_radice(avvio: str) -> list[str]:
    rossi = []
    # (codice, versione della sessione, radice prima, radice attesa o None = quella della sessione, cartelle esistenti)
    casi = [("HS05", "0.2.25", "0.2.26", "0.2.26", ["0.2.26"]),
            ("HS06", "0.2.25", "0.2.24", None, ["0.2.24"]),
            ("HS07", "0.2.25", "0.2.99", None, []),
            ("HS08", "0.2.25", "clone", None, []),
            ("HS09", "0.2.10", "0.2.9", None, ["0.2.9"])]
    for codice, versione, prima, attesa, esistenti in casi:
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp, "home")
            cache = home / ".claude" / "plugins" / "cache" / "arturo" / "arturo"
            for nome in esistenti:
                (cache / nome).mkdir(parents=True, exist_ok=True)
            if prima == "clone":
                radice_prima = Path(tmp, "clone", "arturo")
                radice_prima.mkdir(parents=True)
            else:
                radice_prima = cache / prima
            dopo = avvio_radice(avvio, home, versione, str(radice_prima))
            atteso = str(cache / (attesa or versione))
            if dopo != atteso:
                rossi.append(f"{codice} radice è {dopo!r}, attesa {atteso!r}")
    return rossi


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument("--baseline-ref")
    argomenti = parser.parse_args()
    repo = Path(argomenti.repo)

    def testo(nome: str) -> str:
        if argomenti.baseline_ref:
            return subprocess.run(["git", "-C", str(repo), "show", f"{argomenti.baseline_ref}:hooks/{nome}"],
                                  capture_output=True, text=True, encoding="utf-8", check=True).stdout
        return (repo / "hooks" / nome).read_text(encoding="utf-8")

    rossi = prova(testo("session-end.sh"), testo("session-start.sh")) + prova_radice(testo("session-start.sh"))
    if argomenti.baseline_ref:
        codici = [r.split()[0] for r in rossi]
        attesi = DISCRIMINANTI.get(argomenti.baseline_ref[:7])
        assert codici == attesi, f"baseline non discriminante: rossi {codici}, attesi {attesi}"
        print(f"BASELINE_DISCRIMINANTE={','.join(codici)}")
        return 0
    for r in rossi:
        print("ROSSO", r)
    print(f"hook di sessione: {len(CASI) - len(rossi)}/{len(CASI)} casi verdi")
    return 1 if rossi else 0


if __name__ == "__main__":
    sys.exit(main())
