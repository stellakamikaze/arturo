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
- Poi spiega: "Si è aperta la finestra di Arturo. Da ora lavori da lì: premi Nuova richiesta per
  scrivere a Claude, oppure scegli un progetto a sinistra. Questa conversazione puoi chiuderla." Fai
  la FASE 10 qui solo se la persona preferisce restare nel terminale.
- Se la persona dice no, salta: si installa più tardi con la stessa riga.
