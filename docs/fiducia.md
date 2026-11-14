# La catena di fiducia del plugin

Questa pagina dice come Arturo controlla che un rilascio del plugin venga da chi lo mantiene. È lo strato Protezione applicato agli aggiornamenti, sul primo asse (Arturo). Il contratto degli strati sta in [`strati.md`](strati.md), il pacchetto e le prove in [`prove-plugin.md`](prove-plugin.md).

## Come funziona (F3, 5/11/2026)

Col clone la fiducia la dà git: si installa solo un tag firmato. Col plugin la cartella del codice è una copia senza git, e Claude Code installa lo sha scritto nel catalogo anche se nessun tag firmato lo indica (prova del 5/11/2026, Claude Code 2.1.318). Quattro pezzi chiudono il buco:

```
rilascio   impacchetta.py --firma → MANIFEST (sha256 di ogni file) + MANIFEST.sig, commit sul ramo plugin,
           tag firmato plugin-vN.N.N → impacchetta.py --catalogo → ramo catalogo: Arturo fissato a tag + sha
/aggiorna  aggiornamenti.py plugin: claude plugin marketplace update → scarica solo il tag → verify-tag con
           l'ancora → lo sha del tag è quello del catalogo? → versione non più vecchia? → claude plugin update
           → la copia installata ha lo sha verificato e torna col suo MANIFEST firmato? → APPLICATO
           un passo che non torna: POSSIBILE COMPROMISSIONE (uscita 3), niente update; firma che il
           computer non sa controllare: FIRMA NON VERIFICABILE (uscita 4)
chiusura   session-end.sh lancia aggiornamenti.py applica dalla copia accanto all'hook: la stessa strada di
           /aggiorna, con lo stesso lucchetto. Non rinvia: Claude Code tiene la copia di prima per le
           sessioni rimaste aperte. L'esito lo dice l'avvio dopo (10/11/2026)
avvio      deriva.py: la copia in uso ha il MANIFEST firmato? quali file non tornano? → riga DERIVA
telemetria versione dal plugin.json della copia, non dai tag del git dell'Orsa
```

- **L'avviso.** Al massimo una volta all'ora l'avvio e la barra in basso lanciano `aggiornamenti.py controlla`, dalla cartella del codice accanto a sé: col plugin scarica il catalogo e confronta la versione con quella installata, senza installare niente. Se è più nuova, la barra mostra "↑ Arturo <versione> · si installa alla chiusura" e l'avvio lo dice al modello; con gli aggiornamenti a mano mostra "serve /aggiorna" (#4860, banco `tests/test_avviso_plugin_2026_11_06.py`).
- **La chiusura.** Dal 10/11/2026 la chiusura della sessione installa il rilascio nuovo anche col plugin, con le verifiche di `/aggiorna`. Una firma che non torna o che il computer non sa controllare resta nello stato: l'avvio e la barra lo dicono finché un'installazione non riesce. Non si installa dopo un `/clear`, con gli aggiornamenti a mano, né da un checkout di sviluppo (banco `tests/test_chiusura_plugin_2026_11_10.py`). L'aggiornamento automatico di Claude Code per il catalogo `arturo` resta spento: installerebbe senza la verifica del tag.
- **L'ancora.** La chiave che verifica sta nell'Orsa, in `~/.claude/arturo/rilasci.allowed_signers`: chi cambia la copia del plugin cambierebbe anche la chiave dentro. La prima verifica riuscita la scrive; dopo cambia solo con una copia nuova verificata con la chiave di prima. Così una chiave nuova entra con un rilascio firmato dalla vecchia, come nel clone.
- **Lo spazio dei nomi.** Il MANIFEST si firma con `ssh-keygen -Y sign -n arturo-manifest`, da stdin: con un file, una `MANIFEST.sig` già presente resta com'era e `ssh-keygen` esce con 0 lo stesso. La chiave dei rilasci vale per `git` e `arturo-manifest` (`firme/rilasci.allowed_signers`).
- **Fuori dal MANIFEST** stanno solo la firma, la cartella `.in_use` che Claude Code aggiunge alla cache e i `__pycache__` che Python scrive accanto agli script.
- **Il catalogo** sta sul ramo `catalogo` del repository: la persona lo aggiunge con `claude plugin marketplace add stellakamikaze/arturo#catalogo`, e `main` resta il clone di chi l'ha installato così fino a F4.
- Il banco `tests/test_fiducia_2026_11_05.py` (FD01-FD09) prova tutto con la CLI vera, in un `CLAUDE_CONFIG_DIR` di prova: tag non firmato, firmato da un'altra chiave, sha dopo il tag, rilascio più vecchio, e un aggiornamento vX → vY che va a buon fine.
