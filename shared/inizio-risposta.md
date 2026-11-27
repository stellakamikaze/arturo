# /inizio · la risposta della persona

`/inizio` legge questo file nella FASE 6, quando la persona risponde alla ripartenza. Ogni voce è un caso:
segui quello della sua risposta.

- **Correzioni.** "8 a te" o "7 scarta" vanno subito nell'archivio, e riporti la riga di conferma:
  `python3 $ARTURO_CODICE/bin/arturo todo modifica ID --chi tu|decidi|io` oppure
  `python3 $ARTURO_CODICE/bin/arturo todo scarta ID "motivo"`, col motivo nelle sue parole. Non spostare un
  todo da tu a io o decidi senza un suo sì.
- **"tutto il delegabile".** Esegui in sessione, uno dopo l'altro, i todo "Faccio io" reversibili,
  stime comprese dopo il suo sì. Chiudi ognuno solo dopo aver controllato il risultato vero (il test
  che passa, il file che c'è, la pagina che si apre): poi `arturo todo fatto ID`. Di un "Preparo io,
  poi tu" fai la tua parte e il todo resta aperto. Davanti a un'azione con effetti che non si annullano
  (un invio, un pagamento, una cancellazione) ti fermi e chiedi.
- **Un filone o dei numeri.** Parti da quei todo. Il task di sessione (`TaskCreate`) nasce solo per
  i todo scelti: due numerazioni insieme confondono i numeri.
- **La risposta dalla checklist di Volta.** Arriva come un messaggio della persona, con i numeri della
  ripartenza: "Lavora su 2 5. Già fatto: 3. Scartati: 4. Rimandati: 6. A Claude: 7. A me: 8. Note: 2:
  testo. Nota generale". Ogni parte vale come se la persona l'avesse scritta a parole. "Lavora su" sono
  i numeri da cui parti. "Già fatto" chiude il todo con `arturo todo fatto ID`: lo dice la persona, e
  non serve un controllo tuo. "Scartati" usa `arturo todo scarta ID "<motivo>"`, col motivo dalla sua
  nota o "scartato dalla checklist". "Rimandati" usa `arturo todo modifica ID --quando "più avanti"`. "A
  Claude" usa `--chi io`, "A me" usa `--chi tu`. Una nota sotto un numero vale per quel todo, la nota
  generale per tutta la sessione. Una riga senza todo (`id` nullo) si tratta a parole. Riporta in una
  riga cosa hai scritto nell'archivio, poi parti da "Lavora su".
- **"Lavora su tutto".** Arriva dalla checklist di Volta col pulsante "Su tutto" acceso. È una passata di
  scrematura sull'elenco intero. Per ogni voce aperta: se è già fatta, controlla il risultato vero e
  chiudila (`arturo todo fatto ID`); se è superata, scartala col motivo (`arturo todo scarta ID
  "<motivo>"`). Poi esegui i "Faccio io" reversibili, uno dopo l'altro, come per "tutto il delegabile".
  Alla fine riporta il conto: chiusi, scartati, fatti, rimasti per la persona. I gesti espliciti del
  messaggio (Già fatto, Scartati, Rimandati, le note) vincono sulla passata. Davanti a un'azione con
  effetti che non si annullano ti fermi e chiedi.
- **La risposta all'intervista.** Riscrivi la risposta in una o due frasi coi fatti della persona, senza
  aggiungerne. Mostrala e chiedi: "La salvo nella memoria?". Solo col sì lancia
  `python3 $ARTURO_CODICE/bin/arturo intervista risposta <id> --testo "<le frasi approvate>"`: la nota entra
  come `persona-<id>` e la annuncia `/fine`. Se la risposta dice il mestiere, fissa anche la famiglia con
  `arturo intervista famiglia <1-6>`. Con **salta** lancia `arturo intervista salta <id>`. Con "basta
  domande" lancia `arturo intervista spegni`. Un no al salvataggio non salva niente, e la domanda può
  tornare un altro giorno.
- **La skill dal lavoro che torna.** [solo se `arturo intervista risposta` stampa la riga `SKILL`] La
  persona ha appena detto quale lavoro rifà ogni settimana o ogni mese. Chiedile, una volta sola: "Vuoi
  che ne faccia una skill tua, così non me lo rispieghi ogni volta?". Col sì apri con Read
  `$ARTURO_CODICE/skills/creaskill/SKILL.md` e seguilo: la sua risposta vale come domanda 1 e riparti dalla 2. Poi
  lancia `arturo intervista skill si`. Col no lancia `arturo intervista skill no`. La riga `SKILL` esce
  una volta sola: senza risposta non richiedere.
- **La risposta alla proposta di uno spazio.** Col sì esegui il passo della riga `col sì` di `SPAZIO`:
  per Melchior accendi la memoria;
  per l'Orsa scrivi la regola in una riga, mostrala e solo col suo sì sul testo aggiungila al suo
  `CLAUDE.md`. Poi lancia `python3 $ARTURO_CODICE/bin/arturo spazi si <spazio>`. Col no lancia
  `arturo spazi no <spazio>`, con "basta proposte" `arturo spazi spegni`. Senza risposta non fare niente:
  la proposta non torna comunque.
- **Il nome.** Se la persona vuole chiamare Arturo in un altro modo ("chiamati Bruno"), lancia
  `python3 $ARTURO_CODICE/bin/arturo nome "<nome>"`: il nome sta nell'Orsa e l'avvio lo ripete a ogni sessione.
  Da subito usalo quando parli di te.
- **"qualcosa non torna".** Se la persona dice che Arturo o il progetto non funzionano come si
  aspetta, apri con Read `$ARTURO_CODICE/skills/diagnosi/SKILL.md` e seguilo.
