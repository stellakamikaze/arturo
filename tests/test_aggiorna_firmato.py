#!/usr/bin/env python3
"""AF01-AF06: /aggiorna applica solo l'ultimo tag firmato, mai main (17/10/2026, #3504).

Prima /aggiorna applicava `main` e ne leggeva `bin/aggiorna-applica.sh`, senza guardare la firma.
L'avvio, la barra in basso e /inizio mandavano a /aggiorna proprio quando il rilascio non era
firmato: chi aveva accesso al repository bastava un push per far girare codice sui computer degli
altri, dopo un sì dato a una procedura che sembrava quella di sempre.

Ogni caso costruisce un Arturo pubblicato (bare), chi ne firma i rilasci con una chiave di prova
generata qui, e una HOME con ~/.claude clonata che si fida solo di quella chiave. I blocchi di
/aggiorna, /inizio e del README girano in una shell nuova ciascuno, come le chiamate Bash di Claude.
Niente rete.

AF01 un tag non firmato più nuovo: il Passo 1 dice «possibile compromissione», il Passo 3 non applica.
AF02 un tag firmato e un main avanti con la procedura avvelenata: si applica il tag, con la procedura
     del tag, e i commit di main dopo il tag non arrivano.
AF03 con un repository personale come origin, Arturo arriva solo da tag firmati di upstream: un tag
     firmato si applica con un merge, uno firmato da un'altra chiave no.
AF04 avvio, barra in basso, /inizio e /novita: con un tag non firmato dicono «possibile
     compromissione: non aggiornare, segnala a chi mantiene Arturo», e non mandano a /aggiorna.
AF05 i comandi a mano del README non applicano un tag non firmato.
AF06 un tag firmato pubblicato con un altro nome (lo stesso oggetto sotto un nome nuovo) non passa:
     git describe lo dice col nome scritto dentro più un suffisso, e verify-tag lo rifiuta.
AF07 una copia senza bin/aggiornamenti.py (la verifica) non manda a /aggiorna i commit di main.
AF08 un ssh-keygen senza -Y (OpenSSH prima della 8.2): «FIRMA NON VERIFICABILE», niente si applica, e
     nessuno parla di compromissione.
AF09 un rilascio vecchio senza firma, già installato: `firmato` lo stampa e /inizio non dà l'allarme.

Sulla base 93f323e ogni controllo deve fallire con un AssertionError che comincia con il suo codice.
AF08 e AF09 sulla base 89c7781.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import List

BASH = shutil.which("bash") or "bash"
NODE = shutil.which("node") or "node"
FRASE = "possibile compromissione: non aggiornare, segnala a chi mantiene arturo"
GIT_ENV = {"GIT_AUTHOR_NAME": "a", "GIT_AUTHOR_EMAIL": "a@example.invalid", "GIT_COMMITTER_NAME": "a",
           "GIT_COMMITTER_EMAIL": "a@example.invalid", "GIT_TERMINAL_PROMPT": "0"}


def read(p: Path) -> str:
    return p.read_text(encoding="utf-8")


def blocchi(testo: str, titolo: str, codice: str) -> List[str]:
    """I blocchi ```bash dopo l'intestazione `titolo`, senza il rientro degli elenchi numerati."""
    assert titolo in testo, f"{codice} non trovo «{titolo}»"
    trovati = re.findall(r"```bash\n(.*?)```", testo[testo.index(titolo):], re.S)
    assert trovati, f"{codice} nessun blocco bash dopo «{titolo}»"
    return ["\n".join(r[3:] if r.startswith("   ") else r for r in b.splitlines()) for b in trovati]


class Lab:
    def __init__(self, repo: Path, base: Path):
        self.repo, self.base = repo, base
        self.home = base / "home"
        self.utente = self.home / ".claude"
        self.env = dict(os.environ, HOME=str(self.home), USERPROFILE=str(self.home), GIT_CONFIG_GLOBAL=str(base / "gitconfig"),
                        GIT_CONFIG_NOSYSTEM="1", GIT_CEILING_DIRECTORIES=str(base), ARTURO_TELEMETRIA="0",
                        ARTURO_ALTRE_SESSIONI="0", ARTURO_ATTESA_MAX="0", ARTURO_BANCHI_AVVIO="0",
                        PYTHONDONTWRITEBYTECODE="1", **GIT_ENV)
        for via in ("ARTURO_AGGIORNAMENTI", "ARTURO_RADICE", "CLAUDE_CONFIG_DIR"):
            self.env.pop(via, None)
        (base / "gitconfig").write_text("[core]\n\tautocrlf = false\n[init]\n\tdefaultBranch = main\n", encoding="utf-8")
        self.home.mkdir()
        chiavi = base / "chiavi"
        chiavi.mkdir()
        self.chiave, self.altra = chiavi / "rilasci", chiavi / "altra"
        for k in (self.chiave, self.altra):
            subprocess.run(["ssh-keygen", "-q", "-t", "ed25519", "-N", "", "-C", "prova", "-f", str(k)], check=True,
                           capture_output=True)
        seme = base / "seme"
        for parte in ("bin", "hooks", "firme"):
            (seme / parte).mkdir(parents=True)
        for f in ("bin/aggiorna-applica.sh", "bin/aggiornamenti.py", "hooks/controlla-config.py"):
            if (repo / f).exists():
                shutil.copy(str(repo / f), str(seme / f))
        pub = read(Path(str(self.chiave) + ".pub")).split()
        (seme / "firme" / "rilasci.allowed_signers").write_text(f'rilasci@arturo namespaces="git" {pub[0]} {pub[1]}\n',
                                                                 encoding="utf-8")
        (seme / "settings.json").write_text(json.dumps({"env": {"A": "1"}}, indent=2) + "\n", encoding="utf-8")
        (seme / "NOVITA.md").write_text("# Novita\n\n## 2026-01-01 — Prima\n", encoding="utf-8")
        (seme / ".gitignore").write_text("session-env/\ndata/\n", encoding="utf-8")
        self.git(base, "init", "-q", "-b", "main", str(seme))
        self.git(seme, "add", "-A")
        self.git(seme, "commit", "-q", "-m", "v1")
        self.git(seme, "-c", "gpg.format=ssh", "-c", f"user.signingkey={self.chiave}", "tag", "-s", "v2026-01-01", "-m", "v1")
        self.arturo = base / "arturo.git"
        self.git(base, "clone", "-q", "--bare", str(seme), str(self.arturo))
        self.git(base, "clone", "-q", str(self.arturo), str(self.utente))
        self.autore = base / "autore"
        self.git(base, "clone", "-q", str(self.arturo), str(self.autore))
        self.cwd = self.utente

    def git(self, cartella: Path, *argomenti: str) -> str:
        r = subprocess.run(["git", "-C", str(cartella), *argomenti], env=self.env, capture_output=True, text=True, timeout=60)
        if r.returncode:
            raise RuntimeError(f"git {' '.join(argomenti)}: {r.stderr.strip()}")
        return r.stdout.strip()

    def commit(self, file: str, testo: str) -> str:
        (self.autore / file).parent.mkdir(parents=True, exist_ok=True)
        (self.autore / file).write_text(testo, encoding="utf-8")
        self.git(self.autore, "add", "-A")
        self.git(self.autore, "commit", "-q", "-m", f"cambia {file}")
        return self.git(self.autore, "rev-parse", "HEAD")

    def tagga(self, tag: str, chiave: Path = None, firma: bool = True) -> None:
        if firma:
            self.git(self.autore, "-c", "gpg.format=ssh", "-c", f"user.signingkey={chiave or self.chiave}", "tag", "-s", tag, "-m", tag)
        else:
            self.git(self.autore, "tag", "-a", tag, "-m", tag)

    def pubblica(self) -> None:
        self.git(self.autore, "push", "-q", "--tags", "origin", "main")

    def lancia(self, script: str) -> str:
        """Un blocco in una shell nuova, come una chiamata Bash di Claude: la cartella resta, le variabili no."""
        traccia = self.base / "cwd"
        r = subprocess.run([BASH, "-c", f"trap '{{ pwd -W 2>/dev/null || pwd; }} > \"{traccia}\"' EXIT\n" + script],
                           cwd=str(self.cwd), env=self.env, capture_output=True, timeout=180)
        if traccia.exists():
            self.cwd = Path(read(traccia).strip())
        return (r.stdout + r.stderr).decode("utf-8", "replace")

    def passi(self, *titoli: str) -> str:
        testo = read(self.repo / "commands" / "aggiorna.md")
        return "".join(self.lancia(blocchi(testo, t, "AF")[0]) for t in titoli)

    def head(self) -> str:
        return self.git(self.utente, "rev-parse", "HEAD")

    def personale(self) -> None:
        """/setup FASE 7: origin diventa un repository della persona, Arturo resta come upstream."""
        p = self.base / "personale.git"
        self.git(self.base, "init", "-q", "--bare", "-b", "main", str(p))
        self.git(self.utente, "remote", "rename", "origin", "upstream")
        self.git(self.utente, "remote", "add", "origin", str(p))
        (self.utente / "mio.md").write_text("mio\n", encoding="utf-8")
        self.git(self.utente, "add", "mio.md")
        self.git(self.utente, "commit", "-q", "-m", "mio")
        self.git(self.utente, "push", "-q", "-u", "origin", "main")


def con_lab(repo: Path, prova) -> None:
    with tempfile.TemporaryDirectory() as d:
        prova(Lab(repo, Path(d)))


def test_af01(repo: Path) -> None:
    def prova(lab: Lab) -> None:
        prima = lab.head()
        lab.commit("hooks/nuova.py", "x = 1\n")
        lab.tagga("v2026-02-01", firma=False)
        lab.pubblica()
        uscita = lab.passi("## Passo 1", "## Passo 3")
        assert lab.head() == prima and not (lab.utente / "hooks" / "nuova.py").exists(), \
            f"AF01 /aggiorna applica un rilascio senza firma: {uscita[-300:]!r}"
        assert FRASE in uscita.lower() or "POSSIBILE COMPROMISSIONE" in uscita, \
            f"AF01 /aggiorna non dice che il rilascio senza firma è una possibile compromissione: {uscita[-300:]!r}"
    con_lab(repo, prova)


def test_af02(repo: Path) -> None:
    def prova(lab: Lab) -> None:
        firmato = lab.commit("hooks/nuova.py", "x = 1\n")
        lab.tagga("v2026-02-01")
        veleno = lab.base / "VELENO"
        procedura = read(lab.autore / "bin" / "aggiorna-applica.sh")
        lab.commit("bin/aggiorna-applica.sh", procedura.replace("set -u\n", f"set -u\ntouch '{veleno}'\n", 1))
        lab.commit("hooks/dopo.py", "y = 1\n")
        lab.pubblica()
        uscita = lab.passi("## Passo 1", "## Passo 3")
        assert not veleno.exists(), f"AF02 /aggiorna lancia la procedura di main, non quella del tag firmato: {uscita[-300:]!r}"
        assert lab.head() == firmato and not (lab.utente / "hooks" / "dopo.py").exists(), \
            f"AF02 /aggiorna non applica il tag firmato, o applica anche i commit di main dopo il tag: {uscita[-300:]!r}"
    con_lab(repo, prova)


def test_af03(repo: Path) -> None:
    def prova(lab: Lab) -> None:
        lab.personale()
        firmato = lab.commit("hooks/nuova.py", "x = 1\n")
        lab.tagga("v2026-02-01")
        lab.commit("hooks/dopo.py", "y = 1\n")
        lab.pubblica()
        uscita = lab.passi("## Passo 1", "## Passo 3")
        assert lab.git(lab.utente, "merge-base", "--is-ancestor", firmato, "HEAD") == "" and \
            not (lab.utente / "hooks" / "dopo.py").exists() and (lab.utente / "mio.md").exists(), \
            f"AF03 con un repository personale /aggiorna non applica il solo tag firmato di upstream: {uscita[-300:]!r}"
        prima = lab.head()
        lab.commit("hooks/altra.py", "z = 1\n")
        lab.tagga("v2026-03-01", chiave=lab.altra)
        lab.pubblica()
        uscita = lab.passi("## Passo 1", "## Passo 3")
        assert lab.head() == prima and not (lab.utente / "hooks" / "altra.py").exists(), \
            f"AF03 un tag di upstream firmato da un'altra chiave si applica: {uscita[-300:]!r}"
    con_lab(repo, prova)


def test_af04(repo: Path) -> None:
    def prova(lab: Lab) -> None:
        lab.personale()  # /inizio lavora sul repository personale e guarda upstream per Arturo
        lab.commit("hooks/nuova.py", "x = 1\n")
        lab.tagga("v2026-02-01", firma=False)
        lab.pubblica()
        lab.git(lab.utente, "fetch", "-q", "--tags", "upstream", "main")
        r = subprocess.run([sys.executable, "-B", str(lab.utente / "bin" / "aggiornamenti.py"), "stato"], env=lab.env,
                           capture_output=True, text=True, encoding="utf-8", timeout=60)
        avvio = r.stdout.lower()
        assert FRASE in avvio and "scaricalo con /aggiorna" not in avvio, \
            f"AF04 l'avvio manda a /aggiorna un rilascio senza firma: {r.stdout!r}"
        entrata = json.dumps({"model": {"display_name": "Opus"}, "workspace": {"current_dir": str(lab.home)}})
        (lab.utente / "session-env" / "aggiornamento-controllo").write_text("", encoding="utf-8")  # niente controllo staccato
        barra = subprocess.run([NODE, str(repo / "hooks" / "statusline.js")], input=entrata, env=lab.env,
                               capture_output=True, text=True, encoding="utf-8", timeout=30).stdout
        assert FRASE in barra.lower() and "serve /aggiorna" not in barra, f"AF04 la barra manda a /aggiorna: {barra!r}"
        inizio = lab.lancia(blocchi(read(repo / "commands" / "inizio.md"), "## FASE 0", "AF04")[0])
        assert FRASE in inizio.lower() and "subito con /aggiorna" not in inizio, \
            f"AF04 /inizio manda a /aggiorna un rilascio senza firma: {inizio[-400:]!r}"
        novita = lab.lancia(blocchi(read(repo / "commands" / "novita.md"), "## Passo 0", "AF04")[0])
        assert "POSSIBILE COMPROMISSIONE" in novita and "non ancora applicati: 1" not in novita, \
            f"AF04 /novita conta come aggiornamento un rilascio senza firma: {novita[-300:]!r}"
    con_lab(repo, prova)


def test_af05(repo: Path) -> None:
    def prova(lab: Lab) -> None:
        prima = lab.head()
        lab.commit("hooks/nuova.py", "x = 1\n")
        lab.tagga("v2026-02-01", firma=False)
        lab.pubblica()
        manuale = blocchi(read(repo / "README.md"), "## Aggiornare Arturo", "AF05")[0].replace("/tmp/", f"{lab.base}/")
        uscita = lab.lancia(manuale)
        assert lab.head() == prima and not (lab.utente / "hooks" / "nuova.py").exists(), \
            f"AF05 i comandi a mano del README applicano un rilascio senza firma: {uscita[-300:]!r}"
    con_lab(repo, prova)


def test_af06(repo: Path) -> None:
    def prova(lab: Lab) -> None:
        prima = lab.head()
        lab.commit("hooks/nuova.py", "x = 1\n")
        lab.tagga("v2026-02-01")
        # Lo stesso oggetto firmato, pubblicato solo sotto un altro nome.
        lab.git(lab.autore, "push", "-q", "origin", "main", "refs/tags/v2026-02-01:refs/tags/v2026-03-01")
        uscita = lab.passi("## Passo 1", "## Passo 3")
        assert lab.head() == prima, f"AF06 un tag firmato pubblicato con un altro nome si applica: {uscita[-300:]!r}"
    con_lab(repo, prova)


def test_af07(repo: Path) -> None:
    def prova(lab: Lab) -> None:
        lab.commit("hooks/nuova.py", "x = 1\n")
        lab.pubblica()
        lab.git(lab.utente, "fetch", "-q", "--tags", "origin", "main")
        (lab.utente / "bin" / "aggiornamenti.py").unlink()  # una copia senza la verifica della firma
        r = subprocess.run([BASH, str(repo / "hooks" / "session-start.sh")], input="{}", env=lab.env, cwd=str(lab.home),
                           capture_output=True, text=True, encoding="utf-8", timeout=120)
        assert "scaricalo con /aggiorna" not in r.stdout and "bin/aggiornamenti.py" in r.stdout, \
            f"AF07 senza la verifica della firma l'avvio manda a /aggiorna i commit di main: {r.stdout[-400:]!r}"
    con_lab(repo, prova)


def firmato(lab: Lab) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, "-B", str(lab.utente / "bin" / "aggiornamenti.py"), "firmato"], env=lab.env,
                          cwd=str(lab.utente), capture_output=True, text=True, encoding="utf-8", timeout=60)


def test_af08(repo: Path) -> None:
    def prova(lab: Lab) -> None:
        prima = lab.head()
        lab.commit("hooks/nuova.py", "x = 1\n")
        lab.tagga("v2026-02-01")
        lab.pubblica()
        # Dopo la firma: un ssh-keygen prima della 8.2, senza -Y, come il macOS di sistema fino a Big Sur.
        vecchio = lab.base / "ssh-keygen-vecchio"
        vecchio.write_text("#!/bin/sh\necho 'unknown option -- Y' >&2\nexit 1\n", encoding="utf-8")
        vecchio.chmod(0o755)
        with open(lab.base / "gitconfig", "a", encoding="utf-8") as f:
            f.write(f"[gpg \"ssh\"]\n\tprogram = {vecchio.as_posix()}\n")
        lab.git(lab.utente, "fetch", "-q", "--tags", "origin", "main")
        r = firmato(lab)
        assert r.returncode == 4 and "FIRMA NON VERIFICABILE" in r.stderr and "COMPROMISSIONE" not in r.stderr, \
            f"AF08 una verifica che non parte è data per compromissione: rc={r.returncode} {r.stderr!r}"
        avvio = subprocess.run([sys.executable, "-B", str(lab.utente / "bin" / "aggiornamenti.py"), "stato"], env=lab.env,
                               capture_output=True, text=True, encoding="utf-8", timeout=60).stdout
        assert "non sa controllare la firma" in avvio and FRASE not in avvio.lower(), \
            f"AF08 l'avvio parla di compromissione su un ssh-keygen vecchio: {avvio!r}"
        uscita = lab.passi("## Passo 1", "## Passo 3")
        assert lab.head() == prima and FRASE not in uscita.lower(), \
            f"AF08 /aggiorna applica senza verifica, o parla di compromissione: {uscita[-300:]!r}"
    con_lab(repo, prova)


def test_af09(repo: Path) -> None:
    def prova(lab: Lab) -> None:
        # Un rilascio vecchio, senza firma, già installato: il fetch di oggi non è arrivato (offline).
        lab.commit("hooks/nuova.py", "x = 1\n")
        lab.tagga("v2026-02-01", firma=False)
        lab.pubblica()
        lab.git(lab.utente, "pull", "-q", "--ff-only", "--tags", "origin", "main")
        r = firmato(lab)
        assert r.returncode == 0 and r.stdout.strip() == "v2026-02-01" and "COMPROMISSIONE" not in r.stderr, \
            f"AF09 un rilascio già installato dà l'allarme: rc={r.returncode} {r.stderr!r}"
        inizio = lab.lancia(blocchi(read(repo / "commands" / "inizio.md"), "## FASE 0", "AF09")[0])
        assert FRASE not in inizio.lower(), f"AF09 /inizio dà l'allarme su un rilascio già installato: {inizio[-300:]!r}"
    con_lab(repo, prova)


TESTS = {"AF01": test_af01, "AF02": test_af02, "AF03": test_af03, "AF04": test_af04, "AF05": test_af05, "AF06": test_af06,
         "AF07": test_af07, "AF08": test_af08, "AF09": test_af09}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--baseline-ref")
    args = parser.parse_args()
    repo = args.repo.resolve()
    assert shutil.which("ssh-keygen"), "ssh-keygen mancante: le firme di prova non si generano"
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
    inizio = time.time()
    for test in TESTS.values():
        test(repo)
    print(f"PASS {','.join(TESTS)} controlli={len(TESTS)} secondi={round(time.time() - inizio)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
