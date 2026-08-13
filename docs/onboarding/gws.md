# Onboarding gws — Google Workspace CLI multi-account

Guida per collegare **più account Google** (lavoro + personale) alla CLI `gws`, ognuno con la propria directory di configurazione. Si invoca con `/inizio gws`.

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
