#!/usr/bin/env python3
"""arturo progetti nuovo: un progetto nuovo, con la sua scheda nella memoria.

Uso: arturo progetti nuovo "NOME" --cosa "di cosa si tratta, in una riga" [--json]

Nasce da Volta il 22/11/2026 (il pulsante "Nuovo progetto" della schermata Progetti). Scrive la scheda
progetto-<slug>.md come arturo memoria scheda, col titolo NOME e la riga in "## Cos'è": da lì il progetto
compare in arturo progetti, in Volta e in /inizio. La cartella del codice e la voce nella fonte dei task
non nascono qui: le crea la prima sessione che ne ha bisogno.
Si rifiuta se lo slug è già un progetto o un suo nome alternativo: arturo memoria scheda lo aggiornerebbe
in silenzio. Un nome di un progetto eliminato è un nome alternativo di Miscellanea, e il rifiuto lo dice.
Volta guarda se questo file c'è per mostrare il pulsante.
Exit: 0 fatto · 2 nome già preso, o memoria spenta · 3 uso sbagliato.
"""
from __future__ import annotations

import contextlib
import io
import json
import os
import sys
from pathlib import Path

QUI = Path(os.path.realpath(__file__)).parent
sys.path.insert(0, str(QUI))
import contesto as cx  # noqa: E402
import progetti as pg  # noqa: E402

MISCELLANEA = "miscellanea"
MAX_TITOLO = 60


def nomi_presi() -> dict:
    """{slug o nome alternativo: slug del progetto} di tutti i progetti che Arturo conosce."""
    presi = {}
    for v in pg.elenco().get("progetti", []):
        s = cx.slug(v.get("slug") or "")
        if not s:
            continue
        presi.setdefault(s, s)
        for a in v.get("alias") or []:
            if cx.slug(a):
                presi.setdefault(cx.slug(a), s)
    for s, t in pg.schede().items():
        presi.setdefault(s, s)
        for a in t.get("alias") or []:
            if cx.slug(a):
                presi.setdefault(cx.slug(a), s)
    return presi


def rifiuta(codice: int, testo: str, come_json: bool, s: str = "") -> int:
    if come_json:
        print(json.dumps({"slug": s, "fatto": False, "rifiuto": testo, "codice": codice}, ensure_ascii=False))
    print(f"Errore: {testo}", file=sys.stderr)
    return codice


def nuovo(nome: str, cosa: str, come_json: bool) -> int:
    nome, cosa = " ".join(nome.split()), " ".join(cosa.split())
    s = cx.slug(nome)
    if not s:
        return rifiuta(3, "il nome deve avere almeno una lettera o una cifra", come_json)
    if not cosa:
        return rifiuta(3, "serve --cosa: di cosa si tratta, in una riga", come_json, s)
    if len(nome) > MAX_TITOLO:
        return rifiuta(3, f"il nome è lungo più di {MAX_TITOLO} caratteri: scrivine uno più corto", come_json, s)
    if s == MISCELLANEA:
        return rifiuta(2, "Miscellanea c'è già: raccoglie i progetti eliminati", come_json, s)
    di = nomi_presi().get(s)
    if di == MISCELLANEA:
        return rifiuta(2, f"{s} è un progetto eliminato, ora in Miscellanea: scegli un altro nome", come_json, s)
    if di:
        return rifiuta(2, f"{s} c'è già" + (f" (è un nome di {di})" if di != s else ""), come_json, s)
    import memoria as me  # noqa: PLC0415
    uscita, errori = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(uscita), contextlib.redirect_stderr(errori):
        codice = me.comando_scheda([s, "--cosa", cosa, "--titolo", nome])
    detto = (errori.getvalue() or uscita.getvalue()).strip().splitlines()
    if codice != 0 or not uscita.getvalue().startswith("scheda creata"):
        return rifiuta(2 if codice in (0, 2, 4, 5) else codice, detto[-1] if detto else f"la scheda di {s} non è nata", come_json, s)
    scheda = me.mm.trova_scheda(s)
    if come_json:
        print(json.dumps({"slug": s, "titolo": nome, "fatto": True, "scheda": str(scheda or "")}, ensure_ascii=False))
    else:
        print(f"Progetto nuovo: {nome} ({s}). Scheda: {scheda}")
    return 0


def main(argv: list) -> int:
    come_json = "--json" in argv
    resto = [a for a in argv if a != "--json"]
    cosa = ""
    if "--cosa" in resto:
        i = resto.index("--cosa")
        if i + 1 >= len(resto):
            return rifiuta(3, 'uso: arturo progetti nuovo "NOME" --cosa "una riga" [--json]', come_json)
        cosa = resto[i + 1]
        resto = resto[:i] + resto[i + 2:]
    if len(resto) != 1 or resto[0].startswith("-"):
        return rifiuta(3, 'uso: arturo progetti nuovo "NOME" --cosa "una riga" [--json]', come_json)
    return nuovo(resto[0], cosa, come_json)


if __name__ == "__main__":
    for flusso in (sys.stdout, sys.stderr):
        if hasattr(flusso, "reconfigure"):
            flusso.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(main(sys.argv[1:]))
