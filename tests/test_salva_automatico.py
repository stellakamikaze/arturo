#!/usr/bin/env python3
"""Il salvataggio automatico di una sessione chiusa senza /fine (bin/salva-automatico.py, M4 della memoria, 15/11/2026).

SV01 chiusura con /fine (un handoff con la riga "- Sessione: <id>", senza la marca): nessun file nuovo.
SV02 chiusura senza /fine: un handoff col nome solito, la marca "- Salvato: in automatico", la riga della
     sessione, l'ultima richiesta, il file scritto e il lavoro aperto della sessione; il gate dell'handoff è verde.
SV03 transcript vuoto (solo /inizio, messaggi meta e /clear): nessun file.
SV04 secondo giro della stessa sessione: riscrive il suo handoff, nessun doppione.
SV05 una richiesta con un segreto non entra nell'handoff.
SV06 una sessione headless (entrypoint sdk-cli) non lascia niente.
SV07 da un worktree in .claude/worktrees/<nome> lo slug è quello del repository, non del worktree.
SV08 hooks/session-end.sh lancia il salvataggio.
SV09 arturo contesto (/inizio) dice "L'ultima volta non hai chiuso con /fine" e riporta le ultime richieste.
SV10 a memoria spenta (ARTURO_MEMORIA=0) nessun file.
SV11 dalla home vale l'ultimo /inizio <nome> che porta a un progetto con handoff.
SV12 una scheda che ha la cartella fra i suoi alias decide lo slug: gli handoff vanno nella cartella del progetto,
     non in una seconda col nome della cartella di lavoro (18/11/2026).
SV13 le correzioni della sessione (arturo correzione) entrano nell'handoff nella sezione "## Correzioni", con la
     skill in uso; una correzione con un segreto non entra; /inizio le riporta; il gate resta verde (21/11/2026, #6277).
SV14 tre salvataggi insieme della stessa sessione, dopo un /fine a metà: un handoff automatico solo. Il 16/11 un
     congedo da Volta ne ha scritti tre uguali alle 12:46, 12:47 e 12:48, uno per minuto libero (#5784).

Veleno: --avvelena rompe bin/salva-automatico.py (o il punto sorvegliato) nella copia di prova, un punto per caso,
ed esce 0 solo se ogni rottura fa rosso il suo caso (VELENI del gate).
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import contextlib
import tempfile
import time
from pathlib import Path

# Il bash del PATH: un "bash" senza percorso, su Windows, apre il bash.exe di WSL in System32 (#6455).
BASH_VERO = shutil.which("bash") or "bash"

CASI = ["SV01", "SV02", "SV03", "SV04", "SV05", "SV06", "SV07", "SV08", "SV09", "SV10", "SV11", "SV12", "SV13", "SV14"]
SA = "bin/salva-automatico.py"
# caso -> (file, testo, testo rotto)
VELENI = {
    "SV01": (SA, "        if not dopo_fine[0] and not dopo_fine[1]:", "        if False:"),
    "SV02": (SA, "             f\"- Sessione: {sid}\", MARCA]", "             f\"- Sessione: {sid}\"]"),
    "SV03": (SA, "    if not richieste_vere and not file:", "    if False:"),
    "SV04": (SA, "    if gia is not None:  # l'handoff automatico della stessa sessione", "    if False:"),
    "SV05": (SA, "            if scanner.trova(una):", "            if False:"),
    "SV06": (SA, "    if letto[\"headless\"]:", "    if False:"),
    "SV07": (SA, "            return p.parent\n", "            return Path(git(cwd, \"rev-parse\", \"--show-toplevel\"))\n"),
    "SV08": ("hooks/session-end.sh", "nohup python3 \"$ARTURO_CODICE/bin/salva-automatico.py\"",
             "true \"$ARTURO_CODICE/bin/salva-automatico.py\""),
    "SV09": ("bin/contesto.py", "        if n == 0 and SALVATO_AUTO in testo.splitlines():", "        if False:"),
    "SV10": (SA, "and not mm.memoria_accesa():", "and False:"),
    "SV11": (SA, "            return slug(m.group(1)), None", "            return \"\", None"),
    "SV12": (SA, "        return slug_del_progetto(cartella), cartella", "        return slug(cartella.name), cartella"),
    "SV13": (SA, "                    correzioni_della_sessione(sid, scanner), dopo)", "                    [], dopo)"),
    "SV14": (SA, "    with chiave_sessione(sid):", "    with contextlib.nullcontext():"),
}
SEGRETO = "ghp_" + "A1b2C3d4E5f6G7h8I9j0K1l2M3n4O5p6Q7r8"


def utente(testo: str, meta: bool = False) -> dict:
    r = {"type": "user", "entrypoint": "cli", "sessionId": "", "message": {"role": "user", "content": testo}}
    if meta:
        r["isMeta"] = True
    return r


def uso(nome: str, inp: dict, tid: str) -> dict:
    return {"type": "assistant", "entrypoint": "cli",
            "message": {"role": "assistant", "content": [{"type": "tool_use", "id": tid, "name": nome, "input": inp}]}}


def risultato(tid: str, testo: str) -> dict:
    return {"type": "user", "entrypoint": "cli", "toolUseResult": {},
            "message": {"role": "user", "content": [{"type": "tool_result", "tool_use_id": tid, "content": testo}]}}


@contextlib.contextmanager
def cartella_prova():
    """Una cartella temporanea che alla fine riprova a cancellarsi per dieci secondi: su Windows un processo che
    l'hook ha lasciato andare lavora ancora lì e la tiene aperta (WinError 32, sonda sul runner, #6455)."""
    tmp = tempfile.mkdtemp(prefix="arturo-sv-")
    try:
        yield tmp
    finally:
        for _ in range(20):
            shutil.rmtree(tmp, ignore_errors=True)
            if not os.path.exists(tmp):
                break
            time.sleep(0.5)


class Lab:
    def __init__(self, repo: Path, tmp: Path):
        self.tmp, self.home = tmp, tmp / "home"
        self.cl = self.home / ".claude"
        self.cl.mkdir(parents=True)
        ignora = shutil.ignore_patterns("__pycache__", "*.local")
        for d in ("bin", "hooks"):
            shutil.copytree(str(repo / d), str(self.cl / d), ignore=ignora)
        self.h = self.cl / "data" / "handoffs"
        self.h.mkdir(parents=True)
        self.projects = self.cl / "projects" / "-prova"
        self.projects.mkdir(parents=True)
        self.base = self.home / "Documents" / "ClaudeCode"
        self.progetto = self.base / "Mio Libro"
        self.progetto.mkdir(parents=True)
        self.git("init", "-q", "-b", "main")
        (self.progetto / "capitolo.md").write_text("uno\n", encoding="utf-8")
        self.git("add", "-A")
        self.git("-c", "user.name=prova", "-c", "user.email=prova@example.invalid", "commit", "-q", "-m", "primo")

    def git(self, *a: str) -> None:
        subprocess.run(["git", "-C", str(self.progetto), *a], check=True, capture_output=True, env=self.env())

    def env(self, **extra) -> dict:
        e = dict(os.environ, HOME=str(self.home), USERPROFILE=str(self.home), ARTURO_TELEMETRIA="0",
                 PYTHONDONTWRITEBYTECODE="1", ARTURO_MEMORIA="1", ARTURO_AGGIORNAMENTI="manuali",
                 ARTURO_TODO=str(self.cl / "data" / "todo" / "eventi.jsonl"), GIT_CONFIG_GLOBAL=os.devnull)
        for k in ("PROJECTS_BASE", "CLAUDE_CONFIG_DIR", "CLAUDE_CODE_SESSION_ID", "ARTURO_RADICE"):
            e.pop(k, None)
        e.update(extra)
        return e

    def transcript(self, sid: str, record: list) -> Path:
        p = self.projects / f"{sid}.jsonl"
        with open(p, "w", encoding="utf-8") as f:
            for r in record:
                r = dict(r)
                r["sessionId"] = sid
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
        return p

    def salva(self, sid: str, cwd: Path, **env) -> subprocess.CompletedProcess:
        dati = {"session_id": sid, "transcript_path": str(self.projects / f"{sid}.jsonl"), "cwd": str(cwd),
                "reason": "prompt_input_exit"}
        return subprocess.run([sys.executable, "-B", str(self.cl / SA)], input=json.dumps(dati), capture_output=True,
                              text=True, encoding="utf-8", errors="replace", env=self.env(**env), timeout=120,
                              cwd=str(cwd))

    def salva_insieme(self, sid: str, cwd: Path, quanti: int) -> list:
        """Lancia quanti salvataggi della stessa sessione nello stesso istante, come i congedi doppi di Volta."""
        dati = json.dumps({"session_id": sid, "transcript_path": str(self.projects / f"{sid}.jsonl"),
                           "cwd": str(cwd), "reason": "prompt_input_exit"})
        processi = [subprocess.Popen([sys.executable, "-B", str(self.cl / SA)], stdin=subprocess.PIPE,
                                     stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8",
                                     errors="replace", env=self.env(), cwd=str(cwd)) for _ in range(quanti)]
        uscite = []
        for pr in processi:
            pr.stdin.write(dati)
            pr.stdin.close()
        for pr in processi:
            pr.wait(timeout=120)
            uscite.append((pr.stdout.read().strip(), pr.stderr.read().strip()[-200:]))
            pr.stdout.close()
            pr.stderr.close()
        return uscite

    def handoff(self, slug: str = "mio-libro") -> list:
        return sorted((self.h / slug).glob("HANDOFF_*.md")) if (self.h / slug).is_dir() else []

    def tutti(self) -> list:
        return sorted(self.h.glob("*/HANDOFF_*.md"))


def lavoro(lab: Lab, scritto: Path) -> list:
    return [utente("<command-message>inizio</command-message>\n<command-name>/inizio</command-name>\n"
                   "<command-args>mio libro</command-args>"),
            utente("# Inizio sessione\nistruzioni lunghe", meta=True),
            utente("Riscrivi il capitolo due con la scena del tram"),
            uso("Write", {"file_path": str(scritto), "content": "due\n"}, "t1"),
            risultato("t1", "ok"),
            uso("TaskCreate", {"subject": "Rileggere la scena del tram"}, "t2"),
            risultato("t2", "Task #1 created successfully: Rileggere la scena del tram"),
            uso("TaskCreate", {"subject": "Sistemare il titolo"}, "t3"),
            risultato("t3", "Task #2 created successfully: Sistemare il titolo"),
            uso("TaskUpdate", {"taskId": "2", "status": "completed"}, "t4"),
            risultato("t4", "ok"),
            utente("Adesso aggiungi il dialogo alla fermata ULTIMA-RICHIESTA"),
            utente("<command-name>/clear</command-name>")]


def prova(lab: Lab) -> list:
    rossi = []
    scritto = lab.progetto / "capitolo-due.md"
    scritto.write_text("due\n", encoding="utf-8")

    # SV01: la sessione ha fatto /fine
    d = lab.h / "mio-libro"
    d.mkdir(parents=True, exist_ok=True)
    fine = d / "HANDOFF_2026-11-01_10-00.md"
    fine.write_text("# Session Handoff\n## Progetto\n- Nome: mio-libro / Status: in progress\n- Sessione: s-fine\n"
                    "## Ripartenza\nProssimo passo: X\n## Task Pendenti\nNessun task pendente\n", encoding="utf-8")
    lab.transcript("s-fine", lavoro(lab, scritto))
    r = lab.salva("s-fine", lab.progetto)
    if lab.handoff() != [fine] or not r.stdout.startswith("NIENTE"):
        rossi.append(f"SV01 con /fine: {[p.name for p in lab.handoff()]} {r.stdout.strip()!r} {r.stderr.strip()[-200:]!r}")

    # SV02: senza /fine
    lab.transcript("s-auto", lavoro(lab, scritto))
    r = lab.salva("s-auto", lab.progetto)
    nuovi = [p for p in lab.handoff() if p != fine]
    testo = nuovi[0].read_text(encoding="utf-8") if len(nuovi) == 1 else ""
    gate = subprocess.run([BASH_VERO, str(lab.cl / "bin" / "handoff-gate.sh"), str(nuovi[0])], capture_output=True,
                          text=True, env=lab.env(), timeout=60) if nuovi else None
    attesi = ["- Salvato: in automatico", "- Sessione: s-auto", "ULTIMA-RICHIESTA", str(scritto),
              "Rileggere la scena del tram", "## Task Pendenti", "Branch: main"]
    if len(nuovi) != 1 or any(a not in testo.splitlines() and a not in testo for a in attesi) \
            or "- Salvato: in automatico" not in testo.splitlines() or "Sistemare il titolo" in testo \
            or not gate or gate.returncode != 0:
        rossi.append(f"SV02 senza /fine: {[p.name for p in nuovi]} mancano={[a for a in attesi if a not in testo]} "
                     f"gate={gate.returncode if gate else None} {(gate.stdout + gate.stderr).strip()[-200:] if gate else ''!r} "
                     f"{r.stdout.strip()!r} {r.stderr.strip()[-300:]!r}")

    # SV09: /inizio lo mostra (prima di SV04, che riscrive lo stesso file)
    c = subprocess.run([sys.executable, "-B", str(lab.cl / "bin" / "contesto.py"), "mio-libro"], capture_output=True,
                       text=True, encoding="utf-8", errors="replace", env=lab.env(), timeout=60, cwd=str(lab.home))
    if "L'ultima volta non hai chiuso con /fine" not in c.stdout or "ULTIMA-RICHIESTA" not in c.stdout \
            or "Rileggere la scena del tram" not in c.stdout:
        rossi.append(f"SV09 /inizio: rc={c.returncode} {c.stdout[-600:]!r} {c.stderr[-200:]!r}")

    # SV04: secondo giro
    r = lab.salva("s-auto", lab.progetto)
    if [p for p in lab.handoff() if p != fine] != nuovi or not nuovi:
        rossi.append(f"SV04 secondo giro: {[p.name for p in lab.handoff()]} {r.stdout.strip()!r}")

    # SV03: transcript vuoto
    prima = lab.tutti()
    lab.transcript("s-vuota", [utente("<command-name>/inizio</command-name>\n<command-args>mio libro</command-args>"),
                               utente("istruzioni", meta=True), utente("<command-name>/clear</command-name>")])
    r = lab.salva("s-vuota", lab.progetto)
    if lab.tutti() != prima:
        rossi.append(f"SV03 vuoto: {[p.name for p in lab.tutti()]} {r.stdout.strip()!r}")

    # SV05: segreto in una richiesta
    lab.transcript("s-segreto", [utente(f"usa questo token {SEGRETO} per il push"), utente("poi fai il commit")])
    r = lab.salva("s-segreto", lab.progetto)
    con = [p for p in lab.tutti() if "- Sessione: s-segreto" in p.read_text(encoding="utf-8")]
    if len(con) != 1 or SEGRETO in con[0].read_text(encoding="utf-8") or "poi fai il commit" not in con[0].read_text(encoding="utf-8"):
        rossi.append(f"SV05 segreto: {[p.name for p in con]} {r.stdout.strip()!r} {r.stderr.strip()[-200:]!r}")

    # SV06: headless
    prima = lab.tutti()
    rec = [dict(utente("riassumi il capitolo"), entrypoint="sdk-cli")]
    lab.transcript("s-headless", rec)
    r = lab.salva("s-headless", lab.progetto)
    if lab.tutti() != prima:
        rossi.append(f"SV06 headless: {r.stdout.strip()!r}")

    # SV10: memoria spenta
    lab.transcript("s-spenta", [utente("scrivi la quarta di copertina")])
    r = lab.salva("s-spenta", lab.progetto, ARTURO_MEMORIA="0")
    if lab.tutti() != prima:
        rossi.append(f"SV10 memoria spenta: {r.stdout.strip()!r}")

    # SV07: worktree
    wt = lab.progetto / ".claude" / "worktrees" / "ramo-prova"
    lab.git("worktree", "add", "-q", "-b", "ramo-prova", str(wt))
    lab.transcript("s-wt", [utente("lavora sul ramo")])
    r = lab.salva("s-wt", wt)
    sbagliati = list(lab.h.glob("ramo-prova/HANDOFF_*.md"))
    giusti = [p for p in lab.handoff() if "- Sessione: s-wt" in p.read_text(encoding="utf-8")]
    if sbagliati or len(giusti) != 1:
        rossi.append(f"SV07 worktree: sbagliati={[str(p) for p in sbagliati]} giusti={len(giusti)} {r.stdout.strip()!r}")

    # SV11: dalla home, con /inizio mio-libro
    lab.transcript("s-home", [utente("<command-name>/inizio</command-name>\n<command-args>mio-libro</command-args>"),
                              utente("dimmi dove eravamo rimasti")])
    r = lab.salva("s-home", lab.home)
    if len([p for p in lab.handoff() if "- Sessione: s-home" in p.read_text(encoding="utf-8")]) != 1:
        rossi.append(f"SV11 dalla home: {r.stdout.strip()!r} {r.stderr.strip()[-200:]!r}")

    # SV12: la scheda con la cartella fra gli alias decide lo slug
    schede = lab.cl / "data" / "memory" / "progetti"
    schede.mkdir(parents=True, exist_ok=True)
    scheda = schede / "progetto-romanzo.md"
    scheda.write_text("---\nname: progetto-romanzo\ndescription: il romanzo\nalias: [mio-libro]\n---\ncorpo\n",
                      encoding="utf-8")
    lab.transcript("s-alias", [utente("rileggi il capitolo quattro")])
    r = lab.salva("s-alias", lab.progetto)
    nel_progetto = [p for p in lab.handoff("romanzo") if "- Sessione: s-alias" in p.read_text(encoding="utf-8")]
    if len(nel_progetto) != 1 or any("- Sessione: s-alias" in p.read_text(encoding="utf-8") for p in lab.handoff()):
        rossi.append(f"SV12 slug dalla scheda: {r.stdout.strip()!r} {r.stderr.strip()[-200:]!r}")
    scheda.unlink()

    # SV13: le correzioni della sessione
    correzioni = lab.cl / "data" / "correzioni"
    correzioni.mkdir(parents=True, exist_ok=True)
    (correzioni / "s-corretta.json").write_text(json.dumps([
        {"testo": "Il saluto è Gentile, mai Egregio", "quando": "2026-11-21T10:00:00", "skill": "lettera-cliente"},
        {"testo": f"il token è {SEGRETO}", "quando": "2026-11-21T10:01:00"},
        {"testo": "Le date per esteso", "quando": "2026-11-21T10:02:00", "skill": "../fuori"}]), encoding="utf-8")
    lab.transcript("s-corretta", [utente("scrivi la lettera alla signora Rossi")])
    r = lab.salva("s-corretta", lab.progetto)
    con = [p for p in lab.handoff() if "- Sessione: s-corretta" in p.read_text(encoding="utf-8")]
    testo = con[0].read_text(encoding="utf-8") if len(con) == 1 else ""
    gate = subprocess.run([BASH_VERO, str(lab.cl / "bin" / "handoff-gate.sh"), str(con[0])], capture_output=True,
                          text=True, env=lab.env(), timeout=60) if con else None
    c = subprocess.run([sys.executable, "-B", str(lab.cl / "bin" / "contesto.py"), "mio-libro"], capture_output=True,
                       text=True, encoding="utf-8", errors="replace", env=lab.env(), timeout=60, cwd=str(lab.home))
    righe = testo.splitlines()
    if "## Correzioni" not in righe or "1. Il saluto è Gentile, mai Egregio [skill: lettera-cliente]" not in righe \
            or "3. Le date per esteso" not in righe or SEGRETO in testo or "fuori" in testo \
            or not gate or gate.returncode != 0 or "Il saluto è Gentile" not in c.stdout:
        rossi.append(f"SV13 correzioni: {testo[-500:]!r} gate={gate.returncode if gate else None} "
                     f"{r.stdout.strip()!r} {r.stderr.strip()[-200:]!r} inizio={c.stdout[-300:]!r}")
    senza = [p for p in lab.tutti() if "- Sessione: s-segreto" in p.read_text(encoding="utf-8")]
    if senza and "## Correzioni" in senza[0].read_text(encoding="utf-8"):
        rossi.append("SV13 correzioni: la sezione esce anche per una sessione senza correzioni")

    # SV14: tre giri insieme della stessa sessione, con un /fine a metà e lavoro dopo
    fine_meta = d / "HANDOFF_2026-11-02_09-55.md"
    fine_meta.write_text("# Session Handoff\n## Progetto\n- Nome: mio-libro / Status: in progress\n- Sessione: s-tre\n"
                         "## Ripartenza\nProssimo passo: X\n## Task Pendenti\nNessun task pendente\n", encoding="utf-8")
    lab.transcript("s-tre", [utente("Riscrivi il capitolo due"),
                             utente("<command-name>/fine</command-name>\n<command-args></command-args>"),
                             utente("Poi aggiungi la nota sul tram DOPO-IL-FINE")])
    uscite = lab.salva_insieme("s-tre", lab.progetto, 3)
    automatici = [p for p in lab.tutti() if p != fine_meta and "- Sessione: s-tre" in p.read_text(encoding="utf-8")]
    if len(automatici) != 1 or "DOPO-IL-FINE" not in automatici[0].read_text(encoding="utf-8"):
        rossi.append(f"SV14 tre giri insieme: {[p.name for p in automatici]} {uscite!r}")

    # SV08: session-end.sh lo lancia
    lab.transcript("s-hook", [utente("chiudi il capitolo tre")])
    dati = json.dumps({"session_id": "s-hook", "transcript_path": str(lab.projects / "s-hook.jsonl"),
                       "cwd": str(lab.progetto), "reason": "prompt_input_exit"})
    subprocess.run([BASH_VERO, str(lab.cl / "hooks" / "session-end.sh")], input=dati, capture_output=True, text=True,
                   env=lab.env(), timeout=60, cwd=str(lab.progetto))
    visto = False
    for _ in range(100):
        if any("- Sessione: s-hook" in p.read_text(encoding="utf-8") for p in lab.handoff()):
            visto = True
            break
        time.sleep(0.1)
    if not visto:
        rossi.append("SV08 session-end.sh: nessun handoff della sessione dopo 10 secondi")
    return rossi


def main() -> int:
    for flusso in (sys.stdout, sys.stderr):  # su Windows la pipe è in cp1252
        if hasattr(flusso, "reconfigure"):
            flusso.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument("--avvelena", action="store_true")
    argomenti = parser.parse_args()
    if argomenti.avvelena:
        inerti = []
        for caso in CASI:
            dove, vecchio, rotto = VELENI[caso]
            with cartella_prova() as tmp:
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
    with cartella_prova() as tmp:
        rossi = prova(Lab(Path(argomenti.repo), Path(tmp)))
    for r in rossi:
        print("ROSSO", r)
    print(f"salvataggio automatico: {len(CASI) - len(rossi)}/{len(CASI)} casi verdi")
    return 1 if rossi else 0


if __name__ == "__main__":
    sys.exit(main())
