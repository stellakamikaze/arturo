# Anteprima prima dell'invio (esempio da adattare)

Quando Claude sta per mandare un'email con un connettore (send, reply, forward), l'hook mostra
alla persona destinatari, oggetto e i controlli di {{ORGANIZZAZIONE}}, e chiede conferma. La
persona legge l'anteprima e decide. L'hook non blocca mai da solo.

Le regole stanno in `regole-invio.txt`, non nel codice. Per cambiare una regola cambi il file
nello strato e pubblichi: il codice resta uguale per tutti.

## Come si attiva

1. Copia `anteprima-invio.py` in `plugins/strato/hooks/`.
2. Copia `regole-invio.txt` in `plugins/strato/` e scrivi le vostre regole.
3. In `plugins/strato/hooks/hooks.json`, dentro `PreToolUse`, aggiungi questo blocco:

   ```json
   {
     "matcher": "mcp__.*(send|reply|forward).*",
     "hooks": [
       {
         "type": "command",
         "command": "python3 \"${CLAUDE_PLUGIN_ROOT}/hooks/anteprima-invio.py\" || exit 0",
         "timeout": 10
       }
     ]
   }
   ```

4. Prova con `claude --plugin-dir plugins/strato`: chiedi a Claude di preparare e mandare
   un'email a te stesso, e guarda l'anteprima.

## Da sapere

- Gli invii da riga di comando li ferma già la guardia `comms-guard` di Arturo. Questo esempio
  copre i connettori, dove l'invio passa dalla conferma di Claude Code.
- Se il file delle regole manca o non si legge, l'anteprima mostra solo i controlli generali
  (destinatari, accenti con l'apostrofo). L'invio non resta mai bloccato da un file rotto.
- Nel file delle regole non vanno password o token: lo leggono tutti i colleghi.
