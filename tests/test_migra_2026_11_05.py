#!/usr/bin/env python3
"""MG01-MG07: arturo migra, dal clone in ~/.claude al plugin (strati F4, #4534, docs/strati.md).

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
MG07 un ~/.claude con Arturo come upstream (repository della persona) non si migra: rapporto FERMA,
     migrazione con uscita 1, niente cambia;
MG08 l'avviso dell'avvio: dal clone una riga che nomina `migra --prova` e `migra indietro`, una volta al giorno;
     con Arturo come upstream la riga dice "a mano"; dal codice fuori dall'Orsa (il plugin) niente.

Sulla base 53450c6 (il dev prima di F4) sono tutti rossi: arturo migra non c'è. Con --avvelena una copia
del repository rotta in un punto alla volta deve far fallire il caso che lo sorveglia.
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

CASI = ["MG01", "MG02", "MG03", "MG04", "MG05", "MG06", "MG07", "MG08"]
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


def prova(repo: Path, solo: str | None = None) -> list:
    if not CLAUDE:
        return [f"{c} manca la CLI claude: questo banco prova la CLI vera" for c in CASI]
    rossi = []
    with tempfile.TemporaryDirectory(prefix="migra.") as t:
        tmp = Path(os.path.realpath(t))
        try:
            b = Banco(repo, tmp)
            sha = b.rilascio("0.9.0")
            b.clone()
        except Exception as errore:  # noqa: BLE001
            return [f"{c} preparazione: {type(errore).__name__}: {str(errore)[:160]}" for c in CASI]
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
            return rossi + [f"{c} saltato: la migrazione di MG03 non è riuscita" for c in CASI[3:]
                            if solo in (None, c)]
        if fine("MG03"):
            return rossi

        # MG04 indietro, dalla copia di sicurezza
        p = b.arturo("migra", "indietro", codice=copia / "codice" / "bin" / "arturo")
        dopo = impronta(b.orsa)
        if p.returncode != 0 or dopo != prima or b.installato():
            rossi.append(f"MG04 indietro: rc {p.returncode}, {differenze(prima, dopo)}, plugin {bool(b.installato())}, "
                         f"{(p.stdout + p.stderr)[-200:]!r}")
            return rossi + [f"{c} saltato: indietro di MG04 non è riuscito" for c in CASI[4:] if solo in (None, c)]
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
            # Il 6/11/2026 è comparso una volta lo stato degli aggiornamenti, senza ripetersi: il contenuto dice chi l'ha scritto.
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

        # MG08 l'avviso dell'avvio
        avviso = [sys.executable, b.orsa / "bin" / "migra.py", "avviso"]
        con_upstream = esegui(avviso, env=b.env).stdout
        git(b.orsa, "remote", "remove", "upstream")
        (b.orsa / "session-env" / "migra-avviso.json").unlink()
        primo = esegui(avviso, env=b.env).stdout
        secondo = esegui(avviso, env=b.env).stdout
        (b.orsa / "session-env" / "migra-avviso.json").unlink()
        fuori = esegui([sys.executable, repo / "bin" / "migra.py", "avviso"], env=b.env).stdout
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
    ("MG03", "bin/migra.py", '    for rel in [".git", *registro["albero"]]:\n        voce = orsa / rel\n',
     '    for rel in []:\n        voce = orsa / rel\n'),
    ("MG03", "bin/migra.py", "for antenato in Path(f).parents if", "for antenato in [Path(f).parent] if"),
    ("MG04", "bin/migra.py", '        copia_voce(dentro / ".git", orsa / ".git")\n', '        pass\n'),
    ("MG05", "bin/migra.py", "    if rc != 0:\n        raise Ferma(f\"il catalogo non indica",
     "    if rc not in (0, 3):\n        raise Ferma(f\"il catalogo non indica"),
    ("MG06", "bin/migra.py", "        indietro(cartella)\n        return uscita\n", "        return uscita\n"),
    ("MG07", "bin/migra.py", '    if "upstream" in remoti:\n', '    if False:\n'),
    ("MG08", "bin/migra.py", '    if leggi_json(segno).get("giorno") == oggi:\n', '    if False:\n'),
    ("MG08", "hooks/session-start.sh", 'python3 "$ARTURO_CODICE/bin/migra.py" avviso', 'true'),
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
    print(f"migra: {verdi}/{len(CASI)} casi verdi")
    return 1 if rossi else 0


if __name__ == "__main__":
    sys.exit(main())
