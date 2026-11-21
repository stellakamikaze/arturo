#!/usr/bin/env python3
"""La mappa dei ruoli: quale skill fa quale lavoro (strati F6, #4536, docs/strati.md).

Ogni ruolo di un assistente completo (smistare quello che arriva, la posta, l'agenda, la
manutenzione...) è una skill, senza personaggi. Una skill dichiara il suo ruolo con una riga
`ruolo:` nel frontmatter. All'avvio session-start.sh stampa la riga RUOLI, così la sessione sa quale
skill chiamare anche quando la persona non la nomina.

Le skill vengono da Arturo (skills/ e commands/ accanto a questo file) e dall'Orsa
(~/.claude/skills e ~/.claude/commands). Una skill della persona con lo stesso nome di una di
Arturo prende il suo posto anche qui. Una skill con `disable-model-invocation: true` non entra: il
modello non può chiamarla.

  ruoli.py riga     la riga RUOLI per l'avvio, vuota se nessuna skill ha un ruolo
  ruoli.py elenco   una riga per ruolo: nome<TAB>ruolo<TAB>origine (arturo o orsa)

Solo libreria standard, Python 3.8 o successivo. Non esce mai con un errore: l'avvio non si ferma.
"""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

sys.path.insert(0, str(Path(os.path.realpath(__file__)).parent.parent / "hooks"))
from radici import radice_arturo, radice_orsa  # noqa: E402

LIMITE_RIGA = 900
RUOLO = re.compile(r"^ruolo:[ \t]*(.+?)[ \t]*$", re.M)
SPENTA = re.compile(r"^disable-model-invocation:[ \t]*true[ \t]*$", re.M)


def frontmatter(percorso: Path) -> Optional[str]:
    try:
        testo = percorso.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    testo = testo.replace("\r\n", "\n")
    if not testo.startswith("---\n"):
        return None
    fine = testo.find("\n---", 4)
    return testo[4:fine] if fine > 0 else None


def leggi(percorso: Path) -> Tuple[bool, Optional[str]]:
    """(chiamabile dal modello, ruolo dichiarato o None)."""
    testa = frontmatter(percorso)
    if testa is None:
        return True, None
    if SPENTA.search(testa):
        return False, None
    trovato = RUOLO.search(testa)
    valore = trovato.group(1).strip().strip("\"'").strip() if trovato else ""
    return True, valore or None


def skill_in(radice: Path) -> Dict[str, Path]:
    trovate: Dict[str, Path] = {}
    for comando in sorted((radice / "commands").glob("*.md")):
        trovate[comando.stem] = comando
    for skill in sorted((radice / "skills").glob("*/SKILL.md")):
        trovate[skill.parent.name] = skill
    return trovate


def ruoli() -> List[Tuple[str, str, str]]:
    codice, orsa = radice_arturo(), radice_orsa()
    stesso = os.path.realpath(codice) == os.path.realpath(orsa)
    trovati: Dict[str, Tuple[str, str]] = {}
    for nome, percorso in skill_in(codice).items():
        chiamabile, valore = leggi(percorso)
        if chiamabile and valore:
            trovati[nome] = (valore, "arturo")
    if not stesso:
        for nome, percorso in skill_in(orsa).items():
            chiamabile, valore = leggi(percorso)
            if not chiamabile:
                trovati.pop(nome, None)
            elif valore:
                trovati[nome] = (valore, "orsa")
            elif nome in trovati:
                # Lo stesso nome nell'Orsa prende il posto della skill di Arturo e ne eredita il ruolo.
                trovati[nome] = (trovati[nome][0], "orsa")
    return [(nome, valore, origine) for nome, (valore, origine) in sorted(trovati.items())]


def riga(elenco: List[Tuple[str, str, str]]) -> str:
    if not elenco:
        return ""
    voci = "; ".join(f"{valore} → {nome}" for nome, valore, _ in elenco)
    testo = ("RUOLI: questi lavori hanno una skill. Se la richiesta è uno di questi lavori, chiama la skill "
             f"col tool Skill anche se la persona non la nomina: {voci}.")
    if len(testo) > LIMITE_RIGA:
        testo = testo[:LIMITE_RIGA - 1].rstrip("; ") + "…"
    return testo


def main(argomenti: List[str]) -> int:
    modo = argomenti[0] if argomenti else "riga"
    try:
        elenco = ruoli()
    except Exception:  # noqa: BLE001 - l'avvio non si ferma per la mappa
        return 0
    if modo == "elenco":
        for nome, valore, origine in elenco:
            print(f"{nome}\t{valore}\t{origine}")
        return 0
    testo = riga(elenco)
    if testo:
        print(testo)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
