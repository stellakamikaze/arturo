#!/usr/bin/env python3
"""GR01-GR03: una guardia che si rompe non lascia passare in silenzio.

Le guardie Bash passano dal dispatcher, che trasforma un crash in "ask". web-egress-guard è
registrata da sola in settings.json: fino al 15/10/2026, rotta, usciva con 1, un errore non
bloccante, e l'URL passava. Ora chiede, come ask_guard. protect_claude_md resta com'è: rotta esce
con 2 e blocca, per scelta (invariante I02 di test_permissivita_2026_09_08.py).

Il banco rompe una copia della guardia con un'eccezione dentro l'analisi e guarda l'uscita.

GR02 (revisione del 10/11/2026, HK-2): con un python3 che esce 49 senza eseguire niente, come il rimando
del Microsoft Store su Windows, e un jq che non funziona, il dispatcher non legge il comando. Prima usciva
in silenzio su tutto, anche su un rm ricorsivo. Ora chiede conferma per ogni comando, e tace solo se
l'input non porta un comando.
GR03: in quello stato session-start.sh stampa la riga `PYTHON:`. Con un python3 vero non la stampa.

Sulla base 4515e63 GR01, GR02 e GR03 sono rossi.
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

CASI = ["GR01", "GR02", "GR03"]
BASH = shutil.which("bash") or "bash"


def rotta(repo: Path, nome: str, dove: str, dati: dict, cartella: Path) -> subprocess.CompletedProcess:
    """La guardia con `raise` subito prima della riga `dove`, lanciata su `dati`."""
    sorgente = (repo / "hooks" / nome).read_text(encoding="utf-8")
    righe = sorgente.split("\n")
    trovate = [i for i, r in enumerate(righe) if r.strip().startswith(dove)]
    assert len(trovate) == 1, f'{nome}: la riga "{dove}" va trovata una volta, trovata {len(trovate)}'
    i = trovate[0]
    rientro = righe[i][: len(righe[i]) - len(righe[i].lstrip())]
    righe.insert(i, f"{rientro}raise RuntimeError('veleno del banco')")
    (cartella / "hooks").mkdir(parents=True, exist_ok=True)
    copia = cartella / "hooks" / nome
    copia.write_text("\n".join(righe), encoding="utf-8")
    return subprocess.run([sys.executable, "-B", str(copia)], input=json.dumps(dati),
                          capture_output=True, text=True, timeout=30)


def chiede(esito: subprocess.CompletedProcess) -> bool:
    try:
        decisione = json.loads(esito.stdout)["hookSpecificOutput"]["permissionDecision"]
    except Exception:  # noqa: BLE001
        return False
    return esito.returncode == 0 and decisione == "ask" and "rotta" in esito.stdout


def senza_python(cartella: Path) -> dict:
    """L'ambiente con un python3 e un jq finti davanti a tutto nel PATH, e una home vuota."""
    finti = cartella / "finti"
    finti.mkdir(parents=True, exist_ok=True)
    for nome, codice in (("python3", 49), ("jq", 127)):
        f = finti / nome
        f.write_bytes(f"#!/bin/sh\nexit {codice}\n".encode())  # byte: su Windows un CRLF rompe lo script
        f.chmod(0o755)
    casa = cartella / "casa"
    casa.mkdir(exist_ok=True)
    env = dict(os.environ, PATH=str(finti) + os.pathsep + os.environ.get("PATH", ""),
               HOME=str(casa), USERPROFILE=str(casa), ARTURO_TELEMETRIA="0")
    for chiave in ("CLAUDE_ENV_FILE", "CLAUDE_CONFIG_DIR", "CLAUDE_PLUGIN_ROOT"):
        env.pop(chiave, None)
    return env


def dispatcher(repo: Path, env: dict, tool_input: dict) -> subprocess.CompletedProcess:
    dati = {"tool_name": "Bash", "tool_input": tool_input, "cwd": env["USERPROFILE"], "session_id": "banco",
            "hook_event_name": "PreToolUse"}
    return subprocess.run([BASH, str(repo / "hooks" / "bash-dispatcher.sh")], input=json.dumps(dati),
                          capture_output=True, text=True, encoding="utf-8", env=env, timeout=60)


def avvio(repo: Path, env: dict) -> str:
    esito = subprocess.run([BASH, str(repo / "hooks" / "session-start.sh")], input="", cwd=env["USERPROFILE"],
                           capture_output=True, text=True, encoding="utf-8", errors="replace", env=env,
                           timeout=120)
    return esito.stdout


def gr02(repo: Path, cartella: Path) -> list:
    rossi = []
    env = senza_python(cartella)
    for comando in ("rm -rf ~/Documents/x", "ls"):
        esito = dispatcher(repo, env, {"command": comando})
        try:
            uscita = json.loads(esito.stdout)["hookSpecificOutput"]
        except Exception:  # noqa: BLE001
            uscita = {}
        if not (esito.returncode == 0 and uscita.get("permissionDecision") == "ask"
                and "python3" in uscita.get("permissionDecisionReason", "")):
            rossi.append(f"GR02 senza python3 e jq `{comando}` non chiede: rc={esito.returncode} "
                         f"out={esito.stdout[:120]!r}")
    esito = dispatcher(repo, env, {"description": "senza comando"})
    if esito.returncode != 0 or esito.stdout.strip():
        rossi.append(f"GR02 un input senza comando non tace: rc={esito.returncode} out={esito.stdout[:120]!r}")
    return rossi[:1]


def gr03(repo: Path, cartella: Path) -> list:
    env = senza_python(cartella)
    righe = [r for r in avvio(repo, env).splitlines() if r.startswith("PYTHON:")]
    if len(righe) != 1 or "python.org" not in righe[0]:
        return [f"GR03 session-start senza python3 non stampa una riga PYTHON: {righe!r}"]
    vero = dict(env, PATH=os.path.dirname(sys.executable) + os.pathsep + os.environ.get("PATH", ""))
    con = subprocess.run([BASH, "-c", "python3 -c ''"], env=vero, capture_output=True, timeout=60)
    if con.returncode == 0 and "PYTHON:" in avvio(repo, vero):
        return ["GR03 session-start stampa PYTHON: anche con un python3 che funziona"]
    return []


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument("--baseline-ref")
    argomenti = parser.parse_args()
    repo = Path(argomenti.repo)
    rossi = []
    with tempfile.TemporaryDirectory() as tmp:
        esito = rotta(repo, "web-egress-guard.py", "for url in _iter_urls(tool_input):",
                      {"tool_name": "WebFetch", "tool_input": {"url": "https://example.com/"}}, Path(tmp, "a"))
        if not chiede(esito):
            rossi.append(f"GR01 web-egress-guard rotta non chiede: rc={esito.returncode} out={esito.stdout[:120]!r}")
        rossi += gr02(repo, Path(tmp, "b"))
        rossi += gr03(repo, Path(tmp, "c"))

    if argomenti.baseline_ref:
        codici = [r.split()[0] for r in rossi]
        assert codici == CASI, f"baseline non discriminante: rossi {codici}, attesi {CASI}"
        print(f"BASELINE_DISCRIMINANTE={','.join(codici)}")
        return 0
    for r in rossi:
        print("ROSSO", r)
    print(f"guardie rotte: {len(CASI) - len(rossi)}/{len(CASI)} casi verdi")
    return 1 if rossi else 0


if __name__ == "__main__":
    sys.exit(main())
