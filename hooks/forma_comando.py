"""I programmi che un comando Bash esegue davvero.

Una guardia che guarda il testo con una regex e la prima parola del segmento non
vede un programma scritto col path completo (`/bin/rm`), dentro un blocco `{ }`,
dopo `then`/`do` o passato a `bash -c`. Qui si ricava, segmento per segmento, il
programma vero: senza assegnazioni, parole chiave e wrapper davanti, col solo
nome del binario, e rientrando nel testo di `sh -c` ed `eval`.

Qui sta anche il tokenizer comune (`testo_shell`, `segmenti_parole`), che rispetta le
virgolette e toglie i corpi degli heredoc quotati verso non-shell: block-dangerous.py lo
carica da qui (fino al 15/10/2026 i due file si caricavano a vicenda).

Usato da block-dangerous.py (rm e find che cancellano) e dal dispatcher
(git puro, ramo memoria e handoff).
"""
import importlib.util
import os
import re
import shlex

# Gli heredoc li riconosce heredoc.py, lo stesso modulo delle altre guardie (15/10/2026).
# Se manca, nessun corpo sparisce: la guardia controlla tutto il testo.
try:
    _spec_hd = importlib.util.spec_from_file_location(
        "arturo_heredoc", os.path.join(os.path.dirname(os.path.abspath(__file__)), "heredoc.py"))
    _hd = importlib.util.module_from_spec(_spec_hd)
    _spec_hd.loader.exec_module(_hd)
    _togli_heredoc = _hd.togli
except Exception:
    def _togli_heredoc(cmd, via, segnaposto=None):
        return cmd

    class _hd:  # noqa: N801 - senza heredoc.py nessun messaggio si svuota
        @staticmethod
        def fuori_virgolette(testo, pos):
            return False

# Valore di -m / --message: git non lo esegue, e un messaggio di commit che CITA
# un comando non è quel comando. Restano i messaggi con command-substitution.
_MESSAGGIO = re.compile(r"(?:^|\s)(?:-m|--message)[= ]\s*(['\"])((?:(?!\1).)*)\1", re.DOTALL)


def testo_shell(command: str) -> str:
    """Il comando senza il testo che la shell non legge come comandi.

    Toglie il corpo degli heredoc col delimitatore TRA VIRGOLETTE diretti a un
    comando che non è una shell (python, cat, tee): la shell non lo espande e non
    lo esegue, quindi un `cat <segreto>` scritto lì dentro è testo, non una
    lettura. Un heredoc senza virgolette resta, perché la shell ne espande le
    `$(...)`. Toglie anche i messaggi -m/--message privi di command-substitution.
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
        out.append((prog, args))
        if profondita < 3:
            if prog in SHELL and "-c" in args and args.index("-c") + 1 < len(args):
                out += programmi(args[args.index("-c") + 1], profondita + 1)
            elif prog == "eval" and args:
                out += programmi(" ".join(args), profondita + 1)
    return out


def _ricorsivo(args) -> bool:
    return any(a == "--recursive" or (a.startswith("-") and not a.startswith("--") and "r" in a.lower()) for a in args)


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
_SCRIVONO_TUTTI = frozenset("tee touch mkdir".split())
_PAROLE_VIETATE = re.compile(
    r"settings|hooks|unlock|\.claude\.json|claude(\.local)?\.md|credential|secret|token|personale",
    re.IGNORECASE)
_MENZIONE = re.compile(r"(~|\$HOME|\$\{HOME\}|/[^\s;&|()<>]*)/\.claude(?![\w.-])(/[^\s;&|()<>]*)?")


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


_REDIREZIONE = re.compile(r"^(\d*|&)>>?(.*)$")


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
    menzioni = list(_MENZIONE.finditer(piatto))
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
            scritti = liberi if prog in _SCRIVONO_TUTTI else (liberi[-1:] if prog in ("cp", "mv") else [])
            for parola in scritti:
                p = _assoluto(parola, corrente)
                if p is None or not _zona(p):
                    return False
    return True


def git_puro(cmd: str) -> bool:
    """Vero se ogni comando eseguito è git o cd. Le virgolette si leggono come
    le legge bash: un apostrofo dentro le doppie non apre una stringa. Virgolette
    che non tornano: non è git puro."""
    import shlex
    try:
        lexer = shlex.shlex(cmd, posix=True, punctuation_chars=";&|()\n")
        lexer.whitespace = " \t\r"
        lexer.whitespace_split = True
        list(lexer)
    except ValueError:
        return False
    progs = programmi(cmd)
    return bool(progs) and all(p in ("git", "cd") for p, _ in progs)


if __name__ == "__main__":
    # Claude Code scrive e legge in UTF-8. Su Windows la pipe è in cp1252 (16/10/2026).
    for _flusso in (sys.stdout, sys.stderr):
        try:
            _flusso.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass
    import sys
    # Uso dal dispatcher: python3 forma_comando.py ramo-memoria < payload -> rc 0 se ammesso.
    if len(sys.argv) == 2 and sys.argv[1] == "ramo-memoria":
        import json
        try:
            dati = json.loads(sys.stdin.buffer.read().decode("utf-8"))
            comando = (dati.get("tool_input") or {}).get("command") or ""
            sys.exit(0 if comando and ammesso_ramo_memoria(comando, dati.get("cwd") or "") else 1)
        except Exception:
            sys.exit(1)
    if len(sys.argv) == 3 and sys.argv[1] == "git-puro":
        sys.exit(0 if git_puro(sys.argv[2]) else 1)
    sys.exit(2)
