#!/usr/bin/env python3
"""FI01-FI04: l'invito alla firma locale di Arturo.app per chi ha già Herdr (#5147, 20/11/2026).

Dal 9/11 installa-herdr.sh propone firma-locale.sh con la riga HERDR FIRMA, ma chi aveva già Arturo.app non
ripassa dall'installatore e non la vede mai. Ora il primo avvio sul Mac decide una volta sola, col segno
data/herdr-firma-invito.

FI01 con Arturo.app e senza l'identità "Arturo firma locale" il primo avvio stampa una riga HERDR FIRMA col
     comando di firma-locale.sh, che esiste; il secondo avvio tace;
FI02 con l'identità già presente l'avvio tace e scrive il segno, così il controllo non si ripete;
FI03 senza Arturo.app il primo avvio tace e scrive il segno: chi installa Herdr dopo vede la riga
     dall'installatore, e all'avvio dopo l'installazione l'invito non si ripete;
FI04 il segno resta fuori da git (.gitignore della config).

Gira session-start.sh in una casa finta. L'identità la finge ARTURO_HERDR_FIRMA, come nel banco di
installa-herdr.sh: niente portachiavi vero. Fuori dal Mac i casi FI01-FI03 non girano e lo dice.
--avvelena: ogni copia rotta fa rosso il caso suo.
"""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

CASI = ["FI01", "FI02", "FI03", "FI04"]
SEGNO = Path(".claude/data/herdr-firma-invito")


def avvio(repo: Path, casa: Path, firma: str | None) -> str:
    env = {**os.environ, "HOME": str(casa), "USERPROFILE": str(casa), "PATH": "/usr/bin:/bin:/usr/sbin:/sbin",
           "ARTURO_BANCHI_AVVIO": "0", "ARTURO_AGGIORNAMENTI": "manuali"}
    env.pop("ARTURO_HERDR_FIRMA", None)
    if firma:
        env["ARTURO_HERDR_FIRMA"] = firma
    r = subprocess.run(["bash", str(repo / "hooks/session-start.sh")], env=env, capture_output=True, text=True,
                       encoding="utf-8", errors="replace", timeout=60, stdin=subprocess.DEVNULL)
    return r.stdout


def righe_firma(uscita: str) -> list[str]:
    return [r for r in uscita.splitlines() if r.startswith("HERDR FIRMA")]


def casa_nuova(tmp: Path, nome: str, app: bool) -> Path:
    casa = tmp / nome
    (casa / ".claude/data").mkdir(parents=True)
    if app:
        (casa / "Applications/Arturo.app/Contents").mkdir(parents=True)
    return casa


def fi01(repo: Path, tmp: Path) -> str | None:
    casa = casa_nuova(tmp, "fi01", app=True)
    primo = righe_firma(avvio(repo, casa, "assente"))
    if len(primo) != 1:
        return f"chi ha Arturo.app senza firma riceve {len(primo)} righe HERDR FIRMA, non una"
    comando = str(repo / "shared/volta/firma-locale.sh")
    if comando not in primo[0] or not Path(comando).is_file():
        return f"la riga non porta il comando di firma-locale.sh: {primo[0][:160]}"
    if righe_firma(avvio(repo, casa, "assente")):
        return "l'invito alla firma torna al secondo avvio"
    return None


def fi02(repo: Path, tmp: Path) -> str | None:
    casa = casa_nuova(tmp, "fi02", app=True)
    if righe_firma(avvio(repo, casa, "presente")):
        return "invito alla firma anche con l'identità già presente"
    segno = casa / SEGNO
    if not segno.is_file() or "presente" not in segno.read_text(encoding="utf-8"):
        return "con l'identità presente il segno manca: il controllo si ripete a ogni avvio"
    return None


def fi03(repo: Path, tmp: Path) -> str | None:
    casa = casa_nuova(tmp, "fi03", app=False)
    if righe_firma(avvio(repo, casa, "assente")):
        return "invito alla firma senza Arturo.app"
    segno = casa / SEGNO
    if not segno.is_file() or "senza-app" not in segno.read_text(encoding="utf-8"):
        return "senza Arturo.app il segno manca: dopo /setup l'invito ripeterebbe la riga dell'installatore"
    (casa / "Applications/Arturo.app/Contents").mkdir(parents=True)
    if righe_firma(avvio(repo, casa, "assente")):
        return "dopo l'installazione l'avvio ripete la riga che l'installatore ha già dato"
    return None


def fi04(repo: Path, tmp: Path) -> str | None:
    prova_git = tmp / "fi04"
    prova_git.mkdir()
    shutil.copyfile(repo / ".gitignore", prova_git / ".gitignore")
    subprocess.run(["git", "init", "-q"], cwd=prova_git, check=True)
    r = subprocess.run(["git", "check-ignore", "-q", "--no-index", "data/herdr-firma-invito"], cwd=prova_git)
    return None if r.returncode == 0 else "data/herdr-firma-invito non è in .gitignore"


PROVE = {"FI01": fi01, "FI02": fi02, "FI03": fi03, "FI04": fi04}
SOLO_MAC = {"FI01", "FI02", "FI03"}


def prova(repo: Path) -> tuple[list[str], list[str]]:
    rossi, saltati = [], []
    with tempfile.TemporaryDirectory() as tmp:
        for caso in CASI:
            if caso in SOLO_MAC and sys.platform != "darwin":
                saltati.append(caso)
                continue
            esito = PROVE[caso](repo, Path(tmp))
            if esito:
                rossi.append(f"{caso} {esito}")
    return rossi, saltati


# (caso, file, testo giusto, testo rotto): ogni copia rotta deve far rosso il suo caso.
VELENI = [
    ("FI01", "hooks/session-start.sh", 'printf \'%s %s\\n\' "$(date +%Y-%m-%d)" "$ESITO_FIRMA" > "$SEGNO_FIRMA"', ":"),
    ("FI01", "hooks/session-start.sh", '  if [ "$ESITO_FIRMA" = assente ]; then\n    echo "HERDR FIRMA:',
     '  if false; then\n    echo "HERDR FIRMA:'),
    ("FI01", "hooks/session-start.sh", 'Il comando è: sh \\"$ARTURO_CODICE/shared/volta/firma-locale.sh\\"',
     'Il comando è: sh \\"$HOME/firma-locale.sh\\"'),
    ("FI02", "hooks/session-start.sh", '  if [ "$ESITO_FIRMA" = assente ]; then\n    echo "HERDR FIRMA:',
     '  if [ "$ESITO_FIRMA" != mai ]; then\n    echo "HERDR FIRMA:'),
    ("FI03", "hooks/session-start.sh", "    ESITO_FIRMA=senza-app\n", "    ESITO_FIRMA=assente\n"),
    ("FI03", "hooks/session-start.sh", '[ ! -d "$HOME/Applications/Arturo.app" ]; then\n    ESITO_FIRMA=senza-app\n',
     '[ ! -d "$HOME/Applications/Arturo.app" ]; then\n    exit 0\n'),
    ("FI04", ".gitignore", "data/herdr-firma-invito\n", ""),
]


def avvelena(repo: Path) -> int:
    esiti = []
    for caso, rel, giusto, rotto in VELENI:
        with tempfile.TemporaryDirectory() as tmp:
            copia = Path(tmp) / "repo"
            shutil.copytree(repo, copia, ignore=shutil.ignore_patterns(".git", "__pycache__", "node_modules", "tests"))
            testo = (copia / rel).read_text(encoding="utf-8")
            assert testo.count(giusto) == 1, f"veleno {caso}: il testo da rompere non c'è più in {rel}"
            (copia / rel).write_text(testo.replace(giusto, rotto), encoding="utf-8")
            rossi, saltati = prova(copia)
            if caso in saltati:
                print(f"VELENO {caso} SALTATO: il caso gira solo sul Mac")
                continue
            codici = [r.split()[0] for r in rossi]
            if caso not in codici:
                print(f"VELENO {caso} NON ATTACCA: rossi {codici}")
                return 1
            print(f"VELENO {caso} ROSSO: {next(r for r in rossi if r.startswith(caso))[:120]}")
            esiti.append(caso)
    print(f"VELENI_ROSSI={','.join(esiti)} veleni={len(VELENI)}")
    return 0


def main() -> int:
    for flusso in (sys.stdout, sys.stderr):
        if hasattr(flusso, "reconfigure"):
            flusso.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument("--avvelena", action="store_true")
    argomenti = parser.parse_args()
    if argomenti.avvelena:
        return avvelena(Path(argomenti.repo))
    rossi, saltati = prova(Path(argomenti.repo))
    for r in rossi:
        print("ROSSO", r)
    for s in saltati:
        print("SALTATO", s, "gira solo sul Mac")
    print(f"invito alla firma: {len(CASI) - len(rossi) - len(saltati)}/{len(CASI)} casi verdi")
    return 1 if rossi else 0


if __name__ == "__main__":
    sys.exit(main())
