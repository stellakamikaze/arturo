#!/usr/bin/env bash
# Applica un aggiornamento di Arturo senza mai scrivere un conflitto nei file in uso (12/10/2026).
#
# Claude Code legge settings.json e gli hook mentre lavora: un merge fatto dentro ~/.claude, anche
# se annullato subito dopo, ci lascia i marcatori di conflitto per un attimo, o per sempre se il
# comando si interrompe. Qui il merge (o il rebase) gira in una copia di prova a parte, una
# `git worktree` dentro la cartella .git (git status non la vede, e un riavvio non la svuota come
# la cartella temporanea). Si controlla la config sulla copia, e solo un risultato
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
#   aggiorna-applica.sh <radice> indietro       /aggiorna indietro: annulla l'ultimo aggiornamento registrato,
#                                               coi commit successivi della persona rifatti nella copia di prova
#
# Righe d'esito, la prima parola è quella che conta:
#   APPLICATO                   l'aggiornamento è in ~/.claude e la config è integra
#   GIÀ AGGIORNATO              niente da applicare
#   APPLICAZIONE NON PARTITA    ~/.claude non è stata toccata (modifiche non salvate, config già rotta)
#   APPLICAZIONE ANNULLATA      ~/.claude è com'era prima; con CONFLITTO la copia di prova aspetta
#   SCARTATA / NIENTE DA SCARTARE  esiti di scarta
#   TORNATO INDIETRO / NIENTE DA ANNULLARE / RITORNO ANNULLATO  esiti di indietro (~/.claude com'era
#                               prima con RITORNO ANNULLATO)
#   RIPRISTINO NON RIUSCITO     ~/.claude è rimasta a metà: fermarsi
# Uscita: 0 applicato o niente da fare, 1 non applicato, 2 ripristino non riuscito.
set -u

RADICE=${1:?radice mancante}
MODO=${2:?modo mancante: merge, rebase, sync, concludi, scarta o indietro}
REF=${3:-}
cd "$RADICE" || { echo "APPLICAZIONE NON PARTITA: non trovo $RADICE"; exit 1; }
export GIT_TERMINAL_PROMPT=0 GIT_EDITOR=true
STATO=$(git rev-parse --git-path arturo-aggiorna-copia)  # dentro .git: git status non lo vede mai
# Le copie di prova stanno anche loro dentro .git: una copia con un conflitto può aspettare giorni
# il lavoro di chi lo risolve, e la cartella temporanea si svuota da sola (15/10/2026).
CASA_COPIE="$(git rev-parse --path-format=absolute --git-common-dir 2>/dev/null)/arturo-aggiorna"

nuova_copia() {  # $1 = il commit di partenza. Imposta LAVORO e COPIA, esce 1 se non riesce
  mkdir -p "$CASA_COPIE" 2>/dev/null
  LAVORO=$(mktemp -d "$CASA_COPIE/copia.XXXXXX" 2>/dev/null) || return 1
  COPIA="$LAVORO/copia"
  git worktree add -q --detach "$COPIA" "$1" >/dev/null 2>&1 && return 0
  rm -rf "$LAVORO"
  return 1
}

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
  # Un'installazione dell'aggiornamento automatico (bin/aggiornamenti.py) si conta come automatico.
  [ "${2:-}" = sync ] && return 0
  local esito="$1"
  [ "$esito" = applicato ] && [ "${ARTURO_AGGIORNA_AUTOMATICO:-}" = 1 ] && esito=automatico
  [ -f "$RADICE/bin/telemetria.py" ] && python3 "$RADICE/bin/telemetria.py" registra aggiorna "$esito" >/dev/null 2>&1
  return 0
}

pulita() {  # ~/.claude senza modifiche non salvate
  [ -z "$(git status --porcelain --untracked-files=no)" ]
}

# Le modifiche della persona ai comandi di Arturo che l'aggiornamento cambia vanno in personale/
# (15/10/2026): il comando torna quello di Arturo e non va in conflitto, le sue righe restano sue e
# Claude le legge quando lancia il comando. Tutto succede nella copia di prova, con personale.py della
# versione in arrivo: in ~/.claude i file personali arrivano solo con un risultato integro (porta_dentro).
# Con un repository suo come origin, personale/ viaggia fra le sue macchine solo se quel repository è
# privato (/fine): se non lo è, o non si sa, non si sposta niente e resta il conflitto di sempre.
separa_nella_copia() {
  if [ "$MODO" = merge ]; then
    local vis
    vis=$(gh repo view "$(git remote get-url origin 2>/dev/null)" --json visibility -q .visibility 2>/dev/null)
    if [ "$vis" != PRIVATE ]; then
      echo "  NON SEPARATO: il tuo repository della config non risulta privato (${vis:-visibilità sconosciuta}), e personale/ non viaggerebbe fra le tue macchine. Le tue modifiche ai comandi restano dove sono."
      return 0
    fi
  fi
  git show "$REF:bin/personale.py" > "$LAVORO/personale.py" 2>/dev/null || cp bin/personale.py "$LAVORO/personale.py" 2>/dev/null || return 0
  mkdir -p "$COPIA/personale" && copia_personale "$RADICE" "$COPIA" 2>/dev/null
  ARTURO_RADICE="$COPIA" python3 -I "$LAVORO/personale.py" separa --verso "$REF" > "$LAVORO/separa" 2>&1
  local rc=$?
  sed 's/^/  /' "$LAVORO/separa"
  [ $rc = 0 ] && [ -z "$(git -C "$COPIA" status --porcelain --untracked-files=no)" ]
}

# I file personali sono due tipi: <comando>.md per i comandi e <hook>.sh per gli hook di sessione.
# Fino al 17/10/2026 viaggiavano solo i .md, e le aggiunte agli hook spostate si perdevano (#3519).
copia_personale() {  # $1 = da, $2 = verso
  local f
  for f in "$1"/personale/*.md "$1"/personale/*.sh; do
    [ -f "$f" ] || continue
    mkdir -p "$2/personale" && cp "$f" "$2/personale/" || return 1
  done
}

riporta_personale() {  # i file personali della copia di prova, solo dopo un'applicazione riuscita
  [ -n "${COPIA:-}" ] && [ -d "$COPIA/personale" ] || return 0
  copia_personale "$COPIA" "$RADICE"
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
    riporta_personale || echo "ATTENZIONE: non riesco a copiare personale/ dalla copia di prova ($COPIA): copiali a mano prima di scartarla."
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

# /aggiorna indietro (15/10/2026): torna alla versione prima dell'ultimo aggiornamento registrato e
# rifà sopra i commit della persona arrivati dopo. Il cherry-pick gira nella copia di prova, come il
# merge: un conflitto non lascia mai marcatori nei file che Claude Code sta leggendo.
if [ "$MODO" = indietro ]; then
  RIGA=$(tail -1 session-env/aggiornamenti 2>/dev/null)
  [ -n "$RIGA" ] || { echo "NIENTE DA ANNULLARE: nessun aggiornamento registrato"; exit 0; }
  read -r VPRIMA VDOPO _ <<< "$RIGA"
  pulita || { echo "RITORNO ANNULLATO: ~/.claude ha modifiche non salvate. Non ho toccato niente."; exit 1; }
  [ -f "$STATO" ] && { echo "RITORNO ANNULLATO: una copia di prova con un conflitto aspetta. Concludila o scartala prima. Non ho toccato niente."; exit 1; }
  ADESSO=$(git rev-parse HEAD)
  git merge-base --is-ancestor "$VDOPO" "$ADESSO" 2>/dev/null || {
    echo "RITORNO ANNULLATO: la versione installata non discende più dall'aggiornamento registrato. Non ho toccato niente."; exit 1; }
  nuova_copia "$VPRIMA" || { echo "RITORNO ANNULLATO: non riesco a preparare la copia di prova. Non ho toccato niente."; exit 1; }
  if [ "$VDOPO" != "$ADESSO" ] && ! git -C "$COPIA" cherry-pick "$VDOPO..$ADESSO" > "$LAVORO/esito" 2>&1; then
    togli_copia "$COPIA"
    echo "RITORNO ANNULLATO: i tuoi commit successivi non si applicano sulla versione vecchia. ~/.claude non è stata toccata."
    exit 1
  fi
  if ! controlla "$COPIA"; then
    togli_copia "$COPIA"
    echo "RITORNO ANNULLATO: la versione di prima avrebbe lasciato la config rotta. ~/.claude non è stata toccata."
    exit 1
  fi
  NUOVO=$(git -C "$COPIA" rev-parse HEAD)
  togli_copia "$COPIA"
  if [ "$(git rev-parse HEAD)" = "$ADESSO" ] && git reset -q --keep "$NUOVO" && pulita && controlla "$RADICE"; then
    sed -i.bak '$d' session-env/aggiornamenti && rm -f session-env/aggiornamenti.bak
    segna_esito indietro
    echo "TORNATO INDIETRO: config integra"
    exit 0
  fi
  if [ "$(git rev-parse HEAD)" = "$ADESSO" ] && pulita && controlla "$RADICE"; then
    echo "RITORNO ANNULLATO: git non ha potuto sostituire i file (vedi sopra). ~/.claude è com'era prima"
    exit 1
  fi
  git reset -q --keep "$ADESSO" 2>/dev/null || git reset -q --merge "$ADESSO" 2>/dev/null
  if [ "$(git rev-parse HEAD)" = "$ADESSO" ] && pulita && controlla "$RADICE"; then
    echo "RITORNO ANNULLATO: dopo il ritorno la config risultava rotta. ~/.claude è tornata com'era prima"
    exit 1
  fi
  echo "RIPRISTINO NON RIUSCITO: ~/.claude NON è tornata a prima. Ecco com'è adesso:"
  git status --short
  exit 2
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
# sparita (cancellata a mano, o nella cartella temporanea delle versioni prima del 15/10) non ha
# niente da perdere: si toglie il registro.
if [ -f "$STATO" ] && read -r VECCHIA _ VECCHIO_MODO NATA _ < "$STATO"; then
  if [ ! -d "$VECCHIA" ]; then
    togli_copia "$VECCHIA"; rm -f "$STATO"
    echo "Una copia di prova in attesa non c'era più: tolta dal registro."
  else
    case "$VECCHIO_MODO" in sync) DA="dal sync fra le tue macchine" ;; *) DA="da un aggiornamento di Arturo" ;; esac
    echo "APPLICAZIONE NON PARTITA: una copia di prova con un conflitto aspetta${NATA:+ dal ${NATA/_/ alle }}, $DA: $VECCHIA"
    echo "Concludila (/aggiorna, «Risolvere un conflitto») oppure scartala con: aggiorna-applica.sh <radice> scarta. ~/.claude non è stata toccata."
    exit 1
  fi
fi

PRIMA=$(git rev-parse HEAD)
if ! nuova_copia "$PRIMA"; then
  echo "APPLICAZIONE NON PARTITA: non riesco a preparare la copia di prova. Non ho toccato niente."
  exit 1
fi

if [ "$MODO" != sync ] && ! separa_nella_copia; then
  togli_copia "$COPIA"
  echo "APPLICAZIONE NON PARTITA: spostando le tue modifiche ai comandi in personale/ qualcosa non è andato. ~/.claude non è stata toccata."
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
