---
description: Review prodotto/architettura di un piano - 3 modalità (EXPANSION/HOLD/REDUCTION)
argument-hint: "[file piano o descrizione] (opzionale)"
---

# Plan Review: Revisione Profonda di un Piano

Review completa di un piano di implementazione con postura da founder/CTO. Tre modalità:
- **EXPANSION** — Sogna in grande. Cosa renderebbe questo 10x migliore?
- **HOLD SCOPE** — Massimo rigore. Rendi il piano a prova di bomba.
- **REDUCTION** — Chirurgo. Minimo viabile che produce valore.

## Target

**$ARGUMENTS** (o piano in corso se non specificato)

---

## Filosofia

Non sei qui per approvare il piano. Sei qui per renderlo straordinario, catturare ogni mina prima che esploda, e assicurare che quando shippa, shippa al massimo standard.

### Prime Directive
1. Zero silent failures. Ogni failure mode deve essere visibile.
2. Ogni errore ha un nome. Non dire "gestisci errori" — nomina l'eccezione specifica.
3. I data flow hanno shadow path. Happy path + nil + empty + error per ogni flusso.
4. Le interazioni hanno edge case. Double-click, navigate-away, slow connection, stale state.
5. L'osservabilita' è scope, non afterthought.
6. I diagrammi sono obbligatori per flussi non banali.
7. Tutto cio' che è deferito va scritto. TODOS o non esiste.

---

## Pre-Review: System Audit

```bash
git log --oneline -30
git stash list
git diff --stat HEAD~10..HEAD 2>/dev/null
```

Leggi CLAUDE.md del progetto e qualsiasi doc di architettura esistente.

Mappa:
- Stato corrente del sistema
- Lavoro in corso (branch, PR aperti)
- Pain point noti rilevanti per questo piano

---

## Step 0: Challenge Nucleare + Selezione Modalità

### 0A. Challenge Premesse
1. È il problema giusto da risolvere? Un framing diverso produrrebbe una soluzione più semplice?
2. Qual è l'outcome reale utente/business? Il piano è il percorso più diretto?
3. Cosa succederebbe se non facessimo nulla?

### 0B. Leverage Codice Esistente
1. Quale codice esistente risolve già parzialmente ogni sotto-problema?
2. Il piano ricostruisce qualcosa che esiste già?

### 0C. Dream State
```
STATO ATTUALE          QUESTO PIANO           IDEALE 12 MESI
[descrivi]     --->    [descrivi delta]  ---> [descrivi target]
```

### 0D. Selezione Modalità

Presenta tre opzioni con AskUserQuestion:

1. **SCOPE EXPANSION** — Il piano è buono ma potrebbe essere grande. Proponi la versione ambiziosa.
2. **HOLD SCOPE** — Lo scope è giusto. Revisiona con massimo rigore.
3. **SCOPE REDUCTION** — Il piano è sovradimensionato. Proponi la versione minima.

Default contestuali:
- Greenfield feature → EXPANSION
- Bug fix / hotfix → HOLD SCOPE
- Refactor → HOLD SCOPE
- Piano che tocca >15 file → suggerisci REDUCTION

**Una volta selezionata la modalità, committati completamente. Non deviare silenziosamente.**

---

## Lenti di Review (dopo accordo su scope)

Le sezioni qui sotto sono **lenti suggerite**, non un template obbligatorio da riempire riga per riga. Scegli quelle pertinenti al piano in esame e approfondiscile con l'intensità che meritano: un refactor tocca architettura e code quality più che deployment; una migrazione DB inverte le priorità; un hotfix magari solo error map e test. Se una lente non aggiunge nulla per questo piano, dillo in una riga e vai avanti. Copri ciò che è rilevante, non ciò che è elencato.

Su ogni issue che emerge, usa il giudizio: **fermati e chiedi (AskUserQuestion) quando l'issue è bloccante o cambierebbe l'approccio**; per gli altri raccogli i rilievi e presentali insieme senza interrompere il flusso a ogni riga. Un issue bloccante = una domanda, mai combinare i bloccanti tra loro.

### 1. Architecture Review

Valuta e diagramma:
- Design complessivo e confini componenti
- Data flow — tutti e 4 i path (happy, nil, empty, error)
- State machine per ogni oggetto stateful
- Coupling prima/dopo
- Caratteristiche di scaling (cosa si rompe a 10x? 100x?)
- Single point of failure
- Scenario di failure in produzione per ogni integration point
- Postura di rollback

**EXPANSION**: Cosa renderebbe questa architettura bella? Non solo corretta — elegante.

Se emerge un issue bloccante o che cambia l'approccio, fermati e chiedi (AskUserQuestion, uno per issue bloccante). Gli altri rilievi annotali e prosegui.

### 2. Error & Rescue Map

Per ogni metodo/servizio/codepath che può fallire:

```
METODO/CODEPATH        | COSA PUO' ANDARE STORTO     | GESTITO?  | UTENTE VEDE
-----------------------|-----------------------------|-----------|-----------
Service#call           | API timeout                 | Si, retry | "Servizio non disponibile"
                       | JSON malformato             | NO ← GAP  | 500 error ← MALE
```

Regole:
- `catch (error)` generico è SEMPRE un smell. Nomina le eccezioni specifiche.
- Ogni errore gestito deve: ritentare con backoff, degradare con messaggio, o ri-lanciare con contesto.
- "Inghiottire e continuare" non è quasi mai accettabile.

Se emerge un issue bloccante o che cambia l'approccio, fermati e chiedi (AskUserQuestion, uno per issue bloccante). Gli altri rilievi annotali e prosegui.

### 3. Security & Threat Model

- Superficie di attacco espansa
- Validazione input per ogni nuovo input utente
- Autorizzazione per ogni nuovo accesso dati
- Segreti e credenziali
- Rischio dipendenze
- Vettori injection (SQL, command, template, LLM prompt)

Se emerge un issue bloccante o che cambia l'approccio, fermati e chiedi (AskUserQuestion, uno per issue bloccante). Gli altri rilievi annotali e prosegui.

### 4. Data Flow & Edge Case Interazione

Per ogni nuovo data flow, ASCII diagram:
```
INPUT → VALIDATION → TRANSFORM → PERSIST → OUTPUT
  │          │            │          │         │
  ▼          ▼            ▼          ▼         ▼
[nil?]   [invalid?]  [exception?] [conflict?] [stale?]
```

Per ogni interazione utente: double-click, navigate-away, timeout, retry while in-flight, zero risultati, 10k risultati.

Se emerge un issue bloccante o che cambia l'approccio, fermati e chiedi (AskUserQuestion, uno per issue bloccante). Gli altri rilievi annotali e prosegui.

### 5. Code Quality

- Organizzazione e struttura moduli
- Violazioni DRY
- Naming quality
- Edge case mancanti
- Over/under-engineering

Se emerge un issue bloccante o che cambia l'approccio, fermati e chiedi (AskUserQuestion, uno per issue bloccante). Gli altri rilievi annotali e prosegui.

### 6. Test Review

Diagramma di TUTTO cio' che il piano introduce di nuovo:

```
NUOVI UX FLOW:       [lista]
NUOVI DATA FLOW:     [lista]
NUOVI CODEPATH:      [lista]
NUOVI BACKGROUND JOB:[lista]
NUOVE INTEGRAZIONI:  [lista]
NUOVI ERROR PATH:    [lista, cross-ref sezione 2]
```

Per ogni item: tipo test, esiste?, happy path, failure path, edge case.

**Test ambition check**: Per ogni feature nuova:
- Quale test ti darebbe fiducia per shippare alle 2 di notte di venerdi'?
- Quale test scriverebbe un QA ostile per rompere questo?

Se emerge un issue bloccante o che cambia l'approccio, fermati e chiedi (AskUserQuestion, uno per issue bloccante). Gli altri rilievi annotali e prosegui.

### 7. Performance

- N+1 query
- Memory usage
- Indici database
- Opportunità caching
- Path lenti (top 3 con p99 stimato)

Se emerge un issue bloccante o che cambia l'approccio, fermati e chiedi (AskUserQuestion, uno per issue bloccante). Gli altri rilievi annotali e prosegui.

### 8. Deployment & Rollout (EXPANSION e HOLD)

- Sicurezza migrazione
- Feature flag necessari?
- Ordine rollout
- Piano rollback esplicito step-by-step
- Finestra di rischio deploy
- Checklist verifica post-deploy

Se emerge un issue bloccante o che cambia l'approccio, fermati e chiedi (AskUserQuestion, uno per issue bloccante). Gli altri rilievi annotali e prosegui.

---

## Output Richiesti

### Sezione "NON in scope"
Lista lavoro considerato e deferito, con motivazione per ogni item.

### Sezione "Cosa esiste già"
Codice/flussi esistenti che risolvono parzialmente sotto-problemi.

### Sezione "Dream state delta"
Dove ci lascia questo piano rispetto all'ideale a 12 mesi.

### Failure Modes Registry
```
CODEPATH | FAILURE MODE | GESTITO? | TEST? | UTENTE VEDE? | LOGGATO?
```
Qualsiasi riga con GESTITO=N, TEST=N, UTENTE VEDE=Silenzioso → **GAP CRITICO**.

### Diagrammi (obbligatori, produci tutti quelli applicabili)
1. Architettura sistema
2. Data flow (inclusi shadow path)
3. State machine
4. Error flow
5. Sequenza deployment
6. Flowchart rollback

### Completion Summary
```
+====================================================================+
|                PLAN REVIEW — COMPLETION SUMMARY                     |
+====================================================================+
| Modalita' selezionata | EXPANSION / HOLD / REDUCTION               |
| System Audit          | [finding chiave]                           |
| Step 0                | [modalita' + decisioni chiave]             |
| Sez. 1 (Arch)        | ___ issue trovati                          |
| Sez. 2 (Errori)      | ___ error path mappati, ___ GAP            |
| Sez. 3 (Sicurezza)   | ___ issue trovati                          |
| Sez. 4 (Data/UX)     | ___ edge case mappati, ___ non gestiti     |
| Sez. 5 (Qualita')    | ___ issue trovati                          |
| Sez. 6 (Test)        | Diagramma prodotto, ___ gap                |
| Sez. 7 (Perf)        | ___ issue trovati                          |
| Sez. 8 (Deploy)      | ___ rischi segnalati                       |
+--------------------------------------------------------------------+
| NON in scope          | scritto (___ item)                         |
| Cosa esiste gia'      | scritto                                    |
| Dream state delta     | scritto                                    |
| Failure modes         | ___ totali, ___ GAP CRITICI               |
| Diagrammi prodotti    | ___ (lista tipi)                           |
| Decisioni irrisolte   | ___ (listate sotto)                        |
+====================================================================+
```

### Decisioni Irrisolte
Se qualsiasi AskUserQuestion non riceve risposta, notalo qui. Mai defaultare silenziosamente.

---

## Come Fare Domande

Per ogni AskUserQuestion:
1. **Re-ground**: Progetto, branch, piano/task corrente (1-2 frasi)
2. **Semplifica**: Spiega il problema in italiano semplice che chiunque capirebbe
3. **Raccomanda**: `RACCOMANDAZIONE: Scegli [X] perché [motivo]`
4. **Opzioni**: A) ... B) ... C) ...

- **Un issue = una AskUserQuestion.** Mai combinare.
- Descrivi il problema concretamente con riferimenti file:linea.
- 2-3 opzioni, incluso "non fare nulla" dove ragionevole.
- Escape hatch: se nessun issue in una sezione, dillo e vai avanti.
