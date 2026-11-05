#!/usr/bin/env python3
"""PreToolUse(Bash) hook: gate sulle operazioni DATI irreversibili.

Copre i buchi NON gestiti da block-dangerous.py (che già fa rm/config/segreti/
docker-volume-rm) ne' da comms/exfil. Bersaglio: gli errori classici sui dati —
DB sovrascritto, sync nella direzione sbagliata, dismissione stack senza dump
verificato.

Tutto CHIEDE CONFERMA (permissionDecision:"ask", exit 0) — non blocca duro:
queste operazioni hanno usi legittimi, ma sono punti di non-ritorno sui DATI e
meritano uno speed-bump prima dell'esecuzione (stessa filosofia di block-dangerous
per rm su tree protetti).

Casi coperti:
- SQL distruttivo: DROP TABLE/DATABASE/SCHEMA, TRUNCATE, DELETE FROM senza WHERE
  (solo se c'è un client DB nel comando: mysql/psql/sqlite3/mariadb/mongo...).
  Un WHERE dentro una stringa SQL tra apici ('WHERE') non conta come clausola.
- docker compose down -v / --volumes, anche con opzioni prima di down (-f, -p)
  e nella forma docker-compose (cancella i volumi = i dati dei container)
- rsync --delete verso una destinazione REMOTA (host:path) = può cancellare
  dati sul server se la direzione è sbagliata; dal 17/10/2026 (#3506) anche verso
  una cartella LOCALE (un disco di backup, i Documenti): cancella lì tutto quello
  che la sorgente non ha. Un dry-run (-n, --dry-run) non chiede.
- redirezione/overwrite di un file DB (> *.db / *.sqlite / *.sql.gz)

Fail-open su parsing. Zero dipendenze.
"""
import importlib.util
import json
import os
import re
import signal
import sys


def _stdin_timeout(signum, frame):
    sys.exit(0)


if hasattr(signal, "SIGALRM"):
    signal.signal(signal.SIGALRM, _stdin_timeout)


DB_CLIENT_RE = re.compile(
    r"\b(mysql|mariadb|psql|postgres|sqlite3?|mongo(sh)?|clickhouse-client|"
    r"redis-cli|docker\s+exec|docker\s+compose\s+exec)\b",
    re.IGNORECASE,
)

# --- SQL distruttivo (richiede un client DB nel comando per evitare falsi
#     positivi su testo/markdown) ---
SQL_DESTRUCTIVE = [
    (r"\bDROP\s+(TABLE|DATABASE|SCHEMA)\b", "DROP di tabella/database"),
    (r"\bTRUNCATE\s+(TABLE\s+)?\w", "TRUNCATE (svuota la tabella)"),
]
# DELETE FROM ... senza WHERE (cancella tutte le righe)
DELETE_FROM_RE = re.compile(r"\bDELETE\s+FROM\s+[`\"']?\w[\w.`\"']*", re.IGNORECASE)


def _delete_without_where(cmd: str) -> bool:
    """True se uno statement DELETE FROM non ha una clausola WHERE vera.

    Lo statement arriva fino al primo ';'. Le stringhe SQL tra apici singoli
    si tolgono prima di cercare WHERE: `RETURNING 'WHERE'` non è una clausola.
    """
    for match in DELETE_FROM_RE.finditer(cmd):
        statement = cmd[match.end():].split(";", 1)[0]
        statement = re.sub(r"'[^']*'", "", statement)
        if not re.search(r"\bWHERE\b", statement, re.IGNORECASE):
            return True
    return False


DOCKER_DOWN_VOL_RE = re.compile(
    r"\bdocker(?:\s+compose|-compose)\b[^|&;]*\sdown\b[^|&;]*(?:\s-v\b|\s--volumes\b)", re.IGNORECASE
)

# rsync --delete verso destinazione remota (host:path). Il ':' con un host prima
# indica una dest remota; --delete può cancellare file sul lato remoto.
RSYNC_DELETE_REMOTE_RE = re.compile(
    r"\brsync\b[^|&;\n]*--delete\b[^|&;\n]*\s[\w.-]+@?[\w.-]+:", re.IGNORECASE
)
# 15/10/2026: rsync --delete citato in un heredoc che nessuno esegue, o in un dry-run,
# non chiede. Il flag si cerca fuori dalle virgolette, così `-e "ssh -n"` non vale.
RSYNC_DRY_RUN_RE = re.compile(
    r"\s(?:-(?!-)[A-Za-z]*n[A-Za-z]*|--dry-run)(?=\s|$)"
)
# Gli heredoc li riconosce heredoc.py, lo stesso modulo delle altre guardie (15/10/2026).
# Se manca, nessun corpo sparisce: la guardia controlla tutto il testo.
try:
    _spec_hd = importlib.util.spec_from_file_location(
        "arturo_heredoc", os.path.join(os.path.dirname(os.path.abspath(__file__)), "heredoc.py"))
    _hd = importlib.util.module_from_spec(_spec_hd)
    _spec_hd.loader.exec_module(_hd)
    _togli_heredoc = _hd.togli
except Exception:
    def _togli_heredoc(cmd, via, segnaposto=None):
        return cmd


def _senza_testo(cmd: str) -> str:
    """Il comando senza i corpi di heredoc che vanno a un lettore (cat, tee) o a codice di un
    interprete che non lancia programmi. Nel dubbio il corpo resta (vedi heredoc.py)."""
    return _togli_heredoc(cmd, lambda h: h.inerte() or h.codice_inerte()).replace("\\\n", " ")


# Ogni rsync con --delete (anche --del, --delete-after, --delete-excluded), verso dove che sia.
RSYNC_DELETE_RE = re.compile(r"\brsync\b[^|&;\n]*--del(?:ete)?\b", re.IGNORECASE)


def _rsync_delete_reale(cmd: str) -> str:
    """"remota" o "locale" per il primo rsync --delete che non è un dry-run, "" se non ce n'è."""
    testo = _senza_testo(cmd)
    for m in RSYNC_DELETE_RE.finditer(testo):
        fine = re.search(r"[|&;\n]", testo[m.start():])
        segmento = testo[m.start(): m.start() + fine.start()] if fine else testo[m.start():]
        if not RSYNC_DRY_RUN_RE.search(re.sub(r"\"[^\"]*\"|'[^']*'", " ", segmento)):
            return "remota" if RSYNC_DELETE_REMOTE_RE.search(segmento) else "locale"
    return ""

# Overwrite di un file DB via redirezione (> master.db). Non >> (append).
DB_FILE_OVERWRITE_RE = re.compile(
    # 8/9/2026: `.sql` tolto. Un `.sql` è uno script (`cat > /tmp/query.sql <<SQL`), non un
    # database: sovrascriverlo non perde dati. `.db`, `.sqlite`, `.sql.gz` (backup compresso)
    # e `.dump` restano.
    r"(?<!>)>\s*[^>\s|&;]*\.(?:db|sqlite3?|sql\.gz|dump)\b", re.IGNORECASE
)


def _ask(reason: str) -> int:
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "ask",
            "permissionDecisionReason": reason,
        }
    }))
    return 0


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

    # SQL distruttivo solo se c'è un client DB (riduce falsi positivi)
    if DB_CLIENT_RE.search(cmd):
        for pattern, why in SQL_DESTRUCTIVE:
            if re.search(pattern, cmd, re.IGNORECASE):
                return _ask(
                    f"Operazione SQL distruttiva ({why}). Irreversibile sui dati: "
                    "conferma solo se hai un dump/backup verificato e stai agendo "
                    "sul database giusto."
                )
        if _delete_without_where(cmd):
            return _ask(
                "DELETE FROM senza clausola WHERE: cancella TUTTE le righe. "
                "Conferma solo se è voluto (e c'è un backup)."
            )

    if DOCKER_DOWN_VOL_RE.search(cmd):
        return _ask(
            "`docker compose down -v` rimuove i VOLUMI = i dati persistenti dei "
            "container. Prima di dismettere uno stack, verifica di avere un "
            "dump/export. Conferma solo se i dati sono già salvati."
        )

    dove = _rsync_delete_reale(cmd)
    if dove == "remota":
        return _ask(
            "rsync --delete verso una destinazione REMOTA: se la direzione è "
            "sbagliata (local->master) può cancellare dati sul server. "
            "Verifica sorgente/destinazione e fai un pull/backup prima."
        )
    if dove == "locale":
        return _ask(
            "rsync --delete verso una cartella di questo computer: cancella lì ogni file che la "
            "sorgente non ha, senza cestino. Se la direzione è sbagliata perdi il lavoro. Prova prima "
            "con -n (dry-run) e controlla sorgente e destinazione."
        )

    if DB_FILE_OVERWRITE_RE.search(cmd):
        return _ask(
            "Sovrascrittura di un file di database via redirezione (>). "
            "Se è un master, i dati precedenti vanno persi. Conferma solo se "
            "è voluto; usa >> per appendere o fai una copia prima."
        )

    return 0


if __name__ == "__main__":
    # Claude Code scrive e legge in UTF-8. Su Windows la pipe è in cp1252 (16/10/2026).
    for _flusso in (sys.stdout, sys.stderr):
        try:
            _flusso.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass
    sys.exit(main())
