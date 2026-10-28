---
description: Manda a chi mantiene Arturo un problema, un'idea o una richiesta di integrazione - la bozza la scrive Claude, parte solo dopo il tuo sì
argument-hint: "[cosa vuoi segnalare] (opzionale)"
---

# Segnala

Arturo migliora con quello che le persone gli dicono. Questo comando porta a chi lo mantiene
tre cose:

- **un problema**: qualcosa di Arturo o di Claude Code che non funziona, si blocca o fa altro;
- **un'idea**: un comportamento da cambiare, una cosa che manca, un commento;
- **un'integrazione**: uno strumento da collegare (un programma, un servizio, un archivio).

Chi ti parla **potrebbe non essere una persona tecnica**. Parla semplice, una domanda per volta.
La segnalazione riguarda Arturo e Claude Code, non i bug del codice del progetto della persona:
per quelli proponi alla persona di scrivere `/diagnosi`.

**Cosa dice la persona**: $ARGUMENTS

## Passo 1 — Il tipo

Capisci il tipo dalle sue parole o dalla sessione: `problema`, `proposta` (idea o commento),
`integrazione`. Chiedi solo se non è chiaro.

Se riguarda la sicurezza (un segreto esposto, un modo per aggirare una guardia), fermati: non va
in una segnalazione pubblica. Indica la procedura privata:
https://github.com/stellakamikaze/arturo/blob/main/SECURITY.md

## Passo 2 — La bozza

Se la sessione contiene già il fatto (un errore appena visto, una correzione della persona, una
richiesta che Arturo non sa fare), scrivi tu la bozza e chiedi solo cosa manca. Altrimenti fai
queste domande, una per volta:

- **problema**: cosa stavi facendo? cosa ti aspettavi? cosa è successo invece? c'è un messaggio
  esatto? (il messaggio lo copi tu dalla sessione, se c'è)
- **proposta**: in quale situazione del tuo lavoro ti serve? come la immagini? (facoltativo)
- **integrazione**: quale strumento? per fare cosa, nel tuo lavoro? oggi come fai senza?

Prendi le informazioni sull'ambiente con:

```bash
python3 ~/.claude/bin/arturo segnala info
```

Scrivi la bozza in un file temporaneo, in markdown. Apre con "In breve", poi le stesse intestazioni
dei modelli di GitHub e un blocco finale "Ambiente" con l'output di `info`:

```markdown
### In breve
…
### Cosa stavi facendo?
…
### Cosa ti aspettavi che succedesse?
…
### Cosa è successo invece?
…
### Ambiente
Arturo: … · Claude Code: … · Sistema: …
```

**"In breve"** è la parte che chi mantiene Arturo legge per prima: una o due frasi, senza nomi di
file, di hook o di comandi. Dicono cosa non va o cosa serve, e cosa cambia per chi usa Arturo.
Esempio: "Durante il lavoro nel browser compaiono decine di avvisi di credenziali che non ci sono:
interrompono il lavoro e fanno pensare a una fuga che non c'è." I messaggi esatti e i comandi
restano sotto, nelle loro sezioni.

Per una proposta: "Quale problema vuoi risolvere, nel tuo lavoro?" e "Come immagini la
soluzione?". Per un'integrazione: "Quale strumento?", "Per fare cosa, nel tuo lavoro?", "Come
fai oggi, senza?".

**Togli tu quello che non deve uscire**: nomi di persone, clienti e organizzazioni, contenuti
di documenti ed email, indirizzi interni, nomi di file che dicono troppo. Lascia il fatto:
"un cliente" al posto del nome basta. Lo script toglie da solo le cartelle personali e ferma i
segreti, ma non riconosce un nome o un contenuto riservato: quello è il tuo lavoro.

Il titolo dice il fatto in poche parole comuni: "/fine si ferma al commit", non "Bug", e non
"commit-secret-gate.py dà scansione-fallita".

## Passo 3 — Anteprima

```bash
python3 ~/.claude/bin/arturo segnala prepara --tipo TIPO --titolo "TITOLO" --file BOZZA
```

- Con exit 3 la bozza contiene qualcosa che sembra un segreto: toglilo e rilancia.
- Con exit 0 mostra alla persona l'anteprima per intero, così come la stampa lo script.

Il canale è `arturo`: la segnalazione arriva direttamente a chi mantiene Arturo, senza account e
senza altri passi. Usa un altro canale solo se la persona lo chiede o se l'ha scelto prima
(`python3 ~/.claude/bin/arturo segnala canale` lo dice):

- `gh` o `web` se vuole una issue pubblica su GitHub;
- `email` se vuole mandarla lei, dal suo programma di posta.

Di' dove va, prima del sì:

- `arturo`: "Arriva solo a chi mantiene Arturo."
- `gh` e `web`: "Diventa una issue pubblica su GitHub: la vede chiunque."
- `email`: "Te la preparo negli appunti per federico@stellakamikaze.org: la mandi tu."

Chiedi: "La mando?". La persona può cambiare il testo o il canale. Un cambio del testo passa di
nuovo da `prepara`.

## Passo 4 — Invio, solo dopo il sì

```bash
python3 ~/.claude/bin/arturo segnala invia --canale CANALE --file PRONTA
```

`PRONTA` è il percorso stampato da `prepara` nella riga `PRONTA:`.

- `arturo`: è arrivata, e l'esito dice il suo numero ("è la segnalazione n. 19"). Dillo alla
  persona: chi mantiene Arturo la legge, e quando esce la correzione `/novita` la racconta con
  quel numero. Se il server non risponde, la segnalazione resta salvata e parte da sola alla
  prossima sessione: la persona non deve fare altro.
- `gh`: la issue si apre subito. Dai il link.
- `web`: si apre la pagina della issue già compilata. La persona controlla e preme Invia.
- `email`: il testo è negli appunti. La persona apre il suo programma di posta, incolla e invia.
  Tu non apri il programma di posta e non usi `mailto:`.

Se `invia` esce con 1, riporta l'errore e proponi un altro canale.

Chiudi con una riga: grazie, e dove è andata.
