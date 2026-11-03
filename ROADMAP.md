# La strada di Arturo

Aggiornata il 2026-11-03

Questa pagina dice su cosa lavora Arturo adesso, cosa viene dopo e cosa aspetta una decisione. La aggiorna chi mantiene Arturo, a ogni giro di lavoro. Le versioni uscite e le loro novità stanno in `NOVITA.md`. Ogni blocco ha il numero della versione con cui esce: oggi Arturo è alla 0.2, e la 1.0 sarà il rilascio pubblico.

Se una voce ti riguarda, o se manca qualcosa che ti serve, scrivilo sulla pagina della roadmap: https://arturo.stellakamikaze.org/roadmap/. Ogni voce ha il suo spazio per i commenti, e gli altri utenti li leggono.

<!--
Per le sessioni che sviluppano Arturo: questa è la mappa unica del lavoro (regola in docs/manutenzione.md).
Una sessione parte da una voce e il suo /fine aggiorna "Stato" della voce e la data in testa.
I task della voce stanno nel commento "task:", che il sito non mostra.
Forma di una voce: "### Titolo {#ancora}", poi "Stato: ...", poi i paragrafi, poi il commento dei task.
L'ancora non cambia mai: i commenti sul sito sono legati a lei.
-->

## Adesso (versione 0.3)

### Arturo diventa un plugin, separato dalle tue modifiche {#plugin}

Stato: in corso. Il pacchetto del plugin si genera dal repository. Mancano il passo in `/setup`, il metodo che arriva all'avvio e la prova su un Mac pulito.

Oggi Arturo vive nella stessa cartella delle tue modifiche, `~/.claude`. Per questo un aggiornamento può scontrarsi con un file che hai cambiato tu. Con il plugin, Arturo sta in una cartella sua e la tua parte personale resta tua: un aggiornamento cambia solo Arturo.

Chi oggi usa Arturo non nota niente finché non arriva il passaggio guidato (voce "Il passaggio al plugin").

<!-- task: #4531 #4532 #4566 #4567 #4568 #4565 -->

### Meno conferme, le stesse guardie {#conferme}

Stato: in corso. Una parte è scritta e aspetta il banco di prova.

Le guardie fermano i comandi rischiosi: cancellazioni, invii, segreti. Alcune chiedono conferma più volte per la stessa cosa, o su un file che stai già modificando. L'obiettivo è una conferma sola, dove serve davvero.

<!-- task: #4472 #4473 #4435 #4558 #3779 #4547 #4308 #3118 #3701 -->

### La testata di Arturo sotto quella di Claude Code {#testata}

Stato: in corso. La riga con versione e stato della configurazione è uscita nella 0.2.0; il blocco con la stella e la roadmap arriva con la 0.3.

All'avvio, subito sotto l'intestazione di Claude Code, compare il blocco di Arturo: il marchio con la stella, la versione, lo stato della configurazione e gli aggiornamenti in arrivo. Ogni due settimane, o quando questa pagina cambia, il blocco ti ricorda la roadmap. Gli avvisi dei controlli interni non compaiono più a ogni avvio.

L'intestazione di Claude Code, con la sua mascotte, non si può cambiare: nessuna impostazione e nessun mod la ridisegnano.

<!-- task: #4573 #4574 -->

### Le vostre segnalazioni {#segnalazioni}

Stato: in corso. Tre correzioni escono con il prossimo rilascio.

Ogni `/segnala` e ogni messaggio dal sito diventa un compito. Qui stanno quelli ancora aperti: comandi che si fermano, testi poco chiari, passi di installazione che non tornano.

<!-- task: #4068 #4071 #4074 #4099 #4102 #3842 #3845 #4103 #4187 #4545 #4190 -->

## Prossimo (versione 0.4)

### Aggiornamenti firmati anche con il plugin {#firma}

Stato: da fare, dopo il plugin.

Oggi Arturo si aggiorna da solo, ma installa soltanto i rilasci firmati da chi lo mantiene. Con il plugin la firma deve valere allo stesso modo: il plugin punta a un rilascio firmato, l'aggiornamento controlla la firma, e il controllo della configurazione confronta i file con un elenco firmato.

<!-- task: #4533 #3477 -->

### Il passaggio al plugin per chi usa già Arturo {#passaggio}

Stato: da fare, dopo la firma.

Un comando fa il passaggio in modo guidato: prima una prova che non tocca niente e ti mostra cosa cambia, poi una copia di sicurezza, poi il passaggio. Un secondo comando riporta tutto com'era. Parte solo dopo una decisione esplicita di chi mantiene Arturo.

<!-- task: #4534 -->

### Dove Arturo si blocca, detto dai numeri {#telemetria}

Stato: in corso a fasi. Le prime due fasi sono uscite.

La telemetria manda solo eventi: quale comando, quale guardia, quanto dura una sessione. Mai i tuoi testi, i tuoi file o le risposte di Claude. Le fasi che restano misurano dove le persone si fermano, e servono a migliorare Arturo. L'ultima fase parte solo dopo un parere legale sulla privacy.

<!-- task: #3925 #3926 #3928 #3400 #3435 #4548 #3499 #3930 -->

### Assistenti per ruolo: posta, agenda, archivio {#ruoli}

Stato: in corso. È uscita la parte che trova i tuoi strumenti collegati. Su dev c'è il primo avvio dello smistamento: /monitor ti mostra le fonti che sa leggere e tu scegli quali.

Ogni ruolo di un assistente diventa una skill di Arturo: smistare cosa ti arriva per urgenza, la posta, l'agenda, l'archivio dei documenti, e un osservatore che ti propone cosa delegare. Ogni skill ha una versione generica, e tu la adatti nella tua parte personale.

<!-- task: #4536 #4538 -->

## Dopo (versione 0.5 e oltre)

### Chi mantiene Arturo lo usa come voi {#autore}

Stato: da fare, dopo il passaggio dei primi utenti.

Oggi Arturo nasce dalla configurazione personale di chi lo mantiene. Dopo il plugin il verso si rovescia: anche quella configurazione diventa Arturo più una parte personale, come la vostra.

<!-- task: #4535 #4292 #4293 #4294 -->

### Sito e documentazione {#documentazione}

Stato: da fare.

Il README si apre con lo schema degli strati, e un capitolo spiega come estendere Arturo senza copiarlo. Il sito racconta il plugin. Il criterio: una persona nuova installa Arturo da una macchina pulita seguendo solo la documentazione.

<!-- task: #4537 #3373 #4439 -->

### Le viste dei tuoi compiti {#viste}

Stato: fermo, aspetta una decisione.

I tuoi compiti hanno già un archivio, un comando e una pagina locale. Un compito può aspettarne un altro fin da quando nasce, e ogni progetto ha una riga che dice a che punto è. Restano da scegliere la vista dei progetti e il pannello dentro Claude Code.

<!-- task: #3330 #3850 #3958 #3332 #4433 #3331 #3957 #3959 #3887 #3888 #3868 -->

### Arturo per le organizzazioni {#organizzazioni}

Stato: rinviato.

Uno strato sopra Arturo, curato da una persona di riferimento: le skill del mestiere, la voce e le regole di scrittura, i collegamenti agli strumenti dell'organizzazione. È stato progettato e poi rinviato il 16 ottobre 2026, per finire prima il plugin.

<!-- task: #2731 #2732 -->

## Da decidere

Queste voci aspettano una scelta di chi mantiene Arturo. Il lavoro collegato parte dopo.

- Su quale Mac e con quale account fare la prova del plugin da zero. <!-- task: #4565 -->
- Quando far partire il passaggio al plugin per chi usa già Arturo. <!-- task: #4534 -->
- Quale vista dei progetti tenere, e se tenere la pagina `/dafare`. <!-- task: #3330 #3850 -->
- Se i vecchi compiti di migrazione della configurazione personale sono superati dalla voce "Chi mantiene Arturo lo usa come voi". <!-- task: #4292 #4293 #4294 -->

## Uscito di recente

- 3 novembre 2026, versione 0.2.0: Arturo ha un numero di versione, la sessione si rinnova da sola a ogni passo finito, una riga di Arturo all'avvio, e in modalità auto un comando parte al primo colpo.
- 3 novembre 2026: la telemetria dice anche come usi Arturo, non solo quanto.
- 2 novembre 2026: `/inizio` capisce una frase, e un passo fermato diventa un comando per te.
- 1 novembre 2026: Arturo si installa incollando un link in Claude Code.
- 1 novembre 2026: le guardie chiudono i buchi trovati dalla revisione del 31 ottobre.
- 31 ottobre 2026: su Windows le guardie leggono il comando intero.
- 31 ottobre 2026: meno conferme sul tuo lavoro, le stesse guardie sui rischi veri.
