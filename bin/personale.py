"""arturo personale: le aggiunte della persona ai comandi e agli hook di sessione di Arturo, in file suoi.

Perché esiste: Arturo convive con la config personale. Chi cambia un comando di Arturo (per esempio
aggiunge a /inizio la tabella dei suoi progetti) modifica un file che ogni aggiornamento riscrive:
il merge va in conflitto e la config si rompe. Le aggiunte stanno invece in
~/.claude/personale/<comando>.md, fuori da git. Gli aggiornamenti non le toccano, e quando la
persona lancia /<comando> l'hook inject-now.sh dice a Claude di leggerle. Le righe aggiunte agli
hook di sessione stanno in ~/.claude/personale/session-start.sh (o session-end.sh), che l'hook di
Arturo esegue in fondo.

  elenco                  i file personali e i comandi di Arturo modificati in ~/.claude, e i file
                          personali di un comando o di una skill che Arturo non ha più
  sposta commands/X.md    sposta le modifiche a /X in personale/X.md e riporta X.md com'era in Arturo
  sposta hooks/session-start.sh (o session-end.sh)
                          sposta le aggiunte all'hook in personale/<hook>.sh, COMMENTATE: l'hook di
                          Arturo esegue quel file in fondo, e le righe girano solo dopo una rilettura
  ripristina hooks/X      riporta una guardia (o un altro hook) com'è in Arturo, senza tenere le modifiche
  separa [--verso REF]    sposta i comandi di Arturo modificati (con --verso solo quelli che REF cambia);
                          /aggiorna lo lancia da solo nella copia di prova
  separa --senza-commit   scrive solo i file personali: i file di Arturo e git restano come sono. Lo usa
                          arturo migra, che poi toglie i file di Arturo da ~/.claude
  hook-precedenti [--applica]
                          gli hook, i plugin accesi e le impostazioni (model, env, apiKeyHelper) che la
                          persona aveva prima di Arturo, nell'ultima ~/.claude-backup-*: li elenca, e con
                          --applica li aggiunge al settings.json, coi file degli hook, senza togliere
                          niente di Arturo
  omonimi                 col plugin: le skill, i comandi e gli stili della persona che hanno lo stesso nome
                          di uno di Arturo. Il nome da solo porta a quello della persona, quello di Arturo diventa
                          arturo:<nome>; ogni sostituzione voluta si scrive in personale/sostituzioni.txt,
                          e un omonimo non dichiarato esce con 1
  regole-doppie [--togli] col plugin: le regole consigliate da /setup che il CLAUDE.md della persona ripete,
                          ora che il metodo di Arturo arriva all'avvio. Le elenca (esce 1 se ce ne sono);
                          con --togli le toglie, con la copia di prima in CLAUDE.md.prima-del-plugin

Con un repository della persona come origin (Arturo come upstream), /aggiorna e /aggiorna personale
lanciano separa solo se quel repository è privato: altrimenti personale/ non viaggerebbe fra le sue
macchine. Il controllo sta in chi lancia separa: `sposta` a mano lo salta, e per questo `elenco`
indica /aggiorna personale.

`sposta` è meccanico: copia le parti aggiunte così come sono, con la riga di Arturo dopo cui stavano,
e le parti tolte sotto "Parti di Arturo che non seguo". Il riordino lo fa Claude con la persona.
Il confronto è con il punto in cui la config si è staccata da Arturo: merge-base con upstream/main
se esiste, altrimenti origin/main. Con upstream il ritorno del comando è un commit nuovo (/aggiorna
fa un merge). Senza, i commit locali vengono riscritti senza le modifiche al comando, perché il
rebase di /aggiorna li ripeterebbe uno per uno. Solo libreria standard, Python 3.8 o successivo.
"""
from __future__ import annotations

import difflib
import json
import os
import shutil
import re
import subprocess
import sys
from pathlib import Path

AIUTO = __doc__.split("\n\n")[2] if __doc__ else ""
NOME = re.compile(r"^commands/([a-z0-9-]{1,40})\.md$")
# Gli hook di sessione dove le persone aggiungono righe: dal 16/10/2026 le aggiunte stanno in
# personale/<hook>.sh, che l'hook di Arturo esegue in fondo (task #3470, ciclo del lunedì).
SESSIONE = re.compile(r"^hooks/(session-start|session-end)\.sh$")
HOOK = re.compile(r"^hooks/[A-Za-z0-9_.-]{1,60}$")


def radice() -> Path:
    return Path(os.environ.get("ARTURO_RADICE") or os.environ.get("CLAUDE_CONFIG_DIR") or Path.home() / ".claude")


def git(r: Path, *argomenti, controlla: bool = False) -> subprocess.CompletedProcess:
    # utf-8 esplicito: con un locale cp1252 (Python di python.org su Windows) un comando con accenti
    # tornerebbe corrotto nel commit.
    return subprocess.run(["git", "-C", str(r), *argomenti], capture_output=True, text=True, encoding="utf-8",
                          errors="surrogateescape", timeout=30, check=controlla)


def byte(r: Path, *argomenti) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", str(r), *argomenti], capture_output=True, timeout=30)


def riferimento(r: Path):
    for ref in ("upstream/main", "origin/main"):
        if git(r, "rev-parse", "--verify", "--quiet", ref).returncode == 0:
            return ref
    return None


def base(r: Path):
    ref = riferimento(r)
    mb = git(r, "merge-base", "HEAD", ref) if ref else None
    return mb.stdout.strip() if mb and mb.returncode == 0 else None


def togli_dai_commit(r: Path, b: str, file: str) -> bool:
    """Riscrive i commit locali dopo b senza le modifiche a `file`. Vero se l'ha fatto.

    Serve quando Arturo è origin: /aggiorna fa un rebase, che ripete un commit alla volta, e il
    commit vecchio sul comando andrebbe in conflitto anche dopo lo spostamento. Il rebase riscrive
    già quei commit a ogni aggiornamento: sono solo su questo computer. Con un merge nel mezzo non
    tocca niente e torna falso.
    """
    commit = git(r, "rev-list", "--reverse", "--parents", f"{b}..HEAD").stdout.split("\n")
    commit = [c.split() for c in commit if c.strip()]
    if not commit or any(len(c) != 2 for c in commit):
        return False
    blob = git(r, "rev-parse", f"{b}:{file}", controlla=True).stdout.strip()
    modo = git(r, "ls-tree", b, "--", file, controlla=True).stdout.split()[0]
    # --git-path: nella copia di prova di /aggiorna .git è un file, non una cartella.
    percorso_git = git(r, "rev-parse", "--git-path", "arturo-personale-indice").stdout.strip()
    indice = r / percorso_git if percorso_git else r / ".git" / "arturo-personale-indice"  # relativo a r, o assoluto
    env = dict(os.environ, GIT_INDEX_FILE=str(indice))
    genitore = b
    try:
        for c, _ in commit:
            subprocess.run(["git", "-C", str(r), "read-tree", c], env=env, check=True, capture_output=True)
            subprocess.run(["git", "-C", str(r), "update-index", "--add", "--cacheinfo", f"{modo},{blob},{file}"], env=env,
                           check=True, capture_output=True)
            albero = subprocess.run(["git", "-C", str(r), "write-tree"], env=env, check=True, capture_output=True,
                                    text=True).stdout.strip()
            if albero == git(r, "rev-parse", f"{genitore}^{{tree}}").stdout.strip():
                continue  # il commit cambiava solo il comando: sparisce
            dati = git(r, "log", "-1", "--format=%an%x00%ae%x00%aI%x00%B", c, controlla=True).stdout.split("\x00", 3)
            autore = dict(GIT_AUTHOR_NAME=dati[0], GIT_AUTHOR_EMAIL=dati[1], GIT_AUTHOR_DATE=dati[2])
            genitore = subprocess.run(["git", "-C", str(r), "commit-tree", albero, "-p", genitore, "-m", dati[3].rstrip("\n")],
                                      env=dict(os.environ, **autore), check=True, capture_output=True, text=True).stdout.strip()
    finally:
        try:
            indice.unlink()
        except OSError:
            pass
    # Il comando nella cartella è già la versione di Arturo: si rimette quella di HEAD, così il reset
    # --keep (che non tocca mai modifiche non salvate) porta la versione di Arturo senza fermarsi.
    git(r, "checkout", "HEAD", "--", file, controlla=True)
    git(r, "reset", "-q", "--keep", genitore, controlla=True)
    return True


def senza_cr(dati: bytes) -> bytes:
    """Il testo con gli a capo LF. Su Windows core.autocrlf scrive i file del checkout con CRLF e il blob
    di git resta LF: confrontati in byte, ogni riga di un comando sembra cambiata e tutto il file finiva
    in personale/ come "aggiunte mie" (review del 7/11/2026, L10)."""
    return dati.replace(b"\r\n", b"\n")


def modificati(r: Path, b: str, verso: str = "") -> list:
    """I comandi di Arturo che la persona ha cambiato. Un comando cancellato è una sua scelta: resta
    fuori. Con `verso`, solo quelli che anche l'aggiornamento cambia: gli altri non vanno in conflitto
    e restano come lei li ha scritti."""
    albero = set(git(r, "ls-tree", "-r", "--name-only", b).stdout.splitlines())
    cambiati = [f for f in git(r, "diff", "--name-only", b).stdout.splitlines()
                if f in albero and (NOME.match(f) or SESSIONE.match(f)) and (r / f).exists()]
    if verso:
        arrivo = set(git(r, "diff", "--name-only", b, verso).stdout.splitlines())
        cambiati = [f for f in cambiati if f in arrivo]
    return sorted(cambiati)


def testo_personale(comando: str, originale: list, attuale: list, gia: str) -> str:
    aggiunte, tolte = [], []
    for op, i1, i2, j1, j2 in difflib.SequenceMatcher(a=originale, b=attuale, autojunk=False).get_opcodes():
        if op in ("insert", "replace"):
            dopo = next((x.strip() for x in reversed(originale[:i1]) if x.strip()), "")
            dove = f'(dopo la riga di Arturo "{dopo}")' if dopo else "(in cima al comando)"
            blocco = f"{dove}\n\n" + "".join(attuale[j1:j2]).rstrip("\n")
            if blocco not in gia:  # un secondo spostamento non ripete le stesse righe
                aggiunte.append(blocco)
        if op in ("delete", "replace"):
            blocco = "\n".join("> " + x.rstrip("\n") for x in originale[i1:i2])
            if blocco not in gia:
                tolte.append(blocco)
    parti = [gia.rstrip("\n") + "\n\n" if gia.strip() else
             f"# Aggiunte mie a /{comando}\n\nClaude legge questo file quando lanci /{comando}. Gli aggiornamenti di "
             "Arturo non lo toccano: e' tuo.\n\n"]
    if aggiunte:
        parti.append("## Aggiunte mie\n\n" + "\n\n".join(aggiunte) + "\n\n")
    if tolte:
        parti.append("## Parti di Arturo che non seguo\n\n" + "\n\n".join(tolte) + "\n\n")
    return "".join(parti).rstrip("\n") + "\n"


def testo_hook(hook: str, originale: list, attuale: list, gia: str) -> str:
    """Come testo_personale, ma per uno script: ogni riga spostata arriva commentata. Righe tolte dal
    loro posto (dentro un if, dopo una variabile) possono non funzionare, o fare altro: girano solo
    dopo che la persona le ha rilette con Claude e ha tolto il #."""
    blocchi = []
    for op, i1, i2, j1, j2 in difflib.SequenceMatcher(a=originale, b=attuale, autojunk=False).get_opcodes():
        if op in ("insert", "replace"):
            dopo = next((x.strip() for x in reversed(originale[:i1]) if x.strip()), "")
            dove = f'# (dopo la riga di Arturo "{dopo}")' if dopo else "# (in cima all'hook)"
            blocco = dove + "\n" + "".join("#   " + x.rstrip("\n") + "\n" for x in attuale[j1:j2]).rstrip("\n")
            if blocco not in gia:
                blocchi.append(blocco)
        if op in ("delete", "replace"):
            blocco = "# Riga di Arturo che avevi tolto:\n" + "\n".join("#   > " + x.rstrip("\n") for x in originale[i1:i2])
            if blocco not in gia:
                blocchi.append(blocco)
    testa = gia.rstrip("\n") + "\n\n" if gia.strip() else (
        f"# Aggiunte mie a hooks/{hook}.sh\n"
        f"# hooks/{hook}.sh di Arturo esegue questo file alla fine. Gli aggiornamenti non lo toccano: e' tuo.\n"
        "# Le righe qui sotto le ha spostate /aggiorna dal tuo hook, e sono commentate: rileggile con\n"
        "# Claude e togli il # a quelle che devono girare. Un errore qui non ferma la sessione.\n\n")
    return (testa + "\n\n".join(blocchi)).rstrip("\n") + "\n"


def riporta(r: Path, b: str, file: str, vecchio: bytes, attuale: bytes, messaggio: str) -> None:
    """Rimette `file` com'era al punto b di Arturo. Con Arturo come origin riscrive i commit locali
    senza le modifiche, così il rebase di /aggiorna non va in conflitto; altrimenti è un commit nuovo.
    Se il commit non riesce, il file torna com'era."""
    percorso = r / file
    percorso.write_bytes(vecchio)
    try:
        riscritti = riferimento(r) == "origin/main" and togli_dai_commit(r, b, file)
        if not riscritti:
            git(r, "add", "--", file, controlla=True)
            if git(r, "diff", "--cached", "--quiet", "--", file).returncode != 0:
                # --no-verify: il commit riporta un file di Arturo, gli hook della persona non c'entrano.
                git(r, "commit", "-q", "--no-verify", "-m", messaggio, "--", file, controlla=True)
    except (OSError, subprocess.SubprocessError):
        git(r, "reset", "-q", "--", file)
        percorso.write_bytes(attuale)
        raise


def sposta(file: str, parla: bool = True, commit: bool = True, r: Path | None = None) -> int:
    r = r or radice()
    m = NOME.match(file) or SESSIONE.match(file)
    if not m:
        print(f"Errore: si spostano solo i comandi di Arturo (commands/<nome>.md) e hooks/session-start.sh o "
              f'hooks/session-end.sh (non "{file}").', file=sys.stderr)
        return 2
    comando = m.group(1)
    e_hook = bool(SESSIONE.match(file))
    b = base(r)
    if not b:
        print("Errore: non trovo Arturo (upstream/main o origin/main) in ~/.claude.", file=sys.stderr)
        return 2
    vecchio = byte(r, "show", f"{b}:{file}")
    if vecchio.returncode != 0:
        print(f"Errore: {file} non e' un comando di Arturo.", file=sys.stderr)
        return 2
    percorso = r / file
    attuale = percorso.read_bytes() if percorso.exists() else b""
    if senza_cr(attuale) == senza_cr(vecchio.stdout):  # solo gli a capo diversi: niente di suo da spostare
        if parla:
            print(f"{file if e_hook else '/' + comando} e' gia' com'e' in Arturo: niente da spostare.")
        return 0
    destinazione = r / "personale" / (f"{comando}.sh" if e_hook else f"{comando}.md")
    gia = destinazione.read_text(encoding="utf-8") if destinazione.exists() else ""
    righe = tuple(senza_cr(x).decode("utf-8", "replace").splitlines(True) for x in (vecchio.stdout, attuale))
    testo = testo_hook(comando, *righe, gia) if e_hook else testo_personale(comando, *righe, gia)
    nome = file if e_hook else f"/{comando}"
    # Prima il file di Arturo e il commit, poi il file personale: se il commit non riesce (un hook, un
    # errore) il file torna com'era e niente resta a meta'. Senza commit (arturo migra) il file di
    # Arturo resta com'è: la migrazione lo porta via con gli altri.
    if commit:
        riporta(r, b, file, vecchio.stdout, attuale, f"personale: aggiunte a {nome} spostate in personale/{destinazione.name}")
    destinazione.parent.mkdir(parents=True, exist_ok=True)
    destinazione.write_text(testo, encoding="utf-8")
    if commit and git(r, "ls-files", "--error-unmatch", "--", str(destinazione.relative_to(r))).returncode == 0:
        # personale/ tracciato (remote privato, /fine fa git add -f): il file va nello stesso giro.
        git(r, "add", "-f", "--", str(destinazione.relative_to(r)), controlla=True)
        git(r, "commit", "-q", "--no-verify", "-m", f"personale: {nome}", "--", str(destinazione.relative_to(r)),
            controlla=True)
    if parla:
        print(f"Fatto: le modifiche a {nome} stanno in ~/.claude/personale/{destinazione.name} e {file} e' tornato com'e' in Arturo.\n"
              + ("Le righe sono commentate e non girano: rileggile con la persona e togli il # a quelle da tenere."
                 if e_hook else "Rileggi il file personale con la persona: le parti sono copiate cosi' come erano."))
    else:
        print(f"SEPARATO: {nome} -> personale/{destinazione.name}" + (" (righe commentate, da rileggere)" if e_hook else ""))
    return 0


def ripristina(file: str) -> int:
    """Riporta un hook di Arturo (di solito una guardia) com'è al punto in cui la config si è staccata
    da Arturo. Le modifiche della persona si perdono: lo si lancia solo col suo sì, dopo averle mostrate."""
    r = radice()
    if not HOOK.match(file) or ".." in file:
        print(f'Errore: si ripristinano solo gli hook di Arturo, nella forma hooks/<nome> (non "{file}").', file=sys.stderr)
        return 2
    if SESSIONE.match(file):
        print(f'Errore: per {file} usa "sposta": tiene le tue aggiunte in personale/.', file=sys.stderr)
        return 2
    b = base(r)
    if not b:
        print("Errore: non trovo Arturo (upstream/main o origin/main) in ~/.claude.", file=sys.stderr)
        return 2
    vecchio = byte(r, "show", f"{b}:{file}")
    if vecchio.returncode != 0:
        print(f"Errore: {file} non e' un hook di Arturo.", file=sys.stderr)
        return 2
    percorso = r / file
    attuale = percorso.read_bytes() if percorso.exists() else b""
    if senza_cr(attuale) == senza_cr(vecchio.stdout):
        print(f"{file} e' gia' com'e' in Arturo.")
        return 0
    riporta(r, b, file, vecchio.stdout, attuale, f"guardie: {file} riportato com'e' in Arturo")
    print(f"RIPRISTINATO: {file} e' di nuovo com'e' in Arturo, e il prossimo /aggiorna lo porta all'ultima versione.")
    return 0


def separa(verso: str = "", commit: bool = True, r: Path | None = None) -> int:
    """Ogni comando di Arturo modificato va in personale/: /aggiorna lo lancia prima di applicare,
    solo se il repository della config è di Arturo o è privato (lo controlla chi lo lancia).

    Cosi' la persona non deve pensarci: le sue modifiche restano sue, il comando torna quello di
    Arturo e l'aggiornamento non va in conflitto. Senza comandi modificati non stampa niente.
    """
    r = r or radice()
    b = base(r)
    for file in (modificati(r, b, verso) if b else []):
        esito = sposta(file, parla=False, commit=commit, r=r)
        if esito != 0:
            return esito
    return 0


def elenco() -> int:
    r = radice()
    mie = sorted(list((r / "personale").glob("*.md")) + list((r / "personale").glob("*.sh")))
    print("File personali: " + (", ".join(f"personale/{f.name}" for f in mie) if mie else "nessuno"))
    # Un comando uscito da Arturo (16/10/2026: strato, progetto, discovery, write-plan, percorso)
    # lascia la sua aggiunta senza nessuno che la legga.
    # Un file personale vale anche per una skill (docs/strati.md, "Estendere una skill senza copiarla"):
    # personale/humanizer.md è la voce della persona, e non va mai proposto da cancellare (4/11/2026, #4719).
    orfani = [f for f in mie if f.suffix == ".md" and not (r / "commands" / f.name).exists()
              and not (r / "skills" / f.stem / "SKILL.md").exists()]
    if orfani:
        print("Senza comando (Arturo non ha più /" + ", /".join(f.stem for f in orfani) + "): "
              + ", ".join(f"personale/{f.name}" for f in orfani)
              + ". Nessuno li legge più: rileggili con la persona, e lei decide se tenerli altrove o cancellarli.")
    b = base(r)
    cambiati = modificati(r, b) if b else []
    print("Comandi di Arturo modificati in ~/.claude: " + (", ".join(cambiati) if cambiati else "nessuno"))
    if cambiati:
        print("Per spostarli: /aggiorna personale (sposta solo se il tuo repository della config è privato)")
    return 0


# Le sostituzioni (docs/strati.md, "Estendere una skill senza copiarla"; strati F5, 5/11/2026). Col plugin una
# skill della persona con lo stesso nome di una di Arturo prende il nome nudo, e quella di Arturo resta come
# arturo:<nome> (prova del 2/11/2026). Voluto, è il modo di tenere la propria /inizio; non voluto, è una
# skill nuova di Arturo che la persona non vedrà mai. Per questo ogni sostituzione si dichiara.
SOSTITUZIONI = "personale/sostituzioni.txt"


def _nome_stile(file: Path) -> str:
    """Il name: del frontmatter di uno stile di output, o il nome del file."""
    try:
        righe = file.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeDecodeError):
        return file.stem
    if righe[:1] == ["---"]:
        for riga in righe[1:40]:
            if riga.strip() == "---":
                break
            if riga.startswith("name:"):
                return riga[5:].strip().strip("\"'") or file.stem
    return file.stem


def nomi(cartella: Path, codice: Path | None = None) -> dict:
    """nome -> percorso relativo, per skill, comandi e stili di una cartella. Con codice, un elemento che
    punta dentro il codice di Arturo (il link di un mod, una skill collegata) non è della persona."""
    trovati = {}
    elementi = [(f.parent, f.parent.name, f"skills/{f.parent.name}") for f in sorted(cartella.glob("skills/*/SKILL.md"))]
    elementi += [(f, f.stem, f"commands/{f.name}") for f in sorted(cartella.glob("commands/*.md"))]
    elementi += [(f, _nome_stile(f), f"output-styles/{f.name}") for f in sorted(cartella.glob("output-styles/*.md"))]
    for percorso, nome, rel in elementi:
        if codice is not None:
            vero = Path(os.path.realpath(percorso))
            if vero == codice or codice in vero.parents:
                continue
        trovati.setdefault(nome, rel)
    return trovati


def dichiarate(r: Path) -> list:
    """I nomi di personale/sostituzioni.txt, uno per riga; quello che segue # è il motivo."""
    try:
        testo = (r / SOSTITUZIONI).read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return []
    return [riga.split("#", 1)[0].strip().lstrip("/") for riga in testo.splitlines()
            if riga.split("#", 1)[0].strip()]


def omonimi(r: Path | None = None, codice: Path | None = None) -> int:
    r = r or radice()
    codice = Path(os.path.realpath(codice or Path(__file__).resolve().parent.parent))
    if Path(os.path.realpath(r)) == codice:
        print("OMONIMI: Arturo è un clone in ~/.claude, le skill sono le stesse: niente da controllare.")
        return 0
    di_arturo = nomi(codice)
    della_persona = nomi(r, codice)
    comuni = sorted(set(di_arturo) & set(della_persona))
    voluti = dichiarate(r)
    esito = 0
    sostituiti = [n for n in comuni if n in voluti]
    if sostituiti:
        print("SOSTITUITI: " + ", ".join(f"{n} (Arturo: arturo:{n})" for n in sostituiti))
    for n in comuni:
        if n not in voluti:
            esito = 1
            print(f"OMONIMO NON DICHIARATO: {n} è sia tuo ({della_persona[n]}) sia di Arturo ({di_arturo[n]}). "
                  f"Il nome da solo porta al tuo, per quello di Arturo scrivi arturo:{n}. Se è voluto, scrivi {n} in "
                  f"~/.claude/{SOSTITUZIONI}; altrimenti cambia nome al tuo.")
    for n in voluti:
        if n not in comuni:
            esito = 1
            dove = "Arturo non ha più " + n if n in della_persona else "non hai più un tuo " + n
            print(f"DICHIARATO SENZA OMONIMO: {n} sta in {SOSTITUZIONI}, ma {dove}: togli la riga.")
    if not comuni and not voluti:
        print("OMONIMI: nessuno, le tue skill hanno nomi diversi da quelle di Arturo.")
    return esito


# Le regole consigliate da /setup (shared/setup-claude-md.md) finivano nel CLAUDE.md della persona. Col plugin
# arrivano già col metodo all'avvio (hooks/metodo.sh): nel CLAUDE.md sono doppie (#4874, 6/11/2026). Il CLAUDE.md
# è della persona, quindi si elencano sempre e si tolgono solo con --togli. Si toglie solo una riga uguale per
# intero a una regola consigliata. Una riga con lo stesso inizio può dire il contrario, o avere un seguito rientrato:
# si elenca e resta (revisione del 6/11/2026).
INIZIO_REGOLA = 45  # caratteri dell'inizio di una regola che bastano a dire che una riga le somiglia
REGOLA = re.compile(r'^\d+\. "(.*?)"(?: \(|$)')


def regole_consigliate(codice: Path) -> list:
    """Il testo fra virgolette di ogni regola numerata di shared/setup-claude-md.md: va nel file così.
    Una regola può avere virgolette dentro: finisce a quelle prima della parentesi o a fine riga."""
    try:
        righe = (codice / "shared" / "setup-claude-md.md").read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeDecodeError):
        return []
    return [m.group(1) for m in map(REGOLA.match, righe) if m]


def righe_doppie(testo: str, regole: list) -> tuple:
    """(doppie, simili): gli indici delle righe uguali a una regola consigliata, e di quelle che solo le somigliano."""
    piano = lambda s: re.sub(r"\s+", " ", s).strip()
    intere = {piano(r) for r in regole}
    inizi = [piano(r)[:INIZIO_REGOLA] for r in regole]
    righe = testo.splitlines()
    doppie, simili = [], []
    for i, riga in enumerate(righe):
        nuda = piano(re.sub(r"^\s*(?:[-*+]|\d+[.)])\s+", "", riga))
        seguito = i + 1 < len(righe) and righe[i + 1][:1] in (" ", "\t") and righe[i + 1].strip()
        if nuda in intere and not seguito:
            doppie.append(i)
        elif any(inizio in nuda for inizio in inizi):
            simili.append(i)
    return doppie, simili


def regole_doppie(togli: bool = False, r: Path | None = None, codice: Path | None = None) -> int:
    r = r or radice()
    codice = Path(os.path.realpath(codice or Path(__file__).resolve().parent.parent))
    if Path(os.path.realpath(r)) == codice:
        print("REGOLE: Arturo è un clone in ~/.claude, il metodo non arriva all'avvio: le regole del CLAUDE.md servono.")
        return 0
    file = r / "CLAUDE.md"
    try:
        # newline="": gli a capo restano quelli del file, anche CRLF.
        with open(file, encoding="utf-8", newline="") as f:
            testo = f.read()
    except (OSError, UnicodeDecodeError):
        print("REGOLE: non c'è un CLAUDE.md, niente da controllare.")
        return 0
    doppie, simili = righe_doppie(testo, regole_consigliate(codice))
    righe = testo.splitlines(keepends=True)
    if simili:
        print(f"REGOLE SIMILI: {len(simili)} righe somigliano a una regola del metodo ma non sono uguali. Restano, "
              "le guardi tu:")
        for i in simili:
            print(f"  riga {i + 1}: {righe[i].strip()[:90]}")
    if not doppie:
        print("REGOLE: il tuo CLAUDE.md non ripete le regole che il plugin porta all'avvio.")
        return 0
    if not togli:
        print(f"REGOLE DOPPIE: {len(doppie)} righe del tuo CLAUDE.md ripetono il metodo che il plugin porta all'avvio:")
        for i in doppie:
            print(f"  riga {i + 1}: {righe[i].strip()[:90]}")
        print("Per toglierle (con una copia di prima): arturo personale regole-doppie --togli")
        return 1
    # Una copia per giro: la prima non si riscrive, e un giro dopo ha la sua.
    copia = r / "CLAUDE.md.prima-del-plugin"
    n = 2
    while copia.exists():
        copia = r / f"CLAUDE.md.prima-del-plugin.{n}"
        n += 1
    shutil.copy2(file, copia)
    with open(file, "w", encoding="utf-8", newline="") as f:
        f.write("".join(x for i, x in enumerate(righe) if i not in set(doppie)))
    print(f"REGOLE: tolte {len(doppie)} righe dal tuo CLAUDE.md; quello di prima è in {copia.name}.")
    return 0


# Un percorso dentro ~/.claude in un comando di hook: ~/.claude/x, $HOME/.claude/x, ${HOME}/.claude/x.
DENTRO = re.compile(r"(?:~|\$HOME|\$\{HOME\})/\.claude/([A-Za-z0-9_./-]+)")


def comandi(impostazioni: dict) -> set:
    """(evento, matcher, comando) di ogni hook dichiarato."""
    visti = set()
    for evento, gruppi in (impostazioni.get("hooks") or {}).items():
        for gruppo in gruppi if isinstance(gruppi, list) else []:
            for h in gruppo.get("hooks") or [] if isinstance(gruppo, dict) else []:
                if isinstance(h, dict) and h.get("command"):
                    visti.add((evento, gruppo.get("matcher"), h["command"]))
    return visti


# Le impostazioni del settings.json di prima che l'installazione lascia nella copia (revisione del
# 1/11/2026, I3): settings.json è un file di Arturo, e il reset lo sostituisce. I plugin restano
# installati in ~/.claude/plugins, ma il loro stato acceso sta in enabledPlugins; model, env e
# apiKeyHelper decidono modello e accesso (ANTHROPIC_BASE_URL, CLAUDE_CODE_USE_BEDROCK).
DIZIONARI = ("enabledPlugins", "extraKnownMarketplaces", "env")
VALORI = ("model", "apiKeyHelper")


def impostazioni_precedenti(vecchie: dict, attuali: dict) -> dict:
    """Le voci della copia che il settings.json di Arturo non ha. Solo aggiunte: una chiave che Arturo
    ha già resta la sua. Le righe non stampano i valori di env e apiKeyHelper, che possono essere
    chiavi: si legge solo il nome."""
    righe, unisci, plugin, altre = [], {}, 0, 0
    for chiave in DIZIONARI:
        prima, ora = vecchie.get(chiave), attuali.get(chiave)
        if not isinstance(prima, dict) or (ora is not None and not isinstance(ora, dict)):
            continue
        mancanti = {k: v for k, v in prima.items() if k not in (ora or {})}
        if not mancanti:
            continue
        unisci[chiave] = mancanti
        for nome in sorted(mancanti):
            if chiave == "enabledPlugins":
                plugin += 1
                righe.append(f"PLUGIN: {nome}" + ("" if mancanti[nome] else " (era spento)"))
            elif chiave == "extraKnownMarketplaces":
                altre += 1
                righe.append(f"PLUGIN: marketplace {nome}")
            else:
                altre += 1
                righe.append(f"IMPOSTAZIONE: env {nome}")
    for chiave in VALORI:
        valore = vecchie.get(chiave)
        if isinstance(valore, str) and valore and chiave not in attuali:
            unisci[chiave] = valore
            altre += 1
            righe.append(f"IMPOSTAZIONE: model {valore}" if chiave == "model"
                         else "IMPOSTAZIONE: apiKeyHelper (il comando che dà la chiave di accesso)")
    return {"righe": righe, "unisci": unisci, "plugin": plugin, "impostazioni": altre}


def hook_precedenti(applica: bool) -> int:
    """Gli hook che la persona aveva prima di Arturo (#3758, dal Computer Club il 16/10/2026).

    L'installazione mette da parte ~/.claude in ~/.claude-backup-<data> e riporta login, sessioni e
    plugin, ma non il settings.json: gli hook di un'altra app (ClaudeBar, per esempio) sparivano senza
    avviso. Qui si confronta l'ultima copia con il settings.json di Arturo. Con --applica gli hook
    mancanti si aggiungono, con lo stesso evento e lo stesso matcher, e tornano i file che usano dentro
    ~/.claude. La barra in basso è una sola: se era diversa si dice, e sceglie la persona.
    Dal 1/11/2026 tornano anche i plugin accesi, i marketplace, model, env e apiKeyHelper
    (impostazioni_precedenti): righe PLUGIN e IMPOSTAZIONE, mai coi valori di env.

    I file tornano al loro percorso di prima e /fine li salva con settings.json (#3803, 22/10/2026).
    Restano lì perché l'altra app li cerca e li aggiorna in quel punto. Viaggiano nel commit perché
    settings.json li nomina: su un'altra macchina senza il file, controlla-config.py direbbe config
    rotta, e un hook PreToolUse mancante esce con 2 e blocca ogni azione."""
    r = radice()
    copie = sorted(p for p in r.parent.glob(r.name + "-backup-*/settings.json") if p.is_file())
    if not copie:
        print("Nessuna config precedente: non c'è una ~/.claude-backup-* con un settings.json.")
        return 0
    copia = copie[-1]
    try:
        vecchie = json.loads(copia.read_text(encoding="utf-8"))
        attuali = json.loads((r / "settings.json").read_text(encoding="utf-8"))
    except (OSError, ValueError) as errore:
        print(f"Errore: non leggo {copia} o il settings.json di Arturo: {errore}", file=sys.stderr)
        return 2
    gia = comandi(attuali)
    nuovi = sorted((c for c in comandi(vecchie) if c not in gia), key=lambda c: (c[0], c[1] or "", c[2]))
    assoluto = re.compile(re.escape(str(r)) + r"/([A-Za-z0-9_./-]+)")  # /Users/x/.claude/x
    file = sorted({m for _, _, comando in nuovi for m in DENTRO.findall(comando) + assoluto.findall(comando)
                   if ".." not in m and (copia.parent / m).is_file() and not (r / m).exists()})
    barra = vecchie.get("statusLine")
    extra = impostazioni_precedenti(vecchie, attuali)
    print(f"Config precedente: {copia.parent}")
    if not nuovi:
        print("Hook da riportare: nessuno, quelli che avevi ci sono già.")
    for evento, matcher, comando in nuovi:
        print(f"HOOK: {evento}{' [' + matcher + ']' if matcher else ''}: {comando}")
    for m in file:
        print(f"FILE: ~/.claude/{m}")
    for riga in extra["righe"]:
        print(riga)
    if barra and barra != attuali.get("statusLine"):
        print(f"BARRA: avevi una barra in basso tua ({json.dumps(barra, ensure_ascii=False)}). Ce n'è una sola: "
              "quella di Arturo mostra contesto e quota. Se la persona vuole la sua, Claude la mette con lei.")
    da_fare = bool(nuovi or extra["righe"])
    if not applica or not da_fare:
        if da_fare:
            print("Per riportarli: python3 ~/.claude/bin/arturo personale hook-precedenti --applica")
        return 0
    for chiave, valori in extra["unisci"].items():
        if isinstance(valori, dict):
            attuali.setdefault(chiave, {}).update(valori)
        else:
            attuali[chiave] = valori
    for m in file:
        (r / m).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(str(copia.parent / m), str(r / m))
    tutti = attuali.setdefault("hooks", {})
    for evento, gruppi in (vecchie.get("hooks") or {}).items():
        for gruppo in gruppi if isinstance(gruppi, list) else []:
            if not isinstance(gruppo, dict):
                continue
            matcher = gruppo.get("matcher")
            da_aggiungere = [h for h in gruppo.get("hooks") or []
                             if isinstance(h, dict) and (evento, matcher, h.get("command")) in nuovi]
            if not da_aggiungere:
                continue
            lista = tutti.setdefault(evento, [])
            stesso = next((g for g in lista if isinstance(g, dict) and g.get("matcher") == matcher), None)
            if stesso is None:
                stesso = {"matcher": matcher, "hooks": []} if matcher is not None else {"hooks": []}
                lista.append(stesso)
            stesso.setdefault("hooks", []).extend(da_aggiungere)
    (r / "settings.json").write_text(json.dumps(attuali, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    parti = [f"{len(nuovi)} hook"]
    if extra["plugin"]:
        parti.append(f"{extra['plugin']} plugin")
    if extra["impostazioni"]:
        parti.append(f"{extra['impostazioni']} impostazioni")
    print(f"RIPORTATI: {', '.join(parti)} nel settings.json" + (f" e {len(file)} file" if file else "")
          + ". Valgono dalla prossima sessione di Claude Code.")
    return 0


def main(argv: list) -> int:
    if not argv or argv[0] in ("-h", "--help", "aiuto", "help"):
        print(AIUTO)
        return 0
    if argv == ["elenco"]:
        return elenco()
    if argv == ["omonimi"]:
        return omonimi()
    if argv[:1] == ["regole-doppie"] and argv[1:] in ([], ["--togli"]):
        return regole_doppie(argv[1:] == ["--togli"])
    if argv == ["separa", "--senza-commit"]:
        try:
            return separa(commit=False)
        except (OSError, subprocess.SubprocessError) as errore:
            print(f"Errore: {errore}", file=sys.stderr)
            return 2
    if argv[:1] == ["separa"] and (len(argv) == 1 or (len(argv) == 3 and argv[1] == "--verso")):
        try:
            return separa(argv[2] if len(argv) == 3 else "")
        except (OSError, subprocess.SubprocessError) as errore:
            print(f"Errore: {errore}", file=sys.stderr)
            return 2
    if argv[:1] == ["hook-precedenti"] and argv[1:] in ([], ["--applica"]):
        return hook_precedenti(argv[1:] == ["--applica"])
    if len(argv) == 2 and argv[0] == "ripristina":
        try:
            return ripristina(argv[1])
        except (OSError, subprocess.SubprocessError) as errore:
            print(f"Errore: {errore}", file=sys.stderr)
            return 2
    if len(argv) == 2 and argv[0] == "sposta":
        try:
            return sposta(argv[1])
        except (OSError, subprocess.SubprocessError) as errore:
            print(f"Errore: {errore}", file=sys.stderr)
            return 2
    print(f"Errore: comando sconosciuto: \"{' '.join(argv)}\"\n\n{AIUTO}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    for flusso in (sys.stdout, sys.stderr):  # su Windows la pipe è in cp1252, Claude legge UTF-8
        try:
            flusso.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass
    raise SystemExit(main(sys.argv[1:]))
