"""Volta: sposta una sessione in background da una macchina a un'altra (Federico, 12/11/2026).

  python3 volta_sonda.py sposta DA A ID SESSIONID --cartella DIR [--progetto SLUG] [--titolo NOME]

Serve quando una macchina ha poca memoria: la conversazione continua su un'altra, con lo stesso
sessionId. Gira su questa macchina e parla con le due con herdr-core (hc exec --on), come la sonda.
Stampa {id, sessionId, attach, macchina, cartella} oppure {errore}.

I passi, in quest'ordine:
  1. legge su DA la cartella della sessione, la trascrizione e lo stato di git. Rifiuta solo una HEAD
     staccata: file non salvati e commit non spinti viaggiano con la sessione (#5500, 13/11/2026).
  2. prepara la cartella su A: lo stesso percorso relativo alla base dei progetti (arturo.json), col
     repository allo stesso commit. I commit che non stanno in nessun ramo remoto arrivano in un bundle
     (`git bundle create - <ramo> --not --remotes`), preso in `refs/volta-sposta/<ramo>`. Un worktree che
     manca nasce da `git worktree add`, un repository che manca da `git clone`; una cartella che c'è viene
     avanti con `git merge --ff-only`.
  3. ferma la sessione su DA (claude stop). Solo adesso legge le modifiche non salvate, che la sessione
     ferma non cambia più: `git diff --binary HEAD` e i file nuovi (non ignorati) in un tar. Su A la diff
     entra con `git apply --index` (staged e non staged diventano tutte staged), i file nuovi con gli stessi
     controlli della trascrizione, e un'impronta dei contenuti deve tornare uguale. Se non torna, su A il
     lavoro va in `git stash` ("volta-sposta-<sessionId>") e la sessione riparte su DA.
  4. copia la trascrizione nella cartella dei progetti di Claude su A: `<cartella codificata>/<SESSIONID>.jsonl`
     e la cartella `<SESSIONID>/` se c'è. Una copia che c'era già su A resta accanto, come `.prima-<ora>`.
  5. riprende la stessa conversazione su A (claude --bg --resume, senza fork). Se non riparte, la
     riprende su DA: la sessione non resta mai senza macchina.
Su DA la trascrizione resta com'è. Mai claude rm.
Prima del passo 1 e prima del 3 guarda se la sessione sta facendo un turno: se sì rifiuta con
{errore, lavora: true}, e Volta riprova a turno finito. Lo spostamento non interrompe mai un turno.
"""
from __future__ import annotations

import base64
import json
import os
import subprocess
import sys
import time
# Niente .pyc nella cartella del mod: Herdr ricarica il mod a ogni file nuovo che vi compare, anche in
# __pycache__, e la ricarica ferma per sempre le attese di Volta (cx.sleep di Sposta, #5556, 13/11/2026).
# La variabile vale per i Python figli (lo spostamento staccato, il microfono).
sys.dont_write_bytecode = True
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"

import volta_sonda as vs

# Codice comune a ogni script remoto: la base dei progetti di quella macchina, la cartella di Claude e la
# codifica delle cartelle dei progetti di Claude Code (ogni carattere non alfanumerico diventa "-",
# provato l'12/11/2026 su Mac e su Windows: "C:\\Users\\feder" diventa "C--Users-feder").
COMUNE = r'''
import base64, glob, hashlib, json, os, re, shutil, subprocess, sys, tarfile, tempfile, io, time
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
def gb(cartella, *args, entrata=None, t=120):
    # git coi byte: diff binarie e nomi con -z
    try:
        r = subprocess.run(["git", "-C", cartella] + list(args), capture_output=True, input=entrata,
                           stdin=None if entrata is not None else subprocess.DEVNULL, timeout=t)
    except (OSError, subprocess.SubprocessError) as e:
        return 1, str(e).encode()
    return r.returncode, r.stdout if r.returncode == 0 else (r.stderr or r.stdout)
def ultima(out):
    out = out.decode("utf-8", "replace") if isinstance(out, bytes) else str(out)
    return out.strip().splitlines()[-1][:160] if out.strip() else "nessun messaggio"
def cambiati(top):
    # i file tracciati diversi da HEAD e i file nuovi non ignorati, coi percorsi relativi a top
    a1, d = gb(top, "diff", "--name-only", "-z", "HEAD")
    a2, n = gb(top, "ls-files", "-o", "--exclude-standard", "-z")
    if a1 or a2:
        return None, None
    dec = lambda b: [x.decode("utf-8", "surrogateescape") for x in b.split(b"\0") if x]
    return dec(d), dec(n)
def impronta(top):
    # contenuto di ogni file cambiato o nuovo, non il testo della diff: due macchine con git configurati in
    # modo diverso scrivono diff diverse per lo stesso lavoro
    d, n = cambiati(top)
    if d is None:
        return None
    h = hashlib.sha256(g(top, "rev-parse", "HEAD")[1].encode())
    for p in sorted(set(d) | set(n)):
        f = os.path.join(top, p)
        h.update(b"\0" + p.encode("utf-8", "surrogateescape") + b"\0")
        if os.path.islink(f):
            h.update(b"link:" + os.readlink(f).encode("utf-8", "surrogateescape"))
        elif os.path.isfile(f):
            with open(f, "rb") as fh:
                h.update(hashlib.sha256(fh.read()).digest())
        else:
            h.update(b"-")
    return h.hexdigest()
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
# Il lavoro git sta dove la sessione era all'ultimo messaggio: una sessione nata nella base ed entrata in un
# worktree (EnterWorktree, cd) tiene la trascrizione e la cartella di claude agents nella base, ma l'ultimo
# cwd della trascrizione è il worktree (provato il 13/11/2026, #5500).
ultima = None
with open(tr, encoding="utf-8", errors="replace") as fh:
    for riga in fh:
        for m in re.finditer(r'"cwd":\s*"((?:[^"\\]|\\.)*)"', riga):
            ultima = json.loads('"%s"' % m.group(1))
dove_git = None
for c in (os.path.normpath(os.path.abspath(a["cartella"])), cartella, ultima):
    if c and os.path.isdir(c) and relativo(c) is not None and g(c, "rev-parse", "--is-inside-work-tree")[0] == 0:
        dove_git = c
        break
git = None
if dove_git:
    top = os.path.normpath(g(dove_git, "rev-parse", "--show-toplevel")[1])
    comune = g(dove_git, "rev-parse", "--path-format=absolute", "--git-common-dir")[1]
    principale = os.path.normpath(os.path.dirname(comune)) if comune.endswith(".git") else top
    if relativo(top) is None or relativo(principale) is None:
        esci(errore="il repository di %s non sta nella base dei progetti (%s)" % (dove_git, base))
    ramo = g(dove_git, "rev-parse", "--abbrev-ref", "HEAD")[1]
    rc, url = g(dove_git, "remote", "get-url", "origin")
    rcl, lr = g(dove_git, "ls-remote", "origin", "refs/heads/" + ramo) if rc == 0 and ramo != "HEAD" else (1, "")
    git = {"top": relativo(top), "principale": relativo(principale), "worktree": principale != top,
           "ramo": ramo, "testa": g(dove_git, "rev-parse", "HEAD")[1], "url": url if rc == 0 else None,
           "remoto": lr.split()[0] if rcl == 0 and lr.split() else None,
           "sporchi": len([x for x in g(dove_git, "status", "--porcelain")[1].splitlines() if x.strip()])}
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
    pacco = base64.b64decode(sys.stdin.read().strip()) if a.get("bundle") else None
    def sorgente(repo):
        # da dove viene il commit della sessione: il bundle dei commit non spinti, il ramo su origin, o il
        # commit stesso se sta già in un altro ramo remoto (un ramo nuovo senza commit suoi)
        rc, out = g(repo, "fetch", "origin", t=180)
        if pacco is None:
            if gi.get("remoto"):
                if rc != 0:
                    esci(errore="su %s git fetch non va: %s" % (nome, ultima(out)))
                return "origin/" + ramo
            return gi["testa"]
        fd, f = tempfile.mkstemp(suffix=".bundle")
        with os.fdopen(fd, "wb") as fh:
            fh.write(pacco)
        try:
            rc, out = g(repo, "fetch", "--no-tags", f, "+refs/heads/%s:refs/volta-sposta/%s" % (ramo, ramo), t=300)
        finally:
            os.remove(f)
        if rc != 0:
            esci(errore="su %s i commit non spinti non entrano: %s" % (nome, ultima(out)))
        return "refs/volta-sposta/" + ramo
    if not os.path.isdir(top):
        if gi["worktree"]:
            principale = os.path.normpath(os.path.join(base, gi["principale"]))
            if not os.path.isdir(principale):
                esci(errore="su %s manca il repository %s: clonalo lì" % (nome, gi["principale"]))
            src = sorgente(principale)
            if g(principale, "rev-parse", "--verify", "--quiet", "refs/heads/" + ramo)[0] == 0:
                rc, out = g(principale, "worktree", "add", top, ramo, t=120)
                if rc == 0:
                    rc, out = g(top, "merge", "--ff-only", src, t=120)
            else:
                rc, out = g(principale, "worktree", "add", "-b", ramo, top, src, t=120)
                if rc == 0 and src.startswith("origin/"):
                    g(top, "branch", "--set-upstream-to", src)
        else:
            if not gi.get("url"):
                esci(errore="su %s manca %s, e il repository non ha un remoto da cui clonarlo" % (nome, gi["top"]))
            os.makedirs(os.path.dirname(top), exist_ok=True)
            sul_remoto = bool(gi.get("remoto")) and pacco is None
            try:
                r = subprocess.run(["git", "clone"] + (["--branch", ramo] if sul_remoto else []) + [gi["url"], top],
                                   capture_output=True, text=True, encoding="utf-8", errors="replace",
                                   stdin=subprocess.DEVNULL, timeout=300)
                rc, out = r.returncode, (r.stderr or r.stdout or "").strip()
            except (OSError, subprocess.SubprocessError) as e:
                rc, out = 1, str(e)
            if rc == 0 and not sul_remoto:
                rc, out = g(top, "checkout", "-q", "-B", ramo, sorgente(top), t=120)
        if rc != 0:
            esci(errore="su %s non preparo %s: %s" % (nome, gi["top"], ultima(out)))
    else:
        sporchi = [x for x in g(top, "status", "--porcelain")[1].splitlines() if x.strip()]
        if sporchi:
            esci(errore="su %s la cartella %s ha %d file non salvati in git" % (nome, gi["top"], len(sporchi)))
        qui_ramo = g(top, "rev-parse", "--abbrev-ref", "HEAD")[1]
        if qui_ramo != ramo:
            esci(errore="su %s la cartella sta sul ramo %s, la sessione su %s" % (nome, qui_ramo, ramo))
        rc, out = g(top, "merge", "--ff-only", sorgente(top), t=120)
        if rc != 0:
            esci(errore="su %s la cartella non viene avanti: %s" % (nome, ultima(out)))
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

# Su DA, prima dello stop: i commit del ramo che non stanno in nessun ramo remoto, in un bundle in base64.
# {"bundle"} oppure {"vuoto": true} se ogni commit sta già in un remoto (un ramo nuovo senza commit suoi).
COMMIT = COMUNE + r'''
top = os.path.normpath(os.path.join(base, a["top"]))
ramo = a["ramo"]
rc, n = g(top, "rev-list", "--count", ramo, "--not", "--remotes")
if rc != 0:
    esci(errore="non conto i commit non spinti: %s" % ultima(n))
if int(n or 0) == 0:
    esci(ok=True, vuoto=True)
fd, f = tempfile.mkstemp(suffix=".bundle")
os.close(fd)
try:
    rc, out = g(top, "bundle", "create", f, ramo, "--not", "--remotes", t=300)
    if rc != 0:
        esci(errore="non preparo il bundle dei commit non spinti: %s" % ultima(out))
    with open(f, "rb") as fh:
        dati = fh.read()
finally:
    os.remove(f)
print(json.dumps({"ok": True, "commit": int(n), "bundle": base64.b64encode(dati).decode()}))
'''

LIMITE_MODIFICHE = 100 * 1024 * 1024

# Su DA, a sessione ferma: la diff da HEAD, i file nuovi in un tar.gz e l'impronta dei contenuti.
# {"vuoto": true} senza modifiche; un commit fatto dopo LEGGI ferma tutto (la cartella su A è a un altro commit).
MODIFICHE = COMUNE + r'''
top = os.path.normpath(os.path.join(base, a["top"]))
testa = g(top, "rev-parse", "HEAD")[1]
if testa != a["testa"]:
    esci(errore="la sessione ha fatto un commit mentre la spostavo (%s, prima %s)" % (testa[:8], a["testa"][:8]))
d, n = cambiati(top)
if d is None:
    esci(errore="git non dice quali file sono cambiati")
if not d and not n:
    esci(ok=True, vuoto=True)
rc, diff = gb(top, "diff", "--binary", "HEAD", t=300)
if rc != 0:
    esci(errore="git diff non va: %s" % ultima(diff))
buf = io.BytesIO()
with tarfile.open(fileobj=buf, mode="w:gz") as t:
    for p in n:
        t.add(os.path.join(top, p), arcname=p, recursive=False)
if len(diff) + buf.tell() > a["limite"]:
    esci(errore="le modifiche non salvate pesano %d MB: troppo per portarle" % ((len(diff) + buf.tell()) // 1048576))
print(json.dumps({"ok": True, "file": len(d) + len(n), "impronta": impronta(top),
                  "diff": base64.b64encode(diff).decode(), "nuovi": base64.b64encode(buf.getvalue()).decode()}))
'''

# Su A: diff e file nuovi da stdin, sopra la cartella pulita allo stesso commit. Se l'impronta non torna, il
# lavoro arrivato va in uno stash: la cartella resta pulita per il prossimo tentativo, e niente si perde.
APPLICA = COMUNE + r'''
top = os.path.normpath(os.path.join(base, a["top"]))
if g(top, "rev-parse", "HEAD")[1] != a["testa"]:
    esci(errore="la cartella su questa macchina non è al commit della sessione")
dati = json.loads(sys.stdin.read())
def indietro(perche):
    rc, out = g(top, "stash", "push", "-u", "-m", "volta-sposta-" + a["sid"])
    messo = rc == 0 and "No local changes" not in out
    esci(errore=perche + ("; il lavoro arrivato è nello stash volta-sposta-%s" % a["sid"][:8] if messo else ""))
diff = base64.b64decode(dati.get("diff") or "")
if diff:
    rc, out = gb(top, "apply", "--index", "--binary", "--whitespace=nowarn", entrata=diff, t=300)
    if rc != 0:
        indietro("la diff non entra: %s" % ultima(out))
with tarfile.open(fileobj=io.BytesIO(base64.b64decode(dati.get("nuovi") or "")), mode="r:gz") as t:
    voci = t.getmembers()
    for m in voci:
        nm = m.name.replace("\\", "/")
        parti = nm.split("/")
        if ".." in parti or nm.startswith("/") or re.match(r"^[A-Za-z]:", nm) or ".git" in parti:
            indietro("nome inatteso fra i file nuovi: %s" % nm[:80])
        if not (m.isfile() or m.isdir() or m.issym()):
            indietro("voce inattesa fra i file nuovi: %s" % nm[:80])
        if m.issym() and (os.path.isabs(m.linkname) or ".." in m.linkname.replace("\\", "/").split("/")):
            indietro("collegamento che esce dalla cartella: %s" % nm[:80])
        if os.path.lexists(os.path.join(top, nm)):
            indietro("un file nuovo c'è già qui: %s" % nm[:80])
    t.extractall(top, members=voci)
if impronta(top) != a["impronta"]:
    indietro("le modifiche arrivate non sono uguali a quelle di partenza")
esci(ok=True)
'''

# Su una macchina: il lavoro di claude agents che tiene la conversazione `sid`, e il percorso di claude.
# {"id", "pid", "claude"} oppure {"nessuno": true}. Con "vivo" aspetta fino a 30 s che abbia un processo.
TROVA = COMUNE + "\n" + vs.ELENCO.strip() + "\n" + vs.CERCA_CLAUDE.strip() + r'''
cl = trova_claude()
visto = None
for giro in range(15 if a.get("vivo") else 1):
    try:
        r = subprocess.run([cl, "agents", "--json", "--all"], capture_output=True, text=True, encoding="utf-8",
                           errors="replace", stdin=subprocess.DEVNULL, timeout=15)
        for s in elenco(r.stdout) or []:
            if s.get("sessionId") == a["sid"] and s.get("id"):
                visto = s
                if s.get("pid") or not a.get("vivo"):
                    esci(ok=True, id=s["id"], pid=s.get("pid"), claude=cl, stato=s.get("status") or s.get("state") or "")
    except (OSError, subprocess.SubprocessError):
        pass
    if a.get("vivo"):
        time.sleep(2)
if visto:
    esci(errore="la sessione %s non riparte" % visto["id"])
esci(ok=True, nessuno=True, claude=cl)
'''

# Su A: il progetto della sessione spostata nella sua scheda (cache/scheda/<sid>.json, la legge la sonda).
# Il registro per lavoro della macchina di partenza non viaggia: il lavoro qui ha un altro id (12/11/2026,
# Federico: "questa sessione è categorizzata senza progetto anche se dovrebbe essere su Volta").
SEGNA = COMUNE + r'''
f = os.path.join(radice, "cache", "scheda", a["sid"] + ".json")
try:
    with open(f, encoding="utf-8") as fh:
        d = json.load(fh)
except (OSError, ValueError):
    d = {}
d = d if isinstance(d, dict) else {}
if a.get("spostata"):
    # la macchina di partenza: la conversazione ora vive altrove, la sonda la conta chiusa (#5537)
    d["spostata"] = {"su": a["spostata"], "quando": time.time()}
else:
    d.pop("spostata", None)
    if a.get("progetto"):
        d.update(progetto=a["progetto"], fonte="teletrasporto", quando=time.time())
os.makedirs(os.path.dirname(f), exist_ok=True)
with open(f + ".tmp", "w", encoding="utf-8") as fh:
    json.dump(d, fh)
os.replace(f + ".tmp", f)
esci(ok=True)
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


def controlla_git(gi):
    """Il motivo per non spostare, o None. File non salvati e commit non spinti viaggiano con la sessione
    (MODIFICHE e COMMIT); una HEAD staccata no, perché sull'altra macchina non c'è un ramo da preparare."""
    if not gi:
        return None
    if gi["ramo"] == "HEAD":
        return "la cartella non sta su un ramo (HEAD staccata)"
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


def lavora(da, sid):
    """Il rifiuto se la sessione `sid` su `da` sta facendo un turno, o None. Volta la sposta a turno finito
    (coda di volta.js): fermarla adesso interromperebbe il lavoro a metà. `lavora` dice a Volta di riprovare."""
    ora = esegui(da, TROVA, {"sid": sid})
    if not ora.get("errore") and vs.stato({"status": ora.get("stato")}) == "lavora":
        return {"errore": "sta lavorando: la sposto a turno finito", "lavora": True}
    return None


def sposta(da, a, id_lavoro, sid, cartella, progetto=None, titolo=None):
    for x in (id_lavoro, sid):
        if not vs.ID.fullmatch(x or ""):
            return {"errore": "id di sessione non valido"}
    if (da or "qui") == (a or "qui"):
        return {"errore": "la sessione è già su %s" % vs.chi(a)}
    if not cartella:
        return {"errore": "non so in che cartella gira la sessione"}
    occupata = lavora(da, sid)
    if occupata:
        return occupata
    letto = esegui(da, LEGGI, {"cartella": cartella, "sid": sid})
    if letto.get("errore"):
        return {"errore": letto["errore"]}
    gi = letto.get("git")
    motivo = controlla_git(gi)
    if motivo:
        return {"errore": motivo}
    bundle = None
    if gi and gi.get("remoto") != gi["testa"]:
        commit = esegui(da, COMMIT, {"top": gi["top"], "ramo": gi["ramo"]}, timeout=ATTESA_PACCO)
        if commit.get("errore"):
            return {"errore": commit["errore"]}
        bundle = commit.get("bundle")
    pronto = esegui(a, PREPARA, {"rel": letto["rel"], "git": gi, "nome": vs.chi(a), "bundle": bool(bundle)},
                    entrata=bundle, timeout=360)
    if pronto.get("errore"):
        return {"errore": pronto["errore"]}
    # Preparare la cartella dura anche minuti: nel frattempo la persona può averle scritto. Un turno
    # partito adesso non si interrompe (la cartella pronta su A resta per il prossimo tentativo).
    occupata = lavora(da, sid)
    if occupata:
        return occupata
    # Da qui la sessione si ferma: ogni errore la riprende su DA.
    fermata = vs.azione(da, "stop", id_lavoro)
    if fermata.get("errore"):
        # Una sessione già ferma risponde con un errore, e si va avanti. Se ha ancora un processo, lo stop
        # non l'ha fermata: portarla avanti la lascerebbe viva su due macchine (#5574, 14/11/2026).
        ora = esegui(da, TROVA, {"sid": sid})
        if ora.get("errore") or ora.get("pid"):
            return {"errore": "claude stop non ferma la sessione su %s: %s; resta lì" % (vs.chi(da), fermata["errore"])}
    def torna(perche):
        r = riprendi_su(da, sid, cartella, titolo)
        dove = "riaperta su %s" % vs.chi(da) if not r.get("errore") else "e non si riapre su %s: %s" % (vs.chi(da), r["errore"])
        return {"errore": "%s; la sessione è %s" % (perche, dove)}
    if gi:
        # a sessione ferma il lavoro non cambia più: adesso si legge quello non salvato
        mod = esegui(da, MODIFICHE, {"top": gi["top"], "testa": gi["testa"], "limite": LIMITE_MODIFICHE}, timeout=ATTESA_PACCO)
        if mod.get("errore"):
            return torna("non leggo le modifiche non salvate su %s: %s" % (vs.chi(da), mod["errore"]))
        if not mod.get("vuoto"):
            messe = esegui(a, APPLICA, {"top": gi["top"], "testa": gi["testa"], "impronta": mod["impronta"], "sid": sid},
                           entrata=json.dumps({"diff": mod["diff"], "nuovi": mod["nuovi"]}), timeout=ATTESA_PACCO)
            if messe.get("errore"):
                return torna("le modifiche non salvate non arrivano su %s: %s" % (vs.chi(a), messe["errore"]))
    pacco = esegui(da, PACCO, {"trascrizione": letto["trascrizione"], "sid": sid}, timeout=ATTESA_PACCO)
    if pacco.get("errore") or not pacco.get("pacco"):
        return torna("non leggo la conversazione su %s: %s" % (vs.chi(da), pacco.get("errore") or "pacco vuoto"))
    scarico = esegui(a, SCARICA, {"sid": sid, "progetti": pronto["progetti"]}, entrata=pacco["pacco"], timeout=ATTESA_PACCO)
    if scarico.get("errore") or scarico.get("byte") != pacco["byte"]:
        return torna("la conversazione non arriva intera su %s: %s" % (vs.chi(a), scarico.get("errore") or "%s byte su %s" % (scarico.get("byte"), pacco["byte"])))
    nata = riprendi_su(a, sid, pronto["cartella"], titolo)
    if nata.get("errore"):
        return torna("non riparte su %s: %s" % (vs.chi(a), nata["errore"]))
    # Su A col progetto di prima: fonte "teletrasporto", forte per la sonda (FORTI) e senza il segno di
    # /inizio che Cambia progetto lascia e che farebbe scrivere /inizio nella sessione appena spostata; e
    # via il segno di una partenza vecchia, se la conversazione torna dove era già stata.
    avvisi = []
    perche = segna(a, {"sid": sid, "progetto": progetto})
    if perche:
        avvisi.append("su %s la sessione non ha il segno del progetto (%s)" % (vs.chi(a), perche))
    # Su DA la copia ferma resta "done" anche dopo claude stop, e la sonda la darebbe addormentata: il
    # clic la riprenderebbe lì, con due copie vive della stessa conversazione (#5537, 13/11/2026).
    perche = segna(da, {"sid": sid, "spostata": a or "qui"})
    if perche:
        avvisi.append("su %s la copia ferma non è segnata come spostata (%s): non riaprirla da lì" % (vs.chi(da), perche))
    fatto = {"id": nata["id"], "sessionId": sid, "attach": nata["attach"], "macchina": a or "qui", "cartella": pronto["cartella"]}
    # La sessione vive già su A: un errore farebbe riaprire a Volta la scheda di partenza, e la
    # conversazione tornerebbe viva su due macchine. Il segno mancato arriva come avviso (#5635).
    return dict(fatto, avviso="; ".join(avvisi)) if avvisi else fatto


def segna(nome, dati):
    """SEGNA su `nome`, con un secondo tentativo (#5635): None se il segno è scritto, altrimenti il motivo."""
    r = {}
    for _ in range(2):
        r = esegui(nome, SEGNA, dati)
        if r.get("ok"):
            return None
    return r.get("errore") or "nessuna risposta"


def scrivi_esito(f, d):
    """L'esito di uno spostamento staccato, scritto con una rinomina: chi legge vede il file intero o niente."""
    os.makedirs(os.path.dirname(f) or ".", exist_ok=True)
    tmp = "%s.%d.tmp" % (f, os.getpid())
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(d, fh, ensure_ascii=True)
    os.replace(tmp, f)


def stacca(argv):
    """Rilancia questo spostamento staccato da chi l'ha chiesto (13/11/2026): Volta aspettava la risposta
    di exec, che Herdr ferma a 10 minuti mentre uno spostamento ne può chiedere di più; lo script restava
    a girare da solo, Volta non apriva la scheda nuova e la coda partiva con lo spostamento dopo. Il figlio
    ha VOLTA_SPOSTA_FIGLIO e scrive l'esito nel file di --esito; qui si risponde subito {"avviato"}."""
    nulla = dict(stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    env = dict(os.environ, VOLTA_SPOSTA_FIGLIO="1")
    cmd = [sys.executable, os.path.join(os.path.dirname(os.path.abspath(__file__)), "volta_sonda.py"), "sposta"] + argv
    if os.name == "nt":
        # fuori dal job di chi chiama, se il job lo permette; altrimenti staccato e basta
        for flag in (0x01000000 | 0x00000008 | 0x00000200, 0x00000008 | 0x00000200):
            try:
                subprocess.Popen(cmd, env=env, creationflags=flag, **nulla)
                return True
            except OSError:
                continue
        return False
    subprocess.Popen(cmd, env=env, start_new_session=True, **nulla)
    return True


def main(argv):
    opz = {}
    resto = []
    i = 0
    while i < len(argv):
        if argv[i] in ("--cartella", "--progetto", "--titolo", "--esito") and i + 1 < len(argv):
            opz[argv[i][2:]] = argv[i + 1]
            i += 2
        elif argv[i] == "--controlla":
            opz["controlla"] = True
            i += 1
        else:
            resto.append(argv[i])
            i += 1
    if len(resto) != 4 or any(x.startswith("--") for x in resto):
        print("uso: volta_sonda.py sposta <da> <a> <id> <sessionId> --cartella <dir> [--progetto <slug>] [--titolo <nome>] [--esito <file>] [--controlla]")
        return 2
    if opz.get("controlla"):
        # Solo il controllo del turno, prima che Volta chiuda le schede (#5635): {"lavora"} o {"ok"}.
        if not vs.ID.fullmatch(resto[3] or ""):
            print(json.dumps({"errore": "id di sessione non valido"}))
            return 1
        print(json.dumps(lavora(resto[0], resto[3]) or {"ok": True}, ensure_ascii=True))
        return 0
    f = opz.get("esito")
    if f and not os.environ.get("VOLTA_SPOSTA_FIGLIO"):
        scrivi_esito(f, {"finito": False, "da": time.time()})
        if not stacca(argv):
            scrivi_esito(f, {"finito": True, "errore": "non riesco a far partire lo spostamento staccato"})
            print(json.dumps({"errore": "non riesco a far partire lo spostamento staccato"}))
            return 1
        print(json.dumps({"avviato": True, "esito": f}))
        return 0
    try:
        finto = os.environ.get("VOLTA_SPOSTA_FINTO")  # solo per le prove: {"dorme": s, "esito": {...}} o {"rompi": true}
        if finto:
            f_ = json.loads(finto)
            time.sleep(float(f_.get("dorme") or 0))
            if f_.get("rompi"):
                raise RuntimeError("rotto per prova")
            esito = f_.get("esito") or {}
        else:
            esito = sposta(resto[0], resto[1], resto[2], resto[3], opz.get("cartella"), opz.get("progetto"), opz.get("titolo"))
    except Exception as e:  # il file d'esito deve dire finito anche quando lo spostamento cade
        esito = {"errore": ("lo spostamento è caduto: %s" % e)[:200]}
    if f:
        scrivi_esito(f, dict(esito, finito=True))
    print(json.dumps(esito, ensure_ascii=True))
    return 0 if "errore" not in esito else 1
