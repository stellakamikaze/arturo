"""Il file di sessione: ~/.claude/cache/scheda/<sessione>.json, con un solo padrone (revisione 22/11/2026, C1).

Sette scrittori lo riscrivevano ognuno a modo suo, con due gerarchie di fonti che non coincidevano: la sonda
di Volta teneva "volta" e "teletrasporto" fra le fonti decise, l'hook della scheda ne proteggeva solo due, e
una sessione nata da Volta perdeva il progetto al primo file scritto in un'altra cartella. Ora il formato,
l'elenco delle fonti e la regola stanno qui, e ogni scrittore passa da questo modulo o dal verbo
`arturo sessione progetto` (bin/sessione.py). Il formato sta in docs/scheda-sessione.md.

  FONTI             le fonti del progetto, dalla più debole alla più forte, con il rango
  cede(salvata, nuova)   True se una scrittura da `nuova` non deve sostituire un progetto di fonte `salvata`
  imposta_progetto  progetto (e stato) della sessione, con la regola delle fonti
  segna_spostata    il segno `spostata` di Volta, senza toccare il resto

Solo libreria standard, Python 3.8 o successivo.
"""
from __future__ import annotations

import json
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from radici import radice_orsa, scrivi_atomico  # noqa: E402

VERSIONE = 1

# Il rango dice quanto pesa chi ha deciso il progetto. Sotto DECISA una scrittura cede a un progetto già deciso:
# un file toccato o la cartella di lavoro non spostano una sessione che la persona, Volta o il teletrasporto
# hanno già messo su un progetto. "prompt" (il testo dopo /inizio) è la persona che sceglie: sostituisce sempre.
FONTI = {"cartella": 0, "file": 1, "modello": 1, "prompt": 2,
         "teletrasporto": 3, "volta": 3, "inizio": 3, "persona": 3}
DECISA = 3
# I campi che restano finché il progetto è quello che li ha scritti.
SEGNI = ("spostata", "inizio", "sessionId")
SESSIONE = re.compile(r"[\w-]{1,64}")


def cartella() -> Path:
    return radice_orsa() / "cache" / "scheda"


def percorso(sid: str) -> Path:
    return cartella() / f"{sid}.json"


def leggi(sid: str) -> dict:
    """Il file della sessione, come dizionario: vuoto se manca o non si legge. Senza `versione` vale la 0."""
    try:
        dati = json.loads(percorso(sid).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return dati if isinstance(dati, dict) else {}


def cede(salvata, nuova) -> bool:
    """True se una scrittura da `nuova` non deve cambiare un progetto di fonte `salvata`."""
    if nuova not in FONTI:
        return True
    return FONTI.get(salvata or "", 0) >= DECISA and FONTI[nuova] < FONTI["prompt"]


def imposta_progetto(sid: str, progetto: str, fonte=None, stato=None, quando=None, forza: bool = False) -> tuple:
    """(True, "") se ha scritto, altrimenti (False, motivo). Il file non si tocca se la regola dice no.

    `fonte` None con `forza` è una correzione fatta dalla persona (unisci, rinomina): cambia il progetto e
    lascia fonte e segni come sono. `stato` e `quando` restano quelli del file se non li passi."""
    if not SESSIONE.fullmatch(sid or ""):
        return False, f"sessione non valida: {sid!r}"
    if not progetto:
        return False, "progetto vuoto"
    prima = leggi(sid)
    if fonte is not None and fonte not in FONTI:
        return False, f"fonte sconosciuta: {fonte!r} (valgono {', '.join(FONTI)})"
    if not forza and prima.get("progetto") and cede(prima.get("fonte"), fonte):
        if prima["progetto"] != progetto:
            return False, (f"la sessione ha già {prima['progetto']} da una fonte più forte ({prima.get('fonte')}): "
                           f"{fonte} non lo cambia")
        fonte = prima.get("fonte")  # stesso progetto da una fonte più debole: resta la fonte forte
    nuovo = {"stato": stato or prima.get("stato") or "nuova", "progetto": progetto,
             "fonte": fonte or prima.get("fonte") or "", "quando": quando if quando is not None else time.time()}
    if forza and fonte is None:
        nuovo = dict(prima, progetto=progetto)
    elif prima.get("progetto") == progetto and prima.get("fonte") == nuovo["fonte"]:
        nuovo.update({k: prima[k] for k in SEGNI if k in prima})
    nuovo["versione"] = VERSIONE
    try:
        scrivi_atomico(percorso(sid), json.dumps(nuovo, ensure_ascii=False))
    except OSError as e:
        return False, f"scrittura fallita: {e}"
    return True, ""


def segna_spostata(sid: str, su: str, quando=None) -> tuple:
    """Il segno `spostata` {su, quando}: gli altri campi (progetto, fonte, stato) restano come sono."""
    if not SESSIONE.fullmatch(sid or ""):
        return False, f"sessione non valida: {sid!r}"
    if not su:
        return False, "macchina vuota"
    dati = dict(leggi(sid), spostata={"su": su, "quando": quando if quando is not None else time.time()},
                versione=VERSIONE)
    try:
        scrivi_atomico(percorso(sid), json.dumps(dati, ensure_ascii=False))
    except OSError as e:
        return False, f"scrittura fallita: {e}"
    return True, ""
