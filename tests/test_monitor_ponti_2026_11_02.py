#!/usr/bin/env python3
"""/monitor in Arturo, Fase 1: bin/monitor/ponti.py dice quali fonti della persona sono pronte.

MP01 casa vuota: esce 0; task pronto con arturo todo, sessioni e memoria da collegare, i connettori
     di claude.ai da controllare in sessione.
MP02 gws: conta solo le cartelle gws o gws-<nome> con le credenziali; un login valido è pronto, uno
     scaduto è da collegare; backup e cartelle con spazi non contano.
MP03 bin/fonte-task.local: il ponte dei task dice la fonte esterna.
MP04 ponti personali da personale/monitor/ponti.json: un ponte buono è pronto; un file che manca,
     una prova che fallisce, una voce senza comando sono rotti; un JSON rotto non fa cadere niente.
MP05 --json: ogni voce ha nome, stato, cosa, passo, dettaglio, e lo stato sta nell'elenco chiuso.
MP06 nessun segreto in uscita: un valore che `gws auth status` stampa non arriva all'inventario.
MP07 il nucleo è ponti.py, e nessun file di bin/monitor porta le forme di una persona (fisc, crm, pec,
     canali Slack): fingerprint.py e cursori.py ci sono, ma generici (3/11/2026).

Sulla base 2fe4037 (il dev prima di bin/monitor) sono rossi tutti i casi.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

CASI = ["MP01", "MP02", "MP03", "MP04", "MP05", "MP06", "MP07"]
DISCRIMINANTI = CASI
STATI = {"pronto", "da collegare", "da controllare in sessione", "rotto"}
# Le forme del /monitor di una persona: fingerprint fiscali, CRM, PEC, rotazione dei canali Slack. I nomi
# propri li ferma l'igiene I03 (tests/igiene.py), che li tiene solo come impronte.
FORME_PERSONALI = ("fisc:", "crm:", "pec:<", "slack-canali", "slack_canali")
GWS_FINTO = """#!/usr/bin/env python3
import json, os, sys
d = os.environ.get("GOOGLE_WORKSPACE_CLI_CONFIG_DIR", "")
ok = d.endswith("gws-lavoro")
print(json.dumps({"has_refresh_token": ok, "encryption_valid": True, "campo_riservato": "VALORE-CHE-NON-DEVE-USCIRE"}))
"""


class Lab:
    def __init__(self, repo: Path, tmp: Path):
        self.repo, self.tmp = repo, tmp
        self.script = repo / "bin" / "monitor" / "ponti.py"

    def casa(self, nome):
        c = self.tmp / nome
        (c / "home").mkdir(parents=True)
        (c / "config").mkdir()
        (c / "bin").mkdir()
        (c / "path").mkdir()
        return c

    def lancia(self, c, *arg):
        env = dict(os.environ, ARTURO_HOME=str(c / "home"), GWS_CONFIG_BASE=str(c / "config"),
                   ARTURO_BIN=str(c / "bin"), PATH=f"{c / 'path'}{os.pathsep}{os.environ.get('PATH', '')}")
        if not self.script.is_file():
            return 127, "", "ponti.py assente"
        r = subprocess.run([sys.executable, str(self.script), *arg], capture_output=True, text=True,
                           encoding="utf-8", env=env, timeout=60)
        return r.returncode, r.stdout, r.stderr

    def voci(self, c):
        cod, out, err = self.lancia(c, "--json")
        if cod != 0:
            return cod, {}, err
        return cod, {v["nome"]: v for v in json.loads(out)["ponti"]}, err


def senza_gws(c):
    """Un gws finto che non esiste: PATH punta a una cartella vuota davanti, ma gws vero può esserci."""
    finto = c / "path" / "gws"
    finto.write_text("#!/bin/sh\nexit 127\n")
    finto.chmod(0o755)


def prova(lab: Lab) -> list:
    rossi = []

    c = lab.casa("mp01")
    senza_gws(c)
    cod, v, err = lab.voci(c)
    ok = (cod == 0 and v.get("task", {}).get("stato") == "pronto" and "arturo todo" in v["task"]["dettaglio"]
          and v.get("sessioni", {}).get("stato") == "da collegare" and v.get("memoria", {}).get("stato") == "da collegare"
          and v.get("google-connettori", {}).get("stato") == "da controllare in sessione")
    if not ok:
        rossi.append(f"MP01 casa vuota: exit {cod}, voci {sorted(v)}, {err.strip()[:100]}")

    c = lab.casa("mp02")
    g = c / "path" / "gws"
    g.write_text(GWS_FINTO)
    g.chmod(0o755)
    for nome in ("gws-lavoro", "gws-vecchio", "gws-lavoro 0000aaaa1111bbbb", "gws-lavoro.bak-20260915"):
        (c / "config" / nome).mkdir()
        (c / "config" / nome / "credentials.enc").write_text("x")
    cod, v, err = lab.voci(c)
    pronto = v.get("google-gws", {})
    login = v.get("google-gws-login", {})
    if not (cod == 0 and pronto.get("stato") == "pronto" and pronto.get("dettaglio") == "gws-lavoro"
            and login.get("stato") == "da collegare" and login.get("dettaglio") == "gws-vecchio"):
        rossi.append(f"MP02 gws: exit {cod}, pronto {pronto.get('dettaglio')!r}, login {login.get('dettaglio')!r}")

    c = lab.casa("mp03")
    senza_gws(c)
    (c / "bin" / "fonte-task.local").write_text("comando = python3 ~/.claude/personale/mia_fonte.py\n")
    cod, v, _ = lab.voci(c)
    if not (cod == 0 and "fonte esterna" in v.get("task", {}).get("dettaglio", "")
            and "mia_fonte.py" in v["task"]["dettaglio"]):
        rossi.append(f"MP03 fonte esterna: {v.get('task')}")

    c = lab.casa("mp04")
    senza_gws(c)
    pm = c / "home" / "personale" / "monitor"
    pm.mkdir(parents=True)
    buono = pm / "buono.py"
    buono.write_text("import sys\nsys.exit(0)\n")
    cattivo = pm / "cattivo.py"
    cattivo.write_text("import sys\nsys.exit(4)\n")
    py = sys.executable
    (pm / "ponti.json").write_text(json.dumps({"ponti": [
        {"nome": "chat", "descrizione": "le chat", "comando": [py, str(buono)], "prova": [py, str(buono)]},
        {"nome": "manca", "comando": [py, str(Path.home() / "non-esiste-mai-xyz.py")]},
        {"nome": "prova-ko", "comando": [py, str(cattivo)], "prova": [py, str(cattivo)]},
        {"nome": "senza-comando"}]}))
    cod, v, err = lab.voci(c)
    stati = {k: v.get(k, {}).get("stato") for k in ("chat", "manca", "prova-ko", "senza-comando")}
    (pm / "ponti.json").write_text("{rotto")
    cod2, v2, _ = lab.voci(c)
    if not (cod == 0 and stati == {"chat": "pronto", "manca": "rotto", "prova-ko": "rotto", "senza-comando": "rotto"}
            and cod2 == 0 and v2.get("personali", {}).get("stato") == "rotto" and "task" in v2):
        rossi.append(f"MP04 ponti personali: exit {cod}/{cod2}, stati {stati}, json rotto {v2.get('personali')}")

    c = lab.casa("mp05")
    senza_gws(c)
    cod, out, _ = lab.lancia(c, "--json")
    try:
        voci = json.loads(out)["ponti"] if cod == 0 else []
    except ValueError:
        voci = []
    chiavi_ok = voci and all(set(x) == {"nome", "stato", "cosa", "passo", "dettaglio"} and x["stato"] in STATI
                             for x in voci)
    cod_t, testo, _ = lab.lancia(c)
    if not (chiavi_ok and cod_t == 0 and "Pronti:" in testo and "Da collegare:" in testo):
        rossi.append(f"MP05 schema: exit {cod}, voci {len(voci)}, testo {testo[:80]!r}")

    c = lab.casa("mp06")
    g = c / "path" / "gws"
    g.write_text(GWS_FINTO)
    g.chmod(0o755)
    (c / "config" / "gws-lavoro").mkdir()
    (c / "config" / "gws-lavoro" / "credentials.enc").write_text("x")
    _, j, _ = lab.lancia(c, "--json")
    _, t, _ = lab.lancia(c)
    if not j or "VALORE-CHE-NON-DEVE-USCIRE" in j + t:
        rossi.append("MP06 segreto: il valore stampato da gws arriva all'inventario, o l'inventario è vuoto")

    cartella = lab.repo / "bin" / "monitor"
    personali = sorted(f"{f.name}: {forma}" for f in cartella.glob("*.py") for forma in FORME_PERSONALI
                       if forma in f.read_text(encoding="utf-8").lower())
    if not (cartella / "ponti.py").is_file() or personali:
        rossi.append(f"MP07 nucleo: ponti.py presente {(cartella / 'ponti.py').is_file()}, forme personali {personali}")
    return rossi


def main() -> int:
    for flusso in (sys.stdout, sys.stderr):
        if hasattr(flusso, "reconfigure"):
            flusso.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument("--baseline-ref")
    a = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix="arturo-mp-") as tmp:
        rossi = prova(Lab(Path(a.repo), Path(tmp)))
    if a.baseline_ref:
        codici = [r.split()[0] for r in rossi]
        assert codici == DISCRIMINANTI, f"baseline non discriminante: rossi {codici}, attesi {DISCRIMINANTI}"
        print(f"BASELINE_DISCRIMINANTE={','.join(codici)}")
        return 0
    for r in rossi:
        print("ROSSO", r)
    print(f"ponti di /monitor: {len(CASI) - len(rossi)}/{len(CASI)} casi verdi")
    return 1 if rossi else 0


if __name__ == "__main__":
    sys.exit(main())
