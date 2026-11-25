# /fine in un worktree

`/fine` legge questo file nella FASE 3 se la sessione lavora in un worktree: `/inizio` lo apre quando
un'altra sessione lavora sullo stesso progetto, e una sessione in background ci entra da sola. Il resto
di `/fine` gira poi dal tree principale, oppure dal worktree se la sessione non può uscirne.

Dentro il worktree la guardia di Claude Code rifiuta ogni git rivolto al tree principale, con l'opzione
`-C` o con un `cd` (26/10/2026, mediterranea-landing). Per questo il ramo si segna e si controlla da
dentro, e il merge parte solo dopo l'uscita, nella cartella corrente.

## Riportare il lavoro

1. Il commit della FASE 3 va sul branch del worktree.
2. Guarda i file ignorati con `git status --short --ignored` (righe `!!`). I file di lavoro fuori da
   git, come una cartella `lavoro/`, esistono solo lì.
3. Segna il ramo come chiuso, da dentro il worktree: `python3 ~/.claude/bin/arturo riporto segna <branch>`.
   Il segno sta in `~/.claude/data/riporti.json`, fuori dal repository: la guardia del worktree
   rifiuta `git config`, che scrive nella config comune a tutti i worktree (segnalazione n. 97). Il
   prossimo `/inizio` nel tree principale vede il segno e sa che il ramo aspetta solo il merge (#4007).
   Il segno vale per il commit in cima al ramo: dopo un altro commit sul ramo, rilancia il comando.
4. Esci con `ExitWorktree` e `keep`. Se il tool manca o rifiuta, la sessione è fissata al worktree
   (un subagent isolato, una sessione aperta già dentro): passa al riporto differito.
5. Fuori, nella cartella corrente, che è il tree principale: `git merge --ff-only <branch>`, senza `-C`.
   Se la guardia rifiuta il comando con "This session is isolated in the worktree", passa al riporto
   differito.
6. Se il fast-forward non riesce perché l'altra sessione ha committato nel frattempo, e il tree
   principale non ha modifiche, prova `git merge --no-edit <branch>`. Al primo conflitto lancia
   `git merge --abort`. Rebase e merge con conflitti non si fanno a fine sessione.
7. Merge riuscito: copia nel tree principale, allo stesso percorso, i file ignorati che sono lavoro
   della sessione. Cache, dipendenze e build si rigenerano (`node_modules`, `__pycache__`, `.venv`,
   `dist`) e restano fuori. Un file che esiste già nel tree principale non si sovrascrive: il worktree
   resta e l'handoff lo dice.
8. Solo dopo la copia lancia `git worktree remove <percorso del worktree>` e `git branch -d <branch>`:
   col ramo sparisce anche il segno del passo 3. `worktree remove` cancella anche i file ignorati, senza
   avviso (segnalazione n. 13).
   Mai `--force`: se `remove` si rifiuta, nel worktree ci sono file non salvati in un commit, e
   `--force` li cancella (segnalazione n. 55). La guardia chiede conferma e li elenca.

## Riporto differito

Vale quando la sessione non può lanciare git sul tree principale (passi 4 e 5). Il lavoro è già al
sicuro: il commit sta nel repository, e il segno del passo 3 dice che la sessione l'ha chiuso.
- il worktree e il ramo restano;
- il resto di `/fine` gira dal worktree, con gli stessi comandi;
- l'handoff ha Status `in progress`, non `bloccato`: il merge lo fa il prossimo `/inizio` nel tree
  principale, che vede il ramo segnato "chiuso da /fine" e lo riporta coi passi 5-8;
- la Ripartenza comincia con "N commit sul ramo <branch>: li riporta nella cartella principale il
  prossimo /inizio";
- lo dici alla persona nella chiusura, in una riga.

## Il ramo è riportato? Controllalo prima dell'handoff

`git cherry <branch principale> <branch>` non deve stampare righe con `+`: ognuna è un commit del ramo
che la cartella principale non ha. Il comando gira uguale dal tree principale e dal worktree, perché i
rami sono comuni. Una riga con `-` è un commit già arrivato in altra forma (cherry-pick, rebase) e non
conta. `branch --no-merged` qui non basta: guarda solo la storia, e segnerebbe bloccato un ramo già
riportato. È lo stesso controllo di `arturo contesto` (`git cherry HEAD <branch>` dal tree principale),
così `/inizio` e `/fine` dicono la stessa cosa.

Con almeno una riga `+` e senza il riporto differito, il lavoro non è nella cartella principale:
- il worktree resta;
- l'handoff ha Status `bloccato`;
- la Ripartenza comincia con "N commit restano sul ramo <branch>, non nella cartella principale";
- riportarli diventa un todo;
- lo dici alla persona nella chiusura, non solo nell'handoff (segnalazione n. 20: venti commit fermi
  sul ramo e nessuno lo sapeva).
