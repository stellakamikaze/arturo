# La fonte dei task fuori da Arturo

Arturo tiene i todo in `~/.claude/data/todo/`. Se li tieni già in un altro strumento (un database, un
tracker, un foglio), Arturo può leggerli e scriverli lì, senza cambiare `/inizio` e `/fine`.

## Come si collega

Scrivi in `~/.claude/bin/fonte-task.local` una riga:

```
comando = python3 ~/.claude/personale/mia_fonte.py
```

Da quel momento `arturo todo <argomenti>` lancia il tuo programma con gli stessi argomenti, senza shell,
e restituisce la sua uscita e il suo codice. Nei percorsi usa le barre dritte (`/`), anche su Windows.
Il file è tuo: gli aggiornamenti di Arturo non lo toccano. Per tornare all'archivio di Arturo, toglilo.

## Cosa deve fare il tuo programma

Riceve gli argomenti di `arturo todo` e risponde come lui. Quelli che `/inizio`, `/fine` e
`arturo contesto` usano:

| Argomenti | Cosa fa | Uscita |
|---|---|---|
| `--progetto <slug> --json [--tutti]` | i todo aperti del progetto | il JSON qui sotto |
| `aggiungi "<titolo>" --progetto <slug> [--chi …] [--priorita …]` | un todo nuovo | `#<numero>` del todo |
| `fatto <numero>` | chiude un todo | una riga di conferma |
| `ferma <numero> "<motivo>"`, `nota <numero> "<testo>"`, `modifica <numero> …` | cambia un todo | una riga di conferma |

`--titolo-atteso=<testo>` su un verbo che scrive vuol dire: il todo `<numero>` deve avere ancora quel
titolo, altrimenti fermati con exit 2 e dillo.

Il JSON di `--json`:

```json
{
  "gruppi": [
    {"tipo": "io", "todo": [{"id": 12, "titolo": "Rileggere il capitolo", "stato": "da fare",
                             "priorita": "alta", "scadenza_testo": "entro venerdì"}]}
  ],
  "chiusi_todo": [{"id": 11, "titolo": "Scrivere l'indice", "stato": "fatto", "chiuso": "2026-10-30T18:00"}]
}
```

`tipo` vale `tu`, `decidi`, `io` o `fermo`. Di ogni todo servono `id` e `titolo`; gli altri campi
(`stato`, `priorita`, `scadenza_testo`, `perche`, `motivo`, `attende`) sono facoltativi. `chiusi_todo`
serve solo con `--tutti`.

## Codici d'uscita

- `0` fatto;
- `2` uso sbagliato (argomenti, numero inesistente, titolo atteso diverso);
- `3` fonte giù, oppure esito incerto (per esempio un timeout dopo l'invio: il todo può esistere).

Con `3` in lettura, `arturo contesto` mostra i task della tabella dell'ultimo handoff con l'avviso
NON VERIFICATO. Con `3` su `aggiungi`, `/fine` non ritenta: prima cerca il titolo, poi scrive
`OFFLINE` nella tabella.

Se tieni i task fuori da Arturo, scrivi anche `hooks/handoff-gate.local` con `archivio = no`: il
controllo dell'handoff non cerca più i numeri nell'archivio di Arturo (vedi `bin/handoff_profilo.py`).
