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
import os
import re
import shlex
import signal
import subprocess
import sys


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
    (r"\b1//[A-Za-z0-9_-]{20,}\b", "Google refresh token"),
    (r"\b\d{6,12}:[A-Za-z0-9_-]{30,}\b", "Telegram bot token"),
    (r"\beyJ[A-Za-z0-9_-]{15,}\.eyJ[A-Za-z0-9_-]{15,}\.[A-Za-z0-9_-]{10,}", "JWT"),
    (r"postgres(?:ql)?://[^:@\s]+:[^@\s]+@[^/\s]+", "connection string con password"),
]
COMPILED = [(re.compile(p), name) for p, name in HIGH_CONF]


def _repo_for_command(command: str, cwd: str) -> str | None:
    location = os.path.abspath(cwd)
    for segment in re.split(r"&&|\|\||;|\||\n", command):
        try:
            tokens = shlex.split(segment)
        except ValueError:
            return None
        if not tokens:
            continue
        if tokens[0] == "cd" and len(tokens) > 1:
            location = os.path.abspath(os.path.join(location, os.path.expanduser(tokens[1])))
            continue
        if os.path.basename(tokens[0]) != "git":
            continue
        index = 1
        while index + 1 < len(tokens) and tokens[index] == "-C":
            location = os.path.abspath(os.path.join(location, os.path.expanduser(tokens[index + 1])))
            index += 2
        if index < len(tokens) and tokens[index] == "commit":
            return location
    return location if "gh pr create" in command else None


def _diff(repo: str, commit_all: bool) -> str | None:
    commands = [["git", "-C", repo, "diff", "--cached", "--no-color", "--no-ext-diff", "--no-textconv", "--unified=0"]]
    if commit_all:
        commands.append(["git", "-C", repo, "diff", "--no-color", "--no-ext-diff", "--no-textconv", "--unified=0"])
    output = []
    for command in commands:
        result = subprocess.run(command, capture_output=True, text=True, timeout=4, check=False)
        if result.returncode:
            return None
        output.append(result.stdout)
    return "\n".join(part for part in output if part)


def _ask(reason: str) -> int:
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "ask", "permissionDecisionReason": reason}}))
    return 0


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
    repo = _repo_for_command(command, cwd)
    if not repo:
        return _ask("Repository destinatario del commit non risolvibile: conferma prima di proseguire.")

    # `git commit -a/--all` mette in stage i file tracciati modificati DURANTE il
    # commit: al momento di questo check (PreToolUse) l'index non li contiene ancora,
    # quindi il solo `diff --cached` mancherebbe un secret in un file gia' tracciato.
    commit_all = bool(re.search(r"\bcommit\b[^|;&]*\s-{1,2}(a\b|all\b|[a-zA-Z]*a[a-zA-Z]*\b)", command))
    try:
        out = _diff(repo, commit_all)
    except Exception:
        out = None
    finally:
        if hasattr(signal, "SIGALRM"):
            signal.alarm(0)
    if out is None:
        return _ask("Scansione Git del repository destinatario fallita: conferma prima di proseguire.")

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
