#!/usr/bin/env python3
"""PV01-PV05: le sessioni di prova, marcate dal nome prova- (#5877, prima /revisione del 17/11/2026).

PV01 un transcript con agent-name prova-… (dopo un altro nome) è di prova: rc 0, anche senza claude agents;
PV02 un nome qualunque, o nessun nome, non è di prova: rc 1; senza id di sessione rc 2;
PV03 --elimina su una prova in background lancia claude rm del suo lavoro, staccato, dopo l'attesa;
PV04 --elimina su una prova interattiva non lancia niente, e su una sessione vera non elimina niente;
PV05 /fine apre con la FASE 0 che lancia prova.py --elimina, e il metodo dice di nascere con --name prova-.

Senza rete né Claude: una HOME di prova e un claude finto (ARTURO_CLAUDE) che risponde ad agents --json e
scrive su file le chiamate rm. Sulla base 22e5935 (il dev prima) sono tutti rossi. --avvelena: ogni veleno
toglie la riga che il suo caso sorveglia.
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

CASI = ["PV01", "PV02", "PV03", "PV04", "PV05"]
FINTO = """#!/usr/bin/env python3
import json, os, sys
if sys.argv[1:2] == ["agents"]:
    print(open(os.environ["FINTO_AGENTS"]).read())
elif sys.argv[1:2] == ["rm"]:
    open(os.environ["FINTO_RM"], "a").write("rm " + " ".join(sys.argv[2:]) + "\\n")
"""


def esegui(argv, env):
    try:
        p = subprocess.run(argv, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60, env=env)
        return p.returncode, (p.stdout + p.stderr).strip()
    except (OSError, subprocess.TimeoutExpired) as e:
        return 99, str(e)


def prova(repo: Path, solo: str = "") -> list:
    rossi = []
    script = repo / "bin" / "prova.py"
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        orsa = tmp / "casa" / ".claude"
        cartella = orsa / "projects" / "-tmp-prova"
        cartella.mkdir(parents=True)
        nomi = {"11111111-aaaa": ["arturo-vecchio", "prova-5877"], "22222222-bbbb": ["arturo-lavoro"],
                "33333333-cccc": [], "44444444-dddd": ["prova-mb"], "55555555-eeee": ["prova-qui"]}
        for sid, lista in nomi.items():
            righe = [json.dumps({"type": "user", "message": {"role": "user", "content": "Rispondi solo: ok"}})]
            righe += [json.dumps({"type": "agent-name" if i else "custom-title",
                                  **({"agentName": n} if i else {"customTitle": n}), "sessionId": sid})
                      for i, n in enumerate(lista)]
            (cartella / f"{sid}.jsonl").write_text("\n".join(righe) + "\n", encoding="utf-8")
        finto = tmp / "claude"
        finto.write_text(FINTO, encoding="utf-8")
        finto.chmod(0o755)
        agents, rm = tmp / "agents.json", tmp / "rm.txt"
        agents.write_text(json.dumps([
            {"id": "ab12cd34", "kind": "background", "sessionId": "44444444-dddd", "name": "prova-mb"},
            {"kind": "interactive", "sessionId": "55555555-eeee", "name": "prova-qui"},
            {"id": "ef56ab78", "kind": "background", "sessionId": "22222222-bbbb", "name": "arturo-lavoro"}]))
        env = {**os.environ, "HOME": str(tmp / "casa"), "USERPROFILE": str(tmp / "casa"), "CLAUDE_CONFIG_DIR": str(orsa),
               "ARTURO_CLAUDE": str(finto), "FINTO_AGENTS": str(agents), "FINTO_RM": str(rm),
               "ARTURO_PROVA_ATTESA": "1", "PYTHONDONTWRITEBYTECODE": "1", "PYTHONIOENCODING": "utf-8"}
        env.pop("CLAUDE_CODE_SESSION_ID", None)

        def lancia(*args):
            return esegui([sys.executable, str(script), *args], env)

        if not solo or solo == "PV01":
            rc, out = lancia("--session", "11111111-aaaa")
            if rc != 0 or "prova-5877" not in out:
                rossi.append(f"PV01 prova marcata: rc {rc} · {out[:160]!r}")
        if not solo or solo == "PV02":
            esiti = [lancia("--session", s)[0] for s in ("22222222-bbbb", "33333333-cccc")] + [lancia()[0]]
            if esiti != [1, 1, 2]:
                rossi.append(f"PV02 non di prova: rc {esiti}")
        if not solo or solo == "PV03":
            rc, out = lancia("--session", "44444444-dddd", "--elimina")
            fatto = ""
            for _ in range(40):
                fatto = rm.read_text(encoding="utf-8") if rm.is_file() else ""
                if fatto:
                    break
                time.sleep(0.25)
            if rc != 0 or "claude rm ab12cd34" not in out or fatto.strip() != "rm ab12cd34":
                rossi.append(f"PV03 rm in background: rc {rc}, rm {fatto!r} · {out[:160]!r}")
        if not solo or solo == "PV04":
            prima = rm.read_text(encoding="utf-8") if rm.is_file() else ""
            rc1, out1 = lancia("--session", "55555555-eeee", "--elimina")
            rc2, out2 = lancia("--session", "22222222-bbbb", "--elimina")
            time.sleep(2)
            dopo = rm.read_text(encoding="utf-8") if rm.is_file() else ""
            if rc1 != 0 or "niente da eliminare" not in out1 or rc2 != 1 or dopo != prima:
                rossi.append(f"PV04 niente rm: rc {rc1}/{rc2}, rm in più {dopo[len(prima):]!r} · {out1[:120]!r}")
        if not solo or solo == "PV05":
            fine = (repo / "commands" / "fine.md").read_text(encoding="utf-8")
            metodo = (repo / "shared" / "metodo.md").read_text(encoding="utf-8")
            fase0 = fine.split("## FASE 0", 1)[1].split("## FASE 1", 1)[0] if "## FASE 0" in fine else ""
            if "## FASE 0" not in fine or "~/.claude/bin/prova.py --elimina" not in fase0 \
                    or fine.index("## FASE 0") > fine.index("## FASE 1") or "--name prova-" not in metodo:
                rossi.append(f"PV05 testi: FASE 0 {bool(fase0)}, prova.py {'prova.py --elimina' in fase0}, "
                             f"metodo {'--name prova-' in metodo}")
    return rossi


VELENI = [
    ("PV01", "bin/prova.py", "                if n:\n                    nome = n", "                if n and not nome:\n                    nome = n"),
    ("PV02", "bin/prova.py", 'MARCATO = re.compile(r"^\\s*prova-", re.I)', 'MARCATO = re.compile(r"^\\s*", re.I)'),
    ("PV03", "bin/prova.py", '        elif elimina_dopo(programma_claude(), lavoro):', '        elif False:'),
    ("PV04", "bin/prova.py", "    if not e_prova(nome):\n", "    if False:\n"),
    ("PV05", "commands/fine.md", "`python3 ~/.claude/bin/prova.py --elimina; echo \"rc=$?\"`", "`true`"),
]


def avvelena(repo: Path) -> int:
    esiti = []
    for caso, rel, giusto, rotto in VELENI:
        with tempfile.TemporaryDirectory() as tmp:
            copia = Path(tmp) / "repo"
            shutil.copytree(repo, copia, ignore=shutil.ignore_patterns(".git", "__pycache__", "node_modules", "tests",
                                                                       "server", "docs"))
            testo = (copia / rel).read_text(encoding="utf-8")
            assert testo.count(giusto) == 1, f"veleno {caso}: il testo da rompere non c'è più in {rel}"
            (copia / rel).write_text(testo.replace(giusto, rotto), encoding="utf-8")
            rossi = prova(copia, solo=caso)
            if not rossi or not rossi[0].startswith(caso):
                print(f"VELENO {caso} NON ATTACCA ({rel}): {rossi[:1]}")
                return 1
            print(f"VELENO {caso} ROSSO: {rossi[0][:120]}")
            esiti.append(caso)
    print(f"VELENI_ROSSI={','.join(esiti)} veleni={len(VELENI)}")
    return 0 if len(esiti) == len(VELENI) else 1


def main() -> int:
    if os.name == "nt":
        print("prova: il claude finto è uno script POSIX, il banco gira su macOS e Linux")
        return 0
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument("--avvelena", action="store_true")
    parser.add_argument("--baseline-ref")
    a = parser.parse_args()
    repo = Path(a.repo).resolve()
    if a.avvelena:
        return avvelena(repo)
    rossi = prova(repo)
    if a.baseline_ref:
        codici = sorted({r.split()[0] for r in rossi})
        assert codici == CASI, f"baseline non discriminante: rossi {codici}, attesi {CASI}"
        print(f"BASELINE_DISCRIMINANTE={','.join(codici)}")
        return 0
    for r in rossi:
        print("ROSSO", r)
    print(f"prova: {len(CASI) - len({r.split()[0] for r in rossi})}/{len(CASI)} casi verdi")
    return 1 if rossi else 0


if __name__ == "__main__":
    sys.exit(main())
