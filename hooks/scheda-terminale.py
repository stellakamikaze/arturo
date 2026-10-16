#!/usr/bin/env python3
"""Titolo e colore della scheda del terminale: il progetto della sessione e il suo stato.

Gira come hook asincrono su SessionStart, UserPromptSubmit, PostToolUse, Notification, Stop,
StopFailure e SessionEnd. Legge l'evento da stdin e scrive sul terminale:
  - il titolo, con OSC 0: il solo progetto dove il colore dice lo stato, altrimenti
    «<progetto> · <stato>». Regge solo se Claude Code non lo riscrive: in settings.json c'è
    CLAUDE_CODE_DISABLE_TERMINAL_TITLE=1;
  - il colore della scheda, dove il terminale lo sa fare: verde attende, giallo al lavoro,
    rosso se il turno si è fermato per un errore (StopFailure). Windows Terminal con DECAC,
    iTerm2 con OSC 6. Gli altri terminali ricevono solo il titolo.
Il progetto viene da un «/inizio <nome>» della sessione, poi dalla radice git della cartella,
poi dal nome della cartella. Stato e progetto stanno in ~/.claude/cache/scheda/<sessione>.json.
Su Windows un hook non vede la console della scheda: si attacca a quella del processo claude.exe.
Con ARTURO_SCHEDA_USCITA=<file> le sequenze vanno in quel file (banchi). Ogni errore: exit 0.
Solo libreria standard, Python 3.8+.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

EVENTI = {"SessionStart": "attende", "UserPromptSubmit": "lavoro", "PostToolUse": "lavoro",
          "Notification": "attende", "Stop": "attende", "StopFailure": "problema", "SessionEnd": "fine"}
ETICHETTE = {"attende": "attende", "lavoro": "al lavoro", "problema": "problema"}
DECAC = {"attende": 2, "lavoro": 3, "problema": 1}  # indici della tavolozza: verde, giallo, rosso
RGB = {"attende": (40, 167, 69), "lavoro": (230, 180, 0), "problema": (200, 40, 40)}
INIZIO = re.compile(r"^\s*/inizio\b(.*)$", re.S)


def cache_dir() -> Path:
    radice = os.environ.get("CLAUDE_CONFIG_DIR") or str(Path.home() / ".claude")
    return Path(radice) / "cache" / "scheda"


def leggi(f: Path) -> dict:
    try:
        return json.loads(f.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def progetto_da_cartella(cwd: str) -> str:
    """La radice git (il repo principale anche da un worktree), altrimenti il nome della cartella."""
    for argomenti in (["rev-parse", "--path-format=absolute", "--git-common-dir"], ["rev-parse", "--show-toplevel"]):
        try:
            r = subprocess.run(["git", "-C", cwd, *argomenti], capture_output=True, text=True,
                               encoding="utf-8", errors="replace", timeout=3)
        except (OSError, subprocess.SubprocessError):
            break
        uscita = r.stdout.strip()
        if r.returncode == 0 and uscita:
            p = Path(uscita)
            return (p.parent if p.name == ".git" else p).name
    return Path(cwd).name or "claude"


def progetto_da_prompt(prompt: str) -> str:
    m = INIZIO.match(prompt or "")
    if not m:
        return ""
    for parola in m.group(1).split():
        if parola == "--":
            break
        if not parola.startswith("-"):
            return re.sub(r"[^\w.-]", "", parola)[:40]
    return ""


def sequenze(stato: str, progetto: str) -> str:
    pulito = re.sub(r"[\x00-\x1f\x7f]", "", progetto)[:40]
    if stato == "fine":
        testo = "\x1b]0;\x07"
        if os.environ.get("TERM_PROGRAM") == "iTerm.app":
            testo += "\x1b]6;1;bg;*;default\x07"
        return testo
    # Dove il colore dice lo stato, il titolo è solo il progetto: nella scheda stretta si legge intero.
    if os.environ.get("WT_SESSION"):
        return f"\x1b]0;{pulito}\x07\x1b[2;15;{DECAC[stato]},|"
    if os.environ.get("TERM_PROGRAM") == "iTerm.app":
        r, g, b = RGB[stato]
        return (f"\x1b]0;{pulito}\x07\x1b]6;1;bg;red;brightness;{r}\x07"
                f"\x1b]6;1;bg;green;brightness;{g}\x07\x1b]6;1;bg;blue;brightness;{b}\x07")
    return f"\x1b]0;{pulito} · {ETICHETTE[stato]}\x07"


def scrivi_windows(testo: str) -> None:
    """Scrive nella console di claude.exe: quella dell'hook è nascosta e non arriva alla scheda."""
    import ctypes
    import ctypes.wintypes as w

    k = ctypes.WinDLL("kernel32", use_last_error=True)

    class Voce(ctypes.Structure):
        _fields_ = [("dwSize", w.DWORD), ("cntUsage", w.DWORD), ("th32ProcessID", w.DWORD),
                    ("th32DefaultHeapID", ctypes.c_void_p), ("th32ModuleID", w.DWORD), ("cntThreads", w.DWORD),
                    ("th32ParentProcessID", w.DWORD), ("pcPriClassBase", ctypes.c_long), ("dwFlags", w.DWORD),
                    ("szExeFile", ctypes.c_char * 260)]

    k.CreateToolhelp32Snapshot.restype = w.HANDLE
    foto = k.CreateToolhelp32Snapshot(2, 0)
    voce = Voce()
    voce.dwSize = ctypes.sizeof(Voce)
    padri = {}
    ok = k.Process32First(foto, ctypes.byref(voce))
    while ok:
        padri[voce.th32ProcessID] = (voce.th32ParentProcessID, voce.szExeFile.decode(errors="replace").lower())
        ok = k.Process32Next(foto, ctypes.byref(voce))
    k.CloseHandle(foto)
    pid, passi = os.getpid(), 0
    while pid in padri and passi < 40:
        padre, nome = padri[pid]
        if nome == "claude.exe":
            break
        pid, passi = padre, passi + 1
    else:
        return
    if pid not in padri or padri[pid][1] != "claude.exe":
        return
    k.FreeConsole()
    if not k.AttachConsole(pid):
        return
    try:
        k.CreateFileW.restype = w.HANDLE
        h = k.CreateFileW("CONOUT$", 0x40000000 | 0x80000000, 3, None, 3, 0, None)
        if h in (None, w.HANDLE(-1).value):
            return
        scritti = w.DWORD()
        k.WriteConsoleW(h, testo, len(testo), ctypes.byref(scritti), None)
        k.CloseHandle(h)
    finally:
        k.FreeConsole()


def scrivi(testo: str) -> None:
    uscita = os.environ.get("ARTURO_SCHEDA_USCITA")
    if uscita:
        with open(uscita, "a", encoding="utf-8") as f:
            f.write(testo)
        return
    if os.name == "nt":
        scrivi_windows(testo)
        return
    with open("/dev/tty", "w", encoding="utf-8") as tty:
        tty.write(testo)


def main() -> int:
    adesso = time.time()
    dati = json.loads(sys.stdin.buffer.read().decode("utf-8") or "{}")
    stato = EVENTI.get(str(dati.get("hook_event_name") or ""))
    if not stato:
        return 0
    sessione = re.sub(r"[^\w-]", "", str(dati.get("session_id") or ""))[:64] or "nessuna"
    f = cache_dir() / f"{sessione}.json"
    salvato = leggi(f)
    # Gli hook asincroni possono arrivare fuori ordine: vale l'evento partito per ultimo.
    if adesso < float(salvato.get("quando") or 0):
        return 0
    progetto = progetto_da_prompt(str(dati.get("prompt") or "")) if stato == "lavoro" else ""
    progetto = progetto or salvato.get("progetto") or progetto_da_cartella(str(dati.get("cwd") or os.getcwd()))
    if stato == "fine":
        try:
            f.unlink()
        except OSError:
            pass
    elif salvato.get("stato") == stato and salvato.get("progetto") == progetto:
        return 0  # niente cambia: è il caso comune di PostToolUse
    else:
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(json.dumps({"stato": stato, "progetto": progetto, "quando": adesso}), encoding="utf-8")
    scrivi(sequenze(stato, progetto))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(0)
