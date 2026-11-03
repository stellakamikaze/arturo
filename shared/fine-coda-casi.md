# La coda di /fine: i passi e due casi

`/fine` legge questo file nella FASE 9 quando l'uscita della coda (`bin/fine-coda.py`) non è chiara, se
la coda stampa `SKILL TUE NON SALVATE`, o se la persona ha `~/.claude/personale/fine-coda.py` (le sue
aggiunte).

## Cosa fa la coda, in ordine

1. Si ferma se `~/.claude` è a metà di un rebase o se `hooks/controlla-config.py` la trova rotta: una
   config rotta committata arriverebbe su tutte le macchine.
2. Ripete il gate della FASE 5. Senza handoff della sessione salta gate, retention e indice e fa solo il
   sync della config.
3. Sposta nel cestino i file del dry-run della FASE 6 e rigenera l'indice.
4. Aggiunge al commit i file di Arturo e gli handoff. CLAUDE.md, `personale/`, todo e memoria entrano
   solo se il remote della config risulta privato a `gh`. Mai lucchetti, log delle letture della
   memoria, copie `.bak-*` e indice della memoria.
5. Ferma il commit se un file in stage ha i marcatori di conflitto.
6. Fa due commit: la memoria a parte ("memoria: applicata da /fine"), così si annulla da sola, poi il sync.
7. Fa il push. Se il push è rifiutato, fa un pull `--rebase --autostash` e riprova una volta. Non pusha
   se origin è il repository pubblico di Arturo.

## SKILL TUE NON SALVATE

Dillo alla persona con i nomi delle skill: il repository della sua config non risulta privato, e
pubblicarle lì le rende visibili a tutti. Chiedi se vuole pubblicarle. Col suo sì, per ognuna:
1. `git -C ~/.claude add -- skills/<nome>`;
2. `git -C ~/.claude commit -m "skill <nome>"`;
3. `git -C ~/.claude push origin main`.

Senza sì restano su questa macchina, e il prossimo `/fine` lo ricorda.

## Le tue aggiunte

Se esiste `~/.claude/personale/fine-coda.py`, la coda lo lancia due volte: dopo l'indice
(`"fase": "dopo-index"`) e prima del commit (`"fase": "prima-commit"`). Gli aggiornamenti di Arturo
non lo toccano.

- **Ingresso**: su stdin un JSON con fase, handoff, slug, radice, i file in stage e gli argomenti
  scritti dopo `--` nel comando della coda.
- **Uscita**: una riga JSON `{"esiti": [...], "path": [...], "blocca": null}`. Gli esiti finiscono
  nella riga `coda:`. I path entrano nel commit di sync, solo verso un remote privato.
- **Exit**: 0 fatto, 3 servizio giù, 4 blocca. La coda risponde con lo stesso codice: con 3 il resto è
  fatto, con 4 non parte nessun commit.
