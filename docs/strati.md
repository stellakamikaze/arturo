# Gli strati: Orsa, Arturo, Claude Code

Questo documento dice cosa sta in ogni strato e chi lo cambia. È il contratto da rispettare per ogni file nuovo di Arturo.

```
persona
  └─ Orsa            ~/.claude: CLAUDE.md, personale/<skill>.md, skill proprie, settings della persona,
  │                  memoria Melchior (data/memory), todo, handoff. Arturo non la scrive mai,
  │                  salvo le voci dei settings registrate nel file di blocco.
  └─ Arturo          plugin: guardie (hook), skill e comandi, bin/, motore Melchior, mod,
  │                  output style, metodo iniettato all'avvio
  └─ Claude Code + modello
aggiornamento: cambia solo Arturo. L'Orsa resta com'è; in un conflitto riceve
              la versione della persona, in personale/conflitti/<data>/.
```

## Glossario

- **Orsa**: lo strato personale. Contiene le istruzioni, le preferenze e la memoria di una persona. Cresce sessione dopo sessione e vive in Melchior. Il nome viene da Arturo, "il guardiano dell'orsa".
- **Arturo**: lo strato condiviso. Contiene guardie, metodo e skill uguali per tutti. Lo aggiorna chi mantiene Arturo.
- **Melchior**: il motore della memoria. Il codice sta in Arturo, le note stanno nell'Orsa.
- **File di blocco**: `~/.claude/data/arturo-impostazioni.lock`. Elenca le voci dei settings che Arturo ha scritto, e solo quelle Arturo può cambiare.

## Cosa sta dove

| Cosa | Arturo | Orsa |
|---|---|---|
| Codice | hook, `bin/`, motore Melchior, skill e comandi generici | skill, comandi e hook propri |
| Settings | frammento versionato, applicato con il file di blocco | tutto il resto di `settings.json` |
| Istruzioni | metodo e freni, iniettati all'avvio | `CLAUDE.md`, `personale/<skill>.md` |
| Dati | cache e coda della telemetria in `${CLAUDE_PLUGIN_DATA}` | memoria, todo, handoff, impostazioni di Melchior |
| Preferenze delle guardie | valori di base | `~/.claude/arturo/*.local` |

**Regola d'oro: nessun file esiste in tutti e due gli strati.** Un file copiato in due posti diverge, e l'aggiornamento deve poi scegliere quale tenere.

## Estendere una skill senza copiarla

Se una persona vuole cambiare una skill di Arturo, scrive `~/.claude/personale/<skill>.md`. Un hook lo aggiunge al contesto ogni volta che la skill parte, anche quando la chiama il modello. L'estensione aggiunge e precisa, ma freni e guardie di Arturo vincono sempre.

Se una persona vuole sostituire una skill, scrive una skill con lo stesso nome nell'Orsa. Il nome senza prefisso va alla sua, quella di Arturo resta raggiungibile come `arturo:<nome>`. La sostituzione si dichiara in `personale/sostituzioni.txt`, e `system-audit` segnala ogni omonimo non dichiarato.

## Perché un plugin

Un plugin di Claude Code vive in `~/.claude/plugins/`, fuori dai file della persona. L'aggiornamento sostituisce la sua cartella e non tocca l'Orsa: la separazione la garantisce Claude Code.

Un plugin non può portare alcune cose. Queste le scrive `/setup` nei settings della persona, con il file di blocco:
- i permessi (allow, ask, deny) e `autoMode`;
- `env`, `statusLine` e lo stile di output di base;
- il `CLAUDE.md` (il metodo arriva invece con l'hook di avvio, sotto i 10.000 caratteri).

## Prova del 2/11/2026 (macOS, Claude Code 2.1.316)

Plugin di prova caricato con `--plugin-dir` in una sessione `claude -p`:

| Controllo | Esito |
|---|---|
| Hook SessionStart, UserPromptSubmit, PreToolUse, PostToolUse, Stop | scattano una volta ciascuno, con `CLAUDE_PLUGIN_ROOT` e `CLAUDE_PLUGIN_DATA` |
| Contesto di avvio di 9.400 caratteri | il modello legge la riga in coda |
| `bin/` del plugin nel PATH | sì; `CLAUDE_PLUGIN_ROOT` non c'è nel Bash, quindi uno script trova la sua cartella da `$0` |
| PreToolUse su `Skill` | inietta l'estensione anche quando la skill la chiama il modello |
| Nome senza prefisso | `/sondaruolo` funziona se nessun altro usa il nome |
| Omonimo | con `/inizio` nell'Orsa, la skill del plugin diventa `arturo-spike:inizio` e il nome nudo resta alla persona |

| Variabili nel testo di una skill | Claude Code sostituisce `${CLAUDE_PLUGIN_ROOT}` e `${CLAUDE_SKILL_DIR}` prima che il modello legga; un'altra variabile resta letterale |
| File in `commands/` del plugin | resta solo `/arturo-spike:sondacomando`: il nome senza prefisso ce l'hanno solo le skill con `name:` |

Seconda prova, 3/11/2026, col plugin vero generato da `bin/impacchetta.py` (`claude --plugin-dir`, settings della persona esclusi con `--setting-sources project`):

| Controllo | Esito |
|---|---|
| Hook | ognuno scatta una volta per evento e per tool |
| Comando diventato skill | `/novita` funziona senza prefisso; `$ARGUMENTS` arriva |
| Stile di output | si chiama `arturo:Conciso`: col nome nudo Claude Code non lo applica |
| Mod in `skills/<mod>/.claude-plugin` | dentro un plugin non si caricano: il marketplace li elenca a parte |
| Hook di comando e modulo nello stesso `hooks.json` | scattano tutti e due; il modulo può stare in `../skills/arturo/hooks/` e il tool esce come `mcp__arturo__ruota` (terza prova, 3/11/2026) |
| Agent | gli 8 agent si caricano |

Terza prova, 5/11/2026 (Claude Code 2.1.318), sul pacchetto con il metodo: `impostazioni applica` in una casa vuota, poi `claude -p --plugin-dir` coi settings della persona esclusi (`--setting-sources project`) e `--include-hook-events`:

| Controllo | Esito |
|---|---|
| Hook doppi | zero: i 4 hook di avvio e i 3 del messaggio scattano una volta ciascuno |
| Metodo all'avvio | il modello ne cita la quarta sezione ("Fatto vuol dire verificato") |
| Guardie | i banchi delle guardie lanciati sul pacchetto sono verdi; tre banchi leggono file del repository che il pacchetto non porta (`tests/`, `.gitignore`, `settings.json`) e si lanciano sul repository |
| Login | con una `HOME` finta Claude Code non trova il login: la prova su una macchina pulita la fa una persona (#4565) |

Da provare: Windows (prima di migrare Balthasar); installazione dal catalogo su GitHub (`stellakamikaze/arturo#catalogo`) col primo rilascio del plugin; barra in basso dal puntatore su una macchina pulita.

## Il pacchetto

`python3 bin/impacchetta.py --uscita DIR` genera il plugin dal repository, che resta installabile come clone. Il banco `tests/test_impacchetta_2026_11_03.py` controlla il contratto:
- `.claude-plugin/plugin.json` e `marketplace.json`, con Arturo; il plugin porta anche il mod di Arturo (`skills/arturo`): il suo modulo sta sotto `modules` in `hooks/hooks.json` e il contratto dei tipi in `types` (mod passo 3, 3/11/2026);
- `hooks/hooks.json` dagli hook di `settings.json`, con `"${CLAUDE_PLUGIN_ROOT}/..."` tra virgolette;
- `impostazioni/arturo.json`: il resto di `settings.json`, che `arturo impostazioni applica` unisce ai settings della persona;
- ogni `commands/<nome>.md` diventa `skills/<nome>/SKILL.md` con `name:` e `disable-model-invocation: true`.

`arturo impostazioni applica` fa un'unione a tre vie: la base è il file di blocco, poi i settings della persona, poi il frammento nuovo. Arturo cambia solo le voci che la persona ha lasciato com'erano. Se una voce è cambiata da tutte e due le parti, il comando non scrive niente e la nomina.

Un hook nei settings della persona che lancia un file di Arturo registrato anche dal plugin è **doppio**: lo lascia un clone di prima, e scatterebbe due volte. `impostazioni stato` li elenca, `applica` si ferma finché ci sono, `applica --togli-doppi` li toglie e tiene gli hook propri della persona. La copia dei settings di prima resta in `settings.json.prima-di-arturo`. `/setup` lo fa nella FASE 0, col sì della persona (banco IP10).

**Il metodo** (`shared/metodo.md`, sotto i 9.000 caratteri) col plugin entra all'avvio da un hook suo, `hooks/metodo.sh`, che `impacchetta.py` aggiunge a `SessionStart`. Un hook a sé ha il suo tetto di 10.000 caratteri, mentre l'uscita di `session-start.sh` cresce con handoff e memoria. Col clone non scatta: le stesse regole stanno nel CLAUDE.md che la persona scrive con `/setup` (banco IP09).

Col codice fuori da `~/.claude`, l'avvio scrive `~/.claude/arturo/radice` per la barra in basso e dice al modello dove sta il codice.

## La catena di fiducia (F3, 5/11/2026)

Col clone la fiducia la dà git: si installa solo un tag firmato. Col plugin la cartella del codice è una copia senza git, e Claude Code installa lo sha scritto nel catalogo anche se nessun tag firmato lo indica (prova del 5/11/2026, Claude Code 2.1.318). Quattro pezzi chiudono il buco:

```
rilascio   impacchetta.py --firma → MANIFEST (sha256 di ogni file) + MANIFEST.sig, commit sul ramo plugin,
           tag firmato plugin-vN.N.N → impacchetta.py --catalogo → ramo catalogo: Arturo fissato a tag + sha
/aggiorna  aggiornamenti.py plugin: claude plugin marketplace update → scarica solo il tag → verify-tag con
           l'ancora → lo sha del tag è quello del catalogo? → versione non più vecchia? → claude plugin update
           → la copia installata ha lo sha verificato e torna col suo MANIFEST firmato? → APPLICATO
           un passo che non torna: POSSIBILE COMPROMISSIONE (uscita 3), niente update; firma che il
           computer non sa controllare: FIRMA NON VERIFICABILE (uscita 4)
avvio      deriva.py: la copia in uso ha il MANIFEST firmato? quali file non tornano? → riga DERIVA
telemetria versione dal plugin.json della copia, non dai tag del git dell'Orsa
```

- **L'ancora.** La chiave che verifica sta nell'Orsa, in `~/.claude/arturo/rilasci.allowed_signers`: chi cambia la copia del plugin cambierebbe anche la chiave dentro. La prima verifica riuscita la scrive; dopo cambia solo con una copia nuova verificata con la chiave di prima. Così una chiave nuova entra con un rilascio firmato dalla vecchia, come nel clone.
- **Lo spazio dei nomi.** Il MANIFEST si firma con `ssh-keygen -Y sign -n arturo-manifest`, da stdin: con un file, una `MANIFEST.sig` già presente resta com'era e `ssh-keygen` esce con 0 lo stesso. La chiave dei rilasci vale per `git` e `arturo-manifest` (`firme/rilasci.allowed_signers`).
- **Fuori dal MANIFEST** stanno solo la firma, la cartella `.in_use` che Claude Code aggiunge alla cache e i `__pycache__` che Python scrive accanto agli script.
- **Il catalogo** sta sul ramo `catalogo` del repository: la persona lo aggiunge con `claude plugin marketplace add stellakamikaze/arturo#catalogo`, e `main` resta il clone di Gigi e Filippo fino a F4.
- Il banco `tests/test_fiducia_2026_11_05.py` (FD01-FD09) prova tutto con la CLI vera, in un `CLAUDE_CONFIG_DIR` di prova: tag non firmato, firmato da un'altra chiave, sha dopo il tag, rilascio più vecchio, e un aggiornamento vX → vY che va a buon fine.

## Come un testo di Arturo indica il codice

Due conseguenze della prova:
- **I comandi di Arturo diventano skill** (`skills/<nome>/SKILL.md` con `name:`). Così `/inizio` resta senza prefisso anche nel plugin.
- **Un percorso al codice si scrive `${CLAUDE_SKILL_DIR}/../../bin/...`**. Vale in tutti e due i layout: nel plugin porta alla cartella del plugin, nel clone in `~/.claude` porta a `~/.claude`. Claude Code lo risolve prima della lettura, quindi funziona anche con il tool Read, che non espande le variabili.
- Negli script e negli hook vale `ARTURO_CODICE`: l'hook di avvio lo calcola dalla sua cartella e lo scrive in `$CLAUDE_ENV_FILE` insieme al PATH di `bin/`.
- Negli script Python le due radici vengono da `hooks/radici.py`: `radice_arturo()` è la cartella del codice, calcolata dal file; `radice_orsa()` è `CLAUDE_CONFIG_DIR` o `~/.claude`. Un messaggio che dice alla persona quale comando lanciare usa `comando_arturo()`: col clone scrive `python3 $ARTURO_CODICE/bin/arturo`, col plugin il percorso vero. Da `bin/` si importa con `sys.path.append(<bin>/../hooks)`. Il banco ST08 vieta `Path.home() / ".claude"` e `$ARTURO_CODICE/hooks|bin` scritti a mano, salvo le guardie e le eccezioni che elenca col motivo.
- La memoria (`memoria_accesa()` in `hooks/melchior_match.py`) non guarda più `bin/arturo` accanto agli hook: decidono `ARTURO_MEMORIA` e `"accesa"` in `data/memoria/impostazioni.json`, altrimenti è spenta.

## La testata: dove Arturo si presenta

Il logo di Claude Code non si sostituisce: nessuna opzione dei settings lo cambia e nessun componente dei mod lo ridisegna (verificato su 2.1.317, 3/11/2026). La parte `skills/arturo/hooks/testata` del mod di Arturo piazza con `$.ui.place` il primo blocco sotto l'intestazione: versione di Arturo (`git describe` dal repository che contiene il mod, chiesto a `git rev-parse --show-toplevel` così vale anche da un link in `~/.claude/skills`, altrimenti la radice da `$.plugin.root`, `radiceCodice` di `hooks/parti.ts`), versione di Claude Code (`$.session.version()`), deriva (`cache/deriva.json`, scritto da `hooks/deriva.py`) e aggiornamento (`session-env/aggiornamento.json`). I dati stanno nell'Orsa, il codice in Arturo.
