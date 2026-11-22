#!/usr/bin/env python3
"""RB11-RB21: i bug bassi 11-21 della revisione di Arturo del 20/11/2026 (#6389).

RB11 bin/sync-progetti.sh: dopo il pull i file in stage restano in stage (stash pop --index).
RB12 bin/monthly-cleanup.sh: la pulizia della cartella dei progetti non archivia CLAUDE.md e README.
RB13 bin/aggiorna-applica.sh: un reset --keep rifiutato per un file cambiato da un'altra sessione dà
     APPLICAZIONE ANNULLATA (uscita 1), non RIPRISTINO NON RIUSCITO (uscita 2).
RB14 bin/todo_store.py: chi esce non cancella il lucchetto di un altro; un lucchetto fresco visto vecchio per
     un attimo non si ruba.
RB15 hooks/melchior-postwrite.py: una modifica di Claude arrivata fra la lettura e la scrittura dell'hook resta.
RB16 bin/unisci.py: un errore nelle scritture locali rimette tutto com'era e non chiama la fonte esterna; un
     file col punto presente nei due progetti non prende un nome col trattino davanti.
RB17 bin/salva-automatico.py: con i dieci minuti dopo già presi l'handoff automatico non ne sovrascrive uno.
RB18 bin/migra.py: Ctrl-C a metà della migrazione torna indietro ed esce 130.
RB19 bin/aggiornamenti.py, hooks/agente-worktree.py, bin/correzioni.py, bin/rinomina.py: due scritture dello
     stesso file non usano lo stesso file temporaneo.
RB20 bin/aggiornamenti.py: una sessione lanciata da una home con spazi conta.
RB21 hooks/session-end.sh e bin/telemetria.py: la chiusura di una sessione toglie solo le sue conferme in
     attesa, non quelle delle altre sessioni aperte.

Sulla base 1e84201 sono rossi tutti e undici.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
import time
from pathlib import Path

CASI = ["RB11", "RB12", "RB13", "RB14", "RB15", "RB16", "RB17", "RB18", "RB19", "RB20", "RB21"]
DISCRIMINANTI = list(CASI)
BASH = shutil.which("bash") or "bash"
GIT = shutil.which("git") or "git"


def env_di(home: Path, **extra) -> dict:
    e = dict(os.environ, HOME=str(home), USERPROFILE=str(home), ARTURO_TELEMETRIA="0", ARTURO_AGGIORNAMENTI="manuali",
             PYTHONDONTWRITEBYTECODE="1", GIT_TERMINAL_PROMPT="0", GIT_CONFIG_GLOBAL=os.devnull,
             GIT_CONFIG_NOSYSTEM="1", ARTURO_TODO=str(home / ".claude" / "data" / "todo" / "eventi.jsonl"),
             GIT_AUTHOR_NAME="prova", GIT_AUTHOR_EMAIL="prova@example.invalid",
             GIT_COMMITTER_NAME="prova", GIT_COMMITTER_EMAIL="prova@example.invalid")
    for k in ("PROJECTS_BASE", "CLAUDE_CONFIG_DIR", "CLAUDE_CODE_SESSION_ID", "ARTURO_RADICE", "FINE_CODA_CLAUDE",
              "PULIZIA_CARTELLA_PROGETTI"):
        e.pop(k, None)
    e.update(extra)
    return e


def lancia(cmd: list, env: dict, cwd: Path | None = None, entrata: str = "", timeout: int = 120):
    return subprocess.run(cmd, input=entrata, capture_output=True, text=True, encoding="utf-8", errors="replace",
                          env=env, cwd=str(cwd) if cwd else None, timeout=timeout)


def git(dove: Path, *a: str, env: dict) -> str:
    return subprocess.run([GIT, "-C", str(dove), *a], check=True, capture_output=True, text=True, env=env).stdout


def casa(tmp: Path, nome: str) -> Path:
    home = tmp / nome
    (home / ".claude" / "session-env").mkdir(parents=True)
    return home


def python_con(repo: Path, codice: str, env: dict, entrata: str = "", timeout: int = 120):
    """Lancia un pezzo di Python con bin/ e hooks/ del repo nel percorso: torna l'uscita del processo."""
    prologo = (f"import sys\nsys.path.insert(0, {str(repo / 'bin')!r})\nsys.path.insert(0, {str(repo / 'hooks')!r})\n"
               f"REPO = {str(repo)!r}\n")
    return lancia([sys.executable, "-B", "-c", prologo + codice], env, entrata=entrata, timeout=timeout)


# --- RB11 ---------------------------------------------------------------------------------------------------

def rb11(repo: Path, tmp: Path) -> list:
    home = casa(tmp, "h11")
    env = env_di(home)
    nudo = tmp / "remoto.git"
    git(tmp, "init", "-q", "--bare", "-b", "main", str(nudo), env=env)
    origine = tmp / "origine"
    git(tmp, "init", "-q", "-b", "main", str(origine), env=env)
    for nome in ("pronto.txt", "dopo.txt"):
        (origine / nome).write_text("uno\n", encoding="utf-8")
    git(origine, "add", "-A", env=env)
    git(origine, "commit", "-q", "-m", "primo", env=env)
    git(origine, "remote", "add", "origin", str(nudo), env=env)
    git(origine, "push", "-q", "-u", "origin", "main", env=env)
    radice = tmp / "progetti"
    radice.mkdir()
    clone = radice / "libro"
    git(tmp, "clone", "-q", str(nudo), str(clone), env=env)
    (clone / "pronto.txt").write_text("due\n", encoding="utf-8")
    git(clone, "add", "pronto.txt", env=env)                       # un commit parziale preparato
    (clone / "dopo.txt").write_text("due\n", encoding="utf-8")     # una modifica fuori dallo stage
    r = lancia([BASH, str(repo / "bin" / "sync-progetti.sh"), str(radice)], env, timeout=180)
    in_stage = git(clone, "diff", "--cached", "--name-only", env=env).split()
    fuori = git(clone, "diff", "--name-only", env=env).split()
    if in_stage != ["pronto.txt"] or fuori != ["dopo.txt"]:
        return [f"RB11 dopo il sync lo stage è cambiato: in stage {in_stage}, fuori {fuori} {r.stdout[-300:]!r}"]
    return []


# --- RB12 ---------------------------------------------------------------------------------------------------

def rb12(repo: Path, tmp: Path) -> list:
    home = casa(tmp, "h12")
    progetti = tmp / "progetti"
    progetti.mkdir()
    vecchio = time.time() - 90 * 86400
    for nome in ("CLAUDE.md", "README.md", "appunti-vecchi.txt"):
        (progetti / nome).write_text("x\n", encoding="utf-8")
        os.utime(progetti / nome, (vecchio, vecchio))
    r = lancia([BASH, str(repo / "bin" / "monthly-cleanup.sh"), "--prova"],
               env_di(home, PULIZIA_CARTELLA_PROGETTI=str(progetti), PULIZIA_CACHE="0", PULIZIA_PREFISSI_LAUNCHAGENT=""),
               timeout=180)
    sposterei = sorted(Path(riga.split("sposterei: ", 1)[1]).name for riga in r.stdout.splitlines() if "sposterei: " in riga)
    if sposterei != ["appunti-vecchi.txt"]:
        return [f"RB12 la pulizia archivierebbe {sposterei} invece del solo appunti-vecchi.txt: {r.stdout[-300:]!r}"]
    return []


# --- RB13 ---------------------------------------------------------------------------------------------------

GIT_FINTO = """#!/usr/bin/env bash
# Al primo reset --keep verso l'aggiornamento un'altra sessione cambia config.txt: git rifiuta il reset.
if [ "$1" = reset ] && [ "$2" = -q ] && [ "$3" = --keep ] && [ ! -e "$SEGNO" ] && [ "$4" = "$NUOVO" ]; then
  : > "$SEGNO"
  printf 'cambiata da un altra sessione\\n' >> "$RADICE_PROVA/config.txt"
fi
exec "$GIT_VERO" "$@"
"""


def rb13(repo: Path, tmp: Path) -> list:
    home = casa(tmp, "h13")
    env = env_di(home)
    radice = tmp / "config"
    git(tmp, "init", "-q", "-b", "main", str(radice), env=env)
    (radice / "config.txt").write_text("versione uno\n", encoding="utf-8")
    git(radice, "add", "-A", env=env)
    git(radice, "commit", "-q", "-m", "uno", env=env)
    git(radice, "checkout", "-q", "-b", "arrivo", env=env)
    (radice / "config.txt").write_text("versione due\n", encoding="utf-8")
    git(radice, "commit", "-q", "-am", "due", env=env)
    nuovo = git(radice, "rev-parse", "HEAD", env=env).strip()
    git(radice, "checkout", "-q", "main", env=env)
    finto = tmp / "bin-finto"
    finto.mkdir()
    (finto / "git").write_text(GIT_FINTO, encoding="utf-8")
    (finto / "git").chmod(0o755)
    env_finto = dict(env, PATH=f"{finto}{os.pathsep}{env.get('PATH', '')}", GIT_VERO=GIT, SEGNO=str(tmp / "segno"),
                     NUOVO=nuovo, RADICE_PROVA=str(radice))
    r = lancia([BASH, str(repo / "bin" / "aggiorna-applica.sh"), str(radice), "rebase", "arrivo"], env_finto, cwd=radice,
               timeout=180)
    if not (tmp / "segno").exists():
        return [f"RB13 il banco non ha raggiunto il reset --keep: rc {r.returncode} {(r.stdout + r.stderr)[-400:]!r}"]
    if r.returncode != 1 or "APPLICAZIONE ANNULLATA" not in r.stdout or "RIPRISTINO NON RIUSCITO" in r.stdout:
        return [f"RB13 un reset --keep rifiutato non dice ANNULLATA: rc {r.returncode} {r.stdout[-400:]!r}"]
    return []


# --- RB14 ---------------------------------------------------------------------------------------------------

LUCCHETTO = r"""
import os, time, types
from pathlib import Path
import todo_store as ts
f = Path(os.environ["DOVE"]) / "archivio.json"
lock = f.with_name(f.name + ".lock")
rossi = []

# 1. Chi esce non cancella un lucchetto che nel frattempo è di un altro.
with ts.Lucchetto(f):
    lock.write_text("altro-processo", encoding="ascii")
if not lock.exists():
    rossi.append("all'uscita ha cancellato il lucchetto di un altro")
if lock.exists():
    lock.unlink()

# 2. Un lucchetto fresco di un altro, visto vecchio per un attimo (lo stat prima del cambio), non si ruba.
lock.write_text("altro-processo", encoding="ascii")
vero = Path.stat
volte = {"n": 0}
def stat_finto(self, *a, **k):
    if self == lock and volte["n"] == 0:
        volte["n"] += 1
        return types.SimpleNamespace(st_mtime=time.time() - 100)
    return vero(self, *a, **k)
Path.stat = stat_finto
ts.Lucchetto.ATTESA = 0.3
entrato = False
try:
    with ts.Lucchetto(f):
        entrato = True
except ts.ErroreTodo:
    pass
finally:
    Path.stat = vero
if entrato or not lock.exists() or lock.read_text(encoding="ascii") != "altro-processo":
    rossi.append("ha rubato un lucchetto fresco di un altro processo")
print("ROSSI=" + " | ".join(rossi))
"""


def rb14(repo: Path, tmp: Path) -> list:
    home = casa(tmp, "h14")
    r = python_con(repo, LUCCHETTO, env_di(home, DOVE=str(tmp)))
    righe = [x for x in r.stdout.splitlines() if x.startswith("ROSSI=")]
    if r.returncode != 0 or not righe:
        return [f"RB14 il banco del lucchetto non è arrivato in fondo: rc {r.returncode} {(r.stdout + r.stderr)[-400:]!r}"]
    esito = righe[0][len("ROSSI="):]
    return [f"RB14 {esito}"] if esito else []


# --- RB15 ---------------------------------------------------------------------------------------------------

MEMORIA = r"""
import importlib.util, io, json, os, sys
from pathlib import Path
spec = importlib.util.spec_from_file_location("postwrite", os.path.join(REPO, "hooks", "melchior-postwrite.py"))
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
mem = Path(os.environ["DOVE"]) / "memory"
nota = mem / "feedback" / "nota.md"
m.MEMORY_DIR = mem
vero = m.update_updated_field
def con_claude_in_mezzo(testo):
    nuovo = vero(testo)
    # Claude scrive di nuovo la nota mentre l'hook asincrono lavora.
    nota.write_text(testo + "Riga aggiunta da Claude DOPO-LA-LETTURA.\n", encoding="utf-8")
    return nuovo
m.update_updated_field = con_claude_in_mezzo
payload = json.dumps({"tool_name": "Edit", "tool_input": {"file_path": str(nota)}})
sys.stdin = io.TextIOWrapper(io.BytesIO(payload.encode("utf-8")), encoding="utf-8")
m.main()
print("TESTO=" + json.dumps(nota.read_text(encoding="utf-8")))
"""


def rb15(repo: Path, tmp: Path) -> list:
    home = casa(tmp, "h15")
    nota = tmp / "memory" / "feedback" / "nota.md"
    nota.parent.mkdir(parents=True)
    nota.write_text("---\nname: nota\ndescription: una nota\ntype: feedback\nupdated: 2026-01-01\n"
                    "created: 2026-01-01\n---\nCorpo.\n", encoding="utf-8")
    r = python_con(repo, MEMORIA, env_di(home, DOVE=str(tmp), ARTURO_MEMORIA="1"))
    righe = [x for x in r.stdout.splitlines() if x.startswith("TESTO=")]
    if r.returncode != 0 or not righe:
        return [f"RB15 il banco della memoria non è arrivato in fondo: rc {r.returncode} {(r.stdout + r.stderr)[-400:]!r}"]
    if "DOPO-LA-LETTURA" not in json.loads(righe[0][len("TESTO="):]):
        return ["RB15 l'hook della memoria ha cancellato una modifica di Claude arrivata dopo la sua lettura"]
    return []


# --- RB16 ---------------------------------------------------------------------------------------------------

FONTE_UNISCE = r'''import json, os, sys
from pathlib import Path
a = sys.argv[1:]
with open(Path(os.environ["HOME"]) / "fonte.log", "a", encoding="utf-8") as f:
    f.write(json.dumps(a) + "\n")
if "--backup" in a:
    Path(a[a.index("--backup") + 1]).mkdir(parents=True, exist_ok=True)
print(json.dumps({"task": 1, "riassunto": "1 task"}))
'''


def _laboratorio(repo: Path, tmp: Path):
    spec = importlib.util.spec_from_file_location("banco_unisci", str(repo / "tests" / "test_unisci_2026_11_20.py"))
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    lab = modulo.Lab(repo, tmp)
    lab.prepara()
    return lab


def rb16(repo: Path, tmp: Path) -> list:
    rossi = []
    # 1. Un errore a metà delle scritture locali: tutto torna com'era, la fonte esterna non unisce.
    lab = _laboratorio(repo, tmp / "a")
    (lab.home / "fonte.py").write_text(FONTE_UNISCE, encoding="utf-8")
    fonte = lab.cl / "arturo" / "fonte-task.local"
    fonte.parent.mkdir(parents=True, exist_ok=True)
    fonte.write_text(f'comando = "{sys.executable}" "{lab.home / "fonte.py"}"\n', encoding="utf-8")
    (lab.mem / "_archive").write_text("un file al posto della cartella dell'archivio\n", encoding="utf-8")
    prima_h = sorted(p.name for p in (lab.h / "fenice-vecchia").iterdir())
    prima_v = sorted(p.name for p in (lab.h / "fenice").iterdir())
    scheda_v = (lab.mem / "progetti" / "progetto-fenice.md").read_text(encoding="utf-8")
    r = lab.arturo("progetti", "unisci", "fenice-vecchia", "fenice")
    chiamate = [json.loads(x) for x in (lab.home / "fonte.log").read_text(encoding="utf-8").splitlines()] \
        if (lab.home / "fonte.log").exists() else []
    vere = [c for c in chiamate if "--prova" not in c]
    fonte.unlink()                                                 # i todo si leggono dall'archivio locale
    dopo_h = sorted(p.name for p in (lab.h / "fenice-vecchia").iterdir()) if (lab.h / "fenice-vecchia").is_dir() else []
    dopo_v = sorted(p.name for p in (lab.h / "fenice").iterdir())
    if r.returncode == 0:
        rossi.append("RB16 con l'archivio rotto l'unione esce 0")
    if vere:
        rossi.append(f"RB16 la fonte esterna ha unito prima delle scritture locali: {vere}")
    if dopo_h != prima_h or dopo_v != prima_v or sorted(lab.todo("fenice-vecchia")) != ["Chiamare la tipografia", "Mandare le bozze"]:
        rossi.append(f"RB16 un errore a metà non rimette i file: handoff {dopo_h} / {dopo_v}, todo {lab.todo('fenice-vecchia')}")
    if (lab.mem / "progetti" / "progetto-fenice.md").read_text(encoding="utf-8") != scheda_v:
        rossi.append("RB16 un errore a metà lascia la scheda del vincitore cambiata")

    # 2. Un file col punto presente nei due progetti.
    lab = _laboratorio(repo, tmp / "b")
    for nome in ("fenice-vecchia", "fenice"):
        (lab.h / nome / ".ultimo-fine-completo").write_text("2026-11-18\n", encoding="utf-8")
    r = lab.arturo("progetti", "unisci", "fenice-vecchia", "fenice")
    nomi = sorted(p.name for p in (lab.h / "fenice").iterdir())
    if r.returncode != 0 or any(n.startswith("-") for n in nomi) or ".ultimo-fine-completo-fenice-vecchia" not in nomi:
        rossi.append(f"RB16 il file col punto del perdente prende un nome sbagliato: rc {r.returncode} {nomi} {r.stderr[-200:]!r}")
    return rossi


# --- RB17 ---------------------------------------------------------------------------------------------------

def rb17(repo: Path, tmp: Path) -> list:
    home = casa(tmp, "h17")
    cl = home / ".claude"
    for d in ("bin", "hooks"):
        shutil.copytree(str(repo / d), str(cl / d), ignore=shutil.ignore_patterns("__pycache__", "*.local"))
    progetto = home / "Documents" / "ClaudeCode" / "mio-libro"
    progetto.mkdir(parents=True)
    env = env_di(home, ARTURO_MEMORIA="1")
    git(progetto, "init", "-q", "-b", "main", env=env)
    (progetto / "capitolo.md").write_text("uno\n", encoding="utf-8")
    git(progetto, "add", "-A", env=env)
    git(progetto, "commit", "-q", "-m", "primo", env=env)
    cartella_h = cl / "data" / "handoffs" / "mio-libro"
    cartella_h.mkdir(parents=True)
    # Gli handoff di altre sessioni chiuse da poco: tutti i minuti da adesso a dieci minuti dopo sono presi.
    ora = time.localtime()
    base = time.mktime((ora.tm_year, ora.tm_mon, ora.tm_mday, ora.tm_hour, ora.tm_min, 0, 0, 0, -1))
    presi = {}
    for minuti in range(-2, 14):
        nome = time.strftime("HANDOFF_%Y-%m-%d_%H-%M.md", time.localtime(base + minuti * 60))
        testo = f"# Session Handoff\n## Progetto\n- Nome: mio-libro\n- Sessione: altra-{minuti}\n## Task Pendenti\nNessuno.\n"
        (cartella_h / nome).write_text(testo, encoding="utf-8")
        presi[nome] = testo
    projects = cl / "projects" / "-prova"
    projects.mkdir(parents=True)
    sid = "s-rb17"
    t = projects / f"{sid}.jsonl"
    t.write_text(json.dumps({"type": "user", "entrypoint": "cli", "sessionId": sid,
                             "message": {"role": "user", "content": "Riscrivi il capitolo due con la scena del tram"}})
                 + "\n", encoding="utf-8")
    dati = {"session_id": sid, "transcript_path": str(t), "cwd": str(progetto), "reason": "prompt_input_exit"}
    r = lancia([sys.executable, "-B", str(cl / "bin" / "salva-automatico.py")], env, cwd=progetto, entrata=json.dumps(dati))
    cambiati = [n for n, testo in presi.items() if (cartella_h / n).read_text(encoding="utf-8") != testo]
    nuovi = [p.name for p in cartella_h.glob("HANDOFF_*.md") if p.name not in presi]
    if cambiati or len(nuovi) != 1:
        return [f"RB17 l'handoff automatico ha sovrascritto {cambiati}, nuovi {nuovi}: {r.stdout.strip()[-300:]!r}"]
    return []


# --- RB18 ---------------------------------------------------------------------------------------------------

MIGRA = r"""
import importlib.util, os, sys
from pathlib import Path
spec = importlib.util.spec_from_file_location("migra_prova", os.path.join(REPO, "bin", "migra.py"))
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
cartella = Path(os.environ["DOVE"]) / "copia"
(cartella / "codice" / "bin").mkdir(parents=True)
tornato = []
m.analizza = lambda orsa, unica=False: {"ferma": [], "sessioni": 0, "orsa": Path(os.environ["DOVE"])}
m.fai_copia = lambda a: cartella
class Personale:
    @staticmethod
    def separa(commit=False, r=None):
        return 0
m._modulo = lambda nome, f: Personale
m.passo = lambda c, nome: None
m.installa_plugin = lambda orsa, c: c
m.scrivi_settings = lambda a, copia: None
def interrotta(a, c):
    raise KeyboardInterrupt
m.togli_arturo = interrotta
m.indietro = lambda c, conserva=True: tornato.append(conserva) or 0
try:
    uscita = m.cmd_migra()
except KeyboardInterrupt:
    uscita = "KeyboardInterrupt"
print(f"USCITA={uscita} TORNATO={tornato}")
"""


def rb18(repo: Path, tmp: Path) -> list:
    home = casa(tmp, "h18")
    r = python_con(repo, MIGRA, env_di(home, DOVE=str(tmp)))
    if "USCITA=130 TORNATO=[False]" not in r.stdout:
        return [f"RB18 Ctrl-C a metà della migrazione non torna indietro: {(r.stdout + r.stderr)[-400:]!r}"]
    return []


# --- RB19 ---------------------------------------------------------------------------------------------------

TEMPORANEI = r"""
import importlib.util, os, sys
from pathlib import Path
dove = Path(os.environ["DOVE"])
def carica(nome, rel):
    spec = importlib.util.spec_from_file_location(nome, os.path.join(REPO, rel))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m
usati = []
vero = os.replace
def registra(src, dst, *a, **k):
    usati.append(os.path.basename(str(src)))
    return vero(src, dst, *a, **k)
os.replace = registra
rossi = []
scrittori = {
    "aggiornamenti.scrivi": lambda: carica("agg_prova", "bin/aggiornamenti.py").scrivi(dove / "aggiornamento.json", {"a": 1}),
    "agente-worktree.scrivi": lambda: carica("aw_prova", "hooks/agente-worktree.py").scrivi(dove / "agente.json", {"a": 1}),
    "correzioni.scrivi": lambda: carica("corr_prova", "bin/correzioni.py").scrivi("sessione-prova", [{"testo": "x"}]),
    "rinomina.scrivi_atomico": lambda: carica("rin_prova", "bin/rinomina.py").scrivi_atomico(dove / "nota.md", "x\n"),
}
for nome, scrivi in scrittori.items():
    usati.clear()
    scrivi()
    scrivi()
    if len(usati) != 2 or usati[0] == usati[1]:
        rossi.append(f"{nome} usa lo stesso temporaneo: {usati}")
print("ROSSI=" + " | ".join(rossi))
"""


def rb19(repo: Path, tmp: Path) -> list:
    home = casa(tmp, "h19")
    r = python_con(repo, TEMPORANEI, env_di(home, DOVE=str(tmp), ARTURO_RADICE=str(tmp / "radice")))
    righe = [x for x in r.stdout.splitlines() if x.startswith("ROSSI=")]
    if r.returncode != 0 or not righe:
        return [f"RB19 il banco dei temporanei non è arrivato in fondo: rc {r.returncode} {(r.stdout + r.stderr)[-400:]!r}"]
    esito = righe[0][len("ROSSI="):]
    return [f"RB19 {esito}"] if esito else []


# --- RB20 ---------------------------------------------------------------------------------------------------

SESSIONI = r"""
import importlib.util, os, sys
spec = importlib.util.spec_from_file_location("agg_prova", os.path.join(REPO, "bin", "aggiornamenti.py"))
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
claude = os.environ["CLAUDE_CON_SPAZI"]
righe = [f"{claude} --resume", f"{claude} daemon run", "/usr/bin/vim /tmp/claude", "-zsh"]
print(f"CONTATE={m.conta_sessioni(righe, windows=False)}")
"""


def rb20(repo: Path, tmp: Path) -> list:
    home = casa(tmp, "h20")
    claude = tmp / "Mario Rossi" / ".local" / "bin" / "claude"
    claude.parent.mkdir(parents=True)
    claude.write_text("#!/bin/sh\n", encoding="utf-8")
    claude.chmod(claude.stat().st_mode | stat.S_IXUSR)
    r = python_con(repo, SESSIONI, env_di(home, CLAUDE_CON_SPAZI=str(claude).replace(os.sep, "/")))
    if "CONTATE=1" not in r.stdout:
        return [f"RB20 una sessione da una home con spazi non conta come una: {(r.stdout + r.stderr)[-300:]!r}"]
    return []


# --- RB21 ---------------------------------------------------------------------------------------------------

def rb21(repo: Path, tmp: Path) -> list:
    home = casa(tmp, "h21")
    attese = home / ".claude" / "session-env" / "telemetria-attese.json"
    ora = int(time.time())
    attese.write_text(json.dumps({"toolu_mia": {"guardia": "block-dangerous.py", "ora": ora},
                                  "toolu_altra": {"guardia": "comms-guard.py", "ora": ora}}), encoding="utf-8")
    t = tmp / "sessione.jsonl"
    t.write_text(json.dumps({"type": "assistant", "message": {"content": [
        {"type": "tool_use", "id": "toolu_mia", "name": "Bash", "input": {"command": "rm -rf build"}}]}}) + "\n",
        encoding="utf-8")
    env = env_di(home, ARTURO_MEMORIA="0", ARTURO_CODICE=str(repo))
    lancia([BASH, str(repo / "hooks" / "session-end.sh")], env, cwd=tmp,
           entrata=json.dumps({"session_id": "s-mia", "transcript_path": str(t), "hook_event_name": "SessionEnd",
                               "reason": "other"}))
    rimaste: dict = {}
    for _ in range(100):                                          # telemetria.py fine gira in background
        try:
            rimaste = json.loads(attese.read_text(encoding="utf-8")) if attese.exists() else {}
        except ValueError:
            rimaste = {}
        if "toolu_mia" not in rimaste:
            break
        time.sleep(0.1)
    if sorted(rimaste) != ["toolu_altra"]:
        return [f"RB21 la chiusura di una sessione lascia le conferme in attesa {sorted(rimaste)} invece della sola "
                "conferma dell'altra sessione"]
    return []


def prova(repo: Path) -> list:
    rossi = []
    for caso in (rb11, rb12, rb13, rb14, rb15, rb16, rb17, rb18, rb19, rb20, rb21):
        with tempfile.TemporaryDirectory(prefix="arturo-rb-") as tmp:
            try:
                rossi += caso(repo, Path(tmp))
            except (FileNotFoundError, subprocess.CalledProcessError, AssertionError) as e:
                rossi.append(f"{caso.__name__.upper()} il banco si è fermato: {type(e).__name__}: {str(e)[-300:]}")
    return rossi


def main() -> int:
    for flusso in (sys.stdout, sys.stderr):  # su Windows la pipe è in cp1252
        if hasattr(flusso, "reconfigure"):
            flusso.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument("--baseline-ref")
    argomenti = parser.parse_args()
    rossi = prova(Path(argomenti.repo).resolve())
    if argomenti.baseline_ref:
        codici = sorted({r.split()[0] for r in rossi})
        assert codici == DISCRIMINANTI, f"baseline non discriminante: rossi {codici}, attesi {DISCRIMINANTI}"
        print(f"BASELINE_DISCRIMINANTE={','.join(codici)}")
        return 0
    for r in rossi:
        print("ROSSO", r)
    print(f"bug bassi della revisione del 20/11: {len(CASI) - len({r.split()[0] for r in rossi})}/{len(CASI)} casi verdi")
    return 1 if rossi else 0


if __name__ == "__main__":
    sys.exit(main())
