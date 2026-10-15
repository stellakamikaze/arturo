"""I programmi che un comando Bash esegue davvero.

Una guardia che guarda il testo con una regex e la prima parola del segmento non
vede un programma scritto col path completo (`/bin/rm`), dentro un blocco `{ }`,
dopo `then`/`do` o passato a `bash -c`. Qui si ricava, segmento per segmento, il
programma vero: senza assegnazioni, parole chiave e wrapper davanti, col solo
nome del binario, e rientrando nel testo di `sh -c` ed `eval`.

Riusa il tokenizer di block-dangerous.py (`_testo_shell`, `_segmenti_parole`),
che rispetta le virgolette e toglie i corpi degli heredoc quotati verso non-shell.

Usato da block-dangerous.py (rm e find che cancellano) e dal dispatcher
(git puro, ramo ~/.claude).
"""
import importlib.util
import os
import re

_spec = importlib.util.spec_from_file_location(
    "block_dangerous_forma", os.path.join(os.path.dirname(os.path.abspath(__file__)), "block-dangerous.py"))
_bd = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_bd)

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
    for toks in _bd._segmenti_parole(_bd._testo_shell(cmd)):
        i = 0
        while i < len(toks):
            t = toks[i]
            if t in _DAVANTI or _ASSEGNAZIONE.match(t):
                i += 1
            elif re.match(r"^\d*[<>]", t):
                # redirezione in testa (`<file`, `2>`, `$(<file)`): non e' un programma
                i += 1 if len(t.lstrip("0123456789<>&")) else 2
            elif _nome(t) in _WRAPPER:
                i += 1
                while i < len(toks) and (toks[i].startswith("-") or toks[i].isdigit() or _ASSEGNAZIONE.match(toks[i])):
                    i += 1
            else:
                break
        # `2>&1` si spezza in `2>`, `&`, `1`: un numero da solo non e' un programma.
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


# --- Ramo ~/.claude del dispatcher ---
# Il ramo approva da solo alcuni comandi su memoria e handoff. Non approva un
# comando che contiene uno di questi programmi in qualunque posizione.
_RETE = frozenset(
    "curl wget fetch nc ncat socat telnet ftp sftp ssh scp rsync dig nslookup host gh npm npx "
    "pnpm yarn pip pip3 brew osascript open mail mailx mutt msmtp sendmail gws".split()
)
_INTERPRETI = frozenset("python python3 node perl ruby php".split())
# Codice inline che esegue programmi o va in rete.
_INLINE_RISCHIO = re.compile(
    r"subprocess|os\.(system|popen|exec|spawn)|pty\.|__import__|urllib|requests|http\.client"
    r"|socket|child_process|execSync|spawnSync|fetch\(")


def _ricorsivo(args) -> bool:
    return any(a == "--recursive" or (a.startswith("-") and not a.startswith("--") and "r" in a.lower()) for a in args)


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
    """Vero se ogni comando eseguito e' git o cd. Le virgolette si leggono come
    le legge bash: un apostrofo dentro le doppie non apre una stringa. Virgolette
    che non tornano: non e' git puro."""
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
    import sys
    # Uso dal dispatcher: python3 forma_comando.py ramo-claude "<comando>" -> rc 0 se ammesso.
    if len(sys.argv) == 3 and sys.argv[1] == "ramo-claude":
        sys.exit(0 if ammesso_ramo_claude(sys.argv[2]) else 1)
    if len(sys.argv) == 3 and sys.argv[1] == "git-puro":
        sys.exit(0 if git_puro(sys.argv[2]) else 1)
    sys.exit(2)
