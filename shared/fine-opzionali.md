# /fine: gli opzionali

`/fine` legge questo file con `--full`, oppure quando la condizione di un opzionale è vera.

## A. CLAUDE.md personale

Condizione: `--full`, o la sessione ha prodotto una regola che vale in ogni sessione.

Sale in `~/.claude/CLAUDE.md` solo una di queste:
- una preferenza della persona;
- un freno prima di un'azione con effetti;
- una correzione che si è ripetuta.

Una riga per regola. La scrivi dopo il sì della persona, anche con `/fine salva`, ed entra nel commit
della FASE 9.

## B. Doc staleness

Condizione: `--full`, o la sessione ha toccato documenti `.md`.

Confronta le modifiche con i `.md` del repo. Un documento che descrive codice cambiato e non aggiornato
diventa un todo e una riga della tabella dell'handoff.
