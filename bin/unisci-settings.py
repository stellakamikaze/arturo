#!/usr/bin/env python3
"""Unisce settings.json come JSON: il merge driver che usa l'aggiornamento di Arturo (22/10/2026).

Perché esiste: il 21/10 l'aggiornamento è andato in conflitto su settings.json per tutte e due le
installazioni attive. Arturo aveva aggiunto un hook di avvio, e la persona (o un'app come iTerm2 o
ClaudeBar) aveva cambiato righe vicine. Riga per riga git vede un conflitto. Come dati, le due
modifiche stanno insieme: un hook in più di qua, un permesso in più di là.

  unisci-settings.py BASE NOSTRO LORO

Come un merge driver di git (%O %A %B): scrive il risultato in NOSTRO ed esce 0. Esce 1, senza
toccare NOSTRO, se un file non è JSON o se le due parti hanno cambiato in modo diverso la stessa
cosa: allora git segna il conflitto di sempre, e /aggiorna lo risolve con la persona.

Le regole: un valore cambiato da una parte sola vince. Nelle liste si tiene l'ordine della versione
che arriva e si aggiungono gli elementi che l'altra parte ha aggiunto. Un elemento tolto da una
parte e lasciato com'era dall'altra esce. Gli hook si riconoscono dal comando, i gruppi di hook dal
matcher, il resto dal valore intero. Solo libreria standard, Python 3.8 o successivo.
"""
from __future__ import annotations

import json
import sys

MANCA = object()


class Conflitto(Exception):
    pass


def chiave(elemento):
    """Come si riconosce lo stesso elemento in due versioni di una lista."""
    if isinstance(elemento, dict):
        if "command" in elemento:
            return ("comando", elemento["command"])
        if "hooks" in elemento:
            return ("gruppo", elemento.get("matcher"))
    return ("valore", json.dumps(elemento, sort_keys=True, ensure_ascii=False))


def per_chiave(lista):
    visti = {}
    for elemento in lista:
        k = chiave(elemento)
        if k in visti:  # due elementi con la stessa chiave: niente indovinelli
            raise Conflitto(f"due elementi uguali per {k}")
        visti[k] = elemento
    return visti


def unisci_liste(base, nostro, loro):
    b = per_chiave(base if isinstance(base, list) else [])
    n, l = per_chiave(nostro), per_chiave(loro)
    risultato = []
    for k, elemento in l.items():
        if k in n:
            risultato.append(unisci(b.get(k, MANCA), n[k], elemento))
        elif k not in b:
            risultato.append(elemento)  # aggiunto da loro
        elif elemento != b[k]:
            raise Conflitto(f"{k}: tolto da noi, cambiato da loro")
    for k, elemento in n.items():
        if k in l:
            continue
        if k not in b:
            risultato.append(elemento)  # aggiunto da noi
        elif elemento != b[k]:
            raise Conflitto(f"{k}: cambiato da noi, tolto da loro")
    return risultato


def unisci(base, nostro, loro):
    if nostro == loro:
        return nostro
    if base is MANCA and loro is MANCA:  # chiave aggiunta solo da noi
        return nostro
    if base is MANCA and nostro is MANCA:  # chiave aggiunta solo da loro
        return loro
    if base is not MANCA and nostro == base:
        return loro
    if base is not MANCA and loro == base:
        return nostro
    if isinstance(nostro, dict) and isinstance(loro, dict):
        b = base if isinstance(base, dict) else {}
        risultato = {}
        for k in list(loro) + [k for k in nostro if k not in loro]:
            valore = unisci(b.get(k, MANCA), nostro.get(k, MANCA), loro.get(k, MANCA))
            if valore is not MANCA:
                risultato[k] = valore
        return risultato
    if isinstance(nostro, list) and isinstance(loro, list):
        return unisci_liste(base, nostro, loro)
    raise Conflitto("valori diversi da tutte e due le parti")


def leggi(percorso):
    with open(percorso, encoding="utf-8") as f:
        testo = f.read()
    return json.loads(testo) if testo.strip() else {}


def main(argv):
    if len(argv) != 3:
        print(__doc__, file=sys.stderr)
        return 2
    try:
        base, nostro, loro = (leggi(p) for p in argv)
        risultato = unisci(base, nostro, loro)
    except (OSError, ValueError, Conflitto) as errore:
        print(f"settings.json: unione automatica non riuscita ({errore})", file=sys.stderr)
        return 1
    with open(argv[1], "w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(risultato, indent=2, ensure_ascii=False) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
