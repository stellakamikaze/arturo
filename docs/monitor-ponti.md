# I ponti di /monitor

/monitor legge i materiali della persona: posta, calendario, trascrizioni delle call, task,
handoff delle sessioni, memoria. Ogni fonte arriva da un **ponte**. Questa pagina dice quali ponti
ha Arturo, come aggiungerne uno tuo e cosa un ponte non deve mai fare.

Stato: primo avvio (3/11/2026). Esistono la scoperta dei ponti (`bin/monitor/ponti.py`), la scelta
delle fonti al primo avvio della skill `monitor` (`bin/monitor/fonti.py`), lo schema delle righe
(`bin/monitor/schema.md`, validato da `righe.py`), il fingerprint e i cursori per fonte. Il giro
quotidiano, che legge le fonti scelte e scrive il report, arriva con la fase successiva.

## Cosa vede /monitor oggi

```bash
python3 ~/.claude/bin/monitor/ponti.py
```

Stampa i ponti in quattro gruppi: pronti, da controllare in questa sessione, da collegare, rotti.
Per ognuno dice cosa ti porta e, se manca, il passo per collegarlo.

| Ponte | Cosa ti porta | Come si collega |
|---|---|---|
| Google (connettori di claude.ai) | email a cui rispondere, promesse fatte, riunioni, trascrizioni su Drive | dalle impostazioni di claude.ai; /monitor li cerca fra i suoi tool |
| Google (`gws`) | lo stesso, con più account e dal terminale | `/inizio gws` |
| Task | task nuovi senza doppioni, task fermi da controllare | `arturo todo` di serie, oppure `arturo/fonte-task.local` (`docs/fonte-task.md`) |
| Sessioni | il prossimo passo di ogni lavoro aperto con Claude | si accende alla prima `/fine` |
| Memoria | schede dei progetti, note su persone e decisioni, scritte col tuo sì | `arturo memoria accendi` |

## Un ponte tuo

I ponti personali stanno in `~/.claude/personale/monitor/`, fuori dal repository: gli aggiornamenti
non li toccano. Si dichiarano in `ponti.json`:

```json
{"ponti": [
  {"nome": "chat", "descrizione": "le chat di lavoro",
   "comando": ["python3", "~/.claude/personale/monitor/chat.py"],
   "prova": ["python3", "~/.claude/personale/monitor/chat.py", "--prova"]}
]}
```

- `comando` e `prova` sono liste: niente shell. `~` vale la tua cartella home.
- `prova` è facoltativa: esce con 0 se il ponte risponde. Non deve stampare segreti.
- Il programma consegna righe JSON nello schema di /monitor (`bin/monitor/schema.md`): una riga
  per cosa da fare, più una riga di copertura che dice quanto ha letto. Un ponte che non risponde dà "non letta" e le altre
  fonti vanno avanti.

## Cosa un ponte non fa mai

- **Non scrive e non invia.** Un ponte legge. Task, bozze e note le scrive /monitor, dopo la
  verifica e, dove serve, col tuo sì. La fase che legge testo di altri non ha canali verso fuori:
  se un'email contiene istruzioni, non trova niente con cui eseguirle.
- **Non tiene segreti nei suoi file.** Le credenziali restano dove le tiene il servizio: il
  connettore di claude.ai, il portachiavi del sistema, la CLI che le gestisce.
- **Non passa testo nascosto.** Un ponte che legge email HTML consegna il testo che vedi tu: toglie
  il testo nascosto (display:none, carattere a zero, bianco su bianco) e scrive in una riga quanto ne
  ha tolto. È la via dell'attacco del luglio 2025 ai riassunti di Gmail. I connettori di claude.ai
  estraggono il testo a modo loro: lì vale il resto di queste regole.
