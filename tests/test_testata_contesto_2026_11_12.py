#!/usr/bin/env python3
"""Testata di Volta e contesto del progetto (12/11/2026, Federico: "la sintesi della sessione in massimo
5 parole, aggiornata costantemente" e "una sorta di back-end del catalogo dei progetti").

TC01 `arturo contesto <slug> --json` dà le fonti nell'ordine di lettura (istruzioni di tutte le sessioni,
     indice della memoria, istruzioni del progetto, scheda, quadro di /inizio, ultimo handoff, note
     collegate), ognuna col suo file, i caratteri giusti e le prime righe.
TC02 il nome alternativo della scheda (`alias:`) porta al progetto vero: "volta" apre herdr-arturo.
TC03 un progetto che non esiste dà un JSON valido con un avviso e le fonti assenti segnate "presente": false.
TC04 il comando non scrive: l'albero della HOME di prova è identico prima e dopo.
TC05 titolo-sessione.py legge le due righe del modello (TITOLO: e ADESSO:); la sintesi ha da 2 a 5
     parole, senza virgolette né punto finale; una riga sola senza etichette vale come titolo.
TC06 su PostToolUse l'hook scrive la sintesi; un secondo PostToolUse subito dopo non chiama il modello;
     sotto un nome scritto dalla persona cambia la sintesi e il titolo resta; una risposta senza ADESSO
     sposta comunque il turno della sintesi.

Veleno: --avvelena rompe la copia di prova, un punto per caso, ed esce 0 solo se ogni rottura fa rosso
il suo caso.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

CASI = ["TC01", "TC02", "TC03", "TC04", "TC05", "TC06"]
# caso -> (file, testo giusto, testo rotto)
VELENI = [
    ("TC01", "bin/contesto.py", 'fonte("handoff", "Ultimo handoff"', 'fonte("handoff-x", "Ultimo handoff"'),
    ("TC01", "bin/contesto.py", '"anteprima": [corto(r, 140) for r in righe if r.strip()][:6]', '"anteprima": []'),
    ("TC01", "bin/contesto.py", "    for f in collegate(scheda, pm.radici_memoria()):\n", "    for f in []:\n"),
    ("TC02", "bin/contesto.py", "        if vero:\n            s = vero\n", "        if False:\n            s = vero\n"),
    ("TC03", "bin/contesto.py", '[f\'Nessuna cartella, scheda o handoff per "{nome}".\']', "[]"),
    ("TC05", "hooks/titolo-sessione.py", "return \" \".join(parole) if 2 <= len(parole) <= PAROLE", "return \" \".join(parole) if 2 <= len(parole)"),
    ("TC05", "hooks/titolo-sessione.py", "    if not etichette and len(righe) == 1:\n", "    if False:\n"),
    ("TC06", "hooks/titolo-sessione.py", '    if adesso - float(salvato.get("chiede") or 0) < TETTO:\n        return 0\n', ""),
    ("TC06", "hooks/titolo-sessione.py", "    if s:\n        nuovo[\"sintesi\"] = s\n", ""),
    ("TC06", "hooks/titolo-sessione.py", 'evento not in ("UserPromptSubmit", "Stop", "PostToolUse")', 'evento not in ("UserPromptSubmit", "Stop")'),
    ("TC06", "hooks/titolo-sessione.py", "        nuovo.update({\"quando_sintesi\": adesso, \"peso_sintesi\": peso})\n", "        pass\n"),
]

# Un claude finto: conta le chiamate e risponde con RISPOSTA (variabile d'ambiente).
CLAUDE_FINTO = """#!/usr/bin/env python3
import os, sys
sys.stdin.read()
with open(os.environ["TC_CHIAMATE"], "a") as fh:
    fh.write("x\\n")
sys.stdout.write(os.environ.get("TC_RISPOSTA", ""))
"""


class Lab:
    def __init__(self, repo: Path, tmp: Path):
        self.tmp, self.home = tmp, tmp / "home"
        self.cl = self.home / ".claude"
        self.cl.mkdir(parents=True)
        ignora = shutil.ignore_patterns("__pycache__", "*.local")
        shutil.copytree(str(repo / "bin"), str(self.cl / "bin"), ignore=ignora)
        shutil.copytree(str(repo / "hooks"), str(self.cl / "hooks"), ignore=ignora)
        self.base = self.home / "Documents" / "ClaudeCode"
        self.base.mkdir(parents=True)
        self.mem = self.cl / "data" / "memory"
        (self.mem / "progetti").mkdir(parents=True)
        (self.mem / "errori").mkdir(parents=True)
        self.h = self.cl / "data" / "handoffs"
        self.h.mkdir(parents=True)

    def env(self, **altro) -> dict:
        e = dict(os.environ, HOME=str(self.home), USERPROFILE=str(self.home), ARTURO_TODO=str(self.cl / "data" / "todo" / "eventi.jsonl"),
                 ARTURO_TELEMETRIA="0", PYTHONDONTWRITEBYTECODE="1", ARTURO_OGGI="2026-11-12", ARTURO_MEMORIA="1", **altro)
        for k in ("PROJECTS_BASE", "CLAUDE_CONFIG_DIR", "ARTURO_TITOLI", "ARTURO_TITOLO_FIGLIO", "ARTURO_TITOLI_OGNI", "ARTURO_SINTESI_OGNI"):
            if k not in altro:
                e.pop(k, None)
        return e

    def contesto(self, *a: str):
        r = subprocess.run([sys.executable, "-B", str(self.cl / "bin" / "contesto.py"), *a], capture_output=True, text=True,
                           encoding="utf-8", errors="replace", env=self.env(), timeout=120, cwd=str(self.home))
        try:
            return json.loads(r.stdout), r
        except ValueError:
            return None, r

    def impronta(self) -> str:
        h = hashlib.sha256()
        for f in sorted(self.home.rglob("*")):
            if "__pycache__" in f.parts:
                continue
            h.update(str(f.relative_to(self.home)).encode())
            if f.is_file():
                h.update(f.read_bytes())
        return h.hexdigest()


def prepara(lab: Lab) -> None:
    (lab.cl / "CLAUDE.md").write_text("# Globale\nUna riga.\n", encoding="utf-8")
    chiave = "".join(c if c.isalnum() else "-" for c in str(lab.base))
    m = lab.cl / "projects" / chiave / "memory"
    m.mkdir(parents=True)
    (m / "MEMORY.md").write_text("# Indice\n- [[progetto-herdr-arturo]]\n", encoding="utf-8")
    c = lab.base / "herdr-arturo"
    c.mkdir()
    (c / "CLAUDE.md").write_text("# Herdr\nIstruzioni del progetto.\n", encoding="utf-8")
    (lab.mem / "progetti" / "progetto-herdr-arturo.md").write_text(
        '---\nname: progetto-herdr-arturo\ntitolo: "Volta"\nalias: [volta-celeste, volta]\ndescription: "La finestra"\n---\n'
        "# Volta\nVedi [[errore-comune-uno]] e [[nota-che-non-c-e]].\n", encoding="utf-8")
    (lab.mem / "errori" / "errore-comune-uno.md").write_text("---\nname: errore-comune-uno\n---\nNON fare X.\n", encoding="utf-8")
    d = lab.h / "herdr-arturo"
    d.mkdir()
    (d / "HANDOFF_2026-11-12_21-08.md").write_text("# Session Handoff\n## Ripartenza\n**Prossimo passo:** testata.\n", encoding="utf-8")


def hook(repo_hook: Path):
    spec = importlib.util.spec_from_file_location("titolo_sessione_prova", str(repo_hook))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def trascrizione(lab: Lab, sid: str, righe: int) -> Path:
    p = lab.cl / "projects" / "x" / f"{sid}.jsonl"
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a", encoding="utf-8") as fh:
        for i in range(righe):
            fh.write(json.dumps({"type": "user", "message": {"content": f"Scrivi la testata nuova di Volta, giro {i}"}}) + "\n")
            fh.write(json.dumps({"type": "assistant", "message": {"content": [{"type": "text", "text": f"Fatto il giro {i}."}]}}) + "\n")
    return p


def lancia_hook(lab: Lab, evento: str, sid: str, tr: Path, risposta: str, chiamate: Path, **altro):
    bin_ = lab.tmp / "bin"
    bin_.mkdir(exist_ok=True)
    cl = bin_ / "claude"
    cl.write_text(CLAUDE_FINTO, encoding="utf-8")
    cl.chmod(0o755)
    env = lab.env(TC_RISPOSTA=risposta, TC_CHIAMATE=str(chiamate), **altro)
    env["PATH"] = str(bin_) + os.pathsep + env.get("PATH", "")
    ev = {"hook_event_name": evento, "session_id": sid, "transcript_path": str(tr)}
    return subprocess.run([sys.executable, "-B", str(lab.cl / "hooks" / "titolo-sessione.py")], input=json.dumps(ev), text=True,
                          capture_output=True, env=env, timeout=60)


def conta(f: Path) -> int:
    return len(f.read_text().splitlines()) if f.exists() else 0


def prova(repo: Path) -> dict:
    esiti = {}
    tmp = Path(tempfile.mkdtemp(prefix="tc-"))
    try:
        lab = Lab(repo, tmp)
        prepara(lab)
        prima = lab.impronta()
        d, r = lab.contesto("herdr-arturo", "--json")
        ordine = ["globale", "indice", "progetto", "scheda", "inizio", "handoff", "nota-errore-comune-uno"]
        if not d:
            esiti["TC01"] = f"niente JSON: rc {r.returncode} {r.stderr[-200:]}"
        else:
            ids = [f["id"] for f in d["fonti"]]
            pres = {f["id"]: f for f in d["fonti"]}
            if ids != ordine:
                esiti["TC01"] = f"fonti {ids}, attese {ordine}"
            elif not all(pres[i]["presente"] for i in ordine):
                esiti["TC01"] = "una fonte che c'è risulta assente: " + str([i for i in ordine if not pres[i]["presente"]])
            elif pres["progetto"]["caratteri"] != len("# Herdr\nIstruzioni del progetto.\n") or pres["progetto"]["anteprima"] != ["# Herdr", "Istruzioni del progetto."]:
                esiti["TC01"] = f"istruzioni del progetto: {pres['progetto']}"
            elif not str(pres["handoff"]["percorso"]).endswith("HANDOFF_2026-11-12_21-08.md"):
                esiti["TC01"] = f"ultimo handoff: {pres['handoff']['percorso']}"
            elif d["progetto"].get("titolo") != "Volta":
                esiti["TC01"] = f"titolo del progetto: {d['progetto']}"
            else:
                esiti["TC01"] = None
        d, r = lab.contesto("volta", "--json")
        esiti["TC02"] = None if d and d["progetto"]["slug"] == "herdr-arturo" and any(f["id"] == "scheda" and f["presente"] for f in d["fonti"]) \
            else f"l'alias volta non porta a herdr-arturo: {d and d['progetto']}"
        d, r = lab.contesto("non-esiste-proprio", "--json")
        if not d:
            esiti["TC03"] = f"niente JSON per un progetto che non c'è: rc {r.returncode}"
        else:
            assenti = [f["id"] for f in d["fonti"] if not f["presente"]]
            esiti["TC03"] = None if d["avvisi"] and {"progetto", "scheda", "handoff"} <= set(assenti) else f"avvisi {d['avvisi']}, assenti {assenti}"
        esiti["TC04"] = None if lab.impronta() == prima else "contesto --json ha scritto nella HOME di prova"

        m = hook(lab.cl / "hooks" / "titolo-sessione.py")
        casi = [("TITOLO: Testata nuova di Volta\nADESSO: Scrive la sintesi", ("Testata nuova di Volta", "Scrive la sintesi")),
                ("titolo: Prova del banco\nadesso: uno due tre quattro cinque sei", ("Prova del banco", "")),
                ("Correzione del banco dei test", ("Correzione del banco dei test", "")),
                ("TITOLO: x\nADESSO: \"Lancia i test.\"", ("", "Lancia i test")),
                ("ADESSO: Legge", ("", ""))]
        storti = [(r_, m.due_righe(r_), v) for r_, v in casi if m.due_righe(r_) != v]
        esiti["TC05"] = None if not storti else f"due_righe: {storti[0]}"

        sid = "aaaa1111-2222-3333-4444-555566667777"
        tr = trascrizione(lab, sid, 3)
        ch = tmp / "chiamate.txt"
        f = lab.cl / "cache" / "titolo" / f"{sid}.json"
        r1 = lancia_hook(lab, "PostToolUse", sid, tr, "TITOLO: Testata di Volta\nADESSO: Scrive la testata", ch)
        s1 = json.loads(f.read_text()) if f.exists() else {}
        trascrizione(lab, sid, 1)
        lancia_hook(lab, "PostToolUse", sid, tr, "TITOLO: Altro\nADESSO: Fa altro", ch)
        s2 = json.loads(f.read_text()) if f.exists() else {}
        # un altro hook della stessa sessione sta già chiedendo: questo non chiama il modello
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(json.dumps({**s2, "quando_sintesi": 0, "chiede": time.time()}), encoding="utf-8")
        n2 = conta(ch)
        trascrizione(lab, sid, 1)
        lancia_hook(lab, "PostToolUse", sid, tr, "TITOLO: Doppio\nADESSO: Chiamata doppia", ch)
        doppia = conta(ch) != n2
        # sotto un nome della persona: la sintesi cambia, il titolo no
        f.write_text(json.dumps({**s2, "titolo": "Nome mio", "fonte": "persona", "quando_sintesi": 0, "chiede": 0}), encoding="utf-8")
        trascrizione(lab, sid, 1)
        lancia_hook(lab, "Stop", sid, tr, "TITOLO: Altro titolo\nADESSO: Lancia il banco", ch)
        s3 = json.loads(f.read_text()) if f.exists() else {}
        # una risposta senza ADESSO sposta il turno: subito dopo non si richiama il modello
        f.write_text(json.dumps({**s3, "quando_sintesi": 0}), encoding="utf-8")
        trascrizione(lab, sid, 1)
        lancia_hook(lab, "Stop", sid, tr, "TITOLO: Solo titolo", ch)
        s4 = json.loads(f.read_text()) if f.exists() else {}
        n4 = conta(ch)
        trascrizione(lab, sid, 1)
        lancia_hook(lab, "PostToolUse", sid, tr, "TITOLO: X\nADESSO: Non deve arrivare", ch)
        if s1.get("sintesi") != "Scrive la testata" or s1.get("titolo") != "Testata di Volta":
            esiti["TC06"] = f"primo PostToolUse: {s1} rc {r1.returncode} {r1.stderr[-200:]}"
        elif s2.get("sintesi") != "Scrive la testata" or conta(ch) < 3:
            esiti["TC06"] = f"il secondo PostToolUse subito dopo ha richiamato il modello: {s2}"
        elif doppia:
            esiti["TC06"] = "due hook insieme: il secondo ha chiamato il modello mentre il primo chiedeva"
        elif s3.get("titolo") != "Nome mio" or s3.get("sintesi") != "Lancia il banco":
            esiti["TC06"] = f"sotto un nome della persona: {s3}"
        elif not s4.get("quando_sintesi") or s4.get("sintesi") != "Lancia il banco" or conta(ch) != n4:
            esiti["TC06"] = f"una risposta senza ADESSO non sposta il turno: {s4}, chiamate {n4} poi {conta(ch)}"
        elif "chiede" in s4:
            esiti["TC06"] = "il segno 'chiede' resta nel file dopo la risposta"
        else:
            esiti["TC06"] = None
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return esiti


def main() -> int:
    repo = Path(__file__).resolve().parent.parent
    if "--avvelena" in sys.argv:
        buchi = 0
        for caso, file, giusto, rotto in VELENI:
            testo = (repo / file).read_text(encoding="utf-8")
            if testo.count(giusto) != 1:
                print(f"VELENO {caso} NON ATTACCA: {giusto[:60]!r} c'è {testo.count(giusto)} volte")
                buchi += 1
                continue
            t = Path(tempfile.mkdtemp(prefix="tc-veleno-"))
            try:
                shutil.copytree(str(repo / "bin"), str(t / "bin"))
                shutil.copytree(str(repo / "hooks"), str(t / "hooks"))
                (t / file).write_text(testo.replace(giusto, rotto), encoding="utf-8")
                motivo = prova(t).get(caso)
            finally:
                shutil.rmtree(t, ignore_errors=True)
            print(f"VELENO {caso} {'ROSSO' if motivo else 'VERDE: il caso non vede la rottura'}: {(motivo or giusto)[:100]}")
            buchi += 0 if motivo else 1
        print(f"veleni: {len(VELENI) - buchi}/{len(VELENI)} rossi")
        return 1 if buchi else 0
    t0 = time.time()
    esiti = prova(repo)
    for c in CASI:
        print(f"{c} VERDE" if not esiti.get(c) else f"{c} ROSSO: {esiti[c]}")
    rossi = [c for c in CASI if esiti.get(c)]
    print(f"testata-contesto: {len(CASI) - len(rossi)}/{len(CASI)} casi verdi in {time.time() - t0:.1f} s")
    return 1 if rossi else 0


if __name__ == "__main__":
    sys.exit(main())
