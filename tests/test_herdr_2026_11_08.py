#!/usr/bin/env python3
"""HZ01-HZ07: Herdr, la finestra di Arturo (8/11/2026, ramo di prova `herdr`).

/setup installa Herdr (herdr.dev) con `shared/herdr/installa-herdr.sh`, e l'hook `hooks/herdr-stato.sh`
dice a Herdr se Claude lavora, aspetta la persona o ha finito (OSC 7501). Il banco prova l'installazione
in una casa finta con un installer finto, senza rete e senza Herdr vero.

HZ01 primo giro: Herdr scaricato, layout, tema e mod copiati, arturo.json punta al bin di Arturo,
     shared.json apre il layout Arturo senza il benvenuto di Herdr, telemetria di Herdr spenta.
HZ02 secondo giro su una casa già usata: un tasto della persona resta suo, la sua telemetria e il suo
     shared.json restano com'erano, e il giro dopo non cambia niente.
HZ03 Mac Intel e Linux: esce 0 con `HERDR NO` e non scrive niente.
HZ04 hook: fuori da Herdr non scrive; dentro Herdr scrive `ESC]7501;state=<s>:app=claude-code ESC\\`
     sul terminale di controllo.
HZ05 settings.json registra l'hook sugli otto eventi con lo stato giusto, e la telemetria della deriva
     lo conosce.
HZ06 /setup porta a shared/setup-herdr.md, che lancia installa-herdr.sh.
HZ07 il mod: ogni modulo importato esiste, ogni parte nominata dal layout esiste in main.js.

Con --avvelena cinque copie rotte del repository devono far rosso il caso che le sorveglia.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

CASI = ("HZ01", "HZ02", "HZ03", "HZ04", "HZ05", "HZ06", "HZ07")
INSTALLA = Path("shared/herdr/installa-herdr.sh")
HOOK = Path("hooks/herdr-stato.sh")
ATTESI = {  # evento: (matcher o None, stato)
    "SessionStart": ("", "idle"),
    "UserPromptSubmit": (None, "working"),
    "PermissionRequest": (None, "blocked"),
    "Notification": ("permission_prompt|elicitation_dialog", "blocked"),
    "PreToolUse": ("AskUserQuestion", "blocked"),
    "PostToolUse": (None, "working"),
    "Stop": (None, "done"),
    "SessionEnd": ("", "idle"),
}


def installa(repo: Path, casa: Path, sistema: str = "mac-arm") -> subprocess.CompletedProcess:
    app = casa / "app"
    segno = casa / "scaricato"
    finto = casa / "installer-finto.sh"
    finto.write_text(f"#!/bin/sh\necho scaricato >> '{segno}'\n", encoding="utf-8")
    env = {
        **os.environ,
        "HOME": str(casa / "home"),
        "USERPROFILE": str(casa / "home"),
        "HERDR_APP_HOME": str(app),
        "PROJECTS_BASE": str(casa / "progetti"),
        "ARTURO_HERDR_INSTALLER": str(finto),
        "ARTURO_HERDR_SISTEMA": sistema,
        "ARTURO_HERDR_NON_APRIRE": "1",
        "ARTURO_HERDR_VERSIONE": "0.1.13",
    }
    (casa / "home").mkdir(parents=True, exist_ok=True)
    return subprocess.run(["sh", str(repo / INSTALLA)], env=env, capture_output=True, text=True, timeout=60)


def leggi(p: Path):
    return json.loads(p.read_text(encoding="utf-8"))


def hz01(repo: Path, casa: Path) -> str | None:
    r = installa(repo, casa)
    app = casa / "app"
    if r.returncode != 0 or "HERDR OK" not in r.stdout:
        return f"installazione fallita rc={r.returncode}: {(r.stdout + r.stderr)[-200:]}"
    if not (casa / "scaricato").exists():
        return "l'installer di Herdr non è partito"
    for rel in ("layouts/arturo.json", "layouts/arturo.svg", "themes/arturo.json", "mods/arturo/main.js", "mods/arturo/dati.js", "mods/arturo/fonts"):
        if not (app / rel).exists():
            return f"manca {rel}"
    conf = leggi(app / "arturo.json")
    if not conf["arturo"][-1].endswith("bin/arturo") or Path(conf["arturo"][-1]).resolve() != (repo / "bin/arturo").resolve():
        return f"arturo.json non punta al bin di Arturo: {conf['arturo']}"
    if conf["base"] != str(casa / "progetti"):
        return f"arturo.json ignora PROJECTS_BASE: {conf['base']}"
    sh = leggi(app / "shared.json")
    if sh.get("layout") != "arturo" or sh.get("frame.welcomed") != "skipped":
        return f"il primo avvio non apre il layout Arturo: {sh}"
    if leggi(app / "update-notes.json").get("presented") != ["0.1.13"]:
        return "le note di versione di Herdr si aprirebbero al primo avvio"
    if leggi(app / "settings.json").get("telemetry") is not False:
        return "la telemetria di Herdr non è spenta"
    return None


def hz02(repo: Path, casa: Path) -> str | None:
    app = casa / "app"
    app.mkdir(parents=True)
    (app / "keys.json").write_text('{"global": {"cmd-o": "tab.new"}}', encoding="utf-8")
    (app / "settings.json").write_text('{"telemetry": true, "zoom": 1.2}', encoding="utf-8")
    (app / "shared.json").write_text('{"layout": "main"}', encoding="utf-8")
    r = installa(repo, casa)
    if r.returncode != 0:
        return f"installazione fallita: {r.stderr[-200:]}"
    if leggi(app / "keys.json")["global"].get("cmd-o") != "tab.new":
        return "un tasto della persona è stato sovrascritto"
    if "agent.next" not in leggi(app / "keys.json")["global"].values():
        return "i tasti di Arturo non sono stati aggiunti"
    imp = leggi(app / "settings.json")
    if imp.get("telemetry") is not True or imp.get("zoom") != 1.2:
        return f"le impostazioni della persona sono cambiate: {imp}"
    if leggi(app / "shared.json") != {"layout": "main"}:
        return "lo stato di Herdr della persona è stato riscritto"
    prima = {p.name: p.read_bytes() for p in app.glob("*.json")}
    installa(repo, casa)
    dopo = {p.name: p.read_bytes() for p in app.glob("*.json")}
    if prima != dopo:
        return f"il secondo giro cambia {sorted(k for k in dopo if prima.get(k) != dopo[k])}"
    return None


def hz03(repo: Path, casa: Path) -> str | None:
    for sistema in ("mac-intel", "linux"):
        c = casa / sistema
        c.mkdir()
        r = installa(repo, c, sistema)
        if r.returncode != 0 or "HERDR NO" not in r.stdout:
            return f"{sistema}: rc={r.returncode} {r.stdout[-120:]}"
        if (c / "app").exists() or (c / "scaricato").exists():
            return f"{sistema}: ha scritto o scaricato qualcosa"
    return None


def nel_terminale(repo: Path, env: dict) -> bytes:
    """L'hook lanciato con un terminale di controllo finto: restituisce quello che vi ha scritto.
    Il lato madre si legge mentre l'hook gira: su macOS una scrittura sul terminale aspetta chi legge."""
    import pty
    import select
    madre, figlia = pty.openpty()
    codice = (
        "import os,fcntl,termios,subprocess,sys;"
        "os.setsid();fcntl.ioctl(0,termios.TIOCSCTTY,0);"
        f"subprocess.run(['sh',{str(repo / HOOK)!r},'working'],input=b'{{}}',stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)"
    )
    p = subprocess.Popen([sys.executable, "-c", codice], stdin=figlia, stdout=figlia, stderr=subprocess.PIPE, env=env, close_fds=True)
    os.close(figlia)
    letto = b""
    fine = __import__("time").time() + 20
    while __import__("time").time() < fine:
        pronti = select.select([madre], [], [], 0.2)[0]
        if pronti:
            try:
                pezzo = os.read(madre, 4096)
            except OSError:
                break
            if not pezzo:
                break
            letto += pezzo
        elif p.poll() is not None:
            break
    p.kill() if p.poll() is None else None
    p.wait(timeout=5)
    os.close(madre)
    return letto


def hz04(repo: Path, casa: Path) -> str | None:
    if os.name == "nt":
        return None  # niente pty su Windows: il caso vale su macOS e Linux
    fuori = {k: v for k, v in os.environ.items() if k != "HC_TERMINAL_ID"}
    if b"7501" in nel_terminale(repo, fuori):
        return "fuori da Herdr l'hook scrive sul terminale"
    dentro = {**fuori, "HC_TERMINAL_ID": "t1"}
    letto = nel_terminale(repo, dentro)
    if b"\x1b]7501;state=working:app=claude-code\x1b\\" not in letto:
        return f"dentro Herdr l'hook non scrive lo stato: {letto[:80]!r}"
    return None


def hz05(repo: Path, casa: Path) -> str | None:
    hooks = leggi(repo / "settings.json")["hooks"]
    for evento, (matcher, stato) in ATTESI.items():
        trovati = [g for g in hooks.get(evento, []) for h in g.get("hooks", []) if "herdr-stato.sh" in h.get("command", "")]
        if not trovati:
            return f"{evento} senza herdr-stato.sh"
        comandi = [h["command"] for g in trovati for h in g["hooks"] if "herdr-stato.sh" in h["command"]]
        if not any(c.endswith(f" {stato}") for c in comandi):
            return f"{evento} non manda {stato}: {comandi}"
        if matcher is not None and not any(g.get("matcher", "") == matcher for g in trovati):
            return f"{evento} col matcher sbagliato"
    logica = (repo / "server/logica.js").read_text(encoding="utf-8")
    elenco = re.search(r"DERIVA_HOOK = \[(.*?)\];", logica, re.S)
    if not elenco or '"herdr-stato.sh"' not in elenco.group(1):
        return "DERIVA_HOOK non conosce herdr-stato.sh"
    return None


def hz06(repo: Path, casa: Path) -> str | None:
    setup = (repo / "commands/setup.md").read_text(encoding="utf-8")
    if "shared/setup-herdr.md" not in setup:
        return "/setup non porta a shared/setup-herdr.md"
    passo = (repo / "shared/setup-herdr.md").read_text(encoding="utf-8")
    if "shared/herdr/installa-herdr.sh" not in passo:
        return "setup-herdr.md non lancia installa-herdr.sh"
    for parola in ("HERDR OK", "HERDR NO", "HERDR ERRORE"):
        if parola not in passo or (parola != "HERDR ERRORE" and parola not in (repo / INSTALLA).read_text(encoding="utf-8")):
            return f"l'esito {parola} non torna fra passo e script"
    return None


def hz07(repo: Path, casa: Path) -> str | None:
    mod = repo / "shared/herdr/mods/arturo"
    for js in mod.glob("*.js"):
        for rel in re.findall(r'from "\./([^"]+)"', js.read_text(encoding="utf-8")):
            if not (mod / rel).exists():
                return f"{js.name} importa {rel}, che non c'è"
    main = (mod / "main.js").read_text(encoding="utf-8")
    parti = set(re.findall(r"(\w+): \w+", re.search(r"const PARTI = \{(.*?)\};", main).group(1)))
    layout = (repo / "shared/herdr/layouts/arturo.json").read_text(encoding="utf-8")
    usate = set(re.findall(r'"parte": "(\w+)"', layout)) | set(re.findall(r'parte: "(\w+)"', " ".join(p.read_text(encoding="utf-8") for p in mod.glob("*.js"))))
    if usate - parti:
        return f"parti senza codice: {sorted(usate - parti)}"
    return None


PROVE = {"HZ01": hz01, "HZ02": hz02, "HZ03": hz03, "HZ04": hz04, "HZ05": hz05, "HZ06": hz06, "HZ07": hz07}


def prova(repo: Path) -> list[str]:
    rossi = []
    for codice, f in PROVE.items():
        with tempfile.TemporaryDirectory() as tmp:
            try:
                motivo = f(repo, Path(tmp))
            except Exception as e:  # un caso che si rompe è rosso, non ferma gli altri
                motivo = f"eccezione {type(e).__name__}: {e}"
        if motivo:
            rossi.append(f"{codice} {motivo}")
    return rossi


VELENI = [
    ("HZ01", "shared/herdr/installa-herdr.sh", '"frame.welcomed": "skipped"', '"frame.welcomed": "finished"'),
    ("HZ02", "shared/herdr/installa-herdr.sh", "if k in mia and mia[k] != v:", "if False:"),
    ("HZ03", "shared/herdr/installa-herdr.sh", 'Arturo funziona lo stesso nel Terminale."; exit 0 ;;', 'Arturo funziona lo stesso nel Terminale." ;;'),
    ("HZ04", "hooks/herdr-stato.sh", '[ -n "${HC_TERMINAL_ID:-}" ] || exit 0', ":"),
    ("HZ05", "settings.json", "herdr-stato.sh done", "herdr-stato.sh idle"),
]


def avvelena(repo: Path) -> int:
    esiti = []
    for caso, rel, giusto, rotto in VELENI:
        with tempfile.TemporaryDirectory() as tmp:
            copia = Path(tmp) / "repo"
            shutil.copytree(repo, copia, ignore=shutil.ignore_patterns(".git", "__pycache__", "node_modules", "cache"))
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
    repo = Path(argomenti.repo).resolve()
    if argomenti.avvelena:
        return avvelena(repo)
    if argomenti.baseline_ref:
        print("BASELINE_DISCRIMINANTE=nessuna (banco nuovo: il veleno lo prova con --avvelena)")
        return 0
    rossi = prova(repo)
    for r in rossi:
        print("ROSSO", r)
    print(f"herdr: {len(CASI) - len({r.split()[0] for r in rossi})}/{len(CASI)} casi verdi")
    return 1 if rossi else 0


if __name__ == "__main__":
    raise SystemExit(main())
