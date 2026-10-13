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

Arturo manda una telemetria minima, accesa di default (README, Impegni). Il server è in
`server/`: un Worker Cloudflare su `arturo-dati.stellakamikaze.org` con un database D1 `arturo`.

- **Il recap di ogni mattina.** Ogni mattina alle 8 il Worker manda a chi mantiene il recap del
  giorno prima: installazioni attive, versioni, sistemi, comandi usati, guardie che hanno bloccato,
  esiti di `/aggiorna`, segnalazioni. Parte anche nei giorni vuoti: se un recap manca, il server è fermo.
- **Il riepilogo del lunedì.** Il lunedì, dopo il recap, arriva lo stesso riepilogo sui 7 giorni.
  Poi il Worker cancella gli eventi più vecchi di 12 mesi.
- **Le segnalazioni.** Ogni segnalazione di `/segnala` col canale `arturo` arriva per email,
  con l'oggetto `[Arturo] [tipo] …`, e resta in D1. Quelle aperte da GitHub sono issue con il titolo
  `[problema]`, `[proposta]` o `[integrazione]`.
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

Un cambio dell'elenco degli eventi tocca tre posti insieme: `bin/telemetria.py`, `server/logica.js`
e l'Impegno 3 del README. Il banco M09 li confronta.

## Se lo sviluppo si ferma

L'impegno verso chi usa Arturo (README, sezione «Impegni») è dirlo esplicitamente. Tre passi:

1. Entry in `NOVITA.md` che dichiara lo stop, in cima, con la data.
2. Riga in cima al `README.md` che dice che il progetto non è più mantenuto.
3. Archiviazione del repository su GitHub (Settings → Archive). Un repo archiviato resta
   leggibile: clone e fork continuano a funzionare, e la copia di chi lo usa continua a girare.
