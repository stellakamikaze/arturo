---
name: todo
description: >-
  Legge e modifica i todo della persona con la CLI `arturo todo`: un archivio locale che
  sopravvive alla sessione, diviso per progetto, scadenza e chi agisce (la persona o Claude).
when_to_use: >-
  Usa quando la persona dice «ricordami di…», «segnati che…», «mettilo tra le cose da fare»,
  «cosa c'è da fare?», «cosa scade questa settimana?», o chiede di chiudere, spostare o fermare
  un todo. NON per i passi interni di questa sola sessione (quelli sono TaskCreate e spariscono
  alla chiusura). Segui tutti i passi nell'ordine: non prendere scorciatoie basandoti su questa
  description.
version: 1.0.0
license: MIT
---

# Todo: l'archivio di quello che resta da fare

## Che cosa deve uscire

La persona dice una cosa da fare con parole sue. Dopo pochi secondi la ritrova nell'archivio,
scritta come un'azione, nel progetto giusto, con la scadenza che ha detto e con chi agisce. Tu
le confermi il numero del todo in una riga. Non le chiedi i campi uno per uno: li ricavi dalla
frase e dal contesto, e chiedi solo se manca qualcosa che cambia il lavoro.

Esempio. La persona scrive «ricordami di mandare a Gigi la parola d'ordine entro venerdì».

```bash
python3 ~/.claude/bin/arturo todo aggiungi "Mandare a Gigi la parola d'ordine" --scadenza venerdì --chi tu --perche "invio a terzi"
```

Tu rispondi: «Segnato come #7, scade venerdì.» Il todo è `tu` perché l'invio lo fa la persona.

## I campi

| Campo | Valori | Come lo scegli |
|---|---|---|
| titolo | verbo e oggetto | «Mandare il preventivo a Rossi», non «preventivo-rossi» |
| `--progetto` | slug del progetto | di default la cartella git in cui sei, altrimenti `generale` |
| `--scadenza` | `2026-10-10`, `10/10`, `oggi`, `domani`, `venerdì` | solo se la persona ne dice una |
| `--chi` | `tu` · `decidi` · `io` | `tu`: lo fa la persona. `decidi`: serve una sua scelta, poi lavori tu. `io`: lo fai tu |
| `--perche` | testo breve | perché tocca alla persona: «invio a terzi», «password», «firma» |
| `--priorita` | `alta` · `media` · `bassa` | `media` se non emerge altro |
| `--quando` | `oggi` · `settimana` · `più avanti` | `settimana` se non emerge altro |

Un todo bloccato da qualcosa di esterno va in FERMO con `ferma ID "motivo"`. Non si segna con
`--chi`. Un todo che aspetta un altro todo si collega con `dopo ID ALTRO`.

## I comandi

Scrivi sempre `python3 ~/.claude/bin/arturo todo` davanti. La persona può avere l'alias
`arturo`, ma tu non contarci.

| Comando | Effetto |
|---|---|
| *(niente)* `[--progetto P] [--tutti] [--json]` | i todo aperti divisi in TOCCA A TE, DECIDI TU, FACCIO IO, FERMO |
| `oggi [--giorni N]` | per oggi, scaduti e in scadenza nei prossimi N giorni |
| `progetti` | quanti todo aperti, scaduti, fermi e chiusi ha ogni progetto |
| `mostra ID` | un todo con note e storia |
| `aggiungi "titolo" [campi] [--note "testo"]` | un todo nuovo |
| `modifica ID [campi] [--titolo "nuovo"]` | cambia i campi indicati (`--scadenza ""` la toglie) |
| `fatto ID` · `scarta ID "motivo"` | lo chiude, fatto o senza farlo |
| `ferma ID "motivo"` · `riprendi ID` | lo mette in FERMO, lo riapre |
| `nota ID "testo"` | aggiunge una nota |
| `dopo ID ALTRO [--togli]` | ID aspetta che ALTRO sia chiuso |
| `su ID` · `giu ID` | lo avvicina o lo allontana: più avanti, settimana, oggi |

Le letture accettano `--json`: è il formato che leggono il pannello e la pagina web, e quello
che leggi tu quando devi ragionare sui todo invece di mostrarli.

## Regole

- Prima di aggiungere, guarda se il todo c'è già (`arturo todo --progetto P`). Un doppione
  costa alla persona più di un todo mancante.
- Un todo che hai fatto tu in questa sessione lo chiudi con `fatto` e lo dici.
- Non cancelli mai il file dell'archivio e non lo modifichi a mano. Se un comando dice che una
  riga è illeggibile, riferiscilo alla persona: la riga resta e il resto funziona.
- Il file è `~/.claude/data/todo/eventi.jsonl`. Contiene dati della persona: non va mai in un
  repository pubblico.
