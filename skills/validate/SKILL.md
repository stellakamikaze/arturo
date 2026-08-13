---
name: validate
description: Validazione pre-commit language-aware (type-check, test, lint, build) - Node/TS, Python o prosa
---

# Validazione Pre-Commit

Sequenza di verifica obbligatoria prima di ogni commit. NON committare se un qualsiasi step fallisce.

**Prima cosa: rileva il tipo di progetto e usa i comandi giusti.** Non assumere Node.
Il gate condiviso `shared/validation-gate.md` descrive per ogni linguaggio quali
comandi contano — usalo come riferimento. In sintesi:

- **`package.json` presente (Node/TS)** → step 1-5 qui sotto con gli script npm che
  ESISTONO davvero (`cat package.json` e guarda `scripts`): tipicamente `npx tsc --noEmit`,
  `npm test` (o lo script test del progetto), `npm run lint`, `npm run build`. Se uno
  script non esiste, salta quello step, non inventarlo.
- **`pyproject.toml`/`requirements.txt` (Python)** → `ruff check .` (o `flake8`),
  `mypy .` se configurato, `pytest -q`.
- **Progetto statico / prosa / altro** → niente toolchain: verifica a mano che i file
  cambiati siano coerenti e completi.

## Step 1: Type-check

```bash
# Node/TS: npx tsc --noEmit    |    Python: mypy .    (salta se non applicabile)
```

**Criterio**: zero errori. Se fallisce, correggi prima di procedere.

## Step 2: Test Suite

```bash
# Node: npm test (o lo script reale)    |    Python: pytest -q
```

**Criterio**: tutti i test passano. Se fallisce, correggi prima di procedere.

## Step 3: Lint

```bash
# Node: npm run lint    |    Python: ruff check .   (salta se non configurato)
```

**Criterio**: zero errori (warning accettabili). Se fallisce, correggi prima di procedere.

## Step 4: Console.log / debug-print Check

```bash
git diff --cached --diff-filter=ACM | grep -nE 'console\.log|(^|\s)print\(|breakpoint\(\)' || echo "OK: nessun print di debug aggiunto"
```

**Criterio**: nessun print di debug nei file staged (esclusi `console.warn`/log intenzionali).

## Step 5: Build Check

```bash
# Node: npm run build    (salta se il progetto non ha una build)
```

**Criterio**: build completata senza errori.

## Risultato

Riporta checklist:
- [ ] Type-check: PASS/FAIL
- [ ] Test: PASS/FAIL (N test, N passed)
- [ ] Lint: PASS/FAIL
- [ ] Console.log: PASS/FAIL
- [ ] Build: PASS/FAIL

Se tutti PASS → procedi con il commit.
Se qualsiasi FAIL → correggi e riesegui `/validate`.

## Step 6 (opzionale): Mutation Testing

Solo su richiesta esplicita o per codice critico (pagamenti, auth, sync dati):

```bash
npx stryker run --mutate 'src/lib/services/TARGET.ts'
```

**Criterio**: mutation score > 60%. Un 100% line coverage con 40% mutation score significa che il 60% dei test non verifica nulla di reale.

Non usare di default — e' lento. Usare per validare che i test di un modulo critico catturino davvero i bug.
