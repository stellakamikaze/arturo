---
description: Manda a chi mantiene Arturo un problema, un'idea o una richiesta di integrazione - Claude la scrive, la manda e ti dice cosa è partito e come ritirarla
argument-hint: "[cosa vuoi segnalare] | stato (opzionale)"
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

## Due modi

- **Automatico**, il modo di default dall'11/11/2026. Scrivi la bozza e la mandi con `manda`, senza chiedere
  "La mando?". Subito dopo dici alla persona, in una riga, cosa è partito, il numero e come ritirarla. Vale anche
  quando la persona non ha scritto `/segnala`: un guasto di Arturo visto nella sessione, una sua correzione a un tuo
  comportamento, una cosa che Arturo non sa fare. Una volta per fatto.
- **A mano**. Mostri l'anteprima, chiedi "La mando?" e mandi solo dopo il sì. La persona lo sceglie con
  `python3 ~/.claude/bin/arturo segnalazioni manuali` (o con la variabile `ARTURO_SEGNALAZIONI=manuali`), e torna
  indietro con `arturo segnalazioni automatiche`. Vale da solo anche per chi ha detto `arturo segnala basta`, ha spento
  la telemetria o ha scelto un canale diverso da `arturo`.

Non devi capire tu quale modo vale: lancia sempre `manda` (Passo 4). Se serve il sì, lo dice lui con l'uscita 4.

In nessun modo parte da sola una segnalazione che riguarda la sicurezza (Passo 1), che contiene un segreto, o che
porta nomi di persone, clienti o contenuti di lavoro: quelli li togli tu dalla bozza (Passo 2).

Se la persona scrive `stato`, o chiede che fine hanno fatto le sue segnalazioni, lancia
`python3 ~/.claude/bin/arturo segnala stato` e racconta l'elenco: in attesa, arrivate, corrette
(con la novità che le racconta), e per quelle con la ricevuta lo stato e la risposta di chi mantiene
Arturo, con le sue parole. Poi fermati.

Se chi mantiene Arturo chiede altre informazioni (stato "serve-info"), o la persona vuole aggiungere
qualcosa a una segnalazione partita, scrivi con lei l'aggiunta in un file temporaneo e lancia
`python3 ~/.claude/bin/arturo segnala seguito N --file AGGIUNTA`. Lo script pulisce il testo come
`prepara` e mostra cosa partirebbe: mostralo, chiedi "La mando?", e solo dopo il sì rilancia lo stesso
comando con `--conferma`.

Se la persona vuole ritirare una segnalazione, lancia `python3 ~/.claude/bin/arturo segnala ritira N`,
riporta cosa succede (dal server spariscono titolo, testo, pacchetto e aggiunte; restano numero, tipo e
data) e solo dopo il suo sì rilancia con `--conferma`.

Seguito e ritiro funzionano solo con la ricevuta: le segnalazioni partite da questo computer col canale
`arturo` dal 4/11/2026. Con exit 3 la ricevuta non c'è: proponi una segnalazione nuova che cita il numero.

## Passo 1 — Il tipo

Capisci il tipo dalle sue parole o dalla sessione: `problema`, `proposta` (idea o commento),
`integrazione`. Chiedi solo se non è chiaro.

Se riguarda la sicurezza (un segreto esposto, un modo per aggirare una guardia), fermati: non parte
da sola e non va in una segnalazione pubblica. Indica alla persona la procedura privata:
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
dei modelli di GitHub e un blocco finale "Ambiente" con l'output di `info`. Le versioni e lo stato
della config partono anche nel pacchetto tecnico, ma il blocco "Ambiente" resta: è l'unico
che arriva con i canali `gh`, `web` ed `email`.

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

**Togli tu quello che non deve uscire**, sempre, e con più cura adesso che nessuno rilegge prima dell'invio: nomi di persone, clienti e organizzazioni, contenuti
di documenti ed email, indirizzi interni, nomi di file che dicono troppo. Lascia il fatto:
"un cliente" al posto del nome basta. Lo script toglie da solo cartelle personali, email, indirizzi
web esterni, indirizzi IP, nomi di computer della rete e nomi di documenti, e ferma i segreti, ma non
riconosce un nome o un contenuto riservato: quello è il tuo lavoro.

Se il problema ha un messaggio d'errore lungo (un traceback, l'uscita di un comando), non metterlo
intero nella bozza: salvalo in un altro file temporaneo e passalo a `manda` con `--errore FILE`.
Entra nel pacchetto tecnico. Prima rileggilo tu: se porta nomi, clienti o contenuti di lavoro, taglia quelle righe.

Il titolo dice il fatto in poche parole comuni: "/fine si ferma al commit", non "Bug", e non
"commit-secret-gate.py dà scansione-fallita".

## Passo 3 — È già partita?

La stessa segnalazione può partire più volte, da sessioni diverse che non si vedono fra loro. Prima
di mandarla guarda quelle già partite da questo computer:

```bash
python3 ~/.claude/bin/arturo segnala precedenti
```

Confronta tu il fatto, non le parole. Lo stesso problema raccontato con altre parole è un doppione.
Due problemi diversi nello stesso comando non lo sono.

- Se nessuna racconta lo stesso fatto, vai avanti senza dirlo.
- Se una lo racconta, non parte niente di nuovo. Dillo alla persona con numero e data: "È già la n. 46,
  partita il 3/11." Poi fermati.
- Se la sessione porta un fatto in più (un caso diverso, un messaggio esatto, un'altra versione) e la n. 46 ha la
  ricevuta, proponi di aggiungerlo con `seguito`, che chiede il suo sì. Senza ricevuta manda una segnalazione
  nuova: "In breve" apre con "Si aggiunge alla n. 46 del 3/11:" e il testo tiene solo il nuovo.

## Passo 4 — Invio

```bash
python3 ~/.claude/bin/arturo segnala manda --tipo TIPO --titolo "TITOLO" --file BOZZA [--errore FILE]
```

- Aggiungi `--origine` quando la segnalazione nasce altrove: `fine` dalla FASE 10 di `/fine`, `avvio` da una
  riga dell'avvio (SEGNALA, banchi rossi) o da un fatto che hai visto tu nella sessione. Senza, vale `segnala`.
  Dice a chi mantiene Arturo da dove arrivano le segnalazioni.
- `manda` pulisce la bozza come `prepara`, aggiunge il pacchetto tecnico con le caselle di default (ambiente,
  banchi, config) e la manda sul canale `arturo`: arriva solo a chi mantiene Arturo. Non accetta `--tieni`:
  quello che lo script toglie resta fuori da un invio senza domanda.
- Il contatto. Se la persona ha dato nome ed email con `arturo contatto`, parte con la segnalazione. Se non ha
  ancora risposto alla domanda sul contatto, la segnalazione parte senza: non fare la domanda adesso.

**Uscita 0**: è partita. La prima riga è "Segnalato n. X: titolo. Per ritirarla: arturo segnala ritira X".
Dillo alla persona in una riga, con le tue parole: cosa hai segnalato, il numero, e che la ritira quando vuole.
Esempio: "Ho segnalato a chi mantiene Arturo che /fine si ferma al commit: è la n. 71. Se non la vuoi, dimmi
ritirala." Poi torna al lavoro. Altre due righe possibili, sempre con uscita 0:

- "Segnalato, in coda": il server non risponde, parte da sola alla prossima sessione. Dillo così.
- "Già segnalata": la stessa è partita nelle ultime 24 ore. Di' il numero e non rimandarla.

**Uscita 3**: la bozza o il pacchetto contengono qualcosa che sembra un segreto. Non è partita. Toglilo dalla
bozza e rilancia `manda`.

**Uscita 4**: serve il sì della persona. La riga `DOMANDA:` dice perché: modo manuale, avviso non ancora letto,
un nome di documento da controllare, tetto di dieci in un giorno. Sopra c'è l'anteprima. Vai al Passo 5.

**Uscita 1**: il server l'ha rifiutata. Riporta l'errore e proponi il canale `web` o `email` (Passo 5).

## Passo 5 — A mano: anteprima, sì, invio

Vale dopo un'uscita 4, o quando la persona chiede di vedere il testo prima, di cambiarlo o di usare un altro canale.

- Mostra alla persona l'anteprima per intero, così come la stampa lo script: il testo, la riga "Tolto dal testo"
  e la riga "Da controllare" se ci sono, e il pacchetto tecnico con le sue caselle. Le caselle accese di default
  sono ambiente, banchi e config; deriva, errore (acceso se hai passato `--errore`) e "collega ai miei dati
  d'uso" sono spente. Dillo in una riga: "Con la segnalazione parte un pacchetto tecnico, qui sotto: puoi
  spegnere o accendere ogni casella."
- Se la persona cambia il testo o le caselle, passa da `prepara`, che prende le stesse opzioni di `manda` più
  `--tieni` e stampa la stessa anteprima:

  ```bash
  python3 ~/.claude/bin/arturo segnala prepara --tipo TIPO --titolo "TITOLO" --file BOZZA [--errore FILE]
  ```

  Le caselle: `--pacchetto` e le voci accese separate da virgole (`--pacchetto ambiente,deriva`, o `--pacchetto
  nessuna`). Se una cosa tolta serve a capire il problema (l'indirizzo di un sito pubblico, per esempio), rilancia
  con `--tieni` e la categoria che l'anteprima nomina, solo col sì della persona. Con "Da controllare" guarda i
  nomi di documenti: se la parola prima è parte del nome, toglila dalla bozza e rilancia `prepara`.
- Il contatto. Se l'anteprima ha la riga "Contatto per gli sviluppatori di Arturo", mostrala: parte con la
  segnalazione del canale `arturo` e serve a ricontattarla. Se la persona non lo vuole per questa, rilancia
  `prepara` con `--senza-contatto`. Se l'anteprima ha una riga `CONTATTO:`, la persona non ha ancora risposto
  alla domanda: falla con le parole della riga, prima del "La mando?", poi rilancia `prepara`. Non insistere
  dopo un no.

Il canale è `arturo`: la segnalazione arriva direttamente a chi mantiene Arturo, senza account e
senza altri passi. Usa un altro canale solo se la persona lo chiede o se l'ha scelto prima
(`python3 ~/.claude/bin/arturo segnala canale` lo dice):

- `gh` o `web` se vuole una issue pubblica su GitHub;
- `email` se vuole mandarla lei, dal suo programma di posta.

Di' dove va, prima del sì:

- `arturo`: "Arriva solo a chi mantiene Arturo."
- `gh` e `web`: "Diventa una issue pubblica su GitHub: la vede chiunque."
- `email`: "Te la preparo negli appunti per federico@stellakamikaze.org: la mandi tu."

Chiedi: "La mando?". Solo dopo il sì:

```bash
python3 ~/.claude/bin/arturo segnala invia --canale CANALE --file PRONTA
```

`PRONTA` è il percorso della riga `PRONTA:` dell'anteprima. `invia` manda solo quel file, così com'è: se è
cambiato dopo l'anteprima risponde con exit 2, e si rilancia `prepara`.

- `arturo`: è arrivata, e l'esito dice il suo numero ("è la segnalazione n. 19"). Dillo alla persona.
- `gh`: la issue si apre subito. Dai il link.
- `web`: si apre la pagina della issue già compilata. La persona controlla e preme Invia.
- `email`: il testo è negli appunti. La persona apre il suo programma di posta, incolla e invia.
  Tu non apri il programma di posta e non usi `mailto:`.

Se `invia` esce con 1, riporta l'errore e proponi un altro canale.

## Dopo l'invio

Chi mantiene Arturo legge la segnalazione e può rispondere. La riga "Ricevuta" dice che il codice per leggere la
risposta è salvato sul computer della persona: quando la risposta arriva, l'avvio di una sessione lo dice (riga
SPORTELLO) e `/segnala stato` la mostra. Quando esce la correzione `/novita` la racconta con quel numero.

Chiudi con una riga: dove è andata, e grazie se la segnalazione l'ha chiesta la persona.
