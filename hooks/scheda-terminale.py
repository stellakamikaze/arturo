#!/usr/bin/env python3
"""Titolo e colore della scheda del terminale: il progetto della sessione e il suo stato.

Gira come hook asincrono su SessionStart, UserPromptSubmit, PostToolUse, Notification, Stop,
StopFailure e SessionEnd. Legge l'evento da stdin e scrive sul terminale:
  - il titolo, con OSC 0: il solo progetto, oppure "SBLOCCA · <progetto>" quando la sessione aspetta la persona:
    permesso, domanda, errore, o idle_prompt. Richiesta del 28/10/2026: "SOLO il titolo del progetto".
    La fine del turno da sola non basta (mostrava SBLOCCA a vuoto): Claude Code manda idle_prompt dopo
    60 secondi fermi, e solo se nessun job in background gira e nessuna finestra di dialogo è aperta. Regge solo se Claude Code non lo riscrive: in settings.json c'è
    CLAUDE_CODE_DISABLE_TERMINAL_TITLE=1. Su Terminal di Apple il profilo deve avere spenti
    "Nome processo attivo" nella scheda (ShowActiveProcessInTabTitle), altrimenti accoda "— caffeinate ◂ claude";
  - il colore della scheda, dove il terminale lo sa fare: verde attende, giallo al lavoro,
    rosso se il turno si è fermato per un errore (StopFailure). Windows Terminal con DECAC,
    iTerm2 con OSC 6. Gli altri terminali ricevono solo il titolo.
Il progetto viene dallo slug che il risolutore di /inizio stampa in testa ("# CONTESTO <slug>" di
contesto-progetto.py, "PROGETTO <slug>" di arturo contesto), e prima della risoluzione dal testo intero
dopo "/inizio" (una fonte debole: un file scritto la sostituisce, lo slug no). Senza /inizio vale l'ultima cartella di progetto toccata da Edit o Write
(<PROJECTS_BASE>/<progetto>, di default ~/Documents/ClaudeCode; hook, comandi, skill e file di testa della
config = "claude-config", non piani, memoria e cache), poi la radice git o il nome della cartella.
Limite noto: dopo un permesso concesso Claude Code non manda eventi finché lo strumento non finisce, quindi
"SBLOCCA" resta per tutta la durata del comando approvato. Stato e progetto stanno in ~/.claude/cache/scheda/<sessione>.json:
SessionEnd toglie il suo file, SessionStart quelli fermi da una settimana (sessioni chiuse male).
Su Windows un hook non vede la console della scheda: si attacca a quella del processo claude.exe.
Su macOS e Linux l'hook non ha un terminale di controllo (/dev/tty risponde ENXIO): scrive sul tty del
processo claude, trovato risalendo i padri con ps (18/10/2026: sul Mac le schede non cambiavano mai).
Con ARTURO_SCHEDA_USCITA=<file> le sequenze vanno in quel file (banchi), con ARTURO_SCHEDA_DEV=<cartella>
il tty di claude si cerca lì invece che in /dev (banchi). Ogni errore: exit 0.
Solo libreria standard, Python 3.8+.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import time
import unicodedata
from pathlib import Path

EVENTI = {"SessionStart": "nuova", "UserPromptSubmit": "lavoro", "PostToolUse": "lavoro",
          "Notification": "attende", "Stop": "fermo", "StopFailure": "problema", "SessionEnd": "fine"}
# Le notifiche che vogliono davvero la persona (il matcher in settings.json filtra già: qui è la seconda rete).
CHIEDONO = {"permission_prompt", "idle_prompt", "elicitation_dialog", "elicitation_url_dialog",
            "agent_needs_input", "worker_permission_prompt", "workflow_permission_prompt"}
# Il titolo è il progetto; quando tocca alla persona "SBLOCCA" gli va davanti, senza nasconderlo (29/10/2026).
# Una sessione appena aperta, o col turno finito, non ha niente da sbloccare: mostra il progetto.
TITOLO = {"nuova": "{p}", "fermo": "{p}", "attende": "SBLOCCA · {p}", "lavoro": "{p}", "problema": "SBLOCCA · {p}"}
# Gli eventi che passano la mano alla persona: solo questi suonano la campanella.
FERMANO = {"Notification", "StopFailure"}
DECAC = {"nuova": 2, "fermo": 2, "attende": 2, "lavoro": 3, "problema": 1}  # tavolozza: verde, giallo, rosso
RGB = {"nuova": (40, 167, 69), "fermo": (40, 167, 69), "attende": (40, 167, 69), "lavoro": (230, 180, 0),
       "problema": (200, 40, 40)}
INIZIO = re.compile(r"^\s*/inizio\b(.*)$", re.S)
# Il comando deve eseguire il risolutore (un grep che lo nomina non conta), e la sua prima riga
# d'intestazione c'è solo se ha trovato il progetto.
RISOLUTORE = re.compile(r"(?:^|[\s;&|(])(?:\S*contesto-progetto\.py|\S*arturo\s+contesto)(?=\s|$|[;&|)])", re.M)
CONTESTO = re.compile(r"^(?:# CONTESTO|PROGETTO) (\w[\w.-]*)\s*$")
SCRITTURE = {"Edit", "Write", "MultiEdit", "NotebookEdit"}
# Le cartelle della config che sono lavoro sulla config. Piani, memoria automatica, cache e dati di
# sessione li scrive Claude Code mentre lavora su altro: non rinominano la scheda.
CONFIG = {"hooks", "scripts", "skills", "commands", "agents", "mods", "output-styles", "bin", "tests", "shared",
          "personale", "linux"}
VECCHIO = 7 * 24 * 3600  # secondi: una sessione ferma da una settimana non riparte


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
    """Il testo dopo "/inizio" fino a "--": "/inizio due mondi spoleto" dà "due mondi spoleto"."""
    m = INIZIO.match(prompt or "")
    if not m:
        return ""
    parole = []
    for parola in m.group(1).split():
        if parola == "--":
            break
        if not parola.startswith("-"):
            parole.append(re.sub(r"[^\w.-]", "", parola))
    return " ".join(p for p in parole if p)[:40]


def progetto_da_strumento(dati: dict) -> tuple:
    """(progetto, fonte) da un PostToolUse: lo slug risolto da /inizio, o la cartella di un file scritto."""
    nome = str(dati.get("tool_name") or "")
    entrata = dati.get("tool_input") if isinstance(dati.get("tool_input"), dict) else {}
    if nome == "Bash":
        risposta = dati.get("tool_response")
        uscita = risposta.get("stdout") if isinstance(risposta, dict) else risposta
        prima = (str(uscita or "").strip().splitlines() or [""])[0]
        m = CONTESTO.match(prima) if RISOLUTORE.search(str(entrata.get("command") or "")) else None
        return (m.group(1)[:40], "inizio") if m else ("", "")
    if nome not in SCRITTURE:
        return "", ""
    percorso = Path(str(entrata.get("file_path") or entrata.get("notebook_path") or "")).expanduser()
    config = dentro(percorso, Path(os.path.expanduser(os.environ.get("CLAUDE_CONFIG_DIR") or "~/.claude")))
    if config is not None:
        return ("claude-config", "file") if len(config) == 1 or config[0] in CONFIG else ("", "")
    # La cartella dei progetti come la legge contesto.base_progetti() di Arturo.
    parti = dentro(percorso, Path(os.path.expanduser(os.environ.get("PROJECTS_BASE") or "~/Documents/ClaudeCode")))
    return (parti[0][:40], "file") if parti and len(parti) > 1 else ("", "")


def dentro(percorso: Path, radice: Path):
    """Le parti di percorso sotto radice, o None se sta fuori (Path.is_relative_to è solo dal 3.9)."""
    try:
        return percorso.relative_to(radice).parts
    except ValueError:
        return None


def sequenze(stato: str, progetto: str, campanella: bool = False) -> str:
    # Fuori ogni carattere di controllo (C0, DEL, C1: U+009C chiude un OSC) e di formato (U+202E rovescia il testo).
    pulito = "".join(c for c in progetto if unicodedata.category(c) not in ("Cc", "Cf"))[:40]
    if stato == "fine":
        testo = "\x1b]0;\x07"
        if os.environ.get("TERM_PROGRAM") == "iTerm.app":
            testo += "\x1b]6;1;bg;*;default\x07"
        return testo
    testo = f"\x1b]0;{TITOLO[stato].format(p=pulito)}\x07"
    if os.environ.get("WT_SESSION"):
        return testo + f"\x1b[2;15;{DECAC[stato]},|"
    if os.environ.get("TERM_PROGRAM") == "iTerm.app":
        r, g, b = RGB[stato]
        return (testo + f"\x1b]6;1;bg;red;brightness;{r}\x07"
                f"\x1b]6;1;bg;green;brightness;{g}\x07\x1b]6;1;bg;blue;brightness;{b}\x07")
    # Terminal di Apple non colora la scheda, ma segna con una campanella la scheda in secondo
    # piano che riceve un BEL, finché non ci si entra: è il suo "tocca a te" (18/10/2026).
    if campanella and os.environ.get("TERM_PROGRAM") == "Apple_Terminal":
        testo += "\x07"
    return testo


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


def tty_di_claude() -> str:
    """Il tty del processo claude più vicino fra i padri, o "" se non c'è."""
    pid = os.getppid()
    for _ in range(40):
        try:
            r = subprocess.run(["ps", "-o", "ppid=,tty=,comm=", "-p", str(pid)], capture_output=True, text=True,
                               encoding="utf-8", errors="replace", timeout=3)
        except (OSError, subprocess.SubprocessError):
            return ""
        parti = r.stdout.split(None, 2)
        if len(parti) < 3:
            return ""
        padre, tty, nome = parti
        if Path(nome.strip()).name == "claude" and re.fullmatch(r"(ttys?|pts/)\w+", tty):
            return str(Path(os.environ.get("ARTURO_SCHEDA_DEV") or "/dev") / tty)
        if not padre.isdigit() or int(padre) <= 1:
            return ""
        pid = int(padre)
    return ""


def scrivi(testo: str) -> None:
    uscita = os.environ.get("ARTURO_SCHEDA_USCITA")
    if uscita:
        with open(uscita, "a", encoding="utf-8") as f:
            f.write(testo)
        return
    if os.name == "nt":
        scrivi_windows(testo)
        return
    try:
        with open("/dev/tty", "w", encoding="utf-8") as tty:
            tty.write(testo)
        return
    except OSError:
        pass  # niente terminale di controllo: il caso normale di un hook
    percorso = tty_di_claude()
    if percorso:
        with open(percorso, "w", encoding="utf-8") as tty:
            tty.write(testo)


def pulisci(adesso: float) -> None:
    """Toglie lo stato delle sessioni chiuse male (niente SessionEnd): fermo da più di VECCHIO."""
    for vecchio in [*cache_dir().glob("*.json"), *cache_dir().glob("*.tmp")]:
        try:
            if adesso - vecchio.stat().st_mtime > VECCHIO:
                vecchio.unlink()
        except OSError:
            pass


def main() -> int:
    adesso = time.time()
    dati = json.loads(sys.stdin.buffer.read().decode("utf-8") or "{}")
    evento = str(dati.get("hook_event_name") or "")
    stato = EVENTI.get(evento)
    if not stato or (evento == "Notification" and dati.get("notification_type") not in CHIEDONO):
        return 0
    sessione = re.sub(r"[^\w-]", "", str(dati.get("session_id") or ""))[:64] or "nessuna"
    f = cache_dir() / f"{sessione}.json"
    if dati.get("hook_event_name") == "SessionStart":
        pulisci(adesso)
    salvato = leggi(f)
    # Gli hook asincroni possono arrivare fuori ordine: vale l'evento partito per ultimo.
    if adesso < float(salvato.get("quando") or 0):
        return 0
    # Lo slug risolto da /inizio ("inizio") non lo scavalca un file toccato; il testo scritto dopo /inizio
    # ("prompt") sì, perché può essere un nome che il risolutore non ha trovato.
    progetto, fonte = progetto_da_prompt(str(dati.get("prompt") or "")), "prompt"
    if not progetto and evento == "PostToolUse":
        progetto, fonte = progetto_da_strumento(dati)
        if fonte == "file" and salvato.get("fonte") == "inizio":
            progetto = ""
    if not progetto:
        progetto, fonte = salvato.get("progetto") or "", salvato.get("fonte") or ""
    if not progetto:
        progetto, fonte = progetto_da_cartella(str(dati.get("cwd") or os.getcwd())), "cartella"
    if stato == "fine":
        try:
            f.unlink()
        except OSError:
            pass
    elif salvato.get("stato") == stato and salvato.get("progetto") == progetto and salvato.get("fonte") == fonte:
        return 0  # niente cambia: è il caso comune di PostToolUse
    else:
        # Un evento partito dopo può aver scritto mentre questo leggeva: si ricontrolla, poi si scrive in
        # un file a parte e si sostituisce, così nessuno legge uno stato scritto a metà.
        if adesso < float(leggi(f).get("quando") or 0):
            return 0
        f.parent.mkdir(parents=True, exist_ok=True)
        provvisorio = f.with_name(f"{f.stem}.{os.getpid()}.tmp")
        provvisorio.write_text(json.dumps({"stato": stato, "progetto": progetto, "fonte": fonte, "quando": adesso}),
                               encoding="utf-8")
        os.replace(str(provvisorio), str(f))
    scrivi(sequenze(stato, progetto, campanella=evento in FERMANO))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(0)
