---
description: Avvia nuovo progetto - orchestratore completo dall'idea al primo commit
argument-hint: <nome-progetto>
---

# Nuovo Progetto

**Workflow orchestratore** per avviare un nuovo progetto: dalla directory vuota al primo commit.
Il valore aggiunto di `/progetto` è il bootstrap (directory + git + commit) e l'orchestrazione delle fasi. Le fasi di analisi NON sono duplicate qui: `/progetto` invoca `/discovery` e `/write-plan` con il contesto raccolto.

## Nome Progetto

**$ARGUMENTS**

---

## FASE 1: Setup Directory

```bash
PROJECTS_BASE="${PROJECTS_BASE:-$HOME/Documents/ClaudeCode}"
# Le env di settings.json sono iniettate verbatim: una tilde iniziale NON viene
# espansa dalla shell. Va espansa a mano, altrimenti mkdir crea una cartella "~".
PROJECTS_BASE="${PROJECTS_BASE/#\~/$HOME}"
mkdir -p "$PROJECTS_BASE/$ARGUMENTS"
cd "$PROJECTS_BASE/$ARGUMENTS"
git init
pwd && ls -la
```

---

## FASE 2: Selezione Modalità

Usa AskUserQuestion:

**Header**: "Complessità progetto"

**Opzioni**:
1. **Light** (1-2 giorni) - "Discovery rapida, piano semplice, build diretto"
2. **Standard** (1-2 settimane) - "Discovery + Scope + Piano strutturato"
3. **Non software** - "Un libro, una ricerca, un corso, un archivio: niente codice"

---

## FASE 3A: Modalità Light

Discovery minimale inline (no `/discovery` completo per progetti da 1-2 giorni). Chiedi:
- "Cosa deve fare questo progetto in 1-2 frasi?"
- "Stack preferito? (es. React+Node, Python+FastAPI)"
- "MVP: quali 2-3 feature essenziali?"

Poi crea `CLAUDE.md` con: Progetto, Stack, MVP Features, Comandi (`npm run dev`, `npm test`).

Crea un task con `TaskCreate` per il setup e uno per ogni feature MVP. Marca il setup `in_progress` con `TaskUpdate`. Salta alla FASE 4.

---

## FASE 3C: Modalità Non software

Per chi non scrive codice: il progetto è una cartella di lavoro con le sue regole. Niente
stack, niente `npm`. Chiedi:
- "Cosa vuoi ottenere, in 1-2 frasi?"
- "Che cosa consegni alla fine? (un testo, una presentazione, una raccolta, un corso…)"
- "Ci sono materiali da cui partire, e dove stanno?"
- "Regole tue per questo lavoro? (tono, lunghezza, fonti, scadenze)"

Poi crea `CLAUDE.md` con: Obiettivo, Cosa si consegna, Materiali (con i percorsi), Regole.
Crea le cartelle che servono davvero (per esempio `materiali/` e `bozze/`), niente di più.
Crea un task con `TaskCreate` per ogni passo concreto emerso. Salta alla FASE 4.

---

## FASE 3B: Modalità Standard

Esegui in sequenza i tre comandi standalone, passando il contesto di fase in fase. NON duplicare i loro template qui.

### 3B.1 Discovery
Esegui `/discovery`. Raccoglie requisiti business, contesto tecnico, scala, prioritizzazione e produce il documento di sintesi (Problema, Criteri di successo, Decisioni tecniche, Scope MVP, Fuori scope).

### 3B.2 Piano
Esegui `/write-plan` usando il documento di discovery. Produce architettura, task ordinati e strategia test.

### 3B.3 Crea Task
Dal piano prodotto da `/write-plan`, crea un task con `TaskCreate` per ogni fase:
- "MVP $ARGUMENTS - Setup"
- "MVP $ARGUMENTS - Foundation"
- ecc.

---

## FASE 4: Commit Iniziale

Aggiungi al staging SOLO i file creati nelle fasi precedenti (CLAUDE.md, package.json, config). Mai `git add .` — elenca i file esplicitamente.

```bash
# Esempio (adatta alla lista reale di file creati):
git add CLAUDE.md package.json
git commit -m "feat($ARGUMENTS): initial project setup"
```

**NON usare Co-Authored-By. NON usare `git add .`.**

---

## FASE 5: Prossimi Passi

```
----------------------------------------------------
 PROGETTO CREATO: $ARGUMENTS
----------------------------------------------------

## Struttura
$PROJECTS_BASE/$ARGUMENTS/
├── CLAUDE.md
└── [package.json / config]

## Task Pronti
[lista task creati con TaskCreate]

## Prossimo Step
Inizia implementazione (`/inizio $ARGUMENTS` per riprendere in sessioni future).

----------------------------------------------------
```

---

## Orchestrazione

`/progetto` fa da collante:
- Bootstrap repo (FASE 1: mkdir + git init) e primo commit (FASE 4) — **valore esclusivo di questo comando**
- Selezione modalità Light/Standard (FASE 2)
- Delega l'analisi ai comandi standalone: `/discovery` → `/write-plan` (Standard) con passaggio di contesto tra fasi
- Logica task (TaskCreate dal piano)

**L'utente chiama solo /progetto, il resto è orchestrato.**

---

## Avvia

Esegui FASE 1: crea directory $PROJECTS_BASE/$ARGUMENTS.
