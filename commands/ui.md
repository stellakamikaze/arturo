---
description: Sviluppo frontend/UI con design thinking
argument-hint: <nome-progetto> [componente]
---

# Sviluppo UI

**Workflow orchestratore** per sviluppo frontend, UI/UX e componenti grafici.

## Target

**$ARGUMENTS**

---

## FASE 1: Setup Contesto

```bash
PB="${PROJECTS_BASE:-$HOME/Documents/ClaudeCode}"; PB="${PB/#\~/$HOME}"
PROJECT_PATH=""
for dir in "./$ARGUMENTS" "$PB/$ARGUMENTS" "$HOME/Documents/ClaudeCode/$ARGUMENTS" "$HOME/Documents/$ARGUMENTS" "$HOME/Projects/$ARGUMENTS" "$HOME/$ARGUMENTS"; do
  [ -d "$dir" ] && PROJECT_PATH="$dir" && break
done

if [ -z "$PROJECT_PATH" ]; then
  echo "Progetto non trovato: $ARGUMENTS"
else
  echo "Progetto: $PROJECT_PATH"
  cd "$PROJECT_PATH"
fi
```

Leggi `CLAUDE.md` se esiste.

---

## FASE 2: Analisi Stack

```bash
cat package.json 2>/dev/null | grep -E '"(react|vue|svelte|next|nuxt|angular)"'
ls tailwind.config.* 2>/dev/null && echo "Tailwind: attivo"
find . -name "*.tsx" -o -name "*.vue" -o -name "*.svelte" 2>/dev/null | grep -v node_modules | wc -l
```

---

## FASE 3: Design Principles + UI Reference

Carica la skill `ui-reference` per checklist concrete (8px grid, type scale, dark mode hex, gotchas Tailwind/Safari).

**ATTIVI per questa sessione:**

```
----------------------------------------------------
 FRONTEND DESIGN PRINCIPLES
----------------------------------------------------

Typography: Font distintivi (NO Inter, Roboto, Arial)
Color: Palette coesa con CSS variables
Motion: Micro-interazioni, staggered reveals
Layout: Asimmetria, overlap, rottura griglia
Background: Profondità (gradient, noise, pattern)

VIETATO:
- Font generici
- Purple gradients su bianco
- Layout cookie-cutter
- Nero puro (#000) / bianco puro (#fff) in dark mode

----------------------------------------------------
```

---

## FASE 4: Review UI Esistente

Lancia **internamente** agente `ui-ux-consultant`:

**Accessibilità (WCAG)**:
- Contrasto colori
- Focus indicators
- ARIA labels
- Keyboard navigation

**Consistenza**:
- Spacing system
- Typography scale
- Color usage

**Performance**:
- Bundle size componenti
- Render optimization

---

## FASE 5: Carica Task UI

Usa `TaskList` per vedere task UI aperti.

---

## FASE 6: Dashboard

```
----------------------------------------------------
 SVILUPPO UI: $ARGUMENTS
----------------------------------------------------

## Stack
- Framework: [React/Vue/Svelte/Next/...]
- Styling: [Tailwind/CSS Modules/...]
- Componenti: [N] file

## UI Review
- Accessibilità: [issues trovati]
- Consistenza: [issues trovati]

## Task UI Disponibili
[lista task]

----------------------------------------------------
```

---

## FASE 7: Selezione Lavoro

Usa AskUserQuestion:

**Header**: "Cosa vuoi sviluppare?"

**Opzioni**:
1. **Task esistente** - "Lavora su [primo task UI]"
2. **Fix accessibilità** - "Correggi issue da review"
3. **Nuovo componente** - "Crea componente da zero"
4. **Redesign** - "Ridisegna componente esistente"

---

## FASE 8: Design Thinking (prima di codificare)

Per ogni componente:

1. **Purpose**: Che problema risolve? Chi lo usa?
2. **Tone**: Scegli estetica (minimal, brutalist, organic, luxury, playful...)
3. **Differentiation**: Cosa lo rende MEMORABILE?

---

## FASE 9: Verifica Post-Sviluppo

Lancia **internamente** di nuovo agente `ui-ux-consultant`:
- Conferma fix accessibilità
- Conferma consistenza mantenuta
- Nessuna regressione

---

## Orchestrazione

Questo workflow esegue automaticamente:
- Review UI/UX (ui-ux-consultant agent)
- Performance componenti
- Frontend-design principles
- Logica task (TaskCreate/TaskUpdate)

**L'utente chiama solo /ui, il resto è automatico.**

---

## Avvia

Esegui FASE 1: localizza progetto e naviga alla directory.
