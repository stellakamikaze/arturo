---
description: Protocollo debug - disciplina diagnostica, poi delega la meccanica al debugging nativo
argument-hint: "[file/descrizione bug] (opzionale)"
---

# Debug

**Target**: $ARGUMENTS (o le git changes correnti).

Questo comando impone la **disciplina diagnostica**. La meccanica sistematica
(ispezione, ipotesi iterate, bisect, fix) la esegue il debugging nativo di Claude Code
— qui NON la riscriviamo.

---

## Prima di ipotizzare — raccogli i fatti (obbligatorio)

Non partire dalla prima ipotesi. Chiedi all'utente, se non già chiaro:

1. **Errore esatto** — messaggio/stack trace testuale, non parafrasato.
2. **Behavior atteso** vs osservato.
3. **Cosa ha già escluso** — se dà context negativo ("NON è X"), rispettalo e cerca altrove.
4. **Riproduzione** — passi, input, condizioni.

Se il bug sembra di ambiente (install/auth/config Claude Code, non codice del progetto):
`claude doctor` e fermati lì.

---

## Diagnosi prima del fix

Esponi l'ipotesi in **2-3 bullet** (causa sospetta + come la testeresti) e attendi conferma
prima di toccare il codice. Ragiona sui 4 path del data flow coinvolto: happy / nil / empty /
error — il bug vive quasi sempre in uno shadow path non gestito.

Poi lascia lavorare il debugging nativo: ispezione, test dell'ipotesi, `git bisect` se è una
regressione, fix minimo con test che riproduce.

---

## Regole invalicabili

- **Max 3 tentativi** sullo stesso errore. Se 3 approcci diversi falliscono → STOP, il problema
  richiede un cambio di strategia, non un quarto tentativo. Chiedi all'utente.
- **Fix minimo**: solo la correzione, niente refactoring o "miglioramenti" a lato.
- **Commit selettivo** (`git add` dei file toccati, mai `.`/`-A`), messaggio `fix:` con root cause
  in una riga. NON usare Co-Authored-By.
- Per bug significativi ricorrenti: valuta una riga in `## Errori Comuni` del CLAUDE.md di progetto
  ("NON fare X — causa Y").

---

## Avvia

Raccogli i fatti (errore esatto, atteso, cosa escluso). Poi esponi l'ipotesi in 2-3 bullet
e attendi conferma prima di modificare codice.
