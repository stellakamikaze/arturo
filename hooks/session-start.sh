#!/bin/bash
# Hook Avvio Sessione - Caricamento Memoria
# Carica il contesto del progetto all'avvio della sessione

# Claude Code legge l'uscita dell'hook in UTF-8. Su Windows python3 scrive in cp1252 quando lo stdout è
# una pipe: la riga DERIVA arrivava con "pu\xf2" al posto di "può" (5/11/2026, #4790).
export PYTHONIOENCODING=utf-8

# Tetto di tempo (#6370, 22/11/2026). Claude Code annulla questo hook dopo 10 secondi e, quando lo annulla,
# butta tutto quello che ha stampato e chiude i processi figli. Su un Windows succedeva in 10 avvii su 11 dal
# 20/11: lo stesso hook dura 4 secondi a macchina ferma e 11 sotto carico. Allora il lavoro lo fa una seconda
# copia di questo file (ARTURO_AVVIO_CORPO=1), e questa ne passa le righe man mano. A 7,5 secondi smette di
# aspettare, dice che mancano avvisi ed esce: le righe già uscite restano. La copia che lavora si ferma alla
# prima riga che scrive dopo, perché nessuno la legge più. Lo stdin, il JSON di Claude Code, lo eredita lei;
# il suo stderr va in session-env/avvio-errori.log, perché un figlio che tiene aperto lo stderr dell'hook
# farebbe aspettare Claude Code fino al timeout. ARTURO_AVVIO_TETTO_MS cambia il tetto (i banchi), 0 lo spegne.
if [ -z "${ARTURO_AVVIO_CORPO:-}" ] && [ "${ARTURO_AVVIO_TETTO_MS:-7500}" != 0 ]; then
  _tetto_ms=${ARTURO_AVVIO_TETTO_MS:-7500}
  case "$_tetto_ms" in (*[!0-9]*|"") _tetto_ms=7500 ;; esac
  _inizio_us=${EPOCHREALTIME//[.,]/}
  mkdir -p "$HOME/.claude/session-env" 2>/dev/null
  # exec: bash 3.2 (macOS) non sostituisce la subshell col comando e la lascia viva con lo stderr dell'hook
  # aperto fino alla fine del lavoro, e Claude Code aspetta (#6454, 23/11/2026).
  exec 3< <(export ARTURO_AVVIO_CORPO=1; exec "$BASH" "${BASH_SOURCE[0]}" 2>"$HOME/.claude/session-env/avvio-errori.log")
  _tagliato=0
  while :; do
    if [ -n "$_inizio_us" ]; then
      _ora_us=${EPOCHREALTIME//[.,]/}
      _resta_ms=$(( _tetto_ms - (_ora_us - _inizio_us) / 1000 ))
      _ms="00$(( _resta_ms % 1000 ))"
      _attesa="$(( _resta_ms / 1000 )).${_ms: -3}"
    else
      # bash 3.2 (macOS): niente EPOCHREALTIME e read -t solo a secondi interi. SECONDS conta a scatti di
      # un secondo, quindi un secondo di margine.
      _resta_ms=$(( _tetto_ms - SECONDS * 1000 - 1000 ))
      _attesa=$(( _resta_ms / 1000 ))
    fi
    if [ "$_resta_ms" -le 0 ] || [ "$_attesa" = 0 ]; then _tagliato=1; break; fi
    _riga=""
    _prima=$SECONDS
    if IFS= read -r -t "$_attesa" _riga <&3; then
      printf '%s\n' "$_riga"
    else
      _rc=$?
      # bash 3.2 esce con 1 sia allo scadere sia a fine flusso: lì lo scadere si riconosce dal tempo passato.
      if [ "$_rc" -gt 128 ] || { [ -z "$_inizio_us" ] && [ $(( SECONDS - _prima )) -ge "$_attesa" ]; }; then
        _tagliato=1
      elif [ -n "$_riga" ]; then
        printf '%s\n' "$_riga"
      fi
      break
    fi
  done
  if [ "$_tagliato" = 1 ]; then
    printf '%s\n' "${_inizio_us:-$SECONDS}" >> "$HOME/.claude/session-env/avvio-tagli.log" 2>/dev/null
    echo "AVVIO: il computer è lento in questo momento e il controllo di avvio si è fermato a $(( _tetto_ms / 1000 )) secondi, prima del limite di Claude Code. Mancano gli avvisi che venivano dopo le righe qui sopra: ripartono alla prossima sessione."
  fi
  exit 0
fi

PROJECT_ROOT="${PWD}"
PROJECT_NAME="$(basename "$PROJECT_ROOT")"   # lo legge personale/session-start.sh, eseguito in fondo

# Il titolo della scheda lo scrive scheda-terminale.py a ogni evento, anche nel Terminale di macOS
# (dal 19/10/2026). Il titolo della finestra via osascript è uscito il 20/10: lo sovrascriveva già il
# primo evento, e osascript poteva far chiedere a macOS il permesso di Automazione (#3587).
mkdir -p "$HOME/.claude/session-env"   # dir gitignored: non esiste su un clone fresco

# Il comando arturo per nome anche nei comandi di Claude (segnalazione n. 33, 29/10/2026): Claude Code
# applica ai comandi Bash della sessione le righe export che un hook di avvio scrive in $CLAUDE_ENV_FILE.
# Una riga sola per file: /clear e la ripresa rilanciano l'avvio.
# ARTURO_CODICE dice dove sta il codice di Arturo: ~/.claude oggi, la cartella del plugin domani
# (docs/strati.md). I comandi scrivono ${ARTURO_CODICE:-$HOME/.claude}/bin/..., mai ~/.claude/bin/...
ARTURO_CODICE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." 2>/dev/null && pwd)"
[ -n "$ARTURO_CODICE" ] || ARTURO_CODICE="$HOME/.claude"
if [ -n "${CLAUDE_ENV_FILE:-}" ] && [ -n "$ARTURO_CODICE" ] && ! grep -qs 'arturo-bin-nel-path' "$CLAUDE_ENV_FILE"; then
  printf 'export ARTURO_CODICE="%s"; export PATH="%s/bin:$PATH"  # arturo-bin-nel-path\n' \
    "$ARTURO_CODICE" "$ARTURO_CODICE" >> "$CLAUDE_ENV_FILE" 2>/dev/null || true
fi
# Le shell in background di una sessione chiusa restano accese: Claude Code non le spegne (24/11/2026, 23 su
# un Mac in 11 giorni). bin/shell-orfane.py chiude quelle senza più una sessione di Claude per padre, e scrive
# cosa ha chiuso in data/logs/shell-orfane.log. Staccata e muta: l'avvio non la aspetta. Su Windows non fa niente.
[ -f "$ARTURO_CODICE/bin/shell-orfane.py" ] && ( python3 "$ARTURO_CODICE/bin/shell-orfane.py" chiudi </dev/null >/dev/null 2>&1 & )
# Una sessione aperta dal demone di `claude --bg` eredita il PATH minimo di launchd
# (/usr/bin:/bin:/usr/sbin:/sbin), senza Homebrew: node, npm e gh sembrano mancare anche se ci sono
# (15/11/2026). Le cartelle che esistono e mancano dal PATH entrano in coda, dopo quelle di sistema,
# per l'avviso su node qui sotto e per i comandi di Claude. ARTURO_PATH_CANDIDATE vuota le spegne (banchi).
AGGIUNTE_PATH=""
_vecchio_ifs="$IFS"; IFS=:
for _d in ${ARTURO_PATH_CANDIDATE-/opt/homebrew/bin:/usr/local/bin:$HOME/.local/bin:$HOME/.local/node/bin}; do
  [ -n "$_d" ] && [ -d "$_d" ] || continue
  case ":$PATH:" in *":$_d:"*) ;; *) AGGIUNTE_PATH="${AGGIUNTE_PATH:+$AGGIUNTE_PATH:}$_d" ;; esac
done
IFS="$_vecchio_ifs"
if [ -n "$AGGIUNTE_PATH" ]; then
  PATH="$PATH:$AGGIUNTE_PATH"
  if [ -n "${CLAUDE_ENV_FILE:-}" ] && ! grep -qs 'arturo-path-completo' "$CLAUDE_ENV_FILE"; then
    printf 'export PATH="$PATH:%s"  # arturo-path-completo\n' "$AGGIUNTE_PATH" >> "$CLAUDE_ENV_FILE" 2>/dev/null || true
  fi
fi
# zsh come bash nei comandi di Claude (segnalazione n. 46, 3/11/2026): un glob senza file, una parola
# che inizia con = e una variabile non quotata fanno come in bash. Prima lo faceva il mod riscrivi-bash
# mettendo `setopt` davanti al comando, e in modalità auto Claude Code respinge un comando cambiato dopo
# la revisione: andava rilanciato identico. Il mod è uscito il 3/11/2026; bash-dispatcher.sh legge il
# marcatore e non blocca più un glob in un'opzione.
# `if ... fi` esce 0 anche in bash, dove la riga non fa niente.
if [ -n "${CLAUDE_ENV_FILE:-}" ] && ! grep -qs 'arturo-zsh-come-bash' "$CLAUDE_ENV_FILE"; then
  printf '%s\n' 'if [ -n "${ZSH_VERSION:-}" ]; then setopt nonomatch noequals shwordsplit; fi  # arturo-zsh-come-bash' \
    >> "$CLAUDE_ENV_FILE" 2>/dev/null || true
fi
# Col plugin il codice sta in una cartella che cambia a ogni versione. La barra in basso la legge da
# ~/.claude/arturo/radice, e il modello la riceve qui: Read non espande $ARTURO_CODICE (docs/prove-plugin.md).
# Il puntatore sta dove lo leggono la barra e il lanciatore di scrape: ${CLAUDE_CONFIG_DIR:-~/.claude} (lotto L10).
ORSA_RADICE="${CLAUDE_CONFIG_DIR:-$HOME/.claude}"
# Una sessione aperta prima di un aggiornamento gira ancora dalla cartella della versione vecchia, e a
# ogni /clear riportava radice indietro (27/11/2026: 0.2.26 installata, radice di nuovo a 0.2.25). radice_si_scrive dice no solo se la radice indicata esiste, sta nella stessa cartella dei
# plugin e ha una versione più nuova. Un clone, una cartella sparita o un nome senza versione si scrivono.
radice_si_scrive() {
  local ora="$1" nuova="$2" a b i x y
  [ -n "$ora" ] && [ -d "$ora" ] || return 0
  [ "$(dirname "$ora")" = "$(dirname "$nuova")" ] || return 0
  a="$(basename "$ora")"; b="$(basename "$nuova")"
  [[ "$a" =~ ^[0-9]+(\.[0-9]+)*$ && "$b" =~ ^[0-9]+(\.[0-9]+)*$ ]] || return 0
  local -a va vb
  IFS=. read -r -a va <<< "$a"
  IFS=. read -r -a vb <<< "$b"
  for ((i = 0; i < ${#va[@]} || i < ${#vb[@]}; i++)); do
    x=$((10#${va[i]:-0})); y=$((10#${vb[i]:-0}))
    [ "$x" -gt "$y" ] && return 1
    [ "$x" -lt "$y" ] && return 0
  done
  return 0
}
if [ "$(cd "$ARTURO_CODICE" 2>/dev/null && pwd -P)" != "$(cd "$ORSA_RADICE" 2>/dev/null && pwd -P)" ]; then
  _radice_ora="$(cat "$ORSA_RADICE/arturo/radice" 2>/dev/null)"
  mkdir -p "$ORSA_RADICE/arturo" 2>/dev/null \
    && { [ "$_radice_ora" = "$ARTURO_CODICE" ] || ! radice_si_scrive "$_radice_ora" "$ARTURO_CODICE" \
         || printf '%s' "$ARTURO_CODICE" > "$ORSA_RADICE/arturo/radice" 2>/dev/null; } || true
  echo "ARTURO: il codice di Arturo sta in $ARTURO_CODICE (\$ARTURO_CODICE nel Bash). Un percorso \$ARTURO_CODICE/... o \${CLAUDE_PLUGIN_ROOT}/... in un testo di Arturo letto con Read si legge da lì."
fi

# Info directory di lavoro e macchina: con piu' computer, Claude sa su quale lavora.
echo "DIRECTORY: $PROJECT_ROOT"
MACCHINA=$(scutil --get ComputerName 2>/dev/null || hostname 2>/dev/null)
[ -n "$MACCHINA" ] && echo "MACCHINA: $MACCHINA"

# Il nome scelto dalla persona per Arturo (bin/nome.py, Fase F3 del piano della catena, #5711): sta
# nell'Orsa, in personale/nome.txt. Senza il file non stampa niente. Anche dopo un compact.
if [ -f "$ORSA_RADICE/personale/nome.txt" ] && [ -f "$ARTURO_CODICE/bin/nome.py" ]; then
  python3 "$ARTURO_CODICE/bin/nome.py" riga 2>/dev/null || true
fi

# La barra in basso (statusline.js) gira con node, e scrive le metriche che legge l'avviso sul contesto
# (context-monitor.py, dentro hub.py post dal 23/11/2026).
# Claude Code si installa anche senza node, e allora restano spenti in silenzio (19/10/2026).
command -v node >/dev/null 2>&1 \
  || echo "NODE: manca node, la barra in basso (contesto e quota) e l'avviso sul contesto sono spenti. Dillo a Claude: installa node da nodejs.org, poi riapri Claude Code."

# Le guardie leggono il comando con python3. `command -v` non basta: su Windows il python3 del
# Microsoft Store esiste ed esce 49 senza eseguire niente. Allora il dispatcher chiede conferma a ogni
# comando, e qui si dice perché (revisione del 10/11/2026, HK-2).
python3 -c '' >/dev/null 2>&1 \
  || echo "PYTHON: manca un python3 che funziona: ogni comando della shell chiede conferma. Dillo a Claude: installa Python da python.org, poi riapri Claude Code."

# Dopo un compact il contesto e' stato riassunto: un riepilogo che la persona puo' controllare,
# poi il lavoro riprende da solo, come nella rotazione (segnalazione n. 100, #6555, 27/11/2026):
# il compact automatico arriva a meta' di un lavoro gia' approvato. Si ferma solo se prima del
# compact la sessione aspettava la persona. SessionStart con source "compact" e' la via
# documentata; lo stdout di PostCompact non entra nel contesto.
# read con tetto di 2 secondi: uno stdin lasciato aperto non deve appendere l'avvio.
HOOK_INPUT=""
[ -t 0 ] || IFS= read -r -t 2 -d '' HOOK_INPUT || true
if printf '%s' "$HOOK_INPUT" | grep -qE '"source"[[:space:]]*:[[:space:]]*"compact"'; then
  echo "COMPACT APPENA AVVENUTO: il riassunto può aver perso dettagli. Riepiloga in poche righe file modificati, comandi di test e build, decisioni, task pendenti e ultimo errore. Poi riprendi da solo il lavoro in corso, come nella rotazione, senza chiedere un via. Ti fermi solo se prima del compact aspettavi una risposta della persona o eri a un freno."
  # Il riassunto può perdere una correzione della persona: torna intera da qui (#4099).
  if [ -f "$ARTURO_CODICE/bin/correzioni.py" ]; then
    printf '%s' "$HOOK_INPUT" | python3 "$ARTURO_CODICE/bin/correzioni.py" blocco 2>/dev/null || true
  fi
fi

# Reminder context management
# La soglia vera viene da bin/rotazione.py (arturo rotazione N, 23/11/2026), che stampa anche, una volta,
# l'avviso della rotazione nuova per chi usava già Arturo. Senza python3 resta la riga di Arturo.
CONTEXT_RIGA=$([ -f "$ARTURO_CODICE/bin/rotazione.py" ] && python3 "$ARTURO_CODICE/bin/rotazione.py" riga 2>/dev/null)
if [ -n "$CONTEXT_RIGA" ]; then
  printf '%s\n' "$CONTEXT_RIGA"
else
  echo "CONTEXT: a compito chiuso con una traccia (commit, file, decisione, todo) Arturo fa commit, push e chiude il todo, poi parte col passo dopo nello stesso contesto. /fine --rotazione parte solo dopo l'avviso CONTEXT WARNING (contesto oltre il 50%) o dalle 18. Il tool ruota (mod rotazione) segue sempre: una domanda alla persona viaggia con la rotazione. Senza il mod, all'avviso il compito si chiude e si salva con /fine."
fi

# La mappa dei ruoli (strati F6, #4536): quale skill fa quale lavoro, dalla riga `ruolo:` delle skill di
# Arturo e dell'Orsa. Senza ruoli la riga non esce.
[ -f "$ARTURO_CODICE/bin/ruoli.py" ] && python3 "$ARTURO_CODICE/bin/ruoli.py" riga 2>/dev/null

# Avvisi Git locali: nessuna rete, nessun comando in background.
if git -C "$PROJECT_ROOT" rev-parse --git-dir >/dev/null 2>&1; then
  CHANGES=$(git -C "$PROJECT_ROOT" status --porcelain 2>/dev/null || true)
  [[ -n "$CHANGES" ]] && echo "GIT: working tree con modifiche non committate"
  REBASE_MERGE=$(git -C "$PROJECT_ROOT" rev-parse --git-path rebase-merge 2>/dev/null)
  REBASE_APPLY=$(git -C "$PROJECT_ROOT" rev-parse --git-path rebase-apply 2>/dev/null)
  if [[ -d "$REBASE_MERGE" || -d "$REBASE_APPLY" ]]; then
    echo "GIT: rebase in corso — risolvilo prima di lavorare"
  fi
fi
# Lo stesso controllo su ~/.claude: un aggiornamento o un /fine fermi a metà rebase lasciano la config
# in uno stato che ogni sessione legge (30/10/2026).
if [[ "$(cd "$PROJECT_ROOT" 2>/dev/null && pwd -P)" != "$(cd "$HOME/.claude" 2>/dev/null && pwd -P)" ]] \
   && git -C "$HOME/.claude" rev-parse --git-dir >/dev/null 2>&1; then
  REBASE_MERGE=$(git -C "$HOME/.claude" rev-parse --git-path rebase-merge 2>/dev/null)
  REBASE_APPLY=$(git -C "$HOME/.claude" rev-parse --git-path rebase-apply 2>/dev/null)
  case "$REBASE_MERGE" in /*|?:*) ;; *) REBASE_MERGE="$HOME/.claude/$REBASE_MERGE" ;; esac
  case "$REBASE_APPLY" in /*|?:*) ;; *) REBASE_APPLY="$HOME/.claude/$REBASE_APPLY" ;; esac
  if [[ -d "$REBASE_MERGE" || -d "$REBASE_APPLY" ]]; then
    echo "CONFIG: ~/.claude è a metà rebase — chiudilo (git -C ~/.claude status) prima di lavorare"
  fi
fi

# Guardia anti-divergenza config (~/.claude vs origin/main).
# Il confronto legge gli oggetti Git gia' presenti in locale: senza un fetch resta fermo a
# quello che sapeva l'ultima volta, e chi non lancia mai /inizio non vedrebbe mai un
# aggiornamento. Per questo il fetch parte qui, in background e al massimo ogni 6 ore, cosi'
# l'avvio non aspetta la rete. L'avviso di questa sessione usa il fetch della volta prima.
# Config integra: un settings.json rotto spegne tutte le guardie senza avvisare.
# L'esito passa a deriva.py più sotto, che prima rifaceva gli stessi sei git (#6370): solo con un'uscita
# 0 o 1, cioè un controllo arrivato in fondo.
CONFIG_ESITO=""
if [ -f "$ARTURO_CODICE/hooks/controlla-config.py" ]; then
  CONFIG_RIGHE=$(python3 "$ARTURO_CODICE/hooks/controlla-config.py" --quiet "$HOME/.claude" 2>/dev/null)
  case $? in 0|1) CONFIG_ESITO=fatto ;; esac
  [ -n "$CONFIG_RIGHE" ] && printf '%s\n' "$CONFIG_RIGHE"
fi
if git -C "$HOME/.claude" rev-parse --git-dir >/dev/null 2>&1 && ! git -C "$HOME/.claude" symbolic-ref -q HEAD >/dev/null 2>&1; then
  echo "CONFIG: ~/.claude non sta su un branch (HEAD scollegato): i commit di /fine non finirebbero su main. Chiedi a Claude di riportarla su main."
fi
# File della config cambiati e non salvati in git: lavoro di un'altra sessione o rimasto da
# ieri. I file nuovi non contano: molti sono dati locali che git ignora o non deve vedere. Non
# contano neanche gli archivi della persona, che non fermano l'aggiornamento (bin/aggiorna-applica.sh).
if git -C "$HOME/.claude" rev-parse --git-dir >/dev/null 2>&1; then
  SPORCHI=$(git -C "$HOME/.claude" status --porcelain --untracked-files=no -- . ':!data/handoffs' ':!data/todo' ':!data/memory' 2>/dev/null | wc -l | tr -d ' ')
  if [ "${SPORCHI:-0}" -gt 0 ]; then
    echo "CONFIG: $SPORCHI file di ~/.claude modificati e non salvati in git (lavoro di un'altra sessione o rimasto da ieri). Chiedi a Claude cosa sono prima di aggiornare."
  fi
fi

# Banchi delle guardie (tests/banchi-avvio.sh). Se l'esito ha piu' di 12 ore, i banchi ripartono in
# background e il risultato lo legge la sessione dopo: l'avvio non aspetta. Dal 3/11/2026 un rosso non
# si dice alla persona (chi mantiene Arturo: "molto invasiva e non mi serve a niente saperlo"): banchi-avvio.sh lo
# manda da solo a chi mantiene Arturo, con la telemetria, e un rosso con piu' di 30 minuti fa ripartire
# subito i banchi, cosi' un rosso intermittente si cancella da solo. Il lock e' una cartella, perche' mkdir e' atomico anche dove flock non
# c'e' (macOS, Git Bash): due sessioni che partono insieme non lo prendono entrambe. Dentro c'e'
# il PID di chi lo tiene; un lock col PID morto (kill -9, riavvio) e' orfano e si riprende,
# altrimenti un solo processo ucciso male spegnerebbe i banchi per sempre.
# Solo in un'installazione vera (~/.claude e' un repository git); ARTURO_BANCHI_AVVIO=0 li spegne.
BANCHI_ESITO="$HOME/.claude/cache/banchi-ultimo-esito.txt"
BANCHI_RILANCIO=0
if [ -f "$BANCHI_ESITO" ] && [ "$(sed -n '1p' "$BANCHI_ESITO" 2>/dev/null)" = "ROSSO" ] \
   && [ -n "$(find "$BANCHI_ESITO" -mmin +30 2>/dev/null)" ]; then
  BANCHI_RILANCIO=1
fi
if [ "${ARTURO_BANCHI_AVVIO:-1}" != "0" ] && [ -f "$HOME/.claude/tests/banchi-avvio.sh" ] \
   && git -C "$HOME/.claude" rev-parse --git-dir >/dev/null 2>&1; then
  if [ ! -f "$BANCHI_ESITO" ] || [ "$BANCHI_RILANCIO" = 1 ] || [ -n "$(find "$BANCHI_ESITO" -mmin +720 2>/dev/null)" ]; then
    BANCHI_LOCK="$HOME/.claude/cache/banchi.lock"
    mkdir -p "$HOME/.claude/cache" 2>/dev/null
    if [ -d "$BANCHI_LOCK" ]; then
      TENUTO_DA=$(cat "$BANCHI_LOCK/pid" 2>/dev/null)
      if [ -z "$TENUTO_DA" ] || ! kill -0 "$TENUTO_DA" 2>/dev/null; then
        rm -rf "$BANCHI_LOCK" 2>/dev/null
      fi
    fi
    if mkdir "$BANCHI_LOCK" 2>/dev/null; then
      (
        # Il PID di questa subshell: in bash 3.2 $BASHPID non esiste e $$ e' lo script, che
        # esce subito. `sh -c 'echo $PPID'` stampa il PID di chi lo chiama, su ogni bash.
        sh -c 'echo $PPID' > "$BANCHI_LOCK/pid" 2>/dev/null
        trap 'rm -rf "$BANCHI_LOCK"' EXIT
        # Di notte macOS sospende i processi in background: caffeinate li tiene svegli.
        SVEGLIO=""
        command -v caffeinate >/dev/null 2>&1 && SVEGLIO="caffeinate -i"
        $SVEGLIO bash "$HOME/.claude/tests/banchi-avvio.sh"
      ) >/dev/null 2>&1 &
    fi
  fi
fi

if git -C "$HOME/.claude" rev-parse --git-dir >/dev/null 2>&1; then
  MARCATORE="$HOME/.claude/session-env/ultimo-fetch"            # ultimo tentativo
  RIUSCITO="$HOME/.claude/session-env/ultimo-fetch-riuscito"     # ultimo fetch riuscito
  PRIMO="$HOME/.claude/session-env/primo-fetch-tentato"          # primo tentativo senza un riuscito
  ADESSO=$(date +%s)
  SCORSO=$(cat "$MARCATORE" 2>/dev/null || echo 0)
  case "$SCORSO" in (*[!0-9]*|"") SCORSO=0 ;; esac
  RIUSCITO_T=$(cat "$RIUSCITO" 2>/dev/null || echo 0)
  case "$RIUSCITO_T" in (*[!0-9]*|"") RIUSCITO_T=0 ;; esac
  # Un fetch riuscito vale 6 ore. Un tentativo senza esito vale 30 minuti: fino al 22/11/2026 il marcatore
  # del tentativo fermava i nuovi per 6 ore anche quando il fetch era morto con l'hook (#6370). I 30
  # minuti bastano a un fetch lento per finire senza che ne parta un secondo.
  if [ $((ADESSO - RIUSCITO_T)) -gt 21600 ] && [ $((ADESSO - SCORSO)) -gt 1800 ]; then
    mkdir -p "$HOME/.claude/session-env" 2>/dev/null
    printf '%s' "$ADESSO" > "$MARCATORE" 2>/dev/null
    [ "$RIUSCITO_T" -gt 0 ] || [ -s "$PRIMO" ] || printf '%s' "$ADESSO" > "$PRIMO" 2>/dev/null
    # Il fetch lo fa hooks/avvio-fetch.py, staccato: il processo che lavora non ha più l'hook per padre,
    # e Claude Code su Windows non lo chiude con l'albero dell'hook. Lì il fetch dura fino a 35 secondi.
    # Il marcatore di successo si scrive solo se il fetch riesce davvero. Senza il file o senza un
    # python3 che parte vale il fetch in background di bash.
    if ! { [ -f "$ARTURO_CODICE/hooks/avvio-fetch.py" ] \
           && python3 "$ARTURO_CODICE/hooks/avvio-fetch.py" stacca "$HOME/.claude" "$ADESSO" "$RIUSCITO" >/dev/null 2>&1; }; then
      # GIT_TERMINAL_PROMPT=0: un repository che chiede le credenziali non deve mai appendere
      # l'avvio della sessione.
      # BatchMode: una chiave SSH con passphrase o un host sconosciuto non chiedono niente.
      # ConnectTimeout, ServerAlive e lowSpeed: un server che accetta e non risponde non lascia un fetch appeso
      # per sempre, uno in più a ogni tentativo (review del 9/11/2026, lotto L10).
      ( export GIT_TERMINAL_PROMPT=0 GIT_SSH_COMMAND="ssh -o BatchMode=yes -o ConnectTimeout=10 -o ServerAliveInterval=15 -o ServerAliveCountMax=2"
        LENTO=(-c http.lowSpeedLimit=1000 -c http.lowSpeedTime=30)
        REMOTO=$(git -C "$HOME/.claude" remote get-url upstream >/dev/null 2>&1 && echo upstream || echo origin)
        git -C "$HOME/.claude" "${LENTO[@]}" fetch --quiet --tags "$REMOTO" main >/dev/null 2>&1 && printf '%s' "$ADESSO" > "$RIUSCITO"
        # Con upstream, origin è il repository privato di chi usa: senza questo fetch il BEHIND qui
        # sotto, che confronta con origin/main, restava fermo e il lavoro di un'altra macchina non si
        # vedeva più (30/10/2026).
        [ "$REMOTO" = upstream ] && git -C "$HOME/.claude" "${LENTO[@]}" fetch --quiet origin main >/dev/null 2>&1
      ) >/dev/null 2>&1 &
    fi
  fi
  # I 7 giorni contano dall'ultimo fetch riuscito, o dal primo tentativo se non ne è mai riuscito uno:
  # fino al 22/11/2026 l'avviso taceva per sempre su un computer dove il fetch non era mai riuscito (#6370).
  DA_T="$RIUSCITO_T"
  if [ "$DA_T" -eq 0 ]; then
    DA_T=$(cat "$PRIMO" 2>/dev/null || echo 0)
    case "$DA_T" in (*[!0-9]*|"") DA_T=0 ;; esac
  fi
  if [ "$DA_T" -gt 0 ] && [ $((ADESSO - DA_T)) -gt 604800 ]; then
    echo "ARTURO: da piu' di 7 giorni non riesco a controllare gli aggiornamenti (rete, proxy o credenziali). Prova /aggiorna per vedere l'errore."
  fi
  AHEAD=$(git -C "$HOME/.claude" rev-list --count origin/main..HEAD 2>/dev/null || echo 0)
  BEHIND=$(git -C "$HOME/.claude" rev-list --count HEAD..origin/main 2>/dev/null || echo 0)
  # Se origin e' il repo originale di Arturo, chi usa non puo' pusharci: commit locali
  # "avanti" sono normali e l'avviso sarebbe solo rumore. Tace solo in quel caso.
  ORIGIN_URL=$(git -C "$HOME/.claude" remote get-url origin 2>/dev/null || echo "")
  case "$ORIGIN_URL" in
    https://github.com/stellakamikaze/arturo | https://github.com/stellakamikaze/arturo.git | \
    git@github.com:stellakamikaze/arturo | git@github.com:stellakamikaze/arturo.git | \
    ssh://git@github.com/stellakamikaze/arturo | ssh://git@github.com/stellakamikaze/arturo.git)
      ORIGIN_ARTURO=1 ;;
    *)
      ORIGIN_ARTURO=0 ;;
  esac
  if [ "${AHEAD:-0}" -gt 0 ] && [ "$ORIGIN_ARTURO" -eq 0 ]; then
    echo "CONFIG: ~/.claude e' AVANTI di $AHEAD commit non pushati"
  fi
  # Gli aggiornamenti di Arturo (bin/aggiornamenti.py, 16/10/2026): si installano da soli alla
  # chiusura, solo i rilasci con tag firmati. Qui, senza rete, l'annuncio una volta, l'esito
  # dell'ultima installazione e l'avviso se uno non può installarsi da solo.
  if [ -f "$ARTURO_CODICE/bin/aggiornamenti.py" ]; then
    # ARTURO_BASH: un rinvio si installa da qui, staccato, col bash di questo hook (3/11/2026).
    # ARTURO_AVVIO: il "source" dell'hook. Il rinvio si installa solo con "startup", mai dopo /clear,
    # /compact o una ripresa, col processo di prima vivo (#4732, 4/11/2026).
    ARTURO_AVVIO="$(printf '%s' "$HOOK_INPUT" | sed -n 's/.*"source"[[:space:]]*:[[:space:]]*"\([a-z]*\)".*/\1/p' | head -n 1)"
    ARTURO_AVVIO="$ARTURO_AVVIO" ARTURO_BASH="$BASH" python3 "$ARTURO_CODICE/bin/aggiornamenti.py" stato 2>/dev/null || true
  elif [ "${BEHIND:-0}" -gt 0 ]; then
    # Senza la verifica della firma /aggiorna non applica niente (17/10/2026, #3504): main non si applica mai.
    echo "ARTURO: manca bin/aggiornamenti.py, che verifica la firma dei rilasci: finche' non torna, nessun aggiornamento si installa. Si rimette con: git -C ~/.claude restore bin/aggiornamenti.py"
  fi
elif [ -f "$ARTURO_CODICE/bin/aggiornamenti.py" ] && [ ! -e "$ARTURO_CODICE/.git" ]; then
  # Col plugin ~/.claude di solito non è un repository, e l'avvio deve dire lo stesso che c'è un rilascio
  # nuovo (#4897, 6/11/2026). Senza .git accanto al codice gira solo il ramo del plugin di aggiornamenti.py.
  # ARTURO_SESSIONE: l'id della sessione, per il segno della versione che la barra confronta con quella installata.
  ARTURO_SESSIONE="$(printf '%s' "$HOOK_INPUT" | sed -n 's/.*"session_id"[[:space:]]*:[[:space:]]*"\([A-Za-z0-9_-]*\)".*/\1/p' | head -n 1)" \
    python3 "$ARTURO_CODICE/bin/aggiornamenti.py" stato 2>/dev/null || true
fi

# Canale novità: se NOVITA.md ha una entry più recente dell'ultima vista, segnala.
# Solo un avviso — il racconto lo fa /novita, mai in automatico.
# Una copia di prova di /aggiorna o del sync rimasta in attesa con un conflitto (bin/aggiorna-applica.sh):
# finché aspetta, il sync fra le macchine e gli aggiornamenti non ripartono.
ATTESA=$(git -C "$HOME/.claude" rev-parse --git-path arturo-aggiorna-copia 2>/dev/null)
case "$ATTESA" in /*) ;; ?*) ATTESA="$HOME/.claude/$ATTESA" ;; esac
# Il percorso della copia può avere spazi (una HOME "Mario Rossi"): il registro si legge da destra.
A_RIGA=$([ -n "$ATTESA" ] && [ -f "$ATTESA" ] && head -1 "$ATTESA" | tr -d '\r')
A_COPIA=$(printf '%s\n' "$A_RIGA" | sed -E 's/ [0-9a-f]{40,64}( [a-z]+ [^ ]+)?$//')
A_MODO=$(printf '%s\n' "$A_RIGA" | awk 'NF >= 4 { print $(NF-1) }')
A_NATA=$(printf '%s\n' "$A_RIGA" | awk 'NF >= 4 { print $NF }')
if [ -n "$A_COPIA" ] && [ -d "$A_COPIA" ]; then
  echo "ARTURO: una copia di prova con un conflitto aspetta${A_NATA:+ dal ${A_NATA/_/ alle }} ($([ "$A_MODO" = sync ] && echo "sync fra le tue macchine" || echo "aggiornamento")): finché aspetta, sync e aggiornamenti sono fermi. /aggiorna la conclude o la scarta."
fi

# Col plugin NOVITA.md sta accanto al codice, non in ~/.claude.
NOVITA_FILE="$HOME/.claude/NOVITA.md"
[ -f "$NOVITA_FILE" ] || NOVITA_FILE="$ARTURO_CODICE/NOVITA.md"
if [ -f "$NOVITA_FILE" ]; then
  ULTIMA_NOVITA=$(grep -m1 '^## ' "$NOVITA_FILE" 2>/dev/null | grep -oE '[0-9]{4}-[0-9]{2}-[0-9]{2}')
  # Segnalibro per intestazione (novita-viste: data e titolo); un vecchio novita-vista
  # con una sola data vale come "viste fino a".
  NOVITA_VISTE="$HOME/.claude/session-env/novita-viste"
  NOVITA_VECCHIA=$(cat "$HOME/.claude/session-env/novita-vista" 2>/dev/null || echo "")
  # Chi installa adesso parte da qui: la storia di Arturo non è una lista di cose da leggere.
  if [ ! -e "$NOVITA_VISTE" ] && [ -z "$NOVITA_VECCHIA" ] && [ ! -f "$HOME/.claude/data/setup-fatto" ]; then
    mkdir -p "$HOME/.claude/session-env" 2>/dev/null
    grep '^## ' "$NOVITA_FILE" 2>/dev/null | sed 's/^## //' > "$NOVITA_VISTE" 2>/dev/null
  fi
  # Un passaggio solo: un processo per voce costava quasi un secondo a ogni avvio, e cresceva coi rilasci.
  NON_VISTE=$(awk -v viste="$NOVITA_VISTE" -v vecchia="$NOVITA_VECCHIA" '
    BEGIN { while ((getline riga < viste) > 0) vista[riga] = 1 }
    /^## / {
      voce = substr($0, 4); sub(/\r$/, "", voce)
      data = (voce ~ /^[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]/) ? substr(voce, 1, 10) : ""
      if (vecchia != "" && data != "" && (data "") <= (vecchia "")) next
      if (!(voce in vista)) n++
    }
    END { print n + 0 }' "$NOVITA_FILE" 2>/dev/null)
  if [ "${NON_VISTE:-0}" -gt 0 ]; then
    echo "NOVITA': $NON_VISTE aggiornamenti dell'harness non ancora letti (ultimo: $ULTIMA_NOVITA) — digita /novita per fartelo raccontare"
  fi
fi

# Auto-load selettivo memory (just-in-time: mostra indice, non carica contenuti)
if [ -x /usr/bin/python3 ] || command -v python3 >/dev/null 2>&1; then
    python3 "$ARTURO_CODICE/hooks/memory-autoload.py" 2>/dev/null || true
fi

# Deriva (hooks/deriva.py): file e hook di Arturo cambiati o spenti, config rotta. Una riga solo se
# c'è da fare; registra per la telemetria l'elenco quando cambia. Prima dell'avvio della telemetria,
# così una config rotta parte con l'invio di questa sessione.
if [ -f "$ARTURO_CODICE/hooks/deriva.py" ]; then
  if [ "$CONFIG_ESITO" = fatto ]; then
    ARTURO_CONFIG_CONTROLLATA=1 ARTURO_CONFIG_RIGHE="$CONFIG_RIGHE" \
      python3 "$ARTURO_CODICE/hooks/deriva.py" "$HOME/.claude" 2>/dev/null || true
  else
    python3 "$ARTURO_CODICE/hooks/deriva.py" "$HOME/.claude" 2>/dev/null || true
  fi
fi

# Chi ha ancora il clone in ~/.claude (strati F4, 5/11/2026): una riga al giorno su come passare al plugin.
# Col plugin migra.py non stampa niente.
if [ -f "$ARTURO_CODICE/bin/migra.py" ]; then
  python3 "$ARTURO_CODICE/bin/migra.py" avviso 2>/dev/null || true
fi

# Telemetria (bin/telemetria.py): registra la sessione senza rete, avvisa la persona una
# volta sola e lancia l'invio in background al massimo ogni 6 ore. Non ferma mai l'avvio.
if [ -f "$ARTURO_CODICE/bin/telemetria.py" ]; then
  python3 "$ARTURO_CODICE/bin/telemetria.py" avvio 2>/dev/null || true
fi

# Invito a finire /setup (23/10/2026): nella telemetria una persona ha installato e non l'ha mai lanciato,
# un'altra si è fermata prima della fase 9. Una volta al giorno, solo in un'installazione vera senza il
# segno di data/setup-fatto. Il segno c'è dal 16/10: chi ha installato prima (data del clone nel reflog,
# o reflog vuoto perché scaduto) poteva aver finito senza segno, e lì non si chiede. Gli aggiornamenti
# non contano: arrivano anche da soli, a chi /setup non l'ha mai aperto.
NATA_SETUP=$(git -C "$HOME/.claude" reflog show --date=short --format=%gd HEAD 2>/dev/null | tail -1)
NATA_SETUP=${NATA_SETUP#HEAD@\{}
NATA_SETUP=${NATA_SETUP%\}}
if [ -d "$HOME/.claude/.git" ] && [ ! -f "$HOME/.claude/data/setup-fatto" ] \
  && [[ "$NATA_SETUP" > "2026-10-15" ]]; then
  OGGI_SETUP=$(date +%Y-%m-%d)
  if [ "$(cat "$HOME/.claude/session-env/setup-invito" 2>/dev/null)" != "$OGGI_SETUP" ]; then
    mkdir -p "$HOME/.claude/session-env" && printf '%s\n' "$OGGI_SETUP" > "$HOME/.claude/session-env/setup-invito"
    # /setup scrive in session-env/setup-fase il numero dell'ultima fase finita (1/11/2026). Entra nella
    # riga solo un numero di fase valido, come la telemetria: il file non porta testo nel contesto.
    FASE_SETUP=$(head -c 8 "$HOME/.claude/session-env/setup-fase" 2>/dev/null | tr -d '[:space:]')
    case "$FASE_SETUP" in
      10|[0-9]|[0-9][a-z]) RIPRESA_SETUP=" (ultima fase finita: $FASE_SETUP, proponi di ripartire dalla fase dopo)" ;;
      *) RIPRESA_SETUP="" ;;
    esac
    echo "SETUP: la prima configurazione di Arturo non è finita$RIPRESA_SETUP. Nella tua prima risposta dillo alla persona in una riga e proponi di scrivere /setup, che la guida una cosa per volta. Poi fai quello che chiede, e se dice di no non insistere: l'invito torna domani."
  fi
fi
# Col plugin l'invito non partiva mai: ~/.claude non è il repository di Arturo (review del 10/11/2026, #5266).
# Un plugin non porta permessi, regole di blocco e barra: li unisce /setup, che scrive il file di blocco
# data/arturo-impostazioni.lock. Senza blocco e senza setup-fatto l'invito esce, una volta al giorno.
if [ "$(cd "$ARTURO_CODICE" 2>/dev/null && pwd -P)" != "$(cd "$ORSA_RADICE" 2>/dev/null && pwd -P)" ] \
  && [ -f "$ARTURO_CODICE/.claude-plugin/plugin.json" ] \
  && [ ! -f "$ORSA_RADICE/data/arturo-impostazioni.lock" ] && [ ! -f "$ORSA_RADICE/data/setup-fatto" ]; then
  OGGI_SETUP=$(date +%Y-%m-%d)
  if [ "$(cat "$ORSA_RADICE/session-env/setup-invito" 2>/dev/null)" != "$OGGI_SETUP" ]; then
    mkdir -p "$ORSA_RADICE/session-env" && printf '%s\n' "$OGGI_SETUP" > "$ORSA_RADICE/session-env/setup-invito"
    echo "SETUP: Arturo è installato come plugin, ma i suoi permessi, le regole di blocco e la barra in basso non sono ancora nelle impostazioni di Claude Code: un plugin non li porta. Nella tua prima risposta dillo alla persona in una riga e proponi di scrivere /setup, che li applica e guida il resto una cosa per volta. Poi fai quello che chiede, e se dice di no non insistere: l'invito torna domani."
  fi
fi

# Segnalazioni (11/11/2026): di default Claude le scrive e le manda da solo a chi mantiene Arturo, e dice cosa è
# partito. L'avviso esce una volta sola (arturo segnala avviso, segno in session-env/segnalazioni-annuncio). Con
# "arturo segnalazioni manuali" o ARTURO_SEGNALAZIONI=manuali torna l'invito a proporre /segnala. "arturo segnala
# basta" spegne la riga (stato in session-env/segnala.json). Il modo che vale lo decide comunque `manda`.
SEGNALA_STATO="$HOME/.claude/session-env/segnala.json"
if ! grep -q '"pausa": "sempre"' "$SEGNALA_STATO" 2>/dev/null; then
  if [ "$(printf '%s' "${ARTURO_SEGNALAZIONI:-}" | tr '[:upper:]' '[:lower:]')" = "manuali" ] \
    || grep -q '"modo": "manuali"' "$SEGNALA_STATO" 2>/dev/null; then
    echo "SEGNALA: quando qualcosa di Arturo o di Claude Code si inceppa, la persona corregge un tuo comportamento o chiede una cosa che Arturo non sa fare, proponi una volta /segnala, con la bozza già scritta e --origine avvio in prepara. Vale per Arturo, non per i bug del progetto della persona."
  else
    [ -f "$HOME/.claude/session-env/segnalazioni-annuncio" ] \
      || python3 "$ARTURO_CODICE/bin/arturo" segnala avviso 2>/dev/null || true
    echo "SEGNALA: quando qualcosa di Arturo o di Claude Code si inceppa, la persona corregge un tuo comportamento o chiede una cosa che Arturo non sa fare, la segnalazione parte da sola: scrivi la bozza, mandala con manda e --origine avvio, poi di' alla persona in una riga cosa è partito, il numero e come ritirarla. Una volta per fatto, per Arturo e non per i bug del progetto della persona. Un tema di sicurezza segue SECURITY.md e non parte da solo."
  fi
fi

# Nel Terminale di macOS il profilo accoda al titolo della scheda processo e cartella: la prima
# sessione lo sistema una volta per tutte (bin/schede_mac.py, 29/10/2026). Il segno si controlla qui,
# così le sessioni dopo non avviano Python. La riga SCHEDE: dice alla persona cosa è cambiato. Sta in fondo,
# prima delle aggiunte della persona: se il timeout di 10 secondi lo ferma, il resto dell'avvio è già uscito.
if [ "$TERM_PROGRAM" = "Apple_Terminal" ] && [ -f "$ARTURO_CODICE/bin/schede_mac.py" ] \
   && ! grep -q '"fatto": true' "$HOME/.claude/data/schede-terminale.json" 2>/dev/null; then
  python3 "$ARTURO_CODICE/bin/arturo" schede applica --una-volta 2>/dev/null
fi

# Le aggiunte della persona (personale/session-start.sh, 16/10/2026): gli aggiornamenti di Arturo non le
# toccano, e /aggiorna ci sposta da solo le righe aggiunte a questo file. Girano in una subshell
# alla fine, con le variabili di qui: un loro errore non ferma la sessione.
if [ -f "$HOME/.claude/personale/session-start.sh" ]; then
  ( . "$HOME/.claude/personale/session-start.sh" ) || true
fi
