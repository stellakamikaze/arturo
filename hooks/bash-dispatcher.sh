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
# Uno script Python dal bytecode in __pycache__, come `python3 FILE ARG...` (evento_bash.py esegui, #6327): lanciato
# direttamente, block-dangerous si ricompilava dal sorgente a ogni comando, circa 19 ms su 65. Senza
# evento_bash.py (un'installazione a metà) parte lo script com'era: `python3` su un file che manca esce 2, che
# qui vuol dire blocco.
if [[ -f "$ARTURO_HOOKS/evento_bash.py" ]]; then
    py_cache() { python3 "$ARTURO_HOOKS/evento_bash.py" esegui "$@"; }
else
    py_cache() { python3 "$@"; }
fi

INPUT=$(cat)
# Un solo python3 legge l'evento, prepara le copie del comando e fa il pre-filtro (hooks/evento_bash.py
# prefiltra e hooks/prefiltro_bash.py, 22/11/2026, #6327):
#   COMMAND        il comando com'è scritto;
#   GUARD_COMMAND  il comando che leggono le guardie: senza gli heredoc che vanno a un lettore e che nessuno
#                  esegue (heredoc.py, Heredoc.dati: `cat <<'EOF' | bash` e i confini incerti restano interi),
#                  e senza il suffisso `.exe` in fondo alle parole, perché su Windows `rm.exe` è `rm` (revisione
#                  del 10/11/2026, HK-1). Cambia solo il testo che leggono le guardie, non il comando eseguito;
#   GUARD_INPUT    l'evento col comando delle guardie, che ogni guardia riceve su stdin. Il comando ci arriva
#                  su stdin: come argomento, oltre il limite del sistema (circa 1 MB su macOS, 128 KB per
#                  argomento su Linux) python non partiva e ogni guardia leggeva "niente da dire" (review del
#                  10/11/2026, n. 9). Un byte che non è UTF-8 si sostituisce, e la lettura non cade;
#   USO_ID         il tool_use_id, per la telemetria delle conferme;
#   VISTE          le parole del pre-filtro: quali guardie partono, e se il comando è git puro. I pattern e la
#                  loro storia stanno in prefiltro_bash.py. Fino al 22/11/2026 erano regex di bash, circa 13 µs
#                  per carattere: 18 secondi su 300.000 caratteri;
#   RIDOTTO        il comando di comms-prefilter.py, senza gli heredoc scritti su file e vuoto per un comando di
#                  sola lettura. Lo leggono comms-guard ed exfil-guard in COMMS_REDUCED. Vale solo con la vista
#                  `ridotto`.
# Prima erano jq e quattro python3, circa 50 ms a ogni comando Bash. Su Windows (`crlf`) il CR davanti a un LF si
# toglie: jq e python scrivevano ogni a capo come CRLF, e le guardie vedevano un comando diverso da quello che
# esegue bash (30/10/2026). Su Mac e Linux il comando resta intatto.
# Su macOS e Windows il disco ignora le maiuscole: `RM -rf`, `Git push --force` e `GH repo delete` fanno partire
# `rm`, `git` e `gh`. Con `nocase` il pre-filtro confronta i nomi senza le maiuscole (revisione del 10/11/2026,
# HK-1b); le opzioni restano esatte. Con `zsh` cerca i glob nelle opzioni, che in zsh falliscono.
# I campi arrivano con la lunghezza in byte nella prima riga, e si tagliano con LC_ALL=C: un `$(...)` solo legge
# a blocchi, mentre `read -d ''` da una pipe legge un byte alla volta. Se le lunghezze non tornano col testo,
# tutti i campi restano vuoti e più sotto si chiede conferma.
COMMAND=""; GUARD_COMMAND=""; GUARD_INPUT=""; USO_ID=""; VISTE=""; RIDOTTO=""
leggi_evento() {
    local LC_ALL=C tutto testa l0="" l1="" l2="" l3="" l4="" l5="" opzioni=()
    [[ "$OSTYPE" == msys* || "$OSTYPE" == cygwin* ]] && opzioni+=(crlf)
    [[ "$OSTYPE" == darwin* || "$OSTYPE" == msys* || "$OSTYPE" == cygwin* ]] && opzioni+=(nocase)
    [[ "${SHELL##*/}" == zsh ]] && opzioni+=(zsh)
    tutto=$(printf '%s' "$INPUT" | python3 "$ARTURO_HOOKS/evento_bash.py" prefiltra ${opzioni[@]+"${opzioni[@]}"} 2>/dev/null; printf x)
    tutto=${tutto%x}
    [[ "$tutto" == *$'\n'* ]] || return 0
    testa=${tutto%%$'\n'*}
    tutto=${tutto#*$'\n'}
    read -r l0 l1 l2 l3 l4 l5 <<< "$testa"
    [[ "$l0" =~ ^[0-9]+$ && "$l1" =~ ^[0-9]+$ && "$l2" =~ ^[0-9]+$ && "$l3" =~ ^[0-9]+$ && "$l4" =~ ^[0-9]+$ && "$l5" =~ ^[0-9]+$ ]] || return 0
    (( ${#tutto} == l0 + l1 + l2 + l3 + l4 + l5 )) || return 0
    COMMAND=${tutto:0:l0}
    GUARD_COMMAND=${tutto:l0:l1}
    GUARD_INPUT=${tutto:l0+l1:l2}
    USO_ID=${tutto:l0+l1+l2:l3}
    VISTE=" ${tutto:l0+l1+l2+l3:l4} "
    RIDOTTO=${tutto:l0+l1+l2+l3+l4:l5}
}
leggi_evento
# Vero se il pre-filtro ha visto $1.
vista() { [[ "$VISTE" == *" $1 "* ]]; }

# Senza un lettore del JSON nessuna guardia vede il comando: con un python3 che non parte (su Windows il
# rimando del Microsoft Store esce 49), COMMAND restava vuoto e ogni comando passava in silenzio (revisione del
# 10/11/2026, HK-2). Se l'input porta un "command" non vuoto e qui non è arrivato niente, si chiede conferma.
# Senza ask_guard: la telemetria è python3, che qui non parte.
_RE_HA_COMANDO='"command"[[:space:]]*:[[:space:]]*"[^"]'
if [[ -z "$COMMAND" && "$INPUT" =~ $_RE_HA_COMANDO ]]; then
    printf '%s\n' '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"ask","permissionDecisionReason":"Le guardie non leggono il comando: manca un python3 che funziona. Conferma solo se sai cosa fa. Per sistemare: /diagnosi."}}'
    exit 0
fi
# Oltre 1.000.000 di caratteri le guardie non finiscono in tempo, e il comando cade sul tempo massimo
# dell'hook. Un comando così lungo dopo la riduzione degli heredoc non è un uso normale: si chiede conferma
# (#5262, n. 9). Il limite era 100.000 finché il pre-filtro era in bash (#5347, #6327): dal 22/11/2026 il
# pre-filtro è in Python: su un Mac il dispatcher intero, con tutte le guardie in gioco, impiega 1,5 secondi su
# 380.000 caratteri e 3,7 su un milione, contro un tempo massimo di 30 (banco PB04). Oltre il limite del sistema
# per l'ambiente (circa 1 MB su macOS, 128 KB per variabile su Linux) COMMS_REDUCED non passa a comms-guard ed
# exfil-guard: la guardia non parte e run_guard chiede conferma, il lato sicuro.
# Questa conferma e le due qui sotto escono con printf, senza ask_guard: run_guard e la telemetria nascono più
# in basso e leggono GUARD_INPUT, che qui manca o non serve. Non entrano in confermeGuardie e non passano da
# attenua: sono casi rari, e una conferma in più è il lato sicuro (#5361, rilievo 11).
if [[ ${#GUARD_COMMAND} -gt 1000000 ]]; then
    printf '%s\n' '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"ask","permissionDecisionReason":"Comando troppo lungo per le guardie (oltre 1.000.000 di caratteri): non lo hanno letto. Conferma solo se sai cosa fa, oppure metti il contenuto in un file."}}'
    exit 0
fi
# Senza la copia dell'evento nessuna guardia vede il comando: si chiede conferma, come sopra per COMMAND.
if [[ -n "$COMMAND" && -z "$GUARD_INPUT" ]]; then
    printf '%s\n' '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"ask","permissionDecisionReason":"Le guardie non riescono a leggere questo comando (troppo lungo o con caratteri non validi). Conferma solo se sai cosa fa."}}'
    exit 0
fi
# Il pre-filtro si è rotto: non si sa quali guardie servono, e nessuna si salta.
if vista errore; then
    printf '%s\n' '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"ask","permissionDecisionReason":"Il pre-filtro delle guardie si è fermato su questo comando. Conferma solo se sai cosa fa. Per sistemare: /diagnosi."}}'
    exit 0
fi
unset COMMS_REDUCED
# Il comando ridotto passa a comms-guard ed exfil-guard: lo stesso testo per tutte e due.
esporta_ridotto() { vista ridotto && export COMMS_REDUCED="$RIDOTTO"; return 0; }

# --- Glob dentro un'opzione, in zsh ---
# `--include=*.md` senza virgolette in zsh è un glob che non trova niente: il comando muore con "no matches
# found" prima di partire. Il pre-filtro scrive la parola nella vista `glob-zsh=`; se la sessione ha la riga di
# session-start.sh che accende nonomatch (marcatore arturo-zsh-come-bash in $CLAUDE_ENV_FILE), la vista non c'è
# (prefiltro_bash.py, _glob_opzione).
if [[ "$VISTE" == *" glob-zsh="* ]]; then
    _OPTGLOB=${VISTE#* glob-zsh=}; _OPTGLOB=${_OPTGLOB%% *}
    _OPT="${_OPTGLOB%%=*}"; _VAL="${_OPTGLOB#*=}"
    echo "BLOCCATO: in zsh '$_OPTGLOB' senza virgolette e' un glob che fallisce con 'no matches found'. Scrivi $_OPT='$_VAL'." >&2
    exit 2
fi

# --- timeout su macOS ---
# Sui Mac `timeout` non esiste: `command not found` va su stderr, la pipeline riceve stdout vuoto e la diagnosi
# finisce sul servizio sbagliato. Il testo lo guarda il pre-filtro (vista `timeout`: fuori da virgolette, senza
# ssh, docker exec ed heredoc); qui si guarda se il programma c'è.
# La guardia può girare con un PATH più corto della shell di Claude, che legge il profilo della persona: lì
# /opt/homebrew/bin c'è, qui a volte no, e `timeout` di coreutils veniva bloccato anche dove esiste
# (20/11/2026, 11 blocchi in 7 giorni). Contano anche le cartelle di Homebrew; ARTURO_TIMEOUT_CARTELLE le
# sostituisce, e vuota le spegne (i banchi del blocco).
_timeout_c_e() {
  command -v timeout &>/dev/null && return 0
  local d
  for d in ${ARTURO_TIMEOUT_CARTELLE-/opt/homebrew/bin /usr/local/bin}; do
    [[ -x "$d/timeout" ]] && return 0
  done
  return 1
}
if vista timeout && ! _timeout_c_e; then
    echo "BLOCCATO: 'timeout' non esiste su questo sistema. Fallirebbe con 'command not found' e stdout vuoto. Usa il parametro timeout del tool Bash, 'curl --max-time N', oppure 'cmd & pid=\$!; sleep N; kill \$pid'." >&2
    exit 2
fi

# Esegue un guard: un crash o stdout non decisionale diventa ask, mai allow implicito.
# $1 = la guardia che si e' rotta: la telemetria la registra come `errore`.
ask_guard() {
    [[ -n "${1:-}" && -f "$ARTURO_BIN/telemetria.py" ]] && \
        py_cache "$ARTURO_BIN/telemetria.py" registra errore "$1" >/dev/null 2>&1
    printf '%s\n' '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"ask","permissionDecisionReason":"Una guardia non ha prodotto una decisione valida. Conferma prima di eseguire il comando."}}'
    exit 0
}

# Una guardia ha deciso, ma il suo controllo non è arrivato in fondo: `errore`, <guardia>.<causa>.
# La causa è un nome di un elenco chiuso (CAUSE in bin/telemetria.py), mai il messaggio di git.
segna_errore() {
    [[ -f "$ARTURO_BIN/telemetria.py" ]] && \
        py_cache "$ARTURO_BIN/telemetria.py" registra errore "$1.$2" >/dev/null 2>&1
    return 0
}

# Telemetria (bin/telemetria.py): il nome della guardia che ha bloccato, mai il comando.
# Dice dove le persone si fermano e quali guardie danno falsi positivi. Non fallisce mai.
segna_guardia() {
    [[ -f "$ARTURO_BIN/telemetria.py" ]] && py_cache "$ARTURO_BIN/telemetria.py" registra guardia "$1" >/dev/null 2>&1
    return 0
}

# Una guardia ha chiesto conferma: `chiede`, e la chiamata resta in attesa. Se lo strumento parte,
# il PostToolUse registra `confermata` (bin/telemetria.py esito). Il rapporto fra i due dice quali
# guardie chiedono a vuoto. Escono il nome della guardia e l'id della chiamata, mai il comando.
segna_chiede() {
    [[ -f "$ARTURO_BIN/telemetria.py" ]] || return 0
    # L'id della chiamata lo legge già evento_bash.py, insieme al comando (USO_ID).
    [[ -n "$USO_ID" ]] && py_cache "$ARTURO_BIN/telemetria.py" chiede "$1${2:+.$2}" "$USO_ID" >/dev/null 2>&1
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
        ARTURO_REGOLA=1 py_cache "$(guardia_file "$g")" "$@" <<< "$GUARD_INPUT"
    fi
}

run_guard() {
    local out rc regola="" causa="" riserva="$_RISERVA" senza_allow="$_SENZA_ALLOW"
    _RISERVA=""; _SENZA_ALLOW=""
    # ARTURO_REGOLA=1: una guardia che sa nominare la regola che chiede (block-dangerous, commit-secret-gate, e dal 21/11/2026
    # exfil-guard, comms-guard e data-guard) la scrive in
    # una riga "REGOLA: <nome>" dopo il JSON. Si toglie qui, prima di ogni controllo: Claude Code
    # riceve solo il JSON, la telemetria registra <guardia>.<regola> (22/10/2026).
    out=$(lancia_guardia "$@")
    rc=$?
    if [[ $rc -ne 0 && $rc -ne 2 && -n "$riserva" ]]; then
        run_guard "$riserva"
        return 0
    fi
    # Dopo REGOLA commit-secret-gate scrive anche "CAUSA: <nome>", quando la scansione non arriva in fondo
    # (21/11/2026, #5761): parte come `errore`, <guardia>.<causa>. Si toglie prima di REGOLA, che sta sopra.
    if [[ "$out" == *$'\n'"CAUSA: "* ]]; then
        causa=${out##*$'\n'CAUSA: }
        causa=${causa%$'\r'}
        out=${out%$'\n'CAUSA: *}
        out=${out%$'\r'}
        [[ "$causa" =~ ^[a-z0-9-]{1,30}$ ]] || causa=""
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
        [[ -n "$causa" && "$out" == *'"ask"'* ]] && segna_errore "$1" "$causa"
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

# block-dangerous riceve sempre lo stesso comando: se ha già taciuto una volta, non riparte. Dal 21/11/2026
# (#6259) i pattern di git che lo chiamano prima dello skip git-puro sono sei, e `git checkout x` lo lanciava
# due volte.
_BD_FATTO=0
danger_una_volta() {
    [[ $_BD_FATTO -eq 1 ]] && return 0
    _BD_FATTO=1
    run_guard block-dangerous.py
}

# Commit secret gate: PRIMA dello skip git-puro (scansiona il diff, non il message). Parte anche su un nome di
# sottocomando che il pre-filtro non conosce, che può essere un alias di commit (#6259, S10).
vista commit && run_guard commit-secret-gate.py
# Prima di ogni git push il gate scansiona i commit che il remoto non ha ancora (S10).
vista push && run_guard commit-secret-gate.py push

# git clean -f, git branch -D, push, una destinazione riscritta, amend, config, reset, checkout, restore,
# credential, e un programma nascosto con una parola pericolosa (#6323): PRIMA dello skip git-puro, che
# altrimenti lascerebbe passare `git log && git clean -fdx` (17/10/2026, #3506).
vista danger-git && danger_una_volta

# --- Skip git puro (commit, log, show...): i messaggi possono contenere "rm -rf" o "smtplib" come testo, e non
# sono esecuzioni. Il pre-filtro dà `git-puro` solo se ogni programma eseguito è git o cd (forma_comando.py,
# git_puro), senza sostituzioni e senza le opzioni che scrivono o leggono file fuori dal repository. ---
vista git-puro && exit 0

# Opzioni Git che possono cambiare scritture o comportamento non sono testo inerte.
vista git-opzioni && danger_una_volta

# Comms guard: invii email/messaggi esterni (draft-first), giudicati sul codice eseguito.
if vista comms; then
    esporta_ridotto
    run_guard comms-guard.py
fi

# Block dangerous: rm su tree protetti, bw export, scrittura config/hook, fork bomb, segreti, link verso un
# percorso protetto, sessione dentro ~/.claude, .git o una cartella dei segreti...
# Prima le guardie personali di prima-danger; sui comandi che nominano .claude, se il .local ha una
# danger-claude, decide lei e block-dangerous resta come riserva.
if vista danger; then
    for _i in $(locali prima-danger); do run_locale "$_i"; done
    _DC=""; for _i in $(locali danger-claude); do _DC=$_i; break; done
    if [[ -n "$_DC" ]] && vista claude; then
        _RISERVA=block-dangerous.py; _SENZA_ALLOW=1
        run_locale "$_DC"
    else
        danger_una_volta
    fi
fi

# Exfil guard: upload di un file locale verso host esterni -> ask, sul codice eseguito come per comms.
if vista exfil; then
    esporta_ridotto
    run_guard exfil-guard.py
fi

# I canali di rete grezzi (nc, socat, /dev/tcp) passano da exfil-guard, sul codice eseguito. Una redirezione
# verso /dev/tcp si giudica sul comando intero: il pre-filtro tace su `echo`, che lì scrive in rete.
if vista egress; then
    esporta_ridotto
    run_guard exfil-guard.py
elif vista egress-tcp; then
    export COMMS_REDUCED=$GUARD_COMMAND
    run_guard exfil-guard.py
fi

# Data guard: operazioni distruttive sui DATI (SQL drop, volumi, rsync --delete) -> ask.
vista data && run_guard data-guard.py

# GitHub CLI: operazioni distruttive/sensibili (repo delete, secret, api mutante...), anche via api.github.com.
vista gh && run_guard gh-destructive-guard.py

# Guardie personali del punto finale, sui comandi che nominano .claude.
if vista claude; then
    for _i in $(locali finale); do run_locale "$_i"; done
fi

# Ramo memoria e handoff: nessuna guardia ha deciso. Claude Code chiederebbe conferma a ogni
# scrittura via shell sotto ~/.claude, anche per salvare un handoff o una memoria. Qui l'allow
# arriva solo se forma_comando.py ammette il comando: ogni percorso ~/.claude nominato e ogni
# file scritto stanno in data/handoffs/ o in projects/<p>/memory/, i programmi sono di una
# lista breve, e settings, hook e file di unlock non compaiono nel testo eseguito.
# Altrimenti il ramo tace e decide il flusso normale dei permessi.
if vista memoria && py_cache "$ARTURO_HOOKS/forma_comando.py" ramo-memoria <<< "$INPUT" 2>/dev/null; then
    printf '%s\n' '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"allow","permissionDecisionReason":"scrittura di un handoff o di una memoria in ~/.claude: approvata dal ramo memoria del dispatcher"}}'
    exit 0
fi

exit 0
