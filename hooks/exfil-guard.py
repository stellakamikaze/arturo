#!/usr/bin/env python3
"""PreToolUse(Bash) hook: chiede conferma sull'invio di dati verso host ESTERNI.

Due rami:

  (A) POST/upload  (curl/wget con metodo mutante o payload; python requests.post/
      urllib/httpx/smtplib) -> host esterno = ask, host interno = allow.
      Comportamento storico invariato.

  (B) EGRESS-GET mascherato (NUOVO): canali che portano dati fuori senza POST e che
      quindi sfuggivano al ramo A:
        - curl/wget GET con command-substitution $()/backtick nell'URL, o query con
          blob opaco/base64 lungo, verso host esterno
        - DNS-exfil: dig/nslookup/host con sottodominio che sembra dati (base64/hex >=20)
        - /dev/tcp/<host> redirection bash
        - nc/ncat verso host esterno
      Tutti -> ask (host interni esclusi).

comms-guard.py (messaggistica/email nota) gira PRIMA e BLOCCA quei casi. Gli scanner
PostToolUse (credential-leak) restano come secondo layer detective.
Fail-open su parsing. Zero dipendenze.
"""
import json
import re
import sys
import signal


def _t(s, f):
    sys.exit(0)


if hasattr(signal, "SIGALRM"):
    signal.signal(signal.SIGALRM, _t)

# Host considerati interni/fidati (nessun prompt). Aggiungi qui i tuoi host interni.
INTERNAL = re.compile(
    r'(\.ts\.net|localhost|127\.0\.0\.1|0\.0\.0\.0|'
    r'host\.docker\.internal|192\.168\.|(^|[^0-9])10\.|'
    r'100\.(6[4-9]|[7-9][0-9]|1[01][0-9]|12[0-7])\.)',
    re.IGNORECASE,
)
HOST = re.compile(r'https?://([A-Za-z0-9_.\-]+)', re.IGNORECASE)
EXT_HINT = re.compile(
    r'(smtp[.-][A-Za-z0-9.\-]+|api\.[A-Za-z0-9\-]+\.(com|net|io|org|co)|'
    r'hooks\.[A-Za-z0-9\-]+\.[A-Za-z]{2,})',
    re.IGNORECASE,
)

# Valori dei flag-dato di curl (payload): gli URL qui dentro sono DATI, non
# destinazioni. Vanno rimossi prima di determinare l'host di destinazione, cosi'
# una POST verso host interno con URL esterni nel corpo (es. un DB interno con link
# esterni come campi) non genera falsi positivi.
DATA_FLAG_VAL = re.compile(
    r'(?<![\w-])(?:--data-(?:raw|binary|urlencode|ascii)|--data|-d|--form|-F'
    r'|--upload-file|-T)\s*(?:\$?\'[^\']*\'|"[^"]*"|[^\s"\']+)',
    re.IGNORECASE,
)

# --- Ramo A: marcatori POST/upload ---
POST_MARKERS = re.compile(
    r'(curl|wget)\b[^\n]*(-X\s*(POST|PUT|PATCH|DELETE)|--request\s*(POST|PUT|PATCH|DELETE)'
    r'|-d\b|--data|-F\b|--form|-T\b|--upload-file)'
    r'|requests\.(post|put|patch|delete)|urllib\.request|httpx\.(post|put|patch)'
    r'|import\s+smtplib|smtplib\.',
    re.IGNORECASE,
)

# --- Ramo B: marcatori egress-GET ---
CMD_SUB = re.compile(r'\$\(|`')
CURL_CMDSUB = re.compile(r'\b(curl|wget)\b[^\n|;&]*(\$\(|`)', re.IGNORECASE)
DNS_CMD = re.compile(r'(^|[;&|]\s*)(dig|nslookup|host|drill)\b', re.IGNORECASE)
CURL_URL = re.compile(r'\b(?:curl|wget)\b[^\n|;&]*?\bhttps?://([A-Za-z0-9_.\-]+)([^\s"\']*)',
                      re.IGNORECASE)
OPAQUE = re.compile(r'[A-Za-z0-9_\-+/%=]{40,}')
DNS_EXFIL = re.compile(
    r'\b(dig|nslookup|host)\b[^\n|;&]*?([A-Za-z0-9+/=_-]{20,})\.[A-Za-z0-9.-]+\.[A-Za-z]{2,}',
    re.IGNORECASE,
)
DEV_TCP = re.compile(r'/dev/tcp/([A-Za-z0-9_.\-]+)', re.IGNORECASE)
NC_HOST = re.compile(r'\b(nc|ncat)\b\s+[^\n|;&]*?\b([A-Za-z0-9][A-Za-z0-9.\-]+\.[A-Za-z]{2,})\b',
                     re.IGNORECASE)


def _ask(reason=None):
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "ask",
            "permissionDecisionReason": reason or (
                "Invio di dati (POST/upload) verso un host esterno o non "
                "riconosciuto. Conferma solo se l'invio e' voluto "
                "(possibile esfiltrazione di credenziali/contenuti)."
            ),
        }
    }))
    return 0


def _external_host(h):
    return bool(h) and not INTERNAL.search(h)


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

    # ---- Ramo A: POST/upload (comportamento storico) ----
    if POST_MARKERS.search(cmd):
        # Valuta solo l'host di DESTINAZIONE: rimuovi i valori dei flag-dato
        # (payload) cosi' gli URL nel corpo non vengono scambiati per destinazioni.
        dest = DATA_FLAG_VAL.sub(" ", cmd)
        ext = False
        internal_seen = False
        for h in HOST.findall(dest):
            if INTERNAL.search(h):
                internal_seen = True
            else:
                ext = True
        if not ext:
            for m in EXT_HINT.finditer(dest):
                if not INTERNAL.search(m.group(0)):
                    ext = True
                    break
        if ext:
            return _ask()
        if internal_seen:
            return 0
        return _ask()  # POST ma host non chiaro -> conservativo

    # ---- Ramo B: egress-GET mascherato ----
    # /dev/tcp verso host esterno
    for h in DEV_TCP.findall(cmd):
        if _external_host(h):
            return _ask("Redirezione bash /dev/tcp verso un host esterno "
                        "(canale di esfiltrazione). Conferma solo se voluto.")
    # DNS-exfil: comando dig/nslookup/host con dati interpolati ($()/backtick) o
    # sottodominio che sembra dati codificati.
    if DNS_CMD.search(cmd) and (CMD_SUB.search(cmd) or DNS_EXFIL.search(cmd)):
        return _ask("Query DNS con dati interpolati o un sottodominio che sembra "
                    "codificato (possibile DNS-exfiltration). Conferma solo se voluto.")
    # nc/ncat verso host esterno
    m = NC_HOST.search(cmd)
    if m and _external_host(m.group(2)):
        return _ask("nc/ncat verso un host esterno (canale di esfiltrazione). "
                    "Conferma solo se voluto.")
    # curl/wget GET con command-substitution nell'URL verso host esterno
    if CURL_CMDSUB.search(cmd):
        for h, _ in CURL_URL.findall(cmd):
            if _external_host(h):
                return _ask("curl/wget verso host esterno con dati interpolati "
                            "nell'URL ($()/backtick): possibile esfiltrazione via GET. "
                            "Conferma solo se voluto.")
    # curl/wget GET con blob opaco lungo nell'URL verso host esterno
    for h, rest in CURL_URL.findall(cmd):
        if _external_host(h):
            mm = OPAQUE.search(rest or "")
            if mm and len(mm.group(0)) >= 40:
                return _ask("curl/wget verso host esterno con un blob opaco lungo "
                            "nell'URL: possibile esfiltrazione di dati via GET. "
                            "Conferma solo se voluto.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
