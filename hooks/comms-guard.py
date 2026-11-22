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


# Ogni voce: (pattern, etichetta per la persona, famiglia del canale). La famiglia va nella telemetria come
# comms-guard.py.<famiglia> (21/11/2026, #5762): dice il tipo di canale, mai il servizio. "chat" non dice
# se è WhatsApp o Telegram, "api-invio" non dice quale API, come le famiglie dei segreti di
# commit-secret-gate. L'etichetta resta nel testo della conferma, che non esce.
FAMIGLIA_MAILTO = "mailto"
FAMIGLIA_ENDPOINT = "api-invio"
# Una corsa `.*` dopo una parola che si può ripetere: `_dopo("gws")` è `\bgws\b` più la corsa, che si ferma dove
# la parola ricomincia (#6363, 22/11/2026). Con `.*` re.search ripartiva da ogni gws e correva fino in fondo alla
# riga: 90.000 caratteri di `gws ` ripetuto tenevano comms-guard 52 secondi. Il risultato non cambia: se la regex
# parte da un gws, parte anche dall'ultimo gws prima di quello che cerca (banco LG04 in
# tests/test_guardie_lineari_2026_11_22.py). `classe` è il carattere della corsa, `.` o una classe come [^\n|;&].
def _dopo(testa: str, classe: str = ".", fine: str = r"\b") -> str:
    parola = r"\b" + testa + fine
    return parola + r"(?:(?!" + parola + r")" + classe + r")*"


# La variabile la cerca _VARIABILE_GMAIL, dalla prima soltanto: la corsa dopo attraversa tutto. gmail conta a inizio
# parola anche nella corsa che segue.
_VARIABILE_GMAIL_INVIO = (r"\$\{?[A-Za-z_]\w*\}?\s+(?:\S+\s+)*?gmail\b(?:(?!(?<=\s)gmail\b)[^\n|;&])*"
                          r"(?:\+send\b|\bdrafts\s+send\b|\bmessages\s+send\b)")
SEND_BINARIES = [
    (r"\bsendmail\b", "sendmail", "email"),
    (r"\bmail\s+-s\b", "mail -s", "email"),
    (_dopo("mutt", fine=r"\s+") + r"-s\b", "mutt", "email"),
    (r"\bmailx\b", "mailx", "email"),
    (r"\bmsmtp\b", "msmtp", "email"),
    (_dopo("git", r"[^|;&\n]") + r"\b(send-email|imap-send)\b", "git send-email / imap-send", "email"),
    (_dopo("gws", r"[^\n|;&]") + r"\bmessages\s+send\b", "gws Gmail send", "email"),
    # gws: l'invio si ferma, la bozza no. `gws gmail +send` è la forma più comune.
    (_dopo("gws") + _dopo("gmail") + r"(?:\+send\b|\bdrafts\s+send\b)", "gws gmail (invio)", "email"),
    # 21/11/2026 (#6259, rilievo S8 della revisione del 20/11): il programma in una variabile (`G=gws; $G gmail
    # +send`). `+send` e `drafts send` sono parole di gws: dopo una variabile il programma non si legge.
    (_VARIABILE_GMAIL_INVIO, "gws gmail (invio, col programma in una variabile)", "email"),
    # Un invito di calendario spedito agli invitati, e la condivisione di un file: chi riceve l'accesso riceve
    # anche un'email, e con type anyone il file diventa pubblico.
    (_dopo("gws") + _dopo("calendar") +
     r"(?:sendUpdates[\"'\s:=\\]+(?:all|externalOnly)|sendNotifications[\"'\s:=\\]+true)",
     "gws calendar (invito spedito agli invitati)", "email"),
    # Tace la condivisione con una persona quando il comando spegne l'email di avviso: lì non parte niente.
    (_dopo("gws") + _dopo("drive") + _dopo(r"permissions\s+(?:create|update)") + r"\banyone\b",
     "gws drive (file aperto a chiunque abbia il link)", "email"),
    (_dopo("gws") + _dopo("drive") +
     _dopo(r"permissions\s+create", fine=r"\b(?![^\n]*sendNotificationEmail[\"'\s:=\\]+false)") +
     r"\b(?:user|group)\b", "gws drive (condivisione, con l'email di avviso)", "email"),
    (r"(?s)" + _dopo("nodemailer") + r"\b(?:sendMail|createTransport)\b", "nodemailer (invio email via Node)", "email"),
    # Inoltro automatico, deleghe e filtri della casella: spediscono la posta altrove
    # in silenzio, per sempre. Stesso rango di un invio.
    (_dopo("gws") + _dopo("gmail") + _dopo("(?:forwardingAddresses|updateAutoForwarding|delegates|filters)") +
     r"\b(create|update|patch)\b",
     "gws gmail (inoltro, delega o filtro)", "email-inoltro"),
    (r"\bmail\s+\S+@\S+", "mail <indirizzo>", "email"),
    # mail e mutt come programma, anche senza -s e con l'indirizzo in una variabile.
    # Dopo il separatore gli spazi senza a capo: con `\s*` ogni a capo ripartiva e correva su tutti quelli dopo
    # (#6363). L'ultimo a capo prima del programma trova lo stesso.
    (r"(?:^|[;&|(`\n])[^\S\n]*(?:sudo\s+|command\s+|env\s+)?(?:mail|mutt)\s+\S", "mail/mutt", "email"),
    (r"\bmutt\s+\S+@\S+", "mutt <indirizzo>", "email"),
    # mailto: conta solo come argomento di un programma che apre un link (31/10/2026): dentro sed, un
    # heredoc o un --json è testo (un invito di calendario ha ORGANIZER;CN=…:mailto:…). Vedi _MAILTO_APERTO.
    (r"\bsmtps?://", "smtp:// (invio diretto)", "email"),
    (r"\bswaks\b", "swaks", "email"),
    # (?s): la forma naturale è un heredoc su più righe (`osascript <<'EOF'` e `tell application "Mail"` a capo,
    # review del 7/11/2026, finding 6).
    (r"(?s)" + _dopo("osascript") + r"\b(Mail|Messages)\b", "AppleScript Mail/Messages", "applescript"),
    (r"\bwhatsapp[_/-]?send\b", "helper WhatsApp", "chat"),
    (r"\btelegram[_/-]?send\b", "helper Telegram", "chat"),
    # Python SMTP: invio email diretto (bypassava i binari noti).
    (r"\bsmtplib\b", "smtplib (invio email via Python)", "email"),
    (r"\bSMTP_SSL\b", "SMTP_SSL (Python)", "email"),
    (r"(?s)" + _dopo("EmailMessage") + r"\bsend", "EmailMessage/send (Python)", "email"),
    # http.client verso un servizio di messaggistica: un POST senza curl ne' requests.
    (r"(?s)" + _dopo(r"http\.client") + r"\b(telegram|slack|sendgrid|mailgun|discord|twilio|postmark|resend)\b",
     "http.client verso un servizio di messaggistica", "api-invio"),
    # mailgun da codice (requests, fetch, urllib), anche sugli host regionali: SEND_ENDPOINTS vuole curl o wget.
    (_dopo(r"api\.(?:[a-z]{2}\.)?mailgun\.net/", r"[^\s\"']", "") + r"messages", "mailgun (invio email)", "api-invio"),
]

SEND_ENDPOINTS = re.compile(
    r"\b(curl|wget|http|https|fetch)\b.*("
    r"api\.telegram\.org/bot[^/]+/(sendmessage|sendphoto|sendvideo|senddocument|sendaudio)|"
    r"hooks\.slack\.com|slack\.com/api/chat\.postmessage|slack\.com/api/files\.upload|"
    r"api\.sendgrid\.com|api\.(?:eu\.)?mailgun\.net|api\.postmarkapp\.com|"
    r"api\.resend\.com|api\.mailjet\.com|"
    r"api\.brevo\.com|[a-z0-9.-]*\.smtp2go\.com|api\.sparkpost\.com|"
    r"api\.elasticemail\.com|[a-z0-9.-]*\.zeptomail\.[a-z]+|api\.mailchannels\.net|"
    r"email[.-][a-z0-9-]*\.amazonaws\.com|"
    r"graph\.microsoft\.com/(?:(?!graph\.microsoft\.com/)\S)*/sendmail|"
    r"gmail\.googleapis\.com/(?:(?!gmail\.googleapis\.com/)\S)*/messages/send|"
    r"discord\.com/api/webhooks|discordapp\.com/api/webhooks|"
    r"api\.twilio\.com/(?:(?!api\.twilio\.com/)\S)*/Messages|"
    r"graph\.facebook\.com/(?:(?!graph\.facebook\.com/)\S)*/messages|"
    r"hooks\.zapier\.com|hook\.(eu[0-9]*\.)?make\.com|hook\.integromat\.com"
    r")",
    re.IGNORECASE,
)
# La testa di SEND_ENDPOINTS: la regex si prova dal primo programma di ogni riga (forma_comando.cerca_dalle_teste,
# #6363). 90.000 caratteri di `curl ` ripetuto la tenevano oltre 90 secondi.
_ENDPOINT_TESTA = re.compile(r"\b(curl|wget|http|https|fetch)\b", re.IGNORECASE)


# I programmi che aprono un link, quindi anche un mailto: che prepara un invio. Un elenco solo, per
# _MAILTO_APERTO e _mailto_indiretto.
_APRITORE_NOME = (r"(?:open(?!\s*\()|xdg-open|gio|kde-open|gnome-open|wslview|start|explorer(?:\.exe)?"
                  r"|Start-Process|saps)")
_MAILTO_TESTA = (
    r"(?:\b" + _APRITORE_NOME + r"\b"
    r"|\brundll32(?:\.exe)?\s+(?:url\.dll,\s*FileProtocolHandler|shell32\.dll,\s*ShellExec_RunDLL)\b"
    r"|\bopen\s+location\b"
    r"|\bpython[0-9.]*\s+-m\s+webbrowser\b|\bwebbrowser\.open(?:_new(?:_tab)?)?\s*\(|\bos\.startfile\s*\()")
_MAILTO_APERTO = re.compile(_MAILTO_TESTA + r"[^;&|\n]*mailto:", re.IGNORECASE)
# Un mailto: che arriva all'apritore per un'altra strada (1/11/2026, F23): `U="mailto:…"; open "$U"`,
# `printf 'mailto:…' | xargs open`, `u='mailto:…'; os.startfile(u)` aprivano la bozza senza conferma. Conta
# solo se l'apritore riceve davvero quel valore: `sed … mailto: … && open index.html` o `open('x').read()`
# di python con un mailto: nel testo non aprono nessuna bozza (review delle correzioni del 1/11/2026).
_VALORE_MAILTO = re.compile(r"""([A-Za-z_]\w*)\s*=\s*["']?[^"'\s;]*mailto:""", re.IGNORECASE)
_PIPE_MAILTO = re.compile(r"mailto:[^\n]*\|\s*xargs\s+(?:-\S+\s+)*(?:open|xdg-open|start|gio|wslview)\b", re.IGNORECASE)
# Un link che apre WhatsApp o Telegram col destinatario e il testo già scritti: prepara un invio, come mailto:
# (21/11/2026, #6259, S8).
_CHAT_TESTA = (
    r"(?:\b" + _APRITORE_NOME + r"\b"
    r"|\bpython[0-9.]*\s+-m\s+webbrowser\b|\bwebbrowser\.open(?:_new(?:_tab)?)?\s*\(|\bos\.startfile\s*\()")
_CHAT_APERTA = re.compile(
    _CHAT_TESTA + r"[^;|\n]*(?:\bwa\.me/|\bapi\.whatsapp\.com/send|\bwhatsapp://send|\bt\.me/share|\btg://msg)",
    re.IGNORECASE,
)
# Le teste di queste regex: si provano dal primo apritore di ogni tratto (#6363). `open ` ripetuto le faceva ripartire
# da ogni open fino al primo `;`.
_TESTE = {
    _MAILTO_APERTO: (re.compile(_MAILTO_TESTA, re.IGNORECASE), ";&|\n"),
    _CHAT_APERTA: (re.compile(_CHAT_TESTA, re.IGNORECASE), ";|\n"),
    _PIPE_MAILTO: (re.compile("mailto:", re.IGNORECASE), "\n"),
    SEND_ENDPOINTS: (_ENDPOINT_TESTA, "\n"),
}
_APRITORE_TESTA = re.compile(r"(?<![\w-])" + _APRITORE_NOME + r"\b", re.IGNORECASE)
# La variabile davanti a `gmail +send` (SEND_BINARIES): la corsa dopo attraversa tutto, e conta solo la prima.
_VARIABILE_GMAIL = re.compile(r"\$\{?[A-Za-z_]\w*\}?\s+", re.IGNORECASE)


def _cerca(regex, testo: str) -> bool:
    """regex.search(testo), dalle teste di _TESTE se la regex ne ha (forma_comando.cerca_dalle_teste)."""
    if regex in _TESTE and _fc is not None:
        testa, confini = _TESTE[regex]
        return bool(_fc.cerca_dalle_teste(regex, testa, testo, confini))
    return bool(regex.search(testo))


def _mailto_indiretto(command: str) -> bool:
    # Senza un mailto: non c'è un valore da aprire, né una pipe che lo porta: findall ripartiva da ogni nome.
    if "mailto:" not in command.lower():
        return False
    for nome in dict.fromkeys(_VALORE_MAILTO.findall(command)):
        n = re.escape(nome)
        regex = re.compile(r"(?<![\w-])" + _APRITORE_NOME + r"\b[^;&|\n]*\$\{?" + n + r"\b", re.IGNORECASE)
        if _fc.cerca_dalle_teste(regex, _APRITORE_TESTA, command, ";&|\n") if _fc is not None else regex.search(command):
            return True
        if re.search(r"\b(?:os\.startfile|webbrowser\.open\w*)\s*\(\s*" + n + r"\b", command):
            return True
    return _cerca(_PIPE_MAILTO, command)
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
            parole = _parole(seg)
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


# shlex.split allunga la parola un carattere alla volta: su una parola lunga cresce col quadrato. forma_comando.parole
# dà le stesse parole in tempo lineare (#5347).
_parole = _fc.parole if _fc is not None else shlex.split
_SMTP_URL = r"\bsmtps?://"
_SMTP_CURL_INVIO = re.compile(r"--mail-rcpt|--mail-from|(?<![\w-])-T\b|--upload-file|(?<![\w-])-d\b|--data", re.IGNORECASE)
_SMTP_SOLO_TESTO = re.compile(r"^\s*(?:grep|egrep|fgrep|rg|ugrep|echo|printf)\b")


def _opzioni_nascoste(seg: str) -> bool:
    """Opzioni di curl che non si leggono: un file di config (-K) o una variabile come argomento a sé
    (`curl smtp://x $OPTS` con --mail-rcpt dentro). Il valore di un'opzione (`--netrc-file $N`) no."""
    if re.search(r"(?<![\w-])-K\b|--config\b", seg):
        return True
    try:
        parole = _parole(seg)
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
    aperto = _cerca(_MAILTO_APERTO, command) or _mailto_indiretto(command)
    matched, famiglia = ("mailto: (apre un invio)", FAMIGLIA_MAILTO) if aperto else (None, None)
    if not matched and _cerca(_CHAT_APERTA, command):
        matched, famiglia = "un link di WhatsApp o Telegram (apre un invio)", "chat"
    for pattern, label, fam in ([] if matched else SEND_BINARIES):
        if pattern == _SMTP_URL:
            if _smtp_invia(command):
                matched, famiglia = label, fam
                break
            continue
        if pattern == _VARIABILE_GMAIL_INVIO and _fc is not None:
            trovato = _fc.cerca_dalle_teste(re.compile(pattern, re.IGNORECASE), _VARIABILE_GMAIL, command, "")
        else:
            trovato = re.search(pattern, command, re.IGNORECASE)
        if trovato:
            matched, famiglia = label, fam
            break
    if not matched and _cerca(SEND_ENDPOINTS, command):
        matched, famiglia = "endpoint messaggistica/email", FAMIGLIA_ENDPOINT

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
        # Il dispatcher di Arturo chiede anche quale regola ha parlato. Senza la variabile esce il solo JSON.
        if os.environ.get("ARTURO_REGOLA") == "1":
            sys.stdout.write(f"REGOLA: {famiglia}\n")
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
