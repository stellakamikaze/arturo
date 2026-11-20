#!/usr/bin/env python3
"""MG01-MG18: arturo migra, dal clone in ~/.claude al plugin (strati F4, #4534, docs/migrazione.md).

Un clone di prova con le modifiche tipiche di chi usa Arturo da settimane: una riga aggiunta a /inizio,
una guardia cambiata, un hook e un permesso suoi in settings.json, CLAUDE.md, todo e una skill sua.
Il plugin viene da un catalogo in una cartella, con un tag firmato da una chiave di prova che è anche la
chiave del clone. La CLI di Claude Code è quella vera, in un CLAUDE_CONFIG_DIR di prova.

MG01 --prova: il rapporto dice PRONTA, nomina il comando che passa in personale/ e la guardia cambiata,
     conta gli hook di Arturo che escono e quello della persona che resta, non riporta i valori della
     persona, e non cambia niente in ~/.claude salvo il rapporto in data/migra/;
MG02 con una sessione di Claude Code aperta la migrazione non parte: uscita 1, niente cambia, nessuna copia;
MG03 la migrazione: copia di sicurezza con .git e i file di Arturo; /inizio della persona in
     personale/inizio.md; plugin installato allo sha del tag firmato e verificato; settings.json senza
     hook di Arturo, con l'hook, il permesso e la scelta della persona, la barra dal puntatore e lo stile
     del plugin; `impostazioni stato` del plugin dice "già applicate"; i file di Arturo e .git fuori da
     ~/.claude, i file della persona al loro posto;
MG04 `migra indietro`, lanciato dal codice nella copia di sicurezza come dice il messaggio: ~/.claude torna identica
     a prima, file per file, .git compreso, e il plugin non c'è più;
MG05 il catalogo indica un tag non firmato: uscita 3 (possibile compromissione), il plugin non si
     installa, e ~/.claude torna identica da sola;
MG06 il plugin si installa ma settings.json ha una voce cambiata sia dalla persona sia da Arturo: uscita 1,
     e il ritorno automatico toglie anche il plugin;
MG07 un ~/.claude con Arturo come upstream (repository della persona) senza --unica-macchina non si migra: rapporto
     FERMA, migrazione con uscita 1, niente cambia;
MG18 la forma upstream con --unica-macchina (segnalazione n. 62, 9/11/2026): il repository della persona ha il suo
     origin; la prova dice PRONTA, la migrazione toglie i file di Arturo con un commit, .git e .gitignore restano,
     il plugin c'è; `migra indietro` annulla quel commit con un revert e rimette i file com'erano;
MG08 l'avviso dell'avvio: dal clone una riga che nomina `migra --prova` e `migra indietro`, una volta al giorno;
     con Arturo come upstream la riga dice "a mano"; dal codice fuori dall'Orsa (il plugin) niente; su un sistema
     dove il passaggio non è provato, oggi Windows, niente (review del 7/11/2026, finding 99).

I casi della review del 7/11/2026 (finding 14, 23, 84, 86) chiamano le funzioni di migra.py su un clone piccolo,
senza la CLI:
MG09 una copia di sicurezza che si ferma a metà (disco pieno) non resta accanto all'Orsa, e una copia a metà
     lasciata da una versione di prima non la prende `migra indietro`: .git resta quello vero (84);
MG10 una copia che non torna uguale all'originale ferma la migrazione, senza copie rimaste (86, riga di uguali);
MG11 se manca la copia di un file, togli_arturo non toglie niente, neanche .git (86);
MG12 dopo l'unione dei settings restano hook che lanciano file di Arturo: ferma, settings.json non cambia (86);
MG13 una barra in basso (statusLine) che usa un file di Arturo ferma la migrazione (86);
MG14 un file che non si toglie a metà di togli_arturo: il ritorno automatico rimette l'Orsa identica (86);
MG15 `migra indietro` mette in sostituiti-<ora>/ i file cambiati dopo la migrazione, e solo quelli, e lo dice (14);
MG16 il conto delle regole consigliate ripetute dal CLAUDE.md: 0 senza regole, 1 con una (23);
MG17 dopo `claude plugin install` uno sha diverso da quello verificato, un file diverso dal MANIFEST o una firma
     che non torna fermano con uscita 3 (4 se la firma non si può verificare), con la CLI e la fiducia finte (85, 86).

Sulla base 53450c6 (il dev prima di F4) sono tutti rossi: arturo migra non c'è. Su a442b38 (prima del lotto L4)
sono rossi MG09, MG11, MG15 e MG16. Con --avvelena una copia
del repository rotta in un punto alla volta deve far fallire il caso che lo sorveglia. Due veleni di MG03 rompono le
barre di Windows e sugli altri sistemi escono come SALTO; su Windows escono come SALTO i due di MG08 sull'avviso.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

CASI = ["MG01", "MG02", "MG03", "MG04", "MG05", "MG06", "MG07", "MG08",
        "MG09", "MG10", "MG11", "MG12", "MG13", "MG14", "MG15", "MG16", "MG17", "MG18"]
UNITA = CASI[8:17]
DISCRIMINANTI = list(CASI)
CLAUDE = shutil.which("claude")
RIGA_MIA = "Riga mia della prova: i miei progetti stanno in ~/lavoro.\n"
PERMESSO_MIO = "Bash(miocomando-segreto:*)"
HOOK_MIO = "bash ~/.claude/hooks/mio-hook.sh"


def esegui(argv, **kw):
    kw.setdefault("capture_output", True)
    kw.setdefault("text", True)
    kw.setdefault("timeout", 600)
    kw.setdefault("stdin", subprocess.DEVNULL)
    try:
        return subprocess.run([str(a) for a in argv], **kw)
    except (OSError, subprocess.SubprocessError) as errore:
        return subprocess.CompletedProcess(argv, 99, "", str(errore))


def git(cartella: Path, *argomenti, **kw):
    return esegui(["git", "-C", cartella, "-c", "user.name=prova", "-c", "user.email=prova@arturo",
                   "-c", "commit.gpgsign=false", "-c", "tag.gpgsign=false", *argomenti], **kw)


def chiave(cartella: Path, nome: str) -> tuple:
    privata = cartella / nome
    esegui(["ssh-keygen", "-q", "-t", "ed25519", "-N", "", "-C", nome, "-f", privata])
    pubblica = (cartella / f"{nome}.pub").read_text(encoding="utf-8").split()
    firmatari = cartella / f"{nome}.allowed_signers"
    firmatari.write_text(f'rilasci@arturo namespaces="git,arturo-manifest" {pubblica[0]} {pubblica[1]}\n',
                         encoding="utf-8")
    return privata, firmatari


def modulo_fiducia(repo: Path):
    import importlib.util
    spec = importlib.util.spec_from_file_location("fiducia_prova_migra", str(repo / "hooks" / "fiducia.py"))
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


def leggi(f: Path) -> dict:
    try:
        return json.loads(f.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def impronta(orsa: Path) -> dict:
    """percorso -> sha256 (o destinazione di un collegamento) di ogni file dell'Orsa. Restano fuori il
    rapporto della prova e la cache dei plugin, che Claude Code può lasciare dopo la disinstallazione."""
    voci = {}
    for cartella, dirs, files in os.walk(orsa):
        rel_c = Path(cartella).relative_to(orsa).as_posix()
        if rel_c in ("data/migra", "plugins/cache", "plugins/marketplaces", "plugins/data") or \
                rel_c.startswith(("data/migra/", "plugins/cache/", "plugins/marketplaces/", "plugins/data/")):
            dirs[:] = []
            continue
        for nome in files + [d for d in dirs if os.path.islink(os.path.join(cartella, d))]:
            p = Path(cartella) / nome
            rel = p.relative_to(orsa).as_posix()
            # Lo stato di Claude Code (.claude.json e le sue copie in backups/) lo riscrive la CLI a ogni
            # comando, e i __pycache__ li scrive Python lanciando bin/arturo: non sono della migrazione.
            if rel == ".claude.json" or rel.startswith("backups/") or "/__pycache__/" in f"/{rel}":
                continue
            # L'indice di git tiene anche le date dei file, e ogni git diff lo riscrive: conta il contenuto.
            if rel == ".git/index":
                voci[rel] = git(orsa, "ls-files", "-s").stdout
                continue
            if not os.path.islink(p) and not p.is_file():
                continue  # il socket del demone fsmonitor di git
            if rel.startswith("plugins/") and rel not in ("plugins/installed_plugins.json", "plugins/known_marketplaces.json"):
                continue
            voci[rel] = ("-> " + os.readlink(p)) if os.path.islink(p) else hashlib.sha256(p.read_bytes()).hexdigest()
    return voci


def differenze(prima: dict, dopo: dict) -> str:
    diversi = sorted(k for k in set(prima) | set(dopo) if prima.get(k) != dopo.get(k))
    return f"{len(diversi)} diversi: {diversi[:6]}"


class Banco:
    """Il repository di Arturo, i rilasci del plugin, il catalogo e il clone della persona."""

    def __init__(self, repo: Path, tmp: Path):
        self.repo, self.tmp = repo, tmp
        self.privata, self.firmatari = chiave(tmp, "rilasci")
        self.up = tmp / "up"
        shutil.copytree(repo, self.up, ignore=shutil.ignore_patterns(".git", "__pycache__", "node_modules", "tests",
                                                                     "server", ".claude"))
        shutil.copy2(self.firmatari, self.up / "firme" / "rilasci.allowed_signers")
        git(self.up, "init", "-q", "-b", "main")
        git(self.up, "add", "-A")
        git(self.up, "commit", "-qm", "Arturo di prova")
        self.pub = tmp / "pub"
        self.pub.mkdir()
        git(self.pub, "init", "-q", "-b", "plugin")
        self.catalogo = tmp / "catalogo"
        (self.catalogo / ".claude-plugin").mkdir(parents=True)
        self.casa = tmp / "casa"
        self.casa.mkdir()
        self.orsa = self.casa / ".claude"
        self.env = {**os.environ, "CLAUDE_CONFIG_DIR": str(self.orsa), "ARTURO_TELEMETRIA": "0",
                    "GIT_TERMINAL_PROMPT": "0", "ARTURO_ALTRE_SESSIONI": "0", "ARTURO_CATALOGO": str(self.catalogo)}
        for variabile in ("CLAUDE_PLUGIN_ROOT", "CLAUDE_PLUGIN_DATA", "ARTURO_CODICE", "ARTURO_RADICE"):
            self.env.pop(variabile, None)

    def rilascio(self, versione: str, firmato: bool = True, giorni: int = 90) -> str:
        """Il pacchetto del plugin generato da `up`, con cleanupPeriodDays a `giorni`, e il suo tag."""
        settings = self.up / "settings.json"
        dati = json.loads(settings.read_text(encoding="utf-8"))
        originale = settings.read_text(encoding="utf-8")
        dati["cleanupPeriodDays"] = giorni
        settings.write_text(json.dumps(dati, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        try:
            fatto = esegui([sys.executable, self.up / "bin" / "impacchetta.py", "--uscita", self.pub, "--versione",
                            f"v{versione}"])
        finally:
            settings.write_text(originale, encoding="utf-8")
        if fatto.returncode != 0:
            raise RuntimeError(f"impacchetta: {(fatto.stdout + fatto.stderr)[-200:]}")
        modulo_fiducia(self.up).firma(self.pub, self.privata)
        git(self.pub, "add", "-A")
        git(self.pub, "commit", "-qm", f"plugin {versione}")
        nome = f"plugin-v{versione}"
        if firmato:
            git(self.pub, "-c", "gpg.format=ssh", "-c", f"user.signingkey={self.privata}", "tag", "-s", nome, "-m", nome)
        else:
            git(self.pub, "tag", "-a", nome, "-m", nome)
        sha = git(self.pub, "rev-parse", "HEAD").stdout.strip()
        (self.catalogo / ".claude-plugin" / "marketplace.json").write_text(json.dumps({
            "name": "arturo", "owner": {"name": "prova"},
            "plugins": [{"name": "arturo", "description": "prova",
                         "source": {"source": "url", "url": f"file://{self.pub}", "ref": nome, "sha": sha}}],
        }), encoding="utf-8")
        return sha

    def clone(self) -> None:
        """Il clone della persona, con le sue modifiche."""
        git(self.casa, "clone", "-q", self.up, self.orsa)
        inizio = self.orsa / "commands" / "inizio.md"
        inizio.write_text(inizio.read_text(encoding="utf-8") + "\n" + RIGA_MIA, encoding="utf-8")
        guardia = self.orsa / "hooks" / "block-dangerous.py"
        guardia.write_text(guardia.read_text(encoding="utf-8") + "\n# allentata da me\n", encoding="utf-8")
        (self.orsa / "CLAUDE.md").write_text("# Le mie regole\n", encoding="utf-8")
        (self.orsa / "data" / "todo").mkdir(parents=True)
        (self.orsa / "data" / "todo" / "registro.jsonl").write_text('{"id": 1}\n', encoding="utf-8")
        (self.orsa / "skills" / "mia").mkdir(parents=True)
        (self.orsa / "skills" / "mia" / "SKILL.md").write_text("---\nname: mia\n---\nMia.\n", encoding="utf-8")
        (self.orsa / "hooks" / "mio-hook.sh").write_text("#!/bin/bash\nexit 0\n", encoding="utf-8")
        settings = self.orsa / "settings.json"
        dati = json.loads(settings.read_text(encoding="utf-8"))
        dati.setdefault("permissions", {}).setdefault("allow", []).append(PERMESSO_MIO)
        dati["hooks"].setdefault("PostToolUse", []).append({"matcher": "Mio", "hooks": [{"type": "command",
                                                                                         "command": HOOK_MIO}]})
        dati["cleanupPeriodDays"] = 60
        settings.write_text(json.dumps(dati, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    def arturo(self, *argomenti, env: dict | None = None, codice: Path | None = None):
        return esegui([sys.executable, (codice or self.orsa / "bin" / "arturo"), *argomenti], env=env or self.env)

    def copie(self) -> list:
        return sorted(p for p in self.casa.glob(".claude-arturo-clone-*") if p.is_dir())

    def installato(self) -> dict:
        return ((leggi(self.orsa / "plugins" / "installed_plugins.json").get("plugins") or {}).get("arturo@arturo")
                or [{}])[0]


def modulo_migra(repo: Path):
    import importlib.util
    # migra.py importa radici dal suo bin/: in cache resterebbe quello della copia di prima (i veleni ne usano una
    # per caso), e radice_arturo() punterebbe a una cartella già tolta.
    for nome in ("radici", "fiducia"):
        sys.modules.pop(nome, None)
    spec = importlib.util.spec_from_file_location("migra_prova", str(repo / "bin" / "migra.py"))
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


def clone_piccolo(tmp: Path) -> tuple:
    """Un clone con due file di Arturo e settings.json, in un commit: (orsa, a) come li vuole migra.py."""
    orsa = tmp / "casa" / ".claude"
    (orsa / "bin").mkdir(parents=True)
    (orsa / "hooks").mkdir()
    (orsa / "bin" / "a.py").write_text("print('a')\n", encoding="utf-8")
    (orsa / "hooks" / "b.sh").write_text("#!/bin/bash\nexit 0\n", encoding="utf-8")
    (orsa / "settings.json").write_text('{"cleanupPeriodDays": 30}\n', encoding="utf-8")
    git(orsa, "init", "-q", "-b", "main")
    git(orsa, "add", "-A")
    git(orsa, "commit", "-qm", "clone")
    return orsa, {"orsa": orsa, "albero": {"bin/a.py", "hooks/b.sh"}, "separa": [], "base": "HEAD"}


def copie_di(orsa: Path) -> list:
    return sorted(orsa.parent.glob(".claude-arturo-clone-*"))


def prova_unita(repo: Path, solo: str | None = None) -> list:
    """MG09-MG16: le funzioni di migra.py su un clone piccolo, senza la CLI di Claude Code."""
    import contextlib
    import io
    rossi = []
    casi = [c for c in UNITA if solo in (None, c)]
    for caso in casi:
        with tempfile.TemporaryDirectory(prefix="migra-unita.") as t:
            tmp = Path(os.path.realpath(t))
            env_prima = dict(os.environ)
            try:
                orsa, a = clone_piccolo(tmp)
                os.environ.update({"CLAUDE_CONFIG_DIR": str(orsa), "ARTURO_ALTRE_SESSIONI": "0", "ARTURO_TELEMETRIA": "0"})
                m = modulo_migra(repo)
                prima = impronta(orsa)
                testa = git(orsa, "rev-parse", "HEAD").stdout.strip()
                uscita = io.StringIO()
                errore = ""
                if caso == "MG09":
                    vera, conta = m.copia_voce, [0]

                    def piena(sorgente, dest):
                        conta[0] += 1
                        if conta[0] == 2:
                            raise OSError(28, "No space left on device")
                        vera(sorgente, dest)
                    m.copia_voce = piena
                    try:
                        m.fai_copia(a)
                        errore = "fai_copia non si è fermata"
                    except OSError:
                        pass
                    m.copia_voce = vera
                    rimaste = copie_di(orsa)
                    # Una copia a metà lasciata da una versione di prima: passi vuoti e un .git parziale.
                    vecchia = orsa.parent / ".claude-arturo-clone-20261107-120000"
                    (vecchia / "copia" / ".git").mkdir(parents=True)
                    (vecchia / "copia" / ".git" / "HEAD").write_text("ref: refs/heads/main\n", encoding="utf-8")
                    (vecchia / "migra.json").write_text(json.dumps({"versione": 1, "orsa": str(orsa), "passi": [],
                                                                    "albero": sorted(a["albero"]), "toccati": {}}),
                                                        encoding="utf-8")
                    with contextlib.redirect_stdout(uscita), contextlib.redirect_stderr(uscita):
                        rc = m.main(["indietro"])
                    dopo = git(orsa, "rev-parse", "HEAD").stdout.strip()
                    if errore or rimaste or rc != 1 or dopo != testa or "Nessuna copia" not in uscita.getvalue():
                        rossi.append(f"MG09 copia a metà: {errore}, copie rimaste {len(rimaste)}, indietro rc {rc}, "
                                     f"HEAD {dopo[:8]!r} invece di {testa[:8]}, {uscita.getvalue()[-160:]!r}")
                elif caso == "MG10":
                    m.uguali = lambda x, y: False
                    try:
                        m.fai_copia(a)
                        errore = "nessuna Ferma"
                    except m.Ferma as e:
                        errore = "" if "non torna" in str(e) else f"Ferma diversa: {e}"
                    except OSError as e:
                        errore = f"OSError {e}"
                    if errore or copie_di(orsa) or impronta(orsa) != prima:
                        rossi.append(f"MG10 copia diversa: {errore}, copie {len(copie_di(orsa))}, "
                                     f"{differenze(prima, impronta(orsa))}")
                elif caso == "MG11":
                    cartella = m.fai_copia(a)
                    (cartella / "copia" / "hooks" / "b.sh").unlink()
                    try:
                        m.togli_arturo(a, cartella)
                        errore = "nessuna Ferma"
                    except m.Ferma as e:
                        errore = "" if "manca la copia di hooks/b.sh" in str(e) else f"Ferma diversa: {e}"
                    if errore or impronta(orsa) != prima:
                        rossi.append(f"MG11 copia mancante: {errore}, {differenze(prima, impronta(orsa))}")
                elif caso == "MG12":
                    plugin = tmp / "plugin"
                    (plugin / "impostazioni").mkdir(parents=True)
                    (plugin / "impostazioni" / "arturo.json").write_text('{"cleanupPeriodDays": 90}', encoding="utf-8")
                    for parte in ("bin", "hooks"):
                        try:
                            os.symlink(repo / parte, plugin / parte)
                        except OSError:  # Windows senza il permesso dei link (WinError 1314): una copia vale uguale
                            shutil.copytree(repo / parte, plugin / parte,
                                            ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
                    unito = {"hooks": {"Stop": [{"hooks": [{"type": "command", "command": "bash ~/.claude/hooks/b.sh"}]}]}}
                    m.settings_nuovi = lambda *x: ({}, unito, [])
                    try:
                        m.scrivi_settings(a, plugin)
                        errore = "nessuna Ferma"
                    except m.Ferma as e:
                        errore = "" if "dopo l'unione restano" in str(e) else f"Ferma diversa: {e}"
                    if errore or impronta(orsa) != prima:
                        rossi.append(f"MG12 hook di Arturo dopo l'unione: {errore}, {differenze(prima, impronta(orsa))}")
                elif caso == "MG13":
                    (orsa / "settings.json").write_text(json.dumps({"cleanupPeriodDays": 30, "statusLine": {
                        "type": "command", "command": "bash ~/.claude/hooks/b.sh"}}), encoding="utf-8")
                    try:
                        m.settings_nuovi(orsa, "HEAD", a["albero"], {"cleanupPeriodDays": 30})
                        errore = "nessuna Ferma"
                    except m.Ferma as e:
                        errore = "" if "barra in basso" in str(e) else f"Ferma diversa: {e}"
                    if errore:
                        rossi.append(f"MG13 barra con un file di Arturo: {errore}")
                elif caso == "MG14":
                    cartella = m.fai_copia(a)
                    vera, conta = m.togli, [0]

                    def ostinato(voce):
                        conta[0] += 1
                        if conta[0] == 3:  # .git e bin/a.py sono già fuori, hooks/b.sh non si toglie
                            raise PermissionError(13, "Permission denied", str(voce))
                        vera(voce)
                    m.togli = ostinato
                    try:
                        m.togli_arturo(a, cartella)
                        errore = "togli_arturo non si è fermato"
                    except OSError:
                        pass
                    m.togli = vera
                    with contextlib.redirect_stdout(uscita), contextlib.redirect_stderr(uscita):
                        m.indietro(cartella, conserva=False)
                    if errore or impronta(orsa) != prima:
                        rossi.append(f"MG14 ritorno dopo togli_arturo a metà: {errore}, {differenze(prima, impronta(orsa))}")
                elif caso == "MG15":
                    a["separa"] = ["commands/inizio.md"]
                    cartella = m.fai_copia(a)
                    # La migrazione: settings nuovi, il blocco delle impostazioni, personale/inizio.md.
                    (orsa / "settings.json").write_text('{"cleanupPeriodDays": 90}\n', encoding="utf-8")
                    (orsa / "data").mkdir()
                    (orsa / "data" / "arturo-impostazioni.lock").write_text("{}", encoding="utf-8")
                    (orsa / "personale").mkdir()
                    (orsa / "personale" / "inizio.md").write_text("riga spostata\n", encoding="utf-8")
                    m.passo(cartella, "fuori")
                    m.registra_dopo(cartella, orsa)
                    # Due settimane dopo: la persona aggiunge una riga e cambia un'impostazione.
                    (orsa / "personale" / "inizio.md").write_text("riga spostata\nriga mia di dopo\n", encoding="utf-8")
                    (orsa / "settings.json").write_text('{"cleanupPeriodDays": 90, "model": "mio"}\n', encoding="utf-8")
                    with contextlib.redirect_stdout(uscita), contextlib.redirect_stderr(uscita):
                        m.indietro(cartella)
                    parte = sorted(cartella.glob("sostituiti-*"))
                    messi = sorted(p.relative_to(parte[0]).as_posix() for p in parte[0].rglob("*") if p.is_file()) if parte else []
                    mio = (parte[0] / "personale" / "inizio.md").read_text(encoding="utf-8") if parte and \
                        (parte[0] / "personale" / "inizio.md").is_file() else ""
                    if messi != ["personale/inizio.md", "settings.json"] or "riga mia di dopo" not in mio \
                            or "sostituiti-" not in uscita.getvalue() or impronta(orsa) != prima:
                        rossi.append(f"MG15 indietro conserva: messi {messi}, {differenze(prima, impronta(orsa))}, "
                                     f"{uscita.getvalue()[-200:]!r}")
                elif caso == "MG16":
                    personale = m._modulo("personale_prova", repo / "bin" / "personale.py")
                    regola = personale.regole_consigliate(repo)[0]
                    zero = m.regole_doppie(personale, "# Il mio CLAUDE.md\nniente regole qui\n")
                    una = m.regole_doppie(personale, f"# Il mio CLAUDE.md\n- {regola}\n")
                    if (zero, una) != (0, 1):
                        rossi.append(f"MG16 regole doppie: {zero} senza regole e {una} con una, attesi 0 e 1")
                elif caso == "MG17":
                    import types
                    cartella = tmp / "copia-di-prova"
                    cartella.mkdir()
                    (cartella / "migra.json").write_text('{"passi": ["copia"]}', encoding="utf-8")
                    (orsa / "plugins").mkdir()
                    (orsa / "plugins" / "known_marketplaces.json").write_text('{"arturo": {}}', encoding="utf-8")
                    m._claude = lambda *x, **k: subprocess.CompletedProcess(x, 0, "", "")
                    vero_modulo = m._modulo
                    esiti = []
                    for installato, controllo, attesa in (
                            ("d" * 40, {"firma": "ok", "motivo": "", "cambiati": [], "mancano": []}, 3),
                            ("a" * 40, {"firma": "ok", "motivo": "", "cambiati": ["hooks/x.py"], "mancano": []}, 3),
                            ("a" * 40, {"firma": "non-torna", "motivo": "firma", "cambiati": [], "mancano": []}, 3),
                            ("a" * 40, {"firma": "non-verificabile", "motivo": "ssh", "cambiati": [], "mancano": []}, 4)):
                        finti = {
                            "aggiornamenti_migra": types.SimpleNamespace(
                                verifica_catalogo=lambda o: (0, "plugin-v9.9.9", "a" * 40),
                                installato=lambda o, s=installato: {"installPath": str(tmp), "gitCommitSha": s}),
                            "fiducia_migra": types.SimpleNamespace(fissa_ancora=lambda *x: None,
                                                                   controlla=lambda *x, c=controllo: c)}
                        m._modulo = lambda nome, file: finti.get(nome) or vero_modulo(nome, file)
                        try:
                            m.installa_plugin(orsa, cartella)
                            esiti.append("passa")
                        except m.Ferma as e:
                            esiti.append(e.uscita)
                    if esiti != [3, 3, 3, 4]:
                        rossi.append(f"MG17 controlli dopo l'installazione: uscite {esiti}, attese [3, 3, 3, 4]")
            except Exception as e:  # noqa: BLE001
                rossi.append(f"{caso} eccezione: {type(e).__name__}: {str(e)[:200]}")
            finally:
                os.environ.clear()
                os.environ.update(env_prima)
    return rossi


def prova(repo: Path, solo: str | None = None) -> list:
    rossi = prova_unita(repo, solo)
    if solo in UNITA:
        return rossi
    if not CLAUDE:
        return rossi + [f"{c} manca la CLI claude: questo banco prova la CLI vera" for c in CASI if c not in UNITA]
    with tempfile.TemporaryDirectory(prefix="migra.") as t:
        tmp = Path(os.path.realpath(t))
        try:
            b = Banco(repo, tmp)
            sha = b.rilascio("0.9.0")
            b.clone()
        except Exception as errore:  # noqa: BLE001
            return rossi + [f"{c} preparazione: {type(errore).__name__}: {str(errore)[:160]}" for c in CASI
                            if c not in UNITA]
        prima = impronta(b.orsa)

        def fine(caso: str) -> bool:
            return solo == caso

        # MG01 --prova
        p = b.arturo("migra", "--prova")
        dopo = impronta(b.orsa)
        rapporti = sorted((b.orsa / "data" / "migra").glob("rapporto-*.txt")) if (b.orsa / "data" / "migra").is_dir() else []
        attesi = ["ESITO: PRONTA", "commands/inizio.md -> personale/inizio.md", "hooks/block-dangerous.py",
                  "restano 1 hook tuoi"]
        mancano = [x for x in attesi if x not in p.stdout]
        if p.returncode != 0 or mancano or "escono 0 hook" in p.stdout or PERMESSO_MIO in p.stdout \
                or "~/lavoro" in p.stdout or dopo != prima or not rapporti:
            rossi.append(f"MG01 rapporto: rc {p.returncode}, mancano {mancano}, invariata {dopo == prima} "
                         f"({differenze(prima, dopo)}), rapporti {len(rapporti)}, {(p.stdout + p.stderr)[-240:]!r}")
        if fine("MG01"):
            return rossi

        # MG02 sessione aperta
        p = b.arturo("migra", env={**b.env, "ARTURO_ALTRE_SESSIONI": "1"})
        dopo = impronta(b.orsa)
        if p.returncode != 1 or "sessioni di Claude Code aperte" not in p.stderr or dopo != prima or b.copie():
            rossi.append(f"MG02 sessione aperta: rc {p.returncode}, invariata {dopo == prima}, copie {len(b.copie())}, "
                         f"{(p.stdout + p.stderr)[-200:]!r}")
        if fine("MG02"):
            return rossi

        # MG03 migrazione. Lo stato del clone è una cache: col plugin direbbe cose false, e non torna con indietro.
        (b.orsa / "session-env").mkdir(exist_ok=True)
        stato_clone = b.orsa / "session-env" / "aggiornamento.json"
        stato_clone.write_text('{"stato": "pronto", "versione": "v0.2.5"}', encoding="utf-8")
        p = b.arturo("migra")
        copia = b.copie()[-1] if b.copie() else tmp / "manca"
        voce = b.installato()
        settings = leggi(b.orsa / "settings.json")
        comandi = [h.get("command", "") for gs in (settings.get("hooks") or {}).values() for g in gs
                   for h in g.get("hooks", [])]
        di_arturo = [c for c in comandi if "/.claude/hooks/" in c or "/.claude/bin/" in c]
        cartella_plugin = Path(str(voce.get("installPath") or tmp / "manca"))
        stato = esegui([sys.executable, cartella_plugin / "bin" / "impostazioni.py", "stato"], env=b.env)
        personale = (b.orsa / "personale" / "inizio.md")
        controlli = {
            "uscita 0": p.returncode == 0,
            "stato del clone via": not stato_clone.exists(),
            "copia con .git e bin/arturo": (copia / "copia" / ".git").is_dir() and (copia / "copia" / "bin" / "arturo").is_file()
            and (copia / "codice" / "bin" / "migra.py").is_file() and "codice/bin/arturo migra indietro" in p.stdout,
            "personale/inizio.md": personale.is_file() and RIGA_MIA.strip() in personale.read_text(encoding="utf-8"),
            "plugin allo sha": voce.get("gitCommitSha") == sha,
            "hook di Arturo tolti": di_arturo == [HOOK_MIO],
            "hook mio": HOOK_MIO in comandi,
            "permesso mio": PERMESSO_MIO in (settings.get("permissions") or {}).get("allow", []),
            "scelta mia": settings.get("cleanupPeriodDays") == 60,
            "barra dal puntatore": "arturo/radice" in str((settings.get("statusLine") or {}).get("command")),
            "stile del plugin": str(settings.get("outputStyle", "")).startswith("arturo:"),
            "plugin acceso": (settings.get("enabledPlugins") or {}).get("arturo@arturo") is True,
            "impostazioni applicate": "già applicate" in stato.stdout,
            "ancora": (b.orsa / "arturo" / "rilasci.allowed_signers").is_file(),
            "file di Arturo fuori": not (b.orsa / ".git").exists() and not (b.orsa / "bin").exists()
            and not (b.orsa / "commands").exists() and not (b.orsa / "hooks" / "block-dangerous.py").exists(),
            "nessuna cartella di Arturo vuota": not (b.orsa / "skills" / "arturo").exists() and not (b.orsa / "tools").exists(),
            "file miei al posto": all((b.orsa / f).is_file() for f in ("CLAUDE.md", "data/todo/registro.jsonl",
                                                                       "skills/mia/SKILL.md", "hooks/mio-hook.sh")),
        }
        falliti = [k for k, v in controlli.items() if not v]
        if falliti:
            rossi.append(f"MG03 migrazione: {falliti}, {(p.stdout + p.stderr)[-300:]!r} {stato.stdout[-120:]!r}")
            return rossi + [f"{c} saltato: la migrazione di MG03 non è riuscita" for c in CASI[3:8] + ["MG18"]
                            if solo in (None, c)]
        if fine("MG03"):
            return rossi

        # MG04 indietro, dalla copia di sicurezza
        p = b.arturo("migra", "indietro", codice=copia / "codice" / "bin" / "arturo")
        dopo = impronta(b.orsa)
        if p.returncode != 0 or dopo != prima or b.installato():
            rossi.append(f"MG04 indietro: rc {p.returncode}, {differenze(prima, dopo)}, plugin {bool(b.installato())}, "
                         f"{(p.stdout + p.stderr)[-200:]!r}")
            return rossi + [f"{c} saltato: indietro di MG04 non è riuscito" for c in CASI[4:8] + ["MG18"] if solo in (None, c)]
        if fine("MG04"):
            return rossi

        # MG05 tag non firmato
        b.rilascio("0.9.1", firmato=False)
        p = b.arturo("migra")
        dopo = impronta(b.orsa)
        if p.returncode != 3 or "POSSIBILE COMPROMISSIONE" not in p.stderr or dopo != prima or b.installato():
            rossi.append(f"MG05 tag non firmato: rc {p.returncode}, {differenze(prima, dopo)}, plugin "
                         f"{bool(b.installato())}, {(p.stdout + p.stderr)[-240:]!r}")
        if fine("MG05"):
            return rossi

        # MG06 conflitto in settings.json dopo l'installazione
        b.rilascio("0.9.2", giorni=120)
        p = b.arturo("migra")
        dopo = impronta(b.orsa)
        if p.returncode != 1 or "cleanupPeriodDays" not in p.stderr or "PLUGIN:" not in p.stdout \
                or dopo != prima or b.installato():
            # Se compare lo stato degli aggiornamenti, l'ha scritto l'aggiornamento automatico partito da session-end.sh.
            stato_file = b.orsa / "session-env" / "aggiornamento.json"
            scritto = stato_file.read_text(encoding="utf-8")[:200] if stato_file.exists() else ""
            rossi.append(f"MG06 conflitto: rc {p.returncode}, {differenze(prima, dopo)}, plugin {bool(b.installato())}, "
                         f"stato {scritto!r}, {(p.stdout + p.stderr)[-240:]!r}")
        if fine("MG06"):
            return rossi

        # MG07 Arturo come upstream
        git(b.orsa, "remote", "add", "upstream", b.up)
        git(b.orsa, "fetch", "-q", "upstream")
        prima7 = impronta(b.orsa)
        r = b.arturo("migra", "--prova")
        m = b.arturo("migra")
        dopo = impronta(b.orsa)
        if r.returncode != 1 or "ESITO: FERMA" not in r.stdout or "upstream" not in r.stdout or m.returncode != 1 \
                or dopo != prima7 or b.installato():
            rossi.append(f"MG07 upstream: rc {r.returncode}/{m.returncode}, {differenze(prima7, dopo)}, "
                         f"{(r.stdout + m.stderr)[-240:]!r}")
        if fine("MG07"):
            return rossi

        # MG18 la forma upstream con un computer solo: il repository della persona ha il suo origin. Un rilascio
        # nuovo senza il conflitto di MG06.
        b.rilascio("0.9.3")
        persona = tmp / "persona.git"
        git(tmp, "init", "-q", "--bare", persona)
        git(b.orsa, "remote", "set-url", "origin", str(persona))
        git(b.orsa, "push", "-q", "origin", "HEAD:main")
        prima18 = impronta(b.orsa)
        indice18 = git(b.orsa, "ls-files", "-s").stdout
        r = b.arturo("migra", "--prova", "--unica-macchina")
        m = b.arturo("migra", "--unica-macchina")
        tracciati = git(b.orsa, "ls-files").stdout.split()
        sporchi = git(b.orsa, "status", "--porcelain", "--untracked-files=no").stdout.strip()
        ultimo = git(b.orsa, "log", "-1", "--format=%s").stdout
        controlli = {
            "prova PRONTA": r.returncode == 0 and "ESITO: PRONTA" in r.stdout and "--unica-macchina" in r.stdout,
            "migrato": m.returncode == 0 and "MIGRATO" in m.stdout,
            ".git resta": (b.orsa / ".git").is_dir() and (b.orsa / ".gitignore").is_file(),
            "file di Arturo fuori": not (b.orsa / "bin").exists() and not any(f.startswith("bin/") for f in tracciati),
            "commit nel repository": "plugin" in ultimo and not sporchi,
            "plugin installato": bool(b.installato()),
            "file miei": (b.orsa / "CLAUDE.md").is_file(),
        }
        falliti = [k for k, v in controlli.items() if not v]
        if falliti:
            rossi.append(f"MG18 forma upstream: {falliti}, sporchi {sporchi[:80]!r}, {(r.stdout + m.stdout + m.stderr)[-240:]!r}")
        else:
            copia = b.copie()[-1]
            i = b.arturo("migra", "indietro", codice=copia / "codice" / "bin" / "arturo")
            dopo = {k: v for k, v in impronta(b.orsa).items() if not k.startswith(".git/")}
            prima_senza_git = {k: v for k, v in prima18.items() if not k.startswith(".git/")}
            ultimo = git(b.orsa, "log", "-1", "--format=%s").stdout
            if i.returncode != 0 or dopo != prima_senza_git or git(b.orsa, "ls-files", "-s").stdout != indice18 \
                    or not ultimo.startswith("Revert") or b.installato():
                rossi.append(f"MG18 indietro della forma upstream: rc {i.returncode}, {differenze(prima_senza_git, dopo)}, "
                             f"ultimo commit {ultimo.strip()[:60]!r}, plugin {bool(b.installato())}, "
                             f"{(i.stdout + i.stderr)[-200:]!r}")
        if fine("MG18"):
            return rossi

        # MG08 l'avviso dell'avvio
        avviso = [sys.executable, b.orsa / "bin" / "migra.py", "avviso"]
        con_upstream = esegui(avviso, env=b.env).stdout
        git(b.orsa, "remote", "remove", "upstream")
        # missing_ok: dove il passaggio non è provato l'avviso non parte e il segno del giorno non nasce.
        (b.orsa / "session-env" / "migra-avviso.json").unlink(missing_ok=True)
        primo = esegui(avviso, env=b.env).stdout
        secondo = esegui(avviso, env=b.env).stdout
        (b.orsa / "session-env" / "migra-avviso.json").unlink(missing_ok=True)
        fuori = esegui([sys.executable, repo / "bin" / "migra.py", "avviso"], env=b.env).stdout
        (b.orsa / "session-env" / "migra-avviso.json").unlink(missing_ok=True)
        # Su un sistema dove il passaggio non è provato (Windows, finding 99) niente avviso.
        non_provato = esegui([sys.executable, "-c", "import sys; sys.path.insert(0, sys.argv[1]); import migra; "
                              "migra.SISTEMI_PROVATI = (); print(migra.avviso())", b.orsa / "bin"], env=b.env).stdout
        if non_provato.strip():
            rossi.append(f"MG08 avviso su un sistema non provato: {non_provato[:80]!r}")
        if os.name == "nt":  # qui l'avviso non parte: il resto di MG08 vale solo dove il passaggio è provato
            return rossi
        avvio = (repo / "hooks" / "session-start.sh").read_text(encoding="utf-8")
        if 'python3 "$ARTURO_CODICE/bin/migra.py" avviso' not in avvio:
            rossi.append("MG08 avviso: hooks/session-start.sh non lancia migra.py avviso")
        if "ARTURO PLUGIN" not in primo or "migra --prova" not in primo or "migra indietro" not in primo \
                or secondo.strip() or "a mano" not in con_upstream or fuori.strip():
            rossi.append(f"MG08 avviso: primo {primo[:80]!r}, secondo {secondo[:60]!r}, upstream {con_upstream[-80:]!r}, "
                         f"fuori {fuori[:60]!r}")
    return rossi


# (caso, file, testo giusto, testo rotto): ogni veleno toglie la riga che il caso sorveglia.
VELENI = [
    ("MG01", "bin/migra.py", '    a["separa"] = personale.modificati(orsa, a["base"])\n', '    a["separa"] = []\n'),
    ("MG03", "bin/migra.py", '            (a["orsa"] / "session-env" / "aggiornamento.json").unlink()\n', '            pass\n'),
    ("MG02", "bin/migra.py", '    if a["sessioni"]:\n', '    if False:\n'),
    ("MG03", "bin/migra.py", '    for rel in voci:\n        togli(orsa / rel)\n', '    for rel in []:\n        togli(orsa / rel)\n'),
    ("MG03", "bin/migra.py", "for antenato in Path(f).parents if", "for antenato in [Path(f).parent] if"),
    ("MG03", "bin/migra.py", '{antenato.as_posix() for f in registro["albero"]', '{str(antenato) for f in registro["albero"]'),
    ("MG03", "bin/migra.py", 'testo[len(casa):].replace(os.sep, "/") if testo == casa', 'testo[len(casa):] if testo == casa'),
    ("MG04", "bin/migra.py", '        copia_voce(dentro / ".git", orsa / ".git")\n', '        pass\n'),
    ("MG05", "bin/migra.py", "    if rc != 0:\n        raise Ferma(f\"il catalogo non indica",
     "    if rc not in (0, 3):\n        raise Ferma(f\"il catalogo non indica"),
    ("MG06", "bin/migra.py", "        indietro(cartella, conserva=False)\n        return uscita\n", "        return uscita\n"),
    ("MG07", "bin/migra.py", '    if "upstream" in remoti:\n', '    if False:\n'),
    ("MG08", "bin/migra.py", '    if leggi_json(segno).get("giorno") == oggi:\n', '    if False:\n'),
    ("MG18", "bin/migra.py", '    voci = [f for f in registro["albero"] if f != ".gitignore"] if upstream else [".git", *registro["albero"]]\n',
     '    voci = [".git", *registro["albero"]]\n'),
    ("MG18", "bin/migra.py", '        problemi += ritorno_upstream(orsa, registro.get("commit") or "", list(registro.get("toccati") or {}))\n',
     '        pass\n'),
    ("MG08", "bin/migra.py", "    if os.name not in SISTEMI_PROVATI:\n        return \"\"\n", ""),
    ("MG08", "hooks/session-start.sh", 'python3 "$ARTURO_CODICE/bin/migra.py" avviso', 'true'),
    ("MG09", "bin/migra.py", "        togli(cartella)\n        raise\n", "        raise\n"),
    ("MG09", "bin/migra.py", 'if "copia" in (leggi_json(p / "migra.json").get("passi") or [])',
     'if (p / "migra.json").is_file()'),
    ("MG10", "bin/migra.py", "        if not uguali(orsa / rel, dentro / rel):\n", "        if False:\n"),
    ("MG11", "bin/migra.py", "    if manca:\n", "    if False:\n"),
    ("MG12", "bin/migra.py", '    if impostazioni.doppi(unito) or hook_di_arturo(unito, a["albero"], orsa):\n', "    if False:\n"),
    ("MG13", "bin/migra.py", '    if hook_di_arturo({"hooks": {"barra"', '    if False and hook_di_arturo({"hooks": {"barra"'),
    ("MG14", "bin/migra.py", "        if not esiste(voce):\n            copia_voce(dentro / rel, voce)\n",
     "        if False:\n            copia_voce(dentro / rel, voce)\n"),
    ("MG15", "bin/migra.py", "        copia_voce(voce, da_parte / rel)\n", "        pass\n"),
    ("MG17", "bin/migra.py", '    if voce.get("gitCommitSha") != sha:\n', "    if False:\n"),
    ("MG17", "bin/migra.py", '    if controllo["firma"] != "ok" or controllo["cambiati"] or controllo["mancano"]:\n',
     '    if controllo["firma"] != "ok":\n'),
    ("MG16", "bin/migra.py", "personale.regole_consigliate(radice_arturo()))[0])", "personale.regole_consigliate(radice_arturo())))"),
]


# Veleni che rompono la gestione delle barre rovesciate (#4873): su macOS e Linux str() e as_posix() danno lo stesso
# testo e os.sep è già "/", quindi il codice rotto fa la stessa cosa del giusto e il veleno non ha cosa rompere (#5092).
SOLO_WINDOWS = {
    '{antenato.as_posix() for f in registro["albero"]',
    'testo[len(casa):].replace(os.sep, "/") if testo == casa',
}


def avvelena(repo: Path) -> int:
    esiti = []
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from salti_windows import dichiara  # noqa: PLC0415
    for caso, rel, giusto, rotto in VELENI:
        if os.name == "nt" and caso == "MG08" and "SISTEMI_PROVATI" not in giusto:
            # Su Windows l'avviso non parte e MG08 si ferma al controllo del sistema non provato: questi due
            # veleni rompono la parte che lì non gira.
            dichiara(f"veleno MG08 ({rel})", "l'avviso dell'avvio su Windows è spento, il veleno non ha cosa rompere")
            esiti.append(caso)
            continue
        if os.name != "nt" and giusto in SOLO_WINDOWS:
            dichiara(f"veleno {caso} ({giusto[:40]})", "le barre rovesciate ci sono solo su Windows, il veleno non ha cosa rompere")
            esiti.append(caso)
            continue
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
    print(f"migra: {verdi}/{len(CASI)} casi verdi")
    return 1 if rossi else 0


if __name__ == "__main__":
    sys.exit(main())
