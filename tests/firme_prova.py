"""Rilasci firmati per i banchi che pubblicano un Arturo finto (17/10/2026, #3504).

Da quando /aggiorna applica solo l'ultimo tag firmato, un Arturo pubblicato nei banchi deve firmare i
suoi rilasci come quello vero. Qui una chiave di prova generata al volo, la sua riga in
firme/rilasci.allowed_signers del seme, e un hook post-receive nel repository pubblicato che firma
un tag a ogni push su main: ogni pubblicazione di un banco diventa un rilascio firmato.

  chiave = semina(seme, repo, cartella)   prima del primo commit del seme
  arma(pubblicato, chiave, env)           dopo il clone --bare, prima dei clone di chi usa e di chi scrive
"""
from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path
from typing import Dict, Optional

HOOK = """#!/bin/sh
# Ogni push su main diventa un rilascio firmato con la chiave di prova del banco.
while read vecchio nuovo ref; do
  [ "$ref" = refs/heads/main ] || continue
  case "$nuovo" in 0000000000000000000000000000000000000000) continue ;; esac
  n=$(( $(cat "$GIT_DIR/firme-prova" 2>/dev/null || echo 0) + 1 ))
  echo "$n" > "$GIT_DIR/firme-prova"
  git -c gpg.format=ssh -c user.signingkey='@CHIAVE@' -c user.name=prova -c user.email=prova@example.invalid \\
    tag -s "$(printf 'vprova-%04d' "$n")" -m rilascio "$nuovo" >/dev/null 2>&1 || echo "firma di prova non riuscita" >&2
done
"""


def semina(seme: Path, repo: Path, cartella: Path) -> Path:
    """La chiave di prova, la sua riga in firme/ e bin/aggiornamenti.py (la verifica di /aggiorna) nel seme."""
    cartella.mkdir(parents=True, exist_ok=True)
    chiave = cartella / "rilasci"
    subprocess.run(["ssh-keygen", "-q", "-t", "ed25519", "-N", "", "-C", "prova", "-f", str(chiave)], check=True,
                   capture_output=True, timeout=60)
    pub = Path(str(chiave) + ".pub").read_text(encoding="utf-8").split()
    (seme / "firme").mkdir(parents=True, exist_ok=True)
    (seme / "firme" / "rilasci.allowed_signers").write_text(f'rilasci@arturo namespaces="git" {pub[0]} {pub[1]}\n',
                                                             encoding="utf-8")
    verifica = repo / "bin" / "aggiornamenti.py"
    if verifica.exists():  # sulle basi di prima del 16/10/2026 non c'è: /aggiorna applicava main
        (seme / "bin").mkdir(parents=True, exist_ok=True)
        shutil.copy(str(verifica), str(seme / "bin" / "aggiornamenti.py"))
    return chiave


def arma(pubblicato: Path, chiave: Path, env: Optional[Dict[str, str]] = None) -> None:
    """L'hook che firma ogni push su main, e la firma del main già pubblicato."""
    hook = pubblicato / "hooks" / "post-receive"
    hook.parent.mkdir(parents=True, exist_ok=True)
    hook.write_text(HOOK.replace("@CHIAVE@", str(chiave).replace("\\", "/")), encoding="utf-8", newline="\n")
    hook.chmod(0o755)
    (pubblicato / "firme-prova").write_text("1\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(pubblicato), "-c", "gpg.format=ssh", "-c", f"user.signingkey={chiave}",
                    "-c", "user.name=prova", "-c", "user.email=prova@example.invalid",
                    "tag", "-s", "vprova-0001", "-m", "rilascio", "main"],
                   check=True, capture_output=True, timeout=60, env=dict(env or os.environ))
