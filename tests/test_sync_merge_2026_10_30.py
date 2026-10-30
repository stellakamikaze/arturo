#!/usr/bin/env python3
"""SM01: il sync fra macchine non appiattisce un aggiornamento di Arturo non ancora pushato.

Una macchina unisce un rilascio di Arturo con un merge e non fa ancora push; intanto un'altra macchina
pusha sul repository privato. Il sync di /inizio (aggiorna-applica.sh sync) fino al 30/10/2026 faceva
un rebase semplice: i commit di Arturo diventavano copie con hash nuovi, e il commit di Arturo non era
più un antenato della config. Con --rebase-merges il merge si rifà (migrazione della config di
Federico, #4291).

Sulla base 749e18d SM01 è rosso.
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
from pathlib import Path

CASI = ["SM01"]
BASH = shutil.which("bash") or "bash"


def git(cartella: Path, *argomenti: str) -> str:
    p = subprocess.run(["git", "-C", str(cartella), "-c", "user.name=Prova", "-c", "user.email=p@example.com",
                        "-c", "commit.gpgsign=false", *argomenti],
                       capture_output=True, text=True, encoding="utf-8", timeout=60)
    if p.returncode:
        raise RuntimeError(f"git {' '.join(argomenti)}: {p.stderr.strip()}")
    return p.stdout.strip()


def prova(repo: Path, applica: str) -> list[str]:
    with tempfile.TemporaryDirectory() as tmp:
        t = Path(tmp)
        arturo, privato, casa = t / "arturo", t / "privato.git", t / "home" / ".claude"
        arturo.mkdir()
        dati = subprocess.run(["git", "-C", str(repo), "archive", "HEAD"], capture_output=True, check=True).stdout
        with tarfile.open(fileobj=io.BytesIO(dati)) as archivio:
            if hasattr(tarfile, "data_filter"):
                archivio.extractall(arturo, filter="data")
            else:
                archivio.extractall(arturo)
        (arturo / "bin" / "aggiorna-applica.sh").write_text(applica, encoding="utf-8", newline="\n")
        git(arturo, "init", "-q", "-b", "main")
        git(arturo, "add", "-A")
        git(arturo, "commit", "-q", "-m", "rilascio A0")
        git(t, "clone", "-q", "--bare", str(arturo), str(privato))
        git(t, "clone", "-q", str(privato), str(casa))
        git(casa, "remote", "add", "upstream", str(arturo))
        (casa / "personale.md").write_text("mio\n", encoding="utf-8")
        git(casa, "add", "personale.md")
        git(casa, "commit", "-q", "-m", "U1 di Federico")
        git(casa, "push", "-q", "origin", "main")
        # Arturo pubblica A1; questa macchina lo unisce con un merge e non pusha.
        (arturo / "NOVITA-PROVA.md").write_text("A1\n", encoding="utf-8")
        git(arturo, "add", "NOVITA-PROVA.md")
        git(arturo, "commit", "-q", "-m", "rilascio A1")
        a1 = git(arturo, "rev-parse", "HEAD")
        git(casa, "fetch", "-q", "upstream")
        git(casa, "merge", "-q", "--no-edit", "upstream/main")
        # Un'altra macchina pusha U2 sul privato.
        altra = t / "altra"
        git(t, "clone", "-q", str(privato), str(altra))
        (altra / "altra.md").write_text("U2\n", encoding="utf-8")
        git(altra, "add", "altra.md")
        git(altra, "commit", "-q", "-m", "U2 dall'altra macchina")
        git(altra, "push", "-q", "origin", "main")
        git(casa, "fetch", "-q", "origin")
        env = {**os.environ, "HOME": str(casa.parent), "USERPROFILE": str(casa.parent), "ARTURO_TELEMETRIA": "0",
               "GIT_AUTHOR_NAME": "Prova", "GIT_AUTHOR_EMAIL": "p@example.com",
               "GIT_COMMITTER_NAME": "Prova", "GIT_COMMITTER_EMAIL": "p@example.com"}
        p = subprocess.run([BASH, str(casa / "bin" / "aggiorna-applica.sh"), str(casa), "sync", "origin/main"],
                           capture_output=True, text=True, encoding="utf-8", errors="replace", env=env, timeout=300)
        antenato = subprocess.run(["git", "-C", str(casa), "merge-base", "--is-ancestor", a1, "HEAD"]).returncode == 0
        u2 = subprocess.run(["git", "-C", str(casa), "merge-base", "--is-ancestor", "origin/main", "HEAD"]).returncode == 0
        if not (p.stdout.startswith("APPLICATO") or "\nAPPLICATO" in p.stdout) or not antenato or not u2:
            ultima = (p.stdout.strip().splitlines() or [""])[-1]
            return [f"SM01 sync: esito {ultima!r}, A1 antenato={antenato}, U2 dentro={u2}"]
    return []


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument("--baseline-ref")
    argomenti = parser.parse_args()
    repo = Path(argomenti.repo)
    if argomenti.baseline_ref:
        applica = subprocess.run(["git", "-C", str(repo), "show", f"{argomenti.baseline_ref}:bin/aggiorna-applica.sh"],
                                 capture_output=True, text=True, encoding="utf-8", check=True).stdout
    else:
        applica = (repo / "bin" / "aggiorna-applica.sh").read_text(encoding="utf-8")
    rossi = prova(repo, applica)
    if argomenti.baseline_ref:
        codici = [r.split()[0] for r in rossi]
        assert codici == CASI, f"baseline non discriminante: rossi {codici}, attesi {CASI}"
        print(f"BASELINE_DISCRIMINANTE={','.join(codici)}")
        return 0
    for r in rossi:
        print("ROSSO", r)
    print(f"sync con merge: {len(CASI) - len(rossi)}/{len(CASI)} casi verdi")
    return 1 if rossi else 0


if __name__ == "__main__":
    sys.exit(main())
