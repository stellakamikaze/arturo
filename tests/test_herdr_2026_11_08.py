#!/usr/bin/env python3
"""HZ01-HZ30: Herdr, la finestra di Arturo (8/11/2026, ramo di prova `herdr`).

/setup installa Herdr (herdr.dev) con `shared/volta-celeste/installa-herdr.sh`, e l'hook `hooks/herdr-stato.sh`
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
     guarda i due Info.plist e lancia la copia dello script fuori da Documenti (#5087). L'installatore la chiama solo sul Mac e solo senza installer finto. Fuori da
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
HZ17 Volta Celeste, i gruppi (sessioni.js con node, #5068): per macchina nell'ordine del file con la nota
     della macchina giù; per progetto con "Senza progetto" in fondo; dentro il gruppo ti aspetta >
     errore > lavora > ferma; i nomi automatici ("claudecode-ca") lasciano il posto alla risposta.
HZ18 Volta Celeste, il clic (sessioni.js con node): una sessione in background si aggancia con l'argv
     del file (locale o ssh), un'interattiva ferma passa da porta-volta, una al lavoro, che aspetta o di
     una macchina giù no, col motivo; la scheda già aperta si riconosce anche dall'argv avvolto da zsh
     da un ciclo ssh dentro sh -c e da pwsh -Command su Windows, senza prendere un id che ne contiene un altro.
HZ19 Volta Celeste nella barra: barra.js monta volta.js e accetta il comando volta-<id>, volta.js
     lancia teletrasporto.py volta --scrivi e porta-volta, e senza teletrasporto.py non mostra niente.
HZ20 Volta Celeste su Windows (9/11/2026): volta.js lancia teletrasporto.py col Python di arturo.json
     (quello che installa-herdr.sh ha trovato), mai con un Python scritto a mano.
HZ21 installa-herdr.sh su Windows scrive layout, mod e arturo.json in ~/.config/herdr-app e la shell
     di herdr-core in ~/.config/herdr-core/config.toml, dove Herdr 0.1.14 li legge; niente in %APPDATA%.
HZ22 i tasti per sistema: su Windows keys-ctrl.json (Ctrl+Shift+A apre un progetto, Ctrl+Shift+M la nota)
     e nessun cmd, che lì è il tasto Windows; sui Mac keys.json con cmd-o.
HZ23 l'installatore prende il primo Python che risponde, non il primo che esiste: con un python3 che esce
     9009 come lo stub dello Store, arturo.json usa python (#5079).
HZ24 barra di stato e guida scrivono i tasti da tasti() di comuni.js, mai ⌘ a mano; volta.js avvisa se
     il comando do porta l'id di una sessione che non è nell'elenco (#5078).
HZ25 nelle finestre di dialogo (Cosa posso chiedere, Apri un progetto, La settimana, menu dei todo)
     l'azione parte prima che la finestra si chiuda: chiusa, la finestra ferma il suo codice al primo
     await, e i pulsanti di Cosa posso chiedere non facevano niente (9/11/2026).
HZ26 su cosa è una nota (#5117 passo 1, nota.js con node): regione() rifà i rettangoli di
     layouts/arturo.json con le misure prese nell'istanza di prova (finestra 1440x900, barra 292, lavoro
     1147) e dice la parte sotto il punto, anche con barra e pannello allargati, col pannello nascosto e col
     benvenuto; con misure vecchie o assenti dà null. main.js fa riportare la misura alle parti del layout,
     notaui.js mette la parte e il terminale in nota.json. Senza node la parte con node si salta.
HZ27 il velo delle note (#5117 passo 2, nota.js con node): nota.json versione 2 con id, numero, tipo, stato,
     filo e todo; una nota versione 1 si legge come aperta; i segni delle note aperte del progetto hanno
     numeri unici e si riportano in scala sulla finestra; risposta e chiusura passano nel filo; lo script
     LEGGI_NOTE legge la cartella col Python; la CLI vera dà l'id del todo con --json. notaui.js riscrive
     nota.json solo se è ancora quello letto e porta Risolta e Scarta sul todo. Senza node la parte con node
     si salta.
HZ28 l'elenco delle note (#5117 passo 3, nota.js con node): prima le aperte coi numeri dei segni, con
     "tutte" anche le chiuse dalla più recente e senza numero; ultima risposta di Claude, età in parole,
     conteggio per progetto; una risposta nuova di Claude si annuncia, ma non alla prima lettura. ⌘⇧E sui
     Mac e Ctrl+Shift+E altrove aprono la parte `note`; la barra di stato guarda la cartella delle note e
     il suo conteggio apre l'elenco; una riga aperta porta al velo con arturo.nota-<id>.
HZ29 il giro di Claude con `arturo note` (#5117 passo 4, CLI vera in una casa finta): elenco coi numeri dei
     segni (una nota versione 1 prende il primo libero), --md come brief, mostra col ritaglio attorno al
     punto in scala sullo scatto al doppio, prendi, rispondi e risolvi che portano il todo in corso, nota e
     fatto; una nota chiusa non si richiude, scarta chiude col motivo, un percorso al posto dell'id esce 2.
HZ30 scrittura concorrente: se il velo scrive fra la lettura e la scrittura della CLI, la CLI rilegge e
     rifà la sua modifica, e nel filo restano tutte e due le risposte.

Con --avvelena le copie rotte del repository devono far rosso il caso che le sorveglia.
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

CASI = ("HZ01", "HZ02", "HZ03", "HZ04", "HZ05", "HZ06", "HZ07", "HZ08", "HZ09", "HZ10", "HZ11", "HZ12", "HZ13", "HZ14", "HZ15", "HZ16", "HZ17", "HZ18", "HZ19", "HZ20", "HZ21", "HZ22", "HZ23", "HZ24", "HZ25", "HZ26", "HZ27", "HZ28", "HZ29", "HZ30")
INSTALLA = Path("shared/volta-celeste/installa-herdr.sh")
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
    # su Windows installa-herdr.sh scrive C:/... con le barre dritte (cygpath -m): si confrontano i percorsi
    if Path(conf["base"]).resolve() != (casa / "progetti").resolve():
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
    if "shared/volta-celeste/installa-herdr.sh" not in passo:
        return "setup-herdr.md non lancia installa-herdr.sh"
    for parola in ("HERDR OK", "HERDR NO", "HERDR ERRORE"):
        if parola not in passo or (parola != "HERDR ERRORE" and parola not in (repo / INSTALLA).read_text(encoding="utf-8")):
            return f"l'esito {parola} non torna fra passo e script"
    # #5020: la firma locale si propone con una riga e il comando, e lo script è eseguibile come gli altri.
    if "HERDR FIRMA" not in passo:
        return "setup-herdr.md non dice cosa fare con la riga HERDR FIRMA"
    if not os.access(repo / "shared/volta-celeste/firma-locale.sh", os.X_OK):
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
    mod = repo / "shared/volta-celeste/mods/arturo"
    for js in mod.glob("*.js"):
        for rel in re.findall(r'from "\./([^"]+)"', js.read_text(encoding="utf-8")):
            if not (mod / rel).exists():
                return f"{js.name} importa {rel}, che non c'è"
    main = (mod / "main.js").read_text(encoding="utf-8")
    parti = set(re.findall(r"(\w+): \w+", re.search(r"const PARTI = \{(.*?)\};", main).group(1)))
    layout = (repo / "shared/volta-celeste/layouts/arturo.json").read_text(encoding="utf-8")
    # [^"]+ e non \w+: un nome col trattino o col punto non deve sparire dal controllo
    usate = set(re.findall(r'"parte": "([^"]+)"', layout)) | set(re.findall(r'parte: "([^"]+)"'," ".join(p.read_text(encoding="utf-8") for p in mod.glob("*.js"))))
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
    dati = (repo / "shared/volta-celeste/mods/arturo/dati.js").read_text(encoding="utf-8")
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
    trova = (repo / "shared/volta-celeste/trova-progetti.md").read_text(encoding="utf-8")
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
    shutil.copyfile(repo / "shared/volta-celeste/mods/arturo/partenza.js", copia)
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
    mod = repo / "shared/volta-celeste/mods/arturo"
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
    mod = repo / "shared/volta-celeste/mods/arturo"
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
    copia = casa / "Library/Application Support/Arturo/arturo-app"
    env = {**os.environ, "ARTURO_HERDR_APP": str(herdr), "ARTURO_APP": str(arturo), "ARTURO_APP_AGENTI": str(agenti),
           "ARTURO_APP_COPIA": str(copia), "ARTURO_APP_NO_LAUNCHCTL": "1", "ARTURO_APP_FIRMA": "adhoc"}

    def giro(*arg):
        return subprocess.run(["sh", str(repo / "shared/volta-celeste/arturo-app.sh"), *arg], capture_output=True,
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
        agente = plistlib.load(f)
    guarda = agente.get("WatchPaths", [])
    # launchd non legge Documenti: l'agente lancia la copia fuori dal repository, con l'icona accanto (#5087).
    lancia = agente.get("ProgramArguments", [])
    if lancia != ["/bin/sh", str(copia / "arturo-app.sh")]:
        return f"il LaunchAgent non lancia la copia fuori dal repository: {lancia}"
    if not (copia / "arturo-icona.svg").exists() \
            or (copia / "arturo-app.sh").read_bytes() != (repo / "shared/volta-celeste/arturo-app.sh").read_bytes():
        return "la copia per il LaunchAgent manca o non è uguale allo script del repository"
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
    mod = repo / "shared/volta-celeste/mods/arturo"
    if "nota: Nota" not in (mod / "main.js").read_text(encoding="utf-8"):
        return "main.js non ha la parte nota"
    if json.loads((repo / "shared/volta-celeste/keys.json").read_text(encoding="utf-8")).get("global", {}).get("cmd-shift-n") != "arturo.nota":
        return "keys.json non lega cmd-shift-n alle note"
    barra = (mod / "barra.js").read_text(encoding="utf-8")
    # apriNota sta in comuni.js dal passo 3 di #5117: la usano la barra e l'elenco delle note.
    corpo = (mod / "comuni.js").read_text(encoding="utf-8").split("export async function apriNota(apri = null) {", 1)[-1].split("\n}\n", 1)[0]
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
    fonti = [f for f in (repo / "shared/volta-celeste").rglob("*") if f.is_file() and f.suffix in (".js", ".sh", ".py")]
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
    script = repo / "shared" / "volta-celeste" / "servizi-gui.sh"

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


PROVA_VOLTA = r"""
import * as v from %s;
const ADESSO = Date.parse("2026-11-09T18:00:00Z");
const r = (o) => ({ macchina: "MacBook Air", host: "macbook", questa: true, tipo: "background", stato: "ferma", ultimo: "", risposta: "", progetto: null, attach: ["claude", "attach", o.id], ...o });
const dati = {
  macchine: [{ macchina: "MacBook Air", host: "macbook", questa: true }, { macchina: "Amaltea", host: "amaltea", questa: false },
             { macchina: "Balthasar", host: "balthasar", questa: false, irraggiungibile: "timeout" }],
  sessioni: [
    r({ id: "a1", nome: "uno", stato: "ferma", ultimo: "2026-11-09T15:00:00Z", progetto: "arturo" }),
    r({ id: "a2", nome: "due", stato: "lavora", progetto: "arturo" }),
    r({ id: "a3", nome: "claudecode-ca", tipo: "interattiva", attach: null, risposta: "**Fatto:** il deck è pronto\nresto", stato: "aspetta" }),
    r({ id: "b1", nome: "tre", host: "amaltea", macchina: "Amaltea", questa: false, stato: "errore", progetto: "due-mondi", attach: ["ssh", "-t", "amaltea", ".local/bin/claude", "attach", "b1"] }),
    r({ id: "b2", nome: "quattro", host: "amaltea", macchina: "Amaltea", questa: false, stato: "ferma", progetto: "arturo" }),
  ],
};
const forma = (gs) => gs.map((g) => [g.titolo, g.nota ?? "", g.sessioni.map((s) => s.id)]);
const s = (id) => dati.sessioni.find((x) => x.id === id);
console.log(JSON.stringify({
  macchina: forma(v.gruppi(dati, "macchina")),
  progetto: forma(v.gruppi(dati, "progetto")),
  titoli: ["a1", "a3"].map((id) => v.titolo(s(id))),
  quanto: [v.daQuanto("2026-11-09T17:56:00Z", ADESSO), v.daQuanto("2026-11-09T15:00:00Z", ADESSO), v.daQuanto("2026-11-07T18:00:00Z", ADESSO), v.daQuanto("", ADESSO)],
  dettaglio: [v.dettaglio(s("a1"), "macchina", ADESSO).testo, v.dettaglio(s("b1"), "progetto", ADESSO).testo],
  clic: [
    v.clic(s("a1")), v.clic(s("b1")), v.clic({ ...s("a3"), stato: "ferma" }), v.clic(s("a3")).azione,
    v.clic({ ...s("a3"), stato: "lavora" }).azione, v.clic({ ...s("a1"), vecchia: true }).azione, v.clic({ ...s("a1"), attach: null }).azione,
  ],
  aggancio: [v.agganciata(["/bin/zsh", "-lic", "x", "/bin/zsh", "ssh", "-t", "amaltea", ".local/bin/claude", "attach", "b1"], s("b1")),
             v.agganciata(["claude", "attach", "zz"], s("b1")), v.agganciata(undefined, s("b1")),
             v.agganciata(["/bin/zsh", "-lic", "x", "/bin/zsh", "sh", "-c", "while :; do ssh -t amaltea .local/bin/claude attach b1; [ $? -eq 255 ] || break; done"], s("b1")),
             v.agganciata(["sh", "-c", "ssh amaltea claude attach b10"], s("b1")), v.agganciata(["sh", "-c", "echo b1"], s("b1")),
             v.agganciata(["pwsh.exe", "-NoExit", "-Command", "& 'C:\\\\Windows\\\\System32\\\\OpenSSH\\\\ssh.exe' '-t' 'amaltea' '.local/bin/claude' 'attach' 'b1'"], s("b1"))],
}));
"""


def volta_node(repo: Path, casa: Path) -> dict | str | None:
    node = shutil.which("node")
    if not node:
        return None
    copia = casa / "sessioni.mjs"
    shutil.copyfile(repo / "shared/volta-celeste/mods/arturo/sessioni.js", copia)
    r = subprocess.run([node, "--input-type=module", "-e", PROVA_VOLTA % json.dumps(copia.as_uri())],
                       capture_output=True, text=True, timeout=30)
    if r.returncode != 0:
        return f"sessioni.js non gira: {(r.stderr or r.stdout).strip()[:160]}"
    return json.loads(r.stdout.strip().splitlines()[-1])


def hz17(repo: Path, casa: Path) -> str | None:
    avuto = volta_node(repo, casa)
    if not isinstance(avuto, dict):
        return avuto
    atteso = {
        "macchina": [["MacBook Air", "", ["a3", "a2", "a1"]], ["Amaltea", "", ["b1", "b2"]], ["Balthasar", "Non risponde", []]],
        "progetto": [["Senza progetto", "Balthasar non risponde", ["a3"]]],
        "titoli": ["uno", "Fatto: il deck è pronto"],
        "quanto": ["da 4 min", "da 3 ore", "da 2 giorni", ""],
        "dettaglio": ["Arturo · Ferma da 3 ore", "Amaltea · Si è fermata con un errore"],
    }
    gp = avuto.get("progetto", [])
    if [g[0] for g in gp] != ["Due mondi", "Arturo", "Senza progetto"]:
        return f"progetto: ordine dei gruppi {[g[0] for g in gp]}, atteso Due mondi, Arturo, Senza progetto"
    if gp[1][2] != ["a2", "a1", "b2"]:
        return f"progetto: dentro Arturo {gp[1][2]}, atteso lavora prima delle ferme"
    for k, v in atteso.items():
        a = avuto.get(k)
        if k == "progetto":
            a = a[-1:]
        if a != v:
            return f"{k}: atteso {v}, avuto {a}"
    return None


def hz18(repo: Path, casa: Path) -> str | None:
    avuto = volta_node(repo, casa)
    if not isinstance(avuto, dict):
        return avuto
    atteso = {
        "clic": [{"azione": "aggancia", "argv": ["claude", "attach", "a1"]},
                 {"azione": "aggancia", "argv": ["ssh", "-t", "amaltea", ".local/bin/claude", "attach", "b1"]},
                 {"azione": "porta"}, "no", "no", "no", "no"],
        "aggancio": [True, False, False, True, False, False, True],
    }
    for k, v in atteso.items():
        if avuto.get(k) != v:
            return f"{k}: atteso {v}, avuto {avuto.get(k)}"
    return None


def hz19(repo: Path, casa: Path) -> str | None:
    mod = repo / "shared/volta-celeste/mods/arturo"
    barra = (mod / "barra.js").read_text(encoding="utf-8")
    volta = (mod / "volta.js").read_text(encoding="utf-8")
    for pezzo, dove in (('import { Volta } from "./volta.js";', "barra.js"), ("this.volta.init(cx);", "barra.js"),
                        ("this.volta.render(cx)", "barra.js"), ('c.startsWith("volta-")) this.volta.premiId(', "barra.js")):
        if pezzo not in barra:
            return f"{dove} senza {pezzo}"
    for pezzo in ('"volta", "--scrivi"', '"porta-volta"', "if (!this.script) return null;", "if (!this.script || this.inCorso) return;",
                  'from "./sessioni.js"', "agganciata(x.argv, s)"):
        if pezzo not in volta:
            return f"volta.js senza {pezzo}"
    return None


def hz20(repo: Path, casa: Path) -> str | None:
    volta = (repo / "shared/volta-celeste/mods/arturo/volta.js").read_text(encoding="utf-8")
    if "this.py = (await config()).arturo[0];" not in volta:
        return "volta.js non prende Python da arturo.json"
    for pezzo in ('exec(this.py, [this.script, "volta"', 'exec(this.py, [this.script, "porta-volta"'):
        if pezzo not in volta:
            return f"volta.js senza {pezzo}"
    if 'exec("python' in volta:
        return "volta.js lancia ancora un Python scritto a mano"
    return None


def hz21(repo: Path, casa: Path) -> str | None:
    # APPDATA finto: il veleno (la cartella di prima) non deve scrivere nella cartella vera
    r = installa(repo, casa, "windows", {"HERDR_APP_HOME": "", "APPDATA": str(casa / "appdata")})
    if r.returncode != 0 or "HERDR OK" not in r.stdout:
        return f"installazione Windows fallita rc={r.returncode}: {(r.stdout + r.stderr)[-200:]}"
    app = casa / "home" / ".config" / "herdr-app"
    if not (app / "layouts" / "arturo.json").is_file() or not (app / "arturo.json").is_file():
        return f"layout e arturo.json non sono in ~/.config/herdr-app, dove Herdr li legge su Windows"
    core = casa / "home" / ".config" / "herdr-core" / "config.toml"
    if not core.is_file() or "shell = [" not in core.read_text(encoding="utf-8"):
        return "la shell di herdr-core non è in ~/.config/herdr-core/config.toml"
    if (casa / "appdata").exists():
        return "l'installatore ha scritto in %APPDATA%, che Herdr su Windows non legge"
    return None


def hz22(repo: Path, casa: Path) -> str | None:
    esiti = {}
    for sistema in ("windows", "mac-arm"):
        sotto = casa / sistema
        sotto.mkdir()
        extra = {"ARTURO_HERDR_FIRMA": "presente"} if sistema == "mac-arm" else {}
        r = installa(repo, sotto, sistema, extra)
        if r.returncode != 0 or "HERDR OK" not in r.stdout:
            return f"installazione {sistema} fallita rc={r.returncode}: {(r.stdout + r.stderr)[-200:]}"
        esiti[sistema] = leggi(sotto / "app" / "keys.json").get("global", {})
    win, mac = esiti["windows"], esiti["mac-arm"]
    if win.get("ctrl-shift-a") != "arturo.apri" or win.get("ctrl-shift-m") != "arturo.nota":
        return f"su Windows mancano Ctrl+Shift+A e Ctrl+Shift+M: {win}"
    if any(k.startswith("cmd-") for k in win):
        return f"su Windows sono finiti tasti con cmd (il tasto Windows): {sorted(k for k in win if k.startswith('cmd-'))}"
    if mac.get("cmd-o") != "arturo.apri" or "ctrl-shift-a" in mac:
        return f"sui Mac i tasti non sono quelli con ⌘: {mac}"
    return None


def hz23(repo: Path, casa: Path) -> str | None:
    # python3 finto come lo stub di WindowsApps (esce 9009), python che porta al Python vero
    finti = casa / "finti"
    finti.mkdir()
    vero = Path(sys.executable).as_posix()
    (finti / "python3").write_text("#!/bin/sh\necho 'Python was not found' >&2\nexit 9009\n", encoding="utf-8", newline="\n")
    (finti / "python").write_text(f'#!/bin/sh\nexec "{vero}" "$@"\n', encoding="utf-8", newline="\n")
    for f in finti.iterdir():
        f.chmod(0o755)
    r = installa(repo, casa, "windows", {"PATH": str(finti) + os.pathsep + os.environ.get("PATH", "")})
    if r.returncode != 0 or "HERDR OK" not in r.stdout:
        return f"installazione fallita rc={r.returncode}: {(r.stdout + r.stderr)[-200:]}"
    py = leggi(casa / "app" / "arturo.json")["arturo"][0]
    if py != "python":
        return f"arturo.json usa {py!r}: con python3 che non risponde serve python"
    return None


def hz24(repo: Path, casa: Path) -> str | None:
    mod = repo / "shared/volta-celeste/mods/arturo"
    testata = (mod / "testata.js").read_text(encoding="utf-8")
    guida = (mod / "guida.js").read_text(encoding="utf-8")
    volta = (mod / "volta.js").read_text(encoding="utf-8")
    for nome, testo in (("testata.js", testata), ("guida.js", guida)):
        codice = "\n".join(r for r in testo.splitlines() if not r.lstrip().startswith("//"))
        if "⌘" in codice:
            return f"{nome} scrive ⌘ a mano: i tasti vengono da tasti() di comuni.js"
        if "tasti()" not in codice:
            return f"{nome} non prende i tasti da tasti()"
    if 'window()?.platform === "macos"' not in (mod / "comuni.js").read_text(encoding="utf-8"):
        return "tasti() non sceglie per sistema"
    if "else notify({ title: `Non trovo la sessione ${id}`" not in volta:
        return "premiId non avvisa quando la sessione non è nell'elenco"
    return None


def hz25(repo: Path, casa: Path) -> str | None:
    # Una finestra di dialogo chiusa ferma il suo codice al primo await: la chiusura viene dopo l'azione.
    mod = repo / "shared/volta-celeste/mods/arturo"
    prima = re.compile(r"(this\.chiudi\(\)|dopo\?\.\(\)|closeOverlay\([^)]*\));\s*(?:await\s+)?(apri|esegui|scrivi|chiedi|nuova)\(")
    for f in sorted(mod.glob("*.js")):
        m = prima.search(f.read_text(encoding="utf-8"))
        if m:
            return f"{f.name} chiude la finestra prima di {m.group(2)}(): l'azione non parte"
    attesi = {"suggerimenti.js": "try { await esegui(sug); } finally { dopo?.(); }",
              "apri.js": "try { await apri(nome); } finally { this.chiudi(); }",
              "revisione.js": "try { await apri(k); } finally { this.chiudi(); }",
              "menu.js": "scrivi(v.argv(testo), v.esito, titolo).finally(() => this.chiudi());"}
    for nome, pezzo in attesi.items():
        if pezzo not in (mod / nome).read_text(encoding="utf-8"):
            return f"{nome} non aspetta l'azione prima di chiudere"
    return None


PROVA_REGIONE = r"""
const { regione, misureDaLayout, ultimeRighe, nota } = await import(%s);
const lay = %s;
const mis = (l, a) => ({ larghezza: l, altezza: a });
const parti = { marchio: mis(292, 54), barra: mis(292, 690), piede: mis(292, 156), testata: mis(1147, 54),
  todo: mis(340, 792), stato: mis(1147, 30), benvenuto: mis(0, 0) };
const m = misureDaLayout(lay, parti, mis(1440, 900));
const b = (x, y, mm = m) => regione({ x, y }, mm)?.blocco ?? null;
const largo = { ...m, marchio: mis(400, 54), barra: mis(400, 690), piede: mis(400, 156), testata: mis(1039, 54),
  stato: mis(1039, 30), todo: mis(500, 792) };
console.log(JSON.stringify({
  base: [[100, 20], [100, 300], [100, 800], [292, 300], [600, 20], [600, 880], [600, 400], [1200, 400], [1080, 400], [1086, 400]].map(([x, y]) => b(x, y)),
  main: regione({ x: 600, y: 400 }, m)?.rettangolo,
  largo: [[350, 300], [402, 400], [1000, 400], [900, 400]].map(([x, y]) => b(x, y, largo)),
  nascosto: b(1200, 400, misureDaLayout({ ...lay, children: JSON.parse(JSON.stringify(lay.children).replace('"id":"pannello",', '"id":"pannello","hidden":true,')) }, parti, mis(1440, 900))),
  benvenuto: b(690, 100, { ...m, benvenuto: mis(520, 300) }),
  vecchie: [b(600, 400, { ...m, finestra: mis(1440, 820) }), b(600, 400, { ...m, finestra: mis(1280, 900) })],
  assenti: b(600, 400, misureDaLayout(lay, {}, mis(1440, 900))),
  righe: ultimeRighe("a\nb\nc\n\n  \n", 2),
  dove: nota({ testo: "x", x: 1, y: 2, larghezza: 3, altezza: 4, progetto: "p", cartella: "/c", quando: "q",
    dove: { blocco: "main", cwd: "/w" } }),
}));
"""


def hz26(repo: Path, casa: Path) -> str | None:
    mod = repo / "shared/volta-celeste/mods/arturo"
    main = (mod / "main.js").read_text(encoding="utf-8")
    if '"marchio", "barra", "piede", "testata", "todo", "stato", "benvenuto"' not in main \
            or "if (!MISURATE.has(this.nome) || !el?.on_size_change) return el;" not in main \
            or "return el.id(`misura-${this.nome}`).on_size_change(" not in main or "arturo.misura.${this.nome}" not in main:
        return "main.js non fa riportare la misura alle parti del layout"
    ui = (mod / "notaui.js").read_text(encoding="utf-8")
    if "const dove = await doveNota(this.punto, this.misura);" not in ui or "quando: new Date().toISOString(), dove, tipo: this.tipo" not in ui:
        return "notaui.js non mette la parte e il terminale nella nota"
    node = shutil.which("node")
    if not node:
        return None
    copia = casa / "nota.mjs"
    shutil.copyfile(mod / "nota.js", copia)
    lay = (repo / "shared/volta-celeste/layouts/arturo.json").read_text(encoding="utf-8")
    r = subprocess.run([node, "--input-type=module", "-e", PROVA_REGIONE % (json.dumps(copia.as_uri()), lay)],
                       capture_output=True, text=True, timeout=30)
    if r.returncode != 0:
        return f"nota.js non gira: {(r.stderr or r.stdout).strip()[:160]}"
    g = json.loads(r.stdout.strip().splitlines()[-1])
    attese = ["marchio", "progetti", "piede", "progetti", "testata", "stato", "main", "pannello", "main", "pannello"]
    if g["base"] != attese:
        return f"regione() sbaglia la parte sotto il punto: {g['base']}"
    if g["main"] != {"x": 305, "y": 66, "larghezza": 771, "altezza": 792}:
        return f"il rettangolo della sessione non è quello dello scatto: {g['main']}"
    if g["largo"] != ["progetti", "main", "pannello", "main"]:
        return f"con barra e pannello allargati regione() sbaglia: {g['largo']}"
    if g["nascosto"] != "main":
        return "col pannello nascosto il punto a destra non va alla sessione"
    if g["benvenuto"] != "benvenuto":
        return "il benvenuto sopra la sessione non si riconosce"
    if g["vecchie"] != [None, None] or g["assenti"] is not None:
        return "con misure vecchie o assenti regione() inventa una parte"
    if g["righe"] != "b\nc":
        return f"ultimeRighe() tiene le righe vuote in fondo: {g['righe']!r}"
    if g["dove"]["dati"].get("dove", {}).get("blocco") != "main" or "parte main (terminale in /w)" not in g["dove"]["argv"][8]:
        return "nota.json e il todo non portano la parte e il terminale"
    return None


PROVA_VELO = r"""
const n = await import(%s);
const base = { x: 700, y: 400, larghezza: 1440, altezza: 900, progetto: "p", cartella: "/c/note-finestra/2026-11-10_07-00-00",
  quando: "2026-11-10T06:00:00Z", testo: "Il bottone è storto" };
const v1 = JSON.stringify({ versione: 1, quando: "2026-11-09T10:00:00Z", testo: "vecchia", punto: { x: 10, y: 20 },
  finestra: { larghezza: 1440, altezza: 900 }, progetto: "p" });
const letta = n.leggiNota(v1, "2026-11-09_10-00-00");
const mk = (id, numero, stato, progetto = "p", quando = id) => ({ id, numero, stato, progetto, quando, punto: { x: 1, y: 1 }, finestra: { larghezza: 1, altezza: 1 } });
const aperte = n.noteAperte([letta, mk("b", 1, "aperta"), mk("c", 3, "presa"), mk("d", 2, "risolta"), mk("e", 5, "aperta", "altro")], "p");
const nuova = n.nota({ ...base, numero: 4 }).dati;
const risposta = n.rispondi(nuova, "claude", "  fatto,  guarda ", "t1");
console.log(JSON.stringify({
  nuova, argv: n.nota(base).argv, tipo: [n.nota({ ...base, tipo: "domanda" }).dati.tipo, n.nota({ ...base, tipo: "boh" }).dati.tipo],
  letta, rotta: [n.leggiNota("{", "x"), n.leggiNota("{}", "x")],
  aperte: aperte.map((a) => [a.id, a.numero]), prossimo: [n.prossimoNumero(aperte), n.prossimoNumero([])],
  segni: [n.segno(nuova, { larghezza: 1440, altezza: 900 }), n.segno(nuova, { larghezza: 720, altezza: 450 }),
    n.segno({ ...nuova, punto: { x: 1439, y: 899 } }, { larghezza: 700, altezza: 400 })],
  risposta: risposta.filo, vuota: n.rispondi(nuova, "claude", "  ", "t"), chi: n.rispondi(nuova, "altro", "x", "t"),
  risolta: n.chiudiNota(risposta, "risolta", "sistemato", "t2", "claude"), scartata: n.chiudiNota(nuova, "scartata", "", "t3"),
  sbagliata: n.chiudiNota(nuova, "boh", "x", "t"),
  script: n.LEGGI_NOTE,
}));
"""


def hz27(repo: Path, casa: Path) -> str | None:
    mod = repo / "shared/volta-celeste/mods/arturo"
    ui = (mod / "notaui.js").read_text(encoding="utf-8")
    for pezzo, perche in [
        ('exec(py, ["-c", LEGGI_NOTE, cartellaNote(home())]', "il velo non legge le note col Python di arturo.json"),
        ("writeTextFile(file, json({ ...n.dati, todo: r.json.id }), scritto)", "la nota non salva l'id del todo"),
        ("json(salvata), prima.testo);", "il velo riscrive nota.json senza controllare che sia ancora quello letto"),
        ('await todo(["fatto", String(n.todo)]);', "Risolta non chiude il todo"),
        ('await todo(["scarta", String(n.todo)', "Scarta non scarta il todo"),
        ("el.children(this.segni(t))", "il velo non disegna i segni delle note aperte"),
        (".child(this.pastiglie(t))", "il campo non ha le pastiglie del tipo"),
        ("numero: prossimoNumero(aperte)", "la nota nuova non prende il numero dopo le aperte")]:
        if pezzo not in ui:
            return perche
    node = shutil.which("node")
    if not node:
        return None
    copia = casa / "nota.mjs"
    shutil.copyfile(mod / "nota.js", copia)
    r = subprocess.run([node, "--input-type=module", "-e", PROVA_VELO % json.dumps(copia.as_uri())],
                       capture_output=True, text=True, timeout=30)
    if r.returncode != 0:
        return f"nota.js non gira: {(r.stderr or r.stdout).strip()[:160]}"
    g = json.loads(r.stdout.strip().splitlines()[-1])
    d = g["nuova"]
    if (d["versione"], d["id"], d["numero"], d["tipo"], d["stato"], d["todo"], d["filo"]) != (
            2, "2026-11-10_07-00-00", 4, "correggere", "aperta", None,
            [{"chi": "federico", "quando": "2026-11-10T06:00:00Z", "testo": "Il bottone è storto"}]):
        return f"nota.json versione 2 sbagliata: {d}"
    if g["tipo"] != ["domanda", "correggere"]:
        return f"il tipo della nota non si tiene o non ricade sul predefinito: {g['tipo']}"
    if "--json" not in g["argv"] or g["argv"].index("--json") > g["argv"].index("--"):
        return "il todo della nota non si chiede con --json: l'id non torna nella nota"
    l = g["letta"]
    if (l["versione"], l["id"], l["stato"], l["numero"], l["tipo"], l["filo"][0]["testo"], l["dove"]["blocco"]) != (
            2, "2026-11-09_10-00-00", "aperta", None, "correggere", "vecchia", None):
        return f"una nota versione 1 non si legge come aperta versione 2: {l}"
    if g["rotta"] != [None, None]:
        return "un nota.json rotto o vuoto diventa una nota"
    if g["aperte"] != [["b", 1], ["2026-11-09_10-00-00", 2], ["c", 3]] or g["prossimo"] != [4, 1]:
        return f"numeri dei segni sbagliati: {g['aperte']} prossimo {g['prossimo']}"
    if g["segni"] != [{"x": 700, "y": 400}, {"x": 350, "y": 200}, {"x": 699, "y": 399}]:
        return f"i segni non si riportano in scala sulla finestra: {g['segni']}"
    if g["risposta"][-1] != {"chi": "claude", "quando": "t1", "testo": "fatto, guarda"} or g["vuota"] or g["chi"]:
        return "la risposta non entra nel filo, o entra vuota o di qualcun altro"
    ri, sc = g["risolta"], g["scartata"]
    if (ri["stato"], ri["riassunto"], ri["motivo"], ri["chiusa_quando"], ri["filo"][-1]["testo"]) != ("risolta", "sistemato", None, "t2", "sistemato") \
            or (sc["stato"], sc["motivo"], sc["chiusa_quando"], len(sc["filo"])) != ("scartata", None, "t3", 1) or g["sbagliata"] is not None:
        return "risolta e scartata non chiudono la nota come devono"
    cartella = casa / "note"
    for nome, testo in [("a", '{"x": 1}'), ("b", None), ("c", "ciao")]:
        (cartella / nome).mkdir(parents=True)
        if testo:
            (cartella / nome / "nota.json").write_text(testo, encoding="utf-8")
    letto = [json.loads(subprocess.run([sys.executable, "-c", g["script"], str(c)], capture_output=True, text=True, timeout=30).stdout)
             for c in (cartella, casa / "manca")]
    if letto != [[["a", '{"x": 1}'], ["c", "ciao"]], []]:
        return f"LEGGI_NOTE non legge la cartella delle note: {letto}"
    env = {**os.environ, "HOME": str(casa), "USERPROFILE": str(casa), "ARTURO_TODO": str(casa / "eventi.jsonl"),
           "ARTURO_OGGI": "2026-11-10"}
    r = subprocess.run([sys.executable, str(repo / "bin/arturo"), "todo", *g["argv"]], capture_output=True,
                       text=True, timeout=60, env=env, cwd=casa)
    try:
        if json.loads(r.stdout)["id"] != 1:
            return f"la CLI non dà l'id del todo: {r.stdout[:120]}"
    except (ValueError, KeyError):
        return f"la CLI con --json non risponde in JSON: {(r.stderr or r.stdout).strip()[:160]}"
    return None




PROVA_ELENCO = r"""
const n = await import(%s);
const f = { larghezza: 1440, altezza: 900 };
const mk = (id, numero, stato, extra = {}) => ({ id, numero, stato, progetto: "p", quando: `2026-11-10T0${id}:00:00Z`, tipo: "domanda",
  testo: `nota ${id}`, punto: { x: 1, y: 1 }, finestra: f, filo: [{ chi: "federico", quando: "t", testo: `nota ${id}` }], ...extra });
const lista = [
  mk("1", 2, "aperta"),
  mk("2", 1, "presa", { filo: [{ chi: "federico", testo: "x" }, { chi: "claude", testo: "prima" }, { chi: "claude", testo: "ultima" }] }),
  mk("3", 1, "risolta", { chiusa_quando: "2026-11-10T05:00:00Z", riassunto: "fatto" }),
  mk("4", 3, "scartata", { chiusa_quando: "2026-11-10T06:00:00Z", motivo: "doppia" }),
  { ...mk("5", 4, "aperta"), progetto: "altro" },
];
const ora = "2026-11-10T08:00:00Z";
const r = (filtro) => n.righeElenco(lista, "p", filtro, ora).map((x) => [x.id, x.numero, x.etichettaStato, x.risposta, x.chiusura, x.eta, x.tipo]);
const viste = n.risposteClaude(lista);
const dopo = lista.map((x) => x.id === "1" ? { ...x, filo: [...x.filo, { chi: "claude", testo: "nuova" }] } : x);
console.log(JSON.stringify({
  aperte: r("aperte"), tutte: r("tutte"), conta: [n.contaNote(lista, "p"), n.contaNote(lista, null)],
  eta: ["2026-11-10T07:59:30Z", "2026-11-10T07:48:00Z", "2026-11-10T07:00:00Z", "2026-11-10T03:00:00Z", "2026-11-09T07:00:00Z", "2026-11-06T07:00:00Z", "boh"].map((q) => n.eta(q, ora)),
  nuove: n.risposteNuove(viste, dopo).map((x) => x.id), primo: n.risposteNuove(null, dopo).length,
  nuovaNota: n.risposteNuove(viste, [...lista, mk("6", 5, "aperta", { filo: [{ chi: "claude", testo: "subito" }] })]).map((x) => x.id),
}));
"""


def hz28(repo: Path, casa: Path) -> str | None:
    vc = repo / "shared/volta-celeste"
    mod = vc / "mods/arturo"
    testo = {f: (mod / f).read_text(encoding="utf-8") for f in ("main.js", "barra.js", "testata.js", "noteui.js", "comuni.js")}
    for f, pezzo, perche in [
        ("main.js", "note: Note };", "main.js non monta la parte note"),
        ("barra.js", 'else if (c === "note") apriElenco();', "il comando arturo.note non apre l'elenco"),
        ("barra.js", 'else if (c.startsWith("nota-")) await apriNota(c.slice(5));', "arturo.nota-<id> non apre il velo su quella nota"),
        ("comuni.js", 'props: { parte: "nota", cartella, apri }', "il velo non riceve la nota da aprire"),
        ("comuni.js", 'props: { parte: "note" }', "apriElenco non apre la parte note"),
        ("comuni.js", 'elenco: "⌘⇧E"', "tasti() non dice ⌘⇧E sui Mac"),
        ("comuni.js", 'elenco: "Ctrl+Shift+E"', "tasti() non dice Ctrl+Shift+E fuori dal Mac"),
        ("testata.js", "await watchFolder(cartellaNote(home()))", "la barra di stato non guarda la cartella delle note"),
        ("testata.js", ".on_click(() => apriElenco())", "il conteggio della barra di stato non apre l'elenco"),
        ("testata.js", "const nuove = risposteNuove(this.viste, note);", "la barra di stato non annuncia le risposte di Claude"),
        ("noteui.js", "run(`arturo.nota-${r.id}`);\n    this.chiudi();", "l'elenco chiude prima di mandare il comando: il codice di un overlay chiuso si ferma"),
    ]:
        if pezzo not in testo[f]:
            return perche
    mac = leggi(vc / "keys.json").get("global", {})
    win = leggi(vc / "keys-ctrl.json").get("global", {})
    if mac.get("cmd-shift-e") != "arturo.note" or win.get("ctrl-shift-e") != "arturo.note":
        return f"⌘⇧E o Ctrl+Shift+E non aprono l'elenco: {mac.get('cmd-shift-e')} {win.get('ctrl-shift-e')}"
    if "cmd-shift-l" in mac:
        return "⌘⇧L è di Herdr (layout.switch): l'installatore lo lascerebbe alla persona"
    node = shutil.which("node")
    if not node:
        return None
    copia = casa / "nota.mjs"
    shutil.copyfile(mod / "nota.js", copia)
    r = subprocess.run([node, "--input-type=module", "-e", PROVA_ELENCO % json.dumps(copia.as_uri())],
                       capture_output=True, text=True, timeout=30)
    if r.returncode != 0:
        return f"nota.js non gira: {(r.stderr or r.stdout).strip()[:160]}"
    g = json.loads(r.stdout.strip().splitlines()[-1])
    aperte = [["2", 1, "Claude ci lavora", "ultima", None, "6 ore fa", "Domanda"], ["1", 2, "Aperta", None, None, "7 ore fa", "Domanda"]]
    if g["aperte"] != aperte:
        return f"righe delle aperte sbagliate: {g['aperte']}"
    if g["tutte"] != aperte + [["4", None, "Scartata", None, "doppia", "2 ore fa", "Domanda"], ["3", None, "Risolta", None, "fatto", "3 ore fa", "Domanda"]]:
        return f"con tutte le chiuse non seguono dalla più recente, o tengono il numero: {g['tutte'][2:]}"
    if g["conta"] != [{"aperte": 2, "tutte": 4}, {"aperte": 0, "tutte": 0}]:
        return f"conteggio per progetto sbagliato: {g['conta']}"
    if g["eta"] != ["adesso", "12 min fa", "1 ora fa", "5 ore fa", "ieri", "4 giorni fa", ""]:
        return f"età in parole sbagliata: {g['eta']}"
    if g["nuove"] != ["1"] or g["primo"] != 0 or g["nuovaNota"] != ["6"]:
        return f"le risposte nuove di Claude non si annunciano giuste: {g['nuove']} {g['primo']} {g['nuovaNota']}"
    return None


def png(file: Path, larghezza: int, altezza: int) -> None:
    """Un PNG grigio vero, con la sola libreria standard: lo scatto finto della finestra."""
    import struct
    import zlib

    def pezzo(tipo: bytes, dati: bytes) -> bytes:
        return struct.pack(">I", len(dati)) + tipo + dati + struct.pack(">I", zlib.crc32(tipo + dati) & 0xFFFFFFFF)
    riga = b"\x00" + b"\x80" * (larghezza * 3)
    file.write_bytes(b"\x89PNG\r\n\x1a\n" + pezzo(b"IHDR", struct.pack(">IIBBBBB", larghezza, altezza, 8, 2, 0, 0, 0))
                     + pezzo(b"IDAT", zlib.compress(riga * altezza)) + pezzo(b"IEND", b""))


def casa_note(casa: Path) -> tuple:
    """L'ambiente di una casa finta per arturo note e la cartella delle sue note: (env, cartella)."""
    env = {**os.environ, "HOME": str(casa), "USERPROFILE": str(casa), "ARTURO_TODO": str(casa / "eventi.jsonl"),
           "ARTURO_OGGI": "2026-11-10"}
    env.pop("CLAUDE_CONFIG_DIR", None)
    return env, casa / ".claude/data/note-finestra"


def nota_v2(base: Path, ident: str, todo, **altro) -> None:
    d = {"versione": 2, "id": ident, "numero": 1, "quando": "2026-11-10T06:00:00.000Z", "tipo": "domanda",
         "testo": "Perché il bottone è storto?", "punto": {"x": 700, "y": 450}, "finestra": {"larghezza": 800, "altezza": 500},
         "progetto": "p", "dove": {"blocco": "testata", "parte": "testata"}, "stato": "aperta",
         "filo": [{"chi": "federico", "quando": "2026-11-10T06:00:00.000Z", "testo": "Perché il bottone è storto?"}],
         "todo": todo, "screenshot": "finestra.png", **altro}
    (base / ident).mkdir(parents=True, exist_ok=True)
    (base / ident / "nota.json").write_text(json.dumps(d), encoding="utf-8")


def hz29(repo: Path, casa: Path) -> str | None:
    env, base = casa_note(casa)
    arturo = [sys.executable, str(repo / "bin/arturo")]

    def cli(*argv):
        return subprocess.run([*arturo, *argv], capture_output=True, text=True, timeout=120, env=env, cwd=casa)
    aiuto = cli().stdout
    if "arturo note" not in aiuto:
        return "l'aiuto di arturo non nomina arturo note"
    r = cli("todo", "aggiungi", "--progetto", "p", "--chi", "io", "--json", "--", "Nota sulla finestra: il bottone")
    try:
        tid = json.loads(r.stdout)["id"]
    except (ValueError, KeyError):
        return f"il todo della nota non nasce: {(r.stderr or r.stdout)[:120]}"
    nota_v2(base, "2026-11-10_07-00-00", tid)
    png(base / "2026-11-10_07-00-00/finestra.png", 1600, 1000)
    (base / "vecchia").mkdir(parents=True)
    (base / "vecchia/nota.json").write_text(json.dumps({"testo": "v1", "punto": {"x": 5, "y": 5}, "progetto": "p",
        "finestra": {"larghezza": 800, "altezza": 500}, "quando": "2026-11-10T05:00:00Z"}), encoding="utf-8")
    (base / "vuota").mkdir()
    r = cli("note", "elenco", "--json")
    try:
        note = json.loads(r.stdout)["note"]
    except (ValueError, KeyError):
        return f"elenco --json non risponde in JSON: {(r.stderr or r.stdout)[:160]}"
    if [(n["id"], n["numero"], n["stato"]) for n in note] != [("2026-11-10_07-00-00", 1, "aperta"), ("vecchia", 2, "aperta")]:
        return f"elenco: numeri o stati sbagliati (una v1 prende il primo libero, mai uno già preso): {[(n['id'], n['numero'], n['stato']) for n in note]}"
    md = cli("note", "elenco", "--md").stdout
    if "# Note sulla finestra di Volta Celeste: 2 aperte" not in md or "`arturo note mostra 2026-11-10_07-00-00`" not in md:
        return f"elenco --md non è il brief: {md[:160]}"
    r = cli("note", "mostra", "1", "--json")
    try:
        m = json.loads(r.stdout)
    except ValueError:
        return f"mostra --json non risponde in JSON: {(r.stderr or r.stdout)[:160]}"
    rq = m["ritaglio"]["riquadro"]
    if m["id"] != "2026-11-10_07-00-00" or not rq or (rq["x"], rq["y"], rq["larghezza"], rq["altezza"], rq["punto"]) != (
            320, 200, 1280, 800, {"x": 1080, "y": 700}):
        return f"il ritaglio non sta attorno al punto, in scala e dentro lo scatto: {m['ritaglio']}"
    if (shutil.which("ffmpeg") or shutil.which("sips")) and m["ritaglio"]["come"] not in ("ffmpeg", "sips"):
        return f"ritaglio.png non nasce con ffmpeg o sips: {m['ritaglio']}"
    preso = cli("note", "prendi", "1")
    if preso.returncode or json.loads((base / "2026-11-10_07-00-00/nota.json").read_text(encoding="utf-8"))["stato"] != "presa":
        return f"prendi non segna la nota come presa: {preso.stderr.strip()[:80]}"
    passi = [preso,
             cli("note", "rispondi", "2026-11-10_07-00-00", "Ci guardo:", "è il padding"),
             cli("note", "risolvi", "2026-11-10_07-00-00", "Padding corretto")]
    if any(p.returncode for p in passi):
        return f"il giro prendi, rispondi, risolvi non passa: {[(p.returncode, p.stderr.strip()[:80]) for p in passi]}"
    d = json.loads((base / "2026-11-10_07-00-00/nota.json").read_text(encoding="utf-8"))
    if (d["stato"], d["riassunto"], d["motivo"], d["numero"], [(v["chi"], v["testo"]) for v in d["filo"]]) != (
            "risolta", "Padding corretto", None, 1, [("federico", "Perché il bottone è storto?"),
                                                    ("claude", "Ci guardo: è il padding"), ("claude", "Padding corretto")]) \
            or not str(d.get("chiusa_quando", "")).endswith("Z"):
        return f"la nota risolta non porta stato, riassunto e filo: {d}"
    t = json.loads(cli("todo", "mostra", str(tid), "--json").stdout)
    tipi = [s["dati"].get("stato") for s in t["storia"] if s["tipo"] == "stato"]
    if t["stato"] != "fatto" or tipi != ["in corso", "fatto"] or not any("Claude sulla nota 1: Ci guardo" in n for n in t["note"]):
        return f"il todo non segue la nota (in corso, nota, fatto): {t['stato']} {tipi} {t['note']}"
    di_nuovo = cli("note", "risolvi", "2026-11-10_07-00-00", "ancora")
    if di_nuovo.returncode != 2 or "già risolta" not in di_nuovo.stderr:
        return "una nota già chiusa si richiude"
    r = cli("note", "scarta", "1", "doppia")
    v = json.loads((base / "vecchia/nota.json").read_text(encoding="utf-8"))
    if r.returncode or (v["stato"], v["motivo"], v["riassunto"], v["versione"]) != ("scartata", "doppia", None, 2):
        return f"scarta non chiude col motivo la nota versione 1: {r.stderr.strip()[:80]} {v}"
    for argv, perche in [(("note", "mostra", "../vecchia"), "un percorso"), (("note", "risolvi", "2026-11-10_07-00-00"), "un risolvi senza testo"),
                         (("note", "boh"), "un verbo sconosciuto")]:
        if cli(*argv).returncode != 2:
            return f"{perche} non esce con 2"
    if cli("note", "elenco").stdout.strip() != "Nessuna nota aperta sulla finestra.":
        return "con tutte le note chiuse l'elenco non lo dice"
    return None


PROVA_CONCORRENTE = r"""
import json, sys
sys.path.insert(0, sys.argv[1])
import note_finestra as nf
file = nf.cartella() / sys.argv[2] / "nota.json"
originale = nf._sostituisci
chiamate = []
def sostituisci(f, letto, nuovo):
    chiamate.append(1)
    if len(chiamate) == 1:  # il velo scrive proprio adesso, fra la lettura e la scrittura della CLI
        d = json.loads(f.read_text(encoding="utf-8"))
        d["filo"].append({"chi": "federico", "quando": "t", "testo": "dal velo"})
        f.write_text(json.dumps(d), encoding="utf-8")
    return originale(f, letto, nuovo)
nf._sostituisci = sostituisci
nf.aggiorna(sys.argv[2], lambda n: nf.rispondi(n, "dalla CLI"))
nf._sostituisci = originale
print(json.dumps({"chiamate": len(chiamate), "filo": [v["testo"] for v in json.loads(file.read_text(encoding="utf-8"))["filo"]]}))
"""


def hz30(repo: Path, casa: Path) -> str | None:
    env, base = casa_note(casa)
    nota_v2(base, "n1", None)
    r = subprocess.run([sys.executable, "-c", PROVA_CONCORRENTE, str(repo / "bin"), "n1"], capture_output=True,
                       text=True, timeout=60, env=env, cwd=casa)
    if r.returncode != 0:
        return f"la scrittura concorrente si rompe: {(r.stderr or r.stdout).strip()[-200:]}"
    g = json.loads(r.stdout.strip().splitlines()[-1])
    if g["filo"] != ["Perché il bottone è storto?", "dal velo", "dalla CLI"] or g["chiamate"] != 2:
        return f"con il file cambiato fra lettura e scrittura una delle due risposte si perde: {g}"
    if any(p.name.startswith(".nota.") for p in (base / "n1").iterdir()):
        return "la scrittura rifiutata lascia un file temporaneo nella cartella della nota"
    return None


PROVE = {"HZ01": hz01, "HZ02": hz02, "HZ03": hz03, "HZ04": hz04, "HZ05": hz05, "HZ06": hz06, "HZ07": hz07, "HZ08": hz08, "HZ09": hz09, "HZ10": hz10, "HZ11": hz11, "HZ12": hz12, "HZ13": hz13, "HZ14": hz14, "HZ15": hz15, "HZ16": hz16, "HZ17": hz17, "HZ18": hz18, "HZ19": hz19, "HZ20": hz20, "HZ21": hz21, "HZ22": hz22, "HZ23": hz23, "HZ24": hz24, "HZ25": hz25, "HZ26": hz26, "HZ27": hz27, "HZ28": hz28, "HZ29": hz29, "HZ30": hz30}


def prova(repo: Path, solo: str | None = None) -> list[str]:
    rossi = []
    for codice, f in PROVE.items():
        if solo and codice != solo:
            continue
        with tempfile.TemporaryDirectory() as tmp:
            try:
                motivo = f(repo, Path(tmp))
            except Exception as e:  # un caso che si rompe è rosso, non ferma gli altri
                motivo = f"eccezione {type(e).__name__}: {e}"
        if motivo:
            rossi.append(f"{codice} {motivo}")
    return rossi


VELENI = [
    ("HZ01", "shared/volta-celeste/installa-herdr.sh", '"frame.welcomed": "skipped"', '"frame.welcomed": "finished"'),
    ("HZ02", "shared/volta-celeste/installa-herdr.sh", "if k in mia and mia[k] != v:", "if False:"),
    ("HZ03", "shared/volta-celeste/installa-herdr.sh", 'Arturo funziona lo stesso nel Terminale."; exit 0 ;;', 'Arturo funziona lo stesso nel Terminale." ;;'),
    ("HZ04", "hooks/herdr-stato.sh", '[ -n "${HC_TERMINAL_ID:-}" ] || exit 0', ":"),
    ("HZ05", "settings.json", "herdr-stato.sh done", "herdr-stato.sh idle"),
    ("HZ09", "shared/volta-celeste/mods/arturo/dati.js", 'prompt: "/guidami"', 'prompt: "/guidamii"'),
    ("HZ10", "shared/volta-celeste/mods/arturo/partenza.js", "catena.slice(qui + 1)", "catena.slice(qui)"),
    ("HZ11", "shared/volta-celeste/mods/arturo/settimana.js", "else if (te) liste.te.push", "if (te) liste.te.push"),
    ("HZ12", "shared/volta-celeste/mods/arturo/azioni.js", "if (quando === t.quando) continue;", ""),
    ("HZ12", "shared/volta-celeste/mods/arturo/azioni.js", 'argv: ["inizia"', 'argv: ["riprendi"'),
    ("HZ12", "shared/volta-celeste/mods/arturo/todo.js", "const g = inizia(item);", "const g = null;"),
    ("HZ14", "shared/volta-celeste/mods/arturo/nota.js", "if (!t) return null;", ""),
    ("HZ14", "shared/volta-celeste/mods/arturo/nota.js", '"--chi", "io"', '"--chi", "tu"'),
    ("HZ13", "shared/volta-celeste/arturo-app.sh", 'python3 - "$plist" "$copia/arturo-app.sh"', 'python3 - "$plist" "$qui/arturo-app.sh"'),
    ("HZ13", "shared/volta-celeste/arturo-app.sh", '-c "Set :CFBundleIdentifier $ID"', '-c "Set :CFBundleIdentifier dev.herdr.app"'),
    ("HZ13", "shared/volta-celeste/arturo-app.sh", 'if [ -d "$arturo" ] && { [ ! -d "$herdr" ] || ! piu_nuova "$v_herdr" "$v_arturo"; }; then base=$arturo; fi', ":"),
    ("HZ06", "shared/volta-celeste/installa-herdr.sh", '[ "$firma" = assente ]', '[ "$firma" = mai ]'),
    ("HZ07", "shared/volta-celeste/mods/arturo/main.js", 'from "./notaui.js"', 'from "./notaui-perso.js"'),
    ("HZ07", "shared/volta-celeste/mods/arturo/main.js", ", nota: Nota, note: Note };", ", note: Note };"),
    ("HZ07", "shared/volta-celeste/layouts/arturo.json", '"parte": "stato"', '"parte": "stato-perso"'),
    ("HZ16", "shared/volta-celeste/servizi-gui.sh", "plist herdr-core false", "plist herdr-core true"),
    ("HZ16", "shared/volta-celeste/servizi-gui.sh", 'rm -f "$agenti/$PREFISSO.claude-daemon.plist"', 'plist claude-daemon true "$claude" daemon run'),
    ("HZ15", ".gitignore", "data/note-finestra/\n", ""),
    ("HZ15", ".gitignore", "data/herdr-invito\n", ""),
    ("HZ17", "shared/volta-celeste/mods/arturo/sessioni.js", "const RANGO = { aspetta: 0, errore: 1, lavora: 2, ferma: 3 };", "const RANGO = { aspetta: 3, errore: 1, lavora: 2, ferma: 0 };"),
    ("HZ17", "shared/volta-celeste/mods/arturo/sessioni.js", '(a.chiave === "") - (b.chiave === "") || ', ""),
    ("HZ18", "shared/volta-celeste/mods/arturo/sessioni.js", 'if (s.stato === "lavora") return { azione', "if (false) return { azione"),
    ("HZ18", "shared/volta-celeste/mods/arturo/sessioni.js", "if (s.vecchia) return { azione", "if (false) return { azione"),
    ("HZ18", "shared/volta-celeste/mods/arturo/sessioni.js", "|| argv.some((a) => dentro(a, s.id)))", ")"),
    ("HZ18", "shared/volta-celeste/mods/arturo/sessioni.js", '${id.replace(/[^\\w-]/g, "")}\\\\b`', '${id.replace(/[^\\w-]/g, "")}`'),
    ("HZ18", "shared/volta-celeste/mods/arturo/sessioni.js", "\\\\battach['\"]?\\\\s+['\"]?", "\\\\battach\\\\s+"),
    ("HZ19", "shared/volta-celeste/mods/arturo/barra.js", 'else if (c.startsWith("volta-")) this.volta.premiId(c.slice(6), cx);', ""),
    ("HZ19", "shared/volta-celeste/mods/arturo/volta.js", "if (!this.script) return null;", ""),
    ("HZ20", "shared/volta-celeste/mods/arturo/volta.js", 'exec(this.py, [this.script, "volta"', 'exec("python3", [this.script, "volta"'),
    ("HZ21", "shared/volta-celeste/installa-herdr.sh", "app_home=${HERDR_APP_HOME:-$HOME/.config/herdr-app}",
     'if [ "$sistema" = windows ]; then app_home=${HERDR_APP_HOME:-${APPDATA:-$HOME/AppData/Roaming}/herdr-app}; '
     "else app_home=${HERDR_APP_HOME:-$HOME/.config/herdr-app}; fi"),
    ("HZ22", "shared/volta-celeste/installa-herdr.sh", '[ "$sistema" = mac-arm ] || tasti=keys-ctrl.json', ":"),
    ("HZ23", "shared/volta-celeste/installa-herdr.sh", 'if "$c" -c "import sys" >/dev/null 2>&1; then py=$c; break; fi',
     'if command -v "$c" >/dev/null 2>&1; then py=$c; break; fi'),
    ("HZ24", "shared/volta-celeste/mods/arturo/testata.js", "const scorciatoie = `${k.apri} apri un progetto",
     "const scorciatoie = `⌘O apri un progetto"),
    ("HZ25", "shared/volta-celeste/mods/arturo/suggerimenti.js", ".on_click(async () => { try { await esegui(sug); } finally { dopo?.(); } })",
     ".on_click(() => { dopo?.(); esegui(sug); })"),
    ("HZ26", "shared/volta-celeste/mods/arturo/nota.js", "const mainW = testata.larghezza - 2 * pad - (pannelloW ? pannelloW + gap : 0);",
     "const mainW = testata.larghezza - 2 * pad;"),
    ("HZ26", "shared/volta-celeste/mods/arturo/nota.js", "if (Math.abs(marchio.altezza + barra.altezza + piede.altezza - H) > 2) return null;", ""),
    ("HZ26", "shared/volta-celeste/mods/arturo/nota.js", "if (Math.abs(S + (m.divisore ?? 1) + testata.larghezza - W) > 2) return null;", ""),
    ("HZ26", "shared/volta-celeste/mods/arturo/main.js", "if (!MISURATE.has(this.nome) || !el?.on_size_change) return el;", "return el;"),
    ("HZ27", "shared/volta-celeste/mods/arturo/nota.js", "if (Number.isInteger(n.numero)) return n;", "return n;"),
    ("HZ27", "shared/volta-celeste/mods/arturo/nota.js", 'stato: "aperta", chiusa_quando: null', 'stato: "presa", chiusa_quando: null'),
    ("HZ27", "shared/volta-celeste/mods/arturo/nota.js", "n.punto.x * W / f.larghezza", "n.punto.x"),
    ("HZ27", "shared/volta-celeste/mods/arturo/nota.js", '"--note", riga, "--json", "--"', '"--note", riga, "--"'),
    ("HZ27", "shared/volta-celeste/mods/arturo/notaui.js", "json(salvata), prima.testo);", "json(salvata), null);"),
    ("HZ28", "shared/volta-celeste/mods/arturo/nota.js", "recente(b).localeCompare(recente(a))", "recente(a).localeCompare(recente(b))"),
    ("HZ28", "shared/volta-celeste/mods/arturo/nota.js", "numero: aperta ? n.numero : null", "numero: n.numero"),
    ("HZ28", "shared/volta-celeste/mods/arturo/nota.js", "  if (!prima) return [];\n", ""),
    ("HZ28", "shared/volta-celeste/keys.json", '"cmd-shift-e": "arturo.note"', '"cmd-shift-l": "arturo.note"'),
    ("HZ28", "shared/volta-celeste/mods/arturo/testata.js", ".on_click(() => apriElenco())", ""),
    ("HZ28", "shared/volta-celeste/mods/arturo/noteui.js", "run(`arturo.nota-${r.id}`);\n    this.chiudi();", "this.chiudi();\n    run(`arturo.nota-${r.id}`);"),
    ("HZ29", "bin/note_finestra.py", 'return {**n, "stato": "presa"}', "return n"),
    ("HZ29", "bin/note_finestra.py", 'presi = {n["numero"] for n in qui if n["numero"] is not None}', "presi = set()"),
    ("HZ29", "bin/note_finestra.py", 'sul_todo(n, ["fatto"] if stato == "risolta"', 'sul_todo(n, ["inizia"] if stato == "risolta"'),
    ("HZ29", "bin/note_finestra.py", "x = min(max(px - w // 2, 0), W - w)", "x = max(px - w // 2, 0)"),
    ("HZ29", "bin/note_finestra.py", "scala = W / f[\"larghezza\"] if f.get(\"larghezza\") else 1", "scala = 1"),
    ("HZ29", "bin/note_finestra.py", 'if n["stato"] not in APERTE:\n        raise ErroreNota(f"la nota {n[\'id\']} è già {n[\'stato\']}")\n    v = ', "v = "),
    ("HZ29", "bin/arturo", '    "note": ("note_finestra",', '    "notte": ("note_finestra",'),
    ("HZ30", "bin/note_finestra.py", "        if ora != letto:", "        if False:"),
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
            rossi = prova(copia, caso)  # solo il caso sorvegliato: tutti i casi per ogni veleno superano i 30 minuti del gate
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
