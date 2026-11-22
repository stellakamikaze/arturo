#!/usr/bin/env python3
"""Banco di sito/installa.sh, l'installatore che fa installare Arturo come plugin di Claude Code.

Dal 22/11/2026 (revisione D2) le persone nuove entrano dal plugin: lo script aggiunge il catalogo di
Arturo a Claude Code, verifica che il catalogo indichi un tag plugin-vX.Y.Z firmato con la chiave dei
rilasci, fa installare il plugin a Claude Code e controlla lo sha della copia installata. Non scrive
file di Arturo in ~/.claude, salvo l'ancora della chiave in ~/.claude/arturo. Il banco di prima (36
casi, l'innesto del clone) sta nella storia del ramo, fino a fabcc62.

Ogni caso gira in una HOME usa e getta, con un PATH di sistema senza il claude vero. Un claude finto
(CLAUDE_FINTO qui sotto) fa le parti di `claude plugin` che lo script usa e scrive i file veri di Claude
Code: plugins/known_marketplaces.json e plugins/installed_plugins.json. Un repository locale fa da
GitHub (ARTURO_REPO), una chiave di prova firma i tag (ARTURO_FIRMA_RILASCI). Nessun caso tocca la rete.

--avvelena toglie una correzione alla volta dallo script (VELENI) e vuole il caso rosso col suo motivo.
Esce 1 solo se ogni veleno è rosso col motivo atteso; un veleno verde, rosso per un altro motivo o
senza il punto da togliere fa uscire 0, e verifica-allineamento.sh lo legge come veleno verde.
"""
import argparse
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
from pathlib import Path

# Su Windows "bash" per nome è il lanciatore di WSL in System32: serve il bash del PATH (Git Bash, #4362).
BASH = shutil.which("bash") or "bash"
PATH_BASE = "/usr/bin:/bin:/usr/sbin:/sbin"
WINDOWS = os.name == "nt"


def _posix(p) -> str:
    """Su Windows un percorso C:\\… nel PATH di bash spezza la lista ai due punti: va in forma /c/… (#4362)."""
    if not WINDOWS:
        return str(p)
    return subprocess.run(["cygpath", "-u", str(p)], capture_output=True, text=True, check=True).stdout.strip()


if WINDOWS:
    # Git Bash tiene git in /mingw64/bin e python3 sta fuori dalle cartelle di sistema.
    PATH_BASE += ":/mingw64/bin:" + _posix(Path(shutil.which("python3") or sys.executable).parent)

PYTHON = _posix(sys.executable)
TAG = "plugin-v1.0.0"

# Il claude finto. Legge dall'ambiente:
#   FINTO_CATALOGO  la cartella del catalogo (con .claude-plugin/marketplace.json) che `marketplace add`
#                   e `marketplace update` copiano in plugins/marketplaces/arturo
#   FINTO_SHA       lo sha che `install` scrive, al posto di quello del catalogo
#   FINTO_FALLISCE  i comandi che escono con 1, separati da virgole (add, update, install)
#   FINTO_REGISTRO  il file dove annota una riga per chiamata
CLAUDE_FINTO = r'''
import json, os, shutil, sys
from pathlib import Path
a = sys.argv[1:]
with open(os.environ["FINTO_REGISTRO"], "a", encoding="utf-8") as f:
    f.write(" ".join(a) + "\n")
if a[:1] == ["--version"]:
    print("2.1.330 (Claude Code)")
    sys.exit(0)
if a[:1] != ["plugin"]:
    sys.exit(0)
plugins = Path(os.environ["HOME"]) / ".claude" / "plugins"
mercati, installati = plugins / "known_marketplaces.json", plugins / "installed_plugins.json"
def leggi(p):
    return json.loads(p.read_text(encoding="utf-8")) if p.is_file() else {}
def scrivi(p, d):
    if d:
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(d), encoding="utf-8")
    elif p.exists():
        p.unlink()
# Come il claude vero (sonda del 22/11/2026, 2.1.330): add scrive il catalogo in settings.json, install
# accende il plugin, uninstall e remove tolgono la voce e lasciano il dizionario vuoto.
impostazioni = Path(os.environ["HOME"]) / ".claude" / "settings.json"
def voce_settings(chiave, nome, valore=None):
    d = leggi(impostazioni)
    if valore is None:
        d.setdefault(chiave, {}).pop(nome, None)
    else:
        d.setdefault(chiave, {})[nome] = valore
    impostazioni.parent.mkdir(parents=True, exist_ok=True)
    impostazioni.write_text(json.dumps(d, indent=2), encoding="utf-8")
comando = a[1:3] if a[1:2] == ["marketplace"] else a[1:2]
nome = {"marketplace add": "add", "marketplace update": "update", "marketplace remove": "remove"}.get(" ".join(comando), comando[0])
if nome in os.environ.get("FINTO_FALLISCE", "").split(","):
    print(f"Error: {nome} finto non riuscito", file=sys.stderr)
    sys.exit(1)
dove = plugins / "marketplaces" / "arturo"
if nome in ("add", "update"):
    shutil.rmtree(dove, ignore_errors=True)
    shutil.copytree(os.environ["FINTO_CATALOGO"], dove)
    d = leggi(mercati)
    d["arturo"] = {"source": {"source": "github", "repo": "stellakamikaze/arturo", "ref": "catalogo"},
                   "installLocation": str(dove)}
    scrivi(mercati, d)
    if nome == "add":
        voce_settings("extraKnownMarketplaces", "arturo", {"source": d["arturo"]["source"]})
elif nome == "remove":
    shutil.rmtree(dove, ignore_errors=True)
    d = leggi(mercati)
    d.pop("arturo", None)
    scrivi(mercati, d)
    voce_settings("extraKnownMarketplaces", "arturo")
    for vuota in (plugins / "marketplaces", plugins):
        if vuota.is_dir() and not any(vuota.iterdir()):
            vuota.rmdir()
elif nome == "install":
    voce = next(p for p in leggi(dove / ".claude-plugin" / "marketplace.json")["plugins"] if p["name"] == "arturo")
    copia = plugins / "cache" / "arturo" / "arturo" / str(voce.get("version") or "x")
    copia.mkdir(parents=True, exist_ok=True)
    (copia / "README.md").write_text("Arturo", encoding="utf-8")
    d = leggi(installati) or {"version": 2, "plugins": {}}
    d["plugins"]["arturo@arturo"] = [{"scope": "user", "installPath": str(copia), "version": voce.get("version"),
                                      "gitCommitSha": os.environ.get("FINTO_SHA") or voce["source"]["sha"]}]
    scrivi(installati, d)
    voce_settings("enabledPlugins", "arturo@arturo", True)
elif nome == "uninstall":
    d = leggi(installati)
    d.get("plugins", {}).pop("arturo@arturo", None)
    scrivi(installati, d if d.get("plugins") else {})
    voce_settings("enabledPlugins", "arturo@arturo")
    shutil.rmtree(plugins / "cache" / "arturo", ignore_errors=True)
    for vuota in (plugins / "cache", plugins):
        if vuota.is_dir() and not any(vuota.iterdir()):
            vuota.rmdir()
'''


def sh(*args, cwd=None, env=None):
    subprocess.run(args, cwd=cwd, check=True, capture_output=True, env=env)


def git_out(*args, cwd=None) -> str:
    return subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True).stdout.strip()


# La chiave di prova che firma i rilasci dell'origine finta, e lo sha del rilascio. Li scrive origine().
CHIAVE = {"privata": "", "riga": "", "sha": ""}


def chiave_nuova(radice: Path, nome: str) -> tuple:
    """(file privato, riga di allowed_signers) di una chiave ed25519 nuova."""
    k = radice / nome
    sh("ssh-keygen", "-q", "-t", "ed25519", "-N", "", "-C", nome, "-f", str(k))
    pub = (radice / (nome + ".pub")).read_text(encoding="utf-8").split()
    return str(k), f'rilasci@arturo namespaces="git,arturo-manifest" {pub[0]} {pub[1]}'


def firma_tag(lavoro: Path, nome: str, chiave: str, ref: str = "HEAD", dentro: str = ""):
    """Un tag annotato firmato con `chiave`. Con `dentro` il nome scritto nel tag è un altro: è il tag
    firmato vecchio ripubblicato col nome nuovo (finding 109)."""
    sh("git", "-c", "gpg.format=ssh", "-c", f"user.signingkey={chiave}", "-c", "user.name=t",
       "-c", "user.email=t@t", "tag", "-s", "-m", dentro or nome, dentro or nome, ref, cwd=lavoro)
    if dentro:
        oggetto = git_out("rev-parse", dentro, cwd=lavoro)
        sh("git", "tag", "-d", dentro, cwd=lavoro)
        sh("git", "update-ref", f"refs/tags/{nome}", oggetto, cwd=lavoro)


GPG = shutil.which("gpg")


def portachiavi_pgp() -> tuple:
    """(GNUPGHOME, impronta) di un portachiavi nuovo con una chiave PGP senza parola d'ordine: è la chiave di
    un altro che sta nel portachiavi della persona. La cartella è corta: gpg-agent ci apre il suo socket, e
    oltre i 104 caratteri non si apre."""
    casa = tempfile.mkdtemp(prefix="tig", dir="/tmp" if os.path.isdir("/tmp") else None)
    os.chmod(casa, 0o700)
    env = dict(os.environ, GNUPGHOME=casa)
    subprocess.run([GPG, "--batch", "--passphrase", "", "--quick-gen-key", "altro@example.invalid", "ed25519",
                    "sign", "never"], env=env, check=True, capture_output=True, timeout=60)
    righe = subprocess.run([GPG, "--list-secret-keys", "--with-colons"], env=env, check=True, capture_output=True,
                           text=True, timeout=60).stdout.splitlines()
    return casa, [r.split(":")[9] for r in righe if r.startswith("fpr:")][0]


def chiudi_portachiavi(casa: str):
    subprocess.run(["gpgconf", "--kill", "all"], env=dict(os.environ, GNUPGHOME=casa), capture_output=True, timeout=30)
    shutil.rmtree(casa, ignore_errors=True)


def commit(lavoro: Path, file: str, testo: bytes, messaggio: str):
    (lavoro / file).write_bytes(testo)
    sh("git", "add", file, cwd=lavoro)
    sh("git", "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "-m", messaggio, cwd=lavoro)


def origine(radice: Path) -> Path:
    """Un repository al posto di GitHub: il rilascio TAG firmato con la chiave di prova, e un commit dopo,
    senza firma."""
    lavoro = radice / "lavoro"
    lavoro.mkdir()
    sh("git", "init", "-q", "-b", "main", cwd=lavoro)
    commit(lavoro, "README.md", b"Arturo\n", "x")
    CHIAVE["privata"], CHIAVE["riga"] = chiave_nuova(radice, "chiave-rilasci")
    firma_tag(lavoro, TAG, CHIAVE["privata"])
    CHIAVE["sha"] = git_out("rev-parse", "HEAD", cwd=lavoro)
    commit(lavoro, "README.md", b"Arturo dopo il rilascio\n", "dopo il rilascio")
    nudo = radice / "stellakamikaze" / "arturo.git"
    sh("git", "clone", "-q", "--bare", str(lavoro), str(nudo))
    return nudo


def catalogo(cartella: Path, ref: str = TAG, sha: str = "", versione="1.0.0", sorgente="github",
             nome="arturo") -> Path:
    """Una cartella col marketplace.json del ramo catalogo, come lo scrive bin/rilascia.py."""
    voce = {"name": nome, "version": versione,
            "source": {"source": sorgente, "repo": "stellakamikaze/arturo", "ref": ref, "sha": sha or CHIAVE["sha"]}}
    if versione is None:
        del voce["version"]
    (cartella / ".claude-plugin").mkdir(parents=True, exist_ok=True)
    (cartella / ".claude-plugin" / "marketplace.json").write_text(
        json.dumps({"name": "arturo", "plugins": [voce]}), encoding="utf-8")
    return cartella


def variante(lab, prepara) -> str:
    """Una copia dell'origine nella cartella del caso, cambiata da prepara(lavoro). Ritorna il percorso
    da dare ad ARTURO_REPO."""
    lavoro = lab.dir / "lavoro"
    sh("git", "clone", "-q", lab.repo, str(lavoro))
    sh("git", "fetch", "-q", "origin", "+refs/tags/*:refs/tags/*", cwd=lavoro)
    prepara(lavoro)
    nudo = lab.dir / "stellakamikaze" / "arturo.git"
    sh("git", "clone", "-q", "--bare", str(lavoro), str(nudo))
    return _posix(nudo)


def foto(radice: Path, salta: tuple = ()) -> dict:
    """Percorsi e contenuti di un albero: cartelle col segno "dir", file coi byte. `salta` toglie dei
    sottoalberi relativi."""
    esito = {}
    if not radice.exists():
        return esito
    for cartella, sotto, file in os.walk(radice):
        base = Path(cartella)
        for n in sotto:
            esito[(base / n).relative_to(radice).as_posix()] = "dir"
        for n in file:
            esito[(base / n).relative_to(radice).as_posix()] = (base / n).read_bytes()
    return {k: v for k, v in esito.items() if not any(k == s or k.startswith(s + "/") for s in salta)}


def della_persona(c: Path) -> dict:
    """settings.json senza le due voci che Claude Code scrive per Arturo (catalogo e plugin acceso), e senza i
    dizionari che restano vuoti quando le toglie."""
    p = c / "settings.json"
    d = json.loads(p.read_text(encoding="utf-8")) if p.is_file() else {}
    for chiave, nome in (("extraKnownMarketplaces", "arturo"), ("enabledPlugins", "arturo@arturo")):
        if isinstance(d.get(chiave), dict):
            d[chiave].pop(nome, None)
            if not d[chiave]:
                del d[chiave]
    return d


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
        self.catalogo = catalogo(self.dir / "catalogo")
        self.registro = self.dir / "claude.txt"
        (self.dir / "claude_finto.py").write_text(CLAUDE_FINTO, encoding="utf-8")
        # Nessun caso tocca il Path vero di Windows: un powershell.exe finto davanti a tutto annota
        # cosa riceve e non risponde.
        self.powershell = self.dir / "powershell.txt"
        self.finto("powershell.exe", f'cat > "{_posix(self.powershell)}"')

    def altro(self, suffisso: str) -> "Lab":
        return Lab(self.script, self.radice, self.nome + suffisso, self.sorgente)

    def _claude(self, p: Path):
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(f'#!/bin/sh\nexec "{PYTHON}" "{_posix(self.dir / "claude_finto.py")}" "$@"\n'.encode())
        p.chmod(0o755)

    def claude_nel_path(self):
        self._claude(self.bin / "claude")

    def claude_locale(self):
        """claude solo in ~/.local/bin, come lo lascia l'installatore di Claude Code: lo script lo usa da lì."""
        self._claude(self.home / ".local" / "bin" / "claude")

    def finto(self, nome: str, corpo: str):
        # Fine riga LF anche su Windows: con CRLF sh legge "$@"\r.
        p = self.bin / nome
        p.write_bytes(("#!/bin/sh\n" + corpo + "\n").encode())
        p.chmod(0o755)

    def config_vecchia(self):
        c = self.home / ".claude"
        (c / "projects").mkdir(parents=True)
        (c / ".credentials.json").write_text("{}")
        (c / "settings.json").write_text('{"model": "opus"}\n')
        (c / "CLAUDE.md").write_text("# Le mie istruzioni\n")
        (c / "mio.txt").write_text("mio")

    def lancia(self, repo=None, extra=None, script=None):
        env = {
            "HOME": _posix(self.home),
            "PATH": f"{_posix(self.bin)}:{PATH_BASE}",
            "SHELL": "/bin/zsh",
            "ARTURO_REPO": repo or _posix(self.repo),  # con le barre dritte, come lo scrive chi installa
            "ARTURO_FIRMA_RILASCI": CHIAVE["riga"],
            "FINTO_CATALOGO": str(self.catalogo),
            "FINTO_REGISTRO": str(self.registro),
            "LANG": "C.UTF-8",
        }
        env.update(extra or {})
        r = subprocess.run([BASH, script or str(self.script)], env=env, capture_output=True, text=True,
                           encoding="utf-8", stdin=subprocess.DEVNULL, timeout=120)
        return r.returncode, r.stdout + r.stderr

    def chiamate(self) -> list:
        return self.registro.read_text(encoding="utf-8").splitlines() if self.registro.is_file() else []

    def installato(self) -> dict:
        p = self.home / ".claude" / "plugins" / "installed_plugins.json"
        voci = (json.loads(p.read_text(encoding="utf-8")).get("plugins") or {}).get("arturo@arturo") if p.is_file() else []
        return (voci or [{}])[0]

    def mercato(self) -> bool:
        p = self.home / ".claude" / "plugins" / "known_marketplaces.json"
        return p.is_file() and "arturo" in json.loads(p.read_text(encoding="utf-8"))

    def ancora(self) -> Path:
        return self.home / ".claude" / "arturo" / "rilasci.allowed_signers"


# ---------- l'installazione ----------

def caso_nuova(lab):
    lab.claude_nel_path()
    lab.config_vecchia()
    c = lab.home / ".claude"
    prima, impostazioni = foto(c, salta=("settings.json",)), della_persona(c)
    rc, out = lab.lancia()
    assert rc == 0, f"rc {rc}\n{out}"
    assert lab.installato().get("gitCommitSha") == CHIAVE["sha"], f"plugin non installato: {lab.installato()}\n{out}"
    assert f"OK firma del rilascio {TAG}" in out and "Arturo installato" in out, f"firma o esito non detti\n{out}"
    dopo = foto(c, salta=("plugins", "arturo", "settings.json"))
    assert dopo == prima, f"file della persona toccati: {differenze(prima, dopo)}"
    assert della_persona(c) == impostazioni == {"model": "opus"}, f"settings.json della persona cambiato: {della_persona(c)}"
    assert json.loads((c / "settings.json").read_text())["enabledPlugins"] == {"arturo@arturo": True}, "plugin non acceso"
    assert lab.ancora().is_file() and lab.ancora().read_text(encoding="utf-8").strip() == CHIAVE["riga"], \
        "ancora non scritta con la chiave dei rilasci"
    assert not list(lab.home.glob(".claude-backup-*")), "backup creato: col plugin non serve"
    assert "chiedi a Claude" in out and "~/.claude/bin/arturo" not in out, f"telemetria col percorso del clone\n{out}"
    assert "cd ~/.claude" not in out and "tappa-5" not in out, out
    # Seconda volta: niente da rifare, nessun comando di Claude Code.
    n = len(lab.chiamate())
    rc, out = lab.lancia()
    assert rc == 0 and "già installato come plugin" in out, f"rc {rc}\n{out}"
    assert len(lab.chiamate()) == n, f"seconda volta con comandi di Claude Code: {lab.chiamate()[n:]}"


def caso_senza_cartella(lab):
    lab.claude_nel_path()
    rc, out = lab.lancia()
    assert rc == 0 and lab.installato().get("gitCommitSha") == CHIAVE["sha"], f"rc {rc}\n{out}"


def caso_catalogo_gia_presente(lab):
    # Il catalogo c'è già (un Arturo tolto prima): si aggiorna, non si aggiunge, e a un errore resta.
    lab.claude_nel_path()
    rc, out = lab.lancia(extra={"FINTO_FALLISCE": "install"})
    assert rc == 1, f"rc {rc}\n{out}"
    sh(BASH, "-c", f'"{_posix(lab.bin / "claude")}" plugin marketplace add stellakamikaze/arturo#catalogo',
       env=dict(os.environ, HOME=_posix(lab.home), FINTO_CATALOGO=str(lab.catalogo), FINTO_REGISTRO=str(lab.registro)))
    n = len(lab.chiamate())
    rc, out = lab.lancia(extra={"FINTO_FALLISCE": "install"})
    assert rc == 1 and lab.mercato(), f"catalogo di prima tolto: rc {rc}\n{out}"
    assert any("marketplace update" in r for r in lab.chiamate()[n:]), f"catalogo non aggiornato: {lab.chiamate()[n:]}"
    assert not any("marketplace add" in r for r in lab.chiamate()[n:]), "catalogo aggiunto due volte"
    rc, out = lab.lancia()
    assert rc == 0 and lab.installato().get("gitCommitSha") == CHIAVE["sha"], f"rc {rc}\n{out}"


def caso_ancora_gia_presente(lab):
    # Un'ancora scritta da un Arturo di prima resta com'è: la deriva la confronta all'avvio.
    lab.claude_nel_path()
    lab.ancora().parent.mkdir(parents=True)
    lab.ancora().write_text("una chiave di prima\n")
    rc, out = lab.lancia()
    assert rc == 0, f"rc {rc}\n{out}"
    assert lab.ancora().read_text(encoding="utf-8") == "una chiave di prima\n", "ancora di prima sovrascritta"


def caso_clone_presente(lab):
    # Arturo come clone in ~/.claude, anche come upstream di un repository della persona: niente plugin sopra.
    for nome, remoti in (("-clone", {"origin": "https://github.com/stellakamikaze/arturo.git"}),
                         ("-upstream", {"origin": "https://github.com/qualcuno/config-privata.git",
                                        "upstream": "https://github.com/stellakamikaze/arturo.git"})):
        l = lab.altro(nome)
        l.claude_nel_path()
        c = l.home / ".claude"
        sh("git", "init", "-q", str(c))
        for r, url in remoti.items():
            sh("git", "-C", str(c), "remote", "add", r, url)
        (c / "bin").mkdir()
        (c / "bin" / "arturo").write_text("x")
        (c / "settings.json").write_text("{}")
        sh("git", "-C", str(c), "add", "bin/arturo", "settings.json")
        prima = foto(c)
        rc, out = l.lancia()
        assert rc == 0 and "già installato" in out and "migrazione.md" in out, f"{nome}: clone non visto: rc {rc}\n{out}"
        assert l.chiamate() == [] and foto(c) == prima, f"{nome}: clone non visto: plugin installato sopra il clone"


def caso_repo_della_persona(lab):
    # ~/.claude è un repository della persona, senza Arturo (anche col remoto di Arturo ma senza i suoi file):
    # il plugin non lo tocca, e si installa.
    for nome, url in (("-suo", "https://github.com/qualcuno/dotfiles.git"),
                      ("-remoto", "https://github.com/stellakamikaze/arturo.git")):
        l = lab.altro(nome)
        l.claude_nel_path()
        c = l.home / ".claude"
        sh("git", "init", "-q", str(c))
        sh("git", "-C", str(c), "remote", "add", "origin", url)
        (c / "mio.txt").write_text("mio")
        rc, out = l.lancia()
        assert rc == 0 and l.installato().get("gitCommitSha") == CHIAVE["sha"], \
            f"{nome}: remoto scambiato per installazione: rc {rc}\n{out}"
        assert (c / "mio.txt").read_text() == "mio", f"{nome}: file della persona toccato"


def caso_plugin_installato(lab):
    lab.claude_nel_path()
    c = lab.home / ".claude"
    (c / "plugins").mkdir(parents=True)
    (c / "plugins" / "installed_plugins.json").write_text('{"plugins": {"arturo@arturo": []}}')
    prima = foto(c)
    rc, out = lab.lancia()
    assert rc == 0 and "come plugin" in out, f"plugin non visto: rc {rc}\n{out}"
    assert foto(c) == prima and lab.chiamate() == [], f"plugin non visto: toccata {differenze(prima, foto(c))}"


def caso_si_cancella(lab):
    # Il file scaricato da Claude Code in ~/.arturo-installa.sh resta finché serve, poi sparisce.
    lab.claude_nel_path()
    copia = lab.home / ".arturo-installa.sh"
    shutil.copyfile(lab.script, copia)
    lab.finto("python3", "exit 1")
    rc, out = lab.lancia(script=_posix(copia))
    assert rc == 1 and copia.is_file(), f"cancellato prima del tempo: rc {rc}\n{out}"
    (lab.bin / "python3").unlink()
    rc, out = lab.lancia(script=_posix(copia))
    assert rc == 0 and "Arturo installato" in out, f"rc {rc}\n{out}"
    assert not copia.exists(), "~/.arturo-installa.sh resta dopo l'installazione"


# ---------- i programmi che mancano ----------

def caso_python_vecchio(lab):
    lab.claude_nel_path()
    lab.config_vecchia()
    lab.finto("python3", "exit 1")
    prima = foto(lab.home / ".claude")
    rc, out = lab.lancia()
    assert rc == 1 and "MANCA python3" in out and "Comando:" in out, f"rc {rc}\n{out}"
    assert foto(lab.home / ".claude") == prima and lab.chiamate() == [], "ha toccato ~/.claude"


def caso_senza_claude(lab):
    lab.config_vecchia()
    rc, out = lab.lancia()
    assert rc == 1 and "MANCA claude. Comando:" in out, f"rc {rc}\n{out}"
    assert lab.installato() == {}, "plugin installato senza claude"


def caso_dentro_claude_code(lab):
    # claude sta solo in ~/.local/bin: lo script lo usa da lì, e la finestra aperta non lo trova dopo
    # /exit, serve una finestra nuova (I1). Sul Mac con bash la riga va in .bash_profile, su Windows
    # anche nel Path utente.
    lab.claude_locale()
    rc, out = lab.lancia(extra={"CLAUDECODE": "1"})
    assert rc == 0 and lab.installato().get("gitCommitSha") == CHIAVE["sha"], \
        f"claude di ~/.local/bin non usato: rc {rc}\n{out}"
    for parola in ("/exit", "claude", "/setup", "non lanciare altri comandi"):
        assert parola in out, f"manca {parola!r}\n{out}"
    assert "aprine una nuova" in out and "4. Scrivi /setup" in out, f"finestra nuova assente: claude non si trova\n{out}"
    rcfile = (lab.home / ".zshrc").read_text(encoding="utf-8")
    assert rcfile.count(".local/bin") == 1, f"PATH non aggiunto una volta:\n{rcfile}"
    m = lab.altro("-mac-bash")
    m.claude_locale()
    m.finto("uname", "echo Darwin")
    m.finto("xcode-select", "exit 0")
    rc, out = m.lancia(extra={"CLAUDECODE": "1", "SHELL": "/bin/bash"})
    profilo = m.home / ".bash_profile"
    assert rc == 0 and profilo.is_file() and ".local/bin" in profilo.read_text(encoding="utf-8"), \
        f"finestra nuova assente: PATH non in .bash_profile sul Mac\n{out}"
    assert "finestra del terminale" in out, f"finestra nuova assente: messaggio del Mac\n{out}"
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


def caso_config_dir(lab):
    lab.claude_nel_path()
    lab.config_vecchia()
    prima = foto(lab.home)
    rc, out = lab.lancia(extra={"CLAUDE_CONFIG_DIR": _posix(lab.home / "altrove")})
    assert rc == 1 and "CLAUDE_CONFIG_DIR" in out and "Non ho toccato niente" in out, \
        f"CLAUDE_CONFIG_DIR ignorata: rc {rc}\n{out}"
    assert "non è supportato" in out and "togli CLAUDE_CONFIG_DIR" in out, f"rimando sbagliato per CLAUDE_CONFIG_DIR\n{out}"
    assert foto(lab.home) == prima and lab.chiamate() == [], f"CLAUDE_CONFIG_DIR ignorata: HOME cambiata"
    # La stessa cartella, scritta con la barra in fondo, non ferma niente.
    rc, out = lab.lancia(extra={"CLAUDE_CONFIG_DIR": _posix(lab.home / ".claude") + "/"})
    assert rc == 0 and lab.installato(), f"rc {rc}\n{out}"


def caso_mac_git_rimando(lab):
    # Mac senza gli strumenti di Apple: /usr/bin/git c'è ma non funziona, xcode-select -p fallisce.
    lab.claude_nel_path()
    lab.finto("uname", "echo Darwin")
    lab.finto("xcode-select", "exit 2")
    lab.finto("git", "exit 1")
    rc, out = lab.lancia()
    assert rc == 1 and "MANCA git. Comando: xcode-select --install" in out and "until xcode-select -p" in out, \
        f"rc {rc}\n{out}"
    assert lab.chiamate() == [], "ha chiamato Claude Code"


def caso_mac_licenza(lab):
    # I7. Sul Mac con Xcode aggiornato e licenza non accettata xcode-select -p riesce, git no.
    lab.claude_nel_path()
    lab.finto("uname", "echo Darwin")
    lab.finto("xcode-select", "exit 0")
    lab.finto("git", 'echo "You have not agreed to the Xcode license agreements. Please run '
                     'sudo xcodebuild -license from within a Terminal window." >&2; exit 69')
    rc, out = lab.lancia()
    riga = next((r for r in out.splitlines() if r.startswith("MANCA git")), "")
    assert rc == 1 and "sudo xcodebuild -license accept" in riga, f"licenza di Xcode non vista: rc {rc}\n{out}"
    assert "Comando:" in riga and lab.chiamate() == [], out


def caso_python_windows(lab):
    # I2 e F2. Senza nessun Python la riga MANCA dà winget e il riavvio con una finestra nuova: il
    # PATH nuovo arriva solo ai processi nuovi. PATH senza la cartella del python vero.
    w = lab.altro("-senza")
    w.finto("uname", "echo MINGW64_NT-10.0-26100")
    w.finto("python3", "exit 49")
    w.finto("python", "exit 49")
    w.claude_nel_path()
    rc, out = w.lancia(extra={"PATH": f"{_posix(w.bin)}:/usr/bin:/bin:/usr/sbin:/sbin:/mingw64/bin"})
    riga = next((r for r in out.splitlines() if r.startswith("MANCA python3")), "")
    assert rc == 1 and "winget install -e --id Python.Python.3.12" in riga and "Comando:" in riga, f"rc {rc}\n{out}"
    assert "finestra nuova" in riga and "incolla di nuovo il link" in riga, f"manca il riavvio dopo winget: {riga!r}"
    if not WINDOWS:
        return
    # Su Windows vero: python va (un venv, che come python.org non ha python3.exe), python3 è il
    # rimando dello Store. Lo script crea python3.exe accanto a python.exe e va avanti.
    lab.claude_nel_path()
    lab.finto("python3", "exit 49")
    venv = lab.dir / "venv"
    subprocess.run([sys.executable, "-m", "venv", "--without-pip", str(venv)], check=True, capture_output=True)
    scripts = venv / "Scripts"
    for doppio in ("python3.exe", "python3"):
        (scripts / doppio).unlink(missing_ok=True)
    rc, out = lab.lancia(extra={"PATH": f"{_posix(scripts)}:{_posix(lab.bin)}:{PATH_BASE}"})
    nuovo = scripts / "python3.exe"
    assert rc == 0 and nuovo.is_file() and "OK python3 (ho creato" in out, f"python3 non creato: rc {rc}\n{out}"
    assert os.stat(nuovo).st_nlink == 2, f"python3.exe non è un hardlink di python.exe: {os.stat(nuovo).st_nlink}"


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


# ---------- la firma e il catalogo ----------

def _fermo(lab, motivo, testo, repo=None, catalogo_=None, extra=None, preparato=False):
    """Lo script si ferma: ~/.claude com'era, nessun plugin, il catalogo aggiunto tolto, l'ancora non
    scritta, il messaggio atteso."""
    if not preparato:
        lab.claude_nel_path()
        lab.config_vecchia()
    if catalogo_ is not None:
        lab.catalogo = catalogo_
    c = lab.home / ".claude"
    prima, impostazioni = foto(c, salta=("settings.json",)), della_persona(c)
    rc, out = lab.lancia(repo=repo, extra=extra)
    assert rc == 1 and testo in out, f"{motivo}: rc {rc}\n{out}"
    assert lab.installato() == {}, f"{motivo}: plugin installato {lab.installato()}"
    assert not lab.mercato(), f"{motivo}: catalogo aggiunto e rimasto"
    dopo = foto(c, salta=("settings.json",))
    assert dopo == prima, f"{motivo}: ~/.claude toccata {differenze(prima, dopo)}"
    assert della_persona(c) == impostazioni and "arturo" not in (c / "settings.json").read_text(encoding="utf-8"), \
        f"{motivo}: settings.json con Arturo"
    return out


def caso_firma_altra_chiave(lab):
    # Un rilascio firmato da un'altra chiave, indicato dal catalogo: possibile compromissione.
    def prepara(w):
        altra, _ = chiave_nuova(lab.dir, "altra")
        commit(w, "README.md", b"codice di un altro\n", "altro")
        firma_tag(w, "plugin-v1.0.1", altra)
        prepara.sha = git_out("rev-parse", "HEAD", cwd=w)
    repo = variante(lab, prepara)
    out = _fermo(lab, "installato con la firma sbagliata", "possibile compromissione", repo=repo,
                 catalogo_=catalogo(lab.dir / "c2", ref="plugin-v1.0.1", sha=prepara.sha, versione="1.0.1"))
    assert "plugin-v1.0.1" in out, out


def _fermo_pgp(lab, motivo, messaggio=""):
    # Un rilascio firmato PGP con una chiave che sta nel portachiavi della persona (revisione del
    # 20/11/2026, S1, #6258): verify-tag lo passa a gpg, che lo dà buono senza guardare le firme di Arturo.
    if not GPG:
        print(f"NOTA {motivo}: gpg assente, senza gpg l'aggiramento non c'è")
        return ""
    casa, impronta = portachiavi_pgp()
    try:
        def prepara(w):
            commit(w, "README.md", f"codice PGP: {motivo}\n".encode(), "altro")
            subprocess.run(["git", "-c", f"user.signingkey={impronta}", "-c", "user.name=t", "-c", "user.email=t@t",
                            "tag", "-s", "-m", messaggio or "plugin-v1.0.1", "plugin-v1.0.1"], cwd=w,
                           env=dict(os.environ, GNUPGHOME=casa), check=True, capture_output=True, timeout=60)
            prepara.sha = git_out("rev-parse", "HEAD", cwd=w)
        repo = variante(lab, prepara)
        lab.finto("gpg", f'exec "{_posix(Path(GPG))}" "$@"')
        out = _fermo(lab, motivo, "firma non SSH", repo=repo, extra={"GNUPGHOME": _posix(Path(casa))},
                     catalogo_=catalogo(lab.dir / "c2", ref="plugin-v1.0.1", sha=prepara.sha, versione="1.0.1"))
    finally:
        chiudi_portachiavi(casa)
    return out


def caso_firma_pgp(lab):
    _fermo_pgp(lab, "installato con una firma PGP")


def caso_firma_pgp_finta_ssh(lab):
    # La riga di una firma SSH nel messaggio non conta: git legge la firma dall'ultima riga "-----BEGIN".
    _fermo_pgp(lab, "installato con una firma PGP e una finta SSH",
               "plugin-v1.0.1\n\n-----BEGIN SSH SIGNATURE-----\nfinta\n-----END SSH SIGNATURE-----\n")


def caso_tag_senza_firma(lab):
    def prepara(w):
        sh("git", "tag", "plugin-v1.0.1", cwd=w)
    repo = variante(lab, prepara)
    _fermo(lab, "installato un tag senza firma", "tag senza firma", repo=repo,
           catalogo_=catalogo(lab.dir / "c2", ref="plugin-v1.0.1", versione="1.0.1"))


def caso_tag_rinominato(lab):
    # Il rilascio firmato plugin-v0.9.0 ripubblicato come plugin-v1.0.1: la firma è valida, il nome no.
    def prepara(w):
        commit(w, "README.md", b"vecchio\n", "vecchio")
        firma_tag(w, "plugin-v1.0.1", CHIAVE["privata"], dentro="plugin-v0.9.0")
        prepara.sha = git_out("rev-parse", "HEAD", cwd=w)
    repo = variante(lab, prepara)
    _fermo(lab, "tag rinominato accettato", "ripubblicato con un altro nome", repo=repo,
           catalogo_=catalogo(lab.dir / "c2", ref="plugin-v1.0.1", sha=prepara.sha, versione="1.0.1"))


def caso_rilascio_vecchio(lab):
    # Il catalogo riportato a un rilascio firmato più vecchio della versione minima dello script.
    def prepara(w):
        firma_tag(w, "plugin-v0.1.0", CHIAVE["privata"], ref=CHIAVE["sha"])
    repo = variante(lab, prepara)
    _fermo(lab, "rilascio vecchio accettato", "più vecchio della", repo=repo,
           catalogo_=catalogo(lab.dir / "c2", ref="plugin-v0.1.0", versione="0.1.0"))


def caso_sha_catalogo_diverso(lab):
    # Il catalogo indica il tag firmato e lo sha di un altro commit: Claude Code installerebbe quello.
    altro = git_out("rev-parse", "main", cwd=lab.repo)
    _fermo(lab, "sha del catalogo accettato", "non è il rilascio firmato",
           catalogo_=catalogo(lab.dir / "c2", sha=altro))


def caso_catalogo_senza_arturo(lab):
    _fermo(lab, "catalogo vuoto accettato", "non elenca Arturo", catalogo_=catalogo(lab.dir / "c2", nome="altro"))


def caso_catalogo_non_plugin(lab):
    # Un tag vX.Y.Z del clone, firmato, al posto di un tag del plugin.
    def prepara(w):
        firma_tag(w, "v9.0.0", CHIAVE["privata"], ref=CHIAVE["sha"])
    repo = variante(lab, prepara)
    _fermo(lab, "tag non plugin accettato", "plugin-vX.Y.Z", repo=repo,
           catalogo_=catalogo(lab.dir / "c2", ref="v9.0.0", versione="9.0.0"))


def caso_versione_diversa(lab):
    # Il campo version non è firmato: se non dice la versione del tag, avvio e barra mentono.
    _fermo(lab, "versione diversa accettata", "chiama 2.0.0", catalogo_=catalogo(lab.dir / "c2", versione="2.0.0"))


def caso_sorgente_estranea(lab):
    _fermo(lab, "sorgente non github accettata", "non so verificare", catalogo_=catalogo(lab.dir / "c2", sorgente="url"))


def caso_firma_non_verificabile(lab):
    # git o OpenSSH troppo vecchi: la verifica non parte. È una riga MANCA col comando, non una compromissione.
    lab.claude_nel_path()
    lab.config_vecchia()
    lab.finto("ssh-keygen", 'echo "ssh-keygen: illegal option -- Y" >&2; exit 1')
    out = _fermo(lab, "installato senza verifica", "MANCA la verifica della firma", preparato=True)
    assert "compromissione" not in out and "Comando:" in out, out


def caso_scaricamento_fallito(lab):
    _fermo(lab, "scaricamento fallito non detto", "Non riesco a scaricare",
           repo=_posix(lab.dir / "non-esiste" / "arturo.git"))


def caso_catalogo_non_si_aggiunge(lab):
    _fermo(lab, "errore del catalogo non detto", "Non riesco ad aggiungere il catalogo", extra={"FINTO_FALLISCE": "add"})


def caso_installazione_fallita(lab):
    out = _fermo(lab, "installazione fallita lascia resti", "non è riuscito a installare",
                 extra={"FINTO_FALLISCE": "install"})
    assert not lab.ancora().exists(), "installazione fallita lascia resti: l'ancora"
    assert "Claude Code dice:" in out, out


def caso_sha_installato_diverso(lab):
    # Fra la verifica e l'installazione il catalogo cambia: Claude Code installa un altro commit.
    out = _fermo(lab, "installata una copia diversa", "possibile compromissione",
                 extra={"FINTO_SHA": "0" * 40})
    assert any(r.startswith("plugin uninstall") for r in lab.chiamate()), "installata una copia diversa: non tolta"
    assert not lab.ancora().exists(), "installata una copia diversa: l'ancora resta"
    assert "Ho tolto la copia installata" in out, out


def caso_chiave_come_main(lab):
    # La chiave fissata in installa.sh è una riga di firme/rilasci.allowed_signers su main: se la chiave
    # cambia e lo script no, nessuna installazione nuova passa la verifica.
    for ref in ("origin/main", "main"):
        r = subprocess.run(["git", "-C", str(lab.sorgente), "show", f"{ref}:firme/rilasci.allowed_signers"],
                           capture_output=True, text=True, encoding="utf-8")
        if r.returncode == 0:
            break
    else:
        raise AssertionError("chiave non confrontata: non trovo firme/rilasci.allowed_signers su main né su origin/main")
    righe = [x.strip() for x in r.stdout.splitlines() if x.strip() and not x.startswith("#")]
    m = re.search(r"^FIRMA_RILASCI='([^']*)'$", lab.script.read_text(encoding="utf-8"), re.M)
    assert m, "chiave non confrontata: installa.sh non ha la riga FIRMA_RILASCI"
    assert m.group(1) in righe, f"chiave diversa da main: {ref} ha {righe}"


def caso_nomi_come_migra(lab):
    # Il plugin e il catalogo hanno gli stessi nomi di bin/migra.py su main: un nome diverso installa
    # un altro plugin, o non trova quello installato.
    for ref in ("origin/main", "main"):
        r = subprocess.run(["git", "-C", str(lab.sorgente), "show", f"{ref}:bin/migra.py"],
                           capture_output=True, text=True, encoding="utf-8")
        if r.returncode == 0:
            break
    else:
        raise AssertionError("nomi non confrontati: non trovo bin/migra.py su main né su origin/main")
    s = lab.script.read_text(encoding="utf-8")
    for nome in ("PLUGIN", "MERCATO"):
        a = re.search(rf'^{nome} = "([^"]+)"$', r.stdout, re.M)
        b = re.search(rf"^{nome}=(\S+)$", s, re.M)
        assert a and b and a.group(1) == b.group(1), f"nomi diversi da migra.py: {nome}"
    assert "stellakamikaze/arturo#catalogo" in s, "nomi diversi da migra.py: il catalogo"


def caso_guida(lab):
    # La guida d'installazione dice la strada del plugin, coi comandi dello script, e non più il clone.
    g = (lab.sorgente / "sito" / "installa" / "index.html").read_text(encoding="utf-8")
    s = lab.script.read_text(encoding="utf-8")
    for ancora in re.findall(r"https://arturo\.stellakamikaze\.org/installa/#([\w-]+)", s):
        assert f'id="{ancora}"' in g, f"rimando rotto: lo script porta a #{ancora}, che la guida non ha"
    for vecchio in ("git clone", 'B="$HOME/.claude-backup-', "copia di sicurezza", "~/.claude/bin/arturo",
                    "chmod +x", "git -C \"$HOME/.claude\" config"):
        assert vecchio not in g and vecchio not in (lab.sorgente / "sito" / "js" / "installa-1.js").read_text(encoding="utf-8"), \
            f"la guida ha ancora il clone: {vecchio}"
    assert "claude plugin install arturo@arturo" in g, "la guida non dà i comandi del plugin"


CASI = [caso_nuova, caso_senza_cartella, caso_catalogo_gia_presente, caso_ancora_gia_presente, caso_clone_presente,
        caso_repo_della_persona, caso_plugin_installato, caso_si_cancella, caso_python_vecchio, caso_senza_claude,
        caso_dentro_claude_code, caso_config_dir, caso_mac_git_rimando, caso_mac_licenza, caso_python_windows,
        caso_manca_formato, caso_firma_altra_chiave, caso_firma_pgp, caso_firma_pgp_finta_ssh, caso_tag_senza_firma,
        caso_tag_rinominato, caso_rilascio_vecchio, caso_sha_catalogo_diverso, caso_catalogo_senza_arturo,
        caso_catalogo_non_plugin, caso_versione_diversa, caso_sorgente_estranea, caso_firma_non_verificabile,
        caso_scaricamento_fallito, caso_catalogo_non_si_aggiunge, caso_installazione_fallita,
        caso_sha_installato_diverso, caso_chiave_come_main, caso_nomi_come_migra, caso_guida]

# (caso, testo dello script di oggi, testo che toglie la correzione, motivo atteso, solo su Windows).
# Il testo da togliere deve comparire una volta sola.
VELENI = [
    (caso_sha_installato_diverso, 'if [ "$installato" != "$sha" ]; then', "if false; then",
     "installata una copia diversa", False),
    (caso_firma_altra_chiave, 'verifica_rilascio "$tmp/t" "$tmp/firme" || esito_firma=$?',
     'verifica_rilascio "$tmp/t" "$tmp/firme" || :', "installato con la firma sbagliata", False),
    (caso_firma_pgp, "    != '-----BEGIN SSH SIGNATURE-----' ]; then", "    = 'mai' ]; then",
     "installato con una firma PGP", False),
    (caso_tag_rinominato, 'if [ "$dentro" != "$tag" ]; then', "if false; then", "tag rinominato accettato", False),
    (caso_rilascio_vecchio, 'if ! versione_almeno "${tag#plugin-}" "$VERSIONE_MINIMA"; then', "if false; then",
     "rilascio vecchio accettato", False),
    (caso_sha_catalogo_diverso, 'rev-parse "$tag^{commit}" 2>/dev/null)" != "$sha" ]; then',
     'rev-parse "$tag^{commit}" 2>/dev/null)" = mai ]; then', "sha del catalogo accettato", False),
    (caso_catalogo_non_plugin, "grep -Eq '^plugin-v[0-9]+\\.[0-9]+\\.[0-9]+$'", "grep -Eq '.'",
     "tag non plugin accettato", False),
    (caso_versione_diversa, '[ "$versione" != "${tag#plugin-v}" ]', "false", "versione diversa accettata", False),
    (caso_sorgente_estranea, '[ "$sorgente" != github ] ||', "false ||", "sorgente non github accettata", False),
    (caso_firma_non_verificabile, "    return 2\n  fi\n  dentro=", "    return 1\n  fi\n  dentro=",
     "installato senza verifica", False),
    (caso_nuova, '&& cp "$tmp/firme" "$ancora"; then', "&& true; then", "ancora non scritta", False),
    (caso_plugin_installato, "if grep -qs '\"arturo@arturo\"'", "if false", "plugin non visto", False),
    (caso_clone_presente, '&& git -C "$dest" ls-files --error-unmatch bin/arturo settings.json',
     "&& false", "clone non visto", False),
    (caso_repo_della_persona, '&& git -C "$dest" ls-files --error-unmatch bin/arturo settings.json',
     "&& true", "remoto scambiato per installazione", False),
    (caso_dentro_claude_code, '    claude_bin="$HOME/.local/bin/claude"\n', "    claude_bin=claude\n",
     "claude di ~/.local/bin non usato", False),
    (caso_dentro_claude_code, "    path_nuovo=1\n", "    path_nuovo=0\n", "finestra nuova assente", False),
    (caso_python_windows, '  local riapri="Poi la persona', '  local riapri="" vecchio="Poi la persona',
     "manca il riavvio dopo winget", False),
    (caso_python_windows, "      crea_python3\n      esito_py=$?\n", "      esito_py=1\n", "python3 non creato", True),
    (caso_mac_licenza, "if git_uscita=$(git --version 2>&1); then", "if true; then", "licenza di Xcode non vista", False),
    (caso_config_dir, '    if [ "$cfg" != "$dest" ]; then', "    if false; then", "CLAUDE_CONFIG_DIR ignorata", False),
    (caso_installazione_fallita, '    [ -n "$installato" ] && claude_plugin uninstall "$PLUGIN" >/dev/null 2>&1\n'
     '    [ "$aggiunto" = 1 ] && claude_plugin marketplace remove "$MERCATO" >/dev/null 2>&1\n'
     '    togli_ancora\n    pulisci_tmp\n    echo "Claude Code non è riuscito', '    pulisci_tmp\n    echo "Claude Code non è riuscito',
     "installazione fallita lascia resti", False),
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
    ap.add_argument("--avvelena", action="store_true", help="toglie una correzione alla volta: ogni caso deve dare rosso")
    ap.add_argument("--solo", help="lancia solo il caso con questo nome")
    a = ap.parse_args()
    sorgente = Path(a.repo)
    script = sorgente / "sito" / "installa.sh"
    if not script.is_file():
        print(f"FAIL: manca {script}")
        return 1
    with tempfile.TemporaryDirectory() as t:
        radice = Path(t)
        origine(radice)
        if a.avvelena:
            veleni_rossi = prova_veleni(script, radice, sorgente)
            print("installa.sh: veleni " + ("tutti rossi" if veleni_rossi else "NON tutti rossi"))
            return 1 if veleni_rossi else 0
        casi = [c for c in CASI if not a.solo or c.__name__ == a.solo]
        passati = 0
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
    print(f"installa.sh: {passati}/{len(casi)}")
    return 0 if passati == len(casi) else 1


if __name__ == "__main__":
    sys.exit(main())
