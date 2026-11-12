"""Volta: sposta una sessione in background da una macchina a un'altra (Federico, 12/11/2026).

  python3 volta_sonda.py sposta DA A ID SESSIONID --cartella DIR [--progetto SLUG] [--titolo NOME]

Serve quando una macchina ha poca memoria: la conversazione continua su un'altra, con lo stesso
sessionId. Gira su questa macchina e parla con le due con herdr-core (hc exec --on), come la sonda.
Stampa {id, sessionId, attach, macchina, cartella} oppure {errore}.

I passi, in quest'ordine:
  1. legge su DA la cartella della sessione, la trascrizione e lo stato di git. Rifiuta se ci sono file
     non salvati o commit non spinti: sull'altra macchina il lavoro non ci sarebbe.
  2. prepara la cartella su A: lo stesso percorso relativo alla base dei progetti (arturo.json), col
     repository allo stesso commit. Un worktree che manca nasce da `git worktree add`, un repository che
     manca da `git clone`; una cartella che c'è viene avanti con `git pull --ff-only`.
  3. ferma la sessione su DA (claude stop) e copia la trascrizione nella cartella dei progetti di Claude
     su A: `<cartella codificata>/<SESSIONID>.jsonl` e la cartella `<SESSIONID>/` se c'è. Una copia che
     c'era già su A resta accanto, come `.prima-<ora>`.
  4. riprende la stessa conversazione su A (claude --bg --resume, senza fork). Se non riparte, la
     riprende su DA: la sessione non resta mai senza macchina.
Su DA la trascrizione resta com'è. Mai claude rm.
"""
from __future__ import annotations

import base64
import json
import os
import subprocess
import sys
import time

import volta_sonda as vs

# Codice comune a ogni script remoto: la base dei progetti di quella macchina, la cartella di Claude e la
# codifica delle cartelle dei progetti di Claude Code (ogni carattere non alfanumerico diventa "-",
# provato l'12/11/2026 su Mac e su Windows: "C:\\Users\\feder" diventa "C--Users-feder").
COMUNE = r'''
import base64, glob, json, os, re, shutil, subprocess, sys, tarfile, io, time
a = json.loads(base64.b64decode(sys.argv[1]).decode("utf-8"))
def esci(**d):
    print(json.dumps(d)); raise SystemExit
casa = os.path.expanduser("~")
app = os.environ.get("HERDR_APP_HOME") or os.path.join(casa, ".config", "herdr-app")
base = casa
try:
    with open(os.path.join(app, "arturo.json"), encoding="utf-8") as fh:
        base = json.load(fh).get("base") or casa
except (OSError, ValueError, AttributeError):
    pass
base = os.path.normpath(base)
radice = os.environ.get("CLAUDE_CONFIG_DIR") or os.path.join(casa, ".claude")
def codifica(p):
    return re.sub(r"[^A-Za-z0-9]", "-", p)
def g(cartella, *args, t=60):
    try:
        r = subprocess.run(["git", "-C", cartella] + list(args), capture_output=True, text=True,
                           encoding="utf-8", errors="replace", stdin=subprocess.DEVNULL, timeout=t)
    except (OSError, subprocess.SubprocessError) as e:
        return 1, str(e)
    return r.returncode, ((r.stdout or "") if r.returncode == 0 else (r.stderr or r.stdout or "")).strip()
def relativo(p):
    # sui due percorsi veri: git dice /private/var dove la base dice /var (macOS), e un link nella base
    # farebbe sembrare fuori una cartella che sta dentro
    try:
        r = os.path.relpath(os.path.realpath(p), os.path.realpath(base))
    except ValueError:
        return None
    return None if r == ".." or r.startswith(".." + os.sep) or os.path.isabs(r) else r.replace(os.sep, "/")
'''

# Su DA: cartella, trascrizione e git. {"rel", "trascrizione", "byte", "git": {...} | null}.
LEGGI = COMUNE + r'''
cartella = os.path.normpath(os.path.abspath(a["cartella"]))
sid = a["sid"]
trovate = glob.glob(os.path.join(radice, "projects", "*", sid + ".jsonl"))
qui = [t for t in trovate if os.path.basename(os.path.dirname(t)) == codifica(cartella)]
if not (qui or trovate):
    esci(errore="non trovo la conversazione %s fra quelle di Claude" % sid[:8])
tr = (qui or trovate)[0]
# claude --resume cerca la conversazione fra quelle della cartella da cui parte: conta la cartella dove
# sta la trascrizione, che può non essere quella che dice l'elenco (una sessione nata nella base e
# spostata in un worktree). Il campo cwd delle righe della trascrizione dice quale.
if not qui:
    cartella = None
    with open(tr, encoding="utf-8", errors="replace") as fh:
        for riga in fh:
            m = re.search(r'"cwd":\s*"((?:[^"\\]|\\.)*)"', riga)
            if m:
                c = json.loads('"%s"' % m.group(1))
                if codifica(c) == os.path.basename(os.path.dirname(tr)):
                    cartella = os.path.normpath(c)
                    break
    if not cartella:
        esci(errore="non so da che cartella riprendere la conversazione %s" % sid[:8])
    if not os.path.isdir(cartella):
        esci(errore="la cartella della conversazione non c'è più: %s" % cartella)
rel = relativo(cartella)
if rel is None:
    esci(errore="la cartella %s non sta nella base dei progetti (%s)" % (cartella, base))
git = None
if g(cartella, "rev-parse", "--is-inside-work-tree")[0] == 0:
    top = os.path.normpath(g(cartella, "rev-parse", "--show-toplevel")[1])
    comune = g(cartella, "rev-parse", "--path-format=absolute", "--git-common-dir")[1]
    principale = os.path.normpath(os.path.dirname(comune)) if comune.endswith(".git") else top
    if relativo(top) is None or relativo(principale) is None:
        esci(errore="il repository di %s non sta nella base dei progetti (%s)" % (cartella, base))
    ramo = g(cartella, "rev-parse", "--abbrev-ref", "HEAD")[1]
    rc, url = g(cartella, "remote", "get-url", "origin")
    rcl, lr = g(cartella, "ls-remote", "origin", "refs/heads/" + ramo) if rc == 0 and ramo != "HEAD" else (1, "")
    git = {"top": relativo(top), "principale": relativo(principale), "worktree": principale != top,
           "ramo": ramo, "testa": g(cartella, "rev-parse", "HEAD")[1], "url": url if rc == 0 else None,
           "remoto": lr.split()[0] if rcl == 0 and lr.split() else None,
           "sporchi": len([x for x in g(cartella, "status", "--porcelain")[1].splitlines() if x.strip()])}
esci(ok=True, rel=rel, trascrizione=tr, byte=os.path.getsize(tr), git=git)
'''

# Su A: la cartella pronta allo stesso commit, e la cartella dei progetti di Claude. {"cartella", "progetti"}.
PREPARA = COMUNE + r'''
gi = a.get("git")
cartella = os.path.normpath(os.path.join(base, a["rel"]))
nome = a.get("nome") or "questa macchina"
if gi:
    top = os.path.normpath(os.path.join(base, gi["top"]))
    ramo = gi["ramo"]
    if not os.path.isdir(top):
        if gi["worktree"]:
            principale = os.path.normpath(os.path.join(base, gi["principale"]))
            if not os.path.isdir(principale):
                esci(errore="su %s manca il repository %s: clonalo lì" % (nome, gi["principale"]))
            rc, out = g(principale, "fetch", "origin", ramo, t=120)
            if rc != 0:
                esci(errore="su %s git fetch non va: %s" % (nome, out.splitlines()[-1][:160] if out else rc))
            if g(principale, "rev-parse", "--verify", "--quiet", "refs/heads/" + ramo)[0] == 0:
                rc, out = g(principale, "worktree", "add", top, ramo, t=120)
            else:
                rc, out = g(principale, "worktree", "add", "--track", "-b", ramo, top, "origin/" + ramo, t=120)
        else:
            if not gi.get("url"):
                esci(errore="su %s manca %s, e il repository non ha un remoto da cui clonarlo" % (nome, gi["top"]))
            os.makedirs(os.path.dirname(top), exist_ok=True)
            try:
                r = subprocess.run(["git", "clone", "--branch", ramo, gi["url"], top], capture_output=True, text=True,
                                   encoding="utf-8", errors="replace", stdin=subprocess.DEVNULL, timeout=300)
                rc, out = r.returncode, (r.stderr or r.stdout or "").strip()
            except (OSError, subprocess.SubprocessError) as e:
                rc, out = 1, str(e)
        if rc != 0:
            esci(errore="su %s non preparo %s: %s" % (nome, gi["top"], out.splitlines()[-1][:160] if out else rc))
    else:
        sporchi = [x for x in g(top, "status", "--porcelain")[1].splitlines() if x.strip()]
        if sporchi:
            esci(errore="su %s la cartella %s ha %d file non salvati in git" % (nome, gi["top"], len(sporchi)))
        qui_ramo = g(top, "rev-parse", "--abbrev-ref", "HEAD")[1]
        if qui_ramo != ramo:
            esci(errore="su %s la cartella sta sul ramo %s, la sessione su %s" % (nome, qui_ramo, ramo))
        rc, out = g(top, "pull", "--ff-only", "origin", ramo, t=120)
        if rc != 0:
            esci(errore="su %s git pull non va: %s" % (nome, out.splitlines()[-1][:160] if out else rc))
    testa = g(top, "rev-parse", "HEAD")[1]
    if testa != gi["testa"]:
        esci(errore="su %s la cartella è al commit %s, la sessione al %s" % (nome, testa[:8], gi["testa"][:8]))
if not os.path.isdir(cartella):
    esci(errore="su %s manca la cartella %s" % (nome, a["rel"]))
progetti = os.path.join(radice, "projects", codifica(cartella))
os.makedirs(progetti, exist_ok=True)
esci(ok=True, cartella=cartella, progetti=progetti)
'''

# Su DA: la trascrizione e la sua cartella in un tar.gz, in base64 su una riga.
PACCO = COMUNE + r'''
tr = a["trascrizione"]
cartella = os.path.dirname(tr)
sid = a["sid"]
buf = io.BytesIO()
with tarfile.open(fileobj=buf, mode="w:gz") as t:
    t.add(tr, arcname=sid + ".jsonl")
    if os.path.isdir(os.path.join(cartella, sid)):
        t.add(os.path.join(cartella, sid), arcname=sid)
print(json.dumps({"ok": True, "byte": os.path.getsize(tr), "pacco": base64.b64encode(buf.getvalue()).decode()}))
'''

# Su A: il pacco da stdin, aperto nella cartella dei progetti. Solo i nomi della sessione, niente "..".
SCARICA = COMUNE + r'''
sid = a["sid"]
dest = a["progetti"]
dati = base64.b64decode(sys.stdin.read().strip())
ora = time.strftime("%Y%m%d-%H%M%S")
for nome in (sid + ".jsonl", sid):
    p = os.path.join(dest, nome)
    if os.path.exists(p):
        os.rename(p, p + ".prima-" + ora)
with tarfile.open(fileobj=io.BytesIO(dati), mode="r:gz") as t:
    for m in t.getmembers():
        n = m.name.replace("\\", "/")
        if ".." in n.split("/") or n.startswith("/") or not (n == sid + ".jsonl" or n == sid or n.startswith(sid + "/")):
            esci(errore="nome inatteso nel pacco: %s" % n[:80])
        if not (m.isfile() or m.isdir()):
            esci(errore="voce inattesa nel pacco: %s" % n[:80])
    t.extractall(dest)
tr = os.path.join(dest, sid + ".jsonl")
esci(ok=True, byte=os.path.getsize(tr) if os.path.exists(tr) else -1)
'''

# Su una macchina: il lavoro di claude agents che tiene la conversazione `sid`, e il percorso di claude.
# {"id", "pid", "claude"} oppure {"nessuno": true}. Con "vivo" aspetta fino a 30 s che abbia un processo.
TROVA = COMUNE + "\n" + vs.ELENCO.strip() + r'''
fine = ".exe" if os.name == "nt" else ""
cl = shutil.which("claude") or os.path.expanduser("~/.local/bin/claude" + fine)
visto = None
for giro in range(15 if a.get("vivo") else 1):
    try:
        r = subprocess.run([cl, "agents", "--json", "--all"], capture_output=True, text=True, encoding="utf-8",
                           errors="replace", stdin=subprocess.DEVNULL, timeout=15)
        for s in elenco(r.stdout) or []:
            if s.get("sessionId") == a["sid"] and s.get("id"):
                visto = s
                if s.get("pid") or not a.get("vivo"):
                    esci(ok=True, id=s["id"], pid=s.get("pid"), claude=cl)
    except (OSError, subprocess.SubprocessError):
        pass
    if a.get("vivo"):
        time.sleep(2)
if visto:
    esci(errore="la sessione %s non riparte" % visto["id"])
esci(ok=True, nessuno=True, claude=cl)
'''

ATTESA_PACCO = 300


def esegui(nome, codice, dati, entrata=None, timeout=vs.ATTESA_AZIONE):
    """Lancia `codice` su `nome` ("qui" = questa macchina) con `dati` in base64; `entrata` va su stdin.
    Su un'altra macchina prova python3, poi python, solo se il primo non è partito. Torna il JSON."""
    arg = base64.b64encode(json.dumps(dati).encode()).decode()
    if nome in (None, "", "qui"):
        tentativi = [[sys.executable, "-c", codice, arg]]
    else:
        avvio = "import base64;exec(base64.b64decode('%s'))" % base64.b64encode(codice.encode()).decode()
        tentativi = [vs.hc() + ["exec", "--on", nome, "--timeout", str(timeout - 5)] + (["-i"] if entrata is not None else [])
                     + [py, "-c", avvio, arg] for py in ("python3", "python")]
    ultimo = "nessun Python"
    for argv in tentativi:
        try:
            r = subprocess.run(argv, capture_output=True, text=True, encoding="utf-8", errors="replace",
                               input=entrata if entrata is not None else "", timeout=timeout,
                               env=dict(os.environ, PYTHONIOENCODING="utf-8"))
        except subprocess.TimeoutExpired:
            return {"errore": "%s non ha risposto in %d s" % (vs.nome_qui() if nome in (None, "", "qui") else nome, timeout)}
        except OSError as e:
            return {"errore": "%s non risponde: %s" % (nome, str(e)[:160])}
        if r.returncode != 0 and (r.returncode == 9009 or vs.non_parte(r.stdout, r.stderr)):
            continue
        try:
            return vs.leggi_json(r.stdout)
        except ValueError:
            testo = (r.stderr or r.stdout or "").strip()
            ultimo = testo.splitlines()[-1][:200] if testo else "rc %d" % r.returncode
            break
    return {"errore": ultimo}


def chi(nome):
    return "questa macchina" if nome in (None, "", "qui") else nome


def controlla_git(gi):
    """Il motivo per non spostare, o None: il lavoro deve essere su GitHub per arrivare sull'altra macchina."""
    if not gi:
        return None
    if gi["sporchi"]:
        return "%d file non salvati in git: chiedi alla sessione commit e push, poi riprova" % gi["sporchi"]
    if gi["ramo"] == "HEAD":
        return "la cartella non sta su un ramo (HEAD staccata)"
    if not gi.get("url"):
        return "il repository non ha un remoto su GitHub"
    if gi.get("remoto") != gi["testa"]:
        return "il ramo %s ha commit non spinti su GitHub: chiedi alla sessione il push, poi riprova" % gi["ramo"]
    return None


def riprendi_su(nome, sid, cartella, titolo):
    """La stessa conversazione in background su `nome`: {id, attach} oppure {errore}.

    Se la macchina ha già un lavoro di claude agents con questa conversazione (ci è già stata, o è la
    macchina di partenza), claude respawn lo riaccende: rilegge la trascrizione appena copiata e tiene il
    sessionId. claude --bg --resume, lì, farebbe una sessione nuova con un altro sessionId (provato il
    12/11/2026). Su una macchina dove la conversazione non è mai stata, claude --bg --resume."""
    prima = esegui(nome, TROVA, {"sid": sid})
    if prima.get("errore"):
        return {"errore": prima["errore"]}
    if not prima.get("nessuno"):
        r = vs.azione(nome, "respawn", prima["id"])
        if r.get("errore"):
            return {"errore": "claude respawn: %s" % r["errore"]}
    else:
        r = vs.nasci(nome, "", None, cartella, riprendi=sid, titolo=titolo, stessa=True)
        if r.get("errore") and not str(r["errore"]).startswith("è partita"):
            return {"errore": r["errore"]}
    viva = esegui(nome, TROVA, {"sid": sid, "vivo": True}, timeout=90)
    if viva.get("errore") or viva.get("nessuno"):
        return {"errore": viva.get("errore") or "claude agents non la elenca"}
    voce = {"questa": nome in (None, "", "qui"), "claude": viva["claude"]}
    if not voce["questa"]:
        m = next((x for x in (vs.macchine() or []) if x["nome"] == nome), None)
        voce["target"] = m["target"] if m else nome
    return {"id": viva["id"], "attach": vs.argv_attach(voce, viva["id"])}


def sposta(da, a, id_lavoro, sid, cartella, progetto=None, titolo=None):
    for x in (id_lavoro, sid):
        if not vs.ID.fullmatch(x or ""):
            return {"errore": "id di sessione non valido"}
    if (da or "qui") == (a or "qui"):
        return {"errore": "la sessione è già su %s" % chi(a)}
    if not cartella:
        return {"errore": "non so in che cartella gira la sessione"}
    letto = esegui(da, LEGGI, {"cartella": cartella, "sid": sid})
    if letto.get("errore"):
        return {"errore": letto["errore"]}
    motivo = controlla_git(letto.get("git"))
    if motivo:
        return {"errore": motivo}
    pronto = esegui(a, PREPARA, {"rel": letto["rel"], "git": letto.get("git"), "nome": chi(a)}, timeout=360)
    if pronto.get("errore"):
        return {"errore": pronto["errore"]}
    # Da qui la sessione si ferma: ogni errore la riprende su DA.
    vs.azione(da, "stop", id_lavoro)  # una sessione già ferma risponde con un errore: si va avanti
    def torna(perche):
        r = riprendi_su(da, sid, cartella, titolo)
        dove = "riaperta su %s" % chi(da) if not r.get("errore") else "e non si riapre su %s: %s" % (chi(da), r["errore"])
        return {"errore": "%s; la sessione è %s" % (perche, dove)}
    pacco = esegui(da, PACCO, {"trascrizione": letto["trascrizione"], "sid": sid}, timeout=ATTESA_PACCO)
    if pacco.get("errore") or not pacco.get("pacco"):
        return torna("non leggo la conversazione su %s: %s" % (chi(da), pacco.get("errore") or "pacco vuoto"))
    scarico = esegui(a, SCARICA, {"sid": sid, "progetti": pronto["progetti"]}, entrata=pacco["pacco"], timeout=ATTESA_PACCO)
    if scarico.get("errore") or scarico.get("byte") != pacco["byte"]:
        return torna("la conversazione non arriva intera su %s: %s" % (chi(a), scarico.get("errore") or "%s byte su %s" % (scarico.get("byte"), pacco["byte"])))
    nata = riprendi_su(a, sid, pronto["cartella"], titolo)
    if nata.get("errore"):
        return torna("non riparte su %s: %s" % (chi(a), nata["errore"]))
    if progetto:
        vs.cambia(a, "progetto", sid, progetto)
    return {"id": nata["id"], "sessionId": sid, "attach": nata["attach"], "macchina": a or "qui", "cartella": pronto["cartella"]}


def main(argv):
    opz = {}
    resto = []
    i = 0
    while i < len(argv):
        if argv[i] in ("--cartella", "--progetto", "--titolo") and i + 1 < len(argv):
            opz[argv[i][2:]] = argv[i + 1]
            i += 2
        else:
            resto.append(argv[i])
            i += 1
    if len(resto) != 4 or any(x.startswith("--") for x in resto):
        print("uso: volta_sonda.py sposta <da> <a> <id> <sessionId> --cartella <dir> [--progetto <slug>] [--titolo <nome>]")
        return 2
    esito = sposta(resto[0], resto[1], resto[2], resto[3], opz.get("cartella"), opz.get("progetto"), opz.get("titolo"))
    print(json.dumps(esito, ensure_ascii=True))
    return 0 if "errore" not in esito else 1
