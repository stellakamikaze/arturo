# Il server di Arturo

Un Worker Cloudflare con un database D1. Riceve due cose e solo quelle:

- `POST /v1/eventi`: un lotto di eventi d'uso con un id di installazione casuale, dall'elenco chiuso in
  `logica.js` (`sessione`, `comando`, `guardia`, `aggiorna`, `segnalazione`, `deriva`, `config`, `setup`,
  `chiede`, `confermata`, `errore`, `tappa`, `claude`). Ogni evento ha il giorno e mai l'ora. `config`
  (config rotta) manda subito un'email, una al giorno per installazione.
- `POST /v1/segnalazioni`: una segnalazione che la persona ha letto e approvato con `/segnala`.

E dà una cosa sola, a chi ha il token: `GET /v1/riepilogo`, il riepilogo della settimana in JSON con
la sezione «Dove migliorare Arturo» (secret `RIEPILOGO_TOKEN`, almeno 32 caratteri).

L'IP non viene salvato: nello schema non c'è una colonna per l'IP. Gli eventi più vecchi di
12 mesi si cancellano il lunedì.

## I file

| File | Cosa fa |
|------|---------|
| `logica.js` | Validazione, tetti, testo delle email, recap e riepilogo, ritenzione. Niente Cloudflare dentro. |
| `archivio.js` | Le query su D1, compresa «Dove migliorare Arturo». |
| `worker.js` | Collega `logica.js` e `archivio.js` a D1 (`env.DB`), all'invio email (`env.POSTA`) e a Telegram. |
| `schema.sql` | Le tre tabelle: `eventi`, `segnalazioni`, `contatori`. |
| `wrangler.toml` | La config del Worker, con segnaposto al posto dei valori veri. |
| `test.mjs` | Il banco: `node server/test.mjs` prova `logica.js` con un archivio e una posta finti. |
| `test-sql.mjs` | Il banco delle query: `node server/test-sql.mjs` prova `archivio.js` su SQLite in memoria (Node 22). |

## Le email

- **Su Telegram**, se il Worker ha i secret `TELEGRAM_TOKEN` e `TELEGRAM_CHAT`: un messaggio per ogni
  installazione nuova (il primo lotto da un id mai visto) e per ogni segnalazione. Il testo porta solo
  quello che il server già salva. Senza i secret non parte niente.
- **Ogni segnalazione** arriva come email, con l'oggetto `[Arturo] [tipo] titolo`. Il tetto è
  di 40 email al giorno: oltre, la segnalazione resta in D1 senza email.
- **Ogni mattina alle 8** (06:00 UTC) arriva il recap del giorno prima, solo se quel giorno ci
  sono stati eventi o segnalazioni. Ha anche le config rotte e la deriva cambiata.
- **Il lunedì** arriva sempre il riepilogo dei 7 giorni, anche vuoto. Si apre con «Dove migliorare
  Arturo» (ultimi 30 giorni: setup fermi, conferme delle guardie, guardie rotte, aggiornamenti non
  applicati, tappe, ritenzione, versioni di Claude Code), poi tutta la deriva aperta e le
  guardie frequenti (almeno 5 blocchi nella settimana sulla stessa installazione). Poi parte la pulizia. Se il
  riepilogo del lunedì manca, il Worker è fermo.

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
   imposta `ARTURO_TELEMETRIA_URL`. Anche `/segnala` passa da lì.

Per un aggiornamento ripeti i passi 3 e 4. Il database e i dati restano.

L'MCP di Cloudflare non basta per il deploy: la sua autorizzazione non scrive su D1. Usa
`npx wrangler@4`, autenticato con `npx wrangler@4 login`.

## Le query

Da qualunque cartella, con wrangler autenticato:

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
con `python3 ~/.claude/bin/arturo telemetria mostra`:

```bash
npx wrangler@4 d1 execute arturo --remote --command "DELETE FROM eventi WHERE installazione = '<id>'"
```
