Copia fissata di `claude-code/mods/blast-radius` da anthropics/claude-code-playground, commit
569c5283d9a0a7ee7938df85bb32e4f48cbb8c86 (`569c5283d9a0`, 1/10/2026), licenza Apache-2.0 (`LICENSE`). Letta per intero
il 14/10/2026: lancia solo `sleep`, `bash -c` con i percorsi passati come argomenti, `find`, `du`, comandi
git in lettura (`status`, `diff --shortstat`, `log`, `rev-parse`, `clean -n`) e gli elenchi delle migrazioni.
Niente rete, niente scritture su file.

Modifiche di Arturo, segnate `arturo (14/10/2026)` nel sorgente:
1. Senza una superficie che disegna (`claude -p`, cron, workflow) il comando passa: nessuno potrebbe premere
   Proceed e resterebbe fermo 10 minuti.
2. `rm -rf` / `rm -f` su soli percorsi in `/tmp`, `/private/tmp`, `/var/folders` o `$TMPDIR` passa senza pannello.
3. I testi che si vedono (pannello, pulsanti Procedi e Annulla, riepiloghi, messaggi a Claude) sono in italiano.

Non si aggiorna da sola: una versione nuova si scarica, si rilegge e si copia qui a mano.
