# Integrazione del lotto «guardie» (15/10/2026)

Branch `lotto-guardie`, base `cbd8305`. Modifiche ESATTE ai file condivisi che questo lotto non
tocca: `tests/verifica-allineamento.sh`, `settings.json`, `README.md`, `NOVITA.md`.

## 1. `tests/verifica-allineamento.sh`

### 1a. Ambiente del gate

Subito dopo `export ARTURO_TELEMETRIA=0`, aggiungi:

```bash
# I banchi delle guardie in background (session-start.sh) non partono dentro le prove: ogni
# session-start di un banco li lancerebbe in una HOME finta.
export ARTURO_BANCHI_AVVIO=0
```

### 1b. BANCHI

In coda all'array `BANCHI=( … )`, dopo `test_config_2026_10_15.py`:

```
  test_guardie_unite.py
  test_gate_commit.py
```

### 1c. PY38_BANCHI

Aggiungi `test_guardie_unite.py` (lancia le guardie con l'interprete che lo esegue: prova che
girano con Python 3.8). Verificato verde con Python 3.9.6; python3.8 non c'è su questa macchina.

```bash
PY38_BANCHI=(test_todo.py test_web.py test_percorso.py test_segnala.py test_telemetria.py test_deriva.py test_deriva_allineata.py test_personale.py test_guardie_unite.py)
```

### 1d. BASELINE

In coda all'array `BASELINE=( … )`:

```bash
  # Guardie unite alla config dell'autore (15/10/2026): cbd8305, l'ultimo dev prima del lotto.
  "test_guardie_unite.py cbd8305"
  # Gate dei commit (banchi dell'autore): il gate di Arturo era gia' allineato in f2c433e,
  # quindi la controprova e' 842b06f, l'ultimo dev prima di quell'allineamento.
  "test_gate_commit.py 842b06f"
```

Esiti misurati: `test_guardie_unite.py` su cbd8305 → `BASELINE_DISCRIMINANTE=G201,…,G213`;
`test_gate_commit.py` su 842b06f → `BASELINE_DISCRIMINANTE=G214,G215` (su cbd8305 passa: è un
banco di regressione di codice già portato).

## 2. `settings.json`

### 2a. PreToolUse: bozze MCP senza conferma

Nuovo blocco in `hooks.PreToolUse` (dopo quello di `bash-dispatcher.sh`):

```json
      {
        "matcher": "mcp__.*[Dd]raft.*",
        "hooks": [
          {
            "type": "command",
            "command": "python3 ~/.claude/hooks/bozze-mcp-auto-approve.py",
            "timeout": 5
          }
        ]
      },
```

### 2b. PostToolUse: type-check dopo una modifica

Nuovo blocco in `hooks.PostToolUse`:

```json
      {
        "matcher": "Edit|MultiEdit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "python3 ~/.claude/hooks/typecheck-after-edit.py",
            "timeout": 120
          }
        ]
      },
```

### 2c. permissions.allow

Il type-check rosso dice a Claude di rilanciare il controllo: senza queste voci ogni rilancio chiede
conferma.

```json
      "Bash(npx tsc --noEmit:*)",
      "Bash(npx vue-tsc --noEmit:*)",
      "Bash(npx vue-tsc -b:*)",
      "Bash(npx vitest run:*)",
```

### 2d. statusLine

Il flag `*` delle modifiche git e la quota si aggiornano anche quando Claude è fermo:

```json
  "statusLine": {
    "type": "command",
    "command": "node ~/.claude/hooks/statusline.js",
    "refreshInterval": 30
  },
```

## 3. `README.md`

### 3a. Sezione «Configurazione», punto 2 (Host interni)

Sostituisci la riga che comincia con `2. **Host interni**` con:

```
2. **Host interni** — le guardie conoscono solo regole pubbliche: `localhost` e le reti locali (`10.x`, `172.16.x`-`172.31.x`, `192.168.x`, gli indirizzi Tailscale `100.64.x`, link-local e IPv6 locali). Un nome `.ts.net` non conta come interno, perché con Tailscale Funnel può essere pubblico. I tuoi host personali, compresi quelli della tua tailnet, vanno in `hooks/hosts-interni.local` (una voce per riga, hostname o rete), non nei file `.py`. Le API esterne che usi con la tua chiave (fatturazione, CRM) vanno in `hooks/api-fidate.local`, un nome host esatto per riga: un POST verso di loro non chiede conferma.
```

### 3b. Diagramma del dispatcher

Righe da cambiare dentro il riquadro:

```
   │ invio email/messaggi → comms-guard.py                 │ ask
   │ rm, config, segreti, avvio auto → block-dangerous.py  │ blocco o ask
```

E una riga nuova in fondo al riquadro, dopo quella di `gh`:

```
   │ memoria e handoff (nessuna guardia ha deciso) → allow │ allow
```

### 3c. Tabella delle guardie

Riga di `block-dangerous.py`, colonna «Cosa intercetta», aggiungi in coda prima di ` | blocco/conferma |`:

```
. Una scrittura shell su un git hook o su un servizio di avvio (`~/Library/LaunchAgents`, `~/.config/systemd/user`, `~/.config/autostart`) chiede conferma. Il testo di un heredoc verso python o `cat`, un messaggio `-m` e il pattern di `grep` non contano come comandi o file letti
```

Riga di `exfil-guard.py`, colonna «Cosa intercetta»:

```
esfiltrazione verso host esterni: POST e upload (curl/wget/python); il ramo GET è disattivato per scelta di attrito. Giudica il codice eseguito (senza gli heredoc scritti su file). Le API in `hooks/api-fidate.local` passano
```

Riga di `comms-guard.py`: aggiungi `mail` senza `-s` e `http.client` all'elenco, e cambia l'esito
da `blocco` a `conferma`. Testo della colonna «Cosa intercetta»:

```
invio email/messaggi da CLI (sendmail, msmtp, `mail`, gws, smtplib, `http.client`, `git send-email`, AppleScript Mail...) — policy draft-first. Chiede conferma invece di bloccare: il blocco insegnava a Claude ad aggirare la regex. Giudica il codice eseguito: `comms-prefilter.py` toglie gli heredoc scritti su file e tace sulle letture (`grep -ril smtplib`), mentre `find -exec`, `awk system()` e `sed` contano come esecuzione
```

### 3d. «Fuori dal dispatcher»

Sostituisci la riga di `protect_claude_md.py`:

```
- `protect_claude_md.py` — PreToolUse: protegge `CLAUDE.md`, settings e hook da modifiche via `Edit`/`Write` senza file di unlock, e i percorsi di avvio automatico (`.git/hooks`, `~/Library/LaunchAgents`, `~/.config/systemd/user`, `~/.config/autostart`) con un unlock di sistema; scrivere un file di unlock chiede sempre conferma. Avvisa quando il `CLAUDE.md` globale supera il budget di righe (`ARTURO_CLAUDE_MD_RIGHE`, default 200).
```

Sostituisci la riga di `session-start.sh` / `session-end.sh`:

```
- `session-start.sh` / `session-end.sh` — titolo finestra, riga `MACCHINA`, avvisi Git locali, file della config modificati e non salvati, controllo della deriva (`deriva.py`), banchi delle guardie in background ogni 12 ore (`tests/banchi-avvio.sh`, un rosso si dice all'avvio; `ARTURO_BANCHI_AVVIO=0` li spegne), avvio della telemetria (`arturo telemetria`), invito a `/segnala` (si spegne con `arturo segnala basta`), promemoria di chiusura anche senza file cambiati e cleanup degli unlock di sessione.
```

Sostituisci la riga di `statusline.js`:

```
- `statusline.js` — statusline con modello abbreviato, task in corso, progetto@ramo (`*` se ci sono modifiche), uso del contesto e quota delle finestre di 5 ore e 7 giorni.
```

Aggiungi in fondo all'elenco:

```
- `typecheck-after-edit.py` — PostToolUse: dopo una modifica a un file `.ts`, `.tsx` o `.vue` lancia il type-check del progetto (lo script `typecheck` o il `tsc`/`vue-tsc` del `build`) e manda gli errori a Claude. Fuori da un progetto TypeScript tace.
- `bozze-mcp-auto-approve.py` — PreToolUse: la creazione di una bozza via un collegamento (`create_draft`, `slack_send_message_draft`) non chiede conferma; l'invio, la pubblicazione e la cancellazione di una bozza sì.
- `forma_comando.py` — modulo, non un hook: ricava i programmi che un comando esegue davvero (path completo, blocchi, `sh -c`, `eval`). Lo usano `block-dangerous.py` e il dispatcher (git puro, ramo memoria).
```

### 3e. Sezione «Personalizzazione», voce «Host interni»

Sostituisci la voce con:

```
- **Host interni e API fidate.** `INTERNAL_HOSTS` e `INTERNAL_NETS` in `exfil-guard.py` e `web-egress-guard.py` sono i default pubblici: non modificarli. Se lavori con un tuo server, aggiungi il suo hostname o la sua rete in `hooks/hosts-interni.local`, una voce per riga: le chiamate verso quegli host non chiederanno conferma. Una rete più larga di `/8` viene ignorata. Un servizio esterno che usi con la tua chiave va in `hooks/api-fidate.local`, un nome host esatto per riga (niente reti, niente `*`). I due file sono tuoi, nessun aggiornamento li tocca.
```

## 4. `NOVITA.md`

Entry da mettere in cima (sopra «Scegli come ti scrive Claude»):

```markdown
## 2026-10-15 — Guardie che leggono il comando come lo esegue la shell

**Cosa cambia**: un invio di email o messaggi da terminale ora chiede conferma invece di essere
bloccato: vedi il comando vero e decidi tu. Le guardie leggono il comando come lo esegue la shell:
il testo di un heredoc scritto su file, un messaggio di commit e il pattern di `grep` non fanno più
scattare allarmi, mentre un `rm` col percorso completo o dentro `sh -c` si vede. Un git hook o un
servizio che parte all'accesso (`~/Library/LaunchAgents` su Mac, `~/.config/systemd/user` e
`~/.config/autostart` su Linux) si scrive solo con la tua conferma. Le reti locali contano tutte
come interne (anche `172.16.x`-`172.31.x` e le IPv6 locali); un servizio esterno che usi con la tua
chiave lo scrivi in `hooks/api-fidate.local`. Salvare un handoff o una memoria non chiede più
conferma; settings, hook e file di sblocco la chiedono sempre. La statusline mostra il ramo git, un
`*` se ci sono modifiche e la quota dell'abbonamento. Dopo ogni modifica a un file TypeScript o Vue
Claude vede subito gli errori di tipo. Creare una bozza via un collegamento non chiede conferma,
inviarla sì.

**Il principio dietro**: un blocco che sbaglia insegna a Claude ad aggirare la guardia, una
conferma mostra a te il comando vero. Queste correzioni girano da settimane nella config
dell'autore.

**Da sapere**: all'avvio Arturo prova le sue guardie in background, al massimo ogni 12 ore, senza
rallentare la sessione. Se una guardia non funziona su questo computer, la sessione dopo una riga
`GUARDIE` te lo dice. Li spegni con `ARTURO_BANCHI_AVVIO=0`. Se il tuo `CLAUDE.md` supera le 200
righe, Claude ti avvisa quando lo modifica (il limite si cambia con `ARTURO_CLAUDE_MD_RIGHE`).
```

## 5. Già nel branch (non condivisi)

- `.gitignore`: riga `hooks/api-fidate.local`.
- `commands/setup.md`, FASE 6: reti già fidate aggiornate (172.16/12, Tailscale, link-local,
  IPv6) ed esempio `203.0.113.0/24`; una frase su `hooks/api-fidate.local`.
- Banchi esistenti aggiornati perché si aspettavano il blocco degli invii: `test_guardie_minori.py`
  (R04), `test_telemetria.py` (M06), `test_segnala.py` (S05, solo testo),
  `test_bash_dispatcher_review.py` (gws-send, msmtp, S06), `test_revisione_2026_09_30.py` (R09).
  `test_prodotto.py` (P09) usa `198.51.100.0/24` perché `172.16/12` ora è nei default.
