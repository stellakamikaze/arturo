# Lavori lunghi — Modulo Condiviso

Un comando che dura più di due minuti non va lanciato in primo piano: la sessione resta bloccata,
e se si chiude il comando muore con lei.

## Quale strada

| Durata e bisogno | Strada |
|------------------|--------|
| Pochi minuti, l'esito serve in questa sessione | `run_in_background` del tool Bash |
| Più a lungo, o il lavoro deve sopravvivere alla sessione | `~/.claude/bin/bgjob.sh` |

## bgjob.sh

```bash
bash ~/.claude/bin/bgjob.sh start <nome> -- <comando> [argomenti...]
bash ~/.claude/bin/bgjob.sh status <nome>
bash ~/.claude/bin/bgjob.sh stop <nome>
```

- `<nome>` usa solo lettere, cifre, punto, trattino e trattino basso.
- Il comando gira come argomenti, senza `eval`. Per pipe o redirezioni: `-- bash -c '...'`.
- Ogni job ha una cartella in `~/.claude/data/logs/bgjobs/<nome>-<data>/`: `log` con l'output,
  `pid`, `start` e il marker `exit` con l'exit code, scritto solo alla fine.
- `start` stampa anche la riga `attesa:`. Lanciala in background per sapere quando il job finisce.

| Exit di `status` | Significato |
|------------------|-------------|
| `0` | finito con exit 0 |
| `1` | finito con un exit diverso da 0: leggi il `log` |
| `2` | in corso |
| `3` | morto senza esito: il processo non c'è più e il marker manca |
| `4` | uso sbagliato o job inesistente |

## Regole

- Un job in corso non è "fatto". Dì "avviato" e controlla `status` prima di riportare l'esito.
- Se chiudi il turno con un lavoro ancora in corso, anche su un'altra macchina, arma prima un
  `run_in_background` o un Monitor che ti richiami. Senza sveglia armata non promettere "fra X verifico".
- La sveglia vale solo finché la sessione è viva. Claude Code non spegne le shell in background quando la
  sessione si chiude: un ciclo d'attesa resta acceso per ore e nessuno ne legge l'esito (24/11/2026: 23 shell
  così in 11 giorni su un Mac). Un'attesa che deve sopravvivere alla sessione diventa un todo con la data
  (`tasks.py wait` o `arturo todo`) oppure un job di `bgjob.sh`, mai una shell `run_in_background`.
- Prima di chiudere la sessione (`/fine`), ferma con `TaskStop` le shell in background che hai lanciato e non
  servono più. Quelle rimaste le chiude `bin/shell-orfane.py` all'avvio di sessione dopo, e le scrive in
  `data/logs/shell-orfane.log`. Una shell che deve restare accesa porta nel comando il segno `arturo:tieni`.
- Mai `pgrep -f` per sapere se il job gira: trova anche il comando che cerca. Usa `status`.
- Su macOS il job tiene sveglio il computer finché gira (`caffeinate`). Con il coperchio chiuso
  un portatile va comunque in stop: un lavoro di ore va su una macchina che resta accesa.
- Su Windows (Git Bash) il `ps` non sa dire l'ora di avvio di un processo: `bgjob.sh` la legge da
  `/proc`. Se il job si ferma alla chiusura della finestra di Git Bash, `status` dice "morto senza
  esito": rilancialo con la finestra aperta.
