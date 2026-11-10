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
FD12-FD15 (review del 7/11/2026, finding 85 e 18) con una CLI finta di Claude Code (ARTURO_CLAUDE), che a
     `plugin update` scrive in installed_plugins.json la copia e lo sha che il caso sceglie:
FD12 Claude Code installa uno sha diverso da quello verificato: uscita 3, "non riavviare", ancora invariata;
FD13 la copia installata ha un file cambiato dopo la firma, o il MANIFEST firmato da un'altra chiave: uscita 3,
     ancora invariata;
FD14 un aggiornamento riuscito unisce a settings.json le voci nuove del frammento (una regola deny) e tiene
     quelle della persona; l'ancora prende la chiave della copia nuova;
FD15 un catalogo che non fissa Arturo a un tag plugin-vN.N.N: uscita 3.
     In FD12 e FD13, con la cartella della versione di prima ancora lì, installed_plugins.json torna a quella;
     senza, l'uscita dice "non riavviare" (finding 110).
FD16-FD18 (review del 7/11/2026) con una CLI finta che scrive una spia se `plugin update` parte:
FD16 il tag firmato di un rilascio vecchio ripubblicato sotto un nome nuovo: uscita 3 (finding 109);
FD17 un tag leggero, senza firma: "possibile compromissione", non "firma non verificabile" (finding 111);
FD18 un tag firmato su un commit col MANIFEST senza firma: uscita 3 prima di `plugin update` (finding 110).
FD19 impacchetta --firma genera il pacchetto dal tag con git archive: un file non salvato e una modifica locale
     restano fuori dal MANIFEST firmato; senza il tag si ferma; --verifica --firmato vuole MANIFEST.sig
     (finding 112 e 110).
FD20 (#5101) il plugin aggiornato fuori da /aggiorna, con un frammento che il blocco non ha: /aggiorna dice
     "GIÀ AGGIORNATO" e unisce lo stesso le voci nuove a settings.json, l'avvio fa lo stesso e al giro dopo tace;
     da una copia con una guardia cambiata dopo la firma non si unisce niente.

Sulla base 809868a (il dev prima di F3) sono tutti rossi: fiducia.py, il MANIFEST e `plugin` non ci
sono. Su a442b38 (prima del lotto L4) è rosso FD14. Su 78dc1a2 è rosso FD20. Con --avvelena una copia del repository rotta in un punto alla volta deve far fallire il caso
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
import time
from pathlib import Path

CASI = ["FD01", "FD02", "FD03", "FD04", "FD05", "FD06", "FD07", "FD08", "FD09", "FD10", "FD11", "FD12", "FD13",
        "FD14", "FD15", "FD16", "FD17", "FD18", "FD19", "FD20"]
CLI = ["FD06", "FD07", "FD08", "FD09"]  # i casi con la CLI vera di Claude Code
DISCRIMINANTI = list(CASI)
CLAUDE = shutil.which("claude")


def esegui(argv, **kw):
    kw.setdefault("capture_output", True)
    kw.setdefault("text", True)
    kw.setdefault("encoding", "utf-8")  # su Windows il default è cp1252 e l'uscita dei comandi cade (#4987)
    kw.setdefault("errors", "replace")
    kw.setdefault("timeout", 300)
    kw.setdefault("stdin", subprocess.DEVNULL)
    # I figli Python scrivono in utf-8 anche su Windows, dove una pipe prende cp1252 (#4987).
    kw["env"] = {"PYTHONIOENCODING": "utf-8", **(kw.get("env") or os.environ)}
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


def cli_finta(cartella: Path, corpo: str) -> Path:
    """Una CLI di Claude Code finta, scritta in Python. Su Windows uno script con lo shebang non parte
    (WinError 193): lo lancia un .cmd accanto (#4987)."""
    if os.name == "nt":
        (cartella / "claude-finto.py").write_text(corpo, encoding="utf-8")
        finto = cartella / "claude-finto.cmd"
        finto.write_bytes(f'@"{sys.executable}" "%~dp0claude-finto.py" %*\r\n'.encode("utf-8"))
        return finto
    finto = cartella / "claude-finto"
    finto.write_text(f"#!{sys.executable}\n" + corpo, encoding="utf-8")
    finto.chmod(0o755)
    return finto


def copia_plugin(repo: Path, dest: Path, versione: str, firmatari: Path, privata: Path | None,
                 frammento: dict | None = None) -> Path:
    """Una copia del plugin ridotta al codice che la catena usa: bin, hooks, firme, plugin.json; con `frammento`
    anche impostazioni/arturo.json."""
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
    if frammento is not None:
        (dest / "impostazioni").mkdir()
        (dest / "impostazioni" / "arturo.json").write_text(json.dumps(frammento), encoding="utf-8")
    # Come impacchetta.py: con core.autocrlf git riscrive gli a capo al checkout e il MANIFEST dà cambiati
    # tutti i file di testo (#4987).
    (dest / ".gitattributes").write_bytes(b"* -text\n")
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


CLAUDE_FINTO = r"""
import json, os, sys
from pathlib import Path
if sys.argv[1:3] == ["plugin", "update"]:
    scelta = json.loads(os.environ["FINTO_INSTALLA"])
    f = Path(os.environ["CLAUDE_CONFIG_DIR"]) / "plugins" / "installed_plugins.json"
    dati = json.loads(f.read_text())
    dati["plugins"]["arturo@arturo"] = [dict(scope="user", installPath=scelta["path"], version=scelta["version"],
                                             gitCommitSha=scelta["sha"])]
    f.write_text(json.dumps(dati))
"""

DENY_NUOVA = "Read(~/.segreti-di-prova/**)"


def casi_finti(repo: Path, tmp: Path, chiavi: dict, solo: str | None) -> list:
    """FD12-FD14: aggiornamenti.py plugin con la CLI finta, da un rilascio firmato vero."""
    privata, firmatari = chiavi["rilasci"]
    altra, firmatari_altra = chiavi["altra"]
    # Le chiavi della versione nuova: quella dei rilasci e una in più. Solo una copia verificata la porta nell'ancora.
    due = tmp / "due.allowed_signers"
    due.write_text(firmatari.read_text(encoding="utf-8") + firmatari_altra.read_text(encoding="utf-8"), encoding="utf-8")
    finto = cli_finta(tmp, CLAUDE_FINTO)
    rossi = []
    for caso, variante in (("FD12", "sha"), ("FD12", "sparita"), ("FD13", "file"), ("FD13", "firma"),
                           ("FD14", "riuscito")):
        if solo not in (None, caso):
            continue
        base = tmp / f"{caso}-{variante}"
        base.mkdir()
        r = Rilasci(repo, base, chiavi)
        sha1 = r.rilascio("0.3.0", "rilasci")
        prima = copia_plugin(repo, base / "cache" / "0.3.0", "0.3.0", firmatari, privata)
        sha2 = r.rilascio("0.4.0", "rilasci")
        r.indica("plugin-v0.4.0", sha2)
        frammento = {"permissions": {"deny": [DENY_NUOVA]}}
        nuova = copia_plugin(repo, base / "cache" / "0.4.0", "0.4.0", due, altra if variante == "firma" else privata,
                             frammento=frammento)
        if variante == "file":
            guardia = nuova / "hooks" / "block-dangerous.py"
            guardia.write_text(guardia.read_text(encoding="utf-8") + "\n# allentata\n", encoding="utf-8")
        orsa = r.orsa
        (orsa / "plugins").mkdir()
        (orsa / "plugins" / "known_marketplaces.json").write_text(json.dumps({"arturo": {"installLocation": str(r.catalogo)}}),
                                                                  encoding="utf-8")
        # "sparita": la cartella della versione di prima non c'è più, e non si può rimettere.
        percorso_prima = base / "sparita" if variante == "sparita" else prima
        (orsa / "plugins" / "installed_plugins.json").write_text(json.dumps({"plugins": {"arturo@arturo": [
            {"scope": "user", "installPath": str(percorso_prima), "version": "0.3.0", "gitCommitSha": sha1}]}}),
            encoding="utf-8")
        (orsa / "settings.json").write_text(json.dumps({"model": "mio", "permissions": {"deny": []}}), encoding="utf-8")
        (orsa / "data").mkdir()
        (orsa / "data" / "arturo-impostazioni.lock").write_text(json.dumps({"versione": "0.3.0", "frammento": {
            "permissions": {"deny": []}}}), encoding="utf-8")
        modulo_fiducia(repo).fissa_ancora(prima, orsa)
        ancora = orsa / "arturo" / "rilasci.allowed_signers"
        ancora_prima = ancora.read_bytes()
        installa = {"path": str(nuova), "version": "0.4.0", "sha": "d" * 40 if variante in ("sha", "sparita") else sha2}
        env = dict(r.env, ARTURO_CLAUDE=str(finto), FINTO_INSTALLA=json.dumps(installa))
        p = esegui([sys.executable, prima / "bin" / "aggiornamenti.py", "plugin"], env=env)
        uscita = (p.stdout + p.stderr).strip()
        settings = json.loads((orsa / "settings.json").read_text(encoding="utf-8"))
        cambiata = ancora.read_bytes() != ancora_prima
        if variante == "riuscito":
            deny = (settings.get("permissions") or {}).get("deny") or []
            if p.returncode != 0 or not p.stdout.startswith("APPLICATO") or DENY_NUOVA not in deny \
                    or settings.get("model") != "mio" or not cambiata or "NON APPLICATE" in uscita:
                rossi.append(f"{caso} impostazioni dopo l'aggiornamento: rc {p.returncode}, deny {deny}, model "
                             f"{settings.get('model')!r}, ancora cambiata {cambiata}, {uscita[-200:]!r}")
            continue
        atteso = {"sha": "non lo sha verificato", "sparita": "non lo sha verificato", "file": "come il MANIFEST",
                  "firma": "POSSIBILE COMPROMISSIONE"}[variante]
        # Con la cartella di prima ancora lì, la voce di installed_plugins.json torna a quella (finding 110).
        dopo = json.loads((orsa / "plugins" / "installed_plugins.json").read_text(encoding="utf-8"))
        dopo = dopo["plugins"]["arturo@arturo"][0].get("gitCommitSha")
        rimessa = (dopo == sha1 and "Ho rimesso la versione di prima" in uscita) if variante != "sparita" \
            else "non riavviare" in uscita
        if p.returncode != 3 or atteso not in uscita or not rimessa or cambiata \
                or DENY_NUOVA in json.dumps(settings):
            rossi.append(f"{caso} copia installata ({variante}): rc {p.returncode}, installata {str(dopo)[:12]}, "
                         f"ancora cambiata {cambiata}, {uscita[-200:]!r}")
    return rossi


def casi_fuori(repo: Path, tmp: Path, chiavi: dict) -> list:
    """FD20: il plugin aggiornato fuori da /aggiorna (claude plugin update, il pannello /plugin) porta un frammento
    nuovo che il blocco non ha ancora. /aggiorna con "GIÀ AGGIORNATO" e l'avvio lo uniscono a settings.json, solo
    da una copia che torna col suo MANIFEST firmato (#5101)."""
    privata, firmatari = chiavi["rilasci"]
    finto = cli_finta(tmp, CLAUDE_FINTO)
    rossi = []
    for variante in ("gia", "avvio", "cambiata"):
        base = tmp / f"FD20-{variante}"
        base.mkdir()
        r = Rilasci(repo, base, chiavi)
        sha = r.rilascio("0.4.0", "rilasci")
        r.indica("plugin-v0.4.0", sha)
        copia = copia_plugin(repo, base / "cache" / "0.4.0", "0.4.0", firmatari, privata,
                             frammento={"permissions": {"deny": [DENY_NUOVA]}})
        if variante == "cambiata":
            guardia = copia / "hooks" / "block-dangerous.py"
            guardia.write_text(guardia.read_text(encoding="utf-8") + "\n# allentata\n", encoding="utf-8")
        orsa = r.orsa
        (orsa / "plugins").mkdir()
        (orsa / "plugins" / "known_marketplaces.json").write_text(json.dumps({"arturo": {"installLocation": str(r.catalogo)}}),
                                                                  encoding="utf-8")
        (orsa / "plugins" / "installed_plugins.json").write_text(json.dumps({"plugins": {"arturo@arturo": [
            {"scope": "user", "installPath": str(copia), "version": "0.4.0", "gitCommitSha": sha}]}}), encoding="utf-8")
        (orsa / "settings.json").write_text(json.dumps({"model": "mio", "permissions": {"deny": []}}), encoding="utf-8")
        (orsa / "data").mkdir()
        (orsa / "data" / "arturo-impostazioni.lock").write_text(json.dumps({"versione": "0.3.0", "frammento": {
            "permissions": {"deny": []}}}), encoding="utf-8")
        (orsa / "session-env").mkdir()
        # Un controllo appena fatto: l'avvio non lancia quello staccato, che andrebbe in rete.
        (orsa / "session-env" / "aggiornamento.json").write_text(json.dumps({
            "stato": "aggiornato", "plugin": True, "controllato": time.time()}), encoding="utf-8")
        modulo_fiducia(repo).fissa_ancora(copia, orsa)
        env = dict(r.env, ARTURO_CLAUDE=str(finto))
        comando = "plugin" if variante == "gia" else "stato"
        p = esegui([sys.executable, copia / "bin" / "aggiornamenti.py", comando], env=env)
        uscita = (p.stdout + p.stderr).strip()
        settings = json.loads((orsa / "settings.json").read_text(encoding="utf-8"))
        deny = (settings.get("permissions") or {}).get("deny") or []
        if variante == "cambiata":
            if DENY_NUOVA in deny:
                rossi.append(f"FD20 copia cambiata dopo la firma: le impostazioni si sono unite lo stesso, {uscita[-160:]!r}")
            continue
        dopo = esegui([sys.executable, copia / "bin" / "aggiornamenti.py", "stato"], env=env)
        atteso = "GIÀ AGGIORNATO" if variante == "gia" else "ARTURO:"
        if p.returncode != 0 or atteso not in p.stdout or "IMPOSTAZIONI APPLICATE" not in p.stdout or DENY_NUOVA not in deny \
                or settings.get("model") != "mio" or dopo.stdout.strip():
            rossi.append(f"FD20 aggiornato fuori da /aggiorna ({variante}): rc {p.returncode}, deny {deny}, model "
                         f"{settings.get('model')!r}, avvio dopo {dopo.stdout.strip()[:80]!r}, {uscita[-200:]!r}")
    return rossi


def caso_fd15(repo: Path, tmp: Path) -> list:
    rossi = []
    for ref, sha in (("v9.9.9", "e" * 40), ("plugin-v9.9.9", "corto")):
        voce = {"name": "arturo", "version": "9.9.9",
                "source": {"source": "url", "url": f"file://{tmp}/manca", "ref": ref, "sha": sha}}
        p = catalogo_finto(repo, tmp, f"fd15-{ref}-{sha}", voce)
        if "RC 3" not in p.stdout or "non fissa Arturo" not in p.stderr:
            rossi.append(f"FD15 catalogo con ref {ref!r} e sha {sha!r}: {(p.stdout + p.stderr).strip()[-160:]!r}")
    return rossi


def caso_fd19(repo: Path, tmp: Path, chiavi: dict) -> list:
    """impacchetta --firma genera il pacchetto dal tag, non dall'albero di lavoro (finding 112); senza il tag si
    ferma; --verifica --firmato vuole la firma del MANIFEST (finding 110)."""
    privata, firmatari = chiavi["rilasci"]
    sorgente = tmp / "fd19-repo"
    shutil.copytree(repo, sorgente, ignore=shutil.ignore_patterns(".git", "__pycache__", "node_modules", "tests"))
    shutil.copy2(firmatari, sorgente / "firme" / "rilasci.allowed_signers")
    git(sorgente, "init", "-q")
    git(sorgente, "add", "-A")
    git(sorgente, "commit", "-qm", "rilascio")
    git(sorgente, "tag", "-a", "v9.0.0", "-m", "v9.0.0")
    (sorgente / "bin" / "non-committato.py").write_text("print('mai provato dal gate')\n", encoding="utf-8")
    guardia = sorgente / "hooks" / "fiducia.py"
    guardia.write_text(guardia.read_text(encoding="utf-8") + "\n# modifica locale\n", encoding="utf-8")
    generatore = [sys.executable, sorgente / "bin" / "impacchetta.py"]
    uscita = tmp / "fd19-pacchetto"
    fatto = esegui(generatore + ["--uscita", uscita, "--versione", "v9.0.0", "--firma", privata])
    manifest = (uscita / ".claude-plugin" / "MANIFEST").read_text(encoding="utf-8") \
        if (uscita / ".claude-plugin" / "MANIFEST").is_file() else ""
    locale = "modifica locale" in ((uscita / "hooks" / "fiducia.py").read_text(encoding="utf-8")
                                   if (uscita / "hooks" / "fiducia.py").is_file() else "")
    senza_tag = esegui(generatore + ["--uscita", tmp / "fd19-senza-tag", "--versione", "v9.9.9", "--firma", privata])
    non_firmato = tmp / "fd19-non-firmato"
    esegui(generatore + ["--uscita", non_firmato, "--versione", "v9.0.0"])
    verifica = esegui(generatore + ["--verifica", non_firmato, "--firmato"])
    if fatto.returncode != 0 or not manifest or "non-committato" in manifest or locale \
            or not (uscita / ".claude-plugin" / "MANIFEST.sig").is_file() or senza_tag.returncode == 0 \
            or "non c'è" not in senza_tag.stderr or verifica.returncode != 1 or "va firmato" not in verifica.stdout:
        return [f"FD19 pacchetto firmato dal tag: rc {fatto.returncode}/{senza_tag.returncode}/{verifica.returncode}, "
                f"file non salvato {'non-committato' in manifest}, modifica locale {locale}, "
                f"{(fatto.stdout + fatto.stderr + senza_tag.stderr)[-200:]!r}"]
    return []


def casi_tag(repo: Path, tmp: Path, chiavi: dict, solo: str | None) -> list:
    """FD16-FD18 (review del 7/11/2026, finding 109, 111, 110): `aggiornamenti.py plugin` con la CLI finta, che
    scrive una spia se `plugin update` parte."""
    privata, firmatari = chiavi["rilasci"]
    rossi = []
    for caso in ("FD16", "FD17", "FD18"):
        if solo not in (None, caso):
            continue
        base = tmp / f"tag-{caso}"
        base.mkdir()
        r = Rilasci(repo, base, chiavi)
        sha1 = r.rilascio("0.3.0", "rilasci")
        prima = copia_plugin(repo, base / "cache" / "0.3.0", "0.3.0", firmatari, privata)
        if caso == "FD16":
            # Il tag firmato della 0.3.0 ripubblicato sotto un nome più nuovo, con lo stesso oggetto.
            r.rilascio("0.3.5", "rilasci")
            oggetto = git(r.pub, "rev-parse", "refs/tags/plugin-v0.3.0").stdout.strip()
            git(r.pub, "update-ref", "refs/tags/plugin-v9.9.9", oggetto)
            tag, sha, atteso = "plugin-v9.9.9", sha1, "ripubblicato con un altro nome"
        elif caso == "FD17":
            sha = r.rilascio("0.4.0", None, tag=False)
            git(r.pub, "tag", "plugin-v0.4.0", sha)  # tag leggero
            tag, atteso = "plugin-v0.4.0", "tag senza firma"
        else:
            # Un tag firmato su un commit col MANIFEST senza firma: si ferma prima di claude plugin update.
            copia_plugin(repo, r.pub, "0.4.0", firmatari, None)
            git(r.pub, "add", "-A")
            git(r.pub, "commit", "-qm", "plugin 0.4.0 senza firma del MANIFEST")
            git(r.pub, "-c", "gpg.format=ssh", "-c", f"user.signingkey={privata}", "tag", "-s", "plugin-v0.4.0",
                "-m", "plugin-v0.4.0")
            sha = git(r.pub, "rev-parse", "HEAD").stdout.strip()
            tag, atteso = "plugin-v0.4.0", "MANIFEST firmato"
        r.indica(tag, sha)
        orsa = r.orsa
        (orsa / "plugins").mkdir()
        (orsa / "plugins" / "known_marketplaces.json").write_text(json.dumps({"arturo": {"installLocation": str(r.catalogo)}}),
                                                                  encoding="utf-8")
        (orsa / "plugins" / "installed_plugins.json").write_text(json.dumps({"plugins": {"arturo@arturo": [
            {"scope": "user", "installPath": str(prima), "version": "0.3.0", "gitCommitSha": "a" * 40}]}}),
            encoding="utf-8")
        modulo_fiducia(repo).fissa_ancora(prima, orsa)
        spia = base / "update-partito"
        finto = cli_finta(base, "import sys\nif sys.argv[1:3] == ['plugin', 'update']:\n"
                                f"    open({str(spia)!r}, 'w').close()\n")
        p = esegui([sys.executable, prima / "bin" / "aggiornamenti.py", "plugin"], env=dict(r.env, ARTURO_CLAUDE=str(finto)))
        uscita = (p.stdout + p.stderr).strip()
        if p.returncode != 3 or "POSSIBILE COMPROMISSIONE" not in uscita or atteso not in uscita or spia.exists():
            rossi.append(f"{caso} {tag} @ {sha[:12]}: rc {p.returncode}, update partito {spia.exists()}, {uscita[-200:]!r}")
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
                    ("FD11", lambda: caso_fd11(repo, tmp)), ("FD15", lambda: caso_fd15(repo, tmp)),
                    ("FD19", lambda: caso_fd19(repo, tmp, chiavi))]
        for codice, fn in semplici:
            if solo in (None, codice):
                try:
                    rossi += fn()
                except Exception as errore:  # noqa: BLE001 - sulla base fiducia.py non c'è
                    rossi.append(f"{codice} errore: {type(errore).__name__}: {str(errore)[:160]}")
        if solo in (None, "FD12", "FD13", "FD14"):
            try:
                rossi += casi_finti(repo, tmp, chiavi, solo)
            except Exception as errore:  # noqa: BLE001
                rossi += [f"{c} errore: {type(errore).__name__}: {str(errore)[:160]}" for c in ("FD12", "FD13", "FD14")
                          if solo in (None, c)]
        if solo in (None, "FD20"):
            try:
                rossi += casi_fuori(repo, tmp, chiavi)
            except Exception as errore:  # noqa: BLE001
                rossi.append(f"FD20 errore: {type(errore).__name__}: {str(errore)[:160]}")
        if solo in (None, "FD16", "FD17", "FD18"):
            try:
                rossi += casi_tag(repo, tmp, chiavi, solo)
            except Exception as errore:  # noqa: BLE001
                rossi += [f"{c} errore: {type(errore).__name__}: {str(errore)[:160]}" for c in ("FD16", "FD17", "FD18")
                          if solo in (None, c)]
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
    ("FD12", "bin/aggiornamenti.py", '    if dopo.get("gitCommitSha") != sha:\n', "    if False:\n"),
    ("FD13", "bin/aggiornamenti.py", '    if controllo["firma"] != "ok":\n        return _blocca(controllo["motivo"]',
     '    if False:\n        return _blocca(controllo["motivo"]'),
    ("FD13", "bin/aggiornamenti.py", "    if diversi:\n        return _blocca(", "    if False:\n        return _blocca("),
    ("FD14", "bin/aggiornamenti.py", "    impostazioni = applica_impostazioni(copia)\n", '    impostazioni = ""\n'),
    ("FD12", "bin/aggiornamenti.py", "    voci[utente] = prima\n", "    pass\n"),
    ("FD16", "bin/aggiornamenti.py", "        if not dentro or dentro.group(1) != tag:", "        if False:"),
    ("FD17", "bin/aggiornamenti.py", '    if tipo.returncode == 0 and tipo.stdout.strip() != "tag":', "    if False:"),
    ("FD18", "bin/aggiornamenti.py", "        controllo = fiducia.controlla(albero, orsa)\n        if controllo[\"firma\"] != \"ok\":",
     "        controllo = fiducia.controlla(albero, orsa)\n        if False:"),
    ("FD19", "bin/impacchetta.py", "        rc = dal_tag(argomenti)\n", "        rc = -1\n"),
    ("FD19", "bin/impacchetta.py", "    if firmato and not (cartella / fiducia.FIRMA).is_file():", "    if False:"),
    ("FD20", "bin/aggiornamenti.py", '        riga = impostazioni_indietro(Path(percorso), orsa) if percorso', '        riga = "" if percorso'),
    ("FD20", "bin/aggiornamenti.py", '    riga = "" if stato.get("compromesso") else impostazioni_indietro(', '    riga = "" if True else impostazioni_indietro('),
    ("FD20", "bin/aggiornamenti.py", '    if controllo["firma"] != "ok" or controllo["cambiati"] or controllo["mancano"]:\n        return ""',
     '    if controllo["firma"] != "ok":\n        return ""'),
    ("FD15", "bin/aggiornamenti.py", '    if not TAG_PLUGIN.fullmatch(tag) or not re.fullmatch(r"[0-9a-f]{40}", sha):\n',
     "    if False:\n"),
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
    for flusso in (sys.stdout, sys.stderr):  # su Windows l'uscita è cp1252 e un rosso con un accento cade (#4987)
        if hasattr(flusso, "reconfigure"):
            flusso.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[union-attr]
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
