"""arturo segnala: porta a chi mantiene Arturo un problema, un'idea o una richiesta di integrazione.

La conversazione la fa /segnala (commands/segnala.md): capisce il tipo, scrive la bozza con la
persona e toglie a giudizio nomi, clienti e contenuti di lavoro. Questo modulo fa la parte che
deve essere sempre uguale:

- prepara: toglie i percorsi della home, ferma la bozza se contiene un segreto, mostra l'anteprima;
- invia: l'unico passo verso fuori, lanciato solo dopo il sì della persona. Quattro canali:
  arturo (il default: la segnalazione va al server di Arturo, che la manda per email a chi lo
  mantiene; se la rete non risponde resta in attesa e parte con il prossimo invio della telemetria),
  gh (issue pubblica con la CLI di GitHub), web (la pagina della issue già compilata, la persona
  preme Invia), email (il testo negli appunti, la persona lo incolla e lo invia dal suo programma
  di posta). Nessun canale apre un mailto:, che comms-guard nega di proposito;
- chiedi, basta, riprendi: la cadenza della domanda di /fine e il modo di spegnerla.

Lo stato (ultima domanda, ultima segnalazione, canale scelto, pausa) sta in
~/.claude/session-env/segnala.json. Una copia di ogni segnalazione resta in
~/.claude/data/segnalazioni/. Il modulo non raccoglie niente da solo: ogni segnalazione parte
da una persona che ha visto il testo e ha detto sì.

Solo libreria standard, Python 3.8 o successivo.
"""
from __future__ import annotations

import datetime as dt
import importlib.util
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.parse
from pathlib import Path

sys.path.insert(0, str(Path(os.path.realpath(__file__)).parent))
import todo_store as ts  # noqa: E402
import telemetria  # noqa: E402

REPO = "stellakamikaze/arturo"
EMAIL = "federico@stellakamikaze.org"
TIPI = ("problema", "proposta", "integrazione")
CANALI = ("arturo", "gh", "web", "email")
VERSIONE_STATO = 2
GIORNI_TRA_DOMANDE = 7
# GitHub rifiuta URL troppo lunghi: oltre questa soglia la pagina si apre col solo titolo.
URL_MASSIMO = 6000
# Non è un segreto: lo scanner la segnala, la segnalazione può contenerla.
NON_SEGRETI = {"Stripe Publishable Key"}
FIRMA = "\n\n---\n_Inviata con `/segnala` di Arturo._\n"

AIUTO = f"""arturo segnala: un problema, un'idea o un'integrazione da proporre a chi mantiene Arturo.

Di solito lo usa /segnala dentro Claude Code. Comandi:

  info                                   versione di Arturo e di Claude Code, sistema, gh collegato
  prepara --tipo T --titolo "…" --file BOZZA
                                         pulisce la bozza e mostra l'anteprima (T: {", ".join(TIPI)})
  invia --canale C --file PRONTA         la manda (C: arturo = diretta a chi mantiene Arturo, il default;
                                         gh = issue pubblica; web = pagina della issue compilata;
                                         email = testo negli appunti per {EMAIL})
  canale [arturo|gh|web|email]           il canale ricordato, o lo ricorda
  chiedi                                 /fine può fare la domanda della settimana? (0 sì, 3 no)
  basta                                  niente inviti a segnalare finché non dici riprendi
  riprendi                               gli inviti ripartono

Lo stato resta su questo computer: ~/.claude/session-env/segnala.json.
Le copie delle segnalazioni: ~/.claude/data/segnalazioni/."""


# --- stato -------------------------------------------------------------------

def file_stato() -> Path:
    return Path.home() / ".claude" / "session-env" / "segnala.json"


def cartella_copie() -> Path:
    return Path.home() / ".claude" / "data" / "segnalazioni"


def _data(valore):
    try:
        return dt.date.fromisoformat(valore) if isinstance(valore, str) else None
    except ValueError:
        return None


def leggi_stato() -> dict:
    """Un file assente o rotto vale {}: la cadenza riparte, non si ferma niente."""
    try:
        grezzo = json.loads(file_stato().read_text(encoding="utf-8"))
    except (OSError, ValueError, UnicodeDecodeError):
        return {}
    if not isinstance(grezzo, dict):
        return {}
    stato = {}
    for chiave in ("domanda", "inviata"):
        if _data(grezzo.get(chiave)):
            stato[chiave] = grezzo[chiave]
    # Lo stato senza versione viene dalla prima /segnala del 13/10, che non aveva il canale arturo:
    # un canale manuale ricordato allora non era una scelta contro il canale diretto, e decade.
    if grezzo.get("canale") in CANALI and (grezzo.get("versione") == VERSIONE_STATO or grezzo["canale"] == "arturo"):
        stato["canale"] = grezzo["canale"]
    if grezzo.get("pausa") == "sempre":
        stato["pausa"] = "sempre"
    return stato


def cambia_stato(cambia) -> dict:
    with ts.Lucchetto(file_stato()):
        stato = leggi_stato()
        cambia(stato)
        # La chiave "pausa" resta scritta anche quando è spenta: session-start la cerca col grep.
        pulito = {"versione": VERSIONE_STATO, "domanda": stato.get("domanda"), "inviata": stato.get("inviata"),
                  "canale": stato.get("canale"), "pausa": stato.get("pausa")}
        ts.scrivi_json_atomico(file_stato(), pulito)
    return pulito


# --- pulizia ------------------------------------------------------------------

def _pattern_segreti() -> list:
    """I pattern di hooks/credential-leak-scanner.py: una sola lista, quella della guardia."""
    scanner = Path(os.path.realpath(__file__)).parent.parent / "hooks" / "credential-leak-scanner.py"
    spec = importlib.util.spec_from_file_location("credential_leak_scanner", str(scanner))
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return [(re.compile(p), nome) for p, nome in modulo.CREDENTIAL_PATTERNS if nome not in NON_SEGRETI]


def segreti_trovati(testo: str) -> list:
    return sorted({nome for regex, nome in _pattern_segreti() if regex.search(testo)})


def togli_home(testo: str) -> str:
    """Ogni cartella personale diventa ~: la propria e quelle di altri che compaiono in un log."""
    casa = str(Path.home())
    for forma in {casa, os.path.realpath(casa)}:
        if len(forma) > 1:
            testo = testo.replace(forma, "~")
    testo = re.sub(r"/(?:Users|home)/[^/\s\"'`]+", "~", testo)
    return re.sub(r"(?i)[A-Z]:\\Users\\[^\\\s\"'`]+", "~", testo)


def titolo_con_tipo(tipo: str, titolo: str) -> str:
    titolo = " ".join(titolo.split())
    titolo = re.sub(r"^\[(?:problema|proposta|integrazione)\]\s*", "", titolo, flags=re.I)
    return f"[{tipo}] {titolo}"


# --- canali --------------------------------------------------------------------

def _apri(url: str) -> bool:
    try:
        if sys.platform == "darwin":
            return subprocess.run(["open", url], timeout=15).returncode == 0
        if os.name == "nt":
            os.startfile(url)  # noqa: S606 - apre il browser predefinito
            return True
        return subprocess.run(["xdg-open", url], timeout=15).returncode == 0
    except (OSError, subprocess.SubprocessError):
        return False


def _copia(testo: str) -> bool:
    if sys.platform == "darwin":
        comandi = [["pbcopy"]]
    elif os.name == "nt":
        comandi = [["clip"]]
    else:
        comandi = [["wl-copy"], ["xclip", "-selection", "clipboard"]]
    for comando in comandi:
        if not shutil.which(comando[0]):
            continue
        try:
            if subprocess.run(comando, input=testo, text=True, timeout=10).returncode == 0:
                return True
        except (OSError, subprocess.SubprocessError):
            continue
    return False


def _url_issue(tipo: str, titolo: str, testo: str) -> tuple:
    """Torna (url, testo_dentro). Oltre la soglia l'URL porta il solo titolo.
    GitHub applica l'etichetta solo a chi ha accesso al repo: per gli altri il tipo resta nel titolo."""
    base = f"https://github.com/{REPO}/issues/new?"
    pieno = base + urllib.parse.urlencode({"title": titolo, "labels": tipo, "body": testo})
    if len(pieno) <= URL_MASSIMO:
        return pieno, True
    return base + urllib.parse.urlencode({"title": titolo, "labels": tipo}), False


def invia_gh(titolo: str, testo: str):
    if not shutil.which("gh"):
        return None, "gh non è installato: usa il canale web o email"
    fd, corpo = tempfile.mkstemp(prefix="segnala.", suffix=".md")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(testo)
        esito = subprocess.run(["gh", "issue", "create", "--repo", REPO, "--title", titolo, "--body-file", corpo],
                               capture_output=True, text=True, timeout=60)
    except (OSError, subprocess.SubprocessError) as errore:
        return None, f"gh non è partito: {errore}"
    finally:
        try:
            os.unlink(corpo)
        except OSError:
            pass
    if esito.returncode != 0:
        return None, (esito.stderr or esito.stdout).strip() or f"gh è uscito con {esito.returncode}"
    return esito.stdout.strip().splitlines()[-1] if esito.stdout.strip() else "", None


def info() -> str:
    def esegui(comando: list) -> str:
        try:
            r = subprocess.run(comando, capture_output=True, text=True, timeout=10)
            return r.stdout.strip() if r.returncode == 0 else ""
        except (OSError, subprocess.SubprocessError):
            return ""
    versione = esegui(["git", "-C", str(Path.home() / ".claude"), "describe", "--tags", "--abbrev=0", "--match", "v*"]) or "sconosciuta"
    claude = esegui(["claude", "--version"]) or "sconosciuta"
    if not shutil.which("gh"):
        gh = "non installato"
    else:
        try:
            gh = "collegato" if subprocess.run(["gh", "auth", "status"], capture_output=True,
                                               timeout=10).returncode == 0 else "non collegato"
        except (OSError, subprocess.SubprocessError):
            gh = "non collegato"
    canale = leggi_stato().get("canale", "non scelto")
    return (f"Arturo: {versione}\nClaude Code: {claude}\nSistema: {platform.system()} {platform.release()}\n"
            f"gh: {gh}\nCanale ricordato: {canale}")


# --- comandi -------------------------------------------------------------------

def _opzioni(resto: list, ammesse: tuple) -> dict:
    valori, i = {}, 0
    while i < len(resto):
        chiave = resto[i]
        if "=" in chiave and chiave.split("=", 1)[0] in ammesse:
            chiave, valore = chiave.split("=", 1)
            valori[chiave] = valore
            i += 1
            continue
        if chiave not in ammesse or i + 1 >= len(resto):
            raise ValueError(f'opzione sconosciuta o senza valore: "{chiave}"')
        valori[chiave] = resto[i + 1]
        i += 2
    return valori


def prepara(opz: dict) -> int:
    tipo, titolo, bozza = opz.get("--tipo"), (opz.get("--titolo") or "").strip(), opz.get("--file")
    if tipo not in TIPI or not titolo or not bozza:
        print(f"Errore: servono --tipo ({', '.join(TIPI)}), --titolo e --file", file=sys.stderr)
        return 2
    sorgente = Path(bozza)
    testo = togli_home(sorgente.read_text(encoding="utf-8")).strip()
    titolo = togli_home(titolo_con_tipo(tipo, titolo))
    trovati = segreti_trovati(titolo + "\n" + testo)
    if trovati:
        print("Fermo: la bozza contiene qualcosa che sembra un segreto (" + ", ".join(trovati) + "). "
              "Toglilo dalla bozza e rilancia prepara. Niente è stato preparato.", file=sys.stderr)
        return 3
    if not testo:
        print("Errore: la bozza è vuota", file=sys.stderr)
        return 2
    pronta = sorgente.with_name(sorgente.name + ".pronta.json")
    ts.scrivi_json_atomico(pronta, {"tipo": tipo, "titolo": titolo, "testo": testo + FIRMA})
    print(f"PRONTA: {pronta}\n")
    print(f"Titolo: {titolo}\n")
    print(testo + FIRMA)
    print(f"Dove può andare:\n  arturo (di solito): arriva solo a chi mantiene Arturo, senza altri passi\n"
          f"  gh o web: issue pubblica su github.com/{REPO}, la vede chiunque\n"
          f"  email: testo negli appunti da mandare a {EMAIL}")
    return 0


def invia(opz: dict) -> int:
    canale, file = opz.get("--canale"), opz.get("--file")
    if canale not in CANALI or not file:
        print(f"Errore: servono --canale ({', '.join(CANALI)}) e --file", file=sys.stderr)
        return 2
    try:
        dati = json.loads(Path(file).read_text(encoding="utf-8"))
        tipo, titolo, testo = dati["tipo"], dati["titolo"], dati["testo"]
    except (OSError, ValueError, KeyError, TypeError):
        print("Errore: il file non è una segnalazione preparata. Lancia prima prepara.", file=sys.stderr)
        return 2
    # Il file può essere cambiato dopo prepara: il controllo si ripete qui, prima di uscire.
    trovati = segreti_trovati(titolo + "\n" + testo)
    if trovati or tipo not in TIPI:
        print("Fermo: " + (f"il testo contiene qualcosa che sembra un segreto ({', '.join(trovati)})"
                           if trovati else "tipo sconosciuto") + ". Niente è partito.", file=sys.stderr)
        return 3

    esito = ""
    if canale == "arturo":
        dati_server = {"tipo": tipo, "titolo": titolo, "testo": testo, "versione": telemetria.versione(),
                       "sistema": telemetria.sistema()}
        # L'id lega la segnalazione agli eventi d'uso solo se la telemetria è accesa.
        if not telemetria.perche_spenta():
            dati_server["installazione"] = telemetria.installazione()
        status, risposta = telemetria.posta_json("/v1/segnalazioni", dati_server, timeout=10)
        if 200 <= status < 300:
            esito = "arrivata a chi mantiene Arturo"
            # Il numero è quello che torna nelle /novita quando esce la correzione: chi segnala lo deve
            # sapere (Computer Club, 27/10/2026: "quando faccio il segnale cosa succede?").
            numero = risposta.get("numero")
            if isinstance(numero, int) and not isinstance(numero, bool) and numero > 0:
                esito += f": è la segnalazione n. {numero}"
            # Il server risponde: partono anche quelle rimaste in attesa (Liliana, 27/10/2026).
            partite = telemetria.invia_segnalazioni_in_attesa()
            if partite:
                esito += f", con {partite} rimast{'a' if partite == 1 else 'e'} in attesa"
        elif status in (400, 413):
            print(f"Non inviata: il server l'ha rifiutata ({status}). Prova il canale web o email.", file=sys.stderr)
            return 1
        else:
            attesa = telemetria.cartella_attesa()
            attesa.mkdir(parents=True, exist_ok=True)
            ts.scrivi_json_atomico(attesa / f"{dt.datetime.now():%Y-%m-%d_%H%M%S}_{tipo}.attesa.json", dati_server)
            # Il codice dice a chi mantiene Arturo dove guardare: rete o server (segnalazione di Liliana, 27/10/2026).
            motivo = f"risposta {status}" if status else "nessuna risposta dalla rete"
            print(f"Il server ora non risponde ({motivo}): la segnalazione è salvata e parte da sola "
                  "alla prossima sessione.")
            esito = "in attesa: parte da sola appena il server risponde"
    elif canale == "gh":
        link, errore = invia_gh(titolo, testo)
        if errore:
            print(f"Non inviata: {errore}", file=sys.stderr)
            return 1
        esito = f"issue aperta: {link}"
    elif canale == "web":
        url, testo_dentro = _url_issue(tipo, titolo, testo)
        copiato = True if testo_dentro else _copia(testo)
        if not _apri(url):
            print(f"Non riesco ad aprire il browser. Apri tu questo indirizzo:\n{url}")
        if not testo_dentro:
            print("Il testo è lungo: nella pagina c'è il solo titolo. "
                  + ("Il testo è negli appunti, incollalo nella casella." if copiato
                     else "Copia il testo qui sotto nella casella.\n\n" + testo))
        esito = "pagina della issue aperta: la persona controlla e preme Invia"
    else:
        oggetto = f"[Arturo] {titolo}"
        if _copia(testo):
            print(f"Il testo è negli appunti.\nA: {EMAIL}\nOggetto: {oggetto}\n"
                  "Apri il tuo programma di posta, incolla il testo e invia.")
        else:
            print(f"Non riesco a copiare negli appunti. Manda questa email:\nA: {EMAIL}\nOggetto: {oggetto}\n\n{testo}")
        esito = f"email pronta per {EMAIL}: la persona la invia"

    adesso = dt.datetime.now()
    cartella = cartella_copie()
    cartella.mkdir(parents=True, exist_ok=True)
    copia = cartella / f"{adesso:%Y-%m-%d_%H%M%S}_{tipo}.md"
    copia.write_text(f"# {titolo}\n\nData: {adesso:%Y-%m-%d %H:%M}\nCanale: {canale}\nEsito: {esito}\n\n{testo}",
                     encoding="utf-8")
    oggi = ts.oggi().isoformat()
    cambia_stato(lambda s: s.update({"inviata": oggi, "canale": canale}))
    telemetria.registra("segnalazione", tipo)
    print(f"\nFatto: {esito}.\nCopia: {copia}")
    return 0


def chiedi() -> int:
    stato, oggi = leggi_stato(), ts.oggi()
    if stato.get("pausa") == "sempre":
        print("Niente domanda: la persona ha detto basta (arturo segnala riprendi per riaccendere).")
        return 3
    for chiave, cosa in (("domanda", "domanda fatta"), ("inviata", "segnalazione inviata")):
        giorno = _data(stato.get(chiave))
        if giorno and (oggi - giorno).days < GIORNI_TRA_DOMANDE:
            prossima = giorno + dt.timedelta(days=GIORNI_TRA_DOMANDE)
            print(f"Niente domanda: {cosa} il {giorno.isoformat()}, la prossima dal {prossima.isoformat()}.")
            return 3
    cambia_stato(lambda s: s.__setitem__("domanda", oggi.isoformat()))
    print("Puoi fare la domanda della settimana, una sola.")
    return 0


def main(argv: list) -> int:
    if not argv or argv[0] in ("-h", "--help", "aiuto", "help"):
        print(AIUTO)
        return 0
    comando, resto = argv[0], argv[1:]
    try:
        if comando == "info" and not resto:
            print(info())
            return 0
        if comando == "prepara":
            return prepara(_opzioni(resto, ("--tipo", "--titolo", "--file")))
        if comando == "invia":
            return invia(_opzioni(resto, ("--canale", "--file")))
        if comando == "chiedi" and not resto:
            return chiedi()
        if comando == "canale" and len(resto) <= 1:
            if not resto:
                canale = leggi_stato().get("canale")
                print(canale or "nessuno")
                return 0 if canale else 3
            if resto[0] not in CANALI:
                raise ValueError(f"canale sconosciuto: \"{resto[0]}\" ({', '.join(CANALI)})")
            cambia_stato(lambda s: s.__setitem__("canale", resto[0]))
            print(f"Canale ricordato: {resto[0]}")
            return 0
        if comando == "basta" and not resto:
            cambia_stato(lambda s: s.__setitem__("pausa", "sempre"))
            print("Va bene. Niente inviti a segnalare finché non dici: arturo segnala riprendi\n"
                  "/segnala resta lì quando ti serve.")
            return 0
        if comando == "riprendi" and not resto:
            cambia_stato(lambda s: s.__setitem__("pausa", None))
            print("Gli inviti a segnalare ripartono.")
            return 0
    except ValueError as errore:
        print(f"Errore: {errore}\n\n{AIUTO}", file=sys.stderr)
        return 2
    except OSError as errore:
        print(f"Errore: {errore}", file=sys.stderr)
        return 2
    print(f"Errore: comando sconosciuto: \"{' '.join(argv)}\"\n\n{AIUTO}", file=sys.stderr)
    return 2
