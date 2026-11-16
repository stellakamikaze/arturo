"""Le forme della Scoperta: automazione, sintesi e pagina (Fase D del piano della catena di prodotto, #5702).

La Scoperta v1 (bin/scoperta.py) propone una skill quando un file cambia con un ritmo. Il 16/11/2026
Federico ha detto sì alle forme nuove: una sintesi o una pagina web locale, per famiglia di mestiere.
Questo modulo aggiunge tre cose, e scoperta.py le usa:

- D1, i lavori dello storico. Un lavoro dell'indice dello storico (data/storico/indice.json, bin/storico.py)
  con almeno MIN_CONVERSAZIONI conversazioni in almeno MIN_MESI mesi diversi è un lavoro che torna: diventa
  un candidato dal primo giorno, senza aspettare che i file cambino tre volte;
- D3, la forma. Un candidato è un'automazione (una skill, come prima), una sintesi (un documento che
  raccoglie un lavoro lungo) o una pagina (una pagina web locale, da un modello della famiglia di
  mestiere). Un lavoro dello storico è una pagina se titoli e temi chiamano un modello, altrimenti una
  sintesi; un file di dati (csv, tsv) che cambia con un ritmo è una pagina; il resto resta automazione;
- D2, la mappa. `arturo scoperta mappa` dice per ogni progetto cosa Arturo può proporre e in che forma.

I modelli delle pagine stanno in MODELLI, uno per famiglia di docs/mestieri.md, più uno per i dati senza
famiglia. La famiglia viene dall'intervista (bin/intervista.py): scelta dalla persona, dal suo CLAUDE.md
o dallo storico. Restano i limiti della Scoperta: le prove, il sì, l'annullamento, al massimo una proposta
per sessione e due a settimana. Solo libreria standard, niente rete, niente modello.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional

QUI = Path(os.path.realpath(__file__)).parent
sys.path.insert(0, str(QUI))
sys.path.insert(0, str(QUI.parent / "hooks"))
from radici import radice_orsa  # noqa: E402

MIN_CONVERSAZIONI = 5
MIN_MESI = 2
DATI = {".csv", ".tsv"}
FORME = ("automazione", "sintesi", "pagina")

# Un modello di pagina per famiglia: nome, cosa mostra, parole che lo chiamano nei titoli e nei temi.
MODELLI: Dict[str, dict] = {
    "parola": {"nome": "calendario editoriale",
               "cosa": "una pagina con le uscite in ordine di data, il formato e lo stato di ogni pezzo",
               "parole": ["newsletter", "rubrica", "piano editoriale", "calendario", "uscite", "puntat"]},
    "immagine": {"nome": "galleria dei lavori",
                 "cosa": "una pagina con le immagini del progetto, le versioni e le note del cliente",
                 "parole": ["moodboard", "galleria", "portfolio", "shooting", "catalogo foto", "versioni"]},
    "insegnamento": {"nome": "lezione interattiva",
                     "cosa": "una pagina con la scaletta della lezione, gli esempi da provare e le domande per la classe",
                     "parole": ["lezion", "corso", "lezione", "classe", "studenti", "workshop", "seminari", "esercizi"]},
    "produzione": {"nome": "simulatore di spesa",
                   "cosa": "una pagina che legge il foglio delle spese o delle fatture e mostra cosa succede al "
                           "totale se cambi una voce",
                   "parole": ["budget", "spese", "spesa", "consuntiv", "fattur", "preventiv", "costi", "fornitor"]},
    "consulenza": {"nome": "cruscotto del report",
                   "cosa": "una pagina che legge i dati del report e li mostra mese per mese in tabelle e grafici",
                   "parole": ["report", "kpi", "indicator", "analisi", "sondagg", "mercato", "metriche"]},
    "archivio": {"nome": "linea del tempo",
                 "cosa": "una pagina che mette in ordine i materiali per data, con una scheda per ognuno",
                 "parole": ["archivi", "inventari", "mostra", "collezion", "catalog", "fondo", "schedatura"]},
}
DATI_SENZA_FAMIGLIA = {"nome": "cruscotto dei dati",
                       "cosa": "una pagina che legge il foglio e ne mostra i numeri in tabelle e grafici"}


# --- La famiglia della persona -------------------------------------------------------------------------

def famiglia() -> Optional[str]:
    """La famiglia di mestiere dell'intervista, o None. Una rottura dell'intervista non ferma la Scoperta."""
    try:
        import intervista
        fam, _ = intervista.famiglia(intervista.leggi_stato(), intervista.leggi_mestieri())
        return fam
    except Exception:
        return None


def _conta(testo: str, parole: List[str]) -> int:
    testo = testo.lower()
    return sum(1 for p in parole if re.search(r"(?<![a-zàèéìòù])" + re.escape(p), testo))


def modello_per(testo: str, fam: Optional[str]) -> Optional[str]:
    """Il modello che titoli e temi chiamano: prima quello della famiglia, poi quello con più parole."""
    if fam in MODELLI and _conta(testo, MODELLI[fam]["parole"]):
        return fam
    punti = sorted(((_conta(testo, m["parole"]), k) for k, m in MODELLI.items()), reverse=True)
    if punti and punti[0][0] and (len(punti) < 2 or punti[1][0] < punti[0][0]):
        return punti[0][1]
    return None


# --- D1: i lavori dello storico ------------------------------------------------------------------------

def lavori_storico() -> List[dict]:
    try:
        dati = json.loads((radice_orsa() / "data" / "storico" / "indice.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    lavori = dati.get("lavori", []) if isinstance(dati, dict) else []
    return [x for x in lavori if isinstance(x, dict)]


def _mesi(lavoro: dict) -> int:
    """I mesi fra il primo e l'ultimo, contati tutti e due: da 2026-01 a 2026-03 sono 3."""
    def mese(t: object) -> Optional[int]:
        m = re.match(r"^(\d{4})-(\d{2})", str(t or ""))
        return int(m.group(1)) * 12 + int(m.group(2)) if m else None
    da, a = mese(lavoro.get("da")), mese(lavoro.get("a"))
    return (a - da + 1) if da is not None and a is not None and a >= da else 0


def _firma(*parti: str) -> str:
    return hashlib.sha256("\0".join(parti).encode("utf-8")).hexdigest()[:10]


def dallo_storico(fam: Optional[str] = None) -> List[dict]:
    """I candidati dei lavori dello storico che tornano, nella forma dei candidati di scoperta.py."""
    fuori = []
    for x in lavori_storico():
        try:
            n = int(x.get("conversazioni", 0))
        except (TypeError, ValueError):
            n = 0
        mesi = _mesi(x)
        if n < MIN_CONVERSAZIONI or mesi < MIN_MESI:
            continue
        titolo = " ".join(str(x.get("titolo", "")).split())[:80] or "(senza titolo)"
        temi = [str(t) for t in x.get("temi", []) if isinstance(t, (str, int))] if isinstance(x.get("temi"), list) else []
        titoli = [str(t) for t in x.get("titoli", []) if isinstance(t, str)] if isinstance(x.get("titoli"), list) else []
        file = [str(f) for f in x.get("file", []) if isinstance(f, str)] if isinstance(x.get("file"), list) else []
        modello = modello_per(" ".join([titolo, *titoli, *temi]), fam)
        forma = "pagina" if modello else "sintesi"
        fuori.append({
            "id": _firma("storico", str(x.get("id", titolo))), "segnale": "storico", "famiglia": "", "file": file[:10],
            "ritmo": "", "campi": temi[:5], "volte": n, "nuovi": 0, "aggiunta": False,
            "forza": round(n * (1 + mesi / 2) * 1.5, 2), "prove": [], "forma": forma, "modello": modello or "",
            "lavoro": {"id": str(x.get("id", "")), "titolo": titolo, "da": str(x.get("da", "")),
                       "a": str(x.get("a", "")), "mesi": mesi},
        })
    return fuori


# --- D3: la forma di un candidato dei file ------------------------------------------------------------

def con_forma(c: dict, fam: Optional[str]) -> dict:
    """Mette forma e modello a un candidato dei file. Un file di dati che torna è una pagina."""
    if c.get("forma"):
        return c
    ext = os.path.splitext(c.get("famiglia") or (c.get("file") or [""])[0])[1].lower()
    if c.get("segnale") != "insieme" and ext in DATI:
        nome = os.path.basename(c.get("famiglia") or c["file"][0])
        c["forma"] = "pagina"
        c["modello"] = modello_per(nome + " " + " ".join(c.get("campi", [])), fam) or \
            (fam if fam in ("consulenza", "produzione") else "")
    else:
        c["forma"], c["modello"] = "automazione", ""
    return c


def descrizione_modello(c: dict) -> dict:
    return MODELLI.get(c.get("modello") or "", DATI_SENZA_FAMIGLIA)


def _slug(testo: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", testo.lower().replace("à", "a").replace("è", "e").replace("é", "e")
               .replace("ì", "i").replace("ò", "o").replace("ù", "u")).strip("-")
    return s[:30].strip("-") or "lavoro"


def descrivi(c: dict, descrivi_file) -> str:
    """La frase che apre la proposta. descrivi_file è quella di scoperta.py, per i candidati dei file."""
    m = descrizione_modello(c)
    if c.get("segnale") == "storico":
        lav = c["lavoro"]
        visto = (f"In chat hai lavorato a \"{lav['titolo']}\" in {c['volte']} conversazioni, "
                 f"da {lav['da']} a {lav['a']}.")
        if c["forma"] == "sintesi":
            return visto + " Posso raccoglierlo in un documento solo: cosa è, cosa hai deciso, i materiali, cosa resta aperto."
        return visto + f" Posso farne un {m['nome']}: {m['cosa']}."
    frase = descrivi_file(c)
    if c.get("forma") == "pagina":
        frase += f" Posso farne un {m['nome']}: {m['cosa']}."
    return frase


def nome(c: dict) -> str:
    if c.get("segnale") == "storico":
        base = _slug(c["lavoro"]["titolo"])
    else:
        base = _slug(os.path.splitext(os.path.basename(c.get("famiglia") or c["file"][0]))[0])
    return f"{'sintesi' if c['forma'] == 'sintesi' else 'pagina'}-{base}"[:40].strip("-")


def bozza(c: dict, descrivi_file) -> str:
    """La bozza di una sintesi o di una pagina: la legge la persona, poi Claude scrive il file col suo sì."""
    file = ", ".join(c["file"][:5]) or "i materiali che indichi tu"
    if c["forma"] == "sintesi":
        passi = [f"Leggi l'indice del lavoro con arturo storico mostra e i materiali: {file}.",
                 "Scrivi un file .md nella cartella del progetto con quattro parti: cosa è il lavoro, cosa si è "
                 "deciso, i materiali e dove stanno, cosa resta aperto.",
                 "Mostra la sintesi e salvala solo dopo il sì della persona."]
    else:
        m = descrizione_modello(c)
        passi = [f"Leggi i dati: {file}.",
                 f"Costruisci un {m['nome']}: {m['cosa']}. Un solo file .html nella cartella del progetto, senza "
                 "servizi esterni, che si apre anche senza rete.",
                 "Aprila nel browser della persona e salvala solo dopo il suo sì.",
                 "Condividerla con altri è un invio: lo fa la persona."]
    righe = [f"Nome: {nome(c)}", f"Forma: {c['forma']}", f"Cosa fa: {descrivi(c, descrivi_file)}",
             "Quando parte: una volta, col sì della persona; poi si aggiorna quando lo chiede.", "Passi:"]
    righe += [f"  {i}. {p}" for i, p in enumerate(passi, 1)]
    righe.append("Non fa: non manda niente a nessuno, non cancella file.")
    return "\n".join(righe)


def risposta(c_o_voce: dict, ident: str) -> str:
    """La riga Risposta della proposta, che cambia con la forma."""
    if c_o_voce.get("forma") in ("sintesi", "pagina"):
        cosa = "la sintesi" if c_o_voce["forma"] == "sintesi" else "la pagina"
        return (f"Risposta: arturo scoperta rispondi {ident} si (Claude scrive {cosa} dalla bozza) oppure no "
                "(non torna più).")
    return f"Risposta: arturo scoperta rispondi {ident} si (parte /creaskill con la bozza) oppure no (non torna più)."


def dopo_il_si(voce: dict, ident: str) -> str:
    if voce.get("forma") in ("sintesi", "pagina"):
        cosa = "la sintesi" if voce["forma"] == "sintesi" else "la pagina"
        return (f"Ora: scrivi {cosa} dalla bozza, mostrala e salvala col sì; a file salvato, "
                f"arturo scoperta creata {ident} <file>.")
    return f"Ora: /creaskill con la bozza; a skill creata, arturo scoperta creata {ident} <cartella della skill>."


# --- D2: la mappa dei progetti -------------------------------------------------------------------------

def progetto_di(percorso: str) -> str:
    """Il progetto di un file: la cartella sotto Documents/ClaudeCode, altrimenti la cartella che lo contiene."""
    parti = Path(percorso.replace("\\", "/")).parts
    for i, p in enumerate(parti[:-1]):
        if p == "ClaudeCode" and i > 0 and parti[i - 1] == "Documents" and i + 2 < len(parti):
            return parti[i + 1]
    return parti[-2] if len(parti) >= 2 else "altro"


def mappa(candidati: List[dict], proposte: dict) -> List[str]:
    """Le righe di arturo scoperta mappa: per progetto, cosa si può proporre, in che forma, e se è già proposta."""
    gruppi: Dict[str, List[dict]] = {}
    for c in candidati:
        chiave = f"storico · {c['lavoro']['titolo']}" if c.get("segnale") == "storico" else \
            progetto_di(c.get("famiglia") or c["file"][0])
        gruppi.setdefault(chiave, []).append(c)
    if not gruppi:
        return ["Nessun lavoro che torna, per ora: la mappa si riempie quando un file cambia con un ritmo o "
                "lo storico ha un lavoro lungo."]
    righe = []
    for chiave in sorted(gruppi):
        righe.append(chiave)
        for c in gruppi[chiave]:
            stato = proposte.get(c["id"], {}).get("stato", "") if isinstance(proposte.get(c["id"]), dict) else ""
            forma = c["forma"] + (f" ({descrizione_modello(c)['nome']})" if c["forma"] == "pagina" else "")
            cosa = "" if c.get("segnale") == "storico" else " · " + ", ".join(
                os.path.basename(f).replace("#", "N") for f in ([c["famiglia"]] if c.get("famiglia") else c["file"][:3]))
            righe.append(f"  {c['id']} · {forma}{cosa} · {c['volte']} volte" + (f" · {stato}" if stato else ""))
    return righe
