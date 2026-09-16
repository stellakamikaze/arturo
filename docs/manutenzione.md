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
   git checkout main && git merge --ff-only dev && git push origin main
   ```

   `--ff-only` è un freno: se `main` non può avanzare in modo lineare, il merge si ferma e
   ti costringe a guardare perché `dev` e `main` hanno diverto. Mai forzare.

## La versione è la data

Non ci sono tag e non c'è semver. La versione di Arturo è la data dell'entry in cima a
`NOVITA.md`: `## 2026-09-16 — …` vuol dire «versione del 16 settembre 2026». Il canale di
aggiornamento e gli avvisi all'avvio leggono quella data. Aggiungere un secondo sistema di
versioni ne creerebbe due da tenere allineati: non farlo.

## Misurare l'uso senza telemetria

Arturo non ha contatori né ping di versione, per l'impegno sulla telemetria del
README. Chi mantiene può comunque farsi un'idea dell'uso, dal lato GitHub:

```bash
# clone degli ultimi 14 giorni (li vede solo il proprietario del repo).
# Nota: non è verificato se i git fetch automatici contino come clone.
gh api repos/stellakamikaze/arturo/traffic/clones --jq '{count,uniques}'

# stelle e fork
gh repo view stellakamikaze/arturo --json stargazerCount,forkCount

# issue aperte e chiuse
gh issue list --repo stellakamikaze/arturo --state all
```

Sono misure lato manutentore, mai lato utente: niente viene raccolto dentro la
copia di Arturo installata su una macchina.

## Se lo sviluppo si ferma

L'impegno verso chi usa Arturo (README, sezione «Impegni») è dirlo esplicitamente. Tre passi:

1. Entry in `NOVITA.md` che dichiara lo stop, in cima, con la data.
2. Riga in cima al `README.md` che dice che il progetto non è più mantenuto.
3. Archiviazione del repository su GitHub (Settings → Archive). Un repo archiviato resta
   leggibile: clone e fork continuano a funzionare, e la copia di chi lo usa continua a girare.
