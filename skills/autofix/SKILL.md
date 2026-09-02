---
name: autofix
description: >-
  Corregge in autonomia test falliti, errori TypeScript e problemi di lint con un ciclo
  test-fix-retest, e si ferma da sola dopo tre giri documentando cosa resta.
when_to_use: >-
  Usa quando i test o il type-check sono rossi e l'utente dice «sistema i test», «fai passare la
  build», «autofix», o quando /fine e /ship trovano il gate di validazione rosso. NON per bug di
  logica descritti dall'utente senza un test che li dimostri (lì serve /debug) e non per riscrivere i
  test perché passino. Segui tutti i passi nell'ordine: non prendere scorciatoie basandoti su questa
  description.
---

# /autofix — Correzione Autonoma Test / TS / Lint

## Passi

Lavora senza fare domande e decidi col miglior giudizio: l'unica eccezione è il blocco totale descritto nei Rail. Niente pipeline rigida, il ciclo di debug è quello nativo del modello guidato dai passi qui sotto.

1. **Cattura lo stato reale prima di toccare nulla.** Esegui i check che il progetto espone (test, `tsc --noEmit`, lint — usa i comandi effettivi del repo, non assumerli) e leggi l'output vero. Se è già tutto verde, riporta "Nessun problema trovato" e termina.
2. **Diagnosi prima del fix.** Per ogni fallimento: leggi il test (cosa si aspetta) e il sorgente sotto test (perché fallisce). Trova la root cause — bug nel sorgente o aspettativa/mock obsoleto nel test — prima di modificare.
3. **Isola il fix.** Una causa alla volta, modifica minimale e mirata, niente refactoring opportunistico. Preferisci correggere il sorgente; il test si tocca solo nei casi ammessi dai Rail.
4. **Verifica presto e vicino.** Dopo ogni fix riesegui il check più stretto che lo copre (il singolo file/test), non l'intera suite ogni volta.
5. **Giro completo alla fine.** Rilancia tutti i check del progetto (`shared/validation-gate.md`, mode `full`) per scovare regressioni, poi scrivi il report.

## Rail (non negoziabili)

- **Non dichiarare "fatto" finché i check non passano davvero.** Lo stato finale si basa sull'output reale di un giro completo (test + `tsc --noEmit` verde a 0 errori + lint), non sulla tua aspettativa. Se restano fallimenti irrisolti, dillo esplicitamente.
- **Mai modificare un test che passa.** Un test che fallisce si tocca solo se è lui a essere sbagliato (aspettativa o mock obsoleto), mai per farlo diventare verde.
- **Niente regressioni.** Se un fix rompe qualcosa che prima passava, revertilo e ripensa la diagnosi invece di accumulare pezze.
- **Anti-loop.** Se sullo stesso fallimento hai già provato più approcci genuinamente diversi senza risultato, STOP su quel punto: non insistere con l'ennesima variante. Annotalo come irrisolto con cosa hai provato e perché, e passa oltre (o, se blocca tutto, fermati e chiedi). La regola è "cambia strategia, non ritenta la stessa" — il numero esatto di tentativi è indicativo, il segnale è che stai girando a vuoto.
- **Non committare.** Il commit appartiene al chiamante (`/fine`, `/commit`, utente).
- **Non ignorare errori.** Ogni fallimento va diagnosticato, non silenziato.

## Report finale

Riassumi conciso: cosa era rotto, root cause, fix applicato, ed eventuali punti lasciati irrisolti (con i tentativi fatti). Chiudi con lo stato reale: TUTTO VERDE oppure PROBLEMI RESIDUI (quali). Se hai modificato dei test, segnalalo esplicitamente.
