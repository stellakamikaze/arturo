#!/usr/bin/env bash
# Installa Arturo come plugin di Claude Code.
# Strada consigliata: Claude Code scarica questo file e lo lancia, come dice
# https://arturo.stellakamikaze.org/inizia/
# Strada a mano, da un terminale:
#   curl -fsSL https://raw.githubusercontent.com/stellakamikaze/arturo/landing-v2/sito/installa.sh | bash
# (da GitHub, non dal sito: la riga a mano non ha il confronto fra le due copie di /inizia/)
#
# Dal 22/11/2026 (revisione D2) le persone nuove entrano dal plugin, non dal clone in ~/.claude.
# Lo script controlla i programmi, aggiunge il catalogo di Arturo a Claude Code, verifica che il
# catalogo indichi un rilascio firmato, fa installare il plugin a Claude Code e controlla che la
# copia installata sia proprio quel rilascio. Non scrive file di Arturo in ~/.claude, salvo l'ancora
# della chiave: login, conversazioni, CLAUDE.md e plugin della persona restano come sono, e in
# settings.json Claude Code scrive solo il catalogo e il plugin acceso (sonda del 22/11/2026). Permessi,
# regole di blocco e barra in basso li aggiunge /setup, col sì della persona.
# Ogni programma che manca esce in una riga "MANCA <cosa>. Comando: <comando>": l'uscita di Bash
# arriva a Claude parola per parola, una pagina web no.
# Tutto sta in main(): se lo scaricamento si interrompe a metà, non parte niente.
# Bash 3.2 (quello di macOS) e Git Bash su Windows. Niente sudo.

# La chiave che firma i rilasci: la stessa riga di firme/rilasci.allowed_signers su main (il banco la
# confronta). Lo script installa solo lo sha di un tag plugin-vX.Y.Z firmato da questa chiave, e la
# scrive come ancora in ~/.claude/arturo: l'avvio di Arturo verifica la copia con quella. Per cambiare
# chiave: docs/manutenzione.md, e questa riga cambia insieme.
FIRMA_RILASCI='rilasci@arturo namespaces="git,arturo-manifest" ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIP0HfWu3Wxkq0+trFJ6S7P7MZmo2OXRlVKkgTKXI74K5'
# Il rilascio più vecchio che lo script accetta, contro un catalogo riportato indietro a un tag firmato
# con un buco già chiuso. Si alza quando un rilascio chiude un buco grave.
VERSIONE_MINIMA=0.2.23
# Gli errori di verify-tag che dicono "firma verificata e sbagliata": uguali a FIRMA_SBAGLIATA di
# bin/aggiornamenti.py. Ogni altro errore vuol dire che la verifica non è partita.
FIRMA_SBAGLIATA='no signature found|no principal matched|could not verify signature|bad signature|non-tag object'
# Il nome del plugin e del catalogo in Claude Code: gli stessi di bin/migra.py.
PLUGIN=arturo@arturo
MERCATO=arturo

ARTURO_TMP=""

pulisci_tmp() {
  [ -n "$ARTURO_TMP" ] && rm -rf "$ARTURO_TMP"
  ARTURO_TMP=""
}

interrotto() {
  pulisci_tmp
  echo
  echo "Interrotto. Se il catalogo di Arturo era già aggiunto, resta in Claude Code: rilancia lo script per finire."
  exit 130
}

# Il file scaricato da Claude Code serve una volta sola.
cancella_me() {
  local f="$HOME/.arturo-installa.sh"
  if [ "$0" = "$f" ] || { [ -f "$f" ] && [ "$0" -ef "$f" ]; }; then
    rm -f "$f"
  fi
}

# Vero se la versione X.Y.Z ($1, anche con la v davanti) non è più vecchia di X.Y.Z ($2).
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

# La voce di Arturo nel catalogo che Claude Code ha scaricato: "tag sha versione sorgente repo",
# separati da tab, "-" per un campo vuoto. NESSUNO se il catalogo o la voce mancano. Come
# voce_catalogo di bin/aggiornamenti.py.
LEGGI_CATALOGO='import json, os, sys
def leggi(p):
    try:
        with open(p, encoding="utf-8") as f:
            d = json.load(f)
        return d if isinstance(d, dict) else {}
    except Exception:
        return {}
k = leggi(sys.argv[1]).get("arturo")
dove = k.get("installLocation") if isinstance(k, dict) else None
m = leggi(os.path.join(dove, ".claude-plugin", "marketplace.json")) if dove else {}
v = next((p for p in m.get("plugins") or [] if isinstance(p, dict) and p.get("name") == "arturo"), None)
if not v:
    print("NESSUNO")
    sys.exit(0)
s = v.get("source") if isinstance(v.get("source"), dict) else {}
print("\t".join(str(x).strip() or "-" for x in (s.get("ref") or "", s.get("sha") or "", v.get("version") or "",
                                                 s.get("source") or "", s.get("repo") or "")))'

# Lo sha della copia di Arturo che Claude Code ha installato (plugins/installed_plugins.json), vuoto se
# non c'è. Come installato di bin/aggiornamenti.py: prima la voce dello scope user.
LEGGI_INSTALLATO='import json, sys
try:
    with open(sys.argv[1], encoding="utf-8") as f:
        d = json.load(f)
except Exception:
    d = {}
voci = (d.get("plugins") or {}).get("arturo@arturo") if isinstance(d, dict) else None
voci = [v for v in voci or [] if isinstance(v, dict)]
v = next((v for v in voci if v.get("scope") == "user"), voci[0] if voci else {})
print(v.get("gitCommitSha") or "")'

# Il rilascio $tag del catalogo, scaricato in $1 e verificato con la chiave in $2: tag annotato, firma
# SSH di quella chiave, col nome $tag scritto dentro (la firma copre quel nome, non il ref: un tag
# vecchio ripubblicato con un nome nuovo ha una firma valida), non più vecchio di VERSIONE_MINIMA, e
# sul commit $sha che il catalogo indica. Usa tag e sha di main().
# Esito 0 buono, 1 compromissione (messaggio già stampato), 2 la verifica non è partita (git o
# OpenSSH vecchi).
verifica_rilascio() {
  local lavoro="$1" firme="$2" errore dentro
  local fine="Non ho installato niente: segnala a chi mantiene Arturo."
  if [ "$(git -C "$lavoro" cat-file -t "refs/tags/$tag" 2>/dev/null)" != tag ]; then
    echo "Il rilascio $tag non ha la firma di Arturo (tag senza firma): possibile compromissione. $fine"
    return 1
  fi
  # verify-tag sceglie il programma dalla firma scritta nel tag, non da gpg.format: un tag firmato PGP
  # passa da gpg e dal portachiavi della persona, senza guardare $firme (revisione del 20/11/2026, S1,
  # #6258). Git legge la firma dall'ultima riga "-----BEGIN …" del tag: quella deve essere SSH. Come
  # verifica_tag di bin/aggiornamenti.py.
  if [ "$(git -C "$lavoro" cat-file tag "$tag" 2>/dev/null | grep -e '^-----BEGIN ' | tail -n 1 | tr -d '\r')" \
    != '-----BEGIN SSH SIGNATURE-----' ]; then
    echo "Il rilascio $tag non ha la firma di Arturo (firma non SSH): possibile compromissione. $fine"
    return 1
  fi
  if ! errore=$(LC_ALL=C git -C "$lavoro" -c gpg.format=ssh -c gpg.ssh.allowedSignersFile="$firme" \
    verify-tag "$tag" 2>&1 >/dev/null); then
    if printf '%s\n' "$errore" | grep -Eiq "$FIRMA_SBAGLIATA"; then
      echo "Il rilascio $tag non ha la firma di Arturo: possibile compromissione. $fine"
      return 1
    fi
    return 2
  fi
  dentro=$(git -C "$lavoro" cat-file tag "$tag" 2>/dev/null | sed -n 's/^tag //p' | head -n 1)
  if [ "$dentro" != "$tag" ]; then
    echo "Il tag $tag è il rilascio firmato ${dentro:-senza nome} ripubblicato con un altro nome: possibile compromissione. $fine"
    return 1
  fi
  if ! versione_almeno "${tag#plugin-}" "$VERSIONE_MINIMA"; then
    echo "Il catalogo indica $tag, più vecchio della $VERSIONE_MINIMA che questo script conosce: possibile compromissione. $fine"
    return 1
  fi
  if [ "$(git -C "$lavoro" rev-parse "$tag^{commit}" 2>/dev/null)" != "$sha" ]; then
    echo "Il catalogo indica lo sha $sha, che non è il rilascio firmato $tag: possibile compromissione. $fine"
    return 1
  fi
  return 0
}

python3_ok() {
  command -v python3 >/dev/null 2>&1 \
    && python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)' >/dev/null 2>&1
}

# Su Windows python3 deve eseguire davvero. Sonda su un PC con Windows 11 (1/11/2026):
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

# Toglie l'ancora scritta da main() quando l'installazione non va in fondo, e la sua cartella se l'ha
# creata main(). Usa le variabili di main(): bash le vede perché parte da dentro main().
togli_ancora() {
  [ "$ancora_nuova" = 1 ] || return 0
  rm -f "$ancora"
  [ "$ancora_dir" = 1 ] && rmdir "$dest/arturo" 2>/dev/null
  return 0
}

# `claude plugin …` col claude trovato da main(). ARTURO_AGGIORNAMENTI=manuali: anche `claude plugin`
# chiude con gli hook di sessione, e senza lancerebbe l'aggiornamento automatico (come _claude di
# bin/migra.py).
claude_plugin() {
  ARTURO_AGGIORNAMENTI=manuali "$claude_bin" plugin "$@" </dev/null
}

main() {
  set -u
  unset GIT_DIR GIT_WORK_TREE GIT_INDEX_FILE
  local catalogo="${ARTURO_CATALOGO:-stellakamikaze/arturo#catalogo}"
  local migrazione="https://github.com/stellakamikaze/arturo/blob/main/docs/migrazione.md"
  local dest="$HOME/.claude"

  # Con CLAUDE_CONFIG_DIR Claude Code legge la configurazione da un'altra cartella: prima di ogni
  # altra cosa, anche prima di toccare il file della shell. L'Orsa di Arturo vive in ~/.claude.
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
      echo "Non ho toccato niente. Arturo vive solo in $dest: con CLAUDE_CONFIG_DIR non è supportato."
      echo "Per usarlo togli CLAUDE_CONFIG_DIR dal file della tua shell, apri un terminale nuovo e rilancia: Claude Code torna a leggere $dest e può chiederti di nuovo l'accesso."
      return 1
    fi
  fi

  echo "Installo Arturo come plugin di Claude Code"
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
  # cambia il messaggio finale, e `claude plugin` qui sotto parte col percorso intero.
  local rc="" path_nuovo=0 claude_avvio="claude" claude_bin=""
  if command -v claude >/dev/null 2>&1; then
    claude_bin=claude
    echo "OK claude"
  elif [ -x "$HOME/.local/bin/claude" ] || [ -x "$HOME/.local/bin/claude.exe" ]; then
    path_nuovo=1
    claude_bin="$HOME/.local/bin/claude"
    [ -x "$claude_bin" ] || claude_bin="$HOME/.local/bin/claude.exe"
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
  # Il nome arturo@arturo lo scrive Claude Code in installed_plugins.json.
  if grep -qs '"arturo@arturo"' "$dest/plugins/installed_plugins.json"; then
    echo "Arturo è già installato come plugin. Per aggiornarlo scrivi /aggiorna in Claude Code."
    cancella_me
    return 0
  fi
  # Arturo come clone dentro ~/.claude, anche come upstream di un repository della persona: il plugin
  # sopra lo duplicherebbe, con le guardie due volte. Il passaggio è arturo migra. Il remoto da solo
  # non basta (stellakamikaze/arturo-qualcosa è un altro repository): servono anche i file di Arturo.
  if [ -e "$dest/.git" ] \
    && git -C "$dest" remote -v 2>/dev/null | grep -Eq 'stellakamikaze/arturo(\.git)?([[:space:]]|$)' \
    && git -C "$dest" ls-files --error-unmatch bin/arturo settings.json >/dev/null 2>&1; then
    echo "Arturo è già installato in $dest, come copia dentro la cartella. Per aggiornarlo scrivi /aggiorna in Claude Code."
    echo "Per passare al plugin: $migrazione"
    cancella_me
    return 0
  fi

  trap 'pulisci_tmp' EXIT
  trap 'interrotto' INT TERM HUP
  ARTURO_TMP=$(mktemp -d "$HOME/.claude-arturo-XXXXXX") || {
    ARTURO_TMP=""
    echo "Non riesco a creare una cartella temporanea in $HOME: non ho toccato niente."
    return 1
  }
  local tmp="$ARTURO_TMP"

  # Il catalogo: Claude Code lo scarica dal ramo catalogo. Già aggiunto, si aggiorna. Lo script verifica
  # proprio la copia che Claude Code userà per installare.
  local aggiunto=0 uscita=""
  if python3 -c 'import json, sys; sys.exit(0 if "arturo" in json.load(open(sys.argv[1], encoding="utf-8")) else 1)' \
    "$dest/plugins/known_marketplaces.json" >/dev/null 2>&1; then
    uscita=$(claude_plugin marketplace update "$MERCATO" 2>&1) || {
      pulisci_tmp
      echo "Non riesco ad aggiornare il catalogo di Arturo in Claude Code: non ho installato niente."
      echo "Claude Code dice: $(printf '%s' "$uscita" | tr '\n' ' ' | cut -c1-200)"
      echo "Controlla la connessione e rilancia lo script."
      return 1
    }
  else
    uscita=$(claude_plugin marketplace add "$catalogo" 2>&1) || {
      pulisci_tmp
      echo "Non riesco ad aggiungere il catalogo di Arturo a Claude Code: non ho toccato niente."
      echo "Claude Code dice: $(printf '%s' "$uscita" | tr '\n' ' ' | cut -c1-200)"
      echo "Controlla la connessione e rilancia lo script."
      return 1
    }
    aggiunto=1
  fi

  # Da qui un errore toglie il catalogo, se l'ha aggiunto lo script.
  local togli="Ho tolto il catalogo che avevo aggiunto."
  [ "$aggiunto" = 1 ] || togli="Il catalogo di Arturo resta in Claude Code com'era."
  local voce tag="" sha="" versione="" sorgente="" repo=""
  voce=$(python3 -c "$LEGGI_CATALOGO" "$dest/plugins/known_marketplaces.json" 2>/dev/null | tr -d '\r')
  if [ -z "$voce" ] || [ "$voce" = NESSUNO ]; then
    [ "$aggiunto" = 1 ] && claude_plugin marketplace remove "$MERCATO" >/dev/null 2>&1
    pulisci_tmp
    echo "Il catalogo di Arturo non elenca Arturo: possibile compromissione. Non ho installato niente: segnala a chi mantiene Arturo. $togli"
    return 1
  fi
  IFS='	' read -r tag sha versione sorgente repo <<EOF
$voce
EOF
  local url="https://github.com/$repo.git"
  local fermo=""
  if ! printf '%s\n' "$tag" | grep -Eq '^plugin-v[0-9]+\.[0-9]+\.[0-9]+$' \
    || ! printf '%s\n' "$sha" | grep -Eq '^[0-9a-f]{40}$'; then
    fermo="il catalogo non fissa Arturo a un tag plugin-vX.Y.Z e al suo sha ($tag)"
  elif [ "$versione" != - ] && [ "$versione" != "${tag#plugin-v}" ]; then
    fermo="il catalogo chiama $versione il rilascio $tag"
  elif [ "$sorgente" != github ] || ! printf '%s\n' "$repo" | grep -Eq '^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$'; then
    fermo="il catalogo indica una sorgente che non so verificare ($sorgente)"
  fi
  if [ -n "$fermo" ]; then
    [ "$aggiunto" = 1 ] && claude_plugin marketplace remove "$MERCATO" >/dev/null 2>&1
    pulisci_tmp
    echo "Non installo Arturo: $fermo. Possibile compromissione. Non ho installato niente: segnala a chi mantiene Arturo. $togli"
    return 1
  fi
  # ARTURO_REPO e ARTURO_FIRMA_RILASCI servono solo al banco: chi può impostare l'ambiente di questo
  # script può già scegliere da dove scarica.
  url="${ARTURO_REPO:-$url}"
  if ! git init -q "$tmp/t" >/dev/null 2>&1 \
    || ! git -C "$tmp/t" fetch --quiet --depth=1 --no-tags -- "$url" "+refs/tags/$tag:refs/tags/$tag" >/dev/null 2>&1; then
    [ "$aggiunto" = 1 ] && claude_plugin marketplace remove "$MERCATO" >/dev/null 2>&1
    pulisci_tmp
    echo "Non riesco a scaricare da GitHub il rilascio $tag: non ho installato niente. $togli"
    echo "Controlla la connessione e rilancia lo script."
    return 1
  fi

  # La firma, prima dell'installazione.
  local esito_firma=0
  printf '%s\n' "${ARTURO_FIRMA_RILASCI:-$FIRMA_RILASCI}" >"$tmp/firme"
  verifica_rilascio "$tmp/t" "$tmp/firme" || esito_firma=$?
  if [ "$esito_firma" != 0 ]; then
    [ "$aggiunto" = 1 ] && claude_plugin marketplace remove "$MERCATO" >/dev/null 2>&1
    pulisci_tmp
    if [ "$esito_firma" = 2 ]; then
      case "$os" in
        mac) echo "MANCA la verifica della firma dei rilasci: servono git 2.34 e OpenSSH 8.2, o più recenti. Comando: brew install git (senza brew: xcode-select --install, poi rilancia)" ;;
        windows) echo "MANCA la verifica della firma dei rilasci: servono git 2.34 e OpenSSH 8.2, o più recenti. Comando: winget upgrade --id Git.Git -e --source winget. $riapri" ;;
        *) echo "MANCA la verifica della firma dei rilasci: servono git 2.34 e OpenSSH 8.2, o più recenti. Comando: lo scrive la persona, con la sua password: sudo apt install git openssh-client (su Fedora: sudo dnf install git openssh-clients)" ;;
      esac
      echo "Non ho installato niente. $togli"
    else
      echo "$togli"
    fi
    return 1
  fi
  echo "OK firma del rilascio $tag"

  # L'ancora: la chiave con cui l'avvio di Arturo verifica la copia installata (hooks/fiducia.py). Se
  # c'è già, resta: è quella di un Arturo installato prima, e la deriva la confronta.
  local ancora="$dest/arturo/rilasci.allowed_signers" ancora_nuova=0 ancora_dir=0
  [ -d "$dest/arturo" ] || ancora_dir=1
  if [ ! -e "$ancora" ]; then
    if mkdir -p "$dest/arturo" && cp "$tmp/firme" "$ancora"; then
      ancora_nuova=1
    else
      [ "$aggiunto" = 1 ] && claude_plugin marketplace remove "$MERCATO" >/dev/null 2>&1
      pulisci_tmp
      echo "Non riesco a scrivere $ancora: non ho installato niente. $togli"
      return 1
    fi
  fi

  # L'installazione la fa Claude Code, dal catalogo appena verificato. Poi lo sha della copia deve
  # essere quello del tag firmato: fra la verifica e l'installazione il catalogo potrebbe cambiare.
  local installato=""
  if ! uscita=$(claude_plugin install "$PLUGIN" 2>&1); then
    installato=$(python3 -c "$LEGGI_INSTALLATO" "$dest/plugins/installed_plugins.json" 2>/dev/null | tr -d '\r')
    [ -n "$installato" ] && claude_plugin uninstall "$PLUGIN" >/dev/null 2>&1
    [ "$aggiunto" = 1 ] && claude_plugin marketplace remove "$MERCATO" >/dev/null 2>&1
    togli_ancora
    pulisci_tmp
    echo "Claude Code non è riuscito a installare Arturo: non ho installato niente. $togli"
    echo "Claude Code dice: $(printf '%s' "$uscita" | tr '\n' ' ' | cut -c1-200)"
    echo "Rilancia lo script; se l'errore torna, segnala a chi mantiene Arturo."
    return 1
  fi
  installato=$(python3 -c "$LEGGI_INSTALLATO" "$dest/plugins/installed_plugins.json" 2>/dev/null | tr -d '\r')
  if [ "$installato" != "$sha" ]; then
    claude_plugin uninstall "$PLUGIN" >/dev/null 2>&1
    [ "$aggiunto" = 1 ] && claude_plugin marketplace remove "$MERCATO" >/dev/null 2>&1
    togli_ancora
    pulisci_tmp
    echo "Claude Code ha installato ${installato:-una copia senza sha}, non il rilascio firmato $tag ($sha): possibile compromissione. Ho tolto la copia installata. $togli Segnala a chi mantiene Arturo."
    return 1
  fi
  pulisci_tmp
  cancella_me

  echo "OK plugin $tag installato e verificato"
  echo "Arturo installato."
  echo "Il tuo accesso, le tue conversazioni, CLAUDE.md e i tuoi plugin restano come sono. In settings.json Claude Code accende solo il plugin. Permessi, regole di blocco e barra in basso li aggiunge /setup, col tuo sì."
  echo
  echo "Arturo manda a chi lo mantiene dati d'uso da un elenco chiuso, mai le tue richieste o i tuoi file."
  echo "Per vedere cosa parte, chiedi a Claude: \"mostrami la telemetria di Arturo\". Per spegnerla: \"spegni la telemetria di Arturo\"."
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
