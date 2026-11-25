#!/usr/bin/env python3
"""I dati di transito della config su un ramo `sync`, fuori da `main` (revisione del 22/11/2026, D5, #6424).

Handoff, stati dei progetti, note e log di Melchior cambiano a ogni /fine e a ogni prompt. Su `main` facevano
176 commit al giorno e un merge driver per ogni file. Qui stanno in un secondo git dentro la stessa cartella:
`<config>/.git-sync`, con work tree `<config>`, ramo `sync`. I file restano dove li cercano hook e script.
Quali path passano di qui lo dice `data/transito.paths` (uno per riga, # commenta). Il perché e la
migrazione un computer alla volta: docs/ramo-sync.md.

Uso:
  sync_transito.py --giro        commit raggruppato dei path di transito, poi il push se è passato il minuto
  sync_transito.py --subito      come --giro: lo chiama la coda di /fine a fine corsa
  sync_transito.py --migra       crea .git-sync e il ramo sync (con --prova stampa soltanto, non scrive)
  sync_transito.py --stato       una riga: commit locali non spinti, ultimo push, lucchetto, blocco
  sync_transito.py --prima-del-pull [main]    prima del pull di main: commit dei path di transito e segno
                                              "pull in corso", che ferma i giri fino al passo dopo. Se il
                                              pull toglie path di transito cambiati qui, tornano alla copia
                                              di main: la nuova è nel ramo sync, e l'autostash non va in
                                              conflitto
  sync_transito.py --dopo-il-pull <sha>       dopo il pull di main (sha = HEAD di main prima del pull):
                                              ripristina i file che main ha smesso di tracciare, commit,
                                              fetch e rebase del ramo sync anche dentro il minuto

Un solo giro alla volta per macchina (lucchetto .git-sync/lock col pid) e al massimo un push al minuto
(.git-sync/ultimo-push). Un giro che trova il lucchetto occupato esce 0 senza fare niente; --subito aspetta
fino a SYNC_TRANSITO_ATTESA secondi (30) e, se il lucchetto resta preso, esce 8. Il push parte solo
se il remote è privato: con origin sul repository pubblico di Arturo, o senza origin, i commit restano locali.
Un giro senza commit nuovi né commit da spingere non tocca la rete.
Prima del commit la guardia dei segreti (hooks/commit-secret-gate.py) legge le righe nuove: una chiave trovata
ferma il giro (exit 7), e il file la nomina senza mostrare il valore. Più di 25 file cancellati in un giro
fermano il commit (exit 4): di solito è un pull di main fatto a mano, che toglie dal disco i path di transito.

Un conflitto nel rebase si risolve da solo (24/11/2026): una nota di data/memory tiene le righe di tutte e due le
versioni, un handoff e ogni altro file la versione scritta per ultimo. Un giro fermo da 10 minuti stampa una volta
la riga AVVISO col motivo: vale per le uscite 4, 6, 7 e 9 e per un rebase di main lasciato a metà (#6566). Un push
rifiutato (un pre-push che blocca, un remote che rifiuta) esce 9 e dice la riga BLOCK o error, non l'ultima (#6654). Un file
con le righe <<<<<<< e >>>>>>> fra le righe nuove non entra nel ramo (#5528).

Exit: 0 fatto o niente da fare (anche col rebase di main a metà, che conta come blocco) · 4 rebase a metà in
.git-sync, troppe cancellazioni o segni di conflitto in un file: il ramo sync resta com'era · 5 uso sbagliato
· 6 git add o commit falliti · 7 segreto nello stage, o guardia che non si carica · 8 solo con --subito: un
altro giro tiene il lucchetto oltre l'attesa, niente commit · 9 push rifiutato anche dopo il secondo rebase: i
commit restano locali, anche per un push andato in timeout. Un remote che non risponde a ls-remote o a fetch
esce 0: passa da solo.

Variabili per i banchi: SYNC_TRANSITO_CLAUDE (la radice), SYNC_TRANSITO_MINUTO (secondi fra due push, 60),
SYNC_TRANSITO_VISIBILITA (PRIVATE per saltare gh). SYNC_TRANSITO_CANCELLAZIONI_OK=1 lascia passare un giro
con più di 25 cancellazioni, dopo averle guardate.
"""
from __future__ import annotations

import argparse
import importlib.util
import os
import re
import signal
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

QUI = Path(__file__).resolve().parent
sys.path.append(str(QUI.parent / "hooks"))
from radici import radice_orsa  # noqa: E402

# Il bash del PATH: un "bash" senza percorso, su Windows, apre il bash.exe di WSL in System32 (#6455).
BASH_VERO = shutil.which("bash") or "bash"

CL = Path(os.environ.get("SYNC_TRANSITO_CLAUDE") or radice_orsa())
SYNC = CL / ".git-sync"
ELENCO = QUI.parent / "data" / "transito.paths"
GUARDIA = QUI.parent / "hooks" / "commit-secret-gate.py"
RAMO = "sync"
RE_ARTURO = re.compile(r"github\.com[:/]stellakamikaze/arturo(\.git)?/?$")
RE_FILE_DIFF = re.compile(r"^diff --git a/.* b/(.*)$", re.M)
RE_SEGNO_APRE = re.compile(r"^\+<<<<<<< ", re.M)
RE_SEGNO_CHIUDE = re.compile(r"^\+>>>>>>> ", re.M)
RE_ANSI = re.compile(r"\x1b\[[0-9;?]*[A-Za-z]")
# Le righe che dicono perché un push non passa, in ordine: il blocco di un hook, poi il rifiuto di git.
RE_MOTIVO_PUSH = (re.compile(r"\bBLOCK\b"),
                  re.compile(r"(?i)\[(remote )?rejected\]|^(error|fatal|remote: error):|hook declined"))
RE_SENSIBILE = re.compile(r"(?i)^(\.env(\..*)?|.*\.(env|key|pem|p12|pfx)|\.?credentials\.json|client_secret.*\.json"
                          r"|id_(rsa|ed25519|ecdsa|dsa))$")
CARTELLE_SENSIBILI = {"secrets", "credentials"}
RIGENERABILI = {".venv", "venv", "node_modules", "__pycache__"}
DIFF = ["--no-color", "--no-ext-diff", "--no-textconv", "--unified=0", "--no-renames"]
LUCCHETTO_VECCHIO = 600  # secondi: un giro dura pochi secondi, oltre è di un processo morto male
PULL_VECCHIO = 600  # un segno "pull in corso" più vecchio è di un pull morto a metà: i giri ripartono
TANTE_CANCELLAZIONI = 25
_OCCUPATO = (FileExistsError, PermissionError) if os.name == "nt" else (FileExistsError,)
OCCUPATO = 8  # --subito: un altro giro tiene il lucchetto oltre l'attesa, niente commit
PUSH_RIFIUTATO = 9  # il push non passa anche dopo il secondo rebase: i commit restano locali


def run(cmd, timeout=120, env=None, cwd=None):
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace",
                           timeout=timeout, env=env, cwd=cwd)
        return p.returncode, p.stdout, p.stderr
    except subprocess.TimeoutExpired:
        return None, "", f"timeout dopo {timeout} s"
    except OSError as e:
        return None, "", str(e)


def git(*a, timeout=120):
    """Il git del ramo sync, dalla radice della config. Con --work-tree e la cartella corrente in una sua
    sottocartella, git legge i path relativi a quella: la coda di /fine lanciata da data/handoffs falliva con
    "git add: data/handoffs/INDEX.md non corrisponde ad alcun file" (segnalazione n. 101, 24/11/2026)."""
    return run(["git", f"--git-dir={SYNC}", f"--work-tree={CL}", *a], timeout, cwd=str(CL))


def git_main(*a, timeout=60):
    return run(["git", "-C", str(CL), *a], timeout)


def ultima(*testi):
    righe = [r.strip() for t in testi for r in (t or "").replace("\x00", "").splitlines() if r.strip()]
    return righe[-1][:160] if righe else "nessun messaggio"


def motivo_push(err, out):
    """La riga che dice perché il push non passa. Il pre-push della config stampa su stdout la riga INF di gitleaks
    e su stderr la riga BLOCK: ultima() prendeva la INF, e il 25/11/2026 il log ha detto "no leaks found" per due
    ore mentre il pre-push bloccava ogni push (#6654). I colori di gitleaks si tolgono."""
    righe = [RE_ANSI.sub("", r).strip() for t in (err, out) for r in (t or "").replace("\x00", "").splitlines()]
    righe = [r for r in righe if r]
    for regola in RE_MOTIVO_PUSH:
        for r in righe:
            if regola.search(r):
                return r[:160]
    return ultima("\n".join(righe))


def percorsi():
    """I path di transito, relativi alla config."""
    try:
        righe = ELENCO.read_text(encoding="utf-8").splitlines()
    except OSError:
        return []
    return [r.strip().rstrip("/") for r in righe if r.strip() and not r.strip().startswith("#")]


def escluso(rel):
    """Fuori dal ramo sync anche se sta sotto un path di transito: lucchetti, copie di sicurezza, sensibili."""
    parti = rel.split("/")
    nome = parti[-1]
    if nome.endswith(".lock") or ".bak-" in nome or ".git" in parti:
        return True
    if RE_SENSIBILE.match(nome) or any(x in CARTELLE_SENSIBILI for x in parti[:-1]):
        return True
    return nome.endswith(".pyc") or any(x in RIGENERABILI for x in parti[:-1])


def collegamenti():
    """I path che main tiene come collegamenti simbolici (modo 120000). Su Windows Git li scrive come file di
    testo col nome della destinazione: dentro il ramo sync diventerebbero file veri, e sul Mac il rebase si
    fermerebbe sul collegamento vero ("impossibile scollegare l'HEAD", una macchina Windows, 24/11/2026)."""
    out = git_main("ls-files", "-s", "-z", "--", *percorsi())[1]
    return {r.split("\t", 1)[1] for r in out.split("\0") if r.startswith("120000 ") and "\t" in r}


def file_di_transito():
    """I file su disco sotto i path di transito, senza gli esclusi e senza i collegamenti simbolici."""
    out = []
    for p in percorsi():
        pieno = CL / p
        if pieno.is_file():
            out.append(p)
            continue
        for cartella, dirs, nomi in os.walk(pieno):
            dirs[:] = [d for d in dirs if d != ".git" and d not in RIGENERABILI]
            base = Path(cartella).relative_to(CL).as_posix()
            out += [f"{base}/{n}" for n in nomi]
    link = collegamenti()
    return [x for x in dict.fromkeys(out) if not escluso(x) and x not in link and not (CL / x).is_symlink()]


def origine():
    """(url, spingibile, perché non). Spingibile solo con un origin privato che non è il repository di Arturo."""
    url = git_main("remote", "get-url", "origin")[1].strip()
    if not url:
        return "", False, "nessun remote origin"
    if RE_ARTURO.search(url):
        return url, False, "origin è il repository pubblico di Arturo"
    forzata = os.environ.get("SYNC_TRANSITO_VISIBILITA")
    if forzata is not None:
        return url, forzata == "PRIVATE", f"visibilità {forzata or 'sconosciuta'}"
    # gh a ogni minuto sarebbe troppo: la risposta vale un giorno
    cache = SYNC / "visibilita"
    try:
        if time.time() - cache.stat().st_mtime < 86400:
            vis, _, chi = cache.read_text(encoding="utf-8").partition(" ")
            if chi.strip() == url:
                return url, vis == "PRIVATE", f"visibilità {vis or 'sconosciuta'}"
    except OSError:
        pass
    rc, out, _ = run([BASH_VERO, "-c", 'gh repo view "$1" --json visibility -q .visibility', "gh", url], 30)
    vis = out.strip() if rc == 0 else ""
    if vis:
        try:
            cache.write_text(f"{vis} {url}\n", encoding="utf-8")
        except OSError:
            pass
    return url, vis == "PRIVATE", f"visibilità {vis or 'sconosciuta'}"


def prepara():
    """Il git dir del ramo sync, creato se manca. True se l'ha creato adesso."""
    nuovo = not (SYNC / "HEAD").exists()
    if nuovo:
        rc, out, err = run(["git", f"--git-dir={SYNC}", "init", "-q", "-b", RAMO], 60)
        if rc != 0:
            raise RuntimeError(f"git init fallito: {ultima(err, out)}")
    # main non deve vedere il git dir del ramo sync come cartella nuova: lo dice .git/info/exclude, che non si versiona
    esclusione = CL / ".git" / "info" / "exclude"
    try:
        testo = esclusione.read_text(encoding="utf-8") if esclusione.exists() else ""
        if "/.git-sync/" not in testo.splitlines():
            esclusione.parent.mkdir(parents=True, exist_ok=True)
            esclusione.write_text(testo + ("" if not testo or testo.endswith("\n") else "\n") + "/.git-sync/\n",
                                  encoding="utf-8")
    except OSError:
        pass
    git("config", "core.bare", "false")
    # I fine riga seguono main: il work tree è lo stesso, scritto dal checkout di main. Su Windows Git mette
    # core.autocrlf=true nella config di sistema e i file stanno su disco in CRLF; con false qui il ramo sync
    # vedeva cambiato ogni file e li avrebbe spinti tutti in CRLF alle altre macchine (una macchina Windows, 24/11/2026).
    crlf = git_main("config", "--get", "core.autocrlf")[1].strip()
    if crlf:
        git("config", "core.autocrlf", crlf)
    else:
        git("config", "--unset", "core.autocrlf")
    git("config", "status.showUntrackedFiles", "no")
    # La config di main può portare un .gitignore con questi stessi path: il ramo sync li aggiunge con -f e
    # non legge altre regole, così non finisce dentro niente che il passo di transito non abbia scelto.
    git("config", "core.excludesFile", os.devnull)
    url = git_main("remote", "get-url", "origin")[1].strip()
    if url:
        if git("remote", "get-url", "origin")[0] == 0:
            git("remote", "set-url", "origin", url)
        else:
            git("remote", "add", "origin", url)
    for chiave in ("user.name", "user.email", "merge.stati.name", "merge.stati.driver"):
        v = git_main("config", "--get", chiave)[1].strip()
        if v:
            git("config", chiave, v)
    return nuovo


# --- lucchetto ---------------------------------------------------------------------------------------------

def file_lucchetto():
    return SYNC / "lock"


def _viva_windows(pid: int) -> bool:
    """Come in fine-coda.py: su Windows os.kill(pid, 0) manda un Ctrl+C, e prima un lucchetto di un giro
    morto restava valido per sempre (ST04, sonda #6455)."""
    import ctypes
    from ctypes import wintypes
    k = ctypes.WinDLL("kernel32", use_last_error=True)
    k.OpenProcess.argtypes = (wintypes.DWORD, wintypes.BOOL, wintypes.DWORD)
    k.OpenProcess.restype = wintypes.HANDLE
    k.GetExitCodeProcess.argtypes = (wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD))
    k.CloseHandle.argtypes = (wintypes.HANDLE,)
    h = k.OpenProcess(0x1000, False, pid)  # PROCESS_QUERY_LIMITED_INFORMATION
    if not h:
        return ctypes.get_last_error() == 5  # accesso negato: il processo c'è
    try:
        codice = wintypes.DWORD()
        if not k.GetExitCodeProcess(h, ctypes.byref(codice)):
            return True
        return codice.value == 259  # STILL_ACTIVE
    finally:
        k.CloseHandle(h)


def viva(pid):
    try:
        pid = int(pid)
    except (ValueError, TypeError):
        return False
    if os.name == "nt":
        return _viva_windows(pid)
    try:
        os.kill(pid, 0)
        return True
    except (ValueError, ProcessLookupError):
        return False
    except PermissionError:
        return True


def prendi_lucchetto():
    """Il lucchetto, o None se un altro giro lo tiene. Non aspetta: il giro dopo (un minuto) riprova."""
    file = file_lucchetto()
    for _ in range(2):
        try:
            fd = os.open(str(file), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.write(fd, f"{os.getpid()}\n".encode("ascii"))
            os.close(fd)
            return file
        except _OCCUPATO:
            pass
        try:
            eta = time.time() - file.stat().st_mtime
            pid = (file.read_text(encoding="ascii", errors="replace").split() or [""])[0]
        except FileNotFoundError:
            continue
        except OSError:
            return None
        if eta > LUCCHETTO_VECCHIO or (pid.isdigit() and not viva(pid)):
            try:
                file.unlink()
            except OSError:
                return None
            continue
        return None
    return None


def lascia_lucchetto(file):
    try:
        if file.read_text(encoding="ascii", errors="replace").split()[:1] == [str(os.getpid())]:
            file.unlink()
    except (OSError, IndexError):
        pass


# --- segreti -----------------------------------------------------------------------------------------------

def guardia_segreti():
    allarme = getattr(signal, "SIGALRM", None)
    prima = signal.getsignal(allarme) if allarme else None
    try:
        spec = importlib.util.spec_from_file_location("arturo_commit_secret_gate_sync", GUARDIA)
        modulo = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(modulo)
        return modulo if callable(getattr(modulo, "_trovati", None)) and callable(getattr(modulo, "_aggiunte", None)) \
            else None
    except Exception:  # noqa: BLE001 - una guardia che non si carica ferma il giro, non lo rompe
        return None
    finally:
        if allarme:
            signal.signal(allarme, prima)


def segreti(guardia, argomenti):
    """None se pulito, altrimenti le righe che fermano il giro. Mai il valore."""
    if guardia is None:
        return [f"SEGRETI: STOP, nessun commit. La guardia dei segreti ({GUARDIA}) non si carica."]
    rc, out, err = git(*argomenti)
    if rc != 0:
        return [f"SEGRETI: STOP, nessun commit. git non dà il diff: {ultima(err, out)}"]
    trovati = {}
    inizi = list(RE_FILE_DIFF.finditer(out))
    for i, m in enumerate(inizi):
        pezzo = out[m.end():inizi[i + 1].start() if i + 1 < len(inizi) else len(out)]
        for nome in guardia._trovati(guardia._aggiunte(pezzo)):
            trovati.setdefault(m.group(1), {})[nome] = None
    if not trovati:
        return None
    righe = ["SEGRETO: STOP, nessun commit. La guardia dei segreti trova nelle righe nuove:"]
    righe += [f"  {f}: {', '.join(n)}" for f, n in list(trovati.items())[:10]]
    return righe + ["Togli la chiave dal file (va nel vault o in una variabile d'ambiente), poi rilancia."]


# --- giro --------------------------------------------------------------------------------------------------

def git_con_elenco(comando, paths):
    """git <comando> con i path da un file, non nella riga di comando: su Windows la riga si ferma a 32.767
    caratteri, e mille note fanno WinError 206 (una macchina Windows, 24/11/2026)."""
    elenco = SYNC / "elenco-path"
    elenco.write_bytes(b"".join(p.encode("utf-8") + b"\0" for p in paths))
    try:
        return git(*comando, f"--pathspec-from-file={elenco}", "--pathspec-file-nul")
    finally:
        elenco.unlink(missing_ok=True)


def a_meta():
    return any((SYNC / n).is_dir() for n in ("rebase-merge", "rebase-apply"))


def aggiungi():
    """Mette in stage i file di transito: -f perché il .gitignore di main li nomina, e i cancellati con -u."""
    elenco = file_di_transito()
    if elenco:
        rc, out, err = git_con_elenco(("add", "-f", "-A"), elenco)
        if rc != 0:
            return False, ultima(err, out)
    tracciati = [p for p in percorsi() if git("ls-files", "--", p)[1].strip()]
    if tracciati:
        rc, out, err = git("add", "-u", "--", *tracciati)
        if rc != 0:
            return False, ultima(err, out)
    # Un file diventato escluso (un lucchetto, una chiave) non deve restare nel ramo: fuori dall'indice, non dal disco.
    link = collegamenti()
    for x in git("ls-files", "-z")[1].split("\0"):
        if x and (escluso(x) or x in link):
            git("rm", "-q", "--cached", "--", x)
    return True, ""


def segni_di_conflitto():
    """I file in stage con le righe <<<<<<< e >>>>>>> fra le righe nuove: un merge fermo a metà le ha lasciate sul
    disco (stati.json il 12 e il 13/11/2026, #5528). Servono tutte e due: una riga ======= da sola è un titolo
    Markdown."""
    rc, out, _ = git("diff", "--cached", *DIFF)
    if rc != 0:
        return []
    segnati = []
    inizi = list(RE_FILE_DIFF.finditer(out))
    for i, m in enumerate(inizi):
        pezzo = out[m.end():inizi[i + 1].start() if i + 1 < len(inizi) else len(out)]
        if RE_SEGNO_APRE.search(pezzo) and RE_SEGNO_CHIUDE.search(pezzo):
            segnati.append(m.group(1))
    return segnati


def commit(guardia, esiti):
    """0 fatto (o niente), 4 troppe cancellazioni o segni di conflitto, 6 commit fallito, 7 segreto."""
    ok, err = aggiungi()
    if not ok:
        esiti.append(f"git add fallito: {err}")
        return 6
    staged = [p for p in git("diff", "--cached", "--name-only", "--no-renames", "-z")[1].split("\0") if p]
    if not staged:
        esiti.append("niente da committare")
        return 0
    tolti = [p for p in git("diff", "--cached", "--name-only", "--no-renames", "--diff-filter=D", "-z")[1]
             .split("\0") if p]
    if len(tolti) > TANTE_CANCELLAZIONI and os.environ.get("SYNC_TRANSITO_CANCELLAZIONI_OK") != "1":
        # Un pull di main fatto a mano, dopo il commit che toglie i path di transito da main, li cancella dal
        # disco: spinte sul ramo sync, quelle cancellazioni toglierebbero i file a tutte le macchine.
        git("reset", "-q")
        esiti.append(f"STOP, {len(tolti)} file cancellati dal disco (fra cui {tolti[0]}): niente commit. "
                     f"Se le cancellazioni sono volute, rilancia con SYNC_TRANSITO_CANCELLAZIONI_OK=1; se no "
                     f"python3 bin/sync_transito.py --dopo-il-pull <HEAD di main prima del pull> li ripristina")
        return 4
    segnati = segni_di_conflitto()
    if segnati:
        # Spinto, il file rotto arriverebbe a tutte le macchine: stati.json non si leggerebbe più come JSON.
        git("reset", "-q")
        esiti.append(f"STOP, segni di conflitto <<<<<<< >>>>>>> in {', '.join(segnati[:3])}: niente commit. "
                     f"Togli i segni dal file e tieni le righe giuste: il giro dopo riparte da solo")
        return 4
    ferma = segreti(guardia, ("diff", "--cached", *DIFF))
    if ferma:
        print("\n".join(ferma))
        # Lo stage si svuota: il giro dopo rilegge tutto, e una chiave tolta dal file non resta in coda.
        git("reset", "-q")
        return 7
    memoria = [p for p in staged if p.startswith("data/memory/") and ".melchior" not in p]
    resto = [p for p in staged if p not in memoria]
    ora = time.strftime("%Y-%m-%d %H:%M")
    for paths, msg in ((memoria, "memoria: applicata da /fine"), (resto, f"sync: dati di transito {ora}")):
        if not paths:
            continue
        # Dall'indice con un pathspec: git riprende dal disco solo questi file, e "git commit -- <path>" li
        # prende interi. Il commit della memoria va prima e porta solo i suoi path.
        rc, out, err = git_con_elenco(("commit", "-q", "-m", msg, "--only"), paths) if memoria and resto else \
            git("commit", "-q", "-m", msg)
        if rc != 0:
            esiti.append(f"commit fallito: {ultima(err, out)}")
            return 6
        esiti.append(f"commit {git('rev-parse', '--short', 'HEAD')[1].strip()} ({len(paths)} file)")
    return 0


def piu_nuovo(rel):
    """Nel rebase "ours" (stadio 2) è origin/sync, "theirs" (stadio 3) il commit locale che si riapplica. Vince
    quello scritto per ultimo: conta la data d'autore, che il rebase non cambia. A pari data vince il locale."""
    mio = git("log", "-1", "--format=%at", "REBASE_HEAD")[1].strip()
    loro = git("log", "-1", "--format=%at", "HEAD", "--", rel)[1].strip()
    try:
        return 2 if int(loro) > int(mio) else 3
    except ValueError:
        return 3


def unione_righe(base, a, b):
    """Le righe di tutte e due le versioni (git merge-file --union), o None se git non le sa unire (binari)."""
    with tempfile.TemporaryDirectory(prefix="sync-rebase-") as d:
        fo, fa, fb = (Path(d) / n for n in ("base", "a", "b"))
        fo.write_bytes(base or b"")
        fa.write_bytes(a)
        fb.write_bytes(b)
        p = subprocess.run(["git", "merge-file", "-q", "--union", str(fa), str(fo), str(fb)],
                           capture_output=True, timeout=60)
        return fa.read_bytes() if p.returncode >= 0 else None


def risolvi(rel):
    """Un file in conflitto nel rebase, senza persona davanti (24/11/2026, scelta di chi mantiene Arturo). Una nota di
    data/memory tiene le righe di tutte e due le versioni, e qualche riga può uscire doppia; se una versione l'ha
    cancellata e l'altra cambiata, resta la cambiata. Un handoff, e ogni altro file, prende la versione scritta per
    ultimo. La versione che perde resta nella storia del ramo. (ok, come)."""
    stadi = {n: blob([f"--git-dir={SYNC}"], f":{n}:{rel}") for n in (1, 2, 3)}
    unito = None
    if rel.startswith("data/memory/"):
        if stadi[2] is not None and stadi[3] is not None:
            unito = unione_righe(stadi[1], stadi[2], stadi[3])
            come = "righe unite"
        else:
            unito = stadi[2] if stadi[2] is not None else stadi[3]
            come = "tenuta la versione cambiata"
    if unito is None:
        unito = stadi[piu_nuovo(rel)]
        come = "tenuta la più recente"
    pieno = CL / rel
    if unito is None:
        pieno.unlink(missing_ok=True)
        return git("rm", "-q", "--cached", "--ignore-unmatch", "--", rel)[0] == 0, "cancellato"
    pieno.parent.mkdir(parents=True, exist_ok=True)
    pieno.write_bytes(unito)
    return git("add", "-f", "--", rel)[0] == 0, come


def fai_rebase():
    """Il ramo locale sopra origin/sync. (ok, nota). Un conflitto si risolve da solo con risolvi(): prima il giro
    si fermava per sempre, e il 24/11/2026 il Mac ha tenuto fermi 20 commit. Se il rebase si ferma per altro, o
    un file non si risolve, torna com'era."""
    rc, out, err = git("rebase", f"origin/{RAMO}", timeout=180)
    risolti = []
    for _ in range(500):
        if rc == 0 or not a_meta():
            break
        conflitti = [p for p in git("diff", "--name-only", "--diff-filter=U", "-z")[1].split("\0") if p]
        if not conflitti:
            break
        for rel in conflitti:
            ok, come = risolvi(rel)
            if not ok:
                break
            risolti.append(f"{rel} ({come})")
        else:
            # Un commit che dopo la scelta non cambia più niente si salta: --continue lo rifiuterebbe.
            passo = "--skip" if git("diff", "--cached", "--quiet", "HEAD")[0] == 0 else "--continue"
            rc, out, err = git("-c", "core.editor=true", "rebase", passo, timeout=180)
            continue
        break
    if rc == 0 and not a_meta():
        if not risolti:
            return True, ""
        return True, f"{len(risolti)} conflitti risolti da soli: " + ", ".join(risolti[:3]) + \
            (" e altri" if len(risolti) > 3 else "")
    git("rebase", "--abort")
    return False, f"conflitto nel rebase su origin/{RAMO}: {ultima(err, out)}"


def push(esiti):
    """Fetch, rebase se serve, push. Il minuto fra due push lo controlla il chiamante."""
    if git("rev-parse", "--verify", "-q", "HEAD")[0] != 0:
        esiti.append("niente da spingere (ancora nessun commit)")
        return 0
    # ls-remote dice se il ramo c'è senza leggere i messaggi di git, che cambiano con la lingua: 0 c'è, 2 non c'è
    rc, out, err = git("ls-remote", "--exit-code", "--heads", "origin", RAMO, timeout=60)
    if rc not in (0, 2):
        esiti.append(f"remote non raggiunto: {ultima(err, out)}")
        return 0
    if rc == 0:
        rc, out, err = git("fetch", "-q", "origin", RAMO, timeout=90)
        if rc != 0:
            esiti.append(f"fetch non riuscito: {ultima(err, out)}")
            return 0
        if git("merge-base", "--is-ancestor", f"origin/{RAMO}", "HEAD")[0] != 0:
            ok, perche = fai_rebase()
            if perche:
                esiti.append(perche)
            if not ok:
                return 4
    rc, out, err = git("push", "-q", "origin", f"HEAD:{RAMO}", timeout=90)
    if rc != 0:
        # Un altro processo ha spinto fra il fetch e il push: un secondo giro di rebase.
        git("fetch", "-q", "origin", RAMO, timeout=90)
        ok, perche = fai_rebase()
        if perche:
            esiti.append(perche)
        if not ok:
            return 4
        rc, out, err = git("push", "-q", "origin", f"HEAD:{RAMO}", timeout=90)
        if rc != 0:
            # Prima usciva 0: il giro fermo non contava come blocco e l'AVVISO dei 10 minuti non scattava (#6654).
            global _FERMO
            _FERMO = f"push rifiutato: {motivo_push(err, out)}"
            esiti.append(_FERMO)
            return PUSH_RIFIUTATO
    try:
        (SYNC / "ultimo-push").write_text(f"{time.time()}\n", encoding="utf-8")
    except OSError:
        pass
    segna_fetch()  # il push ha appena fatto fetch e rebase: l'entrata riparte da qui
    esiti.append("push riuscito")
    return 0


def segna_fetch():
    try:
        (SYNC / "ultimo-fetch").write_text(f"{time.time()}\n", encoding="utf-8")
    except OSError:
        pass


def secondi_dall_ultimo_fetch():
    try:
        return time.time() - float((SYNC / "ultimo-fetch").read_text(encoding="utf-8").split()[0])
    except (OSError, ValueError, IndexError):
        return 1e9


def entrata(esiti):
    """I dati delle altre macchine, anche senza niente da spingere (24/11/2026): ogni SYNC_TRANSITO_ENTRATA
    secondi (300) un fetch e un rebase del ramo sync. Prima arrivavano solo col push di questa macchina o col
    pull della config, e una macchina ferma restava indietro. Un giro dentro i 5 minuti non tocca la rete."""
    if secondi_dall_ultimo_fetch() < float(os.environ.get("SYNC_TRANSITO_ENTRATA") or 300):
        return 0
    suoi = []
    rc = aggiorna(suoi)
    segna_fetch()
    esiti += [e for e in suoi if "già allineato" not in e and "non ancora su origin" not in e]
    return rc


def secondi_dall_ultimo_push():
    try:
        return time.time() - float((SYNC / "ultimo-push").read_text(encoding="utf-8").split()[0])
    except (OSError, ValueError, IndexError):
        return 1e9


def segno_pull():
    return SYNC / "pull-in-corso"


def pull_in_corso():
    try:
        return time.time() - segno_pull().stat().st_mtime < PULL_VECCHIO
    except OSError:
        return False


def migrato():
    if not (CL / ".git").exists() or not percorsi():
        print("sync: config senza git o nessun path di transito: niente da fare")
        return False
    if not (SYNC / "HEAD").exists():
        print("sync: il ramo sync non c'è su questa macchina (python3 bin/sync_transito.py --migra): niente da fare")
        return False
    return True


def aspetta_lucchetto(secondi=30):
    """Il lucchetto per il pull, che non può rimandare al minuto dopo: aspetta che il giro in corso finisca."""
    fine = time.time() + secondi
    while True:
        lucchetto = prendi_lucchetto()
        if lucchetto is not None or time.time() > fine:
            return lucchetto
        time.sleep(0.5)


BLOCCO_AVVISO = 600  # secondi di giri fermi prima della riga AVVISO
# Le uscite che non passano da sole: il giro dopo trova la stessa cosa (24/11/2026, #6566).
MOTIVI = {4: "rebase, segni di conflitto o troppe cancellazioni", 6: "git add o commit falliti",
          7: "una chiave nei file da salvare", PUSH_RIFIUTATO: "push rifiutato"}
MAIN_A_META = "un rebase di main lasciato a metà"
_GIRO_FATTO = False
_FERMO = ""


def segna_blocco(rc, motivo=""):
    """Da quando il giro è fermo (exit 4, 6, 7 o 9, oppure un rebase di main a metà, che esce 0 per non fermare la
    coda di /fine): .git-sync/bloccato-dal tiene l'ora del primo giro fermo. Oltre BLOCCO_AVVISO stampa una volta
    sola la riga AVVISO, col motivo, che la config gira alla persona. Il primo giro riuscito toglie il segno."""
    f = SYNC / "bloccato-dal"
    motivo = motivo or MOTIVI.get(rc, "")
    if not motivo:
        if rc == 0:
            f.unlink(missing_ok=True)
        return
    try:
        parti = f.read_text(encoding="utf-8").split()
        dal, avvisato = float(parti[0]), len(parti) > 1
    except (OSError, ValueError, IndexError):
        dal, avvisato = time.time(), False
    minuti = int((time.time() - dal) // 60)
    if minuti >= 1:
        print(f"sync: bloccato da {minuti} minuti")
    if time.time() - dal >= BLOCCO_AVVISO and not avvisato:
        print(f"AVVISO: il ramo sync di questa macchina è fermo da {minuti} minuti ({motivo}) e le note non "
              f"partono. Guarda data/logs/sync-transito.log.")
        avvisato = True
    try:
        f.write_text(f"{dal}{' avvisato' if avvisato else ''}\n", encoding="utf-8")
    except OSError:
        pass


def giro(subito=False):
    global _GIRO_FATTO, _FERMO
    _GIRO_FATTO, _FERMO = False, ""
    rc = _giro(subito)
    if _GIRO_FATTO or _FERMO:
        segna_blocco(rc, _FERMO)
    return rc


def _giro(subito=False):
    global _GIRO_FATTO, _FERMO
    if not migrato():
        return 0
    if pull_in_corso():
        # Fra il pull di main e il ripristino i path di transito possono mancare dal disco: un giro adesso
        # committerebbe le loro cancellazioni. Il segno lo toglie --dopo-il-pull.
        print("sync: pull della config in corso, riprovo al prossimo minuto")
        return 0
    if any((CL / ".git" / n).is_dir() for n in ("rebase-merge", "rebase-apply")):
        # Lo stesso rischio, ma un rebase di main a metà non si chiude da solo: conta come blocco, e dopo 10
        # minuti arriva l'AVVISO. Esce 0 lo stesso, perché la coda di /fine non si fermi.
        print("sync: rebase di main a metà, riprovo al prossimo minuto")
        _FERMO = MAIN_A_META
        return 0
    if subito:
        # La coda di /fine non ha un minuto dopo: aspetta il giro in corso, e se non finisce lo dice con un'uscita
        # diversa da 0. Prima usciva 0 e la coda chiudeva con handoff e note fuori dal ramo (segnalazione n. 102).
        attesa = float(os.environ.get("SYNC_TRANSITO_ATTESA") or 30)
        lucchetto = aspetta_lucchetto(attesa)
        if lucchetto is None:
            print(f"sync: un altro giro tiene il lucchetto da oltre {int(attesa)} s: handoff e note di questa /fine "
                  "NON sono sul ramo sync. Li prende il giro del prossimo minuto, o rilancia la coda.")
            return OCCUPATO
    else:
        lucchetto = prendi_lucchetto()
    if lucchetto is None:
        print("sync: un altro giro tiene il lucchetto, riprovo al prossimo minuto")
        return 0
    _GIRO_FATTO = True
    esiti = []
    try:
        prepara()
        if a_meta():
            print("sync: STOP, rebase a metà in .git-sync. Guarda con git --git-dir=.git-sync status.")
            return 4
        rc = commit(guardia_segreti(), esiti)
        if rc:
            print("sync: " + " · ".join(esiti))
            return rc
        url, spingibile, perche = origine()
        avanti = git("rev-list", "--count", f"origin/{RAMO}..HEAD")[1].strip() \
            if git("rev-parse", "--verify", "-q", f"origin/{RAMO}")[0] == 0 else str(
                git("rev-list", "--count", "HEAD")[1].strip() or 0)
        if not spingibile:
            esiti.append(f"solo locale ({perche})")
        elif avanti in ("", "0") and git("rev-parse", "--verify", "-q", f"origin/{RAMO}")[0] == 0:
            pass  # niente di nuovo da spingere: il giro non tocca la rete
        elif secondi_dall_ultimo_push() < float(os.environ.get("SYNC_TRANSITO_MINUTO") or 60) \
                and avanti not in ("", "0"):
            esiti.append("push al prossimo minuto")
        else:
            rc = push(esiti)
            if rc:
                print("sync: " + " · ".join(esiti))
                return rc
        if spingibile and git("rev-list", "--count", f"origin/{RAMO}..HEAD")[1].strip() in ("", "0"):
            rc = entrata(esiti)
            if rc:
                print("sync: " + " · ".join(esiti))
                return rc
        print("sync: " + " · ".join(esiti))
        return 0
    finally:
        lascia_lucchetto(lucchetto)


# --- pull della config -------------------------------------------------------------------------------------

def prima_del_pull(ramo_main="main"):
    """Prima del pull di main: il segno che ferma i giri e il commit di ciò che c'è su disco, così il ramo sync
    ha l'ultima copia dei file anche se il pull li toglie."""
    if not migrato():
        return 0
    try:
        segno_pull().write_text(f"{os.getpid()} {time.time()}\n", encoding="utf-8")
    except OSError as e:
        print(f"sync: segno del pull non scritto ({e}): niente commit prima del pull")
        return 6
    lucchetto = aspetta_lucchetto()
    if lucchetto is None:
        print("sync: il lucchetto resta preso da un altro giro: niente commit prima del pull")
        return 0
    esiti = []
    try:
        prepara()
        if a_meta():
            print("sync: STOP, rebase a metà in .git-sync. Guarda con git --git-dir=.git-sync status.")
            return 4
        rc = commit(guardia_segreti(), esiti)
        if rc == 0:
            libera_per_il_pull(ramo_main, esiti)
        print("sync prima del pull: " + " · ".join(esiti))
        return rc
    finally:
        lascia_lucchetto(lucchetto)


def libera_per_il_pull(ramo_main, esiti):
    """Se il pull porta la cancellazione di path di transito che qui sono cambiati, quei file tornano alla
    copia di main: con l'autostash, modifica contro cancellazione è un conflitto che ferma il pull. La copia
    nuova sta già nel ramo sync (il commit appena fatto), e --dopo-il-pull la rimette su disco."""
    if git_main("fetch", "-q", "origin", ramo_main, timeout=90)[0] != 0:
        return
    # tre punti: solo le cancellazioni arrivate dal remote, non i file aggiunti da commit locali non spinti
    out = git_main("diff", "--name-only", "--no-renames", "--diff-filter=D", "-z", f"HEAD...origin/{ramo_main}",
                   "--", *percorsi())[1]
    tolti = [p for p in out.split("\0") if p]
    salvi = []
    for i in range(0, len(tolti), 200):
        pezzo = tolti[i:i + 200]
        out = git_main("diff", "--name-only", "--no-renames", "-z", "HEAD", "--", *pezzo)[1]
        sporchi = [p for p in out.split("\0") if p]
        # solo i file che il ramo sync ha identici al disco: gli altri (esclusi, o fermati dalla guardia) restano
        diversi = set(p for p in git("diff", "--name-only", "--no-renames", "-z", "HEAD", "--", *sporchi)[1]
                      .split("\0") if p) if sporchi else set()
        nel_ramo = set(p for p in git("ls-tree", "-r", "-z", "--name-only", "HEAD", "--", *sporchi)[1]
                       .split("\0") if p) if sporchi else set()
        salvi += [p for p in sporchi if p in nel_ramo and p not in diversi]
    for i in range(0, len(salvi), 200):
        git_main("checkout", "HEAD", "--", *salvi[i:i + 200])
    if salvi:
        esiti.append(f"{len(salvi)} file che il pull toglie tornati alla copia di main (la nuova sta nel ramo sync)")


def ripristina(main_prima, esiti):
    """I file di transito che il pull di main ha tolto dal disco, ripresi dal ramo sync. Solo quelli che main
    adesso ignora: è il commit che toglie i path da main. Una cancellazione vera, come la retention di una
    macchina non ancora migrata, li lascia tracciati e non ignorati, e resta."""
    if not main_prima or git_main("cat-file", "-e", f"{main_prima}^{{commit}}")[0] != 0:
        return
    rc, out, _ = git_main("diff", "--name-only", "--no-renames", "--diff-filter=D", "-z", main_prima, "HEAD",
                          "--", *percorsi())
    mancanti = [p for p in out.split("\0") if p and not (CL / p).exists()] if rc == 0 else []
    ignorati = []
    for i in range(0, len(mancanti), 200):
        # -z vale solo con --stdin: una riga per path, senza virgolette sugli accenti
        out = git_main("-c", "core.quotePath=false", "check-ignore", "--no-index", "--", *mancanti[i:i + 200])[1]
        ignorati += [p for p in out.splitlines() if p in mancanti]
    nel_ramo = []
    for i in range(0, len(ignorati), 200):
        out = git("ls-tree", "-r", "-z", "--name-only", "HEAD", "--", *ignorati[i:i + 200])[1]
        nel_ramo += [p for p in out.split("\0") if p]
    for i in range(0, len(nel_ramo), 200):
        rc, out, err = git("checkout", "HEAD", "--", *nel_ramo[i:i + 200])
        if rc != 0:
            esiti.append(f"ripristino non riuscito: {ultima(err, out)}")
            return
    if nel_ramo:
        esiti.append(f"ripristinati {len(nel_ramo)} file che main non traccia più")


def aggiorna(esiti):
    """Fetch e rebase del ramo sync, anche dentro il minuto: il pull porta i dati delle altre macchine."""
    rc, out, err = git("ls-remote", "--exit-code", "--heads", "origin", RAMO, timeout=60)
    if rc == 2:
        esiti.append(f"ramo {RAMO} non ancora su origin")
        return 0
    if rc != 0:
        esiti.append(f"remote non raggiunto: {ultima(err, out)}")
        return 0
    rc, out, err = git("fetch", "-q", "origin", RAMO, timeout=90)
    if rc != 0:
        esiti.append(f"fetch non riuscito: {ultima(err, out)}")
        return 0
    if git("merge-base", "--is-ancestor", f"origin/{RAMO}", "HEAD")[0] == 0:
        esiti.append(f"ramo {RAMO} già allineato")
        return 0
    prima = git("rev-parse", "HEAD")[1].strip()
    ok, perche = fai_rebase()
    if perche:
        esiti.append(perche)
    if not ok:
        return 4
    n = git("rev-list", "--count", f"{prima}..HEAD")[1].strip() if prima else "?"
    esiti.append(f"ramo {RAMO} aggiornato ({n} commit arrivati)")
    return 0


def dopo_il_pull(main_prima):
    if not migrato():
        return 0
    lucchetto = aspetta_lucchetto()
    if lucchetto is None:
        print("sync dopo il pull: il lucchetto resta preso da un altro giro, il ramo sync si aggiorna al prossimo pull")
        return 0
    esiti = []
    try:
        prepara()
        if a_meta():
            print("sync: STOP, rebase a metà in .git-sync. Guarda con git --git-dir=.git-sync status.")
            return 4
        ripristina(main_prima, esiti)
        rc = commit(guardia_segreti(), esiti)
        if rc == 0:
            if origine()[1]:
                rc = aggiorna(esiti)
            else:
                esiti.append("solo locale")
        print("sync dopo il pull: " + " · ".join(esiti))
        return rc
    finally:
        try:
            segno_pull().unlink()
        except OSError:
            pass
        lascia_lucchetto(lucchetto)


def blob(gitfn, rif):
    """Il contenuto di un oggetto (HEAD:path), o None se non c'è."""
    p = subprocess.run(["git", *gitfn, "cat-file", "blob", rif], capture_output=True, timeout=60)
    return p.stdout if p.returncode == 0 else None


def unisci_tre(rel, base, mio, loro):
    """(bytes, ok): la fusione a tre del file, col driver che .gitattributes gli dà. ok False = conflitto."""
    driver = git_main("check-attr", "merge", "--", rel)[1].rsplit(": ", 1)[-1].strip()
    with tempfile.TemporaryDirectory(prefix="sync-aggancio-") as d:
        fo, fa, fb = (Path(d) / n for n in ("base", "mio", "loro"))
        fo.write_bytes(base or b"")
        fa.write_bytes(mio)
        fb.write_bytes(loro)
        comando = git_main("config", "--get", f"merge.{driver}.driver")[1].strip() \
            if driver not in ("union", "unspecified", "set", "unset", "") else ""
        if comando:
            rc = subprocess.run(comando.replace("%O", f'"{fo}"').replace("%A", f'"{fa}"').replace("%B", f'"{fb}"'),
                                shell=True, capture_output=True, timeout=60).returncode
        else:
            rc = subprocess.run(["git", "merge-file", "-q", *(["--union"] if driver == "union" else []),
                                 str(fa), str(fo), str(fb)], capture_output=True, timeout=60).returncode
        return fa.read_bytes(), rc == 0


def allinea_aggancio():
    """Dopo l'aggancio a un ramo sync che un'altra macchina ha già: il disco di questa macchina si allinea al
    ramo senza togliere niente. Un file che manca qui si riprende dal ramo: committato come cancellato, il
    primo giro lo toglierebbe a tutte le macchine. Un file diverso si fonde a tre, con la copia di main come
    base: senza cambi locali vince il ramo, coi cambi locali passano tutti e due. In conflitto resta la copia
    di questa macchina, e quella del ramo resta nella sua storia."""
    rc, out, _ = git("diff", "--name-only", "--no-renames", "-z")
    cambiati = [p for p in out.split("\0") if p] if rc == 0 else []
    ripresi, fusi, conflitti = 0, 0, []
    for rel in cambiati:
        loro = blob([f"--git-dir={SYNC}"], f"HEAD:{rel}")
        if loro is None:
            continue
        pieno = CL / rel
        if not pieno.exists():
            if git("checkout", "HEAD", "--", rel)[0] == 0:
                ripresi += 1
            continue
        mio = pieno.read_bytes()
        base = blob(["-C", str(CL)], f"HEAD:{rel}")
        if base == mio:
            git("checkout", "HEAD", "--", rel)
            ripresi += 1
            continue
        if base == loro:
            continue  # solo questa macchina l'ha cambiato: il primo giro lo committa
        unito, ok = unisci_tre(rel, base, mio, loro)
        if ok:
            pieno.write_bytes(unito)
            fusi += 1
        else:
            conflitti.append(rel)
    parti = [f"{ripresi} file presi dal ramo"] if ripresi else []
    parti += [f"{fusi} fusi coi cambi di questa macchina"] if fusi else []
    parti += [f"{len(conflitti)} in conflitto, tengo la copia di questa macchina ({', '.join(conflitti[:5])})"] \
        if conflitti else []
    return (": " + ", ".join(parti)) if parti else ""


def migra(prova):
    elenco = percorsi()
    if not elenco:
        print(f"sync: {ELENCO} non dà nessun path di transito")
        return 5
    url, spingibile, perche = origine()
    esiste = (SYNC / "HEAD").exists()
    print(f"sync: migrazione{' (prova)' if prova else ''}: git dir {SYNC}, path {', '.join(elenco)}, "
          f"origin {url or 'nessuno'}, push {'sì' if spingibile else 'no (' + perche + ')'}"
          f"{', il git dir esiste già' if esiste else ''}")
    if prova:
        return 0
    prepara()
    if url:
        rc, out, err = git("fetch", "-q", "origin", RAMO, timeout=90)
        if rc == 0 and git("rev-parse", "--verify", "-q", f"origin/{RAMO}")[0] == 0:
            # Il ramo c'è già (un'altra macchina l'ha creato): HEAD lo segue, i file su disco restano com'erano
            # e il primo giro committa la differenza.
            git("symbolic-ref", "HEAD", f"refs/heads/{RAMO}")
            git("reset", "-q", f"origin/{RAMO}")
            print(f"sync: ramo {RAMO} di origin agganciato" + allinea_aggancio())
    rc = giro()
    return rc


def stato():
    if not (SYNC / "HEAD").exists():
        print("sync: non migrato su questa macchina")
        return 0
    avanti = git("rev-list", "--count", f"origin/{RAMO}..HEAD")[1].strip() or "?"
    eta = secondi_dall_ultimo_push()
    print(f"sync: {avanti} commit non spinti · ultimo push "
          f"{'mai' if eta > 1e8 else str(int(eta)) + ' s fa'} · lucchetto {'preso' if file_lucchetto().exists() else 'libero'}"
          f"{' · BLOCCATO, guarda data/logs/sync-transito.log' if (SYNC / 'bloccato-dal').exists() else ''}")
    return 0


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--giro", action="store_true")
    g.add_argument("--subito", action="store_true")
    g.add_argument("--migra", action="store_true")
    g.add_argument("--stato", action="store_true")
    g.add_argument("--prima-del-pull", nargs="?", const="main", metavar="RAMO_MAIN")
    g.add_argument("--dopo-il-pull", metavar="SHA")
    ap.add_argument("--prova", action="store_true")
    a = ap.parse_args(argv)
    if a.prima_del_pull is not None:
        return prima_del_pull(a.prima_del_pull)
    if a.dopo_il_pull is not None:
        return dopo_il_pull(a.dopo_il_pull)
    if a.migra:
        return migra(a.prova)
    if a.stato:
        return stato()
    return giro(subito=a.subito)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
