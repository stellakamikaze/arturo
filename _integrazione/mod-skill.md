# Integrazione del lotto «mod-skill» (15/10/2026)

File nuovi del lotto:

- `skills/apri/` (mod `/apri`), `skills/gws/` (mod gws), entrambi con `.claude-plugin/plugin.json`,
  `hooks/` e `tests/`.
- `skills/italiano-semplificato/references/tic-scrittura-ia.md` (catalogo dei tic, scritto da zero).
- `templates/strato/esempi/` (README, `posta/SKILL.md`, `recap/SKILL.md`, `anteprima-invio/`).
- `docs/impeccable.md` (rimando all'upstream, la skill non è copiata).
- `tests/test_mod_skill.py` (Q01-Q08, discriminante su `cbd8305`).

File modificati: `skills/cache-fredda/` (segnali banchi rossi e token gws, versione 0.2.0),
`skills/italiano-semplificato/SKILL.md` (due righe che collegano il catalogo),
`skills/prompt-master/SKILL.md` (sezione Importante allineata al trigger), `agents/ui-ux-consultant.md`
(rimando a impeccable), `commands/strato.md`, `docs/referente.md`, `templates/strato/REFERENTE.md`
(gli esempi dello strato).

## 1. tests/verifica-allineamento.sh

### 1a. Banco da registrare

In `BANCHI`, dopo `test_segnala.py`:

```bash
  test_mod_skill.py
```

In `BASELINE`, in coda:

```bash
  # Mod e skill portati dalla config dell'autore (15/10/2026): cbd8305, la base dei lotti.
  "test_mod_skill.py cbd8305"
```

Il banco chiama `claude plugin validate` e `claude plugin test` (come `test_mod_portati.py`): il gate
controlla già che `claude` ci sia. Non serve in `PY38_BANCHI`: usa solo la stdlib e
`from __future__ import annotations`, ma lancia `claude`.

### 1b. Il gate scrive il suo esito (serve all'avviso «banchi rossi»)

Il mod `cache-fredda` legge `<radice di Arturo>/cache/banchi-ultimo-esito.txt` (riga 1 `ROSSO` o
`VERDE`, riga 2 il riassunto). Oggi nessuno lo scrive: senza questa modifica l'avviso tace sempre
(un file assente non mostra niente). Sostituisci la riga

```bash
trap 'rm -rf "$FIXTURE"' EXIT
```

con

```bash
# L'esito del gate per l'avviso «banchi rossi» del mod cache-fredda. Con set -e il gate si ferma
# al primo rosso: il conto è sempre 1 FAIL. cache/ è fuori da git.
ESITO_GATE="$ROOT/cache/banchi-ultimo-esito.txt"
trap 'rc=$?; mkdir -p "$ROOT/cache" 2>/dev/null && if [[ $rc -eq 0 ]]; then printf "VERDE\n=== gate: tutto verde ===\n"; else printf "ROSSO\n=== gate: 1 FAIL (rc %s) ===\n" "$rc"; fi >"$ESITO_GATE" 2>/dev/null; rm -rf "$FIXTURE"' EXIT
```

Provata nel lotto su una copia temporanea dello script: dopo un gate verde il file contiene `VERDE`.
L'uscita anticipata per un programma mancante (prima del trap) non scrive niente, e va bene così.

## 2. settings.json

Niente. I mod si caricano da `skills/` come gli altri (`skills-dir`). Nessun permesso nuovo:
`claude plugin validate` è già in allow, `claude plugin test` gira solo nel gate.

## 3. README.md

### 3a. Sezione «Gli altri mod», dopo la riga di `skills/cache-fredda/`

Sostituisci la riga di `cache-fredda` con:

```markdown
- `skills/cache-fredda/` scrive sotto il prompt, solo quando serve, tre avvisi: la cache è scaduta (dopo un'ora con l'abbonamento, dopo 5 minuti a quota piena) e il prossimo messaggio riscriverebbe tutto il contesto; l'ultimo gate di Arturo (`tests/verifica-allineamento.sh`) è rosso; un account di `gws` ha il token in errore e va rifatto il login. Se tutto è in regola, non scrive niente.
- `skills/apri/` aggiunge `/apri`: apre l'ultimo link o file citato nelle risposte con il programma predefinito del sistema (il browser per i link, l'app di solito per i file). `/apri 2` apre il secondo della lista, `/apri <parola>` il primo che la contiene, `/apri lista` mostra gli ultimi dieci. Non usa un turno del modello.
- `skills/gws/` aiuta con la CLI `gws`: se un comando fallisce per credenziali mancanti o scadute, Claude lo dice subito e ti chiede di rifare il login invece di riprovare con altri account. Corregge anche `gws gmail messages` in `gws gmail users messages`. Il setup degli account resta in [`docs/onboarding/gws.md`](docs/onboarding/gws.md).
```

### 3b. Struttura delle cartelle (blocco di codice con `docs/onboarding/`)

Dopo la riga `docs/onboarding/     Guide di setup guidato (/inizio gws)` aggiungi:

```
docs/impeccable.md   Come installare Impeccable (design delle interfacce) dall'upstream
```

E la riga di `templates/strato/` diventa:

```
templates/strato/    Modello di plugin per lo strato di un'organizzazione (/strato crea), con esempi da adattare
```

### 3c. Skill `italiano-semplificato`

In coda alla riga di `italiano-semplificato` aggiungi: ` Una seconda passata cerca i tic di ritmo e struttura del testo generato (contrasti inventati, terne automatiche, chiuse a sentenza): il catalogo è in italiano e scritto da zero.`

## 4. NOVITA.md (entry in cima)

```markdown
## 2026-10-15 — /apri, avvisi sotto il prompt, esempi per lo strato

**Cosa cambia**: scrivi `/apri` e si apre l'ultimo link o file che Claude ha citato, con il
programma predefinito del tuo computer. Sotto il prompt, oltre alla cache fredda, compaiono due
avvisi nuovi: l'ultimo controllo di Arturo è rosso, oppure un account Google della CLI `gws` va
ricollegato. Se usi `gws`, un errore di credenziali ora si dichiara al primo colpo, con il comando
per rifare il login. La skill dell'italiano semplificato ha un catalogo dei tic della scrittura
generata. Chi cura lo strato di un'organizzazione trova in `esempi/` tre modelli da adattare: le
email che imparano dalle correzioni, il recap delle riunioni dalla trascrizione intera, l'anteprima
prima dell'invio. Per il design delle interfacce, `docs/impeccable.md` spiega come installare
Impeccable dall'autore.

**Il principio dietro**: un avviso compare solo quando c'è qualcosa da fare. Una cosa che esiste già
fatta bene altrove si installa da lì, non si copia.

**Da sapere**: gli esempi dello strato non sono attivi finché il referente non li copia nello
strato. Gli avvisi tacciono se non usi `gws` e se non lanci i controlli di Arturo. Per spegnere un
mod: `/plugin`, poi il mod, poi disattiva.
```

## 5. Cosa il lotto lascia fuori, e perché

- Il catalogo d'origine dei tic (tropes.fyi): la pagina e il gist dell'autore non dichiarano una
  licenza (verificato il 15/10/2026). Il catalogo di Arturo è scritto da zero, con voci ed esempi
  nuovi; la fonte è citata come spunto.
- La fascia del cruscotto (contesto, task): Arturo ha già la riga di `/dafare` sopra il prompt e la
  statusline. I due segnali utili stanno in `cache-fredda`, nella riga sotto il prompt.
- Il controllo dei token gws del vecchio hook di avvio: in Arturo lo fa `cache-fredda` dopo
  l'avvio e ogni 6 ore, sugli account trovati in `~/.config/gws*` che hanno fatto il login.
- Posta, recap e anteprima come skill operative: in Arturo sono solo esempi dello strato, senza
  account, copie, database dei task o nomi.
