"""Volta Celeste: l'elenco delle sessioni di Claude di questa macchina e delle macchine di Herdr.

Le macchine sono quelle che la persona ha aggiunto a Herdr (`hc machine ls --json`); i comandi su
un'altra macchina passano da herdr-core (`hc exec --on <macchina>`), che gira nella sua sessione
grafica e conosce già ssh, chiavi e Windows. Niente nomi di macchine scritti qui: Volta è un'app da
distribuire (#5172, 10/11/2026).

  python3 volta_sonda.py volta [--scrivi FILE]   l'elenco, nel formato di ~/.cache/volta/sessioni.json
  python3 volta_sonda.py nasci MACCHINA [--progetto SLUG] [-- PROMPT]
      una sessione nuova in background (claude --bg) su MACCHINA ("qui" per questa), nella base dei
      progetti di quella macchina, dopo aver acceso il servizio di Claude. Stampa {id, sessionId, attach,
      macchina, progetto, cartella} oppure {errore}: lo stesso contratto di porta-volta, così Volta la
      aggancia come le altre (#5172 passo 4).
  python3 volta_sonda.py azione MACCHINA logs|stop|respawn|rm ID   (logs: le ultime righe dello schermo)
  python3 volta_sonda.py servizio MACCHINA
      accende il servizio di Claude (claude daemon run) su MACCHINA se manca, dove sopravvive: il
      LaunchAgent di servizi-gui.sh o l'attività di servizio-claude.ps1 se ci sono; altrimenti staccato,
      e su un Windows raggiunto con hc exec in un terminale di herdr-core (hc run). Un servizio che
      risponde non si tocca. Stampa {come} oppure {errore} (#5208).

Una riga di "sessioni": { macchina, host, questa, sessionId, id, nome, progetto, stato, aspetta, tipo,
attach, cartella, ultimo, risposta, azione }. `host` è il nome della macchina in Herdr ("qui" per
questa). Una macchina senza Claude Code resta fuori; una che non risponde tiene le righe dell'ultima
lettura buona, segnate `vecchia`. Per le prove: VOLTA_HC (il comando hc), VOLTA_SONDA_LOCALE (un JSON
al posto della sonda di questa macchina).
"""
import base64
import json
import re
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

# Gira sulla macchina dove nascerà la sessione, prima di NASCI (#5208). Il servizio di Claude che tiene
# le sessioni in background (claude daemon) parte da solo al primo claude --bg, ma a tempo: muore con
# chi l'ha fatto nascere (hc exec chiude tutto ciò che avvia) e, nato da ssh, non ha il login. Un
# claude daemon run invece resta acceso anche senza sessioni, e uno a tempo già acceso gli cede il
# posto riprendendo le sessioni vive (provato il 10/11/2026). Qui: se il servizio risponde non si tocca;
# se manca lo si accende fuori dalla portata di hc exec. Sul Mac col LaunchAgent di servizi-gui.sh se
# c'è, altrimenti staccato in una sessione nuova (sopravvive a hc exec). Su Windows con l'attività di
# servizio-claude.ps1 se c'è; da hc exec un figlio non si stacca dal job, quindi senza attività risponde
# {"serve": "hc-run"} e il terminale lo apre chi chiama. L'argomento è "remoto" o "qui".
# L'etichetta del LaunchAgent e il nome dell'attività stanno anche in servizi-gui.sh, servizio-claude.ps1
# e installa-herdr.sh: il banco HZ43 li tiene uguali.
# Stampa {"acceso": true, "come"} oppure {"serve"} oppure {"errore"}.
SERVIZIO = r'''
import json, os, re, shutil, subprocess, sys, time
def esci(**d):
    print(json.dumps(d)); raise SystemExit
fine = ".exe" if os.name == "nt" else ""
cl = shutil.which("claude") or os.path.expanduser("~/.local/bin/claude" + fine)
if not os.path.exists(cl):
    esci(errore="Claude Code non c'è su questa macchina")
casa = os.path.expanduser("~")
remoto = len(sys.argv) > 1 and sys.argv[1] == "remoto"
nulla = dict(stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
def acceso():
    try:
        r = subprocess.run([cl, "daemon", "status"], capture_output=True, text=True, encoding="utf-8",
                           errors="replace", stdin=subprocess.DEVNULL, timeout=30)
    except (OSError, subprocess.SubprocessError):
        return False
    return re.search(r"control\.sock:\s*reachable", (r.stdout or "") + (r.stderr or "")) is not None
if acceso():
    esci(acceso=True, come="già acceso")
if sys.platform == "darwin":
    etichetta = "org.stellakamikaze.arturo.claude-daemon"
    agente = os.path.join(casa, "Library", "LaunchAgents", etichetta + ".plist")
    if os.path.exists(agente):
        subprocess.run(["launchctl", "kickstart", "gui/%d/%s" % (os.getuid(), etichetta)], timeout=30, **nulla)
        come = "launchd"
    else:
        subprocess.Popen([cl, "daemon", "run"], cwd=casa, start_new_session=True, **nulla)
        come = "staccato"
elif os.name == "nt":
    attivita = "ArturoServizioClaude"
    q = subprocess.run(["schtasks", "/query", "/tn", attivita], timeout=30, **nulla)
    if q.returncode == 0:
        subprocess.run(["schtasks", "/run", "/tn", attivita], timeout=30, **nulla)
        come = "attività"
    elif remoto:
        esci(serve="hc-run")
    else:
        subprocess.Popen([cl, "daemon", "run"], cwd=casa, creationflags=0x00000008 | 0x00000200, **nulla)
        come = "staccato"
else:
    subprocess.Popen([cl, "daemon", "run"], cwd=casa, start_new_session=True, **nulla)
    come = "staccato"
for _ in range(40):
    time.sleep(0.5)
    if acceso():
        esci(acceso=True, come=come)
esci(errore="il servizio di Claude non si accende (%s)" % come)
'''

# Le attese di una nascita (#5214): ogni fase ha il suo tetto, e dati.js (nasciSu) aspetta la somma più
# un margine. Il servizio si ferma al suo tetto prima di far nascere la sessione, così una nascita già
# partita non si taglia a metà: tagliata, nascerebbe lo stesso mentre Volta dice "non risponde".
ATTESA_MACCHINE = 15
ATTESA_SERVIZIO = 120
ATTESA_NASCITA = 180
# Un gesto su una sessione (azione). Riavvia passa prima dal servizio: dati.js (azioneSessione) aspetta
# ATTESA_SERVIZIO più ATTESA_AZIONE più il margine, gli altri gesti ATTESA_AZIONE più il margine.
ATTESA_AZIONE = 60

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
        rc, out, _ = lancia(hc() + ["machine", "ls", "--json"], timeout=ATTESA_MACCHINE)
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


def servizio(nome):
    """Il servizio di Claude acceso su `nome` ("qui" o vuoto = questa macchina), con SERVIZIO (#5208).

    Su un'altra macchina gira con hc exec, python3 e poi python. Se la macchina risponde "hc-run"
    (Windows senza l'attività di servizio-claude.ps1), il servizio nasce in un terminale di herdr-core
    con hc run: vive nella sessione grafica e non muore con chi lo chiede. Mai da ssh.
    Tutto entro ATTESA_SERVIZIO secondi (#5214). Torna {"come"} oppure {"errore"}."""
    codice = "import base64;exec(base64.b64decode('%s'))" % base64.b64encode(SERVIZIO.encode()).decode()
    entro = time.monotonic() + ATTESA_SERVIZIO
    if nome in (None, "", "qui"):
        tentativi = [lambda t: [sys.executable, "-c", codice, "qui"]]
    else:
        tentativi = [lambda t, py=py: hc() + ["exec", "--on", nome, "--timeout", str(t), py, "-c", codice, "remoto"]
                     for py in ("python3", "python")]

    def chiedi():
        ultimo = "nessun Python"
        for argv in tentativi:
            t = min(90, int(entro - time.monotonic()))
            if t < 5:
                return {"errore": "nessuna risposta in %d s" % ATTESA_SERVIZIO}
            try:
                rc, out, err = lancia(argv(t), timeout=t + 5)
            except (OSError, subprocess.SubprocessError) as e:
                return {"errore": str(e)[:160]}
            if rc != 0 and (non_parte(out, err) or rc == 9009):
                continue
            try:
                return leggi_json(out)
            except ValueError:
                testo = (err or out).strip()
                ultimo = testo.splitlines()[-1][:200] if testo else "rc %d" % rc
        return {"errore": ultimo}

    d = chiedi()
    if d.get("serve") == "hc-run":
        try:
            rc, out, err = lancia(hc() + ["run", "--on", nome, "--name", "servizio-claude", "--no-parent", "--rm",
                                          "--bg", "claude", "daemon", "run"],
                                  timeout=max(5, min(60, int(entro - time.monotonic()))))
        except (OSError, subprocess.SubprocessError) as e:
            return {"errore": "hc run non risponde: %s" % str(e)[:160]}
        if rc != 0:
            testo = (err or out).strip()
            return {"errore": "hc run: " + (testo.splitlines()[-1][:160] if testo else "rc %d" % rc)}
        d = {}
        for _ in range(6):  # il terminale parte subito, il servizio dopo qualche secondo
            time.sleep(2)
            d = chiedi()
            if d.get("acceso"):
                return {"come": "terminale di Herdr"}
            if d.get("serve") != "hc-run":
                break
        return {"errore": d.get("errore") or "acceso con hc run, ma non risponde ancora"}
    if d.get("acceso"):
        return {"come": d.get("come")}
    return {"errore": d.get("errore") or "nessuna risposta"}


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
        tentativi = [hc() + ["exec", "--on", nome, "--timeout", str(ATTESA_NASCITA - 30), py, "-c", codice, arg]
                     for py in ("python3", "python")]
    # prima il servizio, acceso dove sopravvive: un claude --bg senza servizio lo farebbe nascere a
    # tempo dentro hc exec, e la sessione morirebbe con lui (#5208)
    s = servizio(nome)
    if s.get("errore"):
        return {"errore": "il servizio di Claude non parte su %s: %s" % (nome or "questa macchina", s["errore"])}
    ultimo = "nessun Python"
    for argv in tentativi:
        try:
            rc, out, err = lancia(argv, timeout=ATTESA_NASCITA)
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


SEQ = re.compile(r"\x1b\[([0-9;?]*)[ -/]*([@-~])|\x1b\][^\x07\x1b]*(?:\x07|\x1b\\)|\x1b[()][A-Za-z0-9]|\x1b[=>78DEM]")


def schermo(testo, quante=12):
    """Le ultime righe che un terminale mostrerebbe per l'uscita grezza di `claude logs`.

    claude disegna lo schermo spostando il cursore (G, C, B, H) invece di scrivere gli spazi:
    togliere le sequenze incollerebbe le parole. Qui si rifà il disegno su una griglia."""
    righe = {}
    r = c = alto = h = 0

    def riga(i):
        return righe.setdefault(i, [])

    def metti(ch):
        nonlocal c
        x = riga(r)
        if len(x) < c:
            x.extend(" " * (c - len(x)))
        if c < len(x):
            x[c] = ch
        else:
            x.append(ch)
        c += 1

    def giu(n):
        nonlocal r, alto
        r += n
        if h and r >= alto + h:
            alto = r - h + 1

    i = 0
    while i < len(testo):
        m = SEQ.match(testo, i)
        if m:
            i = m.end()
            fin = m.group(2)
            if not fin:
                continue
            p = [int(x) if x.isdigit() else 0 for x in m.group(1).replace("?", "").split(";")] if m.group(1) else []
            n = (p[0] if p and p[0] else 1)
            if fin == "G":
                c = n - 1
            elif fin == "C":
                c += n
            elif fin == "D":
                c = max(0, c - n)
            elif fin == "B":
                giu(n)
            elif fin == "A":
                r = max(alto, r - n)
            elif fin in "Hf":
                riga_ = p[0] if p and p[0] else 1
                col = p[1] if len(p) > 1 and p[1] else 1
                h = max(h, riga_)
                r, c = alto + riga_ - 1, col - 1
            elif fin == "d":
                h = max(h, n)
                r = alto + n - 1
            elif fin == "K":
                x = riga(r)
                modo = p[0] if p else 0
                if modo == 0:
                    del x[c:]
                elif modo == 1:
                    x[:c + 1] = [" "] * min(len(x), c + 1)
                else:
                    x.clear()
            elif fin == "J":
                modo = p[0] if p else 0
                if modo in (2, 3):
                    for k in [k for k in righe if k >= alto]:
                        del righe[k]
                elif modo == 0:
                    del riga(r)[c:]
                    for k in [k for k in righe if k > r]:
                        del righe[k]
            continue
        ch = testo[i]
        i += 1
        if ch == "\n":
            c = 0
            giu(1)
        elif ch == "\r":
            c = 0
        elif ch == "\b":
            c = max(0, c - 1)
        elif ch == "\t":
            c = (c // 8 + 1) * 8
        elif ch >= " ":
            metti(ch)
    fuori = ("Checking for updates",)
    viste = ["".join(righe[k]).rstrip() for k in sorted(righe)]
    viste = [v for v in viste if v.strip() and not v.strip().startswith(fuori)]
    return viste[-quante:]


VERBI = ("logs", "stop", "respawn", "rm")


def azione(nome, verbo, sid):
    """Un comando di claude su una sessione di `nome` ("qui" = questa macchina): logs (l'anteprima,
    come righe di schermo), stop, respawn, rm. Le altre macchine passano da herdr-core (hc exec --on).

    Riavvia (respawn) fa ripartire il processo della sessione, che nasce dal servizio di Claude: prima
    il servizio si accende dove sopravvive, come per nasci (#5215). Senza, claude respawn lo farebbe
    nascere a tempo dentro hc exec, e la sessione riavviata morirebbe con lui. Gli altri gesti non
    fanno nascere processi: non lo toccano."""
    if verbo not in VERBI:
        return {"errore": "azione sconosciuta: %s" % verbo}
    if not re.fullmatch(r"[0-9A-Za-z][0-9A-Za-z-]{3,63}", sid or ""):  # mai un'opzione come --all
        return {"errore": "id di sessione non valido"}
    if nome in (None, "", "qui"):
        argv = [shutil.which("claude") or "claude", verbo, sid]
    else:
        argv = hc() + ["exec", "--on", nome, "--timeout", str(ATTESA_AZIONE - 5), "claude", verbo, sid]
    if verbo == "respawn":
        s = servizio(nome)
        if s.get("errore"):
            return {"errore": "il servizio di Claude non parte su %s: %s" % (nome or "questa macchina", s["errore"])}
    try:
        rc, out, err = lancia(argv, timeout=ATTESA_AZIONE)
    except (OSError, subprocess.SubprocessError) as e:
        return {"errore": "%s non risponde: %s" % (nome or "questa macchina", str(e)[:160])}
    if rc != 0:
        testo = (err or out).strip()
        return {"errore": testo.splitlines()[-1][:200] if testo else "rc %d" % rc}
    if verbo == "logs":
        return {"righe": schermo(out)}
    testo = (out or err).strip()
    return {"ok": True, "testo": testo.splitlines()[-1][:200] if testo else ""}


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
    if argv and argv[0] == "servizio":
        if len(argv) != 2:
            print("uso: volta_sonda.py servizio <macchina>")
            return 2
        esito = servizio(argv[1])
        print(json.dumps(esito, ensure_ascii=False))
        return 0 if "errore" not in esito else 1
    if argv and argv[0] == "azione":
        if len(argv) != 4:
            print("uso: volta_sonda.py azione <macchina> <logs|stop|respawn|rm> <id>")
            return 2
        esito = azione(argv[1], argv[2], argv[3])
        print(json.dumps(esito, ensure_ascii=True))
        return 0 if "errore" not in esito else 1
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
