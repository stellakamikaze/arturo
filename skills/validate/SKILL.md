---
name: validate
description: >-
  Esegue la sequenza di verifica prima di un commit — type-check, test, lint, build — riconoscendo da
  sola se il progetto è Node/TypeScript, Python o prosa, e blocca il commit se uno step fallisce.
when_to_use: >-
  Usa prima di ogni commit e quando /fine, /ship o /commit la richiamano; anche quando l'utente dice
  «controlla che sia tutto verde», «valida», «posso committare?». NON per correggere ciò che trova
  (quella è autofix) e non per la review del contenuto (review-checklist). Segui tutti i passi
  nell'ordine: non prendere scorciatoie basandoti su questa description.
---

# /validate — Validazione pre-commit

## Step 0: Rileva il tipo di progetto

Il gate condiviso `shared/validation-gate.md` descrive per ogni linguaggio quali
comandi contano — usalo come riferimento. In sintesi:

- **`package.json` presente (Node/TS)** → step 1-5 qui sotto con gli script npm che
  ESISTONO davvero (`cat package.json` e guarda `scripts`): tipicamente `npx tsc --noEmit`,
  `npm test` (o lo script test del progetto), `npm run lint`, `npm run build`.
- **`pyproject.toml`/`requirements.txt` (Python)** → `ruff check .` (o `flake8`),
  `mypy .` se configurato, `pytest -q`.
- **Progetto statico / prosa / altro** → niente toolchain: verifica a mano che i file
  cambiati siano coerenti e completi.

## Importante

- NON committare se un qualsiasi step fallisce: correggi e riesegui `/validate` da capo.
- Non assumere Node: i comandi li decide lo step 0, non l'abitudine.
- Se uno script non esiste nel progetto, salta quello step e dichiaralo nel risultato; non inventarlo.

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
Se qualsiasi FAIL → vale la regola in «Importante»: correggi e riesegui `/validate`.

## Step 6 (opzionale): Mutation Testing

Solo su richiesta esplicita o per codice critico (pagamenti, auth, sync dati):

```bash
npx stryker run --mutate 'src/lib/services/TARGET.ts'
```

**Criterio**: mutation score > 60%. Un 100% line coverage con 40% mutation score significa che il 60% dei test non verifica nulla di reale.

Non usare di default — è lento. Usare per validare che i test di un modulo critico catturino davvero i bug.
