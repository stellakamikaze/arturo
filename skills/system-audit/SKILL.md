---
name: system-audit
description: >-
  Verifica che la configurazione Claude Code in ~/.claude/ sia coerente e collegata: settings JSON
  valido, hook presenti su disco e nel settings, frontmatter di agent e skill, link e riferimenti a
  comandi inesistenti. Report-only, non modifica file.
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

1. **settings.json valid** — JSON parseabile, schema corretto.
2. **Hooks-on-disk** — ogni `command:` referenziato in `settings.json` esiste su disco ed è eseguibile.
3. **Hook smoke test** — ogni hook Python/JS non esplode su input JSON vuoto (timeout 3s). Gli hook `.sh` di lifecycle sono esclusi (vedi Importante).
4. **Agent frontmatter** — ogni `.md` in `~/.claude/agents/` ha frontmatter YAML valido con `name` e `description`.
5. **Skill frontmatter** — ogni dir in `~/.claude/skills/` ha `SKILL.md` con `name` e `description`.
6. **MEMORY.md** — solo se la memoria esterna (`~/.claude/data/memory/`) è installata: verifica che esista e che i link `[[slug]]` risolvano. Senza, il check è N/A (Arturo di base usa CLAUDE.md + handoff).
7. **Permessi** — `defaultMode` esiste, no permessi contraddittori (stesso pattern in `allow` e `deny`).

## Output atteso

Verdetto in cima (`OK` o `N issues`), poi checklist `PASS/WARN/FAIL` per ogni voce, con il fix concreto per ogni `FAIL`. In fondo: la cosa più importante da fixare, se c'è. Riporta il verdetto dello script così com'è: è la prova che l'audit è stato eseguito.

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
- Validazione pre-commit di codice progetto → `/validate`.
