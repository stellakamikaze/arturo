# Il plugin di Arturo: il pacchetto e le prove

Questa pagina dice come `bin/impacchetta.py` genera il plugin dal repository, e cosa hanno provato le prove sul plugin vero. Il contratto degli strati sta in [`strati.md`](strati.md). La catena di fiducia sta in [`fiducia.md`](fiducia.md), il passaggio dal clone al plugin in [`migrazione.md`](migrazione.md).

## Il pacchetto

`python3 bin/impacchetta.py --uscita DIR` genera il plugin dal repository, che resta installabile come clone. Il banco `tests/test_impacchetta_2026_11_03.py` controlla il contratto:
- `.claude-plugin/plugin.json` e `marketplace.json`, con Arturo; il plugin porta anche il mod di Arturo (`skills/arturo`): il suo modulo sta sotto `modules` in `hooks/hooks.json` e il contratto dei tipi in `types` (mod passo 3, 3/11/2026);
- `hooks/hooks.json` dagli hook di `settings.json`, con `"${CLAUDE_PLUGIN_ROOT}/..."` tra virgolette;
- `impostazioni/arturo.json`: il resto di `settings.json`, che `arturo impostazioni applica` unisce ai settings della persona;
- ogni `commands/<nome>.md` diventa `skills/<nome>/SKILL.md` con `name:` e `disable-model-invocation: true`, tranne
  `fine`, `segnala` e `diagnosi`: li lancia anche Claude (`/fine --rotazione` a ogni compito chiuso).

`arturo impostazioni applica` fa un'unione a tre vie: la base è il file di blocco, poi i settings della persona, poi il frammento nuovo. Arturo cambia solo le voci che la persona ha lasciato com'erano. Se una voce è cambiata da tutte e due le parti, il comando non scrive niente e la nomina.

L'unione parte anche quando il plugin si aggiorna fuori da `/aggiorna` (`claude plugin update`, il pannello `/plugin`): l'avvio e il `GIÀ AGGIORNATO` di `/aggiorna` confrontano il frammento della copia con quello del file di blocco, e se sono diversi lo uniscono, solo da una copia che torna col suo MANIFEST firmato. Senza file di blocco non fanno niente: la prima unione la fa `/setup` (#5101, banco FD20).

`arturo impostazioni adotta` è l'ingresso di chi ha già settings fatti a mano, come la config da cui Arturo è nato: scrive il file di blocco col frammento di oggi e non tocca `settings.json`. Le voci di oggi restano della persona, e un `applica` dopo porta solo i cambi futuri di Arturo. Un blocco già scritto da un frammento diverso non si sostituisce senza `--forza`, perché i cambi fra i due andrebbero persi (banco IP11). Una voce che manca conta da lì in poi come tolta dalla persona, quindi `adotta` si ferma se mancano regole di blocco di Arturo, e solo `--forza` le lascia fuori (banco IP12). Un hook doppio ferma sempre, anche con `--forza` (banco IP13).

Un hook nei settings della persona che lancia un file di Arturo registrato anche dal plugin è **doppio**: lo lascia un clone di prima, e scatterebbe due volte. `impostazioni stato` li elenca, `applica` si ferma finché ci sono, `applica --togli-doppi` li toglie e tiene gli hook propri della persona. La copia dei settings di prima resta in `settings.json.prima-di-arturo`. `/setup` lo fa nella FASE 0, col sì della persona (banco IP10).

**Il metodo** (`shared/metodo.md`, sotto i 9.000 caratteri) col plugin entra all'avvio da un hook suo, `hooks/metodo.sh`, che `impacchetta.py` aggiunge a `SessionStart`. Un hook a sé ha il suo tetto di 10.000 caratteri, mentre l'uscita di `session-start.sh` cresce con handoff e memoria. Col clone non scatta: le stesse regole stanno nel CLAUDE.md che la persona scrive con `/setup` (banco IP09).

Col codice fuori da `~/.claude`, l'avvio scrive `~/.claude/arturo/radice` per la barra in basso e dice al modello dove sta il codice.

## Le prove

### Prima prova, 2/11/2026 (macOS, Claude Code 2.1.316)

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

Quarta prova, 5/11/2026 (Claude Code 2.1.318), col primo rilascio pubblicato (`plugin-v0.2.4`, sha 4659345) in un `CLAUDE_CONFIG_DIR` vuoto: `claude plugin marketplace add stellakamikaze/arturo#catalogo` e `claude plugin install arturo@arturo` installano lo sha del tag firmato; `aggiornamenti.py plugin --verifica` dice "GIÀ AGGIORNATO", la deriva tace e fissa l'ancora, la telemetria legge v0.2.4; una guardia cambiata nella cache esce nella riga DERIVA.

Quinta prova, 9/11/2026 (Claude Code 2.1.321, Windows 11, Python 3.11): il banco `tests/test_migra_2026_11_05.py` su un PC Windows, con la CLI vera e un `CLAUDE_CONFIG_DIR` di prova. Migrazione, ritorno e forma upstream passano, 18 casi su 18: la copia di `.git` coi file in sola lettura, gli spostamenti e `claude plugin` reggono. La prova ha trovato due difetti, corretti: le cartelle vuote di Arturo restavano in `~/.claude`, e il comando per tornare indietro usciva con le barre rovesciate. L'avviso dell'avvio su Windows resta spento (`SISTEMI_PROVATI`): il comando che propone parte da `python3`, che su un Windows senza Python vero è lo stub dello Store.

Sesta prova, 13/11/2026 (Claude Code 2.1.317, Mac): una copia del plugin cambiata sullo sha già installato, in un `CLAUDE_CONFIG_DIR` di prova col catalogo vero. `claude plugin install arturo@arturo` risponde "already installed" e `claude plugin update` "already at the latest version": nessuno dei due riscrive la cartella. `claude plugin uninstall --keep-data` seguito da `claude plugin install` la riscrive: tornano il file cambiato e quello tolto, sparisce quello in più, i dati in `plugins/data/` restano, e un plugin spento torna acceso. `aggiornamenti.py plugin` usa questa strada quando la copia non è come il suo MANIFEST firmato, e rispegne il plugin se era spento (#5480, banco FD21).

Da provare: `arturo migra` su Windows da un terminale vero, su un'installazione di una persona; barra in basso dal puntatore su una macchina pulita.

## La testata: dove Arturo si presenta

Il logo di Claude Code non si sostituisce: nessuna opzione dei settings lo cambia e nessun componente dei mod lo ridisegna (verificato su 2.1.317, 3/11/2026). La parte `skills/arturo/hooks/testata` del mod di Arturo piazza con `$.ui.place` il primo blocco sotto l'intestazione: versione di Arturo (`git describe` dal repository che contiene il mod, chiesto a `git rev-parse --show-toplevel` così vale anche da un link in `~/.claude/skills`, altrimenti la radice da `$.plugin.root`, `radiceCodice` di `hooks/parti.ts`; senza git, col plugin, il campo `version` di `.claude-plugin/plugin.json`), versione di Claude Code (`$.session.version()`), deriva (`cache/deriva.json`, scritto da `hooks/deriva.py`) e aggiornamento (`session-env/aggiornamento.json`). I dati stanno nell'Orsa, il codice in Arturo.
