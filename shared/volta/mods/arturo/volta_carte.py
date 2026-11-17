"""Volta: le prove di una carta della Coda (#5720, 15/11/2026).

Una carta (hooks/carta-sessione.py) porta le prove come percorsi della macchina dove gira la sessione:
screenshot e video. La vista Coda (coda.js) mostra solo le immagini che stanno nella cartella dell'app di
Herdr (gpui-kit assets.rs), quindi questo script ne fa una copia lì, anche da un'altra macchina.

  python3 volta_carte.py prova <macchina|qui> <percorso> <destinazione>
  python3 volta_carte.py risposta <riga JSON>
  python3 volta_carte.py scarta <riga JSON>     {chiave, quando}: la carta resta fuori dalla Coda
  python3 volta_carte.py scartate               le carte scartate di questa macchina, {chiave: quando}
  python3 volta_carte.py recenti                le risposte UF delle ultime 48 ore, {chiave: ms} (#5742)

Stampa una riga JSON: {"ok": true, "byte": N} oppure {"errore": "..."}. Una copia che c'è già non si rifà.

`risposta` (#5721, step 4 del piano): ogni risposta data dalla Coda va in una riga di registro.jsonl, per
la misura delle raccomandazioni accettate (step 6). Il file sta in ~/.cache/volta-carte/ per la finestra
vera, in <HERDR_APP_HOME>/cache/volta-carte/ per una finestra di prova, in VOLTA_CARTE_REGISTRO per i
banchi. Una riga tiene solo i campi di CAMPI_RISPOSTA, tagliati, più `quando`. Stampa {"ok": true}.
Le altre macchine passano da herdr-core (hc exec --on, come volta_note.py), con python3 e poi python.
Tetto MAX_BYTE: una prova più grande resta dov'è, e la carta mostra il percorso.
"""
import base64
import json
import os
import subprocess
import sys
import time
from datetime import datetime
# Niente .pyc nella cartella del mod: Herdr ricarica il mod a ogni file nuovo (#5556, come volta_note.py).
sys.dont_write_bytecode = True
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from volta_sonda import errore_hc, hc, non_parte  # noqa: E402

MAX_BYTE = 8 * 1024 * 1024
ATTESA = 40
ESTENSIONI = (".png", ".jpg", ".jpeg", ".gif", ".webp", ".mp4", ".mov")
# Il codice che gira sull'altra macchina: legge il file in base64, entro il tetto.
LEGGI = ("import base64,json,os,sys;p=sys.argv[1];n=os.path.getsize(p) if os.path.isfile(p) else -1;"
         "print(json.dumps({'manca':True} if n<0 else {'grande':n} if n>%d else "
         "{'b64':base64.b64encode(open(p,'rb').read()).decode()}))" % MAX_BYTE)


def scrivi(dest, dati):
    os.makedirs(os.path.dirname(dest) or ".", exist_ok=True)
    tmp = "%s.%d.tmp" % (dest, os.getpid())
    with open(tmp, "wb") as fh:
        fh.write(dati)
    os.replace(tmp, dest)
    return {"ok": True, "byte": len(dati)}


def da_qui(percorso):
    p = os.path.expanduser(percorso)
    if not os.path.isfile(p):
        return None, "la prova non c'è più"
    if os.path.getsize(p) > MAX_BYTE:
        return None, "la prova è più grande di 8 MB"
    with open(p, "rb") as fh:
        return fh.read(), None


def da_la(macchina, percorso):
    ultimo = "nessun Python"
    for py in ("python3", "python"):
        argv = hc() + ["exec", "--on", macchina, "--timeout", str(ATTESA), py, "-c", LEGGI, percorso]
        try:
            r = subprocess.run(argv, capture_output=True, text=True, encoding="utf-8", errors="replace",
                               timeout=ATTESA + 5, stdin=subprocess.DEVNULL)
        except (OSError, subprocess.TimeoutExpired):
            return None, "%s non ha risposto in tempo" % macchina
        if non_parte(r.stdout, r.stderr):
            ultimo = "%s non ha %s" % (macchina, py)
            continue
        riga = (r.stdout.strip().splitlines() or [""])[-1]
        try:
            d = json.loads(riga)
        except ValueError:
            d = None
        # hc scrive i suoi errori come {"error": {...}} sulla stessa uscita: non è una prova vuota
        if not isinstance(d, dict) or not ({"manca", "grande", "b64"} & set(d)):
            return None, errore_hc(riga or r.stderr) or "%s non risponde" % macchina
        if d.get("manca"):
            return None, "la prova non c'è più su %s" % macchina
        if d.get("grande"):
            return None, "la prova è più grande di 8 MB"
        try:
            return base64.b64decode(d.get("b64") or ""), None
        except ValueError:
            return None, "la prova è arrivata a metà"
    return None, ultimo


def prova(macchina, percorso, dest):
    if not percorso.lower().endswith(ESTENSIONI):
        return {"errore": "non è un'immagine né un video"}
    dest = os.path.expanduser(dest)
    if os.path.isfile(dest):
        return {"ok": True, "byte": os.path.getsize(dest), "gia": True}
    dati, errore = da_qui(percorso) if macchina in ("qui", "") else da_la(macchina, percorso)
    return {"errore": errore} if errore else scrivi(dest, dati)


# I campi di una riga del registro delle risposte, col tetto dei caratteri; numero e accettata a parte.
CAMPI_RISPOSTA = {"chiave": 80, "macchina": 60, "progetto": 40, "tipo": 20, "canale": 20, "esito": 20,
                  "raccomandazione": 200, "scelta": 200, "nota": 300, "errore": 160}
# Le carte scartate dalla Coda (16/11/2026): {chiave: istante della carta}, al più SCARTATE_MAX, le più recenti.
SCARTATE_MAX = 500
# Le risposte UF che Volta rilegge dopo un riavvio (#5742): le ultime RECENTI_ORE ore del registro.
RECENTI_ORE = 48
RIMANDA_MS = 24 * 3600 * 1000


def registro_risposte():
    if os.environ.get("VOLTA_CARTE_REGISTRO"):
        return os.environ["VOLTA_CARTE_REGISTRO"]
    serie = os.path.join(os.path.expanduser("~"), ".config", "herdr-app")
    app = os.environ.get("HERDR_APP_HOME") or serie
    if os.path.normcase(os.path.abspath(app)) != os.path.normcase(os.path.abspath(serie)):
        return os.path.join(app, "cache", "volta-carte", "registro.jsonl")
    return os.path.join(os.path.expanduser("~"), ".cache", "volta-carte", "registro.jsonl")


def riga_risposta(d, quando=None):
    """La riga come entra nel registro, o None se non è una risposta (manca la chiave)."""
    if not isinstance(d, dict) or not isinstance(d.get("chiave"), str) or not d["chiave"]:
        return None
    r = {"quando": quando or time.strftime("%Y-%m-%dT%H:%M:%S%z")}
    for k, n in CAMPI_RISPOSTA.items():
        v = d.get(k)
        if v is None or isinstance(v, (dict, list, bool)):
            continue
        r[k] = " ".join(str(v).split())[:n]
    if isinstance(d.get("numero"), int) and not isinstance(d["numero"], bool) and 0 <= d["numero"] <= 9:
        r["numero"] = d["numero"]
    if isinstance(d.get("accettata"), bool):
        r["accettata"] = d["accettata"]
    # capo: la raccomandazione l'ha data il capo di gabinetto (#5723), non la sessione
    if d.get("capo") is True:
        r["capo"] = True
    return r


def risposta(testo):
    try:
        d = json.loads(testo)
    except ValueError:
        return {"errore": "la riga non è JSON"}
    r = riga_risposta(d)
    if r is None:
        return {"errore": "manca la chiave della carta"}
    f = registro_risposte()
    try:
        os.makedirs(os.path.dirname(f) or ".", exist_ok=True)
        with open(f, "a", encoding="utf-8") as fh:  # una riga corta in append: niente lock
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    except OSError as e:
        return {"errore": "non scrivo il registro: %s" % str(e)[:120]}
    return {"ok": True}


def file_scartate():
    return os.path.join(os.path.dirname(registro_risposte()) or ".", "scartate.json")


def scartate():
    """Le carte scartate di questa macchina, {chiave: istante}; {} se il file manca o è storto."""
    try:
        with open(file_scartate(), encoding="utf-8") as fh:
            d = json.load(fh)
    except (OSError, ValueError):
        return {}
    if not isinstance(d, dict):
        return {}
    return {k: v for k, v in d.items() if isinstance(k, str) and isinstance(v, (int, float)) and not isinstance(v, bool)}


def scarta(testo):
    """Aggiunge una carta alle scartate: {chiave, quando}. Scrittura atomica, tetto SCARTATE_MAX."""
    try:
        d = json.loads(testo)
    except ValueError:
        return {"errore": "la riga non è JSON"}
    k = d.get("chiave") if isinstance(d, dict) else None
    q = d.get("quando") if isinstance(d, dict) else None
    if not isinstance(k, str) or not k or len(k) > 80 or not isinstance(q, (int, float)) or isinstance(q, bool):
        return {"errore": "servono chiave e quando"}
    tutte = scartate()
    tutte.pop(k, None)
    tutte[k] = q
    tutte = dict(list(tutte.items())[-SCARTATE_MAX:])
    f = file_scartate()
    try:
        os.makedirs(os.path.dirname(f) or ".", exist_ok=True)
        tmp = "%s.%d.tmp" % (f, os.getpid())
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(tutte, fh, ensure_ascii=False)
        os.replace(tmp, f)
    except OSError as e:
        return {"errore": "non scrivo le scartate: %s" % str(e)[:120]}
    return {"ok": True, "scartate": len(tutte)}


def recenti(ora=None, ore=RECENTI_ORE):
    """Le risposte alle carte UF delle ultime `ore` ore, dal registro: {chiave: istante in ms}. Dopo un riavvio
    Volta le rimette nelle sue risposte, e una carta già risposta resta fuori fino al giro dopo del capo
    (#5742). Rimanda su una bozza vale fino a 24 ore dopo, come in volta.js (RIMANDA_MS)."""
    ora = ora if ora is not None else time.time()
    fuori = {}
    try:
        with open(registro_risposte(), encoding="utf-8") as fh:
            righe = fh.readlines()[-5000:]
    except OSError:
        return fuori
    for x in righe:
        try:
            d = json.loads(x)
            q = datetime.strptime(str(d.get("quando")), "%Y-%m-%dT%H:%M:%S%z").timestamp()
        except (ValueError, TypeError):
            continue
        k = d.get("chiave") if isinstance(d, dict) else None
        if d.get("canale") != "uf" or d.get("esito") == "errore" or not isinstance(k, str) or ora - q > ore * 3600:
            continue
        ms = int(q * 1000) + (RIMANDA_MS if k.startswith("bozza:") and d.get("scelta") == "Rimanda" else 0)
        fuori[k] = max(fuori.get(k, 0), ms)
    return fuori


def main(argv):
    if argv == ["recenti"]:
        print(json.dumps(recenti(), ensure_ascii=True))
        return 0
    if len(argv) == 2 and argv[0] == "risposta":
        print(json.dumps(risposta(argv[1]), ensure_ascii=True))
        return 0
    if len(argv) == 2 and argv[0] == "scarta":
        print(json.dumps(scarta(argv[1]), ensure_ascii=True))
        return 0
    if argv == ["scartate"]:
        print(json.dumps(scartate(), ensure_ascii=True))
        return 0
    if len(argv) != 4 or argv[0] != "prova":
        print(json.dumps({"errore": "uso: volta_carte.py prova <macchina|qui> <percorso> <destinazione> | risposta <riga JSON> | scarta <riga JSON> | scartate"}))
        return 2
    print(json.dumps(prova(argv[1], argv[2], argv[3]), ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
