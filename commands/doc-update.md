---
description: Aggiornamento documentazione post-ship - staleness check cross-doc
argument-hint: (nessun argomento necessario)
allowed-tools: Bash(git:*), Bash(gh:*)
---

# Document Update: Aggiornamento Documentazione Post-Ship

Workflow che gira **dopo `/ship`** o dopo modifiche significative. Assicura che ogni file di documentazione sia accurato e aggiornato.

---

## Fermarsi SOLO per:
- Cambiamenti narrativi rischiosi (filosofia, sicurezza, rimozioni, riscritture grandi)
- Nuovi TODO da aggiungere
- Contraddizioni cross-doc narrative

## NON fermarsi per:
- Correzioni fattuali dal diff
- Aggiungere item a tabelle/liste
- Aggiornare path, conteggi, versioni
- Fixare riferimenti stale
- Marcare TODO completati

## MAI fare:
- Sovrascrivere o rigenerare entry CHANGELOG — solo polish di voce
- Rimuovere intere sezioni da documenti

---

## Step 1: Pre-flight & Analisi Diff

```bash
BASE=$(gh pr view --json baseRefName -q .baseRefName 2>/dev/null || gh repo view --json defaultBranchRef -q .defaultBranchRef.name 2>/dev/null || echo "main")
git diff $BASE...HEAD --stat
git log $BASE..HEAD --oneline
git diff $BASE...HEAD --name-only
```

Scopri tutti i file di documentazione:
```bash
find . -maxdepth 2 -name "*.md" -not -path "./.git/*" -not -path "./node_modules/*" -not -path "./.planning/*" -not -path "./.context/*" | sort
```

Classifica le modifiche: nuove feature, comportamento cambiato, funzionalita' rimossa, infrastruttura.

---

## Step 2: Audit Per-File

Per ogni file documentazione, leggi e cross-referenzia con il diff:

**README.md:**
- Descrive tutte le feature visibili nel diff?
- Istruzioni install/setup consistenti?
- Esempi e usage ancora validi?

**CLAUDE.md / istruzioni progetto:**
- Struttura progetto corrisponde al file tree reale?
- Comandi e script listati sono accurati?
- Istruzioni build/test matchano package.json?

**Qualsiasi altro .md:**
- Leggi il file, determina scopo e audience
- Cross-referenzia con il diff per contraddizioni

Classifica aggiornamenti necessari come:
- **Auto-update** — Correzioni fattuali chiare dal diff
- **Ask user** — Cambiamenti narrativi, rimozione sezioni, riscritture grandi

---

## Step 3: Applica Auto-Update

Fai tutte le correzioni fattuali chiare con Edit tool.

Per ogni file modificato, output una riga che descrive **cosa specificamente è cambiato**.

---

## Step 4: Chiedi per Cambiamenti Rischiosi

Per ogni update rischioso, AskUserQuestion con:
- Contesto: progetto, branch, quale doc, cosa stiamo revisionando
- La decisione specifica
- `RACCOMANDAZIONE: Scegli [X] perché [motivo]`
- Opzioni incluso C) Skip — lascia com'è

---

## Step 5: Consistency Cross-Doc

Dopo l'audit individuale, pass di consistenza cross-doc:

1. La lista feature del README corrisponde al CLAUDE.md?
2. L'architettura descritta corrisponde al codice?
3. La versione nel CHANGELOG corrisponde al VERSION file?
4. **Discoverability**: Ogni file doc è raggiungibile da README o CLAUDE.md? Se no, segnala.
5. Contraddizioni tra documenti? Auto-fix per fatti, AskUserQuestion per narrativa.

---

## Step 6: Commit & Output

```bash
git status --short
```

Se nessun file doc modificato: "Tutta la documentazione è aggiornata." e esci.

Se modifiche:
1. Stage file doc per nome (mai `git add -A`)
2. Commit: `docs: update project documentation`
3. Push: `git push`

**Summary finale:**

```
Documentazione:
  README.md       [stato] ([dettagli])
  CLAUDE.md       [stato] ([dettagli])
  CHANGELOG.md    [stato] ([dettagli])
  ...
```

Dove stato è: Updated, Current, Voice polished, Skipped, Not found.
