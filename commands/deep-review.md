---
description: Review pre-landing custom con 3 modalità. Default = valore aggiunto (UI/UX Fix-First, AI-slop, doc-staleness, review-checklist) delegando bug+simplify al /code-review nativo. --arch = data flow/failure modes/scaling. --codebase = keep/remove/refactor. Per review di PR GitHub usa il /review nativo; per soli bug sul diff usa /code-review nativo.
argument-hint: '[--arch | --codebase] [path o "changes"]'
---

# Deep Review

Review orchestratore custom. Tre modalità:

- **default** (nessun flag) — review pre-landing di branch/diff. **Delega** bug-finding e simplification al `/code-review` nativo; aggiunge solo il valore custom: UI/UX multi-agente Fix-First, AI-slop, doc-staleness, `review-checklist`.
- **`--arch`** — review architetturale: data flow, failure modes, scaling, diagrammi.
- **`--codebase`** — review codebase: keep/remove/refactor + mappa progetto.

> Per review di **PR GitHub** esiste il `/review` **nativo**. Per soli **bug/semplificazioni sul diff** esiste il `/code-review` **nativo** (che questa modalità default invoca).

**Target**: `$ARGUMENTS` (rimossi i flag) — o modifiche git se non specificato.

---

## FASE 0: Rileva Base Branch e Modalità

```bash
BASE=$(gh pr view --json baseRefName -q .baseRefName 2>/dev/null || gh repo view --json defaultBranchRef -q .defaultBranchRef.name 2>/dev/null || echo "main")
BRANCH=$(git branch --show-current 2>/dev/null)
echo "BASE: $BASE | BRANCH: $BRANCH"
```

Determina la modalità dal primo argomento (`--arch`, `--codebase`, altrimenti default). Il resto di `$ARGUMENTS` è il target (path, o `changes`/vuoto = diff git).

Salta alla sezione corrispondente.

---

# MODALITÀ DEFAULT — Review Pre-Landing

## FASE 1: Bug + Simplify (delega al nativo)

**Invoca la skill nativa `/code-review`** sul diff corrente — è la fonte di verità per bug di correttezza e semplificazioni. Non reimplementare bug-hunting o simplification qui.

- `/code-review` con effort adeguato (medium default; high se diff grande o critico).
- Riporta i suoi finding nella sintesi finale, non duplicarli.

## FASE 2: Checklist Review (Fix-First)

Leggi `~/.claude/skills/review-checklist/SKILL.md` e applica la checklist al diff.

```bash
git fetch origin $BASE --quiet 2>/dev/null
git diff origin/$BASE 2>/dev/null | head -500
```

Segui la skill: Pass 1 (critici), Pass 2 (informazionali), Fix-First Heuristic.

- **AUTO-FIX** (meccanico): applica, output una riga `[AUTO-FIXED] [file:linea] Problema → fix`.
- **ASK** (serve giudizio): accumula, presenta in UNA AskUserQuestion alla fine.

> Nota: la skill copre già SQL/data safety, dead code, magic numbers, test gap. Non ridondare col `/code-review` — se un finding compare in entrambi, cita una volta sola.

## FASE 3: UI/UX + AI Slop (se frontend)

Se il target include `.tsx`, `.vue`, `.svelte`, `.css`, lancia **in parallelo** (singolo messaggio):

1. Agente `ui-ux-consultant` — accessibilità WCAG, contrasto, keyboard nav, touch target.
2. AI Slop Detection (skill `ui-reference`): segnali di UI generata a stampino, di default e senza intenzione. Esempi non esaustivi: gradient viola/indaco, grid 3-colonne feature, icone in cerchi, centrato ovunque, border-radius bubbly, blob/wavy divider, emoji come design, border-left colorato, copy hero generica, ritmo cookie-cutter — più qualsiasi altro tell che riconosci.

```
## UI/UX
| Issue | WCAG | File | Fix | AI Slop? |
|-------|------|------|-----|----------|
| Contrasto basso | AA | Button.tsx | Aumentare ratio | No |
```

## FASE 4: Doc Staleness

```bash
find . -maxdepth 2 -name "*.md" -not -path "./.git/*" -not -path "./node_modules/*" 2>/dev/null | head -10
```

Per ogni doc che descrive codice modificato ma NON aggiornato in questo branch: segnala come nota. Suggerisci `/doc-update` se ci sono doc stale.

## FASE 5: Sintesi + Task

```
+====================================================================+
|                    DEEP REVIEW (default)                           |
+====================================================================+
| /code-review   | N bug, M semplificazioni (dal nativo)             |
| Checklist      | N issue (X auto-fixed, Y da confermare)           |
| UI/UX          | N issue (se frontend) | AI Slop: [Si/No]         |
| Doc Staleness  | N file potenzialmente stale                       |
+--------------------------------------------------------------------+

## Priorità Intervento
### CRITICI (fix immediato)   ### ALTI (fix presto)   ### MEDI (backlog)
```

Se issue critici/alti → `TaskCreate` per ognuno. Prossimi passi: fix applicati → `/commit`; issue ASK aperti → risolvi poi `/commit`; doc stale → `/doc-update`; shipping → `/ship`.

---

# MODALITÀ `--arch` — Review Architettura

Review architetturale con diagrammi data flow, failure modes e scaling.

Target: path forniti, o modifiche git (staged > unstaged).

Lancia agente `architecture-reviewer` — Separation of Concerns, SOLID, Coupling/Cohesion, scalabilità, type design, invarianti.

## Checklist

**1. Separation of Concerns** — confini tra layer, leaking abstraction, coesione, coupling.
**2. SOLID** — Single Responsibility, Open/Closed, Dependency Inversion.

**3. Data Flow & Shadow Paths** — per ogni flow significativo, diagramma ASCII:
```
INPUT ──▶ VALIDATION ──▶ TRANSFORM ──▶ PERSIST ──▶ OUTPUT
  │            │              │            │           │
  ▼            ▼              ▼            ▼           ▼
[nil?]    [invalid?]    [exception?]  [conflict?]  [stale?]
[empty?]  [too long?]   [timeout?]    [dup key?]   [partial?]
```
Per ogni nodo: cosa succede su ogni shadow path? È testato?

**4. Failure Modes** — per ogni integration point / codepath critico:
```
CODEPATH      | FAILURE MODE        | GESTITO? | TEST? | UTENTE VEDE?
API ext call  | Timeout 30s         | Si       | Si    | "Riprova"
              | Response malformata | No ← GAP | No    | Crash silenzioso
```
Riga con GESTITO=No + UTENTE VEDE=Silenzioso/Crash → **GAP CRITICO**.

**5. Scaling & Resilience** — cosa si rompe a 10x? a 100x? Async per long-running? N+1? Servizi stateless?
**6. Rollback Posture** — procedura se shippa e rompe (revert/flag/migration), tempo, rischio data loss.
**7. Security Architecture** — auth boundaries, data access (user A → dati user B?), API surface nuova, segreti in env.

## Report

```
+====================================================================+
|                   ARCHITECTURE REVIEW                              |
+====================================================================+
## Strengths           [pattern validi]
## Critical Risks      | # | Area | File:Linea | Problema | Fix |
## Improvements        | # | Area | File:Linea | Problema | Fix |
## Data Flow Diagrams  [ASCII sopra]
## Failure Modes       [tabella sopra]
## Scaling             10x: ... | 100x: ...
## Rollback            procedura | tempo | data loss si/no
+====================================================================+
```

---

# MODALITÀ `--codebase` — Review Codebase

Workflow guidato per decidere cosa tenere, rimuovere, refactorare. Target: path fornito o directory corrente. Presenta i risultati fase per fase.

**Fase 1 — Inventory** (usa agenti Explore): struttura/layout, stack e dipendenze, metriche (file, LOC, coverage), entry point, design system se frontend (font, palette, componenti).

**Fase 2 — Health Scoring**: valuta lo stato di salute lungo queste dimensioni — Architettura, Test Coverage, Sicurezza, Performance, UI/UX, Code Quality, Documentation, Dependencies. I pesi indicativi sotto sono una guida al *peso relativo* tipico (architettura e sicurezza pesano più delle dipendenze), non un'aritmetica da eseguire: usa il giudizio per stabilire quali dimensioni contano davvero per *questo* progetto e alza/abbassa di conseguenza.

| Categoria | Peso indic. | | Categoria | Peso indic. |
|---|---|---|---|---|
| Architettura | ~20% | | UI/UX | ~10% |
| Test Coverage | ~15% | | Code Quality | ~15% |
| Sicurezza | ~15% | | Documentation | ~10% |
| Performance | ~10% | | Dependencies | ~5% |

Sintetizza in un grado complessivo — A (eccellente) / B (buono) / C (accettabile) / D (fragile) / F (critico) — motivandolo, non calcolandolo alla cifra.

**Fase 3 — Keep**: pattern validi, codice testato, core business logic, integrazioni funzionanti. Per ognuno: perché tenerlo.

**Fase 4 — Remove**: lancia agente `bug-finder` (dead code, non raggiungibile, silent failures, error swallowing). Identifica: dead code, dipendenze inutilizzate, feature incomplete, duplicazioni, legacy deprecated.

**Fase 5 — Refactor**: lancia **in parallelo** agente `architecture-reviewer` (SOLID, coupling, scaling, type design) + ricerca semplificazioni (over-abstraction, complessità inutile). Prioritizza: violazioni SOLID, code smell, accoppiamento, sicurezza, performance (N+1, memory leak), type design deboli.

**Fase 5b — AI Slop Audit (se frontend)**: cerca segnali di UI generata "a stampino", di default e senza intenzione. Esempi non esaustivi da cui partire: gradient viola/indaco, grid 3-colonne feature, icone in cerchi, centrato ovunque, border-radius bubbly, blob/wavy divider, emoji come design, border-left colorato, copy hero generica, ritmo cookie-cutter. Aggiungi qualsiasi altro tell che riconosci. → **Score A-F** motivato.

**Fase 5c — Security Audit**: per ogni entry point — input validato/sanitizzato? autorizzazione (user A → dati user B)? injection (SQL/XSS/command)? segreti hardcoded? CVE note?

**Fase 6 — Continue**: quick wins (<30 min), priorità media, lungo termine.

## Output

```
+====================================================================+
|              CODEBASE REVIEW: [Nome Progetto]                      |
+====================================================================+
| Stack / Size / Health [grade] / AI Slop [grade] / Security [N vuln]|
+====================================================================+
## Keep       - [item] - [perché]
## Remove     - [ ] [item] - [impatto]
## Refactor   | Priorità | Area | Problema | Soluzione |
## Quick Wins (< 30 min)   1. [ ] ...
## Next Steps 1. immediata  2. breve  3. lungo termine
```

Comandi consigliati: `/debug` (bug approfonditi), `/deep-review --arch` (architettura dettagliata), `/plan-review` + `/write-plan` (pianificare refactoring), `/ship` (shippare fix).

---

## Avvia

Esegui FASE 0: rileva base branch, determina modalità e target, poi salta alla sezione corrispondente.
