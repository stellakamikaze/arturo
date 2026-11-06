#!/bin/bash
# Hook Avvio Sessione - Caricamento Memoria
# Carica il contesto del progetto all'avvio della sessione

# Claude Code legge l'uscita dell'hook in UTF-8. Su Windows python3 scrive in cp1252 quando lo stdout è
# una pipe: la riga DERIVA arrivava con "pu\xf2" al posto di "può" (5/11/2026, #4790).
export PYTHONIOENCODING=utf-8

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
# ~/.claude/arturo/radice, e il modello la riceve qui: Read non espande $ARTURO_CODICE (docs/strati.md).
if [ "$(cd "$ARTURO_CODICE" 2>/dev/null && pwd -P)" != "$(cd "$HOME/.claude" 2>/dev/null && pwd -P)" ]; then
  mkdir -p "$HOME/.claude/arturo" 2>/dev/null \
    && { [ "$(cat "$HOME/.claude/arturo/radice" 2>/dev/null)" = "$ARTURO_CODICE" ] \
         || printf '%s' "$ARTURO_CODICE" > "$HOME/.claude/arturo/radice" 2>/dev/null; } || true
  echo "ARTURO: il codice di Arturo sta in $ARTURO_CODICE (\$ARTURO_CODICE nel Bash). Un percorso \$ARTURO_CODICE/... in un testo di Arturo si legge da lì."
fi

# Info directory di lavoro e macchina: con piu' computer, Claude sa su quale lavora.
echo "DIRECTORY: $PROJECT_ROOT"
MACCHINA=$(scutil --get ComputerName 2>/dev/null || hostname 2>/dev/null)
[ -n "$MACCHINA" ] && echo "MACCHINA: $MACCHINA"

# La barra in basso (statusline.js) e l'avviso sul contesto (context-monitor.js) girano con node.
# Claude Code si installa anche senza node, e allora restano spenti in silenzio (19/10/2026).
command -v node >/dev/null 2>&1 \
  || echo "NODE: manca node, la barra in basso (contesto e quota) e l'avviso sul contesto sono spenti. Dillo a Claude: installa node da nodejs.org, poi riapri Claude Code."

# Dopo un compact il contesto e' stato riassunto: prima di continuare, un riepilogo che
# l'utente puo' controllare. SessionStart con source "compact" e' la via documentata;
# lo stdout di PostCompact non entra nel contesto.
# read con tetto di 2 secondi: uno stdin lasciato aperto non deve appendere l'avvio.
HOOK_INPUT=""
[ -t 0 ] || IFS= read -r -t 2 -d '' HOOK_INPUT || true
if printf '%s' "$HOOK_INPUT" | grep -qE '"source"[[:space:]]*:[[:space:]]*"compact"'; then
  echo "COMPACT APPENA AVVENUTO: fermati. Riepiloga all'utente file modificati, comandi di test e build, decisioni, task pendenti e ultimo errore. Poi aspetta la sua conferma prima di continuare."
  # Il riassunto può perdere una correzione della persona: torna intera da qui (#4099).
  if [ -f "$ARTURO_CODICE/bin/correzioni.py" ]; then
    printf '%s' "$HOOK_INPUT" | python3 "$ARTURO_CODICE/bin/correzioni.py" blocco 2>/dev/null || true
  fi
fi

# Reminder context management
echo "CONTEXT: a ogni compito chiuso con una traccia (commit, file, decisione, todo) lancia /fine --rotazione, sempre, anche col contesto leggero; poi il tool ruota (mod rotazione) solo se il passo dopo è tuo. Senza il mod, al ~65% completa il task e salva con /fine"

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
if [ -f "$ARTURO_CODICE/hooks/controlla-config.py" ]; then
  python3 "$ARTURO_CODICE/hooks/controlla-config.py" --quiet "$HOME/.claude" 2>/dev/null
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
# si dice alla persona (Federico: "molto invasiva e non mi serve a niente saperlo"): banchi-avvio.sh lo
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
  MARCATORE="$HOME/.claude/session-env/ultimo-fetch"
  RIUSCITO="$HOME/.claude/session-env/ultimo-fetch-riuscito"
  ADESSO=$(date +%s)
  SCORSO=$(cat "$MARCATORE" 2>/dev/null || echo 0)
  case "$SCORSO" in (*[!0-9]*|"") SCORSO=0 ;; esac
  if [ $((ADESSO - SCORSO)) -gt 21600 ]; then
    mkdir -p "$HOME/.claude/session-env" 2>/dev/null
    printf '%s' "$ADESSO" > "$MARCATORE" 2>/dev/null
    # GIT_TERMINAL_PROMPT=0: un repository che chiede le credenziali non deve mai appendere
    # l'avvio della sessione.
    # BatchMode: una chiave SSH con passphrase o un host sconosciuto non chiedono niente.
    # Il marcatore di successo si scrive solo se il fetch riesce davvero.
    ( export GIT_TERMINAL_PROMPT=0 GIT_SSH_COMMAND="ssh -o BatchMode=yes"
      REMOTO=$(git -C "$HOME/.claude" remote get-url upstream >/dev/null 2>&1 && echo upstream || echo origin)
      git -C "$HOME/.claude" fetch --quiet --tags "$REMOTO" main >/dev/null 2>&1 && printf '%s' "$ADESSO" > "$RIUSCITO"
      # Con upstream, origin è il repository privato di chi usa: senza questo fetch il BEHIND qui
      # sotto, che confronta con origin/main, restava fermo e il lavoro di un'altra macchina non si
      # vedeva più (30/10/2026).
      [ "$REMOTO" = upstream ] && git -C "$HOME/.claude" fetch --quiet origin main >/dev/null 2>&1
    ) >/dev/null 2>&1 &
  fi
  RIUSCITO_T=$(cat "$RIUSCITO" 2>/dev/null || echo 0)
  case "$RIUSCITO_T" in (*[!0-9]*|"") RIUSCITO_T=0 ;; esac
  if [ "$RIUSCITO_T" -gt 0 ] && [ $((ADESSO - RIUSCITO_T)) -gt 604800 ]; then
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
  python3 "$ARTURO_CODICE/bin/aggiornamenti.py" stato 2>/dev/null || true
fi

# Canale novità: se NOVITA.md ha una entry più recente dell'ultima vista, segnala.
# Solo un avviso — il racconto lo fa /novita, mai in automatico.
# Una copia di prova di /aggiorna o del sync rimasta in attesa con un conflitto (bin/aggiorna-applica.sh):
# finché aspetta, il sync fra le macchine e gli aggiornamenti non ripartono.
ATTESA=$(git -C "$HOME/.claude" rev-parse --git-path arturo-aggiorna-copia 2>/dev/null)
case "$ATTESA" in /*) ;; ?*) ATTESA="$HOME/.claude/$ATTESA" ;; esac
if [ -n "$ATTESA" ] && [ -f "$ATTESA" ] && read -r A_COPIA _ A_MODO A_NATA _ < "$ATTESA" && [ -d "$A_COPIA" ]; then
  echo "ARTURO: una copia di prova con un conflitto aspetta${A_NATA:+ dal ${A_NATA/_/ alle }} ($([ "$A_MODO" = sync ] && echo "sync fra le tue macchine" || echo "aggiornamento")): finché aspetta, sync e aggiornamenti sono fermi. /aggiorna la conclude o la scarta."
fi

if [ -f "$HOME/.claude/NOVITA.md" ]; then
  ULTIMA_NOVITA=$(grep -m1 '^## ' "$HOME/.claude/NOVITA.md" 2>/dev/null | grep -oE '[0-9]{4}-[0-9]{2}-[0-9]{2}')
  # Segnalibro per intestazione (novita-viste: data e titolo); un vecchio novita-vista
  # con una sola data vale come "viste fino a".
  NOVITA_VISTE="$HOME/.claude/session-env/novita-viste"
  NOVITA_VECCHIA=$(cat "$HOME/.claude/session-env/novita-vista" 2>/dev/null || echo "")
  NON_VISTE=0
  while IFS= read -r ENTRY; do
    [ -z "$ENTRY" ] && continue
    DATA=$(printf '%s' "$ENTRY" | grep -oE '^[0-9]{4}-[0-9]{2}-[0-9]{2}')
    [ -n "$NOVITA_VECCHIA" ] && [ -n "$DATA" ] && [[ ! "$DATA" > "$NOVITA_VECCHIA" ]] && continue
    grep -qxF "$ENTRY" "$NOVITA_VISTE" 2>/dev/null && continue
    NON_VISTE=$((NON_VISTE + 1))
  done < <(grep '^## ' "$HOME/.claude/NOVITA.md" 2>/dev/null | sed 's/^## //')
  if [ "$NON_VISTE" -gt 0 ]; then
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
  python3 "$ARTURO_CODICE/hooks/deriva.py" "$HOME/.claude" 2>/dev/null || true
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

# Invito a finire /setup (23/10/2026): nella telemetria Liliana ha installato e non l'ha mai lanciato,
# Alessio si è fermato prima della fase 9. Una volta al giorno, solo in un'installazione vera senza il
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

# Invito a segnalare: Arturo migliora con quello che le persone gli dicono. Una riga di contesto,
# spenta da "arturo segnala basta" (stato in session-env/segnala.json).
if ! grep -q '"pausa": "sempre"' "$HOME/.claude/session-env/segnala.json" 2>/dev/null; then
  echo "SEGNALA: se in questa sessione qualcosa di Arturo o di Claude Code si inceppa, la persona corregge un tuo comportamento o chiede una cosa che Arturo non sa fare, proponi una volta /segnala, con la bozza gia' scritta da te e --origine avvio in prepara. Riguarda Arturo, non i bug del progetto della persona."
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
