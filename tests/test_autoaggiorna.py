#!/usr/bin/env python3
"""AA01-AA11: Arturo si aggiorna da solo alla chiusura, solo con rilasci firmati (16/10/2026, #3477).

Ogni caso costruisce un Arturo pubblicato (bare), chi ne firma i rilasci con una chiave di prova
generata qui, e una HOME con ~/.claude clonata, che si fida solo di quella chiave. Niente rete.

AA01 un rilascio firmato e più nuovo si installa alla chiusura, e la config resta integra.
AA02 un tag non firmato, o firmato da un'altra chiave, non si installa: lo stato dice il motivo.
AA03 con «manuali» niente si installa, e l'avvio dice di usare /aggiorna.
AA04 con un'altra sessione di Claude Code aperta si rimanda: ~/.claude non cambia.
AA05 con modifiche non salvate niente cambia, e l'avvio dopo dice che non è partito e perché.
AA06 una storia pubblicata riscritta non si installa mai da sola.
AA07 la barra in basso mostra l'aggiornamento in attesa, e tace quando non c'è.
AA08 l'avvio annuncia la funzione una volta sola, e dopo un'installazione dice la versione una volta.
AA09 si installa il tag, non i commit di main arrivati dopo il tag.
AA10 la chiusura vera della sessione (hooks/session-end.sh) lancia l'installazione.
AA11 con un repository personale come origin, Arturo arriva da upstream con un merge.

Sulla base 5d83592, prima della funzione, ogni controllo deve fallire col suo codice.
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
        assert lab.arturo_cli("manuali").returncode == 0, "AA03 «manuali» non esiste"
        lab.arturo_cli("applica")
        assert lab.head() == prima, "AA03 con «manuali» il rilascio si installa"
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
        assert "non è partito" in uscita and "/aggiorna" in uscita, f"AA05 l'avvio non dice perché: {uscita!r}"
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


TESTS = {"AA01": test_aa01, "AA02": test_aa02, "AA03": test_aa03, "AA04": test_aa04, "AA05": test_aa05,
         "AA06": test_aa06, "AA07": test_aa07, "AA08": test_aa08, "AA09": test_aa09, "AA10": test_aa10, "AA11": test_aa11}


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
