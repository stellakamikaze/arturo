#!/usr/bin/env python3
"""bin/fine-coda.py: la FASE 9 di /fine in una chiamata (#4291, F0 L3).

FC01 gate rosso: exit 1, niente commit.
FC02 remote privato: la memoria entra in un commit suo, senza lucchetti, log di Melchior, copie .bak-* e
     indice della memoria; CLAUDE.md e handoff nel commit di sync; push riuscito.
FC03 remote pubblico: CLAUDE.md, memoria e todo restano fuori dal commit, e la riga lo dice.
FC04 retention: senza dry-run non esce niente e la riga dice "NON applicata"; dopo il dry-run della stessa
     sessione l'handoff in uscita va nel cestino.
FC05 aggancio personale: riceve fase e argomenti dopo --, i suoi path entrano nel commit; exit 4 blocca.
FC06 marcatori di conflitto in un file in stage: exit 4, niente commit.
FC07 ~/.claude a metà di un rebase: exit 4 prima del gate.
FC08 push rifiutato perché un'altra macchina ha pushato: pull --rebase --autostash e secondo push riuscito.
FC09 origin è il repository pubblico di Arturo: niente push, "solo locale".

Sulla base 875109c bin/fine-coda.py non esiste: rossi tutti i casi.
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

CASI = ["FC01", "FC02", "FC03", "FC04", "FC05", "FC06", "FC07", "FC08", "FC09"]
FILE = ["bin/fine-coda.py", "bin/handoff-gate.sh", "bin/handoff-retention.py", "bin/handoff_profilo.py",
        "bin/index-rigenera.py", "bin/todo_store.py", "hooks/melchior_match.py", "hooks/controlla-config.py",
        ".gitignore"]
GIT_ENV = {"GIT_AUTHOR_NAME": "Prova", "GIT_AUTHOR_EMAIL": "p@example.com", "GIT_COMMITTER_NAME": "Prova",
           "GIT_COMMITTER_EMAIL": "p@example.com", "GIT_CONFIG_NOSYSTEM": "1"}
VERDE = "# Session Handoff\n## Progetto\n- Nome: libro / Branch: main\n\n## Task Pendenti\nNessun task pendente.\n"
ROSSO = "# Session Handoff\n## Progetto\n- Nome: libro / Branch: main\n\n## Altro\nniente\n"


class Lab:
    def __init__(self, repo: Path, ref: str | None, tmp: Path, visibilita: str = "PRIVATE"):
        self.tmp = tmp
        self.home = tmp / "home"
        self.cl = self.home / ".claude"
        for rel in FILE:
            if ref:
                p = subprocess.run(["git", "-C", str(repo), "show", f"{ref}:{rel}"], capture_output=True)
                if p.returncode:
                    continue
                dati = p.stdout
            else:
                dati = (repo / rel).read_bytes()
            (self.cl / rel).parent.mkdir(parents=True, exist_ok=True)
            (self.cl / rel).write_bytes(dati)
        finti = tmp / "finti"
        finti.mkdir()
        (finti / "gh").write_text(f"#!/bin/sh\necho {visibilita}\n", encoding="utf-8")
        (finti / "gh").chmod(0o755)
        (finti / "gh.cmd").write_text(f"@echo {visibilita}\r\n", encoding="utf-8")
        self.temp = tmp / "temp"
        self.temp.mkdir()
        self.ambiente = dict(os.environ, HOME=str(self.home), USERPROFILE=str(self.home), FINE_CODA_CLAUDE=str(self.cl),
                             PATH=str(finti) + os.pathsep + os.environ.get("PATH", ""), ARTURO_TODO=str(tmp / "eventi.jsonl"),
                             CLAUDE_CODE_SESSION_ID="prova-fc", TMPDIR=str(self.temp), TEMP=str(self.temp),
                             TMP=str(self.temp), ARTURO_TELEMETRIA="0", PYTHONDONTWRITEBYTECODE="1", **GIT_ENV)
        self.remoto = tmp / "privato.git"
        self.git(tmp, "init", "-q", "--bare", "-b", "main", str(self.remoto))
        self.git(self.cl, "init", "-q", "-b", "main")
        self.git(self.cl, "add", "-A")
        self.git(self.cl, "commit", "-q", "-m", "installazione")
        self.git(self.cl, "remote", "add", "origin", str(self.remoto))
        self.git(self.cl, "push", "-q", "origin", "main")

    def git(self, cartella: Path, *a: str) -> str:
        p = subprocess.run(["git", "-C", str(cartella), *a], capture_output=True, text=True, encoding="utf-8",
                           errors="replace", env=self.ambiente if hasattr(self, "ambiente") else dict(os.environ, **GIT_ENV))
        if p.returncode:
            raise RuntimeError(f"git {' '.join(a)}: {p.stderr.strip()}")
        return p.stdout

    def scrivi(self, rel: str, testo: str) -> Path:
        f = self.cl / rel
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(testo, encoding="utf-8")
        return f

    def handoff(self, nome: str = "HANDOFF_2026-10-30_20-00.md", testo: str = VERDE) -> Path:
        return self.scrivi(f"data/handoffs/libro/{nome}", testo)

    def coda(self, handoff: Path, *altro: str) -> subprocess.CompletedProcess:
        return subprocess.run([sys.executable, "-B", str(self.cl / "bin" / "fine-coda.py"), "--handoff", str(handoff),
                               "--slug", "libro", "--trailer", "Prova: banco", *altro], capture_output=True, text=True,
                              encoding="utf-8", errors="replace", env=self.ambiente, timeout=300)

    def retention(self) -> subprocess.CompletedProcess:
        return subprocess.run([sys.executable, "-B", str(self.cl / "bin" / "handoff-retention.py"), "libro",
                               "--radice", str(self.cl / "data" / "handoffs")], capture_output=True, text=True,
                              encoding="utf-8", errors="replace", env=self.ambiente, timeout=60)

    def nel_remoto(self) -> list:
        return self.git(self.remoto, "ls-tree", "-r", "--name-only", "main").split()

    def commit(self) -> int:
        return int(self.git(self.cl, "rev-list", "--count", "HEAD").strip())


def con_lab(repo, ref, prova, **k):
    with tempfile.TemporaryDirectory(prefix="arturo-fc-") as tmp:
        try:
            lab = Lab(repo, ref, Path(tmp), **k)
            if not (lab.cl / "bin" / "fine-coda.py").exists():
                return "bin/fine-coda.py assente"
            return prova(lab)
        except (RuntimeError, OSError, ValueError, subprocess.TimeoutExpired) as e:
            return f"eccezione {e}"


def memoria(lab: Lab) -> None:
    lab.scrivi("CLAUDE.md", "mie regole\n")
    lab.scrivi("data/memory/pattern/nota.md", "---\nname: nota\n---\n")
    lab.scrivi("data/memory/index.md", "indice rigenerato\n")
    lab.scrivi("data/memory/pattern/nota.md.bak-20261030", "copia\n")
    lab.scrivi("data/memory/.melchior-access.log.d/Prova.log", "letture\n")
    lab.scrivi("data/memory/.melchior-embeddings.json", "{}\n")
    lab.scrivi("data/todo/eventi.jsonl", "{}\n")
    lab.scrivi("data/todo/eventi.jsonl.lock", "")


def fc01(lab: Lab):
    prima = lab.commit()
    r = lab.coda(lab.handoff(testo=ROSSO))
    if r.returncode != 1 or lab.commit() != prima:
        return f"rc={r.returncode} commit {prima}->{lab.commit()} {r.stdout.strip()[-160:]!r}"


def fc02(lab: Lab):
    memoria(lab)
    r = lab.coda(lab.handoff())
    remoto = lab.nel_remoto()
    attesi = {"CLAUDE.md", "data/memory/pattern/nota.md", "data/todo/eventi.jsonl",
              "data/handoffs/libro/HANDOFF_2026-10-30_20-00.md"}
    vietati = {"data/memory/index.md", "data/memory/pattern/nota.md.bak-20261030", "data/todo/eventi.jsonl.lock",
               "data/memory/.melchior-access.log.d/Prova.log", "data/memory/.melchior-embeddings.json"}
    msg = lab.git(lab.cl, "log", "--format=%s", "-3").splitlines()
    solo_memoria = lab.git(lab.cl, "show", "--name-only", "--format=", "HEAD~1").split()
    if r.returncode != 0 or not attesi <= set(remoto) or vietati & set(remoto) \
            or "memoria: applicata da /fine" not in msg or set(solo_memoria) != {"data/memory/pattern/nota.md"} \
            or "push riuscito" not in r.stdout:
        return (f"rc={r.returncode} mancano {sorted(attesi - set(remoto))} vietati {sorted(vietati & set(remoto))} "
                f"commit {msg} memoria {solo_memoria} {r.stdout.strip()[-200:]!r}")


def fc03(lab: Lab):
    memoria(lab)
    r = lab.coda(lab.handoff())
    remoto = set(lab.nel_remoto())
    dentro = remoto & {"CLAUDE.md", "data/memory/pattern/nota.md", "data/todo/eventi.jsonl"}
    if r.returncode != 0 or dentro or "non risulta privato" not in r.stdout:
        return f"rc={r.returncode} pubblicati {sorted(dentro)} {r.stdout.strip()[-200:]!r}"


def fc04(lab: Lab):
    for g in range(1, 7):
        lab.handoff(f"HANDOFF_2026-10-0{g}_10-00.md")
    lab.git(lab.cl, "add", "-f", "data/handoffs")
    lab.git(lab.cl, "commit", "-q", "-m", "handoff")
    ultimo = lab.cl / "data" / "handoffs" / "libro" / "HANDOFF_2026-10-06_10-00.md"
    r1 = lab.coda(ultimo)
    c1 = (lab.cl / "data" / "handoffs" / "libro" / "HANDOFF_2026-10-01_10-00.md").exists()
    lab.retention()
    r2 = lab.coda(ultimo)
    tolto = not (lab.cl / "data" / "handoffs" / "libro" / "HANDOFF_2026-10-01_10-00.md").exists()
    cestino = (lab.cl / "data" / "handoffs" / ".cestino" / "libro" / "HANDOFF_2026-10-01_10-00.md").exists()
    fuori_git = "data/handoffs/libro/HANDOFF_2026-10-01_10-00.md" not in lab.nel_remoto()
    if not c1 or "retention NON applicata" not in r1.stdout or r2.returncode != 0 or not tolto or not cestino \
            or not fuori_git:
        return (f"primo giro restava={c1} {r1.stdout.strip()[-120:]!r}; secondo rc={r2.returncode} tolto={tolto} "
                f"cestino={cestino} fuori dal remoto={fuori_git} {r2.stdout.strip()[-160:]!r}")


AGGANCIO = """import json, sys
d = json.load(sys.stdin)
open(d["radice"] + "/personale/visto-" + d["fase"] + ".json", "w", encoding="utf-8").write(json.dumps(d))
if d["fase"] == "prima-commit":
    open(d["radice"] + "/personale/stato.txt", "w", encoding="utf-8").write("scritto\\n")
    if "--blocca" in d["argomenti"]:
        print(json.dumps({"esiti": [], "path": [], "blocca": "R8 di prova"}))
        sys.exit(4)
    print(json.dumps({"esiti": ["stato ok"], "path": ["personale/stato.txt"], "blocca": None}))
else:
    print(json.dumps({"esiti": ["indice personale ok"], "path": [], "blocca": None}))
"""


def fc05(lab: Lab):
    lab.scrivi("personale/fine-coda.py", AGGANCIO)
    r = lab.coda(lab.handoff(), "--", "--progetto", "libro-uf")
    try:
        visto = json.loads((lab.cl / "personale" / "visto-dopo-index.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        visto = {}
    entrato = "personale/stato.txt" in lab.nel_remoto()
    lab.scrivi("personale/stato.txt", "riscritto\n")
    prima = lab.commit()
    rb = lab.coda(lab.handoff("HANDOFF_2026-10-30_21-00.md"), "--", "--blocca")
    if r.returncode != 0 or visto.get("argomenti") != ["--progetto", "libro-uf"] or visto.get("slug") != "libro" \
            or not entrato or "stato ok" not in r.stdout or rb.returncode != 4 or lab.commit() != prima:
        return (f"rc={r.returncode} argomenti={visto.get('argomenti')} entrato={entrato} {r.stdout.strip()[-120:]!r}; "
                f"blocco rc={rb.returncode} commit {prima}->{lab.commit()}")


def fc06(lab: Lab):
    lab.scrivi("bin/nota.txt", "<<<<<<< HEAD\na\n=======\nb\n>>>>>>> altro\n")
    prima = lab.commit()
    r = lab.coda(lab.handoff())
    if r.returncode != 4 or lab.commit() != prima or "MARCATORI" not in r.stdout:
        return f"rc={r.returncode} commit {prima}->{lab.commit()} {r.stdout.strip()[-160:]!r}"


def fc07(lab: Lab):
    (lab.cl / ".git" / "rebase-merge").mkdir()
    r = lab.coda(lab.handoff(testo=ROSSO))
    if r.returncode != 4 or "REBASE A METÀ" not in r.stdout:
        return f"rc={r.returncode} {r.stdout.strip()[-160:]!r}"


def fc08(lab: Lab):
    altra = lab.tmp / "altra"
    lab.git(lab.tmp, "clone", "-q", str(lab.remoto), str(altra))
    (altra / "altra.md").write_text("dall'altra macchina\n", encoding="utf-8")
    lab.git(altra, "add", "altra.md")
    lab.git(altra, "commit", "-q", "-m", "altra")
    lab.git(altra, "push", "-q", "origin", "main")
    lab.scrivi("CLAUDE.md", "mie regole\n")
    r = lab.coda(lab.handoff())
    remoto = set(lab.nel_remoto())
    if r.returncode != 0 or not {"altra.md", "CLAUDE.md"} <= remoto or "push riuscito" not in r.stdout:
        return f"rc={r.returncode} remoto {sorted(remoto)[:6]} {r.stdout.strip()[-200:]!r}"


def fc09(lab: Lab):
    lab.git(lab.cl, "remote", "set-url", "origin", "https://github.com/stellakamikaze/arturo.git")
    memoria(lab)
    r = lab.coda(lab.handoff())
    if r.returncode != 0 or "solo locale" not in r.stdout or "repository pubblico di Arturo" not in r.stdout:
        return f"rc={r.returncode} {r.stdout.strip()[-200:]!r}"


def prova(repo: Path, ref: str | None) -> list:
    rossi = []
    for codice, fn, k in (("FC01", fc01, {}), ("FC02", fc02, {}), ("FC03", fc03, {"visibilita": "PUBLIC"}),
                          ("FC04", fc04, {}), ("FC05", fc05, {}), ("FC06", fc06, {}), ("FC07", fc07, {}),
                          ("FC08", fc08, {}), ("FC09", fc09, {})):
        esito = con_lab(repo, ref, fn, **k)
        if esito:
            rossi.append(f"{codice} {esito}")
    return rossi


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument("--baseline-ref")
    argomenti = parser.parse_args()
    rossi = prova(Path(argomenti.repo), argomenti.baseline_ref)
    if argomenti.baseline_ref:
        codici = [r.split()[0] for r in rossi]
        assert codici == CASI, f"baseline non discriminante: rossi {codici}, attesi {CASI}"
        print(f"BASELINE_DISCRIMINANTE={','.join(codici)}")
        return 0
    for r in rossi:
        print("ROSSO", r)
    print(f"coda di /fine: {len(CASI) - len(rossi)}/{len(CASI)} casi verdi")
    return 1 if rossi else 0


if __name__ == "__main__":
    sys.exit(main())
