"""arturo segnala: porta a chi mantiene Arturo un problema, un'idea o una richiesta di integrazione.

La conversazione la fa /segnala (commands/segnala.md): capisce il tipo, scrive la bozza con la
persona e toglie a giudizio nomi, clienti e contenuti di lavoro. Questo modulo fa la parte che
deve essere sempre uguale:

- prepara: toglie cartelle personali, email, indirizzi web esterni, indirizzi IP, nomi di computer della rete e
  nomi di documenti (redigi, e l'anteprima dice cosa ha tolto), ferma la bozza se contiene un segreto, mostra
  l'anteprima col pacchetto tecnico a caselle;
- invia: l'unico passo verso fuori, lanciato solo dopo il sì della persona. Quattro canali:
  arturo (il default: la segnalazione va al server di Arturo, che la manda per email a chi lo
  mantiene; se la rete non risponde resta in attesa e parte con il prossimo invio della telemetria),
  gh (issue pubblica con la CLI di GitHub), web (la pagina della issue già compilata, la persona
  preme Invia), email (il testo negli appunti, la persona lo incolla e lo invia dal suo programma
  di posta). Nessun canale apre un mailto:, che comms-guard nega di proposito;
- stato: a che punto sono le segnalazioni della persona (in attesa, arrivate col numero, corrette
  con la voce di NOVITA.md che le cita) e, col codice della ricevuta, lo stato e la risposta di chi
  mantiene Arturo;
- seguito, ritira: un'aggiunta a una segnalazione partita, o il suo ritiro, col codice della ricevuta;
- precedenti: le segnalazioni già partite col loro "In breve", che /segnala confronta con la bozza;
- chiedi, basta, riprendi: la cadenza della domanda di /fine e il modo di spegnerla.

Lo stato (ultima domanda, ultima segnalazione, canale scelto, pausa) sta in
~/.claude/session-env/segnala.json. I codici delle ricevute in ~/.claude/data/segnalazioni/ricevute.json,
leggibile solo dalla persona (lo sportello, 4/11/2026, #3925). Una copia di ogni segnalazione resta in
~/.claude/data/segnalazioni/. Il modulo non raccoglie niente da solo: ogni segnalazione parte
da una persona che ha visto il testo e ha detto sì.

Solo libreria standard, Python 3.8 o successivo.
"""
from __future__ import annotations

import datetime as dt
import hashlib
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
sys.path.append(str(Path(os.path.realpath(__file__)).parent.parent / "hooks"))
from radici import radice_arturo, radice_orsa  # noqa: E402

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
# Lo sportello (4/11/2026, #3925). Le caselle del pacchetto tecnico: (voce, cosa dice l'anteprima, accesa di default).
# Le voci arrivano solo a chi mantiene Arturo, col canale arturo, e il server le svuota dopo 90 giorni. "collega" non
# porta testo: manda l'id dell'installazione, che lega la segnalazione ai dati d'uso. Spenta di default (piano del
# 24/10/2026, decisione 1): il testo legato alla storia d'uso identifica la persona.
VOCI_PACCHETTO = (
    ("ambiente", "ambiente: versioni di Arturo, Claude Code, sistema e Python", True),
    ("banchi", "esito dei controlli delle guardie all'avvio", True),
    ("config", "stato della config: solo i nomi dei guasti", True),
    ("deriva", "file e hook di Arturo cambiati o spenti su questo computer", False),
    ("errore", "il messaggio d'errore intero (con --errore FILE)", False),
    ("collega", "collega la segnalazione ai miei dati d'uso (l'id dell'installazione)", False),
)
VOCE_MASSIMO = 3900
ORIGINI = ("segnala", "avvio", "fine")
# redigi: le categorie che la persona può rimettere con --tieni, col segnaposto e il nome nell'anteprima.
REDAZIONE = {
    "web": ("[indirizzo web]", "indirizzi web"),
    "email": ("[email]", "email"),
    "computer": ("[computer]", "nomi di computer della rete"),
    "ip": ("[indirizzo IP]", "indirizzi IP"),
    "documenti": ("[documento]", "nomi di documenti"),
}
# Gli indirizzi web pubblici che servono a capire il problema: restano.
WEB_PUBBLICI = re.compile(r"^https?://(?:github\.com/stellakamikaze/arturo(?:[/?#]|$)|(?:[a-z0-9-]+\.)*stellakamikaze\.org(?:[/:?#]|$)|"
                          r"(?:docs|code|support)\.(?:claude\.com|anthropic\.com)(?:[/?#]|$)|(?:www\.)?anthropic\.com(?:[/?#]|$)|"
                          r"127\.0\.0\.1|localhost)", re.I)
# Anche ftp, ssh e le cartelle di rete, e gli indirizzi senza schema: www.… e dominio/percorso (review del 7/11/2026,
# finding 103). Un dominio senza schema conta solo con la barra dopo, e mai coi pacchetti del Mac (Arturo.app/Contents).
RE_WEB = re.compile(r"(?:\b(?:https?|s?ftp|ssh|smb|afp|git)://|\bwww\.|(?<![/\w.~@-])(?=(?:[a-z0-9-]+\.)+"
                    r"(?!(?:app|framework|bundle|plugin|kext|appex|xpc|lproj|xcodeproj|git|d)/)[a-z]{2,24}/))"
                    r"[^\s<>\"'`)\]]+", re.I)
RE_EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}")
RE_COMPUTER = re.compile(r"\b[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*\.(?:local|lan|internal|home\.arpa|ts\.net)\b", re.I)
RE_IP = re.compile(r"(?<![\d.])(?:\d{1,3}\.){3}\d{1,3}(?![\d.])")
# Il nome di un documento: anche immagini, audio, video, archivi e testi (finding 103). Le parole con la maiuscola o
# i numeri subito prima, staccati da uno spazio, sono parte del nome ("Contratto Rossi Bianchi 2026.pdf", finding 28).
RE_DOCUMENTI = re.compile(r"(?:\b(?-i:[A-ZÀ-Ý0-9])[^\s/\\\"'`<>|*?:\[\]]* ){0,4}[^\s/\\\"'`<>|*?:\[\]]+\."
                          r"(pdf|docx?|xlsx?|pptx?|key|pages|numbers|odt|ods|odp|rtf|eml|msg|csv|txt|md|"
                          r"png|jpe?g|gif|heic|webp|tiff?|psd|ai|indd|sketch|fig|epub|zip|rar|7z|"
                          r"mp3|mp4|m4a|mov|wav|aiff?)\b", re.I)
# Restano i file di Arturo e di Claude Code: un nome tutto maiuscolo (CLAUDE.md, SKILL.md) o dentro una sua cartella.
RE_FILE_DI_ARTURO = re.compile(r"(?:^|(?<=[\s\"'`(])|(?<=\.claude[/\\])|(?<=arturo[/\\]))(?:commands|agents|hooks|bin|docs|shared|rules|output-styles|skills[/\\][\w-]+)"
                               r"[/\\]$")

# /segnala precedenti: quante copie e quanto del loro "In breve" legge Claude prima dell'anteprima.
PRECEDENTI_MASSIMO = 30
BREVE_MASSIMO = 400

AIUTO = f"""arturo segnala: un problema, un'idea o un'integrazione da proporre a chi mantiene Arturo.

Di solito lo usa /segnala dentro Claude Code. Comandi:

  info                                   versione di Arturo e di Claude Code, sistema, gh collegato
  prepara --tipo T --titolo "…" --file BOZZA [--pacchetto VOCI] [--tieni CATEGORIE] [--errore FILE]
          [--origine {"|".join(ORIGINI)}]
                                         pulisce la bozza e mostra l'anteprima (T: {", ".join(TIPI)}).
                                         --pacchetto: le caselle accese, separate da virgole, o "nessuna"
                                         ({", ".join(v for v, _, _ in VOCI_PACCHETTO)}; di default
                                         {", ".join(v for v, _, a in VOCI_PACCHETTO if a)}).
                                         --tieni: cosa non togliere dal testo ({", ".join(REDAZIONE)})
  invia --canale C --file PRONTA         la manda (C: arturo = diretta a chi mantiene Arturo, il default;
                                         gh = issue pubblica; web = pagina della issue compilata;
                                         email = testo negli appunti per {EMAIL})
  stato                                  le tue segnalazioni: in attesa, arrivate, corrette (da NOVITA.md),
                                         con lo stato e la risposta di chi mantiene Arturo
  seguito N --file TESTO [--conferma]    aggiunge alla n. N quello che chi mantiene Arturo ha chiesto;
                                         senza --conferma mostra solo cosa partirebbe
  ritira N [--conferma]                  ritira la n. N: sul server restano solo numero, tipo e data
  precedenti                             le segnalazioni già partite col loro "In breve", dalla più recente:
                                         /segnala le confronta con la bozza prima dell'anteprima
  canale [arturo|gh|web|email]           il canale ricordato, o lo ricorda
  chiedi                                 /fine può fare la domanda della settimana? (0 sì, 3 no)
  basta                                  niente inviti a segnalare finché non dici riprendi
  riprendi                               gli inviti ripartono

Lo stato resta su questo computer: ~/.claude/session-env/segnala.json. I codici delle ricevute:
~/.claude/data/segnalazioni/ricevute.json, leggibile solo da te.
Le copie delle segnalazioni: ~/.claude/data/segnalazioni/."""


# --- stato -------------------------------------------------------------------

def file_stato() -> Path:
    return radice_orsa() / "session-env" / "segnala.json"


def cartella_copie() -> Path:
    return radice_orsa() / "data" / "segnalazioni"


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

def _scanner():
    """hooks/credential-leak-scanner.py: pattern e immagini in linea vengono da lì, una lista sola."""
    scanner = Path(os.path.realpath(__file__)).parent.parent / "hooks" / "credential-leak-scanner.py"
    spec = importlib.util.spec_from_file_location("credential_leak_scanner", str(scanner))
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


def segreti_trovati(testo: str) -> list:
    modulo = _scanner()
    # Come la guardia: nel base64 di un'immagine in linea AKIA… o BSA… compaiono per caso (#4078).
    testo = modulo.DATA_URI.sub("", testo)
    return sorted({nome for p, nome in modulo.CREDENTIAL_PATTERNS
                   if nome not in NON_SEGRETI and re.search(p, testo)})


def togli_home(testo: str) -> str:
    """Ogni cartella personale diventa ~: la propria e quelle di altri che compaiono in un log."""
    casa = str(Path.home())
    # Anche con le barre doppie del repr di un percorso Windows e con le barre dritte (review del 7/11/2026, finding 44):
    # 'C:\\\\Users\\\\mrossi\\\\.claude' di un errore Python restava intero.
    forme = set()
    for f in {casa, os.path.realpath(casa)}:
        forme |= {f, f.replace("\\", "\\\\"), f.replace("\\", "/")}
    for forma in sorted(forme, key=len, reverse=True):
        if len(forma) > 1:
            testo = testo.replace(forma, "~")
    # Le cartelle personali di altri: il nome arriva fino alla barra dopo, spazi compresi ("Mario Rossi"); senza una
    # barra entro 64 caratteri si ferma allo spazio. Una o due barre, dritte o rovesciate.
    sep = r"(?:\\\\|\\|/)"
    # Anche nelle forme di Git Bash e di WSL, /c/Users/… e /mnt/c/Users/… (finding 28): prima restava "/c~".
    for nome in (r"[^\\/\"'`\r\n<>|:*?]{1,64}?(?=[\\/])", r"[^\\/\s\"'`]+"):
        testo = re.sub(r"(?i)\b[A-Z]:" + sep + r"Users" + sep + nome, "~", testo)
        testo = re.sub(r"(?i)(?:/mnt)?(?:/[a-z])?/(?:Users|home)/" + nome, "~", testo)
    return testo


def _ip_vero(valore: str) -> bool:
    parti = valore.split(".")
    return all(0 <= int(x) <= 255 for x in parti) and valore not in ("127.0.0.1", "0.0.0.0")


def redigi(testo: str, tieni=()) -> tuple:
    """Toglie dal testo quello che dice troppo di chi scrive e non serve a capire il guasto (4/11/2026, piano del
    24/10). Torna (testo, {categoria: quante}). Le cartelle personali escono sempre; le altre categorie restano se
    la persona le nomina in `tieni`. Non riconosce un nome di persona o di cliente: quello lo toglie Claude nella
    bozza, a giudizio."""
    testo, tolti = togli_home(testo), {}

    def via(categoria, regex, filtro=None, forma=None):
        nonlocal testo
        if categoria in tieni:
            return

        def cambia(m):
            if filtro and not filtro(m.group(0)):
                return m.group(0)
            nuovo = forma(m) if forma else REDAZIONE[categoria][0]
            if nuovo != m.group(0):  # forma può tenere il nome: un file di Arturo
                tolti[categoria] = tolti.get(categoria, 0) + 1
            return nuovo
        testo = regex.sub(cambia, testo)

    via("web", RE_WEB, lambda u: not WEB_PUBBLICI.match(u if "://" in u else "https://" + u))
    via("email", RE_EMAIL)
    via("computer", RE_COMPUTER)
    via("ip", RE_IP, _ip_vero)
    # Del documento resta l'estensione: un PDF che non si apre è un'informazione, il suo nome no.
    via("documenti", RE_DOCUMENTI, forma=lambda m: _documento(m, testo))
    return testo, tolti


def _documento(m, testo: str) -> str:
    nome = m.group(0)
    if RE_FILE_DI_ARTURO.search(testo[:m.start()]) or nome.rsplit(".", 1)[0].replace("_", "").replace("-", "").isupper():
        return nome
    return f"{REDAZIONE['documenti'][0]}.{m.group(1).lower()}"


def documenti_da_controllare(testo: str, tieni=()) -> int:
    """Quanti nomi di documenti che redigi toglie hanno una parola minuscola subito prima: di un nome con spazi
    ("contratto rossi.zip") redigi toglie solo l'ultima parte, e l'anteprima chiede di guardarli (finding 28)."""
    if "documenti" in tieni:
        return 0
    testo = togli_home(testo)
    return sum(1 for m in RE_DOCUMENTI.finditer(testo)
               if _documento(m, testo) != m.group(0) and re.search(r"[^\W\d_] $", testo[:m.start()]))


def descrivi_tolti(tolti: dict) -> str:
    return ", ".join(f"{n} {REDAZIONE[c][1]}" for c, n in tolti.items())


# --- pacchetto tecnico -----------------------------------------------------------

def _leggi(percorso: Path, righe: int = 0) -> str:
    try:
        testo = percorso.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""
    return "\n".join(testo.splitlines()[:righe]) if righe else testo


def voci_pacchetto(scelta) -> list:
    """Le voci accese: quelle di default, oppure la scelta della persona ("nessuna" le spegne tutte)."""
    if scelta is None:
        return [v for v, _, accesa in VOCI_PACCHETTO if accesa]
    nomi = [x.strip() for x in scelta.split(",") if x.strip()]
    if nomi in (["nessuna"], ["nessuno"]):
        return []
    ignote = [x for x in nomi if x not in {v for v, _, _ in VOCI_PACCHETTO}]
    if ignote:
        raise ValueError(f"voce del pacchetto sconosciuta: {', '.join(ignote)} "
                         f"({', '.join(v for v, _, _ in VOCI_PACCHETTO)}, oppure nessuna)")
    return nomi


def pacchetto(voci: list, errore: str = "", tieni=()) -> dict:
    """Il testo di ogni voce accesa, già passato da redigi. La voce collega non ha testo."""
    radice = radice_orsa()
    deriva = {}
    try:
        deriva = json.loads((radice / "cache" / "deriva.json").read_text(encoding="utf-8"))
    except (OSError, ValueError, UnicodeDecodeError):
        pass
    deriva = deriva if isinstance(deriva, dict) else {}
    fonti = {
        "ambiente": lambda: f"{ambiente()}\nPython: {platform.python_version()}",
        "banchi": lambda: _leggi(radice / "cache" / "banchi-ultimo-esito.txt", 15) or "i controlli delle guardie non sono ancora girati",
        "config": lambda: ("nessun guasto" if not deriva.get("config") else ", ".join(map(str, deriva["config"])))
                          if deriva else "non misurata su questo computer",
        "deriva": lambda: ("file: " + (", ".join(map(str, deriva.get("file") or [])) or "nessuno") + "\nhook mancanti: "
                           + (", ".join(map(str, deriva.get("hook") or [])) or "nessuno")) if deriva.get("misurata")
                          else "non misurata su questo computer",
        "errore": lambda: errore[-VOCE_MASSIMO:],
    }
    pieno = {}
    for voce in voci:
        if voce == "collega" or voce not in fonti:
            continue
        valore = (fonti[voce]() or "").strip()
        if valore:
            pieno[voce] = redigi(valore, tieni)[0][:VOCE_MASSIMO]
    return pieno


def anteprima_pacchetto(voci: list, contenuto: dict, errore_presente: bool) -> str:
    righe = ["Pacchetto tecnico, solo col canale arturo: lo legge solo chi mantiene Arturo e il server lo cancella dopo 90 giorni."]
    for voce, cosa, _ in VOCI_PACCHETTO:
        accesa = voce in voci and (voce in contenuto or voce == "collega")
        if voce == "errore" and not errore_presente:
            cosa += ", non c'è"
        righe.append(f"  [{'x' if accesa else ' '}] {voce}: {cosa}")
        if accesa and voce in contenuto:
            righe += [f"      {r}" for r in contenuto[voce].splitlines()]
    righe.append("Per cambiare le caselle rilancia prepara con --pacchetto e le voci da accendere, separate da virgole "
                 "(--pacchetto nessuna le spegne tutte).")
    return "\n".join(righe)


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


def testo_appunti(testo: str, programma: str) -> bytes:
    """I byte da passare al programma degli appunti. clip di Windows legge lo stdin nella codepage della console,
    e le accentate arrivavano rotte: in UTF-16 con il BOM le legge giuste (review del 9/11/2026, #5102)."""
    if programma == "clip":
        return "﻿".encode("utf-16-le") + testo.encode("utf-16-le")
    return testo.encode("utf-8")


def copia_appunti(testo: str) -> bool:
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
            if subprocess.run(comando, input=testo_appunti(testo, comando[0]), timeout=10).returncode == 0:
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


def _versione_plugin() -> str:
    """"v0.2.8" dal .claude-plugin/plugin.json del pacchetto, vuoto se non c'è."""
    try:
        numero = json.loads((radice_arturo() / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8")).get("version")
    except (OSError, ValueError, AttributeError):
        return ""
    return "v" + numero if isinstance(numero, str) and numero else ""


def _esegui(comando: list) -> str:
    try:
        r = subprocess.run(comando, capture_output=True, text=True, timeout=10)
        return r.stdout.strip() if r.returncode == 0 else ""
    except (OSError, subprocess.SubprocessError):
        return ""


def ambiente() -> str:
    """Versioni di Arturo e di Claude Code e sistema: le prime righe di info, senza gh né canale. La voce ambiente
    del pacchetto tecnico la usa da sola, per non lanciare gh a ogni anteprima."""
    # Col plugin non c'è git: la versione sta nel manifest del pacchetto (review del 7/11/2026, finding 68).
    versione = _esegui(["git", "-C", str(radice_arturo()), "describe", "--tags", "--abbrev=0", "--match", "v*"]) \
        or _versione_plugin() or "sconosciuta"
    claude = _esegui(["claude", "--version"]) or "sconosciuta"
    return f"Arturo: {versione}\nClaude Code: {claude}\nSistema: {platform.system()} {platform.release()}"


def info() -> str:
    if not shutil.which("gh"):
        gh = "non installato"
    else:
        try:
            gh = "collegato" if subprocess.run(["gh", "auth", "status"], capture_output=True,
                                               timeout=10).returncode == 0 else "non collegato"
        except (OSError, subprocess.SubprocessError):
            gh = "non collegato"
    canale = leggi_stato().get("canale", "non scelto")
    return f"{ambiente()}\ngh: {gh}\nCanale ricordato: {canale}"


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
    tieni = tuple(x.strip() for x in (opz.get("--tieni") or "").split(",") if x.strip())
    ignote = [x for x in tieni if x not in REDAZIONE]
    origine = opz.get("--origine") or "segnala"
    if ignote or origine not in ORIGINI:
        print(f"Errore: --tieni vuole {', '.join(REDAZIONE)}; --origine vuole {', '.join(ORIGINI)}", file=sys.stderr)
        return 2
    voci = voci_pacchetto(opz.get("--pacchetto"))
    errore = Path(opz["--errore"]).read_text(encoding="utf-8", errors="replace") if opz.get("--errore") else ""
    if errore and opz.get("--pacchetto") is None:
        voci.append("errore")  # un errore passato da Claude si vede acceso: la persona lo spegne nell'anteprima
    sorgente = Path(bozza)
    testo, tolti = redigi(sorgente.read_text(encoding="utf-8"), tieni)
    testo = testo.strip()
    titolo, tolti_titolo = redigi(titolo_con_tipo(tipo, titolo), tieni)
    for c, n in tolti_titolo.items():
        tolti[c] = tolti.get(c, 0) + n
    contenuto = pacchetto(voci, errore, tieni)
    trovati = segreti_trovati(titolo + "\n" + testo + "\n" + "\n".join(contenuto.values()))
    if trovati:
        print("Fermo: la bozza contiene qualcosa che sembra un segreto (" + ", ".join(trovati) + "). "
              "Toglilo dalla bozza e rilancia prepara. Niente è stato preparato.", file=sys.stderr)
        return 3
    if not testo:
        print("Errore: la bozza è vuota", file=sys.stderr)
        return 2
    pronta = sorgente.with_name(sorgente.name + ".pronta.json")
    dati = {"tipo": tipo, "titolo": titolo, "testo": testo + FIRMA, "pacchetto": contenuto,
            "collega": "collega" in voci, "origine": origine, "tieni": list(tieni)}
    ts.scrivi_json_atomico(pronta, dict(dati, impronta=impronta_pronta(dati)))
    print(f"PRONTA: {pronta}\n")
    print(f"Titolo: {titolo}\n")
    print(testo + FIRMA)
    if tolti:
        print(f"Tolto dal testo: {descrivi_tolti(tolti)}. Se servono a capire il problema, rilancia prepara con "
              f"--tieni {','.join(tolti)}.\n")
    dubbi = documenti_da_controllare(sorgente.read_text(encoding="utf-8"), tieni)
    if dubbi:
        print(f"Da controllare: {dubbi} nomi di documenti hanno una parola subito prima. Se è parte del nome "
              "(\"contratto rossi.zip\"), è rimasta nel testo: toglila dalla bozza e rilancia prepara.\n")
    print(anteprima_pacchetto(voci, contenuto, bool(errore)) + "\n")
    print(f"Dove può andare:\n  arturo (di solito): arriva solo a chi mantiene Arturo, senza altri passi\n"
          f"  gh o web: issue pubblica su github.com/{REPO}, la vede chiunque\n"
          f"  email: testo negli appunti da mandare a {EMAIL}")
    return 0


def impronta_pronta(dati: dict) -> str:
    """L'impronta di quello che prepara ha pulito e mostrato (review del 7/11/2026, finding 98): invia rifiuta un file
    scritto a mano o cambiato dopo l'anteprima. Non è una firma: dice che il file è quello dell'anteprima."""
    campi = {k: dati.get(k) for k in ("tipo", "titolo", "testo", "pacchetto", "collega", "origine", "tieni")}
    return hashlib.sha256(json.dumps(campi, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()


def pulita(dati: dict) -> bool:
    """Titolo, testo e pacchetto sono già passati da redigi: ripassarli non cambia niente."""
    tieni = tuple(x for x in (dati.get("tieni") or ()) if x in REDAZIONE)
    parti = [dati["titolo"], dati["testo"], *(dati.get("pacchetto") or {}).values()]
    return all(redigi(x, tieni)[0] == x for x in parti if isinstance(x, str))


def invia(opz: dict) -> int:
    canale, file = opz.get("--canale"), opz.get("--file")
    if canale not in CANALI or not file:
        print(f"Errore: servono --canale ({', '.join(CANALI)}) e --file", file=sys.stderr)
        return 2
    try:
        dati = json.loads(Path(file).read_text(encoding="utf-8"))
        tipo, titolo, testo = dati["tipo"], dati["titolo"], dati["testo"]
        # Un file preparato prima dello sportello (4/11/2026) non ha pacchetto: parte senza.
        contenuto = {k: v for k, v in (dati.get("pacchetto") or {}).items()
                     if k in {x for x, _, _ in VOCI_PACCHETTO} and isinstance(v, str)}
        collega = dati.get("collega") is True
        origine = dati.get("origine") if dati.get("origine") in ORIGINI else "segnala"
        # Solo un file uscito da prepara, uguale a quello dell'anteprima e già pulito (finding 98).
        preparata = dati.get("impronta") == impronta_pronta(dati) and pulita(dati)
    except (OSError, ValueError, KeyError, TypeError, AttributeError):
        preparata = False
    if not preparata:
        print("Errore: il file non è la segnalazione preparata e mostrata nell'anteprima. Lancia di nuovo prepara "
              "sulla bozza. Niente è partito.", file=sys.stderr)
        return 2
    # Il file può essere cambiato dopo prepara: il controllo si ripete qui, prima di uscire.
    trovati = segreti_trovati(titolo + "\n" + testo + "\n" + "\n".join(contenuto.values()))
    if trovati or tipo not in TIPI:
        print("Fermo: " + (f"il testo contiene qualcosa che sembra un segreto ({', '.join(trovati)})"
                           if trovati else "tipo sconosciuto") + ". Niente è partito.", file=sys.stderr)
        return 3

    # Un solo orario per il file in attesa e la copia: lo stesso nome li lega quando parte (28/10/2026).
    adesso = dt.datetime.now()
    esito, ricevuta = "", False
    if canale != "arturo" and contenuto:
        print("Il pacchetto tecnico resta su questo computer: parte solo col canale arturo.")
    if canale == "arturo":
        dati_server = {"tipo": tipo, "titolo": titolo, "testo": testo, "versione": telemetria.versione(),
                       "sistema": telemetria.sistema(), "origine": origine}
        if contenuto:
            dati_server["pacchetto"] = contenuto
        # L'id lega la segnalazione agli eventi d'uso solo con la casella "collega" accesa e la telemetria accesa
        # (4/11/2026: prima partiva sempre a telemetria accesa).
        if collega and not telemetria.perche_spenta():
            dati_server["installazione"] = telemetria.installazione()
        status, risposta = telemetria.posta_json("/v1/segnalazioni", dati_server, timeout=10)
        if 200 <= status < 300:
            esito = "arrivata a chi mantiene Arturo"
            # Il numero è quello che torna nelle /novita quando esce la correzione: chi segnala lo deve
            # sapere (Computer Club, 27/10/2026: "quando faccio il segnale cosa succede?").
            numero = risposta.get("numero")
            if isinstance(numero, int) and not isinstance(numero, bool) and numero > 0:
                esito += f": è la segnalazione n. {numero}"
                # La ricevuta (4/11/2026): col codice la persona legge la risposta. Un server di prima non lo manda.
                if telemetria.salva_codice(numero, risposta.get("codice")):
                    ricevuta = True
            # Il server risponde: partono anche quelle rimaste in attesa (27/10/2026).
            partite = telemetria.invia_segnalazioni_in_attesa()
            if partite:
                esito += f", con {partite} rimast{'a' if partite == 1 else 'e'} in attesa"
        elif status in (400, 413):
            print(f"Non inviata: il server l'ha rifiutata ({status}). Prova il canale web o email.", file=sys.stderr)
            return 1
        else:
            attesa = telemetria.cartella_attesa()
            attesa.mkdir(parents=True, exist_ok=True)
            ts.scrivi_json_atomico(attesa / f"{adesso:%Y-%m-%d_%H%M%S}_{tipo}.attesa.json", dati_server)
            # Il codice dice a chi mantiene Arturo dove guardare: rete o server (segnalazione del 27/10/2026).
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
        copiato = True if testo_dentro else copia_appunti(testo)
        if not _apri(url):
            print(f"Non riesco ad aprire il browser. Apri tu questo indirizzo:\n{url}")
        if not testo_dentro:
            print("Il testo è lungo: nella pagina c'è il solo titolo. "
                  + ("Il testo è negli appunti, incollalo nella casella." if copiato
                     else "Copia il testo qui sotto nella casella.\n\n" + testo))
        esito = "pagina della issue aperta: la persona controlla e preme Invia"
    else:
        oggetto = f"[Arturo] {titolo}"
        if copia_appunti(testo):
            print(f"Il testo è negli appunti.\nA: {EMAIL}\nOggetto: {oggetto}\n"
                  "Apri il tuo programma di posta, incolla il testo e invia.")
        else:
            print(f"Non riesco a copiare negli appunti. Manda questa email:\nA: {EMAIL}\nOggetto: {oggetto}\n\n{testo}")
        esito = f"email pronta per {EMAIL}: la persona la invia"

    cartella = cartella_copie()
    cartella.mkdir(parents=True, exist_ok=True)
    copia = cartella / f"{adesso:%Y-%m-%d_%H%M%S}_{tipo}.md"
    partito = ", ".join(sorted(contenuto)) if canale == "arturo" and contenuto else "nessuno"
    copia.write_text(f"# {titolo}\n\nData: {adesso:%Y-%m-%d %H:%M}\nCanale: {canale}\nEsito: {esito}\n"
                     f"Pacchetto: {partito}\n\n{testo}", encoding="utf-8")
    oggi = ts.oggi().isoformat()
    cambia_stato(lambda s: s.update({"inviata": oggi, "canale": canale}))
    telemetria.registra("segnalazione", tipo)
    print(f"\nFatto: {esito}.\nCopia: {copia}")
    if ricevuta:
        print("Ricevuta: il codice per leggere la risposta è salvato su questo computer. "
              "La risposta di chi mantiene Arturo si legge con: arturo segnala stato")
    return 0


def novita_per_numero(testo: str) -> dict:
    """{numero: (data, titolo)} della prima voce di NOVITA.md che cita "segnalazione n. X" (o "segnalazioni
    n. 14, 15 e 16") o "proposta n. X": il numero è lo stesso (segnalazione n. 59). Le voci sono in ordine inverso: vince la più vecchia, cioè la correzione."""
    trovate, data, titolo = {}, "", ""
    for riga in testo.splitlines():
        intestazione = re.match(r"## (\d{4}-\d{2}-\d{2})\s*\S*\s*(.*)", riga)
        if intestazione:
            data, titolo = intestazione.group(1), intestazione.group(2).strip()
            continue
        if not data:
            continue
        for gruppo in re.finditer(r"(?:segnalazion[ei]|propost[ae])\s+n\.\s*\d+(?:(?:\s*,\s*|\s+e\s+)(?:n\.\s*)?\d+)*", riga):
            for numero in re.findall(r"\d+", gruppo.group(0)):
                trovate[int(numero)] = (data, titolo)
    return trovate


def _copie() -> list:
    """Le copie delle segnalazioni partite da questo computer, dalla più vecchia: numero (o None), data,
    titolo, esito, e il paragrafo "In breve" in una riga (per le copie senza, l'inizio del testo)."""
    copie = []
    for copia in sorted(cartella_copie().glob("*.md")):
        try:
            testo = copia.read_text(encoding="utf-8")
        except OSError:
            continue
        titolo = testo.splitlines()[0].lstrip("# ").strip() if testo else copia.stem
        data = re.search(r"^Data: (\S+)", testo, re.M)
        esito = re.search(r"^Esito: (.*)$", testo, re.M)
        esito = esito.group(1) if esito else ""
        numero = re.search(r"segnalazione n\. (\d+)", esito)
        corpo = testo.split("\n\n", 2)[2] if testo.count("\n\n") >= 2 else testo
        breve = re.search(r"^### In breve\s*\n(.*?)(?=^###|\Z)", corpo, re.M | re.S)
        breve = " ".join((breve.group(1) if breve else corpo.replace(FIRMA.strip(), "")).split())
        copie.append({"file": copia.stem, "numero": int(numero.group(1)) if numero else None, "quando": data.group(1) if data else "",
                      "titolo": titolo, "esito": esito, "breve": breve[:BREVE_MASSIMO]})
    return copie


STATO_IN_PAROLE = {
    "ricevuta": "arrivata, chi mantiene Arturo deve ancora guardarla",
    "serve-info": "chi mantiene Arturo ti chiede altre informazioni: rispondi con /segnala seguito",
    "in-lavoro": "in lavoro",
    "chiusa": "chiusa",
    "rifiutata": "non accolta",
    "ritirata": "ritirata da te",
}


def stato() -> int:
    """Le segnalazioni partite da questo computer e dove sono: in attesa, arrivate, corrette e uscite
    (Computer Club N.3, 27/10/2026: "quando faccio il segnale cosa succede?"). Dal 4/11/2026, con il codice della
    ricevuta, anche lo stato e la risposta di chi mantiene Arturo, letti dal server."""
    copie = _copie()
    if not copie:
        print("Nessuna segnalazione partita da questo computer.")
        return 0
    try:
        uscite = novita_per_numero((radice_arturo() / "NOVITA.md").read_text(encoding="utf-8"))
    except OSError:
        uscite = {}
    codici, sportello, rete = telemetria.codici(), telemetria.leggi_sportello(), True
    rifiutate = {f.name.replace(".rifiutata.json", "") for f in cartella_copie().glob("*.rifiutata.json")}
    for c in copie:
        numero, esito, risposta = c["numero"], c["esito"], {}
        if numero and numero in codici and rete:
            status, risposta = telemetria.leggi_contributo(numero, codici[numero])
            rete = status != 0  # una rete giù non si richiede a ogni riga
            if risposta:
                risposta["vista"] = risposta.get("aggiornata", "")
                sportello[numero] = risposta
        risposta = risposta or (sportello.get(numero) if numero else None) or {}
        if c["file"] in rifiutate:
            dove = "rifiutata dal server (troppo lunga o non valida): mandala col canale web o email"
        elif numero and numero in uscite:
            giorno, voce = uscite[numero]
            dove = f"corretta: la novità del {giorno} \"{voce}\" la racconta"
        elif numero and risposta:
            dove = STATO_IN_PAROLE.get(risposta.get("stato"), "arrivata")
            if risposta.get("versione_fix"):
                dove += f", la correzione esce con la versione {risposta['versione_fix']}"
        elif numero:
            dove = "arrivata, la correzione non è ancora uscita"
        elif esito.startswith("in attesa"):
            dove = "in attesa: parte da sola appena il server risponde"
        else:
            dove = esito or "esito non scritto"
        print(f"{'n. ' + str(numero) if numero else '-'} · {c['quando']} · {c['titolo']}: {dove}")
        if risposta.get("risposta"):
            print("  Risposta di chi mantiene Arturo: " + " ".join(risposta["risposta"].split()))
    if not rete:
        print("\nIl server ora non risponde: stato e risposte sono quelli dell'ultima lettura.")
    if sportello:
        telemetria.scrivi_sportello(sportello)
    return 0


def _codice_di(numero: str):
    if not numero.isdigit():
        raise ValueError(f'numero di segnalazione non valido: "{numero}"')
    codice = telemetria.codici().get(int(numero))
    if not codice:
        print(f"La n. {numero} non ha la ricevuta su questo computer: è partita da un altro computer, prima del "
              "4/11/2026 o da un altro canale. Scrivi a chi mantiene Arturo con una segnalazione nuova che la cita.",
              file=sys.stderr)
    return int(numero), codice


def seguito(numero: str, opz: dict) -> int:
    """Un'aggiunta alla segnalazione n. N: le informazioni che chi mantiene Arturo ha chiesto, o un caso nuovo.
    Passa dalla stessa pulizia di prepara. Senza --conferma mostra solo cosa partirebbe."""
    n, codice = _codice_di(numero)
    if not codice:
        return 3
    if not opz.get("--file"):
        print("Errore: serve --file col testo da aggiungere", file=sys.stderr)
        return 2
    testo, tolti = redigi(Path(opz["--file"]).read_text(encoding="utf-8"))
    testo = testo.strip()
    trovati = segreti_trovati(testo)
    if trovati or not testo:
        print("Fermo: " + (f"il testo contiene qualcosa che sembra un segreto ({', '.join(trovati)})" if trovati
                           else "il testo è vuoto") + ". Niente è partito.", file=sys.stderr)
        return 3
    if "--conferma" not in opz:
        print(f"Si aggiunge alla segnalazione n. {n}, solo per chi mantiene Arturo:\n\n{testo}\n")
        if tolti:
            print(f"Tolto dal testo: {descrivi_tolti(tolti)}.")
        print(f"Parte con: arturo segnala seguito {n} --file {opz['--file']} --conferma")
        return 0
    status, risposta = telemetria.chiedi_json(f"/v1/contributi/{n}/seguito", "POST", {"testo": testo},
                                              {"x-arturo-codice": codice}, timeout=10)
    if 200 <= status < 300:
        print(f"Fatto: aggiunta alla segnalazione n. {n}. Chi mantiene Arturo la vede col resto.")
        return 0
    print({0: "Il server ora non risponde: riprova più tardi.", 404: f"Il server non trova la n. {n}.",
           409: f"La n. {n} è ritirata: manda una segnalazione nuova."}.get(status, f"Non partita: il server risponde {status}."),
          file=sys.stderr)
    return 1


def ritira(numero: str, opz: dict) -> int:
    """Ritira la segnalazione n. N: sul server si cancellano titolo, testo, pacchetto e seguiti, restano numero,
    tipo e data. La copia su questo computer resta."""
    n, codice = _codice_di(numero)
    if not codice:
        return 3
    if "--conferma" not in opz:
        print(f"Ritirare la n. {n} cancella dal server titolo, testo, pacchetto tecnico e aggiunte. Restano numero, tipo "
              f"e data. Non si torna indietro.\nParte con: arturo segnala ritira {n} --conferma")
        return 0
    status, _ = telemetria.chiedi_json(f"/v1/contributi/{n}/ritira", "POST", {}, {"x-arturo-codice": codice}, timeout=10)
    if 200 <= status < 300:
        sportello = telemetria.leggi_sportello()
        sportello[n] = {"stato": "ritirata", "risposta": "", "versione_fix": "", "aggiornata": "", "vista": ""}
        telemetria.scrivi_sportello(sportello)
        print(f"Fatto: la n. {n} è ritirata. Sul server restano solo numero, tipo e data.")
        return 0
    print("Il server ora non risponde: riprova più tardi." if status == 0 else f"Non ritirata: il server risponde {status}.",
          file=sys.stderr)
    return 1


def precedenti() -> int:
    """Le segnalazioni già partite, dalla più recente, col loro "In breve": /segnala le confronta con la bozza
    prima dell'anteprima. Il confronto lo fa Claude sul fatto, non sulle parole (proposta n. 53,
    4/11/2026: tre problemi partiti tre volte ciascuno da sessioni diverse)."""
    copie = _copie()[-PRECEDENTI_MASSIMO:]
    if not copie:
        print("Nessuna segnalazione partita da questo computer.")
        return 0
    for c in reversed(copie):
        quale = f"n. {c['numero']}" if c["numero"] else ("in attesa" if c["esito"].startswith("in attesa") else "senza numero")
        print(f"{quale} · {c['quando']} · {c['titolo']}\n  {c['breve']}")
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
            return prepara(_opzioni(resto, ("--tipo", "--titolo", "--file", "--pacchetto", "--tieni", "--errore", "--origine")))
        if comando in ("seguito", "ritira") and resto:
            conferma = "--conferma" in resto
            altri = [x for x in resto[1:] if x != "--conferma"]
            opz = _opzioni(altri, ("--file",) if comando == "seguito" else ())
            if conferma:
                opz["--conferma"] = True
            return seguito(resto[0], opz) if comando == "seguito" else ritira(resto[0], opz)
        if comando == "invia":
            return invia(_opzioni(resto, ("--canale", "--file")))
        if comando == "stato" and not resto:
            return stato()
        if comando == "precedenti" and not resto:
            return precedenti()
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
