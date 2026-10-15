#!/usr/bin/env bash
# handoff-gate.sh: controlla la sezione «## Task Pendenti» di un handoff prima che /fine chiuda.
#
# USO
#   handoff-gate.sh <file-handoff>
#
# ROSSO (una riga per difetto, ognuna comincia con «GATE HANDOFF: rosso:»)
#   - manca la sezione esatta «## Task Pendenti»: c'è sempre, anche senza task;
#   - un titolo quasi uguale («## Task pendenti», «## Task Pendenti (3)»);
#   - la sezione non ha righe e non contiene la frase «nessun task pendente»;
#   - la tabella non ha la colonna ID, o l'ultima colonna non è «Chi»;
#   - una riga ha nella colonna ID un valore diverso da #numero;
#   - il #numero non esiste nell'archivio dei todo, oppure il todo è già chiuso;
#   - Chi non è una delle categorie di bin/todo_store.py (tu, decidi, io);
#   - Task o Descrizione è un segnaposto del modello mai compilato («cosa resta», «[task]», TODO).
#   La frase «nessun task pendente» conta solo dentro la sezione, con maiuscole libere.
#
# L'archivio dei todo è quello di bin/todo_store.py (ARTURO_TODO lo sposta, per i banchi).
#
# EXIT
#   0 verde (stampa «GATE HANDOFF: verde») · 1 rosso · 2 argomento mancante, file assente
#   o archivio dei todo illeggibile

set -u

if [ "$#" -ne 1 ] || [ -z "${1:-}" ]; then
  printf 'GATE HANDOFF: uso: handoff-gate.sh <file-handoff>\n' >&2
  exit 2
fi
if [ ! -f "$1" ]; then
  printf 'GATE HANDOFF: file assente: %s\n' "$1" >&2
  exit 2
fi

QUI=$(cd "$(dirname "$0")" && pwd)
# Le categorie di Chi e i todo aperti vengono dall'archivio: il gate non ne tiene una copia.
# Prima riga: le categorie. Seconda: gli id aperti. Terza: gli id chiusi.
ARCHIVIO=$(python3 - "$QUI" <<'PY'
import sys
sys.path.insert(0, sys.argv[1])
import todo_store as ts
todo, _ = ts.carica()
print(" ".join(ts.CHI))
print(" ".join(str(t["id"]) for t in todo.values() if t["stato"] in ts.APERTI))
print(" ".join(str(t["id"]) for t in todo.values() if t["stato"] not in ts.APERTI))
PY
)
if [ -z "$ARCHIVIO" ]; then
  printf 'GATE HANDOFF: non riesco a leggere l%sarchivio dei todo (bin/todo_store.py)\n' "'" >&2
  exit 2
fi
CHI=$(printf '%s\n' "$ARCHIVIO" | sed -n 1p)
APERTI=$(printf '%s\n' "$ARCHIVIO" | sed -n 2p)
CHIUSI=$(printf '%s\n' "$ARCHIVIO" | sed -n 3p)

awk -v chi_ammessi="$CHI" -v aperti="$APERTI" -v chiusi="$CHIUSI" '
function trim(s) { gsub(/^[ \t]+|[ \t]+$/, "", s); return s }
function rosso(m) { print "GATE HANDOFF: rosso: " m; bad = 1 }
# divide una riga di tabella in celle; il pipe con backslash resta dentro la cella
function celle(riga, out,    n, i, k, parti) {
  gsub(/\\\|/, "\001", riga)
  n = split(riga, parti, "|")
  k = 0
  for (i = 2; i <= n; i++) {
    if (i == n && trim(parti[i]) == "") break
    out[++k] = trim(parti[i])
  }
  return k
}
function separatore(riga,    n, i, c) {
  n = celle(riga, c)
  if (n == 0) return 0
  for (i = 1; i <= n; i++) if (c[i] !~ /^:?-+:?$/) return 0
  return 1
}
# Vero se la cella è fatta solo di segnaposti: tolti quelli e la punteggiatura, non resta niente.
function guscio(s,    t) {
  t = tolower(s)
  gsub(/\[[ \t]*(todo|tbd|xxx|task|nome|descrizione|titolo|progetto|priorita|status|stato)[ \t]*\]/, "", t)
  gsub(/cosa (resta|manca)( da fare)?|da (compilare|riempire|completare|definire|inserire)|lorem ipsum/, "", t)
  gsub(/(^|[^a-z])(todo|tbd|fixme|xxx|placeholder)([^a-z]|$)/, " ", t)
  gsub(/[^a-z0-9]/, "", t)
  return t == ""
}
function intestazione(riga,    n, i, c) {
  n = celle(riga, c)
  colid = 0; coltask = 0; coldesc = 0
  for (i = 1; i <= n; i++) {
    if (tolower(c[i]) == "id") colid = i
    if (tolower(c[i]) == "task") coltask = i
    if (tolower(c[i]) == "descrizione") coldesc = i
  }
  chiok = (n > 0 && c[n] == "Chi")
  if (!colid) rosso("riga " NR ": la tabella non ha la colonna ID")
  if (!chiok) rosso("riga " NR ": l\047ultima colonna della tabella non è «Chi»")
}
function controlla(riga,    n, c, id, num, chi) {
  n = celle(riga, c)
  righe++
  if (colid) {
    id = (colid <= n) ? c[colid] : ""
    if (id !~ /^#[0-9]+$/)
      rosso("riga " NR ": ID «" id "» non è un #numero di todo: crea il todo con arturo todo aggiungi")
    else {
      num = substr(id, 2) + 0
      if (index(" " chiusi " ", " " num " "))
        rosso("riga " NR ": il todo " id " è già chiuso: toglilo dai pendenti")
      else if (!index(" " aperti " ", " " num " "))
        rosso("riga " NR ": il todo " id " non esiste nell\047archivio dei todo")
    }
  }
  if (chiok) {
    chi = (n > 0) ? c[n] : ""
    if (!index(" " chi_ammessi " ", " " chi " ") || chi == "")
      rosso("riga " NR ": Chi «" chi "» non è una delle categorie ammesse (" chi_ammessi ")")
  }
  if (coltask && coltask <= n && guscio(c[coltask]))
    rosso("riga " NR ": Task «" c[coltask] "» è un segnaposto: scrivi l\047azione")
  if (coldesc && coldesc <= n && guscio(c[coldesc]))
    rosso("riga " NR ": Descrizione «" c[coldesc] "» è un segnaposto: scrivi cosa serve per riprendere")
}

# la frase fuori dalla sezione serve solo al messaggio, non rende verde
tolower($0) ~ /nessun task pendente/ { dich = 1 }
tolower($0) ~ /^##?[ \t]*task[ \t]+pendenti/ && $0 !~ /^## Task Pendenti[ \t]*$/ { quasi[++nq] = $0; quasinr[nq] = NR }

/^## Task Pendenti[ \t]*$/ { sez = 1; dentro = 1; tab = 0; next }
dentro && /^##?[ \t]/ { dentro = 0 }
dentro && tolower($0) ~ /nessun task pendente/ { dichsez = 1 }
dentro && /^[ \t]*\|/ {
  riga = $0
  sub(/^[ \t]+/, "", riga)
  if (!tab) { tab = 1; hdr = 0; cand = riga; candnr = NR; next }
  if (!hdr) {
    hdr = 1
    if (separatore(riga)) { intestazione(cand); next }
    rosso("riga " candnr ": tabella senza riga di separazione sotto l\047intestazione")
    colid = 0; chiok = 0; coltask = 0; coldesc = 0
    next
  }
  if (separatore(riga)) next
  controlla(riga)
  next
}
dentro { tab = 0 }

END {
  if (!sez) {
    m = "manca la sezione «## Task Pendenti», obbligatoria anche senza task"
    if (nq) m = m " (trovato «" quasi[1] "» alla riga " quasinr[1] ": il titolo deve essere esatto)"
    else if (dich) m = m " (la frase «nessun task pendente» va dentro la sezione)"
    rosso(m)
  }
  if (sez) for (i = 1; i <= nq; i++)
    rosso("riga " quasinr[i] ": titolo «" quasi[i] "»: il titolo deve essere esatto, «## Task Pendenti»")
  if (sez && !righe && !dichsez)
    rosso("la sezione «## Task Pendenti» non ha righe e non contiene la frase «nessun task pendente»")
  if (bad) exit 1
  print "GATE HANDOFF: verde"
}
' "$1"
