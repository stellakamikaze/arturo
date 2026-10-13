"""arturo telemetria: i dati d'uso minimi che Arturo manda a chi lo mantiene.

Perché esiste: Arturo si sviluppa ogni giorno per persone che spesso non sanno dire dove si
bloccano. Senza dati d'uso chi lo mantiene non vede le guardie che fermano un lavoro legittimo, gli
aggiornamenti che si rompono, i comandi che nessuno usa.

Cosa esce, e solo questo: un id di installazione casuale (non legato alla persona), la versione di
Arturo, il sistema operativo (Darwin, Linux, Windows) e gli eventi di EVENTI con il solo giorno.
Mai prompt, file, percorsi, nomi, risposte o il percorso a tappe. Il server non salva l'IP e tiene
gli eventi 12 mesi. Il suo codice è in server/.

Accesa di default. Si spegne con `arturo telemetria spegni`, con ARTURO_TELEMETRIA=0 o con lo
standard DO_NOT_TRACK=1. `arturo telemetria mostra` fa vedere l'id e la coda, così si vede
esattamente cosa parte.

Due tempi, perché un hook non deve mai aspettare la rete:
- `registra` aggiunge una riga alla coda in ~/.claude/data/telemetria/coda.jsonl, senza rete;
- `invia` manda la coda in un lotto. L'avvio della sessione lo lancia in background, al massimo
  ogni 6 ore. Manda anche le segnalazioni di /segnala rimaste in attesa.

Lo stato (id, ultimo tentativo, spenta, avviso dato) sta in ~/.claude/session-env/telemetria.json.
Solo libreria standard, Python 3.8 o successivo. Nessun comando di questo modulo fallisce in modo
da fermare un hook: gli errori di registra e avvio tacciono.
"""
from __future__ import annotations

import json
import os
import platform
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(os.path.realpath(__file__)).parent))
import todo_store as ts  # noqa: E402

URL = "https://arturo-dati.stellakamikaze.org"
# L'elenco chiuso. Lo stesso elenco sta in server/logica.js e nel README (banco M09).
EVENTI = {
    "sessione": re.compile(r"^$"),
    "comando": re.compile(r"^[a-z0-9-]{1,40}$"),
    "guardia": re.compile(r"^[a-z0-9_.-]{1,60}$"),
    "aggiorna": re.compile(r"^(applicato|conflitto|fallito)$"),
    "segnalazione": re.compile(r"^(problema|proposta|integrazione)$"),
}
OGNI = 6 * 3600          # secondi fra due invii automatici
CODA_MASSIMA = 2000      # righe: oltre, gli eventi nuovi si perdono finché la coda non parte
LOTTO = 500
SPENTI = {"0", "no", "off", "false", "spenta"}

AIUTO = f"""arturo telemetria: i dati d'uso minimi che Arturo manda a chi lo mantiene.

  stato          accesa o spenta, e perché
  mostra         l'id di questa installazione e gli eventi in coda, così come partono
  spegni         la spegne e svuota la coda
  accendi        la riaccende
  invia          manda adesso la coda e le segnalazioni in attesa

Escono solo questi eventi, con il giorno e mai l'ora: {", ".join(EVENTI)}.
Mai prompt, file, percorsi, nomi o risposte. Server: {URL} (codice in server/).
Si spegne anche con ARTURO_TELEMETRIA=0 o DO_NOT_TRACK=1."""


def file_stato() -> Path:
    return Path.home() / ".claude" / "session-env" / "telemetria.json"


def file_coda() -> Path:
    return Path.home() / ".claude" / "data" / "telemetria" / "coda.jsonl"


def cartella_attesa() -> Path:
    return Path.home() / ".claude" / "data" / "segnalazioni"


def url() -> str:
    return os.environ.get("ARTURO_TELEMETRIA_URL", URL).rstrip("/")


def leggi_stato() -> dict:
    try:
        stato = json.loads(file_stato().read_text(encoding="utf-8"))
        return stato if isinstance(stato, dict) else {}
    except (OSError, ValueError, UnicodeDecodeError):
        return {}


def cambia_stato(cambia) -> dict:
    with ts.Lucchetto(file_stato()):
        stato = leggi_stato()
        cambia(stato)
        ts.scrivi_json_atomico(file_stato(), stato)
    return stato


def perche_spenta(stato: dict | None = None):
    """None se è accesa, altrimenti il motivo."""
    if os.environ.get("ARTURO_TELEMETRIA", "").strip().lower() in SPENTI:
        return "ARTURO_TELEMETRIA=0"
    if os.environ.get("DO_NOT_TRACK", "").strip() not in ("", "0"):
        return "DO_NOT_TRACK"
    if (stato if stato is not None else leggi_stato()).get("spenta"):
        return "arturo telemetria spegni"
    return None


def installazione() -> str:
    stato = leggi_stato()
    if isinstance(stato.get("id"), str) and re.fullmatch(r"[A-Za-z0-9-]{8,64}", stato["id"]):
        return stato["id"]
    nuovo = str(uuid.uuid4())
    return cambia_stato(lambda s: s.setdefault("id", nuovo))["id"]


def versione() -> str:
    try:
        r = subprocess.run(["git", "-C", str(Path.home() / ".claude"), "describe", "--tags", "--always"],
                           capture_output=True, text=True, timeout=3)
        return (r.stdout.strip() if r.returncode == 0 else "")[:60] or "sconosciuta"
    except (OSError, subprocess.SubprocessError):
        return "sconosciuta"


def sistema() -> str:
    nome = platform.system()
    return nome if nome in ("Darwin", "Linux", "Windows") else "altro"


def valido(evento: str, valore: str) -> bool:
    regola = EVENTI.get(evento)
    return bool(regola) and isinstance(valore, str) and bool(regola.match(valore))


def registra(evento: str, valore: str = "") -> bool:
    """Aggiunge un evento alla coda. Non usa la rete e non solleva mai."""
    try:
        if perche_spenta() or not valido(evento, valore):
            return False
        coda = file_coda()
        coda.parent.mkdir(parents=True, exist_ok=True)
        with ts.Lucchetto(coda):
            if coda.exists():
                with coda.open(encoding="utf-8") as f:
                    if sum(1 for _ in f) >= CODA_MASSIMA:
                        return False
            with coda.open("a", encoding="utf-8") as f:
                f.write(json.dumps({"giorno": ts.oggi().isoformat(), "evento": evento, "valore": valore}) + "\n")
        return True
    except Exception:  # noqa: BLE001 - un hook non si ferma mai per la telemetria
        return False


def leggi_coda() -> list:
    try:
        righe = file_coda().read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeDecodeError):
        return []
    eventi = []
    for riga in righe:
        try:
            e = json.loads(riga)
        except ValueError:
            continue
        if isinstance(e, dict) and valido(e.get("evento", ""), e.get("valore", "")):
            eventi.append({"giorno": str(e.get("giorno", ""))[:10], "evento": e["evento"], "valore": e["valore"]})
    return eventi


def posta(rotta: str, dati: dict, timeout: float = 5) -> int:
    """POST JSON. Torna lo status HTTP, 0 se la rete non risponde."""
    corpo = json.dumps(dati, ensure_ascii=False).encode("utf-8")
    richiesta = urllib.request.Request(url() + rotta, data=corpo, method="POST",
                                       headers={"content-type": "application/json", "user-agent": "arturo"})
    try:
        with urllib.request.urlopen(richiesta, timeout=timeout) as r:
            return r.status
    except urllib.error.HTTPError as e:
        return e.code
    except (urllib.error.URLError, OSError, ValueError):
        return 0


def invia_segnalazioni_in_attesa() -> int:
    """Le segnalazioni approvate ma non partite: sono un sì della persona, partono anche a telemetria spenta."""
    partite = 0
    for f in sorted(cartella_attesa().glob("*.attesa.json")):
        try:
            dati = json.loads(f.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        status = posta("/v1/segnalazioni", dati)
        if 200 <= status < 300:
            f.unlink()
            partite += 1
        elif status in (400, 413):
            f.rename(f.with_name(f.name.replace(".attesa.json", ".rifiutata.json")))
        else:
            break  # rete giù o server pieno: si riprova la volta dopo
    return partite


def invia() -> tuple:
    """Torna (eventi partiti, segnalazioni partite)."""
    cambia_stato(lambda s: s.__setitem__("ultimo_tentativo", int(time.time())))
    segnalazioni = invia_segnalazioni_in_attesa()
    if perche_spenta():
        return 0, segnalazioni
    eventi = leggi_coda()
    if not eventi:
        return 0, segnalazioni
    base = {"installazione": installazione(), "versione": versione(), "sistema": sistema()}
    partiti = 0
    for i in range(0, len(eventi), LOTTO):
        lotto = eventi[i:i + LOTTO]
        status = posta("/v1/eventi", dict(base, eventi=lotto))
        if 200 <= status < 300 or status in (400, 413):
            partiti += len(lotto)  # un lotto rifiutato non si rimanda all'infinito
        else:
            break
    if partiti:
        coda = file_coda()
        with ts.Lucchetto(coda):
            # Le righe registrate nel frattempo restano: si tolgono solo quelle partite.
            righe = coda.read_text(encoding="utf-8").splitlines() if coda.exists() else []
            resto = righe[partiti:] if len(righe) >= partiti else []
            coda.write_text("".join(r + "\n" for r in resto), encoding="utf-8")
    return partiti, segnalazioni


def avvio() -> int:
    """Lo chiama session-start.sh: registra la sessione, stampa l'avviso una volta, lancia l'invio."""
    try:
        stato = leggi_stato()
        if perche_spenta(stato):
            if any(cartella_attesa().glob("*.attesa.json")):
                _invio_in_background()
            return 0
        registra("sessione")
        if not stato.get("avviso"):
            print("TELEMETRIA: Arturo manda a chi lo mantiene dati d'uso anonimi (versione, sistema, comandi di Arturo "
                  "usati, guardie scattate, esiti di /aggiorna), con un id casuale e mai prompt, file o nomi. "
                  "Dillo alla persona una volta, in due righe, con il perché: senza questi dati chi mantiene Arturo "
                  "non vede dove si blocca chi lo usa. Si spegne con: python3 ~/.claude/bin/arturo telemetria spegni")
            cambia_stato(lambda s: s.__setitem__("avviso", ts.oggi().isoformat()))
        ultimo = stato.get("ultimo_tentativo")
        if not isinstance(ultimo, int) or time.time() - ultimo > OGNI:
            _invio_in_background()
    except Exception:  # noqa: BLE001
        pass
    return 0


def _invio_in_background() -> None:
    opzioni = {"stdin": subprocess.DEVNULL, "stdout": subprocess.DEVNULL, "stderr": subprocess.DEVNULL}
    if os.name == "nt":
        opzioni["creationflags"] = 0x00000008 | 0x00000200  # DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP
    else:
        opzioni["start_new_session"] = True
    subprocess.Popen([sys.executable, os.path.realpath(__file__), "invia", "--zitto"], **opzioni)


def main(argv: list) -> int:
    if not argv or argv[0] in ("-h", "--help", "aiuto", "help"):
        print(AIUTO)
        return 0
    comando, resto = argv[0], argv[1:]
    if comando == "registra" and 1 <= len(resto) <= 2:
        registra(resto[0], resto[1] if len(resto) == 2 else "")
        return 0
    if comando == "avvio" and not resto:
        return avvio()
    if comando == "invia" and resto in ([], ["--zitto"]):
        partiti, segnalazioni = invia()
        if not resto:
            spenta = perche_spenta()
            print(f"Eventi partiti: {partiti}" + (f" (telemetria spenta: {spenta})" if spenta else "")
                  + f". Segnalazioni partite: {segnalazioni}.")
        return 0
    if comando == "stato" and not resto:
        spenta = perche_spenta()
        print(f"Telemetria {'spenta (' + spenta + ')' if spenta else 'accesa'}. Server: {url()}")
        return 0
    if comando == "mostra" and not resto:
        stato = leggi_stato()
        print(f"Id di questa installazione: {stato.get('id', '(non ancora creato)')}")
        print(f"Versione: {versione()} · Sistema: {sistema()}")
        eventi = leggi_coda()
        print(f"Eventi in coda: {len(eventi)}")
        for e in eventi:
            print(f"  {e['giorno']}  {e['evento']}" + (f"  {e['valore']}" if e["valore"] else ""))
        return 0
    if comando == "spegni" and not resto:
        cambia_stato(lambda s: s.__setitem__("spenta", True))
        try:
            file_coda().unlink()
        except OSError:
            pass
        print("Telemetria spenta, coda svuotata. Per riaccenderla: arturo telemetria accendi\n"
              "/segnala continua a funzionare: ogni segnalazione parte solo con il tuo sì.")
        return 0
    if comando == "accendi" and not resto:
        cambia_stato(lambda s: s.__setitem__("spenta", False))
        spenta = perche_spenta()
        print("Telemetria accesa." + (f" Però resta spenta da {spenta}." if spenta else ""))
        return 0
    print(f"Errore: comando sconosciuto: «{' '.join(argv)}»\n\n{AIUTO}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
