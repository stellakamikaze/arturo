#!/usr/bin/env python3
"""HW01-HW05, HW08-HW09: lo stato verso Herdr su Windows (hooks/herdr-stato-windows.py, 25/11/2026, #5639).

Su Windows Claude Code lancia gli hook senza terminale di controllo: herdr-stato.sh non trovava dove scrivere
e lo stato in Herdr restava vuoto. Ora su Windows (OS=Windows_NT) lo sh passa all'aiutante Python, che sale
fino a claude.exe e scrive sulla sua console. Prova dal vero su un PC Windows, sessione prova-5639, 25/11/2026:
due turni, `working` poi `blocked` in Herdr, schermo pulito.

HW01 con OS=Windows_NT lo sh chiama python con l'aiutante accanto e lo stato, anche con le \\ nel percorso.
HW02 se python non parte (rimando del Microsoft Store, 9009) o è di MSYS2 (l'aiutante esce 2), lo sh prova python3.
HW03 fuori da Herdr (senza HC_TERMINAL_ID, anche in background) e con uno stato sconosciuto lo sh non chiama
     nessun python.
HW04 scegli() trova claude.exe fra gli antenati, e si ferma su un PID riusato (padre nato dopo il figlio).
HW05 fuori da Windows l'aiutante esce 2 senza scrivere niente, così lo sh prova l'interprete dopo.
HW06 (#5587) una sessione in background (CLAUDE_JOB_DIR, senza HC_TERMINAL_ID) scrive lo stato in
     ~/.cache/herdr-stato/<job id>, che l'aggancio di Volta legge all'apertura.
HW07 (#5587) uno stato nuovo sostituisce quello di prima nel file.
HW08 in_ordine() scarta uno stato più vecchio dell'ultimo scritto, e non segna l'ora se la scrittura fallisce.
HW09 sali() dà anche il figlio di claude.exe, e con un'ora illeggibile confronta l'ultima ora letta più in basso.

HW10 (#5587) uno stato più vecchio dell'ultima ora (file <job>.ora) si scarta, e un lucchetto rimasto si rompe.
HW11 (#5587) un claude -p figlio (session id che state.json non ha) non scrive; la sessione dopo /clear
     (resumeSessionId) e uno state.json senza sessionId scrivono.
HW12 (#5587) lo stato arriva al tty di ogni claude attach <job id>, anche con un flag o un percorso, una volta
     sola per tty, e non a un attach di un altro job.
HW13 (#5587) un attach via ssh non riceve lo stato.
HW14 (#5587) uno stato ripetuto non riscrive sul tty, uno nuovo sì.
HW15 (#5587) con lo zsh -lic di una scheda di Volta sullo stesso tty, il tempo CPU misurato è quello di claude
     attach (prova dal vero del 25/11/2026: zsh ha il PID più basso ed è fermo).

HW08-HW09 vengono dalla revisione della PR #49 (25/11/2026). HW06-HW07 dalla PR #50 (25/11/2026), HW10-HW14
dalla sua revisione, HW15 dalla prova dal vero.

Sulla base 75082b4 (dev prima della modifica) sono rossi tutti: l'aiutante non c'è.
Solo libreria standard. Nessun modello.
"""
from __future__ import annotations

import argparse
import importlib.util
import os
import shutil
import stat
import subprocess
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from salti_windows import dichiara  # noqa: E402  (i salti contano nell'esito del gate)

CASI = ["HW01", "HW02", "HW03", "HW04", "HW05", "HW06", "HW07", "HW08", "HW09", "HW10", "HW11", "HW12", "HW13",
        "HW14", "HW15"]
DISCRIMINANTI = CASI

FINTO = "#!/bin/sh\nprintf '%s|%s|%s\\n' \"$(basename \"$0\")\" \"$1\" \"$2\" >> \"$REGISTRO\"\nexit {rc}\n"


def _python_finti(cartella: Path, rc_py: int) -> None:
    for nome, rc in (("python", rc_py), ("python3", 0)):
        p = cartella / nome
        p.write_text(FINTO.format(rc=rc), encoding="utf-8")
        p.chmod(p.stat().st_mode | stat.S_IEXEC)


def _lancia(script: str, stato: str, d: Path, rc_py: int = 0, hc: str = "t1", job: str = "") -> list:
    finti = d / "finti"
    finti.mkdir(exist_ok=True)
    _python_finti(finti, rc_py)
    registro = d / "registro.txt"
    registro.write_text("", encoding="utf-8")
    env = {"PATH": f"{finti}:/usr/bin:/bin", "OS": "Windows_NT", "REGISTRO": str(registro), "HC_TERMINAL_ID": hc}
    if job:
        env["CLAUDE_JOB_DIR"] = job
    subprocess.run(["sh", script, stato], input=b"{}", env=env, capture_output=True, timeout=20)
    return [r for r in registro.read_text(encoding="utf-8").splitlines() if r]


def _job(script: Path, stati: list, d: Path) -> str:
    casa = d / "casa"
    casa.mkdir(exist_ok=True)
    env = {"PATH": "/usr/bin:/bin", "HOME": str(casa), "USERPROFILE": str(casa), "CLAUDE_JOB_DIR": str(d / "jobs" / "ab12cd34")}
    for x in stati:
        subprocess.run(["sh", str(script), x], input=b"{}", env=env, capture_output=True, timeout=20)
    f = casa / ".cache" / "herdr-stato" / "ab12cd34"
    return f.read_text(encoding="utf-8").strip() if f.is_file() else ""


# ps finto: l'elenco dei processi viene da un file, il tempo CPU è fermo (claude attach non disegna). I PID
# sono alti, così su Linux non c'è un /proc/<pid> vero che li confonde.
# Ogni PID di cui l'hook chiede il tempo CPU va in <elenco>.cpu (HW15).
PS_FINTO = ("#!/bin/sh\ncase \"$*\" in *-Ao*) cat \"$PS_ELENCO\" ;;\n"
            "  *time=*) echo \"$4\" >> \"$PS_ELENCO.cpu\"; echo 0:00.10 ;; esac\nexit 0\n")
OSC = "\033]7501;state={}:app=claude-code\033\\"


class Banco:
    """Una casa, un job e un /dev finti per l'hook di una sessione in background."""

    def __init__(self, script: Path, d: Path, elenco: str = "", stato_json: str = '{"sessionId": "S1"}'):
        self.script, self.d = script, d
        self.casa, self.dev, finti = d / "casa", d / "dev", d / "finti-ps"
        for x in (self.casa, self.dev, finti):
            x.mkdir(exist_ok=True)
        self.jobdir = d / "jobs" / "ab12cd34"
        self.jobdir.mkdir(parents=True, exist_ok=True)
        if stato_json:
            (self.jobdir / "state.json").write_text(stato_json, encoding="utf-8")
        ps = finti / "ps"
        ps.write_text(PS_FINTO, encoding="utf-8")
        ps.chmod(ps.stat().st_mode | stat.S_IEXEC)
        (d / "elenco.txt").write_text(elenco, encoding="utf-8")
        self.path = f"{finti}:/usr/bin:/bin"
        self.cache = self.casa / ".cache" / "herdr-stato"

    def lancia(self, x: str, sid: str = "S1", stdin_sid: str = "") -> None:
        env = {"PATH": self.path, "HOME": str(self.casa), "USERPROFILE": str(self.casa), "CLAUDE_JOB_DIR": str(self.jobdir),
               "PS_ELENCO": str(self.d / "elenco.txt"), "HERDR_STATO_DEV": str(self.dev)}
        if sid:
            env["CLAUDE_CODE_SESSION_ID"] = sid
        ingresso = ('{"session_id": "%s", "hook_event_name": "Stop"}' % stdin_sid) if stdin_sid else "{}"
        subprocess.run(["sh", str(self.script), x], input=ingresso.encode(), env=env, capture_output=True, timeout=20)

    def stato(self) -> str:
        f = self.cache / "ab12cd34"
        return f.read_text(encoding="utf-8").strip() if f.is_file() else ""

    def tty(self, nome: str) -> str:
        f = self.dev / nome
        return f.read_text(encoding="utf-8") if f.is_file() else ""

    def aspetta(self, nome: str, testo: str, secondi: float = 4.0) -> bool:
        fine = time.monotonic() + secondi
        while time.monotonic() < fine:
            if self.tty(nome).endswith(testo):
                return True
            time.sleep(0.05)
        return False


def prova_sfondo(sh: Path) -> list:
    rossi = []
    with tempfile.TemporaryDirectory() as t:
        b = Banco(sh, Path(t))
        b.lancia("working")
        b.cache.mkdir(parents=True, exist_ok=True)
        (b.cache / "ab12cd34.ora").write_text("8000000000000000000\n", encoding="utf-8")
        b.lancia("blocked")
        vecchio = b.stato()
        (b.cache / "ab12cd34.ora").write_text("0\n", encoding="utf-8")
        (b.cache / "ab12cd34.lock").mkdir()
        b.lancia("done")
        if vecchio != "working" or b.stato() != "done" or (b.cache / "ab12cd34.lock").exists():
            rossi.append(f"HW10 l'ordine non scarta lo stato vecchio o il lucchetto resta: {vecchio} {b.stato()}")
    esiti = {}
    for nome, json_stato, sid, stdin_sid in (("figlio", '{"sessionId": "S1", "resumeSessionId": "S2"}', "S1", "S3"),
                                              ("clear", '{"sessionId": "S1", "resumeSessionId": "S2"}', "S2", ""),
                                              ("formato", '{"id": "S1"}', "", "S3")):
        with tempfile.TemporaryDirectory() as t:
            b = Banco(sh, Path(t), stato_json=json_stato)
            b.lancia("working", sid=sid, stdin_sid=stdin_sid)
            esiti[nome] = b.stato()
    if esiti != {"figlio": "", "clear": "working", "formato": "working"}:
        rossi.append(f"HW11 il figlio scrive o la sessione vera no: {esiti}")
    elenco = "".join(f"{r}\n" for r in (
        "3999901 ttys009 ssh amaltea claude attach ab12cd34",
        "3999902 ttys008 claude attach zz99ee88",
        "3999903 ?? claude attach ab12cd34",
        "3999904 ttys001 claude attach ab12cd34",
        "3999905 ttys001 claude attach ab12cd34",
        "3999906 ttys002 /opt/bin/claude attach --quiet ab12cd34",
    ))
    with tempfile.TemporaryDirectory() as t:
        b = Banco(sh, Path(t), elenco=elenco)
        inizio = time.monotonic()
        b.lancia("working")
        durata = time.monotonic() - inizio
        arrivato = b.aspetta("ttys002", OSC.format("working"))
        time.sleep(0.2)
        uno, due = b.tty("ttys001"), b.tty("ttys002")
        if not arrivato or uno != OSC.format("working") or due != OSC.format("working") or b.tty("ttys008"):
            rossi.append(f"HW12 lo stato non arriva una volta a ogni attach del job: {uno!r} {due!r} {b.tty('ttys008')!r}")
        elif durata > 2:
            rossi.append(f"HW12 l'hook aspetta il processo che scrive sui tty: {durata:.1f} s")
        if b.tty("ttys009"):
            rossi.append("HW13 un attach via ssh riceve lo stato")
        b.lancia("working")
        time.sleep(0.5)
        ripetuto = b.tty("ttys001")
        b.lancia("blocked")
        nuovo = b.aspetta("ttys001", OSC.format("blocked"))
        if ripetuto != OSC.format("working") or not nuovo:
            rossi.append(f"HW14 lo stato ripetuto riscrive o quello nuovo non arriva: {ripetuto!r} {b.tty('ttys001')!r}")
    # La riga di una scheda di Volta: zsh -lic col PID più basso, poi claude attach sullo stesso tty.
    elenco = "".join(f"{r}\n" for r in (
        "3999910 ttys003 /bin/zsh -lic \"$@\"; exec \"$0\" -li /bin/zsh /usr/bin/env VOLTA_DA=M /opt/bin/claude attach ab12cd34",
        "3999911 ttys003 /opt/bin/claude attach ab12cd34",
    ))
    with tempfile.TemporaryDirectory() as t:
        b = Banco(sh, Path(t), elenco=elenco)
        b.lancia("working")
        arrivato = b.aspetta("ttys003", OSC.format("working"))
        cpu = Path(t) / "elenco.txt.cpu"
        chiesti = set(cpu.read_text(encoding="utf-8").split()) if cpu.is_file() else set()
        if not arrivato or chiesti != {"3999911"} or b.tty("ttys003") != OSC.format("working"):
            rossi.append(f"HW15 il tempo CPU non è quello di claude attach: PID {sorted(chiesti)} {b.tty('ttys003')!r}")
    return rossi


def prova(repo: Path) -> list:
    rossi = []
    sh = repo / "hooks" / "herdr-stato.sh"
    aiuto = repo / "hooks" / "herdr-stato-windows.py"
    if not aiuto.is_file():
        return [f"{c} manca hooks/herdr-stato-windows.py" for c in CASI]
    with tempfile.TemporaryDirectory() as t:
        d = Path(t)
        hooks = d / "hooks"
        shutil.copytree(repo / "hooks", hooks, ignore=shutil.ignore_patterns("__pycache__"))
        righe = _lancia(str(hooks / "herdr-stato.sh"), "working", d)
        if righe != [f"python|{hooks}/herdr-stato-windows.py|working"]:
            rossi.append(f"HW01 lo sh non chiama l'aiutante con python: {righe}")
        else:
            # Le \ del percorso di Windows: su POSIX un file che ha le \ nel nome.
            shutil.copy(hooks / "herdr-stato.sh", d / "a\\b\\herdr-stato.sh")
            righe = _lancia(str(d / "a") + "\\b\\herdr-stato.sh", "idle", d)
            if righe != [f"python|{d}/a\\b/herdr-stato-windows.py|idle"]:
                rossi.append(f"HW01 con le \\ nel percorso la cartella dell'aiutante è sbagliata: {righe}")
        for rc in (9009 % 256, 2):
            righe = _lancia(str(hooks / "herdr-stato.sh"), "blocked", d, rc_py=rc)
            if [r.split("|")[0] for r in righe] != ["python", "python3"]:
                rossi.append(f"HW02 con python che esce {rc} lo sh non prova python3: {righe}")
        senza = _lancia(str(hooks / "herdr-stato.sh"), "working", d, hc="")
        ignoto = _lancia(str(hooks / "herdr-stato.sh"), "boh", d)
        sfondo = _lancia(str(hooks / "herdr-stato.sh"), "working", d, hc="", job=str(d / "jobs" / "ab12cd34"))
        if senza or ignoto or sfondo:
            rossi.append(f"HW03 lo sh chiama python fuori da Herdr o con uno stato ignoto: {senza} {ignoto} {sfondo}")
    with tempfile.TemporaryDirectory() as t:
        if _job(sh, ["working"], Path(t)) != "working":
            rossi.append("HW06 la sessione in background senza HC_TERMINAL_ID non scrive lo stato in ~/.cache/herdr-stato")
    with tempfile.TemporaryDirectory() as t:
        if _job(sh, ["working", "blocked", "done"], Path(t)) != "done":
            rossi.append("HW07 lo stato nuovo non sostituisce quello di prima in ~/.cache/herdr-stato")
    rossi += prova_sfondo(sh)
    spec = importlib.util.spec_from_file_location("herdr_stato_windows", aiuto)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    padri = {10: (9, "python.exe"), 9: (8, "sh.exe"), 8: (7, "bash.exe"), 7: (6, "claude.exe"), 6: (5, "pwsh.exe"),
             5: (0, "herdr-core.exe")}
    nati = {10: 100, 9: 90, 8: 80, 7: 70, 6: 60, 5: 50}
    if m.scegli(padri, 10, nati.get) != 7:
        rossi.append(f"HW04 scegli() non trova claude.exe: {m.scegli(padri, 10, nati.get)}")
    riuso = {**nati, 8: 500}
    if m.scegli(padri, 10, riuso.get) is not None:
        rossi.append("HW04 scegli() sale oltre un PID riusato (padre nato dopo il figlio)")
    # Un figlio illeggibile (None) non spegne il controllo: il padre nato dopo l'ultima ora letta è un PID riusato.
    buco = {**nati, 9: None, 8: 150}
    sali = getattr(m, "sali", None)
    if sali is None or sali(padri, 10, nati.get) != (7, 8):
        rossi.append(f"HW09 sali() non dà claude.exe e il suo figlio: {sali and sali(padri, 10, nati.get)}")
    elif m.scegli(padri, 10, buco.get) is not None:
        rossi.append("HW09 con un'ora illeggibile scegli() sale oltre un PID riusato")
    if not hasattr(m, "in_ordine"):
        rossi.append("HW08 manca in_ordine()")
    else:
        with tempfile.TemporaryDirectory() as t:
            f = Path(t) / "ordine.txt"
            scritti = []
            esiti = [m.in_ordine(f, ora, lambda o=ora: scritti.append(o) or True) for ora in (200, 100, 300)]
            fallita = m.in_ordine(f, 400, lambda: False)
            dopo = m.in_ordine(f, 350, lambda: scritti.append(350) or True)
            if esiti != [True, False, True] or fallita or not dopo or scritti != [200, 300, 350]:
                rossi.append(f"HW08 in_ordine() non scarta gli stati vecchi: {esiti} {fallita} {dopo} {scritti}")
    if sys.platform != "win32":
        p = subprocess.run([sys.executable, str(aiuto), "working"], capture_output=True, timeout=20)
        if p.returncode != 2 or p.stdout or p.stderr:
            rossi.append(f"HW05 fuori da Windows l'aiutante non tace: rc={p.returncode} {p.stdout[:80]!r} {p.stderr[-120:]!r}")
    return sorted(rossi)


def main() -> int:
    for flusso in (sys.stdout, sys.stderr):
        if hasattr(flusso, "reconfigure"):
            flusso.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument("--baseline-ref")
    a = parser.parse_args()
    if os.name == "nt":
        dichiara("HW01-HW09", "sh e python finti sono script di POSIX senza estensione")
        return 0
    rossi = prova(Path(a.repo).resolve())
    if a.baseline_ref:
        codici = sorted({r.split()[0] for r in rossi})
        assert codici == DISCRIMINANTI, f"baseline non discriminante: rossi {codici}, attesi {DISCRIMINANTI}"
        print(f"BASELINE_DISCRIMINANTE={','.join(codici)}")
        return 0
    for r in rossi:
        print("ROSSO", r)
    print(f"stato Herdr su Windows: {len(CASI) - len(rossi)}/{len(CASI)} casi verdi")
    return 1 if rossi else 0


if __name__ == "__main__":
    sys.exit(main())
