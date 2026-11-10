#!/bin/sh
# La nascita in background di Volta Celeste (#5172 passo 2): un blocco marcato nel file di avvio della
# shell (zsh e bash) che fa passare il comando claude da volta-claude. Si toglie come si mette.
#
# Uso: nascita.sh metti <cartella di Herdr> | togli | stato
#   metti  scrive il blocco in ~/.zshrc e ~/.bashrc (quelli che la persona usa), o lo riscrive se c'è già;
#   togli  toglie il blocco da tutti e due, e il resto del file resta com'era;
#   stato  stampa "presente <file>" per ogni blocco, "assente" se non ce n'è,
#          e "funzione <file>" per ogni funzione claude della persona fuori dal blocco.
# Una funzione claude della persona vince sul blocco: per avere la nascita in background la fa finire
# con la chiamata a volta-claude (docs/volta-celeste.md).
set -eu

INIZIO='# >>> Volta Celeste: le sessioni di claude nascono in background >>>'
FINE='# <<< Volta Celeste <<<'
say() { printf '%s\n' "$*"; }

# I file di avvio della shell della persona: quelli che ci sono, più quello della sua shell.
file_shell() {
  conchiglia=$(basename "${SHELL:-}")
  if [ -f "$HOME/.zshrc" ] || [ "$conchiglia" = zsh ]; then say "$HOME/.zshrc"; fi
  if [ -f "$HOME/.bashrc" ] || [ "$conchiglia" = bash ]; then say "$HOME/.bashrc"; fi
}

togli_da() {
  f=$1
  [ -f "$f" ] && grep -qF "$INIZIO" "$f" || return 0
  tmp="$f.volta-tmp"
  awk -v a="$INIZIO" -v b="$FINE" '$0 == a { dentro = 1; next } dentro && $0 == b { dentro = 0; next } !dentro' "$f" > "$tmp"
  cat "$tmp" > "$f"  # cat e non mv: permessi e collegamenti del file restano quelli della persona
  rm -f "$tmp"
}

case "${1:-}" in
  metti)
    app=${2:?manca la cartella di Herdr}
    IFS='
'  # una riga per file: la casa può avere spazi nel nome (C:/Users/Mario Rossi)
    for f in $(file_shell); do
      togli_da "$f"
      # un file che non finisce con a capo attaccherebbe il blocco alla sua ultima riga
      if [ -s "$f" ] && [ -n "$(tail -c 1 "$f")" ]; then printf '\n' >> "$f"; fi
      {
        say "$INIZIO"
        say "# Il comando claude apre le sessioni in background, così Volta le vede da ogni macchina."
        say "# CLAUDE_QUI=1 claude apre una sessione qui come prima. Per togliere: sh \"$app/volta-nascita.sh\" togli"
        say "if [ -x \"$app/volta-claude\" ] && ! typeset -f claude >/dev/null 2>&1; then"
        say "  claude() { \"$app/volta-claude\" \"\$@\"; }"
        say "fi"
        say "$FINE"
      } >> "$f"
      say "NASCITA METTI $f"
    done
    ;;
  togli)
    for f in "$HOME/.zshrc" "$HOME/.bashrc"; do
      if [ -f "$f" ] && grep -qF "$INIZIO" "$f"; then togli_da "$f"; say "NASCITA TOLTA $f"; fi
    done
    ;;
  stato)
    trovato=""
    for f in "$HOME/.zshrc" "$HOME/.bashrc"; do
      if [ -f "$f" ] && grep -qF "$INIZIO" "$f"; then say "presente $f"; trovato=1; fi
    done
    [ -n "$trovato" ] || say "assente"
    for f in "$HOME/.zshenv" "$HOME/.zshrc" "$HOME/.zprofile" "$HOME/.bashrc" "$HOME/.bash_profile" "$HOME/.profile"; do
      [ -f "$f" ] || continue
      if awk -v a="$INIZIO" -v b="$FINE" '$0 == a { d = 1 } $0 == b { d = 0; next } !d && /^[[:space:]]*(function[[:space:]]+)?claude[[:space:]]*\(\)/ { t = 1 } END { exit !t }' "$f"; then
        say "funzione $f"
      fi
    done
    ;;
  *) say "uso: nascita.sh metti <cartella di Herdr> | togli | stato"; exit 2 ;;
esac
