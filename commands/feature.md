---
description: Workflow completo per sviluppo nuova feature con review integrata
argument-hint: "[nome feature] (opzionale)"
---

# Nuova Feature

Workflow completo per sviluppare una nuova feature con qualità integrata a ogni passo.

## Contesto

Feature da sviluppare: **$ARGUMENTS**

---

## Obiettivo

Portare la feature da idea a codice committato con qualità integrata. Non c'è una pipeline fissa: dimensiona il percorso alla forma del task. Una modifica di due righe non ha bisogno dello stesso apparato di una feature full-stack. Usa il tuo giudizio per decidere quali momenti servono, in che ordine, e quanto approfondire ciascuno — l'importante è arrivare a un risultato solido, non spuntare una checklist.

## Com'è fatto un buon risultato

- Lo **scope è chiaro** prima di scrivere codice: sai qual è il problema giusto, cosa esiste già, e qual è la versione più piccola che produce valore. Per feature non banali passa da `/scope`; per task piccoli basta ragionarci a voce.
- Gli **errori sono previsti, non scoperti in produzione**: i codepath che possono fallire (input invalido, auth mancante, timeout, risposte malformate, constraint violation) hanno una gestione pensata, e i data flow coprono i shadow path che contano (happy, nil, empty, error). Mappa questo con la profondità che il task richiede.
- Il **codice è verificato**: la scelta tra TDD, test-after o esplorazione dipende dal task. Dove ha senso, delega la verifica a subagent in parallelo (`test-runner`, `bug-finder`) invece di farla in serie.
- La **sicurezza** dei nuovi endpoint/input/data access è considerata: input validato, autorizzazione corretta, niente injection, niente segreti hardcoded. Se emergono dubbi, segnalali prima di committare.
- L'**integrazione architetturale** regge: per feature che toccano più moduli o layer, `/deep-review --arch` cattura accoppiamento, scaling e failure modes. Per modifiche isolate spesso è overkill.

## Rail non negoziabili

- **Test e type-check verdi PRIMA del commit.** Non committare con la suite rossa o `tsc --noEmit` in errore. Questo gate non salta mai, qualunque sia il percorso scelto.
- **Il commit passa da `/commit`** (messaggio auto-generato; commit bisectable se la feature tocca aree diverse). **NON usare Co-Authored-By.**
- Se la feature tocca 3+ layer o moduli indipendenti, **valuta Agent Teams** (worker in worktree isolati, uno per layer) e proponilo all'utente prima di partire — coordinamento reale, non parallelismo forzato.

## Chiusura

A commit fatto, suggerisci il prossimo passo pertinente:
- Se pronto per merge: `/ship`
- Se serve QA manuale: segnala cosa testare
- Se doc impattati: `/doc-update`

## Avvia

Parti dallo scope: chiarisci il problema giusto e il minimo viabile, poi lascia che sia la forma della feature a dettare il resto.
