#!/usr/bin/env python3
"""righe.py: valida le righe che i ponti consegnano a /monitor (schema in bin/monitor/schema.md).

Ogni ponte consegna righe JSON, una per riga: una riga `item` per ogni cosa da fare e una riga
`copertura` che dice quanto ha letto. Questo script tiene le righe valide, aggiunge a ogni item il
fingerprint (`fp`) e il suo `hash`, e scarta le altre dicendo il perché. Meglio un item perso e
detto che un item sbagliato e muto.

  righe.py [--attese a,b] [FILE]
                           legge FILE, o lo standard input senza FILE; scrive le righe valide
                           sullo standard output e i motivi degli scarti sullo standard error.
                           --attese: le fonti scelte (fonti.json); una fonte attesa senza copertura
                           non è stata letta, anche se non ha item

Exit 0 se ogni riga è valida e ogni fonte con item, o attesa, ha la sua copertura, 1 se qualcosa è
scartato o manca, 2 se FILE non si legge. Solo libreria standard, Python 3.8 o successivo.
"""
from __future__ import annotations

import json
import re
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import fingerprint  # noqa: E402

FONTE = re.compile(r"^[a-z][a-z0-9-]{0,39}$")
URGENZE = {"rosso", "giallo", "verde"}
ITEM_OBBLIGATORI = ("tipo", "fonte", "id_sorgente", "data", "riassunto", "urgenza")
ITEM_FACOLTATIVI = ("scadenza", "progetto", "promessa", "extra", "fp")
COPERTURA = ("tipo", "fonte", "listati", "letti", "troncato", "motivo", "dettaglio")
# Campi che un /monitor personale può avere e lo schema generico no: il perché va nel messaggio.
FUORI = {
    "cifra": "le cifre restano fuori dallo schema generico: le porta una parte personale con la sua fonte",
    "progetto_uf": "il progetto si scrive in `progetto`",
    "fp_canonico": "il fingerprint si scrive in `fp`",
}


GIORNO = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def _data(v):
    # La forma prima di fromisoformat: dalla 3.11 accetta anche "2026-W45-1", e la stessa riga valeva o no
    # secondo il Python (review del 9/11/2026, lotto L10).
    try:
        return isinstance(v, str) and bool(GIORNO.match(v)) and bool(date.fromisoformat(v))
    except ValueError:
        return False


def valida_item(r):
    """(riga completata, None) oppure (None, motivo)."""
    for campo in r:
        if campo in FUORI:
            return None, f"campo {campo}: {FUORI[campo]}"
        if campo not in ITEM_OBBLIGATORI + ITEM_FACOLTATIVI:
            return None, f"campo non previsto: {campo}"
    mancano = [c for c in ITEM_OBBLIGATORI if r.get(c) in (None, "")]
    if mancano:
        return None, f"mancano {', '.join(mancano)}"
    if not FONTE.match(str(r["fonte"])):
        return None, f"fonte {r['fonte']!r}: minuscole, cifre e trattini"
    if not isinstance(r["id_sorgente"], str):
        return None, "id_sorgente è una stringa"
    if not _data(r["data"]):
        return None, f"data {r['data']!r}: serve AAAA-MM-GG"
    if r.get("scadenza") is not None and not _data(r["scadenza"]):
        return None, f"scadenza {r['scadenza']!r}: serve AAAA-MM-GG, oppure null"
    if not isinstance(r["urgenza"], str) or r["urgenza"] not in URGENZE:
        return None, f"urgenza {r['urgenza']!r}: rosso, giallo o verde"
    if not isinstance(r["riassunto"], str) or "\n" in r["riassunto"] or len(r["riassunto"]) > 300:
        return None, "riassunto: una riga sola, al massimo 300 caratteri"
    if r.get("progetto") is not None and not isinstance(r["progetto"], str):
        return None, "progetto è una stringa, oppure null"
    p = r.get("promessa")
    if p is not None:
        if not isinstance(p, dict) or not p.get("a_chi") or not p.get("cosa"):
            return None, "promessa vuole a_chi e cosa, oppure null"
        if p.get("entro") is not None and not _data(p["entro"]):
            return None, "promessa.entro: serve AAAA-MM-GG, oppure null"
    if r.get("extra") is not None and not isinstance(r["extra"], dict):
        return None, "extra è un oggetto"
    fp = r.get("fp") or f"{r['fonte']}:{r['id_sorgente']}"
    if not isinstance(fp, str):
        return None, f"fingerprint {fp!r}: è una stringa"
    fp = fp.strip()  # uno spazio in coda dava un fp diverso dalla stringa del suo hash
    ok, motivo = fingerprint.valida(fp)
    if not ok:
        return None, f"fingerprint {fp!r}: {motivo}"
    if not fp.startswith(r["fonte"] + ":"):
        return None, f"fingerprint {fp!r}: deve cominciare con la fonte {r['fonte']}:"
    return dict(r, fp=fp, hash=fingerprint.hash_di(fp)), None


def valida_copertura(r):
    for campo in r:
        if campo not in COPERTURA:
            return None, f"campo non previsto nella copertura: {campo}"
    if not FONTE.match(str(r.get("fonte", ""))):
        return None, "copertura senza fonte valida"
    for campo in ("listati", "letti"):
        v = r.get(campo)
        if not isinstance(v, int) or isinstance(v, bool) or v < 0:
            return None, f"copertura: {campo} è un numero da 0 in su"
    if not isinstance(r.get("troncato"), bool):
        return None, "copertura: troncato è true o false"
    if r["troncato"] and not r.get("motivo"):
        return None, "copertura troncata senza motivo: di' cosa è rimasto fuori e perché"
    # Letti meno dei listati è una lettura troncata: dirla intera farebbe avanzare il cursore oltre le cose
    # mai aperte, che poi escono dalla finestra (lotto L10).
    if r["letti"] > r["listati"]:
        return None, "copertura: letti più dei listati"
    if r["letti"] < r["listati"] and not r["troncato"]:
        return None, "copertura: letti meno dei listati, ma troncato è false"
    return r, None


def valida(righe, attese=()):
    """(valide, scarti). Gli scarti sono stringhe `riga N: motivo` o `fonte X: motivo`. `attese`: le fonti
    scelte, che devono avere la copertura anche senza item."""
    valide, scarti, coperte, con_item, visti = [], [], set(), set(), set()
    for n, testo in enumerate(righe, 1):
        if not testo.strip():
            continue
        try:
            r = json.loads(testo)
        except ValueError:
            scarti.append(f"riga {n}: non è JSON")
            continue
        if not isinstance(r, dict):
            scarti.append(f"riga {n}: non è un oggetto JSON")
            continue
        tipo = r.get("tipo")
        try:
            if tipo == "item":
                buona, motivo = valida_item(r)
            elif tipo == "copertura":
                buona, motivo = valida_copertura(r)
            else:
                buona, motivo = None, f"tipo {tipo!r}: item o copertura"
        except (TypeError, AttributeError, ValueError) as e:
            # Un campo col tipo sbagliato scarta la sua riga, non tutta la consegna (review del 7/11/2026,
            # finding 34): le altre righe restano.
            buona, motivo = None, f"un campo ha il tipo sbagliato ({type(e).__name__}: {e})"
        if motivo:
            scarti.append(f"riga {n}: {motivo}")
            continue
        if tipo == "item":
            if buona["fp"] in visti:
                scarti.append(f"riga {n}: fingerprint {buona['fp']!r} già consegnato in questa consegna")
                continue
            visti.add(buona["fp"])
        (coperte if tipo == "copertura" else con_item).add(buona["fonte"])
        valide.append(buona)
    for fonte in sorted((con_item | set(attese)) - coperte):
        scarti.append(f"fonte {fonte}: manca la riga di copertura, non si sa quanto ha letto")
    return valide, scarti


def main(argv):
    for flusso in (sys.stdout, sys.stderr):
        if hasattr(flusso, "reconfigure"):
            flusso.reconfigure(encoding="utf-8", errors="replace")
    attese = []
    if argv[:1] == ["--attese"] and len(argv) >= 2:
        attese = [a for a in argv[1].split(",") if a]
        argv = argv[2:]
    if len(argv) > 1 or argv[:1] in (["-h"], ["--help"]) or (argv and argv[0].startswith("-")):
        print(__doc__, file=sys.stderr)
        return 2
    try:
        # Lo standard input si legge in UTF-8 anche su Windows, dove il default è cp1252 e rovina gli accenti;
        # utf-8-sig toglie il BOM che certi editor di Windows mettono in testa.
        testo = Path(argv[0]).read_text(encoding="utf-8-sig") if argv else sys.stdin.buffer.read().decode("utf-8-sig")
    except (OSError, UnicodeDecodeError) as e:
        print(f"ERRORE: {e}", file=sys.stderr)
        return 2
    # split("\n"), non splitlines(): U+2028 e U+0085 stanno crudi dentro una stringa JSON valida, e splitlines la
    # tagliava in due righe non JSON (lotto L10).
    valide, scarti = valida([r.rstrip("\r") for r in testo.split("\n")], attese)
    for r in valide:
        print(json.dumps(r, ensure_ascii=True))
    for s in scarti:
        print(f"SCARTATA {s}", file=sys.stderr)
    item = sum(1 for r in valide if r["tipo"] == "item")
    print(f"# righe: {item} item validi, {len(scarti)} scarti", file=sys.stderr)
    return 1 if scarti else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
