---
name: autofix
description: Loop autonomo test-fix-retest - corregge test falliti senza intervento umano
---

# Autofix: Correzione Autonoma Test / TS / Lint

Diagnostica e corregge test falliti, errori TypeScript e problemi lint in autonomia, usando il ciclo di debug del modello. Non chiede domande durante l'esecuzione — usa best judgment. Non re-implementa una pipeline rigida: si appoggia al debugging agentico nativo, guidato dai principi qui sotto.

## Principi

1. **Cattura lo stato reale prima di toccare nulla.** Esegui i check che il progetto espone (test, `tsc --noEmit`, lint — usa i comandi effettivi del repo, non assumerli) e leggi l'output vero. Se è già tutto verde, riporta "Nessun problema trovato" e termina.
2. **Diagnosi prima del fix.** Per ogni fallimento: leggi il test (cosa si aspetta) e il sorgente sotto test (perché fallisce). Trova la root cause — bug nel sorgente o aspettativa/mock obsoleto nel test — prima di modificare.
3. **Isola il fix.** Una causa alla volta, modifica minimale e mirata, niente refactoring opportunistico. Preferisci correggere il sorgente; tocca il test solo se è lui a essere sbagliato, e non modificare mai un test che passa.
4. **Verifica presto e vicino.** Dopo ogni fix riesegui il check più stretto che lo copre (il singolo file/test), non l'intera suite ogni volta. Alla fine fai un giro completo per scovare regressioni.
5. **Niente regressioni.** Se un fix rompe qualcosa che prima passava, revertilo e ripensa la diagnosi invece di accumulare pezze.

## Rail (non negoziabili)

- **Non dichiarare "fatto" finché i check non passano davvero.** Lo stato finale si basa sull'output reale di un giro completo (test + `tsc --noEmit` verde a 0 errori + lint), non sulla tua aspettativa. Se restano fallimenti irrisolti, dillo esplicitamente.
- **Anti-loop.** Se sullo stesso fallimento hai già provato più approcci genuinamente diversi senza risultato, STOP su quel punto: non insistere con l'ennesima variante. Annotalo come irrisolto con cosa hai provato e perché, e passa oltre (o, se blocca tutto, fermati e chiedi). La regola è "cambia strategia, non ritenta la stessa" — il numero esatto di tentativi è indicativo, il segnale è che stai girando a vuoto.
- **Non committare.** Il commit appartiene al chiamante (`/fine`, `/commit`, utente).
- **Non ignorare errori.** Ogni fallimento va diagnosticato, non silenziato.

## Report finale

Riassumi conciso: cosa era rotto, root cause, fix applicato, ed eventuali punti lasciati irrisolti (con i tentativi fatti). Chiudi con lo stato reale: TUTTO VERDE oppure PROBLEMI RESIDUI (quali). Se hai modificato dei test, segnalalo esplicitamente.
