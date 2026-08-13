---
name: review-checklist
description: Checklist strutturata per pre-landing review - usata da /review e /ship
---

# Pre-Landing Review

## Come usarla

Per la caccia ai bug di correttezza sul diff, **delega al `/code-review` nativo** — non re-implementare l'enumerazione qui. Questa skill aggiunge valore sopra il nativo: i principi di review, il giudizio su cosa fixare da soli vs cosa chiedere, e le soppressioni per ridurre il rumore.

Determina il base branch: usa `gh pr view --json baseRefName -q .baseRefName 2>/dev/null || git symbolic-ref refs/remotes/origin/HEAD 2>/dev/null | sed 's|refs/remotes/origin/||' || echo main`. Revisiona il `git diff origin/<base-branch>`. Sii specifico — cita `file:linea` e suggerisci fix. Salta ciò che va bene. Segnala solo problemi reali.

**Formato output:**

```
Pre-Landing Review: N issue (X critici, Y informazionali)

**AUTO-FIXED:**
- [file:linea] Problema → fix applicato

**NEEDS INPUT:**
- [file:linea] Descrizione problema
  Fix raccomandato: suggerimento
```

Se nessun issue: `Pre-Landing Review: Nessun issue trovato.`

Sii conciso. Per ogni issue: una riga problema, una riga fix. Niente preamboli.

---

## Principi di review

Ordina per rischio, non per categoria. Dai la massima severità a ciò che può corrompere dati o comportarsi in modo non deterministico; il resto è informazionale ma comunque azionato.

- **Safety dei dati e della concorrenza in cima.** SQL/query non parametrizzate, pattern check-then-set che dovrebbero essere atomici, transizioni di stato senza guardia (`WHERE old_status = ?`), XSS su dati utente. Qui l'asticella del dubbio è bassa: se sospetti, segnala.
- **Fiducia zero sull'input al confine.** Output LLM o input utente scritti in DB / usati direttamente senza validazione di formato o shape.
- **Completeness sui valori nuovi.** Quando il diff introduce un nuovo valore enum / stato / costante, **traccialo attraverso ogni consumer** (leggi, non solo grep, chi switcha/filtra/mostra quel valore): allowlist, catene `case`/`if-else`, branch di default. È l'errore che il nativo può mancare perché richiede di seguire il valore fuori dal diff.
- **Coerenza e residui.** Side effect dimenticati su un branch, log che dichiarano azioni skippate condizionalmente, dead code, commenti/CHANGELOG/versioni che descrivono un comportamento ormai cambiato.
- **Costo nascosto lato view/query.** N+1 (include/populate mancante), lookup O(n*m) in loop di rendering, filtri client-side che dovrebbero essere `WHERE`, `<style>` inline ri-parsati a ogni render.

Questi sono esempi di dove guardare, **non una lista esaustiva** né una griglia da spuntare: se un problema reale non rientra in nessuno di questi punti, segnalalo comunque.

---

## Cosa fixo da solo vs cosa chiedo

Guida di giudizio, non una matrice rigida.

- **Fixa in autonomia** ciò che è sicuro, meccanico e reversibile: dead code, N+1 evidenti, commenti stale, magic number → costante nominata, validazione output LLM mancante, mismatch versione/path, style inline, lookup O(n*m). In breve: se un senior lo applicherebbe senza discutere.
- **Chiedi** per ciò che tocca scope, architettura o comportamento: scelte di design, sicurezza (auth/XSS/injection), race condition, completeness enum, rimozione di funzionalità, fix ampi, qualsiasi cambiamento visibile all'utente. In breve: se ingegneri ragionevoli potrebbero dissentire, o se stai decidendo *cosa* fare (non solo *come*).

---

## Soppressioni — NON segnalare

- "X è ridondante con Y" quando la ridondanza è innocua e aiuta la leggibilità
- "Aggiungi commento che spiega perché questa soglia" — le soglie cambiano, i commenti marciscono
- "Questa assertion potrebbe essere più stretta" quando già copre il comportamento
- Suggerire cambiamenti solo per consistenza
- Regex che non gestisce edge case quando l'input è vincolato
- No-op innocui
- QUALSIASI cosa già affrontata nel diff che stai revisionando
