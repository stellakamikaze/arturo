Bozza: la rilegge e la corregge Federico prima del rilascio su main.

# 04 — La memoria è tua

> Questo principio sta in una riga: **quello che Claude sa di te deve stare in file tuoi.**
> File che leggi, correggi e porti via quando vuoi.

## Claude non ricorda

Ogni sessione con Claude parte da zero. Non sa chi sei, su cosa lavori, cosa avete deciso ieri.
Sa soltanto quello che trova all'inizio della conversazione.

Quindi «la memoria» di un assistente è sempre un testo che qualcuno gli rilegge all'inizio. La
domanda vera è un'altra: **dove sta quel testo, e chi lo controlla?**

## Due posti possibili

Il primo posto è l'account del fornitore. Molte chat AI ricordano da sole: «ricordo che lavori
in una casa editrice». È comodo. Però quel ricordo vive sui computer di qualcun altro. Non sempre
puoi leggerlo tutto, correggerlo riga per riga o portarlo con te se cambi strumento.

Il secondo posto sono file sul tuo computer. Meno magici, perché li devi tenere in ordine. Però
li leggi come leggi una lettera, li correggi con un editor di testo, e restano tuoi anche il
giorno in cui lo strumento cambia nome, prezzo o padrone.

Arturo sceglie il secondo posto, per le ragioni del capitolo 00.

## Cosa ricorda Arturo, e dove

- **Le tue regole** stanno in `CLAUDE.md`: come vuoi le risposte, cosa non deve mai fare, la
  lingua. Claude lo legge all'inizio di ogni sessione.
- **Il punto in cui eri arrivato** sta negli handoff. A fine sessione `/fine` scrive cosa è
  fatto, cosa resta e chi deve muoversi. Alla sessione dopo `/inizio` lo rilegge e riparti da lì.
- **Le cose da fare** stanno nell'archivio dei todo (`arturo todo`), con scritto chi agisce.
- **Le tue aggiunte ai comandi** stanno in `personale/`. Gli aggiornamenti di Arturo non le
  toccano.
- **Le note che Claude Code prende da solo** diventano utili ovunque se accendi la memoria
  facoltativa (`arturo memoria accendi`). È spenta finché non la accendi tu. Legge le note dove
  sono, in `~/.claude/projects/*/memory/`, in `~/.claude/data/memory/` e nelle cartelle che
  aggiungi: non le copia e non le sposta.

Tutto questo è testo semplice dentro `~/.claude`, una cartella sul tuo computer. Niente sta su
un server, e niente della memoria entra nella telemetria. Se la cartella va in un tuo
repository privato, la ritrovi uguale su un altro computer.

## Una memoria che si controlla

Una memoria in file ha un vantaggio che quella nascosta non ha: la puoi rileggere.

Conviene farlo, perché Claude a volte scrive una nota sbagliata o troppo sicura. Una nota vecchia
che dice il falso è peggio di nessuna nota: Claude la prende per vera. Rileggi gli handoff quando
ripartono, e correggi una regola del `CLAUDE.md` appena smette di valere.

Arturo ti aiuta in due modi. Un controllo sempre acceso guarda ogni nota che Claude scrive, e
avvisa se dentro finiscono una password, una chiave o istruzioni nascoste. `arturo memoria
controlla` trova le note senza descrizione e i collegamenti rotti.

## Meno è meglio

Viene voglia di scrivere tutto: ogni preferenza, ogni eccezione, ogni lezione. Ma ogni riga in
più è una riga che Claude legge a ogni sessione, e che prima o poi invecchia. Per questo Arturo
ti avvisa quando il `CLAUDE.md` supera le duecento righe.

Una buona memoria somiglia a un quaderno tenuto bene: poche cose, vere, aggiornate. Quando una
regola non serve più, cancellala.

## La cosa da portarsi via

Chiediti: **se domani cambiassi strumento, cosa di quello che Claude sa di me potrei portarmi
via?** Se la risposta è «niente», la tua memoria vive in casa d'altri. Se la risposta è «una
cartella di file che conosco», la memoria è tua.

---

*Vuoi provarlo sul tuo lavoro? Chiedi a Claude uno sparring su «la memoria è tua».*
