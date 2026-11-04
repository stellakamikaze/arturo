#!/usr/bin/env python3
"""Tiene la skill humanizer agganciata al suo repository d'origine, blader/humanizer (4/11/2026).

Perché esiste: skills/humanizer è l'adattamento italiano di un progetto che cambia. Senza un controllo,
Arturo restava fermo alla versione copiata e nessuno se ne accorgeva. Questo script serve a chi mantiene
Arturo: chi usa Arturo riceve la skill aggiornata con i rilasci, come il resto.

  humanizer-origine.py controlla   confronta l'ultimo commit di main dell'origine con skills/humanizer/ORIGINE.
                                   Tace se sono pari. Se no stampa una riga HUMANIZER: con versione e commit.
  humanizer-origine.py porta       scarica il SKILL.md dell'origine, riscrive references/originale-en.md
                                   (la versione inglese, così com'è) e ORIGINE, e salva in
                                   cache/humanizer-differenza.md la differenza fra il vecchio e il nuovo
                                   originale. Da lì la sessione riporta le stesse modifiche nell'adattamento
                                   italiano (SKILL.md) e aggiorna la riga derivato-da: il banco Q05 resta
                                   rosso finché SKILL.md non nomina il commit nuovo.
  --commit SHA                     con porta: un commit preciso al posto dell'ultimo di main.

Ambiente: HUMANIZER_ORIGINE_URL (default https://github.com/blader/humanizer), ARTURO_REPO_HUMANIZER (la
radice di Arturo, default la cartella sopra bin/; per i banchi). Usa solo git: niente gh, niente token.
Exit 0 anche offline (è un aiuto, non un gate), 2 per un errore d'uso, 1 se porta non riesce.
"""
from __future__ import annotations

import difflib
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

URL = os.environ.get("HUMANIZER_ORIGINE_URL", "https://github.com/blader/humanizer")
RADICE = Path(os.environ.get("ARTURO_REPO_HUMANIZER") or Path(__file__).resolve().parents[1])
SKILL = RADICE / "skills" / "humanizer"
ORIGINE = SKILL / "ORIGINE"
INGLESE = SKILL / "references" / "originale-en.md"
DIFFERENZA = RADICE / "cache" / "humanizer-differenza.md"
GIT_ENV = dict(os.environ, GIT_TERMINAL_PROMPT="0", LANGUAGE="en")


def nome_repo(url: str) -> str:
    m = re.search(r"([^/:]+/[^/]+?)(?:\.git)?/?$", url)
    return m.group(1) if m else url


def leggi_origine() -> dict[str, str]:
    voci = {}
    for riga in ORIGINE.read_text(encoding="utf-8").splitlines():
        if riga.strip() and " " in riga:
            chiave, valore = riga.split(" ", 1)
            voci[chiave] = valore.strip()
    return voci


def ultimo_commit() -> str | None:
    p = subprocess.run(["git", "ls-remote", URL, "refs/heads/main"], capture_output=True, text=True,
                       timeout=30, env=GIT_ENV)
    if p.returncode or not p.stdout.strip():
        return None
    return p.stdout.split()[0]


def skill_al_commit(commit: str) -> str | None:
    """Il SKILL.md dell'origine a quel commit, con un fetch di un solo commit in una cartella temporanea."""
    with tempfile.TemporaryDirectory() as d:
        for comando in (["git", "init", "-q", d], ["git", "-C", d, "fetch", "-q", "--depth", "1", URL, commit]):
            if subprocess.run(comando, capture_output=True, timeout=60, env=GIT_ENV).returncode:
                return None
        p = subprocess.run(["git", "-C", d, "show", "FETCH_HEAD:SKILL.md"], capture_output=True, text=True,
                           encoding="utf-8", timeout=30, env=GIT_ENV)
        return p.stdout if p.returncode == 0 else None


def versione(testo: str) -> str:
    m = re.search(r'^\s*version:\s*"?([^"\n]+)"?\s*$', testo, re.M)
    return m.group(1).strip() if m else "senza versione"


def pari(fissato: str, commit: str) -> bool:
    return bool(fissato) and commit.startswith(fissato)


def controlla() -> int:
    fissato = leggi_origine().get("commit", "")
    commit = ultimo_commit()
    if commit is None:
        print("humanizer-origine: offline, controllo rimandato", file=sys.stderr)
        return 0
    if pari(fissato, commit):
        return 0
    testo = skill_al_commit(commit)
    nuova = versione(testo) if testo else "versione da leggere"
    print(f"HUMANIZER: {nome_repo(URL)} {nuova} ({commit[:7]}) è uscito, Arturo è a "
          f"{leggi_origine().get('versione', '?')} ({fissato[:7]}): python3 bin/humanizer-origine.py porta")
    return 0


def porta(commit: str | None) -> int:
    commit = commit or ultimo_commit()
    if commit is None:
        print("humanizer-origine: l'origine non risponde, niente da portare", file=sys.stderr)
        return 1
    nuovo = skill_al_commit(commit)
    if nuovo is None:
        print(f"humanizer-origine: SKILL.md non leggibile al commit {commit[:7]}", file=sys.stderr)
        return 1
    vecchio = INGLESE.read_text(encoding="utf-8") if INGLESE.exists() else ""
    prima = leggi_origine()
    if vecchio == nuovo and pari(prima.get("commit", ""), commit):
        print("humanizer-origine: già pari, niente da portare")
        return 0
    INGLESE.parent.mkdir(parents=True, exist_ok=True)
    INGLESE.write_text(nuovo, encoding="utf-8")
    ORIGINE.write_text(f"repository {URL}\ncommit {commit[:7]}\nversione {versione(nuovo)}\n", encoding="utf-8")
    righe = list(difflib.unified_diff(vecchio.splitlines(), nuovo.splitlines(),
                                      f"originale {prima.get('versione', '?')} ({prima.get('commit', '?')})",
                                      f"originale {versione(nuovo)} ({commit[:7]})", lineterm=""))
    DIFFERENZA.parent.mkdir(parents=True, exist_ok=True)
    DIFFERENZA.write_text(
        "# Da riportare nell'adattamento italiano (skills/humanizer/SKILL.md)\n\n"
        "Ogni schema cambiato qui va cambiato anche nella versione italiana, con esempi italiani. Poi la riga\n"
        f"derivato-da del frontmatter prende il commit {commit[:7]} e la versione {versione(nuovo)}, e NOVITA.md\n"
        "riceve una voce.\n\n```diff\n" + "\n".join(righe) + "\n```\n", encoding="utf-8")
    print(f"humanizer-origine: portato {nome_repo(URL)} {versione(nuovo)} ({commit[:7]}), {len(righe)} righe di "
          f"differenza in {DIFFERENZA.relative_to(RADICE)}. Adesso l'italiano: skills/humanizer/SKILL.md")
    return 0


def main(argv: list[str]) -> int:
    if argv[:1] == ["controlla"] and len(argv) == 1:
        return controlla()
    if argv[:1] == ["porta"]:
        resto = argv[1:]
        if not resto:
            return porta(None)
        if len(resto) == 2 and resto[0] == "--commit" and re.fullmatch(r"[0-9a-f]{7,40}", resto[1]):
            return porta(resto[1])
    print("uso: humanizer-origine.py controlla | porta [--commit SHA]", file=sys.stderr)
    return 2


if __name__ == "__main__":
    for flusso in (sys.stdout, sys.stderr):
        try:
            flusso.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass
    sys.exit(main(sys.argv[1:]))
