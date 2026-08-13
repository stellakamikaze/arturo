#!/usr/bin/env python3
"""PreToolUse(Bash) hook: gate sulle operazioni DATI irreversibili.

Copre i buchi NON gestiti da block-dangerous.py (che gia' fa rm/config/segreti/
docker-volume-rm) ne' da comms/exfil. Bersaglio: gli errori classici sui dati —
DB sovrascritto, sync nella direzione sbagliata, dismissione stack senza dump
verificato.

Tutto CHIEDE CONFERMA (permissionDecision:"ask", exit 0) — non blocca duro:
queste operazioni hanno usi legittimi, ma sono punti di non-ritorno sui DATI e
meritano uno speed-bump prima dell'esecuzione (stessa filosofia di block-dangerous
per rm su tree protetti).

Casi coperti:
- SQL distruttivo: DROP TABLE/DATABASE/SCHEMA, TRUNCATE, DELETE FROM senza WHERE
  (solo se c'e' un client DB nel comando: mysql/psql/sqlite3/mariadb/mongo...)
- docker compose down -v / --volumes  (cancella i volumi = i dati dei container)
- rsync --delete verso una destinazione REMOTA (host:path) = puo' cancellare
  dati sul server se la direzione e' sbagliata
- redirezione/overwrite di un file DB (> *.db / *.sqlite / *.sql.gz)

Fail-open su parsing. Zero dipendenze.
"""
import json
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
DELETE_NO_WHERE_RE = re.compile(
    r"\bDELETE\s+FROM\s+[`\"']?\w[\w.`\"']*(?![^;]*\bWHERE\b)", re.IGNORECASE
)

DOCKER_DOWN_VOL_RE = re.compile(
    r"\bdocker\s+compose\s+down\b[^|&;]*(?:\s-v\b|\s--volumes\b)", re.IGNORECASE
)

# rsync --delete verso destinazione remota (host:path). Il ':' con un host prima
# indica una dest remota; --delete puo' cancellare file sul lato remoto.
RSYNC_DELETE_REMOTE_RE = re.compile(
    r"\brsync\b[^|&;]*--delete\b[^|&;]*\s[\w.-]+@?[\w.-]+:", re.IGNORECASE
)

# Overwrite di un file DB via redirezione (> master.db). Non >> (append).
DB_FILE_OVERWRITE_RE = re.compile(
    r"(?<!>)>\s*[^>\s|&;]*\.(?:db|sqlite3?|sql|sql\.gz|dump)\b", re.IGNORECASE
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
        data = json.load(sys.stdin)
        if hasattr(signal, "SIGALRM"):
            signal.alarm(0)
    except Exception:
        return 0

    if data.get("tool_name") != "Bash":
        return 0
    cmd = (data.get("tool_input") or {}).get("command", "")
    if not isinstance(cmd, str) or not cmd:
        return 0

    # SQL distruttivo solo se c'e' un client DB (riduce falsi positivi)
    if DB_CLIENT_RE.search(cmd):
        for pattern, why in SQL_DESTRUCTIVE:
            if re.search(pattern, cmd, re.IGNORECASE):
                return _ask(
                    f"Operazione SQL distruttiva ({why}). Irreversibile sui dati: "
                    "conferma solo se hai un dump/backup verificato e stai agendo "
                    "sul database giusto."
                )
        if DELETE_NO_WHERE_RE.search(cmd):
            return _ask(
                "DELETE FROM senza clausola WHERE: cancella TUTTE le righe. "
                "Conferma solo se e' voluto (e c'e' un backup)."
            )

    if DOCKER_DOWN_VOL_RE.search(cmd):
        return _ask(
            "`docker compose down -v` rimuove i VOLUMI = i dati persistenti dei "
            "container. Prima di dismettere uno stack, verifica di avere un "
            "dump/export. Conferma solo se i dati sono gia' salvati."
        )

    if RSYNC_DELETE_REMOTE_RE.search(cmd):
        return _ask(
            "rsync --delete verso una destinazione REMOTA: se la direzione e' "
            "sbagliata (local->master) puo' cancellare dati sul server. "
            "Verifica sorgente/destinazione e fai un pull/backup prima."
        )

    if DB_FILE_OVERWRITE_RE.search(cmd):
        return _ask(
            "Sovrascrittura di un file di database via redirezione (>). "
            "Se e' un master, i dati precedenti vanno persi. Conferma solo se "
            "e' voluto; usa >> per appendere o fai una copia prima."
        )

    return 0


if __name__ == "__main__":
    sys.exit(main())
