---
description: Ship automatico - merge base, test, review, commit, push, PR
argument-hint: "[descrizione PR] (opzionale)"
allowed-tools: Bash(git:*), Bash(gh:*), Bash(npm:*), Bash(npx:*)
---

# Ship: Workflow Automatico di Rilascio

Workflow **non-interattivo** e completamente automatizzato. L'utente dice `/ship`, il prossimo output è l'URL della PR.

## Argomenti

**$ARGUMENTS**

---

## Fermarsi SOLO per:
- Branch è main/master (abort)
- Conflitti di merge non risolvibili automaticamente
- Test falliti
- Review trova issue ASK che richiedono giudizio umano
- Bump MINOR o MAJOR (chiedere)

## NON fermarsi per:
- Modifiche non committate (includerle sempre)
- Scelta bump PATCH/MICRO (auto)
- Contenuto CHANGELOG (auto-generato)
- Approvazione messaggio commit (auto)

---

## Step 0: Rileva base branch

```bash
BASE=$(gh pr view --json baseRefName -q .baseRefName 2>/dev/null || gh repo view --json defaultBranchRef -q .defaultBranchRef.name 2>/dev/null || echo "main")
echo "BASE: $BASE"
```

Usa il risultato come "base branch" in tutti gli step successivi.

---

## Step 1: Pre-flight

1. Controlla branch corrente. Se su base branch, **abort**: "Sei sul branch base. Shippa da un feature branch."

2. `git status` (mai `-uall`). Modifiche non committate vengono sempre incluse.

3. `git diff $BASE...HEAD --stat` e `git log $BASE..HEAD --oneline` per capire cosa si shippa.

---

## Step 2: Merge base branch

```bash
git fetch origin $BASE --quiet && git merge origin/$BASE --no-edit
```

- Se merge conflict semplice (VERSION, CHANGELOG): auto-resolve
- Se conflict complesso: **STOP**, mostra conflitti
- Se già aggiornato: procedi silenziosamente

---

## Step 3: Esegui test

Lancia direttamente i controlli del progetto — non serve un subagent per eseguire un comando:

1. Test suite completa (col runner del progetto: `npm test`, `pytest`, `cargo test`, ecc.)
2. Type-check: `npx tsc --noEmit` (se package.json esiste)
3. Lint: `npm run lint` (se script lint esiste)

Eseguili in parallelo quando conviene (un solo blocco di comandi). Delega a un subagent (es. `test-runner`) SOLO se serve isolamento o parallelismo reale — non come indirezione di default.

- Se qualsiasi test fallisce: mostra i fallimenti e **STOP**
- Se tutti passano: continua con nota breve dei conteggi

---

## Step 4: Pre-Landing Review

Leggi e applica `~/.claude/skills/review-checklist/SKILL.md` (unica fonte di verità per la checklist).

```bash
git fetch origin $BASE --quiet
git diff origin/$BASE
```

Segui le istruzioni della skill: Pass 1 (critici), Pass 2 (informazionali), Fix-First Heuristic.

Se ci sono item AUTO-FIX: applica direttamente, output una riga per fix.
Se ci sono item ASK: presenta in UNA AskUserQuestion con opzioni per ogni item.

Se fix AUTO-FIX applicati: committa e continua al Step 5 (non ri-runnare /ship).
Se fix ASK applicati: committa e continua al Step 5.

---

## Step 5: Commit (chunk bisectable)

Analizza il diff e raggruppa le modifiche in commit logici, uno per cambiamento coerente. I raggruppamenti giusti emergono dal diff, non da categorie fisse — esempi tipici (non un'enum): infrastruttura (migrazioni, config, route), modelli & servizi con i loro test, controller & view con i loro test, documentazione (CHANGELOG, README). Adatta al progetto reale.

Ogni commit deve essere indipendentemente valido. Ordina per dipendenze.

Formato messaggio:
```
<type>: <summary>
```
type = feat/fix/chore/refactor/docs. Modo imperativo. NON usare Co-Authored-By.

---

## Step 6: Push

```bash
git push -u origin $(git branch --show-current)
```

---

## Step 7: Crea PR

```bash
gh pr create --base $BASE --title "<type>: <summary>" --body "$(cat <<'EOF'
## Summary
<bullet points dal CHANGELOG o dai commit>

## Pre-Landing Review
<risultati Step 4, o "No issues found.">

## Test
- [x] Type-check: PASS
- [x] Test suite: PASS (N test)
- [x] Lint: PASS
EOF
)"
```

**Output l'URL della PR** — questo è l'output finale.

---

## Step 8: Doc Staleness Check (opzionale)

Cross-reference il diff con file `.md` nel repo root. Per ogni doc che descrive codice modificato ma non è stato aggiornato:

Segnala come nota informativa: "Documentazione potenzialmente stale: [file] — considera `/doc-update`."

---

## Regole Importanti

- **Mai saltare i test.** Se falliscono, stop.
- **Mai force push.** Solo `git push` regolare.
- **Mai chiedere conferma** tranne per review ASK items e bump MINOR/MAJOR.
- **Commit bisectable** — ogni commit = un cambiamento logico.
- **L'obiettivo: l'utente dice `/ship`, vede l'URL della PR.**
