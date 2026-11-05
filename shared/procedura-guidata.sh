#!/usr/bin/env bash
#
# Procedura guidata: accompagna una persona, una tappa per volta, nei passi che solo lei può fare
# (un accesso, una chiave da copiare da un sito, un file da scaricare). Claude copia questo file,
# scrive le tappe sotto il segno TAPPE e chiede alla persona di lanciarlo in un Terminale vero:
# col prefisso ! di Claude Code lo script non può leggere quello che la persona scrive.
#
# Sopra il segno TAPPE c'è la libreria: non si modifica. Le tappe si scrivono sotto.
#
# Come lo usa Claude (lo chiamano lo stile Conciso e la guida Google, docs/onboarding/gws.md):
# 1. Serve quando una fase chiede più di tre passi a mano su un sito. Elencati in chat, la persona
#    li perde mentre scorre.
# 2. Copia questo file in ~/.claude/session-env/<nome>.sh e scrivi una tappa per ogni passo.
#    Ogni tappa fa una cosa: apre la pagina, dice cosa cliccare, chiede il valore
#    (chiedi_segreto per chiavi e password, che non si vedono) e lo salva al suo posto.
# 3. Non inventare un passo che non conosci: se non sai com'è fatta la pagina oggi, scrivi cosa
#    cercare. Poi controlla lo script con bash -n.
# 4. Su Mac aprilo tu nel Terminale:
#    osascript -e 'tell application "Terminal" to do script "bash ~/.claude/session-env/<nome>.sh"'
#    Su Windows la persona apre Git Bash e incolla: bash ~/.claude/session-env/<nome>.sh
# 5. Quando la persona torna e scrive "fatto", verifica il risultato e cancella lo script.
#
# Adattato da skills/engineering/wizard/template.sh di mattpocock/skills@4ae2317
# Copyright (c) 2026 Matt Pocock, licenza MIT: https://github.com/mattpocock/skills/blob/main/LICENSE
# Tradotto, senza i segreti di GitHub Actions, con copia_file per i file scaricati.

set -euo pipefail

# --------------------------------------------------------------------------------------------
# Libreria: uguale in ogni procedura.
# --------------------------------------------------------------------------------------------

if [[ -t 1 ]] && command -v tput >/dev/null 2>&1 && [[ "$(tput colors 2>/dev/null || echo 0)" -ge 8 ]]; then
  BOLD=$(tput bold); DIM=$(tput dim); RESET=$(tput sgr0)
  BLUE=$(tput setaf 4); GREEN=$(tput setaf 2); YELLOW=$(tput setaf 3)
else
  BOLD=""; DIM=""; RESET=""; BLUE=""; GREEN=""; YELLOW=""
fi

TOTALE_TAPPE=0
_TAPPA=0
ENV_FILE="${ENV_FILE:-.env}"
SCRITTI=()      # nomi scritti in ENV_FILE in questo giro
COPIATI=()      # file copiati in questo giro
DA_FARE=()      # cose rimaste da fare a mano

_pulisci() {
  [[ -t 1 ]] || return 0
  if command -v tput >/dev/null 2>&1 && tput clear 2>/dev/null; then return 0; fi
  printf '\033[2J\033[3J\033[H'
}

# inizio "Titolo": la schermata di apertura.
inizio() {
  _pulisci
  printf '\n%s%s  %s%s\n' "$BOLD" "$BLUE" "$1" "$RESET"
  printf '%s  %s tappe%s\n\n' "$DIM" "$TOTALE_TAPPE" "$RESET"
  printf '%s  Il browser lo usi tu: qui leggi cosa cliccare e incolli quello che copi.\n' "$DIM"
  printf '  Puoi fermarti quando vuoi con Ctrl-C e ripartire dopo: i valori salvati restano.%s\n' "$RESET"
  pausa "Pronto? Premi Invio."
}

# tappa "Nome": pulisce lo schermo e mostra a che punto sei.
tappa() {
  _pulisci
  _TAPPA=$((_TAPPA + 1))
  printf '\n%s%s> Tappa %s di %s: %s%s\n\n' "$BOLD" "$BLUE" "$_TAPPA" "$TOTALE_TAPPE" "$1" "$RESET"
}

di()     { printf '  %s\n' "$1"; }
passo()  { printf '  %s-%s %s\n' "$BLUE" "$RESET" "$1"; }
nota()   { printf '  %s%s%s\n' "$DIM" "$1" "$RESET"; }
avviso() { printf '  %s! %s%s\n' "$YELLOW" "$1" "$RESET"; }

# apri URL: apre la pagina nel browser della persona (Mac, Linux, Windows con Git Bash o WSL).
apri() {
  local url="$1"
  printf '  %sApro%s %s\n' "$GREEN" "$RESET" "$url"
  { if   command -v wslview      >/dev/null 2>&1; then wslview "$url"
    elif command -v explorer.exe >/dev/null 2>&1; then explorer.exe "$url"
    elif command -v xdg-open     >/dev/null 2>&1; then xdg-open "$url"
    elif command -v open         >/dev/null 2>&1; then open "$url"
    else false; fi
  } >/dev/null 2>&1 || avviso "Non riesco ad aprire il browser: apri tu questa pagina, $url"
}

# pausa "messaggio": aspetta che la persona abbia fatto la parte a mano.
pausa() {
  printf '  %s%s%s ' "$DIM" "${1:-Premi Invio per andare avanti.}" "$RESET"
  read -r _ || true
}

# conferma "domanda": sì o no; riesce solo col sì. Va prima di ogni passo che non si annulla.
conferma() {
  local r=""
  printf '  %s? %s%s [s/N] ' "$YELLOW" "$1" "$RESET"
  read -r r || true
  [[ "$r" =~ ^[SsYy] ]]
}

_esistente() {
  [[ -f "$ENV_FILE" ]] || return 1
  # La virgoletta sta in una variabile: bash 3.2 del Mac terrebbe la barra di \'.
  local riga v sq="'\\''" q="'"; riga=$(grep -E "^${1}=" "$ENV_FILE" | tail -n1) || return 1
  v="${riga#*=}"
  if [[ "$v" == \'*\' ]]; then v="${v:1:${#v}-2}"; v="${v//"$sq"/$q}"
  elif [[ "$v" == \"*\" ]]; then
    v="${v:1:${#v}-2}"
    [[ "$v" == *[\\\$\"]* ]] && return 1
  fi
  printf '%s' "$v"
}

# chiedi NOME "Domanda": legge un valore visibile in $NOME. Invio tiene quello già salvato.
chiedi() {
  local nome="$1" domanda="$2" attuale input s=$'\001' e=$'\002' p rc=0
  attuale=$(_esistente "$nome" || true)
  p="  $s$BOLD$e$domanda$s$RESET$e "
  [[ -n "$attuale" ]] && p+="$s$DIM$e[Invio tiene quello salvato]$s$RESET$e "
  read -e -r -p "$p" input || rc=1
  if (( rc )) && [[ -z "$input" ]]; then return 1; fi
  [[ -z "$input" && -n "$attuale" ]] && input="$attuale"
  printf -v "$nome" '%s' "$input"
}

# chiedi_segreto NOME "Domanda": come chiedi, ma quello che incolli non si vede.
chiedi_segreto() {
  local nome="$1" domanda="$2" attuale input rc=0
  attuale=$(_esistente "$nome" || true)
  if [[ -n "$attuale" ]]; then
    printf '  %s%s%s %s[Invio tiene quello salvato]%s ' "$BOLD" "$domanda" "$RESET" "$DIM" "$RESET"
  else
    printf '  %s%s%s ' "$BOLD" "$domanda" "$RESET"
  fi
  read -rs input || rc=1
  printf '\n'
  if (( rc )) && [[ -z "$input" ]]; then return 1; fi
  [[ -z "$input" && -n "$attuale" ]] && input="$attuale"
  printf -v "$nome" '%s' "$input"
}

# salva NOME VALORE: scrive NOME='VALORE' in ENV_FILE, al posto della riga vecchia.
# Crea il file leggibile solo dalla persona (0600).
salva() {
  local nome="$1" valore="$2" tmp sq="'\\''"
  [[ -e "$ENV_FILE" ]] || (umask 077 && : > "$ENV_FILE")
  tmp=$(mktemp)
  grep -vE "^${nome}=" "$ENV_FILE" > "$tmp" || true
  printf "%s='%s'\n" "$nome" "${valore//\'/$sq}" >> "$tmp"
  cat "$tmp" > "$ENV_FILE"
  rm -f "$tmp"
  printf -v "$nome" '%s' "$valore"
  SCRITTI+=("$nome")
  printf '  %s[ok]%s %s salvato in %s\n' "$GREEN" "$RESET" "$nome" "$ENV_FILE"
}

# copia_file SORGENTE DESTINAZIONE: copia un file scaricato al suo posto, leggibile solo dalla
# persona. Se SORGENTE non c'è, lo segna fra le cose da fare a mano.
copia_file() {
  local da="$1" a="$2"
  da="${da/#\~/$HOME}"; a="${a/#\~/$HOME}"
  if [[ ! -f "$da" ]]; then
    DA_FARE+=("copiare il file in $a: non ho trovato $da")
    avviso "Non trovo $da"
    return 0
  fi
  mkdir -p "$(dirname "$a")"
  (umask 077 && cp "$da" "$a")
  chmod 600 "$a" 2>/dev/null || true
  COPIATI+=("$a")
  printf '  %s[ok]%s copiato in %s\n' "$GREEN" "$RESET" "$a"
}

# fine: il riepilogo di quello che è stato fatto e di quello che resta.
fine() {
  _pulisci
  printf '\n%s%s  Fatto.%s\n' "$BOLD" "$GREEN" "$RESET"
  if (( ${#SCRITTI[@]} )); then nota "Valori salvati in $ENV_FILE: ${SCRITTI[*]}"; fi
  if (( ${#COPIATI[@]} )); then nota "File copiati: ${COPIATI[*]}"; fi
  if (( ${#DA_FARE[@]} )); then
    printf '\n'; avviso "Resta da fare a mano:"
    for c in "${DA_FARE[@]}"; do nota "  - $c"; done
  fi
  printf '\n  Torna su Claude Code e scrivi "fatto".\n\n'
}

# --------------------------------------------------------------------------------------------
# TAPPE: le scrive Claude. Una tappa() per ogni cosa che la persona fa, nell'ordine giusto.
# Sostituisci l'esempio e metti in TOTALE_TAPPE il numero delle tappe. Tutto resta dentro
# procedura(): bash legge il file intero prima della prima domanda.
# --------------------------------------------------------------------------------------------

procedura() {

TOTALE_TAPPE=1

inizio "Esempio: la chiave di un servizio"

tappa "La chiave"
di "Prendiamo la chiave del servizio e la salviamo in un file che leggi solo tu."
apri "https://example.com/impostazioni/chiavi"
passo "Clicca su Crea chiave, poi su Copia."
chiedi_segreto CHIAVE_SERVIZIO "Incolla la chiave e premi Invio:"
salva CHIAVE_SERVIZIO "$CHIAVE_SERVIZIO"

fine
}

procedura "$@"; exit
