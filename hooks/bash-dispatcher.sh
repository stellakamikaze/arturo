#!/bin/bash
# Dispatcher per PreToolUse Bash hooks.
# Instrada verso gli guard solo quando il comando e' rilevante (un solo processo
# per la stragrande maggioranza dei comandi). Ogni guard puo':
#   - uscire con rc!=0  -> blocco duro (stderr -> modello)
#   - stampare JSON permissionDecision su stdout + rc 0 -> ask/allow esplicito
#   - stampare nulla + rc 0 -> silenzioso (prosegue col guard successivo)
# run_guard cattura la decisione e cortocircuita: al massimo UNA decisione emessa.

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

# --- Pattern pre-filtro (in variabili: evita problemi in [[ =~ ]]) ---
# gh ancorato a inizio comando/segmento, MA tollerando i prefissi che non cambiano
# il comando eseguito: assegnazioni env (FOO=bar), `env`, `command`, `\gh`. Senza
# questo, `FOO=1 gh repo delete` o `command gh ...` eludono i guard gh.
_GH_PREFIX='(env[[:space:]]+)?([A-Za-z_][A-Za-z0-9_]*=[^[:space:]]*[[:space:]]+)*(command[[:space:]]+)?\\?'
PATTERN_GH_ISSUE="(^|[;&|][[:space:]]*)${_GH_PREFIX}gh[[:space:]]+(issue|pr)[[:space:]]"
PATTERN_GH_ANY="(^|[;&|][[:space:]]*)${_GH_PREFIX}gh[[:space:]]"
PATTERN_GIT_TEXT='(^|[;&|][[:space:]]*)git[[:space:]]+(-C[[:space:]]+[^[:space:]]+[[:space:]]+)?(commit|log|show|tag|stash[[:space:]]+(push|save))'
PATTERN_COMMS='sendmail|mail[[:space:]]+-s|mailx|mutt|swaks|osascript.*(Mail|Messages)|api\.telegram\.org|hooks\.slack\.com|slack\.com/api/chat|api\.sendgrid|api\.mailgun|api\.postmarkapp|api\.resend|api\.mailjet|api\.brevo|smtp2go|api\.sparkpost|api\.elasticemail|zeptomail|mailchannels|email[.-][a-z0-9-]*\.amazonaws|hooks\.zapier|hook\.[a-z0-9.]*make\.com|integromat|graph\.microsoft\.com.*sendmail|gmail\.googleapis\.com.*messages/send|discord(app)?\.com/api/webhooks|api\.twilio\.com|graph\.facebook\.com.*messages|whatsapp[_/-]?send|telegram[_/-]?send|smtplib|SMTP_SSL'
# block-dangerous: rm ricorsivo (tree protetti), bw export, scrittura config/hook,
# lettura segreti via shell (.ssh/id_*/credentials/.pem...), docker volume rm.
PATTERN_DANGER=':\(\)|/dev/(sd|nvme|disk|hd)|chmod[[:space:]]+-R[[:space:]]+0*777|chown[[:space:]]+-R|\|[[:space:]]*(sudo[[:space:]]+)?(bash|sh|zsh|fish|python3?|perl|ruby|node|php)([[:space:]]|$)|<\([[:space:]]*(curl|wget|fetch)|eval[[:space:]]|mkfs\.|rm[[:space:]]+(-[a-zA-Z]*[rR][a-zA-Z]*|--recursive)|bw[[:space:]]+export|\.claude/(settings|hooks|\.claude\.json)|\.claude/[^[:space:]]*unlock|\.ssh/|id_(rsa|ed25519|ecdsa|dsa)|\.aws/credentials|\.gnupg/|\.git-credentials|\.pem|service-account|credentials\.json|\.pypirc|secrets\.env|\.secrets/|\.config/gh/hosts|\.npmrc|\.docker/config|\.kube/config|docker[[:space:]]+(volume[[:space:]]+rm|system[[:space:]]+prune)'
# Commit secret gate: scansiona il diff staged prima di git commit / gh pr create.
PATTERN_COMMIT='(^|[;&|][[:space:]]*)(git[[:space:]]+(-C[[:space:]]+[^[:space:]]+[[:space:]]+)?commit|gh[[:space:]]+pr[[:space:]]+create)'
# exfil: POST/upload di dati (curl/wget con metodo o payload; python post/smtplib).
PATTERN_EXFIL='(curl|wget)[[:space:]].*(-X[[:space:]]*(POST|PUT|PATCH|DELETE)|--request[[:space:]]*(POST|PUT|PATCH|DELETE)|-d[[:space:]]|--data|-F[[:space:]]|--form|-T[[:space:]]|--upload-file)|requests\.(post|put|patch|delete)|urllib\.request|httpx\.(post|put|patch)|import[[:space:]]+smtplib|smtplib\.'
# exfil ramo egress-GET/transport: canali che portano dati fuori SENZA POST e che
# sfuggivano al pattern sopra — curl/wget GET, DNS-exfil (dig/nslookup/host),
# /dev/tcp, netcat/socat. exfil-guard.py decide poi con precisione (ask solo su
# command-substitution/blob-opaco/host esterno; host interni esclusi).
PATTERN_EGRESS_GET='(^|[;&|[:space:]])(curl|wget|dig|nslookup|host|nc|ncat|socat)[[:space:]]|/dev/tcp/'
# data-guard: operazioni DATI irreversibili non coperte da block-dangerous
# (SQL DROP/TRUNCATE/DELETE FROM, docker compose down -v, rsync --delete remoto, overwrite .db).
PATTERN_DATA='[Dd][Rr][Oo][Pp][[:space:]]+([Tt][Aa][Bb][Ll][Ee]|[Dd][Aa][Tt][Aa][Bb][Aa][Ss][Ee]|[Ss][Cc][Hh][Ee][Mm][Aa])|[Tt][Rr][Uu][Nn][Cc][Aa][Tt][Ee]|[Dd][Ee][Ll][Ee][Tt][Ee][[:space:]]+[Ff][Rr][Oo][Mm]|docker[[:space:]]+compose[[:space:]]+down[^|&;]*(-v|--volumes)|rsync[^|&;]*--delete|>[[:space:]]*[^>[:space:]|&;]*\.(db|sqlite|sqlite3|sql|dump)'

# Esegue un guard: cortocircuita su blocco (rc!=0) o su decisione (stdout non vuoto).
run_guard() {
    local out rc
    out=$(python3 "$HOME/.claude/hooks/$1" <<< "$INPUT")   # stderr passa oltre
    rc=$?
    if [[ $rc -ne 0 ]]; then
        [[ -n "$out" ]] && printf '%s\n' "$out" >&2
        exit $rc
    fi
    if [[ -n "$out" ]]; then
        printf '%s\n' "$out"
        exit 0
    fi
}

# Commit secret gate: PRIMA dello skip git-puro (scansiona il diff, non il message).
[[ "$COMMAND" =~ $PATTERN_COMMIT ]] && run_guard commit-secret-gate.py

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
if [[ "$COMMAND" =~ $PATTERN_GIT_TEXT && ! "$COMMAND" =~ $PATTERN_SUBST ]]; then
    SENT=$'\001'
    # 1) newline -> sentinello, cosi' lo strip delle stringhe quotate (sed, che
    #    lavora riga per riga) copre anche i messaggi -m multi-riga.
    # 2) strip stringhe quotate (il messaggio col suo sentinello sparisce).
    # 3) sentinello superstite (= newline FUORI dai quote) -> newline reale:
    #    resta un separatore di comando come ; && || |.
    STRIPPED=$(printf '%s' "$COMMAND" | tr '\n' "$SENT" \
        | sed -E "s/'[^']*'//g; s/\"[^\"]*\"//g" \
        | tr "$SENT" '\n')
    GIT_PURE=1
    while IFS= read -r seg; do
        seg="${seg#"${seg%%[![:space:]]*}"}"
        [[ -z "$seg" ]] && continue
        if [[ ! "$seg" =~ ^(git|cd)([[:space:]]|$) ]]; then
            GIT_PURE=0
            break
        fi
    done < <(printf '%s\n' "$STRIPPED" | sed -E 's/\|\||&&|;|\|/\n/g')
    [[ $GIT_PURE -eq 1 ]] && exit 0
fi

# Comms guard: invii email/messaggi esterni (draft-first).
[[ "$COMMAND" =~ $PATTERN_COMMS ]] && run_guard comms-guard.py

# Block dangerous: rm su tree protetti, bw export, scrittura config/hook, fork bomb...
[[ "$COMMAND" =~ $PATTERN_DANGER ]] && run_guard block-dangerous.py

# Exfil guard: POST/upload di dati verso host esterni -> ask.
[[ "$COMMAND" =~ $PATTERN_EXFIL ]] && run_guard exfil-guard.py

# Exfil guard (ramo egress-GET): curl/wget GET, DNS-exfil, /dev/tcp, nc/socat -> ask se sospetto.
[[ "$COMMAND" =~ $PATTERN_EGRESS_GET ]] && run_guard exfil-guard.py

# Data guard: operazioni distruttive sui DATI (SQL drop, volumi, rsync --delete) -> ask.
[[ "$COMMAND" =~ $PATTERN_DATA ]] && run_guard data-guard.py

# GitHub CLI: content guard (claude/anthropic nei testi issue/PR).
[[ "$COMMAND" =~ $PATTERN_GH_ISSUE ]] && run_guard github_issue_guard.py

# GitHub CLI: operazioni distruttive/sensibili (repo delete, secret, api mutante...).
[[ "$COMMAND" =~ $PATTERN_GH_ANY ]] && run_guard gh-destructive-guard.py

exit 0
