#!/usr/bin/env bash
# Installa Arturo in ~/.claude con una riga sola:
#   curl -fsSL https://arturo.stellakamikaze.org/installa.sh | bash
# Fa il passo 4 della guida (https://arturo.stellakamikaze.org/installa/), con prima i controlli
# dei passi 2 e 3. Una riga regge anche con "!" dentro Claude Code, dove un blocco lungo si spezza.
# Tutto sta in main(): se lo scaricamento si interrompe a metà, non parte niente.
# Bash 3.2 (quello di macOS) e Git Bash su Windows.

main() {
  set -u
  local repo="${ARTURO_REPO:-https://github.com/stellakamikaze/arturo.git}"
  local guida="https://arturo.stellakamikaze.org/installa/"
  local dest="$HOME/.claude"
  local manca=0

  echo "Installo Arturo in $dest"
  echo

  # Passo 2: git e python3 servono subito, node solo alla barra e a qualche strumento.
  if command -v git >/dev/null 2>&1; then
    echo "OK     git"
  else
    echo "MANCA  git"
    manca=1
  fi
  if command -v python3 >/dev/null 2>&1 \
    && python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)' >/dev/null 2>&1; then
    echo "OK     python3"
  else
    echo "MANCA  python3 (serve la 3.8 o successiva)"
    manca=1
  fi
  if [ "$manca" = 1 ]; then
    echo
    if [ "$(uname -s)" = Darwin ]; then
      echo "Lancia xcode-select --install, scegli Installa e aspetta. Poi rilancia questa riga."
    else
      echo "Installa quello che manca come dice il passo 2 della guida, poi rilancia questa riga."
    fi
    echo "Guida: ${guida}#tappa-2"
    return 1
  fi
  if command -v node >/dev/null 2>&1; then
    echo "OK     node"
  else
    echo "MANCA  node: Arturo si installa lo stesso, ma la barra in basso resta vuota."
    echo "       Scarica la versione LTS da https://nodejs.org/it/download e installala."
  fi

  # Passo 3: l'installatore di Claude Code mette claude in ~/.local/bin, ma non sempre lo
  # aggiunge al PATH. Qui si aggiunge, una volta sola, al file della shell.
  local rc=""
  if command -v claude >/dev/null 2>&1; then
    echo "OK     claude"
  elif [ -x "$HOME/.local/bin/claude" ] || [ -x "$HOME/.local/bin/claude.exe" ]; then
    case "$(basename "${SHELL:-bash}")" in
      zsh) rc="$HOME/.zshrc" ;;
      *) rc="$HOME/.bashrc" ;;
    esac
    if grep -qs '\.local/bin' "$rc"; then
      echo "OK     claude, già nel PATH di $rc: si vede da un terminale nuovo"
    else
      printf '\n# Claude Code (aggiunto da Arturo)\nexport PATH="$HOME/.local/bin:$PATH"\n' >>"$rc"
      echo "OK     claude, aggiunto al PATH in $rc"
    fi
  else
    echo "MANCA  claude"
    echo
    echo "Installa prima Claude Code, passo 3 della guida: ${guida}#tappa-3"
    return 1
  fi
  echo

  # Una seconda volta non rifà niente: l'aggiornamento è /aggiorna.
  # Anche come upstream: chi sincronizza Arturo fra più computer ha origin sul suo repository privato.
  if git -C "$dest" remote -v 2>/dev/null | grep -q 'stellakamikaze/arturo'; then
    echo "Arturo è già installato in $dest. Per aggiornarlo scrivi /aggiorna in Claude Code."
    return 0
  fi

  # Passo 4: la cartella che c'è va da parte con la data, Arturo prende il suo posto,
  # e tornano dove erano login, sessioni e plugin di Claude Code, e da un Arturo di prima
  # anche istruzioni, memoria, todo e scelte (la lista più sotto).
  local b=""
  if [ -e "$dest" ]; then
    b="$HOME/.claude-backup-$(date +%Y%m%d-%H%M%S)"
    mv "$dest" "$b" || { echo "Non riesco a spostare $dest: non ho toccato niente."; return 1; }
  fi
  if ! git clone --quiet "$repo" "$dest"; then
    rm -rf "$dest"
    [ -n "$b" ] && mv "$b" "$dest"
    echo
    echo "Lo scaricamento da GitHub non è riuscito. La tua cartella $dest è tornata com'era."
    echo "Controlla la connessione e rilancia questa riga."
    return 1
  fi
  if [ -n "$b" ]; then
    local x
    # Come il blocco del README: da un Arturo installato prima tornano anche istruzioni, memoria, todo
    # e scelte, compresa la telemetria spenta (#3825, 23/10/2026).
    for x in .credentials.json projects history.jsonl plugins file-history jobs daemon agent-memory todos \
      CLAUDE.md settings.local.json personale hooks/hosts-interni.local hooks/bash-dispatcher.local \
      hooks/protect_claude_md.local hooks/api-fidate.local hooks/handoff-gate.local hooks/index-contenitori.local \
      hooks/inventario.local bin/fonte-task.local data/memory data/memoria data/todo \
      data/segnalazioni data/setup-fatto data/aggiornamenti.json session-env/telemetria.json \
      session-env/segnala.json session-env/novita-viste; do
      if [ -e "$b/$x" ] && [ ! -e "$dest/$x" ]; then
        mkdir -p "$(dirname "$dest/$x")" && mv "$b/$x" "$dest/$x"
      fi
    done
  fi

  echo "Arturo installato."
  [ -n "$b" ] && echo "La configurazione di prima è in $b"
  echo
  echo "Arturo manda a chi lo mantiene dati d'uso da un elenco chiuso, mai le tue richieste o i tuoi file."
  echo "Per vedere cosa parte: python3 ~/.claude/bin/arturo telemetria mostra"
  echo "Per spegnerli: python3 ~/.claude/bin/arturo telemetria spegni"
  echo
  echo "Adesso:"
  if [ -n "${CLAUDECODE:-}" ]; then
    echo "1. Chiudi questa sessione di Claude Code con /exit."
  else
    echo "1. Chiudi questo terminale."
  fi
  echo "2. Apri un terminale nuovo e scrivi: cd ~/.claude && claude"
  echo "3. Segui la guida dal passo 5: ${guida}#tappa-5"
}

main "$@"
