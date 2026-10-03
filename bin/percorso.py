"""arturo percorso: il percorso a tappe, calcolato dall'archivio dei todo.

Le tappe sono quattro: Osserva, Prova, Delega, Orchestra. Si sbloccano con segni di
giudizio, non con il volume: una decisione presa prima del lavoro di Claude, un limite
dichiarato, un no motivato. Il numero di cose delegate non conta mai.

Il modulo legge l'archivio dei todo e non ci scrive mai. Il suo stato (la tappa gia' vista,
i suggerimenti di /fine, la pausa) sta in ~/.claude/session-env/percorso.json, sul computer
della persona. Il modulo non usa la rete e non invia niente.

Un todo spostato da tu a decidi e subito a io (due tasti «c» di fila nel pannello) non conta
come decisione: la persona lo ha affidato a Claude, non ha deciso niente.

Gli annulli non contano. Un evento con il segno `annullo` (un clic annullato nel pannello o
nella pagina, un `ripristina`) toglie dalla storia anche il passo che annulla: un clic
sbagliato non sblocca nessuna tappa.

Solo libreria standard, Python 3.8 o successivo.
"""
from __future__ import annotations

import datetime as dt
import json
import os
import re
import sys
from pathlib import Path

import todo_store as ts

VERSIONE = 1
TAPPE = ("Osserva", "Prova", "Delega", "Orchestra")
# Il capitolo del curriculum di ogni tappa. Orchestra non ne ha uno suo: la skill propone /sparring.
CAPITOLI = (
    "docs/principi/00-chi-possiede-lo-strumento.md",
    "docs/principi/01-chiedere-bene.md",
    "docs/principi/05-tieni-la-decisione.md",
    None,
)
SEGNI = (
    ("Hai almeno un todo nell'archivio",),
    ("Claude ha chiuso un lavoro per te",),
    ("Hai deciso prima che Claude lavorasse", "Hai tenuto un limite o detto un no motivato"),
    ("Una tua decisione ha aperto il lavoro di Claude",),
)
TENUTO = "Tenuto: "
NIENTE = ("niente", "nulla", "nessuna", "nessuno")
CHIAVI = ("versione", "oggi", "tappa", "nome", "nuova_tappa", "tappe", "tieni_tu", "domanda", "esercizio",
          "suggerimenti", "avvisi")
INTESTAZIONE = re.compile(r"^## (E\d{2}) · (Osserva|Prova|Delega|Orchestra) · (.+)$")
CODICE = re.compile(r"\bE\d{2}\b")
# Quanto tace Claude dopo un no a una proposta di /fine, e dopo due no di fila. In giorni.
SILENZIO_UN_NO = 3
SILENZIO_DUE_NO = 14
ULTIMI_SUGGERIMENTI = 10
# Un passaggio tu -> decidi -> io piu' rapido di cosi', senza altri eventi in mezzo, e' un gesto solo.
DI_FILA = 10
PAUSA = "in pausa finché non dici riprendi"
GIA_OGGI = "già uno oggi"


def radice() -> Path:
    """La cartella di Arturo: bin/.. anche quando bin/arturo e' un collegamento."""
    return Path(os.path.realpath(__file__)).parent.parent


def file_stato() -> Path:
    return Path.home() / ".claude" / "session-env" / "percorso.json"


# --- la storia di un todo, senza gli annulli -----------------------------------

def storia_pulita(t: dict) -> tuple:
    """Torna (storia senza annulli, tolto).

    Un evento con `annullo` toglie anche il passo che annulla: l'ultimo evento dello stesso tipo
    che non e' un annullo (per una modifica, uno che tocca almeno un campo uguale). Se il passo
    tolto e' il passaggio a io di `deciso`, va via anche la nota «Deciso:» scritta insieme.
    Un annullo che chiude il todo senza un passo da togliere annulla la creazione (l'Annulla
    di un aggiungi nella pagina): allora il todo e' «tolto» e il percorso non lo legge. Un passo
    vero dopo quell'annullo (un Riprendi, una modifica, una nota) lo rimette nel percorso.
    """
    storia = t["storia"]
    via, tolto_da = set(), None
    for i, e in enumerate(storia):
        dati = e["dati"]
        if not dati.get("annullo"):
            continue
        via.add(i)
        campi = set(dati) - {"annullo"}
        trovato = False
        for j in range(i - 1, -1, -1):
            p = storia[j]
            if j in via or p["tipo"] != e["tipo"] or p["dati"].get("annullo"):
                continue
            if e["tipo"] == "modifica" and not (set(p["dati"]) & campi):
                continue
            via.add(j)
            trovato = True
            prima = storia[j - 1] if j > 0 else None
            # La nota va via solo se e' nata nella stessa scrittura di `deciso`: stesso ts.
            # Una nota «Deciso:» scritta a mano prima del clic resta una decisione.
            if (e["tipo"] == "modifica" and p["dati"].get("chi") == "io" and prima is not None
                    and prima["tipo"] == "nota" and prima["ts"] == p["ts"]
                    and str(prima["dati"].get("testo", "")).startswith(ts.DECISO)):
                via.add(j - 1)
            break
        if not trovato and e["tipo"] == "stato" and dati.get("stato") == "scartato":
            tolto_da = i
    tolto = tolto_da is not None and all(j in via for j in range(tolto_da + 1, len(storia)))
    return [e for i, e in enumerate(storia) if i not in via], tolto


def _istante(valore: str):
    try:
        return dt.datetime.fromisoformat(valore)
    except (TypeError, ValueError):
        return None


def tenuto_decidi(ingresso, posizione: int, quando: str) -> bool:
    """Il todo era davvero DECIDI TU prima del passaggio a io?

    Si': se e' nato decidi, se tra l'ingresso in decidi e il passaggio c'e' un altro evento, o se
    sono passati almeno DI_FILA minuti. No: se il passaggio segue subito l'ingresso, come i due
    tasti «c» di fila nel pannello (tu, decidi, io). Quello e' un affidamento, non una decisione.
    """
    if ingresso is None:
        return True
    dove, entrato = ingresso
    if posizione - dove > 1:
        return True
    prima, dopo = _istante(entrato), _istante(quando)
    if prima is None or dopo is None:
        return False
    try:
        return dopo - prima >= dt.timedelta(minutes=DI_FILA)
    except TypeError:  # un ts con il fuso e uno senza
        return False


def leggi(t: dict) -> dict:
    """Quello che il percorso sa di un todo. Stato, chiusura e decisione vengono dalla storia pulita.

    `deciso` e' l'istante della prima decisione: la nota «Deciso:» su un todo decidi, o il
    passaggio da decidi a io quando il todo era gia' decidi (vedi tenuto_decidi).
    """
    pulita, tolto = storia_pulita(t)
    chi, stato, motivo, chiuso = "tu", "da fare", "", ""
    decisione, riaperto, deciso = False, False, ""
    ingresso = None  # (posizione, ts) della modifica che ha portato il todo a decidi; None se e' nato decidi
    for i, e in enumerate(pulita):
        tipo, dati = e["tipo"], e["dati"]
        if tipo == "crea":
            chi = dati.get("chi") or "tu"
        elif tipo == "modifica" and "chi" in dati:
            if chi == "decidi" and dati["chi"] == "io" and tenuto_decidi(ingresso, i, e["ts"]):
                decisione = True
                deciso = deciso or e["ts"]
            if dati["chi"] == "decidi" and chi != "decidi":
                ingresso = (i, e["ts"])
            chi = dati["chi"]
        elif tipo == "nota" and chi == "decidi" and str(dati.get("testo", "")).startswith(ts.DECISO):
            decisione = True
            deciso = deciso or e["ts"]
        elif tipo == "stato" and dati.get("stato") in ts.STATI:
            if stato == "fatto" and dati["stato"] in ts.APERTI:
                riaperto = True
            stato, motivo = dati["stato"], dati.get("motivo", "") or ""
            chiuso = e["ts"] if stato in ("fatto", "scartato") else ""
    # Lo stato conta solo se la storia pulita e l'archivio dicono la stessa cosa.
    concorde = stato == t["stato"]
    return {
        "tolto": tolto,
        "fatto": concorde and stato == "fatto",
        "scartato": concorde and stato == "scartato",
        "motivo": motivo if concorde else "",
        "chiuso": chiuso if concorde else "",
        "decisione": decisione,
        "deciso": deciso,
        "riaperto": riaperto,
    }


def segnali(todo: dict) -> list:
    """I todo che il percorso legge: niente esercizi del percorso, niente todo tolti da un annullo."""
    fuori = []
    for t in sorted(todo.values(), key=lambda x: x["id"]):
        if t["progetto"] == ts.PROGETTO_PERCORSO:
            continue
        info = leggi(t)
        if not info["tolto"]:
            fuori.append((t, info))
    return fuori


# --- le tappe -----------------------------------------------------------------

def _prima(prove) -> int | None:
    """La prova di un segno: l'id piu' basso che lo soddisfa, None se nessuno."""
    return min(prove, default=None)


def tappe(todo: dict) -> list:
    letti = segnali(todo)
    per_uid = {t["uid"]: (t, info) for t, info in letti}

    osserva = _prima(t["id"] for t, _ in letti)
    prova = _prima(t["id"] for t, info in letti if t["chi"] in ("io", "decidi") and info["fatto"])
    decisione = _prima(t["id"] for t, info in letti if info["decisione"])
    limite = _prima(
        t["id"] for t, info in letti
        if (t["chi"] == "tu" and (t["perche"] or "").strip())
        or (t["chi"] in ("io", "decidi") and info["scartato"] and info["motivo"].strip())
        or (t["chi"] == "io" and info["riaperto"])
    )

    def apre(x, info_x) -> bool:
        """X e' un lavoro di Claude chiuso che aspettava Y. Conta il momento della decisione su Y:
        con `deciso` il todo passa a io e resta aperto, quindi la chiusura di Y non serve. Un Y tu o
        decidi senza decisione conta se e' fatto e chiuso prima di X."""
        if x["chi"] != "io" or not info_x["fatto"]:
            return False
        for uid in x["dopo"]:
            y, info_y = per_uid.get(uid, (None, None))
            if y is None:
                continue
            if info_y["decisione"]:
                if info_y["deciso"] <= info_x["chiuso"]:
                    return True
            elif info_y["fatto"] and y["chi"] in ("tu", "decidi") and info_y["chiuso"] <= info_x["chiuso"]:
                return True
        return False

    orchestra = _prima(t["id"] for t, info in letti if apre(t, info))
    prove = ((osserva,), (prova,), (decisione, limite), (orchestra,))
    fuori = []
    for numero, (nome, testi, ids, capitolo) in enumerate(zip(TAPPE, SEGNI, prove, CAPITOLI), 1):
        segni = [{"testo": testo, "prova": n} for testo, n in zip(testi, ids)]
        fuori.append({"numero": numero, "nome": nome, "fatta": all(s["prova"] is not None for s in segni),
                      "segni": segni, "capitolo": capitolo})
    return fuori


def tappa_attuale(elenco: list) -> int:
    """La tappa k piu' alta con le tappe da 1 a k tutte fatte. 0 se nessuna."""
    k = 0
    for voce in elenco:
        if not voce["fatta"]:
            break
        k = voce["numero"]
    return k


def tieni_tu(todo: dict) -> list:
    """Le cose che la persona tiene per se': i perche dei todo tu e le note «Tenuto: …»."""
    voci = []
    for t in todo.values():
        info = leggi(t)
        if info["tolto"]:
            continue
        if t["chi"] == "tu" and t["progetto"] != ts.PROGETTO_PERCORSO and (t["perche"] or "").strip():
            voci.append((t["creato"], t["id"], t["perche"].strip()))
        for nota in t["note"]:
            testo = nota["testo"]
            tenuto = testo[len(TENUTO):].strip() if testo.startswith(TENUTO) else ""
            # «Tenuto: niente» e' una risposta valida, ma non e' una regola da mettere in lista.
            if tenuto and tenuto.rstrip(".!").strip().casefold() not in NIENTE:
                voci.append((nota["ts"], t["id"], tenuto))
    fuori, visti = [], set()
    for _, _, testo in sorted(voci, key=lambda v: (v[0], v[1])):
        chiave = testo.casefold()
        if chiave not in visti:
            visti.add(chiave)
            fuori.append(testo)
    return fuori


def domanda(todo: dict):
    """Il todo tu aperto con l'id piu' basso e senza perche: la sola domanda che Claude puo' fare."""
    for t, _ in segnali(todo):
        if t["chi"] == "tu" and t["stato"] in ("da fare", "in corso") and not (t["perche"] or "").strip():
            return {"id": t["id"], "titolo": t["titolo"]}
    return None


# --- gli esercizi -------------------------------------------------------------

def esercizi(path: Path | None = None) -> tuple:
    """Gli esercizi di docs/esercizi.md. Torna (lista, avvisi). Un file assente o senza esercizi: []."""
    path = path or radice() / "docs" / "esercizi.md"
    try:
        righe = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeDecodeError):
        righe = []
    lista = []
    for riga in righe:
        m = INTESTAZIONE.match(riga.rstrip())
        if m:
            lista.append({"codice": m.group(1), "tappa": m.group(2), "titolo": m.group(3).strip()})
    if not lista:
        return [], ["esercizi non trovati: docs/esercizi.md manca o non ha intestazioni valide"]
    return lista, []


def esercizio(todo: dict, tappa: int, oggi: dt.date, lista: list):
    """L'esercizio della settimana. Un esercizio aperto nel progetto del percorso resta finché lo chiudi."""
    per_codice = {e["codice"]: e for e in lista}
    del_percorso = sorted((t for t in todo.values() if t["progetto"] == ts.PROGETTO_PERCORSO), key=lambda t: t["id"])
    fatti = set()
    for t in del_percorso:
        codici = [c for c in CODICE.findall(t["titolo"]) if c in per_codice]
        if not codici or leggi(t)["tolto"]:
            continue
        if t["stato"] in ts.APERTI:
            e = per_codice[codici[0]]
            return {"codice": e["codice"], "titolo": e["titolo"], "tappa": e["tappa"], "todo": t["id"]}
        fatti.update(codici)
    prossima = min(tappa + 1, len(TAPPE))
    candidati = [e for e in lista if e["tappa"] == TAPPE[prossima - 1] and e["codice"] not in fatti]
    if not candidati:
        candidati = [e for e in lista if TAPPE.index(e["tappa"]) + 1 <= prossima and e["codice"] not in fatti]
    if not candidati:
        return None
    candidati.sort(key=lambda e: e["codice"])
    e = candidati[oggi.isocalendar()[1] % len(candidati)]
    return {"codice": e["codice"], "titolo": e["titolo"], "tappa": e["tappa"], "todo": None}


# --- lo stato locale ----------------------------------------------------------

def _data_valida(valore) -> bool:
    if not isinstance(valore, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", valore):
        return False
    try:
        dt.date.fromisoformat(valore)
    except ValueError:
        return False
    return True


def leggi_stato(file: Path | None = None) -> tuple:
    """Torna (stato, avvisi). Un file assente vale {}. Un file rotto vale {} con un avviso."""
    file = file or file_stato()
    if not file.exists():
        return {}, []
    try:
        grezzo = json.loads(file.read_text(encoding="utf-8"))
    except (OSError, ValueError, UnicodeDecodeError):
        return {}, ["lo stato del percorso è illeggibile: riparte da capo, e il prossimo comando lo riscrive"]
    if not isinstance(grezzo, dict):
        return {}, ["lo stato del percorso ha una forma sbagliata: riparte da capo"]
    stato = {}
    vista = grezzo.get("tappa_vista")
    if type(vista) is int and 0 <= vista <= len(TAPPE):
        stato["tappa_vista"] = vista
    suggerimenti = grezzo.get("suggerimenti")
    if isinstance(suggerimenti, list):
        stato["suggerimenti"] = [{"data": s["data"], "esito": s.get("esito")} for s in suggerimenti
                                 if isinstance(s, dict) and _data_valida(s.get("data")) and s.get("esito") in (None, "no")]
    if grezzo.get("pausa") == "sempre":
        stato["pausa"] = "sempre"
    return stato, []


def cambia_stato(cambia, file: Path | None = None) -> dict:
    """Rilegge lo stato, applica `cambia(stato)` e lo riscrive, tutto sotto il lucchetto."""
    file = file or file_stato()
    with ts.Lucchetto(file):
        stato, _ = leggi_stato(file)
        cambia(stato)
        pulito = {"tappa_vista": stato.get("tappa_vista", 0),
                  "suggerimenti": stato.get("suggerimenti", [])[-ULTIMI_SUGGERIMENTI:],
                  "pausa": stato.get("pausa")}
        ts.scrivi_json_atomico(file, pulito)
    return pulito


GIORNI = ("lunedì", "martedì", "mercoledì", "giovedì", "venerdì", "sabato", "domenica")
MESI = ("gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno", "luglio", "agosto", "settembre",
        "ottobre", "novembre", "dicembre")


def _giorno(d: dt.date) -> str:
    """Una data in parole, senza articolo: «giovedì 8 ottobre»."""
    return f"{GIORNI[d.weekday()]} {d.day} {MESI[d.month - 1]}"


def suggeribile(stato: dict, oggi: dt.date) -> tuple:
    """Torna (si puo' proporre una delega, motivo). Le soglie sono una preferenza della persona."""
    if stato.get("pausa") == "sempre":
        return False, PAUSA
    suggerimenti = stato.get("suggerimenti", [])
    if any(s["data"] == oggi.isoformat() for s in suggerimenti):
        return False, GIA_OGGI
    fine, perche = silenzio(stato)
    if fine is not None and oggi < fine:
        return False, f"{perche}, Claude torna a proporre da {_giorno(fine)}"
    return True, None


def silenzio(stato: dict) -> tuple:
    """Torna (primo giorno in cui Claude puo' proporre di nuovo, perche'), o (None, None) senza un no."""
    suggerimenti = stato.get("suggerimenti", [])
    if not suggerimenti or suggerimenti[-1]["esito"] != "no":
        return None, None
    ultimo = dt.date.fromisoformat(suggerimenti[-1]["data"])
    due_no = len(suggerimenti) >= 2 and suggerimenti[-2]["esito"] == "no"
    giorni, perche = (SILENZIO_DUE_NO, "dopo due no di fila") if due_no else (SILENZIO_UN_NO, "dopo un no")
    return ultimo + dt.timedelta(days=giorni), perche


# --- il contratto -------------------------------------------------------------

def calcola(todo: dict, avvisi: list, stato: dict, avvisi_stato: list, oggi: dt.date) -> dict:
    elenco = tappe(todo)
    k = tappa_attuale(elenco)
    lista, avvisi_esercizi = esercizi()
    disponibile, motivo = suggeribile(stato, oggi)
    return {
        "versione": VERSIONE,
        "oggi": oggi.isoformat(),
        "tappa": k,
        "nome": TAPPE[k - 1] if k else None,
        "nuova_tappa": k > stato.get("tappa_vista", 0),
        "tappe": elenco,
        "tieni_tu": tieni_tu(todo),
        "domanda": domanda(todo),
        "esercizio": esercizio(todo, k, oggi, lista),
        "suggerimenti": {"disponibile": disponibile, "motivo": motivo, "pausa": stato.get("pausa")},
        "avvisi": list(avvisi) + list(avvisi_stato) + avvisi_esercizi,
    }


def testo(v: dict) -> str:
    """Il percorso in parole per la persona: niente conteggi, niente toni di rimprovero."""
    righe = ["Il tuo percorso. Si calcola solo su questo computer, dai tuoi todo.", ""]
    if v["tappa"]:
        righe.append(f"Tappa attuale: {v['nome']}.")
    else:
        righe.append("Sei all'inizio. La prima tappa è Osserva.")
    for voce in v["tappe"]:
        stato = "fatta" if voce["fatta"] else "aperta"
        for i, segno in enumerate(voce["segni"]):
            prova = f"#{segno['prova']}" if segno["prova"] is not None else "non ancora"
            testa = f"  {voce['nome']:<10} {stato:<7}" if i == 0 else " " * 20
            righe.append(f"{testa} {segno['testo']}: {prova}")
    if v["nuova_tappa"]:
        capitolo = v["tappe"][v["tappa"] - 1]["capitolo"]
        righe += ["", f"Tappa nuova: {v['nome']}." + (f" Il capitolo che la racconta: {capitolo}" if capitolo
                                                      else " Se vuoi, prova /sparring sul capitolo 05.")]
    righe += ["", "Cose che tieni per te:"]
    righe += [f"  - {x}" for x in v["tieni_tu"]] or ["  ancora nessuna. Le scrivi con --perche su un todo tuo."]
    if v["domanda"]:
        d = v["domanda"]
        righe += ["", f"Una domanda: #{d['id']} «{d['titolo']}» resta a te. Perché?"]
    e = v["esercizio"]
    if e:
        if e["todo"]:
            righe += ["", f"Esercizio aperto: {e['codice']} · {e['tappa']} · {e['titolo']} (todo #{e['todo']})."]
        else:
            righe += ["", f"Esercizio di questa settimana: {e['codice']} · {e['tappa']} · {e['titolo']}.",
                      "Lo trovi in docs/esercizi.md."]
    if v["suggerimenti"]["pausa"] == "sempre":
        righe += ["", "Proposte di delega a fine sessione: in pausa. Le riattivi con: arturo percorso riprendi"]
    return "\n".join(righe)


AIUTO = """Il percorso a tappe (scrivi «arturo percorso» davanti a ognuno):

  (niente) [--json]   la tappa, i segni con il todo che li prova, le cose che tieni per te
  visto               segna come vista la tappa attuale
  suggerisci          /fine chiede se può proporre una delega: esce con 0 (sì) o 3 (taci)
  no                  la persona ha detto no alla proposta: Claude tace per qualche giorno
  basta               nessuna proposta finché non dici riprendi
  riprendi            le proposte ripartono
  aiuto               questo testo

Codici di uscita: 0 fatto, 2 errore, 3 (solo suggerisci) oggi Claude non propone niente.
Il calcolo e lo stato restano su questo computer: lo stato sta in ~/.claude/session-env/percorso.json.
"""


def avvisa(avvisi: list) -> None:
    for a in avvisi:
        print(f"Attenzione: {a}", file=sys.stderr)


def main(argv: list) -> int:
    if argv[:1] in (["-h"], ["--help"], ["aiuto"], ["help"]):
        print(AIUTO)
        return 0
    comando = argv[0] if argv and not argv[0].startswith("-") else ""
    resto = argv[1:] if comando else argv
    if resto in (["-h"], ["--help"]):
        print(AIUTO)
        return 0
    ammessi = {"": ["--json"], "visto": [], "suggerisci": [], "no": [], "basta": [], "riprendi": []}
    if comando not in ammessi or any(x not in ammessi[comando] for x in resto):
        sbagliato = comando if comando not in ammessi else " ".join(resto)
        print(f"Errore: comando o opzione sconosciuta: «{sbagliato}»\n\n{AIUTO}", file=sys.stderr)
        return 2
    oggi = ts.oggi()

    if comando == "":
        todo, avvisi = ts.carica()
        stato, avvisi_stato = leggi_stato()
        v = calcola(todo, avvisi, stato, avvisi_stato, oggi)
        if "--json" in resto:
            print(json.dumps(v, ensure_ascii=False, indent=2))
        else:
            avvisa(v["avvisi"])
            print(testo(v))
        return 0

    if comando == "visto":
        todo, avvisi = ts.carica()
        avvisa(avvisi)
        k = tappa_attuale(tappe(todo))
        cambia_stato(lambda s: s.__setitem__("tappa_vista", k))
        print(f"Tappa vista: {TAPPE[k - 1] if k else 'nessuna'}.")
        return 0

    if comando == "suggerisci":
        stato, avvisi_stato = leggi_stato()
        avvisa(avvisi_stato)
        si, motivo = suggeribile(stato, oggi)
        if not si:
            print(f"Niente proposte oggi: {motivo}.")
            return 3
        cambia_stato(lambda s: s.setdefault("suggerimenti", []).append({"data": oggi.isoformat(), "esito": None}))
        print("Puoi proporre una delega, una sola.")
        return 0

    if comando == "no":
        def segna(s: dict) -> None:
            # Una proposta al giorno: un secondo no nello stesso giorno risponde alla stessa proposta.
            elenco = s.setdefault("suggerimenti", [])
            if elenco and elenco[-1]["data"] == oggi.isoformat():
                elenco[-1]["esito"] = "no"
            else:
                elenco.append({"data": oggi.isoformat(), "esito": "no"})
        fine, _ = silenzio(cambia_stato(segna))
        print(f"Va bene. Claude torna a proporre deleghe da {_giorno(fine)}.")
        return 0

    if comando == "basta":
        cambia_stato(lambda s: s.__setitem__("pausa", "sempre"))
        print("Va bene. Niente proposte di delega finché non dici: arturo percorso riprendi")
        return 0

    cambia_stato(lambda s: s.__setitem__("pausa", None))
    print("Le proposte di delega ripartono, al massimo una al giorno.")
    return 0
