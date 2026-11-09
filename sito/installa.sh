#!/usr/bin/env bash
# Installa Arturo in ~/.claude, sul posto.
# Strada consigliata: Claude Code scarica questo file e lo lancia, come dice
# https://arturo.stellakamikaze.org/inizia/
# Strada a mano, da un terminale con Claude Code chiuso:
#   curl -fsSL https://arturo.stellakamikaze.org/installa.sh | bash
#
# Arturo entra dentro ~/.claude senza spostare la cartella: login, conversazioni, file dei plugin e
# file della persona restano dove sono, anche con una sessione di Claude Code aperta. Prima di
# scrivere, i file che Arturo sostituisce vanno in ~/.claude-backup-<data>, copiati e controllati
# con cmp. Fra questi c'è settings.json, con i plugin accesi e le preferenze: /setup li ripropone
# con `arturo personale hook-precedenti`. Se l'innesto non riesce, lo script rimette tutto com'era.
# Ogni programma che manca esce in una riga "MANCA <cosa>. Comando: <comando>": l'uscita di Bash
# arriva a Claude parola per parola, una pagina web no.
# Tutto sta in main(): se lo scaricamento si interrompe a metà, non parte niente.
# Bash 3.2 (quello di macOS) e Git Bash su Windows. Niente sudo.

# La chiave che firma i rilasci: la stessa riga di firme/rilasci.allowed_signers su main (il banco la
# confronta). Lo script installa solo il commit dell'ultimo tag firmato da questa chiave, mai la punta di
# main. Per cambiare chiave: docs/manutenzione.md, e questa riga cambia insieme.
FIRMA_RILASCI='rilasci@arturo namespaces="git,arturo-manifest" ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIP0HfWu3Wxkq0+trFJ6S7P7MZmo2OXRlVKkgTKXI74K5'
# Il rilascio più vecchio che lo script accetta, contro un main riportato indietro a un tag firmato con
# un buco già chiuso. Si alza quando un rilascio chiude un buco grave.
VERSIONE_MINIMA=0.2.8
# Gli errori di verify-tag che dicono "firma verificata e sbagliata": uguali a FIRMA_SBAGLIATA di
# bin/aggiornamenti.py. Ogni altro errore vuol dire che la verifica non è partita.
FIRMA_SBAGLIATA='no signature found|no principal matched|could not verify signature|bad signature|non-tag object'

ARTURO_TMP=""
ARTURO_INNESTO=0
# La copia di sicurezza mentre si scrive: un'interruzione prima dell'innesto la toglie.
ARTURO_BACKUP=""

pulisci_tmp() {
  [ -n "$ARTURO_TMP" ] && rm -rf "$ARTURO_TMP"
  ARTURO_TMP=""
}

# Rimette ~/.claude com'era prima dell'innesto. Usa le variabili di main() (dest, b, nuovi, salvati,
# cartelle, creata, spostato): bash le vede perché rimetti() parte da dentro main().
rimetti() {
  local p tolte=1 errori=0
  ARTURO_INNESTO=0
  [ "$spostato" = 1 ] && rm -rf "$dest/.git"
  for p in ${nuovi[@]+"${nuovi[@]}"}; do
    rm -f "$dest/$p"
  done
  # Le cartelle nate con l'innesto: rmdir toglie solo quelle vuote, e si ripete finché ne toglie.
  while [ "$tolte" = 1 ]; do
    tolte=0
    for p in ${cartelle[@]+"${cartelle[@]}"}; do
      if [ -d "$dest/$p" ] && rmdir "$dest/$p" 2>/dev/null; then
        tolte=1
      fi
    done
  done
  for p in ${salvati[@]+"${salvati[@]}"}; do
    rm -f "$dest/$p"
    if ! cp -pP "$b/$p" "$dest/$p"; then
      errori=1
      echo "Non riesco a rimettere $dest/$p: la copia è in $b/$p"
    fi
  done
  [ "$creata" = 1 ] && rmdir "$dest" 2>/dev/null
  pulisci_tmp
  echo
  if [ "$errori" = 1 ]; then
    echo "L'installazione non è riuscita e non tutto è tornato a posto: i file sopra vanno ricopiati a mano."
    echo "Il backup resta in $b"
  elif [ "$nsalvati" = 0 ]; then
    rm -rf "$b"
    echo "L'installazione non è riuscita: ho rimesso tutto com'era."
  else
    echo "L'installazione non è riuscita: ho rimesso tutto com'era. Il backup resta in $b"
  fi
}

# Ctrl-C, Esc o TERM. Durante l'innesto rimette tutto com'era. Prima, durante la copia di sicurezza,
# toglie la copia parziale: hook-precedenti legge l'ultima ~/.claude-backup-*, e una copia monca
# finirebbe in /setup.
interrotto() {
  if [ "$ARTURO_INNESTO" = 1 ]; then
    rimetti
  elif [ -n "$ARTURO_BACKUP" ]; then
    rm -rf "$ARTURO_BACKUP"
    echo
    echo "Interrotto durante la copia di sicurezza: ho tolto la copia parziale $ARTURO_BACKUP. Non ho toccato ~/.claude."
    ARTURO_BACKUP=""
  fi
  pulisci_tmp
  exit 130
}

# Il file scaricato da Claude Code serve una volta sola.
cancella_me() {
  local f="$HOME/.arturo-installa.sh"
  if [ "$0" = "$f" ] || { [ -f "$f" ] && [ "$0" -ef "$f" ]; }; then
    rm -f "$f"
  fi
}

# Vero se il tag vX.Y.Z ($1) non è più vecchio di X.Y.Z ($2).
versione_almeno() {
  local a b c x y z
  case "${1#v}" in
    *[!0-9.]* | *..* | .* | *.) return 1 ;;
  esac
  IFS=. read -r a b c <<EOF
${1#v}
EOF
  IFS=. read -r x y z <<EOF
$2
EOF
  [ -n "$a" ] && [ -n "$b" ] && [ -n "$c" ] || return 1
  [ "$a" -ne "$x" ] && { [ "$a" -gt "$x" ]; return; }
  [ "$b" -ne "$y" ] && { [ "$b" -gt "$y" ]; return; }
  [ "$c" -ge "$z" ]
}

# Il rilascio da installare nel clone $1: l'ultimo tag vX.Y.Z di origin/main, annotato, firmato dalla
# chiave in $2, col suo nome scritto dentro (la firma copre quel nome, non il ref: un tag vecchio
# ripubblicato con un nome nuovo ha una firma valida) e non più vecchio di VERSIONE_MINIMA.
# Scrive il tag in $rilascio. Esito 0 buono, 1 compromissione (messaggio già stampato), 2 la verifica
# non è partita (git o OpenSSH vecchi).
# Il filtro vX.Y.Z è più stretto di ultimo_tag di bin/aggiornamenti.py (v*), di proposito: qui il nome
# si confronta con VERSIONE_MINIMA e deve essere un numero. Un tag v-qualcosa senza numero questo script
# lo salta; aggiornamenti.py lo prende come ultimo rilascio e, senza firma, lo dice possibile compromissione.
verifica_rilascio() {
  local clone="$1" firme="$2" errore dentro
  rilascio=$(git -C "$clone" describe --tags --abbrev=0 --match 'v[0-9]*.[0-9]*.[0-9]*' origin/main 2>/dev/null)
  if [ -z "$rilascio" ]; then
    echo "Su GitHub non trovo nessun rilascio di Arturo con la firma: possibile compromissione. Non ho toccato niente: segnala a chi mantiene Arturo."
    return 1
  fi
  # Un tag annotato col nome diverso da quello scritto dentro: describe lo dà col nome di dentro e un
  # suffisso (v0.9.0-0-g…). Il controllo su $dentro più sotto copre lo stesso caso se describe cambia.
  case "$rilascio" in
    *-g[0-9a-f]*)
      echo "Su GitHub c'è il rilascio firmato ${rilascio%%-*} ripubblicato con un altro nome: possibile compromissione. Non ho toccato niente: segnala a chi mantiene Arturo."
      return 1
      ;;
  esac
  if [ "$(git -C "$clone" cat-file -t "refs/tags/$rilascio" 2>/dev/null)" != tag ]; then
    echo "Il rilascio $rilascio non ha la firma di Arturo (tag senza firma): possibile compromissione. Non ho toccato niente: segnala a chi mantiene Arturo."
    return 1
  fi
  if ! errore=$(LC_ALL=C git -C "$clone" -c gpg.format=ssh -c gpg.ssh.allowedSignersFile="$firme" \
    verify-tag "$rilascio" 2>&1 >/dev/null); then
    if printf '%s\n' "$errore" | grep -Eiq "$FIRMA_SBAGLIATA"; then
      echo "Il rilascio $rilascio non ha la firma di Arturo: possibile compromissione. Non ho toccato niente: segnala a chi mantiene Arturo."
      return 1
    fi
    return 2
  fi
  dentro=$(git -C "$clone" cat-file tag "$rilascio" 2>/dev/null | sed -n 's/^tag //p' | head -n 1)
  if [ "$dentro" != "$rilascio" ]; then
    echo "Il tag $rilascio è il rilascio firmato ${dentro:-senza nome} ripubblicato con un altro nome: possibile compromissione. Non ho toccato niente: segnala a chi mantiene Arturo."
    return 1
  fi
  if ! versione_almeno "$rilascio" "$VERSIONE_MINIMA"; then
    echo "Su GitHub l'ultimo rilascio è $rilascio, più vecchio della $VERSIONE_MINIMA che questo script conosce: possibile compromissione. Non ho toccato niente: segnala a chi mantiene Arturo."
    return 1
  fi
  return 0
}

python3_ok() {
  command -v python3 >/dev/null 2>&1 \
    && python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)' >/dev/null 2>&1
}

# Su Windows python3 deve eseguire davvero. Sonda su Balthasar (Windows 11, 1/11/2026):
# - WindowsApps\python3.exe e python.exe sono il rimando di App Installer: stampano "Python non è
#   stato trovato" ed escono con 49, senza eseguire niente.
# - L'installatore di python.org mette python.exe e pythonw.exe, mai python3.exe (C:\Python312 e
#   Python313 ne sono senza). Python311 ha python3.exe come hardlink di python.exe, fatto a mano, e gira.
# - winget installa Python.Python.3.12 con PrependPath=1 (manifest 3.12.10): la cartella va in testa
#   al Path utente, quindi davanti a WindowsApps. Un python3.exe nella stessa cartella vince sul rimando.
# - Gli hook di Arturo partono con bash dal Path di Windows. ~/bin entra nel PATH solo col lanciatore
#   Git\bin\bash.exe o con /etc/profile.d/env.sh delle shell di login: non è una base sicura.
# - Prova: un venv senza python3.exe, poi `ln python.exe python3.exe` di Git Bash fa un hardlink
#   (2 collegamenti), e `python3` trova il nuovo file e gira.
# Qui: per ogni python vero (nel PATH o da py -3) si crea python3.exe accanto, e si tiene solo se
# `python3` adesso gira. Esito 0 fatto, 2 un python vero c'è ma il rimando gli sta davanti, 3 la
# cartella non si lascia scrivere (in $bloccata), 1 nessun python vero.
crea_python3() {
  local cand dir exe elenco ombra=0 prima="$IFS" a_capo='
'
  elenco=$(type -ap python 2>/dev/null)
  if command -v py >/dev/null 2>&1; then
    exe=$(py -3 -c 'import sys; print(sys.executable)' 2>/dev/null | tr -d '\r')
    if [ -n "$exe" ] && command -v cygpath >/dev/null 2>&1; then
      exe=$(cygpath -u "$exe" 2>/dev/null)
    fi
    [ -n "$exe" ] && elenco="$elenco$a_capo${exe%.exe}"
  fi
  IFS="$a_capo"
  for cand in $elenco; do
    IFS="$prima"
    case "$cand" in
      */WindowsApps/* | "") continue ;;
    esac
    "$cand" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)' >/dev/null 2>&1 || continue
    dir="${cand%/*}"
    [ -f "$dir/python.exe" ] || continue
    if [ -e "$dir/python3.exe" ]; then
      ombra=1
      continue
    fi
    if ln "$dir/python.exe" "$dir/python3.exe" 2>/dev/null || cp -p "$dir/python.exe" "$dir/python3.exe" 2>/dev/null; then
      hash -r
      if python3_ok; then
        echo "OK python3 (ho creato $dir/python3.exe, lo stesso programma di python.exe)"
        return 0
      fi
      rm -f "$dir/python3.exe"
      hash -r
      ombra=1
    else
      bloccata="$dir"
    fi
  done
  IFS="$prima"
  [ "$ombra" = 1 ] && return 2
  [ -n "$bloccata" ] && return 3
  return 1
}

# PowerShell non legge ~/.bashrc: su Windows ~/.local/bin va nel Path utente, nel registro. Si legge
# senza espandere le %VARIABILI% e si riscrive come ExpandString, così le voci con %USERPROFILE%
# restano com'erano. SetEnvironmentVariable su una variabile di passaggio avvisa le finestre nuove.
# Una riga per istruzione: con -Command - PowerShell legge lo standard input riga per riga.
PS_PATH='$d = Join-Path $env:USERPROFILE ".local\bin"
$k = [Microsoft.Win32.Registry]::CurrentUser.CreateSubKey("Environment")
$v = [string]$k.GetValue("Path", "", [Microsoft.Win32.RegistryValueOptions]::DoNotExpandEnvironmentNames)
$voci = @($v -split ";" | Where-Object { $_ -ne "" })
$espanse = @($voci | ForEach-Object { [Environment]::ExpandEnvironmentVariables($_).TrimEnd("\") })
$nuovo = (@($voci) + $d) -join ";"
if ($espanse -contains $d) { "PRESENTE" } else { $k.SetValue("Path", $nuovo, [Microsoft.Win32.RegistryValueKind]::ExpandString); [Environment]::SetEnvironmentVariable("ARTURO_PATH", "1", "User"); [Environment]::SetEnvironmentVariable("ARTURO_PATH", $null, "User"); "AGGIUNTO" }'

path_windows() {
  local esito
  esito=$(printf '%s\n' "$PS_PATH" | powershell.exe -NoProfile -NonInteractive -Command - 2>/dev/null | tr -d '\r')
  case "$esito" in
    *AGGIUNTO*) echo "OK claude, aggiunto al Path di Windows: lo trova una finestra nuova di PowerShell" ;;
    *PRESENTE*) echo "OK claude, già nel Path di Windows: lo trova una finestra nuova di PowerShell" ;;
    *)
      claude_avvio='& "$env:USERPROFILE\.local\bin\claude.exe"'
      echo "AVVISO non riesco ad aggiungere ~/.local/bin al Path di Windows: in PowerShell apri Claude Code con $claude_avvio"
      ;;
  esac
}

main() {
  set -u
  unset GIT_DIR GIT_WORK_TREE GIT_INDEX_FILE
  local repo="${ARTURO_REPO:-https://github.com/stellakamikaze/arturo.git}"
  local amano="https://arturo.stellakamikaze.org/installa/#a-mano"
  local esteso="https://arturo.stellakamikaze.org/installa/#a-mano-esteso"
  local dest="$HOME/.claude"
  local nl='
'

  # Con CLAUDE_CONFIG_DIR Claude Code legge la configurazione da un'altra cartella: prima di ogni
  # altra cosa, anche prima di toccare il file della shell. Anche la strada a mano scrive in
  # ~/.claude, quindi non si rimanda lì.
  if [ -n "${CLAUDE_CONFIG_DIR:-}" ]; then
    local cfg="${CLAUDE_CONFIG_DIR%/}"
    case "$cfg" in
      "~" | "~"/*) cfg="$HOME${cfg#\~}" ;;
    esac
    if command -v cygpath >/dev/null 2>&1; then
      cfg=$(cygpath -u "$cfg" 2>/dev/null || printf '%s' "$cfg")
    fi
    if [ "$cfg" != "$dest" ]; then
      echo "CLAUDE_CONFIG_DIR vale $CLAUDE_CONFIG_DIR: Claude Code legge la configurazione da lì, non da $dest."
      echo "Non ho toccato niente. Arturo vive solo in $dest: con CLAUDE_CONFIG_DIR non è supportato, nemmeno a mano."
      echo "Per usarlo togli CLAUDE_CONFIG_DIR dal file della tua shell, apri un terminale nuovo e rilancia: Claude Code torna a leggere $dest e può chiederti di nuovo l'accesso."
      return 1
    fi
  fi

  echo "Installo Arturo in $dest"
  echo

  local sistema
  sistema=$(uname -s 2>/dev/null || echo sconosciuto)
  local os=linux
  case "$sistema" in
    Darwin) os=mac ;;
    MINGW* | MSYS* | CYGWIN*) os=windows ;;
  esac
  local manca=0
  # Dopo un winget il PATH nuovo arriva solo ai processi nuovi: si riapre tutto.
  local riapri="Poi la persona chiude Claude Code e la sua finestra di PowerShell, apre una finestra nuova, scrive claude e incolla di nuovo il link."

  # git, eseguito davvero. Su Mac /usr/bin/git esiste anche senza gli strumenti di Apple, e apre solo
  # la loro finestra: senza xcode-select -p non si chiama. Con gli strumenti c'è, ma dopo un
  # aggiornamento di Xcode senza licenza accettata git --version esce con errore.
  local git_ok=0 git_licenza=0 git_uscita=""
  if [ "$os" = mac ]; then
    if xcode-select -p >/dev/null 2>&1; then
      if git_uscita=$(git --version 2>&1); then
        git_ok=1
      else
        case "$git_uscita" in
          *[Ll]icense*) git_licenza=1 ;;
        esac
      fi
    fi
  elif command -v git >/dev/null 2>&1 && git --version >/dev/null 2>&1; then
    git_ok=1
  fi
  if [ "$git_ok" = 1 ]; then
    echo "OK git"
  else
    manca=1
    case "$os" in
      mac)
        if [ "$git_licenza" = 1 ]; then
          echo "MANCA git: la licenza di Xcode non è accettata, e git non risponde. Comando: lo scrive la persona, con la sua password: sudo xcodebuild -license accept"
        else
          echo "MANCA git. Comando: xcode-select --install (si apre una finestra di Apple: la persona clicca Installa). Poi, in background, aspetta la fine con: until xcode-select -p >/dev/null 2>&1; do sleep 10; done"
        fi
        ;;
      windows) echo "MANCA git. Comando: winget install --id Git.Git -e --source winget. $riapri" ;;
      *) echo "MANCA git. Comando: lo scrive la persona, con la sua password: sudo apt install git (su Fedora: sudo dnf install git)" ;;
    esac
  fi

  # python3, almeno la 3.8, eseguito davvero: su Windows un python3 finto apre solo il Microsoft Store.
  local bloccata="" esito_py=1
  if python3_ok; then
    echo "OK python3"
  else
    if [ "$os" = windows ]; then
      crea_python3
      esito_py=$?
    fi
    if [ "$esito_py" != 0 ]; then
      manca=1
      case "$os" in
        mac)
          if [ "$git_licenza" = 1 ]; then
            echo "MANCA python3 (serve la 3.8 o successiva). Comando: lo stesso di git, sudo xcodebuild -license accept: la persona lo scrive una volta sola."
          elif [ "$git_ok" = 0 ]; then
            echo "MANCA python3 (serve la 3.8 o successiva). Comando: xcode-select --install, lo stesso di git: lancialo una volta sola."
          elif command -v brew >/dev/null 2>&1; then
            echo "MANCA python3 (serve la 3.8 o successiva). Comando: brew install python3"
          else
            echo "MANCA python3 (serve la 3.8 o successiva). Comando: xcode-select --install"
          fi
          ;;
        windows)
          case "$esito_py" in
            2) echo "MANCA python3 (serve la 3.8 o successiva): c'è un Python vero, ma python3 apre il rimando al Microsoft Store. Comando: nessuno da lanciare: la persona spegne i due alias di Python in Impostazioni > App > Impostazioni app avanzate > Alias di esecuzione app. $riapri" ;;
            3) echo "MANCA python3 (serve la 3.8 o successiva): in $bloccata c'è python.exe, ma non riesco a creare python3.exe accanto. Comando: winget install -e --id Python.Python.3.12 --source winget (lo mette nella cartella della persona). $riapri" ;;
            *) echo "MANCA python3 (serve la 3.8 o successiva). Comando: winget install -e --id Python.Python.3.12 --source winget. $riapri Al giro dopo lo script crea python3 da solo." ;;
          esac
          ;;
        *) echo "MANCA python3 (serve la 3.8 o successiva). Comando: lo scrive la persona, con la sua password: sudo apt install python3 (su Fedora: sudo dnf install python3)" ;;
      esac
    fi
  fi

  # claude. L'installatore di Claude Code lo mette in ~/.local/bin, ma non sempre lo aggiunge al PATH.
  # Qui si aggiunge, una volta sola, dove lo legge una finestra nuova: .zshrc per zsh, .bash_profile
  # per bash sul Mac (il Terminale apre shell di login), .bashrc altrove, e su Windows anche il Path
  # utente, perché PowerShell non legge .bashrc. La finestra già aperta non lo vede: path_nuovo
  # cambia il messaggio finale.
  local rc="" path_nuovo=0 claude_avvio="claude"
  if command -v claude >/dev/null 2>&1; then
    echo "OK claude"
  elif [ -x "$HOME/.local/bin/claude" ] || [ -x "$HOME/.local/bin/claude.exe" ]; then
    path_nuovo=1
    case "$(basename "${SHELL:-bash}")" in
      zsh) rc="$HOME/.zshrc" ;;
      *)
        if [ "$os" = mac ]; then
          rc="$HOME/.bash_profile"
        else
          rc="$HOME/.bashrc"
        fi
        ;;
    esac
    if grep -qs '\.local/bin' "$rc"; then
      echo "OK claude, già nel PATH di $rc: si vede da un terminale nuovo"
    else
      printf '\n# Claude Code (aggiunto da Arturo)\nexport PATH="$HOME/.local/bin:$PATH"\n' >>"$rc"
      echo "OK claude, aggiunto al PATH in $rc"
    fi
    if [ "$os" = windows ]; then
      path_windows
    fi
  else
    manca=1
    if [ "$os" = windows ]; then
      echo "MANCA claude. Comando: irm https://claude.ai/install.ps1 | iex (in PowerShell)"
    else
      echo "MANCA claude. Comando: curl -fsSL https://claude.ai/install.sh | bash"
    fi
  fi

  # node serve alla barra in basso e a qualche strumento: lo installa /setup nella FASE 1.
  if command -v node >/dev/null 2>&1; then
    echo "OK node"
  else
    echo "AVVISO node non c'è: lo installa /setup. Fino ad allora la barra in basso resta vuota."
  fi
  if [ "$manca" = 1 ]; then
    echo
    echo "Installa quello che manca, poi rilancia questo script."
    return 1
  fi
  echo

  if [ -e "$dest" ] && [ ! -d "$dest" ]; then
    echo "$dest esiste ma non è una cartella: non lo tocco."
    return 1
  fi
  # Dopo `arturo migra` Arturo è un plugin e ~/.claude non ha più .git: un clone sopra lo
  # duplicherebbe. Il nome arturo@arturo lo scrive Claude Code in installed_plugins.json.
  if grep -qs '"arturo@arturo"' "$dest/plugins/installed_plugins.json"; then
    echo "Arturo è già installato in $dest come plugin. Per aggiornarlo scrivi /aggiorna in Claude Code."
    cancella_me
    return 0
  fi
  # Una seconda volta non rifà niente: l'aggiornamento è /aggiorna. Anche come upstream: chi
  # sincronizza Arturo fra più computer ha origin sul suo repository privato. Il remoto da solo non
  # basta (stellakamikaze/arturo-qualcosa è un altro repository): servono anche i file di Arturo.
  if [ -e "$dest/.git" ]; then
    if git -C "$dest" remote -v 2>/dev/null | grep -Eq 'stellakamikaze/arturo(\.git)?([[:space:]]|$)' \
      && git -C "$dest" ls-files --error-unmatch bin/arturo settings.json >/dev/null 2>&1; then
      echo "Arturo è già installato in $dest. Per aggiornarlo scrivi /aggiorna in Claude Code."
      cancella_me
      return 0
    fi
    # La prima riga della strada a mano è questo stesso script: serve il blocco esteso.
    echo "$dest è già un repository git che non è Arturo: non lo tocco."
    echo "Strada a mano: $esteso"
    echo "Nella guida apri \"Preferisco leggere i comandi\" e usa il blocco che comincia con B=: mette da parte tutta la cartella $dest, git compreso, in una copia con la data, e scarica Arturo."
    return 1
  fi

  # Il clone va in una cartella temporanea nella stessa HOME: lo spostamento di .git è un rename.
  trap 'pulisci_tmp' EXIT
  trap 'interrotto' INT TERM HUP
  ARTURO_TMP=$(mktemp -d "$HOME/.claude-arturo-XXXXXX") || {
    ARTURO_TMP=""
    echo "Non riesco a creare una cartella temporanea in $HOME: non ho toccato niente."
    return 1
  }
  local tmp="$ARTURO_TMP"
  if ! git clone --quiet "$repo" "$tmp/a"; then
    pulisci_tmp
    echo
    echo "Lo scaricamento da GitHub non è riuscito: non ho toccato niente."
    echo "Controlla la connessione e rilancia lo script."
    return 1
  fi

  # La firma, prima di ogni scrittura in ~/.claude. ARTURO_FIRMA_RILASCI serve solo al banco, con
  # ARTURO_REPO: chi può impostare l'ambiente di questo script può già scegliere da dove scarica.
  local rilascio="" esito_firma=0
  printf '%s\n' "${ARTURO_FIRMA_RILASCI:-$FIRMA_RILASCI}" >"$tmp/firme"
  verifica_rilascio "$tmp/a" "$tmp/firme" || esito_firma=$?
  if [ "$esito_firma" = 2 ]; then
    pulisci_tmp
    case "$os" in
      mac) echo "MANCA la verifica della firma dei rilasci: servono git 2.34 e OpenSSH 8.2, o più recenti. Comando: brew install git (senza brew: xcode-select --install, poi rilancia)" ;;
      windows) echo "MANCA la verifica della firma dei rilasci: servono git 2.34 e OpenSSH 8.2, o più recenti. Comando: winget upgrade --id Git.Git -e --source winget. $riapri" ;;
      *) echo "MANCA la verifica della firma dei rilasci: servono git 2.34 e OpenSSH 8.2, o più recenti. Comando: lo scrive la persona, con la sua password: sudo apt install git openssh-client (su Fedora: sudo dnf install git openssh-clients)" ;;
    esac
    echo "Non ho toccato niente."
    return 1
  fi
  if [ "$esito_firma" != 0 ]; then
    pulisci_tmp
    return 1
  fi
  if ! git -C "$tmp/a" reset --quiet --hard "$rilascio^{commit}" || ! git -C "$tmp/a" ls-files -z >"$tmp/elenco"; then
    pulisci_tmp
    echo "Non riesco a preparare il rilascio $rilascio: non ho toccato niente. Rilancia lo script."
    return 1
  fi
  echo "OK firma del rilascio $rilascio"

  # Backup per copia: ogni file di Arturo che esiste già in ~/.claude va nel backup, controllato.
  # Un conflitto fra file e cartella, una cartella che è un collegamento, o una copia sbagliata
  # fermano tutto prima di scrivere.
  local b
  b="$HOME/.claude-backup-$(date +%Y%m%d-%H%M%S)"
  if ! mkdir "$b" 2>/dev/null; then
    b="$b-$$"
    if ! mkdir "$b"; then
      pulisci_tmp
      echo "Non riesco a creare la cartella del backup in $HOME: non ho toccato niente."
      return 1
    fi
  fi
  ARTURO_BACKUP="$b"
  local p d conflitto="" visti="$nl" nsalvati=0
  local nuovi=() salvati=() cartelle=()
  while IFS= read -r -d '' p; do
    # Ogni cartella sul percorso, per i file nuovi e per quelli che esistono già: git reset --hard
    # toglie un collegamento a una cartella e ne crea una vera, e le cose della persona sparirebbero
    # da Claude Code (dotfiles con stow o chezmoi, cartelle in Dropbox).
    d="$p"
    while case "$d" in */*) true ;; *) false ;; esac; do
      d="${d%/*}"
      if [ -L "$dest/$d" ]; then
        conflitto="$dest/$d è un collegamento, e Arturo ci vuole una cartella vera"
        break 2
      fi
    done
    if [ -L "$dest/$p" ] || [ -f "$dest/$p" ]; then
      case "$p" in
        */*) mkdir -p "$b/${p%/*}" ;;
      esac
      if cp -pP "$dest/$p" "$b/$p" && { [ -L "$dest/$p" ] || cmp -s "$dest/$p" "$b/$p"; }; then
        salvati+=("$p")
        nsalvati=$((nsalvati + 1))
      else
        conflitto="la copia di sicurezza di $dest/$p non è riuscita"
        break
      fi
    elif [ -e "$dest/$p" ]; then
      conflitto="$dest/$p è una cartella, e Arturo ci vuole un file"
      break
    else
      # File nuovo: si segnano anche le cartelle che non esistono, per toglierle se si torna indietro.
      d="$p"
      while case "$d" in */*) true ;; *) false ;; esac; do
        d="${d%/*}"
        if [ -e "$dest/$d" ] || [ -L "$dest/$d" ]; then
          if [ ! -d "$dest/$d" ]; then
            conflitto="$dest/$d è un file, e Arturo ci vuole una cartella"
            break 2
          fi
          break
        fi
        case "$visti" in
          *"$nl$d$nl"*) ;;
          *)
            cartelle+=("$d")
            visti="$visti$d$nl"
            ;;
        esac
      done
      nuovi+=("$p")
    fi
  done <"$tmp/elenco"
  if [ -n "$conflitto" ]; then
    rm -rf "$b"
    ARTURO_BACKUP=""
    pulisci_tmp
    echo "Non posso installare Arturo: $conflitto."
    echo "Non ho toccato niente. Sposta quel percorso e rilancia lo script, oppure segui la strada a mano: $amano"
    return 1
  fi

  # Innesto: .git entra in ~/.claude e il reset scrive solo i file di Arturo. Sessioni, history.jsonl,
  # login, file dei plugin, CLAUDE.md e settings.local.json restano dove sono.
  local creata=0 spostato=0
  [ -d "$dest" ] || creata=1
  ARTURO_INNESTO=1
  ARTURO_BACKUP=""
  if mkdir -p "$dest" && mv "$tmp/a/.git" "$dest/.git"; then
    spostato=1
  fi
  if [ "$spostato" = 0 ] || ! git -C "$dest" reset --hard -q HEAD; then
    rimetti
    return 1
  fi
  ARTURO_INNESTO=0

  pulisci_tmp
  local impostazioni=0
  if [ -e "$b/settings.json" ] || [ -L "$b/settings.json" ]; then
    impostazioni=1
  fi
  if [ "$nsalvati" = 0 ]; then
    rm -rf "$b"
    b=""
  fi
  cancella_me

  echo "Arturo installato."
  if [ -n "$b" ]; then
    echo "I file che Arturo ha sostituito sono in $b"
  fi
  if [ "$impostazioni" = 1 ]; then
    echo "Il tuo accesso e le tue conversazioni restano dove sono, e i plugin restano installati. Il tuo vecchio settings.json finisce in una copia di sicurezza con la data nel nome: /setup ti propone di riportare hook, plugin e preferenze."
  fi
  echo
  echo "Arturo manda a chi lo mantiene dati d'uso da un elenco chiuso, mai le tue richieste o i tuoi file."
  echo "Per vedere cosa parte: python3 ~/.claude/bin/arturo telemetria mostra"
  echo "Per spegnerli: python3 ~/.claude/bin/arturo telemetria spegni"
  echo
  local finestra="questa finestra del terminale" nuova="un terminale nuovo"
  if [ "$os" = windows ]; then
    finestra="questa finestra di PowerShell"
    nuova="una finestra nuova di PowerShell"
  fi
  if [ -n "${CLAUDECODE:-}" ]; then
    echo "Claude: non lanciare altri comandi in questa sessione."
    if [ "$path_nuovo" = 1 ]; then
      echo "Adesso: 1. Scrivi /exit. 2. Chiudi $finestra e aprine una nuova: solo una finestra nuova trova claude. 3. Scrivi $claude_avvio. 4. Scrivi /setup."
    else
      echo "Adesso: 1. Scrivi /exit. 2. Scrivi claude. 3. Scrivi /setup."
    fi
  elif [ "$path_nuovo" = 1 ]; then
    echo "Adesso: chiudi $finestra, apri $nuova, scrivi $claude_avvio, poi /setup."
  else
    echo "Adesso: apri $nuova, scrivi claude, poi /setup."
  fi
  return 0
}

main "$@"
