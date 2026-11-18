"""L'aspetto della persona: colori di /dafare e della scheda del terminale, pezzi della barra in basso.

Nasce dalla proposta n. 73 (18/11/2026, #5432). Chi cambiava un colore o un pezzo della barra toccava i file
di Arturo, e ogni aggiornamento glieli riscriveva. I valori stanno invece in ~/.claude/personale/aspetto.json,
fuori da git: gli aggiornamenti non lo toccano. Questo modulo lo legge per la scheda del terminale
(hooks/scheda-terminale.py) e per la CLI (`arturo aspetto`, che il pannello /dafare chiama). La barra
(hooks/statusline.js) lo legge da sola con gli stessi nomi, per non lanciare Python a ogni aggiornamento.

Un valore sbagliato resta fuori e vale quello di Arturo: nessuna superficie si rompe per il file.
Solo libreria standard, Python 3.8 o successivo.
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path
sys.path.append(str(Path(os.path.realpath(__file__)).parent))
from radici import radice_orsa  # noqa: E402

# I nomi che il file può usare: le chiavi della palette C del pannello (skills/arturo/hooks/dafare/register.tsx),
# gli stati della scheda (RGB e DECAC di hooks/scheda-terminale.py), i pezzi della barra (hooks/statusline.js).
COLORI_DAFARE = ("tela", "inchiostro", "cenere", "sera", "passa", "blocca", "arturo")
STATI_SCHEDA = ("nuova", "fermo", "attende", "lavoro", "problema", "chiusa")
PEZZI_BARRA = ("contesto", "quota", "aggiornamento", "chiusa", "task")
ESADECIMALE = re.compile(r"^#[0-9a-fA-F]{6}$")
NOME_FILE = re.compile(r"^[A-Za-z0-9_-]{1,40}\.js$")


def file_aspetto() -> Path:
    return radice_orsa() / "personale" / "aspetto.json"


def _rgb(v) -> bool:
    return (isinstance(v, list) and len(v) == 3
            and all(isinstance(x, int) and not isinstance(x, bool) and 0 <= x <= 255 for x in v))


def leggi(percorso: Path | None = None) -> tuple:
    """(valori validi, errori). Senza file: ({}, []). I valori hanno solo le sezioni con qualcosa dentro."""
    f = percorso or file_aspetto()
    if not f.exists():
        return {}, []
    try:
        dati = json.loads(f.read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        return {}, [f"{f.name} non si legge come JSON: {e}"]
    if not isinstance(dati, dict):
        return {}, [f"{f.name} deve essere un oggetto JSON, con le sezioni dafare, scheda e barra"]
    validi, errori = {}, []
    for sezione in dati:
        if sezione not in ("dafare", "scheda", "barra"):
            errori.append(f"sezione sconosciuta: {sezione} (valgono dafare, scheda, barra)")
    dafare = dati.get("dafare") or {}
    colori = dafare.get("colori") if isinstance(dafare, dict) else None
    for nome, v in (colori or {}).items() if isinstance(colori, dict) else ():
        if nome not in COLORI_DAFARE:
            errori.append(f"dafare.colori.{nome}: colore sconosciuto (valgono {', '.join(COLORI_DAFARE)})")
        elif not (isinstance(v, str) and ESADECIMALE.match(v)):
            errori.append(f"dafare.colori.{nome}: {v!r} non è un colore #rrggbb")
        else:
            validi.setdefault("dafare", {}).setdefault("colori", {})[nome] = v.lower()
    scheda = dati.get("scheda") or {}
    for chiave, buono, spiega in (("colori", _rgb, "tre numeri da 0 a 255"),
                                  ("decac", lambda x: isinstance(x, int) and not isinstance(x, bool) and 0 <= x <= 15,
                                   "un indice da 0 a 15 della tavolozza di Windows Terminal")):
        voci = scheda.get(chiave) if isinstance(scheda, dict) else None
        for stato, v in (voci or {}).items() if isinstance(voci, dict) else ():
            if stato not in STATI_SCHEDA:
                errori.append(f"scheda.{chiave}.{stato}: stato sconosciuto (valgono {', '.join(STATI_SCHEDA)})")
            elif not buono(v):
                errori.append(f"scheda.{chiave}.{stato}: {v!r} non è {spiega}")
            else:
                validi.setdefault("scheda", {}).setdefault(chiave, {})[stato] = v
    barra = dati.get("barra") or {}
    if isinstance(barra, dict):
        spenti = barra.get("spenti") or []
        for pezzo in spenti if isinstance(spenti, list) else [spenti]:
            if pezzo in PEZZI_BARRA:
                validi.setdefault("barra", {}).setdefault("spenti", []).append(pezzo)
            else:
                errori.append(f"barra.spenti: {pezzo!r} non è un pezzo della barra (valgono {', '.join(PEZZI_BARRA)})")
        aggiunta = barra.get("aggiunta")
        if aggiunta is not None:
            if isinstance(aggiunta, str) and NOME_FILE.match(aggiunta):
                validi.setdefault("barra", {})["aggiunta"] = aggiunta
            else:
                errori.append(f"barra.aggiunta: {aggiunta!r} deve essere il nome di un file .js in personale/")
    return validi, errori
