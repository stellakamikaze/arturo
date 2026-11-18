slug: briglia
passo: 3
titolo: Una briglia per Claude Code
sottotitolo: Arturo usa Claude e gli mette intorno regole scritte prima: in inglese si chiama harness, i finimenti del cavallo.
descrizione: Che cos'è un harness, cosa contiene Arturo, come le guardie chiedono conferma e come le sessioni si aprono e si chiudono in ordine.
---
Arturo usa Claude attraverso Claude Code, senza un altro modello. Quello che aggiunge è un harness, che in inglese sono i finimenti del cavallo, briglie comprese: istruzioni scritte prima, pensate per chi lavora con la conoscenza e non programma, che dicono a Claude cosa fare da solo e cosa chiedere, come chiudere la sera e da dove ripartire la mattina.

## Come è fatto

Il modello è l'IA che risponde. Claude Code gli dà le mani sul computer. Arturo aggiunge le regole e le abitudini, ed è la configurazione che uso ogni giorno, ripulita e messa in italiano: 32 guardie e automazioni, 11 comandi, 8 agenti e 7 skill.

{figura:anelli}

{figura:cassettiera}

## Le guardie

Claude Code lavora da solo sui file, ed è il motivo per cui conviene. Prima di un comando che cancella i tuoi file o li manda fuori dal computer, però, Arturo gli fa chiedere a te. Ogni comando passa da uno smistatore che chiama le guardie che servono: quasi sempre il comando passa, un gesto che non si annulla aspetta il tuo sì, un danno certo non parte. Se una guardia si rompe, chiede a te invece di lasciar passare.

{figura:guardie}

## La sera e la mattina

`/fine` controlla il lavoro, lo salva e scrive un appunto con il prossimo passo. `/inizio` lo rilegge il giorno dopo e ti dice da dove partire. Gli appunti sono file di testo sul tuo computer, quindi il lavoro non si perde fra una sessione e l'altra.

{figura:ritmo}

## Come lo uso io

Le abilità qui sotto le ho costruite io, chiedendole a Claude, e non sono dentro Arturo: Arturo ti dà il metodo per costruirti le tue.

{figura:uso}

## Gli aggiornamenti

Arturo si aggiorna da solo alla chiusura della sessione, come Claude Code, ma solo coi rilasci firmati da chi lo mantiene. Con `arturo aggiornamenti manuali` torni a confermarli uno per uno. Se hai Arturo come copia nella cartella di Claude Code (il clone), `/aggiorna indietro` riporta la versione di prima.

Fonti:
- [README di Arturo](https://github.com/stellakamikaze/arturo#readme)
- [Le guardie, spiegate](../../claude-code-sicurezza/)
