"""Il pre-filtro di bash-dispatcher.sh: quali guardie partono per un comando (#6327, 22/11/2026).

Modulo del dispatcher, non un hook: lo chiama evento_bash.py leggi, nello stesso processo che legge l'evento.
Fino al 22/11/2026 questi confronti erano regex di bash: circa 13 µs per carattere, 18 secondi su 300.000
caratteri, e per questo il dispatcher chiedeva conferma oltre 100.000. Qui gli stessi pattern girano in
Python, che legge il comando in pochi millisecondi.

I pattern sono scritti come in bash, POSIX ERE (`[[:space:]]`, `$` a fine testo), e `_ere` li traduce in regex
Python. Ogni pattern si spezza nelle sue alternative di primo livello, e ognuna si cerca da sola: Python trova
in fretta un'alternativa che comincia con un testo fisso, mentre una sola regex con cento alternative le prova
tutte a ogni carattere. Il risultato è lo stesso, perché il pattern intero trova qualcosa se lo trova una delle
sue alternative.

Il risultato è un elenco di parole, le viste: ognuna dice al dispatcher che una guardia deve partire, o che
il comando è git puro. Il dispatcher lancia le guardie nell'ordine di prima, e solo le guardie decidono.
`analizza` non decide niente: un errore qui dentro arriva a evento_bash.py, che lascia vuoti tutti i campi,
e il dispatcher chiede conferma.

Le classi POSIX diventano classi ASCII. Dove la classe è negata (`[^[:alnum:]_.-]` come confine di una parola)
un carattere non ASCII conta come confine, quindi Python trova almeno ciò che trovava bash. Il confronto
senza maiuscole (`somiglia` del dispatcher, su macOS e Windows) è re.IGNORECASE in ASCII.

Banco: tests/test_prefiltro_python_2026_11_22.py. Solo libreria standard, Python 3.8 o successivo.
"""
import importlib.util
import json
import os
import re

_QUI = os.path.dirname(os.path.abspath(__file__))

# --- da POSIX ERE a regex Python ---
_CLASSI = {
    "space": " \\t\\n\\r\\f\\v",
    "alnum": "A-Za-z0-9",
    "alpha": "A-Za-z",
    "digit": "0-9",
    "upper": "A-Z",
    "lower": "a-z",
    "cntrl": "\\x00-\\x1f\\x7f",
}


def _carattere(c):
    return c if c.isalnum() and c.isascii() else "\\" + c if c in "\\]^-[" else re.escape(c)


def _parentesi(p, i):
    """La classe fra parentesi quadre che comincia in p[i]: (regex Python, indice dopo la `]`)."""
    j = i + 1
    neg = p[j:j + 1] == "^"
    if neg:
        j += 1
    voci = []
    primo = True
    while j < len(p):
        c = p[j]
        if c == "]" and not primo:
            return "[" + ("^" if neg else "") + "".join(voci) + "]", j + 1
        primo = False
        if p.startswith("[:", j):
            k = p.index(":]", j + 2)
            voci.append(_CLASSI[p[j + 2:k]])
            j = k + 2
            continue
        if j + 2 < len(p) and p[j + 1] == "-" and p[j + 2] != "]":
            voci.append(_carattere(c) + "-" + _carattere(p[j + 2]))
            j += 3
            continue
        voci.append(_carattere(c))
        j += 1
    raise ValueError("parentesi quadra aperta: " + p)


def _ere(p):
    """Un pattern POSIX ERE come lo legge `[[ =~ ]]` di bash, scritto come regex Python (con re.S)."""
    out = []
    i = 0
    while i < len(p):
        c = p[i]
        if c == "\\":
            out.append(re.escape(p[i + 1]))
            i += 2
        elif c == "[":
            r, i = _parentesi(p, i)
            out.append(r)
        elif c == "$":
            out.append("\\Z")
            i += 1
        else:
            out.append(c)
            i += 1
    return "".join(out)


def _temperata(p):
    """Come `_ere`, ma una corsa `.*` o `[^…]*` si ferma dove ricomincia ciò che la precede:
    `rm[[:space:]][^|;&]*X` diventa `rm\\s(?:(?!rm\\s)[^|;&])*X`.

    Perché: Python prova la regex da ogni punto in cui comincia il prefisso, e ogni volta scorre la corsa fino in
    fondo. Con molte parole `rm ` (anche dentro `form `, `term `) in una riga senza `|;&` il tempo cresce col
    quadrato: 217 secondi su 300.000 caratteri. Il motore di bash è lineare e non ne soffriva.
    Il risultato non cambia quando ciò che ferma la corsa non può cominciare dentro di lei e finire dopo l'inizio
    del pezzo che segue: allora l'ultimo punto della corsa dove ricomincia porta allo stesso confronto riuscito.
    Vale per i pattern di Pattern(..., lineare=True), e il banco lo prova contro `_ere` su testi casuali e sui
    comandi veri. Due regole, nell'ordine del testo dell'alternativa:
    - la prima corsa si ferma sul prefisso intero, dall'inizio dell'alternativa;
    - una corsa dopo si ferma sul solo pezzo fra lei e la corsa prima, se tutte le corse prima sono `.*`: una
      corsa `.*` assorbe qualunque testo, e il confronto si sposta sull'ultimo pezzo (`find … -name … -exec`).
      Dopo una corsa più stretta resta come in bash: sui comandi veri `git -c x … push` cambiava risultato."""
    out, _ = _sequenza(p, 0, "", "", {"stelle": False, "punti": True})
    return out


def _sequenza(p, i, ereditato, pezzo_ereditato, stato):
    """Una sequenza fino a `|`, `)` o alla fine. `ereditato` è il prefisso tradotto che sta prima di lei,
    `pezzo_ereditato` ciò che sta fra lei e l'ultima corsa (None se non si sa). `stato` dice se una corsa è già
    comparsa prima nel testo dell'alternativa, e se tutte quelle comparse sono `.*`."""
    pezzi = []
    pezzo = pezzo_ereditato
    while i < len(p) and p[i] not in "|)":
        c = p[i]
        largo = False
        if c == "\\":
            atomo, i = re.escape(p[i + 1]), i + 2
        elif c == "[":
            atomo, i = _parentesi(p, i)
            largo = atomo.startswith("[^")
        elif c == "(":
            alt, i = [], i + 1
            prima = stato["stelle"]
            while True:
                s, i = _sequenza(p, i, ereditato + "".join(pezzi), pezzo, stato)
                alt.append(s)
                if p[i] == "|":
                    i += 1
                    continue
                i += 1  # la `)`
                break
            atomo = "(" + "|".join(alt) + ")"
            if stato["stelle"] and not prima:
                pezzo = None  # una corsa dentro il gruppo: il pezzo dopo di lei non si scrive da qui
        elif c == "$":
            atomo, i = "\\Z", i + 1
        else:
            atomo, i = c, i + 1
            largo = c == "."
        quant = p[i] if i < len(p) and p[i] in "*+?" else ""
        i += len(quant)
        prefisso = ereditato + "".join(pezzi)
        corsa = largo and quant in ("*", "+")
        if quant == "*" and largo and not stato["stelle"] and prefisso:
            pezzi.append("(?:(?!" + prefisso + ")" + atomo + ")*")
        elif quant == "*" and largo and stato["stelle"] and stato["punti"] and pezzo:
            pezzi.append("(?:(?!" + pezzo + ")" + atomo + ")*")
        else:
            pezzi.append(atomo + quant)
            if pezzo is not None and not corsa:
                pezzo += atomo + quant
        if corsa:
            stato["punti"] = stato["punti"] and atomo == "." and quant == "*"
            stato["stelle"] = True
            pezzo = ""
    return "".join(pezzi), i


def _alternative(p):
    """Le alternative di primo livello di un pattern ERE, fuori da parentesi tonde e quadre."""
    parti, inizio, profondo, i = [], 0, 0, 0
    while i < len(p):
        c = p[i]
        if c == "\\":
            i += 2
            continue
        if c == "[":
            i = _parentesi(p, i)[1]
            continue
        if c == "(":
            profondo += 1
        elif c == ")":
            profondo -= 1
        elif c == "|" and profondo == 0:
            parti.append(p[inizio:i])
            inizio = i + 1
        i += 1
    parti.append(p[inizio:])
    return parti


# Due alternative dove la forma temperata non basta: il prefisso finisce con uno spazio, e uno spazio come l'a capo
# o il tab è anche il carattere che chiude il confronto. Le forme qui sotto trovano gli stessi testi, e il banco le
# prova contro la traduzione esatta. La corsa finale `[^;&|]*[;&[:cntrl:]]` diventa `[^;&|[:cntrl:]]*[;&[:cntrl:]]`:
# in tutte e due il confronto riesce se il primo carattere fra `;`, `&`, `|` e i caratteri di controllo non è `|`.
# In wget la corsa si ferma su un `wget` col solo spazio: un `wget` seguito da un a capo chiude già la corsa.
_SP = "[ \\t\\n\\r\\f\\v]"
_A_MANO = {
    "wget[[:space:]][^;&|]*[;&[:cntrl:]]":
        "wget" + _SP + "(?:(?!wget )[^;&|\\x00-\\x1f\\x7f])*[;&\\x00-\\x1f\\x7f]",
    "curl[[:space:]][^;&|]*(-[a-zA-Z]*[oOJ]|--output|--remote-name)[^;&|]*[;&[:cntrl:]]":
        "curl" + _SP + "(?:(?!curl" + _SP + ")[^;&|])*(-[a-zA-Z]*[oOJ]|--output|--remote-name)"
        "[^;&|\\x00-\\x1f\\x7f]*[;&\\x00-\\x1f\\x7f]",
}


_MINUSCOLI = {}


def _minuscolo(testo):
    """Il testo in minuscolo, ricordato per gli ultimi testi: lo stesso comando si confronta con molti pattern.
    str.lower non toglie mai una lettera ASCII, quindi una parola che c'è con re.IGNORECASE c'è anche qui."""
    voce = _MINUSCOLI.get(id(testo))
    if voce is None or voce[0] is not testo:
        if len(_MINUSCOLI) > 16:
            _MINUSCOLI.clear()
        voce = _MINUSCOLI[id(testo)] = (testo, testo.lower())
    return voce[1]


class Pattern:
    """Un pattern del pre-filtro. `trova` è `[[ testo =~ pattern ]]`, `somiglia` è la funzione del dispatcher:
    senza maiuscole se il disco le ignora (macOS e Windows)."""

    def __init__(self, ere, lineare=False, serve=()):
        self.ere = ere
        self.lineare = lineare
        # Le parole senza cui il pattern non trova niente, in minuscolo: se nel testo non ce n'è nessuna, il
        # pattern non si compila nemmeno. Compilare tutte le regex costa circa 7 ms a ogni comando. Il banco PB05
        # prova che ogni alternativa contiene una di queste parole.
        self.serve = serve
        self._esatte = None
        self._senza = None

    def _inutile(self, testo):
        return bool(self.serve) and not any(s in _minuscolo(testo) for s in self.serve)

    def _compila(self, flag, esatta=False):
        if esatta:
            return [re.compile(_ere(a), re.S | re.A | flag) for a in _alternative(self.ere)]
        return [re.compile(r, re.S | re.A | flag) for r in _tradotte(self)]

    def trova(self, testo):
        if self._inutile(testo):
            return False
        if self._esatte is None:
            self._esatte = self._compila(0)
        return any(r.search(testo) for r in self._esatte)

    def senza_maiuscole(self, testo):
        if self._inutile(testo):
            return False
        if self._senza is None:
            self._senza = self._compila(re.I)
        return any(r.search(testo) for r in self._senza)


# Le regex Python di ogni pattern stanno già tradotte in prefiltro_regex.py, un file generato da questo: tradurle
# costa circa 4 ms a ogni comando. Valgono solo se l'impronta sha256 di questo file è quella scritta lì, quindi una
# modifica qui le spegne finché non si rigenerano (`python3 hooks/prefiltro_bash.py genera`): il pre-filtro
# traduce da sé, con lo stesso risultato, e il banco PB06 diventa rosso. È codice versionato e non una cache
# scrivibile: chi cambiasse le regex lì cambierebbe un file di Arturo, come cambiare questo.
_TRADOTTE = {"dati": None}


def _impronta():
    import hashlib
    with open(os.path.join(_QUI, "prefiltro_bash.py"), "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def _chiave(pattern):
    return ("L:" if pattern.lineare else "E:") + pattern.ere


def _traduci(pattern):
    alt = _alternative(pattern.ere)
    return [(_A_MANO.get(a) or _temperata(a)) if pattern.lineare else _ere(a) for a in alt]


def _tradotte(pattern):
    if _TRADOTTE["dati"] is None:
        _TRADOTTE["dati"] = {}
        try:
            generato = _modulo("arturo_prefiltro_regex", "prefiltro_regex.py")
            if generato.IMPRONTA == _impronta() and isinstance(generato.REGEX, dict):
                _TRADOTTE["dati"] = generato.REGEX
        except Exception:
            pass
    tradotte = _TRADOTTE["dati"].get(_chiave(pattern))
    return tradotte if isinstance(tradotte, list) else _traduci(pattern)


def genera():
    """Il testo di prefiltro_regex.py per il sorgente di adesso."""
    righe = ['"""Generato da prefiltro_bash.py (`python3 hooks/prefiltro_bash.py genera`): non modificare a mano.',
             "", "Le regex Python dei pattern del pre-filtro, già tradotte. Valgono solo con l'impronta del sorgente.",
             '"""', "IMPRONTA = " + repr(_impronta()), "REGEX = {"]
    for nome in sorted(globals()):
        oggetto = globals()[nome]
        if isinstance(oggetto, Pattern):
            righe.append("    # " + nome)
            righe.append("    " + repr(_chiave(oggetto)) + ": [")
            righe.extend("        " + repr(r) + "," for r in _traduci(oggetto))
            righe.append("    ],")
    righe.append("}")
    return "\n".join(righe) + "\n"


# --- I pattern, come stavano in bash-dispatcher.sh fino al 22/11/2026 ---

# --- timeout su macOS ---
# Sui Mac `timeout` non esiste: `command not found` va su stderr, la pipeline riceve stdout vuoto e la diagnosi
# finisce sul servizio sbagliato. Esclusi ssh, docker exec e heredoc: lì `timeout` gira su una macchina Linux.
# Se `timeout` c'è davvero lo controlla il dispatcher (_timeout_c_e): qui si guarda solo il testo.
PATTERN_TIMEOUT = Pattern(
    "(^|[;&|(`\n])[[:space:]]*((sudo|env|command|exec)[[:space:]]+)?timeout[[:space:]]+"
    "(-[^[:space:]]+[[:space:]]+([A-Z]+[[:space:]]+)?)*[0-9]")
PATTERN_REMOTE = Pattern(r"(^|[[:space:];&|(])(ssh|docker[[:space:]]+exec|kubectl[[:space:]]+exec)[[:space:]]|<<")

# Una scrittura su file: una redirezione verso un file che non è /dev/null, o un programma che scrive il file
# che riceve. Il percorso protetto può non comparire nel testo: un link (`echo x > lnk/settings.json`), un glob
# (`~/.claud[e]/…`), una cartella raggiunta con un cd che il pre-filtro non segue. block-dangerous risolve il
# percorso vero, quindi parte su ogni scrittura (11/11/2026, #5262, review n. 4 e 7). Costa un processo in più
# sui comandi che scrivono; le letture restano fuori.
# 20/11/2026 (#5361, rilievo 1 della revisione strutturale dell'11/11): anche gpatch, chgrp e git checkout,
# restore e reset, che `_writes_config` giudica. Senza, `git -C lnk checkout -- settings.json` con lnk verso
# ~/.claude passava: la guardia chiedeva, il pre-filtro non la chiamava. Un programma che `_writes_config`
# impara a giudicare entra anche qui, con un caso nel banco GC08 (tests/test_guardie_cieche_2026_11_11.py).
PATTERN_SCRIVE = Pattern(
    r"(^|[^-0-9&>])[0-9]?>[>|]?[[:space:]]*[^&>([:space:]]|&>|(^|[^[:alnum:]_.-])(cp|mv|tee|dd|install|ln|rsync"
    r"|touch|truncate|sponge|tar|gtar|bsdtar|unzip|patch|gpatch|ditto|chmod|chown|chgrp)([[:space:]]|$)"
    r"|(^|[^[:alnum:]_.-])git([[:space:]][^;&|]*)?[[:space:]](checkout|restore|reset)([[:space:]]|$)", lineare=True)

# gh in qualunque posizione (9/10/2026): dopo un a capo, in una subshell, col path completo.
# gh-destructive-guard legge già tutto il comando.
PATTERN_GH_ANY = Pattern(r"(^|[^[:alnum:]_.-])gh[[:space:]]")
PATTERN_API_GITHUB = Pattern(r"api\.github\.com")
PATTERN_GIT_TEXT = Pattern(
    r"(^|[;&|][[:space:]]*)git[[:space:]]+(-C[[:space:]]+[^[:space:]]+[[:space:]]+)?"
    r"(commit|log|show|tag|stash[[:space:]]+(push|save))")

PATTERN_COMMS = Pattern(
    r"""(^|[[:space:];|&("'`])(sendmail|mailx|mutt|msmtp|swaks|mail)([[:space:]]|$)|mailto:|smtps?://"""
    r"|gws[[:space:]].*(messages[[:space:]]+send|send[[:space:]]+message|gmail[[:space:]].*(\+send"
    r"|drafts[[:space:]]+send|forwardingAddresses|updateAutoForwarding|delegates|filters))|osascript.*(Mail|Messages)"
    r"|api\.telegram\.org|hooks\.slack\.com|slack\.com/api/chat|api\.sendgrid|api\.mailgun|api\.postmarkapp"
    r"|api\.resend|api\.mailjet|api\.brevo|smtp2go|api\.sparkpost|api\.elasticemail|zeptomail|mailchannels"
    r"|email[.-][a-z0-9-]*\.amazonaws|hooks\.zapier|hook\.[a-z0-9.]*make\.com|integromat"
    r"|graph\.microsoft\.com.*sendmail|gmail\.googleapis\.com.*messages/send|discord(app)?\.com/api/webhooks"
    r"|api\.twilio\.com|graph\.facebook\.com.*messages|whatsapp[_/-]?send|telegram[_/-]?send|smtplib|SMTP_SSL"
    r"|http\.client|git[[:space:]]+(send-email|imap-send)"
    # 21/11/2026 (#6259, S8): l'invio con gws dietro una variabile (`G=gws; $G gmail +send`), gli inviti di
    # calendario con sendUpdates, la condivisione di un file di Drive, mailgun sugli host regionali, nodemailer e
    # i link che aprono WhatsApp o Telegram con il testo già scritto.
    r"|\+send([[:space:]]|$)|drafts[[:space:]]+send|sendUpdates|sendNotifications|permissions[[:space:]]+(create"
    r"|update)|mailgun\.net|nodemailer|wa\.me/|whatsapp\.com/send|whatsapp://|t\.me/share|tg://msg", lineare=True)

# block-dangerous: rm ricorsivo (tree protetti), bw export, scrittura config/hook,
# scrittura su git hook e servizi di avvio automatico,
# lettura segreti via shell (.ssh/id_*/credentials/.pem...), docker volume rm.
# 20/10/2026: la cartella delle credenziali anche senza la barra finale (`find ~/.claude/data/credentials | xargs cat`).
# 10/11/2026 (#5097): dopo la pipe anche `|&`, un commento, un gruppo che si apre e sudo o doas con le opzioni.
# 10/11/2026 (#5122): nel gruppo anche altri comandi prima dell'interprete, separati da `;`, `&` o a capo
# (`[:cntrl:]` contiene l'a capo, che fra parentesi quadre non si scrive `\n`).
# 11/11/2026 (#5261): la parola unlock: il nome del file scritto (uno sblocco, settings.json) sta nella
# sorgente di un cp e non dopo `.claude/`. Il pre-filtro risparmia un processo: un sì in più costa poco, un
# no è un buco.
# 20/11/2026 (#5361, rilievo 3): tolte le alternative che contenevano `\.claude` (cp, mv, install, ln e rsync
# vicino a `.claude`, `.claude/settings`, `.claude/arturo`, `.claude/data/credentials`, `.claude/…unlock`) e
# PATTERN_CD_CLAUDE: dal #5262 le copre tutte `\.claude` da solo. Se un giorno `\.claude` si restringe, le
# forme da coprire di nuovo sono nei banchi GC01 e GC04 (tests/test_guardie_cieche_2026_11_11.py).
# 13/11/2026 (HK-6): l'avvio automatico su Windows, la cartella Start Menu/Programs/Startup, i profili di
# PowerShell, schtasks, reg add/import/restore/load, sc create, Register-ScheduledTask e New-Service.
# 11/11/2026 (#5262, review n. 7): ogni comando che nomina `.claude` (`~/.claude//settings.json`, `H=~/.claude`,
# `~/.claude.json`), e una variabile al posto del programma (`X=rm; $X -rf`): block-dangerous li risolve già.
# 17/10/2026 (#3506): i file .env (anche .env.local), shutil.rmtree. git clean ha un pattern suo,
# PATTERN_GIT_CLEAN, che parte prima dello skip git-puro.
# 7/11/2026 (review, finding 1 8 9): l'interprete dopo la pipe chiuso da ; ) " o && e con sudo -E; ogni
# sed (le regole sed-w e sed-e le giudica block-dangerous); rmtree anche senza il prefisso shutil.;
# Remove-Item e powershell o pwsh, che su Windows cancellano cartelle.
# 13/11/2026 (HK-5): powershell e pwsh dopo la pipe (`curl u | powershell -`), rmSync, rmdirSync e fs.rm( di
# node, che block-dangerous giudica come shutil.rmtree.
# 21/11/2026 (#6279): un nome che comincia col punto e porta un glob o una graffa, anche senza la barra
# dopo: `cd ~/.s?? && cat i?_ed25519`, `cat ~/.s{sh,x}/i?_ed25519`, `cat ~/{.ssh,x}/i*`, `cat ~/.np?rc`,
# `grep -r x ~/.s??`. Il percorso lo risolve block-dangerous (_segreti_risolti). Passa anche un filtro di jq
# come `.items[]`: costa un processo in più e block-dangerous tace. Anche un glob dopo `.config/`, `.docker/` o
# `.kube/` (`head ~/.config/g?/h*`), e `shopt -s dotglob` o `setopt globdots`, con cui `*` entra in `.ssh`.
# Banco: tests/test_glob_segreti_2026_11_21.py.
PATTERN_DANGER = Pattern(
    r":\(\)|/dev/(sd|nvme|disk|hd)|chmod[[:space:]]+-R[[:space:]]+0*777|chown[[:space:]]+-R"
    r"|\|&?[[:space:]]*(#.*)?([({][[:space:]]*([^|]*[;&[:cntrl:]][[:space:]]*)?)?((sudo|doas)[[:space:]][^|;&]*)?"
    r"(bash|sh|zsh|fish|python3?|perl|ruby|node|php|powershell|pwsh)([^[:alnum:]_.-]|$)"
    r"|<\([[:space:]]*(curl|wget|fetch)|eval[[:space:]]|mkfs\.|(^|[^[:alnum:]_.-])(del|erase|rd|rmdir|format(\.com)?)"
    r"[[:space:]]|rm[[:space:]][^|;&]*(-[a-zA-Z]*[rR][a-zA-Z]*|--recursive)"
    r"|find[[:space:]].*(-delete|-(exec|execdir|ok|okdir)[[:space:]].*(rm|unlink|shred)|xargs[^|;&]*(rm|unlink|shred))"
    r"|bw[[:space:]].*export|unlock|\.claude|(^|[;&|(){[:cntrl:]])[[:space:]]*\$[{A-Za-z_]|CLAUDE(\.local)?\.md"
    r"|firme/|rilasci\.allowed_signers|aggiornamenti\.py|aggiorna-applica\.sh|arturo/radice|\.git/hooks"
    r"|LaunchAgents|\.config/(systemd/user|autostart)|Start[[:space:]]+Menu|profile\.ps1|schtasks"
    r"|(^|[^[:alnum:]_.-])reg(\.exe)?[[:space:]]+(add|import|restore|load)|(^|[^[:alnum:]_.-])sc(\.exe)?[[:space:]]+create"
    r"""|Register-ScheduledTask|New-Service|\.ssh([/[:space:]\"';&|)]|$)|id_(rsa|ed25519|ecdsa|dsa)"""
    r"""|\.aws([/[:space:]\"';&|)]|$)|\.gnupg([/[:space:]\"';&|)]|$)|\.secrets([/[:space:]\"';&|)]|$)|\.netrc"""
    r"|security[[:space:]]+(find-(generic|internet)-password|dump-keychain)|\.[^[:space:]/]*[]*?[][^[:space:]/]*/"
    r"|(^|[[:space:]/=:({,<])\.[^[:space:]/]*[]*?[{}][^[:space:]/]*|\.(config|docker|kube)/[^[:space:];&|]*[]*?[{]"
    r"|dotglob|[Gg][Ll][Oo][Bb]_?[Dd][Oo][Tt][Ss]|\.git-credentials|\.pem|service-account|credentials\.json"
    r"|client_secret|token_cache|\.pypirc|secrets\.env|\.secrets/|\.config/gh/hosts|\.npmrc|\.docker/config"
    r"|\.kube/config|docker[[:space:]]+(volume[[:space:]]+rm|system[[:space:]]+prune)|(^|[^[:alnum:]_.-])sed[[:space:]]"
    r"|\.env([^[:alnum:]_]|$)|rmtree|rm(dir)?Sync|\.rm[[:space:]]*\(|[Rr]emove-[Ii]tem"
    r"|(^|[^[:alnum:]_.-])(powershell|pwsh)(\.exe)?[[:space:]]"
    # 21/11/2026 (#6259, rilievi S4-S9 e S13 della revisione del 20/11): le forme che block-dangerous ora giudica
    # e che il pre-filtro non gli passava. Banco: tests/test_aggiramenti_2026_11_21.py.
    #   S5  `bash -c "$(curl …)"`, un curl o un wget che scrive un file seguito da un altro comando (scarica ed
    #       esegui), base64 -d, xxd -r e openssl enc verso una shell;
    #   S6  find che cerca per nome e legge (-exec, xargs), git credential, la cronologia della shell;
    #   S9  remove_tree e FileUtils di perl e ruby, docker con una cartella montata, diskutil e newfs.
    r"|-[a-zA-Z]*c[[:space:]]+\$\([[:space:]]*(curl|wget|fetch)"
    r"|curl[[:space:]][^;&|]*(-[a-zA-Z]*[oOJ]|--output|--remote-name)[^;&|]*[;&[:cntrl:]]|wget[[:space:]][^;&|]*[;&[:cntrl:]]"
    r"|base64[[:space:]][^|;&]*(-[a-zA-Z]*[dD]|--decode)|xxd[[:space:]][^|;&]*-[a-zA-Z]*r|openssl[[:space:]]+(enc|base64)"
    r"|find[[:space:]].*-i?(name|path|wholename|regex)[[:space:]].*(-(exec|execdir|ok|okdir)[[:space:]]|xargs)"
    r"|git[[:space:]]([^|;&]*[[:space:]])?credential(-[a-z]+)?[[:space:]]|git-credential|_history|\.zhistory"
    r"|remove_tree|FileUtils|rm_rf|(^|[^[:alnum:]_.-])(docker|podman|nerdctl)[[:space:]].*(-v|--volume|--mount)"
    r"|(^|[^[:alnum:]_.-])(diskutil|newfs(_[a-z0-9]+)?)[[:space:]]", lineare=True)

# Commit secret gate: scansiona il diff staged prima di git commit / gh pr create.
# Dal 15/10/2026 parte anche su un commit a capo, in una subshell o in $( ), dopo `env VAR=… `
# o assegnazioni, e con opzioni di git prima di commit (-c k=v, -C dir, --no-pager).
# Dal 15/10/2026 anche dentro virgolette (`bash -c 'git commit'`, `eval "git commit"`) e dopo
# nohup, time, xargs e sudo: commit-secret-gate.py sa già leggerli, il pre-filtro non lo chiamava.
# 11/11/2026 (#5262, review n. 7): anche dopo then, else, do, `{` e `!`, e con un percorso davanti a git.
PATTERN_COMMIT = Pattern(
    "(^|[;&|(`'\"\n])[[:space:]]*((env|command|exec|nohup|time|xargs|sudo|then|else|elif|do|if|while|until|!|\\{)"
    "[[:space:]]+)*([A-Za-z_][A-Za-z0-9_]*=[^[:space:]]*[[:space:]]+)*(([^[:space:];&|]*/)?git([[:space:]]+-[^[:space:]]+"
    "([[:space:]]+[^-[:space:]][^[:space:]]*)?)*[[:space:]]+commit|gh[[:space:]]+pr[[:space:]]+create)", lineare=True)
# Il ciclo delle parole (env, then, do…) e delle assegnazioni ripartiva da ogni a capo fino in fondo al testo:
# 4 secondi su 20.000 caratteri di parole della lista una per riga. Nella forma a mano gli spazi prima di git non
# contengono l'a capo. Il risultato non cambia: l'a capo è anche un inizio valido, e il confronto riparte
# dall'ultimo a capo prima di git con le parole e le assegnazioni che seguono.
_SPAZIO_ERE = _ere("[[:space:]]")
_A_MANO[PATTERN_COMMIT.ere] = _ere(PATTERN_COMMIT.ere).replace(_SPAZIO_ERE, "[ \\t\\r\\f\\v]", 3)
assert _A_MANO[PATTERN_COMMIT.ere].count(_SPAZIO_ERE) == _ere(PATTERN_COMMIT.ere).count(_SPAZIO_ERE) - 3

# exfil: upload di un FILE LOCALE con curl o wget (`-F @file`, `-T`, `--upload-file`, `-d @file`), la forma
# con cui una chiave o un dump escono dalla macchina. Dal 28/10/2026 il POST generico e il codice python
# che chiama la rete non passano più da qui: li giudica il classificatore di auto mode (contratto delle
# guardie: certezze all'hook, dubbi al classificatore). Le email via smtplib restano a comms-guard.
# _FINE_ARG chiude un argomento nella shell (uno spazio) o in una lista python (`'curl', '-d', '@x'`):
# con il solo spazio un invio da subprocess.run([...]) passava senza conferma (21/10/2026, #3645).
# Un & seguito da un carattere che non è spazio né operatore sta dentro l'URL (`?a=1&b=2`) e non chiude
# il comando: prima `curl "https://x/?a=1&b=2" -d @file` passava senza conferma (30/10/2026).
# Il confronto resta esatto anche su macOS e Windows, perché le opzioni contano la maiuscola (`-T` carica
# un file, `-t` no; `-F` è un form, `-f` no). Solo i nomi dei due programmi sono scritti in ogni maiuscola (HK-1b).
_FINE_ARG = """([[:space:]]|["'],[[:space:]]*["']?)"""
PATTERN_EXFIL = Pattern(
    "([cC][uU][rR][lL]|[wW][gG][eE][tT])([^|;&]|&[^[:space:]&|;])*(-[[:alnum:]]*F" + _FINE_ARG + "*[^[:space:]]*[@<]"
    "|--form" + _FINE_ARG + "*[^[:space:]]*[@<]|-[[:alnum:]]*T" + _FINE_ARG + "|-[[:alnum:]]*T[^[:space:]]"
    "|--data-urlencode" + _FINE_ARG + """*["']?[^[:space:]=@"']*@|--upload-file|--(post|body)-file"""
    "|-[[:alnum:]]*d" + _FINE_ARG + """*["']?@|--data[a-z-]*""" + _FINE_ARG + """*["']?@"""
    "|--json" + _FINE_ARG + """*["']?@|--url-query""" + _FINE_ARG + """*["']?@)""", lineare=True)
# La corsa dopo curl o wget è un gruppo (`[^|;&]` o un `&` dentro un URL) e la forma temperata non la vede: si
# ferma a mano sul prossimo curl o wget. Il nome non può finire dentro un'opzione, e la prova regge.
_CORSA_EXFIL = _ere("([^|;&]|&[^[:space:]&|;])*")
assert _CORSA_EXFIL in _ere(PATTERN_EXFIL.ere)
_A_MANO[PATTERN_EXFIL.ere] = _ere(PATTERN_EXFIL.ere).replace(
    _CORSA_EXFIL, "(?:(?![cC][uU][rR][lL]|[wW][gG][eE][tT])" + _CORSA_EXFIL[:-1] + ")*", 1)
# Il GET non passa da exfil-guard (ramo tolto il 30/10/2026, #4325). Vanno a exfil-guard i soli canali di rete
# grezzi: nc/ncat/netcat/socat, anche senza pipe (11/11/2026, #5262, review n. 7), /dev/tcp e /dev/udp.
PATTERN_EGRESS_SOSPETTO = Pattern(r"(^|[^[:alnum:]_.-])(nc|ncat|netcat|socat)([[:space:]]|$)|/dev/(tcp|udp)/")
# Una redirezione verso /dev/tcp scrive in rete anche da un comando che sembra sola lettura (`echo x > /dev/tcp/…`).
PATTERN_DEV_TCP = Pattern(r"[<>]&?[[:space:]]*/dev/(tcp|udp)/")
# git branch -D e git stash drop: dal 31/10/2026 li giudica block-dangerous (tace se il lavoro esiste
# altrove). Dal 7/11/2026 anche git worktree remove (finding 9).
PATTERN_GIT_PERDE = Pattern(
    r"(^|[^[:alnum:]_.-])git[[:space:]]([^|;&]*[[:space:]])?(branch[[:space:]]([^|;&]*[[:space:]])?"
    r"(-[[:alpha:]]*D|--d|-[[:alpha:]]*d)|stash[[:space:]]+(drop|clear)|worktree[[:space:]]+remove)", lineare=True)
# Ogni git push (7/11/2026, finding 5): block-dangerous guarda il flag di forza in qualunque posizione.
PATTERN_GIT_PUSH = Pattern(r"(^|[^[:alnum:]_.-])git[[:space:]]([^|;&]*[[:space:]])?push([[:space:]]|$)", lineare=True)
# Un push con la destinazione riscritta da -c, --config-env o GIT_CONFIG_* (1/11/2026): lo giudica block-dangerous.
PATTERN_GIT_DEST = Pattern(
    r"(^|[^[:alnum:]_.-])git[[:space:]][^|;&]*(-c|--config-env)[^|;&]*[[:space:]]push"
    r"|GIT_CONFIG_(COUNT|KEY_[0-9]+|PARAMETERS)=", lineare=True)
# git commit --amend su un commit che questa sessione non ha fatto (3/11/2026, #4187): lo giudica block-dangerous.
PATTERN_GIT_AMEND = Pattern(r"(^|[^[:alnum:]_.-])git[[:space:]]([^|;&]*[[:space:]])?commit[[:space:]]([^|;&]*[[:space:]])?--am", lineare=True)
# 21/11/2026 (#6259, S4 e S9): git config (core.fsmonitor, core.pager, alias con `!`), reset, checkout, restore
# e credential li giudica block-dangerous. Anche `git -c chiave=valore` e `--config-env`:
# `git -c core.fsmonitor='sh -c …' status` esegue il valore.
PATTERN_GIT_ALTRI = Pattern(
    r"(^|[^[:alnum:]_.-])git[[:space:]]([^|;&]*[[:space:]])?(config|reset|checkout|restore|credential(-[a-z]+)?)"
    r"([[:space:]]|$)|(^|[^[:alnum:]_.-])git[[:space:]]([^|;&]*[[:space:]])?(-c[[:space:]]|--config-env)", lineare=True)
# git clean -f con opzioni in mezzo (`git -C dir clean -fdx`, `git -c k=v clean --force`). Anche l'inizio di
# --force (`--forc`, git lo accetta) e `-c clean.requireForce=false`, che cancella senza -f (20/10/2026, #3525).
PATTERN_GIT_CLEAN = Pattern(
    r"(^|[^[:alnum:]_.-])git[[:space:]]([^|;&]*[[:space:]])?clean[[:space:]]([^|;&]*[[:space:]])?(-[[:alpha:]]*f|--f)"
    r"|(^|[^[:alnum:]_.-])git[[:space:]][^|;&]*[cC]lean\.[rR]equire[fF]orce", lineare=True)
# data-guard: operazioni DATI irreversibili non coperte da block-dangerous
# (SQL DROP/TRUNCATE/DELETE FROM, docker compose down -v, rsync --delete remoto, overwrite .db).
# 13/11/2026 (HK-5): su Windows robocopy con /MIR o /PURGE (in Git Bash anche `//MIR`) e reg delete.
PATTERN_DATA = Pattern(
    r"""[Rr][Oo][Bb][Oo][Cc][Oo][Pp][Yy][^|&;]*[[:space:]]["']?/+([Mm][Ii][Rr]|[Pp][Uu][Rr][Gg][Ee])"""
    r"|(^|[^[:alnum:]_.-])[Rr][Ee][Gg][[:space:]]+[Dd][Ee][Ll][Ee][Tt][Ee]"
    r"|[Dd][Rr][Oo][Pp][[:space:]]+([Tt][Aa][Bb][Ll][Ee]|[Dd][Aa][Tt][Aa][Bb][Aa][Ss][Ee]|[Ss][Cc][Hh][Ee][Mm][Aa])"
    r"|[Tt][Rr][Uu][Nn][Cc][Aa][Tt][Ee]|[Dd][Ee][Ll][Ee][Tt][Ee][[:space:]]+[Ff][Rr][Oo][Mm]"
    r"|docker([[:space:]]+compose|-compose)[^|&;]*[[:space:]]down[^|&;]*(-v|--volumes)"
    r"|rsync[^|&;]*--del(ete)?([^[:alnum:]_]|$)|>[[:space:]]*[^>[:space:]|&;]*\.(db|sqlite|sqlite3|sql|dump)", lineare=True)


def _seconda_corsa(pattern, inizio, corsa, pezzo):
    """La forma lineare dell'alternativa di `pattern` che comincia con `inizio`, con anche l'ultima corsa `corsa`
    fermata sul `pezzo` che la precede. Per `git … commit … --am` il pezzo è ` commit `, spazi compresi.

    Su un comando di 382.000 caratteri con `git commit` a ogni riga, la seconda corsa ripartiva da ogni `commit`
    fino in fondo: 9,7 secondi. Il risultato non cambia: la prima corsa ha la stessa classe e contiene già i
    caratteri del pezzo, quindi il confronto può allungarla fino all'ultimo pezzo prima della fine, e il pezzo
    non può finire dentro ciò che segue."""
    alt = [a for a in _alternative(pattern.ere) if a.startswith(inizio)]
    assert len(alt) == 1, inizio
    lineare = _temperata(alt[0])
    vecchia = _ere(corsa)
    assert vecchia.endswith("*") and lineare.count(vecchia) >= 1, corsa
    k = lineare.rindex(vecchia)
    _A_MANO[alt[0]] = lineare[:k] + "(?:(?!" + _ere(pezzo) + ")" + vecchia[:-1] + ")*" + lineare[k + len(vecchia):]


_GIT_INIZIO = "(^|[^[:alnum:]_.-])git[[:space:]]"
_seconda_corsa(PATTERN_GIT_AMEND, _GIT_INIZIO, "[^|;&]*", "[[:space:]]commit[[:space:]]")
_seconda_corsa(PATTERN_GIT_CLEAN, _GIT_INIZIO + "(", "[^|;&]*", "[[:space:]]clean[[:space:]]")
_seconda_corsa(PATTERN_GIT_PERDE, _GIT_INIZIO, "[^|;&]*", "[[:space:]]branch[[:space:]]")
_seconda_corsa(PATTERN_GIT_DEST, _GIT_INIZIO + "[^|;&]*", "[^|;&]*", "(-c|--config-env)")
_seconda_corsa(PATTERN_DATA, "docker", "[^|&;]*", "[[:space:]]down")

# 22/11/2026 (#6323): un programma nascosto alle guardie (nome calcolato, alias, funzione, xargs, testo verso una
# shell, codice di un interprete) con una parola pericolosa nel comando. Lo giudica block-dangerous (regola
# codice-nascosto, _programma_nascosto); i percorsi dei segreti li porta già PATTERN_DANGER.
PATTERN_NASCOSTO = Pattern(
    r"\$[({A-Za-z_]|`|(^|[^[:alnum:]_.-])(g?xargs|alias|python[0-9.]*|perl|ruby|node|nodejs|php|deno|bun|osascript"
    r"|sh|bash|zsh|dash|ksh|fish|pwsh|powershell)(\.exe)?([^[:alnum:]_.-]|$)|[[:alnum:]_][[:space:]]*\([[:space:]]*\)")
PATTERN_PAROLA_PERICOLOSA = Pattern(r"(^|[^[:alnum:]_.$-])(rm|unlink|shred|push|reset|clean|curl|wget|bw|gh)([^[:alnum:]_-]|$)")

# Lo skip git-puro: bash ESEGUE `$(...)`, i backtick e le process substitution <()/>() ANCHE dentro le doppie
# virgolette. Con una sostituzione il comando non è git puro.
PATTERN_SUBST = Pattern(r"\$\(|`|<\(|>\(")
# `--no-index` fa leggere a git diff e git grep un file qualunque del disco, anche una chiave: non è testo
# inerte, e il comando passa da block-dangerous (11/11/2026, #5262). Le opzioni restano esatte: `-c`
# (configurazione) e `-C` (cartella) sono opzioni diverse. I sottocomandi che inviano sono programmi a parte
# nella cartella di git, e il disco li trova anche scritti `Send-Email` (HK-1b).
PATTERN_GIT_OPZIONI = Pattern(r"(^|[[:space:]])(--output|--exec-path|--config-env|--no-index|-c[[:space:]])|(^|[^>])>>?[^&|;]")
PATTERN_GIT_INVIA = Pattern(r"send-email|imap-send")

# La sessione dentro ~/.claude, dentro `.git` o dentro una cartella dei segreti: una scrittura relativa non
# nomina il percorso protetto, e block-dangerous lo risolve dalla cartella della sessione (4/11/2026, #4566;
# 11/11/2026, #5262; review del 10/11/2026, problema 10, #5263). Si cercano nel JSON dell'evento.
RE_CWD_CLAUDE = Pattern(r'"cwd"[[:space:]]*:[[:space:]]*"[^"]*[/\\]\.claude')
RE_CWD_GIT = Pattern(r'"cwd"[[:space:]]*:[[:space:]]*"[^"]*[/\\]\.git(["/\\])')
RE_CWD_SEGRETI = Pattern(r'"cwd"[[:space:]]*:[[:space:]]*"[^"]*[/\\]\.(ssh|aws|gnupg|secrets)(["/\\])')
# Le parole necessarie (Pattern.serve). PATTERN_COMMS, PATTERN_DANGER, PATTERN_SCRIVE e PATTERN_NASCOSTO non le
# hanno: le loro alternative sono troppe, o troppo corte per scartare qualcosa.
for _p, _parole in (
        (PATTERN_TIMEOUT, ("timeout",)), (PATTERN_REMOTE, ("ssh", "exec", "<<")), (PATTERN_GH_ANY, ("gh",)),
        (PATTERN_API_GITHUB, ("api.github.com",)), (PATTERN_GIT_TEXT, ("git",)), (PATTERN_COMMIT, ("git", "gh")),
        (PATTERN_EXFIL, ("curl", "wget")), (PATTERN_EGRESS_SOSPETTO, ("nc", "cat", "/dev/")),
        (PATTERN_DEV_TCP, ("/dev/",)), (PATTERN_GIT_PERDE, ("git",)), (PATTERN_GIT_PUSH, ("git",)),
        (PATTERN_GIT_DEST, ("git",)), (PATTERN_GIT_AMEND, ("git",)), (PATTERN_GIT_ALTRI, ("git",)),
        (PATTERN_GIT_CLEAN, ("git",)), (PATTERN_SUBST, ("$(", "`", "<(", ">(")),
        (PATTERN_GIT_OPZIONI, ("--", "-c", ">")), (PATTERN_GIT_INVIA, ("send-email", "imap-send")),
        (RE_CWD_CLAUDE, ('"cwd"',)), (RE_CWD_GIT, ('"cwd"',)), (RE_CWD_SEGRETI, ('"cwd"',)),
        (PATTERN_DATA, ("robocopy", "reg", "drop", "truncate", "delete", "docker", "rsync", ">")),
        (PATTERN_PAROLA_PERICOLOSA, ("rm", "unlink", "shred", "push", "reset", "clean", "curl", "wget", "bw", "gh"))):
    _p.serve = _parole

_RE_CWD_VALORE = re.compile(r'"cwd"[ \t\n\r\f\v]*:[ \t\n\r\f\v]*"([^"]*)"')

# I sottocomandi di git che il pre-filtro conosce (lo stesso elenco di _GIT_NOTI in commit-secret-gate.py). Un
# nome fuori da qui può essere un alias di commit (`git -c alias.ci=commit ci`, `git salva`): lo risolve il gate
# (21/11/2026, #6259, S10).
GIT_NOTI = frozenset(
    "add am annotate apply archive bisect blame branch bundle cat-file check-attr check-ignore checkout cherry "
    "cherry-pick clean clone commit commit-graph commit-tree config count-objects credential describe diff "
    "diff-files diff-index diff-tree difftool fetch filter-branch for-each-ref format-patch fsck gc grep gui "
    "hash-object help init log ls-files ls-remote ls-tree lfs maintenance merge merge-base merge-file mergetool "
    "mktree mv name-rev notes pack-refs prune pull push range-diff read-tree rebase reflog remote repack replace "
    "rerere reset restore rev-list rev-parse revert rm send-email shortlog show show-branch show-ref "
    "sparse-checkout stage stash status submodule switch symbolic-ref tag update-index update-ref verify-commit "
    "verify-tag version whatchanged worktree write-tree".split())
_RE_GIT_SOTTO = re.compile(_ere(
    r"(^|[^[:alnum:]_.-])git[[:space:]]+((-[Cc]|--git-dir|--work-tree|--namespace|--exec-path|--config-env)"
    r"[[:space:]]+[^[:space:]]+[[:space:]]+|-[^[:space:]]+[[:space:]]+)*([A-Za-z][A-Za-z0-9_-]*)(.*)$"), re.S | re.A)

# Le parole di link_in_vista: i separatori di `IFS=$' \t\n;&|()<>' read -a` del dispatcher di prima.
_RE_IFS = re.compile(r"[ \t\n]*[;&|()<>][ \t\n]*|[ \t\n]+")


def _modulo(nome, file):
    spec = importlib.util.spec_from_file_location(nome, os.path.join(_QUI, file))
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


def _maschera(c):
    """Il comando con le parti fra virgolette e i caratteri dopo una barra rovesciata coperti da Q: un
    `git commit -m "fix; timeout 30"` non è un timeout, e un `--include=*.md` fra virgolette non è un glob."""
    out, q, i = [], None, 0
    while i < len(c):
        ch = c[i]
        if ch == "\\" and q != "'":
            out.append("QQ")
            i += 2
            continue
        if q is None and ch in "'\"":
            q = ch
            out.append("Q")
        elif q is not None:
            out.append("Q")
            q = None if ch == q else q
        else:
            out.append(ch)
        i += 1
    return "".join(out)


def _sciolto(testo):
    """Il comando senza virgolette e senza barre rovesciate: per bash `\\x27rm\\x27 -rf`, `"rm" -rf`, `r\\m -rf`,
    `git pu\\sh` e `~/.cl\\x27\\x27aude` sono `rm -rf`, `git push` e `~/.claude`, e le guardie li leggono già così
    (review del 10/11/2026, n. 7). Serve solo a decidere se una guardia parte."""
    return testo.replace("\\\n", "").replace("'", "").replace('"', "").replace("\\", "")


def _glob_opzione(comando, grezzo, dati):
    """`--include=*.md` senza virgolette, in zsh: un glob che non trova niente e fa morire il comando con "no
    matches found" prima di partire. Le parti fra virgolette, i backslash e gli heredoc non contano: lì zsh non
    espande. Con la riga di session-start.sh in $CLAUDE_ENV_FILE (marcatore arturo-zsh-come-bash) zsh ha
    nonomatch e un glob senza file resta la parola scritta: il comando parte e il blocco non serve. Claude Code
    esegue quel file solo prima dei comandi del tool Bash, non di Monitor (3/11/2026)."""
    if "<<" in comando:
        return ""
    m = re.search(r"(?:^|[\s;&|(])(--[A-Za-z][\w-]*=[^\s;&|()<>]*\*[^\s;&|()<>]*)", _maschera(comando))
    if not m:
        return ""
    try:
        import glob
        sid = str(dati.get("session_id") or "")
        conf = os.environ.get("CLAUDE_CONFIG_DIR") or os.path.join(os.path.expanduser("~"), ".claude")
        if dati.get("tool_name") == "Bash" and sid and "/" not in sid and ".." not in sid:
            for f in glob.glob(os.path.join(conf, "session-env", sid, "sessionstart-hook-*.sh")):
                with open(f, encoding="utf-8", errors="replace") as fh:
                    if "arturo-zsh-come-bash" in fh.read():
                        return ""
    except Exception:
        pass
    return m.group(1)


def _git_sottocomando_ignoto(sciolto):
    resto, giri = sciolto, 0
    while giri < 20:
        m = _RE_GIT_SOTTO.search(resto)
        if not m:
            return False
        if m.group(4) not in GIT_NOTI:
            return True
        resto = m.group(5)
        giri += 1
    return False


def _sotto_radice(p):
    """Vero se `p` è un percorso assoluto con almeno una cartella sotto la radice: `/a/b`, `C:/a/b`. È il
    `[[ "$p" == /*/* ]]` del dispatcher di prima."""
    if len(p) > 2 and p[1] == ":" and p[0].isalpha():
        p = p[2:]
    return p.startswith("/") and "/" in p[1:]


def _link_in_vista(sciolto, grezzo, somiglia, windows):
    """Un link già sul disco verso una chiave o verso la config (`cat k`, `cat lnk/github` con lnk verso ~/.ssh)
    non nomina il segreto: block-dangerous risolve il percorso (21/11/2026, #6200). Ogni parola che sembra un
    percorso si controlla pezzo per pezzo, senza seguire i link; solo se un pezzo è un link, il percorso vero si
    confronta con PATTERN_DANGER. La cartella di primo livello non conta: su macOS /tmp, /var ed /etc sono link
    verso /private. Oltre 300 parole o 8 link, o se il percorso vero non si legge, parte la guardia.
    Banco: GC12 in tests/test_guardie_cieche_2026_11_11.py."""
    m = _RE_CWD_VALORE.search(grezzo)
    cwd = m.group(1) if m else ""
    if windows:
        cwd = cwd.replace("\\\\", "/")
    casa = os.environ.get("HOME") or os.path.expanduser("~")
    # Le stesse parole non vuote di bash, e mai meno parole in tutto: il tetto delle 300 scatta presto o uguale.
    parole = _RE_IFS.split(sciolto.strip(" \t\n"))
    letti = 0
    for n, parola in enumerate(parole, 1):
        if n > 300:
            return True
        if "=" in parola:
            parola = parola.split("=", 1)[1]
        if not parola or parola.startswith("-") or any(c in parola for c in "$*?[{`"):
            continue
        if parola.startswith("~/"):
            p = casa + "/" + parola[2:]
        elif parola.startswith("/"):
            p = parola
        elif cwd:
            p = cwd + "/" + parola
        else:
            continue
        if windows:
            # python3 su Windows è nativo: `/c/Users/x` di Git Bash diventa `C:/Users/x`, e la lettera del disco
            # non conta come cartella. Il caso non ha un banco su Windows (PB07 lo salta).
            p = p.replace("\\", "/")
            if re.match(r"/[A-Za-z](/|\Z)", p):
                p = p[1].upper() + ":" + p[2:]
        vero = p
        while _sotto_radice(p):
            if os.path.islink(p):
                letti += 1
                if letti > 8:
                    return True
                try:
                    vero = os.path.realpath(vero)
                    # Come `readlink -f` su macOS, che esce 1 se il percorso vero non esiste tutto (22/11/2026: una
                    # libreria di /System/Library/Frameworks, che sta solo nella cache di sistema). Su Linux
                    # readlink accetta l'ultimo pezzo mancante: qui la guardia parte anche lì, il lato sicuro.
                    if not os.path.exists(vero):
                        return True
                except (OSError, ValueError):
                    return True
                if not vero:
                    return True
                if somiglia(vero.replace("\\", "/") if windows else vero, PATTERN_DANGER):
                    return True
                break
            p = p.rsplit("/", 1)[0]
    return False


def analizza(comando, guardie, grezzo, dati, senza_maiuscole=False, windows=False, zsh=False):
    """Le viste del pre-filtro, nell'ordine in cui il dispatcher le usa, e il comando ridotto di
    comms-prefilter (None se nessun ramo lo chiede). `comando` è COMMAND, `guardie` è GUARD_COMMAND,
    `grezzo` è il JSON dell'evento com'è arrivato, `dati` lo stesso JSON letto."""
    viste = []

    def somiglia(testo, pattern):
        return pattern.senza_maiuscole(testo) if senza_maiuscole else pattern.trova(testo)

    sciolto = _sciolto(guardie)

    def vede(pattern):
        return somiglia(guardie, pattern) or (sciolto != guardie and somiglia(sciolto, pattern))

    # Il `*--*=*\**` del dispatcher: un `--`, poi un `=`, poi un `*`. Le prime occorrenze bastano.
    i = comando.find("--")
    j = comando.find("=", i + 2) if i >= 0 else -1
    if zsh and j >= 0 and comando.find("*", j + 1) >= 0:
        glob_opz = _glob_opzione(comando, grezzo, dati)
        if glob_opz:
            viste.append("glob-zsh=" + glob_opz)
    if (PATTERN_TIMEOUT.trova(comando) and not PATTERN_REMOTE.trova(comando)
            and PATTERN_TIMEOUT.trova(_maschera(comando) or comando)):
        viste.append("timeout")
    if somiglia(comando, PATTERN_COMMIT) or vede(PATTERN_COMMIT) or _git_sottocomando_ignoto(sciolto):
        viste.append("commit")
    if vede(PATTERN_GIT_PUSH):
        viste.append("push")
    if (vede(PATTERN_GIT_CLEAN) or vede(PATTERN_GIT_PERDE) or vede(PATTERN_GIT_PUSH) or vede(PATTERN_GIT_DEST)
            or vede(PATTERN_GIT_AMEND) or vede(PATTERN_GIT_ALTRI)
            or (vede(PATTERN_PAROLA_PERICOLOSA) and vede(PATTERN_NASCOSTO))):
        viste.append("danger-git")

    git_testo = somiglia(comando, PATTERN_GIT_TEXT)
    git_rischio = PATTERN_GIT_OPZIONI.trova(comando) or somiglia(comando, PATTERN_GIT_INVIA)
    if (git_testo and not PATTERN_SUBST.trova(comando) and "--output" not in comando
            and "--exec-path" not in comando and "--config-env" not in comando and not git_rischio):
        # Le virgolette si leggono come le legge bash (forma_comando.py): ogni programma eseguito deve essere git
        # o cd, anche col path completo o in un blocco. Virgolette che non tornano: non è git puro.
        try:
            if _modulo("arturo_forma_comando", "forma_comando.py").git_puro(comando):
                viste.append("git-puro")
        except Exception:
            pass
    if git_testo and git_rischio:
        viste.append("git-opzioni")

    # Comms guard, exfil-guard e i canali grezzi si giudicano sul CODICE eseguito: comms-prefilter.py toglie gli
    # heredoc scritti su file e tace sui comandi di sola lettura (`grep -ril smtplib .`), che nominano un invio
    # senza farlo. Se il pre-filtro non gira, si giudica il comando intero.
    ridotto = [None]

    def riduci():
        if ridotto[0] is None:
            try:
                ridotto[0] = _modulo("arturo_comms_prefilter", "comms-prefilter.py").reduce(guardie).rstrip("\n")
            except Exception:
                ridotto[0] = guardie
        return ridotto[0]

    def invio_in_vista(testo):
        return somiglia(testo, PATTERN_COMMS) or ("gws " in testo and "messages send" in testo)

    if invio_in_vista(guardie) and invio_in_vista(riduci()):
        viste.append("comms")

    # Su Windows i percorsi hanno anche le barre rovesciate (`"C:\Users\x\.claude\settings.json"`), e
    # PATTERN_DANGER cerca `.claude/` e le altre voci con la barra dritta (review del 9/11/2026, #5096 e #5121).
    dritto = guardie.replace("\\", "/") if windows else guardie
    if (vede(PATTERN_DANGER) or somiglia(sciolto.replace("/dev/null", ""), PATTERN_SCRIVE)
            or (dritto != guardie and somiglia(dritto, PATTERN_DANGER))
            or somiglia(grezzo, RE_CWD_CLAUDE) or somiglia(grezzo, RE_CWD_GIT) or somiglia(grezzo, RE_CWD_SEGRETI)
            or _link_in_vista(sciolto, grezzo, somiglia, windows)):
        viste.append("danger")
    # 21/11/2026 (#6202): anche senza virgolette e barre, come la guardia, che legge `cu''rl` e `"curl"` come curl.
    if PATTERN_EXFIL.trova(guardie) or PATTERN_EXFIL.trova(sciolto):
        r = riduci()
        if PATTERN_EXFIL.trova(r) or PATTERN_EXFIL.trova(_sciolto(r)):
            viste.append("exfil")
    # Una redirezione verso /dev/tcp si giudica sul comando intero: il pre-filtro tace su `echo`, che lì scrive
    # in rete.
    if vede(PATTERN_EGRESS_SOSPETTO):
        r = riduci()
        if somiglia(r, PATTERN_EGRESS_SOSPETTO) or (r == guardie and somiglia(sciolto, PATTERN_EGRESS_SOSPETTO)):
            viste.append("egress")
        elif PATTERN_DEV_TCP.trova(guardie):
            viste.append("egress-tcp")
    # 21/11/2026 (#6202): anche senza virgolette e barre: `rs"y"nc --delete` e `'DR''OP TABLE t'`.
    if vede(PATTERN_DATA):
        viste.append("data")
    # 21/11/2026 (#6259, S7): anche curl, wget e httpie verso api.github.com, che fanno le stesse chiamate di
    # `gh api`.
    if somiglia(comando, PATTERN_GH_ANY) or vede(PATTERN_GH_ANY) or vede(PATTERN_API_GITHUB):
        viste.append("gh")
    if ".claude" in comando or RE_CWD_CLAUDE.trova(grezzo):
        viste.append("claude")
    if ".claude/" in comando:
        viste.append("memoria")
    if ridotto[0] is not None:
        viste.append("ridotto")
    return viste, ridotto[0]


if __name__ == "__main__":
    import sys
    if sys.argv[1:] == ["genera"]:
        with open(os.path.join(_QUI, "prefiltro_regex.py"), "w", encoding="utf-8") as f:
            f.write(genera())
        sys.exit(0)
    sys.stderr.write("uso: prefiltro_bash.py genera\n")
    sys.exit(64)
