#!/bin/bash
# Dispatcher per PreToolUse Bash hooks.
# Instrada verso gli guard solo quando il comando e' rilevante (un solo processo
# per la stragrande maggioranza dei comandi). Ogni guard puo':
#   - uscire con rc 2    -> blocco duro (stderr -> modello)
#   - uscire con altro rc -> guardia rotta: chiede conferma (ask_guard, fail-closed)
#   - stampare JSON permissionDecision su stdout + rc 0 -> ask/allow esplicito
#   - stampare nulla + rc 0 -> silenzioso (prosegue col guard successivo)
# run_guard cattura la decisione e cortocircuita: al massimo UNA decisione emessa.

# Il JSON di Claude Code è UTF-8. Su Windows ogni python3 qui sotto leggeva e scriveva in cp1252:
# un «”» nel comando svuotava l'input delle guardie e un rm ricorsivo passava (16/10/2026).
export PYTHONIOENCODING=utf-8

# Dove sta il codice (docs/strati.md): ARTURO_HOOKS è la cartella di questo file, ~/.claude/hooks
# nel clone, la cartella del plugin domani. ORSA_HOOKS tiene le guardie della persona, ~/.claude/arturo il .local.
# Si calcola solo dal file, mai da una variabile d'ambiente: una guardia non si sposta da fuori.
ARTURO_HOOKS="$(cd "$(dirname "${BASH_SOURCE[0]}")" 2>/dev/null && pwd)"
ARTURO_BIN="$(dirname "$ARTURO_HOOKS")/bin"
ORSA_HOOKS="$HOME/.claude/hooks"
# Il file di una guardia: prima Arturo, poi l'Orsa.
guardia_file() { if [[ -f "$ARTURO_HOOKS/$1" ]]; then printf '%s' "$ARTURO_HOOKS/$1"; else printf '%s' "$ORSA_HOOKS/$1"; fi; }

INPUT=$(cat)
if command -v jq &>/dev/null; then
  COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command // empty')
else
  # Fallback SENZA jq: parser JSON robusto via python3 (gia' richiesto dagli altri
  # guard). Il vecchio fallback grep si fermava al primo apice doppio dentro il
  # valore, troncando i comandi con virgolette e indebolendo TUTTI i guard a valle.
  COMMAND=$(printf '%s' "$INPUT" | python3 -c 'import sys,json
try: print(json.load(sys.stdin).get("tool_input",{}).get("command",""))
except Exception: pass')
fi
# Windows (30/10/2026 nella config, 31/10/2026 qui): jq e python scrivono ogni a capo come CRLF, e
# le guardie vedevano un comando diverso da quello che esegue bash. Si toglie solo il CR davanti a
# un LF, e solo su Windows: su Mac e Linux il comando resta intatto.
[[ "$OSTYPE" == msys* || "$OSTYPE" == cygwin* ]] && COMMAND="${COMMAND//$'\r\n'/$'\n'}"

# Senza un lettore del JSON nessuna guardia vede il comando: con un python3 che non parte (su Windows il
# rimando del Microsoft Store esce 49) e senza un jq che funziona, COMMAND restava vuoto e ogni comando
# passava in silenzio (revisione del 10/11/2026, HK-2). Se l'input porta un "command" non vuoto e qui non
# è arrivato niente, si chiede conferma. Senza ask_guard: la telemetria è python3, che qui non parte.
_RE_HA_COMANDO='"command"[[:space:]]*:[[:space:]]*"[^"]'
if [[ -z "$COMMAND" && "$INPUT" =~ $_RE_HA_COMANDO ]]; then
    printf '%s\n' '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"ask","permissionDecisionReason":"Le guardie non leggono il comando: manca un python3 che funziona (e jq). Conferma solo se sai cosa fa. Per sistemare: /diagnosi."}}'
    exit 0
fi

# Riduce solo heredoc quotati che vanno a un lettore (cat, tee, grep...) e che nessuno esegue:
# il corpo e' dato, non shell. Lo decide hooks/heredoc.py, lo stesso modulo delle guardie
# (15/10/2026): `cat <<'EOF' | bash`, un file scritto e poi eseguito, `<<` dentro virgolette o
# confini incerti restano interi e passano dalle guardie. Un errore tiene il comando originale.
reduce_inert_heredocs() {
    python3 -c 'import importlib.util, sys
spec = importlib.util.spec_from_file_location("arturo_heredoc", sys.argv[1])
hd = importlib.util.module_from_spec(spec)
spec.loader.exec_module(hd)
source = sys.stdin.read().replace("\r\n", "\n")
print(hd.togli(source, lambda h: h.quotato and h.inerte()), end="")' "$ARTURO_HOOKS/heredoc.py" <<< "$1" 2>/dev/null \
        || printf '%s' "$1"
}

GUARD_COMMAND=$(reduce_inert_heredocs "$COMMAND")
# Anche la riduzione passa da un print di python: su Windows rimetteva i CRLF (MO01, 31/10/2026).
[[ "$OSTYPE" == msys* || "$OSTYPE" == cygwin* ]] && GUARD_COMMAND="${GUARD_COMMAND//$'\r\n'/$'\n'}"
# Su Windows `rm.exe`, `git.exe` e `gh.exe` sono gli stessi programmi di `rm`, `git` e `gh`: il suffisso
# si toglie dalla fine di ogni parola prima di ogni confronto, o pre-filtro e guardie tacciono (revisione
# del 10/11/2026, HK-1). Cambia solo il testo che leggono le guardie, non il comando eseguito.
_RE_EXE='^(.*[^[:space:]/\])\.[Ee][Xx][Ee]([[:space:];&|()<>"'"'"'`].*)?$'
while [[ "$GUARD_COMMAND" =~ $_RE_EXE ]]; do GUARD_COMMAND="${BASH_REMATCH[1]}${BASH_REMATCH[2]}"; done
# Su Windows la shell converte gli argomenti che sembrano path prima di passarli a un programma
# nativo: `/bin/rm -rf ~/Documents` arrivava alle guardie come `C:/Program Files/.../rm` e nessuna
# lo riconosceva. Dove l'argomento è il testo del comando la conversione si spegne. Fuori da
# Windows MSYS2_ARG_CONV_EXCL non conta.
# Oltre 100.000 caratteri le guardie non finiscono in tempo: block-dangerous impiega 20 secondi su 300.000 e
# minuti su un milione, e il comando partiva senza un giudizio o cadeva sul tempo massimo dell'hook. Un
# comando così lungo dopo la riduzione degli heredoc non è un uso normale: si chiede conferma (#5262, n. 9).
if [[ ${#GUARD_COMMAND} -gt 100000 ]]; then
    printf '%s\n' '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"ask","permissionDecisionReason":"Comando troppo lungo per le guardie (oltre 100.000 caratteri): non lo hanno letto. Conferma solo se sai cosa fa, oppure metti il contenuto in un file."}}'
    exit 0
fi
# Il comando arriva a python su stdin, dopo il JSON dell'evento e un a capo: come argomento, un comando oltre
# il limite del sistema (circa 1 MB su macOS, 128 KB per argomento su Linux) non faceva partire python,
# GUARD_INPUT restava vuoto e ogni guardia leggeva "niente da dire" (review del 10/11/2026, n. 9). Un byte
# che non è UTF-8 si sostituisce: prima faceva cadere la lettura e dava lo stesso silenzio.
GUARD_INPUT=$(printf '%s\n%s' "$INPUT" "$GUARD_COMMAND" | python3 -c 'import json, sys
grezzo = sys.stdin.buffer.read().decode("utf-8", "replace").lstrip()
try:
    data, fine = json.JSONDecoder().raw_decode(grezzo)
    if not isinstance(data, dict) or grezzo[fine:fine + 1] != "\n":
        raise ValueError
    data.setdefault("tool_input", {})["command"] = grezzo[fine + 1:]
    print(json.dumps(data))
except Exception:
    pass' 2>/dev/null)
# Senza la copia dell'evento nessuna guardia vede il comando: si chiede conferma, come sopra per COMMAND.
if [[ -n "$COMMAND" && "$GUARD_INPUT" != *'"command"'* ]]; then
    printf '%s\n' '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"ask","permissionDecisionReason":"Le guardie non riescono a leggere questo comando (troppo lungo o con caratteri non validi). Conferma solo se sai cosa fa."}}'
    exit 0
fi
unset COMMS_REDUCED
# Il pre-filtro confronta anche il comando senza virgolette e senza barre rovesciate: per bash `\x27rm\x27 -rf`,
# `"rm" -rf`, `r\m -rf`, `git pu\sh` e `~/.cl\x27\x27aude` sono `rm -rf`, `git push` e `~/.claude`, e le guardie
# li leggono già così. Il pre-filtro no, e non le chiamava (review del 10/11/2026, n. 7). Serve solo a
# decidere se una guardia parte: la guardia riceve sempre il comando com'è scritto.
_APICE="'"
_SCIOLTO="${GUARD_COMMAND//\\$'\n'/}"
_SCIOLTO="${_SCIOLTO//$_APICE/}"
_SCIOLTO="${_SCIOLTO//\"/}"
_SCIOLTO="${_SCIOLTO//\\/}"

# --- Glob dentro un'opzione, in zsh ---
# `--include=*.md` senza virgolette in zsh e' un glob che non trova niente: il comando
# muore con "no matches found" prima di partire. Le parti fra virgolette, i backslash e
# gli heredoc si mascherano prima del match: li' zsh non espande.
if [[ "${SHELL##*/}" == zsh && "$COMMAND" == *--*=*\** ]]; then
    _OPTGLOB=$(MSYS2_ARG_CONV_EXCL='*' python3 -c 'import re,sys
c=sys.argv[1]
if "<<" in c: sys.exit()
out=[]; q=None; i=0
while i<len(c):
    ch=c[i]
    if ch=="\\" and q!="'"'"'": out.append("QQ"); i+=2; continue
    if q is None and ch in "'"'"'\"": q=ch; out.append("Q")
    elif q is not None: out.append("Q"); q=None if ch==q else q
    else: out.append(ch)
    i+=1
m=re.search(r"(?:^|[\s;&|(])(--[A-Za-z][\w-]*=[^\s;&|()<>]*\*[^\s;&|()<>]*)", "".join(out))
if m: print(m.group(1))' "$COMMAND" 2>/dev/null)
    # Con la riga di session-start.sh in $CLAUDE_ENV_FILE (marcatore arturo-zsh-come-bash) zsh ha
    # nonomatch e un glob senza file resta la parola scritta: il comando parte e il blocco non serve.
    # Claude Code esegue quel file solo prima dei comandi del tool Bash, non di Monitor (3/11/2026).
    if [[ -n "$_OPTGLOB" ]] && printf '%s' "$INPUT" | python3 -c 'import glob, json, os, sys
d = json.load(sys.stdin)
sid = str(d.get("session_id") or "")
conf = os.environ.get("CLAUDE_CONFIG_DIR") or os.path.join(os.path.expanduser("~"), ".claude")
if d.get("tool_name") != "Bash" or not sid or "/" in sid or ".." in sid: sys.exit(1)
for f in glob.glob(os.path.join(conf, "session-env", sid, "sessionstart-hook-*.sh")):
    if "arturo-zsh-come-bash" in open(f, encoding="utf-8", errors="replace").read(): sys.exit(0)
sys.exit(1)' 2>/dev/null; then
        _OPTGLOB=""
    fi
    if [[ -n "$_OPTGLOB" ]]; then
        _OPT="${_OPTGLOB%%=*}"; _VAL="${_OPTGLOB#*=}"
        echo "BLOCCATO: in zsh '$_OPTGLOB' senza virgolette e' un glob che fallisce con 'no matches found'. Scrivi $_OPT='$_VAL'." >&2
        exit 2
    fi
fi

# --- timeout su macOS ---
# Sui Mac `timeout` non esiste: `command not found` va su stderr, la pipeline riceve
# stdout vuoto e la diagnosi finisce sul servizio sbagliato. Esclusi ssh, docker exec
# e heredoc: li' `timeout` gira su una macchina Linux.
_NL=$'\n'
PATTERN_TIMEOUT="(^|[;&|(\`${_NL}])[[:space:]]*((sudo|env|command|exec)[[:space:]]+)?timeout[[:space:]]+(-[^[:space:]]+[[:space:]]+([A-Z]+[[:space:]]+)?)*[0-9]"
PATTERN_REMOTE='(^|[[:space:];&|(])(ssh|docker[[:space:]]+exec|kubectl[[:space:]]+exec)[[:space:]]|<<'
# Il match si ripete sul comando con le parti fra virgolette mascherate: un
# `git commit -m "fix; timeout 30"` non e' un timeout. Se python fallisce resta il comando intero.
if [[ "$COMMAND" =~ $PATTERN_TIMEOUT && ! "$COMMAND" =~ $PATTERN_REMOTE ]] && ! command -v timeout &>/dev/null; then
    _SENZAQ=$(MSYS2_ARG_CONV_EXCL='*' python3 -c 'import sys
c=sys.argv[1]; out=[]; q=None; i=0
while i<len(c):
    ch=c[i]
    if ch=="\\" and q!="'"'"'": out.append("QQ"); i+=2; continue
    if q is None and ch in "'"'"'\"": q=ch; out.append("Q")
    elif q is not None: out.append("Q"); q=None if ch==q else q
    else: out.append(ch)
    i+=1
print("".join(out))' "$COMMAND" 2>/dev/null) || _SENZAQ="$COMMAND"
    [[ -n "$_SENZAQ" ]] || _SENZAQ="$COMMAND"
fi
if [[ "$COMMAND" =~ $PATTERN_TIMEOUT && "${_SENZAQ:-$COMMAND}" =~ $PATTERN_TIMEOUT && ! "$COMMAND" =~ $PATTERN_REMOTE ]] && ! command -v timeout &>/dev/null; then
    echo "BLOCCATO: 'timeout' non esiste su questo sistema. Fallirebbe con 'command not found' e stdout vuoto. Usa il parametro timeout del tool Bash, 'curl --max-time N', oppure 'cmd & pid=\$!; sleep N; kill \$pid'." >&2
    exit 2
fi

# Su macOS e Windows il disco ignora le maiuscole: `RM -rf`, `Git push --force` e `GH repo delete`
# fanno partire `rm`, `git` e `gh`. I pattern del pre-filtro si confrontano col comando attraverso
# `somiglia`, che lì ignora le maiuscole (revisione del 10/11/2026, HK-1b). Su Linux `RM` è un altro file e
# il confronto resta esatto. nocasematch si accende solo dentro `somiglia`: tutti gli altri confronti di
# questo file (i punti del .local, il nome della regola, "tace", le opzioni di git) restano esatti.
_SENZA_MAIUSCOLE=0
[[ "$OSTYPE" == darwin* || "$OSTYPE" == msys* || "$OSTYPE" == cygwin* ]] && _SENZA_MAIUSCOLE=1
# $1 = il testo del comando, $2 = un pattern del pre-filtro.
somiglia() {
    local rc
    [[ $_SENZA_MAIUSCOLE -eq 1 ]] && shopt -s nocasematch
    [[ "$1" =~ $2 ]]
    rc=$?
    shopt -u nocasematch
    return $rc
}

# Una scrittura su file: una redirezione verso un file che non è /dev/null, o un programma che scrive il file
# che riceve. Il percorso protetto può non comparire nel testo: un link (`echo x > lnk/settings.json`), un glob
# (`~/.claud[e]/…`), una cartella raggiunta con un cd che il pre-filtro non segue. block-dangerous risolve il
# percorso vero, quindi parte su ogni scrittura (11/11/2026, #5262, review n. 4 e 7). Costa un processo in più
# sui comandi che scrivono; le letture restano fuori.
_SENZA_NULL="${_SCIOLTO//\/dev\/null/}"
PATTERN_SCRIVE='(^|[^-0-9&>])[0-9]?>[>|]?[[:space:]]*[^&>([:space:]]|&>|(^|[^[:alnum:]_.-])(cp|mv|tee|dd|install|ln|rsync|touch|truncate|sponge|tar|gtar|bsdtar|unzip|patch|ditto|chmod|chown)([[:space:]]|$)'

# Vero se il pattern $1 si trova nel comando delle guardie o nella sua forma senza virgolette.
vede() { somiglia "$GUARD_COMMAND" "$1" || somiglia "$_SCIOLTO" "$1"; }

# --- Pattern pre-filtro (in variabili: evita problemi in [[ =~ ]]) ---
# gh ancorato a inizio comando/segmento, MA tollerando i prefissi che non cambiano
# il comando eseguito: assegnazioni env (FOO=bar), `env`, `command`, `\gh`. Senza
# questo, `FOO=1 gh repo delete` o `command gh ...` eludono i guard gh.
_GH_PREFIX='(env[[:space:]]+)?([A-Za-z_][A-Za-z0-9_]*=[^[:space:]]*[[:space:]]+)*(command[[:space:]]+)?\\?'
# 9/10/2026: la parola gh in qualunque posizione (dopo un a capo, in una subshell,
# col path completo). gh-destructive-guard legge gia' tutto il comando.
PATTERN_GH_ANY='(^|[^[:alnum:]_.-])gh[[:space:]]'
PATTERN_GIT_TEXT='(^|[;&|][[:space:]]*)git[[:space:]]+(-C[[:space:]]+[^[:space:]]+[[:space:]]+)?(commit|log|show|tag|stash[[:space:]]+(push|save))'
PATTERN_COMMS='(^|[[:space:];|&("'"'"'`])(sendmail|mailx|mutt|msmtp|swaks|mail)([[:space:]]|$)|mailto:|smtps?://|gws[[:space:]].*(messages[[:space:]]+send|send[[:space:]]+message|gmail[[:space:]].*(\+send|drafts[[:space:]]+send|forwardingAddresses|updateAutoForwarding|delegates|filters))|osascript.*(Mail|Messages)|api\.telegram\.org|hooks\.slack\.com|slack\.com/api/chat|api\.sendgrid|api\.mailgun|api\.postmarkapp|api\.resend|api\.mailjet|api\.brevo|smtp2go|api\.sparkpost|api\.elasticemail|zeptomail|mailchannels|email[.-][a-z0-9-]*\.amazonaws|hooks\.zapier|hook\.[a-z0-9.]*make\.com|integromat|graph\.microsoft\.com.*sendmail|gmail\.googleapis\.com.*messages/send|discord(app)?\.com/api/webhooks|api\.twilio\.com|graph\.facebook\.com.*messages|whatsapp[_/-]?send|telegram[_/-]?send|smtplib|SMTP_SSL|http\.client|git[[:space:]]+(send-email|imap-send)'
# block-dangerous: rm ricorsivo (tree protetti), bw export, scrittura config/hook,
# scrittura su git hook e servizi di avvio automatico,
# lettura segreti via shell (.ssh/id_*/credentials/.pem...), docker volume rm.
# 20/10/2026: la cartella delle credenziali anche senza la barra finale (`find ~/.claude/data/credentials | xargs cat`).
# 10/11/2026 (#5097): dopo la pipe anche `|&`, un commento, un gruppo che si apre e sudo o doas con le opzioni.
# 10/11/2026 (#5122): nel gruppo anche altri comandi prima dell'interprete, separati da `;`, `&` o a capo
# (`[:cntrl:]` contiene l'a capo, che fra parentesi quadre non si scrive `\n`).
# 11/11/2026 (#5261): cp, mv, install, ln e rsync in un comando che nomina ~/.claude, prima o dopo (anche
# `cd ~/.claude; cp x .`), e la parola unlock: il nome del file scritto (uno sblocco, settings.json) sta nella
# sorgente e non dopo `.claude/`. Il pre-filtro risparmia un processo: un sì in più costa poco, un no è un buco.
PATTERN_DANGER=':\(\)|/dev/(sd|nvme|disk|hd)|chmod[[:space:]]+-R[[:space:]]+0*777|chown[[:space:]]+-R|\|&?[[:space:]]*(#.*)?([({][[:space:]]*([^|]*[;&[:cntrl:]][[:space:]]*)?)?((sudo|doas)[[:space:]][^|;&]*)?(bash|sh|zsh|fish|python3?|perl|ruby|node|php|powershell|pwsh)([^[:alnum:]_.-]|$)|<\([[:space:]]*(curl|wget|fetch)|eval[[:space:]]|mkfs\.|(^|[^[:alnum:]_.-])(del|erase|rd|rmdir|format(\.com)?)[[:space:]]|rm[[:space:]][^|;&]*(-[a-zA-Z]*[rR][a-zA-Z]*|--recursive)|find[[:space:]].*(-delete|-(exec|execdir|ok|okdir)[[:space:]].*(rm|unlink|shred)|xargs[^|;&]*(rm|unlink|shred))|bw[[:space:]].*export|(^|[^[:alnum:]_.-])(cp|mv|install|ln|rsync)[[:space:]].*\.claude|\.claude.*[^[:alnum:]_.-](cp|mv|install|ln|rsync)[[:space:]]|unlock|\.claude|(^|[;&|(){[:cntrl:]])[[:space:]]*\$[{A-Za-z_]|\.claude/(settings|hooks|firme|\.claude\.json|plugins(/|[[:space:]\"]|$))|CLAUDE(\.local)?\.md|firme/|rilasci\.allowed_signers|aggiornamenti\.py|aggiorna-applica\.sh|arturo/radice|\.claude/arturo(/|[[:space:]\"]|$)|\.claude/[^[:space:]]*unlock|\.git/hooks|LaunchAgents|\.config/(systemd/user|autostart)|\.ssh(/|[[:space:]\"]|$)|id_(rsa|ed25519|ecdsa|dsa)|\.aws(/|[[:space:]\"]|$)|\.gnupg(/|[[:space:]\"]|$)|\.secrets(/|[[:space:]\"]|$)|\.git-credentials|\.pem|service-account|credentials\.json|client_secret|token_cache|\.pypirc|secrets\.env|\.secrets/|\.config/gh/hosts|\.npmrc|\.claude/data/credentials(/|[[:space:]\"]|$)|\.docker/config|\.kube/config|docker[[:space:]]+(volume[[:space:]]+rm|system[[:space:]]+prune)|(^|[^[:alnum:]_.-])sed[[:space:]]|\.env([^[:alnum:]_]|$)|rmtree|rm(dir)?Sync|\.rm[[:space:]]*\(|[Rr]emove-[Ii]tem|(^|[^[:alnum:]_.-])(powershell|pwsh)(\.exe)?[[:space:]]'
# 11/11/2026 (#5262, review n. 7): ogni comando che nomina `.claude` (`~/.claude//settings.json`, `H=~/.claude`,
# `~/.claude.json`), e una variabile al posto del programma (`X=rm; $X -rf`): block-dangerous li risolve già.
# 17/10/2026 (#3506): i file .env (anche .env.local), shutil.rmtree. git clean ha un pattern suo,
# PATTERN_GIT_CLEAN, che parte prima dello skip git-puro.
# 7/11/2026 (review, finding 1 8 9): l'interprete dopo la pipe chiuso da ; ) " o && e con sudo -E; ogni
# sed (le regole sed-w e sed-e le giudica block-dangerous); rmtree anche senza il prefisso shutil.;
# Remove-Item e powershell o pwsh, che su Windows cancellano cartelle.
# 13/11/2026 (HK-5): powershell e pwsh dopo la pipe (`curl u | powershell -`), rmSync, rmdirSync e fs.rm( di
# node, che block-dangerous giudica come shutil.rmtree.
# Commit secret gate: scansiona il diff staged prima di git commit / gh pr create.
# Dal 15/10/2026 parte anche su un commit a capo, in una subshell o in $( ), dopo `env VAR=… `
# o assegnazioni, e con opzioni di git prima di commit (-c k=v, -C dir, --no-pager).
# Dal 15/10/2026 anche dentro virgolette (`bash -c 'git commit'`, `eval "git commit"`) e dopo
# nohup, time, xargs e sudo: commit-secret-gate.py sa già leggerli, il pre-filtro non lo chiamava.
# 11/11/2026 (#5262, review n. 7): anche dopo then, else, do, `{` e `!`, e con un percorso davanti a git.
PATTERN_COMMIT="(^|[;&|(\`'\"${_NL}])[[:space:]]*((env|command|exec|nohup|time|xargs|sudo|then|else|elif|do|if|while|until|!|\{)[[:space:]]+)*([A-Za-z_][A-Za-z0-9_]*=[^[:space:]]*[[:space:]]+)*(([^[:space:];&|]*/)?git([[:space:]]+-[^[:space:]]+([[:space:]]+[^-[:space:]][^[:space:]]*)?)*[[:space:]]+commit|gh[[:space:]]+pr[[:space:]]+create)"
# exfil: upload di un FILE LOCALE con curl o wget (`-F @file`, `-T`, `--upload-file`, `-d @file`), la forma
# con cui una chiave o un dump escono dalla macchina. Dal 28/10/2026 il POST generico e il codice python
# che chiama la rete non passano più da qui: li giudica il classificatore di auto mode (contratto delle
# guardie: certezze all'hook, dubbi al classificatore). Le email via smtplib restano a comms-guard.
# _FINE_ARG chiude un argomento nella shell (uno spazio) o in una lista python (`'curl', '-d', '@x'`):
# con il solo spazio un invio da subprocess.run([...]) passava senza conferma (21/10/2026, #3645).
_FINE_ARG="([[:space:]]|[\"'],[[:space:]]*[\"']?)"
# Un & seguito da un carattere che non è spazio né operatore sta dentro l'URL (`?a=1&b=2`) e non chiude
# il comando: prima `curl "https://x/?a=1&b=2" -d @file` passava senza conferma (30/10/2026).
# Qui il confronto resta esatto anche su macOS e Windows, perché le opzioni contano la maiuscola (`-T` carica
# un file, `-t` no; `-F` è un form, `-f` no): senza, quasi ogni curl faceva partire due processi in più. Solo
# i nomi dei due programmi sono scritti in ogni maiuscola (HK-1b).
PATTERN_EXFIL='([cC][uU][rR][lL]|[wW][gG][eE][tT])([^|;&]|&[^[:space:]&|;])*(-[[:alnum:]]*F'"$_FINE_ARG"'*[^[:space:]]*[@<]|--form'"$_FINE_ARG"'*[^[:space:]]*[@<]|-[[:alnum:]]*T'"$_FINE_ARG"'|--upload-file|--(post|body)-file|-[[:alnum:]]*d'"$_FINE_ARG"'*["'"'"']?@|--data[a-z-]*'"$_FINE_ARG"'*["'"'"']?@|--json'"$_FINE_ARG"'*["'"'"']?@|--url-query'"$_FINE_ARG"'*["'"'"']?@)'
# Il GET non passa da exfil-guard (ramo tolto il 30/10/2026, #4325). Vanno a exfil-guard i soli canali di rete grezzi: una pipe verso
# nc/ncat/netcat/socat, /dev/tcp e /dev/udp. Dal 28/10/2026 curl con $() e il codice node o python che
# chiama la rete non passano più da qui: li giudica il classificatore di auto mode. Uno script che
# legge archive.org con urllib riceveva "Invio di dati (POST/upload)".
# 11/11/2026 (#5262, review n. 7): nc, ncat, netcat e socat anche senza pipe (`nc host 443 < file`).
PATTERN_EGRESS_SOSPETTO='(^|[^[:alnum:]_.-])(nc|ncat|netcat|socat)([[:space:]]|$)|/dev/(tcp|udp)/'
# Una redirezione verso /dev/tcp scrive in rete anche da un comando che sembra sola lettura (`echo x > /dev/tcp/…`).
PATTERN_DEV_TCP='[<>]&?[[:space:]]*/dev/(tcp|udp)/'
# git clean -f con opzioni in mezzo (`git -C dir clean -fdx`, `git -c k=v clean --force`).
# Anche l'inizio di --force (`--forc`, git lo accetta) e `-c clean.requireForce=false`, che cancella
# senza -f (20/10/2026, #3525).
# git branch -D e git stash drop: dal 31/10/2026 li giudica block-dangerous (tace se il lavoro esiste
# altrove), non più un deny. Partono prima dello skip git-puro, come git clean.
# Dal 7/11/2026 anche git worktree remove (finding 9): la regola git-worktree c'era, ma il dispatcher non
# la chiamava.
PATTERN_GIT_PERDE='(^|[^[:alnum:]_.-])git[[:space:]]([^|;&]*[[:space:]])?(branch[[:space:]]([^|;&]*[[:space:]])?(-[[:alpha:]]*D|--d|-[[:alpha:]]*d)|stash[[:space:]]+(drop|clear)|worktree[[:space:]]+remove)'
# Ogni git push (7/11/2026, finding 5): block-dangerous guarda il flag di forza in qualunque posizione.
PATTERN_GIT_PUSH='(^|[^[:alnum:]_.-])git[[:space:]]([^|;&]*[[:space:]])?push([[:space:]]|$)'
# Un push con la destinazione riscritta da -c, --config-env o GIT_CONFIG_* (1/11/2026): lo giudica block-dangerous.
PATTERN_GIT_DEST='(^|[^[:alnum:]_.-])git[[:space:]][^|;&]*(-c|--config-env)[^|;&]*[[:space:]]push|GIT_CONFIG_(COUNT|KEY_[0-9]+|PARAMETERS)='
# git commit --amend su un commit che questa sessione non ha fatto (3/11/2026, #4187): lo giudica block-dangerous.
PATTERN_GIT_AMEND='(^|[^[:alnum:]_.-])git[[:space:]]([^|;&]*[[:space:]])?commit[[:space:]]([^|;&]*[[:space:]])?--am'
PATTERN_GIT_CLEAN='(^|[^[:alnum:]_.-])git[[:space:]]([^|;&]*[[:space:]])?clean[[:space:]]([^|;&]*[[:space:]])?(-[[:alpha:]]*f|--f)|(^|[^[:alnum:]_.-])git[[:space:]][^|;&]*[cC]lean\.[rR]equire[fF]orce'
# data-guard: operazioni DATI irreversibili non coperte da block-dangerous
# (SQL DROP/TRUNCATE/DELETE FROM, docker compose down -v, rsync --delete remoto, overwrite .db).
# 13/11/2026 (HK-5): su Windows robocopy con /MIR o /PURGE (in Git Bash anche `//MIR`) e reg delete.
PATTERN_DATA='[Rr][Oo][Bb][Oo][Cc][Oo][Pp][Yy][^|&;]*[[:space:]]["'"'"']?/+([Mm][Ii][Rr]|[Pp][Uu][Rr][Gg][Ee])|(^|[^[:alnum:]_.-])[Rr][Ee][Gg][[:space:]]+[Dd][Ee][Ll][Ee][Tt][Ee]|[Dd][Rr][Oo][Pp][[:space:]]+([Tt][Aa][Bb][Ll][Ee]|[Dd][Aa][Tt][Aa][Bb][Aa][Ss][Ee]|[Ss][Cc][Hh][Ee][Mm][Aa])|[Tt][Rr][Uu][Nn][Cc][Aa][Tt][Ee]|[Dd][Ee][Ll][Ee][Tt][Ee][[:space:]]+[Ff][Rr][Oo][Mm]|docker([[:space:]]+compose|-compose)[^|&;]*[[:space:]]down[^|&;]*(-v|--volumes)|rsync[^|&;]*--del(ete)?([^[:alnum:]_]|$)|>[[:space:]]*[^>[:space:]|&;]*\.(db|sqlite|sqlite3|sql|dump)'

# Esegue un guard: un crash o stdout non decisionale diventa ask, mai allow implicito.
# $1 = la guardia che si e' rotta: la telemetria la registra come `errore`.
ask_guard() {
    [[ -n "${1:-}" && -f "$ARTURO_BIN/telemetria.py" ]] && \
        python3 "$ARTURO_BIN/telemetria.py" registra errore "$1" >/dev/null 2>&1
    printf '%s\n' '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"ask","permissionDecisionReason":"Una guardia non ha prodotto una decisione valida. Conferma prima di eseguire il comando."}}'
    exit 0
}

# Telemetria (bin/telemetria.py): il nome della guardia che ha bloccato, mai il comando.
# Dice dove le persone si fermano e quali guardie danno falsi positivi. Non fallisce mai.
segna_guardia() {
    [[ -f "$ARTURO_BIN/telemetria.py" ]] && python3 "$ARTURO_BIN/telemetria.py" registra guardia "$1" >/dev/null 2>&1
    return 0
}

# Una guardia ha chiesto conferma: `chiede`, e la chiamata resta in attesa. Se lo strumento parte,
# il PostToolUse registra `confermata` (bin/telemetria.py esito). Il rapporto fra i due dice quali
# guardie chiedono a vuoto. Escono il nome della guardia e l'id della chiamata, mai il comando.
segna_chiede() {
    [[ -f "$ARTURO_BIN/telemetria.py" ]] || return 0
    local uso
    uso=$(printf '%s' "$INPUT" | python3 -c 'import json, sys
try: print(json.load(sys.stdin).get("tool_use_id") or "")
except Exception: pass' 2>/dev/null)
    [[ -n "$uso" ]] && python3 "$ARTURO_BIN/telemetria.py" chiede "$1${2:+.$2}" "$uso" >/dev/null 2>&1
    return 0
}

# --- Guardie personali (~/.claude/arturo/bash-dispatcher.local, 30/10/2026) ---
# Il file sta in ~/.claude/arturo/ dagli strati F1 (#4531); finché lì manca vale il vecchio
# ~/.claude/hooks/bash-dispatcher.local.
# Chi installa Arturo aggiunge le sue guardie senza toccare questo file. Il .local è solo dati, una
# riga per guardia: `<punto> <guardia> [argomenti]`, `#` per i commenti. Si legge riga per riga e non
# si esegue mai: un `exit 0` scritto lì spegnerebbe tutte le guardie. I punti sono questi quattro:
#   prima-danger   prima di block-dangerous, sui comandi che block-dangerous guarda; può dare allow
#   danger-claude  al posto di block-dangerous sui comandi che nominano .claude (solo la prima riga);
#                  se si rompe decide block-dangerous; non può dare allow
#   attenua        dopo un ask di block-dangerous, exfil-guard, data-guard o danger-claude: se stampa
#                  "tace" l'ask cade e il comando prosegue verso le guardie seguenti; mai un allow
#   finale         prima del ramo memoria, sui comandi che nominano .claude; può dare allow
# La guardia sta in hooks/, il nome è [A-Za-z0-9_.-] con .py o .sh. Ogni guardia gira dentro run_guard:
# un crash chiede conferma. Una riga che non rispetta la forma si salta e lo dice su stderr.
_LOC_PUNTO=(); _LOC_GUARDIA=(); _LOC_ARGS=()
_PUNTI_LOCALI=" prima-danger danger-claude attenua finale "
_LOC_FILE="$HOME/.claude/arturo/bash-dispatcher.local"
[[ ! -f "$_LOC_FILE" && -f "$HOME/.claude/hooks/bash-dispatcher.local" ]] && _LOC_FILE="$HOME/.claude/hooks/bash-dispatcher.local"
if [[ -f "$_LOC_FILE" ]]; then
    while IFS= read -r _riga || [[ -n "$_riga" ]]; do
        _riga="${_riga%%#*}"; _riga="${_riga//$'\r'/}"
        _p=""; _g=""; _a=""
        read -r _p _g _a <<< "$_riga"
        [[ -z "$_p" ]] && continue
        if [[ "$_PUNTI_LOCALI" == *" $_p "* && "$_g" =~ ^[A-Za-z0-9_.-]+\.(py|sh)$ && -f "$(guardia_file "$_g")" ]]; then
            _LOC_PUNTO+=("$_p"); _LOC_GUARDIA+=("$_g"); _LOC_ARGS+=("$_a")
        else
            echo "bash-dispatcher.local: riga ignorata, forma non valida o guardia assente: $_riga" >&2
        fi
    done < "$_LOC_FILE"
fi
# Gli indici delle righe di un punto, nell'ordine del file.
locali() {
    local i
    for i in "${!_LOC_PUNTO[@]}"; do [[ "${_LOC_PUNTO[$i]}" == "$1" ]] && printf '%s\n' "$i"; done
    return 0
}
run_locale() {
    local args=()
    read -ra args <<< "${_LOC_ARGS[$1]}"
    run_guard "${_LOC_GUARDIA[$1]}" "${args[@]}"
}
# Le guardie il cui ask passa dal punto attenua. danger-claude si aggiunge quando c'è.
_ATTENUABILI=" block-dangerous.py exfil-guard.py data-guard.py "
for _i in $(locali danger-claude); do _ATTENUABILI+="${_LOC_GUARDIA[$_i]} "; break; done
# Vero se una guardia del punto attenua risponde "tace" all'ask di $1 (JSON in $2).
attenua() {
    local i r args
    for i in $(locali attenua); do
        args=()
        read -ra args <<< "${_LOC_ARGS[$i]}"
        r=$(ATTENUA_OUT="$2" lancia_guardia "${_LOC_GUARDIA[$i]}" "${args[@]}" "$1" 2>/dev/null) || continue
        [[ "${r//[$'\r\n']/}" == "tace" ]] && return 0
    done
    return 1
}
# _RISERVA: la guardia che decide se questa si rompe. _SENZA_ALLOW: un allow vale come guardia rotta.
_RISERVA=""; _SENZA_ALLOW=""

lancia_guardia() {
    local g="$1"; shift
    if [[ "$g" == *.sh ]]; then
        ARTURO_REGOLA=1 bash "$(guardia_file "$g")" "$@" <<< "$GUARD_INPUT"
    else
        ARTURO_REGOLA=1 python3 "$(guardia_file "$g")" "$@" <<< "$GUARD_INPUT"
    fi
}

run_guard() {
    local out rc regola="" riserva="$_RISERVA" senza_allow="$_SENZA_ALLOW"
    _RISERVA=""; _SENZA_ALLOW=""
    # ARTURO_REGOLA=1: una guardia che sa nominare la regola che chiede (block-dangerous, commit-secret-gate) la scrive in
    # una riga "REGOLA: <nome>" dopo il JSON. Si toglie qui, prima di ogni controllo: Claude Code
    # riceve solo il JSON, la telemetria registra <guardia>.<regola> (22/10/2026).
    out=$(lancia_guardia "$@")
    rc=$?
    if [[ $rc -ne 0 && $rc -ne 2 && -n "$riserva" ]]; then
        run_guard "$riserva"
        return 0
    fi
    if [[ "$out" == *$'\n'"REGOLA: "* ]]; then
        regola=${out##*$'\n'REGOLA: }
        regola=${regola%$'\r'}  # Python su Windows scrive \r\n
        out=${out%$'\n'REGOLA: *}
        out=${out%$'\r'}
        [[ "$regola" =~ ^[a-z0-9-]{1,30}$ ]] || regola=""
    fi
    if [[ $rc -eq 2 ]]; then
        [[ -n "$out" ]] && printf '%s\n' "$out" >&2
        segna_guardia "$1"
        exit 2
    fi
    [[ $rc -ne 0 || -z "$out" ]] && { [[ $rc -ne 0 ]] && ask_guard "$1"; return 0; }
    if printf '%s' "$out" | python3 -c 'import json, sys
try:
    value = json.load(sys.stdin)["hookSpecificOutput"]["permissionDecision"]
    sys.exit(0 if value in {"ask", "allow", "deny"} else 1)
except Exception:
    sys.exit(1)'; then
        [[ -n "$senza_allow" && "$out" == *'"allow"'* ]] && ask_guard "$1"
        if [[ "$out" == *'"ask"'* && "$_ATTENUABILI" == *" $1 "* ]] && attenua "$1" "$out"; then
            return 0
        fi
        [[ "$out" == *'"deny"'* ]] && segna_guardia "$1"
        [[ "$out" == *'"ask"'* ]] && segna_chiede "$1" "$regola"
        printf '%s\n' "$out"
        exit 0
    fi
    ask_guard "$1"
}

# Commit secret gate: PRIMA dello skip git-puro (scansiona il diff, non il message).
{ somiglia "$COMMAND" "$PATTERN_COMMIT" || vede "$PATTERN_COMMIT"; } && run_guard commit-secret-gate.py

# git clean -f cancella i file non tracciati, che git non sa ridare: PRIMA dello skip git-puro, che
# altrimenti lascerebbe passare `git log && git clean -fdx` (17/10/2026, #3506).
vede "$PATTERN_GIT_CLEAN" && run_guard block-dangerous.py
vede "$PATTERN_GIT_PERDE" && run_guard block-dangerous.py
vede "$PATTERN_GIT_PUSH" && run_guard block-dangerous.py
vede "$PATTERN_GIT_DEST" && run_guard block-dangerous.py
vede "$PATTERN_GIT_AMEND" && run_guard block-dangerous.py

# --- Skip pre-filtro su git puro (commit/log/show...): i message possono
# contenere "rm -rf"/"smtplib" come testo, NON sono esecuzioni. Skip SOLO se
# ogni segmento (; && || | e newline) inizia con git o cd, altrimenti si prosegue.
# I newline vanno collassati in un sentinello PRIMA di spogliare le stringhe
# quotate: un messaggio -m multi-riga altrimenti resterebbe non spogliato (sed
# lavora riga per riga) e i suoi segmenti farebbero fallire il check. Il
# sentinello resta poi un separatore di comando nello split (newline = come ;). ---
# Lo skip git-puro spoglia le stringhe quotate per capire se ogni segmento e' git/cd.
# Ma bash ESEGUE `$(...)`, i backtick e le process substitution <()/>() ANCHE dentro
# le doppie virgolette: `git commit -m "$(comando)"` verrebbe ridotto a `git commit -m`,
# dichiarato git-puro, e ogni guard saltato mentre la sostituzione gira. Se il comando
# contiene una sostituzione, NON e' git-puro: si prosegue coi guard.
PATTERN_SUBST='\$\(|`|<\(|>\('
# `--no-index` fa leggere a git diff e git grep un file qualunque del disco, anche una chiave: non è testo
# inerte, e il comando passa da block-dangerous (11/11/2026, #5262).
# Tre confronti, ognuno con la sua regola sulle maiuscole (HK-1b):
# - il programma e il sottocomando (PATTERN_GIT_TEXT) passano da `somiglia`: `Git log` è `git log`;
# - le opzioni (PATTERN_GIT_OPZIONI) restano esatte: `-c` (configurazione) e `-C` (cartella) sono opzioni
#   diverse, e git non accetta `--OUTPUT`;
# - i sottocomandi che inviano (PATTERN_GIT_INVIA) passano da `somiglia`: sono programmi a parte nella
#   cartella di git, e il disco li trova anche scritti `Send-Email`.
PATTERN_GIT_OPZIONI='(^|[[:space:]])(--output|--exec-path|--config-env|--no-index|-c[[:space:]])|(^|[^>])>>?[^&|;]'
PATTERN_GIT_INVIA='send-email|imap-send'
_GIT_TESTO=0
somiglia "$COMMAND" "$PATTERN_GIT_TEXT" && _GIT_TESTO=1
_GIT_UNSAFE=0
if [[ "$COMMAND" =~ $PATTERN_GIT_OPZIONI ]] || somiglia "$COMMAND" "$PATTERN_GIT_INVIA"; then
    _GIT_UNSAFE=1
fi
if [[ $_GIT_TESTO -eq 1 && ! "$COMMAND" =~ $PATTERN_SUBST && "$COMMAND" != *"--output"* && "$COMMAND" != *"--exec-path"* && "$COMMAND" != *"--config-env"* && $_GIT_UNSAFE -eq 0 ]]; then
    # Le virgolette si leggono come le legge bash (forma_comando.py, shlex): lo strip con
    # sed accoppiava un apostrofo dentro le doppie con uno piu' avanti e cancellava i
    # comandi in mezzo. Ogni programma eseguito deve essere git o cd, anche col path
    # completo o in un blocco. Virgolette che non tornano o errore di python: non e'
    # git puro, e il comando passa dalle guardie.
    GIT_PURE=0
    # Come per le guardie: su Windows un argomento che sembra un path verrebbe convertito.
    MSYS2_ARG_CONV_EXCL='*' python3 "$ARTURO_HOOKS/forma_comando.py" git-puro "$COMMAND" 2>/dev/null && GIT_PURE=1
    [[ $GIT_PURE -eq 1 ]] && exit 0
fi

# Opzioni Git che possono cambiare scritture o comportamento non sono testo inerte.
[[ $_GIT_TESTO -eq 1 && $_GIT_UNSAFE -eq 1 ]] && run_guard block-dangerous.py

# Comms guard: invii email/messaggi esterni (draft-first). Il match si rifa' sul CODICE eseguito:
# comms-prefilter.py toglie gli heredoc scritti su file e tace sui comandi di sola lettura
# (`grep -ril smtplib .`), che nominano un invio senza farlo. Se il pre-filtro non gira, si
# giudica il comando intero.
invio_in_vista() { somiglia "$1" "$PATTERN_COMMS" || [[ "$1" == *"gws "* && "$1" == *"messages send"* ]]; }
if invio_in_vista "$GUARD_COMMAND"; then
    COMMS_REDUCED=$(python3 "$ARTURO_HOOKS/comms-prefilter.py" <<< "$GUARD_INPUT" 2>/dev/null) || COMMS_REDUCED=$GUARD_COMMAND
    if invio_in_vista "$COMMS_REDUCED"; then
        export COMMS_REDUCED
        run_guard comms-guard.py
    fi
fi

# Block dangerous: rm su tree protetti, bw export, scrittura config/hook, fork bomb...
# Prima le guardie personali di prima-danger; sui comandi che nominano .claude, se il .local ha una
# danger-claude, decide lei e block-dangerous resta come riserva.
# 4/11/2026 (#4566): una scrittura relativa dopo un `cd` dentro ~/.claude, o con la sessione già lì
# (`cd ~/.claude && echo x > plugins/cache/...`, `> hooks/a.py`), non nomina il percorso protetto: il
# pre-filtro testuale non la vedeva e block-dangerous, che risolve il percorso, non partiva.
PATTERN_CD_CLAUDE="(^|[;&|(${_NL}][[:space:]]*)(cd|pushd)[[:space:]]+[^;&|${_NL}]*\.claude([/[:space:]\"']|\$)"
_RE_CWD_CLAUDE='"cwd"[[:space:]]*:[[:space:]]*"[^"]*[/\\]\.claude'
# Con la sessione dentro `.git`, `cp x hooks/pre-commit` scrive un hook di git senza nominare `.git/hooks`
# (11/11/2026, #5262): block-dangerous risolve il percorso, il pre-filtro guarda la cartella della sessione.
_RE_CWD_GIT='"cwd"[[:space:]]*:[[:space:]]*"[^"]*[/\\]\.git(["/\\])'
# Su Windows i percorsi hanno anche le barre rovesciate (`"C:\Users\x\.claude\settings.json"`), e PATTERN_DANGER
# cerca `.claude/`: il pre-filtro prova anche il comando con le barre dritte (review del 9/11/2026, #5096).
# Anche il `cd` si legge con le barre dritte: `cd "C:\...\.claude\data" && echo x > ../settings.json` ha
# `.claude` seguito da una barra rovesciata, che PATTERN_CD_CLAUDE non conta come fine del nome (#5121).
_GUARD_DRITTO="$GUARD_COMMAND"
if [[ "$OSTYPE" == msys* || "$OSTYPE" == cygwin* ]]; then
    _GUARD_DRITTO="${GUARD_COMMAND//\\//}"
fi
# Su macOS e Windows il disco ignora le maiuscole: `rm ~/.CLAUDE/settings.json` tocca la config (7/11/2026,
# finding 11). Dal 10/11/2026 lo copre `somiglia`, che lì confronta PATTERN_DANGER senza le maiuscole.
if vede "$PATTERN_DANGER" || somiglia "$_SENZA_NULL" "$PATTERN_SCRIVE" || somiglia "$_GUARD_DRITTO" "$PATTERN_DANGER" || somiglia "$_GUARD_DRITTO" "$PATTERN_CD_CLAUDE" || somiglia "$INPUT" "$_RE_CWD_CLAUDE" || somiglia "$INPUT" "$_RE_CWD_GIT"; then
    for _i in $(locali prima-danger); do run_locale "$_i"; done
    _DC=""; for _i in $(locali danger-claude); do _DC=$_i; break; done
    if [[ -n "$_DC" && ( "$COMMAND" == *".claude"* || "$INPUT" =~ $_RE_CWD_CLAUDE ) ]]; then
        _RISERVA=block-dangerous.py; _SENZA_ALLOW=1
        run_locale "$_DC"
    else
        run_guard block-dangerous.py
    fi
fi

# Exfil guard: upload di un file locale verso host esterni -> ask. Come per comms, si giudica il
# codice eseguito: COMMS_REDUCED e' il comando senza gli heredoc scritti su file (vuoto se
# il comando solo legge). Se il pre-filtro non gira, si giudica il comando intero.
if [[ "$GUARD_COMMAND" =~ $PATTERN_EXFIL ]]; then
    [[ -z "${COMMS_REDUCED+x}" ]] && { COMMS_REDUCED=$(python3 "$ARTURO_HOOKS/comms-prefilter.py" <<< "$GUARD_INPUT" 2>/dev/null) || COMMS_REDUCED=$GUARD_COMMAND; }
    if [[ "$COMMS_REDUCED" =~ $PATTERN_EXFIL ]]; then
        export COMMS_REDUCED
        run_guard exfil-guard.py
    fi
fi

# I canali di PATTERN_EGRESS_SOSPETTO (17/10/2026, #3506, ridotti il 28/10) passano da exfil-guard, sul codice eseguito come
# per il POST. Una redirezione verso /dev/tcp si giudica sul comando intero: il pre-filtro tace su
# `echo`, che lì scrive in rete.
if vede "$PATTERN_EGRESS_SOSPETTO"; then
    [[ -z "${COMMS_REDUCED+x}" ]] && { COMMS_REDUCED=$(python3 "$ARTURO_HOOKS/comms-prefilter.py" <<< "$GUARD_INPUT" 2>/dev/null) || COMMS_REDUCED=$GUARD_COMMAND; }
    if somiglia "$COMMS_REDUCED" "$PATTERN_EGRESS_SOSPETTO" || { [[ "$COMMS_REDUCED" == "$GUARD_COMMAND" ]] && somiglia "$_SCIOLTO" "$PATTERN_EGRESS_SOSPETTO"; }; then
        export COMMS_REDUCED
        run_guard exfil-guard.py
    elif [[ "$GUARD_COMMAND" =~ $PATTERN_DEV_TCP ]]; then
        export COMMS_REDUCED=$GUARD_COMMAND
        run_guard exfil-guard.py
    fi
fi

# Data guard: operazioni distruttive sui DATI (SQL drop, volumi, rsync --delete) -> ask.
somiglia "$GUARD_COMMAND" "$PATTERN_DATA" && run_guard data-guard.py

# GitHub CLI: operazioni distruttive/sensibili (repo delete, secret, api mutante...).
{ somiglia "$COMMAND" "$PATTERN_GH_ANY" || vede "$PATTERN_GH_ANY"; } && run_guard gh-destructive-guard.py

# Guardie personali del punto finale, sui comandi che nominano .claude.
if [[ "$COMMAND" == *".claude"* || "$INPUT" =~ $_RE_CWD_CLAUDE ]]; then
    for _i in $(locali finale); do run_locale "$_i"; done
fi

# Ramo memoria e handoff: nessuna guardia ha deciso. Claude Code chiederebbe conferma a ogni
# scrittura via shell sotto ~/.claude, anche per salvare un handoff o una memoria. Qui l'allow
# arriva solo se forma_comando.py ammette il comando: ogni percorso ~/.claude nominato e ogni
# file scritto stanno in data/handoffs/ o in projects/<p>/memory/, i programmi sono di una
# lista breve, e settings, hook e file di unlock non compaiono nel testo eseguito.
# Altrimenti il ramo tace e decide il flusso normale dei permessi.
if [[ "$COMMAND" == *".claude/"* ]] && python3 "$ARTURO_HOOKS/forma_comando.py" ramo-memoria <<< "$INPUT" 2>/dev/null; then
    printf '%s\n' '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"allow","permissionDecisionReason":"scrittura di un handoff o di una memoria in ~/.claude: approvata dal ramo memoria del dispatcher"}}'
    exit 0
fi

exit 0
