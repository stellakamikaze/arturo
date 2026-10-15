# Integrazione del lotto «fine-inizio»

Branch `lotto-fine-inizio`, base `cbd8305`. Modifiche ai file condivisi che l'orchestratore applica.

## tests/verifica-allineamento.sh

In `BANCHI`, in coda:

```
  test_fine_inizio.py
```

In `PY38_BANCHI` aggiungi `test_fine_inizio.py` (lancia gli script nuovi con l'interprete del banco):

```
PY38_BANCHI=(test_todo.py test_web.py test_percorso.py test_segnala.py test_telemetria.py test_deriva.py test_deriva_allineata.py test_personale.py test_fine_inizio.py)
```

In `BASELINE`, in coda:

```
  # Ciclo di sessione di /fine e /inizio sopra i todo (15/10/2026): cbd8305, l'ultimo dev prima del lotto.
  "test_fine_inizio.py cbd8305"
```

Esiti misurati: `python3 -B tests/test_fine_inizio.py --repo .` → `PASS F01,…,F10 controlli=10`;
sulla base estratta con `git archive cbd8305` → `BASELINE_DISCRIMINANTE=F01,…,F10`.

## settings.json

Niente da cambiare: nessun hook nuovo, nessun permesso nuovo. Gli script nuovi stanno in `bin/`,
che il Config Sync di `/fine` già porta.

## README.md

1. Riga «In due righe» (riga 9): la frase sulla CLI diventa
   `una **CLI per i todo** (`arturo todo`) e per il contesto di un progetto (`arturo contesto`)`.

2. Sezione dei comandi, voce `/inizio` (oggi riga 299). Sostituisci con:

   `- **`/inizio <progetto>`** — sync della config, poi il contesto del progetto in una chiamata (`arturo contesto`: git, ripartenza degli handoff recenti, todo aperti divisi per chi agisce, scadenze), il confronto dei todo con `git log` (quelli già fatti non risorgono) e la scelta del lavoro. Con `--tutti` aggiorna anche ogni progetto della cartella dei progetti; con `-- <compito>` parte subito sul compito. `/inizio gws` avvia invece l'onboarding gws.`

3. Voce `/fine` (oggi riga 300). Sostituisci con:

   `- **`/fine`** — inventario dei file della sessione e dove va ognuno, review di completezza per le modifiche di codice, validate, commit selettivo e handoff con la tabella dei todo pendenti e di chi agisce. Un controllo (`bin/handoff-gate.sh`) ferma un handoff senza tabella, con un todo inesistente o con un segnaposto mai compilato; tiene gli ultimi 5 handoff per progetto e rigenera l'indice `data/handoffs/INDEX.md`. Alla fine chiede se Arturo si è inceppato o se ti manca qualcosa (al massimo una domanda a settimana, oppure subito dopo un intoppo).`

## NOVITA.md

Entry nuova in cima (sopra «Scegli come ti scrive Claude»):

```markdown
## 2026-10-15 — /inizio e /fine: il contesto in una chiamata, un handoff che regge

**Cosa cambia**: `/inizio` raccoglie il contesto del progetto in una chiamata sola
(`arturo contesto`): cosa è cambiato in git, la ripartenza degli ultimi handoff, i todo aperti
divisi fra te e Claude, le scadenze dei prossimi giorni e il todo da cui ripartire. Con
`/inizio --tutti` aggiorna anche tutti i progetti della tua cartella dei progetti. `/fine` parte
dall'inventario dei file che la sessione ha scritto, anche fuori dal progetto (Download, Scrivania,
cartelle temporanee), e propone dove deve finire ognuno. Prima di chiudere controlla l'handoff: la
tabella dei pendenti c'è sempre, ogni riga è un todo vero dell'archivio, e chi agisce è tu, decidi
o io. Tiene gli ultimi 5 handoff per progetto, ma prima ti mostra cosa conteneva quello che esce, e
rigenera l'indice dei progetti.

**Il principio dietro**: una sessione nuova vale quanto quello che trova. Un handoff che dice «cosa
resta» senza dire cosa, o un file lasciato in una cartella che sparisce al riavvio, è lavoro perso.
Meglio un controllo che ferma la chiusura che una ripartenza al buio.

**Da sapere**: gli handoff restano solo sul tuo computer, come prima, e viaggiano fra le tue
macchine solo se la config ha un remote privato. I file che l'inventario trova fuori da un progetto
non si spostano da soli: Claude ti chiede dove li tieni. Da terminale il contesto lo vedi con
`python3 ~/.claude/bin/arturo contesto <progetto>`.
```

## Note per l'orchestratore

- Il prompt del lotto nominava `scripts/…`. In Arturo non esiste una cartella `scripts/`: gli
  script stanno in `bin/`, accanto alla CLI, così il Config Sync di `/fine` e `/aggiorna` li
  coprono senza una voce nuova. Percorsi: `bin/handoff-gate.sh`, `bin/handoff-retention.py`,
  `bin/index-rigenera.py`, `bin/inventario-sessione.py`, `bin/contesto.py` (anche
  `arturo contesto`), `bin/sync-progetti.sh`.
- `tools/handoff-lint.py` non è portato: il suo controllo utile (i segnaposti del modello mai
  compilati) è dentro `bin/handoff-gate.sh`. Il resto (strato `claude -p`, scansione di tutti gli
  handoff) non serve al gate di `/fine`.
- I banchi esistenti toccati da questo lotto restano verdi: H10, M06-M08, K5, P04, P08, T10, T11,
  X07-X11, G14, R05, R07, U11, A05, A11, C04, S08.
