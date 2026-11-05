#!/usr/bin/env python3
"""ponti.py: le fonti che /monitor può leggere per la persona, e cosa manca per le altre.

Un ponte porta a /monitor un materiale della persona: la posta, il calendario, le trascrizioni
delle call, i task, gli handoff delle sessioni, la memoria. I ponti di serie li conosce Arturo.
I ponti personali li dichiara la persona in ~/.claude/personale/monitor/ponti.json, fuori da git:
gli aggiornamenti di Arturo non li toccano e nel repository non entra niente di suo.

Questo script vede solo ciò che sta sul disco. I connettori di claude.ai (Gmail, Calendar,
Drive) uno script non li vede: li controlla il modello nell'elenco dei suoi tool, con una
lettura di prova. L'inventario di /monitor unisce le due metà.

Non legge mai un segreto: di `gws` guarda solo se il login c'è (`gws auth status`, locale),
dei ponti personali solo se il programma esiste e, se la persona l'ha scritta, l'esito di una
prova senza argomenti segreti.

  ponti.py              l'inventario in parole, per la persona
  ponti.py --json       lo stesso in JSON, per /monitor

ponti.json, una voce per ponte personale:
  {"ponti": [{"nome": "whatsapp", "descrizione": "le chat di lavoro",
              "comando": ["python3", "~/.claude/personale/monitor/wa.py"],
              "prova": ["python3", "~/.claude/personale/monitor/wa.py", "--prova"]}]}
`comando` e `prova` sono liste: niente shell. `~` vale la home.

Variabili per il banco: ARTURO_HOME (al posto di ~/.claude), GWS_CONFIG_BASE (al posto di
~/.config), ARTURO_BIN (la cartella bin con fonte-task.local e memoria.py). Solo libreria standard, Python 3.8 o successivo.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
sys.path.append(str(Path(os.path.realpath(__file__)).parents[2] / "hooks"))
from radici import radice_orsa  # noqa: E402

CASA = Path(os.environ.get("ARTURO_HOME") or radice_orsa())
CONFIG = Path(os.environ.get("GWS_CONFIG_BASE") or Path.home() / ".config")
BIN = Path(os.environ.get("ARTURO_BIN") or Path(__file__).resolve().parents[1])
NOME_GWS = re.compile(r"^gws(-[a-z0-9]+)?$")


def esegui(argv, timeout=10, env=None):
    """(codice, uscita). Un programma assente o lento è un ponte non pronto, non un errore."""
    try:
        r = subprocess.run(argv, capture_output=True, text=True, encoding="utf-8", errors="replace",
                           stdin=subprocess.DEVNULL, timeout=timeout, env=env)
        return r.returncode, r.stdout
    except (OSError, subprocess.TimeoutExpired) as e:
        return -1, str(e)


def ponte(nome, stato, cosa, passo="", dettaglio=""):
    return {"nome": nome, "stato": stato, "cosa": cosa, "passo": passo, "dettaglio": dettaglio}


def google():
    """Gli account di `gws` col login valido. Le cartelle di backup o con spazi non contano."""
    cosa = "le email a cui rispondere, le promesse che hai fatto, le riunioni e le trascrizioni su Drive"
    connettori = ponte("google-connettori", "da controllare in sessione", cosa,
                       "/monitor guarda se Gmail, Calendar e Drive di claude.ai sono fra i suoi tool")
    exe = shutil.which("gws")
    if not exe:
        return [connettori, ponte("google-gws", "da collegare", cosa,
                                  "facoltativo, per più account: /inizio gws")]
    account, rotti = [], []
    cartelle = sorted(d for d in CONFIG.iterdir() if d.is_dir() and NOME_GWS.match(d.name)) \
        if CONFIG.is_dir() else []
    for d in cartelle:
        if not (d / "credentials.enc").exists() and not (d / "client_secret.json").exists():
            continue
        cod, out = esegui([exe, "auth", "status"], env=dict(os.environ, GOOGLE_WORKSPACE_CLI_CONFIG_DIR=str(d)))
        try:
            s = json.loads(out[out.index("{"):]) if "{" in out else {}
        except ValueError:
            s = {}
        ok = cod == 0 and s.get("has_refresh_token") and s.get("encryption_valid", True)
        (account if ok else rotti).append(d.name)
    voci = [connettori]
    if account:
        voci.append(ponte("google-gws", "pronto", cosa, dettaglio=", ".join(account)))
    if rotti:
        voci.append(ponte("google-gws-login", "da collegare", cosa,
                          f"rifai il login di {', '.join(rotti)}: /inizio gws", ", ".join(rotti)))
    if not account and not rotti:
        voci.append(ponte("google-gws", "da collegare", cosa, "facoltativo, per più account: /inizio gws"))
    return voci


def task():
    cosa = "i task nuovi, senza doppioni, e quelli fermi da controllare"
    locale = BIN / "fonte-task.local"
    if locale.is_file():
        riga = next((r for r in locale.read_text(encoding="utf-8").splitlines()
                     if r.strip().startswith("comando")), "")
        return ponte("task", "pronto", cosa, dettaglio="fonte esterna: " + riga.split("=", 1)[-1].strip())
    eventi = CASA / "data" / "todo" / "eventi.jsonl"
    n = sum(1 for _ in eventi.open(encoding="utf-8")) if eventi.is_file() else 0
    return ponte("task", "pronto", cosa, dettaglio=f"arturo todo ({n} eventi)" if n else "arturo todo, ancora vuoto")


def sessioni():
    cosa = "il prossimo passo di ogni lavoro aperto con Claude, e chi lo deve fare"
    idx = CASA / "data" / "handoffs" / "INDEX.md"
    if not idx.is_file():
        return ponte("sessioni", "da collegare", cosa, "si accende da sola alla prima /fine")
    n = sum(1 for r in idx.read_text(encoding="utf-8").splitlines() if "HANDOFF_" in r)
    return ponte("sessioni", "pronto", cosa, dettaglio=f"{n} filoni nell'indice")


def memoria():
    cosa = "le schede dei progetti e le note su persone e decisioni, aggiornate col tuo sì"
    script = BIN / "memoria.py"
    if not script.is_file():
        return ponte("memoria", "da collegare", cosa, "manca bin/memoria.py: /aggiorna")
    cod, out = esegui([sys.executable, str(script), "stato"])
    prima = out.strip().splitlines()[0] if out.strip() else ""
    if cod == 0 and "accesa" in prima and "spenta" not in prima:
        return ponte("memoria", "pronto", cosa)
    return ponte("memoria", "da collegare", cosa, "arturo memoria accendi")


def personali():
    f = CASA / "personale" / "monitor" / "ponti.json"
    if not f.is_file():
        return []
    try:
        voci = json.loads(f.read_text(encoding="utf-8")).get("ponti") or []
    except (OSError, ValueError, AttributeError) as e:
        return [ponte("personali", "rotto", "i tuoi ponti", f"ponti.json illeggibile: {e}")]
    out = []
    for v in voci:
        if not isinstance(v, dict) or not v.get("nome") or not isinstance(v.get("comando"), list) or not v["comando"]:
            out.append(ponte(str(v.get("nome") if isinstance(v, dict) else "?"), "rotto", "",
                             "ogni ponte vuole nome e comando (una lista)"))
            continue
        argv = [os.path.expanduser(str(a)) for a in v["comando"]]
        trovato = shutil.which(argv[0]) or (Path(argv[0]).is_file() and argv[0])
        assente = [a for a in argv[1:] if a.startswith(str(Path.home())) and not Path(a).exists()]
        if not trovato or assente:
            out.append(ponte(v["nome"], "rotto", v.get("descrizione", ""),
                             f"non trovo {(assente or argv)[0]}"))
            continue
        prova = v.get("prova")
        if isinstance(prova, list) and prova:
            cod, _ = esegui([os.path.expanduser(str(a)) for a in prova])
            if cod != 0:
                out.append(ponte(v["nome"], "rotto", v.get("descrizione", ""), f"la prova esce con {cod}"))
                continue
        out.append(ponte(v["nome"], "pronto", v.get("descrizione", ""), dettaglio="personale"))
    return out


def inventario():
    return google() + [task(), sessioni(), memoria()] + personali()


def in_parole(voci):
    gruppi = [("Pronti", "pronto"), ("Da controllare in questa sessione", "da controllare in sessione"),
              ("Da collegare", "da collegare"), ("Rotti", "rotto")]
    righe = []
    for titolo, stato in gruppi:
        sel = [v for v in voci if v["stato"] == stato]
        if not sel:
            continue
        righe.append(f"{titolo}:")
        for v in sel:
            extra = f" ({v['dettaglio']})" if v["dettaglio"] else ""
            passo = f" → {v['passo']}" if v["passo"] else ""
            righe.append(f"- {v['nome']}{extra}: {v['cosa']}{passo}")
    return "\n".join(righe)


def main(argv):
    for flusso in (sys.stdout, sys.stderr):
        if hasattr(flusso, "reconfigure"):
            flusso.reconfigure(encoding="utf-8", errors="replace")
    voci = inventario()
    if "--json" in argv:
        print(json.dumps({"ponti": voci}, ensure_ascii=False, indent=1))
    else:
        print(in_parole(voci))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
