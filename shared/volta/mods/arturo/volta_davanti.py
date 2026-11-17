"""Volta: la macchina davanti alla persona (17/11/2026, #5881, docs/browser-e-macchina.md di Arturo).

Una sessione in background, o agganciata da un'altra macchina, non sa dove sta la persona: un Mac acceso per
un lavoro non vuol dire che lei sia lì. Volta lo sa, perché vede tutte le macchine: questo script chiede a
ognuna da quanto nessuno tocca tastiera o mouse (HIDIdleTime sul Mac, GetLastInputInfo su Windows) e scrive
su ogni macchina lo stesso file, con l'ultimo tocco di ogni macchina e l'ora.

  python3 volta_davanti.py giro [--scrivi FILE]   un giro con ogni macchina collegata (lo lancia volta.js)
  python3 volta_davanti.py leggi [--json]         per la sessione: quale macchina ha davanti la persona

Il file sta in ~/.cache/volta-davanti/davanti.json, fuori da git, fuori dalla telemetria e fuori da
~/.cache/volta, che la finestra guarda. Tiene per ogni macchina (per host) il nome per le persone e l'ora
dell'ultimo tocco; l'unione fra due copie tiene il tocco più recente di ogni host, così due Volta aperte
insieme, o una che non raggiunge una macchina, non si cancellano a vicenda.

`leggi` dice "qui", "altra" o "ignota". Ignota vuol dire: nessun file, nessun tocco, o l'ultimo tocco è più
vecchio di 15 minuti. Allora vale il punto 3 del documento di Arturo: Claude chiede una volta alla persona.
Una macchina che non sa misurare l'inattività (Linux, una sessione Windows senza desktop) non entra mai.

I comandi sull'altra macchina passano da herdr-core (hc exec --on, -i per il pacco su stdin), come in
volta_note.py, da cui viene Remota. Niente nomi di macchine qui.
Per le prove: VOLTA_HC (il comando hc), VOLTA_DAVANTI (il file), VOLTA_INATTIVA (i secondi di inattività,
vuoto = non si misura), VOLTA_TOCCO (l'ora del tocco), VOLTA_HOST e VOLTA_NOME (chi è questa macchina), VOLTA_ADESSO (l'ora di leggi).
"""
import base64
import json
import os
import subprocess
import sys
import time
import zlib
# Niente .pyc nella cartella del mod: Herdr ricarica il mod a ogni file nuovo che vi compare (#5556).
sys.dont_write_bytecode = True
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from volta_sonda import hc, lancia, macchine, scrivi_atomico  # noqa: E402
import volta_note  # noqa: E402

# Il codice che gira su ogni macchina: qui con exec(), di là compresso dentro hc exec. Misura l'inattività di
# quella macchina, unisce il pacco che arriva col file di là e lo riscrive solo se cambia.
CODICE = r'''
import json, os, platform, re, subprocess, sys, tempfile, time

def file_davanti():
    return os.environ.get("VOLTA_DAVANTI") or os.path.join(os.path.expanduser("~"), ".cache", "volta-davanti", "davanti.json")

def host():
    return os.environ.get("VOLTA_HOST") or (platform.node() or "").split(".")[0].lower()

def nome():
    if os.environ.get("VOLTA_NOME"):
        return os.environ["VOLTA_NOME"]
    if sys.platform == "darwin":
        try:
            r = subprocess.run(["scutil", "--get", "ComputerName"], capture_output=True, text=True, timeout=5)
            if r.returncode == 0 and r.stdout.strip():
                return r.stdout.strip()
        except (OSError, subprocess.SubprocessError):
            pass
    return (platform.node() or "").split(".")[0] or host()

def inattiva():
    """I secondi da quando nessuno tocca tastiera o mouse di questa macchina; None se non si misura."""
    if os.environ.get("VOLTA_TOCCO"):
        return time.time() - float(os.environ["VOLTA_TOCCO"])
    finto = os.environ.get("VOLTA_INATTIVA")
    if finto is not None:
        return float(finto) if finto.strip() else None
    if sys.platform == "darwin":
        try:
            r = subprocess.run(["ioreg", "-c", "IOHIDSystem", "-r", "-d", "1", "-k", "HIDIdleTime"],
                               capture_output=True, text=True, timeout=5)
        except (OSError, subprocess.SubprocessError):
            return None
        m = re.search(r'"HIDIdleTime" = (\d+)', r.stdout or "")
        return int(m.group(1)) / 1e9 if m else None
    if os.name == "nt":
        try:
            import ctypes
            k = ctypes.windll.kernel32
            sessione = ctypes.c_uint(0)
            # la sessione 0 (ssh, servizi) non ha desktop: il suo "ultimo input" non è la persona
            if not k.ProcessIdToSessionId(k.GetCurrentProcessId(), ctypes.byref(sessione)) or sessione.value == 0:
                return None
            class Ultimo(ctypes.Structure):
                _fields_ = [("cbSize", ctypes.c_uint), ("dwTime", ctypes.c_uint)]
            u = Ultimo()
            u.cbSize = ctypes.sizeof(Ultimo)
            if not ctypes.windll.user32.GetLastInputInfo(ctypes.byref(u)):
                return None
            return ((k.GetTickCount() - u.dwTime) & 0xFFFFFFFF) / 1000.0
        except Exception:
            return None
    return None

def vuoto():
    return {"versione": 1, "macchine": {}, "davanti": None, "scritto": None}

def valido(d):
    return isinstance(d, dict) and isinstance(d.get("macchine"), dict)

def unisci(a, b):
    """Un documento da due: per ogni host il tocco più recente. Commutativa e idempotente."""
    out = vuoto()
    for d in (a, b):
        if not valido(d):
            continue
        for h, v in d["macchine"].items():
            if not isinstance(v, dict) or not isinstance(v.get("tocco"), (int, float)):
                continue
            ora = out["macchine"].get(h)
            if ora is None or (v["tocco"], str(v.get("nome") or "")) > (ora["tocco"], str(ora.get("nome") or "")):
                out["macchine"][h] = {"nome": str(v.get("nome") or h), "tocco": float(v["tocco"])}
    if out["macchine"]:
        h = max(out["macchine"], key=lambda x: (out["macchine"][x]["tocco"], x))
        out["davanti"] = dict(out["macchine"][h], host=h)
    return out

def leggi():
    try:
        with open(file_davanti(), encoding="utf-8") as f:
            d = json.load(f)
        return d if valido(d) else None
    except (OSError, ValueError):
        return None

def misura():
    s = inattiva()
    if s is None or s < 0:
        return None
    # al secondo: una macchina ferma dà lo stesso tocco a ogni giro, e il file non si riscrive
    return {"macchine": {host(): {"nome": nome(), "tocco": float(round(time.time() - s))}}}

def unisci_qui(pacco):
    """Il file di questa macchina unito al pacco e al tocco di adesso; lo riscrive solo se cambia."""
    prima = leggi()
    d = unisci(unisci(prima, pacco), misura())
    tolto = lambda x: {k: v for k, v in (x or {}).items() if k != "scritto"}
    if prima is None or tolto(prima) != tolto(d):
        d["scritto"] = time.time()
        f = file_davanti()
        os.makedirs(os.path.dirname(f), exist_ok=True)
        fd, tmp = tempfile.mkstemp(prefix=".davanti.", suffix=".tmp", dir=os.path.dirname(f))
        try:
            with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as h:
                json.dump(d, h, ensure_ascii=False, indent=2)
            os.replace(tmp, f)
        except BaseException:
            try:
                os.unlink(tmp)
            except OSError:
                pass
            raise
    else:
        d["scritto"] = prima.get("scritto")
    return d

def esegui(modo, arg):
    if modo == "unisci":
        return unisci_qui(json.loads(sys.stdin.read() or "null"))
    return {"errore": "modo sconosciuto: %s" % modo}
'''

FRESCO_S = 15 * 60    # oltre, il tocco non dice più dove sta la persona: Claude chiede (decisione del 17/11/2026)
ATTESA_GIRO = 40      # tutto il giro: sta sotto i 60 s che volta.js aspetta


def locale():
    """Il CODICE di qui, come modulo."""
    spazio = {}
    exec(CODICE, spazio)
    return spazio


class Remota(volta_note.Remota):
    """La chiamata di volta_note.py, col CODICE di questo script."""

    def __init__(self, nome, entro):
        self.nome, self.entro, self.py = nome, entro, None
        self.compresso = base64.b64encode(zlib.compress(CODICE.encode(), 9)).decode()


def giro():
    """Il tocco di ogni macchina, unito e scritto su tutte. Ogni macchina riceve quello che si sa fino a lei,
    e il giro dopo porta a tutte anche quelle chiamate dopo."""
    entro = time.monotonic() + ATTESA_GIRO
    qui = locale()
    doc = qui["unisci_qui"](None)
    lista = macchine()
    if lista is None:
        return {"esito": "errore", "errore": "Herdr non risponde", "davanti": doc.get("davanti"), "macchine": {}}
    esiti, errori = {}, 0
    for m in lista:
        if m.get("stato") not in (None, "connected"):
            esiti[m["nome"]] = {"esito": "salta", "perche": m.get("perche") or m.get("stato")}
            continue
        try:
            la = Remota(m["nome"], entro).chiama("unisci", stdin=json.dumps(doc))
            doc = qui["unisci_qui"](la)
            esiti[m["nome"]] = {"esito": "ok"}
        except (RuntimeError, ValueError, OSError, subprocess.SubprocessError) as e:
            errori += 1
            esiti[m["nome"]] = {"esito": "errore", "errore": str(e)[:200]}
    return {"esito": "errore" if errori else "ok", "quando": time.time(), "davanti": doc.get("davanti"),
            "macchine": esiti}


def nome_hc(host):
    """Il nome con cui questa macchina raggiunge `host` (hc exec --on <nome>), o None."""
    try:
        rc, out, _ = lancia(hc() + ["machine", "ls", "--json"], timeout=15)
        voci = json.loads(out).get("machines", []) if rc == 0 else []
    except (OSError, ValueError, AttributeError, subprocess.SubprocessError):
        return None
    for m in voci if isinstance(voci, list) else []:
        if isinstance(m, dict) and str(m.get("host") or "").split(".")[0].lower() == host:
            return m.get("name") or m.get("target")
    return None


def decidi(adesso=None):
    """{esito: qui|altra|ignota, macchina, host, minuti, hc, perche} per la sessione che sta per aprire."""
    qui = locale()
    adesso = time.time() if adesso is None else adesso
    d = qui["leggi"]()
    if d is None:
        return {"esito": "ignota", "perche": "nessun file: Volta non è aperta, o non ha ancora fatto un giro"}
    d = qui["unisci"](d, None)
    top = d.get("davanti")
    if not top:
        return {"esito": "ignota", "perche": "nessuna macchina sa dire da quanto è ferma"}
    eta = adesso - top["tocco"]
    out = {"macchina": top["nome"], "host": top["host"], "minuti": round(max(eta, 0) / 60, 1)}
    if eta > FRESCO_S:
        return dict(out, esito="ignota", perche="l'ultimo tocco è di %d minuti fa, oltre i %d" % (eta // 60, FRESCO_S // 60))
    if top["host"] == qui["host"]():
        return dict(out, esito="qui")
    return dict(out, esito="altra", hc=nome_hc(top["host"]))


def riga(r):
    """La riga per la sessione, in parole."""
    if r["esito"] == "ignota":
        return "macchina davanti: ignota (%s). Chiedi una volta alla persona e ricorda la risposta." % r["perche"]
    quando = "meno di un minuto fa" if r["minuti"] < 1 else "%d minuti fa" % r["minuti"]
    if r["esito"] == "qui":
        return "macchina davanti: questa (%s), ultimo tocco %s." % (r["macchina"], quando)
    via = ("raggiungila con: hc exec --on %s -- <comando>" % r["hc"]) if r.get("hc") else \
        "questa macchina non la conosce in Herdr: chiedi alla persona come raggiungerla"
    return "macchina davanti: un'altra, %s, ultimo tocco %s; %s." % (r["macchina"], quando, via)


def main(argv):
    if argv[:1] == ["giro"]:
        percorso = argv[2] if len(argv) > 2 and argv[1] == "--scrivi" else None
        d = giro()
        if percorso:
            scrivi_atomico(percorso, d)
        print(json.dumps(d, ensure_ascii=False))
        return 0 if d["esito"] == "ok" else 1
    if argv[:1] == ["leggi"]:
        adesso = float(os.environ["VOLTA_ADESSO"]) if os.environ.get("VOLTA_ADESSO") else None
        r = decidi(adesso)
        print(json.dumps(r, ensure_ascii=False) if "--json" in argv else riga(r))
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
