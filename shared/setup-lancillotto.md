# /setup, FASE 8d — Lancillotto (opzionale, solo Mac)

Lo legge `/setup` solo su un Mac: domanda, controlli e installazione di Lancillotto. Sta fuori dal
comando perché serve solo in questo caso, e il corpo di `/setup` entra intero nel contesto.

Chiedi: "Vuoi che Arturo impari da come lavori? Lancillotto è una piccola app per Mac che annota in
locale quali app, finestre e file usi, senza video, foto dello schermo o tasti. Dopo tre giorni Arturo
lo legge e ti propone al massimo tre lavori che ripeti e che può fare lui, con i numeri. Il registro
resta sul tuo Mac. La installo?"

Controlla prima se si può e se c'è già:

```bash
[ "$(uname -s)" = Darwin ] || echo "non è un Mac: Lancillotto non c'è"
[ -d ~/Applications/Lancillotto.app ] && echo "Lancillotto già installato" || echo "Lancillotto non installato"
gh repo view stellakamikaze/lancillotto >/dev/null 2>&1 && echo "repo raggiungibile" || echo "repo non raggiungibile"
```

- Se non è un Mac, o è già installato, dillo e vai avanti. Se è installato, ricorda che dalla sua
  finestra il tasto "Copia il prompt per Arturo" copia la domanda pronta.
- Se il repo non è raggiungibile, il problema è la rete o l'accesso a GitHub: controlla
  `gh auth status`, che la FASE 1 ha già preparato, e riprova.
- Solo dopo il sì dell'utente, scarica e installa. L'installatore compila l'app in circa un minuto,
  la mette in `~/Applications` e apre la sua guida:

  ```bash
  gh repo clone stellakamikaze/lancillotto ~/.local/share/lancillotto && ~/.local/share/lancillotto/installa.sh
  ```

  Poi spiega: "Si è aperta la guida di Lancillotto: ti chiede l'Accessibilità, l'unico permesso
  obbligatorio. Il testo delle finestre e l'invio dei dati d'uso sono a tua scelta. Lancillotto si
  aggiorna da solo una volta al giorno. Fra tre giorni scrivimi `dove mi puoi aiutare?`."
- Se l'utente dice no, salta: si installa anche più tardi con lo stesso comando.
