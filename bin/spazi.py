#!/usr/bin/env python3
"""arturo spazi: Arturo propone uno spazio quando vede un segnale nel lavoro, una volta sola e col perché.

  arturo spazi [stato] [--json]     i due spazi: il segnale visto oggi, se è già stato proposto, la risposta
  arturo spazi proponi [--json]     la proposta di oggi, se c'è, e la segna come fatta (arturo contesto)
  arturo spazi si SPAZIO            la persona ha detto sì: lo stato lo ricorda (il passo dopo lo fa Claude)
  arturo spazi no SPAZIO            la persona ha detto no: lo spazio non torna
  arturo spazi spegni | accendi     ferma o riprende le proposte

Nasce il 16/11/2026 dalla voce "Arturo ti propone uno spazio quando ti serve" (ROADMAP.md, Fase F1 del piano
della catena di prodotto, #5711). Gli spazi sono due, e ognuno ha il suo segnale, contato in locale:
- melchior: la memoria è spenta e il lavoro cresce: almeno SOGLIA_HANDOFF handoff, oppure un CLAUDE.md di
  almeno SOGLIA_RIGHE righe. Melchior è la memoria di Arturo: ordina quello che oggi sta sparso e lo ritrova;
- orsa: la persona corregge spesso lo stesso comportamento: la stessa correzione (arturo correzione) in
  almeno SOGLIA_ORSA sessioni diverse degli ultimi 14 giorni. Spostata nel CLAUDE.md, la regola sta
  nell'Orsa, dove gli aggiornamenti non la toccano, e vale in ogni sessione.
Volta non è uno spazio di Arturo: resta una prova di chi mantiene Arturo (16/11/2026, #5703).

Una volta sola: uno spazio proposto non torna, qualunque sia la risposta. Per l'Orsa vale per ogni
correzione: una correzione diversa che si ripete è una proposta nuova.
Quando tace: proposte spente (anche ARTURO_SPAZI=0), /setup mai finito (data/setup-fatto), una proposta
negli ultimi INTERVALLO giorni, nessun segnale. In rotazione arturo contesto non la chiede, come la domanda
dell'intervista, e non la chiede nemmeno quando oggi c'è già quella domanda: una richiesta sola per /inizio.
Lo stato sta in ~/.claude/data/spazi/stato.json, fuori da git: date e risposte, e per l'Orsa le parole
chiave della correzione già proposta, non le frasi della persona. Solo libreria standard, Python 3.8 o
successivo, niente rete.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional

QUI = Path(os.path.realpath(__file__)).parent
sys.path.insert(0, str(QUI))
sys.path.insert(0, str(QUI.parent / "hooks"))
from radici import radice_orsa  # noqa: E402

SPAZI = ("orsa", "melchior")  # l'ordine quando i segnali sono più di uno: prima la correzione che torna
INTERVALLO = 7          # giorni fra una proposta e la successiva
SOGLIA_HANDOFF = 15
SOGLIA_RIGHE = 250
SOGLIA_ORSA = 3
GIORNI_ORSA = 14
SIMILI = 0.5            # quota di parole in comune perché due correzioni siano la stessa
CODICE = QUI.parent

# Parole che non distinguono una correzione da un'altra.
VUOTE = set("""alla alle allo agli anche ancora come con dalla dalle dagli dove fare fai fatto della delle dello
degli nella nelle nello negli niente nulla ogni oppure per perché più poi prima dopo quando quella quelle quello
quelli questa queste questo questi sempre senza solo sono sulla sulle sullo sugli tutta tutte tutti tutto usa
usare devi deve mai non che chi cosa una uno gli lei lui loro mio mia tuo tua suo sua""".split())


# --- Dove sta lo stato -------------------------------------------------------------------------------

def cartella() -> Path:
    return radice_orsa() / "data" / "spazi"


def file_stato() -> Path:
    return cartella() / "stato.json"


def leggi_stato() -> dict:
    try:
        dati = json.loads(file_stato().read_text(encoding="utf-8"))
    except (OSError, ValueError):
        dati = {}
    if not isinstance(dati, dict):
        dati = {}
    if not isinstance(dati.get("proposte"), dict):
        dati["proposte"] = {}
    if not isinstance(dati.get("orsa"), list):
        dati["orsa"] = []
    return dati


def scrivi_stato(dati: dict) -> None:
    c = cartella()
    c.mkdir(parents=True, exist_ok=True)
    gi = c / ".gitignore"
    if not gi.exists():
        gi.write_text("# Lo stato delle proposte degli spazi resta su questo computer.\n*\n", encoding="utf-8")
    nuovo = file_stato().with_suffix(".json.nuovo")
    nuovo.write_text(json.dumps(dati, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    os.replace(str(nuovo), str(file_stato()))


def oggi() -> dt.date:
    forzato = os.environ.get("ARTURO_OGGI", "")  # solo per i banchi
    try:
        return dt.date.fromisoformat(forzato) if forzato else dt.date.today()
    except ValueError:
        return dt.date.today()


def adesso() -> float:
    """L'ora dei segnali: con ARTURO_OGGI, mezzogiorno di quel giorno (banchi)."""
    if os.environ.get("ARTURO_OGGI"):
        return time.mktime(oggi().timetuple()) + 12 * 3600
    return time.time()


def spente(stato: dict) -> bool:
    env = os.environ.get("ARTURO_SPAZI", "").strip()
    if env in ("0", "1"):
        return env == "0"
    return bool(stato.get("spente"))


def setup_fatto() -> bool:
    return (radice_orsa() / "data" / "setup-fatto").is_file()



# --- Il segnale di Melchior: la memoria spenta e il lavoro che cresce ---------------------------------

def memoria_accesa() -> bool:
    try:
        import melchior_match as mm
        return bool(mm.memoria_accesa())
    except Exception:
        return True  # nel dubbio niente proposta: meglio tacere che proporre una cosa già accesa


def segnale_melchior() -> Optional[dict]:
    if memoria_accesa():
        return None
    radice = radice_orsa()
    try:
        handoff = sum(1 for _ in (radice / "data" / "handoffs").rglob("HANDOFF_*.md"))
    except OSError:
        handoff = 0
    try:
        righe = len((radice / "CLAUDE.md").read_text(encoding="utf-8", errors="replace").splitlines())
    except OSError:
        righe = 0
    if handoff >= SOGLIA_HANDOFF:
        perche = f"la memoria è spenta e hai già {handoff} handoff: le decisioni e gli errori visti stanno " \
                 "sparsi fra quei file"
    elif righe >= SOGLIA_RIGHE:
        perche = f"la memoria è spenta e il tuo CLAUDE.md ha {righe} righe: entra intero in ogni sessione, " \
                 "anche le parti che non servono a quel lavoro"
    else:
        return None
    return {"spazio": "melchior", "chiave": "melchior", "perche": perche,
            "proposta": "Melchior, la memoria di Arturo: tiene decisioni, errori già visti e preferenze in note "
                        "piccole, e porta in ogni sessione solo quelle che servono",
            "con_il_si": f"lancia python3 {CODICE / 'bin' / 'arturo'} memoria accendi"}


# --- Il segnale dell'Orsa: la stessa correzione in più sessioni ---------------------------------------

def parole(testo: str) -> set:
    return {w for w in re.findall(r"[a-zàèéìòù0-9]{4,}", testo.lower()) if w not in VUOTE}


def simili(a: set, b: set) -> bool:
    if not a or not b:
        return False
    return len(a & b) / min(len(a), len(b)) >= SIMILI


def correzioni_recenti() -> List[tuple]:
    """(sessione, testo, skill) delle correzioni degli ultimi GIORNI_ORSA giorni (bin/correzioni.py). La skill
    è quella della persona aperta nella sessione quando la correzione è stata scritta, o ""."""
    # data/correzioni dal 18/11/2026 (segnalazione n. 88), cache/correzioni prima: si leggono tutte e due.
    limite = adesso() - GIORNI_ORSA * 86400
    fuori = []
    file = {}
    for radice in (radice_orsa() / "data" / "correzioni", radice_orsa() / "cache" / "correzioni"):
        try:
            for f in radice.glob("*.json"):
                file.setdefault(f.stem, f)  # una sessione presente in tutte e due: vale data/
        except OSError:
            pass
    for f in file.values():
        try:
            if f.stat().st_mtime < limite:
                continue
            voci = json.loads(f.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        for v in voci if isinstance(voci, list) else []:
            if isinstance(v, dict) and isinstance(v.get("testo"), str) and v["testo"].strip():
                skill = v.get("skill")
                skill = skill if isinstance(skill, str) and re.fullmatch(r"[a-z0-9][a-z0-9-]{0,63}", skill) else ""
                fuori.append((f.stem, v["testo"].strip(), skill))
    return fuori


def segnale_orsa(stato: dict) -> Optional[dict]:
    gia = [set(p) for p in stato["orsa"] if isinstance(p, list)]
    gruppi: List[Dict] = []
    for sessione, testo, skill in correzioni_recenti():
        p = parole(testo)
        if not p or any(simili(p, g) for g in gia):
            continue
        for g in gruppi:
            if simili(p, g["parole"]):
                g["sessioni"].add(sessione)
                break
        else:
            g = {"parole": p, "sessioni": {sessione}, "testo": testo, "skill": {}}
            gruppi.append(g)
        if skill:
            g["skill"].setdefault(skill, set()).add(sessione)
    gruppi = [g for g in gruppi if len(g["sessioni"]) >= SOGLIA_ORSA]
    if not gruppi:
        return None
    g = max(gruppi, key=lambda x: len(x["sessioni"]))
    testo = " ".join(g["testo"].split())[:160]
    perche = (f"in {len(g['sessioni'])} sessioni degli ultimi {GIORNI_ORSA} giorni hai dovuto "
              f"correggere la stessa cosa: \"{testo}\"")
    # La correzione è nata dentro una skill della persona nella maggior parte delle sessioni: la regola sta
    # meglio lì che nel CLAUDE.md, dove peserebbe su ogni sessione (21/11/2026, #6277).
    skill = max(g["skill"], key=lambda n: (len(g["skill"][n]), n)) if g["skill"] else ""
    if skill and 2 * len(g["skill"][skill]) > len(g["sessioni"]) \
            and (radice_orsa() / "skills" / skill / "SKILL.md").is_file():
        return {"spazio": "orsa", "chiave": "orsa", "parole": sorted(g["parole"]),
                "perche": perche + f", mentre usavi la tua skill {skill}",
                "proposta": f"scrivere questa regola nella tua skill {skill} (~/.claude/skills/{skill}/SKILL.md), "
                            "in \"Cosa non fare\" o in \"Finito quando\": lì vale ogni volta che quel lavoro torna, "
                            "senza pesare sulle altre sessioni",
                "con_il_si": f"scrivi la regola in una riga, mostrala e col suo sì aggiungila al SKILL.md di {skill}"}
    return {"spazio": "orsa", "chiave": "orsa", "parole": sorted(g["parole"]),
            "perche": perche,
            "proposta": "spostare questa regola nell'Orsa, cioè nel tuo CLAUDE.md: lì vale in ogni sessione e "
                        "gli aggiornamenti di Arturo non la toccano",
            "con_il_si": "scrivi la regola in una riga, mostrala e col suo sì aggiungila al CLAUDE.md della persona"}


# --- La proposta di oggi -----------------------------------------------------------------------------

def perche_tace(stato: dict) -> Optional[str]:
    if spente(stato):
        return "spente"
    if not setup_fatto():
        return "/setup non è ancora finito"
    ultima = stato.get("ultima")
    try:
        if ultima and (oggi() - dt.date.fromisoformat(ultima)).days < INTERVALLO:
            return f"una proposta il {ultima}: la prossima dopo {INTERVALLO} giorni"
    except ValueError:
        pass
    return None


def segnali(stato: dict) -> List[dict]:
    """I segnali di oggi, nell'ordine di SPAZI, senza gli spazi già proposti."""
    fuori = []
    for spazio in SPAZI:
        if spazio != "orsa" and spazio in stato["proposte"]:
            continue
        segnale = segnale_orsa(stato) if spazio == "orsa" else segnale_melchior()
        if segnale:
            fuori.append(segnale)
    return fuori


def proponi() -> Optional[dict]:
    """La proposta di oggi per /inizio, o None. Se c'è, la segna: lo spazio non torna."""
    stato = leggi_stato()
    if perche_tace(stato):
        return None
    elenco = segnali(stato)
    if not elenco:
        return None
    s = elenco[0]
    stato["proposte"][s["spazio"]] = {"data": oggi().isoformat(), "risposta": None}
    if s["spazio"] == "orsa":
        stato["orsa"].append(s["parole"])
    stato["ultima"] = oggi().isoformat()
    scrivi_stato(stato)
    return s


def righe_contesto(s: dict) -> List[str]:
    """Il blocco SPAZIO di arturo contesto."""
    return ["SPAZIO (una proposta sola per spazio, col segnale che l'ha fatta nascere)",
            f"  spazio: {s['spazio']} · perché: {s['perche']}",
            f"  proposta: {s['proposta']}",
            f"  col sì: {s['con_il_si']}, poi arturo spazi si {s['spazio']} · col no: arturo spazi no "
            f"{s['spazio']} · basta: arturo spazi spegni"]


# --- I comandi ---------------------------------------------------------------------------------------

def comando_stato(come_json: bool) -> int:
    stato = leggi_stato()
    tace = perche_tace(stato)
    visti = {s["spazio"]: s["perche"] for s in segnali(stato)}
    dati = {"accese": not spente(stato), "tace": tace, "segnali": visti,
            "proposte": stato["proposte"]}
    if come_json:
        print(json.dumps(dati, ensure_ascii=False))
        return 0
    print(f"spazi: {'accese' if dati['accese'] else 'spente'}" + (f" · oggi tace: {tace}" if tace else ""))
    for spazio in SPAZI:
        p = stato["proposte"].get(spazio)
        fatta = f"proposto il {p['data']}" + (f", risposta: {p['risposta']}" if p.get("risposta") else "") \
            if isinstance(p, dict) else "mai proposto"
        segnale = visti.get(spazio, "nessun segnale")
        print(f"{spazio}: {fatta} · {segnale}")
    return 0


def comando_proponi(come_json: bool) -> int:
    s = proponi()
    if come_json:
        print(json.dumps(s, ensure_ascii=False))
    elif s:
        print("\n".join(righe_contesto(s)))
    else:
        print(f"nessuna proposta oggi: {perche_tace(leggi_stato()) or 'nessun segnale'}")
    return 0


def comando_risposta(spazio: str, risposta: str) -> int:
    if spazio not in SPAZI:
        print(f'spazio "{spazio}" sconosciuto: usa {", ".join(SPAZI)}', file=sys.stderr)
        return 3
    stato = leggi_stato()
    voce = stato["proposte"].setdefault(spazio, {"data": oggi().isoformat()})
    voce["risposta"] = risposta
    voce["risposta_data"] = oggi().isoformat()
    scrivi_stato(stato)
    print(f"{spazio}: risposta {risposta}, la proposta non torna")
    return 0


def comando_interruttore(accese: bool) -> int:
    stato = leggi_stato()
    stato["spente"] = not accese
    scrivi_stato(stato)
    print("proposte degli spazi accese" if accese
          else "proposte degli spazi spente: /inizio non ne fa più. Per riprenderle: arturo spazi accendi")
    return 0


def main(argv: Optional[List[str]] = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    p = argparse.ArgumentParser(prog="arturo spazi", add_help=False)
    p.add_argument("comando", nargs="?", default="stato")
    p.add_argument("valore", nargs="?")
    p.add_argument("--json", action="store_true")
    p.add_argument("-h", "--help", action="store_true")
    try:
        a = p.parse_args(argv)
    except SystemExit:
        print(__doc__.split("\n\n")[1], file=sys.stderr)
        return 3
    if a.help:
        print(__doc__.split("\n\n")[1])
        return 0
    if a.comando == "stato":
        return comando_stato(a.json)
    if a.comando == "proponi":
        return comando_proponi(a.json)
    if a.comando in ("spegni", "accendi"):
        return comando_interruttore(a.comando == "accendi")
    if a.comando in ("si", "sì", "no"):
        if not a.valore:
            print(f"uso: arturo spazi {a.comando} {'|'.join(SPAZI)}", file=sys.stderr)
            return 3
        return comando_risposta(a.valore, "no" if a.comando == "no" else "sì")
    print(f'comando "{a.comando}" sconosciuto\n' + __doc__.split("\n\n")[1], file=sys.stderr)
    return 3


if __name__ == "__main__":
    for flusso in (sys.stdout, sys.stderr):
        try:
            flusso.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass
    raise SystemExit(main())
