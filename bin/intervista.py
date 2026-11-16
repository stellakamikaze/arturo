#!/usr/bin/env python3
"""arturo intervista: l'intervista che continua dopo /setup, una domanda alla volta.

  arturo intervista [stato] [--json]          accesa o spenta, famiglia, giorni che restano, la prossima domanda
  arturo intervista proponi [--json]          la domanda di oggi, se c'è, e la segna come fatta (arturo contesto)
  arturo intervista risposta ID [--testo T]   col sì della persona, la risposta entra nella memoria come nota
                                              persona-ID (tipo user); senza --testo la legge da stdin
  arturo intervista salta ID                  la domanda non torna più
  arturo intervista famiglia N|NOME|nessuna   fissa la famiglia di mestiere (1-6, o parola, immagine, ...)
  arturo intervista spegni | accendi          ferma o riprende l'intervista

Nasce il 15/11/2026 dalla voce "L'intervista che continua" (ROADMAP.md, Fase C del piano della catena di
prodotto, #5709). /setup intervista la persona una volta. Dopo, /inizio fa al massimo una domanda al giorno,
quindi al massimo una per sessione, sulle cose che Arturo non sa ancora: cosa fa, per chi, come.

Le domande stanno in docs/mestieri.md, fonte unica per chi legge e per questo script: "Le domande per tutti"
e, per ogni famiglia, "Le domande dell'intervista", con le parole che la riconoscono in un commento HTML.
Una domanda è un vuoto se:
- non ha avuto risposta e non è stata saltata (data/intervista/stato.json);
- la memoria non ha già la nota persona-ID, anche scritta da un altro computer;
- il CLAUDE.md della persona non ha già la sezione che la domanda copre ("copre: Chi sono").
La famiglia viene da "intervista famiglia", altrimenti dalle parole della sezione "Chi sono" del CLAUDE.md e
dai temi dell'indice dello storico (data/storico/indice.json). Senza famiglia restano le domande per tutti.

Quando tace: intervista spenta (anche ARTURO_INTERVISTA=0), memoria spenta (la risposta non si potrebbe
salvare), /setup mai finito (data/setup-fatto), oltre GIORNI giorni dal setup, già una domanda oggi.
Una domanda proposta due volte senza risposta conta come saltata.
Lo stato sta in ~/.claude/data/intervista/stato.json, fuori da git: niente testo delle risposte, solo id e
date. Il testo della risposta sta solo nella nota della memoria. Solo libreria standard, Python 3.8 o successivo.
"""
from __future__ import annotations

import argparse
import datetime as dt
import io
import json
import os
import re
import sys
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from typing import Dict, List, Optional, Tuple

QUI = Path(os.path.realpath(__file__)).parent
sys.path.insert(0, str(QUI))
sys.path.insert(0, str(QUI.parent / "hooks"))
from radici import radice_orsa  # noqa: E402

GIORNI = 42          # sei settimane dopo /setup: la durata è una scelta aperta della roadmap (#5709)
PROPOSTE_MASSIME = 2  # una domanda proposta due volte senza risposta non torna
PREFISSO_NOTA = "persona-"
MESTIERI = QUI.parent / "docs" / "mestieri.md"
FAMIGLIE = ("parola", "immagine", "insegnamento", "produzione", "consulenza", "archivio")
ORDINE_GENERALI = (("mestiere", "committenti"), ("ricorrente", "consegna"))  # prima e dopo quelle della famiglia


# --- Le domande da docs/mestieri.md ---------------------------------------------------------------------

_DOMANDA = re.compile(r"^- `([a-z0-9-]+)`(?: \(copre: ([^)]+)\))?: (.+)$")
_TITOLO_FAMIGLIA = re.compile(r"^## (\d)\. (.+)$")
_PAROLE = re.compile(r"^<!-- parole: (.+) -->$")


def leggi_mestieri(percorso: Path = MESTIERI) -> dict:
    """{"generali": [domanda], "famiglie": {chiave: {"numero", "titolo", "domande", "parole"}}}.
    Una domanda è {"id", "testo", "copre"}. Un file mancante dà un elenco vuoto: l'intervista tace."""
    try:
        righe = percorso.read_text(encoding="utf-8").splitlines()
    except OSError:
        return {"generali": [], "famiglie": {}}
    generali: List[dict] = []
    famiglie: Dict[str, dict] = {}
    corrente: Optional[dict] = None
    in_generali = False
    for riga in righe:
        riga = riga.rstrip()
        if riga.startswith("## "):
            m = _TITOLO_FAMIGLIA.match(riga)
            in_generali = riga == "## Le domande per tutti"
            corrente = None
            if m and 1 <= int(m.group(1)) <= len(FAMIGLIE):
                chiave = FAMIGLIE[int(m.group(1)) - 1]
                corrente = {"numero": int(m.group(1)), "titolo": m.group(2).strip(), "domande": [], "parole": []}
                famiglie[chiave] = corrente
            continue
        d = _DOMANDA.match(riga)
        if d:
            domanda = {"id": d.group(1), "testo": d.group(3).strip(), "copre": (d.group(2) or "").strip()}
            if in_generali:
                generali.append(domanda)
            elif corrente is not None:
                corrente["domande"].append(domanda)
            continue
        p = _PAROLE.match(riga)
        if p and corrente is not None:
            corrente["parole"] = [w.strip().lower() for w in p.group(1).split(",") if w.strip()]
    return {"generali": generali, "famiglie": famiglie}


# --- Dove sta lo stato -------------------------------------------------------------------------------

def cartella() -> Path:
    return radice_orsa() / "data" / "intervista"


def file_stato() -> Path:
    return cartella() / "stato.json"


def leggi_stato() -> dict:
    try:
        dati = json.loads(file_stato().read_text(encoding="utf-8"))
    except (OSError, ValueError):
        dati = {}
    if not isinstance(dati, dict):
        dati = {}
    for chiave in ("risposte", "saltate", "proposte"):
        if not isinstance(dati.get(chiave), dict):
            dati[chiave] = {}
    return dati


def scrivi_stato(dati: dict) -> None:
    c = cartella()
    c.mkdir(parents=True, exist_ok=True)
    gi = c / ".gitignore"
    if not gi.exists():
        gi.write_text("# Lo stato dell'intervista resta su questo computer.\n*\n", encoding="utf-8")
    nuovo = file_stato().with_suffix(".json.nuovo")
    nuovo.write_text(json.dumps(dati, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    os.replace(str(nuovo), str(file_stato()))


def oggi() -> dt.date:
    forzato = os.environ.get("ARTURO_OGGI", "")  # solo per i banchi
    try:
        return dt.date.fromisoformat(forzato) if forzato else dt.date.today()
    except ValueError:
        return dt.date.today()


# --- Cosa Arturo sa già -------------------------------------------------------------------------------

def giorno_setup() -> Optional[dt.date]:
    try:
        testo = (radice_orsa() / "data" / "setup-fatto").read_text(encoding="utf-8")
    except OSError:
        return None
    m = re.search(r"\d{4}-\d{2}-\d{2}", testo)
    try:
        return dt.date.fromisoformat(m.group(0)) if m else None
    except ValueError:
        return None


def sezioni_claude_md() -> Dict[str, str]:
    """Le sezioni del CLAUDE.md della persona, titolo in minuscolo -> testo. Il CLAUDE.md è suo: si legge e basta."""
    try:
        testo = (radice_orsa() / "CLAUDE.md").read_text(encoding="utf-8")
    except OSError:
        return {}
    sezioni: Dict[str, List[str]] = {}
    titolo = None
    for riga in testo.splitlines():
        m = re.match(r"^#{1,4}\s+(.+?)\s*$", riga)
        if m:
            titolo = re.sub(r"^\d+[.)]\s*", "", m.group(1)).strip().lower()
            sezioni.setdefault(titolo, [])
        elif titolo is not None:
            sezioni[titolo].append(riga)
    return {t: "\n".join(r).strip() for t, r in sezioni.items()}


def temi_storico() -> str:
    try:
        dati = json.loads((radice_orsa() / "data" / "storico" / "indice.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return ""
    parti = []
    for lavoro in dati.get("lavori", []) if isinstance(dati, dict) else []:
        if isinstance(lavoro, dict):
            parti.append(str(lavoro.get("titolo", "")))
            temi = lavoro.get("temi", [])
            parti.extend(str(t) for t in temi if isinstance(temi, list))
    return " ".join(parti)


def _conta(testo: str, parole: List[str]) -> int:
    testo = testo.lower()
    return sum(len(re.findall(r"(?<![a-zàèéìòù])" + re.escape(p), testo)) for p in parole)


def famiglia_dedotta(mestieri: dict) -> Tuple[Optional[str], str]:
    """(famiglia, fonte). La sezione "Chi sono" del CLAUDE.md pesa il doppio dei temi dello storico.
    Un pareggio in cima non sceglie: meglio le domande per tutti che una famiglia sbagliata."""
    chi = next((t for s, t in sezioni_claude_md().items() if s.startswith("chi sono")), "")
    storico = temi_storico()
    punti = []
    for chiave, f in mestieri["famiglie"].items():
        a, b = _conta(chi, f["parole"]), _conta(storico, f["parole"])
        punti.append((2 * a + b, a, chiave))
    punti.sort(reverse=True)
    if not punti or punti[0][0] == 0 or (len(punti) > 1 and punti[1][0] == punti[0][0]):
        return None, ""
    return punti[0][2], "dal CLAUDE.md" if punti[0][1] else "dallo storico delle chat"


def note_persona() -> set:
    """I nomi delle note persona-* nella memoria, in ogni cartella fuori dall'archivio."""
    radice = radice_orsa() / "data" / "memory"
    if not radice.is_dir():
        return set()
    return {p.stem for p in radice.rglob(PREFISSO_NOTA + "*.md") if "_archive" not in p.parts}


def memoria_accesa() -> bool:
    try:
        import melchior_match as mm
        return bool(mm.memoria_accesa())
    except Exception:
        return False


def spenta(stato: dict) -> bool:
    env = os.environ.get("ARTURO_INTERVISTA", "").strip()
    if env in ("0", "1"):
        return env == "0"
    return bool(stato.get("spenta"))


# --- La domanda di oggi ------------------------------------------------------------------------------

def famiglia(stato: dict, mestieri: dict) -> Tuple[Optional[str], str]:
    scelta = stato.get("famiglia")
    if scelta == "nessuna":
        return None, "scelta: nessuna"
    if scelta in mestieri["famiglie"]:
        return scelta, "scelta"
    return famiglia_dedotta(mestieri)


def domande_in_ordine(mestieri: dict, fam: Optional[str]) -> List[dict]:
    per_id = {d["id"]: d for d in mestieri["generali"]}
    prima = [per_id[i] for i in ORDINE_GENERALI[0] if i in per_id]
    dopo = [per_id[i] for i in ORDINE_GENERALI[1] if i in per_id]
    altre = [d for d in mestieri["generali"] if d["id"] not in ORDINE_GENERALI[0] + ORDINE_GENERALI[1]]
    proprie = mestieri["famiglie"][fam]["domande"] if fam in mestieri["famiglie"] else []
    return prima + proprie + dopo + altre


def vuoti(stato: dict, mestieri: dict, fam: Optional[str]) -> List[dict]:
    sezioni = sezioni_claude_md()
    gia = note_persona()
    fuori = []
    for d in domande_in_ordine(mestieri, fam):
        i = d["id"]
        if i in stato["risposte"] or i in stato["saltate"] or PREFISSO_NOTA + i in gia:
            continue
        if stato["proposte"].get(i, {}).get("volte", 0) >= PROPOSTE_MASSIME:
            continue
        copre = d["copre"].lower()
        if copre and any(s.startswith(copre) and t for s, t in sezioni.items()):
            continue
        fuori.append(d)
    return fuori


def perche_tace(stato: dict) -> Optional[str]:
    if spenta(stato):
        return "spenta"
    if not memoria_accesa():
        return "memoria spenta: la risposta non si potrebbe salvare"
    inizio = giorno_setup()
    if inizio is None:
        return "/setup non è ancora finito"
    passati = (oggi() - inizio).days
    if passati > GIORNI:
        return f"finita: sono passati {passati} giorni da /setup (dura {GIORNI})"
    if stato.get("ultima") == oggi().isoformat():
        return "già una domanda oggi"
    return None


def prossima(stato: dict, mestieri: Optional[dict] = None) -> Tuple[Optional[dict], Optional[str], str]:
    """(domanda, famiglia, fonte della famiglia) senza scrivere niente."""
    mestieri = mestieri or leggi_mestieri()
    fam, fonte = famiglia(stato, mestieri)
    elenco = vuoti(stato, mestieri, fam)
    return (elenco[0] if elenco else None), fam, fonte


def proponi() -> Optional[dict]:
    """La domanda di oggi per /inizio, o None. Se c'è, la segna: oggi non ne esce un'altra."""
    stato = leggi_stato()
    if perche_tace(stato):
        return None
    mestieri = leggi_mestieri()
    domanda, fam, fonte = prossima(stato, mestieri)
    if domanda is None:
        return None
    voce = stato["proposte"].setdefault(domanda["id"], {"volte": 0})
    voce["volte"] = int(voce.get("volte", 0)) + 1
    voce["ultima"] = oggi().isoformat()
    stato["ultima"] = oggi().isoformat()
    scrivi_stato(stato)
    titolo = mestieri["famiglie"][fam]["titolo"] if fam else ""
    return {"id": domanda["id"], "testo": domanda["testo"], "famiglia": fam or "", "titolo_famiglia": titolo,
            "fonte_famiglia": fonte}


def righe_contesto(d: dict) -> List[str]:
    """Il blocco INTERVISTA di arturo contesto."""
    fam = f"{d['titolo_famiglia'].lower()} ({d['fonte_famiglia']})" if d["famiglia"] else "per tutti"
    return ["INTERVISTA (al massimo una domanda al giorno, dopo /setup)",
            f"  domanda: {d['id']} · {fam} · {d['testo']}",
            f"  col sì sulla nota: arturo intervista risposta {d['id']} --testo \"...\" · "
            f"salta: arturo intervista salta {d['id']} · basta: arturo intervista spegni"]


# --- I comandi ---------------------------------------------------------------------------------------

def _trova(mestieri: dict, ident: str) -> Optional[dict]:
    for d in mestieri["generali"] + [x for f in mestieri["famiglie"].values() for x in f["domande"]]:
        if d["id"] == ident:
            return d
    return None


def comando_stato(come_json: bool) -> int:
    stato = leggi_stato()
    mestieri = leggi_mestieri()
    domanda, fam, fonte = prossima(stato, mestieri)
    tace = perche_tace(stato)
    inizio = giorno_setup()
    dati = {"accesa": not spenta(stato), "tace": tace, "famiglia": fam, "fonte_famiglia": fonte,
            "setup": inizio.isoformat() if inizio else None, "giorni": GIORNI,
            "risposte": sorted(stato["risposte"]), "saltate": sorted(stato["saltate"]),
            "prossima": domanda["id"] if domanda else None}
    if come_json:
        print(json.dumps(dati, ensure_ascii=False))
        return 0
    print(f"intervista: {'accesa' if dati['accesa'] else 'spenta'}" + (f" · oggi tace: {tace}" if tace else ""))
    titolo = mestieri["famiglie"][fam]["titolo"].lower() if fam else "non ancora nota (domande per tutti)"
    print(f"famiglia: {titolo}" + (f" · {fonte}" if fonte and fam else ""))
    if inizio:
        restano = GIORNI - (oggi() - inizio).days
        print(f"setup: {inizio.isoformat()} · " + (f"restano {restano} giorni" if restano >= 0 else "finita"))
    print(f"risposte: {len(dati['risposte'])} · saltate: {len(dati['saltate'])}")
    print(f"prossima: {domanda['id']} · {domanda['testo']}" if domanda else "prossima: nessuna, i vuoti sono coperti")
    return 0


def comando_proponi(come_json: bool) -> int:
    d = proponi()
    if come_json:
        print(json.dumps(d, ensure_ascii=False))
    elif d:
        print("\n".join(righe_contesto(d)))
    else:
        print(f"nessuna domanda oggi: {perche_tace(leggi_stato()) or 'i vuoti sono coperti'}")
    return 0


def comando_risposta(ident: str, testo: Optional[str]) -> int:
    mestieri = leggi_mestieri()
    d = _trova(mestieri, ident)
    if d is None:
        print(f'domanda "{ident}" sconosciuta: le domande stanno in docs/mestieri.md', file=sys.stderr)
        return 3
    if testo is None:
        testo = "" if sys.stdin is None or sys.stdin.isatty() else sys.stdin.read()
    testo = (testo or "").strip()
    if not testo:
        print("serve il testo della risposta, approvato dalla persona", file=sys.stderr)
        return 3
    import memoria  # bin/memoria.py: lo schema, lo scanner e l'annuncio di /fine sono i suoi
    corpo = f"Domanda dell'intervista ({ident}): {d['testo']}\n\n{testo}"
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        rc = memoria.comando_nota(["--tipo", "user", "--nome", PREFISSO_NOTA + ident,
                                   "--descrizione", f"Intervista: {d['testo']}", "--testo", corpo])
    sys.stdout.write(out.getvalue())
    sys.stderr.write(err.getvalue())
    if rc != 0:
        return rc
    stato = leggi_stato()
    stato["risposte"][ident] = oggi().isoformat()
    scrivi_stato(stato)
    return 0


def comando_salta(ident: str) -> int:
    if _trova(leggi_mestieri(), ident) is None:
        print(f'domanda "{ident}" sconosciuta: le domande stanno in docs/mestieri.md', file=sys.stderr)
        return 3
    stato = leggi_stato()
    stato["saltate"][ident] = oggi().isoformat()
    scrivi_stato(stato)
    print(f"la domanda {ident} non torna più")
    return 0


def comando_famiglia(valore: str) -> int:
    mestieri = leggi_mestieri()
    v = valore.strip().lower()
    if v.isdigit() and 1 <= int(v) <= len(FAMIGLIE):
        v = FAMIGLIE[int(v) - 1]
    if v != "nessuna" and v not in mestieri["famiglie"]:
        print(f'famiglia "{valore}" sconosciuta: usa 1-6, {", ".join(FAMIGLIE)} o nessuna', file=sys.stderr)
        return 3
    stato = leggi_stato()
    stato["famiglia"] = v
    scrivi_stato(stato)
    print("famiglia: " + (mestieri["famiglie"][v]["titolo"].lower() if v != "nessuna" else "nessuna, solo le domande per tutti"))
    return 0


def comando_interruttore(accesa: bool) -> int:
    stato = leggi_stato()
    stato["spenta"] = not accesa
    scrivi_stato(stato)
    print("intervista accesa: /inizio riprende le domande" if accesa
          else "intervista spenta: /inizio non fa più domande. Per riprenderla: arturo intervista accendi")
    return 0


def main(argv: Optional[List[str]] = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    p = argparse.ArgumentParser(prog="arturo intervista", add_help=False)
    p.add_argument("comando", nargs="?", default="stato")
    p.add_argument("valore", nargs="?")
    p.add_argument("--testo")
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
    if a.comando in ("risposta", "salta", "famiglia") and not a.valore:
        print(f"uso: arturo intervista {a.comando} " + ("N|NOME|nessuna" if a.comando == "famiglia" else "ID"),
              file=sys.stderr)
        return 3
    if a.comando == "risposta":
        return comando_risposta(a.valore, a.testo)
    if a.comando == "salta":
        return comando_salta(a.valore)
    if a.comando == "famiglia":
        return comando_famiglia(a.valore)
    print(f'comando "{a.comando}" sconosciuto\n' + __doc__.split("\n\n")[1], file=sys.stderr)
    return 3


if __name__ == "__main__":
    for flusso in (sys.stdout, sys.stderr):
        try:
            flusso.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass
    raise SystemExit(main())
