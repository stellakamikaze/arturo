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
`--chi`. Un todo che aspetta un altro todo si collega con `dopo ID ALTRO`. Un todo su cui stai
lavorando adesso va «in corso» con `inizia ID`.

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
| `inizia ID` | lo segna «in corso» |
| `fatto ID` · `scarta ID "motivo"` | lo chiude, fatto o senza farlo |
| `ferma ID "motivo"` · `riprendi ID` | lo mette in FERMO, lo riapre come «da fare» |
| `deciso ID "testo"` | per un todo `decidi`: scrive la nota «Deciso: testo» e passa il todo a `io` |
| `ripristina ID STATO [motivo]` | rimette stato e motivo esatti di prima, con il segno di annullo |
| `nota ID "testo"` | aggiunge una nota |
| `dopo ID ALTRO [--togli]` | ID aspetta che ALTRO sia chiuso |
| `su ID` · `giu ID` | lo avvicina o lo allontana: più avanti, settimana, oggi |

Le letture accettano `--json`: è il formato che leggono il pannello e la pagina web, e quello
che leggi tu quando devi ragionare sui todo invece di mostrarli.

## Decisioni e annulli

Quando la persona sceglie su un todo `decidi` («va bene il piano B»), usa `deciso ID "piano B"`.
Il comando scrive la scelta e passa il lavoro a te in un colpo solo. Non usare `nota` più
`modifica --chi io`: sono due scritture, e chi legge in mezzo vede la nota senza il passaggio a
te. E `deciso` scrive sempre il prefisso «Deciso: », che il percorso legge. Su un todo che non è
`decidi` il comando si rifiuta. Su un todo chiuso si rifiuta anche: prima lo riapri con
`riprendi`. Un todo FERMO resta FERMO, e quando riparte lo fai tu.

Se la persona dice che un passo era uno sbaglio («no, non era fatto»), riporta il todo com'era
con `ripristina ID STATO "motivo di prima"`: lo stato e il motivo li leggi in
`mostra ID --json`, nella storia. Uno stato di due parole va anche senza virgolette:
`ripristina 4 da fare`. Un motivo che comincia con un trattino va in un token solo:
`ripristina 4 --motivo=-firma fermo`. Non usare `riprendi`: riapre sempre come «da fare» e perde il
motivo di un FERMO. `ripristina` mette nell'evento il segno `annullo`, e chi legge la storia sa
che non è una scelta della persona. `modifica`, `su`, `giu`, `inizia`, `fatto`, `riprendi`,
`ferma` e `scarta` accettano `--annullo` per lo stesso scopo: lo usano pannello e pagina web
quando annullano un clic.

## Regole

- Prima di aggiungere, guarda se il todo c'è già (`arturo todo --progetto P`). Un doppione
  costa alla persona più di un todo mancante.
- Un todo che hai fatto tu in questa sessione lo chiudi con `fatto` e lo dici.
- Non cancelli mai il file dell'archivio e non lo modifichi a mano. Se un comando dice che una
  riga è illeggibile, riferiscilo alla persona: la riga resta e il resto funziona.
- Il file è `~/.claude/data/todo/eventi.jsonl`. Contiene dati della persona: non va mai in un
  repository pubblico.

## Il pannello /dafare

La persona può vedere e muovere i suoi todo anche senza di te: scrive `/dafare` e si apre un
pannello dentro Claude Code. Sceglie una riga con il numero e preme una lettera: `f` fatto, `s`
ferma, `r` riprendi, `c` chi lo fa, `a` avvicina, `l` allontana, `u` annulla. Il pannello scrive
con la stessa CLI che usi tu, quindi quello che vedi con `arturo todo` è sempre aggiornato.

- I comandi di un mod non compaiono fra quelli che vedi: per sapere se il pannello c'è, lancia
  una volta per sessione, prima di nominarlo, la stessa riga di `/diagnosi`:

  ```bash
  claude plugin list --json | python3 -c 'import json,sys; v=[p for p in json.load(sys.stdin) if p.get("id") == "dafare@skills-dir"]; print("mod caricato" if v and v[0].get("enabled") else "mod assente")'
  ```

  Il pannello c'è solo se la riga stampa «mod caricato». Con Claude Code più vecchio della
  2.1.287, con il mod spento o se il comando non risponde, manca: allora non nominarlo e mostra
  i gruppi di `arturo todo`, come sempre.
- Se il pannello c'è, la prima volta nella sessione che confermi un `aggiungi` nominalo: «Segnato
  come #1. Lo vedi con /dafare.» Dopo, non ripeterlo.
- Quando la persona chiede «cosa c'è da fare?», mostra i gruppi. Se il pannello c'è, proponi
  `/dafare` per agire con i tasti.
- La riga sopra il prompt («3 cose da fare») si spegne con `/dafare nascondi` e si riaccende con
  `/dafare mostra`.
