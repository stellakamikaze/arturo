#!/usr/bin/env python3
"""Hook PreToolUse (Edit/MultiEdit/Write/NotebookEdit): protegge file critici.

Tre categorie, ognuna con un unlock per-sessione distinto:

  Persistenza (codice che parte da solo, fuori da Claude Code):
    .git/hooks/** di qualunque repository
    ~/Library/LaunchAgents/** (macOS)
    ~/.config/systemd/user/** e ~/.config/autostart/** (Linux)
    -> unlock: touch ~/.claude/system-unlock-{session_id}

  CLAUDE.md (qualsiasi cartella)
    -> unlock: touch ~/.claude/claude-md-unlock-{session_id}
    Sul CLAUDE.md globale avvisa quando il file, dopo la modifica, supera il
    budget di righe (ARTURO_CLAUDE_MD_RIGHE, default 200).

  Config e hook di Claude Code:
    ~/.claude/settings.json, settings.local.json, .claude.json
    ~/.claude/hooks/**
    ~/.claude/firme/**, bin/aggiornamenti.py, bin/aggiorna-applica.sh (l'aggiornamento automatico:
    chi li cambia fa installare da solo codice non firmato)
    -> unlock: touch ~/.claude/config-unlock-{session_id}

Motivo della categoria config/hook: senza questo, sotto defaultMode auto o acceptEdits
un'iniezione può riscrivere settings.json o disattivare un hook via tool Edit/Write
senza alcun prompt, neutralizzando ogni altra guardia. Il vettore shell
(sed -i, >, cp...) è coperto separatamente da block-dangerous.py.

L'unlock (deny + istruzioni, non hard-deny in settings.json) preserva le
modifiche legittime: chiedi conferma all'utente, crea il touch file, riprova.

I file di unlock stessi (qualsiasi nome con "unlock" sotto ~/.claude) chiedono
sempre conferma anche via Edit/Write: un marker scritto dall'assistente senza una
decisione dell'utente sbloccherebbe da solo le due categorie. Il vettore shell
(touch) chiede conferma in block-dangerous.py.

La categoria persistenza viene prima delle altre: un git hook o un servizio
di avvio esegue codice a ogni commit o a ogni login, senza che nessuno lo chieda.
Il vettore shell (echo >, cp, tee...) su questi percorsi chiede conferma in
block-dangerous.py.

Fail-closed: errore di parsing = blocca per sicurezza.
"""
import json
import sys
import os
import re


def _emit(kind, reason):
    json.dump({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": kind,
            "permissionDecisionReason": reason,
        }
    }, sys.stdout)


# Budget di righe del CLAUDE.md globale: oltre, le istruzioni si diluiscono e
# costano contesto a ogni sessione. Si cambia con la variabile d'ambiente.
BUDGET_RIGHE_DEFAULT = 200


def _budget():
    try:
        return max(1, int(os.environ.get('ARTURO_CLAUDE_MD_RIGHE', BUDGET_RIGHE_DEFAULT)))
    except ValueError:
        return BUDGET_RIGHE_DEFAULT


def _righe_dopo(path, ti):
    """Numero di righe del file come sarà dopo Write, Edit o MultiEdit."""
    return len(_testo_dopo(path, ti).splitlines())


def _testo_dopo(path, ti):
    """Il file come sarà dopo Write, Edit o MultiEdit."""
    if isinstance(ti.get('content'), str):
        testo = ti['content']
    else:
        with open(path, encoding='utf-8') as fh:
            testo = fh.read()
        modifiche = ti.get('edits') if isinstance(ti.get('edits'), list) else [ti]
        for m in modifiche:
            vecchio, nuovo = m.get('old_string'), m.get('new_string')
            if isinstance(vecchio, str) and isinstance(nuovo, str) and vecchio:
                testo = testo.replace(vecchio, nuovo) if m.get('replace_all') else testo.replace(vecchio, nuovo, 1)
    return testo


def _avviso_budget(rp, claude_dir, ti):
    """Avviso da aggiungere alla decisione se il CLAUDE.md globale supera il budget."""
    if rp != os.path.join(claude_dir, 'CLAUDE.md'):
        return ""
    try:
        n = _righe_dopo(rp, ti)
    except Exception:
        return ""
    budget = _budget()
    if n <= budget:
        return ""
    return (f" ATTENZIONE: dopo questa modifica il CLAUDE.md globale avra' {n} righe, "
            f"oltre il budget di {budget}. Se aggiungi una regola, togline o accorciane "
            "un'altra nella stessa modifica.")


def _persistenza(rp):
    """True se il path installa codice che parte da solo: git hook o servizio di avvio."""
    if (os.sep + '.git' + os.sep + 'hooks' + os.sep) in rp or rp.endswith(os.sep + '.git' + os.sep + 'hooks'):
        return True
    for radice in ('~/Library/LaunchAgents', '~/.config/systemd/user', '~/.config/autostart'):
        r = os.path.realpath(os.path.expanduser(radice))
        if rp == r or rp.startswith(r + os.sep):
            return True
    return False


def main():
    try:
        data = json.loads(sys.stdin.buffer.read().decode("utf-8"))
        tool = data.get('tool_name', '')
        if tool not in ('Edit', 'MultiEdit', 'Write', 'NotebookEdit'):
            sys.exit(0)

        ti = data.get('tool_input') or {}
        file_path = ti.get('file_path') or ti.get('notebook_path') or ''
        if not file_path:
            sys.exit(0)

        def chiede():
            """Telemetria di Arturo: questa guardia chiede conferma. Solo il nome e l'id della chiamata."""
            try:
                import importlib.util
                f = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'bin', 'telemetria.py')
                uso = data.get('tool_use_id')
                if os.path.exists(f) and isinstance(uso, str):
                    spec = importlib.util.spec_from_file_location('telemetria', f)
                    t = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(t)
                    t.chiede('protect_claude_md.py', uso)
            except Exception:  # noqa: BLE001 - la telemetria non ferma mai una guardia
                pass

        rp = os.path.realpath(os.path.expanduser(file_path))
        base = os.path.basename(rp).upper()
        claude_dir = os.path.realpath(os.path.expanduser('~/.claude'))

        session_id = data.get('session_id', '')
        safe_id = re.sub(r'[^a-zA-Z0-9_-]', '_', session_id)
        home_claude = os.path.expanduser('~/.claude')

        def unlocked(token):
            return os.path.exists(os.path.join(home_claude, f'{token}-{safe_id}'))

        under_claude = (rp == claude_dir or rp.startswith(claude_dir + os.sep))

        # Categoria 0: file di unlock -> sempre una decisione dell'utente
        if under_claude and 'UNLOCK' in base:
            chiede()
            _emit("ask", (
                f"File di unlock ({os.path.basename(rp)}): sbloccherebbe la protezione "
                "di CLAUDE.md, di config/hook o dei percorsi di avvio automatico. "
                "Conferma solo se l'hai chiesto tu."
            ))
            sys.exit(0)

        # Categoria 1: persistenza (git hook, servizi di avvio) -> prima di tutto
        if _persistenza(rp):
            if unlocked('system-unlock'):
                _emit("allow", "percorso di avvio automatico sbloccato da conferma utente")
                sys.exit(0)
            _emit("deny", (
                f"Percorso di avvio automatico protetto ({rp}): un git hook o un servizio "
                "di avvio esegue codice da solo, a ogni commit o a ogni accesso. "
                "Per procedere: 1) chiedi conferma esplicita all'utente. "
                f"2) esegui: touch ~/.claude/system-unlock-{safe_id} "
                "3) riprova la modifica."
            ))
            sys.exit(0)

        # Categoria 2: CLAUDE.md (ovunque)
        if base == 'CLAUDE.MD':
            avviso = _avviso_budget(rp, claude_dir, ti)
            if tool == 'Write' and not os.path.exists(rp):
                chiede()
                _emit("ask", (
                    f"Stai creando un CLAUDE.md nuovo in {os.path.dirname(rp)}: sono istruzioni "
                    "che Claude seguira' ogni volta che lavora in questa cartella. "
                    "Conferma se l'hai chiesto tu." + avviso
                ))
                sys.exit(0)
            if unlocked('claude-md-unlock'):
                _emit("allow", "CLAUDE.md sbloccato da conferma utente." + avviso)
                sys.exit(0)
            _emit("deny", (
                "CLAUDE.md protetto. Per modificarlo: "
                "1) chiedi conferma esplicita all'utente. "
                f"2) esegui: touch ~/.claude/claude-md-unlock-{safe_id} "
                "3) riprova la modifica." + avviso
            ))
            sys.exit(0)

        # Categoria 3: config/hook di Claude Code
        relativo = os.path.relpath(rp, claude_dir).replace(os.sep, '/') if under_claude else ''
        is_config = under_claude and (
            re.match(r'SETTINGS.*\.JSON$', base) is not None
            or base == '.CLAUDE.JSON'
            or (os.sep + 'hooks' + os.sep) in rp
            or rp.endswith(os.sep + 'hooks')
            or relativo == 'firme' or relativo.startswith('firme/')
            or relativo in ('bin/aggiornamenti.py', 'bin/aggiorna-applica.sh')
        )
        if is_config:
            # Un settings*.json che diventerebbe JSON non valido si ferma anche con l'unlock: un
            # settings rotto spegne deny e hook alla ricarica successiva (dalla config dell'autore,
            # 20/10/2026).
            if re.match(r'SETTINGS.*\.JSON$', base) is not None:
                try:
                    json.loads(_testo_dopo(rp, ti))
                except (ValueError, OSError) as e:
                    _emit("deny", f"{os.path.basename(rp)} non sarebbe JSON valido dopo la modifica ({e}). "
                          "Un settings rotto spegne deny e hook: correggi la modifica e riprova.")
                    sys.exit(0)
            if unlocked('config-unlock'):
                _emit("allow", "config/hook Claude Code sbloccati da conferma utente")
                sys.exit(0)
            _emit("deny", (
                f"File di config/hook di Claude Code protetto ({os.path.basename(rp)}). "
                "Modificarlo può disattivare le guardie di sicurezza. Per procedere: "
                "1) chiedi conferma esplicita all'utente. "
                f"2) esegui: touch ~/.claude/config-unlock-{safe_id} "
                "3) riprova la modifica."
            ))
            sys.exit(0)

        sys.exit(0)

    except Exception as e:
        print(f"protect_claude_md: errore interno ({e}), modifica bloccata per sicurezza", file=sys.stderr)
        sys.exit(2)


if __name__ == '__main__':
    # Claude Code scrive e legge in UTF-8. Su Windows la pipe è in cp1252 (16/10/2026).
    for _flusso in (sys.stdout, sys.stderr):
        try:
            _flusso.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass
    main()
