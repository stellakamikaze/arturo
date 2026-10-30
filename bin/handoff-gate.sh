#!/usr/bin/env bash
# handoff-gate.sh: controlla la sezione "## Task Pendenti" di un handoff prima che /fine chiuda.
#
# USO
#   handoff-gate.sh <file-handoff>
#
# ROSSO (una riga per difetto, ognuna comincia con "GATE HANDOFF: rosso:")
#   - manca la sezione esatta "## Task Pendenti": c'è sempre, anche senza task;
#   - un titolo quasi uguale ("## Task pendenti", "## Task Pendenti (3)");
#   - la sezione non ha righe e non contiene la frase "nessun task pendente";
#   - la tabella non ha la colonna ID, o l'ultima colonna non è "Chi";
#   - una riga ha un numero di celle diverso dall'intestazione (un "|" dentro una cella va scritto \|);
#   - una riga ha nella colonna ID un valore diverso da #numero;
#   - il #numero non esiste nell'archivio dei todo, oppure il todo è già chiuso;
#   - Chi non è una delle categorie di bin/todo_store.py (tu, decidi, io) né una delle sue forme
#     scritte per la persona: "Claude" (io), "Decidi tu" (decidi), "Tu: <cosa serve>" (tu);
#   - Task o Descrizione è un segnaposto del modello mai compilato ("cosa resta", "[task]", TODO);
#   - un'idea "→ memoria" nella sezione "## Idee" senza [[slug]], o con uno slug che non è una nota
#     della memoria né una nota in attesa in _in-attesa.md.
#   La frase "nessun task pendente" conta solo dentro la sezione, con maiuscole libere.
#
# PROFILO (hooks/handoff-gate.local, bin/handoff_profilo.py): chi tiene i task fuori da Arturo
# cambia il nome della colonna ID, i valori ammessi in Chi, ammette OFFLINE e spegne il controllo
# sull'archivio dei todo. Senza il file vale il profilo di Arturo descritto sopra.
#
# COMMENTO GITLEAKS
#   "<!-- gitleaks:allow … -->" dentro una cella non conta: il gate legge la cella senza. Dopo
#   l'ultimo "|" il gate lo ignora con una riga "GATE HANDOFF: avviso:".
#
# L'archivio dei todo è quello di bin/todo_store.py (ARTURO_TODO lo sposta, per i banchi).
#
# EXIT
#   0 verde (stampa "GATE HANDOFF: verde") · 1 rosso · 2 argomento mancante, file assente
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
# Profilo, archivio dei todo e idee vengono da Python: il gate non ne tiene una copia.
# Righe: 1 categorie di Chi, 2 id aperti, 3 id chiusi, 4 colonna ID, 5 regex di Chi, 6 offline (1/0),
# 7 archivio (1/0); dalla 8 le righe rosse delle idee.
ARCHIVIO=$(PYTHONIOENCODING=utf-8 python3 - "$QUI" "$1" <<'PY'
import sys
from pathlib import Path
sys.path.insert(0, sys.argv[1])
import handoff_profilo as hp
profilo = hp.carica()
archivio = hp.vero(profilo["archivio"])
try:
    import todo_store as ts
    todo, _ = ts.carica()
    righe = [" ".join(ts.CHI),
             " ".join(str(t["id"]) for t in todo.values() if t["stato"] in ts.APERTI),
             " ".join(str(t["id"]) for t in todo.values() if t["stato"] not in ts.APERTI)]
except Exception:  # noqa: BLE001 - senza archivio il gate vale solo se il profilo lo spegne
    if archivio:
        sys.exit(0)
    righe = ["", "", ""]
testo = Path(sys.argv[2]).read_text(encoding="utf-8", errors="replace")
righe += [profilo["colonna-id"], profilo["chi"], "1" if hp.vero(profilo["offline"]) else "0",
          "1" if archivio else "0"]
righe += hp.idee_senza_nota(testo, hp.cartelle_memoria())
print("\n".join(righe))
PY
)
if [ -z "$ARCHIVIO" ]; then
  printf 'GATE HANDOFF: non riesco a leggere l%sarchivio dei todo (bin/todo_store.py)\n' "'" >&2
  exit 2
fi
CHI=$(printf '%s\n' "$ARCHIVIO" | sed -n 1p)
APERTI=$(printf '%s\n' "$ARCHIVIO" | sed -n 2p)
CHIUSI=$(printf '%s\n' "$ARCHIVIO" | sed -n 3p)
COLONNA=$(printf '%s\n' "$ARCHIVIO" | sed -n 4p)
CHIRE=$(printf '%s\n' "$ARCHIVIO" | sed -n 5p)
OFFLINE=$(printf '%s\n' "$ARCHIVIO" | sed -n 6p)
CONTROLLA_ARCHIVIO=$(printf '%s\n' "$ARCHIVIO" | sed -n 7p)
IDEE=$(printf '%s\n' "$ARCHIVIO" | sed -n '8,$p')

OUT=$(awk -v chi_ammessi="$CHI" -v aperti="$APERTI" -v chiusi="$CHIUSI" -v colnome="$COLONNA" \
  -v chire="$CHIRE" -v offline="$OFFLINE" -v archivio="$CONTROLLA_ARCHIVIO" '
function trim(s) { gsub(/^[ \t]+|[ \t]+$/, "", s); return s }
function rosso(m) { print "GATE HANDOFF: rosso: " m; bad = 1 }
# divide una riga di tabella in celle; il pipe con backslash resta dentro la cella, il commento
# gitleaks dentro una cella non conta
function celle(riga, out,    n, i, k, parti) {
  gsub(/\\\|/, "\001", riga)
  gsub(RE_GL, "", riga)
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
  ncol = n; colid = 0; coltask = 0; coldesc = 0
  for (i = 1; i <= n; i++) {
    if (tolower(c[i]) == tolower(colnome)) colid = i
    if (tolower(c[i]) == "task") coltask = i
    if (tolower(c[i]) == "descrizione") coldesc = i
  }
  chiok = (n > 0 && c[n] == "Chi")
  if (!colid) rosso("riga " NR ": la tabella non ha la colonna " colnome)
  if (!chiok) rosso("riga " NR ": l\047ultima colonna della tabella non è \"Chi\"")
}
function controlla(riga,    n, c, id, num, chi, cat) {
  n = celle(riga, c)
  righe++
  if (ncol && n != ncol) {
    rosso("riga " NR ": " n " celle invece di " ncol ": un \"|\" dentro una cella va scritto \\|")
    return
  }
  if (colid) {
    id = (colid <= n) ? c[colid] : ""
    if (offline == "1" && id == "OFFLINE") {
      # task non ancora creato: lo crea la prossima /fine
    } else if (id !~ /^#[0-9]+$/)
      rosso("riga " NR ": " colnome " \"" id "\" non è un #numero di todo: crea il todo con arturo todo aggiungi")
    else if (archivio == "1") {
      num = substr(id, 2) + 0
      if (index(" " chiusi " ", " " num " "))
        rosso("riga " NR ": il todo " id " è già chiuso: toglilo dai pendenti")
      else if (!index(" " aperti " ", " " num " "))
        rosso("riga " NR ": il todo " id " non esiste nell\047archivio dei todo")
    }
  }
  if (chiok) {
    chi = (n > 0) ? c[n] : ""
    if (chire != "") {
      if (chi !~ ("^(" chire ")$"))
        rosso("riga " NR ": Chi \"" chi "\" non è fra i valori di hooks/handoff-gate.local")
    } else {
      # Le forme per la persona (/fine FASE 4) valgono la categoria che nominano.
      cat = chi
      if (chi == "Claude") cat = "io"
      else if (chi == "Decidi tu") cat = "decidi"
      else if (chi ~ /^Tu:[ \t]*[^ \t]/) cat = "tu"
      if (!index(" " chi_ammessi " ", " " cat " ") || cat == "")
        rosso("riga " NR ": Chi \"" chi "\" non è una delle categorie ammesse (Claude, Decidi tu, Tu: <cosa serve>, oppure " chi_ammessi ")")
    }
  }
  if (coltask && coltask <= n && guscio(c[coltask]))
    rosso("riga " NR ": Task \"" c[coltask] "\" è un segnaposto: scrivi l\047azione")
  if (coldesc && coldesc <= n && guscio(c[coldesc]))
    rosso("riga " NR ": Descrizione \"" c[coldesc] "\" è un segnaposto: scrivi cosa serve per riprendere")
}

BEGIN {
  RE_GL = "<!--[ \t]*gitleaks:allow[^>]*-->"
  RE_GL_CODA = "\\|[ \t]*<!--[ \t]*gitleaks:allow[^>]*-->[ \t]*$"
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
  sub(/\r$/, "", riga)
  if (riga ~ RE_GL_CODA) {
    sub(RE_GL "[ \t]*$", "", riga)
    print "GATE HANDOFF: avviso: riga " NR ": commento gitleaks dopo l\047ultimo \"|\", ignorato (va dentro la cella, accanto all\047ID)"
  }
  if (!tab) { tab = 1; hdr = 0; cand = riga; candnr = NR; next }
  if (!hdr) {
    hdr = 1
    if (separatore(riga)) { intestazione(cand); next }
    rosso("riga " candnr ": tabella senza riga di separazione sotto l\047intestazione")
    ncol = 0; colid = 0; chiok = 0; coltask = 0; coldesc = 0
    next
  }
  if (separatore(riga)) next
  controlla(riga)
  next
}
dentro { tab = 0 }

END {
  if (!sez) {
    m = "manca la sezione \"## Task Pendenti\", obbligatoria anche senza task"
    if (nq) m = m " (trovato \"" quasi[1] "\" alla riga " quasinr[1] ": il titolo deve essere esatto)"
    else if (dich) m = m " (la frase \"nessun task pendente\" va dentro la sezione)"
    rosso(m)
  }
  if (sez) for (i = 1; i <= nq; i++)
    rosso("riga " quasinr[i] ": titolo \"" quasi[i] "\": il titolo deve essere esatto, \"## Task Pendenti\"")
  if (sez && !righe && !dichsez)
    rosso("la sezione \"## Task Pendenti\" non ha righe e non contiene la frase \"nessun task pendente\"")
  if (bad) exit 1
  print "GATE HANDOFF: verde"
}
' "$1")
RC=$?

if [ -n "$IDEE" ]; then
  OUT=$(printf '%s\n' "$OUT" | grep -v '^GATE HANDOFF: verde$'; printf '%s\n' "$IDEE" | sed 's/^/GATE HANDOFF: rosso: /')
  RC=1
fi
printf '%s\n' "$OUT"
exit "$RC"
