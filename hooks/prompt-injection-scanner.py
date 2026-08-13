#!/usr/bin/env python3
"""PostToolUse hook: scansiona output MCP e tool per pattern di prompt injection.
Lightweight — no dipendenze esterne, regex-based."""

import sys
import json
import re
import signal

def _stdin_timeout(signum, frame):
    sys.exit(0)

_HAS_SIGALRM = hasattr(signal, "SIGALRM")
if _HAS_SIGALRM:
    signal.signal(signal.SIGALRM, _stdin_timeout)

# Pattern di injection noti (da threat DB pubblici + CVE-2025-59536)
INJECTION_PATTERNS = [
    # Istruzioni dirette al modello
    r'(?i)ignore\s+(all\s+)?previous\s+instructions',
    r'(?i)ignore\s+(all\s+)?above\s+instructions',
    r'(?i)disregard\s+(all\s+)?previous',
    r'(?i)forget\s+(all\s+)?(your\s+)?instructions',
    r'(?i)you\s+are\s+now\s+(a|an)\s+',
    r'(?i)new\s+system\s+prompt',
    r'(?i)override\s+(system|safety)\s+(prompt|instructions)',
    r'(?i)act\s+as\s+if\s+you\s+(are|were)\s+',
    r'(?i)pretend\s+(that\s+)?you\s+(are|were)\s+',
    r'(?i)from\s+now\s+on\s+you\s+(will|must|should)',
    # Istruzioni dirette in ITALIANO (la lingua di lavoro: prima evadevano del tutto)
    r'(?i)ignora\s+(tutte\s+)?(le\s+)?(precedenti\s+)?istruzioni',
    r'(?i)dimentica\s+(tutte\s+)?(le\s+)?(tue\s+)?(precedenti\s+)?istruzioni',
    r'(?i)dimentica\s+quanto\s+(detto|scritto)\s+(sopra|prima)',
    r'(?i)non\s+seguire\s+le\s+istruzioni\s+(precedenti|iniziali|di\s+sistema)',
    r'(?i)(le\s+)?istruzioni\s+(iniziali|precedenti)\s+sono\s+(obsolete|scadute|annullate)',
    r'(?i)nuove?\s+istruzioni\s+di\s+sistema',
    r'(?i)sei\s+(ora\s+|adesso\s+)un[\'a]?\s+(assistente|intelligenza|modello|AI)',
    # Esfiltrazione
    r'(?i)curl\s+.*\|\s*bash',
    r'(?i)wget\s+.*\|\s*sh',
    r'(?i)(curl|wget|nc|ncat)\s+.*\b(api[_-]?key|token|secret|password|credential)',
    r'(?i)echo\s+\$\w+\s*[|>].*\b(curl|wget|nc)',
    # Exfil via DNS/HTTP
    r'(?i)\$\(.*\)\.\w+\.(com|net|io|xyz)',
    r'(?i)base64.*\|\s*(curl|wget)',
    # Hidden instructions in markdown/HTML
    r'<!--\s*(?:system|instruction|prompt)',
    r'<\s*(?:script|img\s+src\s*=\s*["\'](?:https?://|data:))',
    # Zero-width e caratteri invisibili (unicode injection)
    r'[\u200b\u200c\u200d\u2060\ufeff\u00ad]',
    r'[\u2066\u2067\u2068\u2069\u202a\u202b\u202c\u202d\u202e]',
    # PUA (Private Use Area)
    r'[\ue000-\uf8ff]',
    r'[\U000f0000-\U000ffffd]',
]

COMPILED_PATTERNS = [re.compile(p) for p in INJECTION_PATTERNS]

def scan(text: str) -> list[str]:
    """Ritorna lista di pattern trovati."""
    if not text:
        return []
    findings = []
    for i, pattern in enumerate(COMPILED_PATTERNS):
        matches = pattern.findall(text)
        if matches:
            # Limita per evitare output enorme
            sample = matches[0] if isinstance(matches[0], str) else str(matches[0])
            findings.append(f"Pattern #{i}: {INJECTION_PATTERNS[i][:60]}... → '{sample[:80]}'")
    return findings

def main():
    try:
        if _HAS_SIGALRM:
            signal.alarm(10)
        data = json.load(sys.stdin)
        if _HAS_SIGALRM:
            signal.alarm(0)
    except (json.JSONDecodeError, EOFError):
        sys.exit(0)

    tool_name = data.get("tool_name", "")
    # Claude Code usa "tool_response"; "tool_output" mantenuto come fallback
    tool_output = data.get("tool_response") or data.get("tool_output") or ""

    # Scansiona solo output da MCP server e WebFetch (superficie di attacco esterna)
    is_mcp = tool_name.startswith("mcp__")
    is_web = tool_name in ("WebFetch", "WebSearch")

    if not (is_mcp or is_web):
        sys.exit(0)

    # Estrai testo dall'output
    if isinstance(tool_output, (dict, list)):
        text = json.dumps(tool_output)
    else:
        text = str(tool_output)

    findings = scan(text)

    if findings:
        # Non blocca (exit 0), ma avvisa nel context
        warning = f"[WARNING] SECURITY: Possibile prompt injection in output di {tool_name}:\n"
        for f in findings[:5]:  # Max 5 finding
            warning += f"  - {f}\n"
        warning += "Verifica il contenuto prima di procedere."
        print(warning)

    sys.exit(0)

if __name__ == "__main__":
    main()
