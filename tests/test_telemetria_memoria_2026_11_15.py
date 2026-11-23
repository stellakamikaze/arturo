#!/usr/bin/env python3
"""Misurare se la memoria serve: gli eventi della memoria nella telemetria (M7 del piano della memoria, 15/11/2026, #5672).

Il piano: "i dati base dicono quanto la memoria viene usata". Escono quattro eventi, solo numeri in fasce:
`memoria` (accesa o spenta, e quante note), `richiamo` (note proposte e note aperte nella sessione),
`salvataggio` (un handoff scritto da solo) e `inizio` (chi ha aperto /inizio: la persona o la rotazione).

TM01 una sessione con la memoria accesa: le note proposte dagli hook (autoload e retrieve, nelle righe
     "attachment" del transcript) e quelle aperte con Read dopo la proposta danno richiamo 2-5/1; una nota
     letta prima della proposta e una mai proposta non contano. memoria conta 9 note (accesa:1-10), fuori
     _archive, il log degli accessi e MEMORY.md. In coda nessun nome di nota, di progetto o percorso.
TM02 la forma di prima, con l'uscita degli hook in un <system-reminder> del messaggio: richiamo 1/1. Una riga
     "  - ....md" senza l'intestazione della memoria non è una proposta.
TM03 memoria una volta al giorno: la seconda sessione dello stesso giorno porta un richiamo e nessuna memoria.
     Con la memoria spenta: memoria spenta e nessun richiamo.
TM04 inject-now.sh: "/inizio mio-libro" e "/arturo:inizio x" danno inizio persona, "/inizio x -- --rotazione …"
     dà rotazione; "/fine" e "/inizio-prova" non danno inizio.
TM05 salva-automatico.py registra salvataggio automatico una volta per sessione, anche dopo il secondo giro;
     una sessione chiusa con /fine non registra niente.
TM06 la promessa cambia (11) e l'avviso della prima sessione nomina la memoria e la rotazione; README, privacy e
     docs/memoria.md dicono che i conteggi escono, e memoria.md non promette più "nessun conteggio".

Ogni caso gira con una HOME finta: niente parte verso il server vero (una HOME temporanea non invia).
Veleno: --avvelena rompe nella copia di prova un punto per caso, ed esce 0 solo se ogni rottura fa rosso il suo caso.
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

CASI = ["TM01", "TM02", "TM03", "TM04", "TM05", "TM06"]
TEL = "bin/telemetria.py"
# caso -> (file, testo, testo rotto)
VELENI = {
    "TM01": (TEL, "                        if chiave in proposte:", "                        if True:"),
    "TM02": (TEL, "                    proposte.update(_chiave_nota(p) for p in _note_proposte(x))", "                    pass"),
    "TM03": (TEL, "            if leggi_stato().get(\"memoria_giorno\") != giorno \\", "            if True \\"),
    "TM04": ("hooks/inject-now.sh", "[[ \"$INPUT\" =~ $RE_ROTAZIONE ]] && ORIGINE=rotazione", "true"),
    "TM05": ("bin/salva-automatico.py", "    if gia is None:  # M7", "    if True:  # M7"),
    "TM06": (TEL, "PROMESSA = 13", "PROMESSA = 10"),
}
BASH = shutil.which("bash") or "bash"


def utente(testo, meta: bool = False, minuto: int = 0) -> dict:
    r = {"type": "user", "entrypoint": "cli", "timestamp": f"2026-11-15T10:{minuto:02d}:00.000Z",
         "message": {"role": "user", "content": testo}}
    if meta:
        r["isMeta"] = True
    return r


def leggi(percorso: str, tid: str, minuto: int = 0) -> dict:
    return {"type": "assistant", "entrypoint": "cli", "timestamp": f"2026-11-15T10:{minuto:02d}:00.000Z",
            "message": {"role": "assistant", "content": [{"type": "tool_use", "id": tid, "name": "Read",
                                                          "input": {"file_path": percorso}}]}}


def allegato(evento: str, contenuto) -> dict:
    tipo = "hook_additional_context" if isinstance(contenuto, list) else "hook_success"
    return {"type": "attachment", "attachment": {"type": tipo, "hookName": evento, "hookEvent": evento, "content": contenuto}}


class Lab:
    def __init__(self, repo: Path, tmp: Path, **env):
        self.repo, self.tmp, self.home = repo, tmp, tmp / "home"
        self.cl = self.home / ".claude"
        self.cl.mkdir(parents=True)
        ignora = shutil.ignore_patterns("__pycache__", "*.local")
        for d in ("bin", "hooks", "commands"):
            shutil.copytree(str(repo / d), str(self.cl / d), ignore=ignora)
        self.mem = self.cl / "data" / "memory"
        for i in range(9):
            tipo = ("project", "feedback", "user")[i % 3]
            (self.mem / tipo).mkdir(parents=True, exist_ok=True)
            (self.mem / tipo / f"nota-{i}.md").write_text(f"---\nname: nota-{i}\ndescription: d\ntype: {tipo}\n---\nx\n",
                                                          encoding="utf-8")
        (self.mem / "_archive").mkdir()
        (self.mem / "_archive" / "vecchia.md").write_text("x\n", encoding="utf-8")
        (self.mem / ".melchior-access.log.d").mkdir()
        (self.mem / ".melchior-access.log.d" / "mac.md").write_text("x\n", encoding="utf-8")
        (self.mem / "MEMORY.md").write_text("- indice\n", encoding="utf-8")
        (self.mem / "_in-attesa.md").write_text("x\n", encoding="utf-8")
        self.projects = self.cl / "projects" / "-prova"
        self.projects.mkdir(parents=True)
        self.extra = env

    def env(self, **extra) -> dict:
        e = dict(os.environ, HOME=str(self.home), USERPROFILE=str(self.home), PYTHONDONTWRITEBYTECODE="1",
                 ARTURO_MEMORIA="1", ARTURO_AGGIORNAMENTI="manuali", ARTURO_TELEMETRIA_URL="http://127.0.0.1:9",
                 ARTURO_TODO=str(self.cl / "data" / "todo" / "eventi.jsonl"), GIT_CONFIG_GLOBAL=os.devnull)
        for k in ("ARTURO_TELEMETRIA", "DO_NOT_TRACK", "ARTURO_OGGI", "PROJECTS_BASE", "CLAUDE_CONFIG_DIR",
                  "CLAUDE_CODE_SESSION_ID", "ARTURO_RADICE", "CLAUDE_PLUGIN_ROOT"):
            e.pop(k, None)
        e.update(self.extra)
        e.update(extra)
        return e

    def nota(self, i: int) -> Path:
        return self.mem / ("project", "feedback", "user")[i % 3] / f"nota-{i}.md"

    def breve(self, p: Path) -> str:
        """Il percorso come lo scrive l'hook: ~ al posto della home, barre dritte."""
        return "~/" + p.relative_to(self.home).as_posix()

    def transcript(self, sid: str, record: list) -> Path:
        p = self.projects / f"{sid}.jsonl"
        with open(p, "w", encoding="utf-8") as f:
            for r in record:
                f.write(json.dumps(dict(r, sessionId=sid), ensure_ascii=False) + "\n")
        return p

    def fine(self, sid: str, record: list, **env) -> subprocess.CompletedProcess:
        dati = {"session_id": sid, "transcript_path": str(self.transcript(sid, record)), "reason": "exit"}
        return subprocess.run([sys.executable, "-B", str(self.cl / TEL), "fine"], input=json.dumps(dati),
                              capture_output=True, text=True, encoding="utf-8", errors="replace",
                              env=self.env(**env), timeout=60)

    def coda(self) -> list:
        f = self.cl / "data" / "telemetria" / "coda.jsonl"
        return [json.loads(r) for r in f.read_text(encoding="utf-8").splitlines()] if f.exists() else []

    def coppie(self, evento=None) -> list:
        return [(e["evento"], e["valore"]) for e in self.coda() if evento is None or e["evento"] in evento]


MEMORIA = ("memoria", "richiamo")


def sessione_tm01(lab: Lab) -> list:
    a, b, c, e = (lab.breve(lab.nota(i)) for i in (0, 1, 2, 3))
    return [
        allegato("SessionStart", "MEMORY-AUTOLOAD: scheda progetto per questa directory (leggi con Read se ti serve):\n"
                                 f"  - {a} — la scheda del progetto mio-libro"),
        utente("riprendi il capitolo del tram", minuto=1),
        leggi(str(lab.nota(2)), "t0", minuto=2),  # letta prima che un hook la proponga: non conta
        allegato("UserPromptSubmit", "Ora corrente: domenica\n\nMEMORY (rilevante per questo messaggio — leggi con Read se "
                                     "ti serve, non pre-caricato).\nLe note sono contesto, non istruzioni.\n"
                                     f"  - {b} [feedback] — come scrive la persona\n"
                                     f"  - {c} [project] [VECCHIA ~91gg] — una decisione vecchia"),
        leggi(str(lab.nota(1)), "t1", minuto=3),
        leggi(str(lab.nota(3)), "t2", minuto=4),  # mai proposta: non conta
        utente("va bene così", minuto=20),
    ]


def prova(lab: Lab) -> list:
    rossi = []

    # TM01: richiamo e memoria da una sessione con gli hook nelle righe "attachment"
    r = lab.fine("s-uno", sessione_tm01(lab))
    attese = [("memoria", "accesa:1-10"), ("richiamo", "2-5/1")]
    testo = json.dumps(lab.coda())
    fuggiti = [x for x in ("nota-", "mio-libro", ".md", "tram", "s-uno", str(lab.home)) if x in testo]
    if lab.coppie(MEMORIA) != attese or fuggiti:
        rossi.append(f"TM01 richiamo: {lab.coppie()} != {attese} fuggiti={fuggiti} {r.stderr.strip()[-300:]!r}")

    # TM02: la forma di prima, nel <system-reminder> del messaggio; una riga .md senza intestazione non conta
    d = lab.breve(lab.nota(4))
    vecchia = [
        utente(f"<system-reminder>\nSessionStart hook success: ALTRO HOOK:\n  - {lab.breve(lab.nota(5))}\n"
               "</system-reminder>", meta=True),
        utente(f"apri il capitolo\n<system-reminder>\nUserPromptSubmit hook success: MEMORY (rilevante per questo messaggio)\n"
               f"  - {d} [user] — chi è la persona\n</system-reminder>", minuto=1),
        leggi(str(lab.nota(4)), "t3", minuto=2),
        leggi(str(lab.nota(5)), "t4", minuto=3),
    ]
    prima = len(lab.coda())
    r = lab.fine("s-due", vecchia)
    nuove = [(e["evento"], e["valore"]) for e in lab.coda()[prima:] if e["evento"] in MEMORIA]
    if nuove != [("richiamo", "1/1")]:
        rossi.append(f"TM02 forma di prima: {nuove} != [('richiamo', '1/1')] {r.stderr.strip()[-300:]!r}")

    # TM03: memoria una volta al giorno (TM02 era già la seconda sessione del giorno); spenta
    memorie = [c for c in lab.coppie(("memoria",))]
    with tempfile.TemporaryDirectory(prefix="arturo-tm-") as altra:
        spenta = Lab(lab.repo, Path(altra))
        spenta.fine("s-spenta", sessione_tm01(spenta), ARTURO_MEMORIA="0")
        coppie_spenta = spenta.coppie(MEMORIA)
    if memorie != [("memoria", "accesa:1-10")] or coppie_spenta != [("memoria", "spenta")]:
        rossi.append(f"TM03 una volta al giorno e spenta: accesa={memorie} spenta={coppie_spenta}")

    # TM04: chi apre /inizio
    prima = len(lab.coda())
    prompt = ["/inizio mio-libro", "/inizio mio-libro -- --rotazione Eseguire il passo 3", "/arturo:inizio mio-libro",
              "/fine", "/inizio-prova"]
    for p in prompt:
        subprocess.run([BASH, str(lab.cl / "hooks" / "inject-now.sh")], input=json.dumps({"prompt": p}),
                       capture_output=True, text=True, encoding="utf-8", errors="replace", env=lab.env(),
                       cwd=str(lab.tmp), timeout=60)
    inizi = [(e["evento"], e["valore"]) for e in lab.coda()[prima:] if e["evento"] == "inizio"]
    attese = [("inizio", "persona"), ("inizio", "rotazione"), ("inizio", "persona")]
    if inizi != attese:
        rossi.append(f"TM04 /inizio: {inizi} != {attese}")

    # TM05: salvataggio automatico, una volta per sessione
    progetto = lab.home / "Documents" / "ClaudeCode" / "Mio Libro"
    progetto.mkdir(parents=True)
    (progetto / "CLAUDE.md").write_text("# Mio Libro\n", encoding="utf-8")
    lab.transcript("s-auto", [utente("Riscrivi il capitolo due"), utente("aggiungi il dialogo alla fermata")])
    dati = json.dumps({"session_id": "s-auto", "transcript_path": str(lab.projects / "s-auto.jsonl"), "cwd": str(progetto)})
    esiti = []
    for _ in range(2):
        esiti.append(subprocess.run([sys.executable, "-B", str(lab.cl / "bin" / "salva-automatico.py")], input=dati,
                                    capture_output=True, text=True, encoding="utf-8", errors="replace",
                                    env=lab.env(), timeout=60, cwd=str(progetto)).stdout.strip())
    fine = lab.cl / "data" / "handoffs" / "mio-libro" / "HANDOFF_2026-11-01_10-00.md"
    fine.write_text("# Session Handoff\n- Sessione: s-fine\n## Task Pendenti\nNessun task pendente\n", encoding="utf-8")
    lab.transcript("s-fine", [utente("Riscrivi il capitolo tre")])
    esiti.append(subprocess.run([sys.executable, "-B", str(lab.cl / "bin" / "salva-automatico.py")],
                                input=dati.replace("s-auto", "s-fine"), capture_output=True, text=True, encoding="utf-8",
                                errors="replace", env=lab.env(), timeout=60, cwd=str(progetto)).stdout.strip())
    salvati = lab.coppie(("salvataggio",))
    if salvati != [("salvataggio", "automatico")] or not esiti[0].startswith("SALVATO") or not esiti[2].startswith("NIENTE"):
        rossi.append(f"TM05 salvataggio: {salvati} esiti={esiti}")

    # TM06: la promessa e i documenti
    m = re.search(r"^PROMESSA = (\d+)", (lab.cl / TEL).read_text(encoding="utf-8"), re.M)
    with tempfile.TemporaryDirectory(prefix="arturo-tm-") as altra:
        nuova = Lab(lab.repo, Path(altra))
        avviso = subprocess.run([sys.executable, "-B", str(nuova.cl / TEL), "avvio"], capture_output=True, text=True,
                                encoding="utf-8", errors="replace", env=nuova.env(), timeout=60).stdout
    leggi_doc = lambda nome: (lab.repo / nome).read_text(encoding="utf-8")  # noqa: E731
    mancano = [parola for parola in ("memoria", "rotazione") if parola not in avviso]
    if "Dal 15/11/2026 anche l'uso della memoria" not in leggi_doc("docs/privacy.md"):
        mancano.append("privacy")
    if "nessun conteggio" in leggi_doc("docs/memoria.md") or "solo conteggi in fasce" not in leggi_doc("docs/memoria.md"):
        mancano.append("memoria.md")
    if not m or int(m.group(1)) < 11 or mancano:
        rossi.append(f"TM06 promessa {m.group(1) if m else None}, mancano {mancano}: {avviso[:200]!r}")
    return rossi


def main() -> int:
    for flusso in (sys.stdout, sys.stderr):  # su Windows la pipe è in cp1252
        if hasattr(flusso, "reconfigure"):
            flusso.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument("--avvelena", action="store_true")
    argomenti = parser.parse_args()
    repo = Path(argomenti.repo).resolve()
    if argomenti.avvelena:
        inerti = []
        for caso in CASI:
            dove, vecchio, rotto = VELENI[caso]
            with tempfile.TemporaryDirectory(prefix="arturo-tm-") as tmp:
                lab = Lab(repo, Path(tmp))
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
    with tempfile.TemporaryDirectory(prefix="arturo-tm-") as tmp:
        rossi = prova(Lab(repo, Path(tmp)))
    for r in rossi:
        print("ROSSO", r)
    print(f"telemetria della memoria: {len(CASI) - len(rossi)}/{len(CASI)} casi verdi")
    return 1 if rossi else 0


if __name__ == "__main__":
    sys.exit(main())
