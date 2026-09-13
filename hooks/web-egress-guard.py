#!/usr/bin/env python3
"""PreToolUse hook: gate egress GET mascherato da ingest su WebFetch/jina/playwright.

Buco strutturale coperto: exfil-guard.py vede solo Bash curl/wget POST. I canali
WebFetch(GET), jina.read_url/parallel_read_url/capture_screenshot_url e
playwright.browser_navigate possono portare dati fuori mettendoli nella
query-string/path di una URL verso un host esterno (es. attacker/?d=<segreto>).

Decisione:
- host interno (Tailscale/localhost/LAN)         -> allow (silenzioso)
- host esterno + URL "pulita"                             -> allow (non rompe la ricerca web normale)
- host esterno + payload sospetto nell'URL                -> ask
    (command-substitution $()/backtick, o query mostruosa >=300 char)

Alleggerito 2026-07-15 (troppi prompt): rimosso il check
"blob opaco >=40 char per segmento" — falsi positivi sistematici su ID Google
Docs/Drive (44 char), hash CDN, URL firmate (S3/googleusercontent). Restano i
due segnali ad alta precisione.

Fail-open su qualsiasi errore. Zero dipendenze.
"""
import ipaddress
import json
import re
import signal
import sys
from urllib.parse import urlsplit


def _t(*_):
    sys.exit(0)


if hasattr(signal, "SIGALRM"):
    signal.signal(signal.SIGALRM, _t)

INTERNAL_HOSTS = frozenset(("localhost", "host.docker.internal", "0.0.0.0"))
INTERNAL_NETS = tuple(map(ipaddress.ip_network, (
    "127.0.0.0/8", "10.0.0.0/8", "192.168.0.0/16", "100.64.0.0/10",
)))
CMD_SUB = re.compile(r'\$\(|`')


def _internal_host(host: str | None) -> bool:
    if not host:
        return False
    normalized = host.lower().rstrip(".")
    if normalized in INTERNAL_HOSTS or normalized.endswith(".ts.net"):
        return True
    try:
        return any(ipaddress.ip_address(normalized) in network for network in INTERNAL_NETS)
    except ValueError:
        return False


def _iter_urls(tool_input):
    """Estrae stringhe URL da campi comuni (url, urls, href, uri)."""
    if not isinstance(tool_input, dict):
        return
    for k, v in tool_input.items():
        if not re.search(r'url|uri|href|link', k, re.IGNORECASE):
            continue
        if isinstance(v, str):
            yield v
        elif isinstance(v, list):
            for item in v:
                if isinstance(item, str):
                    yield item


def _suspicious(url):
    """True se l'URL verso host esterno trasporta un payload sospetto."""
    try:
        parts = urlsplit(url)
    except Exception:
        return False
    host = parts.hostname
    if not host or _internal_host(host):
        return False  # interno o non parsabile -> non gated qui
    if CMD_SUB.search(url):
        return True
    if len(parts.query or "") >= 300:  # query mostruosa = sospetta
        return True
    return False


def _ask(reason):
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "ask",
            "permissionDecisionReason": reason,
        }
    }))
    return 0


def main():
    try:
        if hasattr(signal, "SIGALRM"):
            signal.alarm(6)
        data = json.load(sys.stdin)
        if hasattr(signal, "SIGALRM"):
            signal.alarm(0)
    except Exception:
        return 0

    tool_input = data.get("tool_input") or {}
    for url in _iter_urls(tool_input):
        if _suspicious(url):
            return _ask(
                "L'URL verso un host esterno contiene un payload opaco/lungo nella "
                "query o nel path (possibile esfiltrazione di dati via GET). Conferma "
                "solo se il link e' legittimo e voluto."
            )
    return 0


if __name__ == "__main__":
    sys.exit(main())
