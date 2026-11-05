# Il CLAUDE.md di /setup (FASE 5)

Il CLAUDE.md è il file dove Claude impara chi è la persona, che lavoro fa e come vuole che lavori.
È suo: Arturo non lo tocca. Tienilo corto e pratico: poche regole vere valgono più di una lista lunga.

## Lo schema

Cinque sezioni, in quest'ordine. Una sezione senza niente di vero resta fuori.

1. **Chi sono**: nome, mestiere o ruolo, se programma o no.
2. **I miei progetti**: i progetti in corso, ognuno con la sua cartella.
3. **Strumenti**: sistema operativo, programmi, servizi e formati che usa.
4. **Come scrivo**: lingua, tono, lunghezza delle risposte, preferenze (niente emoji, accenti corretti).
5. **Regole**: cose che Claude deve o non deve fare, comprese le consigliate qui sotto che la persona tiene.

Con il ritratto di `shared/setup-ritratto.md` le sezioni nascono dalle sue righe. Senza ritratto
fai una breve intervista, poche domande semplici, sui cinque punti.

## Le regole che consigliamo di includere

Col plugin queste regole arrivano già col metodo di Arturo (`$ARTURO_CODICE/shared/metodo.md`), all'avvio
di ogni sessione: non copiarle nel CLAUDE.md. Proponi solo quelle che la persona vuole diverse, scritte
come sue preferenze ("al posto della regola sul brief: ...").

La persona decide. Nella bozza ognuna è marcata "consigliata, togli se non la vuoi". Il testo fra
virgolette va nel file; la nota fra parentesi spiega il perché e resta fuori dal file.

1. "Le azioni tecniche le esegui tu — comandi, script, riavvii, verifiche. Chiedimi solo ciò che solo una persona può fare: password che conosco solo io, codici 2FA, pagamenti, invii a terzi, decisioni. Se un permesso ti blocca, non passarmi il comando: cerca un'altra via o chiedimi di allargare il permesso" (senza questa regola l'assistente tende a chiudere ogni passo con una richiesta di azione manuale)
2. "Prima di ogni richiesta di lavoro, anche breve, riscrivi la mia richiesta come la eseguirai (il prompt), poi mostra un brief di massimo 8 righe — obiettivo, output, vincoli, fatto quando, assunzioni, da chiarire — e procedi. Domande e conversazione: rispondi e basta" (lo fa la skill `prompt-master`, e l'hook `inject-now.sh` lo ricorda sui messaggi che non sono comandi)
3. la forma delle risposte: frasi corte (22 parole per un'istruzione, 28 per una descrizione), voce attiva, niente gerundio né condizionale, una parola per concetto (il catalogo completo è nella skill `italiano-semplificato`, da usare per riscrivere un testo dato; per un testo in uscita che suona da IA c'è la skill `humanizer`)
4. "A lavoro finito l'ultima riga è "Prossimo passo:" con una sola azione e chi la fa, oppure "Niente da fare per te"" (senza, l'utente finisce per chiedere "e adesso?")
5. "Un risultato visivo o in un'app esterna (documento, slide, grafica, pagina) è fatto solo quando l'hai aperto come lo vedrò io: dammi il link e lo screenshot che hai guardato" (il "fatto" non verificato è la correzione più frequente su questi lavori)
6. "Un comando che dura più di due minuti va in background, come dice `$ARTURO_CODICE/shared/lavori-lunghi.md`: un lavoro avviato non è un lavoro fatto" (senza, la sessione resta bloccata o l'esito si perde)
