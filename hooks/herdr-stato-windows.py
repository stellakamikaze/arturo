#!/usr/bin/env python3
"""Lo stato di Claude Code verso Herdr su Windows, col protocollo OSC 7501 (25/11/2026, #5639).

Lo chiama herdr-stato.sh quando gira su Windows. Uso: herdr-stato-windows.py <idle|working|blocked|done|error>.

Perché esiste. Su Windows Claude Code lancia gli hook senza terminale di controllo: `/dev/tty` non si apre, il
ps di Git non conosce `-o` e il padre che vede sh è 1 (sonda prova-5639b, 25/11/2026 21:50). La sequenza
invece arriva a Herdr se qualcuno la scrive sulla console giusta: ConPTY la passa al terminale. Questo
aiutante sale fra gli antenati veri (gli ID di Windows, non quelli di MSYS) fino a claude.exe, lascia la sua
console, si aggancia a quella di claude.exe con AttachConsole e scrive su CONOUT$.

Un PID di Windows si riusa: un padre nato dopo il figlio è un altro processo, e lì la salita si ferma. Se
l'ora di nascita di un antenato non si legge, il confronto usa l'ultima ora letta più in basso.

L'ordine (revisione della PR #49, 25/11/2026). PostToolUse lancia `working` in async, e Python su Windows
parte lento: un `working` vecchio può arrivare dopo lo stato di fine turno. Ogni hook porta l'ora di nascita
del processo che Claude Code ha lanciato per lui, cioè il figlio di claude.exe nella salita. Un file per
sessione in %TEMP% tiene l'ora dell'ultimo stato scritto, sotto un lucchetto: uno stato più vecchio si scarta.
Il lucchetto mette in fila anche gli aiutanti che cambiano la modalità della console.

Su un Python di Windows esce sempre 0, anche quando non trova niente. Su un Python di MSYS2 o Cygwin
(`sys.platform` diverso da win32) esce 2: herdr-stato.sh allora prova l'interprete dopo.
"""
from __future__ import annotations

import sys

STATI = ("idle", "working", "blocked", "done", "error")
# Il primo antenato con uno di questi nomi è Claude Code: l'installazione nativa (claude.exe) o quella di npm.
NOMI = ("claude.exe", "node.exe")
PASSI = 12
VT = 0x0004  # ENABLE_VIRTUAL_TERMINAL_PROCESSING: senza, la console stampa ESC come un carattere.
NON_WINDOWS = 2


def sequenza(stato: str) -> bytes:
    return f"\033]7501;state={stato}:app=claude-code\033\\".encode("ascii")


def sali(padri: dict, io: int, nato, passi: int = PASSI):
    """(PID di Claude Code, PID del suo figlio nella salita): il primo antenato di `io` con un nome di NOMI.

    padri: {pid: (pid del padre, nome dell'eseguibile)}. nato(pid): l'ora di nascita, o None se non si legge.
    Senza Claude Code fra gli antenati, o dopo un PID riusato: (None, None).
    """
    pid, quando = io, nato(io)
    for _ in range(passi):
        voce = padri.get(pid)
        if not voce:
            return None, None
        padre = voce[0]
        if padre in (0, pid) or padre not in padri:
            return None, None
        quando_padre = nato(padre)
        if quando is not None and quando_padre is not None and quando_padre > quando:
            return None, None  # PID riusato: il padre vero è già uscito
        if padri[padre][1].lower() in NOMI:
            return padre, pid
        pid = padre
        if quando_padre is not None:
            quando = quando_padre
    return None, None


def scegli(padri: dict, io: int, nato, passi: int = PASSI):
    """Il PID del primo antenato di `io` che si chiama come in NOMI, o None."""
    return sali(padri, io, nato, passi)[0]


def _blocca(f) -> None:
    try:
        import msvcrt
    except ImportError:  # fuori da Windows: solo per il banco
        import fcntl

        fcntl.flock(f.fileno(), fcntl.LOCK_EX)
        return
    f.seek(0)
    msvcrt.locking(f.fileno(), msvcrt.LK_LOCK, 1)


def _sblocca(f) -> None:
    try:
        import msvcrt
    except ImportError:
        import fcntl

        fcntl.flock(f.fileno(), fcntl.LOCK_UN)
        return
    f.seek(0)
    msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, 1)


def in_ordine(percorso, ora: int, scrivi) -> bool:
    """Chiama scrivi() solo se `ora` non è più vecchia dell'ultimo stato scritto in `percorso`.

    Vero se lo stato è partito. Il file tiene l'ora dell'ultimo stato scritto; tutto avviene sotto lucchetto.
    """
    with open(percorso, "a+b") as f:
        _blocca(f)
        try:
            f.seek(0)
            testo = f.read().strip()
            prima = int(testo) if testo.isdigit() else 0
            if ora < prima:
                return False
            if not scrivi():
                return False
            f.seek(0)
            f.truncate()
            f.write(str(ora).encode("ascii"))
            f.flush()
            return True
        finally:
            _sblocca(f)


def _kernel32():
    import ctypes
    from ctypes import wintypes as w

    k = ctypes.WinDLL("kernel32", use_last_error=True)
    k.CreateToolhelp32Snapshot.argtypes = [w.DWORD, w.DWORD]
    k.CreateToolhelp32Snapshot.restype = w.HANDLE
    k.OpenProcess.argtypes = [w.DWORD, w.BOOL, w.DWORD]
    k.OpenProcess.restype = w.HANDLE
    k.GetProcessTimes.argtypes = [w.HANDLE] + [ctypes.POINTER(ctypes.c_ulonglong)] * 4
    k.GetProcessTimes.restype = w.BOOL
    k.CloseHandle.argtypes = [w.HANDLE]
    k.CloseHandle.restype = w.BOOL
    k.FreeConsole.argtypes = []
    k.FreeConsole.restype = w.BOOL
    k.AttachConsole.argtypes = [w.DWORD]
    k.AttachConsole.restype = w.BOOL
    k.CreateFileW.argtypes = [w.LPCWSTR, w.DWORD, w.DWORD, ctypes.c_void_p, w.DWORD, w.DWORD, w.HANDLE]
    k.CreateFileW.restype = w.HANDLE
    k.GetConsoleMode.argtypes = [w.HANDLE, ctypes.POINTER(w.DWORD)]
    k.GetConsoleMode.restype = w.BOOL
    k.SetConsoleMode.argtypes = [w.HANDLE, w.DWORD]
    k.SetConsoleMode.restype = w.BOOL
    k.WriteFile.argtypes = [w.HANDLE, ctypes.c_char_p, w.DWORD, ctypes.POINTER(w.DWORD), ctypes.c_void_p]
    k.WriteFile.restype = w.BOOL
    return k


def processi(k) -> dict:
    """{pid: (pid del padre, nome)} di tutti i processi, da una foto di Toolhelp."""
    import ctypes
    from ctypes import wintypes as w

    class Voce(ctypes.Structure):  # PROCESSENTRY32W
        _fields_ = [("dwSize", w.DWORD), ("cntUsage", w.DWORD), ("th32ProcessID", w.DWORD),
                    ("th32DefaultHeapID", ctypes.c_size_t), ("th32ModuleID", w.DWORD), ("cntThreads", w.DWORD),
                    ("th32ParentProcessID", w.DWORD), ("pcPriClassBase", w.LONG), ("dwFlags", w.DWORD),
                    ("szExeFile", w.WCHAR * 260)]

    k.Process32FirstW.argtypes = k.Process32NextW.argtypes = [w.HANDLE, ctypes.POINTER(Voce)]
    k.Process32FirstW.restype = k.Process32NextW.restype = w.BOOL
    foto = k.CreateToolhelp32Snapshot(0x2, 0)  # TH32CS_SNAPPROCESS
    if not foto or foto == w.HANDLE(-1).value:
        return {}
    tutti = {}
    try:
        v = Voce()
        v.dwSize = ctypes.sizeof(Voce)
        ok = k.Process32FirstW(foto, ctypes.byref(v))
        while ok:
            tutti[v.th32ProcessID] = (v.th32ParentProcessID, v.szExeFile)
            ok = k.Process32NextW(foto, ctypes.byref(v))
    finally:
        k.CloseHandle(foto)
    return tutti


def nascita(k, pid: int):
    import ctypes

    h = k.OpenProcess(0x1000, False, pid)  # PROCESS_QUERY_LIMITED_INFORMATION
    if not h:
        return None
    try:
        t = [ctypes.c_ulonglong() for _ in range(4)]
        if not k.GetProcessTimes(h, *(ctypes.byref(x) for x in t)):
            return None
        return t[0].value
    finally:
        k.CloseHandle(h)


def scrivi(k, pid: int, dati: bytes) -> bool:
    """Scrive `dati` sulla console del processo `pid`. Vero se l'ha scritta tutta."""
    import ctypes
    from ctypes import wintypes as w

    k.FreeConsole()  # una console sola per processo: senza lasciare la sua, AttachConsole fallisce
    if not k.AttachConsole(pid):
        return False
    try:
        # GENERIC_READ|GENERIC_WRITE, FILE_SHARE_READ|FILE_SHARE_WRITE, OPEN_EXISTING: Get/SetConsoleMode
        # chiedono anche la lettura.
        h = k.CreateFileW("CONOUT$", 0xC0000000, 0x3, None, 3, 0, None)
        if not h or h == w.HANDLE(-1).value:
            return False
        try:
            modo = w.DWORD()
            accendi = bool(k.GetConsoleMode(h, ctypes.byref(modo))) and not modo.value & VT
            if accendi:
                k.SetConsoleMode(h, modo.value | VT)
            scritti = w.DWORD()
            ok = k.WriteFile(h, dati, len(dati), ctypes.byref(scritti), None)
            if accendi:
                # Si rilegge la modalità: si spegne solo il VT acceso qui, il resto resta com'è adesso.
                ora = w.DWORD()
                if k.GetConsoleMode(h, ctypes.byref(ora)):
                    k.SetConsoleMode(h, ora.value & ~VT)
            return bool(ok) and scritti.value == len(dati)
        finally:
            k.CloseHandle(h)
    finally:
        k.FreeConsole()


def main(argv: list) -> int:
    stato = argv[1] if len(argv) > 1 else ""
    if sys.platform != "win32":
        return NON_WINDOWS
    if stato not in STATI:
        return 0
    import os
    import tempfile

    k = _kernel32()
    pid, figlio = sali(processi(k), os.getpid(), lambda p: nascita(k, p))
    if not pid:
        return 0
    ora = nascita(k, figlio)
    if ora is None:  # senza l'ora dell'hook non c'è ordine: lo stato parte comunque
        scrivi(k, pid, sequenza(stato))
        return 0
    file = os.path.join(tempfile.gettempdir(), f"herdr-stato-{pid}-{nascita(k, pid) or 0}.txt")
    in_ordine(file, ora, lambda: scrivi(k, pid, sequenza(stato)))
    return 0


if __name__ == "__main__":
    try:
        rc = main(sys.argv)
    except Exception:  # un hook di stato non ferma mai Claude Code
        rc = 0
    sys.exit(rc)
