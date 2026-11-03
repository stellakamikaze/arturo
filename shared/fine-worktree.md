# /fine in un worktree

`/fine` legge questo file nella FASE 3 se la sessione lavora in un worktree: `/inizio` lo apre quando
un'altra sessione lavora sullo stesso progetto. Il resto di `/fine` gira poi dal tree principale.

## Riportare il lavoro

1. Il commit della FASE 3 va sul branch del worktree.
2. Guarda i file ignorati con `git status --short --ignored` (righe `!!`). I file di lavoro fuori da
   git, come una cartella `lavoro/`, esistono solo lì.
3. Esci con `ExitWorktree` e `keep`. Dentro il worktree la guardia di Claude Code vieta git sul tree
   principale.
4. Fuori, riporta il lavoro con `git -C <tree principale> merge --ff-only <branch>`.
5. Se il fast-forward non riesce perché l'altra sessione ha committato nel frattempo, e il tree
   principale non ha modifiche, prova `git -C <tree principale> merge --no-edit <branch>`. Al primo
   conflitto lancia `git -C <tree principale> merge --abort`. Rebase e merge con conflitti non si fanno
   a fine sessione.
6. Merge riuscito: copia nel tree principale, allo stesso percorso, i file ignorati che sono lavoro
   della sessione. Cache, dipendenze e build si rigenerano (`node_modules`, `__pycache__`, `.venv`,
   `dist`) e restano fuori. Un file che esiste già nel tree principale non si sovrascrive: il worktree
   resta e l'handoff lo dice.
7. Solo dopo la copia lancia `git -C <tree principale> worktree remove <percorso del worktree>` e
   `git -C <tree principale> branch -d <branch>`. `worktree remove` cancella anche i file ignorati,
   senza avviso (segnalazione n. 13).

## Il ramo è riportato? Controllalo prima dell'handoff

`git -C <tree principale> cherry HEAD <branch>` non deve stampare righe con `+`: ognuna è un commit del
ramo che la cartella principale non ha. Una riga con `-` è un commit già arrivato in altra forma
(cherry-pick, rebase) e non conta. `branch --no-merged` qui non basta: guarda solo la storia, e
segnerebbe bloccato un ramo già riportato. È lo stesso controllo di `arturo contesto`, così `/inizio`
e `/fine` dicono la stessa cosa.

Con almeno una riga `+` il lavoro non è nella cartella principale:
- il worktree resta;
- l'handoff ha Status `bloccato`;
- la Ripartenza comincia con "N commit restano sul ramo <branch>, non nella cartella principale";
- riportarli diventa un todo;
- lo dici alla persona nella chiusura, non solo nell'handoff (segnalazione n. 20: venti commit fermi
  sul ramo e nessuno lo sapeva).
