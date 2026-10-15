# Arturo

> *Arturo — da Arktouros, "il guardiano dell'orsa": la stella più luminosa del cielo boreale, quella che i naviganti usavano per non perdere la rotta.*

Arturo è un **harness per [Claude Code](https://docs.anthropic.com/en/docs/claude-code)**: una configurazione completa di guardrail, workflow di sessione, agenti e skill che trasforma Claude Code da strumento a collaboratore affidabile. Come il suo omonimo celeste, Arturo fa il guardiano — sorveglia i comandi pericolosi, tiene i segreti fuori dalla history git, chiede conferma prima dei punti di non ritorno — e nel frattempo ti dà una rotta: sessioni che si aprono, si chiudono e si riprendono in modo ordinato, anche su più macchine.

È il telaio di una config personale usata quotidianamente in produzione, estratto e igienizzato: **zero dati, zero credenziali, zero riferimenti a infrastrutture private**. Quello che resta è il metodo.

In due righe: **23 guardie e automazioni**, **13 slash command**, **9 subagent**, **5 skill**, una **CLI per i todo** (`arturo todo`) e per il contesto di un progetto (`arturo contesto`), un **server open source** per la telemetria minima e le segnalazioni (`server/`) — più un **curriculum di principi** (`docs/principi/`) e un canale di aggiornamento (`/novita`) pensati per chi parte da zero, anche senza un mestiere tecnico. Il server lo tiene chi mantiene Arturo: a te non serve niente. Nessun server, nessun account, nessun dominio richiesto — solo `git` e le CLI standard.

I todo si vedono anche in una pagina del browser: chiedilo a Claude, oppure scrivi `python3 ~/.claude/bin/arturo web` nel terminale. La pagina è facoltativa e locale: risponde solo sul tuo computer (127.0.0.1), non si collega a internet e si spegne da sola dopo 30 minuti senza la pagina aperta.

---

## In breve

**Per chi è.** Arturo è per chi vuole cominciare a usare Claude Code e non sa da dove partire, anche senza un mestiere tecnico. Ti dà regole di sicurezza già pronte, un modo ordinato di aprire e chiudere il lavoro, e un percorso per imparare i principi.

**Cominciare in tre passi.**

1. Installa Claude Code, `git`, `python3` e `node` (vedi [Requisiti](#requisiti)).
2. Scarica Arturo in `~/.claude` con i comandi di [Installazione](#installazione). Quasi sempre quella cartella esiste già, perché Claude Code la crea al primo avvio: i comandi la mettono da parte prima del download. Su Windows usa Git Bash.
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
2. **Solo `/aggiorna` applica gli aggiornamenti, e solo dopo il tuo sì.** L'avvio della sessione e `/inizio` controllano soltanto se ci sono novità. Se hai collegato un tuo repository privato, `/inizio` sincronizza quello: sono le tue macchine, non codice di altri.
3. **Telemetria minima, accesa di default, e il perché.** Arturo si sviluppa ogni giorno per persone che spesso non sanno dire dove si bloccano. Senza dati d'uso chi lo mantiene non vede le guardie che fermano un lavoro legittimo, gli aggiornamenti che si rompono, i comandi che nessuno usa. Per questo Arturo manda a chi lo mantiene pochi eventi, con un elenco chiuso: `sessione`, `comando` (il nome di un comando di Arturo, mai il testo), `guardia` (il nome della guardia che ha bloccato), `aggiorna` (l'esito di `/aggiorna`), `segnalazione` (il tipo), `deriva` (i file e gli hook di Arturo che hai cambiato o spento: dei file solo la posizione dentro Arturo, che è pubblica), `config` (la config rotta, che parte subito perché spegne le guardie). Con gli eventi partono un id casuale creato da Arturo, la versione e il sistema operativo, con il solo giorno e mai l'ora. Mai prompt, file tuoi, percorsi del tuo computer, nomi, risposte o il tuo percorso a tappe. Il server (`server/`, open source) non salva l'indirizzo IP e tiene gli eventi 12 mesi. Vedi cosa parte con `python3 ~/.claude/bin/arturo telemetria mostra`, la spegni con `python3 ~/.claude/bin/arturo telemetria spegni` o con `DO_NOT_TRACK=1`. Per far cancellare i tuoi dati scrivi a federico@stellakamikaze.org con l'id che ti mostra `mostra`. Gli altri contatti automatici con l'esterno: il controllo degli aggiornamenti (un `git fetch` al massimo ogni sei ore) e l'invio degli eventi (al massimo ogni sei ore, salvo una config rotta, che parte all'avvio). Le segnalazioni di `/segnala` partono solo dopo che hai letto il testo e detto sì, e arrivano solo a chi mantiene Arturo, salvo che tu scelga una issue pubblica su GitHub.
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

1. **La sicurezza sta nei rail, non nell'attrito.** `defaultMode: auto`: il classificatore di Claude Code giudica ogni comando, senza un popup per ogni passo. Sopra di lui i deny espliciti e i hook guard formano una seconda rete, deterministica, che intercetta le operazioni davvero pericolose: una cancellazione ricorsiva fuori dalle cartelle rigenerabili, un invio, un segreto in un commit. Meglio pochi blocchi affidabili che cento popup ignorati per abitudine.
2. **Mai exit-0 muto.** Un check che non gira non è un check passato. Il validation gate distingue "verde" da "assente" — l'assenza di test non è un successo.
3. **Ogni regola è un passivo.** L'harness compensa solo ciò che il modello non può garantirsi da solo: guardie deterministiche, integrazioni, preferenze genuine. Tutto il resto va potato, non accresciuto (la skill `system-audit` include un "Bitter Lesson pass" proprio per questo).

---

## Requisiti

| Strumento | Serve per | Note |
|---|---|---|
| **Claude Code** | tutto | [guida ufficiale](https://docs.anthropic.com/en/docs/claude-code) |
| **git** | sessioni, sync, guardie commit | qualsiasi versione recente |
| **python3** ≥ 3.8 | la maggior parte dei guard | solo standard library, nessun pip. PyYAML, se c'è, rende più preciso l'audit |
| **node** ≥ 18 | `statusline.js`, `context-monitor.js` | |
| **jq** | parsing veloce nel dispatcher | c'è un fallback in `python3` se manca |

**Sistemi.** macOS e Linux. Su Windows Arturo funziona solo dentro **Git Bash** (Git for Windows): senza, Claude Code esegue i comandi con PowerShell e le guardie di Arturo non li vedono. Il `python3` deve essere quello di python.org, non il rimando del Microsoft Store: `/setup` controlla entrambe le cose.

Facoltativi: **`gitleaks`** (audit segreti), **`bw`** (Bitwarden CLI, per le credenziali), **`gws`** (Google Workspace CLI — vedi [onboarding](#onboarding-gws-google-workspace-cli-opzionale)). Lo smoke test di `/system-audit` usa `timeout` se c'è (su Linux e Git Bash sì, su macOS di norma no); senza, gira comunque, solo senza tetto di tempo.

---

## Installazione

Claude Code crea `~/.claude` al primo avvio, quindi la cartella di solito esiste già. Il primo comando la mette da parte con la data nel nome: le tue impostazioni restano lì, niente si perde.

**macOS e Linux** (Terminale), **Windows** (Git Bash, non PowerShell né il Prompt dei comandi):

```bash
[ -d "$HOME/.claude" ] && mv "$HOME/.claude" "$HOME/.claude-backup-$(date +%Y%m%d-%H%M)"
git clone https://github.com/stellakamikaze/arturo.git "$HOME/.claude"
```

Poi apri Claude Code dentro la cartella: `cd ~/.claude && claude`, e scrivi `/setup`.

Oppure, per innestare Arturo su una config esistente: clona altrove e copia `settings.json`, `bin/`, `hooks/`, `commands/`, `agents/`, `skills/`, `shared/`, `output-styles/`, `docs/`, `templates/`, `tools/`, `tests/`, `NOVITA.md` dentro `~/.claude/` (`docs/` e `NOVITA.md` servono a `/sparring`, `/novita` e `/inizio gws`; `templates/` serve a `/strato`; `tests/` ai banchi delle guardie che l'avvio lancia da solo).

> **Il tuo remote.** Il clone qui sopra punta al repo originale, su cui non hai accesso in scrittura. `/fine` salva i commit sulla tua macchina e non prova a pusharli. Se vuoi **sincronizzare le tue modifiche tra più macchine**, crea un tuo repo privato e puntaci `origin`:
> ```bash
> git -C ~/.claude remote rename origin upstream   # Arturo resta raggiungibile: /aggiorna scarica da qui
> gh repo create mio-claude --private --source ~/.claude --remote origin --push
> # oppure, se il repo esiste già:  git -C ~/.claude remote add origin <URL-del-tuo-repo>
> ```

---

## Aggiornare Arturo

Arturo continua a evolvere. All'avvio della sessione ti avvisa quando c'è una versione nuova:

```
ARTURO: c'e' un aggiornamento (3 commit) — scaricalo con /aggiorna
```

**`/aggiorna`** fa il resto: ti dice quale versione hai e quale arriva, ti racconta cosa cambia
nelle guardie, controlla che non travolga le tue modifiche e applica dopo il tuo sì. Se
l'applicazione non riesce, la annulla da sola: la tua copia non resta mai a metà. L'aggiornamento
gira prima in una **copia di prova** a parte, fuori da `~/.claude`. Claude Code legge `settings.json`
e gli hook mentre lavora: un aggiornamento fatto lì dentro, anche se annullato subito, potrebbe
lasciare per un attimo un file rotto. Solo se la copia di prova è integra il risultato arriva in
`~/.claude`. A mano, con lo stesso script della versione in arrivo:

```bash
git -C ~/.claude status --short --untracked-files=no   # deve restare vuoto: vedi sotto
git -C ~/.claude fetch origin main          # upstream invece di origin, se hai un tuo repository
git -C ~/.claude show origin/main:bin/aggiorna-applica.sh > /tmp/aggiorna-applica.sh
bash /tmp/aggiorna-applica.sh ~/.claude rebase origin/main   # con un tuo repository: merge upstream/main
```

La prima parola dell'ultima riga dice com'è andata: `APPLICATO`, `GIÀ AGGIORNATO`,
`APPLICAZIONE NON PARTITA` o `APPLICAZIONE ANNULLATA` (in questi due casi `~/.claude` è com'era).

In entrambi i casi, poi **chiudi e riapri Claude Code**: comandi, hook e skill si caricano all'avvio della sessione,
quindi quelli appena arrivati non compaiono finché non riapri. Se la prima riga elenca dei file,
sono modifiche tue non ancora salvate con un commit (tipico: `/setup` scrive in `settings.json`).
Lo script allora risponde `APPLICAZIONE NON PARTITA` e non tocca niente: salvale con `/fine`, poi
lancia `/aggiorna`. Se un commit tuo tocca gli stessi punti dell'aggiornamento, lo script risponde
`APPLICAZIONE ANNULLATA` con un `CONFLITTO`: `~/.claude` resta com'era e la copia di prova aspetta.
Lancia `/aggiorna` e risolvi con Claude un file per volta, nella copia di prova.

Dopo il primo aggiornamento non serve più ricordarselo: all'avvio della sessione Arturo ti avvisa
quando ci sono novità, **`/aggiorna`** le applica e **`/novita`** te le racconta.

Se un aggiornamento non ti convince, **`/aggiorna indietro`** riporta alla versione di prima: ti
mostra cosa torna indietro, lo fa solo dopo il tuo sì e conserva le modifiche ai tuoi file.

Quali file arrivano con gli aggiornamenti e quali restano tuoi:

| Di Arturo (arriva con gli aggiornamenti) | Tuo (nessun aggiornamento lo tocca) |
|---|---|
| `bin/`, `hooks/`, `commands/`, `agents/`, `skills/`, `shared/`, `output-styles/` (gli stili di Arturo; uno tuo con un nome nuovo resta tuo), `docs/`, `templates/`, `tools/`, `tests/`, `NOVITA.md`, `README.md` | `CLAUDE.md`, `tools/scrapling/.venv/` (il venv di `scrape`), `personale/` (le tue aggiunte ai comandi di Arturo), `hooks/hosts-interni.local`, `hooks/api-fidate.local`, `data/` (compresi i tuoi todo in `data/todo/`), `projects/` e le altre cartelle di lavoro |

`settings.json` è di Arturo, ma le tue modifiche restano come commit locali. `/aggiorna` ti mostra i file cambiati sia da te sia dall'aggiornamento prima di applicare. Se nella copia di prova `settings.json` non è JSON valido o resta un conflitto, l'aggiornamento non arriva in `~/.claude`: un `settings.json` rotto spegnerebbe tutte le guardie. L'avvio della sessione te lo segnala con una riga `CONFIG ROTTA`.

**Arturo convive con la tua config.** Le tue regole, i tuoi comandi e i tuoi permessi restano tuoi. Se vuoi cambiare un comando di Arturo, scrivi le tue aggiunte in `~/.claude/personale/<comando>.md`: quando lanci il comando Claude le legge, e nessun aggiornamento le tocca. Se hai già modificato un comando di Arturo, `/aggiorna personale` sposta le tue modifiche lì. L'avvio ti avvisa con una riga `DERIVA` quando la distanza dalla config di Arturo rischia di rompere qualcosa: un comando di Arturo modificato che andrà in conflitto, un hook di Arturo tolto o spento.

> Se `/aggiorna` o `/novita` rispondono «comando sconosciuto», la tua copia è precedente a quei
> comandi: fai l'aggiornamento a mano con i comandi qui sopra e riapri Claude Code. Da lì in poi bastano gli slash.

## Prima accensione — checklist

> **La via rapida: `/setup`.** Apri Claude Code dentro `~/.claude` e lancia **`/setup`**: ti guida passo-passo in tutta la configurazione qui sotto (prerequisiti, permessi, `PROJECTS_BASE`, lingua, `CLAUDE.md`, sync, verifica finale), una cosa alla volta e in linguaggio semplice. È il modo consigliato, soprattutto se non sei un programmatore. La checklist qui sotto è la versione manuale, per chi preferisce farla a mano.

1. **`settings.json` → `env.PROJECTS_BASE`** — la cartella dove vivono i tuoi progetti (default `~/Documents/ClaudeCode`). Vale per `/progetto` e `/inizio`.
2. **Host interni** — le guardie conoscono solo regole pubbliche: `localhost` e le reti locali (`10.x`, `172.16.x`-`172.31.x`, `192.168.x`, gli indirizzi Tailscale `100.64.x`, link-local e IPv6 locali). Un nome `.ts.net` non conta come interno, perché con Tailscale Funnel può essere pubblico. I tuoi host personali, compresi quelli della tua tailnet, vanno in `hooks/hosts-interni.local` (una voce per riga, hostname o rete), non nei file `.py`. Le API esterne che usi con la tua chiave (fatturazione, CRM) vanno in `hooks/api-fidate.local`, un nome host esatto per riga: un POST verso di loro non chiede conferma.
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
   │ invio email/messaggi → comms-guard.py                 │ ask
   │ rm, config, segreti, avvio auto → block-dangerous.py  │ blocco o ask
   │ POST/upload → exfil-guard.py                          │ ask
   │ GET-exfil → disattivato per scelta di attrito          │
   │ SQL, volumi, rsync → data-guard.py                    │ ask
   │ gh → gh-destructive-guard.py                          │ blocco o ask
   │ memoria e handoff (nessuna guardia ha deciso) → allow │ allow
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
hooks/               23 guardie e automazioni, più 4 strumenti che usano
bin/                 La CLI arturo e i suoi moduli
tools/scrapling/     scrape: lettura di una pagina web senza browser (facoltativo, si installa da /setup)
server/              Il server della telemetria e delle segnalazioni (Cloudflare Worker, open source)
commands/            13 slash command di workflow (incl. /setup, /aggiorna, /guidami, /novita, /strato, /segnala)
agents/              9 subagent specializzati
skills/              5 skill (+ regole condivise in shared/)
output-styles/       Due stili di scrittura: Guida (di partenza) e Conciso (si sceglie in /setup)
docs/principi/       Il curriculum: i principi spiegati in semplice
docs/esercizi.md     Gli esercizi del percorso a tappe (/percorso)
docs/onboarding/     Guide di setup guidato (/inizio gws)
docs/impeccable.md   Come installare Impeccable (design delle interfacce) dall'upstream
docs/referente.md    Guida del referente di un'organizzazione (/strato)
templates/strato/    Modello di plugin per lo strato di un'organizzazione (/strato crea), con esempi da adattare
tests/               I banchi di prova: il gate completo e i banchi delle guardie che l'avvio lancia da solo
NOVITA.md            Canale di aggiornamento (lo racconta /novita)
```

### I guardiani (`hooks/`)

Instradati dal dispatcher:

| Guard | Cosa intercetta | Esito |
|---|---|---|
| `block-dangerous.py` | `rm` ricorsivi su tree protetti, export vault, scrittura su config/hook (anche via `cd`), creazione di file di unlock, lettura segreti via shell (incl. `perl`/`ruby`/`nc`/redirezioni e comandi dentro `$(...)`), `curl\|bash` e sue varianti (process-sub, `eval`, pipe verso interpreti), fork bomb, `docker volume rm`. Un `rm` ricorsivo si riconosce anche con le opzioni separate, in una subshell, dentro `sh -c` o `eval`, e dietro `xargs`, dove chiede sempre. Una scrittura shell su un `CLAUDE.md` chiede conferma. Una scrittura shell su un git hook o su un servizio di avvio (`~/Library/LaunchAgents`, `~/.config/systemd/user`, `~/.config/autostart`) chiede conferma. Il testo di un heredoc verso python o `cat`, un messaggio `-m` e il pattern di `grep` non contano come comandi o file letti | blocco/conferma |
| `commit-secret-gate.py` | segreti nel diff staged (e nel working tree su `git commit -a`), anche nei file aggiunti nello stesso comando, prima di ogni `git commit` / `gh pr create`; se il controllo va oltre il tempo, chiede | conferma |
| `data-guard.py` | SQL distruttivo (DROP/TRUNCATE/DELETE senza WHERE), `docker compose down -v`, `rsync --delete` verso host remoti, overwrite di file `.db` | conferma |
| `exfil-guard.py` | esfiltrazione verso host esterni: POST e upload (curl/wget/python); il ramo GET è disattivato per scelta di attrito. Giudica il codice eseguito (senza gli heredoc scritti su file). Le API in `hooks/api-fidate.local` passano | conferma |
| `comms-guard.py` | invio email/messaggi da CLI (sendmail, msmtp, `mail`, gws, smtplib, `http.client`, `git send-email`, AppleScript Mail...) — policy draft-first. Chiede conferma invece di bloccare: il blocco insegnava a Claude ad aggirare la regex. Giudica il codice eseguito: `comms-prefilter.py` toglie gli heredoc scritti su file e tace sulle letture (`grep -ril smtplib`), mentre `find -exec`, `awk system()` e `sed` contano come esecuzione | conferma |
| `gh-destructive-guard.py` | operazioni GitHub distruttive (repo delete anche via GraphQL, secret, api DELETE/PUT/PATCH) → blocco; mutazioni GraphQL, query lette da file e POST anche impliciti (`-f`/`-F`/`--input`) → conferma; anche con prefisso `env`/`command` | blocco / conferma |

Fuori dal dispatcher:

- `protect_claude_md.py` — PreToolUse: protegge `CLAUDE.md`, settings e hook da modifiche via `Edit`/`Write` senza file di unlock, e i percorsi di avvio automatico (`.git/hooks`, `~/Library/LaunchAgents`, `~/.config/systemd/user`, `~/.config/autostart`) con un unlock di sistema; scrivere un file di unlock chiede sempre conferma. Avvisa quando il `CLAUDE.md` globale supera il budget di righe (`ARTURO_CLAUDE_MD_RIGHE`, default 200).
- `web-egress-guard.py` — PreToolUse su `WebFetch`, jina, tavily, `browser_navigate` (anche Firefox) e Claude in Chrome (`navigate` e `browser_batch`): esfiltrazione via URL verso host esterni.
- `credential-leak-scanner.py` — PostToolUse: rileva token e chiavi negli output di Bash/WebFetch/MCP. L'avviso arriva a Claude, non solo a te (`additionalContext`).
- `prompt-injection-scanner.py` — PostToolUse: segnala tentativi di prompt injection nei contenuti esterni (pattern EN + IT). Anche questo avviso arriva a Claude.
- `memoria-scrittura.py` — PostToolUse, sempre acceso: controlla le note di memoria e gli handoff che Claude scrive (password, chiavi, istruzioni nascoste). `memoria-richiamo.py` e `memoria-subagente.py` sono la memoria facoltativa, spenta di default: vedi «La memoria (facoltativa)».
- `emoji_remover.py` — PostToolUse: niente emoji decorative nei file (i simboli tecnici legittimi sono whitelistati).
- `context-monitor.js` — avvisa quando il context si avvicina alla soglia di rotazione.
- `session-start.sh` / `session-end.sh` — titolo finestra, riga `MACCHINA`, avvisi Git locali, file della config modificati e non salvati, controllo della deriva (`deriva.py`), banchi delle guardie in background ogni 12 ore (`tests/banchi-avvio.sh`, un rosso si dice all'avvio; `ARTURO_BANCHI_AVVIO=0` li spegne), avvio della telemetria (`arturo telemetria`), invito a `/segnala` (si spegne con `arturo segnala basta`), promemoria di chiusura anche senza file cambiati e cleanup degli unlock di sessione.
- `controlla-config.py` — strumento, non un hook: controlla che la config sia integra (`settings.json` valido, nessun rebase o conflitto a metà) e stampa `CONFIG OK` o `CONFIG ROTTA`. Lo usano l'avvio, `/inizio`, `/aggiorna` e `/fine`.
- `deriva.py` — strumento, non un hook: all'avvio misura quanto la tua config si è allontanata da quella di Arturo (comandi e file di Arturo modificati, hook di Arturo tolti o spenti, config rotta) e stampa una riga `DERIVA` solo se c'è da fare.
- `inject-now.sh` — inietta data/ora corrente a ogni prompt. Quando lanci un comando con aggiunte tue in
  `personale/`, dice a Claude di leggerle. Sui messaggi che non sono comandi ricorda che un lavoro su più
  file, con effetti fuori dal computer o ambiguo comincia con PROMPT + BRIEF; domande e richieste
  chiare e piccole hanno risposta diretta. Per spegnere il promemoria, cancella il blocco `cat` finale
  dello script.
- `input-notifier-start.sh` — notifica quando Claude aspetta input.
- `statusline.js` — statusline con modello abbreviato, task in corso, progetto@ramo (`*` se ci sono modifiche), uso del contesto e quota delle finestre di 5 ore e 7 giorni.
- `typecheck-after-edit.py` — PostToolUse: dopo una modifica a un file `.ts`, `.tsx` o `.vue` lancia il type-check del progetto (lo script `typecheck` o il `tsc`/`vue-tsc` del `build`) e manda gli errori a Claude. Fuori da un progetto TypeScript tace.
- `bozze-mcp-auto-approve.py` — PreToolUse: la creazione di una bozza via un collegamento (`create_draft`, `slack_send_message_draft`) non chiede conferma; l'invio, la pubblicazione e la cancellazione di una bozza sì.
- `forma_comando.py` — modulo, non un hook: ricava i programmi che un comando esegue davvero (path completo, blocchi, `sh -c`, `eval`). Lo usano `block-dangerous.py` e il dispatcher (git puro, ramo memoria).

**Cosa registrano gli hook per la telemetria.** Ogni hook scrive al massimo una riga nella coda
`~/.claude/data/telemetria/coda.jsonl`, senza rete; la coda parte in un lotto al massimo ogni sei ore.
`session-start.sh` registra l'evento `sessione` e manda la coda in background. `inject-now.sh`
registra `comando` con il nome di un comando di Arturo, mai il testo del prompt: un comando tuo o
dello strato della tua organizzazione non si registra. `bash-dispatcher.sh` registra `guardia` con il
nome della guardia che ha bloccato, mai il comando. `bin/aggiorna-applica.sh` registra `aggiorna` con
l'esito. `deriva.py` registra `deriva` solo quando cambia l'elenco dei file e degli hook di Arturo
cambiati o spenti, e `config` una volta al giorno se la config è rotta. Con la telemetria spenta nessuno di loro scrive. `python3 ~/.claude/bin/arturo telemetria mostra`
fa vedere la coda così come parte.

### La rotta (`commands/`)

Setup: **`/setup`** — configurazione guidata dell'intero harness per un nuovo utente (prerequisiti, permessi, `PROJECTS_BASE`, `CLAUDE.md`, sync, verifica); pensato anche per chi non programma.

Manutenzione: **`/aggiorna`** — scarica e applica l'ultima versione di Arturo, dopo averti mostrato cosa cambia e controllato che non travolga le tue modifiche. **`/aggiorna personale`** sposta le tue modifiche ai comandi di Arturo in `personale/`, dove gli aggiornamenti non vanno in conflitto.

Ripresa: **`/guidami`** — guarda gli ultimi handoff e le conversazioni recenti e ti propone tre o quattro cose che ha senso fare adesso, con il motivo e il primo passo. Per quando riapri e non sai da dove ripartire.

Pedagogia: **`/novita`** — racconta gli aggiornamenti dell'harness non ancora visti (cosa cambia, il principio dietro); **`/sparring`** — prende un principio del curriculum e lo prova sul lavoro reale dell'utente, con esperimenti piccoli e reversibili. Vedi [Imparare con Arturo](#imparare-con-arturo).

Il ciclo di lavoro quotidiano:

`- **`/inizio <progetto>`** — sync della config, poi il contesto del progetto in una chiamata (`arturo contesto`: git, ripartenza degli handoff recenti, todo aperti divisi per chi agisce, scadenze), il confronto dei todo con `git log` (quelli già fatti non risorgono) e la scelta del lavoro. Con `--tutti` aggiorna anche ogni progetto della cartella dei progetti; con `-- <compito>` parte subito sul compito. `/inizio gws` avvia invece l'onboarding gws.`
`- **`/fine`** — inventario dei file della sessione e dove va ognuno, review di completezza per le modifiche di codice, validate, commit selettivo e handoff con la tabella dei todo pendenti e di chi agisce. Un controllo (`bin/handoff-gate.sh`) ferma un handoff senza tabella, con un todo inesistente o con un segnaposto mai compilato; tiene gli ultimi 5 handoff per progetto e rigenera l'indice `data/handoffs/INDEX.md`. Alla fine chiede se Arturo si è inceppato o se ti manca qualcosa (al massimo una domanda a settimana, oppure subito dopo un intoppo).`
- **`/segnala`** — manda a chi mantiene Arturo un problema, un'idea o uno strumento da collegare. La bozza la scrive Claude, senza nomi né segreti. Tu la leggi e dici sì: arriva direttamente a chi mantiene Arturo, senza account né email da mandare. Se preferisci, diventa una issue pubblica su GitHub. Se non vuoi più gli inviti a segnalare: `python3 ~/.claude/bin/arturo segnala basta`.

Sviluppo: `/progetto` (da idea a primo commit), `/discovery`, `/write-plan`, `/diagnosi` (disciplina diagnostica: fatti prima delle ipotesi; si chiama così per non nascondere il `/debug` di Claude Code).

Organizzazioni: **`/strato`** — lo strato di un'organizzazione sopra Arturo (chi siete, voce, lavori ricorrenti, dati riservati), come plugin nel vostro repository privato. Il referente lo prepara con `/strato crea` e lo pubblica con `/strato pubblica`; i colleghi lo ricevono con `/strato installa`. Guida del ruolo: [`docs/referente.md`](docs/referente.md).

Qualità: usa le capacità native di review e verifica dell'harness.

### L'equipaggio (`agents/`)

Subagent con un mestiere solo, richiamati a mano: `architecture-reviewer`, `bug-finder`, `structural-completeness-reviewer`, `doc-reviewer`, `performance-profiler`, `ui-ux-consultant`, `test-runner`, `researcher`, `fact-checker`.

### Le skill (`skills/`)

- **`shared/validation-gate.md`** — il gate: riconosce il linguaggio del progetto (Node, Python, prosa) con `bin/validation-gate-lang.sh` e legge l'exit da file, mai da una pipe. Esce verde, rosso o «inconclusivo»: la prosa e gli strumenti assenti non sono mai un verde. Spiega anche come provare un banco nuovo con `bin/gate-run.sh` (prima il veleno, poi il gate) e come confrontare i file serviti dopo un deploy con `bin/sonda_servito.py`.
- **`shared/lavori-lunghi.md`** — un comando che dura più di due minuti va in background. Per un lavoro che deve sopravvivere alla sessione c'è `bin/bgjob.sh`: log, PID e un marker con l'exit code in `data/logs/bgjobs/`.
- **`system-audit`** — audit dell'harness: hook diretti e transitivi, smoke test, frontmatter YAML, permessi, slash-comandi citati nei documenti senza una skill o un comando dietro, peso dei corpi, plugin installati e non attivi. `--strict` fallisce se manca un requisito. Il banco avvelenato `skills/system-audit/tests/banco-gate.sh` lavora su una copia e non tocca la tua `~/.claude`.
- **`prompt-master`** — due modalità: un prompt pronto da incollare in un altro tool AI, oppure il **brief interno**: prima di un lavoro che tocca più file, ha effetti fuori dal computer o si può capire in due modi ricostruisce il contesto che manca, riscrive la richiesta come la eseguirà (il **prompt**) e mostra obiettivo, output, vincoli, criterio di fatto, assunzioni e ambiguità (il **brief**). Domande e richieste chiare e piccole hanno risposta diretta. L'hook `inject-now.sh` lo ricorda sui messaggi che non sono comandi (upstream `nidhinjs/prompt-master`, MIT).
- **`todo`** — quando dici «ricordami di…» o chiedi cosa c'è da fare, Claude usa la CLI `arturo todo`. I todo stanno in un archivio sul tuo computer (`data/todo/eventi.jsonl`), divisi per progetto, scadenza e chi agisce: tu, tu che decidi e poi Claude, oppure Claude. `/fine` ci scrive quello che resta, `/inizio` lo rilegge. Da terminale: `python3 ~/.claude/bin/arturo todo aiuto`. Se chiedi di vederli in una pagina, Claude avvia `arturo web`: una pagina nel browser che risponde solo sul tuo computer.
- **`percorso`** — quando chiedi «a che punto sono?» o scrivi `/percorso`, Claude lancia `arturo percorso` e ti mostra la tappa (Osserva, Prova, Delega, Orchestra) con il todo che la prova, le cose che tieni per te e un esercizio della settimana sul tuo lavoro. Conta le decisioni che tieni, non il lavoro che deleghi. Il calcolo e lo stato restano sul tuo computer. I todo da cui nasce viaggiano come gli altri todo: solo verso il tuo repository privato.
- **`italiano-semplificato`** — riscrive o controlla un testo con l'Italiano Tecnico Semplificato (63 regole): frasi corte, voce attiva, una parola per concetto, senza burocratese né slop AI. Una seconda passata cerca i tic di ritmo e struttura del testo generato (contrasti inventati, terne automatiche, chiuse a sentenza): il catalogo è in italiano e scritto da zero.

**Gli altri mod.** Claude Code li carica da soli dalle loro cartelle in `skills/`, come `/dafare`. Per spegnerne uno: `/plugin`, poi il mod, poi disattiva. Attenzione a `redazione-segreti` e `blast-radius`: sono i mod che proteggono. Spenti, Claude legge i segreti in chiaro e un `rm -rf` parte senza mostrarti cosa cancella.

- `skills/redazione-segreti/` sostituisce i segreti negli output dei tool con la loro forma (`[REDATTO:tipo len=N sha256=…]`) prima che Claude li legga, e blocca la scrittura di una sigla su disco. `credential-leak-scanner.py` resta come rete.
- `skills/riscrivi-bash/` fa comportare zsh, la shell del Mac, come bash, che è la shell che Claude scrive: un glob che non trova file non ferma il comando, una parola che inizia con `=` resta una parola, una variabile si spezza in parole. Corregge anche un glob non quotato in un'opzione (`--include=*.md`) e toglie `timeout`, che sul Mac non esiste. I blocchi di `bash-dispatcher.sh` restano come rete.
- `skills/blast-radius/` ferma `rm -rf`, `git reset --hard`, `git clean`, un push forzato e le migrazioni, e ti mostra cosa cambierebbero: quanti file spariscono, quali modifiche si perdono, quali commit. Scegli Procedi o Annulla. Non ferma la pulizia dei file temporanei e non scatta quando nessuno può rispondere (`claude -p`). È codice di Anthropic in copia fissata, tradotto e letto riga per riga: provenienza e licenza nella sua cartella.
- `skills/cache-fredda/` scrive sotto il prompt, solo quando serve, tre avvisi: la cache è scaduta (dopo un'ora con l'abbonamento, dopo 5 minuti a quota piena) e il prossimo messaggio riscriverebbe tutto il contesto; i banchi delle guardie, che l'avvio lancia da solo ogni 12 ore, sono rossi (lo dice anche la riga `GUARDIE` dell'avvio, con lo stesso rimedio: `bash ~/.claude/tests/banchi-avvio.sh`); un account di `gws` ha il token in errore e va rifatto il login. Se tutto è in regola, non scrive niente.
- `skills/apri/` aggiunge `/apri`: apre l'ultimo link o file citato nelle risposte con il programma predefinito del sistema (il browser per i link, l'app di solito per i file). `/apri 2` apre il secondo della lista, `/apri <parola>` il primo che la contiene, `/apri lista` mostra gli ultimi dieci. Non usa un turno del modello.
- `skills/gws/` aiuta con la CLI `gws`: se un comando fallisce per credenziali mancanti o scadute, Claude lo dice subito e ti chiede di rifare il login invece di riprovare con altri account. Corregge anche `gws gmail messages` in `gws gmail users messages`. Il setup degli account resta in [`docs/onboarding/gws.md`](docs/onboarding/gws.md).

**Il pannello dei todo (`/dafare`).** Scrivi `/dafare` e si apre un pannello con le tue cose da fare, divise come in `arturo todo`. Scegli una riga con il numero (o con `j` e `k`) e premi una lettera: `f` fatto, `s` ferma, `r` riprendi, `c` chi lo fa, `a` avvicina, `l` allontana, `u` annulla, `p` cambia progetto, Esc chiude. `/dafare libro` apre solo il progetto `libro`. Quando hai cose aperte, sopra il prompt compare una riga («3 cose da fare · /dafare per vederle»): `/dafare nascondi` la spegne, `/dafare mostra` la riaccende. Il pannello scrive solo con la CLI `arturo todo`, chiede Claude Code 2.1.287 o successivo e si spegne con `claude plugin disable dafare@skills-dir`. La cartella `skills/dafare/` ha `.claude-plugin/plugin.json` al posto di `SKILL.md`: è un mod di Claude Code, non una skill, e non entra nel conteggio delle skill.

---

**La memoria (facoltativa).** Claude Code salva da solo alcune note sulle sessioni passate, in
`~/.claude/projects/*/memory/`: cosa preferisci, cosa hai deciso, dove stanno le cose. Di solito le
rilegge solo nel progetto in cui le ha scritte. La memoria di Arturo le rende utili ovunque, ed è
spenta finché non la accendi (`/setup` te lo chiede, oppure `python3 ~/.claude/bin/arturo memoria accendi`).
Quando è accesa:

- a ogni tuo messaggio `memoria-richiamo.py` cerca le note che parlano della stessa cosa e ne dà a
  Claude il percorso. Claude apre una nota solo se gli serve. Sotto una soglia di pertinenza tace;
- `memoria-subagente.py` dice ai subagenti che la memoria esiste e come cercarla.

`arturo memoria cerca "parole"` cerca a mano, anche a memoria spenta. `arturo memoria controlla`
trova note senza descrizione, frontmatter illeggibili e link rotti. `arturo memoria cartella aggiungi
<cartella>` aggiunge una tua cartella di note markdown (con `name` e `description` in testa).
`arturo memoria spegni` la spegne: le note restano dove sono. Tutto resta su questo computer:
nessun server, nessun archivio nuovo, e niente della memoria entra nella telemetria.
L'interruttore sta in `~/.claude/data/memoria/`, fuori da git; `ARTURO_MEMORIA=0` lo scavalca.

Una parte resta sempre accesa, anche a memoria spenta: `memoria-scrittura.py` controlla ogni nota e
ogni handoff che Claude scrive. Se dentro c'è una password, una chiave o un'istruzione nascosta,
Claude riceve un avviso. Il valore trovato non viene mai stampato.

## Cosa NON c'è (di proposito)

Arturo è stato estratto da una config che include anche una memoria su server, un task manager centralizzato e integrazioni con server privati. Quei pezzi **non ci sono** e le loro funzioni sono coperte in modo autosufficiente:

| Al posto di... | Arturo usa |
|---|---|
| Task manager su server | l'archivio locale dei todo (`arturo todo`, in `data/todo/`) + `TaskList`/`TaskCreate` nativi per i passi della sessione |
| Memoria su database/server | il tuo `CLAUDE.md`, gli handoff in `data/handoffs/` e, se la accendi, la memoria facoltativa: le note di Claude Code su questo computer (`arturo memoria`) |
| Sync su server privato | il repo git stesso: `data/handoffs/` e `data/todo/` viaggiano con la config, solo se il suo remote è privato |

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
4. **`/novita`** — quando l'harness si aggiorna (`/aggiorna`), all'avvio della sessione
   Arturo ti avvisa; `/novita` racconta cosa è cambiato, il principio dietro, e ti
   propone lo sparring. Così l'harness — e chi lo usa — restano aggiornati insieme.
5. **Il percorso** — chiedi «a che punto sono?» o scrivi `/percorso`. Quattro tappe (Osserva,
   Prova, Delega, Orchestra) che si aprono con segni di giudizio: una decisione presa prima del
   lavoro di Claude, un limite dichiarato, un no motivato. Delega chiede due segni insieme: una
   decisione e un limite (o un no motivato). Ogni settimana un esercizio dal tuo
   lavoro vero ([`docs/esercizi.md`](docs/esercizi.md)) e il capitolo
   [Tieni la decisione](docs/principi/05-tieni-la-decisione.md). Il percorso resta sul tuo
   computer.

Le novità vivono in [`NOVITA.md`](NOVITA.md), la entry più recente in cima.

---

## Personalizzazione

- **Più/meno attrito.** In modalità `auto` decide il classificatore di Claude Code; la protezione deterministica sono deny + guard. Vuoi che Claude chieda conferma più spesso? Metti `defaultMode: "default"` in `settings.json`. Vuoi meno interruzioni? Aggiungi pattern specifici all'`allow`.
- **Host interni e API fidate.** `INTERNAL_HOSTS` e `INTERNAL_NETS` in `exfil-guard.py` e `web-egress-guard.py` sono i default pubblici: non modificarli. Se lavori con un tuo server, aggiungi il suo hostname o la sua rete in `hooks/hosts-interni.local`, una voce per riga: le chiamate verso quegli host non chiederanno conferma. Una rete più larga di `/8` viene ignorata. Un servizio esterno che usi con la tua chiave va in `hooks/api-fidate.local`, un nome host esatto per riga (niente reti, niente `*`). I due file sono tuoi, nessun aggiornamento li tocca.
- **Lingua.** `language` in `settings.json` (default `italian`) e i messaggi dei guard sono in italiano — cambiali se preferisci un'altra lingua.
- **Disattivare un guard.** Commenta la riga corrispondente in `bash-dispatcher.sh` (per i guard instradati) o rimuovi il blocco da `settings.json` (per quelli PostToolUse). Poi rilancia `/system-audit`.
- **Cambiare un comando di Arturo.** Non modificare `commands/<comando>.md`: scrivi le tue aggiunte in `~/.claude/personale/<comando>.md` (oppure lascia che `/aggiorna personale` le sposti lì). Claude le legge quando lanci il comando, `/fine` le sincronizza solo verso un tuo repository privato, e nessun aggiornamento le tocca.
- **Aggiungere un comando o una skill.** Un file `.md` in `commands/` diventa uno slash command; una cartella con `SKILL.md` in `skills/` diventa una skill. Il frontmatter `name` + `description` è obbligatorio (`/system-audit` lo verifica).

---
- **Pulizia mensile.** `bash ~/.claude/bin/monthly-cleanup.sh --prova` elenca cosa toglierebbe (tasks, shell-snapshots e paste-cache vecchi di Claude Code, cache dei package manager) senza toccare niente. Senza `--prova` pulisce. Facoltativi: `PULIZIA_CARTELLA_PROGETTI=<cartella>` archivia in `_archivio/` i file sciolti fermi da 60 giorni (li sposta, non li cancella), `PULIZIA_PREFISSI_LAUNCHAGENT="com.esempio."` segnala su macOS i tuoi LaunchAgent non caricati, `PULIZIA_CACHE=0` salta le cache.

## Sicurezza

- Il dispatcher converte un errore o output spurio di una guardia in `ask`. I singoli guard restano conservativi sui pattern riconosciuti.
- `commit-secret-gate.py` chiede conferma se trova un segreto nel diff del repository destinatario. Non confermare credenziali reali.
- Le operazioni GitHub distruttive via `gh` CLI restano coperte dal dispatcher.
- Questo repo è periodicamente auditato (segreti, dati personali, bypass dei guard) prima di ogni pubblicazione. Se trovi qualcosa che non dovrebbe esserci — un segreto, un dato personale, un modo per aggirare una guardia — segnalalo in privato secondo [`SECURITY.md`](SECURITY.md), non con una issue pubblica.

---

## Multi-macchina

Il repo config **È** il canale di sync: `/fine` committa e pusha, `/inizio` scarica le modifiche delle tue altre macchine. Anche il sync passa dalla copia di prova di `/aggiorna`: se il risultato non è integro, la config resta com'era e `/inizio` te lo dice. Gli handoff stanno solo in `~/.claude/data/handoffs/`, mai nel repository del progetto, ed entrano nel push solo se `gh repo view` dice che il remote della config è privato. Lo stesso vale per i todo in `~/.claude/data/todo/`: il file è un registro in cui ogni modifica è una riga in più, e `.gitattributes` lo unisce senza conflitti. Se due macchine creano offline un todo con lo stesso numero, il più recente prende un numero nuovo e `arturo todo` te lo dice. `session-start.sh` avvisa se la macchina è rimasta indietro rispetto a `origin/main`. Per usarlo su più macchine: clona il **tuo** fork/repo privato (vedi [Installazione](#installazione)) come `~/.claude` su ognuna.

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
| Un guard chiede conferma su un comando legittimo | falso positivo del pattern | conferma ed esegui; se ricorre, scrivi `/segnala` (o apri una issue col comando esatto) |
| Commit bloccato con un messaggio che *parla* di comandi pericolosi | il messaggio contiene un pattern come `curl\|bash` | usa `git commit -F file` (il guard scansiona il comando, non il file) |
| Nessun titolo nel terminale su macOS | `session-env/` mancante (creata al primo avvio) | innocuo; si risolve da solo |
| `/system-audit` segnala `cita /qualcosa, che non esiste` | un documento cita un comando tolto o rinominato | correggi la riga; se è un comando nuovo di Claude Code, aggiungilo a `NATIVE` in `skills/system-audit/audit.sh` |
| `scrape` esce 3 con «bloccato» | il sito rifiuta le richieste automatiche | apri la pagina nel browser: `scrape` non prova a superare le verifiche anti-bot |

---

## Autore e manutenzione

Arturo è un progetto di **Federico Nejrotti** — autore, non programmatore: questo harness
è anche la dimostrazione della sua stessa tesi, che il metodo conta più del codice. La
history del repo è volutamente neutra; la firma sta qui.

Arturo si sviluppa ogni giorno: è l'estratto di una configurazione usata in produzione, e
le novità arrivano a chi lo usa con `/aggiorna`. Gli impegni verso chi lo usa stanno in
[Impegni](#impegni). Le segnalazioni sono benvenute e vengono lette: il modo più semplice è
`/segnala`, che scrive la segnalazione con te e la consegna. Non c'è promessa di risposta né di fix. Tutto è fatto per essere forkato e adattato. Come si rilascia una
versione — branch, gate, novità, cosa succede se lo sviluppo si ferma — sta in
[`docs/manutenzione.md`](docs/manutenzione.md).

---

## Licenza

Arturo è distribuito con licenza **MIT** (vedi [`LICENSE`](LICENSE)): usalo, forkalo, adattalo, anche per lavoro, mantenendo l'avviso di copyright. `skills/prompt-master/` resta sotto la sua licenza MIT originale (`skills/prompt-master/LICENSE`). Se ci trovi dentro qualcosa che non dovrebbe esserci, segnalalo in privato secondo [`SECURITY.md`](SECURITY.md).
