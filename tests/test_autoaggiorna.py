#!/usr/bin/env python3
"""AA01-AA20: Arturo si aggiorna da solo alla chiusura, solo con rilasci firmati (16/10/2026, #3477).

Ogni caso costruisce un Arturo pubblicato (bare), chi ne firma i rilasci con una chiave di prova
generata qui, e una HOME con ~/.claude clonata, che si fida solo di quella chiave. Niente rete.

AA01 un rilascio firmato e più nuovo si installa alla chiusura, e la config resta integra.
AA02 un tag non firmato, o firmato da un'altra chiave, non si installa: lo stato dice il motivo.
AA03 con "manuali" niente si installa, e l'avvio dice di usare /aggiorna.
AA04 con un'altra sessione di Claude Code aperta si rimanda: ~/.claude non cambia.
AA05 con modifiche non salvate niente cambia, e l'avvio dopo dice che non è partito e perché.
AA06 una storia pubblicata riscritta non si installa mai da sola.
AA07 la barra in basso mostra l'aggiornamento in attesa, e tace quando non c'è.
AA08 l'avvio annuncia la funzione una volta sola, e dopo un'installazione dice la versione una volta.
AA09 si installa il tag, non i commit di main arrivati dopo il tag.
AA10 la chiusura vera della sessione (hooks/session-end.sh) lancia l'installazione.
AA11 con un repository personale come origin, Arturo arriva da upstream con un merge.
AA12 un rilascio rinviato si installa all'avvio dopo, se la sessione che parte è l'unica (3/11/2026).
AA13 con un'altra sessione aperta l'avvio non installa il rinvio, e dice perché.
AA14 un conflitto su un file di Arturo installa il rilascio: la versione della persona va in
     personale/conflitti/<data>, con differenze.patch, e l'avvio lo dice una volta sola.
AA15 un conflitto su settings.json resta alla persona: niente si installa, la copia di prova aspetta.
AA16 una copia di prova in attesa da un aggiornamento si salva in copia-in-attesa.patch, e il rilascio
     si installa.
AA17 una copia di prova in attesa dal sync fra le macchine resta com'è: niente si installa.
AA18 dopo un /clear, un /compact o una ripresa il rinvio non si installa: lo installa l'apertura dopo di
     Claude Code, perché il processo di prima ha i mod caricati (#4732, 4/11/2026).
AA19 una procedura che non parte lascia all'avvio i file che la fermano, senza dire anche che il rilascio
     si installa da solo (segnalazione n. 49 di Gigi, #4767, 4/11/2026).
AA20 con le modifiche salvate in un commit lo stato torna pronto e il rilascio si installa alla chiusura.
AA22 con uno spazio nella HOME ("Mario Rossi") una copia di prova in attesa resta dov'è al giro dopo, e
     "scarta" toglie solo lei: niente sopra la HOME si cancella (review del 7/11/2026, critico).
AA23 un rilascio tolto con /aggiorna indietro non si reinstalla da solo alla chiusura dopo; uno più nuovo sì.
AA24 "concludi" porta in personale/conflitti anche i file già risolti col rilascio prima del conflitto rimasto
     alla persona: il suo commit non sparisce in silenzio.

Sulla base 5d83592, prima della funzione, ogni controllo deve fallire col suo codice. AA12-AA17 sono rossi
anche sulla base 9ca11aa (dev del 3/11/2026), salvo le invarianti AA15 e AA17.
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

BASH = shutil.which("bash") or "bash"
NODE = shutil.which("node") or "node"
GIT_ENV = {"GIT_AUTHOR_NAME": "a", "GIT_AUTHOR_EMAIL": "a@example.invalid", "GIT_COMMITTER_NAME": "a",
           "GIT_COMMITTER_EMAIL": "a@example.invalid"}


def read(p: Path) -> str:
    return p.read_text(encoding="utf-8")


class Lab:
    def __init__(self, repo: Path, base: Path, codice: str):
        self.repo, self.base, self.codice = repo, base, codice
        assert (repo / "bin" / "aggiornamenti.py").exists(), f"{codice} manca bin/aggiornamenti.py"
        self.home = base / "home"
        self.utente = self.home / ".claude"
        self.env = dict(os.environ, HOME=str(self.home), USERPROFILE=str(self.home), GIT_CONFIG_GLOBAL=str(base / "gitconfig"),
                        GIT_CONFIG_NOSYSTEM="1", ARTURO_TELEMETRIA="0", ARTURO_ALTRE_SESSIONI="0", ARTURO_ATTESA_MAX="0",
                        ARTURO_BANCHI_AVVIO="0", PYTHONDONTWRITEBYTECODE="1", **GIT_ENV)
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
        for f in ("bin/aggiornamenti.py", "bin/aggiorna-applica.sh", "hooks/controlla-config.py", "hooks/session-end.sh"):
            shutil.copy(str(repo / f), str(seme / f))
        pub = read(Path(str(self.chiave) + ".pub")).split()
        (seme / "firme" / "rilasci.allowed_signers").write_text(f'rilasci@arturo namespaces="git" {pub[0]} {pub[1]}\n',
                                                                 encoding="utf-8")
        (seme / "settings.json").write_text(json.dumps({"env": {"A": "1"}}, indent=2) + "\n", encoding="utf-8")
        (seme / "NOVITA.md").write_text("# Novita\n", encoding="utf-8")
        (seme / ".gitignore").write_text("session-env/\ndata/\n", encoding="utf-8")
        self.git(base, "init", "-q", "-b", "main", str(seme))
        self.git(seme, "add", "-A")
        self.git(seme, "commit", "-q", "-m", "v1")
        self.git(seme, "tag", "-a", "v2026-01-01", "-m", "v1")
        self.arturo = base / "arturo.git"
        self.git(base, "clone", "-q", "--bare", str(seme), str(self.arturo))
        self.git(base, "clone", "-q", str(self.arturo), str(self.utente))
        self.autore = base / "autore"
        self.git(base, "clone", "-q", str(self.arturo), str(self.autore))

    def git(self, cartella: Path, *argomenti: str) -> str:
        r = subprocess.run(["git", "-C", str(cartella), *argomenti], env=self.env, capture_output=True, text=True, timeout=60)
        if r.returncode:
            raise RuntimeError(f"git {' '.join(argomenti)}: {r.stderr.strip()}")
        return r.stdout.strip()

    def rilascia(self, file: str, testo: str, tag: str, chiave: Path = None, firma: bool = True) -> str:
        (self.autore / file).parent.mkdir(parents=True, exist_ok=True)
        (self.autore / file).write_text(testo, encoding="utf-8")
        self.git(self.autore, "add", "-A")
        self.git(self.autore, "commit", "-q", "-m", f"rilascio {tag}")
        if tag:
            if firma:
                self.git(self.autore, "-c", "gpg.format=ssh", "-c", f"user.signingkey={chiave or self.chiave}",
                         "tag", "-s", tag, "-m", tag)
            else:
                self.git(self.autore, "tag", "-a", tag, "-m", tag)
        self.git(self.autore, "push", "-q", "--force", "--tags", "origin", "main")
        return self.git(self.autore, "rev-parse", "HEAD")

    def arturo_cli(self, *argomenti: str, **extra: str) -> subprocess.CompletedProcess:
        return subprocess.run([sys.executable, "-B", str(self.utente / "bin" / "aggiornamenti.py"), *argomenti],
                              env=dict(self.env, **extra), capture_output=True, text=True, encoding="utf-8", timeout=300)

    def stato(self) -> dict:
        f = self.utente / "session-env" / "aggiornamento.json"
        return json.loads(read(f)) if f.exists() else {}

    def head(self) -> str:
        return self.git(self.utente, "rev-parse", "HEAD")


def con_lab(repo: Path, codice: str, prova) -> None:
    with tempfile.TemporaryDirectory() as d:
        prova(Lab(repo, Path(d), codice))


def test_aa01(repo: Path) -> None:
    def prova(lab: Lab) -> None:
        commit = lab.rilascia("hooks/nuova.py", "x = 1\n", "v2026-02-01")
        r = lab.arturo_cli("applica")
        assert lab.head() == commit and (lab.utente / "hooks" / "nuova.py").exists(), \
            f"AA01 il rilascio firmato non si installa: {r.stdout[-300:]!r} {r.stderr[-300:]!r}"
        esito = json.loads(read(lab.utente / "session-env" / "aggiornamento-esito.json"))
        assert esito["esito"] == "APPLICATO" and esito["versione"] == "v2026-02-01", f"AA01 esito: {esito}"
        assert lab.git(lab.utente, "status", "--porcelain", "--untracked-files=no") == "", "AA01 restano modifiche"
    con_lab(repo, "AA01", prova)


def test_aa02(repo: Path) -> None:
    def prova(lab: Lab) -> None:
        prima = lab.head()
        lab.rilascia("hooks/nuova.py", "x = 1\n", "v2026-02-01", firma=False)
        lab.arturo_cli("applica")
        assert lab.head() == prima, "AA02 un tag non firmato si installa"
        assert lab.stato().get("stato") == "bloccato" and "firma" in lab.stato().get("motivo", ""), \
            f"AA02 lo stato non dice della firma: {lab.stato()}"
        lab.rilascia("hooks/nuova.py", "x = 2\n", "v2026-02-02", chiave=lab.altra)
        lab.arturo_cli("applica")
        assert lab.head() == prima, "AA02 un tag firmato da un'altra chiave si installa"
    con_lab(repo, "AA02", prova)


def test_aa03(repo: Path) -> None:
    def prova(lab: Lab) -> None:
        prima = lab.head()
        lab.rilascia("hooks/nuova.py", "x = 1\n", "v2026-02-01")
        assert lab.arturo_cli("manuali").returncode == 0, 'AA03 "manuali" non esiste'
        lab.arturo_cli("applica")
        assert lab.head() == prima, 'AA03 con "manuali" il rilascio si installa'
        lab.git(lab.utente, "fetch", "-q", "--tags", "origin", "main")
        uscita = lab.arturo_cli("stato").stdout
        assert "/aggiorna" in uscita and "a mano" in uscita, f"AA03 l'avvio non dice di usare /aggiorna: {uscita!r}"
        lab.arturo_cli("automatici")
        lab.arturo_cli("applica", ARTURO_AGGIORNAMENTI="manuali")
        assert lab.head() == prima, "AA03 ARTURO_AGGIORNAMENTI=manuali non ferma l'installazione"
    con_lab(repo, "AA03", prova)


def test_aa04(repo: Path) -> None:
    def prova(lab: Lab) -> None:
        prima = lab.head()
        lab.rilascia("hooks/nuova.py", "x = 1\n", "v2026-02-01")
        lab.arturo_cli("applica", ARTURO_ALTRE_SESSIONI="1")
        assert lab.head() == prima, "AA04 con un'altra sessione aperta si installa lo stesso"
    con_lab(repo, "AA04", prova)


def test_aa05(repo: Path) -> None:
    def prova(lab: Lab) -> None:
        prima = lab.head()
        (lab.utente / "settings.json").write_text(json.dumps({"env": {"A": "mio"}}, indent=2) + "\n", encoding="utf-8")
        lab.rilascia("hooks/nuova.py", "x = 1\n", "v2026-02-01")
        lab.arturo_cli("applica")
        assert lab.head() == prima and '"mio"' in read(lab.utente / "settings.json"), \
            "AA05 con modifiche non salvate ~/.claude cambia"
        uscita = lab.arturo_cli("stato").stdout
        assert "settings.json" in uscita and "/aggiorna" in uscita and "non si installa da sola" in uscita, \
            f"AA05 l'avvio non dice perché: {uscita!r}"
        assert "si installa da sola alla chiusura" not in uscita and lab.stato().get("stato") == "bloccato", \
            f"AA05 l'avvio promette l'installazione che le modifiche fermano (n. 49): {uscita!r} {lab.stato()}"
    con_lab(repo, "AA05", prova)


def test_aa06(repo: Path) -> None:
    def prova(lab: Lab) -> None:
        lab.git(lab.utente, "fetch", "-q", "origin", "main")
        prima = lab.head()
        radice = lab.git(lab.autore, "rev-list", "--max-parents=0", "HEAD")
        lab.git(lab.autore, "checkout", "-q", "--orphan", "riscritta")
        lab.git(lab.autore, "rm", "-rq", "--cached", ".")
        lab.git(lab.autore, "checkout", "-q", radice, "--", ".")
        lab.git(lab.autore, "commit", "-q", "-m", "storia nuova")
        lab.git(lab.autore, "branch", "-M", "main")
        lab.rilascia("hooks/nuova.py", "x = 1\n", "v2026-02-01")
        lab.arturo_cli("applica")
        assert lab.head() == prima, "AA06 una storia riscritta si installa da sola"
        assert lab.stato().get("stato") == "bloccato", f"AA06 stato: {lab.stato()}"
    con_lab(repo, "AA06", prova)


def test_aa07(repo: Path) -> None:
    with tempfile.TemporaryDirectory() as d:
        home = Path(d)
        (home / ".claude" / "session-env").mkdir(parents=True)
        f = home / ".claude" / "session-env" / "aggiornamento.json"
        env = dict(os.environ, HOME=str(home), USERPROFILE=str(home))
        env.pop("CLAUDE_CONFIG_DIR", None)
        entrata = json.dumps({"model": {"display_name": "Opus"}, "workspace": {"current_dir": str(home)}})

        def barra() -> str:
            r = subprocess.run([NODE, str(repo / "hooks" / "statusline.js")], input=entrata, env=env,
                               capture_output=True, text=True, encoding="utf-8", timeout=30)
            return r.stdout
        f.write_text(json.dumps({"controllato": int(time.time()), "versione": "v2026-02-01", "stato": "pronto"}),
                     encoding="utf-8")
        assert "Arturo v2026-02-01 · si installa alla chiusura" in barra(), f"AA07 la barra non mostra l'aggiornamento: {barra()!r}"
        f.write_text(json.dumps({"controllato": int(time.time()), "versione": "v2026-02-01", "stato": "bloccato"}),
                     encoding="utf-8")
        assert "serve /aggiorna" in barra(), "AA07 la barra non dice quando serve /aggiorna"
        f.write_text(json.dumps({"controllato": int(time.time()), "versione": "v2026-02-01", "stato": "aggiornato"}),
                     encoding="utf-8")
        assert "Arturo v" not in barra(), "AA07 la barra parla di un aggiornamento già installato"


def test_aa08(repo: Path) -> None:
    def prova(lab: Lab) -> None:
        primo = lab.arturo_cli("stato").stdout
        assert "si aggiorna da solo" in primo, f"AA08 manca l'annuncio: {primo!r}"
        assert "si aggiorna da solo" not in lab.arturo_cli("stato").stdout, "AA08 l'annuncio si ripete"
        lab.rilascia("hooks/nuova.py", "x = 1\n", "v2026-02-01")
        lab.arturo_cli("applica")
        dopo = lab.arturo_cli("stato").stdout
        assert "aggiornato a v2026-02-01" in dopo, f"AA08 l'avvio non dice la versione installata: {dopo!r}"
        assert "aggiornato a" not in lab.arturo_cli("stato").stdout, "AA08 la riga dell'installazione si ripete"
    con_lab(repo, "AA08", prova)


def test_aa09(repo: Path) -> None:
    def prova(lab: Lab) -> None:
        commit = lab.rilascia("hooks/nuova.py", "x = 1\n", "v2026-02-01")
        lab.rilascia("hooks/dopo.py", "y = 1\n", "")
        lab.arturo_cli("applica")
        assert lab.head() == commit and not (lab.utente / "hooks" / "dopo.py").exists(), \
            "AA09 si installano anche i commit dopo il tag"
    con_lab(repo, "AA09", prova)


def test_aa10(repo: Path) -> None:
    def prova(lab: Lab) -> None:
        commit = lab.rilascia("hooks/nuova.py", "x = 1\n", "v2026-02-01")
        subprocess.run([BASH, str(lab.utente / "hooks" / "session-end.sh")], input="{}", env=lab.env, cwd=str(lab.home),
                       capture_output=True, text=True, timeout=60)
        fine = time.time() + 90
        while time.time() < fine and lab.head() != commit:
            time.sleep(1)
        assert lab.head() == commit, "AA10 la chiusura della sessione non installa il rilascio"
        fine = time.time() + 30
        while time.time() < fine and (lab.utente / "session-env" / "aggiornamento.lock").exists():
            time.sleep(0.5)
    con_lab(repo, "AA10", prova)


def test_aa11(repo: Path) -> None:
    # Con un repository personale come origin (/setup FASE 7), Arturo è upstream: si aggiorna da lì,
    # con un merge che non riscrive i commit già pubblicati sul repository personale.
    def prova(lab: Lab) -> None:
        mio = lab.base / "mio.git"
        lab.git(lab.base, "init", "-q", "--bare", "-b", "main", str(mio))
        lab.git(lab.utente, "remote", "rename", "origin", "upstream")
        lab.git(lab.utente, "remote", "add", "origin", str(mio))
        (lab.utente / "mio.md").write_text("mio\n", encoding="utf-8")
        lab.git(lab.utente, "add", "mio.md")
        lab.git(lab.utente, "commit", "-q", "-m", "mio")
        lab.git(lab.utente, "push", "-q", "-u", "origin", "main")
        pubblicato = lab.head()
        commit = lab.rilascia("hooks/nuova.py", "x = 1\n", "v2026-02-01")
        lab.arturo_cli("applica")
        assert lab.git(lab.utente, "merge-base", "--is-ancestor", commit, "HEAD") == "" and \
            (lab.utente / "hooks" / "nuova.py").exists(), f"AA11 con Arturo come upstream il rilascio non si installa: {lab.stato()}"
        assert lab.git(lab.utente, "merge-base", "--is-ancestor", pubblicato, "HEAD") == "" and (lab.utente / "mio.md").exists(), \
            "AA11 l'aggiornamento riscrive o perde i commit del repository personale"
    con_lab(repo, "AA11", prova)


def aspetta_head(lab: Lab, commit: str, secondi: int = 90) -> bool:
    fine = time.time() + secondi
    while time.time() < fine and lab.head() != commit:
        time.sleep(1)
    fine = time.time() + 30
    while time.time() < fine and (lab.utente / "session-env" / "aggiornamento.lock").exists():
        time.sleep(0.5)
    return lab.head() == commit


def gitdir(lab: Lab) -> Path:
    return Path(lab.git(lab.utente, "rev-parse", "--absolute-git-dir"))


def test_aa12(repo: Path) -> None:
    def prova(lab: Lab) -> None:
        commit = lab.rilascia("hooks/nuova.py", "x = 1\n", "v2026-02-01")
        lab.arturo_cli("applica", ARTURO_ALTRE_SESSIONI="1")
        assert lab.head() != commit, "AA12 la prova non parte: il rilascio si installa con un'altra sessione aperta"
        uscita = lab.arturo_cli("stato", ARTURO_ALTRE_SESSIONI="1").stdout
        assert "installo ora" in uscita, f"AA12 l'avvio con una sessione sola non installa il rinvio: {uscita!r}"
        assert aspetta_head(lab, commit), f"AA12 il rinvio non si installa all'avvio: {lab.stato()}"
    con_lab(repo, "AA12", prova)


def test_aa13(repo: Path) -> None:
    def prova(lab: Lab) -> None:
        prima = lab.head()
        lab.rilascia("hooks/nuova.py", "x = 1\n", "v2026-02-01")
        lab.arturo_cli("applica", ARTURO_ALTRE_SESSIONI="1")
        uscita = lab.arturo_cli("stato", ARTURO_ALTRE_SESSIONI="2").stdout
        time.sleep(3)
        assert lab.head() == prima, "AA13 con un'altra sessione aperta l'avvio installa lo stesso"
        assert "non si è installata" in uscita and "all'avvio di una sessione sola" in uscita, \
            f"AA13 l'avvio non dice perché il rinvio resta: {uscita!r}"
    con_lab(repo, "AA13", prova)


def guardia_della_persona(lab: Lab) -> str:
    """Un file di Arturo installato, poi cambiato dalla persona con un commit suo."""
    commit = lab.rilascia("hooks/guardia.py", "regola = 1\n", "v2026-02-01")
    lab.arturo_cli("applica")
    assert lab.head() == commit, "il primo rilascio non si installa"
    (lab.utente / "hooks" / "guardia.py").write_text("regola = 'della persona'\n", encoding="utf-8")
    lab.git(lab.utente, "commit", "-q", "-am", "la mia regola")
    return lab.rilascia("hooks/guardia.py", "regola = 2\n", "v2026-02-02")


def cartelle_orsa(lab: Lab) -> list:
    c = lab.utente / "personale" / "conflitti"
    return sorted(d for d in c.iterdir() if d.is_dir()) if c.is_dir() else []


def test_aa14(repo: Path) -> None:
    def prova(lab: Lab) -> None:
        commit = guardia_della_persona(lab)
        r = lab.arturo_cli("applica")
        dentro = subprocess.run(["git", "-C", str(lab.utente), "merge-base", "--is-ancestor", commit, "HEAD"],
                                env=lab.env, capture_output=True).returncode == 0
        assert dentro and read(lab.utente / "hooks" / "guardia.py") == "regola = 2\n", \
            f"AA14 il conflitto ferma il rilascio: {r.stdout[-300:]!r} {lab.stato()}"
        cartelle = cartelle_orsa(lab)
        assert len(cartelle) == 1 and read(cartelle[0] / "hooks" / "guardia.py") == "regola = 'della persona'\n" \
            and "della persona" in read(cartelle[0] / "differenze.patch"), \
            f"AA14 la versione della persona non è in personale/conflitti: {cartelle}"
        assert lab.git(lab.utente, "status", "--porcelain", "--untracked-files=no") == "", "AA14 restano modifiche"
        assert not (gitdir(lab) / "arturo-aggiorna-copia").exists(), "AA14 resta una copia di prova in attesa"
        primo = lab.arturo_cli("stato").stdout
        secondo = lab.arturo_cli("stato").stdout
        assert "personale/conflitti/" in primo and "hooks/guardia.py" in primo and "personale/conflitti/" not in secondo, \
            f"AA14 l'avvio non lo dice una volta sola: {primo!r} {secondo!r}"
    con_lab(repo, "AA14", prova)


def test_aa15(repo: Path) -> None:
    def prova(lab: Lab) -> None:
        (lab.utente / "settings.json").write_text(json.dumps({"env": {"A": "persona"}}, indent=2) + "\n", encoding="utf-8")
        lab.git(lab.utente, "commit", "-q", "-am", "le mie impostazioni")
        prima = lab.head()
        lab.rilascia("settings.json", json.dumps({"env": {"A": "2"}}, indent=2) + "\n", "v2026-02-01")
        lab.arturo_cli("applica")
        assert lab.head() == prima and "persona" in read(lab.utente / "settings.json"), \
            "AA15 un conflitto su settings.json si risolve senza la persona"
        assert (gitdir(lab) / "arturo-aggiorna-copia").exists(), \
            "AA15 la copia di prova col conflitto su settings.json non aspetta"
    con_lab(repo, "AA15", prova)


def copia_in_attesa(lab: Lab, modo: str) -> Path:
    """Una copia di prova lasciata da una versione di prima, col lavoro a metà di chi la risolveva."""
    copia = gitdir(lab) / "arturo-aggiorna" / "copia.vecchia" / "copia"
    copia.parent.mkdir(parents=True)
    lab.git(lab.utente, "worktree", "add", "-q", "--detach", str(copia), "HEAD")
    (copia / "NOVITA.md").write_text("# Novita\nlavoro a metà\n", encoding="utf-8")
    (gitdir(lab) / "arturo-aggiorna-copia").write_text(f"{copia} {lab.head()} {modo} 2026-02-01_10:00\n",
                                                       encoding="utf-8")
    return copia


def test_aa16(repo: Path) -> None:
    def prova(lab: Lab) -> None:
        copia_in_attesa(lab, "rebase")
        commit = lab.rilascia("hooks/nuova.py", "x = 1\n", "v2026-02-01")
        r = lab.arturo_cli("applica")
        assert lab.head() == commit, f"AA16 una copia in attesa ferma il rilascio: {r.stdout[-300:]!r} {lab.stato()}"
        patch = [d / "copia-in-attesa.patch" for d in cartelle_orsa(lab) if (d / "copia-in-attesa.patch").exists()]
        assert patch and "lavoro a metà" in read(patch[0]), f"AA16 il lavoro della copia in attesa non è salvato: {patch}"
    con_lab(repo, "AA16", prova)


def test_aa17(repo: Path) -> None:
    def prova(lab: Lab) -> None:
        copia = copia_in_attesa(lab, "sync")
        prima = lab.head()
        lab.rilascia("hooks/nuova.py", "x = 1\n", "v2026-02-01")
        lab.arturo_cli("applica")
        assert lab.head() == prima and copia.exists(), "AA17 una copia in attesa dal sync si toglie da sola"
    con_lab(repo, "AA17", prova)


def test_aa18(repo: Path) -> None:
    def prova(lab: Lab) -> None:
        prima = lab.head()
        commit = lab.rilascia("hooks/nuova.py", "x = 1\n", "v2026-02-01")
        lab.arturo_cli("applica", ARTURO_ALTRE_SESSIONI="1")
        dopo_clear = lab.arturo_cli("stato", ARTURO_ALTRE_SESSIONI="1", ARTURO_AVVIO="clear").stdout
        time.sleep(3)
        assert "prossima apertura" in dopo_clear and "installo ora" not in dopo_clear, \
            f"AA18 dopo un /clear l'avvio non rimanda il rinvio all'apertura: {dopo_clear!r}"
        assert lab.head() == prima, "AA18 dopo un /clear il rinvio si installa con la sessione di prima viva"
        apertura = lab.arturo_cli("stato", ARTURO_ALTRE_SESSIONI="1", ARTURO_AVVIO="startup").stdout
        assert "installo ora" in apertura, f"AA18 l'apertura dopo il /clear non installa il rinvio: {apertura!r}"
        assert aspetta_head(lab, commit), f"AA18 il rinvio non si installa all'apertura: {lab.stato()}"
    con_lab(repo, "AA18", prova)


def test_aa19(repo: Path) -> None:
    def prova(lab: Lab) -> None:
        prima = lab.head()
        procedura = ("#!/usr/bin/env bash\n"
                     "echo 'APPLICAZIONE NON PARTITA: questi file hanno modifiche tue non ancora salvate con un commit:'\n"
                     "echo '  settings.json'\necho 'Non ho toccato niente.'\nexit 1\n")
        lab.rilascia("bin/aggiorna-applica.sh", procedura, "v2026-02-01")
        lab.arturo_cli("applica")
        assert lab.head() == prima, "AA19 la prova non parte: il rilascio si installa"
        uscita = lab.arturo_cli("stato").stdout
        assert "non è partito" in uscita and "settings.json" in uscita, \
            f"AA19 l'avvio non dice quali file fermano l'aggiornamento: {uscita!r}"
        assert "si installa da sola" not in uscita, \
            f"AA19 l'avvio dice insieme che non è partito e che si installa da solo (n. 49): {uscita!r}"
    con_lab(repo, "AA19", prova)


def test_aa20(repo: Path) -> None:
    def prova(lab: Lab) -> None:
        (lab.utente / "settings.json").write_text(json.dumps({"env": {"A": "mio"}}, indent=2) + "\n", encoding="utf-8")
        commit = lab.rilascia("hooks/nuova.py", "x = 1\n", "v2026-02-01")
        lab.arturo_cli("applica")
        assert lab.stato().get("stato") == "bloccato", f"AA20 la prova non parte: {lab.stato()}"
        lab.git(lab.utente, "commit", "-qam", "le mie impostazioni")
        uscita = lab.arturo_cli("stato").stdout
        assert lab.stato().get("stato") == "pronto" and "si installa da sola" in uscita, \
            f"AA20 dopo il commit l'avvio non torna a dire che si installa: {uscita!r} {lab.stato()}"
        lab.arturo_cli("applica")
        assert (lab.utente / "hooks" / "nuova.py").exists() and '"mio"' in read(lab.utente / "settings.json"), \
            f"AA20 dopo il commit il rilascio {commit[:7]} non si installa: {lab.stato()}"
    con_lab(repo, "AA20", prova)


def test_aa21(repo: Path) -> None:
    def prova(lab: Lab) -> None:
        prima = lab.head()
        lab.rilascia("hooks/nuova.py", "x = 1\n", "v2026-02-01")
        lab.arturo_cli("applica", ARTURO_ALTRE_SESSIONI="1")
        assert lab.head() == prima, "AA21 la prova non parte: la prima chiusura installa con un'altra sessione aperta"
        lab.arturo_cli("applica", ARTURO_ALTRE_SESSIONI="1", ARTURO_ATTESA_MAX="30")
        assert (lab.utente / "hooks" / "nuova.py").exists(), \
            f"AA21 la chiusura dopo un rinvio aspetta ancora le altre sessioni (#4074): {lab.stato()}"
        commit = lab.rilascia("hooks/altra.py", "y = 1\n", "v2026-02-02")
        lab.arturo_cli("applica", ARTURO_ALTRE_SESSIONI="1")
        assert lab.head() != commit, "AA21 un rinvio già installato vale ancora per il rilascio dopo"
        lab.rilascia("hooks/terza.py", "z = 1\n", "v2026-02-03")
        lab.arturo_cli("applica", ARTURO_ALTRE_SESSIONI="1", ARTURO_ATTESA_MAX="30")
        assert (lab.utente / "hooks" / "terza.py").exists(), \
            f"AA21 un rinvio rimasto indietro non vale per il rilascio uscito dopo: {lab.stato()}"
    con_lab(repo, "AA21", prova)


def procedura(lab: Lab, *argomenti: str) -> str:
    p = subprocess.run([BASH, str(lab.utente / "bin" / "aggiorna-applica.sh"), str(lab.utente), *argomenti],
                       env=dict(lab.env, GIT_EDITOR="true"), cwd=str(lab.utente), capture_output=True, text=True,
                       encoding="utf-8", timeout=300)
    return p.stdout + p.stderr


def test_aa22(repo: Path) -> None:
    with tempfile.TemporaryDirectory() as d:
        assert " " not in d, "AA22 prova: la cartella temporanea ha già uno spazio"
        scatola = Path(d) / "scatola"
        altra = scatola / "altra-persona" / "documento.txt"
        altra.parent.mkdir(parents=True)
        altra.write_text("non mio\n", encoding="utf-8")
        base = scatola / "Mario Rossi"
        base.mkdir()
        lab = Lab(repo, base, "AA22")
        (lab.utente / "settings.json").write_text(json.dumps({"env": {"A": "persona"}}, indent=2) + "\n", encoding="utf-8")
        lab.git(lab.utente, "commit", "-q", "-am", "le mie impostazioni")
        lab.rilascia("settings.json", json.dumps({"env": {"A": "2"}}, indent=2) + "\n", "v2026-02-01")
        lab.arturo_cli("applica")
        stato = gitdir(lab) / "arturo-aggiorna-copia"
        assert stato.exists(), "AA22 prova: il conflitto su settings.json non lascia una copia in attesa"
        copia = Path(read(stato).split(" " + lab.head())[0])
        assert copia.is_dir(), f"AA22 prova: la copia in attesa non c'è: {copia}"
        lab.arturo_cli("applica")
        assert altra.exists() and lab.utente.is_dir(), \
            "AA22 il giro dopo ha cancellato la cartella sopra la HOME con lo spazio"
        assert copia.is_dir() and stato.exists(), "AA22 il giro dopo ha tolto la copia in attesa della persona"
        uscita = procedura(lab, "scarta")
        assert altra.exists() and lab.utente.is_dir(), f"AA22 scarta ha cancellato fuori dalle copie di prova: {uscita[-200:]!r}"
        assert "SCARTATA" in uscita and not copia.exists() and not stato.exists(), \
            f"AA22 scarta non toglie la copia con lo spazio nel percorso: {uscita[-300:]!r}"


def test_aa23(repo: Path) -> None:
    def prova(lab: Lab) -> None:
        prima = lab.head()
        commit = lab.rilascia("hooks/nuova.py", "x = 1\n", "v2026-02-01")
        lab.arturo_cli("applica")
        assert lab.head() == commit, "AA23 prova: il rilascio non si installa"
        uscita = procedura(lab, "indietro")
        assert "TORNATO INDIETRO" in uscita and lab.head() == prima, f"AA23 prova: indietro non torna: {uscita[-300:]!r}"
        lab.arturo_cli("applica")
        assert not (lab.utente / "hooks" / "nuova.py").exists() and lab.stato().get("stato") == "manuale", \
            f"AA23 il rilascio tolto con indietro si reinstalla da solo alla chiusura: {lab.stato()}"
        avvio = lab.arturo_cli("stato").stdout
        assert "/aggiorna indietro" in avvio and "si installa da sola" not in avvio, \
            f"AA23 l'avvio non dice che il rilascio tolto aspetta /aggiorna: {avvio!r}"
        nuovo = lab.rilascia("hooks/altra.py", "y = 1\n", "v2026-02-02")
        lab.arturo_cli("applica")
        assert lab.head() == nuovo, f"AA23 un rilascio più nuovo di quello tolto non si installa: {lab.stato()}"
    con_lab(repo, "AA23", prova)


def test_aa24(repo: Path) -> None:
    def prova(lab: Lab) -> None:
        lab.rilascia("hooks/guardia.py", "regola = 1\n", "v2026-02-01")
        lab.arturo_cli("applica")
        (lab.utente / "hooks" / "guardia.py").write_text("regola = 'della persona'\n", encoding="utf-8")
        lab.git(lab.utente, "commit", "-q", "-am", "la mia regola")
        (lab.utente / "settings.json").write_text(json.dumps({"env": {"A": "persona"}}, indent=2) + "\n", encoding="utf-8")
        lab.git(lab.utente, "commit", "-q", "-am", "le mie impostazioni")
        lab.rilascia("hooks/guardia.py", "regola = 2\n", "")
        lab.rilascia("settings.json", json.dumps({"env": {"A": "2"}}, indent=2) + "\n", "v2026-02-02")
        lab.arturo_cli("applica")
        stato = gitdir(lab) / "arturo-aggiorna-copia"
        assert stato.exists(), f"AA24 prova: il conflitto su settings.json non aspetta: {lab.stato()}"
        copia = Path(read(stato).split()[0])
        (copia / "settings.json").write_text(json.dumps({"env": {"A": "unita"}}, indent=2) + "\n", encoding="utf-8")
        lab.git(copia, "add", "settings.json")
        subprocess.run(["git", "-C", str(copia), "rebase", "--continue"], env=dict(lab.env, GIT_EDITOR="true"),
                       capture_output=True, text=True, timeout=60)
        uscita = procedura(lab, "concludi")
        assert "APPLICATO" in uscita, f"AA24 prova: concludi non applica: {uscita[-300:]!r}"
        salvate = [d / "hooks" / "guardia.py" for d in cartelle_orsa(lab) if (d / "hooks" / "guardia.py").exists()]
        assert salvate and read(salvate[0]) == "regola = 'della persona'\n", \
            f"AA24 concludi perde in silenzio la versione della persona del file risolto col rilascio: {cartelle_orsa(lab)}"
    con_lab(repo, "AA24", prova)


TESTS = {"AA01": test_aa01, "AA02": test_aa02, "AA03": test_aa03, "AA04": test_aa04, "AA05": test_aa05,
         "AA06": test_aa06, "AA07": test_aa07, "AA08": test_aa08, "AA09": test_aa09, "AA10": test_aa10, "AA11": test_aa11,
         "AA12": test_aa12, "AA13": test_aa13, "AA14": test_aa14, "AA15": test_aa15, "AA16": test_aa16,
         "AA17": test_aa17, "AA18": test_aa18, "AA19": test_aa19,
         "AA20": test_aa20, "AA21": test_aa21, "AA22": test_aa22, "AA23": test_aa23, "AA24": test_aa24}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--baseline-ref")
    args = parser.parse_args()
    repo = args.repo.resolve()
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
