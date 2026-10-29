"""arturo schede: nel Terminale di macOS la scheda mostra solo il titolo che scrive scheda-terminale.py.

Il Terminale di Apple accoda al titolo della scheda il processo attivo, la cartella e l'indicatore di
attività: "arturo  caffeinate ◂ claude …". Dal 29/10/2026 la scheda deve dire solo il progetto, o
"SBLOCCA · <progetto>", per tutti. Le sette chiavi del profilo che lo fanno sono in CHIAVI.

Terminale non rilegge un profilo cambiato da fuori, e quando salva i profili riscrive le preferenze
dalla sua memoria: una chiave scritta con defaults sparisce al primo salvataggio (provato il 29/10).
Per questo il profilo nuovo entra dal vivo: un file .terminal aperto con open, poi AppleScript sul
modello di Terminale per assegnarlo alle schede e farne il predefinito. Il profilo "Arturo" è una copia
di quello predefinito (stessi colori e font) con le sette chiavi spente; quello di prima resta, e
"arturo schede ripristina" lo rimette. Un profilo "Arturo" che la persona aveva già non si tocca.

session-start.sh lancia "applica --una-volta" alla prima sessione nel Terminale di Apple: vale per chi
installa e per chi aggiorna. L'avvio ha 10 secondi in tutto: il lavoro ha un tetto di TETTO secondi, e
il tentativo si conta PRIMA di lavorare, perché un processo ucciso dal timeout non arriva all'except.
Il segno sta in ~/.claude/data/schede-terminale.json, che nessun aggiornamento tocca; dopo TENTATIVI
tentativi l'avvio non riprova più da solo.

AppleScript riceve i nomi come argv, mai dentro il testo dello script; gli script stanno in costanti,
così il banco li compila con osacompile. ARTURO_SISTEMA finge il sistema, solo per i banchi. Solo
libreria standard, Python 3.8 o successivo.
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
TETTO = 6.0  # secondi per tutto il lavoro: session-start.sh ne ha 10, e il resto dell'avvio ne usa uno
LUCCHETTO_VECCHIO = 60  # secondi: un lucchetto più vecchio è di un processo morto
RISERVA = 1.5  # secondi che l'attesa della finestra lascia allo scambio dei profili

# Assegna il profilo nuovo alle schede che usano quello vecchio, poi predefinito e, se era il vecchio,
# di avvio. Rende il nome del predefinito, per controllare che il cambio sia avvenuto.
SCAMBIA = (
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
)
FINESTRE = ('tell application "Terminal" to get id of every window',)
ESISTE = ("on run argv", 'tell application "Terminal" to return exists settings set (item 1 of argv)', "end run")
# Della finestra: se qualche scheda è al lavoro, e il profilo della prima scheda.
FINESTRA = ("on run argv", 'tell application "Terminal"', "set w to window id ((item 1 of argv) as integer)",
            "return {busy of every tab of w, name of current settings of tab 1 of w}", "end tell", "end run")
CHIUDI = ("on run argv", 'tell application "Terminal" to close window id ((item 1 of argv) as integer)', "end run")
ELIMINA = ("on run argv", 'tell application "Terminal" to delete settings set (item 1 of argv)', "end run")
SCRIPT = {"SCAMBIA": SCAMBIA, "FINESTRE": FINESTRE, "ESISTE": ESISTE, "FINESTRA": FINESTRA, "CHIUDI": CHIUDI,
          "ELIMINA": ELIMINA}


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


def tentativi(segno: dict) -> int:
    try:
        return int(segno.get("tentativi") or 0)
    except (TypeError, ValueError):
        return TENTATIVI  # un segno illeggibile non deve far riprovare a ogni avvio


def scrivi_segno(dati: dict) -> None:
    f = file_segno()
    f.parent.mkdir(parents=True, exist_ok=True)
    provvisorio = f.with_name(f"{f.name}.{os.getpid()}.tmp")
    provvisorio.write_text(json.dumps(dict(dati, quando=time.strftime("%Y-%m-%dT%H:%M:%S")), ensure_ascii=False)
                           + "\n", encoding="utf-8")
    os.replace(str(provvisorio), str(f))


class Tempo:
    """Il tetto di tutto il lavoro: ogni comando ha al massimo il tempo che resta."""

    def __init__(self, secondi: float):
        self.fine = time.time() + secondi

    def resta(self) -> float:
        rimasto = self.fine - time.time()
        if rimasto <= 0:
            raise Errore("tempo finito")
        return rimasto


def esegui(argv: list, cosa: str, tempo: Tempo) -> str:
    try:
        r = subprocess.run(argv, capture_output=True, timeout=tempo.resta())
    except (OSError, subprocess.SubprocessError) as e:
        raise Errore(f"{cosa}: {e}")
    if r.returncode != 0:
        raise Errore(f"{cosa}: {r.stderr.decode('utf-8', 'replace').strip()[:160] or f'exit {r.returncode}'}")
    return r.stdout.decode("utf-8", "replace")


def osa(script: tuple, *argomenti: str, cosa: str, tempo: Tempo) -> str:
    argv = ["osascript"]
    for riga in script:
        argv += ["-e", riga]
    return esegui(argv + list(argomenti), cosa, tempo).strip()


def preferenze(tempo: Tempo) -> dict:
    """Le preferenze di Terminale come le vede cfprefsd adesso, non il file su disco."""
    testo = esegui(["defaults", "export", "com.apple.Terminal", "-"], "lettura delle preferenze di Terminale", tempo)
    try:
        dati = plistlib.loads(testo.encode("utf-8"))
    except Exception as e:  # plistlib solleva tipi diversi a seconda del formato rotto
        raise Errore(f"preferenze di Terminale illeggibili: {e}")
    return dati if isinstance(dati, dict) else {}


def profili(prefs: dict) -> dict:
    p = prefs.get("Window Settings")
    return p if isinstance(p, dict) else {}


def predefinito(prefs: dict) -> tuple:
    """(nome, profilo) del profilo predefinito; il profilo è {} se non sta nelle preferenze."""
    nome = str(prefs.get("Default Window Settings") or "Basic")
    profilo = profili(prefs).get(nome)
    return nome, (profilo if isinstance(profilo, dict) else {})


def pulito(profilo: dict) -> bool:
    return all(profilo.get(k) is False for k in CHIAVI)


def finestre(tempo: Tempo) -> set:
    uscita = osa(FINESTRE, cosa="elenco delle finestre", tempo=tempo)
    return {x.strip() for x in uscita.split(",") if x.strip().isdigit()}


def esiste(nome: str, tempo: Tempo) -> bool:
    return osa(ESISTE, nome, cosa="ricerca del profilo", tempo=tempo) == "true"


def importa(profilo: dict, tempo: Tempo) -> None:
    """Apre il .terminal del profilo nuovo e chiude la finestra vuota che l'import apre."""
    prima = finestre(tempo)
    cartella = Path(tempfile.mkdtemp(prefix="arturo-schede."))
    try:
        file = cartella / f"{NOME}.terminal"
        with open(file, "wb") as f:
            plistlib.dump(profilo, f)
        esegui(["open", "-g", "-a", "Terminal", str(file)], "apertura del profilo", tempo)
        while not esiste(NOME, tempo):
            time.sleep(0.3)
    finally:
        for f in cartella.glob("*"):
            f.unlink()
        cartella.rmdir()
    # La finestra dell'import arriva dopo il profilo, e appena nata il login la tiene occupata per un
    # attimo (provato il 29/10). Si chiude solo lei: nuova, col profilo "Arturo" (una finestra aperta
    # dalla persona in questi secondi ha ancora il profilo di prima) e senza processi al lavoro. Se non
    # si libera entro il tetto resta aperta: la si chiude a mano, mai una sessione della persona.
    try:
        while tempo.fine - time.time() > RISERVA:
            for wid in sorted(finestre(tempo) - prima):
                occupate, scheda = osa(FINESTRA, wid, cosa="controllo della finestra nuova", tempo=tempo).rsplit(", ", 1)
                if scheda == NOME and "true" not in occupate:
                    osa(CHIUDI, wid, cosa="chiusura della finestra nuova", tempo=tempo)
                    return
            time.sleep(0.3)
    except Errore:
        return  # il profilo c'è: la finestra rimasta non ferma il resto


def applica(una_volta: bool) -> int:
    if sistema() != "darwin":
        if not una_volta:
            print("SCHEDE: serve solo nel Terminale di macOS: qui non c'è niente da fare.")
        return 0
    segno = leggi_segno()
    if una_volta and (os.environ.get("TERM_PROGRAM") != "Apple_Terminal" or segno.get("fatto")
                      or tentativi(segno) >= TENTATIVI):
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
    conto = tentativi(segno) + 1
    # Prima di lavorare: se il timeout dell'avvio uccide il processo, il tentativo è già contato.
    scrivi_segno(dict(segno, fatto=False, tentativi=conto))
    tempo = Tempo(float(os.environ.get("ARTURO_SCHEDE_TETTO", TETTO)))
    try:
        prefs = preferenze(tempo)
        nome, profilo = predefinito(prefs)
        if (nome == NOME and segno.get("creato")) or pulito(profilo):
            scrivi_segno({"fatto": True, "prima": segno.get("prima") or nome,
                          "creato": bool(segno.get("creato") or segno.get("importato")), "gia_pulito": True})
            if not una_volta:
                print(f'SCHEDE: il profilo "{nome}" mostra già solo il titolo: niente da cambiare.')
            return 0
        nostro = bool(segno.get("importato") or segno.get("creato"))
        if (NOME in profili(prefs) or nome == NOME) and not nostro:
            raise Errore(f'c\'è già un profilo "{NOME}" tuo: non lo tocco')
        if not profilo and nome != "Basic":
            raise Errore(f'il profilo "{nome}" non si legge dalle preferenze')
        nuovo = dict(profilo)
        nuovo.update({k: False for k in CHIAVI}, name=NOME, type="Window Settings")
        avvio = str(prefs.get("Startup Window Settings") or nome)
        if not esiste(NOME, tempo):
            importa(nuovo, tempo)
            # Da qui il profilo è nostro: se il timeout uccide il processo, il giro dopo lo sa, e sa
            # quale profilo rimettere con ripristina.
            segno = dict(segno, importato=True, prima=nome, avvio_prima=avvio)
            scrivi_segno(dict(segno, fatto=False, tentativi=conto))
        if osa(SCAMBIA, nome, NOME, cosa="assegnazione del profilo", tempo=tempo) != NOME:
            raise Errore(f'il profilo predefinito non è diventato "{NOME}"')
    except Errore as e:
        resta = {k: v for k, v in segno.items() if k in ("importato", "prima", "avvio_prima")}
        scrivi_segno(dict(resta, fatto=False, tentativi=conto, errore=str(e)[:200]))
        dopo = "riprovo alla prossima sessione" if conto < TENTATIVI else "non riprovo più da solo"
        print(f"SCHEDE: non ho sistemato il titolo delle schede del Terminale ({e}): {dopo}. "
              'A mano: "python3 ~/.claude/bin/arturo schede applica".')
        return 0 if una_volta else 1
    scrivi_segno({"fatto": True, "prima": nome, "avvio_prima": avvio, "creato": True})
    print(f'SCHEDE: nel Terminale le schede mostrano solo il progetto, o "SBLOCCA · <progetto>". Ho creato il '
          f'profilo "{NOME}", copia di "{nome}" senza processo, cartella e indicatore nel titolo. '
          'Per tornare indietro: "python3 ~/.claude/bin/arturo schede ripristina".')
    return 0


def ripristina() -> int:
    if sistema() != "darwin":
        print("SCHEDE: serve solo nel Terminale di macOS: qui non c'è niente da fare.")
        return 0
    segno = leggi_segno()
    prima = str(segno.get("prima") or "Basic")
    if not (segno.get("creato") or segno.get("importato")):
        print(f'SCHEDE: il profilo "{NOME}" non l\'ho creato io: niente da ripristinare.')
        return 0
    tempo = Tempo(4 * TETTO)  # a mano, senza il timeout dell'avvio
    try:
        if prima != NOME and esiste(NOME, tempo):
            osa(SCAMBIA, NOME, prima, cosa="ritorno al profilo di prima", tempo=tempo)
            osa(ELIMINA, NOME, cosa=f'cancellazione del profilo "{NOME}"', tempo=tempo)
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
        nome, profilo = predefinito(preferenze(Tempo(TETTO)))
    except Errore as e:
        print(f"SCHEDE: {e}", file=sys.stderr)
        return 1
    segno = leggi_segno()
    print(f'profilo predefinito: "{nome}", titolo {"pulito" if pulito(profilo) else "con processo e cartella"}')
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
