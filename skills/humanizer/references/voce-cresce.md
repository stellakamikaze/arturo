# La voce cresce con l'uso

Parte della skill `humanizer` (`../SKILL.md`): si legge quando manca il file della voce o quando la
persona corregge un testo riscritto.

Il file `personale/humanizer.md` è della persona: lo scrivi solo dopo il suo sì, e un aggiornamento
di Arturo non lo tocca mai.

- **Se manca**, proponi `/voce` in una riga: costruisce la sua voce con qualche testo suo, una prova e
  il suo sì (`~/.claude/commands/voce.md`). Col sì lancia `/voce`, poi torna al testo. Se vuole andare
  avanti senza, scrivi il testo e dille che segue le regole generali di questa skill, non la sua voce.
  Il file lo compone `/voce` col modello `voce-modello.md`, con le quattro parti.
- **Mai un'altra persona come modello**: la voce si ricava dai testi di chi firma. Il nome di un'altra
  persona entra solo se lei lo chiede esplicitamente, e allora lo scrivi con le sue parole.
- **Quando la persona corregge** un testo che hai riscritto ("io avrei scritto...", una sua versione
  incollata, una parola cambiata), proponi di aggiungere una riga in `## Le mie correzioni`, con il prima
  e il dopo insieme: `- Prima: "..." — Dopo: "..."`. Se tre correzioni dicono la stessa cosa, proponi la regola in `## Le mie
  regole` al posto delle tre.
- Mostra sempre il testo che aggiungeresti, poi scrivi solo col sì.
