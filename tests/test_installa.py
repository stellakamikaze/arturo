#!/usr/bin/env python3
"""Banco di sito/installa.sh, l'installatore che innesta Arturo dentro ~/.claude sul posto.

Ogni caso gira in una HOME usa e getta, con un PATH di sistema senza il claude vero e un
repository locale al posto di GitHub (ARTURO_REPO). Nessun caso tocca la rete.

Dal 1/11/2026 lo script non sposta più ~/.claude (prima: mv "$dest" "$b", poi i file tornavano
dal backup). Con una sessione di Claude Code aperta lo spostamento perdeva le righe scritte nel
frattempo, e su Windows un file aperto lo bloccava. caso_innesto_sessione_viva lo prova.

Revisione del 1/11/2026 (I1-I7, F2, F4): ogni correzione ha un caso. caso_dentro_claude_code vuole
la finestra nuova quando claude stava solo in ~/.local/bin (I1); caso_python_windows vuole il
python3.exe creato accanto al python vero e il riavvio dopo winget (I2, F2); caso_settings_nel_backup
vuole la frase sulle impostazioni di prima (I3); caso_cartella_collegata vuole lo stop su una
cartella che è un collegamento (I4); caso_interrotto_backup vuole tolta la copia parziale (I6);
caso_mac_licenza vuole git --version riuscito sul Mac (I7); caso_repo_estraneo, caso_config_dir e
caso_guida_rimandi vogliono la strada giusta per un ~/.claude già git e per CLAUDE_CONFIG_DIR (F4).

--avvelena il banco lo prova da solo. Prende con git show l'installatore con mv di VELENO_REF e
vuole che caso_innesto_sessione_viva diventi rosso col motivo "righe perse". Poi, per ogni voce di
VELENI, toglie una correzione dallo script di oggi e vuole il caso rosso col suo motivo. Esce 1 solo
se ogni veleno è rosso col motivo atteso; un veleno verde, rosso per un altro motivo o senza il
punto da togliere fa uscire 0, e verifica-allineamento.sh lo legge come veleno verde.
"""
import argparse
import hashlib
import html
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import time
from pathlib import Path

# Su Windows "bash" per nome è il lanciatore di WSL in System32: serve il bash del PATH (Git Bash, #4362).
BASH = shutil.which("bash") or "bash"

PATH_BASE = "/usr/bin:/bin:/usr/sbin:/sbin"

# L'ultima versione dell'installatore che spostava ~/.claude con mv (landing-v2, 1/11/2026).
VELENO_REF = "e7c5a7d"


def _posix(p) -> str:
    """Su Windows un percorso C:\\… nel PATH di bash spezza la lista ai due punti: va in forma /c/… (#4362)."""
    if os.name != "nt":
        return str(p)
    return subprocess.run(["cygpath", "-u", str(p)], capture_output=True, text=True, check=True).stdout.strip()


if os.name == "nt":
    # Git Bash tiene git in /mingw64/bin e python3 sta fuori dalle cartelle di sistema.
    PATH_BASE += ":/mingw64/bin:" + _posix(Path(shutil.which("python3") or sys.executable).parent)

GIT_VERO = _posix(shutil.which("git") or "/usr/bin/git")
CMP_VERO = _posix(shutil.which("cmp") or "/usr/bin/cmp")
WINDOWS = os.name == "nt"


def collega(destinazione: Path, cartella: Path):
    """Un collegamento a una cartella. Su Windows senza il privilegio dei symlink si usa una junction:
    anche quella bash la vede con [ -L ]."""
    try:
        os.symlink(str(cartella), str(destinazione), target_is_directory=True)
    except OSError:
        if not WINDOWS:
            raise
        import _winapi
        _winapi.CreateJunction(str(cartella), str(destinazione))


def e_collegamento(p: Path) -> bool:
    if os.path.islink(p):
        return True
    try:
        return bool(getattr(os.lstat(p), "st_file_attributes", 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT)
    except (OSError, AttributeError):
        return False

# Una sessione di Claude Code aperta: ogni 100 ms accoda una riga alla sessione e a history.jsonl,
# aprendo il file per nome come fa Claude Code. Segna quali righe sono entrate e quali no.
SCRITTORE = r'''
import json, os, sys, time
casa, stop, esito = sys.argv[1:4]
file = {"s.jsonl": os.path.join(casa, ".claude", "projects", "x", "s.jsonl"),
        "history.jsonl": os.path.join(casa, ".claude", "history.jsonl")}
ok = {n: [] for n in file}
fallite = []
k = 0
while not os.path.exists(stop):
    for nome, percorso in file.items():
        try:
            with open(percorso, "ab") as f:
                f.write(json.dumps({"nuova": k}).encode() + b"\n")
            ok[nome].append(k)
        except OSError as e:
            fallite.append(f"{nome} {k}: {e.__class__.__name__}")
    k += 1
    time.sleep(0.1)
with open(esito, "w", encoding="utf-8") as f:
    json.dump({"ok": ok, "fallite": fallite}, f)
'''


def sh(*args, cwd=None):
    subprocess.run(args, cwd=cwd, check=True, capture_output=True)


def origine(radice: Path) -> Path:
    """Un repository con 'stellakamikaze/arturo' nel percorso, come il remoto vero: un file in cima,
    settings.json e un file in una cartella, come Arturo."""
    lavoro = radice / "lavoro"
    (lavoro / "hooks").mkdir(parents=True)
    (lavoro / "README.md").write_bytes(b"Arturo\n")
    (lavoro / "settings.json").write_bytes(b'{"hooks": {}}\n')
    (lavoro / "hooks" / "esempio.sh").write_bytes(b"#!/bin/sh\nexit 0\n")
    sh("git", "init", "-q", "-b", "main", cwd=lavoro)
    sh("git", "add", "README.md", "settings.json", "hooks/esempio.sh", cwd=lavoro)
    sh("git", "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "-m", "x", cwd=lavoro)
    nudo = radice / "stellakamikaze" / "arturo.git"
    sh("git", "clone", "-q", "--bare", str(lavoro), str(nudo))
    return nudo


def foto(radice: Path) -> dict:
    """Percorsi e contenuti di un albero: cartelle col segno "dir", file con lo sha256."""
    esito = {}
    if not radice.exists():
        return esito
    for cartella, sotto, file in os.walk(radice):
        base = Path(cartella)
        for n in sotto:
            esito[(base / n).relative_to(radice).as_posix()] = "dir"
        for n in file:
            esito[(base / n).relative_to(radice).as_posix()] = hashlib.sha256((base / n).read_bytes()).hexdigest()
    return esito


def differenze(prima: dict, dopo: dict) -> str:
    tutte = sorted(set(prima) | set(dopo))
    return ", ".join(p for p in tutte if prima.get(p) != dopo.get(p))[:300]


class Lab:
    def __init__(self, script: Path, radice: Path, nome: str, sorgente: Path):
        self.script = script
        self.radice = radice
        self.nome = nome
        self.sorgente = sorgente
        self.dir = radice / nome
        self.home = self.dir / "home"
        self.bin = self.dir / "bin"
        self.home.mkdir(parents=True)
        self.bin.mkdir()
        self.repo = str(radice / "stellakamikaze" / "arturo.git")
        # Nessun caso tocca il Path vero di Windows: un powershell.exe finto davanti a tutto annota
        # cosa riceve e non risponde.
        self.powershell = self.dir / "powershell.txt"
        self.finto("powershell.exe", f'cat > "{_posix(self.powershell)}"')

    def altro(self, suffisso: str) -> "Lab":
        return Lab(self.script, self.radice, self.nome + suffisso, self.sorgente)

    def claude_locale(self):
        p = self.home / ".local" / "bin" / "claude"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(b"#!/bin/sh\necho 2.1.308\n")
        p.chmod(0o755)

    def finto(self, nome: str, corpo: str):
        # Fine riga LF anche su Windows: con CRLF sh legge "$@"\r.
        p = self.bin / nome
        p.write_bytes(("#!/bin/sh\n" + corpo + "\n").encode())
        p.chmod(0o755)

    def config_vecchia(self):
        c = self.home / ".claude"
        (c / "projects").mkdir(parents=True)
        (c / ".credentials.json").write_text("{}")
        (c / "mio.txt").write_text("mio")

    def lancia(self, repo=None, extra=None, script=None):
        env = {
            "HOME": _posix(self.home),
            "PATH": f"{_posix(self.bin)}:{PATH_BASE}",
            "SHELL": "/bin/zsh",
            "ARTURO_REPO": repo or _posix(self.repo),  # con le barre dritte, come lo scrive chi installa
            "LANG": "C.UTF-8",
        }
        env.update(extra or {})
        r = subprocess.run([BASH, script or str(self.script)], env=env, capture_output=True, text=True,
                           encoding="utf-8", stdin=subprocess.DEVNULL, timeout=120)
        return r.returncode, r.stdout + r.stderr

    def backup(self):
        return sorted(p.name for p in self.home.glob(".claude-backup-*"))


def caso_nuova(lab):
    lab.claude_locale()
    lab.config_vecchia()
    rc, out = lab.lancia()
    c = lab.home / ".claude"
    assert rc == 0, f"rc {rc}\n{out}"
    assert (c / ".git").is_dir() and (c / "README.md").is_file(), "Arturo non è in ~/.claude"
    assert (c / ".credentials.json").is_file() and (c / "projects").is_dir(), "login o sessioni non al loro posto"
    assert (c / "mio.txt").read_text(encoding="utf-8") == "mio", "un file della persona è sparito"
    assert lab.backup() == [], f"backup senza file sostituiti: {lab.backup()}"
    rcfile = (lab.home / ".zshrc").read_text(encoding="utf-8")
    assert rcfile.count(".local/bin") == 1, f"PATH non aggiunto una volta:\n{rcfile}"
    assert "Arturo installato" in out and "tappa-5" not in out and "cd ~/.claude" not in out, out
    # Seconda volta: niente backup nuovo, niente riga doppia.
    rc, out = lab.lancia()
    assert rc == 0 and "già installato" in out, f"rc {rc}\n{out}"
    assert lab.backup() == [], f"backup in più: {lab.backup()}"
    assert (lab.home / ".zshrc").read_text(encoding="utf-8").count(".local/bin") == 1, "riga del PATH doppia"


def caso_senza_cartella(lab):
    lab.claude_locale()
    rc, out = lab.lancia()
    assert rc == 0 and (lab.home / ".claude" / ".git").is_dir(), f"rc {rc}\n{out}"
    assert lab.backup() == [] and "sostituito" not in out, out


def caso_clone_fallito(lab):
    lab.claude_locale()
    lab.config_vecchia()
    prima = foto(lab.home / ".claude")
    rc, out = lab.lancia(repo=str(lab.home / "non-esiste" / "stellakamikaze" / "arturo.git"))
    assert rc == 1, f"rc {rc}\n{out}"
    assert foto(lab.home / ".claude") == prima, "la cartella è cambiata"
    assert lab.backup() == [], f"backup rimasto: {lab.backup()}"
    assert "non ho toccato niente" in out, out


def caso_python_vecchio(lab):
    lab.claude_locale()
    lab.config_vecchia()
    lab.finto("python3", "exit 1")
    rc, out = lab.lancia()
    assert rc == 1 and "MANCA python3" in out and "Comando:" in out, f"rc {rc}\n{out}"
    assert (lab.home / ".claude" / "mio.txt").is_file() and lab.backup() == [], "ha toccato ~/.claude"


def caso_senza_claude(lab):
    lab.config_vecchia()
    rc, out = lab.lancia()
    assert rc == 1 and "MANCA claude. Comando:" in out, f"rc {rc}\n{out}"
    assert not (lab.home / ".claude" / ".git").exists() and lab.backup() == [], "ha toccato ~/.claude"


def caso_dentro_claude_code(lab):
    # claude sta solo in ~/.local/bin: la finestra aperta non lo trova dopo /exit, serve una finestra
    # nuova (I1). Sul Mac con bash la riga va in .bash_profile, su Windows anche nel Path utente.
    lab.claude_locale()
    rc, out = lab.lancia(extra={"CLAUDECODE": "1"})
    assert rc == 0, f"rc {rc}\n{out}"
    for parola in ("/exit", "claude", "/setup", "non lanciare altri comandi"):
        assert parola in out, f"manca {parola!r}\n{out}"
    for vecchia in ("cd ~/.claude", "tappa-5"):
        assert vecchia not in out, f"resta {vecchia!r}\n{out}"
    assert "aprine una nuova" in out and "4. Scrivi /setup" in out, f"finestra nuova assente: claude non si trova\n{out}"
    # Mac con bash: il Terminale apre shell di login, che leggono .bash_profile.
    m = lab.altro("-mac-bash")
    m.claude_locale()
    m.finto("uname", "echo Darwin")
    m.finto("xcode-select", "exit 0")
    rc, out = m.lancia(extra={"CLAUDECODE": "1", "SHELL": "/bin/bash"})
    profilo = m.home / ".bash_profile"
    assert rc == 0 and profilo.is_file() and ".local/bin" in profilo.read_text(encoding="utf-8"), \
        f"finestra nuova assente: PATH non in .bash_profile sul Mac\n{out}"
    assert "finestra del terminale" in out, f"finestra nuova assente: messaggio del Mac\n{out}"
    # Windows: PowerShell non legge .bashrc, la cartella va nel Path utente.
    w = lab.altro("-win")
    w.claude_locale()
    w.finto("uname", "echo MINGW64_NT-10.0-26100")
    w.finto("powershell.exe", f'cat > "{_posix(w.powershell)}"; echo AGGIUNTO')
    rc, out = w.lancia(extra={"CLAUDECODE": "1"})
    ricevuto = w.powershell.read_text(encoding="utf-8") if w.powershell.is_file() else ""
    assert rc == 0 and "DoNotExpandEnvironmentNames" in ricevuto and "ExpandString" in ricevuto, \
        f"finestra nuova assente: Path di Windows non toccato\n{out}"
    assert "Chiudi questa finestra di PowerShell e aprine una nuova" in out and "aggiunto al Path di Windows" in out, \
        f"finestra nuova assente: messaggio di Windows\n{out}"


def caso_config_di_prima(lab):
    # La ~/.claude di prima ha cose della persona: restano al loro posto, mai spostate (#3825).
    lab.claude_locale()
    c = lab.home / ".claude"
    (c / "data" / "memory").mkdir(parents=True)
    (c / "data" / "memory" / "nota.md").write_text("mia")
    (c / "CLAUDE.md").write_text("# Gunnar")
    (c / "session-env").mkdir()
    (c / "session-env" / "telemetria.json").write_text('{"spenta": true}')
    voci = ("data/memory/nota.md", "CLAUDE.md", "session-env/telemetria.json")
    mtime = {f: (c / f).stat().st_mtime_ns for f in voci}
    rc, out = lab.lancia()
    assert rc == 0, f"rc {rc}\n{out}"
    for f, t in zip(voci, ("mia", "# Gunnar", '{"spenta": true}')):
        assert (c / f).is_file() and (c / f).read_text(encoding="utf-8") == t, f"non c'è più {f}"
        assert (c / f).stat().st_mtime_ns == mtime[f], f"{f} è stato riscritto"
    assert lab.backup() == [], f"backup con file della persona: {lab.backup()}"


def caso_sincronizzata(lab):
    # Arturo sincronizzato su un repository privato: origin è suo, upstream è Arturo. Non si reinstalla.
    lab.claude_locale()
    c = lab.home / ".claude"
    sh("git", "init", "-q", str(c))
    sh("git", "-C", str(c), "remote", "add", "origin", "https://github.com/qualcuno/config-privata.git")
    sh("git", "-C", str(c), "remote", "add", "upstream", "https://github.com/stellakamikaze/arturo.git")
    (c / "mio.txt").write_text("mio")
    rc, out = lab.lancia()
    assert rc == 0 and "già installato" in out, f"rc {rc}\n{out}"
    assert (c / "mio.txt").is_file() and lab.backup() == [], "ha toccato una config sincronizzata"


def caso_innesto_sessione_viva(lab):
    # Una sessione aperta scrive mentre lo script lavora. Il clone è rallentato di un secondo,
    # così ogni strada che lascia ~/.claude vuota per un momento perde righe.
    lab.claude_locale()
    lab.finto("git", f'if [ "$1" = clone ]; then sleep 1; fi\nexec "{GIT_VERO}" "$@"')
    c = lab.home / ".claude"
    (c / "projects" / "x").mkdir(parents=True)
    vecchie = {"s.jsonl": [b'{"vecchia": %d}' % i for i in range(3)],
               "history.jsonl": [b'{"vecchia": %d}' % i for i in range(2)]}
    percorsi = {"s.jsonl": c / "projects" / "x" / "s.jsonl", "history.jsonl": c / "history.jsonl"}
    for nome, righe in vecchie.items():
        percorsi[nome].write_bytes(b"".join(r + b"\n" for r in righe))
    credenziali = b'{"claudeAiOauth": {"accessToken": "finto"}}\n'
    (c / ".credentials.json").write_bytes(credenziali)
    scrittore = lab.dir / "scrittore.py"
    scrittore.write_text(SCRITTORE, encoding="utf-8")
    stop, esito = lab.dir / "stop", lab.dir / "esito.json"
    proc = subprocess.Popen([sys.executable, str(scrittore), str(lab.home), str(stop), str(esito)])
    try:
        limite = time.time() + 20
        while percorsi["s.jsonl"].read_bytes().count(b"\n") < 6 and time.time() < limite:
            time.sleep(0.05)
        rc, out = lab.lancia()
        time.sleep(0.5)
    finally:
        stop.write_text("")
        proc.wait(timeout=20)
    rep = json.loads(esito.read_text(encoding="utf-8"))
    assert not rep["fallite"], (f"righe perse: {len(rep['fallite'])} scritture fallite durante l'installazione "
                                f"({', '.join(rep['fallite'][:3])})")
    for nome, righe in vecchie.items():
        attese = righe + [b'{"nuova": %d}' % k for k in rep["ok"][nome]]
        trovate = percorsi[nome].read_bytes().splitlines() if percorsi[nome].is_file() else []
        assert trovate == attese, f"righe perse in {nome}: {len(trovate)} in ~/.claude, attese {len(attese)}"
    assert len(rep["ok"]["s.jsonl"]) >= 15, f"lo scrittore non ha girato durante l'installazione: {rep['ok']}"
    assert rc == 0, f"rc {rc}\n{out}"
    assert (c / ".credentials.json").read_bytes() == credenziali, ".credentials.json cambiato"
    dentro = sorted(p.name for p in c.glob(".claude-backup-*"))
    assert not dentro, f"backup dentro ~/.claude: {dentro}"


def caso_handle_aperto(lab):
    # Su Windows un file aperto blocca lo spostamento della sua cartella: l'innesto non sposta niente.
    lab.claude_locale()
    c = lab.home / ".claude"
    (c / "projects" / "x").mkdir(parents=True)
    aperto = c / "projects" / "x" / "aperto.jsonl"
    with open(aperto, "ab") as f:
        f.write(b"prima\n")
        f.flush()
        rc, out = lab.lancia()
        f.write(b"dopo\n")
    assert rc == 0, f"rc {rc}\n{out}"
    assert aperto.read_bytes() == b"prima\ndopo\n", f"file aperto cambiato: {aperto.read_bytes()!r}"
    assert (c / ".git").is_dir(), "Arturo non è in ~/.claude"


def caso_settings_nel_backup(lab):
    # Il settings.json di prima, con l'hook di un'altra app, va nel backup identico byte per byte,
    # e `arturo personale hook-precedenti` (bin/personale.py di main) lo trova lì.
    lab.claude_locale()
    c = lab.home / ".claude"
    (c / "claudebar").mkdir(parents=True)
    (c / "claudebar" / "hook.sh").write_bytes(b"#!/bin/sh\n")
    (c / "README.md").write_bytes(b"il mio readme\n")
    vecchio = (b'{"hooks": {"PreToolUse": [{"matcher": "Bash", "hooks": '
               b'[{"type": "command", "command": "~/.claude/claudebar/hook.sh"}]}]}}\n')
    (c / "settings.json").write_bytes(vecchio)
    rc, out = lab.lancia()
    assert rc == 0, f"rc {rc}\n{out}"
    b = lab.backup()
    assert len(b) == 1, f"backup: {b}"
    copia = lab.home / b[0]
    assert (copia / "settings.json").read_bytes() == vecchio, "settings.json non identico nel backup"
    assert (copia / "README.md").read_bytes() == b"il mio readme\n", "README.md sostituito non è nel backup"
    # json e non byte: con core.autocrlf (Git per Windows) il reset scrive CRLF.
    assert json.loads((c / "settings.json").read_text(encoding="utf-8")) == {"hooks": {}}, \
        "il settings.json di Arturo non c'è"
    assert (c / "claudebar" / "hook.sh").is_file(), "un file della persona è sparito"
    assert f"sostituito sono in {_posix(copia)}" in out, out
    frase = ("Il tuo accesso e le tue conversazioni restano dove sono, e i plugin restano installati. Il tuo vecchio "
             "settings.json finisce in una copia di sicurezza con la data nel nome: /setup ti propone di riportare hook, plugin e preferenze.")
    assert frase in out, f"impostazioni di prima non dette: plugin e preferenze nella copia senza avviso\n{out}"
    personale = None
    for ramo in ("origin/main", "main"):
        r = subprocess.run(["git", "-C", str(lab.sorgente), "show", f"{ramo}:bin/personale.py"], capture_output=True)
        if r.returncode == 0:
            personale = r.stdout
            break
    assert personale, "non trovo bin/personale.py in origin/main o main"
    script = lab.dir / "personale.py"
    script.write_bytes(personale)
    env = dict(os.environ, ARTURO_RADICE=str(c), HOME=str(lab.home), USERPROFILE=str(lab.home),
               PYTHONIOENCODING="utf-8")
    r = subprocess.run([sys.executable, str(script), "hook-precedenti"], env=env, capture_output=True,
                       text=True, encoding="utf-8", timeout=60)
    atteso = "HOOK: PreToolUse [Bash]: ~/.claude/claudebar/hook.sh"
    assert r.returncode == 0 and atteso in r.stdout, f"hook-precedenti non trova l'hook:\n{r.stdout}{r.stderr}"


def caso_repo_estraneo(lab):
    lab.claude_locale()
    c = lab.home / ".claude"
    sh("git", "init", "-q", str(c))
    sh("git", "-C", str(c), "remote", "add", "origin", "https://github.com/qualcuno/altro.git")
    (c / "mio.txt").write_text("mio")
    prima = foto(c)
    rc, out = lab.lancia()
    assert rc == 1, f"rc {rc}\n{out}"
    # La strada a mano comincia con lo stesso script: serve il blocco esteso (F4).
    assert "non è Arturo" in out and "#a-mano-esteso" in out and "B=" in out, f"blocco esteso non nominato\n{out}"
    assert foto(c) == prima, f"albero cambiato: {differenze(prima, foto(c))}"
    assert lab.backup() == [], f"backup: {lab.backup()}"


def caso_reset_fallito(lab):
    # Il reset scrive i file e poi fallisce: tutto torna com'era, senza .git, col backup che resta.
    lab.claude_locale()
    lab.finto("git", f'for a in "$@"; do if [ "$a" = reset ]; then "{GIT_VERO}" "$@"; exit 1; fi; done\n'
                     f'exec "{GIT_VERO}" "$@"')
    lab.config_vecchia()
    c = lab.home / ".claude"
    (c / "README.md").write_bytes(b"il mio readme\n")
    prima = foto(c)
    rc, out = lab.lancia()
    assert rc == 1, f"rc {rc}\n{out}"
    assert not (c / ".git").exists(), "resta .git"
    assert foto(c) == prima, f"non è tornato tutto com'era: {differenze(prima, foto(c))}"
    b = lab.backup()
    assert len(b) == 1 and (lab.home / b[0] / "README.md").read_bytes() == b"il mio readme\n", f"backup: {b}"
    assert "com'era" in out and "Il backup resta in" in out, out


def caso_interrotto(lab):
    # Ctrl-C durante il reset: la trappola rimette tutto com'era.
    lab.claude_locale()
    lab.finto("git", f'for a in "$@"; do if [ "$a" = reset ]; then "{GIT_VERO}" "$@"; kill -INT $PPID; '
                     f'sleep 1; exit 0; fi; done\nexec "{GIT_VERO}" "$@"')
    lab.config_vecchia()
    c = lab.home / ".claude"
    prima = foto(c)
    rc, out = lab.lancia()
    assert rc != 0, f"rc {rc}\n{out}"
    assert not (c / ".git").exists(), f"resta .git\n{out}"
    assert foto(c) == prima, f"non è tornato tutto com'era: {differenze(prima, foto(c))}\n{out}"
    assert lab.backup() == [], f"backup vuoto rimasto: {lab.backup()}"


def caso_conflitto_cartella(lab):
    # Una cartella al posto di un file di Arturo, o un file al posto di una sua cartella: lo script
    # se ne accorge prima di scrivere e non tocca niente.
    for sotto, prepara in (("-cartella", lambda c: (c / "README.md" / "dentro.txt")),
                           ("-file", lambda c: (c / "hooks"))):
        l = lab.altro(sotto)
        l.claude_locale()
        c = l.home / ".claude"
        f = prepara(c)
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text("mio")
        prima = foto(c)
        rc, out = l.lancia()
        assert rc == 1 and "non ho toccato niente" in out.lower(), f"{sotto}: rc {rc}\n{out}"
        assert foto(c) == prima, f"{sotto}: albero cambiato: {differenze(prima, foto(c))}"
        assert l.backup() == [] and not list(l.home.glob(".claude-arturo-*")), f"{sotto}: resti in HOME"


def caso_config_dir(lab):
    lab.claude_locale()
    lab.config_vecchia()
    prima = foto(lab.home)
    rc, out = lab.lancia(extra={"CLAUDE_CONFIG_DIR": _posix(lab.home / "altrove")})
    assert rc == 1 and "CLAUDE_CONFIG_DIR" in out and "Non ho toccato niente" in out, f"rc {rc}\n{out}"
    # Anche la strada a mano scrive in ~/.claude: niente rimando, si dice cosa fare (F4).
    assert "non è supportato" in out and "togli CLAUDE_CONFIG_DIR" in out and "#a-mano" not in out, \
        f"rimando sbagliato per CLAUDE_CONFIG_DIR\n{out}"
    assert foto(lab.home) == prima, f"HOME cambiata: {differenze(prima, foto(lab.home))}"
    # La stessa cartella, scritta con la barra in fondo, non ferma niente.
    rc, out = lab.lancia(extra={"CLAUDE_CONFIG_DIR": _posix(lab.home / ".claude") + "/"})
    assert rc == 0 and (lab.home / ".claude" / ".git").is_dir(), f"rc {rc}\n{out}"


def caso_claude_md_resta(lab):
    lab.claude_locale()
    c = lab.home / ".claude"
    c.mkdir()
    (c / "CLAUDE.md").write_bytes(b"# Le mie istruzioni\n")
    mtime = (c / "CLAUDE.md").stat().st_mtime_ns
    rc, out = lab.lancia()
    assert rc == 0, f"rc {rc}\n{out}"
    assert (c / "CLAUDE.md").read_bytes() == b"# Le mie istruzioni\n", "CLAUDE.md cambiato"
    assert (c / "CLAUDE.md").stat().st_mtime_ns == mtime, "CLAUDE.md riscritto"


def caso_mac_git_rimando(lab):
    # Mac senza gli strumenti di Apple: /usr/bin/git c'è ma non funziona, xcode-select -p fallisce.
    lab.claude_locale()
    lab.config_vecchia()
    lab.finto("uname", "echo Darwin")
    lab.finto("xcode-select", "exit 2")
    lab.finto("git", "exit 1")
    prima = foto(lab.home / ".claude")
    rc, out = lab.lancia()
    assert rc == 1, f"rc {rc}\n{out}"
    assert "MANCA git. Comando: xcode-select --install" in out, out
    assert "until xcode-select -p" in out, out
    assert foto(lab.home / ".claude") == prima, "ha toccato ~/.claude"


def caso_python_windows(lab):
    # I2 e F2. Senza nessun Python la riga MANCA dà winget e il riavvio con una finestra nuova: il
    # PATH nuovo arriva solo ai processi nuovi. PATH senza la cartella del python vero.
    w = lab.altro("-senza")
    w.finto("uname", "echo MINGW64_NT-10.0-26100")
    w.finto("python3", "exit 49")
    w.finto("python", "exit 49")
    w.claude_locale()
    rc, out = w.lancia(extra={"PATH": f"{_posix(w.bin)}:/usr/bin:/bin:/usr/sbin:/sbin:/mingw64/bin"})
    riga = next((r for r in out.splitlines() if r.startswith("MANCA python3")), "")
    assert rc == 1 and "winget install -e --id Python.Python.3.12" in riga and "Comando:" in riga, f"rc {rc}\n{out}"
    assert "finestra nuova" in riga and "incolla di nuovo il link" in riga, f"manca il riavvio dopo winget: {riga!r}"
    assert not (w.home / ".claude").exists() and w.backup() == [], "ha toccato ~/.claude"
    if not WINDOWS:
        return
    # Su Windows vero: python va (un venv, che come python.org non ha python3.exe), python3 è il
    # rimando dello Store. Lo script crea python3.exe accanto a python.exe e va avanti.
    lab.claude_locale()
    lab.finto("python3", "exit 49")
    venv = lab.dir / "venv"
    subprocess.run([sys.executable, "-m", "venv", "--without-pip", str(venv)], check=True, capture_output=True)
    scripts = venv / "Scripts"
    # Un venv creato da python3.exe ha già python3.exe: lo si toglie, come nell'installazione di python.org.
    for doppio in ("python3.exe", "python3"):
        (scripts / doppio).unlink(missing_ok=True)
    rc, out = lab.lancia(extra={"PATH": f"{_posix(scripts)}:{_posix(lab.bin)}:{PATH_BASE}"})
    nuovo = scripts / "python3.exe"
    assert rc == 0 and nuovo.is_file() and "OK python3 (ho creato" in out, f"python3 non creato: rc {rc}\n{out}"
    assert os.stat(nuovo).st_nlink == 2, f"python3.exe non è un hardlink di python.exe: {os.stat(nuovo).st_nlink}"
    assert "Arturo installato" in out, out


def caso_cartella_collegata(lab):
    # I4. Una cartella di Arturo è un collegamento (dotfiles, Dropbox): git reset --hard la sostituirebbe
    # con una cartella vera. Lo script si ferma prima di scrivere, col file nuovo e con quello che c'è già.
    for sotto, gia in (("-nuovo", False), ("-esistente", True)):
        l = lab.altro(sotto)
        l.claude_locale()
        c = l.home / ".claude"
        c.mkdir()
        dot = l.dir / "dotfiles" / "hooks"
        dot.mkdir(parents=True)
        (dot / "mio.sh").write_text("mio")
        if gia:
            (dot / "esempio.sh").write_text("il mio esempio")
        collega(c / "hooks", dot)
        prima = foto(l.dir / "dotfiles")
        rc, out = l.lancia()
        assert rc == 1 and "è un collegamento" in out, f"{sotto}: collegamento non visto: rc {rc}\n{out}"
        assert e_collegamento(c / "hooks"), f"{sotto}: il collegamento è sparito"
        assert foto(l.dir / "dotfiles") == prima, f"{sotto}: la cartella collegata è cambiata"
        assert not (c / ".git").exists() and l.backup() == [], f"{sotto}: resti dell'innesto: {l.backup()}"


def caso_interrotto_backup(lab):
    # I6. Ctrl-C durante la copia di sicurezza: la copia parziale sparisce, ~/.claude resta com'era.
    lab.claude_locale()
    lab.finto("cmp", f'kill -INT $PPID; sleep 1; exec "{CMP_VERO}" "$@"')
    c = lab.home / ".claude"
    c.mkdir()
    (c / "README.md").write_bytes(b"il mio readme\n")
    (c / "settings.json").write_bytes(b"{}\n")
    prima = foto(c)
    rc, out = lab.lancia()
    assert rc != 0, f"rc {rc}\n{out}"
    assert lab.backup() == [], f"copia parziale rimasta: {lab.backup()}\n{out}"
    assert "copia parziale" in out, f"interruzione senza avviso\n{out}"
    assert foto(c) == prima and not (c / ".git").exists(), f"~/.claude cambiata: {differenze(prima, foto(c))}"


def caso_mac_licenza(lab):
    # I7. Sul Mac con Xcode aggiornato e licenza non accettata xcode-select -p riesce, git no.
    lab.claude_locale()
    lab.config_vecchia()
    lab.finto("uname", "echo Darwin")
    lab.finto("xcode-select", "exit 0")
    lab.finto("git", 'echo "You have not agreed to the Xcode license agreements. Please run '
                     'sudo xcodebuild -license from within a Terminal window." >&2; exit 69')
    prima = foto(lab.home / ".claude")
    rc, out = lab.lancia()
    riga = next((r for r in out.splitlines() if r.startswith("MANCA git")), "")
    assert rc == 1 and "sudo xcodebuild -license accept" in riga, f"licenza di Xcode non vista: rc {rc}\n{out}"
    assert "Comando:" in riga and "scaricamento" not in out, out
    assert foto(lab.home / ".claude") == prima, "ha toccato ~/.claude"


def caso_guida_rimandi(lab):
    # F4 e F2 nella guida: ogni rimando dello script porta a un id che esiste, il blocco esteso ha il
    # suo id e lo nomina chi ha ~/.claude già git, e la guida non promette i plugin accesi.
    script = lab.script.read_bytes().decode("utf-8")
    g = html.unescape((lab.sorgente / "sito" / "installa" / "index.html").read_bytes().decode("utf-8"))
    ids = set(re.findall(r'\sid="([^"]+)"', g))
    for ancora in re.findall(r"https://arturo\.stellakamikaze\.org/installa/#([\w-]+)", script):
        assert ancora in ids, f"rimando rotto: lo script porta a #{ancora}, che la guida non ha"
    m = re.search(r'<details[^>]*id="a-mano-esteso"[^>]*>(.*?)</details>', g, re.S)
    assert m and 'B="$HOME/.claude-backup-' in m.group(1), "rimando rotto: #a-mano-esteso non è il blocco con B="
    git_estraneo = [li for li in re.findall(r"<li[^>]*>(.*?)</li>", g, re.S) if "repository git che non è Arturo" in li]
    assert git_estraneo and all("#a-mano-esteso" in li and "B=" in li for li in git_estraneo), \
        f"rimando rotto: la guida non dà il blocco esteso a chi ha ~/.claude già git: {git_estraneo}"
    assert "CLAUDE_CONFIG_DIR" in g, "rimando rotto: la guida non dice cosa fare con CLAUDE_CONFIG_DIR"
    assert "conversazioni e plugin restano dove sono" not in g, "la guida promette ancora i plugin com'erano"
    frase = "Il tuo vecchio settings.json finisce in una copia di sicurezza con la data nel nome: /setup ti propone di riportare hook, plugin e preferenze."
    assert frase in g, "manca la frase sulle impostazioni di prima"
    win = [li for li in re.findall(r'<li data-solo="win">(.*?)</li>', g, re.S) if "python" in li.lower()]
    assert win and all("finestra nuova" in li for li in win), f"python su Windows senza la finestra nuova: {win}"


def caso_manca_formato(lab):
    # git, python3 e claude mancano tutti: tre righe MANCA, ognuna col suo comando.
    lab.finto("git", "exit 1")
    lab.finto("python3", "exit 1")
    rc, out = lab.lancia()
    righe = [r for r in out.splitlines() if r.startswith("MANCA")]
    assert rc == 1 and len(righe) == 3, f"rc {rc}, righe MANCA {len(righe)}\n{out}"
    senza = [r for r in righe if "Comando:" not in r]
    assert not senza, f"righe MANCA senza Comando: {senza}"
    assert not any(r.startswith("MANCA node") for r in out.splitlines()), "node deve restare un avviso"


def caso_si_cancella(lab):
    # Il file scaricato da Claude Code in ~/.arturo-installa.sh resta finché serve, poi sparisce.
    lab.claude_locale()
    copia = lab.home / ".arturo-installa.sh"
    shutil.copyfile(lab.script, copia)
    lab.finto("python3", "exit 1")
    rc, out = lab.lancia(script=_posix(copia))
    assert rc == 1 and copia.is_file(), f"cancellato prima del tempo: rc {rc}\n{out}"
    (lab.bin / "python3").unlink()
    rc, out = lab.lancia(script=_posix(copia))
    assert rc == 0 and "Arturo installato" in out, f"rc {rc}\n{out}"
    assert not copia.exists(), "~/.arturo-installa.sh resta dopo l'installazione"


CASI = [caso_nuova, caso_config_di_prima, caso_sincronizzata, caso_senza_cartella, caso_clone_fallito, caso_python_vecchio,
        caso_senza_claude, caso_dentro_claude_code, caso_innesto_sessione_viva, caso_handle_aperto,
        caso_settings_nel_backup, caso_repo_estraneo, caso_reset_fallito, caso_interrotto, caso_conflitto_cartella,
        caso_config_dir, caso_claude_md_resta, caso_mac_git_rimando, caso_manca_formato, caso_si_cancella,
        caso_python_windows, caso_cartella_collegata, caso_interrotto_backup, caso_mac_licenza, caso_guida_rimandi]

# I veleni della revisione del 1/11/2026: (caso, testo dello script di oggi, testo che toglie la
# correzione, motivo atteso, solo su Windows). Il testo da togliere deve comparire una volta sola.
VELENI = [
    (caso_dentro_claude_code, "    path_nuovo=1\n", "    path_nuovo=0\n", "finestra nuova assente", False),
    (caso_python_windows, '  local riapri="Poi la persona', '  local riapri="" vecchio="Poi la persona',
     "manca il riavvio dopo winget", False),
    (caso_python_windows, "      crea_python3\n      esito_py=$?\n", "      esito_py=1\n", "python3 non creato", True),
    (caso_settings_nel_backup, "    impostazioni=1\n", "    impostazioni=0\n", "impostazioni di prima non dette", False),
    (caso_cartella_collegata, 'if [ -L "$dest/$d" ]; then\n        conflitto="$dest/$d è un collegamento',
     'if false; then\n        conflitto="$dest/$d è un collegamento', "collegamento non visto", False),
    (caso_interrotto_backup, '  ARTURO_BACKUP="$b"\n', "  :\n", "copia parziale rimasta", False),
    (caso_mac_licenza, "if git_uscita=$(git --version 2>&1); then", "if true; then", "licenza di Xcode non vista", False),
    (caso_repo_estraneo, 'echo "Strada a mano: $esteso"', 'echo "Strada a mano: $amano"', "blocco esteso non nominato", False),
    (caso_config_dir, "non è supportato, nemmeno a mano.", "Strada a mano: $amano", "rimando sbagliato per CLAUDE_CONFIG_DIR", False),
]


def prova_veleni(script: Path, radice: Path, sorgente: Path) -> bool:
    """True se ogni veleno è rosso col suo motivo. Stampa una riga FAIL per ogni rosso."""
    testo = script.read_bytes().decode("utf-8")
    tutti = True
    for i, (caso, vecchio, nuovo, motivo, solo_windows) in enumerate(VELENI):
        nome = f"{caso.__name__} ({motivo})"
        if solo_windows and not WINDOWS:
            print(f"VELENO {nome}: saltato, vale solo su Windows")
            continue
        if testo.count(vecchio) != 1:
            print(f"GUASTO veleno {nome}: il testo da togliere compare {testo.count(vecchio)} volte")
            tutti = False
            continue
        rotto = radice / f"veleno-{i}.sh"
        rotto.write_bytes(testo.replace(vecchio, nuovo).encode("utf-8"))
        lab = Lab(rotto, radice, f"veleno-{i}-{caso.__name__}", sorgente)
        try:
            caso(lab)
        except AssertionError as e:
            if motivo in str(e):
                print(f"FAIL {caso.__name__}: {str(e).splitlines()[0]}")
                continue
            print(f"VELENO {nome}: rosso per un altro motivo: {str(e).splitlines()[0]}")
        else:
            print(f"VELENO VERDE {nome}")
        tutti = False
    return tutti


def main():
    for flusso in (sys.stdout, sys.stderr):
        try:
            flusso.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=str(Path(__file__).resolve().parent.parent))
    ap.add_argument("--avvelena", action="store_true",
                    help=f"prova caso_innesto_sessione_viva sull'installatore con mv di {VELENO_REF}: deve dare rosso")
    a = ap.parse_args()
    sorgente = Path(a.repo)
    script = sorgente / "sito" / "installa.sh"
    casi = CASI
    if not script.is_file():
        print(f"FAIL: manca {script}")
        return 1
    passati = 0
    with tempfile.TemporaryDirectory() as t:
        radice = Path(t)
        if a.avvelena:
            r = subprocess.run(["git", "-C", str(sorgente), "show", f"{VELENO_REF}:sito/installa.sh"],
                               capture_output=True)
            if r.returncode != 0 or b'mv "$dest" "$b"' not in r.stdout:
                print(f"GUASTO: non trovo l'installatore con mv in {VELENO_REF}")
                return 3
            origine(radice)
            veleni_rossi = prova_veleni(script, radice, sorgente)
            script = radice / "installa-mv.sh"
            script.write_bytes(r.stdout)
            casi = [caso_innesto_sessione_viva]
        else:
            origine(radice)
        for caso in casi:
            lab = Lab(script, radice, caso.__name__, sorgente)
            try:
                caso(lab)
                resti = sorted(p.name for p in lab.home.glob(".claude-arturo-*"))
                assert not resti, f"cartella temporanea rimasta in HOME: {resti}"
                passati += 1
                print(f"PASS {caso.__name__}")
            except AssertionError as e:
                print(f"FAIL {caso.__name__}: {e}")
    print(f"installa.sh: {passati}/{len(casi)}" + (" (veleno)" if a.avvelena else ""))
    if a.avvelena:
        # Rosso (1) solo se il veleno con mv e ogni veleno di VELENI sono rossi col loro motivo.
        return 1 if passati == 0 and veleni_rossi else 0
    return 0 if passati == len(casi) else 1


if __name__ == "__main__":
    sys.exit(main())
