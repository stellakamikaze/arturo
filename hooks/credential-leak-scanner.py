#!/usr/bin/env python3
"""PostToolUse hook: rileva credenziali leaked nell'output dei tool.
Scansiona TUTTI gli output (non solo MCP) per catturare leak accidentali."""

import sys
import json
import re
import signal

def _stdin_timeout(signum, frame):
    sys.exit(0)

_HAS_SIGALRM = hasattr(signal, "SIGALRM")
if _HAS_SIGALRM:
    signal.signal(signal.SIGALRM, _stdin_timeout)

CREDENTIAL_PATTERNS = [
    # AWS
    (r'(?:A3T[A-Z0-9]|AKIA|AGPA|AIDA|AROA|AIPA|ANPA|ANVA|ASIA)[A-Z0-9]{16}', "AWS Access Key"),
    # GitHub
    (r'gh[pousr]_[A-Za-z0-9_]{36,}', "GitHub Token"),
    (r'github_pat_[A-Za-z0-9_]{22,}', "GitHub PAT"),
    # Generic API keys
    (r'(?i)(?:api[_-]?key|apikey|secret[_-]?key)\s*[:=]\s*["\']?[A-Za-z0-9\-_]{20,}', "API Key"),
    # Slack
    (r'xox[bporas]-[A-Za-z0-9\-]{10,}', "Slack Token"),
    # Stripe
    (r'sk_(?:live|test)_[A-Za-z0-9]{20,}', "Stripe Secret Key"),
    (r'pk_(?:live|test)_[A-Za-z0-9]{20,}', "Stripe Publishable Key"),
    # Supabase
    (r'(?i)supabase[_-]?(?:key|secret|anon)\s*[:=]\s*["\']?eyJ[A-Za-z0-9\-_]+', "Supabase Key"),
    # JWT (non tutti sono leak, ma in output tool sono sospetti)
    (r'eyJ[A-Za-z0-9\-_]{20,}\.eyJ[A-Za-z0-9\-_]{20,}\.[A-Za-z0-9\-_]{20,}', "JWT Token"),
    # Private keys
    (r'-----BEGIN (?:RSA |EC |DSA )?PRIVATE KEY-----', "Private Key"),
    # Anthropic
    (r'sk-ant-[A-Za-z0-9\-]{20,}', "Anthropic API Key"),
    # OpenAI (project keys: sk-proj-, org keys: sk-org-, legacy: sk- + 48 chars)
    (r'sk-(?:proj|org)-[A-Za-z0-9\-_]{20,}', "OpenAI Project/Org Key"),
    (r'sk-[A-Za-z0-9]{48,}', "OpenAI Legacy API Key"),
    # Neon
    (r'(?i)postgres(?:ql)?://[^:]+:[^@]+@[^/]+', "Database Connection String"),
    # Telegram
    (r'\d{8,10}:[A-Za-z0-9_-]{35}', "Telegram Bot Token"),
    # Brave Search
    (r'BSA[A-Za-z0-9]{10,}', "Brave Search API Key"),
    # Vercel
    (r'(?i)vercel[_-]?token\s*[:=]\s*["\']?[A-Za-z0-9]{24,}', "Vercel Token"),
    # Discord
    (r'[MN][A-Za-z\d]{23,}\.[\w-]{6}\.[\w-]{27,}', "Discord Bot Token"),
    # Firebase
    (r'AIza[A-Za-z0-9\-_]{35}', "Firebase/Google API Key"),
    # Generic long secret (32+ alphanum in env-like context)
    (r'(?i)(?:password|passwd|secret|token)\s*[:=]\s*["\']?[A-Za-z0-9\-_/+]{32,}', "Generic Secret"),
]

COMPILED = [(re.compile(p), name) for p, name in CREDENTIAL_PATTERNS]

def main():
    try:
        if _HAS_SIGALRM:
            signal.alarm(10)
        data = json.load(sys.stdin)
        if _HAS_SIGALRM:
            signal.alarm(0)
    except (json.JSONDecodeError, EOFError):
        sys.exit(0)

    # Claude Code usa "tool_response"; "tool_output" mantenuto come fallback
    tool_output = data.get("tool_response") or data.get("tool_output") or ""

    if isinstance(tool_output, (dict, list)):
        text = json.dumps(tool_output)
    else:
        text = str(tool_output)

    if len(text) < 10:
        sys.exit(0)

    findings = []
    for pattern, name in COMPILED:
        if pattern.search(text):
            findings.append(name)

    if findings:
        unique = list(dict.fromkeys(findings))
        warning = f"[WARNING] CREDENTIAL LEAK: Rilevate possibili credenziali nell'output:\n"
        for f in unique[:5]:
            warning += f"  - {f}\n"
        warning += "NON includere questi valori in commit, log, o output visibili."
        print(warning)

    sys.exit(0)

if __name__ == "__main__":
    main()
