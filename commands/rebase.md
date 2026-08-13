---
description: Rebase automatico con gestione stash intelligente
argument-hint: "[branch] (default: upstream della branch corrente)"
allowed-tools: Bash(git:*)
---

# Rebase Automatico

Rebase della branch corrente sulla branch remota con gestione intelligente dello stash.

## Argomenti

**$ARGUMENTS** (opzionale - default: branch upstream)

---

## Comportamento

| Comando | Azione |
|---------|--------|
| `/rebase` | Rebase su branch remota di tracking |
| `/rebase main` | Rebase su `origin/main` |
| `/rebase feature/x` | Rebase su `origin/feature/x` |

---

## Processo

### 1. Verifica Stato

```bash
CURRENT_BRANCH=$(git branch --show-current)
echo "Branch corrente: $CURRENT_BRANCH"

if [ -d ".git/rebase-merge" ] || [ -d ".git/rebase-apply" ]; then
  echo "ATTENZIONE: Rebase già in corso!"
  echo "Usa: git rebase --continue | --abort | --skip"
  exit 1
fi
```

### 2. Gestione Cambiamenti Non Committati

```bash
CHANGES=$(git status --porcelain)

if [ -n "$CHANGES" ]; then
  echo "Cambiamenti non committati rilevati, eseguo stash..."
  git stash push -m "auto-stash before rebase on $(date +%Y-%m-%d_%H:%M)"
  STASHED=true
else
  STASHED=false
fi
```

### 3. Fetch Remoto

```bash
git fetch origin
```

### 4. Determina Target Branch

```bash
if [ -z "$ARGUMENTS" ]; then
  TARGET=$(git rev-parse --abbrev-ref --symbolic-full-name @{upstream} 2>/dev/null)
  if [ -z "$TARGET" ]; then
    echo "Nessun upstream configurato. Specificare branch target."
    exit 1
  fi
else
  TARGET="origin/$ARGUMENTS"
fi

echo "Target rebase: $TARGET"
```

### 5. Esegui Rebase

```bash
git rebase "$TARGET"
REBASE_STATUS=$?
```

### 6. Gestione Risultato

```bash
if [ $REBASE_STATUS -eq 0 ]; then
  echo "Rebase completato con successo!"

  if [ "$STASHED" = true ]; then
    echo "Ripristino modifiche dallo stash..."
    git stash pop
  fi
else
  echo "CONFLITTI RILEVATI!"
  echo ""
  echo "Opzioni:"
  echo "  1. Risolvi i conflitti manualmente"
  echo "  2. git rebase --continue (dopo aver risolto)"
  echo "  3. git rebase --abort (per annullare)"
  echo ""
  echo "Nota: Lo stash verrà ripristinato dopo il rebase."
fi
```

---

## Gestione Conflitti

Se ci sono conflitti:

1. **Visualizza conflitti**
   ```bash
   git diff --name-only --diff-filter=U
   ```

2. **Risolvi manualmente** i file in conflitto

3. **Continua rebase**
   ```bash
   git add <file-risolti>
   git rebase --continue
   ```

4. **Oppure annulla**
   ```bash
   git rebase --abort
   ```

---

## Note

- Lo stash viene creato automaticamente se ci sono modifiche non committate
- Lo stash viene ripristinato automaticamente dopo un rebase riuscito
- Se il rebase fallisce, lo stash rimane disponibile (`git stash list`)
- Fetch sempre eseguito prima del rebase per avere l'ultima versione

---

## Avvia

Esegui il processo di rebase con gestione automatica dello stash.
