# La coda di /fine: i passi e due casi

`/fine` legge questo file nella FASE 9 quando l'uscita della coda (`bin/fine-coda.py`) non è chiara, se
la coda stampa `SKILL TUE NON SALVATE`, `FILE TUOI NON SALVATI` o `SEGRETO`, o se la persona ha `~/.claude/personale/fine-coda.py` (le sue
aggiunte).

## Cosa fa la coda, in ordine

1. Si ferma se `~/.claude` è a metà di un rebase o se `hooks/controlla-config.py` la trova rotta: una
   config rotta committata arriverebbe su tutte le macchine.
2. Ripete il gate della FASE 5. Senza handoff della sessione salta gate, retention e indice e fa solo il
   sync della config. In rotazione (`--leggero` o `--rotazione`) si ferma anche se l'handoff chiede alla
   persona `/clear` e `/inizio`: in rotazione li fa il tool `ruota`. Con `ARTURO_ROTAZIONE=0` tace.
3. Sposta nel cestino i file del dry-run della FASE 6 e rigenera l'indice.
4. Aggiunge al commit i file di Arturo e gli handoff. CLAUDE.md, `personale/`, todo e memoria entrano
   solo se il remote della config risulta privato a `gh`. Mai lucchetti, log delle letture della
   memoria, copie `.bak-*` e indice della memoria. Verso un remote non privato, nelle cartelle di Arturo
   (`commands`, `bin`, `hooks` e le altre) entrano solo i file già salvati in git.
5. Ferma il commit se un file in stage ha i marcatori di conflitto.
6. Ferma il commit se la guardia dei segreti trova una chiave nelle righe nuove dello stage (exit 7).
7. Fa due commit: la memoria a parte ("memoria: applicata da /fine"), così si annulla da sola, poi il sync.
8. Ferma il push se la guardia trova una chiave nei commit che il remote non ha ancora (exit 7).
9. Fa il push. Se il push è rifiutato, rifà i commit sopra quelli del remote in una copia di prova dentro
   `.git`, mai nei file che Claude Code sta leggendo, e riprova una volta. In `~/.claude` arriva solo una
   copia integra. Con un conflitto vero, o con un file modificato qui che il remote cambia, `~/.claude` resta
   com'era, i commit restano in locale e la riga dice "push non riuscito" col motivo. Non pusha
   se origin è il repository pubblico di Arturo.

## SEGRETO (exit 7)

La coda nomina il file e il tipo di chiave, mai il valore. Commit e push partono da uno script: la guardia
dei comandi Bash non li vede, e per questo la coda fa lo stesso controllo.
- **Chiave vera**: toglila dal file e mettila nel vault o in una variabile d'ambiente. Se sta già in un
  commit non spinto, toglila anche da lì (`git -C ~/.claude log origin/main..HEAD` elenca quei commit).
  Poi rilancia la coda.
- **Falso allarme** (una chiave finta di un test): fai tu il commit o il push a mano. La guardia dei comandi
  chiede conferma alla persona, e la decisione resta sua.
- **La guardia non si carica**: manca `hooks/commit-secret-gate.py`. Reinstalla Arturo con `/aggiorna`.

## FILE TUOI NON SALVATI

Come per le skill qui sotto: sono file nuovi della persona nelle cartelle di Arturo (un comando, un hook,
uno script). Il repository della config non risulta privato, quindi restano su questa macchina. Col suo sì
li pubblichi con `git -C ~/.claude add -- <file>`, poi commit e push.

## SKILL TUE NON SALVATE

Dillo alla persona con i nomi delle skill: il repository della sua config non risulta privato, e
pubblicarle lì le rende visibili a tutti. L'elenco porta le skill nuove e quelle sue già salvate che la
sessione ha modificato, per esempio con una correzione. Chiedi se vuole pubblicarle. Col suo sì, per ognuna:
1. `git -C ~/.claude add -- skills/<nome>`;
2. `git -C ~/.claude commit -m "skill <nome>"`;
3. `git -C ~/.claude push origin main`.

Senza sì restano su questa macchina, e il prossimo `/fine` lo ricorda.

## Le tue aggiunte

Se esiste `~/.claude/personale/fine-coda.py`, la coda lo lancia due volte: dopo l'indice
(`"fase": "dopo-index"`) e prima del commit (`"fase": "prima-commit"`). Gli aggiornamenti di Arturo
non lo toccano.

- **Ingresso**: su stdin un JSON con fase, handoff, slug, radice, i file in stage, `leggero`, `rotazione`
  e gli argomenti scritti dopo `--` nel comando della coda.
- **Uscita**: una riga JSON `{"esiti": [...], "path": [...], "blocca": null}`. Gli esiti finiscono
  nella riga `coda:`. I path entrano nel commit, solo verso un remote privato: quelli sotto `data/memory`
  nel commit della memoria, gli altri nel commit di sync.
- **Solo i tuoi path**: con `--solo-percorsi` la coda non aggiunge per cartella. Entrano l'handoff,
  l'indice, il segno del fine completo, le uscite della retention e i path del tuo script. Serve se tieni
  più sessioni sulla stessa config: il lavoro a metà delle altre resta fuori dal commit.
- **Exit**: 0 fatto, 3 servizio giù, 4 blocca. La coda risponde con lo stesso codice: con 3 il resto è
  fatto, con 4 non parte nessun commit.
