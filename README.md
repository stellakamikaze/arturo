# Arturo

> *Arturo — da Arktouros, "il guardiano dell'orsa": la stella più luminosa del cielo boreale, quella che i naviganti usavano per non perdere la rotta.*

Arturo è un **harness per [Claude Code](https://docs.anthropic.com/en/docs/claude-code)**: una configurazione completa di guardrail, workflow di sessione, agenti e skill che trasforma Claude Code da strumento a collaboratore affidabile. Come il suo omonimo celeste, Arturo fa il guardiano — sorveglia i comandi pericolosi, tiene i segreti fuori dalla history git, chiede conferma prima dei punti di non ritorno — e nel frattempo ti dà una rotta: sessioni che si aprono, si chiudono e si riprendono in modo ordinato, anche su più macchine.

È il telaio di una config personale usata quotidianamente in produzione, estratto e igienizzato: **zero dati, zero credenziali, zero riferimenti a infrastrutture private**. Quello che resta è il metodo.

In due righe: **18 guardie e automazioni**, **11 slash command**, **9 subagent**, **3 skill** — più un **curriculum di principi** (`docs/principi/`) e un canale di aggiornamento (`/novita`) pensati per chi parte da zero, anche senza un mestiere tecnico. Nessun server, nessun account, nessun dominio richiesto — solo `git` e le CLI standard.

---

## In breve

**Per chi è.** Arturo è per chi vuole cominciare a usare Claude Code e non sa da dove partire, anche senza un mestiere tecnico. Ti dà regole di sicurezza già pronte, un modo ordinato di aprire e chiudere il lavoro, e un percorso per imparare i principi.

**Cominciare in tre passi.**

1. Installa Claude Code, `git`, `python3` e `node` (vedi [Requisiti](#requisiti)).
2. Scarica Arturo con `git clone https://github.com/stellakamikaze/arturo.git ~/.claude`. Se hai già una cartella `~/.claude`, leggi prima [Installazione](#installazione).
3. Apri Claude Code dentro `~/.claude` e scrivi `/setup`. Il comando ti guida una cosa per volta.

Quando esce una versione nuova, Arturo te lo dice all'avvio. `/aggiorna` ti mostra cosa arriva e la applica dopo il tuo sì.

Il resto della pagina spiega come funziona Arturo dentro. Per cominciare non serve leggerlo.

## Cosa non è neutro

Arturo è gratuito e open source. Lo strumento su cui gira non lo è. Prima di cominciare devi sapere tre cose:

- **Claude Code è un servizio a pagamento di Anthropic, un'azienda privata.** Anthropic decide prezzi, limiti e funzioni, e li può cambiare. Arturo non cambia questa condizione.
- **Quello che scrivi passa dai server di Anthropic.** Le guardie di Arturo fermano segreti e credenziali, ma la conversazione esce comunque dal tuo computer.
- **Un aggiornamento di Arturo è codice scritto da altri, e gira sul tuo computer.** Per questo `/aggiorna` ti mostra cosa arriva prima di applicarlo. Se un aggiornamento non ti convince, non applicarlo.

Il primo capitolo del curriculum, [Chi possiede lo strumento](docs/principi/00-chi-possiede-lo-strumento.md), spiega perché conviene usare Claude Code lo stesso e come tenere bassa la dipendenza.

## Impegni

Arturo cambia ogni giorno. Chi lo usa ha diritto di sapere cosa aspettarsi:

1. **Il repository resta pubblico e con licenza MIT.** Non diventa privato e non viene cancellato.
2. **L'avvio della sessione non applica aggiornamenti.** Controlla soltanto se ci sono novità. Gli aggiornamenti li applicano `/aggiorna`, dopo il tuo sì, e `/inizio`, che sincronizza la configurazione quando apri un progetto.
3. **Niente telemetria.** Arturo non raccoglie dati su di te né su come lo usi. L'unico contatto automatico con l'esterno è il controllo degli aggiornamenti: un `git fetch` verso i repository della tua configurazione, al massimo ogni sei ore.
4. **Arturo resta in italiano.**
5. **Se lo sviluppo si ferma, lo scrivo.** Lo dichiarano l'ultima entry di [`NOVITA.md`](NOVITA.md) e la cima di questa pagina. La copia che hai continua a funzionare, e puoi farne un fork.

---

## Indice

- [In breve](#in-breve)
- [Cosa non è neutro](#cosa-non-è-neutro)
- [Impegni](#impegni)
- [Filosofia](#filosofia)
- [Requisiti](#requisiti)
- [Installazione](#installazione)
- [Aggiornare Arturo](#aggiornare-arturo)
- [Prima accensione — checklist](#prima-accensione--checklist)
- [Come funziona: il dispatcher](#come-funziona-il-dispatcher)
- [Cosa c'è dentro](#cosa-cè-dentro)
  - [I guardiani (`hooks/`)](#i-guardiani-hooks)
  - [La rotta (`commands/`)](#la-rotta-commands)
  - [L'equipaggio (`agents/`)](#lequipaggio-agents)
  - [Le skill (`skills/`)](#le-skill-skills)
- [Cosa NON c'è (di proposito)](#cosa-non-cè-di-proposito)
- [Imparare con Arturo](#imparare-con-arturo)
- [Personalizzazione](#personalizzazione)
- [Sicurezza](#sicurezza)
- [Multi-macchina](#multi-macchina)
- [Onboarding gws (opzionale)](#onboarding-gws-google-workspace-cli-opzionale)
- [Troubleshooting](#troubleshooting)
- [Autore e manutenzione](#autore-e-manutenzione)
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

Facoltativi: **`gitleaks`** (audit segreti), **`bw`** (Bitwarden CLI, per le credenziali), **`gws`** (Google Workspace CLI — vedi [onboarding](#onboarding-gws-google-workspace-cli-opzionale)). Lo smoke test di `/system-audit` usa `timeout` se c'è (su Linux e Git Bash sì, su macOS di norma no); senza, gira comunque, solo senza tetto di tempo.

---

## Installazione

```bash
# Se hai già una config, falle un backup:
mv ~/.claude ~/.claude-backup-$(date +%Y%m%d) 2>/dev/null

git clone https://github.com/stellakamikaze/arturo.git ~/.claude
```

Oppure, per innestare Arturo su una config esistente: clona altrove e copia `settings.json`, `hooks/`, `commands/`, `agents/`, `skills/`, `shared/`, `docs/`, `NOVITA.md` dentro `~/.claude/` (`docs/` e `NOVITA.md` servono a `/sparring`, `/novita` e `/inizio gws`).

> **Il tuo remote.** Il clone qui sopra punta al repo originale, su cui non hai accesso in scrittura: `/fine` tenta un push di sincronizzazione che fallirà — te lo dice con un messaggio chiaro, **non è un errore di rete**, e va benissimo usarlo così. Se invece vuoi **sincronizzare le tue modifiche tra più macchine**, crea un tuo repo privato e puntaci `origin`:
> ```bash
> git -C ~/.claude remote rename origin upstream   # Arturo resta raggiungibile: /novita scarica da qui
> gh repo create mio-claude --private --source ~/.claude --remote origin --push
> # oppure, se il repo esiste già:  git -C ~/.claude remote add origin <URL-del-tuo-repo>
> ```

---

## Aggiornare Arturo

Arturo continua a evolvere. All'avvio della sessione ti avvisa quando c'è una versione nuova:

```
ARTURO: c'e' un aggiornamento (3 commit) — scaricalo con /aggiorna
```

**`/aggiorna`** fa il resto: ti mostra cosa arriva, controlla che non travolga le tue modifiche e
applica. A mano è la stessa cosa:

```bash
git -C ~/.claude pull
```

In entrambi i casi, poi **chiudi e riapri Claude Code**: comandi, hook e skill si caricano all'avvio della sessione,
quindi quelli appena arrivati non compaiono finché non riapri. Se `pull` si ferma perché hai
modificato file tuoi (tipico: `CLAUDE.md`, i permessi in `settings.json`), non forzare nulla:
guarda `git -C ~/.claude status --short` e sistema un file per volta.

Dopo il primo aggiornamento non serve più ricordarselo: all'avvio della sessione Arturo ti avvisa
quando ci sono novità, e **`/novita`** te le racconta e propone il pull.

> Se `/aggiorna` o `/novita` rispondono «comando sconosciuto», la tua copia è precedente a quei
> comandi: fai il `git pull` qui sopra a mano e riapri Claude Code. Da lì in poi bastano gli slash.

## Prima accensione — checklist

> **La via rapida: `/setup`.** Apri Claude Code dentro `~/.claude` e lancia **`/setup`**: ti guida passo-passo in tutta la configurazione qui sotto (prerequisiti, permessi, `PROJECTS_BASE`, lingua, `CLAUDE.md`, sync, verifica finale), una cosa alla volta e in linguaggio semplice. È il modo consigliato, soprattutto se non sei un programmatore. La checklist qui sotto è la versione manuale, per chi preferisce farla a mano.

1. **`settings.json` → `env.PROJECTS_BASE`** — la cartella dove vivono i tuoi progetti (default `~/Documents/ClaudeCode`). Vale per `/progetto` e `/inizio`.
2. **`hooks/exfil-guard.py`** — gli host interni sono regole pubbliche: `localhost`, reti locali esplicite e suffisso `.ts.net`. Non aggiungere host personali alla distribuzione.
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
   │ bash-dispatcher.sh    │  prosa heredoc inerte ridotta; ambiguità → originale
   └──────────┬───────────┘
              │
              ▼
   ┌──────────────────────────────────────────────────────┐
   │ git commit / gh pr create → commit-secret-gate.py     │ ask
   │ git puro non esecutivo → esce                         │
   │ invio email/messaggi → comms-guard.py                 │ blocco
   │ rm, config, segreti → block-dangerous.py              │ blocco o ask
   │ POST/upload → exfil-guard.py                          │ ask
   │ GET-exfil → disattivato per scelta di attrito          │
   │ SQL, volumi, rsync → data-guard.py                    │ ask
   │ gh → gh-destructive-guard.py                          │ blocco o ask
   └──────────┬───────────────────────────────────────────┘
              │
              ▼
   rc 2 → blocco · JSON valido → decisione · crash/spurio → ask · vuoto → prosegue
```

Gli hook su `Edit`/`Write` proteggono config e forma. Gli scanner PostToolUse rilevano segreti e prompt injection. Un input non interpretabile produce una conferma, non un allow implicito.

---

## Cosa c'è dentro

```
settings.json        Permessi (allow/deny/ask), wiring hook, preferenze
hooks/               18 guardie e automazioni
commands/            11 slash command di workflow (incl. /setup, /aggiorna, /guidami, /novita)
agents/              9 subagent specializzati
skills/              3 skill (+ regole condivise in shared/)
docs/principi/       Il curriculum: i principi spiegati in semplice
docs/onboarding/     Guide di setup guidato (/inizio gws)
NOVITA.md            Canale di aggiornamento (lo racconta /novita)
```

### I guardiani (`hooks/`)

Instradati dal dispatcher:

| Guard | Cosa intercetta | Esito |
|---|---|---|
| `block-dangerous.py` | `rm` ricorsivi su tree protetti, export vault, scrittura su config/hook (anche via `cd`), creazione di file di unlock, lettura segreti via shell (incl. `perl`/`ruby`/`nc`/redirezioni e comandi dentro `$(...)`), `curl\|bash` e sue varianti (process-sub, `eval`, pipe verso interpreti), fork bomb, `docker volume rm` | blocco/conferma |
| `commit-secret-gate.py` | segreti nel diff staged (e nel working tree su `git commit -a`), prima di ogni `git commit` / `gh pr create` | conferma |
| `data-guard.py` | SQL distruttivo (DROP/TRUNCATE/DELETE senza WHERE), `docker compose down -v`, `rsync --delete` verso host remoti, overwrite di file `.db` | conferma |
| `exfil-guard.py` | esfiltrazione verso host esterni: POST e upload (curl/wget/python); il ramo GET è disattivato per scelta di attrito | conferma |
| `comms-guard.py` | invio email/messaggi da CLI (sendmail, msmtp, gws, smtplib, AppleScript Mail...) — policy draft-first | blocco |
| `gh-destructive-guard.py` | operazioni GitHub distruttive (repo delete anche via GraphQL, secret, api DELETE/PUT/PATCH) → blocco; mutazioni GraphQL, query lette da file e POST anche impliciti (`-f`/`-F`/`--input`) → conferma; anche con prefisso `env`/`command` | blocco / conferma |

Fuori dal dispatcher:

- `protect_claude_md.py` — PreToolUse: protegge `CLAUDE.md`, settings e hook da modifiche via `Edit`/`Write` senza file di unlock; scrivere un file di unlock chiede sempre conferma.
- `web-egress-guard.py` — PreToolUse su `WebFetch`/jina/`browser_navigate`, inclusa la navigazione Firefox: esfiltrazione via URL verso host esterni.
- `credential-leak-scanner.py`` — PostToolUse: rileva token e chiavi negli output di Bash/WebFetch/MCP.
- `prompt-injection-scanner.py` — PostToolUse: segnala tentativi di prompt injection nei contenuti esterni (pattern EN + IT).
- `emoji_remover.py` — PostToolUse: niente emoji decorative nei file (i simboli tecnici legittimi sono whitelistati).
- `context-monitor.js` — avvisa quando il context si avvicina alla soglia di rotazione.
- `session-start.sh` / `session-end.sh` — titolo finestra, avvisi Git locali e cleanup degli unlock di sessione.
- `inject-now.sh` — inietta data/ora corrente a ogni prompt, e ricorda che una richiesta di lavoro
  comincia con `Skill(prompt-master)` e con PROMPT + BRIEF. Per spegnere il promemoria, cancella il
  blocco `cat` finale dello script.
- `input-notifier-start.sh` — notifica quando Claude aspetta input.
- `statusline.js` — statusline con modello, task in corso, cartella e uso del contesto.

### La rotta (`commands/`)

Setup: **`/setup`** — configurazione guidata dell'intero harness per un nuovo utente (prerequisiti, permessi, `PROJECTS_BASE`, `CLAUDE.md`, sync, verifica); pensato anche per chi non programma.

Manutenzione: **`/aggiorna`** — scarica e applica l'ultima versione di Arturo, dopo averti mostrato cosa cambia e controllato che non travolga le tue modifiche.

Ripresa: **`/guidami`** — guarda gli ultimi handoff e le conversazioni recenti e ti propone tre o quattro cose che ha senso fare adesso, con il motivo e il primo passo. Per quando riapri e non sai da dove ripartire.

Pedagogia: **`/novita`** — racconta gli aggiornamenti dell'harness non ancora visti (cosa cambia, il principio dietro); **`/sparring`** — prende un principio del curriculum e lo prova sul lavoro reale dell'utente, con esperimenti piccoli e reversibili. Vedi [Imparare con Arturo](#imparare-con-arturo).

Il ciclo di lavoro quotidiano:

- **`/inizio <progetto>`** — sync della config, localizza il progetto, riprende l'ultimo handoff, ricrea i task pendenti cross-referenziandoli con `git log` (quelli già completati non risorgono). `/inizio gws` avvia invece l'onboarding gws.
- **`/fine`** — review di completezza per le modifiche di codice, validate, commit selettivo e handoff.

Sviluppo: `/progetto` (da idea a primo commit), `/discovery`, `/write-plan`, `/debug` (disciplina diagnostica: fatti prima delle ipotesi).

Qualità: usa le capacità native di review e verifica dell'harness.

### L'equipaggio (`agents/`)

Subagent con un mestiere solo, richiamati a mano: `architecture-reviewer`, `bug-finder`, `structural-completeness-reviewer`, `doc-reviewer`, `performance-profiler`, `ui-ux-consultant`, `test-runner`, `researcher`, `fact-checker`.

### Le skill (`skills/`)

- **`shared/validation-gate.md`** — il gate: type-check, test, lint e print di debug. Il produttore della pipeline decide l'esito; una cache non sostituisce il controllo.
- **`system-audit`** — audit dell'harness: hook diretti e transitivi, smoke test, frontmatter YAML e permessi. `--strict` fallisce se manca un requisito.
- **`prompt-master`** — due modalità: un prompt pronto da incollare in un altro tool AI, oppure il **brief interno**: prima di ogni richiesta di lavoro ricostruisce il contesto che manca, riscrive la richiesta come la eseguirà (il **prompt**) e mostra obiettivo, output, vincoli, criterio di fatto, assunzioni e ambiguità (il **brief**). L'hook `inject-now.sh` lo ricorda a ogni prompt (upstream `nidhinjs/prompt-master`, MIT).
- **`italiano-semplificato`** — riscrive o controlla un testo con l'Italiano Tecnico Semplificato (63 regole): frasi corte, voce attiva, una parola per concetto, senza burocratese né slop AI.

---

## Cosa NON c'è (di proposito)

Arturo è stato estratto da una config che include anche memoria persistente, task manager centralizzato e integrazioni con server privati. Quei pezzi **non ci sono** e le loro funzioni sono coperte in modo autosufficiente:

| Al posto di... | Arturo usa |
|---|---|
| Task manager su server | `TaskList`/`TaskCreate` nativi + tabella task nell'handoff |
| Memoria su database/server | il tuo `CLAUDE.md` + gli handoff in `data/handoffs/` |
| Sync su server privato | il repo git stesso: `data/handoffs/` viaggia con la config, solo se il suo remote è privato |

Nessun componente richiede un server, un dominio o un account specifico.

---

## Imparare con Arturo

Arturo non è solo una configurazione: è pensato anche come **percorso pedagogico** per chi
è incuriosito dall'AI, ne intuisce l'impatto, vorrebbe usare Claude Code ma non sa da dove
partire — incluse le persone che non fanno un mestiere tecnico. Il percorso:

1. **`/setup`** — l'installazione guidata, una cosa per volta, in linguaggio semplice.
2. **`docs/principi/`** — il curriculum: i principi dell'usare bene un'AI, spiegati in
   parole semplici. Si parte da [Chi possiede lo strumento](docs/principi/00-chi-possiede-lo-strumento.md)
   (il potere prima dei comandi), poi [Chiedere bene](docs/principi/01-chiedere-bene.md):
   il modello risponde alla domanda che gli hai fatto, non a quella che avevi in testa.
3. **`/sparring`** — una sessione guidata che prende un principio e lo prova sul TUO
   lavoro reale, con esperimenti piccoli e reversibili. Anche «questo per ora non ti
   serve» è un risultato.
4. **`/novita`** — quando l'harness si aggiorna (`git pull`), all'avvio della sessione
   Arturo ti avvisa; `/novita` racconta cosa è cambiato, il principio dietro, e ti
   propone lo sparring. Così l'harness — e chi lo usa — restano aggiornati insieme.

Le novità vivono in [`NOVITA.md`](NOVITA.md), la entry più recente in cima.

---

## Personalizzazione

- **Più/meno attrito.** L'allow-list Bash è ampia per design; la protezione vera sono deny + guard. Vuoi che Claude chieda conferma più spesso? Metti `defaultMode: "default"` in `settings.json` e sfoltisci l'`allow`. Vuoi meno interruzioni? Aggiungi pattern specifici all'`allow`.
- **Host interni.** Se lavori con un tuo server, aggiungi il suo hostname a `INTERNAL_HOSTS` (o la sua rete a `INTERNAL_NETS`) in `exfil-guard.py` e in `web-egress-guard.py`: le chiamate verso quegli host non chiederanno conferma.
- **Lingua.** `language` in `settings.json` (default `italian`) e i messaggi dei guard sono in italiano — cambiali se preferisci un'altra lingua.
- **Disattivare un guard.** Commenta la riga corrispondente in `bash-dispatcher.sh` (per i guard instradati) o rimuovi il blocco da `settings.json` (per quelli PostToolUse). Poi rilancia `/system-audit`.
- **Aggiungere un comando o una skill.** Un file `.md` in `commands/` diventa uno slash command; una cartella con `SKILL.md` in `skills/` diventa una skill. Il frontmatter `name` + `description` è obbligatorio (`/system-audit` lo verifica).

---

## Sicurezza

- Il dispatcher converte un errore o output spurio di una guardia in `ask`. I singoli guard restano conservativi sui pattern riconosciuti.
- `commit-secret-gate.py` chiede conferma se trova un segreto nel diff del repository destinatario. Non confermare credenziali reali.
- Le operazioni GitHub distruttive via `gh` CLI restano coperte dal dispatcher.
- Questo repo è periodicamente auditato (segreti, dati personali, bypass dei guard) prima di ogni pubblicazione. Se ci trovi qualcosa che non dovrebbe esserci, aprine una issue.

---

## Multi-macchina

Il repo config **È** il canale di sync: `/fine` committa e pusha, `/inizio` pulla. Gli handoff stanno solo in `~/.claude/data/handoffs/`, mai nel repository del progetto, ed entrano nel push solo se `gh repo view` dice che il remote della config è privato. `session-start.sh` avvisa se la macchina è rimasta indietro rispetto a `origin/main`. Per usarlo su più macchine: clona il **tuo** fork/repo privato (vedi [Installazione](#installazione)) come `~/.claude` su ognuna.

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
| `/system-audit` segnala `hook diretto mancante` | un file citato in `settings.json` non c'è (copia manuale incompleta) | ricopia il file da Arturo e rilancia `/system-audit` |
| Un guard chiede conferma su un comando legittimo | falso positivo del pattern | conferma ed esegui; se ricorre, apri una issue col comando esatto |
| Commit bloccato con un messaggio che *parla* di comandi pericolosi | il messaggio contiene un pattern come `curl\|bash` | usa `git commit -F file` (il guard scansiona il comando, non il file) |
| Nessun titolo nel terminale su macOS | `session-env/` mancante (creata al primo avvio) | innocuo; si risolve da solo |

---

## Autore e manutenzione

Arturo è un progetto di **Federico Nejrotti** — autore, non programmatore: questo harness
è anche la dimostrazione della sua stessa tesi, che il metodo conta più del codice. La
history del repo è volutamente neutra; la firma sta qui.

Arturo si sviluppa ogni giorno: è l'estratto di una configurazione usata in produzione, e
le novità arrivano a chi lo usa con `/aggiorna`. Gli impegni verso chi lo usa stanno in
[Impegni](#impegni). Le issue sono benvenute e vengono lette, ma non c'è promessa di
risposta né di fix. Tutto è fatto per essere forkato e adattato.

---

## Licenza

Arturo è distribuito con licenza **MIT** (vedi [`LICENSE`](LICENSE)): usalo, forkalo, adattalo, anche per lavoro, mantenendo l'avviso di copyright. `skills/prompt-master/` resta sotto la sua licenza MIT originale (`skills/prompt-master/LICENSE`). Se ci trovi dentro qualcosa che non dovrebbe esserci, apri una issue.
