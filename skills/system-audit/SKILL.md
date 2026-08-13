---
name: system-audit
description: Audit di integrità della config Claude Code globale (~/.claude/). Verifica hooks-on-disk, frontmatter agents/skills, validità JSON settings, link MEMORY.md. Usa dopo modifiche alla config o se "qualcosa sembra rotto".
---

# System Audit

Report-only. **Non modifica file**. Verifica che la configurazione Claude Code sia coerente e wirata correttamente. Da usare dopo `git pull` del repo config, dopo aver aggiunto hook/skill/agent, o quando il comportamento è inatteso.

## Cosa controlla

1. **settings.json valid** — JSON parseabile, schema corretto.
2. **Hooks-on-disk** — ogni `command:` referenziato in `settings.json` esiste su disco ed è eseguibile.
3. **Hook smoke test** — ogni hook Python/JS non esplode su input JSON vuoto (timeout 3s). Gli hook `.sh` di lifecycle sono esclusi (hanno side-effect: un audit è report-only).
4. **Agent frontmatter** — ogni `.md` in `~/.claude/agents/` ha frontmatter YAML valido con `name` e `description`.
5. **Skill frontmatter** — ogni dir in `~/.claude/skills/` ha `SKILL.md` con `name` e `description`.
6. **MEMORY.md** — solo se la memoria esterna (`~/.claude/data/memory/`) è installata: verifica che esista e che i link `[[slug]]` risolvano. Senza, il check è N/A (Arturo di base usa CLAUDE.md + handoff).
7. **Permessi** — `defaultMode` esiste, no permessi contraddittori (stesso pattern in `allow` e `deny`).


## Esegui

```bash
bash ~/.claude/skills/system-audit/audit.sh
```

## Output atteso

Verdetto in cima (`OK` o `N issues`), poi checklist `PASS/WARN/FAIL` per ogni voce, con il fix concreto per ogni `FAIL`. In fondo: la cosa più importante da fixare, se c'è.

## Bitter Lesson pass (a richiesta, giudizio non checker)

Periodicamente — o quando la superficie di regole cresce — rivedi hook/comandi/skill/subagent/regole col **Test Bitter Lesson**: ogni pezzo serve a *compensare* una debolezza attuale del modello, o a dare una *garanzia / integrazione / preferenza* che il modello non può darsi da solo? Segnala (non auto-rimuovere) ciò che:
- decide un esito con soglia/regex/pesi fissi che il giudizio del modello farebbe meglio;
- impone una procedura passo-passo rigida dove basterebbe "obiettivo + rail";
- duplica una capacità nativa (debugging, `/code-review`) o un subagent generico;
- congela gusto/euristiche datate (blocklist, checklist chiuse, pin di nome-modello).
Questo è un giudizio, **non** un detector automatico: un regex che cerca violazioni sarebbe esso stesso una violazione. La superficie di regole va potata, non accresciuta. Tieni sempre i rail legittimi (safety deny, plumbing/auth, gate di determinismo, preferenze genuine).

## Quando NON usarla

- Test funzionali di una feature → la skill ha solo check strutturali.
- Validazione pre-commit di codice progetto → `/validate`.
