"""Archivio dei todo di Arturo: un registro di eventi, una riga JSON per evento.

Il file e' ~/.claude/data/todo/eventi.jsonl (ARTURO_TODO lo sposta, per i test).
Ogni scrittura aggiunge una riga in coda con una sola write(): due viste che
scrivono insieme non si sovrascrivono, e il registro passa tra le macchine con
un merge per unione. Lo stato si ricostruisce rileggendo il registro.

Un todo si riconosce dal suo uid. L'id numerico serve alle persone: se due
macchine creano lo stesso id, il todo piu' recente ne prende uno nuovo e la
lettura lo segnala. Gli eventi successivi puntano all'uid, quindi restano giusti.

CLI, pannello e vista web leggono da qui: `carica()` e `vista()` sono il contratto.
"""
from __future__ import annotations

import datetime as dt
import json
import os
import re
import time
import uuid
from pathlib import Path

VERSIONE = 1
STATI = ("da fare", "in corso", "fermo", "fatto", "scartato")
APERTI = ("da fare", "in corso", "fermo")
CHI = ("tu", "decidi", "io")
PRIORITA = ("alta", "media", "bassa")
QUANDO = ("oggi", "settimana", "più avanti")
GRUPPI = (
    ("tu", "TOCCA A TE"),
    ("decidi", "DECIDI TU, POI FACCIO IO"),
    ("io", "FACCIO IO"),
    ("fermo", "FERMO"),
)
CAMPI = ("titolo", "progetto", "scadenza", "chi", "perche", "priorita", "quando")
GIORNI = ("lunedi", "martedi", "mercoledi", "giovedi", "venerdi", "sabato", "domenica")


class ErroreTodo(ValueError):
    """Un valore che la persona puo' correggere: il messaggio le dice come."""


def percorso() -> Path:
    altro = os.environ.get("ARTURO_TODO")
    if altro:
        return Path(altro)
    return Path.home() / ".claude" / "data" / "todo" / "eventi.jsonl"


def oggi() -> dt.date:
    fisso = os.environ.get("ARTURO_OGGI")
    return dt.date.fromisoformat(fisso) if fisso else dt.date.today()


def _adesso() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="microseconds")


# --- valori chiusi e date -----------------------------------------------------

def scelta(valore: str, ammessi: tuple, nome: str) -> str:
    v = valore.strip().lower()
    if v == "piu avanti":
        v = "più avanti"
    if v not in ammessi:
        raise ErroreTodo(f"{nome} «{valore}» non valido. Valori ammessi: {', '.join(ammessi)}")
    return v


def data(valore: str) -> str:
    """AAAA-MM-GG, gg/mm, gg/mm/aaaa, oggi, domani, un giorno della settimana. Vuoto = nessuna."""
    v = valore.strip().lower()
    if not v:
        return ""
    base = oggi()
    if v == "oggi":
        return base.isoformat()
    if v == "domani":
        return (base + dt.timedelta(days=1)).isoformat()
    senza_accento = v.replace("ì", "i").replace("í", "i")
    if senza_accento in GIORNI:
        avanti = (GIORNI.index(senza_accento) - base.weekday()) % 7 or 7
        return (base + dt.timedelta(days=avanti)).isoformat()
    try:
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}", v):
            return dt.date.fromisoformat(v).isoformat()
        m = re.fullmatch(r"(\d{1,2})/(\d{1,2})(?:/(\d{2}|\d{4}))?", v)
        if m:
            anno = int(m.group(3)) if m.group(3) else base.year
            if anno < 100:
                anno += 2000
            return dt.date(anno, int(m.group(2)), int(m.group(1))).isoformat()
    except ValueError:
        pass
    raise ErroreTodo(f"data «{valore}» non valida. Scrivi 2026-10-10, 10/10, oggi, domani o un giorno (venerdì)")


def normalizza(campi: dict) -> dict:
    """Controlla i campi di un todo. Una stringa vuota svuota il campo."""
    fuori = {}
    for chiave, valore in campi.items():
        if valore is None:
            continue
        if chiave not in CAMPI:
            raise ErroreTodo(f"campo sconosciuto: {chiave}")
        valore = str(valore).strip()
        if chiave == "titolo" and not valore:
            raise ErroreTodo("il titolo non può essere vuoto")
        if chiave == "chi":
            valore = scelta(valore, CHI, "chi")
        elif chiave == "priorita":
            valore = scelta(valore, PRIORITA, "priorità")
        elif chiave == "quando":
            valore = scelta(valore, QUANDO, "quando")
        elif chiave == "scadenza":
            valore = data(valore)
        fuori[chiave] = valore
    return fuori


# --- lettura ------------------------------------------------------------------

def _righe(file: Path) -> list:
    if not file.exists():
        return []
    with open(file, "rb") as f:
        return f.read().decode("utf-8", errors="replace").splitlines()


def carica(file: Path | None = None) -> tuple:
    """Rilegge il registro. Torna (todo per uid, avvisi). Una riga rotta si salta."""
    file = file or percorso()
    eventi, avvisi, visti = [], [], set()
    for numero, riga in enumerate(_righe(file), 1):
        if not riga.strip():
            continue
        try:
            e = json.loads(riga)
            if not isinstance(e, dict) or "tipo" not in e or "todo" not in e:
                raise ValueError
        except ValueError:
            avvisi.append(f"riga {numero} del registro illeggibile, saltata")
            continue
        if e.get("ev") in visti:
            continue  # la stessa riga arrivata due volte da un merge
        visti.add(e.get("ev"))
        eventi.append((str(e.get("ts", "")), numero, e))
    eventi.sort(key=lambda x: (x[0], x[1]))

    todo, usati = {}, {}
    for ts, numero, e in eventi:
        uid, tipo, dati = e["todo"], e["tipo"], e.get("dati") or {}
        if tipo == "crea":
            if uid in todo:
                continue
            numero_todo = e.get("id")
            if not isinstance(numero_todo, int) or numero_todo in usati:
                nuovo = max(usati, default=0) + 1
                if isinstance(numero_todo, int):
                    avvisi.append(f"#{numero_todo} esisteva già su un'altra macchina: il todo «{dati.get('titolo', '')}» ora è #{nuovo}")
                numero_todo = nuovo
            usati[numero_todo] = uid
            t = {"id": numero_todo, "uid": uid, "titolo": "", "progetto": "generale", "scadenza": "",
                 "chi": "tu", "perche": "", "priorita": "media", "quando": "settimana", "stato": "da fare",
                 "motivo": "", "dopo": [], "note": [], "creato": ts, "aggiornato": ts, "chiuso": "", "storia": []}
            t.update({k: v for k, v in dati.items() if k in CAMPI})
            todo[uid] = t
        else:
            t = todo.get(uid)
            if t is None:
                avvisi.append(f"riga {numero}: evento per un todo che non esiste, saltato")
                continue
            if tipo == "modifica":
                t.update({k: v for k, v in dati.items() if k in CAMPI})
            elif tipo == "stato" and dati.get("stato") in STATI:
                t["stato"] = dati["stato"]
                t["motivo"] = dati.get("motivo", "")
                t["chiuso"] = ts if t["stato"] in ("fatto", "scartato") else ""
            elif tipo == "nota" and dati.get("testo"):
                t["note"].append({"ts": ts, "testo": dati["testo"]})
            elif tipo == "dopo":
                if dati.get("aggiungi") and dati["aggiungi"] not in t["dopo"]:
                    t["dopo"].append(dati["aggiungi"])
                if dati.get("togli") in t["dopo"]:
                    t["dopo"].remove(dati["togli"])
            t["aggiornato"] = ts
        todo[uid]["storia"].append({"ts": ts, "tipo": tipo, "dati": dati})
    return todo, avvisi


def per_id(todo: dict, numero) -> dict:
    try:
        n = int(str(numero).lstrip("#"))
    except ValueError:
        raise ErroreTodo(f"«{numero}» non è un numero di todo")
    for t in todo.values():
        if t["id"] == n:
            return t
    raise ErroreTodo(f"il todo #{n} non esiste. Vedi la lista con: arturo todo")


# --- scrittura ----------------------------------------------------------------

def _scrivi(evento: dict, file: Path) -> None:
    file.parent.mkdir(parents=True, exist_ok=True)
    riga = (json.dumps(evento, ensure_ascii=False, separators=(",", ":")) + "\n").encode("utf-8")
    fd = os.open(str(file), os.O_WRONLY | os.O_APPEND | os.O_CREAT | getattr(os, "O_BINARY", 0), 0o600)
    try:
        os.write(fd, riga)
    finally:
        os.close(fd)


class _Lucchetto:
    """Serve solo a dare id diversi a due todo creati nello stesso istante."""

    def __init__(self, file: Path):
        self.file = file.with_name(file.name + ".lock")

    def __enter__(self):
        self.file.parent.mkdir(parents=True, exist_ok=True)
        limite = time.time() + 10
        while True:
            try:
                os.close(os.open(str(self.file), os.O_CREAT | os.O_EXCL | os.O_WRONLY))
                return self
            except FileExistsError:
                try:
                    if time.time() - self.file.stat().st_mtime > 10:
                        self.file.unlink()  # lasciato da un processo interrotto
                        continue
                except FileNotFoundError:
                    continue
                if time.time() > limite:
                    raise ErroreTodo(f"archivio occupato da un altro processo: se non ce n'è uno, cancella {self.file}")
                time.sleep(0.02)

    def __exit__(self, *_):
        try:
            self.file.unlink()
        except FileNotFoundError:
            pass


def _evento(tipo: str, uid: str, dati: dict, **altro) -> dict:
    return {"v": VERSIONE, "ts": _adesso(), "ev": uuid.uuid4().hex, "todo": uid, "tipo": tipo, "dati": dati, **altro}


def aggiungi(campi: dict, file: Path | None = None) -> dict:
    file = file or percorso()
    dati = normalizza(campi)
    if not dati.get("titolo"):
        raise ErroreTodo("il titolo non può essere vuoto")
    uid = uuid.uuid4().hex
    with _Lucchetto(file):
        todo, _ = carica(file)
        numero = max((t["id"] for t in todo.values()), default=0) + 1
        _scrivi(_evento("crea", uid, dati, id=numero), file)
    return carica(file)[0][uid]


def registra(numero, tipo: str, dati: dict, file: Path | None = None) -> dict:
    """Modifica, stato, nota o dopo su un todo esistente, indicato col suo numero."""
    file = file or percorso()
    todo, _ = carica(file)
    t = per_id(todo, numero)
    if tipo == "modifica":
        dati = normalizza(dati)
        if not dati:
            raise ErroreTodo("niente da modificare: indica almeno un campo")
    elif tipo == "stato":
        dati = {"stato": scelta(dati["stato"], STATI, "stato"), "motivo": dati.get("motivo", "")}
    elif tipo == "nota":
        if not str(dati.get("testo", "")).strip():
            raise ErroreTodo("la nota è vuota")
    elif tipo == "dopo":
        altro = per_id(todo, dati.pop("id"))
        if altro["uid"] == t["uid"]:
            raise ErroreTodo("un todo non può aspettare se stesso")
        dati = {("togli" if dati.get("togli") else "aggiungi"): altro["uid"]}
    else:
        raise ErroreTodo(f"tipo di evento sconosciuto: {tipo}")
    _scrivi(_evento(tipo, t["uid"], dati), file)
    return carica(file)[0][t["uid"]]


# --- viste --------------------------------------------------------------------

def gruppo(t: dict):
    """FERMO viene dallo stato. Gli altri gruppi da chi agisce. I chiusi non hanno gruppo."""
    if t["stato"] in ("fatto", "scartato"):
        return None
    if t["stato"] == "fermo":
        return "fermo"
    return t["chi"] if t["chi"] in CHI else "tu"


def giorni(t: dict):
    if not t["scadenza"]:
        return None
    return (dt.date.fromisoformat(t["scadenza"]) - oggi()).days


def _ordine(t: dict) -> tuple:
    g = giorni(t)
    return (0 if g is not None and g < 0 else 1, PRIORITA.index(t["priorita"]) if t["priorita"] in PRIORITA else 1,
            g if g is not None else 10 ** 6, t["id"])


def esporta(t: dict, todo: dict) -> dict:
    """Un todo nella forma del contratto JSON: niente uid, id numerici per le dipendenze."""
    per_uid = {x["uid"]: x for x in todo.values()}
    dopo = [per_uid[u] for u in t["dopo"] if u in per_uid]
    return {
        "id": t["id"], "titolo": t["titolo"], "progetto": t["progetto"], "scadenza": t["scadenza"] or None,
        "giorni": giorni(t), "priorita": t["priorita"], "stato": t["stato"], "quando": t["quando"],
        "chi": t["chi"], "perche": t["perche"] or None, "motivo": t["motivo"] or None,
        "gruppo": gruppo(t), "dopo": [x["id"] for x in dopo],
        "attende": [x["id"] for x in dopo if x["stato"] in APERTI],
        "note": [n["testo"] for n in t["note"]],
    }


def vista(todo: dict, avvisi: list, progetto: str | None = None, tutti: bool = False) -> dict:
    scelti = [t for t in todo.values() if not progetto or t["progetto"] == progetto]
    gruppi = []
    for tipo, titolo in GRUPPI:
        dentro = sorted((t for t in scelti if gruppo(t) == tipo), key=_ordine)
        gruppi.append({"tipo": tipo, "titolo": titolo, "todo": [esporta(t, todo) for t in dentro]})
    chiusi = sorted((t for t in scelti if gruppo(t) is None), key=lambda t: t["chiuso"], reverse=True)
    risultato = {"versione": VERSIONE, "oggi": oggi().isoformat(), "progetto": progetto, "gruppi": gruppi,
                 "chiusi": len(chiusi), "avvisi": avvisi}
    if tutti:
        risultato["chiusi_todo"] = [esporta(t, todo) for t in chiusi]
    return risultato
