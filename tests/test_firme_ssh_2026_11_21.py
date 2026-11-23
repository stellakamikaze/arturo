#!/usr/bin/env python3
"""FS01-FS02: la verifica dei rilasci accetta solo firme SSH (21/11/2026, #6258).

La revisione di sicurezza del 20/11 (rilievo S1) ha provato che `git -c gpg.format=ssh verify-tag` non fissa il
formato: git sceglie il programma dalla firma scritta nel tag. Un tag firmato PGP passa da gpg e dal portachiavi
della persona, e firme/rilasci.allowed_signers non conta più. Basta una chiave PGP dell'attaccante nel portachiavi
della vittima. Adesso verifica_tag vuole che il blocco di firma del tag sia SSH, prima di chiamare verify-tag.

Ogni caso crea un repository con un portachiavi gpg suo (GNUPGHOME in una cartella temporanea) e una chiave SSH di
prova scritta nel file delle firme. Niente rete, niente portachiavi vero della persona.

FS01 un tag firmato SSH con la chiave del file passa; un tag firmato PGP con una chiave del portachiavi no, ed è
     una possibile compromissione.
FS02 un tag con la riga "-----BEGIN SSH SIGNATURE-----" nel messaggio e la firma PGP in fondo non passa: git legge
     la firma dall'ultima riga "-----BEGIN …", e l'ultima è PGP.

Sulla base ff920f0 ogni controllo deve fallire con un AssertionError che comincia con il suo codice.
"""
from __future__ import annotations

import argparse
import contextlib
import importlib.util
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Iterator, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent))
from salti_windows import cartella_prova, dichiara  # noqa: E402

GPG = shutil.which("gpg")


def percorso_gpg(cartella: Path) -> str:
    """Il gpg di Git per Windows è un programma msys: C:\\... con le barre rovesciate gli sembra un percorso
    relativo e ci attacca davanti la cartella corrente. C:/... lo legge giusto (#6455)."""
    return cartella.as_posix() if os.name == "nt" else str(cartella)


class Lab:
    def __init__(self, repo: Path, base: Path, gnupg: Path):
        self.base = base
        self.env = dict(os.environ, GNUPGHOME=percorso_gpg(gnupg), GIT_CONFIG_GLOBAL=str(base / "gitconfig"),
                        GIT_CONFIG_NOSYSTEM="1", GIT_CEILING_DIRECTORIES=str(base), GIT_TERMINAL_PROMPT="0",
                        GIT_AUTHOR_NAME="a", GIT_AUTHOR_EMAIL="a@example.invalid", GIT_COMMITTER_NAME="a",
                        GIT_COMMITTER_EMAIL="a@example.invalid", PYTHONDONTWRITEBYTECODE="1")
        (base / "gitconfig").write_text("[core]\n\tautocrlf = false\n[init]\n\tdefaultBranch = main\n", encoding="utf-8")
        self.esegui(GPG, "--batch", "--passphrase", "", "--quick-gen-key", "attaccante@example.invalid", "ed25519",
                    "sign", "never")
        righe = self.esegui(GPG, "--list-secret-keys", "--with-colons").splitlines()
        self.pgp = [r.split(":")[9] for r in righe if r.startswith("fpr:")][0]
        self.ssh = base / "rilasci"
        self.esegui("ssh-keygen", "-q", "-t", "ed25519", "-N", "", "-C", "prova", "-f", str(self.ssh))
        pub = Path(str(self.ssh) + ".pub").read_text(encoding="utf-8").split()
        self.firme = base / "rilasci.allowed_signers"
        self.firme.write_text(f'rilasci@arturo namespaces="git" {pub[0]} {pub[1]}\n', encoding="utf-8")
        self.r = base / "r"
        self.esegui("git", "init", "-q", str(self.r))
        (self.r / "f").write_text("x\n", encoding="utf-8")
        self.git("add", "f")
        self.git("commit", "-q", "-m", "c")
        self.modulo = carica(repo)

    def esegui(self, *comando: str) -> str:
        r = subprocess.run(list(comando), env=self.env, capture_output=True, text=True, timeout=60)
        if r.returncode:
            raise RuntimeError(f"{' '.join(comando[:3])}: {r.stderr.strip()}")
        return r.stdout

    def git(self, *argomenti: str) -> str:
        return self.esegui("git", "-C", str(self.r), *argomenti)

    def tag_ssh(self, tag: str) -> None:
        self.git("-c", "gpg.format=ssh", "-c", f"user.signingkey={self.ssh}", "tag", "-s", tag, "-m", tag)

    def tag_pgp(self, tag: str, messaggio: str = "") -> None:
        self.git("-c", f"user.signingkey={self.pgp}", "tag", "-s", tag, "-m", messaggio or tag)

    def verifica(self, tag: str) -> Tuple[str, bool]:
        vecchio = dict(os.environ)
        os.environ.clear()
        os.environ.update(self.env)
        try:
            return self.modulo.verifica_tag(self.r, tag, self.firme)
        finally:
            os.environ.clear()
            os.environ.update(vecchio)


def carica(repo: Path):
    """bin/aggiornamenti.py della copia in prova, non quello installato."""
    spec = importlib.util.spec_from_file_location("aggiornamenti_in_prova", str(repo / "bin" / "aggiornamenti.py"))
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


@contextlib.contextmanager
def lab(repo: Path) -> Iterator[Lab]:
    # Il portachiavi in una cartella corta: gpg-agent apre lì il suo socket, e un percorso oltre i 104 caratteri
    # non si apre ("File name too long"). Nel gate TMPDIR è già lungo: il portachiavi va in /tmp, se c'è.
    gnupg = Path(tempfile.mkdtemp(prefix="fsg", dir="/tmp" if os.path.isdir("/tmp") else None))
    gnupg.chmod(0o700)
    env = dict(os.environ, GNUPGHOME=percorso_gpg(gnupg))
    try:
        with cartella_prova() as d:
            yield Lab(repo, Path(d), gnupg)
    finally:
        subprocess.run(["gpgconf", "--kill", "all"], env=env, capture_output=True, timeout=30)
        shutil.rmtree(str(gnupg), ignore_errors=True)


def test_fs01(repo: Path) -> None:
    with lab(repo) as l:
        l.tag_ssh("v1.0.0")
        motivo, compromesso = l.verifica("v1.0.0")
        assert motivo == "" and not compromesso, f"FS01 il tag firmato SSH con la chiave del file non passa: {motivo!r}"
        l.tag_pgp("v1.0.1")
        motivo, compromesso = l.verifica("v1.0.1")
        assert motivo and compromesso and "non ha la firma di Arturo" in motivo, \
            f"FS01 un tag firmato PGP con una chiave del portachiavi passa la verifica: {motivo!r} {compromesso!r}"


def test_fs02(repo: Path) -> None:
    with lab(repo) as l:
        l.tag_pgp("v1.0.2", "rilascio\n\n-----BEGIN SSH SIGNATURE-----\nfinta\n-----END SSH SIGNATURE-----\n")
        motivo, compromesso = l.verifica("v1.0.2")
        assert motivo and compromesso, \
            f"FS02 un tag PGP con una finta firma SSH nel messaggio passa la verifica: {motivo!r} {compromesso!r}"


TESTS = {"FS01": test_fs01, "FS02": test_fs02}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--baseline-ref")
    args = parser.parse_args()
    repo = args.repo.resolve()
    assert shutil.which("ssh-keygen"), "ssh-keygen mancante: le firme di prova non si generano"
    if not GPG:
        for nome in TESTS:
            dichiara(nome, "gpg mancante: senza gpg un tag firmato PGP non si verifica, e l'aggiramento non c'è")
        return 0
    if args.baseline_ref:
        rossi, altro = [], []
        for nome, test in TESTS.items():
            try:
                test(repo)
            except AssertionError as e:
                (rossi if str(e).startswith(nome) else altro).append(f"{nome}: {e}")
            except Exception as e:  # noqa: BLE001
                altro.append(f"{nome}: {type(e).__name__} {e}")
        assert not altro and len(rossi) == len(TESTS), \
            "baseline non discriminante: ogni controllo deve fallire col suo codice.\n" + "\n".join(altro + rossi)
        print(f"BASELINE_DISCRIMINANTE={','.join(r.split(':')[0] for r in rossi)}")
        return 0
    for test in TESTS.values():
        test(repo)
    print(f"PASS {','.join(TESTS)} controlli={len(TESTS)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
