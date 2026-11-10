#!/bin/sh
# La nascita in background di Volta Celeste (#5172 passi 2 e 3): un blocco marcato nel file di avvio della
# shell che fa passare il comando claude da volta-claude. zsh e bash sul Mac, il profilo di PowerShell
# (Windows PowerShell 5.1 e PowerShell 7) su Windows. Si toglie come si mette.
#
# Uso: nascita.sh metti [cartella di Herdr] | togli | no | stato
#   metti  scrive il blocco nei file della persona, o lo riscrive se c'è già, e dimentica un no di prima;
#   togli  toglie il blocco da tutti i file, e il resto dei file resta com'era;
#   no     toglie il blocco e ricorda il no: l'installatore non ripropone la nascita;
#   stato  stampa "presente <file>" per ogni blocco, "assente" se non ce n'è, "rifiutata" dopo un no,
#          "funzione <file>" per ogni funzione claude della persona fuori dal blocco,
#          "policy <file> <valore>" se PowerShell non legge i profili (ExecutionPolicy Restricted o AllSigned),
#          "utf16 <file>" per un profilo in UTF-16, che il blocco non tocca.
# La cartella di Herdr, se manca, è quella di questo file (installato come ~/.config/herdr-app/volta-nascita.sh).
# Una funzione claude della persona vince sul blocco: per avere la nascita in background la fa finire
# con la chiamata a volta-claude (docs/volta-celeste.md).
#
# Per i banchi: VOLTA_PROFILI_PS (i profili di PowerShell, uno per riga, al posto di quelli che dice
# PowerShell) e VOLTA_POLICY_PS (la ExecutionPolicy, al posto di quella che dice PowerShell).
set -eu

INIZIO='# >>> Volta Celeste: le sessioni di claude nascono in background >>>'
FINE='# <<< Volta Celeste <<<'
say() { printf '%s\n' "$*"; }
app=$(cd "$(dirname "$0")" && pwd)
NO="$app/nascita-no"

windows() { case "$(uname -s)" in MINGW* | MSYS* | CYGWIN*) return 0 ;; esac; return 1; }
# Percorsi in forma Windows (C:/Users/...) per PowerShell, uguali altrove.
percorso() { if command -v cygpath >/dev/null 2>&1; then cygpath -m "$1"; else printf '%s' "$1"; fi; }

# I file di avvio della shell della persona: quelli che ci sono, più quello della sua shell.
# Su Windows no: lì il terminale di tutti i giorni è PowerShell, e Git Bash non ha sempre un terminale vero.
file_shell() {
  windows && return 0
  conchiglia=$(basename "${SHELL:-}")
  if [ -f "$HOME/.zshrc" ] || [ "$conchiglia" = zsh ]; then say "$HOME/.zshrc"; fi
  if [ -f "$HOME/.bashrc" ] || [ "$conchiglia" = bash ]; then say "$HOME/.bashrc"; fi
}

# I profili di PowerShell della persona (CurrentUserCurrentHost), uno per programma installato.
# Fuori da Windows non ce ne sono, salvo nei banchi.
profili_ps() {
  if [ -n "${VOLTA_PROFILI_PS+x}" ]; then
    [ -n "$VOLTA_PROFILI_PS" ] && printf '%s\n' "$VOLTA_PROFILI_PS"
    return 0
  fi
  windows || return 0
  for ps in powershell pwsh; do
    command -v "$ps" >/dev/null 2>&1 || continue
    p=$("$ps" -NoProfile -NonInteractive -Command '$PROFILE.CurrentUserCurrentHost' 2>/dev/null </dev/null | tr -d '\r')
    [ -n "$p" ] && { cygpath -u "$p" 2>/dev/null || say "$p"; }
  done
}

# La ExecutionPolicy del programma del profilo: con Restricted o AllSigned PowerShell non legge il profilo.
policy_ps() {
  if [ -n "${VOLTA_POLICY_PS:-}" ]; then say "$VOLTA_POLICY_PS"; return 0; fi
  windows || { say Unrestricted; return 0; }
  case "$1" in */WindowsPowerShell/*) ps=powershell ;; *) ps=pwsh ;; esac
  "$ps" -NoProfile -NonInteractive -Command 'Get-ExecutionPolicy' 2>/dev/null </dev/null | tr -d '\r'
}

# Un profilo salvato da Windows PowerShell con > è in UTF-16: aggiungere righe in UTF-8 lo rovinerebbe.
utf16() { [ -s "$1" ] && case "$(head -c 2 "$1" | od -An -tx1 | tr -d ' \n')" in fffe | feff) return 0 ;; esac; return 1; }

tutti_i_file() { say "$HOME/.zshrc"; say "$HOME/.bashrc"; profili_ps; }

togli_da() {
  f=$1
  [ -f "$f" ] && grep -qF "$INIZIO" "$f" || return 0
  tmp="$f.volta-tmp"
  # \r tolto nel confronto: un profilo di PowerShell può avere le righe di Windows. BINMODE=3: l'awk di Git
  # per Windows altrimenti toglie i \r anche dalle righe della persona (provato il 10/11/2026); altrove non conta.
  awk -v BINMODE=3 -v a="$INIZIO" -v b="$FINE" '{ l = $0; sub(/\r$/, "", l) } l == a { dentro = 1; next } dentro && l == b { dentro = 0; next } !dentro' "$f" > "$tmp"
  cat "$tmp" > "$f"  # cat e non mv: permessi e collegamenti del file restano quelli della persona
  rm -f "$tmp"
}

# Un file che non finisce con a capo attaccherebbe il blocco alla sua ultima riga.
a_capo() { if [ -s "$1" ] && [ -n "$(tail -c 1 "$1" | tr -d '\r')" ]; then printf '\n' >> "$1"; fi; }

blocco_sh() {
  say "$INIZIO"
  say "# Il comando claude apre le sessioni in background, così Volta le vede da ogni macchina."
  say "# CLAUDE_QUI=1 claude apre una sessione qui come prima. Per togliere: sh \"$app/volta-nascita.sh\" togli"
  say "if [ -x \"$app/volta-claude\" ] && ! typeset -f claude >/dev/null 2>&1; then"
  say "  claude() { \"$app/volta-claude\" \"\$@\"; }"
  say "fi"
  say "$FINE"
}

# Solo ASCII: Windows PowerShell 5.1 legge un profilo senza BOM come ANSI, e le lettere accentate si rovinano.
blocco_ps() {
  ps1="$(percorso "$app")/volta-claude.ps1"
  say "$INIZIO"
  say "# Il comando claude apre le sessioni in background, che Volta vede da ogni macchina."
  say "# \$env:CLAUDE_QUI = 1 apre una sessione qui come prima. Per togliere: sh \"$(percorso "$app")/volta-nascita.sh\" togli"
  say "if ((Test-Path -LiteralPath '$ps1') -and -not (Get-Command claude -CommandType Function -ErrorAction SilentlyContinue)) {"
  say "  function global:claude { & '$ps1' @args }"
  say "}"
  say "$FINE"
}

case "${1:-}" in
  metti)
    app=$(cd "${2:-$app}" && pwd)
    rm -f "$NO" "$app/nascita-no"
    IFS='
'  # una riga per file: la casa può avere spazi nel nome (C:/Users/Mario Rossi)
    for f in $(file_shell); do
      togli_da "$f"
      a_capo "$f"
      blocco_sh >> "$f"
      say "NASCITA METTI $f"
    done
    for f in $(profili_ps); do
      if utf16 "$f"; then say "NASCITA UTF16 $f"; continue; fi
      mkdir -p "$(dirname "$f")"
      togli_da "$f"
      a_capo "$f"
      blocco_ps >> "$f"
      say "NASCITA METTI $f"
    done
    ;;
  togli | no)
    IFS='
'
    for f in $(tutti_i_file); do
      if [ -f "$f" ] && grep -qF "$INIZIO" "$f"; then togli_da "$f"; say "NASCITA TOLTA $f"; fi
    done
    if [ "$1" = no ]; then date '+%Y-%m-%d' > "$NO"; say "NASCITA NO: l'installazione non la ripropone. Si accende con: sh \"$app/volta-nascita.sh\" metti"; fi
    ;;
  stato)
    IFS='
'
    trovato=""
    for f in $(tutti_i_file); do
      if [ -f "$f" ] && grep -qF "$INIZIO" "$f"; then say "presente $f"; trovato=1; fi
    done
    [ -n "$trovato" ] || say "assente"
    [ -f "$NO" ] && say "rifiutata"
    for f in "$HOME/.zshenv" "$HOME/.zshrc" "$HOME/.zprofile" "$HOME/.bashrc" "$HOME/.bash_profile" "$HOME/.profile"; do
      [ -f "$f" ] || continue
      if awk -v a="$INIZIO" -v b="$FINE" '$0 == a { d = 1 } $0 == b { d = 0; next } !d && /^[[:space:]]*(function[[:space:]]+)?claude[[:space:]]*\(\)/ { t = 1 } END { exit !t }' "$f"; then
        say "funzione $f"
      fi
    done
    for f in $(profili_ps); do
      if utf16 "$f"; then say "utf16 $f"; continue; fi
      if [ -f "$f" ] && awk -v a="$INIZIO" -v b="$FINE" '{ l = $0; sub(/\r$/, "", l) } l == a { d = 1 } l == b { d = 0; next } !d && tolower(l) ~ /^[[:space:]]*function[[:space:]]+(global:)?claude([[:space:]]|\{|$)/ { t = 1 } END { exit !t }' "$f"; then
        say "funzione $f"
      fi
      pol=$(policy_ps "$f")
      case "$pol" in Restricted | AllSigned) say "policy $f $pol" ;; esac
    done
    ;;
  *) say "uso: nascita.sh metti [cartella di Herdr] | togli | no | stato"; exit 2 ;;
esac
