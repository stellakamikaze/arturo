"""Volta Celeste: l'elenco delle sessioni di Claude di questa macchina e delle macchine di Herdr.

Le macchine sono quelle che la persona ha aggiunto a Herdr (`hc machine ls --json`); i comandi su
un'altra macchina passano da herdr-core (`hc exec --on <macchina>`), che gira nella sua sessione
grafica e conosce già ssh, chiavi e Windows. Niente nomi di macchine scritti qui: Volta è un'app da
distribuire (#5172, 10/11/2026).

  python3 volta_sonda.py volta [--scrivi FILE]   l'elenco, nel formato di ~/.cache/volta/sessioni.json
  python3 volta_sonda.py nasci MACCHINA [--progetto SLUG] [-- PROMPT]
      una sessione nuova in background (claude --bg) su MACCHINA ("qui" per questa), nella base dei
      progetti di quella macchina. Stampa {id, sessionId, attach, macchina, progetto, cartella} oppure
      {errore}: lo stesso contratto di porta-volta, così Volta la aggancia come le altre (#5172 passo 4).

Una riga di "sessioni": { macchina, host, questa, sessionId, id, nome, progetto, stato, aspetta, tipo,
attach, cartella, ultimo, risposta, azione }. `host` è il nome della macchina in Herdr ("qui" per
questa). Una macchina senza Claude Code resta fuori; una che non risponde tiene le righe dell'ultima
lettura buona, segnate `vecchia`. Per le prove: VOLTA_HC (il comando hc), VOLTA_SONDA_LOCALE (un JSON
al posto della sonda di questa macchina).
"""
import base64
import json
import os
import platform
import shutil
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor

# Gira sulla macchina da leggere (anche con hc exec, passata in base64). Stampa un JSON:
# {"claude": percorso o null, "sessioni": [...]} con progetto e ultime parole letti dai file di Claude.
SONDA = r'''
import glob, json, os, shutil, subprocess
fine = ".exe" if os.name == "nt" else ""
cl = shutil.which("claude") or os.path.expanduser("~/.local/bin/claude" + fine)
if not os.path.exists(cl):
    print(json.dumps({"claude": None, "sessioni": []})); raise SystemExit
radice = os.environ.get("CLAUDE_CONFIG_DIR") or os.path.expanduser("~/.claude")
r = subprocess.run([cl, "agents", "--json"], capture_output=True, text=True, encoding="utf-8", errors="replace",
                   stdin=subprocess.DEVNULL, timeout=40)
try:
    sessioni = json.loads(r.stdout or "[]")
except ValueError:
    sessioni = []
def testo(c):
    if isinstance(c, str):
        return c
    return " ".join(b.get("text", "") for b in c if isinstance(b, dict) and b.get("type") == "text")
for s in sessioni:
    sid = s.get("sessionId") or "-"
    s["progetto"] = None
    try:  # il progetto lo scrive hooks/scheda-terminale.py di Arturo; senza Arturo resta vuoto
        with open(os.path.join(radice, "cache", "scheda", sid + ".json"), encoding="utf-8") as fh:
            p = json.load(fh).get("progetto")
        if isinstance(p, str) and p.strip():
            s["progetto"] = p.strip()[:60]
    except (OSError, ValueError, AttributeError):
        pass
    f = glob.glob(os.path.join(radice, "projects", "*", sid + ".jsonl"))
    if not f:
        continue
    with open(f[0], "rb") as fh:
        fh.seek(0, 2); fh.seek(max(0, fh.tell() - 3000000))
        righe = fh.read().decode("utf-8", "replace").splitlines()[1:]
    risposta, azione, ultimo = "", "", ""
    for l in righe:
        try:
            d = json.loads(l)
        except ValueError:
            continue
        ultimo = d.get("timestamp", ultimo)
        m = d.get("message") or {}
        if d.get("type") == "assistant":
            for b in m.get("content", []) or []:
                if not isinstance(b, dict):
                    continue
                if b.get("type") == "text" and b.get("text", "").strip():
                    risposta = b["text"].strip()[:400]
                elif b.get("type") == "tool_use":
                    i = b.get("input") or {}
                    azione = b.get("name", "") + ": " + str(i.get("description") or i.get("command") or i.get("file_path") or "")[:150]
    s.update(risposta=risposta, azione=azione, ultimo=ultimo)
# solo ASCII: la console di Windows stampa in cp1252 e una freccia nel testo rompeva la riga
print(json.dumps({"claude": cl, "sessioni": sessioni}))
'''

# Gira sulla macchina dove nasce la sessione (anche con hc exec). L'argomento è un JSON in base64
# ({"prompt", "progetto"}): passa intero anche fra le virgolette di Windows. La cartella è la base dei
# progetti di quella macchina (arturo.json di Volta), perché claude --bg vuole una cartella fidata.
# Stampa {"id", "sessionId", "claude", "cartella"} oppure {"errore"}; mai una seconda sessione.
NASCI = r'''
import base64, json, os, re, shutil, subprocess, sys, time
a = json.loads(base64.b64decode(sys.argv[1]).decode("utf-8"))
def esci(**d):
    print(json.dumps(d)); raise SystemExit
fine = ".exe" if os.name == "nt" else ""
cl = shutil.which("claude") or os.path.expanduser("~/.local/bin/claude" + fine)
if not os.path.exists(cl):
    esci(errore="Claude Code non c'è su questa macchina")
casa = os.path.expanduser("~")
base = casa
# la cartella di Herdr come la cerca installa-herdr.sh: HERDR_APP_HOME, altrimenti ~/.config/herdr-app
app = os.environ.get("HERDR_APP_HOME") or os.path.join(casa, ".config", "herdr-app")
try:
    with open(os.path.join(app, "arturo.json"), encoding="utf-8") as fh:
        base = json.load(fh).get("base") or casa
except (OSError, ValueError, AttributeError):
    pass
if not os.path.isdir(base):
    base = casa
argv = [cl, "--bg"] + ([a["prompt"]] if a.get("prompt") else [])
try:
    r = subprocess.run(argv, cwd=base, capture_output=True, text=True, encoding="utf-8", errors="replace",
                       stdin=subprocess.DEVNULL, timeout=90)
except subprocess.TimeoutExpired:
    esci(errore="claude --bg non ha risposto in 90 s: claude agents dice se è nata")
uscita = (r.stdout or "") + "\n" + (r.stderr or "")
m = re.search(r"claude attach ([0-9A-Za-z-]+)", uscita)
if not m:
    righe = [x.strip() for x in uscita.splitlines() if x.strip() and not x.startswith("Starting background service")]
    if r.returncode == 0:
        esci(errore="è partita, ma non ho letto il suo id: claude agents la elenca")
    esci(errore="non parte in background: " + (righe[0][:160] if righe else "rc %d" % r.returncode))
corto = m.group(1)
sid = corto
try:
    r = subprocess.run([cl, "agents", "--json"], capture_output=True, text=True, encoding="utf-8",
                       errors="replace", stdin=subprocess.DEVNULL, timeout=40)
    for s in json.loads(r.stdout or "[]"):
        if str(s.get("sessionId", "")).startswith(corto):
            sid = s["sessionId"]
except (OSError, ValueError, subprocess.SubprocessError):
    pass
if a.get("progetto") and sid != corto:
    # il progetto per Volta (spazio giusto su ogni macchina), come l'eredità di porta-volta
    d = os.path.join(os.environ.get("CLAUDE_CONFIG_DIR") or os.path.join(casa, ".claude"), "cache", "scheda")
    try:
        os.makedirs(d, exist_ok=True)
        f = os.path.join(d, sid + ".json")
        with open(f + ".tmp", "w", encoding="utf-8") as fh:
            json.dump({"stato": "nuova", "progetto": a["progetto"], "fonte": "volta", "quando": time.time()}, fh)
        os.replace(f + ".tmp", f)
    except OSError:
        pass
esci(id=corto, sessionId=sid, claude=cl, cartella=base)
'''

LAVORA = {"busy", "working", "running", "starting"}
ASPETTA = {"waiting", "blocked"}
SSH_WIN = r"C:\Windows\System32\OpenSSH\ssh.exe"


def stato(s):
    """Uno stato solo per le due forme di `claude agents`: `status` per le interattive, `state` per le altre."""
    v = s.get("status") or s.get("state") or ""
    if v in LAVORA:
        return "lavora"
    if v in ASPETTA:
        return "aspetta"
    if v in ("failed", "crashed"):
        return "errore"
    return "ferma"


def hc():
    """Il comando hc come argv. VOLTA_HC (prove) può essere un argv JSON: ["python3", "hc_finto.py"]."""
    finto = os.environ.get("VOLTA_HC")
    if finto:
        return json.loads(finto) if finto.startswith("[") else [finto]
    return [shutil.which("hc") or os.path.expanduser("~/.local/bin/hc")]


def lancia(argv, timeout=60):
    # stdin chiuso: senza, ssh.exe e hc su Windows restano appesi
    r = subprocess.run(argv, capture_output=True, text=True, encoding="utf-8", errors="replace",
                       stdin=subprocess.DEVNULL, timeout=timeout, env=dict(os.environ, PYTHONIOENCODING="utf-8"))
    return r.returncode, r.stdout, r.stderr


def nome_qui():
    """Il nome di questa macchina per le persone: il nome del computer sul Mac, l'host altrove."""
    if sys.platform == "darwin":
        try:
            rc, out, _ = lancia(["scutil", "--get", "ComputerName"], timeout=5)
            if rc == 0 and out.strip():
                return out.strip()
        except (OSError, subprocess.SubprocessError):
            pass
    return platform.node().split(".")[0] or "Questa macchina"


def macchine():
    """Le macchine di Herdr: [{nome, target, stato, perche}]. Senza hc o senza macchine: []."""
    try:
        rc, out, _ = lancia(hc() + ["machine", "ls", "--json"], timeout=15)
        voci = json.loads(out).get("machines", []) if rc == 0 else []
    except (OSError, ValueError, subprocess.SubprocessError, AttributeError):
        return []
    return [{"nome": m.get("name") or m.get("host"), "target": m.get("target") or m.get("host"),
             "stato": m.get("state"), "perche": m.get("why")} for m in voci if m.get("name") or m.get("host")]


def leggi_json(out):
    """L'ultima riga JSON di un'uscita: hc exec può mettere avvisi della shell prima."""
    for riga in reversed((out or "").strip().splitlines()):
        riga = riga.strip()
        if riga.startswith("{"):
            return json.loads(riga)
    raise ValueError("nessun JSON nell'uscita")


def sonda_locale():
    finto = os.environ.get("VOLTA_SONDA_LOCALE")
    if finto:
        return json.loads(finto)
    rc, out, err = lancia([sys.executable, "-c", SONDA], timeout=90)
    if rc != 0:
        raise RuntimeError((err or out).strip()[-200:] or "rc %d" % rc)
    return leggi_json(out)


def sonda_remota(nome):
    """La sonda su un'altra macchina via herdr-core: prima python3, poi python (Windows, dove python3
    può essere lo stub dello Store, che esce 9009)."""
    codice = "import base64;exec(base64.b64decode('%s'))" % base64.b64encode(SONDA.encode()).decode()
    ultimo, senza = "nessun Python", 0
    for py in ("python3", "python"):
        rc, out, err = lancia(hc() + ["exec", "--on", nome, py, "-c", codice], timeout=90)
        if rc == 0:
            try:
                return leggi_json(out)
            except ValueError:
                ultimo = "risposta senza JSON"
                continue
        if non_parte(out, err):
            senza += 1
            continue
        ultimo = (err or out).strip().splitlines()[-1][:200] if (err or out).strip() else "rc %d" % rc
    if senza < 2:
        raise RuntimeError(ultimo)
    # senza Python: l'elenco nudo di claude agents, senza progetto né ultime parole
    rc, out, err = lancia(hc() + ["exec", "--on", nome, "claude", "agents", "--json"], timeout=60)
    if rc != 0 and non_parte(out, err):
        return {"claude": None, "sessioni": []}  # né Python né Claude: non è una macchina di Volta
    if rc != 0:
        raise RuntimeError(((err or out).strip().splitlines() or ["rc %d" % rc])[-1][:200])
    testo = (out or "").strip()
    return {"claude": "claude", "sessioni": json.loads(testo[testo.find("["):] or "[]")}


def non_parte(out, err):
    """hc exec dice spawn_failed quando il programma non c'è sulla macchina."""
    return '"spawn_failed"' in (out or "") + (err or "")


def ssh_bin():
    return SSH_WIN if os.name == "nt" and os.path.exists(SSH_WIN) else "ssh"


def argv_attach(voce, corto):
    """L'argv che aggancia la sessione `corto` da questa macchina: claude attach qui, ssh -t altrove."""
    if voce["questa"]:
        return [voce["claude"], "attach", corto]
    return [ssh_bin(), "-t", voce["target"], voce["claude"], "attach", corto]


def raccogli(viste=None):
    """Le voci per macchina, interrogate in parallelo: questa per prima, poi quelle di Herdr.
    `viste`: gli host in cui Volta ha già visto Claude (dal documento di prima). Una macchina che non
    risponde e dove Claude non si è mai visto resta fuori: può essere un server senza Claude."""
    qui = {"macchina": nome_qui(), "host": "qui", "questa": True, "target": None}
    altre = [{"macchina": m["nome"], "host": m["nome"], "questa": False, "target": m["target"],
              "stato_hc": m["stato"], "perche": m["perche"]} for m in macchine()]

    def una(v):
        if not v["questa"] and v.get("stato_hc") not in (None, "connected"):
            v["irraggiungibile"] = (v.get("perche") or "Herdr non la raggiunge")[:200]
            return v
        try:
            d = sonda_locale() if v["questa"] else sonda_remota(v["host"])
        except Exception as e:  # spenta, in stop, rete giù: lo si dice e si va avanti
            v["irraggiungibile"] = str(e)[:200]
            return v
        v["claude"] = d.get("claude")
        v["sessioni"] = d.get("sessioni") or []
        return v

    voci = [qui] + altre
    with ThreadPoolExecutor(max_workers=max(1, len(voci))) as ex:
        voci = list(ex.map(una, voci))
    # una macchina che risponde ma non ha Claude Code (un server, un Raspberry) non è di Volta
    viste = set(viste or ())
    return [v for v in voci if v.get("claude") or ("irraggiungibile" in v and (v["questa"] or v["host"] in viste))]


def gia_viste(precedente):
    return {m.get("host") for m in (precedente or {}).get("macchine", [])}


def righe(voci):
    """Da raccogli() all'elenco piatto: una riga per sessione."""
    out = []
    for v in voci:
        for s in v.get("sessioni") or []:
            sid = s.get("sessionId") or ""
            if not sid:
                continue
            corto = sid[:8]
            fondo = s.get("kind") == "background"
            out.append({
                "macchina": v["macchina"], "host": v["host"], "questa": v["questa"],
                "sessionId": sid, "id": corto, "nome": s.get("name") or corto,
                "progetto": s.get("progetto"), "stato": stato(s), "aspetta": s.get("waitingFor"),
                "tipo": "background" if fondo else "interattiva",
                # un'interattiva va prima portata in background, poi si aggancia
                "attach": argv_attach(v, corto) if fondo else None,
                "cartella": s.get("cwd"), "ultimo": s.get("ultimo") or "",
                "risposta": (s.get("risposta") or "")[:200], "azione": s.get("azione") or "",
            })
    return out


def documento(voci, precedente=None, adesso=None):
    """Il documento di Volta. Una macchina che non risponde tiene le righe dell'ultima lettura buona."""
    adesso = adesso or time.strftime("%Y-%m-%dT%H:%M:%S")
    sessioni = righe(voci)
    elenco = []
    for v in voci:
        voce = {"macchina": v["macchina"], "host": v["host"], "questa": v["questa"]}
        if "irraggiungibile" in v:
            voce["irraggiungibile"] = v["irraggiungibile"]
            sessioni += [dict(r, vecchia=True) for r in (precedente or {}).get("sessioni", [])
                         if r.get("host") == v["host"]]
        elenco.append(voce)
    return {"letto": adesso, "macchine": elenco, "sessioni": sessioni}


def scrivi_atomico(percorso, dati):
    percorso = os.path.expanduser(percorso)
    os.makedirs(os.path.dirname(percorso) or ".", exist_ok=True)
    tmp = "%s.%d.tmp" % (percorso, os.getpid())
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(dati, fh, ensure_ascii=False)
    os.replace(tmp, percorso)


def nasci(nome, prompt="", progetto=None):
    """Una sessione nuova in background su `nome` ("qui" o vuoto = questa macchina).

    Su un'altra macchina prova python3, poi python; passa al secondo solo se il primo non è partito
    (spawn_failed, o 9009 dello stub dello Store su Windows): un Python partito può aver già fatto
    nascere la sessione, e ripetere ne farebbe due."""
    questa = nome in (None, "", "qui")
    arg = base64.b64encode(json.dumps({"prompt": prompt or "", "progetto": progetto}).encode()).decode()
    if questa:
        voce = {"questa": True, "target": None}
        tentativi = [[sys.executable, "-c", NASCI, arg]]
    else:
        m = next((x for x in macchine() if x["nome"] == nome), None)
        if m is None:
            return {"errore": "%s non è fra le macchine di Herdr" % nome}
        if m["stato"] not in (None, "connected"):
            return {"errore": "%s non risponde: %s" % (nome, (m["perche"] or "Herdr non la raggiunge")[:160])}
        voce = {"questa": False, "target": m["target"]}
        codice = "import base64;exec(base64.b64decode('%s'))" % base64.b64encode(NASCI.encode()).decode()
        tentativi = [hc() + ["exec", "--on", nome, "--timeout", "150", py, "-c", codice, arg] for py in ("python3", "python")]
    ultimo = "nessun Python"
    for argv in tentativi:
        try:
            rc, out, err = lancia(argv, timeout=180)
        except (OSError, subprocess.SubprocessError) as e:
            return {"errore": "%s non risponde: %s" % (nome or "questa macchina", str(e)[:160])}
        # hc dice spawn_failed (anche lui in JSON) se il programma non c'è: prima di leggere la risposta
        if rc != 0 and (non_parte(out, err) or rc == 9009):
            continue
        try:
            d = leggi_json(out)
        except ValueError:
            d = {}
        if d.get("errore"):
            return {"errore": d["errore"]}
        if not d.get("id") or not d.get("claude"):
            testo = (err or out).strip()
            ultimo = testo.splitlines()[-1][:200] if testo else "rc %d" % rc
            break
        voce["claude"] = d["claude"]
        return {"id": d["id"], "sessionId": d["sessionId"], "attach": argv_attach(voce, d["id"]),
                "macchina": "qui" if questa else nome, "progetto": progetto, "cartella": d.get("cartella")}
    return {"errore": "non parte su %s: %s" % (nome or "questa macchina", ultimo)}


def main_nasci(argv):
    resto = argv[argv.index("--") + 1:] if "--" in argv else []
    testa = argv[:argv.index("--")] if "--" in argv else argv
    if not testa:
        print(__doc__.strip())
        return 2
    progetto = testa[testa.index("--progetto") + 1] if "--progetto" in testa[:-1] else None
    esito = nasci(testa[0], " ".join(resto), progetto)
    print(json.dumps(esito, ensure_ascii=False))
    return 0 if "errore" not in esito else 1


def main(argv):
    if argv and argv[0] == "nasci":
        return main_nasci(argv[1:])
    if not argv or argv[0] != "volta":
        print(__doc__.strip())
        return 2
    percorso = argv[argv.index("--scrivi") + 1] if "--scrivi" in argv else None
    precedente = None
    if percorso:
        try:
            with open(os.path.expanduser(percorso), encoding="utf-8") as fh:
                precedente = json.load(fh)
        except (OSError, ValueError):
            pass
    dati = documento(raccogli(gia_viste(precedente)), precedente)
    if percorso:
        scrivi_atomico(percorso, dati)
        giu = [m["macchina"] for m in dati["macchine"] if "irraggiungibile" in m]
        print("volta: %d sessioni%s" % (len(dati["sessioni"]), (", non rispondono: " + ", ".join(giu)) if giu else ""))
    else:
        print(json.dumps(dati, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
