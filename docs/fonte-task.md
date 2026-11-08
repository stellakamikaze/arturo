# La fonte dei task fuori da Arturo

Arturo tiene i todo in `~/.claude/data/todo/`. Se li tieni già in un altro strumento (un database, un
tracker, un foglio), Arturo può leggerli e scriverli lì, senza cambiare `/inizio` e `/fine`.

## Come si collega

Scrivi in `~/.claude/arturo/fonte-task.local` una riga:

```
comando = python3 ~/.claude/personale/mia_fonte.py
```

Da quel momento `arturo todo <argomenti>` lancia il tuo programma con gli stessi argomenti, senza shell,
e restituisce la sua uscita e il suo codice. Nei percorsi usa le barre dritte (`/`), anche su Windows.
Il file è tuo: gli aggiornamenti di Arturo non lo toccano. Per tornare all'archivio di Arturo, toglilo.
Arturo lo cerca sempre lì, nella tua cartella di casa, anche se lanci Arturo da un'altra cartella: un banco con una casa di prova non trova la tua fonte e non scrive sul tuo strumento.

## Cosa deve fare il tuo programma

Riceve gli argomenti di `arturo todo` e risponde come lui. Quelli che `/inizio`, `/fine` e
`arturo contesto` usano:

| Argomenti | Cosa fa | Uscita |
|---|---|---|
| `--progetto <slug> --json [--tutti]` | i todo aperti del progetto | il JSON qui sotto |
| `aggiungi "<titolo>" --progetto <slug> [--chi …] [--priorita …]` | un todo nuovo | `#<numero>` del todo |
| `fatto <numero>` | chiude un todo | una riga di conferma |
| `ferma <numero> "<motivo>"`, `nota <numero> "<testo>"`, `modifica <numero> …` | cambia un todo | una riga di conferma |

Due verbi sono facoltativi: se il tuo programma non li conosce, esce con 2 e Arturo prosegue senza.

| Argomenti | Cosa fa | Uscita |
|---|---|---|
| `aggiungi "<titolo>" … --dopo N[,M]` | il todo nuovo aspetta i todo N e M | `#<numero>` del todo |
| `stato [--progetto <slug>] ["<riga>"]` | senza riga legge, con la riga scrive a che punto è il progetto | la riga |

Il pannello `/dafare` usa altri verbi. Se il tuo programma non li conosce, il tasto risponde con il suo
errore e non cambia niente.

| Argomenti | Cosa fa | Uscita |
|---|---|---|
| `mostra <numero> --json` | un todo, per aprire una sessione su di lui (tasto o) | JSON con almeno `titolo` e `progetto` |
| `riprendi <numero>`, `su <numero>`, `giu <numero>` | riapre, avvicina, allontana | una riga di conferma |
| `ripristina <numero> --atteso=stato=<s> [--motivo=<m>] -- <stato>` | l'annulla di fatto, ferma, riprendi | una riga di conferma |
| `modifica <numero> --chi <chi>` o `--quando <quando>` `[--atteso=<campo>=<valore>] [--annullo]` | chi lo fa, e l'annulla di su e giu | una riga di conferma |

`--atteso=<campo>=<valore>` vuol dire: scrivi solo se il campo ha ancora quel valore, altrimenti esci
con 2. Il `progetto` di `mostra` diventa il nome dopo `/inizio`: Arturo lo riduce a lettere, numeri e
trattini.

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

Il pannello `/dafare` legge anche il blocco facoltativo `progetti`: un elemento per progetto con todo
aperti, dal più urgente. Se manca, il pannello lo ricava dai gruppi, con la riga dichiarata come calcolata.

```json
"progetti": [
  {"nome": "sito", "parola": "va", "riga": "La home è scritta a metà", "calcolato": false,
   "scritto": "2026-11-05T09:00", "eta_gg": 0, "vecchio": false, "aperti": 3, "scaduti": 0,
   "chiedono_te": 0, "fermi": 0, "catena": [2, 3, 4], "da_dove": {"id": 2, "motivo": "Sblocca #3"}}
]
```

`parola` vale `a rischio`, `chiede te`, `fermo` o `va`. `catena` elenca i todo legati da "dopo", dal
primo passo all'ultimo; `da_dove` è il todo da cui ripartire, o `null`. Con `--progetto <slug>` il
blocco ha solo quel progetto.

Tre campi facoltativi servono alla finestra di Arturo in Herdr ([herdr.md](herdr.md)): `titolo`, il nome del
progetto come lo leggono le persone ("Casa / Mutuo Torino"); `categoria`, la sezione in cui compare
("Commesse", "Personale"); `slug`, il nome per `/inizio` quando `nome` è diverso. Senza `titolo` la
finestra ricava il nome da `nome`, senza `categoria` mette tutto sotto "I tuoi progetti".

## Codici d'uscita

- `0` fatto;
- `2` uso sbagliato (argomenti, numero inesistente, titolo atteso diverso);
- `3` fonte giù, oppure esito incerto (per esempio un timeout dopo l'invio: il todo può esistere).

Con `3` in lettura, `arturo contesto` mostra i task della tabella dell'ultimo handoff con l'avviso
NON VERIFICATO. Con `3` su `aggiungi`, `/fine` non ritenta: prima cerca il titolo, poi scrive
`OFFLINE` nella tabella.

Se tieni i task fuori da Arturo, scrivi anche `arturo/handoff-gate.local` con `archivio = no`: il
controllo dell'handoff non cerca più i numeri nell'archivio di Arturo (vedi `bin/handoff_profilo.py`).
