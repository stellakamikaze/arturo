# /setup, FASE 7: il repository privato

Controlla prima il permesso `workflow`. Arturo contiene un file di
automazione, e senza quel permesso GitHub rifiuta il primo invio e il repository resta vuoto (segnalazione n. 60):

```bash
gh auth status 2>&1 | grep -q "workflow" && echo "permesso workflow: c'è" || echo "permesso workflow: manca"
```

Se manca, fai lanciare alla persona `! gh auth refresh -h github.com -s workflow`: è un login nel browser
col codice, e Claude non può farlo al suo posto. Poi crea il repository:

```bash
git -C ~/.claude remote rename origin upstream
gh repo create <nome-repo> --private --source ~/.claude --remote origin --push
git -C ~/.claude remote -v
```

L'automazione di Arturo gira solo nel repository pubblico: nel repository privato il suo lavoro si salta e non consuma minuti. Non serve spegnere le Actions.
