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
aggiornamento: cambia solo Arturo. L'Orsa resta com'è.
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
| Agent | gli 8 agent si caricano |

Da provare: Windows (prima di migrare Balthasar); installazione da marketplace GitHub con sha fissato; barra in basso dal puntatore su una macchina pulita.

## Il pacchetto

`python3 bin/impacchetta.py --uscita DIR` genera il plugin dal repository, che resta installabile come clone. Il banco `tests/test_impacchetta_2026_11_03.py` controlla il contratto:
- `.claude-plugin/plugin.json` e `marketplace.json`, con Arturo e i suoi mod;
- `hooks/hooks.json` dagli hook di `settings.json`, con `"${CLAUDE_PLUGIN_ROOT}/..."` tra virgolette;
- `impostazioni/arturo.json`: il resto di `settings.json`, che `arturo impostazioni applica` unisce ai settings della persona;
- ogni `commands/<nome>.md` diventa `skills/<nome>/SKILL.md` con `name:` e `disable-model-invocation: true`.

`arturo impostazioni applica` fa un'unione a tre vie: la base è il file di blocco, poi i settings della persona, poi il frammento nuovo. Arturo cambia solo le voci che la persona ha lasciato com'erano. Se una voce è cambiata da tutte e due le parti, il comando non scrive niente e la nomina.

Col codice fuori da `~/.claude`, l'avvio scrive `~/.claude/arturo/radice` per la barra in basso e dice al modello dove sta il codice.

## Come un testo di Arturo indica il codice

Due conseguenze della prova:
- **I comandi di Arturo diventano skill** (`skills/<nome>/SKILL.md` con `name:`). Così `/inizio` resta senza prefisso anche nel plugin.
- **Un percorso al codice si scrive `${CLAUDE_SKILL_DIR}/../../bin/...`**. Vale in tutti e due i layout: nel plugin porta alla cartella del plugin, nel clone in `~/.claude` porta a `~/.claude`. Claude Code lo risolve prima della lettura, quindi funziona anche con il tool Read, che non espande le variabili.
- Negli script e negli hook vale `ARTURO_CODICE`: l'hook di avvio lo calcola dalla sua cartella e lo scrive in `$CLAUDE_ENV_FILE` insieme al PATH di `bin/`.
