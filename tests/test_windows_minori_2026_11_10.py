#!/usr/bin/env python3
"""WM01-WM03: tre difetti minori di Arturo su Windows dalla review del 9/11/2026 (#5102).

WM01 il conto delle sessioni salta i servizi di Claude Code (`daemon run`, `bg-spare --bg-spare`,
     `bg-pty-host --bg-pty-host`) ma conta una sessione con la parola "daemon" nel prompt, su Windows e sul Mac;
WM02 la copia negli appunti passa a clip il testo in UTF-16 col BOM, e agli altri programmi in UTF-8: con il testo
     e text=True clip leggeva nella codepage della console e le accentate arrivavano rotte (/segnala, arturo sessione);
WM03 con Windows Terminal il punto e virgola del prompt esce come \\; (per wt separa due schede anche dentro un
     argomento); il comando di riserva con cmd e la riga da scrivere a mano restano col testo intero;
WM04 impostazioni.py e unisci-settings.py scrivono in UTF-8 anche se la pipe ha un'altra codifica: su Windows è la
     codepage della console, e Claude Code leggeva le accentate rotte. Il banco la simula con PYTHONIOENCODING=latin-1.

Le funzioni girano in un processo figlio con bin/ della copia da provare, HOME e USERPROFILE spostati in una
cartella di prova, e il programma degli appunti finto: niente appunti veri, niente finestre. Sulla base 3f12336
sono tutti rossi. --avvelena: ogni copia rotta fa rosso il caso suo.
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

CASI = ["WM01", "WM02", "WM03", "WM04"]
DISCRIMINANTI = list(CASI)

# Gira nel figlio: sys.argv[1] è la cartella bin/ da provare. Stampa i rossi in JSON.
FIGLIO = r'''
import json, os, subprocess, sys
from pathlib import Path
sys.path.insert(0, sys.argv[1])
rossi = []

import aggiornamenti as a
w = r"C:\Users\x\.local\bin\claude.exe"
servizi_w = [f'{w}\t"{w}" daemon run --origin transient', f'{w}\t"{w}" bg-spare --bg-spare pipe-cc',
             f'{w}\t"{w}" bg-pty-host --bg-pty-host pipe-p 200 50']
sessioni_w = [f'{w}\t"{w}" riavvia il daemon di stampa', f'{w}\t"{w}" spiega daemon run', f'{w}\t"{w}" daemon',
              f'{w}\t"{w}"']
servizi_m = ["/Users/x/.local/bin/claude daemon run", "claude bg-spare --bg-spare /tmp/cc/b.claim.sock",
             "claude bg-pty-host --bg-pty-host /tmp/cc/b.pty.sock 200 50 -- /x/2.1.319 --bg-spare"]
sessioni_m = ["claude riavvia il daemon", "claude spiega daemon run", "claude -n prova /inizio daemon", "claude daemon", "claude"]
conti = (a.conta_sessioni(servizi_w + sessioni_w, windows=True), a.conta_sessioni(servizi_m + sessioni_m, windows=False))
if conti != (4, 5):
    rossi.append(f"WM01 sessioni contate (Windows, Mac) {conti}, attese (4, 5)")

import segnala
passati = []
def finto_run(comando, **kw):
    passati.append((comando[0], kw.get("input"), kw.get("text")))
    return subprocess.CompletedProcess(comando, 0)
segnala.shutil.which = lambda nome: nome
vero_run, segnala.subprocess.run = subprocess.run, finto_run
testo = "perché è già lì; città"
utf16, utf8 = b"\xff\xfe" + testo.encode("utf-16-le"), testo.encode("utf-8")
segnala.copia_appunti(testo)  # col programma di questo sistema: clip, pbcopy o wl-copy
subprocess.run = vero_run
nativo = "clip" if os.name == "nt" else "pbcopy" if sys.platform == "darwin" else "wl-copy"
attesi = [(nativo, utf16 if nativo == "clip" else utf8, None)]
converti = getattr(segnala, "testo_appunti", lambda t, programma: b"")
byte = (converti(testo, "clip"), converti(testo, "pbcopy"))
if passati != attesi or byte != (utf16, utf8):
    rossi.append(f"WM02 appunti: passati {[(p, i[:12] if isinstance(i, bytes) else i, t) for p, i, t in passati]!r}, "
                 f"byte {[b[:12] for b in byte]!r}")

import sessione
prompt = "/inizio arturo -- todo #12: prova; poi chiudi"
dove = Path("C:/Users/x/Documents/ClaudeCode")
sessione.shutil.which = lambda nome: "wt.exe" if nome == "wt" else None
con_wt, a_mano = sessione.comando("windows", dove, prompt)
sessione.shutil.which = lambda nome: None
con_cmd, _ = sessione.comando("windows", dove, prompt)
if con_wt[-1] != prompt.replace(";", "\\;") or con_cmd[-1] != prompt or prompt not in a_mano:
    rossi.append(f"WM03 punto e virgola: wt {con_wt[-1]!r}, cmd {con_cmd[-1]!r}, a mano {a_mano!r}")

for nome, argomenti in (("impostazioni.py", ["aiuto"]), ("unisci-settings.py", [])):
    p = subprocess.run([sys.executable, str(Path(sys.argv[1]) / nome), *argomenti], capture_output=True, timeout=30,
                       env=dict(os.environ, PYTHONIOENCODING="latin-1"))
    uscita = p.stdout + p.stderr
    try:
        accentate = any(c in uscita.decode("utf-8") for c in "àèéìòù")
    except UnicodeDecodeError:
        accentate = False
    if not accentate:
        rossi.append(f"WM04 {nome} non scrive in UTF-8: {uscita[:80]!r}")
print(json.dumps(rossi))
'''


def prova(repo: Path, solo: str = "") -> list:
    with tempfile.TemporaryDirectory() as tmp:
        casa = Path(tmp) / "casa"
        (casa / ".claude").mkdir(parents=True)
        env = dict(os.environ, HOME=str(casa), USERPROFILE=str(casa), CLAUDE_CONFIG_DIR=str(casa / ".claude"),
                   ARTURO_RADICE=str(casa / ".claude"), PYTHONIOENCODING="utf-8", PYTHONDONTWRITEBYTECODE="1")
        p = subprocess.run([sys.executable, "-c", FIGLIO, str(repo.resolve() / "bin")], capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=60, env=env, cwd=tmp)
    try:
        rossi = json.loads(p.stdout.strip().splitlines()[-1])
    except (IndexError, ValueError):
        # Un processo caduto non è il rosso di un caso: un veleno che lo fa cadere non prova il suo caso.
        return [f"CADUTO il processo di prova: {(p.stdout + p.stderr)[-300:]!r}"]
    return [r for r in rossi if not solo or r.startswith(solo)]


# (caso, file, testo giusto, testo rotto): ogni veleno toglie la riga che il caso sorveglia.
VELENI = [
    ("WM01", "bin/aggiornamenti.py", '        if SERVIZI_CLAUDE.match(" ".join(argomenti.split()[1:])):\n',
     '        if SERVIZI_CLAUDE.search(" ".join(argomenti.split()[1:])):\n'),
    ("WM01", "bin/aggiornamenti.py", 'SERVIZI_CLAUDE = re.compile(r"(?:daemon run|bg-spare --bg-spare|bg-pty-host --bg-pty-host)(?=\\s|$)")',
     'SERVIZI_CLAUDE = re.compile(r"(?:daemon|bg-spare|bg-pty-host)(?=\\s|$)")'),
    ("WM02", "bin/segnala.py", '    if programma == "clip":\n', '    if False:\n'),
    ("WM02", "bin/segnala.py", 'input=testo_appunti(testo, comando[0]), timeout=10)', 'input=testo, text=True, timeout=10)'),
    ("WM03", "bin/sessione.py", 'prompt.replace(";", "\\\\;")], a_mano', 'prompt], a_mano'),
    ("WM04", "bin/impostazioni.py", '            flusso.reconfigure(encoding="utf-8")', '            pass'),
    ("WM04", "bin/unisci-settings.py", '            flusso.reconfigure(encoding="utf-8")', '            pass'),
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
            if not rossi or rossi[0].startswith("CADUTO"):
                print(f"VELENO {caso} NON ATTACCA ({rel}): {rossi[:1]}")
                return 1
            print(f"VELENO {caso} ROSSO: {rossi[0][:120]}")
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
    codici = {r.split()[0] for r in rossi}
    verdi = 0 if "CADUTO" in codici else len([c for c in CASI if c not in codici])
    print(f"difetti minori su Windows: {verdi}/{len(CASI)} casi verdi")
    return 1 if rossi else 0


if __name__ == "__main__":
    sys.exit(main())
