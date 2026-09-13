# Validation Gate — Modulo Condiviso

Usato da: `/fine`

## Modalità

| Mode | tsc | test | lint | console.log | build | Quando |
|------|-----|------|------|-------------|-------|--------|
| `quick` | x | x | | x | | `/fine` |
| `full` | x | x | x | x | x | verifica manuale |
| `shipping` | x | x | x | | | consegna manuale |

## Nessuna cache

Ogni gate esegue i controlli nel working tree corrente. Un esito recente non prova una sorgente cambiata.

## Esecuzione

```bash
# Rilevamento linguaggio: niente piu' exit-0 MUTO sui progetti non-Node
# (evita il false-green sui progetti Python e su tutto il non-code).
if [ -f "package.json" ]; then PROJ_LANG="node"
elif [ -f "pyproject.toml" ] || [ -f "requirements.txt" ] || ls *.py >/dev/null 2>&1; then PROJ_LANG="python"
else PROJ_LANG="prose"; fi

if [ "$PROJ_LANG" = "node" ]; then
  # Step 1: TypeScript (tutti i mode)
  echo "--- TypeScript ---"
  set -o pipefail
  npx tsc --noEmit 2>&1 | tail -20
  TSC_EXIT=${PIPESTATUS[0]}

  # Step 2: Test (tutti i mode)
  echo "--- Test ---"
  npm test 2>&1 | tail -30
  TEST_EXIT=${PIPESTATUS[0]}

  # Step 3: Lint (solo full e shipping)
  if [ "$MODE" = "full" ] || [ "$MODE" = "shipping" ]; then
    echo "--- Lint ---"
    npm run lint 2>&1 | tail -20
    LINT_EXIT=${PIPESTATUS[0]}
  fi

  # Step 4: Console.log (solo quick e full)
  if [ "$MODE" = "quick" ] || [ "$MODE" = "full" ]; then
    echo "--- Console.log ---"
    git diff --cached --diff-filter=ACM 2>/dev/null | grep -n 'console\.log' && echo "WARN: console.log trovati" || echo "OK"
  fi

  # Step 5: Build (solo full)
  if [ "$MODE" = "full" ]; then
    echo "--- Build ---"
    npm run build 2>&1 | tail -20
    BUILD_EXIT=${PIPESTATUS[0]}
  fi

elif [ "$PROJ_LANG" = "python" ]; then
  # Progetto Python. Tool assenti =
  # SKIP ESPLICITO (mai exit-0 muto): l'assenza di check non e' un "verde".
  echo "--- Python: ruff ---"
  command -v ruff >/dev/null 2>&1 && { ruff check . 2>&1 | tail -20; RUFF_EXIT=$?; } || echo "ruff assente: SKIP esplicito (installa per il lint)"
  echo "--- Python: pytest ---"
  command -v pytest >/dev/null 2>&1 && { pytest -q 2>&1 | tail -30; TEST_EXIT=$?; } || echo "pytest assente: SKIP esplicito (nessun test eseguito)"
  if [ "$MODE" = "full" ] && command -v mypy >/dev/null 2>&1 && [ -f pyproject.toml ]; then
    echo "--- Python: mypy ---"
    mypy . 2>&1 | tail -20; MYPY_EXIT=$?
  fi

else
  # Prosa/memory/config: nessun codice da compilare. NON fingere verde:
  # substance gate advisory sui deliverable verso persone reali.
  echo "--- Nessun progetto code: substance gate (advisory) ---"
  echo "Lo firmeresti? Verifica a mano i deliverable: contenuto NON vuoto,"
  echo "ogni cifra con fonte documentale, chiusura = un fatto non una metafora."
fi
```

## Risultato

Se qualsiasi step critico fallisce (tsc, test):
- **STOP** — non procedere
- Mostra errori
- In `/fine`: chiedi se fixare ora o documentare l'errore.
- Prima di una consegna: STOP assoluto, non consegnare codice rotto

## Referenziare da altri comandi

Nei workflow che chiudono una sessione:
```
Leggi e applica `~/.claude/shared/validation-gate.md` con mode=[quick|full|shipping].
```
