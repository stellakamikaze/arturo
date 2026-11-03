#!/usr/bin/env python3
"""IP01-IP08: il plugin di Arturo generato dal repository rispetta il contratto (strati F2, docs/strati.md).

IP01 bin/impacchetta.py genera il pacchetto e la sua verifica non trova errori;
IP02 ogni commands/<nome>.md è skills/<nome>/SKILL.md con name: e disable-model-invocation, e nel
     pacchetto non c'è commands/ (un comando del plugin prende il prefisso arturo:);
IP03 hooks/hooks.json ha tutti gli hook di settings.json, coi file tra virgolette in ${CLAUDE_PLUGIN_ROOT};
IP04 impostazioni/arturo.json non ha hook, lo stile è "arturo:Conciso", la barra legge il puntatore;
IP05 i percorsi ai dati della persona restano in ~/.claude (data/handoffs in /fine), quelli al codice no;
IP06 arturo impostazioni applica: in un'Orsa vuota scrive settings e blocco, la seconda volta non cambia
     niente, una voce propria della persona resta, una voce cambiata da tutte e due le parti ferma
     tutto con rc 1 e il file intatto;
IP07 col codice fuori da ~/.claude l'avvio scrive ~/.claude/arturo/radice e dice dove sta il codice;
IP08 il marketplace elenca Arturo, e il plugin Arturo porta il modulo del suo mod (skills/arturo/hooks/register.tsx
     sotto "modules" in hooks.json, mod passo 3 del 3/11/2026): nel pacchetto skills/arturo non è un plugin a sé.

Sulla base c247fed (il dev prima di F2) sono tutti rossi: il generatore non c'è. Con --avvelena una
copia del repository rotta in un punto alla volta deve far fallire il caso che lo sorveglia.
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

CASI = ["IP01", "IP02", "IP03", "IP04", "IP05", "IP06", "IP07", "IP08"]
DISCRIMINANTI = list(CASI)
BASH = shutil.which("bash") or "bash"


def esegui(argv, **kw):
    return subprocess.run(argv, capture_output=True, text=True, encoding="utf-8", errors="replace",
                          timeout=120, **kw)


def comandi_hook(hooks: dict) -> list:
    return [h.get("command", "") for gruppi in hooks.values() for g in gruppi for h in g.get("hooks", [])]


def prova(repo: Path) -> list[str]:
    rossi = []
    generatore = repo / "bin" / "impacchetta.py"
    if not generatore.exists():
        return [f"{c} manca bin/impacchetta.py" for c in CASI]
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        pacchetto = tmp / "arturo"
        esito = esegui([sys.executable, str(generatore), "--uscita", str(pacchetto), "--versione", "v0.2.0"])
        if esito.returncode != 0 or not (pacchetto / ".claude-plugin" / "plugin.json").exists():
            return [f"IP01 il generatore fallisce: {(esito.stdout + esito.stderr)[-200:]!r}"] + \
                   [f"{c} pacchetto non generato" for c in CASI[1:]]

        comandi = sorted(p.stem for p in (repo / "commands").glob("*.md"))
        mancanti = []
        for nome in comandi:
            skill = pacchetto / "skills" / nome / "SKILL.md"
            testa = skill.read_text(encoding="utf-8").split("\n---", 1)[0] if skill.exists() else ""
            if f"name: {nome}" not in testa or "disable-model-invocation: true" not in testa:
                mancanti.append(nome)
        if mancanti or (pacchetto / "commands").exists() or not comandi:
            rossi.append(f"IP02 comandi non diventati skill: {mancanti[:4]}")

        settings = json.loads((repo / "settings.json").read_text(encoding="utf-8"))
        hooks = json.loads((pacchetto / "hooks" / "hooks.json").read_text(encoding="utf-8")).get("hooks", {})
        attesi, generati = comandi_hook(settings.get("hooks", {})), comandi_hook(hooks)
        sbagliati = [c for c in generati if "~/.claude/" in c or "$HOME/.claude/" in c
                     or ("${CLAUDE_PLUGIN_ROOT}" in c and '"${CLAUDE_PLUGIN_ROOT}/' not in c)]
        if len(attesi) != len(generati) or sbagliati or set(hooks) != set(settings.get("hooks", {})):
            rossi.append(f"IP03 hooks.json: {len(generati)} hook su {len(attesi)}, sbagliati {sbagliati[:2]}")

        imp = json.loads((pacchetto / "impostazioni" / "arturo.json").read_text(encoding="utf-8"))
        linea = imp.get("statusLine", {}).get("command", "")
        if "hooks" in imp or imp.get("outputStyle") != "arturo:Conciso" or "arturo/radice" not in linea:
            rossi.append(f"IP04 impostazioni: stile {imp.get('outputStyle')!r}, barra {linea[:60]!r}")

        fine = (pacchetto / "skills" / "fine" / "SKILL.md").read_text(encoding="utf-8")
        if "~/.claude/data/handoffs/" not in fine or "~/.claude/bin/" in fine or "${CLAUDE_PLUGIN_ROOT}/bin/" not in fine:
            rossi.append("IP05 /fine nel pacchetto: dati della persona spostati o codice ancora in ~/.claude/bin")

        orsa = tmp / "orsa"
        orsa.mkdir()
        (orsa / "settings.json").write_text('{"permissions": {"allow": ["Bash(mio-comando:*)"]}}\n', encoding="utf-8")
        env = {**os.environ, "CLAUDE_CONFIG_DIR": str(orsa), "ARTURO_TELEMETRIA": "0"}
        arturo = [sys.executable, str(pacchetto / "bin" / "arturo"), "impostazioni"]
        primo = esegui(arturo + ["applica"], env=env)
        dati = json.loads((orsa / "settings.json").read_text(encoding="utf-8"))
        secondo = esegui(arturo + ["applica"], env=env)
        blocco = orsa / "data" / "arturo-impostazioni.lock"
        ok = (primo.returncode == 0 and blocco.exists() and "Bash(mio-comando:*)" in dati["permissions"]["allow"]
              and dati.get("outputStyle") == "arturo:Conciso" and "già applicate" in secondo.stdout)
        dati["outputStyle"] = "Mio"
        (orsa / "settings.json").write_text(json.dumps(dati), encoding="utf-8")
        frammento = pacchetto / "impostazioni" / "arturo.json"
        nuovo = dict(imp, outputStyle="arturo:Altro")
        frammento.write_text(json.dumps(nuovo), encoding="utf-8")
        prima = (orsa / "settings.json").read_text(encoding="utf-8")
        terzo = esegui(arturo + ["applica"], env=env)
        if not ok or terzo.returncode != 1 or (orsa / "settings.json").read_text(encoding="utf-8") != prima \
                or "outputStyle" not in terzo.stderr:
            rossi.append(f"IP06 impostazioni applica: {(primo.stdout + secondo.stdout + terzo.stderr)[-200:]!r}")
        frammento.write_text(json.dumps(imp), encoding="utf-8")

        home = tmp / "casa"
        (home / ".claude").mkdir(parents=True)
        progetto = tmp / "progetto"
        progetto.mkdir()
        avvio = esegui([BASH, str(pacchetto / "hooks" / "session-start.sh")], input='{"source":"startup"}',
                       cwd=progetto, env={**os.environ, "HOME": str(home), "USERPROFILE": str(home),
                                          "ARTURO_TELEMETRIA": "0", "ARTURO_AGGIORNAMENTI": "manuali",
                                          "GIT_TERMINAL_PROMPT": "0"})
        puntatore = home / ".claude" / "arturo" / "radice"
        letto = puntatore.read_text(encoding="utf-8") if puntatore.exists() else ""
        if Path(letto).resolve() != pacchetto.resolve() if letto else True:
            rossi.append(f"IP07 puntatore della barra: {letto!r}")
        elif "ARTURO: il codice di Arturo sta in" not in avvio.stdout:
            rossi.append("IP07 l'avvio non dice dove sta il codice")

        mercato = json.loads((pacchetto / ".claude-plugin" / "marketplace.json").read_text(encoding="utf-8"))
        nomi = {p["name"]: p["source"] for p in mercato.get("plugins", [])}
        altri = sorted(p.parent.parent.name for p in (repo / "skills").glob("*/.claude-plugin/plugin.json")
                       if p.parent.parent.name != "arturo")
        moduli = json.loads((pacchetto / "hooks" / "hooks.json").read_text(encoding="utf-8")).get("modules")
        modulo_c_e = (pacchetto / "skills" / "arturo" / "hooks" / "register.tsx").is_file()
        if nomi.get("arturo") != "./" or any(nomi.get(m) != f"./skills/{m}" for m in altri) or "arturo" in [
                m for m in nomi if nomi[m] != "./"] or moduli != ["../skills/arturo/hooks/register.tsx"] \
                or not modulo_c_e or (pacchetto / "skills" / "arturo" / ".claude-plugin").exists():
            rossi.append(f"IP08 marketplace {nomi}, moduli {moduli}, modulo nel pacchetto {modulo_c_e}")
    return rossi


# (caso, file, testo giusto, testo rotto): ogni veleno toglie la riga che il caso sorveglia.
VELENI = [
    ("IP02", "bin/impacchetta.py", 'testa = f"name: {nome}\\n" + testa', "pass"),
    ("IP03", "bin/impacchetta.py", """r'"${CLAUDE_PLUGIN_ROOT}/\\1"'""", """r'${CLAUDE_PLUGIN_ROOT}/\\1'"""),
    ("IP04", "bin/impacchetta.py", 'resto["outputStyle"] = f"{NOME}:{stile}"', "pass"),
    ("IP06", "bin/impostazioni.py", "        return attuale, None, frammento, f\"{_dove(", "        return attuale, frammento, frammento, None and f\"{_dove("),
    ("IP07", "hooks/session-start.sh", '|| printf \'%s\' "$ARTURO_CODICE" > "$HOME/.claude/arturo/radice"', "|| true"),
    ("IP08", "bin/impacchetta.py", '        dati_hooks["modules"] = [f"../skills/{NOME}/hooks/register.tsx"]', "        pass"),
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
    print(f"impacchetta: {len(CASI) - len(rossi)}/{len(CASI)} casi verdi")
    return 1 if rossi else 0


if __name__ == "__main__":
    sys.exit(main())
