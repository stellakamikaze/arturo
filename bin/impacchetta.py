#!/usr/bin/env python3
"""Genera il plugin di Arturo dal repository, senza toccare il repository (strati F2, docs/strati.md).

Il repository resta installabile come clone in ~/.claude (Gigi e Filippo fino a F4). Questo script
ne ricava una cartella pronta per Claude Code come plugin:

  .claude-plugin/plugin.json      nome, versione (dal tag), descrizione
  .claude-plugin/marketplace.json il marketplace: Arturo (sorgente "./"), che porta anche il suo mod
  hooks/hooks.json                gli hook di settings.json, coi percorsi in ${CLAUDE_PLUGIN_ROOT}, e il modulo
                                  del mod (skills/arturo/hooks/register.tsx) sotto "modules"
  impostazioni/arturo.json        il resto di settings.json: lo applica /setup col file di blocco
  skills/<comando>/SKILL.md       ogni commands/<comando>.md, con name: (il nome resta senza prefisso)
  .gitattributes                  "* -text": il ramo plugin si scarica senza riscrivere gli a capo
  .claude-plugin/MANIFEST         sha256 e percorso di ogni file (strati F3, hooks/fiducia.py); con --firma
                                  anche MANIFEST.sig, firmato con la chiave dei rilasci

Nei testi un percorso al codice (~/.claude/bin, hooks, shared...) diventa ${CLAUDE_PLUGIN_ROOT}/...
dove Claude Code lo sostituisce (skill), $ARTURO_CODICE/... altrove: l'avvio lo esporta nel Bash.
I percorsi ai dati della persona (~/.claude/data, personale, CLAUDE.md, session-env) restano: sono l'Orsa.

  python3 bin/impacchetta.py --uscita DIR [--versione v0.2.0] [--firma CHIAVE]
  python3 bin/impacchetta.py --verifica DIR     il pacchetto rispetta il contratto (rc 1 se no)
  python3 bin/impacchetta.py --catalogo DIR --tag plugin-v0.3.0 --sha SHA [--repo stellakamikaze/arturo]
                                                il catalogo pubblicato (ramo catalogo): Arturo fissato allo
                                                sha del tag firmato (strati F3)
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

RADICE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RADICE / "hooks"))
import fiducia  # noqa: E402
NOME = "arturo"
# Cosa entra nel plugin. Restano fuori: tests (si girano sul repository), server (il Worker della
# telemetria, si pubblica a parte), settings.json (diventa hooks.json più impostazioni/arturo.json).
CARTELLE = ["agents", "bin", "docs", "firme", "hooks", "output-styles", "scripts", "shared", "skills", "tools"]
FILE = ["LICENSE", "NOVITA.md", "PRODUCT.md", "README.md", "ROADMAP.md", "SECURITY.md", "package.json"]
IGNORA = shutil.ignore_patterns("__pycache__", "*.pyc", ".DS_Store", "node_modules")
# Cartelle e file di ~/.claude che nel clone sono codice di Arturo e nel plugin stanno nella sua cartella.
CODICE = ("bin", "hooks", "shared", "tools", "scripts", "docs", "firme", "agents", "output-styles",
          "commands", "tests", "NOVITA.md", "README.md")
METODO = 'bash "${CLAUDE_PLUGIN_ROOT}/hooks/metodo.sh"'
TAG_PLUGIN = re.compile(r"plugin-v\d{1,4}\.\d{1,4}\.\d{1,6}")
VARIANTI_HOME = (r"~/\.claude", r"\$HOME/\.claude", r"\$\{HOME\}/\.claude", r"\$\{ARTURO_CODICE:-\$HOME/\.claude\}")


def versione_da_git() -> str:
    try:
        # Solo i rilasci numerati (dal 3/11/2026): "v0.2.0", o "v0.2.0-8-gabc1234" su una copia di sviluppo.
        return subprocess.run(["git", "-C", str(RADICE), "describe", "--tags", "--always", "--match", "v[0-9]*.[0-9]*.[0-9]*"],
                              capture_output=True, text=True, check=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return "0.0.0-sviluppo"


def skill_di_arturo() -> set[str]:
    nomi = {p.name for p in (RADICE / "skills").iterdir() if p.is_dir()}
    return nomi | {p.stem for p in (RADICE / "commands").glob("*.md")}


def riscrivi(testo: str, radice_codice: str, skill: set[str]) -> str:
    """I percorsi al codice di Arturo puntano a `radice_codice`; quelli ai dati della persona restano."""
    for home in VARIANTI_HOME:
        voci = "|".join(re.escape(c) for c in CODICE)
        testo = re.sub(rf"{home}/(?=(?:{voci})(?:/|\b))", radice_codice + "/", testo)
        nomi = "|".join(re.escape(s) for s in sorted(skill, key=len, reverse=True))
        testo = re.sub(rf"{home}/skills/(?=(?:{nomi})(?:/|\b))", radice_codice + "/skills/", testo)
        # commands/<comando>.md del clone è skills/<comando>/SKILL.md nel plugin.
        testo = re.sub(rf"{re.escape(radice_codice)}/commands/([a-z0-9-]+)\.md",
                       lambda m: f"{radice_codice}/skills/{m.group(1)}/SKILL.md", testo)
    return testo


def hooks_json(settings: dict) -> dict:
    """Gli hook di settings.json con ${CLAUDE_PLUGIN_ROOT} al posto di ~/.claude per il codice."""
    hooks = json.loads(json.dumps(settings.get("hooks", {})))
    for gruppi in hooks.values():
        for gruppo in gruppi:
            for hook in gruppo.get("hooks", []):
                if isinstance(hook.get("command"), str):
                    # Tra virgolette: su Windows la cartella dell'utente può avere spazi.
                    hook["command"] = re.sub(r"~/\.claude/((?:hooks|bin)/[^\s\"']+)",
                                             r'"${CLAUDE_PLUGIN_ROOT}/\1"', hook["command"])
    # Il metodo (shared/metodo.md) col plugin arriva da un hook di avvio suo: un plugin non porta un
    # CLAUDE.md. Col clone non c'è, perché le regole stanno nel CLAUDE.md scritto da /setup.
    hooks.setdefault("SessionStart", []).append(
        {"hooks": [{"type": "command", "command": METODO, "timeout": 10}]})
    return {"description": "Guardie, avvio e telemetria di Arturo", "hooks": hooks}


def impostazioni(settings: dict) -> dict:
    """Le voci che un plugin non può portare: le scrive /setup nei settings della persona."""
    resto = {k: v for k, v in settings.items() if k not in ("hooks", "$schema")}
    linea = resto.get("statusLine")
    if isinstance(linea, dict) and isinstance(linea.get("command"), str):
        # La cartella del plugin cambia a ogni versione: la barra la legge dal puntatore che
        # l'avvio riscrive (~/.claude/arturo/radice).
        linea = dict(linea, command=linea["command"].replace(
            "~/.claude/hooks/statusline.js", '"$(cat ~/.claude/arturo/radice)/hooks/statusline.js"'))
        resto["statusLine"] = linea
    # Uno stile portato da un plugin si chiama col prefisso: "Conciso" diventa "arturo:Conciso"
    # (prova del 3/11/2026: col nome nudo Claude Code non lo applica).
    stile = resto.get("outputStyle")
    if isinstance(stile, str) and ":" not in stile and stile_di_arturo(stile):
        resto["outputStyle"] = f"{NOME}:{stile}"
    return resto


def stile_di_arturo(nome: str) -> bool:
    for md in (RADICE / "output-styles").glob("*.md"):
        testa = md.read_text(encoding="utf-8").split("\n---", 1)[0]
        if re.search(rf"^name:\s*[\"']?{re.escape(nome)}[\"']?\s*$", testa, re.M) or md.stem.lower() == nome.lower():
            return True
    return False


def comando_in_skill(sorgente: Path, dest: Path) -> None:
    testo = sorgente.read_text(encoding="utf-8")
    nome = sorgente.stem
    if testo.startswith("---\n"):
        fine = testo.index("\n---", 4)
        testa, corpo = testo[4:fine], testo[fine + 4:]
        if not re.search(r"^name:", testa, re.M):
            testa = f"name: {nome}\n" + testa
        # Un comando lo lancia la persona: nel plugin resta così, il modello non lo chiama da solo.
        if not re.search(r"^disable-model-invocation:", testa, re.M):
            testa += "\ndisable-model-invocation: true"
        testo = f"---\n{testa.rstrip()}\n---{corpo}"
    else:
        testo = f"---\nname: {nome}\ndisable-model-invocation: true\n---\n\n{testo}"
    dest.mkdir(parents=True, exist_ok=True)
    (dest / "SKILL.md").write_text(testo, encoding="utf-8")


def impacchetta(uscita: Path, versione: str) -> None:
    if uscita.exists():
        if not (uscita / ".claude-plugin" / "plugin.json").exists() and any(uscita.iterdir()):
            raise SystemExit(f"{uscita} non è vuota e non è un pacchetto di Arturo: non la cancello")
        # Il pacchetto si rigenera da zero, tranne .git (il ramo plugin in una worktree).
        for voce in uscita.iterdir():
            if voce.name == ".git":
                continue
            shutil.rmtree(voce) if voce.is_dir() and not voce.is_symlink() else voce.unlink()
    uscita.mkdir(parents=True, exist_ok=True)
    for c in CARTELLE:
        if (RADICE / c).is_dir():
            shutil.copytree(RADICE / c, uscita / c, ignore=IGNORA, symlinks=True)
    for f in FILE:
        if (RADICE / f).is_file():
            shutil.copy2(RADICE / f, uscita / f)
    skill = skill_di_arturo()
    for comando in sorted((RADICE / "commands").glob("*.md")):
        if (uscita / "skills" / comando.stem).exists():
            raise SystemExit(f"commands/{comando.name} e skills/{comando.stem} hanno lo stesso nome")
        comando_in_skill(comando, uscita / "skills" / comando.stem)

    for md in uscita.rglob("*.md"):
        if md.is_symlink():
            continue
        dentro_skill = md.relative_to(uscita).parts[0] == "skills"
        radice_codice = "${CLAUDE_PLUGIN_ROOT}" if dentro_skill else "$ARTURO_CODICE"
        prima = md.read_text(encoding="utf-8")
        dopo = riscrivi(prima, radice_codice, skill)
        if dopo != prima:
            md.write_text(dopo, encoding="utf-8")

    settings = json.loads((RADICE / "settings.json").read_text(encoding="utf-8"))
    dati_hooks = hooks_json(settings)
    # Il mod di Arturo (skills/arturo) dentro un plugin non si carica da solo: lo porta il plugin Arturo, con
    # gli hook di comando nello stesso hooks.json (provato su 2.1.317, 3/11/2026). Così il tool resta
    # mcp__arturo__ruota e gli atom restano del plugin "arturo" come nel clone.
    mod = uscita / "skills" / NOME
    if (mod / "hooks" / "register.tsx").is_file():
        dati_hooks["modules"] = [f"../skills/{NOME}/hooks/register.tsx"]
        shutil.rmtree(mod / ".claude-plugin", ignore_errors=True)
        (mod / "hooks" / "hooks.json").unlink(missing_ok=True)
    (uscita / "hooks" / "hooks.json").write_text(
        json.dumps(dati_hooks, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (uscita / "impostazioni").mkdir(exist_ok=True)
    (uscita / "impostazioni" / "arturo.json").write_text(
        json.dumps(impostazioni(settings), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    meta = uscita / ".claude-plugin"
    meta.mkdir(exist_ok=True)
    descrizione = "Arturo: guardie, metodo e skill condivise sopra Claude Code. Lo strato personale è l'Orsa, in ~/.claude."
    manifest = {
        "name": NOME, "version": versione.lstrip("v"), "description": descrizione,
        "author": {"name": "Federico Nejrotti"}, "homepage": "https://github.com/stellakamikaze/arturo",
        "license": "MIT",
    }
    # Il contratto dei valori in $.state del mod: senza, Claude Code rifiuta gli atom del modulo.
    if "modules" in dati_hooks and (mod / "types" / "index.d.ts").is_file():
        manifest["types"] = f"./skills/{NOME}/types/index.d.ts"
    (meta / "plugin.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    # Un altro mod in skills/<nome>/.claude-plugin è un plugin a sé: nel clone Claude Code lo carica dalla
    # cartella skills, dentro un plugin no. Il marketplace lo elenca accanto ad Arturo.
    plugin = [{"name": NOME, "source": "./", "description": descrizione, "version": versione.lstrip("v")}]
    for mod in sorted((uscita / "skills").glob("*/.claude-plugin/plugin.json")):
        dati = json.loads(mod.read_text(encoding="utf-8"))
        plugin.append({"name": dati["name"], "source": f"./skills/{mod.parent.parent.name}",
                       "description": dati.get("description", ""), "version": dati.get("version", "0.1.0")})
    (meta / "marketplace.json").write_text(json.dumps({
        "name": NOME, "owner": {"name": "Federico Nejrotti"}, "description": descrizione, "plugins": plugin,
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    # Il ramo plugin si scarica byte per byte: su Windows, con core.autocrlf, git riscriverebbe gli a capo
    # e il MANIFEST darebbe cambiati tutti i file di testo.
    (uscita / ".gitattributes").write_text("* -text\n", encoding="utf-8")
    # Il MANIFEST per ultimo, quando ogni file è al suo posto.
    fiducia.scrivi_manifest(uscita)


def catalogo(cartella: Path, tag: str, sha: str, repo: str) -> None:
    """Il catalogo che le persone aggiungono (claude plugin marketplace add stellakamikaze/arturo#catalogo).
    Arturo vi è fissato allo sha del tag firmato: Claude Code installa quello sha e nient'altro, e
    `aggiornamenti.py plugin` controlla prima che il tag sia firmato e porti proprio quello sha."""
    if not TAG_PLUGIN.fullmatch(tag):
        raise SystemExit(f"il tag {tag} non ha la forma plugin-vN.N.N")
    if not re.fullmatch(r"[0-9a-f]{40}", sha):
        raise SystemExit("lo sha va scritto intero, 40 caratteri esadecimali")
    descrizione = "Arturo: guardie, metodo e skill condivise sopra Claude Code. Lo strato personale è l'Orsa, in ~/.claude."
    meta = cartella / ".claude-plugin"
    meta.mkdir(parents=True, exist_ok=True)
    (meta / "marketplace.json").write_text(json.dumps({
        "name": NOME, "owner": {"name": "Federico Nejrotti"}, "description": descrizione,
        "plugins": [{"name": NOME, "description": descrizione, "version": tag[len("plugin-v"):],
                     "source": {"source": "github", "repo": repo, "ref": tag, "sha": sha}}],
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def verifica(cartella: Path) -> list[str]:
    """Il contratto del pacchetto: niente codice cercato in ~/.claude, hook tutti nel plugin."""
    errori = []
    voci = "|".join(re.escape(c) for c in CODICE if c not in ("docs", "tests"))
    fisso = re.compile(rf"(?:~|\$HOME|\$\{{HOME\}})/\.claude/(?:{voci})(?:/|\b)")
    for md in cartella.rglob("*.md"):
        if md.is_symlink() or md.relative_to(cartella).parts[0] == "docs":
            continue
        for n, riga in enumerate(md.read_text(encoding="utf-8").splitlines(), 1):
            if fisso.search(riga):
                errori.append(f"{md.relative_to(cartella)}:{n} {riga.strip()[:100]}")
    hooks = json.loads((cartella / "hooks" / "hooks.json").read_text(encoding="utf-8"))
    for comando in re.findall(r'"command": "([^"]*)"', json.dumps(hooks)):
        if "~/.claude/" in comando or "$HOME/.claude/" in comando:
            errori.append(f"hooks.json: {comando[:100]}")
        for rel in re.findall(r"\$\{CLAUDE_PLUGIN_ROOT\}/(\S+)", comando):
            if not (cartella / rel).exists():
                errori.append(f"hooks.json: manca {rel}")
    for modulo in hooks.get("modules", []):
        if not (cartella / "hooks" / modulo).resolve().is_file():
            errori.append(f"hooks.json: manca il modulo {modulo}")
    manifest = json.loads((cartella / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))
    if hooks.get("modules") and not (cartella / str(manifest.get("types", "manca"))).is_file():
        errori.append("plugin.json: il modulo del mod c'è, il contratto dei tipi (types) no")
    if (cartella / "skills" / NOME / ".claude-plugin").exists():
        errori.append(f"skills/{NOME}/.claude-plugin nel pacchetto: il mod lo porta il plugin, non è un plugin a sé")
    if (cartella / "commands").exists():
        errori.append("commands/ nel pacchetto: un comando del plugin prende il prefisso arturo:")
    differenze = fiducia.confronta(cartella)
    if differenze is None:
        errori.append(f"{fiducia.MANIFEST}: manca o non si legge")
    else:
        for tipo, elenco in differenze.items():
            errori += [f"{fiducia.MANIFEST}: {tipo.replace('_', ' ')} {p}" for p in elenco[:10]]
    if (cartella / fiducia.FIRMA).is_file():
        esito, motivo = fiducia.verifica_firma(cartella, cartella / fiducia.FIRMATARI)
        if esito != "ok":
            errori.append(f"{fiducia.FIRMA}: {motivo}")
    return errori


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    gruppo = parser.add_mutually_exclusive_group(required=True)
    gruppo.add_argument("--uscita", type=Path)
    gruppo.add_argument("--verifica", type=Path)
    gruppo.add_argument("--catalogo", type=Path)
    parser.add_argument("--versione", default=None)
    parser.add_argument("--firma", type=Path, default=None, help="chiave privata dei rilasci (file 600 temporaneo)")
    parser.add_argument("--tag")
    parser.add_argument("--sha")
    parser.add_argument("--repo", default="stellakamikaze/arturo")
    argomenti = parser.parse_args()
    if argomenti.catalogo:
        if not (argomenti.tag and argomenti.sha):
            parser.error("--catalogo vuole --tag e --sha")
        catalogo(argomenti.catalogo, argomenti.tag, argomenti.sha, argomenti.repo)
        print(f"catalogo in {argomenti.catalogo}: arturo {argomenti.tag} @ {argomenti.sha[:12]}")
        return 0
    if argomenti.verifica:
        errori = verifica(argomenti.verifica)
        for e in errori:
            print("ERRORE", e)
        print(f"pacchetto: {len(errori)} errori")
        return 1 if errori else 0
    impacchetta(argomenti.uscita.resolve(), argomenti.versione or versione_da_git())
    if argomenti.firma:
        fiducia.firma(argomenti.uscita.resolve(), argomenti.firma)
    errori = verifica(argomenti.uscita.resolve())
    for e in errori[:30]:
        print("ERRORE", e)
    print(f"pacchetto in {argomenti.uscita}: {len(errori)} errori")
    return 1 if errori else 0


if __name__ == "__main__":
    sys.exit(main())
