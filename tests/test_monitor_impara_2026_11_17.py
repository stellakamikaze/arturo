#!/usr/bin/env python3
"""/monitor impara dalle correzioni della persona (17/11/2026): bin/monitor/impara.py.

IM01 segna: un tipo o un campo ignoto, una richiesta senza il campo che serve e un quando col fuso escono con 2
     e non scrivono; un segnale buono è una riga di segnali.jsonl col mittente in minuscolo e gli accenti
     intatti.
IM02 mittenti: una proposta accolta dà "si"; due rifiutate e nessuna accolta danno "no"; una rifiutata sola non
     decide niente; un rifiuto intoccabile non conta.
IM03 regole: due ripristini sugli ultimi cinque usi sospendono la regola; un ripristino no; due ripristini
     vecchi, seguiti da cinque declassamenti giusti, no.
IM04 sezioni: cinque giri senza azione comprimono la sezione; quattro giri no; un'azione in uno dei cinque no;
     una sezione "sempre" della persona e un giro con una voce intoccabile no. L'ordine mette prima le
     sezioni "sempre", poi la quota di voci agite.
IM05 modo: senza apprendimento.json calcola propone e non scrive appreso.json; con {"modo": "auto"} applica e
     registra; applica <id> applica solo quell'id; un id che non è fra le proposte esce con 2 e non scrive.
IM06 annullo: dopo annulla lo stato torna quello di prima e un ricalcolo con le stesse prove non rifà la
     modifica; una prova nuova, arrivata dopo l'annullo, la rifà. Il riepilogo dà l'annullo con l'id.
IM07 raccogli: i doppioni si saltano, una riga rotta si scarta col numero ed esce 1, le righe buone entrano;
     il BOM in testa e gli accenti passano.
IM08 robustezza: un appreso.json rotto non si riscrive (exit 2, file intatto); "arturo monitor" senza
     "impara" esce con 2; "arturo monitor impara mostra" risponde con lo stato; niente scritto fuori da
     ARTURO_HOME.

Con --avvelena quattro copie rotte di impara.py devono far rosso il caso che le sorveglia. Sulla base e0ec624
(il dev prima del motore) sono rossi tutti i casi.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

CASI = ("IM01", "IM02", "IM03", "IM04", "IM05", "IM06", "IM07", "IM08")


class Lab:
    def __init__(self, repo: Path, tmp: Path):
        self.repo, self.tmp, self.n = repo, tmp, 0

    def casa(self, config=None):
        self.n += 1
        c = self.tmp / f"casa{self.n}"
        (c / "home").mkdir(parents=True)
        if config is not None:
            f = c / "home" / "personale" / "monitor" / "apprendimento.json"
            f.parent.mkdir(parents=True)
            f.write_text(json.dumps(config), encoding="utf-8")
        return c / "home"

    def lancia(self, home, *arg, stdin=None, via_arturo=False):
        file = self.repo / "bin" / ("arturo" if via_arturo else "monitor/impara.py")
        if not file.is_file() or not (self.repo / "bin" / "monitor" / "impara.py").is_file():
            return 127, "", "impara.py assente"
        env = dict(os.environ, ARTURO_HOME=str(home), PYTHONIOENCODING="cp1252", HOME=str(home.parent))
        cmd = [sys.executable, str(file), *(("monitor", "impara") if via_arturo else ()), *arg]
        r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace",
                           input=stdin, env=env, timeout=60)
        return r.returncode, r.stdout, r.stderr

    def segna(self, home, tipo, **campi):
        arg = ["segna", tipo]
        for k, v in campi.items():
            arg += ["--intoccabile"] if k == "intoccabile" else [f"--{k}", v]
        return self.lancia(home, *arg)


def dati(home, nome):
    f = home / "data" / "monitor" / nome
    if not f.exists():
        return None
    if nome.endswith(".jsonl"):
        return [json.loads(r) for r in f.read_text(encoding="utf-8").splitlines() if r.strip()]
    return json.loads(f.read_text(encoding="utf-8"))


def proposte(out):
    return [r for r in out.splitlines() if r.startswith(("PROPOSTA", "APPLICATA"))]


def prova(lab: Lab) -> list:
    rossi = []

    # IM01
    d = []
    h = lab.casa()
    for arg in (("segna", "inventato"), ("segna", "scartato", "--colore", "blu"), ("segna", "proposta_accolta"),
                ("segna", "fatto", "--quando", "2026-11-10T09:00+01:00")):
        rc, _o, _e = lab.lancia(h, *arg)
        if rc != 2:
            d.append(f"{' '.join(arg[1:])}: exit {rc}")
    if dati(h, "segnali.jsonl") is not None:
        d.append("un segnale rifiutato ha scritto il file")
    rc, _o, e = lab.segna(h, "proposta_accolta", mittente="Città@Studio.it", motivo="l'ha chiesto lei")
    righe = dati(h, "segnali.jsonl") or []
    if rc != 0 or len(righe) != 1 or righe[0].get("mittente") != "città@studio.it" or "quando" not in righe[0]:
        d.append(f"segnale buono: exit {rc}, righe {righe}, {e[:80]}")
    if d:
        rossi.append("IM01 " + "; ".join(d))

    # IM02
    d = []
    h = lab.casa({"modo": "auto"})
    lab.segna(h, "proposta_accolta", mittente="si@a.it", quando="2026-11-10T09:00")
    lab.segna(h, "proposta_rifiutata", mittente="no@b.it", quando="2026-11-10T09:00")
    lab.segna(h, "proposta_rifiutata", mittente="no@b.it", quando="2026-11-11T09:00")
    lab.segna(h, "proposta_rifiutata", mittente="uno@c.it", quando="2026-11-11T09:00")
    lab.segna(h, "proposta_rifiutata", mittente="tocca@d.it", quando="2026-11-10T09:00", intoccabile="1")
    lab.segna(h, "proposta_rifiutata", mittente="tocca@d.it", quando="2026-11-11T09:00")
    rc, o, e = lab.lancia(h, "calcola")
    m = (dati(h, "appreso.json") or {}).get("mittenti", {})
    stati = {k: v.get("stato") for k, v in m.items()}
    if rc != 0 or stati != {"si@a.it": "si", "no@b.it": "no"}:
        if "uno@c.it" in stati:
            d.append(f"una rifiutata sola decide: {stati}")
        else:
            d.append(f"mittenti: exit {rc}, {stati}, {e[:80]}")
    if d:
        rossi.append("IM02 " + "; ".join(d))

    # IM03
    d = []
    h = lab.casa({"modo": "auto"})
    for g in range(1, 4):
        lab.segna(h, "declassato", regola="doppia", quando=f"2026-11-0{g}T08:00")
    lab.segna(h, "ripristinato", regola="doppia", quando="2026-11-05T08:00")
    lab.segna(h, "ripristinato", regola="doppia", quando="2026-11-06T08:00")
    lab.segna(h, "declassato", regola="singola", quando="2026-11-01T08:00")
    lab.segna(h, "ripristinato", regola="singola", quando="2026-11-02T08:00")
    lab.segna(h, "ripristinato", regola="vecchia", quando="2026-10-01T08:00")
    lab.segna(h, "ripristinato", regola="vecchia", quando="2026-10-02T08:00")
    for g in range(1, 6):
        lab.segna(h, "declassato", regola="vecchia", quando=f"2026-11-0{g}T08:00")
    rc, o, e = lab.lancia(h, "calcola")
    r = {k: v.get("stato") for k, v in ((dati(h, "appreso.json") or {}).get("regole", {})).items()}
    if rc != 0 or r.get("doppia") != "sospesa" or r.get("singola") != "attiva" or r.get("vecchia") != "attiva":
        d.append(f"regole: exit {rc}, {r}, {e[:80]}")
    if d:
        rossi.append("IM03 " + "; ".join(d))

    # IM04
    d = []
    h = lab.casa({"modo": "auto", "sempre": ["scadenze"]})
    for g in range(1, 6):
        for sezione in ("resto", "scadenze", "oggi", "toccata"):
            lab.segna(h, "voce_mostrata", sezione=sezione, giro=f"g{g}", quando=f"2026-11-1{g}T08:00")
    for g in range(1, 5):
        lab.segna(h, "voce_mostrata", sezione="giovane", giro=f"g{g}", quando=f"2026-11-1{g}T08:00")
    lab.segna(h, "voce_agita", sezione="oggi", giro="g4", quando="2026-11-14T09:00")
    lab.segna(h, "voce_mostrata", sezione="toccata", giro="g5", quando="2026-11-15T08:01", intoccabile="1")
    rc, o, e = lab.lancia(h, "calcola")
    a = dati(h, "appreso.json") or {}
    s = {k: v.get("stato") for k, v in a.get("sezioni", {}).items()}
    attese = {"resto": "compressa", "scadenze": "piena", "oggi": "piena", "giovane": "piena", "toccata": "piena"}
    if rc != 0 or s != attese:
        if s.get("scadenze") == "compressa":
            d.append(f"sempre compressa: {s}")
        d.append(f"sezioni: exit {rc}, {s}, {e[:80]}")
    ordine = a.get("ordine") or []
    if ordine[:2] != ["scadenze", "oggi"]:
        d.append(f"ordine: {ordine}")
    if d:
        rossi.append("IM04 " + "; ".join(d))

    # IM05
    d = []
    h = lab.casa()
    lab.segna(h, "proposta_accolta", mittente="a@a.it", quando="2026-11-10T09:00")
    lab.segna(h, "proposta_accolta", mittente="b@b.it", quando="2026-11-10T09:00")
    rc, o, e = lab.lancia(h, "calcola")
    p = proposte(o)
    if rc != 0 or len(p) != 2 or not all(x.startswith("PROPOSTA") for x in p):
        d.append(f"proposta: exit {rc}, {p}, {e[:80]}")
    if dati(h, "appreso.json") is not None or dati(h, "appreso-registro.jsonl") is not None:
        d.append("proposta scrive appreso.json o il registro")
    ids = [x.split()[1].rstrip(":") for x in p]
    rc, o, e = lab.lancia(h, "applica", "ffffffff")
    if rc != 2 or dati(h, "appreso.json") is not None:
        d.append(f"applica di un id ignoto: exit {rc}")
    if ids:
        rc, o, e = lab.lancia(h, "applica", ids[0])
        m = (dati(h, "appreso.json") or {}).get("mittenti", {})
        if rc != 0 or len(m) != 1 or len(dati(h, "appreso-registro.jsonl") or []) != 1:
            d.append(f"applica {ids[0]}: exit {rc}, {m}, {e[:80]}")
    h2 = lab.casa({"modo": "auto"})
    lab.segna(h2, "proposta_accolta", mittente="a@a.it", quando="2026-11-10T09:00")
    rc, o, e = lab.lancia(h2, "calcola")
    if rc != 0 or not o.startswith("APPLICATA") or (dati(h2, "appreso.json") or {}).get("mittenti", {}).get("a@a.it", {}).get("stato") != "si":
        d.append(f"modo auto: exit {rc}, {o[:80]}, {e[:80]}")
    if d:
        rossi.append("IM05 " + "; ".join(d))

    # IM06
    d = []
    h = lab.casa({"modo": "auto"})
    lab.segna(h, "proposta_rifiutata", mittente="x@x.it", quando="2026-11-10T09:00")
    lab.segna(h, "proposta_rifiutata", mittente="x@x.it", quando="2026-11-11T09:00")
    lab.lancia(h, "calcola")
    registro = dati(h, "appreso-registro.jsonl") or []
    if not registro:
        d.append("nessuna modifica registrata da annullare")
    else:
        mid = registro[0]["id"]
        rc, o, e = lab.lancia(h, "riepilogo", "--dal", "2000-01-01T00:00")
        if rc != 0 or f"annulla {mid}" not in o:
            d.append(f"riepilogo senza annullo: {o[:120]}")
        rc, o, e = lab.lancia(h, "annulla", mid)
        m = (dati(h, "appreso.json") or {}).get("mittenti", {})
        if rc != 0 or "x@x.it" in m:
            d.append(f"annulla: exit {rc}, {m}, {e[:80]}")
        rc, o, e = lab.lancia(h, "calcola")
        if "x@x.it" in (dati(h, "appreso.json") or {}).get("mittenti", {}):
            d.append("annullo rifatto dalle stesse prove")
        lab.segna(h, "proposta_rifiutata", mittente="x@x.it", quando="2099-01-01T00:00")
        lab.segna(h, "proposta_rifiutata", mittente="x@x.it", quando="2099-01-02T00:00")
        lab.lancia(h, "calcola")
        if (dati(h, "appreso.json") or {}).get("mittenti", {}).get("x@x.it", {}).get("stato") != "no":
            d.append("una prova nuova dopo l'annullo non rifà la modifica")
    if d:
        rossi.append("IM06 " + "; ".join(d))

    # IM07
    d = []
    h = lab.casa()
    buona = {"tipo": "scartato", "task": "uf/12", "motivo": "già coperto da un altro task", "quando": "2026-11-10T09:00",
             "origine": "pannello"}
    testo = "﻿" + "\n".join([json.dumps(buona, ensure_ascii=False), json.dumps(buona, ensure_ascii=False),
                                  "{rotta", json.dumps(dict(buona, task="uf/13"), ensure_ascii=False)]) + "\n"
    f = h.parent / "ponte.jsonl"
    f.write_text(testo, encoding="utf-8")
    rc, o, e = lab.lancia(h, "raccogli", str(f))
    righe = dati(h, "segnali.jsonl") or []
    if rc != 1 or len(righe) != 2 or "riga 3" not in e or righe[0].get("motivo") != buona["motivo"]:
        d.append(f"raccogli: exit {rc}, {len(righe)} righe, {e[:100]}")
    rc, o, e = lab.lancia(h, "raccogli", "-", stdin=json.dumps(buona) + "\n")
    if rc != 0 or len(dati(h, "segnali.jsonl") or []) != 2:
        d.append(f"un doppione da stdin è entrato: exit {rc}, {o[:80]}")
    if d:
        rossi.append("IM07 " + "; ".join(d))

    # IM08
    d = []
    h = lab.casa({"modo": "auto"})
    rotto = h / "data" / "monitor" / "appreso.json"
    rotto.parent.mkdir(parents=True)
    rotto.write_text("{non json", encoding="utf-8")
    lab.segna(h, "proposta_accolta", mittente="a@a.it")
    rc, o, e = lab.lancia(h, "calcola")
    if rc != 2 or rotto.read_text(encoding="utf-8") != "{non json":
        d.append(f"appreso.json rotto: exit {rc}")
    h = lab.casa()
    if (lab.repo / "bin" / "monitor" / "impara.py").is_file():
        r = subprocess.run([sys.executable, str(lab.repo / "bin" / "arturo"), "monitor"], capture_output=True,
                           text=True, env=dict(os.environ, ARTURO_HOME=str(h), HOME=str(h.parent)), timeout=60)
        if r.returncode != 2:
            d.append(f"arturo monitor senza impara: exit {r.returncode}")
    else:
        d.append("impara.py assente")
    rc, o, e = lab.lancia(h, "mostra", via_arturo=True)
    if rc != 0 or '"modo": "proposta"' not in o:
        d.append(f"arturo monitor impara mostra: exit {rc}, {e[:80]}")
    # La cache di Python su macOS (Library/Caches/com.apple.python) nasce sotto HOME: non è di Arturo.
    fuori = [p for p in h.parent.rglob("*") if p.is_file() and h not in p.parents and "Library" not in p.parts]
    if fuori:
        d.append(f"scritto fuori da ARTURO_HOME: {fuori[:3]}")
    if d:
        rossi.append("IM08 " + "; ".join(d))
    return rossi


# (caso, file, [(testo giusto, testo rotto)], motivo atteso nel rosso)
VELENI = [
    ("IM02", "bin/monitor/impara.py", [("    if rifiutate >= 2 and not accolte:", "    if rifiutate >= 1 and not accolte:")],
     "una rifiutata sola decide"),
    ("IM04", "bin/monitor/impara.py", [("    if sezione in sempre or len(ultimi)", "    if len(ultimi)")],
     "sempre compressa"),
    ("IM05", "bin/monitor/impara.py", [('    if modo == "proposta":\n        for m in trovate:', '    if False:\n        for m in trovate:')],
     "proposta scrive"),
    ("IM06", "bin/monitor/impara.py", [("    if not blocco:\n        return gruppo", "    if True:\n        return gruppo")],
     "annullo rifatto"),
]


def avvelena(repo: Path) -> int:
    esiti = []
    for caso, rel, cambi, motivo in VELENI:
        with tempfile.TemporaryDirectory(prefix="arturo-im-v-") as tmp:
            copia = Path(tmp) / "repo"
            shutil.copytree(repo, copia, ignore=shutil.ignore_patterns(".git", "__pycache__", "node_modules", "tests", "cache"))
            testo = (copia / rel).read_text(encoding="utf-8")
            for giusto, rotto in cambi:
                assert testo.count(giusto) == 1, f"veleno {caso}: il testo da rompere non c'è più in {rel}"
                testo = testo.replace(giusto, rotto)
            (copia / rel).write_text(testo, encoding="utf-8")
            (Path(tmp) / "lab").mkdir()
            rossi = prova(Lab(copia, Path(tmp) / "lab"))
            colpiti = [r for r in rossi if r.startswith(caso) and motivo in r]
            if not colpiti:
                print(f"VELENO {caso} NON ATTACCA: rossi {[r[:60] for r in rossi]}, atteso {motivo!r}")
                return 1
            print(f"VELENO {caso} ROSSO: {colpiti[0][:120]}")
            esiti.append(caso)
    print(f"VELENI_ROSSI={','.join(esiti)} veleni={len(VELENI)}")
    return 0 if len(esiti) == len(VELENI) else 1


def main() -> int:
    for flusso in (sys.stdout, sys.stderr):
        if hasattr(flusso, "reconfigure"):
            flusso.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument("--baseline-ref")
    parser.add_argument("--avvelena", action="store_true")
    a = parser.parse_args()
    repo = Path(a.repo).resolve()
    if a.avvelena:
        return avvelena(repo)
    with tempfile.TemporaryDirectory(prefix="arturo-im-") as tmp:
        rossi = prova(Lab(repo, Path(tmp)))
    if a.baseline_ref:
        codici = sorted({r.split()[0] for r in rossi})
        assert codici == list(CASI), f"baseline non discriminante: rossi {codici}, attesi {list(CASI)}"
        print(f"BASELINE_DISCRIMINANTE={','.join(codici)}")
        return 0
    for r in rossi:
        print("ROSSO", r)
    print(f"/monitor impara: {len(CASI) - len({r.split()[0] for r in rossi})}/{len(CASI)} casi verdi")
    return 1 if rossi else 0


if __name__ == "__main__":
    raise SystemExit(main())
