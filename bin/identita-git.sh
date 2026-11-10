#!/usr/bin/env bash
# identita-git.sh: l'identità di Git che /setup sceglie, valida in ogni repository della persona.
#
# /setup la scriveva solo in ~/.claude: col plugin ~/.claude non è un repository, e i commit dei progetti
# (/inizio, /fine) restavano senza nome. `git config --global` è negato da Arturo. L'identità sta quindi in
# un file di Arturo, ~/.claude/arturo/git-identita, e si copia nel repository che ne ha bisogno (review del
# 7/11/2026, finding 79 e 80).
#
#   identita-git.sh --controlla            stampa MANCA se né il computer né Arturo hanno un'email
#   identita-git.sh --imposta NOME [EMAIL] la scrive; senza EMAIL una finta, NOME@arturo.local
#   identita-git.sh CARTELLA               se git in CARTELLA non trova un'email, copia quella di Arturo;
#                                          senza neanche quella, accetta l'identità automatica di Git
#                                          con un AVVISO
#
# Uscite: 0 a posto (anche con AVVISO), 1 identità mancante, 2 uso sbagliato.
set -uo pipefail

ORSA="${CLAUDE_CONFIG_DIR:-$HOME/.claude}"
FILE="$ORSA/arturo/git-identita"

# L'identità di Arturo: il file, oppure quella che un /setup di prima ha scritto nel clone in ~/.claude.
leggi() {
  git config --file "$FILE" "user.$1" 2>/dev/null \
    || { [ -e "$ORSA/.git" ] && git -C "$ORSA" config --local "user.$1" 2>/dev/null; }
}

case "${1:-}" in
  --controlla)
    # Da HOME: l'identità di un repository aperto non vale per gli altri.
    if (cd "$HOME" 2>/dev/null && git config user.email >/dev/null 2>&1) || [ -n "$(leggi email)" ]; then
      exit 0
    fi
    echo "MANCA l'identità di Git"
    exit 1 ;;
  --imposta)
    NOME="${2:-}"
    [ -n "$NOME" ] || { echo "uso: identita-git.sh --imposta NOME [EMAIL]" >&2; exit 2; }
    EMAIL="${3:-$(printf '%s' "$NOME" | tr '[:upper:] ' '[:lower:]-')@arturo.local}"
    mkdir -p "$(dirname "$FILE")"
    git config --file "$FILE" user.name "$NOME" && git config --file "$FILE" user.email "$EMAIL" || exit 1
    # Col clone anche ~/.claude è un repository: /fine ci committa.
    if [ -e "$ORSA/.git" ]; then
      git -C "$ORSA" config user.name "$NOME" && git -C "$ORSA" config user.email "$EMAIL"
    fi
    echo "identità di Git: $NOME <$EMAIL>" ;;
  -*|"")
    echo "uso: identita-git.sh --controlla | --imposta NOME [EMAIL] | CARTELLA" >&2
    exit 2 ;;
  *)
    CARTELLA="$1"
    git -C "$CARTELLA" rev-parse --git-dir >/dev/null 2>&1 || { echo "$CARTELLA non è un repository Git" >&2; exit 2; }
    git -C "$CARTELLA" config user.email >/dev/null 2>&1 && exit 0
    NOME="$(leggi name)"; EMAIL="$(leggi email)"
    if [ -z "$EMAIL" ]; then
      # Git ricava da solo un'identità da utente e computer, e il commit parte: non fermare /fine per
      # questo, ma dillo (segnalazione n. 67, 10/11/2026). Fallisce come il commit con useConfigOnly.
      AUTO="$(git -C "$CARTELLA" var GIT_AUTHOR_IDENT 2>/dev/null | sed 's/ [0-9]* [-+][0-9]*$//')"
      if [ -n "$AUTO" ]; then
        echo "AVVISO: il commit usa l'identità automatica di Git, $AUTO. Per un nome tuo: /setup, FASE 1"
        exit 0
      fi
      echo "MANCA l'identità di Git: la sceglie /setup, FASE 1"
      exit 1
    fi
    git -C "$CARTELLA" config user.name "${NOME:-$EMAIL}" && git -C "$CARTELLA" config user.email "$EMAIL" ;;
esac
