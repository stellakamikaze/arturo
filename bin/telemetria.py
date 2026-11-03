"""arturo telemetria: gli eventi d'uso che Arturo manda a chi lo mantiene, per migliorarsi.

Perché esiste: Arturo si sviluppa ogni giorno per persone che spesso non sanno dire dove si
bloccano. Senza dati d'uso chi lo mantiene non vede la fase di /setup dove ci si ferma, le guardie
che chiedono a vuoto, gli aggiornamenti rifiutati. Ogni lunedì il server ne fa un riepilogo, e ogni
correzione nata da un segnale lo dice nella sua voce di NOVITA.md.

Cosa esce, e solo questo: un id di installazione casuale e stabile, la versione di Arturo, il sistema
operativo (Darwin, Linux, Windows) e gli eventi di EVENTI con il solo giorno. L'id è casuale, ma chi
mantiene Arturo può sapere chi c'è dietro se conosce la persona: non sono dati anonimi
(docs/privacy.md). Dei file di Arturo modificati o in conflitto esce il percorso dentro Arturo, che è
pubblico, e solo per un file versionato di Arturo (percorso_pubblico): un file della persona esce come
`file:altro`. Delle guardie e dei comandi escono solo i nomi di Arturo, da un elenco chiuso. Mai prompt,
file della persona, percorsi del suo computer, nomi, risposte o testi. Il server non salva l'IP e
tiene gli eventi 12 mesi. Il suo codice è in server/.

Accesa di default. Si spegne con `arturo telemetria spegni`, con ARTURO_TELEMETRIA=0 o con lo
standard DO_NOT_TRACK=1. `arturo telemetria mostra` fa vedere l'id e la coda, così si vede
esattamente cosa parte.

Due tempi, perché un hook non deve mai aspettare la rete:
- `registra` aggiunge una riga alla coda in ~/.claude/data/telemetria/coda.jsonl, senza rete. Lo
  stesso fanno `chiede` (una guardia chiede conferma, per block-dangerous con il nome della regola e
  per commit-secret-gate con la famiglia del segreto: l'id della chiamata resta in
  session-env/telemetria-attese.json) ed `esito` (il PostToolUse o il PostToolUseFailure, via
  bin/telemetria-esito.sh: se la chiamata era in attesa, registra `confermata`);
- `invia` manda la coda in un lotto. L'avvio della sessione lo lancia in background, al massimo
  ogni 6 ore, e lì registra anche la versione di Claude Code quando cambia. Manda anche le
  segnalazioni di /segnala rimaste in attesa.
- `fine` (hooks/session-end.sh, in background) legge il transcript della sessione che chiude e registra
  durata e messaggi della persona in fasce larghe, e le skill usate (dal 3/11/2026, #4540). Del transcript
  non esce niente altro.

Lo stato (id, ultimo tentativo, spenta, avviso_promessa, claude, deriva e config
già inviate, gli id delle ultime sessioni contate da `fine`) sta in ~/.claude/session-env/telemetria.json.
Solo libreria standard, Python 3.8 o successivo. Nessun comando di questo modulo fallisce in modo
da fermare un hook: gli errori di registra e avvio tacciono.
"""
from __future__ import annotations

import json
import os
import platform
import re
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
import uuid
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(os.path.realpath(__file__)).parent))
import todo_store as ts  # noqa: E402

URL = "https://arturo-dati.stellakamikaze.org"
# L'elenco chiuso. Lo stesso elenco sta in server/logica.js e nel README (banco M09).
EVENTI = {
    "sessione": re.compile(r"^$"),
    "comando": re.compile(r"^[a-z0-9-]{1,40}$"),
    "guardia": re.compile(r"^[a-z0-9_.-]{1,60}$"),
    # applicato, conflitto, fallito e scartato li scrive bin/aggiorna-applica.sh; rifiutato (un no al
    # Passo 3) e indietro li registra /aggiorna. automatico è un'installazione alla chiusura della
    # sessione (bin/aggiornamenti.py), dal 16/10/2026. Dal 20/10/2026 (#3637) anche perché un rilascio
    # non si installa da solo, una volta per versione: rinviato (un'altra sessione resta aperta),
    # bloccato-firma, bloccato-verifica, bloccato-storia, bloccato-versione, manuale.
    "aggiorna": re.compile(r"^(applicato|conflitto|fallito|rifiutato|indietro|scartato|automatico|rinviato|bloccato-firma|bloccato-verifica|bloccato-storia|bloccato-versione|manuale)$"),
    "segnalazione": re.compile(r"^(problema|proposta|integrazione)$"),
    # Da hooks/deriva.py: un `insieme:<n>` apre l'elenco corrente. Dei file solo la posizione
    # nel repository di Arturo, relativa e senza "..": è pubblica, non dice niente dei file della persona.
    "deriva": re.compile(r"^(insieme:\d{1,3}|hook:[a-z0-9_.-]{1,60}|file:(?!.*\.\.)((agents|bin|commands|docs|firme|hooks|output-styles|server|shared"
                         r"|skills|tests|tools|\.github)/[A-Za-z0-9_./-]{1,70}|[A-Za-z0-9_.-]{1,40}))$"),
    "config": re.compile(r"^rotta-(settings|conflitto|rebase|hook)$"),
    # Dal 15/10/2026, per il miglioramento di Arturo. In coda: l'ordine è lo stesso del server (M09).
    "setup": re.compile(r"^(fase:(10|[0-9][a-z]?)|fine)$"),
    "chiede": re.compile(r"^[a-z0-9_.-]{1,60}$"),
    "confermata": re.compile(r"^[a-z0-9_.-]{1,60}$"),
    "errore": re.compile(r"^[a-z0-9_.-]{1,60}$"),
    "claude": re.compile(r"^\d{1,3}\.\d{1,3}\.\d{1,4}$"),
    # Dal 3/11/2026 (#4540), il "come" dell'uso: alla chiusura della sessione la sua durata e i messaggi
    # della persona, solo in fasce larghe, e una volta per sessione ogni skill usata (fine_sessione).
    "durata": re.compile(r"^(<5m|5-30m|30m-2h|>2h)$"),
    "turni": re.compile(r"^(1|2-5|6-20|>20)$"),
    "skill": re.compile(r"^[a-z0-9-]{1,40}$"),
    # Dal 3/11/2026: il nome di un banco delle guardie diventato rosso su questo computer
    # (tests/banchi-avvio.sh), solo quando l'elenco dei rossi cambia. Alla persona non si dice più.
    "banchi": re.compile(r"^test[a-z0-9_-]{1,56}\.py$"),
}
# Le guardie di Arturo che parlano alla telemetria: quelle che bash-dispatcher.sh lancia con run_guard,
# più web-egress-guard.py e protect_claude_md.py, che chiamano chiede da sole. Un nome fuori elenco non
# si registra: un hook della persona con un nome suo, o un client modificato, non fa uscire uno slug
# parlante (24/10/2026). Lo stesso elenco sta in server/logica.js; il banco TF03 (tests/test_telemetria_f1_2026_10_24.py) lo confronta col repository.
GUARDIE = frozenset({"block-dangerous.py", "comms-guard.py", "commit-secret-gate.py", "data-guard.py", "exfil-guard.py",
                     "gh-destructive-guard.py", "protect_claude_md.py", "web-egress-guard.py"})
# Le regole che una guardia può aggiungere al nome in chiede e confermata, come <guardia>.<regola>.
# block-dangerous: le regole di _ask() nel suo codice. commit-secret-gate: la famiglia del segreto, mai
# il fornitore (24/10/2026: "google-api-key" diceva quale servizio usa la persona), e i tre casi senza
# segreto (scaduta, repo-ignoto, scansione-fallita). Una regola fuori elenco cade, e resta il solo nome
# della guardia.
FAMIGLIE_SEGRETI = ("segreto-cloud", "segreto-token", "segreto-password", "segreto-chiave-privata", "segreto-altro")
REGOLE = {
    "block-dangerous.py": frozenset({"avvio-automatico", "claude-md", "config", "docker-volumi", "find-delete", "git-clean",
                                     "rm-cartella", "rm-ignoto", "rm-illeggibile", "rm-protetto", "rm-xargs",
                                     "rmtree-cartella", "rmtree-illeggibile", "rmtree-variabile", "sblocco",
                                     "sblocco-claude-md", "sed-w", "sed-e", "segreto", "git-ramo", "git-destinazione",
                                     "git-stash", "git-amend"}),
    "commit-secret-gate.py": frozenset(FAMIGLIE_SEGRETI + ("scaduta", "repo-ignoto", "scansione-fallita")),
}
# La promessa sulla telemetria cambia di versione quando cambia cosa esce. A una versione nuova
# l'avviso torna una volta, anche a chi aveva già visto la precedente. 3: senza le tappe (16/10/2026).
# 4: gli aggiornamenti installati da soli alla chiusura si contano a parte (16/10/2026, #3482).
# 5: gli aggiornamenti che non partono da soli dicono perché, una volta per versione (20/10/2026, #3637).
# 6: le conferme di block-dangerous e di commit-secret-gate dicono quale regola ha chiesto (22-23/10/2026, #3798).
# 7: esce di meno (24/10/2026). Di commit-secret-gate la famiglia del segreto, non il fornitore; di un file
# in conflitto che non è di Arturo solo `file:altro`; un comando della persona diventa `altro`. Le
# conferme contano anche su Monitor e dopo un comando fallito. Come versione esce solo un tag di rilascio di
# Arturo, mai un tag della persona. Il README non dice più "non legato a te".
# 8: escono la durata della sessione e i messaggi della persona in fasce, e le skill di Arturo usate (3/11/2026, #4540).
# 9: esce il nome di un banco delle guardie diventato rosso, che alla persona non si dice più (3/11/2026).
PROMESSA = 9
# I comandi di Arturo, gli unici di cui parte il nome. Un comando scritto dalla persona in
# ~/.claude/commands/ ha un nome suo: esce come `altro`, che conta l'uso senza dire il nome (24/10/2026).
# Il banco M10 controlla che l'elenco coincida con commands/ del repository.
COMANDI = frozenset({"aggiorna", "creaskill", "diagnosi", "fine", "guidami", "inizio", "novita", "proponi", "segnala",
                     "setup", "sparring"})
# Le skill di Arturo, le uniche di cui parte il nome (3/11/2026, #4540). Una skill della persona o di un plugin
# esce come `altro`, come un comando. Il banco TS01 (tests/test_telemetria_fase2_2026_11_03.py) controlla che
# l'elenco coincida con skills/ del repository e con SKILL in server/logica.js.
SKILL = frozenset({"apri", "cache-fredda", "concetti", "dafare", "italiano-semplificato", "prompt-master",
                   "redazione-segreti", "rotazione", "system-audit", "testata", "todo"})
# Un transcript più grande non si legge alla chiusura: la sessione esce senza durata, turni e skill.
TRANSCRIPT_MASSIMO = 64 * 1024 * 1024
# Le sessioni già contate da fine_sessione: una sessione ripresa con --resume e chiusa di nuovo non si conta due volte.
SESSIONI_RICORDATE = 50
OGNI = 6 * 3600         # secondi fra due invii automatici
CODA_MASSIMA = 2000      # righe: oltre, gli eventi nuovi si perdono finché la coda non parte
LOTTO = 500
SPENTI = {"0", "no", "off", "false", "spenta"}
# I tag dei rilasci di Arturo: v0.2.0, v0.2.1 dal 3/11/2026. Prima erano date (v2026-10-19, v2026-10-19.2), e il
# server le traduce nel loro numero. La stessa forma di rilascio() in server/logica.js.
RILASCIO = re.compile(r"v\d{1,4}\.\d{1,4}\.\d{1,6}|v\d{4}-\d{2}-\d{2}(\.\d+)?")
# Solo i tag con la forma di un rilascio: un tag della persona come "vacanze-rossi" non copre quello di Arturo.
TAG_RILASCIO = ("v[0-9]*.[0-9]*.[0-9]*", "v[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]*")

AIUTO = f"""arturo telemetria: gli eventi d'uso che Arturo manda a chi lo mantiene, per migliorarsi.

  stato          accesa o spenta, e perché
  mostra         l'id di questa installazione e gli eventi in coda, così come partono
  spegni         la spegne e svuota la coda
  accendi        la riaccende
  invia          manda adesso la coda e le segnalazioni in attesa
  segnalazioni   manda adesso solo le segnalazioni in attesa

Escono solo questi eventi, con il giorno e mai l'ora: {", ".join(EVENTI)}.
Dei file di Arturo modificati o in conflitto solo la posizione nel repository di Arturo, che è
pubblica; un file tuo esce come "file:altro". Delle guardie, dei comandi e delle skill solo i nomi
di Arturo: un comando o una skill tua esce come "altro", di un segreto fermato in un commit solo la
famiglia, mai il servizio. Come versione esce solo il rilascio di Arturo installato, mai un tuo tag.
Di ogni sessione, alla chiusura, solo la durata e quanti messaggi hai scritto, in fasce larghe:
meno di 5 minuti, fino a 30, fino a 2 ore, oltre; 1, da 2 a 5, da 6 a 20, oltre 20 messaggi.
Mai prompt, file tuoi, percorsi del tuo computer, nomi, risposte o testi.
L'id è casuale, ma chi mantiene Arturo può sapere chi c'è dietro se ti conosce: non sono dati
anonimi. Cosa si tiene, per quanto e i tuoi diritti: docs/privacy.md.
Server: {URL} (codice in server/). Si spegne anche con ARTURO_TELEMETRIA=0 o DO_NOT_TRACK=1.
Da una HOME in una cartella temporanea, un banco di prova, non parte niente verso questo server:
gli eventi vanno solo a un server indicato con ARTURO_TELEMETRIA_URL."""


def file_stato() -> Path:
    return Path.home() / ".claude" / "session-env" / "telemetria.json"


def file_attese() -> Path:
    """Le conferme chieste da una guardia e non ancora eseguite: tool_use_id -> guardia."""
    return Path.home() / ".claude" / "session-env" / "telemetria-attese.json"


def file_coda() -> Path:
    return Path.home() / ".claude" / "data" / "telemetria" / "coda.jsonl"


def cartella_attesa() -> Path:
    return Path.home() / ".claude" / "data" / "segnalazioni"


def home_di_prova() -> bool:
    """Una HOME dentro una cartella temporanea è un banco di prova, non una persona."""
    home = Path.home().resolve()
    for radice in (tempfile.gettempdir(), "/tmp", "/var/folders"):
        try:
            home.relative_to(Path(radice).resolve())
            return True
        except (ValueError, OSError):
            continue
    return False


def url() -> str:
    # Un test lanciato da solo eredita la telemetria accesa: il 16/10/2026 quattro prove sono arrivate
    # al server come installazioni nuove. Da una HOME di prova parte solo verso un server indicato a mano.
    scelto = os.environ.get("ARTURO_TELEMETRIA_URL", "").strip()
    if scelto:
        return scelto.rstrip("/")
    return "http://127.0.0.1:9" if home_di_prova() else URL


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
    """Il rilascio di Arturo installato: l'ultimo tag v* raggiungibile, senza i commit della persona.
    Solo i tag di Arturo (v*): un tag della persona come "backup/prima" fa rifiutare dal server ogni lotto
    (VERSIONE in server/logica.js), e con i lotti si perdono anche gli avvisi delle config rotte (17/10/2026).
    Senza --abbrev=0 la versione era "v2026-10-17-94-g03ee13d", con l'hash del repository privato di sync:
    il riepilogo non diceva chi era sull'ultimo rilascio (19/10/2026, #3613).
    Dal 24/10/2026 vale solo la forma dei rilasci di Arturo (RILASCIO, la stessa di rilascio() in
    server/logica.js): v* prendeva anche un tag della persona come "vacanze-rossi", che arrivava fino a
    Telegram e al recap. Un tag con la data e un nome suo dopo ("v2026-10-20-rossi") dà "sconosciuta".
    Dal 3/11/2026 il rilascio è un numero (v0.2.0). Il commit di un rilascio a data porta anche il suo numero, con
    un tag più recente, e git describe sceglie il numero."""
    match = [x for t in TAG_RILASCIO for x in ("--match", t)]
    try:
        r = subprocess.run(["git", "-C", str(Path.home() / ".claude"), "describe", "--tags", "--abbrev=0", *match],
                           capture_output=True, text=True, timeout=3)
        v = r.stdout.strip() if r.returncode == 0 else ""
        return v if RILASCIO.fullmatch(v) else "sconosciuta"
    except (OSError, subprocess.SubprocessError):
        return "sconosciuta"


def sistema() -> str:
    nome = platform.system()
    return nome if nome in ("Darwin", "Linux", "Windows") else "altro"


def normalizza(evento: str, valore: str):
    """Il valore che parte per questo evento, o None se non parte. La forma la decide EVENTI; poi le
    liste chiuse (24/10/2026): un comando fuori da COMANDI diventa `altro`, una guardia fuori da
    GUARDIE non parte, una regola fuori da REGOLE cade e resta il nome della guardia."""
    regola = EVENTI.get(evento)
    if not regola or not isinstance(valore, str) or not regola.fullmatch(valore):
        return None
    if evento == "comando":
        return valore if valore in COMANDI else "altro"
    if evento == "skill":
        return valore if valore in SKILL else "altro"
    if evento in ("guardia", "errore"):
        return valore if valore in GUARDIE else None
    if evento in ("chiede", "confermata"):
        if valore in GUARDIE:
            return valore
        guardia = next((g for g in GUARDIE if valore.startswith(g + ".")), None)
        if guardia is None:
            return None
        return valore if valore[len(guardia) + 1:] in REGOLE.get(guardia, ()) else guardia
    return valore


def valido(evento: str, valore: str) -> bool:
    return normalizza(evento, valore) is not None


def ref_di_arturo(radice) -> str | None:
    """Il ref che dice cosa è Arturo: upstream/main se la persona ha un remote upstream (il suo repository
    è origin), altrimenti origin/main. None se manca. Con un upstream dichiarato ma mai scaricato non
    ripiega su origin/main, che lì è il repository della persona (24/10/2026)."""
    def git(*argomenti) -> int:
        try:
            return subprocess.run(["git", "-C", str(radice), *argomenti], capture_output=True, timeout=10).returncode
        except (OSError, subprocess.SubprocessError):
            return 1
    ha_upstream = git("config", "--get", "remote.upstream.url") == 0
    ref = "upstream/main" if ha_upstream else "origin/main"
    return ref if git("rev-parse", "--verify", "--quiet", ref + "^{commit}") == 0 else None


def file_di_arturo(radice=None, ref=None):
    """I percorsi versionati di Arturo, o None se git non risponde.

    Arturo è il ref che arriva (`ref`, da bin/aggiorna-applica.sh) oppure ref_di_arturo, come in
    hooks/deriva.py. Senza un ref di Arturo torna None, e ogni file diventa `file:altro`: fino al
    24/10/2026 qui si ripiegava su git ls-files, che comprende i file che la persona ha versionato nel
    suo repository, e skills/clienti-rossi/SKILL.md usciva col suo nome."""
    radice = str(radice or Path.home() / ".claude")
    if ref and ref.startswith("-"):  # un ref che git leggerebbe come opzione non vale
        ref = None
    chiave = (radice, ref or "")
    if chiave in _MANIFESTI:
        return _MANIFESTI[chiave]
    elenco = None
    scelto = ref or ref_di_arturo(radice)
    if scelto:
        try:
            r = subprocess.run(["git", "-C", radice, "ls-tree", "-r", "-z", "--name-only", scelto], capture_output=True, timeout=10)
            if r.returncode == 0:
                elenco = frozenset(p for p in r.stdout.decode("utf-8", "replace").split("\0") if p)
        except (OSError, subprocess.SubprocessError):
            pass
    _MANIFESTI[chiave] = elenco
    return elenco


_MANIFESTI = {}


def percorso_pubblico(percorso: str, di_arturo=None, radice=None, ref=None) -> str:
    """Il valore `file:` della deriva per un percorso dentro la config: `file:<percorso>` se è un file
    versionato di Arturo con la forma della deriva, altrimenti `file:altro`.

    Il filtro unico di hooks/deriva.py e di segna_conflitti in bin/aggiorna-applica.sh. Fino al
    24/10/2026 bastava la forma: un conflitto su skills/clienti-rossi/SKILL.md, una skill della persona,
    mandava il nome del cliente. `di_arturo` è l'elenco dei file di Arturo se chi chiama l'ha già (deriva.py
    legge l'albero di Arturo); senza, lo legge file_di_arturo. Se git non risponde, o non c'è un ref di Arturo,
    tutto è `file:altro`."""
    if not isinstance(percorso, str) or percorso == "altro" or not EVENTI["deriva"].fullmatch("file:" + percorso):
        return "file:altro"
    elenco = di_arturo if di_arturo is not None else file_di_arturo(radice, ref)
    return f"file:{percorso}" if elenco and percorso in elenco else "file:altro"


def _registra(evento: str, valore: str = ""):
    """Aggiunge un evento alla coda e torna il valore scritto, o None. Non usa la rete e non solleva mai."""
    try:
        valore = normalizza(evento, valore)
        if perche_spenta() or valore is None:
            return None
        coda = file_coda()
        coda.parent.mkdir(parents=True, exist_ok=True)
        with ts.Lucchetto(coda):
            # Oltre CODA_MASSIMA righe gli eventi nuovi si perdono finché la coda non parte, e niente lo
            # conta. Il contatore dei persi è della fase F5 del piano del 24/10/2026, non di questa.
            if coda.exists():
                with coda.open(encoding="utf-8") as f:
                    if sum(1 for _ in f) >= CODA_MASSIMA:
                        return None
            with coda.open("a", encoding="utf-8") as f:
                f.write(json.dumps({"giorno": ts.oggi().isoformat(), "evento": evento, "valore": valore}) + "\n")
        return valore
    except Exception:  # noqa: BLE001 - un hook non si ferma mai per la telemetria
        return None


def registra(evento: str, valore: str = "") -> bool:
    """Aggiunge un evento alla coda. Non usa la rete e non solleva mai."""
    return _registra(evento, valore) is not None


def registra_conflitti(percorsi, ref=None, radice=None) -> int:
    """I file in conflitto di un aggiornamento, come righe `file:` della deriva, al massimo 20. Ognuno
    passa da percorso_pubblico: esce solo un file di Arturo. Torna quante righe ha scritto."""
    scritte = 0
    for p in [p.strip() for p in percorsi if p.strip()][:20]:
        scritte += registra("deriva", percorso_pubblico(p, radice=radice, ref=ref))
    return scritte


def _evento_valido(riga: str):
    """L'evento di una riga della coda, o None se la riga non parte (rotta, o di un evento tolto)."""
    try:
        e = json.loads(riga)
    except ValueError:
        return None
    if not isinstance(e, dict):
        return None
    # Una riga scritta da una versione di prima parte come la scriverebbe questa (24/10/2026): la regola
    # di un segreto col fornitore perde la regola, un file della persona diventa file:altro.
    valore = normalizza(e.get("evento", ""), e.get("valore", ""))
    if valore is None:
        return None
    if e["evento"] == "deriva" and valore.startswith("file:"):
        valore = percorso_pubblico(valore[5:])
    return {"giorno": str(e.get("giorno", ""))[:10], "evento": e["evento"], "valore": valore}


def leggi_coda() -> list:
    try:
        righe = file_coda().read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeDecodeError):
        return []
    return [e for e in map(_evento_valido, righe) if e]


def _scrivi_coda_atomica(righe: list) -> None:
    """Come ts.scrivi_json_atomico: chi legge trova la coda vecchia o la nuova, mai mezza."""
    coda = file_coda()
    fd, temporaneo = tempfile.mkstemp(prefix=f".{coda.name}.", suffix=".tmp", dir=str(coda.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
            f.write("".join(r + "\n" for r in righe))
            f.flush()
            os.fsync(f.fileno())
        os.replace(temporaneo, str(coda))
    except BaseException:
        try:
            os.unlink(temporaneo)
        except FileNotFoundError:
            pass
        raise


def posta_json(rotta: str, dati: dict, timeout: float = 5) -> tuple:
    """POST JSON. Torna (status HTTP, risposta in JSON): (0, {}) se la rete non risponde, {} se la
    risposta non è un oggetto JSON. /segnala ne legge il numero della segnalazione."""
    corpo = json.dumps(dati, ensure_ascii=False).encode("utf-8")
    richiesta = urllib.request.Request(url() + rotta, data=corpo, method="POST",
                                       headers={"content-type": "application/json", "user-agent": "arturo"})
    try:
        with urllib.request.urlopen(richiesta, timeout=timeout) as r:
            status = r.status
            try:
                risposta = json.loads(r.read(65536).decode("utf-8"))
            except (OSError, ValueError, UnicodeDecodeError):
                risposta = {}
            return status, risposta if isinstance(risposta, dict) else {}
    except urllib.error.HTTPError as e:
        return e.code, {}
    except (urllib.error.URLError, OSError, ValueError):
        return 0, {}


def posta(rotta: str, dati: dict, timeout: float = 5) -> int:
    """POST JSON. Torna lo status HTTP, 0 se la rete non risponde."""
    return posta_json(rotta, dati, timeout)[0]


def _segna_numero(attesa: Path, dati: dict, numero) -> None:
    """Una segnalazione partita in differita: la copia .md passa da "in attesa" al suo numero, che
    /segnala stato incrocia con NOVITA.md (Computer Club N.3, 28/10/2026). La copia ha lo stesso
    nome del file in attesa; per quelle di prima del 28/10 vale il titolo."""
    if not isinstance(numero, int) or isinstance(numero, bool) or numero <= 0:
        return
    stessa = attesa.with_name(attesa.name.replace(".attesa.json", ".md"))
    candidate = [stessa] if stessa.exists() else sorted(attesa.parent.glob("*.md"))
    for copia in candidate:
        try:
            testo = copia.read_text(encoding="utf-8")
        except OSError:
            continue
        if not testo.startswith(f"# {dati.get('titolo', '')}\n") or "\nEsito: in attesa" not in testo:
            continue
        testo = re.sub(r"\nEsito: in attesa[^\n]*", f"\nEsito: arrivata a chi mantiene Arturo: è la segnalazione n. {numero}",
                       testo, count=1)
        try:
            copia.write_text(testo, encoding="utf-8")
        except OSError:
            pass
        return


def invia_segnalazioni_in_attesa() -> int:
    """Le segnalazioni approvate ma non partite: sono un sì della persona, partono anche a telemetria spenta."""
    partite = 0
    for f in sorted(cartella_attesa().glob("*.attesa.json")):
        try:
            dati = json.loads(f.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        status, risposta = posta_json("/v1/segnalazioni", dati)
        if 200 <= status < 300:
            _segna_numero(f, dati, risposta.get("numero"))
            f.unlink()
            partite += 1
        elif status in (400, 413):
            f.rename(f.with_name(f.name.replace(".attesa.json", ".rifiutata.json")))
        else:
            break  # rete giù o server pieno: si riprova la volta dopo
    return partite


def versione_claude() -> str:
    """La versione di Claude Code, o "" se non si legge. Gira solo nell'invio in background."""
    eseguibile = shutil.which("claude")
    if not eseguibile:
        return ""
    try:
        r = subprocess.run([eseguibile, "--version"], capture_output=True, text=True, timeout=15,
                           stdin=subprocess.DEVNULL)
    except (OSError, subprocess.SubprocessError):
        return ""
    trovata = re.match(r"\s*(\d{1,3}\.\d{1,3}\.\d{1,4})", r.stdout or "")
    return trovata.group(1) if trovata else ""


def segna_claude() -> None:
    """Registra la versione di Claude Code quando cambia: dice quale versione accompagna un guasto."""
    v = versione_claude()
    if v and v != leggi_stato().get("claude") and registra("claude", v):
        cambia_stato(lambda s: s.__setitem__("claude", v))


def _leggi_attese() -> dict:
    try:
        attese = json.loads(file_attese().read_text(encoding="utf-8"))
        return attese if isinstance(attese, dict) else {}
    except (OSError, ValueError, UnicodeDecodeError):
        return {}


def chiede(guardia: str, uso: str) -> None:
    """Una guardia ha chiesto conferma: registra `chiede` e ricorda la chiamata fino all'esito."""
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,100}", uso or ""):
        return
    guardia = _registra("chiede", guardia)  # il valore com'è uscito: confermata dice lo stesso
    if guardia is None:
        return
    file_attese().parent.mkdir(parents=True, exist_ok=True)
    with ts.Lucchetto(file_attese()):
        attese = _leggi_attese()
        attese[uso] = guardia
        ts.scrivi_json_atomico(file_attese(), dict(list(attese.items())[-50:]))


def esito(dati: dict) -> None:
    """Dal PostToolUse o dal PostToolUseFailure: lo strumento è partito, quindi la persona ha detto sì
    alla guardia. Anche un comando che poi fallisce è un sì: fino al 24/10/2026 il PostToolUseFailure
    non era collegato, e quel sì restava un no nel tasso delle conferme. Dei dati legge solo tool_use_id."""
    uso = dati.get("tool_use_id") if isinstance(dati, dict) else None
    if not isinstance(uso, str) or not file_attese().exists():
        return
    with ts.Lucchetto(file_attese()):
        attese = _leggi_attese()
        guardia = attese.pop(uso, None)
        if guardia is None:
            return
        if attese:
            ts.scrivi_json_atomico(file_attese(), attese)
        else:
            file_attese().unlink()
    registra("confermata", guardia)


def invia(zitto: bool = False) -> tuple:
    """Torna (eventi partiti, segnalazioni partite)."""
    cambia_stato(lambda s: s.__setitem__("ultimo_tentativo", int(time.time())))
    segnalazioni = invia_segnalazioni_in_attesa()
    if perche_spenta():
        return 0, segnalazioni
    if zitto:
        segna_claude()
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
            # Partiti conta righe valide, non righe del file: le righe che non partono (rotte, o di un
            # evento tolto) si scartano, si saltano le prime `partiti` valide e restano quelle
            # registrate nel frattempo. Tagliare per righe grezze rimandava un evento per ogni scartata.
            righe = coda.read_text(encoding="utf-8").splitlines() if coda.exists() else []
            valide = [r for r in righe if _evento_valido(r)]
            _scrivi_coda_atomica(valide[partiti:])
    return partiti, segnalazioni


def _fascia_durata(secondi: float) -> str:
    if secondi < 5 * 60:
        return "<5m"
    if secondi < 30 * 60:
        return "5-30m"
    return "30m-2h" if secondi < 2 * 3600 else ">2h"


def _fascia_turni(turni: int) -> str:
    return "1" if turni == 1 else "2-5" if turni <= 5 else "6-20" if turni <= 20 else ">20"


# I messaggi del transcript che la persona non ha scritto: l'uscita di un comando locale, il messaggio di
# un'altra sessione, l'avviso di un job finito. /clear apre la sessione nuova col suo nome, ma non è una richiesta.
NON_SCRITTI = ("<local-command", "<agent-message", "Another Claude session", "<task-notification", "<system-reminder",
               "<command-name>/clear</command-name>", "Caveat:")
COMANDO_DIGITATO = re.compile(r"<command-name>/([a-z0-9-]{1,40})</command-name>")


def _secondi(testo) -> float | None:
    if not isinstance(testo, str):
        return None
    try:  # fromisoformat di Python 3.8 non legge la Z finale
        return datetime.fromisoformat(testo.replace("Z", "+00:00")).timestamp()
    except ValueError:
        return None


def leggi_sessione(percorso: Path) -> tuple:
    """Da un transcript di Claude Code: (secondi fra il primo e l'ultimo messaggio, o None; messaggi scritti
    dalla persona; skill usate, in ordine e senza doppi). Del transcript non esce niente altro: i testi servono
    solo a riconoscere un messaggio della persona e il nome di una skill, e restano qui."""
    primo = ultimo = None
    turni = 0
    skill: list = []
    with percorso.open(encoding="utf-8", errors="replace") as f:
        for riga in f:
            try:
                d = json.loads(riga)
            except ValueError:
                continue
            if not isinstance(d, dict) or d.get("isSidechain") or d.get("type") not in ("user", "assistant"):
                continue
            t = _secondi(d.get("timestamp"))
            if t is not None:
                primo = t if primo is None else min(primo, t)
                ultimo = t if ultimo is None else max(ultimo, t)
            messaggio = d.get("message")
            contenuto = messaggio.get("content") if isinstance(messaggio, dict) else None
            blocchi = contenuto if isinstance(contenuto, list) else []
            if d["type"] == "user" and not d.get("isMeta"):
                testi = [contenuto] if isinstance(contenuto, str) else \
                    [b.get("text") for b in blocchi if isinstance(b, dict) and b.get("type") == "text" and isinstance(b.get("text"), str)]
                scritti = [x for x in testi if x.strip() and not x.lstrip().startswith(NON_SCRITTI)]
                immagine = any(isinstance(b, dict) and b.get("type") == "image" for b in blocchi)
                if scritti or immagine:
                    turni += 1
                for x in scritti:  # una skill di Arturo lanciata con la barra, come /todo
                    for nome in COMANDO_DIGITATO.findall(x):
                        if nome in SKILL and nome not in skill:
                            skill.append(nome)
            elif d["type"] == "assistant":
                for b in blocchi:
                    if isinstance(b, dict) and b.get("type") == "tool_use" and b.get("name") == "Skill" \
                            and isinstance(b.get("input"), dict) and isinstance(b["input"].get("skill"), str):
                        nome = b["input"]["skill"].lstrip("/")
                        nome = nome if nome in SKILL else "altro"
                        if nome not in skill:
                            skill.append(nome)
    secondi = ultimo - primo if primo is not None and ultimo is not None else None
    return secondi, turni, skill


def fine_sessione(dati: dict) -> None:
    """Lo chiama session-end.sh in background, col JSON dell'hook: registra durata, turni e skill della sessione
    che chiude. Una sessione senza messaggi della persona non registra niente. Non usa la rete e non solleva."""
    try:
        if perche_spenta() or not isinstance(dati, dict):
            return
        sessione, percorso = dati.get("session_id"), dati.get("transcript_path")
        if not isinstance(sessione, str) or not sessione or not isinstance(percorso, str) or not percorso:
            return
        if sessione in (leggi_stato().get("sessioni_chiuse") or []):
            return
        transcript = Path(percorso)
        if not transcript.is_file() or transcript.stat().st_size > TRANSCRIPT_MASSIMO:
            return
        secondi, turni, skill = leggi_sessione(transcript)
        cambia_stato(lambda s: s.__setitem__("sessioni_chiuse", (
            [x for x in (s.get("sessioni_chiuse") or []) if isinstance(x, str) and x != sessione] + [sessione])[-SESSIONI_RICORDATE:]))
        if not turni:
            return
        if secondi is not None:
            registra("durata", _fascia_durata(secondi))
        registra("turni", _fascia_turni(turni))
        for nome in skill:
            registra("skill", nome)
    except Exception:  # noqa: BLE001 - la chiusura di una sessione non si ferma mai per la telemetria
        pass


def avvio() -> int:
    """Lo chiama session-start.sh: registra la sessione, stampa l'avviso una volta, lancia l'invio."""
    try:
        stato = leggi_stato()
        if perche_spenta(stato):
            if any(cartella_attesa().glob("*.attesa.json")):
                _invio_in_background(solo_segnalazioni=True)
            return 0
        registra("sessione")
        if stato.get("avviso_promessa") != PROMESSA:
            nuova = " Cosa esce è cambiato da quando l'ha letto: diglielo." if stato.get("avviso") else ""
            print("TELEMETRIA: Arturo manda a chi lo mantiene eventi d'uso con un id casuale: versione di Arturo e di "
                  "Claude Code, sistema, comandi e skill di Arturo usati (uno della persona conta come altro), durata della sessione e "
                  "numero dei messaggi della persona in fasce larghe, guardie che bloccano o chiedono, con la regola che chiede "
                  "(di un segreto solo la famiglia), e se la persona conferma, guardie che si rompono, banchi di prova delle guardie rossi, fase di /setup raggiunta, esiti di /aggiorna e degli "
                  "aggiornamenti automatici, perché un aggiornamento automatico non parte, file e hook di Arturo cambiati, spenti o in conflitto "
                  "(un file della persona conta come altro). Mai prompt, file, nomi o testi. L'id è casuale, ma chi mantiene Arturo può "
                  "sapere chi c'è dietro se conosce la persona: non sono dati anonimi (docs/privacy.md)."
                  + nuova + " Dillo alla persona una volta, in due righe, con il perché: con questi dati Arturo "
                  "corregge ogni settimana i punti dove le persone si bloccano. "
                  "Si spegne con: python3 ~/.claude/bin/arturo telemetria spegni")
            cambia_stato(lambda s: s.update(avviso=ts.oggi().isoformat(), avviso_promessa=PROMESSA))
        # Una segnalazione in attesa parte alla sessione dopo, come promette /segnala, senza aspettare le 6 ore
        # dell'invio degli eventi (Liliana, 27/10/2026). Parte da sola: gli eventi aspettano le 6 ore promesse
        # da docs/privacy.md (#4073).
        ultimo = stato.get("ultimo_tentativo")
        if not isinstance(ultimo, int) or time.time() - ultimo > OGNI:
            _invio_in_background()
        elif any(cartella_attesa().glob("*.attesa.json")):
            _invio_in_background(solo_segnalazioni=True)
    except Exception:  # noqa: BLE001
        pass
    return 0


def _invio_in_background(solo_segnalazioni: bool = False) -> None:
    opzioni = {"stdin": subprocess.DEVNULL, "stdout": subprocess.DEVNULL, "stderr": subprocess.DEVNULL}
    if os.name == "nt":
        opzioni["creationflags"] = 0x00000008 | 0x00000200  # DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP
    else:
        opzioni["start_new_session"] = True
    comando = ["segnalazioni"] if solo_segnalazioni else ["invia", "--zitto"]
    subprocess.Popen([sys.executable, os.path.realpath(__file__), *comando], **opzioni)


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
    if comando == "conflitti" and len(resto) <= 2:
        # bin/aggiorna-applica.sh: i file in conflitto sullo stdin, uno per riga; gli argomenti sono il ref
        # di Arturo che arriva e la config. Un telemetria.py di prima non ha questo comando e non registra niente.
        try:
            registra_conflitti(sys.stdin.buffer.read().decode("utf-8", "replace").splitlines(),
                               (resto[0] if resto else "") or None, resto[1] if len(resto) == 2 else None)
        except Exception:  # noqa: BLE001 - un aggiornamento non si ferma mai per la telemetria
            pass
        return 0
    if comando == "fine" and not resto:
        try:  # hooks/session-end.sh, col JSON dell'hook sullo stdin
            fine_sessione(json.loads(sys.stdin.buffer.read().decode("utf-8", "replace") or "{}"))
        except Exception:  # noqa: BLE001 - un hook non si ferma mai per la telemetria
            pass
        return 0
    if comando == "chiede" and len(resto) == 2:
        chiede(resto[0], resto[1])
        return 0
    if comando == "esito" and not resto:
        try:
            esito(json.loads(sys.stdin.buffer.read().decode("utf-8") or "{}"))
        except Exception:  # noqa: BLE001 - un hook non si ferma mai per la telemetria
            pass
        return 0
    if comando == "invia" and resto in ([], ["--zitto"]):
        partiti, segnalazioni = invia(zitto=bool(resto))
        if not resto:
            spenta = perche_spenta()
            print(f"Eventi partiti: {partiti}" + (f" (telemetria spenta: {spenta})" if spenta else "")
                  + f". Segnalazioni partite: {segnalazioni}.")
        return 0
    if comando == "segnalazioni" and not resto:
        print(f"Segnalazioni partite: {invia_segnalazioni_in_attesa()}.")
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
        for f in (file_coda(), file_attese()):
            try:
                f.unlink()
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
    print(f"Errore: comando sconosciuto: \"{' '.join(argv)}\"\n\n{AIUTO}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    for flusso in (sys.stdout, sys.stderr):  # su Windows la pipe è in cp1252, Claude legge UTF-8
        try:
            flusso.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass
    raise SystemExit(main(sys.argv[1:]))
