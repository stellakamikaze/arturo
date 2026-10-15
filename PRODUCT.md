# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users
Una persona sola che usa Arturo ogni giorno: un autore che lavora con Claude Code come sviluppatore principale e tiene nello stesso archivio di todo il lavoro di studio, i prodotti propri, gli strumenti e la vita personale. Apre la pagina dei progetti dal Mac e spesso dall'iPhone. Il lavoro principale che ci fa è governare tutti i progetti: vedere lo stato di ognuno, cosa è fermo e cosa si muove, come in una revisione settimanale. Ripartire al mattino e smistare i todo sono lavori secondari.

## Product Purpose
Arturo è un harness per Claude Code: guardie, memoria, todo condivisi fra la persona e Claude. La pagina dei progetti legge lo stesso archivio di Claude e di `arturo todo` e lo rende governabile: per ogni progetto i todo aperti, chi agisce, cosa è scaduto, cosa è fermo, il prossimo passo. Successo: in un minuto la persona sa quali progetti chiedono lei, quali sono fermi e quali stanno andando da soli.

## Positioning
Ogni todo dice chi agisce: «tocca a te», «decidi tu, poi faccio io», «faccio io», oppure «fermo». La pagina divide il lavoro fra la persona e Claude, cosa che un gestore di task generico non fa.

## Operating Context
Scala reale di un'istanza in uso (15/10/2026): circa 1.000 todo aperti e 1.000 chiusi, 40 progetti in 4 categorie. Due terzi dei todo toccano alla persona, un quinto a Claude, un decimo aspetta una decisione. Una cinquantina sono scaduti. Pochi progetti grandi (oltre 100 todo) convivono con molti piccoli (1-10). I nomi di progetto e di categoria vengono dall'archivio: la pagina non li conosce in anticipo.

## Capabilities and Constraints
- Dati: `/api/vista` e `/api/todo` in lettura, scritture solo via `/api/azione` (aggiungi, fatto, cambia chi, priorità, scadenza).
- Per ogni progetto: aperti, scaduti, fermi, chiusi, e i todo con titolo, scadenza, priorità, chi. I todo chiusi non portano la data di chiusura.
- La pagina gira anche in locale senza rete: niente risorse esterne, font nel repository, niente innerHTML.
- Italiano, frasi corte, nessun gergo tecnico nell'interfaccia.

## Brand Commitments
Nome Arturo, la stella dei naviganti. Il mondo visivo attuale (carta, Sorts Mill Goudy, Atkinson, una stella arancio) è della landing; per questa pagina la persona ha aperto l'esplorazione a mondi diversi (15/10/2026), con ritorno nel mondo di Arturo dopo la scelta.
