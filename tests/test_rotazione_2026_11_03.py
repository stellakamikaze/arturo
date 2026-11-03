#!/usr/bin/env python3
"""La rotazione automatica della sessione (3/11/2026): il fine leggero e la marca di /inizio.

A ogni milestone il modello lancia /fine --rotazione (la coda con --leggero), poi un mod apre /clear e
"/inizio <slug> -- --rotazione <compito>".

RT01 fine-coda --leggero: la retention non gira anche col dry-run pronto, l'esito dice "retention: al
     fine completo" e il segno del fine completo non nasce.
RT02 fine-coda completo: senza handoff (solo sync) niente segno; con l'handoff scrive la data di oggi in
     <cartella dell'handoff>/.ultimo-fine-completo, il segno entra nel commit con l'handoff e l'indice
     non lo elenca.
RT03 arturo contesto libro -- --rotazione scrivere i test: "compito: scrivere i test" e "rotazione: sì".
RT04 arturo contesto libro -- scrivere i test: il compito, e nessuna riga rotazione.
RT05 arturo contesto --stdin con la marca, nella forma di commands/inizio.md: compito e rotazione.
RT06 --rotazione prima di " -- " resta un'opzione sconosciuta: exit 3, nessuna riga rotazione.

bin/contesto.py non ha un'uscita --json: la chiave "rotazione" non ha dove stare, e RT06 sorveglia la
marca scritta nel posto sbagliato.

Sulla base bf394ad (il dev prima della rotazione) sono rossi RT01, RT02, RT03 e RT05; RT04 e RT06 sono
invarianti. Con --avvelena una copia del repository rotta in un punto alla volta deve far fallire i casi
che lo sorvegliano.
"""
from __future__ import annotations

import argparse
import io
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
from datetime import date
from pathlib import Path

CASI = ["RT01", "RT02", "RT03", "RT04", "RT05", "RT06"]
DISCRIMINANTI = ["RT01", "RT02", "RT03", "RT05"]
PERCORSI = ["bin", "hooks/melchior_match.py", "hooks/controlla-config.py", ".gitignore"]
SEGNO = ".ultimo-fine-completo"
GIT_ENV = {"GIT_AUTHOR_NAME": "Prova", "GIT_AUTHOR_EMAIL": "p@example.com", "GIT_COMMITTER_NAME": "Prova",
           "GIT_COMMITTER_EMAIL": "p@example.com", "GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": os.devnull}
VERDE = "# Session Handoff\n## Progetto\n- Nome: libro / Branch: main\n\n## Task Pendenti\nNessun task pendente.\n"
# (casi che devono diventare rossi, file, testo giusto, testo rotto)
VELENI = [
    (["RT01"], "bin/fine-coda.py",
     '        if a.leggero:\n            esiti.append("retention: al fine completo")',
     '        if False:\n            esiti.append("retention: al fine completo")'),
    (["RT02"], "bin/fine-coda.py", 'SEGNO_COMPLETO = ".ultimo-fine-completo"', 'SEGNO_COMPLETO = ".fine-completo"'),
    (["RT03", "RT05"], "bin/contesto.py", "        parole = parole[1:]\n", "        parole = parole[0:]\n"),
    (["RT04"], "bin/contesto.py", "    if rotazione:\n        righe.append(", "    if True:\n        righe.append("),
    (["RT06"], "bin/contesto.py", 'if p != "--tutti"]', 'if p not in ("--tutti", "--rotazione")]'),
]


class Lab:
    """Una HOME di prova con ~/.claude in git, un remote privato finto e la cartella del progetto libro."""

    def __init__(self, repo: Path, ref: str | None, tmp: Path):
        self.tmp = tmp
        self.home = tmp / "home"
        self.cl = self.home / ".claude"
        self.cl.mkdir(parents=True)
        if ref:
            dati = subprocess.run(["git", "-C", str(repo), "archive", ref, *PERCORSI], capture_output=True,
                                  check=True).stdout
            with tarfile.open(fileobj=io.BytesIO(dati)) as archivio:
                archivio.extractall(self.cl, **({"filter": "data"} if hasattr(tarfile, "data_filter") else {}))
        else:
            for rel in PERCORSI:
                if (repo / rel).is_dir():
                    shutil.copytree(str(repo / rel), str(self.cl / rel),
                                    ignore=shutil.ignore_patterns("__pycache__", "*.local"))
                else:
                    (self.cl / rel).parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(str(repo / rel), str(self.cl / rel))
        (self.home / "Documents" / "ClaudeCode" / "libro").mkdir(parents=True)
        finti = tmp / "finti"
        finti.mkdir()
        (finti / "gh").write_text("#!/bin/sh\necho PRIVATE\n", encoding="utf-8")
        (finti / "gh").chmod(0o755)
        (finti / "gh.cmd").write_text("@echo PRIVATE\r\n", encoding="utf-8")
        temp = tmp / "temp"
        temp.mkdir()
        self.ambiente = dict(os.environ, HOME=str(self.home), USERPROFILE=str(self.home),
                             FINE_CODA_CLAUDE=str(self.cl), PATH=str(finti) + os.pathsep + os.environ.get("PATH", ""),
                             ARTURO_TODO=str(tmp / "eventi.jsonl"), CLAUDE_CODE_SESSION_ID="prova-rt",
                             TMPDIR=str(temp), TEMP=str(temp), TMP=str(temp), ARTURO_TELEMETRIA="0",
                             ARTURO_OGGI="2026-11-03", PYTHONDONTWRITEBYTECODE="1", **GIT_ENV)
        self.ambiente.pop("PROJECTS_BASE", None)
        self.remoto = tmp / "privato.git"
        self.git(tmp, "init", "-q", "--bare", "-b", "main", str(self.remoto))
        self.git(self.cl, "init", "-q", "-b", "main")
        self.git(self.cl, "add", "-A")
        self.git(self.cl, "commit", "-q", "-m", "installazione")
        self.git(self.cl, "remote", "add", "origin", str(self.remoto))
        self.git(self.cl, "push", "-q", "origin", "main")

    def git(self, cartella: Path, *a: str) -> str:
        p = subprocess.run(["git", "-C", str(cartella), *a], capture_output=True, text=True, encoding="utf-8",
                           errors="replace", env=getattr(self, "ambiente", dict(os.environ, **GIT_ENV)))
        if p.returncode:
            raise RuntimeError(f"git {' '.join(a)}: {p.stderr.strip()}")
        return p.stdout

    def lancia(self, *a: str, entrata: str | None = None) -> subprocess.CompletedProcess:
        return subprocess.run([sys.executable, "-B", *a], capture_output=True, text=True, encoding="utf-8",
                              errors="replace", env=self.ambiente, timeout=300, input=entrata, cwd=str(self.home))

    def handoff(self, nome: str = "HANDOFF_2026-11-03_10-00.md") -> Path:
        f = self.cl / "data" / "handoffs" / "libro" / nome
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(VERDE, encoding="utf-8")
        return f

    def coda(self, *a: str) -> subprocess.CompletedProcess:
        return self.lancia(str(self.cl / "bin" / "fine-coda.py"), "--slug", "libro", "--trailer", "Prova: banco", *a)

    def contesto(self, *a: str, entrata: str | None = None) -> subprocess.CompletedProcess:
        return self.lancia(str(self.cl / "bin" / "arturo"), "contesto", *a, entrata=entrata)

    def nel_remoto(self) -> list:
        return self.git(self.remoto, "ls-tree", "-r", "--name-only", "main").split()


def rt01(lab: Lab):
    for g in range(1, 7):
        lab.handoff(f"HANDOFF_2026-10-0{g}_10-00.md")
    lab.git(lab.cl, "add", "-f", "data/handoffs")
    lab.git(lab.cl, "commit", "-q", "-m", "handoff")
    cartella = lab.cl / "data" / "handoffs" / "libro"
    # il dry-run della FASE 6 c'è: senza --leggero il primo handoff uscirebbe
    lab.lancia(str(lab.cl / "bin" / "handoff-retention.py"), "libro", "--radice", str(cartella.parent))
    r = lab.coda("--handoff", str(cartella / "HANDOFF_2026-10-06_10-00.md"), "--leggero")
    resta = (cartella / "HANDOFF_2026-10-01_10-00.md").exists()
    segno = (cartella / SEGNO).exists()
    if r.returncode != 0 or not resta or segno or "retention: al fine completo" not in r.stdout \
            or "retention ok" in r.stdout:
        return (f"rc={r.returncode} l'handoff fuori dal keep resta={resta} segno={segno} "
                f"{(r.stdout + r.stderr).strip()[-200:]!r}")


def rt02(lab: Lab):
    oggi = {date.today().isoformat()}
    solo_sync = lab.coda()
    segni = sorted(p.relative_to(lab.cl).as_posix() for p in lab.cl.rglob(SEGNO))
    if solo_sync.returncode != 0 or segni:
        return f"solo sync: rc={solo_sync.returncode} segni {segni} {solo_sync.stdout.strip()[-160:]!r}"
    r = lab.coda("--handoff", str(lab.handoff()))
    oggi.add(date.today().isoformat())
    f = lab.cl / "data" / "handoffs" / "libro" / SEGNO
    testo = f.read_text(encoding="utf-8") if f.exists() else None
    nel_commit = set(lab.git(lab.cl, "show", "--name-only", "--format=", "HEAD").split())
    attesi = {"data/handoffs/libro/HANDOFF_2026-11-03_10-00.md", f"data/handoffs/libro/{SEGNO}"}
    indice = lab.cl / "data" / "handoffs" / "INDEX.md"
    nell_indice = indice.exists() and SEGNO in indice.read_text(encoding="utf-8")
    if r.returncode != 0 or testo not in {f"{g}\n" for g in oggi} or not attesi <= nel_commit \
            or f"data/handoffs/libro/{SEGNO}" not in lab.nel_remoto() or nell_indice:
        return (f"rc={r.returncode} segno={testo!r} mancano nel commit {sorted(attesi - nel_commit)} "
                f"nell'indice={nell_indice} {(r.stdout + r.stderr).strip()[-200:]!r}")


def rt03(lab: Lab):
    lab.handoff()
    r = lab.contesto("libro", "--", "--rotazione", "scrivere", "i", "test")
    righe = r.stdout.splitlines()
    if r.returncode != 0 or "compito: scrivere i test" not in righe or not any(
            x.startswith("rotazione: sì") for x in righe):
        return f"rc={r.returncode} {r.stdout[:300]!r} {r.stderr[-160:]!r}"


def rt04(lab: Lab):
    lab.handoff()
    r = lab.contesto("libro", "--", "scrivere", "i", "test")
    righe = r.stdout.splitlines()
    if r.returncode != 0 or "compito: scrivere i test" not in righe or any(x.startswith("rotazione:") for x in righe):
        return f"rc={r.returncode} {r.stdout[:300]!r} {r.stderr[-160:]!r}"


def rt05(lab: Lab):
    lab.handoff()
    # commands/inizio.md passa $ARGUMENTS su stdin, fra due righe ARGOMENTI
    r = lab.contesto("--stdin", entrata="libro -- --rotazione scrivere i test\n")
    righe = r.stdout.splitlines()
    if r.returncode != 0 or "PROGETTO libro" not in righe or "compito: scrivere i test" not in righe \
            or not any(x.startswith("rotazione: sì") for x in righe):
        return f"rc={r.returncode} {r.stdout[:300]!r} {r.stderr[-160:]!r}"


def rt06(lab: Lab):
    lab.handoff()
    r = lab.contesto("--stdin", entrata="libro --rotazione scrivere i test\n")
    if r.returncode != 3 or "opzione sconosciuta: --rotazione" not in r.stderr or "rotazione: sì" in r.stdout:
        return f"rc={r.returncode} {r.stdout[:200]!r} {r.stderr[-160:]!r}"


PROVE = {"RT01": rt01, "RT02": rt02, "RT03": rt03, "RT04": rt04, "RT05": rt05, "RT06": rt06}


def prova(repo: Path, ref: str | None) -> list:
    assert list(PROVE) == CASI, f"casi {list(PROVE)} diversi dall'elenco {CASI}"
    rossi = []
    for codice, fn in PROVE.items():
        with tempfile.TemporaryDirectory(prefix="arturo-rt-") as tmp:
            try:
                lab = Lab(repo, ref, Path(tmp))
                esito = fn(lab) if (lab.cl / "bin" / "fine-coda.py").exists() else "bin/fine-coda.py assente"
            except (RuntimeError, OSError, ValueError, subprocess.SubprocessError) as e:
                esito = f"eccezione {e}"
        if esito:
            rossi.append(f"{codice} {esito}")
    return rossi


def avvelena(repo: Path) -> int:
    esiti = []
    for casi, rel, giusto, rotto in VELENI:
        with tempfile.TemporaryDirectory(prefix="arturo-rt-veleno-") as tmp:
            copia = Path(tmp) / "repo"
            for p in PERCORSI:
                if (repo / p).is_dir():
                    shutil.copytree(str(repo / p), str(copia / p), ignore=shutil.ignore_patterns("__pycache__", "*.local"))
                else:
                    (copia / p).parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(str(repo / p), str(copia / p))
            testo = (copia / rel).read_text(encoding="utf-8")
            assert testo.count(giusto) == 1, f"veleno {'+'.join(casi)}: il testo da rompere non c'è più in {rel}"
            (copia / rel).write_text(testo.replace(giusto, rotto), encoding="utf-8")
            rossi = prova(copia, None)
            codici = [r.split()[0] for r in rossi]
            mancano = [c for c in casi if c not in codici]
            if mancano:
                print(f"VELENO {'+'.join(casi)} NON ATTACCA: rossi {codici}")
                print("VELENI KO: una copia rotta passa il banco")
                return 1
            for c in casi:
                print(f"VELENO {c} ROSSO: {next(r for r in rossi if r.startswith(c))[:140]}")
                esiti.append(c)
    print(f"VELENI_ROSSI={','.join(esiti)} veleni={len(VELENI)}")
    print("VELENI OK: ogni copia rotta fa rosso il banco col motivo atteso")
    return 0


def main() -> int:
    for flusso in (sys.stdout, sys.stderr):  # su Windows la pipe è in cp1252
        if hasattr(flusso, "reconfigure"):
            flusso.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument("--baseline-ref")
    parser.add_argument("--avvelena", action="store_true")
    argomenti = parser.parse_args()
    repo = Path(argomenti.repo).resolve()
    if argomenti.avvelena:
        return avvelena(repo)
    rossi = prova(repo, argomenti.baseline_ref)
    if argomenti.baseline_ref:
        for r in rossi:
            print("ROSSO SULLA BASE", r[:200])
        codici = [r.split()[0] for r in rossi]
        assert codici == DISCRIMINANTI, f"baseline non discriminante: rossi {codici}, attesi {DISCRIMINANTI}"
        print(f"BASELINE_DISCRIMINANTE={','.join(codici)}")
        return 0
    for r in rossi:
        print("ROSSO", r)
    print(f"rotazione della sessione: {len(CASI) - len(rossi)}/{len(CASI)} casi verdi")
    print("BANCO ROSSO" if rossi else "BANCO VERDE")
    return 1 if rossi else 0


if __name__ == "__main__":
    sys.exit(main())
