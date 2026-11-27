#!/usr/bin/env python3
"""Il titolo di una sessione: poche parole in italiano che dicono il lavoro in corso.

Gira come hook asincrono su UserPromptSubmit e su Stop. Legge l'evento da stdin e scrive
~/.claude/cache/titolo/<sessione>.json: {"titolo", "fonte", "quando", "peso"}.
  - UserPromptSubmit, solo se la sessione non ha ancora un titolo: il compito di /inizio (il testo dopo
    " -- ") o la prima richiesta, accorciata. Fonte "avvio", nessun modello.
  - Stop: un modello piccolo (claude -p --model haiku, senza strumenti, hook, MCP, CLAUDE.md e memoria)
    legge il progetto, le ultime richieste, l'ultima risposta e l'ultima azione, e scrive il titolo.
    Fonte "modello". Al massimo una volta ogni OGNI secondi per sessione, e solo se la trascrizione è
    cresciuta. Una risposta che non è una riga da 2 a 60 caratteri si scarta: resta il titolo di prima.
  - Fonte "persona": il nome che la persona ha scritto dalla finestra di Volta (volta_sonda.py rinomina,
    #5292). Nessuno dei due eventi lo riscrive, e resta finché la sessione ha una trascrizione.
  - La sintesi (12/11/2026: "5 parole massimo per descrivere che cosa sta succedendo nella
    sessione, aggiornati costantemente"): la stessa chiamata dà anche la riga ADESSO, da 2 a 5 parole,
    nel campo "sintesi" con "quando_sintesi" e "peso_sintesi". Si rifà ogni OGNI_SINTESI secondi se la
    trascrizione è cresciuta, anche su PostToolUse, così cambia durante un turno lungo; il titolo resta
    ogni OGNI secondi. Vale anche sotto un nome scritto dalla persona: lì cambia solo la sintesi. Due
    hook partiti insieme non chiamano il modello due volte: il primo segna "chiede" nel file.
  - Il progetto (14/11/2026, la persona: "il progetto associato alle sessioni non viene aggiornato"): la stessa
    chiamata sceglie il progetto dal contenuto fra quelli noti (`arturo progetti --json`, cioè
    bin/progetti.py accanto a questo hook, letto al più una volta all'ora in cache/titolo-progetti.json).
    Scrive "progetto" e "candidato": il primo verdetto vale subito, un cambio solo se il modello lo ripete
    al giro dopo, e "nessuno" non toglie mai un progetto. Vale anche sotto un nome scritto dalla persona.
    Lo legge volta_sonda.py, sopra un file scritto e la cartella, sotto /inizio e la scelta della persona.
    ARTURO_TITOLI_PROGETTI=<file json> dà l'elenco (banchi). Portato dalla copia della config (#6717).
Il file è a parte da quello della scheda (cache/scheda), che scheda-terminale.py riscrive per intero e
toglie a fine sessione. Lo leggono la sonda di Volta (volta_sonda.py) e chi elenca le sessioni.
Richiesta del 10/11/2026: aprire Volta e capire dal titolo cosa fa ogni sessione.
Si spegne con ARTURO_TITOLI=0. ARTURO_TITOLI_OGNI cambia l'intervallo in secondi (prove). La chiamata
al modello porta ARTURO_TITOLO_FIGLIO=1: se un hook partisse dentro di lei, questo esce subito.
Misurato il 10/11/2026: 6 secondi e circa 4.000 token di Haiku per titolo, nessuna sessione in più
in claude agents. Ogni errore: exit 0. Solo libreria standard, Python 3.8+.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))
from radici import radice_orsa  # noqa: E402

OGNI = 600           # secondi fra due titoli del modello per la stessa sessione
OGNI_SINTESI = 90    # secondi fra due sintesi (cosa succede adesso) per la stessa sessione
PAROLE = 5           # parole al più nella sintesi
TETTO = 45           # secondi: oltre, la chiamata al modello si lascia perdere
VECCHIO = 7 * 24 * 3600
LUNGO = 60           # caratteri: il titolo sta in una riga della barra di Volta
CODA = 3000000       # byte della trascrizione letti dal fondo, come la sonda di Volta
CONTESTO = 2000      # caratteri passati al modello
ATTESA_BIN = 6       # secondi di attesa del link di claude mentre npm lo reinstalla (#6682, come la config)
ISTRUZIONE = (
    "Dai un titolo a una sessione di lavoro fra una persona e un assistente, per un elenco che la persona "
    "scorre con l'occhio. Ricevi degli appunti: progetto, ultime richieste della persona, ultimo comando e "
    "ultima risposta dell'assistente, a volte il titolo di prima. Se il lavoro è lo stesso di prima e il "
    "titolo di prima lo dice bene, ripetilo uguale. Il titolo dice l'obiettivo del lavoro in corso, cioè che cosa la "
    "persona sta ottenendo: di solito sta nell'ultima richiesta lunga, non nell'ultimo comando lanciato. "
    "Da 3 a 7 parole in italiano, una frase naturale con articoli e preposizioni, che comincia col nome "
    "dell'azione o della cosa. Esempi: Prova dei gesti sulle sessioni. Preventivo per il libro dei "
    "vent'anni. Correzione del banco dei test. Titoli chiari per le sessioni. "
    "Il titolo va senza punto finale, senza virgolette, senza due punti e senza numeri di task. "
    "Poi una seconda cosa: cosa sta succedendo adesso nella sessione, da 2 a 5 parole in italiano, al "
    "presente, dal punto di vista dell'assistente. Esempi: Scrive la testata nuova. Lancia il banco dei test. "
    "Aspetta la tua risposta. Legge la posta di oggi. "
    "Poi una terza cosa: il progetto del lavoro fra i progetti noti degli appunti, quello di cui parla il "
    "lavoro, anche se i file stanno nella cartella di un altro: il progetto è il cliente o il lavoro, non lo "
    "strumento usato per farlo. Scrivi lo slug esatto dell'elenco, oppure nessuno se non è chiaro. "
    "Rispondi con tre righe e niente altro, senza punto finale, virgolette e premesse:\n"
    "TITOLO: <il titolo>\n"
    "ADESSO: <cosa succede adesso>\n"
    "PROGETTO: <slug oppure nessuno>"
)
PROGETTI_ORA = 3600  # secondi: l'elenco dei progetti noti si rilegge al più una volta all'ora
PROGETTI_MAX = 80    # i progetti più recenti passati al modello (l'elenco di arturo è dal più recente)
DESCRIZIONE = 90     # caratteri della descrizione di ogni progetto negli appunti
RIASSUNTO = 700      # caratteri del riassunto di una compattazione negli appunti
COMPATTATA = "This session is being continued from a previous conversation"
TESTA = 512000       # byte letti dall'inizio della trascrizione per la prima richiesta
SLUG = re.compile(r"[a-z0-9][a-z0-9-]{0,59}")
INIZIO = re.compile(r"^\s*/inizio\b(.*)$", re.S)
ARGOMENTI = re.compile(r"<command-args>(.*?)</command-args>", re.S)
COMANDO = re.compile(r"<command-name>(.*?)</command-name>", re.S)


def cartella() -> Path:
    return Path(str(radice_orsa())) / "cache" / "titolo"


def leggi(f: Path) -> dict:
    try:
        d = json.loads(f.read_text(encoding="utf-8"))
        return d if isinstance(d, dict) else {}
    except (OSError, ValueError):
        return {}


def scrivi(f: Path, dati: dict) -> None:
    f.parent.mkdir(parents=True, exist_ok=True)
    provvisorio = f.with_name(f"{f.stem}.{os.getpid()}.tmp")
    provvisorio.write_text(json.dumps(dati), encoding="utf-8")
    os.replace(str(provvisorio), str(f))


def accorcia(testo: str, lungo: int = LUNGO) -> str:
    t = re.sub(r"\s+", " ", testo or "").strip()
    if len(t) <= lungo:
        return t
    return re.sub(r"\s+\S*$", "", t[:lungo]).rstrip(" ,;:(") + "…"


def compito(prompt: str) -> str:
    """Il titolo di partenza da una richiesta: di "/inizio x -- --rotazione Fare Y" resta "Fare Y", di
    "/inizio x fare y" resta tutto il testo dopo il comando, di un altro comando i suoi argomenti."""
    p = (prompt or "").strip()
    m = INIZIO.match(p)
    if m:
        resto = m.group(1)
        if " -- " in resto:
            resto = resto.split(" -- ", 1)[1]
        p = " ".join(w for w in resto.split() if not w.startswith("--"))
    elif p.startswith("/"):
        p = p.split(None, 1)[1] if len(p.split(None, 1)) > 1 else ""
    p = re.sub(r"\(#\d+\)|#\d+", "", p)
    p = re.sub(r"\s+([,;:.])", r"\1", p)
    # 22/11/2026: "/inizio x -- #6357: fare y" dava il titolo ": fare y". La punteggiatura in testa se ne va.
    return accorcia(re.sub(r"^[\s,;:.·|—–-]+", "", p.split("\n")[0]) if p else "")


def pulito(risposta: str) -> str:
    """Il titolo dentro la risposta del modello, o "" se non è una riga da 2 a LUNGO caratteri. La riga
    "Titolo: …" se c'è, altrimenti la risposta di una riga sola (il formato di prima)."""
    righe = [r.strip() for r in (risposta or "").strip().splitlines() if r.strip()]
    etichettate = [r for r in righe if re.match(r"titolo\s*:", r, re.I)]
    if len(etichettate) == 1:
        righe = etichettate
    elif len(righe) != 1 or re.match(r"progetto\s*:", righe[0], re.I):
        return ""
    t = re.sub(r"^(?:titolo\s*:\s*)", "", righe[0], flags=re.I).strip().strip("\"'`*\u00ab\u00bb\u201c\u201d").strip()
    t = t.rstrip(".").strip()
    return t if 2 <= len(t) <= LUNGO else ""


def sintesi_pulita(testo: str) -> str:
    """La sintesi: da 2 a PAROLE parole su una riga, senza virgolette né punto finale; "" altrimenti."""
    t = (testo or "").strip().strip("\"'`*«»“”").strip().rstrip(".").strip()
    parole = t.split()
    return " ".join(parole) if 2 <= len(parole) <= PAROLE and len(t) <= LUNGO else ""


def due_righe(risposta: str) -> tuple:
    """(titolo, sintesi) dalla risposta del modello: le righe TITOLO: e ADESSO:. Una risposta di una
    riga sola senza etichette vale come titolo (il modello di prima). Ciò che non torna resta ""."""
    righe = [r.strip() for r in (risposta or "").strip().splitlines() if r.strip()]
    titolo = sintesi = ""
    etichette = 0
    for r in righe:
        m = re.match(r"^(titolo|adesso)\s*:\s*(.*)$", r, flags=re.I)
        if not m:
            continue
        etichette += 1
        if m.group(1).lower() == "titolo":
            titolo = pulito(m.group(2))
        else:
            sintesi = sintesi_pulita(m.group(2))
    if not etichette and len(righe) == 1:
        titolo = pulito(righe[0])
    return titolo, sintesi


def progetto_scelto(risposta: str, noti: dict) -> str:
    """Lo slug della riga "Progetto: …" se è un progetto noto (anche per nome alternativo), altrimenti ""."""
    for r in (risposta or "").splitlines():
        m = re.match(r"\s*progetto\s*:\s*(.+)$", r, re.I)
        if m:
            v = m.group(1).strip().strip("\"'`*").strip().lower()
            return noti.get(v, "")
    return ""


def progetti_noti() -> tuple:
    """({nome: slug}, righe): i progetti noti dal più recente, con slug e nomi alternativi, e una riga per
    progetto da dare al modello ("slug: titolo, descrizione"). ({}, []) se non si sa."""
    fonte = os.environ.get("ARTURO_TITOLI_PROGETTI")
    dati = None
    if fonte:
        try:
            dati = json.loads(Path(fonte).read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return {}, []
    else:
        f = cartella().parent / "titolo-progetti.json"
        salvati = leggi(f)
        if time.time() - float(salvati.get("quando") or 0) < PROGETTI_ORA and isinstance(salvati.get("progetti"), list):
            dati = salvati
        else:
            dati = chiedi_progetti()
            if dati is None:
                return {}, []
            try:
                scrivi(f, {"quando": time.time(), "progetti": dati.get("progetti") or []})
            except OSError:
                pass
    out, righe = {}, []
    for p in (dati or {}).get("progetti") or []:
        if not isinstance(p, dict) or not SLUG.fullmatch(str(p.get("slug") or "")) or p["slug"] in out:
            continue
        s = p["slug"]
        out[s] = s
        detto = ", ".join(x for x in (str(p.get("titolo") or "").strip(), accorcia(str(p.get("descrizione") or ""), DESCRIZIONE)) if x)
        righe.append(f"- {s}: {detto}" if detto else f"- {s}")
        for a in p.get("alias") or []:
            if isinstance(a, str) and SLUG.fullmatch(a.lower()):
                out.setdefault(a.lower(), s)
        if len(righe) >= PROGETTI_MAX:
            break
    return out, righe


def chiedi_progetti():
    """`arturo progetti --json` (bin/progetti.py accanto a questo hook), o None."""
    try:
        bin_ = Path(os.path.realpath(__file__)).parent.parent / "bin" / "progetti.py"
        r = subprocess.run([sys.executable, "-B", str(bin_), "--json"], capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=20, env=dict(os.environ, PYTHONIOENCODING="utf-8"))
        d = json.loads(r.stdout) if r.returncode == 0 else None
        return d if isinstance(d, dict) else None
    except (OSError, ValueError, subprocess.SubprocessError):
        return None


def accetta(salvato: dict, verdetto: str) -> tuple:
    """(progetto, candidato) dopo un verdetto del modello. Il primo vale subito; un cambio vale solo se il
    modello lo ripete al giro dopo; un verdetto vuoto non toglie il progetto."""
    prima, candidato = str(salvato.get("progetto") or ""), str(salvato.get("candidato") or "")
    if not verdetto:
        return prima, candidato
    if not prima or verdetto == prima or verdetto == candidato:
        return verdetto, verdetto
    return prima, verdetto


def testo_di(contenuto) -> str:
    if isinstance(contenuto, str):
        return contenuto
    if isinstance(contenuto, list):
        return " ".join(b.get("text", "") for b in contenuto if isinstance(b, dict) and b.get("type") == "text")
    return ""


def richiesta(testo: str) -> str:
    """Una richiesta della persona come l'ha scritta: di un comando restano nome e argomenti, gli
    avvisi che Claude Code accoda (<system-reminder>, notifiche dei job) non sono richieste."""
    t = (testo or "").strip()
    if "<command-name>" in t:
        nome, arg = COMANDO.search(t), ARGOMENTI.search(t)
        t = ((nome.group(1) if nome else "") + " " + (arg.group(1) if arg else "")).strip()
    elif t.startswith("<") or t.startswith("Base directory for this skill"):
        return ""
    return re.sub(r"\s+", " ", t)[:500]


def appunti(trascrizione: str, progetto: str, prima: str = "", noti: str = "") -> str:
    """Il testo per il modello: progetto, titolo di prima, prima richiesta, ultime tre richieste, ultima azione,
    ultima risposta. Una trascrizione più lunga di CODA perdeva la richiesta che ha aperto la sessione: le
    uscite lunghe degli strumenti la spingevano fuori, e il modello vedeva solo l'ultimo comando (14/11/2026).
    La prima richiesta si cerca allora nei primi TESTA byte."""
    try:
        with open(trascrizione, "rb") as fh:
            fh.seek(0, 2)
            lungo = fh.tell()
            fh.seek(max(0, lungo - CODA))
            righe = fh.read().decode("utf-8", "replace").splitlines()[1:]
            testa = []
            if lungo > CODA:
                fh.seek(0)
                testa = fh.read(TESTA).decode("utf-8", "replace").splitlines()[:-1]
    except OSError:
        return ""
    apertura = ""
    for riga in testa:
        try:
            d = json.loads(riga)
        except ValueError:
            continue
        if isinstance(d, dict) and d.get("type") == "user" and not d.get("isSidechain") and not d.get("isMeta"):
            r = richiesta(testo_di((d.get("message") or {}).get("content")))
            if len(r) >= 12 and not r.startswith(COMPATTATA):
                apertura = r
                break
    richieste, risposta, azione, riassunto = [], "", "", ""
    for riga in righe:
        try:
            d = json.loads(riga)
        except ValueError:
            continue
        # Fuori i subagent e i testi che Claude Code accoda da sé (il corpo di una skill, un avviso).
        if not isinstance(d, dict) or d.get("isSidechain") or d.get("isMeta"):
            continue
        m = d.get("message") or {}
        if d.get("type") == "user":
            grezzo = testo_di(m.get("content"))
            # Il riassunto di una compattazione non è una richiesta: dice di cosa parla la sessione, e
            # tagliato a 500 caratteri come richiesta perdeva proprio il lavoro (Spoleto, 14/11/2026).
            if grezzo.lstrip().startswith(COMPATTATA):
                i = grezzo.find("Summary:")
                riassunto = re.sub(r"\s+", " ", grezzo[i + 8:] if i >= 0 else grezzo).strip()[:RIASSUNTO]
                continue
            r = richiesta(grezzo)
            # "1", "vai", "sì" rispondono a una domanda: non dicono il lavoro
            if len(r) >= 12:
                richieste.append(r)
        elif d.get("type") == "assistant":
            for b in m.get("content", []) or []:
                if not isinstance(b, dict):
                    continue
                if b.get("type") == "text" and b.get("text", "").strip():
                    risposta = b["text"].strip()
                elif b.get("type") == "tool_use":
                    i = b.get("input") or {}
                    azione = (b.get("name", "") + ": " + str(i.get("description") or i.get("command") or i.get("file_path") or ""))[:200]
    if not richieste and not risposta and not apertura:
        return ""
    pezzi = ["Progetto scelto all'avvio: " + (progetto or "nessuno")]
    if noti:
        pezzi.append("Progetti noti:\n" + noti)
    if prima:
        pezzi.append("Titolo di prima: " + prima)
    if riassunto:
        pezzi.append("Riassunto della conversazione di prima: " + riassunto)
    if apertura and apertura not in richieste[-3:]:
        pezzi.append("Richiesta che ha aperto la sessione: " + apertura)
    pezzi += ["Richiesta della persona: " + r for r in richieste[-3:]]
    if risposta:
        pezzi.append("Ultima risposta dell'assistente: " + risposta[:500])
    if azione:
        pezzi.append("Ultimo comando: " + azione)
    testa, coda = (pezzi[:2], pezzi[2:]) if noti else (pezzi[:1], pezzi[1:])
    # l'elenco dei progetti non conta nel tetto: il contesto del lavoro resta intero
    return "\n".join(testa + ["\n".join(coda)[:CONTESTO]])


def claude_bin(attesa: float = ATTESA_BIN) -> str:
    """Il percorso di claude; se manca, riprova ogni 0,2 s per `attesa` secondi (#6682).
    L'aggiornatore di Claude Code reinstalla claude con npm e il link manca per 4-5 s (misura del 25/11/2026)."""
    fine = ".exe" if os.name == "nt" else ""
    scade = time.monotonic() + attesa
    while True:
        cl = shutil.which("claude") or os.path.expanduser("~/.local/bin/claude" + fine)
        if os.path.exists(cl):
            return cl
        if time.monotonic() >= scade:
            return ""
        time.sleep(0.2)


def chiedi(testo: str) -> str:
    cl = claude_bin()
    if not cl:
        return ""
    env = dict(os.environ, ARTURO_TITOLO_FIGLIO="1", CLAUDE_CODE_DISABLE_CLAUDE_MDS="1",
               CLAUDE_CODE_DISABLE_AUTO_MEMORY="1", PYTHONIOENCODING="utf-8")
    env.pop("CLAUDECODE", None)
    r = subprocess.run([cl, "-p", "--model", "haiku", "--tools", "", "--strict-mcp-config", "--no-session-persistence",
                        "--settings", '{"disableAllHooks":true}', "--system-prompt", ISTRUZIONE],
                       input="Appunti:\n" + testo + "\n\nLe tre righe:", capture_output=True, text=True, encoding="utf-8", errors="replace",
                       timeout=TETTO, env=env, cwd=os.path.expanduser("~"))
    return r.stdout if r.returncode == 0 else ""


def viva(sessione: str) -> bool:
    """True se la sessione ha ancora una trascrizione: Claude Code la elenca e la riapre."""
    return any((cartella().parent.parent / "projects").glob(f"*/{sessione}.jsonl"))


def spazza(adesso: float) -> None:
    try:
        for f in cartella().glob("*.json"):
            if adesso - f.stat().st_mtime <= VECCHIO:
                continue
            # il nome scritto dalla persona resta finché la sessione esiste
            if leggi(f).get("fonte") == "persona" and viva(f.stem):
                continue
            f.unlink()
    except OSError:
        pass


def main() -> int:
    if os.environ.get("ARTURO_TITOLI") == "0" or os.environ.get("ARTURO_TITOLO_FIGLIO"):
        return 0
    adesso = time.time()
    dati = json.loads(sys.stdin.buffer.read().decode("utf-8") or "{}")
    evento = str(dati.get("hook_event_name") or "")
    sessione = re.sub(r"[^\w-]", "", str(dati.get("session_id") or ""))[:64]
    if not sessione or evento not in ("UserPromptSubmit", "Stop", "PostToolUse"):
        return 0
    f = cartella() / f"{sessione}.json"
    salvato = leggi(f)
    if evento == "UserPromptSubmit":
        if salvato.get("titolo"):
            return 0
        t = compito(str(dati.get("prompt") or ""))
        if len(t) >= 2:
            scrivi(f, {"titolo": t, "fonte": "avvio", "quando": adesso, "peso": 0,
                       **{k: salvato[k] for k in ("progetto", "candidato") if k in salvato}})
        return 0
    try:
        ogni = float(os.environ.get("ARTURO_TITOLI_OGNI") or OGNI)
        ogni_sintesi = float(os.environ.get("ARTURO_SINTESI_OGNI") or OGNI_SINTESI)
    except ValueError:
        ogni, ogni_sintesi = OGNI, OGNI_SINTESI
    trascrizione = str(dati.get("transcript_path") or "")
    try:
        peso = os.path.getsize(trascrizione)
    except OSError:
        return 0
    # il nome l'ha scritto la persona: il modello non lo riscrive, ma la sintesi sì
    persona = salvato.get("fonte") == "persona" and bool(salvato.get("titolo"))
    modello = salvato.get("fonte") == "modello"
    vuole_titolo = not persona and not (modello and (adesso - float(salvato.get("quando") or 0) < ogni
                                                     or peso <= int(salvato.get("peso") or 0)))
    vuole_sintesi = (adesso - float(salvato.get("quando_sintesi") or 0) >= ogni_sintesi
                     and peso > int(salvato.get("peso_sintesi") or 0))
    # un altro hook della stessa sessione sta già chiedendo al modello (PostToolUse arriva a raffica)
    if adesso - float(salvato.get("chiede") or 0) < TETTO:
        return 0
    if not vuole_titolo and not vuole_sintesi:
        return 0
    scheda = leggi(cartella().parent / "scheda" / f"{sessione}.json")
    noti, righe = progetti_noti()
    # il progetto della scheda si dice al modello solo se l'ha scelto qualcuno (/inizio, la persona, Volta):
    # la cartella di un file scritto lo portava sullo strumento invece che sul lavoro (14/11/2026)
    scelto = str(scheda.get("progetto") or "") if scheda.get("fonte") in ("inizio", "persona", "volta", "teletrasporto") else ""
    testo = appunti(trascrizione, scelto, str(salvato.get("titolo") or ""), "\n".join(righe))
    if not testo:
        return 0
    scrivi(f, {**salvato, "chiede": adesso})
    risposta = chiedi(testo)
    t, s = due_righe(risposta)
    nuovo = {k: v for k, v in leggi(f).items() if k != "chiede"}
    if t and vuole_titolo:
        nuovo.update({"titolo": t, "fonte": "modello", "quando": adesso, "peso": peso})
    if vuole_sintesi:
        # anche senza una sintesi buona: il prossimo tentativo aspetta il suo turno, non il PostToolUse dopo
        nuovo.update({"quando_sintesi": adesso, "peso_sintesi": peso})
    if s:
        nuovo["sintesi"] = s
    if t or s:
        # vota sul progetto solo una risposta nel formato giusto
        progetto, candidato = accetta(nuovo, progetto_scelto(risposta, noti))
        if progetto:
            nuovo.update(progetto=progetto, candidato=candidato)
    scrivi(f, nuovo)
    spazza(adesso)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:  # noqa: BLE001 - un titolo mancato non deve mai rompere la sessione
        sys.exit(0)
