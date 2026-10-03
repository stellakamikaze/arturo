"""Archivio dei todo di Arturo: un registro di eventi, una riga JSON per evento.

Il file e' ~/.claude/data/todo/eventi.jsonl (ARTURO_TODO lo sposta, per i test).
Ogni scrittura aggiunge una riga in coda con una sola write(): due viste che
scrivono insieme non si sovrascrivono, e il registro passa tra le macchine con
un merge per unione. Lo stato si ricostruisce rileggendo il registro.

Un todo si riconosce dal suo uid. L'id numerico serve alle persone: se due
macchine creano lo stesso id, il todo piu' recente ne prende uno nuovo e la
lettura lo segnala. Gli eventi successivi puntano all'uid, quindi restano giusti.

CLI, pannello e vista web leggono da qui: `carica()` e `vista()` sono il contratto.
Le chiavi di un todo esportato stanno in CHIAVI_TODO, e da qui le leggono i banchi.

Due versioni, separate di proposito. VERSIONE_EVENTI e' il campo `v` di ogni riga del
registro. VERSIONE_VISTA e' il campo `versione` del JSON delle viste. Un evento nuovo
(per esempio il segno `annullo`) non cambia il contratto delle viste, e il pannello
che controlla `versione` non si spegne.
"""
from __future__ import annotations

import datetime as dt
import json
import os
import re
import tempfile
import time
import uuid
from pathlib import Path

VERSIONE_EVENTI = 1
VERSIONE_VISTA = 1
STATI = ("da fare", "in corso", "fermo", "fatto", "scartato")
APERTI = ("da fare", "in corso", "fermo")
CHI = ("tu", "decidi", "io")
PRIORITA = ("alta", "media", "bassa")
QUANDO = ("oggi", "settimana", "più avanti")
GRUPPI = (
    ("tu", "TOCCA A TE", "Lo fai tu."),
    ("decidi", "DECIDI TU, POI FACCIO IO", "Serve una tua scelta, poi lavora Claude."),
    ("io", "FACCIO IO", "Lo fa Claude."),
    ("fermo", "FERMO", "Aspetta qualcosa o qualcuno."),
)
CAMPI = ("titolo", "progetto", "scadenza", "chi", "perche", "priorita", "quando")
# Il contratto di un todo esportato (vista, --json). Congelato: una chiave nuova e' un cambio
# di VERSIONE_VISTA, e pannello e pagina web la leggono da qui.
CHIAVI_TODO = ("id", "titolo", "progetto", "scadenza", "scadenza_testo", "giorni", "priorita", "stato",
               "quando", "chi", "perche", "motivo", "gruppo", "dopo", "attende", "note")
# I verbi che cambiano lo stato: verbo -> (stato nuovo, parola per la conferma).
AZIONI_STATO = {
    "fatto": ("fatto", "Chiuso"),
    "riprendi": ("da fare", "Riaperto"),
    "inizia": ("in corso", "Iniziato"),
    "ferma": ("fermo", "Fermato"),
    "scarta": ("scartato", "Scartato"),
}
# Il progetto degli esercizi del percorso. Lo slug di una cartella ammette solo [a-z0-9-]
# e non comincia con un trattino, quindi nessun repository finisce qui per caso.
PROGETTO_PERCORSO = "_percorso"
DECISO = "Deciso: "
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
    if v in ("in-corso", "in_corso"):
        v = "in corso"
    if v in ("da-fare", "da_fare"):
        v = "da fare"
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
        if chiave == "progetto" and not valore:
            raise ErroreTodo("il progetto non può essere vuoto: usa generale")
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
        testo = f.read().decode("utf-8", errors="replace")
    # Solo "\n" separa le righe. splitlines() spezza anche su U+0085, U+2028 e U+2029, che un
    # titolo incollato da un PDF può contenere: la riga si romperebbe in due pezzi illeggibili.
    return [riga[:-1] if riga.endswith("\r") else riga for riga in testo.split("\n")]


def _riga_valida(e) -> bool:
    """La forma di un evento letto dal registro. Una riga con la forma sbagliata si salta tutta.

    Il registro passa tra le macchine e si unisce con un merge: un valore di tipo sbagliato
    non deve fermare la lettura di tutto l'archivio.
    """
    if not isinstance(e, dict) or not isinstance(e.get("tipo"), str) or not isinstance(e.get("todo"), str):
        return False
    if not isinstance(e.get("ts", ""), str):
        return False
    dati = e.get("dati") or {}
    if not isinstance(dati, dict):
        return False
    for chiave in CAMPI:
        if chiave in dati and not isinstance(dati[chiave], str):
            return False
    for chiave, ammessi in (("chi", CHI), ("priorita", PRIORITA), ("quando", QUANDO)):
        if chiave in dati and dati[chiave] not in ammessi:
            return False
    scadenza = dati.get("scadenza", "")
    if scadenza:
        try:
            if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", scadenza):
                return False
            dt.date.fromisoformat(scadenza)
        except ValueError:
            return False
    for chiave in ("stato", "motivo", "testo", "aggiungi", "togli"):
        if chiave in dati and not isinstance(dati[chiave], str):
            return False
    if "titolo" in dati and not dati["titolo"].strip():
        return False  # un todo senza nome non si mostra
    if e["tipo"] == "crea":
        numero = e.get("id")
        # type() e non isinstance(): true e' un int per Python, e prenderebbe il posto di #1.
        if not dati.get("titolo") or type(numero) is not int or numero < 1:
            return False
    return isinstance(dati.get("annullo", False), bool)


def carica(file: Path | None = None) -> tuple:
    """Rilegge il registro. Torna (todo per uid, avvisi). Una riga rotta si salta."""
    file = file or percorso()
    eventi, avvisi, visti = [], [], set()
    for numero, riga in enumerate(_righe(file), 1):
        if not riga.strip():
            continue
        try:
            e = json.loads(riga)
            if not _riga_valida(e):
                raise ValueError
        except ValueError:
            avvisi.append(f"riga {numero} del registro illeggibile, saltata")
            continue
        ev = e.get("ev")
        if not isinstance(ev, str) or not ev:
            # Senza ev la riga non ha un nome: si riconosce dal suo testo intero.
            ev = "riga:" + riga.strip()
        if ev in visti:
            continue  # la stessa riga arrivata due volte da un merge
        visti.add(ev)
        eventi.append((str(e.get("ts", "")), numero, e))
    eventi.sort(key=lambda x: (x[0], x[1]))

    todo, usati = {}, {}
    for ts, numero, e in eventi:
        uid, tipo, dati = e["todo"], e["tipo"], e.get("dati") or {}
        if tipo == "crea":
            if uid in todo:
                continue
            numero_todo = e["id"]  # _riga_valida: un int positivo
            if numero_todo in usati:
                nuovo = max(usati) + 1
                avvisi.append(f"#{numero_todo} esisteva già su un'altra macchina: il todo «{dati['titolo']}» ora è #{nuovo}")
                numero_todo = nuovo
            usati[numero_todo] = uid
            t = {"id": numero_todo, "uid": uid, "titolo": "", "progetto": "generale", "scadenza": "",
                 "chi": "tu", "perche": "", "priorita": "media", "quando": "settimana", "stato": "da fare",
                 "motivo": "", "dopo": [], "note": [], "creato": ts, "aggiornato": ts, "chiuso": "", "storia": []}
            t.update({k: v for k, v in dati.items() if k in CAMPI})
            t["progetto"] = t["progetto"] or "generale"  # righe scritte prima che il vuoto fosse rifiutato
            todo[uid] = t
        else:
            t = todo.get(uid)
            if t is None:
                avvisi.append(f"riga {numero}: evento per un todo che non esiste, saltato")
                continue
            if tipo == "modifica":
                t.update({k: v for k, v in dati.items() if k in CAMPI})
                t["progetto"] = t["progetto"] or "generale"
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

# Separatori di riga per Unicode che json.dumps lascia crudi con ensure_ascii=False. Nel registro
# vanno come escape JSON: così ogni lettore che spezza le righe come splitlines() le trova intere.
_SEPARATORI = {"\u0085": "\\u0085", "\u2028": "\\u2028", "\u2029": "\\u2029"}


def _riga_json(evento: dict) -> str:
    riga = json.dumps(evento, ensure_ascii=False, separators=(",", ":"))
    for crudo, escape in _SEPARATORI.items():
        riga = riga.replace(crudo, escape)
    return riga


def _scrivi_molti(eventi: list, file: Path) -> None:
    """Piu' eventi in una sola write(): chi legge li trova tutti o nessuno."""
    file.parent.mkdir(parents=True, exist_ok=True)
    righe = "".join(_riga_json(e) + "\n" for e in eventi).encode("utf-8")
    fd = os.open(str(file), os.O_WRONLY | os.O_APPEND | os.O_CREAT | getattr(os, "O_BINARY", 0), 0o600)
    try:
        os.write(fd, righe)
    finally:
        os.close(fd)


def _scrivi(evento: dict, file: Path) -> None:
    _scrivi_molti([evento], file)


def scrivi_json_atomico(path, dati) -> None:
    """Scrive `dati` come JSON in `path`: chi legge trova il file vecchio o quello nuovo, mai mezzo.

    Il testo va in un file temporaneo nella stessa cartella, poi os.replace() lo mette al posto
    giusto. Se la scrittura fallisce, il file di prima resta com'era.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    testo = json.dumps(dati, ensure_ascii=False, indent=2) + "\n"
    fd, temporaneo = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
            f.write(testo)
            f.flush()
            os.fsync(f.fileno())
        os.replace(temporaneo, str(path))
    except BaseException:
        try:
            os.unlink(temporaneo)
        except FileNotFoundError:
            pass
        raise


class Lucchetto:
    """Un file .lock accanto a `file` (Path o stringa): un solo processo alla volta nel blocco `with`.

    L'archivio lo usa per dare id diversi a due todo creati nello stesso istante. Altri moduli
    lo usano per i loro file. Un lucchetto piu' vecchio di 10 secondi e' di un processo interrotto
    e si toglie da solo.
    """

    def __init__(self, file):
        file = Path(file)
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


_Lucchetto = Lucchetto  # il nome di prima, per chi lo usa gia'


def _evento(tipo: str, uid: str, dati: dict, **altro) -> dict:
    return {"v": VERSIONE_EVENTI, "ts": _adesso(), "ev": uuid.uuid4().hex, "todo": uid, "tipo": tipo, "dati": dati, **altro}


def aggiungi(campi: dict, file: Path | None = None) -> dict:
    file = file or percorso()
    dati = normalizza(campi)
    if not dati.get("titolo"):
        raise ErroreTodo("il titolo non può essere vuoto")
    uid = uuid.uuid4().hex
    with Lucchetto(file):
        todo, _ = carica(file)
        numero = max((t["id"] for t in todo.values()), default=0) + 1
        _scrivi(_evento("crea", uid, dati, id=numero), file)
    return carica(file)[0][uid]


def registra(numero, tipo: str, dati: dict, file: Path | None = None) -> dict:
    """Modifica, stato, nota o dopo su un todo esistente, indicato col suo numero.

    Su stato e modifica, `"annullo": True` nei dati segna l'evento come annullo di un passo
    precedente (un clic sbagliato nel pannello o nella pagina). Il segno resta nella storia:
    chi legge i comportamenti della persona salta questi eventi.
    """
    file = file or percorso()
    todo, _ = carica(file)
    t = per_id(todo, numero)
    dati = dict(dati)
    annullo = bool(dati.pop("annullo", False))
    if annullo and tipo not in ("stato", "modifica"):
        raise ErroreTodo("il segno di annullo vale solo per stato e modifica")
    if tipo == "modifica":
        dati = normalizza(dati)
        if not dati:
            raise ErroreTodo("niente da modificare: indica almeno un campo")
    elif tipo == "stato":
        dati = {"stato": scelta(dati["stato"], STATI, "stato"), "motivo": dati.get("motivo", "") or ""}
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
    if annullo:
        dati["annullo"] = True
    _scrivi(_evento(tipo, t["uid"], dati), file)
    return carica(file)[0][t["uid"]]


def ripristina(numero, stato: str, motivo: str = "", file: Path | None = None) -> dict:
    """Rimette stato e motivo esatti di prima. E' l'inverso che usano pannello e pagina web."""
    return registra(numero, "stato", {"stato": stato, "motivo": motivo, "annullo": True}, file)


def deciso(numero, testo: str, file: Path | None = None) -> dict:
    """La persona ha deciso: nota «Deciso: testo» e chi passa a io, in una sola scrittura.

    Un todo chiuso si rifiuta: nessuno ci lavora piu', e il suo chi=decidi resta come segnale.
    Un todo FERMO accetta la decisione e resta FERMO: quando riparte, lo fa Claude.
    """
    file = file or percorso()
    testo = str(testo).strip()
    if not testo:
        raise ErroreTodo("scrivi cosa hai deciso, per esempio: arturo todo deciso 4 \"va bene il piano B\"")
    todo, _ = carica(file)
    t = per_id(todo, numero)
    if t["stato"] in ("fatto", "scartato"):
        raise ErroreTodo(f"il todo #{t['id']} è chiuso ({t['stato']}): riaprilo con riprendi prima di "
                         "registrare la decisione")
    if t["chi"] != "decidi":
        raise ErroreTodo(f"il todo #{t['id']} non aspetta una tua decisione: chi è «{t['chi']}», non «decidi»")
    nota = _evento("nota", t["uid"], {"testo": DECISO + testo})
    # Lo stesso ts sui due eventi: chi legge la storia riconosce la nota scritta da deciso
    # (l'ordine resta quello delle righe). Una nota scritta a mano ha sempre un ts suo.
    _scrivi_molti([nota, dict(_evento("modifica", t["uid"], {"chi": "io"}), ts=nota["ts"])], file)
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


def scadenza_testo(g):
    """Il testo unico della scadenza per tutte le viste. g = giorni da oggi, None = nessuna."""
    if g is None:
        return None
    if g < 0:
        return "scaduto ieri" if g == -1 else f"scaduto da {-g} g"
    return {0: "scade oggi", 1: "scade domani"}.get(g, f"scade tra {g} g")


def progetti(todo: dict) -> dict:
    """Per ogni progetto: quanti todo aperti, scaduti, fermi e chiusi."""
    conti = {}
    for t in todo.values():
        c = conti.setdefault(t["progetto"], {"aperti": 0, "scaduti": 0, "fermi": 0, "chiusi": 0})
        if gruppo(t) is None:
            c["chiusi"] += 1
            continue
        c["aperti"] += 1
        c["fermi"] += t["stato"] == "fermo"
        g = giorni(t)
        c["scaduti"] += g is not None and g < 0
    return conti


def _ordine(t: dict) -> tuple:
    g = giorni(t)
    return (0 if g is not None and g < 0 else 1, PRIORITA.index(t["priorita"]) if t["priorita"] in PRIORITA else 1,
            g if g is not None else 10 ** 6, t["id"])


def esporta(t: dict, todo: dict) -> dict:
    """Un todo nella forma del contratto JSON: niente uid, id numerici per le dipendenze."""
    per_uid = {x["uid"]: x for x in todo.values()}
    dopo = [per_uid[u] for u in t["dopo"] if u in per_uid]
    g = giorni(t)
    return {
        "id": t["id"], "titolo": t["titolo"], "progetto": t["progetto"], "scadenza": t["scadenza"] or None,
        "scadenza_testo": scadenza_testo(g), "giorni": g, "priorita": t["priorita"], "stato": t["stato"], "quando": t["quando"],
        "chi": t["chi"], "perche": t["perche"] or None, "motivo": t["motivo"] or None,
        "gruppo": gruppo(t), "dopo": [x["id"] for x in dopo],
        "attende": [x["id"] for x in dopo if x["stato"] in APERTI],
        "note": [n["testo"] for n in t["note"]],
    }


def vista(todo: dict, avvisi: list, progetto: str | None = None, tutti: bool = False) -> dict:
    scelti = [t for t in todo.values() if not progetto or t["progetto"] == progetto]
    gruppi = []
    for tipo, titolo, descrizione in GRUPPI:
        dentro = sorted((t for t in scelti if gruppo(t) == tipo), key=_ordine)
        gruppi.append({"tipo": tipo, "titolo": titolo, "descrizione": descrizione,
                       "todo": [esporta(t, todo) for t in dentro]})
    chiusi = sorted((t for t in scelti if gruppo(t) is None), key=lambda t: t["chiuso"], reverse=True)
    risultato = {"versione": VERSIONE_VISTA, "oggi": oggi().isoformat(), "progetto": progetto, "gruppi": gruppi,
                 "chiusi": len(chiusi), "avvisi": avvisi}
    if tutti:
        risultato["chiusi_todo"] = [esporta(t, todo) for t in chiusi]
    return risultato
