"""I programmi che un comando Bash esegue davvero (9/10/2026).

Una guardia che guarda il testo con una regex e la prima parola del segmento non
vede un programma scritto col path completo (`/bin/rm`), dentro un blocco `{ }`,
dopo `then`/`do` o passato a `bash -c`. Qui si ricava, segmento per segmento, il
programma vero: senza assegnazioni, parole chiave e wrapper davanti, col solo
nome del binario, e rientrando nel testo di `sh -c` ed `eval`.

Qui sta anche il tokenizer comune (`testo_shell`, `segmenti_parole`), che rispetta le
virgolette e toglie i corpi degli heredoc quotati verso non-shell: block-dangerous.py lo
carica da qui. Questo file non carica block-dangerous.py: fino al 15/10/2026 i due file
si caricavano a vicenda.

Usato da block-dangerous.py (rm e find che cancellano), commit-secret-gate.py (le shell),
cred-read-internal.py e protect_claude_md.py dove ci sono, e dal dispatcher: git puro,
ramo memoria e handoff, ramo ~/.claude, script e scritture sulla config.
Solo libreria standard.
"""
import importlib.util
import os
import re
import shlex

# Gli heredoc li riconosce heredoc.py, lo stesso modulo delle altre guardie (15/10/2026).
# Se manca, nessun corpo sparisce: la guardia controlla tutto il testo.
try:
    _spec_hd = importlib.util.spec_from_file_location(
        "heredoc", os.path.join(os.path.dirname(os.path.abspath(__file__)), "heredoc.py"))
    _hd = importlib.util.module_from_spec(_spec_hd)
    _spec_hd.loader.exec_module(_hd)
    _togli_heredoc = _hd.togli
except Exception:
    def _togli_heredoc(cmd, via, segnaposto=None):
        return cmd

    class _hd:  # noqa: N801 - senza heredoc.py nessun messaggio e nessun corpo si svuota
        INTERPRETI = frozenset("python python3 node ruby perl php".split())

        @staticmethod
        def fuori_virgolette(testo, pos):
            return False

        @staticmethod
        def togli(cmd, via, segnaposto=None):
            return cmd

        @staticmethod
        def percorsi_python(h):
            return None

# Valore di -m / --message: git non lo esegue, e un messaggio di commit che CITA
# un comando non è quel comando. Restano i messaggi con command-substitution.
_MESSAGGIO = re.compile(r"(?:^|\s)(?:-m|--message)[= ]\s*(['\"])((?:(?!\1).)*)\1", re.DOTALL)


def testo_shell(command: str) -> str:
    """Il comando senza il testo che la shell non legge come comandi.

    Toglie il corpo degli heredoc col delimitatore TRA VIRGOLETTE diretti a un
    lettore (cat, tee, grep...) o a un interprete (python, node...) il cui codice
    non lancia programmi: la shell non lo espande e non lo esegue, quindi un
    `cat <segreto>` scritto lì dentro è testo, non una lettura. Un heredoc senza
    virgolette resta, perché la shell ne espande le `$(...)`. Il confine lo legge
    heredoc.py. Toglie anche i messaggi -m/--message privi di command-substitution.
    """
    # Un corpo verso bash, sh, ssh (anche `cat <<'EOF' | bash`) resta: la shell lo esegue.
    testo = _togli_heredoc(command, lambda h: h.quotato and (h.inerte() or h.codice_inerte()))

    def _svuota(m):
        corpo = m.group(2)
        if "$(" in corpo or "`" in corpo:
            return m.group(0)
        # Solo il messaggio vero di git commit/tag, fuori da altre virgolette: `echo ' -m "'` non lo è.
        inizio = m.start(1)
        if not _hd.fuori_virgolette(testo, inizio) or not re.search(r"\bgit\b[^;&|\n]*$", testo[:inizio]):
            return m.group(0)
        return m.group(0).replace(corpo, "")

    return _MESSAGGIO.sub(_svuota, testo)


def segmenti_parole(cmd: str):
    """Segmenti come liste di parole, rispettando le virgolette.

    Un pattern di grep o uno script sed che contiene `|` o spazi non spezza il
    comando. Se le virgolette non tornano, ricade su uno split semplice.
    """
    try:
        lexer = shlex.shlex(cmd, posix=True, punctuation_chars=";&|()\n")
        lexer.whitespace = " \t\r"
        lexer.whitespace_split = True
        segmenti, corrente = [], []
        for tok in lexer:
            if tok and set(tok) <= set(";&|()\n"):
                if corrente:
                    segmenti.append(corrente)
                corrente = []
            else:
                corrente.append(tok)
        if corrente:
            segmenti.append(corrente)
        return segmenti
    except ValueError:
        def parole(seg):
            try:
                return shlex.split(seg)
            except ValueError:
                return seg.split()
        return [parole(seg) for seg in re.split(r"[|;&\n]+", cmd)]


_ASSEGNAZIONE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=")
# Parole che stanno davanti al programma senza esserlo.
_DAVANTI = frozenset("! { } then do else elif if while until time fi done esac".split())
# Intestazioni che non eseguono niente: `for x in a b`, `case $x in`.
_INTESTAZIONI = frozenset("for case select".split())
# Wrapper che eseguono il comando che segue; le loro opzioni si saltano.
_WRAPPER = frozenset("command builtin exec nohup nice env sudo caffeinate".split())
SHELL = frozenset("sh bash zsh dash ksh fish".split())


def _nome(parola: str) -> str:
    return os.path.basename(parola.lstrip("\\"))


def programmi(cmd: str, profondita: int = 0):
    """Lista di (programma, argomenti) per ogni comando semplice di `cmd`."""
    return [(_nome(t), a) for t, a in comandi(cmd, profondita)]


def comandi(cmd: str, profondita: int = 0):
    """Come programmi(), ma col programma scritto come nel comando (path compreso)."""
    out = []
    for toks in segmenti_parole(testo_shell(cmd)):
        i = 0
        while i < len(toks):
            t = toks[i]
            if t in _DAVANTI or _ASSEGNAZIONE.match(t):
                i += 1
            elif re.match(r"^\d*[<>]", t):
                # redirezione in testa (`<file`, `2>`, `$(<file)`): non è un programma
                i += 1 if len(t.lstrip("0123456789<>&")) else 2
            elif _nome(t) in _WRAPPER:
                i += 1
                while i < len(toks) and (toks[i].startswith("-") or toks[i].isdigit() or _ASSEGNAZIONE.match(toks[i])):
                    i += 1
            else:
                break
        # `2>&1` si spezza in `2>`, `&`, `1`: un numero da solo non è un programma.
        if i >= len(toks) or toks[i] in _INTESTAZIONI or toks[i].isdigit():
            continue
        prog, args = _nome(toks[i]), toks[i + 1:]
        out.append((toks[i], args))
        if profondita < 3:
            if prog in SHELL and "-c" in args and args.index("-c") + 1 < len(args):
                out += comandi(args[args.index("-c") + 1], profondita + 1)
            elif prog == "eval" and args:
                out += comandi(" ".join(args), profondita + 1)
    return out


def _ricorsivo(args) -> bool:
    return any(a == "--recursive" or (a.startswith("-") and not a.startswith("--") and "r" in a.lower()) for a in args)


# Redirezione in scrittura: `>f`, `2>>f`, `&>f`, `>|f`. Il gruppo 2 è il bersaglio, vuoto se staccato.
_REDIREZIONE = re.compile(r"^\d*(>>?|&>>?|>\|)(.*)$")


# --- Variabili del comando (19/10/2026) ---
# `SP=/private/tmp/x; python3 $SP/hook.py`: la variabile assegnata nel comando stesso si
# espande, poi quella dell'ambiente. Le stesse regole di block-dangerous.py, copiate qui
# perché questo file non carica block-dangerous.py.
_VAR_RE = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)(:?[-=])([^}]*)\}|\$\{([A-Za-z_][A-Za-z0-9_]*)\}|\$([A-Za-z_][A-Za-z0-9_]*)")
_ASSEGNAZIONE_CMD_RE = re.compile(r"""(?:^|(?<=[\s;&|(]))([A-Za-z_][A-Za-z0-9_]*)=("([^"]*)"|'([^']*)'|[^\s;&|()]*)""")


def _assegnazioni(command: str) -> dict:
    """Le variabili assegnate nel comando, in ordine (vince l'ultima), col valore grezzo."""
    out = {}
    for m in _ASSEGNAZIONE_CMD_RE.finditer(command):
        grezzo = m.group(3) if m.group(3) is not None else (m.group(4) if m.group(4) is not None else m.group(2))
        out[m.group(1)] = grezzo
    return out


def _espandi_variabili(t: str, assegnate: dict):
    """Espande le variabili: prima quelle assegnate nel comando, poi l'ambiente. None se resta
    qualcosa che non si risolve (`$(...)`, backtick, variabile non definita)."""
    def rep(m):
        name = m.group(1) or m.group(4) or m.group(5)
        if name in assegnate:
            val = os.path.expanduser(assegnate[name]) if assegnate[name].startswith("~") else assegnate[name]
        else:
            val = os.path.expanduser("~") if name == "HOME" else os.environ.get(name)
        if m.group(1):
            if val is None or (val == "" and m.group(2).startswith(":")):
                return m.group(3)
            return val
        return val if val is not None else m.group(0)
    for _ in range(3):  # il default può contenere a sua volta una variabile (${X:-$HOME/..})
        t2 = _VAR_RE.sub(rep, t)
        if t2 == t:
            break
        t = t2
    if "$" in t or "`" in t:
        return None
    return t


# --- Ramo memoria e handoff del dispatcher ---
# Claude Code chiede conferma a ogni scrittura via shell sotto ~/.claude, anche per
# salvare un handoff o una memoria. Il ramo approva da solo SOLO questi comandi:
#   - ogni percorso ~/.claude nominato sta in data/handoffs/ o in projects/<p>/memory/;
#   - ogni file scritto (redirezione, tee, touch, mkdir, destinazione di cp e mv) sta lì;
#   - i programmi sono di una lista breve, senza rete, senza cancellazioni, senza shell;
#   - nel testo eseguito non compaiono settings, hooks, unlock, CLAUDE.md, credenziali,
#     variabili (tranne HOME), sostituzioni $( ) o percorsi con `..`.
# Settings, hook e file di unlock restano fuori per costruzione: un comando che li nomina,
# anche spezzato dalle virgolette, non riceve mai l'allow e passa dal flusso normale.
_PROG_MEMORIA = frozenset(
    "mkdir cat printf echo tee cp mv touch ls head tail wc grep sort diff date test [ true cd stat "
    "find basename dirname".split())
_SCRIVONO_MEMORIA = frozenset("tee touch mkdir".split())
_PAROLE_VIETATE = re.compile(
    r"settings|hooks|unlock|\.claude\.json|claude(\.local)?\.md|credential|secret|token|personale",
    re.IGNORECASE)
_MENZIONE_MEMORIA = re.compile(r"(~|\$HOME|\$\{HOME\}|/[^\s;&|()<>]*)/\.claude(?![\w.-])(/[^\s;&|()<>]*)?")


def _zona(p: str) -> bool:
    """True se il path (assoluto) sta in data/handoffs/ o in projects/<p>/memory/ di ~/.claude.
    Vale sia sul path scritto sia su quello reale: un link simbolico non porta fuori."""
    claude = os.path.normpath(os.path.join(os.path.expanduser("~"), ".claude"))

    def dentro(q: str, radice: str) -> bool:
        parti = os.path.relpath(q, radice).split(os.sep)
        if parti[:2] == ["data", "handoffs"]:
            return True
        return len(parti) >= 3 and parti[0] == "projects" and parti[1] not in ("", ".", "..") and parti[2] == "memory"

    return dentro(os.path.normpath(p), claude) and dentro(os.path.realpath(p), os.path.realpath(claude))


def _assoluto(parola: str, cwd: str):
    home = os.path.expanduser("~")
    t = parola.replace("${HOME}", home).replace("$HOME", home)
    t = os.path.expanduser(t)
    if not os.path.isabs(t):
        if not cwd:
            return None
        t = os.path.join(cwd, t)
    return os.path.normpath(t)


def _senza_redirezioni(toks):
    """(parole senza le redirezioni, bersagli delle redirezioni in scrittura)."""
    parole, bersagli, i = [], [], 0
    while i < len(toks):
        m = _REDIREZIONE.match(toks[i])
        if m:
            if m.group(2):
                bersagli.append(m.group(2))
                i += 1
            elif i + 1 < len(toks):
                bersagli.append(toks[i + 1])
                i += 2
            else:
                i += 1  # `2>&1`: il lexer stacca `&`, qui resta solo `2>`
            continue
        if re.match(r"^\d*<", toks[i]):
            i += 1 if len(toks[i].lstrip("0123456789<")) else 2
            continue
        parole.append(toks[i])
        i += 1
    return parole, bersagli


def ammesso_ramo_memoria(cmd: str, cwd: str = "") -> bool:
    testo = testo_shell(cmd)
    if any(x in testo for x in ("$(", "`", "<(", ">(", "..")):
        return False
    piatto = re.sub(r"[\"'\\]", "", testo)
    if _PAROLE_VIETATE.search(piatto):
        return False
    if re.search(r"\$(?!HOME\b|\{HOME\})", piatto):
        return False
    menzioni = list(_MENZIONE_MEMORIA.finditer(piatto))
    if not menzioni:
        return False
    for m in menzioni:
        if m.group(1).startswith("/") and _assoluto(m.group(1), "/") != os.path.normpath(os.path.expanduser("~")):
            return False
        if not _zona(os.path.join(os.path.expanduser("~"), ".claude") + (m.group(2) or "")):
            return False
    corrente = cwd
    for toks in segmenti_parole(testo):
        parole, bersagli = _senza_redirezioni(toks)
        # Le redirezioni scrivono: ogni bersaglio sta nella zona (o è /dev/null).
        for bersaglio in bersagli:
            if bersaglio.startswith("&") or bersaglio == "/dev/null":
                continue
            p = _assoluto(bersaglio, corrente)
            if p is None or not _zona(p):
                return False
        trovati = programmi(" ".join(shlex.quote(t) for t in parole)) if parole else []
        if len(trovati) > 1:
            return False
        for prog, args in trovati:
            if prog not in _PROG_MEMORIA:
                return False
            liberi = [a for a in args if not a.startswith("-")]
            if prog == "cd":
                if len(liberi) != 1:
                    return False
                corrente = _assoluto(liberi[0], corrente)
                if corrente is None or not _zona(corrente):
                    return False
                continue
            if prog == "find" and any(a.startswith(("-exec", "-ok", "-delete", "-fprint", "-fls")) for a in args):
                return False
            if prog == "sort" and any(a.startswith(("-o", "--output")) for a in args):
                return False
            if prog == "sed" and any(a.startswith(("-i", "--in-place")) for a in args):
                return False
            if prog in ("cp", "mv") and any(a == "-t" or a.startswith("--target-directory") for a in args):
                return False
            scritti = liberi if prog in _SCRIVONO_MEMORIA else (liberi[-1:] if prog in ("cp", "mv") else [])
            for parola in scritti:
                p = _assoluto(parola, corrente)
                if p is None or not _zona(p):
                    return False
    return True


# --- Ramo ~/.claude del dispatcher (9/10/2026) ---
# Il ramo approva da solo i comandi che toccano ~/.claude. Non approva un comando
# che contiene uno di questi programmi in qualunque posizione: decide il classificatore.
_RETE = frozenset(
    "curl wget fetch nc ncat socat telnet ftp sftp ssh scp rsync dig nslookup host gh npm npx "
    "pnpm yarn pip pip3 brew osascript open mail mailx mutt msmtp sendmail gws".split()
)
_INTERPRETI = _hd.INTERPRETI
# Codice inline che esegue programmi o va in rete.
_INLINE_RISCHIO = re.compile(
    r"subprocess|os\.(system|popen|exec|spawn)|pty\.|__import__|urllib|requests|http\.client"
    r"|socket|child_process|execSync|spawnSync|fetch\(")


def ammesso_ramo_claude(cmd: str) -> bool:
    progs = programmi(cmd)
    for prog, args in progs:
        if prog in _RETE or prog in ("eval", "xargs", "rmdir"):
            return False
        if prog == "rm" and _ricorsivo(args):
            return False
        if prog in SHELL:
            liberi = [a for a in args if not a.startswith("-")]
            if "-c" in args or "-s" in args or not liberi:
                return False
        if prog == "find" and any(a in ("-delete", "-exec", "-execdir", "-ok", "-okdir") for a in args):
            return False
        if prog in ("awk", "gawk") and any("system(" in a or "getline" in a for a in args):
            return False
    if any(p in _INTERPRETI for p, _ in progs) and _INLINE_RISCHIO.search(cmd):
        return False
    return True


def git_puro(cmd: str) -> bool:
    """Vero se ogni comando eseguito è git o cd (9/10/2026). Le virgolette si leggono come
    le legge bash: un apostrofo dentro le doppie non apre una stringa. Virgolette che non
    tornano: non è git puro."""
    try:
        lexer = shlex.shlex(cmd, posix=True, punctuation_chars=";&|()\n")
        lexer.whitespace = " \t\r"
        lexer.whitespace_split = True
        list(lexer)
    except ValueError:
        return False
    progs = programmi(cmd)
    if not progs or not all(p in ("git", "cd") for p, _ in progs):
        return False
    # 24/10/2026 (#3575): un git che riscrive file della cartella di lavoro (apply, am, checkout,
    # restore, switch, stash pop e stash apply) non è git puro: il comando passa da D6 invece di
    # uscire prima. _git_riscrive sta più sotto, con le scritture che il comando non nomina.
    return not any(p == "git" and _git_riscrive(args) for p, args in progs)


# --- Script eseguiti da sotto ~/.claude (18/10/2026) ---
# Il ramo .claude approva da solo i comandi sotto ~/.claude, e da quel ramo uno
# script appena scritto lì (anche da un'injection) partiva senza conferma. Ora un
# file sotto ~/.claude si esegue senza chiedere solo se è tracciato in git e
# uguale a HEAD. Lo scratchpad e i progetti restano fuori da questa regola.
_HOME_RE = re.compile(r"\$HOME\b|\$\{HOME\}")
_ESEGUONO_FILE = _INTERPRETI | SHELL | frozenset(("source", "."))
# Opzioni che rendono il primo argomento non un file da eseguire.
_SENZA_FILE = frozenset(("-c", "-m", "-e", "-n", "--check", "-V", "--version", "-h", "--help"))


def _espandi(parola: str, base: str, assegnate=None) -> str:
    # Le variabili assegnate nel comando stesso (`SP=/private/tmp/...; python3 $SP/x.py`) e quelle
    # dell'ambiente si espandono (19/10/2026): la copia di un hook nello scratchpad non è la config.
    # Se una variabile non si risolve, si espande solo HOME e il resto resta col `$`.
    if "$" in parola:
        espansa = _espandi_variabili(parola, assegnate or {})
        parola = espansa if espansa is not None else _HOME_RE.sub(lambda m: os.path.expanduser("~"), parola)
    return os.path.normpath(os.path.join(base, os.path.expanduser(parola)))


def _file_eseguiti(cmd: str, cwd: str, assegnate=None):
    """Path dei file che `cmd` esegue: lo script di un interprete o di una shell,
    il file di `source`, o il programma stesso scritto con un path."""
    base, out = cwd, []
    for tok, args in comandi(cmd):
        nome = _nome(tok)
        if nome == "cd":
            if args and not args[0].startswith("-"):
                base = _espandi(args[0], base, assegnate)
            continue
        if nome in _ESEGUONO_FILE:
            # `python3 - <<EOF` legge il codice da stdin: non c'è un file da eseguire.
            if any(a in _SENZA_FILE or a == "-" for a in args):
                continue
            liberi = [a for a in args if not a.startswith(("-", "<", ">")) and not re.match(r"^\d*[<>]", a)]
            if liberi:
                out.append(_espandi(liberi[0], base, assegnate))
        elif "/" in tok:
            # Un path lanciato direttamente conta solo se è un file eseguibile: il
            # corpo di un heredoc verso cat arriva qui come parole, non come comandi.
            path = _espandi(tok, base, assegnate)
            if os.path.isfile(path) and os.access(path, os.X_OK):
                out.append(path)
    return out


def script_claude_non_tracciati(cmd: str, cwd: str):
    """File sotto ~/.claude che `cmd` esegue e che non sono tracciati in git, o
    sono diversi da HEAD. Un path con variabili non espanse conta come non verificato."""
    import subprocess
    radice = os.path.realpath(os.path.expanduser("~/.claude"))
    trovati = []
    for path in _file_eseguiti(cmd, cwd, _assegnazioni(cmd)):
        if "$" in path or "`" in path:
            if ".claude" in path:
                trovati.append(path)
            continue
        reale = os.path.realpath(path)
        if not reale.startswith(radice + os.sep):
            continue
        rel = os.path.relpath(reale, radice)
        if banco(rel.split(os.sep)):
            continue
        try:
            tracciato = subprocess.run(["git", "-C", radice, "ls-files", "--error-unmatch", "--", rel],
                                       capture_output=True, timeout=5).returncode == 0
            pulito = tracciato and subprocess.run(["git", "-C", radice, "diff", "--quiet", "HEAD", "--", rel],
                                                  capture_output=True, timeout=5).returncode == 0
        except Exception:
            pulito = False
        if not pulito:
            trovati.append("~/.claude/" + rel)
    return trovati


# --- Scritture sulla config (18/10/2026) ---
# La shell riscriveva settings, hook e skill senza conferma. Dal 18/10/2026 una scrittura
# su questi path chiede, ma conta solo la DESTINAZIONE: il falso positivo di prima era un
# `cp` che leggeva settings.json e scriveva altrove.
CONFIG_DIR = frozenset(("hooks", "mods", "scripts", "skills", "agents", "commands", "output-styles"))
CONFIG_FILE = frozenset(("CLAUDE.md", "INSTANCE.md"))
_SETTINGS = re.compile(r"^settings[^/]*\.json$")
# ditto scrive l'ultimo argomento come cp. Il contenuto che ci mette dentro lo conta
# _scritture_indirette (24/10/2026, #3575).
_SCRIVONO_ULTIMO = frozenset("cp install ln rsync ditto".split())
# mv scrive la destinazione e toglie la sorgente: contano tutti i suoi argomenti.
_SCRIVONO_TUTTI = frozenset("mv tee touch truncate chmod chown rm unlink".split())
_SCRITTURA_INLINE = re.compile(
    r"open\([^\n]*?,\s*[rb]?[\x27\x22][wax+]|write_text|write_bytes|os\.(replace|rename)\(|shutil\.(copy|move)"
    r"|writeFileSync|appendFileSync|renameSync|copyFileSync|\.touch\(")
_MENZIONE = re.compile(
    r"(?:~|\$HOME|\$\{HOME\}|/Users/[^/\s\x27\x22]+)/\.claude/[\w./-]+"
    r"|(?<![\w/.~-])(?:settings[\w.-]*\.json|CLAUDE\.md|INSTANCE\.md"
    r"|(?:hooks|mods|scripts|skills|agents|commands|output-styles)/[\w./-]+)")


def _codice_inline(cmd: str, progs):
    """Il codice che un interprete esegue (corpi degli heredoc, `-c`, `-e`) e gli argomenti
    dell'interprete (19/10/2026). Prima si cercavano i percorsi in tutto il comando: un
    `~/.claude/scripts/gate-run.sh` lanciato accanto a uno script che scrive un file di progetto
    contava come scrittura sulla config. Nel corpo python restano solo le stringhe senza spazi:
    la prosa che uno script scrive in una nota nomina skills/ o settings.json senza scriverci."""
    codici = []

    def raccogli(h) -> bool:
        if h.consumatore in _INTERPRETI:
            righe = _hd.percorsi_python(h)
            codici.append("\n".join(h.corpo if righe is None else righe))
        return False

    _hd.togli(cmd, raccogli)
    interpreti = [(t, a) for t, a in progs if _nome(t) in _INTERPRETI]
    if interpreti and "<<" in cmd and not codici:
        codici.append(cmd)  # heredoc che heredoc.py non legge con certezza: conta tutto il testo
    argomenti = []
    for _, args in interpreti:
        inline = False
        for j, a in enumerate(args):
            if a in ("-c", "-e", "--eval", "-p", "--print") and j + 1 < len(args):
                codici.append(args[j + 1])
                inline = True
        liberi = [a for a in args if not a.startswith(("-", "<")) and not _REDIREZIONE.match(a)]
        # Solo l'interprete che esegue codice inline (`python3 - ARG`, `-c`, stdin): gli argomenti di
        # `python3 ~/.claude/skills/posta/posta.py bozza` accanto a un heredoc non sono destinazioni
        # del codice inline, e lo script stesso lo copre D1 (21/10/2026).
        if inline or "-" in args or not liberi:
            argomenti += liberi
    return codici, argomenti


_BANCO = re.compile(r"^test[_-][\w.-]*\.py$")


def banco(parti) -> bool:
    """Un banco di prova (`hooks/test_*.py`, `tests/*.py`): nessun hook lo carica, eseguirlo vale
    come uno script nello scratchpad. Scriverlo e lanciarlo non chiede (21/10/2026)."""
    return len(parti) == 2 and parti[0] in ("hooks", "tests") and bool(_BANCO.match(parti[1]))


def e_config(path: str) -> bool:
    """Vero se `path` (assoluto) è un file di config sotto ~/.claude."""
    radice = os.path.realpath(os.path.expanduser("~/.claude"))
    reale = os.path.realpath(path)
    if not reale.startswith(radice + os.sep):
        return False
    parti = os.path.relpath(reale, radice).split(os.sep)
    if banco(parti):
        return False
    if parti[0] in CONFIG_DIR:
        return True
    return len(parti) == 1 and (parti[0] in CONFIG_FILE or bool(_SETTINGS.match(parti[0])))


# --- Scritture che il comando non nomina (24/10/2026, #3575) ---
# Un archivio estratto, una patch applicata o uno stash ripreso scrivono file che non compaiono
# nel comando: conta la cartella in cui finiscono. `--output FILE` scrive quanto una redirezione.
# cp, mv, ln, install e rsync verso una cartella scrivono la cartella più il nome della sorgente.
# ditto mette dentro la destinazione il contenuto della sorgente, o dell'archivio con -x.
_TAR = frozenset(("tar", "gtar", "bsdtar"))
# Opzioni di patch che prendono un valore staccato: il valore non è il file da correggere.
_PATCH_CON_VALORE = frozenset("-d -o -i -p -D -B -r -z -V -F -Y -g --directory --output --input".split())
_GIT_CON_VALORE = frozenset(("-C", "-c", "--git-dir", "--work-tree", "--namespace"))
# git che riscrive file della cartella di lavoro senza nominarli tutti: git_puro non lo salta.
_GIT_RISCRIVE = frozenset(("apply", "am", "checkout", "restore", "switch"))


def _git_riscrive(args) -> bool:
    """Vero se git esegue apply, am, checkout, restore, switch, stash pop o stash apply."""
    i = 0
    while i < len(args) and args[i].startswith("-"):
        i += 2 if args[i] in _GIT_CON_VALORE else 1
    sotto = args[i] if i < len(args) else ""
    return sotto in _GIT_RISCRIVE or (sotto == "stash" and args[i + 1:i + 2] in (["pop"], ["apply"]))


def _radice_git(cartella: str) -> str:
    """La cartella del repo git che contiene `cartella`: lì scrivono git apply, git am e
    git stash pop. Fuori da un repo, `cartella` stessa."""
    c = os.path.realpath(cartella)
    while not os.path.exists(os.path.join(c, ".git")):
        if os.path.dirname(c) == c:
            return cartella
        c = os.path.dirname(c)
    return c


def _scrive_dentro(cartella: str) -> bool:
    """Vero se un file scritto dentro `cartella` può essere config: la cartella è config o sta in
    una cartella di config, oppure è ~/.claude o una cartella che la contiene."""
    radice = os.path.realpath(os.path.expanduser("~/.claude"))
    reale = os.path.realpath(cartella)
    return (e_config(reale) or e_config(os.path.join(reale, "x")) or reale == radice
            or radice.startswith(reale.rstrip(os.sep) + os.sep))


def _scritture_indirette(nome, args, liberi, base, assegnate):
    """(candidati, cartelle) che scritture_config non legge dalla destinazione scritta: i candidati
    sono file come (parola, base), le cartelle sono path assoluti in cui il comando scrive."""
    candidati, cartelle = [], []

    def valore(*opzioni):
        # `-C DIR` e `-CDIR` per le opzioni corte, `--directory DIR` e `--directory=DIR` per le lunghe.
        for i, a in enumerate(args):
            for o in opzioni:
                if a == o and i + 1 < len(args):
                    return args[i + 1]
                if o.startswith("--") and a.startswith(o + "="):
                    return a[len(o) + 1:]
                if not o.startswith("--") and not a.startswith("--") and a.startswith(o) and len(a) > len(o):
                    return a[len(o):]
        return None

    def cartella(opzioni):
        v = valore(*opzioni)
        return _espandi(v, base, assegnate) if v else base

    if nome == "git":
        i = 0
        while i < len(args) and args[i].startswith("-"):
            if args[i] == "-C" and i + 1 < len(args):
                base = _espandi(args[i + 1], base, assegnate)
            i += 2 if args[i] in _GIT_CON_VALORE else 1
        sotto, resto = (args[i], args[i + 1:]) if i < len(args) else ("", [])
        lettura = "--apply" not in resto and any(a in ("--check", "--stat", "--numstat", "--summary") for a in resto)
        if (sotto == "apply" and not lettura and "--cached" not in resto) or sotto == "am" or \
                (sotto == "stash" and resto[:1] in (["pop"], ["apply"])):
            cartelle.append(_radice_git(base))
        if sotto == "format-patch" and valore("-o", "--output-directory"):
            cartelle.append(cartella(("-o", "--output-directory")))
    elif nome in _TAR:
        brevi = "".join(a[1:] for a in args if a.startswith("-") and not a.startswith(("--", "-C")))
        if args and not args[0].startswith("-"):
            brevi += args[0]  # forma vecchia: `tar xzf archivio.tgz`
        lunghe = [a.split("=", 1)[0] for a in args if a.startswith("--")]
        if ("x" in brevi or "--extract" in lunghe or "--get" in lunghe) and \
                "O" not in brevi and "--to-stdout" not in lunghe:
            cartelle.append(cartella(("-C", "--directory", "--cd")))
    elif nome == "unzip":
        # -l, -t, -v, -z, -Z elencano o provano, -p stampa: nessun file scritto.
        brevi = "".join(a[1:] for a in args if a.startswith("-") and not a.startswith(("--", "-d")))
        if not any(m in brevi for m in "lptvzZ"):
            cartelle.append(cartella(("-d",)))
    elif nome in ("patch", "gpatch") and not any(a in ("--dry-run", "--check", "-C") for a in args):
        dove = cartella(("-d", "--directory"))
        cartelle.append(dove)
        salta = False
        for a in args:
            if salta:
                salta = False
            elif a in _PATCH_CON_VALORE or re.fullmatch(r"\d*<", a):
                salta = True
            elif not a.startswith("-") and not re.match(r"^\d*[<>]", a):
                candidati.append((a, dove))  # `patch FILE < diff`: il file da correggere
        uscita = valore("-o", "--output")
        if uscita:
            candidati.append((uscita, dove))
    if nome == "ditto":
        # ditto non scrive destinazione/nome come cp: il contenuto della sorgente, o dell'archivio
        # con -x, finisce dentro la destinazione. Conta la cartella intera.
        if len(liberi) >= 2:
            cartelle.append(_espandi(liberi[-1], base, assegnate))
    elif nome in _SCRIVONO_ULTIMO or nome == "mv":
        dest = valore("-t", "--target-directory") if nome != "rsync" else None
        sorgenti = [a for a in liberi if a != dest] if dest else liberi[:-1]
        dest = dest or (liberi[-1] if len(liberi) >= 2 else "")
        if dest and not (nome == "rsync" and re.match(r"^[^/]*:", dest)):
            d = _espandi(dest, base, assegnate)
            if dest.endswith("/") or os.path.isdir(d):
                for s in sorgenti:
                    if s.endswith(("/", "/.")):
                        cartelle.append(d)  # `rsync a/ d`, `cp -R a/. d`: il contenuto di a finisce in d
                    else:
                        t = os.path.join(d, os.path.basename(s))
                        candidati.append((t, base))
                        if os.path.isdir(_espandi(s, base, assegnate)):
                            cartelle.append(t)
    uscita = valore("--output")
    if uscita:
        candidati.append((uscita, base))
    return candidati, cartelle


def scritture_config(cmd: str, cwd: str):
    """Path di config sotto ~/.claude che `cmd` scrive: redirezioni, cp/mv/tee/touch/rm/sed -i,
    git checkout/restore, e codice inline (python, node) con una scrittura che nomina un path.
    Dal 24/10/2026 anche archivi estratti, patch, git apply, git am e stash pop, --output, ditto
    e copie verso una cartella (_scritture_indirette)."""
    assegnate = _assegnazioni(cmd)
    base, basi, candidati, cartelle = cwd, [cwd], [], []
    progs = comandi(cmd)
    for tok, args in progs:
        nome = _nome(tok)
        if nome == "cd":
            if args and not args[0].startswith("-"):
                base = _espandi(args[0], base, assegnate)
                basi.append(base)
            continue
        for i, a in enumerate(args):
            m = _REDIREZIONE.match(a)
            if m:
                bersaglio = m.group(2) or (args[i + 1] if i + 1 < len(args) else "")
                if bersaglio and not bersaglio.startswith("&"):
                    candidati.append((bersaglio, base))
        liberi = [a for a in args if not a.startswith("-") and not _REDIREZIONE.match(a)]
        # Archivi, patch, stash, --output e copie verso una cartella (24/10/2026, #3575).
        indiretti, dentro = _scritture_indirette(nome, args, liberi, base, assegnate)
        candidati += indiretti
        cartelle += dentro
        if nome in _SCRIVONO_ULTIMO and len(liberi) >= 2:
            candidati.append((liberi[-1], base))
            if "-t" in args and args.index("-t") + 1 < len(args):
                candidati.append((args[args.index("-t") + 1], base))
        elif nome in _SCRIVONO_TUTTI:
            candidati += [(a, base) for a in liberi]
        elif nome in ("sed", "gsed", "perl") and any(a == "--in-place" or re.match(r"^-[a-zA-Z]*i", a) for a in args):
            candidati += [(a, base) for a in liberi]
        elif nome == "dd":
            candidati += [(a[3:], base) for a in args if a.startswith("of=")]
        elif nome == "git":
            i, base_git = 0, base
            while i < len(args) and args[i].startswith("-"):
                if args[i] == "-C" and i + 1 < len(args):
                    base_git = _espandi(args[i + 1], base, assegnate)
                    i += 2
                else:
                    i += 1
            if i < len(args) and args[i] in ("checkout", "restore"):
                candidati += [(a, base_git) for a in args[i + 1:] if not a.startswith("-")]
    trovati = []
    codici, argomenti = _codice_inline(cmd, progs)
    if any(_SCRITTURA_INLINE.search(c) for c in codici):
        for c in codici:
            for m in _MENZIONE.finditer(c):
                candidati += [(m.group(0), b) for b in basi]
        # `python3 - "$F" <<'EOF'` con `open(sys.argv[1], 'w')`: la destinazione è un argomento.
        candidati += [(a, b) for a in argomenti for b in basi]
        # Codice inline che scrive mentre la cartella corrente è dentro la config: un nome
        # di file nudo (`open('x.py', 'w')` dopo `cd ~/.claude/hooks`) non si vede col path.
        radice = os.path.realpath(os.path.expanduser("~/.claude"))
        for b in basi:
            if e_config(os.path.join(b, "x")):
                trovati.append("~/.claude/" + os.path.relpath(os.path.realpath(b), radice) + "/ (codice inline)")
    for parola, b in candidati:
        parola = parola.strip("\x27\x22")
        if "$" in parola.replace("$HOME", "").replace("${HOME}", ""):
            parola = _espandi_variabili(parola, assegnate) or ""
            if not parola:
                continue
        path = _espandi(parola, b, assegnate)
        if e_config(path):
            rel = "~/.claude/" + os.path.relpath(os.path.realpath(path), os.path.realpath(os.path.expanduser("~/.claude")))
            if rel not in trovati:
                trovati.append(rel)
    # Le cartelle in cui il comando scrive file che non nomina (24/10/2026, #3575).
    radice_claude = os.path.realpath(os.path.expanduser("~/.claude"))
    for c in cartelle:
        if "$" in c or "`" in c or not _scrive_dentro(c):
            continue
        reale = os.path.realpath(c)
        voce = "~/.claude" + reale[len(radice_claude):] if (reale + os.sep).startswith(radice_claude + os.sep) else reale
        voce += "/ (file che il comando non nomina)"
        if voce not in trovati:
            trovati.append(voce)
    return trovati


if __name__ == "__main__":
    import json
    import sys
    # Claude Code scrive e legge in UTF-8. Su Windows la pipe è in cp1252 (16/10/2026).
    for _flusso in (sys.stdout, sys.stderr):
        try:
            _flusso.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass
    # Uso dal dispatcher: python3 forma_comando.py ramo-memoria < payload -> rc 0 se ammesso.
    if len(sys.argv) == 2 and sys.argv[1] == "ramo-memoria":
        try:
            dati = json.loads(sys.stdin.buffer.read().decode("utf-8"))
            comando = (dati.get("tool_input") or {}).get("command") or ""
            sys.exit(0 if comando and ammesso_ramo_memoria(comando, dati.get("cwd") or "") else 1)
        except Exception:
            sys.exit(1)
    # Uso dal dispatcher: forma_comando.py script-claude < payload -> stampa la decisione
    # ask se il comando esegue uno script non tracciato sotto ~/.claude o scrive sulla
    # config, altrimenti niente.
    if len(sys.argv) == 2 and sys.argv[1] == "script-claude":
        dati = json.loads(sys.stdin.buffer.read().decode("utf-8"))
        cmd = (dati.get("tool_input") or {}).get("command") or ""
        cwd = dati.get("cwd") or os.getcwd()
        motivo = None
        trovati = script_claude_non_tracciati(cmd, cwd)
        if trovati:
            motivo = ("esegue uno script sotto ~/.claude non tracciato in git o diverso da HEAD: "
                      + ", ".join(trovati[:3]) + " (D1, 18/10/2026)")
        else:
            scritti = scritture_config(cmd, cwd)
            if scritti:
                motivo = ("scrive sulla config di ~/.claude: " + ", ".join(scritti[:3])
                          + ". Conferma richiesta (D6, 18/10/2026)")
        if motivo:
            print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse",
                              "permissionDecision": "ask", "permissionDecisionReason": motivo}}))
        sys.exit(0)
    # Uso dal dispatcher: python3 forma_comando.py ramo-claude "<comando>" -> rc 0 se ammesso.
    if len(sys.argv) == 3 and sys.argv[1] == "ramo-claude":
        sys.exit(0 if ammesso_ramo_claude(sys.argv[2]) else 1)
    if len(sys.argv) == 3 and sys.argv[1] == "git-puro":
        sys.exit(0 if git_puro(sys.argv[2]) else 1)
    sys.exit(2)
