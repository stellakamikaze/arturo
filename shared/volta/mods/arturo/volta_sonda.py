"""Volta: l'elenco delle sessioni di Claude di questa macchina e delle macchine di Herdr.

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
  python3 volta_sonda.py duplica MACCHINA [--progetto SLUG] [--cartella DIR] [-- PROMPT]
      una sessione nuova accanto a un'altra: come nasci, ma nella cartella di quella sessione (la base
      dei progetti se la cartella non c'è più). Stesso contratto di nasci (#5291). In un progetto Volta
      passa PROMPT = /inizio SLUG (#5465).
  python3 volta_sonda.py fork MACCHINA SESSIONID [--progetto SLUG] [--cartella DIR] [--titolo NOME]
      una copia della conversazione SESSIONID in una sessione nuova (claude --bg --resume SESSIONID
      --fork-session), nella cartella della sessione: l'originale resta com'è. Stesso contratto di nasci;
      se la cartella non c'è più risponde {errore}, perché claude cerca lì la conversazione (#5291).
  python3 volta_sonda.py azione MACCHINA logs|stop|respawn|rm ID
      un gesto su una sessione in background. logs: le ultime righe dello schermo, per chi non ha
      trascrizione. respawn (Riavvia) accende prima il servizio di Claude su MACCHINA, come nasci: il
      processo nuovo nasce da lì (#5215). stop, rm e logs non fanno nascere processi e non lo toccano.
  python3 volta_sonda.py congeda MACCHINA ID SESSIONID [--cartella DIR] [--auto]
      il primo tempo della chiusura di una sessione (12/11/2026): claude stop ID, poi la stessa
      conversazione ripresa in background col solo /fine (claude --bg --resume SESSIONID, senza
      --fork-session), nella sua cartella. Lo stop finale lo chiede Volta a /fine finito. Mai rm.
      --auto: la chiusura automatica di una sessione ferma (#5366), col suo motivo nel testo di /fine.
      Stampa {ok, fermata} oppure {errore}.
  python3 volta_sonda.py apri MACCHINA ID [--riavvia]
      prepara l'aggancio di una sessione in background: accende il servizio di Claude su MACCHINA, così
      claude attach trova chi tiene la sessione; con --riavvia fa prima claude respawn (una sessione in
      errore, o una che attach non riapre). Stampa {ok, riavviata} oppure {errore} (#5290).
  python3 volta_sonda.py rinomina MACCHINA SESSIONID [--portato] [-- NOME]
      il nome che la persona dà a una sessione dalla finestra (#5292): scrive cache/titolo/SESSIONID.json
      su MACCHINA con fonte "persona", che hooks/titolo-sessione.py non riscrive. Senza NOME toglie il
      nome scritto, e il titolo torna automatico. --portato segna che Claude Code ha già quel nome
      (/rename scritto nella sessione da Volta). Stampa {ok, titolo} oppure {errore}.
  python3 volta_sonda.py sposta DA A ID SESSIONID --cartella DIR [--progetto SLUG] [--titolo NOME]
      sposta una sessione in background sull'altra macchina A, con la stessa conversazione e lo stesso
      sessionId (12/11/2026): i passi stanno in volta_sposta.py. Stessa risposta di nasci, o {errore}.
  python3 volta_sonda.py progetto MACCHINA SESSIONID [--iniziato] -- SLUG
      il progetto che la persona dà a una sessione dalla finestra (#5292): scrive cache/scheda/SESSIONID.json
      su MACCHINA con fonte "persona", che hooks/scheda-terminale.py non riscrive e non toglie a fine
      sessione. Un progetto nuovo porta inizio: false, e la lettura dà daIniziare finché Volta non ha
      scritto /inizio nella sessione; --iniziato lo chiude (#5465). Stampa {ok, progetto, iniziato}
      oppure {errore}.
  python3 volta_sonda.py inizia MACCHINA ID SESSIONID SLUG [--cartella DIR]
      una sessione in background spostata in un progetto riparte da /inizio SLUG (#5465): claude stop ID,
      poi la stessa conversazione ripresa col solo /inizio, come congeda. Stampa {ok, fermata} oppure
      {errore}.
  python3 volta_sonda.py servizio MACCHINA
      accende il servizio di Claude (claude daemon run) su MACCHINA se manca, dove sopravvive: il
      LaunchAgent di servizi-gui.sh o l'attività di servizio-claude.ps1 se ci sono; altrimenti staccato,
      e su un Windows raggiunto con hc exec in un terminale di herdr-core (hc run). Un servizio che
      risponde non si tocca. Stampa {come} oppure {errore} (#5208).

Una riga di "sessioni": { macchina, host, questa, sessionId, id, nome, progetto, titolo, stato, aspetta, tipo,
attach, cartella, ultimo, risposta, azione, daPortare }. `host` è il nome della macchina in Herdr ("qui" per
questa). Una macchina senza Claude Code resta fuori; una che non risponde tiene le righe dell'ultima
lettura buona, segnate `vecchia`; così anche tutte le macchine di prima, se è Herdr a non rispondere.
Progetto e nome restano col lavoro: la sonda tiene su ogni macchina un registro per lavoro
(<cartella di Claude>/cache/volta-lavori/<id del lavoro>.json), perché /clear cambia il sessionId e la
scheda nuova riparte dalla cartella. Con fonte "cartella" e senza registro la cartella base dei progetti
non è un progetto: la riga esce con progetto vuoto ("Senza progetto").
Una lettura dura al più ATTESA_LETTURA secondi, macchine lente comprese (VOLTA_ATTESA_LETTURA la cambia).
Per le prove: VOLTA_HC (il comando hc), VOLTA_SONDA_LOCALE (un JSON al posto della sonda di questa macchina).
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
import zlib
# Niente .pyc nella cartella del mod: Herdr ricarica il mod a ogni file nuovo che vi compare, anche in
# __pycache__, e la ricarica ferma per sempre le attese di Volta (cx.sleep di Sposta, #5556, 13/11/2026).
# La variabile vale per i Python figli (lo spostamento staccato, il microfono).
sys.dont_write_bytecode = True
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
from concurrent.futures import ThreadPoolExecutor

# Il registro degli eventi (#5549) sta accanto: anche quando un banco o volta_sposta.py carica questo file
# da un'altra cartella.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import volta_registro as registro  # noqa: E402

# Il terminale di Herdr che ospita un processo: Herdr mette HC_TERMINAL_ID nell'ambiente della shell di
# ogni scheda, e claude lo eredita. Sul Mac e su Linux l'ambiente lo dà ps; su Windows si legge dalla
# memoria del processo (PEB, ProcessParameters, Environment: scostamenti dei processi a 64 bit), perché
# nessun comando di sistema lo mostra. None se il processo non c'è, non si legge o non sta in Herdr.
# Sta a parte perché entra nella SONDA, che gira sulla macchina da leggere, e il banco la prova da sola.
TERMINALE = r'''
def terminale_di(pid):
    import os, subprocess
    if os.name != "nt":
        try:
            amb = subprocess.run(["ps", "eww", "-o", "command=", "-p", str(pid)], capture_output=True, text=True,
                                 errors="replace", stdin=subprocess.DEVNULL, timeout=5).stdout
        except (OSError, subprocess.SubprocessError):
            return None
        return next((x[15:] for x in amb.split() if x.startswith("HC_TERMINAL_ID=")), None)
    try:
        import ctypes
        from ctypes import wintypes as w
        k, n = ctypes.WinDLL("kernel32"), ctypes.WinDLL("ntdll")
        k.OpenProcess.restype = w.HANDLE
        k.OpenProcess.argtypes = [w.DWORD, w.BOOL, w.DWORD]
        k.ReadProcessMemory.restype = w.BOOL
        k.ReadProcessMemory.argtypes = [w.HANDLE, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t)]
        k.CloseHandle.argtypes = [w.HANDLE]
        n.NtQueryInformationProcess.restype = ctypes.c_long
        n.NtQueryInformationProcess.argtypes = [w.HANDLE, ctypes.c_int, ctypes.c_void_p, ctypes.c_ulong, ctypes.c_void_p]
        if ctypes.sizeof(ctypes.c_void_p) != 8:
            return None
        h = k.OpenProcess(0x0410, False, pid)  # PROCESS_QUERY_INFORMATION | PROCESS_VM_READ
        if not h:
            return None
        try:
            def leggi(indirizzo, quanti):
                buf, letti = ctypes.create_string_buffer(quanti), ctypes.c_size_t(0)
                if not indirizzo or not k.ReadProcessMemory(h, ctypes.c_void_p(indirizzo), buf, quanti, ctypes.byref(letti)):
                    return b""
                return buf.raw[:letti.value]
            def numero(indirizzo):
                b = leggi(indirizzo, 8)
                return int.from_bytes(b, "little") if len(b) == 8 else 0
            info = (ctypes.c_void_p * 6)()  # PROCESS_BASIC_INFORMATION: il secondo campo è l'indirizzo del PEB
            if n.NtQueryInformationProcess(h, 0, info, ctypes.sizeof(info), None) != 0 or not info[1]:
                return None
            parametri = numero(info[1] + 0x20)       # PEB.ProcessParameters
            blocco = numero(parametri + 0x80) if parametri else 0       # .Environment
            lungo = numero(parametri + 0x3F0) if parametri else 0       # .EnvironmentSize, in byte
            if not blocco or not 0 < lungo <= 4 * 1024 * 1024:
                return None
            for riga in leggi(blocco, lungo).decode("utf-16-le", "replace").split("\0"):
                if riga.startswith("HC_TERMINAL_ID="):
                    return riga[15:]
            return None
        finally:
            k.CloseHandle(h)
    except Exception:
        return None
'''

# L'elenco di `claude agents --json` dentro un'uscita: claude può scrivere un avviso prima del JSON, e
# quella riga in più faceva sparire tutte le sessioni della macchina. Si legge dal primo "[" che apre
# un elenco di oggetti; None se non c'è. Sta a parte perché entra nella SONDA e in NASCI, che girano
# sulla macchina da leggere, e serve anche qui.
ELENCO = r'''
def elenco(testo):
    import json
    testo = testo or ""
    i = testo.find("[")
    while i >= 0:
        try:
            v = json.JSONDecoder().raw_decode(testo, i)[0]
        except ValueError:
            v = None
        if isinstance(v, list) and all(isinstance(x, dict) for x in v):
            return v
        i = testo.find("[", i + 1)
    return None
'''
exec(ELENCO)

# La ricerca di claude, una sola per il mod (#5576, 14/11/2026): qui con exec, come ELENCO, e negli
# script che girano sulle macchine al posto di #CLAUDE#. Prima i gesti su questa macchina cercavano solo
# nel PATH, che sul Mac non ha ~/.local/bin quando Herdr parte dal Dock.
CERCA_CLAUDE = r'''
def trova_claude():
    """claude come lo trova il PATH, altrimenti dove lo mette l'installatore (~/.local/bin)."""
    fine = ".exe" if os.name == "nt" else ""
    return shutil.which("claude") or os.path.expanduser("~/.local/bin/claude" + fine)
'''
exec(CERCA_CLAUDE)

# Gira sulla macchina da leggere (anche con hc exec, passata in base64). Stampa un JSON:
# {"claude": percorso o null, "sessioni": [...]} con progetto e ultime parole letti dai file di Claude,
# oppure {"errore"} se claude agents non dà l'elenco: la macchina è irraggiungibile, non vuota.
# Chi la lancia mette davanti T, i secondi che ha: claude agents non aspetta oltre.
SONDA = r'''
import glob, json, os, re, shutil, subprocess, sys, time
scade =time.time() + (T if "T" in globals() else 40)
fine = ".exe" if os.name == "nt" else ""
#CLAUDE#
cl = trova_claude()
if not os.path.exists(cl):
    print(json.dumps({"claude": None, "sessioni": []})); raise SystemExit
radice = os.environ.get("CLAUDE_CONFIG_DIR") or os.path.expanduser("~/.claude")
# Senza --all claude agents nasconde le sessioni in background fermate (stopped) e quelle in errore
# (failed): Volta non le mostrerebbe, e Riavvia non comparirebbe mai (#5203). Delle chiuse tiene quelle
# nate negli ultimi CHIUSE_GIORNI giorni; un Claude senza --all dà l'elenco di prima.
CHIUSE_GIORNI = 3
CHIUSE = ("done", "stopped", "failed", "crashed")
#ELENCO#
guasto = [""]
def agenti(extra):
    try:
        r = subprocess.run([cl, "agents", "--json"] + extra, capture_output=True, text=True, encoding="utf-8",
                           errors="replace", stdin=subprocess.DEVNULL, timeout=max(2, min(40, scade - time.time())))
    except subprocess.TimeoutExpired:
        guasto[0] = "claude agents non ha risposto in tempo"
        return None
    if r.returncode != 0:
        righe = [x.strip() for x in ((r.stderr or "") + "\n" + (r.stdout or "")).splitlines() if x.strip()]
        guasto[0] = "claude agents: " + (righe[0][:140] if righe else "uscita %d" % r.returncode)
        return None
    if not (r.stdout or "").strip():
        return []
    v = elenco(r.stdout)
    if v is None:
        guasto[0] = "claude agents: risposta senza elenco"
    return v
sessioni = agenti(["--all"])
if sessioni is None:
    sessioni = agenti([])
if sessioni is None:
    # un elenco che non si legge non è un elenco vuoto: chi chiama tiene le righe dell'ultima lettura
    print(json.dumps({"errore": guasto[0] or "claude agents non risponde"})); raise SystemExit
tutte = list(sessioni)
soglia = (time.time() - CHIUSE_GIORNI * 86400) * 1000
def usata(s):
    # Nata da più di CHIUSE_GIORNI giorni ma usata da poco: il servizio di Claude ritira da solo una
    # sessione ferma da un'ora (#5495) e la lascia "done", anche se è nata una settimana fa. Conta
    # l'ultima scrittura della trascrizione.
    if (s.get("startedAt") or 0) >= soglia:
        return True
    sid = s.get("sessionId")
    f = glob.glob(os.path.join(radice, "projects", "*", sid + ".jsonl")) if isinstance(sid, str) and re.fullmatch(r"[0-9A-Za-z-]{4,64}", sid) else []
    try:
        return bool(f) and os.path.getmtime(f[0]) * 1000 >= soglia
    except OSError:
        return False
sessioni = [s for s in sessioni if s.get("kind") != "background" or (s.get("state") or s.get("status")) not in CHIUSE
            or usata(s)]
def testo(c):
    if isinstance(c, str):
        return c
    return " ".join(b.get("text", "") for b in c if isinstance(b, dict) and b.get("type") == "text")
#TERMINALE#
# Il registro per lavoro (cache/volta-lavori/<lavoro>.json): progetto e nome restano col lavoro. La scheda
# e il titolo di Arturo portano il sessionId, che /clear e la rotazione cambiano: la scheda nuova riparte
# dalla cartella, e tutte le sessioni finivano sotto "ClaudeCode" (revisione dell'11/11/2026). Il lavoro
# è l'id della sessione in background, che resta quello della nascita, o il pid di un'interattiva.
# Una fonte forte vale e aggiorna il registro; la fonte debole ("cartella", o nessuna scheda) cede al
# registro; senza registro il nome della cartella base o della casa non è un progetto: resta vuoto.
FORTI = ("persona", "inizio", "volta", "teletrasporto", "file")
LAVORI_GIORNI = 14
lavori = os.path.join(radice, "cache", "volta-lavori")
casa = os.path.expanduser("~")
base = None
try:  # la base dei progetti come la legge NASCI: arturo.json di Volta
    with open(os.path.join(os.environ.get("HERDR_APP_HOME") or os.path.join(casa, ".config", "herdr-app"), "arturo.json"), encoding="utf-8") as fh:
        base = json.load(fh).get("base")
except (OSError, ValueError, AttributeError):
    pass
if not isinstance(base, str) or not base:
    base = os.environ.get("PROJECTS_BASE") or os.path.join(casa, "Documents", "ClaudeCode")
basi = {os.path.basename(os.path.normpath(os.path.expanduser(x))).lower() for x in (base, casa)}
def lavoro_di(s):
    if not s.get("sessionId"):
        return None
    k = s.get("id") if s.get("kind") == "background" else ("pid-%d" % s["pid"] if isinstance(s.get("pid"), int) else None)
    return k if isinstance(k, str) and re.fullmatch(r"[0-9A-Za-z-]{4,64}", k) else None
def leggi(f):
    try:
        with open(f, encoding="utf-8") as fh:
            d = json.load(fh)
    except (OSError, ValueError):
        return {}
    return d if isinstance(d, dict) else {}
def scrivi(f, d):
    try:  # un registro che non si scrive non ferma l'elenco
        os.makedirs(os.path.dirname(f), exist_ok=True)
        tmp = "%s.%d.tmp" % (f, os.getpid())
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(d, fh)
        os.replace(tmp, f)
    except OSError:
        pass
for s in sessioni:
    sid = s.get("sessionId") or "-"
    k = lavoro_di(s)
    reg = leggi(os.path.join(lavori, k + ".json")) if k else {}
    nuovo = {x: reg[x] for x in ("progetto", "fonte", "titolo") if isinstance(reg.get(x), str) and reg[x].strip()}
    s["progetto"] = None
    s["daIniziare"] = None
    s["spostata"] = False
    fonte = None
    try:  # il progetto lo scrive hooks/scheda-terminale.py di Arturo; senza Arturo resta vuoto
        with open(os.path.join(radice, "cache", "scheda", sid + ".json"), encoding="utf-8") as fh:
            scheda = json.load(fh)
        p, fonte = scheda.get("progetto"), scheda.get("fonte")
        s["spostata"] = bool(scheda.get("spostata"))
        if isinstance(p, str) and p.strip():
            s["progetto"] = p.strip()[:60]
            # spostata dalla persona in un progetto e non ancora ripartita da /inizio (#5465): Volta lo
            # scrive appena è ferma. Una scheda senza il campo (spostata prima) non dà niente.
            if fonte == "persona" and scheda.get("inizio") is False:
                s["daIniziare"] = s["progetto"]
    except (OSError, ValueError, AttributeError):
        pass
    if s["progetto"] and fonte in FORTI:
        nuovo.update(progetto=s["progetto"], fonte=fonte)
    elif fonte in (None, "", "cartella"):
        if nuovo.get("progetto"):
            s["progetto"] = nuovo["progetto"].strip()[:60]
        elif s["progetto"] and s["progetto"].lower() in basi:
            s["progetto"] = None
    # Un'interattiva partita nella shell di una scheda di Herdr porta nell'ambiente il nome di quel
    # terminale: Volta la porta davanti col clic invece di rimandare a "un Terminale" (11/11/2026).
    s["terminale"] = None
    if s.get("kind") != "background" and isinstance(s.get("pid"), int):
        s["terminale"] = terminale_di(s["pid"])
    s["titolo"] = None
    s["sintesi"] = None
    s["daPortare"] = None
    scritto = False
    ftit = os.path.join(radice, "cache", "titolo", sid + ".json")
    try:  # il titolo lo scrive hooks/titolo-sessione.py di Arturo a fine turno; senza resta vuoto
        with open(ftit, encoding="utf-8") as fh:
            tit = json.load(fh)
        t = tit.get("titolo")
        # la sintesi: cosa succede adesso, al più 5 parole (titolo-sessione.py, 12/11/2026), per la testata
        si = tit.get("sintesi")
        if isinstance(si, str) and si.strip():
            s["sintesi"] = " ".join(si.split()[:5])[:60]
        if isinstance(t, str) and t.strip():
            s["titolo"] = t.strip()[:80]
            scritto = tit.get("fonte") == "persona"
            # un nome scritto dalla persona che Claude Code non ha ancora: Volta lo porta con /rename
            if tit.get("fonte") == "persona" and not tit.get("portato"):
                s["daPortare"] = s["titolo"]
    except (OSError, ValueError, AttributeError):
        pass
    if scritto:
        nuovo["titolo"] = s["titolo"]
    elif nuovo.get("titolo") and reg.get("sessionId") != sid:
        # il lavoro ha cambiato sessionId (/clear, rotazione): il nome dato dalla persona passa al file
        # del sessionId nuovo, già "portato", così Volta non riscrive /rename e Rinomina lo toglie come prima
        s["titolo"] = nuovo["titolo"].strip()[:80]
        scrivi(ftit, {"titolo": s["titolo"], "fonte": "persona", "quando": time.time(), "peso": 0, "portato": True})
    else:
        nuovo.pop("titolo", None)  # stesso sessionId e nessun nome scritto: la persona l'ha tolto
    if k:
        nuovo["sessionId"] = sid
        if nuovo != {x: v for x, v in reg.items() if x != "quando"} and (len(nuovo) > 1 or reg):
            scrivi(os.path.join(lavori, k + ".json"), dict(nuovo, quando=time.time()))
    f = glob.glob(os.path.join(radice, "projects", "*", sid + ".jsonl"))
    if not f:
        continue
    with open(f[0], "rb") as fh:
        fh.seek(0, 2); fh.seek(max(0, fh.tell() - 3000000))
        righe = fh.read().decode("utf-8", "replace").splitlines()[1:]
    # Per le fasi di Volta (#5366): `interazione` è l'ora dell'ultimo messaggio vero (della persona o di
    # Claude, non le righe di sistema), `coda` la fine dell'ultimo testo di Claude, `chi` chi ha parlato
    # per ultimo ("claude" a turno chiuso con un testo, "azione" se l'ultima cosa è un comando, "persona"
    # per un messaggio senza risposta), `fineFatta` se l'ultimo messaggio della persona è /fine.
    risposta, azione, ultimo, interazione, coda, chi, fine_fatta = "", "", "", "", "", "", False
    for l in righe:
        try:
            d = json.loads(l)
        except ValueError:
            continue
        if not isinstance(d, dict):  # una riga tagliata a metà può essere un numero o una stringa
            continue
        ultimo = d.get("timestamp", ultimo)
        m = d.get("message") or {}
        if not isinstance(m, dict):
            continue
        if d.get("type") == "assistant":
            for b in m.get("content", []) or []:
                if not isinstance(b, dict):
                    continue
                if b.get("type") == "text" and b.get("text", "").strip():
                    tx = b["text"].strip()
                    # tagliata a una parola intera, col segno: l'Anteprima di Volta la mostra (#5240)
                    risposta = tx if len(tx) <= 400 else tx[:400].rsplit(None, 1)[0] + "\u2026"
                    coda = tx[-300:]
                    chi, interazione = "claude", d.get("timestamp", interazione)
                elif b.get("type") == "tool_use":
                    i = b.get("input") or {}
                    azione = b.get("name", "") + ": " + str(i.get("description") or i.get("command") or i.get("file_path") or "")[:150]
                    chi, interazione = "azione", d.get("timestamp", interazione)
        elif d.get("type") == "user" and not d.get("isMeta"):
            c = m.get("content")
            if isinstance(c, list) and any(isinstance(b, dict) and b.get("type") == "tool_result" for b in c):
                interazione = d.get("timestamp", interazione)  # l'esito di un comando: Claude lavora ancora
                continue
            tx = testo(c).strip()
            if not tx or tx.startswith(("<local-command", "<system-reminder>", "Caveat:", "<task-notification>")):
                continue
            chi, interazione, coda = "persona", d.get("timestamp", interazione), ""
            fine_fatta = bool(re.match(r"\s*(<command-message>[^<]*</command-message>\s*)?(<command-name>)?/fine\b", tx))
    s.update(risposta=risposta, azione=azione, ultimo=ultimo, interazione=interazione, coda=coda, chi=chi, fineFatta=fine_fatta)
# La pulizia del registro: il pid di un'interattiva sparita torna libero per un altro processo, quindi la
# sua voce va via subito; quella di un lavoro che claude agents non elenca più dopo LAVORI_GIORNI giorni.
vivi = {lavoro_di(s) for s in tutte}
try:
    for n in os.listdir(lavori):
        f = os.path.join(lavori, n)
        if n.endswith(".json") and n[:-5] not in vivi and (n.startswith("pid-") or time.time() - os.path.getmtime(f) > LAVORI_GIORNI * 86400):
            os.remove(f)
except OSError:
    pass
# Un ricevitore del microfono morto male (kill -9, riavvio) lascia microfono.json e l'ingresso sul
# virtuale: ripara lo rimette. Gira solo se il file c'è, e un ponte vivo non lo tocca.
# La cartella di Volta come cacheVolta() di dati.js: una finestra di prova (HERDR_APP_HOME fuori da
# ~/.config/herdr-app) tiene la sua sotto la sua cartella di Herdr e non tocca il ponte della vera (#5449).
app_vc = os.environ.get("HERDR_APP_HOME") or os.path.join(casa, ".config", "herdr-app")
di_prova = os.path.normcase(os.path.abspath(app_vc)) != os.path.normcase(os.path.abspath(os.path.join(casa, ".config", "herdr-app")))
vc = os.environ.get("VOLTA_CACHE") or (os.path.join(app_vc, "cache", "volta") if di_prova else os.path.join(casa, ".cache", "volta"))
mic = os.path.join(app_vc, "mods", "arturo", "volta_microfono.py")
if os.path.exists(os.path.join(vc, "microfono.json")) and os.path.exists(mic):
    try:
        subprocess.run([sys.executable, mic, "ripara"], capture_output=True, stdin=subprocess.DEVNULL, timeout=10)
    except (OSError, subprocess.SubprocessError):
        pass
# Le nascite che cadono (13/11/2026): con Documenti bloccato da macOS ogni sessione nuova di un Mac
# usciva in 10 s con "exit 1 before init", e Volta la faceva ripartire a ogni clic senza dire niente
# della macchina. I job stanno in <config>/jobs/<id>/state.json, fuori da Documenti: si leggono anche
# quando Documenti non risponde. Rotta = almeno NASCITE_CRASH crash "before init" su almeno due lavori
# negli ultimi NASCITE_MIN minuti, e nessun lavoro nato dopo l'ultimo crash che stia in piedi.
NASCITE_MIN = 30
NASCITE_CRASH = 3
CONGEDO_INTENTO = "/fine congedo da Volta"
lavori_dir = os.path.join(radice, "jobs")
def stato_lavoro(n):
    try:
        with open(os.path.join(lavori_dir, n, "state.json"), encoding="utf-8") as fh:
            d = json.load(fh)
    except (OSError, ValueError):
        return {}
    return d if isinstance(d, dict) else {}
def nascite(ora=None):
    ora = ora or time.time()
    crash, nati = [], []
    try:
        nomi = os.listdir(lavori_dir)
    except OSError:
        return None
    for n in nomi:
        try:
            if ora - os.path.getmtime(os.path.join(lavori_dir, n, "state.json")) > NASCITE_MIN * 60:
                continue
        except OSError:
            continue
        d = stato_lavoro(n)
        perche = str(d.get("detail") or "")
        if d.get("state") in ("failed", "crashed") and "before init" in perche:
            m = re.search(r"(exit \d+|SIGKILL \(\d+\)) before init", perche)
            crash.append((str(d.get("updatedAt") or ""), n, m.group(0) if m else "before init"))
        elif d.get("state") not in ("failed", "crashed"):
            nati.append(str(d.get("createdAt") or ""))
    if len(crash) < NASCITE_CRASH or len({c[1] for c in crash}) < 2:
        return None
    crash.sort()
    if any(x > crash[-1][0] for x in nati):
        return None
    return {"rotta": True, "da": crash[0][0], "ultimo": crash[-1][0], "quante": len(crash), "motivo": crash[-1][2]}
# Un congedo rimasto a metà (13/11/2026): la sessione ripresa con /fine resta viva, o in errore, e il
# registro dei congedi l'ha persa. L'intento del lavoro dice che la persona l'aveva chiusa.
for s in sessioni:
    if s.get("kind") == "background" and isinstance(s.get("id"), str) and re.fullmatch(r"[0-9A-Za-z-]{4,64}", s["id"]):
        if str(stato_lavoro(s["id"]).get("intent") or "").startswith(CONGEDO_INTENTO):
            s["congedo"] = True
# solo ASCII: la console di Windows stampa in cp1252 e una freccia nel testo rompeva la riga
uscita = {"claude": cl, "sessioni": sessioni}
rotta = nascite()
if rotta:
    uscita["nascita"] = rotta
print(json.dumps(uscita))
'''
SONDA = SONDA.replace("#TERMINALE#", TERMINALE.strip())
SONDA = SONDA.replace("#ELENCO#", ELENCO.strip()).replace("#CLAUDE#", CERCA_CLAUDE.strip())


def senza_commenti(codice):
    """Il codice senza le righe di solo commento: la sonda verso un'altra macchina viaggia in una riga
    di cmd.exe (8191 caratteri), e i commenti ne prendevano quasi metà (13/11/2026). Un # dentro una
    riga di codice resta: si tolgono solo le righe che cominciano con #."""
    return "\n".join(r for r in codice.split("\n") if not r.lstrip().startswith("#"))

# Gira sulla macchina dove nasce la sessione (anche con hc exec). L'argomento è un JSON in base64
# ({"prompt", "progetto"}, e per Duplica e Fork anche "cartella", "riprendi", "nome"): passa intero anche
# fra le virgolette di Windows. La cartella è la base dei progetti di quella macchina (arturo.json di
# Volta), perché claude --bg vuole una cartella fidata; con "cartella" è quella, se c'è ancora. Con
# "riprendi" (un sessionId) la sessione nuova è una copia di quella conversazione (--resume e
# --fork-session): l'originale tiene il suo id e la sua trascrizione (provato l'11/11/2026).
# Stampa {"id", "sessionId", "claude", "cartella"} oppure {"errore"}; mai una seconda sessione.
NASCI = r'''
import base64, json, os, re, shutil, subprocess, sys, time
a = json.loads(base64.b64decode(sys.argv[1]).decode("utf-8"))
def esci(**d):
    print(json.dumps(d)); raise SystemExit
fine = ".exe" if os.name == "nt" else ""
#CLAUDE#
cl = trova_claude()
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
cartella = a.get("cartella")
qui = bool(cartella) and os.path.isdir(cartella)
if a.get("riprendi") and not qui:
    # claude --resume cerca la conversazione fra quelle della cartella da cui parte
    esci(errore="la cartella della sessione non c'è più: " + str(cartella or "sconosciuta")[:120])
if qui:
    base = cartella
argv = [cl, "--bg"]
if a.get("riprendi"):
    # "stessa": la ripresa della stessa conversazione (il congedo, /fine), senza copia
    argv += ["--resume", a["riprendi"]] + ([] if a.get("stessa") else ["--fork-session"])
nome = str(a.get("nome") or "").lstrip("-").strip()[:60]
if nome:
    argv += ["-n", nome]
argv += [a["prompt"]] if a.get("prompt") else []
#ELENCO#
def processo(sid):
    """Il pid della sessione `sid` secondo claude agents, None se non gira, False se non si legge."""
    try:
        r = subprocess.run([cl, "agents", "--json", "--all"], capture_output=True, text=True, encoding="utf-8",
                           errors="replace", stdin=subprocess.DEVNULL, timeout=15)
        for s in elenco(r.stdout) or []:
            if s.get("sessionId") == sid or s.get("id") == sid:
                return s.get("pid")
        return None
    except (OSError, subprocess.SubprocessError):
        return False
def lancia():
    try:
        return subprocess.run(argv, cwd=base, capture_output=True, text=True, encoding="utf-8", errors="replace",
                              stdin=subprocess.DEVNULL, timeout=90)
    except subprocess.TimeoutExpired:
        esci(errore="claude --bg non ha risposto in 90 s: claude agents dice se è nata")
if a.get("stessa"):
    # la ripresa subito dopo claude stop non sveglia niente (12/11/2026): prima la sessione deve essere
    # ferma davvero, e dopo il lancio deve avere un processo; se no, un secondo tentativo
    for _ in range(15):
        if not processo(a["riprendi"]):
            break
        time.sleep(1)
    for tentativo in range(2):
        r = lancia()
        for _ in range(15):
            time.sleep(1)
            if processo(a["riprendi"]):
                break
        else:
            continue
        break
    else:
        esci(errore="ripresa lanciata, ma la sessione non riparte")
else:
    r = lancia()
uscita = (r.stdout or "") + "\n" + (r.stderr or "")
m = re.search(r"claude attach ([0-9A-Za-z-]+)", uscita)
if not m:
    righe = [x.strip() for x in uscita.splitlines() if x.strip() and not x.startswith("Starting background service")]
    if r.returncode == 0:
        esci(errore="è partita, ma non ho letto il suo id: claude agents la elenca")
    esci(errore="non parte in background: " + (righe[0][:160] if righe else "rc %d" % r.returncode))
corto = m.group(1)
sid = corto
# il sessionId intero serve per scrivere il progetto: claude agents può non elencarla subito
for giro in range(3):
    try:
        r = subprocess.run([cl, "agents", "--json"], capture_output=True, text=True, encoding="utf-8",
                           errors="replace", stdin=subprocess.DEVNULL, timeout=15)
        for s in elenco(r.stdout) or []:
            if s.get("id") == corto or str(s.get("sessionId", "")).startswith(corto):
                sid = str(s.get("sessionId") or corto)
    except (OSError, subprocess.SubprocessError):
        pass
    if sid != corto:
        break
    time.sleep(1)
def scrivi(f, d):
    try:
        os.makedirs(os.path.dirname(f), exist_ok=True)
        with open(f + ".tmp", "w", encoding="utf-8") as fh:
            json.dump(d, fh)
        os.replace(f + ".tmp", f)
    except OSError:
        pass
if a.get("progetto"):
    cache = os.path.join(os.environ.get("CLAUDE_CONFIG_DIR") or os.path.join(casa, ".claude"), "cache")
    # il registro del lavoro, subito: vale anche se il sessionId non si è letto, e resta dopo /clear
    scrivi(os.path.join(cache, "volta-lavori", corto + ".json"),
           {"progetto": a["progetto"], "fonte": "volta", "sessionId": sid, "quando": time.time()})
    if sid != corto:
        # il progetto per Volta (spazio giusto su ogni macchina), come l'eredità di porta-volta
        scrivi(os.path.join(cache, "scheda", sid + ".json"),
               {"stato": "nuova", "progetto": a["progetto"], "fonte": "volta", "quando": time.time()})
esci(id=corto, sessionId=sid, claude=cl, cartella=base)
'''
NASCI = NASCI.replace("#ELENCO#", ELENCO.strip()).replace("#CLAUDE#", CERCA_CLAUDE.strip())

# Gira sulla macchina della sessione (anche con hc exec): scrive il nome o il progetto che la persona le
# ha dato dalla finestra (#5292). L'argomento è un JSON in base64: {"cosa": "titolo" | "scheda",
# "sessionId", "valore", "portato"}. Il file del titolo si riscrive intero; quello della scheda tiene lo
# stato che c'era. La fonte "persona" dice ai due hook di Arturo di non riscriverli. Idempotente.
# Stampa {"ok": true, ...} oppure {"errore"}.
SCRIVI = r'''
import base64, json, os, sys, time
a = json.loads(base64.b64decode(sys.argv[1]).decode("utf-8"))
def esci(**d):
    print(json.dumps(d)); raise SystemExit
radice = os.environ.get("CLAUDE_CONFIG_DIR") or os.path.expanduser("~/.claude")
titolo = a["cosa"] == "titolo"
d = os.path.join(radice, "cache", "titolo" if titolo else "scheda")
f = os.path.join(d, a["sessionId"] + ".json")
try:
    with open(f, encoding="utf-8") as fh:
        prima = json.load(fh)
    if not isinstance(prima, dict):
        prima = {}
except (OSError, ValueError):
    prima = {}
valore = a.get("valore") or ""
try:
    if titolo and a.get("portato"):
        # solo se il nome è ancora quello: la persona può averlo cambiato nel frattempo
        if prima.get("fonte") != "persona" or (valore and prima.get("titolo") != valore):
            esci(ok=True, titolo=prima.get("titolo") or "", portato=False)
        nuovo = dict(prima, portato=True)
    elif titolo and not valore:
        if prima.get("fonte") == "persona":
            os.remove(f)
        esci(ok=True, titolo="")
    elif titolo:
        nuovo = {"titolo": valore, "fonte": "persona", "quando": time.time(), "peso": 0, "portato": False}
    elif a.get("iniziato"):
        # /inizio scritto nella sessione (#5465): il segno si chiude solo se il progetto è ancora quello
        if prima.get("fonte") != "persona" or prima.get("progetto") != valore:
            esci(ok=True, progetto=prima.get("progetto") or "", iniziato=False)
        nuovo = dict(prima, inizio=True)
    else:
        # inizio False: la sessione deve ancora ripartire da /inizio del progetto nuovo (#5465). Lo
        # stesso progetto di prima tiene il segno che aveva: la conversazione ha già quel contesto.
        stesso = prima.get("progetto") == valore
        nuovo = dict(prima or {"stato": "nuova"}, progetto=valore, fonte="persona", quando=time.time(),
                     inizio=prima.get("inizio", True) if stesso else False)
    os.makedirs(d, exist_ok=True)
    tmp = "%s.%d.tmp" % (f, os.getpid())
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(nuovo, fh)
    os.replace(tmp, f)
except OSError as e:
    esci(errore="non riesco a scrivere: " + str(e)[:160])
if titolo:
    esci(ok=True, titolo=nuovo["titolo"], portato=bool(nuovo.get("portato")))
esci(ok=True, progetto=valore, iniziato=nuovo.get("inizio") is not False)
'''

# Gira sulla macchina dove nascerà la sessione, prima di NASCI (#5208). Il servizio di Claude che tiene
# le sessioni in background (claude daemon) parte da solo al primo claude --bg, ma a tempo: muore con
# chi l'ha fatto nascere (hc exec chiude tutto ciò che avvia) e, nato da ssh, non ha il login. Un
# claude daemon run invece resta acceso anche senza sessioni, e uno a tempo già acceso gli cede il
# posto riprendendo le sessioni vive (provato il 10/11/2026). Qui: se il servizio risponde non si tocca;
# se manca lo si accende fuori dalla portata di hc exec. Sul Mac col LaunchAgent di servizi-gui.sh se
# c'è; altrimenti, chiesto da un'altra macchina, risponde {"serve": "hc-run"} come Windows (nato da ssh
# non sente il microfono, #5427), e chiesto da qui nasce staccato in una sessione nuova. Su Windows con l'attività di
# servizio-claude.ps1 se c'è; da hc exec un figlio non si stacca dal job, quindi senza attività risponde
# {"serve": "hc-run"} e il terminale lo apre chi chiama. L'argomento è "remoto" o "qui".
# Con "serve" c'è anche "claude", il percorso intero: hc run sul Mac non ha ~/.local/bin nel PATH (#5560).
# L'etichetta del LaunchAgent e il nome dell'attività stanno anche in servizi-gui.sh, servizio-claude.ps1
# e installa-herdr.sh: il banco HZ43 li tiene uguali.
# Stampa {"acceso": true, "come"} oppure {"serve"} oppure {"errore"}.
SERVIZIO = r'''
import json, os, re, shutil, subprocess, sys, time
def esci(**d):
    print(json.dumps(d)); raise SystemExit
fine = ".exe" if os.name == "nt" else ""
#CLAUDE#
cl = trova_claude()
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
    elif remoto:
        # Da hc exec il servizio sarebbe figlio di ssh: macOS gli nega il microfono in silenzio, e così a
        # ogni sessione in background che ne nasce (12/11/2026, #5427). Lo apre chi chiama, in un
        # terminale di Herdr Core, che vive nella sessione grafica e ha il microfono.
        esci(serve="hc-run", claude=cl)
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
        esci(serve="hc-run", claude=cl)
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
SERVIZIO = SERVIZIO.replace("#CLAUDE#", CERCA_CLAUDE.strip())

# Le attese di una nascita (#5214): ogni fase ha il suo tetto, e dati.js (nasciSu) aspetta la somma più
# un margine. Il servizio si ferma al suo tetto prima di far nascere la sessione, così una nascita già
# partita non si taglia a metà: tagliata, nascerebbe lo stesso mentre Volta dice "non risponde".
ATTESA_MACCHINE = 15
ATTESA_SERVIZIO = 120
ATTESA_NASCITA = 180
# Un gesto su una sessione (azione). Riavvia passa prima dal servizio: dati.js (azioneSessione) aspetta
# ATTESA_SERVIZIO più ATTESA_AZIONE più il margine, gli altri gesti ATTESA_AZIONE più il margine.
ATTESA_AZIONE = 60
# Una lettura dell'elenco (volta): un tetto solo per tutto, diviso fra Herdr e le macchine, che si leggono
# insieme. Sta sotto i 60 s che volta.js (aggiorna) aspetta: prima ogni macchina aveva i suoi 90 s per
# tentativo, e una sola macchina lenta lasciava l'elenco fermo all'ultima lettura (revisione dell'11/11/2026).
ATTESA_LETTURA = 45
MARGINE_LETTURA = 3  # per scrivere il documento dopo l'ultima macchina

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
    return [shutil.which("hc") or os.path.expanduser("~/.local/bin/hc" + (".exe" if os.name == "nt" else ""))]


def attesa_lettura():
    try:
        return max(6, int(os.environ.get("VOLTA_ATTESA_LETTURA") or ATTESA_LETTURA))
    except ValueError:
        return ATTESA_LETTURA


def resta(entro):
    """I secondi interi che restano alla lettura; senza scadenza (una chiamata sola) il tetto intero."""
    return int(entro - time.monotonic()) if entro is not None else attesa_lettura() - MARGINE_LETTURA


def evento_hc(argv):
    """("hc exec python3", "amaltea") per un comando hc, o None per un comando che non passa da hc."""
    base = hc()
    if len(argv) <= len(base) or argv[:len(base)] != base:
        return None
    resto, macchina, prog = argv[len(base):], "", ""
    verbo = resto[0]
    i = 1
    while i < len(resto) and resto[i].startswith("-"):
        if resto[i] == "--on" and i + 1 < len(resto):
            macchina = resto[i + 1]
        i += 2 if resto[i] in ("--on", "--timeout", "--name") else 1
    if verbo == "exec" and i < len(resto):
        prog = " " + os.path.basename(resto[i])
    return "hc %s%s" % (verbo, prog), macchina


def lancia(argv, timeout=60):
    # stdin chiuso: senza, ssh.exe e hc su Windows restano appesi
    ev = evento_hc(argv)
    t = time.monotonic()
    try:
        r = subprocess.run(argv, capture_output=True, text=True, encoding="utf-8", errors="replace",
                           stdin=subprocess.DEVNULL, timeout=timeout, env=dict(os.environ, PYTHONIOENCODING="utf-8"))
    except subprocess.TimeoutExpired:
        if ev:  # il registro (#5549): le chiamate a hc che scadono
            registro.registra(ev[0], macchina=ev[1], ms=(time.monotonic() - t) * 1000, esito="tetto",
                              errore="oltre %s s" % timeout)
        raise
    if ev:
        testo = (r.stderr or r.stdout or "").strip() if r.returncode else ""
        registro.registra(ev[0], macchina=ev[1], ms=(time.monotonic() - t) * 1000,
                          esito="ok" if r.returncode == 0 else "rc %d" % r.returncode,
                          errore=testo.splitlines()[-1] if testo else None)
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


def chi(nome):
    """Il nome di `nome` nei messaggi per le persone: "qui" o vuoto è il nome vero di questa macchina, mai
    "qui" (#5534: gli errori dicevano "non parte su qui"). Lo usano anche volta_sposta.py e PREPARA."""
    return nome_qui() if nome in (None, "", "qui") else nome


def macchine(attesa=ATTESA_MACCHINE):
    """Le macchine di Herdr: [{nome, target, stato, perche}]. Senza hc o senza macchine: [].
    None se Herdr non risponde (hc esce male, non fa in tempo, risponde altro): non vuol dire che le
    macchine non ci sono più, e chi chiama tiene quelle di prima."""
    try:
        rc, out, _ = lancia(hc() + ["machine", "ls", "--json"], timeout=attesa)
    except FileNotFoundError:
        return []
    except (OSError, subprocess.SubprocessError):
        return None
    try:
        voci = json.loads(out).get("machines", []) if rc == 0 else None
    except (ValueError, AttributeError):
        voci = None
    if not isinstance(voci, list):
        return None
    return [{"nome": m.get("name") or m.get("host"), "target": m.get("target") or m.get("host"),
             "stato": m.get("state"), "perche": m.get("why")}
            for m in voci if isinstance(m, dict) and (m.get("name") or m.get("host"))]


def leggi_json(out):
    """L'ultima riga JSON di un'uscita: hc exec può mettere avvisi della shell prima."""
    for riga in reversed((out or "").strip().splitlines()):
        riga = riga.strip()
        if riga.startswith("{"):
            return json.loads(riga)
    raise ValueError("nessun JSON nell'uscita")


def entro_il_tetto(argv, entro, margine=0):
    """lancia() con i secondi che restano alla lettura. Fuori tempo dice quanti erano, non il comando."""
    t = resta(entro)
    if t < 2:
        raise RuntimeError("non ha risposto in tempo")
    try:
        return lancia(argv(t), timeout=t + margine)
    except subprocess.TimeoutExpired:
        raise RuntimeError("non ha risposto in %d s" % t) from None


def risposta(d):
    """La risposta della SONDA: {"errore"} vuol dire che la macchina c'è ma l'elenco non si legge."""
    if not isinstance(d, dict):
        raise RuntimeError("risposta che non è un elenco di sessioni")
    if d.get("errore"):
        raise RuntimeError(str(d["errore"])[:200])
    return d


def sonda_locale(entro=None):
    finto = os.environ.get("VOLTA_SONDA_LOCALE")
    if finto:
        return json.loads(finto)
    rc, out, err = entro_il_tetto(lambda t: [sys.executable, "-c", "T = %d\n" % max(2, t - 2) + SONDA], entro)
    if rc != 0:
        raise RuntimeError((err or out).strip()[-200:] or "rc %d" % rc)
    return risposta(leggi_json(out))


def sonda_remota(nome, entro=None):
    """La sonda su un'altra macchina via herdr-core: prima python3, poi python (Windows, dove python3
    può essere lo stub dello Store, che esce 9009). I due tentativi e l'elenco nudo dividono lo stesso
    tetto (`entro`), che vale anche per hc exec e per claude agents dentro la sonda."""
    # compressa: con terminale_di la sonda in base64 supererebbe gli 8191 caratteri di una riga di cmd.exe
    compressa = base64.b64encode(zlib.compress(senza_commenti(SONDA).encode(), 9)).decode()
    ultimo, senza = "nessun Python", 0
    for py in ("python3", "python"):
        rc, out, err = entro_il_tetto(lambda t: hc() + ["exec", "--on", nome, "--timeout", str(t), py, "-c",
                                                        "T=%d;import base64,zlib;exec(zlib.decompress(base64.b64decode('%s')))" % (max(2, t - 3), compressa)],
                                      entro, 1)
        if rc == 0:
            try:
                return risposta(leggi_json(out))
            except ValueError:
                ultimo = "risposta senza JSON"
                continue
        if non_parte(out, err):
            senza += 1
            continue
        ultimo = errore_hc((err or out).strip().splitlines()[-1]) if (err or out).strip() else "rc %d" % rc
    if senza < 2:
        raise RuntimeError(ultimo)
    # senza Python: l'elenco nudo di claude agents, senza progetto né ultime parole
    rc, out, err = entro_il_tetto(lambda t: hc() + ["exec", "--on", nome, "--timeout", str(t), "claude", "agents", "--json"], entro, 1)
    if rc != 0 and non_parte(out, err):
        return {"claude": None, "sessioni": []}  # né Python né Claude: non è una macchina di Volta
    if rc != 0:
        raise RuntimeError(errore_hc(((err or out).strip().splitlines() or ["rc %d" % rc])[-1]))
    sessioni = elenco(out) if (out or "").strip() else []  # noqa: F821 (elenco viene da ELENCO)
    if sessioni is None:
        raise RuntimeError("claude agents: risposta senza elenco")
    return {"claude": "claude", "sessioni": sessioni}


def errore_hc(riga):
    """La riga d'errore di hc per le persone: hc scrive {"error": {"message": ...}}, e quel JSON
    finiva intero sulla riga della sessione. Resta il solo messaggio; una riga qualunque resta com'è."""
    riga = (riga or "").strip()
    if riga.startswith("{"):
        try:
            e = json.loads(riga).get("error")
            if isinstance(e, dict) and e.get("message"):
                return str(e["message"])[:200]
        except (ValueError, AttributeError):
            pass
    return riga[:200]


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


def raccogli(viste=None, prima=None, entro=None):
    """Le voci per macchina, interrogate in parallelo: questa per prima, poi quelle di Herdr.
    `viste`: gli host in cui Volta ha già visto Claude (dal documento di prima). Una macchina che non
    risponde e dove Claude non si è mai visto resta fuori: può essere un server senza Claude.
    `prima`: le macchine del documento di prima. Se Herdr non dice le macchine restano quelle,
    irraggiungibili, con le righe dell'ultima lettura: prima sparivano tutte, sessioni comprese.
    `entro`: la scadenza della lettura (time.monotonic), la stessa per Herdr e per ogni macchina."""
    if entro is None:
        entro = time.monotonic() + attesa_lettura() - MARGINE_LETTURA
    qui = {"macchina": nome_qui(), "host": "qui", "questa": True, "target": None}
    note = macchine(max(2, min(ATTESA_MACCHINE, resta(entro) // 3)))
    if note is None:
        altre = [{"macchina": m.get("macchina") or m["host"], "host": m["host"], "questa": False, "target": None,
                  "irraggiungibile": "Herdr non dice le macchine: sono quelle dell'ultima lettura"}
                 for m in (prima or []) if isinstance(m, dict) and isinstance(m.get("host"), str)
                 and m["host"] != "qui" and not m.get("questa")]
    else:
        altre = [{"macchina": m["nome"], "host": m["nome"], "questa": False, "target": m["target"],
                  "stato_hc": m["stato"], "perche": m["perche"]} for m in note]

    def una(v):
        if "irraggiungibile" in v:
            return v
        if not v["questa"] and v.get("stato_hc") not in (None, "connected"):
            v["irraggiungibile"] = (v.get("perche") or "Herdr non la raggiunge")[:200]
            return v
        with registro.Durata("lettura", macchina="qui" if v["questa"] else v["host"]) as dura:
            try:
                d = sonda_locale(entro) if v["questa"] else sonda_remota(v["host"], entro)
            except Exception as e:  # spenta, in stop, rete giù: lo si dice e si va avanti
                v["irraggiungibile"] = str(e)[:200]
                dura.esito, dura.errore = "irraggiungibile", v["irraggiungibile"]
                return v
        v["claude"] = d.get("claude")
        v["sessioni"] = d.get("sessioni") or []
        if isinstance(d.get("nascita"), dict):
            v["nascita"] = d["nascita"]
        return v

    voci = [qui] + altre
    with ThreadPoolExecutor(max_workers=max(1, len(voci))) as ex:
        voci = list(ex.map(una, voci))
    # una macchina che risponde ma non ha Claude Code (un server, un Raspberry) non è di Volta
    viste = set(viste or ())
    return [v for v in voci if v.get("claude") or ("irraggiungibile" in v and (v["questa"] or v["host"] in viste))]


def gia_viste(precedente):
    return {m.get("host") for m in (precedente or {}).get("macchine", [])}


def nascita(s):
    """L'ora di nascita di una sessione (startedAt di claude agents, in millisecondi) come data ISO:
    tiene il posto dell'ultima interazione quando la trascrizione manca o non si legge, così la
    sessione appena nata sta in cima all'elenco e non in fondo. Vuoto se manca anche quella."""
    t = s.get("startedAt")
    if isinstance(t, bool) or not isinstance(t, (int, float)) or t <= 0:
        return ""
    try:
        return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(t / 1000))
    except (OverflowError, OSError, ValueError):
        return ""


def righe(voci):
    """Da raccogli() all'elenco piatto: una riga per sessione."""
    out = []
    for v in voci:
        for s in v.get("sessioni") or []:
            sid = s.get("sessionId") or ""
            if not sid:
                continue
            fondo = s.get("kind") == "background"
            senza = fondo and not s.get("pid") and not s.get("status") and stato(s) != "errore"
            # claude attach, stop, logs e respawn vogliono l'id del lavoro in background, che resta
            # quello della nascita: dopo /clear o una rotazione il sessionId cambia e il suo inizio
            # non aggancia più ("No job matching"). Un'interattiva non ha lavoro: l'inizio del sessionId.
            lavoro = s.get("id") if fondo else None
            ospite = None if fondo else s.get("terminale")
            corto = lavoro if isinstance(lavoro, str) and re.fullmatch(r"[0-9A-Za-z-]{4,64}", lavoro) else sid[:8]
            out.append({
                "macchina": v["macchina"], "host": v["host"], "questa": v["questa"],
                "sessionId": sid, "id": corto, "nome": s.get("name") or corto,
                "progetto": s.get("progetto"), "titolo": s.get("titolo"), "sintesi": s.get("sintesi"), "stato": stato(s), "aspetta": s.get("waitingFor"),
                "tipo": "background" if fondo else "interattiva",
                # un'interattiva va prima portata in background, poi si aggancia
                "attach": argv_attach(v, corto) if fondo else None,
                # la scheda di Herdr che la ospita, se è partita lì dentro: il clic la porta davanti
                "terminale": ospite if isinstance(ospite, str) and re.fullmatch(r"t[0-9a-z]{1,12}", ospite) else None,
                "cartella": s.get("cwd"), "ultimo": s.get("ultimo") or nascita(s),
                "risposta": (s.get("risposta") or "")[:420], "azione": s.get("azione") or "",
                # le fasi di Volta (#5366): ultimo messaggio vero, fine dell'ultimo testo, chi ha parlato
                "interazione": s.get("interazione") or "", "coda": (s.get("coda") or "")[-300:],
                "chi": s.get("chi") or "", "fineFatta": s.get("fineFatta") is True,
                # ripresa da un congedo di Volta (/fine dopo ⌘W): la persona l'aveva chiusa
                "congedo": s.get("congedo") is True,
                "daPortare": s.get("daPortare") if isinstance(s.get("daPortare"), str) else None,
                "daIniziare": s.get("daIniziare") if isinstance(s.get("daIniziare"), str) else None,
                # In background senza processo e senza status ci sono due casi (#5495, 13/11/2026).
                # chiusa: fermata con claude stop ("stopped") o dopo /fine come ultimo messaggio, cioè
                # il congedo di ⌘W. Volta non la mostra più; una in errore resta, per Riavvia.
                # dorme: ritirata dal servizio di Claude (ferma da un'ora, 8 con Remote Control, 60 s
                # con poca memoria) o rimasta senza processo dopo un riavvio. Resta nell'elenco e nel
                # giro: claude attach la riprende. Spostata su un'altra macchina (volta_sposta.py): chiusa,
                # perché claude stop lascia "done" una sessione che aveva finito il turno (#5537).
                "chiusa": senza and (s.get("state") == "stopped" or s.get("fineFatta") is True or s.get("spostata") is True),
                "dorme": senza and not (s.get("state") == "stopped" or s.get("fineFatta") is True or s.get("spostata") is True),
            })
    return out


def documento(voci, precedente=None, adesso=None):
    """Il documento di Volta. Una macchina che non risponde tiene le righe dell'ultima lettura buona."""
    adesso = adesso or time.strftime("%Y-%m-%dT%H:%M:%S")
    sessioni = righe(voci)
    elenco = []
    for v in voci:
        voce = {"macchina": v["macchina"], "host": v["host"], "questa": v["questa"]}
        if isinstance(v.get("nascita"), dict):
            voce["nascita"] = v["nascita"]
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


def claude_per_hc_run(d):
    """Il claude da lanciare con hc run: il percorso intero che SERVIZIO ha trovato sulla macchina (#5560),
    perché sul Mac il terminale di herdr-core non ha ~/.local/bin nel PATH. Solo un percorso assoluto che
    finisce in claude o claude.exe; altrimenti "claude" nudo, come lo trova il PATH di Windows."""
    cl = d.get("claude")
    if isinstance(cl, str) and (cl.startswith("/") or re.match(r"[A-Za-z]:[\\/]", cl)) \
            and re.search(r"[\\/]claude(\.exe)?$", cl) and not re.search(r"[\x00-\x1f]", cl):
        return cl
    return "claude"


def servizio(nome):
    """Il servizio di Claude acceso su `nome` ("qui" o vuoto = questa macchina), con SERVIZIO (#5208).

    Su un'altra macchina gira con hc exec, python3 e poi python. Se la macchina risponde "hc-run"
    (Windows senza l'attività di servizio-claude.ps1, Mac senza il LaunchAgent), il servizio nasce in un terminale di herdr-core
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
                ultimo = errore_hc(testo.splitlines()[-1]) if testo else "rc %d" % rc
        return {"errore": ultimo}

    d = chiedi()
    if d.get("serve") == "hc-run":
        try:
            rc, out, err = lancia(hc() + ["run", "--on", nome, "--name", "servizio-claude", "--no-parent", "--rm",
                                          "--bg", claude_per_hc_run(d), "daemon", "run"],
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


def nasci(nome, prompt="", progetto=None, cartella=None, riprendi=None, titolo=None, stessa=False):
    """Una sessione nuova in background su `nome` ("qui" o vuoto = questa macchina).

    Duplica e Fork (#5291) passano da qui: `cartella` è quella della sessione di partenza, `riprendi`
    il sessionId di cui la nuova è una copia (fork), `titolo` il nome della copia in Claude Code.

    Su un'altra macchina prova python3, poi python; passa al secondo solo se il primo non è partito
    (spawn_failed, o 9009 dello stub dello Store su Windows): un Python partito può aver già fatto
    nascere la sessione, e ripetere ne farebbe due."""
    questa = nome in (None, "", "qui")
    if riprendi is not None and not ID.fullmatch(riprendi or ""):  # mai un'opzione come --all
        return {"errore": "id di sessione non valido"}
    dati = {"prompt": prompt or "", "progetto": progetto}
    dati.update({k: v for k, v in (("cartella", cartella), ("riprendi", riprendi), ("nome", titolo), ("stessa", stessa)) if v})
    arg = base64.b64encode(json.dumps(dati).encode()).decode()
    if questa:
        voce = {"questa": True, "target": None}
        tentativi = [[sys.executable, "-c", NASCI, arg]]
    else:
        note = macchine()
        if note is None:
            return {"errore": "Herdr non dice le macchine: riprova fra poco"}
        m = next((x for x in note if x["nome"] == nome), None)
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
        return {"errore": "il servizio di Claude non parte su %s: %s" % (chi(nome), s["errore"])}
    ultimo = "nessun Python"
    for argv in tentativi:
        try:
            rc, out, err = lancia(argv, timeout=ATTESA_NASCITA)
        except (OSError, subprocess.SubprocessError) as e:
            return {"errore": "%s non risponde: %s" % (chi(nome), str(e)[:160])}
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
    return {"errore": "non parte su %s: %s" % (chi(nome), ultimo)}


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
ID = re.compile(r"[0-9A-Za-z][0-9A-Za-z-]{3,63}")

# Gira sulla macchina della sessione quando hc exec non trova claude (#5555): sui Mac hc exec parte con
# un PATH senza ~/.local/bin, dove l'installatore mette claude. Lo cerca come SONDA e NASCI, lo lancia
# con gli stessi argomenti e ne passa uscita e codice d'uscita.
CLAUDE_FUORI_PATH = r'''
import os, shutil, subprocess, sys
fine = ".exe" if os.name == "nt" else ""
#CLAUDE#
cl = trova_claude()
if not os.path.exists(cl):
    sys.stderr.write("Claude Code non c'è su questa macchina\n"); raise SystemExit(127)
raise SystemExit(subprocess.call([cl] + sys.argv[1:], stdin=subprocess.DEVNULL))
'''
CLAUDE_FUORI_PATH = CLAUDE_FUORI_PATH.replace("#CLAUDE#", CERCA_CLAUDE.strip())


def claude_remoto(nome, args, entro):
    """claude con `args` su `nome` via hc exec, entro l'istante `entro`. Prima claude nudo, come lo trova
    il PATH di hc exec (Windows); se non parte, python3 e poi python con CLAUDE_FUORI_PATH (i Mac, #5555).
    Se non parte niente, resta l'errore di claude nudo, che dice cosa manca."""
    codice = "import base64;exec(base64.b64decode('%s'))" % base64.b64encode(CLAUDE_FUORI_PATH.encode()).decode()
    primo = None
    for prog in (["claude"], ["python3", "-c", codice], ["python", "-c", codice]):
        t = round(entro - time.monotonic())
        if t < 10:
            break
        rc, out, err = lancia(hc() + ["exec", "--on", nome, "--timeout", str(t - 5)] + prog + args, timeout=t)
        if rc != 0 and (rc == 9009 or non_parte(out, err)):  # il programma non è partito: il prossimo
            primo = primo or (rc, out, err)
            continue
        return rc, out, err
    return primo or (1, "", "nessuna risposta in %d s" % ATTESA_AZIONE)


def azione(nome, verbo, sid):
    """Un comando di claude su una sessione di `nome` ("qui" = questa macchina): logs (l'anteprima,
    come righe di schermo), stop, respawn, rm. Le altre macchine passano da herdr-core (hc exec --on).

    Riavvia (respawn) fa ripartire il processo della sessione, che nasce dal servizio di Claude: prima
    il servizio si accende dove sopravvive, come per nasci (#5215). Senza, claude respawn lo farebbe
    nascere a tempo dentro hc exec, e la sessione riavviata morirebbe con lui. Gli altri gesti non
    fanno nascere processi: non lo toccano."""
    if verbo not in VERBI:
        return {"errore": "azione sconosciuta: %s" % verbo}
    if not ID.fullmatch(sid or ""):  # mai un'opzione come --all
        return {"errore": "id di sessione non valido"}
    qui = nome in (None, "", "qui")
    if verbo == "respawn":
        s = servizio(nome)
        if s.get("errore"):
            return {"errore": "il servizio di Claude non parte su %s: %s" % (chi(nome), s["errore"])}
    try:
        if qui:
            rc, out, err = lancia([trova_claude(), verbo, sid], timeout=ATTESA_AZIONE)
        else:
            rc, out, err = claude_remoto(nome, [verbo, sid], time.monotonic() + ATTESA_AZIONE)
    except (OSError, subprocess.SubprocessError) as e:
        return {"errore": "%s non risponde: %s" % (chi(nome), str(e)[:160])}
    if rc != 0:
        testo = (err or out).strip()
        return {"errore": testo.splitlines()[-1][:200] if testo else "rc %d" % rc}
    if verbo == "logs":
        return {"righe": schermo(out)}
    testo = (out or err).strip()
    return {"ok": True, "testo": testo.splitlines()[-1][:200] if testo else ""}


# Il congedo (12/11/2026): chiudere una sessione da Volta vuol dire /fine e poi claude stop. Qui il primo
# tempo: claude stop (se gira ancora), poi la stessa conversazione ripresa in background col solo /fine.
# Il secondo stop lo chiede volta.js quando /fine ha finito il turno (passoCongedo di sessioni.js).
# Mai claude rm. "è partita, ma non ho letto il suo id" vale come ripresa: --resume non stampa l'aggancio.
# VOLTA_PROMPT_CONGEDO sostituisce il testo solo per le prove dal vivo, su una sessione usa e getta.
PROMPT_CONGEDO = os.environ.get("VOLTA_PROMPT_CONGEDO") or (
    "/fine congedo da Volta: la persona ha chiuso questa sessione. Niente rotazione, "
    "nessuna domanda e nessun menu: salva e chiudi.")
# La chiusura automatica (#5366): Volta chiude da sola una sessione ferma da più di un'ora, a turno
# finito e senza domande aperte. Lo stesso congedo, con il motivo vero nel testo di /fine.
PROMPT_CONGEDO_AUTO = os.environ.get("VOLTA_PROMPT_CONGEDO") or (
    "/fine congedo da Volta: la sessione era ferma da più di un'ora, a turno finito e senza domande. "
    "Niente rotazione, nessuna domanda e nessun menu: salva e chiudi.")


def congeda(nome, sid_lavoro, session_id, cartella=None, auto=False):
    if not ID.fullmatch(sid_lavoro or "") or not ID.fullmatch(session_id or ""):
        return {"errore": "id di sessione non valido"}
    fermata = azione(nome, "stop", sid_lavoro)  # una sessione già ferma risponde con un errore: si va avanti
    r = nasci(nome, PROMPT_CONGEDO_AUTO if auto else PROMPT_CONGEDO, None, cartella, riprendi=session_id, stessa=True)
    if r.get("errore") and not str(r["errore"]).startswith("è partita"):
        return {"errore": r["errore"], "fermata": bool(fermata.get("ok"))}
    return {"ok": True, "fermata": bool(fermata.get("ok"))}


def inizia(nome, sid_lavoro, session_id, slug, cartella=None):
    """Una sessione in background spostata in un altro progetto riparte da /inizio di quel progetto
    (#5465, Federico 12/11/2026). Come il congedo: claude stop, poi la stessa conversazione ripresa
    col solo /inizio. Volta lo chiede solo a sessione ferma e senza una scheda che la mostri: con la
    scheda aperta scrive /inizio lì dentro. Il progetto non passa a nasci, che riscriverebbe la scheda."""
    if not ID.fullmatch(sid_lavoro or "") or not ID.fullmatch(session_id or ""):
        return {"errore": "id di sessione non valido"}
    if not SLUG.fullmatch(slug or ""):
        return {"errore": "il progetto è uno slug: minuscole, numeri e trattini, al più 40 caratteri"}
    ferma = azione(nome, "stop", sid_lavoro)  # già ferma risponde con un errore: si va avanti
    r = nasci(nome, "/inizio %s" % slug, None, cartella, riprendi=session_id, stessa=True)
    if r.get("errore") and not str(r["errore"]).startswith("è partita"):
        return {"errore": r["errore"], "fermata": bool(ferma.get("ok"))}
    return {"ok": True, "fermata": bool(ferma.get("ok"))}


CAMBI = {"rinomina": "titolo", "progetto": "scheda"}
SLUG = re.compile(r"[a-z0-9][a-z0-9-]{0,39}")
NOME_LUNGO = 60


def nome_pulito(testo):
    """Il nome di una sessione come lo tiene un titolo: una riga, senza caratteri di controllo."""
    t = "".join(" " if ord(c) < 32 or 127 <= ord(c) < 160 else c for c in str(testo or ""))
    return re.sub(r"\s+", " ", t).strip()[:NOME_LUNGO].strip()


def cambia(nome, verbo, sid, valore="", portato=False):
    """Rinomina e Cambia progetto (#5292): il nome o il progetto di `sid` scritti sulla macchina `nome`
    ("qui" = questa), con SCRIVI. `sid` è il sessionId intero: i due file della cache portano quello.

    Su un'altra macchina prova python3, poi python: scrivere due volte lo stesso file non fa danni."""
    if verbo not in CAMBI:
        return {"errore": "cambio sconosciuto: %s" % verbo}
    if not ID.fullmatch(sid or ""):
        return {"errore": "id di sessione non valido"}
    if verbo == "progetto":
        if not SLUG.fullmatch(valore or ""):
            return {"errore": "il progetto è uno slug: minuscole, numeri e trattini, al più 40 caratteri"}
    else:
        valore = nome_pulito(valore)
    # `portato` vale per tutti e due: il nome che Claude Code ha già (/rename), il progetto da cui la
    # sessione è già ripartita (/inizio, #5465)
    segno = {"portato": bool(portato)} if verbo == "rinomina" else {"iniziato": bool(portato)}
    arg = base64.b64encode(json.dumps(dict({"cosa": CAMBI[verbo], "sessionId": sid, "valore": valore}, **segno)).encode()).decode()
    if nome in (None, "", "qui"):
        tentativi = [[sys.executable, "-c", SCRIVI, arg]]
    else:
        codice = "import base64;exec(base64.b64decode('%s'))" % base64.b64encode(SCRIVI.encode()).decode()
        tentativi = [hc() + ["exec", "--on", nome, "--timeout", str(ATTESA_AZIONE - 5), py, "-c", codice, arg]
                     for py in ("python3", "python")]
    ultimo = "nessun Python"
    for argv in tentativi:
        try:
            rc, out, err = lancia(argv, timeout=ATTESA_AZIONE)
        except (OSError, subprocess.SubprocessError) as e:
            return {"errore": "%s non risponde: %s" % (chi(nome), str(e)[:160])}
        if rc != 0 and (rc == 9009 or non_parte(out, err)):  # il Python non è partito: si prova l'altro
            continue
        try:
            return leggi_json(out)
        except ValueError:
            testo = (err or out).strip()
            ultimo = testo.splitlines()[-1][:200] if testo else "rc %d" % rc
    return {"errore": ultimo}


def main_cambia(verbo, argv):
    """rinomina MACCHINA SESSIONID [--portato] [-- NOME] e progetto MACCHINA SESSIONID [--iniziato] -- SLUG."""
    resto = argv[argv.index("--") + 1:] if "--" in argv else []
    testa = argv[:argv.index("--")] if "--" in argv else argv
    segno = "--portato" if verbo == "rinomina" else "--iniziato"
    portato = segno in testa
    testa = [a for a in testa if a != segno]
    if len(testa) != 2 or any(x.startswith("--") for x in testa) or (verbo == "progetto" and len(resto) != 1):
        print("uso: volta_sonda.py rinomina <macchina> <sessionId> [--portato] [-- <nome>]\n"
              "     volta_sonda.py progetto <macchina> <sessionId> [--iniziato] -- <slug>")
        return 2
    esito = cambia(testa[0], verbo, testa[1], " ".join(resto), portato)
    print(json.dumps(esito, ensure_ascii=True))
    return 0 if "errore" not in esito else 1


def apri(nome, sid, riavvia=False):
    """Prepara l'aggancio della sessione `sid` di `nome` ("qui" = questa macchina), prima di claude attach.

    claude attach riapre da solo una sessione finita o fermata (done, stopped), ma gli serve il servizio
    di Claude: senza, lo farebbe nascere a tempo, e da ssh morirebbe con la connessione lasciando nella
    scheda una shell vuota. Quindi qui il servizio si accende dove sopravvive, come per nasci. Con
    `riavvia` la sessione riparte prima con claude respawn (azione, che accende lei il servizio): serve
    dopo un errore (failed, crashed) e quando attach è uscito subito."""
    if ID.fullmatch(sid or "") is None:
        return {"errore": "id di sessione non valido"}
    if riavvia:
        r = azione(nome, "respawn", sid)
        if not r.get("ok"):
            return {"errore": "non si riavvia: %s" % (r.get("errore") or "nessuna risposta")}
        return {"ok": True, "riavviata": True}
    s = servizio(nome)
    if s.get("errore"):
        return {"errore": "il servizio di Claude non parte su %s: %s" % (chi(nome), s["errore"])}
    return {"ok": True, "riavviata": False, "servizio": s.get("come")}


# Le risposte JSON per Volta escono in ASCII (le accentate come è): su Windows lo stdout di Python è
# cp1252 e Volta lo legge come UTF-8, così un errore con un'accentata arrivava illeggibile (#5536).
def main_nasci(argv):
    resto = argv[argv.index("--") + 1:] if "--" in argv else []
    testa = argv[:argv.index("--")] if "--" in argv else argv
    if not testa:
        print(__doc__.strip())
        return 2
    progetto = testa[testa.index("--progetto") + 1] if "--progetto" in testa[:-1] else None
    esito = nasci(testa[0], " ".join(resto), progetto)
    print(json.dumps(esito, ensure_ascii=True))
    return 0 if "errore" not in esito else 1


COPIE = ("duplica", "fork")
OPZIONI_COPIA = ("--progetto", "--cartella", "--titolo")


def main_copia(verbo, argv):
    """duplica MACCHINA e fork MACCHINA SESSIONID, con --progetto, --cartella e --titolo. Duplica
    prende anche `-- PROMPT`: in un progetto Volta le passa /inizio (#5465)."""
    prompt = " ".join(argv[argv.index("--") + 1:]) if "--" in argv and verbo == "duplica" else ""
    argv = argv[:argv.index("--")] if "--" in argv else argv
    opz, resto, i = {}, [], 0
    while i < len(argv):
        if argv[i] in OPZIONI_COPIA and i + 1 < len(argv):
            opz[argv[i][2:]] = argv[i + 1]
            i += 2
        else:
            resto.append(argv[i])
            i += 1
    attesi = 2 if verbo == "fork" else 1
    if len(resto) != attesi or any(x.startswith("--") for x in resto):
        print("uso: volta_sonda.py %s <macchina>%s [--progetto <slug>] [--cartella <dir>]%s"
              % (verbo, " <sessionId>" if verbo == "fork" else "", " [--titolo <nome>]" if verbo == "fork" else " [-- <prompt>]"))
        return 2
    if verbo == "fork":
        esito = nasci(resto[0], "", opz.get("progetto"), opz.get("cartella"), resto[1], opz.get("titolo"))
    else:
        esito = nasci(resto[0], prompt, opz.get("progetto"), opz.get("cartella"))
    print(json.dumps(esito, ensure_ascii=True))
    return 0 if "errore" not in esito else 1


def main(argv):
    if argv and argv[0] == "sposta":
        # lo spostamento fra macchine sta in volta_sposta.py, accanto a questo file
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        import volta_sposta
        return volta_sposta.main(argv[1:])
    if argv and argv[0] == "nasci":
        return main_nasci(argv[1:])
    if argv and argv[0] in COPIE:
        return main_copia(argv[0], argv[1:])
    if argv and argv[0] in CAMBI:
        return main_cambia(argv[0], argv[1:])
    if argv and argv[0] == "servizio":
        if len(argv) != 2:
            print("uso: volta_sonda.py servizio <macchina>")
            return 2
        esito = servizio(argv[1])
        print(json.dumps(esito, ensure_ascii=True))
        return 0 if "errore" not in esito else 1
    if argv and argv[0] == "apri":
        resto = [a for a in argv[1:] if a != "--riavvia"]
        if len(resto) != 2:
            print("uso: volta_sonda.py apri <macchina> <id> [--riavvia]")
            return 2
        esito = apri(resto[0], resto[1], "--riavvia" in argv[1:])
        print(json.dumps(esito, ensure_ascii=True))
        return 0 if "errore" not in esito else 1
    if argv and argv[0] == "congeda":
        resto = argv[1:]
        cartella = resto[resto.index("--cartella") + 1] if "--cartella" in resto[:-1] else None
        resto = [a for i, a in enumerate(resto) if a != "--cartella" and (i == 0 or resto[i - 1] != "--cartella")]
        auto = "--auto" in resto
        resto = [a for a in resto if a != "--auto"]
        if len(resto) != 3:
            print("uso: volta_sonda.py congeda <macchina> <id> <sessionId> [--cartella <dir>] [--auto]")
            return 2
        esito = congeda(resto[0], resto[1], resto[2], cartella, auto)
        print(json.dumps(esito, ensure_ascii=True))
        return 0 if "errore" not in esito else 1
    if argv and argv[0] == "inizia":
        resto = argv[1:]
        cartella = resto[resto.index("--cartella") + 1] if "--cartella" in resto[:-1] else None
        resto = [a for i, a in enumerate(resto) if a != "--cartella" and (i == 0 or resto[i - 1] != "--cartella")]
        if len(resto) != 4:
            print("uso: volta_sonda.py inizia <macchina> <id> <sessionId> <progetto> [--cartella <dir>]")
            return 2
        esito = inizia(resto[0], resto[1], resto[2], resto[3], cartella)
        print(json.dumps(esito, ensure_ascii=True))
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
    if not isinstance(precedente, dict):
        precedente = None
    entro = time.monotonic() + attesa_lettura() - MARGINE_LETTURA
    with registro.Durata("giro") as dura:
        dati = documento(raccogli(gia_viste(precedente), (precedente or {}).get("macchine"), entro), precedente)
        giu = [m["macchina"] for m in dati["macchine"] if "irraggiungibile" in m]
        if giu:
            dura.esito, dura.errore = "parziale", "non rispondono: " + ", ".join(giu)
    if percorso:
        scrivi_atomico(percorso, dati)
        giu = [m["macchina"] for m in dati["macchine"] if "irraggiungibile" in m]
        print("volta: %d sessioni%s" % (len(dati["sessioni"]), (", non rispondono: " + ", ".join(giu)) if giu else ""))
    else:
        print(json.dumps(dati, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
