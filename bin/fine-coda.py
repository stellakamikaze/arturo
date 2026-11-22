#!/usr/bin/env python3
"""La coda di /fine in una chiamata: gate, retention, indice, commit e push della config (#4291, F0 L3).

Questi passi non chiedono giudizio, e ogni chiamata a un tool rilegge tutto il contesto di fine sessione:
qui girano in un processo solo. Il giudizio resta in /fine: destino dei file, handoff, scelta di cosa
salvare degli handoff in uscita (il dry-run della retention), memoria.

Uso:
  python3 ~/.claude/bin/fine-coda.py --handoff <path> --slug <slug> [--leggero] [--rotazione] [--trailer <riga>] [-- <argomenti tuoi>]

--leggero: il fine leggero della rotazione automatica (/fine --rotazione, 3/11/2026). Salta la retention,
che aspetta il fine completo. Senza --leggero la coda scrive la data di oggi (AAAA-MM-GG) in
<cartella dell'handoff>/.ultimo-fine-completo, e il file segue l'handoff: entra nel commit solo verso
un remote privato. Senza handoff
(solo il sync della config) niente segno. Indice, retention e contesto leggono solo i file HANDOFF_*.md.

--rotazione: il giro è in rotazione anche quando è il completo delle 18; --leggero lo implica. L'handoff
non chiede alla persona /clear e /inizio (#5878): una riga "Prossimo passo:" con tutti e due, senza "io",
"Claude" o "Arturo" come soggetto, o una riga della Ripartenza con "scrivi", "lancia", "tu"... prima di
/clear, rende la coda rossa (exit 1). Con ARTURO_ROTAZIONE spenta ("0", "no", "off") il controllo tace.

Ordine dei passi:
  1. stop se ~/.claude è a metà di un rebase, o se hooks/controlla-config.py la trova rotta;
  2. gate (bin/handoff-gate.sh): rosso = niente commit; in rotazione anche il passo dopo che chiede /clear;
  3. retention con --applica: escono solo i file dell'elenco del dry-run della FASE 6 (non con --leggero);
     senza --leggero, il segno del fine completo nella cartella dell'handoff;
  4. indice (bin/index-rigenera.py --scrivi);
  5. aggancio personale "dopo-index";
  6. git add per percorso: i file di Arturo, gli handoff, e solo verso un remote privato CLAUDE.md,
     data/todo, personale/ e data/memory (senza lucchetti, log di Melchior, copie .bak-* e indice
     della memoria, che si rigenera; senza i file sensibili di .gitignore e le cartelle rigenerabili,
     che la riga di esito nomina). Verso un remote non privato, nelle cartelle di Arturo entrano solo i file
     già tracciati: quelli nuovi sono della persona, e la riga FILE TUOI NON SALVATI li nomina;
  7. controllo dei marcatori di conflitto nei file in stage: un file con <<<<<<< e >>>>>>>, nominato;
  8. aggancio personale "prima-commit";
  8b. segreti nello stage, coi pattern di hooks/commit-secret-gate.py: una chiave trovata ferma il commit;
  9. commit della memoria ("memoria: applicata da /fine") separato dal commit di sync;
 10. segreti nei commit che il remote non ha ancora, poi push. Se il primo è rifiutato, i commit si
     rifanno sopra origin/main in una copia di prova dentro .git, mai nei file in uso (#6248); solo una
     copia integra arriva in ~/.claude, con git reset --keep, e parte il secondo push. Niente push
     se origin è il repository pubblico di Arturo. Un conflitto solo su file derivati (INDEX.md,
     .ultimo-fine-completo) si risolve da solo: l'indice si rigenera, il segno tiene la data più recente.
     Ogni altro conflitto lascia ~/.claude com'era e i commit in locale.

--avvisi: l'anteprima della FASE 9, prima della coda (#6275, segnalazione n. 94). Il passo 6 gira su una copia
dell'indice e dà i file fuori da data/ che il commit di sync prenderebbe; poi legge le altre sessioni vive di
questa macchina (sessions/<pid>.json) e le loro trascrizioni. Stampa una riga "AVVISA <nome> (sessione <id>):
<file>" per ogni sessione che ha scritto o nominato uno di quei file. Exit 0 con almeno una riga, exit 3 con
una riga sola quando non c'è nessuno da avvisare. Niente commit, niente gate, l'indice vero resta com'era.
I path dell'aggancio personale non entrano nell'anteprima. FINE_CODA_SESSIONI sposta le sessioni (banchi).

Aggancio personale: se esiste ~/.claude/personale/fine-coda.py, la coda lo lancia ai passi 5 e 8 con un
JSON su stdin: {"fase", "handoff", "slug", "radice", "argomenti" (quelli dopo --), "in_stage"}. Risponde
su stdout {"esiti": [...], "path": [...], "blocca": null o "motivo"}. I "path" (relativi a ~/.claude)
entrano nel commit di sync. Exit 0 fatto, 3 servizio giù (la coda prosegue e lo dice), 4 blocca.

Exit:
  0 fatto (l'ultima riga è la riga tecnica per la chiusura) · 1 gate rosso, o handoff che in rotazione
  chiede /clear alla persona · 3 l'aggancio personale
  dice che un servizio è giù · 4 rebase a metà, config rotta, marcatori di conflitto o blocco
  dell'aggancio: niente commit · 5 uso sbagliato · 6 git add o git commit falliti · 7 segreto nello stage
  (niente commit) o nei commit da spingere (niente push), o guardia dei segreti che non si carica
  · 8 un'altra coda tiene il lucchetto oltre l'attesa: niente commit

Lucchetto: una coda alla volta per config, in session-env/fine-coda.lock col pid (A4, 22/11/2026). La seconda
aspetta fino a FINE_CODA_ATTESA secondi (300). Un lucchetto col pid di un processo morto, o più vecchio di
30 minuti, è di una coda interrotta e si toglie da solo. --avvisi non lo prende: lavora su una copia dell'indice.

FINE_CODA_CLAUDE sposta la radice (per i banchi).
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import time
from datetime import date
from pathlib import Path
sys.path.append(str(Path(os.path.realpath(__file__)).parent.parent / "hooks"))
from radici import radice_orsa  # noqa: E402

CL = Path(os.environ.get("FINE_CODA_CLAUDE") or radice_orsa())
QUI = Path(__file__).resolve().parent
PY = sys.executable
# Su Windows "bash" senza percorso apre il bash di WSL da System32, prima del PATH: serve quello di Git.
BASH = shutil.which("bash") or "bash"
# Un conflitto è un file con <<<<<<< e >>>>>>> insieme: una riga di soli ======= è la sottolineatura di
# un titolo in Markdown (review del 7/11/2026, finding 30).
RE_APRE = re.compile(r"^\+<<<<<<< ", re.M)
RE_CHIUDE = re.compile(r"^\+>>>>>>> ", re.M)
RE_FILE_DIFF = re.compile(r"^diff --git a/.* b/(.*)$", re.M)
RE_ARTURO = re.compile(r"github\.com[:/]stellakamikaze/arturo(\.git)?/?$")
ARTURO = ["settings.json", ".gitattributes", ".gitignore", "bin", "commands", "agents", "hooks", "shared",
          "docs", "tools", "tests", "output-styles", "NOVITA.md", "README.md", "package.json"]
PRIVATI = ["CLAUDE.md", "data/todo", "personale", "data/memory"]
# Restano fuori anche verso un remote privato: il lucchetto di arturo todo, i log e le cache di
# Melchior, le copie di sicurezza e l'indice della memoria, che si rigenera. L'elenco dei file lo fa la
# coda: git add -f con un pathspec ":(exclude)" su una cartella ignorata a volte non aggiunge niente e
# non dà errore (git 2.55 su Windows, 30/10/2026, stesso comando con esiti diversi).
INDICE_MEMORIA = "data/memory/index.md"
# Il segno del fine completo (rotazione automatica, 3/11/2026), nella cartella dell'handoff.
SEGNO_COMPLETO = ".ultimo-fine-completo"


# I file sensibili di .gitignore ("MAI committare") e le cartelle che si rigenerano restano fuori anche
# verso un remote privato: git add -f scavalcherebbe .gitignore. La coda li nomina (review del 7/11/2026,
# finding 25).
RE_SENSIBILE = re.compile(r"(?i)^(\.env(\..*)?|.*\.(env|key|pem|p12|pfx)|\.?credentials\.json|client_secret.*\.json"
                          r"|id_(rsa|ed25519|ecdsa|dsa))$")
CARTELLE_SENSIBILI = {"secrets", "credentials"}
RIGENERABILI = {".venv", "venv", "node_modules", "__pycache__"}


def escluso(rel):
    parti = rel.split("/")
    nome = parti[-1]
    return (rel == INDICE_MEMORIA or nome.endswith(".lock") or ".bak-" in nome
            or any(x.startswith(".melchior-") or x == ".git" for x in parti))


def fuori_per_regola(rel):
    """"sensibile", "rigenerabile" o "" per un file su disco che git add -f non deve prendere."""
    parti = rel.split("/")
    if RE_SENSIBILE.match(parti[-1]) or any(x in CARTELLE_SENSIBILI for x in parti[:-1]):
        return "sensibile"
    if parti[-1].endswith(".pyc") or any(x in RIGENERABILI for x in parti[:-1]):
        return "rigenerabile"
    return ""


def file_privati(radice, percorsi, saltati=None):
    """I file da aggiungere con -f: quelli su disco sotto i percorsi, più i tracciati cancellati, senza gli
    esclusi. I file sensibili e le cartelle rigenerabili finiscono in `saltati` (tipo -> percorsi)."""
    saltati = {} if saltati is None else saltati
    out = []
    for p in percorsi:
        pieno = radice / p
        if pieno.is_file():
            out.append(p)
            continue
        for cartella, dirs, nomi in os.walk(pieno):
            base = Path(cartella).relative_to(radice).as_posix()
            for d in [d for d in dirs if d in RIGENERABILI]:
                saltati.setdefault("rigenerabile", []).append(f"{base}/{d}/")
            dirs[:] = [d for d in dirs if d != ".git" and d not in RIGENERABILI]
            out += [f"{base}/{n}" for n in nomi]
    tenuti = []
    for x in dict.fromkeys(out):
        perche = fuori_per_regola(x)
        if perche:
            saltati.setdefault(perche, []).append(x)
        elif not escluso(x):
            tenuti.append(x)
    tracciati = git("ls-files", "-z", "--", *percorsi)[1].split("\0")
    tenuti += [t for t in tracciati if t and not (radice / t).exists() and not escluso(t)]
    return list(dict.fromkeys(tenuti))


def riga_saltati(saltati):
    """L'esito dei file lasciati fuori da file_privati, o "" se non ce ne sono."""
    pezzi = []
    for tipo, nome in (("sensibile", "sensibili"), ("rigenerabile", "rigenerabili")):
        elenco = saltati.get(tipo) or []
        if elenco:
            pezzi.append(f"{nome} {', '.join(elenco[:5])}" + (f" e altri {len(elenco) - 5}" if len(elenco) > 5 else ""))
    return ("fuori dal commit, come dice .gitignore: " + "; ".join(pezzi)) if pezzi else ""
STOP_REBASE = ("REBASE A METÀ in ~/.claude: STOP, niente commit né push. Guarda con git -C ~/.claude status,\n"
               "poi rebase --continue (o --abort), e rilancia la coda.")


def run(cmd, timeout=180, entrata=None, cwd=None, env=None):
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace",
                           timeout=timeout, input=entrata, cwd=cwd, env=env)
        return p.returncode, p.stdout, p.stderr
    except subprocess.TimeoutExpired:
        return None, "", f"timeout dopo {timeout} s"
    except OSError as e:
        return None, "", str(e)


# L'anteprima degli avvisi (--avvisi) fa girare il passo 6 su una copia dell'indice: git() e aggiungi_forzati()
# leggono l'ambiente da qui, e None vuol dire l'indice vero.
ENV_GIT = None


def git(*a, timeout=120):
    return run(["git", "-C", str(CL), *a], timeout, env=ENV_GIT)


def ultima(*testi):
    righe = [r.strip() for t in testi for r in (t or "").splitlines() if r.strip()]
    return righe[-1][:160] if righe else "nessun messaggio"


def rebase_a_meta(radice=None):
    """Un rebase fermo in ~/.claude, o nella cartella `radice` (la copia di prova, dove .git è un file)."""
    if radice is None:
        return (CL / ".git" / "rebase-merge").is_dir() or (CL / ".git" / "rebase-apply").is_dir()
    for nome in ("rebase-merge", "rebase-apply"):
        rc, out, _ = run(["git", "-C", str(radice), "rev-parse", "--path-format=absolute", "--git-path", nome], 30)
        if rc == 0 and Path(out.strip()).is_dir():
            return True
    return False


def visibilita(url):
    """PRIVATE, PUBLIC, INTERNAL o "" se gh non risponde: solo PRIVATE apre i file personali."""
    if not url:
        return ""
    # gh passa da bash, come nella FASE 9 di prima: bash lo trova anche quando è uno script, su ogni sistema
    rc, out, _ = run([BASH, "-c", 'gh repo view "$1" --json visibility -q .visibility', "gh", url], 30)
    return out.strip() if rc == 0 else ""


def handoff_della_sessione():
    """L'handoff di questa sessione (riga "- Sessione: <id>"), il più recente per nome, o None."""
    sid = os.environ.get("CLAUDE_CODE_SESSION_ID", "").strip()
    if not sid:
        return None
    trovati = []
    for f in (CL / "data" / "handoffs").glob("*/HANDOFF_*.md"):
        try:
            if re.search(rf"(?m)^- Sessione: {re.escape(sid)}\s*$", f.read_text(encoding="utf-8", errors="replace")):
                trovati.append(f)
        except OSError:
            continue
    return max(trovati, key=lambda f: f.name) if trovati else None


# In rotazione /clear e /inizio li fa il tool ruota: un handoff che li chiede alla persona porta quella
# richiesta nella chiusura (#5878, revisione del 17/11/2026: cinque sessioni chiuse con "scrivi /clear").
RE_CLEAR = re.compile(r"(?i)(?<![\w/])/clear\b")
RE_INIZIO = re.compile(r"(?i)(?<![\w/])/(?:arturo:)?inizio\b")
RE_PASSO = re.compile(r"(?i)^\s*[-*]?\s*\**prossimo passo:?\**:?\s*(.*)$")
# Il passo che nomina Claude come soggetto racconta il lavoro, non chiede un gesto alla persona.
RE_SOGGETTO_CLAUDE = re.compile(r"(?i)^(io|claude|arturo)\b")
# Fuori dal prossimo passo conta solo una richiesta esplicita, con il verbo prima di /clear.
RE_RICHIESTA = re.compile(r"(?i)\b(tu|scrivi|scrivete|scrivimi|digita|lancia|esegui|batti|premi|incolla)\b"
                          r"[^.\n]{0,60}(?<![\w/])/clear\b")


def rotazione_spenta(valore):
    """Lo stesso interruttore del mod (skills/arturo/hooks/rotazione/rotazione.ts, spenta())."""
    return valore is not None and bool(re.fullmatch(r"(?i)0|no|off|spent[ao]|false", valore.strip()))


def chiede_clear(testo):
    """Le righe della Ripartenza (o "Prossimo passo:" ovunque) che chiedono alla persona /clear e /inizio."""
    trovate, in_ripartenza = [], False
    for riga in testo.splitlines():
        if riga.startswith("## "):
            in_ripartenza = riga.strip().lower() == "## ripartenza"
            continue
        passo = RE_PASSO.match(riga)
        if not (passo or in_ripartenza) or not (RE_CLEAR.search(riga) and RE_INIZIO.search(riga)):
            continue
        if passo:
            if not RE_SOGGETTO_CLAUDE.match(passo.group(1).strip("* ")):
                trovate.append(riga.strip())
        elif RE_RICHIESTA.search(riga):
            trovate.append(riga.strip())
    return trovate


def personale(fase, base, in_stage):
    """L'aggancio personale: (esiti, path, blocca, offline). Assente = niente."""
    script = CL / "personale" / "fine-coda.py"
    if not script.is_file():
        return [], [], None, False
    rc, out, err = run([PY, str(script)], 300, entrata=json.dumps({**base, "fase": fase, "in_stage": in_stage}))
    try:
        dati = json.loads(out.strip().splitlines()[-1]) if out.strip() else {}
    except (ValueError, IndexError):
        dati = {}
    esiti = [str(x) for x in dati.get("esiti") or []] if isinstance(dati, dict) else []
    path = [str(x) for x in dati.get("path") or []] if isinstance(dati, dict) else []
    blocca = dati.get("blocca") if isinstance(dati, dict) else None
    if rc == 4 and not blocca:
        blocca = ultima(err, out)
    if rc not in (0, 3, 4):
        esiti.append(f"personale/fine-coda.py ({fase}) rc={rc}: {ultima(err, out)}")
    if err.strip() and rc in (0, 3):
        print(err.strip())
    return esiti, path, blocca, rc == 3


# I file che la coda rigenera: due macchine che chiudono /fine li cambiano nello stesso punto, e il
# rebase si fermava lì (review del 7/11/2026, finding 26). Un conflitto solo su questi si risolve da solo.
RE_DERIVATO = re.compile(r"^data/handoffs/(INDEX\.md|[^/]+/\.ultimo-fine-completo)$")


def in_conflitto(radice):
    return [p for p in run(["git", "-C", str(radice), "diff", "--name-only", "--diff-filter=U", "-z"], 60)[1]
            .split("\0") if p]


def risolvi_derivati(radice=None):
    """Un rebase fermo solo su file derivati: l'indice si rigenera dagli handoff, il segno del fine completo
    tiene la data più recente, poi il rebase continua. True se alla fine non c'è più un rebase a metà.
    `radice` è la copia di prova della coda; senza, ~/.claude (un rebase lasciato da una coda di prima)."""
    dove = radice or CL
    env = dict(os.environ, GIT_EDITOR="true")
    for _ in range(100):
        if not rebase_a_meta(radice):
            return True
        conflitti = in_conflitto(dove)
        if not conflitti or not all(RE_DERIVATO.match(p) for p in conflitti):
            return False
        for p in conflitti:
            if p.endswith("/" + SEGNO_COMPLETO):
                try:
                    date_viste = re.findall(r"\d{4}-\d{2}-\d{2}", (dove / p).read_text(encoding="utf-8", errors="replace"))
                    (dove / p).write_text((max(date_viste) if date_viste else date.today().isoformat()) + "\n",
                                          encoding="utf-8")
                except OSError:
                    return False
        if any(p.endswith("INDEX.md") for p in conflitti):
            rc, _, _ = run([PY, str(QUI / "index-rigenera.py"), "--scrivi", "--radice", str(dove / "data" / "handoffs")], 60)
            if rc != 0:
                return False
        if run(["git", "-C", str(dove), "add", "--", *conflitti], 60)[0] != 0:
            return False
        rc, _, _ = run(["git", "-C", str(dove), "rebase", "--continue"], 120, env=env)
        if rc != 0 and not rebase_a_meta(radice):
            return False
    return not rebase_a_meta(radice)


# Commit e push della coda partono da subprocess: la guardia dei segreti del dispatcher legge solo i comandi
# Bash, e un token in settings.json usciva su GitHub senza controllo (revisione del 20/11/2026, A2, #6249).
# La coda usa gli stessi pattern della guardia, dal suo file: un elenco solo.
GUARDIA = QUI.parent / "hooks" / "commit-secret-gate.py"
DIFF = ["--no-color", "--no-ext-diff", "--no-textconv", "--unified=0", "--no-renames"]


def guardia_segreti():
    """Il modulo di hooks/commit-secret-gate.py, o None se non si carica. Il modulo arma un gestore di SIGALRM
    quando si carica: la coda rimette il suo."""
    allarme = getattr(signal, "SIGALRM", None)
    prima = signal.getsignal(allarme) if allarme else None
    try:
        spec = importlib.util.spec_from_file_location("arturo_commit_secret_gate", GUARDIA)
        modulo = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(modulo)
        return modulo if callable(getattr(modulo, "_trovati", None)) and callable(getattr(modulo, "_aggiunte", None)) \
            else None
    except Exception:  # noqa: BLE001 - una guardia che non si carica ferma la coda, non la rompe
        return None
    finally:
        if allarme:
            signal.signal(allarme, prima)


def segreti_nel_diff(guardia, diff):
    """[(file, [tipi di segreto])] nelle righe aggiunte di un diff, anche di più commit. Mai il valore."""
    per_file = {}
    inizi = list(RE_FILE_DIFF.finditer(diff))
    for i, m in enumerate(inizi):
        pezzo = diff[m.end():inizi[i + 1].start() if i + 1 < len(inizi) else len(diff)]
        for nome in guardia._trovati(guardia._aggiunte(pezzo)):
            per_file.setdefault(m.group(1), {})[nome] = None
    return [(f, list(nomi)) for f, nomi in per_file.items()]


def controlla_segreti(guardia, argomenti, dove, rimedio):
    """None se il diff è pulito, altrimenti le righe che fermano la coda. `dove` dice cosa si stava per fare,
    `rimedio` cosa fare con una chiave trovata."""
    if guardia is None:
        return [f"SEGRETI: STOP, niente {dove}. La guardia dei segreti ({GUARDIA}) non si carica, e la coda non "
                "manda niente senza controllo. Reinstalla Arturo con /aggiorna, poi rilancia la coda."]
    rc, out, err = git(*argomenti, timeout=120)
    if rc != 0:
        return [f"SEGRETI: STOP, niente {dove}. git non dà il diff da controllare: {ultima(err, out)}. "
                "Rilancia la coda; se resta così, guarda con git -C ~/.claude status."]
    trovati = segreti_nel_diff(guardia, out)
    if not trovati:
        return None
    righe = [f"SEGRETO: STOP, niente {dove}. La guardia dei segreti trova nelle righe nuove:"]
    righe += [f"  {f}: {', '.join(nomi)}" for f, nomi in trovati[:10]]
    if len(trovati) > 10:
        righe.append(f"  e altri {len(trovati) - 10} file")
    return righe + [rimedio]


# Il push rifiutato si univa con un pull --rebase --autostash dentro ~/.claude: con un conflitto su
# settings.json il file restava coi marcatori, non era più JSON e Claude Code spegneva tutte le guardie
# (revisione del 20/11/2026, A1, #6248). Ora il rebase gira in una copia di prova dentro .git, come in
# bin/aggiorna-applica.sh, e in ~/.claude arriva solo un risultato integro, con git reset --keep: si
# rifiuta, senza toccare niente, se un file modificato o non tracciato qui verrebbe sovrascritto.
CASA_COPIE = "arturo-fine-coda"
FERMA_QUI = "la config su questa macchina è com'era, e i commit restano qui: il prossimo /inizio li riprova"


def togli_copia(lavoro, copia):
    if copia.exists():
        run(["git", "-C", str(copia), "rebase", "--abort"], 60)
    run(["git", "-C", str(CL), "worktree", "remove", "--force", str(copia)], 120)
    # Si cancella solo una cartella delle copie di prova della coda, mai un percorso letto da git.
    if lavoro.parent.name == CASA_COPIE and lavoro.name.startswith("copia."):
        shutil.rmtree(lavoro, ignore_errors=True)
    git("worktree", "prune")


def unisci_nella_copia(prima):
    """(commit unito o None, motivo): i commit da `prima` rifatti sopra origin/main in una copia di prova.
    La copia si toglie sempre, anche con un conflitto: lì i commit restano solo in ~/.claude."""
    comune = git("rev-parse", "--path-format=absolute", "--git-common-dir")[1].strip()
    if not comune:
        return None, "non trovo la cartella .git della config"
    casa = Path(comune) / CASA_COPIE
    try:
        casa.mkdir(exist_ok=True)
        lavoro = Path(tempfile.mkdtemp(prefix="copia.", dir=str(casa)))
    except OSError as e:
        return None, f"copia di prova non pronta: {e}"
    copia = lavoro / "copia"
    try:
        rc, out, err = git("worktree", "add", "-q", "--detach", str(copia), prima, timeout=300)
        if rc != 0:
            return None, f"copia di prova non pronta: {ultima(err, out)}"
        # --rebase-merges come il sync di /inizio: un merge di un aggiornamento di Arturo non ancora
        # pushato resta un merge.
        rc, out, err = run(["git", "-C", str(copia), "rebase", "--rebase-merges", "origin/main"], 300,
                           env=dict(os.environ, GIT_EDITOR="true"))
        if rebase_a_meta(copia) and not risolvi_derivati(copia):
            conflitti = in_conflitto(copia)
            return None, ("conflitto con origin su " + ", ".join(conflitti[:5]) if conflitti
                          else f"unione ferma: {ultima(err, out)}")
        nuovo = run(["git", "-C", str(copia), "rev-parse", "HEAD"], 30)[1].strip()
        if not nuovo or run(["git", "-C", str(copia), "merge-base", "--is-ancestor", "origin/main", nuovo], 30)[0] != 0:
            return None, f"unione ferma: {ultima(err, out)}"
        controlla = CL / "hooks" / "controlla-config.py"
        if controlla.is_file():
            rc, out, err = run([PY, str(controlla), "--quiet", str(copia)], 60, env=dict(os.environ, ARTURO_RIPIEGO=str(CL)))
            if rc != 0:
                return None, f"l'unione con origin romperebbe la config: {ultima(err, out)}"
        return nuovo, ""
    finally:
        togli_copia(lavoro, copia)


def integra():
    """(ok, motivo): il push rifiutato. I commit locali si uniscono a origin/main nella copia di prova, e
    ~/.claude passa al risultato solo se la copia è integra."""
    rc, out, err = git("fetch", "-q", "origin", "main", timeout=90)
    if rc != 0:
        return False, f"fetch fermo: {ultima(err, out)}"
    prima = git("rev-parse", "HEAD")[1].strip()
    nuovo, motivo = unisci_nella_copia(prima)
    if not nuovo:
        return False, f"{motivo}; {FERMA_QUI}"
    if git("rev-parse", "HEAD")[1].strip() != prima:
        return False, f"un commit nuovo è arrivato durante l'unione; {FERMA_QUI}"
    rc, out, err = git("reset", "-q", "--keep", nuovo)
    if rc != 0:
        return False, (f"l'unione cambierebbe file modificati o non tracciati qui ({ultima(err, out)}); "
                       f"{FERMA_QUI}")
    controlla = CL / "hooks" / "controlla-config.py"
    if controlla.is_file() and run([PY, str(controlla), "--quiet"], 60)[0] != 0:
        git("reset", "-q", "--keep", prima)
        return False, f"dopo l'unione la config risultava rotta, tornata a prima; {FERMA_QUI}"
    return True, ""


def push(origin_url):
    """(ok, motivo). Un push rifiutato passa dall'unione nella copia di prova (integra) e riprova una volta."""
    rc, out, err = git("push", "-q", "origin", "HEAD:main", timeout=90)
    if rc == 0:
        return True, ""
    ok, motivo = integra()
    if not ok:
        return False, motivo
    rc, out, err = git("push", "-q", "origin", "HEAD:main", timeout=90)
    return rc == 0, ultima(err, out)


def aggiungi(*argomenti):
    rc, _, err = git("add", *argomenti)
    return rc == 0 or "did not match any files" in err, err


def skill_di_arturo():
    """I nomi delle skill di Arturo (l'elenco della telemetria, banco TS01), o un insieme vuoto se manca."""
    sys.path.insert(0, str(QUI))
    try:
        import telemetria
        return set(telemetria.SKILL)
    except Exception:  # noqa: BLE001 - senza elenco ogni skill vale come della persona e resta fuori
        return set()
    finally:
        sys.path.pop(0)


def aggiungi_forzati(elenco):
    """git add -A -f per un elenco esplicito di file, passato su stdin: niente limiti di riga di comando."""
    if not elenco:
        return True, ""
    rc, _, err = run(["git", "-C", str(CL), "add", "-A", "-f", "--pathspec-from-file=-", "--pathspec-file-nul"],
                     120, entrata="\0".join(elenco), env=ENV_GIT)
    return rc == 0, err


def retention(slug):
    """Il passo 3: la retention con --applica, in una riga di esito."""
    rc, out, err = run([PY, str(QUI / "handoff-retention.py"), slug, "--applica",
                        "--radice", str(CL / "data" / "handoffs")], 60)
    if rc == 0:
        n = len(re.findall(r"(?m)^NEL CESTINO ", out))
        resta = len(re.findall(r"(?m)^RESTA ", out))
        if "AVVISO: nessun elenco" in out:
            return ("retention NON applicata: manca il dry-run della FASE 6"
                    + (f", {resta} file oltre il keep restano" if resta else ""))
        return ("retention ok" + (f" ({n} nel cestino)" if n else "")
                + (f", {resta} restano: fuori dal dry-run" if resta else ""))
    if rc == 2 and "cartella assente" in err:
        return "retention: nessun handoff per questo slug"
    print((out + err).strip())
    return f"retention rc={rc}: {ultima(err, out)}"


def aggiungi_per_percorso():
    """Il passo 6: git add per percorso, sull'indice di ENV_GIT. Non stampa: le righe da mostrare e gli esiti
    tornano a chi chiama, così l'anteprima di --avvisi usa le stesse regole del commit vero."""
    origin = git("remote", "get-url", "origin")[1].strip()
    origin_arturo = bool(RE_ARTURO.search(origin))
    vis = visibilita(origin) if origin and not origin_arturo else ""
    falliti, righe, esiti = [], [], []
    # Verso un remote non privato un file nuovo in commands, bin, hooks e nelle altre cartelle di Arturo è della
    # persona: i file di Arturo arrivano già tracciati da /aggiorna. Fino al 21/11/2026 "git add" li portava nel
    # commit e uscivano (revisione del 20/11, A3, #6249). Senza remote o verso Arturo il commit resta locale.
    remoto_aperto = bool(origin) and not origin_arturo and vis != "PRIVATE"
    nuovi_fermi = []
    for p in ARTURO:
        if (CL / p).exists():
            if remoto_aperto and (CL / p).is_dir():
                nuovi_fermi += [x for x in git("ls-files", "-z", "--others", "--exclude-standard", "--", p)[1]
                                .split("\0") if x]
                # "add -u" su una cartella senza file tracciati fallisce, con un messaggio tradotto nella lingua
                # di git: il controllo di aggiungi() legge solo quello inglese
                ok, err = aggiungi("-u", "--", p) if git("ls-files", "--", p)[1].strip() else (True, "")
            else:
                ok, err = aggiungi("--", p)
            if not ok:
                falliti.append(f"{p}: {ultima(err)}")
    if nuovi_fermi:
        righe.append(f"FILE TUOI NON SALVATI: {' '.join(nuovi_fermi[:10])}"
              + (f" e altri {len(nuovi_fermi) - 10}" if len(nuovi_fermi) > 10 else "")
              + f" - il remote della config non risulta privato (visibilità: {vis or 'sconosciuta'}). "
                "Restano su questa macchina.")
    if (CL / "skills").is_dir():
        nuove = git("ls-files", "--others", "--exclude-standard", "--directory", "--", "skills")[1].split()
        if vis == "PRIVATE" or origin_arturo or not origin:
            aggiungi("-u", "--", "skills")
            if nuove:
                aggiungi("--", "skills")
        else:
            # Verso un remote non privato resta fuori anche una skill della persona già tracciata e modificata:
            # fino al 21/11/2026 "git add -u" la portava nel commit, e una correzione scritta nella skill usciva
            # (#6277). Le skill di Arturo sono già pubbliche e passano. Senza l'elenco dei nomi restano tutte fuori.
            di_arturo = skill_di_arturo()
            modificate = set()
            for p in git("diff", "--name-only", "-z", "--", "skills")[1].split("\0"):
                pezzi = p.split("/")
                if len(pezzi) >= 3 and pezzi[1] not in di_arturo:
                    modificate.add(f"skills/{pezzi[1]}/")
                elif p:
                    aggiungi("-u", "--", p)
            ferme = nuove + sorted(modificate - set(nuove))
            if ferme:
                righe.append(f"SKILL TUE NON SALVATE: {' '.join(ferme)} - il remote della config non risulta privato "
                      f"(visibilità: {vis or 'sconosciuta'}). Restano su questa macchina.")
    saltati = {}
    if vis == "PRIVATE":
        ok, err = aggiungi_forzati(file_privati(CL, [p for p in PRIVATI if (CL / p).exists()], saltati))
        if not ok:
            falliti.append(f"{', '.join(PRIVATI)}: {ultima(err)}")
        # Gli handoff senza -f: una riga della persona nel .gitignore (un progetto riservato) va rispettata.
        if (CL / "data" / "handoffs").exists():
            aggiungi("-A", "--", "data/handoffs")
    else:
        esiti.append(f"CLAUDE.md, personale/, handoff, todo e memoria solo su questa macchina: il remote "
                     f"non risulta privato (visibilità: {vis or 'sconosciuta'})")
        if origin_arturo or not origin:
            for p in ("data/handoffs", "data/todo", "data/memory"):
                if git("ls-files", "--", p)[1].strip() and git("rm", "-r", "-q", "--cached", "--", p)[0] == 0:
                    esiti.append(f"{p} tolto dal tracciamento di git, i file restano su questa macchina")
    return {"origin": origin, "origin_arturo": origin_arturo, "vis": vis, "saltati": saltati,
            "falliti": falliti, "righe": righe, "esiti": esiti}


def da_salvare_fuori_data():
    """I file fuori da data/ che il commit di sync prenderebbe adesso: il passo 6 su una copia dell'indice, che
    poi sparisce. None se ~/.claude non ha git o la copia non riesce."""
    global ENV_GIT
    if not (CL / ".git").exists():
        return None
    indice = Path(git("rev-parse", "--git-path", "index")[1].strip())
    indice = indice if indice.is_absolute() else CL / indice
    fd, nome = tempfile.mkstemp(prefix="index.fine-avvisi-", dir=str(indice.parent))
    os.close(fd)
    copia = Path(nome)
    try:
        if indice.is_file():
            shutil.copy2(str(indice), str(copia))
        else:
            copia.unlink()  # senza indice git parte da un indice vuoto, come il commit vero
        ENV_GIT = dict(os.environ, GIT_INDEX_FILE=str(copia))
        if aggiungi_per_percorso()["falliti"]:
            return None
        rc, out, _ = git("diff", "--cached", "--name-only", "--no-renames", "-z")
        if rc != 0:
            return None
        return [p for p in out.split("\0") if p and not p.startswith("data/")]
    finally:
        ENV_GIT = None
        copia.unlink(missing_ok=True)


def cartella_sessioni():
    """Dove Claude Code scrive un file per ogni sessione viva (<pid>.json): FINE_CODA_SESSIONI per i banchi."""
    if os.environ.get("FINE_CODA_SESSIONI"):
        return Path(os.environ["FINE_CODA_SESSIONI"])
    return radice_orsa() / "sessions"


def viva(pid):
    """Il processo esiste ancora. Su Windows os.kill chiude il processo: lì vale il file della sessione."""
    if os.name == "nt":
        return True
    try:
        os.kill(int(pid), 0)
    except (ProcessLookupError, ValueError, TypeError):
        return False
    except PermissionError:
        return True
    except OSError:
        return False
    return True


# Una coda alla volta sulla stessa config: due /fine in parallelo si pestavano sull'indice di git, e una
# metteva nel suo commit i file dell'altra o li toglieva dallo stage (A4, revisione del 20/11/2026).
LUCCHETTO_VECCHIO = 1800  # secondi: oltre, il lucchetto è di una coda interrotta anche se il pid risulta vivo
_OCCUPATO = (FileExistsError, PermissionError) if os.name == "nt" else (FileExistsError,)


def file_lucchetto():
    return CL / "session-env" / "fine-coda.lock"


def prendi_lucchetto():
    """Il lucchetto della coda, o None se un'altra coda lo tiene oltre FINE_CODA_ATTESA secondi (300)."""
    file = file_lucchetto()
    try:
        file.parent.mkdir(parents=True, exist_ok=True)
    except OSError:
        return None
    try:
        attesa = float(os.environ.get("FINE_CODA_ATTESA") or 300)
    except ValueError:
        attesa = 300.0
    limite, avvisato = time.time() + attesa, False
    while True:
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
            eta, pid = 0, ""
        # Un pid scritto e morto, o un lucchetto troppo vecchio: è di una coda interrotta, si toglie.
        if eta > LUCCHETTO_VECCHIO or (pid.isdigit() and not viva(pid)):
            try:
                file.unlink()
            except FileNotFoundError:
                pass
            except OSError:
                return None
            continue
        if not avvisato:
            print(f"fine-coda: un'altra /fine sta salvando la config (pid {pid or '?'}), aspetto che finisca", flush=True)
            avvisato = True
        if time.time() > limite:
            return None
        time.sleep(0.5)


def lascia_lucchetto(file):
    """Toglie il lucchetto solo se è ancora di questo processo."""
    try:
        if file.read_text(encoding="ascii", errors="replace").split()[:1] == [str(os.getpid())]:
            file.unlink()
    except (OSError, IndexError):
        pass


def sessioni_vive():
    """Le altre sessioni vive su questa macchina: [{"id", "nome", "cwd"}], senza quella di CLAUDE_CODE_SESSION_ID."""
    mia = os.environ.get("CLAUDE_CODE_SESSION_ID", "").strip()
    out, visti = [], set()
    for f in sorted(cartella_sessioni().glob("*.json")):
        try:
            d = json.loads(f.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        sid = str(d.get("sessionId") or "")
        if not sid or sid == mia or sid in visti or not viva(d.get("pid", f.stem)):
            continue
        visti.add(sid)
        out.append({"id": sid, "nome": str(d.get("name") or ""), "cwd": str(d.get("cwd") or "")})
    return out


def trascrizione(sessione):
    """Il file .jsonl della sessione sotto projects/, accanto alla cartella delle sessioni, o None."""
    for f in (cartella_sessioni().parent / "projects").glob(f"*/{sessione['id']}.jsonl"):
        return f
    return None


def toccati(sessione, file):
    """I file (relativi a ~/.claude) che la sessione ha scritto con Edit, Write o NotebookEdit, o nominato in un
    comando di Bash. Un file cambiato da uno script lanciato senza nominarlo sfugge: in quel caso niente avviso."""
    tr = trascrizione(sessione)
    if not tr or not file:
        return []
    radice = CL.resolve()
    pieni = {(radice / r).as_posix(): r for r in file}
    home = Path.home().resolve()
    aghi = {}
    for r in file:
        aghi[(CL / r).as_posix()] = r
        aghi[(radice / r).as_posix()] = r
        try:
            sotto = (radice / r).relative_to(home).as_posix()
            aghi["~/" + sotto] = r
            aghi["$HOME/" + sotto] = r
        except ValueError:
            pass
    cwd = Path(sessione["cwd"]).expanduser() if sessione["cwd"] else None
    dentro = False
    if cwd:
        try:
            cwd.resolve().relative_to(radice)
            dentro = True
        except (ValueError, OSError):
            pass
    trovati = set()
    try:
        righe = tr.open(encoding="utf-8", errors="replace")
    except OSError:
        return []
    with righe:
        for riga in righe:
            if '"tool_use"' not in riga:
                continue
            try:
                contenuto = (json.loads(riga).get("message") or {}).get("content")
            except ValueError:
                continue
            for pezzo in contenuto if isinstance(contenuto, list) else []:
                if not isinstance(pezzo, dict) or pezzo.get("type") != "tool_use":
                    continue
                entrata = pezzo.get("input") or {}
                for chiave in ("file_path", "notebook_path"):
                    v = entrata.get(chiave)
                    if isinstance(v, str) and v:
                        p = Path(v).expanduser()
                        if not p.is_absolute() and cwd:
                            p = cwd / p
                        try:
                            p = p.resolve()
                        except OSError:
                            pass
                        if p.as_posix() in pieni:
                            trovati.add(pieni[p.as_posix()])
                comando = entrata.get("command")
                if isinstance(comando, str):
                    for ago, r in aghi.items():
                        if ago in comando:
                            trovati.add(r)
                    if dentro:
                        trovati.update(r for r in file if r in comando)
    return [r for r in file if r in trovati]


def avvisi():
    """--avvisi: a chi mandare l'avviso della FASE 9 prima della coda. Exit 0 con una riga AVVISA per sessione;
    exit 3 con una riga sola quando non c'è nessuno da avvisare."""
    file = da_salvare_fuori_data()
    if file is None:
        print("avvisi: niente anteprima del commit di sync (config senza git o indice non copiato): nessun avviso")
        return 3
    if not file:
        print("avvisi: nessun file della config fuori da data/ da salvare: nessun avviso")
        return 3
    righe = []
    for s in sessioni_vive():
        suoi = toccati(s, file)
        if suoi:
            nome = s["nome"] or "senza nome"
            righe.append(f"AVVISA {nome} (sessione {s['id'][:8]}): {', '.join(suoi[:10])}"
                         + (f" e altri {len(suoi) - 10}" if len(suoi) > 10 else ""))
    if not righe:
        print(f"avvisi: {len(file)} file da salvare fuori da data/, nessuna altra sessione viva li ha toccati: "
              "nessun avviso")
        return 3
    print("\n".join(righe))
    return 0


def main(argv):
    for flusso in (sys.stdout, sys.stderr):  # su Windows la pipe è in cp1252, chi legge vuole UTF-8
        if hasattr(flusso, "reconfigure"):
            flusso.reconfigure(encoding="utf-8", errors="replace")
    propri = argv[:argv.index("--")] if "--" in argv else argv
    suoi = argv[argv.index("--") + 1:] if "--" in argv else []
    ap = argparse.ArgumentParser(description="Coda di /fine")
    ap.add_argument("--handoff", help="default: l'handoff di questa sessione (CLAUDE_CODE_SESSION_ID)")
    ap.add_argument("--slug", help="default: la cartella dell'handoff")
    ap.add_argument("--trailer", action="append", default=[])
    ap.add_argument("--leggero", action="store_true",
                    help="fine leggero della rotazione: niente retention e niente segno del fine completo")
    ap.add_argument("--rotazione", action="store_true",
                    help="giro in rotazione (anche il completo delle 18): l'handoff non chiede /clear alla persona")
    ap.add_argument("--avvisi", action="store_true",
                    help="solo l'anteprima: quali altre sessioni vive avvisare, senza commit (exit 3: nessuna)")
    ap.error = lambda m: (sys.stderr.write(f"fine-coda: {m}\n"), sys.exit(5))
    a = ap.parse_args(propri)
    if a.avvisi:
        return avvisi()
    lucchetto = prendi_lucchetto()
    if lucchetto is None:
        print(f"fine-coda: un'altra /fine tiene ancora la config ({file_lucchetto()}), niente commit. Aspetta che "
              "finisca e rilancia la coda. Se nessuna /fine è in corso, cancella quel file.")
        return 8
    try:
        return coda(a, ap, suoi)
    finally:
        lascia_lucchetto(lucchetto)


def coda(a, ap, suoi):
    handoff =Path(a.handoff).expanduser().resolve() if a.handoff else handoff_della_sessione()
    if a.handoff and not handoff.is_file():
        ap.error(f"handoff assente: {handoff}")
    if handoff:
        try:
            handoff.resolve().relative_to((CL / "data" / "handoffs").resolve())
        except ValueError:
            ap.error(f"l'handoff non sta sotto {CL / 'data' / 'handoffs'}: {handoff}")
    slug = a.slug or (handoff.parent.name if handoff else "")
    if slug and ("/" in slug or "\\" in slug or slug.startswith(".")):
        ap.error(f"slug non valido: {slug}")
    base = {"handoff": str(handoff or ""), "slug": slug, "radice": str(CL), "argomenti": suoi}
    esiti, offline = [], False

    # 1. config integra. Un rebase fermo sui soli file derivati, lasciato da una coda di prima, si chiude.
    if rebase_a_meta() and not risolvi_derivati():
        print(STOP_REBASE)
        return 4
    controlla = CL / "hooks" / "controlla-config.py"
    if controlla.is_file():
        rc, out, err = run([PY, str(controlla), "--quiet"], 60)
        if rc != 0:
            print((out + err).strip())
            print("fine-coda: la config non è integra, niente commit. Sistemala prima (vedi sopra) e rilancia.")
            return 4

    if not handoff:
        # Senza handoff della sessione la coda fa solo il sync della config: /fine senza handoff, o un
        # salvataggio della config a mano.
        esiti.append("nessun handoff di questa sessione: solo il sync della config")
        extra = []
    else:
        # 2. gate: bloccante
        rc, out, err = run([BASH, str(QUI / "handoff-gate.sh"), str(handoff)], 60)
        if rc != 0:
            print((out + err).strip())
            print("fine-coda: gate ROSSO, niente commit. Correggi l'handoff e rilancia.")
            return 1
        esiti.append("gate verde")

        # 2b. rotazione: il passo dopo non chiede alla persona /clear e /inizio, li fa il tool ruota.
        # Con il mod spento (ARTURO_ROTAZIONE) quella richiesta è la chiusura giusta e resta.
        if (a.rotazione or a.leggero) and not rotazione_spenta(os.environ.get("ARTURO_ROTAZIONE")):
            righe = chiede_clear(handoff.read_text(encoding="utf-8", errors="replace"))
            if righe:
                print("fine-coda: ROTAZIONE rossa: l'handoff chiede alla persona /clear e /inizio. In rotazione "
                      "li fa il tool ruota (commands/fine.md, Modo rotazione).")
                for r in righe[:5]:
                    print(f"  {r}")
                print("Riscrivi il passo dopo: \"io faccio <passo>\" se è tuo, il gesto vero se è della persona. "
                      "Poi rilancia la coda.")
                return 1
            esiti.append("rotazione: il passo dopo non chiede /clear")

        # 3. retention: esce solo l'elenco del dry-run che /fine ha già letto. Il fine leggero della
        # rotazione non fa il triage della FASE 6: la retention aspetta il fine completo.
        if a.leggero:
            esiti.append("retention: al fine completo")
        else:
            esiti.append(retention(slug))
            # Il segno del fine completo: /fine --rotazione lo legge per promuoversi a completo una volta
            # al giorno. Sta accanto all'handoff ed entra nel commit con lui; il punto lo tiene fuori da
            # indice, retention e contesto, che leggono solo i file HANDOFF_*.md.
            oggi = date.today().isoformat()
            try:
                (handoff.parent / SEGNO_COMPLETO).write_text(f"{oggi}\n", encoding="utf-8")
                esiti.append(f"fine completo segnato: {oggi}")
            except OSError as e:
                esiti.append(f"segno del fine completo NON scritto: {e}")

        # 4. indice
        rc, out, err = run([PY, str(QUI / "index-rigenera.py"), "--scrivi", "--radice", str(CL / "data" / "handoffs")], 60)
        esiti.append("indice ok" if rc == 0 else f"indice NON rigenerato: {ultima(err, out)}")

        # 5. aggancio personale dopo l'indice
        e, extra, blocca, off = personale("dopo-index", base, [])
        esiti += e
        offline |= off
        if blocca:
            print(f"fine-coda: personale/fine-coda.py (dopo-index) blocca: {blocca}")
            return 4

    # 6. add per percorso
    if not (CL / ".git").exists():
        esiti.append("config senza git: niente commit")
        print("coda: " + " · ".join(esiti))
        return 3 if offline else 0
    p6 = aggiungi_per_percorso()
    for r in p6["righe"]:
        print(r)
    esiti += p6["esiti"]
    origin, origin_arturo, vis, saltati = p6["origin"], p6["origin_arturo"], p6["vis"], p6["saltati"]
    if p6["falliti"]:
        print("fine-coda: git add fallito su " + "; ".join(p6["falliti"]))
        return 6

    # 7. marcatori di conflitto
    staged = [p for p in git("diff", "--cached", "--name-only", "--no-renames", "-z")[1].split("\0") if p]
    con_marcatori = []
    if staged:
        diff = git("diff", "--cached", "--no-renames")[1]
        inizi = list(RE_FILE_DIFF.finditer(diff))
        for i, m in enumerate(inizi):
            pezzo = diff[m.end():inizi[i + 1].start() if i + 1 < len(inizi) else len(diff)]
            if RE_APRE.search(pezzo) and RE_CHIUDE.search(pezzo):
                con_marcatori.append(m.group(1))
    if con_marcatori:
        print("MARCATORI DI CONFLITTO: STOP. Nei file in stage ci sono righe <<<<<<< ======= >>>>>>>: "
              + ", ".join(con_marcatori[:10]) + (f" e altri {len(con_marcatori) - 10}" if len(con_marcatori) > 10 else ""))
        print("In un log o una lista tieni le due versioni, in una regola scegli, poi rilancia.")
        return 4

    # 8. aggancio personale prima del commit
    e, extra2, blocca, off = personale("prima-commit", base, staged)
    esiti += e
    offline |= off
    if blocca:
        print(f"fine-coda: personale/fine-coda.py (prima-commit) blocca: {blocca}")
        return 4
    extra = [p for p in dict.fromkeys(extra + extra2) if p and not p.startswith(("/", ".."))]
    if extra and vis != "PRIVATE":
        # personale/ e i .local sono ignorati da Arturo: senza un remote privato restano fuori
        rc, _, err = git("add", "-A", "--", *extra)
        if rc != 0:
            esiti.append(f"path dell'aggancio personale fuori dal commit: il remote non risulta privato")
        extra = []
    if extra:
        ok, err = aggiungi_forzati(file_privati(CL, extra, saltati))
        if not ok:
            print(f"fine-coda: git add fallito sui path dell'aggancio personale: {ultima(err)}")
            return 6
        staged = [p for p in git("diff", "--cached", "--name-only", "--no-renames", "-z")[1].split("\0") if p]

    if riga_saltati(saltati):
        esiti.append(riga_saltati(saltati))

    # 8b. segreti nello stage, dopo le aggiunte dell'aggancio personale: niente commit se la guardia trova una
    # chiave. Il commit a mano passa dalla guardia del dispatcher, che chiede conferma alla persona.
    guardia = guardia_segreti() if staged else None
    if staged:
        ferma = controlla_segreti(guardia, ("diff", "--cached", *DIFF), "commit né push",
                                  "Togli la chiave dal file (va nel vault o in una variabile d'ambiente), poi rilancia "
                                  "la coda. Se è un falso allarme, come la chiave finta di un test, fai il commit a mano "
                                  "con git -C ~/.claude commit: la guardia chiede conferma alla persona.")
        if ferma:
            print("\n".join(ferma))
            return 7
        esiti.append("segreti: nessuno nello stage")

    # 9. commit: la memoria a parte, così si annulla da sola
    trailer = "".join(f"\n{t}" for t in a.trailer)
    memoria = [p for p in staged if p.startswith("data/memory/")]
    resto = [p for p in staged if p not in memoria]
    # Commit dall'indice, mai "git commit -- <path>": con i path git riprende i file dal disco e annulla un
    # "rm --cached" (test F17). La memoria va prima, con una copia dell'indice senza il resto.
    indice = Path(git("rev-parse", "--git-path", "index")[1].strip())
    indice = indice if indice.is_absolute() else CL / indice
    for paths, msg, nome in ((memoria, "memoria: applicata da /fine", "commit memoria"),
                             (resto, f"chore: session sync {date.today()}", "commit")):
        if not paths:
            continue
        stat = git("diff", "--cached", "--stat", "--", *paths)[1].rstrip()
        messaggio = msg + ("\n" + trailer if trailer else "")
        if paths is memoria and resto:
            # Una copia col nome unico: con un nome fisso la coda di un'altra sessione la toglieva, e git legge
            # un indice assente come vuoto, quindi committava un albero senza file (review del 7/11, finding 27).
            fd, nome_copia = tempfile.mkstemp(prefix="index.fine-coda-", dir=str(indice.parent))
            os.close(fd)
            copia = Path(nome_copia)
            env = dict(os.environ, GIT_INDEX_FILE=str(copia))
            try:
                shutil.copy2(str(indice), str(copia))
                rc, out, err = run(["git", "-C", str(CL), "reset", "-q", "--", *resto], 120, env=env)
                if rc != 0 or not copia.is_file() or copia.stat().st_size == 0:
                    rc, out, err = rc or 1, out, f"copia dell'indice non pronta: {ultima(err, out)}"
                else:
                    rc, out, err = run(["git", "-C", str(CL), "commit", "-q", "-m", messaggio], 120, env=env)
            finally:
                copia.unlink(missing_ok=True)
        else:
            rc, out, err = git("commit", "-q", "-m", messaggio)
        if rc != 0:
            print(f"fine-coda: commit fallito: {ultima(err, out)}")
            return 6
        h = git("rev-parse", "--short", "HEAD")[1].strip()
        print(f"-- {nome} {h} --\n{stat}")
        esiti.append(f"{nome} {h}")
    if not staged:
        esiti.append("config: niente da committare")
    fuori = [r for r in git("status", "--short")[1].splitlines() if r.strip()]
    if fuori:
        print(f"-- fuori dal commit: {len(fuori)} righe di git status --")
        print("\n".join(fuori[:15]) + (f"\n... e altre {len(fuori) - 15}" if len(fuori) > 15 else ""))

    # 10. push
    if origin_arturo:
        esiti.append("config: solo locale, origin è il repository pubblico di Arturo (vedi /setup FASE 7)")
    elif not origin:
        esiti.append("config: solo locale, nessun remote origin")
    else:
        git("fetch", "-q", "origin", "main", timeout=90)
        avanti = git("rev-list", "--count", "origin/main..HEAD")[1].strip()
        if avanti == "0":
            esiti.append("config: niente da pushare")
        else:
            # Anche i commit fatti prima, fuori dalla coda o da un'altra sessione: il push li manda tutti.
            ferma = controlla_segreti(guardia or guardia_segreti(),
                                      ("log", "-p", "--format=", *DIFF, "HEAD", "--not", "--remotes=origin"),
                                      "push",
                                      "I commit restano su questa macchina. Se la chiave è vera, toglila dal file e dai "
                                      "commit non ancora spinti (li elenca git -C ~/.claude log origin/main..HEAD), poi "
                                      "rilancia la coda. Se è un falso allarme, fai il push a mano: la guardia chiede "
                                      "conferma alla persona.")
            if ferma:
                print("coda: " + " · ".join(esiti))
                print("\n".join(ferma))
                return 7
            ok, perche = push(origin)
            esiti.append("config: push riuscito" if ok else f"config: push non riuscito ({perche}), "
                         f"{avanti or '?'} commit da ritentare")

    print("coda: " + " · ".join(esiti))
    return 3 if offline else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
