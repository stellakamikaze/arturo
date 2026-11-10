# /setup col plugin (FASE 0)

Col plugin il codice di Arturo sta nella cartella dei plugin di Claude Code, e `~/.claude` è la
cartella della persona, non un repo di Arturo: è giusto così, e il resto della FASE 0 sul clone non vale.

Prima di andare avanti applica le impostazioni che un plugin non può portare (permessi, `env`, barra in basso, stile):
- mostra le voci che `stato` elenca e chiedi conferma, perché cambiano `~/.claude/settings.json`;
- col sì lancia `python3 ~/.claude/bin/arturo impostazioni applica`. La prima volta salva una copia in
  `settings.json.prima-di-arturo`, e il file di blocco `data/arturo-impostazioni.lock` ricorda cosa ha
  scritto Arturo: un aggiornamento cambia solo quelle voci;
- se dice che una voce è cambiata sia da te sia da Arturo, mostra le due versioni e chiedi quale tenere;
- se elenca hook doppi (li lascia un Arturo installato prima come clone), spiega che scatterebbero due
  volte e, col sì, lancia `applica --togli-doppi`. Gli hook tuoi, che il plugin non porta, restano;
- chiudi con `impostazioni stato`: deve dire "già applicate" senza hook doppi.
Il metodo di Arturo (`~/.claude/shared/metodo.md`) col plugin arriva da solo all'avvio di ogni sessione.

Salta anche la FASE 7: col plugin `~/.claude` non è un repository, e la sincronizzazione tra macchine di
`/setup` vale solo col clone. Dillo in una riga se la persona usa più computer. L'identità di Git della
FASE 1 invece vale: `identita-git.sh` non chiede un repository in `~/.claude`.
