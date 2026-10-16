#!/bin/bash
# Hook Avvio Sessione - Caricamento Memoria
# Carica il contesto del progetto all'avvio della sessione

PROJECT_ROOT="${PWD}"
PROJECT_NAME="$(basename "$PROJECT_ROOT")"

# macOS: cattura window ID e setta titolo terminale
# Solo nell'app Terminale: da iTerm, VS Code o dall'app desktop osascript aprirebbe il
# Terminale e macOS chiederebbe il permesso di Automazione a chi non sa cosa sia.
if [[ "$OSTYPE" == "darwin"* && "${TERM_PROGRAM:-}" == "Apple_Terminal" ]]; then
  mkdir -p "$HOME/.claude/session-env"   # dir gitignored: non esiste su un clone fresco
  WID_FILE="$HOME/.claude/session-env/terminal-wid-$PROJECT_NAME"
  WID=$(osascript -e 'tell application "Terminal" to id of front window' 2>/dev/null)
  if [ -n "$WID" ]; then
    echo "$WID" > "$WID_FILE"
    osascript -e "tell application \"Terminal\" to set custom title of window id $WID to \"Claude: $PROJECT_NAME\"" 2>/dev/null
  fi
fi

# Info directory di lavoro e macchina: con piu' computer, Claude sa su quale lavora.
echo "DIRECTORY: $PROJECT_ROOT"
MACCHINA=$(scutil --get ComputerName 2>/dev/null || hostname 2>/dev/null)
[ -n "$MACCHINA" ] && echo "MACCHINA: $MACCHINA"

# Dopo un compact il contesto e' stato riassunto: prima di continuare, un riepilogo che
# l'utente puo' controllare. SessionStart con source "compact" e' la via documentata;
# lo stdout di PostCompact non entra nel contesto.
# read con tetto di 2 secondi: uno stdin lasciato aperto non deve appendere l'avvio.
HOOK_INPUT=""
[ -t 0 ] || IFS= read -r -t 2 -d '' HOOK_INPUT || true
if printf '%s' "$HOOK_INPUT" | grep -qE '"source"[[:space:]]*:[[:space:]]*"compact"'; then
  echo "COMPACT APPENA AVVENUTO: fermati. Riepiloga all'utente file modificati, comandi di test e build, decisioni, task pendenti e ultimo errore. Poi aspetta la sua conferma prima di continuare."
fi

# Reminder context management
echo "CONTEXT: al ~65% di utilizzo completa il task, chiudi con /fine e riparti con /inizio in una sessione nuova"

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

# Guardia anti-divergenza config (~/.claude vs origin/main).
# Il confronto legge gli oggetti Git gia' presenti in locale: senza un fetch resta fermo a
# quello che sapeva l'ultima volta, e chi non lancia mai /inizio non vedrebbe mai un
# aggiornamento. Per questo il fetch parte qui, in background e al massimo ogni 6 ore, cosi'
# l'avvio non aspetta la rete. L'avviso di questa sessione usa il fetch della volta prima.
# Config integra: un settings.json rotto spegne tutte le guardie senza avvisare.
if [ -f "$HOME/.claude/hooks/controlla-config.py" ]; then
  python3 "$HOME/.claude/hooks/controlla-config.py" --quiet "$HOME/.claude" 2>/dev/null
fi
if git -C "$HOME/.claude" rev-parse --git-dir >/dev/null 2>&1 && ! git -C "$HOME/.claude" symbolic-ref -q HEAD >/dev/null 2>&1; then
  echo "CONFIG: ~/.claude non sta su un branch (HEAD scollegato): i commit di /fine non finirebbero su main. Chiedi a Claude di riportarla su main."
fi
# File della config cambiati e non salvati in git: lavoro di un'altra sessione o rimasto da
# ieri. I file nuovi non contano: molti sono dati locali che git ignora o non deve vedere.
if git -C "$HOME/.claude" rev-parse --git-dir >/dev/null 2>&1; then
  SPORCHI=$(git -C "$HOME/.claude" status --porcelain 2>/dev/null | grep -v '^??' | wc -l | tr -d ' ')
  if [ "${SPORCHI:-0}" -gt 0 ]; then
    echo "CONFIG: $SPORCHI file di ~/.claude modificati e non salvati in git (lavoro di un'altra sessione o rimasto da ieri). Chiedi a Claude cosa sono prima di aggiornare."
  fi
fi

# Banchi delle guardie (tests/banchi-avvio.sh): un rosso si dice subito, all'avvio. Se l'esito
# ha piu' di 12 ore, i banchi ripartono in background e il risultato lo legge la sessione dopo:
# l'avvio non aspetta. Il lock e' una cartella, perche' mkdir e' atomico anche dove flock non
# c'e' (macOS, Git Bash): due sessioni che partono insieme non lo prendono entrambe. Dentro c'e'
# il PID di chi lo tiene; un lock col PID morto (kill -9, riavvio) e' orfano e si riprende,
# altrimenti un solo processo ucciso male spegnerebbe i banchi per sempre.
# Solo in un'installazione vera (~/.claude e' un repository git); ARTURO_BANCHI_AVVIO=0 li spegne.
BANCHI_ESITO="$HOME/.claude/cache/banchi-ultimo-esito.txt"
if [ -f "$BANCHI_ESITO" ] && [ "$(sed -n '1p' "$BANCHI_ESITO" 2>/dev/null)" = "ROSSO" ]; then
  echo "GUARDIE: banchi rossi, una guardia potrebbe non proteggere: $(sed -n '2p' "$BANCHI_ESITO")"
  sed -n '3,6p' "$BANCHI_ESITO" | sed 's/^/        /'
  echo "        Dillo a Claude: rilancia con bash ~/.claude/tests/banchi-avvio.sh e proponi /segnala."
fi
if [ "${ARTURO_BANCHI_AVVIO:-1}" != "0" ] && [ -f "$HOME/.claude/tests/banchi-avvio.sh" ] \
   && git -C "$HOME/.claude" rev-parse --git-dir >/dev/null 2>&1; then
  if [ ! -f "$BANCHI_ESITO" ] || [ -n "$(find "$BANCHI_ESITO" -mmin +720 2>/dev/null)" ]; then
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
      git -C "$HOME/.claude" fetch --quiet "$REMOTO" main >/dev/null 2>&1 && printf '%s' "$ADESSO" > "$RIUSCITO"
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
  if [ "${BEHIND:-0}" -gt 0 ]; then
    echo "ARTURO: c'e' un aggiornamento ($BEHIND commit) — scaricalo con /aggiorna"
  fi
  # Con un repository personale come origin, Arturo vive su upstream.
  if git -C "$HOME/.claude" rev-parse --verify --quiet upstream/main >/dev/null 2>&1; then
    UPSTREAM_BEHIND=$(git -C "$HOME/.claude" rev-list --count HEAD..upstream/main 2>/dev/null || echo 0)
    if [ "${UPSTREAM_BEHIND:-0}" -gt 0 ]; then
      echo "ARTURO: c'e' un aggiornamento dell'harness ($UPSTREAM_BEHIND commit su upstream) — scaricalo con /aggiorna"
    fi
  fi
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

# Deriva (hooks/deriva.py): file e hook di Arturo cambiati o spenti, config rotta. Una riga solo se
# c'è da fare; registra per la telemetria l'elenco quando cambia. Prima dell'avvio della telemetria,
# così una config rotta parte con l'invio di questa sessione.
if [ -f "$HOME/.claude/hooks/deriva.py" ]; then
  python3 "$HOME/.claude/hooks/deriva.py" "$HOME/.claude" 2>/dev/null || true
fi

# Telemetria (bin/telemetria.py): registra la sessione senza rete, avvisa la persona una
# volta sola e lancia l'invio in background al massimo ogni 6 ore. Non ferma mai l'avvio.
if [ -f "$HOME/.claude/bin/telemetria.py" ]; then
  python3 "$HOME/.claude/bin/telemetria.py" avvio 2>/dev/null || true
fi

# Invito a segnalare: Arturo migliora con quello che le persone gli dicono. Una riga di contesto,
# spenta da «arturo segnala basta» (stato in session-env/segnala.json).
if ! grep -q '"pausa": "sempre"' "$HOME/.claude/session-env/segnala.json" 2>/dev/null; then
  echo "SEGNALA: se in questa sessione qualcosa di Arturo o di Claude Code si inceppa, la persona corregge un tuo comportamento o chiede una cosa che Arturo non sa fare, proponi una volta /segnala, con la bozza gia' scritta da te. Riguarda Arturo, non i bug del progetto della persona."
fi

# Le aggiunte della persona (personale/session-start.sh, 16/10/2026): gli aggiornamenti di Arturo non le
# toccano, e /aggiorna ci sposta da solo le righe aggiunte a questo file. Girano in una subshell
# alla fine, con le variabili di qui: un loro errore non ferma la sessione.
if [ -f "$HOME/.claude/personale/session-start.sh" ]; then
  ( . "$HOME/.claude/personale/session-start.sh" ) || true
fi
