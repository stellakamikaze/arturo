---
description: Diagnosi di un progetto intero - prima Arturo, poi git, handoff e todo, i file citati che non esistono più, i materiali sparsi da mettere a posto, e il bug nel codice se c'è
argument-hint: "[progetto] [descrizione del problema] (opzionale)"
---

# Diagnosi

**Cosa dice la persona**: $ARGUMENTS

`/diagnosi` guarda un progetto intero, non solo il codice. Va insieme a `/setup`: `/setup`
configura Arturo, `/diagnosi` controlla che Arturo regga e che il progetto sia in ordine. La
persona potrebbe non essere tecnica: parla semplice e spiega ogni parola tecnica in mezza riga.

Il progetto è il primo argomento, se è il nome di un progetto. Altrimenti è la cartella
corrente. Il resto dell'argomento descrive il problema, se la persona ne ha uno.

**Legge e propone, non ripara da sola.** Le parti 1-4 sono in sola lettura. Ogni correzione
parte solo dopo il sì della persona, e nessun file si cancella: si sposta, o resta.

---

## Parte 1 — Arturo regge?

```bash
python3 "$HOME/.claude/hooks/controlla-config.py" "$HOME/.claude"; echo "config rc=$?"
python3 "$HOME/.claude/hooks/deriva.py" "$HOME/.claude"
cat "$HOME/.claude/cache/banchi-ultimo-esito.txt" 2>/dev/null | head -3 || echo "banchi: nessun esito salvato"
bash "$HOME/.claude/skills/system-audit/audit.sh" 2>&1 | tail -25
```

- `CONFIG ROTTA` o un FAIL dell'audit: le guardie possono essere spente. È la prima cosa da
  dire, e la cura è `/setup`, che rifà la fase giusta.
- Una riga `DERIVA:`: la persona ha cambiato file o hook di Arturo. Non è un errore. Diglielo,
  e ricorda che `/aggiorna personale` mette da parte le sue modifiche ai comandi.
- Le aggiunte della persona ai comandi: `python3 ~/.claude/bin/arturo personale elenco`. Una riga
  `Senza comando` nomina i file di `personale/` di un comando uscito da Arturo: nessuno li legge
  più. Mostrali alla persona: decide lei se tenerli altrove o cancellarli.
- Se il problema sembra dell'installazione di Claude Code (accesso, account, versione), lancia
  `claude doctor` e riporta cosa dice.

**I todo.** L'archivio deve essere leggibile:

```bash
python3 ~/.claude/bin/arturo todo --json | PYTHONIOENCODING=utf-8 python3 -c 'import json,sys; v=json.load(sys.stdin); print("archivio leggibile, avvisi:", len(v["avvisi"])); [print("avviso:", a) for a in v["avvisi"]]'
```

Riporta ogni avviso con le sue parole: una riga illeggibile, un evento per un todo che non
esiste, un numero cambiato dopo un merge. Non correggere il file a mano: ogni riga resta, e il
resto dell'archivio funziona. Se il comando esce con un errore, riporta l'errore esatto.

**Il pannello `/dafare`.** Controlla che il mod sia caricato e che Claude Code sia abbastanza
nuovo:

```bash
claude plugin list --json | python3 -c 'import json,sys; v=[p for p in json.load(sys.stdin) if p.get("id") == "dafare@skills-dir"]; print("mod caricato: dafare@skills-dir" if v and v[0].get("enabled") else "mod spento: dafare@skills-dir" if v else "mod NON caricato: dafare@skills-dir manca")'
echo "versione di Claude Code: $(claude --version) (il pannello chiede la 2.1.287 o successiva)"
```

Se il mod manca, guarda se esiste `~/.claude/skills/dafare/.claude-plugin/plugin.json` e se il
plugin è spento (`claude plugin enable dafare@skills-dir` lo riaccende). In un'organizzazione
le managed settings decidono se Claude Code carica i mod da `~/.claude/skills`:

- con un elenco chiuso di marketplace (`strictKnownMarketplaces`) i mod non si caricano, finché
  l'elenco non contiene `{"source": "skills-dir"}`;
- `{"source": "skills-dir"}` dentro `blockedMarketplaces` li spegne tutti.

Spenti i mod, la persona perde il pannello **e la redazione dei segreti**
(`redazione-segreti@skills-dir`): Claude torna a leggere in chiaro un token stampato da un
comando. Se va spento qualcosa, si spegne il solo pannello con
`claude plugin disable dafare@skills-dir`.

---

## Parte 2 — Lo stato del progetto

```bash
python3 "$HOME/.claude/bin/arturo" contesto "<progetto>"; echo "rc=$?"
```

Con `rc=2` il progetto non c'è: proponi i nomi simili che stampa e fermati. Dal contesto
guarda git (modifiche non salvate, conflitti, commit dopo l'ultimo handoff), l'ultimo handoff,
i todo aperti, le scadenze passate e gli AVVISI.

Poi due controlli sugli handoff, in sola lettura:

```bash
H=$(ls -t "$HOME/.claude/data/handoffs/<slug>"/HANDOFF_*.md 2>/dev/null | head -1)
[ -n "$H" ] && { bash "$HOME/.claude/bin/handoff-gate.sh" "$H"; echo "gate rc=$?"; } || echo "nessun handoff"
python3 "$HOME/.claude/bin/index-rigenera.py" --dry-run --diff; echo "indice rc=$?"
```

Un gate rosso vuol dire un handoff con la tabella dei todo rotta. Un `LINK MORTO` vuol dire
un indice che punta a un handoff sparito. Si sistemano entrambi col prossimo `/fine`.

---

## Parte 3 — I file citati esistono ancora?

Gli handoff (sezione «File e materiali») e il `CLAUDE.md` del progetto (sezione «Materiali»)
dicono dove stanno i file del lavoro. Controlla che ci siano ancora:

```bash
python3 "$HOME/.claude/bin/arturo" diagnosi percorsi "<progetto>"; echo "rc=$?"
```

Ogni riga `MANCA:` è un file che un handoff o il `CLAUDE.md` danno per esistente, e non c'è
più. Per ognuno chiedi alla persona se l'ha spostato, rinominato o cancellato. Se l'ha
spostato, cerca il file col suo nome e proponi di correggere la riga del `CLAUDE.md`. Un
handoff vecchio non si riscrive: la correzione va nel prossimo.

---

## Parte 4 — Consolida i materiali

I file di un progetto finiscono sparsi: in Download, sulla Scrivania, fuori dal repo. Trovali:

```bash
python3 "$HOME/.claude/bin/arturo" diagnosi materiali "<progetto>"; echo "rc=$?"
```

Per ogni file lo script propone un destino, con le stesse regole di `/fine`:

- **repo**: entra nel repository del progetto e nel prossimo commit;
- **archivia**: un documento di lavoro che sta fuori da ogni repo. Chiedi alla persona dove
  tiene i documenti, e sposta solo dopo il sì;
- **resta**: un file pesante, sopra i 20 MB, o un oggetto online. Non si sposta, ma il suo
  percorso va scritto nella sezione «Materiali» del `CLAUDE.md`, così la Parte 3 lo ritrova;
- **scarto**: un file temporaneo. Lo nomini e basta: non si cancella.

Mostra la tabella, poi chiedi: **tutto come proposto**, i numeri da cambiare, oppure **niente**.
Sposta con `mv` solo dopo il sì, e aggiorna la sezione «Materiali» del `CLAUDE.md` per ogni
file che non entra nel repo.

---

## Parte 5 — Se c'è un bug nel codice

Solo se la persona descrive un errore, o se le parti 1-4 ne hanno trovato uno.

**Prima i fatti.** Non partire dalla prima ipotesi. Chiedi, se non è già chiaro:

1. **L'errore esatto**: il messaggio così com'è, non riassunto.
2. **Cosa si aspettava** e cosa succede invece.
3. **Cosa ha già escluso**: se dice «NON è X», rispettalo e cerca altrove.
4. **Come si riproduce**: passi, input, condizioni.

**Poi un'ipotesi che si possa smentire.** Esponila in 2-3 righe: la causa sospetta e la prova.
Formulala così: *se la causa fosse X, allora dovrebbe succedere Y*. La prova deve rispondere
sì o no. Un controllo che non può smentirti è un tentativo di correzione travestito, ed è da lì
che nascono i giri a vuoto. Guarda i quattro casi del dato coinvolto: quello normale, quello
vuoto, quello mancante e quello d'errore. Il bug vive quasi sempre in uno dei tre meno battuti.

Aspetta il sì prima di toccare il codice. Poi lascia lavorare il debugging di Claude Code:
ispezione, prova dell'ipotesi, `git bisect` se è una regressione, una correzione minima con un
test che riproduce il bug.

- **Al massimo tre tentativi** sullo stesso errore. Se tre approcci diversi falliscono, fermati:
  serve un'altra strategia, non un quarto tentativo. Chiedi alla persona.
- **Correzione minima**: solo quella, niente miglioramenti a lato.
- **Commit selettivo**: `git add` dei soli file toccati, messaggio `fix:` con la causa in una riga.
- Per un errore che può tornare, proponi una riga in `## Errori Comuni` del `CLAUDE.md` del
  progetto («NON fare X — causa Y»).

---

## Il referto

Chiudi con una riga per parte, in quest'ordine, ognuna con verde, giallo o rosso e il motivo
in poche parole:

```
Arturo        verde   config integra, audit senza FAIL, todo leggibili
Progetto      giallo  3 file non salvati, ultimo handoff di 12 giorni fa
File citati   rosso   2 mancano (vedi sotto)
Materiali     giallo  5 file da mettere a posto
Codice        —       nessun bug descritto
```

Poi le proposte numerate, prima quelle rosse. Chiudi con le parole di risposta in grassetto:
**tutto**, i numeri, oppure **niente**.
