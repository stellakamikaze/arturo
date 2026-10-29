"""arturo schede: nel Terminale di macOS la scheda mostra solo il titolo che scrive scheda-terminale.py.

Il Terminale di Apple accoda al titolo della scheda il processo attivo, la cartella e l'indicatore di
attività: "arturo  caffeinate ◂ claude …". Federico, 29/10/2026: la scheda deve dire solo il progetto,
o "SBLOCCA · <progetto>", e per tutti. Le sette chiavi del profilo che lo fanno sono in CHIAVI.

Terminale non rilegge un profilo cambiato da fuori, e quando salva i profili riscrive le preferenze
dalla sua memoria: una chiave scritta con defaults sparisce al primo salvataggio (provato il 29/10).
Per questo il profilo nuovo entra dal vivo: un file .terminal aperto con open, poi AppleScript sul
modello di Terminale per assegnarlo alle schede e farne il predefinito. Il profilo "Arturo" è una copia
di quello predefinito (stessi colori e font) con le sette chiavi spente; quello di prima resta, e
"arturo schede ripristina" lo rimette.

session-start.sh lancia "applica --una-volta" alla prima sessione nel Terminale di Apple: vale per chi
installa e per chi aggiorna. Il segno sta in ~/.claude/data/schede-terminale.json, che nessun
aggiornamento tocca; dopo tre tentativi falliti non riprova più da solo.

AppleScript riceve i nomi dei profili come argv, mai dentro il testo dello script. ARTURO_SISTEMA
finge il sistema, solo per i banchi. Solo libreria standard, Python 3.8 o successivo.
"""
from __future__ import annotations

import json
import os
import plistlib
import subprocess
import sys
import tempfile
import time
from pathlib import Path

AIUTO = """arturo schede: nel Terminale di macOS la scheda mostra solo il progetto, o "SBLOCCA · <progetto>".

  arturo schede stato                    il profilo predefinito e se il titolo è già pulito
  arturo schede applica                  crea il profilo "Arturo" (copia del tuo, senza processo,
                                         cartella e indicatore nel titolo) e lo mette su tutte le schede
  arturo schede ripristina               rimette il profilo di prima e cancella "Arturo"

La prima sessione nel Terminale di Apple lo applica da sola (session-start.sh)."""

NOME = "Arturo"
CHIAVI = ("ShowActiveProcessInTabTitle", "ShowActiveProcessArgumentsInTabTitle", "ShowComponentsWhenTabHasCustomTitle",
          "ShowRepresentedURLInTabTitle", "ShowRepresentedURLPathInTabTitle", "ShowTTYNameInTabTitle",
          "ShowActivityIndicatorInTab")
TENTATIVI = 3
ATTESA = 4.0  # secondi per vedere comparire il profilo importato
# session-start.sh ha 10 secondi in tutto: ogni comando ne ha al massimo 4, e di solito basta mezzo.
TEMPO = 4
LUCCHETTO_VECCHIO = 60  # secondi: un lucchetto più vecchio è di un processo morto

# Assegna il profilo nuovo alle schede che usano quello vecchio, poi predefinito e, se era il vecchio,
# di avvio. Rende il nome del predefinito, per controllare che il cambio sia avvenuto.
SCAMBIA = [
    "on run argv",
    'tell application "Terminal"',
    "set vecchio to item 1 of argv",
    "set nuovo to settings set (item 2 of argv)",
    "repeat with w in windows",
    "repeat with t in tabs of w",
    "if name of current settings of t is vecchio then set current settings of t to nuovo",
    "end repeat",
    "end repeat",
    "if name of startup settings is vecchio then set startup settings to nuovo",
    "set default settings to nuovo",
    "return name of default settings",
    "end tell",
    "end run",
]


class Errore(Exception):
    pass


def sistema() -> str:
    finto = os.environ.get("ARTURO_SISTEMA", "")
    if finto in ("darwin", "windows", "linux"):
        return finto
    if sys.platform == "darwin":
        return "darwin"
    return "windows" if os.name == "nt" else "linux"


def file_segno() -> Path:
    return Path.home() / ".claude" / "data" / "schede-terminale.json"


def leggi_segno() -> dict:
    try:
        dati = json.loads(file_segno().read_text(encoding="utf-8"))
        return dati if isinstance(dati, dict) else {}
    except (OSError, ValueError):
        return {}


def scrivi_segno(dati: dict) -> None:
    f = file_segno()
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(json.dumps(dict(dati, quando=time.strftime("%Y-%m-%dT%H:%M:%S")), ensure_ascii=False) + "\n",
                 encoding="utf-8")


def esegui(argv: list, cosa: str) -> str:
    try:
        r = subprocess.run(argv, capture_output=True, timeout=TEMPO)
    except (OSError, subprocess.SubprocessError) as e:
        raise Errore(f"{cosa}: {e}")
    if r.returncode != 0:
        raise Errore(f"{cosa}: {r.stderr.decode('utf-8', 'replace').strip()[:160] or f'exit {r.returncode}'}")
    return r.stdout.decode("utf-8", "replace")


def osa(righe: list, *argomenti: str, cosa: str = "AppleScript") -> str:
    argv = ["osascript"]
    for riga in righe:
        argv += ["-e", riga]
    return esegui(argv + list(argomenti), cosa).strip()


def preferenze() -> dict:
    """Le preferenze di Terminale come le vede cfprefsd adesso, non il file su disco."""
    testo = esegui(["defaults", "export", "com.apple.Terminal", "-"], "lettura delle preferenze di Terminale")
    try:
        dati = plistlib.loads(testo.encode("utf-8"))
    except Exception as e:  # plistlib solleva tipi diversi a seconda del formato rotto
        raise Errore(f"preferenze di Terminale illeggibili: {e}")
    return dati if isinstance(dati, dict) else {}


def predefinito(prefs: dict) -> tuple:
    """(nome, profilo) del profilo predefinito; il profilo è {} se non sta nelle preferenze."""
    nome = str(prefs.get("Default Window Settings") or "Basic")
    profili = prefs.get("Window Settings") if isinstance(prefs.get("Window Settings"), dict) else {}
    profilo = profili.get(nome)
    return nome, (profilo if isinstance(profilo, dict) else {})


def pulito(profilo: dict) -> bool:
    return all(profilo.get(k) is False for k in CHIAVI)


def finestre() -> set:
    uscita = osa(['tell application "Terminal" to get id of every window'], cosa="elenco delle finestre")
    return {x.strip() for x in uscita.split(",") if x.strip().isdigit()}


def profili_aperti() -> list:
    uscita = osa(['tell application "Terminal" to get name of every settings set'], cosa="elenco dei profili")
    return [x.strip() for x in uscita.split(",")]


def importa(profilo: dict) -> None:
    """Apre il .terminal del profilo nuovo e chiude la finestra vuota che l'import apre."""
    prima = finestre()
    cartella = Path(tempfile.mkdtemp(prefix="arturo-schede."))
    try:
        file = cartella / f"{NOME}.terminal"
        with open(file, "wb") as f:
            plistlib.dump(profilo, f)
        esegui(["open", "-g", "-a", "Terminal", str(file)], "apertura del profilo")
        limite = time.time() + float(os.environ.get("ARTURO_SCHEDE_ATTESA", ATTESA))
        while NOME not in profili_aperti():
            if time.time() >= limite:
                raise Errore(f'il profilo "{NOME}" non è comparso in Terminale')
            time.sleep(0.3)
        # La finestra dell'import arriva dopo il profilo (provato il 29/10): si aspetta anche lei.
        nuove = finestre() - prima
        while not nuove and time.time() < limite:
            time.sleep(0.3)
            nuove = finestre() - prima
    finally:
        for f in cartella.glob("*"):
            f.unlink()
        cartella.rmdir()
    # Si chiude solo una finestra nuova e senza processi al lavoro: mai una sessione della persona.
    # Appena nata la finestra è occupata dal login per un attimo (provato il 29/10): si aspetta che
    # si liberi; se resta occupata fino al limite, resta aperta.
    for wid in sorted(nuove):
        while True:
            occupate = osa(["on run argv", 'tell application "Terminal" to get busy of every tab of window id '
                            "((item 1 of argv) as integer)", "end run"], wid, cosa="controllo della finestra nuova")
            if "true" not in occupate or time.time() >= limite:
                break
            time.sleep(0.3)
        if "true" not in occupate:
            osa(["on run argv", 'tell application "Terminal" to close window id ((item 1 of argv) as integer)',
                 "end run"], wid, cosa="chiusura della finestra nuova")


def applica(una_volta: bool) -> int:
    if sistema() != "darwin":
        if not una_volta:
            print("SCHEDE: serve solo nel Terminale di macOS: qui non c'è niente da fare.")
        return 0
    segno = leggi_segno()
    if una_volta and (os.environ.get("TERM_PROGRAM") != "Apple_Terminal" or segno.get("fatto")
                      or int(segno.get("tentativi") or 0) >= TENTATIVI):
        return 0
    # Due sessioni che partono insieme: il profilo lo importa una sola. mkdir è atomico.
    lucchetto = file_segno().with_suffix(".lock")
    lucchetto.parent.mkdir(parents=True, exist_ok=True)
    try:
        if lucchetto.exists() and time.time() - lucchetto.stat().st_mtime > LUCCHETTO_VECCHIO:
            lucchetto.rmdir()
        lucchetto.mkdir()
    except OSError:
        return 0
    try:
        return _applica(una_volta, segno)
    finally:
        try:
            lucchetto.rmdir()
        except OSError:
            pass


def _applica(una_volta: bool, segno: dict) -> int:
    try:
        prefs = preferenze()
        nome, profilo = predefinito(prefs)
        if nome == NOME or pulito(profilo):
            scrivi_segno({"fatto": True, "prima": segno.get("prima") or nome, "gia_pulito": True})
            if not una_volta:
                print(f'SCHEDE: il profilo "{nome}" mostra già solo il titolo: niente da cambiare.')
            return 0
        if not profilo and nome != "Basic":
            raise Errore(f'il profilo "{nome}" non si legge dalle preferenze')
        nuovo = dict(profilo)
        nuovo.update({k: False for k in CHIAVI}, name=NOME, type="Window Settings")
        if NOME not in profili_aperti():
            importa(nuovo)
        avvio = str(prefs.get("Startup Window Settings") or nome)
        if osa(SCAMBIA, nome, NOME, cosa="assegnazione del profilo") != NOME:
            raise Errore(f'il profilo predefinito non è diventato "{NOME}"')
    except Errore as e:
        tentativi = int(segno.get("tentativi") or 0) + 1
        scrivi_segno({"fatto": False, "tentativi": tentativi, "errore": str(e)[:200]})
        dopo = "riprovo alla prossima sessione" if tentativi < TENTATIVI else "non riprovo più da solo"
        print(f"SCHEDE: non ho sistemato il titolo delle schede del Terminale ({e}): {dopo}. "
              'A mano: "arturo schede applica".')
        return 0 if una_volta else 1
    scrivi_segno({"fatto": True, "prima": nome, "avvio_prima": avvio})
    print(f'SCHEDE: nel Terminale le schede mostrano solo il progetto, o "SBLOCCA · <progetto>". Ho creato il '
          f'profilo "{NOME}", copia di "{nome}" senza processo, cartella e indicatore nel titolo. '
          'Per tornare indietro: "arturo schede ripristina".')
    return 0


def ripristina() -> int:
    if sistema() != "darwin":
        print("SCHEDE: serve solo nel Terminale di macOS: qui non c'è niente da fare.")
        return 0
    segno = leggi_segno()
    prima = str(segno.get("prima") or "Basic")
    try:
        if prima != NOME and NOME in profili_aperti():
            osa(SCAMBIA, NOME, prima, cosa="ritorno al profilo di prima")
            osa(["on run argv", 'tell application "Terminal" to delete settings set (item 1 of argv)', "end run"],
                NOME, cosa=f'cancellazione del profilo "{NOME}"')
    except Errore as e:
        print(f"SCHEDE: ripristino non riuscito: {e}", file=sys.stderr)
        return 1
    # Il segno resta "fatto": la sessione dopo non deve rimettere il profilo che la persona ha tolto.
    scrivi_segno({"fatto": True, "prima": prima, "ripristinato": True})
    print(f'SCHEDE: torna il profilo "{prima}", e "{NOME}" non c\'è più.')
    return 0


def stato() -> int:
    if sistema() != "darwin":
        print("SCHEDE: serve solo nel Terminale di macOS.")
        return 0
    try:
        nome, profilo = predefinito(preferenze())
    except Errore as e:
        print(f"SCHEDE: {e}", file=sys.stderr)
        return 1
    segno = leggi_segno()
    print(f'profilo predefinito: "{nome}", titolo {"pulito" if nome == NOME or pulito(profilo) else "con processo e cartella"}')
    print(f"segno: {json.dumps(segno, ensure_ascii=False) if segno else 'nessuno'}")
    return 0


def main(argv: list) -> int:
    voce = argv[0] if argv else ""
    if voce in ("", "-h", "--help", "aiuto", "help"):
        print(AIUTO)
        return 0 if voce else 2
    if voce == "applica" and argv[1:] in ([], ["--una-volta"]):
        return applica(argv[1:] == ["--una-volta"])
    if voce == "ripristina" and len(argv) == 1:
        return ripristina()
    if voce == "stato" and len(argv) == 1:
        return stato()
    print(f"Errore: comando non previsto: {' '.join(argv)}\n\n{AIUTO}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
