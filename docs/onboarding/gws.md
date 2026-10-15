# Collegare Gmail, Calendar e Drive

Si invoca con `/inizio gws`. Ci sono due strade. Parti sempre dalla prima.

## 0. La strada semplice: i connettori di claude.ai

Per chi usa un solo account Google e non ha mai creato un progetto su Google Cloud.

1. Apri claude.ai nel browser, con lo stesso account con cui entri in Claude Code.
2. Vai in Impostazioni › Connettori e attiva Gmail, Google Calendar e Google Drive. Google chiede il consenso: leggilo e accetta.
3. Chiudi Claude Code e riaprilo. Scrivi `/mcp`: i connettori compaiono con il nome `claude.ai Gmail`, `claude.ai Google Calendar` e così via.
4. Prova: «leggi le ultime tre email e dimmi chi mi ha scritto».

Cosa sapere:
- I connettori arrivano in Claude Code solo se entri con l'abbonamento di claude.ai. Con una chiave API non compaiono.
- Gmail e Calendar non si aggiungono con `claude mcp add`: si collegano solo da claude.ai.
- Se nel tuo piano non trovi i connettori, o sei in un piano Team o Enterprise dove li aggiunge solo l'amministratore, chiedi a lui oppure usa la seconda strada.
- Le bozze non chiedono conferma. Mandare, rispondere e inoltrare la chiedono sempre: lo dice `permissions.ask` di `settings.json` (`mcp__*__*send*`, `*reply*`, `*forward*`).
- Per spegnerli tutti: `"disableClaudeAiConnectors": true` in `settings.json`.

Fonte: la pagina MCP della documentazione di Claude Code, sezione «Use MCP servers from claude.ai».

## La strada avanzata: Google Workspace CLI multi-account

Serve a chi lavora con **più account Google** (lavoro + personale) o vuole i comandi `gws` nel terminale. Ogni account ha la sua directory di configurazione, e serve un progetto su Google Cloud: è la parte lunga.

> gws ≥ v0.22: il multi-account si fa SOLO via `GOOGLE_WORKSPACE_CLI_CONFIG_DIR` (il flag `--account` non esiste più).

## 1. Installazione

```bash
npm install -g @googleworkspace/cli
gws --version
```

## 2. Prerequisito GCP: un progetto per "famiglia" di account

Ogni account ha bisogno di un `client_secret.json` OAuth (tipo "Desktop app") scaricato dalla [GCP Console](https://console.cloud.google.com/apis/credentials):

- **Account Workspace** (dominio aziendale): un progetto GCP nell'org del dominio. Più account dello stesso dominio possono condividere lo stesso `client_secret.json`.
- **Account Gmail consumer** (@gmail.com): serve un progetto GCP **separato e personale** — le org Workspace bloccano gli scope Gmail "restricted" per gli account consumer. Non riusare il client del progetto aziendale: il login fallirebbe con errori di policy.

Per ogni progetto: abilita le API che ti servono (Gmail, Drive, Docs, Sheets, Calendar, Tasks) e crea le credenziali OAuth Desktop.

## 3. Una config dir per account

```bash
mkdir -p ~/.config/gws-lavoro ~/.config/gws-personale
cp ~/Downloads/client_secret_progetto_lavoro.json    ~/.config/gws-lavoro/client_secret.json
cp ~/Downloads/client_secret_progetto_personale.json ~/.config/gws-personale/client_secret.json
```

**MAI committare i `client_secret.json`** (il `.gitignore` di questo repo li esclude, e `commit-secret-gate.py` li blocca comunque).

## 4. Login (una volta per macchina)

Il browser si apre per il consenso OAuth. Le credenziali risultanti sono criptate (`.enc`) con chiave nel Keyring del sistema operativo: **non sono trasferibili tra macchine** — su una macchina nuova si rifà il login, non si copiano i file.

```bash
GOOGLE_WORKSPACE_CLI_CONFIG_DIR=~/.config/gws-lavoro    gws auth login -s drive,docs,sheets,gmail,calendar,tasks
GOOGLE_WORKSPACE_CLI_CONFIG_DIR=~/.config/gws-personale gws auth login -s drive,gmail,sheets,calendar
```

## 5. Alias in `.zshrc` / `.bashrc`

```bash
# Account di default
export GOOGLE_WORKSPACE_CLI_CONFIG_DIR="$HOME/.config/gws-lavoro"
# Switch esplicito
alias gws-lavoro='GOOGLE_WORKSPACE_CLI_CONFIG_DIR=$HOME/.config/gws-lavoro gws'
alias gws-personale='GOOGLE_WORKSPACE_CLI_CONFIG_DIR=$HOME/.config/gws-personale gws'
```

## 6. Uso programmatico (da Claude Code)

```bash
# Verifica di quale account stai usando (fallo SEMPRE prima di operazioni di scrittura):
GOOGLE_WORKSPACE_CLI_CONFIG_DIR=~/.config/gws-personale gws gmail users getProfile --params '{"userId":"me"}'
```

La env var per-comando è il modo affidabile di scegliere l'account in uno script o in una sessione Claude: niente stato globale, niente sorprese.

## Gotcha noti

- **NON usare** `GOOGLE_WORKSPACE_CLI_CREDENTIALS_FILE` (legacy): entra in conflitto col multi-account. Se è nel tuo ambiente: `unset GOOGLE_WORKSPACE_CLI_CREDENTIALS_FILE`.
- Errore 403 "permission denied" su un account: verifica che quell'account abbia accesso al progetto GCP (invito IAM accettato) e che l'API sia abilitata.
- Login che fallisce su @gmail.com con client aziendale → è il blocco org sugli scope restricted: usa il progetto GCP personale (punto 2).
- Aggiungere scope dopo il primo login richiede un nuovo `gws auth login` con la lista completa.

## Checklist finale

- [ ] `gws --version` risponde
- [ ] Una config dir per account, ciascuna col suo `client_secret.json`
- [ ] Login fatto per ogni account, `getProfile` restituisce l'email giusta
- [ ] Alias nel file di shell
- [ ] Nessun `client_secret.json` dentro repo git
