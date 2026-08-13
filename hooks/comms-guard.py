#!/usr/bin/env python3
"""PreToolUse(Bash) hook: enforce draft-first per comunicazioni esterne.

Blocca shell command che invierebbero email/messaggi senza approvazione esplicita.
Backstop concreto per la policy draft-first: mai inviare senza conferma esplicita.

Lettura JSON da stdin (Claude Code PreToolUse payload).
- exit 0 = consenti
- exit 2 = blocca (stderr → feedback al modello)
- fail-open su qualsiasi errore di parsing
"""
import json
import re
import sys
import signal


def _stdin_timeout(signum, frame):
    sys.exit(0)


if hasattr(signal, "SIGALRM"):
    signal.signal(signal.SIGALRM, _stdin_timeout)


SEND_BINARIES = [
    (r"\bsendmail\b", "sendmail"),
    (r"\bmail\s+-s\b", "mail -s"),
    (r"\bmutt\s+.*-s\b", "mutt"),
    (r"\bmailx\b", "mailx"),
    (r"\bswaks\b", "swaks"),
    (r"\bosascript\b.*\b(Mail|Messages)\b", "AppleScript Mail/Messages"),
    (r"\bwhatsapp[_/-]?send\b", "helper WhatsApp"),
    (r"\btelegram[_/-]?send\b", "helper Telegram"),
    # Python SMTP: invio email diretto (bypassava i binari noti).
    (r"\bsmtplib\b", "smtplib (invio email via Python)"),
    (r"\bSMTP_SSL\b", "SMTP_SSL (Python)"),
    (r"\bEmailMessage\b.*\bsend", "EmailMessage/send (Python)"),
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
    command = (data.get("tool_input") or {}).get("command", "")
    if not isinstance(command, str) or not command:
        return 0

    matched = None
    for pattern, label in SEND_BINARIES:
        if re.search(pattern, command, re.IGNORECASE):
            matched = label
            break
    if not matched and SEND_ENDPOINTS.search(command):
        matched = "endpoint messaggistica/email"

    if matched:
        sys.stderr.write(
            f"Bloccato: questo comando invierebbe una comunicazione esterna via {matched}. "
            "Bozza prima, mostra all'utente per approvazione, poi l'utente invia oppure "
            "conferma esplicitamente l'esecuzione di questo comando.\n"
        )
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
