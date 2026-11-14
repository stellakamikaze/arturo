# La migrazione dal clone al plugin

Questa pagina dice come `arturo migra` porta Arturo dal clone in `~/.claude` al plugin. È lo strato trasversale Ingresso: separa Arturo dall'Orsa senza toccare i file della persona. Il contratto degli strati sta in [`strati.md`](strati.md), la catena di fiducia in [`fiducia.md`](fiducia.md).

## Come funziona (F4, 5/11/2026)

Chi ha Arturo come clone in `~/.claude` passa al plugin con `arturo migra` (`bin/migra.py`). Prima si lancia la prova, che non tocca niente; poi la migrazione vera, con Claude Code chiuso, da un Terminale.

```
arturo migra --prova   rapporto: PRONTA o FERMA coi motivi, cosa cambia, cosa resta della persona
                       → ~/.claude/data/migra/rapporto-<data>.txt, da mandare con /segnala
arturo migra           1 controlli del rapporto, e nessuna sessione di Claude Code aperta
                       2 copia di sicurezza: ~/.claude-arturo-clone-<data>/copia (.git, file di Arturo,
                         settings.json, file dei plugin, ancora, file di blocco) + codice (bin e hooks
                         di chi migra, da cui si lancia indietro) + migra.json coi passi
                       3 personale.py separa --senza-commit: /inizio cambiato → personale/inizio.md
                       4 catalogo → ancora = chiave del clone → tag firmato e sha (verifica_catalogo)
                         → claude plugin install → la copia torna col MANIFEST firmato?
                       5 settings.json in una scrittura: via gli hook di Arturo, unione a tre vie col
                         frammento del plugin, file di blocco
                       6 i file di Arturo e .git escono da ~/.claude (la copia li tiene)
                       un passo che fallisce → indietro da solo (uscita 1, o 3 per il catalogo)
arturo migra indietro  toglie plugin e catalogo messi dalla migrazione, riporta ogni file dalla copia
```

- **La base dell'unione** è il `settings.json` di Arturo da cui il clone è partito (`git show <merge-base>:settings.json`), tradotto come il pacchetto traduce il suo (barra dal puntatore, stile `arturo:`). Una voce che la persona ha lasciato com'era prende il valore del plugin, una voce sua resta sua, una voce cambiata da tutte e due le parti ferma la migrazione e si nomina.
- **Gli hook che escono** sono quelli che lanciano un file di Arturo dentro `~/.claude`, anche se il plugin non li porta più: dopo il passo 6 quel file non c'è. Un hook della persona resta. Una barra in basso della persona che usa un file di Arturo ferma la migrazione.
- **Il rapporto** nomina i file di Arturo e conta quelli della persona, senza nomi e senza i valori dei settings: va a chi mantiene Arturo.
- **Una `~/.claude` con Arturo come `upstream`** (il repository della persona) si migra solo con `--unica-macchina`, dal 9/11/2026 (segnalazione n. 62). `.git` e `.gitignore` restano, e i file di Arturo escono con un commit nel repository della persona, che la `/fine` dopo pubblica. `migra indietro` lo annulla con un `git revert`, senza sostituire `.git`, che nel frattempo può avere commit suoi. Con più computer il commit arriverebbe agli altri alla prima sincronizzazione e lì toglierebbe Arturo e le guardie senza avviso. Per questo senza `--unica-macchina` la migrazione si ferma, e con più computer si fa a mano.
- **La sessione aperta** blocca la migrazione: una sessione partita col clone ha gli hook in `~/.claude/hooks`, e dopo il passo 6 ogni hook mancante bloccherebbe le sue azioni.
- Il demone fsmonitor di git tiene aperta `.git`: la migrazione lo spegne per i suoi git, e copia e confronto saltano i socket.
- **Il CLAUDE.md** resta della persona. Le regole consigliate che `/setup` ci aveva scritto col plugin arrivano anche col metodo all'avvio: il rapporto le conta, e dopo la migrazione `arturo personale regole-doppie` le elenca e con `--togli` le toglie, con la copia in `CLAUDE.md.prima-del-plugin` (#4874, banco `tests/test_regole_doppie_2026_11_06.py`). Si toglie solo una riga uguale per intero alla regola, e senza un seguito rientrato: una riga che le somiglia si elenca e resta.
- Il banco `tests/test_migra_2026_11_05.py` (MG01-MG18) prova tutto con la CLI vera, in un `CLAUDE_CONFIG_DIR` di prova: rapporto, sessione aperta, migrazione, ritorno identico file per file, tag non firmato, conflitto nei settings dopo l'installazione, `upstream` senza e con `--unica-macchina` (MG07, MG18).
