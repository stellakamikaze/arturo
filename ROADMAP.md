# La strada di Arturo

Aggiornata il 2026-11-14

Questa pagina dice su cosa lavora Arturo adesso, cosa viene dopo e cosa aspetta una decisione. La aggiorna chi mantiene Arturo, a ogni giro di lavoro. Le versioni uscite e le loro novità stanno in `NOVITA.md`. Ogni blocco ha il numero della versione con cui esce: oggi Arturo è alla 0.2, e la 1.0 sarà il rilascio pubblico. Ogni voce dice il suo strato: Protezione, Metodo, Memoria, Collegamenti, Scoperta e Orsa, oppure Ingresso e Misura, che servono a tutti (`docs/strati.md`).

Se una voce ti riguarda, o se manca qualcosa che ti serve, scrivilo sulla pagina della roadmap: https://arturo.stellakamikaze.org/roadmap/. Ogni voce ha il suo spazio per i commenti, e gli altri utenti li leggono.

<!--
Per le sessioni che sviluppano Arturo: questa è la mappa unica del lavoro (regola in docs/manutenzione.md).
Una sessione parte da una voce e il suo /fine aggiorna "Stato" della voce e la data in testa.
I task della voce stanno nel commento "task:", che il sito non mostra.
Forma di una voce: "### Titolo {#ancora}", poi "Stato: ...", poi "Strato: ...", poi i paragrafi, poi il commento dei task.
L'ancora non cambia mai: i commenti sul sito sono legati a lei.
-->

## Adesso (versione 0.3)

### Arturo diventa un plugin, separato dalle tue modifiche {#plugin}

Stato: quasi finito. Il plugin si installa, si aggiorna solo da rilasci firmati e all'avvio porta le regole di Arturo. Manca la prova su un Mac pulito.

Strato: Ingresso.

Oggi Arturo vive nella stessa cartella delle tue modifiche, `~/.claude`. Per questo un aggiornamento può scontrarsi con un file che hai cambiato tu. Con il plugin, Arturo sta in una cartella sua e la tua parte personale resta tua: un aggiornamento cambia solo Arturo.

Chi oggi usa Arturo su Mac trova all'avvio, una volta al giorno, la proposta di provare il passaggio guidato: la prova non cambia niente (voce "Il passaggio al plugin"). Su Windows la proposta arriva quando il passaggio è provato anche lì.

<!-- task: #4531 #4532 #4566 #4567 #4568 #4565 -->

### Le correzioni della revisione di novembre {#revisione-novembre}

Stato: in corso. Prima le guardie su Windows: fatte le correzioni sui programmi scritti con `.exe` e in maiuscolo, sul Python che manca e sui comandi di Windows che cancellano o eseguono (`robocopy`, `reg delete`, PowerShell, `wsl`, node) e sull'avvio automatico (cartella Esecuzione automatica, profili PowerShell, `schtasks`, chiavi `Run` del registro, `sc create`) e sul codice Python e node che scrive la config (`open()`, `shutil.copy`, `write_text`, `writeFileSync`, archivi estratti).

Strato: Protezione.

Una revisione ha riletto i comandi, le skill e le guardie di Arturo. Ha trovato buchi veri, soprattutto su Windows: un programma scritto con `.exe` passava dalle guardie senza conferma, e una copia poteva smettere di aggiornarsi senza dirlo. Le correzioni escono a gruppi: prima le guardie, poi l'aggiornamento, la chiusura delle sessioni, i comandi, le segnalazioni, il peso dei testi e la forma.

<!-- task: #5123 #5124 -->

### Meno conferme, le stesse guardie {#conferme}

Stato: in corso. Una parte è scritta e aspetta il banco di prova.

Strato: Protezione.

Le guardie fermano i comandi rischiosi: cancellazioni, invii, segreti. Alcune chiedono conferma più volte per la stessa cosa, o su un file che stai già modificando. L'obiettivo è una conferma sola, dove serve davvero.

<!-- task: #4472 #4473 #4435 #4558 #3779 #4547 #4308 #3118 #3701 -->

### La testata di Arturo sotto quella di Claude Code {#testata}

Stato: in corso. La riga con versione e stato della configurazione è uscita nella 0.2.0; il blocco con la stella e la roadmap arriva con la 0.3.

Strato: Ingresso.

All'avvio, subito sotto l'intestazione di Claude Code, compare il blocco di Arturo: il marchio con la stella, la versione, lo stato della configurazione e gli aggiornamenti in arrivo. Ogni due settimane, o quando questa pagina cambia, il blocco ti ricorda la roadmap. Gli avvisi dei controlli interni non compaiono più a ogni avvio.

L'intestazione di Claude Code, con la sua mascotte, non si può cambiare: nessuna impostazione e nessun mod la ridisegnano.

<!-- task: #4573 #4574 -->

### I testi che scrivi con Claude suonano tuoi {#scrittura}

Stato: in corso. La skill `humanizer` è su dev ed esce con il prossimo rilascio.

Strato: Metodo.

Un post, un'email o una proposta scritti con Claude si riconoscono: contrasti inventati, chiuse a effetto, elenchi di tre, parole gonfie. La skill `humanizer` li toglie senza cambiare cosa dice il testo, e segue il tuo modo di scrivere. È l'adattamento italiano di un progetto open source di blader, e prende il posto del catalogo dei tic che Arturo aveva dentro la skill dell'italiano semplificato.

<!-- task: #4695 -->

### Le vostre segnalazioni {#segnalazioni}

Stato: in corso. Tre correzioni escono con il prossimo rilascio.

Strato: Misura.

Ogni `/segnala` e ogni messaggio dal sito diventa un compito. Qui stanno quelli ancora aperti: comandi che si fermano, testi poco chiari, passi di installazione che non tornano.

<!-- task: #4068 #4071 #4074 #4099 #4102 #3842 #3845 #4103 #4187 #4545 #4190 -->

## Prossimo (versione 0.4)

### Arturo ti propone cosa automatizzare {#scoperta}

Stato: in corso. La prima versione è pronta sul ramo di sviluppo `dev` ed esce col prossimo rilascio. Comprende il comando `arturo scoperta`, l'indice che si aggiorna dopo ogni modifica, l'impronta dei file presa da `/inizio` e la proposta che arriva con `/fine`. Per ora non manda niente alla telemetria: i conteggi partiranno solo quando sarà pubblicato il testo nuovo sulla privacy.

Strato: Scoperta.

Claude Code tiene già una copia di ogni versione dei file che modifichi con lui. Arturo le legge e cerca le ripetizioni: lo stesso file cambiato a intervalli regolari, gli stessi campi riscritti, gruppi di file toccati insieme. A fine lavoro, in `/fine`, ti propone un'automazione con le prove: le date, le modifiche, una bozza da leggere. Le proposte sono al massimo una per sessione e due a settimana. Se dici sì, la bozza diventa una skill o una routine, che puoi sempre annullare; se dici no, la stessa proposta non torna. Le versioni dei file e le bozze restano sul tuo computer: alla telemetria arriveranno solo i conteggi delle proposte fatte, accettate e annullate, dopo il testo nuovo della privacy.

<!-- task: #5615 -->

### Il passaggio al plugin per chi usa già Arturo {#passaggio}

Stato: pronto. Il comando è `arturo migra`. Su Mac l'avvio propone la prova, e il passaggio lo lanci tu, a mano. Chi mantiene Arturo decide quando chiederlo a tutti.

Strato: Ingresso.

Un comando fa il passaggio in modo guidato: prima una prova che non tocca niente e ti mostra cosa cambia, poi una copia di sicurezza, poi il passaggio. Un secondo comando riporta tutto com'era. Il passaggio vero parte solo se lo lanci tu da un Terminale.

<!-- task: #4534 -->

### Dove Arturo si blocca, detto dai numeri {#telemetria}

Stato: in corso a fasi. Le prime due fasi sono uscite.

Strato: Misura.

La telemetria manda solo eventi: quale comando, quale guardia, quanto dura una sessione. Mai i tuoi testi, i tuoi file o le risposte di Claude. Le fasi che restano misurano dove le persone si fermano, e servono a migliorare Arturo. L'ultima fase parte solo dopo un parere legale sulla privacy.

<!-- task: #3925 #3926 #3928 #3400 #3435 #4548 #3499 #3930 -->

### Assistenti per ruolo: posta, agenda, archivio {#ruoli}

Stato: in corso. È uscita la parte che trova i tuoi strumenti collegati. Su dev c'è il primo avvio dello smistamento: /monitor ti mostra le fonti che sa leggere e tu scegli quali.

Strato: Collegamenti.

Ogni ruolo di un assistente diventa una skill di Arturo: smistare cosa ti arriva per urgenza, la posta, l'agenda, l'archivio dei documenti, e un osservatore che ti propone cosa delegare. Ogni skill ha una versione generica, e tu la adatti nella tua parte personale.

<!-- task: #4536 #4538 -->

## Dopo (versione 0.5 e oltre)

### Chi mantiene Arturo lo usa come voi {#autore}

Stato: da fare, dopo il passaggio dei primi utenti.

Strato: Orsa.

Oggi Arturo nasce dalla configurazione personale di chi lo mantiene. Dopo il plugin il verso si rovescia: anche quella configurazione diventa Arturo più una parte personale, come la vostra.

<!-- task: #4535 #4292 #4293 #4294 -->

### Sito e documentazione {#documentazione}

Stato: in corso. Il README è riordinato, e `docs/strati.md` descrive i due assi per chi sviluppa Arturo. Restano il sito e la prova da una macchina pulita.

Strato: Ingresso.

Il README parte da cosa fa Arturo, e `docs/strati.md` spiega come estendere una skill senza copiarla. Resta il sito, che deve raccontare il plugin. Il lavoro è finito quando una persona nuova installa Arturo su una macchina pulita seguendo solo la documentazione.

<!-- task: #4537 #3373 #4439 -->

### Le viste dei tuoi compiti {#viste}

Stato: fermo, aspetta una decisione.

Strato: Memoria.

I tuoi compiti hanno già un archivio, un comando e una pagina locale. Un compito può aspettarne un altro fin da quando nasce, e ogni progetto ha una riga che dice a che punto è. Restano da scegliere la vista dei progetti e il pannello dentro Claude Code.

<!-- task: #3330 #3850 #3958 #3332 #4433 #3331 #3957 #3959 #3887 #3888 #3868 -->

### Arturo per le organizzazioni {#organizzazioni}

Stato: rinviato.

Strato: Orsa.

Uno strato sopra Arturo, curato da una persona di riferimento: le skill del mestiere, la voce e le regole di scrittura, i collegamenti agli strumenti dell'organizzazione. È stato progettato e poi rinviato il 16 ottobre 2026, per finire prima il plugin.

<!-- task: #2731 #2732 -->

## Da decidere

Queste voci aspettano una scelta di chi mantiene Arturo. Il lavoro collegato parte dopo.

- Su quale Mac e con quale account fare la prova del plugin da zero. <!-- task: #4565 -->
- Quando far partire il passaggio al plugin per chi usa già Arturo. <!-- task: #4534 -->
- Quale vista dei progetti tenere, e se tenere la pagina `/dafare`. <!-- task: #3330 #3850 -->
- Se i vecchi compiti di migrazione della configurazione personale sono superati dalla voce "Chi mantiene Arturo lo usa come voi". <!-- task: #4292 #4293 #4294 -->

## Uscito di recente

- 6 novembre 2026, versione 0.2.6: col plugin vedi quando esce un rilascio nuovo, e hai tre comandi per mettere in ordine la tua copia dopo il passaggio.
- 5 novembre 2026, versione 0.2.5: Arturo si installa come plugin da rilasci firmati, e `arturo migra` porta al plugin chi ha già una copia.
- 3 novembre 2026, versione 0.2.0: Arturo ha un numero di versione, la sessione si rinnova da sola a ogni passo finito, una riga di Arturo all'avvio, e in modalità auto un comando parte al primo colpo.
- 3 novembre 2026: la telemetria dice anche come usi Arturo, non solo quanto.
- 2 novembre 2026: `/inizio` capisce una frase, e un passo fermato diventa un comando per te.
- 1 novembre 2026: Arturo si installa incollando un link in Claude Code.
- 1 novembre 2026: le guardie chiudono i buchi trovati dalla revisione del 31 ottobre.
- 31 ottobre 2026: su Windows le guardie leggono il comando intero.
- 31 ottobre 2026: meno conferme sul tuo lavoro, le stesse guardie sui rischi veri.
