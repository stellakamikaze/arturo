# /fine: gli handoff in uscita

`/fine` legge questo file nella FASE 6 se il dry-run di `bin/handoff-retention.py` stampa almeno un
blocco `=== IN USCITA`. Lo store tiene gli ultimi 5 handoff per progetto, o per filone se l'handoff ha
la riga "- Filone:". Nessun handoff esce senza essere letto.

## Una scelta per ogni voce

Per ogni handoff in uscita lo script stampa i Vicoli ciechi e le righe dei task senza ID. Per ogni voce
scegli:
- **Promuovi.** Il vicolo cieco che può tornare va in due righe nel `CLAUDE.md` del progetto ("NON
  fare X: causa Y"). Un task ancora valido diventa un todo adesso.
- **Già coperto.** Dici dove, dopo una ricerca vera: `grep` sul `CLAUDE.md` del progetto,
  `arturo todo`, `arturo memoria cerca "parole"`.
- **Muore.** Era una tantum o è superato, e lo dici.

## Cosa fa poi la coda

Lo spostamento nel cestino e l'indice li fa la coda della FASE 9:
- esce solo ciò che il dry-run ha mostrato: un handoff scritto nel frattempo da un'altra sessione resta;
- senza dry-run non esce niente, e la riga della coda dice "retention NON applicata";
- il cestino è `~/.claude/data/handoffs/.cestino/<slug>/`: i file restano 30 giorni e la coda lo
  svuota oltre i 30 giorni per ogni progetto, dicendo quanti file ha spostato;
- per riportare un handoff, sposta il file da `.cestino/<slug>/` alla cartella `<slug>/`;
- l'indice `~/.claude/data/handoffs/INDEX.md` nasce dagli handoff e non si corregge a mano.
