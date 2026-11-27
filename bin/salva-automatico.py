#!/usr/bin/env python3
"""salva-automatico.py: l'handoff minimo di una sessione chiusa senza /fine (M4 del piano della memoria, 15/11/2026).

Lo lancia hooks/session-end.sh alla chiusura, in background e senza modello, col JSON dell'hook su stdin
(session_id, transcript_path, cwd, reason). Se la sessione non ha fatto /fine, legge il transcript e scrive
in ~/.claude/data/handoffs/<slug>/ un handoff col nome solito (HANDOFF_<AAAA-MM-GG>_<HH-MM>.md) e la riga
"- Salvato: in automatico". Il nome solito serve: /inizio, la retention e l'indice lo contano come un handoff
normale, e il primo /fine vero lo riscrive al posto suo (commands/fine.md, FASE 4).

Cosa entra: le ultime richieste della persona, i file scritti (come inventario-sessione.py), il lavoro aperto
della sessione (TodoWrite, TaskCreate e TaskUpdate), branch e ultimo commit. Una richiesta con un possibile
segreto o una frase da injection non entra: lo dice lo scanner della memoria (hooks/memory-write-scanner.py).
La tabella Task Pendenti dice "Nessun task pendente nuovo": il gate dell'handoff resta verde, e i todo veri
restano nell'archivio.

Non scrive niente quando:
  - la sessione ha già il suo handoff di /fine (la riga "- Sessione: <id>" in un handoff non automatico) e
    dopo l'ultimo /fine non ha lavoro: né una richiesta di almeno quattro parole né un file scritto fuori da
    data/ e dal CLAUDE.md della persona. Con quel lavoro scrive un handoff automatico nuovo, accanto a quello
    di /fine, con la riga "- Dopo il /fine: <file>" e solo il lavoro venuto dopo;
  - il transcript non ha né una richiesta scritta dalla persona né un file scritto;
  - la sessione è headless (claude -p: entrypoint sdk-*);
  - la memoria è spenta (ARTURO_MEMORIA=0 o "accesa": false nelle impostazioni);
  - la cartella non è un progetto (né git né CLAUDE.md), o è la home o la cartella dei progetti, senza un
    /inizio <nome> nella sessione che porti a un progetto con handoff.
Un secondo giro della stessa sessione riscrive il suo handoff automatico: nessun doppione. Due giri insieme
(un congedo da Volta ne lancia più d'uno) passano uno alla volta, con una chiave per sessione (#5784).

USO
  salva-automatico.py < json-dell-hook
  Solo per i banchi: --projects DIR (dove cercare il transcript se il JSON non lo dice).

USCITA
  una riga: "SALVATO: <percorso>" oppure "NIENTE: <motivo>". Exit 0 sempre, salvo uso sbagliato (2).
"""
from __future__ import annotations

import argparse
import contextlib
import datetime as dt
import glob
import hashlib
import importlib.util
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

QUI = Path(os.path.realpath(__file__)).parent
sys.path.insert(0, str(QUI))
sys.path.append(str(QUI.parent / "hooks"))
from radici import radice_orsa  # noqa: E402

MARCA = "- Salvato: in automatico"
MAX_RICHIESTE = 5
MAX_RICHIESTA = 240
MAX_FILE = 30
CHIAVE_ATTESA = 60  # secondi che un giro aspetta la chiave della sessione tenuta da un altro giro
CHIAVE_VECCHIA = 300  # una chiave più vecchia l'ha lasciata un giro morto: si toglie
# I comandi che non dicono cosa stavi facendo.
COMANDI_MUTI = {"/clear", "/fine", "/exit", "/quit", "/compact", "/resume", "/model", "/config", "/status",
                "/cost", "/help", "/login", "/logout", "/doctor", "/memory", "/permissions", "/context"}
TAG_VIA = re.compile(r"<(system-reminder|local-command-caveat|local-command-stdout|local-command-stderr|"
                     r"task-notification|bash-stdout|bash-stderr)>.*?</\1>", re.S)


def carica(nome: str, percorso: Path):
    try:
        spec = importlib.util.spec_from_file_location(nome, str(percorso))
        modulo = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(modulo)
        return modulo
    except Exception:  # noqa: BLE001 - senza il modulo la parte che ne dipende salta
        return None


def slug(nome: str) -> str:
    """Lo stesso slug di /inizio, /fine e arturo todo (bin/contesto.py)."""
    return re.sub(r"^-+|-+$", "", re.sub(r"[^a-z0-9]+", "-", nome.lower()))


def git(cartella: Path, *argomenti: str) -> str:
    try:
        r = subprocess.run(["git", "-c", "core.fsmonitor=false", "-C", str(cartella), *argomenti],
                           capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=15,
                           env={**os.environ, "GIT_OPTIONAL_LOCKS": "0"})
    except (OSError, subprocess.SubprocessError):
        return ""
    return r.stdout.strip() if r.returncode == 0 else ""


def base_progetti() -> Path:
    pb = os.environ.get("PROJECTS_BASE") or str(Path.home() / "Documents" / "ClaudeCode")
    return Path(os.path.expanduser(pb))


def cartella_progetto(cwd: Path) -> Path | None:
    """La cartella del progetto: la cima di git, e per un worktree il repository che lo ospita (lo slug di
    .claude/worktrees/<nome> sarebbe il nome del worktree, non del progetto)."""
    comune = git(cwd, "rev-parse", "--path-format=absolute", "--git-common-dir")
    if comune:
        p = Path(comune)
        if p.name == ".git":
            return p.parent
        cima = git(cwd, "rev-parse", "--show-toplevel")
        return Path(cima) if cima else None
    if (cwd / "CLAUDE.md").is_file():
        return cwd
    return None


# --- lettura del transcript ----------------------------------------------------------------------------

def righe(path: Path):
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            for riga in f:
                try:
                    r = json.loads(riga)
                except ValueError:
                    continue
                if isinstance(r, dict):
                    yield r
    except OSError:
        return


def testo_utente(r: dict) -> str:
    """Il testo scritto dalla persona in un record, o "" per tool_result, iniezioni e messaggi meta."""
    if r.get("type") != "user" or r.get("isMeta") or r.get("toolUseResult") is not None:
        return ""
    m = r.get("message")
    if not isinstance(m, dict):
        return ""
    c = m.get("content")
    if isinstance(c, list):
        if any(isinstance(x, dict) and x.get("type") == "tool_result" for x in c):
            return ""
        c = "\n".join(x.get("text", "") for x in c if isinstance(x, dict) and x.get("type") == "text")
    if not isinstance(c, str):
        return ""
    comando = re.search(r"<command-name>\s*(/?[\w:.-]+)\s*</command-name>", c)
    if comando:
        nome = "/" + comando.group(1).lstrip("/")
        if nome in COMANDI_MUTI:
            return ""
        arg = re.search(r"<command-args>(.*?)</command-args>", c, re.S)
        return f"{nome} {arg.group(1).strip() if arg else ''}".strip()
    c = TAG_VIA.sub("", c).strip()
    if not c or c.startswith("[Request interrupted") or c.startswith("<"):
        return ""
    return c


FINE = re.compile(r"<command-name>\s*/?(?:arturo:)?fine\s*</command-name>|^\s*/(?:arturo:)?fine(?:\s|$)")
SCRIVE = {"Write": "file_path", "Edit": "file_path", "MultiEdit": "file_path", "NotebookEdit": "notebook_path"}
# Dopo un /fine a metà, una risposta corta ("salva", "ok", "grazie") chiude il /fine, non apre lavoro nuovo.
PAROLE_LAVORO = 4


def e_fine(r: dict) -> bool:
    """Vero se il record è un /fine scritto dalla persona (anche /arturo:fine)."""
    if r.get("type") != "user" or r.get("isMeta") or r.get("toolUseResult") is not None:
        return False
    m = r.get("message")
    c = m.get("content") if isinstance(m, dict) else None
    if isinstance(c, list):
        c = "\n".join(x.get("text", "") for x in c if isinstance(x, dict) and x.get("type") == "text")
    return isinstance(c, str) and bool(FINE.search(c))


def leggi_transcript(path: Path) -> dict:
    richieste, todo, task, attesi, headless, sid = [], {}, {}, {}, False, ""
    # Il lavoro dopo l'ultimo /fine: la persona usa /fine anche a metà, come salvataggio, e poi continua.
    fine_visto, richieste_dopo, file_dopo = False, [], []
    for r in righe(path):
        if str(r.get("entrypoint", "")).startswith("sdk"):
            headless = True
        sid = sid or str(r.get("sessionId") or "")
        if e_fine(r):
            fine_visto, richieste_dopo, file_dopo = True, [], []
        t = testo_utente(r)
        if t:
            richieste.append(t)
            richieste_dopo.append(t)
        m = r.get("message")
        if not isinstance(m, dict) or not isinstance(m.get("content"), list):
            continue
        for c in m["content"]:
            if not isinstance(c, dict):
                continue
            if c.get("type") == "tool_use":
                nome, inp = c.get("name", ""), c.get("input") or {}
                # La rotazione lancia /fine --rotazione col tool Skill, senza un prompt della persona.
                if nome == "Skill" and isinstance(inp, dict) and str(inp.get("skill", "")).strip() in ("fine", "arturo:fine"):
                    fine_visto, richieste_dopo, file_dopo = True, [], []
                    continue
                if nome in SCRIVE and isinstance(inp, dict) and isinstance(inp.get(SCRIVE[nome]), str):
                    if inp[SCRIVE[nome]] not in file_dopo:
                        file_dopo.append(inp[SCRIVE[nome]])
                if nome == "TodoWrite" and isinstance(inp.get("todos"), list):
                    todo = {str(i): (str(x.get("content") or ""), str(x.get("status") or ""))
                            for i, x in enumerate(inp["todos"]) if isinstance(x, dict)}
                elif nome == "TaskCreate":
                    attesi[c.get("id")] = str(inp.get("subject") or inp.get("description") or "")
                elif nome == "TaskUpdate" and inp.get("taskId") is not None:
                    tid = str(inp["taskId"]).lstrip("#")
                    if tid in task and inp.get("status"):
                        task[tid] = (task[tid][0], str(inp["status"]))
            elif c.get("type") == "tool_result" and c.get("tool_use_id") in attesi:
                titolo = attesi.pop(c["tool_use_id"])
                cont = c.get("content")
                testo = cont if isinstance(cont, str) else " ".join(
                    x.get("text", "") for x in cont or [] if isinstance(x, dict))
                n = re.search(r"#(\d+)", testo or "")
                if n and titolo:
                    task[n.group(1)] = (titolo, "pending")
    aperti = [f"{t} ({s.replace('_', ' ')})" for t, s in list(todo.values()) + list(task.values())
              if t and s not in ("completed", "deleted")]
    return {"richieste": richieste, "aperti": aperti, "headless": headless, "sid": sid,
            "fine_visto": fine_visto, "richieste_dopo": richieste_dopo, "file_dopo": file_dopo}


def lavoro_dopo_fine(letto: dict) -> tuple:
    """(richieste, file) venuti dopo l'ultimo /fine, senza la coda del /fine stesso: le risposte corte e i
    file che /fine scrive da sé (handoff, memoria, CLAUDE.md della persona). Vuoti se il lavoro non c'è."""
    orsa = os.path.realpath(radice_orsa())
    propri = (os.path.join(orsa, "data") + os.sep, os.path.join(orsa, "CLAUDE.md"))
    richieste = [r for r in letto["richieste_dopo"]
                 if not re.match(r"^/(?:[\w-]+:)?inizio(\s|$)", r) and len(r.split()) >= PAROLE_LAVORO]
    file = []
    for f in letto["file_dopo"]:
        vero = os.path.realpath(os.path.expanduser(f))
        if vero == propri[1] or vero.startswith(propri[0]):
            continue
        file.append(f)
    return richieste, file


def file_scritti(sid: str, projects: str, home: str) -> list:
    """I file della sessione, con lo stesso inventario di /fine (bin/inventario-sessione.py)."""
    inv = carica("inventario_sessione", QUI / "inventario-sessione.py")
    if inv is None:
        return []
    try:
        dati = inv.raccogli(sid, projects, home)
    except Exception:  # noqa: BLE001 - un inventario che si rompe non ferma il salvataggio
        return []
    out = []
    for f in (dati or {}).get("file", []):
        stato = f.get("git") or ("fuori da git" if not f.get("repo") else "")
        out.append(f"{f['path']}" + (f" ({stato})" if stato else ""))
    return out


# --- handoff -----------------------------------------------------------------------------------------------

def handoff_con_sessione(sid: str) -> list:
    """Gli handoff della sessione, dal più recente: (percorso, automatico)."""
    radice = radice_orsa() / "data" / "handoffs"
    riga = f"- Sessione: {sid}"
    fuori = []
    for p in sorted(radice.glob("*/HANDOFF_*.md"), key=lambda q: q.name, reverse=True):
        try:
            righe_h = p.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            continue
        if riga in righe_h:
            fuori.append((p, MARCA in righe_h))
    return fuori


def sicura(testo: str, scanner) -> str:
    una = " ".join(testo.split())
    if scanner is not None:
        try:
            if scanner.trova(una):
                return "(richiesta non copiata: lo scanner della memoria vi ha trovato un possibile segreto o un'istruzione nascosta)"
        except Exception:  # noqa: BLE001
            pass
    return una if len(una) <= MAX_RICHIESTA else una[:MAX_RICHIESTA - 1].rstrip() + "…"


def correzioni_della_sessione(sid: str, scanner) -> list:
    """Le correzioni della sessione (bin/correzioni.py), una riga l'una con la skill se c'è. Finiscono con la
    sessione: senza /fine nessuno decide dove vanno, e l'handoff automatico è l'unico posto che le tiene."""
    if not re.match(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,127}$", sid):
        return []
    modulo = carica("correzioni", QUI / "correzioni.py")
    if modulo is None or not hasattr(modulo, "leggi"):
        return []
    fuori = []
    for voce in modulo.leggi(sid):
        skill = modulo.skill_di(voce) if hasattr(modulo, "skill_di") else ""
        fuori.append(sicura(voce["testo"], scanner) + (f" [skill: {skill}]" if skill else ""))
    return fuori


def componi(s: str, cartella: Path | None, sid: str, quando: dt.datetime, richieste: list, file: list,
            aperti: list, correzioni: list = (), dopo: str = "") -> str:
    branch = git(cartella, "rev-parse", "--abbrev-ref", "HEAD") if cartella else ""
    commit = git(cartella, "log", "-1", "--format=%h - %s") if cartella else ""
    testa = [f"# Session Handoff - {quando:%Y-%m-%d %H:%M}", "## Progetto",
             f"- Nome: {s}" + (f" / Branch: {branch}" if branch else "") + " / Status: salvato in automatico",
             f"- Sessione: {sid}", MARCA]
    if dopo:
        testa.append(f"- Dopo il /fine: {dopo}")
    if commit:
        testa.append(f"- Ultimo commit: {commit}")
    ultima = richieste[-1] if richieste else ""
    if dopo:
        corpo = (f"La sessione ha fatto /fine a metà ({dopo}), poi ha continuato e si è chiusa senza un altro /fine. "
                 "Arturo ha salvato da solo il lavoro venuto dopo, senza giudicare: niente decisioni, niente todo nuovi.")
    else:
        corpo = ("La sessione si è chiusa senza /fine. Arturo ha salvato da solo cosa stavi facendo, senza "
                 "giudicare: niente decisioni, niente todo nuovi.")
    if ultima:
        corpo += f" L'ultima richiesta: \"{ultima}\"."
    if file:
        corpo += f" File scritti: {len(file)}."
    # Se cambi questa frase, aggiorna RIGHE_FISSE in bin/doppioni.py: lì la frase non conta come doppione (#6742).
    out = testa + ["## Ripartenza", corpo,
                   "Prossimo passo: riprendere da qui e chiudere con /fine, che completa questo salvataggio."]
    if richieste:
        out += ["## Ultime richieste"] + [f"{n}. {r}" for n, r in enumerate(richieste, 1)]
    if file:
        out += ["## File e materiali"] + [f"- {f}" for f in file[:MAX_FILE]]
        if len(file) > MAX_FILE:
            out.append(f"- … e altri {len(file) - MAX_FILE} file")
    if aperti:
        out += ["## Lavoro aperto nella sessione"] + [f"- {a}" for a in aperti]
    if correzioni:
        out += ["## Correzioni",
                "Dette dalla persona nella sessione. Il prossimo /fine (FASE 8) decide dove vanno: nella skill "
                "fra parentesi quadre, nel CLAUDE.md o in memoria."] + [f"{n}. {c}" for n, c in enumerate(correzioni, 1)]
    out += ["## Task Pendenti",
            "Nessun task pendente nuovo: il salvataggio automatico non crea todo. I todo aperti restano "
            "nell'archivio, e il prossimo /fine li riporta qui."]
    return "\n".join(out) + "\n"


def scrivi(percorso: Path, testo: str) -> None:
    percorso.parent.mkdir(parents=True, exist_ok=True)
    tmp = percorso.with_name(f".{percorso.name}.tmp-{os.getpid()}")
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        f.write(testo)
    os.replace(str(tmp), str(percorso))


def scrivi_nuovo(cartella: Path, quando: dt.datetime, testo: str) -> Path:
    """Scrive l'handoff nel primo minuto libero, da quando in avanti, e torna il percorso.

    Il nome si prende e si scrive in un passo solo: il file intero nasce col collegamento (os.link), che non
    sovrascrive mai. Fino al 22/11/2026 nome_libero guardava se il nome c'era e poi scrivi() faceva os.replace:
    più schede dello stesso progetto chiuse insieme sceglievano lo stesso minuto, e restava un handoff solo
    (revisione del 20/11, bug 17)."""
    cartella.mkdir(parents=True, exist_ok=True)
    tmp = cartella / f".handoff-nuovo.tmp-{os.getpid()}"
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        f.write(testo)
    try:
        for minuti in range(24 * 60):
            p = cartella / f"HANDOFF_{quando + dt.timedelta(minutes=minuti):%Y-%m-%d_%H-%M}.md"
            try:
                os.link(str(tmp), str(p))
                return p
            except FileExistsError:
                continue
            except OSError:  # un disco senza collegamenti: la creazione esclusiva fa lo stesso lavoro
                try:
                    with open(p, "x", encoding="utf-8", newline="\n") as f:
                        f.write(testo)
                    return p
                except FileExistsError:
                    continue
        raise OSError(f"nessun nome libero in {cartella}")
    finally:
        try:
            tmp.unlink()
        except OSError:
            pass


def slug_del_progetto(cartella: Path) -> str:
    """Lo slug della scheda del progetto se una scheda vale per questa cartella (nome, `alias:` o `cartella:`),
    altrimenti il nome della cartella. Fino al 18/11/2026 valeva sempre il nome della cartella: una cartella
    rinominata o diversa dal progetto apriva una seconda cartella di handoff accanto a quella di /fine."""
    nome = slug(cartella.name)
    try:
        import melchior_match as mm
        scheda = mm.trova_scheda(nome) if mm.memoria_accesa() else None
    except Exception:  # noqa: BLE001 - una memoria rotta non ferma il salvataggio
        scheda = None
    if scheda is not None and scheda.stem.startswith("progetto-") and slug(scheda.stem[len("progetto-"):]):
        return slug(scheda.stem[len("progetto-"):])
    return nome


def scegli_progetto(cwd: Path, richieste: list) -> tuple:
    """(slug, cartella) o ("", None)."""
    home = Path.home().resolve()
    pb = base_progetti()
    contenitore = cwd in (home, pb.resolve() if pb.exists() else pb)
    cartella = None if contenitore else cartella_progetto(cwd)
    if cartella and cartella.resolve() != home:
        return slug_del_progetto(cartella), cartella
    # Dalla home o dalla cartella dei progetti vale l'ultimo /inizio <nome> che porta a un progetto noto.
    for r in reversed(richieste):
        m = re.match(r"^/(?:[\w-]+:)?inizio\s+([^\s]+)", r)
        if m and slug(m.group(1)) and (radice_orsa() / "data" / "handoffs" / slug(m.group(1))).is_dir():
            return slug(m.group(1)), None
    return "", None


@contextlib.contextmanager
def chiave_sessione(sid: str):
    """Un giro alla volta per sessione: la cartella della chiave nasce con os.mkdir, che non riesce a due processi.

    Fino al 27/11/2026 più giri insieme della stessa sessione cercavano tutti l'handoff, non lo trovavano, e
    scrivevano ognuno il suo nel primo minuto libero: il 16/11 tre doppioni alle 12:46, 12:47 e 12:48 (#5784).
    Dopo CHIAVE_ATTESA secondi il giro salva lo stesso: meglio un doppione che un lavoro perso."""
    radice = radice_orsa() / "data" / "handoffs"
    chiave = radice / f".salva-{hashlib.sha256(sid.encode('utf-8')).hexdigest()[:16]}.chiave"
    presa = False
    try:
        radice.mkdir(parents=True, exist_ok=True)
        fine = time.monotonic() + CHIAVE_ATTESA
        while time.monotonic() < fine:
            try:
                os.mkdir(str(chiave))
                presa = True
                break
            except FileExistsError:
                try:
                    if time.time() - chiave.stat().st_mtime > CHIAVE_VECCHIA:
                        os.rmdir(str(chiave))
                        continue
                except OSError:
                    pass
                time.sleep(0.1)
    except OSError:
        pass
    try:
        yield
    finally:
        if presa:
            try:
                os.rmdir(str(chiave))
            except OSError:
                pass


def main(argv: list) -> int:
    for flusso in (sys.stdout, sys.stderr):
        try:
            flusso.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--projects", default=str(radice_orsa() / "projects"))
    parser.add_argument("-h", "--help", action="store_true")
    a, resto = parser.parse_known_args(argv)
    if a.help:
        print(__doc__.strip())
        return 0
    if resto:
        print(f"salva-automatico: argomento sconosciuto: {resto[0]}", file=sys.stderr)
        return 2
    try:
        dati = json.loads(sys.stdin.read() or "{}")
    except ValueError:
        dati = {}
    if not isinstance(dati, dict):
        dati = {}

    mm = carica("melchior_match", QUI.parent / "hooks" / "melchior_match.py")
    if mm is not None and hasattr(mm, "memoria_accesa") and not mm.memoria_accesa():
        print("NIENTE: memoria spenta")
        return 0
    sid = str(dati.get("session_id") or "")
    transcript = Path(str(dati.get("transcript_path") or ""))
    if sid and not transcript.is_file():
        trovati = sorted(glob.glob(os.path.join(a.projects, "*", f"{sid}.jsonl")))
        transcript = Path(trovati[0]) if trovati else transcript
    if not sid or not transcript.is_file():
        print("NIENTE: id di sessione o transcript assente")
        return 0
    with chiave_sessione(sid):
        return salva_sessione(sid, transcript, dati)


def salva_sessione(sid: str, transcript: Path, dati: dict) -> int:
    """Cerca l'handoff della sessione e scrive il suo automatico: il tratto che gira sotto la chiave."""
    letto = leggi_transcript(transcript)
    # L'handoff di /fine più recente della sessione, e l'automatico se è venuto dopo. Un /fine a metà non
    # chiude la sessione: fino al 22/11/2026 il lavoro venuto dopo si perdeva (A5, revisione del 20/11).
    gia, dopo, dopo_fine = None, "", None
    for p, automatico in handoff_con_sessione(sid):
        if automatico:
            gia = gia or p
            continue
        dopo_fine = lavoro_dopo_fine(letto) if letto["fine_visto"] else ([], [])
        if not dopo_fine[0] and not dopo_fine[1]:
            print(f"NIENTE: la sessione ha chiuso con /fine ({p.name})")
            return 0
        dopo = p.name
        break
    if letto["headless"]:
        print("NIENTE: sessione headless")
        return 0
    cwd = Path(str(dati.get("cwd") or os.getcwd())).expanduser()
    try:
        cwd = cwd.resolve()
    except OSError:
        pass
    s, cartella = scegli_progetto(cwd, letto["richieste"])
    if not s:
        print("NIENTE: la sessione non sta in un progetto")
        return 0
    if dopo_fine is not None:
        # Dopo un /fine a metà entra solo il lavoro venuto dopo: il resto sta già nel suo handoff.
        da_salvare, file = dopo_fine
    else:
        progetti = str(transcript.parent.parent)
        file = file_scritti(sid, progetti, str(Path.home()))
        da_salvare = letto["richieste"]
        richieste_vere = [r for r in da_salvare if not re.match(r"^/(?:[\w-]+:)?inizio(\s|$)", r)]
        if not richieste_vere and not file:
            print("NIENTE: transcript senza richieste e senza file scritti")
            return 0

    scanner = carica("memory_write_scanner", QUI.parent / "hooks" / "memory-write-scanner.py")
    richieste = [sicura(r, scanner) for r in da_salvare[-MAX_RICHIESTE:]]
    adesso = dt.datetime.now().replace(second=0, microsecond=0)
    cartella_h = radice_orsa() / "data" / "handoffs" / s
    testo = componi(s, cartella, sid, adesso, richieste, file, letto["aperti"],
                    correzioni_della_sessione(sid, scanner), dopo)
    if gia is not None:  # l'handoff automatico della stessa sessione, a un giro dopo: si riscrive
        percorso = gia
        scrivi(percorso, testo)
    else:
        percorso = scrivi_nuovo(cartella_h, adesso, testo)
    if gia is None:  # M7 della memoria: un evento per sessione salvata, non uno per giro della stessa
        telemetria = carica("telemetria", QUI / "telemetria.py")
        if telemetria is not None and hasattr(telemetria, "registra"):
            telemetria.registra("salvataggio", "automatico")
    print(f"SALVATO: {percorso}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
