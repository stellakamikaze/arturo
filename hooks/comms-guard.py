#!/usr/bin/env python3
"""PreToolUse(Bash) hook: enforce draft-first per comunicazioni esterne.

Chiede conferma (ask) sui comandi che invierebbero email o messaggi. Backstop
concreto per la policy draft-first: nessun invio parte senza un si' della persona.

Fino al 15/10/2026 bloccava (exit 2). Il blocco insegnava al modello ad aggirare
la regex: riscriveva il comando finché passava. Con ask la persona vede il
comando reale e decide con un click; il modello non ha niente da aggirare.

Lettura JSON da stdin (Claude Code PreToolUse payload).
- exit 0 senza output = consenti
- stdout JSON permissionDecision=ask = la persona conferma il comando reale
- fail-open su qualsiasi errore di parsing
"""
import importlib.util
import json
import os
import re
import shlex
import sys
import signal

# I comandi semplici li legge forma_comando.py, il lettore unico delle guardie: non spezza dentro le
# virgolette né dentro `2>&1` (#5122). Se manca, resta lo split di prima, come in comms-prefilter.
try:
    _spec_fc = importlib.util.spec_from_file_location(
        "forma_comando", os.path.join(os.path.dirname(os.path.abspath(__file__)), "forma_comando.py"))
    _fc = importlib.util.module_from_spec(_spec_fc)
    _spec_fc.loader.exec_module(_fc)
except Exception:
    _fc = None


def _stdin_timeout(signum, frame):
    sys.exit(0)


if hasattr(signal, "SIGALRM"):
    signal.signal(signal.SIGALRM, _stdin_timeout)


SEND_BINARIES = [
    (r"\bsendmail\b", "sendmail"),
    (r"\bmail\s+-s\b", "mail -s"),
    (r"\bmutt\s+.*-s\b", "mutt"),
    (r"\bmailx\b", "mailx"),
    (r"\bmsmtp\b", "msmtp"),
    (r"\bgit\b[^|;&\n]*\b(send-email|imap-send)\b", "git send-email / imap-send"),
    (r"\bgws\b[^\n|;&]*\bmessages\s+send\b", "gws Gmail send"),
    # gws: l'invio si ferma, la bozza no. `gws gmail +send` è la forma più comune.
    (r"\bgws\b.*\bgmail\b.*(?:\+send\b|\bdrafts\s+send\b)", "gws gmail (invio)"),
    # Inoltro automatico, deleghe e filtri della casella: spediscono la posta altrove
    # in silenzio, per sempre. Stesso rango di un invio.
    (r"\bgws\b.*\bgmail\b.*\b(forwardingAddresses|updateAutoForwarding|delegates|filters)\b.*\b(create|update|patch)\b",
     "gws gmail (inoltro, delega o filtro)"),
    (r"\bmail\s+\S+@\S+", "mail <indirizzo>"),
    # mail e mutt come programma, anche senza -s e con l'indirizzo in una variabile.
    (r"(?:^|[;&|(`\n])\s*(?:sudo\s+|command\s+|env\s+)?(?:mail|mutt)\s+\S", "mail/mutt"),
    (r"\bmutt\s+\S+@\S+", "mutt <indirizzo>"),
    # mailto: conta solo come argomento di un programma che apre un link (31/10/2026): dentro sed, un
    # heredoc o un --json è testo (un invito di calendario ha ORGANIZER;CN=…:mailto:…). Vedi _MAILTO_APERTO.
    (r"\bsmtps?://", "smtp:// (invio diretto)"),
    (r"\bswaks\b", "swaks"),
    # (?s): la forma naturale è un heredoc su più righe (`osascript <<'EOF'` e `tell application "Mail"` a capo,
    # review del 7/11/2026, finding 6).
    (r"(?s)\bosascript\b.*\b(Mail|Messages)\b", "AppleScript Mail/Messages"),
    (r"\bwhatsapp[_/-]?send\b", "helper WhatsApp"),
    (r"\btelegram[_/-]?send\b", "helper Telegram"),
    # Python SMTP: invio email diretto (bypassava i binari noti).
    (r"\bsmtplib\b", "smtplib (invio email via Python)"),
    (r"\bSMTP_SSL\b", "SMTP_SSL (Python)"),
    (r"(?s)\bEmailMessage\b.*\bsend", "EmailMessage/send (Python)"),
    # http.client verso un servizio di messaggistica: un POST senza curl ne' requests.
    (r"(?s)\bhttp\.client\b.*\b(telegram|slack|sendgrid|mailgun|discord|twilio|postmark|resend)\b",
     "http.client verso un servizio di messaggistica"),
]

SEND_ENDPOINTS = re.compile(
    r"\b(curl|wget|http|https|fetch)\b.*("
    r"api\.telegram\.org/bot[^/]+/(sendmessage|sendphoto|sendvideo|senddocument|sendaudio)|"
    r"hooks\.slack\.com|slack\.com/api/chat\.postmessage|slack\.com/api/files\.upload|"
    r"api\.sendgrid\.com|api\.mailgun\.net|api\.postmarkapp\.com|"
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
    r")",
    re.IGNORECASE,
)


# I programmi che aprono un link, quindi anche un mailto: che prepara un invio. Un elenco solo, per
# _MAILTO_APERTO e _mailto_indiretto.
_APRITORE_NOME = (r"(?:open(?!\s*\()|xdg-open|gio|kde-open|gnome-open|wslview|start|explorer(?:\.exe)?"
                  r"|Start-Process|saps)")
_MAILTO_APERTO = re.compile(
    r"(?:\b" + _APRITORE_NOME + r"\b"
    r"|\brundll32(?:\.exe)?\s+(?:url\.dll,\s*FileProtocolHandler|shell32\.dll,\s*ShellExec_RunDLL)\b"
    r"|\bopen\s+location\b"
    r"|\bpython[0-9.]*\s+-m\s+webbrowser\b|\bwebbrowser\.open(?:_new(?:_tab)?)?\s*\(|\bos\.startfile\s*\()"
    r"[^;&|\n]*mailto:",
    re.IGNORECASE,
)
# Un mailto: che arriva all'apritore per un'altra strada (1/11/2026, F23): `U="mailto:…"; open "$U"`,
# `printf 'mailto:…' | xargs open`, `u='mailto:…'; os.startfile(u)` aprivano la bozza senza conferma. Conta
# solo se l'apritore riceve davvero quel valore: `sed … mailto: … && open index.html` o `open('x').read()`
# di python con un mailto: nel testo non aprono nessuna bozza (review delle correzioni del 1/11/2026).
_VALORE_MAILTO = re.compile(r"""([A-Za-z_]\w*)\s*=\s*["']?[^"'\s;]*mailto:""", re.IGNORECASE)
_PIPE_MAILTO = re.compile(r"mailto:[^\n]*\|\s*xargs\s+(?:-\S+\s+)*(?:open|xdg-open|start|gio|wslview)\b", re.IGNORECASE)


def _mailto_indiretto(command: str) -> bool:
    for nome in dict.fromkeys(_VALORE_MAILTO.findall(command)):
        n = re.escape(nome)
        if re.search(r"(?<![\w-])" + _APRITORE_NOME + r"\b[^;&|\n]*\$\{?" + n + r"\b", command, re.IGNORECASE):
            return True
        if re.search(r"\b(?:os\.startfile|webbrowser\.open\w*)\s*\(\s*" + n + r"\b", command):
            return True
    return bool(_PIPE_MAILTO.search(command))
_HELP_ESENTI = frozenset(("gws", "gh"))
# Una sostituzione gira prima del programma: `gws --help $(gws gmail +send …)` invia (F24).
_SOSTITUZIONE = re.compile(r"\$\(|`|<\(|>\(")


def _senza_help(command: str) -> str:
    """Il comando senza i segmenti `gws … --help` e `gh … --help` (31/10/2026): chiedono l'aiuto, non
    inviano. Vale solo la forma lunga, come parola a sé e non come valore di un'opzione
    (`--subject --help` manda una mail con oggetto "--help"). mail, mailx, sendmail e msmtp no."""
    if _fc is not None:
        tratti = _fc.comandi_semplici(command, posizioni=True)
    else:
        tratti, inizio = [], 0
        for m in re.finditer(r"[|;&\n]+", command):
            tratti.append((inizio, m.start()))
            inizio = m.end()
        tratti.append((inizio, len(command)))
    via = []
    for a, b in tratti:
        seg = command[a:b]
        if _SOSTITUZIONE.search(seg):
            continue
        try:
            parole = shlex.split(seg)
        except ValueError:
            continue
        if not parole or os.path.basename(parole[0]) not in _HELP_ESENTI:
            continue
        for k, parola in enumerate(parole[1:], start=1):
            prima = parole[k - 1]
            if parola == "--help" and not (prima.startswith("-") and "=" not in prima):
                via.append((a, b))
                break
    for a, b in reversed(via):
        command = command[:a] + " " + command[b:]
    return command


_SMTP_URL = r"\bsmtps?://"
_SMTP_CURL_INVIO = re.compile(r"--mail-rcpt|--mail-from|(?<![\w-])-T\b|--upload-file|(?<![\w-])-d\b|--data", re.IGNORECASE)
_SMTP_SOLO_TESTO = re.compile(r"^\s*(?:grep|egrep|fgrep|rg|ugrep|echo|printf)\b")


def _opzioni_nascoste(seg: str) -> bool:
    """Opzioni di curl che non si leggono: un file di config (-K) o una variabile come argomento a sé
    (`curl smtp://x $OPTS` con --mail-rcpt dentro). Il valore di un'opzione (`--netrc-file $N`) no."""
    if re.search(r"(?<![\w-])-K\b|--config\b", seg):
        return True
    try:
        parole = shlex.split(seg)
    except ValueError:
        parole = seg.split()
    return any(p.startswith("$") and (i == 0 or not parole[i - 1].startswith("-"))
               for i, p in enumerate(parole))


def _smtp_invia(command: str) -> bool:
    """smtp:// conta come invio solo se un segmento lo usa per spedire. Non spedisce un curl senza
    destinatario né corpo (`curl smtp://host:587 -X NOOP` prova l'accesso), né un grep che cerca
    la stringa (21/10/2026: due falsi allarmi in una mattina)."""
    testo = command.replace("\\\n", " ")
    for seg in (_fc.comandi_semplici(testo) if _fc is not None else re.split(r"[|;&\n]", testo)):
        if not re.search(_SMTP_URL, seg, re.IGNORECASE):
            continue
        if re.search(r"\bcurl\b", seg) and not _SMTP_CURL_INVIO.search(seg) and not _opzioni_nascoste(seg):
            continue
        if _SMTP_SOLO_TESTO.match(seg):
            continue
        return True
    return False


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
    command = (data.get("tool_input") or {}).get("command", "")
    # Il dispatcher passa la versione RIDOTTA (senza heredoc scritti su file, vedi
    # comms-prefilter.py): si giudica il codice eseguito, non la prosa.
    reduced = os.environ.get("COMMS_REDUCED")
    if reduced is not None and reduced.strip():
        command = reduced
    if not isinstance(command, str) or not command:
        return 0

    command = _senza_help(command)
    aperto = _MAILTO_APERTO.search(command) or _mailto_indiretto(command)
    matched = "mailto: (apre un invio)" if aperto else None
    for pattern, label in ([] if matched else SEND_BINARIES):
        if pattern == _SMTP_URL:
            if _smtp_invia(command):
                matched = label
                break
            continue
        if re.search(pattern, command, re.IGNORECASE):
            matched = label
            break
    if not matched and SEND_ENDPOINTS.search(command):
        matched = "endpoint messaggistica/email"

    if matched:
        reason = (
            f"Questo comando invia una comunicazione esterna via {matched}. "
            "Bozza prima: conferma solo se hai già letto il testo e vuoi inviarlo "
            "così com'è."
        )
        sys.stdout.write(json.dumps({"hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "ask",
            "permissionDecisionReason": reason,
        }}) + "\n")
        return 0
    return 0


if __name__ == "__main__":
    # Claude Code scrive e legge in UTF-8. Su Windows la pipe è in cp1252 (16/10/2026).
    for _flusso in (sys.stdout, sys.stderr):
        try:
            _flusso.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass
    sys.exit(main())
