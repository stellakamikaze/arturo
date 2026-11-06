#!/usr/bin/env python3
"""AV01-AV10: col plugin l'avvio e la barra dicono quando c'è un rilascio nuovo di Arturo (#4860, strati F5).

Col clone `aggiornamenti.py controlla` scarica i tag e la barra mostra "↑ Arturo vX". Col plugin non c'è git, e
fino al 6/11/2026 stato e controlla tacevano: un rilascio nuovo si scopriva solo lanciando /aggiorna.

AV01 controlla, col catalogo a una versione più nuova di quella installata, scrive lo stato "manuale" con la
     versione nuova; col catalogo pari scrive "aggiornato";
AV02 stato dice all'avvio la versione nuova e /aggiorna; con la versione installata pari tace;
AV03 controlla non riscarica il catalogo prima di un'ora, salvo --subito;
AV04 la barra mostra "↑ Arturo <versione> · serve /aggiorna", e con lo stato vecchio lancia controlla dal codice
     accanto a sé (la cartella del plugin), non da ~/.claude/bin che col plugin non c'è;
AV05 session-start annuncia il rilascio nuovo anche con ~/.claude senza git, il caso di chi ha migrato (#4897);
AV06 chi installa da zero non riceve la storia di Arturo come novità da leggere: il primo avvio la segna vista;
AV07 col plugin NOVITA.md sta accanto al codice, e l'avvio conta lo stesso le voci non viste;
AV08 l'avvio lancia il controllo staccato: chi ha una barra sua non lancia quello della barra di Arturo;
AV09 senza ARTURO_RADICE lo stato va in CLAUDE_CONFIG_DIR, dove lo legge la barra;
AV10 dopo /aggiorna la barra smette di dire "serve /aggiorna" subito (revisione del 6/11/2026, AV06-AV10).

Gira su una copia del repository senza git (così aggiornamenti.py si crede il plugin), con una CLI di Claude
finta: niente rete. Sulla base 3b5e6c3 sono tutti rossi. --avvelena: ogni copia rotta fa rosso il caso suo.
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

CASI = ["AV01", "AV02", "AV03", "AV04", "AV05", "AV06", "AV07", "AV08", "AV09", "AV10"]
DISCRIMINANTI = list(CASI)
NODE = shutil.which("node") or "node"


def esegui(argv, **kw):
    return subprocess.run(argv, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60, **kw)


def claude_finto(tmp: Path) -> Path:
    if os.name == "nt":
        f = tmp / "claude.cmd"
        f.write_text("@exit /b 0\r\n", encoding="utf-8")
    else:
        f = tmp / "claude"
        f.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
        f.chmod(0o755)
    return f


def catalogo(cartella: Path, versione: str) -> None:
    (cartella / ".claude-plugin").mkdir(parents=True, exist_ok=True)
    (cartella / ".claude-plugin" / "marketplace.json").write_text(json.dumps({"name": "arturo", "plugins": [
        {"name": "arturo", "version": versione, "source": {"source": "github", "ref": f"plugin-v{versione}"}}]}),
        encoding="utf-8")


def prova(repo: Path) -> list[str]:
    rossi = []
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        copia = tmp / "plugin"
        shutil.copytree(repo, copia, ignore=shutil.ignore_patterns(".git", "__pycache__", "node_modules", "tests"))
        (copia / ".claude-plugin").mkdir(exist_ok=True)
        (copia / ".claude-plugin" / "plugin.json").write_text('{"name": "arturo", "version": "0.2.5"}', encoding="utf-8")
        casa = tmp / "casa"
        orsa = casa / ".claude"
        (orsa / "plugins").mkdir(parents=True)
        (orsa / "session-env").mkdir()
        cat = tmp / "catalogo"
        catalogo(cat, "0.2.6")
        (orsa / "plugins" / "installed_plugins.json").write_text(json.dumps({"plugins": {"arturo@arturo": [
            {"scope": "user", "version": "0.2.5", "installPath": str(copia)}]}}), encoding="utf-8")
        (orsa / "plugins" / "known_marketplaces.json").write_text(json.dumps({"arturo": {"installLocation": str(cat)}}),
                                                                 encoding="utf-8")
        env = {**os.environ, "HOME": str(casa), "USERPROFILE": str(casa), "CLAUDE_CONFIG_DIR": str(orsa),
               "ARTURO_RADICE": str(orsa), "ARTURO_CLAUDE": str(claude_finto(tmp)), "ARTURO_TELEMETRIA": "0"}
        agg = [sys.executable, str(copia / "bin" / "aggiornamenti.py")]
        stato_file = orsa / "session-env" / "aggiornamento.json"
        leggi = lambda: json.loads(stato_file.read_text(encoding="utf-8")) if stato_file.exists() else {}

        c1 = esegui(agg + ["controlla"], env=env)
        s1 = leggi()
        s2 = esegui(agg + ["stato"], env=env)
        catalogo(cat, "0.2.5")
        c3 = esegui(agg + ["controlla"], env=env)
        s3 = leggi()
        c4 = esegui(agg + ["controlla", "--subito"], env=env)
        s4 = leggi()
        s5 = esegui(agg + ["stato"], env=env)
        if c1.returncode != 0 or s1.get("stato") != "manuale" or s1.get("versione") != "0.2.6" \
                or s4.get("stato") != "aggiornato":
            rossi.append(f"AV01 controlla: rc {c1.returncode}, stato {s1} poi {s4}, {c1.stderr[-160:]!r}")
        if "c'è la versione 0.2.6" not in s2.stdout or "/aggiorna" not in s2.stdout or s5.stdout.strip():
            rossi.append(f"AV02 stato all'avvio: {s2.stdout[-160:]!r} poi {s5.stdout[-120:]!r}")
        if c3.returncode != 0 or not s1 or s3 != s1:
            rossi.append(f"AV03 un controllo entro l'ora: stato {s1} diventato {s3}")

        entrata = json.dumps({"model": {"display_name": "Opus"}, "workspace": {"current_dir": str(casa)}})
        env_barra = {k: v for k, v in env.items() if k != "CLAUDE_CONFIG_DIR"}
        stato_file.write_text(json.dumps({"controllato": int(time.time()), "versione": "0.2.6", "stato": "manuale",
                                          "plugin": True}), encoding="utf-8")
        barra = esegui([NODE, str(copia / "hooks" / "statusline.js")], input=entrata, env=env_barra).stdout
        stato_file.write_text(json.dumps({"controllato": 0, "versione": "0.2.6", "stato": "manuale", "plugin": True}),
                              encoding="utf-8")
        esegui([NODE, str(copia / "hooks" / "statusline.js")], input=entrata, env=env_barra)
        rilanciato = False
        for _ in range(40):  # controlla parte staccato: si aspetta che scriva lo stato nuovo
            if leggi().get("stato") == "aggiornato":
                rilanciato = True
                break
            time.sleep(0.25)
        if "↑ Arturo 0.2.6 · serve /aggiorna" not in barra or not rilanciato:
            rossi.append(f"AV04 barra: {barra[-120:]!r}, controlla lanciato dalla barra {rilanciato}")

        # L'hook vero, con ~/.claude che non è un repository: dopo arturo migra è così per chi non ha un repo suo.
        catalogo(cat, "0.2.6")
        stato_file.write_text(json.dumps({"controllato": int(time.time()), "versione": "0.2.6", "stato": "manuale",
                                          "plugin": True}), encoding="utf-8")
        avvio = esegui([shutil.which("bash") or "bash", str(copia / "hooks" / "session-start.sh")],
                       input='{"source": "startup"}', env=env)
        if "c'è la versione 0.2.6" not in avvio.stdout:
            rossi.append(f"AV05 avvio senza git: rc {avvio.returncode}, {avvio.stdout[-200:]!r}, {avvio.stderr[-160:]!r}")

        # Il primo avvio qui sopra era quello di un'installazione nuova: niente segnalibro, niente setup finito.
        viste = orsa / "session-env" / "novita-viste"
        voci = [r[3:] for r in (copia / "NOVITA.md").read_text(encoding="utf-8").splitlines() if r.startswith("## ")]
        if "aggiornamenti dell'harness" in avvio.stdout or not viste.exists() \
                or viste.read_text(encoding="utf-8").splitlines() != voci:
            rossi.append(f"AV06 primo avvio: segnalibro {viste.exists()}, {avvio.stdout[-200:]!r}")

        if viste.exists():
            viste.write_text("\n".join(voci[1:]) + "\n", encoding="utf-8")
        avvio2 = esegui([shutil.which("bash") or "bash", str(copia / "hooks" / "session-start.sh")],
                        input='{"source": "startup"}', env=env)
        if "1 aggiornamenti dell'harness" not in avvio2.stdout:
            rossi.append(f"AV07 novità col plugin: {avvio2.stdout[-200:]!r}")

        stato_file.unlink(missing_ok=True)
        esegui(agg + ["stato"], env=env)
        partito = False
        for _ in range(40):  # controlla parte staccato
            if leggi().get("versione") == "0.2.6":
                partito = True
                break
            time.sleep(0.25)
        if not partito:
            rossi.append(f"AV08 avvio senza barra: stato {leggi()}")

        stato_file.unlink(missing_ok=True)
        altra = tmp / "altra-casa"
        altra.mkdir()
        env9 = {k: v for k, v in env.items() if k != "ARTURO_RADICE"}
        env9.update({"HOME": str(altra), "USERPROFILE": str(altra)})
        esegui(agg + ["controlla", "--subito"], env=env9)
        if leggi().get("versione") != "0.2.6" or (altra / ".claude").exists():
            rossi.append(f"AV09 CLAUDE_CONFIG_DIR: stato {leggi()}, casa toccata {(altra / '.claude').exists()}")

        sha = "a" * 40
        (cat / ".claude-plugin" / "marketplace.json").write_text(json.dumps({"name": "arturo", "plugins": [
            {"name": "arturo", "version": "0.2.6", "source": {"source": "github", "repo": "prova/arturo",
                                                              "ref": "plugin-v0.2.6", "sha": sha}}]}), encoding="utf-8")
        (orsa / "plugins" / "installed_plugins.json").write_text(json.dumps({"plugins": {"arturo@arturo": [
            {"scope": "user", "version": "0.2.6", "installPath": str(copia), "gitCommitSha": sha}]}}), encoding="utf-8")
        stato_file.write_text(json.dumps({"controllato": int(time.time()), "versione": "0.2.6", "stato": "manuale",
                                          "plugin": True}), encoding="utf-8")
        aggiorna = esegui(agg + ["plugin"], env=env)
        barra2 = esegui([NODE, str(copia / "hooks" / "statusline.js")], input=entrata, env=env_barra).stdout
        if "GIÀ AGGIORNATO" not in aggiorna.stdout or "serve /aggiorna" in barra2:
            rossi.append(f"AV10 dopo /aggiorna: {aggiorna.stdout[-120:]!r}, barra {barra2[-100:]!r}")
    return rossi


# (caso, file, testo giusto, testo rotto): ogni veleno toglie la riga che il caso sorveglia.
VELENI = [
    ("AV01", "bin/aggiornamenti.py", '"plugin": True} if nuova else', '"plugin": True} if False else'),
    ("AV02", "bin/aggiornamenti.py", '    if stato.get("plugin") and stato.get("stato") == "manuale"',
     '    if False and stato.get("plugin") and stato.get("stato") == "manuale"'),
    ("AV03", "bin/aggiornamenti.py",
     '        return 0\n    _, radici = _moduli()\n    _claude("marketplace", "update", "arturo", timeout=120)',
     '        pass\n    _, radici = _moduli()\n    _claude("marketplace", "update", "arturo", timeout=120)'),
    ("AV04", "hooks/statusline.js", "const AGG_SCRIPT = path.join(CODICE_AGG, 'bin', 'aggiornamenti.py');",
     "const AGG_SCRIPT = path.join(CLAUDE_DIR, 'bin', 'aggiornamenti.py');"),
    ("AV05", "hooks/session-start.sh", 'elif [ -f "$ARTURO_CODICE/bin/aggiornamenti.py" ] && [ ! -e "$ARTURO_CODICE/.git" ]; then',
     'elif false; then'),
    ("AV06", "hooks/session-start.sh",
     'if [ ! -e "$NOVITA_VISTE" ] && [ -z "$NOVITA_VECCHIA" ] && [ ! -f "$HOME/.claude/data/setup-fatto" ]; then',
     'if false; then'),
    ("AV07", "hooks/session-start.sh", '[ -f "$NOVITA_FILE" ] || NOVITA_FILE="$ARTURO_CODICE/NOVITA.md"', 'true'),
    ("AV08", "bin/aggiornamenti.py", '        avvia_staccato(r, "controlla")\n', '        pass\n'),
    ("AV09", "bin/aggiornamenti.py", 'os.environ.get("ARTURO_RADICE") or os.environ.get("CLAUDE_CONFIG_DIR") or',
     'os.environ.get("ARTURO_RADICE") or'),
    ("AV10", "bin/aggiornamenti.py", '        segna_aggiornato(radice())\n        print(f"GIÀ AGGIORNATO: {tag}")',
     '        print(f"GIÀ AGGIORNATO: {tag}")'),
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
            rossi = prova(copia)
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
        codici = [r.split()[0] for r in rossi]
        assert codici == DISCRIMINANTI, f"baseline non discriminante: rossi {codici}, attesi {DISCRIMINANTI}"
        print(f"BASELINE_DISCRIMINANTE={','.join(codici)}")
        return 0
    for r in rossi:
        print("ROSSO", r)
    print(f"avviso del plugin: {len(CASI) - len(rossi)}/{len(CASI)} casi verdi")
    return 1 if rossi else 0


if __name__ == "__main__":
    sys.exit(main())
