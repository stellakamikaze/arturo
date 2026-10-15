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

- Un job in corso non è «fatto». Dì «avviato» e controlla `status` prima di riportare l'esito.
- Mai `pgrep -f` per sapere se il job gira: trova anche il comando che cerca. Usa `status`.
- Su macOS il job tiene sveglio il computer finché gira (`caffeinate`). Con il coperchio chiuso
  un portatile va comunque in stop: un lavoro di ore va su una macchina che resta accesa.
- Su Windows (Git Bash) il `ps` non sa dire l'ora di avvio di un processo: `bgjob.sh` la legge da
  `/proc`. Se il job si ferma alla chiusura della finestra di Git Bash, `status` dice «morto senza
  esito»: rilancialo con la finestra aperta.
