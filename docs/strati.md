# Gli strati di Arturo, su due assi

Questo documento è il contratto degli strati. Ogni file nuovo di Arturo sta in un punto di tutti e due gli assi: di chi è, e cosa fa per la persona. Se un file non trova posto, il dubbio va nella voce della roadmap prima del codice. Il disegno è uno solo e sta in [`come-e-fatto.md`](come-e-fatto.md).

## Primo asse: di chi è

- **Orsa**: lo strato della persona, in `~/.claude`. Contiene istruzioni, preferenze, memoria, todo, handoff e skill proprie. Cresce sessione dopo sessione. Arturo non la scrive mai, salvo le voci dei settings registrate nel file di blocco. Il nome viene da Arturo, "il guardiano dell'orsa".
- **Arturo**: lo strato condiviso, uguale per tutti. Contiene guardie, metodo, skill e comandi, `bin/`, il motore della memoria Melchior e il mod. Lo aggiorna chi mantiene Arturo, con rilasci firmati.
- **Claude Code e il modello**: di Anthropic. Arturo non li cambia.

Un aggiornamento cambia solo Arturo. In un conflitto l'Orsa riceve la versione della persona, in `personale/conflitti/<data>/`. Il **file di blocco** (`~/.claude/data/arturo-impostazioni.lock`) elenca le voci dei settings che Arturo ha scritto: solo quelle Arturo può cambiare.

| Cosa | Arturo | Orsa |
|---|---|---|
| Codice | hook, `bin/`, motore Melchior, skill e comandi generici | skill, comandi e hook propri |
| Settings | frammento versionato, applicato con il file di blocco | tutto il resto di `settings.json` |
| Istruzioni | metodo e freni, iniettati all'avvio | `CLAUDE.md`, `personale/<skill>.md` |
| Dati | cache e coda della telemetria in `${CLAUDE_PLUGIN_DATA}` | memoria, todo, handoff, impostazioni di Melchior |
| Preferenze delle guardie | valori di base | `~/.claude/arturo/*.local` |
| Identità di Git e venv di `scrape` | `bin/identita-git.sh`, `tools/scrapling/setup.sh` | `~/.claude/arturo/git-identita`, `~/.claude/data/scrapling/.venv` |

**Regola d'oro: nessun file esiste in tutti e due gli strati.** Un file copiato in due posti diverge, e l'aggiornamento deve poi scegliere quale tenere.

## Secondo asse: cosa fa per te

Gli strati vanno nell'ordine in cui cresce il valore, e ognuno poggia su quelli prima.

| Strato | Cosa fa per la persona | Dove sta |
|---|---|---|
| 1 Protezione | chiede un sì prima di un gesto che non si annulla, ferma segreti ed esfiltrazione | guardie in `hooks/`, permessi di `settings.json`, parte `redazione-segreti` del mod, [`fiducia.md`](fiducia.md) |
| 2 Metodo | dice come si lavora: brief prima del lavoro, freni, fatto vuol dire verificato | `shared/metodo.md`, `prompt-master`, stile Conciso, `italiano-semplificato`, `humanizer`, subagent |
| 3 Memoria | fa ripartire ogni sessione dallo stato vero | `/inizio`, `/fine`, handoff, `arturo todo`, `/dafare`, Melchior, rotazione |
| 4 Collegamenti | porta dentro posta, agenda, documenti e pagine web | `/inizio gws`, `monitor` e i suoi ponti, [`fonte-task.md`](fonte-task.md), `scrape`, i progetti consigliati |
| 5 Scoperta | propone le automazioni con le prove, e le costruisce solo dopo il sì | progetto scritto, codice in fila (voce `scoperta` di `ROADMAP.md`); oggi `/guidami` e `/creaskill` |
| 6 Orsa | rende la configurazione della persona | `CLAUDE.md`, `personale/`, skill proprie, la voce in `personale/humanizer.md` |

I primi due sono le fondamenta, il 3 e il 4 il lavoro di ogni giorno, il 5 e il 6 la crescita. Due parti attraversano tutti gli strati:
- **Ingresso**: installazione, `/setup`, `/aggiorna`, [`migrazione.md`](migrazione.md);
- **Misura**: banchi in `tests/`, `/diagnosi`, `system-audit`, telemetria, `/segnala`.

**Il ciclo dell'Orsa.** Il lavoro lascia versioni dei file e memoria (3). La Scoperta ne ricava una proposta (5). Il sì della persona la fa entrare nell'Orsa (6), e ogni automazione creata si annulla. Il lavoro dopo parte da un'Orsa più sua. Protezione e Metodo valgono a ogni giro.

## Estendere una skill senza copiarla

Se una persona vuole cambiare una skill di Arturo, scrive `~/.claude/personale/<skill>.md`. Un hook lo aggiunge al contesto ogni volta che la skill parte, anche quando la chiama il modello. L'estensione aggiunge e precisa, ma freni e guardie di Arturo vincono sempre.

Se una persona vuole sostituire una skill, scrive una skill con lo stesso nome nell'Orsa. Il nome senza prefisso va alla sua, quella di Arturo resta raggiungibile come `arturo:<nome>`. La sostituzione si dichiara in `personale/sostituzioni.txt`: un nome per riga (skill, comando o `name:` di uno stile), col motivo dopo `#`. `arturo personale omonimi` e `system-audit` nominano ogni omonimo non dichiarato e ogni riga che non ha più un omonimo (banco `tests/test_sostituzioni_2026_11_05.py`, SO01-SO05). Senza dichiarazione, una skill nuova di Arturo con un nome che la persona usa già non si vedrebbe mai.

## Perché un plugin

Un plugin di Claude Code vive in `~/.claude/plugins/`, fuori dai file della persona. L'aggiornamento sostituisce la sua cartella e non tocca l'Orsa: la separazione la garantisce Claude Code. Un plugin però non porta permessi, `autoMode`, `env`, `statusLine`, lo stile di base e il `CLAUDE.md`. Queste voci le scrive `/setup` nei settings della persona, con il file di blocco; il metodo arriva con l'hook di avvio. Pacchetto e prove: [`prove-plugin.md`](prove-plugin.md).

## Dove sta il codice

- I comandi di Arturo diventano skill (`skills/<nome>/SKILL.md` con `name:`), così `/inizio` resta senza prefisso anche nel plugin.
- Un testo di Arturo indica il codice con `${CLAUDE_SKILL_DIR}/../../bin/...`. Vale nel plugin e nel clone, e Claude Code lo risolve prima della lettura, anche per il tool Read.
- Negli script e negli hook vale `ARTURO_CODICE`: l'hook di avvio lo calcola dalla sua cartella e lo scrive in `$CLAUDE_ENV_FILE` insieme al PATH di `bin/`.
- Negli script Python le due radici vengono da `hooks/radici.py`: `radice_arturo()` è la cartella del codice, `radice_orsa()` è `CLAUDE_CONFIG_DIR` o `~/.claude`. Un messaggio con un comando per la persona usa `comando_arturo()`. Da `bin/` si importa con `sys.path.append(<bin>/../hooks)`. Il banco ST08 vieta `Path.home() / ".claude"` e `$HOME/.claude/hooks|bin` scritti a mano, salvo le eccezioni che elenca col motivo.
- La memoria (`memoria_accesa()` in `hooks/melchior_match.py`) la decidono `ARTURO_MEMORIA` e `"accesa"` in `data/memoria/impostazioni.json`, altrimenti è spenta. Cosa ricorda, lo schema delle note e cosa esce dal computer: [`memoria.md`](memoria.md).

## Gli altri documenti

- [`prove-plugin.md`](prove-plugin.md): come si genera il plugin, le sei prove sul plugin vero e la testata.
- [`fiducia.md`](fiducia.md): la catena di fiducia, dal rilascio firmato all'avvio.
- [`migrazione.md`](migrazione.md): `arturo migra`, dal clone al plugin e indietro.
- [`memoria.md`](memoria.md): il contratto della memoria, cosa ricorda e cosa esce dal computer.
