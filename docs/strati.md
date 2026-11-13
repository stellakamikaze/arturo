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
| Identità di Git e venv di `scrape` | `bin/identita-git.sh`, `tools/scrapling/setup.sh` | `~/.claude/arturo/git-identita`, `~/.claude/data/scrapling/.venv` |

**Regola d'oro: nessun file esiste in tutti e due gli strati.** Un file copiato in due posti diverge, e l'aggiornamento deve poi scegliere quale tenere.

## Estendere una skill senza copiarla

Se una persona vuole cambiare una skill di Arturo, scrive `~/.claude/personale/<skill>.md`. Un hook lo aggiunge al contesto ogni volta che la skill parte, anche quando la chiama il modello. L'estensione aggiunge e precisa, ma freni e guardie di Arturo vincono sempre.

Se una persona vuole sostituire una skill, scrive una skill con lo stesso nome nell'Orsa. Il nome senza prefisso va alla sua, quella di Arturo resta raggiungibile come `arturo:<nome>`. La sostituzione si dichiara in `personale/sostituzioni.txt`: un nome per riga (skill, comando o `name:` di uno stile), col motivo dopo `#`. `arturo personale omonimi` e `system-audit` nominano ogni omonimo non dichiarato e ogni riga che non ha più un omonimo (banco `tests/test_sostituzioni_2026_11_05.py`, SO01-SO05). Senza dichiarazione, una skill nuova di Arturo con un nome che la persona usa già non si vedrebbe mai.

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

Quarta prova, 5/11/2026 (Claude Code 2.1.318), col primo rilascio pubblicato (`plugin-v0.2.4`, sha 4659345) in un `CLAUDE_CONFIG_DIR` vuoto: `claude plugin marketplace add stellakamikaze/arturo#catalogo` e `claude plugin install arturo@arturo` installano lo sha del tag firmato; `aggiornamenti.py plugin --verifica` dice "GIÀ AGGIORNATO", la deriva tace e fissa l'ancora, la telemetria legge v0.2.4; una guardia cambiata nella cache esce nella riga DERIVA.

Quinta prova, 9/11/2026 (Claude Code 2.1.321, Windows 11, Python 3.11): il banco `tests/test_migra_2026_11_05.py` su un PC Windows, con la CLI vera e un `CLAUDE_CONFIG_DIR` di prova. Migrazione, ritorno e forma upstream passano, 18 casi su 18: la copia di `.git` coi file in sola lettura, gli spostamenti e `claude plugin` reggono. La prova ha trovato due difetti, corretti: le cartelle vuote di Arturo restavano in `~/.claude`, e il comando per tornare indietro usciva con le barre rovesciate. L'avviso dell'avvio su Windows resta spento (`SISTEMI_PROVATI`): il comando che propone parte da `python3`, che su un Windows senza Python vero è lo stub dello Store.

Sesta prova, 13/11/2026 (Claude Code 2.1.317, Mac): una copia del plugin cambiata sullo sha già installato, in un `CLAUDE_CONFIG_DIR` di prova col catalogo vero. `claude plugin install arturo@arturo` risponde "already installed" e `claude plugin update` "already at the latest version": nessuno dei due riscrive la cartella. `claude plugin uninstall --keep-data` seguito da `claude plugin install` la riscrive: tornano il file cambiato e quello tolto, sparisce quello in più, i dati in `plugins/data/` restano, e un plugin spento torna acceso. `aggiornamenti.py plugin` usa questa strada quando la copia non è come il suo MANIFEST firmato, e rispegne il plugin se era spento (#5480, banco FD21).

Da provare: `arturo migra` su Windows da un terminale vero, su un'installazione di una persona; barra in basso dal puntatore su una macchina pulita.

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
chiusura   session-end.sh lancia aggiornamenti.py applica dalla copia accanto all'hook: la stessa strada di
           /aggiorna, con lo stesso lucchetto. Non rinvia: Claude Code tiene la copia di prima per le
           sessioni rimaste aperte. L'esito lo dice l'avvio dopo (10/11/2026)
avvio      deriva.py: la copia in uso ha il MANIFEST firmato? quali file non tornano? → riga DERIVA
telemetria versione dal plugin.json della copia, non dai tag del git dell'Orsa
```

- **L'avviso.** Al massimo una volta all'ora l'avvio e la barra in basso lanciano `aggiornamenti.py controlla`, dalla cartella del codice accanto a sé: col plugin scarica il catalogo e confronta la versione con quella installata, senza installare niente. Se è più nuova, la barra mostra "↑ Arturo <versione> · si installa alla chiusura" e l'avvio lo dice al modello; con gli aggiornamenti a mano mostra "serve /aggiorna" (#4860, banco `tests/test_avviso_plugin_2026_11_06.py`).
- **La chiusura.** Dal 10/11/2026 la chiusura della sessione installa il rilascio nuovo anche col plugin, con le verifiche di `/aggiorna`. Una firma che non torna o che il computer non sa controllare resta nello stato: l'avvio e la barra lo dicono finché un'installazione non riesce. Non si installa dopo un `/clear`, con gli aggiornamenti a mano, né da un checkout di sviluppo (banco `tests/test_chiusura_plugin_2026_11_10.py`). L'aggiornamento automatico di Claude Code per il catalogo `arturo` resta spento: installerebbe senza la verifica del tag.
- **L'ancora.** La chiave che verifica sta nell'Orsa, in `~/.claude/arturo/rilasci.allowed_signers`: chi cambia la copia del plugin cambierebbe anche la chiave dentro. La prima verifica riuscita la scrive; dopo cambia solo con una copia nuova verificata con la chiave di prima. Così una chiave nuova entra con un rilascio firmato dalla vecchia, come nel clone.
- **Lo spazio dei nomi.** Il MANIFEST si firma con `ssh-keygen -Y sign -n arturo-manifest`, da stdin: con un file, una `MANIFEST.sig` già presente resta com'era e `ssh-keygen` esce con 0 lo stesso. La chiave dei rilasci vale per `git` e `arturo-manifest` (`firme/rilasci.allowed_signers`).
- **Fuori dal MANIFEST** stanno solo la firma, la cartella `.in_use` che Claude Code aggiunge alla cache e i `__pycache__` che Python scrive accanto agli script.
- **Il catalogo** sta sul ramo `catalogo` del repository: la persona lo aggiunge con `claude plugin marketplace add stellakamikaze/arturo#catalogo`, e `main` resta il clone di chi l'ha installato così fino a F4.
- Il banco `tests/test_fiducia_2026_11_05.py` (FD01-FD09) prova tutto con la CLI vera, in un `CLAUDE_CONFIG_DIR` di prova: tag non firmato, firmato da un'altra chiave, sha dopo il tag, rilascio più vecchio, e un aggiornamento vX → vY che va a buon fine.

## La migrazione dal clone (F4, 5/11/2026)

Chi ha Arturo come clone in `~/.claude` passa al plugin con `arturo migra` (`bin/migra.py`). Prima si lancia la prova, che non tocca niente; poi la migrazione vera, con Claude Code chiuso, da un Terminale.

```
arturo migra --prova   rapporto: PRONTA o FERMA coi motivi, cosa cambia, cosa resta della persona
                       → ~/.claude/data/migra/rapporto-<data>.txt, da mandare con /segnala
arturo migra           1 controlli del rapporto, e nessuna sessione di Claude Code aperta
                       2 copia di sicurezza: ~/.claude-arturo-clone-<data>/copia (.git, file di Arturo,
                         settings.json, file dei plugin, ancora, file di blocco) + codice (bin e hooks
                         di chi migra, da cui si lancia indietro) + migra.json coi passi
                       3 personale.py separa --senza-commit: /inizio cambiato → personale/inizio.md
                       4 catalogo → ancora = chiave del clone → tag firmato e sha (verifica_catalogo)
                         → claude plugin install → la copia torna col MANIFEST firmato?
                       5 settings.json in una scrittura: via gli hook di Arturo, unione a tre vie col
                         frammento del plugin, file di blocco
                       6 i file di Arturo e .git escono da ~/.claude (la copia li tiene)
                       un passo che fallisce → indietro da solo (uscita 1, o 3 per il catalogo)
arturo migra indietro  toglie plugin e catalogo messi dalla migrazione, riporta ogni file dalla copia
```

- **La base dell'unione** è il `settings.json` di Arturo da cui il clone è partito (`git show <merge-base>:settings.json`), tradotto come il pacchetto traduce il suo (barra dal puntatore, stile `arturo:`). Una voce che la persona ha lasciato com'era prende il valore del plugin, una voce sua resta sua, una voce cambiata da tutte e due le parti ferma la migrazione e si nomina.
- **Gli hook che escono** sono quelli che lanciano un file di Arturo dentro `~/.claude`, anche se il plugin non li porta più: dopo il passo 6 quel file non c'è. Un hook della persona resta. Una barra in basso della persona che usa un file di Arturo ferma la migrazione.
- **Il rapporto** nomina i file di Arturo e conta quelli della persona, senza nomi e senza i valori dei settings: va a chi mantiene Arturo.
- **Una `~/.claude` con Arturo come `upstream`** (il repository della persona) si migra solo con `--unica-macchina`, dal 9/11/2026 (segnalazione n. 62). `.git` e `.gitignore` restano, e i file di Arturo escono con un commit nel repository della persona, che la `/fine` dopo pubblica. `migra indietro` lo annulla con un `git revert`, senza sostituire `.git`, che nel frattempo può avere commit suoi. Con più computer il commit arriverebbe agli altri alla prima sincronizzazione e lì toglierebbe Arturo e le guardie senza avviso. Per questo senza `--unica-macchina` la migrazione si ferma, e con più computer si fa a mano.
- **La sessione aperta** blocca la migrazione: una sessione partita col clone ha gli hook in `$ARTURO_CODICE/hooks`, e dopo il passo 6 ogni hook mancante bloccherebbe le sue azioni.
- Il demone fsmonitor di git tiene aperta `.git`: la migrazione lo spegne per i suoi git, e copia e confronto saltano i socket.
- **Il CLAUDE.md** resta della persona. Le regole consigliate che `/setup` ci aveva scritto col plugin arrivano anche col metodo all'avvio: il rapporto le conta, e dopo la migrazione `arturo personale regole-doppie` le elenca e con `--togli` le toglie, con la copia in `CLAUDE.md.prima-del-plugin` (#4874, banco `tests/test_regole_doppie_2026_11_06.py`). Si toglie solo una riga uguale per intero alla regola, e senza un seguito rientrato: una riga che le somiglia si elenca e resta.
- Il banco `tests/test_migra_2026_11_05.py` (MG01-MG18) prova tutto con la CLI vera, in un `CLAUDE_CONFIG_DIR` di prova: rapporto, sessione aperta, migrazione, ritorno identico file per file, tag non firmato, conflitto nei settings dopo l'installazione, `upstream` senza e con `--unica-macchina` (MG07, MG18).

## Come un testo di Arturo indica il codice

Due conseguenze della prova:
- **I comandi di Arturo diventano skill** (`skills/<nome>/SKILL.md` con `name:`). Così `/inizio` resta senza prefisso anche nel plugin.
- **Un percorso al codice si scrive `${CLAUDE_SKILL_DIR}/../../bin/...`**. Vale in tutti e due i layout: nel plugin porta alla cartella del plugin, nel clone in `~/.claude` porta a `~/.claude`. Claude Code lo risolve prima della lettura, quindi funziona anche con il tool Read, che non espande le variabili.
- Negli script e negli hook vale `ARTURO_CODICE`: l'hook di avvio lo calcola dalla sua cartella e lo scrive in `$CLAUDE_ENV_FILE` insieme al PATH di `bin/`.
- Negli script Python le due radici vengono da `hooks/radici.py`: `radice_arturo()` è la cartella del codice, calcolata dal file; `radice_orsa()` è `CLAUDE_CONFIG_DIR` o `~/.claude`. Un messaggio che dice alla persona quale comando lanciare usa `comando_arturo()`: col clone scrive `python3 $ARTURO_CODICE/bin/arturo`, col plugin il percorso vero. Da `bin/` si importa con `sys.path.append(<bin>/../hooks)`. Il banco ST08 vieta `Path.home() / ".claude"` e `$ARTURO_CODICE/hooks|bin` scritti a mano, salvo le guardie e le eccezioni che elenca col motivo.
- La memoria (`memoria_accesa()` in `hooks/melchior_match.py`) non guarda più `bin/arturo` accanto agli hook: decidono `ARTURO_MEMORIA` e `"accesa"` in `data/memoria/impostazioni.json`, altrimenti è spenta.

## La testata: dove Arturo si presenta

Il logo di Claude Code non si sostituisce: nessuna opzione dei settings lo cambia e nessun componente dei mod lo ridisegna (verificato su 2.1.317, 3/11/2026). La parte `skills/arturo/hooks/testata` del mod di Arturo piazza con `$.ui.place` il primo blocco sotto l'intestazione: versione di Arturo (`git describe` dal repository che contiene il mod, chiesto a `git rev-parse --show-toplevel` così vale anche da un link in `~/.claude/skills`, altrimenti la radice da `$.plugin.root`, `radiceCodice` di `hooks/parti.ts`; senza git, col plugin, il campo `version` di `.claude-plugin/plugin.json`), versione di Claude Code (`$.session.version()`), deriva (`cache/deriva.json`, scritto da `hooks/deriva.py`) e aggiornamento (`session-env/aggiornamento.json`). I dati stanno nell'Orsa, il codice in Arturo.
