#!/usr/bin/env python3
"""PreToolUse(Bash) hook: gate operazioni gh CLI distruttive/sensibili.

Invocato dal dispatcher quando il comando contiene `gh ` (anche in catena).
Blocca operazioni distruttive GitHub prima dell'esecuzione.

- exit 2 (blocco duro): repo delete (anche deleteRepository via GraphQL),
  secret/variable set|delete, release delete, gh api con -X/--method
  DELETE|PUT|PATCH, gh auth token|logout.
- ask (conferma): pr merge, workflow run, run rerun (reversibili ma outward);
  gh api che scrive: mutazioni GraphQL, query GraphQL lette da file (effetto non
  leggibile), POST espliciti o impliciti (-f/-F/--field/--raw-field/--input
  senza -X GET).
Fail-open su parsing.
"""
from __future__ import annotations

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
    (r'\bgh\s+api\b[^|]*\bdeleteRepository\b', "eliminazione di un repository GitHub via GraphQL"),
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


def _api_write(cmd: str) -> str | None:
    """Motivo per chiedere conferma su un `gh api` che scrive, altrimenti None."""
    for match in re.finditer(r'\bgh\s+api\b[^|;&\n]*', cmd, re.IGNORECASE):
        seg = match.group(0)
        if re.search(r'\bgh\s+api\s+graphql\b', seg, re.IGNORECASE):
            if re.search(r'\bmutation\b', seg, re.IGNORECASE):
                return "mutazione GraphQL GitHub"
            if re.search(r'(?:^|\s)--input(?:\s|=|$)|=@', seg):
                return "query GraphQL letta da file: effetto non verificabile"
            continue
        method = re.search(r'(?:^|\s)(?:-X|--method)(?:\s+|=)?([A-Za-z]+)', seg)
        body = re.search(r'(?:^|\s)(?:-f|-F|--field|--raw-field|--input)(?:\s|=|$)', seg)
        verb = method.group(1).upper() if method else ("POST" if body else "GET")
        if verb == "POST":
            return "chiamata API GitHub POST (anche implicita con -f/-F/--input)"
    return None


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

    reasons = [why for pat, why in ASK if re.search(pat, cmd, re.IGNORECASE)]
    api_write = _api_write(cmd)
    if api_write:
        reasons.append(api_write)
    if reasons:
        print(json.dumps({
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "ask",
                "permissionDecisionReason": f"Operazione gh: {reasons[0]}. Conferma.",
            }
        }))
        return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
