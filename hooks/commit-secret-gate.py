#!/usr/bin/env python3
"""PreToolUse(Bash) hook: gate anti-leak prima di `git commit` / `gh pr create`.

Scansiona il diff STAGED (git diff --cached) alla ricerca di secret ad ALTA
confidenza nelle righe aggiunte. Se trovati -> ask (non blocco: evita di rompere
commit legittimi; l'utente decide). Usa un set curato di pattern per minimizzare
i falsi positivi (NO "password=..." generico che matcha codice/test).

I leak in un commit sono irreversibili una volta pushati: questo e' l'unico
layer PREVENTIVO (gli scanner PostToolUse avvisano a cose fatte).

Fail-open su qualsiasi errore. Legge cwd dal payload per lanciare git nel repo giusto.
"""
import json
import re
import sys
import os
import subprocess
import signal


def _stdin_timeout(signum, frame):
    sys.exit(0)


if hasattr(signal, "SIGALRM"):
    signal.signal(signal.SIGALRM, _stdin_timeout)


HIGH_CONF = [
    (r"-----BEGIN (?:RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----", "chiave privata"),
    (r"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b", "AWS Access Key"),
    (r"\bgh[pousr]_[A-Za-z0-9_]{36,}\b", "GitHub token"),
    (r"\bgithub_pat_[A-Za-z0-9_]{22,}\b", "GitHub PAT"),
    (r"\bsk-ant-[A-Za-z0-9-]{20,}", "Anthropic API key"),
    (r"\bsk_live_[A-Za-z0-9]{20,}", "Stripe live key"),
    (r"\bxox[baprs]-[A-Za-z0-9-]{10,}", "Slack token"),
    (r"\bAIza[A-Za-z0-9_-]{35}\b", "Google API key"),
    (r"\bGOCSPX-[A-Za-z0-9_-]{20,}\b", "Google OAuth client secret"),
    (r"\beyJ[A-Za-z0-9_-]{15,}\.eyJ[A-Za-z0-9_-]{15,}\.[A-Za-z0-9_-]{10,}", "JWT"),
    (r"postgres(?:ql)?://[^:@\s]+:[^@\s]+@[^/\s]+", "connection string con password"),
]
COMPILED = [(re.compile(p), name) for p, name in HIGH_CONF]


def main() -> int:
    try:
        if hasattr(signal, "SIGALRM"):
            signal.alarm(6)
        data = json.load(sys.stdin)
    except Exception:
        return 0

    if data.get("tool_name") != "Bash":
        return 0
    command = (data.get("tool_input") or {}).get("command", "")
    if not isinstance(command, str) or not command:
        return 0
    cwd = data.get("cwd") or os.path.expanduser("~")

    # `git commit -a/--all` mette in stage i file tracciati modificati DURANTE il
    # commit: al momento di questo check (PreToolUse) l'index non li contiene ancora,
    # quindi il solo `diff --cached` mancherebbe un secret in un file gia' tracciato.
    # In quel caso si scansiona anche il working tree (diff sui tracciati).
    commit_all = bool(re.search(r"\bcommit\b[^|;&]*\s-{1,2}(a\b|all\b|[a-zA-Z]*a[a-zA-Z]*\b)", command)) \
        and bool(re.search(r"\bgit\b", command))
    try:
        diffs = [subprocess.run(
            ["git", "-C", cwd, "diff", "--cached", "--no-color", "--unified=0"],
            capture_output=True, text=True, timeout=4,
        ).stdout]
        if commit_all:
            diffs.append(subprocess.run(
                ["git", "-C", cwd, "diff", "--no-color", "--unified=0"],
                capture_output=True, text=True, timeout=4,
            ).stdout)
        out = "\n".join(d for d in diffs if d)
    except Exception:
        return 0
    finally:
        if hasattr(signal, "SIGALRM"):
            signal.alarm(0)

    if not out:
        return 0

    added = "\n".join(
        ln[1:] for ln in out.splitlines()
        if ln.startswith("+") and not ln.startswith("+++")
    )
    if not added:
        return 0

    found = []
    for rx, name in COMPILED:
        if rx.search(added):
            found.append(name)
    if not found:
        return 0

    uniq = list(dict.fromkeys(found))
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "ask",
            "permissionDecisionReason": (
                "Possibile secret nel diff staged: " + ", ".join(uniq[:5]) + ". "
                "Un leak pushato e' irreversibile. Conferma solo dopo aver "
                "verificato che non sia una credenziale reale."
            ),
        }
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
