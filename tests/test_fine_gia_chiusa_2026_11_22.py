#!/usr/bin/env python3
"""Un /fine su una sessione già chiusa si ferma prima del modello (bin/fine-gia-chiusa.py, 22/11/2026, #6274).

Segnalazioni n. 79, 87 e 93: il mod chiusura-automatica di una persona rilancia /fine ogni 45 minuti su una
sessione ferma. Arturo lo ferma in inject-now.sh (UserPromptSubmit): uscita 2, il prompt non arriva al modello.

FG01 sessione chiusa (handoff con "- Sessione: <id>" dopo l'ultimo /fine, dopo solo righe meta e risultati di
     tool): "/fine chiusura automatica dopo 45 minuti senza messaggi" esce 2 e nomina l'handoff.
FG02 un messaggio della persona dopo il /fine: il /fine parte (uscita 0).
FG03 nessun handoff di questa sessione (solo quello di un'altra): parte.
FG04 l'handoff della sessione è un salvataggio automatico ("- Salvato: in automatico"): parte.
FG05 /fine --forza, /fine --full e /fine salva partono anche su una sessione chiusa; "salva" a metà testo no.
FG06 l'handoff della sessione è più vecchio dell'ultimo /fine (il /fine non l'ha riscritto): parte.
FG07 un messaggio di un'altra sessione o la fine di un lavoro in background dopo il /fine: parte.
FG08 la trascrizione senza nessun /fine: parte, anche con l'handoff della sessione.
FG09 inject-now.sh esce 2 su /fine e /arturo:fine di una sessione chiusa, 0 su /finestra e su un messaggio.
FG10 nel dubbio parte: JSON rotto, trascrizione che non esiste.
FG11 il prompt deve essere proprio /fine: /finestra e "fine del lavoro" partono anche su una sessione chiusa.
FG12 il congedo di Volta ("/fine congedo da Volta: ...") parte: Volta ha il suo controllo contro il secondo /fine
     e aspetta il turno di /fine per fermare la sessione.

Veleno: --avvelena rompe il punto sorvegliato nella copia di prova, un punto per caso, ed esce 0 solo se ogni
rottura fa rosso il suo caso (VELENI del gate).
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
from datetime import datetime, timezone
from pathlib import Path

# Il bash del PATH: un "bash" senza percorso, su Windows, apre il bash.exe di WSL in System32 (#6455).
BASH_VERO = shutil.which("bash") or "bash"

CASI = ["FG01", "FG02", "FG03", "FG04", "FG05", "FG06", "FG07", "FG08", "FG09", "FG10", "FG11", "FG12"]
FG = "bin/fine-gia-chiusa.py"
# Sulla base di prima (b54e244) ogni /fine parte: rossi i casi che si aspettano il blocco.
DISCRIMINANTI = ["FG01", "FG05", "FG09"]
AUTO = "/fine chiusura automatica dopo 45 minuti senza messaggi"
# caso -> (file, testo, testo rotto)
VELENI = {
    "FG01": (FG, "    return handoff_dopo(sid.strip(), quando)", "    return None"),
    "FG02": (FG, "                ultimo = None   # un messaggio dopo il /fine", "                pass"),
    "FG03": (FG, "        if riga.search(corpo) and MARCA_AUTO", "        if True and MARCA_AUTO"),
    "FG04": (FG, "and MARCA_AUTO not in corpo.splitlines():", "and True:"),
    "FG05": (FG, "    if any(p in SBLOCCO for p in parole) or parole[:1] == [\"salva\"]:", "    if False:"),
    "FG06": (FG, "            if f.stat().st_mtime < dopo:", "            if False:"),
    "FG07": (FG, "                ultimo = None   # un'altra sessione", "                pass"),
    "FG08": (FG, "    if quando is None:\n        return None\n", "    if quando is None:\n        quando = 0.0\n"),
    "FG09": ("hooks/inject-now.py", 'script("bin/fine-gia-chiusa.py", [], entrata, errori=True) == 2:', 'script("bin/fine-gia-chiusa.py", [], entrata, errori=True) == 99:'),
    "FG10": (FG, "        return 0   # nel dubbio", "        return 2   # nel dubbio"),
    "FG11": (FG, r'r"\s*/(?:arturo:)?fine(?:\s+(.*))?\s*\Z"', r'r"\s*/(?:arturo:)?fine(.*)"'),
    "FG12": (FG, "    if (m.group(1) or \"\").lstrip().startswith(VOLTA):", "    if False:"),
}
ORA = time.time()


def iso(t: float) -> str:
    return datetime.fromtimestamp(t, timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def utente(testo: str, t: float, meta: bool = False, origine: str | None = "human") -> dict:
    r = {"type": "user", "entrypoint": "cli", "timestamp": iso(t), "message": {"role": "user", "content": testo}}
    if meta:
        r["isMeta"] = True
    if origine:
        r["origin"] = {"kind": origine}
    return r


def comando_fine(t: float, args: str = "") -> dict:
    return utente(f"<command-message>fine</command-message>\n<command-name>/fine</command-name>\n"
                  f"<command-args>{args}</command-args>", t)


def risultato(t: float) -> dict:
    return {"type": "user", "timestamp": iso(t), "toolUseResult": {},
            "message": {"role": "user", "content": [{"type": "tool_result", "tool_use_id": "t1", "content": "ok"}]}}


def assistente(t: float) -> dict:
    return {"type": "assistant", "timestamp": iso(t),
            "message": {"role": "assistant", "content": [{"type": "text", "text": "Fatto: handoff scritto."}]}}


def chiusa(t_fine: float) -> list:
    """Una sessione di lavoro chiusa da /fine: dopo il /fine solo meta, risultati di tool e risposte."""
    return [utente("<command-message>inizio</command-message>\n<command-name>/inizio</command-name>\n"
                   "<command-args>mio libro</command-args>", t_fine - 3600),
            utente("# Inizio sessione\nistruzioni", t_fine - 3599, meta=True),
            utente("Riscrivi il capitolo due", t_fine - 3000),
            risultato(t_fine - 2990),
            assistente(t_fine - 2980),
            comando_fine(t_fine, "chiusura automatica dopo 45 minuti senza messaggi"),
            utente("# Fine sessione\ncorpo della skill", t_fine + 1, meta=True),
            risultato(t_fine + 60),
            utente("<local-command-caveat>The command below was run directly</local-command-caveat>",
                   t_fine + 70, meta=True, origine="plugin"),
            assistente(t_fine + 120)]


class Lab:
    def __init__(self, repo: Path, tmp: Path):
        self.home = tmp / "home"
        self.cl = self.home / ".claude"
        self.cl.mkdir(parents=True)
        ignora = shutil.ignore_patterns("__pycache__", "*.local")
        for d in ("bin", "hooks"):
            shutil.copytree(str(repo / d), str(self.cl / d), ignore=ignora)
        self.h = self.cl / "data" / "handoffs" / "mio-libro"
        self.h.mkdir(parents=True)
        self.projects = self.cl / "projects" / "-prova"
        self.projects.mkdir(parents=True)
        self.n = 0

    def env(self) -> dict:
        e = dict(os.environ, HOME=str(self.home), USERPROFILE=str(self.home), ARTURO_TELEMETRIA="0",
                 PYTHONDONTWRITEBYTECODE="1", GIT_CONFIG_GLOBAL=os.devnull)
        for k in ("CLAUDE_CONFIG_DIR", "CLAUDE_CODE_SESSION_ID", "ARTURO_RADICE"):
            e.pop(k, None)
        return e

    def transcript(self, sid: str, record: list) -> Path:
        p = self.projects / f"{sid}.jsonl"
        with open(p, "w", encoding="utf-8") as f:
            for r in record:
                r = dict(r)
                r["sessionId"] = sid
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
        return p

    def handoff(self, sid: str, quando: float, extra: str = "") -> Path:
        self.n += 1
        p = self.h / f"HANDOFF_2026-11-20_17-{self.n:02d}.md"
        p.write_text(f"# Handoff\n\n- Sessione: {sid}\n{extra}\n## Ripartenza\nfatto\n", encoding="utf-8")
        os.utime(p, (quando, quando))
        return p

    def evento(self, sid: str, prompt: str) -> str:
        return json.dumps({"session_id": sid, "transcript_path": str(self.projects / f"{sid}.jsonl"),
                           "cwd": str(self.home), "hook_event_name": "UserPromptSubmit", "prompt": prompt})

    def script(self, dati: str) -> subprocess.CompletedProcess:
        if not (self.cl / FG).is_file():   # la base di prima: nessun controllo, il /fine parte sempre
            return subprocess.CompletedProcess([FG], 0, "", "")
        return subprocess.run([sys.executable, "-B", str(self.cl / FG)], input=dati, capture_output=True, text=True,
                              encoding="utf-8", errors="replace", env=self.env(), timeout=60)

    def ferma(self, sid: str, prompt: str = AUTO) -> subprocess.CompletedProcess:
        return self.script(self.evento(sid, prompt))

    def hook(self, sid: str, prompt: str) -> subprocess.CompletedProcess:
        return subprocess.run([BASH_VERO, str(self.cl / "hooks" / "inject-now.sh")], input=self.evento(sid, prompt),
                              capture_output=True, text=True, encoding="utf-8", errors="replace", env=self.env(),
                              timeout=60)


def prova(lab: Lab) -> list:
    rossi = []
    t_fine = ORA - 1800   # il /fine automatico di mezz'ora fa; l'handoff l'ha scritto due minuti dopo

    def esito(caso: str, r: subprocess.CompletedProcess, atteso: int, nota: str) -> None:
        if r.returncode != atteso:
            rossi.append(f"{caso} {nota}: rc={r.returncode} atteso {atteso} err={r.stderr.strip()[-300:]!r}")

    # FG01: sessione chiusa, il secondo giro si ferma e nomina l'handoff
    lab.transcript("s-chiusa", chiusa(t_fine))
    h = lab.handoff("s-chiusa", t_fine + 120)
    r = lab.ferma("s-chiusa")
    esito("FG01", r, 2, "sessione chiusa")
    if r.returncode == 2 and (h.name not in r.stderr or "--forza" not in r.stderr):
        rossi.append(f"FG01 la riga non nomina l'handoff o lo sblocco: {r.stderr!r}")

    # FG02: un messaggio della persona dopo il /fine
    lab.transcript("s-ripresa", chiusa(t_fine) + [utente("aggiungi una nota al capitolo tre", t_fine + 600)])
    lab.handoff("s-ripresa", t_fine + 120)
    esito("FG02", lab.ferma("s-ripresa"), 0, "messaggio della persona dopo il /fine")

    # FG03: c'è solo l'handoff di un'altra sessione
    lab.transcript("s-senza", chiusa(t_fine))
    lab.handoff("s-altra", t_fine + 120)
    esito("FG03", lab.ferma("s-senza"), 0, "handoff di un'altra sessione")

    # FG04: l'handoff della sessione è un salvataggio automatico
    lab.transcript("s-auto", chiusa(t_fine))
    lab.handoff("s-auto", t_fine + 120, extra="- Salvato: in automatico\n")
    esito("FG04", lab.ferma("s-auto"), 0, "salvataggio automatico")

    # FG05: le parole che chiedono un giro nuovo
    for prompt in ("/fine --forza", "/fine --full", "/fine salva", "/fine --forza chiusura automatica"):
        esito("FG05", lab.ferma("s-chiusa", prompt), 0, f"sblocco {prompt!r}")
    esito("FG05", lab.ferma("s-chiusa", "/fine chiusura automatica: salva e chiudi"), 2, "salva a metà testo")

    # FG06: handoff scritto prima dell'ultimo /fine
    lab.transcript("s-vecchio", chiusa(t_fine))
    lab.handoff("s-vecchio", t_fine - 900)
    esito("FG06", lab.ferma("s-vecchio"), 0, "handoff più vecchio del /fine")

    # FG07: un'altra sessione o un lavoro in background dopo il /fine
    lab.transcript("s-peer", chiusa(t_fine) + [utente("Another Claude session sent a message:\n"
                                                      "<cross-session-message from=\"x\">rifai il push</cross-session-message>",
                                                      t_fine + 600, meta=True, origine="peer")])
    lab.handoff("s-peer", t_fine + 120)
    esito("FG07", lab.ferma("s-peer"), 0, "messaggio di un'altra sessione")
    lab.transcript("s-lavoro", chiusa(t_fine) + [utente("<task-notification>\n<task-id>b1</task-id>",
                                                        t_fine + 600, origine="task-notification")])
    lab.handoff("s-lavoro", t_fine + 120)
    esito("FG07", lab.ferma("s-lavoro"), 0, "lavoro in background finito")

    # FG08: nessun /fine nella trascrizione (per esempio una sessione ripresa dopo un handoff)
    lab.transcript("s-mai", chiusa(t_fine)[:5])
    lab.handoff("s-mai", t_fine + 120)
    esito("FG08", lab.ferma("s-mai"), 0, "trascrizione senza /fine")

    # FG09: inject-now.sh
    esito("FG09", lab.hook("s-chiusa", AUTO), 2, "inject-now.sh su /fine")
    esito("FG09", lab.hook("s-chiusa", "/arturo:fine chiusura automatica"), 2, "inject-now.sh su /arturo:fine")
    esito("FG09", lab.hook("s-chiusa", "/finestra nuova"), 0, "inject-now.sh su /finestra")
    r = lab.hook("s-chiusa", "continua col capitolo quattro")
    esito("FG09", r, 0, "inject-now.sh su un messaggio")
    if "Ora corrente" not in r.stdout:
        rossi.append(f"FG09 inject-now.sh non stampa più l'ora: {r.stdout[:200]!r}")

    # FG10: nel dubbio parte
    esito("FG10", lab.script("{non è json"), 0, "JSON rotto")
    esito("FG10", lab.script(json.dumps({"session_id": "s-chiusa", "prompt": AUTO,
                                         "transcript_path": str(lab.projects / "non-esiste.jsonl")})),
          0, "trascrizione che non esiste")
    rotto = lab.projects / "s-binaria.jsonl"
    rotto.mkdir()
    esito("FG10", lab.script(json.dumps({"session_id": "s-binaria", "prompt": AUTO,
                                         "transcript_path": str(rotto)})), 0, "trascrizione che è una cartella")

    # FG11: solo il comando /fine
    for prompt in ("/finestra", "fine del lavoro", "/fine-coda", "/finale"):
        esito("FG11", lab.ferma("s-chiusa", prompt), 0, f"prompt {prompt!r}")

    # FG12: il congedo di Volta passa, Volta ha il suo controllo e aspetta il turno di /fine
    esito("FG12", lab.ferma("s-chiusa", "/fine congedo da Volta: la sessione era ferma da più di un'ora, a turno "
                                       "finito e senza domande. Niente rotazione, nessuna domanda e nessun menu: "
                                       "salva e chiudi."), 0, "congedo di Volta")
    return rossi


def main() -> int:
    for flusso in (sys.stdout, sys.stderr):  # su Windows la pipe è in cp1252
        if hasattr(flusso, "reconfigure"):
            flusso.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument("--avvelena", action="store_true")
    parser.add_argument("--baseline-ref")
    argomenti = parser.parse_args()
    if argomenti.baseline_ref:
        with tempfile.TemporaryDirectory(prefix="arturo-fg-") as tmp:
            codici = sorted({r.split()[0] for r in prova(Lab(Path(argomenti.repo), Path(tmp)))})
        assert codici == DISCRIMINANTI, f"baseline non discriminante: rossi {codici}, attesi {DISCRIMINANTI}"
        print(f"BASELINE_DISCRIMINANTE={','.join(codici)}")
        return 0
    if argomenti.avvelena:
        inerti = []
        for caso in CASI:
            dove, vecchio, rotto = VELENI[caso]
            with tempfile.TemporaryDirectory(prefix="arturo-fg-") as tmp:
                lab = Lab(Path(argomenti.repo), Path(tmp))
                sorgente = lab.cl / dove
                testo = sorgente.read_text(encoding="utf-8")
                if testo.count(vecchio) != 1:
                    inerti.append(f"{caso}: il punto da rompere compare {testo.count(vecchio)} volte")
                    continue
                sorgente.write_text(testo.replace(vecchio, rotto), encoding="utf-8")
                if not any(r.startswith(caso + " ") for r in prova(lab)):
                    inerti.append(f"{caso}: la rottura non lo fa rosso")
        assert not inerti, "veleni che non attaccano:\n" + "\n".join(inerti)
        print(f"VELENI_ROSSI={','.join(CASI)} veleni={len(CASI)}")
        return 0
    with tempfile.TemporaryDirectory(prefix="arturo-fg-") as tmp:
        rossi = prova(Lab(Path(argomenti.repo), Path(tmp)))
    for r in rossi:
        print("ROSSO", r)
    print(f"/fine su sessione chiusa: {len(CASI) - len(rossi)}/{len(CASI)} casi verdi")
    return 1 if rossi else 0


if __name__ == "__main__":
    sys.exit(main())
