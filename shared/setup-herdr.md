# /setup, prima della FASE 10 — Herdr, la finestra di Arturo

Lo legge `/setup` prima del primo lavoro. Herdr (herdr.dev, open source) è un'app che tiene le
sessioni di Claude in una finestra sola: a sinistra i progetti della persona, al centro la
conversazione, a destra i todo divisi fra lei e Claude. Chi non ha mai usato un terminale ci lavora
come in una chat. Sta fuori dal comando perché il corpo di `/setup` entra intero nel contesto.

Controlla prima se si può e se c'è già:

```bash
case "$(uname -s)" in
  Darwin) [ "$(sysctl -n hw.optional.arm64 2>/dev/null)" = 1 ] && echo "si può" || echo "Mac Intel: Herdr non c'è" ;;
  MINGW* | MSYS* | CYGWIN*) echo "si può (Windows)" ;;
  *) echo "Linux: per ora salta" ;;
esac
command -v herdr-app >/dev/null 2>&1 || [ -d ~/Applications/Herdr.app ] && echo "Herdr già installato" || echo "Herdr non installato"
```

- Mac Intel o Linux: dillo in una riga ("Arturo funziona lo stesso qui nel terminale") e passa alla FASE 10.
- Herdr già installato: non chiedere. Lancia l'installazione qui sotto, che non riscarica Herdr e aggiorna
  solo il layout di Arturo, e segui le righe che stampa come dopo un sì.
- Altrimenti chiedi una volta sola: "Ti installo Herdr? È la finestra dove vedi i tuoi progetti,
  cosa aspetta te e cosa sta facendo Claude, senza usare il terminale. È gratuita e open source, si
  aggiorna da sola da herdr.dev, e la sua telemetria la lascio spenta."
- Dopo il sì lancia l'installazione. Scarica Herdr dal sito ufficiale (che ne controlla firma e
  integrità), mette il layout di Arturo e apre la finestra:

  ```bash
  sh ~/.claude/shared/volta-celeste/installa-herdr.sh
  ```

  La riga `HERDR OK` vuol dire fatto. `HERDR NO` vuol dire che qui non si può: dillo e prosegui.
  `HERDR ERRORE` va mostrata com'è e non blocca il resto del setup.
- Se c'è la riga `HERDR FIRMA`, proponi il passo in una riga: "Perché il Mac ricordi i permessi
  della finestra anche dopo gli aggiornamenti, lancia nel tuo Terminale questo comando; ti chiede
  due volte la password del Mac." Mostra il comando della riga così com'è. Non lo lanci tu: segna un
  certificato come affidabile, ed è un'impostazione di sicurezza della persona. Se dice no, la
  finestra funziona lo stesso e macOS richiede i permessi dopo un aggiornamento.
- Se c'è la riga `HERDR NASCITA`, chiedi in una riga: "Vuoi che le sessioni che apri col comando claude
  nel terminale nascano in background? Lavori come prima, e la finestra le apre anche da un altro
  computer mentre lavorano." Col sì lancia tu il comando `metti` della riga e riporta le righe
  `NASCITA METTI`. Col no lancia il comando `no` della riga: la proposta non torna alle installazioni dopo.
  È l'unica strada per accenderla o spegnerla: l'installazione la propone e basta.
  Se il permesso di scrivere nei file di avvio della shell ti viene negato, mostra il comando alla
  persona: lo lancia lei nel suo terminale.
- Le righe `HERDR NASCITA FUNZIONE`, `HERDR NASCITA POLICY` e `HERDR NASCITA UTF16` mostrale come sono:
  la funzione, la policy di PowerShell e il profilo sono della persona, e li cambia lei.
- La riga `HERDR SERVIZIO` propone il servizio di Claude fisso: tiene vive le sessioni in background e
  parte a ogni accesso. Senza, la finestra lo accende da sola prima di ogni sessione nuova, e vale fino
  al riavvio del computer.
  - Su Windows chiedi in una riga: "Vuoi che il servizio che tiene vive le sessioni in background parta
    da solo a ogni accesso? Non apre finestre." Col sì lancia tu il comando `powershell` della riga e
    riporta le righe `SERVIZIO CLAUDE`. Si toglie con lo stesso comando e `-Togli` in fondo.
  - Sul Mac non lanciarlo adesso: prima macOS deve dare a `claude` l'accesso a Documenti, e lo dà la
    persona. Dillo in una riga: "Quando vuoi che il servizio parta da solo a ogni login, dai a claude
    l'accesso a Documenti in Impostazioni di Sistema, Privacy e sicurezza, File e cartelle, poi chiedimelo."
    Quando lo chiede, lo script fa ripartire anche herdr-core, e i terminali di Herdr si chiudono (le
    sessioni in background restano). Se questa conversazione gira in un terminale di Herdr, chiedi alla
    persona di riaprirla dal Terminale. Poi lancia `hc server stop`, il comando `sh` della riga, e
    riporta le righe `SERVIZI GUI`.
- Poi spiega: "Si è aperta la finestra di Arturo. Da ora lavori da lì: premi Nuova richiesta per
  scrivere a Claude, oppure scegli un progetto a sinistra. Questa conversazione puoi chiuderla." Fai
  la FASE 10 qui solo se la persona preferisce restare nel terminale.
- Se la persona dice no, salta: si installa più tardi con la stessa riga.
