#!/usr/bin/env python3
"""Il file di sessione ha un solo padrone (hooks/scheda_file.py, verbo `arturo sessione progetto`, 23/11/2026, C1).

SE01 un progetto deciso (fonte volta, teletrasporto, inizio, persona) non cambia quando la sessione scrive un file
     in un'altra cartella di progetto: né il progetto né la fonte.
SE02 la regola vale nei due sensi: il testo "/inizio <nome>" della persona sostituisce anche un progetto deciso,
     e una fonte decisa ne sostituisce un'altra (teletrasporto su volta).
SE03 il segno `spostata` sopravvive a un evento di stato dell'hook (Stop).
SE04 un file senza `versione` (scritto prima del 23/11) si legge, e alla prima scrittura prende `versione: 1`.
SE05 sessione, progetto o fonte non validi escono 3 e non scrivono niente.
SE06 una scrittura che la regola rifiuta esce 2 col motivo, e il file resta com'era.
SE07 una correzione della persona (forza, senza fonte: unisci) cambia il progetto e lascia fonte e segni; e
     bin/unisci.py passa dal modulo, non riscrive il JSON.
SE08 i segni passati a imposta_progetto (Volta, #6421 passo 8d): `inizio` False resta scritto, None toglie
     `spostata` anche con lo stesso progetto e la stessa fonte, un segno fuori da SEGNI esce col motivo.
SE09 togli_spostata toglie solo il segno e lascia progetto e fonte; senza il segno il file non cambia.

Veleno: --avvelena rompe il codice nella copia di prova, un punto per caso, ed esce 0 solo se ogni rottura fa
rosso il suo caso (VELENI del gate).
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

CASI = ["SE01", "SE02", "SE03", "SE04", "SE05", "SE06", "SE07", "SE08", "SE09"]
# caso -> (file, testo da rompere, testo rotto)
VELENI = {
    "SE01": ("hooks/scheda_file.py", 'return FONTI.get(salvata or "", 0) >= DECISA and',
             'return (salvata or "") in ("inizio", "persona") and'),
    "SE02": ("hooks/scheda_file.py", 'and FONTI[nuova] < FONTI["prompt"]', "and True"),
    "SE03": ("hooks/scheda_file.py", "nuovo.update({k: prima[k] for k in SEGNI if k in prima})", "pass"),
    "SE04": ("hooks/scheda_file.py", 'nuovo["versione"] = VERSIONE', "pass"),
    "SE05": ("bin/sessione.py", "if len(pos) != 2 or fonte is None or not NOME_PROGETTO.match(pos[1]):",
             "if len(pos) != 2 or fonte is None:"),
    "SE06": ("bin/sessione.py", "    if not ok:\n        print(motivo, file=sys.stderr)\n        return 2\n",
             "    if not ok:\n        print(motivo, file=sys.stderr)\n        return 0\n"),
    "SE07": ("hooks/scheda_file.py", "if forza and fonte is None:", "if False:"),
    "SE08": ("hooks/scheda_file.py", "            nuovo.pop(campo, None)\n", "            pass\n"),
    "SE09": ("hooks/scheda_file.py", '    dati.pop("spostata")\n', "    pass\n"),
}


class Lab:
    def __init__(self, repo: Path, tmp: Path):
        self.home = tmp / "home"
        self.cl = self.home / ".claude"
        self.cl.mkdir(parents=True)
        ignora = shutil.ignore_patterns("__pycache__", "*.local")
        for nome in ("bin", "hooks"):
            shutil.copytree(str(repo / nome), str(self.cl / nome), ignore=ignora)
        self.base = self.home / "Documents" / "ClaudeCode"
        for p in ("altro", "primo"):
            (self.base / p).mkdir(parents=True)
        self.dir = self.cl / "cache" / "scheda"

    def env(self) -> dict:
        import os
        e = {k: v for k, v in os.environ.items()
             if k not in ("CLAUDE_CONFIG_DIR", "PROJECTS_BASE", "WT_SESSION", "TERM_PROGRAM", "ARTURO_SCHEDA_USCITA")}
        e.update(HOME=str(self.home), USERPROFILE=str(self.home), PYTHONDONTWRITEBYTECODE="1",
                 ARTURO_SCHEDA_USCITA=str(self.home / "uscita.txt"), ARTURO_TELEMETRIA="0")
        return e

    def verbo(self, *a: str) -> subprocess.CompletedProcess:
        return subprocess.run([sys.executable, "-B", str(self.cl / "bin" / "arturo"), "sessione", *a],
                              capture_output=True, text=True, encoding="utf-8", errors="replace",
                              env=self.env(), timeout=60, cwd=str(self.home))

    def hook(self, evento: str, sid: str, **altro) -> None:
        dati = {"hook_event_name": evento, "session_id": sid, "cwd": str(self.home), **altro}
        r = subprocess.run([sys.executable, "-B", str(self.cl / "hooks" / "scheda-terminale.py")],
                           input=json.dumps(dati).encode("utf-8"), capture_output=True, env=self.env(), timeout=60)
        assert r.returncode == 0, r.stderr[-200:]

    def scrive_file(self, sid: str, cartella: str) -> None:
        self.hook("PostToolUse", sid, tool_name="Write", tool_input={"file_path": str(self.base / cartella / "x.txt")})

    def leggi(self, sid: str) -> dict:
        try:
            return json.loads((self.dir / f"{sid}.json").read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return {}

    def modulo(self, codice: str) -> subprocess.CompletedProcess:
        return subprocess.run([sys.executable, "-B", "-c", "import sys; sys.path.insert(0, %r)\n" % str(self.cl / "hooks") + codice],
                              capture_output=True, text=True, encoding="utf-8", errors="replace", env=self.env(), timeout=60)


def prova(lab: Lab) -> list:
    rossi = []
    # SE01 e SE02
    for fonte in ("volta", "teletrasporto", "inizio", "persona"):
        sid = f"decisa-{fonte}"
        r = lab.verbo("progetto", sid, "primo", "--fonte", fonte)
        lab.scrive_file(sid, "altro")
        d = lab.leggi(sid)
        if r.returncode != 0 or d.get("progetto") != "primo" or d.get("fonte") != fonte:
            rossi.append(f"SE01 fonte {fonte}: rc={r.returncode} file={d}")
    lab.verbo("progetto", "debole", "primo", "--fonte", "file")
    lab.scrive_file("debole", "altro")
    if lab.leggi("debole").get("progetto") != "altro":
        rossi.append(f"SE01 controllo: un progetto da file si sposta con un altro file: {lab.leggi('debole')}")
    lab.verbo("progetto", "inizio-nuovo", "primo", "--fonte", "volta")
    lab.hook("UserPromptSubmit", "inizio-nuovo", prompt="/inizio altro -- prova")
    d = lab.leggi("inizio-nuovo")
    r = lab.verbo("progetto", "inizio-nuovo", "terzo", "--fonte", "teletrasporto")
    d2 = lab.leggi("inizio-nuovo")
    if d.get("progetto") != "altro" or r.returncode != 0 or d2.get("progetto") != "terzo" or d2.get("fonte") != "teletrasporto":
        rossi.append(f"SE02 sostituzioni: dopo il prompt={d} dopo teletrasporto rc={r.returncode} {d2}")
    # SE03
    lab.verbo("progetto", "spost", "primo", "--fonte", "volta")
    r = lab.verbo("spostata", "spost", "--su", "amaltea")
    lab.hook("Stop", "spost")
    d = lab.leggi("spost")
    if r.returncode != 0 or d.get("spostata", {}).get("su") != "amaltea" or d.get("progetto") != "primo":
        rossi.append(f"SE03 segno spostata dopo l'evento Stop: rc={r.returncode} file={d}")
    # SE04
    lab.dir.mkdir(parents=True, exist_ok=True)
    (lab.dir / "vecchia.json").write_text(json.dumps({"stato": "attende", "progetto": "primo", "fonte": "cartella",
                                                      "quando": 1.0}), encoding="utf-8")
    r = lab.verbo("progetto", "vecchia", "altro", "--fonte", "volta")
    d = lab.leggi("vecchia")
    if r.returncode != 0 or d.get("versione") != 1 or d.get("stato") != "attende" or d.get("progetto") != "altro":
        rossi.append(f"SE04 file senza versione: rc={r.returncode} {r.stderr.strip()} file={d}")
    # SE05
    for args in (("progetto", "../x", "primo", "--fonte", "volta"), ("progetto", "ok-1", "a b/../c", "--fonte", "volta"),
                 ("progetto", "ok-1", "primo", "--fonte", "inventata"), ("progetto", "ok-1", "primo"),
                 ("spostata", "ok-1"), ("spostata", "../x", "--su", "m")):
        r = lab.verbo(*args)
        if r.returncode != 3:
            rossi.append(f"SE05 argomenti non validi {args}: rc={r.returncode}")
    if (lab.dir / "ok-1.json").exists() or (lab.cl / "cache" / "x.json").exists() or (lab.dir.parent / "x.json").exists():
        rossi.append("SE05 un argomento non valido ha scritto un file")
    # SE06
    prima = lab.leggi("decisa-volta")
    r = lab.verbo("progetto", "decisa-volta", "altro", "--fonte", "file")
    if r.returncode != 2 or "volta" not in r.stderr or lab.leggi("decisa-volta") != prima:
        rossi.append(f"SE06 rifiuto: rc={r.returncode} stderr={r.stderr.strip()!r} file={lab.leggi('decisa-volta')}")
    # SE07
    r = lab.modulo("import scheda_file as sf\nprint(sf.imposta_progetto('spost', 'nuovo', forza=True))")
    d = lab.leggi("spost")
    sorgente = (lab.cl / "bin" / "unisci.py").read_text(encoding="utf-8")
    if d.get("progetto") != "nuovo" or d.get("fonte") != "volta" or d.get("spostata", {}).get("su") != "amaltea" \
            or "scheda_file" not in sorgente or "rn.scrivi_atomico(f, json.dumps" in sorgente:
        rossi.append(f"SE07 correzione della persona: {r.stdout.strip()} {r.stderr.strip()[-150:]} file={d}")
    # SE08
    r = lab.modulo("import scheda_file as sf\n"
                   "print(sf.imposta_progetto('segni', 'primo', 'persona', segni={'inizio': False}))\n"
                   "print(sf.segna_spostata('segni', 'torre'))\n"
                   "print(sf.imposta_progetto('segni', 'primo', 'persona', segni={'spostata': None}))\n"
                   "print(sf.imposta_progetto('segni', 'primo', 'persona', segni={'colore': 1}))")
    d = lab.leggi("segni")
    righe = r.stdout.strip().splitlines()
    if r.returncode != 0 or d.get("inizio") is not False or "spostata" in d or d.get("progetto") != "primo" \
            or len(righe) != 4 or "segno sconosciuto" not in righe[3]:
        rossi.append(f"SE08 segni di imposta_progetto: {r.stdout.strip()} {r.stderr.strip()[-150:]} file={d}")
    # SE09
    lab.verbo("progetto", "torna", "primo", "--fonte", "teletrasporto")
    lab.verbo("spostata", "torna", "--su", "torre")
    prima = (lab.dir / "decisa-volta.json").read_bytes()
    r = lab.modulo("import scheda_file as sf\nprint(sf.togli_spostata('torna'), sf.togli_spostata('decisa-volta'))")
    d = lab.leggi("torna")
    if r.returncode != 0 or "spostata" in d or d.get("progetto") != "primo" or d.get("fonte") != "teletrasporto" \
            or (lab.dir / "decisa-volta.json").read_bytes() != prima:
        rossi.append(f"SE09 togli_spostata: {r.stdout.strip()} {r.stderr.strip()[-150:]} file={d}")
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
            nome, vecchio, rotto = VELENI[caso]
            with tempfile.TemporaryDirectory(prefix="arturo-se-") as tmp:
                lab = Lab(Path(argomenti.repo), Path(tmp))
                sorgente = lab.cl / nome
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
    with tempfile.TemporaryDirectory(prefix="arturo-se-") as tmp:
        rossi = prova(Lab(Path(argomenti.repo), Path(tmp)))
    for r in rossi:
        print("ROSSO", r)
    print(f"file di sessione: {len(CASI) - len(rossi)}/{len(CASI)} casi verdi")
    return 1 if rossi else 0


if __name__ == "__main__":
    sys.exit(main())
