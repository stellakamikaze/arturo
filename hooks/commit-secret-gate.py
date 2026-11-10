#!/usr/bin/env python3
"""PreToolUse(Bash) hook: gate anti-leak prima di `git commit` / `gh pr create`.

Scansiona il diff STAGED (git diff --cached) alla ricerca di secret ad ALTA
confidenza nelle righe aggiunte. Se trovati -> ask (non blocco: evita di rompere
commit legittimi; l'utente decide). Usa un set curato di pattern per minimizzare
i falsi positivi (NO "password=..." generico che matcha codice/test).

I leak in un commit sono irreversibili una volta pushati: questo è l'unico
layer PREVENTIVO (gli scanner PostToolUse avvisano a cose fatte).

Fail-open su qualsiasi errore. Legge cwd dal payload per lanciare git nel repo giusto.
"""
from __future__ import annotations

import importlib.util
import json
import os
import re
import shlex
import signal
import subprocess
import sys


def _regola(nome: str) -> None:
    # Il dispatcher di Arturo chiede anche quale regola ha parlato: va nella telemetria come
    # commit-secret-gate.py.<regola>. Dal 19 al 22/10/2026 la guardia ha chiesto 6 volte durante
    # /fine e nessun dato diceva perché. Senza la variabile l'uscita resta il solo JSON. Per un segreto
    # la regola è la famiglia (FAMIGLIA), dal 24/10/2026.
    if os.environ.get("ARTURO_REGOLA") == "1":
        print(f"REGOLA: {nome}")


def _stdin_timeout(signum, frame):
    # 9/10/2026: un gate che scade e tace è un gate spento (git lento, disco freddo).
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "ask",
                      "permissionDecisionReason": "Scansione dei segreti nel commit scaduta: conferma prima di proseguire."}}))
    _regola("scaduta")
    sys.exit(0)


if hasattr(signal, "SIGALRM"):
    signal.signal(signal.SIGALRM, _stdin_timeout)


HIGH_CONF = [
    # Anche le chiavi cifrate e i blocchi PGP (review del 7/11/2026, finding 67).
    (r"-----BEGIN (?:RSA |EC |DSA |OPENSSH |ENCRYPTED |PGP )?PRIVATE KEY(?: BLOCK)?-----", "chiave privata"),
    (r"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b", "AWS Access Key"),
    (r"\bgh[pousr]_[A-Za-z0-9_]{36,}\b", "GitHub token"),
    (r"\bgithub_pat_[A-Za-z0-9_]{22,}\b", "GitHub PAT"),
    (r"\bsk-ant-[A-Za-z0-9-]{20,}", "Anthropic API key"),
    # OpenAI (review del 7/11/2026, finding 7): le stesse forme di credential-leak-scanner.py. Gli altri pattern
    # dello scanner (API Key, Generic Secret) sono generici e qui darebbero falsi positivi sul codice.
    (r"\bsk-(?:proj|org|svcacct|admin)-[A-Za-z0-9_-]{20,}", "OpenAI API key"),
    (r"\bsk-[A-Za-z0-9]{48,}\b", "OpenAI API key"),
    (r"\bsk_live_[A-Za-z0-9]{20,}", "Stripe live key"),
    (r"\bxox[baprs]-[A-Za-z0-9-]{10,}", "Slack token"),
    (r"\bAIza[A-Za-z0-9_-]{35}\b", "Google API key"),
    (r"\bGOCSPX-[A-Za-z0-9_-]{20,}\b", "Google OAuth client secret"),
    (r"\b1//[A-Za-z0-9_-]{20,}\b", "Google refresh token"),
    (r"\b\d{6,12}:[A-Za-z0-9_-]{30,}\b", "Telegram bot token"),
    (r"\beyJ[A-Za-z0-9_-]{15,}\.eyJ[A-Za-z0-9_-]{15,}\.[A-Za-z0-9_-]{10,}", "JWT"),
    (r"postgres(?:ql)?://[^:@\s]+:[^@\s]+@[^/\s]+", "connection string con password"),
]
COMPILED = [(re.compile(p), name) for p, name in HIGH_CONF]
# La telemetria di Arturo riceve la famiglia del segreto, mai il fornitore (24/10/2026): "google-api-key"
# diceva quale servizio usa la persona. Le famiglie sono quelle di FAMIGLIE_SEGRETI in bin/telemetria.py e
# di server/logica.js; un pattern nuovo senza famiglia esce come segreto-altro.
FAMIGLIA = {
    "chiave privata": "segreto-chiave-privata",
    "AWS Access Key": "segreto-cloud",
    "Google API key": "segreto-cloud",
    "Google OAuth client secret": "segreto-cloud",
    "Google refresh token": "segreto-cloud",
    "GitHub token": "segreto-token",
    "GitHub PAT": "segreto-token",
    "Anthropic API key": "segreto-token",
    "OpenAI API key": "segreto-token",
    "Stripe live key": "segreto-token",
    "Slack token": "segreto-token",
    "Telegram bot token": "segreto-token",
    "JWT": "segreto-token",
    "connection string con password": "segreto-password",
}


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
_ASSIGN = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)=(.*)$", re.S)
_VAR = re.compile(r"\$(?:\{([A-Za-z_][A-Za-z0-9_]*)\}|([A-Za-z_][A-Za-z0-9_]*))")
# Le shell sono quelle di forma_comando.py, un solo elenco per tutte le guardie (15/10/2026).
try:
    _spec_fc = importlib.util.spec_from_file_location(
        "forma_comando", os.path.join(os.path.dirname(os.path.abspath(__file__)), "forma_comando.py"))
    _fc = importlib.util.module_from_spec(_spec_fc)
    _spec_fc.loader.exec_module(_fc)
    _SHELL = _fc.SHELL
    _togli_commenti = _fc.togli_commenti
    # Il nome del programma come lo leggono le altre guardie: senza `.exe`, e in minuscolo dove il disco
    # ignora le maiuscole. Col confronto esatto `Git commit` e `GH pr create` saltavano la scansione
    # (revisione del 10/11/2026, HK-1b).
    _nome = _fc._nome
    _RE_NOMI = _fc.RE_NOMI
except Exception:
    _SHELL = frozenset("sh bash zsh dash ksh fish".split())
    _RE_NOMI = re.IGNORECASE if sys.platform in ("darwin", "win32") else 0

    def _nome(parola: str) -> str:
        nome = os.path.basename(parola)
        return nome.lower() if _RE_NOMI else nome

    def _togli_commenti(command: str) -> str:
        return command
_WRAPPERS = _SHELL | {"eval", "xargs", "env", "command", "exec", "nohup", "time", "sudo"}
_UNRESOLVED = object()


def _senza_heredoc(command: str) -> str:
    """Il comando senza i corpi di heredoc che vanno a un lettore (cat, tee) o a codice di un
    interprete che non lancia programmi. Nel dubbio il corpo resta (vedi heredoc.py)."""
    return _togli_heredoc(command, lambda h: h.inerte() or h.codice_inerte()
                          or (h.consumatore == "git" and h.quotato))


_MKTEMP = re.compile(r"^\$\(\s*mktemp\b[^()`$;|&]*\)$")
_NUOVA = "<cartella nuova di mktemp>"
# Nel commit in una cartella di mktemp: i soli programmi di cui si sa cosa portano nella cartella.
_NUOVA_AMMESSI = frozenset("mktemp cd pushd popd git cp mv install cat echo printf mkdir touch ls true : test [ rm".split())
# Quelli che portano dentro il contenuto di un file: i loro argomenti si scansionano.
_NUOVA_SORGENTI = frozenset(("cp", "mv", "install", "cat"))


def _mktemp_nuova(testo: str) -> bool:
    """Vero se `$(mktemp …)` crea di sicuro una cartella nuova nel temporaneo di sistema (1/11/2026, F20):
    con -d, senza -p/--tmpdir, e con un modello solo se assoluto o con -t. `mktemp -d ./t.XXXX` crea la
    cartella dentro la cartella corrente, che può stare in un repository vero."""
    m = re.match(r"^\$\(\s*mktemp\b([^()`$;|&]*)\)$", testo.strip())
    if not m:
        return False
    parole = m.group(1).split()
    opzioni = [p for p in parole if p.startswith("-")]
    modelli = [p for p in parole if not p.startswith("-")]
    corte = "".join(o[1:] for o in opzioni if not o.startswith("--"))
    if not ("d" in corte or "--directory" in opzioni):
        return False
    if "p" in corte or any(o.startswith("--tmpdir") for o in opzioni):
        return False
    return all(os.path.isabs(x) or x.startswith("/") or "t" in corte for x in modelli)


def _expand(word: str, variables: dict):
    if _MKTEMP.match(word.strip()):
        return _NUOVA if _mktemp_nuova(word) else _UNRESOLVED
    if "`" in word or "$(" in word:
        return _UNRESOLVED

    def sub(m):
        name = m.group(1) or m.group(2)
        if name in variables:
            return variables[name]
        if name == "HOME":
            return os.path.expanduser("~")
        if os.environ.get(name):
            return os.environ[name]
        raise KeyError(name)

    try:
        expanded = os.path.expanduser(_VAR.sub(sub, word))
    except KeyError:
        return _UNRESOLVED
    return _UNRESOLVED if "$" in expanded else expanded


def _segments(command: str):
    # Senza commentatore e senza commenti (review del 7/11/2026, finding 0): `git status # nota` seguito da un
    # a capo e da `git commit` faceva del commit tre argomenti di git status, e il gate tace.
    lexer = shlex.shlex(_togli_commenti(command), posix=True, punctuation_chars=";&|()\n")
    lexer.commenters = ""
    lexer.whitespace = " \t\r"
    lexer.whitespace_split = True
    segment = []
    for token in lexer:
        if token and set(token) <= set(";&|()\n"):
            if segment:
                yield segment
            segment = []
            for ch in token:
                if ch in "()":
                    yield ["\x00" + ch]  # subshell o $(...): un cd qui dentro non vale fuori
        else:
            segment.append(token)
    if segment:
        yield segment


def _repo_for_command(command: str, cwd: str):
    """Il repository su cui girera' `git commit`.

    Restituisce il percorso, None se non risolvibile (-> ask), oppure False se
    nessun `git commit` viene eseguito davvero (il pattern ha visto la parola
    in un messaggio o in un heredoc). Il parsing rispetta le virgolette: un
    messaggio di commit su più righe non spezza il comando.
    """
    location = os.path.abspath(cwd)
    variables: dict = {}
    try:
        segments = list(_segments(_senza_heredoc(command)))
    except ValueError:
        return None
    nuove = {nome for nome, valore in re.findall(r"(?<![\w$])([A-Za-z_]\w*)=\"?(\$\(\s*mktemp\b[^()`$;|&]*\))",
                                                 command) if _mktemp_nuova(valore)}
    pila = []
    cartelle = []   # la pila di pushd: popd torna alla cartella di prima (1/11/2026, F20)
    inizializzato = False  # un `git init` vero, letto sui token e non sul testo del messaggio
    sorgenti = []     # i file che il comando copia o legge: si scansionano se il commit va in una cartella nuova
    estranei = False  # un programma fuori da _NUOVA_AMMESSI, o una sorgente che non si risolve

    def dentro_nuova(loc):
        return isinstance(loc, str) and loc.startswith(_NUOVA)

    def sposta(loc, target):
        if target is _UNRESOLVED or loc is None:
            return None
        if target.startswith(_NUOVA):
            return _NUOVA
        if os.name == "nt" and target.startswith("/"):
            # Git Bash: /c/Users/... e /tmp/... non sono percorsi di Windows; cygpath li traduce.
            try:
                r = subprocess.run(["cygpath", "-w", target], capture_output=True, text=True, timeout=3)
                target = r.stdout.strip() if r.returncode == 0 and r.stdout.strip() else None
            except (OSError, subprocess.SubprocessError):
                target = None
            if target is None:
                return None
        if dentro_nuova(loc):
            if os.path.isabs(os.path.expanduser(target)):
                return os.path.abspath(os.path.expanduser(target))
            return None if ".." in re.split(r"[\\/]", target) else _NUOVA
        return os.path.abspath(os.path.join(loc, target))

    for tokens in segments:
        if tokens == ["\x00("]:
            pila.append(location)
            continue
        if tokens == ["\x00)"]:
            if pila:
                location = pila.pop()
            continue
        index = 0
        assigned = {}
        while index < len(tokens) and _ASSIGN.match(tokens[index]):
            name, value = _ASSIGN.match(tokens[index]).groups()
            assigned[name] = value
            index += 1
        if tokens[index:index + 1] == ["export"]:
            for token in tokens[index + 1:]:
                if _ASSIGN.match(token):
                    name, value = _ASSIGN.match(token).groups()
                    assigned[name] = value
            index = len(tokens)
        if index >= len(tokens):
            for name, value in assigned.items():
                if value == "$" and name in nuove:
                    variables[name] = _NUOVA  # `D=$(mktemp -d)`: shlex lascia solo "$"
                    continue
                if value == "$":
                    variables.pop(name, None)  # un $( ) che non è un mktemp nuovo: non si risolve
                    continue
                expanded = _expand(value, variables)
                if expanded is _UNRESOLVED:
                    variables.pop(name, None)
                else:
                    variables[name] = expanded
            continue
        tokens = tokens[index:]
        head = _nome(tokens[0])
        if head == "ssh" and re.search(r"\bgit\b.*\bcommit\b", " ".join(tokens[1:]), _RE_NOMI):
            return None  # un commit su un'altra macchina: il suo diff non si legge da qui (31/10/2026)
        if head not in _NUOVA_AMMESSI:
            estranei = True
        else:
            # Un file letto con `<file` o `< file` porta il suo contenuto nel comando (1/11/2026, F19).
            letti = []
            for k, x in enumerate(tokens[1:], start=1):
                m = re.match(r"^\d*<(?![<&])(.*)$", x)
                if m:
                    letti.append(m.group(1) or (tokens[k + 1] if k + 1 < len(tokens) else ""))
            argomenti = []
            if head in _NUOVA_SORGENTI:
                argomenti = [x for x in tokens[1:] if not x.startswith("-") and not re.match(r"^\d*[<>]", x)
                             and x not in letti]
                bersaglio = None
                for k, x in enumerate(tokens[1:], start=1):
                    if x in ("-t", "--target-directory") and k + 1 < len(tokens):
                        bersaglio = tokens[k + 1]
                    elif x.startswith("--target-directory="):
                        bersaglio = x.split("=", 1)[1]
                if head in ("cp", "mv", "install"):
                    if bersaglio is not None:
                        argomenti = [x for x in argomenti if x != bersaglio]  # con -t le altre sono sorgenti
                    else:
                        argomenti = argomenti[:-1]  # l'ultimo è la destinazione
            if head in ("echo", "printf") and any("$(" in x or "`" in x for x in tokens[1:]):
                estranei = True  # `echo "$(<k.txt)"` legge un file che non si vede
            for x in argomenti + [x for x in letti if x]:
                espanso = _expand(x, variables)
                dove = sposta(location, espanso if espanso is _UNRESOLVED else os.path.expanduser(espanso))
                if dove is None:
                    estranei = True
                elif not dove.startswith(_NUOVA):
                    sorgenti.append(dove)
        if head in ("cd", "pushd", "popd"):
            argomenti_cd = [x for x in tokens[1:] if not re.match(r"^\d*[<>]", x) and x != "--"]
            if head == "popd":
                location = cartelle.pop() if cartelle else None
            elif argomenti_cd[:1] == ["-"] or (argomenti_cd and argomenti_cd[0].startswith(("-", "+"))):
                location = None  # `cd -`, `pushd +1`: la cartella non si legge dal testo (F20 F21)
            elif not argomenti_cd:
                if head == "pushd":
                    location = None
                else:
                    location = os.path.expanduser("~")  # `cd` da solo va nella home, anche da mktemp
            else:
                if head == "pushd":
                    cartelle.append(location)
                location = sposta(location, _expand(argomenti_cd[0], variables))
            continue
        # `env VAR=… git …` e `command git …` (4/10/2026, #2832): si tolgono il wrapper e le
        # assegnazioni e si guarda il git che resta. Gli altri wrapper restano "non risolvibile".
        if head in ("env", "command"):
            resto = tokens[1:]
            while resto and _ASSIGN.match(resto[0]):
                resto = resto[1:]
            if resto and _nome(resto[0]) == "git":
                tokens, head = resto, "git"
        if head in _WRAPPERS and "commit" in " ".join(tokens[1:]):
            return None
        if head != "git":
            continue
        index = 1
        # Opzioni globali prima del sottocomando (15/10/2026): `--no-pager`, `-p` e simili
        # si saltano; prima `git --no-pager -C repo commit` usciva come "nessun commit".
        while index < len(tokens) and tokens[index].startswith("-"):
            opzione = tokens[index]
            if opzione in ("-C", "-c"):
                if index + 1 >= len(tokens):
                    return None
                if opzione == "-C":
                    location = sposta(location, _expand(tokens[index + 1], variables))
                    if location is None:
                        return None
                index += 2
                continue
            if opzione.startswith(("--git-dir", "--work-tree", "--namespace", "--config-env", "--exec-path")):
                return None
            index += 1
        if index < len(tokens) and tokens[index] == "init" and dentro_nuova(location):
            inizializzato = True
        if index < len(tokens) and tokens[index] == "commit":
            if dentro_nuova(location):
                # Repo nato nello stesso comando in una cartella di mktemp (31/10/2026). Il diff non si
                # legge prima che il comando giri: si scansionano il testo del comando e i file che vi
                # copia. Vale solo con `git init` nello stesso comando, senza un modo di prendere o
                # mandare commit (clone, fetch, push, remote...) e solo con i programmi di
                # _NUOVA_AMMESSI: `git clone … "$D"; cp <credenziali> .` passava muto col False largo.
                if estranei or not inizializzato or re.search(
                        r"\bgit\b[^;&|\n]*\b(clone|fetch|pull|remote|push|submodule|bundle|am|apply)\b", command,
                        _RE_NOMI):
                    return None
                return (_NUOVA, tuple(sorgenti))
            return location
    if re.search(r"\bgh(?:\.exe)?\s+pr\s+create\b", command, _RE_NOMI):
        return location
    return False


class _Fallita(Exception):
    """La scansione non è partita: causa e rimedio in parole, per il popup (3/11/2026, #4472)."""

    def __init__(self, causa: str, rimedio: str) -> None:
        super().__init__(causa)
        self.causa, self.rimedio = causa, rimedio


def _causa(stderr: str, repo: str) -> _Fallita:
    """Traduce l'errore di git in causa e rimedio. Prima il popup diceva solo "fallita", e la persona
    diceva sì alla cieca: 8 richieste e 7 sì in una settimana, su un'installazione (#4472)."""
    testo = (stderr or "").strip()
    basso = testo.lower()
    if "dubious ownership" in basso:
        return _Fallita("la cartella appartiene a un altro utente del computer, e git non la legge",
                        f'git config --global --add safe.directory "{repo}"')
    if "index.lock" in basso:
        return _Fallita("un altro git sta lavorando su questo repository",
                        "aspetta che finisca; se non gira nessun git, togli .git/index.lock")
    if "index" in basso and ("corrupt" in basso or "bad signature" in basso or "bad index" in basso
                            or "smaller than expected" in basso):
        return _Fallita("l'indice di git è rotto", f"git status nella cartella {repo}, per vedere l'errore")
    prima = testo.splitlines()[0][:160] if testo else "git è uscito con un errore senza messaggio"
    return _Fallita(f"git ha risposto: {prima}", f'git -C "{repo}" diff --cached --stat, per vedere l\'errore intero')


def _git(command: list, repo: str, **kw) -> subprocess.CompletedProcess:
    # I messaggi di git in inglese: _causa li riconosce per parola, e un git in italiano diceva
    # "versione indice non valida" (prova del 4/11/2026). LANGUAGE cambia solo i messaggi, non il diff.
    env = dict(os.environ, LANGUAGE="en")
    try:
        return subprocess.run(command, capture_output=True, timeout=4, check=False, env=env, **kw)
    except subprocess.TimeoutExpired:
        raise _Fallita("git ha impiegato più di 4 secondi a mostrare le modifiche (repository grande o disco lento)",
                       f'git -C "{repo}" diff --cached --stat, per vedere quanto pesa') from None
    except OSError as e:
        raise _Fallita(f"git non si avvia ({e.strerror or e})", "git --version, per vedere se git è installato") from None


# Le opzioni di git commit e di git add che prendono un valore staccato (review del 7/11/2026, finding 7).
_COMMIT_CON_VALORE = frozenset(("--message", "--file", "--reuse-message", "--reedit-message", "--author", "--date",
                                "--template", "--fixup", "--squash", "--cleanup", "--trailer", "--pathspec-from-file"))
_COMMIT_LETTERE_VALORE = "mFCct"
_LIMITE_FILE = 200


def _invocazioni_git(command: str):
    """(sottocomando, argomenti) di ogni git del comando, dopo le opzioni globali."""
    try:
        segmenti = list(_segments(_senza_heredoc(command)))
    except ValueError:
        return []
    out = []
    for tokens in segmenti:
        i = 0
        while i < len(tokens) and (_ASSIGN.match(tokens[i]) or _nome(tokens[i]) in ("env", "command")):
            i += 1
        if i >= len(tokens) or _nome(tokens[i]) != "git":
            continue
        i += 1
        while i < len(tokens) and tokens[i].startswith("-"):
            i += 2 if tokens[i] in ("-C", "-c") else 1
        if i < len(tokens):
            out.append((tokens[i], tokens[i + 1:]))
    return out


def _percorsi_commit(args) -> list:
    """I path che `git commit` nomina: git committa il loro contenuto di lavoro, non quello in stage."""
    percorsi, i, dopo = [], 0, False
    while i < len(args):
        a = args[i]
        if dopo or not a.startswith("-") or a == "-":
            percorsi.append(a)
        elif a == "--":
            dopo = True
        elif a.startswith("--"):
            if "=" not in a and a in _COMMIT_CON_VALORE:
                i += 1
        else:
            corpo = a[1:]
            for k, ch in enumerate(corpo):
                if ch in _COMMIT_LETTERE_VALORE:
                    if k == len(corpo) - 1:
                        i += 1  # `-m testo`, `-am testo`: il valore è la parola dopo
                    break
        i += 1
    return percorsi


def _forzati_add(args) -> list:
    """I path di `git add -f`: git li aggiunge anche se ignorati, e ls-files --exclude-standard non li vede."""
    if not any(a in ("-f", "--force") or (a.startswith("-") and not a.startswith("--") and "f" in a) for a in args):
        return []
    return [a for a in args if not a.startswith("-")]


def _leggi_percorsi(repo: str, percorsi) -> list:
    """Il contenuto dei file nominati, come righe aggiunte. Oltre _LIMITE_FILE file solleva _Fallita."""
    parti, visti = [], 0
    for p in percorsi:
        pieno = os.path.join(repo, os.path.expanduser(p))
        nomi = [os.path.join(r, f) for r, _, fs in os.walk(pieno) for f in fs] if os.path.isdir(pieno) else [pieno]
        for nome in nomi:
            visti += 1
            if visti > _LIMITE_FILE:
                raise _Fallita(f"git add -f nomina più di {_LIMITE_FILE} file, oltre quelli che la guardia legge",
                               "aggiungi i file a gruppi, oppure git status per vedere cosa entra")
            try:
                with open(nome, encoding="utf-8", errors="ignore") as f:
                    parti.append("\n".join("+" + riga for riga in f.read(200_000).splitlines()))
            except OSError:
                continue
    return parti


def _diff(repo: str, commit_all: bool, add_prima: bool = False, percorsi=(), forzati=()) -> str:
    """Il diff da scansionare. Se git non lo dà, solleva _Fallita con causa e rimedio."""
    commands = [["git", "-C", repo, "diff", "--cached", "--no-color", "--no-ext-diff", "--no-textconv", "--unified=0"]]
    if commit_all or add_prima:
        commands.append(["git", "-C", repo, "diff", "--no-color", "--no-ext-diff", "--no-textconv", "--unified=0"])
    elif percorsi:
        # `git commit -m x a.py` committa a.py com'è nella cartella, anche se non è in stage (finding 7).
        commands.append(["git", "-C", repo, "diff", "--no-color", "--no-ext-diff", "--no-textconv", "--unified=0",
                         "--", *percorsi])
    output = []
    for command in commands:
        # Un file non UTF-8 in stage (un CSV della banca in Latin-1) faceva cadere la decodifica e ogni
        # commit chiedeva conferma per "scansione fallita" (#4047, 29/10/2026). Un segreto è ASCII:
        # sostituire i byte non validi non lo nasconde.
        result = _git(command, repo, encoding="utf-8", errors="replace")
        if result.returncode:
            raise _causa(result.stderr, repo)
        output.append(result.stdout)
    if add_prima:
        # 9/10/2026: `git add X && git commit` mette X in stage dopo questo controllo.
        # Si leggono anche i file non tracciati che git add potrebbe aggiungere.
        # surrogateescape: un nome di file non UTF-8 resta apribile con open().
        result = _git(["git", "-C", repo, "ls-files", "--others", "--exclude-standard", "-z"], repo,
                      encoding="utf-8", errors="surrogateescape")
        if result.returncode:
            raise _causa(result.stderr, repo)
        nuovi = [n for n in result.stdout.split("\0") if n]
        if len(nuovi) > _LIMITE_FILE:
            # Prima si leggevano i primi 200 e il resto passava muto: il primo commit di un progetto li supera
            # spesso (finding 7).
            raise _Fallita(f"ci sono {len(nuovi)} file nuovi, oltre i {_LIMITE_FILE} che la guardia legge",
                           "aggiungi i file a gruppi, oppure controlla con git status cosa entra nel commit")
        for nome in nuovi:
            try:
                with open(os.path.join(repo, nome), encoding="utf-8", errors="ignore") as f:
                    output.append("\n".join("+" + riga for riga in f.read(200_000).splitlines()))
            except OSError:
                continue
    output += _leggi_percorsi(repo, forzati)
    return "\n".join(part for part in output if part)


def _leggi_sorgenti(percorsi) -> str | None:
    """Il contenuto dei file e delle cartelle copiati (al massimo 200 file, 200 KB ciascuno). None se troppi."""
    parti, visti = [], 0
    for percorso in percorsi:
        candidati = [percorso]
        if os.path.isdir(percorso):
            candidati = [os.path.join(r, f) for r, _, fs in os.walk(percorso) for f in fs]
        for nome in candidati:
            visti += 1
            if visti > 200:
                return None
            try:
                with open(nome, encoding="utf-8", errors="ignore") as f:
                    parti.append(f.read(200_000))
            except OSError:
                continue
    return "\n".join(parti)


def _scansiona_nuova(command: str, sorgenti) -> int:
    """Commit in una cartella appena creata da mktemp: si scansionano il comando e i file copiati."""
    contenuto = _leggi_sorgenti(sorgenti)
    if contenuto is None:
        return _ask("scansione-fallita", "Commit in una cartella nuova con troppi file copiati da scansionare: "
                    "conferma prima di proseguire.")
    testo = command + "\n" + contenuto
    uniq = list(dict.fromkeys(name for rx, name in COMPILED if rx.search(testo)))
    if not uniq:
        return 0
    return _ask(FAMIGLIA.get(uniq[0], "segreto-altro"),
                "Possibile secret nei file del commit (cartella nuova): " + ", ".join(uniq[:5]) + ". "
                "Un leak pushato è irreversibile. Conferma solo dopo aver "
                "verificato che non sia una credenziale reale.")


def _ask(regola: str, reason: str) -> int:
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "ask", "permissionDecisionReason": reason}}))
    _regola(regola)
    return 0


def main() -> int:
    try:
        if hasattr(signal, "SIGALRM"):
            signal.alarm(6)
        data = json.loads(sys.stdin.buffer.read().decode("utf-8"))
    except Exception:
        return 0

    if data.get("tool_name") not in ("Bash", "Monitor"):  # Monitor lancia comandi shell (19/10/2026)
        return 0
    command = (data.get("tool_input") or {}).get("command", "")
    if not isinstance(command, str) or not command:
        return 0
    cwd = data.get("cwd") or os.path.expanduser("~")
    repo = _repo_for_command(command, cwd)
    if repo is False:
        return 0
    if isinstance(repo, tuple):
        return _scansiona_nuova(command, repo[1])
    if not repo:
        return _ask("repo-ignoto", "Repository destinatario del commit non risolvibile: conferma prima di proseguire.")
    # Una cartella calcolata che non esiste vuol dire un cd che fallisce: la shell resta dov'era, e il
    # commit gira nel repository di prima (1/11/2026, F21). Non è "fuori da un repository".
    if not os.path.isdir(repo):
        # Una cartella che lo stesso comando crea prima del cd (`mkdir nuovo && cd nuovo && git init …`,
        # `git clone … && cd y && … git commit`) è nuova: si scansiona il testo del comando, come per mktemp
        # (review delle correzioni del 1/11/2026). Il caso di F21 resta: un cd che fallisce senza crearla.
        nome = os.path.basename(os.path.normpath(repo))
        if re.search(r"\b(?:mkdir\b|git\b[^;&|\n]*\b(?:clone|init)\b)[^;&|\n]*" + re.escape(nome), command,
                     _RE_NOMI):
            return _scansiona_nuova(command, [])
        return _ask("repo-ignoto", "Il commit gira dopo un cd verso una cartella che non esiste: la shell resta "
                    "nella cartella di prima, e il repository non si legge. Conferma prima di proseguire.")
    # Fuori da un repository Git il commit fallisce da solo: niente da scansionare.
    try:
        dentro = subprocess.run(["git", "-C", repo, "rev-parse", "--git-dir"], capture_output=True,
                                text=True, timeout=4, check=False).returncode == 0
    except Exception:
        dentro = True
    if not dentro:
        return 0

    # `git commit -a/--all` mette in stage i file tracciati modificati DURANTE il
    # commit: al momento di questo check (PreToolUse) l'index non li contiene ancora,
    # quindi il solo `diff --cached` mancherebbe un secret in un file già tracciato.
    commit_all = bool(re.search(r"\bcommit\b[^|;&]*\s-{1,2}(a\b|all\b|[a-zA-Z]*a[a-zA-Z]*\b)", command))
    add_prima = bool(re.search(r"\bgit\b[^;&|\n]*\sadd\b", command, _RE_NOMI))
    invocazioni = _invocazioni_git(command)
    percorsi = next((_percorsi_commit(a) for s, a in invocazioni if s == "commit"), [])
    forzati = [p for s, a in invocazioni if s == "add" for p in _forzati_add(a)]
    try:
        out = _diff(repo, commit_all, add_prima, percorsi, forzati)
    except _Fallita as f:
        out = f
    except Exception as e:
        out = _Fallita(f"errore interno della guardia ({type(e).__name__})",
                       "/diagnosi, oppure /segnala per dirlo a chi mantiene Arturo")
    finally:
        if hasattr(signal, "SIGALRM"):
            signal.alarm(0)
    if isinstance(out, _Fallita):
        # La conferma resta e il nome della regola non cambia: la telemetria resta confrontabile.
        return _ask("scansione-fallita", f"La scansione dei segreti non è partita: {out.causa}. Per ripararla: "
                    f"{out.rimedio}. Se confermi, il commit parte senza controllo dei segreti.")

    if not out and not add_prima:
        return 0

    added = "\n".join(
        ln[1:] for ln in out.splitlines()
        if ln.startswith("+") and not ln.startswith("+++")
    )
    if add_prima:
        # Un file scritto nello stesso comando prima di `git add` non esiste ancora quando la guardia legge il
        # repository: si scansiona anche il testo del comando, senza il messaggio di commit (1/11/2026, F22).
        added += "\n" + re.sub(r"""(?:\s-m|\s--message)(?:=|\s+)(?:"[^"]*"|'[^']*'|\S+)""", " ", command)
    if not added.strip():
        return 0

    found = []
    for rx, name in COMPILED:
        if rx.search(added):
            found.append(name)
    if not found:
        return 0

    uniq = list(dict.fromkeys(found))
    # La regola è la famiglia del primo pattern trovato: "Google API key" -> segreto-cloud. Il nome del
    # fornitore resta solo nel messaggio per la persona, che non esce da questo computer.
    return _ask(FAMIGLIA.get(uniq[0], "segreto-altro"),
                "Possibile secret nel diff staged: " + ", ".join(uniq[:5]) + ". "
                "Un leak pushato è irreversibile. Conferma solo dopo aver "
                "verificato che non sia una credenziale reale.")


if __name__ == "__main__":
    # Claude Code scrive e legge in UTF-8. Su Windows la pipe è in cp1252 (16/10/2026).
    for _flusso in (sys.stdout, sys.stderr):
        try:
            _flusso.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass
    sys.exit(main())
