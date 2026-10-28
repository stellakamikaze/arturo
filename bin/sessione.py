"""arturo sessione: apre una finestra nuova del terminale con Claude già partito su un progetto.

Nasce dal Computer Club N.3 (27/10/2026): "slash cosa da fare... clicco e vado avanti". Il pannello
/dafare lo lancia col tasto o sulla riga scelta. Il prompt è sempre /inizio <progetto>, con il titolo
del todo dopo "--" quando c'è un todo: il titolo si legge dall'archivio per numero, mai da un testo
passato da fuori.

Il terminale cambia col sistema, e il comando passa sempre come argv:
- macOS: Terminal, con osascript e il comando come argomento (mai dentro l'AppleScript);
- Windows: Windows Terminal (wt) se c'è, altrimenti una finestra di cmd con start;
- Linux: gnome-terminal, konsole o x-terminal-emulator, il primo che trova.
Senza terminale stampa il comando da lanciare a mano e lo copia negli appunti.

Solo libreria standard, Python 3.8 o successivo.
"""
from __future__ import annotations

import json
import os
import re
import shlex
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(os.path.realpath(__file__)).parent))
import contesto  # noqa: E402
import todo_store as ts  # noqa: E402

AIUTO = """arturo sessione: una finestra nuova del terminale con Claude già partito su un progetto.

  arturo sessione PROGETTO               apre /inizio PROGETTO
  arturo sessione --todo ID              apre /inizio sul progetto del todo, col suo titolo
  --stampa                               scrive il comando senza aprire niente

Lo usa il pannello /dafare (tasto o)."""

SLUG = re.compile(r"^[a-z0-9][a-z0-9-]{0,63}$")
# Caratteri che cmd di Windows legge anche dentro le virgolette, e le virgolette stesse: dal titolo
# di un todo si tolgono, perché il prompt deve arrivare a claude così com'è.
SPORCHI = re.compile(r'["%^`\x00-\x1f\x7f]')


def sistema() -> str:
    """darwin, windows o linux. ARTURO_SISTEMA lo finge, solo per i banchi."""
    finto = os.environ.get("ARTURO_SISTEMA", "")
    if finto in ("darwin", "windows", "linux"):
        return finto
    if sys.platform == "darwin":
        return "darwin"
    return "windows" if os.name == "nt" else "linux"


def prompt_per(progetto: str, todo: dict | None) -> str:
    if not todo:
        return f"/inizio {progetto}"
    titolo = " ".join(SPORCHI.sub(" ", str(todo.get("titolo", ""))).split())[:200]
    return f"/inizio {progetto} -- #{todo['id']} {titolo}".rstrip()


def cartella() -> Path:
    """La cartella dei progetti, come per la pagina dafare personale: /inizio poi entra nel progetto."""
    base = contesto.base_progetti()
    return base if base.is_dir() else Path.home()


def comando(sis: str, dove: Path, prompt: str) -> tuple:
    """(argv da lanciare, riga da scrivere a mano). argv vuoto: nessun terminale trovato."""
    a_mano = f"cd {shlex.quote(str(dove))} && claude {shlex.quote(prompt)}"
    if sis == "darwin":
        script = ["on run argv", 'tell application "Terminal"', "do script (item 1 of argv)", "activate",
                  "end tell", "end run"]
        argv = ["osascript"]
        for riga in script:
            argv += ["-e", riga]
        return argv + [a_mano], a_mano
    if sis == "windows":
        a_mano = f'cd /d "{dove}" && claude "{prompt}"'
        if shutil.which("wt"):
            return ["wt", "-d", str(dove), "claude", prompt], a_mano
        return ["cmd", "/c", "start", "", "/d", str(dove), "claude", prompt], a_mano
    for nome, argv in (("gnome-terminal", ["gnome-terminal", f"--working-directory={dove}", "--", "claude", prompt]),
                       ("konsole", ["konsole", "--workdir", str(dove), "-e", "claude", prompt]),
                       ("x-terminal-emulator", ["x-terminal-emulator", "-e", "claude", prompt])):
        if shutil.which(nome):
            return argv, a_mano
    return [], a_mano


def _copia(testo: str) -> bool:
    import segnala
    return segnala._copia(testo)


def main(argv: list) -> int:
    if not argv or argv[0] in ("-h", "--help", "aiuto", "help"):
        print(AIUTO)
        return 0 if argv else 2
    progetto, numero, stampa = "", None, False
    resto = list(argv)
    while resto:
        voce = resto.pop(0)
        if voce == "--stampa":
            stampa = True
        elif voce == "--todo" and resto:
            numero = resto.pop(0)
        elif voce.startswith("--todo="):
            numero = voce.split("=", 1)[1]
        elif not voce.startswith("-") and not progetto:
            progetto = voce
        else:
            print(f"Errore: argomento non previsto: {voce}\n\n{AIUTO}", file=sys.stderr)
            return 2

    todo = None
    if numero is not None:
        todo_map, _ = ts.carica()
        todo = ts.per_id(todo_map, numero)
        progetto = progetto or todo["progetto"]
    progetto = contesto.slug(progetto)
    if not SLUG.match(progetto):
        print("Errore: serve il nome di un progetto (lettere, numeri e trattini) oppure --todo ID.", file=sys.stderr)
        return 2

    prompt = prompt_per(progetto, todo)
    dove = cartella()
    argv_terminale, a_mano = comando(sistema(), dove, prompt)
    if stampa:
        print(json.dumps({"argv": argv_terminale, "a_mano": a_mano, "prompt": prompt}, ensure_ascii=False))
        return 0
    if not shutil.which("claude"):
        print("Non trovo il comando claude: scrivi /diagnosi in una sessione aperta.", file=sys.stderr)
        return 1
    if argv_terminale:
        try:
            subprocess.Popen(argv_terminale, cwd=str(dove), stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                             stderr=subprocess.DEVNULL, start_new_session=True)
            print(f"Aperta una sessione nuova: {prompt}")
            return 0
        except OSError:
            pass
    copiato = _copia(a_mano)
    print("Non riesco ad aprire un terminale. " + ("Il comando è negli appunti: " if copiato else "Lancia questo: ")
          + a_mano)
    return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
