#!/usr/bin/env python3
"""arturo web: la pagina dei todo nel browser, solo su questo computer.

Il server ascolta solo su 127.0.0.1, su una porta scelta dal sistema. Ogni avvio crea una
chiave casuale: il link stampato la contiene, e le API la vogliono nell'header X-Arturo-Token.
Un altro sito aperto nel browser non legge e non scrive niente: il controllo di Host, Origin,
chiave e Content-Type lo ferma prima.

Ogni lettura e ogni scrittura passano da todo_store, con le stesse regole della CLI. La pagina
non tiene dati suoi e il processo non scrive niente su disco, salvo l'archivio dei todo.

Il processo si ferma da solo dopo 30 minuti senza richieste (ARTURO_WEB_INATTIVO, in secondi,
cambia il tempo), con il bottone «Spegni la pagina» o con Ctrl+C.

Solo libreria standard, Python 3.8 o successivo.
"""
from __future__ import annotations

import argparse
import errno
import hmac
import json
import math
import os
import secrets
import sys
import threading
import time
import traceback
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

sys.path.insert(0, str(Path(os.path.realpath(__file__)).parent))
import todo_store as ts  # noqa: E402

HOST = "127.0.0.1"
CARTELLA = Path(os.path.realpath(__file__)).parent / "web"
MASSIMO = 16384  # byte di un corpo POST
INATTIVO = 1800  # secondi senza richieste prima di spegnersi

# Gli unici file serviti: nome nel link -> (file in bin/web, tipo). Nessun percorso si compone
# con quello che chiede il browser, quindi «..» e simili non escono mai da qui.
STATICI = {
    "stile.css": ("stile.css", "text/css; charset=utf-8"),
    "app.js": ("app.js", "text/javascript; charset=utf-8"),
    "font/sorts-mill-goudy.woff2": ("font/sorts-mill-goudy.woff2", "font/woff2"),
    "font/atkinson-next.woff2": ("font/atkinson-next.woff2", "font/woff2"),
    "font/atkinson-mono.woff2": ("font/atkinson-mono.woff2", "font/woff2"),
}

CSP = ("default-src 'none'; script-src 'self'; style-src 'self'; font-src 'self'; img-src 'self' data:; "
       "connect-src 'self'; base-uri 'none'; form-action 'none'; frame-ancestors 'none'")

TESTI_ERRORE = {
    400: "Richiesta non valida.",
    403: "Accesso negato: questa pagina risponde solo al link che ha stampato arturo web.",
    404: "Qui non c'è niente. Apri il link che ha stampato arturo web.",
    405: "Metodo non ammesso: la pagina usa solo GET e POST.",
    411: "Manca la lunghezza del corpo della richiesta.",
    413: "Richiesta troppo grande: il limite è 16 KB.",
    414: "Indirizzo troppo lungo.",
    415: "Formato non ammesso: la pagina accetta solo JSON.",
    431: "Intestazioni troppo grandi.",
    500: "Qualcosa non ha funzionato in Arturo web. Riprova, o chiedi a Claude di guardare.",
    501: "Metodo non ammesso: la pagina usa solo GET e POST.",
}

PAGINA_NEGATA = """<!doctype html>
<html lang="it"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Arturo · link da aprire</title><link rel="stylesheet" href="/static/stile.css"></head>
<body class="negata"><main><h1>Questo link non apre la pagina</h1>
<p>Apri il link che ha stampato arturo web, oppure chiedi a Claude di aprire la pagina dei todo.</p>
</main></body></html>
"""

AZIONI = ("aggiungi", "modifica", "nota", "deciso", "ripristina") + tuple(ts.AZIONI_STATO)
# La parola dell'esito di un ripristino viene dallo stato di arrivo, come per le azioni di stato.
PAROLA_STATO = {nuovo: parola for nuovo, parola in ts.AZIONI_STATO.values()}
# Il motivo con cui l'Annulla di un aggiungi scarta il todo appena scritto.
MOTIVO_TOLTO = "annullato dalla pagina"


class ErroreRichiesta(Exception):
    """Una richiesta da rifiutare: codice HTTP e testo in italiano per la persona."""

    def __init__(self, codice: int, testo: str, **altro):
        super().__init__(testo)
        self.codice = codice
        self.testo = testo
        self.altro = altro


class Stato:
    """Quello che il server sa: chiave, porta, progetto di partenza, ora dell'ultima richiesta."""

    def __init__(self, token: str, progetto: str, inattivo: float):
        self.token = token
        self.progetto = progetto
        self.inattivo = inattivo
        self.porta = 0
        self.ultima = time.monotonic()
        self.motivo = ""
        self.server = None
        # Una scrittura alla volta: l'immagine «prima» per Annulla e la scrittura restano coerenti.
        self.scrittura = threading.Lock()

    def spegni(self, motivo: str) -> None:
        """`motivo` è la frase che il terminale stampa all'uscita."""
        if not self.motivo:
            self.motivo = motivo
        threading.Thread(target=self.server.shutdown, daemon=True).start()


def lettura() -> dict:
    todo, avvisi = ts.carica()
    return {"vista": ts.vista(todo, avvisi, tutti=True), "progetti": ts.progetti(todo)}


def _testo(corpo: dict, chiave: str):
    valore = corpo.get(chiave)
    if valore is not None and not isinstance(valore, str):
        raise ErroreRichiesta(400, f"il campo {chiave} deve essere testo")
    return valore


def controlla_corpo(corpo) -> dict:
    """I tipi del corpo di /api/azione. Un valore che non è testo non arriva mai al store."""
    if not isinstance(corpo, dict):
        raise ErroreRichiesta(400, "il corpo della richiesta deve essere un oggetto JSON")
    azione = _testo(corpo, "azione")
    if not azione:
        raise ErroreRichiesta(400, "manca l'azione")
    if azione not in AZIONI:
        raise ErroreRichiesta(400, f"azione «{azione}» sconosciuta. Azioni ammesse: {', '.join(AZIONI)}")
    numero = corpo.get("id")
    if numero is not None and (isinstance(numero, bool) or not isinstance(numero, (int, str))):
        raise ErroreRichiesta(400, "il campo id deve essere un numero o testo")
    campi = corpo.get("campi")
    if campi is None:
        campi = {}
    if not isinstance(campi, dict):
        raise ErroreRichiesta(400, "il campo campi deve essere un oggetto")
    for chiave, valore in campi.items():
        if not isinstance(valore, str):
            raise ErroreRichiesta(400, f"il campo {chiave} deve essere testo")
    annullo = corpo.get("annullo", False)
    if not isinstance(annullo, bool):
        raise ErroreRichiesta(400, "il campo annullo deve essere vero o falso")
    return {"azione": azione, "id": numero, "campi": campi, "annullo": annullo,
            "motivo": _testo(corpo, "motivo") or "", "testo": _testo(corpo, "testo"),
            "stato": _testo(corpo, "stato"), "titolo_atteso": _testo(corpo, "titolo_atteso")}


def esegui(stato: Stato, richiesta: dict) -> dict:
    """Una azione della pagina, con le funzioni del store. Torna messaggio, annulla e vista nuova."""
    azione, numero = richiesta["azione"], richiesta["id"]
    with stato.scrittura:
        todo, _ = ts.carica()
        prima = None
        if azione != "aggiungi":
            if numero is None or numero == "":
                raise ErroreRichiesta(400, "manca il numero del todo")
            prima = dict(ts.per_id(todo, numero))
            atteso = richiesta["titolo_atteso"]
            if atteso is not None and atteso != prima["titolo"]:
                # Un merge può aver rinumerato i todo: il numero non indica più lo stesso todo.
                raise ErroreRichiesta(409, f"Il todo #{prima['id']} è cambiato da quando hai aperto la pagina: "
                                           "ricarico la lista.", **lettura())
        annulla = None

        if azione == "aggiungi":
            campi = dict(richiesta["campi"])
            if not campi.get("progetto", "").strip():
                campi["progetto"] = "generale"
            t = ts.aggiungi(campi)
            messaggio = "Aggiunto"
            annulla = {"azione": "ripristina", "id": t["id"], "titolo_atteso": t["titolo"],
                       "stato": "scartato", "motivo": MOTIVO_TOLTO}

        elif azione == "modifica":
            t = ts.registra(numero, "modifica", dict(richiesta["campi"], annullo=richiesta["annullo"]))
            cambiati = {k: prima[k] for k in ts.CAMPI if k in richiesta["campi"] and t[k] != prima[k]}
            messaggio = "Modificato"
            if cambiati and not richiesta["annullo"]:
                annulla = {"azione": "modifica", "id": t["id"], "titolo_atteso": t["titolo"],
                           "campi": cambiati, "annullo": True}

        elif azione in ts.AZIONI_STATO:
            nuovo, messaggio = ts.AZIONI_STATO[azione]
            t = ts.registra(numero, "stato", {"stato": nuovo, "motivo": richiesta["motivo"],
                                               "annullo": richiesta["annullo"]})
            if not richiesta["annullo"]:
                annulla = {"azione": "ripristina", "id": t["id"], "titolo_atteso": t["titolo"],
                           "stato": prima["stato"], "motivo": prima["motivo"]}

        elif azione == "ripristina":
            if not richiesta["stato"]:
                raise ErroreRichiesta(400, "manca lo stato da ripristinare")
            t = ts.ripristina(numero, richiesta["stato"], richiesta["motivo"])
            if t["stato"] == "scartato" and t["motivo"] == MOTIVO_TOLTO:
                messaggio = "Tolto"
            else:
                messaggio = PAROLA_STATO.get(t["stato"], "Ripristinato")

        elif azione == "nota":
            t = ts.registra(numero, "nota", {"testo": richiesta["testo"] or ""})
            messaggio = "Nota aggiunta a"

        else:  # deciso
            t = ts.deciso(numero, richiesta["testo"] or "")
            messaggio = "Deciso"
            annulla = {"azione": "modifica", "id": t["id"], "titolo_atteso": t["titolo"],
                       "campi": {"chi": prima["chi"]}, "annullo": True}

        risposta = {"messaggio": f"{messaggio} #{t['id']}: {t['titolo']}", "id": t["id"], "annulla": annulla}
        risposta.update(lettura())
        return risposta


def crea_gestore(stato: Stato):
    class Gestore(BaseHTTPRequestHandler):
        server_version = "Arturo"
        sys_version = ""

        def log_message(self, *_):
            """Niente righe «GET /…» nel terminale: le richieste della pagina non interessano a nessuno."""

        # --- risposte -------------------------------------------------------

        def _rispondi(self, codice: int, corpo: bytes, tipo: str) -> None:
            self.send_response(codice)
            self.send_header("Content-Type", tipo)
            self.send_header("Content-Length", str(len(corpo)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Referrer-Policy", "no-referrer")
            self.send_header("X-Frame-Options", "DENY")
            self.send_header("Content-Security-Policy", CSP)
            self.end_headers()
            if self.command != "HEAD":
                self.wfile.write(corpo)

        def _json(self, codice: int, dati: dict) -> None:
            self._rispondi(codice, json.dumps(dati, ensure_ascii=False).encode("utf-8"),
                           "application/json; charset=utf-8")

        def send_error(self, code, message=None, explain=None):
            """Anche gli errori della libreria (riga malformata, metodo ignoto) escono in italiano."""
            self.close_connection = True
            testo = TESTI_ERRORE.get(code, TESTI_ERRORE[400])
            try:
                self._json(code, {"errore": testo})
            except OSError:
                pass

        # --- controlli ------------------------------------------------------

        def _controlla_origine(self) -> None:
            ammessi = (f"127.0.0.1:{stato.porta}", f"localhost:{stato.porta}")
            if self.headers.get("Host", "") not in ammessi:
                # Un nome diverso vuol dire un altro sito che punta a 127.0.0.1 (DNS rebinding).
                raise ErroreRichiesta(403, TESTI_ERRORE[403])
            origine = self.headers.get("Origin")
            if origine is not None and origine not in tuple("http://" + a for a in ammessi):
                raise ErroreRichiesta(403, TESTI_ERRORE[403])

        def _controlla_chiave(self, chiave) -> None:
            if not chiave or not hmac.compare_digest(chiave.encode("utf-8"), stato.token.encode("utf-8")):
                raise ErroreRichiesta(403, TESTI_ERRORE[403])

        def _corpo(self) -> dict:
            if not self.headers.get("Content-Type", "").lower().startswith("application/json"):
                raise ErroreRichiesta(415, TESTI_ERRORE[415])
            lunghezza = self.headers.get("Content-Length")
            if lunghezza is None:
                raise ErroreRichiesta(400, TESTI_ERRORE[411])
            try:
                n = int(lunghezza)
            except ValueError:
                raise ErroreRichiesta(400, "lunghezza del corpo non valida")
            if n < 0:
                raise ErroreRichiesta(400, "lunghezza del corpo non valida")
            if n > MASSIMO:
                # Il corpo si legge e si butta: chiudere con dati non letti fa perdere la risposta.
                self.close_connection = True
                if n <= 64 * MASSIMO:
                    resto = n
                    while resto > 0:
                        pezzo = self.rfile.read(min(resto, 65536))
                        if not pezzo:
                            break
                        resto -= len(pezzo)
                raise ErroreRichiesta(413, TESTI_ERRORE[413])
            grezzo = self.rfile.read(n)
            try:
                return json.loads(grezzo.decode("utf-8"))
            except (UnicodeDecodeError, ValueError):
                raise ErroreRichiesta(400, "il corpo della richiesta non è JSON valido")

        # --- metodi ---------------------------------------------------------

        def _gestisci(self, funzione) -> None:
            stato.ultima = time.monotonic()
            try:
                self._controlla_origine()
                funzione(urlsplit(self.path))
            except ErroreRichiesta as e:
                if e.codice == 403 and self.command == "GET" and urlsplit(self.path).path == "/":
                    self._rispondi(403, PAGINA_NEGATA.encode("utf-8"), "text/html; charset=utf-8")
                else:
                    self._json(e.codice, dict({"errore": e.testo}, **e.altro))
            except ts.ErroreTodo as e:
                self._json(400, {"errore": str(e)})
            except (BrokenPipeError, ConnectionResetError):
                pass
            except Exception:  # noqa: BLE001 - la pagina riceve un testo, il terminale il dettaglio
                traceback.print_exc(file=sys.stderr)
                try:
                    self._json(500, {"errore": TESTI_ERRORE[500]})
                except OSError:
                    pass

        def do_GET(self):
            self._gestisci(self._get)

        def do_POST(self):
            self._gestisci(self._post)

        def _non_ammesso(self):
            stato.ultima = time.monotonic()
            self.send_error(405)

        do_HEAD = do_PUT = do_DELETE = do_PATCH = do_OPTIONS = do_TRACE = do_CONNECT = _non_ammesso

        def _get(self, url) -> None:
            if url.path == "/":
                self._controlla_chiave((parse_qs(url.query).get("t") or [""])[0])
                pagina = (CARTELLA / "index.html").read_text(encoding="utf-8").replace("{{TOKEN}}", stato.token)
                self._rispondi(200, pagina.encode("utf-8"), "text/html; charset=utf-8")
            elif url.path.startswith("/static/"):
                voce = STATICI.get(url.path[len("/static/"):])
                if voce is None:
                    raise ErroreRichiesta(404, TESTI_ERRORE[404])
                self._rispondi(200, (CARTELLA / voce[0]).read_bytes(), voce[1])
            elif url.path == "/api/vista":
                self._controlla_chiave(self.headers.get("X-Arturo-Token"))
                self._json(200, dict(lettura(), partenza=stato.progetto))
            else:
                raise ErroreRichiesta(404, TESTI_ERRORE[404])

        def _post(self, url) -> None:
            if url.path not in ("/api/azione", "/api/spegni"):
                raise ErroreRichiesta(404, TESTI_ERRORE[404])
            self._controlla_chiave(self.headers.get("X-Arturo-Token"))
            corpo = self._corpo()
            if url.path == "/api/spegni":
                self._json(200, {"messaggio": "Arturo web si spegne. Puoi chiudere questa scheda."})
                stato.spegni("Arturo web si è fermato dalla pagina.")
                return
            self._json(200, esegui(stato, controlla_corpo(corpo)))

    return Gestore


AIUTO = """arturo web apre la pagina dei todo nel browser, solo su questo computer.
Opzioni: --porta N sceglie la porta (da 0 a 65535, 0 la sceglie il sistema), --non-aprire stampa il link senza aprire il browser."""

OPZIONI = "Le opzioni sono --porta N e --non-aprire. Vedi: arturo web aiuto"


def porta(valore: str) -> int:
    """Il numero di --porta. Un valore sbagliato arriva a Parser.error con una frase già italiana."""
    try:
        n = int(valore)
    except ValueError:
        raise argparse.ArgumentTypeError(f"--porta vuole un numero da 0 a 65535, non «{valore}».")
    if not 0 <= n <= 65535:
        raise argparse.ArgumentTypeError(f"--porta vuole un numero da 0 a 65535, non {n}.")
    return n


class Parser(argparse.ArgumentParser):
    """Gli errori delle opzioni in italiano: il testo inglese di argparse non arriva alla persona."""

    def error(self, message):
        if "--host" in message:
            testo = "l'opzione --host non esiste: la pagina ascolta solo su 127.0.0.1, cioè solo su questo computer."
        elif "--porta vuole" in message:
            testo = message.split(": ", 1)[-1] if message.startswith("argument") else message
        elif "--porta" in message:
            testo = f"--porta vuole un numero da 0 a 65535. {OPZIONI}"
        else:
            sconosciute = message.split(":", 1)[-1].strip() if "unrecognized" in message else ""
            testo = (f"opzione sconosciuta «{sconosciute}». " if sconosciute else "opzione non valida. ") + OPZIONI
        print(f"arturo web: {testo}", file=sys.stderr)
        raise SystemExit(2)


def parser() -> argparse.ArgumentParser:
    p = Parser(prog="arturo web", add_help=False)
    p.add_argument("--porta", type=porta, default=0)
    p.add_argument("--non-aprire", action="store_true")
    return p


def inattivo_da(valore) -> float:
    """ARTURO_WEB_INATTIVO in secondi, almeno 1. Un valore vuoto, non numerico o non finito vale 30 minuti."""
    try:
        secondi = float(valore or INATTIVO)
    except ValueError:
        return float(INATTIVO)
    return max(secondi, 1.0) if math.isfinite(secondi) else float(INATTIVO)


def perche_porta(e: OSError) -> str:
    """Il motivo di un bind fallito, in italiano. strerror arriva dal sistema, spesso in inglese."""
    if e.errno in (errno.EADDRINUSE, getattr(errno, "WSAEADDRINUSE", -1)):
        return "la porta è già usata da un altro programma"
    if e.errno in (errno.EACCES, getattr(errno, "WSAEACCES", -1)):
        return "il sistema non permette di usare questa porta"
    return "il sistema rifiuta la porta"


def durata(secondi: float) -> str:
    if secondi >= 60:
        minuti = int(round(secondi / 60))
        return "un minuto" if minuti == 1 else f"{minuti} minuti"
    return "un secondo" if int(secondi) == 1 else f"{int(secondi)} secondi"


def sorveglia(stato: Stato) -> None:
    """Spegne il server quando nessuna richiesta arriva per `inattivo` secondi."""
    passo = max(0.1, min(1.0, stato.inattivo / 4))
    while not stato.motivo:
        time.sleep(passo)
        if time.monotonic() - stato.ultima > stato.inattivo:
            stato.spegni(f"Arturo web si è fermato: {durata(stato.inattivo)} senza la pagina aperta.")
            return


def main(argv: list, progetto: str = "generale") -> int:
    for flusso in (sys.stdout, sys.stderr):
        try:
            flusso.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass
    # L'aiuto vale in ogni posizione: «arturo web --non-aprire --help» stampa l'aiuto, non un errore.
    if any(a in ("aiuto", "-h", "--help") for a in argv):
        print(AIUTO)
        return 0
    args = parser().parse_args(argv)
    stato = Stato(secrets.token_urlsafe(32), progetto, inattivo_da(os.environ.get("ARTURO_WEB_INATTIVO")))
    try:
        server = ThreadingHTTPServer((HOST, args.porta), crea_gestore(stato))
    except (OSError, OverflowError) as e:
        motivo = perche_porta(e) if isinstance(e, OSError) else "il numero di porta non è valido"
        print(f"arturo web: non riesco ad aprire la porta {args.porta} su {HOST}: {motivo}. "
              "Riprova senza --porta: il sistema ne sceglie una libera.", file=sys.stderr)
        return 1
    server.daemon_threads = True
    stato.server = server
    indirizzo, stato.porta = server.server_address[0], server.server_address[1]
    url = f"http://{HOST}:{stato.porta}/?t={stato.token}"
    print(f"Arturo web: {url}", flush=True)
    print(f"In ascolto su {indirizzo}:{stato.porta}, solo su questo computer. Si ferma dopo "
          f"{durata(stato.inattivo)} senza la pagina aperta, con il bottone «Spegni la pagina» o con Ctrl+C.",
          flush=True)
    if not args.non_aprire:
        try:
            webbrowser.open(url)
        except Exception:  # noqa: BLE001 - senza browser il link resta stampato
            pass
    threading.Thread(target=sorveglia, args=(stato,), daemon=True).start()
    try:
        server.serve_forever(poll_interval=0.25)
    except KeyboardInterrupt:
        print("Arturo web chiuso.", flush=True)
        return 0
    finally:
        server.server_close()
    print(stato.motivo, flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
