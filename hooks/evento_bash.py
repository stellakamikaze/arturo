#!/usr/bin/env python3
"""La parte Python di bash-dispatcher.sh: un processo al posto di tre, e le guardie dalla cache (#6327, 22/11/2026).

Modulo del dispatcher, non un hook. Due comandi:

  evento_bash.py leggi [crlf]
      Legge su stdin il JSON del PreToolUse e scrive su stdout quattro campi: il comando com'è scritto
      (COMMAND), il comando che leggono le guardie (GUARD_COMMAND), la copia dell'evento col comando delle
      guardie (GUARD_INPUT) e il tool_use_id. La prima riga dà la lunghezza in byte di ognuno, poi i campi
      seguono attaccati: il dispatcher li legge con un solo `$(...)`, che legge a blocchi. Un separatore
      nullo obbligava `read -d ''`, che da una pipe legge un byte alla volta (430 ms su 300.000 caratteri).
      Prima servivano jq e due python3, uno per gli heredoc e uno per la copia: su un Mac erano circa 50 ms a
      ogni comando Bash.
      GUARD_COMMAND è il comando senza gli heredoc inerti (heredoc.py, Heredoc.dati) e senza il suffisso `.exe`
      in fondo alle parole. Con `crlf` (Git Bash su Windows) il CR davanti a un LF si toglie, come faceva il
      dispatcher. Un campo che non si costruisce esce vuoto, e il dispatcher chiede conferma: una guardia non
      riceve mai meno di quello che bash esegue.
      I campi seguono le regole della shell di prima: gli a capo in coda spariscono, come in `$(...)`, e un
      byte nullo sparisce, come lo toglieva bash.

  evento_bash.py esegui FILE [ARG...]
      Esegue lo script FILE come `python3 FILE ARG...`, ma dal bytecode in __pycache__: uno script lanciato
      direttamente si ricompila dal sorgente a ogni avvio, e per block-dangerous (4.000 righe) erano circa 19
      ms su 65. Il bytecode è a hash controllato (PEP 552): Python lo usa solo se l'impronta del sorgente è
      quella di quando l'ha compilato, anche dopo una modifica nello stesso secondo e con la stessa
      lunghezza. Se la cartella non è scrivibile, Python compila in memoria come prima. Codice d'uscita,
      stdout e stderr sono quelli dello script.

Solo libreria standard, Python 3.8 o successivo.
"""
import os
import sys

# Su Windows il suffisso `.exe` in fondo a una parola si toglie prima di ogni confronto: `rm.exe` è `rm`
# (revisione del 10/11/2026, HK-1). È la regex del ciclo che stava nel dispatcher (_RE_EXE), con la classe
# [[:space:]] di bash scritta per intero: `\s` di Python conta anche gli spazi Unicode.
_SPAZI = " \t\n\r\f\v"
_RE_EXE = None


def _senza_exe(testo):
    global _RE_EXE
    if ".exe" not in testo.lower():
        return testo
    if _RE_EXE is None:
        import re
        _RE_EXE = re.compile("^(.*[^" + _SPAZI + "/\\\\])\\.[Ee][Xx][Ee]([" + _SPAZI + ";&|()<>\"'`].*)?\\Z", re.S)
    while True:
        m = _RE_EXE.match(testo)
        if not m:
            return testo
        testo = m.group(1) + (m.group(2) or "")


def _riduci_heredoc(comando):
    """GUARD_COMMAND prima del suffisso .exe: il comando senza gli heredoc che vanno a un lettore e che nessuno
    esegue (heredoc.py). Un errore tiene il comando intero, come faceva il dispatcher."""
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "arturo_heredoc", os.path.join(os.path.dirname(os.path.abspath(__file__)), "heredoc.py"))
        hd = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(hd)
        # Il dispatcher passava il comando con `<<<`, che aggiunge un a capo: la chiusura di un heredoc in
        # fondo al comando si riconosce solo con quell'a capo.
        return hd.togli((comando + "\n").replace("\r\n", "\n"), lambda h: h.dati()).rstrip("\n")
    except Exception:
        return comando


def leggi(crlf):
    import json
    campi = ["", "", "", ""]
    grezzo = sys.stdin.buffer.read().decode("utf-8", "replace")
    try:
        dati = json.loads(grezzo)
    except Exception:
        dati = None
    comando = ""
    if isinstance(dati, dict) and isinstance(dati.get("tool_input"), dict):
        valore = dati["tool_input"].get("command")
        if isinstance(valore, str):
            comando = valore
        elif valore is not None and valore is not False:
            comando = json.dumps(valore)
    # Un surrogato isolato (`\ud800` nel JSON) non si scrive in UTF-8: diventa `?` qui e in ogni copia.
    comando = comando.encode("utf-8", "replace").decode("utf-8").replace("\0", "").rstrip("\n")
    if crlf:
        comando = comando.replace("\r\n", "\n")
    campi[0] = comando
    guardie = _riduci_heredoc(comando)
    if crlf:
        guardie = guardie.replace("\r\n", "\n")
    guardie = _senza_exe(guardie)
    campi[1] = guardie
    if isinstance(dati, dict):
        try:
            copia = dict(dati)
            copia["tool_input"] = dict(dati.get("tool_input") or {})
            copia["tool_input"]["command"] = guardie
            campi[2] = json.dumps(copia)
        except Exception:
            campi[2] = ""
        uso = dati.get("tool_use_id")
        campi[3] = uso if isinstance(uso, str) and "\0" not in uso else ""
    dati_campi = [c.encode("utf-8", "replace") for c in campi]
    testa = " ".join(str(len(c)) for c in dati_campi).encode("ascii") + b"\n"
    sys.stdout.buffer.write(testa + b"".join(dati_campi))
    return 0


def _bytecode_controllato(percorso):
    """Il bytecode di `percorso` a hash controllato, se manca o è di un altro tipo. Un errore non conta:
    Python compila in memoria."""
    if sys.dont_write_bytecode:
        return
    try:
        import importlib.util
        pyc = importlib.util.cache_from_source(percorso)
        try:
            with open(pyc, "rb") as f:
                testa = f.read(8)
            # Byte 4-7: i flag di PEP 552. 3 = a hash, da controllare sul sorgente a ogni avvio.
            if testa[:4] == importlib.util.MAGIC_NUMBER and int.from_bytes(testa[4:8], "little") == 3:
                return
        except OSError:
            pass
        import py_compile
        py_compile.compile(percorso, cfile=pyc, doraise=True,
                           invalidation_mode=py_compile.PycInvalidationMode.CHECKED_HASH)
    except Exception:
        pass


def esegui(percorso, argomenti):
    import importlib.util
    percorso = os.path.abspath(percorso)
    _bytecode_controllato(percorso)
    sys.argv = [percorso] + list(argomenti)
    # Come per uno script: la sua cartella è la prima dove cerca i moduli.
    sys.path[0] = os.path.dirname(percorso)
    spec = importlib.util.spec_from_file_location("__main__", percorso)
    modulo = importlib.util.module_from_spec(spec)
    sys.modules["__main__"] = modulo
    spec.loader.exec_module(modulo)
    return 0


def main():
    if sys.argv[1:2] == ["leggi"]:
        return leggi(sys.argv[2:3] == ["crlf"])
    if sys.argv[1:2] == ["esegui"] and len(sys.argv) >= 3:
        return esegui(sys.argv[2], sys.argv[3:])
    sys.stderr.write("uso: evento_bash.py leggi [crlf] | esegui FILE [ARG...]\n")
    return 64


if __name__ == "__main__":
    sys.exit(main())
