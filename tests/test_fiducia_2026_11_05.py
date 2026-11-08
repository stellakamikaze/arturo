#!/usr/bin/env python3
"""FD01-FD09: la catena di fiducia del plugin di Arturo (strati F3, #4533, docs/strati.md).

Col plugin il codice sta nella cache di Claude Code, senza git. Prova del 5/11/2026 (Claude Code 2.1.318):
Claude Code installa lo sha scritto nel catalogo anche se nessun tag firmato lo indica. La fiducia la
danno quindi tre pezzi di Arturo, e questo banco li prova con una chiave di prova generata qui:

FD01 impacchetta scrive .claude-plugin/MANIFEST con le impronte di ogni file e .gitattributes "* -text"
     (gli a capo di Windows), e la verifica del pacchetto trova un file cambiato dopo; una worktree appena
     creata col ramo plugin, col solo file .git, vale come vuota e il .git resta;
FD02 hooks/fiducia.py: un MANIFEST firmato con la chiave dei rilasci torna; cambiato, firmato da un'altra
     chiave o senza firma, no;
FD03 la deriva su una copia del plugin: pulita tace e fissa l'ancora nell'Orsa; una guardia cambiata
     esce nella riga DERIVA; chiave e MANIFEST rifirmati da un'altra chiave danno "possibile
     compromissione", perché la chiave che verifica è quella dell'ancora;
FD04 la telemetria legge la versione dal plugin.json della copia, non dai tag del git dell'Orsa;
FD05 impacchetta --catalogo fissa Arturo al tag e al suo sha, e rifiuta un tag fuori forma;
FD06-FD09 `aggiornamenti.py plugin` con la CLI vera di Claude Code, in un CLAUDE_CONFIG_DIR di prova, da
     un catalogo in una cartella e da un repository locale:
FD06 un tag non firmato e un tag firmato da un'altra chiave: uscita 3, e `claude plugin update` non parte;
FD07 il catalogo indica un tag firmato ma lo sha di un commit dopo, non taggato: uscita 3, niente cambia;
FD08 il catalogo torna a un rilascio firmato più vecchio: uscita 3, niente cambia;
FD09 vX → vY: un tag firmato col suo sha si applica, la copia nuova torna col suo MANIFEST firmato, la
     deriva tace, e il giro dopo dice "GIÀ AGGIORNATO".
FD10 un indirizzo del catalogo che comincia con "-" non arriva a git come opzione (--upload-pack=<comando>):
     niente parte, e l'uscita è 3 (review del 7/11/2026);
FD11 una voce del catalogo con hooks, mcpServers o un'altra chiave che non sceglie il rilascio dà
     "possibile compromissione", anche con tag e sha giusti: Claude Code la unirebbe al plugin firmato.

Sulla base 809868a (il dev prima di F3) sono tutti rossi: fiducia.py, il MANIFEST e `plugin` non ci
sono. Con --avvelena una copia del repository rotta in un punto alla volta deve far fallire il caso
che lo sorveglia.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

CASI = ["FD01", "FD02", "FD03", "FD04", "FD05", "FD06", "FD07", "FD08", "FD09", "FD10", "FD11"]
CLI = ["FD06", "FD07", "FD08", "FD09"]  # i casi con la CLI vera di Claude Code
DISCRIMINANTI = list(CASI)
CLAUDE = shutil.which("claude")


def esegui(argv, **kw):
    kw.setdefault("capture_output", True)
    kw.setdefault("text", True)
    kw.setdefault("timeout", 300)
    kw.setdefault("stdin", subprocess.DEVNULL)
    try:
        return subprocess.run([str(a) for a in argv], **kw)
    except (OSError, subprocess.SubprocessError) as errore:
        return subprocess.CompletedProcess(argv, 99, "", str(errore))


def git(cartella: Path, *argomenti, **kw):
    return esegui(["git", "-C", cartella, "-c", "user.name=prova", "-c", "user.email=prova@arturo",
                   "-c", "commit.gpgsign=false", "-c", "tag.gpgsign=false", *argomenti], **kw)


def chiave(cartella: Path, nome: str) -> tuple:
    """(privata, allowed_signers) di una chiave di prova."""
    privata = cartella / nome
    esegui(["ssh-keygen", "-q", "-t", "ed25519", "-N", "", "-C", nome, "-f", privata])
    pubblica = (cartella / f"{nome}.pub").read_text(encoding="utf-8").split()
    firmatari = cartella / f"{nome}.allowed_signers"
    firmatari.write_text(f'rilasci@arturo namespaces="git,arturo-manifest" {pubblica[0]} {pubblica[1]}\n',
                         encoding="utf-8")
    return privata, firmatari


def modulo_fiducia(repo: Path):
    sys.path.insert(0, str(repo / "hooks"))
    try:
        import importlib
        if "fiducia" in sys.modules:
            del sys.modules["fiducia"]
        return importlib.import_module("fiducia")
    finally:
        sys.path.pop(0)


def copia_plugin(repo: Path, dest: Path, versione: str, firmatari: Path, privata: Path | None) -> Path:
    """Una copia del plugin ridotta al codice che la catena usa: bin, hooks, firme, plugin.json."""
    if dest.exists():
        for voce in dest.iterdir():
            if voce.name != ".git":
                shutil.rmtree(voce) if voce.is_dir() else voce.unlink()
    dest.mkdir(parents=True, exist_ok=True)
    for c in ("bin", "hooks"):
        shutil.copytree(repo / c, dest / c, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    (dest / "firme").mkdir()
    shutil.copy2(firmatari, dest / "firme" / "rilasci.allowed_signers")
    (dest / ".claude-plugin").mkdir()
    (dest / ".claude-plugin" / "plugin.json").write_text(json.dumps({"name": "arturo", "version": versione}),
                                                         encoding="utf-8")
    f = modulo_fiducia(repo)
    f.scrivi_manifest(dest)
    if privata:
        f.firma(dest, privata)
    return dest


def ambiente(orsa: Path) -> dict:
    return {**os.environ, "CLAUDE_CONFIG_DIR": str(orsa), "ARTURO_TELEMETRIA": "0", "GIT_TERMINAL_PROMPT": "0"}


def caso_fd01(repo: Path, tmp: Path) -> list:
    uscita = tmp / "pacchetto"
    fatto = esegui([sys.executable, repo / "bin" / "impacchetta.py", "--uscita", uscita, "--versione", "v0.3.0"])
    manifest = uscita / ".claude-plugin" / "MANIFEST"
    righe = manifest.read_text(encoding="utf-8").splitlines() if manifest.is_file() else []
    voce = next((r for r in righe if r.endswith("  hooks/block-dangerous.py")), "")
    (uscita / "hooks" / "block-dangerous.py").write_text("# cambiata\n", encoding="utf-8") \
        if (uscita / "hooks").is_dir() else None
    dopo = esegui([sys.executable, repo / "bin" / "impacchetta.py", "--verifica", uscita])
    vuota = tmp / "worktree-vuota"
    vuota.mkdir()
    (vuota / ".git").write_text("gitdir: /altrove\n", encoding="utf-8")
    in_worktree = esegui([sys.executable, repo / "bin" / "impacchetta.py", "--uscita", vuota, "--versione", "v0.3.0"])
    if in_worktree.returncode != 0 or not (vuota / ".git").is_file():
        return [f"FD01 worktree appena creata: rc {in_worktree.returncode}, {(in_worktree.stdout + in_worktree.stderr)[-160:]!r}"]
    attributi = (uscita / ".gitattributes").read_text(encoding="utf-8") if (uscita / ".gitattributes").is_file() else ""
    if fatto.returncode != 0 or not voce or "hooks.json" not in manifest.read_text(encoding="utf-8") \
            or attributi.strip() != "* -text" \
            or dopo.returncode != 1 or "cambiati hooks/block-dangerous.py" not in dopo.stdout:
        return [f"FD01 MANIFEST del pacchetto: rc {fatto.returncode}/{dopo.returncode}, {len(righe)} righe, "
                f"{(fatto.stdout + fatto.stderr + dopo.stdout)[-200:]!r}"]
    return []


def caso_fd02(repo: Path, tmp: Path, chiavi: dict) -> list:
    f = modulo_fiducia(repo)
    privata, firmatari = chiavi["rilasci"]
    altra, _ = chiavi["altra"]
    copia = copia_plugin(repo, tmp / "fd02", "0.3.0", firmatari, privata)
    esiti = [f.verifica_firma(copia, firmatari)[0]]
    manifest = copia / f.MANIFEST
    originale = manifest.read_bytes()
    manifest.write_bytes(originale + b"0" * 64 + b"  hooks/in-piu.py\n")
    esiti.append(f.verifica_firma(copia, firmatari)[0])
    manifest.write_bytes(originale)
    f.firma(copia, altra)
    esiti.append(f.verifica_firma(copia, firmatari)[0])
    (copia / f.FIRMA).unlink()
    esiti.append(f.verifica_firma(copia, firmatari)[0])
    if esiti != ["ok", "non-torna", "non-torna", "manca"]:
        return [f"FD02 firma del MANIFEST: {esiti}, attesi ok, non-torna, non-torna, manca"]
    return []


def caso_fd03(repo: Path, tmp: Path, chiavi: dict) -> list:
    privata, firmatari = chiavi["rilasci"]
    altra, firmatari_altra = chiavi["altra"]
    copia = copia_plugin(repo, tmp / "fd03" / "cache", "0.3.0", firmatari, privata)
    orsa = tmp / "fd03" / "orsa"
    orsa.mkdir()
    deriva = [sys.executable, copia / "hooks" / "deriva.py", orsa]
    pulita = esegui(deriva, env=ambiente(orsa))
    ancora = (orsa / "arturo" / "rilasci.allowed_signers").is_file()
    guardia = copia / "hooks" / "block-dangerous.py"
    guardia.write_text(guardia.read_text(encoding="utf-8") + "\n# allentata\n", encoding="utf-8")
    cambiata = esegui(deriva, env=ambiente(orsa))
    f = modulo_fiducia(repo)
    shutil.copy2(firmatari_altra, copia / "firme" / "rilasci.allowed_signers")
    f.scrivi_manifest(copia)
    f.firma(copia, altra)
    rifirmata = esegui(deriva, env=ambiente(orsa))
    cache = json.loads((orsa / "cache" / "deriva.json").read_text(encoding="utf-8")) \
        if (orsa / "cache" / "deriva.json").is_file() else {}
    if pulita.stdout.strip() or not ancora or "hooks/block-dangerous.py" not in cambiata.stdout \
            or "possibile compromissione" not in rifirmata.stdout or cache.get("firma") != "non-torna":
        return [f"FD03 deriva del plugin: pulita {pulita.stdout.strip()[:80]!r}, ancora {ancora}, cambiata "
                f"{cambiata.stdout.strip()[:100]!r}, rifirmata {rifirmata.stdout.strip()[:100]!r}, cache {cache}"]
    return []


def caso_fd04(repo: Path, tmp: Path, chiavi: dict) -> list:
    privata, firmatari = chiavi["rilasci"]
    copia = copia_plugin(repo, tmp / "fd04" / "cache", "0.3.0", firmatari, privata)
    orsa = tmp / "fd04" / "orsa"
    orsa.mkdir()
    git(orsa, "init", "-q")
    (orsa / "CLAUDE.md").write_text("mio\n", encoding="utf-8")
    git(orsa, "add", "-A")
    git(orsa, "commit", "-qm", "mio")
    git(orsa, "tag", "v9.9.9")
    codice = ("import sys; sys.path.insert(0, sys.argv[1]); import telemetria; print(telemetria.versione())")
    r = esegui([sys.executable, "-c", codice, copia / "bin"], env=ambiente(orsa))
    if r.stdout.strip() != "v0.3.0":
        return [f"FD04 versione della telemetria: {r.stdout.strip()!r} {r.stderr[-120:]!r}, attesa v0.3.0"]
    return []


def caso_fd05(repo: Path, tmp: Path) -> list:
    sha = "a" * 40
    cartella = tmp / "fd05"
    fatto = esegui([sys.executable, repo / "bin" / "impacchetta.py", "--catalogo", cartella, "--tag", "plugin-v0.3.0",
                    "--sha", sha])
    dati = {}
    try:
        dati = json.loads((cartella / ".claude-plugin" / "marketplace.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        pass
    voce = (dati.get("plugins") or [{}])[0]
    fuori = esegui([sys.executable, repo / "bin" / "impacchetta.py", "--catalogo", tmp / "fd05b", "--tag", "v0.3.0",
                    "--sha", sha])
    attesa = {"source": "github", "repo": "stellakamikaze/arturo", "ref": "plugin-v0.3.0", "sha": sha}
    if fatto.returncode != 0 or dati.get("name") != "arturo" or voce.get("source") != attesa or fuori.returncode == 0:
        return [f"FD05 catalogo: rc {fatto.returncode}/{fuori.returncode}, voce {voce}"]
    return []


CATALOGO_PROVA = r"""
import json, sys
from pathlib import Path
sys.path.insert(0, sys.argv[1])
import aggiornamenti
orsa, voce = Path(sys.argv[2]), json.loads(sys.argv[3])
catalogo = orsa / "catalogo"
(catalogo / ".claude-plugin").mkdir(parents=True, exist_ok=True)
(catalogo / ".claude-plugin" / "marketplace.json").write_text(json.dumps({"name": "arturo", "plugins": [voce]}))
(orsa / "plugins").mkdir(exist_ok=True)
(orsa / "plugins" / "known_marketplaces.json").write_text(json.dumps({"arturo": {"installLocation": str(catalogo)}}))
print("RC", aggiornamenti.verifica_catalogo(orsa)[0])
"""


def catalogo_finto(repo: Path, tmp: Path, nome: str, voce: dict):
    orsa = tmp / nome
    orsa.mkdir()
    return esegui([sys.executable, "-c", CATALOGO_PROVA, repo.resolve() / "bin", orsa, json.dumps(voce)], cwd=str(tmp),
                  env=dict(os.environ, HOME=str(orsa), CLAUDE_CONFIG_DIR=str(orsa), ARTURO_TELEMETRIA="0"))


def caso_fd10(repo: Path, tmp: Path) -> list:
    spia = tmp / "fd10-eseguito"
    voce = {"name": "arturo", "version": "9.9.9",
            "source": {"source": "url", "url": f"--upload-pack=touch {spia};:", "ref": "plugin-v9.9.9", "sha": "b" * 40}}
    p = catalogo_finto(repo, tmp, "fd10", voce)
    if spia.exists() or "RC 3" not in p.stdout:
        return [f"FD10 indirizzo come opzione di git: comando eseguito {spia.exists()}, {(p.stdout + p.stderr).strip()[-160:]!r}"]
    return []


def caso_fd11(repo: Path, tmp: Path) -> list:
    rossi = []
    for chiave_in_piu in ("hooks", "mcpServers"):
        voce = {"name": "arturo", "version": "9.9.9", chiave_in_piu: {"SessionStart": []},
                "source": {"source": "url", "url": f"file://{tmp}/manca", "ref": "plugin-v9.9.9", "sha": "c" * 40}}
        p = catalogo_finto(repo, tmp, f"fd11-{chiave_in_piu}", voce)
        if "RC 3" not in p.stdout or "POSSIBILE COMPROMISSIONE" not in p.stderr or chiave_in_piu not in p.stderr:
            rossi.append(f"FD11 voce del catalogo con {chiave_in_piu}: {(p.stdout + p.stderr).strip()[-160:]!r}")
    return rossi


class Rilasci:
    """Un repository di rilasci del plugin, un catalogo in una cartella e un'Orsa con la CLI vera."""

    def __init__(self, repo: Path, tmp: Path, chiavi: dict):
        self.repo, self.tmp, self.chiavi = repo, tmp, chiavi
        self.pub = tmp / "pub"
        self.pub.mkdir()
        git(self.pub, "init", "-q", "-b", "plugin")
        self.catalogo = tmp / "catalogo"
        (self.catalogo / ".claude-plugin").mkdir(parents=True)
        self.orsa = tmp / "orsa"
        self.orsa.mkdir()
        self.env = ambiente(self.orsa)

    def rilascio(self, versione: str, firma: str | None, tag: bool = True) -> str:
        """Un commit con la copia del plugin, e il tag plugin-v<versione> firmato da `firma` (None: non firmato)."""
        privata, firmatari = self.chiavi["rilasci"]
        copia_plugin(self.repo, self.pub, versione, firmatari, privata)
        git(self.pub, "add", "-A")
        git(self.pub, "commit", "-qm", f"plugin {versione}")
        if tag:
            nome = f"plugin-v{versione}"
            if firma:
                git(self.pub, "-c", "gpg.format=ssh", "-c", f"user.signingkey={self.chiavi[firma][0]}",
                    "tag", "-s", nome, "-m", nome)
            else:
                git(self.pub, "tag", "-a", nome, "-m", nome)
        return git(self.pub, "rev-parse", "HEAD").stdout.strip()

    def indica(self, tag: str, sha: str) -> None:
        (self.catalogo / ".claude-plugin" / "marketplace.json").write_text(json.dumps({
            "name": "arturo", "owner": {"name": "prova"},
            "plugins": [{"name": "arturo", "description": "prova",
                         "source": {"source": "url", "url": f"file://{self.pub}", "ref": tag, "sha": sha}}],
        }), encoding="utf-8")

    def claude(self, *argomenti):
        return esegui([CLAUDE, "plugin", *argomenti], env=self.env)

    def installato(self) -> dict:
        try:
            dati = json.loads((self.orsa / "plugins" / "installed_plugins.json").read_text(encoding="utf-8"))
            return dati["plugins"]["arturo@arturo"][0]
        except (OSError, ValueError, KeyError, IndexError):
            return {}

    def aggiorna(self, *extra):
        copia = Path(self.installato().get("installPath") or self.tmp / "manca")
        return esegui([sys.executable, copia / "bin" / "aggiornamenti.py", "plugin", *extra], env=self.env)


def casi_cli(repo: Path, tmp: Path, chiavi: dict, solo: str | None) -> list:
    if not CLAUDE:
        return [f"{c} manca la CLI claude: questo banco prova la CLI vera" for c in CLI]
    r = Rilasci(repo, tmp, chiavi)
    sha1 = r.rilascio("0.3.0", "rilasci")
    r.indica("plugin-v0.3.0", sha1)
    aggiunto = r.claude("marketplace", "add", r.catalogo)
    messo = r.claude("install", "arturo@arturo")
    if r.installato().get("gitCommitSha") != sha1:
        return [f"{c} installazione di partenza: {(aggiunto.stdout + aggiunto.stderr + messo.stdout + messo.stderr)[-200:]!r}"
                for c in CLI]
    rossi = []

    def fermo(caso: str, tag: str, sha: str, descrizione: str) -> None:
        r.indica(tag, sha)
        p = r.aggiorna()
        dopo = r.installato().get("gitCommitSha")
        if p.returncode != 3 or "POSSIBILE COMPROMISSIONE" not in p.stderr or dopo != sha1:
            rossi.append(f"{caso} {descrizione}: rc {p.returncode}, installato {str(dopo)[:12]}, "
                         f"{(p.stdout + p.stderr).strip()[-160:]!r}")

    if solo in (None, "FD06"):
        fermo("FD06", "plugin-v0.3.1", r.rilascio("0.3.1", None), "tag non firmato")
        fermo("FD06", "plugin-v0.3.2", r.rilascio("0.3.2", "altra"), "tag firmato da un'altra chiave")
    if solo in (None, "FD07"):
        r.rilascio("0.3.3", "rilasci")
        fermo("FD07", "plugin-v0.3.3", r.rilascio("0.3.4", None, tag=False), "sha dopo il tag firmato")
    if solo in (None, "FD08"):
        fermo("FD08", "plugin-v0.2.9", r.rilascio("0.2.9", "rilasci"), "rilascio firmato più vecchio")
    if solo in (None, "FD09"):
        sha2 = r.rilascio("0.4.0", "rilasci")
        r.indica("plugin-v0.4.0", sha2)
        vista = r.aggiorna("--verifica")
        prima = r.installato().get("gitCommitSha")
        p = r.aggiorna()
        dopo = r.installato()
        copia = Path(str(dopo.get("installPath") or tmp / "manca"))
        deriva = esegui([sys.executable, copia / "hooks" / "deriva.py", r.orsa], env=r.env)
        giro = r.aggiorna()
        if vista.stdout.strip() != "plugin-v0.4.0" or prima != sha1 or p.returncode != 0 \
                or not p.stdout.startswith("APPLICATO: plugin-v0.4.0") or dopo.get("gitCommitSha") != sha2 \
                or dopo.get("version") != "0.4.0" or deriva.stdout.strip() or not giro.stdout.startswith("GIÀ AGGIORNATO"):
            rossi.append(f"FD09 vX → vY: verifica {vista.stdout.strip()!r}, rc {p.returncode}, installato "
                         f"{dopo.get('version')} {str(dopo.get('gitCommitSha'))[:12]}, deriva {deriva.stdout.strip()[:80]!r}, "
                         f"giro {giro.stdout.strip()[:40]!r}, {(p.stdout + p.stderr).strip()[-160:]!r}")
    return rossi


def prova(repo: Path, solo: str | None = None) -> list:
    rossi = []
    with tempfile.TemporaryDirectory(prefix="fiducia.") as t:
        tmp = Path(os.path.realpath(t))
        chiavi = {n: chiave(tmp, n) for n in ("rilasci", "altra")}
        semplici = [("FD01", lambda: caso_fd01(repo, tmp)), ("FD02", lambda: caso_fd02(repo, tmp, chiavi)),
                    ("FD03", lambda: caso_fd03(repo, tmp, chiavi)), ("FD04", lambda: caso_fd04(repo, tmp, chiavi)),
                    ("FD05", lambda: caso_fd05(repo, tmp)), ("FD10", lambda: caso_fd10(repo, tmp)),
                    ("FD11", lambda: caso_fd11(repo, tmp))]
        for codice, fn in semplici:
            if solo in (None, codice):
                try:
                    rossi += fn()
                except Exception as errore:  # noqa: BLE001 - sulla base fiducia.py non c'è
                    rossi.append(f"{codice} errore: {type(errore).__name__}: {str(errore)[:160]}")
        if solo is None or solo in CLI:
            try:
                rossi += casi_cli(repo, tmp, chiavi, solo)
            except Exception as errore:  # noqa: BLE001
                rossi += [f"{c} errore: {type(errore).__name__}: {str(errore)[:160]}" for c in CLI
                          if solo in (None, c)]
    return rossi


# (caso, file, testo giusto, testo rotto): ogni veleno toglie la riga che il caso sorveglia.
VELENI = [
    ("FD01", "bin/impacchetta.py", "    fiducia.scrivi_manifest(uscita)\n", "    pass\n"),
    ("FD02", "hooks/fiducia.py", "        if r.returncode == 0:\n            return \"ok\", \"\"",
     "        if True:\n            return \"ok\", \"\""),
    ("FD03", "hooks/deriva.py", "        if fiducia.plugin(codice):", "        if False:"),
    ("FD04", "bin/telemetria.py", "    if da_plugin is not None:", "    if False:"),
    ("FD05", "bin/impacchetta.py", '"ref": tag, "sha": sha}', '"ref": tag}'),
    ("FD06", "bin/aggiornamenti.py", "        motivo, compromesso = verifica_tag(lavoro, tag, ",
     "        motivo, compromesso = \"\", False\n        _ = (lavoro, tag, "),
    ("FD07", "bin/aggiornamenti.py", '.stdout.strip() != sha:\n', '.stdout.strip() == "":\n'),
    ("FD08", "bin/aggiornamenti.py", "    if numero(tag) < numero(", "    if False and numero(tag) < numero("),
    ("FD09", "bin/aggiornamenti.py", 'aggiorna = _claude("update", NOME_PLUGIN)', 'aggiorna = _claude("list")'),
    ("FD10", "bin/aggiornamenti.py", 'URL_AMMESSO.fullmatch(str(sorgente.get("url")))', 'isinstance(sorgente.get("url"), str)'),
    ("FD11", "bin/aggiornamenti.py", "    estranea = voce_estranea(voce)\n    if estranea:", "    estranea = ''\n    if estranea:"),
]


def avvelena(repo: Path) -> int:
    esiti = []
    for caso, rel, giusto, rotto in VELENI:
        with tempfile.TemporaryDirectory() as tmp:
            copia = Path(tmp) / "repo"
            shutil.copytree(repo, copia, ignore=shutil.ignore_patterns(".git", "__pycache__", "node_modules", "tests"))
            testo = (copia / rel).read_text(encoding="utf-8")
            assert testo.count(giusto) == 1, f"veleno {caso}: il testo da rompere non c'è più in {rel}"
            (copia / rel).write_text(testo.replace(giusto, rotto), encoding="utf-8")
            rossi = prova(copia, solo=caso)
            codici = [r.split()[0] for r in rossi]
            if caso not in codici:
                print(f"VELENO {caso} NON ATTACCA: rossi {codici}")
                return 1
            print(f"VELENO {caso} ROSSO: {next(r for r in rossi if r.startswith(caso))[:120]}")
            esiti.append(caso)
    print(f"VELENI_ROSSI={','.join(esiti)} veleni={len(VELENI)}")
    return 0 if len(esiti) == len(VELENI) else 1


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument("--baseline-ref")
    parser.add_argument("--avvelena", action="store_true")
    argomenti = parser.parse_args()
    if argomenti.avvelena:
        return avvelena(Path(argomenti.repo))
    rossi = prova(Path(argomenti.repo))
    if argomenti.baseline_ref:
        codici = sorted({r.split()[0] for r in rossi})
        assert codici == DISCRIMINANTI, f"baseline non discriminante: rossi {codici}, attesi {DISCRIMINANTI}"
        print(f"BASELINE_DISCRIMINANTE={','.join(codici)}")
        return 0
    for r in rossi:
        print("ROSSO", r)
    verdi = len(CASI) - len({r.split()[0] for r in rossi})
    print(f"fiducia: {verdi}/{len(CASI)} casi verdi")
    return 1 if rossi else 0


if __name__ == "__main__":
    sys.exit(main())
