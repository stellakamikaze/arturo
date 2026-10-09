#!/usr/bin/env python3
"""A01-A11: /aggiorna e /inizio falliscono in modo sicuro e lo dicono (9/10/2026).

Claude lancia ogni blocco bash di un comando in una chiamata sua: le variabili di un blocco non
arrivano al successivo, la cartella corrente si'. Qui ogni blocco gira in una shell nuova, con bash
e con zsh, e parte dalla cartella in cui e' finito il blocco prima.

A01-A03 con un repository personale come origin e Arturo come upstream, ogni blocco di /aggiorna
ricava da se' da dove arrivano gli aggiornamenti: il diff di guardie e permessi non esce vuoto
(A01), il Passo 2 vede i file cambiati da tutti e due (A02), il Passo 3 applica da upstream con un
merge (A03). A04 con un file della config modificato e non salvato il Passo 3 non parte, lo dice e
non tocca niente. A05 lo stesso per il sync di /inizio. A06 se il pull di /inizio esce con 0 e
lascia un file in conflitto, la config torna a prima, e A07 il messaggio di ripristino compare
solo se il ripristino riesce davvero. A08 e A09 lo stesso per il Passo 3 di /aggiorna, che senza
ripristino non registra l'aggiornamento. A10 i comandi a mano del README non lasciano conflitti in
settings.json. A11 nessun blocco di /aggiorna, /inizio e /novita usa una variabile nata in un
altro blocco.

Il conflitto «a codice 0» di A06-A09 si fabbrica con un git finto in testa al PATH: dopo il pull,
il rebase o il merge veri lascia settings.json con tre versioni nell'indice e i marcatori nel
file, come un autostash che non si riapplica. Con FALLISCE_RESET=1 anche il reset fallisce.

Sulla base bb19ef9 ogni controllo deve fallire con un AssertionError che comincia con il suo
codice: un rosso per un file assente non conta.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Callable, Dict, List

GIT_ENV = {
    "GIT_AUTHOR_NAME": "prova", "GIT_AUTHOR_EMAIL": "prova@example.invalid",
    "GIT_COMMITTER_NAME": "prova", "GIT_COMMITTER_EMAIL": "prova@example.invalid",
    "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1", "GIT_TERMINAL_PROMPT": "0",
}
SHELL = [s for s in ("bash", "zsh") if shutil.which(s)]
SECONDA = "# Novita\n\n## 2026-09-02 — Seconda\n\n## 2026-09-01 — Prima\n"
# Le variabili che arrivano da fuori: l'ambiente della sessione e gli argomenti del comando.
DA_FUORI = {"HOME", "ARGUMENTS", "PROJECTS_BASE", "PWD"}

FINTO_GIT = r'''#!/bin/bash
# Il git vero, piu' un guasto a richiesta: vedi la docstring del banco.
VERO="@VERO@"
SUB=""
for a in "$@"; do
  case "$a" in pull|rebase|merge|reset) SUB=$a; break ;; esac
done
if [ "$SUB" = reset ] && [ "${FALLISCE_RESET:-}" = 1 ]; then
  echo "fatal: reset finto che fallisce" >&2; exit 1
fi
"$VERO" "$@"; rc=$?
case " $* " in *" --abort "*) exit $rc ;; esac
if [ $rc = 0 ] && [ -n "${CONFLITTO_DOPO:-}" ] && [ "$SUB" = "$CONFLITTO_DOPO" ] && [ ! -e "$CONFLITTO_FATTO" ]; then
  : > "$CONFLITTO_FATTO"
  cd "$CONFLITTO_REPO" || exit 1
  b1=$(printf '{"B": "base"}\n' | "$VERO" hash-object -w --stdin)
  b2=$(printf '{"B": "tuo"}\n' | "$VERO" hash-object -w --stdin)
  b3=$(printf '{"B": "loro"}\n' | "$VERO" hash-object -w --stdin)
  "$VERO" update-index --force-remove settings.json
  printf '100644 %s 1\tsettings.json\n100644 %s 2\tsettings.json\n100644 %s 3\tsettings.json\n' "$b1" "$b2" "$b3" \
    | "$VERO" update-index --index-info
  printf '<<<<<<< tuo\n{"B": "tuo"}\n=======\n{"B": "loro"}\n>>>>>>> loro\n' > settings.json
fi
exit $rc
'''


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def blocchi(testo: str, titolo: str, codice: str) -> List[str]:
    """I blocchi ```bash dopo l'intestazione `titolo`, senza il rientro degli elenchi numerati."""
    assert titolo in testo, f"{codice} non trovo «{titolo}»"
    trovati = re.findall(r"```bash\n(.*?)```", testo[testo.index(titolo):], re.S)
    assert trovati, f"{codice} nessun blocco bash dopo «{titolo}»"
    return ["\n".join(r[3:] if r.startswith("   ") else r for r in b.splitlines()) for b in trovati]


def blocco(testo: str, titolo: str, codice: str, indice: int = 0) -> str:
    return blocchi(testo, titolo, codice)[indice]


class Lab:
    """Arturo pubblicato (bare), chi ne scrive gli aggiornamenti, e una HOME con ~/.claude clonata."""

    def __init__(self, repo: Path, base: Path, shell: str):
        self.repo, self.base, self.shell = repo, base, shell
        self.home = base / "home"
        self.utente = self.home / ".claude"
        self.cwd = self.home / "progetto"
        self.env = dict(os.environ, HOME=str(self.home), GIT_CEILING_DIRECTORIES=str(base), **GIT_ENV)
        for via in ("CONFLITTO_DOPO", "FALLISCE_RESET"):
            self.env.pop(via, None)
        seme = base / "seme"
        (seme / "hooks").mkdir(parents=True)
        self.cwd.mkdir(parents=True)
        (seme / "settings.json").write_text(json.dumps({"env": {"A": "1", "B": "2", "C": "3"}}, indent=2) + "\n")
        (seme / "NOVITA.md").write_text("# Novita\n\n## 2026-09-01 — Prima\n")
        (seme / "hooks" / "guardia.py").write_text("blocca = True\n")
        shutil.copy(str(repo / "hooks" / "controlla-config.py"), str(seme / "hooks" / "controlla-config.py"))
        self.git(base, "init", "-q", "-b", "main", str(seme))
        self.git(seme, "add", "-A")
        self.git(seme, "commit", "-q", "-m", "v0")
        arturo = base / "arturo.git"
        self.git(base, "clone", "-q", "--bare", str(seme), str(arturo))
        self.git(base, "clone", "-q", str(arturo), str(self.utente))
        self.autore = base / "autore"
        self.git(base, "clone", "-q", str(arturo), str(self.autore))

    def git(self, cartella: Path, *argomenti: str) -> str:
        r = subprocess.run(["git", "-C", str(cartella), *argomenti], env=self.env, capture_output=True, text=True,
                           timeout=60)
        if r.returncode:
            raise RuntimeError(f"git {' '.join(argomenti)}: {r.stderr.strip()}")
        return r.stdout.strip()

    def personale(self) -> Path:
        """/setup FASE 7: origin diventa un repository della persona, Arturo resta come upstream."""
        p = self.base / "personale.git"
        self.git(self.base, "init", "-q", "--bare", "-b", "main", str(p))
        self.git(self.utente, "remote", "rename", "origin", "upstream")
        self.git(self.utente, "remote", "add", "origin", str(p))
        self.git(self.utente, "push", "-q", "-u", "origin", "main")
        return p

    def cambia(self, cartella: Path, file: str, vecchio: str, nuovo: str) -> None:
        f = cartella / file
        testo = read(f)
        assert vecchio in testo, f"prova: {vecchio} manca in {file}"
        f.write_text(testo.replace(vecchio, nuovo))

    def pubblica(self, cartella: Path, modifiche: Dict[str, Callable[[str], str]], messaggio: str) -> None:
        for nome, fare in modifiche.items():
            (cartella / nome).write_text(fare(read(cartella / nome)))
        self.git(cartella, "commit", "-q", "-am", messaggio)
        self.git(cartella, "push", "-q", "origin", "main")

    def guasto(self, dopo: str, reset_fallisce: bool = False) -> None:
        finti = self.base / "finti"
        finti.mkdir()
        vero = shutil.which("git", path=os.environ.get("PATH"))
        assert vero, "prova: git mancante"
        (finti / "git").write_text(FINTO_GIT.replace("@VERO@", vero))
        (finti / "git").chmod(0o755)
        self.env.update(PATH=f"{finti}{os.pathsep}{os.environ.get('PATH', '')}", CONFLITTO_DOPO=dopo,
                        CONFLITTO_REPO=str(self.utente), CONFLITTO_FATTO=str(self.base / "conflitto-fatto"))
        if reset_fallisce:
            self.env["FALLISCE_RESET"] = "1"

    def lancia(self, script: str) -> str:
        """Un blocco in una shell nuova, come una chiamata Bash di Claude: la cartella resta, le variabili no."""
        traccia = self.base / "cwd"
        r = subprocess.run([self.shell, "-c", f"trap 'pwd > \"{traccia}\"' EXIT\n" + script], cwd=str(self.cwd),
                           env=self.env, capture_output=True, timeout=120)
        if traccia.exists():
            self.cwd = Path(read(traccia).strip())
        return (r.stdout + r.stderr).decode("utf-8", "replace")

    def head(self) -> str:
        return self.git(self.utente, "rev-parse", "HEAD")

    def config_integra(self) -> bool:
        r = subprocess.run(["python3", str(self.utente / "hooks" / "controlla-config.py"), "--quiet", str(self.utente)],
                           env=dict(self.env, PATH=os.environ.get("PATH", "")), capture_output=True, timeout=60)
        return r.returncode == 0

    def registro(self) -> str:
        f = self.utente / "session-env" / "aggiornamenti"
        return read(f) if f.exists() else ""


def per_shell(prova: Callable[[Lab], None], repo: Path) -> None:
    assert SHELL, "bash mancante: i blocchi non si provano"
    for shell in SHELL:
        with tempfile.TemporaryDirectory() as tmp:
            prova(Lab(repo, Path(tmp), shell))


def aggiorna(repo: Path) -> str:
    return read(repo / "commands" / "aggiorna.md")


def fase0(repo: Path) -> str:
    return blocco(read(repo / "commands" / "inizio.md"), "## FASE 0", "A05")


# --- A01-A03: da dove arrivano gli aggiornamenti, in ogni blocco ---------------------------------

def con_upstream(lab: Lab) -> str:
    """Un commit suo su settings.json gia' pubblicato, e un aggiornamento di Arturo che allenta una
    guardia e tocca un'altra riga di settings.json. Ritorna il commit pubblicato."""
    lab.personale()
    lab.cambia(lab.utente, "settings.json", '"A": "1"', '"A": "mio"')
    lab.git(lab.utente, "commit", "-q", "-am", "chore: session sync")
    lab.git(lab.utente, "push", "-q", "origin", "main")
    lab.pubblica(lab.autore, {"hooks/guardia.py": lambda t: "blocca = False  # GUARDIA_ALLENTATA\n",
                              "settings.json": lambda t: t.replace('"C": "3"', '"C": "autore"'),
                              "NOVITA.md": lambda t: SECONDA}, "v1")
    return lab.head()


def test_a01(repo: Path) -> None:
    def prova(lab: Lab) -> None:
        con_upstream(lab)
        testo = aggiorna(repo)
        lab.lancia(blocco(testo, "## Passo 1", "A01"))
        uscita = lab.lancia(blocco(testo, "## Passo 1", "A01", 1))
        assert "GUARDIA_ALLENTATA" in uscita and '"C": "autore"' in uscita, \
            f"A01 con {lab.shell}, in una shell sua, il diff di guardie e permessi da upstream esce vuoto: {uscita[-300:]!r}"
    per_shell(prova, repo)


def test_a02(repo: Path) -> None:
    def prova(lab: Lab) -> None:
        con_upstream(lab)
        testo = aggiorna(repo)
        lab.lancia(blocco(testo, "## Passo 1", "A02"))
        uscita = lab.lancia(blocco(testo, "## Passo 2", "A02"))
        tutti_e_due = uscita.split("sia dall'aggiornamento", 1)[-1]
        assert "settings.json" in tutti_e_due, \
            f"A02 con {lab.shell}, in una shell sua, il Passo 2 non vede settings.json cambiato da tutti e due: {uscita!r}"
    per_shell(prova, repo)


def test_a03(repo: Path) -> None:
    def prova(lab: Lab) -> None:
        pubblicato = con_upstream(lab)
        testo = aggiorna(repo)
        lab.lancia(blocco(testo, "## Passo 1", "A03"))  # il fetch
        lab.cwd = lab.home / "progetto"  # il Passo 3 lanciato da un progetto, dopo il sì
        uscita = lab.lancia(blocco(testo, "## Passo 3", "A03"))
        assert "Seconda" in read(lab.utente / "NOVITA.md"), \
            f"A03 con {lab.shell}, in una shell sua, il Passo 3 non applica l'aggiornamento di upstream: {uscita[-300:]!r}"
        r = subprocess.run(["git", "-C", str(lab.utente), "merge-base", "--is-ancestor", pubblicato, "HEAD"],
                           env=lab.env, capture_output=True)
        assert r.returncode == 0, "A03 il Passo 3 riscrive un commit gia' pubblicato sul repository personale"
        assert lab.registro(), "A03 l'aggiornamento applicato non e' registrato: /aggiorna indietro non lo trova"
    per_shell(prova, repo)


# --- A04-A05: modifiche non salvate ---------------------------------------------------------------

def sporca(lab: Lab) -> None:
    """Quello che fa /setup: una riga di settings.json cambiata e non salvata con un commit."""
    lab.cambia(lab.utente, "settings.json", '"B": "2"', '"B": "utente"')


def intatta(lab: Lab, prima: str, codice: str, uscita: str) -> None:
    impostazioni = read(lab.utente / "settings.json")
    assert lab.head() == prima, f"{codice} con {lab.shell} la copia e' cambiata: {uscita[-400:]!r}"
    assert "<<<<<<<" not in impostazioni and '"B": "utente"' in impostazioni, \
        f"{codice} con {lab.shell} settings.json ha perso la modifica o ha i marcatori: {impostazioni!r} {uscita[-300:]!r}"
    assert lab.config_integra(), f"{codice} con {lab.shell} la config non e' integra: {uscita[-300:]!r}"
    assert not lab.git(lab.utente, "stash", "list"), f"{codice} con {lab.shell} le modifiche sono finite in uno stash"


def test_a04(repo: Path) -> None:
    def prova(lab: Lab) -> None:
        lab.pubblica(lab.autore, {"settings.json": lambda t: t.replace('"B": "2"', '"B": "autore"'),
                                  "NOVITA.md": lambda t: SECONDA}, "v1")
        sporca(lab)
        prima = lab.head()
        testo = aggiorna(repo)
        lab.lancia(blocco(testo, "## Passo 1", "A04"))
        uscita = lab.lancia(blocco(testo, "## Passo 3", "A04"))
        intatta(lab, prima, "A04", uscita)
        assert "NON PARTITA" in uscita and "settings.json" in uscita, \
            f"A04 con {lab.shell} il Passo 3 non dice che non parte e quale file aspetta: {uscita[-300:]!r}"
        assert not lab.registro(), "A04 un aggiornamento non applicato e' registrato"
    per_shell(prova, repo)


def test_a05(repo: Path) -> None:
    def prova(lab: Lab) -> None:
        p = lab.personale()
        altro = lab.base / "altro-computer"
        lab.git(lab.base, "clone", "-q", str(p), str(altro))
        lab.pubblica(altro, {"settings.json": lambda t: t.replace('"B": "2"', '"B": "altro computer"')},
                     "chore: session sync")
        sporca(lab)
        prima = lab.head()
        uscita = lab.lancia(fase0(repo))
        intatta(lab, prima, "A05", uscita)
        assert "non ho scaricato" in uscita and "settings.json" in uscita, \
            f"A05 con {lab.shell} /inizio non dice che non scarica e quale file aspetta: {uscita[-300:]!r}"
        assert "Ho riportato" not in uscita, f"A05 con {lab.shell} /inizio dice di aver riportato una copia mai toccata"
    per_shell(prova, repo)


# --- A06-A09: un conflitto con codice d'uscita 0, e il ripristino ---------------------------------

def sync_da_altro_computer(lab: Lab) -> None:
    p = lab.personale()
    altro = lab.base / "altro-computer"
    lab.git(lab.base, "clone", "-q", str(p), str(altro))
    lab.pubblica(altro, {"settings.json": lambda t: t.replace('"B": "2"', '"B": "altro computer"')},
                 "chore: session sync")


def test_a06(repo: Path) -> None:
    def prova(lab: Lab) -> None:
        sync_da_altro_computer(lab)
        prima = lab.head()
        lab.guasto("pull")
        uscita = lab.lancia(fase0(repo))
        assert lab.head() == prima and not lab.git(lab.utente, "diff", "--name-only", "--diff-filter=U") \
            and lab.config_integra(), \
            f"A06 con {lab.shell} un pull che lascia settings.json in conflitto non torna a prima: {uscita[-400:]!r}"
        assert "riportato" in uscita and "NON sono riuscito" not in uscita, \
            f"A06 con {lab.shell} il ripristino riuscito non e' detto: {uscita[-300:]!r}"
    per_shell(prova, repo)


def test_a07(repo: Path) -> None:
    def prova(lab: Lab) -> None:
        sync_da_altro_computer(lab)
        lab.guasto("pull", reset_fallisce=True)
        uscita = lab.lancia(fase0(repo))
        assert not lab.config_integra(), "A07 prova: il guasto finto non ha lasciato la config rotta"
        assert "Ho riportato la copia" not in uscita and "Ho riportato la config" not in uscita, \
            f"A07 con {lab.shell} /inizio dice di aver riportato la copia a prima, ma la config e' rotta: {uscita[-400:]!r}"
        assert "NON sono riuscito" in uscita, f"A07 con {lab.shell} /inizio non dice che il ripristino e' fallito: {uscita[-300:]!r}"
    per_shell(prova, repo)


def aggiornamento_da_applicare(lab: Lab) -> None:
    lab.pubblica(lab.autore, {"settings.json": lambda t: t.replace('"B": "2"', '"B": "autore"'),
                              "NOVITA.md": lambda t: SECONDA}, "v1")


def test_a08(repo: Path) -> None:
    def prova(lab: Lab) -> None:
        aggiornamento_da_applicare(lab)
        prima = lab.head()
        testo = aggiorna(repo)
        lab.lancia(blocco(testo, "## Passo 1", "A08"))
        lab.guasto("rebase")
        uscita = lab.lancia(blocco(testo, "## Passo 3", "A08"))
        assert lab.head() == prima and not lab.git(lab.utente, "diff", "--name-only", "--diff-filter=U") \
            and lab.config_integra(), \
            f"A08 con {lab.shell} un rebase che lascia settings.json in conflitto non torna a prima: {uscita[-400:]!r}"
        assert "APPLICAZIONE ANNULLATA" in uscita, f"A08 con {lab.shell} l'annullamento non e' detto: {uscita[-300:]!r}"
        assert not lab.registro(), "A08 un aggiornamento annullato e' registrato"
    per_shell(prova, repo)


def test_a09(repo: Path) -> None:
    def prova(lab: Lab) -> None:
        aggiornamento_da_applicare(lab)
        testo = aggiorna(repo)
        lab.lancia(blocco(testo, "## Passo 1", "A09"))
        lab.guasto("rebase", reset_fallisce=True)
        uscita = lab.lancia(blocco(testo, "## Passo 3", "A09"))
        assert not lab.config_integra(), "A09 prova: il guasto finto non ha lasciato la config rotta"
        assert "APPLICAZIONE ANNULLATA" not in uscita and "RIPRISTINO NON RIUSCITO" in uscita, \
            f"A09 con {lab.shell} il Passo 3 non dice che il ripristino e' fallito: {uscita[-400:]!r}"
        assert not lab.registro(), "A09 un aggiornamento rimasto a meta' e' registrato come applicato"
    per_shell(prova, repo)


# --- A10-A11 -----------------------------------------------------------------------------------------

def test_a10(repo: Path) -> None:
    def prova(lab: Lab) -> None:
        aggiornamento_da_applicare(lab)
        sporca(lab)
        prima = lab.head()
        uscita = lab.lancia(blocco(read(repo / "README.md"), "## Aggiornare Arturo", "A10"))
        intatta(lab, prima, "A10", uscita)
    per_shell(prova, repo)


def variabili_orfane(script: str) -> List[str]:
    """Le variabili MAIUSCOLE che il blocco legge senza averle assegnate lui."""
    assegnate = set(re.findall(r"\b([A-Z_][A-Z0-9_]*)=", script))
    for nomi in re.findall(r"\bread\s+(?:-r\s+)?((?:[A-Za-z_][A-Za-z0-9_]*\s*)+)", script):
        assegnate.update(nomi.split())
    assegnate.update(re.findall(r"\bfor\s+([A-Z_][A-Z0-9_]*)\s+in\b", script))
    lette = set(re.findall(r"\$\{?([A-Z_][A-Z0-9_]*)", script))
    return sorted(lette - assegnate - DA_FUORI)


def test_a11(repo: Path) -> None:
    orfane = []
    for comando in ("aggiorna.md", "inizio.md", "novita.md"):
        testo = read(repo / "commands" / comando)
        for numero, script in enumerate(re.findall(r"```bash\n(.*?)```", testo, re.S), 1):
            for nome in variabili_orfane(script):
                orfane.append(f"{comando} blocco {numero}: ${nome}")
    assert not orfane, "A11 blocchi che leggono una variabile nata in un altro blocco: " + "; ".join(orfane)


TESTS: Dict[str, Callable[[Path], None]] = {
    "A01": test_a01, "A02": test_a02, "A03": test_a03, "A04": test_a04, "A05": test_a05, "A06": test_a06,
    "A07": test_a07, "A08": test_a08, "A09": test_a09, "A10": test_a10, "A11": test_a11,
}


def baseline(tests: Dict[str, Callable[[Path], None]], repo: Path) -> tuple:
    """La controprova: (codici rossi col loro codice, controlli rossi per un altro motivo o verdi)."""
    rossi, altro = [], []
    for nome, test in tests.items():
        try:
            test(repo)
        except AssertionError as e:
            if str(e).startswith(nome):
                rossi.append(nome)
            else:
                altro.append(f"{nome}: AssertionError senza il codice: {str(e)[:160]}")
        except Exception as e:  # noqa: BLE001 - un file assente non e' il motivo del controllo
            altro.append(f"{nome}: {type(e).__name__} {str(e)[:160]}")
        else:
            altro.append(f"{nome}: verde")
    return rossi, altro


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--baseline-ref")
    parser.add_argument("--solo", help="codici separati da virgola, per i veleni")
    args = parser.parse_args()
    repo = args.repo.resolve()
    scelti: Dict[str, Callable[[Path], None]] = {
        k: v for k, v in TESTS.items() if not args.solo or k in args.solo.split(",")}
    if args.baseline_ref:
        rossi, altro = baseline(scelti, repo)
        assert not altro and rossi == list(scelti), \
            "baseline non discriminante: ogni controllo deve fallire col suo codice.\n" + "\n".join(altro)
        print(f"BASELINE_DISCRIMINANTE={','.join(rossi)}")
        return 0
    for test in scelti.values():
        test(repo)
    print(f"PASS {','.join(scelti)} controlli={len(scelti)} shell={','.join(SHELL)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
