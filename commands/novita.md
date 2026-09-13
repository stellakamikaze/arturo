---
description: Racconta le novità dell'harness non ancora viste - cosa cambia, il principio dietro, e propone lo sparring per provarle sui propri casi d'uso
argument-hint: "(nessuno) | tutte"
---

# Novità

Sei il canale di aggiornamento di **Arturo**. Quando l'harness evolve, il repo si aggiorna per tutti — questo comando racconta a chi lo usa **cosa è cambiato e perché gli conviene saperlo**, in linguaggio semplice, senza dare niente per scontato.

## Passo 0 — L'harness è aggiornato?

Gli aggiornamenti di Arturo arrivano da `upstream` se l'utente ha un repository suo come `origin` (vedi `/setup` FASE 7), altrimenti da `origin`.

```bash
SRC=$(git -C "$HOME/.claude" remote get-url upstream >/dev/null 2>&1 && echo upstream || echo origin)
git -C "$HOME/.claude" fetch --quiet "$SRC" main 2>/dev/null
BEHIND=$(git -C "$HOME/.claude" rev-list --count "HEAD..$SRC/main" 2>/dev/null || echo 0)
echo "Aggiornamenti di Arturo da $SRC non ancora applicati: ${BEHIND:-0}"
```

Se è indietro, spiega che ci sono aggiornamenti da scaricare e proponi (chiedendo conferma):

```bash
git -C "$HOME/.claude" pull --rebase "$SRC" main
```

Se il pull fallisce per modifiche locali, non forzare nulla: mostra `git -C ~/.claude status --short` e aiuta l'utente a capire cosa ha cambiato lui, un file per volta.

## Passo 1 — Cosa non ha ancora visto

Le novità vivono in `~/.claude/NOVITA.md` (entry in ordine inverso, la più recente in cima, intestazione `## AAAA-MM-GG — Titolo`). Il segnalibro è l'elenco delle intestazioni delle entry già raccontate (data e titolo, senza `## `), una per riga, in `~/.claude/session-env/novita-viste`. L'intestazione intera distingue due entry della stessa data. Un vecchio `~/.claude/session-env/novita-vista` con una sola data vale ancora: le entry fino a quella data contano come viste.

```bash
VISTE="$HOME/.claude/session-env/novita-viste"
VECCHIA=$(cat "$HOME/.claude/session-env/novita-vista" 2>/dev/null || echo "")
grep '^## ' "$HOME/.claude/NOVITA.md" 2>/dev/null | sed 's/^## //' | while IFS= read -r ENTRY; do
  DATA=$(printf '%s' "$ENTRY" | grep -oE '^[0-9]{4}-[0-9]{2}-[0-9]{2}')
  if { [ -n "$VECCHIA" ] && [ -n "$DATA" ] && [[ ! "$DATA" > "$VECCHIA" ]]; } || grep -qxF "$ENTRY" "$VISTE" 2>/dev/null; then
    echo "vista:     $ENTRY"
  else
    echo "non vista: $ENTRY"
  fi
done
```

- Nessuna entry vista → è la prima volta: racconta tutte le entry (o le ultime 3 se sono tante, offrendo le altre).
- Altrimenti → racconta solo le entry `non vista`, dalla più vecchia alla più recente.
- Nessuna `non vista` → dillo in una riga («sei aggiornato, ultima novità del ...») e fermati. Con argomento `tutte`, racconta tutto lo storico a prescindere dal segnalibro.

## Passo 2 — Il racconto

Per ogni entry non vista, **una per volta**:

1. **Cosa cambia**, in due frasi tue — non incollare l'entry, raccontala.
2. **Il principio dietro** — perché questa novità esiste, cosa insegna. Se l'entry rimanda a un capitolo di `docs/principi/`, offri di leggerlo insieme.
3. **Ti riguarda se...** — aiuta l'utente a capire se la novità tocca il suo modo di usare l'harness.
4. Proponi: «vuoi fare un po' di sparring per vedere se ti serve?» → se sì, passa a `/sparring novità AAAA-MM-GG — Titolo` con l'intestazione di questa entry.
5. Segna questa entry come vista (Passo 3) prima di passare alla successiva.

Linguaggio semplice, zero gergo non spiegato. Se le entry nuove sono più di una, chiedi dopo ciascuna se proseguire.

## Passo 3 — Segna l'entry appena raccontata

Dopo ogni singola entry raccontata, subito, mai in blocco alla fine. Se la lettura si interrompe, le entry non raccontate restano `non vista`.

```bash
mkdir -p "$HOME/.claude/session-env"
ENTRY="AAAA-MM-GG — Titolo"   # l'intestazione dell'entry appena raccontata, senza «## »
grep -qxF "$ENTRY" "$HOME/.claude/session-env/novita-viste" 2>/dev/null || echo "$ENTRY" >> "$HOME/.claude/session-env/novita-viste"
echo "Segnata come vista: $ENTRY"
```

## Regole

- Mai auto-eseguire pull o esperimenti senza conferma.
- Se `NOVITA.md` non esiste, dillo senza drammatizzare: questa copia dell'harness è precedente al canale novità — proponi il pull.
- Il comando informa e propone: le decisioni restano dell'utente.
