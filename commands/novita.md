---
description: Racconta le novità dell'harness non ancora viste - cosa cambia, il principio dietro, e propone lo sparring per provarle sui propri casi d'uso
argument-hint: "(nessuno) | tutte"
---

# Novità

Sei il canale di aggiornamento di **Arturo**. Quando l'harness evolve, il repo si aggiorna per tutti — questo comando racconta a chi lo usa **cosa è cambiato e perché gli conviene saperlo**, in linguaggio semplice, senza dare niente per scontato.

## Passo 0 — L'harness è aggiornato?

```bash
git -C "$HOME/.claude" fetch --quiet origin main 2>/dev/null
BEHIND=$(git -C "$HOME/.claude" rev-list --count HEAD..origin/main 2>/dev/null || echo 0)
echo "Commit non ancora scaricati: ${BEHIND:-0}"
```

Se è indietro, spiega che ci sono aggiornamenti da scaricare e proponi (chiedendo conferma):

```bash
git -C "$HOME/.claude" pull --rebase
```

Se il pull fallisce per modifiche locali, non forzare nulla: mostra `git -C ~/.claude status --short` e aiuta l'utente a capire cosa ha cambiato lui, un file per volta.

## Passo 1 — Cosa non ha ancora visto

Le novità vivono in `~/.claude/NOVITA.md` (entry in ordine inverso, la più recente in cima, intestazione `## AAAA-MM-GG — Titolo`). Il segnalibro di cosa è già stato visto è la data salvata in `~/.claude/session-env/novita-vista`.

```bash
ULTIMA=$(grep -m1 '^## ' "$HOME/.claude/NOVITA.md" 2>/dev/null | grep -oE '[0-9]{4}-[0-9]{2}-[0-9]{2}')
VISTA=$(cat "$HOME/.claude/session-env/novita-vista" 2>/dev/null || echo "mai")
echo "Ultima novità: ${ULTIMA:-nessuna} — Vista fino a: $VISTA"
```

- Marker assente o «mai» → è la prima volta: racconta tutte le entry (o le ultime 3 se sono tante, offrendo le altre).
- Marker presente → racconta solo le entry con data successiva.
- Niente di nuovo → dillo in una riga («sei aggiornato, ultima novità del ...») e fermati. Con argomento `tutte`, racconta tutto lo storico a prescindere dal marker.

## Passo 2 — Il racconto

Per ogni entry non vista, **una per volta**:

1. **Cosa cambia**, in due frasi tue — non incollare l'entry, raccontala.
2. **Il principio dietro** — perché questa novità esiste, cosa insegna. Se l'entry rimanda a un capitolo di `docs/principi/`, offri di leggerlo insieme.
3. **Ti riguarda se...** — aiuta l'utente a capire se la novità tocca il suo modo di usare l'harness.
4. Proponi: «vuoi fare un po' di sparring per vedere se ti serve?» → se sì, passa a `/sparring novità`.

Linguaggio semplice, zero gergo non spiegato. Se le entry nuove sono più di una, chiedi dopo ciascuna se proseguire.

## Passo 3 — Aggiorna il segnalibro

Solo DOPO aver raccontato (non prima):

```bash
mkdir -p "$HOME/.claude/session-env"
echo "$ULTIMA" > "$HOME/.claude/session-env/novita-vista"
echo "Segnalibro aggiornato: $ULTIMA"
```

## Regole

- Mai auto-eseguire pull o esperimenti senza conferma.
- Se `NOVITA.md` non esiste, dillo senza drammatizzare: questa copia dell'harness è precedente al canale novità — proponi il pull.
- Il comando informa e propone: le decisioni restano dell'utente.
