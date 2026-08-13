---
description: Chiudi sessione lavoro correttamente
argument-hint: "[--full] [note opzionali]"
---

# Fine Sessione

Chiudi la sessione in modo pulito. **Chiusura tipica leggera**; le fasi costose sono
opzionali (flag `--full`) o condizionali (si attivano solo se rilevanti).

**Argomenti / Note utente**: $ARGUMENTS

- `--full` → esegue anche: plugin claude-md, doc-staleness, retro.
- Senza flag → esegue solo il core + le fasi condizionali che risultano rilevanti.

---

## CORE (sempre)

### 1. Stato

```bash
git status --short
git branch --show-current 2>/dev/null
```

Usa `TaskList` per i task pendenti.

### 2. Completezza

Lancia **internamente** l'agente `structural-completeness-reviewer` (cambiamenti integrati?
dead code rimosso? niente a metà?). Poi mini-verify: ricostruisci l'obiettivo della sessione
dalla conversazione e confrontalo con i deliverable prodotti.

Se emergono gap: elencali e chiedi se fixare ora o documentarli nell'handoff come task pendente.
Se tutto coperto: procedi in silenzio.

### 3. Validate

Applica `~/.claude/shared/validation-gate.md` con **mode=quick** (tsc + test + console.log).

- Passa → commit.
- Errori chiari e ripetitivi → skill `~/.claude/skills/autofix/SKILL.md`, loop test-fix-retest (max 3).
- Autofix fallisce o errori ambigui → documenta nell'handoff come task pendente.

### 4. Commit Progetto

Se ci sono modifiche non committate:
1. `git diff --stat` per review
2. Staging **selettivo** (`git add` dei file pertinenti — MAI `git add .` / `-A`)
3. Escludi file sensibili (.env, credentials, temporanei)
4. Commit con messaggio appropriato. **NON usare Co-Authored-By.**

### 5. Handoff + Push

Nome file: `HANDOFF_$(date +%Y-%m-%d_%H-%M).md`.

**Prima di scrivere, rispondi internamente alle 5 domande:**
1. Cosa c'è da fare? (anche cose dette di sfuggita)
2. Cosa è rimasto in sospeso? (decisioni rimandate, dubbi)
3. Cosa si potrebbe fare che non è stato discusso? (migliorie, edge case, tech debt)
4. Ogni item emerso è in `TaskList`? Se manca, crealo con `TaskCreate` ora.
5. I task da sessioni precedenti vanno aggiornati/chiusi?

Template:

```markdown
# Session Handoff - [YYYY-MM-DD] [HH:MM]

## Progetto
- Nome / Branch / Status [in progress|completato|bloccato] / Ultimo commit [hash - msg]

## Cosa stavamo facendo
[Task/feature principale, conciso]

## Decisioni prese
1. [Decisione e motivazione]

## File modificati
[git diff --stat o lista]

## Task Pendenti
Da `TaskList`, tutti i task con status != completed:

| # | Progetto | Priorità | Task | Status | Descrizione |
|---|----------|----------|------|--------|-------------|
| 1 | [nome] | alta | nome-task | in_progress | cosa resta |

Regole: ogni task DEVE avere il Progetto; status `pending|in_progress|blocked`;
priorità `alta|media|bassa`; Descrizione con contesto sufficiente a riprendere senza
rileggere il codice; includi anche task da sessioni precedenti se ancora validi.

## In sospeso (non ancora task)
- [Decisioni rimandate, dubbi]

## Idee emerse (non discusse)
- [Migliorie, edge case, tech debt]

## Prossimi passi
1. [ ] [Azione immediata più importante]

## Riferimenti / Note
- [Link a issue/PR/doc] · [Note utente]
```

Push (l'handoff NON deve restare solo locale):

```bash
git add "$HANDOFF_FILE"
git commit -m "docs: session handoff $(date +%Y-%m-%d)"
if git remote get-url origin >/dev/null 2>&1; then
  git push 2>&1 || echo "Push handoff non riuscito (vedi errore sopra: permessi o rete)"
else
  echo "Nessun remote 'origin' configurato: l'handoff resta locale (ok)."
fi
```

**Mirror cross-machine (se usi la config su più macchine).** Lo store
`~/.claude/data/handoffs/` viaggia col repo config: ogni macchina vede gli handoff
di tutte le altre. Slug = nome progetto in kebab-case (stesso nome usato con `/inizio`).

```bash
SLUG="<slug-progetto>"
HDIR=~/.claude/data/handoffs/"$SLUG"
mkdir -p "$HDIR"
cp "$HANDOFF_FILE" "$HDIR/"
# retention: ultimi 5 (i vecchi restano nella history git)
ls -t "$HDIR"/HANDOFF_*.md 2>/dev/null | tail -n +6 | xargs rm -f 2>/dev/null
```

Poi aggiorna la riga del progetto in `~/.claude/data/handoffs/INDEX.md`
(colonne: Progetto | Ultimo handoff | Data | Stato | Prossimo passo — il "Prossimo passo"
deve essere leggibile senza aprire l'handoff). Il push avviene con il Config Sync della
FASE 6.

### 6. Config Sync (condizionale)

**Solo se `~/.claude` ha modifiche non committate.** Altrimenti salta.

```bash
if [ -n "$(git -C ~/.claude status --porcelain 2>/dev/null)" ]; then
  PREV_DIR="$PWD" && cd ~/.claude && git add settings.json commands/ agents/ hooks/ skills/ shared/ data/handoffs/ package.json README.md 2>/dev/null; git commit -m "chore: session sync $(date +%Y-%m-%d)" 2>/dev/null || true; if git remote get-url origin >/dev/null 2>&1; then git push origin main 2>&1 || echo "Config push non riuscito (vedi errore: serve un remote tuo con accesso in scrittura)"; else echo "Config senza remote 'origin': i commit restano locali (ok). Per sincronizzare tra le tue macchine, configura un tuo repo privato come origin."; fi; cd "$PREV_DIR"
else
  echo "Config Claude: nessuna modifica, skip sync"
fi
```

### 7. Conferma

```
+====================================================================+
|                      SESSIONE CHIUSA                                |
+--------------------------------------------------------------------+
| Commit progetto | [hash o "nessuno"]                               |
| Handoff         | [HANDOFF_*.md]                                   |
| Task pendenti   | [N] (nell'handoff)                               |
| Validate        | [passed / N errori documentati]                  |
| Config sync     | [pushato / nessuna modifica]                     |
| Extra (--full)  | [claude-md/doc/retro o "skip"]                   |
+--------------------------------------------------------------------+
| Riprendi: /inizio [progetto]  ·  sessione esatta: claude -r        |
+====================================================================+
```

---

## OPZIONALI (`--full` o se rilevante)

Esegui queste fasi **solo** se è passato `--full`, oppure quando la condizione indicata è vera.

### A. CLAUDE.md — `--full`, o se la sessione ha prodotto insight duraturi
Plugin `claude-md-management:revise-claude-md` (fallback: leggi, identifica pattern
ripetuti, proponi update). Le modifiche entrano nel commit config della FASE 6.

### B. Doc staleness — `--full`, o se la sessione ha toccato doc/.md
Cross-reference le modifiche con i `.md` del repo. Se un doc descrive codice modificato ma non
aggiornato: segnalalo nell'handoff e suggerisci `/doc-update` alla prossima sessione.

### C. Retro — `--full`, o se la sessione ha 5+ commit / lavoro significativo
Suggerisci: "Hai fatto parecchio lavoro. Considera `/retro`."

---

## Avvia

Esegui il CORE. Attiva le fasi OPZIONALI solo con `--full` o quando la loro condizione è vera.
