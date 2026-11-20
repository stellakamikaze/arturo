#!/usr/bin/env python3
"""arturo nome: il nome con cui la persona chiama Arturo, nell'avvio e nei testi.

  arturo nome              il nome di oggi: quello scelto, oppure Arturo
  arturo nome NOME         Claude si presenta e parla di sé con NOME, da questo avvio
  arturo nome togli        torna Arturo
  arturo nome riga         per session-start.sh: la riga NOME per Claude, o niente

Nasce il 16/11/2026 dalla voce "Arturo ti propone uno spazio quando ti serve" (ROADMAP.md, Fase F3 del piano
della catena di prodotto, #5711): nell'Orsa entra un nome tuo per Arturo. Il nome sta in
~/.claude/personale/nome.txt, nell'Orsa: gli aggiornamenti non lo toccano e i file di Arturo restano come
sono. Cambia come Claude parla di sé nelle risposte e nei testi per la persona. I comandi (arturo, /inizio,
/fine), le skill (arturo:...) e i nomi dei file restano quelli di Arturo, perché li scrive il codice.

Un nome è al massimo di tre parole: lettere, spazi, apostrofo, trattino e punto, al massimo LUNGHEZZA caratteri.
Niente a capo né simboli: la riga entra nel contesto di ogni sessione, e un nome lungo o con istruzioni
dentro non ci deve arrivare. Solo libreria standard, Python 3.8 o successivo.
"""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path
from typing import List, Optional

sys.path.insert(0, str(Path(os.path.realpath(__file__)).parent.parent / "hooks"))
from radici import radice_orsa  # noqa: E402

LUNGHEZZA = 30
PREDEFINITO = "Arturo"
VALIDO = re.compile(r"^[^\W\d_](?:[^\W\d_]|[ '.\-])*$")


def file_nome() -> Path:
    return radice_orsa() / "personale" / "nome.txt"


def pulisci(testo: str) -> Optional[str]:
    """Il nome pronto da scrivere, o None se non è un nome."""
    nome = " ".join((testo or "").split())
    if not nome or len(nome) > LUNGHEZZA or not VALIDO.match(nome) or len(nome.split()) > 3:
        return None
    return nome


def leggi() -> Optional[str]:
    """Il nome scelto, o None: un file vuoto, rotto o con un nome non valido vale come nessuna scelta."""
    try:
        righe = file_nome().read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeDecodeError):
        return None
    prima = next((r for r in righe if r.strip() and not r.lstrip().startswith("#")), "")
    nome = pulisci(prima)
    return nome if nome and nome.lower() != PREDEFINITO.lower() else None


def riga() -> str:
    nome = leggi()
    if not nome:
        return ""
    return (f'NOME: la persona ti chiama "{nome}" (lo ha scelto con arturo nome). Usa {nome} quando ti presenti '
            f"e quando parli di te o di Arturo nelle risposte e nei testi per lei. Restano come sono i comandi "
            f"(arturo, /inizio, /fine), le skill arturo:... e i nomi dei file. Per tornare ad Arturo: arturo nome togli")


def main(argv: Optional[List[str]] = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv and argv[0] in ("-h", "--help", "aiuto"):
        print(__doc__.split("\n\n")[1])
        return 0
    if not argv:
        nome = leggi()
        print(f"nome: {nome} (scelto da te, in {file_nome()})" if nome else f"nome: {PREDEFINITO}")
        return 0
    if argv == ["riga"]:
        testo = riga()
        if testo:
            print(testo)
        return 0
    if argv == ["togli"]:
        try:
            file_nome().unlink()
        except FileNotFoundError:
            pass
        except OSError as e:
            print(f"non riesco a togliere {file_nome()}: {e}", file=sys.stderr)
            return 1
        print(f"nome: {PREDEFINITO}, dal prossimo avvio")
        return 0
    nome = pulisci(" ".join(argv))
    if not nome:
        print(f"non è un nome: al massimo tre parole, solo lettere, spazi, apostrofo, trattino e punto, al massimo "
              f"{LUNGHEZZA} caratteri", file=sys.stderr)
        return 3
    f = file_nome()
    f.parent.mkdir(parents=True, exist_ok=True)
    nuovo = f.with_suffix(".txt.nuovo")
    nuovo.write_text(f"# Il nome con cui chiami Arturo (arturo nome). Gli aggiornamenti non lo toccano.\n{nome}\n",
                     encoding="utf-8")
    os.replace(str(nuovo), str(f))
    print(f"nome: {nome}, dal prossimo avvio. In questa sessione lo uso già." if nome.lower() != PREDEFINITO.lower()
          else f"nome: {PREDEFINITO}")
    return 0


if __name__ == "__main__":
    for flusso in (sys.stdout, sys.stderr):
        try:
            flusso.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass
    raise SystemExit(main())
