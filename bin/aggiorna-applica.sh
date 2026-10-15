#!/usr/bin/env bash
# Applica un aggiornamento di Arturo senza mai scrivere un conflitto nei file in uso (12/10/2026).
#
# Claude Code legge settings.json e gli hook mentre lavora: un merge fatto dentro ~/.claude, anche
# se annullato subito dopo, ci lascia i marcatori di conflitto per un attimo, o per sempre se il
# comando si interrompe. Qui il merge (o il rebase) gira in una copia di prova a parte, una
# `git worktree` in una cartella temporanea. Si controlla la config sulla copia, e solo un risultato
# integro arriva in ~/.claude con `git reset --keep`, che non sovrascrive mai un file suo.
#
# /aggiorna non lancia questo file dalla copia installata: lo legge dalla versione in arrivo
# (`git show <ref>:bin/aggiorna-applica.sh`). Così una correzione a questa procedura protegge già
# l'aggiornamento che la porta.
#
# Uso:
#   aggiorna-applica.sh <radice> merge  <ref>   con un repository suo come origin, Arturo è upstream
#   aggiorna-applica.sh <radice> rebase <ref>   con Arturo come origin
#   aggiorna-applica.sh <radice> sync   <ref>   /inizio dal suo repository: un rebase che non si
#                                               registra, perché non è un aggiornamento di Arturo
#   aggiorna-applica.sh <radice> concludi       dopo aver risolto i conflitti nella copia di prova
#   aggiorna-applica.sh <radice> scarta         toglie la copia di prova in attesa, solo col sì della persona
#
# Righe d'esito, la prima parola è quella che conta:
#   APPLICATO                   l'aggiornamento è in ~/.claude e la config è integra
#   GIÀ AGGIORNATO              niente da applicare
#   APPLICAZIONE NON PARTITA    ~/.claude non è stata toccata (modifiche non salvate, config già rotta)
#   APPLICAZIONE ANNULLATA      ~/.claude è com'era prima; con CONFLITTO la copia di prova aspetta
#   SCARTATA / NIENTE DA SCARTARE  esiti di scarta
#   RIPRISTINO NON RIUSCITO     ~/.claude è rimasta a metà: fermarsi
# Uscita: 0 applicato o niente da fare, 1 non applicato, 2 ripristino non riuscito.
set -u

RADICE=${1:?radice mancante}
MODO=${2:?modo mancante: merge, rebase, sync o concludi}
REF=${3:-}
cd "$RADICE" || { echo "APPLICAZIONE NON PARTITA: non trovo $RADICE"; exit 1; }
export GIT_TERMINAL_PROMPT=0 GIT_EDITOR=true
STATO=$(git rev-parse --git-path arturo-aggiorna-copia)  # dentro .git: git status non lo vede mai

controlla() {  # la config della cartella $1, col controllo della versione in arrivo se c'è
  local c="$1/hooks/controlla-config.py"
  [ -f "$c" ] || c="$RADICE/hooks/controlla-config.py"
  [ -f "$c" ] || return 0
  python3 "$c" --quiet "$1" >/dev/null
}

togli_copia() {
  [ -n "${1:-}" ] || return 0
  git -C "$1" merge --abort >/dev/null 2>&1
  git -C "$1" rebase --abort >/dev/null 2>&1
  git worktree remove --force "$1" >/dev/null 2>&1
  rm -rf "$(dirname "$1")"
  git worktree prune >/dev/null 2>&1
}

segna_esito() {  # $1 = applicato|conflitto|fallito|scartato, $2 = il modo. Un evento della telemetria di
  # Arturo (bin/telemetria.py): dice se gli aggiornamenti arrivano integri. Il sync fra le macchine
  # della persona non è un aggiornamento di Arturo e non si conta. Non fallisce mai.
  [ "${2:-}" = sync ] && return 0
  [ -f "$RADICE/bin/telemetria.py" ] && python3 "$RADICE/bin/telemetria.py" registra aggiorna "$1" >/dev/null 2>&1
  return 0
}

pulita() {  # ~/.claude senza modifiche non salvate
  [ -z "$(git status --porcelain --untracked-files=no)" ]
}

porta_dentro() {  # $1 = il commit della copia, $2 = HEAD di ~/.claude quando è nata, $3 = il modo
  local nuovo=$1 prima=$2 modo=$3
  if [ "$(git rev-parse HEAD)" != "$prima" ]; then
    echo "APPLICAZIONE ANNULLATA: la tua copia è cambiata dopo la prova (un commit nuovo). Rilancia il Passo 3."
    return 1
  fi
  if [ "$nuovo" = "$prima" ]; then
    echo "GIÀ AGGIORNATO: niente da applicare"
    return 0
  fi
  if ! git reset -q --keep "$nuovo"; then
    if [ "$(git rev-parse HEAD)" = "$prima" ] && pulita && controlla "$RADICE"; then
      echo "APPLICAZIONE ANNULLATA: git non ha potuto sostituire i file (vedi sopra). La copia è com'era prima"
      return 1
    fi
  fi
  if [ "$(git rev-parse HEAD)" = "$nuovo" ] && pulita && controlla "$RADICE"; then
    if [ "$modo" != sync ]; then  # /aggiorna indietro torna solo sugli aggiornamenti di Arturo
      mkdir -p session-env
      printf '%s %s %s\n' "$prima" "$nuovo" "$(date +%Y-%m-%d_%H-%M)" >> session-env/aggiornamenti
      printf '%s\n' "$prima" > session-env/ultimo-aggiornamento
    fi
    segna_esito applicato "$modo"
    echo "APPLICATO: config integra"
    return 0
  fi
  # Non dovrebbe succedere: la copia era integra. Si torna a prima e lo si controlla.
  git reset -q --keep "$prima" 2>/dev/null || git reset -q --merge "$prima" 2>/dev/null
  segna_esito fallito "$modo"
  if [ "$(git rev-parse HEAD)" = "$prima" ] && pulita && controlla "$RADICE"; then
    echo "APPLICAZIONE ANNULLATA: dopo l'applicazione la config risultava rotta. La copia è tornata esattamente a prima"
    return 1
  fi
  echo "RIPRISTINO NON RIUSCITO: la config risultava rotta, e la copia NON è tornata a prima. Ecco com'è adesso:"
  git status --short
  return 2
}

if [ "$MODO" = scarta ]; then
  { [ -f "$STATO" ] && read -r COPIA _ < "$STATO"; } || { echo "NIENTE DA SCARTARE: nessuna copia di prova in attesa"; exit 0; }
  togli_copia "$COPIA"; rm -f "$STATO"
  segna_esito scartato
  echo "SCARTATA: la copia di prova $COPIA non c'è più. ~/.claude non è stata toccata."
  exit 0
fi

if [ "$MODO" = concludi ]; then
  { [ -f "$STATO" ] && read -r COPIA PRIMA DA_DOVE _ < "$STATO"; } || { echo "APPLICAZIONE NON PARTITA: nessuna copia di prova in attesa"; exit 1; }
  if [ ! -d "$COPIA" ]; then
    rm -f "$STATO"
    echo "APPLICAZIONE NON PARTITA: la copia di prova non c'è più. Rilancia il Passo 3."
    exit 1
  fi
  if ! controlla "$COPIA"; then
    echo "APPLICAZIONE NON PARTITA: nella copia di prova restano conflitti. ~/.claude non è stata toccata:"
    python3 "$RADICE/hooks/controlla-config.py" "$COPIA" 2>/dev/null | sed 's/^/  /'
    exit 1
  fi
  pulita || { echo "APPLICAZIONE NON PARTITA: ~/.claude ha modifiche non salvate. Non ho toccato niente."; exit 1; }
  porta_dentro "$(git -C "$COPIA" rev-parse HEAD)" "$PRIMA" "${DA_DOVE:-merge}"; esito=$?
  [ $esito = 1 ] && [ "$(git rev-parse HEAD)" != "$PRIMA" ] && exit 1  # copia cambiata: la prova resta
  togli_copia "$COPIA"; rm -f "$STATO"
  exit $esito
fi

case "$MODO" in merge|rebase|sync) ;; *) echo "APPLICAZIONE NON PARTITA: modo sconosciuto «$MODO»"; exit 1 ;; esac
[ -n "$REF" ] || { echo "APPLICAZIONE NON PARTITA: manca la versione da applicare"; exit 1; }

MODIFICATI=$(git status --porcelain --untracked-files=no | cut -c4-)
if [ -n "$MODIFICATI" ]; then
  echo "APPLICAZIONE NON PARTITA: questi file hanno modifiche tue non ancora salvate con un commit:"
  printf '%s\n' "$MODIFICATI" | sed 's/^/  /'
  echo "Non ho toccato niente."
  exit 1
fi
if ! controlla "$RADICE"; then
  echo "APPLICAZIONE NON PARTITA: la config è già rotta prima dell'aggiornamento. Non ho toccato niente:"
  python3 hooks/controlla-config.py "$RADICE" 2>/dev/null | sed 's/^/  /'
  exit 1
fi

# Una copia di prova con un conflitto aspetta: può contenere il lavoro di chi la stava risolvendo.
# Nessun modo la sostituisce in silenzio: si conclude, o si scarta col sì della persona. Una copia
# sparita (la cartella temporanea si svuota al riavvio) non ha niente da perdere: si toglie il registro.
if [ -f "$STATO" ] && read -r VECCHIA _ VECCHIO_MODO NATA _ < "$STATO"; then
  if [ ! -d "$VECCHIA" ]; then
    togli_copia "$VECCHIA"; rm -f "$STATO"
    echo "Una copia di prova in attesa non c'era più (cartella temporanea svuotata): tolta dal registro."
  else
    case "$VECCHIO_MODO" in sync) DA="dal sync fra le tue macchine" ;; *) DA="da un aggiornamento di Arturo" ;; esac
    echo "APPLICAZIONE NON PARTITA: una copia di prova con un conflitto aspetta${NATA:+ dal ${NATA/_/ alle }}, $DA: $VECCHIA"
    echo "Concludila (/aggiorna, «Risolvere un conflitto») oppure scartala con: aggiorna-applica.sh <radice> scarta. ~/.claude non è stata toccata."
    exit 1
  fi
fi

PRIMA=$(git rev-parse HEAD)
TEMP=${TMPDIR:-/tmp}
LAVORO=$(mktemp -d "${TEMP%/}/arturo-aggiorna.XXXXXX") || { echo "APPLICAZIONE NON PARTITA: niente cartella temporanea"; exit 1; }
COPIA="$LAVORO/copia"
if ! git worktree add -q --detach "$COPIA" "$PRIMA" >/dev/null 2>&1; then
  rm -rf "$LAVORO"
  echo "APPLICAZIONE NON PARTITA: non riesco a preparare la copia di prova. Non ho toccato niente."
  exit 1
fi

if [ "$MODO" = merge ]; then
  git -C "$COPIA" merge --no-edit "$REF" > "$LAVORO/esito" 2>&1
else
  git -C "$COPIA" rebase "$REF" > "$LAVORO/esito" 2>&1
fi
rc=$?
# Un comando che esce con 0 può lasciare file in conflitto: conta lo stato, non il codice d'uscita.
CONFLITTI=$(git -C "$COPIA" diff --name-only --diff-filter=U)
if [ $rc != 0 ] || [ -n "$CONFLITTI" ]; then
  if [ -n "$CONFLITTI" ]; then
    printf '%s %s %s %s\n' "$COPIA" "$PRIMA" "$MODO" "$(date +%Y-%m-%d_%H:%M)" > "$STATO"
    segna_esito conflitto "$MODO"
    echo "APPLICAZIONE ANNULLATA: CONFLITTO. La tua copia è com'era prima, e nei suoi file non c'è nessun marcatore."
    echo "Copia di prova con i conflitti: $COPIA"
    echo "File in conflitto:"
    printf '%s\n' "$CONFLITTI" | sed 's/^/  /'
    exit 1
  fi
  tail -5 "$LAVORO/esito"
  togli_copia "$COPIA"
  segna_esito fallito "$MODO"
  echo "APPLICAZIONE ANNULLATA: git si è fermato (vedi sopra). La tua copia è com'era prima"
  exit 1
fi
if ! controlla "$COPIA"; then
  python3 "$RADICE/hooks/controlla-config.py" "$COPIA" 2>/dev/null | sed 's/^/  /'
  togli_copia "$COPIA"
  segna_esito fallito "$MODO"
  echo "APPLICAZIONE ANNULLATA: la versione in arrivo avrebbe lasciato la config rotta. La tua copia è com'era prima"
  exit 1
fi
porta_dentro "$(git -C "$COPIA" rev-parse HEAD)" "$PRIMA" "$MODO"; esito=$?
togli_copia "$COPIA"
exit $esito
