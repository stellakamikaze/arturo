# /fine: il modello dell'handoff

`/fine` legge questo file nella FASE 4, prima di scrivere l'handoff. Il gate della FASE 5
(`bin/handoff-gate.sh`) controlla la tabella `## Task Pendenti` e i segnaposto mai compilati.

## Il modello

```markdown
# Session Handoff - AAAA-MM-GG HH:MM
## Progetto
- Nome: <slug> / Branch: <branch> / Status: in progress|completato|bloccato
- Filone: <solo se il progetto ha più filoni di lavoro: un nome breve, sempre lo stesso>
- Sessione: <valore di $CLAUDE_CODE_SESSION_ID>
- Ultimo commit: <hash - messaggio>
## Ripartenza
<Per la persona fra una settimana, tre o quattro frasi senza gergo, hash e nomi di file: cosa esiste
adesso, cosa è cambiato per lei, dove vi siete fermati e perché.>
Prossimo passo: <una azione col gesto che serve: "mi dici quale account uso">
## Decisioni
1. <decisione e motivo>
## Vicoli ciechi
- NON fare X: causa Y, con l'errore esatto se c'è
## File e materiali
- <file o oggetto> → <posizione finale: percorso nel progetto, link, percorso dove resta, scarto>
## Task Pendenti
Da `arturo todo --progetto .`: tutti i todo aperti del progetto.

| ID | Progetto | Priorità | Task | Status | Descrizione | Chi |
|----|----------|----------|------|--------|-------------|-----|
| #4 | libro | alta | Rileggere il capitolo tre | da fare | Mancano le note dell'editor: senza, la revisione resta a metà | Claude |
| #5 | libro | media | Mandare la bozza all'editor | da fare | La bozza è pronta nella cartella del progetto | Tu: invio a terzi |

## In sospeso
- <decisione rimandata o dubbio>
## Idee
- <idea> → #ID | → memoria [[nome-della-nota]] | → scartata: <motivo>
```

La riga "- Sessione:" serve: `/fine` rilanciato ritrova da lì il suo handoff, e la coda della FASE 9
lo trova senza `--handoff`.

## Le regole della tabella `## Task Pendenti`

- **La sezione c'è sempre**, con questo titolo esatto. Senza task contiene la frase "Nessun task pendente".
- **La colonna ID ha il numero del todo** nell'archivio (`#4`): prima crei il todo, poi scrivi la riga.
  Un todo chiuso non sta nella tabella. Entrano anche i todo aperti delle sessioni prima: la tabella è
  la fotografia, la fonte di verità è l'archivio.
- **Chi** è l'ultima colonna. Vale `Claude` per ogni passo che Claude esegue da solo, `Decidi tu` se
  serve una scelta della persona prima che Claude lavori, `Tu: <cosa serve>` se il gesto è della persona
  (`Tu: invio a terzi`, `Tu: password`, `Tu: pagamento`, `Tu: gesto fisico`). Il `Tu: <cosa serve>`
  nomina il gesto del passo, non un perché.
- Status `da fare|in corso|fermo`, priorità `alta|media|bassa`, come in `arturo todo`.
- **Task e Descrizione si leggono senza contesto**: il verbo all'infinito e cosa serve per riprendere.
  Gergo, percorsi e hash vanno in Decisioni.
- **Ogni idea ha un destino**: un'idea già vista prima non resta idea una terza volta. "→ memoria"
  nomina con `[[nome]]` la nota dove l'idea è finita: il gate cerca quella nota nella memoria o in
  `_in-attesa.md`, e senza nota esce rosso.
