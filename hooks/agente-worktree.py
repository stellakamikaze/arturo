#!/usr/bin/env python3
"""Un agente ripreso fuori dalla sua copia separata si ferma e lo dice (segnalazione n. 51, 4/11/2026).

Un agente lanciato con `isolation: "worktree"` lavora in `.claude/worktrees/agent-<id>`. Se finisce o si
ferma (quota, rete) senza modifiche, Claude Code toglie quella copia. Ripreso con SendMessage, riparte
nella cartella della sessione madre, senza avviso: più agenti scrivono sullo stesso ramo. Provato su
Claude Code 2.1.318 con `claude -p`: alla ripresa SubagentStart riscatta, con lo stesso agent_id e il
cwd della madre; le chiamate dei tool dell'agente portano agent_id e quel cwd.

SubagentStart: un cwd dentro `.claude/worktrees/agent-*` si annota in
<config>/cache/agenti-worktree/<agent_id>.json. Se lo stesso agente riparte con un altro cwd, l'annotazione
prende il segno `fuori` e l'agente riceve l'avviso nel contesto.
PreToolUse (Edit, MultiEdit, Write, NotebookEdit, Bash): un agente col segno `fuori` che lavora ancora
fuori dalla sua copia riceve un deny. Read, Grep e Glob restano liberi: l'agente guarda e riporta, la
sessione madre decide. Per lasciarlo lavorare lì, la madre cancella il file dell'annotazione.

Un agente senza copia separata, o la sessione principale, non hanno annotazione: l'hook tace.
"""
import json
import os
import re
import sys
import time
from pathlib import Path

COPIA_AGENTE = re.compile(r"[/\\]\.claude[/\\]worktrees[/\\]agent-[^/\\]+$")
SCRITTURA = {"Edit", "MultiEdit", "Write", "NotebookEdit", "Bash"}
SCADENZA = 7 * 86400  # le annotazioni più vecchie di una settimana si tolgono


def cartella() -> Path:
    radice = os.environ.get("CLAUDE_CONFIG_DIR") or str(Path.home() / ".claude")
    return Path(radice) / "cache" / "agenti-worktree"


def norma(percorso: str) -> str:
    return os.path.normcase(os.path.normpath(percorso)) if percorso else ""


def dentro(cwd: str, copia: str) -> bool:
    c, w = norma(cwd), norma(copia)
    return bool(w) and (c == w or c.startswith(w + os.sep))


def nome_sicuro(agente: str) -> bool:
    return bool(re.fullmatch(r"[A-Za-z0-9_-]{1,80}", agente))


def leggi(f: Path) -> dict:
    try:
        return json.loads(f.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def scrivi(f: Path, dati: dict) -> None:
    f.parent.mkdir(parents=True, exist_ok=True)
    tmp = f.with_suffix(".tmp")
    tmp.write_text(json.dumps(dati, ensure_ascii=False), encoding="utf-8")
    os.replace(tmp, f)


def pulisci(d: Path) -> None:
    limite = time.time() - SCADENZA
    try:
        for f in d.glob("*.json"):
            if f.stat().st_mtime < limite:
                f.unlink()
    except OSError:
        pass


def avviso(copia: str, cwd: str, f: Path) -> str:
    sparita = "non esiste più" if not os.path.isdir(copia) else "esiste ancora, ma non sei lì"
    return (
        f"ATTENZIONE: sei un agente ripreso fuori dalla tua copia separata. La tua copia {copia} {sparita}: "
        f"ora lavori in {cwd}, la cartella della sessione che ti ha lanciato o di un altro agente. "
        "Qui non modificare file, non lanciare comandi e non fare commit: mescoleresti il tuo lavoro col loro. "
        "Puoi leggere con Read, Grep e Glob. Fermati e scrivi nel report, come prima riga, che la tua copia "
        "separata non c'è più e cosa ti resta da fare. La sessione madre decide: rilanciare il lavoro in un "
        f"agente nuovo con isolation \"worktree\", oppure lasciarti lavorare qui cancellando {f}."
    )


def avvio(dati: dict, agente: str) -> int:
    cwd = str(dati.get("cwd") or "")
    d = cartella()
    f = d / f"{agente}.json"
    nota = leggi(f)
    copia = str(nota.get("copia") or "")
    if copia and dentro(cwd, copia):
        nota.pop("fuori", None)  # ripreso nella sua copia: il segno di prima non vale più
        scrivi(f, nota)
        return 0
    if not copia:
        if COPIA_AGENTE.search(cwd.rstrip("/\\")):
            pulisci(d)
            scrivi(f, {"copia": cwd, "quando": int(time.time())})
        return 0
    nota["fuori"] = cwd
    scrivi(f, nota)
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "SubagentStart",
        "additionalContext": avviso(copia, cwd, f),
    }}, ensure_ascii=False))
    return 0


def strumento(dati: dict, agente: str) -> int:
    if str(dati.get("tool_name") or "") not in SCRITTURA:
        return 0
    f = cartella() / f"{agente}.json"
    if not f.is_file():
        return 0
    nota = leggi(f)
    copia = str(nota.get("copia") or "")
    cwd = str(dati.get("cwd") or "")
    if not nota.get("fuori") or not copia or dentro(cwd, copia):
        return 0
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "deny",
        "permissionDecisionReason": "Agente fuori dalla sua copia separata (segnalazione n. 51). " + avviso(copia, cwd, f),
    }}, ensure_ascii=False))
    return 0


def main() -> int:
    try:
        dati = json.loads(sys.stdin.buffer.read().decode("utf-8"))
    except (ValueError, UnicodeDecodeError):
        return 0
    agente = str(dati.get("agent_id") or "")
    if not agente or not nome_sicuro(agente):
        return 0
    evento = dati.get("hook_event_name")
    if evento == "SubagentStart":
        return avvio(dati, agente)
    if evento == "PreToolUse":
        return strumento(dati, agente)
    return 0


if __name__ == "__main__":
    # Claude Code scrive e legge in UTF-8. Su Windows la pipe è in cp1252 (16/10/2026).
    for _flusso in (sys.stdout, sys.stderr):
        try:
            _flusso.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass
    try:
        sys.exit(main())
    except Exception:
        sys.exit(0)
