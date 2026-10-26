#!/usr/bin/env python3
"""CP01-CP02: i testi scritti in più posti dicono la stessa cosa (#3852, 23/10/2026).

La revisione di fine sessione del 23/10 ha trovato due copie rimaste indietro: la cancellazione dei
dati di un'installazione aveva tre righe in docs/manutenzione.md e una sola in server/README.md.
La lista del ripristino ha cinque copie scritte a mano, e quelle della landing le vedeva solo il gate
della landing.

CP01 la cancellazione di un'installazione ha le stesse istruzioni DELETE in docs/manutenzione.md e
     in server/README.md, e tocca eventi, segnalazioni e contatori.
CP02 la lista del ripristino ha le stesse voci nel README e in commands/setup.md. Se il repository ha
     il ramo della landing (origin/landing-v2 o landing-v2), anche installatore, guida e llms.txt della
     landing hanno le stesse voci. Senza quel ramo (un clone di chi usa Arturo) la parte della landing
     si salta e lo dice.
CP03 nessun testo tracciato chiama anonimi i dati d'uso (26/10/2026): l'id è casuale, ma chi mantiene
     Arturo può sapere chi c'è dietro (docs/privacy.md). Restano le frasi che lo negano ("non sono
     anonimi") e NOVITA.md, che racconta anche la storia.

Sulla base f4ae0aa ogni controllo deve fallire con un AssertionError che comincia con il suo codice.
"""
from __future__ import annotations

import argparse
import html
import re
import subprocess
from pathlib import Path

MINIMO = 20  # il 23/10/2026 le voci sono 22: sotto 20 l'estrazione si è rotta, non la lista
CICLO = re.compile(r"for x in (.*?); do", re.S)
DELETE = re.compile(r"DELETE FROM (\w+) WHERE (.+?) = '")
RAMI_LANDING = ("origin/landing-v2", "landing-v2")
LANDING = ("sito/installa.sh", "sito/installa/index.html", "sito/llms.txt")


def voci(testo: str):
    """Le voci del primo ciclo `for x in …; do` che nomina CLAUDE.md, o None se non c'è."""
    for m in CICLO.finditer(html.unescape(testo)):
        parole = m.group(1).replace("\\\n", " ").split()
        if "CLAUDE.md" in parole:
            return parole
    return None


def cancellazioni(testo: str) -> set:
    return {(tabella, re.sub(r"\s+", " ", condizione)) for tabella, condizione in DELETE.findall(testo)}


def test_cp01(repo: Path) -> None:
    copie = {}
    for percorso in ("docs/manutenzione.md", "server/README.md"):
        f = repo / percorso
        assert f.is_file(), f"CP01 manca {percorso}"
        copie[percorso] = cancellazioni(f.read_text(encoding="utf-8"))
    a, b = copie.values()
    assert a == b, f"CP01 le due procedure di cancellazione differiscono: {sorted(a ^ b)}"
    tabelle = {tabella for tabella, _ in a}
    assert tabelle >= {"eventi", "segnalazioni", "contatori"}, f"CP01 la cancellazione non tocca tutto: {sorted(tabelle)}"


def dal_ramo(repo: Path, percorso: str):
    if not (repo / ".git").exists():
        return None, None
    for ramo in RAMI_LANDING:
        r = subprocess.run(["git", "-C", str(repo), "show", f"{ramo}:{percorso}"], capture_output=True, text=True,
                           encoding="utf-8", check=False)
        if r.returncode == 0:
            return r.stdout, f"{ramo}:{percorso}"
    return None, None


def test_cp02(repo: Path) -> None:
    liste = {}
    for percorso in ("README.md", "commands/setup.md"):
        f = repo / percorso
        assert f.is_file(), f"CP02 manca {percorso}"
        v = voci(f.read_text(encoding="utf-8"))
        assert v is not None and len(v) >= MINIMO, f"CP02 {percorso}: la lista del ripristino manca o è corta ({v})"
        liste[percorso] = v
    saltate = 0
    for percorso in LANDING:
        testo, nome = dal_ramo(repo, percorso)
        if testo is None:
            saltate += 1
            continue
        v = voci(testo)
        assert v is not None and len(v) >= MINIMO, f"CP02 {nome}: la lista del ripristino manca o è corta ({v})"
        liste[nome] = v
    tutte = set().union(*map(set, liste.values()))
    for nome, v in liste.items():
        assenti = sorted(tutte - set(v))
        assert not assenti, f"CP02 {nome}: mancano {' '.join(assenti)}"
    if saltate:
        print(f"NOTA CP02: ramo della landing assente, confrontate {len(liste)} copie su 5")


# Cartelle locali o generate, che git non porta: data/ e cache/ della persona, dipendenze.
FUORI = {".git", "data", "cache", "node_modules", "__pycache__", "session-env", "worktrees", ".claude"}
NEGA = re.compile(r"non (sono )?(dati )?anonim|non anonim", re.I)


def test_cp03(repo: Path) -> None:
    # Dal disco e non da git ls-files: nel gate la base è una cartella esportata, senza .git.
    file = [p for p in repo.rglob("*") if p.suffix in (".md", ".py", ".sh", ".js", ".html") and p.is_file()
            and not set(p.relative_to(repo).parts[:-1]) & FUORI]
    trovate = []
    for percorso in file:
        nome = percorso.relative_to(repo).as_posix()
        if nome == "NOVITA.md" or nome.startswith("tests/") or percorso.name.startswith("HANDOFF_"):
            continue
        righe = percorso.read_text(encoding="utf-8", errors="replace").splitlines()
        for n, riga in enumerate(righe, 1):
            # la negazione può andare a capo: "non sono dati" / "anonimi"
            if re.search(r"anonim", riga, re.I) and not NEGA.search(" ".join(righe[max(n - 2, 0):n])):
                trovate.append(f"{nome}:{n}")
    assert len(file) > 50, f"CP03 trovati solo {len(file)} file di testo: l'elenco si è rotto"
    assert not trovate, f"CP03 testi che chiamano anonimi i dati d'uso: {trovate}"


TESTS = {"CP01": test_cp01, "CP02": test_cp02, "CP03": test_cp03}


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
