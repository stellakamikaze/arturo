#!/usr/bin/env python3
"""P01-P07: le aggiunte della persona ai comandi di Arturo stanno in ~/.claude/personale/ (14/10/2026).

Il caso vero è quello di chi aggiunge a /inizio la tabella dei suoi progetti: ogni aggiornamento
che tocca /inizio va in conflitto. P01 con lo spostamento il Passo 3 di /aggiorna applica pulito, e
P02 il file personale tiene le parti aggiunte con la riga di Arturo dopo cui stavano, e quelle tolte.
P03 inject-now dice a Claude di leggere il file personale quando parte il comando, e il promemoria
del brief non scatta sui comandi /nome. P04 personale/ resta fuori da git e viaggia con /fine solo
verso un remote privato. P05 lo spostamento rifiuta ciò che non è un comando di Arturo e non crea
commit vuoti. P06 /aggiorna propone lo spostamento (Passo 2b e /aggiorna personale). P07 con Arturo
come upstream (merge) lo spostamento è un commit nuovo e non riscrive i commit pubblicati; P01 e P02
coprono Arturo come origin (rebase), dove i commit locali vengono riscritti senza il comando.

Riusa il Lab di test_aggiorna_sicuro.py: un Arturo pubblicato, chi ne scrive gli aggiornamenti e
una HOME con ~/.claude clonata. Sulla base f750408 ogni controllo deve fallire col suo codice.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Callable, Dict

_spec = importlib.util.spec_from_file_location("aggiorna_sicuro", Path(__file__).with_name("test_aggiorna_sicuro.py"))
assert _spec and _spec.loader
_sicuro = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_sicuro)
Lab, blocco, read, baseline = _sicuro.Lab, _sicuro.blocco, _sicuro.read, _sicuro.baseline

INIZIO = "# /inizio\n\nApri la sessione.\n\n## FASE 1\nLeggi l'handoff.\n\n## FASE 2\nMostra i todo.\n"


def prepara(repo: Path, tmp: Path) -> Lab:
    """Arturo pubblica /inizio; la persona ci aggiunge la sua tabella e toglie una riga; Arturo cambia la FASE 1."""
    lab = Lab(repo, tmp, "bash")
    (lab.autore / "commands").mkdir()
    (lab.autore / "commands" / "inizio.md").write_text(INIZIO)
    (lab.autore / ".gitignore").write_text(read(repo / ".gitignore"))  # come nell'Arturo vero
    lab.git(lab.autore, "add", "-A")
    lab.git(lab.autore, "commit", "-q", "-m", "v1: /inizio")
    lab.git(lab.autore, "push", "-q", "origin", "main")
    lab.git(lab.utente, "pull", "-q", "--ff-only")
    mio = INIZIO.replace("Leggi l'handoff.\n", "Leggi l'handoff.\nPoi la tabella dei miei progetti e i dischi.\n")
    mio = mio.replace("Apri la sessione.\n\n", "")
    (lab.utente / "commands" / "inizio.md").write_text(mio)
    lab.git(lab.utente, "commit", "-q", "-am", "chore: session sync")
    lab.pubblica(lab.autore, {"commands/inizio.md": lambda t: t.replace("Leggi l'handoff.", "Leggi l'handoff piu' recente.")},
                 "v2: /inizio")
    return lab


def arturo(lab: Lab, *argomenti: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, "-B", str(lab.repo / "bin" / "arturo"), *argomenti], env=lab.env,
                          capture_output=True, text=True, timeout=60)


def con_lab(prova: Callable[[Lab], None], repo: Path) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        prova(prepara(repo, Path(tmp)))


def test_p01(repo: Path) -> None:
    def prova(lab: Lab) -> None:
        testo = read(repo / "commands" / "aggiorna.md")
        lab.lancia(blocco(testo, "## Passo 1", "P01"))
        r = arturo(lab, "personale", "sposta", "commands/inizio.md")
        assert r.returncode == 0, f"P01 lo spostamento non riesce: {r.stdout!r} {r.stderr!r}"
        uscita = lab.lancia(blocco(testo, "## Passo 3", "P01"))
        assert "APPLICATO" in uscita and "CONFLITTO" not in uscita, f"P01 dopo lo spostamento l'aggiornamento non applica: {uscita[-300:]!r}"
        assert "handoff piu' recente" in read(lab.utente / "commands" / "inizio.md"), "P01 l'aggiornamento di /inizio non è arrivato"
        assert lab.config_integra(), "P01 la config non è integra"
    con_lab(prova, repo)


def test_p02(repo: Path) -> None:
    def prova(lab: Lab) -> None:
        arturo(lab, "personale", "sposta", "commands/inizio.md")
        personale = lab.utente / "personale" / "inizio.md"
        assert personale.exists(), "P02 manca personale/inizio.md"
        testo = read(personale)
        assert "Poi la tabella dei miei progetti e i dischi." in testo and "dopo la riga di Arturo «Leggi l'handoff.»" in testo, \
            f"P02 l'aggiunta non c'è o non dice dove stava: {testo!r}"
        assert "## Parti di Arturo che non seguo" in testo and "> Apri la sessione." in testo, f"P02 la parte tolta manca: {testo!r}"
        assert read(lab.utente / "commands" / "inizio.md") == INIZIO, "P02 /inizio non è tornato com'era in Arturo"
        assert "commands/inizio.md" not in lab.git(lab.utente, "diff", "--name-only", "origin/main...HEAD"), \
            "P02 con Arturo come origin un commit locale cambia ancora /inizio: il rebase di /aggiorna andrebbe in conflitto"
        assert lab.git(lab.utente, "status", "--porcelain") == "", "P02 personale/ compare fra i file di git"
        arturo(lab, "personale", "sposta", "commands/inizio.md")
        assert read(personale).count("Poi la tabella") == 1, "P02 un secondo spostamento duplica le aggiunte"
    con_lab(prova, repo)


def test_p07(repo: Path) -> None:
    # Con un repository personale come origin, Arturo è upstream e /aggiorna fa un merge: lo
    # spostamento è un commit nuovo, i commit già pubblicati sul repository personale restano.
    def prova(lab: Lab) -> None:
        pubblicato = lab.head()
        lab.personale()
        testo = read(repo / "commands" / "aggiorna.md")
        lab.lancia(blocco(testo, "## Passo 1", "P07"))
        r = arturo(lab, "personale", "sposta", "commands/inizio.md")
        assert r.returncode == 0 and lab.git(lab.utente, "log", "-1", "--format=%s").startswith("personale:"), \
            f"P07 con upstream lo spostamento non è un commit nuovo: {r.stderr!r}"
        assert lab.git(lab.utente, "merge-base", "--is-ancestor", pubblicato, "HEAD") == "", "P07 riscritto un commit pubblicato"
        uscita = lab.lancia(blocco(testo, "## Passo 3", "P07"))
        assert "APPLICATO" in uscita and "handoff piu' recente" in read(lab.utente / "commands" / "inizio.md"), \
            f"P07 con upstream l'aggiornamento non applica dopo lo spostamento: {uscita[-300:]!r}"
    con_lab(prova, repo)


def test_p03(repo: Path) -> None:
    def prova(lab: Lab) -> None:
        (lab.utente / "personale").mkdir()
        (lab.utente / "personale" / "inizio.md").write_text("# mie\n")
        hook = lambda prompt: subprocess.run(["bash", str(repo / "hooks" / "inject-now.sh")], input=json.dumps({"prompt": prompt}),
                                             capture_output=True, text=True, env=lab.env, timeout=60).stdout
        assert "PERSONALE:" in hook("/inizio progetto") and "personale/inizio.md" in hook("/inizio"), \
            "P03 /inizio non dice di leggere le aggiunte personali"
        assert "PERSONALE:" not in hook("/fine"), "P03 PERSONALE per un comando senza aggiunte"
        assert "BRIEF:" not in hook("/inizio") and "REGOLA FISSA" not in hook("/inizio"), "P03 il promemoria del brief scatta su un comando"
        assert "BRIEF:" in hook("sistemami il deploy"), "P03 il promemoria del brief manca su una richiesta"
    con_lab(prova, repo)


def test_p04(repo: Path) -> None:
    r = subprocess.run(["git", "-C", str(repo), "check-ignore", "-q", "--no-index", "personale/inizio.md"], capture_output=True)
    assert r.returncode == 0, "P04 personale/ non è in .gitignore"
    fine = read(repo / "commands" / "fine.md")
    privato = fine[fine.index('if [ "$VIS" = "PRIVATE" ]'):fine.index("else", fine.index('if [ "$VIS" = "PRIVATE" ]'))]
    assert "personale" in privato, "P04 /fine non porta personale/ verso il remote privato"
    pubblico = fine[fine.index("for p in settings.json"):fine.index("done", fine.index("for p in settings.json"))]
    assert "personale" not in pubblico, "P04 /fine porta personale/ anche verso un remote pubblico"


def test_p05(repo: Path) -> None:
    def prova(lab: Lab) -> None:
        for file in ("hooks/guardia.py", "commands/../settings.json", "commands/non-esiste.md"):
            r = arturo(lab, "personale", "sposta", file)
            assert r.returncode == 2, f"P05 sposta accetta {file}: {r.stdout!r}"
        lab.git(lab.utente, "reset", "-q", "--hard", "HEAD~1")  # la persona non ha ancora salvato niente
        (lab.utente / "commands" / "inizio.md").write_text(INIZIO + "\nMia riga.\n")
        prima = lab.head()
        r = arturo(lab, "personale", "sposta", "commands/inizio.md")
        assert r.returncode == 0 and lab.head() == prima, "P05 una modifica non salvata crea un commit vuoto"
        assert read(lab.utente / "commands" / "inizio.md") == INIZIO and "Mia riga." in read(lab.utente / "personale" / "inizio.md"), \
            "P05 la modifica non salvata non è spostata"
        elenco = arturo(lab, "personale", "elenco").stdout
        assert "personale/inizio.md" in elenco and "Comandi di Arturo modificati in ~/.claude: nessuno" in elenco, \
            f"P05 elenco: {elenco!r}"
    con_lab(prova, repo)


def test_p06(repo: Path) -> None:
    testo = read(repo / "commands" / "aggiorna.md")
    assert "### Passo 2b" in testo and "personale sposta commands/<nome>.md" in testo, "P06 /aggiorna non propone lo spostamento"
    assert "## Le sue aggiunte, senza aggiornare" in testo and "personale elenco" in testo, "P06 manca /aggiorna personale"
    assert "indietro | personale" in testo.split("---")[1], "P06 l'argomento personale non è dichiarato"


TESTS: Dict[str, Callable[[Path], None]] = {
    "P01": test_p01, "P02": test_p02, "P03": test_p03, "P04": test_p04, "P05": test_p05, "P06": test_p06,
    "P07": test_p07,
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--baseline-ref")
    parser.add_argument("--solo")
    args = parser.parse_args()
    repo = args.repo.resolve()
    scelti = {k: v for k, v in TESTS.items() if not args.solo or k in args.solo.split(",")}
    if args.baseline_ref:
        rossi, altro = baseline(scelti, repo)
        assert not altro and rossi == list(scelti), \
            "baseline non discriminante: ogni controllo deve fallire col suo codice.\n" + "\n".join(altro)
        print(f"BASELINE_DISCRIMINANTE={','.join(rossi)}")
        return 0
    for test in scelti.values():
        test(repo)
    print(f"PASS {','.join(scelti)} controlli={len(scelti)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
