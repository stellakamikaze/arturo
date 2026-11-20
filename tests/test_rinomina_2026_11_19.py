#!/usr/bin/env python3
"""arturo progetti rinomina: un progetto cambia nome in un passo (bin/rinomina.py, proposta n. 90, 19/11/2026).

RN01 i todo del progetto, aperti e chiusi, passano al nome nuovo; col nome vecchio non resta nessun todo.
RN02 la riga di stato passa al nome nuovo.
RN03 gli handoff passano nella cartella nuova, con "- Nome:" e "- Filone:" riscritti; la cartella vecchia
     sparisce e INDEX.md punta alla cartella nuova.
RN04 la scheda diventa progetto-<nuovo>.md, con `name:` nuovo e il nome vecchio in `alias:`; il link
     [[progetto-<vecchio>]] di un'altra nota diventa [[progetto-<nuovo>]].
RN05 dopo la rinomina /inizio col nome vecchio apre il progetto nuovo, e lo dice.
RN06 --prova non scrive niente: l'albero della HOME di prova è identico prima e dopo.
RN07 un progetto con la sua cartella nella base dei progetti esce 2 e non scrive niente.
RN08 "fenice_blu" e "fenice-blu" sono lo stesso nome: exit 3.
RN09 la rinomina all'indietro rimette i todo sul nome vecchio, e la scheda non ha più il proprio nome fra gli alias.

Veleno: --avvelena rompe bin/rinomina.py (o contesto.py per RN05) nella copia di prova, un punto per caso,
ed esce 0 solo se ogni rottura fa rosso il suo caso.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

CASI = ["RN01", "RN02", "RN03", "RN04", "RN05", "RN06", "RN07", "RN08", "RN09"]
# caso -> (file in bin/, testo, testo rotto)
VELENI = {
    "RN01": ("rinomina.py", 'ts.normalizza({"progetto": nuovo})', 'ts.normalizza({"titolo": "x"})'),
    "RN02": ("rinomina.py", "        ts.scrivi_stato(nuovo, stato[\"riga\"])\n", "        pass\n"),
    "RN03": ("rinomina.py", "            scrivi_atomico(f, testo)\n    avvisi = []", "            pass\n    avvisi = []"),
    "RN04": ("rinomina.py", '            voci.append(vecchio)\n', '            pass\n'),
    "RN05": ("contesto.py", "        if slug(pref) in nuovi:\n", "        if False:\n"),
    "RN06": ("rinomina.py", "    if prova:\n", "    if False:\n"),
    "RN07": ("rinomina.py", "    if cartella is not None:\n", "    if False:\n"),
    "RN08": ("rinomina.py", "    if vecchio == nuovo:\n", "    if False:\n"),
    "RN09": ("rinomina.py", "        voci = [v for v in voci if cx.slug(v) != nuovo]\n", ""),
}

HANDOFF = ("# Session Handoff - 2026-11-18 10:00\n## Progetto\n- Nome: fenice-vecchia / Branch: nessuno / Status: in progress\n"
           "- Filone: fenice-vecchia/stampa\n\n## Ripartenza\n**Prossimo passo:** io chiamo la tipografia.\n")


class Lab:
    def __init__(self, repo: Path, tmp: Path):
        self.home = tmp / "home"
        self.cl = self.home / ".claude"
        self.cl.mkdir(parents=True)
        ignora = shutil.ignore_patterns("__pycache__", "*.local")
        shutil.copytree(str(repo / "bin"), str(self.cl / "bin"), ignore=ignora)
        shutil.copytree(str(repo / "hooks"), str(self.cl / "hooks"), ignore=ignora)
        self.base = self.home / "Documents" / "ClaudeCode"
        self.base.mkdir(parents=True)
        self.h = self.cl / "data" / "handoffs"
        self.mem = self.cl / "data" / "memory"

    def env(self) -> dict:
        e = dict(os.environ, HOME=str(self.home), USERPROFILE=str(self.home),
                 ARTURO_TODO=str(self.cl / "data" / "todo" / "eventi.jsonl"), ARTURO_TELEMETRIA="0",
                 PYTHONDONTWRITEBYTECODE="1", ARTURO_OGGI="2026-11-19", ARTURO_MEMORIA="1")
        for k in ("PROJECTS_BASE", "CLAUDE_CONFIG_DIR"):
            e.pop(k, None)
        return e

    def arturo(self, *a: str) -> subprocess.CompletedProcess:
        return subprocess.run([sys.executable, "-B", str(self.cl / "bin" / "arturo"), *a], capture_output=True,
                              text=True, encoding="utf-8", errors="replace", env=self.env(), timeout=120,
                              cwd=str(self.home))

    def prepara(self) -> None:
        for titolo in ("Chiamare la tipografia", "Mandare le bozze"):
            r = self.arturo("todo", "aggiungi", titolo, "--progetto", "fenice-vecchia")
            assert r.returncode == 0, r.stderr
        r = self.arturo("todo", "fatto", "2")
        assert r.returncode == 0, r.stderr
        r = self.arturo("todo", "aggiungi", "Altro lavoro", "--progetto", "altro")
        assert r.returncode == 0, r.stderr
        r = self.arturo("todo", "stato", "bozze in stampa", "--progetto", "fenice-vecchia")
        assert r.returncode == 0, r.stderr
        d = self.h / "fenice-vecchia"
        d.mkdir(parents=True)
        (d / "HANDOFF_2026-11-18_10-00.md").write_text(HANDOFF, encoding="utf-8")
        (self.h / "INDEX.md").write_text(
            "| Progetto | Ultimo handoff | Data | Stato | Prossimo passo |\n|---|---|---|---|---|\n"
            "| fenice-vecchia — fenice-vecchia/stampa | [HANDOFF_2026-11-18_10-00.md](fenice-vecchia/HANDOFF_2026-11-18_10-00.md)"
            " | 2026-11-18 | in progress | io chiamo la tipografia. |\n", encoding="utf-8")
        p = self.mem / "progetti"
        p.mkdir(parents=True)
        (p / "progetto-fenice-vecchia.md").write_text(
            "---\nname: progetto-fenice-vecchia\ndescription: la rivista\nalias: [fenice]\n---\ncorpo\n", encoding="utf-8")
        (p / "persona-tipografo.md").write_text(
            "---\nname: persona-tipografo\n---\nStampa [[progetto-fenice-vecchia]] e [[progetto-altro]].\n", encoding="utf-8")

    def todo(self, progetto: str) -> list:
        r = self.arturo("todo", "lista", "--progetto", progetto, "--tutti", "--json")
        try:
            d = json.loads(r.stdout)
            return [t["titolo"] for g in d["gruppi"] for t in g["todo"]] + [t["titolo"] for t in d.get("chiusi_todo", [])]
        except (ValueError, KeyError, TypeError):
            return []

    def impronta(self) -> str:
        h = hashlib.sha256()
        for p in sorted(self.home.rglob("*")):
            st = p.lstat()
            h.update(f"{p.relative_to(self.home).as_posix()}|{st.st_size}|{st.st_mtime_ns}\n".encode())
        return h.hexdigest()


def prova(repo: Path, rompi=None) -> list:
    rossi = []
    with tempfile.TemporaryDirectory(prefix="arturo-rn-") as tmp:
        lab = Lab(repo, Path(tmp))
        if rompi:
            f, vecchio, rotto = rompi
            sorgente = lab.cl / "bin" / f
            testo = sorgente.read_text(encoding="utf-8")
            assert testo.count(vecchio) == 1, f"il punto da rompere in {f} compare {testo.count(vecchio)} volte"
            sorgente.write_text(testo.replace(vecchio, rotto), encoding="utf-8")
        lab.prepara()

        prima = lab.impronta()
        r = lab.arturo("progetti", "rinomina", "fenice-vecchia", "fenice-blu", "--prova")
        if r.returncode != 0 or lab.impronta() != prima or "todo: 2" not in r.stdout:
            rossi.append(f"RN06 --prova: rc={r.returncode}, albero cambiato={lab.impronta() != prima}, {r.stdout[-200:]}")

        r = lab.arturo("progetti", "rinomina", "fenice_blu", "fenice-blu")
        if r.returncode != 3:
            rossi.append(f"RN08 stesso nome: rc={r.returncode}")

        (lab.base / "con-cartella").mkdir()
        lab.arturo("todo", "aggiungi", "Lavoro in cartella", "--progetto", "con-cartella")
        prima = lab.impronta()
        r = lab.arturo("progetti", "rinomina", "con-cartella", "senza")
        if r.returncode != 2 or lab.impronta() != prima:
            rossi.append(f"RN07 cartella: rc={r.returncode}, albero cambiato={lab.impronta() != prima}")

        r = lab.arturo("progetti", "rinomina", "fenice-vecchia", "fenice_blu")
        if r.returncode != 0:
            rossi.append(f"RN01 rinomina: rc={r.returncode} {r.stderr[-300:]}")
        nuovi, vecchi = lab.todo("fenice-blu"), lab.todo("fenice-vecchia")
        if sorted(nuovi) != ["Chiamare la tipografia", "Mandare le bozze"] or vecchi:
            rossi.append(f"RN01 todo: nuovo={nuovi}, vecchio={vecchi}")
        s = lab.arturo("todo", "stato", "--progetto", "fenice-blu")
        if "bozze in stampa" not in s.stdout:
            rossi.append(f"RN02 stato: {s.stdout.strip()!r} {s.stderr.strip()[-200:]}")

        nuova = lab.h / "fenice-blu" / "HANDOFF_2026-11-18_10-00.md"
        index = (lab.h / "INDEX.md").read_text(encoding="utf-8")
        testo = nuova.read_text(encoding="utf-8") if nuova.exists() else ""
        if (not nuova.exists() or (lab.h / "fenice-vecchia").exists() or "- Nome: fenice-blu /" not in testo
                or "- Filone: fenice-blu/stampa" not in testo or "fenice-blu/HANDOFF_2026-11-18_10-00.md" not in index
                or "fenice-vecchia/" in index):
            rossi.append(f"RN03 handoff: file nuovo={nuova.exists()}, testo={testo[:160]!r}, index={index[-200:]!r}")

        scheda = lab.mem / "progetti" / "progetto-fenice-blu.md"
        sch = scheda.read_text(encoding="utf-8") if scheda.exists() else ""
        nota = (lab.mem / "progetti" / "persona-tipografo.md").read_text(encoding="utf-8")
        if ((lab.mem / "progetti" / "progetto-fenice-vecchia.md").exists() or "name: progetto-fenice-blu\n" not in sch
                or "alias: [fenice, fenice-vecchia]\n" not in sch or "[[progetto-fenice-blu]]" not in nota
                or "[[progetto-altro]]" not in nota):
            rossi.append(f"RN04 scheda: {sch!r} nota: {nota!r}")

        c = lab.arturo("contesto", "fenice-vecchia")
        if c.returncode != 0 or "fenice-blu" not in c.stdout or "nome vecchio" not in c.stdout:
            rossi.append(f"RN05 contesto: rc={c.returncode} {c.stdout[:300]!r}")

        r = lab.arturo("progetti", "rinomina", "fenice-blu", "fenice-vecchia")
        indietro = lab.todo("fenice-vecchia")
        f = lab.mem / "progetti" / "progetto-fenice-vecchia.md"
        sch = f.read_text(encoding="utf-8") if f.exists() else ""
        if (r.returncode != 0 or sorted(indietro) != ["Chiamare la tipografia", "Mandare le bozze"]
                or "alias: [fenice, fenice-blu]\n" not in sch):
            rossi.append(f"RN09 indietro: rc={r.returncode} todo={indietro} scheda={sch!r} {r.stderr[-200:]}")
    return rossi


def main() -> int:
    for flusso in (sys.stdout, sys.stderr):
        if hasattr(flusso, "reconfigure"):
            flusso.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument("--avvelena", action="store_true")
    a = parser.parse_args()
    repo = Path(a.repo)
    if a.avvelena:
        inerti = []
        for caso in CASI:
            try:
                rossi = prova(repo, VELENI[caso])
            except AssertionError as e:
                inerti.append(f"{caso}: {e}")
                continue
            if not any(r.startswith(caso + " ") for r in rossi):
                inerti.append(f"{caso}: la rottura non lo fa rosso")
        assert not inerti, "veleni che non attaccano:\n" + "\n".join(inerti)
        print(f"VELENI_ROSSI={','.join(CASI)} veleni={len(CASI)}")
        return 0
    rossi = prova(repo)
    for r in rossi:
        print("ROSSO", r)
    print(f"rinomina: {len(CASI) - len(set(r.split()[0] for r in rossi))}/{len(CASI)} casi verdi")
    return 1 if rossi else 0


if __name__ == "__main__":
    sys.exit(main())
