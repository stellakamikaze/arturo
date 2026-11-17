#!/usr/bin/env python3
"""prova: riconosce le sessioni di prova, cioè le sessioni nate da una sonda, da un banco o da una prova dal vivo.

Il marcatore è il nome della sessione: comincia con `prova-` (#5877, prima /revisione del 17/11/2026: sul
MacBook circa 30 sessioni di prova su 143 in 7 giorni, e Volta mandava /fine a una prova).

  claude --bg --name prova-5877 "Rispondi solo: ok"          nasce marcata
  python3 ~/.claude/bin/prova.py                             questa sessione è di prova?
  python3 ~/.claude/bin/prova.py --elimina                   se lo è, claude rm fra 30 secondi

Chi lo legge:
- /fine (FASE 0): una sessione di prova non scrive handoff, todo né memoria, e si elimina da sola;
- Volta (passoCongedo di sessioni.js, stesso prefisso): alla chiusura niente /fine, solo stop e claude rm;
- bin/revisione.py estrai: la salta, e conta quante ne ha saltate.

Il nome viene da `claude agents --json` (il campo name) o, senza, dall'ultimo custom-title o agent-name del
transcript: Claude Code scrive lì il valore di --name. Uscita: 0 di prova, 1 non di prova, 2 id o transcript
assenti. Solo libreria standard.
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

PREFISSO = "prova-"
MARCATO = re.compile(r"^\s*prova-", re.I)
try:  # secondi: il turno di /fine finisce prima che claude rm fermi la sessione; il banco lo accorcia
    ATTESA_RM = max(0, min(600, int(os.environ.get("ARTURO_PROVA_ATTESA") or 30)))
except ValueError:
    ATTESA_RM = 30


def e_prova(nome) -> bool:
    return isinstance(nome, str) and bool(MARCATO.match(nome))


def nome_da_record(r) -> str:
    """Il nome scritto in un record del transcript, o "" se il record non ne porta uno."""
    if not isinstance(r, dict):
        return ""
    if r.get("type") == "custom-title":
        return str(r.get("customTitle") or "")
    if r.get("type") == "agent-name":
        return str(r.get("agentName") or "")
    return ""


def nome_da_transcript(file) -> str:
    """L'ultimo nome della sessione nel transcript: /rename lo cambia, e conta quello di adesso."""
    nome = ""
    try:
        with open(file, encoding="utf-8", errors="replace") as righe:
            for line in righe:
                if '"custom-title"' not in line and '"agent-name"' not in line:
                    continue
                try:
                    n = nome_da_record(json.loads(line))
                except ValueError:
                    continue
                if n:
                    nome = n
    except OSError:
        return ""
    return nome


def programma_claude() -> str:
    dato = os.environ.get("ARTURO_CLAUDE") or ""
    scelto = (shutil.which(dato) if dato else None) or shutil.which("claude")
    if scelto:
        return scelto
    for cartella in (Path.home() / ".local" / "bin", Path.home() / ".claude" / "local"):
        for nome in (("claude.exe", "claude.cmd") if os.name == "nt" else ("claude",)):
            if (cartella / nome).is_file():
                return str(cartella / nome)
    return ""


def voce_agents(sid: str) -> dict:
    """La riga di `claude agents --json` di questa sessione, o {} (CLI assente, lenta, sessione non elencata)."""
    claude = programma_claude()
    if not claude:
        return {}
    try:
        p = subprocess.run([claude, "agents", "--json"], capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=20)
        dati = json.loads(p.stdout or "[]")
    except (OSError, subprocess.TimeoutExpired, ValueError):
        return {}
    elenco = dati if isinstance(dati, list) else (dati.get("sessions") or []) if isinstance(dati, dict) else []
    for s in elenco:
        if isinstance(s, dict) and s.get("sessionId") == sid:
            return s
    return {}


def trova_transcript(sid: str, projects: Path) -> str:
    trovati = glob.glob(os.path.join(str(projects), "*", f"{glob.escape(sid)}.jsonl"))
    return trovati[0] if trovati else ""


def radice_projects() -> Path:
    base = os.environ.get("CLAUDE_CONFIG_DIR")
    return (Path(base) if base else Path.home() / ".claude") / "projects"


def elimina_dopo(claude: str, lavoro: str) -> bool:
    """claude rm del lavoro in background fra ATTESA_RM secondi, in un processo staccato da questa sessione."""
    if not re.fullmatch(r"[0-9A-Za-z-]{4,64}", lavoro or ""):
        return False
    try:
        if os.name == "nt":
            comando = ["powershell", "-NoProfile", "-Command",
                       f"Start-Sleep -Seconds {ATTESA_RM}; & '{claude}' rm {lavoro}"]
            subprocess.Popen(comando, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                             creationflags=0x00000008 | 0x00000200)  # DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP
        else:
            subprocess.Popen(["sh", "-c", f'sleep {ATTESA_RM}; "$0" rm "$1"', claude, lavoro],
                             stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                             start_new_session=True)
    except OSError:
        return False
    return True


def main(argv: list) -> int:
    ap = argparse.ArgumentParser(prog="prova.py", description="Questa sessione è una sessione di prova?")
    ap.add_argument("--session", default=os.environ.get("CLAUDE_CODE_SESSION_ID", ""))
    ap.add_argument("--projects", help="default: ~/.claude/projects")
    ap.add_argument("--elimina", action="store_true", help="se è di prova e in background: claude rm fra poco")
    a = ap.parse_args(argv)
    sid = (a.session or "").strip()
    if not sid:
        print("prova: manca l'id di sessione (CLAUDE_CODE_SESSION_ID o --session)")
        return 2
    voce = voce_agents(sid)
    nome = str(voce.get("name") or "")
    if not nome:
        file = trova_transcript(sid, Path(a.projects) if a.projects else radice_projects())
        if not file and not voce:
            print(f"prova: transcript non trovato per {sid[:8]}")
            return 2
        nome = nome_da_transcript(file) if file else ""
    if not e_prova(nome):
        print(f"prova: no · nome {nome or '(nessuno)'}")
        return 1
    riga = f"prova: sì · nome {nome}"
    if a.elimina:
        lavoro = str(voce.get("id") or "") if voce.get("kind") == "background" else ""
        if not lavoro:
            riga += " · interattiva: niente da eliminare, chiudila"
        elif elimina_dopo(programma_claude(), lavoro):
            riga += f" · claude rm {lavoro} fra {ATTESA_RM} secondi"
        else:
            riga += f" · claude rm {lavoro} non è partito: lancialo a mano"
    print(riga)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
