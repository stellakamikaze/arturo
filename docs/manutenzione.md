# Manutenzione di Arturo

Per chi mantiene Arturo e per chi ne fa un fork. Le regole sono poche e deliberate.

## Due branch

- **`dev`**: lo sviluppo quotidiano. Ogni modifica entra qui.
- **`main`**: il canale di rilascio. È il branch che ricevono gli utenti con
  `git clone` e `/aggiorna`: deve contenere solo versioni che funzionano.

## Portare `dev` su `main`

Una modifica è pronta per il rilascio quando passano tutte e quattro le cose:

1. **Gate verde**: `bash tests/verifica-allineamento.sh` esce con `0`.
2. **Entry nuova in `NOVITA.md`**: in cima, con data ISO nell'intestazione, nel formato delle
   altre (Cosa cambia, Il principio dietro, Da sapere). Gli utenti imparano la novità da lì.
3. **Prova su un clone pulito**: clona il repo in una cartella temporanea e verifica che i
   comandi e gli hook toccati funzionino da zero, senza lo stato locale della tua macchina.
4. **Pubblicazione**, solo a questo punto:

   ```bash
   git checkout main && git merge --ff-only dev
   V="v$(grep -m1 '^## ' NOVITA.md | grep -oE '[0-9]{4}-[0-9]{2}-[0-9]{2}')"
   git rev-parse -q --verify "refs/tags/$V" >/dev/null && V="$V.2"   # seconda uscita nello stesso giorno
   git tag -a "$V" -m "Arturo $V" && git push origin main "$V"
   ```

   `--ff-only` è un freno: se `main` non può avanzare in modo lineare, il merge si ferma e
   ti costringe a guardare perché `dev` e `main` hanno diverto. Mai forzare.

## La versione è la data

Non c'è semver. La versione di Arturo è la data dell'entry in cima a `NOVITA.md`:
`## 2026-09-16 — …` vuol dire «versione del 16 settembre 2026». Il tag `v2026-09-16` che
accompagna ogni pubblicazione è la stessa data scritta in un punto che Git sa leggere: non è un
secondo sistema di versioni. Serve perché la data del commit locale cambia con ogni `/fine`,
e perché due uscite nello stesso giorno si distinguono solo con `.2`. `/aggiorna` e il modulo
delle segnalazioni leggono il tag con `git describe --tags --always`.

**Mai riscrivere `main` dopo un tag.** `/aggiorna` confronta la versione pubblicata con quella
che la copia dell'utente conosceva, e se la nuova non discende dalla vecchia si ferma con
`STORIA RISCRITTA`: è lo stesso segnale che darebbe un repository compromesso.

## Misurare l'uso

Arturo manda una telemetria accesa di default (README, Impegni), che serve a migliorarlo. Il server è in
`server/`: un Worker Cloudflare su `arturo-dati.stellakamikaze.org` con un database D1 `arturo`.

- **Dove migliorare Arturo.** Il riepilogo del lunedì si apre con questa sezione, sugli ultimi 30
  giorni: fase di `/setup` dove si fermano le installazioni che non arrivano in fondo, guardie che
  chiedono conferma con la quota di sì (vicina al 100% vuol dire domanda inutile), guardie che si
  rompono, aggiornamenti rifiutati o annullati per versione, installazioni per tappa e quelle ferme
  sulla stessa tappa da 30 giorni pur lavorando, ritenzione a 7, 30 e 60 giorni, versioni di Claude
  Code. Sono numeri, non verdetti: cosa correggere lo decide chi mantiene Arturo. Ogni correzione nata
  da un segnale lo dice nella sua voce di `NOVITA.md` («Da sapere: lo mostrava la telemetria»).
- **Il riepilogo in JSON.** `GET /v1/riepilogo?dal=AAAA-MM-GG&al=AAAA-MM-GG` con l'intestazione
  `authorization: Bearer <token>` dà lo stesso riepilogo, per la routine che propone le correzioni.
  Il token è il secret `RIEPILOGO_TOKEN` del Worker (almeno 32 caratteri): senza, la rotta risponde 401.
- **Il recap di ogni mattina.** Ogni mattina alle 8 il Worker manda a chi mantiene il recap del
  giorno prima: installazioni attive, versioni, sistemi, comandi usati, guardie che hanno bloccato,
  esiti di `/aggiorna`, config rotte, deriva (per ogni installazione il cui elenco è cambiato:
  OSTACOLO se un hook di Arturo è spento, una guardia è modificata o un comando modificato va in
  conflitto con un aggiornamento), segnalazioni. Nei giorni senza eventi né segnalazioni non parte.
- **La config rotta arriva subito.** Un'email `[Arturo] Config rotta su un'installazione`, una sola
  al giorno per installazione, dentro il tetto di 40.
- **Il riepilogo del lunedì.** Il lunedì arriva sempre lo stesso riepilogo sui 7 giorni, anche
  vuoto: se manca, il server è fermo. In più ha la deriva di tutte le installazioni che ne hanno una,
  anche ferma, e le guardie frequenti: almeno 5 blocchi della stessa guardia nella settimana sulla
  stessa installazione, il segno che Arturo intralcia. Poi il Worker cancella gli eventi più vecchi
  di 12 mesi.
- **Le segnalazioni.** Ogni segnalazione di `/segnala` col canale `arturo` arriva per email,
  con l'oggetto `[Arturo] [tipo] …`, e resta in D1. Arriva anche come messaggio Telegram. Quelle
  aperte da GitHub sono issue con il titolo `[problema]`, `[proposta]` o `[integrazione]`.
- **Le installazioni nuove.** Il primo lotto di eventi da un id mai visto manda un messaggio
  Telegram: id abbreviato, versione e sistema. Telegram parte solo se il Worker ha i secret
  `TELEGRAM_TOKEN` e `TELEGRAM_CHAT` (come si danno: `server/README.md`, passo 4).
- **Le query.** Da `server/`, con wrangler autenticato:

  ```bash
  npx wrangler d1 execute arturo --remote --command "SELECT evento, valore, COUNT(*) n FROM eventi WHERE giorno >= date('now','-30 day') GROUP BY 1,2 ORDER BY n DESC"
  npx wrangler d1 execute arturo --remote --command "SELECT id, ricevuta, tipo, titolo FROM segnalazioni ORDER BY id DESC LIMIT 20"
  ```

- **Una richiesta di cancellazione** arriva con un id: `DELETE FROM eventi WHERE installazione = '…'`
  e `DELETE FROM segnalazioni WHERE installazione = '…'`.

Dal lato GitHub restano le misure di prima:

```bash
gh api repos/stellakamikaze/arturo/traffic/clones --jq '{count,uniques}'
gh repo view stellakamikaze/arturo --json stargazerCount,forkCount
gh issue list --repo stellakamikaze/arturo --state all
```

Un cambio dell'elenco degli eventi tocca tre posti che il banco M09 confronta: `bin/telemetria.py`,
`server/logica.js` e l'Impegno 3 del README. Gli eventi però sono raccontati anche in
`server/README.md`, `docs/referente.md`, nell'avviso di `bin/telemetria.py`, nella FASE 0 di
`commands/setup.md` e nella landing: prima del rilascio, `git grep -n` sul nome di un evento. Il server va pubblicato **prima** del client: un
lotto con un evento che il server non conosce viene rifiutato per intero, e il client lo toglie dalla
coda. Se cambia cosa esce, alza anche `PROMESSA` in `bin/telemetria.py`: l'avviso torna una volta.

## Se lo sviluppo si ferma

L'impegno verso chi usa Arturo (README, sezione «Impegni») è dirlo esplicitamente. Tre passi:

1. Entry in `NOVITA.md` che dichiara lo stop, in cima, con la data.
2. Riga in cima al `README.md` che dice che il progetto non è più mantenuto.
3. Archiviazione del repository su GitHub (Settings → Archive). Un repo archiviato resta
   leggibile: clone e fork continuano a funzionare, e la copia di chi lo usa continua a girare.
