# Validation Gate — Modulo Condiviso

Usato da: `/fine` (mode `quick`). Mode `full` e `shipping` su richiesta.

## Modalità

| Mode | tsc | test | lint | console.log | build | Quando |
|------|-----|------|------|-------------|-------|--------|
| `quick` | x | x | | x | | `/fine` |
| `full` | x | x | x | x | x | verifica manuale |
| `shipping` | x | x | x | | x | consegna manuale |

Python: pytest è il validatore core, ruff e mypy lo strato di qualità, in ogni mode.

## Nessuna cache

Ogni gate esegue i controlli nel working tree corrente. Un esito recente non prova una sorgente cambiata.

## Esecuzione

Il gate è uno script solo, `~/.claude/bin/validation-gate-lang.sh`. Riconosce il linguaggio del
progetto (Node, Python, Swift, .NET, prosa) e lancia i validatori giusti. Il suo banco è `tests/gate/test_gate.sh`.

```bash
G="${TMPDIR:-/tmp}/gate-${CLAUDE_CODE_SESSION_ID:-$PPID}"
bash ~/.claude/bin/validation-gate-lang.sh --mode quick --dir <radice-progetto> > "$G.out" 2>&1; echo $? > "$G.rc"
cat "$G.out"; cat "$G.rc"
```

- Lancia le tre righe in una sola chiamata Bash: le variabili non passano da una chiamata all'altra.
- Il file porta il nome della sessione: due `/fine` in parallelo non si sovrascrivono.
- `--dir` è la radice del progetto, cioè la cartella che contiene `package.json`, `pyproject.toml`, `Package.swift` o la soluzione
  `.sln` (anche in una sottocartella).
- Leggi l'exit code dal file, mai dopo una pipe. La shell del tool Bash può essere zsh, e in zsh
  `PIPESTATUS` non esiste: un exit letto così resta vuoto e sembra un verde.

## Risultato

| Exit | Significato | Cosa fai |
|------|-------------|----------|
| `0` | VERDE: validatori core eseguiti e passati | procedi |
| `1` | ROSSO: un validatore ha fallito | **STOP**, mostra gli errori. In `/fine` chiedi se correggere ora o scrivere l'errore nell'handoff. Prima di una consegna: STOP assoluto, non consegnare codice rotto. |
| `2` | INCONCLUSIVO: prosa, configurazione o strumenti assenti | NON è verde. Controlla a mano i testi destinati a persone reali: contenuto non vuoto, ogni cifra con la sua fonte, la chiusura è un fatto e non una metafora. Se mancano pytest, npm, swift o dotnet, dillo alla persona. |

Un `[WARN] console.log` non blocca: va letto e deciso.

## Un banco nuovo: prima il veleno

Un gate vale solo se boccia una versione rotta apposta, il "veleno", per il motivo atteso.
Quando scrivi un banco o un controllo nuovo, eseguilo con `~/.claude/bin/gate-run.sh`:

```bash
bash ~/.claude/bin/gate-run.sh \
  --poison 'bash tests/mio-banco.sh --file fixture-rotta.txt' --expect 'MOTIVO ATTESO' \
  --pass 'PASS' \
  -- bash tests/mio-banco.sh --file fixture-buona.txt
```

- `--poison` gira per primo, sulla versione rotta. Deve uscire diverso da 0 e stampare il testo di `--expect`.
- Se il veleno esce verde, o rosso per un altro motivo, il gate vero non parte: exit 2.
- Il veleno scrive i suoi file solo in `$VELENO_DIR`, con nome `veleno-*`. Altrimenti exit 3.
- Exit: `0` verde, `1` gate rosso, `2` veleno che non boccia, `3` banco guasto o uso sbagliato.
- Il banco di `gate-run.sh` è `tests/test_gate_run.sh`.

## Dopo un deploy

Un deploy riuscito (exit 0, servizio attivo, risposta 200) non prova che giri il codice nuovo:
la stessa risposta arriva anche dalla versione vecchia. Confronta i file serviti con quelli locali:

```bash
python3 ~/.claude/bin/sonda_servito.py --base https://<indirizzo-del-sito> web/index.html= web/app.js
```

- `FILE=PERCORSO` confronta il file con `BASE/PERCORSO`. Senza `=`, il percorso è il nome del file.
- La sonda riprova per 60 secondi (`--attesa`), finché la versione nuova non risponde.
- Exit: `0` servito uguale al locale, `1` almeno un file diverso o assente, `3` sonda non valida
  (redirect, 401 o 403: risponde una pagina di login e non il sito).

## Referenziare da altri comandi

Nei workflow che chiudono una sessione:
```
Leggi e applica `~/.claude/shared/validation-gate.md` con mode=[quick|full|shipping].
```
