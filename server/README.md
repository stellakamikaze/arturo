# Il server di Arturo

Un Worker Cloudflare con un database D1. Riceve quattro cose e solo quelle:

- `POST /v1/eventi`: un lotto di eventi d'uso con un id di installazione casuale, dall'elenco chiuso in
  `logica.js` (`sessione`, `comando`, `guardia`, `aggiorna`, `segnalazione`, `deriva`, `config`, `setup`,
  `chiede`, `confermata`, `errore`, `claude`). Ogni evento ha il giorno e mai l'ora. `config`
  (config rotta) manda subito un'email, una al giorno per installazione. Il server accetta ancora
  `tappa`, che il client non manda più dal 16/10/2026, per non perdere i dati dei client non
  aggiornati: in coda all'elenco, si toglie dopo qualche settimana.
  Dal 24/10/2026 anche i valori sono a lista chiusa: `guardia`, `chiede`, `confermata` ed `errore`
  accettano solo i nomi delle guardie di Arturo (`GUARDIE` in `logica.js`), con il suffisso
  `.<regola>` solo per le regole che esistono (`REGOLE`: quelle di block-dangerous e le famiglie del
  segreto di commit-secret-gate, mai il nome del fornitore). `comando` accetta solo i comandi di
  `commands/` (`COMANDI`) e `altro`. Il lotto passa in parte: la risposta è `200 {accettati, scartati}`,
  gli eventi fuori elenco non si salvano e si contano nel contatore `scartati` del giorno, senza id.
  Il `400` resta per il lotto malformato (installazione, versione o sistema storti, JSON rotto).
  Di `deriva` si salvano solo i nomi di Arturo dove la persona crea cose sue: i file della radice, le
  voci di `skills/`, `agents/` e `commands/` e gli hook di `settings.json` (`DERIVA_NOMI` e `DERIVA_HOOK`).
  Un altro nome si salva come `file:altro` o `hook:altro`. Della versione si salva solo il rilascio
  (`v2026-10-19.2`), senza i commit della persona; un tag della persona diventa `sconosciuta`.
- `POST /v1/segnalazioni`: una segnalazione che la persona ha letto e approvato con `/segnala`.
- `POST /v1/feedback`: il modulo di feedback del sito, che la landing serve come `/api/feedback`.
  Il testo, il tipo e l'email facoltativa restano nella tabella `feedback`. Solo testo scritto: un modulo
  con il campo `voce` torna `400` con il motivo, un corpo oltre 64 KB torna `413`. Al massimo 100 al
  giorno. Cosa ne sa chi usa il sito sta in `docs/privacy.md`, l'unica fonte delle frasi sui dati.
- `POST /v1/lancillotto/eventi`: gli eventi d'uso di Lancillotto (dal 25/10/2026), con un id casuale suo, la versione
  `x.y.z` e `macos-NN`. Elenco chiuso in `server/lancillotto.js`, uguale a `lancillotto/telemetria.py` (caso L03).
  Vanno nella tabella `eventi_lancillotto`, che il Worker crea da solo alla prima richiesta: i numeri di Arturo non
  cambiano. Una nuova installazione suona su Telegram; il riepilogo e l'email del lunedì hanno il blocco "Dove
  migliorare Lancillotto".
- `POST /v1/sito`: un download dal sito, servito come `/api/sito`: il comando di installazione
  copiato o il repository aperto. Non si salva niente oltre al contatore del giorno, e Telegram
  avvisa fino a 60 volte al giorno.

E dà due cose, a chi ha il token. La prima: `GET /v1/segnalazioni`, le ultime 50 segnalazioni senza testo, e
`GET /v1/segnalazioni/<n>`, una segnalazione intera (27/10/2026): le legge la pagina privata di chi mantiene
Arturo. La seconda: `GET /v1/riepilogo`, il riepilogo della settimana in JSON (senza
`dal` e `al`, la stessa dell'email del lunedì: da lunedì a domenica in ora di Roma) con la sezione "Dove migliorare Arturo" (secret `RIEPILOGO_TOKEN`, almeno 32 caratteri). Le statistiche
delle guardie (blocchi, conferme, guardie rotte, guardie frequenti) contano solo le installazioni che
il server ha ricevuto in almeno due giorni diversi, e ogni numero dice quante installazioni lo
producono: chiunque può mandare eventi con un id nuovo, e un lotto di un giorno solo non deve
spostare quei numeri. **Una guardia non si allenta sulla sola base della telemetria**: la
routine che propone correzioni lo tratta come un indizio da verificare, mai come la prova.

L'IP non viene salvato: nello schema non c'è una colonna per l'IP. Gli eventi, i contatori, il
feedback e le segnalazioni più vecchi di 12 mesi si cancellano il lunedì (le segnalazioni dal 24/10/2026). Le chiavi "una volta per installazione"
(come l'avviso del setup finito) se ne vanno con l'ultimo evento della loro installazione.

## I file

| File | Cosa fa |
|------|---------|
| `logica.js` | Validazione, tetti, testo delle email, recap e riepilogo, ritenzione. Niente Cloudflare dentro. |
| `archivio.js` | Le query su D1, compresa "Dove migliorare Arturo". |
| `worker.js` | Collega `logica.js` e `archivio.js` a D1 (`env.DB`), all'invio email (`env.POSTA`) e a Telegram. |
| `schema.sql` | Le quattro tabelle: `eventi`, `segnalazioni`, `contatori`, `feedback`. |
| `wrangler.toml` | La config del Worker, con segnaposto al posto dei valori veri. |
| `test.mjs` | Il banco: `node server/test.mjs` prova `logica.js` con un archivio e una posta finti. |
| `test-sql.mjs` | Il banco delle query: `node server/test-sql.mjs` prova `archivio.js` su SQLite in memoria (Node 22). |

## Le email

- **Su Telegram**, se il Worker ha i secret `TELEGRAM_TOKEN` e `TELEGRAM_CHAT`: un messaggio per ogni
  installazione nuova (il primo lotto da un id mai visto), per ogni segnalazione, per ogni feedback
  del sito, per ogni download dal sito (fino a 60 al giorno) e per il setup finito, una volta per
  installazione. Il testo porta solo quello che il server già salva, e l'id esce con 8 caratteri.
  Senza i secret non parte niente.
- **Segnalazioni e feedback sono campanelli (24/10/2026).** Telegram ed email dicono solo numero, tipo
  e origine: `Arturo: feedback n. 3 · idea · sito`. Mai il titolo, il testo, l'email di chi scrive o
  l'id completo: il testo resta in D1. Dal 27/10/2026 la segnalazione si legge senza comandi:
  `Arturo: segnalazione n. 14, un problema · installazione 826cca31 · Arturo v2026-10-21 · Darwin`,
  e sotto il link `<LEGGI_SEGNALAZIONI>/14` alla pagina privata, che la legge con `GET /v1/segnalazioni/14`.
  Senza la variabile `LEGGI_SEGNALAZIONI` l'avviso dice di leggerla col token. Ogni segnalazione arriva
  anche come email, con l'oggetto `[Arturo] Segnalazione n. 14: un problema` e lo stesso link. Il tetto è
  di 20 email al giorno, separato dalle 20 delle config rotte: oltre, la segnalazione resta in D1 senza email.
- **Un canale che tace si conta (24/10/2026).** Un avviso Telegram o un'email che non parte non ferma
  la richiesta, e sale il contatore del giorno `telegram-ko` o `email-ko`, senza id. Il recap e il
  riepilogo del lunedì mostrano questi due numeri e gli eventi scartati; un giorno con uno di questi
  numeri sopra zero manda il recap anche senza eventi.
- **Tetti e limiti contro l'abuso (16/10/2026).** Gli avvisi Telegram hanno un tetto al giorno:
  20 installazioni nuove, 20 setup finiti, 30 segnalazioni. Oltre, il dato si salva e il messaggio
  no. Il limite per IP sta nei binding `LIMITE_EVENTI` (60 al minuto) e `LIMITE_MODULI` (10 al
  minuto) di `wrangler.toml`; l'IP non si salva. Il modulo e i download rifiutano un invio da un
  altro sito (`Sec-Fetch-Site: cross-site`).
- **Ogni mattina alle 8** (06:00 UTC) arriva il recap del giorno prima, solo se quel giorno ci
  sono stati eventi o segnalazioni. Ha anche le config rotte e la deriva cambiata.
- **Ogni mattina, su Telegram, le installazioni rimaste indietro (23/10/2026)**: attive negli ultimi
  3 giorni e senza un rilascio uscito da almeno 3. Contano solo le installazioni viste in almeno due
  giorni, e un rilascio con la data nel futuro non conta. Un avviso per installazione ogni 7 giorni,
  al massimo 5 al giorno. Nasce da Filippo e Alessio: un difetto dell'aggiornamento automatico gli
  impediva di ricevere la correzione, e solo un `/aggiorna` a mano li ha sbloccati.
- **Il lunedì** arriva sempre il riepilogo della settimana prima, da lunedì a domenica in ora di Roma
  (24/10/2026: prima perdeva il lunedì di sette giorni prima e contava il lunedì appena cominciato), anche vuoto. Si apre con "Dove migliorare
  Arturo" (ultimi 30 giorni: setup fermi, conferme delle guardie, guardie rotte, installazioni rimaste
  indietro, aggiornamenti non applicati, ritenzione, versioni di Claude Code). Dal 24/10/2026 la finestra
  di 30 giorni vale per tutto il blocco, setup e ritenzione compresi (per la soglia di n giorni, le
  installazioni nate fra n e n+30 giorni fa), e contano solo le installazioni viste in almeno due giorni,
  salvo la ritenzione. Lo stesso filtro vale per i comandi usati. Poi tutta la deriva aperta e le
  guardie frequenti (almeno 5 blocchi nella settimana sulla stessa installazione). Poi parte la pulizia. Se il
  riepilogo del lunedì manca, il Worker è fermo.
- **Ogni passo del cron ha il suo try** (24/10/2026): recap, installazioni indietro, riepilogo del lunedì e
  pulizia. Se un passo fallisce, gli altri partono lo stesso, e il log del Worker scrive
  `cron: il passo <nome> non è riuscito` con l'errore. Alla fine il cron risulta fallito anche negli eventi
  di Cloudflare, con i nomi dei passi non riusciti.

## Mettere su il tuo server

Serve un dominio su Cloudflare con Email Routing attivo, e un indirizzo di destinazione già
verificato in Email Routing. Il Worker può scrivere solo a indirizzi verificati.

1. Crea il database e copia il `database_id` che stampa:

   ```bash
   npx wrangler@4 d1 create arturo
   ```

2. Crea le tabelle:

   ```bash
   npx wrangler@4 d1 execute arturo --remote --file schema.sql
   ```

3. Prepara la config fuori dal repository, così i tuoi indirizzi non finiscono in un commit:

   ```bash
   mkdir -p ~/arturo-deploy && cp logica.js archivio.js worker.js schema.sql ~/arturo-deploy/
   sed -e 's/DOMINIO_DEL_SERVER/dati.tuodominio.org/' \
       -e 's/ID_DEL_DATABASE/<database_id>/' \
       -e 's/DESTINATARIO_VERIFICATO/tu@esempio.org/g' \
       -e 's/MITTENTE_SUL_TUO_DOMINIO/arturo@tuodominio.org/' \
       wrangler.toml > ~/arturo-deploy/wrangler.toml
   ```

4. Pubblica, poi dai al Worker il token del riepilogo in JSON (almeno 32 caratteri, lo chiede
   wrangler e non finisce in nessun file):

   ```bash
   cd ~/arturo-deploy && npx wrangler@4 deploy
   npx wrangler@4 secret put RIEPILOGO_TOKEN
   ```

   L'output di `deploy` elenca i binding (`env.POSTA`, `env.DB`), il dominio e il cron `0 6 * * *`.
   Senza il token `GET /v1/riepilogo` risponde sempre 401: è il comportamento sicuro.

   Facoltativi, gli avvisi su Telegram (installazioni nuove e segnalazioni). Crea un bot con
   @BotFather, scrivigli un messaggio, e leggi l'id della chat da
   `https://api.telegram.org/bot<token>/getUpdates` (`message.chat.id`). Poi dai al Worker i due
   secret, sempre da wrangler:

   ```bash
   npx wrangler@4 secret put TELEGRAM_TOKEN
   npx wrangler@4 secret put TELEGRAM_CHAT
   ```

   Senza i due secret non parte niente verso Telegram. Il token del bot è un segreto: chi lo ha
   può scrivere a nome del bot, quindi non va in nessun file né in un commit.

5. Prova che risponde. Un `GET /` restituisce una riga di testo:

   ```bash
   curl https://dati.tuodominio.org/
   ```

6. Indica il tuo server ai client: cambia la costante `URL` in `bin/telemetria.py`, oppure
   imposta `ARTURO_TELEMETRIA_URL`. Anche `/segnala` passa da lì. Da una HOME in una cartella
   temporanea (un banco di prova) vale solo la variabile: la costante lì non conta, e senza
   variabile non parte niente.

Per un aggiornamento ripeti i passi 3 e 4. Il database e i dati restano.

L'MCP di Cloudflare non basta per il deploy: la sua autorizzazione non scrive su D1. Usa
`npx wrangler@4`, autenticato con `npx wrangler@4 login`.

## Le query

Da una cartella senza `wrangler.toml`, con wrangler autenticato. Da `server/` non funzionano: il
`wrangler.toml` del repository ha i segnaposto, e la query risponde "Invalid uuid [code: 7400]".

```bash
# Gli eventi degli ultimi 30 giorni, per tipo e valore
npx wrangler@4 d1 execute arturo --remote --command "SELECT evento, valore, COUNT(*) n FROM eventi WHERE giorno >= date('now','-30 day') GROUP BY 1,2 ORDER BY n DESC"

# Le installazioni attive per settimana
npx wrangler@4 d1 execute arturo --remote --command "SELECT strftime('%Y-%W', giorno) settimana, COUNT(DISTINCT installazione) n FROM eventi GROUP BY 1 ORDER BY 1 DESC LIMIT 12"

# Le ultime segnalazioni, e quelle rimaste senza email
npx wrangler@4 d1 execute arturo --remote --command "SELECT id, ricevuta, tipo, titolo, email_inviata FROM segnalazioni ORDER BY id DESC LIMIT 20"

# Il testo di una segnalazione
npx wrangler@4 d1 execute arturo --remote --command "SELECT testo FROM segnalazioni WHERE id = 1"
```

Per cancellare i dati di un'installazione che lo chiede, serve il suo id. La persona lo legge
con `python3 ~/.claude/bin/arturo telemetria mostra`. Il feedback del sito non ha un id: si
cancella con l'email che la persona ha lasciato nel modulo:

```bash
npx wrangler@4 d1 execute arturo --remote --command "DELETE FROM eventi WHERE installazione = '<id>'"
npx wrangler@4 d1 execute arturo --remote --command "DELETE FROM segnalazioni WHERE installazione = '<id>'"
npx wrangler@4 d1 execute arturo --remote --command "DELETE FROM contatori WHERE substr(chiave, instr(chiave, ':') + 1) = '<id>'"
npx wrangler@4 d1 execute arturo --remote --command "DELETE FROM feedback WHERE email = '<email>'"
```

La terza toglie le chiavi dei contatori che portano l'id (`setup-fine:`, `rotta:`, `indietro:`), che
altrimenti restano fino a 12 mesi. Una segnalazione mandata senza id, o un feedback senza email, si
cancella col suo numero (`DELETE` con `WHERE id = N`), se la persona lo dice.
Le copie già uscite verso Gmail e Telegram non si raggiungono dal server, e la pulizia dei 12 mesi non
le tocca: il recap e il riepilogo del lunedì (prime 8 cifre dell'id con deriva, guardie frequenti e
installazioni indietro), gli avvisi di installazione nuova, setup finito, installazione indietro e config
rotta. Prima del 24/10/2026 portavano anche il testo delle segnalazioni e del feedback. Chi mantiene
Arturo le cancella a mano nella casella e nella chat; l'elenco intero sta in `docs/privacy.md` ("Chi li
riceve"). La stessa procedura sta in `docs/manutenzione.md`: il banco CP01 le confronta.
