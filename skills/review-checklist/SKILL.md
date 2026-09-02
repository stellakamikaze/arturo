---
name: review-checklist
description: >-
  Aggiunge alla review nativa del diff la checklist pre-landing che il codice da solo non copre:
  completezza strutturale, coerenza con il piano, documentazione, rischi di deploy.
when_to_use: >-
  Usa quando /deep-review o /ship la richiamano, o quando l'utente chiede «è pronto per andare?»,
  «facciamo la review prima del merge». NON per la caccia ai bug di correttezza sul diff: quella è il
  /code-review nativo, da lanciare prima. Segui tutti i passi nell'ordine: non prendere scorciatoie
  basandoti su questa description.
---

# Pre-Landing Review

## Passi

1. Determina il base branch: `gh pr view --json baseRefName -q .baseRefName 2>/dev/null || git symbolic-ref refs/remotes/origin/HEAD 2>/dev/null | sed 's|refs/remotes/origin/||' || echo main`.
2. Lancia il `/code-review` nativo sul diff: bug di correttezza e semplificazioni sono suoi. Sopra il nativo questa checklist aggiunge i principi di review, il giudizio su cosa fixare da soli e le soppressioni.
3. Revisiona `git diff origin/<base-branch>` con i «Principi di review» qui sotto. Per ogni issue cita `file:linea` e suggerisci il fix.
4. Decidi ogni issue con «Cosa fixo da solo vs cosa chiedo», poi filtra il rumore con «Soppressioni».
5. Riporta nel formato qui sotto. Sii conciso: una riga problema, una riga fix, niente preamboli.

### Formato output

```
Pre-Landing Review: N issue (X critici, Y informazionali)

**AUTO-FIXED:**
- [file:linea] Problema → fix applicato

**NEEDS INPUT:**
- [file:linea] Descrizione problema
  Fix raccomandato: suggerimento
```

Se nessun issue: `Pre-Landing Review: Nessun issue trovato.`

---

## Importante

- La caccia ai bug di correttezza sul diff è del `/code-review` nativo: non re-implementare l'enumerazione qui.
- Segnala solo problemi reali, ciascuno con `file:linea`. Salta ciò che va bene.
- Fix in autonomia solo su ciò che è sicuro, meccanico e reversibile; sicurezza, race condition, architettura e comportamento visibile all'utente si chiedono. La linea di confine sta in «Cosa fixo da solo vs cosa chiedo».
- Ciò che è elencato in «Soppressioni» non si segnala, mai.

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
