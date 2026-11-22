#!/usr/bin/env python3
"""LG: block-dangerous, comms-guard e gh-destructive-guard in tempo lineare sui comandi ripetuti (22/11/2026, #6363).

Una regex `testa .* resto` riparte da ogni testa e corre fino in fondo alla riga: su 90.000 caratteri di `curl `
ripetuto block-dangerous impiegava 83 secondi, comms-guard oltre 90, gh-destructive-guard 21; `gws ` ripetuto
teneva comms-guard 52 secondi e `find ` block-dangerous 8. Il tetto di 25 secondi (TG, #6363) le fermava con una
conferma, ma il comando aspettava. Ora le stesse regole si leggono una volta sola, e i giudizi non cambiano:

  LG01  block-dangerous: le tre regole di DANGEROUS_ISTRUZIONE lette da _trova_regola danno lo stesso esito di
        re.search su testi casuali, con abbastanza casi veri da contare;
  LG02  block-dangerous: il find con -exec di _lettura_indiretta (cerca_dalle_teste) dà lo stesso match di
        re.search, gruppi compresi;
  LG03  comms-guard: ogni regola riscritta trova esattamente ciò che trovava la regola del 21/11, e le regex con
        una testa (SEND_ENDPOINTS, mailto:, link di chat, la variabile davanti a gmail) danno l'esito di re.search;
  LG04  gh-destructive-guard: _chiamate_api_github dà i tratti di _API_GITHUB.finditer, e le regole di BLOCK e
        ASK riscritte trovano ciò che trovavano prima;
  LG05  i comandi costruiti apposta (curl, wget, gws, find, open, $x, gh api ripetuti fino a 90.000 caratteri)
        stanno sotto i 6 secondi per guardia.

Con --baseline-ref ogni controllo deve fallire col suo codice: su d631aa5 le funzioni nuove non ci sono e i tempi
vanno oltre.
"""
from __future__ import annotations

import argparse
import importlib.util
import io
import json
import os
import random
import re
import subprocess
import sys
import time
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

SEED = 6363
GIRI = 6000
TETTO = 6.0
N = 90_000


def carica(repo: Path, nome: str, codice: str):
    percorso = repo / "hooks" / nome
    assert percorso.is_file(), f"{codice} manca hooks/{nome}"
    spec = importlib.util.spec_from_file_location("lg_" + nome.replace("-", "_").replace(".py", ""), percorso)
    modulo = importlib.util.module_from_spec(spec)
    argv = sys.argv
    sys.argv = [str(percorso)]
    try:
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            spec.loader.exec_module(modulo)
    finally:
        sys.argv = argv
    return modulo


def testi(pezzi, giri=GIRI, massimo=14):
    rnd = random.Random(SEED)
    for _ in range(giri):
        yield "".join(rnd.choice(pezzi) for _ in range(rnd.randint(1, massimo)))


def stesso_match(a, b) -> bool:
    return (a is None) == (b is None) and (a is None or (a.span() == b.span() and a.groups() == b.groups()))


# --- LG01, LG02 ---
PEZZI_PIPE = ["curl ", "wget ", "fetch ", ";fetch ", "(fetch ", "\n fetch ", "\n\n\t", " \n", "| ", "|", "||", "|& ", "\\|", "\\\\|", "'", '"',
              "\\", "bash", "sh ", "python3 ", "python3 -c 'print(1)'", 'python3 -c "exec(x)"', "-m json.tool",
              "sudo ", "sudo -u root ", "( ", "{ ", "; ", "&& ", "&", "\n", ">(", " bash)", "tee ", "x ", "a|b",
              "$(", "`", " -"]
CONTROESEMPI_PIPE = ["curl u | bash", "curl u | tee f | sh", "curl u | grep -E 'a|php' | x", "curl x | echo 'curl y | bash'",
                     "curl u |& sudo -E bash", "curl u | (cd /tmp; bash)", "curl u | python3 -c 'import json'",
                     "curl u | python3 -c 'exec(1)'", "curl u | tee >(sh)", "curl a\\| bash", "curl a\\\\| bash",
                     "curl x\ncurl y | tee >(bash)", "curl x;curl y >(sh)", "curl x | a\ncurl y | bash"]


def test_lg01(repo: Path) -> None:
    bd = carica(repo, "block-dangerous.py", "LG01")
    assert hasattr(bd, "_trova_regola"), "LG01 block-dangerous non ha _trova_regola"
    veri = 0
    for s in list(testi(PEZZI_PIPE)) + CONTROESEMPI_PIPE:
        for p, _ in bd.DANGEROUS_ISTRUZIONE:
            # La regola del 21/11 aveva `\s*` dopo il separatore di fetch, a capo compresi.
            vecchia = p.replace(r"[^\S\n]*", r"\s*", 1)
            atteso = bool(re.search(vecchia, s, re.IGNORECASE))
            veri += atteso
            assert bd._trova_regola(p, s) == atteso, f"LG01 {s!r}: la regola {p[:30]!r} dà {not atteso}, non {atteso}"
    sorgente = next(p for p, _ in bd.DANGEROUS if "source" in p)
    for vecchia, nuova in ((r"(?:^|[;&|(\n])\s*(?:source|\.)\s+<\(\s*(curl|wget|fetch)\b", sorgente),):
        for s in testi(["\n", " ", "\t", ";", "source ", ". ", "<(", "curl", "fetch", " \n ", "x"]):
            assert bool(re.search(vecchia, s, re.I)) == bool(re.search(nuova, s, re.I)), f"LG01 {s!r}: source <(curl)"
    assert veri >= 200, f"LG01 solo {veri} casi veri: il confronto non conta"


def test_lg02(repo: Path) -> None:
    bd = carica(repo, "block-dangerous.py", "LG02")
    assert hasattr(bd, "_FIND_EXEC"), "LG02 block-dangerous non ha _FIND_EXEC"
    vecchia = re.compile(r"\bfind\b(.*?)\s-(?:exec|execdir|ok|okdir)\s+(\S+)", bd._RE_NOMI)
    veri = 0
    for s in testi(["find ", "find", " -exec ", "-exec", " -ok ", "cat ", "\n", " ", "x", "-execdir", "\t", "{}", ";"]):
        a, b = vecchia.search(s), bd._fc.cerca_dalle_teste(bd._FIND_EXEC, bd._FIND_TESTA, s)
        veri += a is not None
        assert stesso_match(a, b), f"LG02 {s!r}: {a} invece di {b}"
    assert veri >= 300, f"LG02 solo {veri} casi veri"


# --- LG03 ---
# Le regole di comms-guard del 21/11/2026 (d631aa5), prima della riscrittura.
VECCHIE_COMMS = {
    "mutt": r"\bmutt\s+.*-s\b",
    "mail/mutt": r"(?:^|[;&|(`\n])\s*(?:sudo\s+|command\s+|env\s+)?(?:mail|mutt)\s+\S",
    "git send-email / imap-send": r"\bgit\b[^|;&\n]*\b(send-email|imap-send)\b",
    "gws Gmail send": r"\bgws\b[^\n|;&]*\bmessages\s+send\b",
    "gws gmail (invio)": r"\bgws\b.*\bgmail\b.*(?:\+send\b|\bdrafts\s+send\b)",
    "gws gmail (invio, col programma in una variabile)":
        r"\$\{?[A-Za-z_]\w*\}?\s+(?:\S+\s+)*?gmail\b[^\n|;&]*(?:\+send\b|\bdrafts\s+send\b|\bmessages\s+send\b)",
    "gws calendar (invito spedito agli invitati)":
        r"\bgws\b.*\bcalendar\b.*(?:sendUpdates[\"'\s:=\\]+(?:all|externalOnly)|sendNotifications[\"'\s:=\\]+true)",
    "gws drive (file aperto a chiunque abbia il link)":
        r"\bgws\b.*\bdrive\b.*\bpermissions\s+(?:create|update)\b[^\n]*\banyone\b",
    "gws drive (condivisione, con l'email di avviso)":
        r"\bgws\b.*\bdrive\b.*\bpermissions\s+create\b(?![^\n]*sendNotificationEmail[\"'\s:=\\]+false)"
        r"[^\n]*\b(?:user|group)\b",
    "nodemailer (invio email via Node)": r"(?s)\bnodemailer\b.*\b(?:sendMail|createTransport)\b",
    "gws gmail (inoltro, delega o filtro)":
        r"\bgws\b.*\bgmail\b.*\b(forwardingAddresses|updateAutoForwarding|delegates|filters)\b.*\b(create|update|patch)\b",
    "AppleScript Mail/Messages": r"(?s)\bosascript\b.*\b(Mail|Messages)\b",
    "EmailMessage/send (Python)": r"(?s)\bEmailMessage\b.*\bsend",
    "http.client verso un servizio di messaggistica":
        r"(?s)\bhttp\.client\b.*\b(telegram|slack|sendgrid|mailgun|discord|twilio|postmark|resend)\b",
    "mailgun (invio email)": r"\bapi\.(?:[a-z]{2}\.)?mailgun\.net/[^\s\"']*messages",
}
VECCHIO_ENDPOINT = re.compile(
    r"\b(curl|wget|http|https|fetch)\b.*("
    r"api\.telegram\.org/bot[^/]+/(sendmessage|sendphoto|sendvideo|senddocument|sendaudio)|"
    r"hooks\.slack\.com|slack\.com/api/chat\.postmessage|slack\.com/api/files\.upload|"
    r"api\.sendgrid\.com|api\.(?:eu\.)?mailgun\.net|api\.postmarkapp\.com|"
    r"api\.resend\.com|api\.mailjet\.com|"
    r"api\.brevo\.com|[a-z0-9.-]*\.smtp2go\.com|api\.sparkpost\.com|"
    r"api\.elasticemail\.com|[a-z0-9.-]*\.zeptomail\.[a-z]+|api\.mailchannels\.net|"
    r"email[.-][a-z0-9-]*\.amazonaws\.com|"
    r"graph\.microsoft\.com/[^\s]*/sendmail|"
    r"gmail\.googleapis\.com/[^\s]*/messages/send|"
    r"discord\.com/api/webhooks|discordapp\.com/api/webhooks|"
    r"api\.twilio\.com/[^\s]*/Messages|"
    r"graph\.facebook\.com/[^\s]*/messages|"
    r"hooks\.zapier\.com|hook\.(eu[0-9]*\.)?make\.com|hook\.integromat\.com"
    r")", re.IGNORECASE)
PEZZI_COMMS = ["gws ", "gws", "gmail ", "xgmail ", "gmail", "+send ", "drafts send ", "messages send ", "calendar ",
               "drive ", "permissions create ", "permissions update ", "anyone ", "user ", "group ",
               "sendNotificationEmail=false ", "sendUpdates=all ", "sendNotifications: true ", "forwardingAddresses ",
               "filters ", "create ", "patch ", "mutt ", "-s ", "git ", "send-email ", "imap-send ", "$G ", "${G} ",
               "nodemailer ", "sendMail ", "osascript ", "Mail ", "EmailMessage ", "send ", "http.client ", "slack ",
               "api.mailgun.net/", "api.eu.mailgun.net/", "messages ", "curl ", "wget ", "https ", "fetch ",
               "graph.microsoft.com/", "/sendmail ", "api.twilio.com/", "/Messages ", "gmail.googleapis.com/",
               "/messages/send ", "graph.facebook.com/", "/messages ", "hooks.slack.com ", "open ", "xdg-open ",
               "start ", "open location ", "webbrowser.open(", "mailto:", "wa.me/", "U=", "$U ", "| xargs open ",
               " ", " ", "\n", "|", ";", "&", "x", "'", '"', "\t", "/", "a=b", "="]


SEPARATORI = [" ", " ", "\n", "|", ";", "&", "x", "'", '"', "\t"]
PEZZI_REGOLA = {
    "calendar": ["gws ", "calendar ", "sendUpdates=all ", "sendUpdates: 'externalOnly' ", "sendNotifications=true "],
    "drive": ["gws ", "drive ", "permissions create ", "permissions update ", "anyone ", "user ", "group ",
              "sendNotificationEmail=false ", "sendNotificationEmail: false "] * 3,
    "inoltro": ["gws ", "gmail ", "forwardingAddresses ", "delegates ", "filters ", "create ", "patch ", "update "],
    "variabile": ["$G ", "${G} ", "gmail ", "xgmail ", "+send ", "drafts send ", "messages send ", "a "],
    "mail": ["mail ", "mutt ", "sudo ", "env ", "\n", " \n ", "\t", ";", "(", "x@y", "-s "],
}


def _vecchio_mailto_indiretto(comms, command: str) -> bool:
    for nome in dict.fromkeys(comms._VALORE_MAILTO.findall(command)):
        n = re.escape(nome)
        if re.search(r"(?<![\w-])" + comms._APRITORE_NOME + r"\b[^;&|\n]*\$\{?" + n + r"\b", command, re.IGNORECASE):
            return True
        if re.search(r"\b(?:os\.startfile|webbrowser\.open\w*)\s*\(\s*" + n + r"\b", command):
            return True
    return bool(comms._PIPE_MAILTO.search(command))


def test_lg03(repo: Path) -> None:
    comms = carica(repo, "comms-guard.py", "LG03")
    assert hasattr(comms, "_cerca"), "LG03 comms-guard non ha _cerca"
    nuove = {etichetta: p for p, etichetta, _ in comms.SEND_BINARIES}
    veri = dict.fromkeys(VECCHIE_COMMS, 0)
    # Ogni regola ha anche testi fatti dei suoi pezzi soli: dai pezzi di tutte, una regola a tre parole non esce mai.
    casi = list(testi(PEZZI_COMMS, giri=GIRI * 2))
    for pezzi in PEZZI_REGOLA.values():
        casi += list(testi(pezzi + SEPARATORI, giri=GIRI // 2, massimo=10))
    # Una testa che non arriva al confine e un'altra dopo: la seconda va provata.
    casi += ["open x\nopen wa.me/x", "open x;open mailto:a", "open x|xdg-open mailto:a", "curl x\ncurl hooks.slack.com",
             "start x\nstart t.me/share", "open x&open wa.me/x", "mailto:a\nmailto:b | xargs open"]
    for s in casi:
        for etichetta, vecchia in VECCHIE_COMMS.items():
            atteso = bool(re.search(vecchia, s, re.IGNORECASE))
            veri[etichetta] += atteso
            nuova = nuove[etichetta]
            if nuova == comms._VARIABILE_GMAIL_INVIO:
                trovato = comms._fc.cerca_dalle_teste(re.compile(nuova, re.IGNORECASE), comms._VARIABILE_GMAIL, s, "")
            else:
                trovato = re.search(nuova, s, re.IGNORECASE)
            assert bool(trovato) == atteso, f"LG03 {s!r}: la regola {etichetta!r} dà {not atteso}, non {atteso}"
        assert comms._cerca(comms.SEND_ENDPOINTS, s) == bool(VECCHIO_ENDPOINT.search(s)), f"LG03 {s!r}: SEND_ENDPOINTS"
        for regex in (comms._MAILTO_APERTO, comms._CHAT_APERTA, comms._PIPE_MAILTO):
            assert comms._cerca(regex, s) == bool(regex.search(s)), f"LG03 {s!r}: {regex.pattern[:30]!r}"
        assert comms._mailto_indiretto(s) == _vecchio_mailto_indiretto(comms, s), f"LG03 {s!r}: mailto indiretto"
    pochi = [e for e, k in veri.items() if k < 5]
    assert not pochi, f"LG03 regole con meno di 5 casi veri: il confronto non conta per {pochi}"


# --- LG04 ---
VECCHIE_GH = {
    "eliminazione di un repository GitHub via GraphQL": r'\bgh\s+api\b[^|]*\bdeleteRepository\b',
    "esposizione token / logout gh": r'\bgh\s+auth\s+status\b[^|;&\n]*\s(?:--show-token\b|-[a-zA-Z]*t\b)',
    "chiamata API GitHub mutante (DELETE/PUT/PATCH)": r'\bgh\s+api\b[^|]*(-X|--method)\s*=?\s*(DELETE|PUT|PATCH)\b',
    "cambio di visibilità di un repository": r'\bgh\s+repo\s+edit\b[^|;&\n]*--visibility\b',
    "creazione di un repository pubblico": r'\bgh\s+repo\s+create\b[^|;&\n]*--public\b',
    "gist pubblico": (r'\bgh\s+gist\s+create\b[^|;&\n]*\s(?:--public\b|-[a-zA-Z]*p\b)',
                      r'\bgh\s+gist\s+edit\b[^|;&\n]*--public\b'),
}
PEZZI_GH = ["curl ", "wget ", "http ", "https ", "xh ", "api.github.com", "API.GITHUB.COM", "/repos ", "-X ", "DELETE ",
            "gh ", "gh api ", "api ", "deleteRepository ", "--method=", "PUT ", "gh auth status ", "--show-token ", "-t ",
            "gh repo edit ", "--visibility ", "gh repo create ", "--public ", "gh gist create ", "gh gist edit ", "-p ",
            " ", " ", "|", ";", "&", "\n", "'", '"', "x", "\t"]


def test_lg04(repo: Path) -> None:
    gh = carica(repo, "gh-destructive-guard.py", "LG04")
    assert hasattr(gh, "_chiamate_api_github"), "LG04 gh-destructive-guard non ha _chiamate_api_github"
    nuove = {}
    for p, motivo in gh.BLOCK + gh.ASK:
        nuove.setdefault(motivo, []).append(p)
    tratti = 0
    for s in testi(PEZZI_GH, giri=GIRI * 2):
        attesi = [m.group(0) for m in gh._API_GITHUB.finditer(s)]
        tratti += len(attesi)
        assert gh._chiamate_api_github(s) == attesi, f"LG04 {s!r}: tratti {gh._chiamate_api_github(s)} invece di {attesi}"
        for motivo, vecchie in VECCHIE_GH.items():
            vecchie = vecchie if isinstance(vecchie, tuple) else (vecchie,)
            atteso = any(re.search(v, s, re.IGNORECASE) for v in vecchie)
            trovato = any(re.search(p, s, re.IGNORECASE) for p in nuove[motivo])
            if motivo == "esposizione token / logout gh":
                # Lo stesso motivo ha anche `gh auth token|logout`, che la riscrittura non tocca.
                trovato = bool(re.search(gh._dopo(r'gh\s+auth\s+status') + r'\s(?:--show-token\b|-[a-zA-Z]*t\b)', s,
                                         re.IGNORECASE))
            assert trovato == atteso, f"LG04 {s!r}: la regola {motivo!r} dà {trovato}, non {atteso}"
    assert tratti >= 300, f"LG04 solo {tratti} tratti verso api.github.com"


# --- LG06 ---
PEZZI_SCRITTURE = [">", ">>", "> ", ">(", "<", "<(", "$(<", "$( < ", "tee ", "touch ", "mkdir ", "chmod ", "dd ", "of=",
                   "sed ", "-i ", "-i", "~/.claude/", "/Users/x/.claude/", "settings.json", "settings.local.json",
                   "hooks/", "x.py", "config-unlock", "unlock", "CLAUDE.md", ".git/hooks/", "pre-commit",
                   "Library/LaunchAgents/", "a.plist", ".ssh/", "id_ed25519", "config", ".env", ".aws/", "credentials",
                   " ", " ", "|", ";", "&", "\n", ")", "'", '"', "x", "/"]
PEZZI_DECODIFICA = ["base64 ", "gbase64 ", "-d ", "--decode ", "-D", "xxd ", "-r ", "-pr ", "openssl enc ", "openssl base64 ",
                    "| ", "|", "||", "sh", "bash ", "sudo ", "python3 ", "python3 -", "/bin/sh ", "eval ", "$(", "`", "<(",
                    "bash -c ", ". ", "source ", " ", " ", "\n", ";", "&", "x", ")", "(", "-"]


def test_lg06(repo: Path) -> None:
    bd = carica(repo, "block-dangerous.py", "LG06")
    assert hasattr(bd, "_codice_nascosto") and hasattr(bd, "_corsa"), "LG06 block-dangerous non ha _codice_nascosto"
    vecchie = [
        (bd._riserva("config", r">>?\s*{p}|\b(?:tee|truncate|touch|chmod|chown)\b[^|;&]*{p}|\bdd\b[^|;&]*\bof={p}|"
                               r"\bsed\b[^|;&]*-i[^|;&]*{p}", "wa"), bd.CONFIG_WRITE_RE),
        (bd._riserva("claude-md", r">>?\s*{p}|" + bd._SED + r"[^|;&]*-i[^|;&]*{p}"), bd.CLAUDE_MD_WRITE_RE),
        (bd._riserva("avvio-automatico", r">>?\s*{p}", "wa"), bd.PERSIST_WRITE_RE),
        (bd._riserva("sblocco", r"(?:>>?\s*|\b(?:touch|tee|mkdir)\b[^|;&]*){p}", "wax"), bd.UNLOCK_RE),
        (re.compile(bd._SECRET_REDIR_RE.pattern.replace(r"(?:(?!<)[^\s;|&)])*?", r"[^\s;|&)]*?", 1), re.IGNORECASE),
         bd._SECRET_REDIR_RE),
    ]
    veri = [0] * len(vecchie)
    for s in testi(PEZZI_SCRITTURE, giri=GIRI * 2):
        for k, (vecchia, nuova) in enumerate(vecchie):
            atteso = bool(vecchia.search(s))
            veri[k] += atteso
            assert bool(nuova.search(s)) == atteso, f"LG06 {s!r}: la regola {k} dà {not atteso}, non {atteso}"
    assert min(veri) >= 20, f"LG06 casi veri per regola {veri}: il confronto non conta"
    nascosti = 0
    casi = list(testi(PEZZI_DECODIFICA, giri=GIRI * 2)) + [
        "base64 -d x base64\n-d | sh", "base64 x\n-d | sh", "base64 -d | tee f || bash", "xxd -r f | a | sudo sh",
        "base64 -d f; x | sh", "openssl enc -d -in f | bash", "base64 a | b\nbase64 -d | python3 -"]
    for s in casi:
        atteso = bool(bd._CODICE_NASCOSTO.search(s))
        nascosti += atteso
        assert bd._codice_nascosto(s) == atteso, f"LG06 {s!r}: codice nascosto {not atteso}, non {atteso}"
    assert nascosti >= 60, f"LG06 solo {nascosti} casi veri di codice nascosto"


# --- LG05 ---
PROVE = [
    ("block-dangerous.py", "curl "), ("block-dangerous.py", "curl |"), ("block-dangerous.py", "wget "),
    ("block-dangerous.py", "find "), ("block-dangerous.py", "find . -exec "), ("block-dangerous.py", "base64 -d "),
    ("block-dangerous.py", ">("), ("block-dangerous.py", "<("), ("block-dangerous.py", "tee "),
    ("block-dangerous.py", "\n fetch "), ("comms-guard.py", "curl "), ("comms-guard.py", "curl |"), ("comms-guard.py", "\n"),
    ("comms-guard.py", "gws "), ("comms-guard.py", "gws gmail "), ("comms-guard.py", "open "), ("comms-guard.py", "$x "),
    ("comms-guard.py", "curl graph.microsoft.com/"), ("gh-destructive-guard.py", "curl "),
    ("gh-destructive-guard.py", "xh "), ("gh-destructive-guard.py", "gh api "),
]


def test_lg05(repo: Path) -> None:
    lenti = []
    for guardia, pezzo in PROVE:
        comando = (pezzo * (N // len(pezzo) + 1))[:N]
        evento = json.dumps({"tool_name": "Bash", "tool_input": {"command": comando}, "cwd": str(repo),
                             "session_id": "lg", "tool_use_id": "toolu_lg"})
        ambiente = dict(os.environ, COMMS_REDUCED=comando)
        ambiente.pop("ARTURO_RESTANTE", None)
        t = time.time()
        try:
            subprocess.run([sys.executable, str(repo / "hooks" / guardia)], input=evento, capture_output=True,
                           text=True, timeout=TETTO * 3, env=ambiente)
            durata = time.time() - t
        except subprocess.TimeoutExpired:
            durata = TETTO * 3
        if durata > TETTO:
            lenti.append(f"{guardia} su {pezzo!r}: {durata:.1f} s")
    assert not lenti, "LG05 guardie oltre i " + f"{TETTO:.0f} secondi su {N} caratteri: " + "; ".join(lenti)


TESTS = {"LG01": test_lg01, "LG02": test_lg02, "LG03": test_lg03, "LG04": test_lg04, "LG06": test_lg06,
         "LG05": test_lg05}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--baseline-ref")
    args = parser.parse_args()
    repo = args.repo.resolve()
    if args.baseline_ref:
        rossi, altro = [], []
        for nome, test in TESTS.items():
            try:
                test(repo)
            except AssertionError as e:
                (rossi if str(e).startswith(nome) else altro).append(f"{nome}: {e}")
        assert not altro and len(rossi) == len(TESTS), \
            "baseline non discriminante: ogni controllo deve fallire col suo codice.\n" + "\n".join(altro + rossi)
        print(f"baseline {args.baseline_ref}: {len(rossi)}/{len(TESTS)} rossi col loro codice")
        return 0
    for nome, test in TESTS.items():
        test(repo)
        print(f"{nome} ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())
