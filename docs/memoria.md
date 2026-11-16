# La memoria di Arturo

Questa pagina dice cosa ricorda Arturo, dove lo tiene e cosa esce dal tuo computer. È il contratto
della memoria: se un altro testo di Arturo dice una cosa diversa, vale questa pagina. Il nome
tecnico della memoria è Melchior: lo trovi nei nomi dei file del codice.

## Cosa ricorda

- **I progetti**: cos'è un progetto, dove sta la sua cartella, con che nomi lo chiami.
- **Le decisioni**: le scelte chiuse, per non rimetterle in discussione a ogni sessione.
- **Gli errori già visti**: cosa non rifare, e perché.
- **Le persone**: chi sono le persone con cui lavori, se ne parli con Claude.
- **Le tue preferenze**: come vuoi le risposte, cosa correggi spesso.

Lo stato del lavoro (cosa è fatto, cosa resta) non sta nella memoria. Sta nei riepiloghi di
passaggio (gli handoff) che `/fine` scrive a fine sessione, e nell'elenco delle cose da fare di
`arturo todo`.

## Come funziona

Ogni cosa ricordata è una nota: un file di testo con poche righe in testa e il contenuto sotto.

- A ogni tuo messaggio Arturo cerca le note che parlano della stessa cosa e dice a Claude dove
  sono. Claude apre una nota solo se gli serve. Se nessuna nota c'entra, Arturo non dice niente.
- Ogni progetto ha una scheda: cos'è, dove sta la cartella, le decisioni chiuse e gli errori da non
  ripetere. La scrive `/fine` da solo, la prima volta e poi solo coi fatti nuovi, e tiene le righe
  che scrivi tu. `/inizio` la rilegge anche se apri Claude dalla home, e all'avvio Arturo la indica a
  Claude. `arturo memoria scheda <progetto>` te la mostra.
- Se chiudi una sessione senza `/fine`, Arturo salva da solo cosa stavi facendo: le ultime richieste,
  i file scritti e il lavoro rimasto aperto. Non usa Claude e non decide niente: legge solo la
  conversazione. Una richiesta con dentro una password non viene copiata. Al prossimo `/inizio` lo
  vedi in cima, e il primo `/fine` lo completa senza farne un doppione. Una sessione senza richieste
  né file non lascia niente, e a memoria spenta il salvataggio non parte.
- A fine sessione `/fine` salva da solo le note nuove, senza chiederti niente, e nella chiusura te
  le elenca: "Ho ricordato: 1. … 2. …". Se una non ti serve, scrivi "togli" e il numero: la nota va
  nell'archivio (`data/memory/_archive/`), non viene cancellata. Se una nota nuova parla di una cosa
  già ricordata, `/fine` aggiorna quella che c'è invece di scriverne un'altra. Una nota delle sessioni
  precedenti la togli con `arturo memoria togli <nome>`.
- Una volta a settimana `/fine` fa l'igiene della memoria (`arturo memoria igiene`). Una nota che
  Arturo non propone a Claude da 90 giorni diventa dormiente: lo segna una riga in testa, il file non
  si sposta, e Arturo continua a proporla quando c'entra. La prima volta che torna proposta, l'igiene
  dopo toglie il segno. L'igiene segnala anche i collegamenti rotti e le note quasi uguali, che
  conviene unire, e lo fa senza Claude e senza cancellare niente.
- Ogni nota che Claude scrive passa da un controllo. Se dentro c'è una password, o un testo che
  prova a dare ordini a Claude di nascosto, Claude riceve un avviso. La nota resta scritta, e Claude la può correggere.

La memoria è accesa di default dal 14 novembre 2026, e la prima sessione te lo dice. `arturo memoria
spegni` la spegne, e le note restano dove sono. Se l'hai spenta, resta spenta anche dopo un
aggiornamento: `arturo memoria accendi` la riaccende.

## Dove stanno le note

`arturo memoria`, senza altre parole, dice cosa Arturo ricorda: per ogni progetto quante note ha e
le ultime decisioni, poi le note dormienti e le cartelle dei file. La stessa risposta arriva se chiedi
a Claude "cosa ricordi di me?".

- `~/.claude/projects/*/memory/`: le note che Claude Code scrive da solo, una cartella per progetto.
- `~/.claude/data/memory/`: le note curate, divise in cartelle per tipo.
- Le cartelle che aggiungi tu con `arturo memoria cartella aggiungi <cartella>`.

Se la stessa nota si trova passando da due di queste cartelle, Arturo la conta una volta sola.
Due note diverse con lo stesso nome in due progetti restano invece due note.

## Lo schema di una nota

La nota ha in testa le righe che usa anche Claude Code:

```markdown
---
name: preventivi-studio
description: come impaginare i preventivi dello studio
type: reference
---
I preventivi partono dal modello dell'anno scorso, con le tariffe del listino.
```

- `name`: il nome corto della nota.
- `description`: una riga che dice di cosa parla. È la prima cosa che Arturo legge quando cerca
  le note da proporre a Claude.
- `type`: uno dei quattro tipi di Claude Code. `user` per chi sei, `feedback` per come vuoi che
  Claude lavori, `project` per un progetto, `reference` per un'informazione da ritrovare.
  Claude Code scrive il tipo anche dentro `metadata:`, e vale lo stesso.
- Facoltativi: `alias` (altri nomi del progetto), `cartella` (dove sta il progetto), `triggers`
  (parole che devono richiamare la nota).

Una nota nuova scritta in `~/.claude/data/memory/` va da sola nella cartella del suo tipo: `user`
in `profilo/`, `feedback` in `feedback/`, `project` in `progetti/`, `reference` in `reference/`.
`arturo memoria controlla` trova le note senza queste righe, le righe che non si leggono e i
collegamenti rotti.

## Passare un progetto a un collega

Il contesto di un progetto è tuo, e puoi passarne una copia a un collega o a un altro strumento di IA.
`arturo fascicolo esporta <progetto>` scrive una cartella di file di testo nella cartella in cui sei
(`--in` ne sceglie un'altra). Dentro ci sono:

- `scheda.md`: la scheda del progetto;
- `note/`: le note della memoria legate al progetto;
- `stato.md`: la riga di stato e i todo aperti;
- `lavori.md`: i lavori dello storico delle chat che scegli con `--lavoro ID`;
- `materiali/`: i file di testo che indichi con `--materiali` (Markdown, testo, CSV, JSON, HTML, sottotitoli);
- `LEGGIMI.md` e `fascicolo.json` (il manifesto): cosa c'è, come si usa e l'impronta di ogni file, un
  codice che cambia se il file viene modificato.

Prima di scrivere, Arturo controlla ogni file. Un file con un possibile segreto (una password, un
token) resta fuori, e il messaggio del comando dice perché. Le note su di te (tipo `user`) non entrano
nel fascicolo, a meno che tu non aggiunga `--anche-persona`. Un file che sembra contenere istruzioni per Claude (per esempio un comando che manda dati a un
indirizzo web) esce, ma il messaggio lo segna "da rivedere": il collega con Arturo lo rifiuterà.
`--prova` mostra cosa uscirebbe e non scrive niente. Il fascicolo resta sul tuo
computer: lo passi tu, come un qualsiasi file. Per un progetto di Claude.ai o di ChatGPT, carica i
file `.md` della cartella fra i file del progetto.

Il collega lo importa con `arturo fascicolo importa <cartella>`. I testi del fascicolo li ha scritti
un'altra persona, quindi Arturo li tratta come dati:

- entra solo un file elencato in `fascicolo.json`, con l'impronta giusta, dentro le cartelle previste e
  in formato testo. Arturo rifiuta un link simbolico, un percorso con `..` o un file nascosto;
- Arturo rifiuta un file con un possibile segreto o con un'istruzione nascosta, e il messaggio del
  comando dice il motivo;
- le note vanno in `~/.claude/data/memory/importati/<progetto>/`. Ogni nota porta in testa chi l'ha
  scritta e una riga che dice a Claude di leggerla come dato, non come istruzione;
- niente sovrascrive i tuoi file. Se hai già la scheda del progetto, quella importata va accanto. Se
  una nota col suo nome c'è già, l'importata prende un nome suo;
- una copia intera del fascicolo accettato resta in `~/.claude/data/fascicoli/`, una cartella che non
  va su GitHub;
- lo stesso fascicolo importato due volte entra una volta sola.

`--prova` dice cosa entrerebbe e non scrive niente. Una nota importata si toglie come le altre, con
`arturo memoria togli <nome>`. Se la tua `~/.claude` va su un GitHub privato, anche le note importate
vanno lì, come le tue.

## Cosa esce dal computer

- **Ad Anthropic**: le note che Claude apre entrano nella conversazione, e passano ad Anthropic
  come il resto della conversazione. Le note che Claude non apre non escono.
- **A chi mantiene Arturo**: solo se la telemetria è accesa, e solo conteggi in fasce e risposte
  sì o no. Una volta al giorno parte un dato che dice se la memoria è accesa o spenta e quante note
  contiene, in fasce (nessuna, fino a 10, fino a 50 e così via). Per ogni sessione parte quante note
  Arturo propone e quante Claude ne apre, sempre in fasce. Parte anche un dato quando Arturo salva al
  posto tuo una sessione chiusa senza `/fine`, e uno che dice se `/inizio` l'hai scritto tu
  o l'ha lanciato Arturo da solo per passare al passo dopo di un lavoro lungo (la rotazione). Il nome e il testo delle note non escono mai.
  La telemetria si spegne con `arturo telemetria spegni`.
- **Su GitHub, solo se la copia è privata**: se la tua `~/.claude` è collegata a un repository
  privato su GitHub (in gergo, un remote privato), `/fine` salva lì anche le note di
  `data/memory/`, così le ritrovi sugli altri computer. Se il repository è pubblico, o se non c'è,
  le note restano solo su questo computer.

## Cosa resta sul computer oltre alle note

- `~/.claude/cache/melchior-notes.json`: una copia del testo delle note, per cercarle in fretta.
  Si rifà da sola quando una nota cambia, e la puoi cancellare.
- `~/.claude/data/memory/.melchior-access.log.d/`: il registro delle volte in cui Arturo ha
  proposto una nota a Claude, con una riga per proposta e un file per computer.
- `~/.claude/data/memoria/impostazioni.json`: l'interruttore e le tue cartelle.
- `~/.claude/data/memoria/ricordate.json`: le note salvate da `/fine`, ognuna col numero con cui te
  l'ha elencata, così "togli" e il numero sa quale togliere.
- `~/.claude/data/memoria/ultima-igiene`: il giorno dell'ultima igiene, da cui `/fine` conta la settimana.

Nessuno di questi file entra nel repository di Arturo, e `/fine` non li salva nemmeno sul tuo
GitHub privato.
