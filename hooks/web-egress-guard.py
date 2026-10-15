#!/usr/bin/env python3
"""PreToolUse hook: gate egress GET mascherato da ingest su WebFetch/jina/tavily/browser.

Buco strutturale coperto: exfil-guard.py vede solo Bash curl/wget POST. I canali
WebFetch(GET), jina e tavily, playwright.browser_navigate e Claude in Chrome
(navigate, e browser_batch con gli URL annidati nelle azioni) possono portare dati fuori mettendoli nella
query-string/path di una URL verso un host esterno (es. attacker/?d=<segreto>).

Decisione:
- host interno (localhost/LAN/IP Tailscale, hosts-interni.local) -> allow (silenzioso).
  Un nome `.ts.net` non e' interno: con Tailscale Funnel puo' essere pubblico.
- host esterno + URL "pulita"                             -> allow (non rompe la ricerca web normale)
- host esterno + payload sospetto nell'URL                -> ask
    (command-substitution $()/backtick, o query mostruosa >=300 char)

Alleggerito 2026-07-15 (troppi prompt): rimosso il check
"blob opaco >=40 char per segmento" — falsi positivi sistematici su ID Google
Docs/Drive (44 char), hash CDN, URL firmate (S3/googleusercontent). Restano i
due segnali ad alta precisione.

Fail-open su qualsiasi errore. Zero dipendenze.
"""
from __future__ import annotations

import ipaddress
import json
import re
import signal
import sys
from pathlib import Path
from urllib.parse import urlsplit


def _t(*_):
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
CMD_SUB = re.compile(r'\$\(|`')


def _leggi_host_locali(path: Path):
    """Legge hosts-interni.local: una voce per riga, # commento, righe vuote ignorate.

    Una voce accettata da ip_network(strict=False) e' una rete, altrimenti e' un
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
                # Una rete piu' larga di /8 renderebbe fidata mezza internet: si ignora.
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
    # ::ffff:8.8.8.8 e' l'IPv4 8.8.8.8: si giudica quello.
    if addr.version == 6 and addr.ipv4_mapped is not None:
        addr = addr.ipv4_mapped
    return any(addr.version == network.version and addr in network for network in INTERNAL_NETS + LOCAL_NETS)


def _iter_urls(tool_input, profondita=0):
    """Estrae stringhe URL da campi comuni (url, urls, href, uri), anche annidati.

    Dal 15/10/2026 scende in dict e liste fino a 4 livelli: browser_batch di Claude in
    Chrome porta gli URL dentro actions[].input, e prima la guardia non li vedeva.
    """
    if profondita > 4:
        return
    if isinstance(tool_input, list):
        for item in tool_input:
            yield from _iter_urls(item, profondita + 1)
        return
    if not isinstance(tool_input, dict):
        return
    for k, v in tool_input.items():
        if re.search(r'url|uri|href|link', k, re.IGNORECASE):
            if isinstance(v, str):
                yield v
                continue
            if isinstance(v, list) and all(isinstance(x, str) for x in v):
                yield from v
                continue
        if isinstance(v, (dict, list)):
            yield from _iter_urls(v, profondita + 1)


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


def _segna_chiede(data):
    """Telemetria di Arturo: questa guardia ha chiesto conferma. Solo il nome e l'id della chiamata."""
    try:
        import importlib.util
        from pathlib import Path
        f = Path(__file__).resolve().parent.parent / "bin" / "telemetria.py"
        uso = data.get("tool_use_id") if isinstance(data, dict) else None
        if f.exists() and isinstance(uso, str):
            spec = importlib.util.spec_from_file_location("telemetria", f)
            t = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(t)
            t.chiede("web-egress-guard.py", uso)
    except Exception:  # noqa: BLE001 - la telemetria non ferma mai una guardia
        pass


def _ask(reason, data=None):
    _segna_chiede(data)
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
                "solo se il link e' legittimo e voluto.",
                data,
            )
    return 0


if __name__ == "__main__":
    sys.exit(main())
