"""arturo scoperta: propone cosa automatizzare, dalle versioni dei file che cambi.

La terza promessa di Arturo (README, "Ti propone cosa automatizzare"). Claude Code salva già ogni
versione dei file che modifica con Edit e Write: le copie stanno in ~/.claude/file-history/<sessione>/
e la mappa dal percorso alla copia nelle righe `file-history-snapshot` dei transcript. Dopo
`cleanupPeriodDays` (30 giorni di default) quella storia sparisce: per questo l'hook
hooks/scoperta-indice.py tiene un indice proprio (percorso, ora, forma della modifica, mai il testo).
Le modifiche fatte a mano le vede il confronto fra l'impronta di /inizio e quella di /fine.

Tre segnali:
  cadenza   lo stesso file, o la stessa famiglia di file, cambiato in almeno 3 giorni con un ritmo;
  campi     gli stessi campi o paragrafi cambiati ogni volta;
  insieme   gruppi di file toccati insieme in almeno 3 sessioni.

La proposta arriva solo a fine lavoro, in /fine: al massimo 1 per sessione e 2 a settimana, con date,
pezzi di diff e una bozza leggibile della skill. Un no la fa tacere per sempre; un sì passa la bozza a
/creaskill; ogni skill creata così si annulla con `arturo scoperta annulla ID`. Tutto resta su questo
computer, in ~/.claude/data/scoperta/. Non esce niente: i conteggi nella telemetria arrivano solo
col testo della privacy approvato (piano del 14/11/2026, passo S9).

  analizza [--giorni N] [--json]   i candidati trovati negli ultimi N giorni (90), dal più forte
  proponi [--sessione ID]          per /fine: una proposta, se i limiti la permettono (exit 3: niente)
  rispondi ID si|no                la risposta della persona
  creata ID PERCORSO               la skill nata dal sì, perché si possa annullare
  annulla ID                       sposta la skill creata in data/scoperta/annullate/
  impronta [--cartella C]          per /inizio: l'impronta dei file di testo del progetto
  confronta [--cartella C]         per /fine: le modifiche a mano dall'impronta di /inizio
  stato                            proposte fatte, accettate, rifiutate e annullate
  escludi MODELLO / esclusioni     una cartella o un file da non guardare mai (modello con * e ?)

Solo libreria standard, Python 3.8 o successivo.
"""
from __future__ import annotations

import datetime as dt
import difflib
import fnmatch
import hashlib
import json
import os
import re
import shutil
import statistics
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

sys.path.append(str(Path(os.path.realpath(__file__)).parent.parent / "hooks"))
from radici import radice_orsa  # noqa: E402

for _flusso in (sys.stdout, sys.stderr):
    try:
        _flusso.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

ID_SESSIONE = re.compile(r"^[A-Za-z0-9_-]{8,80}$")
# I file di testo: le copie, le impronte e i diff guardano solo questi.
TESTO = {".md", ".markdown", ".txt", ".csv", ".tsv", ".json", ".yaml", ".yml", ".toml", ".html", ".htm",
         ".xml", ".tex", ".rtf", ".org", ".rst", ".ini", ".srt", ".vtt", ".ics", ".js", ".ts", ".tsx", ".jsx",
         ".py", ".sh", ".css", ".scss", ".vue", ".svelte", ".astro", ".sql", ".php", ".rb", ".go", ".rs"}
# Il lavoro di chi non programma: a parità di prove, una proposta su questi file viene prima.
SCRITTURA = {".md", ".markdown", ".txt", ".csv", ".tsv", ".html", ".htm", ".tex", ".rtf", ".org", ".rst",
             ".srt", ".vtt", ".ics", ".yaml", ".yml", ".json"}
# Mai guardati. I file che Arturo e Claude Code scrivono da soli (handoff, memoria, piani, transcript,
# cache) sono già un'automazione; le cartelle temporanee e di build non sono lavoro della persona. Il
# resto di ~/.claude resta: una skill o un materiale che la persona cambia ogni settimana conta.
ESCLUSI_SEMPRE = ("~/.claude/projects/*", "~/.claude/file-history/*", "~/.claude/plans/*", "~/.claude/jobs/*",
                  "~/.claude/todos/*", "~/.claude/cache/*", "~/.claude/session-env/*", "~/.claude/plugins/*",
                  "~/.claude/arturo/*", "~/.claude/data/handoffs/*/HANDOFF_*", "~/.claude/data/handoffs/*INDEX.md",
                  "~/.claude/data/memory/*", "~/.claude/data/scoperta/*", "~/.claude/data/telemetria/*",
                  "~/.cache/*", "*/scratchpad/*", "*/node_modules/*",
                  "*/.git/*", "*/dist/*", "*/build/*", "*/.venv/*", "*/__pycache__/*", "*.lock",
                  "*/package-lock.json", "*.min.js", "*.min.css")
# Le cartelle temporanee del sistema valgono solo fuori dalla home: su macOS anche una home di prova può
# stare sotto /private/var/folders.
TEMPORANEE = ("/tmp/*", "/private/*", "/var/folders/*")
CARTELLE_SALTATE = {".git", "node_modules", ".claude", "dist", "build", ".venv", "venv", "__pycache__", ".next",
                    ".astro", ".cache", ".wrangler", "coverage", ".idea", ".vscode"}
MAX_FILE_IMPRONTA = 3000
MAX_BYTE_FILE = 512 * 1024
MAX_BYTE_COPIE = 80 * 1024 * 1024
MAX_DIFF = 8000
GIORNI_SETTIMANA = ("il lunedì", "il martedì", "il mercoledì", "il giovedì", "il venerdì", "il sabato",
                    "la domenica")
# I limiti delle proposte (piano S7): una per sessione, due nei sette giorni.
PER_SESSIONE = 1
PER_SETTIMANA = 2
MIN_VOLTE = 3


# ---------------------------------------------------------------- dove stanno i dati

def cartella() -> Path:
    return radice_orsa() / "data" / "scoperta"


def _file(nome: str) -> Path:
    return cartella() / nome


def _leggi_json(percorso: Path, vuoto):
    try:
        return json.loads(percorso.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return vuoto


def _scrivi_json(percorso: Path, dati) -> None:
    percorso.parent.mkdir(parents=True, exist_ok=True)
    tmp = percorso.with_name(percorso.name + f".{os.getpid()}.tmp")
    tmp.write_text(json.dumps(dati, ensure_ascii=False, indent=1), encoding="utf-8")
    os.replace(tmp, percorso)


def _aggiungi_riga(percorso: Path, dati: dict) -> None:
    percorso.parent.mkdir(parents=True, exist_ok=True)
    with open(percorso, "a", encoding="utf-8") as f:
        f.write(json.dumps(dati, ensure_ascii=False) + "\n")


def _righe(percorso: Path):
    try:
        with open(percorso, encoding="utf-8", errors="replace") as f:
            for riga in f:
                try:
                    dati = json.loads(riga)
                except ValueError:
                    continue
                if isinstance(dati, dict):
                    yield dati
    except OSError:
        return


_CWD = re.compile(r'"cwd"\s*:\s*"((?:[^"\\]|\\.)*)"')


def _istantanee(percorso: Path):
    """Le righe `file-history-snapshot` di un transcript, ognuna con la cartella di lavoro del momento:
    i percorsi relativi valgono da lì, e la cartella cambia quando la sessione entra in un progetto.
    Decodificare ogni riga costa secondi su un transcript lungo, cercare una stringa no."""
    cwd = None
    try:
        with open(percorso, encoding="utf-8", errors="replace") as f:
            for riga in f:
                if '"file-history-snapshot"' not in riga:
                    # Solo all'inizio della riga, dove sta la chiave della riga stessa: più avanti un
                    # "cwd" può essere di un oggetto annidato (il risultato di uno strumento).
                    m = _CWD.search(riga, 0, 600)
                    if m:
                        try:
                            cwd = json.loads('"' + m.group(1) + '"')
                        except ValueError:
                            pass
                    continue
                try:
                    dati = json.loads(riga)
                except ValueError:
                    continue
                if isinstance(dati, dict) and dati.get("type") == "file-history-snapshot":
                    yield dati, cwd
    except OSError:
        return


# ---------------------------------------------------------------- percorsi ed esclusioni

def normalizza(percorso: str, cwd: str | None = None) -> str:
    """Il percorso assoluto, con le barre dritte e senza il worktree: un file modificato in
    .claude/worktrees/<nome>/ è lo stesso file del repository principale."""
    if not percorso:
        return ""
    p = percorso
    if not os.path.isabs(p) and cwd:
        p = os.path.join(cwd, p)
    p = os.path.normpath(p).replace(os.sep, "/")
    return re.sub(r"/\.claude/worktrees/[^/]+(?=/|$)", "", p)


def esclusioni() -> list:
    modelli = list(ESCLUSI_SEMPRE)
    try:
        for riga in _file("esclusioni.txt").read_text(encoding="utf-8").splitlines():
            riga = riga.strip()
            if riga and not riga.startswith("#"):
                modelli.append(riga)
    except OSError:
        pass
    casa = str(Path.home()).replace(os.sep, "/")
    return [casa + m[1:] if m.startswith("~") else m for m in modelli]


def escluso(percorso: str, modelli: list) -> bool:
    casa = str(Path.home()).replace(os.sep, "/")
    if not percorso.startswith(casa + "/") and any(fnmatch.fnmatchcase(percorso, m) for m in TEMPORANEE):
        return True
    return any(fnmatch.fnmatchcase(percorso, m) or fnmatch.fnmatchcase(percorso + "/", m) for m in modelli)


def famiglia(percorso: str) -> str:
    """I file con lo stesso nome salvo i numeri: HANDOFF_2026-11-14.md e HANDOFF_2026-11-21.md, o
    fattura-12.md e fattura-13.md. Un file senza numeri è una famiglia da solo."""
    return re.sub(r"\d+", "#", percorso)


def corto(percorso: str) -> str:
    casa = str(Path.home()).replace(os.sep, "/")
    return "~" + percorso[len(casa):] if percorso.startswith(casa + "/") else percorso


# ---------------------------------------------------------------- campi e paragrafi cambiati

_CAMPO = (
    re.compile(r"^\s*\|\s*\**([^|*]{1,40}?)\**\s*\|"),            # | Campo | valore |
    re.compile(r"^\s*[-*]?\s*\*\*([^*]{1,40}?)\*\*\s*:?"),          # - **Campo**: valore
    re.compile(r'^\s*"([^"]{1,40})"\s*:'),                          # "campo": valore
    re.compile(r"^\s*[-*]?\s*([A-Za-zÀ-ÿ][\wÀ-ÿ .'/-]{0,38}?)\s*:\s+\S"),  # Campo: valore
)
_TITOLO = re.compile(r"^\s{0,3}(#{1,6})\s+(.{1,60}?)\s*#*\s*$")


def etichetta(riga: str) -> str:
    for modello in _CAMPO:
        m = modello.match(riga)
        if m:
            nome = " ".join(m.group(1).split()).strip(" .:-").lower()
            if nome and not nome.isdigit() and not nome.startswith("http"):
                return nome
    return ""


def _titoli(righe: list) -> list:
    """Per ogni riga, il titolo markdown sotto cui sta (o "")."""
    attuale, fuori = "", []
    for riga in righe:
        m = _TITOLO.match(riga)
        if m:
            attuale = " ".join(m.group(2).split()).lower()
        fuori.append(attuale)
    return fuori


TITOLI = {".md", ".markdown", ".txt", ".rst", ".org"}


def etichette(vecchio: str, nuovo: str, massimo: int = 6, titoli: bool = True) -> tuple:
    """I campi o i paragrafi cambiati fra due testi, e quante righe sono entrate e uscite. Un campo
    è il nome prima dei due punti o la prima cella di una tabella; altrimenti vale il titolo del
    paragrafo, con "§" davanti. Le cifre diventano #: "sett. 46" e "sett. 47" sono lo stesso campo."""
    a, b = vecchio.splitlines(), nuovo.splitlines()
    # Un "#" apre un titolo solo nel testo: in uno script è un commento.
    ta, tb = (_titoli(a), _titoli(b)) if titoli else ([""] * len(a), [""] * len(b))
    nomi, piu, meno = [], 0, 0
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes():
        if tag == "equal":
            continue
        meno += i2 - i1
        piu += j2 - j1
        for riga, titolo in list(zip(a[i1:i2], ta[i1:i2])) + list(zip(b[j1:j2], tb[j1:j2])):
            if not riga.strip():
                continue
            nome = etichetta(riga) or (("§ " + titolo) if titolo else "")
            nome = re.sub(r"\d+", "#", nome)
            if nome and nome not in nomi:
                nomi.append(nome)
    return nomi[:massimo], piu, meno


def pezzo_di_diff(vecchio: str, nuovo: str, righe: int = 8) -> str:
    diff = [r for r in difflib.unified_diff(vecchio.splitlines(), nuovo.splitlines(), lineterm="", n=0)
            if not r.startswith(("---", "+++", "@@"))]
    corti = [r if len(r) <= 120 else r[:117] + "..." for r in diff[:righe]]
    if len(diff) > righe:
        corti.append(f"  (altre {len(diff) - righe} righe)")
    return "\n".join(corti)


# ---------------------------------------------------------------- le modifiche, da tre fonti

class Volta:
    """Una volta in cui un file è cambiato: in una sessione, oppure a mano fra /inizio e /fine."""
    __slots__ = ("sessione", "percorso", "ora", "prima", "dopo", "fonte", "campi", "piu", "meno", "creato")

    def __init__(self, sessione, percorso, ora, prima=None, fonte="claude", campi=None, creato=False):
        self.sessione, self.percorso, self.ora, self.prima = sessione, percorso, ora, prima
        self.dopo, self.fonte, self.campi, self.creato = None, fonte, list(campi or []), creato
        self.piu = self.meno = 0

    @property
    def giorno(self) -> dt.date:
        return self.ora.date()


def _ora(testo) -> dt.datetime | None:
    if not isinstance(testo, str):
        return None
    try:
        return dt.datetime.fromisoformat(testo.replace("Z", "+00:00")).astimezone().replace(tzinfo=None)
    except ValueError:
        return None


def _leggi_copia(storia: Path, sessione: str, nome) -> str | None:
    """Il contenuto di una versione: "" se il file allora non c'era, None se la copia è sparita."""
    if nome is None:
        return ""
    try:
        return (storia / sessione / nome).read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None


def da_transcript(giorni: int, modelli: list, radice: Path | None = None) -> list:
    """Le volte dalla storia dei file di Claude Code. Per ogni sessione e file vale la prima versione
    (lo stato prima delle modifiche di quella sessione) e l'ora della prima modifica."""
    radice = radice or radice_orsa()
    storia = radice / "file-history"
    limite = time.time() - giorni * 86400
    volte = []
    for transcript in (radice / "projects").glob("*/*.jsonl"):
        try:
            if transcript.stat().st_mtime < limite:
                continue
        except OSError:
            continue
        sessione, versioni, cartelle, prima_cartella = transcript.stem, defaultdict(dict), {}, None
        for riga, cwd in _istantanee(transcript):
            prima_cartella = prima_cartella or cwd
            copie = (riga.get("snapshot") or {}).get("trackedFileBackups") or {}
            for percorso, v in copie.items():
                if not isinstance(v, dict) or not isinstance(v.get("version"), int):
                    continue
                if not cartelle.get(percorso):
                    cartelle[percorso] = cwd
                versioni[percorso].setdefault(v["version"], v)
        for percorso, elenco in versioni.items():
            # La prima istantanea viene prima di ogni riga con la cartella: allora vale la prima trovata.
            assoluto = normalizza(percorso, cartelle.get(percorso) or prima_cartella)
            if not os.path.isabs(assoluto) or escluso(assoluto, modelli):
                continue
            prima, ora = _stato_iniziale(storia, sessione, elenco)
            if ora is None or ora.timestamp() < limite:
                continue
            volte.append(Volta(sessione, assoluto, ora, prima))
    return volte


def _stato_iniziale(storia: Path, sessione: str, versioni: dict) -> tuple:
    """Il file com'era prima delle modifiche della sessione, e l'ora della prima modifica.
    La versione 1 spesso non compare nei transcript ma sta su disco: il nome della copia è
    <impronta del percorso>@v<N>, e l'impronta si legge da qualsiasi altra versione."""
    ore = [o for o in (_ora(v.get("backupTime")) for v in versioni.values()) if o is not None]
    nomi = [v.get("backupFileName") for v in versioni.values() if isinstance(v.get("backupFileName"), str)]
    impronta_ = nomi[0].split("@")[0] if nomi else ""
    if impronta_:
        uno = storia / sessione / f"{impronta_}@v1"
        try:
            ore.append(dt.datetime.fromtimestamp(uno.stat().st_mtime))
            return uno.read_text(encoding="utf-8", errors="replace"), min(ore)
        except OSError:
            pass
    for n in sorted(versioni):
        nome = versioni[n].get("backupFileName")
        if isinstance(nome, str):
            return _leggi_copia(storia, sessione, nome), (min(ore) if ore else None)
    return None, (min(ore) if ore else None)


def da_indice(giorni: int, modelli: list) -> list:
    """Le volte dall'indice di Arturo: restano anche dopo che Claude Code ha pulito la sua storia."""
    limite = time.time() - giorni * 86400
    viste = {}
    for riga in _righe(_file("indice.jsonl")):
        ora = _ora(riga.get("ora"))
        percorso, sessione = riga.get("percorso"), riga.get("sessione")
        if ora is None or ora.timestamp() < limite or not isinstance(percorso, str) or not isinstance(sessione, str) \
                or escluso(percorso, modelli):
            continue
        # Una volta per sessione e file, con i campi di tutte le sue modifiche.
        volta = viste.get((sessione, percorso))
        if volta is None:
            volta = viste[(sessione, percorso)] = Volta(sessione, percorso, ora, None)
        volta.campi += [c for c in riga.get("campi") or [] if isinstance(c, str) and c not in volta.campi]
    return list(viste.values())


def da_manuali(giorni: int, modelli: list) -> list:
    limite = time.time() - giorni * 86400
    volte = []
    for riga in _righe(_file("manuali.jsonl")):
        ora = _ora(riga.get("ora"))
        percorso = riga.get("percorso")
        if ora is None or ora.timestamp() < limite or not isinstance(percorso, str) or escluso(percorso, modelli):
            continue
        volta = Volta(str(riga.get("sessione") or ""), percorso, ora, None, fonte="a mano",
                      campi=[c for c in riga.get("campi") or [] if isinstance(c, str)])
        volta.piu, volta.meno = int(riga.get("piu") or 0), int(riga.get("meno") or 0)
        volta.dopo = riga.get("diff") if isinstance(riga.get("diff"), str) else None
        volte.append(volta)
    return volte


def raccogli(giorni: int = 90, radice: Path | None = None) -> list:
    """Tutte le volte, una per sessione e file, con i campi cambiati. Il cambio di una volta va dal
    suo stato iniziale a quello iniziale della volta dopo (o al file di oggi): comprende tutto il
    lavoro di quella sessione su quel file."""
    modelli = esclusioni()
    volte = da_transcript(giorni, modelli, radice)
    viste = {(v.sessione, v.percorso) for v in volte}
    volte += [v for v in da_indice(giorni, modelli) if (v.sessione, v.percorso) not in viste]
    manuali = da_manuali(giorni, modelli)
    per_file = defaultdict(list)
    for v in volte:
        per_file[v.percorso].append(v)
    for percorso, elenco in per_file.items():
        elenco.sort(key=lambda v: v.ora)
        try:
            oggi = Path(percorso).read_text(encoding="utf-8", errors="replace") if os.path.getsize(percorso) <= MAX_BYTE_FILE else None
        except OSError:
            oggi = None
        for i, v in enumerate(elenco):
            dopo = elenco[i + 1].prima if i + 1 < len(elenco) else oggi
            if v.prima is None or dopo is None:
                continue
            v.campi, v.piu, v.meno = etichette(v.prima, dopo, titoli=os.path.splitext(percorso)[1].lower() in TITOLI)
            v.dopo = pezzo_di_diff(v.prima, dopo)
    return volte + manuali


# ---------------------------------------------------------------- i tre segnali

def _cadenza(giorni: list):
    """Il ritmo di una serie di giorni, o None se non ce n'è uno. Vale un intervallo regolare (ogni
    intervallo fra metà e il doppio della mediana, su almeno due settimane) o lo stesso giorno
    della settimana per almeno tre volte su cinque."""
    if len(giorni) < MIN_VOLTE:
        return None
    intervalli = [(b - a).days for a, b in zip(giorni, giorni[1:])]
    mediana = statistics.median(intervalli)
    durata = (giorni[-1] - giorni[0]).days
    settimana = Counter(g.weekday() for g in giorni).most_common(1)[0]
    if settimana[1] >= MIN_VOLTE and settimana[1] / len(giorni) >= 0.6 and durata >= 14:
        return f"{GIORNI_SETTIMANA[settimana[0]]}", 1.0
    if mediana < 1 or durata < 14:
        return None
    regolari = sum(1 for x in intervalli if mediana * 0.5 <= x <= mediana * 2)
    if regolari / len(intervalli) < 0.75:
        return None
    if mediana <= 1.5:
        nome = "ogni giorno"
    elif 5 <= mediana <= 9:
        nome = "ogni settimana"
    elif 12 <= mediana <= 17:
        nome = "ogni due settimane"
    elif 26 <= mediana <= 35:
        nome = "ogni mese"
    else:
        nome = f"ogni {round(mediana)} giorni circa"
    return nome, regolari / len(intervalli)


def _firma(segnale: str, chiave: str) -> str:
    return hashlib.sha256(f"{segnale}\0{chiave}".encode("utf-8")).hexdigest()[:10]


def candidati(volte: list) -> list:
    """I candidati, dal più forte. Ognuno porta le volte che lo provano."""
    fuori = []
    per_famiglia = defaultdict(list)
    for v in volte:
        per_famiglia[famiglia(v.percorso)].append(v)
    for fam, elenco in per_famiglia.items():
        elenco.sort(key=lambda v: v.ora)
        giorni = sorted({v.giorno for v in elenco})
        ritmo = _cadenza(giorni)
        con_campi = [v for v in elenco if v.campi]
        conta = Counter(c for v in con_campi for c in dict.fromkeys(v.campi))
        ripetuti = [c for c, n in conta.most_common() if n >= MIN_VOLTE and n / max(1, len(con_campi)) >= 0.5]
        # Un file che a ogni volta cresce (una voce nuova in un diario, un registro, le novità) non si
        # "aggiorna": gli si aggiunge un pezzo con le stesse parti.
        con_diff = [v for v in elenco if v.piu or v.meno]
        aggiunta = bool(con_diff) and sum(1 for v in con_diff if v.piu >= 3 * max(1, v.meno)) / len(con_diff) >= 0.6
        if aggiunta and any(not c.startswith("§") for c in ripetuti):
            # Il titolo sotto cui entra ogni parte nuova è il contenitore, non una sua voce.
            ripetuti = [c for c in ripetuti if not c.startswith("§")]
        membri = sorted({v.percorso for v in elenco})
        # Una famiglia con un file nuovo a ogni volta (fattura-12, fattura-13) è un file che crei.
        nuovi = len(membri) if len(membri) >= MIN_VOLTE else 0
        if ritmo is None and (not ripetuti or len(giorni) < MIN_VOLTE):
            continue
        segnale = "cadenza" if ritmo else "campi"
        ext = os.path.splitext(fam)[1].lower()
        forza = len(giorni) * (1 + (ritmo[1] if ritmo else 0)) * (1.5 if ripetuti else 1) * (1.5 if ext in SCRITTURA else 1)
        fuori.append({
            "id": _firma(segnale, fam), "segnale": segnale, "famiglia": fam, "file": membri,
            "ritmo": ritmo[0] if ritmo else "", "campi": ripetuti[:5], "volte": len(giorni), "nuovi": nuovi,
            "aggiunta": aggiunta,
            "forza": round(forza, 2), "prove": elenco,
        })
    fuori += _insieme(volte)
    fuori.sort(key=lambda c: -c["forza"])
    return fuori


def _insieme(volte: list) -> list:
    """I gruppi di file toccati insieme: la stessa coppia di famiglie in almeno 3 sessioni, e quasi
    sempre insieme (in 7 sessioni su 10 di quella che compare meno)."""
    sessioni = defaultdict(set)
    giorno_di = {}
    for v in volte:
        if v.sessione:
            sessioni[v.sessione].add(famiglia(v.percorso))
            giorno_di.setdefault(v.sessione, v.giorno)
    dove = defaultdict(set)
    for s, fams in sessioni.items():
        for f in fams:
            dove[f].add(s)
    coppie = Counter()
    for fams in sessioni.values():
        if 2 <= len(fams) <= 30:
            ordinate = sorted(fams)
            for i, a in enumerate(ordinate):
                for b in ordinate[i + 1:]:
                    coppie[(a, b)] += 1
    gruppi = []
    usate = set()
    for (a, b), n in coppie.most_common():
        if n < MIN_VOLTE or n / min(len(dove[a]), len(dove[b])) < 0.7 or (a, b) in usate:
            continue
        gruppo = {a, b}
        comuni = dove[a] & dove[b]
        for f in sorted(dove, key=lambda f: -len(dove[f] & comuni)):
            if f in gruppo:
                continue
            insieme = comuni & dove[f]
            if len(insieme) >= MIN_VOLTE and len(insieme) / len(dove[f]) >= 0.7 and len(insieme) >= 0.7 * len(comuni):
                gruppo.add(f)
                comuni = insieme
        for x in gruppo:
            for y in gruppo:
                if x < y:
                    usate.add((x, y))
        giorni = sorted({giorno_di[s] for s in comuni})
        prove = sorted((v for v in volte if v.sessione in comuni and famiglia(v.percorso) in gruppo), key=lambda v: v.ora)
        scritti = sum(1 for f in gruppo if os.path.splitext(f)[1].lower() in SCRITTURA)
        gruppi.append({
            "id": _firma("insieme", "\n".join(sorted(gruppo))), "segnale": "insieme", "famiglia": "", "file": sorted(gruppo),
            "ritmo": "", "campi": [], "volte": len(comuni), "nuovi": 0, "aggiunta": False,
            "forza": round(len(comuni) * (1 + 0.2 * len(gruppo)) * (1.5 if scritti else 1), 2), "prove": prove,
            "giorni": [str(g) for g in giorni],
        })
    return gruppi


# ---------------------------------------------------------------- la proposta leggibile

def _nome_skill(c: dict) -> str:
    base = os.path.basename(c["famiglia"] or c["file"][0])
    base = os.path.splitext(base)[0]
    base = re.sub(r"[#_\s.]+", "-", base.lower())
    base = re.sub(r"[^a-z0-9-]", "", base).strip("-") or "lavoro"
    prefisso = "insieme" if c["segnale"] == "insieme" else "aggiorna"
    return f"{prefisso}-{base}"[:40].strip("-")


def descrivi(c: dict) -> str:
    """La frase che apre la proposta: cosa ha visto Arturo, in parole comuni."""
    volte = c["volte"]
    if c["segnale"] == "insieme":
        nomi = ", ".join(os.path.basename(f) for f in c["file"][:4])
        return f"In {volte} sessioni hai cambiato insieme questi file: {nomi}."
    nome = os.path.basename(c["famiglia"]).replace("#", "N")
    if c["nuovi"] >= MIN_VOLTE:
        verbo, soggetto = "hai creato", f"un file nuovo come {nome}"
    elif c.get("aggiunta"):
        verbo, soggetto = "hai aggiunto", f"una parte nuova a {nome}"
    else:
        verbo, soggetto = "hai cambiato", nome
    frase = f"{c['ritmo'].capitalize()} {verbo} {soggetto}: {volte} volte" if c["ritmo"] else \
        f"{verbo.capitalize()} {soggetto} {volte} volte"
    if c["campi"]:
        frase += (", sempre con " if c.get("aggiunta") else ", e ogni volta cambiano ") + \
            ", ".join(f'"{x}"' for x in c["campi"][:4])
    return frase + "."


def bozza(c: dict) -> str:
    """La bozza della skill: la legge la persona, poi /creaskill la rifinisce con lei."""
    nome = _nome_skill(c)
    file = [corto(f.replace("#", "N")) for f in c["file"][:5]]
    if c["segnale"] == "insieme":
        passi = [f"Quando cambi uno di questi file, apri anche gli altri: {', '.join(file)}.",
                 "Per ognuno, di' cosa va allineato e proponi la modifica.",
                 "Mostra le modifiche insieme e salva solo dopo il sì della persona."]
        quando = "quando la persona cambia uno di questi file"
    else:
        passi = [f"Apri {file[0]}" + (" (l'ultimo della serie)" if len(c["file"]) > 1 else "") + "."]
        if c["nuovi"] >= MIN_VOLTE:
            passi = [f"Crea il file nuovo partendo dall'ultimo della serie ({file[-1]}), col numero o la data giusti."]
        if c.get("aggiunta"):
            passi.append("Aggiungi la parte nuova sul modello delle ultime" + (
                ", con queste voci: " + ", ".join(c["campi"][:5]) if c["campi"] else "") +
                ". Chiedi alla persona il contenuto che non trovi.")
        elif c["campi"]:
            passi.append("Aggiorna questi campi: " + ", ".join(c["campi"][:5]) + ". Chiedi alla persona i valori che non trovi.")
        else:
            passi.append("Fai le modifiche di sempre: guardale nelle prove qui sotto.")
        passi.append("Mostra il cambio e salva solo dopo il sì della persona.")
        quando = (c["ritmo"] or "quando la persona lo chiede")
    righe = [f"Nome: {nome}", f"Cosa fa: {descrivi(c)}", f"Quando parte: {quando}", "Passi:"]
    righe += [f"  {i}. {p}" for i, p in enumerate(passi, 1)]
    righe.append("Non fa: non manda niente a nessuno, non cancella file.")
    return "\n".join(righe)


def prove(c: dict, massimo: int = 5) -> str:
    righe = []
    for v in c["prove"][-massimo:]:
        testa = f"- {v.ora:%d/%m/%Y %H:%M} · {corto(v.percorso)}" + (" · a mano" if v.fonte == "a mano" else "")
        if v.campi:
            testa += " · " + ", ".join(v.campi[:4])
        righe.append(testa)
        if v.dopo and v.fonte != "a mano":
            righe += ["    " + r for r in v.dopo.splitlines()[:4]]
    return "\n".join(righe)


def come_json(c: dict) -> dict:
    fuori = {k: v for k, v in c.items() if k != "prove"}
    fuori["prove"] = [{"ora": v.ora.isoformat(timespec="minutes"), "percorso": v.percorso, "fonte": v.fonte,
                       "campi": v.campi, "piu": v.piu, "meno": v.meno} for v in c["prove"]]
    return fuori


# ---------------------------------------------------------------- lo stato delle proposte

def leggi_proposte() -> dict:
    dati = _leggi_json(_file("proposte.json"), {})
    return dati if isinstance(dati, dict) else {}


def limiti_permettono(proposte: dict, sessione: str, adesso: dt.datetime) -> bool:
    fatte = [p for p in proposte.values() if isinstance(p, dict) and p.get("quando")]
    if sum(1 for p in fatte if p.get("sessione") == sessione) >= PER_SESSIONE:
        return False
    settimana = adesso - dt.timedelta(days=7)
    return sum(1 for p in fatte if (_ora(p["quando"]) or adesso) >= settimana) < PER_SETTIMANA


def proponi(sessione: str, giorni: int = 90, adesso: dt.datetime | None = None, volte: list | None = None):
    """La proposta di questa chiusura, o None. Una proposta già fatta non torna: un no tace per
    sempre, e una senza risposta resta in `stato` finché la persona non risponde."""
    adesso = adesso or dt.datetime.now()
    proposte = leggi_proposte()
    if not limiti_permettono(proposte, sessione, adesso):
        return None
    for c in candidati(volte if volte is not None else raccogli(giorni)):
        if c["id"] in proposte:
            continue
        testo = bozza(c)
        percorso = _file("bozze") / f"{c['id']}.md"
        percorso.parent.mkdir(parents=True, exist_ok=True)
        percorso.write_text(testo + "\n\nProve:\n" + prove(c, 10) + "\n", encoding="utf-8")
        proposte[c["id"]] = {"stato": "proposta", "quando": adesso.isoformat(timespec="seconds"), "sessione": sessione,
                             "segnale": c["segnale"], "volte": c["volte"], "descrizione": descrivi(c),
                             "tipo": os.path.splitext(c["famiglia"] or c["file"][0])[1].lower()}
        _scrivi_json(_file("proposte.json"), proposte)
        return c
    return None


def blocco_proposta(c: dict) -> str:
    return "\n".join([
        f"SCOPERTA {c['id']}: {descrivi(c)}",
        "",
        "Prove:",
        prove(c),
        "",
        "Bozza della skill:",
        bozza(c),
        "",
        f"Risposta: arturo scoperta rispondi {c['id']} si (parte /creaskill con la bozza) oppure no (non torna più).",
    ])


def rispondi(ident: str, risposta: str) -> int:
    proposte = leggi_proposte()
    voce = proposte.get(ident)
    if not isinstance(voce, dict):
        print(f"Errore: nessuna proposta {ident}. Le proposte stanno in arturo scoperta stato.", file=sys.stderr)
        return 2
    risposta = risposta.lower()
    if risposta in ("si", "sì", "yes"):
        voce.update(stato="accettata", risposta=dt.datetime.now().isoformat(timespec="seconds"))
        _scrivi_json(_file("proposte.json"), proposte)
        percorso = _file("bozze") / f"{ident}.md"
        print(f"Accettata. Bozza: {corto(str(percorso).replace(os.sep, '/'))}")
        print(f"Ora: /creaskill con la bozza; a skill creata, arturo scoperta creata {ident} <cartella della skill>.")
        return 0
    if risposta == "no":
        voce.update(stato="rifiutata", risposta=dt.datetime.now().isoformat(timespec="seconds"))
        _scrivi_json(_file("proposte.json"), proposte)
        print("Rifiutata: questa proposta non torna più.")
        return 0
    print("Errore: la risposta è si oppure no.", file=sys.stderr)
    return 2


def creata(ident: str, percorso: str) -> int:
    proposte = leggi_proposte()
    voce = proposte.get(ident)
    if not isinstance(voce, dict) or voce.get("stato") != "accettata":
        print(f"Errore: la proposta {ident} non è accettata.", file=sys.stderr)
        return 2
    assoluto = os.path.realpath(os.path.expanduser(percorso))
    if not os.path.exists(assoluto):
        print(f"Errore: {percorso} non esiste.", file=sys.stderr)
        return 2
    voce["creata"] = assoluto
    _scrivi_json(_file("proposte.json"), proposte)
    print(f"Registrata: arturo scoperta annulla {ident} la toglie, senza cancellarla.")
    return 0


def annulla(ident: str) -> int:
    proposte = leggi_proposte()
    voce = proposte.get(ident)
    if not isinstance(voce, dict) or not voce.get("creata"):
        print(f"Errore: la proposta {ident} non ha una skill creata.", file=sys.stderr)
        return 2
    sorgente = Path(voce["creata"])
    destinazione = _file("annullate") / f"{ident}-{dt.datetime.now():%Y%m%d-%H%M%S}"
    if sorgente.exists():
        destinazione.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(sorgente), str(destinazione / sorgente.name))
    voce.update(stato="annullata", annullata=dt.datetime.now().isoformat(timespec="seconds"),
                copia=str(destinazione / sorgente.name))
    _scrivi_json(_file("proposte.json"), proposte)
    print(f"Annullata: la skill sta in {corto(str(destinazione / sorgente.name))}. Per rimetterla, spostala di nuovo in {corto(str(sorgente))}.")
    return 0


def stato() -> int:
    proposte = leggi_proposte()
    conta = Counter(p.get("stato") for p in proposte.values() if isinstance(p, dict))
    print(f"Proposte: {sum(conta.values())} · accettate {conta['accettata']} · rifiutate {conta['rifiutata']} · "
          f"annullate {conta['annullata']} · senza risposta {conta['proposta']}")
    for ident, p in proposte.items():
        if isinstance(p, dict) and p.get("stato") == "proposta":
            print(f"  {ident} · {p.get('quando', '')[:10]} · {p.get('descrizione', '')}")
    return 0


# ---------------------------------------------------------------- impronte: le modifiche a mano

def _sessione(argv: list) -> str:
    sessione = _opzione(argv, "--sessione") or os.environ.get("CLAUDE_CODE_SESSION_ID", "")
    return sessione if ID_SESSIONE.match(sessione or "") else ""


def _file_di_testo(radice: Path):
    contati = 0
    for cartella_, sotto, nomi in os.walk(radice):
        sotto[:] = sorted(d for d in sotto if d not in CARTELLE_SALTATE and not d.startswith("."))
        for nome in sorted(nomi):
            if os.path.splitext(nome)[1].lower() not in TESTO:
                continue
            percorso = Path(cartella_) / nome
            try:
                if percorso.is_symlink() or percorso.stat().st_size > MAX_BYTE_FILE:
                    continue
            except OSError:
                continue
            contati += 1
            if contati > MAX_FILE_IMPRONTA:
                return
            yield percorso


def _peso_copie() -> int:
    totale = 0
    for cartella_, _, nomi in os.walk(_file("copie")):
        for nome in nomi:
            try:
                totale += os.path.getsize(os.path.join(cartella_, nome))
            except OSError:
                pass
    return totale


def progetto_valido(radice: Path) -> bool:
    """Una cartella di progetto, non la home né la radice del disco né ~/.claude."""
    try:
        reale = radice.resolve()
    except OSError:
        return False
    casa = Path.home().resolve()
    return reale.is_dir() and reale != casa and reale != Path(reale.anchor) and casa in reale.parents \
        and not str(reale).startswith(str(radice_orsa().resolve()))


GIORNI_IMPRONTE = 14


def pulisci_impronte() -> None:
    """Toglie le impronte di più di 14 giorni e le copie che nessuna impronta usa più: una sessione
    mai chiusa con /fine non lascia copie per sempre."""
    limite = time.time() - GIORNI_IMPRONTE * 86400
    usate = set()
    for f in _file("impronte").glob("*.json"):
        try:
            if f.stat().st_mtime < limite:
                f.unlink()
                continue
        except OSError:
            continue
        dati = _leggi_json(f, {})
        usate.update((dati.get("file") or {}).values() if isinstance(dati, dict) else ())
    for copia in _file("copie").glob("*/*"):
        if copia.name not in usate:
            try:
                copia.unlink()
            except OSError:
                pass


def impronta(radice: Path, sessione: str) -> int:
    if not sessione or not progetto_valido(radice):
        return 0
    pulisci_impronte()
    modelli = esclusioni()
    file, spazio = {}, MAX_BYTE_COPIE - _peso_copie()
    for percorso in _file_di_testo(radice):
        assoluto = normalizza(str(percorso))
        if escluso(assoluto, modelli):
            continue
        try:
            dati = percorso.read_bytes()
        except OSError:
            continue
        impronta_ = hashlib.sha256(dati).hexdigest()
        copia = _file("copie") / impronta_[:2] / impronta_
        if not copia.exists() and spazio > len(dati):
            copia.parent.mkdir(parents=True, exist_ok=True)
            copia.write_bytes(dati)
            spazio -= len(dati)
        file[assoluto] = impronta_
    _scrivi_json(_file("impronte") / f"{sessione}.json",
                 {"cartella": normalizza(str(radice.resolve())), "ora": dt.datetime.now().isoformat(timespec="seconds"),
                  "file": file})
    return len(file)


def toccati_da_claude(sessione: str) -> set:
    return {r.get("percorso") for r in _righe(_file("indice.jsonl")) if r.get("sessione") == sessione}


def confronta(sessione: str) -> int:
    """Le modifiche fatte a mano fra /inizio e /fine: un file cambiato che Claude non ha toccato in
    questa sessione. Rilanciato, sostituisce le righe di prima della stessa sessione."""
    dati = _leggi_json(_file("impronte") / f"{sessione}.json", None) if sessione else None
    if not isinstance(dati, dict) or not isinstance(dati.get("file"), dict):
        return 0
    prima, claude, modelli = dati["file"], toccati_da_claude(sessione), esclusioni()
    adesso = dt.datetime.now().isoformat(timespec="seconds")
    nuove = []
    for percorso, vecchia in prima.items():
        if percorso in claude or escluso(percorso, modelli):
            continue
        try:
            testo = Path(percorso).read_bytes()
        except OSError:
            continue
        if hashlib.sha256(testo).hexdigest() == vecchia:
            continue
        try:
            vecchio = (_file("copie") / vecchia[:2] / vecchia).read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        nuovo = testo.decode("utf-8", errors="replace")
        campi, piu, meno = etichette(vecchio, nuovo, titoli=os.path.splitext(percorso)[1].lower() in TITOLI)
        nuove.append({"ora": adesso, "sessione": sessione, "percorso": percorso, "campi": campi, "piu": piu,
                      "meno": meno, "diff": pezzo_di_diff(vecchio, nuovo, 12)[:MAX_DIFF]})
    file_manuali = _file("manuali.jsonl")
    tenute = [r for r in _righe(file_manuali) if r.get("sessione") != sessione]
    file_manuali.parent.mkdir(parents=True, exist_ok=True)
    tmp = file_manuali.with_name(file_manuali.name + f".{os.getpid()}.tmp")
    tmp.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in tenute + nuove), encoding="utf-8")
    os.replace(tmp, file_manuali)
    return len(nuove)


# ---------------------------------------------------------------- la riga di comando

def _opzione(argv: list, nome: str, predefinito: str = "") -> str:
    for i, x in enumerate(argv):
        if x == nome and i + 1 < len(argv):
            return argv[i + 1]
        if x.startswith(nome + "="):
            return x.split("=", 1)[1]
    return predefinito


def _giorni(argv: list) -> int:
    try:
        return max(1, min(365, int(_opzione(argv, "--giorni", "90"))))
    except ValueError:
        return 90


def main(argv: list) -> int:
    verbo = argv[0] if argv else "stato"
    resto = argv[1:]
    if verbo in ("-h", "--help", "aiuto", "help"):
        print(__doc__)
        return 0
    if verbo == "analizza":
        trovati = candidati(raccogli(_giorni(resto)))
        if "--json" in resto:
            print(json.dumps([come_json(c) for c in trovati], ensure_ascii=False, indent=1))
            return 0
        if not trovati:
            print("Nessuna ripetizione trovata.")
        for c in trovati[:int(_opzione(resto, "--quanti", "10") or 10)]:
            print(f"{c['id']} · {c['segnale']} · forza {c['forza']} · {descrivi(c)}")
            print(prove(c, 3))
            print()
        return 0
    if verbo == "proponi":
        sessione = _sessione(resto) or "senza-sessione"
        c = proponi(sessione, _giorni(resto))
        if c is None:
            return 3
        print(blocco_proposta(c))
        return 0
    if verbo == "rispondi" and len(resto) >= 2:
        return rispondi(resto[0], resto[1])
    if verbo == "creata" and len(resto) >= 2:
        return creata(resto[0], resto[1])
    if verbo == "annulla" and resto:
        return annulla(resto[0])
    if verbo == "stato":
        return stato()
    if verbo == "impronta":
        n = impronta(Path(_opzione(resto, "--cartella", os.getcwd())), _sessione(resto))
        print(f"SCOPERTA: impronta di {n} file" if n else "SCOPERTA: niente impronta (cartella fuori progetto o sessione ignota)")
        return 0
    if verbo == "confronta":
        n = confronta(_sessione(resto))
        print(f"SCOPERTA: {n} file cambiati a mano" if n else "SCOPERTA: nessun file cambiato a mano")
        return 0
    if verbo == "escludi" and resto:
        modello = " ".join(resto).strip()
        _file("esclusioni.txt").parent.mkdir(parents=True, exist_ok=True)
        with open(_file("esclusioni.txt"), "a", encoding="utf-8") as f:
            f.write(modello + "\n")
        print(f"Escluso: {modello}")
        return 0
    if verbo == "esclusioni":
        print("\n".join(esclusioni()))
        return 0
    print(f"Comando sconosciuto: {verbo}. Scrivi arturo scoperta aiuto.", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
