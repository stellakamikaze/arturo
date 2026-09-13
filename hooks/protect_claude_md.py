#!/usr/bin/env python3
"""Hook PreToolUse (Edit/MultiEdit/Write/NotebookEdit): protegge file critici.

Due categorie, ognuna con un unlock per-sessione distinto:

  CLAUDE.md (qualsiasi cartella)
    -> unlock: touch ~/.claude/claude-md-unlock-{session_id}

  Config e hook di Claude Code:
    ~/.claude/settings.json, settings.local.json, .claude.json
    ~/.claude/hooks/**
    -> unlock: touch ~/.claude/config-unlock-{session_id}

Motivo della categoria config/hook: senza questo, sotto defaultMode:acceptEdits
un'iniezione puo' riscrivere settings.json o disattivare un hook via tool Edit/Write
senza alcun prompt, neutralizzando ogni altra guardia. Il vettore shell
(sed -i, >, cp...) e' coperto separatamente da block-dangerous.py.

L'unlock (deny + istruzioni, non hard-deny in settings.json) preserva le
modifiche legittime: chiedi conferma all'utente, crea il touch file, riprova.

I file di unlock stessi (qualsiasi nome con "unlock" sotto ~/.claude) chiedono
sempre conferma anche via Edit/Write: un marker scritto dall'assistente senza una
decisione dell'utente sbloccherebbe da solo le due categorie. Il vettore shell
(touch) chiede conferma in block-dangerous.py.

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


def main():
    try:
        data = json.load(sys.stdin)
        tool = data.get('tool_name', '')
        if tool not in ('Edit', 'MultiEdit', 'Write', 'NotebookEdit'):
            sys.exit(0)

        file_path = (data.get('tool_input') or {}).get('file_path', '') or ''
        if not file_path:
            sys.exit(0)

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
            _emit("ask", (
                f"File di unlock ({os.path.basename(rp)}): sbloccherebbe la protezione "
                "di CLAUDE.md o di config/hook. Conferma solo se l'hai chiesto tu."
            ))
            sys.exit(0)

        # Categoria 1: CLAUDE.md (ovunque)
        if base == 'CLAUDE.MD':
            if unlocked('claude-md-unlock'):
                _emit("allow", "CLAUDE.md sbloccato da conferma utente")
                sys.exit(0)
            _emit("deny", (
                "CLAUDE.md protetto. Per modificarlo: "
                "1) chiedi conferma esplicita all'utente. "
                f"2) esegui: touch ~/.claude/claude-md-unlock-{safe_id} "
                "3) riprova la modifica."
            ))
            sys.exit(0)

        # Categoria 2: config/hook di Claude Code
        is_config = under_claude and (
            re.match(r'SETTINGS.*\.JSON$', base) is not None
            or base == '.CLAUDE.JSON'
            or (os.sep + 'hooks' + os.sep) in rp
            or rp.endswith(os.sep + 'hooks')
        )
        if is_config:
            if unlocked('config-unlock'):
                _emit("allow", "config/hook Claude Code sbloccati da conferma utente")
                sys.exit(0)
            _emit("deny", (
                f"File di config/hook di Claude Code protetto ({os.path.basename(rp)}). "
                "Modificarlo puo' disattivare le guardie di sicurezza. Per procedere: "
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
    main()
