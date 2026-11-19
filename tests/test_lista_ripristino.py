#!/usr/bin/env python3
"""Banco della lista del ripristino: le copie scritte a mano devono dire le stesse voci (#3844).

La lista dice cosa torna dalla cartella messa da parte quando si installa Arturo a mano (strada
"A mano, con Claude Code chiuso"). Una copia sta qui sulla landing (la guida), una sul ramo che
ricevono gli utenti (README), letta con git dal ramo main. Dal 19/11/2026 llms.txt non ha più la
strada a mano: manda gli agenti solo all'installazione verificata (rilievo 16 della revisione, #6092),
come CP02 di dev, e il banco controlla che il ciclo non ci torni. Dal 9/11/2026 /setup non ha più
una sua copia: rimanda al blocco della guida (review del 7/11, L10), e i suoi 64 byte di margine non
reggevano il ripristino dopo un clone fallito. Una voce che manca in
una copia vuol dire una persona che perde memoria, todo o scelte solo perché ha seguito la strada
sbagliata.

Dal 1/11/2026 sito/installa.sh innesta Arturo sul posto e non sposta più ~/.claude: il ciclo è uscito
dallo script, e il banco controlla che non ci torni come quinta copia da allineare.

--avvelena toglie l'ultima voce dalla copia della guida e vuole il rosso "mancano".
"""
import argparse
import html
import re
import subprocess
import sys
from pathlib import Path

MINIMO = 20  # il 23/10/2026 le voci sono 22: sotto 20 l'estrazione si è rotta, non la lista
CICLO = re.compile(r"for x in (.*?); do", re.S)


def voci(testo: str):
    """Le voci del primo ciclo `for x in …; do` che nomina CLAUDE.md, o None se non c'è."""
    for m in CICLO.finditer(html.unescape(testo)):
        parole = m.group(1).replace("\\\n", " ").split()
        if "CLAUDE.md" in parole:
            return parole
    return None


def dal_ramo(repo: Path, rami, percorso: str):
    for ramo in rami:
        r = subprocess.run(["git", "-C", str(repo), "show", f"{ramo}:{percorso}"], capture_output=True, text=True,
                           encoding="utf-8")
        if r.returncode == 0:
            return r.stdout, f"{ramo}:{percorso}"
    return None, f"{'/'.join(rami)}:{percorso}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=str(Path(__file__).resolve().parent.parent))
    ap.add_argument("--ramo", action="append", help="ramo dove leggere il README (default origin/main, poi main)")
    ap.add_argument("--avvelena", action="store_true", help="toglie una voce dalla guida: deve dare rosso")
    a = ap.parse_args()
    repo = Path(a.repo)
    rami = a.ramo or ["origin/main", "main"]

    copie = {}
    for percorso in ("sito/installa/index.html",):
        f = repo / percorso
        copie[percorso] = f.read_text(encoding="utf-8") if f.is_file() else None
    for percorso in ("README.md",):
        testo, nome = dal_ramo(repo, rami, percorso)
        copie[nome] = testo

    errori = []
    guida = "sito/installa/index.html"
    if a.avvelena and copie[guida]:
        v = voci(copie[guida])
        if v:
            copie[guida] = re.sub(r"\s" + re.escape(v[-1]) + r";", ";", html.unescape(copie[guida]), count=1)
    installatore = repo / "sito" / "installa.sh"
    if installatore.is_file() and voci(installatore.read_text(encoding="utf-8")) is not None:
        errori.append("sito/installa.sh: è tornato il ciclo `for x in …; do` con CLAUDE.md, ma lo script innesta sul posto")
    agenti = repo / "sito" / "llms.txt"
    if agenti.is_file() and voci(agenti.read_text(encoding="utf-8")) is not None:
        errori.append("sito/llms.txt: è tornato il ciclo `for x in …; do` con CLAUDE.md, ma llms.txt manda solo all'installazione verificata")
    liste = {}
    for nome, testo in copie.items():
        if testo is None:
            errori.append(f"manca {nome}")
            continue
        v = voci(testo)
        if v is None:
            errori.append(f"{nome}: nessun ciclo `for x in …; do` con CLAUDE.md")
        elif len(v) < MINIMO:
            errori.append(f"{nome}: {len(v)} voci, meno di {MINIMO}")
        elif len(set(v)) != len(v):
            errori.append(f"{nome}: voci ripetute")
        else:
            liste[nome] = v
    if len(liste) == len(copie):
        tutte = set().union(*map(set, liste.values()))
        for nome, v in liste.items():
            assenti = sorted(tutte - set(v))
            if assenti:
                errori.append(f"{nome}: mancano {' '.join(assenti)}")

    for e in errori:
        print(f"FAIL {e}")
    if errori:
        print(f"lista del ripristino: {len(errori)} errori su {len(copie)} copie")
        return 1
    print(f"lista del ripristino: {len(copie)}/{len(copie)} copie uguali, {len(next(iter(liste.values())))} voci")
    return 0


if __name__ == "__main__":
    sys.exit(main())
