#!/usr/bin/env python3
"""I dati di transito della config su un ramo `sync`, fuori da `main` (revisione del 22/11/2026, D5, #6424).

Handoff, stati dei progetti, note e log di Melchior cambiano a ogni /fine e a ogni prompt. Su `main` facevano
176 commit al giorno e un merge driver per ogni file. Qui stanno in un secondo git dentro la stessa cartella:
`<config>/.git-sync`, con work tree `<config>`, ramo `sync`. I file restano dove li cercano hook e script.
Quali path passano di qui lo dice `data/transito.paths` (uno per riga, # commenta).

Uso:
  sync_transito.py --giro        commit raggruppato dei path di transito, poi il push se è passato il minuto
  sync_transito.py --subito      come --giro: lo chiama la coda di /fine a fine corsa
  sync_transito.py --migra       crea .git-sync e il ramo sync (con --prova stampa soltanto, non scrive)
  sync_transito.py --stato       una riga: commit locali non spinti, ultimo push, lucchetto

Un solo giro alla volta per macchina (lucchetto .git-sync/lock col pid) e al massimo un push al minuto
(.git-sync/ultimo-push). Un giro che trova il lucchetto occupato esce 0 senza fare niente. Il push parte solo
se il remote è privato: con origin sul repository pubblico di Arturo, o senza origin, i commit restano locali.
Prima del commit la guardia dei segreti (hooks/commit-secret-gate.py) legge le righe nuove: una chiave trovata
ferma il giro (exit 7), e il file la nomina senza mostrare il valore.

Exit: 0 fatto o niente da fare · 4 rebase a metà o conflitto: il ramo sync resta com'era · 5 uso sbagliato
· 6 git add o commit falliti · 7 segreto nello stage, o guardia che non si carica.

Variabili per i banchi: SYNC_TRANSITO_CLAUDE (la radice), SYNC_TRANSITO_MINUTO (secondi fra due push, 60),
SYNC_TRANSITO_VISIBILITA (PRIVATE per saltare gh).
"""
from __future__ import annotations

import argparse
import importlib.util
import os
import re
import signal
import subprocess
import sys
import time
from pathlib import Path

QUI = Path(__file__).resolve().parent
sys.path.append(str(QUI.parent / "hooks"))
from radici import radice_orsa  # noqa: E402

CL = Path(os.environ.get("SYNC_TRANSITO_CLAUDE") or radice_orsa())
SYNC = CL / ".git-sync"
ELENCO = QUI.parent / "data" / "transito.paths"
GUARDIA = QUI.parent / "hooks" / "commit-secret-gate.py"
RAMO = "sync"
RE_ARTURO = re.compile(r"github\.com[:/]stellakamikaze/arturo(\.git)?/?$")
RE_FILE_DIFF = re.compile(r"^diff --git a/.* b/(.*)$", re.M)
RE_SENSIBILE = re.compile(r"(?i)^(\.env(\..*)?|.*\.(env|key|pem|p12|pfx)|\.?credentials\.json|client_secret.*\.json"
                          r"|id_(rsa|ed25519|ecdsa|dsa))$")
CARTELLE_SENSIBILI = {"secrets", "credentials"}
RIGENERABILI = {".venv", "venv", "node_modules", "__pycache__"}
DIFF = ["--no-color", "--no-ext-diff", "--no-textconv", "--unified=0", "--no-renames"]
LUCCHETTO_VECCHIO = 600  # secondi: un giro dura pochi secondi, oltre è di un processo morto male
_OCCUPATO = (FileExistsError, PermissionError) if os.name == "nt" else (FileExistsError,)


def run(cmd, timeout=120, env=None):
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace",
                           timeout=timeout, env=env)
        return p.returncode, p.stdout, p.stderr
    except subprocess.TimeoutExpired:
        return None, "", f"timeout dopo {timeout} s"
    except OSError as e:
        return None, "", str(e)


def git(*a, timeout=120):
    """Il git del ramo sync."""
    return run(["git", f"--git-dir={SYNC}", f"--work-tree={CL}", *a], timeout)


def git_main(*a, timeout=60):
    return run(["git", "-C", str(CL), *a], timeout)


def ultima(*testi):
    righe = [r.strip() for t in testi for r in (t or "").replace("\x00", "").splitlines() if r.strip()]
    return righe[-1][:160] if righe else "nessun messaggio"


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


def file_di_transito():
    """I file su disco sotto i path di transito, senza gli esclusi."""
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
    return [x for x in dict.fromkeys(out) if not escluso(x)]


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
    rc, out, _ = run(["bash", "-c", 'gh repo view "$1" --json visibility -q .visibility', "gh", url], 30)
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
    git("config", "core.autocrlf", "false")
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


def viva(pid):
    if os.name == "nt":
        return True
    try:
        os.kill(int(pid), 0)
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

def a_meta():
    return any((SYNC / n).is_dir() for n in ("rebase-merge", "rebase-apply"))


def aggiungi():
    """Mette in stage i file di transito: -f perché il .gitignore di main li nomina, e i cancellati con -u."""
    elenco = file_di_transito()
    for i in range(0, len(elenco), 200):
        rc, out, err = git("add", "-f", "-A", "--", *elenco[i:i + 200])
        if rc != 0:
            return False, ultima(err, out)
    tracciati = [p for p in percorsi() if git("ls-files", "--", p)[1].strip()]
    if tracciati:
        rc, out, err = git("add", "-u", "--", *tracciati)
        if rc != 0:
            return False, ultima(err, out)
    # Un file diventato escluso (un lucchetto, una chiave) non deve restare nel ramo: fuori dall'indice, non dal disco.
    for x in git("ls-files", "-z")[1].split("\0"):
        if x and escluso(x):
            git("rm", "-q", "--cached", "--", x)
    return True, ""


def commit(guardia, esiti):
    """0 fatto (o niente), 6 commit fallito, 7 segreto."""
    ok, err = aggiungi()
    if not ok:
        esiti.append(f"git add fallito: {err}")
        return 6
    staged = [p for p in git("diff", "--cached", "--name-only", "--no-renames", "-z")[1].split("\0") if p]
    if not staged:
        esiti.append("niente da committare")
        return 0
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
        rc, out, err = git("commit", "-q", "-m", msg, "--only", "--", *paths) if memoria and resto else \
            git("commit", "-q", "-m", msg)
        if rc != 0:
            esiti.append(f"commit fallito: {ultima(err, out)}")
            return 6
        esiti.append(f"commit {git('rev-parse', '--short', 'HEAD')[1].strip()} ({len(paths)} file)")
    return 0


def fai_rebase():
    """Il ramo locale sopra origin/sync. (ok, perché non). In conflitto torna com'era."""
    rc, out, err = git("rebase", f"origin/{RAMO}", timeout=180)
    if rc == 0:
        return True, ""
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
            if not ok:
                esiti.append(perche)
                return 4
    rc, out, err = git("push", "-q", "origin", f"HEAD:{RAMO}", timeout=90)
    if rc != 0:
        # Un altro processo ha spinto fra il fetch e il push: un secondo giro di rebase.
        git("fetch", "-q", "origin", RAMO, timeout=90)
        ok, perche = fai_rebase()
        if not ok:
            esiti.append(perche)
            return 4
        rc, out, err = git("push", "-q", "origin", f"HEAD:{RAMO}", timeout=90)
        if rc != 0:
            esiti.append(f"push non riuscito: {ultima(err, out)}")
            return 0
    try:
        (SYNC / "ultimo-push").write_text(f"{time.time()}\n", encoding="utf-8")
    except OSError:
        pass
    esiti.append("push riuscito")
    return 0


def secondi_dall_ultimo_push():
    try:
        return time.time() - float((SYNC / "ultimo-push").read_text(encoding="utf-8").split()[0])
    except (OSError, ValueError, IndexError):
        return 1e9


def giro():
    if not (CL / ".git").exists() or not percorsi():
        print("sync: config senza git o nessun path di transito: niente da fare")
        return 0
    if not (SYNC / "HEAD").exists():
        print("sync: il ramo sync non c'è su questa macchina (python3 bin/sync_transito.py --migra): niente da fare")
        return 0
    lucchetto = prendi_lucchetto()
    if lucchetto is None:
        print("sync: un altro giro tiene il lucchetto, riprovo al prossimo minuto")
        return 0
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
        elif secondi_dall_ultimo_push() < float(os.environ.get("SYNC_TRANSITO_MINUTO") or 60) \
                and avanti not in ("", "0"):
            esiti.append("push al prossimo minuto")
        else:
            rc = push(esiti)
            if rc:
                print("sync: " + " · ".join(esiti))
                return rc
        print("sync: " + " · ".join(esiti))
        return 0
    finally:
        lascia_lucchetto(lucchetto)


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
            print(f"sync: ramo {RAMO} di origin agganciato")
    rc = giro()
    return rc


def stato():
    if not (SYNC / "HEAD").exists():
        print("sync: non migrato su questa macchina")
        return 0
    avanti = git("rev-list", "--count", f"origin/{RAMO}..HEAD")[1].strip() or "?"
    eta = secondi_dall_ultimo_push()
    print(f"sync: {avanti} commit non spinti · ultimo push "
          f"{'mai' if eta > 1e8 else str(int(eta)) + ' s fa'} · lucchetto {'preso' if file_lucchetto().exists() else 'libero'}")
    return 0


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--giro", action="store_true")
    g.add_argument("--subito", action="store_true")
    g.add_argument("--migra", action="store_true")
    g.add_argument("--stato", action="store_true")
    ap.add_argument("--prova", action="store_true")
    a = ap.parse_args(argv)
    if a.migra:
        return migra(a.prova)
    if a.stato:
        return stato()
    return giro()


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
