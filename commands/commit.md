---
description: Commit intelligente basato sul contesto della conversazione
argument-hint: "[descrizione] (opzionale)"
allowed-tools: Bash(git:*)
model: haiku
---

# Commit Intelligente

Crea commit git basati sul contesto della conversazione corrente.

## Argomenti

**$ARGUMENTS**

## Comportamento

### Senza argomenti
Committa SOLO i file correlati al lavoro recente della conversazione.
NON fare `git add .` cieco.

### Con descrizione
Filtra i file in base alla descrizione fornita e committa solo quelli rilevanti.

### Con richiesta multi-commit
Se richiesto, crea **commit bisectable** — ogni commit è un cambiamento logico indipendente.

---

## Processo

### 1. Analizza Contesto

```bash
git status --short
git diff --name-only
git diff --cached --name-only
git log --oneline -5
```

### 2. Identifica File Rilevanti

Dalla cronologia della conversazione, identifica:
- File su cui hai lavorato direttamente
- File creati o modificati come parte del task
- File correlati alle modifiche richieste

**NON includere:**
- File modificati accidentalmente
- File non correlati al task corrente
- Modifiche di formattazione non richieste

### 3. Pre-Commit Check Rapido

```bash
# Console.log check
git diff --cached --diff-filter=ACM 2>/dev/null | grep -n 'console\.log' && echo "ATTENZIONE: console.log trovati" || echo "OK: nessun console.log"
```

Se trovati `console.log` nei file staged (esclusi `console.warn` intenzionali): segnala e chiedi se rimuoverli prima del commit.

### 3b. Quality Gate (bloccante, con cache)

Leggi e applica `~/.claude/shared/validation-gate.md` con **mode=quick**.

**Se FAIL**: STOP. Non procedere con il commit.
- Mostra errori all'utente
- Chiedi: fixare ora o committare comunque? (sconsigliato)
- Se non ha package.json o non ha test configurati: skip e procedi

### 4. Commit Bisectable (se multi-file)

Se le modifiche toccano **aree logiche diverse**, splitta in commit separati ordinati per dipendenza:

1. **Infrastruttura**: config, migrazioni, dipendenze
2. **Backend**: modelli, servizi, API + relativi test
3. **Frontend**: componenti, view, stili + relativi test
4. **Meta**: documentazione, tipi

Ogni commit deve essere indipendentemente valido — no import rotti, no riferimenti a codice che non esiste ancora.

Se le modifiche sono piccole (<50 righe, <4 file) o tutte nello stesso ambito logico: un singolo commit va bene.

### 5. Staging Selettivo

```bash
git add <file1>
git add <file2>
```

### 6. Crea Commit

```bash
git commit -m "$(cat <<'EOF'
<type>: <summary>
EOF
)"
```

**NON usare Co-Authored-By nei commit.**

---

## Linee Guida Messaggi

### Formato
- `<type>: <summary>` — type = feat/fix/chore/refactor/docs/test
- Modo imperativo ("Add", "Fix", "Update", non "Added", "Fixed")
- Prima lettera maiuscola dopo il type
- No punto finale

### Contenuto
- Focalizzati su "cosa" e "perché"
- Evita metriche ("reduced by 50%")
- Evita linguaggio promozionale
- Segui lo stile esistente del progetto

### Esempi Buoni
```
feat: Add user authentication middleware
fix: Handle null pointer in payment processing
chore: Update API rate limiting configuration
refactor: Extract database connection pooling
```

---

## Regole Critiche

1. **Mai `git add .`** - Sempre staging selettivo
2. **Consulta la conversazione** - Identifica file lavorati
3. **Chiedi se ambiguo** - Se non è chiaro quali file, chiedi
4. **Un commit = un cambiamento logico** - Se servono più commit, falli separati e bisectable
5. **Verifica prima di committare** - Mostra cosa stai per committare
6. **NO Co-Authored-By** - Mai includere questa riga
7. **Console.log check** - Segnala console.log nei file staged
8. **Ordine dipendenze** - Infrastruttura prima, frontend dopo

---

## Avvia

Analizza il contesto della conversazione e identifica i file su cui hai lavorato.
