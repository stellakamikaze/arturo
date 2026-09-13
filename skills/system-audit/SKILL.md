---
name: system-audit
description: >-
  Verifica che la configurazione Claude Code in ~/.claude/ sia coerente e collegata: settings JSON
  valido, hook e statusline presenti su disco, guardie richiamate dal dispatcher, smoke test degli
  hook, frontmatter di agent e skill, defaultMode e permessi senza sovrapposizioni. Report-only, non
  modifica file.
when_to_use: >-
  Usa con /system-audit dopo ogni git pull dell'harness, dopo aver aggiunto o tolto hook, skill o
  comandi, o quando «qualcosa sembra rotto» (una guardia che non scatta, un comando che non compare).
  NON per controllare il codice di un progetto: per quello ci sono validate e la review. Segui tutti i
  passi nell'ordine: non prendere scorciatoie basandoti su questa description.
---

# System Audit

## Esegui

```bash
bash ~/.claude/skills/system-audit/audit.sh
```

Lo script legge `~/.claude/` e richiede `python3` con **PyYAML**; `node` serve per controllare sintassi degli hook JS. Con `--strict`, un `FAIL` o un controllo obbligatorio non eseguito termina con codice nonzero. Installa PyYAML prima dell'audit, mai durante l'audit.

```bash
python3 -m pip install PyYAML
bash ~/.claude/skills/system-audit/audit.sh --strict
```

## Cosa controlla

Solo questi controlli, niente di più:

1. **settings.json** — JSON valido con radice a mappa. Lo schema dei campi non si verifica.
2. **Hook diretti** — ogni script `.py`/`.sh`/`.js` citato da un `command` degli hook o da `statusLine` esiste su disco (path con virgolette e spazi compresi).
3. **Guardie transitive** — ogni guardia richiamata da `bash-dispatcher.sh` con `run_guard` esiste su disco.
4. **Smoke test** — ogni hook Python riceve `{}` su stdin ed esce 0 (timeout 5 s se c'è `timeout`); ogni hook JS passa `node --check`. Gli hook `.sh` non si eseguono (vedi Importante).
5. **Agent** — ogni `.md` in `~/.claude/agents/` ha frontmatter YAML con `name` e `description`.
6. **Skill** — ogni cartella in `~/.claude/skills/` ha `SKILL.md` con frontmatter YAML, `name` e `description`.
7. **README** — `~/.claude/README.md` esiste.
8. **Permessi** — `defaultMode` presente e nessun pattern uguale in `allow` e `deny`.

## Output atteso

Una riga `PASS`/`WARN`/`FAIL` per controllo, poi `Totali: PASS=… WARN=… FAIL=…` in fondo. Con `--strict` lo script esce 1 se c'è almeno un `FAIL`. Riporta le righe dello script così come sono, con il fix concreto per ogni `FAIL`: sono la prova che l'audit è stato eseguito.

## Bitter Lesson pass (a richiesta, giudizio non checker)

Periodicamente — o quando la superficie di regole cresce — rivedi hook/comandi/skill/subagent/regole col Test Bitter Lesson: ogni pezzo serve a *compensare* una debolezza attuale del modello, o a dare una *garanzia / integrazione / preferenza* che il modello non può darsi da solo? Segnala ciò che:
- decide un esito con soglia/regex/pesi fissi che il giudizio del modello farebbe meglio;
- impone una procedura passo-passo rigida dove basterebbe "obiettivo + rail";
- duplica una capacità nativa (debugging, `/code-review`) o un subagent generico;
- congela gusto/euristiche datate (blocklist, checklist chiuse, pin di nome-modello).
I limiti di questo passaggio stanno in Importante.

## Importante

- Report-only: l'audit non modifica file. Un `FAIL` si riporta col suo fix, non si corregge durante l'audit.
- Gli hook `.sh` di lifecycle (session-start/end, notifier) non si eseguono mai in audit: hanno side-effect.
- Il Bitter Lesson pass è un giudizio, non un detector automatico: un regex che cerca violazioni sarebbe esso stesso una violazione. Segnala, non auto-rimuovere. La superficie di regole va potata, non accresciuta.
- Tieni sempre i rail legittimi: safety deny, plumbing/auth, gate di determinismo, preferenze genuine.

## Cosa evitare

- Rifare i controlli a mano (aprire `settings.json`, scorrere `skills/`) invece di lanciare `audit.sh`: la copertura è parziale e il "tutto OK" non è provato.
- Dichiarare l'audit fatto senza il verdetto dello script nel report.

## Quando NON usarla

- Test funzionali di una feature → la skill ha solo check strutturali.
- Validazione pre-commit di codice progetto → applica `shared/validation-gate.md`.
