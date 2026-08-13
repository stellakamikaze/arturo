#!/usr/bin/env python3
"""PreToolUse(Bash) hook: gate operazioni gh CLI distruttive/sensibili.

Invocato dal dispatcher quando il comando contiene `gh ` (anche in catena).
github_issue_guard.py resta separato (blocca claude/anthropic nei testi issue/PR).

- exit 2 (blocco duro): repo delete, secret/variable set|delete, release delete,
  gh api con -X/--method DELETE|PUT|PATCH, gh auth token|logout.
- ask (conferma): pr merge, workflow run, run rerun (reversibili ma outward).
Fail-open su parsing.
"""
import json
import re
import sys
import signal


def _t(s, f):
    sys.exit(0)


if hasattr(signal, "SIGALRM"):
    signal.signal(signal.SIGALRM, _t)

BLOCK = [
    (r'\bgh\s+repo\s+delete\b', "eliminazione di un repository GitHub"),
    (r'\bgh\s+secret\s+(set|delete|remove)\b', "modifica/rimozione di secret GitHub"),
    (r'\bgh\s+variable\s+(set|delete|remove)\b', "modifica/rimozione di variabili GitHub"),
    (r'\bgh\s+release\s+delete\b', "eliminazione di una release"),
    (r'\bgh\s+auth\s+(token|logout)\b', "esposizione token / logout gh"),
    (r'\bgh\s+api\b[^|]*(-X|--method)\s*=?\s*(DELETE|PUT|PATCH)\b', "chiamata API GitHub mutante (DELETE/PUT/PATCH)"),
]
ASK = [
    (r'\bgh\s+pr\s+merge\b', "merge di una PR"),
    (r'\bgh\s+workflow\s+run\b', "avvio di un workflow CI"),
    (r'\bgh\s+run\s+rerun\b', "ri-esecuzione di un run CI"),
]


def main() -> int:
    try:
        if hasattr(signal, "SIGALRM"):
            signal.alarm(8)
        data = json.load(sys.stdin)
        if hasattr(signal, "SIGALRM"):
            signal.alarm(0)
    except Exception:
        return 0
    if data.get("tool_name") != "Bash":
        return 0
    cmd = (data.get("tool_input") or {}).get("command", "")
    if not isinstance(cmd, str) or not cmd:
        return 0

    for pat, why in BLOCK:
        if re.search(pat, cmd, re.IGNORECASE):
            sys.stderr.write(
                f"Bloccato: {why}. Operazione irreversibile/sensibile: "
                "eseguila manualmente in un terminale se e' intenzionale.\n"
            )
            return 2

    for pat, why in ASK:
        if re.search(pat, cmd, re.IGNORECASE):
            print(json.dumps({
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "ask",
                    "permissionDecisionReason": f"Operazione gh: {why}. Conferma.",
                }
            }))
            return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
