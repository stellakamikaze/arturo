# Arturo

> *Arturo — da Arktouros, "il guardiano dell'orsa": la stella più luminosa del cielo boreale, quella che i naviganti usavano per non perdere la rotta.*

Arturo è un **harness per [Claude Code](https://docs.anthropic.com/en/docs/claude-code)**: una configurazione completa di guardrail, workflow di sessione, agenti e skill che trasforma Claude Code da strumento a collaboratore affidabile. Come il suo omonimo celeste, Arturo fa il guardiano — sorveglia i comandi pericolosi, tiene i segreti fuori dalla history git, chiede conferma prima dei punti di non ritorno — e nel frattempo ti dà una rotta: sessioni che si aprono, si chiudono e si riprendono in modo ordinato, anche su più macchine.

È il telaio di una config personale usata quotidianamente in produzione, estratto e igienizzato: **zero dati, zero credenziali, zero riferimenti a infrastrutture private**. Quello che resta è il metodo.

In due righe: **21 guardie e automazioni**, **19 slash command**, **11 subagent**, **6 skill**. Nessun server, nessun account, nessun dominio richiesto — solo `git` e le CLI standard.

---

## Indice

- [Filosofia](#filosofia)
- [Requisiti](#requisiti)
- [Installazione](#installazione)
- [Prima accensione — checklist](#prima-accensione--checklist)
- [Come funziona: il dispatcher](#come-funziona-il-dispatcher)
- [Cosa c'è dentro](#cosa-cè-dentro)
  - [I guardiani (`hooks/`)](#i-guardiani-hooks)
  - [La rotta (`commands/`)](#la-rotta-commands)
  - [L'equipaggio (`agents/`)](#lequipaggio-agents)
  - [Le skill (`skills/`)](#le-skill-skills)
- [Cosa NON c'è (di proposito)](#cosa-non-cè-di-proposito)
- [Personalizzazione](#personalizzazione)
- [Sicurezza](#sicurezza)
- [Multi-macchina](#multi-macchina)
- [Onboarding gws (opzionale)](#onboarding-gws-google-workspace-cli-opzionale)
- [Troubleshooting](#troubleshooting)
- [Licenza](#licenza)

---

## Filosofia

Tre idee tengono insieme tutto:

1. **La sicurezza sta nei rail, non nell'attrito.** `defaultMode: acceptEdits` e un allow ampio su Bash: Claude lavora veloce. In cambio, i deny espliciti e i hook guard formano una rete che intercetta le operazioni davvero pericolose. Meglio pochi blocchi affidabili che cento popup ignorati per abitudine.
2. **Mai exit-0 muto.** Un check che non gira non è un check passato. Il validation gate distingue "verde" da "assente" — l'assenza di test non è un successo.
3. **Ogni regola è un passivo.** L'harness compensa solo ciò che il modello non può garantirsi da solo: guardie deterministiche, integrazioni, preferenze genuine. Tutto il resto va potato, non accresciuto (la skill `system-audit` include un "Bitter Lesson pass" proprio per questo).

---

## Requisiti

| Strumento | Serve per | Note |
|---|---|---|
| **Claude Code** | tutto | [guida ufficiale](https://docs.anthropic.com/en/docs/claude-code) |
| **git** | sessioni, sync, guardie commit | qualsiasi versione recente |
| **python3** ≥ 3.8 | la maggior parte dei guard | solo standard library, nessun pip |
| **node** ≥ 18 | `statusline.js`, `context-monitor.js` | |
| **jq** | parsing veloce nel dispatcher | c'è un fallback in `python3` se manca |

Facoltativi: **`gitleaks`** (audit segreti), **`bw`** (Bitwarden CLI, per le credenziali), **`gws`** (Google Workspace CLI — vedi [onboarding](#onboarding-gws-google-workspace-cli-opzionale)). Su macOS, per il timeout dello smoke test in `/system-audit` serve `gtimeout` (da `brew install coreutils`); se manca, il check gira comunque senza timeout.

---

## Installazione

```bash
# Se hai già una config, falle un backup:
mv ~/.claude ~/.claude-backup-$(date +%Y%m%d) 2>/dev/null

git clone https://github.com/stellakamikaze/arturo.git ~/.claude
```

Oppure, per innestare Arturo su una config esistente: clona altrove e copia `settings.json`, `hooks/`, `commands/`, `agents/`, `skills/`, `shared/` dentro `~/.claude/`.

> **Il tuo remote.** Il clone qui sopra punta al repo originale, su cui non hai accesso in scrittura: `/fine` tenta un push di sincronizzazione che fallirà — te lo dice con un messaggio chiaro, **non è un errore di rete**, e va benissimo usarlo così. Se invece vuoi **sincronizzare le tue modifiche tra più macchine**, crea un tuo repo privato e puntaci `origin`:
> ```bash
> gh repo create mio-claude --private --source ~/.claude --remote origin --push
> # oppure, se il repo esiste già:  git -C ~/.claude remote set-url origin <URL-del-tuo-repo>
> ```

---

## Prima accensione — checklist

1. **`settings.json` → `env.PROJECTS_BASE`** — la cartella dove vivono i tuoi progetti (default `~/Documents/ClaudeCode`). Vale per `/progetto`, `/inizio` e `/ui`.
2. **`hooks/exfil-guard.py` → regex `INTERNAL`** — aggiungi i tuoi host fidati (hostname del tuo server, tailnet, LAN) se ne hai. Di default passa solo `localhost`/LAN/CGNAT.
3. **Scrivi il tuo `~/.claude/CLAUDE.md`** — le istruzioni personali (chi sei, come lavori, regole tue). Non è incluso: è personale per definizione.
4. **`language` in `settings.json`** — è `italian`; cambialo se serve.
5. Apri Claude Code e lancia **`/system-audit`**: verifica che hook, skill e agent siano wirati correttamente sulla tua macchina. L'obiettivo è "tutto verde".

---

## Come funziona: il dispatcher

Ogni comando `Bash` passa da un unico router, `hooks/bash-dispatcher.sh`, che lo instrada **solo** verso i guard rilevanti. Un comando innocuo (la stragrande maggioranza) non fa partire nessun guard: zero latenza percepita.

```
         comando Bash
              │
              ▼
   ┌──────────────────────┐
   │   bash-dispatcher.sh  │  estrae il comando (jq, o python3 di fallback)
   └──────────┬───────────┘
              │  match dei pattern pre-filtro
              ▼
   ┌─────────────────────────────────────────────────────┐
   │  git commit / gh pr create → commit-secret-gate.py  │  scansiona il diff
   │  è "git puro" senza $(...) ? → esce, nessun guard    │
   │  invio email/messaggi       → comms-guard.py         │  blocco (draft-first)
   │  rm -r / config / segreti…  → block-dangerous.py     │  blocco o conferma
   │  POST/upload o GET-exfil…   → exfil-guard.py         │  conferma
   │  SQL/volumi/rsync --delete  → data-guard.py          │  conferma
   │  gh (anche FOO=… gh …)      → gh-*-guard.py          │  conferma
   └──────────┬──────────────────────────────────────────┘
              │  ogni guard può:
              ▼
   exit≠0 → BLOCCO (motivo allo stdout del modello)
   JSON "ask" → CONFERMA all'utente
   niente → prosegue silenzioso
```

Gli hook su `Edit`/`Write` (protezione config, emoji, quality-check) e i **PostToolUse** detective (scanner segreti, prompt-injection) girano in parallelo a questo flusso. Nessun guard blocca il lavoro se il payload è strano: sono **fail-open** sugli errori di parsing, **fail-closed** sui pattern che riconoscono.

---

## Cosa c'è dentro

```
settings.json        Permessi (allow/deny/ask), wiring hook, preferenze
hooks/               21 guardie e automazioni
commands/            19 slash command di workflow
agents/              11 subagent specializzati
skills/              6 skill (+ regole condivise in shared/)
docs/onboarding/     Guide di setup guidato (/inizio gws)
```

### I guardiani (`hooks/`)

Instradati dal dispatcher:

| Guard | Cosa intercetta | Esito |
|---|---|---|
| `block-dangerous.py` | `rm` ricorsivi su tree protetti, export vault, scrittura su config/hook (anche via `cd`), creazione di file di unlock, lettura segreti via shell (incl. `perl`/`ruby`/`nc`/redirezioni e comandi dentro `$(...)`), `curl\|bash` e sue varianti (process-sub, `eval`, pipe verso interpreti), fork bomb, `docker volume rm` | blocco/conferma |
| `commit-secret-gate.py` | segreti nel diff staged (e nel working tree su `git commit -a`), prima di ogni `git commit` / `gh pr create` | conferma |
| `data-guard.py` | SQL distruttivo (DROP/TRUNCATE/DELETE senza WHERE), `docker compose down -v`, `rsync --delete` verso host remoti, overwrite di file `.db` | conferma |
| `exfil-guard.py` | esfiltrazione verso host esterni: POST/upload (curl/wget/python) **e** GET mascherato, DNS-exfil, `/dev/tcp`, `nc`/`socat` | conferma |
| `comms-guard.py` | invio email/messaggi da CLI (sendmail, smtplib, AppleScript Mail...) — policy draft-first | blocco |
| `gh-destructive-guard.py` | operazioni GitHub distruttive (repo delete, secret, api mutanti), anche con prefisso `env`/`command` | conferma |
| `github_issue_guard.py` | contenuti da rivedere nei testi di issue/PR | conferma |

Fuori dal dispatcher:

- `protect_claude_md.py` — PreToolUse: protegge `CLAUDE.md` e i settings da modifiche via `Edit`/`Write` non richieste esplicitamente.
- `web-egress-guard.py` — PreToolUse su `WebFetch`/jina/`browser_navigate`: esfiltrazione via URL (dati interpolati nella query-string verso host esterni).
- `credential-leak-scanner.py` — PostToolUse: rileva token e chiavi negli output di Bash/WebFetch/MCP.
- `prompt-injection-scanner.py` — PostToolUse: segnala tentativi di prompt injection nei contenuti esterni (pattern EN + IT).
- `emoji_remover.py` — PostToolUse: niente emoji decorative nei file (i simboli tecnici legittimi sono whitelistati).
- `quality-check.sh` — PostToolUse asincrono: type-check/lint leggero dopo le modifiche.
- `context-monitor.js` — avvisa quando il context si avvicina alla soglia di rotazione.
- `session-start.sh` / `session-end.sh` / `session-reminder.sh` — titolo finestra, guardia anti-divergenza del repo config tra macchine, promemoria di chiusura.
- `inject-now.sh` — inietta data/ora corrente a ogni prompt.
- `input-notifier-start.sh` — notifica quando Claude aspetta input.
- `statusline.js` — statusline con modello, branch e stato sessione.

### La rotta (`commands/`)

Il ciclo di lavoro quotidiano:

- **`/inizio <progetto>`** — sync della config, localizza il progetto, riprende l'ultimo handoff, ricrea i task pendenti cross-referenziandoli con `git log` (quelli già completati non risorgono). `/inizio gws` avvia invece l'onboarding gws.
- **`/fine`** — review di completezza (agente dedicato), validate, commit selettivo, **handoff** con tabella task, mirror in `data/handoffs/` e push: la sessione successiva riparte da lì, su qualsiasi macchina.
- **`/commit`** — commit intelligente dal contesto della conversazione.

Sviluppo: `/progetto` (da idea a primo commit), `/discovery`, `/scope`, `/write-plan`, `/feature`, `/ui`, `/debug` (disciplina diagnostica: fatti prima delle ipotesi), `/rebase`, `/worktree`, `/ship`.

Qualità: `/deep-review` (review pre-landing multi-prospettiva), `/plan-review` (review di piani: EXPANSION/HOLD/REDUCTION), `/arewedone` (completezza strutturale), `/retro`, `/doc-update`, `/creative` (scrittura non-code).

### L'equipaggio (`agents/`)

Subagent con un mestiere solo, richiamati dai comandi o a mano: `architecture-reviewer`, `bug-finder`, `structural-completeness-reviewer`, `doc-reviewer`, `performance-profiler`, `ui-ux-consultant`, `test-runner`, `researcher`, `fact-checker`, `synthesizer`, `drafter`.

### Le skill (`skills/`)

- **`validate`** + **`shared/validation-gate.md`** — il gate: type-check, test, lint, print di debug; language-aware (Node/TS, Python, prosa); mai exit-0 muto.
- **`autofix`** — loop autonomo test-fix-retest (max 3 giri, poi si ferma e documenta).
- **`review-checklist`** — checklist strutturata pre-landing, usata da `/deep-review` e `/ship`.
- **`system-audit`** — audit dell'harness stesso: hook wirati vs presenti su disco, smoke test degli hook, frontmatter, JSON validi. Da lanciare dopo ogni modifica alla config.
- **`ui-reference`** — valori concreti e gotcha per frontend (layout, dark mode, accessibilità, animazioni).
- **`keyword-research`** — framework tri-superficie per content/SEO (organico, AEO, GEO).

---

## Cosa NON c'è (di proposito)

Arturo è stato estratto da una config che include anche memoria persistente, task manager centralizzato e integrazioni con server privati. Quei pezzi **non ci sono** e le loro funzioni sono coperte in modo autosufficiente:

| Al posto di... | Arturo usa |
|---|---|
| Task manager su server | `TaskList`/`TaskCreate` nativi + tabella task nell'handoff |
| Memoria su database/server | il tuo `CLAUDE.md` + gli handoff in `data/handoffs/` |
| Sync su server privato | il repo git stesso: `data/handoffs/` viaggia con la config |

Nessun componente richiede un server, un dominio o un account specifico.

---

## Personalizzazione

- **Più/meno attrito.** L'allow-list Bash è ampia per design; la protezione vera sono deny + guard. Vuoi che Claude chieda conferma più spesso? Metti `defaultMode: "default"` in `settings.json` e sfoltisci l'`allow`. Vuoi meno interruzioni? Aggiungi pattern specifici all'`allow`.
- **Host interni.** Se lavori con un tuo server, aggiungi il suo hostname alla regex `INTERNAL` in `exfil-guard.py` e `web-egress-guard.py`: le chiamate verso quegli host non chiederanno conferma.
- **Lingua.** `language` in `settings.json` (default `italian`) e i messaggi dei guard sono in italiano — cambiali se preferisci un'altra lingua.
- **Disattivare un guard.** Commenta la riga corrispondente in `bash-dispatcher.sh` (per i guard instradati) o rimuovi il blocco da `settings.json` (per quelli PostToolUse). Poi rilancia `/system-audit`.
- **Aggiungere un comando o una skill.** Un file `.md` in `commands/` diventa uno slash command; una cartella con `SKILL.md` in `skills/` diventa una skill. Il frontmatter `name` + `description` è obbligatorio (`/system-audit` lo verifica).

---

## Sicurezza

- L'allow-list Bash è ampia per design; la protezione vera sono **deny + guard**. I guard sono **fail-open** sugli errori di parsing (non ti bloccano se il payload è strano) ma **fail-closed** sui pattern che riconoscono.
- `commit-secret-gate.py` è l'ultima linea: se un segreto arriva al commit, il commit non parte. Ma la prima linea sei tu — `client_secret.json`, `.env` e simili non vanno mai in un repo (il `.gitignore` incluso li esclude, insieme ai file di runtime di Claude Code).
- I permessi `mcp__github__*` e il guard `github_issue_guard` sul matcher MCP si attivano solo se configuri un server MCP GitHub (`claude mcp add`); senza, sono inerti. Le operazioni via `gh` CLI sono comunque coperte dal dispatcher.
- Questo repo è periodicamente auditato (segreti, dati personali, bypass dei guard) prima di ogni pubblicazione. Se ci trovi qualcosa che non dovrebbe esserci, aprine una issue.

---

## Multi-macchina

Il repo config **È** il canale di sync: `/fine` committa e pusha (handoff inclusi), `/inizio` pulla. `session-start.sh` avvisa se la macchina è rimasta indietro rispetto a `origin/main`. Per usarlo su più macchine: clona il **tuo** fork/repo privato (vedi [Installazione](#installazione)) come `~/.claude` su ognuna.

---

## Onboarding gws (Google Workspace CLI, opzionale)

Se vuoi collegare più account Google (lavoro + personale) alla CLI `gws`, lancia:

```
/inizio gws
```

Claude ti guida passo-passo seguendo [`docs/onboarding/gws.md`](docs/onboarding/gws.md): installazione, progetti GCP (uno per gli account Workspace, uno separato per i `@gmail.com`), una config dir per account via `GOOGLE_WORKSPACE_CLI_CONFIG_DIR`, login, alias e checklist finale.

---

## Troubleshooting

| Sintomo | Causa probabile | Rimedio |
|---|---|---|
| `/fine` dice "Config push non riuscito" | hai clonato il repo originale, non un tuo fork (nessun accesso in scrittura) | normale; per sincronizzare imposta un tuo `origin` (vedi [Installazione](#installazione)) |
| `/system-audit` segnala hook "non eseguibile" | permessi persi dopo il clone | `chmod +x ~/.claude/hooks/*.sh ~/.claude/hooks/*.py` |
| Un guard chiede conferma su un comando legittimo | falso positivo del pattern | conferma ed esegui; se ricorre, apri una issue col comando esatto |
| Commit bloccato con un messaggio che *parla* di comandi pericolosi | il messaggio contiene un pattern come `curl\|bash` | usa `git commit -F file` (il guard scansiona il comando, non il file) |
| Nessun titolo nel terminale su macOS | `session-env/` mancante (creata al primo avvio) | innocuo; si risolve da solo |
| `/system-audit`: WARN su `MEMORY.md` | stai usando un sistema di memoria esterno non installato | ignora; senza `data/memory/` il check è N/A |

---

## Licenza

Usalo, forkalo, adattalo. Se ci trovi dentro qualcosa che non dovrebbe esserci, apri una issue.
