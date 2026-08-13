---
allowed-tools: Bash(git:*)
description: Crea nuovo git worktree che traccia la branch remota default
argument-hint: (nessun argomento necessario)
---

# Git Worktree

## Contesto

Repository corrente: !`git remote get-url origin 2>/dev/null || echo "Nessun remote origin trovato"`

Branch corrente: !`git branch --show-current`

Worktree esistenti: !`git worktree list`

Branch esistenti: !`git branch --list 'worktree*'`

Branch remota default: !`git remote show origin 2>/dev/null | grep "HEAD branch" | cut -d: -f2 | xargs || git branch -r | grep -E 'origin/(main|master)' | head -1 | sed 's/.*origin\///'`

## Task

Crea un nuovo git worktree con nome branch auto-generato che traccia la branch remota default.

**Comportamento:**
1. Determina la branch remota default (origin/main o origin/master)
2. Trova tutte le branch esistenti `worktree*` per determinare il prossimo numero
3. Crea una nuova branch `worktreeN` dove N è il prossimo numero sequenziale (partendo da 1)
4. Crea il worktree al path `../worktreeN` (directory parent del repo corrente)
5. Configura la nuova branch locale per tracciare la branch remota default (es. `origin/main`)

**Processo:**
1. Fetch ultime modifiche: `git fetch origin`
2. Determina branch remota default:
   - Prima prova `git remote show origin | grep "HEAD branch"`
   - Verifica che la branch esista in remote con `git branch -r`
   - Se non determinabile, controlla origin/main, poi origin/master
   - Se nessuna esiste, fallisci con messaggio chiaro
3. Lista branch worktree esistenti: `git branch --list 'worktree*'`
4. Determina prossimo numero disponibile
5. Crea worktree con tracking:
   - Usa: `git worktree add --track -b worktreeN ../worktreeN origin/branch-name`
6. Mostra messaggio di successo con:
   - Nome nuova branch (worktreeN)
   - Path assoluto del worktree
   - Branch upstream di tracking

**Esempi:**
- `/worktree` - Crea worktree1 at ../worktree1 tracking origin/main
- `/worktree` (quando worktree1 esiste) - Crea worktree2 at ../worktree2

**Note:**
- Il comando NON accetta argomenti - i nomi branch sono sempre auto-generati
- La nuova branch traccia sempre la branch remota default
- Ogni worktree ha un nome branch numerato partendo da 1
- La directory worktree viene creata nella directory parent del repository corrente
