---
description: Racconta le novità dell'harness non ancora viste - cosa cambia, il principio dietro, e propone lo sparring per provarle sui propri casi d'uso
argument-hint: "(nessuno) | tutte"
---

# Novità

Sei il canale delle novità di **Arturo**. Quando l'harness evolve, i rilasci firmati arrivano a tutti: questo comando racconta a chi lo usa **cosa è cambiato e perché gli conviene saperlo**, in linguaggio semplice, senza dare niente per scontato.

## Passo 0 — L'harness è aggiornato?

Gli aggiornamenti di Arturo arrivano da `upstream` se l'utente ha un repository suo come `origin` (vedi `/setup` FASE 7), altrimenti da `origin`.

```bash
# Col plugin ~/.claude non è il repository di Arturo: il rilascio nuovo si legge dal catalogo firmato.
if [ -n "${ARTURO_CODICE:-}" ] && [ "$(cd "$ARTURO_CODICE" 2>/dev/null && pwd -P)" != "$(cd ~/.claude 2>/dev/null && pwd -P)" ]; then
  VERIFICA=$(python3 ~/.claude/bin/aggiornamenti.py plugin --verifica 2>&1); rc=$?
  case "$rc:$VERIFICA" in
    0:*"GIÀ AGGIORNATO"*) echo "Aggiornamenti di Arturo non ancora applicati: 0 (col plugin)" ;;
    0:*) echo "Aggiornamenti di Arturo non ancora applicati: c'è il rilascio firmato $(printf '%s\n' "$VERIFICA" | tail -1)" ;;
    *) printf '%s\n' "$VERIFICA" ;;
  esac
else
SRC=$(git -C ~/.claude remote get-url upstream >/dev/null 2>&1 && echo upstream || echo origin)
git -C ~/.claude fetch --quiet --tags "$SRC" main 2>/dev/null
# Conta solo fino all'ultimo tag firmato: i commit di main dopo il tag non si applicano (#3504).
if TAG=$(python3 ~/.claude/bin/aggiornamenti.py firmato); then
  BEHIND=$(git -C ~/.claude rev-list --count "HEAD..$TAG" 2>/dev/null || echo 0)
  echo "Aggiornamenti di Arturo da $SRC non ancora applicati: ${BEHIND:-0} (fino al rilascio firmato $TAG)"
fi
fi
```

Se è indietro, spiega che c'è un rilascio firmato non ancora installato. Di solito si installa da
solo alla chiusura della sessione. Se lo vuole subito, o l'avvio dice "serve /aggiorna", proponi
**`/aggiorna`**: gli mostra cosa cambia e lo applica dopo il suo sì. `/novita` non scarica niente da solo. Se compare `POSSIBILE COMPROMISSIONE`, non proporre `/aggiorna`: diglielo con le
parole "possibile compromissione: non aggiornare, segnala a chi mantiene Arturo". Se compare
`FIRMA NON VERIFICABILE`, il suo computer non sa controllare la firma: digli di aggiornare git e
OpenSSH, e che non è un problema di sicurezza.

## Passo 1 — Cosa non ha ancora visto

Le novità vivono in `~/.claude/NOVITA.md` (entry in ordine inverso, la più recente in cima, intestazione `## AAAA-MM-GG — Titolo`). Il segnalibro è l'elenco delle intestazioni delle entry già raccontate (data e titolo, senza `## `), una per riga, in `~/.claude/session-env/novita-viste`. L'intestazione intera distingue due entry della stessa data. Un vecchio `~/.claude/session-env/novita-vista` con una sola data vale ancora: le entry fino a quella data contano come viste.

```bash
VISTE=~/.claude/session-env/novita-viste
VECCHIA=$(cat ~/.claude/session-env/novita-vista 2>/dev/null || echo "")
grep '^## ' ~/.claude/NOVITA.md 2>/dev/null | sed 's/^## //' | while IFS= read -r ENTRY; do
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
- Più di 10 entry `non vista` → non raccontarle una per una: proponi subito un riassunto per temi, con il Passo 2b.
- Nessuna `non vista` → dillo in una riga ("sei aggiornato, ultima novità del ...") e fermati. Con argomento `tutte`, racconta tutto lo storico a prescindere dal segnalibro.

## Passo 2 — Il racconto

Per ogni entry non vista, **una per volta**:

1. **La sua segnalazione, se c'è.** Se l'entry cita una "segnalazione n. X" mandata da questa persona,
   la prima frase lo dice: "è uscita la correzione della tua segnalazione n. X". Le sue segnalazioni e i
   loro numeri: `python3 ~/.claude/bin/arturo segnala stato`, lanciato una volta all'inizio del racconto.
2. **Il diagramma, se c'è.** Un blocco di codice aperto con ` ```diagramma ` si mostra così com'è, intero e
   prima del racconto, dentro un blocco di codice: è l'unica parte dell'entry che non racconti a parole.
   Poi una frase che dice dove si trova la persona nel disegno.
3. **Cosa cambia**, in due frasi tue — non incollare l'entry, raccontala.
4. **Il principio dietro** — perché questa novità esiste, cosa insegna. Se l'entry rimanda a un capitolo di `~/.claude/docs/principi/`, offri di leggerlo insieme.
5. **Ti riguarda se...** — aiuta l'utente a capire se la novità tocca il suo modo di usare l'harness.
6. Proponi: "vuoi fare un po' di sparring per vedere se ti serve?" → se sì, apri con Read `~/.claude/commands/sparring.md` e seguilo con l'argomento `novità AAAA-MM-GG — Titolo`, l'intestazione di questa entry.
7. Segna questa entry come vista (Passo 3) prima di passare alla successiva.

Linguaggio semplice, zero gergo non spiegato. Se le entry nuove sono più di una, chiedi dopo ciascuna se proseguire.

## Passo 2b — Un arretrato grande

Con più di 10 entry `non vista`, il racconto una per volta dura ore (segnalazione n. 59: 113 voci arretrate).

1. Lancia una volta `python3 ~/.claude/bin/arturo segnala stato`. Apri con le entry che correggono le sue segnalazioni, col numero.
2. Raggruppa il resto in pochi temi, una o due frasi per tema, con le entry che ne fanno parte.
3. Chiedi se vuole approfondire un tema. Il racconto del Passo 2 vale per le entry che sceglie.
4. Quando ha letto il riassunto, segna come viste tutte le entry che copre, con il ciclo del Passo 3.

Con argomento `tutte` vale la stessa regola: il racconto una per volta parte solo se la persona lo chiede.

## Passo 3 — Segna l'entry appena raccontata

Dopo ogni singola entry raccontata, subito, mai in blocco alla fine. Se la lettura si interrompe, le entry non raccontate restano `non vista`.

```bash
mkdir -p ~/.claude/session-env
ENTRY="AAAA-MM-GG — Titolo"   # l'intestazione dell'entry appena raccontata, senza "## "
grep -qxF "$ENTRY" ~/.claude/session-env/novita-viste 2>/dev/null || echo "$ENTRY" >> ~/.claude/session-env/novita-viste
echo "Segnata come vista: $ENTRY"
```

## Regole

- Mai applicare aggiornamenti: i rilasci firmati si installano da soli alla chiusura della sessione, e `/aggiorna` applica quelli che restano in attesa. Mai esperimenti senza conferma.
- Se `NOVITA.md` non esiste, dillo senza drammatizzare: questa copia dell'harness è precedente al canale novità: proponi `/aggiorna`.
- Il comando informa e propone: le decisioni restano dell'utente.
