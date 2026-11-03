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
# Un conflitto di un aggiornamento di Arturo si risolve da solo (3/11/2026): vince il file del rilascio, e la
# versione della persona va in personale/conflitti/<data>/ (risolvi_nella_orsa). Restano da risolvere con
# la persona settings.json, i CLAUDE.md e i conflitti del sync.
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

segna_conflitti() {  # $1 = il modo, $2 = i file in conflitto, uno per riga. Dopo un conflitto escono i loro
  # percorsi dentro Arturo come righe `file:` della deriva, così il riepilogo dice quale file blocca
  # (20/10/2026, #3589). Dal 24/10/2026 passano dal filtro unico di telemetria.py (percorso_pubblico):
  # esce solo un file versionato nel ref di Arturo che arriva, ogni altro diventa `file:altro`. Prima
  # bastava la forma, e un conflitto su skills/clienti-rossi/SKILL.md mandava il nome del cliente. Un
  # telemetria.py di prima non conosce `conflitti` e non registra niente. Non fallisce mai.
  [ "${1:-}" = sync ] && return 0
  [ -f "$RADICE/bin/telemetria.py" ] || return 0
  printf '%s\n' "$2" | head -20 | python3 "$RADICE/bin/telemetria.py" conflitti "$REF" "$RADICE" >/dev/null 2>&1
  return 0
}

# Gli archivi della persona (handoff, todo, memoria) non fermano l'applicazione (segnalazione n. 14,
# 26/10/2026). /fine li salva solo verso un remote privato: con Arturo come origin un handoff già
# tracciato, tolto dalla retention, restava una modifica non salvata e l'aggiornamento non partiva più.
# Il controllo vale per ogni modo. In rebase Arturo non li versiona: `git reset --keep` lascia com'è
# ogni file che l'aggiornamento non cambia. In merge e sync li versiona il repository della persona, e
# un commit in arrivo (un handoff scritto su un'altra macchina) può cambiare un archivio con modifiche
# non salvate: lì `git reset --keep` si rifiuta, e porta_dentro risponde APPLICAZIONE ANNULLATA con
# ~/.claude com'era. Il /fine dopo salva l'archivio, e l'applicazione riparte.
# La fonte della lista: le copie in session-start.sh, /inizio, /aggiorna, /fine e README le controlla CP04.
ARCHIVI_PERSONALI=(':(exclude)data/handoffs' ':(exclude)data/todo' ':(exclude)data/memory')

modificati() {  # i file tracciati con modifiche non salvate, archivi della persona esclusi
  git status --porcelain --untracked-files=no -- . "${ARCHIVI_PERSONALI[@]}" | cut -c4-
}

pulita() {  # ~/.claude senza modifiche non salvate
  [ -z "$(modificati)" ]
}

# Le modifiche della persona ai comandi di Arturo che l'aggiornamento cambia vanno in personale/
# (15/10/2026): il comando torna quello di Arturo e non va in conflitto, le sue righe restano sue e
# Claude le legge quando lancia il comando. Tutto succede nella copia di prova, con personale.py della
# versione in arrivo: in ~/.claude i file personali arrivano solo con un risultato integro (porta_dentro).
# Con un repository suo come origin, personale/ viaggia fra le sue macchine solo se quel repository è
# privato (/fine): se non lo è, o non si sa, non si sposta niente e resta il conflitto di sempre.
# ORSA_VIAGGIA: 0 se personale/ non viaggia fra le macchine della persona (il sync, o un suo repository non
# privato come origin). Allora l'Orsa non riceve niente, e un conflitto resta suo (3/11/2026).
ORSA_VIAGGIA=1
VISIBILITA=""
if [ "$MODO" = sync ]; then
  ORSA_VIAGGIA=0
elif [ "$MODO" = merge ]; then
  VISIBILITA=$(gh repo view "$(git remote get-url origin 2>/dev/null)" --json visibility -q .visibility 2>/dev/null)
  [ "$VISIBILITA" = PRIVATE ] || ORSA_VIAGGIA=0
fi
separa_nella_copia() {
  if [ "$MODO" = merge ]; then
    local vis=$VISIBILITA
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

# I conflitti vanno nell'Orsa (3/11/2026). In un aggiornamento di Arturo, un file che va in conflitto prende
# la versione del rilascio, e la versione della persona finisce in personale/conflitti/<data>/, fuori da git,
# con differenze.patch: le sue modifiche rispetto al punto in cui si era staccata da Arturo. Prima un
# conflitto lasciava la copia di prova in attesa, e ogni aggiornamento dopo si fermava lì finché la persona
# non lanciava /aggiorna. Restano conflitti veri, da risolvere con la persona: settings.json (dopo
# unisci-settings.py) e i CLAUDE.md, che sono suoi, e ogni conflitto del sync fra le sue macchine.
CONFLITTI_ORSA=""
salva_della_persona() {  # $1 = il file in conflitto. Copia la versione della persona (quella di $PRIMA)
  local f=$1 dest="$LAVORO/conflitti/$1" base
  grep -qxF -- "$f" "$LAVORO/conflitti/FILE.txt" 2>/dev/null && return 0
  mkdir -p "$LAVORO/conflitti" && printf '%s\n' "$f" >> "$LAVORO/conflitti/FILE.txt" || return 1
  if git cat-file -e "$PRIMA:$f" 2>/dev/null; then
    mkdir -p "$(dirname "$dest")" && git show "$PRIMA:$f" > "$dest" || return 1
  fi
  base=$(git merge-base "$PRIMA" "$REF" 2>/dev/null)
  [ -n "$base" ] && git diff "$base" "$PRIMA" -- "$f" >> "$LAVORO/conflitti/differenze.patch" 2>/dev/null
  return 0
}

da_risolvere_a_mano() {  # $1 = l'elenco dei file in conflitto: c'è un file che resta alla persona?
  local f
  while IFS= read -r f; do
    case "$f" in settings.json|CLAUDE.md|CLAUDE.local.md|*/CLAUDE.md) return 0 ;; esac
  done <<< "$1"
  return 1
}

in_corso() {  # un rebase o un merge fermo nella copia di prova
  [ -d "$(git -C "$COPIA" rev-parse --git-path rebase-merge)" ] || [ -d "$(git -C "$COPIA" rev-parse --git-path rebase-apply)" ] \
    || git -C "$COPIA" rev-parse -q --verify MERGE_HEAD >/dev/null 2>&1
}

risolvi_nella_orsa() {  # esce 0 se nella copia non resta nessun conflitto e merge o rebase sono conclusi
  [ "$ORSA_VIAGGIA" = 0 ] && return 1
  local giri=0 f lista
  while :; do
    lista=$(git -C "$COPIA" diff --name-only --diff-filter=U)
    if [ -z "$lista" ]; then
      in_corso || return 0
      # Un commit della persona rimasto vuoto dopo la risoluzione: il rebase lo salta.
      git -C "$COPIA" rebase --skip >/dev/null 2>&1 || return 1
      continue
    fi
    giri=$((giri + 1)); [ "$giri" -le 50 ] || return 1
    da_risolvere_a_mano "$lista" && return 1
    while IFS= read -r f; do
      [ -n "$f" ] || continue
      salva_della_persona "$f" || return 1
      # Un file che la persona ha cancellato resta cancellato, anche se il rilascio lo cambia: è una sua
      # scelta, come un comando che non usa. Se serviva alla config, controlla la ferma più sotto.
      if git cat-file -e "$REF:$f" 2>/dev/null && git cat-file -e "$PRIMA:$f" 2>/dev/null; then
        git -C "$COPIA" checkout "$REF" -- "$f" >/dev/null 2>&1 || return 1
      else
        git -C "$COPIA" rm -q --force -- "$f" >/dev/null 2>&1 || return 1
      fi
    done <<< "$lista"
    if [ "$MODO" = merge ]; then
      git -C "$COPIA" commit -q --no-edit >/dev/null 2>&1 || return 1
    else
      git -C "$COPIA" rebase --continue >/dev/null 2>&1 || in_corso || return 1
    fi
  done
}

porta_nella_orsa() {  # dopo un'applicazione riuscita: i file della persona in ~/.claude/personale/conflitti
  [ -n "$CONFLITTI_ORSA" ] && [ -d "${LAVORO:-}/conflitti" ] || return 0
  local dest="$RADICE/personale/conflitti/$(date +%Y-%m-%d_%H-%M)"
  mkdir -p "$dest" && cp -R "$LAVORO/conflitti/." "$dest/" && printf '%s\n' "$REF" > "$dest/VERSIONE.txt"
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
    if [ -n "$CONFLITTI_ORSA" ]; then
      porta_nella_orsa || echo "ATTENZIONE: non riesco a copiare le tue versioni dei file in conflitto in personale/conflitti: sono in $LAVORO/conflitti."
      segna_conflitti "$modo" "$CONFLITTI_ORSA"
      echo "Le tue versioni di questi file, andati in conflitto, sono in personale/conflitti:"
      printf '%s\n' "$CONFLITTI_ORSA" | sed 's/^/  /'
    fi
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

case "$MODO" in merge|rebase|sync) ;; *) echo "APPLICAZIONE NON PARTITA: modo sconosciuto \"$MODO\""; exit 1 ;; esac
[ -n "$REF" ] || { echo "APPLICAZIONE NON PARTITA: manca la versione da applicare"; exit 1; }

MODIFICATI=$(modificati)
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
  elif [ "$VECCHIO_MODO" != sync ] && [ "$ORSA_VIAGGIA" = 1 ] \
      && ! da_risolvere_a_mano "$(git -C "$VECCHIA" diff --name-only --diff-filter=U 2>/dev/null)"; then
    # Una copia in attesa da un aggiornamento di Arturo fermava ogni aggiornamento dopo (3/11/2026). Il suo
    # stato, col lavoro di chi la stava risolvendo, va in una patch nell'Orsa; poi la copia si toglie e
    # l'aggiornamento riparte, con i conflitti risolti come sopra.
    SALVA="$RADICE/personale/conflitti/$(date +%Y-%m-%d_%H-%M)"
    if mkdir -p "$SALVA" && { git -C "$VECCHIA" status --short; echo; git -C "$VECCHIA" diff HEAD; } > "$SALVA/copia-in-attesa.patch" 2>/dev/null \
        && [ -s "$SALVA/copia-in-attesa.patch" ]; then
      togli_copia "$VECCHIA"; rm -f "$STATO"
      echo "Una copia di prova con un conflitto aspettava${NATA:+ dal ${NATA/_/ alle }}: il suo stato è in $SALVA/copia-in-attesa.patch, e l'aggiornamento riparte."
    else
      echo "APPLICAZIONE NON PARTITA: una copia di prova con un conflitto aspetta, e non riesco a salvarla in personale/conflitti: $VECCHIA. ~/.claude non è stata toccata."
      exit 1
    fi
  else
    case "$VECCHIO_MODO" in sync) DA="dal sync fra le tue macchine" ;; *) DA="da un aggiornamento di Arturo" ;; esac
    echo "APPLICAZIONE NON PARTITA: una copia di prova con un conflitto aspetta${NATA:+ dal ${NATA/_/ alle }}, $DA: $VECCHIA"
    echo "Concludila (/aggiorna, \"Risolvere un conflitto\") oppure scartala con: aggiorna-applica.sh <radice> scarta. ~/.claude non è stata toccata."
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

# settings.json si unisce come JSON (22/10/2026): il 21/10 un hook aggiunto da Arturo e righe vicine
# cambiate dalla persona, o da un'app come iTerm2, hanno fermato l'aggiornamento di tutti. L'unione
# viene dalla versione in arrivo e vale solo qui, per questo comando. Se la versione non ce l'ha, o se
# le due parti hanno cambiato la stessa cosa, resta il conflitto riga per riga di sempre.
UNISCI=()
if git show "$REF:bin/unisci-settings.py" > "$LAVORO/unisci-settings.py" 2>/dev/null; then
  printf 'settings.json merge=arturo-settings\n' > "$LAVORO/attributi"
  UNISCI=(-c "core.attributesFile=$LAVORO/attributi"
          -c "merge.arturo-settings.driver=python3 \"$LAVORO/unisci-settings.py\" %O %A %B")
fi
if [ "$MODO" = merge ]; then
  git ${UNISCI[@]+"${UNISCI[@]}"} -C "$COPIA" merge --no-edit "$REF" > "$LAVORO/esito" 2>&1
elif [ "$MODO" = sync ]; then
  # Nel sync fra macchine un aggiornamento di Arturo appena unito con merge può non essere ancora
  # pushato: un rebase semplice lo appiattiva in commit singoli e la storia di upstream si perdeva
  # (30/10/2026, migrazione della config di Federico). --rebase-merges rifà il merge.
  git ${UNISCI[@]+"${UNISCI[@]}"} -C "$COPIA" rebase --rebase-merges "$REF" > "$LAVORO/esito" 2>&1
else
  git ${UNISCI[@]+"${UNISCI[@]}"} -C "$COPIA" rebase "$REF" > "$LAVORO/esito" 2>&1
fi
rc=$?
# Un comando che esce con 0 può lasciare file in conflitto: conta lo stato, non il codice d'uscita.
CONFLITTI=$(git -C "$COPIA" diff --name-only --diff-filter=U)
if [ -n "$CONFLITTI" ] && risolvi_nella_orsa; then
  CONFLITTI_ORSA=$(cat "$LAVORO/conflitti/FILE.txt" 2>/dev/null)
  CONFLITTI=""; rc=0
elif [ -n "$CONFLITTI" ]; then
  # Resta un conflitto che non si risolve da solo (settings.json, un CLAUDE.md): la copia aspetta /aggiorna,
  # con i file già risolti col rilascio e le versioni della persona in $LAVORO/conflitti.
  CONFLITTI=$(git -C "$COPIA" diff --name-only --diff-filter=U)
  [ -n "$CONFLITTI" ] || CONFLITTI=$(cat "$LAVORO/conflitti/FILE.txt" 2>/dev/null)
fi
if [ $rc != 0 ] || [ -n "$CONFLITTI" ]; then
  if [ -n "$CONFLITTI" ]; then
    printf '%s %s %s %s\n' "$COPIA" "$PRIMA" "$MODO" "$(date +%Y-%m-%d_%H:%M)" > "$STATO"
    segna_esito conflitto "$MODO"
    segna_conflitti "$MODO" "$CONFLITTI"
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
