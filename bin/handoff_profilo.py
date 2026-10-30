"""Il profilo degli handoff e il controllo delle idee "→ memoria" (#4291, 30/10/2026).

hooks/handoff-gate.local dice come sono fatti gli handoff di chi installa Arturo, senza toccare
handoff-gate.sh e handoff-retention.py. Righe `chiave = valore`, `#` per i commenti:

  colonna-id = Ticket   nome della colonna con l'ID dei task (default: ID)
  chi = <regex>         valori ammessi nella colonna Chi, regex estesa su tutta la cella
                        (default: le categorie di bin/todo_store.py e le loro forme per la persona)
  offline = sì          ammette OFFLINE nella colonna ID, per un task non ancora creato (default: no)
  archivio = no         non cerca gli ID nell'archivio dei todo di Arturo: i task stanno altrove
                        (default: sì)

Il file si legge come dati e non si esegue. Un file assente o illeggibile, o una riga fuori
vocabolario, valgono il profilo di Arturo.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

QUI = Path(__file__).resolve().parent
LOCALE = QUI.parent / "hooks" / "handoff-gate.local"
DEFAULT = {"colonna-id": "ID", "chi": "", "offline": "no", "archivio": "sì"}
SI = {"sì", "si", "yes", "1", "true"}


def carica(percorso: Path | None = None) -> dict:
    profilo = dict(DEFAULT)
    try:
        testo = (percorso or LOCALE).read_text(encoding="utf-8")
    except (OSError, ValueError):
        return profilo
    for riga in testo.splitlines():
        if riga.lstrip().startswith("#") or "=" not in riga:
            continue
        chiave, valore = (x.strip() for x in riga.split("=", 1))
        if chiave not in DEFAULT or not valore:
            continue
        if chiave == "chi":
            try:
                re.compile(valore)
            except re.error:
                continue
        profilo[chiave] = valore
    return profilo


def vero(valore: str) -> bool:
    return valore.strip().lower() in SI


def _sezione(testo: str, titolo: str) -> list:
    out, dentro = [], False
    for n, r in enumerate(testo.splitlines(), 1):
        if re.match(r"^##?[ \t]", r):
            dentro = re.match(rf"^## {re.escape(titolo)}[ \t]*$", r) is not None
            continue
        if dentro:
            out.append((n, r))
    return out


def _note_esistenti(cartelle) -> tuple:
    """Gli slug delle note e quelli che aspettano il "salva" in _in-attesa.md, su tutte le cartelle."""
    note, attesa = set(), set()
    for c in cartelle:
        c = Path(c)
        try:
            for p in c.rglob("*.md"):
                if "_archive" not in p.relative_to(c).parts:
                    note.add(p.stem)
            testo = (c / "_in-attesa.md").read_text(encoding="utf-8")
        except (OSError, ValueError):
            continue
        # una nota in attesa sta sotto "## <path>/<slug>.md · data · progetto"
        attesa.update(m.group(1) for m in re.finditer(r"^## (?:\S*/)?([^/\s]+)\.md(?:\s|$)", testo, re.M))
    return note, attesa


def idee_senza_nota(testo: str, cartelle) -> list:
    """Righe rosse: un'idea "→ memoria" senza [[slug]], o con uno slug che non è una nota."""
    rossi, cache = [], None
    for n, r in _sezione(testo, "Idee"):
        if not re.search(r"(→|->)[ \t]*memoria", r):
            continue
        slugs = re.findall(r"\[\[([^\]|]+)", r)
        if not slugs:
            rossi.append(f"riga {n}: idea \"→ memoria\" senza [[slug]] della nota dove è finita")
            continue
        if cache is None:
            cache = _note_esistenti(cartelle)
        note, attesa = cache
        for s in (x.strip() for x in slugs):
            if s not in note and s not in attesa:
                rossi.append(f"riga {n}: [[{s}]] non è una nota della memoria: scrivila o cambia destino")
    return rossi


def cartelle_memoria() -> list:
    sys.path.insert(0, str(QUI.parent / "hooks"))
    try:
        import melchior_match as mm
        return mm.radici()
    except Exception:  # noqa: BLE001 - senza memoria nessuna nota: l'idea resta rossa
        return []
