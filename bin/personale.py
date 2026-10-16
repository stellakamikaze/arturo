"""arturo personale: le aggiunte della persona ai comandi e agli hook di sessione di Arturo, in file suoi.

Perché esiste: Arturo convive con la config personale. Chi cambia un comando di Arturo (per esempio
aggiunge a /inizio la tabella dei suoi progetti) modifica un file che ogni aggiornamento riscrive:
il merge va in conflitto e la config si rompe. Le aggiunte stanno invece in
~/.claude/personale/<comando>.md, fuori da git. Gli aggiornamenti non le toccano, e quando la
persona lancia /<comando> l'hook inject-now.sh dice a Claude di leggerle. Le righe aggiunte agli
hook di sessione stanno in ~/.claude/personale/session-start.sh (o session-end.sh), che l'hook di
Arturo esegue in fondo.

  elenco                  i file personali e i comandi di Arturo modificati in ~/.claude, e i file
                          personali di un comando che Arturo non ha più
  sposta commands/X.md    sposta le modifiche a /X in personale/X.md e riporta X.md com'era in Arturo
  sposta hooks/session-start.sh (o session-end.sh)
                          sposta le aggiunte all'hook in personale/<hook>.sh, COMMENTATE: l'hook di
                          Arturo esegue quel file in fondo, e le righe girano solo dopo una rilettura
  ripristina hooks/X      riporta una guardia (o un altro hook) com'è in Arturo, senza tenere le modifiche
  separa [--verso REF]    sposta i comandi di Arturo modificati (con --verso solo quelli che REF cambia);
                          /aggiorna lo lancia da solo nella copia di prova

Con un repository della persona come origin (Arturo come upstream), /aggiorna e /aggiorna personale
lanciano separa solo se quel repository è privato: altrimenti personale/ non viaggerebbe fra le sue
macchine. Il controllo sta in chi lancia separa: `sposta` a mano lo salta, e per questo `elenco`
indica /aggiorna personale.

`sposta` è meccanico: copia le parti aggiunte così come sono, con la riga di Arturo dopo cui stavano,
e le parti tolte sotto «Parti di Arturo che non seguo». Il riordino lo fa Claude con la persona.
Il confronto è con il punto in cui la config si è staccata da Arturo: merge-base con upstream/main
se esiste, altrimenti origin/main. Con upstream il ritorno del comando è un commit nuovo (/aggiorna
fa un merge). Senza, i commit locali vengono riscritti senza le modifiche al comando, perché il
rebase di /aggiorna li ripeterebbe uno per uno. Solo libreria standard, Python 3.8 o successivo.
"""
from __future__ import annotations

import difflib
import os
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
    return Path(os.environ.get("ARTURO_RADICE") or Path.home() / ".claude")


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
            dove = f"(dopo la riga di Arturo «{dopo}»)" if dopo else "(in cima al comando)"
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
            dove = f"# (dopo la riga di Arturo «{dopo}»)" if dopo else "# (in cima all'hook)"
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


def sposta(file: str, parla: bool = True) -> int:
    r = radice()
    m = NOME.match(file) or SESSIONE.match(file)
    if not m:
        print(f"Errore: si spostano solo i comandi di Arturo (commands/<nome>.md) e hooks/session-start.sh o "
              f"hooks/session-end.sh (non «{file}»).", file=sys.stderr)
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
    if attuale == vecchio.stdout:  # in byte: un file salvato con CRLF non e' «uguale»
        if parla:
            print(f"{file if e_hook else '/' + comando} e' gia' com'e' in Arturo: niente da spostare.")
        return 0
    destinazione = r / "personale" / (f"{comando}.sh" if e_hook else f"{comando}.md")
    gia = destinazione.read_text(encoding="utf-8") if destinazione.exists() else ""
    righe = (vecchio.stdout.decode("utf-8", "replace").splitlines(True), attuale.decode("utf-8", "replace").splitlines(True))
    testo = testo_hook(comando, *righe, gia) if e_hook else testo_personale(comando, *righe, gia)
    nome = file if e_hook else f"/{comando}"
    # Prima il file di Arturo e il commit, poi il file personale: se il commit non riesce (un hook, un
    # errore) il file torna com'era e niente resta a meta'.
    riporta(r, b, file, vecchio.stdout, attuale, f"personale: aggiunte a {nome} spostate in personale/{destinazione.name}")
    destinazione.parent.mkdir(parents=True, exist_ok=True)
    destinazione.write_text(testo, encoding="utf-8")
    if git(r, "ls-files", "--error-unmatch", "--", str(destinazione.relative_to(r))).returncode == 0:
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
        print(f"Errore: si ripristinano solo gli hook di Arturo, nella forma hooks/<nome> (non «{file}»).", file=sys.stderr)
        return 2
    if SESSIONE.match(file):
        print(f"Errore: per {file} usa «sposta»: tiene le tue aggiunte in personale/.", file=sys.stderr)
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
    if attuale == vecchio.stdout:
        print(f"{file} e' gia' com'e' in Arturo.")
        return 0
    riporta(r, b, file, vecchio.stdout, attuale, f"guardie: {file} riportato com'e' in Arturo")
    print(f"RIPRISTINATO: {file} e' di nuovo com'e' in Arturo, e il prossimo /aggiorna lo porta all'ultima versione.")
    return 0


def separa(verso: str = "") -> int:
    """Ogni comando di Arturo modificato va in personale/: /aggiorna lo lancia prima di applicare,
    solo se il repository della config è di Arturo o è privato (lo controlla chi lo lancia).

    Cosi' la persona non deve pensarci: le sue modifiche restano sue, il comando torna quello di
    Arturo e l'aggiornamento non va in conflitto. Senza comandi modificati non stampa niente.
    """
    r = radice()
    b = base(r)
    for file in (modificati(r, b, verso) if b else []):
        esito = sposta(file, parla=False)
        if esito != 0:
            return esito
    return 0


def elenco() -> int:
    r = radice()
    mie = sorted(list((r / "personale").glob("*.md")) + list((r / "personale").glob("*.sh")))
    print("File personali: " + (", ".join(f"personale/{f.name}" for f in mie) if mie else "nessuno"))
    # Un comando uscito da Arturo (16/10/2026: strato, progetto, discovery, write-plan, percorso)
    # lascia la sua aggiunta senza nessuno che la legga.
    orfani = [f for f in mie if f.suffix == ".md" and not (r / "commands" / f.name).exists()]
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


def main(argv: list) -> int:
    if not argv or argv[0] in ("-h", "--help", "aiuto", "help"):
        print(AIUTO)
        return 0
    if argv == ["elenco"]:
        return elenco()
    if argv[:1] == ["separa"] and (len(argv) == 1 or (len(argv) == 3 and argv[1] == "--verso")):
        try:
            return separa(argv[2] if len(argv) == 3 else "")
        except (OSError, subprocess.SubprocessError) as errore:
            print(f"Errore: {errore}", file=sys.stderr)
            return 2
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
    print(f"Errore: comando sconosciuto: «{' '.join(argv)}»\n\n{AIUTO}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    for flusso in (sys.stdout, sys.stderr):  # su Windows la pipe è in cp1252, Claude legge UTF-8
        try:
            flusso.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass
    raise SystemExit(main(sys.argv[1:]))
