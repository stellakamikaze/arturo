#!/usr/bin/env python3
"""P01-P18: le aggiunte della persona ai comandi di Arturo stanno in ~/.claude/personale/ (14/10/2026).

Il caso vero è quello di chi aggiunge a /inizio la tabella dei suoi progetti: ogni aggiornamento
che tocca /inizio va in conflitto. P01 con lo spostamento il Passo 3 di /aggiorna applica pulito, e
P02 il file personale tiene le parti aggiunte con la riga di Arturo dopo cui stavano, e quelle tolte.
P03 inject-now dice a Claude di leggere il file personale quando parte il comando, e il promemoria
del brief non scatta sui comandi /nome. P04 personale/ resta fuori da git e viaggia con /fine solo
verso un remote privato. P05 lo spostamento rifiuta ciò che non è un comando di Arturo e non crea
commit vuoti, ed elenco segnala il file personale di un comando uscito da Arturo. P06 /aggiorna sposta da solo, senza chiedere (Passo 2b), e /aggiorna personale lo fa subito. P07 con Arturo
come upstream (merge) lo spostamento è un commit nuovo e non riscrive i commit pubblicati; P01 e P02
coprono Arturo come origin (rebase), dove i commit locali vengono riscritti senza il comando. P08
con Arturo come origin /aggiorna sposta da solo, senza i passi di Claude. P09 con un repository privato e
Arturo come upstream /aggiorna sposta e non riscrive i commit pubblicati. P10 il sync fra le macchine
non sposta niente. P11 con un repository non privato non si sposta niente e ~/.claude non cambia. P12
se l'aggiornamento va in conflitto anche dopo lo spostamento, personale/ non viene scritto. P13 si
spostano solo i comandi che l'aggiornamento cambia, mai uno cancellato. P14 un secondo spostamento
tiene le righe personali di prima. P15 /aggiorna personale rispetta la stessa regola del repository
privato. P16 le aggiunte a hooks/session-start.sh vanno in personale/session-start.sh, commentate, e
l'hook di Arturo esegue quel file in fondo. P17 ripristina rimette una guardia com'è in Arturo. P18
quando è /aggiorna a spostare le aggiunte all'hook, personale/session-start.sh arriva in ~/.claude e
tiene quelle spostate prima.

Riusa il Lab di test_aggiorna_sicuro.py: un Arturo pubblicato, chi ne scrive gli aggiornamenti e
una HOME con ~/.claude clonata. Sulla base f750408 ogni controllo deve fallire col suo codice, anche P18
(che sulla base bf2207b fallisce sul file personale perso).
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Callable, Dict

# Su Windows "bash" per nome è quello di WSL: si prende il bash del PATH (Git Bash).
BASH = shutil.which("bash") or "bash"

_spec = importlib.util.spec_from_file_location("aggiorna_sicuro", Path(__file__).with_name("test_aggiorna_sicuro.py"))
assert _spec and _spec.loader
_sicuro = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_sicuro)
Lab, blocco, read, baseline = _sicuro.Lab, _sicuro.blocco, _sicuro.read, _sicuro.baseline

INIZIO = "# /inizio\n\nApri la sessione.\n\n## FASE 1\nLeggi l'handoff.\n\n## FASE 2\nMostra i todo.\n"


def prepara(repo: Path, tmp: Path, altri: Dict[str, str] = None) -> Lab:
    """Arturo pubblica /inizio; la persona ci aggiunge la sua tabella e toglie una riga; Arturo cambia la FASE 1."""
    lab = Lab(repo, tmp, "bash")
    (lab.autore / "commands").mkdir()
    (lab.autore / "commands" / "inizio.md").write_text(INIZIO, encoding="utf-8")
    for nome, testo in (altri or {}).items():
        (lab.autore / "commands" / nome).write_text(testo, encoding="utf-8")
    (lab.autore / ".gitignore").write_text(read(repo / ".gitignore"))  # come nell'Arturo vero
    if (repo / "bin" / "personale.py").exists():  # /aggiorna lo legge dalla versione in arrivo, come aggiorna-applica.sh
        shutil.copy(str(repo / "bin" / "personale.py"), str(lab.autore / "bin" / "personale.py"))
    lab.git(lab.autore, "add", "-A")
    lab.git(lab.autore, "commit", "-q", "-m", "v1: /inizio")
    lab.git(lab.autore, "push", "-q", "origin", "main")
    lab.git(lab.utente, "pull", "-q", "--ff-only")
    mio = INIZIO.replace("Leggi l'handoff.\n", "Leggi l'handoff.\nPoi la tabella dei miei progetti e i dischi.\n")
    mio = mio.replace("Apri la sessione.\n\n", "")
    (lab.utente / "commands" / "inizio.md").write_text(mio, encoding="utf-8")
    lab.git(lab.utente, "commit", "-q", "-am", "chore: session sync")
    lab.pubblica(lab.autore, {"commands/inizio.md": lambda t: t.replace("Leggi l'handoff.", "Leggi l'handoff piu' recente.")},
                 "v2: /inizio")
    return lab


def arturo(lab: Lab, *argomenti: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, "-B", str(lab.repo / "bin" / "arturo"), *argomenti], env=lab.env,
                          capture_output=True, text=True, encoding="utf-8", timeout=60)


def con_lab(prova: Callable[[Lab], None], repo: Path, altri: Dict[str, str] = None) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        prova(prepara(repo, Path(tmp), altri))


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
        assert "Poi la tabella dei miei progetti e i dischi." in testo and "dopo la riga di Arturo \"Leggi l'handoff.\"" in testo, \
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
        (lab.utente / "personale" / "inizio.md").write_text("# mie\n", encoding="utf-8")
        hook = lambda prompt: subprocess.run([BASH, str(repo / "hooks" / "inject-now.sh")], input=json.dumps({"prompt": prompt}),
                                             capture_output=True, text=True, env=lab.env, timeout=60).stdout
        assert "PERSONALE:" in hook("/inizio progetto") and "personale/inizio.md" in hook("/inizio"), \
            "P03 /inizio non dice di leggere le aggiunte personali"
        assert "PERSONALE:" not in hook("/fine"), "P03 PERSONALE per un comando senza aggiunte"
        assert "BRIEF:" not in hook("/inizio") and "REGOLA FISSA" not in hook("/inizio"), "P03 il promemoria del brief scatta su un comando"
        # Dal 20/10/2026 il promemoria ha il testo della config ("REGOLA FISSA"), uguale dalle due parti.
        assert "REGOLA FISSA" in hook("sistemami il deploy"), "P03 il promemoria del brief manca su una richiesta"
    con_lab(prova, repo)


def test_p04(repo: Path) -> None:
    r = subprocess.run(["git", "-C", str(repo), "check-ignore", "-q", "--no-index", "personale/inizio.md"], capture_output=True)
    assert r.returncode == 0, "P04 personale/ non è in .gitignore"
    fine = read(repo / "commands" / "fine.md")
    privato = fine[fine.index('if [ "$VIS" = "PRIVATE" ]; then'):fine.index("else", fine.index('if [ "$VIS" = "PRIVATE" ]; then'))]
    assert "personale" in privato, "P04 /fine non porta personale/ verso il remote privato"
    pubblico = fine[fine.index("for p in settings.json"):fine.index("done", fine.index("for p in settings.json"))]
    assert "personale" not in pubblico, "P04 /fine porta personale/ anche verso un remote pubblico"


def test_p05(repo: Path) -> None:
    def prova(lab: Lab) -> None:
        for file in ("hooks/guardia.py", "commands/../settings.json", "commands/non-esiste.md"):
            r = arturo(lab, "personale", "sposta", file)
            assert r.returncode == 2, f"P05 sposta accetta {file}: {r.stdout!r}"
        lab.git(lab.utente, "reset", "-q", "--hard", "HEAD~1")  # la persona non ha ancora salvato niente
        (lab.utente / "commands" / "inizio.md").write_text(INIZIO + "\nMia riga.\n", encoding="utf-8")
        prima = lab.head()
        r = arturo(lab, "personale", "sposta", "commands/inizio.md")
        assert r.returncode == 0 and lab.head() == prima, "P05 una modifica non salvata crea un commit vuoto"
        assert read(lab.utente / "commands" / "inizio.md") == INIZIO and "Mia riga." in read(lab.utente / "personale" / "inizio.md"), \
            "P05 la modifica non salvata non è spostata"
        elenco = arturo(lab, "personale", "elenco").stdout
        assert "personale/inizio.md" in elenco and "Comandi di Arturo modificati in ~/.claude: nessuno" in elenco, \
            f"P05 elenco: {elenco!r}"
        assert "Senza comando" not in elenco, f"P05 un file personale di un comando che c'è risulta orfano: {elenco!r}"
        # Un comando uscito da Arturo lascia il suo file personale senza lettore (16/10/2026).
        (lab.utente / "personale" / "strato.md").write_text("Mia regola.\n", encoding="utf-8")
        elenco = arturo(lab, "personale", "elenco").stdout
        assert "Senza comando (Arturo non ha più /strato): personale/strato.md" in elenco, \
            f"P05 il file personale di un comando uscito non è segnalato: {elenco!r}"
    con_lab(prova, repo)


def test_p06(repo: Path) -> None:
    testo = read(repo / "commands" / "aggiorna.md")
    passo = testo[testo.index("### Passo 2b"):testo.index("## Passo 3")] if "### Passo 2b" in testo else ""
    assert "Non deve fare niente" in passo and "SEPARATO:" in passo, "P06 il Passo 2b non dice che lo spostamento è automatico"
    assert "chiedi il sì" not in passo and "Solo dopo il suo sì" not in passo, "P06 il Passo 2b chiede ancora il sì"
    assert "## Le sue aggiunte, senza aggiornare" in testo and "personale separa" in testo, "P06 manca /aggiorna personale"
    assert "indietro | personale" in testo.split("---")[1], "P06 l'argomento personale non è dichiarato"


def _aggiorna_senza_passi(lab: Lab, repo: Path, codice: str) -> str:
    """Solo /aggiorna: Passo 1 e Passo 3, nessuno spostamento a mano."""
    testo = read(repo / "commands" / "aggiorna.md")
    lab.lancia(blocco(testo, "## Passo 1", codice))
    uscita = lab.lancia(blocco(testo, "## Passo 3", codice))
    assert "APPLICATO" in uscita and "CONFLITTO" not in uscita, \
        f"{codice} con un comando modificato /aggiorna non applica da solo: {uscita[-400:]!r}"
    assert "SEPARATO: /inizio" in uscita, f"{codice} /aggiorna non dice che ha spostato /inizio: {uscita[-400:]!r}"
    assert "handoff piu' recente" in read(lab.utente / "commands" / "inizio.md"), f"{codice} l'aggiornamento di /inizio non è arrivato"
    personale = lab.utente / "personale" / "inizio.md"
    assert personale.exists() and "Poi la tabella dei miei progetti e i dischi." in read(personale), \
        f"{codice} le aggiunte della persona non sono in personale/inizio.md"
    assert lab.config_integra(), f"{codice} la config non è integra"
    return uscita


def test_p08(repo: Path) -> None:
    # Arturo come origin: /aggiorna fa un rebase, e lo spostamento riscrive il commit locale sul comando.
    con_lab(lambda lab: _aggiorna_senza_passi(lab, repo, "P08"), repo)


def gh_finto(lab: Lab, visibilita: str) -> None:
    """`gh repo view` che risponde con la visibilità data: personale/ viaggia solo verso un repository privato."""
    finti = lab.base / "gh-finto"
    finti.mkdir(exist_ok=True)
    (finti / "gh").write_text(f"#!/bin/sh\necho {visibilita}\n", encoding="utf-8")
    (finti / "gh").chmod(0o755)
    lab.env["PATH"] = f"{finti}{os.pathsep}{lab.env.get('PATH', '')}"


def test_p09(repo: Path) -> None:
    # Il caso di chi ha un suo repository privato: Arturo è upstream, /aggiorna fa un merge, i commit pubblicati restano.
    def prova(lab: Lab) -> None:
        pubblicato = lab.head()
        lab.personale()
        gh_finto(lab, "PRIVATE")
        _aggiorna_senza_passi(lab, repo, "P09")
        assert lab.git(lab.utente, "merge-base", "--is-ancestor", pubblicato, "HEAD") == "", "P09 riscritto un commit pubblicato"
    con_lab(prova, repo)


def test_p10(repo: Path) -> None:
    # Il sync fra le macchine della persona non è un aggiornamento di Arturo: non sposta niente.
    def prova(lab: Lab) -> None:
        lab.git(lab.utente, "fetch", "-q", "origin")
        applica = repo / "bin" / "aggiorna-applica.sh"
        r = subprocess.run([BASH, str(applica), str(lab.utente), "sync", "origin/main"], cwd=str(lab.utente), env=lab.env,
                           capture_output=True, text=True, timeout=120)
        assert "SEPARATO" not in r.stdout and not (lab.utente / "personale" / "inizio.md").exists(), \
            f"P10 il sync sposta i comandi: {r.stdout[-300:]!r}"
        assert "Poi la tabella dei miei progetti" in read(lab.utente / "commands" / "inizio.md"), "P10 il sync ha toccato /inizio"
        # Il sync va in conflitto su /inizio e lascia la copia di prova: si scarta, come farebbe la persona.
        subprocess.run([BASH, str(applica), str(lab.utente), "scarta"], cwd=str(lab.utente), env=lab.env,
                       capture_output=True, timeout=120)
        # Lo stesso comando con un aggiornamento vero sposta: il controllo sopra non è verde per caso.
        _aggiorna_senza_passi(lab, repo, "P10")
    con_lab(prova, repo)


def test_p11(repo: Path) -> None:
    # Repository suo non privato: personale/ non viaggerebbe fra le sue macchine, quindi non si sposta niente.
    def prova(lab: Lab) -> None:
        lab.personale()
        gh_finto(lab, "PUBLIC")
        testo = read(repo / "commands" / "aggiorna.md")
        lab.lancia(blocco(testo, "## Passo 1", "P11"))
        prima = lab.head()
        uscita = lab.lancia(blocco(testo, "## Passo 3", "P11"))
        assert "NON SEPARATO" in uscita and "SEPARATO: /inizio" not in uscita, f"P11 separa verso un repository pubblico: {uscita[-300:]!r}"
        assert lab.head() == prima and not (lab.utente / "personale" / "inizio.md").exists(), "P11 ~/.claude è cambiata"
    con_lab(prova, repo)


def test_p12(repo: Path) -> None:
    # Separazione fatta, ma l'aggiornamento va in conflitto su un altro file: ~/.claude non cambia per niente.
    def prova(lab: Lab) -> None:
        lab.git(lab.utente, "commit", "-q", "--allow-empty", "-m", "vuoto")
        (lab.utente / "NOVITA.md").write_text("# mia\n", encoding="utf-8")
        lab.git(lab.utente, "commit", "-q", "-am", "mia NOVITA")
        lab.pubblica(lab.autore, {"NOVITA.md": lambda t: t + "\n## 2026-10-16 — Altra\n"}, "v3: NOVITA")
        testo = read(repo / "commands" / "aggiorna.md")
        lab.lancia(blocco(testo, "## Passo 1", "P12"))
        prima, inizio = lab.head(), read(lab.utente / "commands" / "inizio.md")
        uscita = lab.lancia(blocco(testo, "## Passo 3", "P12"))
        assert "SEPARATO: /inizio" in uscita and "CONFLITTO" in uscita, \
            f"P12 serve una separazione seguita da un conflitto su NOVITA: {uscita[-300:]!r}"
        assert lab.head() == prima and read(lab.utente / "commands" / "inizio.md") == inizio, \
            "P12 con l'aggiornamento annullato la separazione ha cambiato ~/.claude"
        assert not (lab.utente / "personale" / "inizio.md").exists(), "P12 personale/ scritto senza un'applicazione riuscita"
    con_lab(prova, repo)


def test_p13(repo: Path) -> None:
    # Un comando cancellato dalla persona resta cancellato; uno che l'aggiornamento non tocca resta com'è.
    def prova(lab: Lab) -> None:
        lab.git(lab.utente, "rm", "-q", "commands/fine.md")
        (lab.utente / "commands" / "setup.md").write_text("# /setup\n\nPrepara.\nMia riga.\n", encoding="utf-8")
        lab.git(lab.utente, "commit", "-q", "-am", "via /fine, mia riga in /setup")
        lab.pubblica(lab.autore, {"commands/fine.md": lambda t: t + "Poi salva.\n"}, "v3: /fine")
        testo = read(repo / "commands" / "aggiorna.md")
        lab.lancia(blocco(testo, "## Passo 1", "P13"))
        uscita = lab.lancia(blocco(testo, "## Passo 3", "P13"))
        assert "SEPARATO: /inizio" in uscita, f"P13 /inizio, che l'aggiornamento cambia, non è separato: {uscita[-300:]!r}"
        assert "SEPARATO: /fine" not in uscita and "Errore" not in uscita, f"P13 sposta un comando cancellato: {uscita[-300:]!r}"
        assert "Mia riga." in read(lab.utente / "commands" / "setup.md") and not (lab.utente / "personale" / "setup.md").exists(), \
            "P13 sposta un comando che l'aggiornamento non cambia"
        assert not (lab.utente / "commands" / "fine.md").exists(), "P13 il comando cancellato è tornato"
    con_lab(prova, repo, {"fine.md": "# /fine\n\nChiudi.\n", "setup.md": "# /setup\n\nPrepara.\n"})


def test_p14(repo: Path) -> None:
    # personale/ già tracciato (remote privato, /fine fa git add -f): un secondo spostamento non sporca la config.
    def prova(lab: Lab) -> None:
        lab.personale()
        gh_finto(lab, "PRIVATE")
        (lab.utente / "personale").mkdir()
        (lab.utente / "personale" / "inizio.md").write_text("# Aggiunte mie a /inizio\n\nGia' mia.\n", encoding="utf-8")
        lab.git(lab.utente, "add", "-f", "personale")
        lab.git(lab.utente, "commit", "-q", "-m", "session sync con personale")
        uscita = _aggiorna_senza_passi(lab, repo, "P14")
        assert lab.git(lab.utente, "status", "--porcelain", "--untracked-files=no") == "", \
            f"P14 dopo l'aggiornamento la config ha modifiche non salvate: {uscita[-200:]!r}"
        assert "Gia' mia." in read(lab.utente / "personale" / "inizio.md"), "P14 il file personale ha perso le righe di prima"
    con_lab(prova, repo)


def test_p15(repo: Path) -> None:
    # /aggiorna personale segue la regola del Passo 3: con un repository suo non privato non sposta niente.
    def prova(lab: Lab) -> None:
        lab.personale()
        for f in [repo / "bin" / "arturo", *(repo / "bin").glob("*.py")]:  # la CLI vera, fuori da git
            if not (lab.utente / "bin" / f.name).exists():
                shutil.copy(str(f), str(lab.utente / "bin" / f.name))
        codice = blocco(read(repo / "commands" / "aggiorna.md"), "## Le sue aggiunte, senza aggiornare", "P15")
        gh_finto(lab, "PUBLIC")
        prima, inizio = lab.head(), read(lab.utente / "commands" / "inizio.md")
        uscita = lab.lancia(codice)
        assert "NON SEPARATO" in uscita and "SEPARATO: /inizio" not in uscita, \
            f"P15 /aggiorna personale sposta verso un repository pubblico: {uscita[-300:]!r}"
        assert lab.head() == prima and read(lab.utente / "commands" / "inizio.md") == inizio \
            and not (lab.utente / "personale" / "inizio.md").exists(), "P15 ~/.claude è cambiata"
        gh_finto(lab, "PRIVATE")
        uscita = lab.lancia(codice)
        assert "SEPARATO: /inizio" in uscita and (lab.utente / "personale" / "inizio.md").exists(), \
            f"P15 con un repository privato /aggiorna personale non sposta: {uscita[-300:]!r}"
    con_lab(prova, repo)


AVVIO = "#!/bin/bash\necho \"MACCHINA: x\"\necho \"fine avvio\"\n"


def test_p16(repo: Path) -> None:
    # Dal ciclo del lunedì (16/10/2026): una persona aggiunge righe a hooks/session-start.sh e ogni
    # aggiornamento che tocca l'hook va in conflitto. Le righe vanno in personale/, commentate.
    def prova(lab: Lab) -> None:
        (lab.autore / "hooks" / "session-start.sh").write_text(AVVIO, encoding="utf-8")
        lab.git(lab.autore, "add", "-A")
        lab.git(lab.autore, "commit", "-q", "-m", "v3: avvio")
        lab.git(lab.autore, "push", "-q", "origin", "main")
        testo = read(repo / "commands" / "aggiorna.md")
        lab.lancia(blocco(testo, "## Passo 1", "P16"))
        lab.lancia(blocco(testo, "## Passo 3", "P16"))
        avvio = lab.utente / "hooks" / "session-start.sh"
        assert avvio.exists() and read(avvio) == AVVIO, "P16 l'hook di Arturo non è arrivato"
        mio = AVVIO.replace('echo "fine avvio"\n', 'echo "fine avvio"\necho "i miei dischi"\n')
        (lab.utente / "hooks" / "session-start.sh").write_text(mio, encoding="utf-8")
        lab.git(lab.utente, "commit", "-q", "-am", "mio avvio")
        lab.pubblica(lab.autore, {"hooks/session-start.sh": lambda t: t.replace("MACCHINA: x", "MACCHINA: y")}, "v4: avvio")
        r = arturo(lab, "personale", "separa")
        assert r.returncode == 0 and "SEPARATO: hooks/session-start.sh -> personale/session-start.sh" in r.stdout, \
            f"P16 separa non sposta l'hook di sessione: {r.stdout!r} {r.stderr!r}"
        personale = read(lab.utente / "personale" / "session-start.sh")
        assert '#   echo "i miei dischi"' in personale and "\necho \"i miei dischi\"" not in personale, \
            f"P16 la riga spostata non è commentata: {personale!r}"
        assert read(lab.utente / "hooks" / "session-start.sh") == AVVIO, "P16 l'hook non è tornato com'è in Arturo"
        lab.lancia(blocco(testo, "## Passo 1", "P16"))
        uscita = lab.lancia(blocco(testo, "## Passo 3", "P16"))
        assert "APPLICATO" in uscita and "MACCHINA: y" in read(lab.utente / "hooks" / "session-start.sh"), \
            f"P16 dopo lo spostamento l'aggiornamento dell'hook non applica: {uscita[-300:]!r}"
        # L'hook vero di Arturo esegue il file personale in fondo, e un suo errore non ferma l'avvio.
        coda = read(repo / "hooks" / "session-start.sh")
        coda = coda[coda.index("# Le aggiunte della persona"):]
        (lab.utente / "personale" / "session-start.sh").write_text('echo "mio: $PROJECT_NAME"\nfalse\n', encoding="utf-8")
        r = subprocess.run([BASH, "-c", 'PROJECT_NAME=romanzo\n' + coda + '\necho "dopo"'], env=lab.env,
                           capture_output=True, text=True, timeout=60)
        assert "mio: romanzo" in r.stdout and "dopo" in r.stdout and r.returncode == 0, \
            f"P16 l'hook non esegue il file personale, o un suo errore ferma l'avvio: {r.stdout!r} {r.stderr!r}"
    con_lab(prova, repo)


def test_p17(repo: Path) -> None:
    # Una guardia modificata in locale: col sì della persona torna com'è in Arturo, e l'aggiornamento
    # dopo non va in conflitto. Gli hook di sessione e i file fuori da hooks/ si rifiutano.
    def prova(lab: Lab) -> None:
        guardia = lab.utente / "hooks" / "guardia.py"
        guardia.write_text("blocca = False  # troppe conferme\n", encoding="utf-8")
        lab.git(lab.utente, "commit", "-q", "-am", "mia guardia")
        lab.pubblica(lab.autore, {"hooks/guardia.py": lambda t: t + "chiedi = True\n"}, "v3: guardia")
        for file in ("settings.json", "hooks/../settings.json", "hooks/session-start.sh"):
            assert arturo(lab, "personale", "ripristina", file).returncode == 2, f"P17 ripristina accetta {file}"
        r = arturo(lab, "personale", "ripristina", "hooks/guardia.py")
        assert r.returncode == 0 and "RIPRISTINATO" in r.stdout and read(guardia) == "blocca = True\n", \
            f"P17 la guardia non torna com'è in Arturo: {r.stdout!r} {r.stderr!r} {read(guardia)!r}"
        assert lab.git(lab.utente, "status", "--porcelain") == "", "P17 il ripristino lascia modifiche non salvate"
        testo = read(repo / "commands" / "aggiorna.md")
        lab.lancia(blocco(testo, "## Passo 1", "P17"))
        uscita = lab.lancia(blocco(testo, "## Passo 3", "P17"))
        assert "APPLICATO" in uscita and read(guardia) == "blocca = True\nchiedi = True\n", \
            f"P17 dopo il ripristino l'aggiornamento della guardia non applica: {uscita[-300:]!r}"
    con_lab(prova, repo)


def test_p18(repo: Path) -> None:
    # Segnalazione n.3 della v2026-10-16.5 (#3519): /aggiorna diceva di aver spostato le aggiunte all'hook
    # in personale/session-start.sh, ma la copia di prova portava avanti e indietro solo i .md: il file
    # non arrivava in ~/.claude e le righe tolte dall'hook si perdevano. Le aggiunte spostate prima restano.
    def prova(lab: Lab) -> None:
        (lab.autore / "hooks" / "session-start.sh").write_text(AVVIO, encoding="utf-8")
        lab.git(lab.autore, "add", "-A")
        lab.git(lab.autore, "commit", "-q", "-m", "v3: avvio")
        lab.git(lab.autore, "push", "-q", "origin", "main")
        testo = read(repo / "commands" / "aggiorna.md")
        lab.lancia(blocco(testo, "## Passo 1", "P18"))
        lab.lancia(blocco(testo, "## Passo 3", "P18"))
        avvio = lab.utente / "hooks" / "session-start.sh"
        assert avvio.exists() and read(avvio) == AVVIO, "P18 l'hook di Arturo non è arrivato"
        personale = lab.utente / "personale" / "session-start.sh"
        personale.parent.mkdir(exist_ok=True)
        personale.write_text("# Aggiunte mie a hooks/session-start.sh\n\n#   echo \"il mio vecchio avvio\"\n", encoding="utf-8")
        mio = AVVIO.replace('echo "fine avvio"\n', 'echo "fine avvio"\necho "i miei dischi"\n')
        (lab.utente / "hooks" / "session-start.sh").write_text(mio, encoding="utf-8")
        lab.git(lab.utente, "commit", "-q", "-am", "mio avvio")
        lab.pubblica(lab.autore, {"hooks/session-start.sh": lambda t: t.replace("MACCHINA: x", "MACCHINA: y")}, "v4: avvio")
        lab.lancia(blocco(testo, "## Passo 1", "P18"))
        uscita = lab.lancia(blocco(testo, "## Passo 3", "P18"))
        assert "APPLICATO" in uscita and "SEPARATO: hooks/session-start.sh" in uscita, \
            f"P18 /aggiorna non sposta l'hook di sessione: {uscita[-400:]!r}"
        assert "MACCHINA: y" in read(lab.utente / "hooks" / "session-start.sh"), "P18 l'aggiornamento dell'hook non è arrivato"
        testo_mio = read(personale) if personale.exists() else ""
        assert '#   echo "i miei dischi"' in testo_mio, f"P18 le aggiunte all'hook non sono in personale/session-start.sh: {testo_mio!r}"
        assert "il mio vecchio avvio" in testo_mio, f"P18 le aggiunte spostate prima si sono perse: {testo_mio!r}"
        assert lab.config_integra(), "P18 la config non è integra"
    con_lab(prova, repo)


TESTS: Dict[str, Callable[[Path], None]] = {
    "P01": test_p01, "P02": test_p02, "P03": test_p03, "P04": test_p04, "P05": test_p05, "P06": test_p06,
    "P07": test_p07, "P08": test_p08, "P09": test_p09, "P10": test_p10,
    "P11": test_p11, "P12": test_p12, "P13": test_p13, "P14": test_p14, "P15": test_p15,
    "P16": test_p16, "P17": test_p17, "P18": test_p18,
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
