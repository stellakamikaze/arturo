# Validation Gate — Modulo Condiviso

Usato da: `/commit`, `/ship`, `/fine`, `/validate`

## Modalità

| Mode | tsc | test | lint | console.log | build | Quando |
|------|-----|------|------|-------------|-------|--------|
| `quick` | x | x | | x | | `/commit`, `/fine` |
| `full` | x | x | x | x | x | `/validate` |
| `shipping` | x | x | x | | | `/ship` (in parallelo) |

## Logica Cache (Bridge File)

Prima di eseguire, controlla il bridge file del quality-check async:

```bash
PROJECT_HASH=$(echo "$PWD" | md5 -q 2>/dev/null || echo "$PWD" | md5sum 2>/dev/null | cut -d' ' -f1)
BRIDGE="/tmp/claude-quality-check/${PROJECT_HASH}-result.json"
NOW=$(date +%s)

if [ -f "$BRIDGE" ]; then
  BRIDGE_TS=$(python3 -c "import json; print(json.load(open('$BRIDGE'))['timestamp'])" 2>/dev/null || echo "0")
  BRIDGE_STATUS=$(python3 -c "import json; print(json.load(open('$BRIDGE'))['status'])" 2>/dev/null || echo "unknown")
  if [ $((NOW - BRIDGE_TS)) -lt 30 ] && [ "$BRIDGE_STATUS" = "pass" ]; then
    echo "Quality gate: SKIP (async check passato di recente)"
    # Skip solo per mode=quick. Full e shipping eseguono sempre.
  fi
fi
```

**Regola**: la cache si applica solo in mode `quick`. I mode `full` e `shipping` eseguono sempre tutto.

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
  npx tsc --noEmit 2>&1 | tail -20
  TSC_EXIT=$?

  # Step 2: Test (tutti i mode)
  echo "--- Test ---"
  npm test 2>&1 | tail -30
  TEST_EXIT=$?

  # Step 3: Lint (solo full e shipping)
  if [ "$MODE" = "full" ] || [ "$MODE" = "shipping" ]; then
    echo "--- Lint ---"
    npm run lint 2>&1 | tail -20
    LINT_EXIT=$?
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
    BUILD_EXIT=$?
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
- In `/commit` e `/fine`: chiedi se fixare ora o procedere comunque
- In `/ship`: STOP assoluto, non shippare codice rotto

## Referenziare da altri comandi

Nei comandi `/commit`, `/ship`, `/fine`:
```
Leggi e applica `~/.claude/shared/validation-gate.md` con mode=[quick|full|shipping].
```
