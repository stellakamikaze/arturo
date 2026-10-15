# Integrazione del lotto «script»

Branch `lotto-script`, base `cbd8305`. Modifiche da applicare ai file condivisi.

## tests/verifica-allineamento.sh

In `BANCHI`, in coda:

```
  test_script.py
```

In `PY38_BANCHI`, aggiungi `test_script.py` (la parte Python è 3.8: provata con 3.9 e 3.14, python3.8
assente su questa macchina):

```
PY38_BANCHI=(test_todo.py test_web.py test_percorso.py test_segnala.py test_telemetria.py test_deriva.py test_deriva_allineata.py test_personale.py test_script.py)
```

In `BASELINE`, in coda:

```
  # Gli script portati dalla config dell'autore (15/10/2026): cbd8305, l'ultimo dev prima del porting.
  "test_script.py cbd8305"
```

Il banco dura circa 30 secondi (Z07 lancia 12 volte l'audit su una copia, Z02 il banco del gate).
Non dipende da pytest: Z02 mette nel PATH un pytest minimo suo.

## Un file condiviso fuori elenco già cambiato nel branch

`tests/test_allineamento.py`, controllo C06: prima esigeva `PIPESTATUS[0]` in
`shared/validation-gate.md`, cioè proprio il difetto da chiudere. Ora esige il contrario:

```python
    # C06: il gate legge l'exit da file (in zsh PIPESTATUS non esiste e l'exit letto resta vuoto).
    assert "PIPESTATUS[0]" not in gate and "validation-gate-lang.sh" in gate and '.rc"' in gate \
        and "Quality gate: SKIP" not in gate, "C06 gate maschera errori"
```

Se un altro lotto tocca `test_allineamento.py` (per esempio `VIETATI`), tieni questa riga.

## settings.json

Niente da cambiare: nessun hook nuovo, nessun permesso nuovo.

## README.md

1. Sezione **Cosa c'è dentro**, nel blocco di codice: sostituisci la riga di `bin/` e aggiungi `tools/`:

```
bin/                 La CLI arturo, i suoi moduli e gli script di servizio (gate, job lunghi, pulizia)
tools/scrapling/     scrape: lettura di una pagina web senza browser (facoltativo, si installa da /setup)
```

2. Sezione **Installazione**, riga «per innestare Arturo su una config esistente»: nell'elenco delle
   cartelle da copiare aggiungi `tools/` dopo `templates/`.

3. Sezione **Aggiornare Arturo**, tabella (riga 173 circa): nella colonna di ciò che Arturo aggiorna
   aggiungi `tools/` dopo `templates/`; nella colonna di ciò che resta tuo aggiungi
   `tools/scrapling/.venv/` (il venv di `scrape`).

4. Sezione **Le skill (`skills/`)**: sostituisci le righe di `shared/validation-gate.md` e `system-audit` con:

```
- **`shared/validation-gate.md`** — il gate: riconosce il linguaggio del progetto (Node, Python, prosa) con `bin/validation-gate-lang.sh` e legge l'exit da file, mai da una pipe. Esce verde, rosso o «inconclusivo»: la prosa e gli strumenti assenti non sono mai un verde. Spiega anche come provare un banco nuovo con `bin/gate-run.sh` (prima il veleno, poi il gate) e come confrontare i file serviti dopo un deploy con `bin/sonda_servito.py`.
- **`shared/lavori-lunghi.md`** — un comando che dura più di due minuti va in background. Per un lavoro che deve sopravvivere alla sessione c'è `bin/bgjob.sh`: log, PID e un marker con l'exit code in `data/logs/bgjobs/`.
- **`system-audit`** — audit dell'harness: hook diretti e transitivi, smoke test, frontmatter YAML, permessi, slash-comandi citati nei documenti senza una skill o un comando dietro, peso dei corpi, plugin installati e non attivi. `--strict` fallisce se manca un requisito. Il banco avvelenato `skills/system-audit/tests/banco-gate.sh` lavora su una copia e non tocca la tua `~/.claude`.
```

5. Sezione **Personalizzazione**, in coda all'elenco:

```
- **Pulizia mensile.** `bash ~/.claude/bin/monthly-cleanup.sh --prova` elenca cosa toglierebbe (tasks, shell-snapshots e paste-cache vecchi di Claude Code, cache dei package manager) senza toccare niente. Senza `--prova` pulisce. Facoltativi: `PULIZIA_CARTELLA_PROGETTI=<cartella>` archivia in `_archivio/` i file sciolti fermi da 60 giorni (li sposta, non li cancella), `PULIZIA_PREFISSI_LAUNCHAGENT="com.esempio."` segnala su macOS i tuoi LaunchAgent non caricati, `PULIZIA_CACHE=0` salta le cache.
```

6. Sezione **Troubleshooting**, due righe nuove in fondo alla tabella:

```
| `/system-audit` segnala `cita /qualcosa, che non esiste` | un documento cita un comando tolto o rinominato | correggi la riga; se è un comando nuovo di Claude Code, aggiungilo a `NATIVE` in `skills/system-audit/audit.sh` |
| `scrape` esce 3 con «bloccato» | il sito rifiuta le richieste automatiche | apri la pagina nel browser: `scrape` non prova a superare le verifiche anti-bot |
```

## NOVITA.md

Entry in cima:

```
## 2026-10-15 — Gate che non mentono, lavori lunghi, lettura del web senza browser

**Cosa cambia**: il gate di `/fine` è uno script (`bin/validation-gate-lang.sh`). Riconosce se il
progetto è Node, Python o testo, e lancia i controlli giusti. Prima il gate leggeva l'esito dei test
in un modo che, nella shell di Claude Code, poteva restare vuoto e sembrare un verde. Un comando lungo
ha una strada sua, `bin/bgjob.sh`: gira staccato dalla sessione e scrive l'esito su un file.
`/system-audit` segnala anche i comandi citati nei documenti che non esistono più, e i plugin
installati ma spenti. In `/setup` c'è una fase facoltativa per `scrape`, che legge una pagina web e
tiene solo il testo utile.

**Il principio dietro**: un controllo vale solo se sa dire «rosso». Ogni gate nuovo ha un caso
avvelenato, una versione rotta apposta che deve bocciare. Il «non so» è un esito onesto: il testo e
gli strumenti mancanti danno «inconclusivo», mai verde.

**Da sapere**: `scrape` occupa circa 300 MB e si installa solo se dici sì in `/setup`. Non finge di
essere un browser: se un sito blocca i programmi, te lo dice e ti consiglia di aprire la pagina nel
browser. La pulizia mensile (`bin/monthly-cleanup.sh`) è facoltativa: prova prima con `--prova`.
```

## Fuori dal lotto, e perché

- `skills/system-audit/review.workflow.js` e `review-prep.sh`: non generali. Le aree, i termini
  dell'indice grep e i percorsi parlano della config dell'autore, e il workflow chiede il tool
  Workflow, che una persona di Arturo non ha per forza.
- Gate personali dell'audit: indice di memoria, set lingua delle skill, hook documentati in un file
  di istanza, path dei LaunchAgent personali, corsa dei banchi personali.
- Il controllo dei path di script citati nei documenti (gate 7b della config dell'autore): non
  richiesto; si può portare in un lotto dopo, con lo stesso banco.
- Dal monthly-cleanup: residui di un hook tolto, app personali, archivio fisso in una cartella dei
  progetti personale.
- Da scrape: `StealthyFetcher`, `--stealth`, `--visibile`, `--sessione`, `--fast`, `--retry`,
  `--wait`, `--xhr` (vive solo nel browser), il profilo browser, l'impronta TLS di Chrome e il
  referer di Google. Il banco di rete reale è sostituito da un banco senza rete.
