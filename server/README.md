# Il server di Arturo

Un Worker Cloudflare con un database D1. Riceve due cose e solo quelle:

- `POST /v1/eventi`: un lotto di eventi d'uso anonimi, dall'elenco chiuso in `logica.js`
  (`sessione`, `comando`, `guardia`, `aggiorna`, `segnalazione`). Ogni evento ha il giorno e mai l'ora.
- `POST /v1/segnalazioni`: una segnalazione che la persona ha letto e approvato con `/segnala`.

L'IP non viene salvato: nello schema non c'è una colonna per l'IP. Gli eventi più vecchi di
12 mesi si cancellano il lunedì.

## I file

| File | Cosa fa |
|------|---------|
| `logica.js` | Validazione, tetti, testo delle email, recap e riepilogo. Niente Cloudflare dentro. |
| `worker.js` | Collega `logica.js` a D1 (`env.DB`) e all'invio email (`env.POSTA`). |
| `schema.sql` | Le tre tabelle: `eventi`, `segnalazioni`, `contatori`. |
| `wrangler.toml` | La config del Worker, con segnaposto al posto dei valori veri. |
| `test.mjs` | Il banco: `node server/test.mjs` prova `logica.js` con un archivio e una posta finti. |

## Le email

- **Ogni segnalazione** arriva come email, con l'oggetto `[Arturo] [tipo] titolo`. Il tetto è
  di 40 email al giorno: oltre, la segnalazione resta in D1 senza email.
- **Ogni mattina alle 8** (06:00 UTC) arriva il recap del giorno prima, anche nei giorni vuoti.
  Se un recap manca, il Worker è fermo.
- **Il lunedì**, dopo il recap, arriva il riepilogo dei 7 giorni. Poi parte la pulizia.

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
   mkdir -p ~/arturo-deploy && cp logica.js worker.js schema.sql ~/arturo-deploy/
   sed -e 's/DOMINIO_DEL_SERVER/dati.tuodominio.org/' \
       -e 's/ID_DEL_DATABASE/<database_id>/' \
       -e 's/DESTINATARIO_VERIFICATO/tu@esempio.org/g' \
       -e 's/MITTENTE_SUL_TUO_DOMINIO/arturo@tuodominio.org/' \
       wrangler.toml > ~/arturo-deploy/wrangler.toml
   ```

4. Pubblica:

   ```bash
   cd ~/arturo-deploy && npx wrangler@4 deploy
   ```

   L'output elenca i binding (`env.POSTA`, `env.DB`), il dominio e il cron `0 6 * * *`.

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
