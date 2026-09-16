---
description: Scarica e applica l'ultima versione di Arturo, poi racconta cosa è cambiato
argument-hint: "(nessuno)"
---

# Aggiorna

Porti la copia di Arturo di chi ti parla all'ultima versione. È il comando che l'avviso di avvio
gli suggerisce quando c'è qualcosa di nuovo.

Chi ti parla **potrebbe non essere una persona tecnica**: niente gergo di Git, nessun output
grezzo incollato senza spiegazione.

## Passo 1 — Guarda cosa c'è di nuovo

Gli aggiornamenti arrivano da `upstream` se ha un repository suo come `origin` (vedi `/setup`
FASE 7), altrimenti da `origin`.

```bash
SRC=$(git -C "$HOME/.claude" remote get-url upstream >/dev/null 2>&1 && echo upstream || echo origin)
GIT_TERMINAL_PROMPT=0 git -C "$HOME/.claude" fetch --quiet "$SRC" main 2>&1 || echo "fetch non riuscito (rete?)"
BEHIND=$(git -C "$HOME/.claude" rev-list --count "HEAD..$SRC/main" 2>/dev/null || echo 0)
echo "Aggiornamenti da $SRC: ${BEHIND:-0}"
git -C "$HOME/.claude" log --oneline "HEAD..$SRC/main" 2>/dev/null | head -20
git -C "$HOME/.claude" status --short
```

Se `BEHIND` è `0`, diglielo in una riga — è già aggiornato — e fermati.

## Passo 2 — Controlla le sue modifiche

`git status --short` ti dice se ha cambiato file suoi: tipicamente `CLAUDE.md` o i permessi in
`settings.json`. Se ce ne sono, **mostraglieli e chiedi conferma prima di procedere**: sono suoi,
e un aggiornamento non deve mangiarseli.

## Passo 3 — Applica

Solo dopo il suo sì:

```bash
git -C "$HOME/.claude" pull --rebase "$SRC" main
```

Se il comando si ferma per un conflitto, **non forzare nulla**: nessun `--force`, nessun `reset
--hard`, nessun `checkout` che butti via il suo lavoro. Mostragli quali file sono in conflitto e
risolvili con lui uno per volta, spiegando in parole semplici cosa c'era prima e cosa arriva.

## Passo 4 — Riavvio e racconto

Due cose, in quest'ordine:

1. Digli di **chiudere e riaprire Claude Code**. Comandi, hook e skill si leggono all'avvio della
   sessione: finché non riapre, quello che è appena arrivato non esiste per lui. È il passo che si
   dimentica più spesso, quindi dillo esplicitamente.
2. Dopo il riavvio, **`/novita`** gli racconta cosa è cambiato e perché gli conviene saperlo. Se
   `NOVITA.md` è arrivato solo ora, è normale: prima quella copia non aveva il canale.

## Freni

- Il `pull` si fa dopo un sì, mai in automatico.
- Mai scartare modifiche sue per far passare l'aggiornamento.
- Se il fetch fallisce, è quasi sempre la rete o un repository non raggiungibile: dillo senza
  drammatizzare e non ritentare a oltranza.
