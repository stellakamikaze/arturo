"""Volta: le note sulla finestra uguali su tutte le macchine di Herdr (12/11/2026).

Una nota (⌘⇧N) è una cartella ~/.claude/data/note-finestra/<data-ora>/ con nota.json e finestra.png, sulla
macchina dove nasce. Questo script la porta sulle altre macchine di `hc machine ls` e riporta qui le loro:
così Claude la trova con `arturo note` dovunque lavori, e la finestra di ogni macchina la mostra.

  python3 volta_note.py sincronizza [--scrivi FILE]   un giro con ogni macchina collegata

Un giro, per ogni macchina: legge i nota.json di là (LEGGI), scarica le note che mancano qui (png prima,
nota.json per ultimo), spinge le note che mancano di là, e per le note che stanno da tutte e due le parti
scrive su ogni lato l'unione (unisci). Ogni scrittura è un compare-and-swap sul testo letto: se il file è
cambiato nel frattempo (Claude ha appena risposto, il velo ha chiuso la nota) salta, e il giro dopo rifà
l'unione sul testo nuovo. L'unione non guarda gli orologi ed è commutativa: due Volta aperte che fanno lo
stesso giro insieme arrivano alla stessa nota.

Le note non si cancellano: una cartella tolta a mano torna dall'altra macchina. Si chiude con Risolta o Scarta.
I comandi sull'altra macchina passano da herdr-core (hc exec --on, -i per il pacco su stdin), come in
volta_sonda.py, da cui vengono hc(), macchine() e le altre funzioni di servizio. Niente nomi di macchine qui.
Per le prove: VOLTA_HC (il comando hc), CLAUDE_CONFIG_DIR (la cartella della persona).
"""
import base64
import json
import os
import subprocess
import sys
import time
import zlib
# Niente .pyc nella cartella del mod: Herdr ricarica il mod a ogni file nuovo che vi compare, anche in
# __pycache__, e la ricarica ferma per sempre le attese di Volta (cx.sleep di Sposta, #5556, 13/11/2026).
# La variabile vale per i Python figli (lo spostamento staccato, il microfono).
sys.dont_write_bytecode = True
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from volta_sonda import errore_hc, hc, leggi_json, macchine, non_parte, scrivi_atomico  # noqa: E402

# Il codice che gira da tutte e due le parti: qui con exec(), di là compresso dentro hc exec. Legge e
# scrive solo la cartella delle note; MODO e il pacco arrivano dal chiamante.
CODICE = r'''
import base64, json, os, re, sys, tempfile
ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")

def base():
    return os.path.join(os.environ.get("CLAUDE_CONFIG_DIR") or os.path.join(os.path.expanduser("~"), ".claude"),
                        "data", "note-finestra")

def leggi():
    b, out = base(), {}
    for nome in (sorted(os.listdir(b)) if os.path.isdir(b) else []):
        if not ID.match(nome):
            continue
        try:
            with open(os.path.join(b, nome, "nota.json"), encoding="utf-8", newline="") as f:
                testo = f.read()
        except OSError:
            continue
        p = os.path.join(b, nome, "finestra.png")
        out[nome] = {"json": testo, "png": os.path.getsize(p) if os.path.isfile(p) else None}
    return out

def png(ident):
    if not ID.match(ident):
        return None
    try:
        with open(os.path.join(base(), ident, "finestra.png"), "rb") as f:
            return base64.b64encode(f.read()).decode()
    except OSError:
        return None

def _sostituisci(file, dati, binario=False):
    fd, tmp = tempfile.mkstemp(prefix=".nota.", suffix=".tmp", dir=os.path.dirname(file))
    try:
        with os.fdopen(fd, "wb" if binario else "w", **({} if binario else {"encoding": "utf-8", "newline": "\n"})) as f:
            f.write(dati)
        os.replace(tmp, file)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise

def scrivi(pacco):
    scritte, saltate = [], []
    for v in pacco:
        ident = v.get("id") or ""
        if not ID.match(ident):
            saltate.append(ident)
            continue
        d = os.path.join(base(), ident)
        os.makedirs(d, exist_ok=True)
        p = os.path.join(d, "finestra.png")
        if v.get("png") and not os.path.isfile(p):
            _sostituisci(p, base64.b64decode(v["png"]), binario=True)
        f = os.path.join(d, "nota.json")
        try:
            with open(f, encoding="utf-8", newline="") as h:
                ora = h.read()
        except OSError:
            ora = None
        if ora != v.get("atteso"):
            saltate.append(ident)
            continue
        _sostituisci(f, v["json"])
        scritte.append(ident)
    return {"scritte": scritte, "saltate": saltate}

def esegui(modo, arg):
    if modo == "leggi":
        return {"note": leggi()}
    if modo == "png":
        return {"png": png(arg)}
    if modo == "scrivi":
        return scrivi(json.loads(sys.stdin.read() or "[]"))
    return {"errore": "modo sconosciuto: %s" % modo}
'''

ATTESA_GIRO = 50      # tutto il giro: sta sotto i 60 s che volta.js aspetta
ATTESA_CHIAMATA = 25  # una chiamata a un'altra macchina
RANGO = {"aperta": 0, "presa": 1, "risolta": 2, "scartata": 2}
CHIUSURA = ("stato", "chiusa_quando", "riassunto", "motivo")


def locale():
    """Il CODICE di qui, come modulo."""
    spazio = {}
    exec(CODICE, spazio)
    return spazio


def _canonico(d):
    return json.dumps(d, ensure_ascii=False, sort_keys=True)


def _dati(testo):
    """nota.json come dizionario; None se non si legge."""
    try:
        d = json.loads(testo)
    except (TypeError, ValueError):
        return None
    return d if isinstance(d, dict) else None


def unisci(a, b):
    """Una nota sola da due copie della stessa nota. Commutativa e idempotente: non guarda gli orologi delle
    macchine, solo il contenuto. La base è la copia col testo canonico più piccolo, completata dall'altra nei
    campi nulli; il filo è l'unione delle voci; lo stato è il più avanti (aperta, presa, chiusa), e fra due
    chiusure diverse vince quella con chiusa_quando più recente, col suo riassunto o motivo."""
    if a is None or b is None:
        return a if b is None else b
    base, altra = sorted((a, b), key=_canonico)
    out = dict(base)
    for k, v in altra.items():
        if out.get(k) is None and v is not None:
            out[k] = v
    fili = [v for d in (a, b) for v in (d.get("filo") if isinstance(d.get("filo"), list) else [])]
    if fili:
        viste, filo = set(), []
        for v in sorted(fili, key=lambda v: (str(v.get("quando") or ""), str(v.get("chi") or ""), str(v.get("testo") or ""))
                        if isinstance(v, dict) else ("", "", "")):
            chiave = _canonico(v)
            if chiave not in viste:
                viste.add(chiave)
                filo.append(v)
        out["filo"] = filo

    def peso(d):
        return (RANGO.get(d.get("stato"), 0), str(d.get("chiusa_quando") or ""), str(d.get("stato") or ""))
    vince = max((a, b), key=peso)
    if peso(a) != peso(b):
        for k in CHIUSURA:
            out[k] = vince.get(k)
    return out


def testo(d):
    return json.dumps(d, ensure_ascii=False, indent=2)


class Remota:
    """Le tre chiamate a un'altra macchina, con python3 e poi python (Windows: python3 può essere lo stub
    dello Store). Il primo Python che parte resta per il giro."""

    def __init__(self, nome, entro):
        self.nome, self.entro, self.py = nome, entro, None
        self.compresso = base64.b64encode(zlib.compress(CODICE.encode(), 9)).decode()

    def chiama(self, modo, arg="", stdin=None):
        ultimo = "nessun Python"
        for py in ([self.py] if self.py else ["python3", "python"]):
            t = int(min(ATTESA_CHIAMATA, self.entro - time.monotonic()))
            if t < 2:
                raise RuntimeError("non ha risposto in tempo")
            codice = ("import base64,zlib,json;exec(zlib.decompress(base64.b64decode('%s')));"
                      "print(json.dumps(esegui(%r,%r)))" % (self.compresso, modo, arg))
            argv = hc() + ["exec", "--on", self.nome, "--timeout", str(t)] + (["-i"] if stdin is not None else []) \
                + [py, "-c", codice]
            try:
                r = subprocess.run(argv, input=stdin if stdin is not None else "", capture_output=True, text=True,
                                   encoding="utf-8", errors="replace", timeout=t + 2,
                                   env=dict(os.environ, PYTHONIOENCODING="utf-8"))
            except subprocess.TimeoutExpired:
                raise RuntimeError("non ha risposto in %d s" % t) from None
            if r.returncode == 0:
                self.py = py
                d = leggi_json(r.stdout)
                if d.get("errore"):
                    raise RuntimeError(str(d["errore"])[:200])
                return d
            if non_parte(r.stdout, r.stderr):
                continue
            righe = (r.stderr or r.stdout).strip().splitlines()
            ultimo = errore_hc(righe[-1]) if righe else "rc %d" % r.returncode
            break
        raise RuntimeError(ultimo)


def giro(qui, remota):
    """Un giro con una macchina: {scaricate, spinte, unite, saltate}."""
    conto = {"scaricate": 0, "spinte": 0, "unite": 0, "saltate": 0}
    di_qua, di_la = qui["leggi"](), remota.chiama("leggi")["note"]
    pacco_qua, pacco_la = [], []
    for ident in sorted(set(di_qua) | set(di_la)):
        a, b = di_qua.get(ident), di_la.get(ident)
        if a is None:
            if _dati(b["json"]) is None:
                continue
            png = remota.chiama("png", ident)["png"] if b.get("png") else None
            pacco_qua.append({"id": ident, "atteso": None, "json": b["json"], "png": png})
            conto["scaricate"] += 1
            continue
        if b is None:
            if _dati(a["json"]) is None:
                continue
            pacco_la.append({"id": ident, "atteso": None, "json": a["json"], "png": qui["png"](ident) if a.get("png") else None})
            conto["spinte"] += 1
            continue
        da, db = _dati(a["json"]), _dati(b["json"])
        u = unisci(da, db)
        if u is None:
            continue
        png_la = qui["png"](ident) if a.get("png") and not b.get("png") else None
        png_qua = remota.chiama("png", ident)["png"] if b.get("png") and not a.get("png") else None
        if u != da or png_qua:
            pacco_qua.append({"id": ident, "atteso": a["json"], "json": testo(u) if u != da else a["json"], "png": png_qua})
        if u != db or png_la:
            pacco_la.append({"id": ident, "atteso": b["json"], "json": testo(u) if u != db else b["json"], "png": png_la})
        if u != da or u != db:
            conto["unite"] += 1
    if pacco_qua:
        conto["saltate"] += len(qui["scrivi"](pacco_qua)["saltate"])
    if pacco_la:
        conto["saltate"] += len(remota.chiama("scrivi", stdin=json.dumps(pacco_la))["saltate"])
    return conto


def sincronizza():
    entro = time.monotonic() + ATTESA_GIRO
    qui = locale()
    lista = macchine()
    if lista is None:
        return {"esito": "errore", "errore": "Herdr non risponde", "macchine": {}}
    esiti, errori = {}, 0
    for m in lista:
        if m.get("stato") not in (None, "connected"):
            esiti[m["nome"]] = {"esito": "salta", "perche": m.get("perche") or m.get("stato")}
            continue
        try:
            esiti[m["nome"]] = {"esito": "ok", **giro(qui, Remota(m["nome"], entro))}
        except (RuntimeError, ValueError, OSError, subprocess.SubprocessError) as e:
            errori += 1
            esiti[m["nome"]] = {"esito": "errore", "errore": str(e)[:200]}
    return {"esito": "errore" if errori else "ok", "quando": time.time(), "macchine": esiti}


def main(argv):
    if not argv or argv[0] != "sincronizza":
        print(__doc__)
        return 2
    percorso = argv[2] if len(argv) > 2 and argv[1] == "--scrivi" else None
    d = sincronizza()
    if percorso:
        scrivi_atomico(percorso, d)
    print(json.dumps(d, ensure_ascii=False))
    return 0 if d["esito"] == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
