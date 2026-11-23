# Il file di sessione

Ogni sessione di Claude Code ha un file `~/.claude/cache/scheda/<sessione>.json`. Dice a che progetto
appartiene la sessione e in che stato è. Lo leggono la barra in basso, la scheda del terminale e Volta.
Dal 23/11/2026 il file ha un solo padrone: `hooks/scheda_file.py`. Nessun altro scrittore lo riscrive a mano.

## Formato (versione 1)

| Campo | Cosa contiene |
|---|---|
| `versione` | 1. Un file senza il campo vale 0 e prende la 1 alla prima scrittura. |
| `stato` | nuova, lavoro, attende, fermo, problema, chiusa. Lo scrive l'hook della scheda. |
| `progetto` | lo slug del progetto, fino a 60 caratteri fra lettere, cifre, punto e trattino. |
| `fonte` | chi ha deciso il progetto: una voce della tabella sotto. |
| `quando` | l'istante della scrittura, in secondi. Un evento più vecchio non sovrascrive. |
| `spostata` | `{su, quando}`: la sessione è stata spostata su un'altra macchina (Volta, `sposta-sessione`). |
| `inizio`, `sessionId` | segni di Volta, validi finché il progetto e la fonte sono quelli che li hanno scritti. |

I campi nuovi si aggiungono senza cambiare la versione. Un campo che cambia significato alza la versione.

## Le fonti

| Fonte | Rango | Chi la scrive |
|---|---|---|
| `cartella` | 0 | l'hook: la cartella di lavoro |
| `file`, `modello` | 1 | l'hook: un file scritto in un progetto; Volta: il modello |
| `prompt` | 2 | l'hook: il testo dopo `/inizio` |
| `teletrasporto`, `volta`, `inizio`, `persona` | 3 (decise) | teletrasporto, Volta, il risolutore di `/inizio`, la persona |

Una fonte sotto il rango del `prompt` non sostituisce un progetto di fonte decisa. Se il progetto è lo stesso,
resta la fonte forte. Il `prompt` e le fonti decise sostituiscono sempre.

## Come si scrive

- Da Python: `scheda_file.imposta_progetto(sessione, progetto, fonte)` e `scheda_file.segna_spostata(sessione, su)`.
  `forza=True` senza fonte è la correzione della persona (`arturo progetti unisci`): cambia il progetto e lascia fonte e segni.
- Da fuori (Volta, teletrasporto, `sposta-sessione`): `arturo sessione progetto SID SLUG --fonte F` e
  `arturo sessione spostata SID --su MACCHINA`. Exit 0 scritto, 2 rifiutato dalla regola (dice perché), 3 argomenti non validi.

Il banco è `tests/test_scheda_file.py` (casi SE01-SE07, con veleni).
