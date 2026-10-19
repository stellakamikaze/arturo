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
import json
import os
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
    (r"mailto:", "mailto: (apre un invio)"),
    (r"\bsmtps?://", "smtp:// (invio diretto)"),
    (r"\bswaks\b", "swaks"),
    (r"\bosascript\b.*\b(Mail|Messages)\b", "AppleScript Mail/Messages"),
    (r"\bwhatsapp[_/-]?send\b", "helper WhatsApp"),
    (r"\btelegram[_/-]?send\b", "helper Telegram"),
    # Python SMTP: invio email diretto (bypassava i binari noti).
    (r"\bsmtplib\b", "smtplib (invio email via Python)"),
    (r"\bSMTP_SSL\b", "SMTP_SSL (Python)"),
    (r"\bEmailMessage\b.*\bsend", "EmailMessage/send (Python)"),
    # http.client verso un servizio di messaggistica: un POST senza curl ne' requests.
    (r"\bhttp\.client\b.*\b(telegram|slack|sendgrid|mailgun|discord|twilio|postmark|resend)\b",
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

    matched = None
    for pattern, label in SEND_BINARIES:
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
