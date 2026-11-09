#!/usr/bin/env python3
"""HZ01-HZ15: Herdr, la finestra di Arturo (8/11/2026, ramo di prova `herdr`).

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
HZ06 /setup porta a shared/setup-herdr.md, che lancia installa-herdr.sh. Sul Mac senza l'identità "Arturo firma
     locale" l'installatore propone firma-locale.sh con la riga HERDR FIRMA, e il passo dice cosa farne (#5020).
HZ07 il mod: ogni modulo importato esiste, ogni parte nominata dal layout esiste in main.js.
HZ08 chi ha già Arturo (setup fatto) e non ha Herdr riceve all'avvio l'invito `HERDR:` una volta sola;
     chi non ha finito /setup non lo riceve.
HZ09 i suggerimenti della finestra puntano a cose che esistono: ogni comando slash a un file di
     commands/, "Trova i miei progetti" a trova-progetti.md, che usa la parte 2c del ritratto e i
     sottocomandi veri di ritratto.py.
HZ10 "Da dove partire" in cima al pannello Da fare (partenza.js, con node): il todo di da_dove col motivo,
     poi al massimo tre passi della catena dopo di lui, senza i todo segnati fatti; niente scheda senza
     da_dove o col todo già fatto. Senza node il caso si salta.
HZ11 "La settimana" (settimana.js, con node): ogni progetto in una lista sola, la più urgente (scaduti,
     poi aspettano te, poi fermi da più di sette giorni), ognuna dal caso peggiore, col motivo che dice
     tutti i fatti; un progetto senza niente da guardare resta fuori. La settimana ISO regge il cambio
     d'anno. La finestra è una parte di main.js e il piede la apre. Senza node il caso si salta.
HZ12 le azioni sui todo del pannello Da fare (azioni.js, con node): ogni gesto del menu e "Aggiungi"
     girano sulla CLI vera in una casa finta e lasciano il todo come promettono (chi, quando, fermo col
     motivo, ripreso, nota, scartato, fatto); il menu non propone il chi e il quando che il todo ha già,
     né "Fermo" a un todo fermo; un titolo vuoto non aggiunge niente. Lavoraci (#4994) segna il todo
     in corso prima di aprire Claude, non riscrive un todo già in corso, e il menu lo rimette da fare.
     Menu e finestra sono parti di main.js. Senza node il caso si salta.
HZ13 Arturo.app (arturo-app.sh, solo macOS, #5002): da un Herdr.app finto nasce Arturo.app col nome, l'id e
     l'icona di Arturo e la firma locale valida; il secondo giro non la tocca; dopo un aggiornamento che le
     ridà il nome di Herdr torna Arturo alla versione nuova; un Herdr.app più nuovo la rifà; il LaunchAgent
     guarda i due Info.plist. L'installatore la chiama solo sul Mac e solo senza installer finto. Fuori da
     macOS resta solo il controllo sull'installatore.
HZ14 le note sulla finestra (⌘⇧N, nota.js con node): la nota porta testo, punto, misura della finestra e
     progetto; diventa una cosa da fare di Claude per oggi, con punto e cartella nelle note, sulla CLI vera
     in una casa finta; vuota non parte; senza progetto resta nella cartella; note_progetto vince sul
     progetto aperto. barra.js fa lo screenshot prima del velo, keys.json lega cmd-shift-n, main.js ha la
     parte, l'installatore tiene note_progetto in arturo.json. Senza node la parte con node si salta.
HZ15 ogni cartella o file che la parte Herdr scrive in ~/.claude/data/ (mod, hook herdr-stato.sh, invito di
     session-start.sh) è escluso dal .gitignore di Arturo (#5018): uno screenshot delle note fermava
     l'aggiornamento automatico o finiva in un commit di /fine.
HZ16 servizi-gui.sh (9/11/2026): herdr-core da LaunchAgent senza KeepAlive (si passa da solo a
     launchd ed esce 0); il gestore delle sessioni non va in launchd senza --launchd (senza l'accesso
     a Documenti le sessioni morirebbero all'avvio), con --launchd sì e con KeepAlive; plist validi.

Con --avvelena ventuno copie rotte del repository devono far rosso il caso che le sorveglia.
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

CASI = ("HZ01", "HZ02", "HZ03", "HZ04", "HZ05", "HZ06", "HZ07", "HZ08", "HZ09", "HZ10", "HZ11", "HZ12", "HZ13", "HZ14", "HZ15", "HZ16")
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


def installa(repo: Path, casa: Path, sistema: str = "mac-arm", extra: dict | None = None) -> subprocess.CompletedProcess:
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
        **(extra or {}),
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
    # #5020: la firma locale si propone con una riga e il comando, e lo script è eseguibile come gli altri.
    if "HERDR FIRMA" not in passo:
        return "setup-herdr.md non dice cosa fare con la riga HERDR FIRMA"
    if not os.access(repo / "shared/herdr/firma-locale.sh", os.X_OK):
        return "firma-locale.sh non è eseguibile"
    for firma, attesa in (("assente", True), ("presente", False)):
        with tempfile.TemporaryDirectory() as d:
            r = installa(repo, Path(d), extra={"ARTURO_HERDR_FIRMA": firma})
        riga = next((x for x in r.stdout.splitlines() if x.startswith("HERDR FIRMA")), "")
        if attesa and "firma-locale.sh" not in riga:
            return "senza la firma locale l'installatore non propone firma-locale.sh"
        if not attesa and riga:
            return "con la firma locale già fatta l'installatore la propone lo stesso"
    with tempfile.TemporaryDirectory() as d:
        if "HERDR FIRMA" in installa(repo, Path(d), "windows", {"ARTURO_HERDR_FIRMA": "assente"}).stdout:
            return "l'installatore propone la firma locale fuori dal Mac"
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


def hz08(repo: Path, casa: Path) -> str | None:
    if os.name == "nt":
        return None  # sysctl e i percorsi del Mac: il caso vale fuori da Windows
    if sys.platform == "darwin":
        r = subprocess.run(["sysctl", "-n", "hw.optional.arm64"], capture_output=True, text=True)
        if r.stdout.strip() != "1":
            return None
    elif not sys.platform.startswith("linux"):
        return None
    if sys.platform.startswith("linux"):
        return None  # su Linux l'invito non parte: niente da provare qui
    env = {**os.environ, "HOME": str(casa), "USERPROFILE": str(casa), "PATH": "/usr/bin:/bin:/usr/sbin:/sbin",
           "ARTURO_BANCHI_AVVIO": "0", "ARTURO_AGGIORNAMENTI": "manuali"}
    def avvio() -> str:
        r = subprocess.run(["bash", str(repo / "hooks/session-start.sh")], env=env, capture_output=True, text=True,
                           timeout=60, stdin=subprocess.DEVNULL)
        return r.stdout
    (casa / ".claude/data").mkdir(parents=True)
    if "HERDR:" in avvio():
        return "invito a chi non ha finito /setup"
    (casa / ".claude/data/setup-fatto").write_text("2026-11-08\n", encoding="utf-8")
    primo, secondo = avvio(), avvio()
    if primo.count("HERDR:") != 1:
        return "chi ha già Arturo non riceve l'invito a Herdr"
    if "HERDR:" in secondo:
        return "l'invito a Herdr torna a ogni avvio"
    return None


def hz09(repo: Path, casa: Path) -> str | None:
    dati = (repo / "shared/herdr/mods/arturo/dati.js").read_text(encoding="utf-8")
    blocco = re.search(r"export const SUGGERIMENTI = \[(.*?)\n\];", dati, re.S)
    if not blocco:
        return "SUGGERIMENTI non trovato in dati.js"
    prompt = re.findall(r'prompt: "([^"]+)"', blocco.group(1))
    for p in prompt:
        if p.startswith("/"):
            nome = p[1:].split()[0]
            if not (repo / "commands" / f"{nome}.md").exists():
                return f"il suggerimento {p} non ha un comando in commands/"
        for rel in re.findall(r"~/\.claude/([\w./-]+\.md)", p):
            if not (repo / rel).exists():
                return f"il suggerimento rimanda a {rel}, che non c'è"
    trova = (repo / "shared/herdr/trova-progetti.md").read_text(encoding="utf-8")
    ritratto = (repo / "shared/setup-ritratto.md").read_text(encoding="utf-8")
    if "2c. Le cartelle" not in trova or "## 2c. Le cartelle" not in ritratto:
        return "trova-progetti.md non usa la parte 2c del ritratto"
    sotto = set(re.findall(r'add_parser\("(\w+)"', (repo / "bin/ritratto.py").read_text(encoding="utf-8")))
    if not {"cartelle", "scan"} <= sotto:
        return f"ritratto.py non ha più cartelle e scan: {sorted(sotto)}"
    if "arturo todo stato --progetto" not in trova:
        return "trova-progetti.md non scrive la riga di stato dei progetti nuovi"
    return None


PROVA_PARTENZA = r"""
import { partenza } from %s;
const t = (id) => ({ id, titolo: "todo " + id });
const vista = (da, catena) => ({ gruppi: [{ tipo: "io", todo: [1, 2, 3, 4, 5, 6, 7].map(t) }],
  progetti: [{ nome: "p", catena, da_dove: da ? { id: da, motivo: "Sblocca #3" } : null }] });
const forma = (r) => r && { id: r.todo.id, motivo: r.motivo, poi: r.poi.map((x) => x.id) };
console.log(JSON.stringify([
  forma(partenza(vista(2, [1, 2, 3, 4, 5, 6]))),
  forma(partenza(vista(2, [1, 2, 3, 4, 5, 6]), new Set([3]))),
  forma(partenza(vista(null, [1, 2]))),
  forma(partenza(vista(2, [2, 3]), new Set([2]))),
  forma(partenza(vista(7, [1, 2]))),
  forma(partenza(null)),
]));
"""


def hz10(repo: Path, casa: Path) -> str | None:
    node = shutil.which("node")
    if not node:
        return None
    copia = casa / "partenza.mjs"  # .mjs: senza package.json node leggerebbe il .js come CommonJS
    shutil.copyfile(repo / "shared/herdr/mods/arturo/partenza.js", copia)
    modulo = copia.as_uri()
    r = subprocess.run([node, "--input-type=module", "-e", PROVA_PARTENZA % json.dumps(modulo)],
                       capture_output=True, text=True, timeout=30)
    if r.returncode != 0:
        return f"partenza.js non gira: {(r.stderr or r.stdout).strip()[:160]}"
    atteso = [{"id": 2, "motivo": "Sblocca #3", "poi": [3, 4, 5]}, {"id": 2, "motivo": "Sblocca #3", "poi": [4, 5, 6]},
              None, None, {"id": 7, "motivo": "Sblocca #3", "poi": []}, None]
    avuto = json.loads(r.stdout.strip().splitlines()[-1])
    for n, (a, b) in enumerate(zip(atteso, avuto), 1):
        if a != b:
            return f"caso {n}: atteso {a}, avuto {b}"
    return None


PROVA_SETTIMANA = r"""
import { revisione, settimanaDi } from %s;
const t = (progetto, giorni) => ({ progetto, giorni });
const vista = {
  gruppi: [{ tipo: "tu", todo: [t("a", -3), t("a", -20), t("b", 2), t("c", -1)] }],
  progetti: [
    { nome: "a", chiedono_te: 4, eta_gg: 15 },
    { nome: "b", chiedono_te: 1, eta_gg: 2 },
    { nome: "c", chiedono_te: 0, eta_gg: null },
    { nome: "d", chiedono_te: 9, eta_gg: 1 },
    { nome: "e", chiedono_te: 0, eta_gg: 8 },
    { nome: "f", chiedono_te: 0, eta_gg: 7 },
    { nome: "g", chiedono_te: 0, eta_gg: 30 },
  ],
};
const r = revisione(vista);
const forma = (l) => l.map((v) => [v.progetto.nome, v.motivo]);
console.log(JSON.stringify({ scaduti: forma(r.scaduti), te: forma(r.te), fermi: forma(r.fermi),
  settimane: ["2026-11-08", "2026-11-09", "2021-01-03", "2024-12-30", "x"].map(settimanaDi) }));
"""


def hz11(repo: Path, casa: Path) -> str | None:
    mod = repo / "shared/herdr/mods/arturo"
    main = (mod / "main.js").read_text(encoding="utf-8")
    if "settimana: Settimana" not in main or 'from "./revisione.js"' not in main:
        return "main.js non ha la parte settimana"
    if "apriRevisione()" not in (mod / "barra.js").read_text(encoding="utf-8"):
        return "barra.js non apre La settimana"
    node = shutil.which("node")
    if not node:
        return None
    copia = casa / "settimana.mjs"
    shutil.copyfile(mod / "settimana.js", copia)
    r = subprocess.run([node, "--input-type=module", "-e", PROVA_SETTIMANA % json.dumps(copia.as_uri())],
                       capture_output=True, text=True, timeout=30)
    if r.returncode != 0:
        return f"settimana.js non gira: {(r.stderr or r.stdout).strip()[:160]}"
    avuto = json.loads(r.stdout.strip().splitlines()[-1])
    atteso = {
        "scaduti": [["a", "2 todo scaduti, il più vecchio da 20 giorni · 4 todo aspettano te · ultimo punto 15 giorni fa"],
                    ["c", "1 todo scaduto da 1 giorno"]],
        "te": [["d", "9 todo aspettano te"], ["b", "1 todo aspetta te"]],
        "fermi": [["g", "Ultimo punto 30 giorni fa"], ["e", "Ultimo punto 8 giorni fa"]],
        "settimane": ["2026-W45", "2026-W46", "2020-W53", "2025-W01", ""],
    }
    for k, v in atteso.items():
        if avuto.get(k) != v:
            return f"{k}: atteso {v}, avuto {avuto.get(k)}"
    return None


PROVA_AZIONI = r"""
import { azioni, aggiungi, fatto, inizia } from %s;
import { readFileSync } from "fs";
const righe = JSON.parse(readFileSync(%s, "utf-8"));
const testo = "perché sì";
console.log(JSON.stringify({
  aggiungi: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map((n) => aggiungi({ titolo: `  prova   ${n} `, progetto: "prova", chi: "io", quando: "oggi" })?.argv),
  vuoto: aggiungi({ titolo: "   ", progetto: "prova" }),
  righe: righe.map((t) => ({ id: t.id, voci: Object.fromEntries(azioni(t).map((v) => [v.id, v.argv(testo)])), fatto: fatto(t).argv, inizia: inizia(t)?.argv ?? null })),
}));
"""

# Per ogni todo di prova (in ordine) il gesto da fare e cosa deve lasciare: campo, valore.
GESTI = [("chi-tu", "chi", "tu"), ("chi-decidi", "chi", "decidi"), ("quando-settimana", "quando", "settimana"),
         ("quando-più avanti", "quando", "più avanti"), ("ferma", "motivo", "perché sì"), ("nota", "note", ["perché sì"]),
         ("scarta", "stato", "scartato"), ("fatto", "stato", "fatto"), ("ferma", "stato", "fermo")]


def hz12(repo: Path, casa: Path) -> str | None:
    mod = repo / "shared/herdr/mods/arturo"
    main = (mod / "main.js").read_text(encoding="utf-8")
    if "azioni: Azioni" not in main or "nuovo: Nuovo" not in main:
        return "main.js non ha le parti azioni e nuovo"
    pannello = (mod / "todo.js").read_text(encoding="utf-8")
    if "apriMenu(item)" not in pannello:
        return "il pannello Da fare non apre il menu delle azioni"
    # Lavoraci, nella riga e nella scheda in cima, segna il todo in corso prima di aprire Claude.
    corpo = pannello.split("  lavoraci(item, cx) {", 1)[-1].split("\n  }\n", 1)[0]
    if pannello.count("this.lavoraci(item, cx)") != 2 or "const g = inizia(item);" not in corpo \
            or corpo.find("todo(g.argv)") > corpo.find("await apri(progetto, scelto)"):
        return "Lavoraci non segna il todo in corso prima di aprire Claude"
    node = shutil.which("node")
    if not node:
        return None
    copia = casa / "azioni.mjs"
    shutil.copyfile(mod / "azioni.js", copia)
    env = {**os.environ, "HOME": str(casa), "USERPROFILE": str(casa), "ARTURO_TODO": str(casa / "eventi.jsonl"),
           "ARTURO_OGGI": "2026-11-08"}

    def cli(argv):
        return subprocess.run([sys.executable, str(repo / "bin/arturo"), "todo", *argv], capture_output=True,
                              text=True, timeout=60, env=env, cwd=casa)

    def gesti(righe):
        (casa / "righe.json").write_text(json.dumps(righe), encoding="utf-8")
        r = subprocess.run([node, "--input-type=module", "-e", PROVA_AZIONI % (json.dumps(copia.as_uri()),
                            json.dumps(str(casa / "righe.json")))], capture_output=True, text=True, timeout=30)
        if r.returncode != 0:
            raise RuntimeError(f"azioni.js non gira: {(r.stderr or r.stdout).strip()[:160]}")
        return json.loads(r.stdout.strip().splitlines()[-1])

    def mostra(n):
        return json.loads(cli(["mostra", str(n), "--json"]).stdout)

    g = gesti([])
    if g["vuoto"] is not None:
        return "un titolo vuoto aggiunge un todo"
    for argv in g["aggiungi"]:
        r = cli(argv)
        if r.returncode != 0:
            return f"Aggiungi non va sulla CLI: {argv} → {(r.stderr or r.stdout).strip()[:120]}"
    righe = [mostra(n) for n in range(1, len(GESTI) + 1)]
    if [(t["titolo"], t["chi"], t["quando"]) for t in righe[:1]] != [("prova 1", "io", "oggi")]:
        return f"Aggiungi non scrive titolo, chi e quando: {righe[0]}"
    voci = gesti(righe)["righe"]
    if any(k in voci[0]["voci"] for k in ("chi-io", "quando-oggi", "riprendi")):
        return f"il menu propone quello che il todo ha già: {sorted(voci[0]['voci'])}"
    for (gesto, campo, valore), riga in zip(GESTI, voci):
        argv = riga["fatto"] if gesto == "fatto" else riga["voci"][gesto]
        r = cli(argv)
        if r.returncode != 0:
            return f"il gesto {gesto} non va sulla CLI: {argv} → {(r.stderr or r.stdout).strip()[:120]}"
        avuto = mostra(riga["id"]).get(campo)
        if avuto != valore:
            return f"il gesto {gesto} lascia {campo} = {avuto!r}, atteso {valore!r}"
    fermo = mostra(len(GESTI))
    voci = gesti([fermo])["righe"][0]["voci"]
    if "ferma" in voci or "riprendi" not in voci:
        return f"a un todo fermo il menu propone {sorted(voci)}"
    r = cli(voci["riprendi"])
    if r.returncode != 0 or mostra(len(GESTI))["stato"] != "da fare":
        return f"Riprendi non riapre il todo fermo: {(r.stderr or r.stdout).strip()[:120]}"
    # Lavoraci: il todo passa in corso, non si riscrive se lo è già, e il menu lo rimette da fare.
    n = len(GESTI) + 1
    r = cli(gesti([mostra(n)])["righe"][0]["inizia"])
    if r.returncode != 0 or mostra(n)["stato"] != "in corso":
        return f"Lavoraci non segna il todo in corso: {mostra(n)['stato']} {(r.stderr or r.stdout).strip()[:120]}"
    corso = gesti([mostra(n)])["righe"][0]
    if corso["inizia"] is not None:
        return "Lavoraci riscrive un todo già in corso"
    if "riprendi" not in corso["voci"] or "ferma" not in corso["voci"]:
        return f"a un todo in corso il menu propone {sorted(corso['voci'])}"
    r = cli(corso["voci"]["riprendi"])
    if r.returncode != 0 or mostra(n)["stato"] != "da fare":
        return f"il menu non rimette da fare un todo in corso: {(r.stderr or r.stdout).strip()[:120]}"
    return None


def hz13(repo: Path, casa: Path) -> str | None:
    installa_sh = (repo / INSTALLA).read_text(encoding="utf-8")
    if 'sh "$qui/arturo-app.sh" --agente' not in installa_sh \
            or '[ -z "${ARTURO_HERDR_INSTALLER:-}" ] && [ -d "$HOME/Applications/Herdr.app" ]' not in installa_sh:
        return "l'installatore non crea Arturo.app sul Mac, o la crea anche nei banchi"
    if sys.platform != "darwin":
        return None
    import plistlib

    def app(dove: Path, nome: str, versione: str, ident: str) -> None:
        (dove / "Contents/MacOS").mkdir(parents=True, exist_ok=True)
        (dove / "Contents/Resources").mkdir(parents=True, exist_ok=True)
        eseg = dove / "Contents/MacOS/Herdr"
        eseg.write_text("#!/bin/sh\necho herdr\n", encoding="utf-8")
        eseg.chmod(0o755)
        with open(dove / "Contents/Info.plist", "wb") as f:
            plistlib.dump({"CFBundleName": nome, "CFBundleDisplayName": nome, "CFBundleIdentifier": ident,
                           "CFBundleExecutable": "Herdr", "CFBundleIconFile": "Herdr", "CFBundlePackageType": "APPL",
                           "CFBundleShortVersionString": versione}, f)

    herdr, arturo, agenti = casa / "Applications/Herdr.app", casa / "Applications/Arturo.app", casa / "agenti"
    env = {**os.environ, "ARTURO_HERDR_APP": str(herdr), "ARTURO_APP": str(arturo), "ARTURO_APP_AGENTI": str(agenti),
           "ARTURO_APP_NO_LAUNCHCTL": "1", "ARTURO_APP_FIRMA": "adhoc"}

    def giro(*arg):
        return subprocess.run(["sh", str(repo / "shared/herdr/arturo-app.sh"), *arg], capture_output=True,
                              text=True, timeout=60, env=env)

    def arturo_ok(versione):
        with open(arturo / "Contents/Info.plist", "rb") as f:
            i = plistlib.load(f)
        avuto = (i.get("CFBundleName"), i.get("CFBundleIdentifier"), i.get("CFBundleShortVersionString"))
        if avuto != ("Arturo", "org.stellakamikaze.arturo", versione):
            return f"Arturo.app ha {avuto}, attesa Arturo {versione}"
        if not (arturo / "Contents/Resources/Arturo.icns").exists():
            return "Arturo.app senza icona"
        v = subprocess.run(["codesign", "--verify", "--deep", "--strict", str(arturo)], capture_output=True, text=True)
        return f"firma di Arturo.app non valida: {v.stderr.strip()[:120]}" if v.returncode else None

    app(herdr, "Herdr", "0.1.13", "dev.herdr.app")
    r = giro("--agente")
    if r.returncode != 0:
        return f"arturo-app.sh esce {r.returncode}: {(r.stderr or r.stdout).strip()[:160]}"
    if (m := arturo_ok("0.1.13")):
        return m
    with open(agenti / "org.stellakamikaze.arturo-app.plist", "rb") as f:
        guarda = plistlib.load(f).get("WatchPaths", [])
    if sorted(guarda) != sorted([str(herdr / "Contents/Info.plist"), str(arturo / "Contents/Info.plist")]):
        return f"il LaunchAgent non guarda i due Info.plist: {guarda}"
    prima = (arturo / "Contents/Info.plist").stat().st_mtime_ns
    if "già a posto" not in giro().stdout or (arturo / "Contents/Info.plist").stat().st_mtime_ns != prima:
        return "il secondo giro rifà Arturo.app"
    shutil.rmtree(arturo)
    app(arturo, "Herdr", "0.1.14", "dev.herdr.app")  # l'aggiornamento fatto da dentro Arturo.app
    giro()
    if (m := arturo_ok("0.1.14")):
        return f"dopo l'aggiornamento: {m}"
    shutil.rmtree(herdr)
    app(herdr, "Herdr", "0.1.15", "dev.herdr.app")  # Herdr.app aggiornato dall'installer
    giro()
    if (m := arturo_ok("0.1.15")):
        return f"con Herdr.app più nuovo: {m}"
    return None


PROVA_NOTA = r"""
import { nota, cartellaNota, progettoNota } from %s;
const base = { x: 412.6, y: 233.2, larghezza: 1440, altezza: 900, cartella: "/casa/.claude/data/note-finestra/x", schermo: "Ricette", quando: "2026-11-09T09:00:00Z" };
console.log(JSON.stringify({
  piena: nota({ ...base, testo: "  Il   pulsante è troppo piccolo ", progetto: "prova" }),
  vuota: nota({ ...base, testo: "   ", progetto: "prova" }),
  senza: nota({ ...base, testo: "ciao", progetto: null }),
  cartella: cartellaNota("/casa", new Date(2026, 10, 9, 9, 5, 7)),
  scelto: progettoNota("arturo", "ricette"), aperto: progettoNota(null, "ricette"),
}));
"""


def hz14(repo: Path, casa: Path) -> str | None:
    mod = repo / "shared/herdr/mods/arturo"
    if "nota: Nota" not in (mod / "main.js").read_text(encoding="utf-8"):
        return "main.js non ha la parte nota"
    if json.loads((repo / "shared/herdr/keys.json").read_text(encoding="utf-8")).get("global", {}).get("cmd-shift-n") != "arturo.nota":
        return "keys.json non lega cmd-shift-n alle note"
    barra = (mod / "barra.js").read_text(encoding="utf-8")
    corpo = barra.split("async function apriNota() {", 1)[-1].split("\n}\n", 1)[0]
    if 'else if (c === "nota") await apriNota();' not in barra or corpo.find(" shot ") < 0 or corpo.find(" shot ") > corpo.find("openOverlay("):
        return "barra.js non fa lo screenshot prima di aprire il velo delle note"
    if 'arturo = leggi("arturo.json") or {}' not in (repo / INSTALLA).read_text(encoding="utf-8"):
        return "l'installatore riscrive arturo.json perdendo note_progetto"
    node = shutil.which("node")
    if not node:
        return None
    copia = casa / "nota.mjs"
    shutil.copyfile(mod / "nota.js", copia)
    r = subprocess.run([node, "--input-type=module", "-e", PROVA_NOTA % json.dumps(copia.as_uri())],
                       capture_output=True, text=True, timeout=30)
    if r.returncode != 0:
        return f"nota.js non gira: {(r.stderr or r.stdout).strip()[:160]}"
    g = json.loads(r.stdout.strip().splitlines()[-1])
    if g["vuota"] is not None:
        return "una nota vuota parte lo stesso"
    if g["senza"]["argv"] is not None or g["senza"]["dati"]["testo"] != "ciao":
        return "senza progetto la nota non resta solo nella cartella"
    d = g["piena"]["dati"]
    if (d["testo"], d["punto"], d["finestra"], d["progetto"], d["screenshot"]) != (
            "Il pulsante è troppo piccolo", {"x": 413, "y": 233}, {"larghezza": 1440, "altezza": 900}, "prova", "finestra.png"):
        return f"nota.json non porta testo, punto, finestra e progetto: {d}"
    if g["cartella"] != "/casa/.claude/data/note-finestra/2026-11-09_09-05-07":
        return f"cartella della nota sbagliata: {g['cartella']}"
    if (g["scelto"], g["aperto"]) != ("arturo", "ricette"):
        return "il progetto delle note non preferisce note_progetto al progetto aperto"
    env = {**os.environ, "HOME": str(casa), "USERPROFILE": str(casa), "ARTURO_TODO": str(casa / "eventi.jsonl"),
           "ARTURO_OGGI": "2026-11-09"}
    r = subprocess.run([sys.executable, str(repo / "bin/arturo"), "todo", *g["piena"]["argv"]], capture_output=True,
                       text=True, timeout=60, env=env, cwd=casa)
    if r.returncode != 0:
        return f"la nota non va sulla CLI: {(r.stderr or r.stdout).strip()[:160]}"
    t = json.loads(subprocess.run([sys.executable, str(repo / "bin/arturo"), "todo", "mostra", "1", "--json"],
                                  capture_output=True, text=True, timeout=60, env=env, cwd=casa).stdout)
    if (t["chi"], t["quando"], t["progetto"]) != ("io", "oggi", "prova") or not t["titolo"].startswith("Nota sulla finestra: Il pulsante"):
        return f"la nota non diventa una cosa da fare di Claude per oggi: {t['chi']} {t['quando']} {t['progetto']} {t['titolo']}"
    if not any("note-finestra/x" in n and "413,233" in n for n in t.get("note", [])):
        return f"la cosa da fare non porta punto e cartella nelle note: {t.get('note')}"
    return None


def scritti_in_data(repo: Path) -> set[str]:
    """I nomi sotto ~/.claude/data/ che la parte Herdr scrive: mod, hook di stato e invito all'avvio."""
    fonti = [f for f in (repo / "shared/herdr").rglob("*") if f.is_file() and f.suffix in (".js", ".sh", ".py")]
    fonti.append(repo / "hooks/herdr-stato.sh")
    testi = [f.read_text(encoding="utf-8") for f in fonti]
    testi += [r for r in (repo / "hooks/session-start.sh").read_text(encoding="utf-8").splitlines() if "herdr" in r]
    return {m for testo in testi for m in re.findall(r"\.claude/data/([A-Za-z0-9_.-]+)", testo)}


def hz15(repo: Path, casa: Path) -> str | None:
    nomi = scritti_in_data(repo)
    if not {"note-finestra", "herdr-invito"} <= nomi:
        return f"il banco non trova più le scritture in data/: {sorted(nomi)}"
    prova_git = casa / "git"
    prova_git.mkdir()
    shutil.copyfile(repo / ".gitignore", prova_git / ".gitignore")
    subprocess.run(["git", "init", "-q"], cwd=prova_git, check=True)
    fuori = []
    for nome in sorted(nomi):
        # Una cartella si prova con un file dentro, un file col suo nome: check-ignore risponde 0 se è escluso.
        forme = (f"data/{nome}/x/nota.json", f"data/{nome}")
        if not any(subprocess.run(["git", "check-ignore", "-q", "--no-index", rel], cwd=prova_git).returncode == 0
                   for rel in forme):
            fuori.append(f"data/{nome}")
    return f".gitignore non esclude {', '.join(fuori)}" if fuori else None


def hz16(repo: Path, casa: Path) -> str | None:
    if sys.platform != "darwin":
        return None
    bin_ = casa / ".local" / "bin"
    bin_.mkdir(parents=True)
    for nome in ("claude", "herdr-core"):
        (bin_ / nome).write_text("#!/bin/sh\n")
        (bin_ / nome).chmod(0o755)
    agenti = casa / "agenti"
    env = dict(os.environ, HOME=str(casa), SERVIZI_AGENTI=str(agenti), SERVIZI_NO_LAUNCHCTL="1")
    script = repo / "shared" / "herdr" / "servizi-gui.sh"

    def leggi(nome: str) -> dict | None:
        f = agenti / f"org.stellakamikaze.arturo.{nome}.plist"
        if not f.exists():
            return None
        r = subprocess.run(["plutil", "-convert", "json", "-o", "-", str(f)], capture_output=True, text=True)
        return json.loads(r.stdout) if r.returncode == 0 else {"rotto": r.stderr}

    r = subprocess.run(["sh", str(script)], env=env, capture_output=True, text=True)
    if r.returncode:
        return f"servizi-gui.sh esce {r.returncode}: {r.stderr.strip()[-200:]}"
    core = leggi("herdr-core")
    if not core or core.get("KeepAlive") is not False or core.get("ProgramArguments", [])[-1:] != ["serve"]:
        return f"herdr-core: plist mancante, rotto o con KeepAlive: {core}"
    if leggi("claude-daemon") is not None:
        return "senza --launchd il gestore delle sessioni non deve stare in launchd"
    r = subprocess.run(["sh", str(script), "--launchd"], env=env, capture_output=True, text=True)
    gestore = leggi("claude-daemon")
    if r.returncode or not gestore or gestore.get("KeepAlive") is not True or gestore.get("ProgramArguments", [])[1:] != ["daemon", "run"]:
        return f"--launchd: gestore mancante o sbagliato: {gestore}"
    return None


PROVE = {"HZ01": hz01, "HZ02": hz02, "HZ03": hz03, "HZ04": hz04, "HZ05": hz05, "HZ06": hz06, "HZ07": hz07, "HZ08": hz08, "HZ09": hz09, "HZ10": hz10, "HZ11": hz11, "HZ12": hz12, "HZ13": hz13, "HZ14": hz14, "HZ15": hz15, "HZ16": hz16}


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
    ("HZ09", "shared/herdr/mods/arturo/dati.js", 'prompt: "/guidami"', 'prompt: "/guidamii"'),
    ("HZ10", "shared/herdr/mods/arturo/partenza.js", "catena.slice(qui + 1)", "catena.slice(qui)"),
    ("HZ11", "shared/herdr/mods/arturo/settimana.js", "else if (te) liste.te.push", "if (te) liste.te.push"),
    ("HZ12", "shared/herdr/mods/arturo/azioni.js", "if (quando === t.quando) continue;", ""),
    ("HZ12", "shared/herdr/mods/arturo/azioni.js", 'argv: ["inizia"', 'argv: ["riprendi"'),
    ("HZ12", "shared/herdr/mods/arturo/todo.js", "const g = inizia(item);", "const g = null;"),
    ("HZ14", "shared/herdr/mods/arturo/nota.js", "if (!t) return null;", ""),
    ("HZ14", "shared/herdr/mods/arturo/nota.js", '"--chi", "io"', '"--chi", "tu"'),
    ("HZ13", "shared/herdr/arturo-app.sh", '-c "Set :CFBundleIdentifier $ID"', '-c "Set :CFBundleIdentifier dev.herdr.app"'),
    ("HZ13", "shared/herdr/arturo-app.sh", 'if [ -d "$arturo" ] && { [ ! -d "$herdr" ] || ! piu_nuova "$v_herdr" "$v_arturo"; }; then base=$arturo; fi', ":"),
    ("HZ06", "shared/herdr/installa-herdr.sh", '[ "$firma" = assente ]', '[ "$firma" = mai ]'),
    ("HZ16", "shared/herdr/servizi-gui.sh", "plist herdr-core false", "plist herdr-core true"),
    ("HZ16", "shared/herdr/servizi-gui.sh", 'rm -f "$agenti/$PREFISSO.claude-daemon.plist"', 'plist claude-daemon true "$claude" daemon run'),
    ("HZ15", ".gitignore", "data/note-finestra/\n", ""),
    ("HZ15", ".gitignore", "data/herdr-invito\n", ""),
    ("HZ08", "hooks/session-start.sh", 'mkdir -p "$HOME/.claude/data" && date +%Y-%m-%d > "$HOME/.claude/data/herdr-invito"', ":"),
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
