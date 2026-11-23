#!/usr/bin/env python3
"""Riquadri, barre e tabelle di Arturo per il terminale, uguali su Mac, Linux e Windows (23/11/2026).

Ogni carattere che esce da qui sta nella tabella CP850, quella della console di un Windows italiano o
europeo coi suoi font di sistema (Consolas, Lucida Console, i font raster di cmd). CP850 ha le lettere
accentate maiuscole e minuscole (À, è) e i bordi semplici; CP437, la tabella americana, non ha À. Fuori
da lì un carattere come ╭, ▲ o un emoji diventa un quadratino, oppure occupa due colonne e storce il
bordo. Per questo gli angoli sono
dritti e i segni sono ASCII o del blocco dei bordi. `CARATTERI` è l'elenco ammesso, e i banchi lo
controllano su tutto quello che si disegna.

Ogni riga ha la stessa larghezza in colonne: una riga troppo lunga fa errore, non si taglia in silenzio.
Solo libreria standard, Python 3.8 o successivo.
"""
from __future__ import annotations

from typing import Sequence

ANGOLI = "┌┐└┘"
LINEE = "─│├┤┬┴┼"
BLOCCHI = "█░"
# Tutto quello che il disegno usa oltre all'ASCII stampabile e alle lettere accentate: sta in CP850.
CARATTERI = ANGOLI + LINEE + BLOCCHI
MARGINE = "  "


def larghezza_ok(testo: str) -> bool:
    """Vero se ogni carattere sta in CP850 (ASCII, lettere accentate, bordi semplici) e non è un controllo."""
    try:
        testo.encode("cp850")
    except UnicodeEncodeError:
        return False
    return all(c >= " " for c in testo)


def riquadro(righe: Sequence[str], larghezza: int = 62) -> str:
    """Le righe dentro un bordo, tutte di `larghezza` colonne più il bordo. "---" è un separatore.
    Due colonne di margine a destra, come le tre a sinistra che mette chi scrive la riga."""
    fuori = [MARGINE + "┌" + "─" * larghezza + "┐"]
    for r in righe:
        if r == "---":
            fuori.append(MARGINE + "├" + "─" * larghezza + "┤")
            continue
        if len(r) > larghezza - 2:
            raise ValueError(f"riga del riquadro troppo lunga ({len(r)} su {larghezza - 2}): {r!r}")
        fuori.append(MARGINE + "│" + r.ljust(larghezza) + "│")
    fuori.append(MARGINE + "└" + "─" * larghezza + "┘")
    testo = "\n".join(fuori)
    if not larghezza_ok(testo.replace("\n", "")):
        fuori_tabella = sorted({c for c in testo if c != "\n" and not larghezza_ok(c)})
        raise ValueError(f"caratteri fuori da CP850 nel riquadro: {''.join(fuori_tabella)!r}")
    return testo


def barra(percento: float, colonne: int = 30) -> str:
    """Una barra piena fino a `percento`, vuota dopo."""
    piene = max(0, min(colonne, round(colonne * percento / 100)))
    return "█" * piene + "░" * (colonne - piene)


def segno_sotto(percento: float, testo: str, colonne: int = 30) -> str:
    """La riga sotto la barra con un segno all'altezza dell'ultima colonna piena: "   └ testo"."""
    piene = max(1, min(colonne, round(colonne * percento / 100)))
    return " " * (piene - 1) + "└ " + testo
