#!/usr/bin/env python3
"""A01-A05: la deriva parla la stessa lingua in tre posti.

hooks/deriva.py produce i valori, bin/telemetria.py li lascia partire, server/logica.js li accetta.
Le tre regex sono copie a mano, e due copie a mano divergono (pattern dei segreti, 3/10/2026). Se
deriva.py aggiunge una radice e telemetria.py no, `registra()` ha già messo in coda `insieme:<n>` e
manda meno righe di n: il server ricostruisce un elenco incompleto, senza errori.
Questo banco confronta il contenuto delle copie, non solo i nomi degli eventi (M09).
Veleno: --avvelena aggiunge una radice a deriva.py e il banco deve diventare rosso su A02.
"""
from __future__ import annotations

import importlib.util
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

H = Path(sys.argv[sys.argv.index("--repo") + 1] if "--repo" in sys.argv else Path(__file__).resolve().parent.parent)


def carica(nome: str, percorso: Path):
    spec = importlib.util.spec_from_file_location(nome, percorso)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


deriva = carica("deriva", H / "hooks" / "deriva.py")
telemetria = carica("telemetria", H / "bin" / "telemetria.py")
radici = list(deriva.RADICI)
if "--avvelena" in sys.argv:
    radici.append("radice-avvelenata")

logica = (H / "server" / "logica.js").read_text(encoding="utf-8")


def js(evento: str) -> str:
    m = re.search(r"^\s*" + evento + r": /(.+)/,\s*$", logica, re.M)
    return m.group(1).replace(r"\/", "/") if m else ""


def radici_in(sorgente: str) -> set:
    m = re.search(r"\(\(([a-z|\\.-]+)\)/", sorgente)
    return {r.replace("\\.", ".") for r in m.group(1).split("|")} if m else set()


def alternative(sorgente: str) -> set:
    m = re.search(r"rotta-\(([a-z|]+)\)", sorgente)
    return set(m.group(1).split("|")) if m else set()


# Radici tolte dal client che il server accetta ancora: un client non aggiornato le manda, e il
# server rifiuterebbe il lotto intero. Escono dal server con l'evento tappa, dopo il 13/11 (#3435).
RADICI_VECCHIE = {"templates"}

py_deriva = telemetria.EVENTI["deriva"].pattern
js_deriva = js("deriva")
js_attuale = js_deriva
for vecchia in RADICI_VECCHIE:
    js_attuale = js_attuale.replace("|" + vecchia + "|", "|")
rossi = []
CASI = ["A01", "A02", "A03", "A04", "A05"]

# A01: la regex di telemetria.py e quella del server sono la stessa stringa, a parte le radici vecchie.
if not js_deriva or py_deriva != js_attuale:
    rossi.append(f"A01 deriva diversa fra bin/telemetria.py e server/logica.js:\n  py {py_deriva}\n  js {js_deriva}")

# A02: le radici dei file sono le stesse in deriva.py, telemetria.py e server.
for dove, sorgente in (("bin/telemetria.py", py_deriva), ("server/logica.js", js_attuale)):
    if radici_in(sorgente) != set(radici):
        rossi.append(f"A02 radici di {dove} {sorted(radici_in(sorgente))} diverse da hooks/deriva.py {sorted(radici)}")

# A03: la parte `file:` e la parte `hook:` di telemetria.py coincidono con FILE e HOOK di deriva.py.
corpo_file = deriva.FILE.pattern[1:-1]
caratteri_hook = re.search(r"\(\[(.+?)\]\{1,60\}\)", deriva.HOOK.pattern)
if "file:" + corpo_file not in py_deriva:
    rossi.append(f"A03 la parte file: di telemetria.py non è FILE di deriva.py: {corpo_file}")
if not caratteri_hook or f"hook:[{caratteri_hook.group(1)}]{{1,60}}" not in py_deriva:
    rossi.append(f"A03 la parte hook: di telemetria.py non è HOOK di deriva.py: {deriva.HOOK.pattern}")

# A04: le categorie di config rotta sono le stesse in deriva.py, telemetria.py e server.
cat_deriva = set(re.findall(r'"rotta-([a-z]+)"', (H / "hooks" / "deriva.py").read_text(encoding="utf-8")))
cat_py = alternative(telemetria.EVENTI["config"].pattern)
cat_js = alternative(js("config"))
if not cat_deriva or not (cat_deriva == cat_py == cat_js):
    rossi.append(f"A04 categorie config diverse: deriva.py {sorted(cat_deriva)} · telemetria.py {sorted(cat_py)} · server {sorted(cat_js)}")


# A05: categorie_config() riconosce i messaggi veri di controlla-config.py, non solo settings.
def git(cartella: str, *argomenti) -> None:
    subprocess.run(["git", "-C", cartella, *argomenti], check=True, capture_output=True,
                   env={**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"})


with tempfile.TemporaryDirectory() as tmp:
    attese = {}
    rebase = os.path.join(tmp, "rebase")
    os.makedirs(rebase)
    git(rebase, "init", "-q")
    Path(rebase, "a.txt").write_text("a\n", encoding="utf-8")
    git(rebase, "add", "a.txt")
    git(rebase, "commit", "-q", "-m", "a")
    git_dir = subprocess.run(["git", "-C", rebase, "rev-parse", "--git-dir"], capture_output=True, text=True).stdout.strip()
    os.makedirs(os.path.join(rebase, git_dir, "rebase-merge"))
    attese[rebase] = ["rotta-rebase"]

    conflitto = os.path.join(tmp, "conflitto")
    os.makedirs(conflitto)
    git(conflitto, "init", "-q")
    Path(conflitto, "b.md").write_text("<<<<<<< HEAD\nx\n=======\ny\n>>>>>>> altro\n", encoding="utf-8")
    git(conflitto, "add", "b.md")
    git(conflitto, "commit", "-q", "-m", "b")
    attese[conflitto] = ["rotta-conflitto"]

    # Uno script di hook citato e assente: python3 esce con 2 e su PreToolUse blocca ogni azione.
    hook = os.path.join(tmp, "hook")
    os.makedirs(os.path.join(hook, "hooks"))
    Path(hook, "hooks", "presente.py").write_text("", encoding="utf-8")
    Path(hook, "settings.json").write_text(json.dumps({"hooks": {"PreToolUse": [{"matcher": "Bash", "hooks": [
        {"type": "command", "command": "python3 ~/.claude/hooks/presente.py"},
        {"type": "command", "command": "python3 $HOME/.claude/hooks/sparito.py"}]}]}}), encoding="utf-8")
    attese[hook] = ["rotta-hook"]

    for cartella, attesa in attese.items():
        trovate = deriva.categorie_config(Path(cartella))
        if trovate != attesa:
            rossi.append(f"A05 {os.path.basename(cartella)}: categorie_config dà {trovate}, attese {attesa}")

for r in rossi:
    print("ROSSO", r)
print(f"deriva allineata: {len(CASI) - len({r[:3] for r in rossi})}/{len(CASI)} casi verdi")
sys.exit(1 if rossi else 0)
