#!/usr/bin/env python3
"""bin/fine-coda.py passa dal controllo dei segreti (21/11/2026, #6249, revisione del 20/11 rilievi A2 e A3).

Commit e push della coda partono da subprocess: la guardia del dispatcher legge solo i comandi Bash, e un
token in settings.json usciva su GitHub senza controllo.

FS01 un token GitHub in settings.json, in stage: exit 7, niente commit, niente push. L'uscita nomina il file e
     il tipo di segreto, mai il valore.
FS02 un commit fatto prima a mano, non ancora spinto, con una chiave in bin/: stage pulito, exit 7, niente
     push, il commit resta locale.
FS03 un path dell'aggancio personale con una chiave, verso un remote privato: exit 7, niente commit.
FS04 la guardia dei segreti non c'è: exit 7, niente commit. La coda non manda niente senza controllo.
FS05 (A3) verso un remote pubblico i file nuovi in commands/ e hooks/ restano fuori, e la riga FILE TUOI NON
     SALVATI li nomina; un file già tracciato e modificato in bin/ entra. Verso un remote privato il file nuovo
     entra.

Sulla base 6132caf la coda committa e spinge tutto: rossi tutti i casi.
"""
from __future__ import annotations

import argparse
import importlib.util
import subprocess
import sys
import tempfile
from pathlib import Path

QUI = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("banco_fine_coda", QUI / "test_fine_coda_2026_10_30.py")
fc = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(fc)

CASI = ["FS01", "FS02", "FS03", "FS04", "FS05"]
# Le chiavi finte si compongono a pezzi: questo file non deve far parlare la guardia.
TOKEN = "gh" + "p_" + "A1b2C3d4" * 5
AWS = "AK" + "IA" + "ABCDEFGHIJKLMNOP"


def con_lab(repo, ref, prova, **k):
    with tempfile.TemporaryDirectory(prefix="arturo-fs-") as tmp:
        try:
            lab = fc.Lab(repo, ref, Path(tmp), **k)
            if not (lab.cl / "bin" / "fine-coda.py").exists():
                return "bin/fine-coda.py assente"
            return prova(lab)
        except (RuntimeError, OSError, ValueError, subprocess.TimeoutExpired) as e:
            return f"eccezione {e}"


def fs01(lab):
    lab.scrivi("settings.json", '{"env": {"GITHUB_TOKEN": "' + TOKEN + '"}}\n')
    prima = lab.commit()
    r = lab.coda(lab.handoff())
    uscito = "settings.json" in lab.nel_remoto()
    if r.returncode != 7 or lab.commit() != prima or uscito or "settings.json" not in r.stdout \
            or "GitHub token" not in r.stdout or TOKEN in r.stdout + r.stderr:
        return f"rc={r.returncode} commit {prima}->{lab.commit()} uscito={uscito} {r.stdout.strip()[-200:]!r}"


def fs02(lab):
    lab.scrivi("bin/avvio.sh", f"export AWS_ACCESS_KEY_ID={AWS}\n")
    lab.git(lab.cl, "add", "bin/avvio.sh")
    lab.git(lab.cl, "commit", "-q", "-m", "a mano")
    locale = lab.git(lab.cl, "rev-parse", "HEAD").strip()
    r = lab.coda(lab.handoff())
    uscito = "bin/avvio.sh" in lab.nel_remoto()
    ancora = lab.git(lab.cl, "merge-base", "--is-ancestor", locale, "HEAD") == ""
    if r.returncode != 7 or uscito or not ancora or "bin/avvio.sh" not in r.stdout or "niente push" not in r.stdout \
            or AWS in r.stdout + r.stderr:
        return f"rc={r.returncode} uscito={uscito} {r.stdout.strip()[-200:]!r}"


AGGANCIO = """import json, sys
d = json.load(sys.stdin)
if d["fase"] == "prima-commit":
    open(d["radice"] + "/personale/stato.txt", "w", encoding="utf-8").write("chiave=" + "%s" + "\\n")
    print(json.dumps({"esiti": [], "path": ["personale/stato.txt"], "blocca": None}))
else:
    print(json.dumps({"esiti": [], "path": [], "blocca": None}))
"""


def fs03(lab):
    lab.scrivi("personale/fine-coda.py", AGGANCIO % TOKEN)
    lab.git(lab.cl, "add", "-f", "personale/fine-coda.py")
    lab.git(lab.cl, "commit", "-q", "-m", "aggancio")
    lab.git(lab.cl, "push", "-q", "origin", "main")
    prima = lab.commit()
    r = lab.coda(lab.handoff())
    uscito = "personale/stato.txt" in lab.nel_remoto()
    if r.returncode != 7 or lab.commit() != prima or uscito or "personale/stato.txt" not in r.stdout:
        return f"rc={r.returncode} commit {prima}->{lab.commit()} uscito={uscito} {r.stdout.strip()[-200:]!r}"


def fs04(lab):
    (lab.cl / "hooks" / "commit-secret-gate.py").unlink()
    prima = lab.commit()
    r = lab.coda(lab.handoff())
    if r.returncode != 7 or lab.commit() != prima or "non si carica" not in r.stdout:
        return f"rc={r.returncode} commit {prima}->{lab.commit()} {r.stdout.strip()[-200:]!r}"


def fs05(lab):
    lab.scrivi("commands/mio.md", "il mio comando\n")
    lab.scrivi("hooks/mio.py", "print('mio')\n")
    lab.scrivi("bin/todo_store.py", (lab.cl / "bin" / "todo_store.py").read_text(encoding="utf-8") + "# ritocco\n")
    r = lab.coda(lab.handoff())
    remoto = set(lab.nel_remoto())
    usciti = sorted({"commands/mio.md", "hooks/mio.py"} & remoto)
    ritocco = "# ritocco" in lab.git(lab.remoto, "show", "main:bin/todo_store.py")
    if r.returncode != 0 or usciti or not ritocco or "FILE TUOI NON SALVATI" not in r.stdout \
            or "commands/mio.md" not in r.stdout:
        return f"pubblico rc={r.returncode} usciti {usciti} ritocco={ritocco} {r.stdout.strip()[-200:]!r}"


def fs05_privato(lab):
    lab.scrivi("commands/mio.md", "il mio comando\n")
    r = lab.coda(lab.handoff())
    if r.returncode != 0 or "commands/mio.md" not in lab.nel_remoto():
        return f"privato rc={r.returncode} {r.stdout.strip()[-200:]!r}"


def prova(repo: Path, ref: str | None) -> list:
    rossi = []
    for codice, passi in (("FS01", [(fs01, {})]), ("FS02", [(fs02, {})]), ("FS03", [(fs03, {})]),
                          ("FS04", [(fs04, {})]),
                          ("FS05", [(fs05, {"visibilita": "PUBLIC"}), (fs05_privato, {})])):
        esiti = [e for e in (con_lab(repo, ref, fn, **k) for fn, k in passi) if e]
        if esiti:
            rossi.append(f"{codice} {'; '.join(esiti)}")
    return rossi


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", default=str(QUI.parent))
    parser.add_argument("--baseline-ref")
    argomenti = parser.parse_args()
    rossi = prova(Path(argomenti.repo), argomenti.baseline_ref)
    if argomenti.baseline_ref:
        codici = [r.split()[0] for r in rossi]
        assert codici == CASI, f"baseline non discriminante: rossi {codici}, attesi {CASI}"
        print(f"BASELINE_DISCRIMINANTE={','.join(codici)}")
        return 0
    for r in rossi:
        print("ROSSO", r)
    print(f"coda di /fine e segreti: {len(CASI) - len(rossi)}/{len(CASI)} casi verdi")
    return 1 if rossi else 0


if __name__ == "__main__":
    sys.exit(main())
